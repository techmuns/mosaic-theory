---
status: shipped
date: 2026-11-11
prs: [951, 953, 955, 956, 957, 960, 962, 963, 964, 965, 966, 969]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 1: 31 fix-log rows flipped to `fixed` from ten merged PRs, 3 rows set to `in progress` where their PR calls them partly fixed, STATE row 60 recounted (61 fixed, 111 open, 5 in progress, 1 disagreed), and rule 1 rewritten for batched bookkeeping

**WHAT.** This is the first batch under batched bookkeeping. The operator approved it on
2026-11-10: "yes to all, merge them one at a time". Fix PRs no longer edit
`docs/fix-log-teamnostra-2.md` or STATE.md §5.0 row 60. Each lists its changes in a "Bookkeeping
for the coordinator" section of its body, and one docs-only PR applies them. This is that PR. It
touches only the log, row 60 and this record.

- **The batch.** Each PR's section was applied, and each squash commit is checked reachable from
  `origin/main` by `tests/test_fix_log.py`:
  - #956 (`f2c8cfc3`): V2-N1 and RE2-D13 fixed; E2-D15's residual.
  - #957 (`507d4f32`): RA-D3, RA-D8, RA-D11, RA-D13, RBC-D6.
  - #960 (`33ff2024`): A-D2, D-D3, BC-D10.
  - #962 (`bfedbac9`): RE2-D2 and RE2-D8 fixed; RE2-D5 and RE2-D6 in progress; E2-D11's residual.
  - #963 (`2f920944`): RA-D9, RA-D14.
  - #965 (`cd832299`): RA-D15, RA-D16.
  - #966 (`7adfdae4`): RE2-D9 fixed; RE2-D10 in progress.
  - #969 (`670a784c`): RE2-D11, RE2-D12, RE2-D14, RE2-D15.
- **Merged earlier, rows still reading `in progress (#N)`.** Each row whose status named a merged
  PR was looked up with `gh pr view`:
  - #964 (`a71b9f67`): A-D13, A-D16, RBC-D7, BC-D1, BC-D2, BC-D3, BC-D5, BC-D6 and BC-D7, all
    fixed.
  - #953 (`7ec84833`): RD-D1, fixed.
  - #951 (`586fdcfd`): RG-D19 gains the squash commit and stays `in progress`, because PR 3, the
    $0 page pass, is still to come.
  - #941: RG-D8 is unchanged. It is `in progress`, its clause-binding half is not built, and no
    page carries the checks until PR 3.
  - #944, #947, #949, #954, #955, #936 and #937: no row still read `in progress` for them. Row
    60 now says #955 is merged.
- **Flipped to `fixed` (31):**
  - from `open` (19): RA-D3, RA-D8, RA-D11, RA-D13, RBC-D6, A-D2, BC-D10, D-D3, RE2-D2, RE2-D8,
    RE2-D9, RE2-D11, RE2-D12, RE2-D14, RA-D9, RA-D14, RE2-D15, RA-D15, RA-D16;
  - from `in progress` (12): RD-D1, V2-N1, RE2-D13, BC-D7, RBC-D7, BC-D1, BC-D2, A-D13, A-D16,
    BC-D3, BC-D5, BC-D6.
