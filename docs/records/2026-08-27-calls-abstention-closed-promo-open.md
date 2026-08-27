---
id:
status: shipped
date: 2026-08-27
prs: []
supersedes:
superseded-by:
---

# 35 more hand rows close the abstention question and make the promo one more expensive

**The batch.** 35 new (post, ticker) decisions, **0 disagreements with the adopted reading**. Imported
with the previous 185 (idempotent); hand labels **268 → 303**.

**It did not land on the target.** The power note asked for ~16 PROMO-DIRECTIONAL rows, filtered.
The read was taken on the default `priority` sort with no class filter, so 31 of the 35 came back
`4 not a call` and only **5** were promo-directional.

**ABSTENTION — CLOSED.** 27 more `none → none` agreements:

| | rate | 95% CI |
| --- | --- | --- |
| previous sample | 48/50 = 96% | [87%, 99%] |
| **with this batch** | **75/77 = 97%** | **[91%, 99%]** |

The adopted reading's `none` is trustworthy across ~4,900 corpus rows. Stop testing it.

**PROMO COIN-FLIP — WEAKENED, AND NOW DEARER TO SETTLE.** All 5 new promo-directional rows KEPT
their direction, so the over-commit count held at 7 while the denominator grew:

| | rate | 95% CI |
| --- | --- | --- |
| promo, before | 7/12 = 58% | [32%, 81%] |
| **promo, now** | **7/17 = 41%** | **[22%, 64%]** |
| non-promo | 13/60 = 22% | [13%, 34%] |

Still overlapping (22–34% common to both). **The point estimate moving 58% → 41% RAISES the cost of
proving it**: at 58% vs 22% the two-proportion test needed ~28 promo-directional rows (11 more); at
41% vs 22% it needs **~88 (71 more)**. The earlier "16 more rows" was priced off an estimate that has
since moved against it — recorded here because the temptation is to keep quoting the cheap number.

**Scoring: nothing moved.** 3,261 rows, 0 status changes, 0 verdict changes, direction-correct
51.00% of 2,841 — every one of the 35 was an agreement, so there was nothing for the scorer to
revise. The HAND subset reads 57.4% of 129.

**The U+2028 fix earned itself.** This export contained one too: `splitlines()` would have read 221
lines for 220 rows and the import would have failed exactly as before. The `jsonl_lines()` guard is
now load-bearing on every export, not a one-off repair.

**Standing guidance.** The decision-useful position is already reached — accept `none` (97%), treat
a directional label as a ~68% prior, and rank promo-classed directional rows lower in a review
queue without proving the exact multiplier. If more labelling happens, the higher-value target is
`signal_candidate` + directional (2,423 unlabelled): that is the population that actually carries
the 51% headline, and it currently rests on 59 hand rows.
