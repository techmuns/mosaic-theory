---
status: shipped
date: 2026-11-13
prs: [1065]
supersedes:
superseded-by:
---

# The gate runs the offline suite across the runner's cores (`-n auto`, pytest-xdist 3.8.0 from the lock), every test's outcome the same as on one process, after four tests stopped writing into the committed tree while they ran

**WHAT.**
- **The authority.** The operator asked coordinator B why every PR waits about 15 minutes for
  `gate`. B's brief to this session: make the gate faster without weakening it; every test that
  runs today must still run.
- **The plugin.** `pytest-xdist>=3.8` joins `.[dev]` in `pyproject.toml`. `requirements.lock` is
  regenerated in place by the command in its header (uv 0.13.8), the #1049 rule. It gains
  `pytest-xdist==3.8.0` and its one dependency `execnet==2.1.2`, with hashes, and no other pin
  moves (+10 lines). It still regenerates byte for byte, offline.
- **The gate.** `gate.yml`'s pytest step adds `-n auto`: one worker per core of the runner,
  so 4 on `ubuntu-latest`. Every other flag is unchanged.
- **The other gates stay on one process.** `bin/commit` runs in the shared venv. Agents may not
  reinstall it (STATE row 62), and it has no pytest-xdist until it is re-synced from the lock. The
  scheduled workflows' own gates (`weekly-screen`, `monthly-score`, `theme-intelligence-weekly`)
  are left as they were, since the brief named `gate.yml`.
  - `tests/test_one_gate.py` required every gate to carry each of gate.yml's flags. `-n` is now a
    scheduling flag that gate.yml carries and the others may leave out (`_SCHEDULING`). A new pin
    shows that a gate dropping `-rs`, `-p no:warnings` or `-m "not network"` is still caught.
    Main's version of the test fails against the new gate.yml, naming the three workflows and
    `bin/commit` as lacking `-n auto`.
- **Four tests stopped writing into the checkout.** Each wrote into the committed tree while it
  ran and restored it after, so git stayed clean and one process never noticed. On several
  workers, a test reading the same files at the same moment on another worker could catch them
  missing, empty, or carrying something uncommitted:

  | test | what it wrote | now |
  |---|---|---|
  | `test_scenarios.py::test_emit_scenarios_is_deterministic` | removed `frontend/scenarios/` and wrote its 14 files again | emits into its own folder (`OUT_SCEN` patched) and compares that with the committed mirror byte for byte |
  | `test_quantity_kind_guard.py::test_the_stamps_round_trip_and_an_unstamped_fact_emits_no_key` | rewrote `scenarios/SMPL.json`, which dozens of tests read | `write_record(root=tmp_path)`, same byte comparison |
  | `test_known_wrong_marker.py`: the two tests that drop a marker | put `known_wrong.json` beside AMZN's committed dossier, sealing it for as long as the test took | the marker is in a dossiers root of the test's own, passed as `dossiers_root=`, as every production render passes it |
  | `test_cohort_anchoring.py::test_the_falsifier_can_actually_fire` | planted 12 empty `data/dossiers/<T>/dossier.json` | runs a copy of the script in a checkout of its own: every entry linked in, the 12 added there |

  Each still fails where it should. Run against a checkout with no names added, the falsifier test
  fails on its own assertion ("did NOT trip the falsifier"). Rendered without its root, the marker
  test fails "the marker did not reach the rendered page".

**WHY.**
- **Where the gate's time went.** The pytest step took 758 to 1,416 s on ten successful gate runs
  of 2026-11-13, a median of 1,081 s. Install took 15 to 21 s, mypy 12 to 27 s, ruff about 0 s.
- **Where pytest's time goes.** Measured on one process locally (Apple M-series), at main
  `6a5a28f5`, in a venv installed from the lock. 11,952 tests summed 736 s, inside 760 s of wall
  time.
  - **Most of it is CPU.** user 586 s plus sys 100 s of 766 s wall, for the pytest process and
    the children it waited on together (`/usr/bin/time`). The run is compute-bound, not waiting,
    so it divides across cores.
  - **No few tests to fix.** The slowest is 28.7 s
    (`test_footnote_every_figure.py::test_the_gd6_draw_is_caught_the_same_with_each_figure_footnoted`).
    The slowest 40 tests sum 234 s (31.5%), and the 128 tests over 1 s sum 363 s (49%).
    The slowest file, `test_footnote_every_figure.py`, takes 77 s (10.4%).
  - **Child processes: 225 s (30.6%), in 691 tests**, timed per test by a measuring plugin over
    `subprocess.Popen`.
    - `python` children: 99.7 s, 243 of them, in 86 tests;
    - `git`: 93.3 s, 5,077 calls, in 521 tests;
    - `node`: 11.4 s, 165 calls, in 134 tests;
    - LibreOffice 9.4 s and Brave 4.1 s, in four tests. In gate run 43424477388's log (main
      `6a5a28f5`), three of the four skip on CI: the two Brave tests ("needs a headless Chromium")
      and `test_vote_rule_confirmation.py:173`, the 8.8 s one ("no licensed CIQ folder"). That
      run counted 11,270 passed and 671 skipped, against 11,274 and 667 here.
  - **Committed artifacts: 3,174 tests (255 s, 34.7%) open a file under `data/`, `frontend/`,
    `scenarios/`, `docs/` or another committed area** (the same plugin over `open`).
    `data/dossiers/` alone is read by 1,426 tests summing 158.5 s. These tests overlap the
    child-process ones, so the two shares do not add.