- **Left `in progress`, and why (5):**
  - **RE2-D5** (#962): only the actuals half shipped. #962 says "the guide half is open". Open PR
    #976 names that half, but no row records it.
  - **RE2-D6** (#962): its section writes a plain row. Its Completion table, though, says
    "SHIPPED (code); PARTIAL on real text", because Par Pacific's $(5.5) comparison is still set
    aside by `_sub_unit`, found and not fixed.
  - **RE2-D10** (#966): its Completion table says the no-flag half is NOT changed. An absent
    going-concern statement still writes no flag.
  - **RG-D19** (#951) and **RG-D8** (#941): PR 3 of the stream has not opened.
- **Two residual notes updated to the merge:**
  - **E2-D11.** #962's order-3 residual note replaces #956's, as the coordinator directed. It read
    "in progress in the release-actuals PR", which is #962, now merged, so it reads fixed in
    `bfedbac9`. Its pin joins the Test cell.
  - **E2-D15.** #956's section left the residual "in progress in V2-N1's PR". #956 is that PR,
    now merged, so the residual reads fixed in `f2c8cfc3`, with #956's two billions pins.
- **Rule 1** of the log now describes the batched process. Row 60's "The rule" clause now says
  the same.
- **Row 60** also received:
  - its title, recounted;
  - the row-60 clauses of #957, #960, #963 and #965 under the CIQ-reader stream, and of #962,
    #966 and #969 under group E2, each with its squash commit;
  - "#964 merged as `a71b9f67`";
  - "#955 merged as `5e3def4a`";
  - for the RG-D19/RG-D8 stream, "PR 2 MERGED as 586fdcfd (#951)" in place of "IN CODE".

**WHY.** Rule 3: `fixed` means on `main`. A row naming a merged PR while it reads `open` or
`in progress` claims less than is true. A row flipped past what its PR claimed would claim more.
Every flip here is therefore read from the PR's own words: its bookkeeping section, its fix-log
table, or its Completion table.

**SECTIONS NOT APPLIED AS WRITTEN.**
1. **"fixed on merge"** (#957, #960, #963, #965) is not one of the five statuses. It was applied as
   `fixed`, naming the squash commit beside the PR.
2. **Rows written `in progress (#N)` before merge** (#956, #962, #966, #969) are `fixed` now that
   #N has merged. RE2-D5, RE2-D6 and RE2-D10 are the exceptions.
3. **Accession numbers moved out of the Commit or PR cell**:
   - V2-N1: HP's 10-Q;
   - RE2-D13: Archer's 10-Q;
   - RE2-D9: Solo Brands' 10-Q and Aeluma's 10-K.

   The lint reads every run of 7 to 40 hex characters in that cell of a `fixed` row as a commit
   (`SHA = \b[0-9a-f]{7,40}\b`). An accession's ten-digit filer prefix is such a run, so the row
   would fail as an unreachable commit. Each accession now sits in the Test cell, beside the pin
   that reads its text. V2-N1 gains `test_helmerich_and_payne_term_loans_are_part_of_its_debt`
   for this, which #956 committed and its section did not name.
4. **#964 has no bookkeeping section.** Its body's fix-log table was applied instead: the removal
   pin `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it`, and
   no pages. **BC-D7 is the one flip composed from more than one PR.**
   - #964's table says "graph half" only.
   - #957's Completion table and #960's both name the graph parser as BC-D7's remaining half.
   - The dossier half was fixed in #881 (`60151ccc`), and the spreadsheet half is RBC-D6, in
     #957.

   All three halves are on main, so the row reads `fixed`. The coordinator should confirm or
   revert this one.
5. **#953 has no bookkeeping section.** Its table says "Fixed in code; pages refreshed at $0", so
   RD-D1 reads `fixed` with the row's own pins and pages. Its review finding 18, a one-leg peer's
   ratio entering the charge median, stays open, as #953's record says. It does not hold the row.

No section named a test that does not exist. All 39 test nodes the changed rows name are
collected by `pytest --collect-only`.

**HOW VERIFIED.** Run on this branch before `bin/commit`:
- `tests/test_fix_log.py` passes (39 tests). Its `landed_problems` reads every `fixed` row's
  commits and PRs against `origin/main`, because `fixed` rows exist.
- `tests/test_state_open_now.py` and `tests/test_state_identifiers.py` pass.
- `tests/test_records_ledger.py` passes.
- `pytest --collect-only` collects all 39 test nodes the changed rows name, with no error.

**BOUNDARY.**
- **The status counts (61 / 111 / 5 / 1):** all 178 rows of the table in
  `docs/fix-log-teamnostra-2.md`, by their Status cell, on this branch. The branch was cut from
  main `cd832299` and counted 2026-11-11.
- **The baseline (30 / 133 / 14 / 1):** the same file at `cd832299`.
- **"31 flipped":** rows not `fixed` at `cd832299` and `fixed` here.
- **"3 set to in progress":** rows `open` at `cd832299` and `in progress` here (RE2-D5, RE2-D6,
  RE2-D10).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Some `fixed` rows still have page work to come.** Their Pages cell says so:
  - E2-D11's residual, RE2-D2 and RE2-D8: notes on 10 pages once the $0
    `release_figures_transform` pass runs;
  - A-D2: 13 bridges in the $0 pass after driver facts PR 3;
  - RA-D13 and RA-D16: when the named pages are next assembled.

  Each PR called its code half shipped. Rule 3 asks for the pages the fix "changed and rebuilt";
  these name the pages to come.
- **Five `in progress` rows now name merged PRs.** Rule 2 reads such a row as taken, so no other
  agent will start the rest of these IDs until a row names who holds them.
- **Found, not fixed** (out of this PR's scope):
  - the log's header paragraph still reads "RD-D1 waits for #930" and "Order 2 is in two PRs",
    both stale since #953;
  - row 60's "order 2 (a session, no PR yet)" was not checked and may be stale.
