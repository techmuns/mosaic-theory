---
id:
status: shipped
date: 2026-11-17
prs: [1109]
supersedes:
superseded-by:
---

# 14 `test_dossier` render tests dormant since 2026-09-02 run again: 13 of the 14 run on every CI run, and so does the 15th; each one revived turns red on a breakage of what it checks; BRBR's admin-only 8-K pin stays dormant and is reported ($0)

**WHAT.**
- **The hole.** Found by the pins-off-living-pages series and named in slice 4's record
  (`docs/records/2026-11-17-pins-off-living-pages-slice-4.md`, PR #1108). #407 (2026-08-11)
  replaced one hardcoded undecided name, EPAM, with a run-time pick: the first page whose
  `scenarios/<T>.json` was `pending_analyst`. The same seven lines then went into 14 other tests
  of `tests/test_dossier.py`, and none of them reads the pick. Their only use of it was
  `if pend is None: pytest.skip(...)`, so each one skipped whenever no record was pending.
- **When it bit.** The tests ran while SMPL's record was pending (2026-08-11 → 08-20, #479) and
  while GOOGL's was (2026-09-01 → 09-02, #557 → #567). None has been pending since. On main
  `e15659ba`, all 15 skip.
- **The 15, and what each was meant to check.** "Web half" means the part that renders the page
  through `frontend/views/shared/dossier.js` under node. "Whole" means the test asserted nothing
  before the pick.

  | test | page read | what it checks | dormant part |
  |---|---|---|---|
  | `test_return_ratios_exhibit_no_phantom_negative_tick_e2e` | IT | an all-positive return-ratio exhibit draws no negative % tick | whole |
  | `test_dossier_page_logs_anchor_and_scenario_panels` | IT | the screening panel renders, says "not a verdict", and is absent with no anchor; the underwrite band renders only with a record | whole |
  | `test_opener_narrative_slot_rationale_once_and_conditional_warning_node` | IT + the pick | a logged name's rationale renders once, as the thesis, above About; a PENDING name renders one machine Assessment and no thesis; the warning strip fires only on a decision caveat | whole |
  | `test_buyside_cover_and_field_grids_e2e_node` | IT | the cover's crux renders once and matches the committed question; the basis tags and an UNKNOWN note are visible; the wall chips equal the instruments' sums; what-broke leads with its read | whole |
  | `test_what_broke_restructure_and_survival_columns_e2e_node` | IT | what-broke order and relocations; the street card's guidance fact renders once; the survival columns; the peer descriptor is prose | whole |
  | `test_one_8k_explaining_two_gap_downs_renders_once_e2e` | SMPL | one 8-K explaining two gap-downs renders once, naming both | web half (md half ran until 2026-11-05) |
  | `test_admin_only_gap_8k_card_suppressed_on_committed_brbr_e2e` | BRBR | an administrative-only 8-K gets the honest label and no card; the earnings card stays | web half |
  | `test_caveats_collapse_dejargon_and_acronyms_committed_brbr_e2e` | BRBR | md and web agree on the caveat count; no jargon leaks; the web rewords the catalyst caveat and collapses a repeated lead | web half |
  | `test_catalyst_calendar_js_twin_parity_node` | SMPL (+ injected rows) | the web calendar matches the md: after the argument, the row, the trigger, the crux's Next-catalyst line, the no-probabilities line | whole |
  | `test_positioning_lands_in_the_appendix_in_both_twins_e2e` | every page with insider activity | Ownership & positioning renders in the Appendix and never in the street | web half |
  | `test_analysis_tier_reads_in_decision_order_e2e` | every page; SMPL on the web | the Analysis tier renders in decision order in both twins | web half |
  | `test_assumption_methodology_renders_in_both_twins_e2e` | every page with a record | "How these numbers were set" renders in the Appendix with every axis's method and source | web half |
  | `test_each_own_history_panel_carries_its_own_as_of_e2e` | every page with a band | each own-history panel prints its own band's as_of, and the shared caption prints none | whole |
  | `test_two_panels_with_different_as_ofs_each_keep_their_own` | constructed | two panels whose as_ofs differ each keep their own (the P5 shape) | whole |
  | `test_a_band_with_no_as_of_says_undated_rather_than_going_silent` | constructed | a band with no as_of says "undated" | whole |

- **The change.** It is test-only. No production file, protected file, page or record changes.
  1. The dead seven-line block is deleted from the 14 tests that never read it. 12 pass at once.
  2. `test_one_8k_explaining_two_gap_downs_renders_once_e2e` also skipped first on its living page,
     since SMPL's page lost its shared-accession pair on 2026-11-05 (`3e97ee7d`). It now reads
     SMPL's page frozen at 2026-08-18. That copy already exists, already obeys the transcript and
     local-path rules, and carries the pair. Beside it the test reads SMPL's card as committed at
     `f2c6e7aa`, the commit that page was frozen from.
  3. `test_opener_narrative_slot_rationale_once_and_conditional_warning_node`, the one test that
     uses the pick, reads EPAM's page from `frozen_pages/cut-4889ddba/` beside EPAM's 2026-07-21
     record, `frontend/scenarios/EPAM-2026-07-21.json` cut byte for byte at the same commit. That
     record is `pending_analyst` with no rationale, and archived. It was superseded on the
     2026-08-07 reconciliation (#402) before any verdict was recorded on it.
  4. New fixture `tests/fixtures/frozen_cards/`: its `README.md` heads each copy with its source,
     commit, blob and pin. A new guard, `tests/test_frozen_cards_are_cuts.py`, holds every copy to
     `git show <sha>:frontend/scenarios/<file>`, the twin of `test_frozen_pages_are_cuts`. Both
     copies are existing git blobs (`eae3502c`, `6ed6d2be`), so 0 new objects.
  5. `tests/fixtures/frozen_pages/README.md`: the 2026-08-18 SMPL row names the new pin.

**WHY THE EXEMPLARS ARE THESE.**
- **No old page with the property can be committed.** The last committed pending exemplar is
  GOOGL's page and record at `afb94fcb` (2026-09-02). That page breaks the public-transcript rule
  192 times (`tests/test_public_transcript_text.violations`) and carries two absolute local paths
  in its price-store stamp. Every other old page checked breaks the rule too:
  - SMPL at `eac82b7f`, 69 times;
  - each of the 24 BRBR pages on main that carried an administrative-only gap 8-K
    (2026-07-23 → 08-12, `27913b9a` → `48bc8c89`), 24 to 38 times.

  A byte-for-byte cut of any of them would publish what the rule forbids, so none is used.
  SMPL's 2026-08-18 copy is a frozen page already put through both rewrites (`eac82b7f`,
  `91817458`), and it carries the pair.
- **Two committed records are still `pending_analyst` at `4889ddba`, both archived:** EPAM's
  2026-07-21 and GOOGL's 2026-08-17. GOOGL's card carries a `voided` block, attached by
  `frontend/build.py` since the 2026-11-11 void of GOOGL's BUY. That is a second state, which a
  pin about undecided records must not bring with it, so EPAM's card is used. EPAM is also the name
  the pin was written against, hardcoded until #407 decided EPAM's live record.
- **The page and the card are paired at one commit**, so a frozen page never sits beside a living
  record (slice 4's code-review finding on `test_catalyst_calendar_render_placement_b_and_crux_line`).
  The EPAM page in the cut was assembled after the 2026-07-21 record. The live site pairs a
  record with a newer page the same way, since records and pages run on separate clocks, and the
  pin reads only the card's verdict state.

**HOW VERIFIED.** Every run below is offline, at $0, in a worktree of main `e15659ba` with no CIQ
folder linked (as CI).
- **Before, on main:** the 15 tests skipped, 15 of 15. 13 named the pending pick; SMPL's and BRBR's
  skipped first on their living pages.
- **After:** 14 of the 15 run and pass: every test in the table above but
  `test_admin_only_gap_8k_card_suppressed_on_committed_brbr_e2e`. Each reaches its assertions; the
  breakage table below is the proof. BRBR's admin-only test skips, and its skip states why and
  names its unlock (WHAT REMAINS).
- **Skips.** Across the 15 functions, the `pytest.skip` calls fall 39 → 23, down 16: the 15 pending-pick skips and
  SMPL's "no committed SMPL dossier.json". The skips that fire on main today fall 15 → 1. The
  checker's DISABLED count reads 0, because it counts only skips that are added.
- **Fail first.** Each test that now runs was run green, then red on a deliberate breakage of the
  renderer code it guards, then green with the code restored. 14 of 14 turned red:

  | test | breakage | red on |
  |---|---|---|
  | return-ratios phantom tick | `exhibit.js` pads the line axis below 0 unconditionally | "phantom tick on all-positive ratios" |
  | anchor and scenario panels | `uw-card.js` stat band loses its class | "a passed scenario record must render the underwrite card" |
  | opener (pending exemplar) | a pending card's machine read is titled as a thesis | "a pending name carries the machine assessment once and never a thesis block" |
  | buy-side cover | the basis tags lose their visible class | `'<span class="fg-basis">NET</span>' in …` |
  | what-broke restructure | the peer descriptor renders as a numeric cell | `'class="peer-desc"' in …` |
  | one 8-K, two gap-downs | filings no longer grouped by accession | "the shared 8-K must render ONE filing card, got 2" |
  | BRBR caveats | the web no longer rewords the catalyst caveat | "web catalyst caveat must lead with the staleness discriminator" |
  | catalyst twin parity | the crux loses its Next-catalyst line | the parity dict differs |
  | positioning | the web section reverts to "Ownership & concentration" | "AMZN: web lost the Ownership & positioning section" |
  | analysis tier order | Business quality renders before What broke | "web analysis sections out of decision order" |
  | assumption methodology | a reference point loses its source | "BRBR: web rendered 2 of the record's 15 sources" |
  | own-history as_of | every panel prints a date not its band's | "AMZN: panel … does not carry ITS OWN band's as_of 2026-09-30" |
  | two panels | every panel prints the fresh band's date (P5) | "the STALE panel shows '10%ile · 12q · 2026-07-17'" |
  | band with no as_of | a dateless panel goes silent | "panel '10%ile · 12q' carries no date and does not say so" |

  The exemplar itself was checked too: pointed at EPAM's live, decided card, the opener test
  turns red on its pending assertion.
- **The guard, corpus first.** `test_frozen_cards_are_cuts` checks both committed copies, 2 of 2.
  Its negatives are made from real bytes:
  - a one-byte edit to the pending card's verdict status;
  - a card renamed to a name its commit never had;
  - a cut folder named for no commit;
  - a copy the README does not head, and a README row naming another source;
  - two README rows for one copy;
  - a headed cut whose commit is missing, which must not be called missing a copy.

  The last two were code review round 0's fixes (`fc497583`), each red on `d130bb23`'s guard.
  8 pass.
- **No assertion changes.** `python scripts/asserts_unchanged.py e15659ba tests/test_dossier.py
  tests/test_frozen_cards_are_cuts.py` reads changed 0, disabled 0, control 0 and vanished 0. The
  guard's 8 tests and 3 helpers are new.
- **The new frozen files obey the publishing rules.** `tests/test_no_local_paths.scan()` reads all
  three, the two cards and their README: 2,161 files are scanned, with 0 hits.
  `tests/test_public_transcript_text` reads pages only, never a card. Its quote rule, applied to
  every card field whose source names a call or a transcript, finds none, and neither card
  contains the word "transcript".
- **After slices 2–4 merged.** #1108 merged first, as A ordered, and main `6110795d`, holding slices
  2, 3 and 4, was merged into this branch (`811ebfea`) clean. The checks were then run again:
  - the 15 by name: 14 PASSED, 1 SKIPPED (BRBR's, with its stated reason);
  - the breakage table again: 14 of 14 red, then green once restored;
  - `asserts_unchanged.py 6110795d`: changed 0, disabled 0, control 0, vanished 0.
- **The full offline gate.** `bin/commit` runs ruff, `mypy --strict` over `vinci/`,
  `pytest -m "not network"` and the mirror check. It is green at `d130bb23`, `fc497583`, `00a3bb3b`
  and on this record's commit over the merged tree,
  with no CIQ folder linked, as in CI.
- **The impact check.** `python -m vinci.impact run --base origin/main --head HEAD` was run at
  `811ebfea`, against base `6110795d`, the merge base. It was first run at `f0cc9cc1` against
  `2f85a6f2`, with the same result. 0 of 374 tests fail on base code and pass on head code. That is expected for a test-only change: `vinci/` is byte-identical, so the
  fail-first evidence is the breakage table above. 363 pass at both, 11 skip, 0 fail at head.
  The 11 skips are:
  - the eight card-guard pins, which skip in the harness's exported tree by design;
  - BRBR's admin-only test;
  - two pins that need data CI lacks.

  `verify` reads VALID.
- **Code review round 0** (`/code-review high --fix`) gave 7 findings: 2 FIX in the card guard,
  and 5 DEFER or DISMISS. Each is listed in the PR's Review dispositions table.

**WHAT REMAINS.**
1. **BRBR's admin-only 8-K pin stays dormant. Owner: the operator.**
   - **What it needs.** `test_admin_only_gap_8k_card_suppressed_on_committed_brbr_e2e` needs a page
     carrying an administrative-only gap 8-K. 0 of the 106 committed pages, mirrors and fixture
     pages carry one.
   - **Why no page has one.** BRBR's left its page on 2026-08-13 (`513b2a95`). Each of the 24 BRBR
     pages on main that carried it (2026-07-23 → 08-12, `27913b9a` → `48bc8c89`) breaks the
     transcript rule 24 to 38 times.
   - **The unlock.** A compliant copy needs the operator's `vinci driver-facts-pass` on one of those
     pages. That pass files the words in the operator's private evidence store, so it is never the
     agent's to run. The copy then gets a cut and this pin reads it.
   - **What stands meanwhile.** The test's skip now states all of this.
     `test_admin_only_8k_is_non_explanatory_with_an_honest_label` pins the behaviour's deterministic
     half on every run. Its web half is pinned nowhere today.

**FOUND, NOT FIXED (out of scope; reported to A).**
1. **The 2026-08-18 SMPL row in `tests/fixtures/frozen_pages/README.md`** says the copy was rewritten
   for its store stamp "and nothing else". `git log` shows a second rewrite, the transcript page
   pass at `91817458` (2026-11-11). This PR's frozen-cards README states both; the old row is left
   as it was.
2. **GOOGL's archived 2026-08-17 card carries `voided`.** `frontend/build.py` attaches the void
   of GOOGL's BUY to the archived, undecided record. Whether an undecided record should show a
   void is not this PR's question.

**BOUNDARY.**
- **"15 tests" / "14 tests":** the functions of `tests/test_dossier.py` at `e15659ba` whose source
  names `pending_analyst` (an AST scan), and the 14 of them that never read `pend` beyond its skip.
- **"Skipped" / "pass":** the 15, run as `pytest tests/test_dossier.py -k <the 15>`, offline, with
  node 24, at `e15659ba` and at this PR's head.
- **The pending windows:** the commits on main at which some `scenarios/<T>.json` read
  `pending_analyst` (`git log -S`), from #407 on.
- **"Violations":** `tests/test_public_transcript_text.violations` over a page at the named commit.
- **"106 committed pages":** every JSON file with a `mechanical` key under `data/dossiers/`,
  `frontend/dossiers/` and `tests/fixtures/` at this branch's head, with main `6110795d` merged
  in (106 before that merge too). An administrative-only gap 8-K is a `drawdown_cause.filings` row with
  `explanatory: false`.
- **"24 BRBR pages":** every commit in `git log -- data/dossiers/BRBR/dossier.json` whose page
  carries such a row.
- **"Skip calls":** `pytest.skip(...)` calls inside the 15 functions (AST), at `e15659ba` and at head.
- **"0 new objects":** each copy's `git hash-object --no-filters` equals an existing blob.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The md halves read frozen renders.** `test_one_8k_explaining_two_gap_downs_renders_once_e2e`'s
   md half reads SMPL's committed 2026-08-18 md, so it pins that render rather than today's md
   renderer. Its web half renders through current code. Falsifier: an md regression on grouping
   by accession passes this pin. The md twin's grouping is not separately pinned at the render
   layer here.
2. **One more fixture class, and its own guard.** `frozen_cards/` sits beside `frozen_pages/`.
   Slice 1's guard does not fit it, for two reasons:
   - It holds a cut's file to `data/dossiers/<T>/<file>`, and a card is `frontend/scenarios/<key>.json`.
   - Its README rows need a page's `dossier.json` and `dossier.md` blobs as a pair, and a card is one
     file.

   Fitting the card there would change that guard's contract in a file the series owns. So the
   twin reuses its git helpers (`_git`, `_blob_of`, `_cut_files`, `needs_git`) and adds only the
   path and the README shape. Falsifier: a card is edited or added without a README row, and the
   guard stays green.
3. **$0.** No model call, no vendor call, and no page or record rebuilt, re-rendered or edited.
