---
id: W77b
status: open
date: 2026-11-20
prs: []
supersedes:
superseded-by:
---

# W77b: the W77 guard patch, fixed before anyone applied it — a long string no longer switches the after-check off, slow git no longer costs the ask, and a change of unknown cause is never blamed on the call

**WHAT.** `docs/patches/w77-bash-writes-ask-first.diff` is REPLACED: it is now W77 (#1155) plus the
fixes below, one patch against main's unpatched `.claude/hooks/decision_path_guard.py` and
`.claude/settings.json`. No hook is changed by this PR; the operator applies the patch (STATE row
32, item (37)). The operator's ruling on B's review, 2026-11-20, verbatim: "Hold and fix first".
The held `w77-apply` branch, which applies the patch as merged, is not to be pushed.

B's review is on #1004, comment 7037804674. Each fix, with the finding it answers:
1. **B#1 — a long string switched the after-check off, silently.**
   - Inline Python that makes a write call has each string literal under 300 characters read as a
     path. Under the system `python3` 3.9.6, a 256–299-byte literal with no `/` makes
     `Path.is_dir()` raise `OSError` 63 (a name too long). So the before-reading crashed, no
     per-call reading was kept, and the after-check said nothing about a write the command did not
     show.
   - The fix: `locate` reads with `os.path.isdir` / `os.path.exists`, which answer False, and
     returns None on any `OSError` or `ValueError` (a NUL byte). `_roots` does the same.
   - A reading that crashes for any other reason no longer ends the hook: the fingerprint is still
     taken, the after-check still runs, and the crash is printed to the operator.
2. **B#3 — slow git lost the ask.**
   - The ask was printed only after every checkout's `git status` had run, each with its own 10 s
     timeout, inside the hook's 15 s. Two checkouts at 8 s each outlived the hook, which was killed
     with nothing printed: a visible write went through with no ask.
   - The fix: every git call of one hook run shares ONE budget, `BUDGET_S = 10.0` s from the
     hook's start. The ask is built before any `git status` and is printed whatever git does.
   - Fails open, loudly: a checkout git did not answer for (a timeout, a non-zero exit, the budget
     spent) is named in a `systemMessage`, before the call ("the after-check is off for it in …")
     and after it ("it could not read git status in …").
3. **B#2 — wrong blame and wrong advice.**
   - The after-check sees WHAT changed during a call, never WHO changed it. W77 told the agent
     "if it is not [intended], restore the file". That can undo approved work: another process's
     change, a subagent's (subagents share the parent's `session_id`), or a `run_in_background`
     write that lands during a later call.
   - The fix, the report: it says "The cause is unknown" and lists the causes. It tells the agent
     to STOP and ask the operator, and "Do not restore or undo it yourself: it may be someone
     else's approved work". The operator is told as before.
   - The fix, the count: the report is made for EACH change. W77 spent a once-per-file-per-session
     notice, so a report about a change the call never made silenced the next unasked write of that
     file. A file that does not change again is not reported again, since each call compares its
     own before and after.
   - The fix, background calls: a `run_in_background` call's grant covers the files it visibly
     writes. Its PostToolUse runs before its command writes, and W77 grants only what a call
     changed, so its own asked, granted write was reported as unasked when it landed. The operator
     is told the grant was made.
4. **B#7 — misses before the call.** Now read:
   - the shell keywords `if`, `then`, `else`, `elif`, `do`, `while`, `until`, `!` and `{` in
     front of a command;
   - a process substitution (`> >(tee f)`), whose `>(` was taken as the redirect's target;
   - a single-level brace expansion of a path-shaped word (`mv vinci/seal.py{,.bak}`). shlex drops
     the quotes, so only a word of path characters expands, never code or JSON;
   - a shell script run by its path (`./tools/write.sh`), by a `.sh` / `.bash` name or a shell
     shebang, as one run by `bash` already was.
5. **B#8 — the guard's own grant store.** A Bash write into the store (`guard-<session>.json`
   there IS a grant) asks every time, as does an Edit or Write of a file there. No grant covers the
   store, not even a grant naming the store file itself.

