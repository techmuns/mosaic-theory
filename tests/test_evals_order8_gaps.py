"""Fix request 2, order 8 — the six gaps B's independent check found in A's order-8 branch
(`claude/order8-evals-harness` at 7d1761b4; #1004, 2026-11-11; operator: "Yes, take B's tests and
close all six"). Tests for gaps 1–5; gap 6 (drawn-once sees only this checkout's and main's rows)
is A's accepted risk and has no test here.

Every test FAILS on 7d1761b4, for the gap's own reason (shown in B's message on #1004). $0: no key,
no network. A PAID path is the one with no SDK injected; it is run with the client class spied, so
a refusal is shown to come before any client exists. Pages are the panel's frozen blobs.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "tests" / "fixtures" / "synthesis_gold"
HELD_OUT = ROOT / "vinci" / "evals" / "held_out_pages.json"
#: PR 2's grader-calibration approval (#925): the sha256 of its ledger's first line,
#: `synthesis-eval-pr2/ledger-b-judge-calibration.jsonl` in the session family's notes folder
#: (opened 2026-11-06T21:11:39+0530; its 14 `judge:test:` calls are the gold's one TEST read).
PR2_JUDGE_APPROVAL = "3e7cc4be361f1a5db05ece120f2353c8083633823dd0b831bebe2a3c354da7ef"


def _frozen(t: str) -> dict[str, Any]:
    from vinci.evals import replay as rp
    panel = rp.load_panel_file()
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                       f"{panel['freeze_ref']}^{{commit}}"], capture_output=True).returncode:
        pytest.skip("needs the history holding the panel's freeze commit")
    return rp.page_at(t, panel["freeze_ref"], expect_blob=panel["pages"][t]["dossier_blob"])


class _Spy:
    built = 0

    def __init__(self, *a: Any, **k: Any) -> None:
        _Spy.built += 1
        raise AssertionError("a paid client was built before the refusal")


@pytest.fixture()
def spy(monkeypatch: pytest.MonkeyPatch) -> type[_Spy]:
    from vinci.evals import replay as rp
    _Spy.built = 0
    monkeypatch.setattr(rp, "AnthropicLlmClient", _Spy)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return _Spy


def _budget(tmp_path: Path, name: str = "ledger") -> Any:
    from vinci.evals import replay as rp
    return rp.Budget.open(tmp_path / f"{name}.jsonl", cap_usd=5.0, approval=f"operator: {name}")


# --------------------- gap 1, RG-D12's scope: production files at BASE's, the harness its own


def _scorer_repo(tmp_path: Path) -> Path:
    """A git repository holding this checkout's scorer files, committed as BASE (A's helper)."""
    from vinci.evals.compare import SCORER_FILES
    repo = tmp_path / "repo"
    for f in SCORER_FILES:
        (repo / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / f, repo / f)
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return repo


def test_a_base_older_than_this_harness_can_be_scored_by_its_production_files(
        tmp_path: Path) -> None:
    """(+) Gap 1. The rule compared EVERY scorer file with BASE's, the harness's own included, so a
    BASE older than the harness — any retrospective, #953's `586fdcfd` among them — was refused
    from every checkout that has the order-8 rules (`refuse_unless_scored_by_base("586fdcfd")`
    names `compare.py`, `capture_child.py`, `replay.py`). What a candidate edits, and the metrics
    borrow, is production's code: THAT must be BASE's. The harness is this checkout's, and its
    fingerprint is the one registered and re-checked at draw and score."""
    from vinci.evals.compare import refuse_unless_scored_by_base, scorer_fingerprint
    repo = _scorer_repo(tmp_path)
    harness = repo / "vinci/evals/compare.py"
    harness.write_text(harness.read_text() + "\n# a harness newer than BASE's\n")
    assert refuse_unless_scored_by_base("HEAD", root=repo) == scorer_fingerprint(repo)


def test_a_production_edit_is_still_refused_beside_a_newer_harness(tmp_path: Path) -> None:
    """(−) Gap 1. The narrower scope never admits a candidate's production edit."""
    from vinci.evals.compare import refuse_unless_scored_by_base
    from vinci.evals.replay import ReplayError
    repo = _scorer_repo(tmp_path)
    for f, note in (("vinci/evals/compare.py", "harness"), ("vinci/dossier/synthesis.py", "cand")):
        (repo / f).write_text((repo / f).read_text() + f"\n# {note}\n")
    with pytest.raises(ReplayError, match=r"vinci/dossier/synthesis\.py"):
        refuse_unless_scored_by_base("HEAD", root=repo)


