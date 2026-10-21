"""The desk opens on the weekly scan, never on the price refresh the weekly job runs after it.

Observed 2026-10-21 on the first weekly run with data (Actions run 39565710165): the job's
`market` step started after its scan, so it opened a week of its own — "21 Oct 2026 — manual runs,
no weekly scan yet", 0 articles, 0 theses — and the desk (and the app's published copy) opened on
it, the scan's week pushed back to "previous". A price refresh analyses nothing: alone after a
scan it joins that scan's week. Manual RESEARCH after a scan is still a week of its own, and says
it follows a scan instead of claiming there was none.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from tests.theme_intelligence_support import (
    CALM_AS_OF,
    JPM_AS_OF,
    ingest_calm,
    ingest_jpm,
    make_pipeline,
)
from vinci.theme_intelligence import desk as dk
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.publish import publish
from vinci.theme_intelligence.report import report_runs
from vinci.theme_intelligence.schemas import RunStatus, WeeklyRun


def _scan(pipe: Pipeline) -> WeeklyRun:
    """The weekly scan, as the job runs it: one analysed article inside its window."""
    pipe.start_run("scan", as_of=JPM_AS_OF, window_from=JPM_AS_OF - dt.timedelta(days=9),
                   window_to=JPM_AS_OF)
    ingest_jpm(pipe)
    return pipe.finish_run(RunStatus.SUCCEEDED)


def _run(pipe: Pipeline, mode: str, status: RunStatus = RunStatus.SUCCEEDED, *,
         as_of: dt.date = JPM_AS_OF) -> WeeklyRun:
    """A run that analyses nothing — the price refresh, or a manual run that failed."""
    pipe.start_run(mode, as_of=as_of)
    return pipe.finish_run(status)


def test_the_published_desk_opens_on_the_scan_not_on_its_price_refresh(tmp_path: Path) -> None:
    """END TO END, through `publish` — the surface the failure was seen on: the app's copy names
    the scan's week and counts its article, never an empty "no weekly scan yet" week."""
    pipe = make_pipeline(tmp_path)
    scan = _scan(pipe)
    market = _run(pipe, "market")
    (week,) = dk.desk_weeks(pipe.store, scan)
    out = tmp_path / "published"
    publish(pipe.store, market.run_id, out)
    manifest = json.loads((out / "index.json").read_text())
    assert manifest["run_id"] == market.run_id
    assert manifest["week"] == week.label and week.label.startswith("Week of ")
    home = (out / "site" / "index.html").read_text()
    assert f"<h1>{week.label}</h1>" in home
    assert "1 article read" in home and "no weekly scan yet" not in home


