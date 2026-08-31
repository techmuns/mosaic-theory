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

from vinci.dossier import band_guards as bg
from vinci.dossier import midcycle as mc
from vinci.edgar.client import _max_outstanding_debt
from vinci.edgar.concepts import (
    CONCEPT_ALIASES,
    ConceptPoint,
    extract_points,
    latest_annual,
    latest_instant,
    points_for_tag,
)

# --- tunable constants (named, not magic) -----------------------------------------------------
ANCHOR_FIRM_MIN_YEARS = 7            # a margin spanning >=7 FYs plausibly covers a cycle -> "firm"
# The multiple leg is firm on the WINDOW it actually spans, not a raw close count: a band could show
# 20 closes yet span 20 years if annual-mislabelled (the 2026-07-21 incident). Firm ⇔ >=5 calendar
# years AND quarterly periodicity — never point-count alone.
ANCHOR_FIRM_MIN_MULT_YEARS = 5.0

_USD_M = 1e6
RECIPE_R1 = "R1_midcycle_margin_evebitda"
RECIPE_R2 = "R2_NEEDED"
RECIPE_UNKNOWN = "unknown"
RECIPE_UNRESOLVED = "ANCHOR_UNRESOLVED"
# An OPERATOR re-tag, never machine-derived (2026-07-21, CNXC): R1 computes cleanly but its output
# is not ROBUST — one turn of multiple error moves value/share by most of spot, so the grid cannot
# discriminate whatever the arithmetic says. Distinct from R2_NEEDED (the recipe does not fit) and
# from ANCHOR_UNRESOLVED (an input is missing): here the recipe fits and the inputs are sound, and
# the ANSWER is still not usable. Recorded by hand with its re-engagement trigger.
RECIPE_R1_NOT_ROBUST = "R1_NOT_ROBUST"

# The margin DENOMINATOR is chosen by what the tag MEANS (total company revenue), never by which
# series is longest. Longest-wins picked AORT's `Revenues`, which reports a partial/segment measure
# for FY2011–17 ($30–45M vs the 606 tag's $180–190M — ~4x) and manufactured 38–50% "margins" and a
# false 15.83% anchor median. Preference order: the post-2018 ASC-606 total-revenue standard first,
# legacy totals last. Fewer VALID years beats more invalid ones.
_REVENUE_TAG_PREFERENCE = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
)
# Two tags reporting the SAME fiscal year this far apart are not two views of one number — one of
# them is not total revenue. Never silently pick: flag, and use the preferred (total) tag.
_TAG_CONFLICT_PCT = 0.25
DQ_REVENUE_TAG_CONFLICT = "revenue_tag_conflict"
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

    recipe_hint: str                    # RECIPE_R1 | RECIPE_R2 | RECIPE_UNKNOWN | RECIPE_UNRESOLVED
    applicable: bool
    multiple_basis: str = mc.MULTIPLE_BASIS  # "EV/EBITDA"
    computed_at: datetime
    reason: str | None = None           # why inapplicable (R2 / gap), else None
    # Fail-loud data-quality channel. A fired flag CAPS overall_confidence at "weak" no matter how
    # many years/quarters underlie the stats — AORT read "firm" on fabricated years; never again.
    data_quality: str | None = None                  # e.g. DQ_REVENUE_TAG_CONFLICT
    data_quality_detail: list[str] = []              # which tags disagreed, by how much
    margin: AnchorMargin | None = None
    multiple: AnchorMultiple | None = None
    d_and_a: AnchorInput | None = None
    net_debt: AnchorInput | None = None
    diluted_shares: AnchorInput | None = None
    ltm_revenue: AnchorInput | None = None
    # (R2 cohort, 2026-07-21) Free cash flow — the SURVIVAL input. A negative value IS the burn the
    # R2 gate divides cash+facilities by, so its basis is stated on the block rather than assumed:
    # EDGAR reports a clean ANNUAL point, and summing XBRL quarterlies into a true LTM is where a
    # fabricated burn would come from (Q4 is usually FY-minus-9M, not a filed discrete quarter).
    # The R2 record takes this as a DEFAULT the analyst may override with a reason. Additive/opt.
    ltm_fcf: AnchorInput | None = None
    anchor_base_value_per_share: float | None = None   # the spot-independent fundamental
    anchor_ev_ebit: float | None = None
    overall_confidence: str | None = None  # firm | weak (the WEAKER of margin/multiple)
    note: str = _NOTE


