---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

14. **THE FIRST INSTRUMENTED RECORD-WRITE PATH — `vinci scenario-refresh` (2026-07-27).**
   `write_record()` previously had **ZERO programmatic callers**: every record edit in this repo's
   history was hand-edited JSON, including the 2026-07-24 SMPL machine refresh — which is exactly
   *why* that refresh ended up narrated inside a sealed rationale. There was nowhere else to put
   it. `scenario-refresh` is now the one path for changing a record's MACHINE inputs (spot +
   the six refreshable facts): it recomputes through the engine, appends a `refresh_log` entry per
   field with old → new and a REQUIRED source, and **refuses** any analyst surface — an
   analyst-owned input is not expressible, and legs/assumptions/verdict are asserted unchanged on
   the way out. Hand-editing remains physically possible; it is now the exception, not the norm.
