---
status: open
date: 2026-11-10
prs: [947]
supersedes:
superseded-by:
---

# Fix request 2, group F, the seal (RF-D7): `log_verdict` refuses a close older than its staleness bound, going forward. GOOGL's sealed row is untouched, and how it is read is the operator's ruling, with four options set out here

**WHAT.**
- **The fault.** `log_verdict` asks the store for the latest close on or before the reference
  date with `staleness_days`, and `Store.close_as_of` marks an older bar STALE. But the seal
  checked `is_known`, which is TRUE for a stale value, so `staleness_days` had no effect.
  - A close 31 days old was sealed: decided 2026-10-31, entry 20.0 as of 2026-09-30.
  - The row's forward clock is scored from `entry_price_as_of` (`scoring/harness.py`), so it
    started 31 days before the decision.
- **The fix.** The seal now requires the close to be current (`is_evaluable`: PRESENT, inside
  the bound). Otherwise it refuses before the append, naming the close, its age and the bound,
  and telling the operator to refresh EOD bars and log again. The bound is the CLI's own
  `price_staleness_days` (5 calendar days), so a Friday close still seals a Monday or Wednesday
  decision.
  - **The close is held to the decision as well.** The bound above is measured from the reference
    date, which the CLI takes from `--ref`. The code review (round 0) found that a `--ref` set back
    to an old close's own date made that close "fresh" while `decided_at` was today: GOOGL's 08-14
    close sealed on 2026-11-10, 88 days before the decision. That is RF-D7 through another input,
    and a door to deciding with hindsight. A close more than the bound before `decided_at`'s date
    is now refused too.
- **Not changed.** The scorer still starts the clock at `entry_price_as_of`. Starting it at the
  decision date instead was the other option the brief named. It was not taken: a return measured
  from a stale price with a clock from a later date measures a window nobody held. A seal that is
  current makes the two dates the same.
- **Test fixture.** `tests/test_stated_limit.py` built its close from a hand-rolled class with
  three attributes. It now builds the real `DataField` the store returns, so a gate that reads a
  field the stub lacked cannot pass on the stub.

**WHY.** These are TeamNostra's fix request 2 (document 15), order 4, prices. The coordinator's
record found RF-D7 live on the committed ledger (`docs/records/2026-11-09-teamnostra-fix-request-2.md`
§4): GOOGL's BUY (`V-GOOGL`) was decided 2026-08-28 on the 2026-08-14 close.

**HOW VERIFIED.**
- **The defect, reproduced first.** `tests/test_seal_is_current.py` fails 3 of 9 on a clean
  checkout of `main` (`6fbbb4a2`), each with "DID NOT RAISE": the audit's 31-day case, GOOGL's
  14-day case, and the back-dated `--ref`. All 9 pass here. The negative pins pass on both: a close
  5 days old, and a verdict logged the morning after its reference close.
- **Two ledger tests** (`tests/test_ledger.py`) logged on the 2026-07-13 pivot day against a
  2026-06-12 close, 31 days back. They now seal a close from that week; the pins they hold, on
  dispositions and anti-anchoring, are unchanged.
- **On the corpus.** Each of the five committed decisions is sealed again in a scratch store, at
  its own entry date and its own `decided_at`. The ledger itself is never touched. The gaps are
  IT 1, SMPL 1, SMPL 1, VRRM 4 and GOOGL 14 days. The first four seal; GOOGL's is refused. So the
  rule refuses exactly the one row the coordinator found, and no other.
- **The edge.** A close exactly 5 days old seals (a Friday close for a Wednesday decision).
- ruff and `mypy --strict vinci` are clean, and the full offline suite passes (`bin/commit`).

