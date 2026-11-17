#!/usr/bin/env python3
"""THE PROTECTED-FILE APPROVAL CHECK: a branch that changes a decision-line file names the
operator's approval of it in a commit message, or the gate refuses it.

    Operator-approved: <path> "<the operator's words, quoted>" <YYYY-MM-DD>

One line per protected file the branch changes against main, anywhere in a commit message on the
branch. `<path>` is the file, or one of the guard's own directory entries (`vinci/evals/`) holding
it. Operator ruling 2026-11-17: "Approve as designed (Recommended)".

WHY (2026-11-17, #1097). `.claude/hooks/decision_path_guard.py` asks before an Edit or Write to a
file on its PROTECTED list, and the ask was being read as the operator's decision. Measured that day:
  * a grant is a click nothing durable records. 47 of the 48 asks logged 2026-11-04 → 11-17, every
    one in auto mode, were granted through the app's "Allow once" path, 10 of them within 10 s of
    being raised (#1097's by the operator, an hour after it was raised); a grant lives in a temp
    file and a local transcript, never in what the person merging reads;
  * a Bash edit never reaches the hook. sed, python, a heredoc, `git apply` and
    `git checkout <ref> -- f` each rewrote a protected file with no prompt (5 of 5).
So this reads the RESULT, not the tool: whatever wrote the file, the branch's diff shows it.

COMMIT MESSAGES, NOT THE PR BODY: a message cannot change after the check passes, reaches this
check on every push, exists before a PR does (so bin/commit runs the same check), and a squash
merge carries it into main's history. A PR body can be edited after a green run, and editing it
re-runs nothing.

WHAT IT DOES NOT CATCH: a line an agent writes with words the operator never said. Agents and the
operator share one GitHub account, so nothing here can tell them apart; the check turns a SILENT
change into a public, permanent CLAIM that the person merging reads and can refute.

THE LIST IS THE GUARD'S OWN — `PROTECTED`, loaded from the hook file by path, never a copy.
Standard library only, Python 3.9+: bin/commit runs it under the system `python3`, as the hooks run.

    protected_approval.py [--root DIR] [--base REF] [--head REF] [-- <git commit arguments>]

With `--head` (CI): the change is `merge-base(base, head)..head`. Without it (bin/commit): the
change is the INDEX against the branch's merge base, and the message being committed is read from
the `-m`/`-F` arguments after `--`. While a merge is being concluded the base is taken against
MERGE_HEAD, so a re-sync from main is never read as the branch changing what main changed.
Exit 0 approved or nothing protected; 1 refused; 2 the check could not run (a refusal too).
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable, NamedTuple, Optional

GUARD = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "decision_path_guard.py"

#: The one form an approval takes: a whole line, the operator's own words in double quotes, the day
#: they said them.
APPROVAL = re.compile(r'^Operator-approved: (?P<path>\S+) "(?P<words>[^"]*\S[^"]*)" '
                      r'(?P<date>\d{4}-\d{2}-\d{2})[ \t]*$', re.MULTILINE)
FORM = 'Operator-approved: <path> "<the operator\'s words>" <YYYY-MM-DD>'


class Approval(NamedTuple):
    path: str
    words: str
    date: str


class CannotRun(Exception):
    pass


def load_guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location("decision_path_guard", GUARD)
    if spec is None or spec.loader is None:
        raise CannotRun(f"cannot load the guard's list from {GUARD}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise CannotRun(f"git {' '.join(args)}: {out.stderr.strip() or 'failed'}")
    return out.stdout


def _merging(root: Path) -> bool:
    return subprocess.run(["git", "-C", str(root), "rev-parse", "-q", "--verify", "MERGE_HEAD"],
                          capture_output=True, text=True).returncode == 0


def changed_files(root: Path, base: str, head: Optional[str]) -> list[str]:
    """Every path whose content differs between ``base`` and ``head`` (the index when None). No
    rename detection, so a protected file moved away counts under its old name too."""
    args = ["diff", "--name-only", "--no-renames", "-z"]
    args += [base, head] if head else ["--cached", base]
    return [p for p in _git(root, *args).split("\0") if p]


def branch_messages(root: Path, base: str, head: str) -> list[str]:
    raw = _git(root, "log", "--format=%B%x00", f"{base}..{head}")
    return [m for m in raw.split("\0") if m.strip()]


def approvals(texts: Iterable[str]) -> list[Approval]:
    found = []
    for text in texts:
        for m in APPROVAL.finditer(text):
            try:
                dt.date.fromisoformat(m.group("date"))
            except ValueError:
                continue
            found.append(Approval(m.group("path"), m.group("words"), m.group("date")))
    return found


def commit_arg_messages(args: list[str]) -> list[str]:
    """The message a `git commit` invocation writes, from its -m/--message and -F/--file options,
    clustered short flags included (`-qm`, `-am`). A message given any other way (the editor, -C,
    -c, `-F -`) is not read; the check then reads only the branch's earlier commits."""
    out: list[str] = []
    i = 0
    while i < len(args):
        a, nxt = args[i], (args[i + 1] if i + 1 < len(args) else None)
        if a in ("-m", "--message", "-F", "--file"):
            if nxt is not None:
                out.append(nxt if a in ("-m", "--message") else _read(nxt))
            i += 2
            continue
        if a.startswith("--message="):
            out.append(a.split("=", 1)[1])
        elif a.startswith("--file="):
            out.append(_read(a.split("=", 1)[1]))
        elif a.startswith("-") and not a.startswith("--"):
            for j, ch in enumerate(a[1:], start=1):
                if ch in "mF":
                    attached = a[j + 1:]
                    value = attached or nxt
                    if value is not None:
                        out.append(value if ch == "m" else _read(value))
                    if not attached:
                        i += 1
                    break
        i += 1
    return out


