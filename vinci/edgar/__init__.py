"""EDGAR client — US fundamentals (XBRL), 8-K event detection, recent filings."""

from vinci.edgar.client import (
    EdgarClient,
    Filing,
    FtsHit,
    FundamentalSnapshot,
    all_unknown_snapshot,
    compute_fundamental_snapshot,
    parse_fts_hit,
    parse_fts_response,
)
from vinci.edgar.concepts import (
    CONCEPT_ALIASES,
    ConceptPoint,
    extract_points,
    latest_annual,
    latest_instant,
)

__all__ = [
    "CONCEPT_ALIASES",
    "ConceptPoint",
    "EdgarClient",
    "Filing",
    "FtsHit",
    "FundamentalSnapshot",
    "all_unknown_snapshot",
    "compute_fundamental_snapshot",
    "extract_points",
    "latest_annual",
    "latest_instant",
    "parse_fts_hit",
    "parse_fts_response",
]
