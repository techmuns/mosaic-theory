---
id:
status: shipped
date: 2026-10-27
prs: []
supersedes:
superseded-by:
---

# CIQ's EBITDA differences carry their cause, the lease checks compare like with like, and the CIQ bridge refuses a foreign currency and stores its scale check (integrity wave 2, lane L6)

**WHAT.** Items 11 and 12 of wave 2, plus two leftovers from #819.

**Item 11 — `ebitda_vs_xbrl`, the largest unexplained pool.** Every differing-unexplained or
unchecked quarter on the committed pages was given its cause, and each cause that code can state
is stated by `vinci/dossier/ebitda_recon.py`. Nothing in the scorecard was edited by hand.

| cause | what it is | quarters | rule |
|---|---|--:|---|
| wrong file | LLY's `Financials_Quarterly.xls` is its ANNUAL export (sha `7f23de02b0` on both files, 'Period Type: Annual'), so four fiscal years were set against four rebuilt quarters | 4 → block removed | four columns spanning other than 240–300 days are no LTM: no block |
| our rebuild | CNXC tags D&A only as `Depreciation` + `AmortizationOfIntangibleAssets`; GOOGL does too from 2026 | 6 rebuilt (GOOGL's two match CIQ to the dollar) | the split pair, the SAME quarter on both legs (the anchor's own pair, `anchor._latest_dep_amort`) |
| our rebuild | BURL tags no net interest line after its 2025 Q2, only `InterestExpenseNonoperating` | 4 rebuilt (1 confirms) | pre-tax + gross interest expense + D&A, stated as its own construction |
| CIQ normalising an item out | the gap is an amount the quarter's own XBRL tags: V's `LossContingencyLossInPeriod` 903 / 708 / 329 ($M), VITL's `FinanceLeaseRightOfUseAssetAmortization` (3 quarters), PARR's D&A inside cost of sales, NKE's other non-operating line | 8 stated | a family of unusual-item and D&A-component us-gaap tags, matched within $1K and 2%; the non-operating line only for a pre-tax construction |
| CIQ normalising items out (a SUM) | CIQ's EBITDA is its EBIT + D&A, and its EBIT leaves out the unusual items its own Income Statement itemises between 'EBT Excl.' and 'EBT Incl. Unusual Items' | 10 stated | `unusual_explains`: their net within 2% of the gap (stored as `ciq_unusual`) |
| period mismatch | AMZN +$2,500M to 2025-09-30, −$2,500M to 2025-12-31; the LTM agrees to the dollar | 2 stated | `offset_by`: two LTM quarters whose gaps cancel within $1M and 2% |
| vintage | V's quarter to 2026-06-30: companyfacts (fetched 2026-10-27 15:39) ends at the 10-Q filed 2026-04-29 | 1 unchecked | the note now says EDGAR has not reported the quarter, not "no D&A tag" |

Releases quoted by #818's table reader (VRRM 2025-12-31, SMPL 2025-11-29) land on the pages too.
The CIQ itemisation agrees with every release quote already on the pages, to the thousand: TJX,
ROST, BRBR, WLK and SMPL.

**What stays unexplained (15 quarters, each diagnosed).** In every case the gap is a partial
itemisation, with a residual that no single stated amount explains:

- **AORT, 2025-06-30.** +2.600 against CIQ's unusual items of 5.264. The residual (−2.664) is the
  debt-extinguishment loss its release states (2,664). That is a non-operating item CIQ also
  itemises, so it sits below operating income.
- **AORT, 2025-12-31.** −1.296 against −1.39: three items, each rounded to $0.1M.
- **BURL ×3.** −52.5, +10.3 and −60.2 against 6.8, 17.9 and −49.9. The construction keeps BURL's
  other non-operating income inside. The quarter to 2026-08-01 carries the $55M tariff refund its
  release states.
- **CNXC ×2.** +36.7 and +35.4 against 40.7 and 31.7, CIQ's merger and restructuring items.
- **EPAM ×2.** +17.4 and +16.4 against 21.6 and 17.4.
- **NKE ×2.** +148 and +71 against restructuring of 230 and 81. The pre-tax construction keeps
  NKE's other (income) expense inside.
