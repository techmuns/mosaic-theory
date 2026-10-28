---
status: shipped
date: 2026-10-28
prs: [836]
supersedes:
superseded-by:
---

# The anchor's D&A covers the window its LTM EBIT and revenue cover — the same twelve months, ending on the same day, or none; R1 bases move on 14 pages, no guard outcome changes

**WHAT.** The anchor's D&A is now the D&A over the page's own window: the twelve months its LTM
EBIT and LTM revenue cover.
- **The window** (`anchor._page_window`) is the annual table's last actual column, the one
  `_ltm_ebit_from_fs` and `_ltm_revenue_from_fs` read. Its end and its kind (LTM or a fiscal
  year) come from `financial_summary.statement_reconciliation`, which states them for every
  column. All 27 committed pages state it.
- **EDGAR's D&A over that window** (`anchor._window_dep_amort`):
  - the guarded annual (`_dep_amort_point`, #830) where it ends on the window's end. That covers a
    fiscal-year window (NKE's FY26) and a filer's own 10-Q trailing column (AMZN).
  - Otherwise, for a trailing window, the fiscal year + year-to-date − prior year-to-date on one
    tag, through `statement_recon.twelve_months`. That is the builder that already sets CIQ's
    columns against the filings, exposed rather than duplicated.
  - Its end must sit within 7 days of the window's end (`WINDOW_SLACK_DAYS`, `statement_recon`'s
    rule for a 52/53-week year).
- **The CIQ bridge** fills D&A only with a figure over the same window: the same kind of twelve
  months, ending on the same day (`_ciq_on_window`, reading #834's structured period). Otherwise
  the D&A is UNKNOWN, with both reasons. It is never a fiscal-year D&A.
- **The CIQ FCF fill** reads OCF and capex WITH their column's period (`ciq_balance.extract`, OCF
  keeping `ltm_ocf`'s rounding). It pairs them only when they are one period (`_one_period`), and
  labels it ("trailing twelve months to 2026-06-30", "fiscal year to …"). An LTM OCF less a
  fiscal-year capex is refused, naming both.
- **Not changed:** `midcycle.R1_FORMULA` (a record stamp, #762), sealed scenario records under
  `scenarios/` (no file touched; a sealed record keeps the inputs it was sealed with), and the
  screen.

**WHY.** Operator decision (2026-10-28), on #834's found-not-fixed. The anchor combines D&A with an
LTM figure in three places:
- `market_reconciliation`'s recorded EBITDA (LTM EBIT + D&A);
- `recorded_d_and_a_check` (D&A ÷ LTM revenue);
- R1's base (`scenario_value`: LTM revenue × margin, + D&A).

It read the latest fiscal year's D&A, so on 24 of the 27 committed anchors those three were figures
whose legs covered two windows. A figure like that never existed. It is the same rule #821 applied
to the screen, reaching R1's base value.

**HOW VERIFIED.**
- **Real run, the decision path.** `compute_anchor` on all 27 committed pages, BEFORE (#834's tip,
  4e9b2b5e) and AFTER (this branch), on the SAME inputs: today's companyfacts from the shared SEC
  cache, and the same CIQ bridge read of each workbook (`mosaic-theory-ta/data/manual/ciq`,
  read-only, 2026-10-28). Only the code differs. The 24 committed anchors whose D&A was a fiscal
  year:

  | page | committed D&A ($M, FY) | after ($M) | read as | R1 base before → after | reconciliation | recorded-D&A check |
  |---|---|---|---|---|---|---|
  | AORT | 22.458 | 23.352 | EDGAR FY + YTD − prior YTD | 25.3879 → 26.0844 | agree → agree | not_run → not_run |
  | BRBR | 18.6 | 19.8 | EDGAR FY + YTD − prior YTD | 57.765 → 57.9689 | agree → agree | agree → agree |
  | BURL | 417.871 | 449.908 | EDGAR FY + YTD − prior YTD | 327.6008 → 335.9511 | agree → agree | not_run → not_run |
  | CNXC | 660.433 | 642.82 | CIQ LTM (since #830) | 82.7509 → 82.7509 | agree → agree | not_run → not_run |
  | EPAM | 124.811 | 125.74 | EDGAR FY + YTD − prior YTD | 403.8351 → 404.2908 | agree → agree | not_run → not_run |
  | FUBO | 38.548 | 98.564 | CIQ LTM (since #830) | — | — | — |
  | IT | 200.309 | 194.98 | EDGAR FY + YTD − prior YTD | 383.8594 → 381.8862 | agree → agree | agree → agree |
  | LLY | 1,997 | 2,099 | EDGAR FY + YTD − prior YTD | 699.6511 → 702.6319 | agree → agree | agree → agree |
  | NCNO | 42.255 | 41.633 | EDGAR FY + YTD − prior YTD | — | — | — |
  | NFLX | 333.389 | 372.414 | EDGAR FY + YTD − prior YTD | 53.5401 → 53.9059 | agree → agree | not_run → not_run |
  | NKE | 747 | 747 | EDGAR FY (the window IS FY26) | 101.0715 → 101.0715 | agree → agree | not_run → not_run |
  | ORKA | 0.015 | 0.134 | CIQ LTM (since #830) | — | — | — |
  | PARR | 144.325 | 143.941 | EDGAR FY + YTD − prior YTD | 47.8638 → 47.8039 | agree → agree | not_run → not_run |
  | ROST | 509.391 | 539.844 | EDGAR FY + YTD − prior YTD | 166.1793 → 167.5944 | agree → agree | not_run → not_run |
  | SMPL | 21.431 | 24.047 | EDGAR FY + YTD − prior YTD | 44.8347 → 45.3648 | agree → agree | not_run → not_run |
  | TECX | 1.375 | 1.264 | EDGAR FY + YTD − prior YTD | — | — | — |
  | TGT | 3,134 | 3,173 | EDGAR FY + YTD − prior YTD | 159.274 → 160.042 | agree → agree | not_run → not_run |
  | TJX | 1,247 | 1,319 | EDGAR FY + YTD − prior YTD | 131.1019 → 132.1391 | agree → agree | not_run → not_run |
  | UBER | 719 | 745 | EDGAR FY + YTD − prior YTD | — | — | — |
  | V | 1,220 | 1,342 | CIQ LTM (EDGAR's year-to-date stops at 2026-03-31) | — | agree → agree | agree → agree |
  | VITL | 9.254 | 9.635 | EDGAR FY + YTD − prior YTD | — | differ → differ | differ → differ |
  | VRRM | 114.08 | 115.815 | EDGAR FY + YTD − prior YTD | 21.7803 → 21.9358 | agree → agree | agree → agree |
  | WERN | 286.4 | 313.717 | CIQ LTM (since #830) | 35.7058 → 35.7058 | agree → agree | not_run → not_run |
  | WLK | 1,178 | 1,170 | EDGAR FY + YTD − prior YTD | 116.1475 → 115.6523 | agree → agree | not_run → not_run |

  Of the 24: 18 read EDGAR's FY + YTD − prior YTD, five read CIQ's LTM (CNXC, WERN, FUBO and
  ORKA since #830; V here), and NKE keeps its fiscal year because its window is one.

  "—" is an anchor whose R1 recipe does not resolve (no base, or no guard run), before and after
  alike. **R1 bases move on 14 pages, the largest AORT +2.74% (BURL +2.55%). No reconciliation or
  recorded-D&A outcome changes on any page.** The three pages not in the table (AMZN's 10-Q
  trailing column, GOOGL's CIQ LTM, MVST's CIQ LTM) are unchanged.
- **Pages that move at re-assembly** (none re-assembled; they refresh in the November pass):
  - the 19 whose anchor D&A changes under this code (the 18 EDGAR rows above, and V);
  - the 14 of those whose R1 base moves, listed in `tests/test_dilution_denominator.py`'s
    `ANCHORS_AWAITING_BACKFILL`, which that test exists to hold;
  - CNXC, WERN, FUBO and ORKA, which moved with #830.
  - IT's vendor-filled FCF keeps its value and changes its basis text, from "trailing twelve
    months (vendor basis)" to "trailing twelve months to 2026-03-31 (vendor basis)": the
    one-period fill names its period. IT is the one committed anchor whose FCF CIQ fills.
- **Pins** (`tests/test_anchor_ltm_window.py`, on frozen real companyfacts in
  `tests/fixtures/ltm_window/`, each checked against the full blob at cut time):
  - **positive:** BURL's $449.908M over the twelve months to 2026-08-01, where the anchor read
    FY2025's $417.871M; a fiscal-year window reading the fiscal year;
  - **negative:** V, with no D&A year-to-date reaching 2026-06-30, refused and never its FY2025
    $1,220M, then CIQ's LTM over the same window filling it;
  - the CIQ FCF fill: one period filled and named, LTM − FY refused;
  - `extract` carrying OCF's and capex's periods;
  - the window read off the LAST actual column;
  - a same-day CIQ figure of the wrong kind refused.
- **Existing pins moved to the window rule** (test-file changes, no behaviour loosened):
  - `test_band_guards`'s committed-shape synthetic page now states its window;
  - `test_band_checks`'s CIQ stand-in carries that window's period;
  - `test_anchor_dep_amort`'s pages state CNXC's and WERN's real windows. A new pin there: a page
    with no window, or a CIQ figure off by a quarter, gets no D&A.
- **Mutation: 9 mutants in a scratch copy, 9 killed:**
  - W1: the bridge reading the fiscal year again;
  - W2: no composition;
  - W3: any end matching;
  - W4: CIQ filling whatever its window;
  - W5: the kind of twelve months not compared;
  - W6: the FCF fill pairing any two periods;
  - W7: `extract` dropping the legs' periods;
  - W8: no window falling back to the fiscal year;
  - W9: the window read off the first column.
- **Suite:** ruff + `mypy --strict vinci` clean, `pytest -m "not network"` 7,508 passed, 534 skipped, 0 failed (rebased on main 2c0946c9, with this record and STATE.md).

**BOUNDARY.**
- **Real run:** the 27 pages under `data/dossiers/` at 4e9b2b5e (#834's tip), re-run at main
  2c0946c9 after #831 rewrote nine pages — identical results, each page's committed mechanical layer, today's companyfacts (shared SEC cache, fetched
  2026-08-12..10-26) and its CIQ workbook. One anchor per row.
- "Committed D&A" is the value on the page; "before" is #834's code on today's inputs. The two can
  differ where inputs moved since assembly, which is why bases are compared before → after on
  the same inputs.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A name without a CIQ pull whose EDGAR cannot reach the window gets no D&A, and so no R1
   base.** That is honest, and every dossier name has a CIQ pull. Falsifier: a committed anchor
   left with an UNKNOWN D&A that its workbook could have filled over the same window.
2. **D&A's split substitute (#822) is not composed over a window.** `statement_recon` builds on
   one tag, never a sum. A filer whose combined line stopped gets CIQ's LTM instead. Today CIQ
   fills seven pages: CNXC, WERN, FUBO, ORKA, V, GOOGL and MVST.
3. **The window is the page's committed column.** A page assembled before
   `statement_reconciliation` existed would state none and get no D&A. None of the 27 is such a
   page.
