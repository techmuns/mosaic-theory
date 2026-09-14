---
id:
status: recorded
date: 2026-09-14
prs: []
supersedes:
superseded-by:
---

# The market already prices the discriminator — the AI ratifies sit ~29 rank points expensive

**WHAT.** All 13 panes landed 2026-09-14. The pre-registered test **returns a result, not a
silence**: ratified names sit **+29.76 median rank points** above their matched passed counterparts
**within their own size stratum**, 95% CI on the mean **[+12.19, +33.28]** — which **excludes the
pre-registered ±10 threshold from outside**. **44 of 56 pairs positive, p < 0.0001.**

**The 168 ratifies identify durability that is already in the price.** The tradeable set is where the
verdicts **disagree** with the market, and that set is **seven names**.

## The test

Pre-registered before the pull: matched pairs on SIC2×size, **within-stratum percentile rank** of the
forward multiple, threshold **≥10 rank points**, result reported **with its CI** so *"no gap"* and
*"cannot tell"* are distinguishable on the page.

| | |
|---|---|
| pairs measured | **56** of 69 |
| median rank gap (R − P) | **+29.76** |
| mean | +22.74 (SD 40.25, SE 5.38) |
| **95% CI on the mean** | **[+12.19, +33.28]** |
| sign test | **44 of 56** pairs with ratified above |
| t / p | +4.227 / **p < 0.0001** |
| minimum detectable at 80% power, observed SD | 15.1 points — **the observed gap clears it** |

**Verdict: ALREADY PRICED.** The CI's lower bound is **+12.19**, above the threshold — the gap is
≥10 with 95% confidence. *(A first cut of the verdict logic encoded only two states — "no gap" and
"cannot tell" — and mislabelled this decisive result as "cannot tell". The third state, a CI that
excludes the threshold from OUTSIDE, was missing. Corrected; the arithmetic was never wrong.)*

**It holds in every stratum**: large **+37.50**, mid **+28.57**, small **+28.57** (medians).

**And it survives the window sweep** — the anchor-sweep discipline applied to the measurement date:

| window | pairs | median gap | 95% CI | positive |
|---|---:|---:|---|---:|
| 14d | 56 | +28.57 | [+12.4, +33.4] | 44/56 |
| **28d** *(registered)* | **56** | **+29.76** | **[+12.2, +33.3]** | 44/56 |
| 60d | 56 | +28.57 | [+12.1, +33.0] | 43/56 |
| 120d | 57 | +28.57 | [+14.4, +33.7] | 45/57 |
| 365d | 54 | +32.14 | [+17.8, +38.3] | 42/54 |

**Not a window artifact.** The CI's lower bound never falls below +12.1.

## The economic translation, as pre-registered

Registered as a **computation**, not a number, because rank-to-turns needs a density only the pull
produces. At each stratum's median multiple:

| stratum | n | median fwd P/E | 10 rank points = | the observed gap = |
|---|---:|---:|---:|---:|
| large | 25 | 19.3x | +0.8x | **+12.9x** |
| mid | 57 | 15.6x | +1.2x | **+4.9x** |
| small | 43 | 15.0x | +2.0x | **+8.6x** |

## THE ATTRITION IS ARM-DIFFERENTIAL — AND IT RUNS AGAINST THE FINDING

**13 of 138 names carry no usable multiple: 10 ratified, 3 passed.** Under equal attrition a 10/3
split has one-sided p ≈ 0.046 — suggestive at n=13, not conclusive.

**But the direction is conservative.** Forward P/E requires positive forward EPS, so the drops are
loss-making and recently-listed names — **BBAI, CRWV, CTEV, INTA, KC, NBIS, NTSK, RUM, RXT, SHAZ**
on the ratified side against **NXDR, SOUN, WIT** on the passed side. Those are the *speculative* end
of the ratified cohort, which if priced at all would price **expensive**. Removing them strips the
high tail from the ratified arm, so **the measured +29.76 is more likely an understatement than an
overstatement.** The bias works against the result rather than manufacturing it.

**56 surviving pairs, not the ~44 projected from Pane 1** — Set 1 was the worst pane.

