---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**PR CADENCE CHANGED — 2026-07-28 (operator, reviewing the run: eight PRs, five docs-only). THE
RULES LIVE IN docs/engineering.md §PR cadence; THE CONSEQUENCE FOR THIS QUEUE IS AN ORDER.**
(i) **No more record-only PRs** — the record rides in the PR that implements what it records, one
PR per item. **#244 is the last of the class** (it is the amendment that adopts the rule).
(ii) **Batch by RISK, not size** — mechanical and independent go together; **guards and policy stay
SOLO** (19, 18a, 18, 1, 22), because focused review is what caught two gate omissions and one
incomplete fix on this run. (iii) **Topology first** — every branch currently conflicts at the
same insertion points, so re-sequencing is what makes batching cheap rather than merge-expensive.
**THE ORDER, FIXED (amended 2026-07-28 for the 26a/26b split):** `26a` **(ships next — LIFTS THE
FREEZE)** → **STATE topology (solo, ahead of the batch)** → **mechanical batch: 21 + 28 + 27a in
ONE PR** → `26b` → `19` scoping. Note STATE-topology is pulled OUT of the batch it was first
listed in; it precedes the batch precisely so the batch does not fight it.
