#!/usr/bin/env python3
"""THE PROTECTED-FILE APPROVAL CHECK: a branch that changes a decision-line file names the
operator's approval of it in a commit message, or the gate refuses it.

    Operator-approved: <path> "<the operator's words, quoted>" <YYYY-MM-DD>

One line per protected file the branch changes against main, in a commit message on the branch
made no earlier than the branch's last change to that file. `<path>` is the file, or one of MAIN's
directory entries (`vinci/evals/`) holding it. Operator ruling 2026-11-17: "Approve as designed
(Recommended)".

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

WHICH GUARD (#1104 review round 1). The only guard CODE this runs is MAIN's: the guard file as the
merge base has it, executed for its matching rule. The BRANCH's guard is read for its lists as
LITERALS (`ast.literal_eval`), never run, so a branch cannot patch this check through the file it
loads; its lists are matched by main's rule, beside main's own. Directory approvals come from
main's list alone, so a branch cannot widen what one line approves. A base with no guard, or one
that will not load, is exit 2, never a pass.

WHAT IT DOES NOT CATCH: a line an agent writes with words the operator never said. Agents and the
operator share one GitHub account, so nothing here can tell them apart; the check turns a SILENT
change into a public, permanent CLAIM that the person merging reads and can refute. Nor a PR that
rewrites THIS script or the gate.yml step: a pull_request run uses the PR's own copy of both
(STATE row 32 item 33: a check run from main's copy is the operator's call).

Standard library only, Python 3.9+: bin/commit runs it under the system `python3`, as the hooks run.

    protected_approval.py [--root DIR] [--base REF] [--head REF] [-- <git commit arguments>]

With `--head` (CI): the change is `merge-base(base, head)..head`. Without it (bin/commit): the
change is the INDEX against the branch's merge base, and the message being committed is read from
the `git commit` arguments after `--` (-m, -F, -C, -c, --trailer; with `--amend` and a new
message, HEAD's old one no longer counts). While a merge is being concluded the base is taken
against HEAD and MERGE_HEAD together, so a re-sync from main is never read as the branch changing
what main changed. Exit 0 approved or nothing protected; 1 refused; 2 the check could not run (a
refusal too).
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable, Iterable, NamedTuple, Optional

GUARD_REL = ".claude/hooks/decision_path_guard.py"
#: The guard's literal lists, read from the BRANCH's copy without running it.
LIST_NAMES = ("PROTECTED", "PROTECTED_NAMES")

#: The one form an approval takes: a whole line, the operator's own words in double quotes, the day
#: they said them.
APPROVAL = re.compile(r'^Operator-approved: (?P<path>\S+) "(?P<words>[^"\n]*\S[^"\n]*)" '
                      r'(?P<date>\d{4}-\d{2}-\d{2})[ \t]*$', re.MULTILINE)
FORM = 'Operator-approved: <path> "<the operator\'s words>" <YYYY-MM-DD>'

#: An approval may be dated at most this many days before the branch's first commit. The operator
#: approves a card, then a session builds it: on this PR and on #1097 the approval and the first
#: commit fell on the same day. Two weeks covers a proposal card's one-week life with a week to
#: spare; an older approval was given against a main that has since moved by some 200 merges
#: (2026-11-04 → 11-17: 203 first-parent commits), and is asked again.
APPROVAL_WINDOW_DAYS = 14
#: The latest calendar date anywhere is UTC+14's: a date after it has not been said yet. UTC
#: itself would refuse a date the operator (UTC+05:30) said after local midnight.
LATEST_ZONE = dt.timezone(dt.timedelta(hours=14))


class Approval(NamedTuple):
    path: str
    words: str
    date: str
    commit: Optional[str]  # None: the message being committed


class CannotRun(Exception):
    pass


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def _git(root: Path, *args: str) -> str:
    out = _run(root, *args)
    if out.returncode != 0:
        raise CannotRun(f"git {' '.join(args)}: {out.stderr.strip() or 'failed'}")
    return out.stdout


def _exec_guard(source: str, label: str) -> ModuleType:
    module = ModuleType("decision_path_guard_at_base")  # its __name__ is not "__main__"
    try:
        exec(compile(source, label, "exec"), module.__dict__)
    except Exception as e:  # a guard that will not load is a check that cannot run: exit 2
        raise CannotRun(f"cannot load the guard at {label}: {e!r}") from e
    if not (isinstance(getattr(module, "PROTECTED", None), tuple)
            and callable(getattr(module, "protected_reason", None))):
        raise CannotRun(f"the guard at {label} has no PROTECTED tuple or protected_reason")
    return module


def base_guard_source(root: Path, base: str) -> str:
    """The guard file as the BASE commit has it. Absent is exit 2, never "nothing protected"."""
    listed = _git(root, "ls-tree", "--name-only", base, "--", GUARD_REL).strip()
    if listed != GUARD_REL:
        raise CannotRun(f"the base {base[:8]} has no {GUARD_REL}, so what main protects is unknown")
    return _git(root, "show", f"{base}:{GUARD_REL}")


def literal_lists(source: str, label: str) -> dict[str, tuple[tuple[str, str], ...]]:
    """The guard's lists as LITERALS: parsed, never executed."""
    try:
        tree = ast.parse(source, filename=label)
    except SyntaxError as e:
        raise CannotRun(f"cannot parse the guard at {label}: {e}") from e
    out: dict[str, tuple[tuple[str, str], ...]] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        elif isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        else:
            continue
        for target in targets:
            if not (isinstance(target, ast.Name) and target.id in LIST_NAMES) or value is None:
                continue
            try:
                entries = ast.literal_eval(value)
            except ValueError as e:
                raise CannotRun(f"{target.id} at {label} is not a literal: {e}") from e
            if not (isinstance(entries, tuple) and all(
                    isinstance(x, tuple) and len(x) == 2 and all(isinstance(s, str) for s in x)
                    for x in entries)):
                raise CannotRun(f"{target.id} at {label} is not a tuple of (path, reason) pairs")
            out[target.id] = entries
    if "PROTECTED" not in out:
        raise CannotRun(f"the guard at {label} states no literal PROTECTED")
    return out


