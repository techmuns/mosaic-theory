"""Does this management CREATE or DESTROY capital? — one EDGAR read, four source-bound answers.

THE QUESTION NOTHING COULD ANSWER. SMPL wrote off **$391.9M** of acquired brand value, borrowed
~$148M, and repurchased 11.65M shares at an average $18.29 against an $11.33 market. The dossier
could show none of it: no impairment headroom, no buyback economics, no acquisition price. Three of
those are plain XBRL and are built here.

COVERAGE WAS MEASURED BEFORE BUILDING, and the first measurement was wrong in the direction that
would have killed the build. One tag per concept returned "impairment 2/11, acquisition 3/11, and
SMPL has neither" — which reads as *not worth building*. Reading SMPL's actual tag list found four
impairment tags and ``TreasuryStockAcquiredAverageCostPerShare``. The alias families below are what
the corpus actually uses:

    goodwill                    10/11        buyback cash          9/11
    intangibles (net)           10/11        buyback shares        7/11
    acquisition consideration    8/11        buyback avg price     4/11 (DIRECT tag)

WHAT IS NOT HERE, AND SAYS SO. The **$391.9M Atkins/OWYN split** has no XBRL axis: goodwill
separates from intangibles by TAG, but the BRAND dimension is footnote prose. `brand_split` is
therefore always a stated gap — recorded so the aggregate does not read as complete.

EVERY ABSENCE CARRIES ITS REASON and every value carries THE TAG THAT ANSWERED. Three of these
concepts have alias families, so "goodwill impairment" alone does not tell a reader whether it came
from `GoodwillImpairmentLoss` or the combined `GoodwillAndIntangibleAssetImpairment` — different
scopes, and the source_ref must say which.
"""
from __future__ import annotations

from typing import Any

from vinci.dossier.schemas import CapitalAllocation, Sourced
from vinci.edgar.concepts import ConceptPoint, latest_instant, points_for_tag

_USD_M = 1_000_000.0

#: Alias FAMILIES, in preference order. First tag with a usable annual point answers, and the one
#: that answered is named in the `source_ref` — an alias set whose winner is invisible is the
#: `dep_amort` lesson (an abandoned tag kept its last value forever and nothing said so).
GOODWILL = ("Goodwill",)
INTANGIBLES = (
    "IntangibleAssetsNetExcludingGoodwill",       # the total, when the filer states one
    "FiniteLivedIntangibleAssetsNet",             # else the finite-lived leg
    "IndefiniteLivedIntangibleAssetsExcludingGoodwill",
)
GOODWILL_IMPAIRMENT = ("GoodwillImpairmentLoss", "GoodwillAndIntangibleAssetImpairment")
INTANGIBLE_IMPAIRMENT = (
    "ImpairmentOfIntangibleAssetsExcludingGoodwill",
    "ImpairmentOfIntangibleAssetsIndefinitelivedExcludingGoodwill",
    "ImpairmentOfIntangibleAssetsFinitelived",
)
BUYBACK_CASH = ("PaymentsForRepurchaseOfCommonStock",)
BUYBACK_SHARES = ("TreasuryStockSharesAcquired",)
BUYBACK_AVG_PRICE = ("TreasuryStockAcquiredAverageCostPerShare",)
ACQUISITION = (
    "BusinessCombinationConsiderationTransferred1",
    "BusinessCombinationConsiderationTransferred",
    "PaymentsToAcquireBusinessesNetOfCashAcquired",
)

#: WHY THE AVERAGE PRICE IS NOT A PURCHASE PRICE. The tag blends every repurchase in the fiscal
#: period into one number: SMPL's $18.29 spans a stock that fell from roughly $30 to $11. Buying at
#: $30 in September and $12 in June are OPPOSITE judgements and this figure hides both. It must
#: never be read as evidence of WHEN they bought, so the caveat travels ON the value.
AVG_PRICE_BASIS = (
    "fiscal-period average across every repurchase in the period — NOT a purchase price and not "
    "evidence of timing; a period spanning a large price move averages opposite decisions into one "
    "number")


