"""R1 anchor — the mid-cycle-margin × own-history-EV/EBITDA fundamental, PERSISTED source-bound.

A committed, spot-INDEPENDENT anchor so triage is a cheap READ, not a live CIQ+EDGAR recompute. The
value math is the #150 mid-cycle block (:func:`midcycle.scenario_value`, EBITDA basis: EV = (EBIT +
D&A) × multiple) — this module only GATHERS the source-bound inputs and CALLS it, never reimplements
the arithmetic. Every input is cited; a gap is FLAGGED and the anchor marked inapplicable, never
fabricated (a silently-zeroed D&A would understate EBITDA → understate the anchor).

An ATTENTION FILTER, not a verdict: it re-rates the name to its OWN-history median multiple on a
NAIVE reported-median margin — cycle / one-off / mix adjustments are the analyst's job in the full
2:1 underwrite. Spot and reward-to-base are computed LIVE at triage, never stored here.
"""
from __future__ import annotations

import statistics as st
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from vinci.dossier import midcycle as mc
from vinci.edgar.client import _max_outstanding_debt
from vinci.edgar.concepts import (
    ConceptPoint,
    extract_points,
    latest_annual,
    latest_instant,
    points_for_tag,
)

# --- tunable constants (named, not magic) -----------------------------------------------------
ANCHOR_FIRM_MIN_YEARS = 7            # a margin spanning >=7 FYs plausibly covers a cycle -> "firm"
ANCHOR_FIRM_MIN_MULT_QUARTERS = 20   # >=~5y of EV/EBITDA closes -> "firm" multiple; fewer -> "weak"

_USD_M = 1e6
RECIPE_R1 = "R1_midcycle_margin_evebitda"
RECIPE_R2 = "R2_NEEDED"
RECIPE_UNKNOWN = "unknown"
_DILUTED_TAG = "WeightedAverageNumberOfDilutedSharesOutstanding"
_NOTE = (
    "ATTENTION FILTER, not a verdict. Even a firm anchor requires a full bear/base/bull 2:1 "
    "underwrite before any BUY. Spot and reward-to-base are computed live at triage, not stored "
    "here."
)


class AnchorMargin(BaseModel, frozen=True):
    """The own-history median operating margin used, with its coverage + confidence."""

    value: float | None
    unit: str = "fraction"
    basis: str
    source: str
    anchor_years: int
    confidence: str  # firm | weak


class AnchorMultiple(BaseModel, frozen=True):
    """The own-history median EV/EBITDA — READ from the committed valuation block, never
    recomputed (same series/statistic the valuation own-history band already committed)."""

    value: float | None
    unit: str = "EV/EBITDA"
    source: str = "valuation.own_history.median"
    history_quarters: int
    confidence: str  # firm | weak


class AnchorInput(BaseModel, frozen=True):
    """One source-bound scalar input: value + unit + basis + citation (source-stamped)."""

    value: float | None
    unit: str
    basis: str
    source: str


class Anchor(BaseModel, frozen=True):
    """The R1 anchor block — source-bound, spot-independent. Optional on the Dossier so committed
    JSON predating it round-trips byte-identically; the UI ignores it for now (data-only)."""

    recipe_hint: str                    # RECIPE_R1 | RECIPE_R2 | RECIPE_UNKNOWN
    applicable: bool
    multiple_basis: str = mc.MULTIPLE_BASIS  # "EV/EBITDA"
    computed_at: datetime
    reason: str | None = None           # why inapplicable (R2 / gap), else None
    margin: AnchorMargin | None = None
    multiple: AnchorMultiple | None = None
    d_and_a: AnchorInput | None = None
    net_debt: AnchorInput | None = None
    diluted_shares: AnchorInput | None = None
    ltm_revenue: AnchorInput | None = None
    anchor_base_value_per_share: float | None = None   # the spot-independent fundamental
    anchor_ev_ebit: float | None = None
    overall_confidence: str | None = None  # firm | weak (the WEAKER of margin/multiple)
    note: str = _NOTE


