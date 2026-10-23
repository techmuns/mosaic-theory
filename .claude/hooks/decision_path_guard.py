#!/usr/bin/env python3
"""PreToolUse / PostToolUse hook: ASK the operator before an agent edits a decision-path file.

WHY. CLAUDE.md draws one line that must not blur — the LLM never free-writes a verdict, the
proposal mapping is never outcome-tuned, nothing approaches execution — and says "if a change
crosses any of these, STOP and flag it". That was a sentence an agent had to remember. This makes
it a permission prompt the agent cannot skip: an Edit/Write to a file below forces Claude Code to
ask the operator (a hook's "ask" also forces the prompt in auto mode), naming what the file is.

ONCE PER FILE PER SESSION. PreToolUse asks; PostToolUse runs only if the edit went through, i.e.
the operator approved, and records the approval — so a build that edits `vinci/dossier/schemas.py`
twenty times asks once. A DENIED edit records nothing, so a retry asks again.

The list is the decision line itself plus the gates that guard it (an agent able to edit its own
guard without asking is the "optimizer edits its grader" failure). It is deliberately NOT every
decision-path module: screens and the ranker are governed by the real-run-before-merge rule, and a
prompt on every ranker edit would train the operator to click through.

Standard library only, Python 3.9+ (hooks run under the system `python3`). Fails OPEN on anything
unexpected (no git, unreadable input): a broken guard must not wedge every session; the gate in CI
is the backstop.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

#: (path or directory prefix ending in "/", what it is) — relative to the repo root.
PROTECTED: tuple[tuple[str, str], ...] = (
    ("vinci/dossier/verdict.py",
     "the machine-proposal mapping (face-validity frozen; never outcome-tuned)"),
    ("vinci/dossier/schemas.py",
     "where the Synthesis field set lives (no verdict field — test-pinned)"),
    ("vinci/seal.py", "the rationale seal"),
    ("scenarios/", "a sealed scenario record or the seal manifest"),
    ("vinci/ledger/", "the append-only decision ledger's write path"),
    ("data/snapshots/decision_ledger.jsonl", "the sealed, append-only decision ledger"),
    ("vinci/scoring/", "the forward-spread scoring harness"),
    (".claude/settings.json", "the agent hooks' wiring"),
    (".claude/hooks/", "an agent hook"),
    (".github/workflows/", "a CI workflow (the gate)"),
    ("bin/commit", "the local gate"),
)
STATE_DIR = Path(tempfile.gettempdir()) / "mosaic-theory-hooks"


def protected_reason(rel: str) -> str | None:
    for path, why in PROTECTED:
        if rel == path or (path.endswith("/") and rel.startswith(path)):
            return why
    return None


def repo_relative(file_path: str) -> str | None:
    """The path relative to its mosaic-theory checkout, or None outside one."""
    p = Path(file_path)
    probe = p.parent if not p.is_dir() else p
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    try:
        out = subprocess.run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    root = Path(out.stdout.strip()) if out.returncode == 0 else None
    if root is None or not (root / "vinci" / "__init__.py").exists():
        return None
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _state_file(session_id: str) -> Path:
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_") or "unknown"
    return STATE_DIR / f"guard-{safe}.json"


def approved(session_id: str) -> set[str]:
    try:
        return set(json.loads(_state_file(session_id).read_text()))
    except (OSError, ValueError):
        return set()


def record_approval(session_id: str, rel: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    _state_file(session_id).write_text(json.dumps(sorted(approved(session_id) | {rel})))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not file_path:
        return 0
    if not os.path.isabs(file_path):
        file_path = os.path.join(payload.get("cwd") or os.getcwd(), file_path)
    rel = repo_relative(file_path)
    why = protected_reason(rel) if rel else None
    if why is None or rel is None:
        return 0
    session = str(payload.get("session_id") or "unknown")
    if payload.get("hook_event_name") == "PostToolUse":
        record_approval(session, rel)
        return 0
    if rel in approved(session):
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            f"`{rel}` is {why}. CLAUDE.md treats a change here as crossing the decision line — "
            "confirm it is intended. Asked once per file per session "
            "(.claude/hooks/decision_path_guard.py)."),
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
