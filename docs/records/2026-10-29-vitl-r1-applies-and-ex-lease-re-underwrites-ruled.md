---
id:
status: shipped
date: 2026-10-29
prs: [848]
supersedes:
superseded-by:
---

# The operator rules STATE row 32 (10) and (11): EPAM, WERN and SMPL are re-underwritten on the ex-lease basis, SMPL first; VITL's re-tag is withdrawn and R1 applies — firm, $30.05 on a 22.97x ex-lease median, landed without a re-assembly

**WHAT.** Two operator rulings on STATE §5.0 row 32, given 2026-10-29, verbatim:
- item (10): *"C2: re-underwrite all three on the ex-lease basis, SMPL first"*;
- item (11): *"C3: b) Withdraw it, and R1 applies"*.

**(11) is LANDED on VITL's page** (`data/dossiers/VITL/` and its `frontend/dossiers/` mirror) in
four deterministic $0 steps: no re-assembly, no LLM call, no freshness bypass. None of the four is
the assembly path the 45-day panel ceiling gates, and none refused.
1. **`refresh.lease_basis_transform`** through `refresh_dossier`, synthesis kept — #752's step 1,
   held for VITL since 2026-10-20. It writes `mechanical.valuation.lease_basis`, and it may: the
   quarterly export on disk is the one the page's bands carry (sha `7217811451`).
2. **`vinci anchor-backfill --tickers VITL`** — #752's step 2, the HELD values. The operator's
   `R2_NEEDED` still stood, so `preserve_operator_tag` kept it and printed the divergence.
3. **`vinci anchor-retag --ticker VITL --retire`** — the withdrawal. `anchor.operator_decision` is
   removed and the recipe returns to the machine's, `R1_midcycle_margin_evebitda`.
4. **`refresh.valuation_bases_transform`** — #762's step, re-run. #762 gave VITL its basis blocks
   while it had no lease basis, so R1's basis at the page's price and the rent pairing in "What
   CIQ's EV/EBITDA divides" could not be written; every other ex-lease page carries both.

Then `mirror_to_frontend()`. The order is forced: `anchor-retag --retire` refuses while the
machine's read moves a committed value, and `--values-held` never licenses a retire (#780), so the
values land under the standing decision first and the decision is retired after.

