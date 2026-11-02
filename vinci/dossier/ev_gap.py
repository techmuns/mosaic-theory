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
    #: R2's convention: D&A as a SHARE OF REVENUE. Either form converts OUR leg; only one of them
    #: exists on any given record. LAST, because a defaulted field cannot precede undefaulted ones.
    d_and_a_ratio: float | None = None


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
    if i.d_and_a is not None:
        return i.revenue * i.margin + i.d_and_a
    # A D&A RATIO CONVERTS OUR OWN LEG, AND CROSSES NO HORIZON. `revenue x ratio` is our revenue
    # against our own stated D&A share — every term struck on one basis. The reserved analyst
    # decision was never this: it is whether our TERMINAL margin may be compared to a NEAR-TERM
    # consensus margin, which is a question about the DECOMPOSITION, not about our own EBITDA.
    # Conflating the two suppressed a total gap that needs no consensus at all (operator, revised).
    if i.d_and_a_ratio is not None:
        return i.revenue * (i.margin + i.d_and_a_ratio)
    raise BasisMismatchError(
        "the recipe stores an OPERATING margin against an EV/EBITDA multiple and no D&A — neither "
        "an absolute nor a ratio — is available to convert it")


def total_gap(leg: dict[str, object], *, tev: float) -> float:
    """`our_EV / TEV` — OUR leg against the MARKET's price, and nothing else.

    NO CONSENSUS ENTERS THIS. That is the whole point of separating it (operator, revised
    2026-08-03): the decomposition needs a consensus margin struck on a comparable horizon, and the
    TOTAL does not. Suppressing both because one is unavailable withheld a statement that was
    always computable — AORT 0.94, NCNO 0.85, MVST 1.61 were measurable the entire time.
    """
    i = EvGapInputs(
        revenue=float(leg["revenue"]), margin=float(leg["margin"]),      # type: ignore[arg-type]
        margin_basis=str(leg["margin_basis"]), multiple=float(leg["multiple"]),  # type: ignore[arg-type]
        multiple_basis=str(leg["multiple_basis"]),
        d_and_a=leg.get("d_and_a"), d_and_a_ratio=leg.get("d_and_a_ratio"),  # type: ignore[arg-type]
        consensus_revenue=1.0, consensus_ebitda=1.0, tev=tev, net_debt=0.0, shares=1.0)
    return our_ebitda(i) * float(leg["multiple"]) / tev   # type: ignore[arg-type]


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


#: THE SAME HORIZON-BASIS PROBLEM IS SOLVED TWO WAYS HERE, DELIBERATELY. Do not unify them.
#:
#:   R2 REFUSES the comparison — `_emit_price_implied`, "our margin is a TERMINAL-state assumption
#:      and the consensus at this anchor is a NEAR-TERM forecast". Its mismatch is STRUCTURAL: a
#:      terminal margin is never struck at a near-term consensus year, on any R2 record, ever.
#:   R1 FLAGS it — `leg_basis`, `agrees`/`disagrees`/`unstated`. Its mismatch is OCCASIONAL: the
#:      proposer strikes the base leg AT the anchor by construction, so it arises only when an
#:      analyst overrides the year (SMPL's 18-month thesis reading FY2028).
#:
#: Structural earns a refusal; occasional earns a flag. Unifying them breaks whichever way it goes:
#: making R1 refuse would reject records that should only carry a caveat, and making R2 flag would
#: have it emit a margin ratio it correctly declines to compute — a view difference and a horizon
#: difference mixed in unknown proportion, which is the number the refusal exists to withhold.
#: The three states a leg's fiscal year can be in relative to the year the gap decomposes on.
LEG_BASIS_STATES = ("agrees", "disagrees", "unstated")


