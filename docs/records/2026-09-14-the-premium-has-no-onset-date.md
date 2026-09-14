---
id:
status: recorded
date: 2026-09-14
prs: []
supersedes:
superseded-by:
---

# The premium has no onset date — half of it predates the driver, and the rest arrived as a trend

**WHAT.** The decomposition registered at `929009f` **before it was run** returns **NEITHER** of the
two hypotheses, on both the full and the balanced panel. **The cross-section stands and the
attribution fails.** The ratified class is more expensive — **and open-weight convergence is not
shown to be why.**

## The path, not the net

Quarterly rank gap, same 67 pairs, same strata, ranks recomputed per quarter from that quarter's
live population:

| | gap | | | gap | | | gap |
|---|---:|---|---|---:|---|---|---:|
| 2021Q4 | **+11.4** | | 2023Q2 | +19.9 | | 2025Q1 | +22.9 |
| 2022Q1 | +13.0 | | 2023Q3 | +19.4 | | 2025Q2 | +22.7 |
| 2022Q2 | +15.8 | | 2023Q4 | +16.7 | | 2025Q3 | +26.7 |
| 2022Q3 | +17.0 | | 2024Q1 | +18.1 | | 2025Q4 | +26.4 |
| 2022Q4 | +18.8 | | 2024Q2 | +20.1 | | 2026Q1 | +28.8 |
| 2023Q1 | +18.2 | | 2024Q3 | +23.3 | | 2026Q2 | +28.5 |
| | | | 2024Q4 | +22.8 | | **2026Q3** | **+29.9** |

*(means; per-quarter CI ≈ ±10–11 as registered, so adjacent quarters are not separable — which is
why the readings were defined on period means)*

| | E · 2021Q4–2022Q4 | L · 2025Q3–2026Q3 | L − E |
|---|---:|---:|---:|
| all pairs | **+15.20** | **+28.07** | +12.87 |
| **balanced panel** (53 pairs live in every quarter of both) | **+16.40** | **+31.03** | **+14.63** |

## THE REGISTERED READING: NEITHER — and both hypotheses fail for opposite reasons

| reading | rule | observed | |
|---|---|---|---|
| STANDING PREMIUM | E ≥ +20 **and** \|L−E\| < 10 | E = **+16.4**, \|L−E\| = **14.6** | **fails both** |
| DRIVER RE-RATING | E < +10 **and** L−E ≥ +15 | E = **+16.4**, L−E = **+14.6** | **fails both** |
| SINGLE-QUARTER STEP | ≥60% of L−E in one quarter | largest move **+4.0 = 31%** | **fails** |

**Both hypotheses are wrong in the same direction: the premium was ALREADY SUBSTANTIAL before the
driver was visible, AND it has genuinely widened since.** Roughly **half of today's gap
(16.4 of 31.0, 53%) predates the driver window entirely.**

**The widening is real and is NOT a composition shift** — the registered follow-up strengthens it
rather than dissolving it: **+12.87 → +14.63** on the 53 pairs live in every quarter of both
periods, where the naive worry was that later-listing names were doing the work.

## WHY THIS BREAKS THE ATTRIBUTION, EVEN THOUGH THE WIDENING IS REAL

**The widening is smooth and continuous from 2021Q4, with no onset.** It was already climbing
through 2022 and 2023 — **before open-weight convergence was visible** — and the largest
quarter-to-quarter move in five years is **+4.0 points, well inside the ±10 noise band.** There is
no step, no reversal, and **no date.**

**The operator's registered caution is what this lands on:** markets price anticipations, so *"the
driver is recent"* does not imply *"unpriced"* — **but it does imply the premium should have a DATE.
It does not have one.** A gap that was +11 in 2021, +19 in 2023 and +30 in 2026, rising steadily
throughout, is a **trend** the card can decorate but cannot claim.

**NO BREAKPOINT SEARCH WAS RUN.** A regression with a break at 2023 or 2024 would very likely find
one, and finding one **after seeing the path** is precisely the degree of freedom the
pre-registration exists to close. **Not run, deliberately, and recorded as not run.**

## WHAT THIS DOES TO THE AI LEG — it does not close as previously stated

The prior record closed the leg as *"the sheet identified durability correctly and the market has
already paid for it."* **That is still true and it is now incomplete.** The corrected statement:

> **The discriminator works. The market pays for it. The card's mechanism is not shown to be the
> reason** — half the premium predates open-weight convergence, and the half that arrived did so as
> a five-year trend without an onset.

**This is a stronger result against the card than the cross-section was**, because it removes the
one reading under which "already priced" would still have vindicated the thesis: that the market had
repriced *on the driver* and merely got there first. **It did not get there on the driver.**

