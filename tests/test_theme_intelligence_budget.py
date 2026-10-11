"""Spending limits checked BEFORE every paid model call (budget.py). Measured 2026-10-11: Citi's
60-page Gridlock report cost $46.67 through the pipeline, its LatAm report $9.47, its ETF report
$3.80 — model-processing costs, not publisher fees.

The real pipeline runs here with a scripted model (`FakeLlm`, reporting 1,000 input / 400
output tokens per call) on the hypothetical long article of the long-article tests.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_long_articles import AS_OF, LONG, FakeLlm, _pass1
from tests.theme_intelligence_support import FIXTURES, JPM_DIR, FrozenSecHttp, fetched
from vinci.theme_intelligence.budget import BudgetExceeded, GuardedClient, SpendGuard, call_bound
from vinci.theme_intelligence.config import (
    DOC_RETRY_COMPLETENESS_SHARE,
    LLM_MAX_TOKENS,
    load_sources,
    load_taxonomy,
)
from vinci.theme_intelligence.documents import Declared
from vinci.theme_intelligence.ingest import ingest_file
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.securities import SecResolver

MS_PDF = FIXTURES / "synthetic_documents" / "ms_report_synthetic.pdf"


def _pipe(tmp_path: Path, fake: FakeLlm) -> Pipeline:
    resolver = SecResolver(tmp_path / "sec", http=FrozenSecHttp(JPM_DIR))  # type: ignore[arg-type]
    return Pipeline(tmp_path / "ti", sources=load_sources(), taxonomy=load_taxonomy(),
                    client=fake, resolver=resolver, review=False)  # type: ignore[arg-type]


def _process(pipe: Pipeline, limit: float | None = None) -> Any:
    doc = LONG.doc()
    return pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="manual",
                                 as_of=AS_OF, publisher_override=LONG.publisher,
                                 cost_limit=limit)


# --- the guard ---------------------------------------------------------------------------------

def test_a_call_that_does_not_fit_is_never_sent() -> None:
    fake = FakeLlm(_pass1(bad_items=False))
    guard = SpendGuard(run_limit=0.10)
    client = GuardedClient(fake, guard)
    tool = {"name": "record_article_evidence"}
    with pytest.raises(BudgetExceeded, match="does not fit the remaining"):
        client.extract(system="s", user="u" * 1000, tool=tool)
    assert fake.calls == [] and guard.refusals and guard.run_spent == 0


def test_the_bound_covers_the_output_cap_and_cache_write_input() -> None:
    b = call_bound("claude-opus-4-8", "s" * 250, "u" * 2250, {})
    # 2,502 characters / 2.5 = 1,000.8 tokens at $5 x 1.25; 21,333 output tokens at $25
    assert b == pytest.approx((len("s" * 250 + "u" * 2250 + "{}") / 2.5 * 6.25
                               + LLM_MAX_TOKENS * 25) / 1e6)
    with pytest.raises(BudgetExceeded, match="no price is configured"):
        call_bound("some-other-model", "s", "u", {})


def test_retries_and_completeness_take_only_their_share_of_a_document() -> None:
    g = SpendGuard(run_limit=100.0)
    g.begin_document("A-1", 10.0)
    assert g.classify({"name": "record_article_evidence"}) == "extraction"
    assert g.classify({"name": "record_article_evidence"}) == "retry"  # the compact re-run
    assert g.classify({"name": "record_completeness"}) == "completeness"
    g.record("completeness", 1.0, 8.4)
    left, which = g.remaining("completeness")
    assert left == pytest.approx(10.0 * DOC_RETRY_COMPLETENESS_SHARE - 8.4)
    assert "retry / completeness limit" in which
    assert g.remaining("review")[0] == pytest.approx(10.0 - 8.4)  # reviews keep their share


def test_a_billed_call_that_fails_is_still_counted() -> None:
    fake = FakeLlm(_pass1(bad_items=False), truncate=frozenset({""}))
    guard = SpendGuard(run_limit=100.0)
    client = GuardedClient(fake, guard)
    with pytest.raises(Exception, match="truncated"):
        client.extract(system="s", user="This is part :", tool={"name": "record_completeness"})
    assert len(guard.calls) == 1 and guard.calls[0]["actual_usd"] > 0


# --- through the pipeline: checkpoint, resume without paying twice ----------------------------

def test_a_document_over_its_limit_is_checkpointed_and_resumed_without_repaying(
        tmp_path: Path) -> None:
    # measure the two calls' bounds once, with room
    probe = _pipe(tmp_path / "probe", FakeLlm(_pass1(bad_items=False)))
    probe.start_run("article", as_of=AS_OF)
    _process(probe, limit=100.0)
    bounds = {c["kind"]: c["bound_usd"] for c in probe.guard.calls}
    assert set(bounds) == {"extraction", "completeness"}
    # the extraction fits, the completeness pass does not (its share of the document limit)
    fake = FakeLlm(_pass1(bad_items=False))
    pipe = _pipe(tmp_path / "real", fake)
    run = pipe.start_run("article", as_of=AS_OF)
    limit = bounds["extraction"] + 0.001
    assert bounds["completeness"] > limit * DOC_RETRY_COMPLETENESS_SHARE
    res = _process(pipe, limit=limit)
    assert res.status == "BUDGET_HELD" and "completeness" in res.note
    assert fake.calls == ["extract"]  # the refused call was never sent
    assert pipe.store.theses() == [] and not pipe._applied(res.article_id, res.version_id)
    assert any(i.code == "BUDGET_HELD" for i in pipe.store.issues(run_id=run.run_id))
    done = pipe.finish_run(RunStatus.PARTIAL)
    assert done.spend["refusals"] and done.spend["paid_calls"] == 1
    assert done.spend["calls"][0]["bound_usd"] >= done.spend["calls"][0]["actual_usd"]
    # resumed with the operator's higher limit: the extraction comes from the cache, unpaid
    pipe.start_run("article", as_of=AS_OF)
    again = _process(pipe, limit=100.0)
    assert again.status == "PROCESSED" and fake.calls == ["extract", "complete"]
    assert len(pipe.store.theses()) == 1


def test_a_run_budget_stops_every_further_call(tmp_path: Path) -> None:
    fake = FakeLlm(_pass1(bad_items=False))
    pipe = _pipe(tmp_path, fake)
    pipe.start_run("article", as_of=AS_OF)
    pipe.guard.run_limit = 0.05  # below any call's bound
    assert _process(pipe).status == "BUDGET_HELD" and fake.calls == []


def test_a_supplied_document_over_budget_is_held_with_its_resume_command(tmp_path: Path) -> None:
    fake = FakeLlm(_pass1(bad_items=False))
    pipe = _pipe(tmp_path, fake)
    pipe.start_run("ingest", as_of=date(2026, 10, 11))
    pipe.guard.run_limit = 0.05
    res = ingest_file(pipe, MS_PDF, Declared(source_id="ms_research", llm_permitted=True),
                      as_of=date(2026, 10, 11))
    assert res.status == "HELD" and res.note.startswith("BUDGET:")
    assert f"--release {res.doc_id} --max-cost" in res.note and fake.calls == []
    pipe.guard.run_limit = 100.0
    ok = ingest_file(pipe, MS_PDF, Declared(source_id="ms_research", llm_permitted=True),
                     as_of=date(2026, 10, 11))
    assert ok.status == "INGESTED" and ok.doc_id == res.doc_id


def test_a_scan_stops_at_the_first_refusal_and_queues_the_rest(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.test_theme_intelligence_scan import _fake_scan
    from vinci.theme_intelligence.pipeline import ArticleResult

    pipe = _pipe(tmp_path, FakeLlm(_pass1(bad_items=False)))
    urls = [f"https://example.test/hypothetical/b{i}" for i in range(3)]
    _fake_scan(monkeypatch, pipe, urls)
    seen: list[str] = []

    def held(self: Pipeline, url: str, **kw: Any) -> ArticleResult:
        seen.append(url)
        return ArticleResult(url, "BUDGET_HELD", "A-x", "AV-x", note="the run budget $1.00")

    monkeypatch.setattr(Pipeline, "process_url", held)
    run = pipe.run_scan(window_from=date(2026, 10, 2), window_to=date(2026, 10, 11),
                        as_of=date(2026, 10, 11), max_articles=10, budget=1.0)
    assert len(seen) == 1  # nothing after the first refusal is attempted
    assert run.status is RunStatus.PARTIAL and run.counts["articles_queued"] == 3
    assert any("spend guard: the run budget is exhausted" in w for w in run.warnings)
    assert sorted(u for u, _s, _m in pipe.store.candidates("QUEUED")) == sorted(urls)
