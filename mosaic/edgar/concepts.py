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
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
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
        """Heuristic: a full-year flow (≈ 12-month period or FY)."""
        if self.period_start is None:
            return False
        return self.fp == "FY" or (self.period_end - self.period_start).days >= 300


def _parse_date(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


def extract_points(facts: dict[str, Any], concept: str) -> list[ConceptPoint]:
    """Extract all reported points for a logical concept, trying alias tags in priority order."""
    nsmap = facts.get("facts", {})
    for tag in CONCEPT_ALIASES[concept]:
        node = None
        for ns in _NAMESPACES:
            node = nsmap.get(ns, {}).get(tag)
            if node:
                break
        if not node:
            continue
        points: list[ConceptPoint] = []
        for unit, rows in node.get("units", {}).items():
            for r in rows:
                end = _parse_date(r.get("end"))
                filed = _parse_date(r.get("filed"))
                if end is None or filed is None or r.get("val") is None:
                    continue
                points.append(
                    ConceptPoint(
                        concept=concept,
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
        if points:
            return points  # first alias with data wins
    return []


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
