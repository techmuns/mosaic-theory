---
id:
status: shipped
date: 2026-09-23
prs: [644]
supersedes:
superseded-by:
---

# The Polygon pace is set to what the plan actually serves, measured, and a rate limit now waits out its window instead of retrying inside it

**WHAT.** `PacingConfig.polygon_requests_per_min` read **100.0** behind a comment asserting *"Polygon
Starter lifts the free-tier 5/min cap"*. The account does not serve that. It is now **4.0** by
default — under the measured ceiling rather than on it — readable from
**`POLYGON_REQUESTS_PER_MIN`**, and `Config.pacing` is built per config rather than once at import,
so an override set after import (a CLI that loads `.env` on entry) is actually honoured. An
unreadable override RAISES; it never falls back to the default silently.

**AND A 429 IS A CLOCK, NOT A QUEUE.** `_fetch_with_retries` sent 429 down the same exponential
ladder as a 5xx — 1+2+4+8+16 ≈ **31 seconds of total backoff against a limit enforced per
MINUTE**, so every retry landed inside the window that had just refused the call, and the fifth
failure raised "Exhausted retries". 429 now waits `_RATE_LIMIT_WAIT_SEC` (61s, clearing a 60s
window) per attempt; **5xx keeps the fast ladder**, because a server error is not a clock. The
retry BUDGET is unchanged, so an exhausted rate limit still fails loud.

**WHY.** Pacing 20x above what the plan serves is how every recent Polygon job died, and the retry
path could not recover because it retried inside the refusing window. With #643 cutting the weekly
refresh to 79 sessions, these two were the remaining blockers between the operator and a weekly
screen that completes. The comment is the deeper lesson: it stated a plan as fact, and the number
was trusted for as long as nothing forced a measurement.

A wrong default must not need a code edit to correct twice, hence the env override — and the
import-time freeze was found by the pin that tests it, not by inspection: a bare `PacingConfig()`
as a field default is evaluated when the class is defined, so an env-driven pace would have been
frozen to whatever the environment held at import.

**HOW VERIFIED.**

* **The plan's ceiling, measured.** Ten `/v3/reference/tickers/<T>` calls, distinct tickers, ~2s
  apart, no cache layer: **200 on calls 1-6 (t+1.1s … t+12.1s), 429 on calls 7-10** (t+14.0s …
  t+20.0s). That is a ~5/min ceiling, not 100.
* **The new pace, against live Polygon, through the real client.** `PolygonEodClient.from_config`
  over an empty cache dir, six `grouped_daily` calls: **t+1.0s, 15.9s, 31.0s, 46.0s, 61.0s, 76.1s**
  — 15s spacing, every call 200, the retry path never entered. All six days returned 0 bars, which
  is also the confirmation that those dates (2021-11-25 … 2022-05-30) are closed sessions.
* **No retry hint exists to read.** A second burst (8 calls, ~0.5s apart) returned 200 five times
  then 429; the 429 carried **no `Retry-After`, no `X-RateLimit-*`, no `RateLimit-*`** — only a body
  saying to wait or upgrade. So the window itself is the only honest wait.
* **The failure this fixes, observed.** A weekly attempt against an empty store died at
  `Exhausted retries for …/v2/aggs/grouped/…/2021-09-29?adjusted=true` after five sub-window
  retries.
* **Pins.** `test_the_polygon_pace_stays_under_the_plans_five_a_minute` (pins the PACE, not the
  constant: ≤5/min and ≥12s between calls), `test_the_polygon_pace_is_overridable_without_a_code_edit`
  (which caught the import-time freeze), `test_an_unreadable_pace_override_fails_loud` over
  `"fast"`, `""`, `"0"`, `"-5"`; and `tests/test_netcache_rate_limit.py` — ⊕ a 429 waits a full
  window, ⊖ a 5xx still retries at 1s/2s/4s, ⊖ an unclearing 429 still raises, ⊕ a mixed 503→429
  sequence waits per cause. **Mutation:** 429 back on the exponential ladder, 5xx over-corrected to
  a full window, and the window shortened to 30s — each fails a different pin, all pass restored.

**BOUNDARY.** All three measurements are from 2026-09-23, one Polygon account/key, from this
machine.
The ceiling probe: 10 calls, `/v3/reference/tickers/<TICKER>`, ~2s spacing, cache bypassed, unit =
HTTP status. The client run: 6 calls, `/v2/aggs/grouped/…` on 2021-11-25, 2021-12-24, 2022-01-17,
2022-02-21, 2022-04-15, 2022-05-30, fresh cache dir, unit = seconds since first call. The 1,304 and
79 session counts are #643's, over 2021-09-23 … 2026-09-22 weekdays, universe 2,128 names.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **Every Polygon job is now slow by construction** — 15s per uncached call. The weekly's remaining
   work is ~31 uncached sessions ≈ 8 minutes, so this is affordable where the call count is small,
   and unaffordable where it is not. That is a true statement about the plan, not about the code.
2. **CI cannot run the weekly screen at all under this plan** — it holds no store (`data/vinci.db`
   is git-ignored, prices are not snapshotted), so it re-acquires all 1,304 sessions ≈ 5.4 hours.
   The weekly runs LOCALLY until the plan changes. Recorded as STATE.md §5.0 row 31, owner:
   operator.
3. **4.0 is a face-validity choice, not a measured optimum** — it leaves ~20% headroom under a
   rolling 5/min window. Falsifier: 429s during a paced run, which would mean the window is
   stricter than measured.
4. **A rate-limited call now costs up to ~4 minutes before it gives up** (4 retries x 61s), where it
   used to cost ~31 seconds. That is the point — the old cost bought a guaranteed failure — but a
   badly-paced job will now fail SLOWLY rather than quickly. Pacing is what keeps that path cold.
