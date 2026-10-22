"""THE CHECKED-IN AGENT HOOKS — each pinned against the real checkout, positive and negative.

WHY (2026-10-22). Every rule in CLAUDE.md was advisory: an agent had to remember "no red commit",
"read §5.0 first" and "STOP and flag a change to the decision line". `.claude/settings.json` now
wires three hooks that make them mechanical — a Stop hook that runs the fast half of the gate on
uncommitted changes, a SessionStart hook that prints the §5.0 index, and a PreToolUse guard that
forces a permission prompt before a decision-line file is edited. A hook nothing tests is a note
again, so each one ships here with what it must catch AND what it must leave alone.

The hooks run under the system `python3` (3.9 on the operator's Mac), not the venv; the scripts are
run here with the test interpreter, and a parse at `feature_version=(3, 9)` pins the syntax.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import uuid
from types import ModuleType

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOKS = ROOT / ".claude" / "hooks"
SETTINGS = ROOT / ".claude" / "settings.json"


def _run(script: str, payload: dict[str, object], cwd: pathlib.Path = ROOT,
         env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(HOOKS / script)], input=json.dumps(payload),
                          capture_output=True, text=True, cwd=cwd, timeout=300,
                          env=dict(os.environ, **(env or {})))


def _load(script: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(script.removesuffix(".py"), HOOKS / script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _session() -> str:
    return f"test-{uuid.uuid4().hex}"


# ── the wiring ───────────────────────────────────────────────────────────────────────────────────

def test_settings_wire_each_hook_to_a_script_that_exists() -> None:
    hooks = json.loads(SETTINGS.read_text())["hooks"]
    assert set(hooks) == {"SessionStart", "PreToolUse", "PostToolUse", "Stop"}
    for event, groups in hooks.items():
        for group in groups:
            for hook in group["hooks"]:
                script = re.search(r"\.claude/hooks/(\w+\.py)", hook["command"])
                assert script, f"{event}: {hook['command']} names no hook script"
                assert (HOOKS / script.group(1)).exists(), f"{event}: {script.group(1)} is missing"
    for event in ("PreToolUse", "PostToolUse"):
        matcher = hooks[event][0]["matcher"].split("|")
        assert {"Edit", "Write", "MultiEdit", "NotebookEdit"} <= set(matcher), event


def test_hook_scripts_parse_as_python_3_9() -> None:
    """The system `python3` that runs them is 3.9: newer syntax would break every session."""
    scripts = sorted(HOOKS.glob("*.py"))
    assert len(scripts) == 3
    for script in scripts:
        ast.parse(script.read_text(), filename=str(script), feature_version=(3, 9))


# ── PreToolUse / PostToolUse: the decision-line guard ────────────────────────────────────────────

def _edit(path: str, session: str, event: str = "PreToolUse") -> subprocess.CompletedProcess[str]:
    return _run("decision_path_guard.py", {"session_id": session, "hook_event_name": event,
                                           "tool_name": "Edit",
                                           "tool_input": {"file_path": str(ROOT / path)}})


def test_guard_asks_before_the_proposal_mapping_is_edited() -> None:
    out = _edit("vinci/dossier/verdict.py", _session())
    assert out.returncode == 0
    decision = json.loads(out.stdout)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "ask"
    assert "vinci/dossier/verdict.py" in decision["permissionDecisionReason"]


def test_guard_leaves_an_ordinary_module_alone() -> None:
    out = _edit("vinci/dossier/assemble.py", _session())
    assert out.returncode == 0 and out.stdout == ""


def test_guard_protects_the_hooks_and_the_ci_gate_themselves() -> None:
    """An agent able to rewrite its own guard without asking is the optimizer editing its grader."""
    for path in (".claude/hooks/fast_gate.py", ".claude/settings.json",
                 ".github/workflows/gate.yml", "data/snapshots/decision_ledger.jsonl"):
        out = _edit(path, _session())
        assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask", path


def test_guard_asks_once_per_file_per_session_and_only_after_an_approved_edit() -> None:
    session = _session()
    assert _edit("vinci/scoring/harness.py", session).stdout          # asks
    assert _edit("vinci/scoring/harness.py", session).stdout          # still asks: nothing ran
    # PostToolUse fires only when the edit went through — i.e. the operator approved it
    assert _edit("vinci/scoring/harness.py", session, "PostToolUse").stdout == ""
    assert _edit("vinci/scoring/harness.py", session).stdout == ""    # approved for this session
    assert _edit("vinci/scoring/metrics.py", session).stdout          # another file asks
    assert _edit("vinci/scoring/harness.py", _session()).stdout       # another session asks


def test_guard_is_silent_outside_a_mosaic_checkout(tmp_path: pathlib.Path) -> None:
    target = tmp_path / "vinci" / "dossier" / "verdict.py"
    target.parent.mkdir(parents=True)
    target.write_text("")
    out = _run("decision_path_guard.py", {"session_id": _session(), "hook_event_name": "PreToolUse",
                                          "tool_input": {"file_path": str(target)}})
    assert out.returncode == 0 and out.stdout == ""


# ── SessionStart: the §5.0 index, on the committed STATE.md ──────────────────────────────────────

def test_open_now_indexes_every_row_of_the_committed_state() -> None:
    out = _run("open_now.py", {"cwd": str(ROOT), "source": "startup"})
    assert out.returncode == 0
    lines = (ROOT / "STATE.md").read_text().splitlines()
    head = next(i for i, x in enumerate(lines) if x.startswith("### 5.0"))
    end = next(i for i, x in enumerate(lines[head + 1:], head + 1) if x.startswith("### "))
    rows = [m.group(1) for x in lines[head:end] if (m := re.match(r"^\|\s*(\d+)\s*\|", x))]
    assert rows, "§5.0 has no rows — the corpus this pins against moved"
    for n in rows:
        assert f"  #{n} [" in out.stdout, f"row {n} missing from the index"
    # it says what it leaves out, and stays under the size Claude Code moves into a file
    assert f"{len(rows)} open rows — TITLES ONLY" in out.stdout
    assert re.search(r"STATE\.md lines \d+–\d+", out.stdout)
    assert len(out.stdout) < 10_000


# ── Stop: the fast gate ──────────────────────────────────────────────────────────────────────────

def test_fast_gate_selects_the_tests_that_import_a_changed_module() -> None:
    gate = _load("fast_gate.py")
    chosen = gate.select_tests(ROOT, ["vinci/seal.py"])
    assert "tests/test_seal.py" in chosen
    assert gate.select_tests(ROOT, ["frontend/build.py"]) == []


def _scratch_checkout(tmp_path: pathlib.Path, probe: str) -> pathlib.Path:
    """A minimal git checkout the gate recognises, with one uncommitted file under frontend/."""
    repo = tmp_path / "checkout"
    (repo / "vinci").mkdir(parents=True)
    (repo / "vinci" / "__init__.py").write_text("")
    (repo / "pyproject.toml").write_text('[tool.ruff]\nline-length = 100\n'
                                         '[tool.ruff.lint]\nselect = ["F"]\n')
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "base"], check=True)
    (repo / "frontend").mkdir()
    (repo / "frontend" / "probe.py").write_text(probe)
    return repo


def _stop(repo: pathlib.Path, session: str, continuing: bool) -> subprocess.CompletedProcess[str]:
    return _run("fast_gate.py", {"session_id": session, "cwd": str(repo),
                                 "stop_hook_active": continuing},
                cwd=repo, env={"VENV": sys.executable})


def test_fast_gate_blocks_the_turn_on_a_lint_failure(tmp_path: pathlib.Path) -> None:
    repo = _scratch_checkout(tmp_path, "import os\n")
    out = _stop(repo, _session(), continuing=False)
    assert out.returncode == 2
    assert "FAST GATE FAILED" in out.stderr and "F401" in out.stderr


def test_fast_gate_lets_a_clean_change_finish(tmp_path: pathlib.Path) -> None:
    repo = _scratch_checkout(tmp_path, "VALUE = 1\n")
    out = _stop(repo, _session(), continuing=False)
    assert out.returncode == 0 and out.stderr == ""


def test_fast_gate_gives_up_blocking_after_its_cap(tmp_path: pathlib.Path) -> None:
    """Claude Code's own 8-block cap resets on every tool call; an unfixable failure needs this."""
    repo = _scratch_checkout(tmp_path, "import os\n")
    session = _session()
    codes = [_stop(repo, session, continuing=i > 0).returncode for i in range(4)]
    assert codes == [2, 2, 2, 0]
    last = _stop(repo, session, continuing=True)
    assert "STILL FAILING" in json.loads(last.stdout)["systemMessage"]
    # a fresh stop (not a continuation) starts the count again
    assert _stop(repo, session, continuing=False).returncode == 2
