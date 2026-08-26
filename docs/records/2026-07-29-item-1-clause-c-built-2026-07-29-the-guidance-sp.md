---
id: 
status: shipped
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**ITEM 1 CLAUSE (c) — BUILT 2026-07-29 (the guidance SPLIT). P2 CLOSES IN CODE — 3 OF 13 — BUT NO
ARTIFACT CARRIES IT YET.** Stated with the qualification deliberately (operator): `current_guide`
is None on every committed dossier because they predate the field, so **a reader does not meet it
until a re-assembly runs**. Same distinction that made P1 pt1 real only once SMPL and CNXC showed
the surfaced row — code-closed and reader-closed are different states, and the count says which.
**THE MECHANISM WAS NEITHER PARTY'S.** The audit named the CIQ Guidance sheet's prose cell (no CIQ
sheet is involved); I proposed max-date selection (which would have BROKEN the drawdown field). The
operator read `_revised_guidance` and its docstring settles it: *"Follow the furnished 99.1 exhibit
ON THE DRAWDOWN 8-Ks … and surface … THE VERDICT-RELEVANT NUMBER."* Both readings in one sentence,
diverging exactly when guidance is revised after the drawdown. **One function was trying to be two
things**, so it is now two: `drawdown_cause.revised_guidance` (unchanged construction, renamed
"Guidance at the drawdown (8-K 99.1)") and `primary_source.current_guide` (latest results filing,
no dependence on a price event).
**PER-NAME GATE: 11/11 get a current guide; SEVEN go from NO guidance block at all to having one**
(AORT, CNXC, EPAM, FUBO, IT, MVST, NCNO). **A fix motivated by SMPL that changes seven other names
more than it changes SMPL** — the generalisation goal, demonstrated rather than asserted.
**`filed` VERIFIED ON THE REAL EXTRACTION PATH, not synthesised** (operator asked): EDGAR returns
`…-26-000021 → 2026-07-09` and `…-26-000010 → 2026-04-09` for SMPL, so the July filing really is
newest and the selection has the dates it claims.
**SELECTION IS PINNED AGAINST BOTH WAYS OF GETTING IT WRONG** — by POSITION (fixture ordered so
`[0]`, `[-1]` and `max(filed)` are three different answers) and by DRAWDOWN SCOPE. Mutation-verified:
`dated[0]` reds it. Test count moved 1163 → 1167; the operator caught that it had NOT moved on the
first cut, which is the standing "every fix ships with a behavioural red" doing its job.
