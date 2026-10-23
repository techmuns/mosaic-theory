---
id: 2026-10-24-operator-decision-dated-local
status: shipped
date: 2026-10-24
prs: [794]
supersedes:
superseded-by:
---

# An operator's decision is dated on the local calendar, and its pins agree: the first re-tag pin expected UTC's date and was red every night from 00:00 to 05:30 IST

**WHAT.** `vinci anchor-retag` dates a decision on the operator's LOCAL calendar
(`vinci/cli.py`, `today = date.today()`). That code is unchanged. Two changes are in
`tests/test_operator_decision.py`:

- `test_retag_records_a_decision_and_moves_no_value` expects `date.today()`. It had expected
  `datetime.now(UTC).date()`.
- New pin, `test_a_decision_made_now_is_dated_on_the_local_calendar_under_a_real_zone`. It sets the
  process's REAL zone (`TZ` + `time.tzset()`) and records a decision with no `--decided-on`. It
  then checks that the decision is dated on the local calendar and is recorded as made now (the
  machine's read is written beside it).
  - The zone is chosen so the run is always the divergent case: UTC−12 before 11:00 UTC, UTC+14
    from then on. UTC−12 reads yesterday until 12:00 UTC, and UTC+14 reads tomorrow from 10:00 UTC.
    Either way the zone's own midnight is at least an hour from the run.
  - The test asserts that local and UTC disagree before it runs the command. If the zone did not
    take, it fails loudly instead of passing on the easy case.

**WHY.** #780 introduced both sides. Its review (FINDING 5) moved the stamp from UTC to the local
calendar, so that a decision dated "today" just after local midnight is neither refused as a future
date nor read as backdated. `test_today_is_the_operators_calendar_and_never_the_future` pins that
choice. The older pin in the same file kept UTC. So from local midnight to UTC midnight
(00:00–05:30 IST) it failed on every commit. On 2026-10-24 at 00:05 IST it blocked `bin/commit`'s
gate for #792, which had to be re-run under `TZ=UTC`. CI runs in UTC, so it never saw the failure.

**Local is the right calendar for a decision, and it is the repo's convention:**

- **Human decisions are dated by the local calendar.**
  - The verdict of record: `decided_at=datetime.now()` (`vinci/cli.py:1413`). Its
    `reference_date` defaults to `date.today()` (`:1367`).
  - Theme ratification: `ratify_date` (`:3752`) and the forward-freeze stamp (`:3764`).
  - `close-position --as-of` (`:1481`).
  - `anchor-retag`'s `decided_on` (`:941`).
- **UTC is used for instants and machine logs.** Instants: `computed_at`, `built_at`, the run
  records' `started`/`finished`. Machine logs: `LayerRefresh.date` (`vinci/dossier/layer_refresh.py:67`).
  An instant is unambiguous in UTC. A calendar date names a day, and a decision's day is the
  operator's.

**Other tests with the same mismatch: none found.**

- A grep of `tests/` for a UTC calendar date (`now(UTC).date()`, `now(timezone.utc).date()`,
  `utcnow().date()`, `gmtime`) found two sites:
  - this one;
  - `tests/test_themes_draft.py:332`. It expects UTC because its code (the radar review's
    `reviewed`, `vinci/cli.py:3384`) stamps UTC. The test and code agree, so it does not flake.
- `date.today()` appears in 7 test files. Each one either compares against code that dates on the
  same local calendar (`run-weekly`'s last session, the monitor's `as_of`, `first_seen`) or makes
  no comparison across clocks.
- The full offline suite was run inside the window, in IST (see HOW VERIFIED). It is the
  empirical check of the grep.

**HOW VERIFIED.**

- **The failure, reproduced live.** At 00:26 IST on 2026-10-24, with the old pin, the command
  wrote `2026-10-24` (IST) and the pin expected `2026-10-23` (UTC): 1 failed. The copy was of the
  committed BRBR page, with the network stubbed.
- **The fixed pins, in five zones.** The three date pins (the fixed one, the `_Day` pin and the new
  one) were run under `Asia/Kolkata`, `UTC`, `America/Los_Angeles`, `<-12>+12` and `<+14>-14`.
  All passed: 3 passed in each zone.
- **Mutants.** Each mutant put one of the command's two calendar reads on UTC: the default stamp,
  and the "made now" comparison that decides whether the machine's read is recorded. Each was run
  against the three pins and restored byte for byte.
  - **In IST, inside the window:** all 6 killed.
  - **In `TZ=UTC`, as CI runs:** the fixed first pin let both mutants survive, because it cannot
    tell the clocks apart there. The `_Day` pin and the new real-zone pin killed both. The new pin
    is the only one that drives the DEFAULT stamp under a real clock on which the local and UTC
    calendars DISAGREE. It kills at any hour, in any zone the suite runs in.
- **The full offline suite, inside the window, in IST** (`pytest -m "not network"`, 00:28–00:31
  IST): **6,429 passed, 529 skipped, 37 deselected, 0 failed** in 178 s. No other test fails while
  the local and UTC calendars disagree.

**BOUNDARY.**

- **"The window."** From local midnight to UTC midnight. In IST (UTC+5:30) that is 00:00–05:30.
  Every run above was made on 2026-10-24 between 00:26 and 00:32 IST on the operator's Mac, on
  this change over the branch's base `795d7e7c`. That is one night, in one zone east of UTC. A
  zone west of UTC (local behind UTC) was exercised only by the three date pins, not by the full
  suite.
- **The test grep.** All of `tests/` at `795d7e7c`. 2 UTC-calendar lines. 7 files that call
  `date.today()`.
- **The convention survey.** All of `vinci/` at `795d7e7c`, by grep line. 31 lines match
  `date.today()`, comments and docstrings included. 1 line matches `now(UTC).date()`. The UTC
  instants (`datetime.now(UTC)` not reduced to a date) were read, not counted.

**FOUND, NOT FIXED (outside this change's scope).**

- **The radar review dates an analyst's decision on UTC's calendar.** `vinci/cli.py:3384`
  `"reviewed": datetime.now(UTC).date()`. A review made between 00:00 and 05:30 IST is stamped
  with yesterday's date. This is the same class as the stamp #780's FINDING 5 fixed. Its pin
  (`tests/test_themes_draft.py:332`) agrees with it, so nothing is red.
- **The decision ledger's `decided_at` column holds two naive clocks.** A verdict row is stamped
  with `datetime.now()` (local, `vinci/cli.py:1413`). A close row is stamped with
  `datetime.now(UTC).replace(tzinfo=None)` (`:1492`). `Store.iter_ledger` orders by that column
  (`vinci/store/store.py:628`).
  - Read on its own, this means a close logged within 5½ h of its verdict in IST could sort
    before it.
  - **Untested.** The 7 committed rows (`data/snapshots/decision_ledger.jsonl`) show no
    inversion: both close rows are stamped at midnight. Whether any reader depends on the order
    was not checked.

- **`anchor-retag` reads the local date twice** (found by this PR's own pre-PR review). It reads
  it at `vinci/cli.py:941` for the default stamp, and again at `:980` to decide whether the
  decision is "made now". The machine's network read sits between the two. If local midnight
  falls between them, a decision made now with no `--decided-on` is dated yesterday, and the
  machine's read is dropped as though the decision were backdated. Reusing `today` at `:980` would
  close it. It is left for its own change because this PR changes no production code.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **The new pin changes the process's zone for its own duration.** It restores `TZ` and calls
  `tzset()` in a `finally`.
- **`time.tzset()` is POSIX-only.** CI (Ubuntu) and the operator's Mac both have it. The suite
  does not run on Windows.
