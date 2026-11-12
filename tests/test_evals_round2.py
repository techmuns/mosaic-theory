"""Round 2 of #924's review (the coordinator's): the harness's own integrity — one approved budget
shared by every run, a registration that binds the scorer, the held-out rule applied as written,
gold read at the freeze, and the mutants that survived round 1. Every test here failed on
58e97056 before its fix.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import anthropic
import pytest

try:   # the SDK's own HTTP library: httpx2 from anthropic 1.x on (CI: 2.6.0), httpx before (0.112)
    import httpx2 as httpx  # type: ignore[import-not-found]
except ImportError:
    import httpx

from tests.stripped_pages import replayable_text
from vinci.evals import compare as cm
from vinci.evals import gold as gd
from vinci.evals import panel as pn
from vinci.evals import replay as rp
from vinci.evals import report

ROOT = Path(__file__).resolve().parents[1]
FREEZE = rp.load_panel_file()["freeze_ref"]


def _full_history(root: Path = ROOT, ref: str = FREEZE) -> bool:
    """What `pn.motivated_from_git` needs: the freeze commit reachable AND the clone not shallow.
    It raises on ANY shallow repository, so a shallow clone that happens to hold the freeze commit
    errored here instead of skipping (fix request 2, RH-D5 = RG-D22)."""
    git = ["git", "-C", str(root)]
    shallow = subprocess.run([*git, "rev-parse", "--is-shallow-repository"],
                             capture_output=True, text=True).stdout.strip()
    return shallow == "false" and subprocess.run(
        [*git, "cat-file", "-e", f"{ref}^{{commit}}"], capture_output=True).returncode == 0


def test_a_shallow_clone_holding_the_freeze_commit_is_not_full_history(tmp_path: Path) -> None:
    """RH-D5, both halves on a real three-commit repository: its full clone holds history; a
    depth-2 clone holds the freeze commit and is still NOT full history, so the motivated-set tests
    skip there rather than raise. Negative: a ref the clone does not hold is not full history."""
    full = tmp_path / "full"
    git = ["git", "-C", str(full), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q", str(full)], check=True)
    for n in ("a", "b", "c"):
        (full / n).write_text(n)
        subprocess.run([*git, "add", n], check=True)
        subprocess.run([*git, "commit", "-qm", n], check=True)
    freeze = subprocess.run([*git, "rev-parse", "HEAD~1"], capture_output=True, text=True,
                            check=True).stdout.strip()
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "2", f"file://{full}", str(shallow)],
                   check=True)
    assert _full_history(full, freeze)
    assert not _full_history(shallow, freeze)
    assert subprocess.run(["git", "-C", str(shallow), "cat-file", "-e", f"{freeze}^{{commit}}"],
                          capture_output=True).returncode == 0, "the clone must hold the commit"
    assert not _full_history(full, "0" * 40)


@pytest.fixture(scope="module")
def nflx() -> dict[str, Any]:
    page: dict[str, Any] = json.loads(replayable_text("NFLX"))
    return page


class _FakeSdk:
    def __init__(self) -> None:
        self.calls = 0
        self.messages = self

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        usage = SimpleNamespace(input_tokens=24, output_tokens=7000,
                                cache_creation_input_tokens=190000 if self.calls == 1 else 0,
                                cache_read_input_tokens=0 if self.calls == 1 else 190000)
        block = SimpleNamespace(type="tool_use", input={"evidence_balance": "mixed — fake"})
        return SimpleNamespace(usage=usage, content=[block], model="claude-opus-4-8",
                               stop_reason="tool_use")


# ----------------------------------------------- 1. one approved budget, shared; retries metered

def test_a_paid_budget_needs_an_opened_approval(tmp_path: Path) -> None:
    with pytest.raises(rp.ReplayError, match="no approved budget"):
        rp.Budget.load(tmp_path / "ledger.jsonl")
    rp.Budget.open(tmp_path / "ledger.jsonl", cap_usd=5.0, approval="operator: test")
    with pytest.raises(rp.ReplayError, match="already exists"):
        rp.Budget.open(tmp_path / "ledger.jsonl", cap_usd=50.0, approval="again")
    with pytest.raises(rp.ReplayError, match="above the approved"):
        rp.Budget.load(tmp_path / "ledger.jsonl", cap_usd=6.0)
    assert rp.Budget.load(tmp_path / "ledger.jsonl", cap_usd=4.0).cap_usd == 4.0


def test_the_cap_holds_across_runs_and_resumes(tmp_path: Path, nflx: dict[str, Any]) -> None:
    """Two runs under one approval: the second starts from the first's spend, not from $0."""
    ledger = tmp_path / "ledger.jsonl"
    rp.Budget.open(ledger, cap_usd=5.0, approval="operator: test")
    req = rp.capture(nflx, None)
    rp.run_request(req, draws=5, budget=rp.Budget.load(ledger), label="a",
                   draws_out=tmp_path / "a.jsonl", sdk=_FakeSdk())
    first = rp.Budget.load(ledger).spent()
    sdk = _FakeSdk()
    with pytest.raises(rp.BudgetStop, match="would cross the \\$5.00 cap"):
        rp.run_request(req, draws=5, budget=rp.Budget.load(ledger), label="b",
                       draws_out=tmp_path / "b.jsonl", sdk=sdk)
    assert first > 2.0 and sdk.calls == 1


