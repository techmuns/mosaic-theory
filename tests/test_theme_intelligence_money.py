"""The spend guard and the paid-call ledger: four verified review leads
(`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`).

- U3: `scan --resume` restarted the guard at $0 — a run that had spent $38.50 of $40 could spend
  another $40, and its manifest then read 0 spent, 0 paid calls.
- U4: a paid call that ended in an exception (a truncated review, a failed completeness pass, a
  truncated enrichment) was counted by the guard and missing from the ledger — the run's
  `cost_usd` read $0.35 for $0.70 billed, $0 for $0.45.
- U26: one report over its OWN limit (its retry / completeness share) was reported as "the run
  budget is exhausted", and every later candidate was queued.
- U29: two refusals of one thesis's review in one run shared one issue id with two payloads —
  StoreIntegrityError, which failed the article (and a scan with it).

The model is a stand-in returning the REAL tools' shapes; the J.P. Morgan article and SEC data are
the authentic frozen fixtures; other articles are HYPOTHETICAL.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_budget import _pipe, _process
from tests.test_theme_intelligence_enrichment import ANSWER, StandIn
from tests.test_theme_intelligence_enrichment import _memory_thesis as _enrichable
from tests.test_theme_intelligence_long_articles import FakeLlm, _pass1
from tests.theme_intelligence_support import (
    JPM_AS_OF,
    JPM_DIR,
    FrozenSecHttp,
    fetched,
    ingest_jpm,
    jpm_completeness,
    jpm_document,
    jpm_extraction,
)
from vinci.graph.llm import LlmError
from vinci.theme_intelligence import budget as budget_mod
from vinci.theme_intelligence.budget import BudgetExceeded, GuardedClient, SpendGuard
from vinci.theme_intelligence.config import load_sources, load_taxonomy
from vinci.theme_intelligence.pipeline import ArticleResult, Pipeline
from vinci.theme_intelligence.schemas import RunStatus
from vinci.theme_intelligence.securities import SecResolver

MODEL = "claude-opus-4-8"
WEEK = {"window_from": date(2026, 10, 4), "window_to": date(2026, 10, 11),
        "as_of": date(2026, 10, 11)}


class Scripted:
    """A model stand-in that bills every call (usage reported) and answers per tool: a dict is
    the tool input, an exception is raised after billing — a truncation, a missing tool call; a
    list is answered in order, its last entry for every call after."""

    model = MODEL

    def __init__(self, answers: dict[str, Any], usage: dict[str, int] | None = None) -> None:
        self.answers = answers
        self.usage = usage or {"input_tokens": 10_000, "output_tokens": 4_000}
        self.calls: list[str] = []
        self.last_usage: dict[str, int] | None = None

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **_kw: Any) -> dict[str, Any]:
        self.calls.append(tool["name"])
        self.last_usage = dict(self.usage)
        out = self.answers[tool["name"]]
        if isinstance(out, list):
            out = out.pop(0) if len(out) > 1 else out[0]
        if isinstance(out, Exception):
            raise out
        return dict(out)


def _pipeline(tmp: Path, client: Any, *, review: bool = False,
              sources: tuple[Any, ...] | None = None) -> Pipeline:
    resolver = SecResolver(tmp / "sec", http=FrozenSecHttp(JPM_DIR))  # type: ignore[arg-type]
    return Pipeline(tmp / "ti", sources=load_sources() if sources is None else sources,
                    taxonomy=load_taxonomy(), client=client, resolver=resolver, review=review)


def _paid(pipe: Pipeline, run_id: str) -> list[dict[str, Any]]:
    return [c for c in pipe.store.llm_calls(run_id) if not c.get("cached")]


# --- U3: a resumed scan spends its limit once ------------------------------------------------

def _first_attempt(tmp: Path, *, spent: float, finish: bool = True) -> tuple[Pipeline, str]:
    """An attempt that paid `spent` (one recorded call, as the pipeline records it)."""
    p = _pipeline(tmp, Scripted({}), sources=())
    run = p.start_run("scan", **WEEK)
    p.guard.record("extraction", spent, spent)
    p._llm_call("extract", "A-1", False, {"input_tokens": 1}, spent, 1.0, MODEL, "v")  # noqa: SLF001
    if finish:
        p.guard.refusals.append("a completeness call bounded at $3.00 does not fit the "
                                "remaining $1.50 of the run budget $40.00 — not sent")
        p.finish_run(RunStatus.PARTIAL)
    return p, run.run_id


def _resume(tmp: Path, run_id: str, budget: float | None = None) -> tuple[Pipeline, Any]:
    p = _pipeline(tmp, Scripted({}), sources=())
    out = p.run_scan(max_articles=10, resume_run_id=run_id, budget=budget, **WEEK)
    return p, out


def test_a_resumed_scan_counts_what_the_run_already_spent(tmp_path: Path) -> None:
    """POSITIVE: $38.50 of $40 spent → the resumed run may spend $1.50, and its manifest keeps
    the first attempt's spend, call and refusal. NEGATIVE: a new run starts at $0."""
    _p1, rid = _first_attempt(tmp_path, spent=38.5)
    p2, out = _resume(tmp_path, rid)
    assert out.spend["spent_usd"] == pytest.approx(38.5) and out.spend["paid_calls"] == 1
    assert len(out.spend["refusals"]) == 1  # the first attempt's
    assert p2.guard.run_spent == pytest.approx(38.5)
    assert p2.guard.remaining("review")[0] == pytest.approx(1.5)
    with pytest.raises(BudgetExceeded, match="of the run budget"):
        p2.guard.check(3.0, "review")
    assert out.cost_usd == pytest.approx(38.5)  # the ledger and the guard agree
    assert any("resumed with $38.50 already spent" in w and "$40.00" in w for w in out.warnings)
    fresh = _pipeline(tmp_path / "new", Scripted({}), sources=())
    fresh.start_run("scan", **WEEK)
    assert fresh.guard.run_spent == 0 and fresh.guard.calls == [] == fresh.guard.refusals