# --- committed-artifact readers (work on the mechanical layer as a dict) -----------------------
def _own_history_multiple(mechanical: dict[str, Any]) -> tuple[float, int] | None:
    """(median EV/LTM-EBITDA, close-count) from committed ``valuation.own_history`` — READ, never
    recomputed. None when the own-history multiple is absent/UNKNOWN."""
    oh = ((mechanical.get("valuation") or {}).get("own_history") or {}).get("value")
    if not isinstance(oh, list):
        return None
    ev = next((r for r in oh if isinstance(r, dict) and "EBITDA" in str(r.get("metric", ""))), None)
    if not ev or ev.get("median") is None:
        return None
    return float(ev["median"]), int(ev.get("n_closes") or 0)


def _fs_annual(mechanical: dict[str, Any]) -> dict[str, Any]:
    return ((mechanical.get("financial_summary") or {}).get("annual") or {}).get("value") or {}


def _last_actual_index(ann: dict[str, Any], n: int) -> int:
    """Index of the last ACTUAL (non-estimate) column of the annual table."""
    ise = ann.get("is_estimate") or []
    return max((i for i, e in enumerate(ise) if not e), default=n - 1)


def _ltm_revenue_from_fs(mechanical: dict[str, Any]) -> float | None:
    """LTM revenue ($M) = the last ACTUAL Revenue column of committed
    ``financial_summary.annual`` (the same base the render's LTM column shows)."""
    ann = _fs_annual(mechanical)
    rev = next((r for r in ann.get("rows") or [] if r.get("label") == "Revenue ($M)"), None)
    vals = (rev or {}).get("values") or []
    if not vals:
        return None
    idx = _last_actual_index(ann, len(vals))
    return float(vals[idx]) if 0 <= idx < len(vals) and vals[idx] is not None else None


def _margin_from_fs(mechanical: dict[str, Any]) -> tuple[float, int] | None:
    """FALLBACK margin: median(EBIT / Revenue) over the ACTUAL years of committed
    ``financial_summary.annual`` (short history; used only when EDGAR op-income is untagged)."""
    ann = _fs_annual(mechanical)
    rows = {r.get("label"): r for r in ann.get("rows") or []}
    ebit = (rows.get("EBIT ($M)") or {}).get("values") or []
    rev = (rows.get("Revenue ($M)") or {}).get("values") or []
    ise = ann.get("is_estimate") or []
    margins = [
        ebit[i] / rev[i]
        for i in range(min(len(ebit), len(rev)))
        if not (i < len(ise) and ise[i]) and ebit[i] is not None and rev[i]
    ]
    return (st.median(margins), len(margins)) if margins else None


# --- EDGAR source-bound extractors (fail-loud; a gap → None, never a fabricated zero) ----------
def _latest_dep_amort(facts: dict[str, Any]) -> tuple[float, str] | None:
    """Latest-FY consolidated D&A ($). Prefer the combined tag; else the source-stamped
    ``Depreciation + AmortizationOfIntangibleAssets`` split-sum (a filer like CNXC reports the two
    separately, not the combined tag). None when neither is tagged — flagged, never zero-filled."""
    p = latest_annual(extract_points(facts, "dep_amort"))
    if p:
        return p.value, "EDGAR companyfacts dep_amort (combined)"
    dep = latest_annual(points_for_tag(facts, "Depreciation"))
    am = latest_annual(points_for_tag(facts, "AmortizationOfIntangibleAssets"))
    # SAME fiscal period or nothing: summing an FY2025 depreciation into an FY2024 amortisation
    # would fabricate a D&A that never existed. This is the period-alignment discipline
    # ``edgar_fundamentals`` already applies to its own EBITDA add-back — misaligned → UNKNOWN
    # (flagged upstream), never a silently blended number.
    if dep and am and dep.period_end == am.period_end:
        fy = dep.fy or dep.period_end.year
        return dep.value + am.value, (
            f"EDGAR Depreciation + AmortizationOfIntangibleAssets (split, FY{fy})")
    return None


def _latest_point(facts: dict[str, Any], tag: str) -> ConceptPoint | None:
    """The most recent reported point for an explicit tag, by (period_end, filed).

    For a DURATION concept — the diluted weighted-average share count has no instant context —
    ``latest_instant`` would only reach it through its balance-sheet fallback, so the selection is
    made explicit here rather than resting on that fallback. The latest period IS the latest 10-Q's
    weighted average, which is the divisor the anchor wants."""
    pts = points_for_tag(facts, tag)
    return max(pts, key=lambda p: (p.period_end, p.filed)) if pts else None


