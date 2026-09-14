---
id:
status: recorded
date: 2026-09-14
prs: []
supersedes:
superseded-by:
---

# The EV/Sales replication CONFIRMS — the gap is valuation, not the earnings base

**WHAT.** All 13 `TEV/Forward Total Revenue` panes landed 2026-09-14, hours after the forward-P/E
run. **Against the decision rule registered before the pull, the result is CONFIRMS.** The gap is
**larger** on a metric whose denominator cannot approach zero, and the attrition that biased the
P/E run **disappears**.

## The registered rule, applied

| | forward P/E | **TEV/Forward Revenue** |
|---|---:|---:|
| pairs | 55 | **67** |
| median rank gap | +29.27 | **+36.96** |
| mean | +24.28 | **+29.76** |
| **95% CI** | [+13.91, +34.65] | **[+21.13, +38.39]** |
| sign test | 44/55 | **48/67** |
| p | <0.0001 | **<0.0001** |
| MDE @80%, observed SD | 15.1 | **12.3** |

*(both excluding FVRR — see below)*

**CI lower bound +21.13, more than double the ±10 threshold, and the upper bound exceeds the P/E
gap. By the registered rule that is CONFIRMS, not MIXED** — there is no evidence the P/E figure was
inflated by the earnings base, because the base-free metric gives a **larger** gap.

**AND THE ATTRITION COLLAPSES — which was the other half of the objection:**

| | usable | unusable | ratified lost | passed lost |
|---|---:|---:|---:|---:|
| forward P/E | 125/138 | 13 | **10** | 3 |
| **TEV/Fwd Revenue** | **137/138** | **1** | **0** | 1 (WIT) |

**Revenue does not approach zero, so the loss-making and recently-listed ratified names are priced
rather than dropped.** The arm-differential attrition that could have manufactured the P/E result
is **absent here**, and the result is the same only stronger.

## A THIRD SENTINEL SHAPE: HOLIDAY FILLS — and it defeats the run detector

Scanning both datasets for values repeating exactly, **38 dates carry `42.0` across ~90% of live
series**: **2023-05-29, 2024-05-27, 2025-05-26, 2026-05-25 (Memorial Days), 2021-12-24, 2025-07-04.**
**They are US market holidays** — present in the date grid because it spans non-US trading calendars
(the Israeli names trade Sun–Thu), and filled with the placeholder.

**Benign for a median over ~20 observations** — one or two cells cannot move it. **But it has a
second-order effect that is not benign:** the run detector's discriminating condition is *the value
occurs nowhere outside the run*, and **scattered holiday fills make `42.0` "recur" everywhere**,
which **suppresses detection of genuine long runs**. MBGL (1,458 of 1,512 cells at 42.0), XZO
(1,096), KVYO (783), RDVT (663) are all unflagged for this reason. *None corrupts its measurement
window here — their placeholder mass sits in the early period — so no result changes, but the
mechanism is now known and will bite a window that overlaps one.*

## FVRR WAS CORRUPTED IN BOTH RUNS, INCLUDING THE PUBLISHED ONE

**FVRR's 28-day window is 21 of 21 placeholder cells**, so its median IS `42.0` in both datasets. Its
real TEV/Revenue tail reads **0.20, 0.21, 0.27, 0.31, 0.07** — the placeholder is two orders of
magnitude out. Excluded, with its pair (CRNC):

| | as published | FVRR excluded |
|---|---|---|
| forward P/E | +29.76 median, CI [+12.19, +33.28], n=56 | **+29.27, CI [+13.91, +34.65], n=55** |
| TEV/Fwd Revenue | +35.39, CI [+19.33, +37.08], n=68 | **+36.96, CI [+21.13, +38.39], n=67** |

**Both results strengthen.** The corrupted pair was one of the 12 negatives —
`CRNC 11.2x vs FVRR 42.0x, gap −57.1`, recorded in
`docs/records/2026-09-14-the-market-already-prices-the-discriminator.md` as a genuine disagreement.
**It was a sentinel.** That record is amended rather than rewritten; its headline stands because the
change is 0.5 rank points.

## WHAT IS STILL NOT TESTED — the growth confound

**The growth condition registered before the pull was NOT run, because revenue was not pulled as a
series.** The panes carry `TEV/Forward Total Revenue` only. **So EV/Sales confirms the gap is not an
earnings-base artifact, and says nothing about whether it is a GROWTH premium rather than a
durability premium** — high-growth names carry higher sales multiples legitimately, and if ratified
names are higher-growth the gap is explained without durability entering.

**That is the live objection now, and it is the same shape as the one just closed**: an uncontrolled
variable correlated with the arm. It needs revenue as a second series — **13 more panes, not 38** —
and the registered split still applies, with its MDE recomputed on **SD 36.04 at ~33 per side ≈ 17.6
rank points**, so it remains descriptive rather than a test at ±10.

**BOUNDARY.** Source: operator's 13 `Forward TEV:Total Forward Revenue` exports, pulled 2026-09-14,
read the same day. **138 series, every manifest name present, none missing, none extra**; metric
`TEV/Forward Total Revenue` on all 138; window 2021-09-14 → **2026-09-11** after truncating Set 13,
which again ended 2026-09-14. Measure: **median over 2026-08-14 → 2026-09-11**, date-anchored (Set 5
again carries 212 Sunday rows). Strata, pairs and method are identical to the forward-P/E run,
regenerated deterministically from `data/themes/baskets/ai-value-migration.json` at freeze
2026-09-01. Holiday-fill dates counted across both datasets, threshold ≥20 live series at exactly
42.0. No raw CIQ committed.

**WHAT IT COSTS / WHAT IS ACCEPTED.** **The growth confound is untested and is now the binding
objection** — stated here rather than left for a reader to notice. **The holiday-fill suppression is
a KNOWN, UNFIXED detector limitation**: it changes no result in this run because the affected series
carry their placeholder mass outside the measurement window, and the cheap fix — nulling rows where
a supermajority of live series share one exact value — is **proposed, not built**, because building
it speculatively on a run it does not change is the wrong order. **Falsifier: a measurement window
overlapping a long placeholder run on a name whose scattered holiday fills suppress its detection**
— at which point the row-level fix ships. **And this tests SIC 73 only**, as the P/E run did; the 50
ratified names outside it remain unaddressed.