def test_one_guarded_create_is_one_http_attempt(tmp_path: Path, nflx: dict[str, Any]) -> None:
    """The SDK's own retries (max_retries=2) sent unmetered attempts behind one guarded call."""
    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        return httpx.Response(529, json={"type": "error", "error": {"type": "overloaded_error",
                                                                     "message": "busy"}})
    sdk = anthropic.Anthropic(api_key="test-not-a-key", http_client=anthropic.DefaultHttpxClient(
        transport=httpx.MockTransport(handler)))
    ledger = tmp_path / "ledger.jsonl"
    rp.Budget.open(ledger, cap_usd=5.0, approval="operator: test")
    raws = rp.run_request(rp.capture(nflx, None, draws=1), draws=1, budget=rp.Budget.load(ledger),
                          label="r", draws_out=tmp_path / "d.jsonl", sdk=sdk,
                          registration="a-test-registration")   # a real client: RG-D10 asks one
    assert len(attempts) == 1 and raws == [None]
    row = json.loads((tmp_path / "d.jsonl").read_text().splitlines()[0])
    assert row["raw"] is None and "529" in row["error"]


# --------------------------------------------------- 2. the registration binds the scorer

def _reg(**over: Any) -> cm.Registration:
    base: dict[str, Any] = {"base_ref": "A", "cand_ref": "B", "transforms": (), "pages": ("NFLX",),
                            "draws": 5, "targets": ("M-LABEL",), "held_out": (),
                            "scorer": cm.scorer_fingerprint()}
    return cm.Registration(**{**base, **over})


def _run_dir(tmp_path: Path, reg: cm.Registration, rows: list[tuple[str, str, Any]]) -> Path:
    out = tmp_path / "run"
    out.mkdir()
    (out / "registration.json").write_text(reg.to_json(), encoding="utf-8")
    with (out / "draws.jsonl").open("w") as f:
        for t, cond, raw in rows:
            f.write(json.dumps({"label": f"{t}:{cond}", "raw": raw, "stop_reason": "tool_use"})
                    + "\n")
    return out


def _five(raw: Any, t: str = "NFLX") -> list[tuple[str, str, Any]]:
    return [(t, "BASE", raw)] * 5 + [(t, "CAND", raw)] * 5


def test_score_refuses_draws_on_unregistered_pages(tmp_path: Path, nflx: dict[str, Any]) -> None:
    reg = _reg(pages=("CNXC",))
    with pytest.raises(rp.ReplayError, match="registered pages"):
        cm.score_run(_run_dir(tmp_path, reg, _five(nflx["synthesis"])), reg,
                     pages={"NFLX": nflx})


def test_score_refuses_a_draw_count_other_than_registered(tmp_path: Path,
                                                          nflx: dict[str, Any]) -> None:
    reg = _reg(draws=5)
    rows = _five(nflx["synthesis"])[:-1]
    with pytest.raises(rp.ReplayError, match="registered 5 draws"):
        cm.score_run(_run_dir(tmp_path, reg, rows), reg, pages={"NFLX": nflx})


def test_score_refuses_a_registration_other_than_the_runs(tmp_path: Path,
                                                          nflx: dict[str, Any]) -> None:
    out = _run_dir(tmp_path, _reg(), _five(nflx["synthesis"]))
    with pytest.raises(rp.ReplayError, match="not the registration this run"):
        cm.score_run(out, _reg(targets=("M-ABSENT",)), pages={"NFLX": nflx})


def test_score_refuses_a_scorer_other_than_the_registered_one(tmp_path: Path,
                                                              nflx: dict[str, Any]) -> None:
    reg = _reg(scorer="0" * 64)
    with pytest.raises(rp.ReplayError, match="scorer"):
        cm.score_run(_run_dir(tmp_path, reg, _five(nflx["synthesis"])), reg,
                     pages={"NFLX": nflx})


