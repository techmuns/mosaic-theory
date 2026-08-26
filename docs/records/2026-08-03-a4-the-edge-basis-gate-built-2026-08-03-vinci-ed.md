---
id: 
status: shipped
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**A4 — THE EDGE-BASIS GATE, BUILT 2026-08-03. `vinci/edge_basis.py`, wired into
`cli._cmd_log_verdict` BEFORE the ledger write.** No verdict without one of six bases picked
explicitly. **SILENCE REFUSED, AGREEMENT ALLOWED** — five of the six say "no variant" out loud and
are fully valid, because a gate that accepted only a variant claim would manufacture views to fill
a field, and **a fabricated gap is worse than an honest none**: it survives into the ledger, the
spread and every retrospective wearing the same shape as a real one.
**THE ESCAPES ARE THE MAJORITY PATH, NOT A COURTESY: 8 of 11 committed names cannot state a variant
today** (5 no record, 3 R2). The refusal message therefore LISTS the five alternatives — a bare
refusal would teach the operator to type `variant-expectation` and invent a number, which is the
defect the gate exists to prevent, manufactured by the gate.
**OPTION 1 IS SATISFIED BY A STATED TOTAL GAP**; where routing sends the decomposition away the
line reads *"total gap 1.42x — attribution suppressed: coverage n=3, form two-ratio"*. **Option 6
is a SLOT ONLY**, rendering *"analyst-asserted, machine verification pending"* until A5 exists — a
slot that read as verified would be false confirmation, worse than not offering it.
**SHOWN RUN ON THE REAL DECISION PATH** (scratch DB copy; the real ledger is untouched):
· silence → REFUSED, listing all six · `variant-expectation` on a name with no gap → REFUSED,
naming the alternatives · `variant-expectation` on SMPL → **"Variant expectation stated — total gap
2.10x, decomposed"** · `valuation-asymmetry` on AAUC → **LOGGED**, and read back out of the
append-only row: `[edge: No variant; valuation asymmetry at this price · reward:risk 3.1:1 at
12.40]`.
**SEALED INTO THE THESIS** with an `[edge: …]` prefix — the ledger row has no field for it yet, and
a prefix is machine-findable later without parsing prose. **THE GATE READS THE COMMITTED ARTIFACT,
never a fresh computation**: the question is what the human could POINT AT when they decided, and a
recompute could pass a verdict the page in front of them did not support. Both pinned structurally.
Gate: ruff + `mypy --strict` clean (118 files) · **1733 passed, 3 skipped**.