## THE OUTPUT: seven names where the verdict disagrees with the market

Ratified names in the **cheap quartile of their own stratum** — all shown, 7 of 59 measured:

| ticker | stratum | fwd P/E | rank |
|---|---|---:|---:|
| **OTEX** | mid | 6.2 | **2%** |
| **CLVT** | small | 3.1 | **5%** |
| **BLKB** | mid | 8.4 | 9% |
| TDC | mid | 10.4 | 18% |
| TRU | large | 16.2 | 21% |
| DV | mid | 12.3 | 21% |
| YEXT | small | 9.1 | 24% |

*For contrast, ten ratified names sit above the 90th percentile — NET at 198.0x (100%), VRNS 198.6x,
FIG 96.6x, XMTR 93.8x. The basket's ratified mass is expensive; these seven are the residual.*

## The spike rate is 9x the carried expectation — a finding about the BASKET, not the detector

**2,612 spikes (1,893 inverted, 72%) in 176,855 cells = 1.477%**, against the expectation carried
before the pull of **~560 at 0.163% with ~31% inverted**.

**The inverted share is the tell.** A forward P/E is price over forward EPS; as EPS approaches zero
the ratio explodes **upward**, so a small estimate revision on a barely-profitable name produces an
up-then-down spike. The WST peers were profitable large-cap instrument makers at 31% inverted; this
basket is small-cap software near break-even at 72%. **That is a property of the population, and it
is exactly why the measure is a MEDIAN over a window rather than a close** — the window sweep above
shows the result is unmoved by it.

## THE EARNINGS-BASE CONFOUND — raised 2026-09-14, tested on data in hand, NOT YET SETTLED

**The objection.** Forward P/E diverges as EPS approaches zero. **Matching was on market cap within
SIC 73 and nothing matched on PROFITABILITY.** If ratified names sit systematically closer to
break-even than their matched peers — plausible, since they were ratified for growth-adjacent moats
while passed names skew mature — then **+29.76 is an earnings-base artifact, not a valuation
premium.** The spike evidence in this record is the objection's own support: **72% inverted at
1.477%** is the signature of a near-zero denominator.

**The premise is partly confirmed.** Ratified names DO carry higher multiples and sit nearer the
explosive region:

| multiple band | ratified | passed |
|---|---:|---:|
| <20x | 29 | **50** |
| 20–35x | **15** | 8 |
| 35–60x | **9** | 5 |
| >60x | **6** | 3 |

Median **20.3x ratified against 14.5x passed**; share above 60x **10% against 5%**.

**The confound's strongest prediction is not met — but this is WEAKER than the 'prediction fails' an earlier draft of this record claimed.** If the gap lived in the near-zero-EPS region it would
collapse once names with comfortably positive earnings are the only ones left. **It does not:**

| keep pairs where BOTH < | n | median gap | 95% CI |
|---|---:|---:|---|
| no trim | 56 | +29.8 | [+12.2, +33.3] |
| 100x | 52 | **+31.5** | [+14.2, +35.4] |
| 60x | 47 | **+32.1** | [+16.1, +36.9] |
| 40x | 40 | **+30.4** | [+15.4, +36.4] |
| 30x | 34 | +23.2 | [+11.7, +33.4] |

**The CI's lower bound stays above the +10 threshold at every trim**, and trimming at 100x — which
removes NET (198.0x), VRNS (198.6x) and PRCH (232.0x) — **raises** the gap. **NET is not the
exhibit it appears to be: deleting it makes the finding stronger.**

**This is a DIAGNOSTIC, NOT A REPLACEMENT ESTIMATE.** Trimming on the outcome variable is selection,
and a name at 25x can still carry a depressed earnings base relative to its pair. **The confound is
weakened, not eliminated — EV/Sales remains the deciding test**, on the same pairs, strata, window
and registered method, where the denominator cannot approach zero. **Operator ruling 2026-09-14: the
EV/Sales replication runs before the seven-name screen and before any leg-closing decision.**

### CORRECTION to the trim reading, and it matters

