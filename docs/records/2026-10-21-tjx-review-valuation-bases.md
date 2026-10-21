---
id:
status: shipped
date: 2026-10-21
prs: [762]
supersedes:
superseded-by:
---

# A review of TJX's page, closed in one PR: what CIQ's EV/EBITDA divides is measured, R1's ex-lease multiple is struck at the page's price, CIQ's EBITDA is set against the filings, the GAAP EPS guide is read, and the anchor divides a point-in-time count the filer corroborates — TJX re-assembled and the fleet passed

**WHAT.** The operator's eight-point review of TJX's `dossier.json` (2026-10-21), and the operator's
instruction: "fix all the issues in one PR … instead of requiring another to-fro".

| # | the review's point | disposition |
|---|---|---|
| 1 | the headline 13.3x EV/EBITDA does not divide reported EBITDA (19.1x) | **SHIPPED** — `valuation.ev_ebitda_basis`: TEV ÷ multiple, measured against reported LTM EBITDA and against EBITDA + rent, per page |
| 2 | the lease basis | already handled (#750/#752) |
| 3 | the current multiple on R1's basis | **SHIPPED** — `valuation.ev_ebitda_ex_lease_at_price`; `valuation_basis.current_multiple` for R1 filled from it |
| 4 | the $331M tariff refund; "GAAP basis" labels on CIQ's EBITDA | **SHIPPED** — `financial_summary.ebitda_reconciliation`, quarter by quarter; labels now "CIQ's EBITDA, vendor-normalised" |
| 5 | three FY27 earnings bases | **SHIPPED** — `gaap diluted eps` read beside `adjusted eps` |
| 6 | the forward-FCF gap | already handled on main |
| 7 | the estimate timing | already handled on main (the page dates the export "data ≥ 2026-10-09") |
| 8 | 1.100B point-in-time vs 1.117B weighted-average shares | **SHIPPED** — the base divides the point-in-time count where the filer's own basic weighted average corroborates it; a dilution test beside it |

On TJX's re-assembled page (main `4b514dca` + this PR's code, the 2026-10-20 close $146.99):

- **Item 1:** CIQ's 13.3x divides TEV $170,372M by $12,810M. Reported LTM EBITDA $8,903M plus rent
  $3,814M is $12,717M, 0.7% apart: TEV *with* operating leases over EBITDA *with* rent added back.
  The page now says it is NOT a multiple of reported EBITDA.
- **Item 3:** R1's own basis at the page's price is **17.8x**. That is (price × 1,099,974,061 shares
  outstanding + net debt −$3,133M excluding operating leases) ÷ $8,903M. Before this, the page's
  only "current" figure was the ex-lease history's 16.3x quarterly close.
- **Item 4:**
  - Q2 FY27 (to 2026-08-01) reads CIQ $1,996M against $2,327M rebuilt from the 10-Q: pre-tax income
    less net interest income, plus D&A.
  - That is −$331M, and the quarter's release states "aggregate refunds of $331 million". TJX's
    three earlier quarters agree.
  - The leverage caveat and the triangulation rows no longer call CIQ's EBITDA "consolidated GAAP".
- **Item 5:** the guide reads GAAP diluted EPS FY27 **$5.31–$5.36** and Q3 $1.36–$1.38, beside
  adjusted $5.15–$5.20 and Q3 $1.30–$1.32. The adjusted-EPS valuation field still reads the
  adjusted guide only.
- **Item 8:** the anchor is **$131.10** on 1,099,974,061 shares outstanding. It was $129.10 on the
  1.117B diluted weighted average. The dilution test is **$129.57**: the same equity over the count
  plus 13,000,000, which is TJX's diluted less basic weighted average for the quarter to
  2026-08-01.

**WHAT THE FLEET PASS FOUND, AND WHAT IT CHANGED IN THE CODE.** Three defects surfaced while the
pass ran on real pages, and each was fixed and pinned before anything was committed.

