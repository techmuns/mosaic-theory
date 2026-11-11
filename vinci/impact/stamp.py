"""What an impact report was measured on, and when a later head may keep it (`still_valid`).

THE STAMP. Base and head shas, their merge base, the date, the inputs boundary (`inputs` in the
report: the data ref, every CIQ export's sha256, the price store's file and content digests, the
cache roots), and the PR's OWN DIFF IDENTITY — ``git patch-id --stable`` of the PR's diff over the
paths that can change behaviour (`BEHAVIOUR_EXCLUDE` names the ones that cannot).

THE RULE (2026-11-11). A report stamped for (base B, head H) stays valid for a later head H' — a
re-sync that merges main — when BOTH hold:

1. **the diff identity is unchanged**: the patch-id of ``git diff merge-base(main', H') H'`` over
   the behaviour paths equals the stamped one. ``--stable`` ignores line numbers and whitespace, so
   main's edits elsewhere in a file the PR touches shift the hunks without changing the id; a
   conflict resolution that edits the PR's own hunks, or any new commit of the PR's code, changes
   it;
2. **main touched none of the PR's files**: ``git diff --name-only B merge-base(main', H')`` lists
   none of the paths the PR's diff changes. A file both sides edited can interact even when the
   hunks merge cleanly, so it is a re-run, never a carry-over.

Anything else main brought (other modules, other pages) is main's own PRs' to measure, each under
its own report. Both checks are mechanical (`still_valid`), so the follow-up CI check can refuse a
PR body whose stamped identity does not match its head.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Paths whose change cannot move a page, a request, a rendered file or a consumer: prose and
#: bookkeeping. Every other path is in the diff identity, artifacts included (a re-committed page
#: is a change the report must see).
BEHAVIOUR_EXCLUDE = ("docs/", "planning/", "STATE.md", "CLAUDE.md", "AGENTS.md", "README.md")


class StampError(RuntimeError):
    """A ref the stamp cannot resolve, or git refusing a step: never a guessed identity."""


def git(repo: Path, *args: str, input_text: str | None = None) -> str:
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          input=input_text)
    if done.returncode != 0:
        raise StampError(f"git {' '.join(args)} exited {done.returncode}: "
                         f"{done.stderr.strip()[-800:]}")
    return done.stdout


def sha(repo: Path, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()


def merge_base(repo: Path, a: str, b: str) -> str:
    return git(repo, "merge-base", a, b).strip()


def _pathspec() -> list[str]:
    return ["--", ".", *(f":(exclude){p}" for p in BEHAVIOUR_EXCLUDE)]


def changed_paths(repo: Path, base: str, head: str, *, behaviour_only: bool = True) -> list[str]:
    """The paths the PR changes: ``merge-base(base, head)`` → ``head``."""
    mb = merge_base(repo, base, head)
    spec = _pathspec() if behaviour_only else []
    out = git(repo, "diff", "--name-only", "--no-renames", mb, head, *spec)
    return sorted(p for p in out.splitlines() if p)


def diff_identity(repo: Path, base: str, head: str) -> dict[str, Any]:
    """The PR's own diff, over the behaviour paths: its patch-id, and the paths it touches."""
    mb = merge_base(repo, base, head)
    diff = git(repo, "diff", "--no-renames", "--binary", mb, head, *_pathspec())
    pid = ""
    if diff.strip():
        pid = git(repo, "patch-id", "--stable", input_text=diff).split(" ", 1)[0].strip()
    return {"patch_id": pid or None, "merge_base": mb,
            "paths": changed_paths(repo, base, head),
            "all_paths": changed_paths(repo, base, head, behaviour_only=False),
            "excluded": list(BEHAVIOUR_EXCLUDE)}


@dataclass(frozen=True)
class Validity:
    valid: bool
    reasons: tuple[str, ...]


def still_valid(repo: Path, stamp: dict[str, Any], *, base: str, head: str) -> Validity:
    """The rule in this module's docstring, for a report's ``stamp`` and a later (base, head)."""
    now = diff_identity(repo, base, head)
    was = stamp["diff_identity"]
    reasons: list[str] = []
    if now["patch_id"] != was["patch_id"]:
        reasons.append(f"the PR's diff identity moved: patch-id {was['patch_id']} → "
                       f"{now['patch_id']} (its own code or artifacts changed)")
    moved = git(repo, "diff", "--name-only", "--no-renames", stamp["base"]["sha"],
                now["merge_base"]).splitlines()
    overlap = sorted(set(moved) & set(was["paths"]) | set(moved) & set(now["paths"]))
    if overlap:
        reasons.append(f"main changed {len(overlap)} file(s) the PR also changes since the "
                       f"stamped base {stamp['base']['sha'][:10]}: {', '.join(overlap)}")
    return Validity(not reasons, tuple(reasons))
