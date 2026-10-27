---
id:
status: shipped
date: 2026-10-27
prs: [820]
supersedes:
superseded-by:
---

# A ledger row is scored on its horizon session's close: it resolves only once the benchmark's bar for that session is stored, and a resolved row whose name stopped trading raises instead of exiting on its last trade

**WHAT.** `vinci/scoring/harness.py` `score_ledger` gains two rules. Both are set by face validity,
and no forward return was read to set either.

1. **A row resolves only once the store holds a benchmark bar dated on or after its horizon.** The
   condition is `as_of >= horizon` AND the newest benchmark bar on or before `as_of` is dated on or
   after the horizon. Until then the row is pending, and the report names it, its horizon and the
   bar it waits on (`ScoreReport.row_notes`, printed under the pending count in
   `scoring_report.md`; the same text is on the score as `VerdictScore.note`). The bar is bounded by
   `as_of`: a bar stored after the scoring date has not landed in the book being scored, so a
   re-cut says what a run on that day said. A weekend horizon resolves when Monday's bar lands, and
   its exit is still Friday's close.
2. **The exit stays the name's last bar on or before the horizon.** If the benchmark has a later
   session in the same window, the name stopped trading. A RESOLVED row raises `StaleExitError`,
   naming the row, the name's last bar and the benchmark's session. An UNRESOLVED row's interim mark
   carries a note and does not raise, because unresolved rows never enter the spread.

Not touched: the ledger, the verdict mapping, the benchmark-sealing guard and every threshold. Two
existing guards are gated on `resolved` (`BenchmarkMismatchError`, `TotalReturnUnknownError`). They
now fire when a row resolves under rule 1. That is the moment its number would count, which is the
condition each one states.

**WHY.** Record `2026-10-27-vrrm-inputs-before-maturity`, FOUND 2. `resolved` was
`as_of >= horizon_date`, and the exit was `bar_on_or_before(name_bars, scoring_date)`: whatever bar
was last, however old. `ingest_prices` reads the empty grouped-daily of a session that has not
closed as a holiday. So a `run-monthly` on 2026-12-14 in India, before the US close, would resolve
VRRM (`V-VRRM-screen2-20260617`, the first row the ledger resolves) on the 2026-12-11 close. The
next run would correct it, but a scoring report committed in between would publish a wrong first
resolved number. The worse case is a halted or delisted name that silently exits at its last trade.
For an AVOID_TERMINAL row, that is the very event the call predicts.

**THE OTHER SURFACES THAT MARK A LEDGER ROW (rule 3).**

- **The monitor** (`vinci monitor`; `cli._cmd_monitor`, `monitor.position_row`). *Rule 1 already
  holds, by construction.* The mark date is the latest session whose grouped-daily is non-empty
  (`monitor.session_on_or_before`), a leg whose benchmark is missing from that session raises, and
  `resolved = current_date >= horizon_date`. A run before the 12-14 US close therefore marks 12-11,
  and VRRM reads unresolved. *Rule 2 is stricter there:* a name missing from the session raises
  for every row, resolved or not ("no position bar … refusing to guess a price"), so the monitor
  never marks a stale bar. *Where it differs:* the monitor marks every row to the latest session,
  past the horizon too (FOUND 1). Not changed here.
- **The follow-basket comparator** (`baseline.basket_return`) marks follow-list members, not ledger
  rows. Each member still exits on `bar_on_or_before(bars, end)`, however old (FOUND 2).
- **Not ledger surfaces:** `vinci/calls/score.py` scores posted calls and already trims both legs to
  the common last bar. `vinci/themes/forward.py` measures theme baskets. On the web,
  `frontend/lib/snapshots.js` computes only the horizon date and the days to it, and
  `decision-log.js` prints the monitor's mark.

**HOW VERIFIED.**

