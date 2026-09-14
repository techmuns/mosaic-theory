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
