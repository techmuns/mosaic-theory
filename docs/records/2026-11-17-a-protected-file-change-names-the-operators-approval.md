---
id:
status: shipped
date: 2026-11-17
prs: [1104]
supersedes:
superseded-by:
---

# A change to a decision-line file is refused by the gate until a commit message names the operator's approval of it; the guard's prompt stays, and is no longer read as the record

**WHAT.** `.github/scripts/protected_approval.py` (new) reads a branch's diff against main and lists
every file on `.claude/hooks/decision_path_guard.py`'s `PROTECTED` list that the branch changes. It
loads the guard's list by path, never a copy. It refuses the branch unless, for each such file, a
commit message on the branch carries one line of a fixed form:

    Operator-approved: <path> "<the operator's words, quoted>" <YYYY-MM-DD>

`<path>` is the file itself, or one of the guard's own directory entries that holds it
(`vinci/evals/`). No other prefix counts.

Two gates run it:
- **`gate.yml`**, on every pull request, before the install. It reads against `origin/<base_ref>`.
- **`bin/commit`**, after the tree-equals-index check and before ruff. It reads the staged change
  and the `-m`/`-F` message being committed.

How the diff is read:
- Renames are not detected, so a protected file moved away or deleted counts under its old name.
- A re-sync from main is not read as the branch's own change. That holds in CI and while
  bin/commit concludes a merge, where the base is taken against MERGE_HEAD.
- A missing base is a refusal (exit 2), never a pass.

The guard still asks. Its reason now names the line the gate will want, and its docstring says what
the prompt is and is not. Operator ruling 2026-11-17, relayed by the coordinator: "Approve as
designed (Recommended)". It covers the contract change and this PR's four protected files.

**WHY.** #1097 edited `vinci/dossier/schemas.py` through the Edit tool in auto mode. The guard
returned `ask`. The edit waited an hour, then went through.
- **Who granted it.** The first account was that auto mode answered the ask with no prompt
  reaching the operator. Wrong: asked "Did you click that 'Allow once'?", the operator answered
  "Yes, I clicked it". The "did not see it" came from a session's guess, not from the operator.
- **The docstring's sentence was not false.** It said "a hook's 'ask' also forces the prompt in
  auto mode", and Claude Code's docs say the same (permission-modes: auto mode "still shows you
  those prompts" a hook forces).
- **What was false was the reading of it.** The prompt was treated as a decision of record. It is
  a click: 10 of 47 grants came within 10 s of the ask, and a grant is kept only in a temp file and
  a local transcript, never in anything the person merging reads.
- **It never fires on a Bash edit.** The docs say an `Edit|Write` matcher fires only for those
  tools.
- **A second sentence WAS false.** "The gate in CI is the backstop": no gate looked at protected
  files until now.

So the record moves from the tool to the result. Whatever wrote the file, the branch's diff shows
it.

