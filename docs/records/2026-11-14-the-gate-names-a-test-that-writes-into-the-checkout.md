---
status: shipped
date: 2026-11-14
prs: [1071]
supersedes:
superseded-by:
---

# The gate fails, by name, on any file the tests write into the checkout, which closes most of #1065's accepted risk, and a run on workers prints its deselected count again

**WHAT.**
- **The authority.** Coordinator B checked #1065 independently and briefed this session to close
  the two gaps it left: the accepted risk of a test that writes into the committed tree, and the
  deselected count the summary line lost on workers. Both changes stay inside gate.yml's existing
  pytest flags.
- **The guard, three steps in `gate.yml`.**
  - `mark the time before the tests`: `touch "$RUNNER_TEMP/before-the-tests"`, outside the
    checkout.
  - `pytest (offline)`: unchanged but for `id: pytest`.
  - `the tests wrote no file into the checkout`: runs whenever the pytest step ran, passed or
    failed. It lists every file, not directory, newer than the mark outside `.git/`,
    `.pytest_cache`, `.hypothesis` and every `__pycache__`. Any file listed fails the job, by
    name. It also fails if nothing at all is newer than the mark, not even the bytecode every
    run writes, since then the check cannot see the run. Otherwise it prints how many files it
    saw and that every one is in a cache.
  - `git status --porcelain` would not do: a test that restores a file byte for byte leaves git
    clean, and that is the shape #1065 accepted.
  - **CI only.** On a person's machine a file they edit during the run would trip it, which is
    why #1065 deferred a whole-run check. `bin/commit` has no such step.
- **The deselected count, in `tests/conftest.py`.** Each worker keeps the ids `pytest_deselected`
  hands it and, once its collection is done, sends them in xdist's `workeroutput`. The controller
  keeps what each worker sent (`pytest_testnodedown`) and prints the count on the line above the
  summary line: `39 deselected (-m "not network"), the same 39 on each of the 4 workers`.
  - A worker that sent nothing (one that died) makes it `deselected: UNKNOWN (gw0 39, gw1 sent
    none, …)`. An unknown count is never printed as a number.
  - **Beside the summary line, not in it.** The first cut put the ids into the terminal reporter's
    `stats`, so the line would read exactly as on one process. Hypothesis's own terminal-summary
    hook reads `__dict__` from every entry there, and the run ended in `AttributeError: 'str'
    object has no attribute '__dict__'`.
  - On one process nothing changes: the hooks send nothing, and pytest prints `39 deselected` in
    the summary line as before.
- **`bin/commit` and the three scheduled workflows stay on one process.** The shared venv still
  has no pytest-xdist (`import xdist` raises ModuleNotFoundError; `pip show pytest-xdist` finds
  nothing), and agents may not reinstall it (STATE row 62). `tests/test_one_gate.py` is unchanged
  and green.
