---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, RA-D2 split from #967: the dividend per share is the dividend, and CIQ's 'NA' is not stated (the operator's ruling of 2026-11-11). Measured on its own panel before it ships

**WHAT.**
- **The split.** #967 held RA-D2 and RA-D4 together, and its panel check did not ship (#973). The
  operator, relayed by the coordinator on 2026-11-11, verbatim: **"go ahead with the correct steps
  as per experts"**. The steps: split #967 into RA-D2 (this) and RA-D4, measure each on its own,
  merge what passes, stop what fails. This PR carries RA-D2's half of #967's code, unchanged except
  for the 'NA' ruling below, plus the evals harness's `--ciq` plumbing and its own transform.
- **RA-D2** (`ciq_sheets._dividend_per_share`, read by `return_ratios` and `key_ratios`). CIQ's
  Ratios sheet has no dividend level: its 'Dividend per Share' rows are growth rates, and the first
  was printed as "Dividend/sh". V read 0.19, 0.15, 0.13, 0.14 against dividends of 1.87, 2.15,
  2.44, 2.79; GOOGL read 0.38 and 0.05 against 0.83 and 0.86. Both now read the Income
  Statement's 'Dividends per Share' level for the same period, matched by period kind and end, and
  cite it. MCK's LTM figure over a quarter CIQ marks carries a note (the operator's ruling of
  2026-11-10).
- **The 'NA' ruling** (the operator, 2026-11-11, on #967's deferred Codex P1): CIQ's 'NA' in
  'Dividends per Share' means NOT STATED. It reads "—" (UNKNOWN), never zero and never "none"; the
  table's own note, printed under it, says which cells CIQ marks, and the key ratios read "dividend: not stated (the
  Income Statement reads 'NA')". A page says no dividend only where CIQ states 0 or a dash
  (`_NO_DIVIDEND_CELLS`). A filing's statement is not read here.
  - **On the exports on disk** (36 folders, 2026-11-11): CIQ writes neither 0 nor a dash in that row.
    Every non-payer's cell reads 'NA' (218 annual and 781 quarterly cells across the folders), and
    payers carry 'NA' in quarters they paid (BDX, CPB, MCK, ROST, TJX). So no page on disk says no
    dividend from CIQ: the 22 non-payers' "dividend: none" becomes "not stated".

