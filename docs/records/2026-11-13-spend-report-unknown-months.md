---
id:
status: shipped
date: 2026-11-13
prs: [1064]
supersedes:
superseded-by:
---

# The spend report never puts a draw in a month it cannot show it ran in, and never prints $0 for a graph month it cannot see: Codex's two deferred P1s on #1061 are fixed

**WHAT.** This is the follow-up to #1061 (`docs/records/2026-11-13-monthly-spend-report.md`, merged
as `81f97600`). Codex's second review of #1061 found two P1s, both in the class "unknown is never
zero". #1061 had used its two bounded rounds, so both were deferred to this PR.

1. **An undated evals draw is bounded, never guessed** (`vinci/spend.py` `evals`).
   - The old rule: a draw row carries no time, so it took the latest stamp above it. A
     `run-compare` ledger opened on 28 Oct and resumed on 3 Nov therefore put November's draws in
     October, as a definite figure.
   - The new rule: a draw lies after the stamp above it and before the `build_end` below it.
     - The lower bound is any stamp: the approval's `opened_at`, a `build_start`'s `started_at`,
       or a `build_end`'s `t` (epoch seconds, `time.time`).
     - The upper bound is a `build_end` only. A `build_start`'s time is taken before its request is
       captured, under a lock that a concurrent build's draws do not take. A draw appended above it
       can therefore be later than its stamp (review round 0).
     - A `build_end` bounds only its OWN build's draws, matched by label
       (`<registration sha>:<ticker>:build<n>`, which `run_build` gives its draws). Its `t` is
       taken before its row is written, with no lock held over the draws, so another command's
       draw appended just above it can be later (Codex P2 on #1064, round 1).
     - With no `build_end` below, the upper bound is the ledger file's last write, the latest time
       any row can have been appended. For byte-identical copies, it is the earliest of their file
       times.
   - Bounds within one month place the draw in that month.
   - Bounds spanning months place it in **no** month. Each month it might belong to prints its
     figure as a floor ("≥") and names the draws: "N undated row(s) in evals ($X) that ran across
     a month boundary and may belong to this month". The total reads "at least".
2. **A graph month after the latest recorded re-judge is NOT READ** (`graph_judge`).
   - A re-judge that stopped (over budget, or on a judge error) spent money and wrote nothing, so
     no later month can be shown to be $0.
   - The month of the recorded re-judge carries the same blind spot: an earlier re-judge it
     overwrote, or a stopped one. Its figure is therefore a floor ("≥$2.61" for 2026-11). This
     extends finding 2 to its own month, and is stated here as such.

`Bucket` gains `unknown`: spend that may belong to the month and is not in its `usd`. Any entry
makes the figure "≥" and the total "at least", naming it, just as unpriced rows already did (#1061,
round 2).

**WHY.** CLAUDE.md: fail loud, never fabricate. A definite month total holding spend from another
month, or a $0 for a month with no record, is a fabricated figure. Both findings are Codex P1s on
`bff7ef27` (`vinci/spend.py:227` and `:324`), deferred on #1061 because its bounded rounds were
spent (the pr-feedback skill).

**HOW VERIFIED.**
- **Fail first.** At `81f97600`, all five changed or new pins fail:
  - `test_a_draw_whose_bounds_span_months_is_not_placed_and_the_figure_is_a_floor`. It replaces
    `test_a_draw_is_dated_by_the_latest_stamp_above_it`, which pinned the old rule.
  - `test_a_resumed_run_compare_is_never_put_in_the_month_its_ledger_opened`, Codex's exact case.
    It has a positive half: the same draws, last written 29 Oct, are October's.
  - `test_a_month_after_the_latest_rejudge_is_not_read`.
  - `test_the_graph_judge_reads_the_committed_rejudge`, whose recorded month is now a floor.
  - `test_a_build_end_bounds_the_draws_before_it`. This is a supporting positive pin. It fails at
    base only because the `unknown` field is new; base's dating gives the same October figure.
- **Review round 0** (`/code-review high --fix`) added two more pins, both red on the round's
  input:
  - `test_a_build_start_is_no_upper_bound_for_the_draws_above_it`, the concurrent-build case;
  - `test_a_byte_identical_copy_bounds_by_the_earliest_last_write`.
- **Round 1 (Codex P2 on #1064)** added `test_a_build_end_bounds_only_its_own_builds_draws`, which
  is red on `6f7594de`. In an interleaved ledger, a `run-compare` draw above a build's
  `build_end` is not that build's, so it is not October's. Re-run as of 2026-11-13 14:11:57Z:
  November at least $384.17 (evals $290.85, still growing). October is unchanged at $136.49. No
  row in either month is named as may-belong.
- **The test ledgers' file times are set,** never the day the suite runs, because the last write
  is now an input.
- **The real run,** re-made after review round 0, as of 2026-11-13 13:34:22Z, over the two ledger
  roots (the coordinator's notes folder and the panel exports folder), with
  `origin/theme-intelligence-state` at `ea8fb4a6`:
  - **November:** pages $66.98, evals $278.93, theme desk $23.73, graph judge ≥$2.61. The total
    reads "at least $372.25", naming the graph judge's blind spot. Confirmations and validate-keys
    are not included.
    - Evals covers 8 ledgers and 612 draws. That includes #953's run folder, which now exists, and
      E2's ledger, still growing.
    - No ledger has a draw whose bounds span months.
  - **October:** $136.49, unchanged, with the graph judge NOT READ.

**BOUNDARY.**
- **Window:** November from 2026-11-01T00:00Z to the as-of time, and the whole of October.
- **Sources:** the committed run files at this PR's base `81f97600`; every budget ledger under the
  two roots, all printed by the run; the state branch at `ea8fb4a6`; `judged_by` at `81f97600`.
- **Excluded:** as in #1061's record.
- **Ledger file times** are as found on this machine.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A copied ledger gets a later last write,** so its undated draws may span more months. That
  errs toward a floor, never toward a wrong month.
- **A ledger whose file time was set backward** (`touch -t`, or a restore) would bound its draws
  too early. The report cannot detect that, and it is accepted. Falsifier: a ledger whose rows
  record a draw after the file's modification time.
- **The real fix for undated draws** is a stamp on every ledger row, written by `run-compare` and
  `judge`. That is a writer change in `vinci/evals`, still listed as a follow-up.
