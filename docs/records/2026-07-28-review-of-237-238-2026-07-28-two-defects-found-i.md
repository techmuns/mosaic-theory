---
id: 
status: shipped
date: 2026-07-28
prs: [237, 238]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**REVIEW OF #237/#238 — 2026-07-28, TWO DEFECTS FOUND IN MY OWN 17b CODE AND FIXED BEFORE MERGE.**
(1) **THE MARKER DID NOT MATCH THE SPEC.** The operator's rule was "any row that TRIGGERS THE
GUARD"; the guard reads the LATEST column, but `mark_material_rows` took `max(|v|)` across EVERY
column. Result: rows promoted to the brief on HISTORY the guard never fires on — **MVST** (LTM
−36.6 = 8.7%, below the floor, flagged off a −93 two years earlier) and **VRRM** (latest column
empty, flagged off an older −97). Precisely the "not every $2M restructuring line" noise the brief
was told not to accumulate. Fixed by resolving the guard's own period in the ASSEMBLED table
(`_latest_actual_index`: LTM, else last non-estimate) — the two indexings differ, and matching the
PERIOD rather than the index is what keeps "flagged for the brief" and "fires the guard" one
predicate. Post-fix the flagged set is exactly SMPL + CNXC, matching the guard. Regression pinned
with the MVST shape.
(2) **THREE COPIES of the brief's core row set** (render.py, assemble.py, dossier.js), two of them
introduced by 17b, with NO pin — the duplication class `test_parity_pins.py` exists for. Per the
repo's own rule ("where a single import IS possible the repo does that instead"), the two PYTHON
copies collapse to one: `render.BRIEF_CORE_ROWS`, imported by assemble. The JS copy cannot import
it, so it is PINNED (`test_brief_core_rows_py_js_parity`), mutation-tested by dropping a label
from the JS side. Drift matters more than usual here because the guard's satisfying set is
CORE ∪ MATERIAL — a label missing on one side silently narrows what counts as "the reader met it".
ALSO CHECKED, no defect: the promoted-row-blank-in-the-brief-window risk does not materialise on
any of the twelve (every flagged row has a value inside the displayed window); #237 carries no
secrets and no licensed CIQ content. Gate: ruff + `mypy --strict` clean · **1129 passed**.
