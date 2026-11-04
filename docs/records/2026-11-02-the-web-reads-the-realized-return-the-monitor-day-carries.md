---
id: 2026-11-02-the-web-reads-the-realized-return-the-monitor-day-carries
status: open
date: 2026-11-02
prs: []
supersedes:
superseded-by:
---

# The web's realized return is the one the monitor day carries, never a quotient of its own (closes STATE §5.0 row 40)

**WHAT.** `frontend/lib/snapshots.js` (`_loadLedger`) derived a closed position's realized return
as `exit_price / entry_price − 1`, from the ledger's two frozen prices.
- `vinci.monitor.pair_closes` dropped that formula on 2026-10-29 (#855). The sealed entry sits on
  the ENTRY date's split basis and the exit on its own, so a split between them read a flat
  2-for-1 as −50%.
- The python side puts the entry on the exit's basis through Polygon's splits reference. The
  browser has no source for that.
- The 2026-10-29 record named this as its accepted cost 2 (`docs/records/2026-10-29-one-split-
  basis-for-every-scored-return.md`) and opened row 40 for it.

Now the web reads the `realized` row of the LATEST committed monitor day by its `close_id`.
- A close no monitor day carries yet shows NO return, never one computed in the browser.
- No monitor history committed also shows none.
- A row whose `close_id` matches but whose `entry_id` names another position is a broken pair,
  and shows none.
- The close's own facts (date, exit price, reason) are untouched. Both renderers, the decision
  log and the dossier card, already print the return only when it is not null.

Row 40 is closed: its §5.0 row is deleted. It was opened on 2026-10-29, after §5 froze, so there
is no archive entry to strike.

**WHY.** One definition of the realized return, the one that has read the splits. A second
derivation in the browser was the mixed-basis number row 40 recorded. Fail loud: an unread
return is shown as none, never as a guess.

**HOW VERIFIED.**
- **`tests/test_web_realized_return.py`** executes the real module. Node imports `snapshots.js`
  with `fetch` stubbed onto the committed `data/snapshots/decision_ledger.jsonl` and
  `frontend/monitor/`, and reads `getLedger()` as both views do.
  - **Red on main's `snapshots.js`** (a7e1214b; unchanged through cfedcb39):
    - **Across a REAL split.** MNST split 2-for-1 on 2026-08-11 (Polygon's splits reference,
      frozen with MNST's two grouped-daily closes in `tests/fixtures/realized_split/MNST.json`).
      A position sealed at the 2026-08-07 close as printed (90.36) closes at 45.98 on 2026-08-12;
      it is the committed SMPL decision and close retargeted. The real `pair_closes` puts the
      entry on the exit's basis (45.18) and derives +1.77%; the monitor day carries that row.
      Main read −49.11%; the page now shows +1.77%.
    - **Across a split, constructed.** The committed SMPL close, its sealed entry put on a
      pre-split basis (21.84, a 2-for-1 of 10.92). Main read −51.8%; the monitor day's row reads
      −3.57%.
    - **Not yet on a monitor day.** The latest day set to 2026-07-20, before both closes. Main
      computed IT 0 and SMPL −3.57%; now none, with the close's exit price kept.
    - **No monitor history.** Main computed both; now none.
  - **The guard:** a realized row naming another position is not read. Red on main, and red
    with the `entry_id` check removed.
  - **The fence, green on both:** on the committed files, IT and SMPL show exactly the
    latest monitor day's rows (2026-11-02 on the merged tree).
- **Real run** on the tree merged with main at cfedcb39 (latest monitor day 2026-11-02): every
  closed position through each version of `snapshots.js`, on the committed files and with the
  MNST close above overlaid:
  ```
  main,   committed:  IT   sealed 141.06  exit 141.06 (2026-07-21)  realized 0.00%
                      SMPL sealed 10.92   exit 10.53  (2026-07-22)  realized -3.57%
  main,   + MNST:     MNST sealed 90.36   exit 45.98  (2026-08-12)  realized -49.11%
  branch, committed:  IT 0.00%, SMPL -3.57% (identical)
  branch, + MNST:     MNST sealed 90.36   exit 45.98  (2026-08-12)  realized 1.77%
  ```
  No committed close spans a split, so the change moves no position on the deployed page today.
  The only move is the split case, −49.11% → +1.77%.
- `tests/test_sleeves.py::test_the_decision_log_page_actually_renders` still renders the real
  decision log over the committed snapshots.
- One existing pin's message said the return "is derived here". It now says it is the monitor
  day's row (`tests/test_record_legibility.py`).
- No extraction module changes, so no extraction-version row: `snapshots.js` is not among the
  drift test's watched modules, and no dossier output moves.

**BOUNDARY.**
- **Code:** branch `claude/p2d-d5-realized-return` from `origin/main` a7e1214b, merged with
  main at cfedcb39 (#884–#889) on 2026-11-04.
- **Data:** the committed ledger (7 rows: 2 closes, IT and SMPL) and the committed monitor
  history (9 days, latest 2026-11-02), read 2026-11-04. MNST's split row and two closes come from
  Polygon, read from a git-ignored worktree cache on 2026-11-04.

**FOUND, NOT FIXED.**
- **E2-D14 extends to notes lists** (the coordinator's review of #883). `edgar.debt_maturities.
  _notes` reads the whole text, not by statement. So in "The Term Loan B matures on June 1,
  2030, and our 2.50% and 3.75% Senior Notes are due 2027 and 2029, respectively." the notes'
  own list is read by position: notes 2027, on main and after #883. Notes never differ in the
  maturity check (`decide`), so no page date moves. No code here.
- **The web reads the LATEST monitor day only.** A close is carried on every monitor day after
  it, so the latest is the complete set. A day that drops a close it carried before would hide
  that close's return. The python side refuses an unpairable close, so this has not been seen.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A close shows no return between its exit and the next monitor day.** That is the brief's
   rule: none, never a computed value. FALSIFIER: a committed close older than the latest monitor
   day that still shows none.
2. **A monitor fetch that fails with anything but a 404 now fails the ledger load.** That is
   `getMonitor`'s own contract, which every monitor surface already shares.
