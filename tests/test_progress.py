"""Tests for progress reporting on the long batch loops (``vinci.progress`` + its wiring).

Three behaviours are pinned: (1) the reporter's cadence + rate/ETA arithmetic (pure, injected clock,
no real time); (2) ``ingest_prices`` emits ``EOD`` progress through an opt-in callback; (3)
``screen_universe`` threads the same callback so both its EOD ingest and its name loop report. All
non-network — fake EOD/EDGAR clients drive the loops deterministically.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from vinci.eod.client import RawBar, ingest_prices
from vinci.progress import ProgressReporter, stderr_reporter
from vinci.schemas.data_record import Identity
from vinci.schemas.envelope import DataField, SourceTier
from vinci.screens import screen_universe
from vinci.store import Store

REF = date(2026, 6, 12)


class _Clock:
    """A controllable monotonic clock so rate/ETA are deterministic without real time."""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _ident(ticker: str, cik: str) -> Identity:
    return Identity(
        internal_id=f"SEC-{cik}-{ticker}", issuer_id=f"ISS-{cik}", cik=cik, ticker=ticker,
        mic="XNYS", exchange="NYSE", eod_symbol=ticker, name=f"{ticker} Inc.",
    )


# --- ProgressReporter: cadence + arithmetic ---------------------------------------------------
def test_reporter_format_rate_and_eta() -> None:
    """At 25/100 done in 5s: rate = 25/5min = 300/min, ETA = 75 left / 5-per-sec = 15s."""
    clock = _Clock()
    msgs: list[str] = []
    reporter = ProgressReporter("EOD", 100, emit=msgs.append, step=25, now=clock)
    clock.t = 5.0
    reporter.tick(25)
    assert msgs == ["EOD 25/100 · 300/min · ETA 15s"]


def test_reporter_emits_exactly_first_step_and_final() -> None:
    """ONLY the first, every step-th, and the final item emit — intermediate ticks are suppressed.

    Asserting the EXACT set (not ``any(...)``) is what actually defends the throttle: an
    emit-on-every-tick regression still satisfies substring checks but fails this exact-equality
    assert. The ``done/total`` token is clock-independent, so no injected clock is needed here.
    """
    msgs: list[str] = []
    reporter = ProgressReporter("screen", 30, emit=msgs.append, step=10)
    for i in range(1, 31):
        reporter.tick(i)
    assert [m.split()[1] for m in msgs] == ["1/30", "10/30", "20/30", "30/30"]


def test_reporter_silent_when_emit_is_none() -> None:
    """The library default (emit=None) produces nothing and never raises."""
    reporter = ProgressReporter("x", 5, emit=None)
    for i in range(1, 6):
        reporter.tick(i)  # no sink → no output, no error


def test_reporter_suffix_is_appended() -> None:
    msgs: list[str] = []
    clock = _Clock()  # stays at 0.0 → elapsed 0 → rate 0/min, ETA 0s (no real-time flakiness)
    ProgressReporter("EOD", 1, emit=msgs.append, now=clock).tick(1, suffix="42 bars")
    assert msgs == ["EOD 1/1 · 0/min · ETA 0s · 42 bars"]


def test_reporter_first_line_has_no_garbage_rate_on_tiny_elapsed() -> None:
    """A sub-second first sample must NOT explode the rate (the screen reporter ticks at once)."""
    clock = _Clock()
    msgs: list[str] = []
    reporter = ProgressReporter("screen", 600, emit=msgs.append, now=clock)
    clock.t = 0.001  # microseconds of elapsed, as on the real clock's first tick
    reporter.tick(1)
    assert msgs == ["screen 1/600 · 0/min · ETA 0s"]  # honest "just started", not 36000000/min


def test_stderr_reporter_writes_to_stderr_not_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """The production sink defends the 'stdout stays clean (parsable summaries)' rule."""
    stderr_reporter("EOD 5/10 · 30/min · ETA 1m00s")
    out, err = capsys.readouterr()
    assert out == ""  # nothing on stdout, which carries the run summary
    assert "EOD 5/10 · 30/min · ETA 1m00s" in err


# --- ingest_prices wires the callback ---------------------------------------------------------
class _FakeEod:
    """Returns one non-empty bar per day for a single ticker (no network)."""

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        return {"AAA": RawBar(ticker="AAA", open=1.0, high=2.0, low=0.5, close=1.5, volume=1e6)}


def test_ingest_prices_reports_progress(tmp_path: Path) -> None:
    sec = _ident("AAA", "0000000001")
    msgs: list[str] = []
    with Store(tmp_path / "p.db") as store:
        store.upsert_security(sec)
        # Mon..Fri 2026-06-01..05 → 5 weekday trading days
        ingest_prices(
            _FakeEod(), store, [sec],
            start=date(2026, 6, 1), end=date(2026, 6, 5), progress=msgs.append,
        )
    assert msgs, "progress callback should have been invoked"
    assert all(m.startswith("EOD ") for m in msgs)
    assert msgs[0].startswith("EOD 1/5")   # announced on the first day
    assert msgs[-1].startswith("EOD 5/5")  # and on the final day


def test_ingest_prices_silent_without_callback(tmp_path: Path) -> None:
    """No callback → no behavioural change (the default path the rest of the suite relies on)."""
    sec = _ident("AAA", "0000000001")
    with Store(tmp_path / "p.db") as store:
        store.upsert_security(sec)
        summary = ingest_prices(
            _FakeEod(), store, [sec], start=date(2026, 6, 1), end=date(2026, 6, 5)
        )
    assert summary["trading_days"] == 5  # behaviour unchanged when progress is omitted


class _FakeEodHoliday:
    """Empty (non-trading) on day 1, then populated — exercises the skip-path tick branch."""

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        if day == date(2026, 6, 1):
            return {}  # holiday/weekend → grouped_daily returns no rows
        return {"AAA": RawBar(ticker="AAA", open=1.0, high=2.0, low=0.5, close=1.5, volume=1e6)}


def test_ingest_prices_reports_on_a_skipped_day(tmp_path: Path) -> None:
    """A non-trading day must still tick — else a holiday stretch looks hung (what this prevents).

    Day 1 is empty, so the ``EOD 1/5`` announce line can only appear via the skip-path tick; without
    it the first emit would be the final ``EOD 5/5``. Pinning ``msgs[0]`` thus guards that branch.
    """
    sec = _ident("AAA", "0000000001")
    msgs: list[str] = []
    with Store(tmp_path / "p.db") as store:
        store.upsert_security(sec)
        ingest_prices(
            _FakeEodHoliday(), store, [sec],
            start=date(2026, 6, 1), end=date(2026, 6, 5), progress=msgs.append,
        )
    assert msgs[0] == "EOD 1/5 · 0/min · ETA 0s · 0 bars"  # skipped day still announced, 0 bars


# --- screen_universe threads the callback to both its ingest and its name loop ----------------
class _FakeEodFlat:
    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        out: dict[str, RawBar] = {}
        for t in ("AAA", "IWM"):
            out[t] = RawBar(ticker=t, open=100.0, high=101.0, low=99.0, close=100.0, volume=1e6)
        return out


class _FakeEdgar:
    def fundamental_snapshot(self, cik: object) -> object:  # pragma: no cover - flat won't reach
        raise AssertionError("flat name must not trigger an EDGAR fetch")

    def companyfacts(self, cik: object) -> dict[str, object]:  # pragma: no cover
        return {}


def _seed_one_name_universe(store: Store, sec: Identity) -> None:
    store.upsert_security(sec)
    cap = DataField.present(1e9, as_of=REF, source="DERIVED", tier=SourceTier.DERIVED)
    store.record_universe(as_of=REF, internal_id=sec.internal_id, in_universe=True, market_cap=cap)


def test_screen_universe_threads_progress(tmp_path: Path) -> None:
    sec = _ident("AAA", "0000000001")
    msgs: list[str] = []
    with Store(tmp_path / "u.db") as store:
        _seed_one_name_universe(store, sec)
        screen_universe(
            store, _FakeEodFlat(), _FakeEdgar(),
            reference_date=REF, lookback_days=400, staleness_days=5, progress=msgs.append,
        )
    assert any(m.startswith("EOD ") for m in msgs), "nested ingest should report"
    screen_lines = [m for m in msgs if m.startswith("screen ")]
    assert screen_lines, "the name loop should report"
    assert all("enriched" in m for m in screen_lines), "screen line shows the enriched count"


def test_screen_universe_silent_by_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Default progress=None emits NOTHING to either stream — the path other tests rely on."""
    sec = _ident("AAA", "0000000001")
    with Store(tmp_path / "u.db") as store:
        _seed_one_name_universe(store, sec)
        screen_universe(
            store, _FakeEodFlat(), _FakeEdgar(),
            reference_date=REF, lookback_days=400, staleness_days=5,  # progress omitted
        )
    out, err = capsys.readouterr()
    assert out == "" and err == ""  # a non-None default would flood every other test's streams
