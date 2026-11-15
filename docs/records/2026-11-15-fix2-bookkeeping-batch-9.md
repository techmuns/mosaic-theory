---
id:
status: shipped
date: 2026-11-15
prs: [1027, 1053, 1054, 1056, 1057, 1058, 1059, 1060, 1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 1070, 1071, 1072, 1073, 1074, 1075, 1076, 1077, 1078]
supersedes:
superseded-by:
---

# Fix request 2 bookkeeping, batch 9 (A, the coordinator): RE2-D6, RE2-D10, RE2-D17 and RE2-D20 to fixed (#1027, each verified against its diff and tests), E2-D11's and E2-D15's WERN halves landed (#1076), RG-D19's deferred test gaps closed (#1058), #953's retrospective booked into row 60, RD-D1 and RA-D4, STATE row 62 restated to B's machine, row 41's WERN clause corrected (its stale part is the export's FY2025 column, not the export; operator: "Wait for the FY2026 10-K"), row 64 opened for #1070's deferred Codex P1 and #1069's vintage misstatement, and row 60 recounted (of 148 asked: 142 fixed, 0 open, 5 in progress, 1 disagreed)

**WHAT.**
- **The fix log**, `docs/fix-log-teamnostra-2.md`. Four statuses move, all by #1027 (`a7d6dc46`, the E2 remainder, merged 2026-11-13 13:12Z). Each row was checked against #1027's diff and its tests before it moved (HOW VERIFIED).
  - **RE2-D17, `open` → `fixed`.** A one-off carries its period (`OneOffItem.period`, `release_parse._one_off_period`), stated in the digest and the gap-driver line. The full-year impairment numerator passes over a quarter's, a span's or an unread item.
  - **RE2-D6, `in progress (#962)` → `fixed`.** #962's residual is fixed: a component ("including an SRE impact of …") is not its figure's lead, so Par Pacific's Q3 2024 adjusted net loss reads −5.5.
  - **RE2-D10, `in progress (#966)` → `fixed`.** #966's other half is fixed: a filing whose notes were read and that states no doubt is CHECKED-ABSENT, never None.
  - **RE2-D20, `in progress (#976)` → `fixed`.** The 21 guides on the `next-fy` default read the period their release states (21 → 0 default flags on the committed pages' 122 cited EX-99.1s, #1027's replay).
    - #1027's record names one residual. Verra Mobility's Q3 2025 release (8-K `0001193125-25-256337`) keeps its three full-year guides on the flagged default, because its only period sits inside a "Based on …" basis clause and its section title is not read. That release is on no committed page.
    - It is outside RE2-D20's ask, which the fix log states as the 21 unread list headers.
  - **Each row's Pages cell** now says what landed. The 9 pages rebuilt since #1027 merged carry its code: EPAM, GOOGL, IT, LLY, NCNO, SMPL, TJX, VITL and WERN (main `1f32cbdf` or later). Measured on the committed pages at main `c58d5b2f`:
    - **RE2-D10:** those 9 read CHECKED-ABSENT (`substantial_doubt` false, no verbatim); the other 17 read None.
    - **RE2-D17:** 9 one-offs on SMPL (7), IT (1) and LLY (1) carry a period. BRBR's 4, VRRM's 4 and WLK's 1 carry none.
    - **RE2-D20:** EPAM, SMPL and VITL carry no `next-fy` guide. BURL's 2 and VRRM's 5 wait for their next re-assembly, where #1027's replay reads BURL 1 and VRRM 5.
    - **RE2-D6:** none now. PARR's −5.5 reaches no page: its $0 build reads a newer release set (#1027's record), and PARR is on watch.
  - **E2-D11's and E2-D15's WERN halves** (#1076, `68e8c474`, merged 2026-11-14 18:41Z). #1076 deferred these two notes until it merged, because `tests/test_fix_log.py` refuses a `fixed` row naming an unmerged PR (#1076's review row 2). Both rows already read `fixed`, so no count moves.
    - **E2-D11:** WERN's page pin, re-pointed to the two releases the page cites (8-K `0000793074-26-000165`, Q3 2026, revenue 950.5; `-000129`, Q2 2026, 933.9), is no longer strict-xfail.
    - **E2-D15:** WERN's wall reads located $0.0 from its September-quarter 10-Q (`0000793074-26-000172`). The page states its DIVERGES flag against the CIQ panel (panel same-window $752.0M against filing $0.0M), as #1039's impact check foresaw.
  - **RG-D19** (#1058, `723aeeb1`). Batch 8 wrote that #1046's three deferred test gaps "wait on a follow-up PR, not yet open". #1058 is that PR and closes all three, each behind a pin that fails under its defect. #1058's own section asks for no fix-log edit, but the row's claim was false once it merged, so the cell names #1058 and its two CI-runnable pins. No status moves.
  - **RD-D1 and RA-D4** (#1063, #1066). #953's retrospective panel check, the falsifier of batch 3's FACTS-only ruling, was registered (#1063, `978a6a52`) and then drawn once and scored (#1066, `1f32cbdf`).
    - **The result:** no class metric worsens (M-PATH nearest, 3 → 6 at p_upper 0.131). The panel's committed-lean draws moved 8 → 15 (two-sided p 0.0274), measured and not explained. BURL:CAND has 1 usable draw of 5.
    - **The operator's ruling,** verbatim from #1066: "Keep it, watch leans (Recommended)". FACTS-only request moves still owe no paid panel by default.
    - **RD-D1's cell** names the check.
    - **RA-D4's cell** said BURL's #983 move was "an operator question after #953's retrospective run". It now says the operator kept the default after that run.
    - **RA-D4's Pages cell** also said "none rebuilt". #983 (`85306351`) is an ancestor of `1f32cbdf`, so SMPL, whose export the RA-D4 test reads, was rebuilt on its code (#1067). Its committed guidance bridge keeps both periods guided on 2026-10-27 (FQ1 2027 and FY 2027) for Revenue, EBITDA and Gross Margin %. #983's record counts 16 of 27 pages moving but does not name them all, so the other 8 rebuilt pages are not re-measured (review round 1).
- **STATE.md §5.0.**
  - **Row 60:**
    - the batch-9 clause and the recount;
    - #953's retrospective, in the pre-merge-check clause and the #983 clause;
    - #1058 in the #1046 clause;
    - the RE2 sentence: RE2-D6, D10 and D20 no longer "stay in progress".
  - **Row 62, restated** to the part that stands: what B's machine runs is unverified. The operator's-Mac part is closed (HOW VERIFIED).
  - **Row 64, new**, owner agent: two statements on committed pages, each fixed by a code PR. They share one row because §5.0 was at 59 of its 60 lines, and two new rows would breach the cap.
    - **(a) Codex's P1 on #1070, deferred.** A page's `date_semantics.analysis_as_of` can read earlier than its CIQ export date, though a CIQ fact is knowable from its export date, never from its period end. What unlocks it: a code PR that counts the export date.
    - **(b) #1069's vintage misstatement.** `vinci/dossier/extraction_versions/2026-11-14.form4-price-its-filing-contradicts-is-refused.json` says the guard refuses "19 sale prices, 14 of them correct". #1069's own record says 16 of the 19 are correct and 3 wrong, and 14 of the 16 are in the 2025-02-25 filing.
      - The text renders into LLY's Extraction note: `data/dossiers/LLY/dossier.md`, line 657, and its mirror `frontend/dossiers/LLY.md`.
      - What fixes it: a code PR that changes the vintage text, then a $0 re-render of LLY. This batch is docs only and does not edit that file.
      - **#1080 (open, lane 3)** is that PR. It amends the vintage's prose and re-renders LLY's page and mirror at $0. The merge order is the coordinator's: this batch first, then #1080 merges main, keeps both row-35 edits, and closes 64 (b). Row 64's unlock cell names it.
  - **Row 35** gains a pointer to row 64 (b), because it already holds #1069's guard and LLY's Extraction note.
  - **Row 41's WERN clause, corrected** (the coordinator's addition to this batch, 2026-11-15). #1076 added an OPERATOR ACTION about WERN's key-unknowns line (`data/dossiers/WERN/dossier.md:253` and its mirror), which says the CIQ panel shows "a $752.0M facility" due within 12 months. That figure is the panel's two revolvers, $427.0M and $325.0M.
    - **The wrong premise.** The clause said the misstatement was unlocked by "a WERN CIQ re-export made after the 2026-10-05 termination", then one paid rebuild of about $7.80. But the export is not stale: WERN's committed CIQ export is dated 2026-11-12, already after the termination.
    - **What is stale is the PERIOD inside it.** `mechanical.capital_structure.instruments` is sourced from "CIQ Financials→Capital Structure Details (A 2025 filed Feb-26-2026)", the FY2025 annual column, 232 days old by its `panel_vintage`. That column still lists the 22 Unsecured Credit Agreement ($427.0M, maturing 2026-10-05) and the Loan Security Agreement Facility ($325.0M, maturing 2027-09-21).
    - **The filing.** The September-quarter 10-Q `0000793074-26-000172` states $803.0M outstanding under the Credit Facilities, with no principal due within 12 months.
    - **Why a re-export does not help yet.** A same-settings re-export does not change that annual column before the FY2026 10-K. A quarterly column would: FUBO's committed page reads "Capital Structure Details (Q3 2026 filed Aug-05-2026)".
    - **The rulings.** The ruling of 2026-11-14, "Wait for a fresh CIQ export (Recommended)", rested on the coordinator's wrong premise. The operator re-ruled on 2026-11-15, relayed to this session by the coordinator, verbatim: "Wait for the FY2026 10-K". The option reads: no action until Werner's FY2026 10-K (~Feb 2027) and a normal re-export, and the page keeps its vintage warning until then.
    - **The new unlock:** Werner's FY2026 10-K and a normal CIQ re-export, then one paid WERN rebuild under #1041's rule. The old unlock text is struck as written, not rewritten.
    - **Where the correction lives.** WERN's record (`docs/records/2026-11-14-wern-lands-after-the-quote-fix.md`, lines 64 to 71) is immutable, so the correction is stated here.
- **No ID and no row,** each by its own body:
  - **#1053** (`53b77a1a`): the ledger safeguards (#1004 item 5).
  - **#1054** (`e832fbaa`): the R1 screening anchor moves off the headline (#1004 item 3c).
  - **#1056** (`5649a650`): three uncalled modules retired. It re-pointed RE2-D15's Test cell itself, to `tests/test_retired_modules.py::test_a_retired_module_is_gone_and_nothing_imports_it`, because the module its old test read was removed. That edit merged before batch 8, which did not record it. No status moves.
  - **#1057** (`6244dbf8`): RUNBOOKS §n, the composite scorer checkout's extra file. It asks that #953's registration record state that file and the reason for it. #1063's commit message and #953's record (`docs/records/2026-11-13-pr953-measured-on-the-panel.md`, line 43) both name `vinci/graph/llm.py`, so there is nothing to write.
  - **#1059** (`9786c8b9`): the impact check sees a key-order-only request difference.
  - **#1060** (`6a5a28f5`): the $0 screen-basket baseline (#1004 item 2).
  - **#1061** (`81f97600`) and **#1064** (`b354882d`): the monthly spend report and its two Codex P1 fixes.
  - **#1062** (`48cf62ee`): #1027's panel check, drawn once and scored. It is booked in row 60's batch-9 clause, under #1027.
  - **#1063** (`50d8337b`): #953's retrospective registered. It is booked under #953's retrospective above.
  - **#1065** (`6652a242`) and **#1072** (`e7457bb1`): the gate on workers, and its status-change check.
  - **#1067, #1068, #1070, #1071, #1076 and #1078:** the rebuild of 9 active pages. Only #1076 names IDs (above); the rest name none. #1067's "G-D3" is part of an extraction-version name, and no G-D3 row exists in this log.
  - **#1069** (`188e0476`): the Form 4 price guard (row 35; its vintage, row 64 (b)).
  - **#1073** (`f9ecad6b`): the covenant line states no cause (row 63). Its section: "Fix-log IDs: none".
  - **#1074** (`4fc47c88`): a release quote never ends before its figure.
  - **#1075** (`2bd2facf`): a price is a date's close only near that date. Its section: "no fix-log ID".
  - **#1077** (`89ac76db`): a transcript passage is filed as the call prints it.

**WHY.**
- **Batched bookkeeping** (operator 2026-11-10): a fix PR edits neither the log nor row 60, and the coordinator applies a batch in one docs-only PR.
- **Verify before marking fixed** (this batch's brief). B reported that #1027 fixed four IDs in code. A row moves only when its named test fails at #1027's parent and passes at main, and when the ask its row states is the thing the test pins.
- **A Pages cell must not go stale under a rebuild.** Rule 3 asks a `fixed` row to name the committed pages the fix changed and rebuilt. #1027 merged before rebuild groups 1 to 3, so "none now" in its suggested rows was already false for 9 pages when this batch was written.
- **Row 62:** the brief said to close it only if nothing in it is still open. B's machine is still unverified, so the row is restated to that part, not closed.
- **Row 64 holds two items in one row** because §5.0 is capped at 60 lines (`tests/test_state_open_now.py`). Both are agent-owned, and each needs a code PR and then a page re-render. Row 32 set this precedent: it folds seven operator actions into one row for the same cap.

**HOW VERIFIED.**
- **#1027, fail first.** A throwaway worktree at #1027's parent `50d8337b` (main, #1063), with #1027's test file and its two fixture files laid over it, ran with that tree's own `vinci/`.
  - The four nodes the rows name all fail there:
    - **RE2-D6:** `test_re2_d6_a_component_inside_the_figure_is_not_its_lead` raises `KeyError: ('adjusted net income', 'Q3 2024')`;
    - **RE2-D10:** `test_re2_d10_a_filing_read_with_no_doubt_is_checked_absent` reads `None` for TECX's real 10-Q;
    - **RE2-D20:** `test_re2_d20_a_header_glued_to_the_last_bullet_heads_its_own_list` reads `'next-fy'` for SMPL's adjusted EBITDA, against "Fiscal 2026";
    - **RE2-D17:** `test_re2_d17_a_charge_carries_the_period_its_release_places_it_in` fails only with `AttributeError: 'OneOffItem' object has no attribute 'period'`, the field the ask adds.
  - **RE2-D17 on behaviour:** two sibling nodes fail there on behaviour, so the row names them too. `test_re2_d17_the_gap_driver_line_states_the_period` gets the line "$11.3M inventory-related charge" with no period. `test_re2_d17_the_full_year_impairment_is_never_a_quarters` reads `35.0`, LLY's prior-year charge, as the year's.
  - **The whole file there:** 24 of its 36 nodes fail and 12 pass.
  - **At main `c58d5b2f`:** all 36 pass, and so do the six named nodes.
  - The worktree was removed after the runs.
- **The earlier halves still hold at main.** #962's, #966's and #976's named nodes pass: `test_re2_d6_a_bracketed_or_minus_negative_is_read_signed`, `test_re2_d10_a_real_conclusion_is_doubt` and `test_re2_d20_a_defaulted_period_is_flagged`.
- **#1027's diff** (`git diff 50d8337b a7d6dc46 -- vinci/`) touches five modules and adds one extraction version. The modules are `vinci/edgar/release_parse.py` (+245 −14), `vinci/edgar/filing_sections.py` (+60 −1: `_notes_heading`, the CHECKED-ABSENT return), `vinci/dossier/schemas.py` (+12: `OneOffItem.period`), `vinci/dossier/mechanical.py` (+18 −4: `_fy_impairment`, the gap-driver line) and `vinci/dossier/synthesis.py` (+6 −1: the digest). Those are the mechanisms the four rows now name.
- **The pages:** each committed `data/dossiers/*/dossier.json` at main `c58d5b2f` was read for `mechanical.primary_source.filing.going_concern`, every release's `one_offs[].period`, and every release's guides with period `next-fy`.
- **WERN (#1076):** `test_wern_revenues_of_releases_carry_their_headline_revenue` and `test_wern_stated_twelve_month_wall_is_located` pass at main, with no xfail mark. WERN's committed `maturity_wall` reads `state` located and `within_12m_total` 0.0, and its DIVERGES line is in `dossier.json`.
- **#1058:** its pins `test_the_real_scan_reads_a_python_file_as_its_joined_literals`, `test_a_line_separator_inside_a_literal_moves_no_offset` and `test_a_call_on_disk_that_does_not_read_fails_the_guard` collect at main. #1058's body shows each failing under its defect, by mutation. This batch did not re-run the mutations.
- **Row 62, the operator's Mac:** the primary checkout's `.venv` reads `anthropic.__version__` 2.6.0 with `pip check` "No broken requirements found" on 2026-11-15, read only.
  - All 11 run lines in `data/snapshots/assembly_runs/` dated 2026-11-14, one per file, state `sdk_version` 2.6.0: NCNO, SMPL, TJX, EPAM, LLY ×2, VITL, IT, WERN and GOOGL ×2. There are no run lines dated 2026-11-13 or 2026-11-15.
  - No run line carries a machine or host field. So nothing here shows what B's machine runs.
- **Row 41's WERN correction:** read from WERN's committed `dossier.json` at main `c58d5b2f`.
  - `mechanical.capital_structure.instruments.source_ref` and `detail_as_of` read "A 2025 filed Feb-26-2026".
  - `panel_vintage` reads "the debt schedule is 232d old (source filed 2026-02-26)" and names the Item 1.02 of 2026-10-08.
  - The instruments are the $427.0M revolver maturing 2026-10-05, the $325.0M one maturing 2027-09-21, and $41.9M of leases with no maturity.
  - The wall's verbatim states $803.0 million "with no principal amount expected to be paid within 12 months".
  - The page's CIQ `source_ref`s read "exported 2026-11-12".
  - FUBO's committed page carries "Capital Structure Details (Q3 2026 filed Aug-05-2026)".
  - The operator's re-ruling is the coordinator's relay to this session (2026-11-15). This batch did not see its source.
- **Row 64 (a), re-measured:** the group 3 record's method was run on the 26 committed pages at main `c58d5b2f`: each page's latest "exported YYYY-MM-DD" in any `source_ref`, against its top-level `date_semantics.analysis_as_of` (`vinci/dossier/schemas.py`, the page's `date_semantics` field).
  - **9 of 26 pages** show an export after the as-of: IT, MCK, NKE, ORKA, TECX, V, VRRM, WERN and WLK.
  - **Against the record:** the record's 8 at `4f7a5d64` (#1070's branch) plus WERN, whose page landed after it (#1076: export 2026-11-12, as-of 2026-11-11).
  - **LLY's file mtime:** the record also counts it as a ninth case at `4f7a5d64`. This method cannot see an mtime, and LLY's page has since been rebuilt (#1071).
- **Row 64 (b):** the vintage file was read on main, and #1069's record (lines 43 and 44) gives the two groups.
  - `0000316011-25-000073`: 4 sales, 2 wrong.
  - The 2025-02-25 filing: 15 sales, 1 wrong.
  - Together, 19 refused: 3 wrong and 16 correct, 14 of them in the 2025-02-25 filing.
  - The string "14 of them correct" occurs in exactly two committed files under `data/dossiers` and `frontend`: LLY's `dossier.md` and its mirror.
- **The count:** a script over `tests/test_fix_log.py`'s `parse_log`, the method batches 7 and 8 used. Before this batch it gives batch 8's figures, 138 fixed, 31 open, 8 in progress and 1 disagreed, which confirms the method. After it, THE COUNT below.
- **`tests/test_fix_log.py`:** 39 passed on this branch, including `test_the_live_log_is_clean`. That test checks every commit in a `fixed` row's Commit cell against `origin/main` and every PR against main's merged list. So #1027's branch commit (`32f4d6a4`, the unread-impairment fix) is described in words, never by its hash, and no accession or issue number sits in a Commit cell.
- **Lints and the full gate:** in the PR.

**BOUNDARY.**
- **The PRs:** every first-parent commit on `origin/main` after batch 8's counted main `3d195fcd`, through `c58d5b2f` (#1078), less batch 8 itself (#1052, `4b8f7426`). They are 26:
  - **#1057, #1056 and #1058**, which merged after `3d195fcd` and before batch 8;
  - **then #1059, #1054, #1060, #1062, #1053, #1063, #1027, #1061, #1064, #1066, #1067, #1068, #1069, #1070, #1065, #1071, #1073, #1074, #1072, #1075, #1076, #1077 and #1078.**
  - `gh pr list --state merged` on 2026-11-15 lists no other PR after `3d195fcd`, and every one targets `main`.
  - The brief also listed #1044, #1046 to #1052 and #1055. Batches 7 and 8 booked #1044, #1046, #1048 to #1051 and #1055, and #1047 and #1052 are batches 7 and 8 themselves. The brief did not list #1053, #1060 or #1065, which the listing found.
- **The counts:** all 178 fix-log rows by their Status cell, and the 148 asked, which is every Order except `§4`. Both are counted on this branch's log, cut from main `c58d5b2f`, on 2026-11-15.
- **The fail-first:** #1027's 36-node test file and its six named nodes at `50d8337b`, and at main `c58d5b2f`, on 2026-11-15.
- **The page reads:** the 26 committed `data/dossiers/*/dossier.json` at main `c58d5b2f`, on 2026-11-15. The unit is one page, one one-off item, or one guide item.
- **Row 62:** one venv, the primary checkout's `.venv`, read on 2026-11-15; and the 11 run lines dated 2026-11-14 at `c58d5b2f`.

**THE COUNT.**
- **Of the 178 rows:** 142 fixed, 30 open, 5 in progress, 1 disagreed.
- **Of the 148 asked:** 142 fixed, 0 open, 5 in progress, 1 disagreed.
  - **The 5 in progress:** RG-D3 (#1040, item (d)), RG-D8 (#1006, the clause-binding half), RH-D2 and H-D1 (#1002) and RG-D13 (#1030, new gold).
  - **The 1 disagreed:** RE2-D18.
  - **The 30 open** are the 30 `§4` IDs, which TeamNostra builds.
- **Against batch 8:** RE2-D17 moved from open to fixed, and RE2-D6, RE2-D10 and RE2-D20 from in progress to fixed.

**REVIEW ROUND 1** (the coordinator's independent review of `1e15ff4c`, "FIX FIRST", docs only). It re-checked the numbers: #1027's fail-first (24 fail at its parent, 36 pass at head), row 60's 142, 30, 5 and 1 of 178, row 64 (a)'s two boundaries, and row 41's WERN correction. It found four, all fixed in one docs commit:
1. **Medium:** row 64 (b) and this record did not name #1080, lane 3's open PR that fixes #1069's vintage, which opened after `1e15ff4c`. Both now name it, with the merge order. This batch's row-35 edit stays one clause of its own, so #1080 can keep both edits when it merges main.
2. **Low:** E2-D11's Pages cell lacked the "not re-measured" caveat this record claimed for it. It now has it, with the "figure skipped" counts on the rebuilt pages (EPAM 4, SMPL 8, TJX 1, VITL 2 at main `c58d5b2f`), marked as not #962's count, because FUBO's pre-#962 page carries 2.
3. **Low:** RA-D4's Pages cell still read "none rebuilt". It now names SMPL's rebuilt bridge (above).
4. **Nit:** row 64 (a) and this record named the field `valuation_basis.date_semantics.analysis_as_of`. The page's field is the top-level `date_semantics.analysis_as_of`, which WERN's `dossier.json` confirms.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **RE2-D17's named test fails at its parent only on a missing field,** never reaching an assertion. The row names two siblings that fail there on behaviour, so the claim does not rest on the attribute error.
- **RE2-D20's residual stays as #1027's record left it.** Verra Mobility's Q3 2025 basis-clause header is on no committed page, and the flag still marks it. The falsifier: a committed page whose `next-fy` guide is one of #1027's 21 after its re-assembly.
- **#962's note counts in the RE2-D6 and E2-D11 cells are #1028's,** at their pages' next build. They are not re-measured on the 9 pages rebuilt since, so those cells say so (E2-D11's since review round 1). A first filter tried here ("figure skipped" in a release flag) also caught FUBO, built before #962, so it is not #962's note, and no count from it is written.
- **§5.0 is now at 60 of its 60 lines.** The next build that opens a row must close one or fold it, as rows 32 and 64 do.
- **Row 64's two items share a row.** When one closes, that build restates the row to the other. The owner and the unlock cell name both items.

**FOUND, NOT FIXED.**
- **Other Pages cells may be stale.** Fix-log rows whose fix lands "at re-assembly" or "at the next build" were not re-measured against the 9 pages rebuilt on 2026-11-14 and 2026-11-15, outside the eight rows this batch edits. A Pages-cell sweep against those 9 pages is a candidate follow-up for the coordinator.
- **TGT's committed page holds one `next-fy` guide** (8-K `0000027419-26-000012`, adjusted EPS). It is not among #1027's 21. This batch did not measure whether it is a defaulted period.
- **The shared venv has no `pytest-xdist`.** #1065 added it to `requirements.lock` on 2026-11-14 (3.8.0, `-n auto` in CI's gate), after the operator's re-sync of 2026-11-13. So `pytest -n auto` is refused locally ("unrecognized arguments: -n"), and this batch's full suite ran serially. `pip check` is still clean, because nothing installed requires it. Row 62's anthropic claim stands; the venv simply no longer matches the whole lock. Agents may not reinstall it, so this is the operator's, at the next re-sync.
- **Batch 8's merged title** reads "of 148 asked: 139 fixed, 1 open, 7 in progress, 1 disagreed". Its record and row 60 read 138, 1, 8 and 1, after RG-D3 moved to in progress in review. The title is git history and cannot be changed. This record and row 60 carry the right figures.