# --- committed-artifact readers (work on the mechanical layer as a dict) -----------------------
def _own_history_multiple(mechanical: dict[str, Any]) -> dict[str, Any] | None:
    """The committed own-history EV/EBITDA band — READ, never recomputed. Returns the median, close
    count, calendar span, periodicity label and any data-quality flag so the caller can judge the
    multiple leg on the WINDOW it actually spans, not the raw point count. None when absent/UNKNOWN.

    ``window_span_years``/``periodicity`` are optional (pre-metadata committed JSON lacks them): a
    band without them is treated as span-UNKNOWN → the leg cannot be firm (the safe read). Likewise
    ``implied_d_and_a_margin`` (the band-coherence read) — absent on pre-guard JSON, which simply
    leaves the recorded-D&A cross-check unrun rather than failing."""
    oh = ((mechanical.get("valuation") or {}).get("own_history") or {}).get("value")
    if not isinstance(oh, list):
        return None
    ev = next((r for r in oh if isinstance(r, dict) and "EBITDA" in str(r.get("metric", ""))), None)
    if not ev or ev.get("median") is None:
        return None
    span = ev.get("window_span_years")
    da_margin = ev.get("implied_d_and_a_margin")
    cur = ev.get("current")
    return {
        "median": float(ev["median"]),
        "current": float(cur) if cur is not None else None,
        "n_closes": int(ev.get("n_closes") or 0),
        "span_years": float(span) if span is not None else None,
        "periodicity": ev.get("periodicity"),
        "data_quality": ev.get("data_quality"),
        "implied_d_and_a_margin": float(da_margin) if da_margin is not None else None,
    }


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


def _ltm_ebit_from_fs(mechanical: dict[str, Any]) -> float | None:
    """LTM EBIT ($M) — the last ACTUAL EBIT column, the same column ``_ltm_revenue_from_fs`` reads.
    Paired with EDGAR D&A it gives the RECORDED EBITDA the market-reconciliation guard tests the
    multiple against (the sheet never states EBITDA outright; it is EBIT + D&A by definition)."""
    ann = _fs_annual(mechanical)
    row = next((r for r in ann.get("rows") or [] if r.get("label") == "EBIT ($M)"), None)
    vals = (row or {}).get("values") or []
    if not vals:
        return None
    idx = _last_actual_index(ann, len(vals))
    return float(vals[idx]) if 0 <= idx < len(vals) and vals[idx] is not None else None


def _market_cap_from_mechanical(mechanical: dict[str, Any]) -> float | None:
    """Committed CIQ market cap ($M) — the market leg of the reconciliation guard, read from the
    artifact so the check runs at BACKFILL time too (no network, no live spot). It feeds only
    ``data_quality``; no anchor VALUE derives from it, so the anchor stays spot-independent."""
    mc_blk = (mechanical.get("implied_valuation") or {}).get("market_cap") or {}
    v = mc_blk.get("value")
    return float(v) if isinstance(v, int | float) else None


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


# --- revenue-denominator selection (anchor-local; the shared resolver is NOT touched) ----------
def _revenue_candidates(facts: dict[str, Any]) -> dict[str, mc.AnnualSeries]:
    """Every candidate revenue tag that actually reports ANNUAL data, keyed by tag.

    Reads each tag EXPLICITLY so the choice below is OURS, not the shared alias resolver's —
    ``extract_points``/``CONCEPT_ALIASES`` and ``midcycle.annual_series`` (used by the mid-cycle
    block and its tests) are deliberately left unchanged. Reuses midcycle's point-folding rather
    than re-implementing XBRL parsing."""
    out: dict[str, mc.AnnualSeries] = {}
    for tag in _REVENUE_TAG_PREFERENCE:
        s = mc._series_from_points("revenue", tag, mc._annual_points(facts, tag, "revenue"))
        if s.by_year:
            out[tag] = s
    return out


def _total_revenue_series(facts: dict[str, Any]) -> tuple[mc.AnnualSeries | None, list[str]]:
    """The TOTAL-company revenue series chosen by PREFERENCE (never by longest coverage), plus any
    fail-loud disagreement notes.

    GUARD: when two candidate tags both report a fiscal year and disagree by more than
    ``_TAG_CONFLICT_PCT``, they are not two views of one number — one is not total revenue. Record
    the disagreement (the caller flags ``data_quality`` and caps confidence) and use the PREFERRED
    tag. No candidate at all → ``(None, [])``, and the caller marks the anchor UNRESOLVED rather
    than deriving a margin from a partial denominator."""
    cands = _revenue_candidates(facts)
    if not cands:
        return None, []
    tag = next(t for t in _REVENUE_TAG_PREFERENCE if t in cands)
    chosen = cands[tag]
    conflicts: list[str] = []
    for other, s in cands.items():
        if other == tag:
            continue
        for y in sorted(set(chosen.by_year) & set(s.by_year)):
            a, b = chosen.by_year[y], s.by_year[y]
            scale = max(abs(a), abs(b))
            if scale and abs(a - b) / scale > _TAG_CONFLICT_PCT:
                conflicts.append(f"FY{y}: {tag} {a / _USD_M:,.0f}M vs {other} {b / _USD_M:,.0f}M "
                                 f"({abs(a - b) / scale * 100:.0f}% apart)")
    return chosen, conflicts


