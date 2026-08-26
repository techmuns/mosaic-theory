---
id: S12
status: falsified
date: 2026-08-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S12. THE SPOT DIVERGENCE IS ZERO — measured 2026-08-01, three routes x seven names. NULL RESULT,
RECORDED SO IT IS NOT RE-LITIGATED.**

The seven `spot_source` strings name three fetch routes, so the seven spots were not known to be
comparable. Each name fetched on ITS OWN spot date by all three:

| name | date | committed | `daily_bars` | `grouped_daily` | store |
|---|---|---|---|---|---|
| AORT | 2026-07-20 | 25.37 | 25.37 | 25.37 | 25.37 |
| EPAM | 2026-07-20 | 89.40 | 89.40 | 89.40 | 89.40 |
| IT | 2026-07-17 | 140.19 | 140.19 | 140.19 | 140.19 |
| MVST | 2026-07-21 | 0.9188 | 0.9188 | 0.9188 | 0.9188 |
| NCNO | 2026-07-20 | 17.93 | 17.93 | 17.93 | 17.93 |
| SMPL | 2026-07-22 | 10.53 | 10.53 | 10.53 | 10.53 |
| WERN | 2026-07-17 | 46.04 | 46.04 | 46.04 | 46.04 |

**Every difference is exactly 0.00**, so every reward:risk is unchanged under every route and **no
name crosses the 2:1 bar under any route** — no route moves any spot at all.

**THE INSTRUMENT WAS VERIFIED ABLE TO MOVE** before the null was accepted (the standing rule: a
check finding nothing in a large corpus is suspicious, not reassuring). `grouped_daily` returned
**12,388 symbols** — a whole-market snapshot — against `daily_bars`' single bar, so they are
genuinely different endpoints; and across adjacent trading days AORT reads **25.06 / 25.37 / 24.94**
on all three routes. A divergence would have shown.

**STRUCTURAL FINDING — THERE ARE TWO INDEPENDENT SOURCES, NOT THREE.** Every store row's `source`
column reads **`polygon-grouped`** on all seven names: the store is a CACHED COPY of the grouped
route, not a third opinion. The real comparison is per-symbol aggregates vs grouped daily, and those
agree exactly. **Consequence for the canonical-route decision (still the operator's):** choosing
"the store" is choosing grouped-daily with a staleness risk attached, not choosing a distinct
source.

**SENSITIVITY — how much divergence it would have taken to matter.** The concern was that a small
denominator move is not automatically immaterial. Measured, spot that would put each name AT its
2:1 bar:

| name | ratio | spot at bar | move needed |
|---|---|---|---|
| **IT** | **1.52** | 130.72 | **-6.76%** (-$9.47) |
| EPAM | 6.34 | 111.62 | +24.86% |
| SMPL | 4.78 | 13.47 | +27.88% |
| WERN | -0.35 | 22.96 | -50.12% |
| NCNO | -0.72 | 5.50 | -69.30% |
| AORT | -0.67 | 5.51 | -78.29% |
| MVST | -0.33 | 0.17 | -81.79% |

**IT was the right name to worry about** — the only one where a realistic divergence could have
flipped the verdict, with a whole tolerance of $9.47. Every other name needs a 25%+ move. Observed
divergence: $0.00. The concern is closed on evidence, not on assumption. **Measure-only: no fetch
path was changed and no spot was rewritten.**
