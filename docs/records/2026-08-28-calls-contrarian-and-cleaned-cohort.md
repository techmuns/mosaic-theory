---
id:
status: falsified
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# Fading him wins the coin flip and loses the money

**The cleaned cohort.** All 3,305 directional calls → **3,061** after dropping `pnl_report` (posts
written BECAUSE a trade already worked, so their forward window is selected on the past) → **862**
after a 30-day cool-down per ticker over what remains. A 74% reduction: he restates the same names
for days, and without the cool-down the aggregate measures his posting rate.

**FOLLOW — long the name / short SPY**

| | n | beat SPY | 95% CI | median | **mean** | worst | best |
| --- | --: | --- | --- | --- | --- | --- | --- |
| 5d | 838 | 47% | [44%, 51%] | −0.32% | −0.10% | −60.9% | +50.0% |
| 21d | 805 | 47% | [44%, 51%] | −0.49% | −0.07% | −97.6% | +124.6% |
| 63d | 736 | 49% | [45%, 53%] | −0.10% | +1.37% | −290.7% | +281.8% |
| 126d | 634 | 48% | [44%, 52%] | −0.48% | +2.65% | −276.5% | +349.5% |
| 252d | 397 | 51% | [46%, 56%] | +0.80% | +15.61% | −578.0% | +715.9% |

**FADE — long SPY / short the name, the same rows inverted**

| | n | beat SPY | 95% CI | median | **mean** | worst |
| --- | --: | --- | --- | --- | --- | --- |
| 5d | 838 | 53% | [49%, 56%] | +0.32% | +0.10% | −50.0% |
| 21d | 805 | 53% | [49%, 56%] | +0.49% | +0.07% | −124.6% |
| 63d | 736 | 51% | [47%, 55%] | +0.10% | **−1.37%** | −281.8% |
| 126d | 634 | 52% | [48%, 56%] | +0.48% | **−2.65%** | −349.5% |
| 252d | 397 | 49% | [44%, 54%] | −0.80% | **−15.61%** | −715.9% |

**THE FADE IS THE MIRROR, NOT A DISCOVERY.** Fading is exactly `-excess`, so the hit-rates sum to
100% and the medians negate by construction. Nothing is learned by flipping the sign — the hit-rate
was already known from the follow table. What differs is the DISTRIBUTION, and that is the finding.

**IT WINS THE HIT-RATE AND LOSES THE MONEY.** At 63d the fade is right 51% of the time on a +0.10%
median — and has a **mean of −1.37%**. At 252d it is right 49% of the time and the mean is
**−15.61%**. Stock excess returns are right-skewed; inverting them converts a right tail into a
left tail. Every 5-point median win is paid for by a short in a name that tripled: the worst single
fade at 252d is **−715.9%**, which is not a bad quarter, it is the account.

**The median and the hit-rate are the wrong statistics for a position**, and this is the cleanest
example of it in the corpus: at every horizon past 21 days the fade wins on both and still
compounds negative. Only the mean compounds.

**Also note the follow side's means turn POSITIVE at longer horizons (+1.37%, +2.65%, +15.61%)
while its medians stay negative.** Same skew, right way up: the typical call underperforms and a
few large winners carry the average. That is the 1.59× beta book restated — and it is not skill,
because the mean is doing the work in a market that rose.

**Ruling: FALSIFIED.** There is no tradeable contrarian edge. The finfluencer literature's result
(≈1.2%/month against "antiskilled" influencers) does not reproduce here, and the reason is visible
in the table: their construction is a diversified portfolio with position limits, whereas the row
level shows what an unhedged fade of a momentum book actually costs.

`scripts/calls/contrarian.py` prints both tables with mean, worst and best beside every hit-rate,
so the hit-rate can never be read on its own.