def test_a_resume_with_a_higher_budget_raises_the_runs_total(tmp_path: Path) -> None:
    """`--budget` on a resume is the run's TOTAL limit: $60 after $38.50 leaves $21.50."""
    _p1, rid = _first_attempt(tmp_path, spent=38.5)
    p2, out = _resume(tmp_path, rid, budget=60.0)
    assert p2.guard.remaining("review")[0] == pytest.approx(21.5)
    assert any("$60.00" in w for w in out.warnings if w.startswith("resumed with"))


def test_an_attempt_that_died_without_its_summary_is_read_from_the_ledger(
        tmp_path: Path) -> None:
    """POSITIVE: no summary was written (the process died) — its paid ledger rows count; a
    cached row (spent nothing) does not. A second death after a resume: the larger of the
    summary and the ledger."""
    p1, rid = _first_attempt(tmp_path, spent=2.0, finish=False)
    p1._llm_call("extract", "A-2", True, {"input_tokens": 9}, 5.0, 0.0, MODEL, "v")  # noqa: SLF001
    assert p1.store.run(rid).spend == {}  # type: ignore[union-attr]
    p2, out = _resume(tmp_path, rid)
    assert out.spend["spent_usd"] == pytest.approx(2.0)
    # attempt 2 writes its summary ($2); attempt 3 pays $1.25 and dies before writing one
    p3 = _pipeline(tmp_path, Scripted({}), sources=())
    p3.run = p3.store.run(rid)
    p3._llm_call("extract", "A-3", False, {"input_tokens": 3}, 1.25, 0.0, MODEL, "v")  # noqa: SLF001
    p3.run.status = RunStatus.INTERRUPTED  # type: ignore[union-attr]
    p3.store.upsert_run(p3.run)  # type: ignore[arg-type]
    p4, _out = _resume(tmp_path, rid)
    assert p4.guard.run_spent == pytest.approx(3.25)


# --- U4: every paid call is in the ledger -----------------------------------------------------

def test_a_failed_completeness_pass_is_in_the_runs_cost(tmp_path: Path) -> None:
    """POSITIVE: the completeness call was billed and raised — its cost is in the ledger
    (`completeness-unrecorded`, with why) and the run's cost equals the guard's."""
    fake = Scripted({"record_article_evidence": jpm_extraction(),
                     "record_completeness": LlmError(f"model {MODEL} returned no tool_use "
                                                     f"block (stop=end_turn)")},
                    usage={"input_tokens": 40_000, "output_tokens": 6_000})
    pipe = _pipeline(tmp_path, fake)
    pipe.start_run("ingest", as_of=JPM_AS_OF)
    doc = jpm_document()
    res = pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="jpm_tmt",
                                as_of=JPM_AS_OF)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    assert res.status == "PROCESSED" and fake.calls == ["record_article_evidence",
                                                        "record_completeness"]
    rows = _paid(pipe, run.run_id)
    assert sorted(r["purpose"] for r in rows) == ["completeness-unrecorded", "extract"]
    (missed,) = [r for r in rows if r["purpose"] == "completeness-unrecorded"]
    assert "LlmError" in missed["note"] and "no tool_use block" in missed["note"]
    assert run.spend["paid_calls"] == len(rows) == 2
    assert run.cost_usd == pytest.approx(run.spend["actual_total_usd"]) and run.cost_usd > 0
    assert any("recorded in the ledger as *-unrecorded" in w for w in run.warnings)