**"The prediction fails" overstated it.** The series runs **+29.8 → +31.5 → +32.1 → +30.4 →
+23.2** — flat-to-rising through the 40x trim, then a **22% drop at 30x**. **A pure confound
predicts monotone collapse; pure valuation predicts flat. This is neither** — it is consistent with
the earnings base contributing a **MINORITY SHARE**, not with its absence.

**And the trim cannot reach the real mechanism.** The confound is not explosive multiples, it is
**MARGIN DIFFERENCE, which persists at every level of the distribution**: a 5%-margin name and a
25%-margin name differ **5x on P/E at identical EV/Sales**, and neither need be above 40x. **The
telling number is the one inside the trimmed range** — ratified median **20.3x** against passed
**14.5x**.

### THE NEGATIVE PAIRS ARE MANUFACTURED BY THE PASSED SIDE — the same defect, reversed

| group | n | median ratified | median passed |
|---|---:|---:|---:|
| all pairs | 56 | 20.3x | 14.5x |
| **negative pairs** | 12 | 13.1x | **30.4x** |
| positive pairs | 44 | 22.6x | 12.9x |

**Passed names above 40x: 42% of negative pairs against 2% of positive — a 21x enrichment.** Five of
the twelve negatives are that shape: **CLVT 3.1x vs CCO 71.4x** (Clear Channel Outdoor — a 71.4x
forward P/E on an outdoor advertising company is a near-zero earnings base, not a rich valuation),
DV vs PRCH 232.0x, CRNC vs FVRR 42.0x, CASS vs CEVA 40.3x, GTLB vs NAVN 108.7x.

**So the seven-name residual is produced by the SAME metric defect as the headline, running the
other way.** The overlap between the residual and the negative tail was already recorded; this makes
**both suspect for one reason**, which is a stronger argument against screening the seven than the
overlap alone. **A conclusion this test CAN deliver is "the ratified class is more expensive." A
conclusion it CANNOT deliver is "these seven are mispriced."**

## THE EV/SALES REPLICATION — DECISION RULE, REGISTERED BEFORE THE PULL

Registering this after seeing +29.8 would be the degree of freedom the threshold discipline exists
to close. **Same 138 names, same 13 panes, same strata, same window to 2026-09-11, same
within-stratum rank, same ±10 threshold, same three-state CI logic.**

| outcome | rule | reading |
|---|---|---|
| **CONFIRMS** | CI lower bound **> +10** | valuation, not the earnings base. The P/E finding stands, strengthened |
| **COLLAPSES** | CI fits inside **±10** | a real null — **+29.76 was the earnings base and the conclusion inverts** |
| **MIXED** | CI lower **> +10** AND CI upper **< +29.76** | both present; the base's share is approximately `(29.76 − gap) / 29.76` |
| **CANNOT TELL** | CI spans **+10** | underpowered, **not** a null; report and stop |

**THE GROWTH CONDITION, registered with it.** EV/Sales carries its own confound: **high-growth names
carry higher sales multiples legitimately.** If ratified names are higher-growth, an EV/Sales gap is
a **growth premium, not a durability premium**. So **revenue must be pulled as a series alongside**,
which yields growth from the same export at no extra pane cost. **Registered split: pairs where the
ratified name's trailing 3-year revenue CAGR EXCEEDS its pair's, versus those where it does not.**
If the gap clears +10 only in the faster-growing half, **the finding is a growth premium** and the
durability reading is not available.

**AVAILABILITY MUST BE CHECKED BEFORE A SESSION IS SPENT.** EV/Sales may not sit among the chart
builder's quick metrics. **TEV/EBITDA is NOT a substitute** — EBITDA approaches zero on the same
names and reproduces the defect. If the fallback is **Market Cap + Revenue as two series**, note
what changes: that yields **P/Sales, not EV/Sales**, and **P/Sales is confounded by leverage in the
direction that FLATTERS the finding** — mature passed names carry more debt, so their EV exceeds
market cap by more, P/Sales understates them, and the measured gap **inflates**. Under the fallback
either net debt is pulled too, or **a confirming result is an UPPER BOUND and must be recorded as
one**.

