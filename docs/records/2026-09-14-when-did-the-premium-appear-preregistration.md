---
id:
status: recorded
date: 2026-09-14
prs: []
supersedes:
superseded-by:
---

# When did the premium appear? — PRE-REGISTRATION, written before the decomposition is run

**WHAT.** The replication tested a **LEVEL**: matched pairs ranked on one recent window. It
establishes that the ratified class trades richer than matched passed names **today**. **It cannot
say WHEN that premium appeared, or whether open-weight convergence put it there.**

**That gap is decisive for the card**, whose mechanism is recent. **If the rank gap was already ~+30
in 2022, the premium predates the driver and the card explains none of it** — it is a standing
quality premium. If it opened through 2024–26, the market has been repricing on the driver.

**The data is already in hand** — 1,254 dates, 2021-09-14 → 2026-09-11 — and **only the last window
has been read.** No new pull. **This record is committed BEFORE the decomposition runs**, because we
now know which answer we want.

## Method, fixed in advance

Identical to the replication in every respect except the window: **same 67 pairs, same SIC-73 size
strata, same within-stratum percentile rank, same sentinel-cleaned series, FVRR excluded.** The
measure becomes **one rank gap per calendar quarter**, each from that quarter's median
`TEV/Forward Total Revenue` per name.

**Ranks are recomputed per quarter from that quarter's live population.** A name not yet listed, or
carrying no usable value in a quarter, **leaves both the pair AND the rank pool for that quarter** —
the two-operations rule, applied rather than restated. **n is reported per quarter**, and early
quarters will carry fewer pairs than late ones by construction.

**Report the PATH, never the net.** *A net says where a series ended and never what it has been
doing* — already on the books, and the reason this decomposition exists.

## THE REGISTERED READINGS

Let **E** = mean quarterly gap over **2021Q4–2022Q4** (before open-weight convergence was visible)
and **L** = mean over **2025Q3–2026Q3** (the most recent year).

| reading | rule | what it means |
|---|---|---|
| **STANDING PREMIUM** | **E ≥ +20** and **\|L − E\| < 10** | the premium predates the driver; **the card explains none of it** |
| **DRIVER RE-RATING** | **E < +10** and **L − E ≥ +15**, with the middle period lying between | the market has repriced on the driver; the finding means what the replication said |
| **SINGLE-QUARTER STEP** | **≥60% of (L − E) lands in ONE quarter** | an **event**, not a re-rating — **the WST shape**, named rather than smoothed |
| **NEITHER** | anything else — no trend, or a rise that reverses | the cross-section stands and the timing is unresolved |

**Precision, stated in advance:** at n≈67 and the observed SD 36.04 a quarterly gap carries
**SE ≈ 4.4, CI ≈ ±8.6**. **So a single quarter's gap is not separable from its neighbour at ±10** —
**the readings above are deliberately defined on PERIOD MEANS, not on single quarters**, and any
quarter-to-quarter move inside ±8.6 is noise. Early quarters with fewer pairs are wider still.

## CARRY THE WST PRECEDENT EXPLICITLY

**WST's premium looked like a driver re-rating until the window was decomposed**, and turned out to
be **standing quality with the move sitting in a single quarter** — 21m→18m at **−18.2%** against a
~flat 18-month net. **Same instrument, same shape, opposite conclusion available.** That is why
`SINGLE-QUARTER STEP` is a registered reading rather than a footnote.

## ONE INTERPRETATION CAUTION, REGISTERED WITH THE RULES

**Markets price anticipations.** Open-weight convergence has been visible since 2023 and the
app-layer repricing this year was explicitly about it. **So "the driver is recent" does not imply
"unpriced"** — a premium can have opened in 2023 on anticipation and be fully priced by 2026.

**But it does imply the premium should have a DATE. If it does not — if E is already ~+30 — the
durability reading is weaker than the cross-section suggested**, because a premium with no onset is
not evidence of a mechanism that began recently.

**BOUNDARY.** Population: the 67 matched pairs surviving the TEV replication (69 less WIT-unusable,
less FVRR-corrupted), SIC 73, size strata as frozen 2026-09-01. Source: the 13
`TEV/Forward Total Revenue` exports pulled 2026-09-14, 138 series, 2021-09-14 → 2026-09-11.
Quarters are calendar quarters; a quarter's value per name is the median of its clean observations in
that quarter. Precision figures use SD 36.04 from the replication. **Nothing has been computed on
the pre-2026-08-14 window at the time of writing.**

**WHAT IT COSTS / WHAT IS ACCEPTED.** **The early quarters are thin by construction** — many ratified
names listed after 2021, so E rests on a smaller and differently-composed sample than L, and a
composition shift between the two periods is an alternative explanation the design cannot exclude.
**Falsifier for the whole decomposition: a period difference that disappears when restricted to
pairs live in BOTH periods** — which is the first thing to check if a re-rating reading emerges, and
is registered here as a required follow-up rather than an option.