- **TGT ×2.** +221 and +115 against 196 and 89.
- **VITL, 2025-12-28.** +1.958, with nothing itemised by CIQ.
- **WLK, 2025-12-31.** +368 against 504.

**What stays unchecked (15 quarters, each a definition or coverage gap):**

- **GOOGL's two 2025 quarters:** depreciation is tagged, amortisation is not.
- **MVST ×4:** it tags only `DepreciationNonproduction`, which by its own definition is not total
  D&A.
- **ORKA ×4:** it tags depreciation only. Its quarterly export is not proven the page's own (no
  band stamp), so it is not back-filled.
- **WERN ×4:** it tags `OtherDepreciationAndAmortization`. That is its income-statement D&A
  (286.321 for FY2025 = depreciation 276.3 + amortisation 10.1), but the tag is not an alias in
  `concepts.CONCEPT_ALIASES`, which is another lane's file.
- **V ×1:** the vintage case in the table above.

**Item 12 — the checks that compared unlike quantities.**

- **Rent (`lease_basis`).** The comparator is the filer's TOTAL lease cost: `LeaseCost`, else the
  parts it tags, summed, sublease income netted.
  - **NKE:** operating 693 + variable 453 = 1,146, which is CIQ's rent to the dollar. It was
    compared with 693 alone; now it confirms.
  - **WLK:** CIQ's 128 equals one part, its `ShortTermLeaseCost` (128 of a 306 total). That is a
    narrower cost, stored as `rent_component` and scored unchecked, never as a difference.
  - **Three immaterial names** move their total and still agree: BRBR 3.9 → 5.2, MVST 3.394 →
    3.575, VRRM 10.3 → 14.0.
- **Lease rows (`lease_basis._split`).** CIQ's rows less a finance-lease figure are compared only
  where that figure is the date's own (`_finance_dated`, within a week).
  - **UBER** tags its finance leases complete only at year-end. Carried onto quarter-ends, that
    figure produced four 'unreconciled' near-misses (2.0–2.1%, and 2019-03-31 with no figure in
    reach) and five 'reconciled' dates, all comparing two different dates.
  - Where CIQ's rows EXCEED the operating figure on a date with no finance figure of its own, the
    date is now unchecked.
  - **WERN's 2019-12-31** stays a difference: CIQ's rows are 0 against EDGAR's 11.736, and no
    finance figure explains rows short of the leases.

**Leftover (a) — the scale check has an outcome.** `ciq_balance.extract` now sets `scale_check`:
agree, differ, or not_run where there is no revenue or no figure to measure. `scale_outcome`
wraps it. The anchor stores it as `anchor.ciq_scale_check`, set by both callers of the CIQ bridge
(assembly's `_assembly_anchor` and `anchor-backfill`'s `_machine_anchor`). It is scored as
`ciq_scale_vs_revenue`: INTERNAL, wrong unit only. The family's "unscored" note now names only
what is still unscored: D&A containment and the net-debt cross-read.

**Leftover (b) — one currency refusal on both paths.** `anchor.ciq_bridge` calls
`ciq_sheets.require_usd` before it extracts, and `_machine_anchor` re-raises `CiqCurrencyError`
instead of anchoring EDGAR-only. ONON's 15 CHF panels are refused on the backfill path, as they
already were at assembly. This is #819's review finding 1. It is an additive edit to `anchor.py`;
its owner (the re-tag session) was messaged before the edit.

**WHY.** A difference the scorecard cannot explain reads as a CIQ error, and so does a
comparison of two different things. The BEFORE had 59 open quarters (30 unexplained + 29
unchecked). They break down as follows, and sum to 59:

- **4 were a wrong file:** LLY.
- **10 were our own rebuild's gap**, and now rebuild: 3 confirm, 2 are CIQ's itemised
  normalisation, 5 differ unexplained.
- **18 of the 30 unexplained were CIQ's normalisation**, stated by the filing's XBRL (8), the
  release (2) or CIQ's own itemisation (8).
- **2 were a period mismatch:** AMZN.
- **25 remain as they were:** the other 10 unexplained and 15 unchecked, one of them the vintage
  case.

With the 5 newly rebuilt quarters that differ (BURL 3, CNXC 2), 30 quarters are open in the
AFTER, each named above.

