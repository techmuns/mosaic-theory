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
