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
