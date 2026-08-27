"""A CASHTAG IS NOT ALWAYS A SYMBOL — the rename splice, and the guards that keep it honest.

The bug this pins: `$SQ` bars stopped dead at 2025-01-17, the day Block became XYZ, because the
fetcher passed the cashtag straight to Polygon and Polygon serves each symbol only for the span it
was live. Nothing said so. The window ran to 2026-01-09; every `$SQ` post in the last twelve months
of it silently lost its price, and `tickers.json` had carried the answer — `{"SQ": "XYZ"}` — in a
map no code read.

WHY THE GUARDS RAISE. A splice of the wrong pair does not produce missing data, it produces a
CONFIDENT WRONG ANSWER: one clean, continuous price history stitched out of two different
companies, indistinguishable from a real one forever after. So each guard fails loud.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.calls.bars import _splice_rename, fetch_account_bars
from vinci.eod.client import RawBar


def _bar(c: float, o: float | None = None) -> RawBar:
    return RawBar(ticker="X", open=o if o is not None else c, high=c, low=c, close=c, volume=1e6)


def _series(start: str, closes: list[float], *, opens: list[float] | None = None
            ) -> list[tuple[date, RawBar]]:
    """Consecutive weekday-ish bars from `start`, one per day."""
    d0 = date.fromisoformat(start)
    return [(date.fromordinal(d0.toordinal() + i), _bar(c, (opens or closes)[i]))
            for i, c in enumerate(closes)]


# --- the real shape: SQ ends, XYZ picks up four days later --------------------------------------

OLD = _series("2025-01-15", [84.0, 85.0, 86.96])                     # ends Fri 2025-01-17
NEW = _series("2025-01-21", [89.5, 90.0], opens=[88.06, 89.6])       # starts Tue 2025-01-21


def test_the_two_halves_join_into_one_continuous_series() -> None:
    got = _splice_rename(OLD, NEW, cashtag="SQ", successor="XYZ")
    assert [d.isoformat() for d, _ in got] == [
        "2025-01-15", "2025-01-16", "2025-01-17", "2025-01-21", "2025-01-22"]
    assert got[2][1].close == 86.96 and got[3][1].open == 88.06, "the seam lost a bar's values"


def test_a_window_on_one_side_of_the_rename_needs_no_seam() -> None:
    assert _splice_rename([], NEW, cashtag="SQ", successor="XYZ") == NEW, "opens after the rename"
    assert _splice_rename(OLD, [], cashtag="SQ", successor="XYZ") == OLD, "closes before it"
    assert _splice_rename([], [], cashtag="SQ", successor="XYZ") == []


def test_where_both_symbols_serve_a_date_the_cashtag_wins() -> None:
    """Not observed for SQ→XYZ, but well-defined if Polygon ever back-fills the successor: the
    overlap is dropped from the successor, never merged."""
    overlapping = _series("2025-01-17", [86.96, 89.5], opens=[86.0, 88.06])
    got = _splice_rename(OLD, overlapping, cashtag="SQ", successor="XYZ")
    assert len(got) == 4, "the shared date was taken twice"
    assert got[2][0].isoformat() == "2025-01-17" and got[2][1].open == 86.96, \
        "the successor's copy of the shared date overwrote the cashtag's"


def test_a_successor_entirely_inside_the_old_span_adds_nothing() -> None:
    assert _splice_rename(OLD, OLD[:2], cashtag="SQ", successor="XYZ") == OLD


# --- the guards: each of these would fabricate a price history ----------------------------------

def test_a_months_long_hole_is_not_a_rename() -> None:
    late = _series("2025-06-02", [89.5, 90.0])
    with pytest.raises(ValueError, match="hands over at the next session"):
        _splice_rename(OLD, late, cashtag="SQ", successor="XYZ")


def test_a_split_sized_step_at_the_seam_is_not_a_rename() -> None:
    doubled = _series("2025-01-21", [174.0, 175.0], opens=[173.9, 174.5])
    with pytest.raises(ValueError, match="split or the wrong symbol"):
        _splice_rename(OLD, doubled, cashtag="SQ", successor="XYZ")


def test_two_symbols_that_disagree_where_they_overlap_are_not_one_security() -> None:
    disagreeing = _series("2025-01-17", [40.0, 41.0])
    with pytest.raises(ValueError, match="not the same security"):
        _splice_rename(OLD, disagreeing, cashtag="SQ", successor="XYZ")


# --- end to end through the fetcher -------------------------------------------------------------

class _FakeClient:
    """Serves each symbol only for the span it was live — exactly what Polygon does."""

    def __init__(self) -> None:
        self.asked: list[str] = []

    def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
        self.asked.append(symbol)
        return {"SQ": OLD, "XYZ": NEW, "TWTR": OLD, "AAA": OLD}.get(symbol, [])


@pytest.fixture()
def acct(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = tmp_path / "calls" / "acct"
    (d / "bars").mkdir(parents=True)
    (d / "tickers.json").write_text(json.dumps({
        "note": "t", "renamed": {"SQ": "XYZ", "TWTR": None},
        "tickers": [{"ticker": t, "mentions": 1, "first_mention": "2025-01-15",
                     "last_mention": "2025-01-22", "fetch_from": "2024-10-12",
                     "fetch_to": "2026-01-22"} for t in ("SQ", "TWTR", "AAA")]}))
    monkeypatch.setattr("vinci.calls.bars.account_dir", lambda h, **k: d)
    return d


def _written(d: Path, sym: str) -> dict[str, Any]:
    return json.loads((d / "bars" / f"{sym}.json").read_text())  # type: ignore[no-any-return]


def test_the_renamed_cashtag_is_fetched_under_both_symbols_and_says_so(acct: Path) -> None:
    cli = _FakeClient()
    counts = fetch_account_bars("acct", client=cli, only={"SQ", "TWTR", "AAA"})

    assert counts["SQ"] == 5, "the successor's half never reached the file"
    sq = _written(acct, "SQ")
    assert sq["bars"][-1][0] == "2025-01-22", "the series still stops at the rename"
    assert sq["renamed_to"] == "XYZ" and sq["spliced_at"] == "2025-01-21", "no provenance"
    assert "XYZ" in cli.asked, "the successor was never requested"


def test_a_delisted_cashtag_with_no_successor_is_left_alone(acct: Path) -> None:
    cli = _FakeClient()
    fetch_account_bars("acct", client=cli, only={"TWTR"})
    tw = _written(acct, "TWTR")
    assert len(tw["bars"]) == 3, "a null successor must not extend the series"
    assert "renamed_to" not in tw, "a null successor is not provenance to record"


def test_an_unmapped_ticker_costs_exactly_one_call(acct: Path) -> None:
    cli = _FakeClient()
    fetch_account_bars("acct", client=cli, only={"AAA"})
    assert [s for s in cli.asked if s != "SPY"] == ["AAA"], "an extra call for an unmapped ticker"
    assert "renamed_to" not in _written(acct, "AAA")
