---
status: shipped
date: 2026-10-27
prs: [830]
supersedes:
superseded-by:
---

# The anchor's D&A reads the screen's guarded line and must be the filer's newest fiscal year — 225 cached filers' EDGAR D&A refused to the CIQ bridge, none reads another value; 5 of 27 pages move on re-assembly

**WHAT.** `anchor._latest_dep_amort` returns `(value, source, basis)` or the reason EDGAR has no
D&A. It no longer picks among the combined aliases and the `Depreciation` +
`AmortizationOfIntangibleAssets` split by vintage. It reads `concepts.current_annual(facts,
"dep_amort")`, the screen's reader:
- the alias walk, which already skips an abandoned alias for a current one (MC1);
- the split only where the filer proved it continues the combined line (#822: the same figure, to
  0.1%, in the latest year both carry, then unbroken);
- #817's check (not reported past by its concept) and #821's (at most one fiscal year behind the
  filer).

**Stricter than the screen: the D&A must be the filer's NEWEST fiscal year.** The anchor adds it to
LTM EBIT, so a year behind would make the EBITDA basis a two-year figure, the pairing #821
forbids.

**What a refusal does.** It returns the reason, never the stale combined figure. `_bridge_inputs`
then fills the hole from the CIQ workbook as before, stamped `vendor_bridge`.
- Its source says "EDGAR D&A withheld — <reason>" where EDGAR's figure was refused, including
  "no combined D&A line, so the split … has no year to be checked against" (CNXC, WERN).
- It keeps the old "no EDGAR D&A tag" where the filer tags no D&A at all.
- The UNKNOWN source names the reason.

**The source text.** The anchor's own split summing is retired. A split reads "(split, FY2025;
continues DepreciationAndAmortization, which stops at the year to 2024-09-30 — the same figure, to
0.1%, in the last year both carry)". The vintage note stays on a combined alias (the FUBO and EPAM
pins), and now counts only combined aliases.

**WHY.** Operator decision 2026-10-27, relayed: fix the anchor's split, which #822 left
unguarded.
- **The old reader took the split only where it was FRESHER than every combined alias.** That is
  exactly a stopped combined line continued by a split: the shape #822 guards in the screen.
- **Ecovyst's anchor read $76.4M for FY2025** from a split that was $68.4M against a combined
  $89.4M in FY2024.