# --- EDGAR source-bound extractors (fail-loud; a gap → None, never a fabricated zero) ----------
def _latest_dep_amort(facts: dict[str, Any]) -> tuple[float, str] | None:
    """Latest-FY consolidated D&A ($) → (value, source). Picks by VINTAGE, not by tag name.

    Was: prefer the combined tag whenever present, else the split pair. That preference is a
    landmine for any filer that CHANGED tags — the abandoned tag stays in companyfacts forever at
    its last reported value. FUBO's combined ``dep_amort`` last reported **$0.003M in FY2014**
    while its current split tags sum to **~$38.5M**; name-preference picked the twelve-year-old
    number, and it flowed straight into the anchor's EBITDA basis. (Queued 2026-07-21, closed here.)

    Now: build both candidates, and take the one whose fiscal period is FRESHER. Ties keep the
    combined tag, which is the filer's own single-line disclosure and needs no summation.

    The split pair still requires the SAME fiscal period on both legs — summing an FY2025
    depreciation into an FY2024 amortisation would fabricate a D&A that never existed."""
    # EVERY combined alias is considered, not just the first one carrying data. ``extract_points``
    # resolves aliases by ORDER — first-with-any-data wins — which is right for breadth and wrong
    # for vintage: an abandoned tag keeps its last value forever and still sorts first. EPAM's
    # `DepreciationDepletionAndAmortization` last reported FY2019 ($45.3M) while its
    # `DepreciationAndAmortization` reports FY2025 ($124.8M), and the FY2019 figure was sitting in
    # a committed anchor under a PENDING underwrite. The shared resolver is deliberately left
    # untouched (other consumers depend on its ordering); the vintage rule lives here.
    cands: list[tuple[Any, float, str]] = []
    for tag in CONCEPT_ALIASES["dep_amort"]:
        p = latest_annual(points_for_tag(facts, tag))
        if p:
            cands.append((p.period_end, p.value,
                          f"EDGAR companyfacts {tag} (combined, FY{p.fy or p.period_end.year})"))
    dep = latest_annual(points_for_tag(facts, "Depreciation"))
    am = latest_annual(points_for_tag(facts, "AmortizationOfIntangibleAssets"))
    # SAME fiscal period or nothing: summing an FY2025 depreciation into an FY2024 amortisation
    # would fabricate a D&A that never existed.
    if dep and am and dep.period_end == am.period_end:
        fy = dep.fy or dep.period_end.year
        cands.append((dep.period_end, dep.value + am.value,
                      f"EDGAR Depreciation + AmortizationOfIntangibleAssets (split, FY{fy})"))
    if not cands:
        return None
    freshest = max(c[0] for c in cands)
    # Ties keep the EARLIEST candidate at that vintage — alias order first, the summed split last,
    # because a filer's own single line needs no summation to be right.
    best = next(c for c in cands if c[0] == freshest)
    stale = [c for c in cands if c[0] < freshest]
    note = ""
    if stale:
        oldest = min(c[0] for c in stale)
        note = (f" — CHOSEN BY VINTAGE over {len(stale)} staler candidate(s), oldest "
                f"FY{oldest.year} ({(freshest - oldest).days // 365}y behind)")
    return best[1], best[2] + note


def _latest_fcf(facts: dict[str, Any]) -> tuple[float, str, str] | None:
    """Latest-FY free cash flow ($) → (value, basis, source). OCF − capex, both from the SAME
    fiscal period or nothing: an FY2025 OCF net of FY2024 capex is a number that never existed.

    ANNUAL basis on purpose, and the basis travels with the value. The R2 survival gate divides
    cash by this when it is negative, so an over-claimed 'LTM' would propagate straight into a
    runway the company does not have. Capex absent entirely → None (never a zero-capex FCF)."""
    ocf = latest_annual(extract_points(facts, "operating_cash_flow"))
    capex = latest_annual(extract_points(facts, "capex"))
    if not ocf or not capex or ocf.period_end != capex.period_end:
        return None
    fy = ocf.fy or ocf.period_end.year
    # capex is reported as a POSITIVE outflow in the cash-flow statement; subtract its magnitude
    return (ocf.value - abs(capex.value), f"latest FY{fy} (not LTM)",
            f"EDGAR companyfacts operating_cash_flow − capex (FY{fy}, same period)")