- *Fail first.* `tests/test_scoring_horizon_close.py` has 11 tests, run on frozen real bars:
  `tests/fixtures/horizon_close/vrrm_iwm_bars.jsonl`, VRRM's and IWM's Polygon bars for
  2026-06-15 → 2026-10-16, cut from `tests/fixtures/prices/` at 987d2b4e. That file is rewritten by
  the weekly screen, which is why the cut is frozen here. The row is VRRM's real one, read from the
  ledger. Where a rule needs a horizon inside the window, the row's horizon is shortened on a
  `model_copy`. On main's logic, with only the new error class stubbed in, 6 of the first 9 were
  red and the 3 negative pins green. The pins, positive and negative per rule:
  - rule 1: pending as of 2026-12-14 on bars ending 2026-10-16, with the report line naming the row
    and both dates (+). Resolves once the benchmark has the horizon's own session, 2026-10-14,
    exiting on that close (−). A Saturday horizon (115 days → 2026-10-10) is still pending on the
    Sunday, although Monday's bar is stored (+). It resolves on the Monday and exits on Friday's
    close (−).
  - rule 2: VRRM cut at 2026-09-15 under a 2026-10-14 horizon raises `StaleExitError`, and the
    message names the row, 2026-09-15 and 2026-10-14 (+). With both series on the horizon session,
    the row resolves with no note (−). The same cut on the real 180-day row, scored as of
    2026-10-16, is marked on the 09-15 close with a note naming both dates, and does not raise (+).
    With no gap there is no note (−).
  - review round 0 (`/code-review high`), 2 pins red before their fix: a followed row's note says
    it is outside the screen-origin pending count, which a screen row's does not; and a row both
    awaiting its horizon close and carrying a gap says scoring stops when it resolves, not "by" a
    horizon already passed.
- *Mutation.* There were 9 mutants, and every one turned at least one pin red:
  - rule 1 reverted (4 red);
  - the `as_of` bound dropped, so the newest stored benchmark bar is read (1 red);
  - the pending note dropped (4 red);
  - a resolved halt that does not raise (1 red);
  - an unresolved halt that raises (2 red);
  - the interim note dropped (2 red);
  - the gap check removed (3 red);
  - the exit read at `as_of` instead of the horizon (2 red);
  - a followed row's note without its scope (1 red).

  `PYTHONDONTWRITEBYTECODE=1` was set and `__pycache__` cleared per mutant, and the restored file
  was byte-identical.
- *The rehearsal* followed `docs/RUNBOOKS.md` §l, as #818 did, on a COPY of the primary checkout's
  store. `data/vinci.db` (bars through 2026-08-05) and `data/cache` were APFS clones in a scratch
  data dir, with a copy of `data/snapshots`. `orchestrator.run_monthly(as_of=2026-10-26)` ran on
  this branch's code with the primary's `.env`. It took 13 s, and every grouped-daily read was a
  cache hit from #818's refresh earlier the same day. It seeded the 7 committed ledger rows, and
  left 91 VRRM and 91 IWM bars in [2026-06-17, 2026-10-26]. Five scenarios were each scored on a
  fresh clone of that store. BEFORE is `origin/main` 64f91b2a, exported by `git archive`; AFTER is
  this branch. Both used Tiingo dividends, with the follow baskets wired as `run-monthly` wires them.

  | scenario | BEFORE (main) | AFTER (this branch) |
  |---|---|---|
  | S1 today, as of 2026-10-26 | 0 resolved, 4 pending; VRRM interim −34.39% total, IWM −4.20% | identical: 5 of 5 decisions equal on every number; the report is byte-identical |
  | S2 as of 2026-12-14, bars end 2026-10-26 | VRRM **RESOLVED** on the 10-26 close ($3.09, −34.39%): 1 AVOID resolved, 3 pending. The report prints "AVOID mean return -34.4%", AVOID hit-rate +100.0% and "AVOIDs kept falling: True", seven lines in all, on a row whose horizon session had not closed | VRRM **pending** (0 resolved, 4 pending); the report prints "V-VRRM-screen2-20260617 (VRRM) is PENDING, not resolved: its horizon 2026-12-14 has passed, but the benchmark's last bar on or before 2026-12-14 is 2026-10-26 — awaiting the horizon session's close." The other 4 decisions are equal on every number |
  | S3 VRRM's bars cut after 2026-09-15, real 180-day row, as of 2026-10-26 | interim on the 09-15 close (−24.84%), silently | the same numbers, plus the note "its last bar on or before 2026-10-26 is 2026-09-15, but the benchmark has a session on 2026-10-26 — this interim mark is on that stale close, and feeds no number. If the gap is still there when the row resolves (its horizon is 2026-12-14), scoring stops." on the score and in the report; no raise |
  | S4 VRRM's row with its horizon shortened to 119 days (2026-10-14), bars through the horizon, as of 2026-10-26 | resolved: −37.58% total, IWM −6.14% | identical; the report is byte-identical |
  | S5 S4 with VRRM's bars cut after 2026-09-15 | **resolved on the stale 09-15 close**: −24.84%, against the −37.58% the name had actually fallen by the horizon | **raises** `StaleExitError`: "…its last bar on or before 2026-10-14 is 2026-09-15, but the benchmark has a session on 2026-10-14 — the name stopped trading before its horizon 2026-10-14, and the row has RESOLVED…" |

  `decision_ledger.jsonl` hashed `43d77c50…` before and after, in this worktree, in the primary
  checkout and in the scratch copy. The primary's `data/vinci.db` was not opened (mtime still
  2026-08-06), and the primary's `data/snapshots` is unchanged (`git status` clean).
