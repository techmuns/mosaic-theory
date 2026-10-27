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

import json
import re
import statistics as st
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from pydantic import BaseModel, ValidationError, computed_field

from vinci.dossier import band_guards as bg
from vinci.dossier import midcycle as mc
from vinci.edgar.concepts import (
    ANNUAL_STALE_DAYS,
    CONCEPT_ALIASES,
    ConceptPoint,
    annual_line,
    current_annual,
    current_pair,
    filer_fiscal_year,
    latest_annual,
    points_for_tag,
)
from vinci.edgar.net_debt import Basis, net_debt

if TYPE_CHECKING:  # ciq_balance imports schemas, which imports this module
    from vinci.dossier.ciq_balance import CiqFacts

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
# Two tags disagreeing by over `midcycle.TAG_CONFLICT_PCT` on one fiscal year are not two views of
# one number. Never silently pick: flag, use the preferred tag, and drop the years it may be the
# wrong one in (`midcycle.tag_disputes` — the threshold, the filing test and the direction live
# there, shared).
DQ_REVENUE_TAG_CONFLICT = "revenue_tag_conflict"
_DILUTED_TAG = "WeightedAverageNumberOfDilutedSharesOutstanding"
#: The same 10-Q's BASIC weighted average: diluted minus basic, over the one period both tag, is the
#: dilutive increment the filer itself counts (options and RSUs by treasury stock, convertibles
#: if-converted) — the only dilution figure this repo reads rather than estimates.
_BASIC_TAG = "WeightedAverageNumberOfSharesOutstandingBasic"
#: How far the point-in-time count may sit from that basic weighted average and still be the
#: per-share denominator. BELOW it is what a buyback does between the quarter's midpoint and the
#: cover date (IT −5.0% on $1,082M repurchased in the half — the deepest of the 19 pages carrying a
#: base value, measured 2026-10-21 on main 4b514dca's 27 pages). ABOVE it is issuance OR a count the
#: filer does not treat as outstanding for EPS — Lilly's cover reads 941.4M against 892.4M basic,
#: the gap its employee benefit trust holds (`CommonStockSharesHeldInEmployeeTrustShares`
#: 50,000,000, FY2025 10-K); PARR +3.3% — and the counts cannot tell those apart, so beyond the
#: margin neither is chosen. The other 16 pages with a base sit within −1.6% (SMPL) .. +0.7%
#: (GOOGL).
SHARES_BELOW_BASIC = 0.10
SHARES_ABOVE_BASIC = 0.02
_NOTE = (
    "ATTENTION FILTER, not a verdict. Even a firm anchor requires a full bear/base/bull 2:1 "
    "underwrite before any BUY. Spot and reward-to-base are computed live at triage, not stored "
    "here."
)


#: The gap, in operating-margin PERCENTAGE POINTS between the last twelve months and R1's median,
#: at which the page must say the mid-cycle assumption is doing heavy lifting. Set by face
#: validity, never by what it would have paid: five points of margin is five percent of revenue in
#: EBIT — half the profit of a business earning 10% — which is material on any reading.
MIDCYCLE_GAP_PTS = 5.0
#: THE TWO LEGS ARE DIFFERENT SOURCES, and this is where that is admitted rather than assumed. The
#: LTM is committed CIQ EBIT, which EXCLUDES unusual items; R1's median is EDGAR GAAP operating
#: income, which INCLUDES them. Measured on the fleet's latest common fiscal year when this shipped:
#: median disagreement 1.2 points, but CNXC 15.5, WLK 12.5, V 7.0 and SMPL 5.8 — impairments and
#: litigation charges GAAP carries and CIQ strips. An earlier draft of this note claimed the
#: threshold "sits well clear of the basis difference"; the fleet showed that false, so the flag
#: now REPORTS the same-year disagreement beside every gap instead of forcing the legs to match.
#: Within this many points the sources are said to agree; beyond it the page says which way the
#: difference pushes the gap — part of it may be basis, or the difference can only be hiding part
#: of it (WLK, below the median with CIQ above GAAP, is the second kind).
BASIS_AGREE_PTS = 2.0


class AnchorMidcycleGap(BaseModel, frozen=True):
    """R1's central assumption, stated where it is being STRETCHED — never a correction to it.

    R1 reverts the operating margin to its own history's median and re-rates it at the median
    multiple of the SAME history. The two are a matched pair, so the anchor is internally
    consistent: it answers "what is this worth if the business is still what it was?". That
    answer is only as good as the history, and when the last twelve months sit far from the
    median the page has to say so — because the machine cannot tell a structural change (a new
    mix, a new model: history misleads) from a cyclical excursion (a peak or a trough: reverting
    is right). That call is the human's.

    Measured when this shipped: 7 of the 16 R1 anchors on the committed fleet sit five or more
    points out, in BOTH directions — LLY +19.9, NFLX +18.2, PARR +10.5, AMZN +6.8, GOOGL +6.8
    above; WLK -8.7, BRBR -5.7 below. AMZN's is the instructive case: a 5.3% median margin paired
    with a 24.4x multiple earned on those same margins lands at $245.46 against a $245.96 price —
    not because the anchor is right, but because two stale inputs offset.

    ``read`` is the ONE sentence both renderers print, written once here; the structured values
    sit beside it for anything that computes."""

    ltm_margin: float                   # fraction — committed financial_summary EBIT / revenue
    median_margin: float                # fraction — the anchor's own margin.value
    median_years: int
    gap_pts: float                      # (ltm − median) × 100, signed
    # "above" | "below" the median — a margin's POSITION, named so: `direction` is a forbidden field
    # token (test_dossier_schema_has_no_conclusion_field), and the guard is right to be blunt
    ltm_side: str
    # the latest fiscal year BOTH sources report, and how far they disagree on it — the evidence for
    # how much of ``gap_pts`` could be basis rather than business. None when no common year exists.
    basis_year: int | None = None
    basis_gap_pts: float | None = None  # |CIQ EBIT margin − EDGAR GAAP margin| on basis_year
    # the two margins themselves on basis_year (fractions, signed), so WHICH WAY the sources
    # disagree is data, not prose — the sign decides whether the difference can account for part
    # of the gap or can only hide part of it (``midcycle_gap``). Set exactly when basis_year is.
    basis_gaap_margin: float | None = None
    basis_ciq_margin: float | None = None
    # True when R1's median itself came from the committed CIQ panel (EDGAR tags no operating
    # income — LLY), so both legs are ONE source and there is no basis difference to discount
    same_source: bool = False
    basis: str
    read: str


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


#: The block's R1 VALUE fields — R1's screen arithmetic. `recipe_hint`, `applicable`, `reason` and
#: the confidence/provenance fields are the block's identity, not R1's inputs.
R1_VALUE_FIELDS: tuple[str, ...] = (
    "multiple_basis", "margin", "multiple", "d_and_a", "net_debt", "diluted_shares",
    "shares_outstanding", "dilutive_increment", "ltm_revenue", "ltm_fcf",
    "anchor_base_value_per_share", "anchor_base_value_per_share_diluted", "midcycle_gap",
    "anchor_ev_ebit")


class ScenarioEligibility(BaseModel, frozen=True):
    """Whether the anchor's R1 value fields may feed a scenario valuation on THIS page."""

    eligible_for_scenario_valuation: bool
    fields: list[str]
    reason: str


def scenario_eligibility(recipe_hint: str | None, applicable: bool) -> ScenarioEligibility:
    """THE SCENARIO GATE'S OWN RULE, stated on the block (operator's schema correction, 2026-10-09).

    The anchor's value fields are R1's: an EV/EBITDA multiple, EDGAR net debt, a weighted-average
    diluted share count. They feed a scenario only through an R1-family record, and the gate
    (`propose.check_tier_agreement`) accepts one only where the tag is R1-family AND R1's anchor
    applies. Everywhere else — AMZN's R4 page, whose anchor still reads `multiple_basis: EV/EBITDA`
    beside `recipe_hint: R4_forward_ev_ebit` — they are audit, and say so here, so no consumer reads
    an R1 field as the active recipe's."""
    hint = recipe_hint or "unknown"
    if hint.startswith("R1") and applicable:
        why = (f"the active recipe is R1-family ({hint}) and R1's anchor applies — these fields "
               "are an R1 record's inputs (its template reads `d_and_a` and `net_debt` from here)")
        return ScenarioEligibility(eligible_for_scenario_valuation=True,
                                   fields=list(R1_VALUE_FIELDS), reason=why)
    if hint.startswith("R1"):
        why = (f"the page is tagged {hint} but R1's anchor declines (applicable=False) — the "
               "scenario gate refuses an R1 record here, so these fields are audit only")
    else:
        why = (f"the active recipe is {hint}; these are R1's screen arithmetic, kept for audit and "
               f"never an input to a {hint} valuation — the active basis is `valuation_basis`")
    return ScenarioEligibility(eligible_for_scenario_valuation=False,
                               fields=list(R1_VALUE_FIELDS), reason=why)


#: A hand re-tag's text marker, as the re-tags before 2026-10-22 wrote it into `reason`.
OPERATOR_RETAG_MARK = "OPERATOR RE-TAG"


