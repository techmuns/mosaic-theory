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
import time
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
    assert len(scripts) == 5
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


def test_guard_names_the_approval_line_the_gate_will_want() -> None:
    """2026-11-17 (#1097): a granted prompt is a click nothing durable records, so the ask says
    what the gate will refuse the branch without — the operator's words, in a commit message."""
    reason = json.loads(_edit("vinci/dossier/schemas.py", _session()).stdout)[
        "hookSpecificOutput"]["permissionDecisionReason"]
    assert 'Operator-approved: vinci/dossier/schemas.py "' in reason
    assert ".github/scripts/protected_approval.py" in reason


def test_guard_leaves_an_ordinary_module_alone() -> None:
    out = _edit("vinci/dossier/assemble.py", _session())
    assert out.returncode == 0 and out.stdout == ""


def test_guard_protects_the_hooks_and_the_ci_gate_themselves() -> None:
    """An agent able to rewrite its own guard without asking is the optimizer editing its grader."""
    for path in (".claude/hooks/fast_gate.py", ".claude/settings.json",
                 ".github/workflows/gate.yml", "data/snapshots/decision_ledger.jsonl"):
        out = _edit(path, _session())
        assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask", path


def test_guard_protects_the_gates_configuration_and_the_grader() -> None:
    """RH-D7 and RG-D18 (fix request 2). The guard covered the hooks, the workflows and bin/commit
    but not what configures the gate (pyproject's pytest/ruff/mypy settings, the suite's conftest,
    the CI key check) nor the grader a prompt change is judged by (vinci/evals and its gold sets) —
    an agent could weaken either without a prompt. NEGATIVE: a test or an ordinary fixture is not
    protected, so the prompt stays rare enough to be read."""
    for path in ("pyproject.toml", "tests/conftest.py", ".github/scripts/validate_keys.py",
                 "vinci/evals/metrics.py", "vinci/evals/synthesis_gap_types.json",
                 "vinci/evals/synthesis_panel.json",
                 "tests/fixtures/synthesis_gap_gold/adjudication.jsonl",
                 "tests/fixtures/synthesis_gold/MANIFEST.json"):
        out = _edit(path, _session())
        assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask", path
    for path in ("tests/test_sleeves.py", "tests/fixtures/ciq_reader_contract.json",
                 "vinci/evalsx.py"):
        assert _edit(path, _session()).stdout == "", path


def test_guard_protects_a_shadowing_package_the_gates_overriding_configs_and_its_lock() -> None:
    """#1104 review round 1, item 5. A package of a protected module's name is imported in its
    place; pytest, ruff and mypy each read a config beside or below pyproject.toml's, at any depth;
    gate.yml installs its tools from requirements.lock. NEGATIVE: a near name is not protected."""
    for path in ("vinci/seal/__init__.py", "vinci/dossier/verdict/core.py",
                 "vinci/dossier/schemas/__init__.py", "conftest.py", "tests/sub/conftest.py",
                 "pytest.ini", ".pytest.ini", "pytest.toml", "tox.ini", "setup.cfg", "ruff.toml",
                 "vinci/.ruff.toml", "mypy.ini", ".mypy.ini", "requirements.lock"):
        out = _edit(path, _session())
        assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask", path
    for path in ("vinci/sealer.py", "vinci/dossier/verdict_helpers.py", "tests/conftest_helpers.py",
                 "requirements.txt", "vinci/seal_test/x.py"):
        assert _edit(path, _session()).stdout == "", path


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


def _venv_without(tmp_path: pathlib.Path, stderr: str) -> str:
    """A stand-in venv interpreter whose `-m ruff` prints `stderr` and exits 1, the way Python
    itself answers, and which runs everything else on this interpreter."""
    stand_in = tmp_path / "bare-venv" / "python"
    stand_in.parent.mkdir(parents=True)
    stand_in.write_text(f'#!/bin/sh\nif [ "$1" = "-m" ] && [ "$2" = "ruff" ]; then\n'
                        f"  cat >&2 <<'EOF'\n{stderr}\nEOF\n  exit 1\nfi\n"
                        f'exec "{sys.executable}" "$@"\n')
    stand_in.chmod(0o755)
    return str(stand_in)


def test_fast_gate_warns_and_lets_a_clean_change_finish_when_a_tool_is_missing(
        tmp_path: pathlib.Path) -> None:
    """RH-D2 (= H-D1; operator ruling 2026-11-11, "Approve the fix"). The hook's own rule is that
    missing tooling is a WARNING, never a block — but a venv without ruff answered exit 1 and the
    hook blocked a clean change for up to three turns. The tool's OWN `No module named <tool>` is
    an INCOMPLETE warning."""
    repo = _scratch_checkout(tmp_path, "VALUE = 1\n")
    out = _run("fast_gate.py", {"session_id": _session(), "cwd": str(repo),
                                "stop_hook_active": False},
               cwd=repo, env={"VENV": _venv_without(
                   tmp_path, f"{tmp_path}/bare-venv/python: No module named ruff")})
    assert out.returncode == 0, out.stderr
    message = json.loads(out.stdout)["systemMessage"]
    assert "INCOMPLETE" in message and "ruff is not installed" in message


