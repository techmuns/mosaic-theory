---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 D3 HYBRID ordering — the bull case leads with its thesis, the bear
case keeps survival-first (branch `feat/d3-hybrid-ordering`, ratified on evidence).** DIAGNOSIS
(operator feedback "this bull point should rank lower / this bull is a bear"): D3's tier was a
FIXED TOPIC hierarchy (solvency→revenue→margin→competitive→valuation), not per-name materiality —
empirically, 19 of the snapshot's 22 lists opened tier-1, the bull side led with the balance-sheet
ENABLER on 9/11 names while the name's own decisive question was a demand/margin/growth question on
10/11; within-tier order was emission (citation key ~mute at 133/31/0); 19% of points sat
UNCLASSIFIED at 4.5; and one K6 regex alt fired tier-1 on ANY parenthesis near "adjusted EBITDA"
(SMPL's bear lead was T1 by the "(" of "(-460bps)" — accidental). RATIFICATION EVIDENCE: a Phase-1
preview (no code changed) ran baseline vs crux-first (A) vs tier-first (B) on the committed 11 +
then across the FREE weather archive git history already holds — **119 distinct historical
synthesis draws, 238 lists** (dedup by synthesis hash). Bull-enabler leads 82→0 under every
variant; lead-crux 74→219(A)/173(HYBRID)/143(B); **A demoted a T1 survival fact below a narrative
crux point in 22/119 draws across 10/11 names (structural, not weather)** — VITL 3/6 draws worst;
crux-ref fuel stable (mean 31%/list, 8% zero-overlap degrading gracefully). Paid same-prompt
re-runs adjudicated NOT NEEDED: every comparison's ordering was already unambiguous. SHIPPED (the
hybrid): `_ordered_points(pts, side=, crux_refs=, driver_refs=)` — bull key (crux, side-rank,
mech, cite, emission); bear key (side-rank, crux, mech, cite, emission); side-aware ranks
bull 2→3→1→4→4.5→5 / bear 1→2→3→4→4.5→5; crux = SAME-SIDE decisive-question evidence ref overlap
(rule-2 verbatim refs make it deterministic); mech = operating-driver ref overlap; K6 "(" alt
narrowed to `\(\s*\$` (accounting-$ only). JS twin mirrored (`orderPoints(pts, side, cruxRefs,
drvRefs)` + `decisiveRefs`/`driverRefs`); dev tags gain `· crux`/`· mech`. Verified: md real-run
(SMPL bull #1 balance-sheet → Quest/OWYN mechanism; IT → the contract-value turn; VITL bear #1
STAYS cash-burn — the guarantee on the exact name A demoted) + live web (Brief ≡ Analysis ≡ md,
console clean; the stall was the fresh worktree's missing git-ignored `frontend/snapshots/`,
symlinked). Gate: ruff · mypy --strict (110) · **1055 offline passed**. INVARIANT pins: the
synthetic hybrid fixture (bear survival-first guarantee, crux/mech tiebreaks, enabler demotion) +
the living-artifact e2e relayered to phrasing-independent hybrid invariants (bear rank monotone +
crux-prefix in runs; bull crux-prefix + rank monotone within groups; py==JS on the same refs) +
fix-4 pins on the real SMPL "(-460bps)" shape. Face-validity throughout — nothing outcome-tuned.
POST-MERGE: the committed .md/frontend artifacts still carry the OLD order until the standing
artifact pass re-renders them (re-render only, no re-assembly needed).
