---
id:
status: recorded
date: 2026-09-11
prs: []
supersedes: data/themes/thesis/archive/ai-value-migration-2026-08-30.json
superseded-by:
---

# The AI card is re-scoped to the leg that can be measured — and it is not the same card

**WHAT.** Operator ruling 2026-09-11, **option 1 of two**. `ai-value-migration` is re-declared with
`--supersede`; the prior card is archived at
**`data/themes/thesis/archive/ai-value-migration-2026-08-30.json`**. The confirming test is
**scoped to the ABOVE leg plus MSFT**; **BELOW and BESIDE are recorded as unmeasurable on
disclosure**. The three falsifiers are unchanged — none depends on the confirming test.

## Why this is a scope, not a re-cut

The card asked for *"the disclosed model-agnostic AI monetization line"*. **No such line exists at
any of the nine.** And the failure is not a gap to fill later — **the filers say the measurement does
not exist**:

> **NVDA**, 10-K: *"it is difficult to estimate with any reasonable degree of precision **the impact
> of accelerated computing and AI models on our reported revenue**."*

**A trigger cannot be cut onto a line whose own filer says it cannot be constructed.**

## The new test, and the four names it reads on

**At the next quarterly print of MSFT, CRM, NOW and VEEV, the share of RPO CONVERTING to revenue over
the next twelve months GROWS.**

**Conversion, never accumulation** — a growing backlog satisfies this thesis and its null at once, so
the readable quantity is the **recognised share**, not the balance. MSFT states *"approximately
30%… over the next 12 months"*; NOW *"approximately 46% of these RPO over the following 12 months"*;
CRM and VEEV publish the twelve-month split, CRM as cRPO.

| leg | names | measurable? | why |
|---|---|---|---|
| **ABOVE** (app moat) | CRM, NOW, VEEV | **yes** | conversion disclosed |
| — | SAP | no | quarterly filing is a **526-word 6-K cover page**, not a 10-Q |
| — | META | no | **publishes no RPO at all** |
| **BELOW** (hyperscaler) | **MSFT** | **yes** | the one readable name |
| — | AMZN | no | **no RPO at all** |
| — | GOOGL | no | an amount, no conversion |
| **BESIDE** (silicon) | NVDA | **no** | no conversion line; attribution *"not estimable"* |

## TWO CONSEQUENCES, WRITTEN INTO THE CARD RATHER THAN LEFT TO THE READ-OUT

**1. A card whose three-leg claim can only be tested on one leg is NOT THE SAME CARD.** The test can
confirm or falsify the **ABOVE** leg. **It cannot speak to MIGRATION** — a *relative* claim that
requires the other two legs to compare against. **Same shape as the compute sub-driver having no
counter-leg**, and the same shape as the testability invariant's half (b): value claimed to be
leaving something needs a measurable counter-leg.

*MSFT is carried as an individually readable name, not as coverage of BELOW. One readable name out
of three does not make a leg measurable.*

**2. The 2026-12-15 read-out carries THREE qualifiers** — scoped to one leg; **GOOGL** absent from
the frozen basket on the observer-vocabulary prefilter defect **despite being a confirmed position**;
**SAP** absent as a foreign private issuer under the row-4 FPI gap.

## HOW VERIFIED

`vinci theme-thesis declare ai-value-migration --file … --supersede` → *"OK — card written … prior
card archived"*, archive present at the path above; mirror rebuilt via `frontend/build.py`.
`market_mistake`, `null_thesis`, `mechanism` and all three falsifiers are **byte-identical** to the
archived card — only `first_confirming` and the appended `note` entry differ.

---

# ITEM 3 — the sampling design, RULED 2026-09-11, NOT YET RUN

The question: **do the 168 ratified verdicts sit on the expensive side of the market's own line?** If
the market already separated regulatory depth / proprietary workflow data / systems of record from
ordinary software, the ratifies identify durability **already in the price**, and the tradeable set
is where the verdicts **disagree**.

