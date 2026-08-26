---
id: S5
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S5. G2'S START ANCHOR IS BOUNDED — built 2026-07-31, piece three step one.** `_bar_on_or_before`
reached back with NO limit, so a hole in a series silently widened the window: **OPI's start price
came from 2025-10-06 at $0.20**, 116 days before the window start and on the far side of an
eight-month gap, and the gate computed `17.45/0.20 − 1 = +8,625%` over **296 days against a 180-day
threshold**. A longer window means a larger |rel|, which makes the −15% bar EASIER — the failure
mode ADMITS names, and with the legs reversed it puts one in the pool cohort selection draws from.
**THE POPULATION SEPARATES CLEANLY:** of the 596 that reached G2, **593 anchor exactly ON the
window start**; the next three sit at 108d, 116d and 1,472d, with nothing in 1–107. Any bound in
that range gives identical outcomes today, so `MAX_ANCHOR_LAG_DAYS = 10` is derived from the
MARKET CALENDAR — **corrected at review**: the first derivation used the STORE-wide distribution,
whose 5–9d tail is per-name HALTS, i.e. the very population the bound refuses, so it set the
threshold from what it screens out. IWM and MDY agree exactly (which is what makes them the
calendar) and neither gap exceeds **4d**; the bound of 10 leaves six days of margin over the worst
holiday weekend the market actually produces, and is pinned from both sides so it can neither
refuse a normal weekend nor admit a multi-week halt. Out of range → **NOT_EVALUATED with its reason,
never FAIL**. **THE STAMP NOW SAYS WHAT THE NUMBER COVERS:** `StampedInput` carries structured
`span_days` + `observations`, and refuses one without the other — 296 days is innocuous at 124 bars
and a hole at 28, so either alone cannot say which.
**CONTAMINATION MEASURED, NOT CLEARED (operator):** of the 281 names that passed all three gates on
the 2026-07-29 run, **2 have an out-of-range anchor** — **ARIS** (108d back, 288d span, rel −0.525)
and **MRLN** (1,472d back, **1,652d span**, 94 bars, rel −0.970). Both PASSED G2 on a window between
1.6× and 9× the calibrated one. They stay in the committed run; the next screen refuses them. OPI is
the third out-of-range name and it FAILED, which is why the defect surfaced as an impossible +8,625%
rather than as a false admission.
**FIXTURE NOTE:** the #280 pins dated their first bar 2026-05-01 against a 2026-05-18 window start —
an 81-day hole incidental to what they test. Re-anchored ON the start; every asserted number is
unchanged because the anchor price was already 100.
