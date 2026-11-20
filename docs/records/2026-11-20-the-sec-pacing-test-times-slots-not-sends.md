---
status: shipped
date: 2026-11-20
prs: [1165]
supersedes:
superseded-by:
---

# The two-process SEC pacing test times each slot where the lock decides it, not each send: a stall between slot and send no longer fails it under load, and a missing flock now fails it every time ($0, tests + record)

**WHAT.**
- `tests/test_sec_pacing.py::test_two_processes_on_one_machine_share_one_budget` keeps its shape:
  four real processes on the real clock over a mock transport. Two share a pace file (the PAIR)
  and two have a file each (the CONTROL).
- Each child now records two kinds of event:
  - `take`: the moment a request takes its slot. This is the one wall-clock reading
    `SharedPace._update` makes under the flock, kept by a recording clock installed as
    `netcache.time`. If `_update` ever reads the clock other than once, the child fails and
    names the reason.
  - `send`: the moment the request reaches the mock transport (what the test timed before).
- What the test asserts:
  - Each child's events are exactly `take, send` eight times: every request took a slot of its
    own before it was sent.
  - No two of the pair's 16 slots are closer than one whole interval (0.375 s), less 1 µs of
    float rounding. The old floor was half an interval, on sends.
  - The control fails that same check.
- The child's read of the pace file lingers 5 ms before its write (`SlowRead` wraps
  `netcache.os.pread`). Without the flock, two processes then read the same slot on nearly every
  turn, so a missing flock fails the test every time instead of only when two reads happen within
  microseconds.
- The file's seven other tests are unchanged. No change to `vinci/`.

**WHY.**
- **It was the measurement, not the lock.** The pacer takes a slot under the flock, releases it,
  and only then sends. The test timed the send. One process can stall between its slot and its
  send while the other sends on time, so their sends land together although their slots were an
  interval apart. A double take through the lock would look the same in those times. The slot
  times tell the two apart.
- **Checked by a harness** (the test's four processes, each recording both times): 60 runs at
  load averages 31.3–44.7.
  - 4 runs failed the old check, with send gaps of 0.0017, 0.0713, 0.101 and 0.1498 s.
  - In those 4 runs the pair's slots were never closer than 0.3750–0.3753 s. The pair's slot
    gap was at least 0.3750 s in all 60 runs.
  - Each failing run had one process waiting 0.24–0.46 s between its slot and its send. The
    test's old comment said that delay "cannot outgrow 0.19 s".
  - Every request in all 60 runs took its own slot before it was sent.
- **The lock's guarantee is exact.** A slot is taken only when the reading made under the flock
  is at or past the `next_at` the previous taker wrote, and the taker writes `now + interval`.
  So two slots are never closer than one interval, whatever the scheduler does afterwards. A
  check on the slots needs no allowance for a loaded machine.
- **The send-time spread is real, and it is in production too** (see Found, not fixed).

**HOW VERIFIED.**
- **Load.** 6 `while :; do :; done` loops, plus two loops of the offline suite at `-n 8` (this
  file deselected), with 4 copies of the test running at once. Other sessions shared the
  machine, so the load average is stated per batch.
- **Failure rate, before and after:**

  | test | runs | failed | load average (1 min) |
  |---|---|---|---|
  | before (main `ae5bd872`) | 40 | **3** (`min gap 0.167s` / `0.178s` / `0.173s across two processes`) | 15.4–30.8 |
  | before, a copy of the tree | 40 | **1** (`min gap 0.087s`) | 42.9–85.2 |
  | after, first version (no `SlowRead`) | 80 | **0** | 24.5–62.1 |
  | after, as committed | 100 | **0** | 37.7–131.8 |
  | after, as committed, a copy of the tree | 12 | **0** | 43.3–47.6 |

- **Mutants.** Each mutant ran in its own copy of `vinci/` with the test beside it, never in the
  checkout:

  | mutant | test before | test after, no `SlowRead` | test after, as committed |
  |---|---|---|---|
  | `noflock`: both `fcntl.flock` calls removed, the thread lock kept | 18 of 20 failed | 18 of 20 failed | **30 of 30 failed** |
  | `ownfile`: a pace file per process (no shared budget) | 20 of 20 failed | 20 of 20 failed | **20 of 20 failed** |
  | `nowait`: `acquire` sends whether or not it got a slot | 20 of 20 failed | 20 of 20 failed | **20 of 20 failed** (the `take, send` order check) |

  - The after test fails `noflock` and `ownfile` with slot gaps of 0.0000–0.0049 s.
- **The other timing tests in the file.** Five of the file's seven other tests assert on
  times. They are deterministic by construction: they run on the file's per-thread virtual
  clock, which only sleeping moves. So the times they assert on depend on the order slots are
  reserved under the locks, never on the scheduler. The other two check which pace file is in
  use. All seven (`-k "not two_processes"`, the `network` one included) passed 40 runs of 40
  under the load at averages 53.9–75.6.
- **The suite.** Ruff and `mypy --strict vinci/` are clean, and `pytest -m "not network"` is
  green (the PR body has the totals).

**BOUNDARY.**
- One 8-core Mac, shared with other sessions; Python 3.14.3, pytest 9.1.1, pytest-xdist 3.8.0.
- Measured on 2026-11-20 between 16:45 and 17:22 IST, at main `ae5bd872` plus this change.
- Unit: one pytest run of one test id, or one run of the 4-process harness.
- Load average: the 1-minute figure read as each run started.
- The before rates are small samples (3 of 40, 1 of 40, 4 of 60). The case for determinism is
  structural: no assertion reads a time measured after the flock is released. The 192 runs after
  are the measurement.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The test no longer asserts anything about send times. That matches the code's own claim: the
  lock spaces slots, and `vinci/netcache.py` already says a send leaves after its slot.
- Every pace-file read in the test's children takes 5 ms longer (`SlowRead`). This adds well under
  a second to the test.
- The control still needs its two processes to run at the same time. Its trains of 8 slots
  overlap unless one process starts about 2.6 s (7 intervals) after the other. In 60 harness runs
  at load averages 31.3–44.7, the control's first slots were at most 0.0215 s apart.
- **Found, not fixed** (production, so it is reported, not changed):
  - `vinci/netcache.py` (the comment on `SEC_MAX_REQUESTS_PER_SEC`) says "a send leaves some
    milliseconds after its slot, so a loaded machine can bunch a few". Under these loads the
    delay reached 0.464 s (pair) and 0.594 s (control).
  - With a delay of up to L seconds, a machine's sends in any one second come from its slots in
    1 + L seconds: up to 4 at L = 0.46 and 5 at L = 0.59, against the 3 the slot arithmetic
    allows.
  - Across three machines, SEC's ceiling is 10 against a nominal 9. Exceeding it needs every
    machine sending flat out, heavily loaded, at the same moment.
  - `tests/test_sec_budget_across_machines.py::test_two_machines_sending_at_once_stay_under_secs_ceiling_per_user`
    times sends the same way, against a ceiling of 10 where the slot arithmetic gives 6. It
    passed 24 of 24 at load averages 66.2–80.3.