def test_every_score_is_logged_with_its_registration(tmp_path: Path,
                                                     nflx: dict[str, Any]) -> None:
    reg = _reg()
    out = _run_dir(tmp_path, reg, _five(nflx["synthesis"]))
    cm.score_run(out, reg, pages={"NFLX": nflx})
    cm.score_run(out, reg, pages={"NFLX": nflx})
    log = [json.loads(x) for x in (out / "score_log.jsonl").read_text().splitlines()]
    assert len(log) == 2 and {r["registration"] for r in log} == {reg.sha}
    assert log[0]["scorer"] == reg.scorer


def test_an_unknown_target_cannot_be_registered() -> None:
    with pytest.raises(ValueError, match="not a deterministic metric"):
        _reg(targets=("LABEL",))


def test_two_targets_are_read_with_holm() -> None:
    # p 0.03 and 0.04: Holm rejects neither at 0.05 (0.03 > 0.025), although each is below 0.05
    assert cm.holm({"M-LABEL": 0.03, "M-ABSENT": 0.04}) == {"M-LABEL": False, "M-ABSENT": False}
    assert cm.holm({"M-LABEL": 0.01, "M-ABSENT": 0.04}) == {"M-LABEL": True, "M-ABSENT": True}


# --------------------------------------- 3. the held-out rule applied as written; the salt fixed

def test_the_motivated_rule_reads_commit_bodies_and_in_flight_records() -> None:
    if not _full_history():
        pytest.skip("needs the full history")
    tickers = sorted(rp.load_panel_file()["pages"])
    mot = pn.motivated_from_git(ROOT, FREEZE, tickers)
    assert "CNXC" in mot                       # named in commit BODIES only
    # The record as MERGED (#923's squash, a9c59287, on main): the in-flight ref the freeze read,
    # 4449189d, was #923's branch head, and a squash merge leaves it outside every clone's history
    # — main's own gate went red on it (2026-11-07). The merged record names the same five.
    flight = pn.in_flight_names(ROOT, ["a9c59287:docs/records/"
                                       "2026-11-06-the-fact-layers-labels-describe-never-judge.md"],
                                tickers)
    assert {"MCK", "NKE", "ROST", "CNXC", "LLY"} <= flight


def test_under_the_rule_as_written_no_page_is_held_out() -> None:
    frozen = rp.load_panel_file()
    assert frozen["held_out"]["pages"] == []
    assert all(r["motivated"] for r in frozen["rows"])


def test_the_tie_break_salt_is_the_freeze_commit_not_a_chosen_string() -> None:
    frozen = rp.load_panel_file()
    assert frozen["salt"] == frozen["freeze_ref"] and len(frozen["salt"]) == 40
    sel = pn.select_panel(pn.rows_from_json(frozen["rows"]), salt=frozen["salt"])
    assert list(sel.panel) == frozen["panel"]


# ------------------------------------------------------------ 4. gold read at the freeze

def test_gold_pages_are_read_at_the_freeze_not_the_living_tree(tmp_path: Path) -> None:
    if not _full_history():
        pytest.skip("needs the full history")
    ctx = report.gold_context("NFLX")
    frozen = json.loads(subprocess.run(["git", "-C", str(ROOT), "show",
                                        f"{FREEZE}:data/dossiers/NFLX/dossier.json"],
                                       capture_output=True, check=True).stdout)
    assert ctx.page == frozen
    moved = tmp_path / "NFLX"
    moved.mkdir()
    (moved / "dossier.json").write_text(
        replayable_text("NFLX") + " ", encoding="utf-8")
    assert report.living_drift(["NFLX"], pages=tmp_path) == ["NFLX"]


# ------------------------------------------------------- 5. the mutants that survived round 1

def test_the_guard_refuses_a_user_only_or_system_only_change(tmp_path: Path,
                                                             nflx: dict[str, Any]) -> None:
    req = rp.capture(nflx, None)
    ledger = tmp_path / "l.jsonl"
    rp.Budget.open(ledger, cap_usd=20.0, approval="operator: test")
    from vinci.graph.llm import AnthropicLlmClient
    client = AnthropicLlmClient(model="claude-opus-4-8", api_key="test-not-a-key")
    for field in ("user", "system"):
        sdk = _FakeSdk()
        guard = rp.GuardedSdk(sdk, req, rp.Budget.load(ledger), label="t",
                              draws_out=tmp_path / "d.jsonl", client=client)
        kw = json.loads(json.dumps(req.kwargs))
        if field == "user":
            kw["messages"][0]["content"] += " "
        else:
            kw["system"] += " "
        with pytest.raises(rp.BudgetStop, match="differs from the one captured"):
            guard.create(**kw)
        assert sdk.calls == 0