def test_fast_gate_still_blocks_when_a_tool_fails_importing_something_else(
        tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN: only the tool's own absence may become a warning. A tool that is there but
    fails importing another module is broken, not missing, and still blocks the turn. The shape
    is Python's own for that case — a traceback ending in `ModuleNotFoundError`, the module name
    quoted — not the one-line `<python>: No module named <tool>` of a tool that is absent."""
    repo = _scratch_checkout(tmp_path, "VALUE = 1\n")
    traceback = ('Traceback (most recent call last):\n'
                 '  File "<frozen runpy>", line 198, in _run_module_as_main\n'
                 '  File "ruff/__main__.py", line 4, in <module>\n'
                 "ModuleNotFoundError: No module named 'tomli'")
    out = _run("fast_gate.py", {"session_id": _session(), "cwd": str(repo),
                                "stop_hook_active": False},
               cwd=repo, env={"VENV": _venv_without(tmp_path, traceback)})
    assert out.returncode == 2
    assert "FAST GATE FAILED" in out.stderr and "No module named 'tomli'" in out.stderr


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


def test_review_gate_gates_a_pr_that_moves_only_the_grader(tmp_path: pathlib.Path) -> None:
    """RG-D18's second half (fix request 2): the grader's gap types and panel and its gold sets
    are JSON, which the code rule did not count, so a PR moving only them skipped /code-review and
    Codex. They count now; the docs-and-data test above is the negative half."""
    for changed in ("vinci/evals/synthesis_gap_types.json", "vinci/evals/synthesis_panel.json",
                    "tests/fixtures/synthesis_gap_gold/adjudication.jsonl",
                    "tests/fixtures/synthesis_gold/MANIFEST.json"):
        repo = _branch_checkout(tmp_path / changed.replace("/", "_"), changed)
        assert _create(repo, []).returncode == 2, changed


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


def test_review_gate_reads_a_heredoc_as_data_not_a_pr(tmp_path: pathlib.Path) -> None:
    """Found on the gate's own live transcript: a heredoc that WROTE test code containing
    `cd x && gh pr create` was counted as a PR opened after the review, so the review stopped
    counting. A heredoc body is data, in the transcript and in the command being decided."""
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    heredoc = "cat >> t.py <<'EOF'\nfor c in ('cd x && gh pr create --fill',):\n    pass\nEOF"
    wrote_tests = _tool("toolu_h", "Bash", {"command": heredoc})
    assert _create(repo, [_review("toolu_r"), wrote_tests]).returncode == 0
    assert _create(repo, [], command=heredoc).returncode == 0
    assert _create(repo, [], command="cd x\ngh pr create --fill").returncode == 2


# ── the review gate judges the checkout the PR comes from (2026-10-23) ───────────────────────────
# Found live: the gate read the hook's `cwd` — the SESSION's folder — so `cd <docs-only checkout> &&
# gh pr create` was refused for code files that were merged commits on the session's stale branch,
# and the reverse (a clean session folder, a code PR from elsewhere) would have passed unreviewed.

def _two_branch_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """One repo, `main` checked out and clean, plus a `code` branch and a `docs` branch."""
    repo = tmp_path / "repo"
    (repo / "vinci").mkdir(parents=True)
    (repo / "vinci" / "__init__.py").write_text("")
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git, "init", "-q", "-b", "main"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "base"], check=True)
    for branch, path in (("code", "vinci/probe.py"), ("docs", "docs/note.md")):
        subprocess.run([*git, "switch", "-qc", branch, "main"], check=True)
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text("x = 1\n")
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-qm", branch], check=True)
    subprocess.run([*git, "switch", "-q", "main"], check=True)
    return repo


def test_review_gate_judges_the_checkout_a_leading_cd_names(tmp_path: pathlib.Path) -> None:
    """The live false positive: the session's own folder changes code, the PR's does not."""
    session = _branch_checkout(tmp_path / "session", "vinci/probe.py")
    docs_pr = _branch_checkout(tmp_path / "pr", "docs/records/note.md")
    assert _create(session, [], command=f"cd {docs_pr} && gh pr create --fill").returncode == 0
    assert _create(session, [], command=f'cd "{docs_pr}" && gh pr create --fill').returncode == 0


def test_review_gate_gates_a_code_pr_opened_from_another_checkout(tmp_path: pathlib.Path) -> None:
    """The reverse: a clean session folder no longer waves through a code PR made elsewhere."""
    session = _branch_checkout(tmp_path / "session", "docs/records/note.md")
    code_pr = _branch_checkout(tmp_path / "pr", "vinci/probe.py")
    out = _create(session, [], command=f"cd {code_pr} && gh pr create --fill")
    assert out.returncode == 2 and "vinci/probe.py" in out.stderr
    assert _create(session, [_review("toolu_r")],
                   command=f"cd {code_pr} && gh pr create --fill").returncode == 0


def test_review_gate_judges_the_head_branch_when_one_is_named(tmp_path: pathlib.Path) -> None:
    repo = _two_branch_repo(tmp_path)              # `main` checked out, nothing changed
    for command in ("gh pr create --head code", "gh pr create -H code --base main"):
        out = _create(repo, [], command=command)
        assert out.returncode == 2 and "branch code" in out.stderr, command
    for command in ("gh pr create --head docs", "gh pr create --head=docs --fill"):
        assert _create(repo, [], command=command).returncode == 0, command


def test_review_gate_treats_an_unresolvable_checkout_as_code(tmp_path: pathlib.Path) -> None:
    """`cd "$W"` names a folder only the shell knows: with no `--head`, the gate cannot see the PR
    and fails CLOSED; naming the branch lets it judge the PR exactly."""
    repo = _two_branch_repo(tmp_path)
    out = _create(repo, [], command='cd "$W" && gh pr create --fill')
    assert out.returncode == 2 and "could not be determined" in out.stderr
    assert _create(repo, [_review("toolu_r")], command='cd "$W" && gh pr create').returncode == 0
    assert _create(repo, [], command='cd "$W" && gh pr create --head docs').returncode == 0


def test_review_gate_leaves_a_pr_from_another_repository_alone(tmp_path: pathlib.Path) -> None:
    session = _branch_checkout(tmp_path / "session", "vinci/probe.py")
    other = tmp_path / "other-repo"
    other.mkdir()
    subprocess.run(["git", "-C", str(other), "init", "-q"], check=True)
    assert _create(session, [], command=f"cd {other} && gh pr create --fill").returncode == 0


def test_review_gate_reads_head_through_wrappers_and_fork_syntax(tmp_path: pathlib.Path) -> None:
    """Found by this change's own review: `time gh pr create --head …` hid the flag, and GitHub's
    cross-fork `owner:branch` form named no ref, so both were judged on the wrong thing."""
    repo = _two_branch_repo(tmp_path)
    assert _create(repo, [], command="time gh pr create --head code").returncode == 2
    assert _create(repo, [], command="env A=1 gh pr create --head docs").returncode == 0
    assert _create(repo, [], command="gh pr create --head techmuns:docs").returncode == 0
    assert _create(repo, [], command="gh pr create --head techmuns:code").returncode == 2


# ── PostToolUse on Bash: one `@codex review` request per code PR (2026-10-23) ─────────────────────
# `gh` is a stand-in put first on PATH that records every call it receives. The tool_response is
# the one Claude Code recorded for this session's real `gh pr create` of #788, number and URL
# swapped — all eight real creates in that transcript (#781–#788) carry this exact shape.

URL = "https://github.com/techmuns/mosaic-theory/pull/999"
REQUEST = ["pr", "comment", URL, "--body", "@codex review"]
_FAKE_GH = """
import json, os, sys
with open(os.environ["FAKE_GH_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["pr", "view"]:
    print(os.environ["FAKE_GH_VIEW"])
elif sys.argv[1:3] == ["pr", "list"]:
    print(os.environ.get("FAKE_GH_LIST", "[]"))
elif os.environ["FAKE_GH_FAIL"]:
    sys.exit(os.environ["FAKE_GH_FAIL"])
"""


def _created(url: str = URL) -> dict[str, object]:
    return {"stdout": url, "stderr": "", "interrupted": False, "isImage": False,
            "noOutputExpected": False,
            "gitOperation": {"pr": {"number": int(url.rsplit("/", 1)[-1]), "url": url,
                                    "action": "created"}}}


def _codex_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    repo = _two_branch_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin",
                    "https://github.com/techmuns/mosaic-theory.git"], check=True)
    return repo


def _opened(repo: pathlib.Path, command: str = "gh pr create --head code",
            response: object = None, comments: tuple[str, ...] = (), fail: str = "",
            tool: str = "Bash", prs: list[dict[str, str]] | None = None,
            start: pathlib.Path | None = None
            ) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    """Run the hook on one finished tool call; return its output and every `gh` call it made.
    ``prs`` is what `gh pr list` reports; ``start`` is the session's folder (default ``repo``)."""
    fake = repo.parent / "bin" / "gh"
    fake.parent.mkdir(exist_ok=True)
    fake.write_text(f"#!{sys.executable}\n{_FAKE_GH}")
    fake.chmod(0o755)
    log = repo.parent / f"gh-{uuid.uuid4().hex}.log"
    env = {"PATH": f"{fake.parent}{os.pathsep}{os.environ['PATH']}", "FAKE_GH_LOG": str(log),
           "FAKE_GH_VIEW": json.dumps({"comments": [{"body": b} for b in comments]}),
           "FAKE_GH_LIST": json.dumps(prs or []), "FAKE_GH_FAIL": fail}
    folder = start or repo
    out = _run("codex_request.py", {"tool_name": tool, "hook_event_name": "PostToolUse",
                                    "cwd": str(folder), "tool_input": {"command": command},
                                    "tool_response": _created() if response is None else response},
               cwd=folder, env=env)
    calls = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
    return out, calls


def test_codex_request_is_wired_to_every_finished_bash_call() -> None:
    groups = json.loads(SETTINGS.read_text())["hooks"]["PostToolUse"]
    wired = [g for g in groups if "codex_request.py" in json.dumps(g)]
    assert len(wired) == 1 and wired[0]["matcher"] == "Bash"


def test_codex_request_asks_codex_once_for_a_code_pr(tmp_path: pathlib.Path) -> None:
    out, calls = _opened(_codex_repo(tmp_path))
    assert out.returncode == 0
    assert calls.count(REQUEST) == 1 and calls[-1] == REQUEST
    told = json.loads(out.stdout)["hookSpecificOutput"]
    assert told["hookEventName"] == "PostToolUse"
    assert URL in told["additionalContext"] and "Do not post another" in told["additionalContext"]


def test_codex_request_leaves_a_pr_that_changes_no_code_alone(tmp_path: pathlib.Path) -> None:
    repo = _codex_repo(tmp_path)                    # `main` checked out, nothing changed
    for command in ("gh pr create --head docs", "gh pr create --fill"):
        out, calls = _opened(repo, command)
        assert out.returncode == 0 and out.stdout == "" and calls == [], command


def test_codex_request_uses_the_review_gates_own_code_rule(tmp_path: pathlib.Path) -> None:
    """One rule, two hooks: a PR the gate holds for review is exactly a PR Codex is asked to
    review — including the gate's fail-closed reading of a checkout it cannot resolve."""
    repo = _codex_repo(tmp_path)
    for command in ("gh pr create --head code", "gh pr create --head docs",
                    "time gh pr create --head techmuns:code", "gh pr create --head techmuns:docs",
                    'cd "$W" && gh pr create', "gh pr create --fill"):
        gated = _create(repo, [], command=command).returncode == 2
        _, calls = _opened(repo, command)
        assert (REQUEST in calls) == gated, command


def test_codex_request_posts_nothing_for_what_opened_no_pr(tmp_path: pathlib.Path) -> None:
    """Run from a checkout that DOES change code, so only the not-a-PR reading keeps it quiet
    (found by mutation: on a clean checkout the code rule alone hid a missing check)."""
    repo = _codex_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "switch", "-q", "code"], check=True)
    viewed = {"stdout": f"title:\tt\nnumber:\t999\n--\nView this pull request on GitHub: {URL}\n"}
    for command in ('git commit -m "then gh pr create"', "gh pr view 999", "gh pr list"):
        assert _opened(repo, command, response=viewed)[1] == [], command
    assert _opened(repo, tool="Edit")[1] == []
    browser = {"stdout": "Opening github.com/techmuns/mosaic-theory/compare in your browser."}
    assert _opened(repo, "gh pr create --web --head code", response=browser)[1] == []
    viewed = _created()
    viewed["gitOperation"] = {"pr": {"number": 999, "url": URL, "action": "viewed"}}
    assert _opened(repo, response=viewed)[1] == []


def test_codex_request_reads_gh_output_when_claude_code_records_no_pr(
        tmp_path: pathlib.Path) -> None:
    repo = _codex_repo(tmp_path)
    pushed = {"stdout": f"remote: ...\n{URL}\n",
              "gitOperation": {"branch": {"ref": "origin/code", "action": "pushed"}}}
    assert REQUEST in _opened(repo, "git push -u origin code && gh pr create --head code",
                              response=pushed)[1]


def test_codex_request_does_not_ask_twice(tmp_path: pathlib.Path) -> None:
    repo = _codex_repo(tmp_path)
    for existing in ("@codex review", "@codex review for security regressions"):
        out, calls = _opened(repo, comments=("LGTM", existing))
        assert REQUEST not in calls and out.stdout == "", existing
    assert REQUEST in _opened(repo, comments=("ask @codex review later",))[1]


def test_codex_request_never_comments_on_another_repository(tmp_path: pathlib.Path) -> None:
    repo = _codex_repo(tmp_path)
    elsewhere = _created("https://github.com/nostra-demus/equity-research/pull/12")
    assert _opened(repo, response=elsewhere)[1] == []
    other = tmp_path / "other-repo"
    other.mkdir()
    subprocess.run(["git", "-C", str(other), "init", "-q"], check=True)
    assert _opened(repo, f"cd {other} && gh pr create --fill")[1] == []
    subprocess.run(["git", "-C", str(repo), "remote", "remove", "origin"], check=True)
    assert _opened(repo)[1] == []                   # no origin: the PR's repo cannot be matched


def test_codex_request_matches_origin_however_it_is_written(tmp_path: pathlib.Path) -> None:
    """GitHub names are case-blind and a remote may be ssh or lack `.git`; gh prints its own
    canonical URL, so the match must not depend on how the operator typed the remote."""
    repo = _codex_repo(tmp_path)
    for origin in ("git@github.com:techmuns/mosaic-theory.git",
                   "https://github.com/TechMuns/Mosaic-Theory",
                   "ssh://git@github.com/techmuns/mosaic-theory.git"):
        subprocess.run(["git", "-C", str(repo), "remote", "set-url", "origin", origin], check=True)
        assert REQUEST in _opened(repo)[1], origin


def test_codex_request_warns_and_never_blocks_when_gh_fails(tmp_path: pathlib.Path) -> None:
    repo = _codex_repo(tmp_path)
    out, calls = _opened(repo, fail="HTTP 502: Bad Gateway")
    assert out.returncode == 0 and REQUEST in calls
    told = json.loads(out.stdout)
    assert "could NOT post" in told["systemMessage"] and "HTTP 502" in told["systemMessage"]
    assert f"gh pr comment {URL}" in told["hookSpecificOutput"]["additionalContext"]
    # a long error says it was cut (CLAUDE.md: a truncated output prints its own truncation)
    long = json.loads(_opened(repo, fail="GraphQL: " + "x" * 400)[0].stdout)["systemMessage"]
    assert "[first 300 of 409 characters]" in long


# ── the review gate counts only a create that OPENED a PR (2026-10-26) ───────────────────────────
# Found live 2026-10-23: a `gh pr create` that failed on a wrong `--repo` reset the gate, so the
# review run before it stopped counting and the session had to review a second time. Each result
# below is the shape a real transcript records: the item's `is_error`, and Claude Code's own record
# of the call on the entry's `toolUseResult` (a dict for a call that ran, the error text otherwise).

#: The live failure, verbatim. Piped through `tail -2`, it exited 0: `is_error` is FALSE, and only
#: the missing creation record says no PR opened (4 of the 10 real failed creates read this way).
PIPED_FAILURE = {"stdout": "92\nGraphQL: Could not resolve to a Repository with the name "
                 "'nogods404/mosaic-theory'. (repository)", "stderr": "", "interrupted": False,
                 "isImage": False, "noOutputExpected": False}
EXIT_FAILURE = ('Error: Exit code 1\nPost "https://api.github.com/graphql": dial tcp '
                '20.207.73.85:443: i/o timeout')
REFUSED = ('Error: PreToolUse:Bash hook error: [python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/'
           'review_gate.py"]: PR CREATION IS GATED ON A CODE REVIEW '
           '(.claude/hooks/review_gate.py).')


def _result(tool_id: str, response: object, is_error: bool = False) -> str:
    text = response if isinstance(response, str) else json.dumps(response)
    return json.dumps({"type": "user", "message": {"role": "user", "content": [
        {"tool_use_id": tool_id, "type": "tool_result", "content": text, "is_error": is_error}]},
        "toolUseResult": response})


def test_review_gate_does_not_count_a_create_that_failed(tmp_path: pathlib.Path) -> None:
    """The live incident: review, a create that failed, then the real create — which must pass."""
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    for failed in (_result("toolu_f", PIPED_FAILURE),
                   _result("toolu_f", EXIT_FAILURE, is_error=True),
                   _result("toolu_f", REFUSED, is_error=True)):
        assert _create(repo, [_review("toolu_r"), _pr("toolu_f"), failed]).returncode == 0, failed


def test_review_gate_still_counts_a_create_that_opened_a_pr(tmp_path: pathlib.Path) -> None:
    """A PR that opened still needs its successor reviewed afresh — on Claude Code's own record,
    or on the URL gh prints when there is none (the reading codex_request.py posts on)."""
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    printed = {"stdout": f"remote: ...\n{URL}\n", "stderr": ""}
    for opened in (_result("toolu_pr1", _created()), _result("toolu_pr1", printed)):
        assert _create(repo, [_review("toolu_r"), _pr("toolu_pr1"), opened]).returncode == 2
    retried = [_review("toolu_r"), _pr("toolu_f"), _result("toolu_f", PIPED_FAILURE),
               _pr("toolu_pr1"), _result("toolu_pr1", _created())]
    assert _create(repo, retried).returncode == 2
    reviewed_again = [*retried, _review("toolu_r2"), _pr("toolu_f2"),
                      _result("toolu_f2", REFUSED, is_error=True)]
    assert _create(repo, reviewed_again).returncode == 0


def test_review_gate_still_refuses_after_a_refused_create(tmp_path: pathlib.Path) -> None:
    """A refusal is no review, and skipping it never revives a review an opened PR used up."""
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    refused = [_pr("toolu_f"), _result("toolu_f", REFUSED, is_error=True)]
    assert _create(repo, refused).returncode == 2
    used_up = [_review("toolu_r"), _pr("toolu_pr1"), _result("toolu_pr1", _created()), *refused]
    assert _create(repo, used_up).returncode == 2


def test_review_gate_counts_a_create_whose_outcome_is_not_recorded(tmp_path: pathlib.Path) -> None:
    """No readable outcome counts as OPENED. Measured live 2026-10-26: a call's result is not yet
    in the transcript when the next call of the same message runs, so an earlier create with no
    result may just have opened a PR. Several results in one entry share no `toolUseResult`
    (374 of 87,486 real entries), so a create's record there cannot be read either."""
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    assert _create(repo, [_review("toolu_r"), _pr("toolu_pr1")]).returncode == 2
    # `gh pr create > pr.txt` opens a PR and prints nothing, so Claude Code records none
    silent = {**PIPED_FAILURE, "stdout": ""}
    assert _create(repo, [_review("toolu_r"), _pr("toolu_pr1"),
                          _result("toolu_pr1", silent)]).returncode == 2
    # every real shared entry records None; a record there (none seen) would be another call's
    for record in (None, PIPED_FAILURE):
        shared = json.dumps({"type": "user", "toolUseResult": record, "message": {"content": [
            {"tool_use_id": "toolu_x", "type": "tool_result", "content": "ok", "is_error": False},
            {"tool_use_id": "toolu_pr1", "type": "tool_result", "content": URL,
             "is_error": False}]}})
        assert _create(repo, [_review("toolu_r"), _pr("toolu_pr1"), shared]).returncode == 2


def test_the_hooks_share_one_reading_of_a_created_pr() -> None:
    """The gate counts a PR opened exactly when codex_request.py asks Codex to review it."""
    codex = _load("codex_request.py")
    assert codex.created_pr is codex.review_gate.created_pr


# ── every way this project has opened a PR is a PR opened (2026-10-27) ───────────────────────────
# Found live: #812 was opened with `env -u GH_TOKEN … gh pr create`, which the detector did not read
# as a create — so the review gate never checked it and codex_request.py asked Codex for nothing.
# Replayed over this project's transcripts (531 real creates), two more forms ran unseen: a VAR
# whose value holds a space (`GH_TOKEN=$(cat ~/.mosaic_gh_token)`, 60 creates) and `gh api` POSTing
# to the pulls endpoint (62 — the route a memory note recommended). Every command below is a real
# one from those transcripts, its title or body path shortened and its branch renamed `code`.

#: The command that opened #812.
ENV_UNSET = ("env -u GH_TOKEN -u GITHUB_TOKEN gh pr create --base main --head code "
             "--title \"A later exhibit's refused covenant term withholds the value in force\" "
             "--body-file /tmp/pr.md")
SPACED_VALUE = ('GH_TOKEN=$(cat ~/.mosaic_gh_token) gh pr create --base main --head code \\\n'
                '  --title "R2 EV/Revenue basis — capability only" \\\n  --body-file /tmp/pr187.md')
#: The memory note's route, verbatim but for the placeholders.
API_CREATE = ("env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/techmuns/mosaic-theory/pulls -X POST "
              "-f title=t -f head=code -f base=main -F body=@/tmp/pr.md")
API_CREATES = (
    API_CREATE,
    # the method implied by the fields, inside a command substitution, before a later `cd`
    'N=$(GH_TOKEN="$(cat ~/.mosaic_gh_token)" gh api --method POST repos/techmuns/mosaic-theory/'
    'pulls -f base=main -f head=code -f title="A failed price fetch stops vinci monitor" '
    "-F body=@$SP/pr_body_mon.md --jq '.number'); echo \"PR #$N\"; cd $SP/wt-mon && git push",
    # the fields on continuation lines
    "GH_TOKEN=$(cat ~/.mosaic_gh_token) gh api -X POST repos/techmuns/mosaic-theory/pulls \\\n"
    '  -f title="fix(extractors): SMPL audit triage" \\\n  -f head="code" -f base="main" \\\n'
    "  -F body=@$SCRATCH/pr_body.md 2>&1 | python -c 'import json,sys; print(sys.stdin.read())'",
)
#: Real `gh api` calls on a pull request that open none — merge, reviews, a reply, a reopen, reads.
API_NOT_CREATES = (
    "gh api --method PUT repos/techmuns/mosaic-theory/pulls/203/merge \\\n  -f merge_method=squash",
    "gh api repos/techmuns/mosaic-theory/pulls/333/reviews --jq '.[].state'",
    'gh api repos/techmuns/mosaic-theory/pulls/811/comments/4381711703/replies -f body="DEFERRED"',
    "gh api -X PATCH repos/techmuns/mosaic-theory/pulls/377 -f state=open -f base=main",
    "gh api repos/techmuns/mosaic-theory/pulls/198",
    "gh api 'repos/techmuns/mosaic-theory/pulls?state=open&per_page=50'",
    "gh api repos/techmuns/mosaic-theory/pulls",
    "gh api -X GET repos/techmuns/mosaic-theory/pulls -f state=open",
)


def test_a_pr_create_behind_env_options_or_a_spaced_value_is_read_as_one() -> None:
    gate = _load("review_gate.py")
    for command in (ENV_UNSET, SPACED_VALUE, "env -i PATH=$PATH gh pr create --head code",
                    "env --unset=GH_TOKEN gh pr create --head code", "env -- gh pr new --head code",
                    'GH_TOKEN=$(cat "$HOME/.mosaic_gh_token") gh pr create --head code'):
        assert gate.opens_a_pr(command), command
        assert gate.pr_target(command, str(ROOT)).head == "code", command
    # what was read before still is, and a mention is still not a create
    for command in ("env GH_HOST=github.com gh pr create", "GH_TOKEN= gh pr create --fill"):
        assert gate.opens_a_pr(command), command
    for command in (f"bin/commit -m {json.dumps(ENV_UNSET)}", f"echo {ENV_UNSET!r}",
                    f"cat > t.sh <<'EOF'\n{ENV_UNSET}\nEOF", "env -u GH_TOKEN gh pr view 812"):
        assert not gate.opens_a_pr(command), command


def test_a_gh_api_post_to_the_pulls_endpoint_is_a_pr_create() -> None:
    gate = _load("review_gate.py")
    for command in API_CREATES:
        assert gate.opens_a_pr(command), command
        assert gate.pr_target(command, str(ROOT))[1:] == ("code", "main", False), command
    assert gate.pr_target("gh api /repos/o/r/pulls --input pr.json", str(ROOT)).head is None
    assert gate.opens_a_pr("gh api /repos/o/r/pulls --input pr.json")
    assert gate.pr_target("gh api repos/o/r/pulls -f head=o:code -f base=dev", "/").head == "code"
    # gh's flag parser also takes a short option's value attached (found by this change's review)
    for attached in ("gh api repos/o/r/pulls -fhead=code -ftitle=t",
                     "gh api -XPOST repos/o/r/pulls"):
        assert gate.opens_a_pr(attached), attached
    assert gate.pr_target("gh api repos/o/r/pulls -fhead=code -fbase=main", "/").head == "code"
    for command in API_NOT_CREATES:
        assert not gate.opens_a_pr(command), command
    for command in (f"bin/commit -m {json.dumps(API_CREATE)}",
                    f"cat > t.sh <<'EOF'\n{API_CREATE}\nEOF"):
        assert not gate.opens_a_pr(command), command


def test_review_gate_refuses_every_unreviewed_route_and_judges_its_head(
        tmp_path: pathlib.Path) -> None:
    """End to end through the hook: each route is refused unreviewed and passes after a review,
    and the branch it names — not the checkout it runs in — decides whether it is code."""
    repo = _two_branch_repo(tmp_path)              # `main` checked out, nothing changed
    for command in (ENV_UNSET, SPACED_VALUE, *API_CREATES):
        out = _create(repo, [], command=command)
        assert out.returncode == 2 and "branch code" in out.stderr, command
        assert _create(repo, [_review("toolu_r")], command=command).returncode == 0, command
        docs = command.replace("head=code", "head=docs").replace('head="code"', 'head="docs"')
        assert _create(repo, [], command=docs.replace("--head code", "--head docs")).returncode == 0
    for command in API_NOT_CREATES:
        assert _create(repo, [], command=command).returncode == 0, command


#: A `gh api` create whose head the command does not carry: in the payload file (Codex on #813,
#: P1, its command verbatim) or computed by the shell.
API_HIDDEN_HEAD = ("gh api repos/techmuns/mosaic-theory/pulls --method POST --input pr.json",
                   'gh api repos/techmuns/mosaic-theory/pulls -f head="$B" -f base=main -f title=t')


def test_review_gate_fails_closed_when_a_gh_api_create_hides_its_head(
        tmp_path: pathlib.Path) -> None:
    """Codex on #813 (P1): with the head inside `pr.json`, the gate judged the clean `main`
    checkout the command ran in and let a code PR through unreviewed. An API create names its head
    only in its payload, so one the hook cannot read is UNKNOWN, gated like code — as an
    unresolvable `cd` is."""
    repo = _two_branch_repo(tmp_path)              # `main` checked out, nothing changed
    for command in API_HIDDEN_HEAD:
        out = _create(repo, [], command=command)
        assert out.returncode == 2 and "could not be read" in out.stderr, command
        assert _create(repo, [_review("toolu_r")], command=command).returncode == 0, command
    # a head the command names is still judged exactly, and `gh pr create` with no `--head` still
    # opens the checkout's own branch, so it is still judged there
    assert _create(repo, [], command=API_CREATE.replace("head=code", "head=docs")).returncode == 0
    assert _create(repo, [], command="gh pr create --fill").returncode == 0
    # a PR from another repository's checkout is still that repository's business
    other = tmp_path / "other-repo"
    other.mkdir()
    subprocess.run(["git", "-C", str(other), "init", "-q"], check=True)
    assert _create(repo, [], command=f"cd {other} && {API_HIDDEN_HEAD[0]}").returncode == 0


def test_review_gate_counts_a_pr_opened_through_gh_api(tmp_path: pathlib.Path) -> None:
    """The transcript reads the same way: a PR opened through `gh api` uses up the review before
    it, whether gh printed the URL (`--jq .html_url`) or the whole JSON record."""
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    for printed in ({"stdout": f"999\n{URL}\n", "stderr": ""},
                    {"stdout": json.dumps(API_RECORD), "stderr": ""}):
        opened = [_review("toolu_r"), _tool("toolu_api", "Bash", {"command": API_CREATE}),
                  _result("toolu_api", printed)]
        assert _create(repo, opened).returncode == 2, printed
    # a create the API refused (piped, so it exited 0) opened nothing and voids no review
    refused = {"stdout": '{"message":"Validation Failed","status":"422"}', "stderr": ""}
    failed = [_review("toolu_r"), _tool("toolu_api", "Bash", {"command": API_CREATE}),
              _result("toolu_api", refused)]
    assert _create(repo, failed).returncode == 0


#: What `gh api` prints for a created PR: the record for #812 (GET of the same object 2026-10-27),
#: cut to the keys that carry a URL, in GitHub's order, with the number swapped for the stand-in's.
#: The body cites another PR, as bodies here do — the PR's own URL must still be the one read.
API_RECORD = {
    "url": "https://api.github.com/repos/techmuns/mosaic-theory/pulls/999", "id": 5028538316,
    "html_url": URL, "diff_url": f"{URL}.diff", "patch_url": f"{URL}.patch",
    "issue_url": "https://api.github.com/repos/techmuns/mosaic-theory/issues/999", "number": 999,
    "state": "open", "title": "t",
    "user": {"login": "nogods404", "html_url": "https://github.com/nogods404"},
    "body": "Follows https://github.com/techmuns/mosaic-theory/pull/803.",
    "head": {"ref": "code", "repo": {"html_url": "https://github.com/techmuns/mosaic-theory"}},
    "base": {"ref": "main", "repo": {"html_url": "https://github.com/techmuns/mosaic-theory"}},
    "_links": {"self": {"href": "https://api.github.com/repos/techmuns/mosaic-theory/pulls/999"},
               "html": {"href": URL}},
    "merged": False, "merged_by": None,
}


def test_codex_request_asks_for_a_review_of_a_pr_opened_any_of_these_ways(
        tmp_path: pathlib.Path) -> None:
    """codex_request.py reads the command through the same detector, and finds the PR in what
    `gh api` prints — Claude Code records no `gitOperation` for that route."""
    repo = _codex_repo(tmp_path)
    api_printed = {"stdout": json.dumps(API_RECORD), "stderr": ""}
    for command, response in ((ENV_UNSET, None), (SPACED_VALUE, None),
                              *((c, api_printed) for c in (*API_CREATES, *API_HIDDEN_HEAD))):
        assert REQUEST in _opened(repo, command, response=response)[1], command
    # on a checkout that DOES change code, only the not-a-create reading keeps these quiet
    subprocess.run(["git", "-C", str(repo), "switch", "-q", "code"], check=True)
    for command in API_NOT_CREATES:
        assert _opened(repo, command, response=api_printed)[1] == [], command


def test_the_create_reading_stays_linear_on_a_long_prefix() -> None:
    """Found by this change's own check: a `$(…)` value and `-u NAME` could each be matched two
    ways, so a long run of either that ends in no create backtracked exponentially — 22 `$(a)`
    segments took 1.2 s, each one more doubling it — and a hook runs on every Bash call."""
    gate = _load("review_gate.py")
    for command in ("A=" + "$(a)" * 25 + " echo", "env" + " -u" * 37 + " echo",
                    "env" + " --unset" * 36 + " echo"):
        started = time.perf_counter()
        assert not gate.opens_a_pr(command)
        assert time.perf_counter() - started < 1.0, command[:24]


# ── the re-review: ONE more `@codex review` after a push that fixes what Codex found (2026-10-27)
# Operator, 2026-10-27: a fix written to answer Codex is code Codex never saw, and a push does not
# re-trigger it. Replayed on the real PRs #770–#813, the rule asks on exactly #791, #793, #796 and
# #799 — the four where Codex found issues and the session then pushed code it never re-reviewed.

#: What a finished `git push` returns to the hook: Claude Code records no `gitOperation` for it.
PUSHED = {"stdout": "", "stderr": "To https://github.com/techmuns/mosaic-theory.git\n"
          "   1111111..2222222  HEAD -> code\n", "interrupted": False, "isImage": False,
          "noOutputExpected": False}


def _codex_summary(reviewed: str, found: bool | None = True, status: str = "completed") -> str:
    """Codex's summary comment as it posts it — #811's, verbatim but for the commit and values."""
    state = {"code_review": {"commit_sha": reviewed, "has_any_findings": found,
                             "has_unresolved_findings": found, "status": status},
             "security_review": {"commit_sha": None, "has_any_findings": None,
                                 "has_unresolved_findings": None, "status": None}}
    return ("<!-- codex-pull-request-review-summary -->\n"
            f"<!-- codex-review-state:v1 {json.dumps(state, separators=(',', ':'))} -->\n\n"
            "## Codex Review Summary\n")


def _sha(repo: pathlib.Path, ref: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", ref], capture_output=True,
                          text=True, check=True).stdout.strip()


def _pr_list(head: str, branch: str = "code") -> list[dict[str, str]]:
    return [{"url": URL, "headRefName": branch, "headRefOid": head}]


def _fixed(tmp_path: pathlib.Path, branch: str = "code") -> tuple[pathlib.Path, str, str]:
    """A checkout on ``branch``: Codex reviewed `main`'s commit, the branch's commit is the fix."""
    repo = _codex_repo(tmp_path)
    subprocess.run(["git", "-C", str(repo), "switch", "-q", branch], check=True)
    return repo, _sha(repo, "main"), _sha(repo, branch)


def test_codex_request_asks_again_after_a_push_that_fixes_what_codex_found(
        tmp_path: pathlib.Path) -> None:
    repo, reviewed, head = _fixed(tmp_path)
    out, calls = _opened(repo, "git push -q origin code", response=PUSHED,
                         comments=("@codex review", _codex_summary(reviewed)), prs=_pr_list(head))
    assert out.returncode == 0
    assert calls.count(REQUEST) == 1 and calls[-1] == REQUEST
    told = json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "2 of 2" in told and "round 2" in told and reviewed[:8] in told


def test_codex_request_asks_again_only_when_every_condition_holds(tmp_path: pathlib.Path) -> None:
    repo, reviewed, head = _fixed(tmp_path)
    asked, summary = "@codex review", _codex_summary(reviewed)
    for why, comments, prs in (
            ("Codex found nothing", (asked, _codex_summary(reviewed, found=False)), _pr_list(head)),
            ("its review is still running", (asked, _codex_summary(reviewed, True, "running")),
             _pr_list(head)),
            ("its record names no commit", (asked, _codex_summary("")), _pr_list(head)),
            ("the re-review is spent", (asked, summary, "@codex review again"), _pr_list(head)),
            ("Codex was never asked (no code)", (summary,), _pr_list(head)),
            ("Codex reviewed this very commit", (asked, _codex_summary(head)), _pr_list(head)),
            ("Codex left no record", (asked,), _pr_list(head)),
            ("no open PR has the branch", (asked, summary), []),
            ("the open PR is another branch's", (asked, summary), _pr_list(head, "other"))):
        out, calls = _opened(repo, "git push -q origin code", response=PUSHED, comments=comments,
                             prs=prs)
        assert REQUEST not in calls and out.stdout == "", why
    # a push that changed no CODE since the review (a record, a docs edit) asks nothing
    docs, reviewed, head = _fixed(tmp_path / "d", "docs")
    assert REQUEST not in _opened(docs, "git push", response=PUSHED,
                                  comments=("@codex review", _codex_summary(reviewed)),
                                  prs=_pr_list(head, "docs"))[1]


def test_codex_request_reads_only_a_real_push(tmp_path: pathlib.Path) -> None:
    """Nothing is asked of GitHub for what pushes nothing — a dry run, a mention, another git
    command — so the hook costs no call on the Bash calls that are not pushes."""
    repo, _, head = _fixed(tmp_path)
    for command in ("git push -n origin code", "git push -qn", "git push --dry-run", "git status",
                    "echo 'then git push'", 'git commit -qm "fix, then git push"',
                    "cat > note.md <<'EOF'\ngit push -q\nEOF"):
        assert _opened(repo, command, response=PUSHED, prs=_pr_list(head))[1] == [], command


def test_codex_request_reads_every_way_this_project_pushes(tmp_path: pathlib.Path) -> None:
    """The shapes this project's transcripts push with (2026-10-27): behind the commit message's
    heredoc marker, through the gh credential helper to `HEAD:<branch>`, from a `cd`, with `-C`."""
    repo, reviewed, head = _fixed(tmp_path)
    elsewhere = tmp_path / "session"
    elsewhere.mkdir()
    comments = ("@codex review", _codex_summary(reviewed))
    for command, start in (
            ("git add -A && git commit -q -F - <<'MSG' && git push -q 2>&1 | tail -1\n"
             "Fix what Codex found\n\nCo-Authored-By: Claude <noreply@anthropic.com>\nMSG", repo),
            ("git -c credential.helper= -c 'credential.helper=!gh auth git-credential' "
             "push -q origin HEAD:code", repo),
            (f"cd {repo} && git push -q -u origin code", elsewhere),
            (f"git -C {repo} push", elsewhere),
            (f"git --git-dir {repo}/.git -C {repo} push", elsewhere),
            ("env -u GH_TOKEN git push --force-with-lease", repo)):
        assert REQUEST in _opened(repo, command, response=PUSHED, comments=comments,
                                  prs=_pr_list(head), start=start)[1], command


def test_codex_request_finds_the_pr_a_bare_push_lands_on(tmp_path: pathlib.Path) -> None:
    """A bare `git push` lands on the branch's UPSTREAM, which may be named apart from the local
    branch (a session's worktree branch pushed to the PR's)."""
    repo, reviewed, head = _fixed(tmp_path)
    git = ["git", "-C", str(repo)]
    subprocess.run([*git, "switch", "-qc", "worktree-local"], check=True)
    subprocess.run([*git, "update-ref", "refs/remotes/origin/code", head], check=True)
    subprocess.run([*git, "branch", "-q", "--set-upstream-to=origin/code"], check=True)
    assert REQUEST in _opened(repo, "git push -q", response=PUSHED,
                              comments=("@codex review", _codex_summary(reviewed)),
                              prs=_pr_list(head))[1]


def test_codex_request_says_so_when_the_push_has_not_reached_the_pr(
        tmp_path: pathlib.Path) -> None:
    """A failed push piped through `tail` still exits 0, so the PR's head must BE the pushed
    commit: looked for three times, then the session is told rather than Codex re-reviewing
    the commit it already reviewed."""
    repo, reviewed, _ = _fixed(tmp_path)
    out, calls = _opened(repo, "git push -q 2>&1 | tail -1", response=PUSHED,
                         comments=("@codex review", _codex_summary(reviewed)),
                         prs=_pr_list(reviewed))
    assert REQUEST not in calls and sum(c[:2] == ["pr", "list"] for c in calls) == 3
    told = json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "post the one re-review by hand" in told and f"gh pr comment {URL}" in told
    # a lagging push that changed no code owes Codex nothing, so it advises nothing
    docs, reviewed, _ = _fixed(tmp_path / "d", "docs")
    out, calls = _opened(docs, "git push", response=PUSHED, prs=_pr_list(reviewed, "docs"),
                         comments=("@codex review", _codex_summary(reviewed)))
    assert REQUEST not in calls and out.stdout == ""


def test_codex_request_tells_the_session_to_switch_on_auto_fix(tmp_path: pathlib.Path) -> None:
    """Codex's comments reach a session only through the PR's Auto-fix monitor; #813's session
    missed both reviews' delivery until the operator allowed `mcp__ccd_pr__set_monitor`."""
    told = json.loads(_opened(_codex_repo(tmp_path))[0].stdout)["hookSpecificOutput"]
    assert "Auto-fix" in told["additionalContext"]
    assert "mcp__ccd_pr__set_monitor" in told["additionalContext"]


def test_review_gate_reads_a_create_on_a_heredoc_marker_line(tmp_path: pathlib.Path) -> None:
    """A heredoc's BODY is data; the rest of its marker's line still runs. Read as one, it hid 3
    real creates in this project's transcripts (`… <<'MSG' && git push && gh pr create`)."""
    gate = _load("review_gate.py")
    marker_line = "git commit -q -F - <<'MSG' && git push -q && gh pr create --fill\nbody\nMSG"
    assert gate.opens_a_pr(marker_line)
    assert not gate.opens_a_pr("cat > note.md <<'EOF'\ngh pr create --fill\nEOF")
    repo = _branch_checkout(tmp_path, "vinci/probe.py")
    assert _create(repo, [], command=marker_line).returncode == 2


# ── W77: a protected file written through the Bash tool ──────────────────────────────────────────
#
# Twice on 2026-11-19 a session changed a protected file through the Bash tool, so the guard's ask
# never reached the operator; the commit gate caught both (coordinator B on #1004, comment
# 7031763467). #1133 is one: a Python script rewrote scenarios/IT.json through the record API,
# which builds the path inside vinci/scenarios.py. The guard is wired to Edit|Write only. The fix,
# docs/patches/w77-bash-writes-ask-first.diff, is for the operator to apply (agents do not edit
# .claude/hooks/): it reads each Bash call before it runs and compares git status after it.

W77 = pytest.mark.xfail(strict=True, reason=(
    "W77: the guard runs only on Edit/Write, so a Bash write to a protected file reaches disk with "
    "no ask. The fix is docs/patches/w77-bash-writes-ask-first.diff, for the operator to apply "
    "(agents do not edit .claude/hooks/); applying it turns this into an XPASS, which fails the "
    "suite, and the patch removes this marker."))

IT_RECORD = '{"ticker": "IT", "note": "A"}\n'
#: A stand-in for vinci/scenarios.py's record API (`read_record` → `model_copy` → `write_record`):
#: the caller never names the file, as in #1133.
RECORD_API = '''import json
from pathlib import Path

FOLDER = Path(__file__).parent / "scenarios"


def read_record(ticker):
    return json.loads((FOLDER / f"{ticker}.json").read_text())


def write_record(rec):
    (FOLDER / f"{rec['ticker']}.json").write_text(json.dumps(rec) + "\\n")
'''
#: A repo script that READS a protected file and writes a plain one, as frontend/build.py does.
COUNT_SCRIPT = '''import json
from pathlib import Path

rec = json.loads(Path("scenarios/IT.json").read_text())
Path("notes/count.txt").write_text(str(len(rec)) + "\\n")
'''
#: The #1133 shape: the record read, changed and written back, no protected path in the command.
RECORD_REWRITE = ("python3 - <<'EOF'\nfrom records import read_record, write_record\n"
                  "rec = read_record('IT')\nrec['note'] = 'B'\nwrite_record(rec)\nEOF")


#: A unified diff of scenarios/IT.json from IT_RECORD's note "A" to "P", for `git apply`.
FIX_DIFF = ('diff --git a/scenarios/IT.json b/scenarios/IT.json\n--- a/scenarios/IT.json\n'
            '+++ b/scenarios/IT.json\n@@ -1 +1 @@\n-{"ticker": "IT", "note": "A"}\n'
            '+{"ticker": "IT", "note": "P"}\n')


def _git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
                           *args], check=True, capture_output=True, text=True).stdout