def leg_basis(leg: dict[str, object] | None, anchor: str | None) -> dict[str, object]:
    """Whether the leg is struck at the year the decomposition uses.

    States: ``agrees`` / ``disagrees`` / ``unstated``.

    WHY THIS IS NOT ABOUT THE TOTAL. `ev_gap = our_EV / TEV`, and neither term carries a year: our
    EBITDA and multiple come from the leg, TEV from the comps panel. **The total is
    anchor-independent** — measured on SMPL, 1.6711 struck at FY2026 and 1.6711 struck at FY2028.
    What moves is the ATTRIBUTION: the same gap splits differently across revenue/margin/multiple,
    so the driver the page names as dominant can change while the number does not. That is what a
    reader acts on, and it is what this flags.

    ALL THREE RATIOS ARE STRUCK AT `anchor`, which is why the year belongs to the LEG rather than to
    its revenue: `revenue_ratio` divides by consensus revenue there, `margin_ratio` by consensus
    EBITDA÷revenue there, and `multiple_ratio` by `TEV ÷ consensus EBITDA` there — "the market's
    multiple ON THE ANCHOR YEAR". `EvGapInputs.revenue` has always been commented "our leg's revenue
    at the anchor"; this makes that assumption checkable instead of assumed.

    UNSTATED IS NOT DISAGREEING, and the two must render differently. Every record committed before
    2026-08-05 predates `leg_fy`, so `unstated` means "this record never said" — unverifiable, not
    wrong. A record cannot be faulted for lacking a field that did not exist when it was written.
    Collapsing the two would make the flag useless on exactly the records it exists for.
    """
    fy = (leg or {}).get("leg_fy")
    fy = str(fy) if fy not in (None, "") else None
    if anchor is None:
        return {"leg_fy": fy, "anchor_fy": None, "state": "unstated",
                "note": "no anchor year — the decomposition is not struck at all"}
    if fy is None:
        return {"leg_fy": None, "anchor_fy": anchor, "state": "unstated",
                "note": (
                    "the record does not state which fiscal year its base leg is struck "
                    f"at, so the split across revenue/margin/multiple is reported on "
                    f"FY{anchor}'s basis and cannot be verified against the leg. The "
                    "TOTAL gap is unaffected — it carries no year.")}
    if fy == str(anchor):
        return {"leg_fy": fy, "anchor_fy": anchor, "state": "agrees", "note": None}
    return {"leg_fy": fy, "anchor_fy": anchor, "state": "disagrees",
            "note": (
                f"the base leg is struck at FY{fy} and the decomposition at FY{anchor}, "
                "so the split across revenue/margin/multiple — and the shape label drawn "
                "from it — describes a comparison the leg does not make. The TOTAL gap is "
                f"unaffected. Re-read the attribution on FY{fy}, or state why FY{anchor} "
                "is the right basis.")}


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
        # FORWARDED (2026-08-05). `total_gap` and `_emit_price_implied` both pass this; this call
        # site alone dropped it, so a leg carrying a D&A RATIO instead of an absolute — every R2
        # record does — raised BasisMismatchError here even though `our_ebitda` can convert it.
        # Latent today because R2 routes to price-implied before reaching this, and no R1 leg
        # carries a ratio: measured, every committed decomposition is byte-identical after the
        # change. It bites the moment an R2 name is routed three-ratio.
        d_and_a_ratio=leg.get("d_and_a_ratio"),  # type: ignore[arg-type]
        consensus_revenue=float(rev_c["median"]),   # type: ignore[arg-type]
        consensus_ebitda=float(eb_c["median"]),     # type: ignore[arg-type]
        tev=tev, net_debt=net_debt, shares=shares))


def _margin_figures(levels: dict[str, list[dict[str, object]]], leg: dict[str, object],
                    anchor: str) -> dict[str, object] | None:
    """Our EBITDA margin and the street's, AS FIGURES SIDE BY SIDE — never divided.

    THE RATIO IS THE THING BEING REFUSED, not the numbers. `14.4% vs 19.4%` lets a reader see the
    distance and judge how much of it is horizon; `0.74` presents that same distance as if its
    cause were settled. Showing the figures is strictly more information than showing the ratio.
    """
    rev_c, eb_c = _cell(levels, "Revenue", anchor), _cell(levels, "EBITDA", anchor)
    if rev_c is None or eb_c is None:
        return None
    cm, cr = eb_c.get("median"), rev_c.get("median")
    if not isinstance(cm, (int, float)) or not isinstance(cr, (int, float)) or not cr:
        return None
    # OUR EBITDA MARGIN AS `our_ebitda` CONVERTS IT, OR NONE (audit RC1; PR #877 round 2): an
    # absent D&A ratio was added as 0, so an operating margin stood beside the street's EBITDA
    # margin under the EBITDA label. An EBITDA-basis margin needs no conversion; an operating one
    # takes its D&A ratio, or its absolute D&A over its revenue; with neither there is no figure.
    def num(x: object) -> float | None:
        return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None

    margin, ratio = float(leg["margin"]), num(leg.get("d_and_a_ratio"))  # type: ignore[arg-type]
    d_abs, rev = num(leg.get("d_and_a")), num(leg.get("revenue"))
    if leg.get("margin_basis") == "ebitda":
        ours = margin
    elif ratio is not None:
        ours = margin + ratio
    elif d_abs is not None and rev:
        ours = margin + d_abs / rev
    else:
        return None
    return {"ours": ours, "consensus": cm / cr, "basis": "EBITDA margin, ours converted from the "
            "recipe's D&A ratio; consensus = median EBITDA / median revenue at the anchor"}