class OperatorDecision(BaseModel, frozen=True):
    """THE OPERATOR'S RECIPE CALL, in its own block (operator ruling 2026-10-22: "keep my reasons in
    their own block").

    WHY A BLOCK. A re-tag lived in `reason`, the field the machine rewrites on every build, and the
    one rule both writers share (`preserve_operator_tag`) kept a hand reason only while the machine
    DISAGREED with the hand recipe — so a reason was lost exactly when the machine came to agree:
    AMZN's R4 re-tag in #700, #752 and #762 (restored by hand each time) and UBER's in #705 (never
    restored until this block). A field the machine writes cannot also be the human's.

    `reason` is VERBATIM — the operator's words, or the words written at the operator's instruction
    that the record names; `decided_by` says which, `source_ref` names the record. Every machine
    writer copies the block unchanged (`preserve_operator_tag`), and every write refuses to drop or
    alter it (`check_decision_write`); only `vinci anchor-retag` sets or retires one."""

    recipe: str
    reason: str
    decided_by: str
    decided_on: str                     # ISO date of the decision
    source_ref: str                     # the record (and commit) the decision is taken from
    # what the machine read when the decision was made — None where no record says
    machine_recipe_at_decision: str | None = None


class Anchor(BaseModel, frozen=True):
    """The R1 anchor block — source-bound, spot-independent. Optional on the Dossier so committed
    JSON predating it round-trips byte-identically. The UI does NOT ignore it: the page prints
    the base value and the reason, which is why `anchor-backfill` re-renders `dossier.md` after
    writing the JSON. An earlier version of this line claimed otherwise, and that claim is what
    left LLY's page reading $706.41 against a record saying 699.65 (review of #536).

    `scenario_eligibility` is COMPUTED from `recipe_hint` and `applicable` at every serialisation,
    so a hand re-tag that edits only the tag still writes a true tag (2026-10-09)."""

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
    # (2026-10-21) THE PER-SHARE DENOMINATOR, AND DILUTION BESIDE IT. The base value per share was
    # `equity ÷ diluted_shares` — a WEIGHTED AVERAGE over the latest quarter, which lags a buyback
    # by the quarter's pace (TJX: 1.117B against 1.100B outstanding on the cover, 1.5%) — while the
    # scenario template and `valuation_basis.exit_share_count` divide by the POINT-IN-TIME count
    # (item 24). The base now divides by that same count, and dilution is TESTED separately: the
    # filer's own diluted-minus-basic increment over the 10-Q's quarter, added to it.
    shares_outstanding: AnchorInput | None = None
    dilutive_increment: AnchorInput | None = None
    ltm_revenue: AnchorInput | None = None
    # (R2 cohort, 2026-07-21) Free cash flow — the SURVIVAL input. A negative value IS the burn the
    # R2 gate divides cash+facilities by, so its basis is stated on the block rather than assumed:
    # EDGAR reports a clean ANNUAL point, and summing XBRL quarterlies into a true LTM is where a
    # fabricated burn would come from (Q4 is usually FY-minus-9M, not a filed discrete quarter).
    # The R2 record takes this as a DEFAULT the analyst may override with a reason. Additive/opt.
    ltm_fcf: AnchorInput | None = None
    anchor_base_value_per_share: float | None = None   # the spot-independent fundamental
    # the same equity over point-in-time shares PLUS the dilutive increment — the dilution test;
    # absent when the filer tags no basic weighted average for the diluted figure's own period
    anchor_base_value_per_share_diluted: float | None = None
    # (2026-09-21) Set only when the last twelve months sit MIDCYCLE_GAP_PTS or more from the
    # median margin; absent otherwise, and DROPPED from the JSON when absent (see
    # `insert_anchor_block`), so an anchor that does not fire serialises byte-identically.
    midcycle_gap: AnchorMidcycleGap | None = None
    anchor_ev_ebit: float | None = None
    overall_confidence: str | None = None  # firm | weak (the WEAKER of margin/multiple)
    note: str = _NOTE
    # (2026-10-22) THE OPERATOR'S DECISION, beside the machine's read — never inside `reason`, which
    # is always the machine's own. `machine_recipe_hint` is the machine's recipe on the build that
    # wrote this block, kept only where a decision governs `recipe_hint` (so a divergence can be
    # SHOWN, never auto-resolved). Both are absent, never null, where no decision exists.
    operator_decision: OperatorDecision | None = None
    machine_recipe_hint: str | None = None
    # (2026-10-27) the two band guards' OUTCOMES — agree / differ / not_run — beside the flag they
    # set, which reads the same on a pass and when a guard could not run. Absent, never null,
    # where the guards were not reached (`band_guards.BandChecks`).
    band_checks: bg.BandChecks | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def scenario_eligibility(self) -> ScenarioEligibility:
        return scenario_eligibility(self.recipe_hint, self.applicable)


# --- committed-artifact readers (work on the mechanical layer as a dict) -----------------------
def ciq_ebitda_band(mechanical: dict[str, Any]) -> dict[str, Any] | None:
    """CIQ's committed own-history EV/EBITDA band dict — READ, never recomputed — or None. The ONE
    lookup of it: the R1 selector, the tagger and the R1 audit all come through here."""
    oh = ((mechanical.get("valuation") or {}).get("own_history") or {}).get("value")
    if not isinstance(oh, list):
        return None
    return next((r for r in oh if isinstance(r, dict) and "EBITDA" in str(r.get("metric", ""))),
                None)


def _band_read(ev: Any) -> dict[str, Any] | None:
    """One committed band dict → the fields the anchor judges a multiple leg on, or None: the
    median, close count, calendar span, periodicity label and any data-quality flag, so the leg is
    judged on the WINDOW it spans, not the raw point count.

    ``window_span_years``/``periodicity`` are optional (pre-metadata committed JSON lacks them): a
    band without them is treated as span-UNKNOWN → the leg cannot be firm (the safe read). Likewise
    ``implied_d_and_a_margin`` (the band-coherence read) — absent on pre-guard JSON, which simply
    leaves the recorded-D&A cross-check unrun rather than failing."""
    if not isinstance(ev, dict) or ev.get("median") is None:
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


#: The bridge basis of an anchor whose multiple is the ex-lease history (`lease_basis`).
NET_DEBT_EX_LEASE = "net debt excluding operating leases (latest 10-Q)"
#: Leases are material and the ex-lease history could not be built or reconciled: the multiple has
#: no basis R1's arithmetic can use, so the anchor refuses rather than fall back to CIQ's history.
DQ_LEASE_BASIS = "lease_basis_unresolved"
_CIQ_BAND_SOURCE = "valuation.own_history.median"
_EX_LEASE_SOURCE = ("valuation.lease_basis.ex_lease_band.median — TEV less operating leases over "
                    "reported LTM EBITDA, the basis of the EBITDA R1 prices")


class R1Band(NamedTuple):
    """WHICH EV/EBITDA HISTORY R1 READS, decided in ONE place (2026-10-19).

    The anchor and the scenario template must price the same multiple against the same bridge;
    two readers choosing separately is how an ex-lease net debt would meet a lease-inclusive
    multiple. ``band`` is the committed band dict (None: the page has none); ``refusal`` is set
    when rent is material and no usable ex-lease history exists — the multiple is then unusable,
    and ``band`` is CIQ's, kept only so the page can show what was refused."""

    band: dict[str, Any] | None
    ex_lease: bool
    refusal: str | None
    source: str
    materiality: str | None


def r1_multiple_band(mechanical: dict[str, Any]) -> R1Band:
    """The band R1 prices on, read from the committed mechanical layer.

    No `lease_basis` (a page assembled before it) or immaterial rent → CIQ's TEV/LTM EBITDA history,
    exactly as before. Material rent → the ex-lease history, or a refusal when it is absent."""
    val = mechanical.get("valuation") or {}
    ciq = ciq_ebitda_band(mechanical)
    lb = val.get("lease_basis")
    if not isinstance(lb, dict) or not lb.get("material"):
        return R1Band(ciq, False, None, _CIQ_BAND_SOURCE,
                      lb.get("materiality") if isinstance(lb, dict) else None)
    ex = lb.get("ex_lease_band")
    if isinstance(ex, dict) and ex.get("median") is not None:
        return R1Band(ex, True, None, _EX_LEASE_SOURCE, lb.get("materiality"))
    return R1Band(ciq, False, str(lb.get("refusal") or "no ex-lease history on the page"),
                  _CIQ_BAND_SOURCE, lb.get("materiality"))


def anchor_prices_ex_lease(anchor: dict[str, Any] | None) -> bool:
    """Whether a committed anchor is on the ex-lease side of the lease line: its multiple was read
    from the ex-lease history, or — on an anchor that stopped before the multiple leg (an R2 name)
    — its net debt leaves the operating leases out. The bridge is gathered on every path, and an
    R2 template pairs it with the band, so it carries the basis where the multiple cannot."""
    a = anchor or {}
    if a.get("multiple"):
        return str((a.get("multiple") or {}).get("source") or "").startswith(
            "valuation.lease_basis")
    return (a.get("net_debt") or {}).get("basis") == NET_DEBT_EX_LEASE


