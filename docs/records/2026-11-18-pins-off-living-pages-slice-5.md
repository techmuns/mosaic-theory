---
id:
status: shipped
date: 2026-11-18
prs: []
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 5 OF 5 (W27 follow-up, STATE row 41 (a) CLOSED): the propose, template, trigger and recipe pins read the cut or walk the roster; the scan's false positives are fixed and three blind spots added; a ratchet holds the 68 (test, page) pairs that remain, each with its reason; retiring AMZN with the whole suite touches 1 test file, from 31 at the cut, and that one is a corpus floor failing loud by A's ruling, not a named read ($0)

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

**WHY.** A retirement re-pointed every test reading the retired name's living page by name
(STATE row 41 (a)): at `4889ddba` an AMZN retirement replayed with the whole suite touched 31 test
files net of named noise. This slice ends the series and leaves a machine check in place of the
plan.

**HOW VERIFIED.**
- **The checker.** `python scripts/asserts_unchanged.py origin/main` (main `b2102256`, #1109
  merged; the same at `6110795d`) over 22 test files and 484 functions: 0 changed, 0 disabled, 0 control, 0 vanished, 1
  reader-only (`test_freshness`: `_assembled("TJX")` → `_frozen_assembled("TJX")`), 6 population
  (the walks above, and two `test_propose` loops whose iterable's reader moved to the cut), 24 new
  (helpers and the new pins).
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
- **The replay, the series' end count.** AMZN retired the roster's way in a scratch worktree of
  `2b442c8a`, as slice 1 did: 1 appended roster line, its 2 page files, its 2 web mirrors and
  `index.json`, 6 files. The whole offline suite ran in it and in an unretired worktree of the
  same commit, both with the CIQ link. A test counts only if the unretired run passed it.
  - **Unretired:** 12,770 tests, 12,593 passed, 54 failed, 123 skipped (27.8 min). **Retired:**
    12,732 tests, 12,556 passed, 55 failed, 121 skipped (26.7 min).
  - **38 tests are collected only unretired**, every one an AMZN case of a corpus parametrization
    and every one passing there: `test_ev_gap_persistence` ×5, `test_ev_gap_render` ×4,
    `test_prespend` ×4, `test_forward_layers_basis` ×4, and 21 more in 15 files. They leave with the
    page and edit nothing.
  - **One test passes unretired and fails retired, and none newly skips:**
    `test_r3_template::test_r1_and_r4_templates_keep_their_shape_across_the_corpus`. That is
    **1 file**, against 31 at `4889ddba` and 25 after slice 1, net of named noise. None of the
    noise slice 1 named appeared in either run this time.
  - **It is not a named read.** It walks the corpus, and its floor needs one R4 page that builds a
    template. AMZN is the only one, since UBER's template step refuses. Retired, the floor fails
    loud: "the corpus check ran over {'r1': 14, 'r4': 0}". That is A's ruling on floors, the
    nearest case slices 3 and 4 named (cost 9, below).
  - **The ratchet passes in the retired tree.** AMZN's 7 named pairs are false positives, and
    with no living AMZN page none is read as stale.
- **The impact check.** `python -m vinci.impact run --base origin/main --head HEAD` at
  `1dca055a` (main `b2102256` merged): 0 of 677 tests fail on base code and pass on head code
  (672 pass at both, 5 skipped), and `verify` reads VALID. At `f79bf681`, against `6110795d`, it
  read the same. The PR body carries the report.

**BOUNDARY.**
- **Counts:** at this slice's commit, against main `6110795d` (slices 1–4 merged) or, where named,
  `b2102256` (#1109 merged too).
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`, a lower bound, over
  `tests/**/*.py` less `tests/fixtures/`; "main's scanner" is its version at `6110795d`.
- **"Pages":** the roster's 26 covered names.
- **The replay:** `-m "not network" -n 8`, CIQ folder linked, 2026-11-17, the whole suite both
  ways.

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
   iterates the cut's pages in a list comprehension; the checker reads only `for` statements round
   an assert, so it lists no POPULATION row. Falsifier: a moved pin's population changes inside a
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
8. **The R4 template floor fails loud when AMZN retires** (the replay, above). AMZN is the only
   covered page whose R4 template builds. This is the floor working as A ruled: a check that walks
   nothing fails. It is the one test an AMZN retirement still edits, and the floor's message says
   what to do then: pin the R4 shape on AMZN's frozen copy. Not changed here, since a moved test
   must assert what it asserted. Falsifier: AMZN retires and the corpus check stays green with no
   R4 page in it.
9. **#1109's `test_dossier` changes are not in this replay.** It ran on `2b442c8a`, before #1109.
10. **$0.** No model call, no vendor call, and no page rebuilt or re-rendered.
