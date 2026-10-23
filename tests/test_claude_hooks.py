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
            tool: str = "Bash") -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    """Run the hook on one finished tool call; return its output and every `gh` call it made."""
    fake = repo.parent / "bin" / "gh"
    fake.parent.mkdir(exist_ok=True)
    fake.write_text(f"#!{sys.executable}\n{_FAKE_GH}")
    fake.chmod(0o755)
    log = repo.parent / f"gh-{uuid.uuid4().hex}.log"
    env = {"PATH": f"{fake.parent}{os.pathsep}{os.environ['PATH']}", "FAKE_GH_LOG": str(log),
           "FAKE_GH_VIEW": json.dumps({"comments": [{"body": b} for b in comments]}),
           "FAKE_GH_FAIL": fail}
    out = _run("codex_request.py", {"tool_name": tool, "hook_event_name": "PostToolUse",
                                    "cwd": str(repo), "tool_input": {"command": command},
                                    "tool_response": _created() if response is None else response},
               cwd=repo, env=env)
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
