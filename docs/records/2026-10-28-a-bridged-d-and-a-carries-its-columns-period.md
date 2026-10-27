---
status: open
date: 2026-10-28
prs: []
supersedes:
superseded-by:
---

# A bridged D&A carries its column's period as a structured value — the trailing twelve months to the header's date, or a fiscal year, never "latest FY"; and the anchor pairs a fiscal-year D&A with LTM figures on 24 of 27 pages

**WHAT.** When the anchor's EDGAR D&A is withheld, the CIQ bridge fills it. Since #830, that
happens at re-assembly for CNXC, WERN, FUBO and ORKA, and it already does for GOOGL.
- `ciq_balance` reads the annual Cash Flow sheet's LAST column.
- **The period is now a STRUCTURED value read off that column's own header cell.**
  `ciq_balance.header_period` turns CIQ's `LTM\n12 months\nAug-31-2026` or
  `12 months\nMay-31-2026` into `("LTM" | "FY" | None, end date)`, through the shared helpers
  `ciq_sheets._is_ltm` and `ciq.excel_date`. `ciq_balance.pick_with_period` and `_cf_cell` carry
  it to `CiqFact.period` / `CiqFact.period_end`. These are new, defaulted fields; every existing
  constructor stays valid.
- **The anchor's basis names it** (`anchor.ciq_da_basis`):
  - "consolidated trailing twelve months to 2026-08-31 (CIQ workbook, vendor basis)";
  - "consolidated fiscal year to …" for a fiscal-year column;
  - "period not stated in the CIQ workbook's column header" where the header says nothing.

  Never "latest FY". The CIQ fact's own basis text now reads "the annual sheet's latest column".
- **This replaces the hedged label #830 merged with** (50d1cc5a: "LTM where the workbook carries
  one, else its latest fiscal year"). The operator ruled the period be carried, not described.

**WHY.** Codex P2 on #830 ("Label CIQ D&A with its actual trailing period"), and the operator's
ruling (2026-10-27): a wrong period stamp on an anchor input is the error class the house rules
guard hardest, since it prints as the basis of the EBITDA leg. The fix uses the column's own
header, never a label built for display (CLAUDE.md: parsers consume structured values).

**HOW VERIFIED.**
- **Every workbook on file** (35, in `mosaic-theory-ta/data/manual/ciq`, read 2026-10-27): the
  annual Cash Flow sheet's last column is `LTM 12 months` on 33. NKE's is a fiscal year
  (`12 months\nMay-31-2026`), and MCK's header did not read.
- **`extract` on the real workbooks now returns:**

  | name | D&A ($M) | period |
  |---|---|---|
  | CNXC | 642.82 | LTM to 2026-08-31 |
  | WERN | 313.717 | LTM to 2026-06-30 |
  | GOOGL | 25,536 | LTM to 2026-06-30 |
  | ORKA | 0.134 | LTM to 2026-06-30 |

  These are the values #830's record states, now with their period.
- **Tests that failed on 50d1cc5a, then passed** (`tests/test_anchor_dep_amort.py`):
  - `test_the_ciq_period_is_read_off_the_columns_own_header`: CNXC's, WERN's and NKE's real
    header cells, an empty one, and a row picked with its period.
  - `test_a_bridged_d_and_a_is_stored_with_its_trailing_period`: end to end on CNXC's and WERN's
    frozen companyfacts (`tests/fixtures/retagged_legs/`, WERN cut for it). EDGAR's D&A is
    withheld, the bridge fills, and the stored basis is the trailing twelve months to each
    column's date. A fiscal-year column and a dateless header are each stated as such.
- **#816's frozen cut** (`tests/fixtures/anchor_ciq_bridge.json`) now carries the period beside
  GOOGL's and ORKA's D&A facts, as `extract` returns it. Its test pins GOOGL's re-assembled
  basis to "trailing twelve months to 2026-06-30"; value and source are unchanged.
- **Suite:** ruff + `mypy --strict vinci` clean, `pytest -m "not network"` 7,475 passed, 533 skipped, 0 failed (on main e388b0f2, with this record and STATE.md).

**THE ANCHOR'S INPUTS AND THEIR PERIODS, after this change** (operator ask):

| input | read from | period |
|---|---|---|
| D&A, EDGAR | `concepts.current_annual`, newest-year cutoff (#830) | the filer's newest fiscal year (10-K), or a 10-Q's trailing column where the filer tags one (AMZN) |
| D&A, CIQ bridge | the annual sheet's last column | LTM to the header's date where the workbook carries one (33 of 35), else a fiscal year; now stated |
| LTM revenue | the page's committed `financial_summary` LTM column | LTM |
| LTM EBIT | the same, `_ltm_ebit_from_fs` | LTM |
| FCF, EDGAR | `current_pair`, OCF − capex | one fiscal year, or one 10-Q trailing column, both legs |
| FCF, CIQ bridge | `ltm_ocf` − the annual sheet's last-column capex | OCF LTM; capex LTM on 33 of 35, a fiscal year on NKE — labelled "trailing twelve months" either way |
| net debt | EDGAR balance sheet (or CIQ's) | one instant, the latest balance-sheet date |
| diluted shares | the latest 10-Q quarter's diluted weighted average | the latest quarter |

**FOUND, NOT FIXED — the anchor pairs an LTM leg with a fiscal-year D&A.**
- **Three computations add or divide D&A beside an LTM figure:**
  - `market_reconciliation`'s recorded EBITDA (LTM EBIT + D&A);
  - `recorded_d_and_a_check` (D&A ÷ LTM revenue);
  - R1's base (`scenario_value`: LTM revenue × margin, + D&A).
- **24 of the 27 committed anchors carry an EDGAR fiscal-year D&A** (main e388b0f2), so on those
  pages each of the three pairs two periods. AMZN's 10-Q trailing column, GOOGL's CIQ LTM and
  MVST (no D&A) are the exceptions.
- This predates #830. #830 moves CNXC, WERN, FUBO and ORKA onto an LTM D&A, where the legs now
  match.
- **The CIQ FCF fill can pair the same way.** It takes LTM OCF less last-column capex: LTM − LTM
  on 33 workbooks, LTM − FY on one like NKE's, still labelled "trailing twelve months". No
  committed page's FCF is filled from such a workbook today.
- **Open in STATE.md §5.0 row 11.** The fix is a period-matched anchor D&A (an EDGAR trailing D&A
  built from 10-K and 10-Q figures, or the CIQ LTM where present), and it moves R1 bases.

**BOUNDARY.**
- Workbooks: the 35 under `mosaic-theory-ta/data/manual/ciq`, read 2026-10-27, not hash-checked
  against Drive.
- Pages: the 27 under `data/dossiers/` at main e388b0f2.
- Unit: one workbook (column census) or one committed anchor (pairing count).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. GOOGL's committed vendor D&A changes its basis label at re-assembly, from "consolidated latest
   FY" to "consolidated trailing twelve months to 2026-06-30 (CIQ workbook, vendor basis)". Its
   value and source do not change.
2. MCK's header did not read: its bridged D&A would print "period not stated", which is true.
