---
id: 2026-11-13-screen-basket-baseline-preregistered
status: recorded
date: 2026-11-13
prs: []
supersedes:
superseded-by:
---

# PRE-REGISTERED before any reading: the $0 screen-basket baseline measures each committed screen run's admitted names, equal-weight from the next close, against the names the same run rejected (the control, read first) and against each name's cap-band benchmark, at 30, 90 and 180 days, each horizon printed only once it has fully passed

**WHAT.** Item 2 of #1004 (operator, 2026-11-13: *"how to do it reliably?"*; B's design in
issuecomment-6847522000, A's three additions in -6847633111, agreed in -6848173835). This record
fixes the metric, the populations, the horizons and the rules BEFORE the module computes its first
reading. It is committed ahead of the code that reads a price; a reading that departs from it is a
new pre-registration, never an edit of this one.

**THE METRIC.**
1. **Cohorts.** One cohort per screen run date in `data/snapshots/screen_runs/`. A date with more
   than one run is one cohort: its LATEST run (the highest `-NN`), because that is the screen's
   answer that day; the earlier runs are named as collapsed. Today that collapses
   `2026-07-29-01` and `-02` into `-03`. Cohorts are never pooled: each prints on its own line,
   and no figure averages across cohorts whose windows overlap.
2. **Each run file is read from the commit that added it** (`git log --diff-filter=A`), and its
   sha256 is printed beside the cohort with that commit. A run records no code commit of its own,
   so the adding commit is the nearest stated commit for "the screen as it was at the run" — said
   as that, never as more.
3. **Populations, from the candidate grain only.** ADMITTED: rows whose `admitted` gate PASSED
   (the names handed to the candidate set). REJECTED: rows that were not admitted and whose
   outcome is FAIL. Rows not admitted and NOT_EVALUATED are neither — counted, not scored.
   Universe-grain drops (out of band, no price, …) never reached the gates and are in neither.
4. **Entry.** Each name's close on the first session after the run's `reference_date` (the next
   close), equal weight. A name with no bar on that session has no entry: counted and named, not
   scored.
5. **Exit at horizon h ∈ {30, 90, 180} calendar days.** The name's last bar on or before
   entry + h. A name whose last bar is before the session the market traded on (delisted or
   halted) is scored TO ITS LAST TRADE and named — never dropped.
6. **Benchmark: the cap band the ledger assigns** (`vinci.monitor.benchmark_for_cap`) on the cap
   that decided the name's membership (`deciding_cap`), over the same two sessions.
7. **Return basis: PRICE return,** names and benchmarks alike. The ledger scores total return
   (ruling 2026-10-26), but the dividends of ~1,800 names a run are not in any cache, and fetching
   them is a vendor pull this $0 build does not make. Said on every reading.
8. **Readings, in this order:**
   1. **the control** — admitted mean return minus rejected mean return, with a 95% interval
      (Welch's standard error, normal approximation), N per leg;
   2. admitted mean excess over each name's own benchmark, with a 95% interval
      (mean ± 1.96 × sd / √N), N.
9. **A horizon prints only once it has fully passed:** entry + h on or before the scoring date
   AND on or before the last session the price source holds. Otherwise the line says when it
   passes, and nothing else.
10. **Split basis.** Cached bars are adjusted as of the day each was fetched, so a split between
    two fetches leaves a step in the series. A name with a session-to-session close ratio at or
    beyond 1.9 or 1/1.9 inside its window is set apart, named and counted, and not scored: its
    basis cannot be checked at $0. A genuine one-day move that large is set apart with it.

**NEVER USED FOR TUNING.** The module sits in the outcome layer (`vinci/scoring/`), and
`tests/test_outcome_import_fences.py` names it: the screen, the cohort split, the triggers and the
scenario records cannot reach it by any import path. Nothing reads these readings back into a
gate, threshold or weight — retention's own rule (`vinci/screens/retention.py`): a reading may
falsify a design, and any parameter chosen after looking is validated forward.

**WHY.** The ledger holds 5 decisions and its first resolved read is 2027-01-16. The screen has
run 8 times since 2026-07-29 and its admitted and rejected names are committed, so whether the
screen selects anything is measurable now, at $0, with N in the hundreds per cohort — a question
the ledger cannot answer for years.

**BOUNDARY.** "8 times": the `.jsonl` files in `data/snapshots/screen_runs/` at `01ab6923`, on 6
reference dates. "~1,800 names a run": candidate-grain rows per run file, 1,780 to 2,126 at
`01ab6923`. "5 decisions": decision rows in `data/snapshots/decision_ledger.jsonl` at `01ab6923`.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Price return understates a dividend payer's total return on
both legs alike. The adding commit is not proof of the code the screen ran on. One cohort is
noise: the interval is printed so it is read as such.
