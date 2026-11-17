"""A CHANGE TO A DECISION-LINE FILE NAMES THE OPERATOR'S APPROVAL, OR THE GATE REFUSES IT.

2026-11-17, operator: "Approve as designed (Recommended)".

WHY. `.claude/hooks/decision_path_guard.py` asks before an Edit or Write to a file on its PROTECTED
list, and on #1097 that ask was granted with the operator never seeing it: the Edit waited an hour,
then completed as an "Allow once" grant that nothing outside a temp file and a local transcript
records. Separately, a Bash edit (sed, python, a heredoc, `git apply`, `git checkout <ref> -- f`)
never reaches that hook at all: 5 of 5 rewrote a protected file with no prompt.

`.github/scripts/protected_approval.py` reads the RESULT instead of the tool: whatever wrote the
file, the branch's diff shows it, and gate.yml and bin/commit refuse the branch until a commit
message on it carries, per protected file changed, `Operator-approved: <path> "<words>" <date>`.
These pins drive that real script, against the guard's real PROTECTED list, in scratch repositories.
"""
from __future__ import annotations

import ast
import datetime as dt
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / ".github" / "scripts" / "protected_approval.py"
GUARD = ROOT / ".claude" / "hooks" / "decision_path_guard.py"
#: Dated today: an approval must fall within the window of the branch's first commit (round 1).
TODAY = dt.date.today().isoformat()
APPROVED = f'Operator-approved: vinci/dossier/verdict.py "Yes, card to fix (Recommended)" {TODAY}'
_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t"}


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str, **env: str) -> str:
    """Git in a scratch repo, auto-maintenance and auto-gc off: a commit otherwise starts a detached
    `git maintenance run --auto` that writes into `.git/` behind the test (#1103)."""
    return subprocess.run(["git", "-C", str(repo), "-c", "maintenance.auto=false",
                           "-c", "gc.auto=0", *args], capture_output=True, text=True, check=True,
                          env=dict(os.environ, **_ENV, **env)).stdout


def _repo(tmp_path: Path, *, guard: bool = True) -> Path:
    """`main` with a few real paths and the REAL guard (main's list is what the check reads),
    `origin/main` pointing at it, and branch `work` checked out."""
    repo = tmp_path / "repo"
    for rel in ("vinci/dossier/verdict.py", "vinci/dossier/schemas.py", "vinci/dossier/assemble.py",
                "vinci/evals/metrics.py", "vinci/seal.py", "bin/commit"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(f"# {rel}\n")
    if guard:
        (repo / ".claude" / "hooks").mkdir(parents=True)
        shutil.copy(GUARD, repo / ".claude" / "hooks" / "decision_path_guard.py")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-qb", "work")
    return repo


def _change(repo: Path, rel: str, message: str) -> None:
    """Write the file directly, as a Bash edit would, and commit it."""
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(path.read_text() + "# changed\n" if path.exists() else "# new\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)


def _check(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECK), "--root", str(repo), *args],
                          capture_output=True, text=True, timeout=60)


def _ci(repo: Path) -> subprocess.CompletedProcess[str]:
    return _check(repo, "--base", "origin/main", "--head", "HEAD")


# ── the three the brief names ─────────────────────────────────────────────────────────────────

def test_a_protected_change_with_no_approval_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py", "tweak the proposal mapping")
    out = _ci(repo)
    assert out.returncode == 1, out.stdout + out.stderr
    assert "REFUSED" in out.stderr and "vinci/dossier/verdict.py" in out.stderr
    # the reason is the guard's own, read from its real list
    why = _load(GUARD).protected_reason("vinci/dossier/verdict.py")
    assert why and why in out.stderr


def test_a_protected_change_with_the_operators_approval_passes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py", f"tweak the proposal mapping\n\n{APPROVED}\n")
    out = _ci(repo)
    assert out.returncode == 0, out.stderr
    assert f'vinci/dossier/verdict.py: "Yes, card to fix (Recommended)" ({TODAY})' in out.stdout


