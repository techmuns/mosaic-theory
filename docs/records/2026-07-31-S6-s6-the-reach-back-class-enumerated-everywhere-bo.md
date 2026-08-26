---
id: S6
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S6. THE REACH-BACK CLASS — ENUMERATED EVERYWHERE, BOUNDED AT G1 (2026-07-31).** Invariant: *no
gate decides on a value reached back beyond the window it claims.* Four sites, derived from code:

| # | site | reach-back | population | separates? |
|---|---|---|---|---|
| 1 | **G1** `latest = bars[-1]` — `drawdown = latest.close/hi − 1` | unbounded | 1,780 | **YES** — 1,778 @0d, 1 @1d, **1 @51d (INHD)** |
| 2 | G1's 52-week window | bounded by construction (anchored on `reference_date`) | — | n/a |
| 3 | G2's start anchor | **bounded in #294** | 596 | 593 @0d, then 108/116/1,472d |
| 4 | **G3** `annual_eps_as_of` | unbounded | 412 | **NO** — continuous tail |

**BOUNDED SITE 1 ONLY** (earliest in the funnel; bounding it changes the population later gates see,
so 3 and 4 must be re-measured after this lands, not extrapolated).
**THE BOUND IS THE SHIPPED CONTRACT, NOT A NEW CONSTANT.** `price_staleness_days = 5` already
existed and was already applied to `last`; the DERIVED ratio G1 gates on was built with
`_derived(...)`, which carries no staleness at all. Applying it clears the market calendar (IWM and
MDY agree exactly; neither gap exceeds 4d) and refuses anything past it. Out of range →
**NOT_EVALUATED with its reason, never FAIL**. Span/count recorded by calling the shared
`window_facts` — no second implementation.

**TWO CORRECTIONS TO THE BRIEF'S PREMISE, both measured:**
1. **EV/EBITDA DECIDES NOTHING.** `enrich_with_fundamentals` sets `ev_ebitda_pctile_vs_history` to
   UNKNOWN unconditionally — deferred, needs net-debt/EV — so `gate_g3_multiple_floor` ALWAYS falls
   through to P/E. Across the 281 committed candidates: **G3 UNKNOWN 186, PASS 95, FAIL 0.** The
   P/E reach-back is not the smaller path, it is the ONLY resolving path, which makes site 4 larger
   than the brief assumed rather than smaller.
2. **G3 DOES NOT SEPARATE.** Of 412 names reaching G3, 263 have a positive annual EPS and its
   period-end age runs p50 210d · p75 575d · p90 1,763d · p99 4,958d · **max 6,054d (16.6y)** —
   buckets ≤1y 174 · 1–2y 26 · 2–5y 37 · >5y 26. A continuous tail with no gap, so its bound cannot
   come from the population; it must come from the FILING CADENCE. Queued as its own PR.
   (The other 149 have no positive annual EPS at all → G3 UNKNOWN → **admitted**, since UNKNOWN
   does not reject.)

**FLAGGED, NOT FIXED:** `high_52w`/`low_52w` stay PRESENT on a stale name and are still labelled
52-week while their window is truncated at the last bar — INHD's covers ~10.5 months, not 12. Same
class (a value claiming a window it does not cover), but they do not gate, so they are out of this
PR's invariant. Queued beside the G3 bound.

**POOL EFFECT OF THIS BOUND: none.** 0 of the 281 become NOT_EVALUATED at G1 — INHD, the one stale
name, had already FAILED G1 and was never in the pool. Whole-run effect is 1 of 1,780 names, and the
value of the change is that the failure is now recorded as *unassessable* rather than *rejected*.