1. **A point-in-time count the filer's EPS does not recognise.**
   - **LLY:** the 10-Q cover reads 941,357,065 shares against 892,400,000 basic. The ~49M gap is the
     shares Lilly's employee benefit trust holds (EDGAR `CommonStockSharesHeldInEmployeeTrustShares`
     50,000,000, FY2025 10-K).
   - Divided by, the cover count would have cut LLY's base **5%**, $699.65 → $664.23.
   - **V:** its only count is CIQ's comps figure, and V tags no weighted average. It would have
     gone from inapplicable to a **new** $357.65 base, on the page whose share basis already fails
     (STATE row 32 (12)).
   - **The fix:** the count is used only within **−10% / +2%** of the filer's basic weighted average
     over the same 10-Q quarter. Below the average is a buyback; IT sits at −5.0% after $1,082M
     repurchased in the half, the deepest of the 19 pages with a base. Above it beyond the margin
     is issuance or a count EPS excludes, and the counts cannot tell those apart.
   - **A refused count** leaves the base on the diluted weighted average, strikes no dilution test,
     and prints its refusal on both renderers.
   - **Refused on this pass:** LLY (+5.5%), PARR (+3.3%), NCNO (+4.5%), MVST (+10.2%), TECX (+3.1%),
     ORKA (+57.3%, a 2025 weighted average) and V (nothing to check against). Only LLY and PARR have
     a base; both stay at main's value.
2. **R1's price and value on two counts.** The at-price multiple read `stock_info.shares_out`
   directly. On PARR that is the count the anchor refuses. Now both read the ONE rule
   (`anchor.share_denominator`), and the line names which count it is.
3. **A refresh that carried a block instead of rebuilding it.**
   - `valuation_bases_transform` validated the page with its old blocks still in it.
   - TJX's page, assembled minutes before `shares_basis` existed, failed that validation.
   - A block the builder no longer writes would also have survived.
   - It now drops and rebuilds the two valuation blocks. The reconciliation is dropped only where
     it is rebuilt.
4. **A coincidental quote.**
   - SMPL's +$95.5M quarter is an $82.0M impairment plus integration and restructuring costs.
   - It quoted "Selling and marketing expenses of $97.0 million", 1.6% away and inside the 2%
     window.
   - A stated amount now matches only within ONE UNIT of its own precision as well.
   - The five quotes that stay are BRBR $69.0M legal provision, ROST $253M tariff refunds, TJX
     $331M, V $707M litigation provision and WLK $18M facility shutdowns. Each was read and judged
     an explanation, not a coincidence.

**THE PASS.**
- **TJX re-assembled (paid)** on this PR's code, then refreshed and backfilled once the three fixes
  above landed.
  - The draws gave **3 strongly-bullish, 2 mixed**, so the machine proposal is withheld.
  - #757's build gave 5/0 on near-identical inputs; this is a tally of this build, never a rate.
  - The kept read is new prose, and the covenant and operating-driver LLM phases re-ran.
- **Every page** went through `refresh_dossier` with `valuation_bases_transform` and
  `leverage_caveat_transform`, under the kept synthesis. FUBO's seal was cleared by #441.
