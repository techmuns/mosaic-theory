"""State sync and dates — the PR #703 review findings O15-O18
(`docs/records/2026-10-14-theme-intelligence-open-review-findings.md`).

- O15 a `state pull` replay is answered by the extraction the document was first given, never
  asked again under the registry context the pull rebuilt;
- O16 `ingest-file --release` keeps the licence and the arrival the record holds;
- O17 a push builds only on the commit it checked;
- O18 a publication instant is compared with the (UTC) as-of by its UTC day, and a document
  refused as published after one run's as-of is analysed by a later run.

Documents are the SYNTHETIC fixtures (see synthetic_documents/README.md); articles are
HYPOTHETICAL and labelled; extractions use the REAL types; the remote is a LOCAL bare repository.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_ingestion import MS_HTML, _ms
from tests.test_theme_intelligence_long_articles import _listed
from tests.test_theme_intelligence_state_sync import AS_OF, MEMORY, MS_PDF, _bare, _ms_ext, _scan
from tests.theme_intelligence_support import (
    JPM_DIR,
    FrozenSecHttp,
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
)
from vinci.theme_intelligence import state
from vinci.theme_intelligence.config import EXTRACT_PROMPT_VERSION, load_sources, load_taxonomy
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.extract import run_extraction
from vinci.theme_intelligence.ingest import ingest_file
from vinci.theme_intelligence.parse import parse_document
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.qa import run_qa
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.securities import SecResolver
from vinci.theme_intelligence.store import Store


class LiveNetworkError(BaseException):
    """A BaseException on purpose: a broad `except Exception` must not swallow it."""


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def refuse(self: Any, request: Any) -> Any:
        raise LiveNetworkError(f"live network request in an offline test: {request.url}")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)


class CountingLlm:
    """A scripted model: pass 1 answers with a fixed extraction, pass 1b accounts for every gap
    it is asked about (immaterial, with a reason). Every call is counted."""

    model = "claude-opus-4-8"

    def __init__(self, pass1: dict[str, Any]) -> None:
        self.pass1 = pass1
        self.calls: list[str] = []
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self.last_usage = {"input_tokens": 1000, "output_tokens": 400}
        self.calls.append(tool["name"])
        if tool["name"] == "record_article_evidence":
            return self.pass1
        gaps = _listed(user)
        return {"figure_reviews": [{"figure_id": g, "verdict": "immaterial", "claim_ids": [],
                                    "reason": "test: not decision-relevant"}
                                   for g in sorted(gaps) if "#" in g],
                "block_reviews": [{"block_id": g, "verdict": "immaterial", "hypothesis_ids": [],
                                   "claim_ids": [], "reason": "test: not decision-relevant"}
                                  for g in sorted(gaps) if "#" not in g],
                "added_claims": [], "added_mentions": [], "hypothesis_additions": [],
                "added_hypotheses": [], "added_risks": []}


def _with_model(root: Path, fake: CountingLlm) -> Pipeline:
    resolver = SecResolver(root / "sec", http=FrozenSecHttp(JPM_DIR))  # type: ignore[arg-type]
    return Pipeline(root / "ti", sources=load_sources(), taxonomy=load_taxonomy(),
                    client=fake, resolver=resolver, review=False)


def _memory_scan(pipe: Pipeline) -> None:
    """A scan on the branch whose thesis the laptop never saw (a new registry-context line)."""
    pipe.start_run("scan", as_of=AS_OF, window_from=date(2026, 10, 2), window_to=AS_OF)
    text = ("[HYPOTHETICAL] HBM contract prices rose 18% QoQ in 3Q26 as AI accelerator demand "
            "absorbed new capacity, in this invented note.")
    art = Hypo(slug="hbm-prices", publisher="Hypothetical Memory Research",
               published=date(2026, 10, 7), blocks=[("paragraph", text)])
    quote = "HBM contract prices rose 18% QoQ in 3Q26"
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", quote, "HBM +18% QoQ in 3Q26", metric="HBM contract price change",
               value=18, value_text="18%", unit="%", period="3Q26")],
        [hyp("h1", "HBM pricing keeps rising", node=MEMORY, mechanism="pricing_cycle",
             geography="Global", supporting=["c1"])]), as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)


# --- O15 ---------------------------------------------------------------------------------------

def _reanalysed_ext() -> dict[str, Any]:
    ext = _ms_ext()
    ext["hypotheses"][0]["title"] = "On-site generation follows AI power demand (re-analysed)"
    return ext


def test_a_replay_is_answered_by_the_analysis_the_document_was_last_given(
        tmp_path: Path) -> None:
    """The extraction request carries the registry's theses as alignment context. A pull
    rebuilds the registry from the branch, so the replay's request differed from the original
    — it paid again and stored a different analysis of the same document."""
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    local_root = tmp_path / "laptop" / "ti"
    state.pull(local_root, remote)
    first = CountingLlm(_ms_ext())
    laptop = _with_model(tmp_path / "laptop", first)
    laptop.start_run("ingest", as_of=AS_OF)
    up = ingest_file(laptop, MS_PDF, Declared(source_id="ms_research", llm_permitted=True),
                     as_of=AS_OF)
    laptop.finish_run(RunStatus.SUCCEEDED)
    assert up.status == "INGESTED" and first.calls.count("record_article_evidence") == 1
    laptop.store.close()
    # outside a replay the registry context decides: a re-analysis asks anew (its context now
    # holds the upload's own thesis), and its answer is the document's latest analysis
    second = CountingLlm(_reanalysed_ext())
    laptop = _with_model(tmp_path / "laptop", second)
    laptop.run_reanalyse(article_ids=[up.article_id or ""], retire=[], reason="test",
                         as_of=AS_OF)
    assert second.calls.count("record_article_evidence") == 1
    latest = laptop.store.extraction_ids(up.version_id or "")[-2:]  # pass 1b and pass 1
    laptop.store.close()
    _memory_scan(actions)  # the branch moves: a thesis the laptop's requests never listed
    state.push(actions.paths.root, remote)

    replay = CountingLlm(_ms_ext())
    res = state.pull(local_root, remote, force=True,  # the re-analysis run is not replayable
                     make_pipeline=lambda: _with_model(tmp_path / "laptop", replay))
    assert any(up.doc_id in x and "replayed — INGESTED" in x for x in res.lines), res.lines
    assert replay.calls == []  # neither pass 1 nor pass 1b asked again
    assert any("every model answer from the cache, $0" in x for x in res.lines), res.lines
    extract_cache = list((local_root / "llm_cache" / "extract").glob("*.json"))
    assert len(extract_cache) == 2  # the upload's answer and the re-analysis's — no third
    again = Store(local_root / "registry.db")
    assert sorted(again.extraction_ids(up.version_id or "")) == sorted(latest)
    assert any(t.title == "On-site generation follows AI power demand (re-analysed)"
               for t in again.theses())
    again.close()


def _keep_answer(cache: Path, key: str, *, model: str = "claude-opus-4-8",
                 version: str = EXTRACT_PROMPT_VERSION, name: str | None = None) -> None:
    d = cache / "extract"
    d.mkdir(parents=True, exist_ok=True)
    (d / (name or f"{key}.json")).write_text(json.dumps({
        "model": model, "prompt_version": version, "usage": None, "seconds": 0.0,
        "output": _ms_ext()}))


@pytest.mark.parametrize(("kept", "reused"), [
    ({}, True),  # the answer the id names, as written by the run that paid for it
    ({"name": "set-aside"}, True),  # an answer set aside beside it is not a second answer
    ({"model": "claude-other"}, False),  # another model's answer is another request
    ({"version": "ti-extract-0"}, False),  # so is an earlier prompt's
])
def test_a_replay_reuses_only_the_answer_its_id_names(
        tmp_path: Path, kept: dict[str, str], reused: bool) -> None:
    key = "0123456789abcdef" + "0" * 48
    if kept.get("name") == "set-aside":
        _keep_answer(tmp_path, key)
        _keep_answer(tmp_path, key, name=f"{key}.invalid-1.json")
    else:
        _keep_answer(tmp_path, key, **kept)
    doc = Hypo(slug="ms", publisher="Hypothetical", published=AS_OF,
               blocks=[("paragraph", "[HYPOTHETICAL] text")]).doc()
    fake = CountingLlm(_ms_ext())
    res = run_extraction(doc, publisher="Hypothetical", as_of=AS_OF.isoformat(),
                         taxonomy=load_taxonomy(), client=fake,
                         cache_dir=tmp_path, reuse=["X-0123456789abcdef"])
    assert (res.extraction_id == "X-0123456789abcdef" and res.cached) is reused
    assert fake.calls == ([] if reused else ["record_article_evidence"])


# --- O16 ---------------------------------------------------------------------------------------

VIA = "linked report fetched automatically from https://example.test/synthetic/teaser"


def _linked_report_in_review(tmp_path: Path) -> tuple[Path, str, str]:
    """A linked report (recorded licence and arrival) that went to REVIEW on a pulled registry:
    (data dir, document id, the article it is a fuller version of)."""
    a = make_pipeline(tmp_path / "a")
    a.start_run("ingest", as_of=AS_OF)
    first = ingest_file(a, MS_PDF, _ms(), as_of=AS_OF, fixture=_ms_ext())
    a.finish_run(RunStatus.SUCCEEDED)
    a.store.export_jsonl(tmp_path / "branch")
    a.store.close()
    data = tmp_path / "b" / "ti"
    data.mkdir(parents=True)
    Store.import_jsonl(tmp_path / "branch", data / "registry.db").close()
    b = make_pipeline(tmp_path / "b")
    b.start_run("ingest", as_of=AS_OF)
    held = ingest_file(b, MS_HTML, replace(_ms(), via=VIA), as_of=AS_OF, fixture=_ms_ext())
    b.finish_run(RunStatus.SUCCEEDED)
    assert held.status == "REVIEW"  # the pulled registry holds no text to compare
    b.store.close()
    return data, held.doc_id, first.article_id or ""


def _release(data: Path, doc_id: str, same_as: str, *flags: str) -> Any:
    import vinci.theme_intelligence.__main__ as cli

    assert cli.main(["--data-dir", str(data), "ingest-file", "--release", doc_id, "--same-as",
                     same_as, "--as-of", AS_OF.isoformat(), "--no-review", *flags]) == 0
    [rec] = [d for d in Store(data / "registry.db").documents() if d.doc_id == doc_id]
    return rec


def test_a_release_keeps_the_licence_and_the_arrival_the_record_holds(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`ingest-file --release` rebuilt the statements without the recorded licence and without
    `via`: a linked report released from REVIEW was HELD again for its licence, and its record
    then read as a manual upload."""
    import vinci.theme_intelligence.__main__ as cli

    monkeypatch.setattr(cli, "_client", lambda required=False: CountingLlm(_ms_ext()))
    rec = _release(*_linked_report_in_review(tmp_path))
    assert rec.status == "UPGRADED", rec.history
    assert rec.declared.get("via") == VIA and rec.declared.get("llm_permitted") == "True"
    assert "own page links to" in rec.match_basis  # read as the linked report it is


