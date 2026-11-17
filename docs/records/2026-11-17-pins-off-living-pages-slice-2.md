---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 2 OF 5 (W27 follow-up, STATE row 41 (a)): 16 facts, quality, evals, impact and CIQ-reader test files read the cut or walk the roster, every assertion unchanged; a CIQ-paired refresh pin now runs on the export its frozen page names, live or archived, where it skipped after a re-export; the panel check reads the frozen copy at the panel's blob and checks two pages where it checked one; the scan's named-living-page pairs fall 423 → 399 (83 → 68 files) ($0)

**WHAT.**
- **Slice 2 of the plan A approved on 2026-11-17** (record of slice 1:
  `docs/records/2026-11-17-pins-off-living-pages-slice-1.md`). It reads through slice 1's cut
  (`tests/fixtures/frozen_pages/cut-4889ddba/`) and `tests/frozen_support.py`. It adds no fixture and
  edits no shared module.
- **To the cut.** Each of these reads a page by name as a host, a value or a page's own shape:
  - `test_historical_forecast_error` (AMZN), `test_horizon_read_block_bounds` (AMZN),
    `test_latest_cell_contract` (TJX), `test_zero_coercion` (TJX);
  - `test_impact_values` and `test_impact_run` (MCK), `test_ciq_relationship_view_edges`,
    `test_band_checks`, `test_edgar_fallback_provenance_and_sign` and
    `test_fiscal_year_change_marker` (AMZN);
  - `test_quantity_kind_guard` (BRBR), `test_ciq_reader_contract` (TECX) and
    `test_filed_tiebreak` (NFLX).
- **`test_ciq_export_support`.** Its support module reads a page by ticker under its own `ROOT`.
  The three SMPL tests that go through that lookup point it at a root whose `data/dossiers` is
  the cut, so the lookup itself still runs, on the frozen page. The review found the third: its
  read was indirect, so the scan could not see it.
- **To the roster.** `test_known_wrong_marker`'s "an unmarked page renders no banner" walks every
  covered page with no sidecar, where it named SMPL, AORT and FUBO.
- **The panel's unmoved-row check reads frozen copies.** An unmoved page is one whose blob is the
  panel's. The check now reads it wherever a frozen copy holds it (`frozen_copies`), never off the
  living tree. On main it read each living page, with AORT and MVST special-cased to their dated
  copies. No living page holds a panel blob any more, so it checked one row, AORT's. It now checks
  two, AORT's 2026-10-26 copy and TECX's 2026-09-28 copy, and both reproduce their rows. The
  hard-coded AORT and MVST paths are gone, and a retirement moves nothing.
- **A CIQ-paired pin runs on its page's export.** `test_historical_forecast_error`'s refresh pin
  pairs the page with an Estimates export, and the transform writes only from the export the page
  names. The frozen page now takes its bundle from `skip_unless_export(..., <the page's own
  sha256>)`, and the store the transform reads points at that bundle's folder. That is the folder's
  export while it is the page's, and otherwise the archived folder that holds it
  (`ciq-archive/replaced-<date>/`, where the operator keeps each replaced export). It skips, naming
  both sha256s, only when neither holds it. The first cut of this slice skipped after any
  re-export (`skip_unless_pages_export`); the review showed the archive path was there.

**Populations changed** (the checker lists both as POPULATION):
- the unmarked-banner check: SMPL, AORT and FUBO → every covered page with no sidecar (26 at the
  cut);
- the panel unmoved-row check: the living tree plus two dated copies → every frozen copy; 1 row →
  2 at the cut (AORT, TECX).

**Kept on the living page, by name, with the reason** (both are outside what the scan sees):
- `test_nm_is_not_missing::test_the_live_fubo_sentence_is_no_longer_flagged` reads FUBO's CURRENT
  synthesis by design and skips when it carries no "not missing" claim. That has been so since
  2026-08-18, and so is it on the cut's copy, where it would skip for good. It already skips when
  the page is gone, so a retirement edits nothing.
- `test_price_date_bounds`'s `_committed_cohort` compares GOOGL's page cohort with the one built
  from the living `data/graph_coverage.json`. That is a page-and-living-artifact pair, the record
  class (A's option (1)). A frozen page beside the living graph would mix two vintages.

**WHY.** A retirement re-points every test reading the retired name's living page by name (STATE row
41 (a)). This slice moves that cost off 16 of the files in the plan's facts, quality, evals,
impact and misc group.

**HOW VERIFIED.**
- **No assertion changed.** `python scripts/asserts_unchanged.py 8a71a383` (main, with slice 1
  merged): 16 files, 393 functions in both: 0 changed, 0 disabled, 0 control, 0 vanished, 0
  reader-only, and 2 population (above).
- **The archive path, run.** In scratch, the live AMZN folder held no Estimates export, and a
  stand-in `ciq-archive/` held AMZN's real export. The refresh pin passed there, reading workbooks
  from the archive. The old gate would have skipped. The scratch copies were deleted.
- **The files.** The 16 changed test files, offline, with the CIQ link present: 576 passed, 4
  skipped, 1 xfailed, 8 failed. The same 8 fail on main `8a71a383` with the same link and the same
  counts: the mislabelled PARR quarterly Financials export (4), the latest-cell contract on the
  current exports (3) and an undated header marker (1).
- **The scan** (`python scripts/named_page_pins.py HEAD`, the same 26 pages, against main at
  `8a71a383`): 423 → 399 pairs (value 208 → 203, invariant 215 → 196), 366 → 343 functions, 83 →
  68 files. What it still flags in these files:
  - `tmp_path` trees named for a ticker (`test_descriptive_labels`, `test_quality_ciq`,
    `test_facts_layer`, `test_ciq_relationship_view_edges`'s writer);
  - a git-revision path (`test_evals_round2`, which reads the gold pages at the freeze);
  - a path string used as a classifier's input (`test_review_process`, `test_impact_run`'s first
    pin);
  - one read of history, `test_tracked_files_hold_no_transcript_run`. It reads #1036's files at
    #1036's parent commit, and its head scan skips a file that is gone, so a retirement edits
    nothing.

  Slice 5 fixes the scan's false positives, records the residue, and adds the blind spots the
  review found: a read through a support module's own `ROOT`, a path built from `__file__`, and a
  page read in a same-module helper.
- **The suite.** {SUITE}
- **The impact check.** {IMPACT}

**BOUNDARY.**
- **Counts:** at this slice's commit, against main at `8a71a383` (slice 1 merged as #1098), unless
  another is named.
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`, a lower bound.
- **"Assertions":** the changed `tests/*.py` files.

**WHAT REMAINS (slices 3–5).** These are slices 3 (valuation), 4 (dossier render, refreshes and the
shared `tests/stripped_pages.committed_page`) and 5 (propose, templates, triggers, the proof, the
ratchet and STATE row 41).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The CIQ-paired refresh pin skips when neither the folder nor the archive holds its page's
   export.** It used to fail until the page was rebuilt. Falsifier: it skips while the folder or
   `ciq-archive/` holds the export the frozen page names.
2. **The checker cannot see a skip inside a helper.** `skip_unless_export` and
   `skip_unless_pages_export` skip from inside a support function, so `asserts_unchanged.py`
   counts no new skip call. Slice 5 teaches it the repo's skip helpers.
3. **$0.** No model call, no vendor call, and no page rebuilt or re-rendered.
