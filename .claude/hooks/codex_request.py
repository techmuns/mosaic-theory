#!/usr/bin/env python3
"""PostToolUse hook on Bash: a CODE PR an agent opens gets ONE `@codex review` request, and ONE more
after a push that fixes what Codex found — never a third.

WHY (2026-10-23). Codex is every PR's second reviewer (.claude/skills/pr-feedback), but its
automatic review never fired on a PR this repo's agents open: #784, #785, #786 and #788 each sat
unreviewed until someone typed `@codex review` by hand, which is the step a busy session forgets.
This posts it the moment `gh pr create` succeeds, so Codex reviews while the session works on.

WHY THE SECOND (operator, 2026-10-27). A fix written to answer Codex is code Codex never saw: a
push alone does not re-trigger it, and the skill's hand-posted re-review ("only when a FIX changed
behaviour beyond the lines the comment named") was the same forgettable step. So the push that
fixes Codex's findings gets its re-review here, and its reply is the skill's round 2.

WHEN (the open). All of: the Bash command RUNS a PR create — `gh pr create`, `env -u GH_TOKEN gh
pr create`, or `gh api` POSTing to the pulls endpoint (review_gate.opens_a_pr — a commit message
that mentions one opens nothing); the call succeeded (PostToolUse fires only on exit 0 — a failed
create fires PostToolUseFailure, which this is not wired to); Claude Code reports the PR it created
(`tool_response.gitOperation.pr`, else the URL gh prints); the PR is in this checkout's own GitHub
repository (`origin`), so a PR opened elsewhere from this session is never commented on; and the
PR changes CODE by the review gate's own rule (review_gate.judged_code — imported, not copied, so
the two hooks cannot drift). A docs/records/artifact PR gets no request, as it gets no in-session
review; a PR whose checkout cannot be determined is treated as code, as the gate treats it.
ONCE: a PR that already carries an `@codex review` comment gets no second one from the open.

WHEN (the re-review). All of: the command RUNS `git push` (read by review_gate.commands, the gate's
own shell reader; a dry run pushes nothing); the pushed checkout is this repository and an OPEN PR
in `origin`'s repository has the pushed branch as its head AND the checkout's HEAD as its head
commit — the push landed (a failed push piped through `tail` still exits 0); the PR carries exactly
ONE `@codex review` request; Codex's own record on its summary comment says its review COMPLETED
and FOUND something; and the push changed CODE (the gate's rule) since the commit Codex reviewed.
A push that only adds a record, a test-free docs edit or nothing new asks nothing; Codex finding
nothing asks nothing.

TWICE AT MOST. Two requests on a PR, however they were posted, end it: round 2's findings are the
skill's to triage, never a third review.

NEVER BLOCKS. The PR is already open and the push is done; this only adds a comment. If gh fails,
the agent and the operator are told to post it by hand. Standard library only, Python 3.9+ (system
`python3`).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_gate  # noqa: E402  (the sibling hook that owns the CODE rule)
from review_gate import PR_URL, created_pr  # noqa: E402  (the gate counts a PR opened by it too)

REQUEST = "@codex review"
#: A comment that already asks Codex for a review (Codex reads `@codex review <focus>` too).
REQUESTED = re.compile(r"\s*@codex\s+review\b", re.I)
#: The repository an `origin` remote names, over https or ssh.
ORIGIN = re.compile(r"github\.com[:/]([\w.-]+?)/([\w.-]+?)(?:\.git)?/?$")
#: `@codex review` requests one PR may carry: the open's, and one re-review after a fix.
CAP = 2
#: Codex's own record on its summary comment — the commit it last reviewed, whether that review
#: completed, and whether it found anything: `<!-- codex-review-state:v1 {"code_review": …} -->`.
CODEX_STATE = re.compile(r"codex-review-state:v1\s+(\{.*?\})\s*-->", re.S)
#: `git push` options whose value is the next word, so that word is not a remote or a refspec.
_PUSH_VALUED = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
#: How often to look for the pushed commit on the PR before saying it could not be checked.
_TRIES, _WAIT = 3, 2.0


def _origin(root: Path) -> tuple[str, str] | None:
    """The (owner, repository) ``root``'s `origin` remote names."""
    _, origin = review_gate.git(root, "remote", "get-url", "origin")
    mine = ORIGIN.search(origin.strip())
    return (mine.group(1), mine.group(2)) if mine else None


