---
id:
status: falsified
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# There is no edge in his calls. The one positive number is beta.

**The bottom line, over all 3,305 directional calls, all classes, against SPY on the identical
window:**

| horizon | n | beat SPY | 95% CI | median excess | 95% CI (bootstrap) |
| --- | --: | --- | --- | --- | --- |
| 5d | 3,252 | 48% | [47%, 50%] | −0.16% | [−0.32%, +0.02%] |
| **21d** | 3,157 | **47%** | **[46%, 49%]** | **−0.34%** | **[−0.60%, −0.10%]** |
| 63d | 2,931 | 49% | [47%, 51%] | −0.11% | [−0.42%, +0.18%] |
| 126d | 2,627 | 49% | [47%, 51%] | −0.26% | [−0.62%, +0.10%] |
| 252d | 1,896 | **56%** | [54%, 58%] | **+3.44%** | [+1.78%, +5.41%] |

At three weeks he is **significantly WORSE than the index** — both the rate and the median excess
exclude the null. At 5, 63 and 126 days he is indistinguishable from it. Only 252 days is positive.

**THE 252d LIFT IS NOT SURVIVORSHIP.** Holding the subsample fixed — the same 1,896 calls measured
at every horizon — the beat-SPY rate still climbs 48 → 50 → 54 → 52 → **56%**. So it is not merely
that the old calls came from good quarters; something does rise with holding period.

**IT IS BETA.** Split those same 252-day windows by what SPY did over them:

| SPY over the window | n | beat SPY | median call | median SPY | median excess |
| --- | --: | --- | --- | --- | --- |
| **rose** | 1,420 | **64%** | +29.71% | +17.04% | +11.04% |
| **fell** | 476 | **33%** | −26.99% | −17.37% | −5.57% |

He beats the index when the index rises and loses to it when it falls, with a median
call/SPY return ratio of **1.59×** in up windows. That is the signature of a high-beta basket, and
a passive one would produce exactly this table while carrying no information whatsoever. His book
is TSLA / NVDA / PLTR / COIN — amplified market, not selection.

The 2024-08 → 2026-08 window is net up, so the long horizon collects the amplification and prints
it as a +3.44% median excess. Over a down window the same 1.59× runs the other way, and the
2025Q4 cohort (22% beat-SPY, −8.97% median) is what that looks like.

**THE COMPLETE ANSWER, assembled over this audit:**

1. Direction-correct ~51% on 2,886 closed calls — a coin flip, stable across **seven** interventions.
2. Beats SPY on 47–49% of rows at every horizon under a year; significantly worse at 21 days.
3. **65 of 144** in-sample "types that beat SPY" — against 3.6 expected by chance — and **zero**
   held on a time-split holdout; they were measuring the quarter (74% → 22%).
4. The only positive aggregate is at one year and is **1.59× beta**, not selection.

**No edge. Not a weak edge, not an edge needing more data — the corpus is 3,305 scored calls over
25 months and every direction it was interrogated from returned the same answer.**

**What was worth having.** The apparatus, not the verdict: a corpus with measured error bars
(class 99%, bias 81%), a scorer whose conventions are pre-registered and reused unchanged by every
analysis here, a holdout that refuted six months of plausible-looking patterns in one script, and a
worked example of the failure mode the fund's own no-tuning rule exists to prevent — 65 findings
that all dissolve. That is what this subsystem was built to be able to say, and it said it about
someone else's calls before ever being pointed at our own.
