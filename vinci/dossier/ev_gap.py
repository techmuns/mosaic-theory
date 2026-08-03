"""(A2a) THE EV GAP, DECOMPOSED INTO THREE RATIOS WHOSE PRODUCT IS THE GAP.

NOT AN ATTRIBUTION. The three ratios are stated; their product reconciles to `our_EV / TEV` by
identity. Nothing here decides which ratio "explains" the gap — that is the reader's call, and the
shape label (A2b) is a function of these three, computed later from the same numbers.

WHY THE MULTIPLE'S DENOMINATOR IS THE ANCHOR YEAR, NOT NTM. `TEV / consensus EBITDA at the anchor`
compares our multiple against the market's multiple ON THE SAME FISCAL YEAR. An NTM denominator
against a fiscal-year numerator is the LTM-vs-NTM defect wearing a different hat.
"""
from __future__ import annotations

from dataclasses import dataclass


class BasisMismatchError(ValueError):
    """The margin's numerator is not the multiple's denominator, and no conversion was possible."""


@dataclass(frozen=True)
class EvGapInputs:
    """Everything the decomposition needs, all of it already persisted somewhere else."""

    revenue: float                 # our leg's revenue at the anchor
    margin: float                  # our leg's margin — see `margin_basis`
    margin_basis: str              # "operating" | "ebitda"
    multiple: float                # our leg's exit multiple
    multiple_basis: str            # "EV/EBITDA" | "EV/EBIT"
    d_and_a: float | None          # required to convert an operating margin to EBITDA
    consensus_revenue: float
    consensus_ebitda: float
    tev: float
    net_debt: float
    shares: float


def our_ebitda(i: EvGapInputs) -> float:
    """Our leg's EBITDA, converting from an operating margin when the multiple demands it.

    SMPL'S RECIPE AS WRITTEN stores an OPERATING margin (0.14) against an EV/EBITDA multiple
    (12.5x). Comparing that margin to a consensus EBITDA margin would divide two different
    quantities and produce a number that looks like a ratio. `rev x op_margin + D&A` is the
    conversion; without D&A there is no conversion and the answer is a REFUSAL, never a
    best-effort.
    """
    if i.multiple_basis != "EV/EBITDA":
        raise BasisMismatchError(
            f"multiple basis {i.multiple_basis!r} is not EV/EBITDA — the decomposition is only "
            "defined where the margin's numerator is the multiple's denominator")
    if i.margin_basis == "ebitda":
        return i.revenue * i.margin
    if i.margin_basis != "operating":
        raise BasisMismatchError(f"unknown margin basis {i.margin_basis!r}")
    if i.d_and_a is None:
        raise BasisMismatchError(
            "the recipe stores an OPERATING margin against an EV/EBITDA multiple and no D&A is "
            "available to convert it — the margin ratio would divide EBIT-margin by EBITDA-margin")
    return i.revenue * i.margin + i.d_and_a


def decompose(i: EvGapInputs) -> dict[str, float]:
    """The three ratios and the gap they multiply to.

    THE PRODUCT IS AN IDENTITY:
        (rev/crev) x (mgn/cmgn) x (mult/cmult)
      = (rev x mgn x mult) / (crev x cmgn x (TEV/cebitda))
      = our_EV / TEV                                        because crev x cmgn == cebitda

    WHAT THE ASSERTION BELOW ACTUALLY GUARDS — corrected in review. It does NOT catch "an input
    moving between the two expressions": every input appears in both, so the identity holds for
    ANY values and the check cannot fire (verified on 3000 random inputs, worst residual 4.5e-13).
    Describing it as an input check was claiming a generality it does not have.

    It is a REFACTOR guard, and a real one. The identity depends on `market_multiple` and
    `consensus_margin` being struck from the SAME two consensus numbers at the SAME year. Change
    the multiple's denominator to NTM — the defect this module's own docstring warns about — and
    the product stops equalling the gap. The assertion is what turns that from a silently wrong
    decomposition into a refusal, which is why it is pinned by a test that actually breaks it.
    """
    ebitda = our_ebitda(i)
    our_margin = ebitda / i.revenue
    consensus_margin = i.consensus_ebitda / i.consensus_revenue
    market_multiple = i.tev / i.consensus_ebitda      # the market's multiple ON THE ANCHOR YEAR

    revenue_ratio = i.revenue / i.consensus_revenue
    margin_ratio = our_margin / consensus_margin
    multiple_ratio = i.multiple / market_multiple

    our_ev = ebitda * i.multiple
    ev_gap = our_ev / i.tev
    product = revenue_ratio * margin_ratio * multiple_ratio
    if abs(product - ev_gap) > 1e-9 * max(1.0, abs(ev_gap)):
        raise ValueError(
            f"the three ratios multiply to {product!r} but our_EV/TEV is {ev_gap!r} — the "
            "multiple's denominator and the margin's denominator are no longer the same consensus "
            "EBITDA at the same year, so these three ratios do not decompose this gap")
    return {
        "revenue_ratio": revenue_ratio,
        "margin_ratio": margin_ratio,
        "multiple_ratio": multiple_ratio,
        "ev_gap": ev_gap,
        "our_ev": our_ev,
        "our_ebitda": ebitda,
        "market_multiple": market_multiple,
        "tev": i.tev,
        "net_debt": i.net_debt,
        "shares": i.shares,
    }


