---
id: 
status: recorded
date: 2026-07-28
prs: [238]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-28 P1 BRIEF FIX (item 17b, operator-blocked #238 until done).** P1 was
NOT closed by surfacing. The operator's blocker, accepted in full: *P1 was never "the writedown is
absent from the data" — it was that a DECISION-MAKER reads the dossier and never meets a charge
worth 43% of market cap.* With both brief snapshots filtering on a STATIC label whitelist, the
surfaced row landed in the APPENDIX only: guard passing, record complete, **harm substantially
intact**. That is the same family as a guard that cannot fire — the acceptance condition did not
match the harm — so it was fixed on the branch rather than deferred. THREE CHANGES: (a) `FinRow`
gains a structural `material: bool = False`, set ONCE at assembly where the market cap lives —
neither renderer recomputes the threshold, because a second copy of that arithmetic in two twins
is the parity hazard this repo keeps closing (default False round-trips every committed
dossier.json); (b) BOTH brief whitelists become DYNAMIC — static labels **∪ any row flagged
material** — so it is not every $2M restructuring line, only rows over the floor; (c) the GUARD'S
TARGET SURFACE MOVES TO THE BRIEF: its satisfying set is CORE ∪ MATERIAL, so an appendix-only row
no longer silences it. VERIFIED END-TO-END on real bundles: SMPL flags `Asset Writedown ($M)` and
CNXC flags `Impairment of Goodwill ($M)`, each brief going 8 → 9 rows; AORT and FUBO flag nothing
and stay at 8 — no noise on names without material one-offs. The web needs no emitter change: the
`frontend/dossiers/` mirror copies the mechanical layer verbatim, so the flag rides through. RED
(operator's, shipped): a >10% charge present in the table but absent from the brief FAILS the
build — and the old appendix-only set is asserted still-passing beside it, so the regression is
explicit rather than implied. Gate: ruff + `mypy --strict` clean · **1128 passed** (+2).
