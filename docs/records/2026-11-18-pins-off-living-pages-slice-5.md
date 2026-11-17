---
id:
status: shipped
date: 2026-11-18
prs: [1111]
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 5 OF 5 (W27 follow-up, STATE row 41 (a) CLOSED): the propose, template, trigger and recipe pins read the cut or walk the roster; the scan's false positives are fixed and three blind spots added; a ratchet holds the 68 (test, page) pairs that remain, each with its reason; retiring AMZN with the whole suite touches 0 test files, from 31 at the cut ($0)

**WHAT.**
- **Slice 5 of the plan A approved on 2026-11-17**, the last (slice 1:
  `docs/records/2026-11-17-pins-off-living-pages-slice-1.md`; slices 2–4 merged as #1106, #1107
  and #1108). It reads through slice 1's cut (`tests/fixtures/frozen_pages/cut-4889ddba/`) and
  `tests/frozen_support.py`, and adds no fixture. 24 files: 19 test files, the shared
  `tests/frozen_support.py`, the two scripts, the checker's pins and a new `test_named_page_pins`.
- **To the cut.** Each of these reads a page by name as a host, a value or a page's own shape:
  - `test_propose` (SMPL, BRBR), with its 18 dead skip marks of the form "no committed <T> page"
    removed: a frozen copy always exists;
  - `test_r4_template` and `test_r3_template` (`_page`), `test_r4_machine_proposal` (`_with_count`
    → `_frozen_page`), `test_r4_forward_ev_ebit`, `test_rebuild_keeps_committed_recipe`
    (`_carrier`), `test_r4_card` (AMZN), `test_operator_decision` (`_carrier`, and its web twin's
    AMZN host, whose mirror is the cut's page byte for byte);
  - `test_prespend` (`_mech`), `test_vote_rule` (LLY), `test_vote_rule_confirmation` (GOOGL, TECX),
    `test_freshness` (TJX), `test_leg_fiscal_year` (EPAM), `test_guidance_vintage` (SMPL);
  - **the regrowth** (A's list, 2026-11-17): `test_recipe_3a`'s and `test_recipe_3b`'s page-only
    pins (GOOGL, AMZN, and `test_recipe_3a`'s five parametrized R1 pages), and
    `test_analysis_as_of_financials_filed`'s `_unfiled("IT")` (#1097), whose cut copy carries both
    Financials rows and no `filed_through`, as its pins need.
- **To the roster.** Each states an invariant every page with a property must meet, so it walks all
  of them through `covered_where`, which fails loud on an empty population. Each was run on every
  page in its population before it moved, and none failed:
  - an adjustment stated clears its refusal, and matching the anchor needs nothing: SMPL's living
    page → the 20 pages proposing base revenue, margin and multiple anchors;
  - the margin anchor is compared in schema units: SMPL → the 21 with a margin anchor;
  - only guidance carries a vintage mark: the walk had no floor (`covered_pages()`, kept non-empty
    by a frozen SMPL entry) and now has one, over the 26 pages carrying a primary source;
  - every no-variant option passes whatever the gap: the 3-ticker parametrize became one walk of
    all 26 (88 → 80 collected in `test_edge_basis_gate`), and the loop that had no floor has one.
  The two `test_propose` walks keep their frozen 2026-08-18 SMPL case beside the walk.
- **The record class stays named, by A's option (1).** A page read beside that name's LIVING
  record is left on its living page: a frozen page beside a newer record would mix two vintages.
  #1096's SMPL record read (`test_trigger_state_surface`, 9 functions) is this class, by A's
  ruling. So are `test_measured_triggers`' three `scenario-criterion SMPL` runs, the GOOGL stamp
  beside GOOGL's record in `test_recipe_3a` (5) and `test_recipe_3b` (9), the IT, NCNO and WERN
  supersedes in `test_recipe_3b` (4), `test_r3_template`'s create, `test_leg_fiscal_year`'s SMPL
  leg, and the residue slices 2–4 named.
- **The scan, `scripts/named_page_pins.py`, sees what it missed and drops what it miscounted.**
  - **Not reads, now:** a path rooted in a pytest tmp directory, or in a name the same function
    assigns from one, or in a helper's parameter that every call site hands one
    (`_copy("UBER", tmp_path)`); a git object path at another revision than `HEAD`
    (`f"{rev}:data/dossiers/NFLX/…"`); a docstring; and a name another function binds (bindings,
    tmp ones included, are read per function first: the code review found a tmp name leaking
    across functions). A literal ticker keys a subscript only of a name the
    function filled from page reads (`got`, not `cut`). Each was a false positive of slices 1–4.
  - **Reads, now:** a page's web mirror (`frontend/dossiers/<T>.json` / `.md`); a node driver's
    `dossiers/${t}` over the tickers its string quotes (#1107's EV/EBITDA twin); and a `tests/`
    support helper whose parameter reaches a page path, wherever it is called (`living_doc(T)`,
    `ciq_export_support.page_export_sha(T)`; slice 2's review). Each was a blind spot.
  - **`--worktree`** scans the working tree, and a module with no `dossiers` text and no call to
    such a helper is skipped, which is exact: no rule can find a pair in it (127 → 10 s).
  - `tests/test_named_page_pins.py` pins each rule with a positive and a negative, on tickers
    that are no page.
- **The ratchet** (`test_no_test_reads_a_living_page_by_name_unless_it_is_named`). It scans the
  working tree and fails on any (test, page) pair `RESIDUE` does not name, and on a named pair the
  scan no longer finds while its page is living: the ratchet only shrinks. A named pair for a
  name with no living page is never stale, so a retirement edits nothing there either (pinned).
  `RESIDUE` is seeded with the 68 pairs left, each with its reason (69 before #1109 merged, below):

  | reason | pairs | functions |
  |---|---|---|
  | record class: the page beside its living record | 46 | 43 |
  | watches the living page by design (FUBO's live sentence; NFLX's and PARR's tripwires) | 3 | 3 |
  | scan false positive: a scratch checkout or tree (`test_gate_on_workers` ×7, `test_impact_run` ×1) | 8 | 8 |
  | scan false positive: a path handed to a classifier (`test_impact_run`, `test_review_process`) | 2 | 2 |
  | scan false positive: pages at a past commit (`test_tracked_files_hold_no_transcript_run`) | 3 | 1 |
  | scan false positive: the helper reads the cut, or refuses first (`test_ciq_export_support` ×5, GOOGL's `_committed`) | 6 | 6 |

- **The checker** (`scripts/asserts_unchanged.py`) follows a skip into a helper to any depth and
  compares skips by WHAT they call and UNDER WHAT conditions, never by count (A's reviews of #1106,
  item 2, and #1107, item 5; the guard, from the code review). It knows an imported support
  helper that skips by what its module defines, not only by the `skip_unless` prefix
  (`retired_checkout`, code review). Over slices 2–4 as merged, each against its parent on main
  (`6419313d`, `8b0e5e4f`, `6110795d`), it reads 1, 3 and 2 disabled, each a named cost there.
- **`living_doc`'s contract names the residue:** it is for a name a roster walk handed back, or a
  test `RESIDUE` names (code review: `test_r3_template` called it with a fixed ticker, against its
  docstring).
- **`tests/frozen_support.py`'s index** greps `frozen_page("T")` and `cut-4889ddba/T` too, so the
  reads that name the cut by path are found (slice 4, cost 4).

**ROUND 1 (A's review of #1111, seven items; one commit, `afa5cb12`, each FIX failing first).**
- **Living reads through a helper whose root DEFAULTS to the living folder**, which the scan could
  not see, move to the cut. `test_guidance_vintage`'s `_digest("SMPL")` read the living page
  beside the cut copy its own assertions read just above, two vintages; it now passes the cut.
  `test_net_sales_is_revenue`'s two BRBR pins read `_releases("BRBR", CUT)`.
  `test_net_debt_as_of`'s two NCNO pins read `_page("NCNO", CUT)`. Its two walk floors named
  LLY and NCNO (`{"LLY", "NCNO"} <= set(compared)`, `"NCNO" in compared`), so an NCNO replay
  failed 4 tests. The floors are now name-free (≥ 20, ≥ 10), and LLY's and NCNO's cut copies are
  checked beside each walk with the same assertions. Each cut value matched; none was re-pinned.
- **`test_guidance_vintage`'s 4 removed skip marks**, each
  `@pytest.mark.skipif(not (DOSS / "SMPL").is_dir(), …)`, are gone with the living reads they
  guarded (this slice's earlier commits).
- **The R4 corpus floor no longer depends on AMZN's living page** (A: "AMZN's count to 0: YES").
  `test_r3_template`'s corpus check walks AMZN's page as frozen at the cut beside the living
  pages, as the `test_propose` walks carry SMPL's. AMZN is the only covered R4 page whose template
  builds. `test_the_r4_shape_is_exercised_with_no_living_r4_page` runs the check on a checkout
  whose living pages hold no AMZN. On the round-0 test it fails as the first replay did, with
  "the corpus check ran over {'r1': 14, 'r4': 0} — it is not exercising both shapes"; it passes
  now. This record first misquoted that message as naming the floor's counts.
- **A call landed since the cut skips its page, naming both sets: the CIQ rule.**
  `test_vote_rule_confirmation`'s transcript pin pairs each page as frozen at the cut with the
  folder on disk. `page_transcripts` refuses a folder whose calls are not the page's recorded
  ones. Before comparing, the pin now checks the page's recorded calls against the folder's, by
  `page_transcripts`' own condition. A page that differs goes on the pin's skip list, as an
  unreadable call already did. The test stays on the cut, not living residue: its subject is
  that two readers read one page, which the cut serves. On a living page the same new call raises
  the same error until the page is rebuilt. `test_a_call_landed_since_the_page_skips_it_naming_both_sets`
  stages GOOGL's real folder, linked in, plus one call its page does not record. On the round-0
  pin it fails with `ConfirmationError`; it passes now.
- **The scan sees four more forms of read:** a parameter whose DEFAULT is the living folder
  (`def _page(t, root=DOSS)`), counted unless the call hands another root by position or keyword;
  a ticker bound in the function itself (`t = "AMZN"`); tuple assignment
  (`DOSS, X = Path("data/dossiers"), …`); and `Path(a, b, …)`, `joinpath` and `os.path.join`.
  Each is pinned, and each pin failed on the round-0 scanner, which read none of them. With them, the ratchet failed on exactly the five reads A named and found
  no other.
- **What the scan still cannot see** is listed, one example each, in the ratchet's failure message
  (`BLIND`) and the scanner's docstring: a ticker in a module constant; a loop or parametrize over
  a module constant; a fixture that reads a page; `+` / `.format`; JavaScript concatenation; class
  and `async` tests; a support helper that reads a fixed ticker; a keyword ticker; and a module
  outside `tests/`.
- **The checker reads three more ways to skip:** a skip mark on one `pytest.param` case; a fixture
  that skips, taken as a parameter or by `usefixtures`; and a module-level `pytestmark` skip or
  `importorskip`, on the row `<module>`. Each is pinned failing first. A mark removed from a case is
  not DISABLED. Its docstring now says what it follows and what it does not: a lambda or alias, a
  `conftest.py` fixture, and a skip's arguments. This record's "follows a skip to any depth" now
  means within the module and the `tests` support modules it imports.
- **`RESIDUE` is pinned.** Its count, `RESIDUE_PAIRS = 68`, is checked, so growing it fails and
  shrinking it means updating the number. Each reason must be one of the six constants. An entry
  for a name the roster lists as retired WARNS rather than fails: a retirement must edit no test,
  this one included, and the warning names the entry for the next change to delete.

**WHY.** A retirement re-pointed every test reading the retired name's living page by name
(STATE row 41 (a)): at `4889ddba` an AMZN retirement replayed with the whole suite touched 31 test
files net of named noise. This slice ends the series and leaves a machine check in place of the
plan.

**HOW VERIFIED.**
- **The checker.** `python scripts/asserts_unchanged.py origin/main` (main `a49ffde9`, #1109 and
  #1110 merged) over 24 test files and 511 functions: 0 disabled, 0 vanished; 1 reader-only
  (`test_freshness`: `_assembled("TJX")` → `_frozen_assembled("TJX")`); 6 population (the walks
  above, and two `test_propose` loops whose iterable's reader moved to the cut); 35 new (helpers
  and the new pins); and 3 rows, each by A's own ask in round 1:
  - 2 changed: `test_net_debt_as_of`'s two floors, made name-free with LLY's and NCNO's cut copies
    checked beside the walks;
  - 1 control: `test_vote_rule_confirmation`'s new `continue` for a page whose calls drifted.
  Before round 1 it read 0 changed and 0 control, over 22 files.
- **The files.** Each part's files, offline, with the CIQ link present, against main `6110795d`
  on the same machine, read the same failure set at head and at main: propose and recipes, 112
  tests, 111 passed, 1 skipped, 0 failed; templates and proposals, 196 passed, 0 failed; gates and
  triggers, 366 of 367 passed and 0 failed at head, 374 of 375 at main (`test_edge_basis_gate`'s
  parametrize became a walk).
  At the merged head (main `b2102256`), the 21 changed test files together: 677 tests, 675 passed,
  2 skipped, 0 failed; main, 667, 665 passed, 2 skipped, 0 failed (18 new pins, less the 8 cases
  made one walk).
- **The scan's rules, failing first.** Each rule's fixture run through main's scanner reads wrong:
  it counts the tmp tree, the tmp helper, the git object path, the other function's binding and
  the frozen map's key, and misses the web mirror. The new scanner reads each right.
- **The ratchet, failing first.** A test file reading `data/dossiers/AMZN/dossier.json` by name,
  added to the tree, turns it red, naming the test and AMZN; removed, it is green.
- **The scan series** (pairs / functions / files; main's scanner → this one; the same 26 pages):

  | at | main's scanner | this scanner | AMZN, this scanner |
  |---|---|---|---|
  | the cut, `4889ddba` | 450 / 385 / 98 | 467 / 400 / 99 | 70 pairs in 25 files |
  | slices 1–4 merged, `6110795d` | 224 / 200 / 44 | 189 / 168 / 29 | 24 in 6 |
  | this slice, `2b442c8a` | 111 / 101 / 35 | 69 / 63 / 16 | 7 in 1 (`test_gate_on_workers`, scratch) |
  | this slice with #1109 merged (`b2102256`) | | 68 / 62 / 16 | 7 in 1 |

  At the cut this scanner reads 17 more, net: the mirrors, the driver templates and the support
  helpers it now sees, less the false positives it now drops. After the moves it reads fewer. Every pair it finds at this slice is in
  `RESIDUE`.
- **The regrowth** (A, 2026-11-17: named here). By main's scanner, 35 pairs in 30 functions and 6
  files are at `6110795d` and not at `4889ddba`: named living reads that landed after the cut
  while slices 1–4 moved the others. `test_recipe_3b` 16 and `test_recipe_3a` 15, the two recipe
  PRs; `test_analysis_as_of_financials_filed` 1 (`_unfiled("IT")`, #1097); `test_propose` 1;
  `test_trigger_state_surface` 1 (#1096's SMPL record read); and `test_gate_on_workers` 1, a
  scratch-checkout false positive. This slice moves the page-only ones and names the record class.
  The ratchet is what keeps the next one from landing silently.
- **The replay, the series' end count: 0 files, from 31 at the cut.** AMZN retired the roster's way,
  as slice 1 did: 1 appended roster line, its 2 page files, its 2 web mirrors and `index.json`, 6
  files. The scratch worktree is of `afa5cb12`, this round's code commit; the head adds only this
  record and STATE.md's line. The whole offline suite (`-m "not network" -n 8`, the CIQ link
  present) ran in it and in an unretired worktree of the same commit, on 2026-11-18. A test counts
  only if the unretired run passed it.
  - **Unretired:** 12,805 tests: 12,642 passed, 54 failed, 109 skipped (15.6 min).
  - **Retired:** 12,767 tests: 12,606 passed, 54 failed, 107 skipped (14.6 min).
  - **No test passes unretired and fails or skips retired: 0 files.** None of slice 1's named noise
    appeared either.
  - **38 tests are collected only unretired.** Each is an AMZN case of a corpus parametrization,
    passing there, and leaves with the page.
  - **2 tests skipped unretired and pass retired:** `test_run_visibility` and `test_sleeves`.
    Neither reads a page: a skip of the environment, not of a page.
  - **The same 54 tests fail in both runs, and no failing test id names AMZN.** They are local-data
    failures that CI does not run: the mislabelled PARR quarterly export, re-exported CIQ workbooks
    and the private evidence store. Several are corpus-wide checks failing on another name, so an
    AMZN case inside one would be masked. Here they are, so that one is visible (A's review of
    #1111):
    - `test_capital_panel_selection` (8): `test_a_genuine_newer_quarterly_panel_is_selected_when_both_are_valid`; `test_a_later_filed_quarterly_note_does_not_win_because_recency_is_not_provenance`; `test_a_printed_term_loan_step_compares_two_like_windows`; `test_the_legacy_debt_line_is_dated_and_tracks_the_picked_panel`; `test_the_selected_details_panel_is_stamped_with_its_own_provenance`; `test_the_selected_stamp_keeps_a_real_termination_inside_its_window`; `test_the_two_sheets_are_read_at_their_own_correct_frequencies`; `test_two_equally_valid_panels_keep_annual`
    - `test_ciq_bridge_unit_step` (1): `test_bc_d10_no_committed_pages_export_is_one_unit_step_from_its_own_rows`
    - `test_ciq_one_export_per_kind` (1): `test_every_live_folder_builds_and_picks_what_it_picked_before`
    - `test_ciq_units_and_headers` (1): `test_ra_d9_no_committed_pages_export_states_another_unit`
    - `test_credit_health_panels` (1): `test_every_real_standalone_export_yields_a_panel`
    - `test_driver_evidence` (1): `test_every_committed_rows_locator_finds_its_passage_on_disk`
    - `test_driver_facts` (2): `test_every_committed_figure_with_a_change_refuses_the_opposite_claim`; `test_every_committed_rows_figures_are_its_quotes`
    - `test_estimate_year_derivation` (1): `test_the_real_workbooks_derive_their_own_years[V-want3]`
    - `test_ev_bridge` (1): `test_claims_equal_ciqs_current_figure_on_every_committed_name`
    - `test_fiscal_year_change_marker` (1): `test_every_undated_header_cell_on_file_is_a_registered_marker`
    - `test_forward_consensus` (4): `test_every_spread_sits_on_its_own_trends_figure[GOOGL]`; `test_every_spread_sits_on_its_own_trends_figure[LLY]`; `test_every_spread_sits_on_its_own_trends_figure[PARR]`; `test_revision_counts_are_bounded_by_their_own_block[PARR]`
    - `test_forward_layers_basis` (4): `test_every_reconciliation_is_the_layers_own_means_and_present_when_it_can_be[PARR]`; `test_every_settled_column_is_a_quarter_end_and_the_latest_is_judged_by_its_date[PARR]`; `test_the_ladder_string_is_the_structured_cells_rendered[PARR]`; `test_the_ntm_cells_are_the_sheets_own[PARR]`
    - `test_forward_multiple_history` (3): `test_every_band_is_the_trailing_bands_own_stat_or_is_named_withheld[PARR]`; `test_every_point_is_its_own_rows_close_cell[PARR]`; `test_nm_and_no_data_stay_different_states`
    - `test_guidance_metric_coverage` (2): `test_a_block_the_former_list_never_named_is_read[PARR-Maintenance Capital Expenditure]`; `test_discovery_reads_every_guide_the_former_lists_read[PARR]`
    - `test_historical_forecast_error` (2): `test_each_line_carries_only_its_meaningful_measures_and_the_identity_holds[PARR]`; `test_every_observation_is_its_fiscal_year_cells_and_agrees_with_ciqs_difference[PARR]`
    - `test_horizon_read_block_bounds` (2): `test_every_line_is_its_own_blocks_counts[PARR]`; `test_the_fix_moves_only_metrics_whose_block_ended_in_the_wrong_place[PARR]`
    - `test_latest_cell_contract` (3): `test_corpus_markers_are_said_where_they_used_to_step_back`; `test_no_reader_serves_a_period_older_than_its_sheets_latest_column`; `test_the_bridge_never_pairs_a_period_older_than_the_latest_column`
    - `test_latest_col_provenance` (5): `test_a_press_release_basis_is_visible_in_the_stamp`; `test_key_ratios_never_mixes_two_periods_in_one_line`; `test_key_ratios_reads_one_named_column_and_attributes_what_is_missing`; `test_the_ascending_convention_holds_on_every_committed_bundle`; `test_the_book_value_stamp_names_its_period_and_never_says_latest`
    - `test_lease_basis` (1): `test_before_842_the_rebuild_reproduces_ciqs_own_multiple`
    - `test_liquidity_line` (1): `test_the_two_builders_agree_on_the_real_workbooks`
    - `test_model_input_checks` (1): `test_every_committed_transcript_row_passes_and_a_rescaled_one_does_not`
    - `test_multiples_vintage` (2): `test_no_band_outlives_the_close_it_reports`; `test_the_value_and_its_as_of_resolve_the_same_close`
    - `test_rtf_relationship_columns` (1): `test_no_committed_name_renders_a_company_in_the_relationship_slot`
    - `test_segment_absence_and_relationship_route` (3): `test_no_bundle_renders_our_own_parse_error_as_its_customer_field`; `test_no_committed_bundle_still_asserts_sheet_shape`; `test_the_customers_export_is_chosen_by_name_not_by_file_order`
    - `test_tracked_files_hold_no_transcript_run` (1): `test_no_tracked_file_shares_13_consecutive_words_with_a_call`
    - `test_transcript_run_guard` (1): `test_no_committed_synthesis_copies_more_than_12_words_of_its_calls[PARR]`
  - **The first replay** (`2b442c8a`, 2026-11-17, before #1109, #1110 and this round) touched 1
    file: `test_r3_template`'s R4 corpus floor, which round 1 walks on AMZN's frozen page too.
  - **The ratchet passes in the retired tree.** AMZN's 7 named pairs are false positives, and with
    no living AMZN page none reads as stale.
- **The impact check.** `python -m vinci.impact run --base origin/main --head HEAD` at
  `afa5cb12` (main `a49ffde9` merged): 0 of 709 tests fail on base code and pass on head code
  (703 pass at both, 6 skipped), and `verify` reads VALID. Before round 1 it read 0 of 677. The PR
  body carries the report.

**BOUNDARY.**
- **Counts:** at this slice's commit, against main `6110795d` (slices 1–4 merged) or, where named,
  `b2102256` (#1109 merged too).
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`, a lower bound, over
  `tests/**/*.py` less `tests/fixtures/`; "main's scanner" is its version at `6110795d`.
- **"Pages":** the roster's 26 covered names.
- **The replay:** `-m "not network" -n 8`, the CIQ link present, the whole suite both ways, at
  `afa5cb12` on 2026-11-18 (the first, at `2b442c8a` on 2026-11-17).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A residue name's retirement still reaches its record-class and living-by-design tests.** By
   the scan, retiring SMPL reaches 17 named functions in 5 files, GOOGL 16 in 4 and IT 8 in 3;
   BRBR 2, and EPAM, FUBO, NCNO, NFLX, PARR and WERN 1 each; AMZN none. Only AMZN's retirement is
   replayed here, so these are the scan's counts, a lower bound. Under A's option (1) each
   stays, named in `RESIDUE`. Falsifier: a residue test that reads only a page,
   with no living record beside it.
2. **The scan is a lower bound, so the ratchet is too.** A read it cannot see passes the ratchet:
   a ticker built at run time; a page reached through a module outside `tests/` (as
   `frontend/build.py`'s `_next_evidence` reads `DOSS/<T>` for `test_r4_card`; with AMZN retired it
   reads nothing, and all 9 tests pass); a test method in a class, or an `async` test; a support
   helper that reads a fixed ticker; a ticker passed by keyword (the last three from the code
   review: none occurs today, and each is stated in the scanner's docstring). The whole-suite replay is the proof, per name. Falsifier:
   a retirement replay touches a file the scan named nothing in.
3. **`test_recipe_3a`'s five living R1 pages read the cut** (SMPL, BRBR, EPAM, IT, VRRM). As a walk
   over every page with an R1 band it fails by design (AMZN's and GOOGL's recipes propose another
   multiple, and the template step refuses five others), and its docstring defines its five pages
   as measured at `4889ddba`, which is the cut. A re-assembly of one of them no longer reaches it.
   Falsifier: one of the five proposes its band's median on its living page and no test goes red.
4. **A population the checker cannot see.** `test_r4_machine_proposal`'s whole-fleet selection pin
   iterates the cut's pages in a list comprehension, and `test_r3_template`'s corpus check appends
   AMZN's frozen page to the list it walks (round 1). The checker reads only `for` statements round
   an assert, so it lists no POPULATION row for either. Falsifier: a moved pin's population changes inside a
   comprehension and no record names it.
5. **#1109 and this slice both describe `test_dossier`.** #1109 (the dormant pending tests, on
   frozen records) merged first, as `b2102256`. Merged here, the ratchet failed on the one named
   pair it moved, `test_one_8k_explaining_two_gap_downs_renders_once_e2e` / SMPL, and found no new
   one. The entry is deleted, and `RESIDUE` now names 9 `test_dossier` pairs. A later PR that
   moves one reconciles the same way. Falsifier: a PR merges green with a stale entry.
6. **The checker compares a skip by its callee and its guard, never its arguments**, so a reason
   reworded is not a new skip. The cost (code review): `pytest.importorskip("json")` changed to
   a module that is missing always skips and reads unchanged. Falsifier: a moved test gains a
   skip that way and no record names it.
7. **The ratchet scans every test file on each run**, about 8 s of CPU.
8. **The R4 corpus check exercises its R4 case on AMZN's frozen page** (round 1). A re-assembly of
   AMZN that breaks the R4 template's shape still reaches it through the living walk while AMZN is
   covered. Once AMZN retires, only the frozen copy carries the case, and the same change to the
   code is still caught there. Falsifier: the R4 template's shape changes and the check stays
   green on a corpus whose only R4 page is the frozen one.
9. **The replay is one name's.** It proves AMZN's retirement edits no test; a residue name's
   (cost 1) is counted by the scan, not replayed. Falsifier: an SMPL, GOOGL or IT replay touches
   a file `RESIDUE` does not name.
10. **$0.** No model call, no vendor call, and no page rebuilt or re-rendered.
