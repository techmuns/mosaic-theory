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


def shape_label(*, revenue_ratio: float, margin_ratio: float, multiple_ratio: float) -> str:
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


_RATIO_KEYS = ("revenue_ratio", "margin_ratio", "multiple_ratio")


def _ratios(d: dict[str, float]) -> dict[str, float]:
    """The three ratios out of a `decompose` result, BY NAME, refusing a partial one.

    A missing key would default-or-crash somewhere downstream; refusing here names the caller's
    mistake at the point it is made."""
    missing = [k for k in _RATIO_KEYS if k not in d]
    if missing:
        raise KeyError(f"shape label needs {missing} — pass the `decompose` result, not a subset")
    return {k: d[k] for k in _RATIO_KEYS}


def adjacent_year(levels: dict[str, list[dict[str, object]]], anchor: str) -> str | None:
    """The next forward year after ``anchor`` where BOTH metrics resolve, or None.

    WHY AN ADJACENT YEAR AT ALL. The shape label is the uncomfortable output — `multiple-dominant`
    says the view rests on re-rating rather than on the business — so it must not be movable by
    choosing a year. Computing it twice is the only way to show it is not.

    CNXC IS THE MINIMUM CASE: exactly `['2026', '2027']` on both metrics, so there is exactly one
    alternative. A name with one forward year has NO adjacent year and returns None — which is a
    real state (the label stands unchecked) and must not be confused with "the labels agree".
    """
    have = {m: {str(c["fy"]) for c in cells} for m, cells in levels.items()}
    if not {"Revenue", "EBITDA"} <= set(have):
        return None
    later = sorted((y for y in have["Revenue"] & have["EBITDA"] if int(y) > int(anchor)), key=int)
    return later[0] if later else None


def labels_across_years(at_anchor: dict[str, float],
                        at_adjacent: dict[str, float] | None) -> dict[str, object]:
    """Both shape labels, and whether they agree.

    TAKES THE `decompose` RESULT BY NAME, never three positional floats. Review of the first cut:
    a margin<->multiple swap silently turned `multiple-dominant` into `earnings` — the
    uncomfortable label becoming the comfortable one, with no error and no way to notice. Three
    interchangeable floats in a tuple is the address-by-position class this repo already ruled on
    (item 33's .rtf parser, the customers/suppliers selection), and the caller ALREADY HAS the
    names because `decompose` returns them.

    PERSISTS BOTH WHEN THEY DISAGREE. A single label chosen from the year that produced it is a
    label chosen by whoever picked the year; carrying both makes the choice visible instead. When
    there is no adjacent year the label is marked UNCHECKED rather than agreed — absent evidence
    and confirming evidence are different states, and only one of them earns confidence.
    """
    anchor_label = shape_label(**_ratios(at_anchor))
    if at_adjacent is None:
        return {"anchor": anchor_label, "adjacent": None, "agree": None,
                "note": "no adjacent forward year — the label is unchecked, not confirmed"}
    adjacent_label = shape_label(**_ratios(at_adjacent))
    agree = anchor_label == adjacent_label
    return {
        "anchor": anchor_label,
        "adjacent": adjacent_label,
        "agree": agree,
        "note": ("both years give the same shape" if agree else
                 f"the shape MOVES between years — {anchor_label} at the anchor, "
                 f"{adjacent_label} adjacent; neither is the answer on its own"),
    }


# --- PERSISTENCE: the resulting FORM, its shape labels, and both vintages -----------------------

#: Route strictness, LOW to HIGH. A build routes on BOTH consensus metrics and takes the WEAKER of
#: the two: revenue's coverage can be as thin as EBITDA's, and a `three-ratio` form struck on a
#: one-estimate revenue median would be the same garbage the route exists to refuse — just entering
#: through the numerator instead of the denominator.
_ROUTE_RANK = {Route.PRICE_IMPLIED_ONLY: 0, Route.TWO_RATIO: 1, Route.FULL: 2}


def _cell(levels: dict[str, list[dict[str, object]]], metric: str,
          fy: str) -> dict[str, object] | None:
    return next((c for c in levels.get(metric, []) if str(c.get("fy")) == fy), None)


def _decompose_at(levels: dict[str, list[dict[str, object]]], fy: str,
                  leg: dict[str, object], tev: float, net_debt: float,
                  shares: float) -> dict[str, float] | None:
    """`decompose` at one fiscal year, or None when either consensus metric is missing there."""
    rev_c, eb_c = _cell(levels, "Revenue", fy), _cell(levels, "EBITDA", fy)
    if rev_c is None or eb_c is None:
        return None
    for c in (rev_c, eb_c):
        if not isinstance(c.get("median"), (int, float)) or not c["median"]:
            return None
    return decompose(EvGapInputs(
        revenue=float(leg["revenue"]),          # type: ignore[arg-type]
        margin=float(leg["margin"]),            # type: ignore[arg-type]
        margin_basis=str(leg["margin_basis"]),
        multiple=float(leg["multiple"]),        # type: ignore[arg-type]
        multiple_basis=str(leg["multiple_basis"]),
        d_and_a=leg.get("d_and_a"),             # type: ignore[arg-type]
        consensus_revenue=float(rev_c["median"]),   # type: ignore[arg-type]
        consensus_ebitda=float(eb_c["median"]),     # type: ignore[arg-type]
        tev=tev, net_debt=net_debt, shares=shares))


