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
from array import array
from bisect import bisect_left, bisect_right
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
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

    def ticker_details(self, ticker: str, as_of: date | None = None) -> dict[str, Any] | None:
        """The source's reference record for ``ticker`` (as of ``as_of`` when given), or None. A
        source with no reference data answers None, and nothing is then aliased through it."""
        return None

    def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
        """Per-symbol daily bars over ``[start, end]``. A source that cannot serve one symbol's
        history answers [], and a carry then has only the bars the store already holds."""
        return []


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

#: How far back a refresh RE-PULLS sessions the store already holds. Bars are fetched
#: ``adjusted=true``, i.e. restated to the CURRENT split factor, so a bar stored before a split
#: keeps the old basis until it is pulled again; this window is the bounded restatement that
#: catches a split while it is recent. BEYOND it, a session the store already holds is SKIPPED —
#: re-pulling it buys only that restatement, and the store is where those bars already live.
#:
#: WHY IT EXISTS (2026-09-23). The weekly run re-pulled its whole 1,825-day window every time —
#: 1,304 whole-market calls — because CI carries no store and builds one from scratch each run. On
#: a data plan serving ~5 requests/min that finishes nowhere: the run died on the rate limit
#: locally AND in CI. The bars beyond this window are already in the local store; acquiring them
#: again was the waste. THE COST, as first stated: a split older than this window leaves the bars
#: before it on the pre-split basis until something re-pulls them.
#:
#: THAT COST LANDED (2026-10-24), and a re-pull cannot pay it. IESC, SFBS and BYND sat pre-split
#: before 2026-08-06 in the 2026-10-16 weekly's store, and SFBS's G1 PASS rested on the step
#: (`docs/records/2026-10-24-prices-quality-source.md`). The plan serves two years, so held bars
#: older than that can never be pulled again. So each refresh now re-fetches ONE held session it
#: would skip — the latest, its ANCHOR — and `restate_held` puts the older held bars of any name the
#: source has restated onto the current basis
#: (`docs/records/2026-10-26-split-restatement-and-total-return.md`).
RESTATE_WINDOW_DAYS = 30

#: A held bar and its re-fetch describe one session on two split bases when all four prices moved
#: by ONE factor, and that factor is away from 1, both within this fraction. Measured 2026-10-26 on
#: 2026-08-05's whole market: 2,340 of 2,350 names came back identical, and the other 10 moved by a
#: single factor to 1e-6, with volume moving inversely to the cent. A bar that changed any other way
#: is a correction, not a new basis, and restates nothing.
RESTATE_TOL = 0.005

#: A session counts as already ingested only when the store holds bars for at least this share of
#: the securities being ingested — never on presence alone. `refresh --aggs` on one name writes a
#: handful of rows into a session, and reading that as "ingested" would skip the whole market's day.
_SESSION_PRESENT_FRACTION = 0.5

#: A series hole longer than this many market sessions is longer than any trading suspension the
#: SEC may order (Exchange Act §12(k)(1)(A): up to 10 business days). Past it the name left the
#: market, and the bars either side may belong to two securities under one ticker. The price
#: scorecard flags such a hole (`quality.sources.prices`, series_gap) and the identity repair
#: probes it (`eod.identity`); both read this one definition.
GAP_SESSIONS = 10


def market_sessions(per_day: dict[str, int]) -> list[int]:
    """A store's market sessions, as day ordinals: the days holding bars for at least
    `_SESSION_PRESENT_FRACTION` of the most names any one day holds. Others are partial days."""
    top = max(per_day.values())
    return sorted(date.fromisoformat(d).toordinal() for d, n in per_day.items()
                  if n >= _SESSION_PRESENT_FRACTION * top)


def missed_sessions(market: list[int], days: array[int]) -> array[int]:
    """Per step between consecutive bars: the market sessions strictly between them."""
    return array("i", (bisect_left(market, days[i]) - bisect_right(market, days[i - 1])
                       for i in range(1, len(days))))


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


def restatement_factor(held: PriceBar, fresh: RawBar) -> float | None:
    """``fresh ÷ held`` when the source has put this session's bar on a new split basis — open,
    high, low and close all scaled by one factor that is away from 1 — else None (unchanged, or
    changed some other way)."""
    pairs = ((fresh.open, held.open), (fresh.high, held.high), (fresh.low, held.low),
             (fresh.close, held.close))
    if any(h <= 0 or f <= 0 for f, h in pairs):
        return None
    ratios = [f / h for f, h in pairs]
    if abs(ratios[3] - 1.0) <= RESTATE_TOL or max(ratios) / min(ratios) - 1.0 > RESTATE_TOL:
        return None
    return ratios[3]


