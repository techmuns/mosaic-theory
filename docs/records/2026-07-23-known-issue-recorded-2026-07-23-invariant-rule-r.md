---
id: 
status: recorded
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**KNOWN-ISSUE (recorded 2026-07-23, INVARIANT RULE) — re-assembly can flip a cap-band benchmark.**
Re-assembling IT flipped its benchmark MDY→IWM (cascading to `stock_performance` + the idio
comparison + the What-broke chart) — the cap→band→benchmark assignment is data-sensitive near a band
boundary (or store-state dependent), so a fresh assembly of a borderline name can silently change
which index it's judged against. Mitigation used: a single-field surgical patch when only a derived
field needs updating. FALSIFIER/next: pin the benchmark to the screen-time cap band (store it on the
record) so dossier re-assembly can't reselect it. **RESOLVED 2026-07-24 — see the build record
immediately below (the pin already existed on the ranked-queue row; the dossier now reads it).**
