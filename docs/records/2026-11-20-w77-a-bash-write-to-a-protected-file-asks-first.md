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
     checkout per session, when the command visibly writes a protected file, and names the
     checkout. The forms it reads:
     - a redirection;
     - `tee`, `sed -i`, `perl -i`;
     - `cp`, `mv`, `ln`, `rm`, `unlink`, and `touch` of a new file;
     - `git checkout|restore` from a ref other than HEAD or main, and `git apply`, `git mv`,
       `git rm`;
     - inline Python (`-c`, or a heredoc on stdin) that names a protected path and makes a write
       call.

     It follows the command through `cd`, `bash -c`, `eval`, `find -exec`, `xargs` and a shell
     script it runs. When the call has run, a grant is recorded for each protected file it
     changed, keyed by checkout AND path, in the store the Edit path uses. So one ask covers that
     file in that checkout for the session, whichever tool asked. The Edit path's keys move from
     the path alone to checkout and path too (review round 2, SF1).
  2. **The guard compares `git status` AFTER the call** (PostToolUse, and PostToolUseFailure for
     a call that exits non-zero). A protected file whose content the call changed, and which no
     ask covered, is reported:
     - to the agent: "STOP and ask the operator";
     - to the operator, as a `systemMessage`.

     Each file is reported once per checkout per session. Content equal to HEAD's, origin/main's,
     main's, or that of a merge, rebase or cherry-pick being applied is not reported. A file a
     GRANTED call changed is named to the operator too, since the ask may have been answered by a
     mode rather than a person (round 2, SF7).
  3. **The patch removes the strict xfail markers** and adds `PostToolUseFailure` to the wiring
     pin's event set. The suite is green the moment the patch is applied.
