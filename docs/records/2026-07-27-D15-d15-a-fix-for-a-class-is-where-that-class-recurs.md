---
id: D15
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D15. A FIX FOR A CLASS IS WHERE THAT CLASS RECURS — third instance, recorded as a pattern**
(operator, 2026-07-31). `refresh_record` froze the `basis` while moving the value, which would have
left "diluted weighted-average (latest 10-Q)" over a number that is neither weighted nor an
average — **the mislabelled-denominator defect, inside the writer built to remove it.** Prior two:
`current_guide` gave IT's fabricated boilerplate a decision surface while fixing the guidance
surface; the period tie-break shipped a cumulative-vs-quarter selector inside the work correcting
share-count basis. **Why it recurs:** a fix touches exactly the code that reasons about the flawed
concept, so the flawed reasoning is nearest to hand; and the author is in "I have understood this"
mode precisely where scepticism is cheapest to skip. **THE CHECK, on any fix:** re-read the fix
asking whether it commits the defect it names — before the tests, because a test written by the
same understanding inherits it. Add to the review pass, not to a doc nobody re-reads.
(Companion instance the same day: the `ratio == 3.83` pin was the TEST-LAYER RULE case caught by
its OWN sibling assertion, and the first rewrite still let a `passFail: "PASS"` hardcode through —
**two attempts to get a pin that tests transport rather than coincidence.**)

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