def _latest_point(facts: dict[str, Any], tag: str) -> ConceptPoint | None:
    """The most recent reported point for an explicit tag — the DISCRETE period, never a cumulative.

    For a DURATION concept — the diluted weighted-average share count has no instant context —
    ``latest_instant`` would only reach it through its balance-sheet fallback, so the selection is
    made explicit here rather than resting on that fallback.

    **THE SHORTEST SPAN WINS AT A GIVEN END DATE (2026-07-31).** The first cut sorted by
    ``(period_end, filed)`` alone, but a 10-Q tags the discrete quarter AND the year-to-date span
    with the SAME ``end`` and the SAME ``filed`` — so the tie broke arbitrarily and the docstring's
    promise of "the latest 10-Q's weighted average" was not what came back. MEASURED on the
    committed fleet: **4 of 11 names got a cumulative period** — SMPL a 272-day nine-month figure
    **4.16% above** its quarter (93,677,801 vs 89,940,680), FUBO a 181-day span −2.17%, BRBR +1.02%,
    CNXC +0.35% — and SMPL's committed record carries the basis string "diluted weighted-average
    (latest 10-Q)" over the nine-month number. A denominator whose stated basis is not what it is
    is the exact defect class the share-count work exists to close.

    Instant facts (``period_start is None``) sort as span 0, so at a shared end date an instant
    beats any duration — it cannot BE a cumulative, which is the thing being excluded. No caller
    currently mixes the two: the sole call site reads the diluted weighted average, a duration.

    **THIS ALSO MOVES THE COMMITTED ANCHOR.** ``anchor_base_value_per_share`` is ``equity ÷
    dil.value`` (below), and ``tagger._leverage`` / ``audit_r1.check_leverage`` read it — so a
    fresh recompute now diverges from committed JSON on SMPL (41.60→43.33, +4.16%), BRBR
    (55.41→55.97, +1.02%) and CNXC (62.33→62.55, +0.35%). The committed values are the ones
    carrying the defect; they are corrected by an anchor backfill, not by this function."""
    pts = points_for_tag(facts, tag)
    if not pts:
        return None

    def span(p: ConceptPoint) -> int:
        # instants sort as span 0 — they cannot be cumulative, so nothing is preferred over them
        return (p.period_end - p.period_start).days if p.period_start else 0

    # latest end date first, then the SHORTEST span at that end, then the latest filing
    return max(pts, key=lambda p: (p.period_end, -span(p), p.filed))


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
    # THE TWO TERMS MUST SHARE A BASIS (review of #531). `LongTermDebtNoncurrent` EXCLUDES current
    # maturities and is meant to be added to a current figure; bare `LongTermDebt` is the total and
    # already CONTAINS them. The alias order encodes that, and adding `debt_current` on top of the
    # total double-counts — VITL surfaced it: $30.0M total (2026-06-28) plus a $1.1M current figure
    # whose own tag stopped in 2020, summed under a "latest 10-Q" label. Which tag was served is the
    # only thing that says which basis this is, so read it rather than assume the pairing.
    ltd_is_total = ltd is not None and ltd.tag == "LongTermDebt"
    td = (ltd.value if ltd else 0.0) + (0.0 if ltd_is_total else (dc.value if dc else 0.0))
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


DQ_VENDOR_BRIDGE = "vendor_bridge"


