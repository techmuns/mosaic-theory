---
status: shipped
date: 2026-11-10
prs: [954]
supersedes:
superseded-by:
---

# Fix request 2, group F, RF-D7's committed rows: a decision sealed on a stale close is corrected by an APPENDED row, read by scoring, the monitor and a close. GOOGL is read at 340.65 on 2026-08-27 and VRRM at 4.44 on 2026-06-18 once the two rows are appended, after this PR merges; VRRM then matures 2026-12-15

**WHAT.**
- **The ruling (operator, 2026-11-09; approved 2026-11-10, both relayed by the coordinator: "yes
  to all").** Every committed entry is corrected by ONE rule, never by hand: the last US close
  completed at the decision moment. Corrections are APPENDED, superseding the decision by
  reference. The ledger is append-only, so no sealed row changes.
- **The rule** (`vinci/ledger/correction.py`, `rule_session`). `decided_at` is the logging
  machine's local time (`log-verdict` stamps `datetime.now()`; the operator works in India), so it
  is read as IST and set against each session's 16:00 ET close. A `decided_at` of exactly
  00:00:00 carries a date only (the hand-authored early rows) and is read at the end of that IST
  day, the latest close it could have seen. Half-day sessions are read at 16:00.
- **The row.** `EVENT_CORRECTION` (`"CORRECTION"`), id `R-<candidate_id>`, `corrects_entry_id`
  naming the decision, carrying the corrected `entry_price` and `entry_price_as_of` and a reason.
  It copies the decision's provenance as a close does, with the proposal fields cleared. The
  schema refuses a correction without its target or reason, one that names itself, one carrying
  close fields or facts, and `corrects_entry_id` on a decision or close row.
- **The readers.** Each reads the decision through `schemas.ledger.corrected`:
  - scoring (`scoring/harness.py`): the return, the dividend window and the horizon run from the
    corrected entry, and the row's note and the report name both entries;
  - the monitor (`monitor.apply_corrections`, called first in `vinci monitor`): every row below it
    sees the corrected entry, the correction rows are dropped, and the day's notes name both
    entries;
  - a close (`ledger/workflow.close_position`, code review round 0): the exit is checked against,
    and the close repeats, the corrected entry.
  - A correction naming no decision raises in every reader, as an unpairable close does. Two
    corrections of one decision raise.
- **The writer.** `vinci correct-entry ENTRY_ID --reason … [--dry-run]`. The corrected entry is
  COMPUTED, never typed: Polygon's daily bars for the name, read across the sealed session and the
  decision. It refuses, with nothing written:
  - a decision whose sealed close Polygon no longer reads within `RESTATE_TOL` (a basis moved by a
    split or a revision since);
  - a decision already corrected (before any fetch, dry run included), one the rule does not move,
    a corrected date after the decision was logged, a decision closed before the corrected entry
    date, and a blank reason.
  - Before the append it re-seeds the working store's ledger table from the committed snapshot
    (additive; an identical row is a no-op), because the export after the append writes the
    store's whole ledger over the committed file.
- **Also changed.** VRRM's maturity reads 2026-12-15 once its correction is committed, wherever
  the snapshot states it: STATE rows 38 and 32 (20), and RUNBOOKS §l (three lines, plus a check
  that `vinci ledger` lists the correction). Its scoring run is after the 12-15 US close, so
  2026-12-16 IST or later.
- **Bookkeeping asked by the coordinator.** The fix log flips every row of a merged PR to
  `fixed`: RBC-D9 and RG-D16 (#937, `d1a91f0a`); RE1-D8, D9, D12, D13, D14 and E1-D7 (#944,
  `a9c60902`); RF-D7 (#947, `81644a28`); and E2-D10, E2-D12, E2-D16 and D-D1 (#949, `7120a4cd`).
  E2-D11 and E2-D15 keep `in progress (#949)`: each row says a half is still open, and whether
  that half is its own ID is #949's stream's call. STATE row 60's title said "ALL OPEN BUT TWO",
  which was already false on `main` (15 rows fixed at `7120a4cd`); it now states the count and its
  boundary.

**WHY.** `log_verdict` sealed a stale close (fixed going forward by #947), so two committed rows
start their forward clock before the decision existed. GOOGL's BUY was decided 2026-08-28 11:24
IST, before that day's US open, and sealed the 08-14 close: nine sessions stale. VRRM's AVOID was
decided 2026-06-21 19:27 IST, a Sunday, and sealed 06-17 while 06-18 had closed (06-19 was a
market holiday): one session stale.

**HOW VERIFIED.**
- **Fail first.** The 30 tests in `tests/test_ledger_correction.py` stop at import on a clean
  `main` (`a9c60902`): `ModuleNotFoundError: No module named 'vinci.ledger.correction'`. Each
  reader and each guard was mutated out in turn, and its own test goes red:

  | Mutation | Red |
  |---|---|
  | scoring ignores the correction | `test_scoring_reads_the_decision_at_its_correction`, `test_the_corrected_horizon_runs_from_the_corrected_date` |
  | the monitor ignores it | `test_the_monitor_marks_the_decision_at_its_correction` |
  | the orphan check removed | `test_a_correction_naming_no_decision_is_refused_by_every_reader` |
  | the closed-before check removed | `test_a_decision_closed_before_its_corrected_entry_is_not_corrected` |
  | `close_position` reads the sealed entry | `test_a_close_after_a_correction_is_read_at_the_corrected_entry` |
  | the dry run's already-corrected check removed | `test_the_dry_run_on_a_corrected_decision_refuses` |

  The schema's shape guards carry a positive pin (`test_a_well_formed_correction_row_validates`)
  and one negative pin per guard (`test_a_malformed_correction_row_is_refused`,
  `test_only_a_correction_names_a_decision_it_corrects`).

- **The rule, on the corpus.** Pinned on all five committed decisions with Polygon's committed
  bars (`tests/fixtures/prices/`): GOOGL and VRRM move, IT and both SMPL decisions read their
  sealed close.
- **The real dry run** (`vinci correct-entry <id> --dry-run`, live Polygon, 2026-11-10; the
  committed ledger's sha256 `43d77c50…` before and after, and no store created):

  | Decision | Decided (IST → ET) | Sealed | The rule | Stale |
  |---|---|---|---|---:|
  | V-GOOGL | 08-28 11:24 → 08-28 01:54 | 345.90 @ 08-14 | **340.65 @ 08-27** | 9 sessions |
  | V-VRRM-screen2-20260617 | 06-21 19:27 → 06-21 09:57 | 4.71 @ 06-17 | **4.44 @ 06-18** | 1 session |
  | V-IT-screen2-20260706 | 07-21 (date only) → 07-21 14:29 | 141.06 @ 07-20 | nothing to correct | 0 |
  | V-SMPL-screen2-20260706 | 07-21 (date only) → 07-21 14:29 | 10.92 @ 07-20 | nothing to correct | 0 |
  | V-SMPL-screen2-20260729 | 08-05 14:59 → 08-05 05:29 | 11.33 @ 08-04 | nothing to correct | 0 |

- **Before and after, on a copy** (`vinci monitor --ref 2026-11-06 --out <scratch>` on a scratch
  tree and a `.backup` copy of the primary's store; the two corrections appended there by the
  real `vinci correct-entry`, exported to the scratch snapshot only; total return):

  | Row | Entry | Return to 11-06 | Excess | Horizon |
  |---|---|---|---|---|
  | V-GOOGL (BUY vs SPY, followed) | 345.90 @ 08-14 → **340.65 @ 08-27** | −17.62% → **−16.35%** | −12.56 → **−11.94** pts | 2027-03-01 → **2027-03-14** |
  | V-VRRM (AVOID vs IWM, screen) | 4.71 @ 06-17 → **4.44 @ 06-18** | −53.50% → **−50.68%** | −48.16 → **−43.50** pts | 2026-12-14 → **2026-12-15** |
  | V-IT, V-SMPL ×2 | unchanged | unchanged | unchanged | unchanged |

  - **The spread** (the monitor's screen-origin BUY−AVOID diagnostic, nothing resolved):
    **+71.55 → +66.89 pts**, all of it VRRM's (the BUY mean excess is +23.39 both ways; GOOGL is
    followed-origin). The price-return spread beside it moves +71.54 → +66.88. The scoring
    report's spread is undefined both ways, as no row has resolved.
  - Both corrected days carry a note naming the sealed and the corrected entry.
  - Live requests in that run: 2, both Polygon (the two corrections' daily bars).

**THE APPEND IS A FOLLOW-UP, AFTER THIS PR MERGES** (the coordinator's call, 2026-11-10; the
operator may override). Two facts found while building this changed the approved order (append
first, then merge):
- `main`'s `LedgerEntry` refuses `event: "CORRECTION"` ("unknown ledger event"). Between an append
  and this PR's merge, `run-monthly` (VRRM's rehearsal), `log-verdict` and `close-position` on
  `main` would fail reading the primary's store.
- The store's triggers forbid an UPDATE or DELETE on the ledger, and the rule is one correction
  per decision. A review finding on the row's shape could not be applied to rows already written.

So nothing is appended here. Once this PR merges, the follow-up runs `vinci correct-entry V-GOOGL`
and `vinci correct-entry V-VRRM-screen2-20260617`, each with its reason, from a clean `main`
worktree linked to the primary's `data/vinci.db` (RUNBOOKS §l's wiring). That is the one write to
the primary's store this stream makes. Exactly what it writes:
1. **The re-seed.** The primary's store held 1 ledger row on 2026-11-10 (VRRM's decision,
   byte-identical to the committed line; the file's sha256 `3106433f…`), against 7 committed. The
   command first loads the other six committed rows (`C-IT-screen2-20260706`,
   `C-SMPL-screen2-20260706`, `V-GOOGL`, `V-IT-screen2-20260706`, `V-SMPL-screen2-20260706`,
   `V-SMPL-screen2-20260729`) into its ledger table, as they are committed. `run_monthly`
   re-seeds every snapshot table into that store before scoring anyway.
2. **The two rows.** `R-GOOGL` (corrects `V-GOOGL`: 340.65 on 2026-08-27) and
   `R-VRRM-screen2-20260617` (corrects `V-VRRM-screen2-20260617`: 4.44 on 2026-06-18), each
   carrying the decision's provenance, the reason, and the time of the append.
3. **The export.** `data/snapshots/decision_ledger.jsonl` goes from 7 rows to 9: the 7 committed
   lines byte-identical, plus the two. On the scratch copy above, exactly that: 9 rows, the 7
   committed lines present byte-identical, the export sorted by `entry_id`.
4. **The record of it.** The sha256 of `data/vinci.db` before and after, and the snapshot
   committed as its own artifact-only PR, with no code.

Until that PR lands, the committed ledger has no correction: scoring and the monitor read the
sealed entries, and VRRM's sealed entry matures 2026-12-14. The order is this PR, then the append's
artifact PR, then the rehearsal (STATE row 38, by 2026-12-07).

**THE WEB IS ITS OWN PR, PREVIEWED FIRST** (the coordinator's call, 2026-11-10). The ledger page
(`frontend/lib/snapshots.js`) and `frontend/build.py`'s card join skip a CORRECTION row, so there
is no phantom entry, but they never apply it. Once the correction is committed they would show
GOOGL at 345.90 @ 08-14 and VRRM at 4.71 @ 06-17, resolving on 2026-12-14, while scoring and the
monitor read 12-15. The fix is a data-only twin of `monitor.apply_corrections`, pinned against it
on the committed ledger. It changes what the ledger page renders, so the PREVIEW RULE applies: the
two cards are rendered from a fixture, collapsed and force-open, and the build STOPS for the
operator's approval. It is split from this PR so this one is not held behind that stop.

**BOUNDARY.**
- The five decisions and two closes are every row of `data/snapshots/decision_ledger.jsonl` at
  `a9c60902` and at `7120a4cd` (7 rows, the same file).
- "Stale" counts the sessions Polygon's daily bars hold after the sealed one, up to and including
  the rule's session.
- Returns, excess and spread: the monitor at `--ref 2026-11-06` on the shared grouped-daily
  cache, total return, each row against its committed benchmark assignment; the spread is the
  screen-origin rows only, BUY mean excess minus AVOID mean excess, in percentage points.
- The fix-log count: all 178 rows of `docs/fix-log-teamnostra-2.md` by their Status cell, at
  `7120a4cd` plus this PR's flips (28 fixed, 147 open, 2 in progress, 1 disagree; at `7120a4cd`
  alone: 15 fixed, 15 in progress, 147 open, 1 disagree).
- Tests: `tests/test_ledger_correction.py`, 30 tests, on this branch.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The follow-up's re-seed will write more than two rows into a store that is behind the
  snapshot.** The primary's store held 1 ledger row (VRRM's, byte-identical to the committed one)
  against 7 committed on 2026-11-10. `correct-entry` adds the other six before its append. `run_monthly`, the run that
  scores VRRM, already re-seeds every snapshot table into that store before scoring, so this is a
  subset of what the rehearsal does.
- **A correction applies at every `--ref`** (review round 0, finding 5, DISMISSED). Neither reader
  filters decisions by date (only closes, by their exit date), and a correction is a ruling on how
  a decision is read, not a market event. A re-cut dated before the correction therefore reads
  the corrected entry. Falsifier: a re-cut whose purpose is to reproduce the stale reading.
- **One correction per decision, append-only.** A wrong correction cannot be corrected again.
  That is why the entry is computed by the rule and the writer refuses so much.