**GOOGL'S SEALED ROW: THE OPERATOR'S RULING, NOT MADE HERE.** The ledger is append-only, and no
code here moves the row.
- **The facts.** These are Polygon closes, read 2026-11-10 from the dry run's cached aggregates.
  - GOOGL was sealed at **345.90** (2026-08-14). The decision was logged 2026-08-28 11:24 IST,
    before that day's US open.
  - The last session completed before it was **2026-08-27**: GOOGL **340.65**, SPY **771.10**,
    against SPY's 776.34 on 08-14.
  - So the record's window includes 14 days the position was not held. Over them GOOGL fell
    1.52% and SPY 0.67%: about −0.85 points of excess charged to the BUY before it existed.
  - The horizon is 199 days: from 08-14 it is 2027-03-01, and from 08-27 it would be 2027-03-14.
  - **Where it lands.** GOOGL is followed-origin, in the quality sleeve, and outside the primary
    screen-origin BUY−AVOID spread. The choice moves the quality sleeve's curve only.
- **The options.**
  1. **Leave it, disclosed.** The row is scored as sealed, with a note saying its clock starts 14
     days before the decision.
     - Cost: a note, and no code on the scoring path.
     - Falsifier of "it doesn't matter": the quality curve's sign turns on this one row.
  2. **Rule the entry session, the row unchanged.** A committed ruling for `V-GOOGL` names the
     entry session 2026-08-27. Scoring reads that session's close from the store, on the store's
     basis, and starts the horizon there. The precedent is the benchmark ruling (`ruled_on`,
     `ruling`, keyed to one decision).
     - Cost: a small harness change on the decision path, with its tests, built only on the
       ruling.
  3. **Close it and log again.** Append a CLOSE for `V-GOOGL` naming RF-D7, then log a new
     decision.
     - The new decision would seal a CURRENT close, not 08-27's: the ledger cannot backdate.
     - It cannot be logged under today's id scheme. A decision's id is `V-{candidate_id}`, and a
       followed name's candidate id is its ticker, so the new row is `V-GOOGL` again, and
       `decision_ledger.entry_id` is the primary key: the append fails as a duplicate even after
       the CLOSE. Option 3 needs a new id scheme on the write path first.
     - Under the 2026-08-12 ruling a close is not a retraction, so the original call still runs to
       its horizon. Two GOOGL decisions would sit in the quality curve unless the first is also
       ruled out.
  4. **Void it by ruling.** Scoring skips `V-GOOGL` with a note. The quality sleeve loses its only
     followed-origin BUY.
- **Recommended: option 1 now, option 2 if the quality curve is to measure GOOGL's decision at
  its own price.** Option 1 puts nothing new on the scoring path before VRRM is scored
  (2026-12-14). Option 2 is the closest reading of the decision without rewriting the row. Build it
  after the 12-14 scoring, on the ruling.

**THE OPERATOR'S RULING (2026-11-09, relayed by the coordinator) SUPERSEDES THE FOUR OPTIONS
ABOVE.**
- **The rule.** Correct every affected entry by ONE rule; never hand-fix GOOGL alone. An entry's
  corrected price is the last US close completed at the decision moment, and a decision made after
  a day's close uses that close. Corrections are APPENDED as entries that supersede by reference;
  scoring reads the corrected entry and the originals are kept. Do it as a dry run first, and
  STOP for approval before any append.
- **How a decision time is read.** `decided_at` is the logging machine's local time:
  `log-verdict` stamps `datetime.now()`, and the operator works in India, so it is read as IST and
  converted to US Eastern. A `decided_at` of exactly 00:00:00 carries a date only (the hand-authored
  early rows), and is read as made during that IST day, at its end: the latest close it could have
  seen.