def _bridge_inputs(mechanical: dict[str, Any], facts: dict[str, Any],
                   ciq: Any = None) -> dict[str, Any]:
    """Every SOURCE-BOUND scalar the block carries, gathered independently of whether R1 applies.

    Split out (2026-07-21, R2 cohort) because the R1 recipe and the FACTS are different things. The
    early returns below used to bail before touching EDGAR, so a name R1 cannot anchor — FUBO has
    no EV/EBITDA band at all, its multiples being NM on a loss-making trailing year — committed an
    anchor block with every input null. Those are exactly the names the R2 recipe underwrites, and
    exactly the facts it needs. An unusable RECIPE is not a reason to withhold the EVIDENCE."""
    da = _latest_dep_amort(facts)
    nd = _lease_inclusive_net_debt(facts)
    nd_val = nd[0] if nd else None
    dil = _latest_point(facts, _DILUTED_TAG)
    ltm_rev = _ltm_revenue_from_fs(mechanical)
    fcf = _latest_fcf(facts)

    # EDGAR-FIRST, ALWAYS. The vendor sheet fills a HOLE; it never overrides a primary filing.
    # A filled hole is stamped so the human can see which numbers are not EDGAR's — the manual CIQ
    # pull is the depth stage, and a bridge that silently mixed the two would hide that boundary.
    vendor: list[str] = []
    if ciq is not None and ciq.ok:
        if da is None and (v := ciq.value("d_and_a")) is not None:
            da = (v * _USD_M, f"CIQ Financials->Cash Flow (vendor basis; no EDGAR D&A tag) "
                              f"[{ciq.source_file} sha {ciq.source_sha256}]")
            vendor.append("d_and_a")
        if nd_val is None and (v := ciq.value("net_debt")) is not None:
            nd_val = v * _USD_M
            nd = (nd_val, f"CIQ classified balance sheet (vendor basis; EDGAR debt tags absent or "
                          f"under-captured) [{ciq.source_file} sha {ciq.source_sha256}]")
            vendor.append("net_debt")
        o, c = ciq.value("ocf"), ciq.value("capex")
        if fcf is None and o is not None and c is not None:
            fcf = ((o - abs(c)) * _USD_M, "trailing twelve months (vendor basis)",
                   f"CIQ Financials->Cash Flow operating cash flow less capital expenditure "
                   f"[{ciq.source_file} sha {ciq.source_sha256}]")
            vendor.append("ltm_fcf")
    return {
        "vendor_filled": vendor,
        "da": da, "nd_val": nd_val, "dil": dil, "ltm_rev": ltm_rev,
        "d_and_a": AnchorInput(
            value=(round(da[0] / _USD_M, 3) if da else None), unit="$M",
            basis="consolidated latest FY",
            source=(da[1] if da else "UNKNOWN — no D&A tag (combined or split)")),
        "net_debt": AnchorInput(value=(round(nd_val / _USD_M, 3) if nd_val is not None else None),
                                unit="$M", basis="lease-inclusive net debt (latest 10-Q)",
                                source=(nd[1] if nd and nd[1].startswith("CIQ")
                                        else ("EDGAR: " + nd[1]) if nd
                                        else "UNKNOWN — no debt/cash tag")),
        "diluted_shares": AnchorInput(value=(dil.value if dil else None), unit="shares",
                                      basis="diluted weighted-average (latest 10-Q)",
                                      source=(f"EDGAR {_DILUTED_TAG}" if dil
                                              else "UNKNOWN — no diluted WA tag")),
        "ltm_revenue": AnchorInput(value=(round(ltm_rev, 3) if ltm_rev is not None else None),
                                   unit="$M", basis="LTM revenue",
                                   source="committed financial_summary.annual (LTM)"),
        "ltm_fcf": AnchorInput(value=(round(fcf[0] / _USD_M, 3) if fcf else None), unit="$M",
                               basis=(fcf[1] if fcf else "free cash flow"),
                               source=(fcf[2] if fcf else
                                       "UNKNOWN — no aligned operating-cash-flow + capex pair")),
    }


_BRIDGE_FIELDS = ("d_and_a", "net_debt", "diluted_shares", "ltm_revenue", "ltm_fcf")


def _with_bridge(anchor: Anchor, bridge: dict[str, Any]) -> Anchor:
    """Attach the source-bound inputs to an anchor whose RECIPE did not resolve — the facts stand
    on their own footing, and the R2 cohort reads them from here.

    THE FLAG RIDES WITH THE FACTS (review of #534). ``DQ_VENDOR_BRIDGE`` used to be composed only
    on the full computation, PAST all four early returns — so a name whose recipe did not resolve
    carried CIQ-supplied numbers under a null ``data_quality``: FUBO's ``net_debt`` (null → 172.4)
    and MVST's ``d_and_a`` 33.201 / ``net_debt`` 65.2, each a workbook figure presented as though
    EDGAR had produced it. That understatement is worst exactly here, because the docstring above
    says the R2 cohort underwrites FROM these numbers. A vendor fill is a property of the FACTS,
    not of the recipe, so it is stamped wherever the facts are attached.
    """
    updates: dict[str, Any] = {k: bridge[k] for k in _BRIDGE_FIELDS}
    if bridge["vendor_filled"]:
        updates["data_quality"] = bg.compose_flag(anchor.data_quality, DQ_VENDOR_BRIDGE)
        updates["data_quality_detail"] = [
            *(anchor.data_quality_detail or []),
            "vendor bridge: " + ", ".join(bridge["vendor_filled"])
            + " supplied by the CIQ workbook because EDGAR had no usable tag",
        ]
    return anchor.model_copy(update=updates)