**WHY.** B reviewed the patch as merged before the operator applied it, as an independent check
(main `e7fbe63c`, patch sha256 `605b9e75…`, in a scratch copy on B's machine). B found finding 1 in
25 of 20,145 real Bash calls since 2026-11-04 there, all Python heredocs, against the record's
"0 raised". The operator held the apply. The patch had never been applied anywhere, so it is
replaced rather than followed by a second one: the operator applies one patch, reviewed once more.

**HOW VERIFIED.**
- **The pins.** 18 new nodes and 1 changed in `tests/test_claude_hooks.py`. Each is a strict xfail
  on main, like the rest of W77, since main's guard reads no Bash call:
  - B#1: `test_a_long_string_in_a_writing_script_does_not_switch_the_after_check_off` (B's repro,
    a 282-byte sentence plus `(Path('scen'+'arios')/'IT.json').write_text('{}')`, run under the
    hooks' own interpreter); `test_a_path_the_filesystem_refuses_to_read_locates_nowhere` (`locate`
    of a 282-byte name and of a NUL path, under that interpreter);
    `test_a_reading_that_crashes_still_keeps_the_after_check`.
  - B#3: `test_slow_git_never_costs_the_ask` (B's repro: `git status` slowed to 8 s in two
    checkouts, the hook run with the timeout settings.json gives it);
    `test_a_git_status_that_fails_is_said_out_loud` (before the call and after it).
  - B#2: `test_a_change_another_process_makes_during_a_call_is_not_blamed_on_it`;
    `test_a_granted_background_write_is_not_reported_when_it_lands`. The changed node:
    `test_a_script_that_writes_a_protected_file_it_never_names_is_reported_after_it_runs` asserted
    `again == {}` (once per file per session) and now asserts that a second change is reported, and
    a call that changes nothing is not.
  - B#7: ten `BASH_WRITES` rows — `for … do cp`, `while … do sed -i`, `until cp`,
    `if … then sed -i`, `else python -c`, `{ … } cp`, `! cp`, a script run by its path, process
    substitution and brace expansion.
  - B#8: `test_a_write_to_the_guards_own_grant_store_is_asked_about`.
- **Each failed first, on the patch as merged.** That guard was swapped back into the scratch
  application with this PR's tests: **19 failed, 131 passed** of `test_claude_hooks.py`'s 150
  nodes. Each failed at the assertion it targets: `OSError: [Errno 63] File name too long` under
  `/usr/bin/python3`; `killed at the hook's own timeout with nothing printed: no ask`; "restore the
  file" in the report; `{}` where a second change should be reported; nothing asked for each
  keyword form. On the updated guard: **150 passed**.
- **Two mutants.** Grant coverage applied to the store's own hits leaves a store write unasked once
  a grant names the store file: the grant-store pin fails on it. A background grant recorded on
  `PostToolUseFailure` too: the background pin fails on it (review round 0, item 1). Each passes
  on the guard.
