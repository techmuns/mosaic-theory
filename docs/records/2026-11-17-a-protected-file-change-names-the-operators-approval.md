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
every file protected by `.claude/hooks/decision_path_guard.py`. It refuses the branch unless, for
each such file, a commit message on the branch carries one line of a fixed form:

    Operator-approved: <path> "<the operator's words, quoted>" <YYYY-MM-DD>

`<path>` is the file itself, or one of MAIN's directory entries that holds it (`vinci/evals/`). No
other prefix counts, and a branch cannot add one.

Two gates run it:
- **`gate.yml`**, on every pull request, before the install. It always reads against
  `origin/main`, never the PR's own base.
- **`bin/commit`**, after the tree-equals-index check and before ruff. It reads the staged change
  and the message being committed: `-m`, `-F`, `-C`/`-c` (the reused commit's message) and
  `--trailer` (`token=value` read as git writes it, `token: value`). With `--amend` and a new
  message, HEAD's old message no longer counts.

**Which guard, and which list:**
- The only guard CODE the check runs is MAIN's: the guard file as the merge base has it, executed
  for its matching rule.
- The branch's guard is read for its lists as LITERALS (`ast.literal_eval`), never run, and its
  entries are matched by main's rule beside main's own.
- So a branch can neither patch the check through the file it loads, nor shrink main's list by
  dropping an entry from its own copy.
- A base with no guard, or one that will not load, exits 2. So does a branch guard with no literal
  list.

**When an approval counts:**
- It must sit in a commit no older than the branch's last change to that file: every commit that
  gives the file new content must be an ancestor of, or the same as, the approving one.
- In bin/commit, a file the commit being made changes needs the line in that commit's own message.
- A two-parent merge has changed a file only where its content differs from what git's own merge
  of the parents gives (`git merge-tree`). So a clean re-sync keeps an approval, and an edit made
  inside a merge does not.
- Its date is no later than the latest date anywhere at that moment (UTC+14), and no earlier than
  14 days before the branch's first commit.

**How the diff is read:**
- Renames are not detected, so a protected file moved away or deleted counts under its old name.
- A re-sync from main is not read as the branch's own change. That holds in CI, and while
  bin/commit concludes a merge, where the base is taken against HEAD and MERGE_HEAD together. A
  merge of a side branch cut from an older main counts only the branch's change.
- An approval is one whole line; quoted words never run over a line break.
- A refusal names, under each file, every approval it did not count and why, and any line that
  mentions `Operator-approved:` but is not in the form.

**The list, widened in round 1** (review item 5):
- `requirements.lock`, which gate.yml installs ruff, mypy and pytest from.
- `PROTECTED_NAMES`: a file of these names at ANY depth, since each is read in place of, or on top
  of, pyproject.toml's settings. They are `conftest.py`, `pytest.ini`, `.pytest.ini`,
  `pytest.toml`, `.pytest.toml`, `tox.ini`, `setup.cfg`, `ruff.toml`, `.ruff.toml`, `mypy.ini` and
  `.mypy.ini`. pytest 9.1.1, the locked version, reads the four pytest names.
- A package shadowing a protected module (`vinci/seal/__init__.py` is imported in place of
  `vinci/seal.py`). The rule covers every protected `.py`.

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
- **Every open PR**, 2026-11-17: #1097 was refused; #1094, #1096, #1098, #1100 and #1102 change
  no protected file and pass. After the coordinator added #1097's line (`433237a9`), it passes.
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

**Review round 0** (`/code-review high --fix`): 10 findings, 8 fixed. Each fix has a pin, which
brings the file to 48. 7 of the new pins failed on the pre-review commit `d81de4de`:
- the words spanning lines;
- an entry on main's list that the branch drops;
- concluding a merge of a side branch;
- an amend with a new message;
- a line not in the form, named;
- a guard that cannot load, exit 2;
- a `--trailer`.

The 8th, an amend that adds only a trailer, passes there. It catches the mutant that lets any
message, a trailer included, replace HEAD's.

**Mutations, each run against the pins:**
- any approval approving any file;
- MERGE_HEAD ignored;
- rename detection left on;
- any prefix approving;
- the date unvalidated;
- messages read from all of history;
- a copied list missing `scenarios/`;
- any message replacing HEAD's on an amend.

8 of 8 were caught.

**Review round 1** (A's independent review of `d1eea93e`, plus Codex's P2): 11 items. Items 1–9
are FIXED, each behind a pin; items 10 and 11 are recorded.
- **Fail-first, measured on `d1eea93e` as reviewed** (all three pin files run there): 19 nodes fail,
  120 pass.
  - The 19 are all 17 new round-1 nodes (11 functions, the config test across 7 names), the
    re-pinned gate.yml wiring, and the hooks file's new pin.
  - Items 1 and 2 run the way gate.yml runs them: the script inside the checkout, no `--root`.
    Under `--root` the old code loaded the script checkout's guard, so those pins passed.
- 1 pin, main's guard failing when RUN (rewritten), passes there: that behaviour was right. A's
  finding was that a mutant survived every pin; it now catches that mutant.
- 9 mutations, one per fix, are each caught by the fix's pin:
  1. the branch's guard code run;
  2. directory approvals from both lists;
  3. no ancestor check;
  4. a merge authoring whatever differs from both parents;
  5. main's guard failing to run swallowed;
  6. a base with no guard read as empty;
  7. the date unbounded;
  8. a trailer not normalised;
  9. `-C`/`-c` not read.
- **M1 at first SURVIVED.** The pin's payload patched `sys.exit`, and `sys.exit(main())` looks
  `sys.exit` up before `main` runs. The pin was hardened to a payload that exits 0 at import, so it
  holds whatever the check's functions are named.
- The file now holds 66 nodes: round 0's 48, the 17 new ones, and the protected-entry parametrize's new node for `requirements.lock`.

**BOUNDARY.**
- **The census** is every transcript present under `~/.claude/projects` on 2026-11-17 that names
  the guard. An ask is a `hook_success` attachment whose stdout carries `"ask"`; its grant is the
  matching tool result's `permissionDecision`. Raise-to-grant is the difference between their
  timestamps, and includes rendering.
- **The corpus** is first-parent commits on main from 2026-10-22T00:00 COMMITTER LOCAL TIME
  (+05:30) to `bdb2d45d`: 322 commits, each diffed against its first parent and read against its
  own message.
  - The protected list used is the HEAD's, at `d1eea93e`.
  - 94 would be refused: 211 (commit, file) pairs over 66 distinct files, `vinci/dossier/schemas.py`
    in 38.
  - From 2026-10-22T00:00 UTC the window holds 319 commits, and 94 would still be refused.
  - Under round 1's widened list: still 94 of 322 (94 of 319 at UTC). Its only new path on main,
    `requirements.lock`, changed in 2 of those commits (`6652a242`, `96d0cfea`), both already
    refused for another file. So the widening adds no refused PR in the window, and 0 tracked
    files beyond `requirements.lock` newly match it.
- **In the census window**, 2026-11-04 to 11-17 by commit date, 62 of 203 commits changed a
  protected file, as 163 pairs. That is not a ratio against the 48 asks: one ask covers a file for a
  whole session, and some asks were on branches never merged.
- **The open-PR run** is `gh pr list --state open` on 2026-11-17, each branch fetched and read
  against `origin/main` at `bdb2d45d`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

**The cost.** About 3 in 10 PRs need at least one line: 94 of 322 since 2026-10-22, and
`schemas.py` alone 38 times in 26 days. Round 1's widened list adds none in that window. Each line
carries the operator's own words, relayed by the coordinator.

A line must now also be no older than the file's last change. So a protected file edited again
after its approval needs a new line, and so does a conflict resolved inside a merge. A clean
re-sync does not.

**Accepted, not catchable here.** A line an agent writes with words the operator never said.
Agents and the operator share one GitHub account, so no check can tell them apart. The check turns
a SILENT change into a public, permanent CLAIM that the person merging reads and can refute.

**Accepted: a PR can pass itself, and a retarget re-runs nothing (STATE row 32 item 33, owner:
the operator).** A `pull_request` run executes the PR's OWN copy of `gate.yml` and of the script.
The routes that remain are:
- edit the script;
- drop or soften the gate.yml step;
- add a stdlib-named module to `.github/scripts/`, which the script's own directory puts first on
  its import path;
- open a PR onto a branch carrying an unapproved change, then retarget it to main. `pull_request`
  has no `edited` trigger and `gate` is not strict, so nothing re-runs.

Round 1 closed the guard route (item 1) and makes every run read against main (item 9). Each
remaining route is itself a protected change, in the diff the person merging reads, but CI does
not refuse it. Closing them needs the check run from MAIN's copy: a ruleset-required workflow, or
`pull_request_target`. That is the operator's call, and it is not built here.

**Accepted: an admin's direct push to main is not checked.** Branch protection takes every change
to main through a PR, but it is not enforced for admins.

**Open PRs that predate the check.** A PR whose gate went green before this merged keeps that
green until its next push. `gate` is a required check but not `strict`. On its next push it is
checked like any other. The coordinator adds the line from the operator's recorded words. #1097
was the one open PR this refused. Its review-round-1 commit `433237a9` now carries
`Operator-approved: vinci/dossier/schemas.py "Approve the edit (Recommended)" 2026-11-17`, and
it passes.

**Falsifiers.**
- If lines start appearing whose quoted words no operator said, or the operator's words become a
  formula approved unread, the line is noise and the gate should change.
- If a protected change reaches main with no line, the check has a hole.