def same_repo(url: str, root: Path) -> bool:
    """True when the PR at ``url`` belongs to the GitHub repository ``root``'s origin names."""
    mine, theirs = _origin(root), PR_URL.fullmatch(url)
    if mine is None or theirs is None:
        return False
    return [p.lower() for p in mine] == [p.lower() for p in theirs.group(1, 2)]


def gh(*args: str) -> tuple[int, str]:
    try:
        out = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)
    return out.returncode, out.stdout if out.returncode == 0 else (out.stderr or out.stdout)


def _comments(url: str) -> list[str] | None:
    """The bodies of the PR's conversation comments — None when gh cannot read them."""
    code, out = gh("pr", "view", url, "--json", "comments")
    try:
        comments = json.loads(out).get("comments") if code == 0 else None
    except (ValueError, AttributeError):
        return None
    if not isinstance(comments, list):
        return None
    return [str(c.get("body", "")) for c in comments if isinstance(c, dict)]


def requests(bodies: list[str]) -> int:
    """How many comments ask Codex for a review."""
    return sum(1 for body in bodies if REQUESTED.match(body))


def codex_state(bodies: list[str]) -> dict[str, object] | None:
    """Codex's record of its latest code review, from its summary comment — None when there is
    none or it cannot be read."""
    for body in reversed(bodies):
        found = CODEX_STATE.search(body)
        if found is None:
            continue
        try:
            review = json.loads(found.group(1)).get("code_review")
        except (ValueError, AttributeError):
            return None
        return review if isinstance(review, dict) else None
    return None


def already_requested(url: str) -> bool:
    """True when a comment on the PR already asks Codex for a review. Unreadable → False: a
    duplicate request costs one extra review, a missed one costs the review."""
    return bool(requests(_comments(url) or []))


def _tell(context: str, warn: bool = False) -> None:
    out: dict[str, object] = {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                     "additionalContext": context}}
    if warn:
        out["systemMessage"] = context
    print(json.dumps(out))


def _post(url: str, posted: str) -> None:
    """Post the request on ``url`` and tell the session ``posted`` — or, if gh fails, to post it
    by hand."""
    code, out = gh("pr", "comment", url, "--body", REQUEST)
    if code != 0:
        error = out.strip()
        if len(error) > 300:
            error = f"{error[:300]}… [first 300 of {len(error)} characters]"
        _tell(f"codex_request.py could NOT post `{REQUEST}` on {url} ({error}). "
              f"Post it by hand: gh pr comment {url} --body '{REQUEST}'", warn=True)
        return
    _tell(posted)


def _on_open(payload: dict[str, object], command: str) -> int:
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
    _post(url, f"`{REQUEST}` is posted on {url} (.claude/hooks/codex_request.py): Codex is "
               "reviewing this PR. Do not post another request; triage its comments with the "
               "pr-feedback skill. Switch on Auto-fix for this PR now (mcp__ccd_pr__set_monitor, "
               "auto_fix and address_comments true) so Codex's comments wake this session.")
    return 0


def pushed(command: str, cwd: str) -> tuple[str | None, list[str]] | None:
    """The directory the shell text's first `git push` runs in and the branches its refspecs name
    — None when it runs no push, or only a dry run."""
    try:
        for directory, words in review_gate.commands(command, cwd):
            if words[0] != "git":
                continue
            i = 1
            while i < len(words) and words[i].startswith("-"):
                if words[i] in ("-C", "-c") and i + 1 < len(words):
                    if words[i] == "-C":    # `git -C <dir>` runs in <dir>
                        directory = review_gate._cd(directory, words[i + 1])
                    i += 1
                i += 1
            if words[i:i + 1] != ["push"]:
                continue
            args, positional, j = words[i + 1:], [], 0
            while j < len(args):
                if args[j] in ("-n", "--dry-run"):
                    return None
                if args[j] in _PUSH_VALUED:
                    j += 1
                elif not args[j].startswith("-"):
                    positional.append(args[j])
                j += 1
            # `<remote> [<src>:]<dst> …`: each refspec's branch (`HEAD` is the checkout's own)
            names = [spec.lstrip("+").split(":")[-1].removeprefix("refs/heads/")
                     for spec in positional[1:]]
            return directory, [n for n in names if n and n != "HEAD"]
    except ValueError:                      # unbalanced quotes: the shell's reading is unknowable
        return None
    return None


