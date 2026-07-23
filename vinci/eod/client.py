"""EOD price client — Polygon Grouped Daily (primary) behind a swappable interface.

Why grouped-daily: one call returns OHLCV for the *entire* US market for a date, so per-symbol rate
limits don't apply and universe size is irrelevant. Backfill cost scales with the number of *days*,
not names (Polygon free tier ≈ 5 calls/min → a 2-year backfill is one throttled, cached job).

**Fail-loud on partial/incomplete refresh** (a hard requirement): a real trading day returns ~10-12k
rows; a non-trading day returns 0 (legitimate, skipped). A ``status != "OK"`` response, or an OK
response with ``0 < rows < floor`` signals a partial fetch and **raises** — never writing a half day
that would feed stale/incomplete prices into the gates or the scoring harness.

The Polygon key travels in the ``Authorization: Bearer`` header (never a ``?apiKey=`` param), so it
stays out of request URLs, the on-disk cache, and error messages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

from pydantic import BaseModel

from vinci.config import Config, get_config, require_env, sec_user_agent
from vinci.netcache import CachedHttp, HttpError
from vinci.progress import ProgressFn, ProgressReporter
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar

_GROUPED = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{day}"
_AGGS = "https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}"
_REFERENCE = "https://api.polygon.io/v3/reference/tickers"
_ONE_DAY = 86_400.0


class EodError(RuntimeError):
    """A partial/degraded/failed EOD fetch — raised rather than writing incomplete data."""


class RawBar(BaseModel, frozen=True):
    """One raw OHLCV bar from an EOD source, before resolution to an internal id."""

    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class EodClient(ABC):
    """The swappable EOD interface. Polygon is primary; Tiingo is the backfill alternative."""

    @abstractmethod
    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        """Whole-market OHLCV for one date, keyed by source ticker. Empty dict = non-trading day."""


def _trading_days(start: date, end: date) -> Iterator[date]:
    """Weekdays in [start, end]. Market holidays are handled downstream (they return 0 rows)."""
    d = start
    while d <= end:
        if d.weekday() < 5:  # Mon-Fri
            yield d
        d += timedelta(days=1)


def ingest_prices(
    client: EodClient,
    store: Any,
    securities: Iterable[Identity],
    *,
    start: date,
    end: date,
    progress: ProgressFn | None = None,
) -> dict[str, int]:
    """Backfill/refresh EOD bars for ``securities`` over [start, end] into the store.

    Fails loud: a degraded day raises inside ``grouped_daily`` and aborts the whole refresh, so the
    store never ends up with a silent gap. Non-trading days (0 rows) are skipped. Returns a summary.
    ``progress`` (opt-in) gets an ``EOD <done>/<total>`` line per step so a long pull is visible.
    """
    sym_to_id = {s.eod_symbol: s.internal_id for s in securities}
    days = list(_trading_days(start, end))
    reporter = ProgressReporter("EOD", len(days), emit=progress)
    days_fetched = 0
    bars_written = 0
    trading_days = 0
    for day in days:
        days_fetched += 1
        raw = client.grouped_daily(day)
        if not raw:
            reporter.tick(days_fetched, suffix=f"{bars_written:,} bars")
            continue  # non-trading day (holiday/weekend)
        trading_days += 1
        rows = [
            PriceBar(
                internal_id=sym_to_id[t],
                bar_date=day,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                source="polygon-grouped",
            )
            for t, b in raw.items()
            if t in sym_to_id
        ]
        bars_written += store.write_prices(rows)
        reporter.tick(days_fetched, suffix=f"{bars_written:,} bars")
    return {
        "days_fetched": days_fetched,
        "trading_days": trading_days,
        "bars_written": bars_written,
        "universe_size": len(sym_to_id),
    }


def ingest_prices_per_symbol(
    client: PolygonEodClient,
    store: Any,
    securities: Iterable[Identity],
    *,
    start: date,
    end: date,
    progress: ProgressFn | None = None,
) -> dict[str, int]:
    """Backfill via ONE per-symbol aggregates call each (``daily_bars``) instead of grouped-daily.

    grouped-daily fetches the WHOLE market per day — right for the ongoing universe refresh, but for
    backfilling a NEW name's history that is ~250 whole-market calls at the free tier's ~5/min (the
    NCNO-class stall: a name that entered the tracked set with no history — its stock-perf
    exhibit and 180d returns were all UNKNOWN). Polygon HAS the history; this pulls it in ONE call
    per symbol. Same store, same PriceBar shape — the efficient path for a per-name backfill."""
    secs = list(securities)
    reporter = ProgressReporter("EOD-aggs", len(secs), emit=progress)
    bars_written = 0
    for i, s in enumerate(secs, 1):
        rows = [
            PriceBar(
                internal_id=s.internal_id, bar_date=d, open=b.open, high=b.high, low=b.low,
                close=b.close, volume=b.volume, source="polygon-aggs",
            )
            for d, b in client.daily_bars(s.eod_symbol, start, end)
        ]
        bars_written += store.write_prices(rows)
        reporter.tick(i, suffix=f"{s.eod_symbol} {len(rows)} bars")
    return {"symbols": len(secs), "bars_written": bars_written}


class PolygonEodClient(EodClient):
    """Polygon.io Grouped Daily adapter (primary). Header auth; fail-loud on partial refresh."""

    def __init__(self, http: CachedHttp, *, min_results: int) -> None:
        self._http = http
        self._min_results = min_results

    @classmethod
    def from_config(cls, config: Config | None = None) -> PolygonEodClient:
        cfg = config or get_config()
        cfg.ensure_dirs()
        http = CachedHttp(
            cache_dir=cfg.cache_dir,
            user_agent=sec_user_agent(),
            min_interval_sec=60.0 / cfg.pacing.polygon_requests_per_min,
            max_retries=cfg.pacing.max_retries,
            timeout_sec=cfg.pacing.http_timeout_sec,
            namespace="polygon",
            extra_headers={"Authorization": f"Bearer {require_env('POLYGON_API_KEY')}"},
        )
        return cls(http, min_results=cfg.grouped_daily_min_results)

    def security_types(self) -> dict[str, str | None]:
        """``{ticker: Polygon security type}`` for all active US stocks — the instrument-type gate.

        One cached, paginated bulk reference pull (no per-name calls); universe size is irrelevant —
        the same breadth-tool discipline as grouped-daily. ``type`` is ``None`` when Polygon lists a
        ticker without one; the universe gate treats that fail-closed (excluded, never admitted).
        """
        out: dict[str, str | None] = {}
        url: str | None = _REFERENCE
        params: dict[str, Any] | None = {"market": "stocks", "active": "true", "limit": 1000}
        pages = 0
        while url and pages < 50:  # ~13 pages for ~12.8k stocks; 50 is a safety stop, not a cap
            raw = self._http.get_json(url, ttl_seconds=_ONE_DAY, params=params)
            data = cast(dict[str, Any], raw)
            for r in data.get("results", []):
                if (t := r.get("ticker")) is not None:
                    out[t] = r.get("type") or None
            url = data.get("next_url")
            params = None  # the cursor is carried inside next_url
            pages += 1
        return out

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        url = _GROUPED.format(day=day.isoformat())
        # immutable once the day has closed → cache forever
        try:
            raw = self._http.get_json(url, ttl_seconds=_ONE_DAY, params={"adjusted": "true"})
        except HttpError as exc:
            # A date before the plan's rolling history window returns 403 NOT_AUTHORIZED — that is
            # "no data for this date" (the start of available history), not a degraded refresh.
            if "NOT_AUTHORIZED" in str(exc):
                return {}
            raise
        data = cast(dict[str, Any], raw)
        return parse_grouped_daily(data, day=day, min_results=self._min_results)

    def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
        """Per-symbol daily OHLCV over ``[start, end]`` (one cached call). Used for the benchmark
        (IWM) history — grouped-daily only stores the finalist universe, so the index that the G2
        idio comparison and the stock-performance exhibit need is fetched here. Fail-loud on a
        non-OK status; ``adjusted`` so splits/dividends don't fabricate a step in the path."""
        url = _AGGS.format(symbol=symbol, start=start.isoformat(), end=end.isoformat())
        raw = self._http.get_json(
            url, ttl_seconds=_ONE_DAY, params={"adjusted": "true", "sort": "asc", "limit": 50000}
        )
        return parse_aggregates(cast(dict[str, Any], raw), symbol=symbol)


