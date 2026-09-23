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