def test_the_operators_licence_statement_overrides_the_recorded_one(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import vinci.theme_intelligence.__main__ as cli

    fake = CountingLlm(_ms_ext())
    monkeypatch.setattr(cli, "_client", lambda required=False: fake)
    data, doc_id, same_as = _linked_report_in_review(tmp_path)
    rec = _release(data, doc_id, same_as, "--llm-not-permitted")
    assert rec.status == "HELD" and fake.calls == []
    assert rec.declared.get("via") == VIA  # the arrival is still the record's


# --- O17 ---------------------------------------------------------------------------------------

def test_a_push_builds_only_on_the_commit_it_checked(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Another machine's push landing between the head check and the clone was overwritten by a
    "fast-forward" from a base this registry never saw."""
    remote = _bare(tmp_path)
    actions = make_pipeline(tmp_path / "actions")
    _scan(actions, "week-1")
    state.push(actions.paths.root, remote)
    local_root = tmp_path / "laptop" / "ti"
    state.pull(local_root, remote)
    checked = state.remote_head(remote)
    _scan(actions, "week-2")  # the other machine pushes …
    state.push(actions.paths.root, remote)
    moved = state.remote_head(remote)
    assert moved != checked
    real = state.remote_head
    seen: list[str] = []

    def stale_then_real(r: str, branch: str = state.BRANCH) -> str | None:
        seen.append(r)  # … after this push's check, before its clone
        return checked if len(seen) == 1 else real(r, branch)
    monkeypatch.setattr(state, "remote_head", stale_then_real)
    with pytest.raises(state.StateSyncError, match="moved during this push"):
        state.push(local_root, remote)
    assert real(remote) == moved  # the other push stands
    monkeypatch.undo()
    with pytest.raises(state.StateSyncError, match="branch moved since your last pull"):
        state.push(local_root, remote)  # unraced, the check itself refuses


# --- O18 ---------------------------------------------------------------------------------------

def _taipei_page(stamp: str) -> Any:
    body = "".join(
        f"<p>[SYNTHETIC TEST FIXTURE] Conventional DRAM contract prices are projected to rise "
        f"12% QoQ in 4Q26 in this invented note, paragraph {i}, written only to test a "
        f"publication stamp given in another time zone than the run's as-of.</p>"
        for i in range(12))
    html = (f'<html><head><title>Synthetic Taipei Memory Note</title><meta property='
            f'"article:published_time" content="{stamp}"></head><body><main><h1>Synthetic '
            f'Taipei Memory Note</h1>{body}</main></body></html>')
    return parse_document(html, "https://example.test/hypothetical/taipei-note")


def _taipei_ext() -> dict[str, Any]:
    q = "Conventional DRAM contract prices are projected to rise 12% QoQ in 4Q26"
    return extraction([claim("c1", "b002", q, "DRAM +12% QoQ in 4Q26", kind="forecast",
                             epistemic="forecast", metric="DRAM contract price change",
                             value=12, value_text="12%", unit="%", period="4Q26")],
                      [hyp("h1", "DRAM pricing keeps rising", node=MEMORY,
                           mechanism="pricing_cycle", geography="Global", supporting=["c1"])])


def test_a_stamp_in_another_time_zone_is_compared_by_its_utc_day(tmp_path: Path) -> None:
    """02:00 on 12 October in Taipei is 18:00 on 11 October UTC: on a run as of 11 October it
    was refused as published after the as-of — by its own clock's date."""
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("ingest", as_of=AS_OF)
    doc = _taipei_page("2026-10-12T02:00:00+08:00")
    res = ingest(pipe, doc, _taipei_ext(), as_of=AS_OF, publisher="Hypothetical Taipei Research")
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert res.status == "PROCESSED", res.note
    qa = {c.name: c for c in run_qa(pipe.store, run.run_id).checks}
    assert qa["no look-ahead past the run's as-of"].ok  # QA reads the same day
    # an instant on the next UTC day is still after the as-of
    late = _taipei_page("2026-10-12T09:00:00+08:00")
    other = make_pipeline(tmp_path / "late")
    other.start_run("ingest", as_of=AS_OF)
    assert ingest(other, late, _taipei_ext(), as_of=AS_OF).status == "LOOKAHEAD"


def test_a_document_refused_as_too_new_is_analysed_by_a_later_run(tmp_path: Path) -> None:
    """A refusal as published after the as-of is not an analysis: the same file imported by a
    later run was a DUPLICATE of its own refusal, refused for good."""
    note = tmp_path / "future-memory-note.md"
    note.write_text("---\ntitle: Synthetic Memory Note From Next Week\ndate: 2026-10-13\n---\n\n"
                    "[SYNTHETIC TEST FIXTURE — invented content]\n\nConventional DRAM contract "
                    "prices are projected to rise 12% QoQ in 4Q26 in this invented note, which "
                    "exists only to test that a document dated after one run's as-of is "
                    "analysed by a later run instead of being refused for good.\n")
    ext = extraction([claim("c1", "b002", "Conventional DRAM contract prices are projected to "
                                          "rise 12% QoQ in 4Q26", "DRAM +12% QoQ in 4Q26",
                            kind="forecast", epistemic="forecast",
                            metric="DRAM contract price change", value=12, value_text="12%",
                            unit="%", period="4Q26")],
                     [hyp("h1", "DRAM pricing keeps rising", node=MEMORY,
                          mechanism="pricing_cycle", geography="Global", supporting=["c1"])])
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    early = ingest_file(pipe, note, _ms(), as_of=AS_OF, fixture=ext)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert early.status == "LOOKAHEAD"
    later = date(2026, 10, 14)
    pipe.start_run("ingest", as_of=later)
    res = ingest_file(pipe, note, _ms(), as_of=later, fixture=ext)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert res.status == "INGESTED", res.note
    assert pipe.store.theses()
    # an analysed document is still a duplicate of itself
    pipe.start_run("ingest", as_of=later)
    assert ingest_file(pipe, note, _ms(), as_of=later, fixture=ext).status == "DUPLICATE"
