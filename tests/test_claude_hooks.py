"""THE CHECKED-IN AGENT HOOKS — each pinned against the real checkout, positive and negative.

WHY (2026-10-22). Every rule in CLAUDE.md was advisory: an agent had to remember "no red commit",
"read §5.0 first" and "STOP and flag a change to the decision line". `.claude/settings.json` now
wires hooks that make them mechanical — a Stop hook that runs the fast half of the gate on
uncommitted changes, a SessionStart hook that prints the §5.0 index, a PreToolUse guard that
forces a permission prompt before a decision-line file is edited, and a review gate that refuses
`gh pr create` on a code change until `/code-review` has run at effort high or above. A hook
nothing tests is a note again, so each one ships here with what it must catch AND what it must
leave alone.

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

import pytest

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
    assert len(scripts) == 4
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


# ── PreToolUse on Bash: the review gate ──────────────────────────────────────────────────────────
# Transcript lines are built in the shape a real session transcript carries them — an "assistant"
# entry whose message content holds the tool_use (checked against a live transcript, 2026-10-22).

def _tool(tool_id: str, name: str, inp: dict[str, str]) -> str:
    return json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": tool_id, "name": name, "input": inp}]}})


def _review(tool_id: str, args: str = "high --fix") -> str:
    return _tool(tool_id, "Skill", {"skill": "code-review", "args": args})


def _pr(tool_id: str) -> str:
    return _tool(tool_id, "Bash", {"command": "gh pr create --title t --body b"})


def _branch_checkout(tmp_path: pathlib.Path, changed: str) -> pathlib.Path:
    """A checkout on a branch that commits one file (`changed`) on top of `main`."""
    repo = tmp_path / "checkout"
    (repo / "vinci").mkdir(parents=True)
    (repo / "vinci" / "__init__.py").write_text("")
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git, "init", "-q", "-b", "main"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "base"], check=True)
    subprocess.run([*git, "switch", "-qc", "feature"], check=True)
    (repo / changed).parent.mkdir(parents=True, exist_ok=True)
    (repo / changed).write_text("x = 1\n")
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "change"], check=True)
    return repo


def _create(repo: pathlib.Path, transcript: list[str], command: str = "gh pr create --fill",
            tool_id: str = "toolu_now") -> subprocess.CompletedProcess[str]:
    path = repo.parent / "transcript.jsonl"
    path.write_text("\n".join([*transcript, _tool(tool_id, "Bash", {"command": command})]) + "\n")
    return _run("review_gate.py", {"tool_name": "Bash", "tool_use_id": tool_id,
                                   "tool_input": {"command": command}, "cwd": str(repo),
                                   "transcript_path": str(path)}, cwd=repo)


def test_review_gate_refuses_a_code_pr_that_was_never_reviewed(tmp_path: pathlib.Path) -> None:
    out = _create(_branch_checkout(tmp_path, "vinci/probe.py"), [])
    assert out.returncode == 2
    assert "vinci/probe.py" in out.stderr and 'args=\"high --fix\"' in out.stderr


def test_review_gate_lets_a_reviewed_code_pr_through(tmp_path: pathlib.Path) -> None:
    out = _create(_branch_checkout(tmp_path, "vinci/probe.py"), [_review("toolu_r")])
    assert out.returncode == 0 and out.stderr == ""


def test_review_gate_needs_a_fresh_review_for_each_pr(tmp_path: pathlib.Path) -> None:
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    assert _create(repo, [_review("toolu_r"), _pr("toolu_pr1")]).returncode == 2
    reviewed_again = [_review("toolu_r"), _pr("toolu_pr1"), _review("toolu_r2")]
    assert _create(repo, reviewed_again).returncode == 0
    # the call being decided is in the transcript already; it must not count as the "last PR"
    assert _create(repo, [_review("toolu_r")], tool_id="toolu_pr1").returncode == 0


def test_review_gate_does_not_accept_a_low_effort_review(tmp_path: pathlib.Path) -> None:
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    assert _create(repo, [_review("toolu_r", "low --fix")]).returncode == 2
    assert _create(repo, [_review("toolu_r", "--fix")]).returncode == 2


def test_review_gate_does_not_gate_a_docs_or_data_branch(tmp_path: pathlib.Path) -> None:
    for changed in ("docs/records/x.md", "data/snapshots/x.jsonl", "STATE.md"):
        repo = _branch_checkout(tmp_path / changed.replace("/", "_"), changed)
        assert _create(repo, []).returncode == 0, changed


def test_review_gate_ignores_every_other_command(tmp_path: pathlib.Path) -> None:
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    for command in ("gh pr view 782", "gh pr list", "git push -u origin feature"):
        assert _create(repo, [], command=command).returncode == 0, command


def test_review_gate_fails_open_visibly_without_a_transcript(tmp_path: pathlib.Path) -> None:
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    out = _run("review_gate.py", {"tool_name": "Bash", "tool_use_id": "t",
                                  "tool_input": {"command": "gh pr create --fill"},
                                  "cwd": str(repo), "transcript_path": str(tmp_path / "none")},
               cwd=repo)
    assert out.returncode == 0
    assert "WITHOUT a verified code review" in json.loads(out.stdout)["systemMessage"]


# ── regressions from the gate's own code review (high, 2026-10-22) ───────────────────────────────

def test_review_gate_ignores_a_commit_message_that_mentions_pr_creation(
        tmp_path: pathlib.Path) -> None:
    """`gh pr create` quoted inside a message is not a PR — this branch's own commit says it."""
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    quoted = 'bin/commit -m "gh pr create waits for /code-review high --fix"'
    assert _create(repo, [], command=quoted).returncode == 0
    for real in ("cd x && gh pr create --fill", "GH_TOKEN=t gh pr create --fill"):
        assert _create(repo, [], command=real).returncode == 2, real


