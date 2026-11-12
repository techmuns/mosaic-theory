---
id:
status: shipped
date: 2026-11-12
prs: [997, 1007, 1014, 1016, 1017, 1018, 1019, 1020]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 5 (S4): RG-D21 to `fixed` (#987, then #1007), seven merged PRs that name no fix-log ID recorded as such, the split's hand-offs amended on batch 3's record, and row 60 recounted (of 148 asked: 125 fixed, 15 open, 7 in progress, 1 disagreed)

**WHAT.**
- **The fix log**, `docs/fix-log-teamnostra-2.md`, changes one row:
  - **RG-D21 → `fixed`** (#987 `bfd6a41a`, #1007 `97573f72`), as #1007's bookkeeping section asks. Batch 3 kept the row `in progress` because a decline stated in percentage points or basis points still read positive. #1007 closes that residual.
  - The row names all four tests, two from each PR.
  - Its commit cell names the one shape #1007's record leaves as it reads, the coordinator's pin. With the bare number as the value text ("27", unit USD millions, quote "a 27 million decline"), +27 still passes. The registry holds 0 such claims.
- **Seven PRs name no fix-log ID, so they book no row.** Each says so in its own bookkeeping section, and an ID scan of each body and record agrees:
  - **#1014** (`9b12444e`): the refresh back-fill is cut at the page's price date. This was #884's open item, and is a hand-off (below).
  - **#1016** (`dacc5fe1`) and **#1020** (`3bc96012`): row 42's two edges, #878's own item.
    - Each PR updated row 42 itself, and this batch leaves the row as they wrote it.
    - Row 42 stays open on (a), `theme_intelligence.securities`, and (b), the web panel's silence on a dropped name, which is a render change.
    - #878's record stays `open`, cited by row 42.
  - **#1017** (`bc8ef88f`): RFL-D1 to RFL-D10 are confirmed on main by TeamNostra's own reproduction.
    - All ten were already `fixed` in batch 3. The confirmations change no row.
    - The PR re-scoped row 44 itself.
  - **#1018** (`91dbdd8a`): docs and rehearsal only. It updated rows 28 and 38 itself.
  - **#1019** (`7af9a5b1`): the prompt-fix program's fix 2, which is not a TeamNostra ID, and is a hand-off (below).
    - Its record names RG-D1 and RG-D7 only to say that A's driver-facts stream builds RG-D1 to RG-D7. All seven stay `open`.
  - **#997** (`53e5f26e`): the operator's 2026-11-11 P/E split rule.
    - Its record names RE1-D10 and RF-D5, both already `fixed`.
    - It renamed one RE1-D10 pin, `test_re1_d10_an_older_aliases_split_refuses_the_range`, to `test_re1_d10_an_older_aliases_split_is_checked_and_adjusted`.
    - The log's RE1-D10 row names a different test, `test_re1_d10_the_pe_range_reads_bars_before_a_retag`. That test still exists, so the row is unchanged.
- **The split's hand-offs** (batch 3's item 3) are amended on batch 3's record, not added as log rows, because the log admits only TeamNostra IDs:
  - fix 2 shipped, except a reconciliation's unit;
  - the refresh price-date edges' three back-fill paths shipped, with two items #1014 found and did not fix, one deferred to A's E2 branch;
  - slices 2b to 6 were re-scoped against RFL-D1 to RFL-D10, with no RFL remainder, and stay open in row 44;
  - the VRRM rehearsal ran on copies.
- **STATE.md §5.0 row 60** gets four changes:
  - the title recount;
  - batch 5 in the list of batches;
  - one batch-5 clause;
  - one sentence after the split, pointing at the amendment.

**WHY.**
- Under batched bookkeeping (operator 2026-11-10), a fix PR edits neither the log nor row 60. One writer applies each batch in a single docs-only PR.
- S4 has been the log's only writer since #1011.

**HOW VERIFIED.** On main `53e5f26e`:
- **Merged, and the log untouched.** Each of the eight PRs is merged at the commit named. None touched `docs/fix-log-teamnostra-2.md` or `tests/test_fix_log.py`: `git diff a0c0a845 origin/main` over both files is empty.
- **RG-D21's fail-first.** Each test file comes from main and runs on its PR's parent code:
  - #987's two tests on `31ff7b87`: 3 of their 4 cases fail;
  - #1007's two tests on `3bc96012`: all 28 of their cases fail, and the file's other 21 cases pass;
  - on main, all 49 cases in the file pass.
- **The ID scan.** Each PR body and its record were searched for every ID shape the log admits. The only IDs found are the ones listed above.
- **Row 42's tests.** `tests/test_netcache_json_body.py` and `tests/test_monitor_unreadable_window.py` pass on main (15 tests).
- **The lints.** These pass on this branch:
  - `tests/test_fix_log.py`;
  - `tests/test_record_status_matches_open_now.py`;
  - `tests/test_state_open_now.py`;
  - `tests/test_state_identifiers.py`;
  - the record lints.
- **The full offline suite.** The gate's run is in the PR.

**BOUNDARY.**
- **The PRs.** The eight the coordinator named for batch 5 (issue #1004, 2026-11-12), read at main `53e5f26e` on 2026-11-12:
  - B's six: #1014, #1016, #1017, #1018, #1019 and #1020;
  - A's two: #1007 and #997.
- **The counts.** All 178 fix-log rows by their Status cell, and separately the 148 asked (every Order but `§4`).
- **Not in this batch:** #1006 and #1015. Both merged before batch 4 did, and their bookkeeping sections ask for fix-log and row-60 changes (below).

**THE COUNT.**
- Of the 178 rows: 125 fixed, 45 open, 7 in progress, 1 disagreed.
- Of the 148 asked: 125 fixed, 15 open, 7 in progress, 1 disagreed.
- Against batch 4, only RG-D21 moved, from in progress to fixed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **RG-D21's scale-word shape is left as it reads.** It is the coordinator's pin from #1007. Closing it means stepping over scale words, which changes the pinned shape's path. No claim on the registry has this shape.
- **Owed by #1006 and #1015, outside this batch's scope:**
  - #1006's section asks for four changes: RG-D19 → `fixed`, RG-D8 → `in progress (#1006)`, row 60's stream clause replaced, and an operator item (10).
  - #1015's section asks for one row-60 clause: the monitor keys a void on the session it files.
  - Neither PR was in batch 4 or batch 5. RG-D19 still reads `in progress (#951)` and RG-D8 `in progress (#941)`, and row 60 still says #1006's PR 3 "follows".
