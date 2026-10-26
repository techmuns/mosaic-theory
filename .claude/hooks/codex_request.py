#!/usr/bin/env python3
"""PostToolUse hook on Bash: a CODE PR an agent has just opened gets ONE `@codex review` request.

WHY (2026-10-23). Codex is every PR's second reviewer (.claude/skills/pr-feedback), but its
automatic review never fired on a PR this repo's agents open: #784, #785, #786 and #788 each sat
unreviewed until someone typed `@codex review` by hand, which is the step a busy session forgets.
This posts it the moment `gh pr create` succeeds, so Codex reviews while the session works on.

WHEN. All of: the Bash command RUNS `gh pr create` (review_gate.opens_a_pr — a commit message that
mentions it opens nothing); the call succeeded (PostToolUse fires only on exit 0 — a failed create
fires PostToolUseFailure, which this is not wired to); Claude Code reports the PR it created
(`tool_response.gitOperation.pr`, else the URL gh prints); the PR is in this checkout's own GitHub
repository (`origin`), so a PR opened elsewhere from this session is never commented on; and the
PR changes CODE by the review gate's own rule (review_gate.judged_code — imported, not copied, so
the two hooks cannot drift). A docs/records/artifact PR gets no request, as it gets no in-session
review; a PR whose checkout cannot be determined is treated as code, as the gate treats it.

ONCE. A PR that already carries an `@codex review` comment gets no second one.

NEVER BLOCKS. The PR is already open; this only adds a comment. If gh fails, the agent and the
operator are told to post it by hand. Standard library only, Python 3.9+ (system `python3`).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_gate  # noqa: E402  (the sibling hook that owns the CODE rule)
from review_gate import PR_URL, created_pr  # noqa: E402  (the gate counts a PR opened by it too)

REQUEST = "@codex review"
#: A comment that already asks Codex for a review (Codex reads `@codex review <focus>` too).
REQUESTED = re.compile(r"\s*@codex\s+review\b", re.I)
#: The repository an `origin` remote names, over https or ssh.
ORIGIN = re.compile(r"github\.com[:/]([\w.-]+?)/([\w.-]+?)(?:\.git)?/?$")


def same_repo(url: str, root: Path) -> bool:
    """True when the PR at ``url`` belongs to the GitHub repository ``root``'s origin names."""
    _, origin = review_gate.git(root, "remote", "get-url", "origin")
    mine, theirs = ORIGIN.search(origin.strip()), PR_URL.fullmatch(url)
    if mine is None or theirs is None:
        return False
    return [p.lower() for p in mine.group(1, 2)] == [p.lower() for p in theirs.group(1, 2)]


def gh(*args: str) -> tuple[int, str]:
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)
    return out.returncode, out.stdout if out.returncode == 0 else (out.stderr or out.stdout)


def already_requested(url: str) -> bool:
    """True when a comment on the PR already asks Codex for a review. Unreadable → False: a
    duplicate request costs one extra review, a missed one costs the review."""
    code, out = gh("pr", "view", url, "--json", "comments")
    try:
        comments = json.loads(out).get("comments") if code == 0 else None
    except (ValueError, AttributeError):
        return False
    return any(isinstance(c, dict) and REQUESTED.match(str(c.get("body", "")))
               for c in comments or [])


def _tell(context: str, warn: bool = False) -> None:
    out: dict[str, object] = {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                     "additionalContext": context}}
    if warn:
        out["systemMessage"] = context
    print(json.dumps(out))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    command = str((payload.get("tool_input") or {}).get("command", ""))
    if payload.get("tool_name") != "Bash" or not review_gate.opens_a_pr(command):
        return 0
    url = created_pr(payload.get("tool_response"))
    start = str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    home = review_gate.repo_root(start)
    if url is None or home is None or not same_repo(url, home):
        return 0
    judged = review_gate.judged_code(command, start)
    if judged is None or not judged.files:
        return 0                            # another repo's checkout, or no code: no request
    if already_requested(url):
        return 0
    code, out = gh("pr", "comment", url, "--body", REQUEST)
    if code != 0:
        error = out.strip()
        if len(error) > 300:
            error = f"{error[:300]}… [first 300 of {len(error)} characters]"
        _tell(f"codex_request.py could NOT post `{REQUEST}` on {url} ({error}). "
              f"Post it by hand: gh pr comment {url} --body '{REQUEST}'", warn=True)
        return 0
    _tell(f"`{REQUEST}` is posted on {url} (.claude/hooks/codex_request.py): Codex is reviewing "
          "this PR. Do not post another request; triage its comments with the pr-feedback skill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
