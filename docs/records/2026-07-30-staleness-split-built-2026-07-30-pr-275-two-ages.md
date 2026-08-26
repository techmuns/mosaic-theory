---
id: 
status: shipped
date: 2026-07-30
prs: [275]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**STALENESS SPLIT — BUILT 2026-07-30 (PR #275).** Two ages wore one number and only one is ours.
**EXPORT staleness** (we have not pulled) gates the build; **CONSENSUS staleness** (no analyst has
revised) prints, caveats past the SAME ceiling, feeds the neglect screen, and never gates.
**THE LIVE CASE:** AORT's Estimates workbook was re-exported 2026-07-30 and still reads 2026-06-30 —
30 days of "staleness" counting toward a breach no operator action could prevent.
**MEMBERSHIP IS MEASURED, by each node's own source_ref, not by name:** `catalyst_path.as_of` and
`financial_summary.as_of` both stamp from *CIQ Estimates→Recent Changes*, and
`implied_expectations.multiples_as_of` is assigned from `catalyst.as_of` in code — so all three are
CONSENSUS. `tev_as_of` (Comparable Analysis→Financial Data) and `stock_info.as_of` (EOD store) are
EXPORT. **`financial_summary` is the trap the category-label rule predicts** — the NAME says
Financials workbook, the STAMP is the Estimates event.
**FLEET EFFECT, measured before building: exactly ONE name changes gate outcome** — MVST, refused at
56d (consensus) against 16d of export age. No name newly fails; a corpus pin asserts the list is
`["MVST"]` alone and that no name's export age can exceed its merged age (which would mean an export
panel was misclassified and the gate weakened). `panel_age` now takes a **mandatory `kind`** — no
default, because a default would let a caller keep the merged meaning while the constant beside it
says the classes differ. Both call sites had to state which; five test sites surfaced the same way.
**RE-RENDER ONLY, verified:** panel age is not persisted (no such field in `dossier.json`) — it is
computed at `assemble.py:219` for the gate and `render.py:3182` for the page, both from stored panel
dates, so 11 names re-rendered from committed JSON with no re-assembly and no LLM. Mutations: gate
reads consensus → 2 red · `consensus_note` raises → 1 · `financial_summary` reclassified → 5 ·
consensus line dropped from the page → 1 · own 90d threshold → 2.