def restate_held(store: Any, fetch: Callable[[date], dict[str, RawBar]],
                 boundaries: Sequence[date],
                 sym_to_id: Mapping[str, str]) -> dict[str, list[tuple[date, float]]]:
    """Put held bars back on the source's CURRENT split basis, one pull at a time.

    Each boundary is the LAST session of one pull of the store. That session is fetched again and
    set beside the held copy, name by name. Where the source has restated a name
    (`restatement_factor`), the name's held bars from just after the previous boundary through
    this one are scaled by that factor (`Store.restate_bars`). A segment's bars are assumed to
    share their boundary's pull, which is true of a refresh: it writes every session it fetches in
    one pass.

    Why a factor, not a re-pull: the plan serves two years of bars, so an older held bar cannot be
    fetched again. The factor is the source's own, read off a bar it serves today. Returns
    ``{internal_id: [(boundary, factor), ...]}`` for each name restated."""
    bounds = sorted(set(boundaries))
    id_to_sym = {iid: sym for sym, iid in sym_to_id.items()}
    found: dict[str, dict[date, float]] = {}
    for b in bounds:
        fresh = fetch(b)
        for iid, held in store.bars_on(b, list(id_to_sym)).items():
            bar = fresh.get(id_to_sym[iid])
            if bar is not None and (r := restatement_factor(held, bar)) is not None:
                found.setdefault(iid, {})[b] = r
    for iid, by_bound in found.items():
        prev: date | None = None
        for b in bounds:
            if b in by_bound:
                store.restate_bars(iid, by_bound[b], through=b, after=prev)
            prev = b
    return {iid: sorted(v.items()) for iid, v in found.items()}


#: How far back a rename's carry asks the source for the old ticker's bars: the two years the data
#: plan serves (`docs/records/2026-10-26-split-restatement-and-total-return.md`). Older sessions
#: come from the bars the store already holds under the old id.
CARRY_DAYS = 730


def carry_forward(client: EodClient, store: Any, *, predecessor_id: str, predecessor_symbol: str,
                  successor_id: str, listed: date, end: date) -> int:
    """Write a renamed line's history under its NEW id: every session before ``listed`` (the day
    the new ticker started trading), so each reader of ``Store.get_price_history`` sees one
    unbroken series. The old id keeps its own bars untouched — it is never re-keyed.

    The source's own bars for the OLD ticker win over the store's copies (they are on the source's
    current split basis), and the store's copies fill what the plan no longer serves. THOSE COPIES
    ARE SET BESIDE A FRESH BAR FIRST (L7's caution): on the earliest session both hold, a held bar
    the source has since restated (`restatement_factor`) means every copy older than the source's
    window is put on the current basis — prices × factor, volume ÷ factor, `+restated` on its
    source, as `Store.restate_bars` does. Bars already held under the new id are never
    overwritten. Each carried bar names its origin (``polygon-alias:<old id>``). Runs once per
    alias: a new id that already holds a CARRIED bar before ``listed`` has been carried. Its own
    bars there do not count — a re-domicile's new id can hold the ticker's last weeks before the
    pair is known (Codex, #839 round 2). Returns the bars written."""
    own = store.get_price_history(successor_id)
    if any(b.bar_date < listed and b.source.startswith("polygon-alias:") for b in own):
        return 0
    taken = {b.bar_date for b in own}
    held = {b.bar_date: b for b in store.get_price_history(predecessor_id) if b.bar_date < listed}
    fresh = {d: b for d, b in client.daily_bars(predecessor_symbol,
                                                end - timedelta(days=CARRY_DAYS),
                                                listed - timedelta(days=1)) if d < listed}
    both = sorted(set(held) & set(fresh))
    factor = (restatement_factor(held[both[0]], fresh[both[0]]) if both else None) or 1.0
    tag = f"polygon-alias:{predecessor_id}"
    rows = [PriceBar(internal_id=successor_id, bar_date=d, open=b.open * f, high=b.high * f,
                     low=b.low * f, close=b.close * f, volume=b.volume / f,
                     source=tag + ("+restated" if f != 1.0 else ""))
            for d, b, f in sorted([(d, b, factor) for d, b in held.items() if d not in fresh]
                                  + [(d, b, 1.0) for d, b in fresh.items()],
                                  key=lambda x: x[0])
            if d not in taken]
    return int(store.write_prices(rows))


