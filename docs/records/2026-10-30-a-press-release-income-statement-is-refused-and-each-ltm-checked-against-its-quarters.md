---
id: 2026-10-30-press-release-ltm
status: open
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# A CIQ press-release Income Statement is refused at assembly, and each annual-summary LTM is checked against its four quarters

**WHAT.**
- **The column's status is a parsed field.** `ciq_sheets.HeaderPeriod.status` is `filed`,
  `reclassified`, `restated` or `press_release`, read from CIQ's own header words. The three
  consumers that read `'Reclassified'` off a label (`_fin_periods`, `_reclassified_cols`,
  `_period_label`) now read the field. A test refuses any `vinci/` line that tests a status word
  against text.
- **The refusal.** `ciq_sheets.require_filed_income_statement` raises `CiqPreliminaryError` (a
  `CiqAmbiguousError`) when a press-release column is among the Income Statement columns a page
  reads as the latest of their kind: in each Financials export, every LTM column, plus the newest
  fiscal year and the newest quarter by the header's date. `assemble_mechanical` calls it right
  after the currency refusal, before anything is fetched. The message names each column and its
  period end. It says to re-export BOTH Financials workbooks once CIQ has processed that period's
  10-Q, or the 10-K at a fiscal year end.
- **The value check.** `vinci/dossier/ltm_quarters.py` runs in `assemble_one` right after the
  mechanical layer, before any model call. It covers each ADDITIVE Income Statement row on the
  annual summary: revenue, EBITDA, EBIT, net income, and the unusual items the summary surfaces.
  It skips EPS rows, margins and growth. Each row's LTM is compared with the sum of the quarterly
  export's four quarters ending on the LTM's own date. The quarters are found by the month each
  header's date is named for, never by position. The tolerance is 2%, or 0.5 $M, which is half
  the whole million the page prints. Outcomes:
  - **agree**: within tolerance on all four quarters;
  - **differ**: the quarters carrying a figure disagree;
  - **unverified**: a quarter reads `-`, and the quarters carrying a figure reconcile;
  - **not_run**: no quarter carries a figure, or a quarter has no column or two.

  Every outcome other than agree is a QA flag (`ciq-ltm-quarters:`, `flags._QA_MARKERS`). The
  build is refused only when a row the 19c guard would demand (`demanded_material_figures` on a
  `_mark_material` copy) is `differ` or `not_run`.
- Extraction version `2026-10-30.press-release-ltm` (the Python table and its `dossier.js` twin).
  Drift pins re-pinned; `ltm_quarters.py` joins the watched set.

**WHY.** CIQ builds the annual LTM as the fiscal year plus the current year-to-date less the prior
one. Under a `LTM / Press Release` header, the current year-to-date comes from the earnings
release, which carries fewer lines than the 10-Q. GOOGL's 2026-10-29 export shows both failures:
- **A line the release omits carries the last fiscal year.** The gain on investments reads FY25's
  24,620.0 in the LTM to Sep-30-2026. Its quarterly export reads 2,353.0 / 36,804.0 / 98,999.0
  for Q4-25 to Q2-26, with Q3 `-`.
- **A line the release reports only in aggregate lands in a catch-all.** Other non-operating reads
  102,541.0 against quarters summing to −9,267.0, so EBT excluding unusual items reads 263,017.0
  against 149,481.0, and normalized diluted EPS reads 13.36 against 7.61.

The filed export it replaced (LTM to Jun-30-2026, `ciq-archive/replaced-2026-10-29b`)
reconciles: the gain is 149,012.0, exactly its four quarters, and other non-operating is 96.0
against 97.0. `_fin_short` printed a bare `LTM` for both columns. So the page, the 19c materiality
guard and the anchor's LTM EBIT/revenue read the preliminary column as a filed one.
`book_value_per_share` already named the same issue for balance sheets and stamped it there alone.

