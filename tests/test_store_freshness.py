"""THE PRICE STORE HAD NO FRESHNESS MEASUREMENT AT ALL.

IT's 6% cap divergence was not a code defect — it was **the refresh command not having been run**,
and nothing measured that. After the staleness split, two sources still carry no as-of: the price
store and the Financials workbook. This closes the first.

NO CALENDAR (operator). The store is measured AGAINST ITSELF: a name trailing the fleet means its
fetch failed or it was halted, and the whole fleet trailing today means the refresh was not run.
The two have different remedies, so they are reported separately.

THE TOLERANCE IS DERIVED, not chosen. Across 7,225 consecutive-bar pairs in the committed store the
observed gaps are 1d 78.0%, 2d 1.2%, 3d 18.0%, 4d 2.9% and nothing beyond — so a lag over 4 days is
not a weekend or a holiday. Same trick as the prior-bar as-of resolution: read the trading calendar
off the data instead of encoding one.

LIVE INSTANCE THE DAY IT WAS WRITTEN: IWM and MDY — the BENCHMARKS, which feed `rel_ret_vs_market`
and therefore a screen gate — trailed the fleet by 8 days while all eleven dossier names sat at 0.
"""
from __future__ import annotations

import datetime as dt
import pathlib

import pytest

from vinci.dossier.freshness import (
    MAX_STORE_LAG_DAYS,
    fleet_lag,
    stale_names,
    store_freshness_note,
    store_lag,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 7, 30)


# --- the store against itself ---------------------------------------------------------------


def test_a_name_behind_the_fleet_is_found_without_a_calendar() -> None:
    """THE RED. A failed per-name fetch leaves that name behind while everything else advances —
    visible with no clock and no holiday table."""
    latest = {"AORT": "2026-07-29", "SMPL": "2026-07-29", "IWM": "2026-07-21"}
    assert store_lag(latest) == {"AORT": 0, "SMPL": 0, "IWM": 8}
    assert stale_names(latest) == {"IWM": 8}


def test_a_weekend_or_holiday_gap_is_not_stale() -> None:
    """The control that keeps this from firing constantly. The store's own gaps run to 4 days, so
    a name 4 days behind is inside normal market structure and must stay quiet."""
    for lag_days in range(MAX_STORE_LAG_DAYS + 1):
        d = (dt.date.fromisoformat("2026-07-29") - dt.timedelta(days=lag_days)).isoformat()
        assert stale_names({"A": "2026-07-29", "B": d}) == {}, lag_days
    over = (dt.date.fromisoformat("2026-07-29")
            - dt.timedelta(days=MAX_STORE_LAG_DAYS + 1)).isoformat()
    assert stale_names({"A": "2026-07-29", "B": over}) == {"B": MAX_STORE_LAG_DAYS + 1}


def test_the_tolerance_matches_the_stores_own_observed_gaps() -> None:
    """The constant is DERIVED. If the committed store ever exhibits a gap larger than the
    tolerance, the tolerance is wrong — and this reds rather than the guard firing spuriously on
    every name after a long holiday."""
    db = ROOT / "data" / "vinci.db"
    if not db.exists():
        pytest.skip("no local store in this worktree")
    import sqlite3

    c = sqlite3.connect(db)
    worst = 0
    for (iid,) in c.execute("select distinct internal_id from prices"):
        ds = [dt.date.fromisoformat(r[0]) for r in c.execute(
            "select bar_date from prices where internal_id=? order by bar_date", (iid,))]
        for a, b in zip(ds, ds[1:], strict=False):
            worst = max(worst, (b - a).days)
    if worst == 0:
        pytest.skip("store has no consecutive bars to measure")
    assert worst <= MAX_STORE_LAG_DAYS, (
        f"the store exhibits a {worst}d gap but the tolerance is {MAX_STORE_LAG_DAYS}d — every "
        "name would read stale after that gap. Re-derive the constant from the distribution.")


# --- the fleet against today ------------------------------------------------------------------


