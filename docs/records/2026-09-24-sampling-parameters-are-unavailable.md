---
id:
status: shipped
date: 2026-09-24
prs: [647]
supersedes:
superseded-by:
---

# The model calls carry no sampling parameter, because the API removed them — and the reproducibility the code claimed cannot be bought back

**WHAT.** `AnthropicLlmClient.extract` — the package's ONLY `messages.create` call site, through
which dossier synthesis, graph extraction and every theme phase run — passes **no `temperature`,
`top_p` or `top_k`**, and now says so with a guard (`tests/test_llm_sampling.py`) and a constant
(`_REJECTED_SAMPLING_PARAMS`). The false reproducibility claim in
`vinci/dossier/assemble.py::_fleet_reference_date` is corrected in place.

**WHY.** The operator asked for `temperature=0`, to make artifacts reproducible from their inputs.
**It cannot be done on this model.** Measured 2026-09-24 against `claude-opus-4-8`:

```
BadRequestError: 400 - {'type': 'invalid_request_error',
                        'message': '`temperature` is deprecated for this model.'}
```

Sampling parameters are REMOVED on the Opus 4.7/4.8 tier — a 400, not a no-op — and there is no
seed parameter. Because one call site serves every LLM phase, the attempt did not degrade one
feature, it **failed all of them**: five names (AMZN, LLY, PARR, BRBR, WLK) each failed assembly
with that 400 before the parameter was taken back out.

**AND THE CLAIM THE FIX WAS MEANT TO HONOUR WAS ALREADY FALSE.** `_fleet_reference_date` justified
dating a dossier from the fleet as-of rather than the wall clock partly because wall-clock dating is
*"irreproducible (identical inputs, a different artifact tomorrow — the property temperature-0
protects, broken without a test that would notice)"*. No temperature was ever passed, so nothing
protected it, and the named test never existed. The as-of rule stands on its other two reasons —
both real — and the third is now struck.

**HOW VERIFIED.**

* **The rejection, observed** — the 400 above, on a real call, for five separate names.
* **The guard is the INVERSE of the obvious one**, and mutation-checked: re-adding
  `temperature=0` to the call turns `test_the_model_call_carries_no_sampling_parameter` and
  `test_no_call_shape_smuggles_one_in` red; removing it again turns them green. A third pin
  (`test_the_request_still_carries_what_the_call_actually_needs`) stops the negative guard being
  satisfiable by sending nothing at all.
* **The revert restores function, on real data** — PARR re-assembled in 190s, 1 dossier, **0
  errors**, `assembled_at` advanced (i.e. the file was genuinely rewritten).
* **Full offline suite: 3,971 passed, 45 skipped, 0 failed** with the local store/CIQ linked in.
  *Stated because the same tree reports "3,869 passed, 147 skipped" in 51 seconds without them —
  104 tests skip themselves for want of a store, and that run looks green while proving far less.*

**A MEASUREMENT HARNESS CAN REPORT A FALSE PASS THE SAME WAY.** The first validation harness called
`assemble_cohort`, which by design catches per-name exceptions into a returned `errors` list so one
bad name cannot crash a batch. The harness captured that list, never printed it, then read the
dossier still on disk and compared it against itself — reporting **"IDENTICAL" for 5 of 5 names**
while not one draw had occurred. What exposed it was TIMING (4–9s where an LLM assembly takes
110–190s) and `assembled_at` being unchanged. Any future draw-comparison harness must assert the
artifact was REWRITTEN before comparing it.

**BOUNDARY.** One model (`claude-opus-4-8`, `config.graph_llm_model`), one account, measured
2026-09-24 on this machine. The five failing names are AMZN, LLY, PARR, BRBR, WLK. Suite counts are
from the branch tree with `data/vinci.db`, `data/manual` and `.env` symlinked from the TA worktree.
Reproducibility observations are n=2 per name: AMZN (2026-09-23) `strongly-bullish`/BUY vs
`mixed`/none on identical inputs; NFLX (2026-09-23) `mixed` twice; PARR (2026-09-23/24) `mixed`
twice.

**THIS IS THE THIRD LOGGED INSTANCE, NOT A DISCOVERY — corrected 2026-09-25 after the operator
asked whether it was already on file.** It is, in two subsystems, and the repo had already settled
both the vocabulary and the method:

* **`docs/records/2026-09-01-opus5-synthesis-regression.md` (#574)** ran the same-inputs test on
  THIS path — the same verbatim prompt replayed: TECX 9 runs (5 FAIL / 4 PASS), SMPL 3 (2/1), V 4
  (4 PASS). Its conclusion is the general one: *"It is stochastic, so a single green run proves
  nothing — any future claim about this knob must measure a RATE"*, and it set the bar at
  **≥5 runs on ≥3 names**. What it measured was COMPLETION (does the tool call come back whole),
  not which LABEL it lands on.
* **`STATE.md` (theme-exposure refactor, 2026-09-02)** logged the label form of it one subsystem
  over: a 4-name live re-run where CORZ graded differently on identical inputs — *"a within-REAL
  sub-grade shift, documented LLM stochasticity, NOT a refactor change; the deterministic
  prompt-equivalence test proves the LLM INPUT is preserved, so run-to-run variance is the LLM's"*.
  The mechanism is `tests/test_themes_exposure.py`'s prompt-equivalence regression: **pin the
  input, then attribute the drift to the model** — the repo's answer to this class is attribution,
  not elimination.
* **`docs/RUNBOOKS.md:612`** already rules on the response: *"Do NOT re-roll a synthesis to get
  cleaner flags — that is selecting prose on outcome."* Keeping draw 2 over draw 3 for AMZN
  followed that rule; it was reasoned to independently here rather than cited, which is its own
  small failure of reading.

**So what is actually new is narrower than the first draft of this record claimed:** that the
variance lands on the machine PROPOSAL — the decision surface — rather than on a caveat or a
sub-grade, and that the obvious repair is not merely unset but UNAVAILABLE (the 400 above).
**And the evidence here is n=2 per name, BELOW the bar #574 set for exactly this kind of claim.**
By that standard "AMZN's label is unstable" stands (one disagreement is sufficient) and nothing
about the other names does.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **Artifacts are NOT reproducible from their inputs, and no parameter can change that.** Where a
   lean label sits near a boundary `derive_proposal` maps deterministically, the machine's PROPOSAL
   moves with the draw. AMZN is a demonstrated case; two draws prove instability where they
   disagree and prove nothing where they agree, so the other names are *consistent with* stable, not
   shown to be.
2. **The remedy is a DESIGN choice and belongs to the operator** — draw N times and refuse a
   proposal the draws disagree on (N× the LLM cost, and the page then states its own
   reproducibility), or accept that a two-sided name's proposal carries less information than it
   appears to and must not be read as a signal. **Not decided here.**
3. **§5.0 OPEN NOW is at its 60-line cap**, so item (2) could not take a row without evicting
   another. It is recorded here and in §2 instead, and the capacity conflict is raised to the
   operator rather than resolved by quietly compressing someone else's entry.