- **The newest-year rule, by face validity.** Anchor D&A years against the filer's newest fiscal
  year, 2,161 cached filers:
  - 1,620 within 29 days;
  - one at 181 (a 10-Q's trailing column);
  - NONE from 300 to 349;
  - 11 at 350–371: Ecovyst, Grocery Outlet, CSW Industries, Accenture, Alto Neuroscience, Happen,
    Rayonier, Tenax, Trilogy Metals, Triller, i-80 Gold.

  The cutoff (`ANNUAL_STALE_DAYS`, a whole shortest fiscal year) sits at the top of that gap.
  Without it, Ecovyst's anchor would read its FY2024 combined $89.4M beside an LTM EBIT, the
  stale combined value the operator ruled out.

**DOES THIS SELECT ON FORM?** (CLAUDE.md, before any new gate.) No. The newest-year cutoff
selects on a PERIOD (how far the D&A year trails the filer's own newest fiscal year), and the
split is admitted on a FIGURE (#822). Neither keys on which tag or disclosure style a filer uses.
What it does do is send every refused name to CIQ, so a filer whose EDGAR tagging is unusual gets
the vendor's D&A, stamped as such, rather than a guess.

**HOW VERIFIED.**
- **Census, BEFORE → AFTER** on the same 2,161 blobs (BEFORE main 56500bb1, whose
  `_latest_dep_amort` is unchanged through 23a6b855; AFTER this branch):

  | anchor EDGAR D&A | all filers | read the split before | read a combined alias before |
  |---|---|---|---|
  | unchanged | 1,593 | 0 | 1,593 |
  | refused (→ the CIQ bridge where a workbook exists) | 225 | 156 | 69 |
  | same value, source text changed | 28 | 13 (the split label) | 15 (the vintage note no longer counts the split) |
  | value changed to another value | 0 | 0 | 0 |
  | none before or after | 315 | — | — |
  | **total** | 2,161 | 169 | 1,677 |

- **Why the 225 are refused:**
  - 107 have no combined line to continue, or no tag at all;
  - 90 are more than a fiscal year behind the filer;
  - 17 have been reported past by their concept;
  - 11 are one fiscal year behind (the newest-year cutoff).

  Among the 169 split-readers:
  - **Merck** $5,845M: refused, its combined line stops at FY2019 (2,192d behind).
  - **Fiserv** $2,969M: refused, its combined line stops at FY2023.
  - **Ecovyst** $76.432M: refused, its combined FY2024 is a year behind.
  - **Scotts** $75.0M: kept, its split proven. The label changes.
- **The 27 committed pages,** each read as filed by its own `assembled_at` and on today's blob
  (both agree). Five move on re-assembly; none is re-assembled here.
  - The CIQ figures are what `anchor.ciq_bridge` reads from each name's workbook
    (`mosaic-theory-ta/data/manual/ciq/<T>`, read 2026-10-27).
  - Each is the workbook's LAST annual column, which is `LTM 12 months` in all four.

  | page | committed anchor D&A ($M) | after |
  |---|---|---|
  | CNXC | 660.433, EDGAR split FY2025 (no combined line ever) | CIQ bridge 642.82 (LTM to 2026-08-31), −2.7% |
  | WERN | 286.4, EDGAR split FY2025 (no combined line ever) | CIQ bridge 313.717 (LTM to 2026-06-30), +9.5% |
  | FUBO | 38.548, EDGAR combined FY2024 (reported past to 2026-06-30) | CIQ bridge 98.564 (LTM to 2026-06-30) |
  | ORKA | 0.015, EDGAR combined FY2023 (731d behind FY2025) | CIQ bridge 0.134 (LTM to 2026-06-30) |
  | AMZN | 75,200, unchanged | the vintage note reads "over 1 staler candidate(s)", was "over 2" |

  - GOOGL's bridged D&A keeps its value and source; only its basis label changes (cost 1). MVST's text is unchanged.
  - **The relay expected CNXC and WERN to keep their committed figures through the bridge
    ($660.433M; $286.321M vs $286.4M).** Those are the workbooks' FY25 columns; the bridge reads
    the last column, the LTM. That LTM matches the LTM EBIT it is added to better than a fiscal
    year does. But see cost 1.
- **Pins: 6 new** (`tests/test_anchor_dep_amort.py`) on frozen real filers
  (`tests/fixtures/retagged_legs/`; CNXC and FUBO cut for it, checked against the full blob).
  - Scotts positive: the split names the line it continues.
  - Ecovyst negative: neither the split nor the year-old combined line is read; the UNKNOWN source
    names why, and the bridge says "withheld".
  - CNXC: no combined line, so the bridge fills, with CNXC's real CIQ figure.
  - FUBO: reported past.
  - The cutoff sits in its gap.
- **Existing pins:**
  - The FUBO and EPAM vintage pins (`tests/test_ciq_balance.py`) are green.
  - Three tests changed by design, each docstring saying why:
    - `test_dep_amort_split_requires_the_same_fiscal_period` (test_anchor) now pins alignment
      on a split that continues a combined line, and the CNXC shape refused;
    - `test_dep_amort_takes_a_fresher_split_over_a_stale_combined` became
      `…_never_reads_an_unproven_split_or_a_stale_combined`;
    - `…_absent_everywhere_is_none_not_zero` now expects `NO_DEP_AMORT`.
- **Pins on committed anchors, updated to the recorded moves** (not loosened):
  - `tests/test_anchor_assembly_ciq_bridge.py` (#816) froze ORKA's backfilled block. A fresh
    assembly now differs in exactly `d_and_a` (EDGAR FY2023 $0.015M → the cut's CIQ $0.134M) and
    `data_quality_detail` (the vendor list adds `d_and_a`). Every other field must still match,
    and the move itself is asserted (`MOVED_BY_THE_DA_GUARD`). The dropped-input test now checks
    that the vendor list does not name the dropped input, since ORKA's D&A is legitimately
    vendor-filled.
  - `tests/test_dilution_denominator.py`: CNXC and WERN join `BRIDGE_ONLY_ANCHORS`, which that
    test's own message asks for, since their R1 base now needs the workbook's D&A.
- **Mutation: 9 mutants in a scratch copy, 9 killed:**
  - D1: no newest-year cutoff.
  - D2: the screen's cutoff.
  - D3: no current-year check.
  - D4: the old unproven split.
  - D5: the vendor text always "no EDGAR D&A tag".
  - D6: an UNKNOWN that never names the reason.
  - D7: the vintage note dropped.
  - D8: a split carrying the vintage note.
  - D9: a filer with only the split reported as having no D&A tag.
- **Suite:** ruff + `mypy --strict vinci` clean, `pytest -m "not network"` 7,321 passed, 533 skipped, 0 failed (the final code rebased on main 3ab4747f, with this record and STATE.md).

**BOUNDARY.**
- **Census:** the shared SEC cache `/Users/work/Documents/GitHub/mosaic-theory-ta/data/cache/sec`,
  read-only, 2,161 companyfacts fetched 2026-08-12..2026-10-26, today's blob, measured
  2026-10-27.
- **Units:**
  - one filer, for `_latest_dep_amort`'s result;
  - one filer's D&A year against the newest annual period of its eight flow concepts, for the
    cutoff gap.
- **Pages:** the 27 under `data/dossiers/` at 23a6b855, re-checked at 3ab4747f (after #826 rewrote the pages): the same five move.
- **CIQ figures:** the workbooks in the `mosaic-theory-ta` copy, read 2026-10-27, not
  hash-checked against Drive.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The bridge's D&A is the workbook's LAST annual column, not a fiscal year — now stated.**
   - `ciq_balance` reads the annual Cash Flow sheet's last column. It is `LTM 12 months` on 33
     of the 35 workbooks on file (2026-10-27); NKE's is a fiscal year, and MCK's carries no
     header.
   - The anchor labelled the filled D&A "consolidated latest FY" whatever it was.
   - **Fixed in review of #830 (Codex P2; operator ruling).** The period is a STRUCTURED value
     read off the column's own header cell: `ciq_balance.header_period` → `CiqFact.period`
     ("LTM" | "FY") and `CiqFact.period_end`. The anchor's basis names it
     (`anchor.ciq_da_basis`), for example "consolidated trailing twelve months to 2026-08-31
     (CIQ workbook, vendor basis)". A header that states nothing says so, never "latest FY".
   - The CIQ fact's own basis text now reads "the annual sheet's latest column".
   - **Measured on the real workbooks:** CNXC LTM to 2026-08-31; WERN, GOOGL and ORKA LTM to
     2026-06-30.
   - GOOGL's committed vendor D&A changes only that label at re-assembly. #816's frozen cut
     (`tests/fixtures/anchor_ciq_bridge.json`) now carries the period beside GOOGL's and ORKA's
     facts, as `extract` returns it.

**THE ANCHOR'S INPUTS AND THEIR PERIODS, after this change** (operator ask, review of #830):

| input | read from | period |
|---|---|---|
| D&A, EDGAR | `concepts.current_annual`, newest-year cutoff | the filer's newest fiscal year (10-K), or a 10-Q's trailing column where the filer tags one (AMZN) |
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
- **24 of the 27 committed anchors carry an EDGAR fiscal-year D&A,** so on those pages each of
  the three pairs two periods. AMZN's 10-Q trailing column, GOOGL's CIQ LTM and MVST (no D&A) are
  the three exceptions.
- This predates the PR. It moves CNXC, WERN, FUBO and ORKA onto an LTM D&A, so for them the legs
  now match.
- **The CIQ FCF fill can pair the same way.** It takes LTM OCF less last-column capex. That is LTM
  − LTM on 33 workbooks, but LTM − FY on a workbook like NKE's, still labelled "trailing twelve
  months". No committed page's FCF is filled from such a workbook today.
- **Recorded in STATE.md §5.0 row 11 as open.** The fix is a period-matched D&A for the anchor
  (an EDGAR trailing D&A built from 10-K and 10-Q figures, or the CIQ LTM where present), and
  it moves R1 bases.

2. **A filer that never tagged a combined line has no EDGAR D&A** (107 cached). Its split is
   unverifiable from companyfacts alone. CNXC's split equals its CIQ FY25 exactly and WERN's is
   within 0.03%, so for those two the split was right; but nothing in the filings shows it, and
   the rule takes no exception.
