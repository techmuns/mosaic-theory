"""A version written WITHOUT the card review never reads as clean (PR #703 review-safety fix,
2026-10-13).

Before: when a run recorded REVIEW_NOT_RUN for a thesis (`--no-review`, the review budget
exhausted, or no model client and no cached review), the new version showed only its own run's
findings — none — so the previous version's open finding vanished from the card and from the
research desk's Review screen, even on an unchanged line.

Now, read from the stored records (nothing copied, nothing edited):
  * an open finding stays on the line with the SAME words and the SAME cited evidence — with the
    version and date that made it;
  * a flagged line whose words or evidence changed reads NOT RE-REVIEWED;
  * a version the review never read says so, even with no earlier finding;
  * a line removed by an unreviewed version keeps its finding open (removed, never resolved);
  * a genuinely successful later review stands on its own findings — a finding it does not raise
    again is no longer open.

Every review answer here comes from an OFFLINE fake client (no network, no paid call); the
articles are SYNTHETIC (tests/theme_intelligence_stress.py) on the reserved `.test` domain.
"""

from __future__ import annotations

import json
import random
import re
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_stress import END, _article, _doc
from tests.theme_intelligence_support import fetched, make_pipeline, table_counts
from vinci.theme_intelligence.budget import GuardedClient
from vinci.theme_intelligence.cards import LABEL_OPEN, _anchor
from vinci.theme_intelligence.engine import SentenceCorrection
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import (
    dismissed_findings,
    line_findings,
    review_carry,
    review_findings,
    write_run_outputs,
)
from vinci.theme_intelligence.resolve import resolve
from vinci.theme_intelligence.schemas import RunStatus, ThesisVersion
from vinci.theme_intelligence.verify import REVIEW_TOOL, card_sentences

KEY = ("ai_infrastructure.memory", "pricing_cycle", "NAND", "Global")
SAID = {"s01.0": "the cited span does not state the supply cause (test finding)",
        "s02.0": "the cited figure is a projection, not a reported change (test finding)"}
_SID = re.compile(r"^\[(s\d\d\.\w+)\] \(", re.M)


class FakeReviewer:
    """An offline card reviewer: SUPPORTED for every line, PARTIAL for the lines in `partial`."""

    model = "claude-opus-4-8"

    def __init__(self, partial: dict[str, str]) -> None:
        self.partial = partial
        self.calls = 0
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **_kw: Any) -> dict[str, Any]:
        assert tool["name"] == REVIEW_TOOL["name"], "only the card review may reach the fake"
        self.calls += 1
        self.last_usage = {"input_tokens": 10, "output_tokens": 10}
        return {"verdicts": [
            {"sentence_id": sid, "verdict": "PARTIAL" if sid in self.partial else "SUPPORTED",
             "problem": self.partial.get(sid, ""), "better_claim_ids": []}
            for sid in _SID.findall(user)]}


def _read(pipe: Pipeline, rng: random.Random, slug: str, as_of: Any) -> None:
    blocks, x, title = _article(KEY, "straddle", as_of, rng, uncaptured=False, tag=slug)
    doc = _doc(slug, title, as_of, blocks)
    res = pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="trendforce",
                                as_of=as_of, fixture=x,
                                completeness_fixture={"figure_reviews": [], "block_reviews": []})
    assert res.status == "PROCESSED", res.note


def _run(pipe: Pipeline, rng: random.Random, slug: str, as_of: Any, review: str,
         fake: FakeReviewer | None = None) -> str:
    """One weekly scan reading one article, its card review `review`: "ok" (the fake answers),
    "no_review" (--no-review), "budget" (exhausted) or "no_client" (no client, no cache)."""
    pipe.review = review != "no_review"
    pipe.client = (GuardedClient(fake, pipe.guard) if review in ("ok", "budget") and fake
                   else None)
    run = pipe.start_run("scan", as_of=as_of, window_from=as_of - timedelta(days=6),
                         window_to=as_of)
    pipe.guard.run_limit = 0.0 if review == "budget" else 100.0
    _read(pipe, rng, slug, as_of)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return run.run_id


def _current(pipe: Pipeline) -> ThesisVersion:
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    return v


def _reviewed_then(tmp_path: Path, review: str) -> tuple[Pipeline, ThesisVersion, ThesisVersion,
                                                         FakeReviewer]:
    """v1 reviewed (two PARTIAL findings), then v2 from a new article with the review `review`."""
    pipe = make_pipeline(tmp_path)
    rng = random.Random(3)
    fake = FakeReviewer(SAID)
    _run(pipe, rng, "carry-1", END - timedelta(days=14), "ok", fake)
    v1 = _current(pipe)
    fake.calls = 0
    _run(pipe, rng, "carry-2", END, review, fake)
    v2 = _current(pipe)
    assert v2.version == v1.version + 1
    return pipe, v1, v2, fake


