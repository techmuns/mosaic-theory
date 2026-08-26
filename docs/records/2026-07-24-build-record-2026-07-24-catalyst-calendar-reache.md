---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 catalyst calendar reached the PDF but not the WEB (card key drift).**
Found by actually LOOKING at the rendered page (operator asked for a screenshot). `frontend/build.py`
camelCases every card key, but never emitted `dated_triggers` at all, and `dossier.js` read it in
SNAKE case — two independent breaks on the same field. Effect: the web calendar rendered SHORT of
the md/PDF — SMPL showed **2 of 3** entries and the missing row was **the analyst's own falsifier**
(the September pricing trigger), i.e. the single most decision-relevant row for a months-to-quarters
book. WHY IT SURVIVED SINCE #209/#211: the twin test `test_catalyst_calendar_js_twin_parity_node`
injected `card.verdict.dated_triggers` — a snake_case shape **build.py never emits** — so the
fixture LIED and the test stayed green while production dropped the data. (A second red herring:
the preview server was rooted in the MAIN checkout, then **45 commits stale**, which briefly looked
like a total outage. Preview only from the worktree under test.) FIX: build.py emits
`datedTriggers` (omitted when empty → trigger-less records stay byte-identical); dossier.js reads
camelCase; the twin fixture now uses the production shape. Artifact diff: **+7 lines on
frontend/scenarios/SMPL.json alone**, every other artifact byte-identical. VERIFIED on the running
worktree preview: SMPL's web calendar now renders **3 rows = md 3**, incl. "Re-underwrite trigger:
September portfolio-wide price increase fails to stick … 2027-01-07 [trigger-deadline]".
INVARIANT (2 pins, both proven RED on the reverted bug then green): `test_card_verdict_keys_read_
by_js_are_emitted_by_build` — every `card.verdict.<key>` the JS reads must be a key build.py emits,
and no snake_case survives on the card side (this is the general guard: it catches the NEXT such
field, not just this one); and `test_committed_web_card_carries_the_same_dated_triggers_as_its_
record` — structural count parity on the committed artifacts (counts only; analyst prose is never
pinned). Gate: ruff + `mypy --strict` clean · 1068 passed.

**THE R2 CHECK — NEITHER HYPOTHESIS WINS CLEANLY, AND MINE WAS MEASURED ON THE WRONG BASIS
(2026-08-03, operator-directed; report only, nothing built).** The operator asked whether the R2
wedge is HORIZON distance or simply an UNCONVERTED operating margin compared against a consensus
EBITDA margin. Measured, `margin + d_and_a_ratio` against consensus at each name's anchor:
| name | ours (op) | +D&A/rev | = EBITDA | consensus | raw gap | CONVERTED |
|---|---:|---:|---:|---:|---:|---:|
| SMPL (R1, calibration) | 14.0% | 1.61% | 15.6% | 16.5% | 2.5pp | **0.9pp** |
| AORT | 9.5% | 4.90% | 14.4% | 19.4% | 9.9pp | **5.0pp** |
| NCNO | 12.6% | 7.10% | 19.7% | 27.1% | 14.5pp | **7.4pp** |
| MVST | 6.0% | 8.94% | 14.9% | 14.0% | 8.0pp | **−1.0pp** |
**MVST LANDS AT CONSENSUS — converted, the wedge is GONE (−1.0pp), so the horizon reason is FALSE
on that page.** AORT and NCNO HALVE but keep 5.0pp and 7.4pp, which is still 5–8× SMPL's 0.9pp
calibration residual — so something beyond D&A survives on those two, but far less than claimed.
**MY "ROUGHLY HALF ON EVERY ONE" WAS COMPUTED ON THE UNCONVERTED MARGIN**, which is the operator's
own point arriving a third time: I compared two quantities on different bases and attributed 100%
of the difference to a cause I had not tested against the obvious alternative. Same shape as
endorsing the mixed-basis claim without checking the panel.
**CONSEQUENCE FOR THE LIVE PAGES: the refusal text is now known to be wrong on MVST and overstated
on AORT/NCNO** ("the ratio would measure the gap between two horizons, not between our view and the
street's" — on the converted basis, part of it IS a view difference). Left in place: whether to
compute those names is the operator's call, and MVST is refused twice over on coverage anyway
(price-implied-only, one estimate), so **only AORT and NCNO turn on the convention.**

**REVIEW OF #325 — `if dossiers:` GUARDED ONLY THE ALL-FAILED CASE, AND MY COMMENT CLAIMED MORE
THAN IT DID (2026-08-03).** In a MIXED cohort — one name assembles, another hits the now-working
refusal — the mirror still rebuilds the WHOLE tree, so the gate does not "stop the old page being
published as fresh". Claiming it did is the declared-vs-enforced class, again, in a comment.
**BUT NEITHER OF THE PROPOSED FIXES IS RIGHT, AND #319'S OWN INVARIANT IS WHY.** It asserts EVERY
`frontend/dossiers/<T>.md` is byte-identical to its source — so mirroring only the successful names,
or skipping on any error, **strands whichever page had drifted**, which is the FUBO defect the call
exists to prevent. And a refusal WRITES NOTHING: measured, `data/` and `frontend/` sha256s match on
every committed name, so a refused name's mirror copy is a **no-op, not a stale publish**. The
whole-tree rebuild stays, now with the reason written down instead of an overclaim.
**THE REAL BUG WAS THE EXIT CODE, AND IT HAD ALREADY BITTEN.** `_cmd_dossier` printed `errors` and
returned 0, so a caller keying on exit status read a refused assembly as a completed one — which is
exactly how the reroll harness for the SMPL task stopped after a single refused build and reported
convergence. **D16's shape at the process boundary.** Now `return 1 if errors else 0`; the per-name
report stays, so a batch still says WHICH names failed rather than dying on the first. Verified no
workflow or script consumes that exit status.
**MIXED-COHORT TESTS SHIPPED — the case the old guard missed** (`test_dossier_cli_partial_failure`,
5 pins). Both mutations CAUGHT: reverting to `return 0` on errors, and skipping the mirror when any
name fails. The second is pinned as DELIBERATE rather than incidental — a mixed cohort must still
mirror, or the name that DID assemble goes stale on the served surface.