# --- the shared anchor computation (called by assembly AND the backfill writer) ----------------
def compute_anchor(mechanical: dict[str, Any], *, facts: dict[str, Any],
                   computed_at: datetime, ciq: Any = None) -> Anchor:
    """The R1 anchor from SOURCE-BOUND inputs. ``mechanical`` is the mechanical layer as a dict
    (``model_dump`` at assembly, committed JSON at backfill); ``facts`` is EDGAR companyfacts.

    Every input is cited and fail-loud: a missing own-history multiple → inapplicable; a
    non-positive margin → the R2 (revenue-anchored) hint; an incomplete value bridge → applicable
    False with the per-input source stamps telling the human exactly what's missing. The base value
    is the #150 block's EBITDA-basis math, never reimplemented here.

    An inapplicable RECIPE never suppresses the FACTS: every return path carries the source-bound
    EDGAR bridge (:func:`_bridge_inputs`), because the names R1 cannot anchor are precisely the
    ones the R2 recipe has to underwrite from those same numbers."""
    bridge = _bridge_inputs(mechanical, facts, ciq)
    mult = _own_history_multiple(mechanical)
    if mult is None:
        return _with_bridge(Anchor(
            recipe_hint=RECIPE_UNKNOWN, applicable=False, computed_at=computed_at,
            reason="own-history multiple missing (valuation.own_history.median absent)"), bridge)
    mult_median, mult_qtrs = mult["median"], mult["n_closes"]
    mult_span, mult_period, mult_dq = mult["span_years"], mult["periodicity"], mult["data_quality"]

    # margin — median operating margin over the years the TOTAL-revenue tag covers. EBIT is aligned
    # to exactly those years by margin_anchor (it intersects the two series), so the ratio is always
    # one consistent basis. Fewer valid years beats more invalid ones.
    rev_s, conflicts = _total_revenue_series(facts)
    if rev_s is None:
        return _with_bridge(Anchor(
            recipe_hint=RECIPE_UNRESOLVED, applicable=False, computed_at=computed_at,
            reason="no reliable total-revenue tag — refusing to derive a margin from a partial "
                   "denominator"), bridge)
    oi_s = mc.annual_series(facts, "operating_income")  # single alias (OperatingIncomeLoss)
    ma = mc.margin_anchor(rev_s, oi_s)
    margin_val, margin_years = ma.median, ma.n_years
    margin_source = (f"EDGAR companyfacts {oi_s.tag} / {rev_s.tag} — reported median over "
                     f"{margin_years} FY") if margin_val is not None else ""
    data_quality = DQ_REVENUE_TAG_CONFLICT if conflicts else None
    forced_weak = bool(conflicts)
    if margin_val is None:
        fb = _margin_from_fs(mechanical)
        if fb is not None:
            margin_val, margin_years = fb
            margin_source = "financial_summary (short history) — EBIT/Revenue reported median"
            forced_weak = True

    # Two DIFFERENT facts, never lumped (the same fail-loud discipline edgar/client.py applies to
    # its own UNKNOWNs): a margin we could not COMPUTE is not a margin we computed and found
    # non-positive. The first is a data gap; only the second is an R2 (revenue-anchored) signal.
    if margin_val is None:
        return _with_bridge(Anchor(
            recipe_hint=RECIPE_UNRESOLVED, applicable=False, computed_at=computed_at,
            reason=f"operating margin not computable — no fiscal year where both {oi_s.tag} and "
                   f"{rev_s.tag} report",
            data_quality=data_quality, data_quality_detail=conflicts), bridge)

    # POSITIVITY GUARD (minimal): a COMPUTED but non-positive margin → the revenue-anchored recipe.
    if margin_val <= 0:
        return _with_bridge(Anchor(
            recipe_hint=RECIPE_R2, applicable=False, computed_at=computed_at,
            reason="no positive operating margin over available history — needs revenue-anchored "
                   "recipe",
            data_quality=data_quality, data_quality_detail=conflicts), bridge)

    # remaining source-bound inputs — the SAME gather every other return path uses, never a
    # second copy of the extraction logic (two gatherers of one fact is the drift class this
    # repo keeps re-learning).
    da, nd_val, dil = bridge["da"], bridge["nd_val"], bridge["dil"]
    ltm_rev = bridge["ltm_rev"]

    # --- BAND GUARDS: does this multiple describe THIS company? (VITL, 2026-07-21) --------------
    # Two cross-checks sharing no input. The sheet-internal half already ran at parse time and rides
    # in on the band's data_quality; here the anchor supplies what only it holds — the RECORDED D&A
    # and EBITDA to test the sheet's implied figures against. A trip disqualifies the multiple: the
    # anchor publishes no base value off a denominator that provably is not this company's EBITDA.
    band_detail: list[str] = []
    da_flag, da_detail = bg.recorded_d_and_a_check(
        implied_d_and_a_margin=mult["implied_d_and_a_margin"], revenue=ltm_rev,
        recorded_d_and_a=(da[0] / _USD_M if da else None))
    band_detail += da_detail
    ltm_ebit = _ltm_ebit_from_fs(mechanical)
    # EVERY argument here is $M. ``nd_val`` and ``da`` arrive from EDGAR in DOLLARS, so both are
    # scaled — passing raw dollars beside a $M market cap silently inflates TEV by 1e6 and trips
    # the guard on every honest name (the #173 defect: latent because no committed artifact had
    # been re-backfilled, and the unit pin used net debt of ZERO, where 0 dollars == 0 $M).
    recon = bg.market_reconciliation(
        market_cap=_market_cap_from_mechanical(mechanical),
        net_debt=(nd_val / _USD_M if nd_val is not None else None),
        current_multiple=mult["current"],
        recorded_ebitda=((ltm_ebit + da[0] / _USD_M) if (ltm_ebit is not None and da) else None))
    band_detail += recon.detail if recon else []
    band_flag = bg.compose_flag(bg.compose_flag(mult_dq, da_flag), recon.flag if recon else None)
    # a PARSE-time incoherence (mult_dq) already disqualifies the band; so does either check here
    band_tripped = bool(da_flag) or bool(recon and recon.flag) or bg.BAND_INCOHERENT in (mult_dq
                                                                                         or "")

    # CONFIDENCE has a VALIDITY component, not just a count: any data-quality flag (or a fallback)
    # caps the margin leg — and therefore the overall — at "weak", however many years underlie it.
    m_conf = "firm" if (margin_years >= ANCHOR_FIRM_MIN_YEARS and not forced_weak) else "weak"
    # Multiple leg is firm on the WINDOW it spans + quarterly cadence — NOT the raw close count. A
    # band lacking span metadata (pre-refresh JSON), flagged periodicity_mismatch, or failing either
    # band guard cannot be firm.
    x_conf = ("firm" if (mult_span is not None and mult_span >= ANCHOR_FIRM_MIN_MULT_YEARS
                         and mult_period == "quarterly" and not mult_dq and not band_tripped)
              else "weak")
    overall = "firm" if (m_conf == "firm" and x_conf == "firm") else "weak"
    if data_quality and margin_source:
        margin_source += f" — CAPPED weak: {data_quality}"

    margin_blk = AnchorMargin(value=round(margin_val, 6), basis="operating margin (EBIT / revenue)",
                              source=margin_source, anchor_years=margin_years, confidence=m_conf)
    multiple_blk = AnchorMultiple(value=mult_median, history_quarters=mult_qtrs, confidence=x_conf)

    # anchor base — the #150 block's EBITDA-basis value math; needs a complete bridge AND a multiple
    # that survived the band guards. A tripped guard means the multiple's denominator is provably
    # not this company's EBITDA, so re-rating to it would publish a fabricated fundamental — the one
    # outcome the fail-loud rule exists to prevent. UNUSABLE until cleared, not merely "weak".
    base = ev_ebit = None
    if (da and nd_val is not None and dil and dil.value > 0 and ltm_rev is not None
            and not band_tripped):
        sv = mc.scenario_value(
            mc.Scenario(name="base", revenue=ltm_rev, margin=margin_val, multiple=mult_median,
                        source="anchor default", d_and_a=da[0] / _USD_M),
            net_debt=nd_val / _USD_M, shares=dil.value)
        base = round(sv.equity * _USD_M / dil.value, 4)
        ev_ebit = round(sv.ev_ebit, 4) if sv.ev_ebit is not None else None

    # a periodicity mismatch or a band-guard trip is its own fail-loud data-quality event; raise it
    # on the anchor (joining any revenue-tag conflict) so the flag rides with the number it taints.
    dq = bg.compose_flag(data_quality, band_flag)
    if bridge["vendor_filled"]:
        dq = bg.compose_flag(dq, DQ_VENDOR_BRIDGE)
    detail = list(conflicts)
    if bridge["vendor_filled"]:
        detail.append("vendor bridge: " + ", ".join(bridge["vendor_filled"])
                      + " supplied by the CIQ workbook because EDGAR had no usable tag")
    if mult_dq:
        detail.append(f"own_history multiple: {mult_dq} (periodicity {mult_period})")
    detail += band_detail
    reason = None
    if band_tripped:
        reason = ("own-history EV/EBITDA band failed a coherence guard — the multiple's "
                  "denominator is not this company's EBITDA; multiple UNUSABLE until re-sourced")
    elif base is None:
        reason = "R1 inputs incomplete — see per-input source stamps"
    return Anchor(
        recipe_hint=RECIPE_R1, applicable=base is not None, computed_at=computed_at, reason=reason,
        margin=margin_blk, multiple=multiple_blk,
        **{k: bridge[k] for k in _BRIDGE_FIELDS},
        anchor_base_value_per_share=base, anchor_ev_ebit=ev_ebit, overall_confidence=overall,
        data_quality=dq, data_quality_detail=detail)


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