def _sum_latest_tags(facts: dict[str, Any], *tags: str) -> float:
    """Sum the latest-instant value of each explicit tag — an absent LEASE tag is a legitimate 0
    (a filer without that lease type), unlike debt/cash which fail loud when wholly absent."""
    return sum(p.value for t in tags if (p := latest_instant(points_for_tag(facts, t))))


def _lease_inclusive_net_debt(facts: dict[str, Any]) -> tuple[float | None, str] | None:
    """Lease-inclusive net debt ($): total debt (LT + current) + finance leases + operating leases −
    cash, latest 10-Q. Returns ``(value_or_None, bridge)``; the tested under-capture guard flips it
    UNKNOWN (value None) when a single instrument exceeds 1.1× the extracted debt total (never a
    confident understatement — 'pull CIQ'). Wholly-absent debt/cash → the whole thing is None."""
    ltd = latest_instant(extract_points(facts, "long_term_debt"))
    dc = latest_instant(extract_points(facts, "debt_current"))
    cash = latest_instant(extract_points(facts, "cash"))
    if not (ltd or dc) or cash is None:
        return None
    td = (ltd.value if ltd else 0.0) + (dc.value if dc else 0.0)
    fin = _sum_latest_tags(facts, "FinanceLeaseLiabilityCurrent", "FinanceLeaseLiabilityNoncurrent")
    opl = _sum_latest_tags(facts, "OperatingLeaseLiabilityCurrent",
                           "OperatingLeaseLiabilityNoncurrent")
    bridge = (
        f"total debt {td / _USD_M:,.0f} + finance leases {fin / _USD_M:,.0f} + operating leases "
        f"{opl / _USD_M:,.0f} − cash {cash.value / _USD_M:,.0f} ($M)"
    )
    ref = max((p.period_end.isoformat() for p in (ltd, dc) if p), default=None)
    witness = _max_outstanding_debt(facts, ref)
    if witness and witness[0] > td * 1.10:
        return None, (bridge + f" — UNDER-CAPTURED: {witness[1]} ${witness[0] / _USD_M:,.0f}M "
                      "alone exceeds the extracted long-term+current total; pull CIQ")
    return td + fin + opl - cash.value, bridge