- **The tests in this PR**, in `tests/test_claude_hooks.py`:
  - **39 strict-xfail nodes (W77).** 26 reproduce one Bash write each. Each command really runs in
    a scratch checkout and changes the file; that half passes today, and the ask is the half that
    fails. The 26:
    - `>`, `>>`, `tee`, `python -c`, a Python heredoc, `sed -i`, `cp`, `mv`, `cp` into the
      directory, `cd` then `sed -i`, and `bash -c`;
    - `git apply`, `git checkout <ref> --`, `git restore --source`, `git mv`, `git rm`, `rm`,
      `touch` of a new file, `ln`, `perl -i`, `eval`, `find -exec`, a shell script it runs, and
      `source` (review round 2);
    - a write after a `cd` inside a subshell (review round 1), and one behind `cd X ||` whose cd
      failed (Codex, round 2).
  - The other 13 xfails pin:
    - the wiring;
    - #1133's shape reported after the call, the command shown to the operator;
    - a script that wrote and then exited 1;
    - the once-per-file-per-session grant shared with the Edit path;
    - a granted ask on a directory covering the files the call writes in it (round 0);
    - the operator's notice stating its truncation, "showing 10 of 11" (round 0);
    - a granted over-ask (a path only named) not covering a later write of that file (round 1);
    - a grant covering its file in its own checkout only, Bash and Edit (round 2, SF1);
    - a grant on a sub-directory covering the files written in it, with no approval line the gate
      rejects (round 2, SF2);
    - the operator told when a granted call changes its file (round 2, SF7);
    - a slow `core.fsmonitor` not switching the after-check off (round 2, SF4);
    - an unwritable store still asking, and saying its after-check is off (round 2, SF5);
    - a failure in the Bash reading saying so (round 2, SF5).
  - **26 negative pins**, passing today and binding the patched guard:
    - 21 Bash calls that write no protected file, or only read one. Among them: a heredoc body
      that names writes, a quoted string naming a write, a comment, a restore from the index, a
      repo script that reads `scenarios/` and writes elsewhere, a glob-shaped Python string
      (round 0), and `sys.stdout.write`, `csv.writer(sys.stdout)` and `rm -rf` of an untracked
      `__pycache__` (round 2).
    - A protected change made before the call is not blamed on it.
    - Taking main's own content (`git checkout origin/main -- f`), or the local `main`'s, is
      neither asked about nor reported.
    - A merge being concluded (MERGE_HEAD's content) is not reported.
    - The after-check never rewrites `.git/index` (round 2, SF3).

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

  **Added in review round 2 — B's check on B's machine (#1004, comments 7035279995 and
  7035724117). EXPLAINED, as B's reproduced inference, not proven inside the app:**
  - **What happened.** W81's five Edits of `vinci/evals/variants.py` (2026-11-20 08:14–08:15Z)
    were INSIDE that session's scratchpad folder, in a worktree created there.
    - Each carries `permissionDecision: accept, source: config, reasonType: other`.
    - No PreToolUse guard record exists for any of them.
    - In that session (`1eded771`, 3,547 records, 2026-11-19 17:32Z → 11-20 09:18Z), 22 Edits and
      Writes in the scratchpad read `config / other`, and 15 in the project worktree read
      `config / classifier`.
  - **What it was not.** Hooks were on: SessionStart and `PostToolUse:Bash` ran. There was no
    `disableAllHooks` and no allow rule matching Edit, and the guard run directly on the same
    path asks.
  - **B's reproduction**, in B's own session: one Edit of a scratch copy's
    `vinci/evals/variants.py` inside B's scratchpad. It gave no prompt, `accept, source: config,
    reasonType: other`, and no guard record.
  - **B's reading:** a file-tool write inside a session's scratchpad is pre-allowed, and the
    PreToolUse guard is not run for it. It was not a Bash write, so this patch's mechanism does
    not explain it. The commit gate enforced it, and both of 11-20's scratchpad-worktree edits
    (W81's and W85's `variants.py`) carry the operator's words.
  - **The same class as SF1.** The grant SF1 found (session 90cb2a26, a scratch copy of
    `vinci/ledger/correction.py`) was given while editing in a worktree under the scratchpad. That
    explains how a grant existed with no ask shown: PostToolUse ran and recorded it, where no
    PreToolUse ask was ever raised. Round 2's per-checkout keys stop such a grant covering the
    real checkout. They do not make the scratchpad edit itself ask.
  - **B's interim rule:** a worktree that will edit a protected file is created under
    `.claude/worktrees/`, never under a scratchpad.
  - The design is not changed for it: no `deny` switch.
- #1104's record had decided the guard "is NOT made to deny" and that Bash was "the next route,
  which no hook sees". This patch keeps the first: it asks and reports, and never denies. It
  answers the second.

**HOW VERIFIED.**
- **Reproduction, on this branch.** The five hook and gate suites (`test_claude_hooks`,
  `test_protected_approval`, `test_one_gate`, `test_rg_d20_instructions_match_the_code`,
  `test_no_local_paths`) give **221 passed, 39 xfailed**.
  - Run with `--runxfail` (first measured at 11 write nodes), each write node fails at its ask, after its own disk
    assertion passed, e.g. "redirect: scenarios/IT.json changed on disk and nothing asked first".
  - The wiring node fails on `'decision_path_guard.py' in ['review_gate.py']`.
- **The patch, applied in a throwaway worktree of this branch** (never committed; removed after):
  - the same five suites give **260 passed**;
  - with the hook and wiring patched but the test file left as this PR has it,
    `test_claude_hooks.py` gives **40 failures**: the 39 W77 nodes as XPASS(strict), and the
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
  - round 2's guard: 81 ms before the call and 79 ms after it in the primary checkout, 70 ms and
    67 ms in this worktree;
  - the first draft: 122/112 ms and 149/117 ms, the same runs before `--no-optional-locks`;
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

**REVIEW ROUND 1** (Codex on `352bc35c`, 2 findings, both P2): 2 FIXED, each behind a pin that fails
on the PR head's patch and passes on the fixed one (2 failed → 2 passed, in a throwaway worktree):
1. FIX — a granted ask recorded approval for every path it named, even one the call never wrote.
   So the accepted over-ask (inline Python that reads a protected file and writes another) covered
   that file for the rest of the session, and a later record-API write to it was neither asked
   about nor reported. Now the grant is recorded only for the protected files the call changed. A
   pending ask still covers that call's own after-check. Pin:
   `test_a_granted_over_ask_does_not_cover_a_later_write_of_that_file`.
2. FIX — a `cd` inside `( … )` (or `$( … )`) carried into the commands after the subshell, so
   `(cd vinci && true); echo x >> vinci/dossier/verdict.py` resolved to `vinci/vinci/…` and did not
   ask. Each `(` now saves the directory and its `)` restores it. Pin: the `after a cd inside a
   subshell` write node.

The census's 100 asks are unchanged. Its 38 prompts assumed every granted ask covers its file for
the session. Under round 1's rule, a path the call only named is asked again; of the 100, at most
4 named a file they did not write.

**REVIEW ROUND 2** (A's independent review of `352bc35c`, 2026-11-20: SF1–SF7 and NITs; Codex's two
P2s overlap SF1 and the subshell NIT and are counted once, in round 1). Each FIX is behind a pin
that fails on the PR head's patch (`ce6807e1`) and passes on the fixed one: on the head's patch 13
nodes failed and 118 passed; on the fixed one, 131 passed (132 with item 10's pin, which
failed alone on the head's patch) (`test_claude_hooks.py`, markers removed,
in a throwaway worktree). Codex's second review (of `ce6807e1`) found one more, folded in as item
10; its pin failed on `ce6807e1`'s patch too.
1. **SF1, FIX.** A grant was keyed by repo-relative path, so one grant in a scratch clone covered
   that file in every checkout of the session. A measured it already happening on the Edit path:
   session 90cb2a26 granted a scratch copy of `vinci/ledger/correction.py` at 2026-11-10T05:03Z,
   and four later Edits of the real one ran unasked. Grants are now keyed by checkout and path, for
   Edit and Bash alike, and the Bash ask names its checkout. Pin:
   `test_a_grant_covers_its_file_in_its_own_checkout_only`.
2. **SF2, FIX.** A grant on `scenarios/archive` did not cover the file the call wrote in it, and
   the ask prescribed `Operator-approved: scenarios/archive "…"`, which the gate rejects
   (`protected_approval.py` takes an exact path or one of main's directory entries). A grant now
   covers what sits under it. A directory ask prescribes `<each file it changes under …/>`; a
   path inline Python only names says it MAY write it. Pin:
   `test_a_grant_on_a_sub_directory_covers_the_files_written_in_it`.
3. **SF3, FIX.** `git status` took the optional index lock: in A's probe, 29 of 150 concurrent
   `git add` calls failed on `index.lock`, and 0 with `--no-optional-locks`. Every git call of the
   after-check now passes it. Pin: `test_the_after_check_never_rewrites_the_index`. Measured here
   first: a plain `git status` on a stale index rewrote `.git/index`, and one with the flag did not.
4. **SF4, FIX.** With `core.fsmonitor` set, each status ran into the 10 s timeout and the write went
   unreported. The guard now runs `-c core.fsmonitor=false` with stdin closed. Pin:
   `test_a_slow_fsmonitor_does_not_switch_the_after_check_off` (a 12 s monitor; the call must
   report, and finish under 9 s).
5. **SF5, FIX.** The per-call reading was written before the ask was printed, so an unwritable
   store dropped the ask, silently. The ask is now built first, a store failure adds a
   `systemMessage` saying the after-check is off, and any crash in the Bash path prints one naming
   it ("fail loud"). Pins: `test_an_unwritable_store_still_asks_and_says_its_after_check_is_off`
   and `test_a_failure_in_the_bash_reading_says_so`.
6. **SF6, FIX (the record).** A concurrent writer is blamed on the call, and uses up the
   once-per-session report: another process writing during a call, or a `run_in_background`
   command whose write lands between calls. Both are now in "cannot see", below.
7. **SF7, FIX.** The patch assumed an ask reached the operator. After a granted call, the operator
   is now told which protected files it changed. Pin:
   `test_the_operator_is_told_when_a_granted_call_changes_its_file`. A's measurement, for the
   record: 56 guard asks 2026-11-04 → 11-17, all in auto mode — 55 resolved by the user, 1 rejected
   by the classifier, 0 accepted by the classifier or a mode; 94 of 187 protected edits ran silent
   on an earlier grant; 2 guard runs timed out (`hook_cancelled`) and failed open. Not recording a
   grant under `bypassPermissions` is DEFERRED: none of the 56 asks ran in that mode.
8. **NITs FIXED:**
   - `main` is a known state after the call, as before it (pin:
     `test_taking_the_local_mains_content_is_not_reported`);
   - `sys.stdout.write` and `csv.writer(sys.stdout)` are no file write (2 negative pins);
   - a removal counts only where git tracks something, so `rm -rf vinci/scoring/__pycache__` is
     silent (pin: the `rm an untracked __pycache__` negative). That also closes round 0's DEFER
     #5;
   - the operator's notice shows the command, cut at 200 characters and saying so;
   - the forms A listed as unpinned now have nodes: `git apply`, `checkout <ref> --`,
     `restore --source`, `git mv`, `git rm`, `rm`, `touch`, `ln`, `perl -i`, `eval`,
     `find -exec`, a run script, `source`, and a merge being concluded;
   - the census, BOUNDARY and apply procedure below are corrected.
9. **NITs DEFERRED**, each a before-call miss the after-check catches:
   - a quoted word starting with `#`, read as a comment;
   - an apostrophe in a trailing comment, which makes `shlex` raise so the command is unread;
   - `git checkout <ref> <file>` with no `--`;
   - `pushd`;
   - `find -exec … {}` and `xargs sed -i`, whose targets come from input;
   - `rsync`, `install`, `truncate`, `tar`, `unzip`, `curl -o`, `node -e`, `ruby -e`, `awk`
     redirects;
   - `$( )` and `$VAR`.

   Also deferred: the load cost (A measured 20k untracked files under `scenarios/` at about 1 s a
   call, 5.1 s at most) and the mutant A found surviving (sed's script read as a file). No
   portable sed script is also a protected path, so no pin can kill it.

10. **Codex P2 (on `ce6807e1`), FIX.** A `cd` that fails before `||` moved the reader's directory,
    but bash runs the fallback from where it started: `cd /missing || printf … >>
    vinci/dossier/verdict.py` resolved under `/missing` and did not ask. The command right after
    `cd X ||` now resolves from the directory before the cd; the commands after it keep X, for
    the `cd X || exit 1; …` idiom. Pin: the `after a cd that failed, behind ||` write node.

The census was re-run on round 2's guard: the same 100 calls, the same hits.

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
  - The census's path reader is LEXICAL: it finds a checkout by the `mosaic-theory` and
    `.claude/worktrees/<name>` parts of a path. So it skips scratch clones under the temp folder,
    which A counted as up to 13 more asks in 4 sessions. It also counts every removal as tracked,
    since git cannot be asked about a deleted worktree.
  - The after-check's report rate is UNMEASURED: a transcript records commands, not what they
    changed.
- **"96 wrote"** means the command's text writes the named protected path. Whether each write was
  approved, committed or reverted later is not read.
- **The suites' counts**: the five test files named above, `-o addopts=""`, on this branch at
  base `6c22b222` with the tests added, and on the patched throwaway worktree.
- **Latency**: wall time of `subprocess.run` of the hook with a `ls scenarios | head -3` payload,
  2026-11-20, median of 10. It includes interpreter start-up.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **About 0.15 s on every Bash call** (round 2's guard): the two readings, `git status` and
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
    resolve, each named target's checkout and `CLAUDE_PROJECT_DIR`;
  - a protected file in a worktree under a session's SCRATCHPAD. A file-tool Edit there gets no
    ask, since the app pre-allows it and runs no PreToolUse guard (B's reproduced inference,
    above). Whether this patch's Bash-path ask and after-call notice run for a Bash call writing
    into a scratchpad is **UNTESTED**: this session's own checks ran Bash in a scratchpad worktree
    by calling the hook directly, never through the app's dispatch;
  - who wrote. Another process writing during the call, or a `run_in_background` command whose
    write lands between calls, is blamed on the call, and uses up the file's once-per-session
    report (A's review, SF6).
- **Over-ask class:** inline Python that names a protected path and writes ANOTHER file. That was
  1 of 100 in the census.
- **Fails open**, as the guard always has, but loudly: a crash in the Bash path lets the call run
  and prints a `systemMessage` naming it, and the gate is still the record. A guard run that
  times out (Claude Code's `hook_cancelled`) still fails open silently.
- **A denied ask leaves a per-call reading** in the temp folder, since no PostToolUse follows it.
  The next call of that session removes any older than a day.
- **Falsifiers:**
  - the operator clicks through these prompts within seconds, as 10 of #1104's 47 Edit grants
    were;
  - a protected change reaches the gate after a Bash call with no report;
  - the prompts per session climb past the census's 12. Then the reading is wrong for this
    project's habits;
  - an "approved … it changed" notice names a write the operator did not approve. Then a mode or
    classifier is answering the asks (SF7);
  - the guard is silently not run, as it was for W81's scratchpad `variants.py` Edits (above).
    Then this patch's ask is as absent as the Edit one, and the commit gate stays the only
    enforcement. A Bash write into a scratchpad worktree showing no ask, or no after-call notice,
    is the first test of that.
- **For the operator, to apply** (STATE row 32, item (37)). Apply it on a branch, never on local
  main: worktrees are cut from local main, so a hook committed there would reach new sessions
  before review. From a checkout whose main holds this PR:

  ```bash
  git fetch origin && git switch -c w77-apply origin/main
  ```
  ```bash
  git apply --check docs/patches/w77-bash-writes-ask-first.diff
  ```
  ```bash
  git apply docs/patches/w77-bash-writes-ask-first.diff && git rm -q docs/patches/w77-bash-writes-ask-first.diff
  ```
  ```bash
  git add .claude/hooks/decision_path_guard.py .claude/settings.json tests/test_claude_hooks.py && bin/commit -m "W77 applied: the decision-line guard reads Bash calls" -m 'Operator-approved: .claude/hooks/decision_path_guard.py "<your words>" <YYYY-MM-DD>' -m 'Operator-approved: .claude/settings.json "<your words>" <YYYY-MM-DD>'
  ```
  ```bash
  git push -u origin w77-apply && gh pr create --fill
  ```

  The paths are staged by name, so no untracked file rides along. A session started before the
  merge may keep the old wiring, because Claude Code reads hook settings at startup.
  - **Rollback:** revert the apply commit, by PR like any other change.
  - **Emergency off-switch:** `{"disableAllHooks": true}` in `.claude/settings.local.json`. That
    file is git-ignored, so it is per machine. It turns off EVERY hook, the fast gate and the
    review gate included, so remove it once the revert lands.
