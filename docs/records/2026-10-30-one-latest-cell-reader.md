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
- **The press-release policy is one constant.** `ciq_sheets.PRESS_RELEASE_REFUSED` names the
  statements whose latest press-release column `require_filed_income_statement` refuses (at
  assembly and in `anchor.ciq_bridge`). It holds `("Income Statement",)`, which is #868's ruling.
  - A release Balance Sheet or Cash Flow column is SERVED WITH ITS STATE SHOWN. Every latest-cell
    source_ref prints the header's own words ('[Press Release Q3 Sep-30-2026]'), and the posture
    appends "(press release)", which `_fin_short` erased.
  - Refusing those two as well is one line:
    `("Income Statement", "Balance Sheet", "Cash Flow")`.
  - **An operator ruling is owed**; see the PR body.

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
    reads 'NA' / '-'.
  - **ORKA:** interest coverage −59.5x, read from [12 months Dec-31-2024] behind a '-' LTM interest
    expense.
  - **FUBO:** free cash flow −107.8, read from [12 months Sep-27-2025].

**HOW VERIFIED.**
- **Failing first.** `tests/test_latest_cell_contract.py`: 55 failed, 2 passed and 1 skipped on
  main 9503c4fa; 59 passed here. The suite covers:
  - each of the 8 `gen.MARKERS` at the latest column, through the reader and through each
    decision-path reader;
  - the positive fences;
  - the policy's one-line switch;
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
  - the posture's label gains "(press release)" on GOOGL, LLY and SMPL;
  - the EBITDA window changes only on FUBO, refused both before and after.

**BOUNDARY.**
- **Census of latest-cell reads:** 104 non-held Financials exports in `mosaic-theory-ta`
  (current folders and `ciq-archive/`), read 2026-10-30 at 9503c4fa.
  - The rows: the 22 labels the readers take, on the Income Statement, Balance Sheet, Cash Flow
    and Ratios sheets of both frequencies. That is a superset of the one sheet each reader opens.
  - 1,975 reads: 1,845 unchanged, 88 empty either way, and 42 that `_latest_col` stepped back past
    a marker (32 of them in current exports).
  - 0 headers undated, 0 out of order, 0 with two columns at the latest date.
- **Press-release measurement:** the 34 current non-held folders, 2026-10-30.
  - With the refusal widened to the Balance Sheet and Cash Flow, 0 names are added: the same four
    (GOOGL, LLY, ONON, SMPL) are refused either way, because every release column on file sits in
    an export whose Income Statement is a release too.
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
