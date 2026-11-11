---
status: shipped
date: 2026-11-10
prs: [955]
supersedes:
superseded-by:
---

# Fix request 2, group F, RF-D7, before the append: a correction row is tagged with the origin and sleeve its decision is read at, and the suite reads a corrected committed ledger. Found by running the suite against the 9-row ledger before anything was written

**WHAT.**
- **The finding.** #954 (`5ec1dc7c`) merged the correction mechanism and deferred the append
  until after merge (`docs/records/2026-11-10-fix2-groupF-d-two-stale-seals-corrected-by-appended-rows.md`).
  Before running that append on the primary's store, the suite was run on a `main` worktree
  (`4c98e17b`) with the 9-row ledger the dry run had exported. 21 tests went red.
  - **One is a defect in the row.** `correct_entry` copied its decision's `origin` and `sleeve`.
    VRRM's decision was logged before those fields existed and carries neither, so
    `R-VRRM-screen2-20260617` was written untagged. `tests/test_sleeves.py` holds that every row
    logged since the fields existed carries both. Appended, the row could never be fixed: the
    ledger refuses an UPDATE or DELETE, and the rule is one correction per decision.
  - **Twenty assumed an uncorrected committed ledger.** They pin values through the live
    artifact, or fake prices at the sealed entry.
- **The fix.** `correct_entry` tags the row with `origin_of(decision)` and `sleeve_of(decision)`,
  the reading the helpers give the decision (a legacy row reads `screen`/`overshoot`). A tagged
  decision passes its own through: GOOGL's correction carries `followed`/`quality`.
- **The tests, made to hold before the append and after.**
  - `tests/test_ledger_correction.py` reads the committed ledger AS SEALED, leaving out its
    CORRECTION rows. These tests write the corrections themselves.
  - `tests/test_monitor.py`: the benchmark assignment is checked against the DECISION row. It is
    stamped at the sealed entry, and a correction moves the entry a decision is read at, never the
    benchmark chosen at entry.
  - `tests/test_ledger_close.py` counts a correction as a third kind of row, and requires each
    one to name a decision.
  - `tests/test_monitor_ref_date_bound.py` (`_wire`, shared with
    `tests/test_realized_total_return.py`) and `tests/test_per_row_benchmark.py` build their flat
    synthetic prices at the entry each decision is READ at. `test_per_row_benchmark` scores to
    2027-03-19, past GOOGL's corrected horizon (2027-03-14), so every row with a horizon by then
    resolves on either ledger.
- **New pins.**
  - `test_a_correction_is_tagged_as_its_decision_is_read`: VRRM's → `screen`/`overshoot`,
    GOOGL's → its own `followed`/`quality`.
  - `test_every_committed_correction_is_the_rules_close`: on the committed artifact, each
    CORRECTION row names a decision the rule moves, carries exactly the rule's session and
    Polygon's close for it, and is tagged as its decision is read.

**WHY.** The coordinator's call (b) on 2026-11-10 put the append after the merge so that a finding
on the row's shape could land before anything permanent. This is such a finding. It was invisible
to #954's tests and to Codex, because both ran on a 7-row ledger with no correction in it.

**HOW VERIFIED.**
- **On the 9-row ledger the fixed writer exports** (the real `vinci correct-entry` on a scratch
  tree and a `.backup` copy of the primary's store): `R-GOOGL` is tagged `followed`/`quality`
  and `R-VRRM-screen2-20260617` `screen`/`overshoot`. The monitor's reading is unchanged from
  #954's dry run: GOOGL 340.65 @ 08-27 (−16.35%), VRRM 4.44 @ 06-18 (−50.68%, horizon
  2026-12-15), and the spread to 2026-11-06 is +71.55 → +66.89 pts.
- **The tests that read the committed ledger** (every `tests/*.py` naming `decision_ledger`,
  `snapshots_dir` or `_committed()`):
  - on `main` (`4c98e17b`) with the old writer's 9-row ledger: 21 failed;
  - on this branch with the committed 7-row ledger: 986 passed, 20 skipped;
  - with the fixed writer's 9-row ledger: 986 passed, 20 skipped.
- **The full offline suite on the 9-row ledger:** see the PR body.
- **Fail first.**
  - Removing the two tagging lines reddens `test_a_correction_is_tagged_as_its_decision_is_read`
    alone.
  - Setting `R-GOOGL`'s price to 340.0 in the 9-row ledger reddens
    `test_every_committed_correction_is_the_rules_close`, so the invariant reads the two rows
    rather than passing over them.

**BOUNDARY.**
- "21 red", "986 passed": the files named above, `pytest -m "not network"`, 2026-11-10, against
  the ledger file stated.
- The 9-row ledger: the 7 committed rows at `4c98e17b` plus `R-GOOGL` and
  `R-VRRM-screen2-20260617`, as `vinci correct-entry` exported them on the scratch copy.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **NOT FIXED HERE: `close_position` has the same gap.** It copies a decision's `origin` and
  `sleeve` too, so a close of VRRM's legacy decision would be written untagged, and
  `tests/test_sleeves.py` would refuse it after the fact. No such close exists. It is reported,
  not fixed, to hold this PR's scope.
- **The append still waits.** The order is this PR, then the append from `main` on the primary's
  store with the artifact-only PR, then VRRM's rehearsal (STATE row 38, by 2026-12-07).