def _read(path: str) -> str:
    if path == "-":
        return ""
    try:
        return Path(path).read_text()
    except OSError:
        return ""


def approval_for(guard: ModuleType, rel: str, found: Iterable[Approval]) -> Optional[Approval]:
    """The approval naming ``rel`` itself, or one of the guard's own directory entries holding it."""
    dirs = {p for p, _ in guard.PROTECTED if p.endswith("/") and rel.startswith(p)}
    return next((a for a in found if a.path == rel or a.path in dirs), None)


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    own, commit_args = (argv[:argv.index("--")], argv[argv.index("--") + 1:]) if "--" in argv \
        else (argv, [])
    ap = argparse.ArgumentParser(description="Refuse a protected-file change no operator approved.")
    ap.add_argument("--root", default=".", help="the checkout (default: the current directory)")
    ap.add_argument("--base", default="origin/main", help="what the branch merges into")
    ap.add_argument("--head", help="the commit to check (default: the index, for bin/commit)")
    ns = ap.parse_args(own)
    root = Path(ns.root).resolve()
    try:
        guard = load_guard()
        tip = ns.head or ("MERGE_HEAD" if _merging(root) else "HEAD")
        base = _git(root, "merge-base", ns.base, tip).strip()
        changed = changed_files(root, base, ns.head)
        texts = branch_messages(root, base, ns.head or "HEAD") + commit_arg_messages(commit_args)
    except CannotRun as e:
        print(f"── REFUSED: the protected-file approval check could not run against "
              f"`{ns.base}`: {e} ──", file=sys.stderr)
        return 2
    found = approvals(texts)
    protected = [(p, why) for p in changed if (why := guard.protected_reason(p)) is not None]
    missing = []
    for p, why in protected:
        a = approval_for(guard, p, found)
        if a is None:
            missing.append((p, why))
        else:
            print(f'  approved  {p}: "{a.words}" ({a.date})')
    where = f"against {ns.base} ({base[:8]})"
    if not protected:
        print(f"── protected-file approval: no protected file changed {where} ──")
        return 0
    if not missing:
        print(f"── protected-file approval: {len(protected)} protected file(s) changed {where}, "
              "every one approved ──")
        return 0
    print(f"── REFUSED: {len(missing)} of {len(protected)} protected file(s) this branch changes "
          f"{where} carry no operator approval ──", file=sys.stderr)
    for p, why in missing:
        print(f"  {p} — {why}", file=sys.stderr)
    print("  Ask the OPERATOR whether each change is intended (a session's or a prompt's answer is\n"
          "  not theirs), then put one line per file in a commit message on this branch, quoting\n"
          "  their words and the date they said them:\n"
          f"    {FORM}\n"
          "  (.github/scripts/protected_approval.py; the list is .claude/hooks/decision_path_guard.py's)",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
