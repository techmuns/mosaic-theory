---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**ACCEPTANCE-RED POLICY CORRECTED (operator 2026-07-28) — THE RED MUST BE THE DEFECT'S BEHAVIOUR,
NEVER AN IMPORT ERROR.** #238's original red was `ModuleNotFoundError` on `2facc5e`, which proves
a FILE WAS ADDED — every new module produces it — not that the defect exists. Replaced with a pin
importing ONLY `ciq_sheets` (present on 2facc5e), running the REAL extraction path over the REAL
SMPL bundle: on 2facc5e it fails with an **AssertionError naming the missing line and printing the
eleven hand-named rows it is absent from**; here it passes. Same function, same input, different
output. This supersedes the acceptance clause as first written and binds every audit-derived build.
