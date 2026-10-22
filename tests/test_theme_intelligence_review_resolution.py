"""A reviewer's resolution of a card-review finding — append-only, never a verification
(follow-up B of the research desk record, 2026-10-13; built 2026-10-21).

Before: a review WARNING closed only through an analyst correction or a re-read. A reviewer who
read a finding and judged it immaterial had no way to say so, so it stayed open on the card, the
desk's Review screen and the weekly report for good ("58 open findings, 39 affecting an action",
the live desk on 2026-10-21).

Now (resolve.py): `review dismiss --finding KEY --reviewer NAME --reason TEXT` records who, when
and why, as a run of its own; `review reopen` reverses it; every row is kept. A dismissal closes
the finding as an OPEN item and nothing else:
  * the line keeps its label cap (at most SOURCE OPINION) — accepting a warning never makes
    unsupported evidence valid;
  * a WITHHELD line, and a line changed since its review (NOT RE-REVIEWED), are never dismissible;
  * the dismissal binds to the finding as it stands: carried onto an unreviewed version on the
    same words it holds; a NEW review's finding is open again;
  * a page rendered as of an earlier run never shows a later dismissal;
  * no research-action rule reads it; a `state pull` carries it; `qa` re-checks it.

Every review answer comes from an OFFLINE fake (no network, no paid call); the articles are
SYNTHETIC (tests/theme_intelligence_stress.py) on the reserved `.test` domain.
"""

from __future__ import annotations

import json
import random
import re
import sqlite3
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.test_theme_intelligence_review_carry import SAID, FakeReviewer, _current, _run
from tests.theme_intelligence_stress import END
from tests.theme_intelligence_support import make_pipeline
from vinci.theme_intelligence import state
from vinci.theme_intelligence.__main__ import main
from vinci.theme_intelligence.cards import _anchor, render_html
from vinci.theme_intelligence.config import Paths
from vinci.theme_intelligence.desk import desk_weeks
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.qa import run_qa
from vinci.theme_intelligence.report import (
    card_context,
    dismissed_findings,
    line_findings,
    review_findings,
    write_run_outputs,
)
from vinci.theme_intelligence.resolve import (
    ResolutionError,
    current_findings,
    finding_state,
    resolve,
)
from vinci.theme_intelligence.schemas import (
    IssueSeverity,
    Provenance,
    ReviewResolution,
    RunStatus,
    ThesisVersion,
)
from vinci.theme_intelligence.store import MIGRATIONS, Store, StoreIntegrityError
from vinci.theme_intelligence.verify import _issue, card_sentences

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "vinci" / "theme_intelligence"
WHO, WHY = "verification-probe", "test: the projection is the source's own, not ours"
FACTS = ("MEASURED OBSERVATION", "EXTERNALLY VERIFIED", "ARTICLE FACT")


class Reviewer(FakeReviewer):
    """The offline reviewer, with a VERDICT per line where PARTIAL is not the one wanted."""

    def __init__(self, partial: dict[str, str], verdict: dict[str, str]) -> None:
        super().__init__(partial)
        self.verdict = verdict

    def extract(self, **kw: Any) -> dict[str, Any]:
        out = super().extract(**kw)
        for v in out["verdicts"]:
            v["verdict"] = self.verdict.get(v["sentence_id"], v["verdict"])
        return out


def _reviewed(tmp_path: Path, said: dict[str, str] | None = None) -> tuple[Pipeline, ThesisVersion]:
    """One weekly scan, its card review raising PARTIAL on s01.0 and s02.0."""
    pipe = make_pipeline(tmp_path)
    _run(pipe, random.Random(3), "res-1", END - timedelta(days=14), "ok",
         FakeReviewer(SAID if said is None else said))
    return pipe, _current(pipe)


def _key(pipe: Pipeline, v: ThesisVersion, sid: str) -> str:
    return next(lf.key for lf in review_findings(pipe.store, v.thesis_id, v)
                if lf.sentence_id == sid)


def _dismiss(pipe: Pipeline, key: str, **kw: Any) -> ReviewResolution:
    _run_, r = resolve(pipe, key, "dismissed", reviewer=kw.get("reviewer", WHO),
                       reason=kw.get("reason", WHY), as_of=END)
    return r


