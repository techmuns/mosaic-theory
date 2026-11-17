---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 1 OF 5 (W27 follow-up, STATE row 41 (a)): every committed page is frozen at main `4889ddba` as the same git blobs, so 0 new page objects; a guard holds each copy to `git show`; 20 covenant, debt, filing and release test files read the cut or walk the roster, every assertion unchanged; the scan's named-living-page pairs fall 450 → 389 (98 → 80 files), and the 5 left in these files are scan false positives; an AMZN retirement replayed at the base breaks 82 tests in 25 files and skips 13 in 7, 31 files in all, which slice 5 brings to 0 ($0)

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
  - a copy its own README does not list, or lists with another blob.

  A git checkout without the commit (a shallow clone) fails. A tree that is not a git checkout at
  all (the impact harness's `git archive` export) skips, with the reason named, as
  `test_state_identifiers` does: it has no history to hold a cut to. CI checks out
  `fetch-depth: 0`, so the guard runs on every PR.
- **The support.** `tests/frozen_support.py` gives `frozen_page(T)` / `frozen_doc(T)`, which never fall
  back to a living page. It also gives the roster walk: `covered_pages()`, `covered_where(has, what)`
  (fails loud when no covered page has the property, never a skip), `roster_names(status)` and
  `living_doc(T)` for a name a walk handed back.
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
  - `test_release_amount_scale` (VRRM, CNXC), `test_release_adjusted_eps` (BURL);
  - `test_debt_maturities` (VRRM), `test_filing_wall_and_concentration_roles` (every name but the
    two already frozen), `test_efts_caps_and_instants`;
  - `test_liquidity_line` (LLY), `test_impairment_headroom` (MCK), `test_insider_own_issuer` and
    `test_section16_fpi` (WERN), `test_capital_allocation` (SMPL, EPAM, IT);
  - `test_segment_facts` and `test_customer_count`'s writer (AMZN), and `test_materiality`'s
    CNXC fixture and its green-path market cap.

  Five invariants now walk the roster:
  - `test_materiality`: an unusual-item row is structured, on every covered page with one (20 at
    the cut);
  - `test_customer_count`: the count is never sent to the synthesis, on every covered page with a
    count and every one without (at least one of each);
  - `test_evals_covenant_transform`: the $0 equality, on every covered panel page with a PRESENT
    quoted term (`vinci/evals/synthesis_panel.json`; BURL, CNXC, MCK and SMPL at the cut, the
    population the parametrize named). It is walked inside the test, never at import (review
    round 0): a walk at import turned a roster mismatch into a collection error that stopped the
    whole suite;
  - `test_release_amount_scale`: VRRM's range-made figures never print, on any covered card, both
    renderers;
  - `test_covenant_coverage_rule`'s pointer precondition reads the cut, its fixtures' source.

  Every `pytest.skip("no committed <T> dossier")` on a moved read is gone: a retired name made those
  tests skip, silently, rather than fail.
- **`scripts/asserts_unchanged.py`** compares the assertions of every changed test file at BASE and
  in the working tree, by AST in source order: `assert`, `pytest.raises` / `warns` and
  `pytest.fail`. Every slice runs it. It does NOT see POPULATIONS (a parametrize list, a loop's
  pages, a removed skip). So every population this slice changes is listed here:
  - unusual-item rows: SMPL and CNXC → the 20 covered pages with a row;
  - the count never sent: AMZN and BURL → the 24 covered pages with a count and the 2 without;
  - the panel equality: the same 4 pages, as one walked test in place of 4 parametrized cases;
  - VRRM's range-made figures: VRRM's card → all 26 covered cards, both renderers;
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
- **0 new page objects.** `git rev-list --objects HEAD --not 4889ddba` on the slice's commit lists
  It lists no page file. Measured tree to tree (`git ls-tree -r`, HEAD's blobs not in
  `4889ddba`'s tree), the slice adds 26 blobs: the 20 changed test files, the new guard, the
  support module, the script, the two READMEs and this record. None is a page file: the only new
  blob under the cut is its README. Each `cut-4889ddba/<T>/` is the same tree object as
  `data/dossiers/<T>/` at `4889ddba` (`git ls-tree -d`: all 26 shared). The working tree grows by 16 MB (`du -sh`) and the object
  store by 0 bytes of page data.
- **The guard fires.**
  - On the committed cut it checks all 52 files.
  - On a tmp copy of the real cut, unedited, it passes (the control).
  - Each negative is that copy edited once, and each is refused: one byte, an extra file, an unknown
    commit, a missing README row, an unlisted copy.
  - A one-byte edit to the real committed cut turns it red; restoring the file turns it green.
    (`differs from 4889ddba…:data/dossiers/SMPL/dossier.json (blob a9d5fff2e740 vs committed
    f8c2a9f74d62)` and `its README states blob f8c2a9f74d62, the copy is a9d5fff2e740`).
  - Outside a git checkout, 7 of its 9 pins skip with the reason named and 2 run; in a
    `--depth 1` clone the walk fails `cut-4889ddba: no commit 4889ddba in this checkout`.
- **No assertion changed.** `python scripts/asserts_unchanged.py 4889ddba`: 22 files (the 20 test
  files, the support module and the guard), 484 functions in both, 0 changed, 0 vanished.
  `11272.0` → `11273.0` in one moved assert of `test_impairment_headroom` exits 1 and names
  `test_the_refresh_reads_edgar_as_filed_by_the_pages_price_date_and_moves_its_fields`.
- **The suite.** The full offline suite (`-m "not network" -n 8`, the CIQ folder linked) at the
  slice's `6c60282e`, against the same run of `4889ddba` on the same machine:
  - **74 → 77 failing**, every one of the base's 74 a local-data failure (CIQ exports re-pulled
    since a pin was verified, date-dependent live reads) that CI does not run;
  - **7 new.** `test_records_ledger` (this record's PR number, filled at the PR); `test_evidence_same_passage`
    (LibreOffice failed to convert a GOOGL transcript RTF, an environment failure that also
    fails alone); `test_theme_intelligence_group3` ×2 (browser tests); `test_transcript_run_guard` ×3;
  - **4 gone**, all of `test_transcript_run_guard` or `test_tracked_files_…`: the set of its
    cases that fail differs between any two runs of the same tree.

  The three files the review round and the guard's skip changed afterwards
  (`test_evals_covenant_transform`, `test_materiality`, `test_frozen_pages_are_cuts`) pass, 25 of
  25. The two browser tests pass run alone, 2 of 2. `test_transcript_run_guard` run alone fails
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
- **The replay's before-count**, measured at `4889ddba` for slice 5 to compare against:
  - **AMZN retired the roster's way** in a scratch tree of `4889ddba`: 1 appended roster line, its
    2 page files, its 2 web mirrors and `index.json`, 6 files.
  - **The whole offline suite there**, against the unretired run: 86 tests newly fail in 27 files,
    and 14 newly skip in 8 files.
  - **Net of noise:** 82 tests fail in 25 files and 13 skip in 7, so **31 test files** must change
    for AMZN to retire today. The noise is named: `test_transcript_run_guard`'s varying cases,
    `test_evidence_same_passage`'s LibreOffice failure, and one BURL queue skip in
    `test_maintenance_path`.
  - The scan counts 25 files for AMZN, and the replay finds files it cannot see: `test_r4_card`,
    `test_anchor_off_headline`, `test_evals_panel_and_stats`, `test_covenant_unextracted_reason`
    and `test_coverage_roster`. The last picks the first retired name and its newest frozen copy,
    so it reds on any retired name with no copy, which the cut now gives every page.
  - **On this slice**, the same retirement over those 34 files leaves 76 failures in 23 files and
    5 skips: the covenant skips, `test_customer_count`, `test_segment_facts` and
    `test_coverage_roster` are gone.
  - The full list is in the slice's notes (`named-pins-replay-before.md`, shared notes folder).

**WHAT REMAINS (slices 2–5).**
- **By the scan:** 389 (test, name) pairs in 80 files, by the plan's file lists. Slice 2 covers
  facts, quality, evals, impact and misc. Slice 3 covers valuation, anchor, EV gap and lease.
  Slice 4 covers dossier render and refreshes. Slice 5 covers propose, templates and triggers.
- **By the replay:** the 31 files less the 6 this slice cleared.
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
- **"Assertions":** `scripts/asserts_unchanged.py` over the 22 changed `tests/*.py` files.
- **The replay:** `-m "not network" -n 8` over all of `tests/`, CIQ folder linked, scratch trees of
  `4889ddba` and of this slice, 2026-11-17; a failure counted only if the unretired run passed it.
- **"New objects":** blobs in HEAD's tree absent from `4889ddba`'s tree (`git ls-tree -r`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **A tripwire on a living page becomes a provenance check.** For example,
   `test_covenant_coverage_rule`'s precondition (fixture pointers equal the page's) used to go red
   when a page was re-assembled. It now holds the fixture to the page it was taken from. A rebuild
   that moves a page's pointers no longer flags the fixture. That is the TEST-LAYER RULE's trade,
   and the fixture still reads the real type. Falsifier: a fixture drifts from the living page and
   a pin on it passes while the extractor's behaviour on that page has changed.
2. **16 MB more in the working tree** (0 in the object store). Every page in the cut is already
   published in this repo's history (A, 2026-11-17, item 3).
3. **Pages no pin reads yet are in the cut** (ORKA and ROST had no site at the base). A cut is the
   corpus at one commit, so a corpus-wide value pin can be pointed at it as a dossiers root.
   Slices 2–5 may need any page. Falsifier: slice 5 finds a copy no test reads, which it then
   reports.
4. **The scan is a lower bound** (helper-module reads are invisible to it). The proof is slice 5's
   replay, not the scan.
5. **$0.** No model call, no vendor call, and no page rebuilt or re-rendered.
