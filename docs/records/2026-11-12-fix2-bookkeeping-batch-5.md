---
id:
status: shipped
date: 2026-11-12
prs: [997, 1006, 1007, 1014, 1015, 1016, 1017, 1018, 1019, 1020]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 5 (S4): RG-D21 to `fixed`, RG-D19 and RG-D8 to `in progress (#1006)`, #1006's stream clause and #1015's void clause in row 60, operator item (10), seven merged PRs that name no fix-log ID recorded as such, the split's hand-offs amended on batch 3's record, and row 60 recounted (of 148 asked: 125 fixed, 15 open, 7 in progress, 1 disagreed)

**WHAT.**
- **The fix log**, `docs/fix-log-teamnostra-2.md`, changes three rows:
  - **RG-D21 → `fixed`** (#987 `bfd6a41a`, #1007 `97573f72`), as #1007's bookkeeping section asks.
    - Batch 3 kept the row `in progress` because a decline stated in percentage points or basis points still read positive. #1007 closes that residual.
    - The row names all four tests, two from each PR.
    - Its commit cell names the one shape #1007's record leaves as it reads, A's pin (#1007). With the bare number as the value text ("27", unit USD millions, quote "a 27 million decline"), +27 still passes. The registry holds 0 such claims.
  - **RG-D19 → `in progress (#1006)`** (#941 `d0563738`, #951 `586fdcfd`, #1006 `91817458`). #1006's section asked for `fixed`; B's review round 2 held it back (#1021).
    - The rule RG-D19 holds is that no public field quotes more than 12 consecutive transcript words. #1006's pin, `tests/test_public_transcript_text.py`, fired 6,284 times before the pass and 0 after, and it fails first (below).
    - **The residual:** three committed syntheses copy more than 12 consecutive transcript words without quotation marks (LLY 15, VITL 14, WERN 14; A on #1004, 2026-11-11 17:58Z, from #1006's Codex round 2). The pin reads a synthesis item only between quotation marks, so it passes over all three.
    - The operator ruled "$0 guard + redaction now (Recommended)": A's `_validate` refusal of any synthesis string sharing more than 12 consecutive words with the build's own transcripts, plus a $0 cut of the three runs. That PR is not on main at `53e5f26e`.
    - B did not re-verify the three, because the transcripts are private.
    - The row keeps the pin named, `test_no_committed_page_publishes_transcript_text_beyond_the_rule`, in place of the PR-1 locator test it named before. It flips to `fixed` when A's PR lands.
    - Batch 3 kept RG-D21 `in progress` for a residual with no live instance. This one has three.
  - **RG-D8 → `in progress (#1006)`**. Its clause-binding half is not built (strict xfail), so it stays in progress after #1006's merge, as that PR's record says.
- **Owed since before batch 4, booked here** (B, #1004, 2026-11-12: "Put #1006's and #1015's owed bookkeeping into #1021 now, as one scope commit"). Both PRs merged before batch 4 did, but neither was in its scope.
  - **#1006** (`91817458`):
    - row 60's RG-D19 + RG-D8 stream clause is replaced with the clause from #1006's section, plus its merge commit;
    - the clause keeps the design record, `docs/records/2026-11-10-driver-facts-not-quotes.md`, cited. That record stays `open`, because RG-D19's residual and RG-D8's clause-binding half are open, and `tests/test_record_status_matches_open_now.py` requires an open row to cite it;
    - the clause's "Still open" adds RG-D19's three-page residual, and row 60's "order 2 is in code but for RG-D19" stays as it reads;
    - **operator item (10)** is added as #1006's record states it: the ingest Mac uploads the spool's 2,266 files (PR 3's first real write) to the private bucket, owed after merge. It lives in **STATE §5.0 row 60**, in the Owner column's operator list after item (9).
  - **#1015** (`1df0dc18`): one clause in row 60's operator item (4), in its record's own words.
    - A monitor day keys a void on the SESSION it files, as it keys a close, never on the run's `--ref`.
    - The first GOOGL-free monitor day is the 2026-11-11 session's, filed once Polygon serves 11-11.
    - None is committed yet: `frontend/monitor/` holds 2026-10-30 and 2026-11-02 only.
    - Its found-not-fixed item, the void writer refusing a back-dated `--ruled-on`, was already in row 60's "after fix request 2, recorded not built".
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
  - the VRRM rehearsal ran on copies;
  - B's own two: fix 6 was dropped by its own $0 test (#1005, `4c8349bc`), and fix 4b waits on order 8 and A's `_validate` guard.
- **STATE.md §5.0 row 60** gets these changes:
  - the title recount;
  - batch 5 in the list of batches;
  - one batch-5 clause;
  - one sentence after the split, pointing at the amendment;
  - #1006's stream clause;
  - order 2's status;
  - #1015's clause in operator item (4);
  - operator item (10).

**WHY.**
- Under batched bookkeeping (operator 2026-11-10), a fix PR edits neither the log nor row 60. One writer applies each batch in a single docs-only PR.
- S4 has been the log's only writer since #1011.
- One batch means one row-60 recount, with no batch-6 rebase over the same lines (B, #1004).

**HOW VERIFIED.** On main `53e5f26e`:
- **Merged, and the log untouched.** Each of the ten PRs is merged at the commit named. None touched `docs/fix-log-teamnostra-2.md` or `tests/test_fix_log.py`. `git diff a0c0a845 origin/main` over both files is empty. #1006's and #1015's own diffs, each against its parent, leave both files and STATE.md untouched.
- **RG-D21's fail-first.** Each test file comes from main and runs on its PR's parent code:
  - #987's two tests on `31ff7b87`: 3 of their 4 cases fail;
  - #1007's two tests on `3bc96012`: all 28 of their cases fail, and the file's other 21 cases pass;
  - on main, all 49 cases in the file pass.
- **RG-D19's fail-first.** Main's `tests/test_public_transcript_text.py` (new in #1006, absent at its parent) runs on #1006's parent, `c0d6d830`, the commit main held before #1006:
  - RG-D19's pin fails with 6,284 violations, the count #1006's record gives at `70fa224d`. It has 1 case; the file imports nothing from `vinci`, so the run reads only that commit's committed pages;
  - `test_every_committed_transcript_row_keeps_its_fact_and_its_locator` fails there too;
  - on main, all 5 tests in the file pass, and so does RG-D8's named test;
  - passing on main does not make RG-D19 `fixed`: the three unquoted copies are outside what the pin reads (above).
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
- **The PRs.** The ten B named for batch 5 (issue #1004, 2026-11-12), read at main `53e5f26e` on 2026-11-12:
  - B's six: #1014, #1016, #1017, #1018, #1019 and #1020;
  - A's two: #1007 and #997;
  - the two owed since before batch 4: #1006 and #1015.
- **The counts.** All 178 fix-log rows by their Status cell, and separately the 148 asked (every Order but `§4`).

**THE COUNT.**
- Of the 178 rows: 125 fixed, 45 open, 7 in progress, 1 disagreed.
- Of the 148 asked: 125 fixed, 15 open, 7 in progress, 1 disagreed.
- Against batch 4:
  - RG-D21 moved from in progress to fixed;
  - RG-D19 and RG-D8 stay in progress, now `(#1006)`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **RG-D21's scale-word shape is left as it reads.** It is A's pin, from #1007. Closing it means stepping over scale words, which changes the pinned shape's path. No claim on the registry has this shape.
- **RG-D19 waits on A's PR.** Until it lands, three committed syntheses break the 12-word rule, and no committed test sees them. The pin holds driver rows, and quoted synthesis runs, over the living tree, not over history: every byte committed before #1006 stays public.
- **Found, not fixed (another row):** STATE row 59's title still reads "RG-D19 WAITS FOR A RULING". The ruling it waits for was made on 2026-11-09 (publish the fact, not the quote), so the title has been stale since then. Row 59 is outside this batch, and is reported to B.
