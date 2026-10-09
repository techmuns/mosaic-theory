"""Polygon access for the audit — security metadata, RAW daily bars, dividends, splits — and the
reader for the repo's already-cached grouped-daily responses.

TWO PRICE SOURCES, ONE BASIS. Measured 2026-10-09: this account's plan serves daily bars only from
2024-10-09 onward (an earlier range answers ``403 NOT_AUTHORIZED — Your plan doesn't include this
data timeframe``). The repo's own netcache, however, already holds a whole-market grouped-daily
response for every weekday 2021-07-01 → 2026-08-05, all of the pre-2026-03 days fetched on
2026-08-06 under the plan then in force. So:

- **live**: ``/v2/aggs/ticker/<T>/range/1/day`` with ``adjusted=false`` — RAW as-traded closes;
- **cache**: grouped-daily with ``adjusted=true`` — split-adjusted AS OF THE FETCH DATE.

The cache is converted back to the raw basis with Polygon's own split events (a split executed
after the bar and on/before the fetch date multiplies the cached price back up), so both sources
meet on one as-traded basis and the total-return series is built ONCE, from raw closes + cash
dividends + split ratios. The two sources overlap from 2024-10-09 to 2026-08-05, and that overlap
is reconciled bar-for-bar before either is trusted (``prices.reconcile_overlap``).

Reference endpoints (details / dividends / splits) are NOT window-limited (AXP's 2023 dividends
return on the same plan), so corporate actions come from Polygon for the whole window.

The key travels in the ``Authorization`` header (never a URL), so neither the cache nor this
module's provenance log can carry it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from vinci.config import load_local_env, require_env, sec_user_agent
from vinci.netcache import CachedHttp, HttpError

BASE = "https://api.polygon.io"
GROUPED_URL = BASE + "/v2/aggs/grouped/locale/us/market/stocks/{day}"
AGGS_URL = BASE + "/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}"
DETAILS_URL = BASE + "/v3/reference/tickers/{symbol}"
TICKERS_URL = BASE + "/v3/reference/tickers"
DIVIDENDS_URL = BASE + "/v3/reference/dividends"
SPLITS_URL = BASE + "/v3/reference/splits"

_STATUS = re.compile(r"Non-retryable (\d{3}) ")


class PolygonAuditError(RuntimeError):
    """A Polygon response the audit cannot use — raised, never papered over."""


@dataclass(frozen=True)
class DailyBar:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    source_ref: str


@dataclass(frozen=True)
class Dividend:
    ex_date: date
    cash: float
    currency: str
    dividend_type: str
    pay_date: str
    polygon_id: str


@dataclass(frozen=True)
class Split:
    execution_date: date
    split_from: float
    split_to: float
    polygon_id: str

    @property
    def ratio(self) -> float:
        """New shares per old share (a 10-for-1 split → 10.0; a 1-for-8 reverse → 0.125)."""
        return self.split_to / self.split_from


@dataclass(frozen=True)
class CallRecord:
    """Provenance for one Polygon response used by the run (never carries the key)."""

    url: str
    fetched_at_utc: str
    sha256: str
    status: str


def _status_of(exc: HttpError) -> int | None:
    m = _STATUS.search(str(exc))
    return int(m.group(1)) if m else None


def full_url(url: str, params: dict[str, Any] | None) -> str:
    """The exact URL string the netcache keys on (same construction as ``CachedHttp``)."""
    if not params:
        return url
    return str(httpx.Request("GET", url, params=params).url)


def cache_file(cache_ns_dir: Path, url: str) -> Path:
    return cache_ns_dir / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()}.json"


def _bar_day(ms: int) -> date:
    # Polygon stamps a daily bar at the window start (00:00 ET) → its UTC date is the session.
    return datetime.fromtimestamp(ms / 1000.0, tz=UTC).date()


class PolygonAudit:
    """Cached, throttled Polygon reads for the audit. Every response used is logged in ``calls``."""

    def __init__(self, http: CachedHttp, cache_ns_dir: Path) -> None:
        self._http = http
        self._ns = cache_ns_dir
        self.calls: list[CallRecord] = []

    @classmethod
    def from_env(cls, cache_dir: Path, *, requests_per_min: float) -> PolygonAudit:
        load_local_env()
        http = CachedHttp(
            cache_dir=cache_dir, user_agent=sec_user_agent(),
            min_interval_sec=60.0 / requests_per_min, max_retries=4, timeout_sec=60.0,
            namespace="polygon",
            extra_headers={"Authorization": f"Bearer {require_env('POLYGON_API_KEY')}"},
        )
        return cls(http, cache_dir / "polygon")

    # -- plumbing --------------------------------------------------------------------------------
    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET via the netcache (cached forever: every request here names a CLOSED window or a
        point-in-time ``date=``), then log where the bytes came from."""
        data = cast(dict[str, Any], self._http.get_json(url, ttl_seconds=None, params=params))
        u = full_url(url, params)
        entry = json.loads(cache_file(self._ns, u).read_text())
        self.calls.append(CallRecord(
            url=u,
            fetched_at_utc=datetime.fromtimestamp(entry["fetched_at"], tz=UTC).isoformat(),
            sha256=hashlib.sha256(entry["text"].encode("utf-8")).hexdigest(),
            status=str(data.get("status", "")),
        ))
        return data

    def _paged(self, url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        data = self._get(url, params)
        out.extend(data.get("results") or [])
        pages = 1
        while (nxt := data.get("next_url")) and pages < 50:
            data = self._get(str(nxt))
            out.extend(data.get("results") or [])
            pages += 1
        if data.get("next_url"):
            raise PolygonAuditError(f"pagination did not finish within 50 pages: {url} {params}")
        return out

    # -- metadata --------------------------------------------------------------------------------
    def details(self, symbol: str, as_of: date) -> dict[str, Any] | None:
        """Point-in-time ticker details (``date=as_of``). ``None`` when Polygon has no such
        ticker at that date (404) — absence is reported, never filled."""
        try:
            data = self._get(DETAILS_URL.format(symbol=symbol), {"date": as_of.isoformat()})
        except HttpError as exc:
            if _status_of(exc) == 404:
                return None
            raise
        res = data.get("results")
        return cast(dict[str, Any], res) if isinstance(res, dict) else None

    def search(self, query: str) -> list[dict[str, Any]]:
        """Name search across every Polygon market (US stocks + OTC + ...) — used ONLY to record
        which non-primary lines exist for an unavailable listing. Never a substitution path."""
        data = self._get(TICKERS_URL, {"search": query, "limit": 50})
        return list(data.get("results") or [])

    # -- prices ----------------------------------------------------------------------------------
    def daily_raw(self, symbol: str, start: date, end: date) -> list[DailyBar]:
        """RAW (``adjusted=false``) daily bars. A range wholly before the plan window → []."""
        url = AGGS_URL.format(symbol=symbol, start=start.isoformat(), end=end.isoformat())
        params = {"adjusted": "false", "sort": "asc", "limit": 50000}
        try:
            data = self._get(url, params)
        except HttpError as exc:
            if _status_of(exc) == 403:
                return []
            raise
        if data.get("status") not in ("OK", "DELAYED"):
            raise PolygonAuditError(f"aggregates {symbol}: status={data.get('status')!r}")
        u = full_url(url, params)
        return [
            DailyBar(day=_bar_day(int(r["t"])), open=float(r["o"]), high=float(r["h"]),
                     low=float(r["l"]), close=float(r["c"]), volume=float(r["v"]),
                     source="polygon-aggs-live adjusted=false", source_ref=u)
            for r in data.get("results") or []
        ]

    def dividends(self, symbol: str, since: date) -> list[Dividend]:
        rows = self._paged(DIVIDENDS_URL, {
            "ticker": symbol, "ex_dividend_date.gte": since.isoformat(),
            "order": "asc", "sort": "ex_dividend_date", "limit": 1000,
        })
        return [
            Dividend(ex_date=date.fromisoformat(r["ex_dividend_date"]),
                     cash=float(r["cash_amount"]), currency=str(r.get("currency") or ""),
                     dividend_type=str(r.get("dividend_type") or ""),
                     pay_date=str(r.get("pay_date") or ""), polygon_id=str(r.get("id") or ""))
            for r in rows
        ]

    def splits(self, symbol: str) -> list[Split]:
        rows = self._paged(SPLITS_URL, {
            "ticker": symbol, "order": "asc", "sort": "execution_date", "limit": 1000,
        })
        return [
            Split(execution_date=date.fromisoformat(r["execution_date"]),
                  split_from=float(r["split_from"]), split_to=float(r["split_to"]),
                  polygon_id=str(r.get("id") or ""))
            for r in rows
        ]


# --- the repo's grouped-daily cache -----------------------------------------------------------

@dataclass(frozen=True)
class GroupedDay:
    day: date
    fetched_at: date
    n_rows: int
    bars: dict[str, DailyBar]


def read_grouped_cache(cache_ns_dir: Path, day: date, symbols: set[str]) -> GroupedDay | None:
    """One cached whole-market grouped-daily response (``adjusted=true``), filtered to ``symbols``.

    ``None`` when the cache holds no response for that day — a GAP, which the caller reports; it
    is never interpolated. An empty-but-present day (a market holiday) returns ``n_rows == 0``.
    The response is read as the netcache stored it; this function never writes the cache.
    """
    url = full_url(GROUPED_URL.format(day=day.isoformat()), {"adjusted": "true"})
    p = cache_file(cache_ns_dir, url)
    if not p.is_file():
        return None
    entry = json.loads(p.read_text())
    if entry.get("url") != url:
        raise PolygonAuditError(f"cache key collision at {p}: {entry.get('url')!r} != {url!r}")
    data = json.loads(entry["text"])
    if data.get("status") not in ("OK", "DELAYED"):
        raise PolygonAuditError(f"cached grouped-daily {day}: status={data.get('status')!r}")
    fetched = datetime.fromtimestamp(float(entry["fetched_at"]), tz=UTC).date()
    results = data.get("results") or []
    ref = f"netcache:{p.name} ({url}; fetched {fetched.isoformat()})"
    bars = {
        r["T"]: DailyBar(day=day, open=float(r["o"]), high=float(r["h"]), low=float(r["l"]),
                         close=float(r["c"]), volume=float(r["v"]),
                         source=f"polygon-grouped-cache adjusted=true@{fetched.isoformat()}",
                         source_ref=ref)
        for r in results if r.get("T") in symbols
    }
    return GroupedDay(day=day, fetched_at=fetched, n_rows=len(results), bars=bars)
