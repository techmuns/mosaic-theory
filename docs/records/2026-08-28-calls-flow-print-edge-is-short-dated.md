---
id:
status: recorded
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# The flow-print edge is short-dated, and it is gone by six months

**The test.** The flow-print bucket read 59% direction-correct on a +2.28% median excess at the
STATED horizon. Put every call on the same clock — `score_call` reused unchanged, once per
(call, horizon) — and the single number splits into a shape.

| | 5d | 21d | 63d | 126d | 252d |
| --- | --- | --- | --- | --- | --- |
| **flow prints** — n | 50 | 49 | 49 | 49 | 19 |
| direction-correct | 58% | **67%** | 59% | **51%** | 84% |
| median excess | +1.52% | **+3.85%** | +2.28% | **−4.42%** | +18.55% |
| beat SPY | 62% | 65% | 53% | 47% | 74% |
| **his own calls** — n | 2,485 | 2,403 | 2,232 | 1,994 | 1,434 |
| direction-correct | 49% | 49% | 50% | 51% | 64% |
| median excess | −0.23% | −0.44% | −0.37% | −0.41% | +2.09% |
| beat SPY | 47% | 46% | 47% | 48% | 55% |

**THE EDGE PEAKS AT THREE WEEKS AND IS GONE BY SIX MONTHS.** 21d is the best cell on every measure
(67% correct, +3.85% median, 65% beating SPY). By 126d the bucket is **51% on a −4.42% median** —
indistinguishable from his own calls and worse on excess. That decay is the finding: it is what an
options-flow signal SHOULD look like, because the position being followed has an expiry. A durable
edge that survived to six months would have been the suspicious result.

**THE 252d CELL IS NOT USABLE.** Only 19 of 49 have 252 days elapsed, and they are necessarily the
OLDEST — posted before 2025-08. That cell measures a different market, not a longer hold, and his
own calls jump to 64% there for the same reason. **Read it as survivorship, not as an 84% hit-rate.**

**AND HIS OWN CALLS UNDERPERFORM THE INDEX.** Across every horizon under a year, `signal_candidate`
directional calls beat SPY on **46–48%** of rows with a median excess of −0.2% to −0.4%. Flat, and
slightly negative. Seven interventions have left the headline at ~51% direction-correct; this is
the same fact stated against the benchmark, which is the honest way to state it.

**STATUS: `recorded`, not `shipped`.** 49 rows. The shape is suggestive and the decay is
mechanistically plausible; neither makes it a finding. The cell cannot be closed by more labelling
(13% yield — see the previous record), so the way to test it is FORWARD, on flow prints as they are
posted, not by reading more of the past.

`scripts/calls/forward_ladder.py` runs it.
