"""Step 3 verification — the EOD client + Screen-2 price features.

Unit tests verify the feature math and the Polygon/Tiingo parsers deterministically on synthetic
data (so correctness doesn't depend on a live feed). Network tests confirm Polygon Grouped Daily
behaves as assumed (whole-market rows on a trading day, empty on a weekend) and the ingest pipeline
writes real bars to the store.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from vinci.eod import (
    EodError,
    PolygonEodClient,
    compute_price_features,
    ingest_prices,
    parse_aggregates,
    parse_grouped_daily,
    parse_tiingo_prices,
    relative_return,
)
from vinci.eod.client import RawBar
from vinci.eod.features import _close_on_or_before
from vinci.resolver import EntityResolver
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import CoverageStatus
from vinci.schemas.market import PriceBar
from vinci.store import Store

REF = date(2026, 6, 15)


def _bar(d: date, *, o=100.0, h=101.0, low=99.0, c=100.0, v=1_000_000.0, iid="X") -> PriceBar:
    return PriceBar(
        internal_id=iid, bar_date=d, open=o, high=h, low=low, close=c, volume=v, source="t"
    )


# --- parse_grouped_daily (fail-loud guard) ----------------------------------------------------
def test_parse_grouped_daily_ok() -> None:
    data = {
        "status": "OK",
        "resultsCount": 3,
        "results": [
            {"T": "AAPL", "o": 1.0, "h": 2.0, "l": 0.5, "c": 1.5, "v": 1000.0},
            {"T": "MSFT", "o": 1.0, "h": 2.0, "l": 0.5, "c": 1.8, "v": 2000.0},
            {"T": "BRK.B", "o": 1.0, "h": 2.0, "l": 0.5, "c": 1.9, "v": 50.0},
        ],
    }
    bars = parse_grouped_daily(data, day=REF, min_results=2)
    assert set(bars) == {"AAPL", "MSFT", "BRK.B"}
    assert bars["AAPL"].close == 1.5


def test_parse_grouped_daily_nontrading_day_is_empty() -> None:
    data = {"status": "OK", "resultsCount": 0, "results": []}
    assert parse_grouped_daily(data, day=REF, min_results=2) == {}


def test_parse_grouped_daily_partial_fails_loud() -> None:
    # status OK but far too few rows for a trading day -> partial/degraded -> must raise
    row = {"T": "AAPL", "o": 1, "h": 2, "l": 1, "c": 1.5, "v": 1}
    data = {"status": "OK", "resultsCount": 1, "results": [row]}
    with pytest.raises(EodError):
        parse_grouped_daily(data, day=REF, min_results=3000)


def test_parse_grouped_daily_error_status_fails_loud() -> None:
    with pytest.raises(EodError):
        parse_grouped_daily({"status": "ERROR", "error": "bad key"}, day=REF, min_results=2)


# --- parse_aggregates (per-symbol daily bars, for the benchmark backfill) ----------------------
def test_parse_aggregates_maps_timestamp_to_trading_date_and_ohlcv() -> None:
    # t is window-start epoch-ms (ET midnight): 1_719_806_400_000 → 2024-07-01 04:00Z → 2024-07-01
    data = {
        "status": "DELAYED",  # historical IWM is served DELAYED on the free tier — still valid
        "resultsCount": 2,
        "results": [
            {"o": 203.5, "h": 203.8, "l": 200.5, "c": 201.2, "v": 2.2e7, "t": 1_719_806_400_000},
            {"o": 201.2, "h": 205.0, "l": 201.0, "c": 204.4, "v": 1.8e7, "t": 1_719_892_800_000},
        ],
    }
    rows = parse_aggregates(data, symbol="IWM")
    assert [d.isoformat() for d, _ in rows] == ["2024-07-01", "2024-07-02"]
    _d0, b0 = rows[0]
    assert b0.ticker == "IWM" and b0.close == 201.2 and b0.open == 203.5 and b0.volume == 2.2e7


def test_parse_aggregates_empty_results_is_empty_list() -> None:
    # an OK status with no bars is a legitimate empty range (weekend/holiday span), not an error
    assert parse_aggregates({"status": "OK", "resultsCount": 0, "results": []}, symbol="IWM") == []
    assert parse_aggregates({"status": "OK"}, symbol="IWM") == []  # missing 'results' key → []


def test_parse_aggregates_error_status_fails_loud() -> None:
    with pytest.raises(EodError):
        parse_aggregates({"status": "ERROR", "error": "bad key"}, symbol="IWM")
    with pytest.raises(EodError):  # a NOT_AUTHORIZED-style non-OK must raise, never silently drop
        parse_aggregates({"status": "NOT_AUTHORIZED"}, symbol="IWM")


# --- parse_tiingo_prices ----------------------------------------------------------------------
def test_parse_tiingo_prices() -> None:
    rows = [
        {"date": "2024-01-02T00:00:00.000Z", "adjOpen": 10.0, "adjHigh": 11.0,
         "adjLow": 9.0, "adjClose": 10.5, "adjVolume": 1000.0},
    ]
    bars = parse_tiingo_prices(rows, "SEC-X-FOO")
    assert len(bars) == 1
    assert bars[0].bar_date == date(2024, 1, 2)
    assert bars[0].close == 10.5 and bars[0].source == "tiingo"


# --- feature math (synthetic, deterministic) --------------------------------------------------
def _year_series() -> list[PriceBar]:
    """13 monthly bars (the 15th) ending REF, with hand-chosen highs/lows/closes."""
    spec = [
        (date(2025, 6, 15), 100.0, 105.0, 95.0),
        (date(2025, 7, 15), 130.0, 135.0, 100.0),
        (date(2025, 8, 15), 180.0, 185.0, 130.0),
        (date(2025, 9, 15), 195.0, 200.0, 180.0),  # 52w HIGH = 200
        (date(2025, 10, 15), 170.0, 198.0, 165.0),
        (date(2025, 11, 15), 150.0, 175.0, 140.0),
        (date(2025, 12, 15), 160.0, 165.0, 95.0),  # ret_6m close = 160
        (date(2026, 1, 15), 140.0, 162.0, 92.0),
        (date(2026, 2, 15), 130.0, 145.0, 90.0),   # 52w LOW = 90
        (date(2026, 3, 15), 150.0, 155.0, 125.0),  # ret_3m close = 150
        (date(2026, 4, 15), 135.0, 152.0, 130.0),
        (date(2026, 5, 15), 125.0, 140.0, 120.0),
        (date(2026, 6, 15), 120.0, 128.0, 118.0),  # last close = 120
    ]
    return [_bar(d, o=c, h=h, low=lo, c=c) for d, c, h, lo in spec]


def test_features_52w_and_returns() -> None:
    f = compute_price_features(_year_series(), reference_date=REF, staleness_days=5)
    assert f.last.coverage_status is CoverageStatus.PRESENT and f.last.value == 120.0
    assert f.high_52w.value == 200.0
    assert f.low_52w.value == 90.0
    assert f.drawdown_from_high.value == pytest.approx(120.0 / 200.0 - 1.0)  # -0.40
    assert f.dist_from_low.value == pytest.approx(120.0 / 90.0 - 1.0)  # +0.333
    assert f.ret_12m.value == pytest.approx(120.0 / 100.0 - 1.0)  # +0.20
    assert f.ret_6m.value == pytest.approx(120.0 / 160.0 - 1.0)  # -0.25
    assert f.ret_3m.value == pytest.approx(120.0 / 150.0 - 1.0)  # -0.20
    # only 3 monthly bars fall in the 90d window -> ADV defers
    assert f.adv_90d_shares.coverage_status is CoverageStatus.UNKNOWN
    # rel-return-vs-sector always defers to step 5 (needs SIC peers)
    assert f.rel_ret_vs_market.coverage_status is CoverageStatus.UNKNOWN


def test_features_adv_and_volume_spike() -> None:
    bars = []
    for i in range(20):
        d = REF - timedelta(days=19 - i)
        bars.append(_bar(d, c=100.0, v=2_000_000.0 if i == 19 else 1_000_000.0))
    f = compute_price_features(
        bars, reference_date=REF, staleness_days=5, market_cap=1_000_000_000.0
    )
    assert f.adv_90d_shares.value == pytest.approx(1_050_000.0)  # (19*1e6 + 2e6)/20
    assert f.adv_90d_usd.value == pytest.approx(105_000_000.0)  # close 100 * adv
    assert f.volume_spike.value == pytest.approx(2_000_000.0 / 1_050_000.0)
    assert f.turnover.value == pytest.approx(0.105)  # adv_usd / market_cap
    # < 1y of history -> 52w features defer rather than report a misleading short-window high
    assert f.high_52w.coverage_status is CoverageStatus.UNKNOWN
    assert f.ret_12m.coverage_status is CoverageStatus.UNKNOWN


def test_features_staleness_and_empty() -> None:
    stale = compute_price_features(
        [_bar(date(2026, 6, 1), c=50.0)], reference_date=REF, staleness_days=5
    )
    assert stale.last.coverage_status is CoverageStatus.STALE  # 14d old > 5d
    assert stale.last.value == 50.0
    empty = compute_price_features([], reference_date=REF, staleness_days=5)
    assert empty.last.coverage_status is CoverageStatus.UNKNOWN and empty.last.value is None


def test_close_on_or_before() -> None:
    bars = [_bar(date(2026, 1, 1), c=10.0), _bar(date(2026, 2, 1), c=20.0)]
    assert _close_on_or_before(bars, date(2026, 1, 20)) == 10.0
    assert _close_on_or_before(bars, date(2026, 2, 5)) == 20.0
    assert _close_on_or_before(bars, date(2025, 12, 1)) is None


def test_relative_return() -> None:
    name = [_bar(date(2026, 3, 15), c=100.0), _bar(REF, c=120.0)]  # +20%
    bench = [_bar(date(2026, 3, 15), c=100.0), _bar(REF, c=110.0)]  # +10%
    rel = relative_return(name, bench, reference_date=REF, lookback_days=92)
    assert rel.value == pytest.approx(0.20 - 0.10)  # name beat bench by +10%
    # missing benchmark coverage -> UNKNOWN, never a corrupted number
    assert relative_return(name, [], reference_date=REF, lookback_days=92).coverage_status is (
        CoverageStatus.UNKNOWN
    )


# --- network: real Polygon --------------------------------------------------------------------
@pytest.mark.network
def test_grouped_daily_trading_day() -> None:
    client = PolygonEodClient.from_config()
    bars = client.grouped_daily(date(2026, 6, 12))  # a Friday
    assert len(bars) > 3000  # whole US market
    assert "AAPL" in bars and bars["AAPL"].close > 0


@pytest.mark.network
def test_grouped_daily_weekend_is_empty() -> None:
    client = PolygonEodClient.from_config()
    assert client.grouped_daily(date(2026, 6, 13)) == {}  # Saturday -> non-trading


def test_ingest_prices_per_symbol_is_one_call_each(tmp_path) -> None:
    """(NCNO-class backfill) The per-symbol path (refresh --aggs) issues exactly ONE daily_bars call
    per name and writes its bars — the efficient fix for a NEW name with no history, where
    grouped-daily would be ~250 whole-market calls at the free tier's ~5/min. Deterministic on a
    fake client; the store round-trips the written bars."""
    from vinci.eod.client import RawBar, ingest_prices_per_symbol

    class _FakeClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def daily_bars(self, symbol: str, start: date, end: date):  # type: ignore[no-untyped-def]
            self.calls.append(symbol)
            b = lambda c: RawBar(ticker=symbol, open=1, high=2, low=1, close=c, volume=9)  # noqa: E731
            return [(date(2026, 6, 10), b(1.5)), (date(2026, 6, 11), b(1.6))]

    def _ident(iid: str, sym: str) -> Identity:
        return Identity(internal_id=iid, issuer_id="ISS-X", cik="0000000001", ticker=sym,
                        mic="XNAS", exchange="Nasdaq", eod_symbol=sym, name=sym)

    secs = [_ident("SEC-1-NCNO", "NCNO"), _ident("IDX-IWM", "IWM")]
    client = _FakeClient()
    with Store(tmp_path / "aggs.db") as store:
        for s in secs:
            store.upsert_security(s)
        summary = ingest_prices_per_symbol(
            client, store, secs, start=date(2026, 6, 1), end=date(2026, 6, 30))  # type: ignore[arg-type]
    assert client.calls == ["NCNO", "IWM"]  # ONE call per symbol, in order
    assert summary == {"symbols": 2, "bars_written": 4}
    with Store(tmp_path / "aggs.db") as store:
        hist = store.get_price_history("SEC-1-NCNO")
    assert len(hist) == 2 and hist[0].source == "polygon-aggs"


def test_ingest_prices_per_symbol_fails_loud_on_empty_backfill(tmp_path) -> None:
    """(fail-loud) An OK-but-empty daily_bars (a mis-resolved eod_symbol, or a range outside the
    free-tier window) IS the silent gap this path exists to catch — it must RAISE, never read as a
    0-bar success. The names that DID return bars are still written before the raise (the operator
    re-runs only the failed ones)."""
    from vinci.eod.client import RawBar, ingest_prices_per_symbol

    class _FakeClient:
        def daily_bars(self, symbol: str, start: date, end: date):  # type: ignore[no-untyped-def]
            if symbol == "BADSYM":
                return []  # OK response, no results — the exact failure shape
            b = RawBar(ticker=symbol, open=1, high=2, low=1, close=1.5, volume=9)
            return [(date(2026, 6, 10), b)]

    def _ident(iid: str, sym: str) -> Identity:
        return Identity(internal_id=iid, issuer_id="ISS-X", cik="0000000001", ticker=sym,
                        mic="XNAS", exchange="Nasdaq", eod_symbol=sym, name=sym)

    secs = [_ident("SEC-GOOD", "GOOD"), _ident("SEC-BAD", "BADSYM")]
    with Store(tmp_path / "aggs.db") as store:
        for s in secs:
            store.upsert_security(s)
        with pytest.raises(EodError, match="BADSYM"):
            ingest_prices_per_symbol(
                _FakeClient(), store, secs,  # type: ignore[arg-type]
                start=date(2026, 6, 1), end=date(2026, 6, 30))
        assert len(store.get_price_history("SEC-GOOD")) == 1  # GOOD written before the raise


@pytest.mark.network
def test_ingest_prices_to_store(tmp_path) -> None:
    resolver = EntityResolver.from_config()
    client = PolygonEodClient.from_config()
    secs = [resolver.resolve_ticker(t) for t in ("AAPL", "MSFT")]
    with Store(tmp_path / "eod.db") as store:
        for s in secs:
            store.upsert_security(s)
        summary = ingest_prices(client, store, secs, start=date(2026, 6, 10), end=date(2026, 6, 12))
        assert summary["trading_days"] == 3  # Wed, Thu, Fri
        assert summary["bars_written"] == 6  # 2 names x 3 days
        hist = store.get_price_history("SEC-0000320193-AAPL")
        assert len(hist) == 3 and all(b.close > 0 for b in hist)


# --- (2026-09-23) a session the store already holds is not re-pulled ---------------------------
def _ident_for(sym: str) -> Identity:
    return Identity(internal_id=f"SEC-{sym}", issuer_id=f"ISS-{sym}", cik="0000000002", ticker=sym,
                    mic="XNAS", exchange="Nasdaq", eod_symbol=sym, name=sym)


class _CountingClient:
    """Answers every day with one bar per name, and records which days were asked for."""

    def __init__(self, syms: list[str]) -> None:
        self.syms, self.calls = syms, []

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        self.calls.append(day)
        return {s: RawBar(ticker=s, open=1.0, high=2.0, low=1.0, close=1.5, volume=100.0)
                for s in self.syms}


def _seed(store, syms, day: date) -> None:  # type: ignore[no-untyped-def]
    store.write_prices([PriceBar(internal_id=f"SEC-{s}", bar_date=day, open=1.0, high=2.0, low=1.0,
                                 close=1.5, volume=100.0, source="polygon-grouped") for s in syms])


def test_a_session_the_store_already_holds_is_not_re_pulled(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """THE COST THAT BROKE THE RUN (2026-09-23): the refresh re-pulled its whole 1,825-day window
    every time — 1,304 whole-market calls — because CI builds its store from scratch. On a plan
    serving ~5 requests/min the weekly run could not finish, locally OR in CI.

    ⊕ a fully-held session older than the restatement window is skipped;
    ⊖ a held session INSIDE the window is re-pulled anyway (that is what restates a split);
    ⊖ the LATEST held session it would skip is re-pulled ONCE, as the anchor that detects a split
      since that pull (2026-10-26, `restate_held`) — one call, never the whole held history;
    ⊖ a session holding only a single-name refresh's rows is not "held" — it is re-pulled;
    ⊖ a store that cannot report what it holds re-pulls everything, exactly as before."""
    from vinci.eod.client import RESTATE_WINDOW_DAYS, ingest_prices

    syms = [f"AA{i}" for i in range(10)]
    secs = [_ident_for(s) for s in syms]
    start, end = date(2026, 6, 1), date(2026, 9, 1)
    held_older, held_old, partial_old = date(2026, 6, 9), date(2026, 6, 10), date(2026, 6, 11)
    held_recent = end - timedelta(days=RESTATE_WINDOW_DAYS - 5)          # inside the window
    with Store(tmp_path / "skip.db") as store:
        for s in secs:
            store.upsert_security(s)
        _seed(store, syms, held_older)                # a whole-market day already ingested
        _seed(store, syms, held_old)                  # the latest such day: the anchor
        _seed(store, syms[:1], partial_old)           # what `refresh --aggs` on ONE name leaves
        _seed(store, syms, held_recent)
        client = _CountingClient(syms)
        summary = ingest_prices(client, store, secs, start=start, end=end)  # type: ignore[arg-type]
    assert held_older not in client.calls, "a session the store already holds was re-pulled"
    assert client.calls.count(held_old) == 1, "the anchor was not re-pulled exactly once"
    assert partial_old in client.calls, "a one-name refresh's rows passed for a whole-market day"
    assert held_recent in client.calls, "the restatement window did not re-pull a held session"
    assert summary["days_skipped"] == 1 and summary["anchor"] == held_old.isoformat()
    assert summary["days_fetched"] == len(client.calls) and summary["restated"] == {}

    class _StoreWithoutCounts:                        # an older/foreign store: never trusted
        def __init__(self) -> None:
            self.written = 0

        def write_prices(self, bars) -> int:  # type: ignore[no-untyped-def]
            rows = list(bars)
            self.written += len(rows)
            return len(rows)

    plain = _StoreWithoutCounts()
    client2 = _CountingClient(syms)
    s2 = ingest_prices(client2, plain, secs, start=start, end=end)  # type: ignore[arg-type]
    assert s2["days_skipped"] == 0
    assert held_old in client2.calls and len(client2.calls) == s2["days_fetched"]


def test_a_day_the_universe_holds_is_still_fetched_for_the_benchmark(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The screen ingests the UNIVERSE, then the BENCHMARK, as two calls against one store.

    A day can hold every universe bar and no IWM bar — the universe pull writes only the universe's
    symbols. Counting the whole `prices` table would answer thousands for the benchmark's own
    ingest and skip it forever, so the count is restricted to the ids being ingested."""
    syms = [f"BB{i}" for i in range(10)]
    secs = [_ident_for(s) for s in syms]
    bench = _ident_for("IWM")
    start, end = date(2026, 6, 1), date(2026, 9, 1)
    old = date(2026, 6, 10)
    with Store(tmp_path / "bench.db") as store:
        for s in [*secs, bench]:
            store.upsert_security(s)
        _seed(store, syms, old)                       # the universe's day — no IWM bar in it
        client = _CountingClient(["IWM"])
        summary = ingest_prices(client, store, [bench], start=start, end=end)  # type: ignore[arg-type]
    assert old in client.calls, "the benchmark was skipped on a day only the universe holds"
    assert summary["days_skipped"] == 0


