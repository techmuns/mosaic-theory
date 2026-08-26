---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

8. **INVARIANT-CHANGE CONSUMER SWEEP — RULE (standing, adopted 2026-07-27).** *When a data
   invariant changes, sweep every CONSUMER of it in the same pass; the invariant's own docstring
   is the first thing to re-read, not the last.* Root cause of #218's header defect: close rows
   shipped 2026-07-22 and broke the invariant "a ticker maps to at most one ledger entry" — which
   `frontend/build.py` had written into its docstring as a standing truth. The producer changed;
   the consumer kept asserting the old contract for five days, and the card silently rendered a
   closed position as an open BUY to an external reader. **The tell is a docstring stating an
   invariant the change just falsified** — grep for the assertion, not only for the field.
   *(Same class as #216: `dated_triggers` gained a consumer with no producer, four days after the
   producer shipped.)*
