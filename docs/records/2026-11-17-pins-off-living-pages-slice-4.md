---
id:
status: shipped
date: 2026-11-17
prs: [1108]
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 4 OF 5 (W27 follow-up, STATE row 41 (a)): 14 dossier-render and refresh test files and the shared `stripped_pages.committed_page` read the cut or walk the roster; five invariants now hold on every covered page with the property; seven assertions change, each for a stated reason; the scan's named-living-page pairs fall 423 → 358 (83 → 76 files); 14 render tests were found dormant since #407 and are reported, not fixed ($0)

**WHAT.**
- **Slice 4 of the plan A approved on 2026-11-17** (slice 1:
  `docs/records/2026-11-17-pins-off-living-pages-slice-1.md`). It reads through slice 1's cut
  (`tests/fixtures/frozen_pages/cut-4889ddba/`) and `tests/frozen_support.py`, and adds no fixture.
- **To the cut.** Each of these reads a page by name as a host, a value or a page's own shape:
  - `test_dossier`: 15 functions on SMPL, VRRM, CNXC, IT and BRBR (17 at round 0; two went to
    the roster, below). The 15 skips of the form "no committed <T> dossier" in those 17 are gone:
    a frozen copy always exists, and the two walks fail loud on an empty population instead. A skip
    removed, never one added.
  - `tests/stripped_pages.committed_page`, the shared host reader. **15 files this slice does not
    otherwise edit reach the cut through it** (the first count here said 11; A's review, round 1,
    found the other four). Four call it directly: `test_evals_independence`,
    `test_evals_run_builds` (NFLX), `test_evals_order8` (SMPL) and `test_evidence_same_passage`
    (GOOGL). Eight reach it through `replayable_text`: `test_evals_compare`, `test_evals_m_gap`,
    `test_evals_pr2`, `test_evals_pr2_round2`, `test_evals_pr926_round2`,
    `test_evals_replay_and_guard`, `test_evals_replication_rule` and `test_evals_round2`. Three
    reach it through `synthetic_page`: `test_driver_evidence`, `test_driver_facts` and
    `test_driver_facts_page_pass`. Each uses the page as a host for invented rows or a replay. Its
    corpus walk, `committed_pages()`, still reads the living pages.
  - `test_pages_await_parser_rebuild`: every landed pin reads the cut (`_PAGES = CUT`). A new
    awaiting pin watches a living page by design, so it reads `living_doc`.
  - `test_surprise_listing_block`: its two strict-xfail tripwires (NFLX, PARR) flip when the
    living page is re-read. They read the living page while the roster covers the name and skip
    once it does not. Every other pin reads the cut.
  - Host moves: `test_layer_refreshes` (UBER, SMPL, AMZN), `test_input_manifest` (NFLX, BURL),
    `test_analysis_as_of_skips_and_filings` (IT, NKE, through `_at_cut`, renamed from `_living`
    because it no longer reads one), `test_cohort_and_benchmark_cause_labels` (AMZN),
    `test_footnote_every_figure` (GOOGL), `test_material_figure_presence` (SMPL),
    `test_method_row` (UBER), `test_benchmark_figures_refresh` (GOOGL) and
    `test_refresh_fleet_and_bridge_guards` (`_folder`, and SMPL's zero-share bridge host).
- **To the roster.** Each states an invariant every page with a property must meet, so it walks all
  of them through `covered_where`, which fails loud on an empty population. Each was run on every
  page in its population before it moved, and none failed:
  - the Brief carries the underwrite layer: IT's page and record → every covered page with a live
    R1 record (5: BRBR, EPAM, IT, SMPL, WERN). The page and the record are both LIVING (A's
    option (1)), because a frozen page beside a living record mixes two vintages. It walks R1
    records only, since the scenario table it asserts is R1's: GOOGL's R3 record renders
    `| scenario | EPS | multiple |…` and failed the R1 header when the walk took every record;
  - the JSON keeps the inputs that reproduce the cap line: UBER → all 26 covered pages;
  - a fleet refresh rebuilds the web mirror: SMPL's mirror → every covered page's mirror (26),
    each written stale before the one refresh. Mutation: `mirror_to_frontend` stubbed to a no-op
    turns it red on AMZN, the first covered name, whose page the message names;
  - a page's stock_performance is structurally valid (both series rebased to 100, dates ascending
    and unique, the name's symbol its ticker, its return reconciling with its last point): CNXC →
    every covered page with one (26). CNXC's benchmark, IWM, is a value (9 covered pages use IWM,
    11 SPY and 6 MDY), so it stays a pin on CNXC's page as frozen at the cut;
  - the md Brief carries the crux inside 'At a glance', and 'The case' repeats neither the
    question nor an unknowns list: IT → every covered page asking a decisive question (26).

  The last two are LIVING invariants their own docstrings name as such. Round 0 moved them to the
  cut, where they could not fail (A's review, round 1). Mutation: living CNXC's first point set to
  99 and the crux heading cut from living IT's md. The round-0 version stays green on both, and
  this one goes red on each, naming CNXC and IT. Both pages were restored (`git checkout`).

**WHY.** A retirement re-points every test reading the retired name's living page by name (STATE
row 41 (a)). This slice moves that cost off the dossier render and refresh group, the plan's slice
4.

