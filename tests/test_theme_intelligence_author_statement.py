"""The operator states an analysed article's author(s) — $0, recorded with who and why
(attribution.py, 2026-10-22).

Before: an upload whose page names no author stayed UNKNOWN for good, and QA's integrity check
"every analysed article names its author(s)" failed on its run. On the registry of record,
Morgan Stanley's three unsigned web articles failed QA on both ingest runs of the 2026-10-21
merge. The only route to an author was to analyse the document again, paid.

Now `author --article A-… --name NAME --by WHO --reason WHY` records the statement: on the
article (with its provenance), among the document's declared statements (a replay states it
again), and as an AUTHORS_STATED issue. A run of mode "author": no desk week, no thesis touched.

Documents are the SYNTHETIC fixtures; articles are HYPOTHETICAL and labelled; extractions use the
REAL types; no network, no model.
"""

from __future__ import annotations

import subprocess
from datetime import timedelta
from pathlib import Path

import pytest

from tests.test_theme_intelligence_state_sync import AS_OF, MS_PDF, _ms_ext, _offline, _scan
from tests.test_theme_intelligence_state_sync import _upload as fixture_upload
from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import state
from vinci.theme_intelligence.__main__ import main
from vinci.theme_intelligence.attribution import AttributionError, state_authors
from vinci.theme_intelligence.desk import desk_weeks
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.qa import run_qa
from vinci.theme_intelligence.schemas import (
    OPERATOR_STATED,
    FieldStatus,
    IssueSeverity,
    RunStatus,
)
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.verify import _issue

__all__ = ["_offline"]  # the state tests' guard against live network requests, applied here

WHO, WHY = "verification-probe", "test: the page names no individual author"
INSTITUTION = "institution — the page names no individual author"


def _authorless(tmp_path: Path) -> tuple[Pipeline, str, str]:
    """A scan, then the synthetic report uploaded with no author stated (it names none)."""
    pipe = make_pipeline(tmp_path)
    _scan(pipe)
    res = fixture_upload(pipe, MS_PDF, _ms_ext())
    assert res.article_id is not None
    doc = pipe.store.document(res.doc_id)
    assert doc is not None and doc.run_id is not None
    return pipe, res.article_id, doc.run_id


def _author_check(pipe: Pipeline, run_id: str) -> tuple[bool, str]:
    c = next(c for c in run_qa(pipe.store, run_id).checks
             if c.name == "every analysed article names its author(s)")
    return c.ok, c.detail