def branch_lists(root: Path, head: Optional[str]) -> dict[str, tuple[tuple[str, str], ...]]:
    """The branch's lists, from ``head``'s guard or the index's. A branch that deletes the guard
    states none (main's still apply, and the deletion is itself a protected change)."""
    if head:
        present = _git(root, "ls-tree", "--name-only", head, "--", GUARD_REL).strip() == GUARD_REL
        spec = f"{head}:{GUARD_REL}"
    else:
        present = _git(root, "ls-files", "--cached", "--", GUARD_REL).strip() == GUARD_REL
        spec = f":{GUARD_REL}"
    if not present:
        return {}
    return literal_lists(_git(root, "show", spec), spec)


def guards(base_source: str, base_label: str,
           branch: dict[str, tuple[tuple[str, str], ...]]) -> tuple[ModuleType, ModuleType]:
    """Main's guard, and main's CODE holding the branch's lists: the branch's entries are matched
    by main's own rule, and none of the branch's code runs."""
    main_guard = _exec_guard(base_source, base_label)
    with_branch = _exec_guard(base_source, f"{base_label} holding the branch's lists")
    for name, entries in branch.items():
        setattr(with_branch, name, entries)
    return main_guard, with_branch


def protected_reason(rules: Iterable[ModuleType], rel: str) -> Optional[str]:
    """What ``rel`` is, by the first guard whose own rule protects it. Never re-implemented here."""
    for guard in rules:
        why: Optional[str] = guard.protected_reason(rel)
        if why is not None:
            return why
    return None


def _merging(root: Path) -> bool:
    return _run(root, "rev-parse", "-q", "--verify", "MERGE_HEAD").returncode == 0


def changed_files(root: Path, base: str, head: Optional[str]) -> list[str]:
    """Every path whose content differs between ``base`` and ``head`` (the index when None). No
    rename detection, so a protected file moved away counts under its old name too."""
    args = ["diff", "--name-only", "--no-renames", "-z"]
    args += [base, head] if head else ["--cached", base]
    return [p for p in _git(root, *args).split("\0") if p]


