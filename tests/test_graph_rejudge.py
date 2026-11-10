"""THE COMMITTED EXPOSURE MAP IS RE-JUDGED WITH ITS EXTRACTION HELD FIXED (2026-11-09, audit RG-D16;
operator: "approve the graph re-judge with $3 cap").

`data/graph_coverage.json` was written before the judge's reasons were kept, so its 27
"unsupported" edges cannot be told from failed calls. `coverage.rejudge` re-asks the judge about
each committed edge, against its own committed evidence, through the same prompt, and leaves every
extraction field as it stands. A budgeted client stops the WHOLE run before a call that could pass
the cap, rather than letting the judge's own error handling turn the rest into judge errors.

Every pin runs on REAL edges cut from the committed map; the judge is scripted.
"""
from __future__ import annotations

import copy
import json
import pathlib
from typing import Any

import pytest

from vinci.graph import coverage as gcov
from vinci.graph.judge import JUDGE_ERROR, judge_edges
from vinci.graph.llm import BudgetedLlmClient, BudgetExceededError, LlmClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAP: dict[str, Any] = json.loads((ROOT / "data" / "graph_coverage.json").read_text())


def _report(n: int = 3) -> dict[str, Any]:
    """The committed map cut to its first ``n`` edges and the names they come from."""
    rep = copy.deepcopy(MAP)
    rep["edges"] = rep["edges"][:n]
    focal = {e["focal_ticker"] for e in rep["edges"]}
    rep["per_name"] = [p for p in rep["per_name"] if p["focal"] in focal]
    return rep


class _Judge(LlmClient):
    """Scripted answers; keeps every prompt it was sent."""

    def __init__(self, script: list[dict[str, Any]], model: str = "fake-judge") -> None:
        self._script = iter(script)
        self._model = model
        self.users: list[str] = []
        self.last_usage: dict[str, int] | None = None
        self.max_tokens = 100     # a worst case of $0.0025 of output at claude-opus-4-8

    @property
    def model(self) -> str:
        return self._model

    def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
        self.users.append(user)
        self.last_usage = {"input_tokens": 600, "output_tokens": 60}
        return dict(next(self._script))


def test_the_rejudge_replaces_only_the_verdicts_and_reasons() -> None:
    """(+) Each committed edge gets the judge's verdict and reason; every extraction field stays
    byte for byte; the derived figures are recomputed from the new verdicts."""
    rep = _report(3)
    judge = _Judge([{"verdict": "competitor", "reason": "named as a peer"},
                    {"verdict": "real_supply_chain", "reason": "its supplier"},
                    {"verdict": "real_supply_chain", "reason": "its customer"}])
    out = gcov.rejudge(rep, judge, on="2026-11-09")
    keep = [k for k in rep["edges"][0] if k not in ("verdict", "reason")]
    for old, new in zip(rep["edges"], out["edges"], strict=True):
        assert {k: new[k] for k in keep} == {k: old[k] for k in keep}
    assert [(e["verdict"], e["reason"]) for e in out["edges"]] == [
        ("competitor", "named as a peer"), ("real_supply_chain", "its supplier"),
        ("real_supply_chain", "its customer")]
    assert out["real_edges"] == 2 and out["evidence_precision"] == round(2 / 3, 3)
    assert out["by_class"] == {"competitor": 1, "real_supply_chain": 2}
    assert out["judge_errors"] == 0
    assert out["model"] == MAP["model"]                     # the extraction's model, unchanged
    assert out["judged_by"]["model"] == "fake-judge" and out["judged_by"]["on"] == "2026-11-09"
    assert out["judged_by"]["edges"] == 3
    assert (out["n_names"], out["total_edges"]) == (rep["n_names"], rep["total_edges"])


def test_the_prompt_is_the_judges_own_with_the_filers_full_name() -> None:
    """The judge is asked exactly what `judge_edges` asks of a fresh extraction: the filer's name
    comes from the map's own per-name rows."""
    rep = _report(1)
    judge = _Judge([{"verdict": "real_supply_chain", "reason": "r"}])
    gcov.rejudge(rep, judge, on="2026-11-09")
    e, name = rep["edges"][0], rep["per_name"][0]["name"]
    assert judge.users[0].startswith(f"Filer: {name} ({e['focal_ticker']})\n")
    assert f'"{e["evidence"]}"' in judge.users[0]


