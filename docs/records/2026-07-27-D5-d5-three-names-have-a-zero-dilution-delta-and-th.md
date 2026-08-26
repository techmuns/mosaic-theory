---
id: D5
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D5. THREE NAMES HAVE A ZERO DILUTION DELTA AND THAT MUST PRINT, not silently no-op.** FUBO, SMPL
and VITL tag basic == diluted for the latest quarter, so the overlay returns the outstanding count
unchanged. FUBO is correct accounting (a loss makes dilution antidilutive); SMPL and VITL are the
filer's tagging and are NOT self-evidently right for a profitable name. The page must say *the
filer reports no dilutive difference in this period*, never leave a reader to infer we checked and
found none — item 22's visible-absence rule applied to the denominator.

*(scheduling superseded by D19.)* **D14. THE MATERIALIZING-WRITE ACCEPTED RISK HAS ITS FIRST LIVE INSTANCE — and its falsifier did
NOT fire.** #284's re-render of MVST added **79 schema-default keys, 0 changed, 0 removed** — the
exact event the 2026-07-27 acceptance predicted ("the NEXT programmatic write of a migrated record
will materialize `role: null / leg: null / excluded: false` on every untagged reference"). The
falsifier is "if a materializing write ever changes a VALUE (not just adds a null key), the
acceptance is void and the write path gets a byte-preserving mode" — **verified key-by-key: nothing
changed, nothing was removed, so the acceptance stands.** Recorded as the instance the queued
**`migrated` third-state** item exists to describe, now live rather than hypothetical: MVST's
`extraction_version` claims one shape while its structure is another, and no field says so.
Instance noted against the item; NOT built.