- **Anchors:**
  - **The CLI path:** `anchor-backfill` on 23 names: AMZN AORT BRBR BURL CNXC EPAM GOOGL IT NCNO
    NFLX NKE ORKA PARR ROST SMPL TECX TGT TJX UBER V VRRM WERN WLK.
  - **The assembly path (EDGAR only):** FUBO, LLY and MVST. Their committed anchors were assembled,
    and the backfill's CIQ vendor fill would have moved them for a reason unrelated to this PR
    (the #752 precedent).
  - **VITL:** NOT re-derived. It is held per row 32 (11), and gets the three blocks and the relabel
    only.
- **AMZN's operator R4 reason** is restored verbatim; the backfill replaced it again (row 27 (6)).

**THE FLEET, as written** (27 pages):

- **What CIQ's EV/EBITDA divides:**
  - **Rent-inclusive (13):** AMZN BURL CNXC EPAM MVST NCNO PARR ROST SMPL TGT TJX WERN WLK, within
    0.1% (TGT) to 4.6% (AMZN).
  - **Reported EBITDA (1):** NFLX.
  - **Indistinguishable (5):** BRBR GOOGL LLY UBER V.
  - **Neither pairing (4):** AORT IT VITL VRRM.
  - **An input missing (4):** FUBO NKE ORKA TECX.
  - A pre-pin probe the same day said "14" rent-inclusive. Its buckets summed to 28 on 27 pages;
    the pages are the count.
- **R1's ex-lease multiple at the page's price (15 pages):** AMZN 16.4x, AORT 27.2x, BURL 12.8x,
  CNXC 4.4x, EPAM 7.2x, NCNO 29.8x, NFLX 20.2x, NKE 11.2x, PARR 3.5x, ROST 19.4x, SMPL 5.7x,
  TGT 9.6x, TJX 17.8x, WERN 8.6x, WLK 11.3x.
- **CIQ's EBITDA against the filings:**
  - **Some quarter differs (16):** AMZN AORT BRBR EPAM IT NCNO NKE PARR ROST SMPL TGT TJX V VITL
    VRRM WLK.
  - **Matches (2):** NFLX UBER.
  - **No quarter could be rebuilt (6):** BURL CNXC GOOGL LLY MVST WERN.
  - **Absent (3):** FUBO ORKA TECX, which have no quarterly export matching the page's bands.
  - AMZN's LTM matches to the dollar while two quarters swap ±$2,500M, and its page says both.
- **The R1 base, main → this PR** (`anchor_base_value_per_share`, $; the dilution test beside it):

  | | main | now | dilution test |
  |---|---:|---:|---:|
  | TJX | 129.10 | 131.10 | 129.57 |
  | BURL | 322.06 | 327.60 | 322.32 |
  | IT | 364.07 | 383.86 | 383.37 |
  | EPAM | 398.58 | 403.84 | 403.29 |
  | NFLX | 52.00 | 53.21 | 52.31 |
  | SMPL | 44.10 | 44.83 | 44.83 |
  | GOOGL | 212.17 | 213.54 | 210.82 |
  | AMZN (R4) | 276.71 | 279.70 | 276.27 |
  | TGT | 158.47 | 159.27 | 158.51 |
  | WLK | 115.51 | 116.15 | 115.73 |
  | BRBR | 57.61 | 57.77 | 57.67 |
  | WERN | 32.53 | 32.67 | 32.53 |
  | NKE | 101.02 | 101.07 | 101.03 |
  | ROST | 166.18 | 166.18 | 165.27 |
  | VRRM | 21.79 | 21.78 | 21.78 |
  | CNXC | 93.27 | 93.11 | 93.11 |
  | AORT | 25.50 | 25.39 | 25.39 |
  | LLY | 699.65 | 699.65 (count refused) | — |
  | PARR | 47.86 | 47.86 (count refused) | — |

  A dilution test equal to the base is a filer whose diluted and basic weighted averages agree
  (AORT, CNXC, SMPL, VRRM). It is not a missing figure.

**WHY.**
- The review read 13.3x against reported EBITDA and got 19.1x. Nothing on the page said which
  pairing CIQ divides, and a label assumed fleet-wide would be wrong on half the pages, so it is
  measured on each one.
- CIQ's EBITDA is CIQ's own normalised figure, and every EV/EBITDA on a page divides it. The label
  "GAAP basis" is demonstrably false on the 16 pages where a quarter differs from the filings.
- The anchor divided a weighted average while the page's market cap, the scenario template and
  `valuation_basis.exit_share_count` divide the point-in-time count.
- The guard exists because the point-in-time count is not always the economic one, and the LLY
  case proves it.

**HOW VERIFIED.**
- **Real runs:** TJX's paid assembly and the fleet transforms on the 27 committed pages.
  - **Before any write:** a dry run of every anchor, both with and without CIQ's vendor fill.
  - **Then a share-count measurement:** each page's point-in-time count against the basic weighted
    average. This is what found LLY, V and PARR.
  - **After the writes:** a path-by-path JSON diff of every page against main showed only this PR's
    fields moved: the three blocks, the triangulation relabel, the single leverage caveat on 10
    pages, `valuation_basis.current_multiple` and the layer-refresh entries.
  - **TJX's re-assembled page** was compared with main field by field. Beyond this PR's fields,
    only the LLM phases and `assembled_at` moved.
- **Pins:** each guard has a positive and a negative pin, built from real shapes.
  - The share guard: LLY's and IT's filed counts, the margins on both sides, and V's no-average
    shape.
  - LLY's real page and frozen companyfacts, recomputed: the same equity on either count.
  - PARR and TJX at the page's price on their real fixtures.
  - The transform's rebuild on TJX's old-shape block and on LLY.
  - The quote precision: SMPL's and V's sentences, verbatim.
  - The GAAP lookbehinds: EPAM's and Concentrix's sentences.
  - The leverage caveat: regenerated from TGT's caveat as main had it, and refused on two
    candidates.
  - E2e on every committed page, both renderers. The web twin runs in node.
- **Mutation battery, 16 of 16 killed:**
  - the corroboration check removed;
  - each margin moved;
  - the diluted-average fallback removed;
  - a refused count divided anyway;
  - the at-price on the stock_info count;
  - the transform carrying old blocks;
  - `PAIRING_TOL` widened;
  - the GAAP lookbehinds dropped;
  - "continues to plan" dropped;
  - each recon threshold moved;
  - the quote-precision rule dropped;
  - the caveat transform taking the first of many;
  - each renderer's refusal row dropped.
- **Previews:** web screen and the FULL PDF export (`ds-print-full`, as the page's menu prints it;
  24 pages for TJX, the collapsed audit tier present) for TJX and LLY.
  `docs/dossier/valuation-bases-2026-10-21/screenshots/`.
- **The first full suite caught a scope error of this build.** The R1 formula constant
  (`midcycle.R1_FORMULA`) had been reworded to describe the anchor's new denominator. But it is the
  SCENARIO recipe that committed underwrite records stamp, and `run_recipe` refuses a record whose
  stamp differs: 44 tests went red, and every R1 record would have refused to recompute.
  - The constant is reverted to main's text; the anchor's count is stated on its own screen row.
  - The pages were restored from the post-assembly snapshot and the pass re-run once, so each page
    carries one entry per writer.
  - The same run made the count check's gap print unsigned with its direction in words ("5.5%
    above"). The screening block may carry no signed percentage (`test_parity_pins`).
- **Suite:** full offline suite (`-m "not network"`) with the shared price store UNLINKED, as in CI: **6,576 passed, 54 skipped, 2 failed** — V (`test_share_basis`) and MCK (`test_capital_panel_selection`), the CIQ data issues that fail identically on main (STATE row 32 (12)). After merging main (#758, #759): **6,592 passed, 54 skipped**, the same two failed; after #761: **6,603 passed, 54 skipped**, the same two.

**BOUNDARY.**
- **Pages:** the 27 committed dossiers at main `4b514dca`, refreshed 2026-10-21.
- **EDGAR:** the shared cache as read on 2026-10-21. The frozen fixtures in
  `tests/fixtures/companyfacts/` agree with it on every figure pinned.
- **CIQ:** the shared copy (`mosaic-theory-ta/data/manual/ciq`). TJX's 10 exports were sha256-matched
  to the operator's Drive. The reconciliation reads a page's quarterly export only where its hash is
  the one the page's bands carry.
- **Share counts:** each filer's latest diluted weighted average and the basic one over the SAME
  10-Q quarter, against `stock_info.shares_out` as committed.
- **"19 pages with a base"** = an `anchor_base_value_per_share` on main.
- **"Different"** = a quarter more than 2% and at least $1M from the rebuild.
- **Guidance:** the 118 EX-99.1 releases the 27 pages cite, re-parsed on this PR's code. The count
  went 100 → 120 items, all 20 additions `gaap diluted eps` (TJX ×12, EPAM ×8), each with a read
  period and none lost.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **One paid assembly:** TJX, with all phases re-run. The fleet moved under kept syntheses.
- **PARR's +3.3% is refused without a named cause.** Unvested restricted stock is the likely one,
  but it is not verified. The refusal says the counts cannot tell; the falsifier is a filer note
  naming the difference.
- **NCNO's page count (109.6M) is not its latest cover (105.7M at 2026-08-20).** The source is not
  traced (row 30). The guard refuses it, so nothing divides it.
- **A quote is evidence for the reader, never an attribution this code makes.** TJX's carries the
  release's section number ("3 IEEPA …") and WLK's carries table debris. Both are verbatim by rule.
- **VITL's anchor stays held** (row 32 (11)); **V stays inapplicable** until a re-assembly gives it
  a checkable count (row 32 (12)).
- **AMZN's reason was restored by hand again.** Until row 27 (6) is fixed, any backfill or
  re-assembly of AMZN overwrites it.
- **TJX's `price_store.declared_path` names this build's scratch store path**, as main's has since
  #757.
