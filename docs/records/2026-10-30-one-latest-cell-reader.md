---
id: 2026-10-30-one-latest-cell-reader
status: open
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# Every CIQ reader of "the latest" figure reads the latest-dated column, and a marker there is said — never an older period in its place (audit RC3)

**WHAT.**
- **One reader.** `ciq_sheets.latest_cell(rows, ri, hdr)` returns a `LatestCell`: value, column,
  period (`header_period`, with #868's column STATUS), label, state and reason.
  - The latest column is the one whose header states the latest DATE (`_column_date`), never a
    position.
  - **present:** the cell there is a number.
  - **unavailable:** the cell there is a CIQ marker ('-', 'NA', 'NM', …) or blank. The reason
    names the cell and the column, and no older column is read in its place.
  - **unplaced:** no header cell states a date, or two columns state the latest one. Nothing is
    guessed.
- **It replaces `_latest_col` at all 11 call sites** (audit A-D5, A-D12):
  - in `ciq_sheets`: `free_cash_flow`, `_bs_latest_from` (net debt, total debt and the bridge's
    balance-sheet lines), `ltm_ebitda`, `ltm_ocf`, `_quarterly_revenue_yoy`, `_segment_roster`,
    `_segment_section`, `key_ratios`, `book_value_per_share` and `_bs_posture_build`;
  - in `ciq_balance`: `pick_with_period`, which the bridge's `_cf_cell` reads.
- **The changed rules at those sites.**
  - `_bs_latest_from` falls to the annual sheet only when the quarterly sheet lacks the row, never
    when its latest cell is a marker.
  - `key_ratios` pins the sheet's latest column. It was the rightmost column ANY ratio populated.
  - The posture's cash anchor is UNKNOWN at a marker. It used to fall to the other sheet.
  - The bridge reads the first statement carrying the row. A cash-flow row at a marker is never
    re-read from the income statement.
- **Sibling readers adopt the same rule.**
  - `interest_coverage` reads EBITDA and interest expense both at the latest column. It used to
    scan right to left for the first column valued in both.
  - `ebitda_recon.reconcile` keeps a marker quarter in its window and refuses the block when any of
    the four latest quarters is one (D-D2). It used to drop the marker quarter, which shifted the
    window back by one.
  - `midcycle.multiple_anchor` is unavailable when the latest TEV/LTM EBITDA close is NM (D-D3), as
    `_own_history_band` already was.
- **The bridge says why a fill cannot be made.**
  - The revenue fact states its period, LTM or FY (A-D7). Its basis read "latest full year" with
    no period.
  - `CiqFacts.unavailable` records why the OCF, capex or D&A fact is absent.
  - `anchor._bridge_inputs` adds that reason to `ltm_fcf`'s and `d_and_a`'s UNKNOWN source.
- **A press-release Balance Sheet or Cash Flow is REFUSED, as the Income Statement is.**
  `ciq_sheets.PRESS_RELEASE_REFUSED = ("Income Statement", "Balance Sheet", "Cash Flow")` names
  the statements whose latest press-release column `require_filed_income_statement` refuses, at
  assembly and in `anchor.ciq_bridge` alike.
  - **RULED 2026-10-30** by the operator ("agreed") on this reasoning: "Waiting a few days for
    the filed numbers costs us nothing. A wrong net debt inside a valuation costs a lot. Serving
    the figure with '(press release)' shown would warn a human reader, but the anchor and bridge
    calculations would still run on the wrong number; a label doesn't stop that."
  - The PR first shipped `("Income Statement",)`, #868's ruling, so the choice was one line; the
    ruling made that edit.
  - **Where a release column can still be read:** outside those two paths, in a refresh
    transform that re-reads a page's own export with no refusal (e.g. `release_figures_transform`
    → `mechanical._release_lines` → `ciq_sheets.net_debt`). A page assembled on a release export
    before #868 has one: LLY's #867 page. There the source_ref keeps CIQ's own words ('[Press
    Release Q3 Sep-30-2026]'), and `LatestCell` carries the status.
  - The posture's "(press release)" suffix, added in this PR's first cut, is removed: the posture
    is built only in assembly, after the refusal, so a release column can no longer reach it.

