"""The scoring conventions, pinned — they are pre-registered, so drift here is a silent restatement.

Each convention below was chosen before any result was seen. A change to one does not break a
build; it quietly moves every number the tape has ever produced. That is what these pins protect.
The look-ahead pin is the load-bearing one: entering at the POST-DAY CLOSE instead of the next
day's open hands the author the rest of the session he was already posting into, and manufactures
alpha out of his own timing.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date, timedelta

import pytest

from vinci.calls.score import DEFAULT_HORIZON_DAYS, Bar, is_scoreable, score_call

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "calls" / "pdicarlotrader"


def _bars(start: date, closes: list[float], *, spread: float = 1.0) -> list[Bar]:
    """One bar per weekday. open == prior close so entry/exit are unambiguous to reason about."""
    out: list[Bar] = []
    d = start
    prev = closes[0]
    for c in closes:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        out.append((d, prev, max(prev, c) + spread, min(prev, c) - spread, c, 1_000.0))
        prev = c
        d += timedelta(days=1)
    return out


def _call(**kw: object) -> object:
    base: dict[str, object] = {
        "tweet_id": "1", "ticker": "X", "posted": date(2025, 1, 6), "bias": "bullish",
        "target": None, "target_type": "none", "horizon_lo": None, "horizon_hi": None, "bench": []}
    base.update(kw)
    return score_call(**base)  # type: ignore[arg-type]


def test_entry_is_the_next_days_open_never_the_post_day_close() -> None:
    """THE LOOK-AHEAD PIN. The post lands on the 6th; the 6th's close is 200 and the 7th opens at
    that 200. Entry must be the 7th's OPEN — reading the 6th's close as entry would let the author
    'enter' after the move he posted into."""
    bars = _bars(date(2025, 1, 6), [200.0] + [210.0] * 80)
    r = _call(bars=bars, horizon_hi=5)
    assert r.entry_date == date(2025, 1, 7), "entry bar is not the next trading day"
    assert r.entry == pytest.approx(200.0)
    assert r.entry_date > r.posted, "entry must strictly follow the post"


def test_a_horizon_that_has_not_elapsed_is_open_and_carries_no_return() -> None:
    """An unfinished call must not contribute a number to anything."""
    r = _call(bars=_bars(date(2025, 1, 6), [100.0] * 10), horizon_hi=63)
    assert r.status == "OPEN"
    assert r.ret is None and r.excess is None and r.direction_correct is None
    assert r.entry is not None, "an OPEN call still knows what it would have entered at"


def test_the_default_horizon_is_flagged_wherever_it_is_applied() -> None:
    """Where the author stated no horizon a 63-day default applies — and must never be silent, or
    a machine-chosen window reads as the author's own."""
    bars = _bars(date(2025, 1, 6), [100.0] * 200)
    assumed = _call(bars=bars)
    assert assumed.horizon_days == DEFAULT_HORIZON_DAYS and assumed.horizon_assumed is True
    stated = _call(bars=bars, horizon_hi=21)
    assert stated.horizon_days == 21 and stated.horizon_assumed is False
    # the HIGH end wins when both are stated
    assert _call(bars=bars, horizon_lo=10, horizon_hi=30).horizon_days == 30


def test_returns_are_signed_by_the_stated_bias() -> None:
    """A bearish call on a stock that falls is a WIN. Unsigned returns would score it a loss."""
    down = _bars(date(2025, 1, 6), [100.0] + [80.0] * 40)
    bear = _call(bars=down, bias="bearish", horizon_hi=5)
    bull = _call(bars=down, bias="bullish", horizon_hi=5)
    assert bear.ret is not None and bear.ret > 0 and bear.direction_correct is True
    assert bull.ret is not None and bull.ret < 0 and bull.direction_correct is False
    assert bear.ret == pytest.approx(-bull.ret)


def test_only_a_stated_direction_is_scoreable() -> None:
    """`none` / `mixed` carry no direction to sign a return by; treating them as bullish would
    invent a stance the author did not take. tracker.py filters them out and so does this."""
    assert is_scoreable("bullish") and is_scoreable("bearish")
    assert not any(is_scoreable(b) for b in ("none", "mixed", "neutral", None, ""))


def test_the_benchmark_leg_ends_on_the_common_last_bar() -> None:
    """vinci/eod/features.py learned this the expensive way: a benchmark that stops early while
    the name runs on is ASYMMETRIC, not merely stale, and the error's sign is set by whichever way
    the market moved in the gap."""
    bars = _bars(date(2025, 1, 6), [100.0] * 40)
    full = _bars(date(2025, 1, 6), [100.0] * 40)
    short = full[:8]                       # benchmark frontier stops well before the horizon end
    r = _call(bars=bars, bench=short, horizon_hi=20)
    assert r.status == "CLOSED" and r.bench_ret is not None
    assert r.excess == pytest.approx(r.ret - r.bench_ret)
    # a benchmark with no usable overlap yields no excess at all — never a zero standing in for one
    assert _call(bars=bars, bench=[], horizon_hi=20).excess is None


def test_the_target_is_touched_on_the_path_not_only_at_the_exit() -> None:
    """'Did he reach it' is a question about the whole window: a target tagged intraday and given
    back by the horizon still counts as touched, and MFE/MAE record the path either way."""
    spike = _bars(date(2025, 1, 6), [100.0, 100.0, 100.0, 145.0, 100.0] + [100.0] * 30)
    r = _call(bars=spike, target="140", target_type="point", horizon_hi=10)
    assert r.target_hit is True, "a target touched mid-window was missed"
    assert r.ret is not None and r.ret == pytest.approx(0.0, abs=1e-9), "exit is still flat"
    assert r.mfe is not None and r.mfe > 0.4 and r.mae is not None and r.mae <= 0


def test_an_absent_or_unpriced_series_fails_loud_rather_than_scoring_zero() -> None:
    assert _call(bars=[]).status == "NO_PRICE_DATA"
    late = _bars(date(2024, 1, 1), [100.0] * 5)          # every bar precedes the post
    assert _call(bars=late).status == "NO_ENTRY_BAR"


@pytest.mark.skipif(not (CORPUS / "results.jsonl").is_file(), reason="no scored corpus")
def test_the_committed_results_obey_every_convention_at_once() -> None:
    """E2E over the real scored corpus — the conventions hold on 3,889 rows, not just fixtures."""
    rows = [json.loads(x) for x in (CORPUS / "results.jsonl").read_text().splitlines() if x.strip()]
    assert len(rows) > 3000, f"scored corpus shrank to {len(rows)} rows"
    for r in rows:
        assert r["bias"] in ("bullish", "bearish"), f"{r['tweet_id']}: undirected row was scored"
        if r["entry_date"]:
            assert r["entry_date"] > r["posted"], f"{r['tweet_id']}: entry on or before the post"
        if r["status"] == "OPEN":
            assert r["ret"] is None, f"{r['tweet_id']}: an OPEN call carries a return"
        if r["status"] == "CLOSED":
            assert r["exit_date"] > r["entry_date"]
            assert (r["ret"] > 0) == r["direction_correct"]
            assert r["mfe"] >= r["mae"], f"{r['tweet_id']}: MFE below MAE"
            if r["excess"] is not None:
                assert r["excess"] == pytest.approx(r["ret"] - r["bench_ret"], abs=1e-9)
    closed = [r for r in rows if r["status"] == "CLOSED"]
    assert closed and any(r["horizon_assumed"] for r in rows), "no assumed horizon to check"
    assert any(not r["horizon_assumed"] for r in rows), "no stated horizon to check"
