---
id:
status: falsified
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# Fading him wins the coin flip and loses the money

**The hypothesis, from the finfluencer literature** (trading against antiskilled influencers earns
~1.2% monthly out-of-sample): if his calls are worse than the index, take the other side.

**The arithmetic is not the test.** Market-neutral fading returns exactly MINUS his excess, so his
48% beat-SPY is the fader's 52% BY DEFINITION. Reporting that would be reporting his 48% twice.
What is not determined in advance is significance, out-of-sample stability, and cost — so the test
is those three.

## It wins more often and loses more money

| market-neutral fade, all rows | n | win rate | median | **mean** | t |
| --- | --: | --- | --- | --- | --- |
| 5d | 3,252 | 52% | +0.16% | −0.07% | −0.47 |
| 21d | 3,157 | 53% | +0.34% | −0.43% | −1.25 |
| **63d** | 2,931 | **51%** | **+0.11%** | **−3.08%** | **−4.96** |
| **126d** | 2,627 | **51%** | **+0.26%** | **−2.30%** | **−2.92** |

Positive win rate, significantly NEGATIVE mean. That gap is the whole story: his book is
right-skewed high-beta, and the short side of a right-skewed distribution wins small repeatedly and
loses enormously once. Shorting the name that went +738% pays for a lot of 51% win rates.

## The apparent edge is a regime bet, and it flips sign

| market-neutral, mean per trade | discovery (pre 2025-09) | holdout (post) |
| --- | --- | --- |
| 21d | **−1.67%** (t −3.85) | **+1.70%** (t +3.12) |
| 63d | **−5.87%** (t −7.48) | **+2.78%** (t +2.87) |
| 126d | **−5.13%** (t −5.72) | **+6.50%** (t +4.12) |

**Both halves significant, opposite signs, at every horizon.** Fading lost heavily while he was
good (2024Q3, 2025Q2–Q3) and won heavily while he was cold (2025Q4 on). It is a bet on which
regime you are in, and the full-sample near-zero is those two halves cancelling.

## Costs finish it

Annualised mean net return on the market-neutral leg:

| | 0bp | 25bp | 50bp | turns/yr |
| --- | --- | --- | --- | --- |
| 5d | −3.8% | −16.4% | −29.0% | 50.4 |
| 21d | −5.1% | −8.1% | −11.1% | 12.0 |
| 63d | −12.3% | −13.3% | −14.3% | 4.0 |
| 126d | −4.6% | −5.1% | −5.6% | 2.0 |

Negative before a single basis point, and this ignores compounding, variance drag, borrow beyond
the haircut, and slippage on names this illiquid — all of which make it worse.

## The outright short confirms the beta finding

Shorting the names against cash loses at every horizon over the full sample (mean −0.18 / −0.77 /
−4.19 / −5.28%), because it is short a 1.59× book in a market that rose. That is not a separate
result; it is the beta finding arriving from the other direction.

## Ruling

**FALSIFIED.** There is no contrarian edge here either. The literature's finding does not
transfer — it rests on classifying influencers as antiskilled on PAST performance and then trading
forward, which is exactly the discovery/holdout structure that fails here: his skill classification
is not stable across the split, so a fade fitted on one period inverts on the next.

**This closes the search.** Follow him: no edge. Fade him: no edge. Filter by class: nothing. Filter
by trend: nothing. Slice by any of ten post-time attributes: 65 in-sample winners, zero survivors.
The corpus has now been asked from every direction available to it and returns the same answer.
