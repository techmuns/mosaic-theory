---
id: D13
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
split-from: 2026-07-27-D15-d15-a-fix-for-a-class-is-where-that-class-recurs.md
date-source: UNKNOWN — not recoverable from the header or git; do not read as fact
---

*(scheduling superseded by D19.)* **D13. `diluted_shares` NOW MEANS TWO DIFFERENT THINGS IN TWO ARTIFACTS** (review finding on #284,
QUEUED — not fixed here). After item 24 the **record's** `facts.diluted_shares` is a valuation-date
OUTSTANDING count while the **anchor's** `anchor.diluted_shares` remains the latest quarter's
WEIGHTED AVERAGE. On SMPL a reader sees 89,940,680 in the anchor block and 88.460545M in the
underwrite table, 1.6% apart, same field name, no cross-reference. **Nothing breaks:** all three
consumers (`tagger._leverage`, `audit_r1.check_leverage`, `audit_r1.check_entity`) read the ANCHOR
only, and `check_entity`'s diluted-vs-outstanding gap stays meaningful precisely because the anchor
did not move. Both fields carry their own `basis` string, so the surface does distinguish them —
but only to a reader who reads both. **The anchor's weighted average is CORRECT for what it is** (a
spot-independent attention filter), so the fix is disclosure, not alignment: state on the anchor
basis that it is a PERIOD average rather than a valuation-date count. Deferred because it rewrites
a basis string on all eleven committed anchors — its own artifact pass, not a rider on this one.

**ALSO VERIFIED, and it was clean:** the write fed `diluted_outstanding` from an ad-hoc
`max(points_for_tag(...))` rather than the pipeline's own `_edgar_shares_outstanding` — two paths to
one quantity, the twin-drift shape. Measured 7 of 7 on the committed names: **identical**. No value
is wrong; the module should still be fed by the pipeline function when it is wired into assembly.