def holders(securities: Iterable[Identity],
            first_sessions: Mapping[str, date] | None = None) -> Callable[[date], dict[str, str]]:
    """``on(day) -> {symbol: internal_id}``: the security that held each symbol ON THAT DAY.

    WHY (2026-10-28). Ingest built ``{eod_symbol: internal_id}`` from TODAY's securities and
    filed every fetched day by it, so a reused ticker's former holder's bars landed under the
    current holder's id (L7: CALY held a BlackRock ETF's 2023–24 bars). An id with a first session
    (`aliases.first_sessions`: a reused ticker's tenure, an alias's listing) holds its symbol only
    from that day; before it the symbol is another id's, or nobody's here, and the bar is not
    written under it. Where several ids could hold one symbol, the latest first session on or
    before the day wins; among ids with none, the last given, as the old dict's did."""
    starts = first_sessions or {}
    by_sym: dict[str, list[tuple[date, int, str]]] = {}
    for i, s in enumerate(securities):
        by_sym.setdefault(s.eod_symbol, []).append(
            (starts.get(s.internal_id, date.min), i, s.internal_id))

    def on(day: date) -> dict[str, str]:
        return {sym: max(c)[2] for sym, cands in by_sym.items()
                if (c := [x for x in cands if x[0] <= day])}
    return on


def ingest_prices(
    client: EodClient,
    store: Any,
    securities: Iterable[Identity],
    *,
    start: date,
    end: date,
    progress: ProgressFn | None = None,
    restate_window_days: int = RESTATE_WINDOW_DAYS,
    first_sessions: Mapping[str, date] | None = None,
) -> dict[str, Any]:
    """Backfill/refresh EOD bars for ``securities`` over [start, end] into the store.

    Fails loud: a degraded day raises inside ``grouped_daily`` and aborts the whole refresh, so the
    store never ends up with a silent gap. Non-trading days (0 rows) are skipped. Returns a summary.
    ``progress`` (opt-in) gets an ``EOD <done>/<total>`` line per step so a long pull is visible.

    A session the store ALREADY HOLDS is skipped unless it falls inside the restatement window
    (:data:`RESTATE_WINDOW_DAYS`) — see that constant for what the re-pull buys and what skipping
    it costs. "Already holds" is a COUNT test (:data:`_SESSION_PRESENT_FRACTION`), so a single-name
    refresh's handful of rows never passes for a whole-market day. A store that cannot report what
    it holds is never trusted into a skip: it re-pulls everything, exactly as before.

    A bar is filed under the id that held its symbol THAT day (`holders`, ``first_sessions``).
    """
    secs = list(securities)
    on = holders(secs, first_sessions)
    id_to_sym = {s.internal_id: s.eod_symbol for s in secs}
    all_ids = sorted(id_to_sym)
    symbols = len(set(id_to_sym.values()))
    days = list(_trading_days(start, end))
    restate_from = end - timedelta(days=restate_window_days)
    counts = getattr(store, "session_bar_counts", None)
    stored = dict(counts(start, end, all_ids)) if callable(counts) else {}
    present_floor = _SESSION_PRESENT_FRACTION * symbols
    reporter = ProgressReporter("EOD", len(days), emit=progress)
    days_seen = 0
    days_fetched = 0
    days_skipped = 0
    bars_written = 0
    trading_days = 0
    # THE ANCHOR: the latest held session this refresh would skip. Fetched once and set beside the
    # held copy, so a split since that pull restates the older held bars instead of leaving them on
    # the old basis under bars pulled on the new one (see RESTATE_WINDOW_DAYS). Every session after
    # it is fetched below, so the anchor bounds the only bars that can still be stale.
    # A store that cannot hand back a held bar is never asked to restate one (an older or foreign
    # store), and the anchor then skips like any held session, exactly as before.
    anchor = (max((d for d in days if d < restate_from and stored.get(d, 0) >= present_floor),
                  default=None) if callable(getattr(store, "bars_on", None)) else None)
    restated: dict[str, list[tuple[date, float]]] = {}
    anchor_bars: dict[str, RawBar] = {}
    on_anchor: set[str] = set()
    if anchor is not None:
        days_fetched += 1
        anchor_bars = client.grouped_daily(anchor)
        on_anchor = set(store.bars_on(anchor, all_ids))
        restated = restate_held(store, lambda _d: anchor_bars, [anchor], on(anchor))
    written: set[str] = set()
    for day in days:
        days_seen += 1
        if day != anchor and day < restate_from and stored.get(day, 0) >= present_floor:
            days_skipped += 1
            reporter.tick(days_seen, suffix=f"{bars_written:,} bars · {days_skipped} held")
            continue
        if day == anchor:
            raw = anchor_bars                     # fetched once, above; written like any session
        else:
            days_fetched += 1
            raw = client.grouped_daily(day)
        if not raw:
            reporter.tick(days_seen, suffix=f"{bars_written:,} bars")
            continue  # non-trading day (holiday/weekend)
        trading_days += 1
        held = on(day)
        rows = [
            PriceBar(
                internal_id=held[t],
                bar_date=day,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                source="polygon-grouped",
            )
            for t, b in raw.items()
            if t in held
        ]
        bars_written += store.write_prices(rows)
        written.update(r.internal_id for r in rows)
        reporter.tick(days_seen, suffix=f"{bars_written:,} bars")
    # A NAME WITH NO BAR ON THE ANCHOR is not checked by it — it did not trade that day, or had
    # stopped. If this run wrote it new bars, its older held bars are set beside the source at its
    # OWN latest held session, one call per distinct date. Measured 2026-10-26: PSTV's held bars end
    # 2026-07-31, before the anchor, and Polygon now serves its whole history ×0.04 — bars resuming
    # on the new basis would have spliced it. Names that got no new bars cost nothing here.
    # AND WHEN THERE IS NO ANCHOR AT ALL (Codex, #796 round 1): a range that starts inside the
    # restatement window skips no held session, so every name that got new bars is checked at its
    # last held bar BEFORE THE RANGE — the bars this run did not touch.
    before = anchor if anchor is not None else (days[0] if days else None)
    if before is not None and callable(getattr(store, "bars_on", None)):
        # keyed by date and a slot, so two ids of one symbol never share a {symbol: id} group
        late: dict[tuple[date, int], dict[str, str]] = {}
        for iid in sorted(written - on_anchor):
            if (last := store.last_bar_before(iid, before)) is not None:
                slot = 0
                while id_to_sym[iid] in late.get((last, slot), {}):
                    slot += 1
                late.setdefault((last, slot), {})[id_to_sym[iid]] = iid
        for (last, _slot), group in sorted(late.items()):
            days_fetched += 1
            restated.update(restate_held(store, client.grouped_daily, [last], group))
    return {
        "days_fetched": days_fetched,
        "days_skipped": days_skipped,
        "trading_days": trading_days,
        "bars_written": bars_written,
        "universe_size": symbols,
        # SAID IN THE SUMMARY, NEVER SILENT: which names had held bars restated, and by what
        "anchor": anchor.isoformat() if anchor is not None else None,
        "restated": {id_to_sym[iid]: [f for _b, f in v] for iid, v in sorted(restated.items())},
    }