def replace_valuation_fields(text: str, updates: dict[str, Any]) -> str:
    """Byte-preserving replace of one or more ``mechanical.valuation.<field>`` values in a committed
    dossier.json TEXT, leaving every OTHER field byte-for-byte identical.

    Takes the WHOLE cluster at once on purpose. ``own_history``, ``range_position``, ``ev_ebitda``
    and ``ev_ebitda_percentile_5y`` all derive from the SAME Multiples close series — the module
    guarantees they "can't drift" precisely because one loader feeds them. Refreshing one alone
    re-introduces the drift the guarantee exists to prevent (a band over 35 closes beside a string
    still saying "over 20 closes"), so the writer refuses to make that easy.

    A model round-trip drifts older-schema dossiers; a plain ``json.load``→``dump(indent=2,
    ensure_ascii=False)`` reproduces the committed bytes EXACTLY (verified), so it is the safe
    surgical path. Raises when a named field is absent (never silently no-ops)."""
    import json

    doc = json.loads(text)
    val = ((doc.get("mechanical") or {}).get("valuation"))
    if not isinstance(val, dict):
        raise ValueError("mechanical.valuation absent — refusing to refresh")
    for field, new in updates.items():
        if field not in val:
            raise ValueError(f"mechanical.valuation.{field} absent — refusing to refresh")
        val[field] = new
    out = json.dumps(doc, indent=2, ensure_ascii=False)
    return out + "\n" if text.endswith("\n") and not out.endswith("\n") else out


