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

## Result of the scheduled re-run — 2026-09-02

> **Pointer correction, not a rewrite.** The amendment above says *"Tracked as STATE.md §5.0 row
> 14."* That row is **now deleted** — the re-run below closed the item, and closing deletes the row.
> §5.0 row 14 is today the standing-trigger row, a different item. The merged text is left as filed
> because record bodies are immutable; this is the forward correction.

Run as scheduled: the parent's 19 prefilter terms over the committed universe (3,036 distinct CIKs),
the CLI's default 290-day window ending at the snapshot `as_of` (2025-11-07 … 2026-08-24), under the
instrumented code.

```
probed CIKs      3036
SKIPPED queries     0      <- the measurement this run existed for
matched NOW      1348
graded THEN      1353      (1266 main run + 102 delta scan, union)
  NOW not THEN      0
  THEN not NOW      5
```

**No detectable silent loss.** `NOW \ THEN = 0` — every name the re-run finds was already graded, so
the original run missed nothing this one can see. The five in the other direction are the shrinkage
direction (filings ageing out of a window that ends earlier than the delta scan did), not loss.
**`ai-value-migration`'s denominator is sound**, and with it the sheet built on top of it.

### The row's own phrasing was a category error

It said "report the candidate count **against 357**." A prefilter yield does not compare to 357: the
357 is `ratified + passed`, a **downstream** selection from the graded population.

```
prefilter yield 1,353  ->  graded  ->  ratified + passed 357
```

The comparison that means something is 1,348 against 1,353. Recorded because mixing two stages'
counts is the denominator confusion this record exists about.

### The motivating anomaly was my own artifact

AES and ETN were escalated because they matched an old prefilter term on a direct probe yet never
reached the 745-name scan, which "vocabulary cannot explain." It can:

| window | AES | ETN |
|---|---|---|
| **290 days — the scan's actual window** | **0 terms** | **0 terms** |
| 400 days — the window my probe used | `hyperscaler` | `hyperscaler` |

The matching filing is older than 290 days. **Their absence from the scan was correct behaviour**,
and the anomaly was a window mismatch between my probe and the scan it was probing. It was flagged
rather than asserted, which is the only reason it cost a check instead of a false record.

### What that leaves standing

The **defect is real**: `skip_errors=True` is hardcoded and, before this, the `break` was uncounted —
a scan could lose up to 100 CIKs per swallowed query and report a clean number. The instrumentation
and the banner stay.

**But there is no evidence it has ever fired.** Both instrumented runs — this one and the
ai-compute-platform corpus check — report **0 skips**. The honest status is a guard against an
unobserved failure mode, not a fix for an observed one. The prior claim that "every denominator in
the theme pipeline is a lower bound over an unknown base" is **withdrawn for the parent**, which is
now measured; it remains formally true only for scans run before instrumentation whose skip count
was never recorded.
