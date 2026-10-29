---
id: 2026-10-29-an-unavailable-lease-cell-leaves-its-quarter-unpriced
status: shipped
date: 2026-10-29
prs: [857]
---

# An unchecked quarter of the ex-lease history whose lease cell CIQ states as UNAVAILABLE is left unpriced, not priced with the missing cell read as zero (audit D-D1)

**WHAT.**
- **The rule.** `vinci/dossier/lease_basis.py` `observations`: a quarter is now priced only where
  CIQ states both lease cells ('Curr. Port. of Leases' and 'Long-Term Leases') or EDGAR vouches
  for the sum.
  - "States" means `clean_num` reads a number: not '-', NM, NA, blank, or a missing row.
  - "EDGAR vouches" means the quarter is reconciled.
  - A pre-adoption quarter takes nothing out of TEV, so it is unaffected.
- **What is left unpriced.** An UNCHECKED quarter (EDGAR has no complete operating-lease figure
  that day) with a cell UNAVAILABLE keeps its row, its status and the cells CIQ does state
  (`leases_in_tev`), with `multiple` None.
- **What was wrong.** The old code read the missing cell as 0.0
  (`(cur_l.get(d) or 0.0) + (lt_l.get(d) or 0.0)`). That broke the reader's own rule that an
  UNAVAILABLE cell is never coerced to 0 (`ciq._UNAVAILABLE_CELLS`).
- **The latest quarter.** When the latest quarter is unpriced this way, `history` names the cause
  ("is left unpriced: …"). Before, it was misreported as "no positive LTM EBITDA".
- **The reason is stored (review round 1).**
  - The unpriced quarter carries `unpriced_reason`, naming the cell: "'Curr. Port. of Leases' is
    '-' (UNAVAILABLE)…", or "the export has no '…' row".
  - The block lists the dates in `unpriced_dates`, beside `unchecked_dates`.
  - Both fields are ABSENT when unset, so a block with nothing unpriced serializes byte for byte
    as before.
  - A band refused as too short names the unpriced quarters and why. Before, it said only "only n
    ex-lease quarter(s)".
- **Version.** Extraction version `2026-10-29.D-D1`, in both the Python and the JS tables.

**WHY.**
- **WLK's 2025-09-30** has a 'Long-Term Leases' cell of $709M and a current-portion cell of '-'.
  The quarters either side state $136M and $138M. EDGAR tags only the noncurrent $709M that day,
  so nothing checks the row.
- **What main did with it.** Main priced that quarter on the long-term row alone: $709M of leases
  out of TEV, 11.391x.
- **How many.** Seven WLK quarters have this shape, and they are the only ones in the corpus.

**HOW VERIFIED.**
- **Real run over the corpus** (`lease_basis` on main and on this branch).
  - **Inputs:** each committed page's own quarterly CIQ export and the frozen
    `tests/fixtures/companyfacts`.
  - **Main reproduces the committed pages.** Main's code reproduces every committed observation's
    multiple and status on 17 of the 18 pages.
  - **UBER is the exception:** 21 of 30. Its committed block predates the like-with-like statuses,
    and the fix moves none of its 30.
  - **What moves:** exactly 7 observations, all WLK's: 2021-09-30, 2022-03-31, 2022-06-30,
    2022-09-30, 2023-09-30, 2024-03-31 and 2025-09-30. Each goes from 5.22 / 5.17 / 3.30 / 3.33 /
    6.77 / 11.41 / 11.39x to unpriced, and each keeps its stated `leases_in_tev`.
  - **The CIQ cells.** At the same dates the export (sha256 `15bec6cee3…`, the page's own) states
    '-' for the current portion beside 392 / 514 / 494 / 474 / 542 / 622 / 709.
- **The other ex-lease names.** SMPL (on its page's own export, archived
  `replaced-2026-10-28`, sha `e41ebc16a4`), EPAM, WERN, UBER and VITL move 0. Their '-' cells are
  all pre-adoption or already unreconciled.
- **WLK's band.** Main has median 7.9102 over 34 quarters (current 13.0252, 94.1st percentile,
  low 3.3004). This branch has median 8.2398 over 27 (current 13.0252, 92.6th percentile, low
  4.4887). As of 2026-08-05 in both.
