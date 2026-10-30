"""XBRL concept aliases + point extraction from SEC ``companyfacts``.

XBRL tagging is inconsistent across filers — e.g. revenue may be tagged ``Revenues`` or
``RevenueFromContractWithCustomerExcludingAssessedTax``. Each logical concept therefore maps to a
**priority-ordered list of us-gaap tags**; we use the first tag a filer actually reports. Values are
extracted **as-reported with the filing date** (point-in-time), and the latest figure for a period
takes the most recent ``filed`` (handling restatements without mutating earlier rows).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, NamedTuple

from pydantic import BaseModel

# logical concept -> priority-ordered us-gaap tags (first present wins)
CONCEPT_ALIASES: dict[str, list[str]] = {
    # Ordered by MEANING, not by which tag happens to have data (#160's preference, extended here
    # so the shared resolver and the anchor can never disagree about what "total revenue" is):
    #   ASC-606 Excluding  →  the modern total, net of assessed tax (the intended denominator)
    #   ASC-606 Including  →  the same total, gross of assessed tax
    #   Revenues           →  the pre-606 catch-all; total for older filers
    #   SalesRevenueNet    →  pre-606 and, for some filers, only a COMPONENT — last resort
    # Previously `Revenues` outranked `Including`, so the shared path and the anchor could pick
    # different denominators for the same filer.
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "operating_income": ["OperatingIncomeLoss"],
    # PRE-TAX, and it exists to be SUBTRACTED FROM rather than read on its own: pre-tax minus
    # operating IS the non-operating block, by the arithmetic of the income statement. That
    # derivation is the whole reason this concept is here — the obvious alternative, reading a
    # one-off gain tag directly, is what the corpus refuses. UBER's Q2-2026 revaluation is carried
    # by THREE overlapping tags at three DIFFERENT values (EquitySecuritiesFvNiUnrealizedGainLoss
    # 1,727M · DebtAndEquitySecuritiesGainLoss 1,612M · OtherNonoperatingIncomeExpense 1,342M), and
    # the aggregate `NonoperatingIncomeExpense` is absent for roughly half the fleet and was
    # abandoned by UBER itself after 2025-09-30. Choosing among those is same-window/different-basis
    # — the class the buyback average was refused for. Subtracting two totals the filer states is
    # not a choice at all.
    "pretax_income": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterest"
        "AndIncomeLossFromEquityMethodInvestments",
    ],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "eps_diluted": [
        "EarningsPerShareDiluted",
        "IncomeLossFromContinuingOperationsPerDilutedShare",
    ],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "dep_amort": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
        "DepreciationAndAmortization",
    ],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "debt_current": ["LongTermDebtCurrent", "DebtCurrent"],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    # shares outstanding lives in the dei namespace (cover page) with a us-gaap fallback
    "shares": [
        "EntityCommonStockSharesOutstanding",
        "CommonStockSharesOutstanding",
        "CommonStockSharesIssued",
    ],
}

# XBRL concepts span two taxonomies; dei holds cover-page facts (shares), us-gaap the financials.
_NAMESPACES = ("dei", "us-gaap")

# A reported FY duration is never exactly 365: 52/53-week filers land on 358–371, leap years on 366.
# The window is deliberately TIGHT — wide enough for every real fiscal year, far too narrow for a
# quarter (~90d) or a half (~180d). See ConceptPoint.is_annual for why duration must be necessary.
ANNUAL_MIN_DAYS = 350
ANNUAL_MAX_DAYS = 380


class ConceptPoint(BaseModel, frozen=True):
    """One reported value for a concept over a period (flow) or at an instant (balance-sheet)."""

    concept: str  # the logical concept (e.g. "operating_income")
    tag: str  # the us-gaap tag actually used
    unit: str
    value: float
    period_start: date | None  # None for instant (balance-sheet) facts
    period_end: date
    filed: date  # the knowable / as-of date
    fy: int | None
    fp: str | None
    form: str | None
    accession: str | None

    @property
    def is_instant(self) -> bool:
        return self.period_start is None

    @property
    def is_annual(self) -> bool:
        """A full-year FLOW: the period must actually span ~12 months.

        DURATION IS NECESSARY, never optional. The old rule was
        ``fp == "FY" or days >= 300`` — an ``or``, so a 90-day quarter stamped ``fp="FY"``
        passed with NO duration check at all. EDGAR stamps every quarterly point inside a
        10-K with ``fp="FY"``, so that admitted Q1 values as if they were the year: EPAM's
        FY2016 revenue read 264 (Q1) instead of 1,160 (FY), which fired a false
        ``revenue_tag_conflict`` and capped a clean anchor to `weak`.

        ``fp`` is now only a fallback for points that omit it entirely — it can never
        override the measured span."""
        if self.period_start is None:
            return False
        return ANNUAL_MIN_DAYS <= (self.period_end - self.period_start).days <= ANNUAL_MAX_DAYS


def _parse_date(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


#: A tag is ABANDONED when it lags the filer's OWN newest reported fact by more than this. Measured
#: against the filer's frontier, not against today, so a filer who is simply late is never called
#: stale — only one that kept filing while this particular tag stopped. 550 days clears an annual
#: series (up to ~365d behind a quarterly frontier, plus filing lag and a 53-week year) and is far
#: below every abandonment in evidence: the nearest real case measured is 670d and the worst 5,907d.
STALE_TAG_LAG_DAYS = 550

#: How far an alias may trail the BEST alias of its own concept before it counts as left behind.
#: 200 days sits inside one annual filing cycle, so an alias the filer still updates never trips it
#: (equally-current siblings measure 0d apart, and priority order is preserved), while a full cycle
#: behind — GOOGL revenue stopping at FY2024 while `Revenues` reached FY2025, 365d — does.
SIBLING_LAG_DAYS = 200


def filer_frontier(facts: dict[str, Any]) -> date | None:
    """The newest period end the filer reports under ANY tag — its own reporting clock."""
    nsmap = facts.get("facts", {})
    ends: list[date] = []
    for ns in _NAMESPACES:
        for body in (nsmap.get(ns) or {}).values():
            for rows in (body.get("units") or {}).values():
                for r in rows:
                    d = _parse_date(r.get("end"))
                    if d is not None:
                        ends.append(d)
    return max(ends) if ends else None


def facts_as_of(facts: dict[str, Any], as_of: date) -> dict[str, Any]:
    """``facts`` as they stood on ``as_of``: every row FILED after it removed, same shape.

    THE CUT IS ON ``filed``, NEVER ON ``end``. ``filed`` is the day a number became public; ``end``
    is the day the period it describes closed — weeks before a 10-K is filed — and every later
    filing re-reports that period as a comparative, restated or not. A cut on ``end`` admits both
    a figure not yet filed and every later RESTATEMENT of a closed period: WOR's FY2023 operating
    income was $212.4M as filed on 2023-07-31 and $29.8M as restated on 2024-07-30 after the steel
    spin-off, and on any day between only the first was knowable.

    THE WHOLE BLOB, NOT THE RETURNED POINTS. :func:`extract_points` picks an alias by how far its
    series reaches against its SIBLING aliases', and net debt reads a dozen tags at one
    balance-sheet date; both would see the future through a later filing even when every point
    they finally return was filed in time. Pruning before any reader runs makes each of them
    point-in-time without threading a date through every one.

    ``filed == as_of`` is KEPT, as in every ``p.filed <= d`` reader here: a row carries a date, not
    an acceptance time. A row whose ``filed`` is missing is DROPPED — its knowable date cannot be
    shown. A unit, tag or namespace left with no row is dropped too, so a namespace not yet reported
    on ``as_of`` cannot shadow one that was (:func:`points_for_tag` takes the FIRST one present).
    """
    nsmap: dict[str, Any] = {}
    for ns, tags in (facts.get("facts") or {}).items():
        kept_tags: dict[str, Any] = {}
        for tag, body in (tags or {}).items():
            units: dict[str, list[dict[str, Any]]] = {}
            for unit, rows in (body.get("units") or {}).items():
                kept = [r for r in rows
                        if (filed := _parse_date(r.get("filed"))) is not None and filed <= as_of]
                if kept:
                    units[unit] = kept
            if units:
                kept_tags[tag] = {**body, "units": units}
        if kept_tags:
            nsmap[ns] = kept_tags
    return {**facts, "facts": nsmap}


def extract_points(facts: dict[str, Any], concept: str, *, currency: str = "USD",
                   as_of: date | None = None) -> list[ConceptPoint]:
    """Extract all reported points for a logical concept, trying alias tags in priority order.

    MC1 — AN ABANDONED ALIAS IS SKIPPED, NOT SERVED. First-present-wins alone hands back whatever
    the filer tagged FIRST in our priority order, even if that series died years ago, because a
    dead series still carries a confident filed date. Measured live at megacaps: Amazon's
    ``PaymentsToAcquirePropertyPlantAndEquipment`` last reports 2017-03-31 and Nvidia's 2020-07-26,
    while BOTH filers report ``PaymentsToAcquireProductiveAssets`` currently — the right number was
    already in this map, one line below the wrong one, and the resolution order withheld it.

    So the freshness test runs BEFORE the alias is accepted, and a stale one falls through to the
    next. When EVERY alias is stale the FIRST present one is still returned rather than refused: a
    tag also stops being reported when the FACT ceases (a company that repaid its current debt stops
    tagging it), and turning that into UNKNOWN would manufacture a hole where the filer simply has
    nothing to report. Distinguishing abandonment from cessation needs the filer's own words, not a
    date — so this fixes what it can prove and leaves the rest visible via ``stale_served``.

    THE ALL-STALE FALLBACK IS THE FIRST ALIAS, NEVER THE LAST. ``CONCEPT_ALIASES`` is ordered by
    MEANING, not by convenience: ``SalesRevenueNet`` is a last resort because for some filers it is
    only a COMPONENT of revenue, and ``CommonStockSharesIssued`` is not shares OUTSTANDING. Falling
    back to whichever alias happened to be iterated last would silently invert that ordering when
    freshness can separate nothing — a wrong-by-meaning number in place of a merely-old one.

    ``currency`` and ``as_of`` are :func:`points_for_tag`'s: dollars only, unless the caller asks
    for the filer's own currency (``REPORTING``), judged as of the reader's date.
    """
    return _resolve(facts, concept, filer_frontier(facts), currency, as_of)


def _reach(points: list[ConceptPoint], *, annual_grain: bool) -> date | None:
    """How far forward an alias's series reaches, at the grain its consumers read it.

    THE GRAIN IS THE WHOLE POINT (review of #531). The first cut measured an alias's newest point
    of ANY duration, but the consumers of these concepts read the ANNUAL series. An alias can
    therefore carry perfectly fresh QUARTERLIES and no annual series at all, sail through a
    freshness test, and starve every annual reader — which is exactly the UBER defect this guard
    was built for, still live on BRBR and MVST when the review found it.
    """
    pool = [p for p in points if p.is_annual] if annual_grain else points
    return max((p.period_end for p in pool), default=None)


def _resolve(
    facts: dict[str, Any], concept: str, frontier: date | None, currency: str = "USD",
    as_of: date | None = None,
) -> list[ConceptPoint]:
    """The alias walk of :func:`extract_points`, taking an already-computed frontier.

    Split out so ``stale_served`` scans the (large) companyfacts blob for the frontier ONCE rather
    than three times — its own call, plus one inside the ``extract_points`` it delegates to.
    """
    present = [(tag, pts) for tag in CONCEPT_ALIASES[concept]
               if (pts := points_for_tag(facts, tag, concept=concept, currency=currency,
                                         as_of=as_of))]
    if not present:
        return []
    first_present = present[0][1]
    if frontier is None:
        return first_present

    # MEASURED AGAINST THE BEST SIBLING, NOT THE FILER'S WHOLE FRONTIER (review of #531). Comparing
    # each alias to the filer's newest fact of any kind let GOOGL through: its served revenue alias
    # sits 456d behind that frontier — inside the 550d allowance — while its ANNUAL series stops at
    # FY2024 and `Revenues` already carries FY2025. The question is not "is this alias old" but
    # "has a SIBLING alias for this same concept moved on without it", which is what abandonment
    # looks like from the outside.
    annual_grain = any(any(p.is_annual for p in pts) for _, pts in present)
    reaches = {tag: _reach(pts, annual_grain=annual_grain) for tag, pts in present}
    best = max((d for d in reaches.values() if d is not None), default=None)
    if best is None:
        return first_present
    for tag, points in present:
        got = reaches[tag]
        # ORDER IS MEANING, so the FIRST alias not left behind wins — never simply the one reaching
        # furthest, which would promote a component tag (SalesRevenueNet) over the real one.
        if got is not None and (best - got).days <= SIBLING_LAG_DAYS:
            return points
    # every alias stale: fall back to priority order, and let ``stale_served`` name it for the sweep
    return first_present


def stale_served(facts: dict[str, Any], concept: str) -> tuple[str, int] | None:
    """``(tag, lag_days)`` when ``extract_points`` had to serve a stale alias — else ``None``.

    The reporting half of MC1: `extract_points` fixes what a fresher alias can fix, and this names
    what it could not, so the monthly sweep can show a human the tags whose series has gone quiet
    rather than leaving them to be discovered in a rendered page.
    """
    frontier = filer_frontier(facts)
    if frontier is None:
        return None
    pts = _resolve(facts, concept, frontier)
    if not pts:
        return None
    lag = (frontier - max(p.period_end for p in pts)).days
    return (pts[0].tag, lag) if lag > STALE_TAG_LAG_DAYS else None


# --- the currency a filer reports in (STATE §5.0 row 4, FPI1a) ---------------------------------

#: A MONETARY unit as companyfacts writes it: an ISO 4217 code alone ("CNY") or over a quantity
#: ("CNY/shares", "USD/bbl"). Every other unit ("shares", "pure", "Employees") carries no currency.
#: Two crypto units fit the shape ("BTC", "ETH") and count as currencies here; no reader asks for
#: one.
_MONETARY_UNIT = re.compile(r"^([A-Z]{3})(?:/|$)")

#: ``currency=REPORTING`` reads a filer's figures in the currency its statements are in, whatever it
#: is. Only for a reading the currency cannot move: a ratio of two figures in one currency, a rank
#: within one series.
REPORTING = "reporting"
#: ``currency=EVERY`` reads every unit, money in any currency included. For a period's DATES only:
#: a fiscal year stated only in a filer's old currency is still that year (Algonquin's 2011-2017,
#: in its CAD 40-Fs). Never for a value.
EVERY = "every"

#: The balance-sheet totals whose units name the currency of a filer's statements.
_CURRENCY_ANCHORS = ("Assets", "Liabilities", "LiabilitiesAndStockholdersEquity",
                     "StockholdersEquity")


def unit_currency(unit: str) -> str | None:
    """The ISO code a monetary unit is in (``"CNY/shares"`` → ``"CNY"``); None for a unit with no
    currency (``"shares"``, ``"pure"``)."""
    m = _MONETARY_UNIT.match(unit)
    return m.group(1) if m else None


def reporting_currency(facts: dict[str, Any], as_of: date | None = None) -> str | None:
    """The currency the filer's statements are in: the most frequent currency among its
    balance-sheet totals (:data:`_CURRENCY_ANCHORS`) in its newest annual report, or in its newest
    filing when it has filed no annual report. Without those totals, every us-gaap monetary fact
    counts. None when no monetary fact is tagged at all.

    NEVER THE UNIT OF ONE FACT. Many foreign filers also tag a USD CONVENIENCE TRANSLATION: their
    newest year at one period-end rate. QFIN's newest balance sheet carries CNY twice (two
    year-ends) and USD once, and the first cut of #837's measurement, which read the unit of
    `Assets`, put it in USD. A filer reporting in USD may tag foreign figures too: its statements
    from before it moved to USD (Algonquin's CAD 40-Fs), or a stray amount (Unum Group's diluted
    EPS in AUD per share, in a 10-Q filed 2023-05-03). Counting the totals in one filing answers
    every case.

    MEASURED 2026-10-28 on 2,543 cached companyfacts, one per CIK (the primary checkout's, the
    2026-10-16 replay worktree's and FPI1a's scratch fetches, newest first). 2,258 carry us-gaap
    money facts filed with an annual report, 2,189 of them a total. On 2,257 this agrees with the
    count over EVERY money fact of the newest annual report. The one exception is Fresenius Medical
    Care: its totals stop at its last US GAAP 20-F (USD), and its IFRS filings since tag ten EUR
    us-gaap facts. Its USD series are what a reader is served, and the stale-annual checks hold
    them. 46 filings carry two currencies, never tied, and the runner-up is at most half: the
    convenience translation's one year against two. A tie would go to the currency that is not
    USD, because a convenience translation is always into USD. 102 come out other than USD
    (CNY 38, CAD 14, EUR 11 …).

    AS OF A DATE, judged on the rows filed by ``as_of`` (all of them when None), so a reader at a
    reference date gets the currency the filer reported in then: JOYY's statements were in CNY
    through its FY2020 20-F and in USD from its FY2021 20-F, filed 2022-04-29. Judged on today's
    filings, a read as of 2021-06-30 served its USD convenience translations as dollars (round 1
    of #844). A blob already cut by :func:`facts_as_of` is judged the same way."""
    gaap = (facts.get("facts") or {}).get("us-gaap") or {}
    rows = (_currency_rows(gaap, _CURRENCY_ANCHORS, as_of)
            or _currency_rows(gaap, tuple(gaap), as_of))
    if not rows:
        return None
    annual = [(cur, r) for cur, r in rows
              if str(r.get("form") or "").upper().startswith(ANNUAL_REPORT_FORMS)]
    pool = annual or rows
    newest = max((str(r.get("filed") or ""), str(r.get("accn") or "")) for _, r in pool)
    count = Counter(cur for cur, r in pool
                    if (str(r.get("filed") or ""), str(r.get("accn") or "")) == newest)
    top = max(count.values())
    return min(count, key=lambda c: (count[c] != top, c == "USD", c))


def _currency_rows(gaap: dict[str, Any], tags: tuple[str, ...],
                   as_of: date | None = None) -> list[tuple[str, dict[str, Any]]]:
    """(currency, row) for every row of ``tags`` in a plain currency unit (not per share), filed by
    ``as_of`` when one is given."""
    cut = as_of.isoformat() if as_of is not None else None
    out: list[tuple[str, dict[str, Any]]] = []
    for tag in tags:
        for unit, rows in ((gaap.get(tag) or {}).get("units") or {}).items():
            cur = unit_currency(unit)
            if cur is not None and "/" not in unit:
                out.extend((cur, r) for r in rows
                           if cut is None or str(r.get("filed") or "9999") <= cut)
    return out


def foreign_currency(facts: dict[str, Any], as_of: date | None = None) -> str | None:
    """The filer's reporting currency (as of ``as_of``) when it is not USD — the reason its money
    figures are withheld (:func:`points_for_tag`) — else None."""
    cur = reporting_currency(facts, as_of)
    return cur if cur not in (None, "USD") else None


def currency_withheld(currency: str) -> str:
    """The one sentence every reader withholding a foreign reporter's figures gives as its
    reason. It names the US GAAP figures, the only ones these readers read: JMIA reports under IFRS
    in USD now, and its us-gaap facts, all from before, are in EUR."""
    return (f"the filer's US GAAP figures are in {currency}, and a {currency} figure is never read "
            f"as dollars — converting it is STATE §5.0 row 4's FPI1b")


def _served_currency(facts: dict[str, Any], currency: str, as_of: date | None) -> str | None:
    """The one currency :func:`points_for_tag` serves for ``currency``; None serves none."""
    reported = reporting_currency(facts, as_of)
    if currency == REPORTING:
        return reported or "USD"
    return currency if reported in (None, currency) else None


def points_for_tag(facts: dict[str, Any], tag: str, *, concept: str = "",
                   currency: str = "USD", as_of: date | None = None) -> list[ConceptPoint]:
    """All reported points under exactly ``tag`` (the first namespace that carries it, in priority
    order). Takes the tag EXPLICITLY — no ``CONCEPT_ALIASES`` lookup, so callers that need a single
    known tag never mutate the shared alias map (which extractors read from parallel assembly
    threads). ``concept`` only labels the returned points; defaults to the tag itself.

    ONE CURRENCY, AND BY DEFAULT ONLY DOLLARS (FPI1a). A money fact is served only in ``currency``
    (USD unless the caller asks otherwise), and only when that is the filer's
    :func:`reporting_currency`:
    - a filer reporting in USD gets its USD facts and none of its foreign ones: its statements
      from before it moved to USD (Algonquin's CAD, SIMO's TWD 20-F/A of 2012) or a stray amount;
    - a filer reporting in another currency gets NO money fact, not even its USD convenience
      translation. QFIN's newest annual revenue was served as CNY 19,205,059,000 to readers that
      print dollars; a translation at one year-end rate is an FX policy, and that is FPI1b's.
    ``currency=REPORTING`` serves the filer's own currency instead, for a reading it cannot move,
    and ``currency=EVERY`` every unit, for a period's dates. A unit with no currency (shares,
    pure) is served either way.

    THE CURRENCY IS JUDGED AT THE READER'S DATE: ``as_of`` is a dated reader's reference date, and
    the currency is the one the filer reported in on it (:func:`reporting_currency`). It cuts no
    point: each reader keeps its own filed-date bound on the values it reads."""
    nsmap = facts.get("facts", {})
    node = None
    for ns in _NAMESPACES:
        node = nsmap.get(ns, {}).get(tag)
        if node:
            break
    if not node:
        return []
    points: list[ConceptPoint] = []
    units = node.get("units", {})
    served = (_served_currency(facts, currency, as_of)
              if currency != EVERY and any(unit_currency(u) for u in units) else None)
    for unit, rows in units.items():
        cur = unit_currency(unit)
        if cur is not None and currency != EVERY and cur != served:
            continue
        for r in rows:
            end = _parse_date(r.get("end"))
            filed = _parse_date(r.get("filed"))
            if end is None or filed is None or r.get("val") is None:
                continue
            points.append(
                ConceptPoint(
                    concept=concept or tag,
                    tag=tag,
                    unit=unit,
                    value=float(r["val"]),
                    period_start=_parse_date(r.get("start")),
                    period_end=end,
                    filed=filed,
                    fy=r.get("fy"),
                    fp=r.get("fp"),
                    form=r.get("form"),
                    accession=r.get("accn"),
                )
            )
    return points


def latest_annual(points: list[ConceptPoint]) -> ConceptPoint | None:
    """Latest full-year flow value (most recent period_end, then most recent filing)."""
    annual = [p for p in points if p.is_annual]
    if not annual:
        return None
    return max(annual, key=lambda p: (p.period_end, p.filed))


def annual_by_period(points: list[ConceptPoint]) -> dict[date, ConceptPoint]:
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


#: An annual is NOT CURRENT once its own concept carries a period ending at least this long after
#: it: a whole fiscal year (the shortest one :attr:`ConceptPoint.is_annual` admits) has then closed
#: past it AND been reported, so the annual describes the year before last. MEASURED 2026-10-27 on
#: 2,161 cached companyfacts: 14,791 of 14,918 served annuals trail their concept's newest period
#: by at most 280d (a third-quarter 10-Q in a 53-week year), the next are KalVista's seven at 335d
#: (an eight-month transition period, after which its newest annual IS its last full year), and
#: then 120 at 365d or more. Set by that gap — never by what a reading would have paid.
ANNUAL_STALE_DAYS = ANNUAL_MIN_DAYS


class StaleAnnual(NamedTuple):
    """The latest annual of a concept, withheld because the concept has been reported past it.

    Both ends travel with the refusal, so a reader can go and check it: the annual that was served
    and the newer period that proves it is not the current year."""

    concept: str
    tag: str  # the alias whose annual was served
    period_end: date  # that annual's period end
    newer_tag: str  # the alias carrying the concept's newest period (the filer's: see below)
    newer_end: date  # that period's end
    lag_days: int
    # True when the newer period is the FILER's newest fiscal year (:func:`behind_filer`), not
    # one of this concept's own: the concept stopped on every alias and the filer moved on.
    against_filer: bool = False

    @property
    def note(self) -> str:
        if self.against_filer:
            return (f"stale annual {self.concept}: {self.tag} for the year to "
                    f"{self.period_end.isoformat()}, {self.lag_days}d behind the filer's newest "
                    f"fiscal year ({self.newer_tag} to {self.newer_end.isoformat()}) — more "
                    f"than one fiscal year behind")
        return (f"stale annual {self.concept}: {self.tag} for the year to "
                f"{self.period_end.isoformat()}, {self.lag_days}d behind {self.newer_tag} to "
                f"{self.newer_end.isoformat()} — not the current year")


def concept_frontier(
    facts: dict[str, Any], concept: str, substitute: tuple[str, ...] = ()
) -> ConceptPoint | None:
    """The point with the newest period end ANY alias of ``concept`` carries, of any duration.

    Every alias, not the one :func:`extract_points` serves: the served alias is the one this is
    measured against. A tie goes to the alias first in priority order. ``substitute`` adds the
    tags of a substitute :func:`annual_line` accepted, since they now carry the concept too.

    A point whose period ends AFTER the day it was filed is skipped: it is a forward-dated
    context, not a period the filer has reported. Measured 2026-10-27 on the 2,161 cached
    companyfacts: 61 such points in 18 filers across the eight flow concepts' aliases."""
    newest: ConceptPoint | None = None
    for tag in (*CONCEPT_ALIASES[concept], *substitute):
        for p in points_for_tag(facts, tag, concept=concept):
            if p.period_end > p.filed:
                continue
            if newest is None or p.period_end > newest.period_end:
                newest = p
    return newest


def stale_against(annual: ConceptPoint, newest: ConceptPoint | None) -> StaleAnnual | None:
    """``annual`` judged against its concept's newest point — a :class:`StaleAnnual` when it is
    :data:`ANNUAL_STALE_DAYS` or more behind, else ``None``."""
    if newest is None:
        return None
    lag = (newest.period_end - annual.period_end).days
    if lag < ANNUAL_STALE_DAYS:
        return None
    return StaleAnnual(concept=annual.concept, tag=annual.tag, period_end=annual.period_end,
                       newer_tag=newest.tag, newer_end=newest.period_end, lag_days=lag)


#: The flow concepts whose annual periods date the filer's newest fiscal year.
FLOW_CONCEPTS = ("revenue", "operating_income", "pretax_income", "net_income", "eps_diluted",
                 "operating_cash_flow", "capex", "dep_amort")

#: An annual is NOT CURRENT once the FILER's newest fiscal year ends at least this long after it:
#: two fiscal years (the shortest :attr:`ConceptPoint.is_annual` admits) have then closed past it,
#: so it is more than one fiscal year behind. MEASURED 2026-10-27 on 2,161 cached companyfacts,
#: each annual the screen served (main 64f91b2a) against its filer's newest fiscal year: 8,811 at
#: 0–29d, 10 at 60–299d (a 10-Q's trailing column, a transition period), 53 at 360–371d (one
#: fiscal year behind, which stays), NOTHING from 372d to 727d, then 273 at 728d or more. Set by
#: that gap — never by what a reading would have paid.
FILER_STALE_DAYS = 2 * ANNUAL_STALE_DAYS


def filer_fiscal_year(facts: dict[str, Any]) -> ConceptPoint | None:
    """The point with the newest ANNUAL period any alias of any :data:`FLOW_CONCEPTS` carries —
    the filer's newest reported fiscal year. A tie goes to the concept, then alias, first in order.

    Its annual periods only, never the filer's frontier of any tag (``filer_frontier``), which
    counts quarters, instants and contexts dated years ahead (Innodata's reaches 2034). A period
    ending after its own filing date is skipped, as in :func:`concept_frontier`. A 10-Q's
    trailing-twelve-month column counts, as it does for every annual reader here (Amazon tags
    one); :data:`FILER_STALE_DAYS` leaves room for it."""
    newest: ConceptPoint | None = None
    for concept in FLOW_CONCEPTS:
        for tag in CONCEPT_ALIASES[concept]:
            for p in points_for_tag(facts, tag, concept=concept):
                if not p.is_annual or p.period_end > p.filed:
                    continue
                if newest is None or p.period_end > newest.period_end:
                    newest = p
    return newest


def behind_filer(annual: ConceptPoint, fiscal_year: ConceptPoint | None) -> StaleAnnual | None:
    """``annual`` judged against the filer's newest fiscal year — a :class:`StaleAnnual` when it
    is more than one fiscal year behind (:data:`FILER_STALE_DAYS`), else ``None``."""
    if fiscal_year is None:
        return None
    lag = (fiscal_year.period_end - annual.period_end).days
    if lag < FILER_STALE_DAYS:
        return None
    return StaleAnnual(concept=annual.concept, tag=annual.tag, period_end=annual.period_end,
                       newer_tag=fiscal_year.tag, newer_end=fiscal_year.period_end,
                       lag_days=lag, against_filer=True)


#: Where a filer may move a concept's annual line once its aliases stop: each entry is one tag,
#: or a split whose same-period values SUM to the line. Chosen by MEANING — the whole line under
#: another name, never a component of it: no class of PP&E (machinery, construction in progress),
#: no capex net of disposal proceeds, no `Depreciation` without the amortization, no "other" D&A.
#: Measured 2026-10-27 on the legs #821 withholds (2,161 cached companyfacts): no tag of that kind
#: carries a later operating income or operating cash flow, so those have none; diluted EPS's one
#: candidate (`EarningsPerShareBasicAndDiluted`) recovered none of 23 legs, its own series having
#: stopped too, and no production reader takes the snapshot's EPS. A substitute is only a
#: CANDIDATE: :func:`annual_line` accepts it per filer, on evidence.
SUBSTITUTES: dict[str, tuple[tuple[str, ...], ...]] = {
    "capex": (("PaymentsToAcquireOtherPropertyPlantAndEquipment",),
              ("PaymentsToAcquireOtherProductiveAssets",),
              ("PaymentsForCapitalImprovements",)),
    "dep_amort": (("Depreciation", "AmortizationOfIntangibleAssets"),),
}

#: A substitute is the old line only where it reports the old line's figure, to rounding, in the
#: LATEST year both carry — the handover. A re-tag is the same line, so it carries the same
#: number; a different number is a different quantity. MEASURED 2026-10-27 on the substitutes
#: above for the legs #821 withholds (112 with such a year): 44 within 0.05%, NOTHING from 0.05% to
#: 0.15%, then a continuum — AbCellera's split 0.15% (30% the year before), DiamondRock 0.40%,
#: Thor's two capex tags 1.13% (one 10-K carries both, at $121.62M and $122.99M: two quantities),
#: Grocery Outlet's split 1.63% short (a component left out, in both years), Ecovyst's 23% short,
#: and 51 beyond 5%. The latest year, not every year: Scotts' split matches exactly from FY2018 to
#: FY2024 and differs 5–17% in FY2014–FY2017, which its filings tagged on another basis. Set by
#: that gap — never by what a reading would have paid.
SUBSTITUTE_TOLERANCE = 0.001


class AnnualLine(NamedTuple):
    """A concept's annual values by period end, and the substitute continuing them, if any."""

    by_period: dict[date, ConceptPoint]
    substitute: tuple[str, ...]  # the substitute's tags; () when the aliases alone carry it


def _substitute_series(facts: dict[str, Any], concept: str, tags: tuple[str, ...],
                       unit: str) -> dict[date, ConceptPoint]:
    """A substitute's annual values by period end, in ``unit``; a split sums its tags for each
    period they ALL carry over the same span, and is stamped with every tag it read."""
    maps = [annual_by_period([p for p in points_for_tag(facts, t, concept=concept)
                              if p.unit == unit]) for t in tags]
    if len(maps) == 1:
        return maps[0]
    out: dict[date, ConceptPoint] = {}
    for end in set.intersection(*(set(m) for m in maps)):
        legs = [m[end] for m in maps]
        if any(p.period_start != legs[0].period_start for p in legs):
            continue
        last = max(legs, key=lambda p: p.filed)
        out[end] = last.model_copy(update={"tag": " + ".join(tags),
                                           "value": sum(p.value for p in legs)})
    return out


def _agrees(old: dict[date, ConceptPoint], new: dict[date, ConceptPoint]) -> bool:
    """``new`` reports ``old``'s figure, within :data:`SUBSTITUTE_TOLERANCE`, in the LATEST year
    both carry over the same span — and there is such a year."""
    years = [e for e in old.keys() & new.keys() if old[e].period_start == new[e].period_start]
    if not years:
        return False
    end = max(years)
    return abs(new[end].value - old[end].value) <= SUBSTITUTE_TOLERANCE * abs(old[end].value)


def _continuation(sub: dict[date, ConceptPoint], last: date) -> dict[date, ConceptPoint]:
    """``sub``'s years after ``last``, while they run unbroken: each ends at most one fiscal year
    (:data:`ANNUAL_MAX_DAYS`) after the one before and carries a figure other than zero."""
    out: dict[date, ConceptPoint] = {}
    prev = last
    for end in sorted(e for e in sub if e > last):
        if (end - prev).days > ANNUAL_MAX_DAYS or sub[end].value == 0:
            break
        out[end] = sub[end]
        prev = end
    return out


def annual_line(facts: dict[str, Any], concept: str) -> AnnualLine:
    """``concept``'s annual values by period end: its served alias's (:func:`extract_points`),
    continued past their last year by a :data:`SUBSTITUTES` entry the filer has PROVEN to be the
    same line.

    A FILER THAT RE-TAGS A LINE HAS NOT STOPPED REPORTING IT. Scotts Miracle-Gro's combined D&A
    ends at FY2024; its FY2025 is `Depreciation` + `AmortizationOfIntangibleAssets`, and in FY2023
    and FY2024 those two summed to the combined figure exactly ($92.5M, $80.6M). So the split
    continues the line. Ecovyst's split ran 23% short of its combined D&A in FY2024: a component,
    not the line, and it is refused.

    THE EVIDENCE IS THE OVERLAP, never the tag name: a substitute is accepted only where it reports
    the served line's figure in the latest year both carry (:data:`SUBSTITUTE_TOLERANCE`). With no
    such year there is nothing to check it against, and it is refused. It then serves only periods
    AFTER the served line's last annual — never in place of a year the aliases report. Two
    accepted substitutes that disagree on those later years are refused together.

    THE CONTINUATION MUST BE UNBROKEN (:func:`_continuation`): one fiscal year after another from
    the served line's last, each a figure other than zero. A missing year or a zero ends it.
    Lantheus's `PaymentsToAcquireOtherProductiveAssets` matched its capex at the FY2023 handover
    ($45.3M), then read $80.9M and, for FY2025, $0 — while `PaymentsForCapitalImprovements` carried
    $36.1M. A line the filer emptied is not a year it spent nothing."""
    served = annual_by_period(extract_points(facts, concept))
    if not served:
        return AnnualLine(served, ())
    last = max(served)
    unit = served[last].unit
    accepted: list[tuple[tuple[str, ...], dict[date, ConceptPoint]]] = []
    for tags in SUBSTITUTES.get(concept, ()):
        sub = _substitute_series(facts, concept, tags, unit)
        later = _continuation(sub, last)
        if later and _agrees(served, sub):
            accepted.append((tags, later))
    if not accepted:
        return AnnualLine(served, ())
    tags, later = accepted[0]
    if any(not _agrees(later, other) for _, other in accepted[1:]):
        return AnnualLine(served, ())
    return AnnualLine({**served, **later}, tags)


def current_annual(
    facts: dict[str, Any], concept: str, fiscal_year: ConceptPoint | None = None
) -> tuple[ConceptPoint | None, StaleAnnual | None]:
    """The latest annual an annual reader may serve AS CURRENT: ``(point, None)``; ``(None, why)``
    when it is stale; ``(None, None)`` when the concept has no annual at all.

    ``fiscal_year`` is the filer's newest (:func:`filer_fiscal_year`), computed when not given;
    a caller judging several concepts passes it once.

    THE ANNUAL-GRAIN LAG CHECK (STATE.md §5.0 row 11). :func:`extract_points` picks an alias by how
    far its ANNUAL series reaches against its siblings', and that is right for choosing an alias.
    It cannot see that the annual it serves is old: a filer that moves to another tag, or stops
    tagging the annual while still tagging quarters, leaves the walk serving a year that closed
    long ago. Measured 2026-10-26: Climb Global's capex for FY2019, served beside FY2025 operating
    cash flow; AbCellera's D&A for FY2023, added to FY2025 operating income.

    ``stale_served`` cannot catch this and is not the check. It measures the served tag's newest
    point of ANY duration against the filer's frontier, so a tag still carrying fresh quarters
    passes with a years-old annual (AbCellera's lags 307d, under its 550d), and the filer's
    frontier is any tag at all, including future-dated contexts (Innodata's reaches 2034).
    This measures the served ANNUAL against the newest period of its OWN concept.

    THEN AGAINST THE FILER (:func:`behind_filer`). A concept that has stopped on EVERY alias passes
    the first check, since its newest period IS the served annual's: Johnson & Johnson's
    `OperatingIncomeLoss` ends at FY2014 and SL Green's capex at FY2019, each served beside FY2025
    figures. So the annual must also be at most one fiscal year behind the filer's newest fiscal
    year. One year behind stays: that is the newest figure the filer gives for the concept.

    The annual read is the concept's :func:`annual_line`: a substitute the filer proved to be the
    same line continues it, and is judged by both checks exactly as an alias is.
    """
    line = annual_line(facts, concept)
    if not line.by_period:
        return None, None
    served = line.by_period[max(line.by_period)]
    stale = (stale_against(served, concept_frontier(facts, concept, line.substitute))
             or behind_filer(served, fiscal_year or filer_fiscal_year(facts)))
    return (None, stale) if stale else (served, None)


class StalePair(NamedTuple):
    """Two annual legs a combined figure cannot read AS CURRENT for one fiscal year.

    ``period_end`` is the newest year both legs carry, or ``None`` when no year carries both.
    ``behind`` is that year judged against the filer's newest fiscal year, ``legs`` each leg at
    that year judged against its own concept; either makes the year not current."""

    first: str
    second: str
    period_end: date | None
    behind: StaleAnnual | None
    legs: tuple[StaleAnnual, ...]
    first_end: date  # each leg's own latest annual, named when the two share no year
    second_end: date

    @property
    def note(self) -> str:
        if self.period_end is None:
            return (f"no fiscal year carries both {self.first} and {self.second} (their latest "
                    f"annuals end {self.first_end.isoformat()} and "
                    f"{self.second_end.isoformat()})")
        head = (f"newest year both {self.first} and {self.second} carry ends "
                f"{self.period_end.isoformat()}")
        if self.behind:
            head += (f", {self.behind.lag_days}d behind the filer's newest fiscal year "
                     f"({self.behind.newer_tag} to {self.behind.newer_end.isoformat()}) — more "
                     f"than one fiscal year behind")
        return "; ".join([head, *(s.note for s in self.legs)])


def current_pair(
    facts: dict[str, Any], first: str, second: str, fiscal_year: ConceptPoint | None = None
) -> tuple[tuple[ConceptPoint, ConceptPoint] | None, StalePair | None]:
    """Both legs of a combined annual figure (FCF = operating cash flow − capex, EBITDA =
    operating income + D&A) for ONE fiscal year: ``((first, second), None)``; ``(None, why)``
    when that year is not current or there is none; ``(None, None)`` when a leg has no annual.

    THE NEWEST YEAR BOTH LEGS CARRY, same start and same end — never each leg's own latest. Two
    latest annuals added together are a number that never existed when their years differ:
    Johnson & Johnson's EBITDA paired FY2014 operating income with FY2025 D&A, and SL Green's FCF
    took FY2019 capex off FY2025 operating cash flow. Measured 2026-10-27 on 2,161 cached
    companyfacts: 132 filers' screen FCF sign and 150 filers' EBITDA paired two fiscal years.

    That year is then judged as :func:`current_annual` judges one annual, on both counts: each
    leg against its own concept's newest period, and the year against the filer's newest fiscal
    year. So a pair that last met years ago is never served as this year's figure: when one leg
    has moved on, the other leg's year is not the current one. The CIQ-empty FCF fallback has
    paired this way since #817; this is that pairing, shared. Each leg is its concept's
    :func:`annual_line`, so a re-tagged leg pairs on the year the filer re-tagged it in.
    """
    line_first, line_second = annual_line(facts, first), annual_line(facts, second)
    by_first, by_second = line_first.by_period, line_second.by_period
    if not by_first or not by_second:
        return None, None
    shared = [e for e in by_first.keys() & by_second.keys()
              if by_first[e].period_start == by_second[e].period_start]
    if not shared:
        return None, StalePair(first=first, second=second, period_end=None, behind=None,
                               legs=(), first_end=max(by_first), second_end=max(by_second))
    end = max(shared)
    a, b = by_first[end], by_second[end]
    behind = behind_filer(a, fiscal_year or filer_fiscal_year(facts))
    legs = tuple(s for s in (
        stale_against(a, concept_frontier(facts, first, line_first.substitute)),
        stale_against(b, concept_frontier(facts, second, line_second.substitute))) if s)
    if behind or legs:
        return None, StalePair(first=first, second=second, period_end=end, behind=behind,
                               legs=legs, first_end=max(by_first), second_end=max(by_second))
    return (a, b), None


# --- the filer's fiscal calendar: which fiscal year a period IS ----------------------------------


def _own_periods(facts: dict[str, Any], forms: tuple[str, ...] = ("10-Q", "10-K"),
                 ) -> list[tuple[str, int, date, date]]:
    """(fiscal period, fiscal year, end, filed) for every filing of ``forms``: the period it states
    as its OWN — the latest end it carries — under the fiscal year and period its XBRL names.
    Read across every unit (``EVERY``): a period's dates carry no currency, and a fiscal year
    stated only in a filer's old currency is still that year."""
    by_acc: dict[str, tuple[str, int, date, date]] = {}
    for tag in (*CONCEPT_ALIASES["revenue"], *CONCEPT_ALIASES["net_income"],
                *CONCEPT_ALIASES["eps_diluted"]):
        for p in points_for_tag(facts, tag, currency=EVERY):
            form = (p.form or "").upper()
            if (p.period_start is None or not p.accession or p.fy is None or not p.fp
                    or not form.startswith(forms)):
                continue
            seen = by_acc.get(p.accession)
            if seen is None or p.period_end > seen[2]:
                by_acc[p.accession] = (p.fp.upper(), int(p.fy), p.period_end, p.filed)
    return list(by_acc.values())


def fiscal_calendar(facts: dict[str, Any]) -> dict[tuple[str, int], date]:
    """(fiscal period, fiscal year) → the period's end, as each 10-Q/10-K states its OWN period: the
    latest period end it carries, under the fiscal year and period its XBRL names. A fourth quarter
    ends with its fiscal year, so ``("FY", y)`` serves both."""
    cal: dict[tuple[str, int], tuple[date, date]] = {}
    for fp, fy, end, filed in _own_periods(facts):
        if fp in ("Q1", "Q2", "Q3", "FY") and ((fp, fy) not in cal or filed < cal[(fp, fy)][1]):
            cal[(fp, fy)] = (end, filed)            # the ORIGINAL filing names the period
    return {k: v[0] for k, v in cal.items()}


#: The forms a filer states its fiscal year in: the 10-K (and 10-KT), a foreign filer's 20-F / 40-F.
#: The one list: the currency reader, the fiscal calendar and every annual-report reader (FPI1a).
ANNUAL_REPORT_FORMS = ("10-K", "20-F", "40-F")
#: A period is the fiscal year whose own annual report ends within this many days of it. A
#: comparative restates the SAME period, so its end is the report's to the day; the slack is a
#: 52/53-week calendar's, never a quarter's.
FISCAL_YEAR_END_DAYS = 7


def fiscal_year_ends(facts: dict[str, Any]) -> dict[int, tuple[date, ...]]:
    """Each fiscal year → every end an annual report states as THAT year's own period: one end,
    repeated by an amendment — or two, when the filer's stamp names two different years
    (:func:`fiscal_year_of` refuses those). The filings :func:`fiscal_calendar` reads, every end
    kept rather than the original filing's alone, and a foreign filer's 20-F / 40-F beside the
    10-K: TAT Technologies' and Gilat's years are stated nowhere else."""
    ends: dict[int, set[date]] = {}
    for fp, fy, end, _filed in _own_periods(facts, ANNUAL_REPORT_FORMS):
        if fp == "FY":
            ends.setdefault(fy, set()).add(end)
    return {fy: tuple(sorted(e)) for fy, e in ends.items()}


def fiscal_year_of(year_ends: dict[int, tuple[date, ...]], point: ConceptPoint) -> int | None:
    """The fiscal year ``point``'s OWN period is (:func:`fiscal_year_ends`): the year whose annual
    report states a period ending within :data:`FISCAL_YEAR_END_DAYS` of it. ``None`` — never a
    guess — when the point is no fiscal year, no annual report the facts hold states its period,
    two years claim it, its year's stamp also names another period, or the stamp is no year the
    period could be called (more than one from the calendar year it ends in).

    NEVER ``point.fy``. companyfacts stamps each fact with the fiscal year of the FILING that
    carried it, so a comparative reads as a later year: Climb Global's FCF for the year to
    2019-12-31 is served from its FY2020 10-K and was labelled "[FY2020]".

    A STAMP THAT NAMES TWO PERIODS NAMES NEITHER. Kroger's 10-Ks for the years to 2025-02-01 and
    2026-01-31 are both stamped 2025, and Wolverine's to 2024-12-28 and 2026-01-03 both 2024
    (116 of 2,161 cached filers carry 123 such stamps, measured 2026-10-28). The calendar keeps the
    earlier filing's period; a label cannot tell which of the two the stamp meant, so both are
    named by their end date instead. Read as the filing's year, those stamps had printed BJ's
    Restaurants' year to 2025-12-30 as "FY2023".

    A STAMP IS A YEAR OR NOTHING. One cached filer (CIK 1653558) stamps its 10-Ks 43465 and 43830 —
    the spreadsheet serials of 2018-12-31 and 2019-12-31 — and the CIQ-empty fallback printed
    "FY43465". A fiscal year ends in the calendar year it is named for or the next (Kroger's
    fiscal 2025 ends 2026-01-31), so a stamp further from the period's end year is refused."""
    if not point.is_annual:
        return None
    years = {fy for fy, ends in year_ends.items()
             if any(abs((e - point.period_end).days) <= FISCAL_YEAR_END_DAYS for e in ends)}
    if len(years) != 1:
        return None
    fy = years.pop()
    ends = year_ends[fy]
    if (ends[-1] - ends[0]).days > FISCAL_YEAR_END_DAYS or abs(fy - point.period_end.year) > 1:
        return None
    return fy


def _amount(value: float, unit: str) -> str:
    """A figure as provenance prints it: a per-share one to the cent, any other whole."""
    return f"{value:,.2f}" if "/" in unit else f"{value:,.0f}"


def superseded(facts: dict[str, Any], p: ConceptPoint) -> ConceptPoint | None:
    """The FIRST filing of ``p``'s own period, tag and unit, when it stated another value — the
    figure a later filing restated (audit E1-D5). None when ``p`` was never stated differently.

    The served point is the latest filed, which on a forward page is the value known at build; the
    earlier one is what a reader of that first filing saw. WOR's FY2022 revenue is served as 1,309
    (filed 2024-07-30, after the steel spin-off) and was first filed as 5,242 (2022-08-01)."""
    earlier = [q for q in points_for_tag(facts, p.tag, currency=EVERY)
               if q.unit == p.unit and q.period_start == p.period_start
               and q.period_end == p.period_end and q.filed < p.filed]
    # the period's FIRST filing, whatever came between: a figure restated and restated back is
    # the figure first filed, not a restatement
    first = min(earlier, key=lambda q: q.filed) if earlier else None
    return first if first is not None and not _same_figure(first.value, p.value) else None


def _same_figure(a: float, b: float) -> bool:
    """Two filings of one figure state the same number when they agree at the COARSER of their
    two precisions (review of #875): −69,100,000 re-reports −69,075,000 rounded to $100,000, it
    does not restate it — 3 of 13 current legs in the cache differed only so. A restatement that
    small, stated at that precision, is not told apart; one past it is."""
    exp = max(Decimal(repr(x)).normalize().as_tuple().exponent for x in (a, b))
    step = Decimal(1).scaleb(int(exp))
    return (Decimal(repr(a)).quantize(step, ROUND_HALF_EVEN)
            == Decimal(repr(b)).quantize(step, ROUND_HALF_EVEN))


def filed_at(p: ConceptPoint, facts: dict[str, Any] | None = None) -> str:
    """Where ``p`` was filed, as a reader can go and check it: its tag, its period, the form and
    accession that carried it and the day — and, given ``facts``, the figure it restates (audit
    E1-D5: the EDGAR fallback served its figures with no accession at all)."""
    when = (f"at {p.period_end}" if p.period_start is None
            else f"{p.period_start}..{p.period_end}")
    out = (f"{p.tag} {when} ({p.form or 'form unstated'} "
           f"{p.accession or 'accession unstated'}, filed {p.filed})")
    if facts is not None and " + " in p.tag:
        # a line the filer splits into two tags has no one tag to look a restatement up under
        # (`annual_line`): say so, never skip it silently (review of #875)
        out += ", restatement not checked: a sum of tags"
    elif facts is not None and (old := superseded(facts, p)) is not None:
        out += (f", restating {_amount(old.value, old.unit)} first filed {old.filed} "
                f"({old.accession or 'accession unstated'})")
    return out


#: Aliased as D&A, but NOT a D&A figure: it nets accretion income (of discounts on investments)
#: against depreciation and amortization. Refused as D&A at the EBITDA readers whatever its sign
#: (review of #875: refusing it only when negative selected on SIGN — 28 of the 35 current EBITDA
#: pairs serving it were positive and read unflagged, 7 negative and refused).
NOT_D_AND_A = frozenset({"DepreciationAmortizationAndAccretionNet"})


def leg_refusal(what: str, p: ConceptPoint) -> str | None:
    """Why a combined figure refuses its ``what`` leg ``p``, or None: a D&A leg under a tag that is
    not a D&A figure (:data:`NOT_D_AND_A`), whatever its sign, or a leg filed negative
    (:func:`negative_leg`)."""
    if what == "D&A" and p.tag in NOT_D_AND_A:
        return (f"D&A served under {p.tag}, which nets accretion income against depreciation and "
                f"amortization — not a D&A figure, so never read as one "
                f"({p.form or 'form unstated'} {p.accession or 'accession unstated'}); refused")
    return negative_leg(what, p)


def negative_leg(what: str, p: ConceptPoint) -> str | None:
    """Why a combined figure refuses ``p``, or None: a capex or D&A leg filed NEGATIVE (audit
    E1-D12). A payment and an expense are filed positive, so a negative one is not the leg the
    figure needs — taken as filed it raised FCF (WOR's capex negated: 170.2 → 282.0) or lowered
    EBITDA (8 of 1,241 current EBITDA pairs in the cache, 2026-10-30, 7 of them under
    `DepreciationAmortizationAndAccretionNet`, which nets accretion income). Refused, naming it —
    never sign-flipped, which would be a guess at what the filer meant."""
    if p.value >= 0:
        return None
    return (f"{what} filed negative: {p.tag} {_amount(p.value, p.unit)} for "
            f"{p.period_start}..{p.period_end} ({p.form or 'form unstated'} "
            f"{p.accession or 'accession unstated'}) — refused, never sign-flipped")


def latest_instant(points: list[ConceptPoint]) -> ConceptPoint | None:
    """Latest balance-sheet value (most recent period_end, then most recent filing), or None.

    NONE WHEN NO POINT IS AN INSTANT (audit E1-D16). The fallback was ``… or points``, so a list of
    flows answered with a flow: WOR's revenue returned its year to 2026-05-31 as if it were a
    balance. No caller feeds it flows today (0 of 2,253 cached filers through net debt and the
    share count, 2026-10-30), which is why the widened population had to go before one did."""
    instants = [p for p in points if p.is_instant]
    if not instants:
        return None
    return max(instants, key=lambda p: (p.period_end, p.filed))


# --- shares-outstanding trajectory (ONE implementation, two consumers) --------------------------
# The trailing window over which a share-count change is read. Lives here rather than in either
# consumer because BOTH read it: the rank-side dilution-spiral demote (vinci.rank.structural) and
# the screen-side evidence strip. Two computations of one quantity is the twin-drift class this
# repo keeps finding — they would agree today and diverge on the first edit to one of them.
SHARES_WINDOW_DAYS = 730  # ~2y, mirroring the dossier's dilution trajectory


class ShareCountChange(NamedTuple):
    """A share-count change over the trailing window, carrying its own endpoints.

    The endpoints travel with the number because a fraction alone cannot be checked: "+42%" is
    unverifiable, "58,598,133 (2024-05-13) → 83,209,441 (2026-05-12)" is a claim a human can go
    read off EDGAR. Every source string built from this uses them.
    """

    change: float  # fraction: +0.42 == shares up 42%; negative == buyback
    from_date: date
    from_value: float
    to_date: date
    to_value: float


def share_window_start(shares: Sequence[tuple[date, float]], *,
                       window_days: int = SHARES_WINDOW_DAYS) -> date | None:
    """Where the trailing share window opens: ``window_days`` before the LAST point, or None for an
    empty series — the one definition :func:`share_count_change` and its callers measure from."""
    return max(d for d, _ in shares) - timedelta(days=window_days) if shares else None


def refused_endpoint(shares: Sequence[tuple[date, float]], refused: Sequence[date], *,
                     window_days: int = SHARES_WINDOW_DAYS) -> date | None:
    """The date of a refused count that would ITSELF be an endpoint of the trailing window, or
    None. Only an endpoint can void a change — :func:`share_count_change` reads the first and last
    counts and nothing between (review of #875: NovaGold's refused 2025-06-30 count sits between
    two good ones, followed by 406,926,988 and 406,994,531, and its +31.1% stands)."""
    kept = {d for d, _ in shares}
    dates = sorted(kept | set(refused))
    if not dates:
        return None
    window = [d for d in dates if d >= dates[-1] - timedelta(days=window_days)]
    hit = [d for d in refused if d in (window[0], window[-1]) and d not in kept]
    return max(hit) if hit else None


def share_count_change(
    shares: list[tuple[date, float]], *, window_days: int = SHARES_WINDOW_DAYS,
    refused: Sequence[date] = (),
) -> ShareCountChange | None:
    """Fractional change in shares outstanding across the trailing window, or None if unreadable.

    None — never 0.0 — when the series is too short or a value is non-positive: a fabricated "no
    change" would read as a confirmed flat share count, which is the opposite of "we could not
    tell". The window is anchored on the LAST point rather than on today, so a name whose XBRL
    series ends early is measured over the span it actually has.

    None, too, when a count in ``refused`` (one its own filing contradicts,
    :mod:`vinci.edgar.cover_count`) would itself be an endpoint (:func:`refused_endpoint`): a
    change FROM or TO an UNKNOWN count is UNKNOWN, never measured from the next one along (Phase 2
    C2, audit X1(a)). One between the endpoints is not read either way.
    """
    if len(shares) < 2:
        return None
    series = sorted(shares)
    if refused_endpoint(series, refused, window_days=window_days) is not None:
        return None
    anchor = share_window_start(series, window_days=window_days)
    assert anchor is not None
    window = [s for s in series if s[0] >= anchor]
    # TWO DISTINCT DATES INSIDE THE WINDOW, or nothing (review, #440). When every other point is
    # older than the window, `window` holds only the latest tuple — and unpacking [0] and [-1] then
    # used ONE datum as both endpoints and returned 0.0, publishing a confident "no change" from a
    # single observation. Measured live: 1 of 273 rows (RXRX, 2026-07-31 → 2026-07-31).
    #
    # AND NO FALLING BACK to the full history: the caller states a horizon, so silently measuring a
    # six-year span and calling it two years swaps one wrong number for another. This also removes a
    # dead `or series` branch — `series[-1]` always satisfies `>= anchor`, so the window could never
    # be empty and the fallback implied a safety net that never once fired.
    if len({d for d, _ in window}) < 2:
        return None
    (d0, v0), (d1, v1) = window[0], window[-1]
    if v0 <= 0 or v1 <= 0:
        return None
    return ShareCountChange(change=v1 / v0 - 1.0, from_date=d0, from_value=v0,
                            to_date=d1, to_value=v1)