def range_commits(root: Path, base: str, tips: Iterable[str]) -> list[str]:
    """Every commit reachable from ``tips`` and not from ``base``, newest first."""
    tips = list(tips)
    return _git(root, "rev-list", *tips, f"^{base}").split() if tips else []


EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def _blob(root: Path, tree: str, path: str) -> Optional[str]:
    out = _run(root, "rev-parse", "-q", "--verify", f"{tree}:{path}")
    return out.stdout.strip() if out.returncode == 0 else None


def _auto_merge_tree(root: Path, ours: str, theirs: str) -> str:
    """The tree git's own merge of two commits produces (conflicted paths hold their markers)."""
    out = _run(root, "merge-tree", "--write-tree", "--no-messages", ours, theirs)
    if out.returncode not in (0, 1) or not out.stdout.strip():
        raise CannotRun(f"git merge-tree --write-tree {ours[:8]} {theirs[:8]}: {out.stderr.strip()}")
    return out.stdout.split()[0]


def _authored_by_merge(root: Path, result: str, parents: list[str], paths: set[str]) -> set[str]:
    """Of ``paths``, which differ from every parent, those a two-parent merge AUTHORED: content
    git's own merge of the parents would not produce (a conflict resolution, or an edit made in
    the merge). A clean merge of both sides' changes authored nothing."""
    if len(parents) != 2 or not paths:
        return paths
    auto = _auto_merge_tree(root, parents[0], parents[1])
    return {p for p in paths if _blob(root, result, p) != _blob(root, auto, p)}


def changed_by(root: Path, commit: str) -> set[str]:
    """The paths ``commit`` gives content of its own: found in none of its parents and, for a
    merge, not what git's merge of them produces."""
    out = _git(root, "diff-tree", "-r", "-c", "--root", "--no-commit-id", "--name-only",
               "--no-renames", "-z", commit)
    paths = {p for p in out.split("\0") if p}
    parents = _git(root, "rev-parse", f"{commit}^@").split()
    return _authored_by_merge(root, commit, parents, paths)


def staged_against(root: Path, parents: list[str]) -> set[str]:
    """The paths the commit being made gives content of its own (the index against ``parents``,
    as `changed_by` reads a commit): only its own message can approve them."""
    if not parents:
        return set(changed_files(root, EMPTY_TREE, None))
    paths = set.intersection(*[set(changed_files(root, p, None)) for p in parents])
    if len(parents) == 2 and paths:
        index_tree = _git(root, "write-tree").strip()
        return _authored_by_merge(root, index_tree, parents, paths)
    return paths


def is_ancestor(root: Path, older: str, newer: str) -> bool:
    out = _run(root, "merge-base", "--is-ancestor", older, newer)
    if out.returncode not in (0, 1):
        raise CannotRun(f"git merge-base --is-ancestor {older[:8]} {newer[:8]}: {out.stderr.strip()}")
    return out.returncode == 0


def approvals_in(text: str, commit: Optional[str]) -> list[Approval]:
    return [Approval(m.group("path"), m.group("words"), m.group("date"), commit)
            for m in APPROVAL.finditer(text)]


def _trailer(value: str) -> str:
    """A `--trailer` as git writes it into the message: `token=value` and `token:value` both
    become `token: value`, the separator being the first `:` or `=`."""
    cut = min((i for i in (value.find(":"), value.find("=")) if i >= 0), default=-1)
    token = value[:cut].strip() if cut >= 0 else ""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", token):
        return value
    return f"{token}: {value[cut + 1:].strip()}"