- **WLK's R1.** `compute_anchor` on the committed mechanical layer and the frozen companyfacts, at
  the page's `computed_at` (2026-10-26T14:56:37Z):
  - Main: multiple 7.910206 (34 quarters), base value $115.6523 a share.
  - This branch: 8.239810 (27 quarters), $121.5196.
  - That is +4.17% on the multiple and +5.07% a share.
- **Why the committed $116.1475 differs.** Main's code on the same inputs already gives $115.6523,
  not this change. Main's D&A is now a trailing twelve months ($1,170M), where the page's anchor
  used FY2025 ($1,178M).
- **Tests.**
  - `tests/test_lease_basis.py::test_d1_neg_…` and `::test_d1_an_unpriced_latest_quarter_…` fail
    on main's `lease_basis.py` and pass here. They use WLK's real cells and frozen companyfacts.
  - `::test_d1_pos_…` is the fence and passes on both. It covers reconciled quarters,
    pre-adoption '-' quarters, and an unchecked quarter with both cells stated.
- **Round 1 (review of #857).**
  - Two pins fail on the round-0 head and pass here: the reason and tally on WLK's real cells, and
    an export with no current-lease row naming why its band is short. The second is latent: every
    committed export carries both rows.
  - The six captured fixtures round-trip byte-identically.
  - The lease_basis block rebuilt on main and on this branch is byte-identical on 17 of the 18
    pages. WLK's differs in its band, its observations and its `unpriced_dates`, which lists all
    7 dates.
- **Mutations.** Five, all killed:
  - the guard deleted;
  - every unchecked quarter dropped;
  - every quarter with an UNAVAILABLE cell dropped;
  - either cell counted as enough;
  - the history message reverted.
- **Suite.** The full offline suite is green: 7,932 passed, 534 skipped, 15 xfailed.

**BOUNDARY.**
- **Corpus:** 18 of the 19 committed pages carrying a `valuation.lease_basis` block with
  observations at `c51c286a`, one held out under a standing operator constraint. These pages hold 567
  observations, of which 87 have an UNAVAILABLE lease cell (79 pre-adoption, 1 unreconciled, 7
  unchecked; the verification run's count).
- **Inputs:** CIQ copies at `mosaic-theory-ta/data/manual/ciq` (and its archive, for SMPL). EDGAR
  is the frozen companyfacts fixtures, not live EDGAR.
- **Units:** multiples are TEV ex-lease ÷ LTM EBITDA; $ figures are $M from CIQ; per-share values
  are R1's base on the anchor's own share count.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **THE +4.2% IS A SELECTION EFFECT, NOT A CORRECTION OF VALUE.** Fill the seven quarters' missing
  current portion with the nearest STATED cell either side (89–138), as an illustration only. The
  median is then 7.9102 over 34 quarters, whichever side is used. That is identical to main's.
  - So their values were only slightly wrong: each multiple was too high by 0.02–0.13x.
  - What moves the median is leaving them out: five of the seven sit below it.
  - The repo does not impute a missing cell, so leaving them unpriced is the rule. But the R1 move
    it produces is the price of not guessing, not a better estimate of the band.
- **Pages wait for the rebuild.** WLK's committed page keeps the old band, anchor and observations
  until the combined Phase-1 rebuild re-assembles it. No page is written here.
- **Not changed:**
  - `fin_at`'s `or 0.0` for a filer with no finance-lease figure within reach (latent; no
    committed page reaches it);
  - a reconciled quarter with one cell UNAVAILABLE still prices, because EDGAR vouches for its
    sum (none in the corpus).
