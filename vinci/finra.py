"""FINRA consolidated equity short-interest — a free, dated positioning input.

FINRA publishes aggregate equity short interest twice-monthly (settlement-dated) through its public
query API (``api.finra.org``, delayed data, no entitlement / no key). We read the latest settlement
points for a symbol and surface shares-short + FINRA's own change% — **dated** facts (no floor
semantics) that INFORM the human, never a conclusion.

The column layout is PINNED (``_REQUIRED_COLUMNS``): if FINRA renames or drops a column we read, the
parse raises :class:`FinraLayoutError` rather than guessing — a silent layout change can't corrupt
the number (the spec's STOP-AND-REPORT rule). Filtering is POST-only: the endpoint ignores GET query
params, so a plain GET returns the whole (all-symbol) file — we filter with ``compareFilters``.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel

from vinci.config import Config, get_config, sec_user_agent
from vinci.netcache import CachedHttp

_ENDPOINT = "https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest"
# The columns the parse BINDS to — pinned so a FINRA layout change fails LOUD, never silently
# mis-maps. Presence is checked (a missing key ⇒ layout deviation ⇒ raise); a null VALUE is data,
# not a layout change, and is tolerated as None.
_REQUIRED_COLUMNS = (
    "settlementDate",
    "currentShortPositionQuantity",
    "previousShortPositionQuantity",
    "changePercent",
    "daysToCoverQuantity",
)
# Short interest settles twice a month; a 3-day cache keeps a within-run reread instant without
# serving a stale settlement across the twice-monthly boundary.
_TTL_SECONDS = 3 * 24 * 3600


class FinraLayoutError(RuntimeError):
    """A FINRA response whose layout deviates from the pinned schema — fail loud, never guess."""


class ShortInterestPoint(BaseModel, frozen=True):
    """One settlement point — FINRA's own aggregates (no recompute of the feed's numbers)."""

    settlement_date: str  # ISO, e.g. "2026-06-15"
    shares_short: int
    prev_shares_short: int | None
    change_percent: float | None
    # FINRA's OWN days-to-cover (uses FINRA's ADV, not the screen ADV) — kept for a transparency
    # note; the dossier recomputes DTC against the screen data-record ADV per the spec.
    finra_days_to_cover: float | None


def build_finra_http(config: Config | None = None) -> CachedHttp:
    """Cached, polite client for ``api.finra.org``. Reuses the declared research-contact UA (FINRA
    imposes no separate UA requirement); JSON content headers so the query API returns JSON rows."""
    cfg = config or get_config()
    cfg.ensure_dirs()
    return CachedHttp(
        cache_dir=cfg.cache_dir,
        user_agent=sec_user_agent(),
        min_interval_sec=1.0 / cfg.pacing.finra_requests_per_sec,
        max_retries=cfg.pacing.max_retries,
        timeout_sec=cfg.pacing.http_timeout_sec,
        namespace="finra",
        extra_headers={"Content-Type": "application/json", "Accept": "application/json"},
    )


def _num(row: dict[str, Any], key: str) -> float | None:
    v = row.get(key)
    return float(v) if v is not None else None


def parse_short_interest(rows: list[dict[str, Any]]) -> list[ShortInterestPoint]:
    """Parse FINRA rows into settlement points, latest first. Presence of every pinned column is
    required (missing ⇒ :class:`FinraLayoutError`); null values are tolerated as None."""
    points: list[ShortInterestPoint] = []
    for row in rows:
        missing = [c for c in _REQUIRED_COLUMNS if c not in row]
        if missing:
            raise FinraLayoutError(
                f"FINRA short-interest row missing pinned column(s) {missing}; layout changed — "
                f"refusing to guess (row keys: {sorted(row)})"
            )
        cur = _num(row, "currentShortPositionQuantity")
        if cur is None:
            continue  # a row with no current short position carries no fact — skip, never fake 0
        prev = _num(row, "previousShortPositionQuantity")
        points.append(
            ShortInterestPoint(
                settlement_date=str(row["settlementDate"]),
                shares_short=int(cur),
                prev_shares_short=int(prev) if prev is not None else None,
                change_percent=_num(row, "changePercent"),
                finra_days_to_cover=_num(row, "daysToCoverQuantity"),
            )
        )
    return sorted(points, key=lambda p: p.settlement_date, reverse=True)


def short_interest_points(
    http: CachedHttp, symbol: str, *, start: date, end: date, limit: int = 8
) -> list[ShortInterestPoint]:
    """The symbol's settlement points in ``[start, end]``, latest first (empty if none on file).

    Filtered server-side by ``symbolCode`` + ``settlementDate`` range (the endpoint ignores GET
    query params — filtering is POST-only). Layout is pinned in :func:`parse_short_interest`."""
    body: dict[str, Any] = {
        "limit": limit,
        "compareFilters": [
            {"compareType": "EQUAL", "fieldName": "symbolCode", "fieldValue": symbol.upper()}
        ],
        "dateRangeFilters": [
            {
                "fieldName": "settlementDate",
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
            }
        ],
    }
    raw = http.post_json(_ENDPOINT, json_body=body, ttl_seconds=_TTL_SECONDS)
    rows = raw if isinstance(raw, list) else raw.get("data", [])
    return parse_short_interest(rows)