def test_an_unprotected_change_is_untouched(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/assemble.py", "an ordinary module")
    out = _ci(repo)
    assert out.returncode == 0, out.stderr
    assert "no protected file changed" in out.stdout and out.stderr == ""


# ── the list is the guard's, every entry of it ────────────────────────────────────────────────

@pytest.mark.parametrize("entry", [p for p, _ in _load(GUARD).PROTECTED])
def test_every_entry_of_the_guards_list_is_checked(tmp_path: Path, entry: str) -> None:
    """Driven from the real PROTECTED tuple, so an entry added to the guard is checked here too
    with no second list to keep in step."""
    repo = _repo(tmp_path)
    rel = entry + "probe.txt" if entry.endswith("/") else entry
    _change(repo, rel, "a change")
    out = _ci(repo)
    assert out.returncode == 1 and rel in out.stderr, (entry, out.stdout, out.stderr)


# ── what an approval is, and what it is not ───────────────────────────────────────────────────

@pytest.mark.parametrize("line", [
    f'Operator-approved: vinci/dossier/schemas.py "Yes" {TODAY}',      # another file
    f"Operator-approved: vinci/dossier/verdict.py Yes {TODAY}",        # words not quoted
    'Operator-approved: vinci/dossier/verdict.py "Yes"',               # no date
    'Operator-approved: vinci/dossier/verdict.py "Yes" 2026-13-40',    # not a date
    f'Operator-approved: vinci/dossier/verdict.py "  " {TODAY}',       # no words
    f'Operator-approved: vinci/ "Yes" {TODAY}',                        # not one of the list's
    f'  Operator-approved: vinci/dossier/verdict.py "Yes" {TODAY}',    # not a whole line
    f'operator-approved: vinci/dossier/verdict.py "Yes" {TODAY}',      # not the fixed form
])
def test_only_the_fixed_form_naming_the_file_approves_it(tmp_path: Path, line: str) -> None:
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py", f"a change\n\n{line}\n")
    assert _ci(repo).returncode == 1, line


def test_one_of_the_lists_own_directories_approves_the_files_under_it(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _change(repo, "vinci/evals/metrics.py", "the grader")
    _change(repo, "vinci/evals/judge.py", 'more grader\n\nOperator-approved: vinci/evals/ "Yes, '
            f'build the grader" {TODAY}\n')
    out = _ci(repo)
    assert out.returncode == 0, out.stderr
    assert "vinci/evals/metrics.py" in out.stdout and "vinci/evals/judge.py" in out.stdout


def test_an_approval_in_any_commit_on_the_branch_counts(tmp_path: Path) -> None:
    """The line may come in a later commit, e.g. an empty one once the operator has answered."""
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py", "a change")
    assert _ci(repo).returncode == 1
    _git(repo, "commit", "-q", "--allow-empty", "-m", f"record the approval\n\n{APPROVED}")
    assert _ci(repo).returncode == 0


def test_mains_approvals_do_not_approve_the_branch(tmp_path: Path) -> None:
    """A line in main's history approves main's change, never a branch's."""
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    _git(repo, "commit", "-q", "--allow-empty", "-m", f"an older PR\n\n{APPROVED}")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-edit", "main")
    _change(repo, "vinci/dossier/verdict.py", "a change")
    assert _ci(repo).returncode == 1


# ── how the branch's own change is read ───────────────────────────────────────────────────────

def test_a_resync_from_main_does_not_count_mains_protected_changes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/assemble.py", "the branch's own change")
    _git(repo, "checkout", "-q", "main")
    _change(repo, "vinci/seal.py", "main moves the seal")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-edit", "main")
    out = _ci(repo)
    assert out.returncode == 0, out.stderr


def test_a_resync_being_concluded_does_not_count_mains_protected_changes(tmp_path: Path) -> None:
    """bin/commit concluding a merge: the index holds main's change, MERGE_HEAD names main."""
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/assemble.py", "the branch's own change")
    _git(repo, "checkout", "-q", "main")
    _change(repo, "vinci/seal.py", "main moves the seal")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-commit", "--no-ff", "main")
    out = _check(repo, "--base", "origin/main", "--", "-m", "merge main")
    assert out.returncode == 0, out.stderr


def test_a_protected_file_moved_or_deleted_counts(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _git(repo, "mv", "vinci/seal.py", "vinci/seal_moved.py")
    _git(repo, "commit", "-qm", "move the seal")
    out = _ci(repo)
    assert out.returncode == 1 and "vinci/seal.py" in out.stderr
    _git(repo, "rm", "-q", "bin/commit")
    _git(repo, "commit", "-qm", "delete the local gate")
    out = _ci(repo)
    assert out.returncode == 1 and "bin/commit" in out.stderr


def test_a_missing_base_is_a_refusal_never_a_pass(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py", "a change")
    out = _check(repo, "--base", "origin/nowhere", "--head", "HEAD")
    assert out.returncode == 2 and "origin/nowhere" in out.stderr


# ── bin/commit's half: the staged change and the message being committed ─────────────────────

def test_a_staged_protected_change_is_refused_until_its_message_names_the_approval(
        tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "vinci/dossier/verdict.py").write_text("# rewritten by sed\n")
    _git(repo, "add", "-A")
    out = _check(repo, "--base", "origin/main", "--", "-qm", "rewrite")
    assert out.returncode == 1 and "vinci/dossier/verdict.py" in out.stderr
    approved = _check(repo, "--base", "origin/main", "--", "-qm", f"rewrite\n\n{APPROVED}")
    assert approved.returncode == 0, approved.stderr
    msg = tmp_path / "msg.txt"
    msg.write_text(f"rewrite\n\n{APPROVED}\n")
    assert _check(repo, "--base", "origin/main", "--", "-F", str(msg)).returncode == 0


def test_the_commit_message_is_read_from_every_way_git_commit_takes_one() -> None:
    check = _load(CHECK)
    read = check.commit_arg_messages
    assert read(["-m", "a", "-m", "b"]) == ["a", "b"]
    assert read(["-mA"]) == ["A"]
    assert read(["--message=A"]) == ["A"]
    assert read(["--message", "A"]) == ["A"]
    assert read(["-qm", "A"]) == ["A"]          # bin/commit's own callers write `-qm`
    assert read(["-am", "A", "--no-verify"]) == ["A"]
    assert read(["-C", "HEAD", "-m", "A"]) == ["A"]
    assert read(["--amend", "--no-edit"]) == []


def test_the_check_parses_as_python_3_9() -> None:
    """bin/commit runs it under the system `python3`, which is 3.9 on the operator's Mac."""
    ast.parse(CHECK.read_text(), filename=str(CHECK), feature_version=(3, 9))


# ── the wiring: both gates run it ─────────────────────────────────────────────────────────────

def test_gate_yml_runs_the_check_on_every_pull_request() -> None:
    text = (ROOT / ".github" / "workflows" / "gate.yml").read_text()
    lines = [ln.strip() for ln in text.splitlines()]
    # always against main, never the PR's own base, which a retarget can make another branch
    run = "run: python .github/scripts/protected_approval.py --base origin/main --head HEAD"
    assert run in lines
    step = lines.index(run)
    assert lines[step - 1] == "if: github.event_name == 'pull_request'", lines[step - 2:step]
    assert "base_ref" not in text and "BASE_REF" not in text
    # before the install, so a refusal costs seconds rather than the suite
    assert step < lines.index("- name: Install")


def test_bin_commit_runs_the_check_before_the_suite() -> None:
    text = (ROOT / "bin" / "commit").read_text()
    call = text.index(".github/scripts/protected_approval.py")
    assert call < text.index("-m ruff check")
    assert '-- "$@"' in text[call:text.index("\n", call)]


# ── review round 0 (/code-review high --fix) ──────────────────────────────────────────────────

def test_the_words_never_span_lines(tmp_path: Path) -> None:
    """An unclosed quote ran on to a later line's `"`: the approval is ONE line."""
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py",
            'a change\n\nOperator-approved: vinci/dossier/verdict.py "Yes\n'
            f'see the card" {TODAY}\n')
    assert _ci(repo).returncode == 1


def test_an_entry_on_mains_list_is_checked_though_the_branch_drops_it(tmp_path: Path) -> None:
    """The branch's own copy of the list cannot shrink what main protects: an entry the base guard
    carries is checked whatever the head's list says, even with the drop itself approved."""
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    guard = repo / ".claude" / "hooks" / "decision_path_guard.py"
    head = "PROTECTED: tuple[tuple[str, str], ...] = (\n"
    real = GUARD.read_text()
    assert real.count(head) == 1
    # main's guard is the real one, carrying one entry the branch's copy will not
    guard.write_text(real.replace(
        head, head + '    ("vinci/dossier/assemble.py", "a file main protects"),\n'))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "main protects assemble.py")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-edit", "main")
    guard.write_text(real)
    (repo / "vinci/dossier/assemble.py").write_text("# changed\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "drop the entry, then change its file\n\nOperator-approved: "
         f'.claude/hooks/decision_path_guard.py "Yes" {TODAY}')
    out = _ci(repo)
    assert out.returncode == 1, out.stdout + out.stderr
    assert "vinci/dossier/assemble.py — a file main protects" in out.stderr


def test_concluding_a_merge_of_another_branch_counts_only_the_branchs_change(
        tmp_path: Path) -> None:
    """MERGE_HEAD is a side branch cut from an older main: main's later protected change, already
    merged into the branch, is not the branch's."""
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-qb", "side", "main")
    _change(repo, "vinci/dossier/assemble.py", "the side branch's change")
    _git(repo, "checkout", "-q", "main")
    _change(repo, "vinci/seal.py", "main moves the seal")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-edit", "main")
    _git(repo, "merge", "-q", "--no-commit", "--no-ff", "side")
    out = _check(repo, "--base", "origin/main", "--", "-m", "merge side")
    assert out.returncode == 0, out.stdout + out.stderr


def test_an_amend_with_a_new_message_does_not_count_the_message_it_replaces(
        tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py", f"a change\n\n{APPROVED}\n")
    assert _check(repo, "--base", "origin/main", "--", "--amend", "--no-edit").returncode == 0
    out = _check(repo, "--base", "origin/main", "--", "--amend", "-m", "a change")
    assert out.returncode == 1, out.stdout + out.stderr


def test_a_refusal_names_a_line_that_is_not_in_the_form(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    near = f'    Operator-approved: vinci/dossier/verdict.py "Yes" {TODAY}'
    _change(repo, "vinci/dossier/verdict.py", f"a change\n\n{near}\n")
    out = _ci(repo)
    assert out.returncode == 1 and near.strip() in out.stderr, out.stderr


def test_a_guard_that_cannot_load_is_exit_2(tmp_path: Path) -> None:
    """Round 1 (item 4): main's guard failing to load is a check that cannot run, never "nothing
    protected" (guard_at's handler returning None used to survive every pin)."""
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    guard = repo / ".claude/hooks/decision_path_guard.py"
    # parses (so the branch's literal read of it succeeds) and raises when RUN: main's code fails
    guard.write_text(guard.read_text() + "raise RuntimeError('main guard breaks')\n")
    _git(repo, "commit", "-qam", "main's guard breaks")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-edit", "main")
    _change(repo, "vinci/dossier/verdict.py", "a change")
    out = _ci(repo)
    assert out.returncode == 2 and "cannot load the guard" in out.stderr, out.stdout + out.stderr


def test_a_trailer_is_read_as_part_of_the_message_being_committed(tmp_path: Path) -> None:
    """`git commit --trailer` writes its line into the message, so CI reads it there; bin/commit's
    reading of the arguments must too, or the two gates disagree."""
    repo = _repo(tmp_path)
    (repo / "vinci/dossier/verdict.py").write_text("# rewritten\n")
    _git(repo, "add", "-A")
    assert _check(repo, "--base", "origin/main", "--", "-m", "x", "--trailer",
                  APPROVED).returncode == 0
    assert _check(repo, "--base", "origin/main", "--", "-m", "x",
                  f"--trailer={APPROVED}").returncode == 0
    read = _load(CHECK).commit_arg_messages
    assert read(["-m", "x", "--trailer", "T"]) == ["x", "T"]
    assert read(["-m", "x", "--trailer", "T"], trailers=False) == ["x"]


def test_an_amend_adding_only_a_trailer_keeps_the_message_it_amends(tmp_path: Path) -> None:
    """A trailer is appended to HEAD's message, never a replacement for it."""
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py", f"a change\n\n{APPROVED}\n")
    out = _check(repo, "--base", "origin/main", "--", "--amend", "--no-edit", "--trailer", "X: y")
    assert out.returncode == 0, out.stderr


# ── review round 1 (A's independent review of d1eea93e, and Codex's P2) ──────────────────────

def _commit_all(repo: Path, message: str, **env: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message, **env)


def _repo_carrying_the_check(tmp_path: Path) -> Path:
    """A scratch repo whose main carries the check itself, for `_gate_run`."""
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    (repo / ".github" / "scripts").mkdir(parents=True)
    shutil.copy(CHECK, repo / ".github" / "scripts" / "protected_approval.py")
    _commit_all(repo, "main carries the check")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-edit", "main")
    return repo


def _gate_run(repo: Path) -> subprocess.CompletedProcess[str]:
    """The check as gate.yml runs it: from the checkout, the script inside it, no `--root`."""
    return subprocess.run([sys.executable, ".github/scripts/protected_approval.py", "--base",
                           "origin/main", "--head", "HEAD"], cwd=repo, capture_output=True,
                          text=True, timeout=60)


def test_the_branchs_guard_code_never_runs_inside_the_check(tmp_path: Path) -> None:
    """Item 1 (HIGH). The check executed the branch's guard file, so lines added to it could
    patch the check itself. Run the way gate.yml runs it. The guard change is itself approved;
    verdict.py is not, and must stay refused."""
    repo = _repo_carrying_the_check(tmp_path)
    guard = repo / ".claude" / "hooks" / "decision_path_guard.py"
    # the review's patch of the check's own `approval_for`, then a line that ends ANY check that
    # runs this file with exit 0 (a patched `sys.exit` would not do: `sys.exit(main())` looks it
    # up before main runs), so the pin holds whatever the check's code is named
    guard.write_text(guard.read_text() + (
        "import os as _os, sys as _sys\n"
        "_m = _sys.modules.get('__main__')\n"
        "if _m is not None and hasattr(_m, 'approval_for'):\n"
        "    _m.approval_for = lambda *a, **k: _m.Approval('x', 'yes', '2026-11-17')\n"
        "else:\n"
        "    _sys.stdout.flush()\n"
        "    _os._exit(0)\n"))
    (repo / "vinci/dossier/verdict.py").write_text("# rewritten\n")
    _commit_all(repo, "patch the check through the guard\n\nOperator-approved: "
                f'.claude/hooks/decision_path_guard.py "Yes" {TODAY}')
    out = _gate_run(repo)
    assert out.returncode == 1, out.stdout + out.stderr
    assert "vinci/dossier/verdict.py" in out.stderr


def test_a_directory_approval_comes_from_mains_list_only(tmp_path: Path) -> None:
    """Item 2. A branch adding `("vinci/", …)` to its own list could approve every module under
    it with one `vinci/` line. Run the way gate.yml runs it, which reads the branch's list."""
    repo = _repo_carrying_the_check(tmp_path)
    guard = repo / ".claude" / "hooks" / "decision_path_guard.py"
    head = "PROTECTED: tuple[tuple[str, str], ...] = (\n"
    guard.write_text(guard.read_text().replace(head, head + '    ("vinci/", "all of it"),\n'))
    (repo / "vinci/dossier/verdict.py").write_text("# rewritten\n")
    _commit_all(repo, "widen the list\n\n"
                f'Operator-approved: .claude/hooks/ "Yes" {TODAY}\n'
                f'Operator-approved: vinci/ "Yes" {TODAY}')
    out = _gate_run(repo)
    assert out.returncode == 1, out.stdout + out.stderr
    assert "vinci/dossier/verdict.py" in out.stderr
    assert "approved  .claude/hooks/decision_path_guard.py" in out.stdout


def test_an_approval_does_not_cover_a_later_change_to_its_file(tmp_path: Path) -> None:
    """Item 3. An approval approves the file as it stood at its commit; a later commit changing
    the file again needs its own, whether the earlier line came on this branch or on a branch
    this one was cut from (a squash leaves that line's commit outside main)."""
    repo = _repo(tmp_path)
    _change(repo, "vinci/dossier/verdict.py", f"v2 only\n\n{APPROVED}")
    assert _ci(repo).returncode == 0
    _change(repo, "vinci/dossier/verdict.py", "v3, never approved")
    out = _ci(repo)
    assert out.returncode == 1 and "older than" in out.stderr, out.stdout + out.stderr
    # an approval in a later commit covers both
    _git(repo, "commit", "-q", "--allow-empty", "-m", f"approve v3\n\n{APPROVED}")
    assert _ci(repo).returncode == 0
    # bin/commit: a staged change after the approving commit needs the line in its own message
    (repo / "vinci/dossier/verdict.py").write_text("# v4\n")
    _git(repo, "add", "-A")
    assert _check(repo, "--base", "origin/main", "--", "-m", "v4").returncode == 1
    assert _check(repo, "--base", "origin/main", "--", "-m", f"v4\n\n{APPROVED}").returncode == 0


def test_a_clean_resync_keeps_an_approval_and_an_edit_made_in_the_merge_does_not(
        tmp_path: Path) -> None:
    """A merge that only combines both sides' changes to a file (what git's own merge produces)
    authored nothing; one that edits the file beyond that authored a change of its own."""
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "main")
    lines = [f"line {i}\n" for i in range(10)]
    (repo / "vinci/dossier/schemas.py").write_text("".join(lines))
    _commit_all(repo, "a longer schemas.py")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-edit", "main")
    (repo / "vinci/dossier/schemas.py").write_text("".join(["branch's line 0\n", *lines[1:]]))
    _commit_all(repo, f'the branch\'s change\n\nOperator-approved: vinci/dossier/schemas.py "Yes" '
                f"{TODAY}")
    _git(repo, "checkout", "-q", "main")
    (repo / "vinci/dossier/schemas.py").write_text("".join([*lines[:9], "main's line 9\n"]))
    _commit_all(repo, "main's change")
    _git(repo, "update-ref", "refs/remotes/origin/main", "main")
    _git(repo, "checkout", "-q", "work")
    _git(repo, "merge", "-q", "--no-commit", "--no-ff", "main")
    assert _check(repo, "--base", "origin/main", "--", "-m", "re-sync").returncode == 0
    _git(repo, "commit", "-qm", "re-sync")
    assert _ci(repo).returncode == 0
    # the same merge, with an edit of its own to the file
    _git(repo, "reset", "-q", "--hard", "HEAD^")
    _git(repo, "merge", "-q", "--no-commit", "--no-ff", "main")
    path = repo / "vinci/dossier/schemas.py"
    path.write_text(path.read_text() + "# slipped into the merge\n")
    _git(repo, "add", "-A")
    assert _check(repo, "--base", "origin/main", "--", "-m", "re-sync").returncode == 1
    _git(repo, "commit", "-qm", "re-sync")
    out = _ci(repo)
    assert out.returncode == 1 and "older than" in out.stderr, out.stdout + out.stderr


def test_a_base_with_no_guard_is_exit_2(tmp_path: Path) -> None:
    """Item 4. A base whose guard cannot be found is not a base that protects nothing."""
    repo = _repo(tmp_path, guard=False)
    _change(repo, "vinci/dossier/verdict.py", "a change")
    out = _ci(repo)
    assert out.returncode == 2 and "has no .claude/hooks/decision_path_guard.py" in out.stderr


def test_a_branch_guard_with_no_literal_list_is_exit_2(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    guard = repo / ".claude" / "hooks" / "decision_path_guard.py"
    head = "PROTECTED: tuple[tuple[str, str], ...] = ("
    guard.write_text(guard.read_text().replace(head, "PROTECTED: tuple[tuple[str, str], ...] = "
                                               "tuple(list((") + "\n")
    _commit_all(repo, "a computed list")
    assert _ci(repo).returncode == 2


def test_a_package_shadowing_a_protected_module_is_protected(tmp_path: Path) -> None:
    """Item 5: `vinci/seal/__init__.py` is imported in place of `vinci/seal.py`."""
    repo = _repo(tmp_path)
    _change(repo, "vinci/seal/__init__.py", "a package shadows the seal")
    out = _ci(repo)
    assert out.returncode == 1 and "vinci/seal/__init__.py" in out.stderr, out.stderr


@pytest.mark.parametrize("rel", ["conftest.py", "pytest.ini", "tests/sub/conftest.py",
                                 "vinci/ruff.toml", "mypy.ini", "setup.cfg", "requirements.lock"])
def test_a_config_that_overrides_the_gates_is_protected(tmp_path: Path, rel: str) -> None:
    repo = _repo(tmp_path)
    _change(repo, rel, "a config beside pyproject.toml's")
    out = _ci(repo)
    assert out.returncode == 1 and rel in out.stderr, (rel, out.stderr)


def test_an_approval_is_dated_between_its_window_and_today(tmp_path: Path) -> None:
    """Item 6. No later than the latest date anywhere (UTC+14), no earlier than 14 days before the
    branch's first commit."""
    check = _load(CHECK)
    today = dt.date.today()
    first = (today - dt.timedelta(days=30)).isoformat()
    for offset, ok in ((3, False), (0, True), (-30 - 14, True), (-30 - 15, False)):
        repo = _repo(tmp_path / f"o{offset}")
        when = (today + dt.timedelta(days=offset)).isoformat()
        (repo / "vinci/dossier/verdict.py").write_text("# rewritten\n")
        _commit_all(repo, f'a change\n\nOperator-approved: vinci/dossier/verdict.py "Yes" {when}',
                    GIT_COMMITTER_DATE=f"{first}T12:00:00")
        out = _ci(repo)
        assert (out.returncode == 0) is ok, (offset, out.stdout + out.stderr)
    assert check.APPROVAL_WINDOW_DAYS == 14


def test_a_trailer_written_token_equals_value_is_read_as_git_writes_it(tmp_path: Path) -> None:
    """Item 7. `--trailer 'Operator-approved=…'` is written by git as `Operator-approved: …`, so
    CI passes it; bin/commit's reading of the argument must agree."""
    repo = _repo(tmp_path)
    (repo / "vinci/dossier/verdict.py").write_text("# rewritten\n")
    _git(repo, "add", "-A")
    value = f'vinci/dossier/verdict.py "Yes, card to fix (Recommended)" {TODAY}'
    trailer = f"Operator-approved={value}"
    assert _check(repo, "--base", "origin/main", "--", "-m", "x", "--trailer",
                  trailer).returncode == 0
    _git(repo, "commit", "-qm", "x", "--trailer", trailer)
    assert f"Operator-approved: {value}" in _git(repo, "log", "-1", "--format=%B")
    assert _ci(repo).returncode == 0


def test_an_amend_reusing_another_commits_message_drops_heads(tmp_path: Path) -> None:
    """Item 8 (Codex P2). `--amend -C <commit>` writes THAT commit's message in place of HEAD's,
    so HEAD's approval no longer counts and the reused message's does."""
    repo = _repo(tmp_path)
    _git(repo, "commit", "-q", "--allow-empty", "-m", "an unapproved message")
    plain = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "commit", "-q", "--allow-empty", "-m", f"an approved message\n\n{APPROVED}")
    approving = _git(repo, "rev-parse", "HEAD").strip()
    _change(repo, "vinci/dossier/verdict.py", f"a change\n\n{APPROVED}")
    for flag in ("-C", "-c", "--reuse-message", "--reedit-message"):
        out = _check(repo, "--base", "origin/main", "--", "--amend", flag, plain)
        assert out.returncode == 1, (flag, out.stdout + out.stderr)
    assert _check(repo, "--base", "origin/main", "--", "--amend", "-C", approving).returncode == 0
    reused = _load(CHECK).commit_arg_messages(["-qC", "X"], reuse=lambda ref: f"message of {ref}")
    assert reused == ["message of X"]