def ingest_prices_per_symbol(
    client: PolygonEodClient,
    store: Any,
    securities: Iterable[Identity],
    *,
    start: date,
    end: date,
    progress: ProgressFn | None = None,
    first_sessions: Mapping[str, date] | None = None,
) -> dict[str, int]:
    """Backfill via ONE per-symbol aggregates call each (``daily_bars``) instead of grouped-daily.

    grouped-daily fetches the WHOLE market per day — right for the ongoing universe refresh, but for
    backfilling a NEW name's history that is ~250 whole-market calls at the free tier's ~5/min (the
    NCNO-class stall: a name that entered the tracked set with no history — its stock-perf
    exhibit and 180d returns were all UNKNOWN). Polygon HAS the history; this pulls it in ONE call
    per symbol. Same store, same PriceBar shape — the efficient path for a per-name backfill."""
    secs = list(securities)
    starts = first_sessions or {}
    reporter = ProgressReporter("EOD-aggs", len(secs), emit=progress)
    bars_written = 0
    empty: list[str] = []
    for i, s in enumerate(secs, 1):
        rows = [
            PriceBar(
                internal_id=s.internal_id, bar_date=d, open=b.open, high=b.high, low=b.low,
                close=b.close, volume=b.volume, source="polygon-aggs",
            )
            # a symbol's aggregates are the TICKER's, whoever held it: none before this id's own
            # first session is filed under it (`holders`)
            for d, b in client.daily_bars(s.eod_symbol, start, end)
            if d >= starts.get(s.internal_id, date.min)
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
            n = (self.ticker_details(t) or {}).get("share_class_shares_outstanding")
            if n:
                out[t] = float(n)
        return out

    def ticker_details(self, ticker: str, as_of: date | None = None) -> dict[str, Any] | None:
        """``/v3/reference/tickers/<T>`` — today's record (cached a day), or the record AS OF a
        date, which is how a renamed ticker's share class is read after the ticker is gone (cached
        for good: a past date's record does not change). None on a failed lookup, never a guess."""
        try:
            raw = self._http.get_json(
                f"{_REFERENCE}/{ticker}", ttl_seconds=None if as_of else _ONE_DAY,
                params={"date": as_of.isoformat()} if as_of else None)
        except HttpError:
            return None
        return cast(dict[str, Any], raw).get("results") or None

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