def test_truncated_reviews_are_in_the_runs_cost(tmp_path: Path) -> None:
    trunc = LlmError(f"model {MODEL} truncated at max_tokens=4000 — tool call incomplete")
    fake = Scripted({"record_review": trunc})
    pipe = _pipeline(tmp_path, fake, review=True)
    pipe.start_run("ingest", as_of=JPM_AS_OF)
    assert ingest_jpm(pipe).status == "PROCESSED"
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    rows = _paid(pipe, run.run_id)
    assert len(fake.calls) == len(rows) == run.spend["paid_calls"] > 0
    assert {r["purpose"] for r in rows} == {"review-unrecorded"}
    assert all("truncated" in r["note"] for r in rows)
    assert run.cost_usd == pytest.approx(run.spend["actual_total_usd"]) and run.cost_usd > 0


def test_a_truncated_enrichment_is_in_the_runs_cost(tmp_path: Path) -> None:
    pipe, _tid = _enrichable(tmp_path)
    fake = Scripted({"record_enrichment": LlmError(f"model {MODEL} truncated at "
                                                   f"max_tokens=4000 — tool call incomplete")})
    pipe.client = GuardedClient(fake, pipe.guard)
    with pytest.raises(LlmError):
        pipe.run_enrich(as_of=JPM_AS_OF)
    run = pipe.run
    assert run is not None and run.status is RunStatus.FAILED
    (row,) = _paid(pipe, run.run_id)
    assert row["purpose"] == "enrichment-unrecorded"
    assert run.cost_usd == pytest.approx(run.spend["actual_total_usd"]) and run.cost_usd > 0


