---
id:
status: accepted-risk
date: 2026-10-12
prs: [708]
supersedes:
superseded-by:
---

# The monitor runs at the latest close, a back-dated day is refused in code, and a past day is never re-cut — operator ruling on #707's open question

**WHAT.** The operator ruled option 1 of the three in
`docs/records/2026-10-11-monitor-reads-nothing-after-its-day.md` (2026-10-12): **a moved page gets a
NEW monitor day; a past day is never re-cut.** Stated so it needs no judgment: **`vinci monitor` is
run with NO `--ref`, which files the LATEST close** — the last session on or before today — and reads
filings through today.
- **Later than the newest committed day:** the run writes a new day.
- **The newest committed day itself:** the run is the same-session re-run.
- **A day that a later close sits after is never re-run.** `--ref` is for scratch re-cuts only:
  `--ref <close>` on a later morning would bound the read at the close and hide that morning's 8-K,
  the defect #707's review fixed.

Where it lives:
- **`docs/RUNBOOKS.md` §j MONITOR DAY** — the loop: date, run, mirror, check, commit as an artifact.
- **In code, for the case code can see.** `monitor.write_snapshot` now refuses ANY day that a later
  day file already sits after: an overwrite, as before, or a BACK-DATED day that was never written.
  The old guard fired only when the day's file existed, so `--ref 2026-10-01` between the committed
  09-22 and 10-09 would have written a new October-1 file reading today's pages. `rewrite_history=True`
  stays the explicit way through.
- **The failure the operator meets.** `tests/test_panel_emit.py::
  test_emit_is_deterministic_over_the_committed_corpus` goes red whenever a page moves after the
  latest day, or when the emitter's code changes. Its assertion message names both causes and the
  ruled remedy, so the tempting fix (re-running the day it names) is answered where it is tempting.
  The assertion itself is unchanged.
- **STATE.md §5.0 row 5:** the past-day re-cut item #707 added is closed. The row's second "(b)"
  (phase 5 and the emitter), which duplicated a label, is relabelled "(c)".

**WHY.** #707 bounds every DATED input a day reads, but the panels, the measured rows and the
record-read fields read today's pages, records and cards. None of those has a per-item date to
filter on, so a re-cut after a later close writes later information into an earlier date; the 09-22
re-cut drew UBER's 10-09 multiple. Of the three options, the rule was already the practice (#705
wrote `2026-10-09.json` rather than re-cut `2026-09-22`). Versioning every document by commit date
(option 2) is kept for the day past days are re-cut for analysis. Stamping (option 3) would only
label the lookahead.

**REVIEW FIXES (same PR, before merge).** A code review of the first cut found eight issues.
- **Fixed in the review's own commit (`128fc99e`):**
  - **The run instruction.** It was `--ref <latest close>`, which brought back #707's hidden-8-K
    defect; it is now no `--ref`.
  - **The step-4 check.** It failed a correct run by comparing filings with the day's `as_of`; it
    now compares with the run date.
  - **The guard's description.** The runbook and record said `write_snapshot` refused more than it
    did.
  - **The test message.** It blamed every failure on "a page moved"; an emitter change also turns
    the pin red, and writing a new day over it would commit the regression.
  - **The falsifier.** It now counts ADDED day files too, and states that commit time stands in for
    run time.
- **Fixed in this commit:**
  - **The accepted risk was not earned.** CLAUDE.md requires showing the cheap fix is unavailable,
    and refusing a back-dated day is a few lines — so it is built (above), and the risk is re-scoped
    to the case it cannot see (below).
  - **The duplicate "(b)"** in row 5.
  - **The PR description** quoted the old message and instruction.

**HOW VERIFIED.**
- **The message, on the real failure shape** (worktree at `9b426cdc`).
  `data/monitor/2026-10-09.json` was set aside, which makes `2026-09-22` the latest day — the state
  #705 was in after UBER's page moved. The pin fails on UBER's two panels and prints the remedy. The
  file was restored and the pin is green again.
- **The guard, on the real command.** `python -m vinci.cli monitor --ref 2026-10-01`, run against
  the committed corpus (days 07-20, 08-11, 09-16, 09-22, 10-09), printed the book, then stopped:
  `FileExistsError: …/data/monitor/2026-10-01.json would be a BACK-DATED day: 1 later snapshot(s)
  already exist (next: 2026-10-09)…`. It exited 1, and `data/monitor/` was unchanged.
- **Pins:**
  - `test_a_back_dated_day_is_refused_even_though_it_was_never_written`: the back-dated day is
    refused and nothing is written; the front re-runs; a day after the newest is written;
    `rewrite_history` still goes through.
  - `test_the_command_refuses_a_back_dated_day_and_writes_nothing`: the same, through the real
    command over the real ledger.
  - Mutation: restoring the old "only if the file exists" condition fails both.

**BOUNDARY.**
- **The demonstrations** ran on the committed corpus at `9b426cdc` plus this branch, 2026-10-12.
- **"UBER's two panels"** are `multiple_and_price` and `dilution`, out of 124 rows.
- **The guard run** used the five committed days listed above; the only later day relevant to
  10-01 is 10-09.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **ACCEPTED: a re-cut of the NEWEST day after a later close, before that close has a file.** No day
  file sits after it yet, so `write_snapshot` cannot tell it from the routine re-run of the front.
  Only an explicit past `--ref` reaches it; the routine no-`--ref` run files the latest close and
  never does. The window shuts as soon as the later close's file is written, after which the guard
  refuses it.
- **Why the fix is not the cheap one.** Both available checks need something this guard does not
  have:
  - **The session calendar past the day.** That is a price fetch at write time, walking back from
    today. `session_on_or_before` fails loud when there are no bars within a week (the
    fetch-is-not-a-holiday rule, `docs/records/2026-09-22-monitor-fetch-error-is-not-a-holiday.md`), so every frozen-data test of the command, and every offline
    scratch re-cut, would need a faked "today".
  - **The session each page is struck on.** That needs a ruling first: a page carries several dates
    (price as-of, CIQ snapshot, screen reference — #702's `date_semantics`), and which one is "its
    session" is a definition, not a line of code.
- **Falsifier:** a committed day file ADDED or modified in a commit made after a later session's
  close — visible in `git log -- data/monitor/<day>.json` against the session calendar. Commit time
  is a proxy for run time: a run made before the later close but committed after it reads as a
  violation, so a hit is checked against the run before it is called one.
- **A moved page can leave the panel-emit pin red until the next close** when the page is struck on
  a session later than the latest committed day and that session's file has not been written yet.
  The remedy is to run the latest close, which needs that close's prices.
