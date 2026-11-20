---
status: shipped
date: 2026-11-20
prs: [1158]
supersedes:
superseded-by:
---

# The theme-intelligence concurrency tests order their stand-in's calls by events, not by sleeps: the three that assert how many calls were in flight or the order they finished in no longer fail under parallel load ($0, tests + record)

**WHAT.**
- `tests/test_theme_intelligence_concurrency.py` (#1141) gets a `Gate`. Each gated call waits at a
  `threading.Barrier` until `together` calls are in flight at once. Then, if the gate has a
  `hold`, the call waits for that event. If it has a `finish_order`, the call waits for its turn,
  and finishing passes the turn to the next call (chained `threading.Event`s). Each wait gives up
  after `GATE_SECONDS` (10 s) with an `AssertionError` naming the thesis. A call that never comes
  fails the test and never hangs it.
- Three tests are gated. Their assertions and meaning are unchanged:

  | test | asserted | gate |
  |---|---|---|
  | `test_a_concurrent_pass_writes_what_one_at_a_time_writes_in_input_order` | `most_live == 5`, `finished == order[::-1]` | `Gate(5, order[::-1])` on the 8-worker pass only (a gate of five would wait forever for calls the one-at-a-time pass never sends) |
  | `test_calls_in_flight_together_never_jointly_pass_the_run_limit` | `most_live == 3`, `len(started) == 3` | `Gate(3, hold=<all five refused>)`, so no admitted call settles and frees room for a thread that reaches the guard late. A gate failure in a thread is now re-raised by the test |
  | `test_calls_with_equal_usage_keep_their_own_ledger_label_when_one_fails` | `finished == [t2, t0, t1]` | `Gate(3, [t2, t0, t1])` |

  `_slowest_first` (80 ms steps) is deleted. It had no other caller.
- Three tests keep their sleeps, because no assertion in them depends on the order calls finish
  in. Each was run 10 times with its sleeps set to zero and 10 times with them inverted (the
  slowest made the fastest), on `-n 8`: 0 of 60 failed.
  - `[t0, t1, t0]` (`test_a_thesis_named_twice_…`): its NEGATIVE, mutant M3 (no wait for a
    thesis's first turn), is still caught with every sleep at zero.
  - `test_a_failed_call_is_raised_at_its_turn_…`.
  - `test_when_the_run_budget_binds_…`.
  In these tests the sleeps only shape the scenario (for example, earlier calls are still in
  flight at admission).
- No change to `vinci/`.

**WHY.**
- **The cause, checked.** The pass's main thread reads each thesis, builds its request and admits
  it before it submits the next one. The stand-in slept 80 ms longer for each earlier thesis, so
  answers came back in reverse order only while successive starts stayed under 80 ms apart.
  - Unloaded, the largest gap between successive starts was 1.5 ms (20 passes).
  - Under the load below, gaps reached 128.7 ms. All 6 failing passes of 240 had a gap of 89 ms
    or more.
- **Two failure shapes seen in pytest:** `most_live == 4` (one call finished before the fifth
  started), and the reverse finish order broken with all five in flight.
- **The reviewer's run.** One run of the reviewer's command (`-n 4` over `tests/test_theme_intelligence*.py`, 1,495
  tests) did not reproduce the failure: the target test passed. A local-only browser test failed
  instead (below).

**HOW VERIFIED.**
- **Failure rate, before and after, at one load.** The load is 24 `while True: pass` processes
  beside pytest `-n 8`. Each test is repeated by a scratch plugin that parametrizes it, as
  pytest-repeat does.

  | run | before (main `4db3d85a`) | after |
  |---|---|---|
  | the three gated tests ×60 each (180 runs) | **3 failed**: the concurrent pass 2 of 60, equal usage 1 of 60, the guard 0 of 60 | **0 failed** |
  | the whole file ×100 (1,000 runs, the three ungated tests included) | not run | **0 failed** |
  | in-process stress: 8 processes × 30 concurrent passes back to back, beside 24 busy loops (240 passes) | **6 failed** (start gaps up to 128.7 ms) | **0 failed** (start gaps up to 437.7 ms) |

  With no extra load (`-n 8` only), and with 16 busy loops, the before code passed 120 of 120
  runs each time. The flake needs a heavily oversubscribed machine.
- **The gated tests still catch what they claim.** Each mutation was applied to `vinci/`, run,
  and reverted:
  - **P1** (`_llm_workers` always returns 1, so the pass runs sequentially). The concurrent-pass
    test and the equal-usage test both fail: "5 (3) calls were never in flight together within
    10.0 s".
  - **G1** (a reservation is never counted, which is the old guard's shape). The guard test fails
    with `most_live == 8`, and the gate's errors are shown.
  - **U1** (an unrecorded call matched by usage alone, round 1 of #1141). The equal-usage test
    fails on the ledger labels.

  Each fails in about 10 s per test. None hangs.
- **The suite.** Ruff is clean, and `pytest -m "not network" -n auto` is green (the PR body has
  the totals).

**BOUNDARY.**
- All counts are from one Mac with 8 cores, shared with other sessions (load average ~7 before
  the busy loops). Python 3.14.3, pytest 9.1.1, pytest-xdist 3.8.0. Measured on 2026-11-20 at
  main `4db3d85a` plus this change.
- Population: the named tests of `tests/test_theme_intelligence_concurrency.py`.
- Unit: one pytest run of one test id, or one concurrent enrichment pass in the stress harness.
- The before rate is small-sample (3 of 180). The case for determinism is structural: a barrier
  and chained events, with no clock in the asserted order. The 1,000 and 240 runs after are the
  measurement.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A pass broken so that a gated call never comes takes up to 10 s per wait to fail, instead of
  failing at once. That is a slow red, never a hang.
- The gated tests fix the finish order rather than produce it from wall time. What they test is
  that the pass's output does not depend on that order. That is the claim, and the old sleeps
  only approximated it.
- **Found, not fixed:**
  - `tests/test_sec_pacing.py::test_two_processes_on_one_machine_share_one_budget`, gate run
    44689179772 (#1152's): `min gap 0.001s across two processes` against a floor of
    `_INTERVAL / 2` = 0.1875 s.
    - It is the same family as this flake (a real-clock bound that a scheduler stall under
      `-n auto` breaks), but a different mechanism. Its children timestamp each send in the mock
      handler, after `SharedPace.acquire()` has released the `flock`. If process A takes slot *k*
      and then stalls about one interval (~0.37 s) before its handler runs, its stamp lands
      within a millisecond of B's slot *k+1*. That stall is twice what the test's comment says
      lag "cannot outgrow".
    - A double take through the lock would read the same, and the log alone cannot tell the two
      apart.
    - A deterministic version would stamp the slot inside the lock: for example, a child's
      patched `os.pwrite` reads the `next_at − interval` the pacer writes there. A stall after
      the lock could not then shrink a gap.
    - #1139's failing run was not found: its branch's three gate runs read success on attempt 1.
  - `tests/test_theme_intelligence_group3.py::test_in_a_browser_a_filter_re_caps_the_articles_table_that_carries_the_id_itself`
    failed once locally under `-n 4`: headless Brave exited 2. It is skipped on CI (no Brave), so
    it is local-only, and it is likely parallel Brave instances. Not investigated.
