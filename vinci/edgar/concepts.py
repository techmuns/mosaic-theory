"""XBRL concept aliases + point extraction from SEC ``companyfacts``.

XBRL tagging is inconsistent across filers — e.g. revenue may be tagged ``Revenues`` or
``RevenueFromContractWithCustomerExcludingAssessedTax``. Each logical concept therefore maps to a
**priority-ordered list of us-gaap tags**; we use the first tag a filer actually reports. Values are
extracted **as-reported with the filing date** (point-in-time), and the latest figure for a period
takes the most recent ``filed`` (handling restatements without mutating earlier rows).
"""

from __future__ import annotations

from datetime import date, timedelta
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


def extract_points(facts: dict[str, Any], concept: str) -> list[ConceptPoint]:
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
    """
    return _resolve(facts, concept, filer_frontier(facts))


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
    facts: dict[str, Any], concept: str, frontier: date | None
) -> list[ConceptPoint]:
    """The alias walk of :func:`extract_points`, taking an already-computed frontier.

    Split out so ``stale_served`` scans the (large) companyfacts blob for the frontier ONCE rather
    than three times — its own call, plus one inside the ``extract_points`` it delegates to.
    """
    present = [(tag, pts) for tag in CONCEPT_ALIASES[concept]
               if (pts := points_for_tag(facts, tag, concept=concept))]
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


def points_for_tag(facts: dict[str, Any], tag: str, *, concept: str = "") -> list[ConceptPoint]:
    """All reported points under exactly ``tag`` (the first namespace that carries it, in priority
    order). Takes the tag EXPLICITLY — no ``CONCEPT_ALIASES`` lookup, so callers that need a single
    known tag never mutate the shared alias map (which extractors read from parallel assembly
    threads). ``concept`` only labels the returned points; defaults to the tag itself."""
    nsmap = facts.get("facts", {})
    node = None
    for ns in _NAMESPACES:
        node = nsmap.get(ns, {}).get(tag)
        if node:
            break
    if not node:
        return []
    points: list[ConceptPoint] = []
    for unit, rows in node.get("units", {}).items():
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
    newer_tag: str  # the alias carrying the concept's newest period
    newer_end: date  # that period's end
    lag_days: int

    @property
    def note(self) -> str:
        return (f"stale annual {self.concept}: {self.tag} for the year to "
                f"{self.period_end.isoformat()}, {self.lag_days}d behind {self.newer_tag} to "
                f"{self.newer_end.isoformat()} — not the current year")


def concept_frontier(facts: dict[str, Any], concept: str) -> ConceptPoint | None:
    """The point with the newest period end ANY alias of ``concept`` carries, of any duration.

    Every alias, not the one :func:`extract_points` serves: the served alias is the one this is
    measured against. A tie goes to the alias first in priority order.

    A point whose period ends AFTER the day it was filed is skipped: it is a forward-dated
    context, not a period the filer has reported. Measured 2026-10-27 on the 2,161 cached
    companyfacts: 61 such points in 18 filers across the eight flow concepts' aliases."""
    newest: ConceptPoint | None = None
    for tag in CONCEPT_ALIASES[concept]:
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


def current_annual(
    facts: dict[str, Any], concept: str
) -> tuple[ConceptPoint | None, StaleAnnual | None]:
    """The latest annual an annual reader may serve AS CURRENT: ``(point, None)``; ``(None, why)``
    when it is stale; ``(None, None)`` when the concept has no annual at all.

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

    A concept that has stopped on EVERY alias is not caught: its newest period IS the served
    annual's. That family is recorded, not handled
    (``docs/records/2026-10-27-annual-readers-withhold-a-stale-annual.md``).
    """
    served = latest_annual(extract_points(facts, concept))
    if served is None:
        return None, None
    stale = stale_against(served, concept_frontier(facts, concept))
    return (None, stale) if stale else (served, None)


def latest_instant(points: list[ConceptPoint]) -> ConceptPoint | None:
    """Latest balance-sheet value (most recent period_end, then most recent filing)."""
    instants = [p for p in points if p.is_instant] or points
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


def share_count_change(
    shares: list[tuple[date, float]], *, window_days: int = SHARES_WINDOW_DAYS
) -> ShareCountChange | None:
    """Fractional change in shares outstanding across the trailing window, or None if unreadable.

    None — never 0.0 — when the series is too short or a value is non-positive: a fabricated "no
    change" would read as a confirmed flat share count, which is the opposite of "we could not
    tell". The window is anchored on the LAST point rather than on today, so a name whose XBRL
    series ends early is measured over the span it actually has.
    """
    if len(shares) < 2:
        return None
    series = sorted(shares)
    anchor = series[-1][0] - timedelta(days=window_days)
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