def lease_basis_mismatch(doc: dict[str, Any]) -> str | None:
    """Why this page's R1 anchor is NOT on the page's lease basis, or None when it is.

    THE ANCHOR IS WHAT R1 PRICES, so every reader that states or proposes R1's multiple keys off
    it — and this is the one test of whether that is safe. The lease basis is written by
    `lease_basis_transform` / `own-history-refresh` WITHOUT re-deriving the anchor, so between
    those and `anchor-backfill` the two can disagree; a consumer that read the page's choice there
    would pair an ex-lease multiple with the anchor's lease-inclusive net debt (review of #750).
    Four ways, each named: the anchor predates an ex-lease history; it is on one the page no longer
    has; it still prices a name whose lease basis now refuses R1; its multiple and net debt sit on
    different bases."""
    anchor = doc.get("anchor") or {}
    if not anchor.get("multiple") and not anchor.get("net_debt"):
        return None                 # nothing priced, nothing bridged — nothing to disagree
    sel = r1_multiple_band(doc.get("mechanical") or {})
    mult_ex = anchor_prices_ex_lease(anchor)
    nd_ex = ((anchor.get("net_debt") or {}).get("basis") == NET_DEBT_EX_LEASE)
    if anchor.get("multiple") and mult_ex != nd_ex:
        return (f"R1's multiple ({'ex-lease' if mult_ex else 'lease-inclusive'}) and net debt "
                f"({'ex-lease' if nd_ex else 'lease-inclusive'}) are on different lease bases")
    if sel.ex_lease and not mult_ex:
        return ("the anchor predates the page's lease basis — rent is material and the page "
                "carries the ex-lease history, but the anchor still prices CIQ's; re-derive the "
                "anchor (anchor-backfill)")
    if mult_ex and not sel.ex_lease:
        return ("the anchor prices an ex-lease history the page's lease basis no longer carries; "
                "re-derive the anchor (anchor-backfill)")
    if sel.refusal and anchor.get("applicable") and DQ_LEASE_BASIS not in str(
            anchor.get("data_quality") or ""):
        return ("the page's lease basis refuses R1 (" + sel.refusal + ") but the anchor still "
                "prices CIQ's mixed history; re-derive the anchor (anchor-backfill)")
    return None


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
    ``midcycle.TAG_CONFLICT_PCT``, they are not two views of one number — one is not total revenue.
    Record the disagreement (the caller flags ``data_quality`` and caps confidence), use the
    PREFERRED tag, and drop the years ``midcycle.tag_disputes`` cannot trust — the preferred figure
    was not filed with that year's operating income while the other was, or, the filing aside, it is
    the SMALLER: a flag beside a median that still read those years published WLK at 16.3% where its
    clean decade gives 9.8%. No candidate at all → ``(None, [])``, and the caller marks the anchor
    UNRESOLVED rather than deriving a margin from a partial denominator."""
    cands = _revenue_candidates(facts)
    if not cands:
        return None, []
    tag = next(t for t in _REVENUE_TAG_PREFERENCE if t in cands)
    conflicts, untrusted = mc.tag_disputes(cands[tag], [s for t, s in cands.items() if t != tag],
                                           mc.annual_series(facts, "operating_income"))
    return mc._without_years(cands[tag], untrusted), conflicts


# --- EDGAR source-bound extractors (fail-loud; a gap → None, never a fabricated zero) ----------
def _period_label(p: ConceptPoint) -> tuple[str, bool]:
    """(label, is_trailing) for a ~12-month flow point, read from ITS OWN PERIOD AND FORM.

    NEVER from ``p.fy``. companyfacts stamps each fact with the fiscal year of the FILING that
    carried it, not of the period the fact covers — and a 10-Q can carry a twelve-month column.
    Amazon's does: its quarterly cash-flow statement reports the trailing twelve months, so the
    freshest ~365-day operating-cash-flow point is **2025-07-01 → 2026-06-30** from the Q2-2026
    10-Q, stamped ``fy=2026``. The label built from ``fy`` read "latest FY2026 (not LTM)" — wrong
    twice: FY2026 has not ended, and a trailing window is exactly an LTM. The same stamp put
    "FY2026" on AMZN's D&A (75,200 over those twelve months; the FY2025 10-K says 65,756).

    The VALUES were never wrong — a trailing window is the fresher, better-matched figure, and it
    pairs with the anchor's LTM revenue over the same months. Only the claim about them was."""
    if (p.form or "").upper().startswith("10-Q"):
        return f"12m to {p.period_end.isoformat()}", True
    return f"FY{p.fy or p.period_end.year}", False


#: Why EDGAR has no D&A when no tag carries one at all: the text every committed page carries.
NO_DEP_AMORT = "no D&A tag (combined or split)"
SPLIT_DEP_AMORT = ("Depreciation", "AmortizationOfIntangibleAssets")
#: Why, when the filer tags the split but never a combined line: the split has nothing to continue.
NO_COMBINED_DEP_AMORT = ("no combined D&A line, so the split (Depreciation + "
                         "AmortizationOfIntangibleAssets) has no year to be checked against")


def _latest_dep_amort(facts: dict[str, Any]) -> tuple[float, str, str] | str:
    """Latest consolidated D&A ($) → (value, source, basis), or why EDGAR has none. The basis says
    what the twelve months ARE (`_period_label`): a fiscal year, or a filer's own trailing column.

    ONE READER, THE SCREEN'S (:func:`vinci.edgar.concepts.current_annual`, 2026-10-27). This used to
    pick among the combined aliases and the `Depreciation` + `AmortizationOfIntangibleAssets` split
    by VINTAGE alone, so a split FRESHER than every combined alias won however little of D&A it
    held: Ecovyst's split read $76.4M for FY2025 against a combined line of $89.4M in FY2024, a
    split that was $68.4M against that $89.4M in the one year both carry. Now:
    - the combined line is the alias walk's, which already skips an abandoned alias for a current
      one (MC1) — FUBO's FY2014 `DepreciationDepletionAndAmortization` ($0.003M) loses to its FY2024
      `DepreciationAndAmortization`, EPAM's FY2019 to its FY2025;
    - the split continues it only where the filer PROVED it is the line: the same figure, to 0.1%,
      in the latest year both carry, then unbroken (:func:`vinci.edgar.concepts.annual_line`);
    - and the year must be current: not reported past by the concept, and — stricter than the
      screen — the filer's NEWEST fiscal year. The anchor adds this D&A to LTM EBIT, so a year
      behind would make its EBITDA basis a two-year figure, the pairing #821 forbids. Measured
      2026-10-27 on 2,161 cached companyfacts: 1,620 anchor D&A years within 29 days of the filer's
      newest, one at 181 (a 10-Q's trailing column), none from 300 to 349, then 11 at 350–371
      (Ecovyst, Grocery Outlet, CSW Industries, Accenture among them) — refused.

    A refusal is the reason, never the stale combined figure: the CIQ bridge then supplies the
    workbook's D&A, stamped `vendor_bridge` (:func:`_bridge_inputs`). A filer that never tagged a
    combined line (CNXC, WERN) has nothing for a split to continue, so EDGAR has no D&A for it."""
    fy = filer_fiscal_year(facts)
    point, stale = current_annual(facts, "dep_amort", fy)
    if point is None:
        if stale:
            return stale.note
        if all(latest_annual(points_for_tag(facts, t)) for t in SPLIT_DEP_AMORT):
            return NO_COMBINED_DEP_AMORT
        return NO_DEP_AMORT
    if fy is not None and (lag := (fy.period_end - point.period_end).days) >= ANNUAL_STALE_DAYS:
        return (f"newest D&A is {point.tag} for the year to {point.period_end.isoformat()}, "
                f"{lag}d behind the filer's newest fiscal year ({fy.tag} to "
                f"{fy.period_end.isoformat()}) — the anchor adds D&A to LTM EBIT, so it must be "
                f"the newest year")
    lbl, trailing = _period_label(point)
    if point.tag not in CONCEPT_ALIASES["dep_amort"]:
        # a split continuing the combined line: name the line and where it stopped
        aliased = [q for q in annual_line(facts, "dep_amort").by_period.values()
                   if q.tag in CONCEPT_ALIASES["dep_amort"]]
        last = max(aliased, key=lambda q: q.period_end)
        source = (f"EDGAR {point.tag} (split, {lbl}; continues {last.tag}, which stops at the "
                  f"year to {last.period_end.isoformat()} — the same figure, to 0.1%, in the last "
                  f"year both carry)")
    else:
        source = f"EDGAR companyfacts {point.tag} (combined, {lbl})"
        # The vintage note survives the reader it was written for: which combined aliases the
        # filer left behind, and how far — so the next reader does not re-derive the choice.
        ends = [q.period_end for tag in CONCEPT_ALIASES["dep_amort"]
                if (q := latest_annual(points_for_tag(facts, tag)))]
        staler = [e for e in ends if e < point.period_end]
        if staler:
            oldest = min(staler)
            source += (f" — CHOSEN BY VINTAGE over {len(staler)} staler candidate(s), oldest "
                       f"FY{oldest.year} ({(point.period_end - oldest).days // 365}y behind)")
    basis = ("consolidated trailing twelve months (the filer's own 10-Q column)" if trailing
             else "consolidated latest FY")
    return point.value, source, basis