def test_the_library_register_refuses_a_scorer_that_is_not_bases() -> None:
    """(−) Gap 1, the library half (B's check: not one of the six as numbered; drop if out of
    scope). The rule is called by the CLI only, so `cm.register` still records whichever
    checkout runs it: `register("dc5b8787", "b109e26c")` from today's checkout returns a
    registration scored by today's production files. Nine existing tests do exactly that
    (`test_evals_pr2.py`, `test_evals_pr926_round2.py`, `test_evals_replication_rule.py`)."""
    from vinci.evals import compare as cm
    from vinci.evals.replay import ReplayError
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", "dc5b8787^{commit}"],
                      capture_output=True).returncode:
        pytest.skip("needs the history holding dc5b8787")
    with pytest.raises(ReplayError, match=r"vinci/dossier/synthesis\.py"):
        cm.register("dc5b8787", "b109e26c", targets=["M-LABEL"], pages=["NFLX"])


# ---------------------------------------- gap 2, RG-D10: the library's paid path, registered


def test_a_paid_draw_with_no_registration_is_refused_before_any_client(
        tmp_path: Path, spy: type[_Spy]) -> None:
    """(−) Gap 2. G-D10's own reproduction (`demo_unregistered_run.py`) calls
    `replay.run_request`: nine draws in three "runs", no registration. #958 closed the `run`
    command, not this path, which every paid draw goes through."""
    from vinci.evals import replay as rp
    req = rp.capture(_frozen("MCK"), None, draws=3)
    b = _budget(tmp_path)
    with pytest.raises(rp.ReplayError, match="registration"):
        rp.run_request(req, draws=3, budget=b, label="MCK:try0", draws_out=tmp_path / "d.jsonl")
    assert spy.built == 0 and not any("draw" in r for r in b.rows())


def test_a_real_client_injected_is_a_paid_draw_too(tmp_path: Path) -> None:
    """(−) Gap 2. A real `anthropic` client passed as ``sdk`` spends like none at all. It points
    at a closed local port here, so nothing leaves the machine either way."""
    import anthropic

    from vinci.evals import replay as rp
    real = anthropic.Anthropic(api_key="not-a-key", base_url="http://127.0.0.1:9", max_retries=0)
    req = rp.capture(_frozen("MCK"), None, draws=1)
    with pytest.raises(rp.ReplayError, match="registration"):
        rp.run_request(req, draws=1, budget=_budget(tmp_path), label="MCK:x",
                       draws_out=tmp_path / "d.jsonl", sdk=real)


# ------------------------------- gap 3, RG-D9: the gold's TEST half was read on 2026-11-06


def _repo_with_index(tmp_path: Path, rows: list[dict[str, Any]]) -> Path:
    """A git repository whose `origin/main` holds an index with ``rows`` (A's helper)."""
    from vinci.evals.registry import INDEX
    repo = tmp_path / "repo"
    (repo / INDEX).parent.mkdir(parents=True)
    (repo / INDEX).write_text("".join(json.dumps(r) + "\n" for r in rows))
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "index"],
                 ["update-ref", "refs/remotes/origin/main", "HEAD"]):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    return repo


def test_the_committed_index_records_pr2s_test_read() -> None:
    """(−) Gap 3. "TEST read once" is a claim about the GOLD, and its TEST half has been read:
    PR 2 (#925), 2026-11-06, 14 calls under the grader calibration's approval. An index that
    starts empty admits one more read under any approval. The read is recorded as a row that says
    it was added after the fact."""
    from vinci.evals import registry
    reads = [r for r in registry.working_rows(ROOT) if r.get("event") == "judge_test_read"]
    assert [r.get("approval") for r in reads] == [PR2_JUDGE_APPROVAL], reads


def test_no_new_approval_can_read_test_against_the_committed_index(tmp_path: Path) -> None:
    """(−) Gap 3, at the claim: main holding the committed index, a new approval is refused."""
    from vinci.evals import registry
    from vinci.evals.replay import ReplayError
    repo = _repo_with_index(tmp_path, registry.working_rows(ROOT))
    with pytest.raises(ReplayError, match="TEST half"):
        registry.claim_judge_test(approval="a" * 64, root=repo)