| VITL's anchor | before (main `f2c6e7aa`) | after |
|---|---|---|
| recipe | `R2_NEEDED`, the operator's (2026-10-07); the machine read R1 | `R1_midcycle_margin_evebitda`, no decision |
| R1 screen | NOT applicable | applicable |
| confidence | weak | firm |
| value / share | none | **$30.05** (dilution test $30.05: diluted = basic weighted average) |
| multiple | 4.20x — CIQ's own TEV/LTM EBITDA median, 24 closes, weak, flagged `band_incoherent` | **22.97x** — the ex-lease median, 21 closes, firm |
| net debt | $87.0M, operating leases ($70M) in | $16.75M, operating leases excluded |
| D&A | $9.254M, FY2025 | $9.635M, the twelve months to 2026-03-29 |
| margin · revenue · shares | 6.02% (8 FY median) · $784.41M LTM · — | unchanged · unchanged · 42,931,522 outstanding |
| data quality | `band_incoherent+band_unreconciled` | none; CIQ's band still flagged, and stated as "not the history R1 prices" |
| band checks | recorded D&A differ · market reconciliation differ | not_run (the ex-lease history does not use CIQ's Multiples ratios) · agree |

The arithmetic: 6.02% × $784.41M = EBIT $47.25M; + D&A $9.635M = EBITDA $56.89M; × 22.97 =
EV $1,306.7M; − $16.75M = equity $1,290.0M; ÷ 42,931,522 = **$30.05**. EV/EBIT 27.65x.

**(10) is RULED; the work stays open in row 32 (10), with owners:**
- **SMPL first.** Its page is being re-assembled in another session and is held behind a code PR
  (the fiscal-year-end defects that re-assembly found). Its record's own trigger has also fired:
  *"initial FY27 guidance below ~$1.30B"* (`scenarios/SMPL.json`, `reunderwrite_triggers`) against
  a guide of *"Net sales expected to decline between 13% and 17% year-over-year"* (8-K
  0001702744-26-000028, EX-99.1, filed 2026-10-27) on FY2026 net sales of $1,356.5M (10-K
  0001702744-26-000031, filed 2026-10-27) — **$1,125.9M–$1,180.2M**.
- **EPAM and WERN follow their CIQ re-exports, after each name's Q3 10-Q.** Neither is filed as of
  2026-10-29: EPAM's last 10-Q is 2026-08-06; WERN released Q3 by 8-K on 2026-10-27, and its 10-Q is
  not yet filed. Both pages are past the 45-day ceiling (row 28), so a full re-export comes first,
  then the re-assembly, then the record.
- **Who:** the operator re-exports and underwrites; the R1 records are the analyst's (`analyst:
  nogods404`). The agent re-assembles each page.
- **Standing:** never `scenario-refresh` a record's `net_debt` from a re-derived anchor as a bare
  number, which would mix the bases (`docs/records/2026-10-19-r1-prices-on-one-lease-basis.md`).

**WHY.**
- **(11).** The withdrawn reason had two halves. One was a judgment: *"no trailing median describes
  this business in either direction; it is a forward-margin question"*. The other was a factual
  claim: *"The EBITDA band also carries a vendor data defect"*. That claim was read on CIQ's
  lease-inclusive history. VITL's own filing reports total lease cost of $293.0M (EDGAR
  `LeaseCost`, FY ending 2025-12-28) beside CIQ's $287.6M rent, so the gap is VITL's rent, not a
  vendor defect (`docs/records/2026-10-20-artifact-pass-r1-lease-basis.md`). The operator withdrew
  the whole decision, both halves, rather than revising its words.
- **(10).** The three R1 records were struck on CIQ's mixed history (lease-inclusive since ASC 842,
  not before it) with lease-inclusive net debt. Rent is 5.0% (SMPL), 9.2% (EPAM) and 8.1% (WERN) of
  EBITDA. Row 32 offered two options: re-underwrite on the ex-lease basis, or keep the records as
  written. The operator chose re-underwrite, in the order SMPL, then EPAM and WERN.
- **Row 32 said $29.84; the page says $30.05.** Row 32's figure was measured on 2026-10-20 at
  `53cbe9fe`. Since then #836 (2026-10-28) gave the anchor's D&A the window its LTM EBIT covers:
  VITL's D&A moved from $9.254M to $9.635M
  (`docs/records/2026-10-28-the-anchors-d-and-a-covers-its-ltm-window.md`). With $9.254M the same
  arithmetic gives $29.843. The whole $0.21 is that one input.

**HOW VERIFIED.** Every run is on the real committed page and the real CIQ export:
- **The retire, before anything moved:** refused — *"the machine's read today moves 4 committed
  value(s) (d_and_a, data_quality_detail, dilutive_increment, shares_outstanding)"*. On the
  lease-inclusive page the machine still read R1 as NOT applicable; only the lease basis makes it
  applicable.
- **Step 1:** `refresh_dossier moved=True`. The page diff against main is the new block and one
  refresh stamp, nothing else.
- **Step 2, dry-run and then written:** *"DIVERGES: the machine reads 'R1_midcycle_margin_evebitda';
  the operator's 'R2_NEEDED' (decided 2026-10-07) stands"*; `VITL 6.0% (8y firm) 23.0x (21q firm) —
  30.05 NEW firm`.
- **Step 3, dry-run and then written:** *"recipe R2_NEEDED → R1_midcycle_margin_evebitda; machine
  reads R1_midcycle_margin_evebitda; decision retired"*.
- **Step 4:** run first on a scratch copy of the page. It moved only the lease-dependent fields
  (the at-price figure, which is new, and the rent pairing on `ev_ebitda_basis`), not the EBITDA
  reconciliation. Run in the worktree, the page came out byte-identical to the scratch copy.
- **Nothing else on the page moves.** 464 JSON leaf paths differ from main: 318 in the new
  `lease_basis`, 72 in `valuation_basis` (derived from the anchor and its recipe), 41 in `anchor`,
  18 in the four refresh stamps, 11 in the new `ev_ebitda_ex_lease_at_price` and 4 in
  `ev_ebitda_basis`. The synthesis and every other block are identical.
  - The page's text moves in five places: the anchor table (the operator-decision block and the
    three data-quality lines go); the basis lines (the lease-basis sentence, the rent pairing, R1's basis
    at the page's price, 6.2x); the refresh stamps; and one new cited source, which renumbers the
    endnotes after it.
- **The prose cites none of it.** The synthesis prose (`refresh._prose`, 6,509 characters) contains
  no old or new multiple (4.2x / 23.0x / 22.97x), net debt (87 / 16.75), base ($30.05) or D&A.
- **Consistency:** `anchor.lease_basis_mismatch` finds none on all 27 pages; VITL's valuation-basis
  block lists no conflict; all 27 `frontend/dossiers` pairs are byte-identical to their source.
- **Two tests read VITL's held page as their live case,** and the ruling ends both. Each is
  re-pointed, never weakened:
  - `test_band_checks::test_each_backfill_proof_refuses_on_its_own` needs a page with a
    recorded-D&A trip. VITL was the only one. Its page as committed at `f2c6e7aa` is frozen at
    `tests/fixtures/band_checks/VITL/dossier.json`; the other four cases still read the live corpus.
  - `test_propose` (renamed `…_on_every_live_case`) asserted that an R1 record on VITL is refused.
    It is not refused now. The pin now reads every committed page of both shapes the old pin
    covered: R1 with `applicable: False` (V today) and `R2_NEEDED` (AORT, MVST, NCNO). It asserts
    each shape exists and refuses every page.
  - Four mutants, four killed: the frozen page swapped for VITL's current one (no trip line); the
    backfill no longer checking trip lines; the tier guard ignoring `applicable=False`; the tier
    guard accepting a live `R2_NEEDED` page.
- **The SMPL trigger** was read from EDGAR on 2026-10-29: the 10-K's
  `RevenueFromContractWithCustomerExcludingAssessedTax` for 2025-08-31 → 2026-08-29, and the 8-K's
  EX-99.1 text.
- **Suite:** the full offline suite, on the committed artifacts — the counts are in the PR.

**BOUNDARY.**
- **The page:** VITL's `dossier.json` and `.md` at main `f2c6e7aa` (identical at `e6df4691`),
  against this branch, 2026-10-29. "Leaf path" means a JSON scalar or empty container, by its full
  path.
- **CIQ:** the shared copy `mosaic-theory-ta/data/manual/ciq/VITL`, read-only. All 10 files are
  byte-identical to Drive (sha256 checked 2026-10-29). The comps are dated 2026-07-29, 92 days
  before 2026-10-29. Nothing was re-exported or synced.
- **EDGAR:** companyfacts fetched live on 2026-10-29. VITL's latest 10-Q runs to 2026-06-28 (filed
  2026-08-06), and its net debt and shares are read from it.
- **The ex-lease band:** CIQ's quarterly Historical Capitalization, 24 observations from 2020-09-10
  to 2026-05-07, all checked: 17 reconcile to EDGAR's operating-lease liability, and 7 (2020-09-10
  → 2022-03-10) predate the standard in CIQ's balance sheet. 22 of them are priced closes.
  - The median of 22.97x is over the 21 closes before the latest; their range is 8.63x–308.68x.
  - The latest close, 4.60x on 2026-05-07, is below all 21 (percentile 0).
  - 2022-05-05 and 2022-08-04 reconcile but carry no multiple: their LTM EBITDA was negative
    (−$1.15M, −$2.94M).
- **Refresh stamps:** dated 2026-10-28, the writer's UTC date. The runs were made after local
  midnight on 2026-10-29.
- **Filing status** (EPAM, WERN, VITL, SMPL): EDGAR submissions read 2026-10-29, forms 10-Q, 10-K
  and Item 2.02 8-Ks since 2026-07-01.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **VITL's R1 stands on a 92-day-old export.** The band's latest close is the Q1 filing
  (2026-05-07); its net debt and share count come from the Q2 10-Q. The next full export, after
  VITL's Q3 10-Q (~2026-11-05 by cadence), re-derives all of it at re-assembly (row 28). Falsifier:
  that re-assembly moves the multiple or the base materially. That would be news about the export,
  not this ruling.
- **What the withdrawn judgment was about, stated as data so the ruling is read with it.** Nine of
  the 22 closes are at or above 48x, all from 2020-09 → 2023-03, on LTM EBITDA of $1.5M–$15.0M (seven
  of the nine predate ASC 842); every other close sits on $23.3M–$102.9M. The base
  is 2.69× the page's $11.16 close (2026-08-17). R1's own basis at that price is 6.2x, against a
  22.97x median. **No scenario record exists for VITL**, so nothing is priced from the anchor until
  one is struck; the page's own note holds that "even a firm anchor requires a full bear/base/bull
  2:1 underwrite before any BUY".
- **The retire takes the operator's words off the page.** A retired decision leaves no block, by
  #780's design. The words and the withdrawal live here and in git (`f2c6e7aa`).
- **Two test changes ride in an artifact PR**, in their own commit, ahead of the artifacts. They
  re-point pins the ruling made false. They change no assertion about how the code behaves.
- **STATE.** Row 32 (11) is closed and row 32 (10) is restated as RULED. Row 27's clause "STILL
  OPEN: VITL is HELD at main's page …" is struck too, because it states the same open item. Row
  10's account of #780 ("on AMZN UBER GOOGL AORT CNXC VITL") describes what #780 built, and is
  left as it stands.