def test_review_gate_accepts_an_operator_typed_review(tmp_path: pathlib.Path) -> None:
    repo = _branch_checkout(tmp_path, "vinci/probe.py")

    def typed(args: str) -> str:
        return json.dumps({"type": "user", "message": {"content": (
            f"<command-name>/code-review</command-name>\n<command-args>{args}</command-args>")}})

    assert _create(repo, [typed("high --fix")]).returncode == 0
    assert _create(repo, [typed("low")]).returncode == 2


def _committed_checkout(tmp_path: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    repo = tmp_path / "checkout"
    for rel, body in {"vinci/__init__.py": "", **files}.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(body)
    (repo / "pyproject.toml").write_text('[tool.ruff.lint]\nselect = ["F"]\n')
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "base"], check=True)
    return repo


def test_fast_gate_sees_a_deleted_module_its_importers_still_need(tmp_path: pathlib.Path) -> None:
    repo = _committed_checkout(tmp_path, {"vinci/a.py": "X: int = 1\n",
                                          "vinci/b.py": "from vinci.a import X\n\nY: int = X\n"})
    (repo / "vinci" / "a.py").unlink()
    out = _stop(repo, _session(), continuing=False)
    assert out.returncode == 2
    assert "mypy --strict vinci" in out.stderr and "vinci.a" in out.stderr


def test_fast_gate_failure_report_drops_pytest_progress_lines(tmp_path: pathlib.Path) -> None:
    body = ("import pytest\n\n\n@pytest.mark.parametrize('i', range(300))\n"
            "def test_ok(i: int) -> None:\n    assert i >= 0\n\n\n"
            "def test_bad() -> None:\n    assert 1 == 2\n")
    repo = _committed_checkout(tmp_path, {})
    (repo / "tests").mkdir()
    (repo / "tests" / "test_probe.py").write_text(body)
    out = _stop(repo, _session(), continuing=False)
    assert out.returncode == 2
    assert "FAILED tests/test_probe.py::test_bad" in out.stderr
    assert not re.search(r"^[.F]+\s*\[\s*\d+%\]$", out.stderr, re.M)


def test_fast_gate_git_degrades_when_git_cannot_run(monkeypatch: pytest.MonkeyPatch) -> None:
    gate = _load("fast_gate.py")
    monkeypatch.setenv("PATH", "")
    assert gate.git(ROOT, "status") == ""