**HOW VERIFIED.**
- **The checker.** `python scripts/asserts_unchanged.py origin/main` (main `2f85a6f2`, merged) over
  15 files and 745 functions: 0 disabled, 0 control, 0 vanished, 1 reader-only
  (`test_an_export_not_on_disk_is_named_never_reported_unchanged`, `_living` → `_at_cut`), 1
  population (the R1 walk), and **7 changed, each reviewed** (5 at round 0, which the title first
  called four; A's review, round 1):
  1. and 2. `test_anchor_off_headline`'s two decision pins, md and web. The floor `decided >= 4`
     became `decided >= _decisions_at_the_cut_still_covered()`, a floor BY NAME: the set of names
     whose cut pages carry a recorded decision (AMZN, CNXC, GOOGL, UBER), on the names the roster
     still covers, must be a subset of the names whose living pages carry one. It is those 4
     today. A retirement lowers it by that name's own decision, never by a test edit; a decision
     a covered page loses goes red even when another page gains one, which a count would net
     (code review, round 0: mutation, AMZN's decision dropped from the md walk → red); and the
     floor itself fails loud once no covered name carried a decision at the cut (the second
     review: shown with the roster stubbed to two undecided names). The message names the lost
     decision.
  3. `test_layer_refreshes::test_a_refresh_that_moves_a_layer_records_it`. A reader swap through a
     path expression: `DOSS / "UBER"` → `frozen_page("UBER")`. The checker normalizes a reader only
     when it is a call, so it reads this as CHANGED. `_copy` writes the same frozen page into the
     tmp tree, so the assertion still compares the refreshed page with the page it came from.
  4. `test_refresh_fleet_and_bridge_guards::test_a_fleet_refresh_updates_the_frontend_mirror`.
     SMPL → each covered name `t`, in the walk above; the message names the page, and the walk
     fails loud on an empty roster. It keeps #1100's `watch_defects.json` copy (merged, not
     hand-edited).
  5. `test_cap_drift_render::test_the_committed_json_still_carries_the_inputs_to_reproduce_it`.
     UBER → the 26 covered pages; each message names its page, and a page with no `stock_info`
     block fails on a named assertion rather than a `TypeError` (the second review).
  6. `test_dossier::test_stock_performance_committed_cnxc_artifact_invariants`. CNXC → every
     covered page with a stock_performance, in the walk above. Each assertion names its page, and
     `name_symbol == ticker and benchmark == "IWM"` splits in two: the symbol holds on every page,
     and IWM is pinned on CNXC's page as frozen at the cut. The name still says CNXC, kept so the
     checker can pair it.
  7. `test_dossier::test_md_brief_crux_block_and_case_dedup`. IT → every covered page asking a
     decisive question, in the walk above; each assertion names its page.

  **"0 disabled" is this checker's count; slice 5's reads 2.** Slice 5's checker follows a skip
  into a helper, to any depth, and compares skips by what they call. It reads
  `test_surprise_listing_block`'s two tripwire pins (NFLX's and PARR's) as DISABLED. On main,
  retiring either name FAILED its pin loudly: the page read raised `FileNotFoundError`, which a
  strict xfail with `raises=AssertionError` does not absorb. Here `_committed` SKIPS it once the
  roster stops covering the name, quietly. That is by design, since a retired name's page awaits no
  re-read, and it is cost 3. A's review, round 1, reconciled the two counts.
- **The dormant test.** `test_return_ratios_exhibit_no_phantom_negative_tick_e2e` skips on main:
  no record is `pending_analyst`, so its move had never run. It was run once with WERN's record set
  to `pending_analyst` in the slice's worktree, and the record was then restored (`git checkout`):
  it passes on the frozen IT page.
- **The files.** The 14 changed test files, offline, with the CIQ link present, at the merged
  head: 642 passed, 17 skipped, 2 xfailed, 0 failed (round 0). At round 1 they were run with the
  15 files that reach the cut through `committed_page`: 1004 tests, 979 passed, 22 skipped or
  xfailed, and 3 failed, the same on main `2f85a6f2`. The 3 are `test_driver_facts` ×2 and
  `test_driver_evidence` ×1, whose corpus walk reads the living `committed_pages()`, not the cut.
- **The scan** (`python scripts/named_page_pins.py HEAD`, the same 26 pages, against main at
  `8a71a383`; main and this slice read the same at round 1, main `2f85a6f2`): 423 → 358 pairs (value 208 → 181, invariant 215 → 177), 366 → 311 functions, 83 →
  76 files. What it still finds in these files, 27 pairs in 24 functions:
  - **scan false positives, 18 pairs in 15 functions:** `tmp_path` trees built from a frozen copy.
    `test_benchmark_figures_refresh` (6, TECX from its 2026-09-28 copy), `test_input_manifest`
    (3, NFLX and BURL), `test_layer_refreshes` (2), `test_surprise_listing_block`'s writer pins
    (2, PARR) and `test_analysis_as_of_skips_and_filings` (2, IT and NKE);
  - **record-class residue, 9 pairs in 9 `test_dossier` functions:** each pairs a named page
    with that name's record. 8 read `frontend/scenarios/<T>.json` (IT ×4, SMPL ×2, BRBR ×2) and
    are dormant today (below). The ninth,
    `test_catalyst_calendar_render_placement_b_and_crux_line`, renders SMPL's page with SMPL's
    `scenarios/SMPL.json` record (`read_record`) and runs. It was moved to the cut and then put
    back on the living page (code review, round 0): a frozen page beside a living record mixes
    two vintages, and SMPL's retirement would archive the record it reads in any case. Under A's
    option (1) the 9 stay, with slice 5's record writing up the class.

  Slice 5 fixes the scan's false positives and records the residue.
- **The suite.** The full offline suite (`-m "not network" -n 8`, the CIQ folder linked) at
  `bca68679` (main `5c9c7eac` merged), against the same run of main `8a71a383`: **74 → 76
  failing**. Main's 74 are local-data failures CI does not run. Of the differences:
  - named noise: `test_records_ledger` (this record's PR number, filled once the PR opened);
    `test_transcript_run_guard`, 2 new and 1 gone; `test_evidence_same_passage`'s LibreOffice
    conversion, gone;
  - `test_forward_multiple_history::test_the_refresh_lands_the_layer_and_moves_nothing_else`, a
    file this slice does not touch: it fails on main `5c9c7eac` itself, with the CIQ link. #1100
    gave a watch page a frozen-since line, and this pin's tmp copy of AMZN has no roster, so the
    re-render drops AMZN's line. CI does not run it. Slice 3 (#1107) moves it to the cut, which
    predates the line. Reported to A.
- **The impact check.** `python -m vinci.impact run --base origin/main --head HEAD` at
  `9aa9db77` (round 1, main `2f85a6f2` merged): 0 of 661 tests fail on base code and pass on head
  code (641 pass at both, 20 skipped), and `verify` reads VALID. Round 0 at `34436f76` read the
  same. The PR body carries the report.

**FOUND, NOT FIXED (out of scope; reported to A).** 14 of the 15 `test_dossier` tests that name
`pending_analyst` compute a pending exemplar, `pend`, and never use it: their only use is
`if pend is None: pytest.skip(...)`. #407 (2026-08-11) replaced one hardcoded undecided name
(EPAM) with that exemplar, and the same block went into 14 other tests, each of which renders its
own named page. So those 14 render tests run only while some record happens to be
`pending_analyst`. No record is, so all 14 skip on main today. The fifteenth,
`test_opener_narrative_slot_rationale_once_and_conditional_warning_node`, uses `pend` and skips
for the right reason.

**BOUNDARY.**
- **Counts:** at this slice's commit, against main at `8a71a383` (slice 1 merged as #1098), unless
  another is named.
- **"Pages":** the roster's 26 covered names at the cut.
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`, a lower bound.
- **"Assertions":** the 15 changed `tests/*.py` files.

**WHAT REMAINS.**
- **Slice 5:** propose, templates and triggers; `test_recipe_3a`/`3b`; the scan's false positives;
  the ratchet; the AMZN replay; STATE row 41.
- **The 14 `test_dossier` render tests that run only while a record is `pending_analyst`**
  (FOUND, NOT FIXED, above). Owner: A, who has carded a follow-up (a frozen pending exemplar).
- **`test_forward_multiple_history`'s refresh pin, red on main with the CIQ link** (the suite,
  above). Owner: slice 3, #1107, whose round 1 copies the roster and `watch_defects.json` into the
  pin's scratch tree and adds a watch-page refresh walk.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A walk's floor fails loud** when the last covered page with its property leaves (A's ruling).
   The R1-record walk is the nearest case: 5 names. Falsifier: a walk passes on an empty
   population.
2. **The decision floor is the cut's names, not a constant.** A decision recorded after the cut
   raises nothing until the page is cut anew; the floor fails loud once none of the cut's names
   is covered. Falsifier: a covered page at the cut loses its decision and the pin stays green.
3. **The tripwires still read living pages, and a retirement skips them quietly.** NFLX's and
   PARR's strict xfails watch for the living page's re-read, so they still name it, behind a
   roster skip. On main a retirement failed them loudly (the checker, above). Falsifier: a covered
   name's tripwire skips.
4. **Nineteen moved reads, in 15 `test_dossier` functions, name the cut by path**
   (`tests/fixtures/frozen_pages/cut-4889ddba/<T>/`, two of them inside JS driver strings), not
   through `frozen_page(T)`. At round 0 they were 22 in 17 functions, which this record first
   called seventeen reads. The `grep 'frozen_doc("T")'` that `tests/frozen_support.py` names as
   the index misses them. They are found by `grep 'cut-4889ddba/T'`. Slice 5 widens the index's
   grep.
5. **Data-only value pins now read a page that cannot change, so they cannot fail** (slice 1's
   cost 1, a tripwire on a living page becoming a provenance check; A's review, round 1). Each
   asserted a fact the assembly wrote onto the page, and goes on guarding only the corrected
   reading as frozen at the cut:
   - the 8 pins of `test_pages_await_parser_rebuild` (FUBO's and VITL's adjusted EBITDA, VRRM's
     one-offs, EPAM's and WERN's release revenues, NFLX's and WERN's twelve-month walls, VITL's
     concentration rows). Falsifier: a re-assembly writes one of the eight defects back onto a
     living page and no test goes red;
   - `test_dossier::test_committed_it_dossier_capband_benchmark_and_fresh_price` (IT's mid-band
     cap reads MDY on every leg; no stale-at-assembly note on the price). Falsifier: a re-assembly
     of IT puts IWM or SPY on a leg, or a stale note on the price, and no test goes red;
   - `test_dossier::test_release_drivers_dedup_identical_segments` (no filing repeats a driver
     segment). Its source guard on the extractor still runs. Falsifier: a re-assembly of IT
     repeats a segment while the guard's line is still in the code, and no test goes red.
6. **$0.** No model call, no vendor call, and no page rebuilt or re-rendered.
