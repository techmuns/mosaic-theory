---
id:
status: falsified
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# 65 kinds of call beat SPY in-sample. None of them held. The variable is the quarter.

**The question.** The class-by-horizon table averages good and bad together, so: which KIND of
bullish call beats SPY under a year? Searched over ten post-time attributes — class, specificity,
action, target type, conditional, retrospective, video, cashtag count, whether a horizon was stated,
and where the stated target sat relative to the last printed close — across four horizons.

**Built to fail honestly.** Only attributes a reader knew AT POST TIME are eligible; no realised
return, no target-hit, nothing from the window. The search runs on rows posted **before
2025-09-01** and every survivor is re-measured untouched on rows posted **after**. Split by TIME,
not at random — a random split leaks the same name across both sides and shares the regime.

**The result.**

| | |
| --- | --- |
| cells tested in discovery (n≥25) | 144 |
| cells whose 95% CI cleared 50% beat-SPY | **65** |
| expected by chance at 144 tests | ~3.6 |
| **cells that held in the holdout** | **0** |

Not one. And the failures are not scattered around 50% — they cluster at **28–42%**. The strongest
discovery cells invert hardest: `target_gap 25%+ above` goes 65% → 28%; `specificity A` 64% → 35%;
`horizon_stated yes` 64% → 36%; `class pnl_report` 71% → 41%.

**WHAT THE 65 CELLS WERE ALL MEASURING IS THE QUARTER.**

| quarter posted | n | beat SPY @63d | median excess |
| --- | --: | --- | --- |
| 2024Q3 | 268 | **74%** | +12.34% |
| 2024Q4 | 397 | 44% | −4.49% |
| 2025Q1 | 346 | 50% | +0.09% |
| 2025Q2 | 241 | 66% | +8.73% |
| 2025Q3 | 358 | 62% | +8.69% |
| **2025Q4** | 299 | **22%** | **−8.97%** |
| 2026Q1 | 164 | 43% | −1.80% |
| 2026Q2 | 88 | 50% | +0.26% |

The discovery window is dominated by 2024Q3 and 2025Q2–Q3 (74%, 66%, 62%); the holdout opens on
2025Q4 (22%). **Every cell that "worked" worked because of when it was posted, not what it was.**
Any attribute common enough to clear n≥25 in the good quarters inherits their rate — which is why
65 of 144 cleared, an implausible number that was itself the tell.

**RULING: FALSIFIED.** There is no type of bullish call in this corpus that beats SPY out of
sample. This is not "we need more features" — the features were fine and the search was fair. The
signal is swamped by a quarterly swing of 74% → 22%, which is ~50 points against a per-type effect
that would have to be a handful.

**Why this was worth running rather than refusing.** The house rule forbids tuning on forward
returns, and an in-sample-only version of this search would have produced 65 publishable "findings"
— including several already half-believed here, like `pnl_report` looking strong and the flow-print
edge. The holdout is what separates them, and it cost one script. The correct use of a corpus this
size is to REFUTE patterns cheaply, not to mine them.

`scripts/calls/what_works.py` re-runs it. It prints the chance-expectation beside the hit count on
purpose, so the next reader sees 65-against-3.6 before they see the ranked table.