**No multiple exists in committed data** — checked across every snapshot; `sic` and `market_cap` are
there, no multiple field anywhere. **So the charting pull is genuinely required**, which settles the
instrument question.

**But the stratifiers ARE committed, at full coverage:**

| arm | n | has market_cap | has SIC | both |
|---|---:|---:|---:|---:|
| ratified | 168 | 168 | 168 | **168** |
| passed | 189 | 189 | 189 | **189** |

**104 matched pairs are available** across 26 of 74 sector×size cells with both arms present.

**AND THE CONFOUND IS REAL, WHICH IS WHY MATCHING IS LOAD-BEARING RATHER THAN TIDY:**

| SIC 73 (business services / software) | ratified | passed | pairs |
|---|---:|---:|---:|
| large | **52** | **14** | 14 |
| mid | 36 | 31 | 31 |
| small | **24** | **34** | 24 |

**The basket is overwhelmingly one sector** — SIC 73 supplies **69 of the 104 pairs (66%)** — so
stratifying on sector is nearly moot. **The live confound is SIZE**: ratified skews **large**
(52 v 14) and passed skews **small** (24 v 34). Large names carry higher multiples for reasons that
have nothing to do with durability, so **an unmatched ratified-vs-passed comparison would largely
measure size and would manufacture a "the market already prices it" result.**

**THE DESIGN, RULED 2026-09-11:**

1. **Contrast: ratified vs passed** — same scan, same freeze, differing only on the verdict. The
   built-in control, per *"the control says no."*
2. **Matched pairs on SIC2 × size band**, never independent samples.
3. **Measure: the WITHIN-STRATUM percentile RANK of the forward multiple**, never the raw level.
4. **N = ALL 69 SIC-73 PAIRS, not a sample of 30** — ~13 panes against 6. **At N=30 the design
   cannot see its own threshold:**

   | SD of paired rank differences | N=30 | **N=69** | N=104 |
   |---:|---:|---:|---:|
   | 20 | 78% | **99%** | 100% |
   | 25 | 59% | **91%** | 98% |
   | 30 | **45%** | **79%** | 92% |
   | 35 | 35% | **66%** | 83% |

   *(true gap 10 rank points, α=0.05 two-sided)*

   **At SD=30 an N=30 null is more likely a miss than a finding — 45% power.** That is the failure
   mode this repo has now named twice: **a check that stays silent on what it cannot see reads as
   coverage.** An underpowered null would say *"no gap"* and mean *"couldn't tell"*, on the question
   deciding whether 168 names are underwritable.

   **And N=69 is the N at which the pre-registered threshold becomes detectable**, which is a
   stronger reason than power alone: the smallest gap visible at 80% power is **10.1 rank points at
   N=69 (SD=30)** against 15.3 at N=30. **The N and the threshold are matched, not chosen
   separately.** Taking all 69 also **removes the sampling step, and with it a place for selection
   to enter.**
5. **PRE-REGISTER, BEFORE THE PULL — three commitments, not one:**
   - **Threshold: a median within-stratum rank gap of ≥10 points** counts as *the market already
     prices it*. Face validity, never tuned on outcomes.
   - **The economic translation is pre-registered as a COMPUTATION, not a number**: at the stratum
     median, 10 rank points will be converted to **turns of multiple** on the pulled distribution
     and reported beside the rank gap. It cannot be stated now — the rank-to-turns mapping depends
     on the density of the multiple distribution, which is what the pull produces. Committing to
     report it is the part available in advance.
   - **THE UNDERPOWERED-NULL DISTINCTION:** a below-threshold result is reported **with its
     confidence interval**, so *"no gap"* and *"cannot tell"* are distinguishable **on the page**
     rather than by inference. A CI spanning the threshold is a non-result and must say so.
6. **The design must be able to return NO GAP**, and does.
7. **Output: the ratified names in the cheap tail** — where the verdict disagrees with the market.

