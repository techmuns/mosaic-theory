"""EOD price ingestion — Polygon Grouped Daily (primary) + Tiingo (deep-history backfill),
plus the Screen-2 price features computed from stored bars."""

from vinci.eod.client import (
    EodClient,
    EodError,
    PolygonEodClient,
    RawBar,
    ingest_prices,
    parse_aggregates,
    parse_grouped_daily,
)
from vinci.eod.features import compute_price_features, relative_return
from vinci.eod.tiingo import TiingoEodClient, parse_tiingo_prices

__all__ = [
    "EodClient",
    "EodError",
    "PolygonEodClient",
    "RawBar",
    "TiingoEodClient",
    "compute_price_features",
    "ingest_prices",
    "parse_aggregates",
    "parse_grouped_daily",
    "parse_tiingo_prices",
    "relative_return",
]