def _pick(facts: dict[str, Any], tags: tuple[str, ...], *,
          kind: str) -> tuple[ConceptPoint, str] | None:
    """The first tag in the family with a usable point, and its name.

    PREFERENCE ORDER, not longest coverage — the `_total_revenue_series` precedent. These families
    are not interchangeable views of one number (a finite-lived intangible balance is not a total),
    so the ORDER encodes which reading we want, and the winner is reported.

    ``kind`` SELECTS THE RIGHT SHAPE, and getting it wrong is silent. Goodwill and intangibles are
    BALANCE-SHEET INSTANTS — SMPL reports 83 and 79 of them and **zero annual durations** — so the
    first cut of this module asked `latest_annual` for them and rendered UNKNOWN on a name with a
    $1.5bn balance. Flows (impairment, buybacks, acquisitions) are durations.

    * ``instant``  — latest balance.
    * ``flow``     — the most recent period_end, and at that end the LONGEST span. A year-to-date
      point is not an annual one and `latest_annual` would skip it: SMPL's live write-off is a
      272-day FY2026 YTD charge, and annual-only would have reported the prior year's $60.9M as
      though it were current.
    * ``largest``  — the biggest POSITIVE value on record. For acquisitions "latest" is the wrong
      question (what did they pay, and when — not what trickled through last year) and the sign
      matters: SMPL carries **+280.4 (FY2024) and −280.4 (FY2025 restating the same period_end)**,
      so magnitude alone would coin-flip between an acquisition and its reversal.
    """
    for tag in tags:
        pts = [x for x in points_for_tag(facts, tag) if x.value is not None]
        if kind == "instant":
            p = latest_instant([x for x in pts if x.is_instant])
        elif kind == "largest":
            pos = [x for x in pts if x.value > 0]
            p = max(pos, key=lambda x: (x.value, x.period_end)) if pos else None
        else:
            flows = [x for x in pts if not x.is_instant and x.period_start is not None]
            end = max((x.period_end for x in flows), default=None)
            at_end = [x for x in flows if x.period_end == end]
            p = max(at_end, key=lambda x: ((x.period_end - x.period_start).days,  # type: ignore[operator]
                                           x.filed)) if at_end else None
        if p is not None:
            return p, tag
    return None


def _span(p: ConceptPoint) -> str:
    """The period a flow COVERS, in days — never the fiscal-year label alone.

    A charge is only comparable to another charge over the same span, and "FY2026" on a 272-day
    year-to-date point invites reading it as a full year. Stated in days so the reader cannot
    mistake nine months for twelve."""
    if p.period_start is None:
        return f"as at {p.period_end}"
    return f"{p.period_start}→{p.period_end}, {(p.period_end - p.period_start).days}d"


def _money(facts: dict[str, Any], tags: tuple[str, ...], label: str, *,
           kind: str = "flow") -> Sourced[float]:
    """A $-denominated value in $M, or UNKNOWN NAMING EVERY TAG TRIED.

    The absence reason lists the family rather than saying "not found": a reader who knows the
    filer uses a fifth tag can then say so, which "no data" does not invite.
    """
    got = _pick(facts, tags, kind=kind)
    if got is None:
        return Sourced.unknown(
            note=f"no {label} under any of {', '.join(tags)} — EDGAR XBRL companyfacts")
    p, tag = got
    return Sourced.present(
        round(p.value / _USD_M, 3),
        source_ref=f"EDGAR companyfacts {tag} ({_span(p)})")


