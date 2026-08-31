---
id:
status: falsified
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# Neither the class tag nor a trend filter separates his calls from his noise

**Two filters asked of the 3,305 directional calls: does the class tag select the good ones, and
would a technical overlay screen out the noise. Neither does.**

## The literature was consulted first, and it shaped the design

- **Sullivan, Timmermann & White (1999)** tested 7,846 technical trading rules on a century of Dow
  data; almost none survived White's Reality Check for multiple comparisons. That is the precedent
  for the second question and the reason this build tests **exactly one** pre-registered rule
  rather than a family.
- **Time-series momentum** (Moskowitz/Ooi/Pedersen; 58 assets, a 1966–85 out-of-sample replication)
  is one of the few technical effects with real support — which is precisely why filtering a signal
  by trend and crediting the caller is an ERROR: the filter brings its own returns.
- The **finfluencer** literature reports that influencers preferentially recommend names with
  strong past performance and high volume, and that recommendations are frequently followed by poor
  performance. Both match what this corpus already showed (a 1.59× beta book).

## 1. Class does not select

Beat-SPY rate by class, all directional calls:

| class | 21d | 63d |
| --- | --- | --- |
| `signal_candidate` (2,401) | 46–48% | 47–48% |
| `promo` (358) | 45–49% | 49–53% |
| `pnl_report` (236) | 48–55% | 52–60% |

Nothing clears the noise except `pnl_report`, and that class is posts written BECAUSE a trade
already worked — selected on the past by construction, so its forward return is not a signal. This
also repeats what the time-split holdout already found: 65 in-sample class/attribute cells cleared
50%, and none held.

## 2. The trend filter does nothing, and the placebo is why we can say so

The rule, fixed in advance: was the last printed close above its **50-day** average at post time?
(50 and not 200 — the 200-day is computable on only 56% of rows, and that 56% is his REPEAT names,
so filtering on it selects a subsample rather than a condition.)

| | above the average | below | lift |
| --- | --- | --- | --- |
| his calls, 21d | 1,788 · **47%** | 1,367 · 48% | **−1.5%** |
| his calls, 63d | 1,659 · **49%** | 1,271 · 49% | **+0.1%** |
| placebo, 21d | 1,697 · 48% | 1,362 · 50% | −2.2% |
| placebo, 63d | 1,560 · 48% | 1,263 · 52% | −3.9% |

**Filtering to above-trend does not raise the beat-SPY rate. It lowers it slightly at 21 days.**

**THE PLACEBO CHANGED THE ANSWER, AND ITS FIRST VERSION WAS WRONG.** The placebo re-runs each call
on a date he did NOT post, same ticker, same bias. The first cut drew that date from the ticker's
whole history and produced a placebo lift of −6.9%, which made his −1.5%/+0.1% look like a real
edge over the counterfactual. That was a REGIME comparison, not a timing one: a date sampled from
two years away is a different market. Bounded to ±90 days the placebo lift becomes −3.9%, and the
difference-of-differences drops to +0.7% / +4.0% — quantities whose components each carry ±3pp,
so not distinguishable from zero.

## Ruling

**FALSIFIED.** Neither filter separates signal from noise here. The class tag was already known to
be 99% accurate, so this is not a labelling failure — the tags are right and the categories simply
do not differ in forward performance. And a trend overlay adds nothing to a book that is already
1.59× beta: it selects for the same names in the same direction.

The general lesson is the one the literature gives for free: **a filter that improves a backtest is
the expected outcome, not evidence.** The only informative version is filter-versus-placebo, and
building the placebo correctly mattered more than choosing the indicator.

`scripts/calls/trend_filter.py` re-runs it and prints the placebo beside every result.

Sources: Sullivan/Timmermann/White via <https://homepage.ntu.edu.tw/~ckuan/pdf/snoop01.pdf>;
White (2000) <https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00152>; time-series
momentum <https://www.sciencedirect.com/science/article/pii/S0304405X11002613>; finfluencer
recommendations <https://www.sciencedirect.com/science/article/abs/pii/S0165176525003489>.
