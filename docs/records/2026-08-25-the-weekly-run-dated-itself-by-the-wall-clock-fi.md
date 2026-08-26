---
id: 
status: shipped
date: 2026-08-25
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**THE WEEKLY RUN DATED ITSELF BY THE WALL CLOCK — FIXED 2026-08-25
(`fix/weekly-run-dates-itself-from-the-data`). THE FOUR "FAILURES" WERE THE GATE WORKING.**

**WHAT IT ACTUALLY WAS.** Not flaky CI, not a stale artifact — `vinci/cli.py::_cmd_run_weekly`
defaulted `--end` to `date.today()`, and that `end` becomes the universe as-of, the screen's
`reference_date`, and every relative-return window. The job fires Monday morning: on 2026-08-24
(a **Monday**, **07:04 UTC** — six hours before the US market opened) it stamped a queue
`2026-08-24` when the newest bar that could exist was Friday 08-21's.
`test_the_wall_clock_is_unreachable_from_the_reference_date` refused it at the gate every week
from 2026-08-03 on. **Main's newest manifest is still `2026-08-14-01`: nothing corrupt was ever
committed.** The run was STRUCTURALLY incapable of going green, not unlucky — and the earlier
diagnosis in this session ("stale price fixture") was the messenger, not the cause.

**SAME DEFECT, SECOND ENTRY POINT.** `_ref_of` in `assemble.py` had this exact wall-clock fallback
and was fixed in #355 ("a reference date names a moment the data reaches, never the clock"). That
fix is guarded by an AST scan **which reads `assemble.py` only** — so the orchestrator's entry
point kept its clock, unguarded, until a Monday cron exposed it. *The lesson is the guard's SCOPE,
not the fix: a per-module AST scan does not generalise to a bug class.*

**THE FIX.** `vinci.eod.last_completed_session(client, today=...)` asks the DATA: `grouped_daily`
returns an empty dict for a non-trading day, so holidays, half-days and an unclosed session all
answer for themselves — no calendar is shipped and none can rot. It probes from **`today - 1`,
never `today`**, because grouped-daily can return partial aggregates for a session in progress and
stamping a half-formed close is the lookahead trapdoor already shut once for entry prices. A stamp
that LAGS the data is harmless (the gate asserts `fleet <= frontier`); one that LEADS it is the
bug. `--end` still overrides and skips the probe. **Live proof:** replaying the broken Monday, old
→ `2026-08-24` (impossible), new → `2026-08-21`.

**TWO COUPLED REPAIRS THE SAME PR HAD TO MAKE, or the run still could not go green:**

1. **THE FIXTURE IS THE SECOND DERIVED MIRROR, AND ONLY ONE WAS BEING REBUILT.**
   `tests/test_maintenance_path.py::_cfg` builds its store from `tests/fixtures/prices/` on EVERY
   machine (deliberately — the maintenance pins passed on every laptop while main ran red for
   eleven merges). So the gate compares the freshly-screened fleet as-of against THOSE bars, not
   against the store. The job rebuilt `frontend/` and left the fixture behind, so a correct as-of
   would STILL have failed. `weekly-screen.yml` now rebuilds it after the screen and before the
   gate (which moves the store aside), and stages it by directory name.
2. **THE OBVIOUS VERSION OF (1) SILENTLY DISABLED A GUARD.** Once the fixture frontier catches up
   to the fleet as-of, `later` in the truncation pin is empty, `if later:` stops running, and the
   only assertion catching "a record carrying the frontier's close under an older stamp" vanishes
   **without ever going red**. The vintage is now FROZEN INSIDE THE FIXTURE — ten bars back from
   its own frontier — so bars after it exist by construction, every week, on every machine.

**INCIDENT → INVARIANT (shipped Y).** `scripts/build_price_fixture.py` wrote files inside its read
loop and `return 1`-ed on the first name with no bars. Observed, not theorised: run against a
partially-refreshed store it rewrote six names back to 2026-08-07, left WERN at 08-14, and never
reached IWM — **the benchmark carrying a different vintage from the names measured against it**,
which `rel_ret_vs_market` cannot survive. Now all-or-nothing, and the job runs it unattended.
