---
id:
status: shipped
date: 2026-08-27
prs: [511]
supersedes:
superseded-by:
---

# The over-commit rate is measured, and the promo effect does not survive measuring it

**The batch.** 71 hand rows drawn with `class = signal_candidate`, `bias = bullish`, random order —
the first sample aimed by the power note rather than by the default sort. Imported with the prior
220; hand labels **303 → 374**.

**What an adopted `bullish` on a `signal_candidate` is worth: 51/71 = 72%** intact, CI [60%, 81%].
The other 20: 8 `mixed`, 5 `none`, 2 `neutral` (abstain) and **5 `bearish` (flip)**.

**THE OVER-COMMIT RATE IS NOW A NUMBER.** Two independent samples land within 2pp:

| | rate | 95% CI |
| --- | --- | --- |
| earlier random sample | 10/54 = 19% | [10%, 31%] |
| this batch | 15/71 = 21% | [13%, 32%] |
| **combined** | **25/125 = 20%** | **[14%, 28%]** |

**THE PROMO EFFECT DID NOT SURVIVE.** Fisher exact, promo vs `signal_candidate` over-commit:

| | comparison | p |
| --- | --- | --- |
| before this batch | 7/12 vs 10/54 | **0.009** |
| after | 7/17 vs 25/125 | **0.064** |

The promo arm barely moved (7/12 → 7/17). What changed is the COMPARISON arm: at n=54 it was noisy
enough to make a 20%-vs-41% gap look decisive. Measuring it properly at n=125 dissolved the result.
**Recorded because the earlier reading was published as "separated" and it was not** — the finding
was an artifact of the arm nobody was looking at.

**"ZERO DIRECTION FLIPS" IS DEAD.** Combined **8/142 = 6%**, CI [3%, 11%]. The original claim came
from the contested band, where it was 0/63.

**A CAVEAT THAT MUST TRAVEL WITH THIS BATCH:** it was drawn `bias = bullish` ONLY, so all 5 of its
flips are necessarily `bullish → bearish`. That CANNOT be read as "the reading over-states
bullishness" — the sample could not have produced the opposite. The bearish pass (678 rows) is what
tests it, and the bench is left filtered and ready for it.

**Scoring.** 3,261 → 3,246 rows (15 dropped to non-directional). Four previously-scored rows changed
verdict, ALL FOUR because a bias flip re-signed the return. Direction-correct **50.99% of 2,828**;
the HAND subset 57.7% of 175. Six independent interventions now, still ~51%.

**Also: the header counts the data instead of remembering it.** `5,641 posts · 8,185 rows ·
214 tickers · 83 hand · 8,102 adopted` were literals typed when the bench was built. After the
ticker backfill and 374 hand labels the header still said 83 and 214 — wrong on two of five figures
while sitting above the numbers it describes. Now derived from `POSTS`/`ROWS` at paint time:
`411 tickers · 7,811 adopted · 374 hand`.

**Convention recorded (operator, 2026-08-27):** `enter_long` and `add` are labelled
interchangeably. Safe today — `action` is carried by `ingest`/`sheet`/`audit` and read by NOTHING
that computes: not `score.py`, not `callscore.js`. If `action` ever becomes load-bearing, this
conflation must be surfaced before it is used.
