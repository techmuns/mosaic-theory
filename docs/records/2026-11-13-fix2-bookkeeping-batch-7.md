---
id:
status: shipped
date: 2026-11-13
prs: [958, 1030, 1034, 1035, 1036, 1037, 1038, 1041, 1042, 1044]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 7 (A, the coordinator): RG-D9, RG-D11, RG-D12, RG-D14 and RG-D15 to `fixed` (#1030, order 8), RG-D10 to `fixed` (#958 and #1030), RG-D13 to `in progress (#1030)`, RG-D19 to `fixed` (#1036), six PRs that move no ID recorded, the hand-offs amended, and row 60 recounted (of 148 asked: 139 fixed, 1 open, 7 in progress, 1 disagreed)

**WHAT.**
- **The fix log**, `docs/fix-log-teamnostra-2.md`:
  - **RG-D9, RG-D11, RG-D12, RG-D14 and RG-D15 → `fixed`** (#1030, `98707f29`, order 8, the evaluation harness, merged 2026-11-12 20:16Z). Each row names its behaviour, its residual where #1030's record states one, and the test nodes that pin it:
    - RG-D9: drawn once across approvals, by design, by request bytes, and the judge's TEST half once. Its accepted risk, two checkouts each drawing a twin design, is held by one drawing machine (operator: "One drawing machine (Recommended)");
    - RG-D11: the gold checked against its hashes before any metric reads it and before any paid draw. Residual: the MANIFEST read is the working copy's;
    - RG-D12: BASE's production files, scored under main's harness, enforced in the library;
    - RG-D14: a registration is a row on main before it is drawn;
    - RG-D15: the capture's model is production's, and the judge keeps its own.
  - **RG-D10 → `fixed`**, by two PRs. #958 (`54fa825b`, merged 2026-11-10) closed the `run` command. Its body names no ID, so no batch booked it, and the row read `open` until now. #1030 (B's gap 2) closed the library's paid path. Residual, deferred in #1030's record (D2): the library guard checks only that a registration string is present.
  - **RG-D13 → `in progress (#1030)`, not `fixed`.** #1030's own bookkeeping section calls it partial. M-GAP is barred as a target. The lasting fix, an independent coding of its gap types, is new gold and the operator's to commission. Fix-log rule 1 keeps an ID `in progress (#N)` where its PR calls it partly fixed.
  - **RG-D19 → `fixed`** (#1036, `c2934d07`). By the rule's words, the counts are LLY `bull_points[5]` 14, VITL `bull_points[2]` 13 and WERN `bull_points[5]` 14. WERN's is counted with hyphenated compounds split; it is 11 at whitespace only. A's 15, 14 and 14 admitted one differing word.
    - The build now refuses a page whose synthesis shares more than 12 consecutive words with its own calls.
    - The three runs are cut at $0.
    - The row keeps #941, #951 and #1006, and its page cell adds #1036's cuts.
    - **Not booked:** A's cut of the 25 transcript runs in tracked files. Its spot audit found 21 in five records and two test files (issue #1004, 2026-11-12 17:36Z; operator: "Cut all 21 + guard (Recommended)"), and its local guard found 4 more (operator 2026-11-13: "Cut all 25, one PR (Recommended)"). It is open as #1046, opened 2026-11-12 20:52Z while this batch was being written, and is not on main at `98707f29`. RG-D19's row names it as pending.
  - **E2-D11's MVST half → not fixing: name retired** (operator 2026-11-12, verbatim: "we want to drop/remove MVST altogether from our list for future as well"; the coordinator's addition to this batch, 2026-11-13). The MVST strict-xfail node leaves the row's test cell, and its Pages cell says MVST's page leaves the corpus with #1044, as AORT's rows read after its retirement. The row stays `fixed`: EPAM's node keeps it valid for `tests/test_fix_log.py`, and WERN's half is unchanged. #1044 keeps that node only as a skipped stub so the log's name check stays green, and deletes it once this merges.
  - **The log's header sentence on order 2** read "in code but for RG-D19 … PR 3 is to come". PR 3 merged in batch 5 (#1006), and RG-D19 is fixed now, so the sentence says so.
- **STATE.md §5.0 row 60:**
  - the title recount, with its boundary;
  - batch 7 in the list of batches;
  - one batch-7 clause;
  - the RG-D19 stream's "Still open" clause, now FIXED by #1036, with the rule's counts. What stays open there is A's cut of the 25 (#1046), RG-D8's clause-binding half and the frozen-panel replay;
  - batch 5's clause keeps A's 15, 14 and 14, with the rule's 14, 13 and 14 beside them;
  - "order 2 is in code but for RG-D19" now reads in code;
  - #953's retrospective: order 8 has merged, so it is A's to register, and it has not run;
  - the split sentence: fix 4b no longer waits, and A took back the four items B finished. Batch 7's hand-offs amendment, on batch 3's record, has the detail;
  - the #956 clause: "MVST retired 2026-11-12: it has no next build", with its ruling, the edit #1044 drops from its own diff because fix-log rule 1 keeps row 60 out of fix PRs.
- **No ID and no row**, each by its own body:
  - **#1034** (`650057f3`): the stock-info price note counts a stale close from the page's reference date. Its body: "Fix log: no row (not a fix-request ID)".
  - **#1035** (`3a6ce8fb`): the operator's three approvals of 2026-11-12 and the coordinator's nine defaults, recorded. It names RG-D20 only as a lint it ran, and as a weakness it found in that lint's case (e) and did not fix: a truncated loop name passes. RG-D20's row is unchanged.
  - **#1037** (`407dc809`): VRRM's second `run-monthly` rehearsal (row 38), docs only.
  - **#1038** (`43c2355f`): row 51 (2). It is coordinator default 9 under the operator's delegation, not an ID. Its body: "Fix log: no row; row 51 is not a fix-request ID".
  - **#1041** (`047f4c6b`): the rebuild prep (row 28). Its body: "None: no fix-log ID moves".
  - **#1044** (MVST retired, operator 2026-11-12), **booked ahead**: it is open, and merges after this batch, which the coordinator ordered. It names no fix-log ID. Its one effect on the log is E2-D11's MVST half, booked above. If #1044 does not merge, that cell and the #956 clause overstate MVST's state.
  - **#1042** (`f2e31cea`): coordinator default 6. It closed STATE row 49 itself. It names RH-D3 only as #996's earlier fix of `bin/commit`, which RH-D3's `fixed` row already holds.
- **STATE.md §5.0 row 59's title** read "SIX OF ITS SEVEN DEFECTS ARE IN CODE … RD-D1 IN #953 … RG-D19 WAITS FOR A RULING". #953 merged on 2026-11-10, RG-D19 was ruled on 2026-11-09, and this batch books it fixed, so all seven of order 2's rows read `fixed`. The title says so, and its unlock strikes "#953's merge". Its open items (1) and (3) to (5) are unchanged, so the row stays (review round 0).
- **Amendments:**
  - batch 3's record gains a third dated entry on the split's hand-offs;
  - the fix-request record gains a dated entry on MVST's retirement, as it did for AORT's, because its §1 names MVST among order 1's pages.

**WHY.**
- Under batched bookkeeping (operator 2026-11-10), a fix PR edits neither the log nor row 60, and one writer applies each batch: S4, B's stream, for batches 4 to 6, after #1011 (batch 3, A's). B is paused until 2026-11-18, and its hand-back makes A, the coordinator, the log's only writer until B resumes. That hand-back (issue #1004, 2026-11-12 16:56Z) named batch 7: "RG-D19 to fixed (#1036: LLY 14, VITL 13, WERN 14 hyphen-split), RG-D9–D15 when order 8 merges, and the PRs above".
- A brief that said "RG-D9 to RG-D15 → fixed by #1030" was checked against #1030's own section, which reads "partial" for RG-D13. The section wins.

**HOW VERIFIED.**
- **Order 8 fails first, on #1030's parent `f2e31cea`.** A throwaway sparse worktree held `f2e31cea`'s `vinci/` with #1030's 16 files under `tests/` (the 15 changed test files #1030's own check counts, and `tests/evals_scorer_stub.py`) and its other non-code files laid over it. It was removed after the runs. The rows name 18 distinct #1030 nodes, and all 18 fail or error there:
  - **9 fail on an assertion about the old behaviour:**
    - RG-D10, gap 2: "a paid client was built before the refusal", and `DID NOT RAISE ReplayError` for an injected real client;
    - RG-D11: `DID NOT RAISE ValueError` for an edited label, and again for an edit inside one coder's half;
    - RG-D12: `DID NOT RAISE ReplayError` from the library's `register`, and the CLI calling no scorer check before `register`;
    - RG-D13: `DID NOT RAISE ReplayError` for M-GAP as a target;
    - RG-D15: `assert 'claude-opus-4-8' == 'claude-test-x'`, and `capture_child.py` still naming a model of its own.
  - **7 fail only because a name the fix adds is missing.** Five need `vinci.evals.registry`: three of RG-D9's and both of RG-D14's. The index is that fix. The other two need `gold.verify_gold` (RG-D11's gap-4 node) and `refuse_unless_scored_by_base` (RG-D12).
  - **2 error in a fixture.** It stands in RG-D12 by patching `refuse_unless_registered_scorer`, which the parent lacks:
    - RG-D9's and RG-D14's library node, `test_a_paid_run_compare_with_no_index_claim_is_refused_before_any_client`. With the stand-in made a no-op in the throwaway tree, it fails on behaviour: "a paid client was built before the refusal". The library drew with no index claim. So every row names at least one node that fails on behaviour;
    - RG-D13's `test_a_registration_whose_only_target_is_barred_decides_nothing`.
- **RG-D10's #958 node fails on #958's parent `a71b9f67`.** It was run with #958's own test file: `DID NOT RAISE ReplayError`, after "NFLX: 0/5 usable draws", so the `run` command drew with no registration. It passes at #1030's parent and at main.
- **At main `98707f29`** (this branch), all 19 named order-8 nodes pass, in a run of 28 nodes.
- **RG-D19, on the committed corpus first.** `tests/test_transcript_run_guard.py::test_no_committed_synthesis_copies_more_than_12_words_of_its_calls` was run against the licensed calls on this Mac's Drive mirror. It reads them in place, read only, and prints a field and a word count, never words.
  - **At main `98707f29`, on all 27 committed pages:**
    - 21 pass, LLY and VITL among them;
    - 5 skip: IT, MVST and WERN, each because a call its page cites is not on this mirror, and ORKA and TECX, which have no call;
    - PARR fails: reading its CIQ folder raises `CiqMislabelledError` on its mislabelled quarterly Financials export. That is an input fault, not a run (Found, not fixed).
  - **With main's code over `68bd4b33`'s three uncut pages:** LLY `bull_points[5].claim` fails at 14 and VITL `bull_points[2].claim` at 13. WERN skips, as above.
  - So LLY's and VITL's counts are reproduced here. WERN's 14 is #1036's measurement, against the call on the primary checkout's mirror.
  - #1036's guard pin cannot fail on behaviour at `68bd4b33`. Its file fails to import there, because `vinci.dossier.transcript_run_pass` does not exist; the guard is the fix.
- **The count.** It is a script over `tests/test_fix_log.py`'s own `parse_log`, by Status cell. As a control, the same script on `origin/main`'s log gives batch 6's numbers: 132 fixed, 38 open, 7 in progress and 1 disagreed of 178; 132, 8, 7 and 1 of 148.
- **The PR list.** It comes from `git log --first-parent 4b2f0cb9..98707f29`, batch 6's base to main: nine commits, batch 6 itself (#1033) and the eight booked here. Each PR's body was read for a "Bookkeeping for the coordinator" section and for ID-shaped tokens.
- **The lints.** These pass on this branch:
  - `tests/test_fix_log.py`;
  - `tests/test_state_open_now.py`;
  - `tests/test_state_identifiers.py`;
  - `tests/test_records_ledger.py`;
  - `tests/test_record_status_matches_open_now.py`;
  - `tests/test_record_legibility.py`.
- **The full gate.** Its run is in the PR.

**BOUNDARY.**
- **The PRs:** every first-parent commit on `origin/main` from batch 6's base `4b2f0cb9` through `98707f29` that batch 6 did not book. These are #1035 and #1034, merged before batch 6 itself, and then #1036, #1038, #1037, #1041, #1042 and #1030. #958 (merged 2026-11-10) is added for RG-D10, and #1044, open, is booked ahead at the coordinator's request. They were read on 2026-11-13.
- **The counts:** all 178 fix-log rows by their Status cell, and separately the 148 asked, which is every Order but `§4`. They are counted on this branch's log, cut from main `98707f29`, on 2026-11-13.
- **The fail-first runs:** 18 #1030 nodes at `f2e31cea`, one #958 node at `a71b9f67`, and #1036's guard file at `68bd4b33`. All were run on 2026-11-13, in a throwaway worktree with this checkout's venv.
- **The corpus check:** the 27 committed pages at `98707f29`, and `68bd4b33`'s LLY, VITL and WERN pages, against this Mac's Drive mirror of the licensed calls as it read on 2026-11-13.

**THE COUNT.**
- Of the 178 rows: 139 fixed, 31 open, 7 in progress, 1 disagreed.
- Of the 148 asked: 139 fixed, 1 open (RE2-D17), 7 in progress, 1 disagreed.
- Against batch 6:
  - RG-D9, RG-D10, RG-D11, RG-D12, RG-D14 and RG-D15 moved from open to fixed;
  - RG-D13 moved from open to in progress;
  - RG-D19 moved from in progress to fixed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **RG-D19 is `fixed` while the same rule's tracked-file half is not on main.** RG-D19 is the pages and syntheses, which #941, #951, #1006 and #1036 cover. 25 more runs over 12 words sit in tracked files outside every page: the 21 A's spot audit found in five records and two test files, and 4 its local guard found. The operator ruled to cut them, and the cut, #1046, is unmerged. RG-D19's falsifier is a committed synthesis holding a run over 12 words against its own calls. The corpus check above fails on one wherever the calls are readable, and never in CI, which holds none. It does not read records or test files, so the 25 runs are outside it: nothing on main guards that half until #1046's cut and its local-only scan of every tracked file land.
- **WERN's count is not re-measured here.** Its cited call is not on this Mac's mirror, so its 14 rests on #1036's run.
- **Seven of the 18 order-8 nodes fail at the parent only by a missing name.** Every row also names a node that fails on behaviour. For RG-D9 and RG-D14, that node is shown failing on behaviour only with its RG-D12 stand-in made a no-op, because as written it errors in that fixture at the parent.

**FOUND, NOT FIXED** (outside this batch's brief):
- **The corpus check fails, rather than skips, on PARR** wherever the calls are readable. Reading PARR's CIQ folder raises `CiqMislabelledError` on its mislabelled quarterly Financials export, the input fault #1030's cross-setup check met at both refs, so no run is checked on PARR. CI holds no calls, so it skips there.
- **STATE §5.0 row 28 still reads "proposed cap $170".** The operator approved $170 on 2026-11-12, relayed by B and confirmed by A on issue #1004, with its terms there. This batch's hand-offs amendment states the approval, and row 28, the rebuild's row, does not yet.