**HOW VERIFIED.**

- **Corpus before synthetic: the EBITDA rebuild.** Each page's block was rebuilt from its own
  quarterly export (the assembler's read-only copy, `mosaic-theory-ta`; sha equal to the page's
  band stamp), EDGAR and the page's releases.
  - With main's code, every stored figure reproduces on the 25 own-export pages. Only #818's two
    quotes differ, and TECX (not its own export) has no stored block.
  - With this branch, only the intended keys move: the new reasons, `ciq_unusual`, the rebuilt
    BURL / CNXC / GOOGL quarters, and LLY's removed block.
- **Null rates, on the corpus.** Population: 41 differing quarters on 18 own-export pages.
  - **Tagged amounts:** 0 of 656 trials with the gap shifted ±{3, 7, 17, 31, 61, 101, 199, 307} ×
    $1K, and 4 of 656 with the same shifts × $1M. Each of the 4 lands on a real unusual-item
    amount of that same quarter (EPAM's restructuring, NKE's asset impairment, WLK's goodwill).
  - **Itemisation:** 1 of 120 against another quarter of the same name, 8 of 3,280 against any
    other quarter.
  - **Offsets:** 0 of 782 cross-name pairs.
  - For comparison, #818's table reader was 1 of 544.
- **Fail first.** The new tests were run against `origin/main` in a scratch worktree:
  - `test_ebitda_recon_wave2`: 13 of 15 red; the 2 green are negative pins whose behaviour main
    already has.
  - `test_lease_basis_wave2` and `test_ciq_balance_scale_outcome`: 14 of 14 red.
  - `test_ciq_bridge_currency_and_scale`: 6 of 7 red; the green one is the USD negative pin.
- **Fixtures.** `tests/fixtures/ebitda_recon_wave2.json` holds the real companyfacts points as
  filed, the page's CIQ quarterly EBITDA, and CIQ's derived unusual-item net per quarter. No raw
  CIQ cell beyond what the page stores is frozen. The lease and scale tests carry real figures
  inline.
- **Mutation.** 32 mutants by hand across the eight touched modules. First run: 29 killed. The 3
  survivors were:
  - an EQUIVALENT mutant: the offset's sign test, which the sum test already implies (|a+b| ≥
    max(|a|,|b|) for one sign);
  - two real gaps: a rent that agrees with a one-part total, and the date test for a finance
    figure. Both were then pinned, with the test extracted into `_finance_dated`.
  - Re-run: 31 of 32 killed; the survivor is the equivalent mutant above.
- **Back-fill, for real.** `ebitda_recon.backfill_transform` and `lease_basis.backfill_transform`
  ran as one refresh per page; `ciq_scale_backfill.scale_check_backfill` wrote the anchor. Each wrote
  only behind its reproduction proof:
  - **EBITDA:** a committed quarter that was built keeps every figure and quote. LLY's block is
    removed only because its own committed dates span 1,095 days.
  - **Lease:** every key except the four rent fields must reproduce.
  - **Scale:** the quarterly sha must equal the page's stamp, and the annual must reproduce the
    page's annual table.
  - Results: 24 pages refreshed, scale written on 25. Refused, each named: FUBO and TECX (no
    quarterly stamp), ORKA (its quarterly export proves no band stamp), and UBER's lease block (it
    moves the band, so it needs a re-assembly).
  - Every page's JSON moved only on the keys named above, checked key by key against the commit.
    The frontend mirror moved only `frontend/dossiers`.

- **Code review (round 0, `/code-review high --fix`).** Four findings fixed, each behind a pin
  that is red on the reviewed commit:
  - the scale outcome never raises where the bridge did not;
  - a bridged read stores its own outcome instead of reading the workbook twice;
  - a sublease income is never a lease-cost part, and never a total alone.
  One finding was skipped: the export-ownership proof is duplicated from
  `refresh.ciq_currency_transform`, whose copy is a closure in another lane's file.
- **Import fences.** The full suite caught a page writer placed in `ciq_balance`. It gave
  `vinci.monitor` a static path to the store's ledger writers, through `anchor` → `ciq_balance` →
  `assemble`. It now lives in `ciq_scale_backfill`, which nothing on that path imports.