NOT_RUN = {"no_review": "--no-review", "budget": "budget", "no_client": "no LLM client"}


@pytest.mark.parametrize("review", ["no_review", "budget", "no_client"])
def test_an_unreviewed_version_keeps_the_earlier_open_findings_on_the_card_and_the_desk(
        tmp_path: Path, review: str) -> None:
    pipe, v1, v2, fake = _reviewed_then(tmp_path, review)
    tid = v1.thesis_id
    assert set(line_findings(pipe.store, tid, v1)[1]) == {"s01.0", "s02.0"}
    assert fake.calls == 0  # the second review was never sent — nothing paid
    not_run = [i for i in pipe.store.issues(run_id=v2.run_id) if i.code == "REVIEW_NOT_RUN"]
    assert len(not_run) == 1 and NOT_RUN[review] in not_run[0].detail
    s1, s2 = card_sentences(v1.content), card_sentences(v2.content)
    assert s1["s01.0"] == s2["s01.0"]  # the same words, the same cited evidence
    assert s1["s02.0"][0] != s2["s02.0"][0]  # a flagged line that changed
    _b, flagged, _c, resolved = line_findings(pipe.store, tid, v2)
    assert flagged == {"s01.0": SAID["s01.0"], "s02.0": SAID["s02.0"]} and resolved == {}
    carry = review_carry(pipe.store, tid, v2)
    assert carry.not_run == not_run[0].detail
    keep, moved = carry.carried["s01.0"], carry.carried["s02.0"]
    assert (keep.changed, keep.origin_version, keep.origin_as_of) == (False, 1, v1.as_of)
    assert (moved.changed, moved.origin_text) == (True, s1["s02.0"][0])
    # nothing duplicated: the only review findings stored are v1's own, unedited
    review_issues = [i for i in pipe.store.issues() if i.code.startswith("REVIEW_PARTIAL")]
    assert {i.run_id for i in review_issues} == {v1.run_id}

    before = table_counts(pipe)
    out = Path(write_run_outputs(pipe.store, v2.run_id, tmp_path / "out")["dir"])
    assert table_counts(pipe) == before  # rendering writes nothing
    card = BeautifulSoup((out / "cards" / f"{tid}.html").read_text(), "html.parser")
    line = card.find(id=_anchor("s01.0"))
    assert line is not None
    warn = line.select_one(".rw").get_text(" ")
    assert warn.startswith("⚠ UNRESOLVED REVIEW") and SAID["s01.0"] in warn
    assert "raised by the review of version 1" in warn
    # the safeguard on a questioned line holds: it is never shown as a verified fact
    assert line.select_one(".lab").get_text() not in (
        "MEASURED OBSERVATION", "EXTERNALLY VERIFIED", "ARTICLE FACT")
    assert "flagged" in (line.get("class") or [])
    changed = card.find(id=_anchor("s02.0")).select_one(".rw").get_text(" ")
    assert changed.startswith("⚠ NOT RE-REVIEWED") and SAID["s02.0"] in changed
    head = card.select_one("header.hdr").get_text(" ")
    assert "Not reviewed" in head and "Review required · 2 line(s)" in head
    assert "No unresolved review findings" not in head

    review_page = BeautifulSoup((out / "review.html").read_text(), "html.parser")
    items = {i.select_one(".line").get_text(" ").strip("“” "): i
             for i in review_page.select("#rv li.rvi")}
    s01_text = re.sub(r"\s*⟨[^⟩]*⟩\s*", " ", s2["s01.0"][0]).strip()
    item = next(v for k, v in items.items() if k.startswith(s01_text[:40]))
    assert SAID["s01.0"] in item.get_text(" ") and "(version 1)" in item.get_text(" ")
    assert v1.as_of.strftime("%b %Y") in item.get_text(" ")  # the first-raised date, kept
    kinds = [i.select_one(".said b").get_text() for i in review_page.select("#rv li.rvi")]
    assert kinds.count("Not re-reviewed:") == 1 and kinds.count("Not reviewed:") == 1
    reading = BeautifulSoup((out / "theses" / f"{tid}.html").read_text(), "html.parser")
    assert "Not reviewed · Review required" in reading.select_one("header.th").get_text(" ")


def test_a_chain_of_unreviewed_versions_carries_the_finding_from_the_last_review(
        tmp_path: Path) -> None:
    pipe, v1, _v2, fake = _reviewed_then(tmp_path, "no_review")
    _run(pipe, random.Random(9), "carry-3", END + timedelta(days=7), "no_review", fake)
    v3 = _current(pipe)
    assert v3.version == 3
    carry = review_carry(pipe.store, v3.thesis_id, v3)
    assert carry.carried["s01.0"].origin_version == 1
    assert line_findings(pipe.store, v3.thesis_id, v3)[1]["s01.0"] == SAID["s01.0"]


