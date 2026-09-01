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
from collections.abc import Iterable, Iterator, Sequence
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


#: How far back :func:`last_completed_session` will probe before giving up. A four-day weekend plus
#: a stacked holiday is the worst real case; 10 covers it without probing indefinitely on an outage.
_SESSION_LOOKBACK_DAYS = 10


def last_completed_session(client: EodClient, *, today: date,
                           lookback_days: int = _SESSION_LOOKBACK_DAYS) -> date:
    """The newest date the MARKET DATA reaches — asked of the data, never of a calendar.

    WHY THIS EXISTS. `vinci run-weekly` defaulted its `--end` to `date.today()`, so the whole
    screen — universe as-of, `reference_date`, every relative-return window — was stamped with the
    WALL CLOCK. On Monday 2026-08-24 the job fired at 07:04 UTC, six hours before the US market
    opened, and stamped a queue `2026-08-24` when the newest bar that could exist was Friday's.
    `test_the_wall_clock_is_unreachable_from_the_reference_date` refused it at the gate, correctly,
    and the weekly run had not been able to go green since. This is the same defect `_ref_of` was
    fixed for in `assemble.py` (#355, "a reference date names a moment the data reaches, never the
    clock") — that fix is guarded by an AST scan which reads `assemble.py` ONLY, so the
    orchestrator's entry point kept its wall clock.

    THE DATA DECIDES WHAT A SESSION IS; the weekday check is COST, not knowledge. `grouped_daily`
    returns an EMPTY dict for any non-trading day, so holidays, half-days and a session that has
    not closed all answer for themselves — no holiday table is shipped, and none can rot. The
    `weekday() < 5` skip only avoids spending two calls on a weekend it would reject anyway, which
    is exactly what `_trading_days` above already does for the same reason. Remove it and the
    answer is unchanged; the probe just costs more.

    IT PROBES FROM `today - 1`, NEVER `today`. A session still in progress can return partial
    aggregates, and stamping a record with a date whose bars are half-formed is the lookahead
    trapdoor this repo has already shut once for entry prices. Yesterday-or-earlier can only ever
    name a CLOSED session, so the answer is safe by construction rather than by timing. The cost is
    that a run fired after today's close stamps yesterday — a stamp that LAGS the data is harmless
    (the gate asserts `fleet <= frontier`); a stamp that LEADS it is the bug being fixed.

    Raises rather than guessing when nothing answers inside the window — a fabricated date here
    would propagate into every stamp the run writes.
    """
    day = today - timedelta(days=1)
    for _ in range(lookback_days):
        if day.weekday() < 5 and client.grouped_daily(day):
            return day
        day -= timedelta(days=1)
    raise RuntimeError(
        f"no completed trading session found in the {lookback_days} days before {today} — the EOD "
        f"source returned no rows for any of them. Refusing to date a run by the wall clock; pass "
        f"an explicit --end naming a session you know closed."
    )


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
    empty: list[str] = []
    for i, s in enumerate(secs, 1):
        rows = [
            PriceBar(
                internal_id=s.internal_id, bar_date=d, open=b.open, high=b.high, low=b.low,
                close=b.close, volume=b.volume, source="polygon-aggs",
            )
            for d, b in client.daily_bars(s.eod_symbol, start, end)
        ]
        if not rows:
            empty.append(s.eod_symbol)  # OK-but-empty ⇒ mis-resolved symbol or out-of-window range
        bars_written += store.write_prices(rows)
        reporter.tick(i, suffix=f"{s.eod_symbol} {len(rows)} bars")
    # FAIL LOUD: a 0-bar backfill IS the NCNO-class silent gap this path exists to prevent — an OK
    # response with no rows (a symbol Polygon doesn't carry, or an out-of-window range) must never
    # read as success. The non-empty names are already written; the operator re-runs these.
    if empty:
        raise EodError(
            f"per-symbol backfill returned NO bars for {empty} — mis-resolved eod_symbol or an "
            f"out-of-window date range; the store gained nothing for these (a silent gap)"
        )
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

    def share_class_counts(self, tickers: Sequence[str]) -> dict[str, float]:
        """``{ticker: shares outstanding OF THE TRADED SHARE CLASS}`` — one cached details call per
        ticker. Absent/zero is OMITTED, never zero-filled: the caller must fail loud.

        WHY THIS EXISTS (measured 2026-08-31). For an ADR the traded unit is the ADS, and the price
        is per ADS — but the filer's XBRL count is usually per ORDINARY share, and nothing converted
        between them. TSM's cap computed as $10,635B (close x 25.9bn ordinary) against Polygon's own
        market_cap of $2,165B: a ~5x error, large enough to push it past the theme band's $10T
        ceiling and out of every band. This count is denominated in the SAME unit as the price, so
        price x count needs no ratio arithmetic at all.

        PER-TICKER BY NECESSITY: the bulk reference feed carries only ticker/type/cik (verified), so
        the share count lives on the details endpoint. Scoped by the caller to ADR/GDR names only —
        ~375 on US venues — and cached for a day, so a rebuild re-reads nothing."""
        out: dict[str, float] = {}
        for t in tickers:
            # ONE BAD TICKER MUST NOT KILL A TEN-MINUTE BUILD. `get_json` raises on a
            # non-retryable status or exhausted retries, and this is called per-name from inside
            # the universe loop — so a single 404 (a delisted-but-still-priced symbol) would abort
            # the whole run, which has no partial-progress recovery. The value is OPTIONAL by
            # design: absent already means "drop this name loudly", so skipping a failed lookup
            # yields the same, already-counted outcome. Same idiom, same reasoning as
            # `mention_prefilter(skip_errors=True)`: a conservative gap, never a fabricated value.
            try:
                raw = self._http.get_json(f"{_REFERENCE}/{t}", ttl_seconds=_ONE_DAY)
            except HttpError:
                continue
            res = cast(dict[str, Any], raw).get("results") or {}
            n = res.get("share_class_shares_outstanding")
            if n:
                out[t] = float(n)
        return out

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        url = _GROUPED.format(day=day.isoformat())
        # A CLOSED DAY'S BARS ARE NOT IMMUTABLE, AND THE 24h TTL IS WHY THIS IS CORRECT. The
        # comment here used to read "immutable once the day has closed → cache forever" while the
        # code passed `_ONE_DAY`; `netcache` honours that TTL, so the comment described a policy
        # the code did not implement — and following it would have BROKEN working code.
        # `adjusted=true` returns prices restated to the CURRENT split factor, so a bar cached
        # before a split and never re-fetched would be stranded on the old basis permanently. The
        # expiry is what lets the weekly refresh re-pull its rolling 1825d window
        # (`screens/run.py`) and overwrite every bar in it via `INSERT OR REPLACE`. Verified on
        # FUBO's ~1-for-11 reverse split: its 2021 closes read ~$312 against the ~$28 it actually
        # traded at, i.e. the whole stored history sits on the post-split basis, and no 11x step
        # exists anywhere in the series.
        # THE BOUND, stated because nothing enforces it: bars OLDER than that rolling window are
        # never re-fetched by any automated path, so a store deeper than 1825d could hold
        # pre-split bars indefinitely. Measured 2026-08-03 — 0 securities sit more than 30d beyond
        # the window, so the hazard is bounded today, not designed out.
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