def _price_implied_only(out: dict[str, object],
                        levels: dict[str, list[dict[str, object]]], leg: dict[str, object],
                        anchor: str, *, tev: float, net_debt: float, shares: float,
                        reason_override: str | None = None) -> dict[str, object]:
    """A stated TOTAL gap with the decomposition suppressed, and its reason named.

    NO SHAPE LABEL. The label ranks the three ratios; with no decomposition there is nothing to
    rank, and emitting one would assert an attribution the numbers do not support.

    TWO DIFFERENT REASONS, NEVER MERGED. Where the CONSENSUS SIDE already routed this name away
    (thin coverage), that is the binding reason and the horizon text would be FALSE — MVST reads
    `2/2` and `1/1`, below the floor, and its margin question never arises. Where coverage is fine,
    the reason is the horizon mix. Recording one reason for both would put a false sentence on one
    of the pages.
    """
    ratios = {"ev_gap": total_gap(leg, tev=tev)}
    if reason_override:
        # THE CONSENSUS SIDE IS ABSENT ENTIRELY — a THIRD reason, distinct from thin coverage and
        # from a horizon mix. Naming it separately matters: "coverage below the floor" implies a
        # consensus was read and found thin, which would be false here.
        return _emit_price_implied(out, levels, leg, anchor, tev=tev, net_debt=net_debt,
                                   shares=shares, ratios=ratios, why=reason_override)
    routes = out.get("routes")
    routes = routes if isinstance(routes, dict) else {}

    def route_of(metric: str) -> str:
        r = routes.get(metric)
        return str(r.get("route") or "") if isinstance(r, dict) else ""

    ebitda_route, rev_route = route_of("EBITDA"), route_of("Revenue")

    thin = Route.PRICE_IMPLIED_ONLY in (ebitda_route, rev_route)
    if thin:
        why = ("consensus coverage at this anchor is below the floor, so no consensus-side "
               "comparison is struck — the total gap stands on our leg and the market price alone")
    else:
        why = ("our margin is a TERMINAL-state assumption and the consensus at this anchor is a "
               "NEAR-TERM forecast; a margin RATIO would mix a view difference with a horizon "
               "difference in unknown proportion, so the two margins are shown as figures instead")
    return _emit_price_implied(out, levels, leg, anchor, tev=tev, net_debt=net_debt,
                               shares=shares, ratios=ratios, why=why)


