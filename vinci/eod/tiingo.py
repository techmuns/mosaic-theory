"""Tiingo EOD adapter — the **deep-history backfill alternative** (per-symbol).

Polygon Grouped Daily (whole-market) is the primary breadth feed; Tiingo is kept for per-symbol
history deeper than Polygon's free 2-year window, "if ever needed". It is wired and its response
parsing is unit-tested; the network path runs only where a ``TIINGO_API_KEY`` is set. Since
2026-10-24 the data-quality scorecard reads it live (`vinci.quality.sources.prices`: Polygon's close
against Tiingo's, per session, for the names with a committed page — and, since 2026-10-27, each
step or zero-volume bar its internal checks flag).

Auth uses the ``Authorization: Token <key>`` header (not a ``?token=`` query param), keeping the key
out of request URLs, the on-disk cache, and logs.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from typing import Any, cast

from vinci.config import Config, get_config, require_env, sec_user_agent
from vinci.netcache import CachedHttp, HttpError
from vinci.schemas.market import PriceBar

_PRICES = "https://api.tiingo.com/tiingo/daily/{symbol}/prices"
_ONE_DAY = 86_400.0


class TiingoRefusedError(HttpError):
    """Tiingo answered 200 with a refusal instead of rows. Measured 2026-10-27 from 20:01 IST:
    ``{"detail": "You have run over your 500 symbol look up for this month. ..."}`` — the plan
    caps the distinct symbols a key may ask for in a calendar month, shared by every user of it.
    ``monthly_cap`` says whether it was that cap, which refuses every NEW symbol until the month
    turns; any other refusal is about the one request."""

    def __init__(self, message: str, *, monthly_cap: bool) -> None:
        super().__init__(message)
        self.monthly_cap = monthly_cap


#: the refusal's wording for the monthly cap, as served
MONTHLY_SYMBOL_LIMIT = "symbol look up"

#: The plan's monthly cap: distinct symbols ONE KEY may look up in a calendar month, shared by
#: every user of it — the refusal's own figure ("500 symbol look up for this month", 2026-10-27).
#: A symbol looked up once in the month is served for the rest of it (VRRM, 2026-10-28 00:45 IST,
#: after the cap); only a symbol NEW to the month is refused.
MONTHLY_SYMBOL_CAP = 500

#: the symbol in a cached request's URL
_SYMBOL_IN_URL = re.compile(r"/tiingo/daily/([^/?]+)/prices")


def tiingo_symbol(symbol: str) -> str:
    """A symbol as Tiingo is asked for it, and as its cap counts it: lower case, a share class
    hyphenated (BRK.B → brk-b), the spelling every caller here sends."""
    return symbol.replace(".", "-").lower()


def month_of(at: datetime) -> str:
    """``YYYY-MM`` of ``at`` in UTC — the calendar month a lookup is counted in. Tiingo does not
    say which clock its month turns on; UTC is assumed, not measured."""
    return at.astimezone(UTC).strftime("%Y-%m")


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

    def daily_rows(self, symbol: str, *, start: date, end: date,
                   ttl_seconds: float | None = _ONE_DAY) -> list[dict[str, Any]]:
        """Tiingo's daily rows as served: the UNADJUSTED open/high/low/close/volume beside the
        ``adj*`` fields, ``divCash`` and ``splitFactor``. The ``adj*`` fields remove dividends as
        well as splits, while Polygon's ``adjusted=true`` restates splits only — so a comparison
        with the store needs the unadjusted close and the split factors, which the parsed bars
        drop. Cached a day unless the caller passes ``ttl_seconds`` (None keeps the response for
        good — only for a window the caller knows has closed).

        A body that is not a list of rows is a REFUSAL served as 200 (`TiingoRefusedError`): it is
        dropped from the cache and raised, never returned as data. Kept, it would be replayed —
        for good under ``ttl_seconds=None`` (45 such bodies were cached that way on 2026-10-27)."""
        url = _PRICES.format(symbol=symbol.lower())
        params = {"startDate": start.isoformat(), "endDate": end.isoformat(), "format": "json"}
        data = self._http.get_json(url, ttl_seconds=ttl_seconds, params=params)
        if not isinstance(data, list):
            # netcache caches every 200 and exposes no eviction; its own path rule is used here
            self._http._cache_path(self._http._with_params(url, params)).unlink(missing_ok=True)
            detail = str(data.get("detail") if isinstance(data, dict) else type(data).__name__)
            cap = MONTHLY_SYMBOL_LIMIT in detail
            raise TiingoRefusedError("over the plan's monthly symbol limit" if cap
                                     else f"refused, no rows: {detail[:60]}", monthly_cap=cap)
        return cast(list[dict[str, Any]], data)

    def cached_rows(self, symbol: str, *, start: date, end: date,
                    ttl_seconds: float | None = _ONE_DAY) -> list[dict[str, Any]] | None:
        """`daily_rows` from the cache alone — None when no fresh copy is held. Never a request:
        read after a plan limit has stopped the asking, so a kept answer is still used."""
        params = {"startDate": start.isoformat(), "endDate": end.isoformat(), "format": "json"}
        text = self._http._read_cache(
            self._http._with_params(_PRICES.format(symbol=symbol.lower()), params), ttl_seconds)
        if text is None:
            return None
        data = json.loads(text)
        return cast(list[dict[str, Any]], data) if isinstance(data, list) else None

    def symbols_asked(self, month: str) -> set[str]:
        """The distinct symbols THIS CLIENT'S CACHE shows looked up in ``month`` (``YYYY-MM``,
        `month_of`): every kept response fetched that month, read off its URL. A refusal is never
        kept (`daily_rows`), so it never counts.

        A FLOOR on the key's use, never the key's count: CI, theme intelligence's own cache and
        other checkouts' caches share the key and are not read here. Measured 2026-10-28: the
        caches on the operator's machine held 112 distinct symbols looked up in October, against
        the 500 the key had met by 2026-10-27 20:01 IST."""
        out: set[str] = set()
        for path in self._http._cache_dir.glob("*.json"):
            try:
                entry = json.loads(path.read_text())
                at = datetime.fromtimestamp(float(entry["fetched_at"]), UTC)
                m = _SYMBOL_IN_URL.search(str(entry["url"]))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue   # an unreadable entry is no lookup this cache can name
            if m is not None and month_of(at) == month:
                out.add(m.group(1))
        return out

    def price_history(
        self, symbol: str, internal_id: str, *, start: date, end: date
    ) -> list[PriceBar]:
        return parse_tiingo_prices(self.daily_rows(symbol, start=start, end=end), internal_id)