def test_a_stated_author_clears_qa_and_records_who_and_why(tmp_path: Path) -> None:
    pipe, aid, upload_run = _authorless(tmp_path)
    art = pipe.store.article(aid)
    assert art is not None and art.authors_status is FieldStatus.UNKNOWN
    assert _author_check(pipe, upload_run) == (False, f"{aid} (Morgan Stanley)")
    versions = {t.thesis_id: t.current_version for t in pipe.store.theses()}
    run, new = state_authors(pipe, aid, ["Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF,
                             title=INSTITUTION)
    assert run.mode == "author" and run.status.value == "SUCCEEDED"
    [stated] = [a for a in new.authors if a.name == "Morgan Stanley"]
    assert stated.title == INSTITUTION
    assert stated.source_field == f"{OPERATOR_STATED} by {WHO} in run {run.run_id}: {WHY}"
    assert new.authors_status is FieldStatus.KNOWN and pipe.store.article(aid) == new
    assert _author_check(pipe, upload_run)[0]  # the upload's run passes now
    # the document states it too — a replay reads it back — and its history says when and who
    [doc] = [d for d in pipe.store.documents() if d.article_id == aid]
    assert Declared.recorded(doc.source_id, doc.declared).authors == ("Morgan Stanley",)
    assert f"AUTHORS STATED by {WHO} (run {run.run_id}): Morgan Stanley — {WHY}" in \
        doc.history[-1]
    [issue] = [i for i in pipe.store.issues(run_id=run.run_id) if i.code == "AUTHORS_STATED"]
    assert issue.ref_id == aid and issue.severity is IssueSeverity.INFO and WHO in issue.detail
    # nothing about a thesis moved, and the run checks out
    assert {t.thesis_id: t.current_version for t in pipe.store.theses()} == versions
    assert pipe.store.events(run_id=run.run_id) == []
    check = next(c for c in run_qa(pipe.store, run.run_id).checks
                 if c.name == "every stated author is on its article")
    assert check.ok and check.detail == "1 article(s)"


@pytest.mark.parametrize(("article", "names", "by", "reason", "why"), [
    (None, [" "], WHO, WHY, "all three are required"),
    (None, ["Morgan Stanley"], "", WHY, "all three are required"),
    (None, ["Morgan Stanley"], WHO, " ", "all three are required"),
    ("A-000000000000", ["Morgan Stanley"], WHO, WHY, "no article A-000000000000"),
])
def test_a_refused_statement_writes_nothing(tmp_path: Path, article: str | None,
                                            names: list[str], by: str, reason: str,
                                            why: str) -> None:
    pipe, aid, _run = _authorless(tmp_path)
    runs = len(pipe.store.runs())
    with pytest.raises(AttributionError, match=why):
        state_authors(pipe, article or aid, names, by=by, reason=reason, as_of=AS_OF)
    assert len(pipe.store.runs()) == runs
    art = pipe.store.article(aid)
    assert art is not None and art.authors_status is FieldStatus.UNKNOWN


def test_a_name_already_credited_is_refused(tmp_path: Path,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    pipe, aid, _run = _authorless(tmp_path)
    state_authors(pipe, aid, ["Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF)
    data = str(pipe.paths.root)
    pipe.store.close()
    assert main(["--data-dir", data, "author", "--article", aid, "--name", "MORGAN  stanley",
                 "--by", WHO, "--reason", WHY]) == 1
    assert "already credits MORGAN  stanley — nothing stated" in capsys.readouterr().out
    assert main(["--data-dir", data, "author", "--article", aid, "--name", "Ana Analyst",
                 "--by", WHO, "--reason", WHY]) == 0
    assert "now credits Morgan Stanley; Ana Analyst; cost $0.00" in capsys.readouterr().out


def test_a_re_read_keeps_an_operator_stated_author(tmp_path: Path) -> None:
    """A later version of the article — its page still naming no author — must not un-state
    the operator's statement (pipeline._article_record, as for a text-credited author)."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    text = "Large-load interconnection requests in the US rose 110% in 2026 on AI demand"
    one = Hypo(slug="unsigned", publisher="Hypothetical Grid Research", author=None,
               published=AS_OF - timedelta(days=5), blocks=[("paragraph", text + ".")])
    ext = extraction([claim("c1", "b001", text, "Requests +110% in 2026",
                            metric="large-load requests", value=110, value_text="110%",
                            unit="%", period="2026")],
                     [hyp("h1", "Grid queues lengthen", node="ai_infrastructure.power_grid",
                          mechanism="supply_constraint", geography="US", supporting=["c1"])])
    r1 = ingest(pipe, one.doc(), ext, as_of=AS_OF, publisher=one.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert r1.article_id is not None
    state_authors(pipe, r1.article_id, ["Grid Desk"], by=WHO, reason=WHY, as_of=AS_OF)
    pipe.start_run("article", as_of=AS_OF + timedelta(days=1))
    two = Hypo(slug="unsigned", publisher="Hypothetical Grid Research", author=None,
               published=AS_OF - timedelta(days=5),
               blocks=[("paragraph", text + "."), ("paragraph", "A second paragraph, added in "
                                                                "a later version of the page.")])
    r2 = ingest(pipe, two.doc(), ext, as_of=AS_OF + timedelta(days=1), publisher=two.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert r2.article_id == r1.article_id and len(pipe.store.article_versions(r1.article_id)) == 2
    art = pipe.store.article(r1.article_id)
    assert art is not None and art.authors_status is FieldStatus.KNOWN
    assert [a.name for a in art.authors] == ["Grid Desk"]


def test_an_author_run_never_opens_a_desk_week(tmp_path: Path) -> None:
    pipe, aid, upload_run = _authorless(tmp_path)
    up = pipe.store.run(upload_run)
    assert up is not None
    before = [w.label for w in desk_weeks(pipe.store, up)]  # the scan's week, the upload's
    run, _art = state_authors(pipe, aid, ["Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF)
    weeks = desk_weeks(pipe.store, run)
    assert [w.label for w in weeks] == before  # no week of its own
    [scan_week] = [w for w in weeks if w.scanned]
    assert run.run_id in scan_week.run_ids  # it follows the scan, as a refresh does


def test_qa_refuses_a_statement_the_article_does_not_carry(tmp_path: Path) -> None:
    """An AUTHORS_STATED record whose article carries no author stated in that run (a forged
    or half-written run) fails QA."""
    pipe, aid, _run = _authorless(tmp_path)
    run, _art = state_authors(pipe, aid, ["Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF)
    scan_article = next(a for a in pipe.store.articles() if a.article_id != aid)
    assert scan_article.authors_status is FieldStatus.KNOWN  # its page credits an author …
    for ref in ("A-not-stated", scan_article.article_id):  # … none stated in this run
        pipe.store.add_issue(_issue(run.run_id, "article", ref, IssueSeverity.INFO,
                                    "AUTHORS_STATED", f"Nobody — forged on {ref}"))
    bad = next(c for c in run_qa(pipe.store, run.run_id).checks
               if c.name == "every stated author is on its article")
    assert not bad.ok and "A-not-stated: no such article" in bad.detail
    assert f"{scan_article.article_id}: no author stated in this run on the article" in bad.detail


def test_an_unpushed_author_run_makes_a_pull_refuse(tmp_path: Path) -> None:
    """The statement is a local run a pull cannot replay: the pull refuses to discard it (push
    first), never drops it silently."""
    remote = str(tmp_path / "remote.git")
    subprocess.run(["git", "init", "--quiet", "--bare", remote], check=True)
    pipe, aid, _run = _authorless(tmp_path)
    pipe.store.close()
    state.push(pipe.paths.root, remote)
    again = make_pipeline(tmp_path)
    run, _art = state_authors(again, aid, ["Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF)
    again.store.close()
    with pytest.raises(state.StateSyncError, match=rf"{run.run_id} \[author\]"):
        state.pull(again.paths.root, remote)
    state.push(again.paths.root, remote)  # pushed, it crosses
    back = tmp_path / "back" / "ti"
    state.pull(back, remote, replay=False)
    art = Store(back / "registry.db").article(aid)
    assert art is not None and [a.name for a in art.authors] == ["Morgan Stanley"]
