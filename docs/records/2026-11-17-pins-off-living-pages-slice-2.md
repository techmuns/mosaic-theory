---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# PINS OFF LIVING PAGES, SLICE 2 OF 5 (W27 follow-up, STATE row 41 (a)): 18 facts, quality, evals, impact and CIQ-reader test files read the cut or walk the roster, every assertion unchanged; a CIQ-paired refresh pin runs only on the export its frozen page names; the scan's named-living-page pairs fall 389 → 365 (80 → 65 files), and what it still finds in these files is false positives or one read of history ($0)

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
  - `test_price_date_bounds` (GOOGL's cohort), `test_quantity_kind_guard` (BRBR),
    `test_ciq_reader_contract` (TECX), `test_filed_tiebreak` (NFLX), `test_nm_is_not_missing`
    (FUBO).
- **`test_ciq_export_support`.** Its support module reads a page by ticker under its own `ROOT`.
  The two SMPL tests that go through that lookup point it at a root whose `data/dossiers` is the
  cut, so the lookup itself still runs, on the frozen page.
- **To the roster.** These now walk covered names, never a named one:
  - `test_known_wrong_marker`'s "an unmarked page renders no banner" walks every covered page
    with no sidecar, where it named SMPL, AORT and FUBO;
  - `test_evals_panel_and_stats`'s unmoved-row check skips a name the roster no longer covers,
    which has no living page. The scan could not see this one, and the slice-1 replay found it.
- **A CIQ-paired pin keeps its pairing honest.** `test_historical_forecast_error`'s refresh pin
  pairs the page with the export on disk, and the transform writes only from the page's own
  export. Its frozen page now runs only while the export on disk is the one it names, and
  otherwise SKIPS, naming both shas (`skip_unless_pages_export(..., page=...)`, the house rule:
  a skip, never a looser assertion). A frozen page with no gate would go red for good at the next
  re-export.

**Populations changed** (`scripts/asserts_unchanged.py` cannot see them):
- the unmarked-banner check: SMPL, AORT and FUBO → every covered page with no sidecar (26 at the
  cut);
- the panel unmoved-row check: unchanged at the cut. A name that leaves the roster is no longer
  checked.

**WHY.** A retirement re-points every test reading the retired name's living page by name (STATE row
41 (a)). This slice moves that cost off 18 of the files in the plan's facts, quality, evals,
impact and misc group.

**HOW VERIFIED.**
- **No assertion changed.** `python scripts/asserts_unchanged.py af030d45` (with slice 3's
  reader-aware version of the checker): 18 files, 417 functions in both; 0 changed, 0 vanished,
  0 reader-only.
- **The scan** (`python scripts/named_page_pins.py HEAD`, the same 26 pages, on top of slice 1): 389 → 365
  pairs (value 183 → 178, invariant 206 → 187), 337 → 314 functions, 80 → 65 files. What it still
  flags in these files:
  - `tmp_path` trees named for a ticker (`test_descriptive_labels`, `test_quality_ciq`,
    `test_facts_layer`, `test_ciq_relationship_view_edges`'s writer);
  - a git-revision path (`test_evals_round2`, which reads the gold pages at the freeze);
  - a path string used as a classifier's input (`test_review_process`, `test_impact_run`'s first
    pin);
  - one read of history, `test_tracked_files_hold_no_transcript_run`. It reads #1036's files at
    #1036's parent commit, and its head scan skips a file that is gone, so a retirement edits
    nothing.

  Slice 5 fixes the scan's false positives and records the residue.
- **The suite.** {SUITE}
- **The impact check.** {IMPACT}

**BOUNDARY.**
- **Counts:** at this slice's commit, on top of slice 1 (`af030d45`), unless another is named.
- **"Pairs" / "functions" / "files":** `scripts/named_page_pins.py`, a lower bound.
- **"Assertions":** the changed `tests/*.py` files.

**WHAT REMAINS (slices 3–5).** These are slices 3 (valuation), 4 (dossier render, refreshes and the
shared `tests/stripped_pages.committed_page`) and 5 (propose, templates, triggers, the proof, the
ratchet and STATE row 41).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The CIQ-paired refresh pin skips after a re-export** until the page is cut anew. Before, it
   failed until the page was rebuilt. Falsifier: it skips while the export on disk is the one the
   frozen page names.
2. **$0.** No model call, no vendor call, and no page rebuilt or re-rendered.
