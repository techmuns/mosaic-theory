---
id: 
status: falsified
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**EXPERIMENT RECORD — 2026-07-23 synthesis net-direction prompt fix TESTED AND REJECTED (weather
baseline).** Diagnosis: BRBR's committed synthesis carried 2 mis-slotted `bull_points` (a net-bear
"fundamental margin collapse … real earnings hit" reconciler + a neutral "a PREMIUM, not a
discount" valuation question), traced to (a) the `bull_points` schema description INSTRUCTING the
LLM to "POSE earned-vs-residual" inside bull (contradicting system rule 7b) and (b) no net-direction
rule for mixed points. A candidate fix (net-bull-only schema description + a 7c NET-DIRECTION rule)
looked like a clean win on ONE run (both mis-slots gone). The operator required a WEATHER BASELINE
before adoption: OLD-prompt fresh runs vs NEW-prompt runs on BRBR/EPAM/SMPL. RESULT — the fix was
REJECTED on three findings: (1) BRBR's OLD-prompt FRESH run produced 7 clean bull points with ZERO
mis-slots — the diagnosed failure is LLM WEATHER, not a stable prompt defect; (2) the one-run "win"
didn't replicate (the NEW run's false-balance flag came back); (3) the fix has a real side effect —
it systematically drains bull_points and FLIPPED SMPL's lean mixed → strongly-bearish (and cut EPAM
9→6 bull), i.e. a bearish bias worse than the artifact it chased. `synthesis.py` reverted untouched.
STANDING LESSON: a defect observed in ONE committed synthesis snapshot is not a prompt defect until
a same-prompt re-run reproduces it; the downstream guards (false-balance + the diagnostic caveats)
are the correct catch for weather-class mis-slots. Experiment artifacts restored from git; committed
dossiers untouched.
