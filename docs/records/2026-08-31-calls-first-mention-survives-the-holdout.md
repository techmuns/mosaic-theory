---
id:
status: recorded
date: 2026-08-31
prs: [511]
supersedes:
superseded-by:
---

# His exits add nothing. The FIRST call on a name is the only thing that has held out of sample.

Two versions a reader could actually have traded, both operator-specified in advance.
`scripts/calls/traded_versions.py`.

## Case 1 — held until his next `exit`/`trim`: no effect

| same entries throughout | n | beat SPY | med excess | mean excess | med days |
| --- | --: | --- | --- | --- | --: |
| his exits | 3,268 | 49% | −0.08% | +1.62% | 25 |
| fixed 63d | 3,268 | 49% | −0.22% | +2.39% | 63 |
| random duration, same distribution | 3,268 | 48% | −0.31% | +0.98% | 22 |
| **his exits, where he ACTUALLY posted one** | **2,491** | **51%** | **+0.12%** | +3.12% | 15 |
| **those same entries, fixed 63d** | **2,491** | **50%** | **+0.13%** | +4.09% | 63 |

Where a real exit signal exists, following it gives **51% / +0.12%** against **50% / +0.13%** for
ignoring it and holding 63 days. Identical. And his exits cut the MEAN excess (+3.12% vs +4.09%),
because exiting early forfeits the right tail — which on a book this skewed is where the return is.

## Case 2 — the operator's hypothesis was right, and their exit rule was wrong

**The entry half is confirmed.** The same 879 first-signal entries:

| | n | beat SPY | med excess | med days |
| --- | --: | --- | --- | --: |
| one position per name, closed by target/bearish/pnl_report/exit | 879 | 49% | −0.13% | **5** |
| **THE SAME entries, held 63d** | 879 | **54%** | **+1.07%** | 63 |
| every bullish call, held 63d | 2,433 | 50% | +0.09% | 63 |

De-duplicating to first-signals lifts median excess **+0.09% → +1.07%**. The repeats really were
diluting it, exactly as proposed. **Then the exit rules give it all back**: median holding collapses
to 5 days, because 404 of 879 positions close on a `pnl_report` — he posts a P&L brag on a name
within days, and using that as an exit trades a small gain for the run.

## AND THE ENTRY EFFECT SURVIVES THE HOLDOUT — the only one that has

Bullish calls held 63 days, split by whether it was the FIRST bullish call on that ticker:

| | n | beat SPY | 95% CI | med excess |
| --- | --: | --- | --- | --- |
| **FIRST call on a name** | 213 | **56%** | [50%, 63%] | **+4.40%** |
|   discovery (pre 2025-09) | 149 | **56%** | [48%, 64%] | +2.77% |
|   **holdout (post)** | **64** | **56%** | **[44%, 68%]** | **+6.91%** |
| LATER calls on that name | 2,220 | 50% | [48%, 52%] | −0.04% |
|   discovery | 1,334 | 59% | [56%, 61%] | +3.39% |
|   **holdout** | **886** | **36%** | **[33%, 39%]** | **−4.58%** |

**56% in both halves.** Every other pattern in this corpus inverts across that split — the later
calls do it right here, 59% → 36%. The first-mention cut does not move.

**WHY THIS IS NOT THE 65-CELL FISHING EXPEDITION.** That search mined ten attributes for whatever
cleared 50% and produced 65 winners, zero survivors. This hypothesis was stated by the operator as
a MECHANISM before any number was computed — first mention is new information, the fifth post about
the same name is not — and it was tested once. A pre-registered hypothesis that survives a time
split is a different object from a mined one that does not.

**IT IS STILL NOT AN EDGE.** 64 holdout rows, and that interval **[44%, 68%] includes 50%**. The
holdout alone establishes nothing; it is the STABILITY across two regimes that is interesting, on a
sample too small to call. And it inherits every limitation already recorded: one 25-month window,
a 1.59× beta book, ~81% bias labels.

**The honest status: the first-mention effect is the single hypothesis in this corpus worth testing
FORWARD.** It is cheap to state now — first bullish call on a name, held ~63 days — and it cannot
be settled by more history, because there are only 213 first-mentions in 25 months.