def _protected_checkout(tmp_path: pathlib.Path) -> pathlib.Path:
    """A mosaic checkout holding the two 2026-11-19 incidents' protected files, a plain file, a
    file to copy in, the record-API stand-in, a reading script, a writing shell script, a patch
    and an archive folder; IT.json's note was "0" one commit back; an untracked `__pycache__`
    sits under vinci/evals/; origin/main is HEAD."""
    repo = _committed_checkout(tmp_path, {
        "scenarios/IT.json": IT_RECORD.replace('"A"', '"0"'), "scenarios/archive/.keep": "",
        "vinci/evals/variants.py": "VALUE = 1\n", "notes/plain.md": "plain\n",
        "incoming.json": '{"new": 1}\n', "records.py": RECORD_API, "tools/count.py": COUNT_SCRIPT,
        "tools/write.sh": "echo '{}' > scenarios/IT.json\n", "fix.diff": FIX_DIFF})
    (repo / "scenarios" / "IT.json").write_text(IT_RECORD)
    _git(repo, "commit", "-qam", "note A")
    cache = repo / "vinci" / "evals" / "__pycache__"
    cache.mkdir()
    (cache / "variants.cpython-39.pyc").write_bytes(b"\x00")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _wired(event: str, tool: str) -> list[str]:
    """The hook scripts settings.json runs for ``tool`` on ``event``, chosen as Claude Code chooses
    them: every group whose matcher (a regex; empty or `*` for all) matches the tool's name."""
    scripts: list[str] = []
    for group in json.loads(SETTINGS.read_text())["hooks"].get(event, []):
        matcher = group.get("matcher") or ""
        if matcher in ("", "*") or re.fullmatch(matcher, tool):
            for hook in group["hooks"]:
                found = re.search(r"\.claude/hooks/(\w+\.py)", hook["command"])
                if found:
                    scripts.append(found.group(1))
    return scripts


