"""EDGAR XBRL fundamentals fallback — fills the dossier's CIQ-sourced fundamentals fields when the
CIQ Financials subsheets (Income Statement / Balance Sheet / Cash Flow) are PRESENT-BUT-DATA-EMPTY
(header-only) WHILE the Multiples sheet is populated. CIQ Multiples stays PRIMARY — this is a
graceful per-field fallback-on-UNKNOWN, never an override of a populated CIQ field.

REUSES :func:`vinci.edgar.concepts.extract_points` (the existing XBRL layer) — no new XBRL fetch
here. Every field is fail-loud and source-honest:

- EBITDA = operating_income + D&A, BOTH the SAME fiscal period; if D&A is absent or
  period-misaligned the period is dropped — a name reporting operating_income but ZERO D&A
  datapoints (the CNXC case) yields NO EBITDA, never operating_income alone, never a fabricated
  number. (Mirrors the exact pattern in :meth:`vinci.edgar.client.fundamental_snapshot`.)
- FCF = operating_cash_flow − capex (same period). NB: this is the simple OCF−capex basis, honestly
  labelled in the source_ref — distinct from CIQ's *Levered* Free Cash Flow definition.
- every source_ref reads ``EDGAR XBRL companyfacts <tag(s)> [<period(s)>]`` (NOT a CIQ ref), so the
  provenance is visible and the human knows the basis is raw GAAP, not CIQ-normalized.

CIQ's normalized / adjusted figures (normalized EBITDA, adjusted EPS, segment data) CANNOT be
derived from raw XBRL and are NOT produced here — they stay UNKNOWN upstream (the caller keeps the
CIQ field).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from vinci.dossier.schemas import PeerComps, Sourced, SourceStatus
from vinci.edgar.concepts import (
    ConceptPoint,
    annual_by_period,
    current_pair,
    extract_points,
    fiscal_year_ends,
    fiscal_year_of,
)

_USD_M = 1e6  # EDGAR companyfacts report in dollars; the dossier/CIQ convention is $M

# The cross-source basis flag carried ON peer_comps.fundamental_deltas (ONLY) when the name's
# fundamentals are EDGAR-derived: the name's side is raw GAAP while the peer medians are CIQ-basis,
# so a delta may be definitional, not a real gap. The MULTIPLES comparison is NOT flagged —
# both the name's and the peers' multiples come from CIQ, so that comparison is same-basis and safe.
CROSS_SOURCE_DELTA_FLAG = (
    "name fundamentals are EDGAR-GAAP basis (CIQ fundamentals empty) vs peers on CIQ basis — a "
    "delta may be definitional, not a real gap"
)


def _period_label(p: ConceptPoint, year_ends: dict[int, tuple[date, ...]]) -> str:
    """The period's OWN fiscal year in the filer's calendar (:func:`fiscal_year_of`), or its end
    date where the calendar places none — never companyfacts' ``fy``, the year of the FILING that
    carried the point (Climb Global's FCF for the year to 2019-12-31 read "[FY2020]")."""
    fy = fiscal_year_of(year_ends, p)
    return f"FY{fy}" if fy is not None else p.period_end.isoformat()


def _span(points: dict[date, ConceptPoint], year_ends: dict[int, tuple[date, ...]]) -> str:
    """A compact 'FY2021–FY2025' span over the periods present (for the source_ref)."""
    keys = sorted(points)
    if not keys:
        return "no period"
    lo, hi = (_period_label(points[keys[0]], year_ends),
              _period_label(points[keys[-1]], year_ends))
    return lo if lo == hi else f"{lo}–{hi}"


class EdgarFundamentals:
    """Source-bound fundamentals derived from ONE company's EDGAR ``companyfacts``. Construct only
    when the CIQ fundamentals are empty + Multiples present (see :func:`build_fallback`)."""

    def __init__(self, facts: dict[str, Any]) -> None:
        self._rev = annual_by_period(extract_points(facts, "revenue"))
        self._op = annual_by_period(extract_points(facts, "operating_income"))
        self._da = annual_by_period(extract_points(facts, "dep_amort"))
        self._ocf = annual_by_period(extract_points(facts, "operating_cash_flow"))
        self._capex = annual_by_period(extract_points(facts, "capex"))
        # EBITDA per period: operating_income + D&A, BOTH the same fiscal period. A period missing
        # D&A is DROPPED (fail-loud), never operating_income alone. CNXC (op present, D&A absent) →
        # this dict stays empty → EBITDA-margin / EBITDA-trajectory are UNKNOWN, never fabricated.
        # period_end AND period_start must match — a same-end pair of different durations (a
        # fiscal-year-transition stub) would otherwise sum mismatched spans into a wrong EBITDA.
        self._ebitda: dict[date, float] = {
            pe: self._op[pe].value + self._da[pe].value
            for pe in sorted(self._op.keys() & self._da.keys())
            if self._op[pe].period_start == self._da[pe].period_start
        }
        self._fcf: dict[date, float] = {
            pe: self._ocf[pe].value - self._capex[pe].value
            for pe in sorted(self._ocf.keys() & self._capex.keys())
            if self._ocf[pe].period_start == self._capex[pe].period_start
        }
        self._facts = facts
        self._year_ends = fiscal_year_ends(facts)  # which fiscal year each period IS

    def _label(self, p: ConceptPoint) -> str:
        return _period_label(p, self._year_ends)

    # --- the three CIQ-sourced fundamentals fields, mirrored on a raw-GAAP basis -----------------

    def free_cash_flow(self) -> Sourced[float]:
        """Latest annual FCF ($M) = operating cash flow − capex (same period). Fail-loud UNKNOWN.

        UNKNOWN, too, when that period is not current (:func:`vinci.edgar.concepts.current_pair`,
        the pairing the screen's FCF sign reads): a fiscal year or more behind the newest period
        either leg's concept carries — Climb Global's last year with both legs is FY2019, and it
        read as the latest FCF beside quarters to 2026 — or more than one fiscal year behind the
        filer's newest. The capex leg may be a substitute the filer proved to be the same line
        (:func:`vinci.edgar.concepts.annual_line`); the source names the tag read."""
        legs, stale = current_pair(self._facts, "operating_cash_flow", "capex")
        if legs is None:
            if stale is None or stale.period_end is None:
                return Sourced.unknown(
                    note="EDGAR: no fiscal period with both operating cash flow and capex"
                )
            return Sourced.unknown(note="EDGAR: " + stale.note)
        ocf, capex = legs
        ref = (
            f"EDGAR XBRL companyfacts {ocf.tag} − {capex.tag} "
            f"[{self._label(ocf)}] ($M)"
        )
        return Sourced.present(round((ocf.value - capex.value) / _USD_M, 1), source_ref=ref)

    def margin_trend(self) -> Sourced[str]:
        """EBITDA-margin trajectory (% per period) PAIRED with the absolute EBITDA + revenue
        reconciler — the same shape CIQ emits, so a falling margin % is never read without the
        absolute series. UNKNOWN when there is no ≥2-period EBITDA margin (e.g. D&A absent)."""
        margin = {pe: self._ebitda[pe] / self._rev[pe].value
                  for pe in sorted(self._ebitda.keys() & self._rev.keys()) if self._rev[pe].value}
        if len(margin) < 2:
            return Sourced.unknown(
                note="EDGAR: no ≥2-period EBITDA margin (operating_income+D&A ÷ revenue) — "
                "D&A absent/misaligned or revenue absent"
            )
        bits = ["EBITDA margin: " + " → ".join(
            f"{self._label(self._rev[pe])} {margin[pe]:.0%}" for pe in sorted(margin))]
        abs_eb = self._series_m(self._ebitda, self._op)
        abs_rev = self._series_m({pe: p.value for pe, p in self._rev.items()}, self._rev)
        if abs_eb:
            bits.append(f"absolute EBITDA: {abs_eb}")
        if abs_rev:
            bits.append(f"absolute revenue: {abs_rev}")
        return Sourced.present(
            "; ".join(bits) + "  [EDGAR GAAP basis, $M; margin % can fall while absolute EBITDA "
            "RISES — read them together]",
            source_ref=f"EDGAR XBRL companyfacts {self._op[max(self._op)].tag}+D&A ÷ "
            f"{self._rev[max(self._rev)].tag} [{_span(self._rev, self._year_ends)}]",
        )

    def multi_year_trajectory(self) -> Sourced[str]:
        """The multi-year arc — revenue / EBITDA / FCF, per period ($M). Partial is fine (EBITDA is
        omitted when D&A is absent); UNKNOWN only when no series has ≥2 periods."""
        lines: list[str] = []
        if (rev := self._series_m({pe: p.value for pe, p in self._rev.items()}, self._rev)):
            lines.append(f"Revenue: {rev}")
        if (eb := self._series_m(self._ebitda, self._op)):
            lines.append(f"EBITDA: {eb}")
        if (fcf := self._series_m(self._fcf, self._ocf)):
            lines.append(f"FCF: {fcf}")
        if not lines:
            return Sourced.unknown(note="EDGAR: no ≥2-period revenue/EBITDA/FCF series")
        return Sourced.present(
            "; ".join(lines) + "  [EDGAR XBRL GAAP basis, $M; per-period values, never YoY'd]",
            source_ref="EDGAR XBRL companyfacts revenue / operating_income+D&A / "
            "operating_cash_flow−capex (annual)",
        )

    def _series_m(
        self, by_period: dict[date, float], label_src: dict[date, ConceptPoint]
    ) -> str | None:
        """'FY21 390 → FY22 410 → …' in $M for a per-period series (≥2 points), labels from
        ``label_src`` (the concept whose ConceptPoint carries the fiscal-year label)."""
        periods = sorted(by_period)
        if len(periods) < 2:
            return None
        return " → ".join(
            f"{self._label(label_src[pe]) if pe in label_src else pe.isoformat()} "
            f"{by_period[pe] / _USD_M:,.0f}"
            for pe in periods
        )


def build_fallback(
    *,
    multiples: list[Sourced[Any]],
    ciq_fundamentals: list[Sourced[Any]],
    facts_fn: Callable[[], dict[str, Any] | None],
) -> EdgarFundamentals | None:
    """Decide whether the EDGAR fundamentals fallback fires, and build its context.

    Trigger (empty-subsheet signature): at least one CIQ **Multiples** signal is PRESENT
    — proof the workbook IS pulled (Financials→Multiples and/or the Comparable Analysis Trading
    Multiples) — AND at least one CIQ fundamentals field is NOT present (the header-only sheets
    surface per-field UNKNOWN). No CIQ multiples present → ``None`` (we never fall back for a wholly
    un-pulled name). ``None`` too when companyfacts can't be fetched — the caller keeps the CIQ
    UNKNOWN, never a fabricated number.
    """
    if not any(s.status is SourceStatus.PRESENT for s in multiples):
        return None
    if all(s.status is SourceStatus.PRESENT for s in ciq_fundamentals):
        return None  # CIQ fundamentals are populated — no fallback needed
    facts = facts_fn()
    if not facts:
        return None
    return EdgarFundamentals(facts)


def flag_deltas_basis(pc: PeerComps) -> PeerComps:
    """Carry the cross-source basis flag on ``fundamental_deltas`` ONLY (never trading_multiples),
    and only when there IS a delta to caveat (PRESENT) — a no-op otherwise (no comparison). Pure."""
    fd = pc.fundamental_deltas
    if fd.status is not SourceStatus.PRESENT or not fd.value:
        return pc
    fd = fd.model_copy(update={"value": f"{fd.value}  [⚠ {CROSS_SOURCE_DELTA_FLAG}]"})
    return pc.model_copy(update={"fundamental_deltas": fd})