def _branches(root: Path, named: list[str]) -> set[str]:
    """Every branch name the push could have landed on: the refspecs', the checkout's own and its
    upstream's (a bare `git push` pushes there)."""
    names = set(named)
    code, branch = review_gate.git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if code == 0 and branch.strip() not in ("", "HEAD"):
        names.add(branch.strip())
    code, upstream = review_gate.git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name",
                                     "@{u}")
    if code == 0 and "/" in upstream.strip():
        names.add(upstream.strip().split("/", 1)[1])
    return names


def _pull_request(repo: str, names: set[str], head: str) -> tuple[str | None, bool]:
    """The open PR whose head is one of ``names`` (its URL, or None when there is none) and
    whether its head commit is already ``head`` — looked for a few times, as GitHub may take a
    moment to move a PR's head after a push."""
    url = None
    for attempt in range(_TRIES):
        if attempt:
            time.sleep(_WAIT)
        code, out = gh("pr", "list", "-R", repo, "--state", "open", "--limit", "100",
                       "--json", "url,headRefName,headRefOid")
        try:
            prs = json.loads(out) if code == 0 else None
        except ValueError:
            prs = None
        if not isinstance(prs, list):
            return None, False
        mine = [p for p in prs if isinstance(p, dict) and p.get("headRefName") in names]
        if not mine:
            return None, False              # a branch with no open PR: nothing to re-review
        landed = [p for p in mine if p.get("headRefOid") == head]
        if landed:
            return str(landed[0].get("url", "")), True
        url = str(mine[0].get("url", ""))
    return url, False


def _changed_code(root: Path, reviewed: str, head: str) -> bool:
    """True when commits since ``reviewed`` change CODE by the gate's rule. A reviewed commit this
    checkout does not have (a force-push rewrote it) counts as changed: the cap bounds the cost."""
    code, names = review_gate.git(root, "diff", "--name-only", reviewed, head)
    return code != 0 or any(review_gate.CODE.search(p) for p in names.splitlines())


def _on_push(payload: dict[str, object], command: str) -> int:
    start = str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    push = pushed(command, start)
    if push is None or push[0] is None:
        return 0
    root = review_gate.repo_root(push[0])
    if root is None:
        return 0
    origin = _origin(root)
    code, head = review_gate.git(root, "rev-parse", "HEAD")
    head = head.strip()
    if origin is None or code != 0 or not head:
        return 0
    url, landed = _pull_request("/".join(origin), _branches(root, push[1]), head)
    bodies = _comments(url) if url is not None else None
    if url is None or bodies is None or requests(bodies) != 1:
        return 0                            # no PR, never asked (no code), or re-review spent
    state = codex_state(bodies)
    reviewed = str((state or {}).get("commit_sha") or "")
    if (state is None or state.get("status") != "completed"
            or state.get("has_any_findings") is not True or not reviewed):
        return 0
    if not landed:
        _tell(f"Codex found issues in {reviewed[:8]} on {url}, but the PR does not show "
              f"{head[:8]} as its head yet, so codex_request.py could not tell whether this push "
              f"landed. If it did and it fixed them, post the one re-review by hand: "
              f"gh pr comment {url} --body '{REQUEST}'")
        return 0
    if not _changed_code(root, reviewed, head):
        return 0
    _post(url, f"`{REQUEST}` is posted on {url} again ({CAP} of {CAP}, .claude/hooks/"
               f"codex_request.py): Codex found issues in {reviewed[:8]} and this push changed "
               "code since. Its reply is round 2 of the pr-feedback skill; no further request "
               "will be posted.")
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command = str((payload.get("tool_input") or {}).get("command", ""))
    if review_gate.opens_a_pr(command):
        return _on_open(payload, command)
    return _on_push(payload, command)


if __name__ == "__main__":
    sys.exit(main())