- **The strict-xfail scheme.** With this PR as merged (main's hooks and wiring, the new pins
  marked), `test_claude_hooks.py` gives **93 passed, 57 xfailed** (W77's 39 and these 18), and the five
  suites below give 229 passed, 57 xfailed. With the patch applied, the five hook and
  gate suites (`test_claude_hooks`, `test_protected_approval`, `test_one_gate`,
  `test_rg_d20_instructions_match_the_code`, `test_no_local_paths`) give **286 passed**. With
  the hook and wiring patched but this PR's test file left as merged: **58 failed** — the 57 as XPASS(strict) and the wiring pin's event set, which
  lacks `PostToolUseFailure`. So no marker can outlive the fix unnoticed.
- **The patch** applies with `git apply --check` to this branch's tip, and the result is
  byte-identical to the tree the tests above ran on. Regenerating it from the merged patch's own
  application gave a byte-identical copy of the merged file, so `git diff` is the generator.
- **The census, on real calls** (BOUNDARY below), each call read through the guard module itself
  under `/usr/bin/python3` 3.9.6:
  - **The reader crashes on 8 calls as merged, and on 0 updated.** All 8 are `OSError 63`, all
    Python heredocs, in 8 sessions, 2026-11-11 → 11-19, every one since 11-04. That is 8 of 39,528
    calls since 11-04 here, against B's 25 of 20,145 on B's machine.
  - **Asks: 108 as merged, 107 updated**, with no grants applied. The one call that moved, from
    session 4147cb8c on 2026-11-17, is `for w in base head; do cd $S/$w; python - <<'EOF' …
    scenarios/WERN.json …`. W77 read `do cd …` as a command named `do`, kept the outer directory,
    and asked about the outer checkout's `scenarios/WERN.json`. The write was to `$S/$w`'s. The
    updated reader reads the `cd`, which only the shell can resolve, so it names nothing: the rule
    W77 already had for `cd $VAR`.
  - **The new forms** (the keywords, process substitution, brace expansion, a script run by its
    path, the store) **added 0 asks** in the 42,485 calls. B found 0 of them in 20,145.
- **Latency** (B#4). Wall time of one hook run under `/usr/bin/python3`, PreToolUse then
  PostToolUse, on an `ls scenarios | head -3` payload; n=30 each; the three guards interleaved per
  round. Medians, before / after the call:

  | checkout | today's guard | W77 as merged | updated |
  |---|---|---|---|
  | primary (`~/dev/mosaic-theory`) | 52 / 48 ms | 135 / 148 ms | 147 / 136 ms |
  | this worktree (a dirty tree) | 55 / 52 ms | 187 / 165 ms | 182 / 164 ms |

  So the update costs what W77 did: about 85–130 ms more than today's guard before each Bash
  call, and as much after. W77's record said 81 / 79 ms and "about 0.15 s on every Bash call". B
  measured about 300 / 285 ms at load 10–13 on B's machine (today's guard: 109 ms). Corrected:
  **about 0.2–0.25 s added to each Bash call here, and about 0.4 s on B's machine**. The figure
  moves with the machine, its load and the size of the checkout's `git status`. A first run of
  this measurement passed relative script paths, so every run failed at once and timed nothing;
  it was caught because the patched guards timed the same as today's, and every run is now
  asserted to exit 0 with nothing on stderr.
- **The patched guard itself:** `mypy --strict --warn-unused-ignores` clean. `ruff` (the repo's
  config) is clean but for line 7's E501, which main's file has too. It parses at
  `feature_version=(3, 9)`, and every pin that runs it as a hook runs it under `/usr/bin/python3`
  where the timing or the interpreter matters (B#1, B#3).

**REVIEW ROUND 0** (`/code-review high --fix`, on the patched guard and the tests, applied in this
worktree): 6 findings, 4 FIXED, 2 SKIPPED.
1. FIX — a background call's grant was recorded on `PostToolUseFailure` too. A launch that failed
   writes nothing later, so its grant would cover a file that a later write, through a path no
   command names, then changes unreported: Codex's round-1 over-grant again. Now granted on
   `PostToolUse` only. Pin: the failed-launch half of the background test, which fails on the
   unfixed guard.
2. FIX — the trouble note kept the first line of git's stderr, cut at 200 characters, and said
   neither (CLAUDE.md: a truncated output prints its own truncation). Now every line, joined, and a
   cut says "the first 200 of N characters".
3. FIX — a command named by its path was read in full (up to 1 MB) before its suffix or shebang
   was checked. Now its first line decides, and only a shell script is read.
4. FIX — the pin for item 1.
5. SKIP — the "approved … changed" notices hand-roll "(showing k of n)" beside the new `_listing`.
   Their wording is W77's merged one, which SF7's pin reads; restyling it is churn.
6. SKIP — the budget is measured from the module's import, not the process's start, so start-up
   under load is outside it. Python 3.9's standard library has no portable process-start clock;
   the residual is accepted under WHAT IT COSTS.

**BOUNDARY.**
- **The census.** Population: every assistant `tool_use` named `Bash` in
  `~/.claude/projects/*mosaic-theory*/**/*.jsonl` on this machine, read 2026-11-20 between about
  11:27Z and 11:33Z. This session's own transcript (`39bfca39`) is excluded, and calls are de-duplicated by
  tool-use id: 396 transcript files, **42,485 calls, 97 sessions**. Window: the timestamps present,
  2026-06-25T11:51Z → 2026-11-20T11:23Z. **39,528** of the calls are since 2026-11-04, in 84
  sessions. W77's census read 34,778 calls (2026-11-09 → 11-20) and is not this population.
  - "crash": the hook's own PreToolUse path (`_bash_before`, the real `locate` and `_roots`), with
    `fingerprint` stubbed to `{}` and the store in a temp folder. Each call is read from its
    recorded `cwd` against today's filesystem.
  - "asks": `bash_writes` + `protected_hits`, with W77's LEXICAL checkout reader (a deleted
    worktree's paths still resolve) and every removal counted as tracked; no grants applied.
- **Latency**: measured 2026-11-20 between about 11:34Z and 11:36Z, at a 1-minute load average
  of 49.6–51.4 on this machine (other sessions' work), the session id `latency-w77b`, with
  `CLAUDE_PROJECT_DIR` set to the checkout measured. Each number includes interpreter start-up.
- **B's numbers** are B's machine's, as B states them: 85,415 Bash calls 2026-07-13 → 11-20, of
  which 20,145 since 11-04, system python3 3.9.6, git 2.50.1, Claude Code 2.1.326.
- **The suites' counts**: the files named, `-o addopts=""`, `-n 8`, on this branch rebased onto
  `a1ecc22b` with this PR's tests, and on a scratch application of the patch in this session's own
  worktree under `.claude/worktrees/` (never committed; the hook files restored before every
  commit).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **About 0.2–0.25 s on every Bash call here** (0.4 s on B's machine; HOW VERIFIED), where W77 said
  0.15 s. It runs beside the hook already on each event (`review_gate.py` before,
  `codex_request.py` after), and hooks on one event run in parallel.
- **Each change is reported.** A script an agent re-runs, writing a protected file through a path
  it builds, is reported on each run that changes the file, where W77 reported it once per
  session. The report says how to have one ask cover the session instead: name the file in the
  command, so the reading asks before it runs. Falsifier: an agent told this keeps running the
  unchanged script, and the operator's notices about one write pile up.
- **The cause stays unknown.** The after-check still cannot tell another process's write from the
  call's own, and does not try. It reports both, and no longer advises either the restore or the
  blame. A concurrent change during a read-only call still blocks that call's agent until it asks
  the operator.
- **The git budget is a cut-off.** Past 10 s of git in one hook run, the remaining checkouts go
  unread for that call, and the hashing of what `git status` lists stops. Each is named to the
  operator; the commit gate stays the record.
- **The after-check still cannot see** (W77's list stands, with B's correction to its scratchpad
  line in W77's amendment):
  - **a worktree created inside the same call** (B#6): `git worktree add X && cd X && echo x >
    scenarios/IT.json` is silent before and after, and only the commit gate sees it. It is common:
    483 of the census's 42,485 calls run `git worktree add`, 407 of them with a write-shaped command
    after it in the same call (a regex over the text, not a reading). Of their 530 `add` targets,
    431 are a `$VAR` path no reading resolves and 99 are literal. Catching it means resolving shell
    variables, which the reader does not do.
  - a store path built at run time (`tempfile.gettempdir()` in Python, `$TMPDIR` in a shell word).
    The store is outside git, so the after-check cannot see it either.
- **Known misses before the call**, each one the after-check catches once the call has run:
  - a case-variant path (`Scenarios/IT.json`) on macOS's case-insensitive disk;
  - a nested or ranged brace (`{a,{b,c}}`, `{1..3}`);
  - a `cp` or `mv` whose source is `$VAR`;
  - a `cd` into a directory only the shell knows, as in the census's one moved call;
  - W77's own list.
- **Fails open, loudly**, except where the hook process itself is killed (Claude Code's
  `hook_cancelled`). Under the budget that needs more than about 5 s of interpreter start-up and
  Python work on top of the 10 s of git.

**For the operator, to apply** (STATE row 32, item (37)). This is the same procedure as W77's,
naming the same path, which now holds the updated patch, with one step first. Apply it on a
branch, never on local main: worktrees are cut from local main, so a hook committed there would
reach new sessions before review. From a checkout whose main holds this PR:

First, drop the held branch that applied the patch as merged (it was never pushed):

```bash
git switch main && git branch -D w77-apply
```
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
- **After the merge, in a fresh session** (B's suggestion): make one Bash write of a protected
  file in a worktree under a scratchpad, and one under `.claude/worktrees/`. Each should ask
  before it runs. A script write that names no path should be reported after it. No ask, or no
  report, is the first test of the falsifier W77 records for a guard the app does not run.
- **Rollback:** revert the apply commit, by PR like any other change.
- **Emergency off-switch:** `{"disableAllHooks": true}` in `.claude/settings.local.json`. That file
  is git-ignored, so it is per machine. It turns off EVERY hook, the fast gate and the review gate
  included, so remove it once the revert lands.