def _bash_guard(event: str, command: str, repo: pathlib.Path, session: str, call: str,
                wired: bool) -> dict[str, object]:
    """The guard's answer to one Bash call ({} for none). ``wired``: only if settings.json routes
    this event's Bash calls to it, as Claude Code would; else the script is run directly, which
    pins what it does whatever the wiring."""
    if wired and "decision_path_guard.py" not in _wired(event, "Bash"):
        return {}
    out = _run("decision_path_guard.py", {
        "session_id": session, "hook_event_name": event, "tool_name": "Bash",
        "tool_use_id": call, "cwd": str(repo), "tool_input": {"command": command}},
        cwd=repo, env={"CLAUDE_PROJECT_DIR": str(repo)})
    assert out.returncode == 0, out.stderr
    answer: dict[str, object] = json.loads(out.stdout) if out.stdout.strip() else {}
    return answer


def _bash_call(command: str, repo: pathlib.Path, session: str, wired: bool = True,
               ) -> tuple[dict[str, object], subprocess.CompletedProcess[str], dict[str, object]]:
    """One Bash call as Claude Code runs it: PreToolUse, the command itself (bash, in the
    checkout; an ask is taken as granted), then PostToolUse — or PostToolUseFailure when the
    command exits non-zero."""
    call = f"toolu_{uuid.uuid4().hex}"
    before = _bash_guard("PreToolUse", command, repo, session, call, wired)
    ran = subprocess.run(["bash", "-c", command], cwd=repo, capture_output=True, text=True,
                         timeout=60)
    event = "PostToolUse" if ran.returncode == 0 else "PostToolUseFailure"
    return before, ran, _bash_guard(event, command, repo, session, call, wired)


