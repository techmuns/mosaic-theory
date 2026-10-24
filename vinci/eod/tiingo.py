"""Tiingo EOD adapter — the **deep-history backfill alternative** (per-symbol).

Polygon Grouped Daily (whole-market) is the primary breadth feed; Tiingo is kept for per-symbol
history deeper than Polygon's free 2-year window, "if ever needed". It is wired and its response
parsing is unit-tested; the network path runs only where a ``TIINGO_API_KEY`` is set. Since
2026-10-24 the data-quality scorecard reads it live (`vinci.quality.sources.prices`: Polygon's close
against Tiingo's, per session, for the names with a committed page).

Auth uses the ``Authorization: Token <key>`` header (not a ``?token=`` query param), keeping the key
out of request URLs, the on-disk cache, and logs.
"""

from __future__ import annotations

from datetime import date
from typing import Any, cast

from vinci.config import Config, get_config, require_env, sec_user_agent
from vinci.netcache import CachedHttp
from vinci.schemas.market import PriceBar

_PRICES = "https://api.tiingo.com/tiingo/daily/{symbol}/prices"
_ONE_DAY = 86_400.0


def parse_tiingo_prices(rows: list[dict[str, Any]], internal_id: str) -> list[PriceBar]:
    """Pure parser: Tiingo daily rows → split/dividend-adjusted PriceBars (unit-testable)."""
    out: list[PriceBar] = []
    for r in rows:
        d = str(r["date"])[:10]  # "2024-01-02T00:00:00.000Z" -> "2024-01-02"
        out.append(
            PriceBar(
                internal_id=internal_id,
                bar_date=date.fromisoformat(d),
                open=r["adjOpen"],
                high=r["adjHigh"],
                low=r["adjLow"],
                close=r["adjClose"],
                volume=r["adjVolume"],
                source="tiingo",
            )
        )
    return out


class TiingoEodClient:
    """Per-symbol EOD history from Tiingo (deep-history backfill alternative)."""

    def __init__(self, http: CachedHttp) -> None:
        self._http = http

    @classmethod
    def from_config(cls, config: Config | None = None) -> TiingoEodClient:
        cfg = config or get_config()
        cfg.ensure_dirs()
        http = CachedHttp(
            cache_dir=cfg.cache_dir,
            user_agent=sec_user_agent(),
            min_interval_sec=1.0,  # free tier is generous per-symbol; stay polite
            max_retries=cfg.pacing.max_retries,
            timeout_sec=cfg.pacing.http_timeout_sec,
            namespace="tiingo",
            extra_headers={"Authorization": f"Token {require_env('TIINGO_API_KEY')}"},
        )
        return cls(http)

    def daily_rows(self, symbol: str, *, start: date, end: date) -> list[dict[str, Any]]:
        """Tiingo's daily rows as served: the UNADJUSTED open/high/low/close/volume beside the
        ``adj*`` fields, ``divCash`` and ``splitFactor``. The ``adj*`` fields remove dividends as
        well as splits, while Polygon's ``adjusted=true`` restates splits only — so a comparison
        with the store needs the unadjusted close and the split factors, which the parsed bars
        drop."""
        url = _PRICES.format(symbol=symbol.lower())
        data = self._http.get_json(
            url,
            ttl_seconds=_ONE_DAY,
            params={"startDate": start.isoformat(), "endDate": end.isoformat(), "format": "json"},
        )
        return cast(list[dict[str, Any]], data)

    def price_history(
        self, symbol: str, internal_id: str, *, start: date, end: date
    ) -> list[PriceBar]:
        return parse_tiingo_prices(self.daily_rows(symbol, start=start, end=end), internal_id)