- **The dry run on every committed decision.** These are Polygon closes, from a `.backup` copy of
  the primary's store and this build's cached aggregates; nothing was written.

  | Entry | Sealed | decided_at (IST → ET) | The rule's close | Sessions stale |
  |---|---|---|---|---:|
  | V-GOOGL | 345.90, 2026-08-14 | 08-28 11:24 → 08-28 01:54 | **340.65, 2026-08-27** | 9 |
  | V-VRRM-screen2-20260617 | 4.71, 2026-06-17 | 06-21 19:27 → 06-21 09:57 | **4.44, 2026-06-18** | 1 (06-19 a holiday) |
  | V-IT-screen2-20260706 | 141.06, 2026-07-20 | 07-21, date only | 141.06, 2026-07-20 | 0 |
  | V-SMPL-screen2-20260706 | 10.92, 2026-07-20 | 07-21, date only | 10.92, 2026-07-20 | 0 |
  | V-SMPL-screen2-20260729 | 11.33, 2026-08-04 | 08-05 14:59 → 08-05 05:29 | 11.33, 2026-08-04 | 0 |

  The coordinator's first read had SMPL 3 and IT 1 sessions stale. Those came from the two CLOSE
  rows' `decided_at` (C-SMPL 07-24, C-IT 07-22), which are exits, not decisions.
- **The effect, to date.** `vinci monitor --out` on the 2026-11-06 session, total return, run on
  the committed ledger and on a scratch copy holding the two corrected entries:
  - **GOOGL:** −17.62% → −16.35%, and its excess vs SPY −12.56 → −11.94 points.
  - **VRRM:** −53.50% → −50.68%, and its excess vs IWM −48.16 → −43.50 points.
  - **The spread:** the screen-origin BUY−AVOID diagnostic is +71.55 → +66.89 points, all of it
    VRRM's. GOOGL is followed-origin and outside it; it moves the quality sleeve's curve only.
  - **The scoring report:** no row has resolved, so its spread is undefined both ways.
- **What a correction moves besides the price.** The horizon runs from the entry date. A corrected
  VRRM matures on **2026-12-15** (06-18 + 180), not 12-14, so it is scored after the 12-15 close.
  A corrected GOOGL matures on 2027-03-14, not 2027-03-01.
- **Going forward.** This PR refuses a close more than 5 calendar days old. That refuses GOOGL's
  case, but it would still have sealed VRRM's: 4 days, 1 session stale, with the 06-18 close
  existing. To refuse every close the correction rule would correct, the seal needs the market's
  sessions at the decision moment. One Polygon request at `log-verdict` would show whether a later
  session had closed. That is proposed, not built.
- **STOPPED.** No correction is appended. The append mechanism, a correction entry that
  supersedes its decision by `entry_id` and that scoring and the monitor read, is a decision-path
  build of its own. It waits on the operator's approval of this dry run, including the call on
  VRRM's one-session correction, which moves the spread 4.66 points and its maturity by a day.

**BOUNDARY.**
- **Ledger:** `data/snapshots/decision_ledger.jsonl` at `6fbbb4a2`: 7 rows, of which 5 are
  decisions and 2 are closes.
- **Gaps:** `decided_at` minus `entry_price_as_of`, in calendar days.
- **Prices:** Polygon `adjusted=true` daily aggregates for GOOGL and SPY over 2026-06-10 →
  2026-11-06, as cached by this build's monitor dry run on 2026-11-10. No split falls in the window
  (Polygon reference, read 2026-11-09).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A stale store refuses every seal** until it is refreshed. That is the point: a decision logged
  on a two-week-old store records a price nobody traded at.
- **`--ref` can no longer back-date a decision** by more than the bound. A verdict decided days
  ago and logged late must be logged within 5 days of its close. A longer back-date is refused:
  it would put a price nobody acted on beside hindsight. If one is ever needed, it is the
  operator's ruling, not a flag.
- **A halted name cannot be logged** while its last close is older than the bound. A verdict on
  one would need the operator to log it deliberately (a fresher bar, or a later ruling). No
  committed row is in that state.
- **The 5-day bound is in calendar days.** It admits a close up to two sessions old over a
  weekend: a Thursday close for a Monday decision, with Friday traded, is 4 days and seals. A
  rule tied to the session calendar would need the market's calendar at seal time, which the store
  holds only as current as its last refresh. Measured on the corpus: no committed seal is more
  than 1 session behind except GOOGL's.
