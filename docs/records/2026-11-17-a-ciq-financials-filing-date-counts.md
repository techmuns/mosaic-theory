---
id:
status: shipped
date: 2026-11-17
prs: [1097]
supersedes:
superseded-by:
---

# A page's `analysis_as_of` counts the CIQ Financials sheets' own `Filing Date` row. Each Financials export's latest stated column filing date is recorded in the page's input record with its cell, or UNKNOWN naming why, and counts where it is later than every other date. 23 of the 26 committed pages gain it at $0 and none is re-dated (STATE row 64(a), the half #1087 left open)

**WHAT.**
- **The gap.** A CIQ fact is knowable from its export date or from its column's own stated filing date, never from the period the column describes (CLAUDE.md, PUBLISHED DATA).
  - CIQ stamps no Financials export date, so #1082's export-date rule reads none for it.
  - Each period column of the Financials statement sheets states a `Filing Date` instead, the column behind `ev_bridge.balance_sheet_date` among them.
  - No reader read that row and no page carried it, so a page whose price and exports all predated its latest balance-sheet column's filing would read early. #1087 counted the one CIQ filing date a page did carry (`panel_filed`), and left this one open behind a page field (STATE row 64(a); coordinator, 2026-11-16: its own PR after #1084).
- **The reader.** `ciq_sheets.financials_filed_through(bundle, freq, *, sha256)` is the one reader; `inputs.filed_through(bundle)` is its door for the build and the backfill.
  - It reads the `Filing Date` row of the Balance Sheet, Income Statement and Cash Flow sheets. Every dated column counts, not only the latest: a comparative column carries the filing it was last taken from (IT's Q3 2025 column is dated by its Q3 2026 10-Q), so an older column filed later than the newest would date the export.
  - Each cell is decoded by `excel_date` off the cell the decode path hands over (an Excel serial on every export on file), never off a display string.
  - The date's `source_ref` names the workbook's full sha256, the sheet, and the cell's row and column, 1-based as the workbook numbers them. Where several cells state the date, the Balance Sheet's latest column is named.
- **Never a guess.** Each of these is UNKNOWN, with a note naming it:
  - a held statement sheet with no `Filing Date` row;
  - a latest column `latest_cell` (the house reader) cannot place;
  - CIQ's no-value marker in the latest column, which is the column behind the page's latest figures. An older column's date is never read in its place;
  - a cell that is neither a date nor a marker;
  - **a date before its own column's period end**, which files no such column. This is a check on the VALUE beside the checks that a date is there (CLAUDE.md, A COUNT TEST CATCHES SPARSE CORRUPTION AND CANNOT CATCH DENSE);
  - an unreadable workbook, and one holding none of the three sheets.
- **Passed over, and named in the note:**
  - an older column reading CIQ's marker (`'NA'`, `'-'`, a blank). It states no filing, and the note counts the columns and gives their first and last label;
  - a statement sheet the export does not hold, or holds as CIQ's no-data shell.
- **The field.** `CiqExport.filed_through` in the input record, on Financials rows only (`inputs.ciq[].filed_through`).
  - Its model, `inputs_schema.FiledThrough`, restates `schemas.Sourced[date]`'s shape and contract (PRESENT carries a value and a `source_ref`; UNKNOWN carries no value). `schemas` imports `inputs_schema`, so `inputs_schema` cannot import `Sourced`; a pin holds the two shapes equal.
  - The build records it as it reads (`load_bundle` → `provenance.FileRead.filed_through` → `inputs._ciq`).
  - ABSENT, never null, on every other row and on a record written before the field (`schemas.CIQ_EXPORT_DROP_WHEN_NONE`), so such a page round-trips byte-identically.
  - It sits outside `mechanical`, the synthesis's only input, so no synthesis request moves. `inputs_id` hashes kind, period type and sha256 only, so no record's id moves.
- **The rule.** `valuation_basis.date_semantics`, the way #1087 counts `panel_filed`:
  - a PRESENT `filed_through` later than every other date sets `analysis_as_of`, and the rule gains `RULE_FILED_CLAUSE` naming the record row (`inputs.ciq[<i>].filed_through`);
  - an UNKNOWN one dates nothing, and the rule gains `RULE_UNFILED_CLAUSE`: "not counted, a CIQ Financials export whose column filing date is UNKNOWN (its record names why), so this date may be early", naming the row;
  - otherwise the block is kept word for word, so the page's bytes do not move there.
- **The $0 path for committed pages.** `refresh.filed_through_transform(ticker, roots)` returns a `FiledThroughStep`, a `NamesSkips` step as #1087's `ExportDateStep` is.
  - It fills a Financials row only off the file whose full sha256 the page's own record names, read under the file name the record gives, by the build's reader.
  - It names each export it cannot read: "not found in any <TICKER> folder under the roots", or "(<file name>) not read as a <freq> Financials export". No line names a local path.
  - A matched export the reader reads UNKNOWN is not a skip: the UNKNOWN is what the export states, and it is written as such.
  - The inputs seam's guard (`_only_export_dates`, renamed `_only_stated_dates`) now admits filling `export_date` or `filed_through` where absent, and never moving or removing either.
- **The pages.** Run over the 26 committed pages at main `4889ddba` (the coverage roster's covered names), the CIQ folder read only:

| page | record | Financials rows filled | latest `filed_through` | `analysis_as_of` (unchanged) |
|---|---|---|---|---|
| AMZN | backfill | 1 of 1 (quarterly) | 2026-10-30 | 2026-11-02 |
| BRBR | backfill | 1 of 1 (quarterly) | 2026-08-04 | 2026-10-23 |
| BURL | backfill | 1 of 1 (quarterly) | 2026-08-27 | 2026-10-23 |
| CNXC | backfill | 2 of 2 | 2026-10-07 | 2026-10-28 |
| EPAM | build | 2 of 2 | 2026-11-05 | 2026-11-11 |
| FUBO | backfill | none recorded | — | 2026-08-17 |
| GOOGL | build | 2 of 2 | 2026-10-29 | 2026-11-11 |
| IT | build | 2 of 2 | 2026-11-03 | 2026-11-12 |
| LLY | build | 2 of 2 | 2026-10-29 | 2026-11-11 |
| MCK | build | 2 of 2 | 2026-11-04 | 2026-11-05 |
| NCNO | build | 2 of 2 | 2026-08-25 | 2026-11-11 |
| NFLX | build | 2 of 2 | 2026-10-21 | 2026-11-04 |
| NKE | backfill | 1 of 1 (quarterly) | 2026-10-02 | 2026-10-28 |
| ORKA | backfill | 0 of 1: skipped, named | — | 2026-10-23 |
| PARR | backfill | 0 of 1: skipped, named | — | 2026-10-23 |
| ROST | backfill | 1 of 1 (quarterly) | 2026-09-01 | 2026-10-28 |
| SMPL | build | 2 of 2 | 2026-10-27 | 2026-11-11 |
| TECX | build | 2 of 2 | 2026-11-05 | 2026-11-09 |
| TGT | backfill | 1 of 1 (quarterly) | 2026-08-28 | 2026-10-23 |
| TJX | build | 2 of 2 | 2026-08-28 | 2026-11-11 |
| UBER | build | 2 of 2 | 2026-11-04 | 2026-11-06 |
| V | build | 2 of 2 | 2026-11-05 | 2026-11-09 |
| VITL | build | 2 of 2 | 2026-11-03 | 2026-11-11 |
| VRRM | build | 2 of 2 | 2026-10-30 | 2026-11-09 |
| WERN | build | 2 of 2 | 2026-11-09 | 2026-11-12 |
| WLK | build | 2 of 2 | 2026-11-04 | 2026-11-09 |

  - **0 pages re-dated.** Every filing date read is earlier than its page's `analysis_as_of`; the nearest is MCK, filed 2026-11-04 against 2026-11-05. This is the count #1087's probe gave (0 of 23), re-measured through the production reader.
  - Every one of the 40 rows read is PRESENT; none is UNKNOWN.
  - Per moved page: `inputs.ciq[<financials row>].filed_through` and one `layer_refreshes` entry (`refresh`, layers `inputs`, at this vintage). `dossier.md` and its mirror move by two lines: the header's "layers refreshed to" stamp and that entry's line under "Refreshed since assembly" (PREVIEW RULE, HOW VERIFIED).
- **Vintage** `2026-11-17.a-financials-filing-date-counts`; `ciq_sheets.py`, `inputs.py`, `inputs_schema.py`, `refresh.py`, `schemas.py`, `valuation_basis.py` and `provenance.py` re-pinned.

**WHY.**
- **Set by face validity:** when the page's facts could have been known. No outcome was read.
- **Why the input record, and not `DateSemantics`.** `date_semantics` is derived from the page on every write (`with_derived`), so it cannot hold a value read off a workbook. The record already says what each file is (its kind, period type, sha256, and since #1082 the export date it states of itself); the latest filing date its columns state is the same kind of fact.
- **Why every dated column, not only the latest.** "The latest date at which every input is knowable": a page reads older columns too (the five-year panels, LTM sums), and CIQ is not point-in-time, so an export's facts are knowable no earlier than its latest stated filing. On the corpus the two readings agree (BOUNDARY); the latest-column reading would miss a restating amendment filed after the newest quarter.
- **Why only the three statement sheets.** The brief and #1087's record name them. The Capital Structure Summary, Supplemental, Segments and Industry Specific sheets carry the row too. The capital-structure panel's filing date reaches the page already (`panel_filed`). Measured on the 40 readable exports, none of the four other sheets states a date later than the statements' (BOUNDARY), so counting them would move nothing today.
- **Why an older column's marker is passed over but the latest column's is not.** CIQ's `'NA'` in an old Balance Sheet column marks a quarter with no balance sheet (27 such cells on the corpus, plus 1 in MCK's quarterly Cash Flow, all in older columns): there is no fact there to date. The latest column holds the page's latest figures, so a missing filing date there leaves the date of those figures unknown, and the reader says so rather than reading the column before it.

**HOW VERIFIED.**
- **Fail first at base `4336b542`.**
  - `tests/test_analysis_as_of_financials_filed.py` fails to import (`FiledThrough`).
  - On behaviour, IT's page as committed at `c58d5b2f` (frozen, checked by its git blob), its quarterly Financials row given a filing date of 2026-11-12:

    | | base `4336b542` | head |
    |---|---|---|
    | `analysis_as_of` | 2026-11-11 | **2026-11-12** |
    | rule names `inputs.ciq[6].filed_through` | no | yes |
    | the serializer keeps the field | no (dropped) | yes |
    | given an UNKNOWN one: `analysis_as_of`, rule names it | 2026-11-11, no | 2026-11-11, **yes** |
- **The pins** (`tests/test_analysis_as_of_financials_filed.py`), on cut-down sheets of IT's and UBER's quarterly Financials exports (`tests/fixtures/ciq_financials_filed_through.json`), the exports their pages record by sha256:
  - The fixture is cut through the real decode path. Each sheet keeps whole the two rows the reader reads: its dated period header (row 15 on all six) and its `Filing Date` row. Every other row is nulled in place, so every row number a `source_ref` prints is the export's. 240 cells for IT and 216 for UBER.
  - **A greedy cell-by-cell cut was tried first and refused.** `_dated_header` takes the first row holding two decodable dates, and `excel_date` decodes any number. So the greedy cut kept two DATA cells (`625.169`, `796.63`) as the Income Statement's "header": the same reading, a shape no export has. This is the CORPUS BEFORE SYNTHETIC hazard in a cut fixture. The cutter is in the session family's notes folder (`financials-filed-through/cut_financials_filed_fixture.py`), and its docstring says why.
  - **Positive:** IT's Balance Sheet latest cell moved to 2026-11-12, one day past the page's latest date, read through the production reader: the page dates 2026-11-12 and its rule names the row. No committed page has a later one (BOUNDARY), so the value is moved on a real page, not found on one.
  - **Negative:** IT's real filing date (2026-11-03), and one ON the page's date (2026-11-11), leave the block word for word.
  - **Missing:** a sheet with no `Filing Date` row is UNKNOWN, named; the page keeps 2026-11-11 and its rule names the row as not counted.
  - Each UNKNOWN case, each named: no row, a marker at the latest column (never the older column's 2026-08-04), a cell that is no date, a date before its period end, no statement sheet held. An older column filed later than the newest is read and named. UBER's three `'NA'` columns are passed over and counted.
  - The record: `FileRead` → `CiqExport`; absent, never null; a read row round-trips.
  - The backfill: it fills only the row whose sha256 matches, handing the reader that sha256; a record naming no Financials export, or already filled, is left alone; a missing file and a file the loader does not kind as that export are each named; `refresh_fleet` states the count with its boundary and prints no local path; the seam refuses a moved, removed or re-identified row.
  - Two CIQ-bound pins skip without the folder and pass with it linked: the reader off IT's real quarterly export reads the fixture's value cell for cell, and `load_bundle` records it on both Financials reads and nothing on the other nine.
- **End to end, on the corpus**, added in their own commit after the pass, each red on the pages before it and green after:
  - `test_no_committed_page_is_dated_before_a_financials_filing_date_it_records`: every page is dated on or after each PRESENT `filed_through` its record states, its rule names a row exactly when that row sets the date, and it names every UNKNOWN one. Red before the pass on its never-vacuous floor (0 rows filled); 40 rows after.
  - `test_every_build_recorded_page_states_its_financials_filing_date`: every Financials row a BUILD recorded carries the field. Red before the pass on EPAM's annual row.
- **The corpus pin** `test_valuation_basis.test_every_page_names_its_dates_from_its_layers` now counts each PRESENT `filed_through` in the latest-of.
- **The real pass.** `refresh_fleet(top_level_for=filed_through_transform(t, [the Drive CIQ folder]))` at head `71acc4ab` (main `4889ddba` merged):
  - 23 moved, FUBO unchanged, 0 refused, ORKA and PARR named: `"ORKA: skipped: export add437d7e322787cafacf8049cee9cd64b3b76ac74c4f8f2e67606ff2bcfc038 not found in any ORKA folder under the roots"`, and PARR's `abe144277e5de551b02a3436b5006bb95ce880c672e22965dc40c77ae6e9d761` alike.
  - The count: `2 skipped of 42 recorded Financials export(s) with no filed_through, matched by full sha256 in every folder named for the page's ticker under 1 root(s) — on 25 of 26 pages refreshed`.
  - **Every changed page audited against main, field by field** (STOP condition: any page re-dated, or any field but the new one moving). The only JSON paths that move on the 23 pages and their 23 mirrors are `+inputs.ciq[i].filed_through` and one appended `layer_refreshes` entry, the same entry on all 46 files. `date_semantics` moves on 0. The only `dossier.md` lines that move are the two named above, on all 23. Nothing to stop for.
- **The PREVIEW RULE.** Two rendered lines move, so the change was previewed before the PR: IT (a build record) and AMZN (a backfill), each before and after, each collapsed and force-open (every `<details>` opened, `body.ds-print-full`), cut from the app's own rendered DOM. Record & reproduce is a plain card, not a `<details>`, so its two states show the same rows. The shots and every changed markdown line are in the session family's notes folder, `financials-filed-through-preview/`. The operator's approval is open on the PR.
- **Code review** (`/code-review high --fix`, round 0), 9 findings:
  - **Fixed, each behind a pin that fails first** (at `ea342140`, before the fix):
    - (1) a matched export this machine cannot PARSE (no `xlrd`) was written UNKNOWN, permanently, since the seam never rewrites a recorded value. It is now a skip, "could not be read here".
    - (2) an export of unread period type beside another Financials export raised `CiqAmbiguousError` out of the build. It is UNKNOWN, named.
    - (4) the seam admitted `filed_through` on a non-Financials row, which `date_semantics` would then count. It is refused.
    - (6) only a lower bound checked the value. A filing date after the day the export is read (`read_on`; the door passes today) is now UNKNOWN: a corrupt 2099 serial read PRESENT at `ea342140` and would have dated the page 2099.
    - (7) the two stated keys were listed twice; the seam now reads the serializer's tuple.
    - (9) a row with no period type was named "a None Financials export". It is named without one.
  - **Dismissed:** (3) a mislabelled matched export stops the fleet loud, the contract #1087's `ExportDateStep` keeps; (5) this record and STATE row 64 are the build's own docs commit; (8) one extra hash of a ~0.5 MB export per read.
- **The suite round.** The full offline suite at `ed16258d` failed 3 tests; `d6e8b2ef` answers them:
  - `test_dossier::test_ciq_modules_covers_every_address_the_extractors_consume`, the CIQ_MODULES drift guard, reads only literal CIQ addresses, and the reader and the step computed theirs (`bundle.sheet("financials", sheet, freq=freq)`). The reader now reads each statement through `_STATEMENT_READS`, six literal addresses (the `_bs_column_near` idiom), and an export whose period type is neither annual nor quarterly is UNKNOWN, named, before any read. The step finds its workbook among `bundle.workbooks` and probes parsing with `ciq.read_sheets`. The reader's output is unchanged: the fixture's frozen reading and the corpus pins hold.
  - `test_input_manifest::test_a_page_with_no_record_reads_as_none_and_round_trips` asserted the string `"inputs"` absent from AMZN's page, the first. AMZN's new `layer_refreshes` entry names the `inputs` layer as a value. The pin's claim is the key's absence, and it now asserts that.
  - `test_sec_pacing::test_two_processes_on_one_machine_share_one_budget` failed on timing (a 0.117 s gap) in the six-way run beside an impact build, and passes alone. It is load, not code.
- **The suite.** ruff and `mypy --strict vinci` are clean (220 files). `pytest -m "not network"` with no CIQ folder, as CI runs it, at head `d6e8b2ef`, in six parallel processes by test file: every shard exits 0, with 11,819 passed, 674 skipped, 7 xfailed and 0 failed, counted from the progress lines. The two CIQ-bound pins pass with the Drive folder linked into the worktree for that run alone.
- **Cross-setup validation** (RUNBOOKS §o): `python -m vinci.impact run`, base `4889ddba` (the merge base) against head `d6e8b2ef`, patch-id `5ad1a9a9`, at $0. It used a store copy priced to 2026-11-11 and the HTTP cache served frozen, with 0 live fetches. The full section is in the PR body.
  - **Fail first:** 30 of the 127 nodes in the 4 changed test files fail on base code and pass on head's; 0 fail at head.
  - **Pages:** 25 of 26 built ($0 mechanical build) and 0 of 25 move. The tool does not compare the input record, so a fresh build's new field is not counted there; the pass above is where the field is measured. PARR is not built at base: its Financials file on disk is a mislabelled export, not the one its page records. That is pre-existing, and the same file the pass names as not found by sha256.
  - **Synthesis requests:** 0 of 25 differ, and the frozen panel is 0 of 6, so the row-53 panel check is not owed. The field sits outside `mechanical`.
  - **Rendered:** 0 of 26 committed pages re-render differently under head's code. The only frontend file that differs is `snapshots/extraction_versions.json`, which carries the new vintage.
  - **Downstream:** the decision ledger, the scoring report and the monitor are identical at both refs. The screen and the theme desk were not run (no `--run-screen`, no `--theme-data`).

**BOUNDARY.**
- **Pages:** the 26 committed `data/dossiers/*/dossier.json` at main `4889ddba` (2026-11-17), the coverage roster's covered names (11 active, 15 watch).
- **Exports:** each Financials export a page's input record names (`inputs.ciq[]` with `kind: financials`), matched by full sha256 in the folders named for the page's ticker under the Drive CIQ folder, on 2026-11-17. 42 recorded rows: 40 matched and read, 2 not.
  - FUBO's record (a backfill) names no Financials export, so it has no row.
  - ORKA's and PARR's (backfills) each name one quarterly export that no file in their ticker's folder matches.
- **"0 of 23 pages later":** each page's latest PRESENT `filed_through` against its `date_semantics.analysis_as_of`, at head. The nearest: MCK filed 2026-11-04 against 2026-11-05.
- **"40 of 40 PRESENT":** the reader's status on each matched export. 12 carry a note naming passed-over `'NA'` columns: 28 cells in all, 27 on a Balance Sheet and 1 on MCK's quarterly Cash Flow, each in an older column. None is UNKNOWN.
- **"latest column = latest date, three sheets agree":** on all 40, the latest date any dated column states equals the latest column's, and the Balance Sheet, Income Statement and Cash Flow agree (the survey, before the reader was written).
- **"0 later on the other sheets":** the Capital Structure Summary (40), Supplemental (40), Segments (40) and Industry Specific (14) sheets' `Filing Date` rows on the same 40 exports, 3,455 dated cells, each row's latest date against that export's `filed_through`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call, no Polygon or Tiingo pull, no re-assembly.
- **23 pages carry a field their build did not write.** `layer_refreshes` names the write (`refresh`, `inputs`, at this vintage), the house record of a change made after assembly, as for #1082's 16. A page assembled from now on records the field as it reads.
- **Three pages carry no Financials filing date.** FUBO, ORKA and PARR gain the field at their next assembly, which records it as it reads. All three are on watch (STATE row 41). Falsifier: a page whose build recorded a Financials export without the field, which `test_every_build_recorded_page_states_its_financials_filing_date` reds.
- **Four sheets that carry the row are not read.** Measured, none states a later date today. Falsifier: a future export whose Segments, Supplemental, Industry Specific or Capital Structure Summary sheet states a filing later than the statements'.
- **`_dated_header` reads any row with two numbers as a header.** It is the house reader and this PR does not change it; on the real sheets the dated header is row 15, above every data row. Found while cutting the fixture; reported, not fixed (Hold scope).
- **NKE and ORKA still read early** until their next assembly records the comps export date (STATE row 64(a), unchanged).
