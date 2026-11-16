---
id:
status: open
date: 2026-11-16
prs: [1087]
supersedes:
superseded-by:
---

# The export-date pass names every recorded export it cannot match, where it said "unchanged". A CIQ column's own stated filing date now counts in `analysis_as_of` where the page carries it as a structured value, which today is only the capital-structure panel's, and it moves none of the 26 committed pages. The Financials `Filing Date` row needs a page field and stays open (STATE row 64(a), #1082's review)

**WHAT.**
- **(2) The pass names its skips.**
  - *The defect:* `refresh.export_date_transform` passed over a recorded comps export that no file under its roots matched by sha256, and `refresh_fleet` reported that page as plain "unchanged". A page left undated read like a page with nothing to fill. Only `test_no_committed_page_is_dated_before_a_ciq_export_it_records` caught a build-recorded page left undated, and the pass's own output did not.
  - *The fix:* the step is now an `ExportDateStep`. It records the sha256 of each export it looked for and names each one it could not date:
    - `"<TICKER>: skipped: export <sha256> not found in any <TICKER> folder under the roots"`, with the full sha256 the page records, where no file in the folders the search reads matches. The search reads only folders named for the ticker beneath each root (`inputs.candidates`), so the line never says "not on disk" (coordinator's review, round 1, F1);
    - `"<TICKER>: skipped: export <sha256> (<file name>) not read as a comps export"`, where a file matches but the loader kinds it as no comps export, so no date was ever read (round 1, F2);
    - `"<TICKER>: skipped: export <sha256> (<file name>) states no export date"`, where a file matches, is read as comps, and states no stamp (code review, round 0).
    - No line names a local path: a file by its name alone, and the roots by their count (round 1, F3). A resolved CIQ root can carry the operator's account folder name, and these lines are pasted into records and PR bodies here.
  - `refresh_fleet` reports each of those under a new `skipped` key, and a page with a skip is never listed "unchanged". A step that names its skips is any step meeting `refresh.NamesSkips`.
  - A `skip_count` line then states the count with its boundary: how many were skipped, of how many looked for, which exports (recorded comps exports with no `export_date`, matched by full sha256), where it looked (every folder named for the page's ticker under N roots), and on how many of the pages refreshed. A refused page never reaches the step, so it is not counted (code review, round 0).
  - A pass with no such step prints no count.
- **(1) A CIQ column's stated filing date counts, where the page carries it structured.**
  - A CIQ fact is knowable from its export date or from its column's own stated filing date, never from its period end (CLAUDE.md, PUBLISHED DATA).
  - Only one such date reaches a page as a structured value: the capital-structure panel's source filing date, `mechanical.capital_structure.maturity_check.panel_filed`. It is ISO, parsed once off the panel's `Source` note ("A 2025 filed Feb-12-2026") by the shared helper `ciq_sheets._cs_panel_filed`. It is on 26 of 26 pages.
  - `valuation_basis.date_semantics` now counts it (`CIQ_FILED_DATES`) where it is later than every other date the rule counts. There it sets `analysis_as_of`, and the rule gains `RULE_FILED_CLAUSE`, which names the field.
  - Where it is not later, the rule is kept word for word, since the latest-of it states IS the page's date. So the page's bytes do not move.
  - The display strings that print the same date (`detail_as_of`, `panel_vintage.source_ref`) are never read.
- **No committed page moves.** The real pass at head moved 0 of 26 pages. `data/dossiers/` and `frontend/` are byte-identical, and the PR carries no artifact commit.
- **Still open: the CIQ Financials `Filing Date` row.**
  - CIQ's Financials sheets (Balance Sheet, Income Statement, Cash Flow) state a `Filing Date` row for each period column, as an Excel serial. No reader reads it and no page carries it.
  - So the filing date behind `balance_sheet_date`, the period end of the latest balance-sheet column, is not counted.
  - Counting it needs a new field: on `inputs_schema.CiqExport`, plus a drop-when-None rule in `schemas.dossier_json`, or on `DateSemantics`. Either way `vinci/dossier/schemas.py` changes, and #1084 has that file open, so this PR stopped short of it and asked the coordinator. The coordinator ruled (2026-11-16): defer it to its own PR after #1084 merges, and leave `schemas.py` untouched here.
  - A $0 probe says it would move no page today (HOW VERIFIED).

**WHY.**
- **A skip that reads "unchanged" is a count without its boundary.** The pass knew it had looked for an export and not found it, and its output said nothing had been asked of the page. Same family as A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION: the population was there, the output just did not carry it.
- **Why the rule text changes only where the filing date binds.**
  - All 26 pages carry `panel_filed`. A rule naming it on every page would rewrite all 26 pages' `date_semantics`. The stale guard (`test_every_committed_page_carries_blocks_derived_from_itself`) would then demand a no-op refresh of every page, while #1084 re-renders pages in its own lane.
  - Where `panel_filed` is not later than the other dates, the latest-of the kept rule names equals the page's date, so the stored rule still states exactly how the date was reached.
  - Where it is later, the rule names it, since it is then the date the page is dated by. This is the shape the coordinator chose for #1082: a page with no recorded export date keeps its exact text.
- **Why only `panel_filed`, and not the strings.** Parsers consume structured values, never rendered strings (CLAUDE.md). The 200 `filed <date>` reads #1082's review counted are display text, of two kinds:
  - 117 are EDGAR filing dates quoted inside a CIQ-context string. 96 of them are the filings the maturity check quotes.
  - 83 are the capital-structure panel's own filing date printed as text, three times per page plus 5 in caveats. All 83 equal their page's `panel_filed`.
  - So `panel_filed` is the one structured CIQ column filing date on the page, and counting it covers every CIQ column date those strings print.
- **Set by face validity**: when the page's facts could have been known. No outcome was read.

**HOW VERIFIED.**
- **Fail first at base `ee9c4635`.** `tests/test_analysis_as_of_skips_and_filings.py`, first draft (11 pins):
  - 6 fail with the base `refresh.py` and `valuation_basis.py`: `KeyError: 'skipped'` twice, no `NamesSkips`, a count printed by a pass with no skipping step, and both positive filing-date pins (`2026-11-11 != 2026-11-12`, `2026-11-12 != 2026-11-13`).
  - The 5 that pass at base are the negatives and the corpus invariant, as they should.
  - The 3 pins added in review each failed against the code before its fix (Code review, below).
- **(2) on real data, before and after.**
  - The tree: the 26 pages as committed at `c58d5b2f`, before #1082 dated any, in a scratch tree. The CIQ root holds 25 links, one to each page's Drive folder except IT's.
  - *Base code:* 15 moved, **11 unchanged, IT among them**, no skip named.
  - *Head code:* 15 moved, 10 unchanged (the backfill-record pages), and IT under neither: `skipped: ['IT: skipped: export a3eeb41a2dde46a56659613c26168c7fe4804b7b38601edd4a6616560b025e5f not found in any IT folder under the roots']`.
  - The count line reads `1 skipped of 16 recorded comps export(s) with no export_date, matched by full sha256 in every folder named for the page's ticker under 1 root(s) — on 16 of 26 pages refreshed`.
  - The 15 that moved are #1082's 16 less IT.
  - The same run with each page's `dossier.md` beside its JSON gives the same counts. That run used head (`6c374b62` plus this round's fix) and main `032d2fde`.
  - **A skipped page can also be "moved".** A skip is reported whether or not the page moved. Where another layer of the page moves, such as a markdown re-render on today's renderer, the page is listed under "moved" and its skip is still named. The coordinator's review run (round 1) shows this: on today's renderer IT landed under "moved", with its skip named. So the defect is the "unchanged" line on a page whose skip went unsaid; a "moved" page never claimed it had nothing to fill.
- **(2) pins**, each on a living page written through the one serializer:
  - IT with its comps `export_date` taken off is named by its own sha256, and NKE (a backfill record naming no comps export) is "unchanged" (negative).
  - An export that IS on disk is filled, and no skip is named (negative).
  - A pass with no skipping step adds no count.
  - The step reports only the last page it was applied to.
- **(1) pins**, off IT's page as committed at `c58d5b2f`, frozen by its git blob:
  - *Positive:* `panel_filed` moved to 2026-11-12, one day past the page's latest date (2026-11-11). The page dates 2026-11-12 and its rule names the field. Beside a comps export date of 2026-11-12, a panel filed 2026-11-13 dates it 2026-11-13. No committed page has ever had a later one: V, SMPL, FUBO and WLK were checked across their last 12 page versions each. So the value is moved on a real page, not found on one.
  - *Negative:* IT's real panel date (2026-02-12), and one ON the page's date (2026-11-11), leave the block word for word.
  - *Never the string:* the display strings moved to Dec-31-2026 move nothing, and a page without `panel_filed` keeps its date.
- **End to end, on the corpus.** `test_no_committed_page_is_dated_before_a_ciq_filing_date_it_carries`: every page carrying `panel_filed` is dated on or after it, and names it in its rule exactly when it sets the date. The corpus pin `test_valuation_basis.test_every_page_names_its_dates_from_its_layers` now counts `panel_filed` in the latest-of.
- **No page moves, shown on the real run.** `refresh_fleet` with `export_date_transform` over the 26 living pages at head, Drive CIQ folder read only:
  - 0 moved, 26 unchanged, 0 refused, 0 skipped.
  - `0 skipped of 0 … on 0 of 26 pages refreshed`: all 16 build-recorded pages were already dated by #1082.
  - `git status` after showed no change under `data/` or `frontend/`.
- **The re-measure.**
  - At main `ee9c4635`, 200 CIQ-context `filed <date>` reads on the 26 pages; 0 are later than their page's `analysis_as_of`. That is #1082's figure, unchanged.
  - Structured: `panel_filed` is on 26 of 26 pages and later than the as-of on 0. The closest is V, filed 2026-11-05 against 2026-11-09.
- **The Financials `Filing Date` probe ($0, count only, fills nothing).** For each page, the Financials export its `ev_bridge.source_sha256` names was matched under the Drive folder, and the latest date its Balance Sheet `Filing Date` row states was read.
  - 23 pages were read. FUBO has no bridge stamp, and ORKA's and PARR's exports are in no folder named for their ticker under the Drive CIQ folder (the search `inputs.candidates` makes).
  - 0 of 23 are later than `analysis_as_of`.
  - The nearest: MCK filed 2026-11-04 against 2026-11-05, WERN 2026-11-09 against 11-12, UBER 2026-11-04 against 11-06.

- **Code review** (`/code-review high --fix`, round 0), 6 findings:
  - **Fixed in review:**
    - (1) the two modules moved without a pin. Vintage `2026-11-16.a-ciq-filing-date-counts-and-skips-are-named` is declared and `refresh.py` and `valuation_basis.py` are re-pinned. Its web copy is git-ignored, so no artifact moves.
    - (2) a matched export from which no date is read was still silent and "unchanged". It is now named, by a pin that failed first.
    - (3) the rule named every later filing date, not only the one that sets the page's date. It names only that one now, by a pin that failed first with two declared fields.
    - (5) the count's page total included refused pages, which never reach the step. It now counts the pages refreshed, by a pin that failed first on a sealed page.
  - **Dismissed:**
    - (4) the skip report is step state read after the call, not a return value. `TopLevelTransform` returns the keys to write and is the contract of six other steps in `refresh.py`, so a return channel would change all of them. `refresh_dossier` calls the step once per page, after every refusal check. The step resets on each call, pinned by `test_the_step_reports_only_its_last_page`.
    - (6) a comps row with no sha256 would be named "export None". `CiqExport.sha256` is a required field, and every committed page is written through the validating serializer, so no page can carry one.

- **Coordinator's independent review, round 1**, 3 findings, all in `refresh.py`'s skip output. Each is fixed behind a test that failed on head `6c374b62`:
  - **F1:** "not on disk" overstated the search. The reviewer held IT's exact export under `<root>/elsewhere/Gartner/`, under a passed root, and head printed "not on disk". The line now says "not found in any IT folder under the roots", and the count says where it looked (`test_the_skip_names_what_was_searched_never_the_whole_disk`).
  - **F2:** a false cause. The same bytes held as `IT/Gartner export.xls`, which the loader kinds as no comps export, were reported as "states no export date". They are now "not read as a comps export", and "states no export date" is kept for a file read as comps with no stamp (`test_a_file_the_loader_does_not_read_as_comps_is_named_as_that`). It is the same false-cause shape as row 63.
  - **F3:** the count printed each root's local path. Roots are now counted, and every skip pin checks that no output line holds an absolute path (`_no_local_path`).
  - The vintage's `names` text is corrected to match. `refresh.py` is re-pinned.

**BOUNDARY.**
- **Pages:** the 26 committed `data/dossiers/*/dossier.json` at main `ee9c4635` (2026-11-16), except the skip demonstration, which read the same 26 as committed at `c58d5b2f`.
- **"200 reads, 0 later":**
  - every `filed <ISO>` or `filed <Mon-D-YYYY>` match in a string value that names "CIQ" or sits under a path containing "ciq";
  - every match counted, not every string;
  - against that page's `date_semantics.analysis_as_of`.
- **The 117 / 83 split of the 200:** "panel-style" is a match of `(A|Qn) YYYY filed Mon-D-YYYY`, the panel's `Source` note shape; every other match is an EDGAR filing date quoted in the string.
- **"26 of 26 carry `panel_filed`, 0 later":** the structured field, against the same date.
- **"0 of 23" (Financials):**
  - the Balance Sheet sheet's `Filing Date` row, latest column, read as an Excel 1900-system serial;
  - in the export each page's `ev_bridge` names by its 10-hex sha256 prefix, under the Drive CIQ folder on 2026-11-16;
  - 3 of the 26 unread, named above.
- **History check:** V, SMPL, FUBO and WLK, their last 12 versions of `dossier.json` in `git log` each, `panel_filed` against `analysis_as_of`: none later.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$0.** No model call, no Polygon or Tiingo pull, no re-assembly, no page written.
- **The Financials column filing date is not counted.** A page whose price and exports all predate its latest balance-sheet column's stated filing date would read early. 0 of the 23 readable pages do today. It needs a page field in `schemas.py`, which is #1084's file, and is open in STATE row 64(a).
- **The rule text names the panel only where it binds.** A page whose rule does not name `panel_filed` was still checked against it. The stored rule describes how that page's date was reached, not every date compared on the way. Falsifier: a page whose `analysis_as_of` equals a `panel_filed` later than every other date while its rule does not name it. The end-to-end pin above fails on that.
- **NKE and ORKA still read early** until their next assembly records the comps export date (STATE row 64(a), unchanged by this PR).