## THE PAIRED-DIFFERENCE DISTRIBUTION, which the CI hides

| percentile | 0 | 10 | 25 | 50 | 75 | 90 | 100 |
|---|---:|---:|---:|---:|---:|---:|---:|
| gap | **−95.2** | −28.6 | +7.1 | **+31.0** | +51.8 | +70.8 | +80.4 |

**Heavy left tail: 12 negative pairs carrying −460 of rank mass against +1,733 positive.** All
twelve, shown in full:

| ratified | | passed | | stratum | gap |
|---|---:|---|---:|---|---:|
| CLVT | 3.1x | CCO | 71.4x | small | **−95.2** |
| DV | 12.3x | PRCH | 232.0x | mid | −78.6 |
| BLKB | 8.4x | ASAN | 24.3x | mid | −66.1 |
| CRNC | 11.2x | FVRR | 42.0x | small | −57.1 |
| OTEX | 6.2x | TTD | 15.1x | mid | −44.6 |
| NCNO | 15.7x | PAYO | 29.8x | mid | −32.1 |
| CASS | 16.8x | CEVA | 40.3x | small | −28.6 |
| ALRM | 19.4x | APPN | 31.0x | mid | −25.0 |
| WIX | 13.9x | NIQ | 15.1x | mid | −12.5 |
| FA | 15.3x | FRSH | 16.8x | mid | −8.9 |
| YEXT | 9.1x | NRDS | 10.2x | small | −7.1 |
| GTLB | 52.8x | NAVN | 108.7x | mid | −3.6 |

**The seven-name residual IS this left tail** — CLVT, DV, BLKB, OTEX, YEXT appear here by
construction. **So the "disagreement" set and the negative pairs are the same object seen twice**,
which is coherent but means the seven are not independent corroboration of the headline.

## TWO RECORDED LIMITS

**N AND THE THRESHOLD ARE NO LONGER MATCHED.** N=69 was chosen because it detects **10.1** rank
points at 80% power, against a threshold registered at 10. **Attrition to 56 pairs moves that to
11.2 points — above the registered threshold.** Immaterial against an observed gap of ~30, but the
matching was deliberate and is now broken; recorded rather than left to be rediscovered.

**SCOPE: the finding speaks only to ratified names with POSITIVE FORWARD EPS — 59 of 69.** The ten
without one are not a sampling gap but a population the metric cannot address at all.


**BOUNDARY.** Source: operator's 13 Charting exports, `AI-revalue-theme/NTM PE 5Y/`, pulled
2026-09-14, read the same day. **138 series — every manifest name present, none missing, none
extra.** Metric **Forward P/E** on all 138; window 2021-09-13/14 → **2026-09-11** after truncating
Set 13, which ended 2026-09-14. Measure: **median over 2026-08-14 → 2026-09-11**, date-anchored
rather than row-anchored because **Set 5 carries 212 Sunday rows** (it holds NICE, WIX, MBGL, NTSK
and Tel Aviv trades Sun–Thu), so a "last 20 rows" window would have spanned a different calendar
there. Strata are the manifest's size bands within SIC 73. Ranks pool both arms within a stratum.
Spike counts from `find_spikes` at its 8%/5% defaults, on sentinel-cleaned series. No raw CIQ
committed.

**WHAT IT COSTS / WHAT IS ACCEPTED — checked, not asserted.** **The registered measure changed from
"last 20 sessions" to a 28-day calendar window**, forced by a grid property I could not know in
advance (the Israeli Sunday rows). The intent — a median rather than a close — is unchanged, the
threshold and N are untouched, and **the window sweep shows the result is insensitive to the choice**.
Stated rather than silently substituted. **The 10/3 attrition split is suggestive, not established**
at n=13; what is established is its direction. **This tests the SOFTWARE ratifies** — SIC 73 — and
cannot speak to the 50 ratified names outside it (SIC 36 electronics, 61 credit institutions, 35
machinery, 80 health services, 87 research, 38 instruments). **Falsifier: the same test on the
non-73 cohort returning no gap**, which would make "already priced" a software-sector property
rather than a property of the verdicts.
