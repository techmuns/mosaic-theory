---
id:
status: shipped
date: 2026-11-17
prs: [1098]
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 1 OF 5 (W27 follow-up, STATE row 41 (a)): every committed page is frozen at main `4889ddba` as the same git blobs, so 0 new page objects; a guard holds each copy to `git show`; 20 covenant, debt, filing and release test files read the cut or walk the roster, every assertion unchanged; the scan's named-living-page pairs fall 450 → 389 (98 → 80 files), and the 5 left in these files are scan false positives; an AMZN retirement replayed on the same code both ways touches 31 test files at the base and 25 with this slice, net of named noise, and slice 5 brings it to 0 ($0)

**WHAT.**
- **The cut.** `tests/fixtures/frozen_pages/cut-4889ddba/<T>/` holds `dossier.json` and `dossier.md`
  for all 26 pages committed at main `4889ddba` (#1092), copied by `git cat-file blob` of each page
  file's blob and checked by `git hash-object`. The roster covered those 26 names at the cut: 11
  active and 15 watch. The web mirrors are byte-identical to these files at the cut, so a test that
  read `frontend/dossiers/<T>.*` reads the same bytes here.
  - Each copy's header is a row of `cut-4889ddba/README.md`, giving its roster status at the cut,
    its assembled date, its reference date and its two blobs. The frozen-pages README has one row
    for the cut and a paragraph on what a `cut-<sha8>/` directory is.
  - Which pins read a copy is derived (`grep 'frozen_doc("T")'`), never listed, so no list rots.
- **The guard.** `tests/test_frozen_pages_are_cuts.py` is required (A, 2026-11-17). It holds every
  file in every `cut-*/` to `git show <sha>:data/dossiers/<T>/<file>`, and both READMEs to the
  copies. It refuses:
  - a one-byte edit;
  - a file the page never had;
  - a cut of an unknown commit;
  - a cut with no README row;
  - a copy its own README does not list, or lists with another blob;
  - an inserted carriage return: the blob is hashed over the raw bytes (`--no-filters`), since
    `* text=auto` normalized a CR away (review round 1, item 5);
  - a cut with no date in `frozen_support.CUTS` (round 1, item 7).

  It reads a cut's files as git does: tracked, plus untracked ones git does not ignore. A file git
  ignores, such as a Mac's `.DS_Store`, is not part of a cut (round 1, item 6). A folder outside any
  checkout (a tmp copy) is walked whole.

  A git checkout without the commit (a shallow clone) fails. A tree that is not a git checkout at
  all (the impact harness's `git archive` export) skips, with the reason named, as
  `test_state_identifiers` does: it has no history to hold a cut to. CI checks out
  `fetch-depth: 0`, so the guard runs on every PR.
- **The support.** `tests/frozen_support.py` gives `frozen_page(T)` / `frozen_doc(T)`, which never fall
  back to a living page. It also gives the roster walk: `covered_pages()`, `covered_where(has, what)`
  (fails loud when no covered page has the property, never a skip), `roster_names(status)` and
  `living_doc(T)` for a name a walk handed back. `CUTS` gives every cut's date, and
  `newest_frozen_copy(T)` returns a name's NEWEST frozen copy (round 1, item 7). NEWEST means the
  latest date: a dated folder's name, which is the page's assembled date (the README's
  convention), or a cut's commit date from `CUTS`, with a cut winning a tie. It never means the sort
  order of the folder names, since hex is not time.
- **The rule applied to each site** (A's ruling of 2026-11-17, item 1):
  - a value pin, or a test about something only that page has (its exhibit, its tag, its
    refusal, its host role for a frozen block), reads the page's frozen copy;
  - an invariant that every page with a property must meet walks every covered page with it,
    with a floor of 1.
- **Slice 1's 20 test files.** These are the sites the scan found in the 21 files the plan named,
  plus `test_covenant_unextracted_reason`, which the scan could not see (its tickers are built in a
  NamedTuple) and the replay found. Two of the 21 needed no change: their hits are scan false
  positives. Most moves are host pages for frozen blocks, which go to the cut:
  - `test_covenant_exhibit_outcomes`, whose `_committed` host also serves `test_covenant_coverage_rule`:
    the scan charged that file 1 function and it reads 7 pages through this helper;
  - `test_covenant_refused_newer`, `test_covenant_value_in_quote`, `test_covenant_source_date`,
    `test_covenant_unextracted_reason`;
  - `test_release_amount_scale` (VRRM, CNXC). Its VRRM card pin reads VRRM's frozen card, since
    the banned strings are VRRM's own wrong figures (round 1, item 1);
  - `test_covenant_coverage_rule`'s pointer precondition, which reads its fixtures' source;
  - `test_debt_maturities` (VRRM), `test_filing_wall_and_concentration_roles` (every name but the
    two already frozen), `test_efts_caps_and_instants`;
  - `test_liquidity_line` (LLY), `test_impairment_headroom` (MCK), `test_insider_own_issuer` and
    `test_section16_fpi` (WERN), `test_capital_allocation` (SMPL, EPAM, IT);
  - `test_segment_facts` and `test_customer_count`'s writer (AMZN), and `test_materiality`'s
    CNXC fixture and its green-path market cap.

  Four invariants now walk the roster:
  - `test_materiality`: an unusual-item row is structured, on every covered page with one (20 at
    the cut);
  - `test_customer_count`: the count is never sent to the synthesis, on every covered page with a
    count and every one without (at least one of each);
  - `test_evals_covenant_transform`: the $0 equality. Its population is the synthesis panel's
    covered pages (`vinci/evals/synthesis_panel.json`) that carried a PRESENT quoted term AT THE
    CUT: BURL, CNXC, MCK and SMPL, the four the parametrize named. The equality itself runs on
    the living pages. So a living page that loses its terms fails its `assert checked` rather than
    dropping out (round 1, item 3; the round-0 walk selected by the living page's own terms, so
    that assert could not fail). This is the stated population (RUNBOOKS §n, the panel's pages)
    rather than all 20 covered pages with a quoted term. It is walked inside the test, never at
    import (review round 0), since a walk at import turned a roster mismatch into a collection error
    that stopped the whole suite;
  - `test_release_adjusted_eps`: the field equals the newest release's annual adjusted-EPS range,
    on every covered page with a filed release (all 26 at the cut, 5 with a range to print; round
    1, item 8). Its own docstring states the living invariant ("whatever it reads after a
    re-pull").

  Every `pytest.skip("no committed <T> dossier")` on a moved read is gone: a retired name made those
  tests skip, silently, rather than fail.
- **`scripts/asserts_unchanged.py`** compares every changed test file's functions at BASE and in the
  working tree, by AST, and sorts each difference into a category. Every slice runs it. Since round
  1 (item 2) it sees a disabled test, as well as a changed assertion:
  - **CHANGED:** an `assert`, `pytest.raises` / `warns` or `pytest.fail` differs, in source order;
  - **DISABLED:** a skip, skipif or xfail decorator appears or changes, or a `pytest.skip` /
    `xfail` / `importorskip` call is added;
  - **CONTROL:** the conditions enclosing an assertion differ (an `if`, `while` or `try` around
    it), or the function gains a `return`, `continue`, `break` or `raise`;
  - **VANISHED:** a test is gone.

  These four fail the check. Two more categories are listed and pass. **READER-ONLY** is an
  assertion that differs only in which page reader it calls. **POPULATION** is a parametrize list
  or a loop's iterable that changed, which is what a walk is. Every population this slice changes:
  - unusual-item rows: SMPL and CNXC → the 20 covered pages with a row;
  - the count never sent: AMZN and BURL → the 24 covered pages with a count and the 2 without;
  - the panel equality: the same 4 pages, now as one walked test, chosen from the frozen panel and
    cut;
  - the release-EPS field: BURL → the 26 covered pages with a filed release;
  - every other moved read: the same named page, at the cut in place of living.

**WHY.** A retirement still re-pointed every test reading the retired name's living page by name
(`docs/records/2026-11-17-the-coverage-roster.md`, WHAT IT COSTS 1). The plan, approved by A on
2026-11-17, is five file-disjoint PRs:
1. this one, the cut, its support and its guard;
2. facts, quality, evals, impact and misc;
3. valuation, anchor, EV gap and lease;
4. dossier render and refreshes;
5. propose, templates and triggers, plus the proof (the scan's residue, the ratchet, and an AMZN
   retirement replayed with the whole suite) and STATE row 41.

Only slice 5 edits STATE.md. Slices 2–4 run concurrently once this merges, each touching only its own
test files and its own record.

**HOW VERIFIED.**
- **0 new page objects.** Measured tree to tree (`git ls-tree -r`, HEAD's blobs not in
  `4889ddba`'s tree), the slice adds 29 blobs against the main it merged (`7973615f`).
  They are 24 test files: 21 changed, among them `test_coverage_roster`, and 3 new, the guard,
  `test_asserts_unchanged` and `test_frozen_support`. The other 5 are the support module, the
  script, the two READMEs and this record. None is a page file: the only new
  blob under the cut is its README. Each `cut-4889ddba/<T>/` is the same tree object as
  `data/dossiers/<T>/` at `4889ddba` (`git ls-tree -d`: all 26 shared). The working tree grows by
  16 MB (`du -sh`), and the object store by 0 bytes of page data.
- **The guard fires.**
  - On the committed cut it checks all 52 files.
  - On a tmp copy of the real cut, unedited, it passes (the control).
  - Each negative is that copy changed once, and each is refused: one byte, an inserted CR (round 1),
    an extra file, an unknown commit, a missing README row, an unlisted copy, and a cut with no
    stated date (round 1).
  - In a tmp git checkout that ignores `.DS_Store`, a `.DS_Store` in the cut and one in a page
    folder pass, and an untracked `notes.json` is still refused (round 1).
  - A one-byte edit to the real committed cut turns it red; restoring the file turns it green
    (`differs from 4889ddba…:data/dossiers/SMPL/dossier.json (blob a9d5fff2e740 vs committed
    f8c2a9f74d62)` and `its README states blob f8c2a9f74d62, the copy is a9d5fff2e740`).
  - Outside a git checkout, the 7 git-reading pins of the round-0 9 skip with the reason named, and
    2 run. In a `--depth 1` clone the walk fails `cut-4889ddba: no commit 4889ddba in this
    checkout`.
- **No assertion changed, and no test was disabled.** `python scripts/asserts_unchanged.py
  7973615f` (the main this slice merged): 23 files and 510 functions in both. Changed 0, disabled
  0, vanished 0, reader-only 0; 4 populations (listed above); 1 CONTROL:
  `test_materiality::test_material_unusual_items_reach_the_committed_record`. The `if` around its
  assert now calls `_is_unusual(r)`, the same predicate moved into a helper (review round 0, item
  10). A moved assert with one literal changed (`11272.0` → `11273.0`) exits 1 and names its test.
- **Review round 1, each fix shown failing first.**
  - **Items 2, 5, 6 and 7.** The new pins were run against the round-0 head (`0889de6c`):
    - `tests/test_asserts_unchanged.py` fails 11 of 11 (no `compare_sources`). The round-0
      checker itself prints "changed 0" for each of six mutations: an xfail decorator, a skipif
      decorator, a `pytest.skip` call, an `importorskip` call, an assert newly under an `if`, and
      an early `return`;
    - the CR pin and the `.DS_Store` pin fail;
    - `tests/test_frozen_support.py` fails to collect (no `newest_frozen_copy`).
  - **Item 4.** With `covered_where`'s floor removed, the new empty-walk pin is red; restored, it is
    green.
  - **Items 1, 3 and 8** move a pin's population, so the pin is the test. Each was run against the
    defect it missed:
    - item 1, VRRM off the roster with its card carrying "adj EPS 2026 $1.10";
    - item 3, BURL's living page with its quoted covenant terms gone;
    - item 8, a non-BURL page whose field misses its range.

    The round-0 head PASSED all three, blind; round 1 is RED on each.
- **The suite.** The full offline suite (`-m "not network" -n 8`, the CIQ folder linked) at the
  slice's `6c60282e`, against the same run of `4889ddba` on the same machine:
  - **74 → 77 failing**, every one of the base's 74 a local-data failure (CIQ exports re-pulled
    since a pin was verified, date-dependent live reads) that CI does not run;
  - **7 new.** `test_records_ledger` (this record's PR number, filled once #1098 opened); `test_evidence_same_passage`
    (LibreOffice failed to convert a GOOGL transcript RTF, an environment failure that also
    fails alone); `test_theme_intelligence_group3` ×2 (browser tests); `test_transcript_run_guard` ×3;
  - **4 gone**, all of `test_transcript_run_guard` or `test_tracked_files_…`: the set of its
    cases that fail differs between any two runs of the same tree.

  The three files the review round and the guard's skip changed afterwards
  (`test_evals_covenant_transform`, `test_materiality`, `test_frozen_pages_are_cuts`) pass, 25 of
  25. After round 1, the 11 files the round changed or added pass offline, and the 34-file
  replay's unretired run of round 1 adds only the named noise against the base. The two browser
  tests pass run alone, 2 of 2. `test_transcript_run_guard` run alone fails
  one case (PARR), another than either full run's: it fails at the base too, a different subset
  each run, on the private evidence store this machine holds.
- **The scan** (`python scripts/named_page_pins.py HEAD`, the same 26 pages):
  - 450 → 389 (test, name) pairs (value 211 → 183, invariant 239 → 206);
  - 385 → 337 test functions, in 98 → 80 files.

  The 5 pairs left in slice 1's files are scan false positives, which slice 5's scan fixes:
  - `test_quality_release` (×2) and `test_customer_count`'s writer (×2) build `tmp_path` trees named
    for a ticker;
  - `test_covenant_document_identity` reads the frozen `2026-08-18/SMPL` through a variable that
    the module also binds to `frontend/dossiers`, and the scan is not scope-aware.
- **The replay**, the same retirement on the same code both ways. AMZN was retired the roster's way
  in a scratch tree: 1 appended roster line, its 2 page files, its 2 web mirrors and `index.json`,
  6 files. A test counts only if the unretired run of the SAME code passed it. Every count is over
  **the 34 files**: the files any of AMZN's retired-tree failures or new skips fell in at
  `4889ddba` (the full table below).
  - **At `4889ddba`** (its full offline suite, run retired and unretired, then restricted to the
    34 files): raw, 86 tests newly fail in 27 files and 14 newly skip in 8, so 34 files are
    touched. Net of the named noise, 82 fail in 25 and 13 skip in 7: **31 files**.
  - **With slice 1, round 1** (the 34 files run retired and unretired): raw, 78 fail in 23 files
    and 8 skip in 5, so 27 files. Net, 71 fail in 22 and 7 skip in 4: **25 files**. That is 31 less
    the 6 slice 1 clears, and no file is newly touched.
  - **Noise** is named, not counted: `test_transcript_run_guard` fails a different case set on every
    run of either tree; `test_evidence_same_passage` fails a LibreOffice RTF conversion under load;
    and `test_maintenance_path` is one BURL queue skip.
  - **The scan's blind spots.** It counts 25 files for AMZN, and the replay finds files it cannot
    see: `test_r4_card`, `test_anchor_off_headline`, `test_evals_panel_and_stats`,
    `test_covenant_unextracted_reason` and `test_coverage_roster`. The last picks a retired name's
    newest frozen copy, and now does so by date (round 1, item 7). The cut gives every page one.
  - **A's independent replay** over this slice's 20 files went from 11 failures at the base to 0.

  | file (`tests/`) | after slice 1 |
  |---|---|
  | `test_anchor.py` | still touched |
  | `test_anchor_off_headline.py` | still touched |
  | `test_band_checks.py` | still touched |
  | `test_ciq_relationship_view_edges.py` | still touched |
  | `test_cohort_and_benchmark_cause_labels.py` | still touched |
  | `test_covenant_coverage_rule.py` | cleared by slice 1 |
  | `test_covenant_exhibit_outcomes.py` | cleared by slice 1 |
  | `test_covenant_unextracted_reason.py` | cleared by slice 1 |
  | `test_coverage_roster.py` | cleared by slice 1 |
  | `test_customer_count.py` | cleared by slice 1 |
  | `test_edgar_fallback_provenance_and_sign.py` | still touched |
  | `test_ev_bridge.py` | still touched |
  | `test_evals_panel_and_stats.py` | still touched |
  | `test_evidence_same_passage.py` | noise (named) |
  | `test_fiscal_year_change_marker.py` | still touched |
  | `test_forward_consensus.py` | still touched |
  | `test_forward_layers_basis.py` | still touched |
  | `test_forward_multiple_history.py` | still touched |
  | `test_historical_forecast_error.py` | still touched |
  | `test_horizon_read_block_bounds.py` | still touched |
  | `test_layer_refreshes.py` | still touched |
  | `test_maintenance_path.py` | noise (named) |
  | `test_net_debt_securities_leg.py` | still touched |
  | `test_operator_decision.py` | still touched |
  | `test_pe_eps_basis.py` | still touched |
  | `test_peer_median_one_family.py` | still touched |
  | `test_r3_template.py` | still touched |
  | `test_r4_card.py` | still touched |
  | `test_r4_forward_ev_ebit.py` | still touched |
  | `test_r4_machine_proposal.py` | still touched |
  | `test_r4_template.py` | still touched |
  | `test_segment_facts.py` | cleared by slice 1 |
  | `test_transcript_run_guard.py` | noise (named) |
  | `test_valuation_basis.py` | still touched |

**WHAT REMAINS (slices 2–5).**
- **By the scan:** 389 (test, name) pairs in 80 files, by the plan's file lists. Slice 2 covers
  facts, quality, evals, impact and misc. Slice 3 covers valuation, anchor, EV gap and lease.
  Slice 4 covers dossier render and refreshes. Slice 5 covers propose, templates and triggers.
- **By the replay:** the 25 files marked "still touched" in the table above (net of noise).
- **The scan's blind spots go to their helper's slice:** `test_r4_card` to slice 5,
  `test_anchor_off_headline` to slice 4, `test_evals_panel_and_stats` to slice 2.
- **Slice 5** carries the proof:
  - the scan's residue, its false positives fixed (a `tmp_path` tree, a git-revision path, a
    variable bound in two scopes);
  - the ratchet, seeded with that residue;
  - the whole-suite AMZN replay, whose target is 0;
  - STATE row 41.

**BOUNDARY.**
- **Counts:** at main `4889ddba` (2026-11-17) and this slice's commit, unless another is named.
- **"Pages":** `data/dossiers/*/dossier.json`, 26.
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`'s AST scan of `tests/**/*.py`
  less `tests/fixtures/` (532 files at the base), a lower bound.
- **"Assertions":** `scripts/asserts_unchanged.py 7973615f` over the 23 changed `tests/*.py` files
  that exist at that commit.
- **The replay:** `-m "not network"`, CIQ folder linked, 2026-11-17. At `4889ddba` it is the whole
  suite, retired and unretired, restricted to the 34 files. With round 1 it is the 34 files run
  retired and unretired, scratch trees of `0889de6c` plus the round's diff. A test counts only if
  the unretired run of the same code passed it.
- **"New objects":** blobs in this slice's index absent from the merged main's tree (`7973615f`,
  `git ls-tree -r`). `data/dossiers/` is unchanged from `4889ddba` there.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A tripwire on a living page becomes a provenance check.** For example,
   `test_covenant_coverage_rule`'s precondition (fixture pointers equal the page's) used to go red
   when a page was re-assembled. It now holds the fixture to the page it was taken from.
   - **What it no longer catches:** a re-assembly that moves a page's covenant pointer rows (a
     newly located filing, a dropped exhibit, a re-dated row). Before, that reddened the
     precondition and asked for the fixture to be re-cut. Now the fixtures
     (`tests/fixtures/covenant_coverage_rule/<T>.json`) go on pinning the selector on the rows as
     they stood at the cut. A selector defect that only a NEW pointer shape on a living page shows
     is caught only once a fixture of that shape is added.
   - That is the TEST-LAYER RULE's trade (A, round 1, item 8), and the fixture still reads the real
     type.

   Falsifier: a fixture drifts from the living page, and a pin on it passes while the extractor's
   behaviour on that page has changed.
2. **16 MB more in the working tree** (0 in the object store). Every page in the cut is already
   published in this repo's history (A, 2026-11-17, item 3).
3. **Pages no pin reads yet are in the cut** (ORKA and ROST had no site at the base). A cut is the
   corpus at one commit, so a corpus-wide value pin can be pointed at it as a dossiers root.
   Slices 2–5 may need any page. Falsifier: slice 5 finds a copy no test reads, which it then
   reports.
4. **The scan is a lower bound** (helper-module reads are invisible to it). The proof is slice 5's
   replay, not the scan.
5. **One CIQ-bound pin mixes two vintages** (named, not changed; A, round 1).
   `test_materiality`'s green-path test reads its market cap off the frozen page and its income
   statement off the CIQ bundle on disk. After a re-export the two are different vintages. The
   cap only scales a threshold, and the round-0 pairing (a living page's cap beside whatever
   export is on disk) mixed vintages the same way. The test skips in CI.
6. **$0.** No model call, no vendor call, and no page rebuilt or re-rendered.
