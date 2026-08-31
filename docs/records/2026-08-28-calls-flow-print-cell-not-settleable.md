---
id:
status: shipped
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# The flow-print cell holds at 59%, and it cannot be settled by reading more

**The question.** `flow_spam` on a 1–2 cashtag post, carrying a direction — the "flow print" bucket
— read **60% direction-correct on a +2.24% median excess** against his own calls' 49% / −0.44%.
On 43 rows that was a pointer, not a finding. A batch was run to fill it.

**53 rows read, and the estimate did not move.**

| | rows | direction-correct | 95% CI | median excess |
| --- | --: | --- | --- | --- |
| flow prints, before | 43 | 60% | [44%, 73%] | +2.24% |
| **flow prints, after** | **49** | **59%** | **[45%, 72%]** | **+2.28%** |
| his own calls | 2,194 | 49% | [47%, 51%] | −0.44% |

Stability is itself informative — 6 new rows and the point estimate moved 1pp, the median excess
0.04pp. But the interval closed by **2pp**, from 29 to 27.

**WHY IT WILL NOT CLOSE: the yield is 13%.** The candidate queue matches on what a post SAYS — a
strike, an expiry, a contract count, the house's alert wording — and deliberately over-catches,
because a regex cannot tell the tape from him talking about the tape. Of 53 rows read, **7 landed
in the cell**; the rest were his own calls (16), promos (8), P&L reports (12) and noise (3). The
arithmetic that follows is the point of this record:

| target | rows needed IN the cell | rows to READ at 13% yield |
| --- | --: | --: |
| ±10pp — edges clear of 49% | 93 (+44) | **~340** |
| ±7.5pp — comfortably separated | 166 (+117) | **~900** |
| ±5pp — a number worth quoting | 372 (+323) | ~2,500 |

**RULING: STOP.** ~340 rows of reading to learn whether 59% is really 55% or really 63% does not
change what anyone does with it. The honest statement is what the data already supports: **flow
prints look better than his own calls, on 49 rows, and the gap is not confirmed.**

**What makes it interesting is that it is the ONLY bucket pointing up.** Seven interventions have
left the headline pinned at ~51% and every structural hypothesis has died under test. This one has
now survived a deliberate attempt to move it — the weakest possible form of evidence, but the first
thing in this corpus that has not shrunk when measured properly.

**Scoring.** 3,307 → 3,305 rows; one already-scored row changed verdict. Direction-correct 51.18%
→ **51.11%** of 2,886. Hand labels 625 → **678**.