def _asked(answer: dict[str, object]) -> str:
    """The reason of the guard's ask ('' when it did not ask)."""
    decision = answer.get("hookSpecificOutput")
    if isinstance(decision, dict) and decision.get("permissionDecision") == "ask":
        return str(decision.get("permissionDecisionReason", ""))
    return ""


#: (form, command, the protected file it writes) — the forms the brief names (`>`, `tee`,
#: `python -c`, `sed -i`, `cp`/`mv`), the inline heredoc that made 84 of the census's 100 asks, and
#: the reading through `cd` and `bash -c`.
BASH_WRITES = (
    ("redirect", "echo '{}' > scenarios/IT.json", "scenarios/IT.json"),
    ("append", "printf 'X = 2\\n' >> vinci/evals/variants.py", "vinci/evals/variants.py"),
    ("tee", "echo '{}' | tee scenarios/IT.json > /dev/null", "scenarios/IT.json"),
    ("python -c", "python3 -c \"from pathlib import Path; Path('scenarios/IT.json')"
                  ".write_text('{}')\"", "scenarios/IT.json"),
    ("python heredoc", "python3 - <<'EOF'\np = 'vinci/evals/variants.py'\ns = open(p).read()\n"
                       "open(p, 'w').write(s.replace('1', '2'))\nEOF", "vinci/evals/variants.py"),
    ("sed -i", "sed -i.bak 's/1/2/' vinci/evals/variants.py", "vinci/evals/variants.py"),
    ("cp", "cp incoming.json scenarios/IT.json", "scenarios/IT.json"),
    ("mv", "mv incoming.json scenarios/IT.json", "scenarios/IT.json"),
    ("cp into the directory", "cp incoming.json scenarios/", "scenarios/incoming.json"),
    ("cd, then sed -i", "cd vinci && sed -i.bak 's/1/2/' evals/variants.py",
     "vinci/evals/variants.py"),
    ("bash -c", "bash -c \"echo '{}' > scenarios/IT.json\"", "scenarios/IT.json"),
    # A's review of #1155, round 2: the forms the patch reads that no node pinned.
    ("git apply", "git apply fix.diff", "scenarios/IT.json"),
    ("git checkout <ref> --", "git checkout HEAD~1 -- scenarios/IT.json", "scenarios/IT.json"),
    ("git restore --source", "git restore --source HEAD~1 scenarios/IT.json",
     "scenarios/IT.json"),
    ("git mv", "git mv scenarios/IT.json scenarios/IT-old.json", "scenarios/IT.json"),
    ("git rm", "git rm -q scenarios/IT.json", "scenarios/IT.json"),
    ("rm", "rm scenarios/IT.json", "scenarios/IT.json"),
    ("touch a new file", "touch scenarios/NEW.json", "scenarios/NEW.json"),
    ("ln", "ln -sf ../incoming.json scenarios/IT.json", "scenarios/IT.json"),
    ("perl -i", "perl -pi -e 's/A/P/' scenarios/IT.json", "scenarios/IT.json"),
    ("eval", "eval \"echo '{}' > scenarios/IT.json\"", "scenarios/IT.json"),
    ("find -exec", "find notes -maxdepth 0 -exec cp incoming.json scenarios/IT.json \\;",
     "scenarios/IT.json"),
    ("a shell script it runs", "bash tools/write.sh", "scenarios/IT.json"),
    ("source", "source tools/write.sh", "scenarios/IT.json"),
    # Codex on #1155, round 2: the command after `cd X ||` runs where the failed cd started.
    ("after a cd that failed, behind ||",
     "cd /nonexistent-w77 2>/dev/null || printf 'X = 2\\n' >> vinci/evals/variants.py",
     "vinci/evals/variants.py"),
    # Codex on #1155, round 1: a subshell's `cd` ends with the subshell.
    ("after a cd inside a subshell",
     "(cd vinci && true); printf 'X = 2\\n' >> vinci/evals/variants.py", "vinci/evals/variants.py"),
)


