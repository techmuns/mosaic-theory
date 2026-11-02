---
id: 2026-11-02-a-tiingo-budget-test-dated-its-month-and-went-red-when-the-month-turned
status: open
date: 2026-11-02
prs: []
supersedes:
superseded-by:
---

# A Tiingo-budget test dated "the month" by hand and went red when the month turned

**WHAT.** `tests/test_tiingo_budget.py::test_the_reserve_is_held_before_any_new_symbol_is_asked`
checked the reserve's cache TTL against `datetime(2026, 10, 1)`. The fetch it checks
(`vinci/quality/sources/prices.py`, `_TiingoFetch.hold`) dates the month's start off the wall
clock (`datetime.now(UTC).replace(day=1, …)`). On 2026-11-01 the two parted by exactly one month,
and the suite went red on main (894e962e) with no code change. The test now dates the month the
way the fetch does. Test only; no output moves, so no extraction-version row.

**WHY.** A fixed calendar date compared against the live clock is true only for the month it was
written in (#839). Every PR's gate and every local commit through `bin/commit` refused, which
blocked unrelated work.

**HOW VERIFIED.**
- On main 894e962e the test fails: `abs(ttl - (now - 2026-10-01)) = 2,678,400.0` seconds (31
  days) against a 120-second tolerance.
- On this branch all 13 tests in the file pass.
- With the wall clock frozen to 2026-10-15, 2026-11-02 and 2026-12-31 (both modules' `datetime`
  and `time.time` patched together), the fixed test passes in each month.
- ruff is clean on the file; the gate's `mypy --strict vinci` is clean (tests are not
  mypy-gated).

**BOUNDARY.** One test function in one file, measured 2026-11-02 against main 894e962e. The
2,678,400-second gap is October's 31 days in seconds.

**WHAT IT COSTS / WHAT IS ACCEPTED.** NOT CHANGED, REPORTED: the fetch reads "the month" from the
wall clock while its `TiingoBudget` carries its own month string, so a budget built at 23:59 on a
month's last day and a fetch made after midnight would disagree on which month a cached copy must
be newer than. In production both are built in one run (`month_of(datetime.now(UTC))`), so the
window is that run's span across midnight UTC on a month's last day. Making the fetch read the
budget's month would close it; that is a code change outside this fix. Other tests compare the
live clock (`time.time()`, `datetime.now`, `date.today`) in 8+ files; none is red today, and none
was audited here for the same shape.