def test_a_successful_later_review_stands_on_its_own_findings(tmp_path: Path) -> None:
    """The opposite case: a review that RUNS and does not raise the finding again clears it —
    the existing rule — and the card no longer reports a skipped review."""
    pipe, _v1, _v2, _fake = _reviewed_then(tmp_path, "no_review")
    clean = FakeReviewer({})
    _run(pipe, random.Random(11), "carry-3", END + timedelta(days=7), "ok", clean)
    v3 = _current(pipe)
    assert clean.calls >= 1
    blocked, flagged, _c, _r = line_findings(pipe.store, v3.thesis_id, v3)
    assert flagged == {} and blocked == {}
    carry = review_carry(pipe.store, v3.thesis_id, v3)
    assert carry.not_run is None and carry.carried == {}
    out = Path(write_run_outputs(pipe.store, v3.run_id, tmp_path / "out")["dir"])
    head = BeautifulSoup((out / "cards" / f"{v3.thesis_id}.html").read_text(),
                         "html.parser").select_one("header.hdr").get_text(" ")
    assert "No unresolved review findings" in head and "Not reviewed" not in head
    review_page = BeautifulSoup((out / "review.html").read_text(), "html.parser")
    assert review_page.select("#rv li.rvi") == []


def test_a_later_review_that_raises_the_finding_again_keeps_it_open(tmp_path: Path) -> None:
    pipe, _v1, _v2, _fake = _reviewed_then(tmp_path, "budget")
    again = FakeReviewer({"s01.0": SAID["s01.0"]})
    _run(pipe, random.Random(11), "carry-3", END + timedelta(days=7), "ok", again)
    v3 = _current(pipe)
    assert line_findings(pipe.store, v3.thesis_id, v3)[1] == {"s01.0": SAID["s01.0"]}
    assert review_carry(pipe.store, v3.thesis_id, v3).not_run is None


@pytest.mark.parametrize("review", ["no_review", "budget", "no_client"])
def test_a_new_thesis_the_review_never_read_says_so(tmp_path: Path, review: str) -> None:
    pipe = make_pipeline(tmp_path)
    run_id = _run(pipe, random.Random(5), "fresh-1", END, review, FakeReviewer({}))
    v = _current(pipe)
    assert v.version == 1
    carry = review_carry(pipe.store, v.thesis_id, v)
    assert carry.not_run is not None and NOT_RUN[review] in carry.not_run
    assert carry.carried == {} and carry.removed == ()
    out = Path(write_run_outputs(pipe.store, run_id, tmp_path / "out")["dir"])
    card = BeautifulSoup((out / "cards" / f"{v.thesis_id}.html").read_text(), "html.parser")
    head = card.select_one("header.hdr").get_text(" ")
    assert "Not reviewed" in head and "No unresolved review findings" not in head
    md = (out / "cards" / f"{v.thesis_id}.md").read_text()
    assert "Not reviewed — the card review did not run for this version" in md
    items = BeautifulSoup((out / "review.html").read_text(), "html.parser").select("#rv li.rvi")
    assert [i.select_one(".line").get_text(" ").strip("“” ") for i in items] == [
        "Version 1 was not reviewed"]


def test_a_flagged_line_an_unreviewed_version_removed_stays_open(tmp_path: Path) -> None:
    """A finding whose line an unreviewed version no longer carries is listed as removed — open,
    never resolved (unit pin on the stored v2, its What-changed items emptied in memory)."""
    pipe, v1, v2, _fake = _reviewed_then(tmp_path, "no_review")
    c = v2.content
    gone = v2.model_copy(update={"content": c.model_copy(update={
        "s02_what_changed": c.s02_what_changed.model_copy(update={"items": ()})})})
    carry = review_carry(pipe.store, v2.thesis_id, gone)
    assert [f.origin_text for f in carry.removed] == [card_sentences(v1.content)["s02.0"][0]]
    assert carry.removed[0].said == SAID["s02.0"]
    assert set(carry.carried) == {"s01.0"}


def test_the_same_words_on_other_evidence_are_not_re_reviewed(tmp_path: Path) -> None:
    """Identical words citing DIFFERENT evidence are a changed line: NOT RE-REVIEWED, never the
    unresolved finding read as if nothing moved (unit pin on the stored v2, its bottom line's
    citation swapped in memory)."""
    pipe, _v1, v2, _fake = _reviewed_then(tmp_path, "no_review")
    c = v2.content
    other = card_sentences(c)["s02.0"][2]
    bottom = c.s01_bottom_line[0].model_copy(update={"claim_ids": other})
    moved = v2.model_copy(update={"content": c.model_copy(update={
        "s01_bottom_line": (bottom, *c.s01_bottom_line[1:])})})
    carry = review_carry(pipe.store, v2.thesis_id, moved)
    assert card_sentences(moved.content)["s01.0"][0] == card_sentences(c)["s01.0"][0]
    assert carry.carried["s01.0"].changed is True


