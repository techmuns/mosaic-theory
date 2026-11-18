---
id:
status: shipped
date: 2026-11-18
prs: [1119]
supersedes:
superseded-by:
---

# W50's page refresh: 8 of the 11 active pages' R1 screening anchors re-derived at the current multiple, the median beside it, and W61's split written on the 7 with a screen value ($0, anchor-backfill, no LLM); VRRM refreshed by its own rebuild (#1121); NCNO unchanged; BRBR deliberately excluded (its own pending D&A backfill); the 15 watch pages left as committed

**WHAT.**
- **Pages refreshed.** `anchor-backfill` re-derived the anchor on EPAM, GOOGL, IT, LLY, SMPL, TJX,
  VITL and WERN on head code `8ea51e99`, which carries W50 (#1114) and W61 (#1118). It is the
  anchor-only $0 writer: EDGAR and the CIQ bridge, with no LLM and no re-assembly.
  `frontend/dossiers` was then mirrored, byte-identical to each page.
- **W61's split rides with it** (coordinator B, 2026-11-18, once #1118 merged). `compute_anchor`
  now writes `anchor.gap_split` wherever it writes a screen value, so it is on 7 of the 8. VITL
  publishes no screen value and so carries no split. GOOGL's split states its refusal (CIQ's 22.9x
  is struck on an EBITDA the page cannot identify) and withholds V0 and the margin effect, never
  substituting another EBITDA. Its close is also flagged stale (42 days), and so is TJX's (75 days).
- **Before → after** (multiple, then screen value per share):

  | Page | Multiple | Screen value / share |
  | --- | --- | --- |
  | EPAM | 23.8347x (median) → 9.8862x (current, 2026-11-05) | $391.78 → $173.28 |
  | GOOGL | 17.4518x → 22.8888x (2026-09-30) | $225.54 → $292.90 |
  | IT | 22.9576x → 9.4263x (2026-11-11) | $371.67 → $136.91 |
  | LLY | 25.6827x → 27.8531x (2026-11-02) | $752.24 → $820.15 |
  | SMPL | 18.2256x → 5.1351x (2026-10-27) | $46.48 → $11.37 |
  | TJX | 15.8450x → 16.3423x (2026-08-28) | $132.14 → $136.20 |
  | VITL | 3.8802x → 1.4439x (2026-11-06) | no base either way (lease-refused) |
  | WERN | 6.6883x → 6.8962x (2026-11-09) | $38.32 → $39.93 |

- **VRRM is refreshed by its own rebuild, not here** (coordinator B, 2026-11-18). A's full paid
  rebuild (#1121, on `8ea51e99`) is VRRM's page of record. It already carries W50's anchor (3.5566x,
  the close of 2026-11-06; base $1.3435) and W61's split, with its leverage flag. This pass derived
  the same multiple and base for VRRM; its files are restored to main here, so the two PRs share
  no page.
- **NCNO is unchanged.** It is an R2 page whose anchor stops before the multiple leg.
- **BRBR is DELIBERATELY EXCLUDED** (coordinator B, option A, 2026-11-18).
  - Its re-derivation also moved `anchor.d_and_a` from 18.6, "consolidated latest FY", to 19.8,
    "trailing twelve months to 2026-06-30".
  - That move is BRBR's own pending backfill, not W50. It is listed in `ANCHORS_AWAITING_BACKFILL`
    (`tests/test_dilution_denominator.py`).
  - BRBR was restored exactly to main. It takes the W50 anchor at its paid rebuild, after its FY26
    10-K and the operator's CIQ export, which will carry the new anchor and its D&A basis together.
- **The watch pages are left as committed** (operator ruling, 2026-11-13): AMZN, BURL, CNXC, FUBO,
  MCK, NFLX, NKE, ORKA, PARR, ROST, TECX, TGT, UBER, V and WLK. Each picks up the W50 anchor at its
  next build once it goes active.