def preserve_operator_tag(old: Anchor | None, new: Anchor) -> tuple[Anchor, list[str]]:
    """An operator's hand re-tag OUTRANKS the machine's fresh proposal. Returns (anchor, notes).

    The backfill recomputes ``recipe_hint``/``reason`` from EDGAR on every run, so AORT's,
    CNXC's and VITL's hand re-tags — each carrying a judgment the machine cannot derive
    ("leveraged residual", "forward-margin question") — were one backfill away from silently
    vanishing. That was the queued overwrite defect; this closes it.

    Provenance is NOT recorded on the block, so the rule is deliberately the conservative one:
    ANY divergence from the committed hint keeps the COMMITTED value, rather than guessing which
    side was human. The machine's proposal is reported, never applied — the tagger is propose-only
    for the same reason.

    Only the RECIPE is preserved. Every computed VALUE (margin, multiple, the bridge, the base)
    refreshes normally: a re-tag is a judgment about which recipe fits, not a freeze on the
    arithmetic. A committed ``data_quality_detail`` that the fresh run does not reproduce is
    REPORTED rather than merged — silently unioning them would keep a root-cause narrative alive
    after a corrected re-pull had made it false."""
    notes: list[str] = []
    if old is None:
        return new, notes
    updates: dict[str, Any] = {}
    if old.recipe_hint and old.recipe_hint != new.recipe_hint:
        updates["recipe_hint"] = old.recipe_hint
        updates["reason"] = old.reason
        notes.append(f"PRESERVED operator recipe_hint {old.recipe_hint!r} "
                     f"(machine proposed {new.recipe_hint!r}) — reason kept verbatim")
    elif old.reason and old.reason != new.reason and old.applicable == new.applicable:
        updates["reason"] = old.reason
        notes.append(f"PRESERVED operator reason under the same hint {old.recipe_hint!r}")
    elif old.reason and old.reason != new.reason:
        # A REASON DOES NOT OUTLIVE THE STATE IT DESCRIBED (review of #534). This branch exists to
        # keep an OPERATOR's judgment, but it cannot tell one from a machine refusal — so when an
        # anchor that was refusing becomes applicable, the old text was a description of the
        # refusal and is now false. GOOGL and NFLX both gained a base (196.01 / 58.17, confidence
        # "firm") while keeping "R1 inputs incomplete — see per-input source stamps", and the
        # renderer prints the reason unconditionally: a refusal sentence under a table stating the
        # anchor applies. Applicability CHANGED, so the fresh reason wins and the drop is reported.
        notes.append(
            f"DROPPED stale reason {old.reason!r} — it described applicable={old.applicable} and "
            f"this run is applicable={new.applicable}; a reason never outlives its own state")
    fresh_detail = new.data_quality_detail or []
    dropped = [d for d in (old.data_quality_detail or []) if d not in fresh_detail]
    if dropped:
        notes.append(f"REVIEW: {len(dropped)} committed data_quality_detail line(s) are NOT "
                     f"reproduced by this run and will be replaced — first: {dropped[0][:80]}…")
    return (new.model_copy(update=updates) if updates else new), notes


def anchor_changed(old: Anchor | None, new: Anchor) -> bool:
    """Did anything MATERIAL change? ``computed_at`` alone must never rewrite a committed artifact —
    a re-validation pass that moves nothing should leave every dossier byte-identical."""
    if old is None:
        return True
    a, b = old.model_dump(mode="json"), new.model_dump(mode="json")
    a.pop("computed_at", None)
    b.pop("computed_at", None)
    return a != b


_ANCHOR_FIELD = '\n  "anchor": {'


def replace_anchor_block(text: str, anchor: Anchor) -> str:
    """Byte-preserving REPLACE of an existing trailing anchor block (or a plain insert when absent).

    ``anchor`` is always the LAST field the model serialises, so the existing block is stripped back
    to the previous field and re-appended — every other field keeps its committed bytes, exactly as
    the #158 insert does."""
    i = text.rfind(_ANCHOR_FIELD)
    if i == -1:
        return insert_anchor_block(text, anchor)
    head = text[:i].rstrip()
    if head.endswith(","):
        head = head[:-1].rstrip()          # drop the separator; insert_anchor_block re-adds it
    trailing = text[len(text.rstrip()):]
    return insert_anchor_block(f"{head}\n}}{trailing}", anchor)
