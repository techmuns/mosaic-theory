---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# Fix request 2, order 4, the CIQ reader's RA-D9 and RA-D14: an export in thousands is refused before assembly, as another currency is; Consensus's stats and Recent Changes are read by their headers, never by position. No page moves

**WHAT.**
- **RA-D9** (`ciq_sheets.require_millions`, `CiqUnitError`). Only the anchor bridge read a
  statement's own unit line (#863, BC-D10). The readers that print the page assume $M, so an
  export in thousands printed "Revenue ($M) 67,357,000" and an `ltm_ebitda` of 30,494,000.
  - A Financials money panel (`_MONEY_PANELS`: Income Statement, Balance Sheet, Cash Flow,
    Segments, Capital Structure, Historical Capitalization) whose unit line states anything but
    Millions is now refused.
  - The refusal sits where `require_usd` refuses another currency: at assembly before any fetch
    (`mechanical`), and on the anchor's CIQ path (`anchor.ciq_bridge`, which re-raises it).
  - A panel stating no unit is not refused. The bridge's magnitude and re-read checks still
    screen it.
- **RA-D14** (`_stat_columns`, `_rc_columns`). Three reads went by column position, so a column
  swap, header included, swapped the values with nothing said:
  - Consensus's Target Price mean and median, also printed in `consensus_view`;
  - LT growth;
  - the target stats (`consensus_stats`: mean, median, high/low, number of estimates).

  Recent Changes (`revision_events`, and the date `estimates_as_of` reads) was read by index too.
  The auditor's cases: a Mean/Median swap printed SMPL's target as mean $14.00 / median $14.88,
  and a Broker Value Prior/Current swap reversed its Interest Expense revision. Each column is now
  found by its header text. A missing header leaves the read unread and says so, never
  positional. The one fixed anchor is column 0's 'Change Type', the row the header is found by.

**WHY.** Document 15, order 4: "an export in thousands printed as $M; target price and Recent
Changes read by column position". Done when: each A case is a passing test.

**HOW VERIFIED.**
- **Fail first.** `tests/test_ciq_units_and_headers.py` fails 7 of 7 on `origin/main`'s
  `vinci/`, run from the primary checkout's licensed folder, and passes here. The RA-D9 corpus
  negative fails there only because `require_millions` does not exist.
- **What the real-export pins do.** They restate SMPL's annual Income Statement unit line as
  Thousands, and swap SMPL's Mean/Median and Broker Value Prior/Current columns (header and
  values) in memory. Each has a constructed twin on the synthetic issuer that runs on CI.
- **$0 compare.** `consensus_view`, `consensus_stats`, `revision_events`, `estimates_as_of` and
  `require_millions` were dumped at both codes on the 36 folders on disk: 0 of 180 (folder,
  reader) cells differ. No synthesis request changes, so no panel is owed.
- **The censuses behind "no page moves."**
  - All 720 money sheets with an 'In … of' line state Millions, and all 72 Capital Structure
    Details sheets state 'Principal Due in Millions of' (Ratios and Multiples state none).
  - All 36 Recent Changes headers are the same ten labels in the same order.
  - All 36 Target Price rows sit directly under their Mean/Median header.

- **Review round 0 (`/code-review high --fix`), each fix behind a test that failed first.**
  - Capital Structure Details states its unit as 'Principal Due in Millions of …'. The
    `ciq.stated_unit` 'In … of' line never matched it, so a Thousands export of that sheet passed.
    It is now read (`_principal_unit`): 72 of 72 such sheets on the 36 folders state Millions.
  - `cli._machine_anchor` (anchor-backfill, anchor-retag) re-raised `CiqCurrencyError` but caught
    `CiqUnitError` as "no CIQ bridge" and anchored the name EDGAR-only. It re-raises it now.
  - `estimates_as_of` names a missing Recent Changes 'Date' header. Before, it said the log held
    no dated events.

**BOUNDARY.** The exports under the primary checkout's `data/manual/ciq/` on 2026-11-10: 36
ticker folders, the current exports only.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A page whose export states Thousands now stops at assembly instead of printing wrong figures.
  The operator re-exports in Millions. No such export exists today.
- **Not in this PR:** RA-D2 and RA-D4, order 4's other two CIQ-reader IDs. Both change what live
  pages print and what their synthesis requests carry:
  - RA-D2: GOOGL's, V's and NKE's `Dividend/sh` rows print the Ratios sheet's dividend GROWTH
    rate.
  - RA-D4: SMPL's FY guide given on the same date as its quarter guide is dropped.

  They are their own PR, which stops for the six-page panel check (RUNBOOKS §n).
- **Extraction version** `2026-11-10.unit-and-headers`; the drift pins are re-pinned.
