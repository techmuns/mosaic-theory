#!/usr/bin/env python3
"""PreToolUse hook on Bash: no `gh pr create` for a CODE change until a code review has run.

WHY. The builder grades itself too kindly — Anthropic's harness research found a separate,
skeptical evaluator more tractable than a self-critical generator, and Claude Code's own guidance
is a fresh-context reviewer before a task counts as done. The bundled `/code-review` skill is that
reviewer (`high` effort; `--fix` applies its findings to the working tree), but it ran only when
the operator remembered to type it. This makes it the default: an agent's `gh pr create` is
refused until a `code-review` at effort high or above has run in the session since the last PR it
opened, and the refusal tells the agent exactly what to run and how to report it.

WHAT COUNTS AS REVIEWED. A `Skill` tool call for `code-review` whose args name an effort of
high, xhigh, max or ultra, found in the session transcript AFTER the last other `gh pr create`
call (so a second PR in one session needs its own review). The transcript is the evidence, not a
marker file an agent could write.

WHAT IS NOT GATED. A branch that changes no code against `origin/main` — records, STATE.md,
committed data, artifact passes — opens freely: reviewing a 266k-line artifact diff buys nothing.

Fails OPEN with a visible warning when the transcript cannot be read; the operator still reviews
and merges every PR. Standard library only, Python 3.9+ (hooks run under the system `python3`).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

#: `gh pr create` at a COMMAND position (start, or after ; & | ( or a newline, optionally behind
#: VAR=value prefixes) — never inside a quoted commit message that merely mentions it.
PR_CREATE = re.compile(r"(?:^|[;&|(\n])\s*(?:[A-Za-z_]\w*=\S*\s+)*gh\s+pr\s+create\b")
#: An operator-typed `/code-review <args>` is recorded as a user command message.
TYPED_REVIEW = re.compile(r"<command-name>/?(?:[\w-]+:)?code-review</command-name>")
TYPED_ARGS = re.compile(r"<command-args>([^<]*)</command-args>")
EFFORTS = {"high", "xhigh", "max", "ultra"}
#: What counts as CODE for the gate — anything that executes or configures execution.
CODE = re.compile(r"\.(py|js|mjs|ts|sh|toml|ya?ml)$|^bin/|^functions/|^\.claude/settings\.json$")


def git(root: Path, *args: str) -> tuple[int, str]:
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                             timeout=30)
    except (OSError, subprocess.SubprocessError):
        return 1, ""
    return out.returncode, out.stdout


def repo_root(start: str) -> Path | None:
    code, top = git(Path(start), "rev-parse", "--show-toplevel")
    root = Path(top.strip()) if code == 0 and top.strip() else None
    return root if root and (root / "vinci" / "__init__.py").exists() else None


def code_files_changed(root: Path) -> list[str]:
    """Code files this branch changes against origin/main (committed or not)."""
    base = "origin/main"
    code, merge_base = git(root, "merge-base", base, "HEAD")
    if code != 0:
        code, merge_base = git(root, "merge-base", "main", "HEAD")
    if code != 0:
        return ["(no merge base with main — treated as code)"]
    _, committed = git(root, "diff", "--name-only", merge_base.strip(), "HEAD")
    _, working = git(root, "diff", "--name-only", "HEAD")
    return sorted({p for p in (committed + working).splitlines() if CODE.search(p)})


def _skill_review(item: dict[str, object]) -> bool:
    if item.get("type") != "tool_use" or item.get("name") != "Skill":
        return False
    inp = item.get("input")
    if not isinstance(inp, dict):
        return False
    skill = str(inp.get("skill", ""))
    args = str(inp.get("args", "")).lower().split()
    return skill.split(":")[-1] == "code-review" and any(a in EFFORTS for a in args)


def _pr_create(item: dict[str, object]) -> bool:
    if item.get("type") != "tool_use" or item.get("name") != "Bash":
        return False
    inp = item.get("input")
    return isinstance(inp, dict) and bool(PR_CREATE.search(str(inp.get("command", ""))))


def reviewed_since_last_pr(transcript: str, current_id: str) -> bool | None:
    """True/False from the transcript; None when it cannot be read."""
    try:
        lines = Path(transcript).read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
    last_review = last_pr = -1
    seen: set[str] = set()
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("type") == "user" and TYPED_REVIEW.search(line):
            typed = TYPED_ARGS.search(line)
            if typed and any(a in EFFORTS for a in typed.group(1).lower().split()):
                last_review = i
            continue
        if not isinstance(entry, dict) or entry.get("type") != "assistant":
            continue
        content = (entry.get("message") or {}).get("content")
        for item in content if isinstance(content, list) else []:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id", ""))
            if item_id and item_id in seen:
                continue          # the transcript can carry the same tool call twice
            seen.add(item_id)
            if _skill_review(item):
                last_review = i
            elif _pr_create(item) and item_id != current_id:
                last_pr = i
    return last_review > last_pr


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    command = str((payload.get("tool_input") or {}).get("command", ""))
    if payload.get("tool_name") != "Bash" or not PR_CREATE.search(command):
        return 0
    root = repo_root(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if root is None:
        return 0
    code = code_files_changed(root)
    if not code:
        return 0
    verdict = reviewed_since_last_pr(str(payload.get("transcript_path", "")),
                                     str(payload.get("tool_use_id", "")))
    if verdict is None:
        print(json.dumps({"systemMessage": "review gate could not read the session transcript — "
                          "this PR opens WITHOUT a verified code review."}))
        return 0
    if verdict:
        return 0
    shown = code[:10]
    print(f"PR CREATION IS GATED ON A CODE REVIEW (.claude/hooks/review_gate.py). This branch "
          f"changes {len(code)} code file(s) against origin/main (showing {len(shown)}: "
          f"{', '.join(shown)}) and no code review at effort high or above has run since the last "
          "PR this session opened. Do this, then run gh pr create again:\n"
          "1. Run the code-review skill — Skill(skill=\"code-review\", args=\"high --fix\"), the "
          "operator's `/code-review high --fix`; if the work is already committed, add the branch "
          "as the target.\n"
          "2. Keep only fixes for CONFIRMED correctness bugs or stated-requirement gaps; revert "
          "anything speculative or style-only (CLAUDE.md: hold scope).\n"
          "3. Commit the fixes through bin/commit and push.\n"
          "4. In the PR body, add a 'Code review (high)' section listing every finding as FIXED or "
          "DISMISSED with a one-line reason.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