def commit_args(args: list[str],
                reuse: Optional[Callable[[str], str]] = None) -> list[tuple[str, str]]:
    """What a `git commit` invocation writes into its message, as (kind, text): "message" for
    -m/--message, -F/--file, a commit's message reused by -C/-c (--reuse-message,
    --reedit-message) and every --fixup form, each of which replaces HEAD's on --amend;
    "prefix" for --squash, which does not; "trailer" for each --trailer. A commit's message is
    read through ``reuse`` ("" without one). Clustered short flags included (`-qm`, `-am`,
    `-qC`). The editor and `-F -` are not read."""
    out: list[tuple[str, str]] = []

    def take(flag: str, value: str) -> None:
        if flag in ("-m", "--message"):
            out.append(("message", value))
        elif flag in ("-F", "--file"):
            out.append(("message", _read(value)))
        elif flag in ("-C", "-c", "--reuse-message", "--reedit-message"):
            out.append(("message", reuse(value) if reuse else ""))
        elif flag == "--fixup":
            # what git writes, measured on git 2.39 (#1104 round 2, Codex): `--fixup=<c>` writes
            # "fixup! <c's subject>" (an -m adds a body); `amend:<c>` and `reword:<c>` write
            # "amend! <subject>" over c's whole message. Each REPLACES HEAD's message on --amend.
            kind, _, target = value.partition(":") if value.startswith(("amend:", "reword:")) \
                else ("", "", value)
            text = reuse(target) if reuse else ""
            subject = " ".join(text.split("\n\n", 1)[0].split())
            out.append(("message", f"amend! {subject}\n\n{text}" if kind else f"fixup! {subject}"))
        elif flag == "--squash":
            # "squash! <c's subject>", and on --amend git KEEPS HEAD's message beneath it unless a
            # -m/-F gives one: a prefix, never a replacement
            text = reuse(value) if reuse else ""
            out.append(("prefix", "squash! " + " ".join(text.split("\n\n", 1)[0].split())))
        else:
            out.append(("trailer", _trailer(value)))

    long_valued = ("--message", "--file", "--reuse-message", "--reedit-message", "--trailer",
                   "--fixup", "--squash")
    i = 0
    while i < len(args):
        a, nxt = args[i], (args[i + 1] if i + 1 < len(args) else None)
        if a in long_valued or a in ("-m", "-F", "-C", "-c"):
            if nxt is not None:
                take(a, nxt)
            i += 2
            continue
        if a.startswith("--") and "=" in a and a.split("=", 1)[0] in long_valued:
            flag, value = a.split("=", 1)
            take(flag, value)
        elif a.startswith("-") and not a.startswith("--"):
            for j, ch in enumerate(a[1:], start=1):
                if ch in "mFCc":
                    attached = a[j + 1:]
                    value = attached or nxt
                    if value is not None:
                        take("-" + ch, value)
                    if not attached:
                        i += 1
                    break
        i += 1
    return out


def commit_arg_messages(args: list[str], trailers: bool = True,
                        reuse: Optional[Callable[[str], str]] = None) -> list[str]:
    """The texts `commit_args` reads, trailers included unless ``trailers`` is False."""
    return [text for kind, text in commit_args(args, reuse)
            if text and (trailers or kind == "message")]


def _read(path: str) -> str:
    if path == "-":
        return ""
    try:
        return Path(path).read_text()
    except OSError:
        return ""


