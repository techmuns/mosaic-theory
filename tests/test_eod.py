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