def test_the_fleet_lag_keys_on_age_not_on_a_bar_for_today() -> None:
    """OPERATOR RULING, recorded in STATE. Assembly runs in Indian daytime against a prior US
    close, so "no bar for today" is the NORMAL case — a guard refusing on it would refuse every run
    before the US close. Silence at one day; reportable only past what the store's gaps explain."""
    assert fleet_lag({"A": "2026-07-29"}, TODAY) == 1
    assert store_freshness_note({"A": "2026-07-29"}, TODAY) is None
    behind = (TODAY - dt.timedelta(days=MAX_STORE_LAG_DAYS + 3)).isoformat()
    note = store_freshness_note({"A": behind}, TODAY)
    assert note is not None and "refresh has not been run" in note


def test_the_two_findings_are_reported_separately() -> None:
    """They have different remedies — refresh ONE name, versus run the refresh at all — so
    collapsing them into a single "store is stale" would send a reader to the wrong action."""
    behind = (TODAY - dt.timedelta(days=10)).isoformat()
    note = store_freshness_note({"A": TODAY.isoformat(), "B": behind}, TODAY)
    assert note is not None and "names behind the fleet: B" in note
    assert "refresh has not been run" not in note, "the fleet is current; only B is behind"


def test_an_empty_store_says_so_rather_than_passing() -> None:
    """An empty store is a KNOWN worktree state here, and it must not read as 'nothing stale'.
    That is the guard-that-cannot-fire class: no bars, no lag, silent pass."""
    assert store_lag({}) == {} and fleet_lag({}, TODAY) is None
    note = store_freshness_note({}, TODAY)
    assert note is not None and "EMPTY" in note


def test_the_note_never_raises() -> None:
    """It is a caveat, not a gate — same contract as `consensus_note`. Nothing it is handed may
    raise, or it becomes a build blocker by accident."""
    cases = ({}, {"A": "2026-07-29"}, {"A": "2020-01-01"},
             {"A": "2026-07-29", "B": "2020-01-01"})
    for latest in cases:
        store_freshness_note(latest, TODAY)


# --- the corpus --------------------------------------------------------------------------------


def test_the_committed_store_is_measured_and_reports_its_laggards() -> None:
    """Non-vacuous: runs against the real store and asserts the measurement produces an answer.
    On the day this was written it flagged IWM and MDY — the BENCHMARKS feeding
    `rel_ret_vs_market`, hence a screen gate — at 8 days behind, which nothing had ever measured."""
    db = ROOT / "data" / "vinci.db"
    if not db.exists():
        pytest.skip("no local store in this worktree")
    import sqlite3

    c = sqlite3.connect(db)
    latest = {r[0].split("-")[-1]: r[1] for r in c.execute(
        "select internal_id, max(bar_date) from prices group by internal_id")}
    if not latest:
        pytest.skip("store has no bars")
    lags = store_lag(latest)
    assert lags and min(lags.values()) == 0, "no name sits at the fleet frontier — impossible"
    assert all(v >= 0 for v in lags.values()), "a negative lag means the frontier is wrong"


def test_the_dossier_names_are_the_ones_that_must_be_current() -> None:
    """The guard's PURPOSE, pinned to the names it protects: every committed dossier's ticker must
    be inside the tolerance, or its next build carries a price nobody refreshed. Benchmarks and
    non-dossier names are reported by the note but do not gate a dossier build."""
    db = ROOT / "data" / "vinci.db"
    if not db.exists() or not (ROOT / "data" / "dossiers").is_dir():
        pytest.skip("no local store or dossiers in this worktree")
    import sqlite3

    c = sqlite3.connect(db)
    latest = {r[0].split("-")[-1]: r[1] for r in c.execute(
        "select internal_id, max(bar_date) from prices group by internal_id")}
    if not latest:
        pytest.skip("store has no bars")
    doss = {p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json")}
    stale = {n: lag for n, lag in stale_names(latest).items() if n in doss}
    assert not stale, (
        f"committed dossier names are behind the fleet: {stale} — their next build would carry a "
        "price nobody refreshed. Run: vinci refresh <tickers> --start … --end … --aggs")