# --- a re-grade after an unreviewed version (2026-10-22) ----------------------------------------

def _regrade(pipe: Pipeline, as_of: Any, sid: str | None = None) -> tuple[ThesisVersion, str]:
    """A re-grade (`reassess`, $0) of the one thesis — with an analyst correction of `sid` (its
    own words and evidence, restated) so it always writes a new version."""
    v = _current(pipe)
    corr = []
    if sid is not None:
        text, _p, cids = card_sentences(v.content)[sid]
        corr = [SentenceCorrection(thesis_id=v.thesis_id, sentence_id=sid,
                                   text=f"{text.split(LABEL_OPEN)[0].strip()} (restated)",
                                   claim_ids=tuple(cids), reason="test")]
    run, outs = pipe.run_reassess(as_of=as_of, corrections=corr)
    assert len(outs) == 1, "the re-grade wrote no new version: nothing would be tested"
    return _current(pipe), run.run_id


def _other_line(v: ThesisVersion) -> str:
    """A line with evidence and no finding — what a correction may restate harmlessly."""
    return next(k for k, (_t, _p, c) in card_sentences(v.content).items()
                if c and k not in SAID and k.startswith(("s02", "s03")))


@pytest.mark.parametrize("review", ["no_review", "budget", "no_client"])
def test_a_re_grade_keeps_what_an_unreviewed_version_carried(
        tmp_path: Path, review: str) -> None:
    """A re-grade copies the findings stored in the run of the version before it; a version
    written WITHOUT the review stores none — it carries them — so the re-grade read CLEAN: its two
    open findings were gone (offline fixture, 2026-10-22: 2 → 0). They are read on as they were
    read there: same origin, same key, a dismissal kept — through a second re-grade too."""
    pipe, v1, v2, _fake = _reviewed_then(tmp_path, review)
    keys = {lf.sentence_id: lf.key for lf in review_findings(pipe.store, v2.thesis_id, v2)}
    assert set(keys) == set(SAID)
    resolve(pipe, keys["s01.0"], "dismissed", reviewer="test", reason="test", as_of=END)
    for week in (1, 2):
        v, run_id = _regrade(pipe, END + timedelta(days=7 * week), _other_line(_current(pipe)))
        now = {lf.sentence_id: lf for lf in review_findings(pipe.store, v.thesis_id, v)}
        assert {s: lf.key for s, lf in now.items()} == keys
        assert {lf.finding.origin_version for lf in now.values()} == {v1.version}
        assert set(dismissed_findings(pipe.store, v.thesis_id, v)) == {"s01.0"}
        assert review_carry(pipe.store, v.thesis_id, v).not_run is None  # no banner: a re-grade
    out = write_run_outputs(pipe.store, run_id, tmp_path / "out")  # the rendered card
    js = json.loads((Path(out["dir"]) / "cards" / f"{v1.thesis_id}.json").read_text())
    assert set(js["review_warnings"]) == set(SAID) and set(js["review_dismissed"]) == {"s01.0"}


def test_a_re_grade_correcting_a_carried_line_closes_its_finding(tmp_path: Path) -> None:
    """An analyst correction closes the corrected line's earlier findings — carried ones as copied
    ones: the corrected line is neither open nor listed as removed."""
    pipe, _v1, _v2, _fake = _reviewed_then(tmp_path, "no_review")
    v, _run_id = _regrade(pipe, END + timedelta(days=7), "s02.0")
    assert {lf.sentence_id for lf in review_findings(pipe.store, v.thesis_id, v)} == {"s01.0"}
    assert review_carry(pipe.store, v.thesis_id, v).removed == ()


def test_a_re_grade_after_a_reviewed_version_reads_only_its_copies(tmp_path: Path) -> None:
    """NEGATIVE: after a REVIEWED version nothing is carried — its findings are the copies the
    re-grade stored (every re-grade on the registry of record is of this kind: its reading is
    unchanged)."""
    pipe, _v1, v2, _fake = _reviewed_then(tmp_path, "ok")
    v, _run_id = _regrade(pipe, END + timedelta(days=7), _other_line(v2))
    carry = review_carry(pipe.store, v.thesis_id, v)
    assert carry.carried == {} and carry.removed == ()
    now = review_findings(pipe.store, v.thesis_id, v)
    assert {lf.sentence_id for lf in now} == set(SAID)
    assert {lf.finding.origin_version for lf in now} == {v2.version}  # its own review's
