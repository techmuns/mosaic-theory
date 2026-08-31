---
id:
status: recorded
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# Bullish calls by class and horizon: the 252d column is a bull market, and the rest is flat

**The run.** Every bullish row (2,459), split by `post_class`, across 5/21/63/126/252 trading days,
against SPY over the identical window — and repeated under 15- and 30-day cool-downs that keep only
the FIRST bullish row per ticker in a rolling window. `scripts/calls/bullish_by_class.py`.

**THE 252d COLUMN IS THE MARKET, NOT THE CALLER.** Every class reads 68–92% direction-correct at
252 days, including `noise` (88%) and `engagement` (100% on 3 rows). Median SPY over the same
windows is **+17%**. A bullish call held a year in this tape is right most of the time because the
tape went up — that column measures the drift, and the only honest reading of it is against SPY,
where the edge collapses.

**AGAINST SPY, `signal_candidate` IS FLAT-TO-NEGATIVE AT EVERY HORIZON UNDER A YEAR.**

| `signal_candidate`, no cool-down | 5d | 21d | 63d | 126d | 252d |
| --- | --- | --- | --- | --- | --- |
| n | 1,793 | 1,738 | 1,590 | 1,485 | 1,042 |
| direction ok | 52% | 53% | 55% | 57% | 81% |
| median call | +0.20% | +0.70% | +3.33% | +4.61% | +29.18% |
| median SPY | +0.35% | +1.31% | +3.91% | +6.68% | +16.97% |
| **median excess** | **−0.24%** | **−0.54%** | **−0.21%** | **−0.26%** | +9.89% |
| **% beat SPY** | **48%** | **47%** | **49%** | **49%** | 64% |

Under 49% beating SPY at every horizon to six months. His own stated calls, held blind, are a
slightly-worse-than-index bet.

**THE COOL-DOWN CUTS THE COHORT BY 61% AND MOVES NOTHING.** 2,459 → 967 rows at 15 days, 747 at 30.
`signal_candidate` median excess goes −0.24/−0.54/−0.21/−0.26% to −0.28/−0.45/−0.37/−1.01% (15d) and
−0.37/−0.65/−0.54/−0.72% (30d); % beating SPY stays at 47–48% throughout. **The repetition was not
inflating the result** — one enthusiastic week was not carrying the average, which was a live
worry and is now closed. What the cool-down DOES kill is the 252d illusion: 81% → 71%, and median
excess +9.89% → +2.10%, because the repeats cluster in names that ran.

**WHERE THE ONLY POSITIVE CELLS ARE.** `flow_spam` (the single-ticker prints) at 21d: 64% correct,
+3.72% median excess, 62% beating SPY — and it SURVIVES the cool-down (61%, +3.47%, 61% on 23 rows).
`pnl_report` at 63d looks strong (+8.16%) but that is a class of posts written BECAUSE the trade
already worked, so its forward return is selected on the past and it should not be read as a signal.

**STATUS `recorded`.** These are descriptive aggregates over a labelled corpus with known error
bars (bias 81%, class 99%, ~3pt drag from unverified rows), not a validated edge. Nothing here
gates anything; the calls subsystem remains a research input that touches no screen, ranker,
ledger or spread.