# --- the shared anchor computation (called by assembly AND the backfill writer) ----------------
def compute_anchor(mechanical: dict[str, Any], *, facts: dict[str, Any],
                   computed_at: datetime) -> Anchor:
    """The R1 anchor from SOURCE-BOUND inputs. ``mechanical`` is the mechanical layer as a dict
    (``model_dump`` at assembly, committed JSON at backfill); ``facts`` is EDGAR companyfacts.

    Every input is cited and fail-loud: a missing own-history multiple → inapplicable; a
    non-positive margin → the R2 (revenue-anchored) hint; an incomplete value bridge → applicable
    False with the per-input source stamps telling the human exactly what's missing. The base value
    is the #150 block's EBITDA-basis math, never reimplemented here."""
    mult = _own_history_multiple(mechanical)
    if mult is None:
        return Anchor(recipe_hint=RECIPE_UNKNOWN, applicable=False, computed_at=computed_at,
                      reason="own-history multiple missing (valuation.own_history.median absent)")
    mult_median, mult_qtrs = mult

    # margin — median operating margin over ALL available FYs (EDGAR); fallback → financial_summary.
    rev_s, oi_s = mc.annual_series(facts, "revenue"), mc.annual_series(facts, "operating_income")
    ma = mc.margin_anchor(rev_s, oi_s)
    margin_val, margin_years = ma.median, ma.n_years
    margin_source = (f"EDGAR companyfacts {oi_s.tag} / {rev_s.tag} — reported median over "
                     f"{margin_years} FY") if margin_val is not None else ""
    forced_weak = False
    if margin_val is None:
        fb = _margin_from_fs(mechanical)
        if fb is not None:
            margin_val, margin_years = fb
            margin_source = "financial_summary (short history) — EBIT/Revenue reported median"
            forced_weak = True

    # POSITIVITY GUARD (minimal): no positive normalizable margin → the revenue-anchored recipe.
    if margin_val is None or margin_val <= 0:
        return Anchor(
            recipe_hint=RECIPE_R2, applicable=False, computed_at=computed_at,
            reason="no positive operating margin over available history — needs revenue-anchored "
                   "recipe")

    # remaining source-bound inputs
    da = _latest_dep_amort(facts)
    nd = _lease_inclusive_net_debt(facts)
    dil = _latest_point(facts, _DILUTED_TAG)
    ltm_rev = _ltm_revenue_from_fs(mechanical)
    nd_val = nd[0] if nd else None

    m_conf = "firm" if (margin_years >= ANCHOR_FIRM_MIN_YEARS and not forced_weak) else "weak"
    x_conf = "firm" if mult_qtrs >= ANCHOR_FIRM_MIN_MULT_QUARTERS else "weak"
    overall = "firm" if (m_conf == "firm" and x_conf == "firm") else "weak"

    margin_blk = AnchorMargin(value=round(margin_val, 6), basis="operating margin (EBIT / revenue)",
                              source=margin_source, anchor_years=margin_years, confidence=m_conf)
    multiple_blk = AnchorMultiple(value=mult_median, history_quarters=mult_qtrs, confidence=x_conf)
    da_blk = AnchorInput(value=(round(da[0] / _USD_M, 3) if da else None), unit="$M",
                         basis="consolidated latest FY",
                         source=(da[1] if da else "UNKNOWN — no D&A tag (combined or split)"))
    nd_blk = AnchorInput(value=(round(nd_val / _USD_M, 3) if nd_val is not None else None),
                         unit="$M", basis="lease-inclusive net debt (latest 10-Q)",
                         source=("EDGAR: " + nd[1]) if nd else "UNKNOWN — no debt/cash tag")
    dil_blk = AnchorInput(value=(dil.value if dil else None), unit="shares",
                          basis="diluted weighted-average (latest 10-Q)",
                          source=(f"EDGAR {_DILUTED_TAG}" if dil
                                  else "UNKNOWN — no diluted WA tag"))
    ltm_blk = AnchorInput(value=(round(ltm_rev, 3) if ltm_rev is not None else None), unit="$M",
                          basis="LTM revenue", source="committed financial_summary.annual (LTM)")

    # anchor base — the #150 block's EBITDA-basis value math; needs a complete bridge.
    base = ev_ebit = None
    if da and nd_val is not None and dil and dil.value > 0 and ltm_rev is not None:
        sv = mc.scenario_value(
            mc.Scenario(name="base", revenue=ltm_rev, margin=margin_val, multiple=mult_median,
                        source="anchor default", d_and_a=da[0] / _USD_M),
            net_debt=nd_val / _USD_M, shares=dil.value)
        base = round(sv.equity * _USD_M / dil.value, 4)
        ev_ebit = round(sv.ev_ebit, 4) if sv.ev_ebit is not None else None

    return Anchor(
        recipe_hint=RECIPE_R1, applicable=base is not None, computed_at=computed_at,
        reason=(None if base is not None else "R1 inputs incomplete — see per-input source stamps"),
        margin=margin_blk, multiple=multiple_blk, d_and_a=da_blk, net_debt=nd_blk,
        diluted_shares=dil_blk, ltm_revenue=ltm_blk,
        anchor_base_value_per_share=base, anchor_ev_ebit=ev_ebit, overall_confidence=overall)


def insert_anchor_block(text: str, anchor: Anchor) -> str:
    """Append the ``anchor`` block as the LAST top-level field of a committed dossier.json TEXT,
    byte-preserving. The ONLY edit to existing bytes is a trailing comma on the previously-last
    field (unavoidable JSON syntax); every other field stays byte-for-byte identical. The backfill
    uses this rather than a model round-trip, because re-serializing older-schema dossiers drifts
    their other fields (new-default materialisation) — a corruption the string insert avoids."""
    body = anchor.model_dump_json(indent=2)  # a top-level-indented anchor object
    inner = "\n".join("  " + ln for ln in body.split("\n"))      # +2 so it sits at the field level
    field = '  "anchor": ' + inner.lstrip()                      # -> '  "anchor": {\n    …\n  }'
    end = text.rstrip()
    if not end.endswith("}"):
        raise ValueError("dossier.json is not a JSON object — refusing to insert the anchor")
    trailing = text[len(end):]                                   # preserved trailing whitespace
    head = end[:-1].rstrip()                                     # up to the last field's value
    return f"{head},\n{field}\n}}{trailing}"