# ------------------------ gap 4, RG-D11's "before any paid draw": run-compare and run too


def _captured_and_registration() -> tuple[Any, Any]:
    from vinci.evals import compare as cm
    from vinci.evals import replay as rp
    base = rp.capture(_frozen("NFLX"), None, draws=2)
    cand = rp.Request(json.loads(json.dumps({**base.kwargs, "system": base.system + " "})))
    c = cm.Captured("A", "B", ())
    c.requests[("NFLX", "BASE")], c.requests[("NFLX", "CAND")] = base, cand
    c.diffs.append(cm.PageDiff("NFLX", False, 0, False, {}, {}))
    reg = cm.Registration(base_ref="A", cand_ref="B", transforms=(), pages=("NFLX",), draws=2,
                          targets=("M-LABEL",), held_out=(), scorer=cm.scorer_fingerprint(),
                          requests=cm.request_pins(c))
    return c, reg


def _gold_moved(monkeypatch: pytest.MonkeyPatch) -> None:
    from vinci.evals import gold as gd

    def moved(*a: Any, **k: Any) -> None:
        raise ValueError("adjudicated.jsonl is not the file the manifest hashed")
    monkeypatch.setattr(gd, "verify_gold", moved)


def test_a_paid_run_compare_checks_the_gold_first(tmp_path: Path, spy: type[_Spy],
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Gap 4. The order's done-when: "registration and the gold hashes are checked before
    any paid draw". `verify_gold` runs inside `load_gold` only, and `run-compare` never loads
    the gold, so its paid draws were preceded by no check."""
    from vinci.evals import compare as cm
    c, reg = _captured_and_registration()
    _gold_moved(monkeypatch)
    with pytest.raises(ValueError, match="manifest"):
        cm.run_compare(c, budget=_budget(tmp_path), out_dir=tmp_path / "run", registration=reg)
    assert spy.built == 0


def test_a_paid_build_checks_the_gold_first(tmp_path: Path, spy: type[_Spy],
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Gap 4, `run`'s path (`builds.run_build`)."""
    from vinci.evals import builds as bd
    from vinci.evals import replay as rp
    req = rp.capture(_frozen("NFLX"), None, draws=2)
    reg = bd.RunRegistration(code_ref="0" * 40, transforms=(), pages=("NFLX",), draws=2,
                             builds=2, min_gap_s=300.0, requests={"NFLX": bd.request_sha(req)},
                             inputs={"ciq_root": "/ciq"})
    monkeypatch.setattr(bd, "capture_request", lambda *a, **k: req)
    _gold_moved(monkeypatch)
    with pytest.raises(ValueError, match="manifest"):
        bd.run_build(reg, "NFLX", 1, budget=_budget(tmp_path), draws_out=tmp_path / "d.jsonl",
                     ciq_root=tmp_path)
    assert spy.built == 0


# --------------------------- gap 5, the held-out pages: never scored, and each one replayable


def test_the_gold_report_never_scores_a_held_out_page() -> None:
    """(−) Gap 5. `python -m vinci.evals gold` is the command a metric change re-runs (RUNBOOKS
    §n step 7); it printed TEST precision and recall over the six held-out pages' claims on every
    run, so they were read while metrics were tuned."""
    from vinci.evals import gold as gd
    from vinci.evals import report
    held = set(json.loads(HELD_OUT.read_text())["pages"])
    gold = gd.load_gold()
    n_test = sum(g.half == "test" and g.page not in held for g in gold)
    lines = [x for x in report.gold_report().splitlines() if " test n=" in x]
    assert lines and all(f" test n={n_test}:" in x for x in lines), lines[:1]


def test_every_held_out_page_has_a_transcript_the_replay_can_read() -> None:
    """(−) Gap 5. A held-out page is kept for an evaluation no fix has seen; one the replay cannot
    rebuild cannot be drawn faithfully. The panel's own rule excludes a page whose frozen row
    has no CIQ transcript (TECX and ORKA, `synthesis_panel.json`)."""
    from vinci.evals import replay as rp
    rows = {r["ticker"]: r for r in rp.load_panel_file()["rows"]}
    held = json.loads(HELD_OUT.read_text())["pages"]
    assert [t for t in held if rows[t]["transcripts"] < 1] == []

