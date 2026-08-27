---
id:
status: shipped
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# A flow LIST is not his call; a flow ALERT is — and the tell is the cashtag count

**OPERATOR RULE (2026-08-28).** `flow_spam` means the multi-ticker FLOW LIST — the
*"Top Bullish Flow: $NVDA $2.4M · $TSLA $2.5M …"* format, a report of where money went rather than
a view. **A post naming only ONE OR TWO cashtags is not that**, whatever else it turns out to be.

**The corpus agrees on the clean side and is a mess on the other.** All 320 flow-LIST posts
(4–8 cashtags, 1,407 rows) are classed `flow_spam` with 100% consistency — that part the labeller
gets right. The single-ticker flow ALERTS it cannot place: 29 "Alpha Gold Alert" posts split
three ways across `promo` (12), `flow_spam` (12) and `signal_candidate` (6). Same template, three
answers.

**116 rows contradicted the rule.** 41 read so far, and the operator did NOT apply it mechanically:

| destination | n |
| --- | --: |
| `signal_candidate` | 34 |
| `pnl_report` | 4 |
| `noise` | 3 |
| `flow_spam` | **0** |

`This 🐋 PRINTED $MCD +12% since this flow` → `pnl_report`. `+8% $META since these buyers showed
up` → `noise`. `$ARM whale is buying more calls for 2025` → a call. The rule says what these are
NOT; the destination needed a reader.

**A RECOMMENDATION MADE AND WITHDRAWN, recorded because it was published.** One row came back kept
as `flow_spam` on a single ticker, and this record's first draft concluded the ticker count was
"a prior, not a law" and that the guard should NOT ship. That row was an operator slip and was
corrected to `signal_candidate` — after which **zero** of the 41 carry `flow_spam` on a ≤2-ticker
post. The reversal is the point: one counterexample was enough to talk a rule down, and it was not
a counterexample. Check whether the exception is real before rewriting the rule around it.

**THE GUARD IS SHIPPABLE, BUT NOT YET.** `flow_spam` + ≤2 cashtags is now a contradiction a test
can detect. It cannot be pinned while **75 rows** still carry it; the guard lands when the backlog
is clear.

**THE PROMOTED ALERTS ARE NOT THE FLOW-SPAM PROBLEM IN NEW CLOTHES.** The original audit removed
flow rows because they scored 50.0% on a +0.0% median — coin-flip noise. Measured as their own
bucket, the 34 promoted alerts land on top of the rest of the book:

| | direction-correct | median excess |
| --- | --- | --- |
| flow alerts → bullish call (34) | **56%** CI [39%, 71%] | −0.34% |
| every other bullish `signal_candidate` (1,521) | **55%** CI [52%, 57%] | −0.41% |

Indistinguishable, on 34 rows — which is the answer that matters: they are ordinary calls, so the
distinction is doing real work rather than re-importing noise.

**Scoring.** 3,242 → 3,273 rows; **zero** already-scored rows changed verdict. Direction-correct
51.06% → **51.09%** of 2,854. Hand labels 484 → **557**.