def _emit_price_implied(out: dict[str, object],
                        levels: dict[str, list[dict[str, object]]], leg: dict[str, object],
                        anchor: str, *, tev: float, net_debt: float, shares: float,
                        ratios: dict[str, float], why: str) -> dict[str, object]:
    """ONE construction for every price-implied-only emission, whatever the reason.

    Three reasons reach here — thin coverage, a horizon mix, and no consensus at all — and they
    must differ ONLY in the sentence. Building the payload three times is how two of them quietly
    stop carrying the same fields."""
    ebitda = our_ebitda(EvGapInputs(
        revenue=float(leg["revenue"]), margin=float(leg["margin"]),        # type: ignore[arg-type]
        margin_basis=str(leg["margin_basis"]), multiple=float(leg["multiple"]),  # type: ignore[arg-type]
        multiple_basis=str(leg["multiple_basis"]),
        d_and_a=leg.get("d_and_a"),                                       # type: ignore[arg-type]
        consensus_revenue=1.0, consensus_ebitda=1.0, tev=tev, net_debt=net_debt, shares=shares,
        d_and_a_ratio=leg.get("d_and_a_ratio")))                          # type: ignore[arg-type]
    return {
        **out,
        "status": "computed",
        "form": Route.PRICE_IMPLIED_ONLY,
        "ratios": ratios,
        "at_adjacent": None,
        "shape": None,                       # nothing to rank
        "decomposition": {"status": "suppressed", "reason": why,
                          "margins": _margin_figures(levels, leg, anchor) if anchor else None},
        "bridge": {"tev": tev, "net_debt": net_debt, "shares": shares,
                   "our_ev": ebitda * float(leg["multiple"]),             # type: ignore[arg-type]
                   "our_ebitda": ebitda, "market_multiple": None},
        "consensus": {m: {k: (c or {}).get(k) for k in ("median", "std_dev", "estimates")}
                      for m in ("Revenue", "EBITDA")
                      if anchor and (c := _cell(levels, m, anchor)) is not None},
    }



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

    # THE CONSENSUS SIDE IS OPTIONAL AND DECIDES ONLY THE DECOMPOSITION. Absent levels or no common
    # anchor means no ROUTE and no ratios — it does NOT mean no total. The first cut returned here,
    # before the leg was even looked at, which is the SAME conflation this function was rewritten to
    # remove, moved one level up: `total_gap` reads our leg and TEV and nothing else, so gating it
    # on a consensus export withholds a statement that was always computable (review of #323).
    anchor = anchor_year(levels) if levels else None
    routes: dict[str, object] = {}
    worst: str | None = None
    if levels and anchor is not None:
        worst = Route.FULL
        for metric in ("Revenue", "EBITDA"):
            cell = _cell(levels, metric, anchor)
            r, why = route_for(cell or {})
            routes[metric] = {"route": r, **why}
            if _ROUTE_RANK[r] < _ROUTE_RANK[worst]:
                worst = r
        out |= {"anchor_fy": anchor, "adjacent_fy": adjacent_year(levels, anchor),
                "form": worst, "routes": routes,
                "leg_basis": leg_basis(leg, anchor)}

    # OUR SIDE. Everything the TOTAL needs, and it needs nothing else.
    if leg is None:
        return nope("no scenario record for this name — "
                    + ("the route is known, the gap is not" if worst
                       else "and no consensus either, so neither side of the comparison exists"))
    for name, v in (("tev", tev), ("net_debt", net_debt), ("shares", shares)):
        if v is None:
            return nope(f"{name} unavailable")
    # SHARES MUST BE POSITIVE, and `is None` was not that check. `decompose` never divides by it,
    # so a 0 or negative count still persisted a `computed` gap — and BOTH renderers then evaluate
    # `equity / shares`, so a malformed record does not degrade the block, it takes down the page.
    assert tev is not None and net_debt is not None and shares is not None
    if shares <= 0:
        return nope(f"share count is {shares:g} — not a usable denominator, so no per-share "
                    "bridge can be struck (present, but not positive)")
    # A LEG THAT CARRIES NO REVENUE OR MARGIN HAS NO OUR-SIDE HERE (2026-09-01, R3). `our_ebitda`
    # is revenue × margin; a forward-P/E leg values a share as EPS × multiple and holds neither,
    # so `total_gap` reaches `float(None)` and raises TypeError — an unhandled crash inside
    # `ev_gap_transform`, taking down the whole refresh for that name. It is masked today only
    # because GOOGL's record states no `diluted_shares` and is refused one line above; the moment
    # an R3 record carries a share count it bites. Stated `not-computed`, the same as every other
    # missing input, rather than a traceback.
    if leg.get("revenue") is None or leg.get("margin") is None:
        return nope("this record's legs carry no revenue and margin (a forward-P/E underwrite "
                    "values a share as EPS × multiple), so there is no EBITDA to strike our side "
                    "of an EV gap from — the comparison is not defined for this recipe")
    try:
        total_gap(leg, tev=tev)          # proves our leg converts before anything is claimed
    except BasisMismatchError as exc:
        return nope(str(exc))

    # NO USABLE CONSENSUS -> the TOTAL still stands; only the decomposition is suppressed, with the
    # reason naming which half is missing rather than reporting the whole block as uncomputed.
    if levels is None or anchor is None:
        # NOT `why` — the route loop above binds that name to a dict, and reusing it re-typed the
        # variable. mypy caught it; a dynamically-typed twin would have shipped a dict into a
        # sentence.
        absent = ("no consensus levels are persisted for this name" if not levels else
                  "no forward year resolves BOTH Revenue and EBITDA, so there is no anchor to "
                  "strike a ratio at")
        return _price_implied_only(out, levels or {}, leg, anchor or "", tev=tev,
                                   net_debt=net_debt, shares=shares, reason_override=(
                                       f"{absent} — the total gap stands on our leg and the market "
                                       "price alone, which need no consensus"))

    # THE DECOMPOSITION IS HORIZON-MIXED ON R2 RECORDS — but the TOTAL is not, so they are decided
    # separately. A margin ratio of 0.74 mixing a view difference and a horizon difference in
    # unknown proportion is uninterpretable, and no caveat rescues it.
    if leg.get("d_and_a") is None and leg.get("d_and_a_ratio") is not None:
        return _price_implied_only(out, levels, leg, anchor, tev=tev, net_debt=net_debt,
                                   shares=shares)
    try:
        at_anchor = _decompose_at(levels, anchor, leg, tev, net_debt, shares)
    except BasisMismatchError as exc:
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
        # THE BRIDGE, PERSISTED RATHER THAN RE-DERIVED BY THE RENDER. The render needs TEV, net debt
        # and shares to carry the gap to a per-share number — and re-striking TEV there would put a
        # SECOND definition of it in the tree, which is exactly what #320's review pinned. Computed
        # once, here, where the vintage stamp is decided beside it.
        "bridge": {k: at_anchor[k] for k in
                   ("tev", "net_debt", "shares", "our_ev", "our_ebitda", "market_multiple")},
        # THE CONSENSUS CELLS THE RATIOS DIVIDE BY, so the render can print sigma WITH ITS n — and
        # print neither when n is absent. A dispersion without its count is the MVST trap in print:
        # 0.0% reads as maximum agreement when it means nobody to disagree.
        "consensus": {m: {k: (c or {}).get(k) for k in ("median", "std_dev", "estimates")}
                      for m in ("Revenue", "EBITDA")
                      if (c := _cell(levels, m, anchor)) is not None},
    }
