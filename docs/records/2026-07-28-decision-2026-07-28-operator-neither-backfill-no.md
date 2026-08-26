---
id: 
status: recorded
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**DECISION — 2026-07-28 (operator): NEITHER BACKFILL NOR SIDECAR. The legacy rows render an
EXPLICIT "no structured source for this decision vintage".** Both options I flagged were REJECTED,
and the reasoning is the part that must survive:
· **NOT BACKFILL.** Adding structured fields to a sealed V-row is additive but still EDITS A
DECISION OF RECORD to satisfy a guard written afterwards. The seal is the point.
· **NOT A SIDECAR EITHER — the less obvious rejection, and the more important one.** A sidecar
carrying `loan_basis: 1.2x` beside a sealed thesis that already states it in prose creates **TWO
COPIES OF ONE FACT THAT CAN DRIFT**. That is the GENERATOR OF EVERY DEFECT IN THIS AUDIT — anchor
block vs reference row, web chip vs md render, the record's three triggers vs the dossier's one.
Solving a divergence problem by adding a second source of truth is the wrong direction, and the
`_amendment_index.json` precedent does not outweigh it.
· **THE THIRD OPTION, AND IT IS NOT A COMPROMISE.** 18a binds forward; the guard treats a
pre-schema row as **"no structured source for this decision vintage"** and RENDERS THAT, rather
than UNKNOWN. This is item 22's visible-absence rule applied consistently: the absence is TRUE,
VISIBLE and ATTRIBUTED, which is exactly what separates it from a false UNKNOWN.
· **WHY THIS IS COMFORTABLE, NOT MERELY TIDY:** the exposure is THREE rows, all closed or avoid,
with the facts recoverable from filings regardless; and **the gap SELF-HEALS** — SMPL is
re-underwritten at the October print and its new V-row is written under the 18a schema.
**Recorded as a DECISION with its reasoning so the next session does not re-open it.**
