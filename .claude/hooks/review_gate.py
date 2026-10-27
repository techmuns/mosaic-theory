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
that opened a PR (so a second PR in one session needs its own review). The transcript is the
evidence, not a marker file an agent could write.

WHICH CREATES COUNT AS A PR OPENED (2026-10-26). Every `gh pr create` did, so one that FAILED voided
the review before it: live on 2026-10-23, a create on a wrong `--repo` sent a session back to
review a second time. Now a create whose recorded outcome shows no PR — a refusal, a non-zero
exit, or a failure a pipe hid from the exit code — is skipped. The outcome is Claude Code's own
record of the call (`created_pr`, the reading codex_request.py posts on), not `is_error`: four of
the ten real failed creates read `is_error: false`, the live one among them. A create whose
outcome cannot be read still counts: the next call of the same message runs before this one's
result reaches the transcript (measured 2026-10-26), several results in one entry share no
record, and a create that printed nothing (`> out.txt`) leaves none — so an unread outcome may be
a PR just opened.

WHAT OPENS A PR (2026-10-27). `gh pr create` or its alias `gh pr new`, behind any VAR=value,
wrapper word or `env` option; or `gh api` POSTing to `repos/{owner}/{repo}/pulls`. #812 opened with
`env -u GH_TOKEN … gh pr create`, which the reading missed — so this gate never checked it and no
Codex review was asked for — and a memory note recommended the `gh api` route, which neither hook
saw at all. A GET of `…/pulls`, a merge, a review or a comment opens nothing.

WHAT IS NOT GATED. A branch that changes no code against `origin/main` — records, STATE.md,
committed data, artifact passes — opens freely: reviewing a 266k-line artifact diff buys nothing.

WHICH BRANCH IS JUDGED — THE ONE THE PR COMES FROM (2026-10-23). The gate first read the hook's
`cwd`, the SESSION's folder. A session that opens a PR from another checkout (`cd <checkout> &&
gh pr create`) was then judged on the wrong tree: live, a docs-only PR was refused for three code
files that were already-merged commits on the session's own stale branch — and a session sitting
in a clean folder could open a real code PR from elsewhere unreviewed. Now, in order:
`--head <branch>` → that branch's commits against `--base` (the PR's exact content); else the
directory the command `cd`s into before `gh pr create`; else the hook's `cwd`. A `cd` the hook
cannot resolve (`cd "$W"`) with no `--head` is UNKNOWN, and unknown is gated like code.

Fails OPEN with a visible warning when the transcript cannot be read; the operator still reviews
and merges every PR. Standard library only, Python 3.9+ (hooks run under the system `python3`).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

#: Words before a command that only set up how it runs: VAR=value, a wrapper word like `time`,
#: or `env` with its own options. Two real forms ran unseen until 2026-10-27: `env -u GH_TOKEN gh
#: pr create` (#812) and `GH_TOKEN=$(cat ~/.mosaic_gh_token) gh pr create`, a value holding a
#: space (60 creates in this project's transcripts). Each piece matches ONE way — a `$` opens a
#: `$(…)` only where one follows, an option's NAME never starts with `-` — or a long run of them
#: ending in no create backtracks exponentially (22 `$(a)` segments took 1.2 s, doubling each).
_PREFIX = (r"(?:[A-Za-z_]\w*=(?:\$\([^()]*\)|[^\s$]|\$(?!\())*|time|command|exec|nice|nohup"
           r"|env(?:\s+(?:-u\s+[^\s-]\S*|--unset\s+[^\s-]\S*|-\S*))*)")
#: `gh pr create` (or its alias `gh pr new`) at a COMMAND position (start, or after ; & | ( or a
#: newline, optionally behind _PREFIX words) — never inside a quoted commit message that merely
#: mentions it.
PR_CREATE = re.compile(rf"(?:^|[;&|(\n])\s*(?:{_PREFIX}\s+)*gh\s+pr\s+(?:create|new)\b")
#: Heredoc bodies and quoted strings are DATA, not commands: a test file written with
#: `cat <<'EOF'` that contains `cd x && gh pr create` opened no PR (found on this gate's own live
#: transcript, 2026-10-22). They are removed before the command-position match.
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?^\s*\2\s*$", re.S | re.M)
QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")
#: A backslash-newline joins two lines into one command: read as a break, it cut the `head=` field
#: off 11 of the 62 real `gh api` creates in this project's transcripts (2026-10-27).
CONTINUATION = re.compile(r"\\\n")
#: An operator-typed `/code-review <args>` is recorded as a user command message.
TYPED_REVIEW = re.compile(r"<command-name>/?(?:[\w-]+:)?code-review</command-name>")
TYPED_ARGS = re.compile(r"<command-args>([^<]*)</command-args>")
EFFORTS = {"high", "xhigh", "max", "ultra"}
#: A GitHub pull-request URL: owner, repository, number.
PR_URL = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)")
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