def anchor_year(levels: dict[str, list[dict[str, object]]]) -> str | None:
    """The nearest forward year where BOTH metrics resolve.

    EPAM carries Revenue 5fy against EBITDA 3fy, so revenue's furthest year would leave the margin
    ratio uncomputable — an anchor is only an anchor if every ratio can be struck there. Nearest
    rather than furthest: the closest forward year is the one the market is actually pricing.
    """
    have = {m: {str(c["fy"]) for c in cells} for m, cells in levels.items()}
    if not {"Revenue", "EBITDA"} <= set(have):
        return None
    both = have["Revenue"] & have["EBITDA"]
    return min(both, key=int) if both else None

# --- A2b: routing, decided on the CONSENSUS SIDE ALONE -----------------------------------------
#
# TWO RULES, AND EACH HAS A LIVE COUNTEREXAMPLE TO THE OTHER. This is what gets simplified away
# later, so the numbers are here:
#
#   VITL FY2026 — coverage 9/10 (fine), EBITDA median 3.300 on high 9.018 / low 0.315.
#     Dispersion 263.7%. Consensus margin 0.4260%, so a 10% our-margin gives r_margin 23.47x and
#     r_mult collapses by the same factor — while the product reconciles EXACTLY, because the
#     identity holds for any inputs. THE EXACT RECONCILIATION IS WHY THE GARBAGE IS NOT CAUGHT.
#     A coverage-only rule passes VITL straight through.
#
#   MVST FY2026 — EBITDA 62.078 on high == low == median, one estimate. Dispersion 0.0%, which
#     reads as MAXIMUM AGREEMENT where there is nobody to disagree. Coverage 1/1.
#     A dispersion-only rule passes MVST straight through.
#
# Neither rule alone is sufficient. Both thresholds are FACE-VALIDITY choices, never tuned on
# outcomes: 3 estimates is the smallest number for which a median is not just a midpoint of two,
# and 50% separates VITL's 263.7% from CNXC's 4.3% by more than an order of magnitude either side.
MIN_ESTIMATES = 3
MAX_DISPERSION = 0.50

#: 3-5 estimates is thin but usable — the count is CARRIED so the render can caution, rather than
#: the route being narrowed. NCNO sits here at 5/7 on EBITDA.
CAUTION_ESTIMATES = 5


class Route:
    """What form the gap statement may take for one metric at one year."""

    FULL = "three-ratio"
    TWO_RATIO = "two-ratio"                # revenue + EV/Revenue; margin stated as a path
    PRICE_IMPLIED_ONLY = "price-implied-only"


def _estimate_count(raw: str | None) -> int | None:
    """The first half of CIQ's raw pair (`9/11` -> 9). Never re-labelled; only read."""
    if not raw or "/" not in raw:
        return None
    head = raw.split("/", 1)[0].strip()
    return int(head) if head.isdigit() else None


def route_for(cell: dict[str, object]) -> tuple[str, dict[str, object]]:
    """(A2b) The route for ONE consensus cell, and why — from the consensus data ALONE.

    OUR LEG NEVER ENTERS THIS. Coverage and dispersion are properties of what the street reported,
    so routing is decidable for every name including the five with no scenario record. That is the
    correct decomposition rather than a workaround: `route_for` is testable on all eleven, and only
    the emission of the gap statement needs a leg.

    COVERAGE IS CHECKED BEFORE DISPERSION, because a single estimate has no dispersion to measure
    and its 0.0% would otherwise read as agreement.
    """
    n = _estimate_count(cell.get("estimates"))            # type: ignore[arg-type]
    why: dict[str, object] = {"estimates": cell.get("estimates"), "n": n}
    if n is None or n < MIN_ESTIMATES:
        why["reason"] = (
            f"{n if n is not None else 'unknown'} estimate(s) — below {MIN_ESTIMATES}; a median "
            "over so few is one analyst's model, and its dispersion reads as agreement because "
            "there is nobody to disagree")
        return Route.PRICE_IMPLIED_ONLY, why

    med, hi, lo = (cell.get("median"), cell.get("high"), cell.get("low"))
    if not isinstance(med, (int, float)) or not med:
        why["reason"] = "no usable median"
        return Route.PRICE_IMPLIED_ONLY, why
    if isinstance(hi, (int, float)) and isinstance(lo, (int, float)):
        dispersion = (hi - lo) / abs(med)
        why["dispersion"] = dispersion
        if dispersion > MAX_DISPERSION:
            why["reason"] = (
                f"dispersion {dispersion:.1%} exceeds {MAX_DISPERSION:.0%} — the margin ratio "
                "divides by a denominator the street does not agree on, and the reconciliation "
                "stays exact while the decomposition stops meaning anything")
            return Route.TWO_RATIO, why

    why["caution"] = n <= CAUTION_ESTIMATES
    thin = " — thin, caution carried" if n <= CAUTION_ESTIMATES else ""
    why["reason"] = f"{n} estimates{thin}"
    return Route.FULL, why


def shape_label(revenue_ratio: float, margin_ratio: float, multiple_ratio: float) -> str:
    """Which ratio carries the gap. A FUNCTION of the three, never a separate judgement.

    `multiple-dominant` is the uncomfortable one — it says the view rests on re-rating rather than
    on the business — so it is defined by distance from the others, not by a bare threshold.
    """
    dist = {"earnings": abs(margin_ratio - 1.0), "timing-duration": abs(revenue_ratio - 1.0),
            "multiple": abs(multiple_ratio - 1.0)}
    lead = max(dist, key=lambda k: dist[k])
    if lead == "multiple" and dist["multiple"] > 2 * max(dist["earnings"], dist["timing-duration"]):
        return "multiple-dominant"
    return lead
