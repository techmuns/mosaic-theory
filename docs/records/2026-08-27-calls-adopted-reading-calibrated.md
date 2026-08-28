---
id:
status: shipped
date: 2026-08-27
prs: [511]
supersedes:
superseded-by:
---

# The adopted reading is calibrated, and there is no rule inside it

**Closing entry for four rounds of hand labelling.** 409 hand labels, of which 321 are UNBIASED
(the other 88 came from priority band 1, which selects FOR reader disagreement and therefore cannot
carry a base rate). The bearish pass — 35 rows, `signal_candidate` + `bearish`, random order — was
the last one needed.

## What the adopted reading is worth

| it says | trust it | n |
| --- | --- | --- |
| `none` | **97%** [91%, 99%] | 77 |
| directional | **76%** [69%, 83%] | 140 |
| direction specifically WRONG | **4%** | 140 |

Of the 24% of directional labels that do not hold, **20 points are over-commitment** (the post was
not a call) and only **4 are a wrong direction**. That split is the whole finding: the reading's
weakness is deciding WHETHER a post is a call, not WHICH WAY.

## Every structural hypothesis failed a proper test

| hypothesis | how it died |
| --- | --- |
| the reading never gets direction wrong | 0/63 in band 1 → **8/142 = 6%** unbiased |
| it over-commits specifically on `bearish` | 45% vs 87% in band 1 → **68% vs 67%** unbiased |
| `promo` rows are a coin flip | Fisher **0.009 → 0.064** once the comparison arm was measured |
| it is better on bearish posts | 83% vs 73%, Fisher **p = 0.29** |
| text signatures predict over-commitment | best gate 58% precision — kills as many real calls as it catches |
| multi-cashtag posts are the failure mode | those rows disagree at **7%** vs 24% single-ticker |

Six hypotheses, six failures. **The honest conclusion is that there is no replicable RULE — there is
a CALIBRATION.** Accept `none`; treat a directional label as a 76% prior; spend human attention on
the over-commitment band rather than on a text signature that does not exist.

**A METHOD NOTE WORTH KEEPING.** Two of the six survived only because a small comparison arm was
noisy — the promo effect tested at p=0.009 against a 54-row arm and dissolved at p=0.064 against a
125-row one. Both were reported as findings before the arm was measured. **Measure the arm you are
comparing against, not just the one you are interested in.**

## Scoring

3,246 → 3,242 rows. ONE previously-scored row changed verdict — `$SPY` 2026-03-31, a
`bearish → bullish` re-read that re-signed its return. Direction-correct **51.06% of 2,824**; the
HAND subset 55.9% of 202.

**Seven independent interventions have now left the headline at ~51%**: noise removal, the adopted
reading, the 197-ticker backfill, the rename splice, and four rounds of hand correction. That number
is no longer provisional — nothing that has been tried moves it.
