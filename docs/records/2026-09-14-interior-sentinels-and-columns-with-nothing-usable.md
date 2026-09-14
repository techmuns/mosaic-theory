---
id:
status: recorded
date: 2026-09-14
prs: []
supersedes:
superseded-by:
---

# The first real pane broke the sentinel detector twice, and the banner read clean both times

**WHAT.** Set 1 of the discriminator pull arrived 2026-09-14. **The format is correct and the data
is not.** Two of eleven series carry no usable multiple, **neither was flagged**, and the coverage
banner printed *"DROPPED 637 sentinel cells"* — naming one series and staying silent on two.
`_sentinel_run` now catches placeholder runs **at any position**, and a column with nothing usable
is **named rather than passed over**.

## What Set 1 actually is

**Format: correct.** Parses first try — sheet `Pane 1`, header row 35 labelled `Dates`, **11 series,
Forward P/E on every column, daily, 1,255 sessions, 2021-09-13 → 2026-09-11.** Names match the
manifest's Pane 1 exactly. The operator pulled **5 years against the 3 requested**, which is
strictly better for reading coverage.

**`find_spikes` behaved as predicted**: **21 spikes, 6 inverted, in 13,805 cells** — 0.152% against
the WST export's 0.163%, and 29% inverted against 31%. **A V-only test would have missed 6.**

## FAILURE 1 — the interior run, which was predicted

**NBIS (Nebius, formerly Yandex N.V.) carries 665 cells of `42.0` from 2022-02-28 to 2024-10-18** —
the trading suspension — **beginning at index 116.**

`_leading_sentinel` walked from index 0 and stopped at the first differing cell, so **it could only
ever see a LEADING run.** NBIS's first cell is a real 78.06, so the walk stopped at n=1 and the
column was passed through with 665 placeholder cells intact. **Its last real value is 2024-10-18 —
23 months stale.**

## FAILURE 2 — placeholder-then-nothing, which was NOT predicted

**CRWV carries 905 cells of `42.0` from 2021-09-13 to 2025-04-21, followed by 350 nulls and nothing
else.** CoreWeave listed in March 2025 and is loss-making: **no positive forward EPS, so no forward
P/E exists to pull.**

**The detector's third guard fired correctly and that is exactly the problem.** `not rest` — there is
no varying data after the run to contrast against — so it declined to call it a sentinel, **and said
nothing.** A column that is **100% unusable reported as clean.** *Same family as the truncation
lesson: a clean banner is a statement about the DETECTOR, not the data.*

## The fix

**`_sentinel_run` replaces `_leading_sentinel`** (kept as a shim) and scans **every maximal constant
run at any position**. The discriminating condition is unchanged and is the second one — **a
placeholder occurs nowhere else in the column, while a genuinely repeated price recurs.** Length
only gates when the question is worth asking:

| position | floor | why |
|---|---|---|
| leading | **n ≥ 2** | position is already evidence; unchanged |
| interior | **n ≥ 5** (`_MIN_INTERIOR_RUN`) | an interior repeat of two sessions is ordinary. Five is a face-validity floor — a forward P/E is price over estimates and **both** move, so a week of byte-identical values whose number occurs nowhere else is not a market. **Never tuned on an outcome.** |

**`ChartingSeries` gains two fields**, because the old shape could not express either failure:
`interior` names the run's **span** (for an interior run *"first real date"* is misleading — there is
real data before it too), and **`unusable` names any column with no data to rank**, which
`report()` now prints as `NO USABLE DATA`.

## HOW VERIFIED — corpus first, then mutation

**On the real Set-1 pane:**

```
DROPPED 1302 sentinel cells — Nebius … =42 x665 [INTERIOR 2022-02-28..2024-10-18],
Reddit … =42 x637 (first real 2024-10-30);
NO USABLE DATA — CoreWeave …: flat at 42 for its whole span — no variation to rank
```

**RDDT is unchanged at 637 cells** — no regression on the case that already worked.

*One existing reported value improves: RDDT's "first real" now reads **2024-10-30** against the old
**2024-03-26**. The old code returned `dates[n]` — the date after the run **whether or not it
carried data** — and RDDT has no forward P/E until October 2024 despite listing in March. The new
value is the first date that actually carries data.*

**Mutation-tested twice, on different pins.** Reverting the detector to leading-only reddens
`test_an_interior_sentinel_run_is_caught_and_its_span_named` and nothing else; stubbing the
usable-data check reddens `test_a_genuine_repeat_whose_value_recurs_is_never_flagged`. **Two
mutations, two distinct pins** — the additions are independently guarded.

**Suite: `ruff` + `mypy --strict` (153 files) clean, 3,686 passed / 147 skipped offline.**

## WHAT THIS DOES TO THE TEST, and it is not small

**Both unusable names are RATIFIED, and each takes its matched pair down with it:** NBIS⇄ADSK and
CRWV⇄TEAM are lost. **Set 1 yields 3 usable pairs of 5** — NET⇄MELI, XYZ⇄WDAY, MDB⇄TWLO.

**If 2-of-11 attrition is typical, N falls from 69 to roughly 44**, which is ~62% power at SD=30 for
the pre-registered 10-point gap — **below the level N=69 was chosen to guarantee.**

**And the attrition is unlikely to be random.** Forward P/E requires positive forward EPS, so it
drops **loss-making and recently-listed** names, which in an AI basket skew **ratified**. In this
pane: **2 of 6 ratified unusable, 0 of 5 passed.** One pane is not evidence — but if it holds, the
surviving ratified sample shifts toward mature profitable names, **the already-priced end, which
would manufacture the result the test exists to check.**

**BOUNDARY.** Source: operator's `Set1_Charting Excel Export - Sep 14th 2026 3_40_03 pm.xls`, sheet
`Pane 1`, read 2026-09-14 — **1,255 dates × 11 series = 13,805 cells**, header row 35, metric Forward
P/E, window 2021-09-13 → **2026-09-11** (Friday close). Spike counts from `find_spikes` at its
default 8%/5% thresholds. Attrition counts are **this pane only, n=11 series** — the arm-differential
reading is a hypothesis on 2 of 6 versus 0 of 5, not a measurement. Twelve panes outstanding. No raw
CIQ committed.

**WHAT IT COSTS / WHAT IS ACCEPTED — checked before claimed.** **`_MIN_INTERIOR_RUN = 5` is a
judgement and the only free parameter added.** The cheap alternative was considered and rejected:
keying purely on *"the value occurs nowhere else"* with no length floor would flag an isolated
two-session repeat of an unusual number, which is ordinary in a thin series. **Falsifier: a real
series caught by the interior rule** — at which point the floor rises and the case is recorded.
**Second accepted item: nulls END a run rather than bridging it**, so a placeholder block split by a
missing session reads as two shorter runs and could fall under the floor. Not observed in Set 1 —
NBIS's 665 cells are contiguous — and stated rather than guarded, because bridging would merge two
genuinely unrelated blocks whenever the gap is real.
