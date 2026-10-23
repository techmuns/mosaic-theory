#!/usr/bin/env python3
"""Stop hook: the FAST half of the offline gate, on the Python files this checkout has changed.

WHY. "Suite stays green — no red commit" was enforced in two places: `bin/commit` (when an agent
remembers to use it) and CI (after the push). Between them an agent could end a turn — and report
work as done — on code that fails ruff, `mypy --strict` or its own tests. Claude Code stops when the
work LOOKS done; a Stop hook that exits 2 keeps the turn going and hands the agent the failure, so
the check closes the loop instead of the operator. (Spotify's background agents gate their PRs the
same way: a stop hook that refuses until the deterministic checks pass.)

WHAT IT RUNS, on UNCOMMITTED changes only (tracked files changed against HEAD, plus untracked
non-ignored files) under `vinci/`, `tests/` and `frontend/` — the gate's own ruff scope:
  1. ruff on the changed files;
  2. `mypy --strict vinci` when a `vinci/` file changed (the gate's exact command);
  3. pytest (`-m "not network"`) on the test files that changed or that IMPORT a changed module.
A clean tree costs one `git status` and exits 0. This is NOT the gate: the full suite still runs in
`bin/commit` and CI, and the failure message says so.

BOUNDED. A failure blocks at most MAX_BLOCKS times in a row; then the turn may end and the operator
sees a warning. (Claude Code's own 8-block cap resets whenever the agent calls a tool, so it does
not stop a failure the agent cannot fix.) Missing tooling is a WARNING, never a block.

Standard library only, Python 3.9+: the hook runs under the system `python3` and runs the checks
under the project venv — `$VENV`, else `<checkout>/.venv`, else the primary checkout's `.venv`
(the same interpreter `bin/commit` uses).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_BLOCKS = 3
SHOW_LINES = 40
MAX_TEST_FILES = 20
TIMEOUT_S = 240
SCOPE = ("vinci/", "tests/", "frontend/")
STATE_DIR = Path(tempfile.gettempdir()) / "mosaic-theory-hooks"


def git(root: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), *args],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout if out.returncode == 0 else ""


def repo_root(start: str) -> Path | None:
    top = git(Path(start), "rev-parse", "--show-toplevel").strip()
    root = Path(top) if top else None
    return root if root and (root / "vinci" / "__init__.py").exists() else None


def changed_python_files(root: Path) -> list[str]:
    tracked = git(root, "diff", "--name-only", "--diff-filter=ACMR", "HEAD").splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted({p for p in tracked + untracked
                   if p.endswith(".py") and p.startswith(SCOPE) and (root / p).exists()})


def deleted_python_files(root: Path) -> list[str]:
    """Deleted `.py` files in scope: nothing to lint, but their importers must still type-check
    and pass — deleting a module others import is a change the gate has to see."""
    gone = git(root, "diff", "--name-only", "--diff-filter=D", "HEAD").splitlines()
    return sorted({p for p in gone if p.endswith(".py") and p.startswith(SCOPE)})


def find_python(root: Path) -> str | None:
    candidates = [os.environ.get("VENV", ""), str(root / ".venv" / "bin" / "python")]
    common = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    if common:
        candidates.append(str(Path(common).parent / ".venv" / "bin" / "python"))
    return next((c for c in candidates if c and os.access(c, os.X_OK)), None)


def module_name(rel: str) -> str:
    parts = rel[: -len(".py")].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def select_tests(root: Path, changed: list[str]) -> list[str]:
    """Changed test files, plus every test file that imports a changed `vinci` module.

    ORDERED most-direct first — changed test files, then tests NAMED for a changed module
    (`test_seal*.py` for `vinci/seal.py`), then the other importers — because a widely imported
    module selects dozens of files (`vinci/dossier/schemas.py`: 72 on 2026-10-22) and only the
    first MAX_TEST_FILES run.
    """
    direct = {p for p in changed if p.startswith("tests/") and Path(p).name.startswith("test_")}
    modules = [module_name(p) for p in changed if p.startswith("vinci/")]
    leaves = {m.rpartition(".")[2] for m in modules}
    importers: set[str] = set()
    if modules:
        patterns = []
        for mod in modules:
            parent, _, leaf = mod.rpartition(".")
            patterns.append(re.compile(rf"\b{re.escape(mod)}\b"))
            if parent:
                patterns.append(re.compile(
                    rf"from {re.escape(parent)} import [^\n]*\b{re.escape(leaf)}\b"))
        for test in sorted((root / "tests").glob("test_*.py")):
            text = test.read_text(encoding="utf-8", errors="ignore")
            if any(p.search(text) for p in patterns):
                importers.add(test.relative_to(root).as_posix())
    named = {t for t in importers
             if any(Path(t).name.startswith(f"test_{leaf}") for leaf in leaves)}
    return sorted(direct) + sorted(named - direct) + sorted(importers - named - direct)


def run(py: str, root: Path, args: list[str]) -> tuple[int, list[str]]:
    env = dict(os.environ, PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE="1")
    try:
        out = subprocess.run([py, "-m", *args], cwd=root, capture_output=True, text=True,
                             timeout=TIMEOUT_S, env=env)
    except subprocess.TimeoutExpired:
        return -1, [f"timed out after {TIMEOUT_S}s"]
    return out.returncode, (out.stdout + out.stderr).splitlines()


#: pytest's progress lines ("....F..  [ 42%]") carry no failure detail and would fill the window.
PROGRESS = re.compile(r"^[.sxXfFE]+\s*\[\s*\d+%\]$")


def check(py: str, root: Path, changed: list[str],
          deleted: list[str] | None = None) -> tuple[list[str], list[str]]:
    """(failure report lines, warnings). A check that TIMES OUT is a warning, never a block:
    a slow machine is not a failing change."""
    failures: list[str] = []
    warnings: list[str] = []

    def record(name: str, code: int, lines: list[str]) -> None:
        if code == -1:
            warnings.append(f"{name}: {lines[0]}")
        elif code != 0:
            failures.append(f"── {name} ──")
            failures.extend(lines)

    if changed:
        code, lines = run(py, root, ["ruff", "check", "--output-format", "concise", *changed])
        record("ruff", code, [x for x in lines if x.strip()])
    touched = [*changed, *(deleted or [])]
    if any(p.startswith("vinci/") for p in touched):
        code, lines = run(py, root, ["mypy", "--strict", "vinci"])
        record("mypy --strict vinci", code, [x for x in lines if "error:" in x] or lines[-5:])
    tests = [t for t in select_tests(root, touched) if (root / t).exists()]
    ran = tests[:MAX_TEST_FILES]
    if ran:
        code, lines = run(py, root, ["pytest", "-m", "not network", "-p", "no:warnings",
                                     "--tb=short", "-x", *ran])
        cut = f" (ran {len(ran)} of {len(tests)} selected)" if len(tests) > len(ran) else ""
        # 5 = no tests collected (a changed test file that holds only helpers) — not a failure.
        record(f"pytest -x on {len(ran)} test file(s){cut}", 0 if code == 5 else code,
               [x for x in lines if x.strip() and not PROGRESS.match(x.strip())])
    return failures, warnings


def _state_file(session_id: str) -> Path:
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_") or "unknown"
    return STATE_DIR / f"gate-{safe}.json"


def blocks_so_far(session_id: str, continuing: bool) -> int:
    if not continuing:
        return 0
    try:
        return int(json.loads(_state_file(session_id).read_text()).get("blocks", 0))
    except (OSError, ValueError, AttributeError):
        return 0


def save_blocks(session_id: str, n: int) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _state_file(session_id).write_text(json.dumps({"blocks": n}))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    start = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    root = repo_root(start)
    if root is None:
        return 0
    changed = changed_python_files(root)
    deleted = deleted_python_files(root)
    session = str(payload.get("session_id") or "unknown")
    if not changed and not deleted:
        save_blocks(session, 0)
        return 0
    py = find_python(root)
    if py is None:
        print(json.dumps({"systemMessage": "fast gate SKIPPED: no project venv found ($VENV, "
                          "<checkout>/.venv, or the primary checkout's .venv)."}))
        return 0
    failures, warnings = check(py, root, changed, deleted)
    if not failures:
        save_blocks(session, 0)
        if warnings:
            print(json.dumps({"systemMessage": "fast gate INCOMPLETE (not blocking): "
                              + "; ".join(warnings)}))
        return 0
    n = blocks_so_far(session, bool(payload.get("stop_hook_active"))) + 1
    save_blocks(session, n)
    if n > MAX_BLOCKS:
        print(json.dumps({"systemMessage": f"fast gate STILL FAILING after {MAX_BLOCKS} attempts "
                          "on the uncommitted Python changes — the turn ends unverified; run "
                          "bin/commit before any commit."}))
        return 0
    shown = failures[:SHOW_LINES]
    files = len(changed) + len(deleted)
    print(f"FAST GATE FAILED on {files} uncommitted Python file(s) — attempt {n} of {MAX_BLOCKS}."
          f" Fix the cause, then finish. This is the fast subset; bin/commit and CI "
          f"run the full gate. Showing {len(shown)} of {len(failures)} lines:", file=sys.stderr)
    print("\n".join(shown), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