- *Session alignment on the copy.* Each of the 5 decisions, in [entry, 2026-10-26], has exactly
  the sessions IWM has, with no gap in either direction. VRRM has 91, SMPL 70 and 59, IT 70, and
  GOOGL 51. So no live row trips rule 2 today.
- *Suite.* `pytest -m "not network"` on this branch (base 64f91b2a): 6,935 passed, 533 skipped,
  38 deselected; ruff and `mypy --strict vinci` clean.

**FOUND, NOT FIXED.**

1. **The monitor marks a row past its horizon to the latest close.** `position_row` takes the
   session the monitor runs on, so from 2026-12-14 VRRM's monitor row reads RESOLVED with its
   return through whatever day the monitor ran. The scoring report scores it on the 12-14 close.
   The web's decision log prints that monitor mark, so from 12-15 the two surfaces will give
   different numbers for the same resolved row. A fix would mark a row whose horizon has passed on
   `session_on_or_before(horizon_date)`, which the monitor already has. That changes the monitor's
   snapshot semantics, so it is proposed separately.
2. **The follow-basket comparator has no stale-exit check.** A follow-list member that stops trading
   exits the equal-weight basket at its last bar. The basket is the quality sleeve's kill test, not
   the primary spread.
3. **The reverse of rule 2 is not guarded.** If the benchmark were missing a session the name has,
   the benchmark leg would end a session earlier than the name's. This was measured at 0 sessions
   on the copy (above).
4. **A resolved row with no name bar after its entry stays pending, unchanged.** It is the existing
   no-forward-price branch: no number is published and nothing raises, but no note names it
   either (review round 0, not applied: outside this brief's two rules).

**OPEN (operator).** The exit for a ledger name that stops trading before its horizon is not ruled,
and no delisting-return rule was invented. `StaleExitError` stops the scoring run until the operator
rules. This is recorded in STATE.md §5.0 row 32 item (21).

**BOUNDARY.**
- Fixture: VRRM's and IWM's bars over 2026-06-15 → 2026-10-16, 87 sessions each (the same
  sessions), cut at 987d2b4e.
- Tests and mutants: `tests/test_scoring_horizon_close.py` on this branch.
- Rehearsal: the primary's store copied 2026-10-27, refreshed through 2026-10-26. The 7 committed
  ledger rows are 5 decisions and 2 closes; the scores list the 5 decisions, and "pending" counts
  the 4 screen-origin ones. Bar counts are sessions in [entry, 2026-10-26]. Returns are total
  return, from Tiingo's dividends read 2026-10-27; VRRM paid none in the window.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- An early run resolves nothing. Run on 2026-12-14 IST before the close, VRRM is pending, and the
  report says so. Row 32 item (20)'s advice to score on 2026-12-15 IST or later stands.
- A benchmark that stops refreshing holds every matured row pending. That failure is loud: each row
  is named.
- Rule 2 compares one session. A thinly traded name with no bar on the horizon's session (a day with
  no trade) would raise as though it had stopped trading. It fails loud, and the operator rules. The
  falsifier: a `StaleExitError` on a name that traded again within days. No live row has a missing
  session today.
