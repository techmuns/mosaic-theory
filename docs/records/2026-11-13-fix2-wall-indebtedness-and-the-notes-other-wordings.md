---
id: 2026-11-13-fix2-wall-indebtedness-and-the-notes-other-wordings
status: shipped
date: 2026-11-13
prs: [1051]
supersedes:
superseded-by:
---

# The balance-sheet debt total refuses an "indebtedness" row (Perrigo's "Current indebtedness 36.6") and a current portion the debt note subtracts under its other wordings, when what it subtracts is debt (the #1039 follow-up) — of 2,049 cached primary documents, 0 walls move and 1 balance-sheet read does (Perrigo's 10-K)

**WHAT.** `vinci/edgar/filing_sections._balance_sheet_debt`, the read #1039 added so one instrument
can cover the maturity wall when its principal is the sheet's whole debt:
- **"indebtedness" is a borrowing word** (`_BS_DEBT_WORD`), as the module's own `_TOTAL_DEBT` and
  `_AGGREGATE` already read it. A sheet with an "… indebtedness" row outside its long-term-debt row
  reads no total.
- **"Accrued interest on notes" is no borrowing row:** it is interest, not principal (the brief's
  stay-out pin). On main the word "notes" made it one, and the total was refused. #1039's record
  accepted that over-refusal; this PR removes it. A "Notes payable" row is still a borrowing.
- **The folded-portion guard reads the debt note's other wordings** (`_NOTE_CURRENT`,
  `_note_subtracts_current`):
  - a cell with no parentheses ("Less current portion of long-term debt 10,000");
  - a bare "Less: Current maturities ( 10,000 )";
  - a lettered footnote ("(a)");
  - a portion "included in accrued expenses ( 10,000 )";
  - "LESS:", a lower-case "less:" and a spaced "Less :" (code review round 0; main read the
    lower-case and capitalized forms, and round 0 restored them).
- **What it subtracts must be debt:**
  - a label that names what it is a portion OF must name debt, never a lease;
  - a bare label takes its subject from its own table: the text back to the sentence's start
    must name debt, and the label no lease, interest or tax;
  - a row's own ", less current maturities 19,779" (Werner's finance-lease row) is never a
    subtraction;
  - a label never runs through another "less" or "current portion";
  - a year is never the cell.
- **Vintage** `2026-11-13.wall-reads-indebtedness-and-the-notes-other-wordings`, following
  `2026-11-12.wall-of-our-borrowings-is-part-of-the-debt`; `filing_sections.py` re-pinned.

**WHY.** The coordinator's independent re-review of #1039 (2026-11-13) found the read's "never a
partial sum" contract leaking on a REAL sheet:
- **Perrigo's 10-K** (`0001585364-26-000009`, unaltered) read 3,603.6 with a current portion of
  0.0. Its sheet lists "Current indebtedness 36.6" beside "Long-term debt, less current portion
  3,603.6", and Note 13 totals them: "Total borrowings outstanding 3,640.2 … Current indebtedness
  ( 36.6 )". With one constructed sentence stating an instrument at $3,603.6M and no principal
  due, main read a located $0.0 beside $36.6M due within the year.
- **Four debt-note wordings escaped the guard,** each reading a located $0.0 beside a folded
  10,000 (constructed). Only the exact "Less: current portion of long-term debt ( 10,000 )"
  refused.
