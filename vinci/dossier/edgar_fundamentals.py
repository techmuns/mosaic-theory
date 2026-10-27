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
from vinci.edgar.concepts import ConceptPoint, concept_frontier, extract_points, stale_against

_USD_M = 1e6  # EDGAR companyfacts report in dollars; the dossier/CIQ convention is $M

# The cross-source basis flag carried ON peer_comps.fundamental_deltas (ONLY) when the name's
# fundamentals are EDGAR-derived: the name's side is raw GAAP while the peer medians are CIQ-basis,
# so a delta may be definitional, not a real gap. The MULTIPLES comparison is NOT flagged —
# both the name's and the peers' multiples come from CIQ, so that comparison is same-basis and safe.
CROSS_SOURCE_DELTA_FLAG = (
    "name fundamentals are EDGAR-GAAP basis (CIQ fundamentals empty) vs peers on CIQ basis — a "
    "delta may be definitional, not a real gap"
)


def _annual_by_period(points: list[ConceptPoint]) -> dict[date, ConceptPoint]:
    """Latest-FILED annual point per fiscal ``period_end`` — collapses restatements to the most
    recent filing without mutating earlier rows (same rule as :func:`latest_annual`)."""
    out: dict[date, ConceptPoint] = {}
    for p in points:
        if not p.is_annual:
            continue
        cur = out.get(p.period_end)
        if cur is None or p.filed > cur.filed:
            out[p.period_end] = p
    return out


def _period_label(p: ConceptPoint) -> str:
    return f"FY{p.fy}" if p.fy else p.period_end.isoformat()


def _span(points: dict[date, ConceptPoint]) -> str:
    """A compact 'FY2021–FY2025' span over the periods present (for the source_ref)."""
    keys = sorted(points)
    if not keys:
        return "no period"
    lo, hi = _period_label(points[keys[0]]), _period_label(points[keys[-1]])
    return lo if lo == hi else f"{lo}–{hi}"


class EdgarFundamentals:
    """Source-bound fundamentals derived from ONE company's EDGAR ``companyfacts``. Construct only
    when the CIQ fundamentals are empty + Multiples present (see :func:`build_fallback`)."""

    def __init__(self, facts: dict[str, Any]) -> None:
        self._rev = _annual_by_period(extract_points(facts, "revenue"))
        self._op = _annual_by_period(extract_points(facts, "operating_income"))
        self._da = _annual_by_period(extract_points(facts, "dep_amort"))
        self._ocf = _annual_by_period(extract_points(facts, "operating_cash_flow"))
        self._capex = _annual_by_period(extract_points(facts, "capex"))
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
        # The newest period each FCF leg's concept carries: the latest FCF year is judged against
        # both, so a pair that last met years ago is never served as this year's FCF.
        self._newest = {c: concept_frontier(facts, c) for c in ("operating_cash_flow", "capex")}

    # --- the three CIQ-sourced fundamentals fields, mirrored on a raw-GAAP basis -----------------

    def free_cash_flow(self) -> Sourced[float]:
        """Latest annual FCF ($M) = operating cash flow − capex (same period). Fail-loud UNKNOWN.

        UNKNOWN, too, when that period is a fiscal year or more behind the newest period either
        leg's concept carries (:func:`vinci.edgar.concepts.current_annual`): Climb Global's last
        year with both legs is FY2019, and it read as the latest FCF beside quarters to 2026."""
        if not self._fcf:
            return Sourced.unknown(
                note="EDGAR: no fiscal period with both operating cash flow and capex"
            )
        pe = max(self._fcf)
        stale = [s for s in (stale_against(self._ocf[pe], self._newest["operating_cash_flow"]),
                             stale_against(self._capex[pe], self._newest["capex"])) if s]
        if stale:
            return Sourced.unknown(note="EDGAR: " + "; ".join(s.note for s in stale))
        ref = (
            f"EDGAR XBRL companyfacts {self._ocf[pe].tag} − {self._capex[pe].tag} "
            f"[{_period_label(self._ocf[pe])}] ($M)"
        )
        return Sourced.present(round(self._fcf[pe] / _USD_M, 1), source_ref=ref)

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
            f"{_period_label(self._rev[pe])} {margin[pe]:.0%}" for pe in sorted(margin))]
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
            f"{self._rev[max(self._rev)].tag} [{_span(self._rev)}]",
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
            f"{_period_label(label_src[pe]) if pe in label_src else pe.isoformat()} "
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