**FRAME: SIC 73 ALONE — AND THE RULED SCOPE LIMIT IS WRONG ON THE FACTS, in the direction that makes
the frame BETTER.** The ruling stated that *"SIC 73 is software and computer services, so the
strongest ratifies — the non-manufacturable data and regulated-gate names — mostly sit outside it."*
**Measured: six of the seven named sit INSIDE.**

| | SIC | inside SIC 73? |
|---|---|---|
| VRSK | 7374 | **yes** |
| TRU | **7320** | **yes** |
| EFX | **7320** | **yes** |
| MCO | **7320** | **yes** |
| CSGP | 7389 | **yes** |
| MSCI | 7389 | **yes** |
| IQV | 8731 | no |

**SIC 73 is BUSINESS SERVICES, not software** — it carries consumer-credit-reporting (**7320**) and
data/analytics (7374, 7389) alongside prepackaged software (7372). **So the frame DOES reach the
regulated-gate and non-manufacturable-data cohort the thesis leaned on hardest**, which was the
stated reason for the limitation.

**What it actually excludes: 50 ratified names, 30% of the 168** — led by SIC 36 electronics (9),
61 credit institutions (7), 35 industrial machinery (6), 80 health services (4), 87 research/CRO (3,
IQV among them), 38 instruments (3). **The real limit is that the test cannot speak to the
HARDWARE, FINANCIAL and HEALTHCARE edges of the basket** — not to its regulated-data core.

*Composition of the 118 ratified inside SIC 73, all eight codes: 7372 prepackaged software **70** ·
7389 **17** · 7370 **11** · 7374 **8** · 7373 **6** · 7320 credit reporting **3** · 7371 **2** ·
7381 **1**. So the frame is software-weighted (59% of its ratifies) while still containing the
regulated-data names.*

**RUN THE TEST FIRST — DO NOT SERVE TEST AND SCREEN FROM ONE PULL.** The design answers a
**hypothesis** (*do ratified names sit systematically higher?*), which needs matched pairs. The
stated output is a **screen** (*which ratified names sit cheap?*), which needs coverage of every name
one would consider underwriting. **Different sample requirements.** If the test returns no systematic
gap the screen becomes more valuable and earns its own pull; if it returns a large gap the basket is
largely priced and the screen is hunting a small residual. **Sequence, not one pull serving both.**

**BOUNDARY.** Card: `data/themes/thesis/ai-value-migration.json` at this commit; archived prior at
`data/themes/thesis/archive/ai-value-migration-2026-08-30.json`. Census figures restated from
`docs/records/2026-09-11-ai-disclosure-census.md` (9 names, 18 primary documents, 881,731 words,
EDGAR 2026-09-11), not re-measured. Basket: `ai-value-migration`, freeze **2026-09-01**, 168
ratified / 189 passed. `market_cap` joined from `theme_universe_snapshot.jsonl` +
`universe_snapshot.jsonl` on `internal_id` (as-of **2026-08-24**, Polygon close × EDGAR shares);
`sic` from `securities.jsonl` + `issuers.jsonl`, 2-digit. Size bands: mega ≥$200bn, large ≥$10bn,
mid ≥$2bn, small below. Power figures: paired test, true gap 10 rank points, α=0.05 two-sided, normal approximation.
SIC codes 4-digit from the same snapshots. Measured 2026-09-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.** **The re-scoped card can no longer test its own headline
claim** — that is the point of recording consequence 1 in the card rather than the record, and it is
accepted deliberately rather than worked around. **The design is RULED but NOT RUN and no pane has been pulled**; the market-cap join is as-of 2026-08-24 while the basket froze 2026-09-01, a
**one-week vintage gap** that is immaterial for size *banding* and would not be for a level.
**Falsifier for the re-scope: any of AMZN, META, GOOGL or NVDA beginning to disclose RPO conversion
or an AI-attributed line** — at which point the excluded legs become measurable and the card is
re-scoped back.
