---
id:
status: shipped
date: 2026-11-12
prs: [1022, 1023, 1024, 1025, 1026, 1029, 1031, 1032]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 6 (S4): RG-D1 to RG-D7 to `fixed` (#1023), STATE row 45 closed with RG-D5, #1029's corrected scopes carried into row 60 and two Pages cells, row 38's blocker cleared, the hand-offs amended, and row 60 recounted (of 148 asked: 132 fixed, 8 open, 7 in progress, 1 disagreed)

**WHAT.**
- **The fix log**, `docs/fix-log-teamnostra-2.md`:
  - **RG-D1 to RG-D7 → `fixed`** (#1023, `85152609`), as #1023's bookkeeping section asks. Each row names its behaviour, its residual where #1023's record states one, and one or more test nodes:
    - RG-D1, the sign: a sign in words is not read;
    - RG-D2, the unit;
    - RG-D3, the period and the row: a period the table lacks restricts nothing;
    - RG-D4, the width: a display cell's own whole-number precision is ignored (latent);
    - RG-D5, a duration: one equal to any window the page names passes;
    - RG-D6, the fields that cite nothing: weaker than its record's item 6 states (random key unknowns trace 64–100% on frozen SMPL; 3 of 412 free-field figures flagged on the corpus);
    - RG-D7, call figures.
  - Each row's pages cell says that flags move on 24 of the 27 committed pages at their next build (447 → 476). A committed page's stored flags change only when it is rebuilt.
  - **A-D2's and RA-D16's Pages cells** carry #1029's corrected scopes: A-D2's note reaches 27 pages, not 13; RA-D16's flags reach 18, not 5.
    - The pages each cell named first are kept, because #960's and #965's merged records name them.
    - No merged record names the others, so none are invented. A's sweep record (draft #1028) is not merged.
- **STATE.md §5.0**:
  - **Row 45 is deleted.** It closes with RG-D5, as #1023's section asks, and has no entry in the frozen §5 archive to strike: it was opened on 2026-11-04, after §5 froze. Its ask was to read a duration's number as a figure where a fact could state it, and RG-D5 delivers that, with the window residual named in RG-D5's row.
  - **Row 38's blocker**, "A's void-keying PR (#1015) and the 2026-11-11 monitor day", is struck: #1015 is merged, and #1022 filed the day. This is #1022's bookkeeping ask.
  - **Row 60:**
    - the title recount;
    - batch 6 in the list of batches;
    - one batch-6 clause;
    - #1025's line on the impact check (kept builds keyed by UTC day; vendor pulls refused by default);
    - the #956, #960 and #976 clauses corrected as #1029's amendments state them;
    - operator item (4): the 2026-11-11 monitor day is filed (#1022), where it read "none yet";
    - one sentence on the hand-offs.
- **STATE.md §2's line on rank and duration** ("a WHOLE-NUMBER duration … is a label") gains a superseded note pointing at RG-D5.
- **Amendments:**
  - **Batch 3's record**, on the split's hand-offs:
    - fix 5 and RG-D1 to RG-D7 shipped (#1023), fix 5's qualitative half not built;
    - the `customers()` hang shipped (#1026);
    - #1014's deferred `as_filed_by` item is fixed (#1031).
  - **RG-D20's record (#1009):** its items (c) and (d) are superseded by #1023, whose record says so (item 8).
- **No ID and no row**, each by its own section:
  - **#1024** (`9708fbc0`) and **#1032** (`4dca5cce`): row 42, our own item, now closed. #1032 deleted it, and row 60's batch-5 clause already says so.
  - **#1029** (`8b4b35f6`): record amendments only.
  - **#1031** (`7f58a2be`): `as_filed_by`, operator ruling 2.
  - **#1026** (`4b2f0cb9`): issue #1004's `customers()` hang. Its section asks for a row with an ID "to be assigned by B", but the log admits only TeamNostra's IDs and none was asked for this, so no ID is invented. It is recorded as a hand-off (above).
  - **#1022** (`493995f0`) and **#1025** (`964cd104`): A's monitor day and impact-check PRs.
- **Left as it reads:** RG-D19's cell. S2's 12-word guard PR is in flight and finds that only LLY (14) and VITL (13) break the rule by its own count, with WERN at 11. RG-D19 flips, with those numbers, in the batch after that PR merges, citing its record (B, #1004).

**WHY.**
- Under batched bookkeeping (operator 2026-11-10), a fix PR edits neither the log nor row 60, and S4 applies each batch.
- CLAUDE.md: closing an item means deleting its §5.0 row and striking its §5 entry, and a supersede must touch the snapshot.

**HOW VERIFIED.** On main `4b2f0cb9`:
- **RG-D1 to RG-D7 fail first.** Main's `tests/test_figure_trace_as_written.py` and `tests/test_untraceable_rank_and_duration.py` were run on #1023's parent `4dca5cce`. Every node the rows name fails there on an assertion about the old behaviour, never on a missing name:
  - the audit's 11 constructed replies, each "not flagged";
  - the sign, percent, period and metric binds;
  - the duration, key-unknown and call-figure pins.

  Four other tests in the files fail at the parent only because a helper is missing (`_claim_figures_as_written`, `_within`, `_row_metric`), so the rows do not name them. On main, both files pass.
- **The monitor day.** `frontend/monitor/2026-11-11.json` is on main, with GOOGL absent from its seven-name freshness set and the void named in its notes.
- **A's WERN/MVST PR.** No draft is open yet; of A's handed-over drafts, only #1028 (the sweep) and #1030 (order 8) are.
- **The lints.** These pass on this branch:
  - `tests/test_fix_log.py`;
  - `tests/test_record_status_matches_open_now.py`;
  - `tests/test_state_open_now.py`;
  - `tests/test_state_identifiers.py`;
  - `tests/test_records_ledger.py`;
  - `tests/test_rg_d20_instructions_match_the_code.py`.
- **The full gate.** Its run is in the PR.

**BOUNDARY.**
- **The PRs.** The ones B named for batch 6 (issue #1004, 2026-11-12), read at main `4b2f0cb9`: #1024, #1029, #1031, #1032, #1023, #1026, #1022 and #1025.
- **The counts.** All 178 fix-log rows by their Status cell, and separately the 148 asked (every Order but `§4`).

**THE COUNT.**
- Of the 178 rows: 132 fixed, 38 open, 7 in progress, 1 disagreed.
- Of the 148 asked: 132 fixed, 8 open, 7 in progress, 1 disagreed.
- Against batch 5, RG-D1 to RG-D7 moved from open to fixed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **RG-D1 to RG-D7 are `fixed` with residuals.** Each is named in its row and in #1023's record, as #1023's section asks. The falsifier #1023's record states has fired twice (PARR's "$21.54", VITL's year 2030), and both are found-not-fixed items for S2's PR after the 12-word guard.
- **The Pages cells name only what a merged record names.** Until A's sweep record merges, A-D2's other 14 pages and the rest of RA-D16's 18 (A states no unit) are counts without names.
