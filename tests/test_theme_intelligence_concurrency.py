"""Independent paid calls sent concurrently (2026-11-19, operator: speed theme intelligence up
"without compromising the quality") — and nothing else changed.

The call map (record 2026-11-19): only the ENRICHMENT pass has independent calls, one per
thesis, each prompt that thesis's own card. Extraction, the completeness parts and the card
reviews are a chain and stay one at a time. So these tests hold three things:
- the spend guard RESERVES: calls in flight together never jointly pass a limit;
- a concurrent enrichment pass writes exactly what a one-at-a-time pass writes, in the same
  order — when its answers arrive out of order, when the run's budget binds, and when a call
  fails;
- a client that does not keep its usage per thread is sent one call at a time.

Offline: the theses are the two AUTHENTIC J.P. Morgan fixtures' (real page excerpts, their real
frozen model outputs), the SEC data their frozen subset; the enrichment model is a stand-in that
answers in the real tool's shape and sleeps a set time per thesis.
"""

from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import (
    CALM_AS_OF,
    JPM_AS_OF,
    ingest_calm,
    ingest_jpm,
    make_pipeline,
)
from vinci.graph.llm import LlmError
from vinci.theme_intelligence.budget import BudgetExceeded, GuardedClient, SpendGuard, call_bound
from vinci.theme_intelligence.config import load_sources, load_taxonomy
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import RunStatus

MODEL = "claude-opus-4-8"


