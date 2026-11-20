---
status: shipped
date: 2026-11-20
prs: [1160]
supersedes:
superseded-by:
---

# `bin/commit` runs the offline suite on pytest-xdist workers (`-n auto`), on one process with one loud warning when its venv lacks pytest-xdist, and its log states its outcome counts again (operator: "Approve bin/commit + gate.yml comment (Recommended)")

**WHAT.**
- **The authority.**
  - Coordinator B's brief, W83 step 2: `bin/commit` runs the full suite with `-n auto`; without
    pytest-xdist it runs serially and says so; the totals line comes back; the stale claims are
    corrected; verified on real runs.
  - `bin/commit` and `.github/workflows/` are protected. The operator answered in this session's
    chat, 2026-11-20: "Approve bin/commit + gate.yml comment (Recommended)". Both commits' messages
    carry the `Operator-approved:` lines.
- **`bin/commit`'s pytest step:**
  - it asks the venv `"$VENV" -c 'import xdist'`;
  - on success it runs gate.yml's line, `-n auto` included:
    `"$VENV" -m pytest -m "not network" -p no:warnings --tb=short -rs -n auto`;
  - otherwise it prints one line to stderr, `── WARNING: pytest-xdist is not importable in $VENV:
    the suite runs on ONE process, 2-3x slower; re-sync the venv from requirements.lock ──`, and
    runs the same line without `-n`. It warns and never refuses, as the fast gate has done since
    #1086 (RH-D2);
  - the two branches are explicit lines, not a flag array: `bin/commit` runs under `/bin/bash`
    3.2 on this Mac, which errors on an empty `"${arr[@]}"` under `set -u`, and
    `tests/test_one_gate.py` reads each pytest line for its flags.
- **The totals line.** The old line added `-q` to addopts' `-q`, which makes `-qq`, and `-qq`
  prints no totals line. On a two-test probe under the repository's addopts, the old line printed
  only `..`; the new line prints `2 passed in …`. The new gate's log of this change's own commit
  ends `12692 passed, 667 skipped, 7 xfailed in 1478.83s`.
- **gate.yml:** comment only. It said `bin/commit` leaves `-n` out because the shared venv has no
  pytest-xdist. It now says `bin/commit` runs it when its venv imports pytest-xdist.
- **The stale claims, corrected:**
  - STATE row 65 said "The shared venv still has no pytest-xdist, so it does not match the whole
    lock". The venv has carried pytest-xdist 3.8.0 since 2026-11-16, its dist-info's date. On
    2026-11-20 it held 52 of the lock's 54 pins at the lock's version; the other two (colorama,
    httpx2-jsfetch) are marked Windows- and Emscripten-only;
  - STATE's 2026-11-13 gate claim said "`bin/commit` stays on one process until the row 62
    re-sync";
  - `tests/test_one_gate.py`'s `_SCHEDULING` comment (:33–35) and
    `tests/test_gate_on_workers.py:97` said the venv has no pytest-xdist.
- **The pins,** in `tests/test_one_gate.py`, each driving the real `bin/commit` in a scratch
  checkout through a stand-in interpreter unless stated:
  - the interpreter test expects the probe before pytest;
  - with xdist, pytest gets `-n auto` and nothing warns;
  - without it, pytest gets no `-n`, exactly one WARNING line names pytest-xdist and ONE process,
    and the commit still happens;
  - a red suite commits nothing, on either branch;
  - `bin/commit` has one pytest line on workers and one on one process;
  - each of those two lines, run as written by the real interpreter on a two-test suite under the
    repository's own addopts, ends with `2 passed in …`. The workers case skips, with its reason,
    on a venv without pytest-xdist, so the fallback gate stays green there.

**WHY.**
- **Speed.** The serial gate took about 17 minutes on a quiet Mac and about 30 under load, run
  1–3 times per PR. The measurement of 2026-11-19 (main `ac3c9479`, 13,172 ids, 4 parallel runs)
  found every outcome the same at `-n auto` and 2.0–3.1x the speed. #1153 fixed the hazards its
  write audit named.
- **A gate whose log cannot say what passed** is a gate the reader takes on trust. `bin/commit`
  has carried `-q` since its first commit (`54908953`, 2026-08-03), and addopts has carried `-q`
  since 2026-06-17 (`17911206`), so the gate never printed a totals line; only its exit status
  said green.
- **Warn, never refuse.** A machine whose venv lacks pytest-xdist must still be able to commit,
  and one may: whether B's Mac's venv has it is stated nowhere, and on 2026-11-16 its checkout had
  no `requirements.lock` (STATE row 65). A refusal there would push the next session to work
  around the gate.

**HOW VERIFIED.**
- **The pins were red first.** On the old `bin/commit`, 6 of the new or changed pins failed: the
  interpreter test, the workers test, the fallback test, the two-lines test, and both totals
  cases. The totals case's output was `..` alone.