def test_a_dismissal_closes_the_finding_on_every_surface_and_verifies_nothing(
        tmp_path: Path) -> None:
    pipe, v = _reviewed(tmp_path)
    tid = v.thesis_id
    before_versions = [x.version for x in pipe.store.thesis_versions(tid)]
    before_priority = v.priority
    run, r = resolve(pipe, _key(pipe, v, "s01.0"), "dismissed", reviewer=WHO, reason=WHY,
                     as_of=END)
    assert run.mode == "review" and run.status.value == "SUCCEEDED" and run.cost_usd in (0, None)
    assert (r.reviewer, r.reason, r.version, r.sentence_id) == (WHO, WHY, v.version, "s01.0")
    # nothing about the thesis moved: no version, no event, the same research action
    assert [x.version for x in pipe.store.thesis_versions(tid)] == before_versions
    assert pipe.store.events(run_id=run.run_id) == []
    assert _current(pipe).priority == before_priority
    # the record of the finding is untouched: still flagged, now dismissed beside it
    assert set(line_findings(pipe.store, tid, v)[1]) == {"s01.0", "s02.0"}
    assert set(dismissed_findings(pipe.store, tid, v)) == {"s01.0"}

    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    card = BeautifulSoup((out / "cards" / f"{tid}.html").read_text(), "html.parser")
    line = card.find(id=_anchor("s01.0"))
    assert line is not None
    note = line.select_one(".rv").get_text(" ")
    assert f"Dismissed by {WHO} on {r.created_at.date().isoformat()} — {WHY}" in note
    assert "verifies nothing" in note and SAID["s01.0"] in note  # the finding's words kept
    assert line.select_one(".rw") is None  # no longer a warning …
    assert "dismissed" in line.get("class", []) and "flagged" not in line.get("class", [])
    assert line.select_one(".lab").get_text() not in FACTS  # … and never a verified fact
    head = card.select_one("header.hdr").get_text(" ")
    assert "Review required · 1 line(s)" in head  # s02.0 only
    assert "1 review finding(s) dismissed by a reviewer" in head
    js = json.loads((out / "cards" / f"{tid}.json").read_text())
    assert js["review_dismissed"]["s01.0"]["reviewer"] == WHO
    assert set(js["review_warnings"]) == {"s01.0", "s02.0"}  # machine-complete: kept

    review_page = BeautifulSoup((out / "review.html").read_text(), "html.parser")
    open_lines = " ".join(i.get_text(" ") for i in review_page.select("#rv li.rvi"))
    assert SAID["s02.0"] in open_lines and SAID["s01.0"] not in open_lines
    hist = review_page.select_one("details.quiet").get_text(" ")
    assert f"Dismissed by {WHO}" in hist and SAID["s01.0"] in hist
    assert "dismissal" in review_page.select_one("p.hint").get_text(" ")
    # the open finding's audit names its key and the command; the dismissed one its record
    audit = " ".join(a.get_text(" ") for a in review_page.select("#rv .aud"))
    assert _key(pipe, v, "s02.0") in audit and "review dismiss --finding" in audit
    # the printable weekly report: the line leaves the open list for the history fold
    rep = BeautifulSoup((out / "report_print.html").read_text(), "html.parser")
    current = rep.select_one(".rq").get_text(" ")
    assert "lines withheld or questioned (1)" in current and SAID["s02.0"][:40] in current
    hist_fold = next(d for d in rep.select("details.rqd")
                     if "Resolved or historical" in d.summary.get_text())
    assert "Resolved or historical (1)" in hist_fold.summary.get_text(" ")
    assert f"Dismissed by {WHO}" in hist_fold.get_text(" ")