# --- (2026-10-26) a split since the held pull restates the held bars, never splices them --------
# THE DEFECT: the restatement window re-pulled 30 days, and skipped every older held session. After
# a split, the bars it pulled came back on the new basis while the held ones stayed on the old, so
# the series stepped by the split ratio at the pull boundary. Measured in the 2026-10-16 weekly's
# store: IESC, SFBS and BYND at 2026-08-06, and SFBS's G1 PASS rested on it
# (docs/records/2026-10-24-prices-quality-source.md). The held bars cannot be re-pulled (the plan
# serves two years), so the fix restates them by the factor the source applies to a bar it serves.

def _px(day: date) -> float:
    """A close that moves every day (so a step is visible) — synthetic, never a real price."""
    return 100.0 + (day.toordinal() % 7)


def _bar_at(sym: str, day: date, scale: float = 1.0, *, close_only: float = 1.0) -> RawBar:
    p = _px(day) * scale
    return RawBar(ticker=sym, open=p, high=p * 1.01, low=p * 0.99, close=p * close_only,
                  volume=1000.0 / scale)


class _BasisClient:
    """Serves every day on the CURRENT basis: names in ``scale`` have split since the store's pull
    (a 2:1 halves every price and doubles volume — what `adjusted=true` returns afterwards)."""

    def __init__(self, syms: list[str], scale: dict[str, float],
                 close_only: dict[str, float] | None = None) -> None:
        self.syms, self.scale, self.close_only, self.calls = syms, scale, close_only or {}, []

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        self.calls.append(day)
        if day.weekday() >= 5:
            return {}
        return {s: _bar_at(s, day, self.scale.get(s, 1.0), close_only=self.close_only.get(s, 1.0))
                for s in self.syms}