def _latest_fcf(facts: dict[str, Any]) -> tuple[float, str, str] | str:
    """Latest-FY free cash flow ($) → (value, basis, source), or why there is none. OCF − capex,
    both from the SAME fiscal period or nothing: an FY2025 OCF net of FY2024 capex is a number
    that never existed.

    ANNUAL basis on purpose, and the basis travels with the value. The R2 survival gate divides
    cash by this when it is negative, so an over-claimed 'LTM' would propagate straight into a
    runway the company does not have. Capex absent entirely → no FCF (never a zero-capex FCF).

    The year must be CURRENT (:func:`vinci.edgar.concepts.current_pair`, the pairing the screen's
    FCF sign reads). A same-period pair was served however old: FUBO's anchor carried
    "operating_cash_flow − capex (FY2024, same period)" while both concepts carried quarters a
    fiscal year past it. Capex may be read from a substitute the filer proved to be the same line
    (:func:`vinci.edgar.concepts.annual_line`), and the source then names its tag."""
    legs, stale = current_pair(facts, "operating_cash_flow", "capex")
    if legs is None:
        return stale.note if stale else "no aligned operating-cash-flow + capex pair"
    ocf, capex = legs
    lbl, trailing = _period_label(ocf)
    basis = (f"trailing {lbl} (the filer's own 10-Q column)" if trailing
             else f"latest {lbl} (not LTM)")
    via = ("" if capex.tag in CONCEPT_ALIASES["capex"]
           else f"; capex read from {capex.tag}, the filer's line once its capex tags stopped")
    # capex is reported as a POSITIVE outflow in the cash-flow statement; subtract its magnitude
    return (ocf.value - abs(capex.value), basis,
            f"EDGAR companyfacts operating_cash_flow − capex ({lbl}, same period{via})")


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

    (History: until 2026-10-21 ``anchor_base_value_per_share`` was ``equity ÷`` this figure, so
    the span fix moved committed anchors — SMPL +4.16%, BRBR +1.02%, CNXC +0.35%. The base now
    divides by the point-in-time count and this figure feeds the dilution test only.)"""
    pts = points_for_tag(facts, tag)
    if not pts:
        return None

    def span(p: ConceptPoint) -> int:
        # instants sort as span 0 — they cannot be cumulative, so nothing is preferred over them
        return (p.period_end - p.period_start).days if p.period_start else 0

    # latest end date first, then the SHORTEST span at that end, then the latest filing
    return max(pts, key=lambda p: (p.period_end, -span(p), p.filed))


def _lease_inclusive_net_debt(facts: dict[str, Any], *, ex_operating_leases: bool = False,
                              ) -> tuple[float | None, str] | None:
    """Lease-inclusive net debt ($): total debt + finance leases + operating leases − cash −
    short-term securities, every line at the latest balance sheet — the EV basis of
    :func:`vinci.edgar.net_debt.net_debt`, the ONE builder the screen's snapshot reads too.
    Returns ``(value_or_None, bridge)``; a refused reading (the tested under-capture witness, or a
    debt line absent from that balance sheet) is ``(None, why)`` — never a confident
    understatement, 'pull CIQ'. A filer with no cash line or no debt tag ever → None.

    ``ex_operating_leases`` drops the operating-lease leg (2026-10-19): the bridge of a multiple
    struck on TEV LESS operating leases (`lease_basis`) — the builder's LEVERAGE basis. The leg is
    still printed, as excluded, so the reader sees what the bridge leaves out and why.

    THE CASH LEG MATCHES THE MULTIPLE IT BRIDGES (§5.0 row 27, 2026-10-08). Every multiple this
    figure bridges is a CIQ TEV multiple, and CIQ's TEV nets cash AND short-term investments.
    Netting cash alone left GOOGL's anchor at net DEBT +$64,880M against CIQ's net CASH
    −$121,683M, the gap its $186,563M of marketable securities to the dollar.

    ONE DATE FOR EVERY LINE (§5.0 row 27 (1), 2026-10-19). Each leg used to be read at its own
    latest date, so a current-debt tag that stopped a quarter early still counted (WERN: $9M of
    debt not on its 2026-06-30 balance sheet, which CIQ's $889M does not carry either)."""
    nd = net_debt(facts)
    if nd is None or nd.nothing_to_read:
        return None
    if nd.borrowings is None and not nd.undercaptured:
        return None, f"{nd.refusal}; pull CIQ"
    sec = nd.securities
    td = nd.debt
    # A name without the line keeps its bridge text byte-for-byte: the leg is printed only where it
    # is netted, so a page that moves is a page whose number moved.
    sec_txt = (f" − short-term investments {sec.value / _USD_M:,.0f} "
               f"({sec.tag}, {sec.period_end.isoformat()})" if sec else "")
    debt_txt = (f"total debt incl. finance leases {td / _USD_M:,.0f}"
                if nd.borrowings is not None and nd.borrowings.finance_leases_inside
                else f"total debt {td / _USD_M:,.0f} + finance leases "
                     f"{nd.finance_leases / _USD_M:,.0f}")
    opl = nd.operating_leases / _USD_M
    if ex_operating_leases:
        # the ex-lease bridge IS the builder's LEVERAGE basis: operating leases out, finance in
        bridge = (
            f"{debt_txt} − cash {nd.cash.value / _USD_M:,.0f}{sec_txt} ($M); operating leases "
            f"{opl:,.0f} EXCLUDED — the multiple is struck on TEV less operating leases"
        )
    else:
        bridge = (
            f"{debt_txt} + operating leases {opl:,.0f} − cash "
            f"{nd.cash.value / _USD_M:,.0f}{sec_txt} ($M)"
        )
    if nd.undercaptured:
        return None, f"{bridge} — UNDER-CAPTURED: {nd.witness_text}; pull CIQ"
    return nd.value(Basis.LEVERAGE if ex_operating_leases else Basis.EV), bridge


DQ_VENDOR_BRIDGE = "vendor_bridge"

#: What the bridged D&A's twelve months ARE. `ciq_balance` reads the annual sheet's LAST column,
#: which is `LTM 12 months` on 33 of the 35 workbooks on file (2026-10-27; NKE's is a fiscal year,
#: MCK's carries no header) — it was labelled "consolidated latest FY" (review of #830).
CIQ_DA_BASIS = ("consolidated, the CIQ workbook's latest annual column — LTM where the workbook "
                "carries one, else its latest fiscal year (vendor basis)")
_NO_VENDOR_EX_LEASE = ("; CIQ's net debt is not substituted, because it carries the operating "
                       "leases this bridge excludes")


def _bridge_inputs(mechanical: dict[str, Any], facts: dict[str, Any],
                   ciq: Any = None, *, ex_lease: bool = False) -> dict[str, Any]:
    """Every SOURCE-BOUND scalar the block carries, gathered independently of whether R1 applies.

    Split out (2026-07-21, R2 cohort) because the R1 recipe and the FACTS are different things. The
    early returns below used to bail before touching EDGAR, so a name R1 cannot anchor — FUBO has
    no EV/EBITDA band at all, its multiples being NM on a loss-making trailing year — committed an
    anchor block with every input null. Those are exactly the names the R2 recipe underwrites, and
    exactly the facts it needs. An unusable RECIPE is not a reason to withhold the EVIDENCE.

    ``ex_lease`` (2026-10-19): the multiple is the ex-lease history (`lease_basis`), so net debt
    leaves the operating leases out — and the CIQ workbook may NOT fill a missing net debt, because
    CIQ's net debt carries those leases. A hole stays a hole rather than a mixed bridge."""
    got_da = _latest_dep_amort(facts)
    da = None if isinstance(got_da, str) else got_da
    nd = _lease_inclusive_net_debt(facts, ex_operating_leases=ex_lease)
    nd_val = nd[0] if nd else None
    dil = _latest_point(facts, _DILUTED_TAG)
    out, out_src = _shares_outstanding(mechanical, facts, dil)
    inc = _dilutive_increment(facts, dil) if out is not None else None
    ltm_rev = _ltm_revenue_from_fs(mechanical)
    got_fcf = _latest_fcf(facts)
    fcf = None if isinstance(got_fcf, str) else got_fcf

    # EDGAR-FIRST, ALWAYS. The vendor sheet fills a HOLE; it never overrides a primary filing.
    # A filled hole is stamped so the human can see which numbers are not EDGAR's — the manual CIQ
    # pull is the depth stage, and a bridge that silently mixed the two would hide that boundary.
    vendor: list[str] = []
    if ciq is not None and ciq.ok:
        if da is None and (v := ciq.value("d_and_a")) is not None:
            why = ("no EDGAR D&A tag" if got_da == NO_DEP_AMORT
                   else f"EDGAR D&A withheld — {got_da}")
            da = (v * _USD_M, f"CIQ Financials->Cash Flow (vendor basis; {why}) "
                              f"[{ciq.source_file} sha {ciq.source_sha256}]",
                  CIQ_DA_BASIS)
            vendor.append("d_and_a")
        if nd_val is None and not ex_lease and (v := ciq.value("net_debt")) is not None:
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
        "da": da, "nd_val": nd_val, "dil": dil, "ltm_rev": ltm_rev, "out": out,
        "inc": inc[0] if inc else None,
        "d_and_a": AnchorInput(
            value=(round(da[0] / _USD_M, 3) if da else None), unit="$M",
            basis=(da[2] if da else "consolidated latest FY"),
            source=(da[1] if da else f"UNKNOWN — {got_da}")),
        "net_debt": AnchorInput(value=(round(nd_val / _USD_M, 3) if nd_val is not None else None),
                                unit="$M", basis=(NET_DEBT_EX_LEASE if ex_lease
                                                  else "lease-inclusive net debt (latest 10-Q)"),
                                source=(nd[1] if nd and nd[1].startswith("CIQ")
                                        else ("EDGAR: " + nd[1]) if nd
                                        else "UNKNOWN — no debt/cash tag" + (
                                            _NO_VENDOR_EX_LEASE if ex_lease else ""))),
        "diluted_shares": AnchorInput(value=(dil.value if dil else None), unit="shares",
                                      basis="diluted weighted-average (latest 10-Q)",
                                      source=(f"EDGAR {_DILUTED_TAG}" if dil
                                              else "UNKNOWN — no diluted WA tag")),
        "shares_outstanding": AnchorInput(
            value=out, unit="shares",
            basis="point-in-time shares outstanding — the per-share denominator (item 24)",
            source=out_src),
        "dilutive_increment": AnchorInput(
            value=(inc[0] if inc else None), unit="shares",
            basis="diluted less basic weighted average over the latest 10-Q quarter — the "
                  "dilution test",
            source=(inc[1] if inc else
                    "UNKNOWN — the 10-Q tags no basic weighted average for the diluted figure's "
                    "own period" if out is not None else
                    "not tested — the base divides the diluted weighted average, which already "
                    "counts it")),
        "ltm_revenue": AnchorInput(value=(round(ltm_rev, 3) if ltm_rev is not None else None),
                                   unit="$M", basis="LTM revenue",
                                   source="committed financial_summary.annual (LTM)"),
        "ltm_fcf": AnchorInput(value=(round(fcf[0] / _USD_M, 3) if fcf else None), unit="$M",
                               basis=(fcf[1] if fcf else "free cash flow"),
                               source=(fcf[2] if fcf else f"UNKNOWN — {got_fcf}")),
    }


