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

- **2026-11-11.** Two lines under HOW VERIFIED merged as template placeholders and were never filled
  ("COMPARE_LINE", "PANEL_LINE"), and `prs:` stayed empty. What they were to say:
  - **$0 compare:** `--base 2b9b766c --cand 9ae02bac --transform dividend_level`. All six panel
    pages differ, in `user.facts` only: BURL +305, CNXC +209, LLY +63, MCK +292, ROST +62 and SMPL
    +309 characters.
  - **The panel:** registration `b29121ebdc675bd3`, no-worsening only, drawn once and scored at $0.
    No class metric worsens. Five lean moves, LLY's proposal none → BUY.
    `docs/records/2026-11-11-ra-d2-measured-on-the-panel.md` records it. The operator ruled the
    moves noise ("Merge, moves are noise"), and the change merged as `62d682c6`.
  - The PR that carried this record is #981.