**WHY.**
- `_latest_col` took the rightmost VALUED cell, so a marker in the latest column served an older
  period under the same label.
- Its order guard decoded only Excel serials. It ran on the annual balance sheet alone, so a
  right-to-left Income Statement served its oldest period.
- Item 20's rule ("no backward-fill on ANY time series") had reached only the Multiples readers.
- Live on committed pages, each value reproduced from the page's own export (sha256 prefix
  matched):
  - **LLY:** `quality.free_cash_flow` 1,951.0 [12 months Dec-31-2025]; `net_debt_to_ocf` 2.7, CIQ
    net debt at the press-release Q3 over OCF 16,813 for FY2025; `anchor.ltm_fcf` 8,972.0,
    "fiscal year to 2025-12-31 (vendor basis)". Each sits behind an LTM press-release column that
    reads 'NA' / '-'. The anchor bridge's `d_and_a` fact, 1,997.0 for FY Dec-2025, behind a '-'
    'Depreciation & Amort., Total', becomes absent with its reason. LLY's anchor reads EDGAR's D&A,
    so no anchor value moves with it. Its D&A check line now names both rows' '-' cells, where it
    said "only one statement discloses a depreciation line".
  - **ORKA:** interest coverage −59.5x, read from [12 months Dec-31-2024] behind a '-' LTM interest
    expense.
  - **FUBO:** free cash flow −107.8, read from [12 months Sep-27-2025].

**HOW VERIFIED.**
- **Failing first.** `tests/test_latest_cell_contract.py` failed 55 and passed 2 (with 1 skipped)
  on main 9503c4fa, at this PR's first head. At the final head it passes 73: 62 at the
  coordinator's review of 856051cd, plus round 2's 11. The suite covers:
  - each of the 8 `gen.MARKERS` at the latest column, through the reader and through each
    decision-path reader;
  - the positive fences;
  - the refusal of a release Balance Sheet and Cash Flow, at assembly and in `ciq_bridge`, which
    fails on the pre-ruling head 29702126, with its filed-statement fence;
  - three corpus properties.
- The strict xfail `test_a_right_to_left_sheet_never_serves_its_oldest_period_as_latest` passes,
  and its marker is removed.
- **Corpus.** On main, the property "a PRESENT figure names its sheet's latest dated column" found
  4 reads:
  - FUBO and LLY free cash flow;
  - LLY OCF;
  - ORKA interest coverage.
  The bridge property found LLY's OCF and capex. Here, 0 of both.
- **Shown run (decision path).** `anchor._bridge_inputs` and `compute_anchor` were run on LLY's
  committed mechanical layer, the frozen `tests/fixtures/companyfacts/LLY.json` and LLY's own
  export:
  - `ltm_fcf` 8,972.0 (FY2025) becomes UNKNOWN, naming the '-' cells;
  - `applicable` stays True;
  - the R1 base stays $752.2356 a share, because `ltm_fcf` does not feed R1.
- **Replay** of every touched reader under main's code and this branch's, over the 26 committed
  pages' names on their `-ta` exports:
  - values move only for LLY, ORKA and FUBO (listed above);
  - every bridge revenue fact gains its period, with no value change;
  - the EBITDA window changes only on FUBO, refused both before and after.

**BOUNDARY.**
- **Census of latest-cell reads:** 104 non-held Financials exports in `mosaic-theory-ta`
  (current folders and `ciq-archive/`), read 2026-10-30 at 9503c4fa.
  - The rows: the 22 labels the readers take, on the Income Statement, Balance Sheet, Cash Flow
    and Ratios sheets of both frequencies. That is a superset of the one sheet each reader opens.
  - 1,975 reads: 1,845 unchanged, 88 empty either way, and 42 that `_latest_col` stepped back past
    a marker (32 of them in current exports).
  - 0 headers undated, 0 out of order, 0 with two columns at the latest date.
- **Press-release measurement:** the 34 current non-held folders, 2026-10-30, run again on the
  ruling's code.
  - Refusing all three statements adds 0 names: the same four (GOOGL, LLY, ONON, SMPL) are refused
    as under the Income Statement alone, because every release column on file sits in an export
    whose Income Statement is a release too. Each refusal now names 6 columns (both exports × the
    three statements), where it named 2.
  - UBER's archived release export (`replaced-2026-10-11`), set against its current filed export
    at Jun-30-2026, counting rows valued on either side:
    - quarterly Balance Sheet: 14 of 48 differ (7 by value, including Net Debt 9,340.0 against
      4,744.0; 7 a value against a marker);
    - quarterly Cash Flow: 8 of 33 differ.