**WHY.** The operator approved the preview on 2026-11-18 ("Approve as shown") and ordered the
refresh in these words: "Run the refresh". #1114 merged as `8edf9ebb` and #1118 as `8ea51e99`.
W50's round-trip pin was restated first (#1117, `48583be9`), because it held that no committed
anchor was W50's. A test change cannot ride in an artifact commit.

**HOW VERIFIED.**
- **Dry run first.** It ran on `8edf9ebb` and matched the impact run on #1114 value for value.
- **Every page diffed leaf by leaf** against main `8ea51e99`, after the rebase onto #1116, #1117
  and #1118, and again at `aa9fde84` (#1120, one test file), where no page had moved. The moved leaves:
  - `anchor.multiple` value, source, statistic, as_of and median, plus `anchor.computed_at`, on
    all 8;
  - `anchor_base_value_per_share` and `anchor_ev_ebit` on 7. VITL is lease-refused and publishes
    neither, at either ref;
  - the diluted twin on 6. LLY prices on the diluted weighted average and carries no twin at
    either ref;
  - `anchor.gap_split` on 7 (not VITL);
  - `anchor.midcycle_gap.read` on 4 (GOOGL, IT, LLY, VITL);
  - one appended `layer_refreshes` entry on each page, at W61's extraction vintage.

  0 other leaves move. `applicable`, `reason`, `recipe_hint`, `valuation_basis`, `ev_gap` and
  `qa_flags` move on none of the 8.
- **The re-derivation on `8ea51e99` equals the W50-only one on `48583be9`** in every leaf but
  `gap_split`, `computed_at` and the refresh entry's vintage. That W50-only refresh was taken
  before #1118 merged, and its gate was stopped unfinished.
- **The split rebuilds each page's published value.** On the 7 it reaches:
  - `anchor_at_current` equals `anchor_base_value_per_share` exactly;
  - V0 + the margin effect = the value at today's multiple, and + the multiple effect = the value
    at the median, both to within $0.0001;
  - `committed_gap_split`, the rebuild from the committed fields alone, raises on none of them and
    lands within $0.0005.

  This checks this pass's pages only. W61's corpus table, re-run on the refreshed pages, is still
  W61's owed item.
- **Each md moves only** in these places:
  - the screening block, now with the split's line and its arithmetic (7 pages);
  - the lease line, on EPAM, SMPL, TJX and WERN;
  - the header's "layers refreshed to" stamp;
  - the rendered refresh entry under "Record & reproduce".
- **Each md re-renders byte-identically from its JSON under main `8ea51e99`'s code.** So #1116's
  FLAG block moves none of them: `input_checks` is absent on all 8.
- **The full offline suite passed** (`bin/commit`) on the committed artifacts before the push.

**BOUNDARY.**
- **Roster:** `data/coverage_roster.jsonl` at `aa9fde84`, with 11 active and 15 watch pages.
- **Inputs:** the CIQ exports in the primary checkout as of 2026-11-18. The EDGAR companyfacts
  are cut at each page's price date.
- **Count:** 8 pages move here, 1 is refreshed by its own rebuild (VRRM, #1121), 1 is unchanged
  (NCNO), 1 is excluded (BRBR), and 15 are left as committed (26 committed pages in all). The
  split is on 7 pages here: 6 split and 1 refused (GOOGL).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The fleet reads two statistics until the watch pages are rebuilt.** 12 committed pages still
  price the median: BRBR, plus the 11 watch pages that carry a multiple (AMZN, BURL, CNXC, MCK,
  NFLX, NKE, PARR, ROST, TGT, V, WLK). VRRM makes a 13th until #1121 merges.
- **No page misreads as the other.** Each states which statistic it prices, through its own
  `multiple.statistic` and its rendered words, and `tests/test_w50_anchor_current.py` holds each
  kind to its own rule (#1117).
- **The same 12 carry no split** until re-derived. A split is written only by `compute_anchor`, and
  on the 7 refreshed pages that carry one it is struck at the current, the statistic each now prices.