**BOUNDARY.** Population: the 67 matched pairs surviving the TEV replication (69 less WIT-unusable,
less FVRR-corrupted); balanced panel is the 53 live in **every** quarter of both periods. Source: the
13 `TEV/Forward Total Revenue` exports pulled 2026-09-14, 138 series, 2021-09-14 → 2026-09-11,
sentinel-cleaned. A quarter's value per name is the median of its clean observations in that quarter,
with a **≥20-observation** floor; ranks recomputed **per quarter** within stratum from that quarter's
live population, so a name absent in a quarter leaves both the pair and the pool for it. 20 quarters,
2021Q4 → 2026Q3. Per-quarter CI from that quarter's own SD. No new pull; no data outside the exports
already read.

**WHAT IT COSTS / WHAT IS ACCEPTED.** **`NEITHER` is a real outcome here, not a failure to measure** —
both hypotheses are excluded by the data rather than by width, since E is too high for re-rating and
L−E too large for a standing premium, and the balanced panel moves both the same way. **What is NOT
established is the shape of the widening**: a smooth trend and a series of small steps are
indistinguishable at ±10 per quarter, and **no test that could separate them was registered**.
**Falsifier for the no-onset reading: a pre-registered breakpoint test on a HELD-OUT population** —
the 50 ratified names outside SIC 73, or the non-SIC-73 cohort — which would put the question to
data this analysis has not touched.
## Amendments
**2026-09-14 (same day) — the DECELERATION claim does not survive, and the closing statement is
narrowed on the operator's ruling.**

### 1. "The rate halves across the driver" is an artifact of where the split is placed

Proposed for the closing statement: the widening runs **+1.42/quarter** before 2023Q2 and
**+0.77/quarter** after, so the trend was **fastest before the driver existed**. **Both endpoint
figures reproduce exactly**, and OLS gives a milder **+1.39 → +0.94**.

**But the split point was chosen after seeing the path — the same degree of freedom that led this
record to decline a breakpoint search — so it was swept:**

| split | pre OLS | post OLS | post slower? |
|---|---:|---:|---|
| 2022Q4 | +1.88 | +0.83 | yes |
| 2023Q1 | +1.50 | +0.89 | yes |
| **2023Q2** | **+1.39** | **+0.94** | **yes** |
| 2023Q3 | +1.18 | +1.05 | yes |
| 2023Q4 | +0.83 | **+1.14** | **NO** |
| 2024Q1 | +0.68 | **+1.09** | **NO** |
| 2024Q2–2025Q3 | +0.66…+0.76 | **+0.98…+1.25** | **NO ×8** |

**Slower in 4 of 12 split points, faster in 8.** The mechanism is visible in the path: the series
climbs steeply through 2022 (+11.4 → +18.8), **plateaus across 2023** (+18.2, +19.9, +19.4, **+16.7**),
then resumes. An early split puts the steep climb in `pre`; a later split averages the plateau into
`pre` and the answer flips.

**So neither acceleration nor deceleration is established.** What survives is what the registered
analysis already found: **a roughly linear climb, whole-period OLS +0.84/quarter, from a base already
at +11.4, with no onset and no step.** **The card's mechanism should have produced an ACCELERATION
and none is visible — that is the honest damaging statement, and it is weaker than "the rate
halves."**

*Recorded because the number was reaching a closing statement as the most damaging figure available.
It is not available.*

### 2. The closing statement, narrowed on the operator's ruling

*"The discriminator works"* claims more than the test establishes. What is shown is that ratified
names trade richer than matched passed names, **persistently, since before the driver existed** —
consistent with identifying durability **and** with identifying something else the market pays for.
**The growth condition was never run, and a five-year persistent gap with no onset is precisely what
a growth premium looks like.** Replacing it:

> **The discriminator selects names the market prices richly, and has done so since before the
> driver existed. Whether it selects for DURABILITY specifically is UNTESTED** — the growth
> alternative was registered, never run, and is now the leading one. **The card's mechanism is not
> shown to be the reason for any of it.**

### 3. The held-out breakpoint test: NO, and the reason is instrumental

The non-SIC-73 cohort is **not held-out data — it is data the instrument cannot read.** It carries
**35 pairs across 25 cells at one or two each**, and a within-stratum rank in a stratum of two is a
sign, not a rank. **A breakpoint test needs MORE power than a level comparison, not less.** Running
it would mean abandoning the matched instrument for a pooled comparison, **which reintroduces the
size confound in the confirming direction** — the exact bias the matching exists to remove.

### 4. THE METHODOLOGY FINDING — worth more than the card

**The discriminator selects persistently expensive names, five years running, independent of the
driver it was built for.** The gap was +11.4 in 2021Q4, before `ai-value-migration` existed as a
thesis, and has never been near zero in twenty quarters.

**This is a property of the METHOD, not a result about AI. Any future thesis using the same screen
will select expensive names for the same reason** — the screen keys on qualities (regulatory depth,
proprietary workflow data, systems of record) that the market prices continuously, not on a
mispricing. **That is why the step-8 price check is the load-bearing change from this workstream and
the AI result is the occasion for it.**
