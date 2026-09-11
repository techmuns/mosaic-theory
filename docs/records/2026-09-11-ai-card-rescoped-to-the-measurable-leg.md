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

# ITEM 3 — the sampling design, PROPOSED not run

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

**The proposed design:**

1. **Contrast: ratified vs passed** — same scan, same freeze, differing only on the verdict. The
   built-in control, per *"the control says no."*
2. **Matched pairs on SIC2 × size band**, not independent samples — kills the confound by
   construction and halves the N.
3. **Measure: within-stratum percentile RANK of the forward multiple**, never the raw level.
4. **N = 30 pairs = 60 names ≈ 6 panes**, drawn proportionally across the three SIC-73 bands to
   preserve the size mix. The full 104 pairs would be ~19 panes; the sample answers a **class**
   question, not a per-name one.
5. **PRE-REGISTER THE THRESHOLD BEFORE THE PULL** — a median within-stratum rank gap of **≥10
   points** counts as *the market already prices it*. Set now, from face validity, never after
   seeing numbers; this is the `ai-compute-platform` lesson.
6. **The design must be able to return NO GAP**, and does — a matched-pair test yields a signed
   median difference with an interval.
7. **The output either way is the tradeable set**: if a gap exists, the interesting names are the
   **ratified names in the cheap tail** — where the verdict disagrees with the market.

**Three things to rule on**: the threshold (≥10 points), N (30 pairs), and whether the frame is the
whole basket or SIC 73 alone — since the other 25 sectors supply 35 pairs across 25 cells, which is
one or two pairs each and will not carry a stratified estimate.

**BOUNDARY.** Card: `data/themes/thesis/ai-value-migration.json` at this commit; archived prior at
`data/themes/thesis/archive/ai-value-migration-2026-08-30.json`. Census figures restated from
`docs/records/2026-09-11-ai-disclosure-census.md` (9 names, 18 primary documents, 881,731 words,
EDGAR 2026-09-11), not re-measured. Basket: `ai-value-migration`, freeze **2026-09-01**, 168
ratified / 189 passed. `market_cap` joined from `theme_universe_snapshot.jsonl` +
`universe_snapshot.jsonl` on `internal_id` (as-of **2026-08-24**, Polygon close × EDGAR shares);
`sic` from `securities.jsonl` + `issuers.jsonl`, 2-digit. Size bands: mega ≥$200bn, large ≥$10bn,
mid ≥$2bn, small below. Measured 2026-09-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.** **The re-scoped card can no longer test its own headline
claim** — that is the point of recording consequence 1 in the card rather than the record, and it is
accepted deliberately rather than worked around. **The sampling design is NOT RUN and no pane has
been pulled**; the market-cap join is as-of 2026-08-24 while the basket froze 2026-09-01, a
**one-week vintage gap** that is immaterial for size *banding* and would not be for a level.
**Falsifier for the re-scope: any of AMZN, META, GOOGL or NVDA beginning to disclose RPO conversion
or an AI-attributed line** — at which point the excluded legs become measurable and the card is
re-scoped back.