def _ref(root: Path, name: str) -> str | None:
    """The first of ``origin/<name>`` and ``<name>`` that names a commit in ``root``'s repo."""
    for candidate in (f"origin/{name}", name):
        code, _ = git(root, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
        if code == 0:
            return candidate
    return None


def code_files_changed(root: Path, head: str | None = None, base: str = "main") -> list[str]:
    """Code files the PR changes against ``base``.

    With ``head``: that branch's commits since its merge base with ``base`` — the PR's content.
    Without: ``root``'s checkout, committed and uncommitted.
    """
    base_ref = _ref(root, base)
    head_ref = _ref(root, head) if head else "HEAD"
    if base_ref is None or head_ref is None:
        return [f"(branch {head or 'HEAD'!r} or base {base!r} not found — treated as code)"]
    code, merge_base = git(root, "merge-base", base_ref, head_ref)
    if code != 0:
        return [f"(no merge base with {base} — treated as code)"]
    _, names = git(root, "diff", "--name-only", merge_base.strip(), head_ref)
    if not head:
        _, working = git(root, "diff", "--name-only", "HEAD")
        names += working
    return sorted({p for p in names.splitlines() if CODE.search(p)})


class Target(NamedTuple):
    """Where the PR comes from: the directory its command runs in (None = could not tell), the
    head branch if named (``--head``, or a `gh api` ``head=`` field), and the base branch."""

    directory: str | None
    head: str | None
    base: str


#: A shell token made only of these characters separates commands (``&&``, ``;``, ``|`` …).
_OPERATOR = re.compile(r"[;&|()<>]+")
#: Words that run the command after them, so the command position carries through them.
_WRAPPERS = {"time", "env", "command", "exec", "nice", "nohup"}
#: `env` options whose value is the next word (`env -u GH_TOKEN gh pr create`).
_ENV_VALUED = {"-u", "--unset"}
#: The REST endpoint a POST to which opens a pull request: /repos/{owner}/{repo}/pulls.
PULLS = re.compile(r"(?:https://api\.github\.com)?/?repos/[^/\s?]+/[^/\s?]+/pulls/?(?:\?\S*)?")
#: `gh api` options whose value is the next word, so that word is not the endpoint.
_API_VALUED = {"-X", "--method", "-f", "--raw-field", "-F", "--field", "-H", "--header",
               "--input", "-q", "--jq", "-t", "--template", "--hostname", "-p", "--preview",
               "--cache"}


def _flag(args: list[str], *names: str) -> str | None:
    for i, arg in enumerate(args):
        for name in names:
            if arg == name and i + 1 < len(args):
                return args[i + 1]
            if name.startswith("--") and arg.startswith(name + "="):
                return arg[len(name) + 1:]
    return None


def _cd(current: str | None, arg: str) -> str | None:
    """Where ``cd arg`` lands from ``current`` — None when the shell alone could resolve it."""
    if current is None or any(c in arg for c in "$`") or arg == "-":
        return None
    path = Path(os.path.expanduser(arg))
    return str(path if path.is_absolute() else Path(current) / path)


def _api_fields(args: list[str]) -> dict[str, str] | None:
    """The fields of the pull request a `gh api` call with ``args`` opens — None when it opens
    none. gh sends ``--method`` when given, else POST when a field or ``--input`` is passed, else
    GET: so a GET of `…/pulls`, a merge, a review or a comment never counts as a create."""
    endpoint: str | None = None
    method = ""
    fields: dict[str, str] = {}
    has_input = False
    i = 0
    while i < len(args):
        arg = args[i]
        name, eq, value = arg.partition("=") if arg.startswith("--") else (arg, "", "")
        if name in _API_VALUED:
            if not eq:
                value = args[i + 1] if i + 1 < len(args) else ""
                i += 1
            if name in ("-X", "--method"):
                method = value
            elif name == "--input":
                has_input = True
            elif name in ("-f", "--raw-field", "-F", "--field"):
                key, _, val = value.partition("=")
                fields[key] = val
        elif re.fullmatch(r"-X\w+", arg):
            method = arg[2:]                # `-XPOST`
        elif not arg.startswith("-") and endpoint is None:
            endpoint = arg
        i += 1
    posts = (method or ("POST" if fields or has_input else "GET")).upper() == "POST"
    return fields if posts and endpoint is not None and PULLS.fullmatch(endpoint) else None


def _created(words: list[str]) -> tuple[str | None, str] | None:
    """The ``(head, base)`` of the pull request the command ``words`` opens — None when it opens
    none: `gh pr create|new [--head H] [--base B]`, or `gh api` POSTing `head=H base=B` to the
    pulls endpoint (the route a memory note recommended until 2026-10-27, unseen by both hooks)."""
    if words[:3] in (["gh", "pr", "create"], ["gh", "pr", "new"]):
        head, base = _flag(words[3:], "--head", "-H"), _flag(words[3:], "--base", "-B")
    elif words[:2] == ["gh", "api"] and (fields := _api_fields(words[2:])) is not None:
        head, base = fields.get("head"), fields.get("base")
    else:
        return None
    if head is not None and any(c in head for c in "$`"):
        head = None                         # a computed branch name the hook cannot evaluate
    elif head is not None:
        head = head.split(":", 1)[-1]       # GitHub's cross-fork `owner:branch` form
    return head, base or "main"


def _walk(command: str, cwd: str | None) -> tuple[Target, bool]:
    """Read the shell text the way the shell will run it, up to the first PR create it contains:
    where that PR comes from, and whether a create was found at all."""
    text = CONTINUATION.sub("", HEREDOC.sub("", command)).replace("\n", " ; ")
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:                      # unbalanced quotes: the shell's reading is unknowable
        return Target(None, None, "main"), False
    directory: str | None = cwd
    at_start = True
    in_env = False                          # reading `env`'s own options
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if _OPERATOR.fullmatch(token):
            at_start = True
        elif at_start and in_env and token.startswith("-"):
            i += 1 if token in _ENV_VALUED else 0   # `-u NAME`: NAME is the option's, no command
        elif at_start and (re.fullmatch(r"[A-Za-z_]\w*=.*", token) or token in _WRAPPERS):
            pass                            # VAR=value or a wrapper word before the command
        elif at_start and token == "cd":
            nxt = tokens[i + 1] if i + 1 < len(tokens) else "~"
            directory = _cd(directory, "~" if _OPERATOR.fullmatch(nxt) else nxt)
            i += 0 if _OPERATOR.fullmatch(nxt) else 1
            at_start = False
        elif at_start and token == "gh":
            words = [token]
            for word in tokens[i + 1:]:
                if _OPERATOR.fullmatch(word):
                    break
                words.append(word)
            created = _created(words)
            if created is not None:
                return Target(directory, created[0], created[1]), True
            at_start = False
        else:
            at_start = False
        in_env = at_start and (token == "env" or (in_env and token.startswith("-")))
        i += 1
    return Target(directory, None, "main"), False


def pr_target(command: str, cwd: str) -> Target:
    """Where the PR the shell text opens comes from (``_walk``)."""
    return _walk(command, cwd)[0]


def opens_a_pr(command: str) -> bool:
    """True when the shell text RUNS a PR create — `gh pr create`, or a POST to the pulls endpoint
    through `gh api` — not when it merely contains the words."""
    if PR_CREATE.search(QUOTED.sub("''", HEREDOC.sub("", command))):
        return True
    # A POST's method, endpoint and fields sit in any order among its words, so only the word-by-
    # word reading can see one; the `pulls` test keeps that reading off every other command.
    return "pulls" in command and _walk(command, None)[1]


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
    return isinstance(inp, dict) and opens_a_pr(str(inp.get("command", "")))


def created_pr(response: object) -> str | None:
    """The URL of the PR this tool call created — Claude Code's own record first, else gh's.
    codex_request.py imports this, so the gate counts a PR opened exactly when Codex is asked."""
    if not isinstance(response, dict):
        return None
    operation = response.get("gitOperation")
    pr = operation.get("pr") if isinstance(operation, dict) else None
    if isinstance(pr, dict):
        url = str(pr.get("url", ""))
        return url if pr.get("action") == "created" and PR_URL.fullmatch(url) else None
    urls = [m.group(0) for m in PR_URL.finditer(str(response.get("stdout", "")))]
    return urls[-1] if urls else None   # gh pr create prints the new PR's URL last


def _outcomes(entry: dict[str, object]) -> dict[str, bool]:
    """Whether each tool call whose result ``entry`` carries opened a PR — for the calls whose
    outcome it shows. An errored result opened none; a result that ran is read through
    ``created_pr`` on the entry's own record, which is unattributable when it shares the entry,
    and shows nothing when the call printed nothing (`gh pr create > out.txt` opens a PR silently).
    """
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    results = [r for r in content if isinstance(r, dict) and r.get("type") == "tool_result"
               and r.get("tool_use_id")] if isinstance(content, list) else []
    record = entry.get("toolUseResult")
    shown: dict[str, bool] = {}
    for result in results:
        if result.get("is_error") is True:
            shown[str(result["tool_use_id"])] = False
        elif len(results) == 1 and isinstance(record, dict) and (
                created_pr(record) or str(record.get("stdout", "")).strip()):
            shown[str(result["tool_use_id"])] = created_pr(record) is not None
    return shown


def reviewed_since_last_pr(transcript: str, current_id: str) -> bool | None:
    """True/False from the transcript; None when it cannot be read."""
    try:
        lines = Path(transcript).read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
    last_review = -1
    creates: list[tuple[int, str]] = []         # (line, tool_use id) of every other create
    opened: dict[str, bool] = {}                # tool_use id → whether its outcome shows a PR
    seen: set[str] = set()
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("type") == "user":
            opened.update(_outcomes(entry))
            typed = TYPED_ARGS.search(line) if TYPED_REVIEW.search(line) else None
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
                creates.append((i, item_id))
    # a create whose outcome the transcript does not show counts as opened: it may be one
    last_pr = max((i for i, tool_id in creates if opened.get(tool_id, True)), default=-1)
    return last_review > last_pr


class Judged(NamedTuple):
    """The code files a PR changes, where they were read, and the base they were read against."""

    files: list[str]
    where: str
    base: str


def judged_code(command: str, start: str) -> Judged | None:
    """The CODE rule for the PR ``command`` opens when run from ``start`` — None when the PR comes
    from a checkout of another repo. codex_request.py imports this, so both hooks share one rule."""
    target = pr_target(command, start)
    # A `cd` into a directory that does not exist is UNKNOWN, not "another repo": the shell may
    # well run `gh pr create` from the folder it failed to leave.
    directory = target.directory if target.directory and Path(target.directory).is_dir() else None
    if directory is not None:
        root = repo_root(directory)
        if root is None:
            return None                     # the PR comes from a checkout of another repo
        code = code_files_changed(root, target.head, target.base)
        where = f"branch {target.head}" if target.head else f"the checkout at {root}"
    elif target.head is not None and (root := repo_root(start)) is not None:
        code = code_files_changed(root, target.head, target.base)  # branches are repo-wide
        where = f"branch {target.head}"
    else:
        code = ["(the checkout this PR comes from could not be determined — treated as code)"]
        where = "this PR"
    return Judged(code, where, target.base)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    command = str((payload.get("tool_input") or {}).get("command", ""))
    if payload.get("tool_name") != "Bash" or not opens_a_pr(command):
        return 0
    start = str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    judged = judged_code(command, start)
    if judged is None or not judged.files:
        return 0
    code, where = judged.files, judged.where
    verdict = reviewed_since_last_pr(str(payload.get("transcript_path", "")),
                                     str(payload.get("tool_use_id", "")))
    if verdict is None:
        print(json.dumps({"systemMessage": "review gate could not read the session transcript — "
                          "this PR opens WITHOUT a verified code review."}))
        return 0
    if verdict:
        return 0
    shown = code[:10]
    print(f"PR CREATION IS GATED ON A CODE REVIEW (.claude/hooks/review_gate.py). {where} "
          f"changes {len(code)} code file(s) against {judged.base} (showing {len(shown)}: "
          f"{', '.join(shown)}) and no code review at effort high or above has run since the last "
          "PR this session opened. Do this, then run gh pr create again:\n"
          "1. Run the code-review skill — Skill(skill=\"code-review\", args=\"high --fix\"), the "
          "operator's `/code-review high --fix`; if the work is already committed, add the branch "
          "as the target.\n"
          "2. Keep only fixes for CONFIRMED correctness bugs or stated-requirement gaps; revert "
          "anything speculative or style-only (CLAUDE.md: hold scope).\n"
          "3. Commit the fixes through bin/commit and push.\n"
          "4. In the PR body's '## Review dispositions' table, add every finding as a round-0 row "
          "with its outcome — FIX, DISMISS or DEFER, with the test or the reason "
          "(.claude/skills/pr-feedback).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