@W77
@pytest.mark.parametrize(("form", "command", "rel"), BASH_WRITES, ids=[c[0] for c in BASH_WRITES])
def test_a_bash_write_to_a_protected_file_is_asked_about_before_it_runs(
        tmp_path: pathlib.Path, form: str, command: str, rel: str) -> None:
    """W77. REPRODUCTION: the command, run by bash in the checkout, changes the protected file on
    disk — that half passes today. The ask is what fails: settings.json routes no Bash call to the
    guard, so nothing asked first. With the patch, the ask names the file and the line the gate
    will want, as an Edit's does."""
    repo = _protected_checkout(tmp_path)
    target = repo / rel
    was = target.read_bytes() if target.exists() else None
    before, ran, _ = _bash_call(command, repo, _session())
    assert ran.returncode == 0, ran.stderr
    assert (target.read_bytes() if target.exists() else None) != was, f"{form}: nothing written"
    reason = _asked(before)
    assert reason, f"{form}: {rel} changed on disk and nothing asked first"
    assert f"`{rel}`" in reason
    assert (f'Operator-approved: {rel} "' in reason          # one file: its own line
            or 'Operator-approved: <each file it changes> "' in reason)   # several (`git mv`)


@W77
def test_settings_route_every_bash_call_to_the_guard_before_and_after_it_runs() -> None:
    """Before (PreToolUse: ask on a visible write), after (PostToolUse: report a write the command
    did not show) and after a failure (PostToolUseFailure: a script that wrote, then exited 1)."""
    for event in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
        assert "decision_path_guard.py" in _wired(event, "Bash"), event