_BRIDGE_FIELDS = ("d_and_a", "net_debt", "diluted_shares", "shares_outstanding",
                  "dilutive_increment", "ltm_revenue", "ltm_fcf")


#: The refusal's prefix — the renderers print the sentence after it as the page's reason.
SHARES_REFUSED = "REFUSED — "


def _basic_point(facts: dict[str, Any], dil: ConceptPoint | None) -> ConceptPoint | None:
    """The basic weighted average over the diluted figure's OWN period (same start, same end)."""
    if dil is None:
        return None
    basic = [p for p in points_for_tag(facts, _BASIC_TAG)
             if p.period_end == dil.period_end and p.period_start == dil.period_start]
    return max(basic, key=lambda p: p.filed) if basic else None


def _span(p: ConceptPoint) -> str:
    return f"{p.period_start.isoformat() if p.period_start else '?'}..{p.period_end.isoformat()}"


def _shares_outstanding(mechanical: dict[str, Any], facts: dict[str, Any],
                        dil: ConceptPoint | None) -> tuple[float | None, str]:
    """(count, source) — the page's own POINT-IN-TIME count, `stock_info.shares_out`: the count its
    market cap is struck on. Read, never re-derived, so the anchor and the CMP cannot disagree about
    how many shares there are — and USED only where the filer's own basic weighted average over the
    latest 10-Q quarter corroborates it (`SHARES_BELOW_BASIC` / `SHARES_ABOVE_BASIC`). A count the
    filer's EPS does not recognise is refused, never divided by: the base then stays on the diluted
    weighted average and the refusal is the page's to state (None, "REFUSED — …")."""
    so = ((mechanical.get("stock_info") or {}).get("shares_out") or {})
    v = so.get("value") if so.get("status") == "present" else None
    if not (isinstance(v, (int, float)) and v > 0):
        return None, f"UNKNOWN — stock_info.shares_out absent ({so.get('note') or 'no count'})"
    src = f"mechanical.stock_info.shares_out ({so.get('source_ref')})"
    b = _basic_point(facts, dil)
    if b is None or b.value <= 0:
        return None, (f"{SHARES_REFUSED}the point-in-time count {v:,.0f} cannot be checked: the "
                      "filer tags no basic weighted average for its latest diluted figure's "
                      f"period. {src}")
    gap = v / b.value - 1
    # UNSIGNED, with its direction in words: the screening block carries no signed percentage
    # (test_parity_pins — a "+x%" there reads as an implied upside against spot)
    where = (f"{abs(gap):.1%} {'above' if gap > 0 else 'below'} the filer's basic weighted "
             f"average {b.value:,.0f} ({_span(b)})")
    if -SHARES_BELOW_BASIC <= gap <= SHARES_ABOVE_BASIC:
        return float(v), f"{src}; {where}"
    why = ("issuance or shares the filer does not count as outstanding for EPS (an employee "
           "benefit trust, unvested restricted stock), which the counts cannot tell apart"
           if gap > 0 else "more than a quarter's buyback pace explains")
    return None, (f"{SHARES_REFUSED}the point-in-time count {v:,.0f} sits {where} — {why}. "
                  f"{src}")


def _dilutive_increment(facts: dict[str, Any], dil: ConceptPoint | None,
                        ) -> tuple[float, str] | None:
    """(shares, source) — diluted less basic weighted average over the diluted figure's OWN period
    (same start, same end), or None. Never two periods mixed: a basic count from another span
    differs by the buyback pace, the very error this field keeps apart from dilution."""
    b = _basic_point(facts, dil)
    if dil is None or b is None:
        return None
    span = _span(b)
    return (max(0.0, dil.value - b.value),
            f"EDGAR {_DILUTED_TAG} {dil.value:,.0f} − {_BASIC_TAG} {b.value:,.0f} ({span})")


#: What the denominator IS, as both consumers print it.
SHARES_OUTSTANDING_LABEL = "shares outstanding"
SHARES_DILUTED_WA_LABEL = ("diluted weighted-average shares (the point-in-time count is refused "
                           "against the filer's basic weighted average)")


def share_denominator(mechanical: dict[str, Any], facts: dict[str, Any],
                      ) -> tuple[float, str] | None:
    """(count, label) — THE per-share denominator, the one rule for the anchor's base and for R1's
    ex-lease multiple at the page's price, so a price and a value are never struck on two counts:
    the corroborated point-in-time count, else the diluted weighted average, else None."""
    dil = _latest_point(facts, _DILUTED_TAG)
    out, _src = _shares_outstanding(mechanical, facts, dil)
    if out is not None:
        return out, SHARES_OUTSTANDING_LABEL
    if dil is not None and dil.value > 0:
        return dil.value, SHARES_DILUTED_WA_LABEL
    return None


def per_share_shares(anchor: dict[str, Any]) -> float | None:
    """THE COUNT `anchor_base_value_per_share` IS DIVIDED BY — the one reading for every consumer
    that rebuilds the anchor's equity (`tagger._leverage`, `audit_r1.check_leverage`). The
    point-in-time count since 2026-10-21; an anchor written before it carries only the diluted
    weighted average, which is what its base was struck on."""
    for key in ("shares_outstanding", "diluted_shares"):
        v = (anchor.get(key) or {}).get("value")
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    return None


def lease_inclusive_net_debt(facts: dict[str, Any]) -> tuple[float | None, str | None]:
    """($M, source) — EDGAR's net debt WITH the operating leases, whatever basis R1 prices on.

    THE CROSS-CHECK BESIDE A CIQ TEV IS LEASE-INCLUSIVE BY CONSTRUCTION (review of #750). CIQ's
    TEV claims carry the operating leases, so the EDGAR figure set beside them (`ev_bridge`) must
    too. It used to be "the anchor's" net debt, which was the same number until R1 moved to the
    ex-lease bridge on lease-material names; reading the anchor there would set AMZN's $22,687M
    beside CIQ claims that hold $96B of leases."""
    nd = _lease_inclusive_net_debt(facts)
    if nd is None:
        return None, "UNKNOWN — no debt/cash tag"
    return (round(nd[0] / _USD_M, 3) if nd[0] is not None else None), "EDGAR: " + nd[1]


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
def basis_check(gaap_by_year: dict[int, float],
                mechanical: dict[str, Any]) -> tuple[int, float, float] | None:
    """(year, gaap_margin, ciq_margin) on the LATEST fiscal year both sources report, else None.

    GAAP from R1's own margin series (EDGAR, keyed by the fiscal year's end); CIQ from the
    committed annual panel's ACTUAL columns ("FY25" / "FY25 (R)"), estimates skipped. No common year
    → None, and the page says the two could not be tested against each other rather than guessing.
    """
    ann = _fs_annual(mechanical)
    cols = ann.get("columns") or []
    ise = ann.get("is_estimate") or []
    rows = {r.get("label"): (r.get("values") or []) for r in ann.get("rows") or []}
    ebit, rev = rows.get("EBIT ($M)") or [], rows.get("Revenue ($M)") or []
    ciq: dict[int, float] = {}
    for i, col in enumerate(cols):
        # the LABEL only names the year ("FY25", "FY25 (R)", "FY26E"); whether a column is an
        # estimate is read from the STRUCTURED is_estimate flag, never from its "E" — a display
        # suffix is not a fact, and the two only agree until an export writes one without the other
        m = re.fullmatch(r"FY(\d\d)(?:E| \(R\))?", str(col).strip())
        if (m is None or (i < len(ise) and ise[i]) or i >= len(ebit) or i >= len(rev)
                or ebit[i] is None or not rev[i]):
            continue
        ciq[2000 + int(m.group(1))] = ebit[i] / rev[i]
    common = sorted(set(ciq) & set(gaap_by_year))
    if not common:
        return None
    y = common[-1]
    return y, gaap_by_year[y], ciq[y]