def test_a_system_only_change_reaches_the_comparison(nflx: dict[str, Any]) -> None:
    base = rp.capture(nflx, None)
    cand = rp.Request({**base.kwargs, "system": base.system + " "})
    d = cm.page_diff("NFLX", base, cand)
    assert not d.identical and not d.system_equal and d.user_diff_lines == 0


def _with_unit(raw: dict[str, Any], text: str) -> dict[str, Any]:
    out = json.loads(json.dumps(raw))
    out["key_unknowns"] = [*out["key_unknowns"], text]
    return out


@pytest.mark.parametrize(("metric", "text"), [
    ("M-PATH", "EBITDA has risen every year from $911M (FY17) to $15,957M (LTM)."),
    ("M-SIGN", "The $2,800.0M merger charge is a one-time drag on earnings."),
])
def test_a_worsening_of_path_or_sign_blocks(tmp_path: Path, nflx: dict[str, Any],
                                            metric: str, text: str) -> None:
    raw = nflx["synthesis"]
    reg = _reg()
    rows = [("NFLX", "BASE", raw)] * 5 + [("NFLX", "CAND", _with_unit(raw, text))] * 5
    s = cm.score_run(_run_dir(tmp_path, reg, rows), reg, pages={"NFLX": nflx})
    assert any(r.startswith(f"{metric} worsens") for r in s.reasons), s.reasons


def test_a_proposal_change_alone_blocks(tmp_path: Path, nflx: dict[str, Any]) -> None:
    """LLY's case: bullish 5/5 proposes; 4 bullish + 1 mixed withholds — same modal lean."""
    raw = nflx["synthesis"]

    def lean(k: str) -> dict[str, Any]:
        out = json.loads(json.dumps(raw))
        out["evidence_balance"] = f"{k} — test"
        return out
    bull, mixed = lean("strongly-bullish"), lean("mixed")
    reg = _reg()
    rows = [("NFLX", "BASE", bull)] * 5 + [("NFLX", "CAND", bull)] * 4 + [("NFLX", "CAND", mixed)]
    s = cm.score_run(_run_dir(tmp_path, reg, rows), reg, pages={"NFLX": nflx})
    assert s.proposals["NFLX"]["BASE"] is not None and s.proposals["NFLX"]["CAND"] is None
    assert any("lean moved" in r for r in s.reasons), s.reasons


# --------------------------------------------- 6–7. the $0 child is offline; no capture into repo

def test_the_capture_child_gets_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-secret")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "tok")
    env = rp.child_env("/x")
    assert "ANTHROPIC_API_KEY" not in env and "ANTHROPIC_AUTH_TOKEN" not in env
    assert env["PYTHONPATH"] == "/x"


def test_the_capture_child_has_no_network() -> None:
    code = ("from vinci.evals import capture_child as c; c.block_network(); import socket; "
            "socket.create_connection(('127.0.0.1', 9), timeout=1)")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert done.returncode != 0 and "network is blocked" in done.stderr


def test_capture_refuses_an_out_file_inside_the_repository() -> None:
    from vinci.evals.__main__ import main
    target = ROOT / "tests/fixtures/should-not-exist.json"
    with pytest.raises(rp.ReplayError, match="inside the repository"):
        main(["capture", "--ticker", "NFLX", "--out", str(target)])
    assert not target.exists()


def test_the_gold_split_still_holds(tmp_path: Path) -> None:
    g = gd.load_gold()
    assert sum(x.half == "test" for x in g) == 314


@pytest.fixture(autouse=True)
def _scorer_is_the_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    """These tests pin the harness's other rules under placeholder refs or old commits. Since
    #1030's review round 1 the library runs RG-D12 whole (BASE's production files, the harness
    at `scorer_ref`), which no such ref holds; it is stood in by the fingerprint comparison
    these tests were written against (`tests/evals_scorer_stub.py`). RG-D12's own pins are in
    `tests/test_evals_order8.py` and `tests/test_evals_order8_round1.py`."""
    from tests.evals_scorer_stub import fingerprint_only
    monkeypatch.setattr(cm, "refuse_unless_registered_scorer", fingerprint_only)
