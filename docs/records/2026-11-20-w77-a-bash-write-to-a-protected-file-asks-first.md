---
id: W77
status: open
date: 2026-11-20
prs: []
supersedes:
superseded-by:
---

# W77: the guard that asks before a protected file changes also reads Bash calls — a tested patch for the operator to apply, and the strict xfails that hold it until then

**WHAT.**
- **The gap.** `.claude/hooks/decision_path_guard.py` asks the operator before an agent changes a
  protected file, but `.claude/settings.json` runs it only for `Edit|Write|MultiEdit|NotebookEdit`.
  A Bash call that writes the same file reaches disk with no ask. The commit gate
  (`.github/scripts/protected_approval.py`) still refuses the branch later.
- **The patch:** `docs/patches/w77-bash-writes-ask-first.diff`. Agents do not edit
  `.claude/hooks/`, so this PR changes neither the hook nor the wiring. Applied, the patch makes
  three changes:
  1. **The guard reads each Bash call BEFORE it runs** (PreToolUse). It asks, once per file per
     session, when the command visibly writes a protected file. The forms it reads:
     - a redirection;
     - `tee`, `sed -i`, `perl -i`;
     - `cp`, `mv`, `ln`, `rm`, `unlink`, and `touch` of a new file;
     - `git checkout|restore` from a ref other than HEAD or main, and `git apply`, `git mv`,
       `git rm`;
     - inline Python (`-c`, or a heredoc on stdin) that names a protected path and makes a write
       call.

     It follows the command through `cd`, `bash -c`, `eval`, `find -exec`, `xargs` and a shell
     script it runs. A grant is recorded once the call has run, in the store the Edit path uses,
     so one ask covers the file for the session whichever tool asked.
  2. **The guard compares `git status` AFTER the call** (PostToolUse, and PostToolUseFailure for
     a call that exits non-zero). A protected file whose content the call changed, and which no
     ask covered, is reported:
     - to the agent: "STOP and ask the operator";
     - to the operator, as a `systemMessage`.

     Each file is reported once per session. Content equal to HEAD's, origin/main's, or that of a
     merge, rebase or cherry-pick being applied is not reported.
  3. **The patch removes the strict xfail markers** and adds `PostToolUseFailure` to the wiring
     pin's event set. The suite is green the moment the patch is applied.
- **The tests in this PR**, in `tests/test_claude_hooks.py`:
  - **17 strict-xfail nodes (W77).** Eleven reproduce one Bash write each: `>`, `>>`, `tee`,
    `python -c`, a Python heredoc, `sed -i`, `cp`, `mv`, `cp` into the directory, `cd` then
    `sed -i`, and `bash -c`. Each command really runs in a scratch checkout and changes the file.
    That half passes today. The ask is the half that fails.
  - The other six xfails pin:
    - the wiring;
    - #1133's shape reported after the call;
    - a script that wrote and then exited 1;
    - the once-per-file-per-session grant shared with the Edit path;
    - a granted ask on a directory covering the files the call writes in it (review round 0);
    - the operator's notice stating its truncation, "showing 10 of 11" (review round 0).
  - **20 negative pins**, passing today and binding the patched guard:
    - 18 Bash calls that write no protected file, or only read one. Among them: a heredoc body
      that names writes, a quoted string naming a write, a comment, a restore from the index, and
      a repo script that reads `scenarios/` and writes elsewhere, and a glob-shaped Python string
      (`glob.glob('*')`), which Python never expands (review round 0).
    - A protected change made before the call is not blamed on it.
    - Taking main's own content (`git checkout origin/main -- f`) is neither asked about nor
      reported.