def test_a_billed_answer_the_run_never_used_is_in_the_runs_cost(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The call SUCCEEDED and the run failed after it (the SEC check of the proposed names),
    before recording it — still paid."""

    def sec_down(*_a: Any, **_kw: Any) -> Any:
        raise RuntimeError("SEC lookup failed: the names could not be read")

    pipe, _tid = _enrichable(tmp_path)
    pipe.client = GuardedClient(StandIn(ANSWER), pipe.guard)
    monkeypatch.setattr(pipe.resolver, "resolve", sec_down)
    with pytest.raises(RuntimeError, match="could not be read"):
        pipe.run_enrich(as_of=JPM_AS_OF)
    assert pipe.run is not None
    (row,) = _paid(pipe, pipe.run.run_id)
    assert row["purpose"] == "enrichment-unrecorded" and row["note"] == "answer not used"
    assert pipe.run.cost_usd == pytest.approx(pipe.run.spend["actual_total_usd"])
    assert pipe.run.cost_usd > 0


def test_a_call_a_path_records_itself_is_never_recorded_twice(tmp_path: Path) -> None:
    """NEGATIVE: a truncated completeness call the split path records itself
    (`complete-truncated`), and every answered call, stay ONE ledger row each — no
    `-unrecorded` row, no warning; the ledger's paid rows equal the guard's paid calls."""
    fake = FakeLlm(_pass1(bad_items=False), truncate=frozenset({""}))
    pipe = _pipe(tmp_path, fake)
    pipe.start_run("article", as_of=date(2026, 10, 2))
    assert _process(pipe, limit=100.0).status == "PROCESSED"
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    rows = _paid(pipe, run.run_id)
    purposes = [r["purpose"] for r in rows]
    assert "complete-truncated" in purposes and len(fake.calls) > 2  # truncated, then split
    assert not any(p.endswith("-unrecorded") for p in purposes)
    assert len(rows) == run.spend["paid_calls"] == len(fake.calls)
    assert not any("-unrecorded" in w for w in run.warnings)
    assert run.cost_usd == pytest.approx(run.spend["actual_total_usd"])


def test_a_call_that_failed_with_no_usage_is_counted_by_the_guard_only() -> None:
    """NEGATIVE: no usage reported = not shown billed — no ledger row is owed (the guard still
    counts the call at its bound, as before)."""

    class Down:
        model = MODEL
        last_usage = None

        def extract(self, **_kw: Any) -> dict[str, Any]:
            raise ConnectionError("connection refused")

    guard = SpendGuard(run_limit=100.0)
    with pytest.raises(ConnectionError):
        GuardedClient(Down(), guard).extract(system="s", user="u", tool={"name": "record_review"})
    assert len(guard.calls) == 1 and guard.run_spent > 0
    assert guard.take_unrecorded() == []


# --- U26: a document's own limit holds that document alone ------------------------------------

def _scan_with_hold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                    how: str) -> tuple[Pipeline, Any, list[str], list[str]]:
    """Four candidates; the first meets the spend guard as `how` says, through the real guard
    and the real hold; the others go through the real pipeline."""
    from tests.test_theme_intelligence_scan import _fake_scan

    pipe = _pipe(tmp_path, FakeLlm(_pass1(bad_items=False)))
    urls = [f"https://example.test/hypothetical/n{i}" for i in range(4)]
    _fake_scan(monkeypatch, pipe, urls)
    ingest = Pipeline.process_url
    seen: list[str] = []

    def process_url(self: Pipeline, url: str, **kw: Any) -> ArticleResult:
        seen.append(url)
        if url != urls[0] or how == "none":
            return ingest(self, url, **kw)
        self.guard.begin_document(url, 2.0)
        try:
            if how == "document":  # $1.50 of its $2 spent; a $1 review does not fit
                self.guard.record("extraction", 1.5, 1.5)
                self.guard.check(1.0, "review")
            elif how == "retry":  # fits the document's $0.50 left, not its retry share
                self.guard.record("completeness", 1.5, 1.5)
                self.guard.check(0.3, "completeness")
            else:  # the run's budget
                self.guard.run_limit = self.guard.run_spent + 0.1
                self.guard.check(0.5, "extraction")
        except BudgetExceeded as exc:
            return self._budget_held(url, "A-held", "AV-held", exc)
        finally:
            self.guard.end_document()
        raise AssertionError("the guard let it through")

    monkeypatch.setattr(Pipeline, "process_url", process_url)
    run = pipe.run_scan(window_from=date(2026, 10, 2), window_to=date(2026, 10, 11),
                        as_of=date(2026, 10, 11), max_articles=10)
    queued = sorted(u for u, _s, _m in pipe.store.candidates("QUEUED"))
    return pipe, run, seen, queued


@pytest.mark.parametrize("how", ["document", "retry"])
def test_a_document_over_its_own_limit_is_queued_and_the_scan_goes_on(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, how: str) -> None:
    pipe, run, seen, queued = _scan_with_hold(tmp_path, monkeypatch, how)
    urls = [f"https://example.test/hypothetical/n{i}" for i in range(4)]
    assert seen == urls and queued == [urls[0]]
    assert run.counts["articles_queued"] == 1 and len(pipe.store.theses()) >= 1
    assert run.status is RunStatus.PARTIAL  # an in-window article was not analysed
    assert any(f"{urls[0]} held by its own limit" in w for w in run.warnings)
    assert not any("the run budget is exhausted" in w for w in run.warnings)


def test_the_runs_own_budget_still_stops_the_scan(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: the RUN's budget refused — nothing after it is attempted, all four queued."""
    _pipe_, run, seen, queued = _scan_with_hold(tmp_path, monkeypatch, "run")
    assert len(seen) == 1 and len(queued) == 4 and run.status is RunStatus.PARTIAL
    assert any("the run budget is exhausted" in w for w in run.warnings)


def test_a_scan_with_no_hold_is_not_partial(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The control: nothing held, nothing queued — SUCCEEDED."""
    _pipe_, run, seen, queued = _scan_with_hold(tmp_path, monkeypatch, "none")
    assert len(seen) == 4 and queued == [] and run.status is RunStatus.SUCCEEDED


def test_a_refusal_says_which_limit_refused_it() -> None:
    g = SpendGuard(run_limit=40.0)
    g.begin_document("A-1", 2.0)
    g.record("completeness", 1.5, 1.5)
    with pytest.raises(BudgetExceeded) as retry:
        g.check(0.3, "completeness")
    with pytest.raises(BudgetExceeded) as doc:
        g.check(1.0, "review")
    g.end_document()
    g.run_limit = g.run_spent + 0.1
    with pytest.raises(BudgetExceeded) as run:
        g.check(0.5, "review")
    with pytest.raises(BudgetExceeded) as price:
        budget_mod.call_bound("no-such-model", "s", "u", {})
    assert [e.value.scope for e in (retry, doc, run, price)] == [
        "retry", "document", "run", "price"]
    assert BudgetExceeded("unscoped").scope == "run"  # a refusal that says nothing stops a scan


@pytest.mark.parametrize(("scope", "asked"), [("document", 2), ("run", 1)])
def test_an_enrichment_held_by_its_own_limit_does_not_stop_the_pass(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scope: str, asked: int) -> None:
    """POSITIVE: each thesis's own limit refuses it — the next one is still asked. NEGATIVE:
    the RUN's budget refuses — the pass stops."""
    pipe, tid = _enrichable(tmp_path)
    model = StandIn(ANSWER)
    pipe.client = GuardedClient(model, pipe.guard)
    if scope == "document":
        monkeypatch.setattr(budget_mod, "DOC_COST_LIMIT_USD", 0.0001)
        run, done = pipe.run_enrich(as_of=JPM_AS_OF, thesis_ids=[tid, tid], refresh=True)
    else:
        run, done = pipe.run_enrich(as_of=JPM_AS_OF, thesis_ids=[tid, tid], refresh=True,
                                    budget=0.0001)
    assert len(run.spend["refusals"]) == len(done) == asked and model.users == []
    assert all(what.startswith("not run — budget") for _t, what in done)
    assert run.status is RunStatus.PARTIAL


# --- U29: two refusals of one thesis in one run -----------------------------------------------

@pytest.mark.parametrize(("limit", "issues"), [("document", 2), ("run", 1)])
def test_two_refusals_of_one_theses_review_in_one_run(
        tmp_path: Path, limit: str, issues: int) -> None:
    """POSITIVE: two articles update one thesis, each review refused by its own document's
    limit (two different statements) — two issues, both articles PROCESSED (main raised
    StoreIntegrityError on the second). NEGATIVE: the same statement twice (the run's budget,
    the same bound) is ONE issue — no duplicate."""
    from tests.test_theme_intelligence_overlap import W1, W2, _launch, _memory_thesis

    pipe = _pipeline(tmp_path, Scripted({"record_review": {"verdicts": []}}), review=True)
    pipe.start_run("ingest", as_of=date(2026, 3, 9))
    if limit == "run":
        pipe.guard.run_limit = 0.01
    out = []
    for slug, when, d, verb in (("launch-on-time", W1, "2Q26", "scheduled"),
                                ("launch-delayed", W2, "4Q26", "delayed")):
        art, x = _launch(slug, when, d, verb)
        doc = art.doc()
        out.append(pipe.process_document(
            doc, fetched(doc), url=doc.canonical_url, source_id="manual", as_of=when, fixture=x,
            publisher_override=art.publisher, cost_limit=0.01 if limit == "document" else None))
    assert [r.status for r in out] == ["PROCESSED", "PROCESSED"]
    thesis = _memory_thesis(pipe)
    assert thesis.current_version == 2
    assert pipe.run is not None
    found = [i for i in pipe.store.issues(run_id=pipe.run.run_id)
             if i.code == "REVIEW_NOT_RUN" and i.ref_id == thesis.thesis_id]
    assert len(found) == len({i.issue_id for i in found}) == issues
    assert len(pipe.guard.refusals) == 2


def test_two_different_review_failures_of_one_thesis_in_one_run(tmp_path: Path) -> None:
    """The same id class on the review's other refusal path: a truncated review, then one that
    returned no tool call — two statements, two issues (main: StoreIntegrityError)."""
    from tests.test_theme_intelligence_overlap import W1, W2, _launch, _memory_thesis

    fake = Scripted({"record_review": [
        LlmError(f"model {MODEL} truncated at max_tokens=4000 — tool call incomplete"),
        LlmError(f"model {MODEL} returned no tool_use block (stop=end_turn)")]})
    pipe = _pipeline(tmp_path, fake, review=True)
    pipe.start_run("ingest", as_of=date(2026, 3, 9))
    for slug, when, d, verb in (("launch-on-time", W1, "2Q26", "scheduled"),
                                ("launch-delayed", W2, "4Q26", "delayed")):
        art, x = _launch(slug, when, d, verb)
        doc = art.doc()
        res = pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="manual",
                                    as_of=when, fixture=x, publisher_override=art.publisher)
        assert res.status == "PROCESSED"
    thesis = _memory_thesis(pipe)
    assert pipe.run is not None and fake.calls == ["record_review"] * 2
    found = {i.issue_id: i.detail for i in pipe.store.issues(run_id=pipe.run.run_id)
             if i.code == "REVIEW_NOT_RUN" and i.ref_id == thesis.thesis_id}
    assert len(found) == 2
    assert {"truncated" in d for d in found.values()} == {True, False}


def test_a_resumed_compact_extraction_does_not_record_the_earlier_runs_truncation(
        tmp_path: Path) -> None:
    """Run 1: the full extraction truncates and its compact retry fails — both billed calls are
    in run 1's ledger. Run 2 resumes from the truncation marker: only the compact call is paid,
    and the truncated attempt is NOT recorded again (it was run 1's). NEGATIVE: run 2 still
    reports the truncated attempt's output tokens in its EXTRACTION_COMPACT note."""
    fake = Scripted({"record_article_evidence": [
        LlmError(f"model {MODEL} truncated at max_tokens=21333 — tool call incomplete"),
        LlmError(f"model {MODEL} returned no tool_use block (stop=end_turn)"),
        jpm_extraction()]}, usage={"input_tokens": 30_000, "output_tokens": 4_321})
    pipe = _pipeline(tmp_path, fake)
    doc = jpm_document()

    def process() -> Any:
        return pipe.process_document(doc, fetched(doc), url=doc.canonical_url,
                                     source_id="jpm_tmt", as_of=JPM_AS_OF,
                                     completeness_fixture=jpm_completeness())

    first = pipe.start_run("ingest", as_of=JPM_AS_OF)
    with pytest.raises(LlmError, match="no tool_use block"):
        process()
    pipe.finish_run(RunStatus.FAILED)
    second = pipe.start_run("ingest", as_of=JPM_AS_OF)
    assert process().status == "PROCESSED"
    pipe.finish_run(RunStatus.SUCCEEDED)
    one, two = _paid(pipe, first.run_id), _paid(pipe, second.run_id)
    assert [r["purpose"] for r in one] == ["article_evidence-unrecorded"] * 2
    assert [r["purpose"] for r in two] == ["extract"]
    assert len(one) + len(two) == len(fake.calls) == 3  # every billed call once
    (note,) = [i.detail for i in pipe.store.issues(run_id=second.run_id)
               if i.code == "EXTRACTION_COMPACT"]
    assert "4321 output tokens" in note


def test_a_compact_retry_in_the_same_run_records_the_truncation_once(tmp_path: Path) -> None:
    """The control: truncated, then compacted in ONE run — the truncated attempt is that run's
    `extract-truncated` row, and nothing is left over as `-unrecorded`."""
    fake = Scripted({"record_article_evidence": [
        LlmError(f"model {MODEL} truncated at max_tokens=21333 — tool call incomplete"),
        jpm_extraction()]})
    pipe = _pipeline(tmp_path, fake)
    run = pipe.start_run("ingest", as_of=JPM_AS_OF)
    doc = jpm_document()
    assert pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id="jpm_tmt",
                                 as_of=JPM_AS_OF,
                                 completeness_fixture=jpm_completeness()).status == "PROCESSED"
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert sorted(r["purpose"] for r in _paid(pipe, run.run_id)) == ["extract",
                                                                     "extract-truncated"]


def test_a_held_documents_warning_never_promises_the_next_scan(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review of #715: every scan applies the same per-document limit, so the document is held
    again — the warning names the route that can process it, never "the next run"."""
    _pipe_, run, _seen, _queued = _scan_with_hold(tmp_path, monkeypatch, "document")
    (w,) = [w for w in run.warnings if "held by its own limit" in w]
    assert "every scan will hold it again" in w and "ingest-file --max-cost" in w
    assert "for the next run" not in w


def test_a_resumed_run_with_no_limit_says_so(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review of #715: no limit is never printed as "$0.00"."""
    _p1, rid = _first_attempt(tmp_path, spent=2.0)
    monkeypatch.setattr(budget_mod, "default_run_limit", lambda mode: None)
    _p2, out = _resume(tmp_path, rid)
    (w,) = [w for w in out.warnings if w.startswith("resumed with")]
    assert "no limit set" in w and "$0.00" not in w