@W77
def test_a_script_that_writes_a_protected_file_it_never_names_is_reported_after_it_runs(
        tmp_path: pathlib.Path) -> None:
    """#1133's shape (2026-11-19): the record read, changed and written back through an API that
    builds the path itself. No reading of the command can see the write, so nothing asks before;
    the after-check compares git status, tells the agent to stop and ask, and tells the operator.
    Once per file per session."""
    repo = _protected_checkout(tmp_path)
    session = _session()
    before, ran, after = _bash_call(RECORD_REWRITE, repo, session)
    assert ran.returncode == 0, ran.stderr
    assert json.loads((repo / "scenarios" / "IT.json").read_text())["note"] == "B"
    assert _asked(before) == ""                   # the command names no protected path
    assert after.get("decision") == "block", after
    assert "`scenarios/IT.json`" in str(after["reason"])
    assert "STOP and ask the operator" in str(after["reason"])
    assert "scenarios/IT.json" in str(after["systemMessage"])
    assert "write_record(rec)" in str(after["systemMessage"])   # the command, for the operator
    again = _bash_call(RECORD_REWRITE.replace("'B'", "'C'"), repo, session)[2]
    assert again == {}                            # reported once per file per session


@W77
def test_a_script_that_fails_after_writing_a_protected_file_is_still_reported(
        tmp_path: pathlib.Path) -> None:
    """A Bash call that exits non-zero gets no PostToolUse, only PostToolUseFailure (Claude Code's
    hooks reference), so a script that wrote and then crashed must be read there."""
    repo = _protected_checkout(tmp_path)
    crash = RECORD_REWRITE.replace("write_record(rec)\n",
                                   "write_record(rec)\nraise SystemExit(1)\n")
    _, ran, after = _bash_call(crash, repo, _session())
    assert ran.returncode == 1
    context = after.get("hookSpecificOutput")
    assert isinstance(context, dict), after
    assert context.get("hookEventName") == "PostToolUseFailure"
    assert "`scenarios/IT.json`" in str(context.get("additionalContext"))