- **Page impact:** the 26 committed `data/dossiers/*` pages less the held pack, at 9503c4fa.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A figure whose latest cell is a marker is now UNKNOWN where it used to print an older one. That
  is the intent.
- LLY's free cash flow and OCF are UNKNOWN until its 10-Q is processed. `net_debt_to_ocf` then
  falls to `mechanical`'s EDGAR breadth fallback; `mechanical` belongs to another session.
- No committed page is re-assembled here. LLY and ORKA are added to STATE row 41. FUBO is not
  pursued and keeps its value.
- Falsifier for "unplaced never fires": a re-export whose header carries two columns at its latest
  date. Those reads then go UNKNOWN, and the reason names both columns.

**ROUND 2 (coordinator review of 856051cd; one commit, each fix behind a test failing there).**
- **The bridge fills from a narrower row only where the primary row is ABSENT.** This covers
  'Cash And Equivalents' for 'Total Cash & ST Investments', the 'Depreciation & Amort.' component
  for the consolidated total, and the annual diluted average for the quarterly count. A marker on
  the primary row makes the fact unavailable, with its reason in `CiqFacts.unavailable`.
  - Under `_latest_col` a marker stepped back to an older period, so the fallback was reached only
    for an absent row.
  - This PR's first cut let the component fill in silently. On the synthetic case that was a D&A
    of 8.0 for 12.8, which the containment check compared with itself. 0 of 104 exports had the
    shape.
- **`ev_bridge` reads its balance-sheet column through `latest_cell`.** It used to take the highest
  dated column index. On a right-to-left sheet it bridged 2024-08-31 while `net_debt` read
  Aug-31-2026. The 26 pages' bridges are identical.
- **A refused EBITDA reconciliation is written WITH its reason.** `EbitdaReconciliation.refused`
  is a new field: no quarters, `ciq_ltm` None, and `line` naming the quarter and its cell.
  - Both renderers print it.
  - The scorecard reads it: "refused at assembly — …".
  - The backfill transform names it: "the rebuild refuses it: …".
  - It used to return None, which the page, the scorecard ("not four consecutive quarters") and
    the transform ("the rebuild wrote no block") all misread. `refused` is absent when unset, so
    committed blocks round-trip byte-identical.
- **An annual balance-sheet release column at the fiscal year's end waits for the 10-K.** It used
  to name the 10-Q. A bare date has no kind, so the year end is read as the month the export's
  columns mostly end in.
- **A period header naming an undated column places none.** A newest column suffixed
  'Jun-30-2026A' was skipped, and the one before it was served as the latest. 0 of 13,496
  non-empty period-header cells in 615 header rows across the 104 exports are undated.
- **Replayed** under main 8e6b12b1's code and this branch's, over the 26 pages' names: the same
  moves only (LLY, ORKA, FUBO, plus LLY's bridge facts above). R1 is unchanged.

**DEFERRED FROM REVIEW (PR #872 round 1, in-session `/code-review high`; Codex hit its usage limit).**
- **To A2, the zero-coercion PR:** `key_ratios` prints "dividend: none" when the pinned column's
  Dividend per Share cell is any non-number, a CIQ marker included. That is the RC1 class (a marker
  read as a stated absence).
- **Latent, 0 cases on file:**
  - `ciq_balance._bs` drops the reason when a balance-sheet leg's latest cell is a marker, so the
    anchor's CIQ net-debt fill fails without naming it. There are 0 such BS-leg markers on the rows
    the bridge reads in current exports; the census above covers it.
  - `ebitda_recon._ciq_quarters` keys quarters by date, so two columns at one date collapse with
    the rightmost winning. There are 0 same-date columns in the 104 exports.
- **For the coordinator:** the corpus tests here, like every existing corpus test, iterate every
  folder under `data/manual/ciq`. In a checkout that holds the held test pack they read its
  exports. Excluding it needs its names in code, which this PR may not write.