**THE SCORECARD, BEFORE → AFTER.**

- **BEFORE:** `data/snapshots/data_quality/ciq/2026-10-27.json` as committed at 56500bb1. It was
  re-run on main and matched on all 18 checks (inputs sha `4dedc3df…`).
- **AFTER:** the same path, rewritten by `vinci audit quality --source ciq --write` on this branch.

Counts are units: confirmed / differs stated / differs unexplained / unchecked.

| check | BEFORE | AFTER |
|---|---|---|
| `ebitda_vs_xbrl` | 37 / 4 / 30 / 29 (100 quarters, 25 pages) | 40 / 26 / 15 / 15 (96 quarters, 24 pages) |
| `rent_vs_edgar_lease_cost` | 21 / 0 / 2 / 1 (24 pages) | 22 / 0 / 0 / 2 |
| `lease_rows_vs_edgar` | 449 / 5 / 5 / 33 | unchanged: UBER moves at its next assembly |
| `ciq_scale_vs_revenue` (new) | unscored | 24 / 0 / 0 / 1 (25 pages; FUBO, TECX not run) |

**BOUNDARY.**

- **Pages:** the 27 committed under `data/dossiers`. BEFORE at main 56500bb1 (inputs sha
  `4dedc3df…`); AFTER on this branch after the back-fill.
- **Units:** quarter (EBITDA), page (rent, scale), balance-sheet date (lease rows).
- **CIQ:** the assembler's workbook copy at `mosaic-theory-ta/data/manual/ciq`, read on
  2026-10-27; a page is read only where its export is proven its own.
- **EDGAR:** the primary checkout's SEC cache, companyfacts fetched 2026-10-27.
- **Releases:** those on each page (the EX-99.1s of the last ten 8-Ks).
- **Null trials:** as stated above.
- **Scale measurement:** the 27 page names' real workbooks gave 25 agree, 2 not run (ORKA and
  TECX report no revenue) and 0 differ, matching #819.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **UBER is a decision-path change at its next assembly, not now.** Under like-with-like
  statuses, UBER's ex-lease band stops refusing: median 45.26x, current 19.14x, 12 closes
  2023-06-30 → 2026-06-30. Its R4 proposal states the condition "R1's anchor declines
  (applicable=False)", which rests on that refusal. So the re-assembly must re-read the proposal.
  Until then, UBER's page keeps its 4 near-misses as unexplained. That is an open row, not
  accepted risk.
- **The itemisation reason is CIQ's account of itself.** The comparison stays independent (the
  filing's figure is EDGAR's); only the REASON comes from CIQ's own export. A CIQ error whose
  itemisation happened to equal its own gap would read as stated. Measured: itemisation matches 1
  of 120 same-name quarter pairs and 8 of 3,280 cross-name pairs by chance. FALSIFIER: an
  itemised quarter whose release contradicts the itemised item.
- **A $1K tagged match is a coincidence at a measured rate**, 4 of 656 at $1M shifts. It is
  evidence to weigh, quoted and not attributed, the same as a sentence.
- **Found, not fixed (other lanes' files):**
  - **LLY's quarterly Financials export is its annual export.** Every reader of that file on
    LLY's page reads annual columns: the own-history band, the `ev_bridge` stamp, the quarterly
    rows. This needs an operator re-export, and a period-type guard in the CIQ loader.
  - **MCK's `Financials_Annual.xls` states 'Period Type: Quarterly'.** MCK has no page.
  - **WERN's `OtherDepreciationAndAmortization`** is a D&A alias candidate (`concepts.py`).
  - **A page keeps only the releases among its last ten 8-Ks**, so the LTM's earlier quarters
    have no release to quote (`mechanical` / `primary_source`).
  - **`ciq_sheets.customers` runs for minutes on AMZN's and GOOGL's customer RTF exports**: more
    than 40s each on main's code. So the two all-folder tests in
    `test_segment_absence_and_relationship_route` run without end wherever `data/manual/ciq` is
    present. Measured on the assembler's copy; this build's suite runs deselect them, named.
  - **The pre-tax constructions keep other non-operating items inside** (BURL, NKE). A
    like-with-like construction would subtract the tagged line. That is not measured on TJX's
    exact matches, so it is not done.