**The status gate reads the measured CAUSE. The value check is the paired VALUE test** (CLAUDE.md:
pair every presence or count guard with a check on the values). The value check catches what the
status cannot see: NFLX's LTM to Sep-30-2026 is FILED, and its merger row reads −2,800.0 while the
quarterly export books +2,800.0 in Q1 2026. That quarterly export is self-consistent, because its
EBT including unusual items (17,700.3) and its net income (14,766.7) both sum to the LTM's exactly.
The annual LTM's EBT excluding unusual items (20,500.3) exceeds its quarters' sum (14,900.3) by
5,600.0, which is 2 × 2,800.0. The annual LTM carries the item with its sign flipped.

**DOES THIS SELECT ON FORM?**
- **The status gate:** it reads a status word, but the word is the measured cause, not a proxy.
  The filed column reconciles, and the press-release column of the same name does not.
- **The value check:** it selects on the figures alone, with one decision made so it does not
  select on form. A `-` quarter never refuses on its own. CIQ writes `-` for a quarter with no
  such item on one row and `0.0` on the next: CNXC's goodwill impairment is −1,523.3 and −1,050.0
  in two quarters, `-` in one and 0.0 in another, and it sums to its LTM of −2,573.3 exactly.
  Refusing on the `-` would refuse CNXC, MVST and WLK permanently on how CIQ writes an empty
  quarter. Every `-` is still a QA flag, as ruled.

**Two readings of the ruling, stated so they can be overruled.**
1. **The quarterly export's "newest FY column" is read as its newest QUARTER.** A quarterly export
   carries no LTM or fiscal-year column. Over the corpus, every export with a press-release
   newest quarter also has a press-release annual LTM or newest fiscal year (GOOGL, LLY, ONON,
   SMPL), so this reading changes no outcome today.
2. **A material row that cannot be checked refuses.** This covers no quarter carrying a figure,
   or a quarter with no column. It is the house rule that a guard refuses when it cannot look
   (audit D-D5). It refuses no folder in the corpus.

**HOW VERIFIED.**
- **Corpus run with the production code**, over the 34 non-test folders of the assembler copy
  (`mosaic-theory-ta/data/manual/ciq`) plus GOOGL, LLY and NKE in
  `ciq-archive/replaced-2026-10-29b`. Materiality used `implied_valuation`'s market cap, the
  figure assembly hands the marker.
  - The status gate refuses 4 live folders: GOOGL, LLY (the 2026-10-29 exports; LTM and Q3 to
    Sep-30-2026), SMPL (newest fiscal year Aug-29-2026, no LTM column) and ONON (LTM and Q1 to
    Mar-31-2026). ONON is refused earlier by `CiqCurrencyError`.
  - The value check refuses GOOGL (gain row), NFLX (merger row) and WAT (merger row: LTM −459.0
    against −346.0, no page).
  - Pins as the brief set them: GOOGL's filed export passes with no flag on the gain row; NKE's
    restructuring (−385.0 against −311.0 on two quarters) is flagged and not refused; ROST and
    TJX pass, each with one `unverified` flag (other unusual items in one quarter, `-` in three).
- **Frozen pins** (`tests/test_ciq_press_release_ltm.py`, 39 tests on
  `tests/fixtures/ciq_ltm_quarters.json`, cut from the real exports; header rows whole, values
  only in the pinned cells). Refused: GOOGL, LLY, SMPL. Passes: GOOGL filed, NFLX, NKE, ROST,
  TJX, CNXC. Also pinned:
  - the value refusal on NFLX and on GOOGL's release gain;
  - CNXC's material `-` that reconciles, which does not refuse;
  - by date, never position: GOOGL's filed annual beside the later quarterly export still agrees;
  - both call sites, by AST, before the first spend.
- **Mutation:** six mutants, all killed. They dropped the status word, deleted the refusal call,
  picked quarters by position, refused on a `-`, deleted the value refusal, and set the tolerance
  to 30%.