def build_ev_gap(
    levels: dict[str, list[dict[str, object]]] | None,
    leg: dict[str, object] | None,
    *,
    tev: float | None,
    net_debt: float | None,
    shares: float | None,
    tev_as_of: str | None,
    consensus_as_of: str | None,
) -> dict[str, object]:
    """(A2b persistence) The resulting FORM for one name — always a value, never an omission.

    EVERY RETURN CARRIES `status`, AND THAT IS THE POINT. This lands render-first: the render ships
    on deploy while the refresh that computes this lags, so an ABSENT block would leave eleven
    pages showing an empty section with nothing saying why. `status="not-computed"` with a stated
    `reason` is a claim a reader can act on; a missing key is not. Same two-speed lesson as the
    insider horizon — a change that is right only after a later step must not look finished before
    it.

    BOTH VINTAGES, ALWAYS, EVEN WHEN THEY DISAGREE. The TEV comes off the comps workbook and the
    consensus off the estimates workbook, and they are pulled on different days: SMPL reads comps
    2026-07-24 against estimates `≥2026-07-21`. A single stamp over both would be the
    `financial_summary.as_of` defect — one date over columns of two vintages. The `≥` is carried
    VERBATIM: SMPL's estimates export has no As-Of header, so its date is a FLOOR, and flattening
    it to a plain date would manufacture precision the workbook does not have.
    """
    out: dict[str, object] = {
        "vintages": {"tev_as_of": tev_as_of, "consensus_as_of": consensus_as_of},
        # PRINTED PER NAME WHILE THE QUESTION IS OPEN (operator ruling 2026-07-30). The two recipes
        # use opposite D&A conventions and nothing reconciles them; A2's job is to make the
        # difference VISIBLE, not to pick one.
        "d_and_a_convention": (leg or {}).get("d_and_a_convention"),
    }

    def nope(reason: str) -> dict[str, object]:
        return {**out, "status": "not-computed", "reason": reason}

    if not levels:
        return nope("no consensus levels on this name — run the consensus refresh first")
    anchor = anchor_year(levels)
    if anchor is None:
        return nope("no forward year resolves BOTH Revenue and EBITDA — no year to strike a "
                    "ratio at")

    # ROUTE FIRST, and on the CONSENSUS SIDE ALONE, so it is decidable for every name — including
    # the five with no scenario record. Only the EMISSION needs a leg.
    routes: dict[str, object] = {}
    worst = Route.FULL
    for metric in ("Revenue", "EBITDA"):
        cell = _cell(levels, metric, anchor)
        r, why = route_for(cell or {})
        routes[metric] = {"route": r, **why}
        if _ROUTE_RANK[r] < _ROUTE_RANK[worst]:
            worst = r
    out |= {"anchor_fy": anchor, "adjacent_fy": adjacent_year(levels, anchor),
            "form": worst, "routes": routes}

    if leg is None:
        return {**out, "status": "not-computed",
                "reason": "no scenario record for this name — the route is known, the gap is not"}
    for name, v in (("tev", tev), ("net_debt", net_debt), ("shares", shares)):
        if v is None:
            return {**out, "status": "not-computed", "reason": f"{name} unavailable"}
    assert tev is not None and net_debt is not None and shares is not None
    try:
        at_anchor = _decompose_at(levels, anchor, leg, tev, net_debt, shares)
    except BasisMismatchError as exc:
        # NAME THE CONVENTION, NEVER "no D&A". `our_ebitda`'s message is written for a data gap,
        # and for an R2 record that reading is wrong in a way that invites the wrong fix: the D&A
        # is not missing, it is stated as a RATIO OF REVENUE, and converting it at the anchor is a
        # reserved analyst decision that moves committed numbers. "Absent" would send a reader
        # looking for a number that is already there.
        if leg.get("d_and_a") is None and leg.get("d_and_a_ratio") is not None:
            return {**out, "status": "not-computed", "reason": (
                f"this record states D&A as a RATIO OF REVENUE ({leg['d_and_a_ratio']}), the R2 "
                "terminal convention — not absent, but converting it at the anchor year is the "
                "open analyst decision on D&A convention, so no gap is struck here")}
        return {**out, "status": "not-computed", "reason": str(exc)}
    if at_anchor is None:
        return {**out, "status": "not-computed", "reason": "consensus medians absent at the anchor"}
    adj_fy = out["adjacent_fy"]
    at_adjacent = None
    if isinstance(adj_fy, str):
        try:
            at_adjacent = _decompose_at(levels, adj_fy, leg, tev, net_debt, shares)
        except BasisMismatchError:                 # the anchor stands; the CHECK is what is lost
            at_adjacent = None
    return {
        **out,
        "status": "computed",
        "ratios": {k: at_anchor[k] for k in (*_RATIO_KEYS, "ev_gap")},
        "at_adjacent": ({k: at_adjacent[k] for k in (*_RATIO_KEYS, "ev_gap")}
                        if at_adjacent else None),
        "shape": labels_across_years(at_anchor, at_adjacent),
    }
