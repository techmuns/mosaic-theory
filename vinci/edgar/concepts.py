"""XBRL concept aliases + point extraction from SEC ``companyfacts``.

XBRL tagging is inconsistent across filers — e.g. revenue may be tagged ``Revenues`` or
``RevenueFromContractWithCustomerExcludingAssessedTax``. Each logical concept therefore maps to a
**priority-ordered list of us-gaap tags**; we use the first tag a filer actually reports. Values are
extracted **as-reported with the filing date** (point-in-time), and the latest figure for a period
takes the most recent ``filed`` (handling restatements without mutating earlier rows).
"""

from __future__ import annotations

from datetime import date
from typing import Any

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


def extract_points(facts: dict[str, Any], concept: str) -> list[ConceptPoint]:
    """Extract all reported points for a logical concept, trying alias tags in priority order."""
    for tag in CONCEPT_ALIASES[concept]:
        points = points_for_tag(facts, tag, concept=concept)
        if points:
            return points  # first alias with data wins
    return []


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


def latest_instant(points: list[ConceptPoint]) -> ConceptPoint | None:
    """Latest balance-sheet value (most recent period_end, then most recent filing)."""
    instants = [p for p in points if p.is_instant] or points
    if not instants:
        return None
    return max(instants, key=lambda p: (p.period_end, p.filed))