The approval lives in commit messages, not the PR body:
- a message cannot change after the check passes, and reaches CI on every push;
- it exists before a PR does, so bin/commit can run the same check;
- a squash merge carries it into main (checked on `7973615f` and `84081736`: each squash body lists
  every branch commit's message).

A PR body can be edited after a green run, and editing it re-runs nothing.

The hook is NOT made to deny:
- All 48 asks observed were in auto mode and 47 were granted. A deny there would have refused every
  one of those Edit-tool changes, and the next route is Bash, which no hook sees.
- `dontAsk` and headless `-p` already deny a call that would prompt (docs).
- `bypassPermissions`, where the docs do not say an ask prompts, was used by none of the 48.

**HOW VERIFIED.**

**Reproduction, $0.** Every transcript under `~/.claude/projects` was read for the guard's asks.
- 48 asks, the first on 2026-11-04, CLI 2.1.309–2.1.325. All 48 were in auto mode.
  - 47 were granted with `permissionDecision {source: user_temporary, grantScope: once}`.
  - 1 was refused by the classifier (`classifier:auto-mode`, an edit of `fast_gate.py`, 2026-11-11).
  - Raise-to-grant times: min 1.2 s, median 100 s, max 7.6 h. 6 grants came within 5 s and 10
    within 10 s.
  - #1097's grant came 60 min after its ask.
- In a scratch worktree of `7973615f`, this session in auto mode ran five Bash edits:
  - `sed -i` on `vinci/dossier/verdict.py`;
  - `python3 -c …write` on `vinci/seal.py`;
  - a heredoc onto `bin/commit`;
  - `git apply` on `.claude/hooks/decision_path_guard.py`;
  - `git checkout <older> -- vinci/dossier/schemas.py`.

  Each was accepted `source: config, reasonType: classifier`, with no guard run: 5 of 5, no prompt.
- Edit in default mode is untested: none of the 48 asks ran in it.

**Real runs of the final script.**
- **The same five Bash edits, staged**, under the system Python 3.9.6: exit 1, "REFUSED: 5 of 5",
  each named with the guard's own reason.
- **#1097's branch** (`origin/claude/financials-filed-through`): exit 1, `vinci/dossier/schemas.py`.
- **Every open PR**, 2026-11-17: #1097 is refused; #1094, #1096, #1098, #1100 and #1102 change no
  protected file and pass.
- **This branch before its commit**: exit 1 on its four protected files. With the four lines in the
  commit message it passes through bin/commit's full gate.

**Pins.** `tests/test_protected_approval.py`, 40 tests, all of which failed on main because there
was no check and no wiring. Among them:
- the three the brief named: no approval is refused, the approval passes, an unprotected change is
  untouched;
- each of the guard's 17 `PROTECTED` entries, parametrized from the real tuple;
- 8 malformed or misdirected lines that must not approve;
- a directory entry, a later empty commit carrying the line, main's lines not approving a branch;
- a re-sync committed, and one being concluded;
- moved and deleted files;
- a missing base;
- the staged change with `-m`/`-qm`/`-F`, and the git-commit argument reader;
- a parse at Python 3.9;
- the gate.yml and bin/commit wiring.

Also:
- `tests/test_one_gate.py`: bin/commit end to end in a scratch checkout. A sed-written `verdict.py`
  is refused before ruff with nothing committed, and the same change with the line commits. On main
  it committed.
- `tests/test_claude_hooks.py`: the ask names the line.

**Mutations, each run against the pins:**
- any approval approving any file;
- MERGE_HEAD ignored;
- rename detection left on;
- any prefix approving;
- the date unvalidated;
- messages read from all of history;
- a copied list missing `scenarios/`.

7 of 7 were caught.

**BOUNDARY.**
- **The census** is every transcript present under `~/.claude/projects` on 2026-11-17 that names
  the guard. An ask is a `hook_success` attachment whose stdout carries `"ask"`; its grant is the
  matching tool result's `permissionDecision`. Raise-to-grant is the difference between their
  timestamps, and includes rendering.
- **The corpus** is first-parent commits on main from 2026-10-22T00:00 to `bdb2d45d`: 322 commits,
  each diffed against its first parent and read against its own message. 94 would be refused: 211
  (commit, file) pairs over 66 distinct files, `vinci/dossier/schemas.py` in 38.
- **In the census window**, 2026-11-04 to 11-17 by commit date, 62 of 203 commits changed a
  protected file, as 163 pairs. That is not a ratio against the 48 asks: one ask covers a file for a
  whole session, and some asks were on branches never merged.
- **The open-PR run** is `gh pr list --state open` on 2026-11-17, each branch fetched and read
  against `origin/main` at `bdb2d45d`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

**The cost.** About 3 in 10 PRs need at least one line: 94 of 322 since 2026-10-22, and
`schemas.py` alone 38 times in 26 days. Each line carries the operator's own words, relayed by the
coordinator.

**Accepted, not catchable here.** A line an agent writes with words the operator never said.
Agents and the operator share one GitHub account, so no check can tell them apart. The check turns
a SILENT change into a public, permanent CLAIM that the person merging reads and can refute.

**Open PRs that predate the check.** A PR whose gate went green before this merged keeps that
green until its next push. `gate` is a required check but not `strict`. On its next push it is
checked like any other. The coordinator adds the line from the operator's recorded words (#1097 is
the one open PR this refuses).

**Falsifiers.**
- If lines start appearing whose quoted words no operator said, or the operator's words become a
  formula approved unread, the line is noise and the gate should change.
- If a protected change reaches main with no line, the check has a hole.