def build_capital_allocation(facts: dict[str, Any]) -> CapitalAllocation:
    """Assemble the block from EDGAR companyfacts. No CIQ, no LLM, no derivation beyond one ratio.

    THE ONE DERIVATION IS GUARDED. `buyback_avg_price` prefers the filer's OWN direct tag; only
    when that is absent AND both legs are present is it computed as cash ÷ shares. It is NEVER
    imputed from one leg — a cash figure without a share count says nothing about price, and a
    fabricated average here would be a decision figure in the strict sense.
    """
    shares_pt = _pick(facts, BUYBACK_SHARES, kind="flow")
    cash_pt = _pick(facts, BUYBACK_CASH, kind="flow")
    cash = _money(facts, BUYBACK_CASH, "share-repurchase cash")
    shares = (
        Sourced.present(
            shares_pt[0].value,
            source_ref=f"EDGAR companyfacts {shares_pt[1]} ({_span(shares_pt[0])})")
        if shares_pt is not None else
        Sourced.unknown(note=f"no annual repurchased-share count under {', '.join(BUYBACK_SHARES)} "
                             f"— EDGAR XBRL companyfacts"))

    direct = _pick(facts, BUYBACK_AVG_PRICE, kind="flow")
    # VINTAGE BEATS DIRECTNESS — `_latest_dep_amort`'s rule, and the same failure it was built for.
    # The filer's own average-price tag is preferred only while it is CURRENT: EPAM's last one is
    # Q1 **2023** ($283.69, on a stock now near $112) sitting beside Q1 **2026** repurchase cash.
    # A three-year-old average presented next to this year's spend is the abandoned-tag shape, and
    # a derivation over the current period is the better answer when both legs are there.
    if (direct is not None and cash_pt is not None and shares_pt is not None
            and direct[0].period_end < cash_pt[0].period_end
            and shares_pt[0].period_end == cash_pt[0].period_end):
        direct = None
    if direct is not None:
        p, tag = direct
        # THE THREE BUYBACK FIELDS MUST NAME THE SAME WINDOW, OR SAY THEY DO NOT. The filer's
        # average-price tag and its cash tag are separate facts with separate latest periods:
        # BRBR states the average over 181 DAYS and the cash over 272. Printed side by side those
        # invite a reader to divide one by the other and derive a share count for a window neither
        # covers. The spans are already in each `source_ref`; this makes the DISAGREEMENT explicit,
        # because a reader comparing two numbers should not have to diff two provenance strings.
        mismatch = ""
        if cash_pt is not None and (
                cash_pt[0].period_start != p.period_start or cash_pt[0].period_end != p.period_end):
            mismatch = (f" PERIOD MISMATCH — this average covers {_span(p)} while the repurchase "
                        f"cash beside it covers {_span(cash_pt[0])}; they are not two views of one "
                        f"window and must not be divided into each other")
        avg = Sourced.present(
            round(p.value, 4),
            source_ref=f"EDGAR companyfacts {tag} ({_span(p)})",
            note=AVG_PRICE_BASIS + mismatch)
    elif (cash_pt is not None and shares_pt is not None and cash.value is not None
          and shares.value
          and cash_pt[0].period_start == shares_pt[0].period_start
          and cash_pt[0].period_end == shares_pt[0].period_end):
        # SAME PERIOD ON BOTH LEGS OR NOTHING — `_latest_dep_amort`'s rule, and the first cut
        # broke it while ASSERTING it: the note read "both legs are the same fiscal year" and the
        # code never checked. VITL divided Q1-2026 cash ($20.0M) by a **2019** share count and
        # published $7.01 as a derived average — a seven-year straddle, and a number that never
        # existed. An assertion the code does not enforce is worse than no assertion, because it
        # tells the reader not to look.
        avg = Sourced.present(
            round(cash.value * _USD_M / shares.value, 4),
            source_ref=f"DERIVED: {cash.source_ref} ÷ {shares.source_ref}",
            note=f"{AVG_PRICE_BASIS}. DERIVED as cash ÷ shares — the filer states no "
                 f"{BUYBACK_AVG_PRICE[0]}; both legs verified on {_span(cash_pt[0])}")
    else:
        if cash.value is None:
            why = "the cash leg is absent"
        elif not shares.value:
            why = "the share-count leg is absent"
        else:
            why = (f"its legs cover DIFFERENT periods — cash {_span(cash_pt[0])} vs shares "  # type: ignore[index]
                   f"{_span(shares_pt[0])} — and dividing one by the other would state an average "  # type: ignore[index]
                   f"for a window neither covers")
        avg = Sourced.unknown(
            note=f"no {BUYBACK_AVG_PRICE[0]} and {why}, so an average would be imputed rather "
                 f"than computed — refused (EDGAR XBRL companyfacts)")

    return CapitalAllocation(
        goodwill=_money(facts, GOODWILL, "goodwill balance", kind="instant"),
        intangibles=_money(facts, INTANGIBLES, "intangible-asset balance", kind="instant"),
        goodwill_impairment=_money(facts, GOODWILL_IMPAIRMENT, "goodwill impairment"),
        intangible_impairment=_money(facts, INTANGIBLE_IMPAIRMENT, "intangible impairment"),
        buyback_cash=cash,
        buyback_shares=shares,
        buyback_avg_price=avg,
        acquisition_consideration=_money(facts, ACQUISITION, "acquisition consideration",
                                         kind="largest"),
        brand_split=Sourced.unknown(
            note="NOT AVAILABLE FROM XBRL — goodwill and intangible impairment separate by TAG, "
                 "but the per-BRAND split (e.g. SMPL's $391.9M across Atkins and OWYN) is "
                 "footnote prose with no XBRL axis. Read the 10-K impairment note; the aggregate "
                 "above is complete only at the goodwill/intangible level"),
    )
