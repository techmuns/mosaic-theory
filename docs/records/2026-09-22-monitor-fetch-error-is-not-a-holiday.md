---
id:
status: shipped
date: 2026-09-22
prs: [642]
supersedes:
superseded-by:
---

# A failed price fetch stops `vinci monitor` instead of dating the book snapshot to an earlier session

**WHAT.** `vinci monitor` dates its snapshot to the latest session on or before `--ref`, stepping
back over non-trading days. It found the session with `except Exception: cache[d] = {}`, so every
fetch failure (a 429 whose retries ran out, a 5xx, the network) was filed as a holiday and stepped
over. The step-back is now `monitor.session_on_or_before`. It steps back only over an EMPTY day,
which is how `grouped_daily` says a market was closed. A raised fetch stops the run and names the
date it failed on, and nothing is written.

**WHY.** Observed 2026-09-22, re-cutting the 2026-09-16 day for the artifact pass (#641). The price
fixture rebuild had just exhausted Polygon's rate limit. `vinci monitor --ref 2026-09-16` then filed
09-16 and 09-15 as holidays and wrote `data/monitor/2026-09-14.json`: a book snapshot dated two
sessions early, with nothing on screen to say so. It was caught only because the command printed
the path it wrote. The file was deleted and the re-cut re-run once the limit cleared.

**HOW VERIFIED.**
- **The observed shape, pinned:** 09-16 and 09-15 raise `HttpError` and 09-14 answers. The step now
  raises, naming 09-16; the old code returned 09-14.
- **A real holiday (an empty day) still steps back** to the prior session.
- **A week of empty days is still refused.**
- **End-to-end:** the real command, over copies of the committed ledger, securities and benchmark
  assignments, with a throttled price source. It raises at 2026-09-16 and the monitor directory
  gains no file.
- **Mutation:** both new pins fail with the pre-fix behaviour restored, and pass with the fix.
- **No other call site** swallows a fetch error. `last_completed_session`, the universe build, the
  theme scans and the cohort script all let it propagate; the monitor was the only one.
- **Full offline suite:** 3,956 passed, 45 skipped, 0 failed.

**BOUNDARY.** The one call site in `_cmd_monitor`; lookback unchanged (8 days: `ref` plus 7 back).

**WHAT IT COSTS / WHAT IS ACCEPTED.** A throttled monitor run now fails instead of producing a
snapshot, and the operator re-runs it. That is the intended trade: a missing day is visible, a
wrongly-dated one is not.