- **So the gain is in spreading the suite, not trimming it.** Two thirds of the time is a long
  tail of ordinary tests; no handful of slow ones accounts for it.
- **The theme desk's share** (coordinator B asked for it; nothing was removed). At the serial run
  of `35c35cd6`'s tree, the 73 files `tests/test_theme_intelligence*.py` hold 27,236 lines
  (27,826 with `tests/theme_intelligence_support.py` and `_stress.py`) of 173,318 in
  `tests/*.py`. They hold **1,468 of 12,066 tests (12.2%)**, 1,463 passing and 5 skipped, and
  **101 s of the 722 s summed (13.9%)**. The slowest three files are `_upload` 17.7 s,
  `_older_pages` 13.9 s and `_desk` 12.9 s.
- **Tests for retired features** (coordinator B, for the operator's question). Searched:
  - every module the code retirements deleted from `vinci/`, `scripts/` and `frontend/`: R1 #905,
    R2 #908, R3 #910, `vinci/ciq` (a71b9f67), the three uncalled modules (5649a650), and the two
    refresh scripts (#746). That is 20 dotted module names, `from … import` forms and file paths,
    over the 511 `tests/*.py` files.
  - **No test exercises deleted code.** Ten files mention one. Each mention is a history comment or
    a pin that the module is gone: `test_retired_modules`, `test_vinci_ciq_removed`,
    `test_scripts_call_current_signatures`.
  - **One test pins live code for a retired caller.**
    `test_submissions_memo.py::test_the_memo_survives_concurrent_use_of_one_client`, and the lock
    it pins in `vinci/edgar/client.py:547`, both give `vinci/themes/exposure.py` (deleted in R2)
    as the caller that shares one `EdgarClient` across threads. None was found now. Of the five
    `ThreadPoolExecutor` users in `vinci/` and `scripts/`, the dossier cohort builds a client per
    call. The lock still guards the client; only its stated reason is stale.
  - **Retired names.** AORT (2026-11-09) and MVST (2026-11-13) have no committed page.
    - 30 test ids name AORT: 25 pass on frozen pages, 5 skip.
    - 31 name MVST: 27 pass, 4 skip.
    - The skips wait for a CIQ bundle (`test_consensus_rows`, `test_consensus_parity`,
      `test_guidance_metric_coverage`, `test_no_backfill`). MVST's record says its CIQ folder is
      gone, so its CIQ-keyed cases can no longer run on any machine. AORT's record does not say:
      unverified.

**HOW VERIFIED.**
- **Serial against parallel, test by test.** Each run wrote a junit file, compared by test id and
  outcome (passed, skipped, xfailed, failed).
  - At `35c35cd6` (main `81f97600` plus this change's first commit), one process:
    **11,388 passed, 667 skipped, 11 xfailed** in 740 s.
  - Four parallel runs of the same tree, every one **11,388 passed, 667 skipped, 11 xfailed**,
    the same test ids with the same outcomes as the serial run and as each other:

    | run | wall |
    |---|---|
    | `-n 4` | 296 s |
    | `-n 4 --dist worksteal` | 366 s |
    | `-n auto` (8 here) | 491 s |
    | `-n auto` again | 291 s |

    The Mac was shared with other sessions' runs (load average 16 to 23 on 4 performance and 4
    efficiency cores), which is why the walls spread and why CI chose the worker count.
    Work-stealing was no faster, so the default distribution stays.
  - `625f8ebb` then changed `test_cohort_anchoring.py`'s helper (pre-PR review). At `25399521`,
    with this record and the STATE line added, one `-n auto` run gave **11,389 passed, 667
    skipped, 11 xfailed**. The one new test id is `test_record_hygiene`'s case for this record;
    every other id has the serial run's outcome.
  - At main `6a5a28f5`, before these fixes: two runs on one process, in the shared venv
    (anthropic 0.112.0) and in the lock venv (2.6.0), and one at `-n 8`. All three gave
    11,274 passed, 667 skipped, 11 xfailed, every test the same.
- **What the four tests wrote, and that nothing writes now.** A finding plugin logged every write
  a test made inside the checkout: `open` in a write mode, `os.replace`/`rename`/`unlink`/`mkdir`
  and `shutil` copies and removals. Its run at `-n 8`, on `6a5a28f5`, found the four above. Two
  findings were noise: `shutil.rmtree`'s directory-relative unlinks of temporary folders, and an
  unlink of a symlink in `test_snapshot_vintage.py`'s own staged copy, read through to its target.
  - A file-time check finds what a child process writes, which the plugin cannot see. After every
    run (serial or parallel, of either tree) no file in the checkout outside the caches is newer
    than the run's start. Before the fixes, `scenarios/SMPL.json` and the 14 `frontend/scenarios/`
    files were.
  - Outside the checkout: the SEC pace file is already one per worker (`tests/conftest.py` puts it
    in the worker's own basetemp). `~/.cache/vinci` was not touched by any run.
- **The gate on CI, before and after.** The runners are noisy: on one day the same suite took
  752 to 1,469 s on one process (coordinator B saw slow runs cluster when about six gate runs
  overlapped). So one run proves nothing, and the comparison controls for the runner.
  - **The control is the mypy step**, single-process CPU work on the same machine just before
    pytest. Across the 59 one-process runs it tracks the pytest step at correlation 0.95, and
    pytest takes 49.9 to 80.9 times mypy's time (median 61.8).

  | | runs | pytest step | job | pytest ÷ mypy |
  |---|---|---|---|---|
  | before, one process | 59 | median 1,114 s (752–1,469) | median 1,163 s | median 61.8 |
  | after, `-n auto` | 4 | median 584 s (508–658) | median 637 s (558–717) | 26.2–27.4 |

  - **Matched on runner speed:**
    - where mypy took 18–20 s, 8 runs before had a pytest median of 1,116 s, and 2 after took
      508 and 511 s: **2.19×**;
    - where mypy took 23–26 s, 10 runs before had a median of 1,338 s, and 2 after took 656 and
      658 s: **2.04×**.

    About 2.1×, then, against the 2.5× four workers gave locally. The hosted runner reports four
    CPUs to `-n auto`, but it does not divide CPU-bound work four ways.
  - **The counts.** Main's own gate at the base (run 43431894009, `81f97600`, one process) gave
    11,383 passed, 671 skipped, 11 xfailed. All four runs here gave **11,385 passed, 671
    skipped, 11 xfailed**: the two more are the two tests this change adds
    (`test_only_the_worker_count_is_left_to_each_gate` and this record's hygiene case). The 298
    skip lines are identical in the base run and the PR's.
  - **The after-runs:** 43442158133 at `25399521`, then 43446418963 at `c5b11680`, run three
    times one after another (attempts 1 to 3), each starting once the last had finished.
- **The lock.** `tests/test_dependency_lock.py` passes, the uv regeneration pin included
  (`VINCI_UV` set, `--offline`): the lock regenerates byte for byte in place.

**BOUNDARY.**
- **CI before:** WHY's 758–1,416 s is the ten successful `gate` runs between 11:22 and 12:28 UTC
  on 2026-11-13 (jobs 131855811772 to 131885693149). The before-and-after table uses every
  successful `gate` run `gh run list --workflow gate.yml --status success --limit 60` returned
  apart from this PR's: 59 runs, created 04:14 to 13:48 UTC on 2026-11-13, PR and push heads alike.
  All times are the step times GitHub reports for each job.
- **CI after:** the four runs named above, 14:23 to 15:21 UTC on 2026-11-13, the only gate runs
  of this PR to complete (the one at `625f8ebb` was cancelled by the next push).
- **Local timings:** one Mac, 8 cores (4 performance, 4 efficiency), shared with other sessions,
  wall time from `/usr/bin/time`. They place the time; CI measures the gain.
- **Counts:** `pytest -m "not network"`, every file under `tests/`; 39 network tests deselected
  in each run. At `6a5a28f5` 11,952 outcomes; at `35c35cd6` 12,066; at `25399521` 12,067.
- **The breakdown's shares** are of summed per-test time (setup, call and teardown) at
  `6a5a28f5`, from one serial run.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **ACCEPTED RISK: a new test that writes into the committed tree.** The next test of that shape
  passes on one process and may fail at random on four. Nothing refuses it at write time: a
  whole-suite check comparing file times would also fire on any file a person edits during the
  run. The finding plugin above is how the four were found, and it can be run again.
  - **The falsifier:** a gate failure, on a single run, in a test that reads a committed path,
    that a re-run passes.
- **`bin/commit` stays on one process** (about 13 minutes locally) until the shared venv carries
  pytest-xdist. After the row 62 re-sync, adding `-n auto` to `bin/commit` is its own change.
- **A failure's log names its worker** (`[gw2]`): a test that fails on CI and passes locally may
  have shared a worker with a test that left state behind, which the per-test comparison above
  rules out for today's suite only.