def parse_aggregates(data: dict[str, Any], *, symbol: str) -> list[tuple[date, RawBar]]:
    """Pure parser + fail-loud guard for a Polygon per-symbol aggregates response (unit-testable).

    Each bar's ``t`` is the window-start epoch-ms (ET midnight of the trading day); its UTC date is
    that trading day. An OK/DELAYED status with no results is a legitimate empty range → []."""
    status = data.get("status")
    if status not in ("OK", "DELAYED"):
        raise EodError(f"aggregates {symbol}: status={status!r} ({data.get('error') or data})")
    out: list[tuple[date, RawBar]] = []
    for r in data.get("results") or []:
        t = r.get("t")
        if t is None:
            continue
        d = datetime.fromtimestamp(t / 1000.0, tz=UTC).date()
        bar = RawBar(
            ticker=symbol, open=r["o"], high=r["h"], low=r["l"], close=r["c"], volume=r["v"]
        )
        out.append((d, bar))
    return out


def parse_grouped_daily(data: dict[str, Any], *, day: date, min_results: int) -> dict[str, RawBar]:
    """Pure parser + fail-loud guard for a Polygon grouped-daily response (unit-testable)."""
    status = data.get("status")
    if status not in ("OK", "DELAYED"):
        raise EodError(f"grouped-daily {day}: status={status!r} ({data.get('error') or data})")
    results = data.get("results") or []
    count = data.get("resultsCount", len(results))
    if count == 0:
        return {}  # non-trading day — legitimate, not an error
    if count < min_results:
        raise EodError(
            f"Polygon grouped-daily {day}: only {count} rows (< floor {min_results}) — "
            "partial/degraded refresh, refusing to write"
        )
    out: dict[str, RawBar] = {}
    for r in results:
        t = r.get("T")
        if t is None:
            continue
        out[t] = RawBar(
            ticker=t, open=r["o"], high=r["h"], low=r["l"], close=r["c"], volume=r["v"]
        )
    return out