@W77
def test_a_granted_bash_ask_covers_that_file_for_the_session_as_an_edit_ask_does(
        tmp_path: pathlib.Path) -> None:
    """Asked once per file per session, whichever tool asked: the grant is recorded when the call
    has run, the asked file is not then reported as unasked, and another session asks again."""
    repo = _protected_checkout(tmp_path)
    session = _session()
    first, _, after = _bash_call("echo '{}' > scenarios/IT.json", repo, session)
    assert _asked(first) and "decision" not in after
    assert _asked(_bash_call("echo '[]' > scenarios/IT.json", repo, session)[0]) == ""
    edit = _run("decision_path_guard.py", {
        "session_id": session, "hook_event_name": "PreToolUse", "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "scenarios" / "IT.json")}})
    assert edit.stdout == ""
    assert _asked(_bash_call("echo '{}' > scenarios/IT.json", repo, _session())[0])


@W77
def test_a_granted_ask_on_a_directory_covers_the_files_the_call_writes_in_it(
        tmp_path: pathlib.Path) -> None:
    """Review round 0: a Python literal naming the folder asks about `scenarios/`; once granted,
    the file the call writes there is not reported as unasked."""
    repo = _protected_checkout(tmp_path)
    command = ("python3 -c \"from pathlib import Path; d = Path('scenarios'); "
               "(d / 'IT.json').write_text('{}')\"")
    before, ran, after = _bash_call(command, repo, _session())
    assert ran.returncode == 0, ran.stderr
    assert "`scenarios/`" in _asked(before)
    assert "decision" not in after


@W77
def test_the_operators_notice_states_its_own_truncation(tmp_path: pathlib.Path) -> None:
    """CLAUDE.md: a truncated output prints its own truncation. Eleven records written through the
    API: the notice lists ten and says so."""
    repo = _protected_checkout(tmp_path)
    command = ("python3 -c \"import records; "
               "[records.write_record({'ticker': f'T{i}'}) for i in range(11)]\"")
    _, ran, after = _bash_call(command, repo, _session())
    assert ran.returncode == 0, ran.stderr
    assert "11 protected file(s) (showing 10 of 11)" in str(after.get("systemMessage"))


@W77
def test_a_granted_over_ask_does_not_cover_a_later_write_of_that_file(
        tmp_path: pathlib.Path) -> None:
    """Codex on #1155, round 1. Inline Python that only READS `scenarios/IT.json` while writing
    another file asks (the accepted over-ask). The grant must not cover the file for the session:
    the call never changed it, so a later write through the record API is still reported."""
    repo = _protected_checkout(tmp_path)
    session = _session()
    reads = ("python3 -c \"import json; d = json.load(open('scenarios/IT.json')); "
             "open('notes/o.json', 'w').write(json.dumps(d))\"")
    first, ran, after = _bash_call(reads, repo, session)
    assert ran.returncode == 0, ran.stderr
    assert "`scenarios/IT.json`" in _asked(first) and after == {}
    later = _bash_call(RECORD_REWRITE, repo, session)[2]
    assert later.get("decision") == "block", later
    assert "`scenarios/IT.json`" in str(later["reason"])


@W77
def test_a_grant_covers_its_file_in_its_own_checkout_only(tmp_path: pathlib.Path) -> None:
    """A's review of #1155, SF1. A grant was keyed by the path alone, so one grant in a scratch
    clone silenced the same file in every checkout of the session — before (no ask) and after (no
    report). It already happened on the Edit path (2026-11-10: a grant on a scratch copy of
    `vinci/ledger/correction.py`, then four unasked Edits of the real one). The ask names its
    checkout."""
    a, b = _protected_checkout(tmp_path / "a"), _protected_checkout(tmp_path / "b")
    session = _session()
    first = _asked(_bash_call("echo '{}' > scenarios/IT.json", a, session)[0])
    assert first and str(a.resolve()) in first
    assert _asked(_bash_call("echo '{}' > scenarios/IT.json", b, session)[0])
    edit = {"session_id": session, "tool_name": "Edit",
            "tool_input": {"file_path": str(a / "vinci" / "evals" / "variants.py")}}
    _run("decision_path_guard.py", {**edit, "hook_event_name": "PostToolUse"})
    elsewhere = {**edit, "hook_event_name": "PreToolUse",
                 "tool_input": {"file_path": str(b / "vinci" / "evals" / "variants.py")}}
    out = _run("decision_path_guard.py", elsewhere)
    assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


@W77
def test_a_grant_on_a_sub_directory_covers_the_files_written_in_it(tmp_path: pathlib.Path) -> None:
    """SF2, the archive-on-supersede shape: a copy into `scenarios/archive` asks (it names the
    folder; its read-only source is the accepted over-ask), says it MAY write, and prescribes no
    `Operator-approved: scenarios/archive` line, which the gate rejects. Granted, the new file it
    lands there is not reported as unasked."""
    repo = _protected_checkout(tmp_path)
    command = ("python3 -c \"import shutil; from pathlib import Path; shutil.copy2("
               "'scenarios/IT.json', Path('scenarios/archive') / 'IT-2026-11-20.json')\"")
    before, ran, after = _bash_call(command, repo, _session())
    assert ran.returncode == 0, ran.stderr
    reason = _asked(before)
    assert "`scenarios/archive`" in reason and "may write it" in reason
    assert 'Operator-approved: scenarios/archive "' not in reason
    assert "decision" not in after, after


@W77
def test_the_operator_is_told_when_a_granted_call_changes_its_file(tmp_path: pathlib.Path) -> None:
    """SF7. An ask may be answered by a permission mode, not a person, so after a granted call the
    operator is told which protected file it changed."""
    repo = _protected_checkout(tmp_path)
    _, _, after = _bash_call("echo '{}' > scenarios/IT.json", repo, _session())
    assert "decision" not in after
    assert "approved" in str(after.get("systemMessage")) and "scenarios/IT.json" in str(
        after.get("systemMessage"))


@W77
def test_a_slow_fsmonitor_does_not_switch_the_after_check_off(tmp_path: pathlib.Path) -> None:
    """SF4. With `core.fsmonitor` set, each `git status` waited on the monitor into its 10 s
    timeout, so the before-reading was lost and a write went unreported. The guard turns the
    monitor off for its own calls."""
    repo = _protected_checkout(tmp_path)
    monitor = tmp_path / "slow-monitor.sh"
    monitor.write_text("#!/bin/sh\nsleep 12\n")
    monitor.chmod(0o755)
    _git(repo, "config", "core.fsmonitor", str(monitor))
    started = time.monotonic()
    _, ran, after = _bash_call(RECORD_REWRITE, repo, _session())
    assert ran.returncode == 0, ran.stderr
    assert after.get("decision") == "block", after
    assert time.monotonic() - started < 9


@W77
def test_an_unwritable_store_still_asks_and_says_its_after_check_is_off(
        tmp_path: pathlib.Path) -> None:
    """SF5. The per-call reading was written before the ask was printed, so a store that cannot be
    written (a full disk, a file where the folder should be) dropped the ask, silently."""
    repo = _protected_checkout(tmp_path)
    store = tmp_path / "tmp"
    store.mkdir()
    (store / "mosaic-theory-hooks").write_text("not a folder")
    out = _run("decision_path_guard.py", {
        "session_id": _session(), "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "tool_use_id": "toolu_store", "cwd": str(repo),
        "tool_input": {"command": "echo '{}' > scenarios/IT.json"}},
        cwd=repo, env={"TMPDIR": str(store), "CLAUDE_PROJECT_DIR": str(repo)})
    answer = json.loads(out.stdout)
    assert _asked(answer)
    assert "after-check is off" in answer["systemMessage"]


@W77
def test_a_failure_in_the_bash_reading_says_so(tmp_path: pathlib.Path) -> None:
    """SF5 (fail loud). The Bash path fails open — a broken guard must not wedge every call — but
    a failure that says nothing reads as "nothing protected here". A corrupt per-call reading
    makes the after-check fail; the operator is told."""
    store = tmp_path / "tmp"
    (store / "mosaic-theory-hooks").mkdir(parents=True)
    session = f"test-{uuid.uuid4().hex}"
    (store / "mosaic-theory-hooks" / f"guard-{session}-call-toolu_bad.json").write_text(
        '{"asked": [], "before": [1]}')
    out = _run("decision_path_guard.py", {
        "session_id": session, "hook_event_name": "PostToolUse", "tool_name": "Bash",
        "tool_use_id": "toolu_bad", "cwd": str(tmp_path), "tool_input": {"command": "ls"}},
        env={"TMPDIR": str(store)})
    assert out.returncode == 0
    assert "failed on this Bash call" in json.loads(out.stdout)["systemMessage"]


def test_the_after_check_never_rewrites_the_index(tmp_path: pathlib.Path) -> None:
    """SF3. A plain `git status` takes the optional index lock to refresh stale stat data, and the
    guard ran two per Bash call: 29 of 150 concurrent `git add` calls failed on `index.lock`. With
    `--no-optional-locks` the index is never written. (Today's guard runs no git on a Bash call,
    so this holds now and must hold after the patch.)"""
    repo = _protected_checkout(tmp_path)
    later = time.time() + 10
    os.utime(repo / "notes" / "plain.md", (later, later))
    index = (repo / ".git" / "index").read_bytes()
    _bash_call("cat notes/plain.md", repo, _session(), wired=False)
    assert (repo / ".git" / "index").read_bytes() == index


def test_taking_the_local_mains_content_is_not_reported(tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN (A's review, round 2). `main` is a safe ref before the call, so its content is
    a known state after it too, as origin/main's is."""
    repo = _protected_checkout(tmp_path)
    _git(repo, "checkout", "-qb", "work")
    _git(repo, "checkout", "-qb", "side")
    (repo / "scenarios" / "IT.json").write_text('{"ticker": "IT", "note": "local main"}\n')
    _git(repo, "commit", "-qam", "local main moves")
    _git(repo, "branch", "-f", "main", "side")
    _git(repo, "checkout", "-q", "work")
    before, ran, after = _bash_call("git checkout main -- scenarios/IT.json", repo, _session(),
                                    wired=False)
    assert ran.returncode == 0, ran.stderr
    assert "local main" in (repo / "scenarios" / "IT.json").read_text()
    assert before == {} and after == {}


def test_a_merge_being_concluded_is_not_reported(tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN. A merge in progress lands the other side's content (MERGE_HEAD's), which the
    gate reads as the merge's own, not as a change the agent made."""
    repo = _protected_checkout(tmp_path)
    _git(repo, "checkout", "-qb", "work")
    _git(repo, "checkout", "-qb", "side")
    (repo / "scenarios" / "IT.json").write_text('{"ticker": "IT", "note": "side"}\n')
    _git(repo, "commit", "-qam", "side")
    _git(repo, "checkout", "-q", "work")
    (repo / "notes" / "plain.md").write_text("work\n")
    _git(repo, "commit", "-qam", "work")
    before, ran, after = _bash_call(
        "git -c user.email=t@t -c user.name=t merge -q --no-commit --no-ff side", repo,
        _session(), wired=False)
    assert ran.returncode == 0, ran.stderr
    assert (repo / ".git" / "MERGE_HEAD").exists()
    assert before == {} and after == {}


#: (form, command) — a Bash call that writes no protected file, or only reads one.
BASH_LEAVES = (
    ("redirect to a plain file", "echo x > notes/plain.md"),
    ("sed -i on a plain file", "sed -i.bak 's/plain/flat/' notes/plain.md"),
    ("python writes a plain file", "python3 -c \"open('notes/out.json', 'w').write('{}')\""),
    ("python with a glob-shaped string", "python3 -c \"import glob; open('notes/out.txt', 'w')"
                                         ".write(str(glob.glob('*')))\""),
    ("mv of a plain file", "mv notes/plain.md notes/moved.md"),
    ("cp from a protected file", "cp scenarios/IT.json notes/copy.json"),
    ("cat", "cat scenarios/IT.json"),
    ("sed -n", "sed -n 1p vinci/evals/variants.py"),
    ("grep into a plain file", "grep -n VALUE vinci/evals/variants.py > notes/grep.txt"),
    ("python reads", "python3 -c \"import json; print(json.load(open('scenarios/IT.json')))\""),
    ("python writes to stdout", "python3 -c \"import sys; "
                                "sys.stdout.write(open('scenarios/IT.json').read())\""),
    ("csv to stdout", "python3 -c \"import csv, json, sys; csv.writer(sys.stdout)"
                      ".writerow(json.load(open('scenarios/IT.json')))\""),
    ("rm an untracked __pycache__", "rm -rf vinci/evals/__pycache__"),
    ("python heredoc reads", "python3 - <<'EOF'\nprint(open('vinci/evals/variants.py').read())\n"
                             "EOF"),
    ("a script that reads scenarios/", "python3 tools/count.py"),
    ("git show into a plain file", "git show HEAD:scenarios/IT.json > notes/old.json"),
    ("git diff", "git diff -- scenarios/IT.json"),
    ("a heredoc body naming writes", "cat > notes/plan.md <<'EOF'\necho '{}' > scenarios/IT.json\n"
                                     "sed -i '' 's/1/2/' vinci/evals/variants.py\nEOF"),
    ("a quoted string naming a write", "echo \"cat > scenarios/IT.json\""),
    ("a comment naming a write", "ls scenarios  # then > scenarios/IT.json"),
    ("restore from the index", "git checkout -- scenarios/IT.json"),
)


@pytest.mark.parametrize(("form", "command"), BASH_LEAVES, ids=[c[0] for c in BASH_LEAVES])
def test_a_bash_call_that_writes_no_protected_file_is_never_asked_about_or_reported(
        tmp_path: pathlib.Path, form: str, command: str) -> None:
    """NEGATIVE PINS (W77). Run straight against the guard script, so they hold whether or not
    settings.json wires it: today the guard says nothing to any Bash call, and with the patch it
    must still say nothing here. Each command really runs, and no protected byte moves."""
    repo = _protected_checkout(tmp_path)
    protected = ("scenarios/IT.json", "vinci/evals/variants.py")
    was = {rel: (repo / rel).read_bytes() for rel in protected}
    before, ran, after = _bash_call(command, repo, _session(), wired=False)
    assert ran.returncode == 0, ran.stderr
    assert before == {} and after == {}, form
    assert {rel: (repo / rel).read_bytes() for rel in protected} == was


def test_a_protected_change_made_before_the_call_is_not_blamed_on_it(
        tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN (W77). The after-check reports what THIS call changed: a protected file already
    modified before it (by an approved Edit, another session, the operator) is not reported by a
    call that only reads it."""
    repo = _protected_checkout(tmp_path)
    (repo / "scenarios" / "IT.json").write_text('{"ticker": "IT", "note": "edited before"}\n')
    before, ran, after = _bash_call("cat scenarios/IT.json && echo x > notes/plain.md", repo,
                                    _session(), wired=False)
    assert ran.returncode == 0 and before == {} and after == {}


def test_taking_mains_own_content_is_neither_asked_about_nor_reported(
        tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN (W77). A re-sync writes protected files, but to main's own content, which the
    gate never counts: `git checkout origin/main -- f` is not asked about, and the content it lands
    is not reported."""
    repo = _protected_checkout(tmp_path)
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    branch = subprocess.run([*git, "branch", "--show-current"], check=True, capture_output=True,
                            text=True).stdout.strip()
    subprocess.run([*git, "checkout", "-qb", "main-moved"], check=True)
    (repo / "scenarios" / "IT.json").write_text('{"ticker": "IT", "note": "main"}\n')
    subprocess.run([*git, "commit", "-qam", "main moves"], check=True)
    subprocess.run([*git, "update-ref", "refs/remotes/origin/main", "HEAD"], check=True)
    subprocess.run([*git, "checkout", "-q", branch], check=True)
    before, ran, after = _bash_call("git checkout origin/main -- scenarios/IT.json", repo,
                                    _session(), wired=False)
    assert ran.returncode == 0, ran.stderr
    assert json.loads((repo / "scenarios" / "IT.json").read_text())["note"] == "main"
    assert before == {} and after == {}