def test_an_edge_whose_filer_the_map_does_not_name_refuses() -> None:
    """(-) No filer name for an edge: refused before any call, never a prompt with a blank."""
    rep = _report(1)
    rep["per_name"] = []
    judge = _Judge([])
    with pytest.raises(ValueError, match="names no filer"):
        gcov.rejudge(rep, judge, on="2026-11-09")
    assert judge.users == []


def test_the_budget_stops_the_whole_run_before_a_call_could_pass_it() -> None:
    """(-) A cap the run cannot fit under: the client refuses the call that could cross it, the
    refusal is NOT turned into a judge error (it is no Exception), and no report comes back."""
    rep = _report(3)
    inner = _Judge([{"verdict": "real_supply_chain", "reason": "r"}] * 3,
                   model="claude-opus-4-8")
    # one call is $0.0045 at list price (600 in, 60 out); the first is admitted on its worst case
    # (~$0.0053 of prompt + $0.0025 of max_tokens), the second would pass $0.008 after the first
    budget = BudgetedLlmClient(inner, cap_usd=0.008)
    with pytest.raises(BudgetExceededError, match="cap"):
        gcov.rejudge(rep, budget, on="2026-11-09")
    assert len(inner.users) == 1 and budget.spent_usd == pytest.approx(0.0045)
    assert not issubclass(BudgetExceededError, Exception)
    with pytest.raises(BudgetExceededError):                 # and stays refused
        gcov.rejudge(_report(1), budget, on="2026-11-09")
    assert len(inner.users) == 1
    assert judge_edges(budget, [])["n_edges"] == 0           # no edge, no call, no refusal


def test_a_model_without_a_price_cannot_be_run_under_a_cap() -> None:
    """(-) An unpriced model's cost is UNKNOWN, so no cap can be held: refused before any call."""
    with pytest.raises(ValueError, match="no list price"):
        BudgetedLlmClient(_Judge([], model="claude-sonnet-4-6"), cap_usd=3.0)


def test_a_judge_failure_in_the_rejudge_is_counted_and_bounded() -> None:
    """A call that fails is `judge_error`, counted, out of the precision, its text bounded."""
    rep = _report(2)

    class _Failing(_Judge):
        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            self.users.append(user)
            if len(self.users) == 1:
                raise TimeoutError("x" * 5000)
            return {"verdict": "real_supply_chain", "reason": "r"}

    out = gcov.rejudge(rep, _Failing([]), on="2026-11-09")
    assert out["judge_errors"] == 1 and out["edges"][0]["verdict"] == JUDGE_ERROR
    assert len(out["edges"][0]["reason"]) < 300 and out["evidence_precision"] == 1.0


def test_the_committed_verdicts_reproduce_the_committed_map() -> None:
    """ON THE WHOLE COMMITTED MAP: a judge answering each edge's committed verdict gives back the
    committed derived figures exactly — real edges, the US/global split, density, precision, the
    class counts, shared nodes and super-connectors — so a moved figure after the paid run is the
    verdicts' doing, never the recomputation's."""
    rep = copy.deepcopy(MAP)
    out = gcov.rejudge(rep, _Judge([{"verdict": e["verdict"], "reason": "r"}
                                    for e in rep["edges"]]), on="2026-11-09")
    for k in ("real_edges", "real_us_listed", "real_global", "edges_per_name",
              "real_edges_per_name", "evidence_precision", "by_class", "shared_nodes",
              "super_connectors", "n_names", "names_with_edges", "total_edges", "per_name"):
        assert out[k] == MAP[k], k


