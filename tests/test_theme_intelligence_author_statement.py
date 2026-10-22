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
from vinci.theme_intelligence.attribution import (
    LINKLESS_RUNS,
    AttributionError,
    retract_author,
    state_authors,
)
from vinci.theme_intelligence.attribution import check_run as check_authors
from vinci.theme_intelligence.desk import desk_weeks
from vinci.theme_intelligence.documents import Declared, DocumentError
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.qa import run_qa
from vinci.theme_intelligence.report import _sources_line, build_dashboard
from vinci.theme_intelligence.schemas import (
    OPERATOR_STATED,
    Author,
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
    assert stated.source_field == f"{OPERATOR_STATED} by {WHO}: {WHY}"
    assert stated.stated_in == run.run_id  # the run, as a structured link
    assert new.authors_status is FieldStatus.KNOWN and pipe.store.article(aid) == new
    assert _author_check(pipe, upload_run)[0]  # the upload's run passes now
    # the document states it too — a replay reads it back — and its history says when and who
    [doc] = [d for d in pipe.store.documents() if d.article_id == aid]
    assert Declared.recorded(doc.source_id, doc.declared).authors == ("Morgan Stanley",)
    assert f"AUTHORS STATED by {WHO}: Morgan Stanley — {WHY} (run {run.run_id})" in \
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


# --- review of #771 ----------------------------------------------------------------------------

def test_a_failed_record_leaves_the_article_untouched(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """The name, the document and the AUTHORS_STATED record are ONE transaction: a failure
    writing the record leaves no name on the article without it."""
    pipe, aid, _run = _authorless(tmp_path)
    before = pipe.store.article(aid)

    def broken(*_a: object, **_k: object) -> None:
        raise RuntimeError("the issue could not be written")

    monkeypatch.setattr(pipe, "_issue", broken)
    with pytest.raises(RuntimeError, match="could not be written"):
        state_authors(pipe, aid, ["Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF)
    assert pipe.store.article(aid) == before
    [doc] = [d for d in pipe.store.documents() if d.article_id == aid]
    assert "authors" not in doc.declared and not any("STATED" in h for h in doc.history)
    failed = max(pipe.store.runs(), key=lambda r: r.started_at)
    assert failed.mode == "author" and failed.status is RunStatus.FAILED


def test_a_wrong_name_is_retracted_never_left_beside_the_right_one(tmp_path: Path) -> None:
    pipe, aid, upload_run = _authorless(tmp_path)
    state_authors(pipe, aid, ["Morgan Stanly"], by=WHO, reason=WHY, as_of=AS_OF)  # a typo
    run, art = retract_author(pipe, aid, "morgan stanly", by=WHO, reason="test: a typo",
                              as_of=AS_OF)
    assert art.authors == () and art.authors_status is FieldStatus.UNKNOWN  # QA says so again
    assert not _author_check(pipe, upload_run)[0]
    [doc] = [d for d in pipe.store.documents() if d.article_id == aid]
    assert "authors" not in doc.declared  # a replay will not state it again
    assert f"AUTHOR RETRACTED by {WHO}: morgan stanly — test: a typo (run {run.run_id})" in \
        doc.history[-1]
    [issue] = [i for i in pipe.store.issues(run_id=run.run_id) if i.code == "AUTHORS_RETRACTED"]
    assert issue.ref_id == aid
    check = next(c for c in run_qa(pipe.store, run.run_id).checks
                 if c.name == "every stated author is on its article")
    assert check.ok
    state_authors(pipe, aid, ["Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF)
    assert _author_check(pipe, upload_run)[0]


@pytest.mark.parametrize(("name", "why"), [
    ("Nobody Here", "does not credit Nobody Here — nothing retracted"),
    ("Test Author", "from the page"),  # the scan's article credits it from its metadata
])
def test_a_retraction_is_refused_unless_the_operator_stated_the_name(
        tmp_path: Path, name: str, why: str) -> None:
    pipe, _aid, _run = _authorless(tmp_path)
    scan_article = next(a for a in pipe.store.articles() if a.authors)
    runs = len(pipe.store.runs())
    with pytest.raises(AttributionError, match=why):
        retract_author(pipe, scan_article.article_id, name, by=WHO, reason=WHY, as_of=AS_OF)
    assert len(pipe.store.runs()) == runs and pipe.store.article(
        scan_article.article_id) == scan_article


def test_an_author_stated_at_upload_can_be_retracted(tmp_path: Path) -> None:
    """`--author` at upload is an operator statement too (no run link): retractable."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    from vinci.theme_intelligence.ingest import ingest_file

    res = ingest_file(pipe, MS_PDF, Declared(source_id="ms_research", llm_permitted=True,
                                             authors=("Erin Wrigth",)),
                      as_of=AS_OF, fixture=_ms_ext())
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert res.article_id is not None
    art = pipe.store.article(res.article_id)
    assert art is not None and [(a.name, a.stated_in) for a in art.authors] == [
        ("Erin Wrigth", None)]
    _run2, after = retract_author(pipe, res.article_id, "Erin Wrigth", by=WHO,
                                  reason="test: a typo at upload", as_of=AS_OF)
    assert after.authors == ()
    [doc] = [d for d in pipe.store.documents() if d.article_id == res.article_id]
    assert Declared.recorded(doc.source_id, doc.declared).authors == ()


def test_qa_reads_the_run_link_and_names_the_three_linkless_runs(tmp_path: Path) -> None:
    """QA links a statement to its run structurally (`Author.stated_in`). An operator-stated
    author with no link passes only for the three runs made before the link existed."""
    pipe, aid, _run = _authorless(tmp_path)
    art = pipe.store.article(aid)
    assert art is not None
    legacy = art.model_copy(update={"authors": (Author(
        name="Morgan Stanley", source_field=f"{OPERATOR_STATED} by {WHO} in run X: {WHY}"),),
        "authors_status": FieldStatus.KNOWN})
    pipe.store.upsert_article(legacy)
    for rid, ok in (("R-20261022T035402Z-author", True), ("R-20990101T000000Z-author", False)):
        assert rid in LINKLESS_RUNS or not ok
        pipe.store.add_issue(_issue(rid, "article", aid, IssueSeverity.INFO, "AUTHORS_STATED",
                                    f"Morgan Stanley — stated by {WHO}: {WHY}"))
        assert (check_authors(pipe.store, rid) == []) is ok, rid


def test_a_report_rendered_again_never_shows_an_author_stated_later(tmp_path: Path) -> None:
    pipe, aid, upload_run = _authorless(tmp_path)
    up = pipe.store.run(upload_run)
    assert up is not None
    tid = next(c.thesis_id for c in pipe.store.contributions() if c.article_id == aid)
    state_authors(pipe, aid, ["Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF)
    then = _sources_line(pipe.store, tid, {upload_run}, until=up.finished_at)
    now = _sources_line(pipe.store, tid, {upload_run})
    assert then and "author UNKNOWN" in then[0] and "Morgan Stanley — Morgan Stanley" in now[0]
    d = build_dashboard(pipe.store, upload_run, cards={}, generated="t")
    lines = [x for rows in d.categories.values() for r in rows if r.thesis_id == tid
             for x in r.sources]
    assert lines and all("author UNKNOWN" in x for x in lines)  # the upload's own week, as then


def test_a_name_holding_the_separator_is_refused_everywhere(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pipe, aid, _run = _authorless(tmp_path)
    with pytest.raises(AttributionError, match="may not contain ';'"):
        state_authors(pipe, aid, ["Research; Morgan Stanley"], by=WHO, reason=WHY, as_of=AS_OF)
    with pytest.raises(DocumentError, match="may not contain ';'"):
        Declared(source_id="ms_research", authors=("Research; Morgan Stanley",))
    data = str(pipe.paths.root)
    pipe.store.close()
    with pytest.raises(SystemExit) as exit_:
        main(["--data-dir", data, "author", "--article", aid, "--name", "A; B", "--by", WHO,
              "--reason", WHY])
    assert exit_.value.code == 2 and "may not contain ';'" in capsys.readouterr().err


def test_a_template_placeholder_is_never_an_author(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Review of #775: the Uploads rows taught `--author "<as printed>"` — quoted, the shell
    passes a forgotten placeholder through, and the upload credited it. Refused at the CLI's
    `--author` / `--name` / `--retract` (exit 2); a real name with angle brackets inside passes."""
    pipe, aid, _run = _authorless(tmp_path)
    data = str(pipe.paths.root)
    pipe.store.close()
    for argv in (["author", "--article", aid, "--name", "<as printed>", "--by", WHO,
                  "--reason", WHY],
                 ["author", "--article", aid, "--retract", " <name> ", "--by", WHO,
                  "--reason", WHY],
                 ["upload", "--path", "x.pdf", "--source", "ms_research", "--budget", "1",
                  "--author", "<as printed>"]):
        with pytest.raises(SystemExit) as exit_:
            main(["--data-dir", data, *argv])
        assert exit_.value.code == 2 and "is a placeholder" in capsys.readouterr().err
    assert main(["--data-dir", data, "author", "--article", aid, "--name", "Morgan <MS> Stanley",
                 "--by", WHO, "--reason", WHY]) == 0  # NEGATIVE: not a whole-name placeholder


def test_an_author_without_a_run_link_serializes_as_before() -> None:
    """Every stored author predating `stated_in` — page, text and upload credits — keeps its
    payload byte for byte; the field is written only when set."""
    page = Author(name="Erin Wright", source_field="article text b001: 'Author Erin Wright'")
    assert page.model_dump_json() == ('{"name":"Erin Wright","title":null,"source_field":'
                                      '"article text b001: \'Author Erin Wright\'"}')
    linked = Author(name="Morgan Stanley", source_field=OPERATOR_STATED, stated_in="R-1")
    assert '"stated_in":"R-1"' in linked.model_dump_json()
    assert Author.model_validate_json(linked.model_dump_json()) == linked
