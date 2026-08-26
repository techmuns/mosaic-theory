---
id: 
status: shipped
date: 2026-08-17
prs: [460]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**ITEM 20's `(latest)` FAMILY IS REOPENED 2026-08-17 (#460) — AND IT CANNOT BE CLOSED BY
REWORDING.** #459 dated the multiples stamps (`Close (latest)` → `Close [ISO]`); #460 REVERTED
all four strings. **Cause: a mechanical `source_ref` is a JOIN KEY, not display text.** An LLM
synthesis point cites evidence by copying the string verbatim into `SourcedPoint.source_ref`;
`synthesis._traces` matches exact/substring, and both renderers dedup endnotes by exact
string. So the reword **broke 8 sealed citations across 7 names** — each keeping `cited: true`
while resolving to nothing, since `_validate` only runs in the LLM path — and **forked
EPAM/IT/UBER's CIQ endnote into two contradictory entries.** `moved_cited_claims` did not
refuse: its grain is moved FIGURES, not moved strings.
  **THE REVERT COST THE READER NOTHING**, which is why it was the right trade: neither renderer
  emits `valuation.ev_ebitda`, so `Close [ISO]` reached **0 of 14 pages**, while
  `range_position` already prints a real `as-of <date>` on all 14. The structured date stays
  available to code via `ev_ebitda_asof`. Precise-but-unresolvable lost to imprecise-but-bound.
  **INVARIANT SHIPPED (INVARIANT RULE):** `tests/test_multiples_vintage.py::test_the_multiples_stamps_are_frozen_because_they_are_join_keys` asserts every committed
  dossier's synthesis citations TRACE into its own mechanical layer — the property the reword
  violated, phrasing-independent, so it fires on the next author who edits these strings
  without re-rolling synthesis. It was RED on the un-reverted artifacts and is green now.
  **UNLOCK:** key provenance by a stable id with the display string DERIVED from it; then the
  wording is free to change. Until then these strings are frozen and the item stays open.