def test_the_command_writes_the_map_only_when_every_edge_is_judged(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THROUGH `vinci graph-rejudge`: a cap the run cannot fit leaves the committed map byte for
    byte (exit 1); a cap it fits writes it, with the calls and the list-price cost recorded."""
    import vinci.cli as cli
    import vinci.graph as graph
    from vinci.config import Config

    (tmp_path / "data").mkdir()
    path = tmp_path / "data" / "graph_coverage.json"
    raw = json.dumps(_report(3), indent=2)
    path.write_text(raw)
    monkeypatch.setattr(cli, "get_config", lambda: Config(data_dir=tmp_path / "data"))

    from vinci.graph.judge import JUDGE_MAX_TOKENS

    class _Priced(_Judge):
        def __init__(self, *, model: str, max_tokens: int = 16384) -> None:
            super().__init__([{"verdict": "real_supply_chain", "reason": "named supplier"}] * 3,
                             model="claude-opus-4-8")
            assert max_tokens == JUDGE_MAX_TOKENS     # the command asks for the judge's ceiling
            self.max_tokens = max_tokens

    monkeypatch.setattr(graph, "AnthropicLlmClient", _Priced)
    assert cli.main(["graph-rejudge", "--budget-usd", "0.008"]) == 1
    assert path.read_text() == raw
    assert cli.main(["graph-rejudge", "--budget-usd", "3"]) == 0
    out = json.loads(path.read_text())
    assert [e["reason"] for e in out["edges"]] == ["named supplier"] * 3
    assert out["judged_by"]["calls"] == 3 and out["judged_by"]["cost_usd"] == pytest.approx(0.0135)


def test_the_bound_is_the_calls_worst_case_never_a_guess_from_cheap_calls() -> None:
    """(-) After a cheap call, a call whose OUTPUT alone could cross the cap is refused: the bound
    holds the client's whole ``max_tokens`` of output, never a multiple of what calls cost."""
    inner = _Judge([{"verdict": "real_supply_chain", "reason": "r"}] * 2, model="claude-opus-4-8")
    inner.max_tokens = 16384                       # the real client's default: up to $0.41 out
    budget = BudgetedLlmClient(inner, cap_usd=0.412)
    budget.extract(system="s", user="u", tool={"name": "t"})  # worst case ~$0.4097; $0.0045 spent
    with pytest.raises(BudgetExceededError, match="refused call 2"):
        budget.extract(system="s", user="u", tool={"name": "t"})
    assert len(inner.users) == 1


@pytest.mark.parametrize("cap", [float("nan"), float("inf"), 0.0, -1.0])
def test_a_cap_that_holds_nothing_is_refused(cap: float) -> None:
    """(-) NaN compares False with everything, so a NaN cap would refuse no call: refused, with
    an infinite, zero or negative one, at construction."""
    with pytest.raises(ValueError, match="positive amount"):
        BudgetedLlmClient(_Judge([], model="claude-opus-4-8"), cap_usd=cap)


def test_a_client_without_max_tokens_cannot_be_run_under_a_cap() -> None:
    """(-) No ``max_tokens``: a call's output cost has no bound, so no cap can be held."""
    inner = _Judge([], model="claude-opus-4-8")
    del inner.max_tokens
    with pytest.raises(ValueError, match="no max_tokens"):
        BudgetedLlmClient(inner, cap_usd=3.0)


def test_a_call_that_returns_without_usage_stops_the_run() -> None:
    """(-) A call that came back with no usage record cost an UNKNOWN amount: never counted as
    free, the run stops."""
    class _NoUsage(_Judge):
        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            out = super().extract(system=system, user=user, tool=tool)
            self.last_usage = None
            return out

    budget = BudgetedLlmClient(_NoUsage([{"verdict": "competitor", "reason": "r"}],
                                        model="claude-opus-4-8"), cap_usd=3.0)
    with pytest.raises(BudgetExceededError, match="no usage record"):
        budget.extract(system="s", user="u", tool={"name": "t"})
    assert (budget.attempts, budget.calls, budget.spent_usd) == (1, 0, 0.0)


def test_the_command_writes_nothing_when_an_edge_gets_no_verdict(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) THROUGH `vinci graph-rejudge`: calls that fail (an expired key fails every one, free)
    are judge errors, NO verdicts — the committed map stays byte for byte, exit 1."""
    import vinci.cli as cli
    import vinci.graph as graph
    from vinci.config import Config

    (tmp_path / "data").mkdir()
    path = tmp_path / "data" / "graph_coverage.json"
    raw = json.dumps(_report(3), indent=2)
    path.write_text(raw)
    monkeypatch.setattr(cli, "get_config", lambda: Config(data_dir=tmp_path / "data"))

    class _Expired(_Judge):
        def __init__(self, *, model: str, max_tokens: int = 16384) -> None:
            super().__init__([], model="claude-opus-4-8")
            self.max_tokens = max_tokens

        def extract(self, *, system: str, user: str, tool: dict[str, Any]) -> dict[str, Any]:
            self.users.append(user)
            self.last_usage = None
            raise PermissionError("401 invalid x-api-key")

    monkeypatch.setattr(graph, "AnthropicLlmClient", _Expired)
    assert cli.main(["graph-rejudge", "--budget-usd", "3"]) == 1
    assert path.read_text() == raw
    kept = tmp_path / "incomplete.json"            # the answers are kept, outside the map
    assert cli.main(["graph-rejudge", "--budget-usd", "3", "--failed-out", str(kept)]) == 1
    assert path.read_text() == raw and json.loads(kept.read_text())["judge_errors"] == 3