def _margin_words(x: float) -> str:
    """A margin as the screening block may print it: a loss in WORDS, never a signed percentage.

    That block is fenced against any signed percentage (`test_parity_pins`: one there reads as an
    upside against spot), and a negative margin formatted ``:.1%`` is exactly that token — WLK's
    FY2025 printed "GAAP -14.1% vs CIQ -1.6%" and turned the fence red on the first artifact pass
    that carried the flag."""
    return f"{x:.1%}" if x >= 0 else f"a {abs(x):.1%} loss"


def midcycle_gap(median_margin: float | None, median_years: int | None, *,
                 ltm_ebit: float | None, ltm_revenue: float | None,
                 median_source: str = "",
                 basis: tuple[int, float, float] | None = None,
                 median_from_ciq: bool = False) -> AnchorMidcycleGap | None:
    """The mid-cycle gap when it is large enough to state (``MIDCYCLE_GAP_PTS``), else None.

    Needs both legs: a margin R1 actually computed, and an LTM EBIT over a positive LTM revenue.
    Either missing → None, which is "nothing to say", not "no gap" — the page stays silent rather
    than implying the assumption was checked and held."""
    if median_margin is None or ltm_ebit is None or not ltm_revenue or ltm_revenue <= 0:
        return None
    ltm = ltm_ebit / ltm_revenue
    # DECIDED ON THE SAME ROUNDING IT IS STORED AT. Unrounded, (0.15 − 0.10) × 100 is
    # 4.999999999999999 and a gap that is five points on any human reading stayed silent — caught
    # by the boundary pin, not by inspection.
    gap = round((ltm - median_margin) * 100, 2)
    if abs(gap) < MIDCYCLE_GAP_PTS:
        return None
    yrs = f"{median_years}-year" if median_years else "historical"
    if gap > 0:
        # "an R1 value", never "this value": the flag also rides on an R1 anchor that publishes NO
        # value (GOOGL, NFLX — inputs incomplete), and "this value" there points at nothing
        tail = ("so an R1 value answers what the business is worth if it is still what it was. If "
                "the gap is STRUCTURAL — a changed mix or model — that history understates it; if "
                "it is a cyclical PEAK, reverting is right.")
        where = "ABOVE"
    else:
        tail = ("so an R1 value assumes a recovery to what the business was. If the decline is "
                "STRUCTURAL, that history overstates it; if it is a cyclical TROUGH, expecting "
                "recovery is right.")
        where = "BELOW"
    med_src = "CIQ EBIT" if median_from_ciq else "EDGAR GAAP operating income"
    if median_from_ciq:
        bsent = (" Both legs are CIQ EBIT — EDGAR carries no operating-income tag for this filer, "
                 "so R1's median already came from the committed panel — and there is no source "
                 "difference to discount.")
        by, bgap, g_m, c_m = None, None, None, None
    elif basis is None:
        bsent = (" The two sources — CIQ EBIT for the twelve months, EDGAR GAAP operating "
                 "income for the median — share no fiscal year to test against each other.")
        by, bgap, g_m, c_m = None, None, None, None
    else:
        by, g_m, c_m = basis
        # decided on the SAME rounding it is stored at (the gap_pts rule above): unrounded, 1.996
        # read "agree" while the record stored basis_gap_pts=2.0, which the threshold calls "differ"
        bgap = round(abs(c_m - g_m) * 100, 2)
        if bgap < BASIS_AGREE_PTS:
            bsent = (f" The two sources agree within {bgap:.1f} points on FY{by}, so the gap is "
                     f"the business, not the source.")
        else:
            # WHICH WAY THE DIFFERENCE PUSHES THE SHOWN GAP. The twelve months are CIQ and the
            # median GAAP, so where CIQ reads above GAAP the shown gap is pushed UP: that can
            # manufacture part of a gap ABOVE, and can only NARROW a gap BELOW — and the mirror
            # where CIQ reads below. The first draft said "part of this gap may be basis" either
            # way, and WLK's page (8.7 points BELOW, CIQ 12.5 points ABOVE GAAP on FY2025) told
            # the reader to discount a gap that measures 8.8 points with CIQ on both legs and
            # 20.8 with GAAP on both.
            ciq_above = c_m > g_m
            if ciq_above:
                why = ("GAAP carries charges CIQ's EBIT excludes, and R1's median sits on the "
                       "GAAP side")
                pull = "pulls the median down toward the twelve months"
            else:
                why = "CIQ's EBIT reads below GAAP, and the twelve months sit on the CIQ side"
                pull = "pulls the twelve months down toward the median"
            bsent = (f" On FY{by} the two sources differ by {bgap:.1f} points (GAAP "
                     f"{_margin_words(g_m)} vs CIQ {_margin_words(c_m)}): {why}")
            if ciq_above == (gap > 0):
                bsent += ", so part of this gap may be basis, not business."
            else:
                bsent += (f" — which {pull}, so the difference narrows this gap rather than "
                          f"creating it: no reason to discount it, and if anything it "
                          f"understates it.")
    read = (f"The last twelve months' operating margin of {_margin_words(ltm)} (CIQ EBIT) sits "
            f"{abs(gap):.1f} points {where} the {yrs} median of {_margin_words(median_margin)} "
            f"({med_src}) that R1 reverts to. R1 pairs that median with the median multiple "
            f"from the same history, {tail}{bsent}")
    basis_txt = (f"LTM: committed financial_summary EBIT ÷ revenue (last actual column); median: "
                 f"{median_source or 'the anchor margin'}; flagged at ≥{MIDCYCLE_GAP_PTS:g} "
                 f"points; sources said to agree within {BASIS_AGREE_PTS:g}")
    return AnchorMidcycleGap(
        ltm_margin=round(ltm, 6), median_margin=round(median_margin, 6),
        median_years=int(median_years or 0), gap_pts=round(gap, 2),
        ltm_side="above" if gap > 0 else "below", basis_year=by,
        basis_gap_pts=(round(bgap, 2) if bgap is not None else None),
        basis_gaap_margin=(round(g_m, 6) if g_m is not None else None),
        basis_ciq_margin=(round(c_m, 6) if c_m is not None else None),
        same_source=median_from_ciq, basis=basis_txt, read=read)


