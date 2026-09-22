---
id:
status: open
date: 2026-09-22
prs: []
supersedes:
superseded-by:
---

# Nike's EBIT is read as its own segment measure, NKE is bridged onto the CIQ share count, and the unvalued-anchor pin stops reading a living page

**WHAT.** Three code/test changes. The 2026-09-22 artifact pass needed them before it could run
green. That pass re-assembled BRBR, GOOGL, LLY and NFLX on fresh CIQ exports and onboarded NKE under
the overshoot book.

1. **A plain EBIT is a filer-defined segment measure.** Nike's chief operating decision maker runs
   the segments on EBIT and tags it `nke:EarningsBeforeInterestAndTaxes`, beside
   `us-gaap:GrossProfit`, on the same two segments. `_FILER_MEASURE` listed only the *adjusted*
   spelling, so gross profit won by default. NKE's first page printed NIKE Brand $19,300M /
   Converse $514M as "segment gross profit — the filer's measure". It now reads NIKE Brand EBIT
   $5,855M (12.9% of $45,222M) and Converse $18M (1.5% of $1,174M). No us-gaap element carries
   that name, so the new alternative can only match a filer's own extension.
2. **NKE joins `BRIDGED`, knowingly.** Nike is dual-class. Its undimensioned `dei` cover-page count
   stopped at 2015-07-17 (855,351,589 shares), 4,085 days old against the 180-day bound, and since
   then it tags each class separately. EDGAR's count is refused and the page takes the CIQ panel's
   own share column: the Visa shape. Pinned on NKE's real companyfacts fixture, added here.
3. **#636's unvalued-anchor pin reads frozen numbers.** It asserted that GOOGL's committed anchor
   publishes no base. That held until the backfill's CIQ bridge gave GOOGL $197.01, and the pin then
   went red for a reason that had nothing to do with the sentence it guards. That is a value pin
   on a re-drawn artifact, which the TEST-LAYER RULE forbids. The unvalued anchor is now built from
   GOOGL's own numbers on the day it published none (main at f4b0264) and rendered through the
   screening block.

**WHY.** The pass's first full offline suite ran 8 failed / 3,942 passed before anything was
committed. Three failures were code-side: this PR. The other five were artifact-side, fixed in the
pass itself. The EBIT gap was found separately, by reading NKE's first page against its 10-K:
the extractor had chosen gross profit while the filing tags EBIT on 24 facts.

**HOW VERIFIED.**
- **Nike fixture.** Trimmed from the real FY2026 instance (2.4 MB → 194 KB; 301 facts, 189 contexts)
  and proven to read IDENTICALLY to the full instance.
- **Pins on the real filing:**
  - ⊕ EBIT is chosen.
  - ⊖ The same filing with its EBIT facts removed falls back to gross profit, so the ORDER
    decides, not the fixture.
  - ⊖ us-gaap's pre-tax income, `OperatingIncomeLoss` and `GrossProfit` never match the filer
    pattern.
  - The page sentence is pinned exactly.
  - An end-to-end pin runs the block through both renderers.
- **No other page moves.** The other nine segment fixtures read unchanged; their existing pins
  are green.
- **Nike's share-count pin** runs on its real companyfacts fixture.
- **Suites.** This branch on main's pages: 3,943 passed, 44 skipped, 0 failed. This code plus
  the pass's regenerated pages: 3,953 passed, 43 skipped, 0 failed.

**BOUNDARY.**
- **Filings:** Nike 10-K accession 0000320187-26-000088, FYE 2026-05-31; companyfacts fetched
  2026-09-22.
- **Share-count bound:** `_SHARES_MAX_AGE_DAYS` = 180, unchanged.
- **Segment fixtures:** 10 committed (9 before this change).

**WHAT IT COSTS / WHAT IS ACCEPTED.** `_FILER_MEASURE` is still a list of spellings. When gross
profit is chosen, the heading calls it "the filer's measure", which is true for Gartner (gross
contribution tagged `GrossProfit`) but not provable in general. A filer whose EBIT uses a spelling
not listed will be mislabelled the way Nike was. ACCEPTED, because nothing in the instance says
which measure the CODM uses. FALSIFIER: the next page whose gross-profit line sits beside a
segment-tagged profit measure the pattern missed.