**WHY.** Twice on 2026-11-19 a session changed a protected file through the Bash tool, so the
guard's ask never reached the operator. The commit gate caught both (coordinator B on #1004,
comment 7031763467).
- **`scenarios/IT.json` (#1133).** The approval commit `555b7590` states the mechanism: the file
  was written "through the record API (read_record -> model_copy -> write_record) from a Python
  script".
  - `vinci/scenarios.py::write_record` (line 2472) builds the path itself, as
    `records_dir(root) / f"{rec.ticker.upper()}.json"`. So no word of the Bash command named the
    file.
  - The guard's matcher excludes Bash, so the guard never ran. And no reading of that command
    could have asked before it ran.
  - That is why the patch has the after-check. It turns a write found at commit time into one
    reported at the call.
- **`vinci/evals/variants.py`.** I did not find this one under these searches:
  - `git log --all -i --grep=protected` and `--grep=vinci/evals/variants.py`;
  - `git log --all -S'Operator-approved: vinci/evals'`;
  - every branch's commits since 2026-11-17 touching the path: none;
  - the bodies and file lists of every PR updated since 2026-11-19. Only #1134 names the file,
    as "found, not fixed", and no such PR changes it;
  - #1004's comments since 2026-11-19: only B's request;
  - this machine's transcripts. None holds a gate refusal naming it.

  The 11-19 sessions B coordinates committed from another machine, whose transcripts are not on
  this one. So how that write bypassed the guard is **unverified here**. Whatever wrote it, the
  after-check sees the content change.
- #1104's record had decided the guard "is NOT made to deny" and that Bash was "the next route,
  which no hook sees". This patch keeps the first: it asks and reports, and never denies. It
  answers the second.

**HOW VERIFIED.**
- **Reproduction, on this branch.** The five hook and gate suites (`test_claude_hooks`,
  `test_protected_approval`, `test_one_gate`, `test_rg_d20_instructions_match_the_code`,
  `test_no_local_paths`) give **215 passed, 17 xfailed**.
  - Run with `--runxfail`, each of the 11 write nodes fails at its ask, after its own disk
    assertion passed, e.g. "redirect: scenarios/IT.json changed on disk and nothing asked first".
  - The wiring node fails on `'decision_path_guard.py' in ['review_gate.py']`.
- **The patch, applied in a throwaway worktree of this branch** (never committed; removed after):
  - the same five suites give **232 passed**;
  - with the hook and wiring patched but the test file left as this PR has it,
    `test_claude_hooks.py` gives **18 failures**: the 17 W77 nodes as XPASS(strict), and the
    wiring pin's event set, which lacks `PostToolUseFailure`. So the markers cannot outlive the
    fix unnoticed.
- **#1133 replayed on real data**, in that worktree, through the patched guard, under the system
  `/usr/bin/python3` 3.9.6. The real `vinci.scenarios` API rewrote the real `scenarios/IT.json`
  (`read_record('IT')` → `model_copy(update={'analyst': …})` → `write_record`).
  - PreToolUse said nothing: the command names no path.
  - `git status` showed `M scenarios/IT.json`.
  - PostToolUse answered `decision: block`, naming `` `scenarios/IT.json` — a sealed scenario
    record or the seal manifest ``, with the operator's `systemMessage`.
  - A byte-identical round trip, the first attempt, changed nothing and reported nothing.
  - The file was restored after.
- **The patched guard itself:** `ruff` (the repo's config) is clean but for line 7's E501, which
  is in today's file too. `mypy --strict --warn-unused-ignores` is clean. It parses at
  `feature_version=(3, 9)` (the existing pin).
  - Its first draft had a bug the census found: `git apply`'s `diff --git` paths were stripped of a
    component twice. It is fixed and checked on a real heredoc diff.
  - The draft also misread `open('scenarios/'+…` as a write mode in its regex fallback. Fixed.
- **False-positive census.** The final reading was run over every Bash call in this machine's
  mosaic-theory transcripts:
  - **34,778 calls → 100 would ask (0.29%)**, 0 raised.
  - After once-per-file-per-session, a granted directory covering its files: **38 prompts, in 16
    of 69 sessions** (most in one session 12, median 1).
  - Each of the 100, by hand and by matching the named path's variable to a write call:
    - **96 wrote or moved a protected file.** 84 were Python heredocs or `-c`, mostly
      read-modify-write of `vinci/evals/*.py`, `schemas.py`, `verdict.py` and `vinci/ledger/*.py`.
      The rest: 5 `sed -i`, 4 `git checkout <sha> -- vinci/`, 2 `git mv` of scenario records,
      1 `git show … >` into `vinci/evals/`.
    - **2 deleted files under a protected directory.** One was iCloud `" 2.py"` duplicates,
      untracked.
    - **1 over-asked**: a PR-body table naming `schemas.py` while the script wrote a scratch file.
    - **1 is an artifact of the census's offline path reader**, not of the hook: a log file
      directly under `.claude/worktrees/` was read as a checkout root.
  - **The first draft asked 128.** Of its 28 extra calls:
    - 27 ran a Python script FILE, which names `scenarios/` and writes elsewhere:
      `frontend/build.py` in 25 (one of them also ran `.github/scripts/protected_approval.py`) and
      `scripts/build_companyfacts_fixture.py` in 2. Script files are no longer read; the
      after-check covers them.
    - 1 was the regex fallback misreading `open('scenarios/'+…` as a write mode (the second bug
      above).
  - **Four forms had 0 uses in the 34,778 calls**: `install`, `truncate`, `dd` and `patch`. They
    were cut from the reader. 7 calls had unbalanced quotes; the reader names nothing for them,
    and the after-check still runs.
- **Latency**, median of 10 Bash payloads per checkout, system Python:
  - before the call: 122 ms in the primary checkout, 149 ms in this worktree;
  - after the call: 112 ms and 117 ms;
  - today's guard on the same payload, which it ignores: 44–48 ms.

**REVIEW ROUND 0** (`/code-review high --fix`, on the patch's guard and this PR's tests): 6 findings,
3 FIXED, each behind a pin that fails on the round-0 guard and passes on the fixed one (3 failed →
3 passed, run in the throwaway worktree):
1. FIX — Python string literals were shell-globbed: a writing script holding `'*'` asked about
   every top-level protected entry. Pin: the glob-shaped negative pin.
2. FIX — a granted ask on a directory entry (`scenarios/`) did not cover the files the call wrote
   in it, so the after-check reported the writes just approved. Pin: the directory-grant xfail.
3. FIX — the operator's notice cut its list at 10 with " …" (CLAUDE.md: a truncated output prints
   its own truncation). Pin: the "showing 10 of 11" xfail.
4. DEFER — a second shell reader beside `review_gate.py`'s `commands()`. That reader treats `>` as
   a command separator, so it cannot name a redirect target. Sharing one reader means editing
   `review_gate.py`, also a hook: a follow-up for the operator's apply, not this patch.
5. DEFER — `rm` of an untracked file under a protected directory asks (1 call in the census). The
   gate never counts it; telling needs `git ls-files` per removal. Accepted below.
6. DISMISS as already accepted — inline Python that names a protected path and writes another file
   asks (1 of 100 in the census). Accepted below.

The census was re-run on the fixed guard: the same 100 calls ask.

**BOUNDARY.**
- **The census.** Population: every assistant `tool_use` named `Bash` in
  `~/.claude/projects/*mosaic-theory*/**/*.jsonl` on this machine, read 2026-11-20, this session's
  own transcript excluded, de-duplicated by tool-use id. That is 371 transcript files, 69
  sessions, both checkout paths. Window: the timestamps present, 2026-11-09T06:28Z →
  2026-11-20T06:07Z (the read asked for 11-06 onward; nothing earlier remains).
  - Each command was read from its recorded `cwd` against the filesystem as it is today. A
    deleted worktree's globs, directories and files are not there, so a `cp` into a directory or
    a glob there is read lexically.
  - "Prompts" assume every ask was granted, which records it for the session.
- **"96 wrote"** means the command's text writes the named protected path. Whether each write was
  approved, committed or reverted later is not read.
- **The suites' counts**: the five test files named above, `-o addopts=""`, on this branch at
  base `6c22b222` with the tests added, and on the patched throwaway worktree.
- **Latency**: wall time of `subprocess.run` of the hook with a `ls scenarios | head -3` payload,
  2026-11-20, median of 10. It includes interpreter start-up.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **About 0.25 s on every Bash call**: the two readings, the after-check's `git status` and
  interpreter start-up. Each runs beside the hook already on that event (`review_gate.py` before,
  `codex_request.py` after), and hooks on one event run in parallel.
- **The before-reading is a reading, not a shell.** It misses:
  - a path built at run time: `$VAR`, `$(…)`, a Python path joined from pieces;
  - `xargs` input;
  - a repo script's own writes.

  The after-check catches each of those once the call has run. That is a report, not an ask: the
  write has happened, and the agent is told to stop and ask.
- **The after-check cannot see:**
  - a commit made inside the call (bin/commit's gate reads it);
  - a write to a checkout the call never names. It reads the call's `cwd`, each `cd` it can
    resolve, each named target's checkout and `CLAUDE_PROJECT_DIR`.
- **Over-ask class:** inline Python that names a protected path and writes ANOTHER file. That was
  1 of 100 in the census.
- **Fails open**, as the guard always has. A crash in the Bash path returns nothing, and the gate
  is still the record.
- **A denied ask leaves a per-call reading** in the temp folder, since no PostToolUse follows it.
  The next call of that session removes any older than a day.
- **Falsifiers:**
  - the operator clicks through these prompts within seconds, as 10 of #1104's 47 Edit grants
    were;
  - a protected change reaches the gate after a Bash call with no report;
  - the prompts per session climb past the census's 12. Then the reading is wrong for this
    project's habits.
- **For the operator, to apply** (STATE row 32, item (37)). From an up-to-date checkout of main
  that holds this PR:

  ```bash
  git apply --check docs/patches/w77-bash-writes-ask-first.diff
  ```
  ```bash
  git apply docs/patches/w77-bash-writes-ask-first.diff && git rm -q docs/patches/w77-bash-writes-ask-first.diff
  ```
  ```bash
  git add -A && bin/commit -m "W77 applied: the decision-line guard reads Bash calls" -m 'Operator-approved: .claude/hooks/decision_path_guard.py "<your words>" <YYYY-MM-DD>' -m 'Operator-approved: .claude/settings.json "<your words>" <YYYY-MM-DD>'
  ```

  The apply commit lands by PR like any other. A session started before the change may keep the
  old wiring, because Claude Code reads hook settings at startup.