- **The pins, `tests/test_gate_on_workers.py`.** Each reads gate.yml, or loads the conftest's
  hooks, so it follows the code it pins.
  - The deselected count: on two workers the line names the 2 a probe suite deselects, with `-k`
    beside `-m` when both are given; the same suite on one process counts them once, in the
    summary line. Without the hooks no count is printed (the shape of #1065's log). A worker
    killed mid-run (`os._exit`) makes the count UNKNOWN.
  - The guard, gate.yml's own step script run as GitHub runs a step that names no `shell:`
    (`bash -e`, no pipefail) in a scratch git checkout: a committed file written back byte for
    byte trips it while `git status --porcelain` is empty; a new file beside a dossier trips it;
    the three caches and `.git/` pass; a mark that sees nothing is refused; a folder the guard
    cannot read fails the step rather than passing it. A sixth pin keeps the mark just before the
    tests and the guard just after them, before the mirror build, which rewrites `frontend/` by
    design.
  - **The pre-PR review's one fix.** The guard pipes `find` into `sort` and `wc`, and GitHub runs
    a step with no `shell:` under `bash -e` without pipefail. A `find` that failed part-way, on a
    folder it could not read, handed its partial list on and the step passed green over a file it
    never saw. The unreadable-folder pin failed so (exit 0, "4 files are newer than the mark,
    every one in…" beside `find: ./data/locked: Permission denied`); the step now opens with
    `set -euo pipefail`, and the pin passes.
  - **Seven mutants, seven caught.** Each pin set was run against a mutant of the code it pins,
    each turning at least one pin red: the guard reading `git status` instead of file times;
    `scenarios/` left out as if it were a cache; the blindness check removed; the guard step
    renamed away; `set -euo pipefail` removed; a worker never sending its ids; a worker that sent
    none counted as agreeing.

**WHY.**
- **The cache list is measured, not guessed.** A real run of the suite, in a clean clone of
  #1065's head `b81d8d6a` (committed files only, no CIQ data, no `.env`) and through the same
  steps as gate.yml (ruff, mypy, the mark, pytest `-n 4`), left 968 files newer than the mark:
  750 in `__pycache__` folders, 214 in `.hypothesis`, 4 in `.pytest_cache`, and none anywhere
  else. The brief also named `.mypy_cache` and `.ruff_cache`. Their steps write them before the
  mark, and the suite writes neither, so they stay inside the check: a test that ran ruff or mypy
  into them would be named.
  - The first such run was not faithful. This machine's shell sets `PYTHONDONTWRITEBYTECODE`,
    which CI does not, so it wrote no bytecode for the tests. It is not counted; the run above
    unset it.
- **Files, not directories.** A directory's time moves whenever an entry is made in it, and the
  run makes many. In the real run below, 28 directories outside the caches were newer than the
  mark: 24 that gained a `__pycache__` (`tests/`, `scripts/`, `frontend/`, `vinci/` and its
  packages among them), the root, which gained `.pytest_cache` and `.hypothesis`, and `data/`,
  `data/cache` and an empty `data/cache/sec`, made during the run. So a directory check would
  trip on every run. Which test makes `data/cache/sec` was not found: the eleven
  `tests/test_quality_*.py` files, run one by one in a clean clone, do not. It holds no file, so
  the guard has nothing to name.

**HOW VERIFIED.**
- **The guard fails on a planted write and passes on the real suite.** Both runs used gate.yml's
  own three step scripts, read out of gate.yml by the pin's helper, in a clean clone at
  `4386c830` (this change on #1065's head), with the caches cleared first, as on a fresh runner.
  They ran under `bash -eo pipefail`, before the review moved `set -euo pipefail` into the step
  itself; no `find` failed in either run, so neither outcome depends on it.
  - **Planted.** One added test read `scenarios/SMPL.json`, wrote it empty, and wrote the
    original bytes back. pytest passed (11,395 passed, 670 skipped, 11 xfailed: the race did not
    fire this time, which is the point), and `git status --porcelain` was empty after it. The
    guard failed:

    ```
    ::error::the tests wrote 1 file(s) into the checkout: on workers, another test can read one mid-write
    ./scenarios/SMPL.json
    ```
  - **Real.** The same clone without the planted test: 11,394 passed, 670 skipped, 11 xfailed,
    and the guard passed:

    ```
    968 files are newer than the mark, every one in .pytest_cache, .hypothesis or a __pycache__
    ```
- **The deselected count, on a real run.** Both runs above printed the same count; the real one
  ended:

  ```
  39 deselected (-m "not network"), the same 39 on each of the 8 workers
  11394 passed, 670 skipped, 11 xfailed in 256.82s (0:04:16)
  ```

  The 39 are main's serial count (gate run 43571490422 at `0f5e3eb2`: `11393 passed, 671
  skipped, 39 deselected, 11 xfailed`). #1065's parallel run 43454365815 printed no count.
- **The pins and the mutants**, above. The six guard pins and the one-process pin run in the
  shared venv too; the three that start workers skip there ("could not import 'xdist'") and run
  on CI, which installs the lock.

**BOUNDARY.**
- **The cache measurement (968 files: 750, 214, 4):** files, not directories, newer than the
  mark outside `.git/`, after `pytest -m "not network" -p no:warnings --tb=short -rs -n 4` over
  every file under `tests/`, in a clean clone of `b81d8d6a` with no git-ignored file, on one Mac,
  2026-11-14. The real run at `4386c830` (`-n auto`, 8 workers) gave the same 968, split the
  same way.
- **Test counts** are of `-m "not network"` over `tests/` in that clone. They are not CI's: the
  two machines have different tools installed, and 670 skipped here against 671 in main's CI
  run 43571490422.
- **Directories (28):** outside `.git/` and the three caches, newer than the mark, in the real
  run at `4386c830`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **#1065's accepted risk is narrowed, not closed.** What the guard cannot see:
  - **A file a test creates in the tree and deletes before the run ends** leaves no newer file.
    That was the shape of one of #1065's four (`test_cohort_anchoring.py` planted 12 dossiers),
    and a directory check cannot see it either, for the reason in WHY.
  - **A write outside the checkout** (the user's cache, a shared temp file).
  - **Which test wrote.** The guard names the file, not the test. #1065's record describes the
    finding plugin that logs every write a test makes; it is not committed, and finding the test
    means running it again or reading the tests that touch the named path.
  - **The falsifier** is #1065's, narrowed: a gate failure, on a single run, in a test that reads
    a committed path, that a re-run passes, while this guard is green.
- **A guard red is not always a bug.** A test that is meant to write into the tree, a new cache
  a new tool writes, would trip it. Either the test moves into its own folder, as #1065's four
  did, or the path joins the left-out list with its measurement, in this step and in its pin.
- **Local runs keep the risk.** `bin/commit` stays on one process and has no guard, so a writing
  test passes it every time and fails only on CI. That is where it is now caught.