def test_a_price_refresh_joins_the_scan_week_it_follows(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    scan = _scan(pipe)
    market = _run(pipe, "market")
    weeks = dk.desk_weeks(pipe.store, market)
    assert [w.scanned for w in weeks] == [True]
    assert {scan.run_id, market.run_id} <= weeks[-1].run_ids


def test_research_after_a_scan_is_its_own_week_and_says_it_follows_one(tmp_path: Path) -> None:
    """NEGATIVE: a manual ARTICLE after the scan is the week in progress — labelled as following a
    scan, never "no weekly scan yet". The price refresh after it is still the SCAN's: one rule."""
    pipe = make_pipeline(tmp_path)
    scan = _scan(pipe)
    pipe.start_run("article", as_of=CALM_AS_OF)
    ingest_calm(pipe)
    article = pipe.finish_run(RunStatus.SUCCEEDED)
    market = _run(pipe, "market")
    weeks = dk.desk_weeks(pipe.store, market)
    assert [w.scanned for w in weeks] == [True, False]
    assert weeks[-1].run_ids == {article.run_id}
    assert {scan.run_id, market.run_id} <= weeks[0].run_ids
    assert weeks[-1].label.endswith("— manual runs since the last weekly scan")


def test_a_failed_manual_run_after_the_scan_keeps_its_week(tmp_path: Path) -> None:
    """NEGATIVE: a manual run that FAILED after the scan is listed in the week in progress, so a
    price refresh beside it does not fold that week away."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    failed = _run(pipe, "article", RunStatus.FAILED)
    market = _run(pipe, "market")
    weeks = dk.desk_weeks(pipe.store, market)
    assert [w.scanned for w in weeks] == [True, False]
    assert [r.run_id for r in weeks[-1].failed] == [failed.run_id]


def test_manual_runs_before_any_scan_still_say_there_was_none(tmp_path: Path) -> None:
    """NEGATIVE: with no scan at all (the pilot's registry until 2026-10-21) the label is
    unchanged — and a price refresh alone still makes a week, since there is no scan to join."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    pipe.finish_run(RunStatus.SUCCEEDED)
    market = _run(pipe, "market")
    weeks = dk.desk_weeks(pipe.store, market)
    assert [(w.scanned, w.after_scan) for w in weeks] == [(False, False)]
    assert weeks[-1].label.endswith("— manual runs, no weekly scan yet")
    alone = make_pipeline(tmp_path / "alone")
    only = _run(alone, "market")
    assert [w.scanned for w in dk.desk_weeks(alone.store, only)] == [False]


# --- the review of #759 (2026-10-21): one rule for a price refresh, wherever weeks are made ------

def test_a_failed_refresh_does_not_reopen_an_empty_week(tmp_path: Path) -> None:
    """The weekly job's market step failed (continue-on-error records it FAILED) and the operator
    re-ran it: the failed refresh is listed as failed in the SCAN's week — it neither opens a week
    nor stops the re-run joining the scan's."""
    pipe = make_pipeline(tmp_path)
    scan = _scan(pipe)
    broke = _run(pipe, "market", RunStatus.FAILED)
    rerun = _run(pipe, "market")
    weeks = dk.desk_weeks(pipe.store, rerun)
    assert [w.scanned for w in weeks] == [True]
    assert {scan.run_id, rerun.run_id} <= weeks[-1].run_ids
    assert [r.run_id for r in weeks[-1].failed] == [broke.run_id]


def test_a_refresh_is_never_taken_into_the_next_scans_week(tmp_path: Path) -> None:
    """A refresh belongs to the scan it follows — in `report_runs` too: the NEXT scan's report
    must not count it (it took in every manual mode, the refresh included), so no run moves
    between weeks when the next scan lands."""
    pipe = make_pipeline(tmp_path)
    first = _scan(pipe)
    market = _run(pipe, "market")
    broke = _run(pipe, "market", RunStatus.FAILED)
    pipe.start_run("scan", as_of=JPM_AS_OF + dt.timedelta(days=7),
                   window_from=JPM_AS_OF - dt.timedelta(days=2),
                   window_to=JPM_AS_OF + dt.timedelta(days=7))
    second = pipe.finish_run(RunStatus.SUCCEEDED)
    assert market.run_id not in {r.run_id for r in report_runs(pipe.store, second)}
    weeks = dk.desk_weeks(pipe.store, second)
    assert [w.scanned for w in weeks] == [True, True]
    assert {first.run_id, market.run_id} <= weeks[0].run_ids
    assert market.run_id not in weeks[1].run_ids
    # a failed refresh between the scans is listed ONCE, in the week it belongs to
    assert [r.run_id for r in weeks[0].failed] == [broke.run_id] and not weeks[1].failed
    # and a refresh after the second scan is the second scan's, never the first's
    later = _run(pipe, "market", as_of=JPM_AS_OF + dt.timedelta(days=7))
    weeks = dk.desk_weeks(pipe.store, later)
    assert later.run_id in weeks[1].run_ids and later.run_id not in weeks[0].run_ids


def test_prices_newer_than_the_scan_week_are_said(tmp_path: Path) -> None:
    """A refresh as of a later day joins the scan's week, and the label says the prices are newer
    than the week it names. NEGATIVE: a refresh inside the week adds nothing to the label."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    same = _run(pipe, "market")
    (week,) = dk.desk_weeks(pipe.store, same)
    assert week.label.startswith("Week of ") and "prices as of" not in week.label
    later = _run(pipe, "market", as_of=JPM_AS_OF + dt.timedelta(days=7))
    (week,) = dk.desk_weeks(pipe.store, later)
    assert week.label.endswith(" · prices as of 16 Feb 2026"), week.label


def test_a_failed_refresh_rendered_on_its_own_is_listed_as_failed(tmp_path: Path) -> None:
    """Rendering the failed refresh itself: it is in the scan week's FAILED runs, never among the
    runs the week reports as done."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    broke = _run(pipe, "market", RunStatus.FAILED)
    (week,) = dk.desk_weeks(pipe.store, broke)
    assert broke.run_id not in week.run_ids
    assert [r.run_id for r in week.failed] == [broke.run_id]


# --- the review of #760 (2026-10-21): research RE-READ after a scan is that scan's week ----------

def _replay(pipe: Pipeline, as_of: dt.date, *, analyse: bool = True) -> WeeklyRun:
    """A replay run, started as `state pull` starts one: an `ingest` run naming the runs it
    re-reads (`replay_of`), dated at their original as-of."""
    run = pipe.start_run("ingest", as_of=as_of)
    run.replay_of = ("R-20261013T155116Z-ingest",)
    if analyse:
        ingest_calm(pipe)
    return pipe.finish_run(RunStatus.SUCCEEDED)


def test_research_re_read_after_the_scan_joins_its_week_end_to_end(tmp_path: Path) -> None:
    """The one-registry merge replayed the pilot's documents after the 21 Oct scan, dated 13–14
    Oct: the desk opened on "13–14 Oct — manual runs since the last weekly scan", a 'latest' week
    dated BEFORE the scan it followed, the scan's Research Now one step back. A replay dated in
    the scan's window is that week's research, re-read later — and the published desk says so."""
    pipe = make_pipeline(tmp_path)
    scan = _scan(pipe)
    replay = _replay(pipe, JPM_AS_OF - dt.timedelta(days=3))
    market = _run(pipe, "market")
    (week,) = dk.desk_weeks(pipe.store, market)
    assert week.scanned and {scan.run_id, replay.run_id, market.run_id} <= week.run_ids
    assert week.label.startswith("Week of ")
    assert "· with research re-read after the scan" in week.label
    out = tmp_path / "published"
    manifest = publish(pipe.store, market.run_id, out)
    assert manifest["week"] == week.label
    home = (out / "site" / "index.html").read_text()
    assert f"<h1>{week.label}</h1>" in home and "2 articles read" in home


def test_a_replay_is_never_the_next_scans_research(tmp_path: Path) -> None:
    """Overlapping windows: a replay dated inside the first scan's window AND the second's is the
    first's alone — `report_runs` of the second never takes it, so no run is counted twice."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    replay = _replay(pipe, JPM_AS_OF - dt.timedelta(days=1))
    pipe.start_run("scan", as_of=JPM_AS_OF + dt.timedelta(days=7),
                   window_from=JPM_AS_OF - dt.timedelta(days=2),
                   window_to=JPM_AS_OF + dt.timedelta(days=7))
    second = pipe.finish_run(RunStatus.SUCCEEDED)
    assert replay.run_id not in {r.run_id for r in report_runs(pipe.store, second)}
    weeks = dk.desk_weeks(pipe.store, second)
    assert replay.run_id in weeks[0].run_ids and replay.run_id not in weeks[1].run_ids


def test_a_replay_dated_before_the_window_is_no_weeks_research(tmp_path: Path) -> None:
    """NEGATIVE: a replay as of a month earlier is not the scan's week (as `report_runs` has always
    held — "a replay as of July is not this week's research") and opens no week of its own."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    old = _replay(pipe, JPM_AS_OF - dt.timedelta(days=30), analyse=False)
    weeks = dk.desk_weeks(pipe.store, old)
    assert [w.scanned for w in weeks] == [True]
    assert old.run_id not in weeks[0].run_ids and "re-read" not in weeks[0].label


def test_a_replay_dated_after_the_scan_is_the_week_in_progress(tmp_path: Path) -> None:
    """NEGATIVE: a replay dated after the scan's window is new research for the next week — the
    week in progress, as any manual run after a scan."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    later = _replay(pipe, JPM_AS_OF + dt.timedelta(days=4), analyse=False)
    weeks = dk.desk_weeks(pipe.store, later)
    assert [w.scanned for w in weeks] == [True, False]
    assert weeks[-1].run_ids == {later.run_id}
    assert weeks[-1].label.endswith("— manual runs since the last weekly scan")


def test_a_replay_dated_on_the_scans_day_is_the_next_weeks(tmp_path: Path) -> None:
    """NEGATIVE: a replay dated the scan's own day is research that arrived after the scan ran (a
    laptop's upload, replayed by `state pull`) — the week in progress, then the next scan's
    report (`test_the_weekly_report_counts_the_replay_once_never_the_carried_runs`)."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    same_day = _replay(pipe, JPM_AS_OF, analyse=False)
    weeks = dk.desk_weeks(pipe.store, same_day)
    assert [w.scanned for w in weeks] == [True, False]
    assert weeks[-1].run_ids == {same_day.run_id} and "re-read" not in weeks[0].label
