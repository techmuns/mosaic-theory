---
status: shipped
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# GOOGL's BUY is VOIDED on the primary's store through the ledger CLI (operator ruling 2026-11-11): X-GOOGL is appended and the committed ledger goes from 9 rows to 10; the monitor day run right after is NOT committed, because it exposed a reproducibility defect (below)

**WHAT.**
- **The write.** This is the void the operator ruled on 2026-11-11 ("we want to remove the buy
  card/ buy verdict altogether given it was done based on really old and wrong data and we dont
  want this buy verdict to interfere in future at all").
  - It ran after the mechanism (V1, #984) and the web twin (V3, #1001) merged, in that order, so
    the web never shows a voided BUY.
  - It ran after the operator-approved price-store refresh, from `main` at `8a72be4c`, in a clean
    worktree whose `data/vinci.db`, `data/cache`, `data/manual` and `.env` link to the
    primary's. It went through the ledger CLI only:

  ```
  vinci void-decision V-GOOGL --ruled-on 2026-11-11 --reason "operator ruling 2026-11-11: \"we want to remove the buy card/ buy verdict altogether given it was done based on really old and wrong data and we dont want this buy verdict to interfere in future at all\"; the entry was sealed on the 2026-08-14 close, 14 days before the 2026-08-28 decision (RF-D7), and is read at its correction R-GOOGL (340.65 on 2026-08-27)"
  ```

  It was run with `--dry-run` first, which printed the same mark and wrote nothing.
- **The store.** Its ledger table held the 9 committed rows, equal row for row to the snapshot,
  before the write.

  | | sha256 |
  |---|---|
  | Before (after the 2026-11-11 refresh) | `a6a18e7d61e7e845e2202f9cceb003c2860a4e49dbfce7ea574c48b57d90a57f` |
  | After the dry run | unchanged |
  | After the void | `2b75fe39a13f35905e6325aca86d9b0902b5414e5f6ab0fc01304ede8abc6b79`, its ledger table the 10 rows, equal row for row to the export |
  | After the monitor day | `2b75fe39…`, unchanged |

  A `.backup` of the store before the write is kept in the session's scratchpad.
- **The row.** `X-GOOGL`: `event` VOID, `voids_entry_id` `V-GOOGL`, `ruled_on` 2026-11-11,
  appended 2026-11-11T11:43:59Z. Its sealed mark is the monitor's own row for GOOGL at the latest
  close:
  - entry 340.65 on 2026-08-27, as the decision is read at its correction;
  - marked 287.38 on 2026-11-10;
  - total return **−15.58%** against SPY −2.51%, excess **−13.08 pts**.
- **The snapshot.** `data/snapshots/decision_ledger.jsonl` goes from 9 rows to 10: the 9 committed
  lines are byte-identical, plus X-GOOGL.
- **The monitor day was run and is NOT committed.** `vinci monitor` (no `--ref`, the routine run)
  ran right after the void.
  - It filed day `2026-11-10`, the latest completed session, with GOOGL out of the book and the
    freshness panel.
  - But that day does not reproduce. A void is in effect from its ruling date (2026-11-11), and
    #984's monitor keys it on the run's `--ref` (2026-11-11), while closes are keyed on the session
    the day is filed under. So a re-cut of 2026-11-10 keeps GOOGL, and
    `test_every_committed_monitor_day_reproduces_with_a_void_ruled_after_it` refuses the
    committed day.
  - A second pin (#1001's freshness pin) requires the latest committed day to carry a voided name,
    and goes red on any post-void day.
  - Both need code, so they are a separate PR, not this artifact.
  - Under the operator's "From 2026-11-11 on", the first day that correctly leaves GOOGL out is
    the 2026-11-11 session's. It is committed after that PR.
- **The frontend** (`python frontend/build.py`): `frontend/scenarios/GOOGL.json` and
  `GOOGL-2026-08-17.json` now carry `voided` and no ledger verdict. The web shows no voided BUY:
  - the live book and counts drop GOOGL (#1001's twins);
  - the freshness panel, still read from the 2026-11-02 day, labels GOOGL "verdict voided".
- **Nothing else.** This is an artifact-only commit: no code.

**WHY.** The operator's rulings of 2026-11-11, all verbatim:
- the void itself, quoted above;
- its mechanism, "Void by appended row (Recommended)";
- its reason, "Your words + the stale entry (Recommended)";
- its effect, "From 2026-11-11 on (Recommended)";
- the finish, "Yes, that order (Recommended)", meaning #991, then the refresh, then V3, then V2
  with the monitor day.

**HOW VERIFIED.**
- **The full offline suite is green on this commit** (`bin/commit`). With the void committed, every
  test reads the ledger its subject needs. #984 and #1001 made the suite robust to a committed
  void and proved it on a simulation of this commit.
- **The cards:** both GOOGL cards carry `voided` and no `ledger` or `supersededLedger`. #1001's
  pins render the banner on the committed GOOGL page from this ledger.
- **Live reads:** Polygon 11, Tiingo 7, for the void's mark and the uncommitted monitor run, the
  ledger's names and benchmarks only.

**BOUNDARY.**
- Store sha256s are for the primary's `data/vinci.db` on 2026-11-11.
- The mark is the monitor's at the latest completed session, 2026-11-10 (the run was at 05:xx ET
  on 2026-11-11).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The void is permanent.** The ledger refuses an UPDATE or DELETE, and one void per decision.
  GOOGL's decision, its correction and its void stay in the ledger as audit history, and the
  decision log's audit tier shows them once.
- **A fresh GOOGL decision** is allowed from 2026-11-11 on (the operator's "After a close or a
  void"). It goes through the vote rule's confirmation, which refuses GOOGL's committed page,
  because it is a backfill, until that page is rebuilt.
## Amendments

- **2026-11-11 — `status: open` → `shipped`** (the record-status sweep, `docs/records/2026-11-11-record-status-sweep.md`). This record's change merged to `main` as `2637e91b` (#1008) on 2026-11-11. `prs:` was left empty at merge; the front matter stays as merged, so this entry names the PR.
