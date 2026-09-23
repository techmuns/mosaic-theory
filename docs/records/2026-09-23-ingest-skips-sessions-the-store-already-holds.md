---
id:
status: shipped
date: 2026-09-23
prs: [643]
supersedes:
superseded-by:
---

# The price refresh skips sessions the store already holds, re-pulling only a bounded recent window

**WHAT.** `ingest_prices` fetched every weekday in its window on every run — 1,304 whole-market
calls for the weekly screen's 1,825-day lookback — regardless of what the store already held. It
now SKIPS a session the store holds, except inside a 30-day restatement window
(`RESTATE_WINDOW_DAYS`), which is always re-pulled.

Two conditions guard the skip, each from a way the obvious version is wrong:

* **A COUNT, never presence** (`_SESSION_PRESENT_FRACTION = 0.5`). `vinci refresh <T> --aggs` writes
  a handful of rows into a session; reading that as "this day is ingested" would skip it for the
  whole universe.
* **Counted over the ids BEING INGESTED, never the whole table.** The screen ingests the universe,
  then the benchmark, as two calls. A day can hold 1,870 universe bars and no IWM bar; a table-wide
  count would answer 1,870 for the benchmark's own ingest and IWM would never be fetched at all.

A store that cannot report what it holds (no `session_bar_counts`) is never trusted into a skip —
it re-pulls everything, exactly as before.

**WHY.** The weekly screen had become unrunnable. On 2026-09-23 it failed on Polygon's rate limit
locally and again in CI (run 35835853063, dead in 19s): ~5 requests/min against 1,304 calls is
~4.5 hours of pure throttle, and CI carries no store, so it re-acquires five years of bars every
run to compute a screen. The operator's correction was the design: *"why don't we have prices for
the past if we already fetch them — what is the point of fetching it again always?"* The bars ARE
in the local store; acquiring them again was the waste. The one thing a re-pull genuinely buys is
restatement — bars are fetched `adjusted=true`, so a stored bar keeps the split basis it was
fetched on — and that is what the 30-day window preserves.

**HOW VERIFIED.** A dry run over a COPY of the live store
(`mosaic-theory-ta/data/vinci.db`, 300MB, copied 2026-09-23 13:57), with a client that records the
day and answers empty, so nothing is fetched and nothing is written:

| leg | fetched | held | of |
|---|---|---|---|
| universe (2,128 names) | 79 | 1,225 | 1,304 weekday sessions |
| benchmark (`IDX-IWM`) | 71 | 1,233 | 1,304 weekday sessions |

The 79 decompose exactly: **51** sessions hold no bars at all (market holidays, incl. 2026-09-07);
**28** hold fewer than the 1,064-bar floor — `2026-08-12 .. 2026-09-21`, the per-name
`refresh --aggs` residue at **26 rows a session** against ~1,870 on a whole-market day; **0** sit
in the restatement window above the floor. That 28-session block is the guard earning its keep on
live data: presence alone would have skipped six weeks across 2,128 names.

Four pins, each mutation-checked red at its own assertion and green restored:
`test_a_session_the_store_already_holds_is_not_re_pulled` (⊕ old held session skipped; ⊖ a held
session inside the window re-pulled; ⊖ a one-name refresh's rows never pass for a whole-market day;
⊖ a store without the count re-pulls everything) and
`test_a_day_the_universe_holds_is_still_fetched_for_the_benchmark`.

**BOUNDARY.** All counts above: window `2021-09-23 .. 2026-09-22` (1,825-day lookback from a
2026-09-22 reference date), weekdays only, unit = SESSIONS unless stated as bars/rows. Population =
the store's `latest_universe` as of 2026-09-21, 2,128 names, floor 1,064 bars. Row counts are of
`prices` over that window in the store copy described above. The 1,304 and the CI failure are from
2026-09-23; the ~5 requests/min is the current data plan, not a measured rate.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **A split older than 30 days leaves the bars before it on the pre-split basis** until something
   re-pulls them; `vinci refresh <T> --aggs` does. Falsifier: a price series with a level break at a
   split date that the current adjusted series does not show.
2. **The 51 holidays are re-fetched on every run, forever** — a closed session holds no bars, so it
   can never be "held". ~51 calls ≈ 10 minutes per run at the current limit. Not fixed here: the fix
   is a persisted known-empty-session marker, which is new state and was not in scope.
3. The floor is a FRACTION of the ids being ingested, so a genuine whole-market day that lost more
   than half its names to delisting between runs would be re-fetched. That is the safe direction.
