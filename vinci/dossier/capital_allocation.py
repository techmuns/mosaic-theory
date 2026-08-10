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

from datetime import timedelta
from statistics import median
from typing import Any

from vinci.dossier.schemas import (
    CapitalAllocation,
    PeerCapitalIntensity,
    PeerCapitalRow,
    PeerImpairment,
    Sourced,
    SourceStatus,
)
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
    if kind == "largest":
        # FAMILY-WIDE, NOT PREFERENCE-FIRST — the one kind where the ORDER is the wrong rule.
        # "What did they pay" is a question about the whole family: EPAM states a $7.0M
        # `…ConsiderationTransferred1` from **2017** and a $912.2M `PaymentsToAcquireBusinesses…`
        # from **2024**, and taking the first tag with any data returned the 2017 figure — a 130x
        # understatement of acquisition spend on a name underwritten for being acquisitive. The
        # tags are different definitions (total consideration vs cash net of cash acquired), which
        # is exactly why the winner is NAMED in the source_ref rather than blended.
        best: tuple[ConceptPoint, str] | None = None
        for tag in tags:
            for x in points_for_tag(facts, tag):
                if x.value is None or x.value <= 0:
                    continue
                if best is None or (x.value, x.period_end) > (best[0].value, best[0].period_end):
                    best = (x, tag)
        return best
    for tag in tags:
        pts = [x for x in points_for_tag(facts, tag) if x.value is not None]
        if kind == "instant":
            p = latest_instant([x for x in pts if x.is_instant])
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

    # DOES THE BUYBACK PAIR NAME ONE WINDOW? Cash and shares are separate facts with separate
    # latest periods — EPAM states cash over **89 days** and shares over **364** — and printed
    # adjacent they invite exactly the division the average-price guard already refuses. The three
    # buyback lines must agree about their window or say they do not, on all three of them.
    if (cash_pt is not None and shares_pt is not None
            and (cash_pt[0].period_start != shares_pt[0].period_start
                 or cash_pt[0].period_end != shares_pt[0].period_end)):
        pair = (f" PERIOD MISMATCH — cash covers {_span(cash_pt[0])} and the share count covers "
                f"{_span(shares_pt[0])}; they are not one window and must not be divided into "
                f"each other")
        cash = cash.model_copy(update={"note": (cash.note or "") + pair})
        shares = shares.model_copy(update={"note": (shares.note or "") + pair})

    # A CHARGE OLDER THAN THE BALANCE IT SITS BESIDE IS NOT A MEASUREMENT OF THIS PERIOD, and the
    # render cannot tell without help: EPAM's goodwill impairment is $0.7M from **FY2022** against
    # a balance as at **2026-03-31**, which printed beside SMPL's live 272-day charge read as the
    # same kind of fact. The staleness IS the finding — EPAM has never written down $1.59bn — so it
    # is flagged HERE, where both dates are structured, rather than reconstructed from a
    # `source_ref` string in the renderer (the divergent-string-parse class).
    bal = _pick(facts, GOODWILL, kind="instant") or _pick(facts, INTANGIBLES, kind="instant")
    impairments = {}
    for name, tags in (("goodwill_impairment", GOODWILL_IMPAIRMENT),
                       ("intangible_impairment", INTANGIBLE_IMPAIRMENT)):
        f = _money(facts, tags, name.replace("_", " "))
        got = _pick(facts, tags, kind="flow")
        # TRAILING TWELVE MONTHS, not a calendar-year comparison. The first cut asked whether the
        # charge's year was LESS than the balance's, which is too blunt by exactly the amount that
        # matters: IT's $150.0M FY2025 charge ends 2025-12-31 against a 2026-06-30 balance — six
        # months apart, different years — and was suppressed off the page as "none in the current
        # period". EPAM's is FOUR YEARS old. A charge inside the balance's trailing year is a
        # current fact; one outside it is not.
        if (f.status is SourceStatus.PRESENT and got is not None and bal is not None
                and (bal[0].period_end - got[0].period_end).days > 366):
            years = (bal[0].period_end - got[0].period_end).days / 365.25
            f = f.model_copy(update={"note": (
                f"STALE — the last such charge covers {_span(got[0])}, {years:.1f} years before "
                f"the balance beside it ({_span(bal[0])}), so it measures no current period. "
                f"Nothing has been written down since")})
        impairments[name] = f

    return CapitalAllocation(
        goodwill=_money(facts, GOODWILL, "goodwill balance", kind="instant"),
        intangibles=_money(facts, INTANGIBLES, "intangible-asset balance", kind="instant"),
        goodwill_impairment=impairments["goodwill_impairment"],
        intangible_impairment=impairments["intangible_impairment"],
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


#: Market-cap floor ($M) for the "large peers" median. STATED, not hidden: SMPL's set spans $49M
#: to $30.1bn, and a $49M distressed name's ratio-to-market-cap (HAIN, 950%) is a de-rating
#: artifact rather than a statement about its balance sheet. The floor is face-validity, never
#: tuned — it separates names whose balance sheets are comparable from ones whose are not.
PEER_SIZE_FLOOR_MUSD = 1_000.0

TOTAL_ASSETS = ("Assets",)


def _acquired_and_assets(facts: dict[str, Any]) -> tuple[float | None, float | None]:
    """(goodwill + intangibles, total assets) in $M — both latest INSTANTS, reusing `_pick`.

    Returns ``(None, assets)`` when the filer reports NEITHER goodwill nor intangibles. That is a
    real economic fact on this set — Freshpet is an organic grower and tags neither — and it is a
    different sentence from "we could not fetch".
    """
    gw = _pick(facts, GOODWILL, kind="instant")
    it = _pick(facts, INTANGIBLES, kind="instant")
    assets = _pick(facts, TOTAL_ASSETS, kind="instant")
    acquired = (((gw[0].value if gw else 0.0) + (it[0].value if it else 0.0)) / _USD_M
                if (gw or it) else None)
    return acquired, (assets[0].value / _USD_M if assets else None)


#: Trailing window, in fiscal years, for the peer write-down history. FACE-VALIDITY, never tuned:
#: five years spans a full impairment cycle for packaged food (KHC's run is FY2019-FY2025) while
#: staying short enough that the answer is about CURRENT management. It is STATED on every row
#: because each peer's window ends at its OWN balance date — fiscal calendars differ by months.
IMPAIRMENT_WINDOW_YEARS = 5

#: Tags whose scope ALREADY INCLUDES intangibles. If the goodwill family resolves to one of these,
#: adding the intangible family on top double-counts the same charge. No name on SMPL's set uses
#: it today (all ten resolved to `GoodwillImpairmentLoss`), so this guard has no live instance —
#: it is written because the tag sits in `GOODWILL_IMPAIRMENT` and the failure would be silent.
COMBINED_IMPAIRMENT_TAGS = frozenset({"GoodwillAndIntangibleAssetImpairment"})

#: The four states in READER words, DEFINED ONCE AND CARRIED IN THE DATA. The first cut wrote this
#: map twice — here and in `dossier.js` — and the duplicate-definition detector (27a) failed the
#: build on it, correctly: its baseline may only ever SHRINK, so a fourteenth entry is not an
#: option. `is_subject` is the precedent (#372, where a positional convention in one twin and a
#: field in the other disagreed): put the fact in the record and both renderers read it, rather
#: than hand-copying vocabulary that can drift one side at a time.
IMPAIRMENT_STATE_LABELS = {
    "charged": "wrote down",
    "explicit-zero": "reports nil",
    "none-in-window": "no annual obs.",
    "untagged": "does not tag",
}


def _annual_series(facts: dict[str, Any],
                   tags: tuple[str, ...]) -> tuple[str | None, list[ConceptPoint]]:
    """The first tag in the family with ANNUAL points, de-duplicated into DISJOINT years.

    THREE HAZARDS, ALL LIVE IN companyfacts, and each one silently inflates a sum:

    1. **Non-annual points.** Year-to-date and quarterly durations overlap the year that contains
       them. `is_annual` (~350-380 days) is the filter, and it is why the total can be summed
       at all.
    2. **Restatements.** The same `period_end` is re-reported across filings. Keyed by
       `period_end`, latest `filed` wins — the amended figure, not the original.
    3. **Overlapping spans that are not equal.** A 52/53-week filer can report two "annual"
       periods whose ends differ by days but whose spans overlap. Kept newest-first, and a point
       overlapping one already kept is dropped.

    Returns ``(None, [])`` when the family yields no annual point at all — `untagged`, which is a
    different fact from a zero and is classified by the caller, never here.
    """
    for tag in tags:
        pts = [p for p in points_for_tag(facts, tag)
               if p.value is not None and not p.is_instant and p.is_annual]
        if not pts:
            continue
        newest: dict[Any, ConceptPoint] = {}
        for p in sorted(pts, key=lambda x: (x.period_end, x.filed)):
            newest[p.period_end] = p                       # hazard 2: latest filed wins
        kept: list[ConceptPoint] = []
        for p in sorted(newest.values(), key=lambda x: x.period_end, reverse=True):
            if any(p.period_start < k.period_end and k.period_start < p.period_end  # type: ignore[operator]
                   for k in kept):
                continue                                    # hazard 3: overlapping spans
            kept.append(p)
        return tag, kept
    return None, []


def _pending_charge(facts: dict[str, Any], after: Any) -> tuple[float, str] | None:
    """The live YTD charge that `is_annual` EXCLUDES, summed across BOTH families on ONE window.

    SMPL's $369.0M is a 272-day year-to-date point. The annual rule that makes the window total
    summable drops it, leaving the peer-comparable figure at the $60.9M FY2025 annual charge —
    a 6x difference between two numbers a reader would otherwise assume are the same quantity.
    Carried separately and never summed into the window total (STATE.md §M3).

    ONE POINT PER FAMILY AT ONE PERIOD END, and the first cut got this wrong in the direction that
    published a wrong headline: taking the single latest point across all five tags returned SMPL's
    **$38.0M goodwill** leg and silently dropped the **$331.0M intangible** leg beside it — the
    number the whole block exists to contextualise. The families are different concepts on the same
    income statement, so they ADD; two tags within one family are aliases, so only the preferred
    one counts. Both legs must share the period end, or the sum spans two windows.
    """
    latest: Any = None
    per_family: list[tuple[Any, float]] = []
    for tags in (GOODWILL_IMPAIRMENT, INTANGIBLE_IMPAIRMENT):
        for tag in tags:
            pts = [p for p in points_for_tag(facts, tag)
                   if p.value is not None and p.value > 0 and not p.is_instant
                   and not p.is_annual and p.period_start is not None
                   and (after is None or p.period_end > after)]
            if not pts:
                continue
            p = max(pts, key=lambda x: (x.period_end, x.filed))
            per_family.append((p, p.value))
            latest = p.period_end if latest is None else max(latest, p.period_end)
            break                                    # preference order within the family
    at_end = [(p, v) for p, v in per_family if p.period_end == latest]
    if not at_end:
        return None
    return sum(v for _, v in at_end) / _USD_M, _span(at_end[0][0])


def _build_peer_impairment(facts: dict[str, Any], acquired: float | None,
                           window_end: Any) -> PeerImpairment:
    """Classify one filer into the four states, with the window STATED on the row."""
    window_start = window_end - timedelta(days=365 * IMPAIRMENT_WINDOW_YEARS + 1)
    gw_tag, gw = _annual_series(facts, GOODWILL_IMPAIRMENT)
    it_tag, it = _annual_series(facts, INTANGIBLE_IMPAIRMENT)
    combined = gw_tag in COMBINED_IMPAIRMENT_TAGS
    if combined:
        it_tag, it = None, []          # the goodwill tag already contains the intangible charge
    series = gw + it
    tags = " + ".join(t for t in (gw_tag, it_tag) if t) or None

    in_win = [p for p in series if window_start <= p.period_end <= window_end]
    charged = [p for p in in_win if p.value > 0]
    observed_ends = {p.period_end for p in in_win}
    total = sum(p.value for p in charged) / _USD_M if charged else None

    last = max((p for p in series if p.value > 0), key=lambda x: x.period_end, default=None)
    pend = _pending_charge(facts, max((p.period_end for p in series), default=None))

    if charged:
        state, note = "charged", None
    elif observed_ends:
        state = "explicit-zero"
        note = (f"the filer REPORTS this concept and states zero — {len(observed_ends)} annual "
                f"period(s) in the window under {tags}, every one nil. A measurement that they did "
                f"not write down, not a missing figure")
    elif series:
        state = "none-in-window"
        note = (f"tagged historically but NOT inside this window — the last annual observation "
                f"under {tags} ends {max(p.period_end for p in series)}. Not evidence of a clean "
                f"{IMPAIRMENT_WINDOW_YEARS} years")
    else:
        state = "untagged"
        note = (f"no annual impairment point under any of "
                f"{', '.join(GOODWILL_IMPAIRMENT + INTANGIBLE_IMPAIRMENT)} — the filer does not "
                f"tag the concept, which is NOT the same as reporting zero")
    if combined:
        note = ((note + " · ") if note else "") + (
            f"{gw_tag} covers goodwill AND intangibles, so the intangible family is deliberately "
            f"not added on top — it would double-count the same charge")

    return PeerImpairment(
        state=state, state_label=IMPAIRMENT_STATE_LABELS[state],
        window_start=window_start, window_end=window_end,
        observations=len(observed_ends), charged_years=len({p.period_end for p in charged}),
        total=round(total, 3) if total is not None else None,
        pct_acquired=(total / acquired) if (total and acquired) else None,
        last_charge_end=last.period_end if last else None,
        last_charge_amount=round(last.value / _USD_M, 3) if last else None,
        pending=round(pend[0], 3) if pend else None,
        pending_span=pend[1] if pend else None,
        tags=tags, note=note)


def build_peer_capital_intensity(
    grid: list[Any], *, resolve: Any, companyfacts: Any,
    floor: float = PEER_SIZE_FLOOR_MUSD,
) -> PeerCapitalIntensity:
    """Acquired-asset intensity for the subject and every peer, on BOTH denominators.

    THE PEER TICKERS COME FROM THE COMPS GRID, already parsed and committed — `PeerRow.ticker` and
    `PeerRow.market_cap`. Nothing re-parses the workbook, so this cannot disagree with the grid the
    page already shows. The CIQ comps panel itself carries NO goodwill and NO intangibles (checked
    across all five sheets: the only book-adjacent column is `LTM Tangible Book Value/Share`, the
    tangible version, per share, with no plain book value to subtract from), so the figures are
    EDGAR's — one cached companyfacts call per peer.

    THREE ABSENCES, THREE SENTENCES. `unresolved` (ticker → no CIK), `fetch-failed` (EDGAR
    unreachable) and `no-tag` (the filer genuinely reports neither) are different facts, and the
    reassuring one must never stand in for the alarming one — #362, where a failed fetch rendered
    as "the filer reports none" on a name carrying $1.2bn.
    """
    rows: list[PeerCapitalRow] = []
    subject: PeerCapitalRow | None = None
    for pr in grid:
        if getattr(pr, "is_median", False) or not getattr(pr, "ticker", ""):
            continue
        tk, mcap = pr.ticker, getattr(pr, "market_cap", None)
        try:
            cik = resolve(tk).cik
        except Exception:                                        # noqa: BLE001
            rows.append(PeerCapitalRow(
                ticker=tk, is_subject=bool(getattr(pr, "is_name", False)), market_cap=mcap,
                note=f"unresolved — no CIK for {tk!r}"))
            continue
        try:
            facts = companyfacts(cik)
        except Exception:                                        # noqa: BLE001
            rows.append(PeerCapitalRow(
                ticker=tk, is_subject=bool(getattr(pr, "is_name", False)), market_cap=mcap,
                note="fetch-failed — EDGAR companyfacts unreachable; this is NOT a statement that "
                     "the filer reports no goodwill"))
            continue
        acquired, assets = _acquired_and_assets(facts)
        # THE WINDOW ENDS AT THIS FILER'S OWN BALANCE DATE, not at a fleet-wide clock. Fiscal
        # calendars differ by months across this set (CAG ends in May, KHC in June, MZTI in
        # March), so one shared cut-off would give some peers four years of history and others
        # six. Each row therefore STATES its own window.
        anchor = (_pick(facts, GOODWILL, kind="instant")
                  or _pick(facts, INTANGIBLES, kind="instant")
                  or _pick(facts, TOTAL_ASSETS, kind="instant"))
        row = PeerCapitalRow(
            ticker=tk, is_subject=bool(getattr(pr, "is_name", False)),
            market_cap=mcap, acquired=acquired, total_assets=assets,
            pct_assets=(acquired / assets) if (acquired and assets) else None,
            pct_market_cap=(acquired / mcap) if (acquired and mcap) else None,
            note=(None if acquired is not None else
                  "no-tag — the filer reports neither goodwill nor intangibles (a real balance "
                  "sheet, not a data gap)"),
            impairment=(_build_peer_impairment(facts, acquired, anchor[0].period_end)
                        if anchor is not None else None))
        if getattr(pr, "is_name", False):
            subject = row
        else:
            rows.append(row)

    def _med(xs: list[float]) -> float | None:
        return median(xs) if xs else None

    peers = [r for r in rows if r.pct_assets is not None and r.pct_market_cap is not None]
    large = [r for r in peers if (r.market_cap or 0.0) >= floor]

    # THE DENOMINATOR IS THE ASSESSED SET, NOT THE LARGE SET. A peer whose window holds no annual
    # observation (CPB — impaired FY2013-FY2018, nothing since) was NOT measured over these five
    # years, and counting it among the clean names would manufacture the reassuring answer out of
    # an absence. Only `charged` and `explicit-zero` are measurements of this window.
    assessed = [r for r in large
                if r.impairment is not None
                and r.impairment.state in ("charged", "explicit-zero")]
    charged_large = [r for r in assessed if r.impairment is not None
                     and r.impairment.state == "charged"]
    return PeerCapitalIntensity(
        rows=([subject] if subject else []) + rows, size_floor=floor,
        imp_window_years=IMPAIRMENT_WINDOW_YEARS,
        imp_n_large_assessed=len(assessed), imp_n_large_charged=len(charged_large),
        imp_median_large_pct=_med([r.impairment.pct_acquired for r in charged_large
                                   if r.impairment is not None
                                   and r.impairment.pct_acquired is not None]),
        imp_subject_pct=(subject.impairment.pct_acquired
                         if subject and subject.impairment else None),
        imp_subject_state=(subject.impairment.state if subject and subject.impairment else None),
        subject_pct_assets=subject.pct_assets if subject else None,
        subject_pct_market_cap=subject.pct_market_cap if subject else None,
        median_all_assets=_med([r.pct_assets for r in peers if r.pct_assets is not None]),
        median_all_market_cap=_med(
            [r.pct_market_cap for r in peers if r.pct_market_cap is not None]),
        median_large_assets=_med([r.pct_assets for r in large if r.pct_assets is not None]),
        median_large_market_cap=_med(
            [r.pct_market_cap for r in large if r.pct_market_cap is not None]),
        n_all=len(peers), n_large=len(large))