- **The red-suite pin was mutation-tested.** A copy of the new `bin/commit` with `|| true` on both
  pytest lines committed a red suite (exit 0, two commits). The pin failed on it on both branches
  and passes on the real script.
- **Old gate against new gate, on one tree (`6d19d565`):**

  | gate | how the suite ran | outcomes (junit) | the log's totals line | gate wall | load1, start → end |
  |---|---|---|---|---|---|
  | main's `bin/commit` | one process | 12,685 passed, 668 skipped, 7 xfailed, 6 failed | none (0 lines) | 3,189 s | 13.5 → 8.6 |
  | the new `bin/commit` | 8 workers | 12,692 passed, 667 skipped, 7 xfailed | `12692 passed, 667 skipped, 7 xfailed in 1478.83s` | 1,499 s | 14.2 → 14.9 |

  - **Speed:** 2.13x, with the new gate under the heavier load (its 5-minute average was 18.8–22.9
    against the old run's 9.3–17.8), so the ratio is conservative.
  - **Outcomes:** both runs hold the same 13,366 ids, and 13,359 have the same outcome. The 7 that
    differ:
    - 6 are this change's own pins, which read `bin/commit` itself. They fail under main's script
      by design, and that is why the old gate exited 1;
    - 1 is `test_vote_rule_confirmation.py::test_the_transcripts_are_read_as_the_replay_harness_reads_them`,
      skipped in the old run and passed in the new. It finds the licensed CIQ folder at
      `ROOT.parents[2]`. The link I made for the scratch worktree sat one level below that. With
      the link moved there, the same test passed in the old worktree (1 passed, 34.85 s): the
      difference is setup, not the gate.
- **The fallback, on a real venv without pytest-xdist:**
  - the venv was a copy of the shared venv with `xdist/` and its dist-info removed:
    `import xdist` fails, and pytest 9.1.1, ruff and mypy import;
  - the new `bin/commit` ran in the scratch worktree, `VENV=<that copy>`,
    `PYTEST_ADDOPTS="-k test_one_gate"` to keep the run short, and `--dry-run --allow-empty`;
  - it printed `── WARNING: pytest-xdist is not importable in <the copy>: the suite runs on ONE
    process, 2-3x slower; re-sync the venv from requirements.lock ──`, ran on one process,
    and ended `13 passed, 1 skipped, 13391 deselected in 61.09s`. The skip is the workers totals
    case, with its reason. Then `gate green; committing`, exit 0, in 72 s.
- **What the fallback run found.** Its first attempt failed one test. The one-process totals
  case's child pytest inherited the caller's `PYTEST_ADDOPTS="-k test_one_gate"`, deselected its
  two tests, and exited 5. The child now runs without `PYTEST_ADDOPTS`: the pin measures the
  command as written. Under that environment the committed `6d19d565` test file gives 2 failed,
  and the fixed file 2 passed. The second attempt is the run above.

**BOUNDARY.**
- **Tree:** `6d19d565` (this change's code commit) on main `4db3d85a`. The old gate ran in a
  detached scratch worktree of that commit with main's `bin/commit` staged in place of the new
  one, never committed (`--dry-run`).
- **Data:** both worktrees held the same ignored data (`data/cache`, `frontend/snapshots`, the
  `.env` link) and no `data/manual`. The licensed CIQ folder sat at `ROOT.parents[2]` from the
  new gate's worktree, and one level below that from the old gate's (the one differing id above).
- **Machine:** the shared Mac (Apple M3, 8 cores), the primary `.venv` (Python 3.12.13, pytest
  9.1.1, pytest-xdist 3.8.0), `/bin/bash` 3.2.57. Other sessions' suites were running throughout;
  loads are stated per run.
- **Junit:** passed to each gate through `PYTEST_ADDOPTS=--junitxml=…`, which leaves the script's
  own command unchanged.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **CPU.** At `-n auto` a run uses about 1.7x the serial run's CPU (the 2026-11-19 measurement:
  2,206–2,400 CPU-s against 1,344), and 8 workers repeat collection. On a Mac shared by several
  sessions, `PYTEST_XDIST_AUTO_NUM_WORKERS` (xdist `plugin.py:17`) caps `-n auto` per machine
  without editing the script.
- **`tests/test_sec_pacing.py:249`** times 4 real processes on the wall clock and has flaked under
  load, serially and on workers. More workers means more load, so expect it now and then on this
  gate too. It is not shared state, and widening it would weaken it (#1153's brief).
- **ACCEPTED RISK: a venv where `import xdist` succeeds but the plugin is not loaded**
  (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, or `-p no:xdist` in `PYTEST_ADDOPTS`). The gate then runs
  `-n auto` and pytest exits 4 on the unknown option: it fails loud rather than falling back. No
  gate sets either.
  - **Falsifier:** a `bin/commit` run that stops with "unrecognized arguments: -n" on a venv that
    has pytest-xdist installed.
- **The scheduled workflows' gates** (weekly-screen, monthly-score, theme-intelligence-weekly)
  still run on one process. That is outside the brief, and they run outside the PR loop.
