---
id:
status: shipped
date: 2026-09-01
prs: []
supersedes:
superseded-by:
---

# The Opus 5 default broke dossier synthesis fleet-wide, and the recorded falsifier watched the wrong failure

**WHAT.** `Config.graph_llm_model` is reverted from `claude-opus-5` to `claude-opus-4-8` by
**operator ruling 2026-09-01**, reversing the 2026-08-29 bump
(`docs/records/2026-08-29-opus5-default-and-two-drivers.md`, PR #519). Under Opus 5 the synthesis
call returns a `tool_use` block **missing required fields** roughly half the time; `synthesize()`
correctly refuses it and the assembly hard-stops, so **no dossier could be reliably assembled with
synthesis for three days**.

**HOW IT WAS FOUND.** Not by a check — by trying to assemble TECX, the first name to need a
synthesis since the bump. It failed three times.

**WHY NOTHING CAUGHT IT.** Two independent reasons, and both are the point of this record:

1. **The bump was never exercised on the synthesis path.** All 18 committed syntheses were produced
   by `claude-opus-4-8`; **not one by Opus 5**. Between 2026-08-29 and 2026-09-01 no dossier was
   assembled with synthesis, so the new model had never actually run the job it was configured for.
2. **The recorded falsifier watched the wrong failure mode.** The 2026-08-29 ruling accepted a
   stated risk — the 4.8-era groundedness benchmark was not re-run — with the falsifier
   *"untraceable figures or mis-cites appearing in fresh extractions"*. That is a **content**
   watch. What broke was **absence**: there is no synthesis to inspect for mis-cites, because the
   model never completes the tool call. A groundedness falsifier cannot fire on a missing artifact.

**MEASURED, BEFORE REVERTING.** Real API calls; prompts built exactly as `synthesize()` builds them
(facts dump + drawdown-guidance marking + primary-source digest + operating-drivers block);
`max_tokens=16384` throughout:

| name | sleeve | model | runs | result |
|---|---|---|---|---|
| TECX | quality | **opus-5** | 9 | **5 FAIL / 4 PASS** (~55% fail) |
| TECX | quality | opus-4-8 | 2 | 2 PASS / 0 FAIL |
| **SMPL** | **overshoot** | **opus-5** | 3 | **2 FAIL / 1 PASS** (~67% fail) |
| V | quality | opus-5 | 4 | 4 PASS / 0 FAIL |

**SMPL is the load-bearing row** — an established, committed, overshoot-sleeve name with full
financials, nothing like TECX — so the regression is **fleet-wide, not a property of pre-revenue
names or of the quality sleeve**. V passing 4 of 4 shows it is not universal either: the rate
varies by name.

**THREE THINGS RULED OUT, each with its measurement:**

- **Not truncation.** `stop_reason` is `tool_use`, never `max_tokens`; failing calls use 35–62% of
  budget. Counter-intuitively the **FAILING** runs burn MORE output tokens (8.7–10.1k) than the
  passing ones (3.9–6.6k) while returning FEWER fields.
- **Not prompt size.** TECX is the **second-smallest** of 18 (182K chars); V, which passes, is 343K.
- **Not the sleeve.** The quality and overshoot tool schemas are structurally identical (verified
  field by field), and SMPL fails on `overshoot`.

The failure shape is a **nesting error**: the model emits `source_ref` at the TOP level — where the
schema has no such field; it belongs inside each `bull_points`/`bear_points` item — and stops.

**HOW VERIFIED.** The same VERBATIM prompt (dumped from a live assembly) replayed: Opus 5 gives
FAIL / PASS / FAIL, Opus 4.8 gives PASS. It is **stochastic**, so a single green run proves
nothing — any future claim about this knob must measure a RATE.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **Nothing was damaged.** `assemble.py` refuses to write when synthesis returns nothing, citing the
  2026-07-30 AORT incident where a committed synthesis was replaced with null. The three failed
  TECX runs left the existing page untouched. **The guard did its job**; this record is about the
  three days of blindness before it fired, not about a lost artifact.
- **Reverting forfeits whatever Opus 5 is better at.** Accepted deliberately: a model that cannot
  complete the tool call ~half the time is unusable on this path regardless of its other qualities.
- **The trigger is undiagnosed.** Untested hypotheses: `tool_choice` forcing interacting with the
  model's default thinking behaviour; the nested `{claim, source_ref}` item shape; the 5,301-char
  system prompt. Each is one measurable experiment. **Not pursued** — the operator's decision was
  to revert, and diagnosing a model we are not using is not on the critical path.
- **STILL OPEN — the misleading message.** `synthesis.py` emits `"… (likely truncated)"` whenever
  required fields are missing. That inference is WRONG here and sends a reader to raise
  `max_tokens`, which would not help. The client already records real usage in `last_usage`; the
  message should state the measurement instead of the guess. The client's own docstring records
  this same trap for SMPL on 2026-08-04, so this is its second occurrence.
- **NOT DONE, deliberately: a bounded retry on incomplete tool output.** It would very likely make
  assembly robust, and it is worth building — but shipping it *instead of* deciding the model would
  have masked a fleet-wide regression behind a retry loop. Sequence matters: decide the model
  first, add the retry as its own change.

**THE INVARIANT SHIPPED WITH THIS (per the INVARIANT RULE).**
`tests/test_llm_default_is_exercised.py` — the configured `graph_llm_model` must have produced at
least one committed synthesis, or be named in `UNEXERCISED_BY_RULING` **with its reason** (empty by
design). **Mutation-tested: setting the knob back to `claude-opus-5` turns it red**, which is
exactly what should have happened on 2026-08-29. It would have forced the choice to be made
deliberately — assemble one name with the new model, or record the exemption — instead of
discovered three days later by a hard-stop.

It cannot test model QUALITY; nothing offline can. It tests that the configured model has been
exercised end-to-end at least once, which is a floor, not a ceiling. Two companion pins keep it
honest: the exemption map may not list a model that has demonstrably worked (that would make it a
bypass rather than a record), and every committed synthesis must name the model that wrote it (an
unattributable artifact would silently shrink the corpus the guard measures).

**RE-RAISING THIS KNOB** requires a measured PASS RATE over **≥5 runs on ≥3 names** including SMPL
and TECX — the two that fail — never a single green run.