- Incident→invariant (shipped Y): `test_a_press_release_income_statement_is_refused`,
  `test_assembly_refuses_before_it_reads_anything`,
  `test_a_material_ltm_its_quarters_contradict_refuses_on_a_filed_column`,
  `test_assembly_checks_before_it_spends_and_refuses_on_the_19c_selection`.

**THE CORPUS RUN'S FLAGS (34 live folders, 219 rows checked).** 126 agree, 37 differ, 50
unverified, 6 not checked, plus SMPL's one "not run" (no LTM column): 94 QA flags. The differ rows
on filed columns include core rows, which are never material and only flag:
- BDX revenue 22,484.0 against 20,074.0 (10.7%);
- BRBR EBITDA 17.2%;
- WAT EBIT 13.6%;
- WLK EBIT 120.0 against 53.0.

**THE BALANCE SHEET AND CASH FLOW (census, not refused).** Press-release columns sit in exactly
the exports whose Income Statement is refused: GOOGL, LLY, ONON and SMPL now, and UBER's
2026-10-11 export (`replaced-2026-10-11`). ONON reports its Q1 and Q3 by release alone, so twelve
of its quarterly columns per statement are permanently `Press Release`. A defect there IS
measured. UBER's press-release column to Jun-30-2026 against the filed column that replaced it:
- **Balance sheet:** 11 of 48 rows differ (over 2% or 0.5 $M). Net Debt reads 9,340.0 against
  4,744.0, and accrued expenses 11,330.0 against 7,945.0.
- **Cash flow:** 3 of 31 annual LTM rows differ and 6 of 33 quarterly rows.
- **Income statement:** 5 of 53 annual LTM rows differ and 7 of 48 quarterly rows.

Widening the refusal changes no outcome on the corpus, because every such export is already
refused. It is the operator's call.

**BOUNDARY.**
- Every count: measured 2026-10-30 at main `1c5df21b` plus this branch, on the assembler copy as
  synced 2026-10-30. The six held test-pack folders are excluded.
- Status census: 5,955 Financials header cells (Income Statement, Balance Sheet, Cash Flow; both
  exports) over the live folders and the `replaced-2026-10-11`, `-20`, `-26`, `-28`, `-29`,
  `-29b` and `-30` archives. LLY and MCK in `replaced-2026-10-29` were refused by the loader
  (`CiqMislabelledError`) and are not in it.
- Value check: one row per additive annual-summary Income Statement row with an LTM figure. The
  window is the four quarters ending on the LTM's date, the unit is $M, and the tolerance is 2%
  or 0.5 $M.
- UBER comparison: same-dated columns of two exports, rows present in both, same tolerance.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **GOOGL waits** for the operator to re-export both Financials workbooks after CIQ processes its
  Q3 10-Q (filed 2026-10-29).
- **LLY's committed page (#867) sits on the press-release column.** Other unusual items show
  FY25's −484.0 against −1,066.1 on its three filed trailing quarters. Asset writedown shows
  −885.0 against −303.0 in Q3 alone. The anchor reads a preliminary LTM EBIT and revenue (each
  within 2% of its quarters). LLY owes one re-assembly after its 10-Q is processed.
- **NFLX's committed page (#867) states the merger row as a −2,800.0 charge.** Its bear point says
  the charge "flattered" net income. Its next assembly is refused until the two exports agree.
  Which export is right is the operator's call, with the arithmetic above.
- **SMPL** is refused at its newest fiscal year, consistent with row 36.
- **Committed pages are not touched;** the refusal is at assembly.
- **Not covered:**
  - `anchor-backfill` (`ciq_bridge`) and the refresh transforms read the same workbooks and do
    not refuse a press-release column;
  - a press-release balance sheet in an export whose Income Statement is filed (none on the
    corpus).
- **Falsifiers:**
  - a filed LTM that the quarters contradict on a material row where the quarterly side is the
    wrong one (NKE's shape, but material) would refuse a correct page, and the operator then
    reads both exports;
  - CIQ heading a preliminary column with a word other than `Press Release` would pass the status
    gate, leaving only the value check.
