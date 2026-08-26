---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**PROCESS RECORD — 2026-07-24 existence-check protocol + house-vocabulary glossary (branch
`docs/vocab-and-existence-protocol`).** INCIDENT (twice): an agent asserted a capability was ABSENT
while it existed — the ranker's screen-time cap, then the D3 deterministic bull/bear ordering
(`render.py:_ordered_points`; the denial happened with `# D3 — deterministic tier order` in the
agent's own grep output). ROOT CAUSES: (a) generic-vocabulary search (rank/weight/materiality)
against idiosyncratic house terms (D3/tier/facts-first) read as proof of absence; (b) semantics
inferred from a call site without reading the definition; (c) the project's knowledge surface is a
chronological ledger (this file) + operator memory — no vocabulary bridge. FIX (deliberately
minimal, derive-never-dual-write): (1) CLAUDE.md existence-check rule — ≥2 vocabularies +
`git log --grep` + `-S` pickaxe + read surfaced definitions; report "not found under <searches>",
never "doesn't exist"; (2) CLAUDE.md coin-time translation rule — a PR coining a house term states
the plain-English equivalent in its squash title/body + one glossary line, by the coiner, in the
same PR (the only translation point that scales across concurrent sessions); (3) a ~25-term
glossary in docs/engineering.md §House vocabulary (translation table ONLY — explicitly NOT a
capability index; a curated index was CONSIDERED AND REJECTED: dual-write across concurrent
sessions guarantees gaps, and an index gap re-creates the false "not listed → doesn't exist"
inference with more confidence). Every glossary pointer verified against the code before commit.
ESCALATION (not built): a CI lint on squash titles only if the coin-time rule is violated in
practice — incident→invariant, applied to process.
