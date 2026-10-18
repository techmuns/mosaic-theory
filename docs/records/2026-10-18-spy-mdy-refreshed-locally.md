---
id: 2026-10-18-spy-mdy-refreshed-locally
status: recorded
date: 2026-10-18
prs: [744]
supersedes:
superseded-by:
---

# SPY and MDY refreshed in this machine's store, so local assemblies read every page's market figures

**WHAT.** Before the refresh, this machine's local price store (`data/vinci.db`, git-ignored) held
SPY to 2026-07-22 and MDY to 2026-08-05. IWM ran to 2026-10-16. Under the benchmark guard (#743,
`docs/records/2026-10-17-benchmark-bar-guard.md`), a local assembly of any of the 15 SPY or MDY
pages therefore refused its market figures. Operator instruction, 2026-10-18: "refresh SPY and MDY".

**HOW.** Grouped-daily, the mode both series were already stored in, with each start set at the
series' own gap. `vinci refresh` takes an explicit `--start`, so the store-wide-latest start that
dug the 2026-09 hole cannot recur here:
- `vinci refresh SPY --start 2026-07-23 --end 2026-10-16`: 62 days fetched, 61 trading days, 61
  bars written.
- `vinci refresh MDY --start 2026-08-06 --end 2026-10-16`: 52 days fetched, 51 trading days, 51
  bars written.
- Every day came from the local netcache (the 2026-10-17 weekly run's grouped-daily pulls), so no
  new Polygon calls were made.
- A pre-refresh copy of the store was kept.

**HOW VERIFIED.**
- **Coverage.** SPY has 368 bars, 2025-05-01 → 2026-10-16. MDY has 1,287 bars, 2021-09-01 →
  2026-10-16, the same count as IWM. The largest gap in each is 4 days (after 2026-09-04, Labor
  Day), the calendar's own.
- **Cross-source.** The refreshed closes match the figures the 2026-10-07 record read on another
  machine:
  - SPY 754.05 on 09-16 and 773.38 on 09-22;
  - MDY 665.88 on 09-16 and 670.49 on 09-22.
- **The guard reads every page again.** All 26 committed dossiers at their own date and at
  2026-10-16, 52 cases: 52 read and 0 refused (22 IWM, 18 SPY, 12 MDY). Before the refresh, 30 were
  refused.

**BOUNDARY.** This machine's store, 2026-10-18; other checkouts and machines keep their own stores.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Nothing committed changes. The nine committed pages that
carry the stale 2026-09-16 close are still uncorrected (STATE row 32 (7), the operator's
re-assemble-versus-refresh decision). This only makes a local re-assembly possible.
