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
from vinci.theme_intelligence.schemas import RunStatus, WeeklyRun


def _scan(pipe: Pipeline) -> WeeklyRun:
    """The weekly scan, as the job runs it: one analysed article inside its window."""
    pipe.start_run("scan", as_of=JPM_AS_OF, window_from=JPM_AS_OF - dt.timedelta(days=9),
                   window_to=JPM_AS_OF)
    ingest_jpm(pipe)
    return pipe.finish_run(RunStatus.SUCCEEDED)


def _run(pipe: Pipeline, mode: str, status: RunStatus = RunStatus.SUCCEEDED) -> WeeklyRun:
    """A run that analyses nothing — the price refresh, or a manual run that failed."""
    pipe.start_run(mode, as_of=JPM_AS_OF)
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
    """NEGATIVE: a manual ARTICLE after the scan is the week in progress (the price refresh after
    it rides along) — labelled as following a scan, never "no weekly scan yet"."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    pipe.start_run("article", as_of=CALM_AS_OF)
    ingest_calm(pipe)
    article = pipe.finish_run(RunStatus.SUCCEEDED)
    market = _run(pipe, "market")
    weeks = dk.desk_weeks(pipe.store, market)
    assert [w.scanned for w in weeks] == [True, False]
    assert {article.run_id, market.run_id} <= weeks[-1].run_ids
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
