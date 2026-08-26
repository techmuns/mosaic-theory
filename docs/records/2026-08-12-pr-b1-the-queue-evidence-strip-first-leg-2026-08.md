---
id: 
status: recorded
date: 2026-08-12
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

### PR-B1 — THE QUEUE EVIDENCE STRIP, first leg (2026-08-12)

The approved plan's Phase B: the queue says WHERE a name ranks but never whether anyone is DOING
anything — issuing stock, buying, shorting. The 2026-08-12 panel killed the price-based answer
(every trend state was one 2025–26 regime measured nine ways), so the strip renders POSITIONING,
one evidence-backed leg at a time.

- **Shipped:** `vinci/evidence.py` (the composer), `RankedCandidate.context`, an `Evidence` column,
  and the fence. Two legs: **net share issuance over ~2y** (Pontiff-Woodgate; the bullish twin of
  the dilution demote) and **distance off the 52-week low** — computed since day one and consumed
  by nothing until now.
- **FREE, not new plumbing.** `enrich_with_fundamentals` ALREADY fetches `companyfacts`, so the
  share series costs no extra network. `Fundamentals.share_count_change_730d` is defaulted, so
  pre-2026-08-12 snapshots still load and read UNKNOWN until a re-screen.
- **ONE implementation of the share-count change.** The window selection was inline in
  `_dilution_spiral`; it is now `vinci.edgar.concepts.share_count_change`, consumed by BOTH the
  demote and the strip. Two computations of one quantity would agree today and diverge on the first
  edit — the twin-drift class this repo keeps finding. Pinned by AST.
- **THE FENCE.** `vinci.rank` and `vinci.screens` must not import `vinci.evidence` — same shape as
  the sector/label fence, and for the same reason: presented context that reaches a weight becomes
  an unvalidated signal driving the queue. The strip is composed by the WRITER, after ranking.
- **DELIBERATE DIVERGENCE FROM THE PLAN:** the plan's price tail listed drawdown. The queue's
  `Depth (52w)` column already shows it, so printing it twice would make a dense table worse and
  let two copies disagree. Distance-off-low ships alone. Pinned.
- **DORMANT UNTIL THE NEXT SCREEN**, like `volume_trend` before it: the field is computed in
  assemble, so it appears when the weekly job next re-screens. The cell degrades to a dash.
- Four guards mutation-tested: the scorer importing the strip, the dilution leg re-deriving its own
  window, the helper inventing a flat 0.0 instead of UNKNOWN, and the drawdown returning.

**STILL OPEN — the two expensive legs, deferred with their costs measured, not hand-waved:**
- **Insider buys/sells.** A real Form 4 parser already exists (`mechanical._form4_codes` →
  `Form4Line`, with `compose_insider_line` split out as a pure function) and its discipline is
  right — P and S never netted, F excluded. But `_INSIDER_SCAN_DAYS` is 1095 and `_form4_codes`
  fetches per accession, so at screen scale that is ~40–120 fetches × ~283 names on a cold cache.
  The submissions JSON is shared with the structural scan (one fetch, not two), and Form 4 docs are
  immutable so later runs are cache hits — but the first run adds materially to a job that now takes
  ~35 minutes, and `data/cache` is already 2.8 GB against Actions' 10 GB ceiling. **A filing COUNT
  without direction must not ship as a substitute** — most Form 4s are grants and withholdings, so
  an undirected count would be the "heavy distribution" mistake again.
- **Short interest.** `vinci/finra.py` exists and is layout-pinned, but it is a NEW external service
  called once per name — a fresh dependency on the weekly cron.
