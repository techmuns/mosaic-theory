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

**MEASURED AT THE #574 BAR, 2026-09-25 — three experiments, and the third overturned this
record's own first conclusion.**

**(1) END-TO-END** — re-assemble a name on the same data, 5 draws each (the artifact-pass case):

| name | book | labels | proposals | agreement | committed page |
|---|---|---|---|---|---|
| AMZN | quality | strongly-bullish 4, mixed 1 | **BUY 4, none 1** | 4/5 | `mixed`/none — the 1-in-5 outcome |
| NFLX | overshoot | strongly-bullish 2, mixed 3 | BUY 2, none 3 | 3/5 | `mixed`/none |
| PARR | ultra_short_term | mixed 5 | none 5 | **5/5** | `mixed`/none |

**This corrects an earlier claim in `docs/records/2026-09-23-pages-onto-the-2026-09-22-as-of.md`**:
on n=2 NFLX's withdrawal "reproduced" and was called data-driven. At n=5 it is **3–2** — roughly
two in five re-assemblies would publish BUY. The n=2 conclusion was under-powered by exactly the
standard #574 set, cited in this record before being met.

**(2) MODEL-ONLY** — ONE byte-identical synthesis prompt (`064761bb4f6a6a1a`), 8 replays, AMZN:
**strongly-bullish 7, mixed 1 → BUY 7/8.** Holding the prompt fixed did NOT stabilise the label:
~1-in-8 against ~1-in-5 end-to-end. So the variance is the SYNTHESIS CALL's own sampling; the
upstream chain's prompt drift adds nothing detectable at this size. (Every end-to-end draw sends a
DIFFERENT synthesis prompt — five LLM extractions run before synthesis and feed it — which is why
(1) alone cannot attribute anything, and why the prompt hash was recorded per draw.)

**(3) FRAME SWAP — the one that matters, and it refutes "stability is name-specific".** The three
names in (1) sat in three different books, so name and METHOD varied together. The per-book system
prompts are **98.6–98.9% character-identical**; the difference is the ~60 characters naming the two
competing cases. Holding AMZN's fact set byte-identical (519,850 chars, verified to contain NO
book-specific wording) and swapping only the frame, 6 draws each:

| frame | BUY | none | bull mean | bear mean | bull:bear |
|---|---|---|---|---|---|
| quality (AMZN's own) | 5 | 1 | 7.0 | **4.7** | 1.50 |
| overshoot | 6 | 0 | 8.3 | **3.7** | 2.27 |
| ultra_short_term | 6 | 0 | 7.7 | 3.8 | 2.00 |

Bear counts are nearly DISJOINT — quality `[5,5,4,4,5,5]`, overshoot `[4,3,4,4,3,4]`. **The method
shapes the evidence the model assembles from identical facts**, and therefore the read.

**SO: BOOK ASSIGNMENT IS A DECISION-SURFACE INPUT, NOT A LABEL.** Putting a name in the quality
book makes its page read measurably more bearish than the same facts in the overshoot book. That is
the same operator decision taken for TECX on 2026-09-23, now with a measured consequence.

**(4) WITHIN ONE BOOK — the test that separates name from method.** Three quality-book names, the
SAME frame, 5 draws each:

| name | book | labels | proposals | agreement |
|---|---|---|---|---|
| AMZN | quality | strongly-bullish 4, mixed 1 | BUY 4/5 | 4/5 |
| GOOGL | quality | strongly-bullish 3, mixed 2 | BUY 3/5 | 3/5 |
| LLY | quality | strongly-bullish 5 | BUY 5/5 | **5/5** |

**Holding the method fixed, stability still ranges 5/5 to 3/5.** So the quality frame is not
"harder" in itself: it produced both the most stable name measured and one of the least. Across all
five names measured, the two that never wavered are LLY (quality) and PARR (ultra_short_term) — and
the three that did span two books. **Stability does not sort by book in either direction.**

**THE SETTLED READING — both effects are real and neither subsumes the other.** The METHOD shapes
the read (3): identical facts under a different frame assemble measurably different bear evidence.
The residual INSTABILITY tracks the NAME (4): with the frame held constant it spans 5/5 to 3/5.
The first draft of this record asserted the second WITHOUT holding the frame constant, which the
operator challenged; it was unsupported as stated and is re-established here only on (4).

**n=5 separates 5/5 from 3/5; it cannot rank 4/5 against 3/5** — those are one draw apart.

**WHERE THIS TOUCHES A POSITION OF RECORD.** GOOGL is the least stable name measured (3/5) and the
only one of the five carrying a LEDGERED verdict — BUY, entry $345.90, 2026-08-14. The human's
verdict of record is unaffected by a machine proposal; but the ledger seals the PROPOSAL beside it
so the spread can decompose into machine baseline vs human delta, and on a name like this the
sealed proposal is close to a coin. **The machine-baseline curve therefore carries measurement noise
that the human-final curve does not** — stated here so nobody reads a machine-vs-human gap on such
names as signal.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **Artifacts are NOT reproducible from their inputs, and no parameter can change that.** Where a
   lean label sits near a boundary `derive_proposal` maps deterministically, the machine's PROPOSAL
   moves with the draw. AMZN is a demonstrated case; two draws prove instability where they
   disagree and prove nothing where they agree, so the other names are *consistent with* stable, not
   shown to be.
2. **NOTHING ON THE PAGE STATES ITS OWN REPRODUCIBILITY — accepted here, not fixed.** A reader
   meets `mixed`/no-proposal on AMZN and BUY on LLY with identical confidence, though one is a
   1-in-5 outcome and the other held 5 for 5. **Falsifier:** any human verdict that overrides a
   proposal on a name whose label later measures ≤3/5, where the operator says they would have read
   the page differently had its reproducibility been shown. **Cheap fix genuinely unavailable?** No —
   this one IS available (record the per-name rate and print it), so this is a deliberate deferral
   pending the operator's design ruling, NOT an unavoidable cost.
3. **The remedy is a DESIGN choice and belongs to the operator** — draw N times and refuse a
   proposal the draws disagree on (N× the LLM cost, and the page then states its own
   reproducibility), or accept that a two-sided name's proposal carries less information than it
   appears to and must not be read as a signal. **Not decided here.**
4. **§5.0 OPEN NOW is at its 60-line cap**, so item (2) could not take a row without evicting
   another. It is recorded here and in §2 instead, and the capacity conflict is raised to the
   operator rather than resolved by quietly compressing someone else's entry.