def ciq_bridge(bundle: Any, ticker: str) -> tuple[CiqFacts | None, str | None]:
    """The CIQ facts the bridge may fill a hole from, and a line saying what was read — ONE read
    for BOTH write paths (STATE row 27 (7), 2026-10-27).

    `anchor-backfill` handed `compute_anchor` the workbook's cross-checked facts and assembly
    handed it none, so a fresh assembly wrote UNKNOWN for every input only CIQ supplies, and each
    pass had to backfill it back (GOOGL's D&A and ORKA's net debt on the 2026-10-26 pass;
    `docs/records/2026-10-27-assembly-anchor-reads-the-ciq-bridge.md`). A sheet that failed a
    coherence check is handed on as None, never its surviving facts (`ciq_balance` refuses rather
    than degrades); two exports of one kind raise, because that is not "no workbook" and the
    operator clears it first."""
    from vinci.dossier.ciq import CiqAmbiguousError
    from vinci.dossier.ciq_balance import extract

    try:
        ciq = extract(bundle, ticker)
    except CiqAmbiguousError:
        raise
    except Exception as exc:  # noqa: BLE001 — no workbook is normal; EDGAR-only then
        return None, f"no CIQ bridge ({type(exc).__name__})"
    if not ciq.ok:
        return None, f"CIQ extraction REFUSED — {'; '.join(ciq.failures)}"
    if not ciq.facts:
        return ciq, None
    return ciq, f"CIQ bridge available ({len(ciq.facts)} facts, {len(ciq.checks)} checks passed)"


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
    # ONE choice of history, read by the bridge too: an ex-lease multiple takes an ex-lease bridge
    sel = r1_multiple_band(mechanical)
    bridge = _bridge_inputs(mechanical, facts, ciq, ex_lease=sel.ex_lease)
    mult = _band_read(sel.band)
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
                     f"{margin_years} FY{ma.excluded_note}") if margin_val is not None else ""
    data_quality = DQ_REVENUE_TAG_CONFLICT if conflicts else None
    forced_weak = bool(conflicts)
    median_from_ciq = False
    if margin_val is None:
        fb = _margin_from_fs(mechanical)
        if fb is not None:
            margin_val, margin_years = fb
            margin_source = "financial_summary (short history) — EBIT/Revenue reported median"
            forced_weak = True
            median_from_ciq = True

    # Two DIFFERENT facts, never lumped (the same fail-loud discipline edgar/client.py applies to
    # its own UNKNOWNs): a margin we could not COMPUTE is not a margin we computed and found
    # non-positive. The first is a data gap; only the second is an R2 (revenue-anchored) signal.
    if margin_val is None:
        return _with_bridge(Anchor(
            recipe_hint=RECIPE_UNRESOLVED, applicable=False, computed_at=computed_at,
            reason=f"operating margin not computable — no fiscal year where both {oi_s.tag} and "
                   f"{rev_s.tag} report{ma.excluded_note}",
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
    da, nd_val = bridge["da"], bridge["nd_val"]
    ltm_rev = bridge["ltm_rev"]

    # --- BAND GUARDS: does this multiple describe THIS company? (VITL, 2026-07-21) --------------
    # Two cross-checks sharing no input. The sheet-internal half already ran at parse time and rides
    # in on the band's data_quality; here the anchor supplies what only it holds — the RECORDED D&A
    # and EBITDA to test the sheet's implied figures against. A trip disqualifies the multiple: the
    # anchor publishes no base value off a denominator that provably is not this company's EBITDA.
    band_detail: list[str] = []
    if sel.ex_lease:
        # the sheet-coherence read interrogates CIQ's Multiples ratios — the series this history
        # REPLACES — so it is not this band's test; the market reconciliation below is, because it
        # takes the ex-lease current multiple with the ex-lease bridge. What CIQ's own band said
        # is still stated, so a reader can see what the rebuild set aside (review of #750).
        band_detail.append("recorded-D&A check not run: it tests CIQ's Multiples-sheet ratios, "
                           "which the ex-lease history does not use")
        ciq_dq = (ciq_ebitda_band(mechanical) or {}).get("data_quality")
        if ciq_dq:
            band_detail.append(f"CIQ's own EV/EBITDA band is flagged {ciq_dq} — not the history "
                               "R1 prices")
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
    # material rent with no usable ex-lease history: CIQ's history cannot price reported EBITDA
    lease_refused = sel.refusal is not None
    if lease_refused:
        band_flag = bg.compose_flag(band_flag, DQ_LEASE_BASIS)
    # a PARSE-time incoherence (mult_dq) already disqualifies the band; so does either check here
    band_tripped = (bool(da_flag) or bool(recon and recon.flag) or lease_refused
                    or bg.BAND_INCOHERENT in (mult_dq or ""))

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
    multiple_blk = AnchorMultiple(value=mult_median, history_quarters=mult_qtrs, confidence=x_conf,
                                  source=sel.source)

    # anchor base — the #150 block's EBITDA-basis value math; needs a complete bridge AND a multiple
    # that survived the band guards. A tripped guard means the multiple's denominator is provably
    # not this company's EBITDA, so re-rating to it would publish a fabricated fundamental — the one
    # outcome the fail-loud rule exists to prevent. UNUSABLE until cleared, not merely "weak".
    base = base_diluted = ev_ebit = None
    # THE DENOMINATOR: the corroborated point-in-time count, else the diluted weighted average the
    # base was struck on before 2026-10-21 — a refused count never silently becomes the divisor.
    out, inc, dil = bridge["out"], bridge["inc"], bridge["dil"]
    shares = out or (dil.value if dil and dil.value > 0 else None)
    if (da and nd_val is not None and shares and ltm_rev is not None and not band_tripped):
        sv = mc.scenario_value(
            mc.Scenario(name="base", revenue=ltm_rev, margin=margin_val, multiple=mult_median,
                        source="anchor default", d_and_a=da[0] / _USD_M),
            net_debt=nd_val / _USD_M, shares=shares)
        base = round(sv.equity * _USD_M / shares, 4)
        if out and inc is not None:
            base_diluted = round(sv.equity * _USD_M / (out + inc), 4)
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
    if sel.ex_lease or lease_refused:
        detail.append(f"lease basis: {sel.materiality}")
    detail += band_detail
    reason = None
    if lease_refused:
        reason = ("rent is material and the ex-lease EV/EBITDA history is not usable — "
                  f"{sel.refusal}. CIQ's TEV/LTM EBITDA history puts operating leases in TEV and "
                  "rent back in EBITDA since ASC 842 and did neither before, so its median cannot "
                  "price reported EBITDA; multiple UNUSABLE until the ex-lease history is built")
    elif band_tripped:
        reason = ("own-history EV/EBITDA band failed a coherence guard — the multiple's "
                  "denominator is not this company's EBITDA; multiple UNUSABLE until re-sourced")
    elif base is None:
        reason = "R1 inputs incomplete — see per-input source stamps"
    return Anchor(
        recipe_hint=RECIPE_R1, applicable=base is not None, computed_at=computed_at, reason=reason,
        margin=margin_blk, multiple=multiple_blk,
        **{k: bridge[k] for k in _BRIDGE_FIELDS},
        anchor_base_value_per_share=base, anchor_base_value_per_share_diluted=base_diluted,
        anchor_ev_ebit=ev_ebit, overall_confidence=overall,
        data_quality=dq, data_quality_detail=detail,
        band_checks=bg.BandChecks(
            recorded_d_and_a=bg.recorded_d_and_a_outcome(
                implied_d_and_a_margin=mult["implied_d_and_a_margin"], revenue=ltm_rev,
                recorded_d_and_a=(da[0] / _USD_M if da else None)),
            market_reconciliation=bg.reconciliation_outcome(recon),
            d_and_a_source=(("ciq" if "d_and_a" in bridge["vendor_filled"] else "edgar")
                            if da else None)),
        midcycle_gap=midcycle_gap(margin_val, margin_years, ltm_ebit=ltm_ebit,
                                  ltm_revenue=ltm_rev, median_source=margin_source,
                                  basis=(None if median_from_ciq
                                         else basis_check(ma.by_year, mechanical)),
                                  median_from_ciq=median_from_ciq))


def anchor_absent_fields(anchor: Anchor) -> dict[str, Any]:
    """Optional anchor keys written ABSENT, never null, when unset — so a page whose anchor does not
    carry them serialises without them (`midcycle_gap` set only when it fires; the dilution test's
    value only where the filer tags both weighted averages; a decision, and the machine's recipe
    beside it, only where an operator has decided — and inside a decision, the machine's read at
    decision only where a record says what it was). A pydantic `exclude` mapping."""
    out: dict[str, Any] = {k: True for k in ("midcycle_gap", "anchor_base_value_per_share_diluted",
                                             "operator_decision", "machine_recipe_hint",
                                             "band_checks")
                           if getattr(anchor, k) is None}
    if anchor.operator_decision is not None \
            and anchor.operator_decision.machine_recipe_at_decision is None:
        out["operator_decision"] = {"machine_recipe_at_decision": True}
    return out


def insert_anchor_block(text: str, anchor: Anchor) -> str:
    """Append the ``anchor`` block as the LAST top-level field of a committed dossier.json TEXT,
    byte-preserving. The ONLY edit to existing bytes is a trailing comma on the previously-last
    field (unavoidable JSON syntax); every other field stays byte-for-byte identical. The backfill
    uses this rather than a model round-trip, because re-serializing older-schema dossiers drifts
    their other fields (new-default materialisation) — a corruption the string insert avoids."""
    body = anchor.model_dump_json(  # a top-level-indented anchor object
        indent=2, exclude=anchor_absent_fields(anchor) or None)
    inner = "\n".join("  " + ln for ln in body.split("\n"))      # +2 so it sits at the field level
    field = '  "anchor": ' + inner.lstrip()                      # -> '  "anchor": {\n    …\n  }'
    end = text.rstrip()
    if not end.endswith("}"):
        raise ValueError("dossier.json is not a JSON object — refusing to insert the anchor")
    trailing = text[len(end):]                                   # preserved trailing whitespace
    head = end[:-1].rstrip()                                     # up to the last field's value
    return f"{head},\n{field}\n}}{trailing}"


def replace_valuation_fields(text: str, updates: dict[str, Any], *,
                             may_add: frozenset[str] = frozenset()) -> str:
    """Byte-preserving replace of one or more ``mechanical.valuation.<field>`` values in a committed
    dossier.json TEXT, leaving every OTHER field byte-for-byte identical.

    Takes the WHOLE cluster at once on purpose. ``own_history``, ``range_position``, ``ev_ebitda``
    and ``ev_ebitda_percentile_5y`` all derive from the SAME Multiples close series — the module
    guarantees they "can't drift" precisely because one loader feeds them. Refreshing one alone
    re-introduces the drift the guarantee exists to prevent (a band over 35 closes beside a string
    still saying "over 20 closes"), so the writer refuses to make that easy.

    A model round-trip drifts older-schema dossiers; a plain ``json.load``→``dump(indent=2,
    ensure_ascii=False)`` reproduces the committed bytes EXACTLY (verified), so it is the safe
    surgical path. Raises when a named field is absent (never silently no-ops) — unless it is
    named in ``may_add``: a field newer than the page (``lease_basis``, 2026-10-19) is added at
    the end of the block, where a fresh assembly serialises it."""
    import json

    doc = json.loads(text)
    val = ((doc.get("mechanical") or {}).get("valuation"))
    if not isinstance(val, dict):
        raise ValueError("mechanical.valuation absent — refusing to refresh")
    for field, new in updates.items():
        if field not in val and field not in may_add:
            raise ValueError(f"mechanical.valuation.{field} absent — refusing to refresh")
        val[field] = new
    out = json.dumps(doc, indent=2, ensure_ascii=False)
    return out + "\n" if text.endswith("\n") and not out.endswith("\n") else out


#: Hints the machine writes when it could NOT compute a recipe: an input absent (`unknown`) or
#: unresolved (`ANCHOR_UNRESOLVED`). A placeholder records a data gap, never a judgment.
PLACEHOLDER_HINTS = frozenset({RECIPE_UNKNOWN, RECIPE_UNRESOLVED})


def preserve_operator_tag(old: Anchor | None, new: Anchor) -> tuple[Anchor, list[str]]:
    """An operator's hand re-tag OUTRANKS the machine's fresh proposal. Returns (anchor, notes).

    The backfill recomputes ``recipe_hint``/``reason`` from EDGAR on every run, so AORT's,
    CNXC's and VITL's hand re-tags — each carrying a judgment the machine cannot derive
    ("leveraged residual", "forward-margin question") — were one backfill away from silently
    vanishing. That was the queued overwrite defect; this closes it. Since #670 assembly applies
    the same rule, so this is the ONE rule for both paths that write an anchor.

    A RECORDED `operator_decision` (2026-10-22) governs outright: copied verbatim, its recipe
    applied, the machine's own recipe and reason refreshed beside it. Without one, provenance is
    NOT recorded on the block, so the rule is deliberately the conservative one:
    ANY divergence from a committed RECIPE keeps the committed value, rather than guessing which
    side was human. The machine's proposal is reported, never applied — the tagger is propose-only
    for the same reason. Two things on the block are not recipes, and the rule does not keep them
    (review of #670, both reproduced on the committed corpus):

    * A PLACEHOLDER hint (``PLACEHOLDER_HINTS``) is the machine saying it could not compute one.
      Kept, it would outlive the data gap that wrote it — FUBO, ORKA and TECX sit committed as
      `unknown`, and keeping it over a later R1 would print "own-history multiple missing" above
      an anchor marked applicable. A real recipe IS still kept over a placeholder: NCNO went
      `R2_NEEDED` → `unknown` on a data gap (07-23), and keeping `R2_NEEDED` there was right.
    * A REASON under an unchanged recipe is the fresh run's. The branch that kept the committed
      reason could not tell an operator's note from a machine refusal, and no operator note under
      an unchanged recipe appears in the committed history — while NFLX and V carry the machine's
      "R1 inputs incomplete", which a later run finding a DIFFERENT cause would have kept on the
      page. A reason does not outlive the state (review of #534) or the cause it described.

    Only the RECIPE is preserved. Every computed VALUE (margin, multiple, the bridge, the base)
    refreshes normally: a re-tag is a judgment about which recipe fits, not a freeze on the
    arithmetic. A committed ``data_quality_detail`` that the fresh run does not reproduce is
    REPORTED rather than merged — silently unioning them would keep a root-cause narrative alive
    after a corrected re-pull had made it false."""
    notes: list[str] = []
    if old is None:
        return new, notes
    updates: dict[str, Any] = {}
    if old.operator_decision is not None:
        # A RECORDED DECISION GOVERNS (2026-10-22). The block is copied verbatim; the recipe is its;
        # the machine's own recipe and reason are kept beside it, refreshed like every computed
        # value — so agreement no longer erases the operator's reason, and disagreement is shown.
        d = old.operator_decision
        # IDEMPOTENT: a `new` read off a committed page (it carries a decision) keeps the machine
        # read recorded beside it, so preserve(page, page) == page — never the decision's recipe
        # mistaken for the machine's (the corpus negative, rewriting every page over itself)
        machine = new.machine_recipe_hint if new.operator_decision is not None else new.recipe_hint
        updates = {"operator_decision": d, "recipe_hint": d.recipe, "machine_recipe_hint": machine}
        if machine in PLACEHOLDER_HINTS:
            # a data gap, as on an undecided page — never shown as the machine disagreeing
            notes.append(f"NO MACHINE READ: this run's hint is {machine!r}, a data gap; the "
                         f"operator's {d.recipe!r} (decided {d.decided_on}) stands")
        elif machine != d.recipe:
            notes.append(f"DIVERGES: the machine reads {machine!r}; the operator's "
                         f"{d.recipe!r} (decided {d.decided_on}) stands — never auto-resolved")
        return new.model_copy(update=updates), [*notes, *_dropped_detail(old, new)]
    if (old.recipe_hint and old.recipe_hint not in PLACEHOLDER_HINTS
            and old.recipe_hint != new.recipe_hint):
        updates["recipe_hint"] = old.recipe_hint
        updates["reason"] = old.reason
        notes.append(f"PRESERVED committed recipe_hint {old.recipe_hint!r} "
                     f"(machine proposed {new.recipe_hint!r}) — reason kept verbatim")
    elif old.recipe_hint != new.recipe_hint:
        notes.append(f"REPLACED placeholder {old.recipe_hint!r} with this run's "
                     f"{new.recipe_hint!r} — a data gap is not a recipe")
    elif old.reason and old.reason != new.reason:
        notes.append(f"REFRESHED reason under {new.recipe_hint!r} — was {old.reason!r} "
                     f"(applicable={old.applicable} → {new.applicable})")
    kept = new.model_copy(update=updates) if updates else new
    return kept, [*notes, *_dropped_detail(old, new)]


def _dropped_detail(old: Anchor, new: Anchor) -> list[str]:
    """The REVIEW note for committed `data_quality_detail` lines this run does not reproduce — the
    same note whether or not a decision governs the page."""
    fresh = new.data_quality_detail or []
    dropped = [x for x in (old.data_quality_detail or []) if x not in fresh]
    if not dropped:
        return []
    return [f"REVIEW: {len(dropped)} committed data_quality_detail line(s) are NOT reproduced by "
            f"this run and will be replaced — first: {dropped[0][:80]}…"]


class DecisionWriteError(ValueError):
    """A write would drop or alter an operator's recorded decision, or would put a hand re-tag back
    into the machine's `reason`."""


def committed_anchor_block(path: Path) -> dict[str, Any] | None:
    """The anchor block stored at `path`, for the decision guard — None only when there is no file
    or the page carries no anchor. A file that EXISTS but cannot be read as a JSON object (a rebase
    left conflict markers in it, a write was cut short) is REFUSED: a write over it could not show
    that it keeps a decision it cannot see, which is how one would be lost (review of #780)."""
    if not path.exists():
        return None
    try:
        stored = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise DecisionWriteError(
            f"{path}: the committed page cannot be read ({type(exc).__name__}) — a write over it "
            "cannot show it keeps an operator's decision; repair the file first") from exc
    if not isinstance(stored, dict):
        raise DecisionWriteError(f"{path}: the committed page is not a JSON object — repair it")
    block = stored.get("anchor")
    return block if isinstance(block, dict) else None


def check_decision_write(committed: dict[str, Any] | None, new: Anchor | None, *,
                         decision_change: bool = False) -> None:
    """THE GUARD EVERY WRITE OF A COMMITTED PAGE RUNS (2026-10-22). Refuses:

    * a write that DROPS or ALTERS the committed `operator_decision` — unless `decision_change`,
      which only `vinci anchor-retag` passes (a new decision, or a retired one, is the operator's);
    * an anchor whose `reason` carries a hand re-tag (`OPERATOR_RETAG_MARK`) with no decision
      block — the pre-2026-10-22 shape, which the next machine write erased.

    `committed` is the page's stored anchor block as read (None when the page has none)."""
    if new is not None and (new.reason or "").startswith(OPERATOR_RETAG_MARK) \
            and new.operator_decision is None:
        raise DecisionWriteError(
            "the anchor's reason carries a hand re-tag with no operator_decision block — record it "
            "with `vinci anchor-retag` so the next machine write cannot erase it")
    block = (committed or {}).get("operator_decision")
    if block is None or decision_change:
        return
    try:   # compared as the MODEL, so an absent optional key and a None are one value
        old = OperatorDecision.model_validate(block)
    except ValidationError as exc:
        raise DecisionWriteError(
            "the committed operator_decision does not validate — a write cannot show it keeps a "
            "decision it cannot read; repair the block first") from exc
    now = new.operator_decision if new is not None else None
    if now != old:
        raise DecisionWriteError(
            f"this write would {'drop' if now is None else 'alter'} the operator's recorded "
            f"decision ({old.recipe}, {old.decided_on}) — only `vinci anchor-retag` changes a "
            "decision")


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
