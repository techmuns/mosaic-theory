---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 4 OF 5 (W27 follow-up, STATE row 41 (a)): 14 dossier-render and refresh test files and the shared `stripped_pages.committed_page` read the cut or walk the roster; three invariants now hold on every covered page with the property; four assertions change, each for a stated reason; the scan's named-living-page pairs fall 423 → 357 (83 → 76 files); 14 render tests were found dormant since #407 and are reported, not fixed ($0)

**WHAT.**
- **Slice 4 of the plan A approved on 2026-11-17** (slice 1:
  `docs/records/2026-11-17-pins-off-living-pages-slice-1.md`). It reads through slice 1's cut
  (`tests/fixtures/frozen_pages/cut-4889ddba/`) and `tests/frozen_support.py`, and adds no fixture.
- **To the cut.** Each of these reads a page by name as a host, a value or a page's own shape:
  - `test_dossier`: 18 functions on SMPL, VRRM, CNXC, IT and BRBR. Their 16 skips of the form
    "no committed <T> dossier" are gone, because a frozen copy always exists. A skip removed, never
    one added.
  - `tests/stripped_pages.committed_page`, the shared host reader. Its callers in four files this
    slice does not otherwise edit now read the cut as well: `test_evals_independence`,
    `test_evals_run_builds` (NFLX), `test_evals_order8` (SMPL) and `test_evidence_same_passage`
    (GOOGL). Each uses the page as a host for invented rows or a replay, and all four files pass
    (96 tests). Its corpus walk, `committed_pages()`, still reads the living pages.
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
    turns it red on AMZN, the first covered name, whose page the message names.

**WHY.** A retirement re-points every test reading the retired name's living page by name (STATE
row 41 (a)). This slice moves that cost off the dossier render and refresh group, the plan's slice
4.

**HOW VERIFIED.**
- **The checker.** `python scripts/asserts_unchanged.py 8a71a383` (main, with slice 1 merged) over 15
  files and 745 functions: 0 disabled, 0 control, 0 vanished, 1 reader-only
  (`test_an_export_not_on_disk_is_named_never_reported_unchanged`, `_living` → `_at_cut`), 2
  population (the R1 walk, the cap-line walk), and **4 changed, each reviewed**:
  1. and 2. `test_anchor_off_headline`'s two decision pins, md and web. The floor `decided >= 4`
     became `decided >= _decisions_at_the_cut_still_covered()`: the recorded decisions the cut's
     pages carry (AMZN, CNXC, GOOGL, UBER), counted on the names the roster still covers. It reads
     4 today. A retirement lowers it by that name's own decision, never by a test edit, and a
     decision a covered page loses still goes red. The message now says "at the cut".
  3. `test_layer_refreshes::test_a_refresh_that_moves_a_layer_records_it`. A reader swap through a
     path expression: `DOSS / "UBER"` → `frozen_page("UBER")`. The checker normalizes a reader only
     when it is a call, so it reads this as CHANGED. `_copy` writes the same frozen page into the
     tmp tree, so the assertion still compares the refreshed page with the page it came from.
  4. `test_refresh_fleet_and_bridge_guards::test_a_fleet_refresh_updates_the_frontend_mirror`.
     SMPL → each covered name `t`, in the walk above, and the message names the page.
- **The dormant test.** `test_return_ratios_exhibit_no_phantom_negative_tick_e2e` skips on main:
  no record is `pending_analyst`, so its move had never run. It was run once with WERN's record set
  to `pending_analyst` in the slice's worktree, and the record was then restored (`git checkout`):
  it passes on the frozen IT page.
- **The files.** The 14 changed test files, offline, with the CIQ link present: 642 passed, 17
  skipped, 2 xfailed, 0 failed.
- **The scan** (`python scripts/named_page_pins.py HEAD`, the same 26 pages, against main at
  `8a71a383`): 423 → 357 pairs (value 208 → 180, invariant 215 → 177), 366 → 310 functions, 83 →
  76 files. What it still finds in these files, 26 pairs in 23 functions:
  - **scan false positives, 18 pairs in 15 functions:** `tmp_path` trees built from a frozen copy.
    `test_benchmark_figures_refresh` (6, TECX from its 2026-09-28 copy), `test_input_manifest`
    (3, NFLX and BURL), `test_layer_refreshes` (2), `test_surprise_listing_block`'s writer pins
    (2, PARR) and `test_analysis_as_of_skips_and_filings` (2, IT and NKE);
  - **record-class residue, 8 pairs in 8 `test_dossier` functions:** each pairs a named page
    with that name's `frontend/scenarios/<T>.json` record (IT ×4, SMPL ×2, BRBR ×2). Under A's
    option (1) they stay, with slice 5's record writing up the class. All 8 are dormant today
    (below).

  Slice 5 fixes the scan's false positives and records the residue.
- **The suite.** {SUITE}
- **The impact check.** {IMPACT}

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

**WHAT REMAINS (slice 5).** Propose, templates and triggers; `test_recipe_3a`/`3b`; the scan's
false positives; the ratchet; the AMZN replay; STATE row 41.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A walk's floor fails loud** when the last covered page with its property leaves (A's ruling).
   The R1-record walk is the nearest case: 5 names. Falsifier: a walk passes on an empty
   population.
2. **The decision floor is the cut's count, not a constant.** A decision recorded after the cut
   raises nothing until the page is cut anew. Falsifier: a covered page at the cut loses its
   decision and the pin stays green.
3. **The tripwires still read living pages.** NFLX's and PARR's strict xfails watch for the living
   page's re-read, so they still name it, behind a roster skip.
4. **$0.** No model call, no vendor call, and no page rebuilt or re-rendered.
