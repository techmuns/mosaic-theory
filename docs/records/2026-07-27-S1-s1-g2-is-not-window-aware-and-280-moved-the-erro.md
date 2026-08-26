---
id: S1
status: recorded
date: 2026-07-27
prs: [280]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S1. G2 IS NOT WINDOW-AWARE, and #280 moved the error into the blind spot.**
`gate_g2_idiosyncratic` compares `rel` to `idio_rel_max` with no window term. Before #280 a stale
benchmark produced PERMISSIVE ADMISSION — countable, because admitted names leave records (4 of
318 on the 2026-07-27 run: CABA, GO, NOMD, TROX; none reached a dossier, NOMD ranked 227 of 275).
After #280 the same input produces a SHORTER window, so `|rel|` shrinks, the −15% threshold gets
harder, and the name FAILS — **silent rejection, no record anywhere.** The fix is right; the
consequence relocated to where nothing sees it. **THEREFORE RETENTION IS THE PRECONDITION FOR
LIFTING THE SCREEN HOLD, not an item behind it** (operator correction — the dependency was stated
backwards). **THE FIX SPLITS ON CAUSE, which dissolves the threshold nobody could derive**
(operator, withdrawing an earlier floor ruling): **end-truncation** (stale benchmark) is uniform
and operator-fixable → the CONSUMPTION GUARD REFUSES THE RUN before G2 computes, so the population
is never degraded for an unrun command — and that is also why "UNKNOWN the whole screen" stops
being an objection; **start-truncation** (short history, halt) is per-name and no action fixes it
→ RECORDED NOT-EVALUATED WITH ITS REASON, NEVER FAIL, which is item 22 applied to the screen: a
name that could not be assessed must not look like one that was assessed and rejected. BASIS
MISTRANSLATION AGAIN — −15% was struck on a ~70-day window, so a `rel` measured over 7 days is a
different quantity. (The operator called this the seventh sighting; the repo carries no enumerated
tally, so the ordinal is not checkable and is recorded as a characterisation, not a count.)
DEMONSTRATED ON A SYNTHETIC FIXTURE, not on the corpus — no committed name is currently behind
its benchmark, so this shape has no live instance to measure: a name 30d behind yields a 37d
window at −10.0%, 60d behind yields 7d/−3.0%, one bar past the start yields 1d/−0.5%, against
67d/−20.0% for a current name. All three FAIL a threshold calibrated on the full window.