def date_problem(date: str, earliest: dt.date, latest: dt.date) -> Optional[str]:
    try:
        said = dt.date.fromisoformat(date)
    except ValueError:
        return "not a real date"
    if said > latest:
        return f"dated after {latest} (the latest date anywhere now)"
    if said < earliest:
        return (f"dated before {earliest}, {APPROVAL_WINDOW_DAYS} days before the branch's first "
                "commit")
    return None


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    own, git_args = (argv[:argv.index("--")], argv[argv.index("--") + 1:]) if "--" in argv \
        else (argv, [])
    ap = argparse.ArgumentParser(description="Refuse a protected-file change no operator approved.")
    ap.add_argument("--root", default=".", help="the checkout (default: the current directory)")
    ap.add_argument("--base", default="origin/main", help="what the branch merges into")
    ap.add_argument("--head", help="the commit to check (default: the index, for bin/commit)")
    ns = ap.parse_args(own)
    root = Path(ns.root).resolve()
    pending_paths: set[str] = set()
    found: list[Approval] = []
    texts: list[str] = []
    try:
        if ns.head:
            tips = [ns.head]
        else:
            # Concluding a merge, the result is HEAD and MERGE_HEAD together: `merge-base A B C` is
            # A's base with a merge of B and C, so main's commits on either side are main's.
            tips = ["HEAD", "MERGE_HEAD"] if _merging(root) else ["HEAD"]
        base = _git(root, "merge-base", ns.base, *tips).strip()
        main_guard, with_branch = guards(base_guard_source(root, base), f"{base[:8]}:{GUARD_REL}",
                                         branch_lists(root, ns.head))
        rules = [main_guard, with_branch]
        changed = changed_files(root, base, ns.head)
        everything = range_commits(root, base, tips)
        first = (_git(root, "log", "-1", "--format=%cs", everything[-1]).strip()
                 if everything else dt.date.today().isoformat())
        committed = everything
        if not ns.head:
            amend = "--amend" in git_args
            parsed = commit_args(git_args, reuse=lambda ref: _git(root, "log", "-1", "--format=%B",
                                                                   ref))
            replaces = any(kind == "message" for kind, _ in parsed)
            parents = _git(root, "rev-parse", "HEAD^@").split() if amend else ["HEAD"]
            if _merging(root):
                parents.append("MERGE_HEAD")
            if amend:
                # HEAD is being replaced: its changes are the new commit's, and its message is
                # kept only when no -m/-F/-C/-c message is given
                head_sha = _git(root, "rev-parse", "HEAD").strip()
                committed = [c for c in everything if c != head_sha]
                if not replaces:
                    pending_text = _git(root, "log", "-1", "--format=%B", "HEAD")
                    found += approvals_in(pending_text, None)
                    texts.append(pending_text)
            pending_paths = staged_against(root, parents)
            for _, text in parsed:
                found += approvals_in(text, None)
                texts.append(text)
        for commit in committed:
            text = _git(root, "log", "-1", "--format=%B", commit)
            found += approvals_in(text, commit)
            texts.append(text)
        protected = [(p, why) for p in changed if (why := protected_reason(rules, p)) is not None]
        changers = {p: [c for c in committed if p in changed_by(root, c)] for p, _ in protected}
        earliest = dt.date.fromisoformat(first) - dt.timedelta(days=APPROVAL_WINDOW_DAYS)
        latest = dt.datetime.now(LATEST_ZONE).date()
        main_dirs = [p for p, _ in main_guard.PROTECTED if p.endswith("/")]
        missing: list[tuple[str, str, list[str]]] = []
        approved: list[tuple[str, Approval]] = []
        for p, why in protected:
            reasons: list[str] = []
            ok: Optional[Approval] = None
            for a in found:
                if not (a.path == p or (a.path in main_dirs and p.startswith(a.path))):
                    continue
                where = "the message being committed" if a.commit is None else a.commit[:8]
                problem = date_problem(a.date, earliest, latest)
                if problem is None and a.commit is not None:
                    if p in pending_paths:
                        problem = "the commit being made changes the file again"
                    else:
                        older = [c for c in changers[p] if not is_ancestor(root, c, a.commit)]
                        if older:
                            problem = f"older than {older[0][:8]}, a later change to the file"
                if problem is None:
                    ok = a
                    break
                reasons.append(f'"{a.words}" ({a.date}) in {where}: {problem}')
            if ok is None:
                missing.append((p, why, reasons))
            else:
                approved.append((p, ok))
    except CannotRun as e:
        print(f"── REFUSED: the protected-file approval check could not run against "
              f"`{ns.base}`: {e} ──", file=sys.stderr)
        return 2
    for p, a in approved:
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
    for p, why, reasons in missing:
        print(f"  {p} — {why}", file=sys.stderr)
        for reason in reasons:
            print(f"      not counted: {reason}", file=sys.stderr)
    print("  Ask the OPERATOR whether each change is intended (a session's or a prompt's answer is\n"
          "  not theirs), then put one line per file in a commit message on this branch, no older\n"
          "  than the last change to that file, quoting their words and the date they said them:\n"
          f"    {FORM}\n"
          "  (.github/scripts/protected_approval.py; the list is .claude/hooks/decision_path_guard.py's)",
          file=sys.stderr)
    unread = [ln.strip() for t in texts for ln in t.splitlines()
              if "operator-approved:" in ln.lower() and not APPROVAL.search(ln)]
    if unread:
        print(f"  {len(unread)} line(s) name an approval but are not in that form (a whole line, "
              "words quoted on it, a date):", file=sys.stderr)
        for ln in unread:
            print(f"    {ln}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
