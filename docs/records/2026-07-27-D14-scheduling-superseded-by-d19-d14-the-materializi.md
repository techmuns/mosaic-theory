---
id: D14
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
split-from: 2026-07-27-D5-d5-three-names-have-a-zero-dilution-delta-and-th.md
date-source: UNKNOWN — not recoverable from the header or git; do not read as fact
---

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
