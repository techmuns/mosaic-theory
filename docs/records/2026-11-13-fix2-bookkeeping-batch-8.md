---
id:
status: shipped
date: 2026-11-13
prs: [1039, 1040, 1043, 1044, 1045, 1048]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 8 (A, the coordinator): #1039's and #1040's residual fixes booked into E2-D15, V2-N1 and RG-D3 to RG-D5 (fix (d) OPEN), RBC-D1's MVST part not fixing, four PRs that move no ID recorded, the operator's four rulings of 2026-11-13 recorded and carried into §5.0 rows 28, 30, 34, 35, 41, 51, 52, 54 and 59, two record amendments, and row 60 recounted (of 148 asked: 139 fixed, 1 open, 7 in progress, 1 disagreed; no status moves)

**WHAT.**
- **The fix log**, `docs/fix-log-teamnostra-2.md`. Every row it touches was already `fixed`, so no status moves; each gains the merged PR, its tests, and the residual its record states.
  - **E2-D15, WERN's half** (#1039, `f676616f`): fixed in code.
    - Werner's Q3 10-Q (`0000793074-26-000172`) reads located $0.0 from the balance sheet's own debt total, which undoes #956's regression.
    - The operator ruled on 2026-11-13, verbatim "$0.0 + LSA stated (Recommended)", and the ruling adds no line. The same 10-Q extends the LSA's termination to 2028-03-27, outside the window (#1039's record, round 2).
    - WERN's page waits for its rebuild, in the active set; its strict xfail stays.
  - **V2-N1** (#1039, round 1): the in-clause check runs before both routes. A total stated inside the clause and repeated by another sentence at the same date had read located $45.0 for one instrument; it no longer does.
  - **RG-D3** (#1040, `fd1c97f3`, W05 item (a)): a metric word no row label carries binds the row it names.
    - **Item (d) is OPEN in the cell:** a January or February year end's "fiscal YYYY". #1040 dropped it in review round 1, because TJX and nCino name their years as CIQ does, while Ross, Target and Burlington name a year by the year it starts. It is pinned strict-xfail, and no committed claim writes it.
    - No cell had claimed (d). RG-D5's cell had said "S2's false-flag PR takes it as item (e)", which is now replaced by what #1040 did.
  - **RG-D4** (item (b)): a figure inside the cited fact's printed width traces. PARR's "$21.54" clears at its next build, and PARR is on watch.
  - **RG-D5** (items (c) and (e)): a year naming what it dates is no figure, and a field name, an accession, a URL or a hash states no span. VITL's "2030" clears at its rebuild. (e)'s residual stands, as #1040 measured it.
  - **RBC-D1's MVST part** reads "not fixing: name retired (operator 2026-11-12)", its page off the corpus with #1044 (`12764514`), as AORT's part reads. MVST leaves the "count written at $0" list.
  - **No other row naming MVST is open.** Only E2-D11 (batch 7) and RBC-D1 name it, and both are `fixed`.
- **No ID and no row**, each by its own body:
  - **#1043** (`c0b6a519`): the transcripts design, STATE row 61. Its body: "None: no fix-log ID moves".
  - **#1045** (`b73bd4ef`): the local-path guard reads the theme desk's committed logs and STATE.md.
  - **#1048** (`b207c8a9`): coordinator default 3, the replication rule as the default. It closed row 53 item (7) itself. Its body: "not a fix-request ID".
  - **#1044** (`12764514`): booked ahead in batch 7. Its bookkeeping section asked for RBC-D1's line, made here.
- **The operator's four rulings of 2026-11-13**, below, carried into STATE §5.0:
  - **Rows 28 and 41:** a dated UPDATE each. The rebuild is the 10 active pages; VRRM is active with no rebuild; 15 pages go on watch with no paid rebuild. The unlock cells no longer ask for a watch page's re-export or rebuild.
  - **Rows 34 and 35:** the six watch pages that keep known errors say so, and say they stay until the name goes active. These are UBER (rows 28 and 34), WLK, PARR, AMZN and NFLX (row 34), and ORKA (row 35).
  - **Rows 30, 51, 52, 54 and 59:** one clause each, where a row promised a watch page a rebuild:
    - UBER's guide periods (row 30);
    - NFLX, UBER, PARR, ORKA and V's window (row 51);
    - NFLX's one rebuild (rows 52 and 54);
    - TECX, UBER, V and WLK's customer count (row 59).
  - **Row 60:** the batch-8 clause, and its #956 clause: the fix is #1039.
- **Amendments:**
  - **#1041's record:** the active set and the descoped watch pages, so its cost line stays true. B asked for this.
  - **#956's record:** the fix is #1039; WERN's half holds and MVST's does not. #1039's body asked for this.

**THE OPERATOR'S RULINGS OF 2026-11-13** (each verbatim, with its source):
1. **The coverage marking for the rebuild.**
   - The source is B's note on issue #1004 (issuecomment-6847554747, 08:05Z). The operator approved it, *"go ahead"*, accepting B's suggested table from issuecomment-6847522000 unchanged.
   - **Active and rebuilt (10):** GOOGL, NCNO, SMPL, TJX; EPAM, LLY, VITL; IT, WERN; and BRBR after its FY26 10-K and a full re-export.
   - **Active, no rebuild now:** VRRM.
   - **Watch, no paid rebuild (15):** AMZN, BURL, CNXC, FUBO, MCK, NFLX, NKE, ORKA, PARR, ROST, TECX, TGT, UBER, V, WLK.
   - **Cost:** $36.96 at last cost, re-derived here from #1041's per-page table. With the ×1.255 allowance it is $46.38; B's note says about $46.39, rounding per page. The $170 cap stands; the operator approved it on 2026-11-12, verbatim *"budget 170 approved"*, relayed by B on #1004.
2. **Group 2's fix-3b losses accepted.** Source: issuecomment-6847662066, verbatim *"accept all three"*. They are EPAM's `buyback_avg_price` for 2023-Q1, LLY's `buyback_shares` for 2021-H1 and VITL's `buyback_shares` for 2019.
3. **Spend caps.** Source: issuecomment-6847993179, verbatim *"Report only"*.
   - The monthly spend ledger reports and refuses nothing.
   - Per-run caps are unchanged: every paid run still needs the operator's approved cap before it spends.
   - No §5.0 row tracks a monthly cap, so this record holds the ruling.
4. **E2's panel cap.** The operator to A in chat, 2026-11-13, verbatim *"Estimate +20%, max $40 (Recommended)"*. #1027's record carries it. #1027 is an open draft, so this is a pointer by PR number, not by path.

The rest of issuecomment-6847522000 quotes further operator answers: no feature freeze, the screen-basket baseline, the recipes, retirement and caps, and the ledger. Each is a lane's own and outside this batch's brief; none is recorded here.

**WHY.**
- **Batched bookkeeping** (operator 2026-11-10): a fix PR edits neither the log nor row 60, and A writes this batch for the coordinator.
- **The coverage marking descopes 15 pages from a rebuild** that rows 28, 30, 34, 35, 41, 51, 52, 54 and 59 promised them. A snapshot still promising those rebuilds would state a false current fact.
- **"Fixed" stays "fixed".** #1039 and #1040 fix residuals that rows already `fixed` had named. Rule 3 asks a row to name its PR and its test, so each row gains both, and no status moves.

**HOW VERIFIED.**
- **#1039 fails first at its parent `c0b6a519`.** This ran in a throwaway sparse worktree: the parent's `vinci/` with #1039's test file. The worktree was removed after the runs.
  - As committed, the file fails to import there. `vinci.edgar.filing_sections` has no `_balance_sheet_debt`, the helper #1039 adds.
  - With that one import made tolerant in the throwaway tree, both named nodes fail on behaviour:
    - E2-D15's WERN node reads `('not_stated', 'no near-term wall stated in filing for the whole debt — $0.0M due ≤12m is stated for part of it only …')`;
    - V2-N1's twin reads `('located', 45.0)`.
  - #1039's record states the same: 3 of its 22 tests fail on behaviour at main.
- **#1040 fails first at its parent `f676616f`,** with #1040's test file and frozen pages laid over the parent's tree. The test file has 34 nodes: 20 fail, 11 pass, and 3 XFAIL, the (d) pins.
  - 18 of the 20 fail on behaviour: PARR's `['21.54']` flagged, a metric word's figure flagged, a field name's span read, and others.
  - 2 fail only on a missing attribute: `printed_half` and `named_windows`.
  - The 7 named nodes that are not (d) pins all fail on behaviour. One of them, `test_a_metric_no_row_carries_falls_back_to_the_cited_fact`, has 10 cases: 7 fail and 3, its negative pins, pass. The (d) pins XFAIL at the parent and at main, as strict xfails should.
- **At main `b207c8a9`** (this branch), the named nodes give 18 passed and 4 xfailed: the three (d) pins and WERN's page pin.
- **The count** is the same script over `tests/test_fix_log.py`'s `parse_log` that batch 7 used.
- **MVST** is named in exactly 2 log lines, E2-D11 and RBC-D1, both `fixed`.
- **The cost:** groups of $16.18 + $10.11 + $8.88 + $1.79 = $36.96, from #1041's per-page last costs, with the $4.44 median for NCNO, IT and WERN.
- **Lints and the full gate:** in the PR.

**BOUNDARY.**
- **The PRs:** every first-parent commit on `origin/main` from batch 7's base `98707f29` through `b207c8a9`, less batch 7 itself (#1047, `dad8f441`). These are #1043, #1039, #1040, #1045, #1044 and #1048. They were read on 2026-11-13.
- **The counts:** all 178 fix-log rows by their Status cell, and the 148 asked, which is every Order but `§4`. They are counted on this branch's log, cut from main `b207c8a9`, on 2026-11-13.
- **The fail-first runs:** #1039's 4 nodes at `c0b6a519` and #1040's 34-node file at `f676616f`, on 2026-11-13.
- **The coverage set:** B's table at main `12764514`, as the note states. Last costs are from #1041's record.

**THE COUNT.**
- Of the 178 rows: 139 fixed, 31 open, 7 in progress, 1 disagreed.
- Of the 148 asked: 139 fixed, 1 open (RE2-D17), 7 in progress, 1 disagreed.
- Against batch 7, no status moves.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **#1039's behaviour fail is shown only with its import made tolerant.** As committed, its test file cannot import at the parent. The named nodes assert on `_maturity_wall` before they read the new helper, so the measurement reads the parent's behaviour.
- **Watch pages keep known errors.** Six named pages carry them, and the other nine keep whatever their committed pages hold. The falsifier: a watch page made active and rebuilt with no row noting what changed. Each row names its pages, so the rebuild's PR can check them.
- **Item (d) stays open with no owner.** #1040's body asks for a §5.0 row or a log line if it needs one. RG-D3's cell now names it, which is the log line. No §5.0 row is opened here: §5.0 is capped at 60 lines, and the coordinator did not ask for one.