def _hold(store: Store, syms: list[str], days: list[date]) -> None:
    """The store's earlier pull, on the OLD basis (scale 1)."""
    store.write_prices([PriceBar(internal_id=f"SEC-{s}", bar_date=d, open=b.open, high=b.high,
                                 low=b.low, close=b.close, volume=b.volume,
                                 source="polygon-grouped")
                        for d in days for s in syms for b in [_bar_at(s, d)]])


def test_restatement_factor_reads_one_basis_change_and_nothing_else() -> None:
    from vinci.eod.client import RESTATE_TOL, restatement_factor
    d = date(2026, 8, 5)
    held = PriceBar(internal_id="SEC-X", bar_date=d, **{k: getattr(_bar_at("X", d), k) for k in
                    ("open", "high", "low", "close", "volume")}, source="polygon-grouped")
    assert restatement_factor(held, _bar_at("X", d)) is None                  # unchanged
    assert restatement_factor(held, _bar_at("X", d, 0.5)) == pytest.approx(0.5)  # 2-for-1
    assert restatement_factor(held, _bar_at("X", d, 30.0)) == pytest.approx(30.0)  # 1-for-30
    assert restatement_factor(held, _bar_at("X", d, 2 / 3)) == pytest.approx(2 / 3)  # 3-for-2 too
    # a correction to the close alone is not a new basis, however large
    assert restatement_factor(held, _bar_at("X", d, close_only=0.5)) is None
    # inside the band either way: no restatement
    assert restatement_factor(held, _bar_at("X", d, 1 + RESTATE_TOL * 0.8)) is None
    assert restatement_factor(held, _bar_at("X", d, 1 + RESTATE_TOL * 1.2)) is not None


