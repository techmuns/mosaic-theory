"""`relative_return` RAN EACH LEG TO ITS OWN LAST BAR — an asymmetric comparison, not a stale one.

THE ROOT DEFECT behind the benchmark incident. `_close_on_or_before(bars, reference_date)` was
called PER SERIES, so a stale benchmark contributed a return that stopped early while every name's
ran to the reference date. That is not "the screen is N days behind" — it is a DIRECTIONAL bias
whose sign is set by whichever way the market moved in the missing days, applied identically to
every name, i.e. a systematic mis-ranking.

MEASURED ON THE REAL RUN. The 2026-07-27 screen had IWM's frontier at 07-21 while names ran to
07-24+. The market fell 1.22% in the gap, so `bench_ret` was overstated, every `rel` was understated
by ~1.22pp, and FOUR of 318 candidates passed G2 only because of it — CABA, GO, NOMD, TROX. None
reached a dossier; NOMD ranked 227 of 275. A market DECLINE admits names that fell with it.

THE FIX makes stale input produce a SHORTER window rather than a skewed one, and stamps what was
actually used — the field feeding the gate had been claiming `as_of=reference_date` even when its
data stopped days earlier.
"""
from __future__ import annotations

import datetime as dt

from vinci.eod.features import relative_return
from vinci.schemas.market import PriceBar

REF = dt.date(2026, 7, 27)
LOOKBACK = 70          # start = 2026-05-18


def _bars(pairs: list[tuple[str, float]]) -> list[PriceBar]:
    return [PriceBar(internal_id="X", bar_date=dt.date.fromisoformat(d), open=c, high=c, low=c,
                     close=c, volume=1.0, source="t") for d, c in pairs]


# The shape of the real incident: the name has a bar the benchmark does not.
NAME = _bars([("2026-05-01", 100.0), ("2026-07-21", 80.0), ("2026-07-24", 79.0)])
BENCH_STALE = _bars([("2026-05-01", 100.0), ("2026-07-21", 101.0)])
BENCH_FRESH = _bars([("2026-05-01", 100.0), ("2026-07-21", 101.0), ("2026-07-24", 99.0)])


def test_a_stale_benchmark_shortens_the_window_it_does_not_skew_the_comparison() -> None:
    """THE RED. Old behaviour compared the name at 07-24 (79 → −21%) against the benchmark at
    07-21 (101 → +1%), giving −22.0% — a full point of skew from the asymmetry alone.

    Both legs now end on the COMMON last bar (07-21): −20% − 1% = −21.0%. The difference is
    exactly the market move the benchmark was missing, which is the bias this removes."""
    stale = relative_return(NAME, BENCH_STALE, reference_date=REF, lookback_days=LOOKBACK)
    assert stale.value is not None
    assert abs(stale.value - (-0.21)) < 1e-9, stale.value
    # the asymmetric answer the old code produced, pinned so a regression is unmistakable
    assert abs(stale.value - (-0.22)) > 1e-6, "the legs are still ending on different bars"


def test_a_fresh_benchmark_uses_the_full_window() -> None:
    """The control: when both sides reach the same bar there is nothing to shorten, and the value
    differs from the stale case only by the extra session."""
    fresh = relative_return(NAME, BENCH_FRESH, reference_date=REF, lookback_days=LOOKBACK)
    assert fresh.value is not None and abs(fresh.value - (-0.20)) < 1e-9, fresh.value
    assert fresh.as_of == dt.date(2026, 7, 24)


def test_the_common_end_is_the_earlier_frontier_whichever_side_is_behind() -> None:
    """Symmetry: the rule is `min(frontiers)`, not "clamp to the benchmark". A name that is itself
    behind must shorten the window the same way — otherwise a halted name gets a free comparison
    against a market that kept trading."""
    name_behind = _bars([("2026-05-01", 100.0), ("2026-07-21", 80.0)])
    r = relative_return(name_behind, BENCH_FRESH, reference_date=REF, lookback_days=LOOKBACK)
    assert r.as_of == dt.date(2026, 7, 21), "the earlier frontier must win regardless of side"


def test_the_window_is_stamped_with_both_frontiers() -> None:
    """THE STAMP RULE, fifth instance. The screen's benchmark frontier was never recorded — the
    2026-07-27 bound had to INFER it, after the store-side evidence had been refreshed away. It was
    recoverable only because the committed `rel` values survived, which was luck.

    `as_of` is now the effective END, and `note` carries the window plus each side's own frontier,
    so a later recompute can reconstruct what the screen actually saw."""
    stale = relative_return(NAME, BENCH_STALE, reference_date=REF, lookback_days=LOOKBACK)
    assert stale.as_of == dt.date(2026, 7, 21), "as_of must be the effective end, not the reference"
    note = stale.note or ""
    assert "2026-05-18→2026-07-21" in note, note
    assert "name frontier 2026-07-24" in note and "benchmark frontier 2026-07-21" in note, note
    assert "6d short of the 2026-07-27 reference" in note, note


def test_as_of_no_longer_claims_the_reference_date_when_the_data_stops_earlier() -> None:
    """The specific stamp defect: the old value stamped `reference_date` unconditionally, so a
    gate input asserted a currency its data did not have. Pinned because that field feeds G2."""
    stale = relative_return(NAME, BENCH_STALE, reference_date=REF, lookback_days=LOOKBACK)
    assert stale.as_of != REF
    assert stale.as_of is not None and stale.as_of < REF


def test_an_empty_side_is_unknown_not_a_number() -> None:
    """Fail-loud, unchanged: no bars on either side yields UNKNOWN rather than a comparison against
    nothing. Both directions, because the frontier lookup is new code on both."""
    empty_name = relative_return([], BENCH_FRESH, reference_date=REF, lookback_days=LOOKBACK)
    assert empty_name.value is None
    assert relative_return(NAME, [], reference_date=REF, lookback_days=LOOKBACK).value is None


def test_bars_after_the_reference_date_are_never_used() -> None:
    """The lookahead guard, which the frontier rewrite must not break: a bar dated after the
    reference date may not set the frontier, or a rerun would silently use future data."""
    future = _bars([("2026-05-01", 100.0), ("2026-07-24", 99.0), ("2026-08-15", 50.0)])
    r = relative_return(NAME, future, reference_date=REF, lookback_days=LOOKBACK)
    assert r.as_of == dt.date(2026, 7, 24), "a post-reference bar leaked into the frontier"