def test_a_withheld_line_and_a_changed_line_are_never_dismissible(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    rng = random.Random(3)
    blocker = Reviewer(SAID, {"s01.0": "UNSUPPORTED"})
    _run(pipe, rng, "res-1", END - timedelta(days=14), "ok", blocker)
    v1 = _current(pipe)
    blocked, flagged, _c, _r = line_findings(pipe.store, v1.thesis_id, v1)
    assert set(blocked) >= {"s01.0"} and set(flagged) == {"s02.0"}
    with pytest.raises(ResolutionError, match="the line is WITHHELD"):
        _dismiss(pipe, _key(pipe, v1, "s01.0"))
    _run(pipe, rng, "res-2", END, "no_review", blocker)  # s02.0 changes, unreviewed
    v2 = _current(pipe)
    assert card_sentences(v1.content)["s02.0"][0] != card_sentences(v2.content)["s02.0"][0]
    with pytest.raises(ResolutionError, match="NOT RE-REVIEWED"):
        _dismiss(pipe, _key(pipe, v2, "s02.0"))
    assert pipe.store.review_resolutions() == []
    assert not [r for r in pipe.store.runs() if r.mode == "review"]  # nothing written


def test_a_review_warning_on_a_line_a_card_check_withholds_is_not_dismissible(
        tmp_path: Path) -> None:
    """The registry of record's TH-16225B12C4 s06.1 (2026-10-21): a REVIEW_PARTIAL on a line the
    run's own deterministic check withheld (NUMBER_NOT_IN_CITED_CLAIMS). `review list` first read
    it NOT RE-REVIEWED while the refusal said withheld; one structured field now decides both.
    The check's record is written here as the run writes it (verify._issue, its detail naming the
    line)."""
    pipe, v = _reviewed(tmp_path)
    text = card_sentences(v.content)["s01.0"][0]
    pipe.store.add_issue(_issue(v.run_id, "card_sentence", f"{v.thesis_id}:s01.0",
                                IssueSeverity.BLOCK, "NUMBER_NOT_IN_CITED_CLAIMS",
                                f"s01.0 prints '2030', which none of its cited claims carry: "
                                f"{text[:100]!r}"))
    blocked, flagged, _c, _r = line_findings(pipe.store, v.thesis_id, v)
    assert "s01.0" in blocked and "s01.0" in flagged  # the card withholds it; the warning stays
    lf = next(x for x in review_findings(pipe.store, v.thesis_id, v) if x.sentence_id == "s01.0")
    assert lf.withheld and not lf.dismissible and not lf.finding.changed
    [x] = [x for x in current_findings(pipe.store) if x.finding.sentence_id == "s01.0"]
    assert finding_state(x) == "WITHHELD"
    with pytest.raises(ResolutionError, match="the line is WITHHELD"):
        _dismiss(pipe, lf.key)
    # a dismissal written AROUND the command (a hand-edited import, say) never applies to it,
    # and qa fails the run that holds it
    other, _r = resolve(pipe, _key(pipe, v, "s02.0"), "dismissed", reviewer=WHO, reason=WHY,
                        as_of=END)
    pipe.store.add_review_resolution(ReviewResolution(**{
        **_r.model_dump(), "resolution_id": "RR-around", "sentence_id": "s01.0",
        "finding_key": lf.key, "finding_code": lf.finding.code,
        "finding_detail": lf.finding.detail, "line_text": lf.text, "claim_ids": lf.claim_ids}))
    assert set(dismissed_findings(pipe.store, v.thesis_id, v)) == {"s02.0"}
    bad = next(c for c in run_qa(pipe.store, other.run_id).checks
               if c.name == "every resolution names a finding it may resolve")
    assert not bad.ok and "RR-around: dismissed" in bad.detail and "WITHHELD" in bad.detail


def test_a_dismissal_holds_on_the_same_words_and_a_new_review_reopens_it(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    rng, fake = random.Random(3), FakeReviewer(SAID)
    _run(pipe, rng, "res-1", END - timedelta(days=14), "ok", fake)
    v1 = _current(pipe)
    _dismiss(pipe, _key(pipe, v1, "s01.0"))
    _run(pipe, rng, "res-2", END, "no_review", fake)  # unreviewed v2
    v2 = _current(pipe)
    assert card_sentences(v1.content)["s01.0"] == card_sentences(v2.content)["s01.0"]
    assert _key(pipe, v2, "s01.0") == _key(pipe, v1, "s01.0")  # the same finding, carried
    assert set(dismissed_findings(pipe.store, v2.thesis_id, v2)) == {"s01.0"}
    # a review that RUNS and raises it again makes a new finding: open, the dismissal history
    _run(pipe, random.Random(11), "res-3", END + timedelta(days=7), "ok", fake)
    v3 = _current(pipe)
    assert "s01.0" in line_findings(pipe.store, v3.thesis_id, v3)[1]
    assert _key(pipe, v3, "s01.0") != _key(pipe, v1, "s01.0")
    assert dismissed_findings(pipe.store, v3.thesis_id, v3) == {}


def test_reopen_and_every_refusal_and_the_history_kept(tmp_path: Path) -> None:
    pipe, v = _reviewed(tmp_path)
    key = _key(pipe, v, "s01.0")
    for kw, why in (({"reviewer": " "}, "reviewer and its reason"),
                    ({"reason": ""}, "reviewer and its reason")):
        with pytest.raises(ResolutionError, match=why):
            _dismiss(pipe, key, **kw)
    with pytest.raises(ResolutionError, match="no open card-review finding F-000"):
        _dismiss(pipe, "F-000000000000")
    with pytest.raises(ResolutionError, match="not dismissed"):
        resolve(pipe, key, "reopened", reviewer=WHO, reason=WHY, as_of=END)
    _dismiss(pipe, key)
    with pytest.raises(ResolutionError, match="already dismissed"):
        _dismiss(pipe, key)
    resolve(pipe, key, "reopened", reviewer="second-reader", reason="test: re-read", as_of=END)
    assert dismissed_findings(pipe.store, v.thesis_id, v) == {}
    rows = pipe.store.review_resolutions(v.thesis_id)
    assert [x.action for x in rows] == ["dismissed", "reopened"]  # both kept, in order
    assert rows[0].supersedes == () and rows[1].supersedes == (rows[0].resolution_id,)
    for sql in ("DELETE FROM review_resolutions", "UPDATE review_resolutions SET payload='{}'"):
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            pipe.store.conn.execute(sql)


def test_a_dismissed_fact_line_is_never_labelled_a_fact(tmp_path: Path) -> None:
    """THE guarantee: accepting a warning never makes the evidence valid. The synthetic lines are
    forecasts, so the stored bottom line is relabelled MEASURED OBSERVATION in memory (unit pin
    on the stored version, as the carry tests do) and rendered through the real card: capped
    while the finding is open, still capped once a reviewer dismisses it. Observed on the
    registry of record (scratch copy, 2026-10-21): TH-38CA111885 s06.0, stored MEASURED
    OBSERVATION, printed SOURCE OPINION before and after a probe dismissal."""
    pipe, v = _reviewed(tmp_path)
    c = v.content
    b0 = c.s01_bottom_line[0].model_copy(update={"provenance": Provenance.MEASURED_OBSERVATION})
    fact = v.model_copy(update={"content": c.model_copy(update={
        "s01_bottom_line": (b0, *c.s01_bottom_line[1:])})})
    t = pipe.store.thesis(v.thesis_id)
    assert t is not None
    for dismissed in (False, True):
        if dismissed:
            _dismiss(pipe, _key(pipe, v, "s01.0"))
        rc = card_context(pipe.store, t, fact, generated="t")
        assert ("s01.0" in rc.dismissed) is dismissed and "s01.0" in rc.flagged
        line = BeautifulSoup(render_html(fact.content, rc), "html.parser").find(
            id=_anchor("s01.0"))
        assert line is not None
        assert line.select_one(".lab").get_text() == "SOURCE OPINION", dismissed


def test_a_page_rendered_before_the_dismissal_never_shows_it(tmp_path: Path) -> None:
    pipe, v = _reviewed(tmp_path)
    scan = max(pipe.store.runs(), key=lambda r: r.started_at)
    r = _dismiss(pipe, _key(pipe, v, "s01.0"))
    t = pipe.store.thesis(v.thesis_id)
    assert t is not None
    then = card_context(pipe.store, t, v, generated="t", until=scan.finished_at)
    now = card_context(pipe.store, t, v, generated="t", until=r.created_at)
    assert then.dismissed == {} and set(now.dismissed) == {"s01.0"}
    assert "s01.0" in then.flagged and "s01.0" in now.flagged  # the cap holds either way
    # the scan's own pages, rendered again after the dismissal, read as the scan did
    out = Path(write_run_outputs(pipe.store, scan.run_id, tmp_path / "out")["dir"])
    rep = (out / "report_print.html").read_text()
    assert "lines withheld or questioned (2)" in rep and "Dismissed by" not in rep
    card = BeautifulSoup((out / "cards" / f"{v.thesis_id}.html").read_text(), "html.parser")
    warn = card.find(id=_anchor("s01.0")).select_one(".rw")
    assert warn is not None and warn.get_text(" ").startswith("⚠ UNRESOLVED REVIEW")


def test_qa_rechecks_a_review_run_and_refuses_a_forged_dismissal(tmp_path: Path) -> None:
    pipe, v = _reviewed(tmp_path)
    run, _r = resolve(pipe, _key(pipe, v, "s01.0"), "dismissed", reviewer=WHO, reason=WHY,
                      as_of=END)
    check = next(c for c in run_qa(pipe.store, run.run_id).checks
                 if c.name == "every resolution names a finding it may resolve")
    assert check.ok and check.detail == "1 resolution(s)"
    # a row written around the command: a key that names no finding of the version it records
    forged = ReviewResolution(**{**_r.model_dump(), "resolution_id": "RR-forged",
                                 "finding_key": "F-000000000000"})
    pipe.store.add_review_resolution(forged)
    bad = next(c for c in run_qa(pipe.store, run.run_id).checks
               if c.name == "every resolution names a finding it may resolve")
    assert not bad.ok and "F-000000000000 is no finding" in bad.detail


def test_a_review_run_never_opens_a_desk_week(tmp_path: Path) -> None:
    pipe, v = _reviewed(tmp_path)
    scan = max(pipe.store.runs(), key=lambda r: r.started_at)
    run, _r = resolve(pipe, _key(pipe, v, "s01.0"), "dismissed", reviewer=WHO, reason=WHY,
                      as_of=END)
    weeks = desk_weeks(pipe.store, run)
    assert weeks[-1].scanned and scan.run_id in weeks[-1].run_ids
    assert run.run_id in weeks[-1].run_ids  # the scan's week, never one of its own
    assert "manual runs" not in weeks[-1].label


def test_the_review_command_lists_dismisses_and_refuses(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pipe, v = _reviewed(tmp_path)
    data = str(pipe.paths.root)
    key = _key(pipe, v, "s01.0")
    pipe.store.close()
    assert main(["--data-dir", data, "review", "list"]) == 0
    listed = capsys.readouterr().out
    assert f"{key}  OPEN" in listed and f"review dismiss --finding {key}" in listed
    assert "2 card-review finding(s) on the current versions of 1 thesis(es)" in listed
    assert main(["--data-dir", data, "review", "dismiss", "--finding", key, "--reviewer", WHO,
                 "--reason", WHY]) == 0
    assert "cost $0.00" in capsys.readouterr().out
    assert main(["--data-dir", data, "review", "dismiss", "--finding", key, "--reviewer", WHO,
                 "--reason", WHY]) == 1
    assert "refused: " in capsys.readouterr().out
    assert main(["--data-dir", data, "review", "list", "--history"]) == 0
    listed = capsys.readouterr().out
    assert f"{key}  DISMISSED" in listed and f"dismissed {key} by {WHO}" in listed
    assert "1 open (1 dismissible), 1 dismissed" in listed


def test_a_state_pull_carries_a_local_review_run(tmp_path: Path) -> None:
    remote = str(tmp_path / "remote.git")
    subprocess.run(["git", "init", "--quiet", "--bare", remote], check=True)
    actions, v = _reviewed(tmp_path / "actions")
    state.push(actions.paths.root, remote)
    local_root = tmp_path / "laptop" / "ti"
    state.pull(local_root, remote)
    laptop = make_pipeline(tmp_path / "laptop")
    run, r = resolve(laptop, _key(laptop, v, "s01.0"), "dismissed", reviewer=WHO, reason=WHY,
                     as_of=END)
    laptop.store.close()
    # the branch moves before the laptop pushes (the weekly run, say)
    actions.start_run("scan", as_of=END, window_from=END, window_to=END)
    actions.finish_run(RunStatus.SUCCEEDED)
    actions.store.close()
    state.push(actions.paths.root, remote)
    pulled = state.pull(local_root, remote)
    assert any("carried 1 review run(s) the branch lacks, with their 1 resolution(s)" in x
               for x in pulled.lines)
    back = Store(Paths(local_root).db)
    kept = back.run(run.run_id)
    assert kept is not None and not kept.ledger_only  # carried whole, not as a ledger record
    assert back.review_resolutions(v.thesis_id) == [r]
    t = back.thesis(v.thesis_id)
    assert t is not None
    cur = back.thesis_version(t.thesis_id, t.current_version)
    assert cur is not None and set(dismissed_findings(back, t.thesis_id, cur)) == {"s01.0"}


def test_a_v7_registry_migrates_and_an_export_carries_the_resolutions(tmp_path: Path) -> None:
    db = tmp_path / "r.db"
    Store(db, migrations=[m for m in MIGRATIONS if m[0] <= 7]).close()
    st = Store(db)
    assert st.schema_version() == max(v for v, _ in MIGRATIONS) and st.review_resolutions() == []
    st.close()
    pipe, v = _reviewed(tmp_path / "p")
    r = _dismiss(pipe, _key(pipe, v, "s01.0"))
    pipe.store.export_jsonl(tmp_path / "x")
    there = Store.import_jsonl(tmp_path / "x", tmp_path / "b.db")
    assert there.review_resolutions() == [r]


def test_old_code_refuses_an_export_from_a_newer_schema_and_reads_its_own(
        tmp_path: Path) -> None:
    """Review of #777: v9 lets a stored issue carry `copied_from`; payloads are validated with
    extra="forbid", so code before it would import such an export and fail mid-command. An
    import now refuses an export made at a newer schema, as `migrate` refuses a newer database.
    NEGATIVE: an export at this code's own schema imports."""
    pipe, _v = _reviewed(tmp_path / "p")
    pipe.store.export_jsonl(tmp_path / "x")
    older = [m for m in MIGRATIONS if m[0] < max(v for v, _ in MIGRATIONS)]
    with pytest.raises(StoreIntegrityError, match="newer than this code"):
        Store.import_jsonl(tmp_path / "x", tmp_path / "old.db", migrations=older)
    assert not (tmp_path / "old.db").exists()  # refused before anything was written
    there = Store.import_jsonl(tmp_path / "x", tmp_path / "same.db")
    assert there.schema_version() == max(v for v, _ in MIGRATIONS)
    with pytest.raises(StoreIntegrityError, match="newer than this code"):
        Store(tmp_path / "same.db", migrations=older)  # the database itself, as before
    Store(tmp_path / "v-old.db", migrations=older).export_jsonl(tmp_path / "x-old")
    back = Store.import_jsonl(tmp_path / "x-old", tmp_path / "old-again.db", migrations=older)
    assert back.schema_version() == max(v for v, _ in older)  # old code reads its own export


def test_no_research_action_rule_reads_a_resolution() -> None:
    """The rules, the engine and the pipeline never read the resolution record — POSITIVE: the
    surfaces that show it do."""
    words = re.compile(r"review_resolutions|ReviewResolution|dismissed_findings|"
                       r"theme_intelligence\.resolve\b")
    for name in ("priority.py", "engine.py", "pipeline.py"):
        assert not words.search((PKG / name).read_text()), name
    assert words.search((PKG / "report.py").read_text())
    assert words.search((PKG / "desk.py").read_text())


def test_the_state_is_what_the_reviewer_saw_never_the_later_clock(tmp_path: Path) -> None:
    """Review of #768: the state was the row with the latest wall-clock stamp, so a reopening
    made on a machine whose clock ran slow sorted before the dismissal it answered, and the
    dismissal won. Each row now names what it supersedes."""
    pipe, v = _reviewed(tmp_path)
    d = _dismiss(pipe, _key(pipe, v, "s01.0"))
    slow = ReviewResolution(**{**d.model_dump(), "resolution_id": "RR-slow-clock",
                               "action": "reopened", "reviewer": "second-reader",
                               "created_at": d.created_at - timedelta(hours=1),
                               "supersedes": (d.resolution_id,)})
    pipe.store.add_review_resolution(slow)
    assert slow.created_at < d.created_at
    assert dismissed_findings(pipe.store, v.thesis_id, v) == {}  # the reopening holds
    # … and a re-dismissal stamped earlier still, answering the reopening, holds in its turn
    back = ReviewResolution(**{**d.model_dump(), "resolution_id": "RR-slower-still",
                               "created_at": d.created_at - timedelta(hours=2),
                               "supersedes": (slow.resolution_id,)})
    pipe.store.add_review_resolution(back)
    assert dismissed_findings(pipe.store, v.thesis_id, v)["s01.0"] == back


def test_a_dismissal_and_a_reopening_made_apart_read_open_until_resolved(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pipe, v = _reviewed(tmp_path)
    key = _key(pipe, v, "s01.0")
    d = _dismiss(pipe, key)
    apart = ReviewResolution(**{**d.model_dump(), "resolution_id": "RR-other-machine",
                                "action": "reopened", "reviewer": "second-reader",
                                "created_at": d.created_at + timedelta(minutes=5),
                                "supersedes": ()})  # never saw the dismissal
    pipe.store.add_review_resolution(apart)
    assert dismissed_findings(pipe.store, v.thesis_id, v) == {}  # fail-safe: OPEN
    [x] = [x for x in current_findings(pipe.store) if x.finding.key == key]
    assert x.conflict and x.state is None and finding_state(x) == "OPEN"
    data = str(pipe.paths.root)
    pipe.store.close()
    assert main(["--data-dir", data, "review", "list"]) == 0
    assert "CONFLICT: dismissed and reopened apart" in capsys.readouterr().out
    again = make_pipeline(tmp_path)
    _run_, r = resolve(again, key, "dismissed", reviewer=WHO, reason=WHY, as_of=END)
    assert set(r.supersedes) == {d.resolution_id, "RR-other-machine"}  # it settles both
    assert set(dismissed_findings(again.store, v.thesis_id, v)) == {"s01.0"}


def test_the_history_keeps_a_finding_gone_from_the_card(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Review of #768: `--history` listed only theses with a current finding, so a dismissal
    whose finding a later review no longer raised was in the table but never shown."""
    pipe = make_pipeline(tmp_path)
    rng = random.Random(3)
    _run(pipe, rng, "res-1", END - timedelta(days=14), "ok", FakeReviewer(SAID))
    v1 = _current(pipe)
    r = _dismiss(pipe, _key(pipe, v1, "s01.0"))
    _run(pipe, rng, "res-2", END, "ok", FakeReviewer({}))  # a clean review: no finding left
    assert current_findings(pipe.store) == []
    data = str(pipe.paths.root)
    pipe.store.close()
    assert main(["--data-dir", data, "review", "list", "--history"]) == 0
    out = capsys.readouterr().out
    assert f"dismissed {r.finding_key} by {WHO}" in out and "; current)" in out
    assert "1 resolution(s) recorded" in out


def test_qa_refuses_a_resolution_superseding_nothing_it_knows(tmp_path: Path) -> None:
    pipe, v = _reviewed(tmp_path)
    run, r = resolve(pipe, _key(pipe, v, "s01.0"), "dismissed", reviewer=WHO, reason=WHY,
                     as_of=END)
    pipe.store.add_review_resolution(ReviewResolution(**{
        **r.model_dump(), "resolution_id": "RR-dangling", "action": "reopened",
        "supersedes": ("RR-nowhere",)}))
    bad = next(c for c in run_qa(pipe.store, run.run_id).checks
               if c.name == "every resolution names a finding it may resolve")
    assert not bad.ok and "RR-dangling: supersedes ['RR-nowhere']" in bad.detail
