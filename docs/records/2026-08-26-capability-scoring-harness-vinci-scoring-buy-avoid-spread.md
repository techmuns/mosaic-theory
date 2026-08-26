---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **Scoring harness** (`vinci/scoring`) — BUY−AVOID spread = `buy_mean_return − avoid_mean_return`

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **Per-sector spread enabler — verdicts sector-tagged at log time (built 2026-06-22).** Every
    `LedgerEntry` now carries a `sector` (coarse GICS-like, `vinci/sectors.sector_for_sic` over the
    EDGAR SIC the resolver already provides — **NO new data source**), captured + frozen at log time
    like the entry price, never derived later. `log_verdict` resolves the SIC via the resolver
    (`Identity.sic` is not populated on candidates) through a `SicSource` Protocol that keeps the
    ledger decoupled + testable; `sector` rides in the entry payload JSON, so **no SQLite migration**.
    **Behavior note:** this adds one **cached** EDGAR `submissions` lookup at log time (1-day TTL) —
    logging a verdict (previously fully offline) now needs that fetch to succeed; fail-loud if it
    can't, consistent with the ethos. Not a real-candidate blocker: the operating-co gate guarantees
    every candidate has a CIK (VRRM resolved SIC 4700 → Industrials live); only CIK-less benchmark
    ETFs would raise, and those are never candidates.
    The harness reads it: `scoring.spread_by_sector` returns a per-sector BUY−AVOID spread that is
    **`sufficient=False` ("insufficient data") until a sector has ≥2 resolved BUYs AND ≥2 AVOIDs** —
    honest emptiness, never a spread off a one-name leg; `ScoreReport.by_sector` + the report markdown
    surface it. **VRRM (logged 2026-06-21, pre-feature) reads back `sector=None` — the immutable entry
    is NOT rewritten;** it is the one untagged verdict and buckets under "Unknown" (no backfill, no
    silent edit — the honest option (b)). *Verified: `sector_for_sic` maps 7372→Technology,
    2834/3841→Health Care, 1311/2911→Energy, 6022→Financials, 6798→Real Estate, 5812→Consumer
    Discretionary, blank/None→Unknown; a logged verdict carries + round-trips its sector; the real
    ledger's per-sector read is empty (0 resolved) honestly. +2 tests (a verdict carries its sector;
    the spread groups by sector + stays insufficient until both legs are real, untagged→"Unknown").
    ruff + `mypy --strict` clean; suite green.* This is the cheap enabler the §6 sector-expertise
    scoping question needs **in place before data accrues** — the scoping DECISION stays open + data-
    gated (§6).