- **Found while building, on the corpus:** the first widening refused A10 Networks' 10-K
  (`aten-20251231`), whose bare "Less: current portion ( 80,824 )" is of DEFERRED REVENUE ("Total
  deferred revenue 142,806"). The subject rule above is the fix.

**HOW VERIFIED.**
- **Fail first, on main `f676616f`** (`tests/test_wall_whole_debt_followup.py`, 28 tests): 4
  fail on the defect each names, and 24 pass at both. The 4:
  - `test_prgo_current_indebtedness_is_a_borrowing_row` (Perrigo's real sheet and Note 13; located
    $0.0);
  - `test_bs_neg_a_current_indebtedness_row_refuses_the_total` (it read 803.0);
  - `test_bs_neg_every_note_wording_of_a_folded_portion_refuses_the_total` (each wording, and
    round 0's lower-case, all-caps, spaced-colon and caption cases);
  - `test_an_accrued_interest_on_notes_row_is_no_borrowing` (main refused the total).

  The 2 new positive pins pass at both, because they guard against over-refusal:
  - `test_aten_a_bare_current_portion_of_deferred_revenue_is_no_folded_debt` (A10's real text) failed
    first on this PR's own first widening, where it read no total;
  - `test_a_lease_or_an_interest_line_is_no_folded_debt_portion` (the lease, interest and tax lines
    stay out).
- **Mutants: 10 of 10 killed.** Each guard was removed in turn: the indebtedness word, the
  interest-on-notes lookbehind, the bare cell, the lettered footnote, the "included" form, the lower-case row skip, the table subject
  rule, the of-object rule, the no-swallow rule and the case-insensitive "less".
- **Real texts, main against this code:** 33 normalized 10-Q/10-K texts, among them Werner's
  Q2/Q3, Microvast's, Amazon's, Alphabet's, Uber's, Perrigo's, PARR's and A10's.
  - **Werner's Q2 and Q3 still read located $0.0** (793.0 and 803.0, current 0.0).
  - **Only Perrigo's balance-sheet read moves** (3,603.6 → none).
  - No wall moves.
- **The sweep** (the same population as #1039 round 1): 2,049 primary documents, main `f676616f`
  against this code.
  - **0 walls move and 0 notes move.**
  - **Walls:** 7 located, 325 `not_stated`, 1,717 with no wall pattern, at both refs.
  - **The balance-sheet read changes on 1 document,** Perrigo's 10-K: 3,603.6 → none (35 → 34 reads).
  - **No errors:** 0 read, normalize or wall errors.
- **The impact check** (`vinci.impact run`, base `f676616f`, the merge base with main; head
  `d68ab1b8`, a local commit holding exactly this PR's code and tests by patch-id; $0; the store
  priced to the 2026-11-09 close, all 27 pages and IWM, MDY, SPY, filled from the cache):
  - **Fail first:** 4 of 28 tests fail on base and pass on head, and 0 fail at head.
  - **Pages:** built 26 of 27, and 0 of 26 move. PARR builds at neither side (a mislabelled CIQ
    export), so "0 move" says nothing of it.
  - **Requests:** 0 of 26 differ, and the frozen panel 0 of 6, so the row-53 panel check is not
    owed.
  - **Rendering:** 0 of 27 committed pages re-render differently. The one frontend file that
    differs is `snapshots/extraction_versions.json`, the new vintage.

**BOUNDARY.**
- **Fail first and mutants:** `tests/test_wall_whole_debt_followup.py` (28 tests), against main
  `f676616f`'s `filing_sections.py`; the mutants are also scored on `tests/test_wall_part_of_the_debt.py`
  and `tests/test_filing_wall_and_concentration_roles.py`.
- **Real texts:** the 33 normalized texts in the coordinator's review folder plus Perrigo's, read
  2026-11-13.
- **Sweep:** 2,049 primary documents (URLs named `<x>-YYYYMMDD.htm`):
  - 2,035 from the primary checkout's `data/cache/sec`, all 18,731 of its files local (0 offloaded),
    read 2026-11-13 IST;
  - 14 from the session scratch caches under `/private/tmp` (60 folders).

  Unit: one document's wall and its balance-sheet read. A10 Networks' 10-K is not in this
  population; it is pinned on its real text.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The guard is still a vocabulary read.** It sees a folded current portion only in the wordings
  above. A note that subtracts it otherwise, or folds it with no line at all, is invisible.
  *Falsifier:* a filing whose long-term-debt row equals one instrument's principal and whose stated
  ≤12m figure equals the sheet's listed current portion, while other debt sits in a row with no
  word of `_BS_DEBT_WORD` and no `_NOTE_CURRENT` line subtracts it.
- **A bare label's subject is the text back to the sentence's start,** so it is only as good as
  the text's sentence ends. A "NOTE 9" heading or a debt table just before a lease table can name
  "debt" for a non-debt portion. That refuses the total (the loud side), never fabricates
  (code review round 0, finding 5).
- **An "of" label is read by the borrowing words,** so "current portion of notes receivable" counts
  as debt. Again it refuses, never fabricates (finding 6).
- **Reported, not decided (definitional):** PARR's sheet lists "Obligations under inventory
  financing agreements 259,245" outside its long-term debt (`parr-20260930`, total read 496.2).
  Whether inventory financing is debt is a definitional question. The read does not count it,
  and PARR's wall reads `not_stated` either way.
- **Found, not fixed (constructed, outside this brief):** a sheet with no liabilities heading at
  all, whose first "liabilities" is a row ("Accrued liabilities"), skips every row above it. A
  "Short-term debt" row there reads Werner's total and a located $0.0 (the reviewer's probe B1).
  No cached layout has shown it.
