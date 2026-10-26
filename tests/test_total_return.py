"""TOTAL RETURN, the primary basis since 2026-10-26 (operator ruling B) — scoring, the follow
basket and the monitor, names and benchmarks alike, with price return printed beside it.

THE DEFECT: `scoring.metrics.total_return` was `exit ÷ entry − 1` on Polygon closes, which
`adjusted=true` restates for splits and never for dividends — a price return under a total return's
name, feeding every spread the fund would score from VRRM's first outcome (2026-12-14).

Pinned on SYNTHETIC values in Tiingo's served row shape (no real price or dividend is copied here):
the coverage rule that makes a missing record UNKNOWN rather than zero, the arithmetic, the price
figures beside it, and every place an unreadable dividend must fail loud instead of falling back.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.dividend_support import no_dividends
from vinci.eod import dividends as divs
from vinci.eod.dividends import DividendsUnknownError, ex_date_yields, growth
from vinci.netcache import HttpError
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.scoring import harness as harness_mod
from vinci.scoring import score_ledger
from vinci.scoring.baseline import Basket, basket_return
from vinci.scoring.metrics import RETURN_BASIS as SCORING_BASIS
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]


def _weekdays(a: date, b: date) -> list[date]:
    out, d = [], a
    while d <= b:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _row(d: date, close: float = 50.0, cash: float = 0.0) -> dict[str, Any]:
    """A Tiingo daily row in the served shape (field set measured 2026-10-24)."""
    return {"date": f"{d.isoformat()}T00:00:00.000Z", "close": close, "high": close,
            "low": close, "open": close, "volume": 1.0, "adjClose": close, "adjHigh": close,
            "adjLow": close, "adjOpen": close, "adjVolume": 1.0, "divCash": cash,
            "splitFactor": 1.0}


A, B = date(2026, 1, 5), date(2026, 3, 6)          # a Monday and a Friday
DAYS = _weekdays(A, B)
EX = date(2026, 2, 11)


# --- the reader ---------------------------------------------------------------------------------


def test_yields_are_cash_over_the_ex_dates_close_inside_the_window() -> None:
    rows = [_row(d, 50.0, 0.5 if d == EX else 0.0) for d in DAYS]
    assert ex_date_yields(rows, A, B) == [(EX, pytest.approx(0.01))]
    assert growth(ex_date_yields(rows, A, B)) == pytest.approx(1.01)
    # the window is (start, end]: an ex-date ON the entry session was paid before the position
    assert ex_date_yields(rows, EX, B) == []
    # ON the exit session it is inside
    assert ex_date_yields(rows, A, EX) == [(EX, pytest.approx(0.01))]
    # a covered window with no dividend reads [] — Tiingo said "none", which is a reading
    assert ex_date_yields([_row(d) for d in DAYS], A, B) == []


@pytest.mark.parametrize("rows, why", [
    ([_row(d) for d in DAYS[1:]], "do not cover"),                 # no row ON the entry session
    ([_row(d) for d in DAYS[:-1]], "do not cover"),                # none ON the exit session
    ([_row(d) for d in DAYS if not (date(2026, 2, 2) <= d <= date(2026, 2, 6))], "hole"),
    ([], "do not cover"),
    ([{**_row(A), "divCash": None}, *[_row(d) for d in DAYS[1:]]], "not readable"),
    ([{**_row(A), "close": 0}, *[_row(d) for d in DAYS[1:]]], "not readable"),
    ([{"close": 1.0, "divCash": 0.0}, *[_row(d) for d in DAYS]], "unreadable"),
])
def test_a_window_tiingo_does_not_cover_is_unknown_never_zero(rows: list[dict[str, Any]],
                                                             why: str) -> None:
    with pytest.raises(DividendsUnknownError, match=why):
        ex_date_yields(rows, A, B, symbol="X")


def test_the_longest_market_closure_is_not_a_hole() -> None:
    """A Friday to the Tuesday after a Monday holiday is four days: still one unbroken record."""
    fri, tue = date(2026, 2, 13), date(2026, 2, 17)
    rows = [_row(d) for d in DAYS if d != date(2026, 2, 16)]
    assert (tue - fri).days == divs.MAX_SESSION_GAP_DAYS
    assert ex_date_yields(rows, A, B) == []


class _Client:
    def __init__(self, rows: dict[str, list[dict[str, Any]]]) -> None:
        self.rows, self.calls = rows, []

    def daily_rows(self, symbol: str, *, start: date, end: date) -> list[dict[str, Any]]:
        self.calls.append(symbol)
        if symbol not in self.rows:
            raise HttpError("Non-retryable 404 from https://api.tiingo.com/x: none")
        return self.rows[symbol]


def test_the_tiingo_source_reads_each_symbol_once_and_fails_loud() -> None:
    rows = [_row(d, 50.0, 0.5 if d == EX else 0.0) for d in DAYS]
    client = _Client({"PAY": rows, "BRK-B": rows})
    src = divs.tiingo_dividends(client, start=A, end=B)  # type: ignore[arg-type]
    assert src("PAY", A, B) == [(EX, pytest.approx(0.01))]
    assert src("PAY", EX, B) == []
    assert src("BRK.B", A, B)                          # a share class is asked for hyphenated
    assert client.calls == ["PAY", "BRK-B"]            # once per symbol, whatever the windows
    with pytest.raises(DividendsUnknownError, match="request failed"):
        src("GONE", A, B)
    with pytest.raises(DividendsUnknownError, match="outside the span"):
        src("PAY", A - timedelta(days=1), B)


def test_without_a_key_every_window_fails_loud(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    src = divs.default_dividends(start=A, end=B)
    with pytest.raises(DividendsUnknownError, match="no TIINGO_API_KEY"):
        src("PAY", A, B)


# --- the scoring harness -------------------------------------------------------------------------

ENTRY, HORIZON = date(2025, 1, 15), date(2025, 4, 15)


def _bars(iid: str, a: float, b: float) -> list[PriceBar]:
    return [PriceBar(internal_id=iid, bar_date=d, open=c, high=c + 1, low=c - 1, close=c,
                     volume=1e6, source="t") for d, c in ((ENTRY, a), (HORIZON, b))]


def _entry(ticker: str, verdict: Verdict) -> LedgerEntry:
    return LedgerEntry(
        entry_id=f"V-{ticker}", candidate_id=f"{ticker}-screen2", internal_id=f"SEC-{ticker}",
        ticker=ticker, verdict=verdict, twin_call="t", entry_price=100.0,
        entry_price_as_of=ENTRY, thesis="t", kill_criteria="k", horizon_days=90,
        confidence=Confidence.MEDIUM, decided_at=datetime.combine(ENTRY, datetime.min.time()))


def _yields(table: dict[str, float]) -> divs.DividendSource:
    """Each symbol paid one dividend of the given yield inside every window it is asked about."""
    def src(symbol: str, a: date, b: date) -> list[tuple[date, float]]:
        if symbol not in table:
            raise DividendsUnknownError(f"{symbol}: synthetic unknown")
        return [(b, table[symbol])] if table[symbol] else []
    return src


def _store(tmp_path: Path) -> Store:
    tmp_path.mkdir(parents=True, exist_ok=True)
    store = Store(tmp_path / "s.db")
    store.write_prices(_bars("IDX-IWM", 100.0, 105.0))
    store.write_prices(_bars("SEC-PAY", 100.0, 110.0))
    store.write_prices(_bars("SEC-NIL", 100.0, 90.0))
    store.append_ledger(_entry("PAY", Verdict.BUY))
    store.append_ledger(_entry("NIL", Verdict.AVOID_TERMINAL))
    return store


def test_every_leg_is_a_total_return_with_price_beside_it(tmp_path: Path) -> None:
    """⊕ the name and its benchmark carry their own dividends; the price figures ride beside;
    ⊖ the spread reads the total return, never the price one."""
    with _store(tmp_path) as store:
        scores, report = score_ledger(store, as_of=HORIZON,
                                      dividends=_yields({"PAY": 0.02, "NIL": 0.0, "IWM": 0.01}))
    s = {x.ticker: x for x in scores}
    assert s["PAY"].name_return == pytest.approx(1.10 * 1.02 - 1)
    assert s["PAY"].name_price_return == pytest.approx(0.10)
    assert s["PAY"].bench_return == pytest.approx(1.05 * 1.01 - 1)
    assert s["PAY"].bench_price_return == pytest.approx(0.05)
    assert s["NIL"].name_return == pytest.approx(-0.10) == s["NIL"].name_price_return
    assert report.buy_avoid_spread == pytest.approx((1.10 * 1.02 - 1) - (-0.10))
    assert report.buy_avoid_spread_price == pytest.approx(0.10 - (-0.10))
    md = report.to_markdown()
    assert SCORING_BASIS in md and "on price return: BUY−AVOID +20.0%" in md


def test_a_resolved_row_with_unknown_dividends_stops_the_score(tmp_path: Path) -> None:
    with _store(tmp_path) as store, pytest.raises(harness_mod.TotalReturnUnknownError,
                                                  match="V-PAY.*never scored on price return"):
        score_ledger(store, as_of=HORIZON, dividends=_yields({"NIL": 0.0, "IWM": 0.0}))
    # the BENCHMARK's dividends are as load-bearing as the name's
    with _store(tmp_path / "b") as store, pytest.raises(harness_mod.TotalReturnUnknownError):
        score_ledger(store, as_of=HORIZON, dividends=_yields({"PAY": 0.0, "NIL": 0.0}))


def test_an_interim_row_with_unknown_dividends_is_pending_not_priced(tmp_path: Path) -> None:
    mid = ENTRY + timedelta(days=30)
    with Store(tmp_path / "s.db") as store:
        store.write_prices(_bars("IDX-IWM", 100.0, 105.0))
        store.write_prices(_bars("SEC-PAY", 100.0, 110.0))
        store.append_ledger(_entry("PAY", Verdict.BUY))
        scores, report = score_ledger(store, as_of=mid, dividends=_yields({}))
    assert scores == [] and report.n_pending == 1


def test_the_beta_regression_carries_the_dividends_too(tmp_path: Path) -> None:
    """The β/α printed beside a total-return spread reads daily TOTAL returns: an ex-date's
    dividend enters both series on that day."""
    days = _weekdays(ENTRY, HORIZON)
    with Store(tmp_path / "s.db") as store:
        for iid, drift in (("IDX-IWM", 0.001), ("SEC-PAY", 0.002)):
            store.write_prices([PriceBar(internal_id=iid, bar_date=d, open=1.0, high=999.0,
                                         low=0.001, close=100.0 * (1 + drift) ** i * (1 + (i % 3)
                                         * 0.01), volume=1.0, source="t")
                                for i, d in enumerate(days)])
        store.append_ledger(_entry("PAY", Verdict.BUY))
        ex = days[20]

        def src(symbol: str, a: date, b: date) -> list[tuple[date, float]]:
            return [(ex, 0.05)] if symbol == "PAY" else []

        _s, with_div = score_ledger(store, as_of=HORIZON, dividends=src)
        _s, none = score_ledger(store, as_of=HORIZON, dividends=no_dividends)
    assert with_div.beta is not None and none.beta is not None
    assert with_div.beta != pytest.approx(none.beta)


# --- the follow basket ---------------------------------------------------------------------------


def test_the_basket_is_a_total_return_and_refuses_an_unknown_member() -> None:
    from vinci.followed import FollowRecord
    recs = tuple(FollowRecord(ticker=t, sleeve="quality", since=date(2020, 1, 1))
                 for t in ("PAY", "NIL"))
    basket = Basket(sleeve="quality", records=recs,
                    internal_ids={"PAY": "SEC-PAY", "NIL": "SEC-NIL"})
    bars = {"PAY": _bars("SEC-PAY", 100.0, 110.0), "NIL": _bars("SEC-NIL", 100.0, 90.0)}
    got, note, _m = basket_return(basket, bars, ENTRY, HORIZON,
                                  dividends=_yields({"PAY": 0.02, "NIL": 0.0}))
    assert note is None and got == pytest.approx(((1.10 * 1.02 - 1) + (-0.10)) / 2)
    got, note, _m = basket_return(basket, bars, ENTRY, HORIZON, dividends=_yields({"PAY": 0.0}))
    assert got is None and note is not None and "dividends unknown" in note and "NIL" in note


# --- the monitor ---------------------------------------------------------------------------------


def test_a_monitor_row_is_total_return_with_price_beside_it() -> None:
    from vinci import monitor as mon
    r = mon.position_row(ticker="X", verdict="BUY", sector=None, entry_price=50.0,
                         entry_date=date(2026, 1, 1), current_price=55.0,
                         current_date=date(2026, 2, 1), benchmark="SPY", benchmark_entry=200.0,
                         benchmark_now=204.0, horizon_days=180, position_growth=1.01,
                         benchmark_growth=1.005)
    assert r.position_return == pytest.approx(1.10 * 1.01 - 1)
    assert r.benchmark_return == pytest.approx(1.02 * 1.005 - 1)
    assert r.excess == pytest.approx(r.position_return - r.benchmark_return)
    assert (r.position_price_return, r.benchmark_price_return, r.excess_price) == (
        pytest.approx(0.10), pytest.approx(0.02), pytest.approx(0.08))
    with pytest.raises(ValueError, match="growth must be > 0"):
        mon.position_row(ticker="X", verdict="BUY", sector=None, entry_price=50.0,
                         entry_date=date(2026, 1, 1), current_price=55.0,
                         current_date=date(2026, 2, 1), benchmark="SPY", benchmark_entry=200.0,
                         benchmark_now=204.0, horizon_days=180, position_growth=0.0,
                         benchmark_growth=1.0)
    spread = mon.compute_spread([r, mon.position_row(
        ticker="Y", verdict="AVOID_TERMINAL", sector=None, entry_price=10.0,
        entry_date=date(2026, 1, 1), current_price=9.0, current_date=date(2026, 2, 1),
        benchmark="SPY", benchmark_entry=200.0, benchmark_now=204.0, horizon_days=180,
        position_growth=1.0, benchmark_growth=1.005)])
    assert spread.spread_price == pytest.approx(0.08 - (-0.10 - 0.02))
    assert spread.spread != pytest.approx(spread.spread_price)


def test_one_snapshot_holds_one_basis() -> None:
    """⊕ a total-return day carries price beside every row; ⊖ a day that mixes is refused both
    ways; ⊕ every committed day — all price return — still loads, and says so."""
    from vinci import monitor as mon
    total = mon.position_row(ticker="X", verdict="BUY", sector=None, entry_price=1.0,
                             entry_date=date(2026, 1, 1), current_price=1.1,
                             current_date=date(2026, 2, 1), benchmark="IWM", benchmark_entry=1.0,
                             benchmark_now=1.0, horizon_days=180, position_growth=1.0,
                             benchmark_growth=1.0)
    legacy = total.model_copy(update={"position_price_return": None, "benchmark_price_return":
                                      None, "excess_price": None})
    spread = mon.compute_spread([total])
    day = mon.MonitorSnapshot(as_of=date(2026, 2, 1), rows=[total], spread=spread,
                              return_basis="total", price_basis=mon.RETURN_BASIS)
    assert "PX-EXC%" in mon.render_table(day) and "on PRICE return" in mon.render_table(day)
    with pytest.raises(ValueError, match="price-return snapshot carrying total-return rows"):
        mon.MonitorSnapshot(as_of=date(2026, 2, 1), rows=[total], spread=spread)
    with pytest.raises(ValueError, match="lack the price figures"):
        mon.MonitorSnapshot(as_of=date(2026, 2, 1), rows=[legacy], spread=spread,
                            return_basis="total")
    for p in sorted((ROOT / "data" / "monitor").glob("20*.json")):
        snap = mon.MonitorSnapshot.model_validate(json.loads(p.read_text()))
        assert snap.return_basis == "price" and snap.price_basis == mon.PRICE_RETURN_BASIS, p.name
        assert "PX-EXC%" not in mon.render_table(snap)


def test_the_monitor_command_writes_a_total_return_day(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """END TO END through the real command over the real committed ledger and assignments:
    the written day declares total return and carries price beside every row; a leg that pays
    a dividend reads a total return above its price return; and a leg whose dividends cannot be
    read stops the run with nothing written."""
    from tests.test_monitor_ref_date_bound import _wire, _written
    from vinci import cli
    from vinci import monitor as mon
    _wire(tmp_path, monkeypatch, [])
    monkeypatch.setattr(cli, "default_dividends", lambda **_kw: _yields(
        {"GOOGL": 0.004, "IT": 0.0, "SMPL": 0.0, "VRRM": 0.0, "SPY": 0.006, "MDY": 0.006,
         "IWM": 0.006}))
    scratch = tmp_path / "scratch"
    import argparse
    assert cli._cmd_monitor(argparse.Namespace(ref="2026-10-23", out=str(scratch))) == 0
    day = _written(scratch / "data/monitor")
    assert day["return_basis"] == "total" and day["price_basis"] == mon.RETURN_BASIS
    rows = {r["ticker"]: r for r in day["rows"]}
    assert all(r["position_price_return"] is not None for r in day["rows"])
    assert rows["GOOGL"]["position_return"] > rows["GOOGL"]["position_price_return"]
    assert rows["IT"]["position_return"] == pytest.approx(rows["IT"]["position_price_return"])
    assert day["spread"]["spread_price"] is not None

    monkeypatch.setattr(cli, "default_dividends", lambda **_kw: _yields({"GOOGL": 0.0}))
    scratch2 = tmp_path / "scratch2"
    with pytest.raises(RuntimeError, match="dividends UNKNOWN.*refusing to mark"):
        cli._cmd_monitor(argparse.Namespace(ref="2026-10-23", out=str(scratch2)))
    assert not (scratch2 / "data" / "monitor").exists() or not any(
        p.name.startswith("2026") for p in (scratch2 / "data" / "monitor").iterdir())
