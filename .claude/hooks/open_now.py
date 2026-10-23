#!/usr/bin/env python3
"""SessionStart hook: print an INDEX of STATE.md §5.0 OPEN NOW into the new session's context.

WHY. CLAUDE.md's session ritual says read §5.0 first and re-read it before proposing next steps,
because conversation memory decays and the file does not. A rule an agent must remember is weaker
than context it is handed: this prints one line per open row (number, owner, the row's bold title)
plus the line range holding the full rows. It is an index, not the rows — §5.0 runs to tens of
thousands of characters (row 32 alone is ~10k), and Claude Code moves SessionStart context over
10,000 characters into a file, so the full text would arrive as a preview anyway. Every printed line
says what it leaves out (CLAUDE.md: a truncated output prints its own truncation).

Standard library only, Python 3.9+: hooks run under the system `python3`, not the project venv.
Never fails the session: a missing STATE.md or §5.0 prints a loud line and exits 0.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

TITLE_CHARS = 150
ROW = re.compile(r"^\|\s*(\d+)\s*\|")
BOLD = re.compile(r"\*\*(.+?)\*\*")


def repo_root(start: str) -> Path | None:
    try:
        out = subprocess.run(["git", "-C", start, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None


def open_rows(state: str) -> tuple[list[tuple[str, str, str]], int, int, str]:
    """(rows as (number, owner, title), first line, last line, the §5.0 heading) — 1-based lines."""
    lines = state.splitlines()
    head = next((i for i, x in enumerate(lines) if x.startswith("### 5.0")), None)
    if head is None:
        return [], 0, 0, ""
    end = next((i for i, x in enumerate(lines[head + 1:], head + 1) if x.startswith("### ")),
               len(lines))
    rows: list[tuple[str, str, str]] = []
    first = last = 0
    for i in range(head + 1, end):
        m = ROW.match(lines[i])
        if not m:
            continue
        cells = lines[i].strip().strip("|").split(" | ")
        owner = cells[-2].strip() if len(cells) >= 4 else "?"
        body = " | ".join(cells[1:-2]) if len(cells) >= 4 else lines[i]
        bold = BOLD.search(body)
        title = (bold.group(1) if bold else body).strip()
        if len(title) > TITLE_CHARS:
            title = title[:TITLE_CHARS].rstrip() + "…"
        rows.append((m.group(1), owner, title))
        first = first or i + 1
        last = i + 1
    return rows, first, last, lines[head].lstrip("# ").strip()


def render(root: Path) -> str:
    state_path = root / "STATE.md"
    if not state_path.exists():
        return ("STATE.md NOT FOUND at the repo root — the session ritual cannot start; "
                "find it first.")
    rows, first, last, heading = open_rows(state_path.read_text(encoding="utf-8"))
    if not rows:
        return "STATE.md has no §5.0 OPEN NOW table — read STATE.md before proposing next steps."
    out = [
        f"STATE.md {heading}",
        f"{len(rows)} open rows — TITLES ONLY, each cut at {TITLE_CHARS} characters. The full "
        f"rows are STATE.md lines {first}–{last}: read a row in full before acting on it or "
        "calling it open or closed. (Printed by .claude/hooks/open_now.py at session start.)",
    ]
    out += [f"  #{n} [{owner}] {title}" for n, owner, title in rows]
    return "\n".join(out)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    start = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    root = repo_root(start)
    if root is None:
        return 0
    print(render(root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
