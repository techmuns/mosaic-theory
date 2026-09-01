---
id: 
status: recorded
date: 2026-08-11
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**EXPERIMENT RECORD — 2026-08-11 price-state falsifier (pre-registered; MEASURE-AND-KILL, nothing
promotable).** Operator asked whether technicals (50/200d MA, RSI) should join the pipeline as
supportive flags. Web research first (recorded in the approved plan): MA-rule profits are
data-snooping that dies out-of-sample (Bajgrowicz-Scaillet 2012); 3–12-month losers CONTINUE to
lose (Jegadeesh-Titman) — the queue's measured ~−1 pt/mo sector-relative drag is what the
literature predicts; the strong-evidence answers to "is anyone buying / is it terminal" are
POSITIONING, not price: insider buys (Cohen-Malloy-Pomorski 2012), short interest
(Rapach-Ringgenberg-Zhou 2016), net issuance (Pontiff-Woodgate), Piotroski F-Score (2000) — the
first three already computed at dossier level (docs/EDGE_THESIS.md "inflection" legs), none at
queue level. Falsifier run (`scripts/price_state_falsifier.py`; report on the operator desktop,
`ranked-queue-price-check/price_states/`): loader sanity gate reproduced the independent
sector-relative sweep to 0.000 pts on 3 months. RESULTS — 200d-MA filter degenerate (R1 DEAD);
RSI null; waiting-for-reclaim FREE (my pre-registered expectation that deferral costs the bounce
was WRONG: winners earned 98% of gains AFTER the 50d reclaim); early-recovery vs still-falling
separates at 120–180d (record-only; replicable momentum continuation; unpromotable per operator
rule — price never moves a rank). **AMENDED 2026-08-12 BEFORE MERGE: the 50d-MA-slope facet of
that residue is SPECIFICATION-FRAGILE — its continuous twin fails the same phase split the binary
passed, and a 28-state panel shows every trend state is one 2025–26 regime measured many ways
(correlations 0.71–0.86). R3 cost-of-waiting and the R1/RSI nulls are unaffected. Full amendment in
§3.** Falsifications recorded in §3; operator ruling appended to the
§ "Fundamental vs quant" bullet. NEXT (approved plan): PR-B1 queue "evidence strip"
(insiders / short interest / share-count direction + price tail, display-only, AST-fenced),
PR-B2 dossier twin, Phase C F-Score display pending separate operator green-light.
## Amendments

**2026-09-01 — the "NEXT (approved plan)" line above is STALE and must not be acted on.** Both of
its remaining items were closed on 2026-08-12/13; the work sat unmerged on
`feat/dossier-evidence-line` and is recorded now.

- **Net issuance (Pontiff-Woodgate) is NOT strong evidence in this pool — FALSIFIED.** rho
  −0.023→−0.006, shuffle 98%→34%, MIXED at every horizon. The leg stays display-only and fenced.
- **PR-B2 (the dossier twin) is CLOSED as unnecessary, not deferred** — every leg of the strip is
  already a first-class, source-bound dossier fact in both renderers.

Record: `docs/records/2026-09-01-net-issuance-falsified-pr-b2-closed.md`. The wider screen-gate
audit that picks up the same thread: `docs/records/2026-09-01-screen-gate-audit-g1-g2-g3.md`.
