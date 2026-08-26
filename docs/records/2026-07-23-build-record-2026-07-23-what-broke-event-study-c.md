---
id: 
status: recorded
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-23 What-broke event study (chart + ledger + true gap %s, operator-driven
redesign).** The What-broke section rebuilt to the institutional "share price & key events"
anatomy, from four operator critiques of the first chart preview (no axes; key wastes vertical
space; drops unquantified and partly invisible; section interleaved analysis into evidence).
ASSEMBLY (re-assembly of 10 names; MVST excluded — candidate_records absence — and stays the LIVE
back-compat case): (1) `stock_performance` DAILY (`_PERF_MAX_POINTS` 60→400 ⇒ 251 pts/52wk) — the
weekly downsample had SMOOTHED AWAY the very 1-day gap-downs the chart marks (CNXC's −11.2% Jun-30
was invisible) and made the true gap % unrecoverable (a weekly proxy misstated −12.7% as −21.7%);
(2) `DrawdownCause.gap_threshold/gap_window_days` (additive, default None) copied from the
now-PUBLIC screen constants — ONE source of truth, no frontend magic numbers; (3) 8.01 refinement:
anchored two-step (offering context → instrument) relabels a routine-8.01 gap from "other event" —
CNXC's Feb pair now reads **debt offering** (the $600M 6.5% notes; the mockup's "equity offering"
guess was WRONG — the anchored classifier read the filing). RENDER (both twins): gridlined chart
(nice-step y, four x dates), right-side EVENT LEDGER (№ · date · true 1-day % · cause · same-8-K
cross-refs), the % derived from consecutive DAILY points by the detector's own formula and OMITTED
(never estimated) on pre-daily JSON; detector-window boundary + HOLLOW markers for real ≤threshold
drops BEFORE the window (CNXC: Aug-1 −11.1%, Sep-26 −13.3% — real drops, honestly outside
coverage); marker stagger on adjacent-day collisions (②③); the three 180d tiles compressed to ONE
idio strip (chart shows the divergence; any absent leg → tile fallback); visible tier = driver
cards only (numbered to the ledger); item recitals → collapsed 8-K-detail provenance
(print-expanded per T1) cleaned of doubled titles / defined-term parentheticals (incl. multi-term)
/ cross-reference stubs; 9.01 filtered from items display (JSON keeps raw). VERIFIED: node renders
across CNXC (5 markers · 7 %s · boundary · 2 hollow · same-8-K · debt offering), SMPL/BRBR (stagger
+ hollow), MVST (markers, %s honestly omitted), NCNO (1 gap → one-liner; `stock_performance` ABSENT
in the STORE for NCNO — pre-existing fail-loud absence, NOT a regression; its first artifact-pass
verify wrongly demanded daily points and discarded a good retry before the check was corrected);
live preview screenshots incl. the EXPANDED provenance state. The twin test caught a REAL ordering
bug pre-ship (title-recovery ate the cross-ref stub → mangled instead of dropped; stub-truncation
now runs first in both twins). Gate green on fresh artifacts: 1038 passed; the guarded CNXC e2e
ACTIVATED (recomputes every % from the artifact's own points; each ≤ the threshold). INVARIANT:
deterministic unit pins (8.01 anchor map, gap-% refusal rules, clean-event trims) + JS↔py twin
equivalence drivers + the committed-CNXC e2e. Synthesis regenerated on the 10 (weather); one
NCNO overwrite incident (synth=null) caught by the standard check and recovered on retry.
