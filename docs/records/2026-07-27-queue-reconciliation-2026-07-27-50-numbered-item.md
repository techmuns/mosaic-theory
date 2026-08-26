---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

11. **QUEUE RECONCILIATION — 2026-07-27.** 50 numbered items at the 2026-07-23 check → **66 now**;
   **nothing was pruned without disposition (zero vanished)** — the queue grew. Every named item
   located in the catalog. Two notable dispositions: **basis-truthfulness GRADUATED** from queue
   item to enforced rule (`margin_basis` validator + `_require_bear_basis`), and
   **`tests-write-to-tmp` is FLAGGED** — it has no STATE record in this window at all (absent from
   the 2026-07-23 queue too, so it did not vanish during the scope), yet is de-facto practice in
   23 test files. **An unwritten convention that 23 files already follow should be written down or
   dropped deliberately — it is currently neither.**
