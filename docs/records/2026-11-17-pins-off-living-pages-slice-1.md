---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 1 OF 5 (W27 follow-up, STATE row 41 (a)): every committed page is frozen at main `4889ddba` as the same git blobs, so 0 new page objects; a guard holds each copy to `git show`; the 21 covenant, debt, filing and release test files read the cut or walk the roster, every assertion unchanged; the scan's named-living-page pairs fall 450 → 389 (98 → 80 files), and the 5 left in these files are scan false positives ($0)

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

  A checkout without the commit fails here; it never skips. CI checks out `fetch-depth: 0`.
- **The support.** `tests/frozen_support.py` gives `frozen_page(T)` / `frozen_doc(T)`, which never fall
  back to a living page. It also gives the roster walk: `covered_pages()`, `covered_where(has, what)`
  (fails loud when no covered page has the property, never a skip), `roster_names(status)` and
  `living_doc(T)` for a name a walk handed back.
- **The rule applied to each site** (A's ruling of 2026-11-17, item 1):
  - a value pin, or a test about something only that page has (its exhibit, its tag, its
    refusal, its host role for a frozen block), reads the page's frozen copy;
  - an invariant that every page with a property must meet walks every covered page with it,
    with a floor of 1.
- **Slice 1's 21 files.** These are the sites the scan found plus the ones it could not see. Most
  moves are host pages for frozen blocks, which go to the cut:
  - `test_covenant_exhibit_outcomes`, whose `_committed` host also serves `test_covenant_coverage_rule`:
    the scan charged that file 1 function and it reads 7 pages through this helper;
  - `test_covenant_refused_newer`, `test_covenant_value_in_quote`, `test_covenant_source_date`;
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
    population the parametrize named);
  - `test_release_amount_scale`: VRRM's range-made figures never print, on any covered card, both
    renderers;
  - `test_covenant_coverage_rule`'s pointer precondition reads the cut, its fixtures' source.

  Every `pytest.skip("no committed <T> dossier")` on a moved read is gone: a retired name made those
  tests skip, silently, rather than fail.
- **`scripts/asserts_unchanged.py`** compares the assertions of every changed test file at BASE and
  in the working tree, by AST in source order: `assert`, `pytest.raises` / `warns` and
  `pytest.fail`. Every slice runs it.

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
  24 new blobs: the 21 test files, the support module, the guard, the script and the two READMEs.
  It lists no page file. It also lists 6 new trees: root, `tests`, `tests/fixtures`,
  `frozen_pages`, the cut, and `scripts`. Each `cut-4889ddba/<T>/` is the same tree object as
  `data/dossiers/<T>/` at `4889ddba`. The working tree grows by 16 MB (`du -sh`) and the object
  store by 0 bytes of page data.
- **The guard fires.**
  - On the committed cut it checks all 52 files.
  - On a tmp copy of the real cut, unedited, it passes (the control).
  - Each negative is that copy edited once, and each is refused: one byte, an extra file, an unknown
    commit, a missing README row, an unlisted copy.
  - A one-byte edit to the real committed cut turns it red; restoring the file turns it green.
    {MUTATION_OUTPUT}
- **No assertion changed.** `python scripts/asserts_unchanged.py 4889ddba`: 21 files, 473 functions
  in both, 0 changed, 0 vanished. A mutation (one literal in one moved assert) exits 1 and names
  the function. {AST_MUTATION}
- **The suite.** {SUITE}
- **The scan** (`python scripts/named_page_pins.py HEAD`, the same 26 pages):
  - 450 → 389 (test, name) pairs (value 211 → 183, invariant 239 → 206);
  - 385 → 337 test functions, in 98 → 80 files.

  The 5 pairs left in slice 1's files are scan false positives, which slice 5's scan fixes:
  - `test_quality_release` (×2) and `test_customer_count`'s writer (×2) build `tmp_path` trees named
    for a ticker;
  - `test_covenant_document_identity` reads the frozen `2026-08-18/SMPL` through a variable that
    the module also binds to `frontend/dossiers`, and the scan is not scope-aware.
- **The replay's before-count**, measured at `4889ddba` for slice 5 to compare against:
  {REPLAY}

**BOUNDARY.**
- **Counts:** at main `4889ddba` (2026-11-17) and this slice's commit, unless another is named.
- **"Pages":** `data/dossiers/*/dossier.json`, 26.
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`'s AST scan of `tests/**/*.py`
  less `tests/fixtures/` (532 files at the base), a lower bound.
- **"Assertions":** `scripts/asserts_unchanged.py` over the 21 changed test files.
- **"New objects":** `git rev-list --objects HEAD --not 4889ddba`.

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
