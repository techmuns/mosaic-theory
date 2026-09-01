---
id:
status: shipped
prs: [544]
date: 2026-09-01
supersedes:
superseded-by:
---

# The weekly-dating pin stopped depending on the wall clock — it freezes it instead

**WHAT.** `test_run_weekly_takes_its_date_from_the_data_and_not_the_clock` now freezes `cli.date`
at Monday 2026-08-24 (a `date` subclass whose `today()` returns it) instead of stubbing a fixed
session and letting the real clock run underneath. **Test-only: no production line moves.**
`_cmd_run_weekly`'s dating was correct before this change and is correct after it.

**WHY.** The test stubbed the last completed session as Friday 2026-08-21 while `_cmd_run_weekly`
searches back `_SESSION_LOOKBACK_DAYS = 10` from `date.today()`. That is green while today is
within ten days of the stub and red forever after: on 2026-09-01 the gap reached 11 days and
`last_completed_session` raised `no completed trading session found in the 10 days before
2026-09-01`. The failure was **on origin/main, independent of any branch** — found while reviewing
#543 and confirmed by running it on main. A test that rots into a standing red teaches people to
skim past failures, which costs more than the bug it was watching for.

**Freezing beats dating the stub relative to today, and that was MEASURED rather than assumed.**
The first spelling tried here — `session = today - 3` — failed on its first run, because
2026-09-01 minus three days is a Saturday and the helper skips `weekday() >= 5`; one week in three
it would have rotted the same way. A stub at `today - 1` would have let a naive `date.today() - 1`
pass the assertion. Monday-after-Friday is also the exact shape of the 2026-08-24 incident this
module exists for, so the frozen pair keeps the calendar realistic.

**HOW VERIFIED.** Full offline suite `pytest -m "not network"` exit 0 — **3,271 passed, 142
skipped**; `ruff` clean; `mypy --strict vinci` clean (137 files), and the test file is clean under
`--strict` too though `tests/` is not in the gate. Then **two mutations, both red**:

1. production regressed to `end = date.today()` → `AssertionError: run-weekly dated itself
   _FrozenDate(2026, 8, 24) instead of the last completed session 2026-08-21 — the wall clock is
   back`.
2. the freeze line deleted → the original `RuntimeError` returns.

The second is the one that matters: it proves the freeze is **load-bearing rather than
decoration**, i.e. the test was repaired without quietly weakening what it asserts — the failure
mode a green-again test is most likely to be hiding.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **The freeze patches `cli.date`, the name the call site actually reads.** A refactor to a
   different spelling would silently stop freezing — but the test then meets the real clock and
   goes RED, so the failure is loud, not silent, and `monkeypatch.setattr` raises outright if the
   seam is renamed away.
2. **THE CLASS IS UNMEASURED, AND THE ATTEMPT TO MEASURE IT FAILED** — recorded because the
   failure is the useful part. 73 test files hard-code 2026 dates. A pytest plugin that advanced
   the clock 90 days by rewriting `datetime.date` / `datetime.datetime` produced 15 failures
   across 4 modules, which read like a fleet of further time bombs. **It was not: a ZERO-SHIFT
   CONTROL reproduced every one of them**, so the instrument was the cause, and the same four
   modules pass unpatched. Two defects: the shim's `today()` returned the base class and broke
   `isinstance` (the same bug shape being fixed here), and it cannot reach the JavaScript half of
   the stack, so `_node`-driven tests compared a shifted expectation against an unshifted
   renderer. **The control said no, and the number is discarded rather than reported.**
   FALSIFIER: if a second date-pinned test rots into a standing red, ship the sound instrument — a
   scheduled CI job running the offline suite under a genuinely shifted clock (a container with
   `faketime`), which moves both halves of the stack and has no subclass identity to break.
