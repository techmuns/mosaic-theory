"""WHAT EACH DOSSIER BUILD COST AND PRODUCED — the per-name run record, pinned end to end.

WHY (2026-10-23, Stage 0 of the agentic-engineering report). Nothing kept what a build spent, which
of its calls failed, or what it produced, so no change to a prompt or an extractor could be judged
against the process it changed. `assemble_cohort` now leaves one line per name ATTEMPTED under
`<snapshots>/assembly_runs/` (`vinci.dossier.run_metrics`).

Two pins here guard a defect the build found rather than a feature: the shared client kept
`last_usage` in a plain attribute while `assemble_cohort` runs eight names on it at once, so a
thread could read another thread's token counts; and a call that got no response left the PREVIOUS
call's counts in place. Both are driven on the real `AnthropicLlmClient` with only its transport
swapped.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import threading
from types import SimpleNamespace
from typing import Any

import pytest

from tests.sec_offline_support import no_network, seed_sec_cache
from vinci.config import LLM_PRICE_PER_MTOK, Config
from vinci.dossier import assemble as asm
from vinci.dossier import run_metrics
from vinci.dossier.schemas import Dossier
from vinci.graph.llm import AnthropicLlmClient, LlmClient, LlmError, MeteredLlmClient, cost_usd

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = "claude-opus-4-8"


def _msg(tokens: int, stop: str = "tool_use") -> SimpleNamespace:
    usage = SimpleNamespace(input_tokens=tokens, output_tokens=tokens // 10,
                            cache_creation_input_tokens=0, cache_read_input_tokens=0)
    block = SimpleNamespace(type="tool_use", input={"ok": True})
    return SimpleNamespace(stop_reason=stop, usage=usage, content=[block])


def _client(create: Any) -> AnthropicLlmClient:
    client = AnthropicLlmClient(model=MODEL, api_key="test")
    client._client = SimpleNamespace(messages=SimpleNamespace(create=create))  # type: ignore[assignment]  # noqa: SLF001
    return client


# ── the shared client: usage per thread, and never a stale count ────────────────────────────────

def test_each_thread_reads_its_own_calls_usage() -> None:
    """THE RACE. Thread A calls, then thread B calls, then A reads `last_usage`. With a plain
    attribute A read B's count — which is what eight assembly workers on one client did."""
    client = _client(lambda **kw: _msg(1000 if kw["messages"][0]["content"] == "A" else 2000))
    a_called, b_called = threading.Event(), threading.Event()
    seen: dict[str, Any] = {}

    def a() -> None:
        client.extract(system="s", user="A", tool={"name": "t"})
        a_called.set()
        b_called.wait(5)
        seen["a"] = client.last_usage

    def b() -> None:
        a_called.wait(5)
        client.extract(system="s", user="B", tool={"name": "t"})
        seen["b"] = client.last_usage
        b_called.set()

    threads = [threading.Thread(target=a), threading.Thread(target=b)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert seen["a"]["input_tokens"] == 1000, "thread A read another thread's token count"
    assert seen["b"]["input_tokens"] == 2000


def test_a_call_with_no_response_leaves_no_usage_behind() -> None:
    """A connection error bills nothing and returns no usage; the counts of the call BEFORE it
    must not be reported as its own."""
    replies: list[Any] = [_msg(1000), ConnectionError("network down")]

    def create(**kw: Any) -> Any:
        r = replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    client = _client(create)
    client.extract(system="s", user="u", tool={"name": "t"})
    assert client.last_usage is not None
    with pytest.raises(ConnectionError):
        client.extract(system="s", user="u", tool={"name": "t"})
    assert client.last_usage is None


# ── the meter ────────────────────────────────────────────────────────────────────────────────────

def test_the_meter_counts_a_call_that_raises_with_its_billed_usage() -> None:
    """A truncated tool call is billed and raises; it is the call whose cost most needs seeing."""
    replies = [_msg(1000), _msg(3000, stop="max_tokens"), ConnectionError("down")]

    def create(**kw: Any) -> Any:
        r = replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    meter = MeteredLlmClient(_client(create))
    meter.extract(system="s", user="u", tool={"name": "covenant_terms"})
    with pytest.raises(LlmError):
        meter.extract(system="s", user="u", tool={"name": "assemble_dossier_framing"}, cache=True)
    with pytest.raises(ConnectionError):
        meter.extract(system="s", user="u", tool={"name": "assemble_dossier_framing"})
    phases = [(c["phase"], c["ok"], c["cached_prompt"]) for c in meter.calls]
    assert phases == [("covenant_terms", True, False), ("assemble_dossier_framing", False, True),
                      ("assemble_dossier_framing", False, False)]
    assert meter.calls[1]["usage"]["input_tokens"] == 3000
    assert "truncated" in meter.calls[1]["error"]
    assert meter.calls[2]["usage"] is None, "a call with no response must not carry a count"

    def interrupted(**kw: Any) -> Any:
        raise KeyboardInterrupt

    stopped = MeteredLlmClient(_client(interrupted))
    with pytest.raises(KeyboardInterrupt):
        stopped.extract(system="s", user="u", tool={"name": "t"})
    assert stopped.calls[0]["ok"] is False, "an interrupted call was recorded as a success"
    # and the record says how many calls its token totals and cost do NOT cover
    record = run_metrics.name_record(
        run_id="r", ticker="X", started=dt.datetime(2026, 10, 23, tzinfo=dt.UTC),
        finished=dt.datetime(2026, 10, 23, 0, 1, tzinfo=dt.UTC), meter=meter)
    assert record["totals"]["calls"] == 3 and record["totals"]["unmetered_calls"] == 1
    assert record["totals"]["input_tokens"] == 4000 and record["totals"]["failed_calls"] == 2


def test_the_meter_passes_the_request_through_unchanged() -> None:
    """An uncached call must reach the inner client exactly as the caller made it: `cache` is
    added only when the caller set it."""
    seen: list[dict[str, Any]] = []

    class Inner(LlmClient):
        model = MODEL  # type: ignore[assignment]

        def extract(self, **kw: Any) -> dict[str, Any]:  # type: ignore[override]
            seen.append(kw)
            return {}

    meter = MeteredLlmClient(Inner())
    meter.extract(system="s", user="u", tool={"name": "t"})
    meter.extract(system="s", user="u", tool={"name": "t"}, cache=True)
    assert "cache" not in seen[0] and seen[1]["cache"] is True
    assert meter.calls[0]["usage"] is None          # an inner client with no usage is unmetered


def test_cost_is_list_price_and_unknown_is_never_zero() -> None:
    usage = {"input_tokens": 1000, "cache_creation_input_tokens": 100_000,
             "cache_read_input_tokens": 400_000, "output_tokens": 5000}
    # opus-4-8 at $5/$25: 1000*5 + 100000*5*1.25 + 400000*5*0.1 + 5000*25 = 955,000 per 1e6
    assert cost_usd(MODEL, usage) == pytest.approx(0.955)
    assert cost_usd("claude-not-priced", usage) is None
    assert cost_usd(MODEL, None) is None


def test_one_price_table_serves_the_fund_and_theme_intelligence() -> None:
    from vinci.theme_intelligence.config import PRICE_PER_MTOK

    assert PRICE_PER_MTOK is LLM_PRICE_PER_MTOK


# ── end to end: through `assemble_cohort`, read back from the file it wrote ──────────────────────

class _Inner(LlmClient):
    """A client whose usage is kept per thread, as the real one's is."""

    def __init__(self) -> None:
        self._local = threading.local()

    @property
    def model(self) -> str:
        return MODEL

    @property
    def last_usage(self) -> dict[str, int] | None:
        return getattr(self._local, "usage", None)

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        self._local.usage = {"input_tokens": 100, "output_tokens": 50,
                             "cache_creation_input_tokens": 1000 if cache else 0,
                             "cache_read_input_tokens": 0, "max_tokens": 16384}
        if user == "fail":
            raise LlmError("model truncated at max_tokens=16384")
        return {}


def _committed_with_draws() -> Dossier:
    """The first committed dossier whose synthesis carries a draw tally — chosen from the corpus,
    not named, so a re-assembly of any one page cannot redden the pin."""
    for path in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        d = Dossier.model_validate_json(path.read_text())
        if d.synthesis is not None and d.synthesis.draw_agreement is not None:
            return d
    pytest.skip("no committed dossier carries a draw tally")


def _cohort(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path,
            llm: LlmClient | None) -> tuple[list[Any], list[str], list[dict[str, Any]], Dossier]:
    """Two finalists through the real `assemble_cohort`: the first writes a real committed dossier,
    the second is refused by the build's own guard. Returns the cohort result and the records."""
    from vinci.rank import load_candidates_from_snapshot

    recs = load_candidates_from_snapshot(ROOT / "data" / "snapshots" / "candidate_records.jsonl")
    def tick(r: Any) -> str:
        return str(r.data_record.identity.ticker)

    good, bad = recs[0], next(r for r in recs if tick(r) != tick(recs[0]))
    fins = [asm.Finalist(r, rank=i + 1, reference_date=dt.date(2026, 10, 1))
            for i, r in enumerate((good, bad))]
    committed = _committed_with_draws()

    def fake_one(fin: Any, *, llm: Any, **kw: Any) -> Dossier:
        assert llm is None or isinstance(llm, MeteredLlmClient), "a phase saw the raw client"
        if llm is not None:
            llm.extract(system="s", user="u", tool={"name": "covenant_terms"})
            llm.extract(system="s", user="u", tool={"name": "assemble_dossier_framing"}, cache=True)
        if fin is fins[1]:
            if llm is not None:
                with pytest.raises(LlmError):
                    llm.extract(system="s", user="fail", tool={"name": "assemble_dossier_framing"})
            raise asm.DossierAssemblyError("TEST: the synthesis never states 1 MATERIAL figure")
        return committed

    monkeypatch.setattr(asm, "assemble_one", fake_one)
    cfg = Config(data_dir=tmp_path)
    seed_sec_cache(cfg)
    with no_network():
        dossiers, errors = asm.assemble_cohort(fins, cfg=cfg, llm=llm)
    files = sorted((tmp_path / "snapshots" / run_metrics.RUNS_DIR).glob("*.jsonl"))
    assert len(files) == 1, f"one run must write exactly one file: {files}"
    records = [json.loads(x) for x in files[0].read_text().splitlines()]
    by_ticker = {r["ticker"]: r for r in records}
    return dossiers, errors, [by_ticker[tick(good)], by_ticker[tick(bad)]], committed


def test_every_name_attempted_leaves_one_record(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    dossiers, errors, (ok, refused), committed = _cohort(monkeypatch, tmp_path, _Inner())
    assert len(dossiers) == 1 and len(errors) == 1

    assert ok["outcome"] == "written" and ok["error"] is None and ok["model"] == MODEL
    assert [c["phase"] for c in ok["calls"]] == ["covenant_terms", "assemble_dossier_framing"]
    assert ok["totals"] == {"calls": 2, "failed_calls": 0, "unmetered_calls": 0,
                            "input_tokens": 200, "output_tokens": 100,
                            "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 0}
    # 200*5 + 1000*5*1.25 + 100*25 = 9,750 per 1e6
    assert ok["usd"] == pytest.approx(0.00975)
    # what the build PRODUCED, read off the dossier it wrote — invariants of a living artifact
    da = committed.synthesis.draw_agreement if committed.synthesis else None
    assert da is not None and ok["synthesis"]["draws"] == da.model_dump(mode="json")
    assert ok["synthesis"]["lean"] in da.labels, "the lean is not one the draws produced"
    assert ok["flags"] == {"caveats": len(committed.caveats), "qa_flags": len(committed.qa_flags)}

    # the refused build is paid for and counted, its failed call included
    assert refused["outcome"] == "refused" and "MATERIAL figure" in refused["error"]
    assert refused["synthesis"] is None and refused["flags"] is None
    assert refused["totals"]["calls"] == 3 and refused["totals"]["failed_calls"] == 1
    assert refused["calls"][2]["usage"] is not None and refused["usd"] > 0


def test_a_build_with_no_llm_is_recorded_as_costing_nothing(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    _, _, (ok, refused), _ = _cohort(monkeypatch, tmp_path, None)
    assert ok["model"] is None and ok["calls"] == [] and ok["usd"] == 0.0
    assert refused["outcome"] == "refused"


def test_a_lost_record_is_an_error_and_the_dossier_still_stands(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    def broken(self: Any, record: Any) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(run_metrics.RunLog, "add", broken)
    from vinci.rank import load_candidates_from_snapshot

    rec = load_candidates_from_snapshot(ROOT / "data" / "snapshots" / "candidate_records.jsonl")[0]
    committed = _committed_with_draws()
    monkeypatch.setattr(asm, "assemble_one", lambda fin, **kw: committed)
    cfg = Config(data_dir=tmp_path)
    seed_sec_cache(cfg)
    with no_network():
        dossiers, errors = asm.assemble_cohort(
            [asm.Finalist(rec, rank=1, reference_date=dt.date(2026, 10, 1))], cfg=cfg)
    assert dossiers == [committed]
    assert len(errors) == 1 and "run record NOT written" in errors[0] and "disk full" in errors[0]


def test_a_long_error_says_it_was_cut() -> None:
    record = run_metrics.name_record(
        run_id="r", ticker="X", started=dt.datetime(2026, 10, 23, tzinfo=dt.UTC),
        finished=dt.datetime(2026, 10, 23, 0, 1, tzinfo=dt.UTC), meter=None,
        error=RuntimeError("x" * 500))
    assert record["outcome"] == "failed"
    assert record["error"].endswith(f"[first {run_metrics.ERROR_CAP} of 514 characters]")


def test_the_console_summary_counts_every_name() -> None:
    recs = [{"ticker": "A", "outcome": "written", "usd": 1.5, "synthesis": {"lean": "mixed"},
             "totals": {"calls": 8, "failed_calls": 0}},
            {"ticker": "B", "outcome": "refused", "usd": None, "synthesis": None,
             "totals": {"calls": 3, "failed_calls": 1}}]
    lines = run_metrics.summary(recs)
    assert len(lines) == 3
    assert "A" in lines[0] and "$1.50" in lines[0] and "unpriced" in lines[1]
    assert lines[2].strip() == "total $1.50 over 1 of 2 name(s) (1 unpriced)"


def test_a_model_without_a_list_price_costs_unknown_not_zero() -> None:
    class Unpriced(_Inner):
        @property
        def model(self) -> str:
            return "claude-not-priced"

    meter = MeteredLlmClient(Unpriced())
    meter.extract(system="s", user="u", tool={"name": "covenant_terms"})
    record = run_metrics.name_record(
        run_id="r", ticker="X", started=dt.datetime(2026, 10, 23, tzinfo=dt.UTC),
        finished=dt.datetime(2026, 10, 23, 0, 1, tzinfo=dt.UTC), meter=meter)
    assert record["usd"] is None and record["totals"]["input_tokens"] == 100
