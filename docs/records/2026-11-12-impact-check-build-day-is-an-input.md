---
id:
status: shipped
date: 2026-11-12
prs: [1025]
supersedes:
superseded-by:
---

# The impact check keys a kept page build by its UTC day, and compares two sides only when both were built within one and the same UTC day; it also refuses Polygon and Tiingo pulls by default

**WHAT.** `vinci.impact run` (RUNBOOKS §o) made three changes:
- **The build cache is keyed by UTC day.** `build_key` takes the day. A kept build is looked up
  under today's UTC day. It is kept under the one day it was built on, and never kept when its
  build ran across two days.
- **The child records the days.** Each page side's `clock.json` holds every UTC day its steps
  ran across (`child.utc_day`, at the first step and after the last). `run.build_days` adds the
  dates the page carries: `assembled_at`, and `statement_reconciliation.as_filed_by`.
- **Off-day sides are re-built.** Two sides built within one and the same UTC day are compared
  as they are. Otherwise `run.off_day_sides` names each side that is not exactly on the day a
  re-build lands on: today, or the latest day either side ran on if that is later. The run
  re-builds those sides once, head first. A page still on two days is set apart as run noise
  and not counted as a move, and the section names it.

The sweep's tooling is in the same PR. `--allow-vendor-pulls`: a Polygon or Tiingo response the
cache lacks is refused unless this flag is passed (coordinator, 2026-11-11: "No Polygon or
Tiingo bulk pulls without asking me"). `--skip-fail-first`: part 1 is left out, and the section
says NOT RUN.

**WHY.** A $0 build stamps today's UTC date on the page:
`statement_reconciliation.as_filed_by = datetime.now(UTC).date()` (`mechanical.py`,
`statement_recon.attach`). That date reaches the synthesis request's facts. The sweep's run of
#984 (base `65758333`, head `a3fc8e1b`) behaved like this:
- 21 of its 27 base sides were KEPT from the previous run, built from 23:43Z on 2026-11-11.
- Every head side was built after 01:26Z on 2026-11-12.
- 5 pages moved (BRBR, BURL, CNXC, EPAM, FUBO, 22 field changes), and so did their 5 requests,
  BURL's and CNXC's on the panel. Every one of those moves was the date.
- AMZN's base build STARTED at 23:43Z on 2026-11-11 and stamped 2026-11-12. The page's own
  start time (`assembled_at`) therefore does not name the day it stamps, which is why the child
  records the window.

**HOW VERIFIED.**
- *Fail first.* The 5 tests in `tests/test_impact_days.py` fail on main's code (`53e5f26e`) and
  pass on this branch.
- *Real dates.* The fixture `tests/fixtures/impact/pr984-days.json` holds the #984 run's own two
  dates per page side. Given those dates, `off_day_sides` re-builds base on exactly AMZN, BRBR,
  BURL, CNXC, EPAM and FUBO. Every page that moved in that run is among them.
- *Live corpus.* The check ran over every finished sweep run on disk: 41 runs, 31 of them with
  pages built, 842 page comparisons. It flags those 6 pages of #984 and nothing else.
- *Cache.* A kept build is reused on its own UTC day and re-built the next day. A build across
  midnight is never kept. Both are tested with a stand-in build.

**BOUNDARY.**
- The #984 counts are that one impact run: stamped 2026-11-12T01:23:36Z; 27 committed pages at
  head `a3fc8e1b`; the store snapshot priced to the 2026-11-09 close.
- The corpus count is every `report.json` under the sweep folder at 2026-11-12 ~16:00 IST: 41
  runs, of which 31 built pages. The other 10 were same-code or not reached by the change.
- One "page comparison" is one page in one run.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *Daily rebuilds.* Main's side is now built once per main commit per UTC day, not once per
  commit.
- *Midnight runs.* A run that crosses UTC midnight re-builds the pages whose sides fall on two
  days.
- *The date stays on the page.* The page's own date is NOT normalised away. It is a real input,
  and with a fresh cache response it can admit a fact filed that day.
- *Two clocks in production (not changed here).* The production build reads the clock twice:
  `assembled_at` comes from `assemble.built_at`, while `statement_recon.attach` takes its own
  `datetime.now(UTC)`. A build across midnight therefore carries two dates. Its falsifier is
  AMZN's base side above. The `assemble` comment says the build's instant is "taken ONCE". The
  operator ruled on 2026-11-12 that B fixes the date leak in `statement_recon.py` ("Fix now, by
  B"), so it is not built here.
- *A re-build can bring back a transcript failure (deferred).* A one-sided transcript failure
  can return when `realign` re-builds a page that the transcript retry never touched. That page
  is not set apart as noise. It needs both a midnight crossing and a LibreOffice collision on
  the same page.
