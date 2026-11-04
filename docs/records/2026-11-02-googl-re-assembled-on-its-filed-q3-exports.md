---
id: 2026-11-02-googl-re-assembled-on-its-filed-q3-exports
status: superseded
date: 2026-11-02
prs: [886]
supersedes:
superseded-by: 2026-11-03-googl-lly-and-amzn-re-assembled-on-their-post-drop-exports.md
---

# GOOGL re-assembled on its filed Q3 exports: its material row reconciles with its four quarters and the synthesis states it; LLY's and AMZN's re-exports are held

**WHAT.** The operator re-exported GOOGL's, LLY's and AMZN's Financials pairs on 2026-11-02, after
CIQ processed each Q3 10-Q ("i've re exported them and added to the folders"). Each pair was
checked on Drive before use, with main `0e574f6b`'s own readers:
`ciq_sheets.press_release_income_columns` (#868, #872) and `ltm_quarters.check` (#868), with
materiality from `mark_material_rows`. Only GOOGL passed everything, so only GOOGL is built.

**GOOGL: written on the first build.**

| | before (2026-10-26 page) | after (2026-11-02 page) |
|---|---|---|
| extraction version | `2026-10-09.3` | `2026-10-30.submissions-pages` |
| lean (draws) | mixed (mixed 3 / strongly-bullish 2) | mixed (mixed 4 / strongly-bullish 1) |
| proposal | none (mixed) | none (mixed; the draws also disagree) |
| R1 base $/sh (diluted) | 213.54 (210.82) | **225.54 (223.50)**, +5.6% (+6.0%) |
| R1 multiple (median EV/EBITDA) | 17.4518x | 17.4518x |
| machine recipe hint | `R1_midcycle_margin_evebitda` | **`R4_forward_ev_ebit`** |
| comps data date | 2026-09-21 | 2026-10-28 |
| material row stated | none demanded | Gain (Loss) On Sale Of Invest. LTM 129,109.0 |
| UNTRACEABLE caveats on the page | 0 (predates #859) | 8 |
| cost (run) | $2.38 (`d8a99585`) | $3.20 (`2c9ee890`) |

- **Neither export carries a press-release column.** The annual LTM column is headed
  "LTM 12 months Sep-30-2026", and the quarterly Q3 column is "3 months Q3 Sep-30-2026". Q2 now
  reads "Restated". The rule covers the Income Statement, Balance Sheet and Cash Flow.
- **The material row reconciles.** Gain (Loss) On Sale Of Invest. LTM is 129,109.0, which equals
  2,353 + 36,804 + 98,999 − 9,047 (Q4-25 … Q3-26) exactly. The 10-29 export had carried FY25's
  24,620.0 into a press-release LTM column. All 5 rows `ltm_quarters.check` reads agree.
- **The synthesis states the row** ("The LTM Gain (Loss) On Sale Of Invest. line is
  $129,109.0M …"), so the 19c guard finds nothing uncited. No `ciq-ltm-quarters` flag fires.
- **The R1 base moves +5.6% on its own inputs; the multiple is unchanged.**
  - LTM revenue: 445,866 → 471,098.
  - D&A: FY25 25,536 → LTM 28,540.
  - Net debt: −121,683 → −114,767.
  - Diluted shares: 12.309bn → 12.368bn.
- **The machine now proposes R4.** All three of #697's ratified conditions hold. The anchor says:
  "R1 cannot anchor: EBITDA basis divergent: consensus-implied D&A 5.75× the actuals"; and R3
  cannot price it cleanly because "4 of the trailing 4 quarters carry material non-operating
  income". The committed recipe, `R3_forward_pe`, still wins (#697, #780). Changing it is the
  operator's call, as with AMZN and UBER (#698).
  - **What moved is condition 3's EPS basis**, on the 2026-11-02 EstimatesReport. CIQ's FY P/E
    rows imply GOOGL's price on GAAP EPS within 0.03% (279.84 / 279.91 / 279.87). The normalized
    line scatters 30.7% (200.75 / 287.09 / 280.79), so `pe_eps_basis.fiscal_years` reads `gaap`.
    On the 10-26 page only the normalized line fit (spread 0.01%; GAAP 1.08%, outside the 1% fit),
    so it read `normalized`. Conditions 1 and 2 held then too. Why CIQ's FY P/E moved to GAAP EPS
    is not measured here; what is measured is the fit on each EstimatesReport.
  - **Two value pins on the living pages move with it** (`tests/test_r4_machine_proposal.py`):
    - the machine's selection is now AMZN, GOOGL and UBER;
    - the "FY P/E struck on normalized EPS" negative pin moves from GOOGL to MVST. MVST is the
      shape GOOGL had: conditions 1 and 2 hold, 4 of 4 quarters are material, and the basis is
      normalized. MVST's page is not rebuilt (row 41).
- **Three net-debt pins read a frozen GOOGL vintage**, `tests/fixtures/companyfacts_frozen/GOOGL.json`.
  - It is main `0e574f6b`'s tracking fixture, with its cash instant at 2026-06-30, the date CIQ's
    frozen GOOGL figures carry.
  - The tracking fixture now ends at 2026-09-30, so the pins' shared-date check failed. This
    follows the README's procedure, as for NFLX and SMPL. The pins' values are unchanged.
- **The pointer-cap row is not gained.** #871 counted GOOGL among the 13 pages that would gain a
  covenant-pointer cap row. This assembly located no agreement exhibit at all, the same as the
  10-26 page ("no CIK-scoped agreement exhibit located across the filing history"), so there is no
  cap to state.
- **The monitor day at the latest close is written**, `data/monitor/2026-10-30.json`, run with no
  `--ref` (RUNBOOKS §j).
  - GOOGL marks at $279.84, −19.05% against its $345.90 entry (−16.63% excess vs SPY).
  - GOOGL closed $324.89 on 10-28, $283.82 on 10-29 (139.7M shares) and $279.84 on 10-30. Tiingo
    agrees to the cent on all three days.
  - The BUY−AVOID spread is +63.08 pp, against +51.37 pp on 10-28.
  - The panel-emit pin is green, and no `newer_filings` or `last_evidence_date` is after 2026-11-02.

**LLY: refused, and neither synced nor built.**
- Drive's `Eli Lilly and Company NYSE LLY Financials_Annual.xls` and
  `… Financials_Quarterly.xls` are byte-identical (sha `3e2345cb9174…`, 657,418 B each).
  `CiqBundle.from_files` raises `CiqMislabelledError`: the file named annual states Period Type
  'quarterly' on all three statements.
- The operator re-exports the Annual. `-ta` keeps its 2026-10-29 pair, and the new LLY
  EstimatesReport waits with it.

**AMZN: Financials verified, but not built (owed items are missing).**
- **Fresh:** Financials_Quarterly and Financials_Annual (2026-11-02, both filed, no press-release
  column) and the EstimatesReport (2026-11-02, `≥2026-11-01`).
- **Stale:** Company Comparable Analysis and Key Developments are 2026-10-07's, from before the Q3
  print.
- **Missing:** the Q3 2026 earnings call. The newest on file is Q2 2026, Jul 30.
- **The checks on the pair:** its material Gain (Loss) On Sale Of Invest. LTM 69,158.0 reconciles
  with its quarters (69,139.0, within tolerance). EBIT's LTM of 104,366.0 is 2.40% off its four
  quarters (101,866.0), a QA flag and not a material row.
- `-ta` is unchanged.

**WHY.** These are the two names row 41 left waiting on post-10-Q re-exports (GOOGL, LLY), plus
AMZN from the b2 group. Each pair was checked first because the 2026-10-29 GOOGL export had shown
that a pair CIQ has not finished processing can carry the wrong LTM on a material row. The merged
#868 now refuses exactly that.

**HOW VERIFIED.**
- **The verify step is $0 and read-only, on Drive** (`verify_exports.py` in this session's
  scratchpad).
  - It runs the merged refusal and LTM check plus `CiqBundle.from_files` per name.
  - Then a hash compare against `-ta`. For GOOGL: the 3 changed files are archived to
    `ciq-archive/replaced-2026-11-02/GOOGL/`, the other 8 are unchanged, and the folder equals
    Drive on 11 of 11 files, with no symlinks.
- **One GOOGL build**, at $3.20 against a $2.80 estimate (stop line about $5.60). No guard refused.
- **The suite:** the full offline suite, CI-like (the CIQ copy, store, caches and `.env`
  unlinked, as CI runs it), on the pre-merge tree (`5dbdb98e`): 8,538 passed, 0 failed, 548
  skipped, 9 xfailed (`pytest -m "not network"`, 7m41s).
  - On the tree with main merged in (`60151ccc`), `bin/commit`'s gate ran 8,603 passed, 0
    failed, 547 skipped, 8 xfailed. Its `-qq` output prints no totals, so these are counted from
    its progress characters.
  - Before the frozen vintage and the two R4 pin moves, the same tree with the artifacts failed
    exactly 5 tests: the three GOOGL net-debt pins and the two R4 pins above.

**BOUNDARY.**
- **Runs:** 1, on 2026-11-02 09:21 UTC, on branch `artifacts/googl-lly-amzn-2026-11-02`
  (main `0e574f6b`). 7 calls, 0 failed, $3.202225 at list price.
- **Draws:** 5. The tallies are tallies, never rates.
- **`ltm_quarters.check`:** reads only the annual summary's additive rows. That is 5 rows on GOOGL
  and 5 on AMZN, at 0e574f6b.
- **UNTRACEABLE:** counted as the page's caveats matching "untraceable figure".
- **Store:** topped up 2026-10-29..10-30 for the 18 names the monitor day carries, 36 bars,
  grouped-daily.
- **File dates:** Drive mtimes, local time.
- **Code:** the page was built on `0e574f6b` (extraction version `2026-10-30.submissions-pages`).
  Main has since merged #879 (E2-D17), #882 (D7, amended filings), #881 (A3), #883 (four
  position-paired readers), #884 (C4, the as-of cut), #885 (net debt as filed by the price date)
  and #888 (the ex-lease multiple's share count, likewise); this branch carries them. Whether they
  move GOOGL's page is unmeasured. #882's own comparison skipped GOOGL, because its submissions
  documents were not cached then. #884 measured a GOOGL 52-week low move (244.15 → 251.85) on the
  10-26 page, not on this one.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$3.20.**
- **For the operator's look before merge:**
  - GOOGL's R1 base moves +5.6%.
  - The machine's recipe proposal moves R1 → R4, with the committed R3 unchanged.
  - Its lean stays mixed with no proposal; the draws moved from 3/2 to 4/1.

## Amendments

**2026-11-03 — superseded by a rebuild on the operator's post-drop comps, and three statements
above corrected.** The GOOGL page this record describes was rebuilt the next day, once, on comps
dated 2026-10-30 ($279.84), with LLY and AMZN
(`docs/records/2026-11-03-googl-lly-and-amzn-re-assembled-on-their-post-drop-exports.md`). Each
correction below was re-derived from the committed pages before it was written. The figures above
stay visible as first written.
- **D&A 25,536 is not fiscal 2025.** It is the twelve months to 2026-06-30. The 2026-10-26 page's
  own annual table carries D&A FY25 21,136 and LTM 25,536 (both rows of today's annual export
  give FY2025 as 21,136). The 10-26 anchor labelled it "consolidated latest FY". That is the
  label `anchor.ciq_da_basis` replaced (#830): the CIQ bridge reads the annual sheet's last
  column, an LTM. So the bullet "D&A: FY25 25,536 → LTM 28,540" should read "LTM to 2026-06-30
  25,536 → LTM to 2026-09-30 28,540".
- **R1 divides by shares outstanding, not the diluted count.**
  - 213.5389 = (0.262717 × 445,866 + 25,536) × 17.451829 + 121,683, all ÷ 12,230,000,000. That
    denominator is `anchor.shares_outstanding`, EDGAR's point-in-time count.
  - 225.5389 is the same with 471,098, 28,540 and 114,767, ÷ 12,294,000,000.
  - The diluted weighted averages, 12,309,000,000 → 12,368,000,000, give 212.17 → 224.19, and
    neither is on the page. So "Diluted shares: 12.309bn → 12.368bn" should read "shares
    outstanding 12.230bn → 12.294bn".
- **The bear point's "four consecutive quarters" is a known defect, recorded and not fixed here.**
  `vinci/dossier/mechanical.py:2185` takes `_nonop_common(...)[-4:]`: the last four quarters with
  operating income, pre-tax income and revenue all filed. GOOGL files no standalone Q4, so the
  window skips Q4 2025 and reaches back to Q3 2025. R4's condition still holds on the four it
  reads. An artifact PR carries no code; the fix is scheduled separately.
