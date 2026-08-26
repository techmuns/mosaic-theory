---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **ONE COMPANY-LABEL RESOLVER — OFFICIAL SIC TABLE + AUTOMATIC CIQ-GICS OVERLAY + DUPLICATION

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **`vinci/sic_table.py` (vendored):** the full official SEC SIC code list — 444 codes, public
    domain, VERBATIM titles (incl. the SEC's own 2836 "DISGNOSTIC" typo; URL + retrieval date
    2026-07-20 in the docstring). Regenerate by re-fetch, never hand-edit.
    `industry_for_sic` now reads it (display-cased deterministically); the hand-rolled ~80-bucket
    map (68 branches) is DELETED. `sector_for_sic` (the coarse grouping axis) is UNCHANGED.
  - **`vinci/labels.py`:** `resolve_label(sic, gics=…)` — precedence CIQ-GICS (present-only) →
    official-SIC → Unknown; **`sector` is ALWAYS the coarse bucket** (a manual CIQ pull must
    never reshuffle the per-sector spread grouping). `committed_gics_index()` reads the committed
    dossier tree (10 names). Rerouted: the rank WRITER (cli.py — rank/screens stay pure; the AST
    fence now also forbids `vinci.labels`/`vinci.sic_table` there), assemble sector, ledger
    sector, theme member rows (NEW `ThemeMember.industry`, default-None round-trip).
  - **THE MODULARITY (the operator's ask):** a future CIQ profile pull → dossier commit →
    `build.py` emits the GICS label into `frontend/dossiers/index.json` `labels` → the ranker
    (and any future consumer) upgrades that name AUTOMATICALLY. Zero per-surface edits. Verified
    live: VRRM's ranker Industry reads "Data Processing and Outsourced Services ·CIQ" (provenance
    mark + source_ref title) while non-dossier names read official SIC titles unmarked; the
    filter matches the DISPLAYED label. Why not GICS-for-all: CIQ is manual/licensed depth-stage
    (~1,800 pulls or a licensed feed the repo deliberately avoids) — operator-decided.
  - **Radar hint (was Mech-C `_SIC_NAME`, 22 hardcoded names DIVERGING from the ranker's map):**
    DELETED; `_industry_hint` now aggregates resolver-attached `member.industry`. Pre-field
    component-a snapshots degrade to raw `SIC <code>` + ONE loud build note (self-heals on the
    next sweep — the current snapshot predates the field). A name is never fabricated.
  - **HIGH-1 LIVE DRIFT FIXED — radar decision vocab:** the analyst record mixed `park`(×10)/
    `parked`(×27) and `reject`(×1)/`rejected`(×6); the renderer knew only parked/rejected →
    unstyled pills AND the "Rejected only" filter SILENTLY DROPPED the `reject` row.
    `_CANON_DECISION` seam canonicalizes at EMIT (park→parked, reject→rejected — mapping recorded
    here verbatim); `reviews.json` (the analyst record) stays UNTOUCHED; an unmapped decision
    fails the build LOUD. Committed log.json regenerated: parked 37 / rejected 7 / advanced 1 /
    watch 1; "Rejected only" now returns 7; zero unstyled pills.
  - **Queue artifact (labels-only refresh, SEPARATE artifact commit):** 274/275 rows upgraded to
    official titles ("Other/Other"→"Other/Services-Management Services" for IT). VERIFIED zero
    non-label field diffs (ranks/scores byte-identical — as-of discipline, no re-rank) and ZERO
    sector changes.
  - **Duplication closeout (2026-07-20 audit; operator scope: HIGH fix + cheap MED + pin rest):**
    FIXED — MED-7 (ONE workflow-state vocab: snapshots.js `WORKFLOW_STATES`, ranker imports it),
    MED-8 (ONE bar: scenarios re-exports midcycle's BAR — the judge-vs-stamp split is gone),
    LOW-11 (uw-card renders the RECORD's bar/basis; absent → honest DASH, never an invented 2).
    PINNED (tests/test_parity_pins.py, one test each) — MED-3 tier-bucket trio, MED-4 ranker
    weights py↔JS, MED-5 screen-gate prose vs thresholds, MED-6 power floor vs forward.py,
    LOW-9 _SCAN_BASIS vs ExposureBasis (genuine bases; UNASSESSED_ERROR deliberately excluded),
    LOW-10 reserved slugs vs the app.js normalizer. Plus: index `labels` ↔
    `committed_gics_index` parity pin; decision-vocab ↔ radar.js DECISION_LABEL source pin;
    `_SIC_NAME`-dead tombstone pin.
  - **ACCEPTED RISK / FLAGGED, not fixed (scope):** (a) `_SCAN_BASIS.get(…, "none")` maps an
    `unassessed-error` basis into the "none" tier count if one ever reaches `_theme_display` —
    possibly conflating a scan FAILURE with genuine no-exposure; whether unassessed rows can
    reach that counter needs a check → QUEUED. (b) The web ledger view still doesn't display
    `LedgerEntry.sector`. (c) The JS overlay precedence (`dispIndustry`) is the one unavoidable
    stdlib-fence twin of `resolve_label` — source-pinned, residual drift risk accepted.
  - **Operator decisions recorded:** #109's Brief trim REAFFIRMED (GICS not re-added to the
    Brief — it surfaces via the ranker overlay); official-SIC-table architecture chosen over
    GICS-for-all and over keeping the hand-rolled buckets.
  - Gate: ruff + `mypy --strict` + full offline pytest green (+11 new pins). Build ×2 idempotent.
