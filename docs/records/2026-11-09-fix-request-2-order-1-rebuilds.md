---
id:
status: shipped
date: 2026-11-09
prs: [949]
supersedes:
superseded-by:
---

# Fix request 2, order 1: VITL, VRRM, EPAM and WLK are re-assembled once each on their 2026-11-09 CIQ exports, and V and UBER under their own cap, all priced at the 2026-11-06 close — the fixes already in code reach their pages, VITL with seven losses the operator accepted, and no machine proposal moves; TECX is built too, with two losses the operator accepted

**WHAT.** TeamNostra's re-audit (fix request 2, 2026-11-09) found pages still carrying figures that
are fixed in code but were never rebuilt. The operator re-exported the full CIQ set for VITL, VRRM,
EPAM and WLK on 2026-11-09 and approved one paid build each, capped at $25 in total ("then start the
rebuilds with $25 cap"). Two names were added to this PR later, each under its own cap; caps are never
pooled:
- **V and UBER:** first "yes, add V and UBER with $10 cap". When the two estimates (V ≈ $3.8, UBER ≈ $6.8)
  passed $10 together, the operator ruled "Both, raise cap to $12". Both were built, for $10.69.
- **TECX:** "TECX ok with $10 cap". Its $0 precheck exited 1 and it stopped unpaid. On the losses
  (below) the operator ruled "Accept both, build now" (2026-11-10), and it was built once for $1.46.

All operator words were relayed verbatim by the coordinating session.

- **Code.** The first four builds ran on main `cb8139ee`, which carries #923 (fix 3a), #927 (fix 4a)
  and #932 (row 57). V and UBER were built after the merge below, on main `6fbbb4a2`. Neither line
  carries #930 (fix 3b), which was open at the time.
- **Order 2.** Main then took #936 (order 2's pages, `6fbbb4a2`). The branch was fast-forwarded onto
  it (it had no commits of its own), and #936's own $0 writer gave each page its customer count
  (`vinci ciq-reread --field customers_listed`).
  - That re-read rendered each `.md` again on the merged code; no `.md` was hand-merged.
  - Its other two writers had nothing to do on these pages: `--field surprise_history` read
    UNCHANGED on all four, and `caveat-reword` found no retired headline.
  - V, UBER and TECX were built after that, on `6fbbb4a2`, so V's and UBER's counts were written at
    assembly (353, 37; the re-read reads UNCHANGED on both). TECX has no current roster, so it has no
    count; the re-read SKIPPED it.
- **Main again, at `d1a91f0a`** (#938, F, `85b124b0`; and order 2's outputs). This was again a
  fast-forward, with STATE.md, the fix log and `tests/test_footnote_every_figure.py` merged three-way
  to keep both sides. All seven pages were re-rendered at $0 on the merged code
  (`refresh._rerender_only`), and every `.md` came out byte-identical; no JSON moved.

| | VITL | VRRM | EPAM | WLK |
|---|---|---|---|---|
| committed page before | 2026-08-18, ext `2026-08-16.1` | 2026-08-18, ext `2026-08-16.1` | 2026-09-17, ext `2026-08-16.1` | 2026-10-26, ext `2026-10-09.3` |
| $0 precheck | exit 1, 6 regressions → operator: "Accept, build VITL" | exit 0 | exit 0 | exit 0 |
| run · cost · calls | `d7e1ac46` · $2.59 · 6 | `b9fd1442` · $5.27 · 8 | `53365700` · $4.49 · 8 | `29d2fce2` · $4.44 · 11 |
| price date (close) | 2026-11-06 ($9.52) | 2026-11-06 ($2.19) | 2026-11-06 ($159.31) | 2026-11-06 ($63.49) |
| lean (5 draws) | mixed (5/5) | mixed (3 mixed / 2 strongly-bearish) | mixed (5/5) | mixed (5/5) |
| machine proposal | none (was none) | none (was none) | none (was none) | none (was none) |
| R1 anchor base $/sh | 30.0469 → **None** | 21.7803 → 23.2328 | 403.8351 → 391.7766 | 116.1475 → 124.0268 |
| UNTRACEABLE caveats | 0 → 4 | 0 → 2 | 0 → 10 | 0 → 4 |
| material rows | none demanded | Impairment of Goodwill FY24 −97.1, LTM −64.0; Asset Writedown LTM −42.5 — all stated | none demanded | Restructuring Charges FY25 −640.0, LTM −581.0 — both stated |
| Sourced fields lost | 6, accepted (below) | 0 | 0 | 0 |
| 10-Q · newest release read | `0001193125-26-444385` · `…-444348` | `0001628280-26-068455` · `…-068453` | `0001352010-26-000052` · `…-000048` | `0001262823-26-000080` · `…-000076` |
| customers listed ($0, #936) | 15 | 4 | 172 | 16 |

| | V | UBER | TECX |
|---|---|---|---|
| committed page before | 2026-10-26, ext `2026-10-09.3` | 2026-10-26, ext `2026-10-09.3` | 2026-09-28, ext `2026-08-16.1` |
| $0 precheck (on `6fbbb4a2`) | exit 0 | exit 0 | exit 1, 2 regressions → "Accept both, build now" |
| run · cost · calls | `bdf37011` · $4.15 · 8 | `46b8ba39` · $6.54 · 10 | `3fdddf73` · $1.46 · 5 |
| price date (close) | 2026-11-06 ($422.65) | 2026-11-06 ($68.59) | 2026-11-06 ($20.64) |
| lean (5 draws) | strongly-bullish (4 / 1 mixed) | mixed (4 / 1 strongly-bullish) | mixed (4 / 1 "strongly-bearish on reported economics") |
| machine proposal | none: withheld, the draws disagreed (was withheld, 4/1) | none (was none) | none (was none) |
| UNTRACEABLE caveats | 0 → 4 | 0 → 7 | 0 → 9 |
| material rows | none demanded | none demanded | none demanded |
| Sourced fields lost | 0 | 0 | 2, accepted (below) |
| 10-Q · newest release read | `0001403161-26-000104` (Q3 FY26; the FY2026 10-K is not filed yet) · `…-000126` | `0001543151-26-000041` · `…-000039` | `0001193125-26-450019` · `…-407823` |
| customers listed | 353 (written at assembly) | 37 (written at assembly) | none: no current roster (`ciq-reread` SKIPPED) |

- **UBER'S PAGE IS NOT PRICEABLE ON R4, COMMITTED AS BUILT** (operator, 2026-11-10: "Commit new page +
  to-do").
  - `valuation_basis.priceable` goes True → False, and `scenario-propose` refuses UBER.
  - The cause: its bridge reads the 2026-09-30 balance sheet ($5,356.0M claims), while CIQ's TEV less
    market cap in the comps export (dated 2026-11-04) is $8,973.0M, a $3,617M gap. The old page agreed
    at 5,827.0 on both sides, on the June balance sheet.
  - The page itself says so: "DISAGREES with CIQ's current TEV less market cap ($8,973.0M) by
    $-3,617.0M — the Financials and comps exports sit on different balance sheets; re-pull before an R4
    record reads th[e bridge]".
  - The precheck read "0 regressions": `valuation_basis` is present either way, and values are not
    compared. That is a second RD-D4 instance, on its fix-log row beside VITL's.
  - The to-do is STATE §5.0 row 28: re-export UBER's comps once CIQ's comps TEV reflects the
    2026-09-30 balance sheet.
    - If only the comps are re-exported, the $0 path is `refresh.refresh_dossier(<UBER page>,
      top_level=refresh.ev_bridge_transform("UBER"))`. It reads from the page's own stamped
      Financials and Estimates, and `valuation_basis` is re-derived on the write. Run today, it would
      write the same 5,356.0 against 8,973.0.
    - If those exports are re-exported too, the transform leaves the page alone, and UBER needs a
      paid rebuild.
- V has no Credit Health Panel in CIQ (operator), and its precheck lost nothing to that.
- **V is another case for the unanimity gate.** Its lean is strongly-bullish on 4 of 5 draws, so
  `derive_proposal` withholds the BUY the mapping would make, exactly as on its old page (also 4/1).
  The #930 session is drafting that rule's design.
- One of TECX's draws returned a label outside the three known leans ("strongly-bearish on reported
  economics"). The modal label is mixed, so the kept read and the proposal are unaffected.
- V's QA flags rose from 8 to 101. 87 of them are "operating-drivers: Tier-B period … is not stated in its
  quote": the period guard flags each driver row whose fiscal-quarter label its quote does not repeat.

**VRRM IS A LIVE LEDGER POSITION** (AVOID_TERMINAL, entered 2026-06-17, matures 2026-12-14).
- Its machine proposal does not change: it was mixed and proposed nothing, and it is mixed now and
  proposes nothing.
- Two of five draws read strongly-bearish. Had that been the modal label, the page would have
  proposed AVOID_TERMINAL; the draw tally is on the page.
- No ledger, scenario or scoring file is touched, and no `scenario-propose` ran.
- VRRM's latest call is Q2 (2026-08-05). CIQ has no Q3 transcript for it (operator, 2026-11-09). Its
  Q3 10-Q and Q3 release are read; nothing works around the missing call.

**VITL'S LOSSES, ACCEPTED BY THE OPERATOR.** The operator said "Accept, build VITL" on 2026-11-09,
relayed by the coordinating session. Each reason below is the precheck's own:
- `capital_structure.covenant_term_rows`:
  - the committed table held 7 rows and 0 values, every row "not stated in latest 10-K
    0001193125-26-073423 · vitl-ex10_10.htm";
  - the E5 identity guard now refuses that exhibit, which "declares itself no agreement at all".
- `drawdown_cause.gap_down_dates` and `drawdown_cause.revised_guidance`:
  - the 2026-02-26 and 2026-05-07 gap-downs left the rolling window ("no gap-down from 2026-05-10 to
    2026-11-06");
  - VITL has no scenario record, so no anchor carries them.
- `leverage_survival.net_debt_to_ebitda`, `quality.net_debt_to_ebitda` and `quality.net_debt_to_ocf`
  (0.0x, 0.0x and 0.3x on the old page): CIQ's LTM EBITDA is now −$14M and its OCF −$49M, so each is a
  "ratio meaningless".
- **A seventh, which the precheck does not compare** (it compares presence, not values; row 43): the
  R1 anchor base, 30.0469 a share → None (`anchor.applicable` false). Accepted separately: "yes, accept
  VITL's anchor loss".
  - The anchor's own reason: the latest quarter (2026-09-27) has no positive LTM EBITDA, so the
    ex-lease history has no current point.
  - CIQ's TEV/LTM EBITDA band mixes lease bases (`band_incoherent`), so its median cannot price
    reported EBITDA either.
  - The root cause is the three ratios'. It was found after the build and reported to the
    coordinating session for the operator.
  - It is a live instance of TeamNostra's RD-D4 (order 4): "the pre-spend check compares presence only,
    yet says nothing is lost". Here the check said six were lost and missed the seventh, because the
    `anchor` block it compares by presence is still present. The evidence is on RD-D4's fix-log row,
    whose status stays `open`.

**TECX'S TWO LOSSES, ACCEPTED BY THE OPERATOR** ("Accept both, build now", 2026-11-10). Its re-export
of 2026-11-09 has 8 files: no Credit Health Panel and no transcripts (operator). Bars were refreshed in the
store copy (598, 2024-06-21..2026-11-06). The precheck on `6fbbb4a2` exited 1 with 2 regressions, and the
paid page lost exactly these two. Neither comes from the missing panel or the missing transcripts.
- `capital_structure.summary` → UNKNOWN, "no aggregates parsed". It is read from CIQ Financials →
  Capital Structure Summary, not the Credit Health Panel. The quarterly export's newest column,
  "3 months Q3 Sep-30-2026", states '-' on every aggregate row; the committed page read Q2 (leases
  4.399). The latest-cell contract reads a marker as UNKNOWN, never the older value. A later re-export
  should restore it once CIQ fills Q3.
- `concentration.customers` → UNKNOWN. CIQ states no recently disclosed customers, and its two 2023
  AVROBIO counterparties are "prior and not recently disclosed". STATE row 41 recorded this as the
  designed result of the reader fix (`docs/records/2026-11-01-four-small-ciq-reader-fixes.md`).
- The precheck also listed 5 fields newly present, 0 post-spend refusals, and freshness in date.
  The paid page gained 3 Sourced fields, the drawdown anchor's.

**THE FIXES THESE PAGES NOW CARRY**, each read off the committed JSON:
- **Audit E2-D10 (VITL):** Q2 2026 adjusted EBITDA −26.6 is on the Q2 release `0001193125-26-336692`.
- **Audit E2-D16 (VITL):** no receivables row in the revenue concentration. The page reads the Q3
  10-Q, whose revenue table names Customers A (20%) and B (11%) and whose receivables table names A, B,
  C (13%) and D (10%). The page carries A and B.
- **Audit E2-D12 (VRRM):** the $94.3M cash-flow change is gone. The one-offs on `0001193125-26-335111`
  are 64.0 and 40.4.
- **Audit E2-D11, EPAM's half:** Q2 2026 revenue 1,415.0 (`0001352010-26-000043`) and Q1 2026 1,400.0
  (`…-000026`), and Q3 2026 1,426.0 on the new release. WERN's and MVST's halves wait for their
  re-exports.
- **D-D1 (WLK, the lease fix):**
  - The ex-lease band names its 7 unpriced quarters: 2021-09-30, 2022-03-31, 2022-06-30, 2022-09-30,
    2023-09-30, 2024-03-31 and 2025-09-30, the seven STATE row 41 named.
  - Its median moves 7.9102 over 34 closes (as of 2026-08-05) → 8.3283 over 28 (as of 2026-11-04),
    and the R1 base 116.1475 → 124.0268.
  - The Q3 10-Q moves the other legs: net debt 3,215 → 3,093, D&A 1,178 (FY) → 1,157 (TTM), LTM
    revenue 11,294 → 11,437.
  - Extraction `2026-10-09.3` → `2026-11-09.asof-cut`.
- **D-D5 (WLK):** its material row is now Restructuring Charges (FY25 −640.0, LTM −581.0), stated by
  the synthesis. `uncited_material_figures` returns [] and `material_direction_flags` [] on all four.
- **#652 (VRRM):** the covenant table is headed "AMENDED AND RESTATED REVOLVING CREDIT AGREEMENT", not
  "2021 Term Loan Due 2028".
- **C1 (VRRM):** the share-count trend reads cover-dated counts: 164,804,157 (2024-10-25) →
  152,009,343 (2026-10-27), −7.8%.
- **Rows 54, 55 and 57:**
  - fix 3a's judgment labels are gone: WLK's "gradual bleed" 1 → 0, and "trailing only"/"trailing-only"
    1–2 → 0 on each of VRRM, EPAM and WLK;
  - `mechanical.disclosure_gaps` is on all four (VITL 5, VRRM 0, EPAM 6, WLK 5);
  - `primary_source.releases_after_price_date` and `catalyst_path.guidance_after_price_date` are
    present and empty on all four.
- **Not carried:** #930 (fix 3b), open when these were built.

**THE PINS** (`tests/test_pages_await_parser_rebuild.py`).
- **Five pass now and lose their strict-xfail markers.** Each was shown by pointing the module's
  `_PAGES` at the old JSON:

  | pin | new page | old page |
  |---|---|---|
  | E2-D10, VITL | pass | fails at `cb8139ee` |
  | E2-D16, VITL | pass | the Q2 pin fails at `cb8139ee` (Customer C present) |
  | E2-D12, VRRM | pass | fails at `cb8139ee` |
  | E2-D11, EPAM's half | pass | fails at `cb8139ee` |
  | E2-D15, NFLX's half | pass | fails on NFLX's 2026-10-26 page |

- **E2-D16 was re-pointed** from the Q2 10-Q `0001193125-26-336753` to the Q3 `…-444385`, because the
  page moved to the newer filing. That is the pin's own `LookupError` path. It now asserts that
  neither receivables row (C, D) appears.
- **NFLX's half landed with its 2026-10-29 assembly** (#867, `1c5df21b`) and was kept by 2026-11-05
  (#918). The fix log's dispute note gives #918.
- **The combined pins are split**, one page per test, so each flips on its own rebuild:
  - E2-D11 becomes EPAM (passing), WERN (strict-xfail) and MVST (strict-xfail);
  - E2-D15 becomes NFLX (passing) and WERN (strict-xfail).
  - FUBO stays strict-xfail.
- **WLK's D-D1 has no pin.** Its lease-basis figures and extraction version are above.

**THE 44 TESTS THE PAGES MOVED, AND WHAT EACH ONE NOW DOES.**
- The first four pages moved 26.
- V's and UBER's moved 6: 4 on UBER's fixture, plus F's [V] and [UBER].
- The final suite on the merged tree found 12 more, on V's, UBER's and TECX's living pages (below). These are classified by attribution: the
failing files re-run with main's pages, mirrors and tracking fixtures swapped back in. The operator
approved the dispositions, relayed by the coordinating session; all are in one test-only commit, as
#914's were.
- **V's and UBER's pages, built later, moved 4 more**, all on UBER's tracking fixture, read off its
  June-quarter vintage (UBER sits in both CIQ comparison files at 2026-06-30). Main `6fbbb4a2`'s copy
  is frozen as `companyfacts_frozen/UBER.json`. The pins:
  - `test_net_debt_one_builder::test_borrowings_inside_the_bare_total_are_not_added` and
    `test_net_debt_securities_leg[UBER]`, which read the frozen copy first;
  - `test_cross_check::test_an_abandoned_alias_is_never_served_for_a_later_period` (32 revenue filing
    dates) and `test_share_basis::test_a_current_count_is_still_accepted` (its count at 2026-08-10),
    now pointed at it.

  All four are red on the new vintage and green on the frozen copy, which is restored byte-for-byte.
- **Twelve more living-page fixtures → frozen pages**, found by the final CIQ-linked suite. The frozen
  pages are `tests/fixtures/frozen_pages/2026-10-26/UBER/`, `2026-10-26/V/` and `2026-09-28/TECX/`, each
  byte-identical to main `d1a91f0a`'s page.
  - **UBER ×8:** `test_r4_template` ×6 and `test_valuation_basis` ×2 need a page `scenario-propose`
    accepts on R4. UBER joins SMPL in `test_r4_template`'s `_FROZEN`, and `test_valuation_basis` reads
    the frozen page in its two R4 value pins only.
  - **V ×1:** `test_guidance_basis`'s Visa arithmetic (FY25 40,000 × 1.13 = the FY26 guide 45,200, the
    example `ciq_sheets` and `render` cite). The new export guides FY 2027 at 50,493.3, about 1.10 ×
    FY26's 45,903.
  - **TECX ×3:** `test_benchmark_figures_refresh` runs on the page the committed price fixtures
    reproduce at 2026-09-22.
  - Each is red under a mutation: the new UBER page in the frozen slot (all 8), V's frozen FY25
    40,000 → 40,100, and the new TECX page in its slot. Each file is restored byte-for-byte.
- **Living-page value pins → frozen pages (8).** Frozen pages are `tests/fixtures/frozen_pages/
  2026-08-18/VITL/`, `2026-08-18/VRRM/` and `2026-09-17/EPAM/`, each byte-identical to main
  `cb8139ee`'s page. The pins:
  - `test_ev_gap_render[EPAM]` (multiple-dominant → earnings);
  - `test_release_amount_scale` ×3 (VRRM's Q1 release left the page);
  - `test_segment_facts` (EPAM's page now has a two-segment block);
  - `test_ev_gap_routing` ×3 (VITL's FY consensus dispersion 263.7%; the new one routes three-ratio).

  Structural halves stay on the living page.
- **Tracking-fixture value pins → `tests/fixtures/companyfacts_frozen/` (11).** EPAM, WLK and VRRM are
  frozen there, each byte-identical to main's tracking fixture, with cash instant 2026-06-30. The pins:
  - `test_net_debt_one_builder` [EPAM] and [WLK], and `test_net_debt_securities_leg` ×2 (WLK). These
    already read the frozen copy first, so they needed no test change.
  - `test_cross_check`'s self-funding cite (WLK).
  - `test_share_readers_cover_dated` ×4 and `test_cover_dated_share_counts` ×2 (VRRM's August shape).

  The regenerated tracking fixtures stay (RUNBOOKS §i step 6): with main's stale VRRM fixture,
  `test_dilution_denominator` fails harder ("a committed anchor the ciq=None recompute cannot value").
- **Every moved pin is shown red under a mutation of its frozen value**, and each file is restored
  byte-for-byte. The mutations: EPAM's anchor shape; VRRM's Q1 release dropped; EPAM given the
  two-segment block; VITL's consensus high = low = median; each frozen companyfacts copy swapped for
  the new vintage.
- **The designed list-shrink (1):** EPAM, VRRM and WLK leave `ANCHORS_AWAITING_BACKFILL`, because their
  committed anchors equal a fresh recompute.
- **A tolerance from the stored precision (1):** `test_anchor_point_in_time_shares`.
  - Both per-share values are `round(…, 4)` (`anchor.py`), so the two equities may differ by up to
    0.5e-4·so + 0.5e-4·(so + inc): ≈ 4.3e-6 relative on VRRM's ~23.2 bases, ≈ 1.3e-7 on LLY's ~752.
  - The fixed `rel=1e-6` refused VRRM's 2.7e-6.
  - A new negative pin holds a 1e-5 relative mismatch outside the bound, on VRRM's real numbers.
- **An expired premise updated, not deleted (1):** "no committed page renders a footnote mark".
  EPAM's page is the first of the nine it renders to carry `figures` (38, none computed). The test now
  requires a sources block exactly on footnoted pages, and a ‡ exactly where a figure is computed.
- **F — fixed by its own PR, #938 (`85b124b0`), merged first (6):**
  - `test_footnote_every_figure::test_no_committed_page_states_a_figure_no_point_could_cite`
    [EPAM], [VITL], [WLK], [V], [UBER]: "DisclosureGap.basis", "DisclosureGap.item";
  - `test_parity_pins::test_every_assembled_field_reaches_both_dossier_renderers`: "disclosure_gaps
    (md=- web=Y)".

  These are the first pages carrying #927's field, and it trips two guards it never met: a gap's text
  states numbers under an optional, usually absent, ref; and neither renderer draws the field while
  the web names it in its changelog string. #938 is a test-only fix with failing-first tests, cut
  from main. After it merged, this branch merged main and all six pass on these pages; the other
  disposition classes took no change for it.

**THE PRIMARY STORE'S SHA256 MOVED, NOT BY THIS BUILD, AND ITS CONTENT DID NOT.** The brief asked for
the primary's `data/vinci.db` hash before and after, equal. It is not equal.
- **Readings:** `0263451a…3b3c` at 15:47 UTC and again after this session's refresh (~15:55 UTC);
  `3106433f…a363` from 17:17 UTC to at least 18:44 UTC. The file was modified at 16:26:53 UTC and
  grew 399,138,816 → 399,147,008 bytes (2 pages of 4,096). The schema is identical.
- **Not this session's writes:**
  - every vinci command ran from this worktree, against its copy;
  - all four pages stamp `price_store.resolved_path` = this worktree;
  - the primary `.env` sets no path (its variable names are keys only);
  - no code resolves a store outside its checkout (`git-common-dir` is read only by
    `vinci/evals/replay.py`, for a path check).
  - 16:26:53 fell inside EPAM's build (16:20:08 → 16:30:18), whose page stamps the copy too.
- **Content unchanged.** Read with `mode=ro` against this worktree's 15:47 copy, these are
  byte-identical: `decision_ledger` (1 row: VRRM, AVOID_TERMINAL, 2026-06-17), `candidate_records`,
  `universe_snapshot`, `meta`, every price row before 2024-11-11, and every price row of a name this
  session did not refresh. `issuers` and `securities` differ only by this copy's own refresh rows.
- **The writer is unknown.** RUNBOOKS §l's scoring run links this store into a clean worktree (row 38).

**HOW VERIFIED.**
- **Pre-spend, at $0, before each paid build.** These are the brief's INPUTS lines, quoted from each
  precheck:
  - VITL, `inputs-20ffa4f21c0095c3`: 11 CIQ exports, 548 responses (efts 1, finra 1, polygon 14,
    sec 532), 2 price series; ciq 0 same, 2 changed (estimates, financials/quarterly), 7 only here.
    Exit 1, re-run before its build: the same six.
  - VRRM, `inputs-127d73cbc94ecc1c`: 11 exports, 237 responses (efts 2, finra 1, polygon 14,
    sec 220), 2 price series; ciq 0 same, 2 changed, 7 only here. Exit 0; 3 newly present.
  - EPAM, `inputs-4b4a49e8ca084f95`: 11 exports, 306 responses (efts 1, finra 1, polygon 14,
    sec 290), 3 price series; ciq 0 same, 2 changed, 7 only here. Exit 0; 6 newly present, the
    underwrite-anchored drawdown among them.
  - WLK, `inputs-f0f29cc55c01e1e8`: 11 exports, 323 responses (efts 2, finra 1, polygon 14,
    sec 306), 7 price series; ciq 0 same, 2 changed, 7 only here. Exit 0; 2 newly present.
  - Every freshness line: oldest panel 3 days old (comps, 2026-11-06), refused from 2026-12-22.
- **The paid pages match their prechecks field for field:** VRRM, EPAM and WLK 0 lost; VITL exactly
  the six.
- **After the merge with main, on the merged code** (extraction `2026-11-09.order2-pages`),
  `vinci dossier precheck` exits 0 with 0 regressions and 0 post-spend refusals on all four, each
  against its new committed page.
- **`python frontend/build.py`** moved only these four names' mirrors (each byte-identical to its
  source), their lead lines in `frontend/dossiers/index.json`, and the EPAM underwrite mirrors'
  `nextEvidence` (the 2026-11-05 print passed; the cadence estimate is now 2027-02-04).
- **CIQ:** the 44 export files (11 each) are byte-identical by sha256 before the first build and after
  the last.
- **Tracking fixtures:** `scripts/build_companyfacts_fixture.py` was run for each of the four
  (RUNBOOKS §i step 6). VITL's, VRRM's, EPAM's and WLK's now read their September-quarter 10-Qs.
- **The CIQ-linked failures the coordinating session expected V's and UBER's pages to clear:**
  - `test_share_basis::test_the_bridged_name_reconciles_cap_shares_and_price_exactly` clears. It
    compares the page's cap ÷ shares with the printed close of V's comps export on disk. The old page's
    $385.45 came from the old export; the new page reads the re-export, whose printed close is $422.65.
  - `test_estimate_year_derivation[V-want3]` and `test_ev_bridge::test_claims_equal_ciqs_current_figure_on_every_committed_name`
    (UBER 5,356 vs 8,973) do NOT clear, and no page can clear them. Each reads the CIQ exports on disk,
    not a page:
    - V's re-export's first estimate year is FY2027 (`['FY27E', 'FY28E']`), because V's FY2026 ended
      2026-09-30;
    - UBER's bridge is computed from its own Financials export against its own comps.
  - Both fail on main with today's CIQ folder linked, and both skip in CI.
- **The six failures that are main's, not this branch's** (CIQ folder linked, store copy present; they
  skip in CI): `test_estimate_year_derivation[V-want3]`;
  `test_ev_bridge::test_claims_equal_ciqs_current_figure_on_every_committed_name` (UBER, above);
  `test_forward_consensus::test_every_spread_sits_on_its_own_trends_figure` [GOOGL] and [LLY];
  `test_forward_multiple_history::test_nm_and_no_data_stay_different_states`; and
  `test_store_freshness::test_the_gated_set_includes_the_benchmark_not_only_the_dossiers` (this
  worktree's store copy).
- **Suites,** on the final tree (main `d1a91f0a` plus this branch), counted from the progress lines:
  - **CIQ folder linked, store copy present** (`pytest -m "not network"`): 10,083 passed, 104 skipped,
    6 xfailed, 6 failed. The six are main's, named above.
  - **CI-style** (`bin/commit`: no CIQ link, no store, no cache): ruff "All checks passed!" and
    `mypy --strict` "Success: no issues found in 204 source files" on both commits. pytest gave
    9,625 passed, 568 skipped, 6 xfailed, 0 failed on `2f4b1ab4`, and 9,663 passed, 556 skipped,
    6 xfailed, 0 failed on `365c879e`, its merge with main `fd123ada` (AORT retired, #930 fix 3b,
    fix request 2 E1 and F).
  - **The merge with `fd123ada`** conflicted in STATE rows 28, 41 and 54 (merged word by word, with no
    overlap), the frozen-pages README, `test_dilution_denominator` (AORT retired, and EPAM, VRRM and
    WLK landed) and `test_ev_gap_render`; all were resolved keeping both sides. The seven pages
    re-render byte-identically at $0 on the merged code.

**BOUNDARY.**
- **Runs:**
  - `b9fd1442` 16:06:20Z, `53365700` 16:20:08Z, `29d2fce2` 16:32:16Z and `d7e1ac46` 17:21:20Z, all
    2026-11-09. Model `claude-opus-4-8`, extraction `2026-11-09.asof-cut`, main `cb8139ee`. 33 calls,
    0 failed, $16.79 at list price ($16.790974) of the $25 cap.
  - V `bdf37011` 19:19:31Z and UBER `46b8ba39` 19:32:19Z, extraction `2026-11-09.order2-pages`, main
    `6fbbb4a2`. 18 calls, 0 failed, $10.69 ($10.690778) of the $12 cap.
  - TECX `3fdddf73` 2026-11-10 03:17:53Z, extraction `2026-11-09.order2-pages`, main `6fbbb4a2`.
    5 calls, 0 failed, $1.46 ($1.463628) of its $10 cap.
- **Draws:** 5 per build; they are tallies, never rates.
- **UNTRACEABLE:** the page's caveats matching "untraceable figure".
- **Field comparison:** every dict carrying `value` and `status`, outside lists, across the whole
  page. The old page is main `cb8139ee`'s.
- **Store:** a COPY of the primary's `data/vinci.db` (sha256 `0263451a…3b3c`; these names' bars ended
  2026-07-02 in it, the store's newest bar 2026-08-11), refreshed in the copy only.
  - `vinci refresh VITL VRRM EPAM WLK IWM MDY ATKR CLF LYB NUE STLD WCC --aggs --start 2021-07-01
    --end 2026-11-06` (the 2026-11-09 session had not closed). Polygon served 499 bars each to 11,
    2024-11-11..2026-11-06; the four names and IWM run 2021-06-21..2026-11-06 with no gap.
  - ATKR was skipped ("no US issuer for ticker 'ATKR'"), so WLK's cohort reads it unpriced. MDY was new
    to the store, so it has 499 bars only.
  - There was no Tiingo call: its key was removed in-process. Keys were loaded in-process from the
    primary's `.env` and never printed.
- **CIQ:** `data/manual/ciq` was a symlink to the primary's Drive link during the builds. It was removed
  with `unlink` before the CI-style gate.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$16.79 of $25, $10.69 of $12, and $1.46 of $10**, the three caps never pooled. No build was
  re-rolled and none was held.
- **VITL's seven losses and TECX's two are accepted by the operator.** The page states each one (UNKNOWN with its
  reason), and the R1 base is not applicable until VITL's LTM EBITDA turns positive.
- **F is owed before this merges.** Until it does, the four F tests are red on these pages, on main's
  test code.
- **The primary store's hash moved without a content change.** The writer is unknown; row 38 says so.