- **Review round 0** (`/code-review high --fix`, 9 findings: 5 fixed, 4 left):
  - **The notes are the table's own.** The 'NA' and LTM notes sat on the field, which no renderer
    prints, so a non-payer's row of "—" would have read as unexplained. They are now
    `FinTable.note`, printed under the table
    (`::test_ra_d2_the_rendered_ratio_table_says_why_its_dividend_row_reads_no_figure`). Once
    re-assembled, a non-payer's page shows the row of "—" and its note where the all-"none" row
    was hidden before.
  - A dash quarter counts as stated in the LTM note; an unplaced column says why it reads no
    figure; the transform compares an UNKNOWN field's note as it stands.
  - Left: the transform proves the folder is the page's by field equality, not by file hashes; the
    harness hands every transform the folder; an unplaceable LTM keeps no reason; a short row's
    cell reads "blank" (see the PR's dispositions table).

**WHY.** Document 15, order 4: "a dividend growth rate printed as dividend per share". The 'NA'
ruling is the fail-loud rule: a cell that states nothing is not a zero.

**HOW VERIFIED.**
- **Fail first.** `tests/test_dividend_level_and_na.py` has 10 cases (8 tests). All 10 fail on
  `origin/main`'s `vinci/` (`ed2c5f8f`; the branch is built on `c2a4d743`, which adds #975, touching neither reader). On #967's head (`4b38b7a2`), the 6 that the 'NA' ruling
  changes fail and the 4 it does not change pass.
- **On real exports:** AMZN, 'NA' in all 10 columns, now reads "—" in each with the note, and
  "dividend: not stated (the Income Statement reads 'NA')"; GOOGL "—" for its 7 pre-dividend years;
  MCK and V print their figures as before.
- **$0 compare.** COMPARE_LINE
- **The panel.** PANEL_LINE

**BOUNDARY.** The exports under the primary checkout's `data/manual/ciq/` on 2026-11-11: 36
folders. The panel is the frozen six (BURL, CNXC, LLY, MCK, ROST, SMPL).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- It changes what live pages print and what their synthesis requests carry once re-assembled, so it
  ships only if its own panel check passes (RUNBOOKS §n). No page is refreshed here.
- The 'NA' ruling moves the key ratios of every non-payer from "dividend: none" to "not stated".
- **Extraction version** `2026-11-11.dividend-level-na-unstated`; the drift pins are re-pinned.
## Amendments

- **2026-11-11.** The "$0 compare" and "The panel" lines under HOW VERIFIED merged as unfilled
  template placeholders, and `prs:` stayed empty. What they were to say:
  - **$0 compare:** `--base 2b9b766c --cand 9ae02bac --transform dividend_level`. All six panel
    pages differ, in `user.facts` only: BURL +305, CNXC +209, LLY +63, MCK +292, ROST +62 and SMPL
    +309 characters.
  - **The panel:** registration `b29121ebdc675bd3`, no-worsening only, drawn once and scored at $0.
    No class metric worsens. Five lean moves, LLY's proposal none → BUY.
    `docs/records/2026-11-11-ra-d2-measured-on-the-panel.md` records it. The operator ruled the
    moves noise ("Merge, moves are noise"), and the change merged as `62d682c6`.
  - The PR that carried this record is #981.
- **2026-11-11.** #981's PR checked its pages with a $0 build of every committed page, which built 17
  of 27: the primary checkout's store had no price bars for BURL, GOOGL, LLY, MCK, NFLX, ROST, TGT, TJX, UBER and V. Those 10 have now been built on
  the full store, at the same pair as that check, base `2b9b766c` → head `9ae02bac`.
  - **Built 10 of 10 on both sides. 10 of 10 move,** in `return_ratios` and `key_ratios` only, and
    each move is a kind the PR stated:
    - the Dividend/sh row's growth rates become the Income Statement's levels;
    - on a non-payer, "none" becomes "—" with the 'NA' note, and the key ratios' "dividend: none"
      becomes "not stated";
    - MCK's LTM note.

    | Page | Dividend/sh cells (base → head) | Table note | Key ratios' dividend |
    |---|---|---|---|
    | BURL | 11 none→— | 'NA' in 11 of 11 column(s) | dividend: none → dividend: not stated (the Income Statement reads 'NA') |
    | GOOGL | 7 none→—; none→0.60, 0.38→0.83, 0.05→0.86 | 'NA' in 7 of 10 column(s) | unchanged |
    | LLY | 0.02→2.08, 0.08→2.25, 0.15→2.58, 0.15→2.96, 0.15→3.40, 0.15→3.92, 0.15→4.52, 0.15→5.20, 0.15→6.00, 0.15→6.69 | — | unchanged |
    | MCK | 0.04→1.12, 0.16→1.30, 0.16→1.51, 0.07→1.62, 0.03→1.67, 0.10→1.83, 0.14→2.09, 0.15→2.40, 0.15→2.75, 0.15→3.17, -0.44→1.64 | Dividend/sh LTM to 2026-09-30 (1.64) is CIQ's own LTM figure, printed as stated; of the four quarters ending then, the quarterly export's 'Dividends per Share' reads 'NA' for the quarter to 2026-09-30, and the 3 it states sum 2.46 | unchanged |
    | NFLX | 10 none→— | 'NA' in 10 of 10 column(s) | dividend: none → dividend: not stated (the Income Statement reads 'NA') |
    | ROST | 0.16→0.57, 0.25→0.71, 0.32→0.93, 0.13→1.05, -0.73→0.29, 3.00→1.14, 0.09→1.24, 0.08→1.34, 0.10→1.47, 0.10→1.62, 0.10→1.70 | — | unchanged |
    | TGT | 0.07→2.32, 0.05→2.44, 0.03→2.52, 0.03→2.60, 0.03→2.68, 0.18→3.16, 0.25→3.96, 0.10→4.36, 0.02→4.44, 0.02→4.52, 0.02→4.56 | — | unchanged |
    | TJX | 0.24→0.52, 0.20→0.63, 0.25→0.78, 0.18→0.92, -0.72→0.26, 3.00→1.04, 0.13→1.18, 0.13→1.33, 0.13→1.50, 0.13→1.70, 0.13→1.81 | — | unchanged |
    | UBER | 11 none→— | 'NA' in 11 of 11 column(s) | dividend: none → dividend: not stated (the Income Statement reads 'NA') |
    | V | 0.18→0.69, 0.28→0.88, 0.19→1.05, 0.16→1.22, 0.09→1.34, 0.18→1.58, 0.19→1.87, 0.15→2.15, 0.13→2.44, 0.14→2.79 | — | unchanged |

  - The price store is a read-only master copy of the full store, sha256 `4e77757f5cb370050ab9b43c450053379e8d20c0f605d4d4213b9e152e6a8e9d`, with bars through 2026-11-09. Every single-page build started from its own fresh APFS clone of it, because a build writes to its store. The other inputs are the primary checkout's.
  - Every row is shown (no rows left out). "unchanged" in the last column: that page's key ratios
    carry no dividend change.
