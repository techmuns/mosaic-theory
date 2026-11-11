---
status: shipped
date: 2026-11-11
prs: [961, 970, 973, 974, 975, 976]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 2, and the faster-fixes process: 20 fix-log rows from #961, #970 and #973–#976 (17 to `fixed`, 3 to `in progress`), STATE row 60 recounted (78 fixed, 92 open, 7 in progress, 1 disagreed), and the operator's four process changes recorded, among them the mechanical re-sync's exception from `bin/commit`

**WHAT.** This record covers two things.

**1. The batch.** This is the second batch under batched bookkeeping (operator 2026-11-10; batch 1
is `2026-11-11-fix2-bookkeeping-batch-1.md`). Each merged PR's "Bookkeeping for the coordinator"
section was applied to `docs/fix-log-teamnostra-2.md`, with its squash commit:
- **#974** (`ed2c5f8f`): RBC-D10 fixed.
- **#975** (`c2a4d743`): RBC-D3, V1-O3 and RBC-D5 fixed, all latent, no page moves.
- **#976** (`2b9b766c`): RE2-D1, RE2-D3, RE2-D4, E2-D3 (= RE2-D4, so both rows move), RE2-D7 and
  RE2-D19 fixed. RE2-D5 is fixed: its actuals half was #962 (`bfedbac9`) and its guide half is
  #976. RE2-D20 is `in progress (#976)`, because #976 calls it partial: the 21 unread list
  headers are still to be read.
- **#973** (`56d777af`), a record: #967 (RA-D2, RA-D4) measured on the panel does not ship. So
  RA-D2 and RA-D4 read `in progress (#967)`, and #967 is being split into two successors, each
  measured on its own.
- **#978** (`e73e7a54`) closes no ID, as its section says.
- **#961** (`d9dd48f5`): RE2-D16 and E2-D19's residual fixed. Its section wrote both as
  `in progress (#961)` before its panel check; the check then passed (no-worsening, $25.79 of
  $35) and it merged, so both read `fixed`.
- **#970** (`173b4818`): RA-D10, A-D15 (= RA-D10), RBC-D2 (= RA-D10, document 14) and RA-D17
  fixed, all latent.

The batch also changed two other things:
- **Fix-log header.** The paragraph saying "Order 2 is in two PRs … RD-D1 waits for #930" was
  stale: #953 merged RD-D1, and #930 merged. It now says what is merged, and adds the
  2026-11-11 process below.
- **STATE row 60.** Its title was recounted. It gained the clauses of #974, #975, #973 and #976,
  and a clause for the process.

**2. The faster-fixes process.** The coordinator reported to the operator on 2026-11-11 why fix
request 2 was slow: shared-file merge conflicts, a loaded machine, iCloud conflict copies, many
small PRs, and some scope beyond document 15. It proposed five changes. The operator approved
1–4 and added a requirement, verbatim: *"yes, approve 1–4 and we need to make sure the system
verifies & validates fixes based on data deterministically and its implication across the setup
before being merged with main / so the goal in short is to complete the fixes correctly in a
faster manner"*. The changes:
1. **The extraction-version table becomes one file per entry**, so concurrent PRs never edit the
   same lines. A session was started for it; its PR is pending.
2. **A mechanical re-sync is gated by CI, not by a local `bin/commit`.** A re-sync is mechanical
   when the merge from main conflicts only in extraction-version rows and their drift pins,
   STATE.md rows or fix-log rows, and it changes no other code. The four shared-file tests run
   locally first: `test_state_identifiers`, `test_state_open_now`, `test_fix_log` and
   `test_extraction_version_drift`. GitHub's `gate` run on the head is then the gate. A re-sync
   touching any other code still goes through `bin/commit`. This is written into
   `.github/workflows/gate.yml`'s header, beside the rule it qualifies ("`bin/commit` stays
   mandatory before a push").
3. **One PR per remaining order group per stream**, in place of one per one or two IDs.
4. **A scope freeze**: no work outside fix request 2 until it is done, apart from what was
   already in flight.
5. **The requirement the operator added: a deterministic cross-setup validation in every fix PR
   body**, checked by the coordinator before any merge. It is built from real committed data,
   with base as the merge-base and head as the PR head:
   - the new tests failing on base code and passing on head;
   - a $0 build of every committed page at both, with every moved value listed;
   - the six panel pages' synthesis requests compared ($0), which says whether a STATE row-53
     paid check is owed;
   - the rendered-file diff;
   - the downstream readers (screens/G3, the ledger and scoring report, the monitor, the theme
     desk, the frontend).
   A session is building it as one command, which also fixes RD-D4, prespend's presence-only
   compare. Until that command lands, each stream builds the section by hand with
   `vinci dossier precheck` and `python -m vinci.evals compare`.