class Model:
    """A stand-in for `ThemeLlmClient`: each call's usage kept ON ITS OWN THREAD
    (`usage_per_thread`), a set sleep per thesis, the real tool's answer shape. It counts how
    many calls are in flight at once and the order they finish in."""

    model = MODEL
    max_tokens = 21_333
    usage_per_thread = True

    def __init__(self, delays: dict[str, float] | None = None, *, output_tokens: int = 300,
                 fail: frozenset[str] = frozenset()) -> None:
        self._local = threading.local()
        self._lock = threading.Lock()
        self.delays = delays or {}
        self.output_tokens = output_tokens
        self.fail = fail
        self.started: list[str] = []
        self.finished: list[str] = []
        self.live = 0
        self.most_live = 0

    @property
    def last_usage(self) -> dict[str, int] | None:
        usage: dict[str, int] | None = getattr(self._local, "usage", None)
        return usage

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                **_kw: Any) -> dict[str, Any]:
        assert tool["name"] == "record_enrichment"
        m = re.search(r"THESIS (TH-\w+)", user)
        assert m is not None
        tid = m.group(1)
        self._local.usage = None
        with self._lock:
            self.started.append(tid)
            self.live += 1
            self.most_live = max(self.most_live, self.live)
        try:
            time.sleep(self.delays.get(tid, 0.0))
            # a usage that differs by request, so no two calls' rows could be confused
            self._local.usage = {"input_tokens": 900 + len(user) // 10,
                                 "output_tokens": self.output_tokens,
                                 "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
            if tid in self.fail:  # billed, then unusable — as a truncated call is
                raise LlmError(f"model {MODEL} truncated at max_tokens=21333 — tool call "
                               "incomplete; raise the cap or shrink the prompt")
            step = re.search(r"\[(s03\.\d+)\]", user)
            assert step is not None
            # two registrants the frozen SEC subset holds (each verified point in time, or set
            # aside where the card already names it) and one citing a step no card holds
            return {"companies": [
                {"name": "FactSet Research Systems", "ticker": "FDS", "exchange": "NYSE",
                 "direction": "hurt", "step_id": step.group(1),
                 "business": "financial data and analytics software",
                 "exposure": f"stand-in exposure for {tid}", "revenue_model": "subscription"},
                {"name": "Micron Technology", "ticker": "MU", "exchange": "Nasdaq",
                 "direction": "benefit", "step_id": step.group(1),
                 "business": "memory chip maker", "exposure": f"stand-in exposure for {tid}"},
                {"name": "Invented Widgets", "ticker": "IWX", "exchange": "NYSE",
                 "direction": "benefit", "step_id": "s03.9", "business": "widgets",
                 "exposure": "No such step."}]}
        finally:
            with self._lock:
                self.live -= 1
                self.finished.append(tid)


def _theses(tmp_path: Path, workers: int, model: Model | Any) -> Pipeline:
    """Five real theses (both J.P. Morgan fixtures), the enrichment model behind the guard."""
    pipe = make_pipeline(tmp_path)
    pipe.llm_workers = workers
    pipe.start_run("ingest", as_of=JPM_AS_OF)
    assert ingest_jpm(pipe).status == "PROCESSED"
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.start_run("ingest", as_of=CALM_AS_OF)
    assert ingest_calm(pipe).status == "PROCESSED"
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.client = GuardedClient(model, pipe.guard)
    return pipe


def _targets(pipe: Pipeline) -> list[str]:
    tids = [t.thesis_id for t in pipe.store.theses()]
    assert len(tids) == 5
    return tids


def _slowest_first(tids: list[str], step: float = 0.08) -> dict[str, float]:
    """Each thesis slower than the next: answers arrive in REVERSE of input order."""
    return {tid: step * (len(tids) - i) for i, tid in enumerate(tids)}


def _written(pipe: Pipeline, run_id: str) -> dict[str, Any]:
    """Everything the run wrote, less what differs by clock or run id alone."""
    sets = [es.model_dump(mode="json", exclude={"set_id", "run_id", "created_at"})
            for t in pipe.store.theses() for es in pipe.store.enrichments(t.thesis_id)]
    # the ledger is read back by its hashed call id, which carries the clock: compared sorted
    calls = sorted(({k: c[k] for k in ("purpose", "ref", "cached", "usage", "cost_usd", "model",
                                       "prompt_version", "note") if k in c}
                    for c in pipe.store.llm_calls(run_id)),
                   key=lambda c: (c["purpose"], c["ref"]))
    cache = {p.name: json.loads(p.read_text())
             for p in sorted((pipe.paths.llm_cache / "enrich").glob("*.json"))}
    run = pipe.store.run(run_id)
    assert run is not None
    spend = dict(run.spend)
    return {"sets": sets, "calls": calls, "cache": cache, "spend": spend,
            "counts": {k: v for k, v in run.counts.items() if "seconds" not in k},
            "status": run.status, "warnings": run.warnings}


# --- the guard ---------------------------------------------------------------------------------

def test_calls_in_flight_together_never_jointly_pass_the_run_limit() -> None:
    """THE FIX. Eight threads send at once against a run limit that holds three calls' bounds.
    POSITIVE: at no moment are more than three in flight, the five that do not fit are refused
    and never sent, and the run's spend stays inside its limit. NEGATIVE (the old guard, which
    checked the remaining dollars and recorded the spend only AFTER the call): every thread read
    the same untouched budget and all eight were sent together, 8 bounds against a 3.5 limit."""
    model = Model({f"TH-{i}": 0.3 for i in range(8)})
    tool = {"name": "record_enrichment"}
    users = [f"THESIS TH-{i} (version 1): t\n  [s03.0] (pricing) x" for i in range(8)]
    bound = call_bound(MODEL, "s", users[0], tool)
    guard = SpendGuard(run_limit=3.5 * bound)
    client = GuardedClient(model, guard)
    gate = threading.Barrier(8)
    refused: list[str] = []

    def one(user: str) -> None:
        gate.wait()
        try:
            client.extract(system="s", user=user, tool=tool)
        except BudgetExceeded as exc:
            refused.append(str(exc))

    threads = [threading.Thread(target=one, args=(u,)) for u in users]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert model.most_live == 3 and len(model.started) == 3
    assert len(refused) == 5 and len(guard.refusals) == 5
    assert all("does not fit the remaining" in r for r in refused)
    assert guard.run_spent <= guard.run_limit  # type: ignore[operator]
    assert guard.in_flight == 0 and guard.run_reserved == 0.0


def test_a_reservation_holds_its_bound_until_it_settles_and_rows_keep_admission_order() -> None:
    """Admitted calls hold their bounds (`remaining` counts them); settling releases the hold and
    spends the actual cost. Rows are written at ADMISSION, so two calls settled in reverse order
    keep their admission order. A run cannot start while a call is in flight."""
    g = SpendGuard(run_limit=10.0)
    a, b = g.scope("enrich TH-A"), g.scope("enrich TH-B")
    ra = g.reserve(3.0, "extraction", a)
    rb = g.reserve(4.0, "extraction", b)
    assert g.remaining("extraction", a)[0] == pytest.approx(3.0)
    with pytest.raises(BudgetExceeded, match="does not fit the remaining"):
        g.reserve(3.5, "extraction", g.scope("enrich TH-C"))
    with pytest.raises(RuntimeError, match="in flight"):
        g.start_run("enrich")
    g.settle(rb, 0.25)
    g.settle(ra, None)  # no reported cost: counted at its bound
    assert g.run_spent == pytest.approx(3.25) and g.run_reserved == 0.0
    assert [(c["document"], c["actual_usd"]) for c in g.calls] == [
        ("enrich TH-A", None), ("enrich TH-B", 0.25)]
    assert a.spent == pytest.approx(3.0) and b.spent == pytest.approx(0.25)


def test_make_room_waits_for_calls_in_flight_before_the_run_refuses() -> None:
    """A call the RUN's budget refuses only because others are in flight waits for them
    (`make_room`), and is admitted once their actual costs leave room; refused only once nothing
    is in flight. A document's own limit refuses at once — waiting cannot help it."""
    g = SpendGuard(run_limit=5.0)
    held = [g.reserve(3.0, "extraction", g.scope("enrich TH-A"))]

    def room() -> bool:
        if not held:
            return False
        g.settle(held.pop(), 0.5)
        return True

    r = g.reserve(4.0, "extraction", g.scope("enrich TH-B"), make_room=room)
    assert held == [] and g.run_reserved == pytest.approx(4.0)
    g.settle(r, 4.0)
    with pytest.raises(BudgetExceeded) as exc:
        g.reserve(1.0, "extraction", g.scope("enrich TH-C"), make_room=room)
    assert exc.value.scope == "run"
    calls = 0

    def never() -> bool:
        nonlocal calls
        calls += 1
        return False

    with pytest.raises(BudgetExceeded) as exc:
        g.reserve(0.4, "extraction", g.scope("enrich TH-D", limit=0.3), make_room=never)
    assert exc.value.scope == "document" and calls == 0


# --- the enrichment pass, concurrent and one at a time -----------------------------------------

def test_a_concurrent_pass_writes_what_one_at_a_time_writes_in_input_order(
        tmp_path: Path) -> None:
    """POSITIVE: five real theses enriched with eight workers, their answers arriving in REVERSE
    of input order, write the same sets, ledger rows, cache files, spend rows and run counts, in
    the same order, as the same pass one call at a time. NEGATIVE: it really ran concurrently —
    all five in flight at once, finished last-first — so the equality is not two sequential runs
    compared."""
    order = _targets(_theses(tmp_path / "probe", 1, Model()))  # thesis ids hash their keys
    out: dict[int, dict[str, Any]] = {}
    seen: dict[int, Model] = {}
    for workers in (1, 8):
        model = Model(_slowest_first(order))
        pipe = _theses(tmp_path / f"w{workers}", workers, model)
        run, done = pipe.run_enrich(as_of=CALM_AS_OF)
        assert run.status is RunStatus.SUCCEEDED, done
        out[workers] = {"done": done, **_written(pipe, run.run_id)}
        seen[workers] = model
    assert seen[1].most_live == 1 and seen[1].finished == order
    assert seen[8].most_live == 5 and seen[8].finished == order[::-1]
    assert out[8] == out[1]
    assert [tid for tid, _ in out[8]["done"]] == order
    assert out[8]["counts"]["theses_enriched"] == 5
    assert [c["purpose"] for c in out[8]["calls"]] == ["enrich"] * 5


def test_when_the_run_budget_binds_a_concurrent_pass_refuses_what_one_at_a_time_refuses(
        tmp_path: Path) -> None:
    """Calls whose actual cost is near their bound, under a run limit that fits four of five
    one after another. POSITIVE: the concurrent pass enriches the same four and refuses the same
    fifth with the same words, and the run never spends past its limit. NEGATIVE: counted at its
    bound while in flight, the fourth call did NOT fit beside the three before it — so a pass
    that refused on reservations alone (no `make_room`) would have stopped one thesis early."""
    order = _targets(_theses(tmp_path / "probe", 1, Model()))
    results: dict[int, Any] = {}
    for workers in (1, 8):  # each call held 0.1 s: the earlier ones are in flight at admission
        model = Model(dict.fromkeys(order, 0.1), output_tokens=17_000)
        pipe = _theses(tmp_path / f"w{workers}", workers, model)
        run, done = pipe.run_enrich(as_of=CALM_AS_OF, budget=2.0)
        assert run.status is RunStatus.PARTIAL
        results[workers] = (done, _written(pipe, run.run_id), run)
    (d1, w1, r1), (d8, w8, r8) = results[1], results[8]
    assert d8 == d1 and w8 == w1
    assert sum(1 for _tid, what in d8 if what.startswith("not run — budget")) == 1
    assert d8[-1][1].startswith("not run — budget") and "run budget $2.00" in d8[-1][1]
    assert r8.spend["spent_usd"] <= 2.0 and r8.spend["refusals"] == r1.spend["refusals"]
    bounds = [c["bound_usd"] for c in r8.spend["calls"]]
    spent3 = sum(c["actual_usd"] for c in r8.spend["calls"][:3])
    assert sum(bounds[:3]) + bounds[3] > 2.0 >= spent3 + bounds[3]  # the NEGATIVE, by numbers


def test_a_failed_call_is_raised_at_its_turn_and_later_paid_calls_are_kept(
        tmp_path: Path) -> None:
    """The second thesis's call is billed and fails. POSITIVE, as one at a time: the run fails
    with THAT error, the first thesis is written, nothing after the second is. What concurrency
    adds is said, never hidden: the calls already sent for the theses after it are paid — each a
    ledger row (`enrich-unrecorded`) — and their answers cached, so the re-run pays only for the
    failed one. NEGATIVE: one at a time sends nothing after the failure."""
    tids = _targets(_theses(tmp_path / "probe", 1, Model()))
    rows: dict[int, list[str]] = {}
    for workers in (1, 8):
        model = Model({tid: 0.05 * (i + 1) for i, tid in enumerate(tids)},
                      fail=frozenset({tids[1]}))
        pipe = _theses(tmp_path / f"w{workers}", workers, model)
        with pytest.raises(LlmError, match="truncated"):
            pipe.run_enrich(as_of=CALM_AS_OF)
        (run,) = [r for r in pipe.store.runs() if r.mode == "enrich"]
        assert run.status is RunStatus.FAILED and "truncated" in run.warnings[0]
        assert [t for t in tids if pipe.store.enrichments(t)] == [tids[0]]
        rows[workers] = sorted(f"{c['purpose']}:{c['ref']}"
                               for c in pipe.store.llm_calls(run.run_id))
        if workers == 1:
            assert model.started == tids[:2]
            continue
        assert sorted(model.started) == sorted(tids)  # all five were in flight
        cached = sorted(p.name for p in (pipe.paths.llm_cache / "enrich").glob("*.json"))
        assert len(cached) == 4  # every answer that came back, the failed one's excepted
        model.fail = frozenset()
        model.started = []
        again, done = pipe.run_enrich(as_of=CALM_AS_OF)
        assert again.status is RunStatus.SUCCEEDED and model.started == [tids[1]]
        assert sorted((c["ref"], c["cached"]) for c in pipe.store.llm_calls(again.run_id)) == [
            (tids[1], False), *((t, True) for t in sorted(tids[2:]))]
    assert rows[1] == [f"enrich:{tids[0]}", f"enrichment-unrecorded:enrich {tids[1]}"]
    assert rows[8] == sorted([f"enrich:{tids[0]}",
                              *(f"enrichment-unrecorded:enrich {t}" for t in tids[1:])])


def test_a_client_that_does_not_keep_usage_per_thread_is_sent_one_call_at_a_time(
        tmp_path: Path) -> None:
    """NEGATIVE: a client that does not say its usage is kept per thread (the tests' stand-ins,
    any wrapper) gets one call at a time whatever `llm_workers` says — a usage read after its
    call could otherwise be another thread's, and land on the wrong ledger row."""
    model = Model()
    model.usage_per_thread = False  # type: ignore[misc]
    pipe = _theses(tmp_path, 8, model)
    assert pipe._llm_workers() == 1
    run, done = pipe.run_enrich(as_of=CALM_AS_OF)
    assert run.status is RunStatus.SUCCEEDED and model.most_live == 1
    assert run.counts["theses_enriched"] == 5
    with pytest.raises(ValueError, match="at least 1"):
        Pipeline(tmp_path / "zero", sources=load_sources(), taxonomy=load_taxonomy(),
                 client=None, llm_workers=0)


def test_the_three_commands_pass_llm_workers_to_the_pipeline(monkeypatch: pytest.MonkeyPatch,
                                                             tmp_path: Path) -> None:
    """`scan`, `enrich` and `reanalyse` hand `--llm-workers` to the pipeline (default
    `config.LLM_WORKERS`). NEGATIVE: 0 is refused by the parser, before any pipeline exists."""
    from vinci.theme_intelligence import __main__ as cli
    from vinci.theme_intelligence import pipeline as pipeline_mod
    from vinci.theme_intelligence.config import LLM_WORKERS

    seen: list[int] = []

    class StopError(Exception):
        pass

    def recorder(*_a: Any, llm_workers: int = -1, **_k: Any) -> Any:
        seen.append(llm_workers)
        raise StopError

    monkeypatch.setattr(pipeline_mod, "Pipeline", recorder)
    monkeypatch.setattr(cli, "_client", lambda required: None)
    reanalyse = ["reanalyse", "--article", "A-x", "--reason", "r", "--as-of", "2026-11-19"]
    for argv in (["scan", "--cache-only"], ["enrich", "--as-of", "2026-11-19"], reanalyse,
                 ["enrich", "--as-of", "2026-11-19", "--llm-workers", "3"]):
        with pytest.raises(StopError):
            cli.main(["--data-dir", str(tmp_path), *argv])
    assert seen == [LLM_WORKERS, LLM_WORKERS, LLM_WORKERS, 3]
    with pytest.raises(SystemExit):
        cli.main(["--data-dir", str(tmp_path), "enrich", "--as-of", "2026-11-19",
                  "--llm-workers", "0"])
    assert seen == [LLM_WORKERS, LLM_WORKERS, LLM_WORKERS, 3]