def test_a_split_since_the_held_pull_leaves_no_step(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """⊕ the split name's whole stored series ends on the current basis, with no whole-number
    step anywhere, and the summary names it with its factor;
    ⊖ a name that did not split, and one whose anchor bar changed only in its close (a correction),
    keep every held bar as it was."""
    from vinci.dossier.freshness import whole_number_ratio
    from vinci.eod.client import RESTATE_WINDOW_DAYS, ingest_prices

    syms = ["SPL", "KEEP", "FIX"] + [f"CC{i}" for i in range(7)]
    secs = [_ident_for(s) for s in syms]
    start, end = date(2026, 5, 1), date(2026, 9, 1)
    restate_from = end - timedelta(days=RESTATE_WINDOW_DAYS)
    held_days = [d for d in (start + timedelta(days=i) for i in range(60))
                 if d.weekday() < 5 and d < restate_from]
    client = _BasisClient(syms, {"SPL": 0.5}, close_only={"FIX": 0.97})
    with Store(tmp_path / "split.db") as store:
        for s in secs:
            store.upsert_security(s)
        _hold(store, syms, held_days)
        summary = ingest_prices(client, store, secs, start=start, end=end)  # type: ignore[arg-type]
        spl = store.get_price_history("SEC-SPL")
        keep = store.get_price_history("SEC-KEEP")
        fix = store.get_price_history("SEC-FIX")
    # THE SUBSTANCE FIRST: on the old ingest this is where it fails — a ×0.5 step at the boundary
    assert not any(whole_number_ratio(b.close / a.close)
                   for a, b in zip(spl, spl[1:], strict=False))
    assert all(b.close == pytest.approx(_px(b.bar_date) * 0.5) for b in spl)
    assert summary["anchor"] == held_days[-1].isoformat()
    assert summary["restated"] == {"SPL": [pytest.approx(0.5)]}
    assert all(b.source.endswith("+restated") for b in spl if b.bar_date < held_days[-1])
    assert all(b.close == pytest.approx(_px(b.bar_date)) and b.source == "polygon-grouped"
               for b in keep)
    held_fix = [b for b in fix if b.bar_date < held_days[-1]]
    assert held_fix and all(b.close == pytest.approx(_px(b.bar_date)) for b in held_fix)


def test_restate_held_restates_each_pull_by_its_own_factor(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The REPAIR path, for a store that already holds a splice: two pulls, the older ending on
    b1, the newer on b2. A name split between them (IESC's shape) restates only the older pull; a
    name split after both (IMMP's shape, ×20 after 2026-10-16) restates both, each by its own."""
    from vinci.eod.client import restate_held

    b1, b2 = date(2026, 8, 5), date(2026, 8, 14)
    old = [date(2026, 8, 3), date(2026, 8, 4), b1]
    new = [date(2026, 8, 6), date(2026, 8, 7), b2]
    with Store(tmp_path / "repair.db") as store:
        for s in ("MID", "LATE", "NONE"):
            store.upsert_security(_ident_for(s))
        _hold(store, ["MID", "LATE", "NONE"], old)
        # MID's newer pull is already on the post-split basis (scale 0.5) — the splice
        store.write_prices([PriceBar(internal_id="SEC-MID", bar_date=d, **{
            k: getattr(_bar_at("MID", d, 0.5), k) for k in ("open", "high", "low", "close",
                                                            "volume")}, source="polygon-grouped")
            for d in new])
        _hold(store, ["LATE", "NONE"], new)
        today = {"MID": 0.5, "LATE": 20.0}

        def fetch(day: date) -> dict[str, RawBar]:
            return {s: _bar_at(s, day, today.get(s, 1.0)) for s in ("MID", "LATE", "NONE")}

        found = restate_held(store, fetch, [b2, b1],
                             {s: f"SEC-{s}" for s in ("MID", "LATE", "NONE")})
        hist = {s: store.get_price_history(f"SEC-{s}") for s in ("MID", "LATE", "NONE")}
    assert found == {"SEC-MID": [(b1, pytest.approx(0.5))],
                     "SEC-LATE": [(b1, pytest.approx(20.0)), (b2, pytest.approx(20.0))]}
    for s, scale in (("MID", 0.5), ("LATE", 20.0), ("NONE", 1.0)):
        assert all(b.close == pytest.approx(_px(b.bar_date) * scale) for b in hist[s]), s
        assert all(b.volume == pytest.approx(1000.0 / scale) for b in hist[s]), s


def test_restate_bars_bounds_tags_once_and_refuses_a_bad_factor(tmp_path) -> None:  # type: ignore[no-untyped-def]
    days = [date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5)]
    with Store(tmp_path / "r.db") as store:
        store.upsert_security(_ident_for("X"))
        _hold(store, ["X"], days)
        assert store.restate_bars("SEC-X", 0.5, through=days[1], after=days[0]) == 1
        assert store.restate_bars("SEC-X", 1.0, through=days[1], after=days[0]) == 1
        with pytest.raises(ValueError, match="not positive"):
            store.restate_bars("SEC-X", 0.0, through=days[2])
        got = {b.bar_date: b for b in store.get_price_history("SEC-X")}
        on = store.bars_on(days[1], ["SEC-X", "SEC-MISSING"])
    assert got[days[0]].close == pytest.approx(_px(days[0]))            # `after` is exclusive
    assert got[days[1]].close == pytest.approx(_px(days[1]) * 0.5)      # `through` inclusive
    assert got[days[2]].close == pytest.approx(_px(days[2]))
    assert got[days[1]].source == "polygon-grouped+restated"            # tagged once
    assert set(on) == {"SEC-X"}


def test_restate_prices_command_repairs_a_spliced_store(tmp_path, monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    """The command a store that already holds a splice is repaired with: the boundary given, the
    latest market session added, each pull restated by its own factor — and a boundary after the
    latest market session refused."""
    from vinci import cli
    from vinci.dossier.freshness import whole_number_ratio

    syms = ["SPL"] + [f"CC{i}" for i in range(5)]
    old = [date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5)]
    new = [date(2026, 8, 6), date(2026, 8, 7)]
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    with Store(tmp_path / "data" / "vinci.db") as store:
        for s in syms:
            store.upsert_security(_ident_for(s))
        _hold(store, syms, old)
        _hold(store, syms[1:], new)
        store.write_prices([PriceBar(internal_id="SEC-SPL", bar_date=d, **{
            k: getattr(_bar_at("SPL", d, 0.5), k) for k in ("open", "high", "low", "close",
                                                            "volume")}, source="polygon-grouped")
            for d in new])
    client = _BasisClient(syms, {"SPL": 0.5})
    monkeypatch.setattr(cli.PolygonEodClient, "from_config",
                        classmethod(lambda cls, cfg=None: client))
    assert cli.main(["restate-prices", "--through", "2026-08-05"]) == 0
    out = capsys.readouterr().out
    assert "SPL" in out and "×0.5" in out and "1 name(s) restated" in out
    assert client.calls == [date(2026, 8, 5), date(2026, 8, 7)]     # the latest session added
    with Store(tmp_path / "data" / "vinci.db") as store:
        spl = store.get_price_history("SEC-SPL")
    assert not any(whole_number_ratio(b.close / a.close)
                   for a, b in zip(spl, spl[1:], strict=False))
    assert cli.main(["restate-prices", "--through", "2026-08-10"]) == 1
    assert "after the store's latest market session" in capsys.readouterr().err


def test_a_name_with_no_bar_on_the_anchor_is_checked_at_its_own_last_bar(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """PSTV'S SHAPE (measured 2026-10-26): its held bars end before the anchor session, so the
    anchor never compares it, and Polygon now serves its whole history on a later basis. When its
    bars resume in a refresh, its older held bars must be restated at its OWN last held session —
    ⊕ no step, the name in the summary; ⊖ a name that got no new bars costs no call."""
    from vinci.dossier.freshness import whole_number_ratio
    from vinci.eod.client import RESTATE_WINDOW_DAYS, ingest_prices

    syms = ["GONE", "BACK"] + [f"CC{i}" for i in range(8)]
    secs = [_ident_for(s) for s in syms]
    start, end = date(2026, 5, 1), date(2026, 9, 1)
    restate_from = end - timedelta(days=RESTATE_WINDOW_DAYS)
    held_days = [d for d in (start + timedelta(days=i) for i in range(60))
                 if d.weekday() < 5 and d < restate_from]
    early = held_days[:10]                         # BACK and GONE stopped trading after these
    client = _BasisClient([s for s in syms if s != "GONE"], {"BACK": 1 / 25})
    with Store(tmp_path / "late.db") as store:
        for s in secs:
            store.upsert_security(s)
        _hold(store, [f"CC{i}" for i in range(8)], held_days)
        _hold(store, ["BACK", "GONE"], early)
        summary = ingest_prices(client, store, secs, start=start, end=end)  # type: ignore[arg-type]
        back = store.get_price_history("SEC-BACK")
        gone = store.get_price_history("SEC-GONE")
    assert not any(whole_number_ratio(b.close / a.close)
                   for a, b in zip(back, back[1:], strict=False))
    assert all(b.close == pytest.approx(_px(b.bar_date) / 25) for b in back)
    assert summary["restated"] == {"BACK": [pytest.approx(1 / 25)]}
    assert client.calls.count(early[-1]) == 1      # BACK's own last held session, fetched once
    assert all(b.source == "polygon-grouped" for b in gone)   # no new bars: never asked about