The coordinator also capped heavy runs at two at a time across the machine: `bin/commit`, a full
pytest, and an all-pages $0 run. The cap is a local wrapper with two slots, not a repo file. It
was stated to the operator in the same report.

**WHY.** Rule 3 of the log says `fixed` means on `main`. Every flip here is read from the PR's
own words: its bookkeeping section, its title, or its Completion table. A PR that calls an ID
partial keeps it `in progress`.

The process changes target where the time went. Each edit to a shared line, whether the version
table, row 60 or the log, made every other open PR conflict. Each conflict then cost a local
re-gate of 30 to 80 minutes under a load average that reached about 470. Batching the
bookkeeping (batch 1) removed two of the three shared surfaces. Item 1 removes the third, and
item 2 makes the remaining conflicts cheap.

The validation requirement answers a different question: whether a fix is right, and what else it
moves. Until now each PR answered that in its own way, and some did not. #953 and #976 each ran a
27-page $0 compare by hand, while the RD-D4 defect shows the one shared tool compares presence
only.

**HOW VERIFIED.**
- `tests/test_fix_log.py` passes on this branch, with `test_state_open_now` and
  `test_state_identifiers`. That lint refuses a `fixed` row whose squash commit is not reachable
  from `origin/main`, or whose test node does not exist. Every test node the 20 changed rows name
  exists on main `173b4818`.
- The counts were read by a script over every row's Status cell.

**BOUNDARY.** The counts:
- 78 fixed, 92 open, 7 in progress and 1 disagreed. These are all 178 rows of
  `docs/fix-log-teamnostra-2.md`, by Status cell, on this branch merged with main `173b4818`,
  counted 2026-11-11.
- The 30 `§4` rows (TeamNostra builds them) are among the 92 open.
- The 20 rows changed: 16 from `open` to `fixed`, 1 from `in progress` to `fixed`, and 3 from
  `open` to `in progress`.
- "30 to 80 minutes" is the range of local `bin/commit` wall times the streams reported on
  2026-11-10 and 2026-11-11.
- "About 470" is the peak 1-minute load average from `uptime` on the primary Mac, as the
  coordinator read it during 2026-11-10 and 2026-11-11. It read 7.3 at 09:17 IST on 2026-11-11,
  when most sessions were idle.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The mechanical re-sync's exception (item 2) is an accepted risk.** After such a re-sync,
  main's code and the branch's meet with no CIQ-bound pin run before merge. CI has no licensed
  export, so those pins skip there.
  **The cheaper fix was measured, not assumed, and it is not cheap.** It would mean running locally
  only the test files CI skips. CI run `42961443683` on main `173b4818` skipped 603 tests in 58
  files. Those 58 files took **2,184 s (36 minutes)** in the primary checkout on 2026-11-11,
  under a 1-minute load average of about 30. That is most of a local `bin/commit`, which takes 30
  to 80 minutes, so it would save little of the re-gate the exception exists to skip.
  **The same run found main red in the primary checkout, on local data state, before any
  mechanical re-sync merged.** Seven tests in six files fail at `173b4818`:
  - `test_estimate_year_derivation[V-want3]`: V's re-export derives FY27E/FY28E;
  - `test_ev_bridge::test_claims_equal_ciqs_current_figure_on_every_committed_name`: UBER, 5356.0
    vs 8973.0;
  - `test_forward_consensus[GOOGL]` and `[LLY]`: a spread's mean off its trends figure beyond 2%;
  - `test_forward_multiple_history::test_nm_and_no_data_stay_different_states`;
  - `test_run_visibility`: the local `frontend/snapshots/` build is from 2026-08-12;
  - `test_store_freshness`: the primary's store is 40 to 60 days behind on the benchmark IWM and on
    14 page names.
  None of the six test files changed on 2026-11-11.
  **FALSIFIER, against that baseline:** after each merge batch, the coordinator runs the full local
  suite on main in the primary checkout, which holds the exports. If a test fails that is not in
  the baseline set above (or in a baseline the record of its fix restates), and the batch merged a
  mechanically re-synced PR, the exception is withdrawn.
- **Hand-built validation sections, until the command lands, can miss a reader.**
  **FALSIFIER:** once the command merges, it is run on the PRs merged with hand-built sections.
  Any moved value or reader they did not list is recorded as a defect of this process.
