---
id:
status: shipped
date: 2026-11-11
prs: [971, 984, 985, 994, 1001, 1008, 1009]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 4 (S4, the fix log's only writer since #1011): RA-D7 and RA-D12 to `fixed`, RF-D7's web twin added to its row, RG-D20 pinned by one test per item and kept `in progress`, and the row-60 clauses batch 3 did not carry

**WHAT.**
- **The fix log**, `docs/fix-log-teamnostra-2.md`:
  - **RA-D7 and RA-D12 → `fixed`** (#971, `df24ff35`). Each names its own test, and both are latent, so no page moves. RA-D7's cell names the residual #971's record found and did not fix: other readers of 'Trends' still return nothing when the sheet is missing.
  - **RF-D7** keeps `fixed`. Its row gains the web twin, its last open piece (#1001, `8a72be4c`), with that PR's test node. Its pages cell gains the two scenario mirrors #1001 rebuilt, and GOOGL's cards rebuilt voided by #1008.
  - **RG-D20** (#1009, `d8147e97`) → `in progress (#1009)`. #1009 changed only comments, docstrings and docs, so no test failed before it. This batch adds `tests/test_rg_d20_instructions_match_the_code.py`, one case per item a–m of #1009's record:
    - each case reads the value or behaviour the instruction states, and compares it with the code's constant or behaviour;
    - (a) checks the `messages.create` call sites by AST; (c) checks `_DIRECTIONAL` against words and signed figures; (d) checks `flags._QA_MARKERS` and `is_qa`; (h) builds a `Registration` targeting M-GAP; (k) checks the two normalizers on a curly quote; (l) checks `require_env`'s line; (m) counts `vinci/` source files at the commit the doc names.
    - **Fail-first:** on #1009's parent `d6001465`, 11 of the 13 fail. (b) and (j) pass there, because #998 corrected them first as G-D15 and G-D14. On main all 13 pass.
    - **Not `fixed`** (coordinator, #1004: "Never `fixed` without a test"). Two items have no code counterpart: (e), CLAUDE.md's loop list against RUNBOOKS's live sections, and (i), the CIQ notes' rule 4 against the row numbers the notes quote. Each resolved two instructions that contradicted each other, so each is pinned doc against doc. Whether that counts as fixed is the operator's call, which the coordinator is taking to the operator.
- **STATE.md §5.0 row 60**:
  - the title recount;
  - batch 4 in the rule's list of batches;
  - one batch-4 clause;
  - in operator item (4), the GOOGL void that #984's bookkeeping section asked for, recorded as done because its three parts (#984, #1001, #1008) are all merged;
  - RA-D2's and RA-D4's panel measurements (#985, #994).

  These are the row-60 clauses S4 found missing when it verified batch 3 (comment on #1004). Batch 3 merged without them.
- **#1010** names no ID (completions only), so it books nothing.

**WHY.** The operator split the remaining work on 2026-11-11 (#1004). S4 is the fix log's only writer since #1011 merged (A, on #1004: "From now, B is the fix log's only writer").

**HOW VERIFIED.** Every row was checked on main `9da013da`:
- each SHA is on `main` and is its PR's squash commit;
- each PR names its ID in its title, body or squash message;
- each named test node exists, is new in its row's PR (absent at the squash commit's parent), and passes on `main`;
- `tests/test_fix_log.py`, `tests/test_state_open_now.py`, `tests/test_state_identifiers.py` and `tests/test_records_ledger.py` pass.

**BOUNDARY.** The batch covers PRs merged after #1003 and not booked by batch 3, read on 2026-11-11 at main `9da013da`: #971, #1001, #1008, #1009 and #1010, plus #984, #985 and #994, which merged before #1003 but whose row-60 clauses batch 3 did not carry. The counts are every one of the 178 fix-log rows by its Status cell, and, separately, the 148 asked (every Order but `§4`).

**THE COUNT.** Of the 178 rows, 121 are fixed, 47 open, 9 in progress and 1 disagreed. Of the 148 asked, 121 are fixed, 17 open, 9 in progress and 1 disagreed. Against batch 3, RA-D7 and RA-D12 moved from open to fixed, and RG-D20 from open to in progress.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The RG-D20 test reads living text.** Editing one of the 13 instructions, or the code it describes, reds the matching case until the two agree again. That is the point. Two cases will meet in-flight work:
  - (h) holds RUNBOOKS §n step 1's "`M-GAP` joined it" equal to whether `register` accepts M-GAP as a target. Order 8's M-GAP bar (announced on #1004) changes the code side, so the PR that lands it must change step 1 in the same commit.
  - (a) holds llm.py's note to the code's `messages.create` call sites. A new call site, say in `vinci/evals/`, must be named there.
- **Found, not fixed (CLAUDE.md, outside this scope):** CLAUDE.md's header names nine RUNBOOKS loops, and RUNBOOKS §o, cross-setup validation (#1000), is not among them. (e) checks only that every loop named is live, so it passes; making the list complete is a CLAUDE.md edit, which the decision-line hook sends to the operator.
- **RA-D2's and RA-D4's named tests skip without the licensed CIQ bundles**, so CI never runs them. They pass with the local bundles (S4's check of batch 3 on #1004).
