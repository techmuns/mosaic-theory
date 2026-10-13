"""ONE registry, ONE weekly report — manual documents and scheduled scans together.

- The week's report: a scan's dashboard takes in the manual-ingest runs since the previous scan
  — one ranked list, each row saying how its evidence arrived, the three dates kept apart.
- Research Intake / Manual Action: the six lists, each with its population.
- State sync against a LOCAL bare git repository standing in for the GitHub remote: pull, push
  (fast-forward only), replay of unpushed documents, refusals, and nothing but derived JSONL
  crossing. (GitHub itself is not exercised here — the record says so.)
- QA on an imported registry: a claim whose text is not held is "not re-checkable here", never
  re-verified.

Documents are the SYNTHETIC fixtures (see synthetic_documents/README.md); articles are
HYPOTHETICAL and labelled; extractions use the REAL types.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import (
    FIXTURES,
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
)
from vinci.theme_intelligence import state
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.extract import Extraction
from vinci.theme_intelligence.ingest import ingest_file
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.qa import run_qa
from vinci.theme_intelligence.report import (
    build_dashboard,
    dates_line,
    render_dashboard_html,
    render_dashboard_md,
    report_runs,
)
from vinci.theme_intelligence.schemas import HealthStatus, RunStatus, SourceHealthCheck
from vinci.theme_intelligence.store import Store

SYN = FIXTURES / "synthetic_documents"
MS_PDF = SYN / "ms_report_synthetic.pdf"
AS_OF = date(2026, 10, 11)
GRID = "ai_infrastructure.power_grid"
MEMORY = "ai_infrastructure.memory"


class LiveNetworkError(BaseException):
    """A BaseException on purpose: a broad `except Exception` must not swallow it."""


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def refuse(self: Any, request: Any) -> Any:
        raise LiveNetworkError(f"live network request in an offline test: {request.url}")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)


def _ok(ext: dict[str, Any]) -> dict[str, Any]:
    Extraction.model_validate(ext)
    return ext


def _ms_ext() -> dict[str, Any]:
    c1 = claim("c1", "b009", "On-site gas turbine orders are projected to grow 30% in 2027",
               "On-site gas turbine orders +30% in 2027", kind="forecast", epistemic="forecast",
               metric="on-site gas turbine order growth", value=30, value_text="30%", unit="%",
               period="2027")
    return _ok(extraction([c1], [hyp("h1", "AI power demand moves generation on-site",
                                     node=GRID, mechanism="demand_volume_shift", geography="US",
                                     supporting=["c1"])]))


def _old_note(tmp: Path) -> Path:
    """A SYNTHETIC report printed with a date a month before it is uploaded."""
    p = tmp / "old-memory-note.md"
    p.write_text("---\ntitle: Synthetic Memory Note From September\ndate: 2026-09-10\n---\n\n"
                 "[SYNTHETIC TEST FIXTURE — invented content]\n\nConventional DRAM contract "
                 "prices are projected to rise 12% QoQ in 4Q26 in this invented note, which "
                 "exists only to test that an old report uploaded today keeps its own date and "
                 "is never shown as newly published, whatever day it reaches the registry.\n")
    return p


def _old_ext() -> dict[str, Any]:
    c1 = claim("c1", "b002", "Conventional DRAM contract prices are projected to rise 12% QoQ "
                             "in 4Q26", "Conventional DRAM +12% QoQ in 4Q26", kind="forecast",
               epistemic="forecast", metric="conventional DRAM contract price change",
               value=12, value_text="12%", unit="%", period="4Q26")
    return _ok(extraction([c1], [hyp("h1", "DRAM pricing keeps rising", node=MEMORY,
                                     mechanism="pricing_cycle", geography="Global",
                                     supporting=["c1"])]))


def _scan_article(pipe: Pipeline, slug: str = "scan-article",
                  publisher: str = "Hypothetical Grid Research") -> None:
    text = (f"Large-load interconnection requests in the US rose 110% in 2026 on AI demand "
            f"({slug}).")
    art = Hypo(slug=slug, publisher=publisher, published=date(2026, 10, 6),
               blocks=[("paragraph", text)])
    quote = "Large-load interconnection requests in the US rose 110% in 2026 on AI demand"
    ext = _ok(extraction([claim("c1", "b001", quote, "Requests +110% in 2026",
                                metric="large-load requests", value=110, value_text="110%",
                                unit="%", period="2026")],
                         [hyp("h1", "Grid queues lengthen", node=GRID, mechanism="supply_"
                              "constraint", geography="US", supporting=["c1"])]))
    ingest(pipe, art.doc(), ext, as_of=AS_OF, publisher=art.publisher)


def _upload(pipe: Pipeline, path: Path, ext: dict[str, Any], source: str = "ms_research",
            **kw: Any) -> Any:
    pipe.start_run("ingest", as_of=AS_OF)
    res = ingest_file(pipe, path, Declared(source_id=source, llm_permitted=True, **kw),
                      as_of=AS_OF, fixture=ext)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return res


def _scan(pipe: Pipeline, slug: str = "scan-article",
          publisher: str = "Hypothetical Grid Research") -> str:
    run = pipe.start_run("scan", as_of=AS_OF, window_from=date(2026, 10, 2), window_to=AS_OF)
    _scan_article(pipe, slug, publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return run.run_id


# --- the week's ONE report ---------------------------------------------------------------------

def test_the_weekly_report_takes_in_manual_runs_since_the_previous_scan(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    first_scan = _scan(pipe, "first-scan")
    up = _upload(pipe, MS_PDF, _ms_ext())
    old = _upload(pipe, _old_note(tmp_path), _old_ext(), source="semianalysis")
    scan = _scan(pipe, "second-scan", "Hypothetical Utility Research")  # an independent origin
    run = pipe.store.run(scan)
    assert run is not None
    ids = [r.run_id for r in report_runs(pipe.store, run)]
    assert ids[-1] == scan and first_scan not in ids and len(ids) == 3  # 2 uploads + the scan
    d = build_dashboard(pipe.store, scan, cards={}, generated="test")
    rows = {r.thesis_id: r for rs in d.categories.values() for r in rs}
    manual_rows = [r for r in rows.values() if any("manual upload" in x for x in r.intake)]
    assert {r.title for r in manual_rows} == {"AI power demand moves generation on-site",
                                              "DRAM pricing keeps rising"}
    assert any(x.startswith("automatic (") for r in rows.values() for x in r.intake)
    # three dates, never conflated: the September note uploaded today is not "published today"
    [dram] = [r for r in manual_rows if r.title == "DRAM pricing keeps rising"]
    assert dram.article_date == "2026-09-10"
    assert dates_line(dram).startswith("Published 2026-09-10")
    today = datetime.now(tz=UTC).date().isoformat()
    [line] = [x for x in d.intake["manual"]["items"] if old.doc_id in x]
    assert "published 2026-09-10 (Markdown front matter (date))" in line
    assert f"uploaded {today}" in line and "analysed as of 2026-10-11" in line
    assert d.intake["manual"]["total"] == 2 and up.doc_id in " ".join(d.intake["manual"]["items"])
    assert d.kpi["manually_imported"] == 2
    # verification covers the report's runs and says so — never "this run" for three
    assert "this report's 3 runs analysed" in d.verification["summary"]
    html, md = render_dashboard_html(d), render_dashboard_md(d)
    assert "Research intake / manual action" in html and "How this evidence arrived" in html
    assert "## Research intake / manual action" in md
    # the next scan's report does not take them in again
    nxt = _scan(pipe, "third-scan")
    nrun = pipe.store.run(nxt)
    assert nrun is not None and [r.run_id for r in report_runs(pipe.store, nrun)] == [nxt]


def test_the_intake_lists_what_needs_a_human(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.store.add_health_check(SourceHealthCheck(
        check_id="SH-test-gs", source_id="gs_research", publisher="Goldman Sachs",
        checked_at=datetime(2026, 10, 11, 6, 0, tzinfo=UTC), trigger="manual",
        status=HealthStatus.BLOCKED, reason="access denied (HTTP 403) (test)",
        next_action="manual upload", expect_blocked=True))
    pipe.store.upsert_candidate("https://newsletter.semianalysis.com/p/x",
                                "semianalysis", "UNDATED",
                                {"source_id": "semianalysis", "title": "An undated insight",
                                 "note": "the page states no publication date — VERIFY"})
    # a RETIRED channel's historical row is never asked about again
    pipe.store.upsert_candidate("https://business.bofa.com/en-us/content/y.html",
                                "bofa_institutional", "UNDATED",
                                {"source_id": "bofa_institutional", "title": "A retired insight",
                                 "note": "the page states no publication date"})
    pipe.start_run("ingest", as_of=AS_OF)
    held = ingest_file(pipe, MS_PDF, Declared(source_id="ms_research"), as_of=AS_OF)
    pipe.finish_run(RunStatus.SUCCEEDED)
    scan = _scan(pipe)
    d = build_dashboard(pipe.store, scan, cards={}, generated="test")
    it = d.intake
    meta = " ".join(it["needs_metadata"]["items"])
    assert "An undated insight" in meta and "VERIFY" in meta
    assert "A retired insight" not in meta
    assert "HELD (licence not confirmed" in meta and held.doc_id in meta
    assert any(x.startswith("Goldman Sachs: BLOCKED") for x in it["publishers"]["items"])
    assert any(x.startswith("Goldman Sachs: coverage UNKNOWN") and "NOT evidence" in x
               for x in it["coverage_gaps"]["items"])
    assert it["manual"]["total"] == 1 and "HELD" in it["manual"]["items"][0]
    for key in ("automatic", "manual", "awaiting_documents", "publishers", "needs_upload",
                "needs_metadata", "coverage_gaps"):
        assert it[key]["total"] == len(it[key]["items"])  # every entry kept; the page truncates


# --- QA on an imported registry ----------------------------------------------------------------

def test_qa_never_counts_text_it_does_not_hold_as_reverified(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path / "a")
    up = _upload(pipe, MS_PDF, _ms_ext())
    rid = pipe.store.contributions(article_id=up.article_id)[0].run_id
    here = run_qa(pipe.store, rid)
    spans = next(c for c in here.checks if c.name == "spans re-found in stored article text")
    assert spans.ok and "1 of 1 verified claim(s)" in spans.detail and "NOT re" not in spans.detail
    pipe.store.export_jsonl(tmp_path / "x")
    there = Store.import_jsonl(tmp_path / "x", tmp_path / "b.db")
    spans2 = next(c for c in run_qa(there, rid).checks
                  if c.name == "spans re-found in stored article text")
    assert spans2.ok  # not a failure …
    assert "0 of 1 verified claim(s)" in spans2.detail  # … and never counted as re-checked
    assert "1 NOT re-checkable here" in spans2.detail


# --- state sync against a local bare repository -----------------------------------------------

def _bare(tmp: Path) -> str:
    remote = tmp / "remote.git"
    subprocess.run(["git", "init", "--quiet", "--bare", str(remote)], check=True)
    return str(remote)


def _branch_files(remote: str, tmp: Path) -> list[str]:
    co = tmp / "inspect"
    if co.exists():
        shutil.rmtree(co)
    subprocess.run(["git", "clone", "--quiet", "--branch", state.BRANCH, remote, str(co)],
                   check=True)
    return sorted(str(p.relative_to(co)) for p in co.rglob("*") if p.is_file()
                  and ".git" not in p.parts)


def test_pull_ingest_push_then_the_scheduled_scan_reports_it(tmp_path: Path) -> None:
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")  # the scheduled run's registry
    _scan(actions, "week-1")
    res = state.push(actions.paths.root, remote)
    assert res.new_commit and "fast-forward from nothing" in res.lines[0]
    files = _branch_files(remote, tmp_path)
    assert files and all(f.startswith("registry/") and f.endswith(".jsonl") for f in files)
    # the operator's machine: pull, upload, push
    local_root = tmp_path / "laptop" / "ti"
    pulled = state.pull(local_root, remote)
    assert any("rebuilt from" in x for x in pulled.lines)
    laptop = make_pipeline(tmp_path / "laptop")
    assert {r.run_id for r in laptop.store.runs()} == {r.run_id for r in actions.store.runs()}
    up = _upload(laptop, MS_PDF, _ms_ext())
    laptop.store.close()
    state.push(local_root, remote)
    # the scheduled run may not overwrite it: its base is stale
    with pytest.raises(state.StateSyncError, match="branch moved since your last pull"):
        state.push(actions.paths.root, remote)
    # … it restores the branch, as the workflow does, and its scan reports the upload
    actions.store.close()
    state.pull(actions.paths.root, remote, replay=False, force=True)
    restored = make_pipeline(tmp_path / "actions")
    scan = _scan(restored, "week-2")
    d = build_dashboard(restored.store, scan, cards={}, generated="test")
    [line] = d.intake["manual"]["items"]
    assert up.doc_id in line and "original NOT on this machine" in line
    assert any("manual upload" in x for rs in d.categories.values() for r in rs
               for x in r.intake)
    # nothing but derived JSONL crossed — and no article text in it
    files = _branch_files(remote, tmp_path)
    assert not [f for f in files if not f.endswith(".jsonl")]
    av = (tmp_path / "inspect" / "registry" / "article_versions.jsonl").read_text()
    assert all(not b["text"] for ln in av.splitlines()
               for b in json.loads(json.loads(ln)["payload"])["blocks"])


def test_a_pull_replays_the_documents_the_branch_does_not_hold(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    local_root = tmp_path / "laptop" / "ti"
    state.pull(local_root, remote)
    laptop = make_pipeline(tmp_path / "laptop")
    up = _upload(laptop, MS_PDF, _ms_ext())  # not pushed yet …
    first = laptop.store.document(up.doc_id)
    assert first is not None and first.filename == MS_PDF.name
    laptop.store.close()
    _scan(actions, "week-2")  # … and the branch moves meanwhile
    state.push(actions.paths.root, remote)
    with pytest.raises(state.StateSyncError, match="branch moved"):
        state.push(local_root, remote)
    sha = MS_PDF.read_bytes()
    import hashlib

    # the operator accepted this document's cost when it was first analysed: a replay never
    # holds it again, even under a lower limit
    from vinci.theme_intelligence import ingest as ingest_mod
    monkeypatch.setattr(ingest_mod, "DOC_COST_LIMIT_USD", 0.01)
    res = state.pull(local_root, remote, make_pipeline=lambda: make_pipeline(tmp_path / "laptop"),
                     fixtures={hashlib.sha256(sha).hexdigest(): _ms_ext()})
    assert any(up.doc_id in x and "replayed — INGESTED" in x for x in res.lines), res.lines
    again = make_pipeline(tmp_path / "laptop")
    runs = {r.run_id for r in again.store.runs()}
    assert {r.run_id for r in actions.store.runs()} <= runs  # the branch's runs are all here
    [doc] = again.store.documents()
    assert doc.status == "INGESTED" and doc.article_id == up.article_id
    # the replay read the private copy (named by its hash): the name the file ARRIVED with and
    # WHEN it arrived are the original record's (observed 2026-10-11, GitHub state test)
    assert doc.filename == MS_PDF.name and doc.received_at == first.received_at
    again.store.close()
    state.push(local_root, remote)  # now a fast-forward


def test_a_pull_never_silently_discards_local_runs_it_cannot_replay(tmp_path: Path) -> None:
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    laptop = make_pipeline(tmp_path / "laptop")
    _scan(laptop, "local-only-scan")  # a local scan the branch never saw
    laptop.store.close()
    with pytest.raises(state.StateSyncError, match="cannot replay"):
        state.pull(laptop.paths.root, remote)
    res = state.pull(laptop.paths.root, remote, force=True)
    assert any("backed up to" in x for x in res.lines)
    assert list((laptop.paths.root / "backups").glob("registry-*.db"))


def test_a_push_refuses_anything_but_derived_records(tmp_path: Path) -> None:
    tree = tmp_path / "t"
    (tree / "registry").mkdir(parents=True)
    (tree / "registry" / "runs.jsonl").write_text("")
    (tree / "report.pdf").write_bytes(b"%PDF-")
    with pytest.raises(state.StateSyncError, match="forbidden file kind"):
        state._check_tree(tree)
    (tree / "report.pdf").unlink()
    payload = json.dumps({"blocks": [{"block_id": "b001", "text": "licensed sentence"}]})
    (tree / "registry" / "article_versions.jsonl").write_text(
        json.dumps({"payload": payload}) + "\n")
    with pytest.raises(state.StateSyncError, match="article text found"):
        state._check_tree(tree)


def test_a_remote_url_is_never_printed_with_its_credentials() -> None:
    assert state.mask("https://user:tok@github.com/o/r.git") == "https://***@github.com/o/r.git"
    assert state.mask("/srv/state.git") == "/srv/state.git"
