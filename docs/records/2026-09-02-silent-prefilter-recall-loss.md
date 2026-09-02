---
id:
status: shipped
date: 2026-09-02
prs: [572]
supersedes:
superseded-by:
---

# The efts prefilter skipped failed queries silently, so every theme denominator is a lower bound

*Escalated as its own defect. It does not close with the `ai-compute-platform` card that surfaced it.*

**WHAT.** `scan_driver_exposure` hardcodes `skip_errors=True` (`vinci/themes/exposure.py:639`). On an
`HttpError` the prefilter `break`s out of that batch×phrase and keeps going. Until now **nothing
counted it**. A batch holds up to 100 CIKs, so a single swallowed query can cost 100 names their
match on that phrase, and the scan reports a clean number regardless.

**HOW IT SURFACED.** AES and ETN matched an **old** prefilter term (`hyperscaler`) on a direct probe,
yet neither appears in the 745-name `ai-compute-platform` scan. Vocabulary cannot explain that, which
leaves silent recall loss. It was first mistaken for a prefilter miss — it is not; the terms matched.

**WHY IT IS ITS OWN DEFECT.** Every denominator in the theme pipeline is therefore **"N that
succeeded" over an unknown base** — the 745 here, and `ai-value-migration`'s 357 on the parent sheet.
Any share computed on such a base (the 67% crypto-origin figure included) is a share of an unmeasured
population. The card that surfaced this is closed; the denominators it touched are not.

**WHAT SHIPPED.** `mention_prefilter` takes an optional `skipped` list and records one entry per
errored batch×phrase, with the phrase, batch size, page offset and the underlying error.
`scan_driver_exposure` collects it and prints a loud banner when non-empty:

```
!! PREFILTER RECALL GAP — N batch×phrase quer(ies) errored and were SKIPPED. Each batch holds up
   to 100 CIKs, so this scan's population is a LOWER BOUND and its denominator is unknown.
   Do not report a share of it.
```

**The gap itself is kept** — skipping a transient efts failure is the right trade for a long scan,
and it is conservative in the safe direction (a missed mention means a name is not scanned, never a
fabricated one). What is fixed is that it was **unmeasurable**. An empty `skipped` list is now the
only thing that licenses reading a yield as complete.

**HOW VERIFIED.** `test_a_swallowed_prefilter_query_is_counted_not_silent` drives a client that
raises `HttpError` on every call and asserts two skips are recorded for two phrases, naming the batch
size and phrase. `test_the_prefilter_still_fails_loud_by_default` pins that counting the skips did
not turn fail-loud into fail-quiet where `skip_errors` is off. Suite green; ruff + `mypy --strict`
clean.

**WHAT IT COSTS / WHAT IS ACCEPTED.** The instrumentation is forward-only. **The scans already run
cannot be retro-measured** — 745 and 357 stay lower bounds of unknown tightness, and no share
computed on them can be repaired by this change. Re-running under instrumentation is the only way to
bound them, and that is a cost decision, not a build.

**FALSIFIER.** A re-run that reports zero skips and returns materially more than 745 names would show
the gap was large in the original run; one that returns ~745 would show it was small. Either is worth
more than the current unknown.

## Incident → invariant

| incident | invariant | shipped |
| --- | --- | --- |
| AES/ETN matched a prefilter term yet never reached the scan; denominators unmeasurable | errored batch×phrase queries are counted and printed as a recall-gap banner | Y (forward-only; prior scans not retro-measurable) |

## Amendments

**2026-09-02 — "cannot be retro-measured" is an OVERSTATEMENT; the re-run is scheduled.**

The body above says the scans already run cannot be retro-measured and that re-running is a cost
decision. That conflated re-running the **prefilter** with **re-grading**.

The expensive half is the LLM pass over 745 names. **The denominator is set by the efts prefilter
alone** — no LLM, no Polygon: the universe is already committed at
`data/snapshots/theme_universe_snapshot.jsonl` and `universe_snapshot.jsonl` (3,036 distinct CIKs in band, across 3,041 securities rows). So
bounding a past scan's denominator is ~31 batches × the driver's terms of cached efts queries under
the now-instrumented code, and it can run unattended.

**Decision taken rather than left implicit: re-run the parent's prefilter.** `ai-value-migration` is
a *declared* driver underpinning 168 ratifies, and its 357 is the denominator every share on that
sheet is computed against — that is worth a few hundred cached queries. Tracked as STATE.md §5.0
row 14. The alternative (logging the unknown as accepted on the parent card) was rejected for the
same reason.

What genuinely does **not** retro-measure is the LLM grading: a name the prefilter missed was never
assessed, so re-running the prefilter bounds the *population*, not the *grades*. A materially larger
candidate set would mean the graded 745 needs extending, which is a second, real cost.
