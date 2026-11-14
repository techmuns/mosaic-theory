"""WHAT RUNNING ON WORKERS TOOK FROM THE GATE, PUT BACK (2026-11-14, after #1065).

#1065 runs gate.yml's pytest step on the runner's cores (`-n auto`, pytest-xdist). Two things went
with the single process:

* THE DESELECTED COUNT. On one process the summary line reads "11393 passed, 671 skipped,
  39 deselected, 11 xfailed" (main's gate run 43571490422 at 0f5e3eb2); on workers it read
  "11393 passed, 671 skipped, 11 xfailed" (#1065's run 43454365815): the controller collects
  nothing, so it never sees what `-m "not network"` left out. `tests/conftest.py` has each worker
  send its deselected ids back and the controller print the count above the summary line.
* A TEST THAT WRITES INTO THE CHECKOUT. One that writes a committed file and restores it passes on
  one process and can fail at random on workers, where another test reads the file mid-write.
  #1065 accepted that risk. git cannot see it — a restored file leaves `git status` clean — so
  gate.yml marks the time before the tests and fails if any file outside `.git/` and the caches
  is newer after them. CI only: on a person's machine, a file they edit during the run would trip
  it too.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE_YML = ROOT / ".github" / "workflows" / "gate.yml"

_INI = "[pytest]\nmarkers =\n    network: a live test\n"
_TESTS = '''\
import pytest

def test_offline():
    pass

def test_offline_too():
    pass

@pytest.mark.network
def test_live():
    pass

@pytest.mark.network
def test_live_too():
    pass

@pytest.mark.skip(reason="a stated reason")
def test_skipped():
    pass
'''
#: The conftest's four deselected-count hooks, and nothing else from it.
_HOOKS = ("from tests.conftest import (pytest_collection_finish, pytest_deselected,  # noqa: F401\n"
          "                            pytest_terminal_summary, pytest_testnodedown)\n")


def _suite(tmp_path: Path, *, hooks: bool, tests: str = _TESTS) -> Path:
    suite = tmp_path / "suite"
    suite.mkdir()
    (suite / "pytest.ini").write_text(_INI)
    (suite / "test_probe.py").write_text(tests)
    if hooks:
        (suite / "conftest.py").write_text(_HOOKS)
    return suite


def _tail(suite: Path, *workers: str, exit_code: int = 0) -> list[str]:
    """The last two lines of a run with the gate's selection, as its log prints them, less the
    run's duration."""
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", "-m",
         "not network", *workers], cwd=suite, capture_output=True, text=True, timeout=120,
        env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert out.returncode == exit_code, out.stdout + out.stderr
    return [re.sub(r" in \d+\.\d+s( \([\d:]+\))?$", "", line)
            for line in out.stdout.splitlines()[-2:]]


def test_a_run_on_workers_states_what_the_selection_left_out(tmp_path: Path) -> None:
    """POSITIVE: on two workers the log states the 2 tests `-m "not network"` deselected, on the
    line above a summary line otherwise the same as one process's."""
    pytest.importorskip("xdist")
    suite = _suite(tmp_path, hooks=True)
    assert _tail(suite, "-n", "2") == [
        '2 deselected (-m "not network"), the same 2 on each of the 2 workers',
        "2 passed, 1 skipped"]
    # A `-k` beside the `-m` is named too, so the count is never credited to `-m` alone.
    assert _tail(suite, "-k", "not too", "-n", "2") == [
        '3 deselected (-m "not network", -k "not too"), the same 3 on each of the 2 workers',
        "1 passed, 1 skipped"]


def test_on_one_process_the_hooks_change_nothing(tmp_path: Path) -> None:
    """NEGATIVE: on one process (`bin/commit`, which has no pytest-xdist) the hooks send nothing
    and print nothing; pytest counts the 2 once, in the summary line, as it always has."""
    tail = _tail(_suite(tmp_path, hooks=True))
    assert tail[-1] == "2 passed, 1 skipped, 2 deselected", tail
    assert not any("workers" in line for line in tail), tail


def test_without_the_hooks_a_run_on_workers_drops_the_count(tmp_path: Path) -> None:
    """NEGATIVE: the same run without the conftest's hooks prints no deselected count at all —
    the shape #1065's gate log took, which the pin above would refuse."""
    pytest.importorskip("xdist")
    suite = _suite(tmp_path, hooks=False)
    assert not any("deselected" in line for line in _tail(suite, "-n", "2"))


def test_a_worker_that_sent_no_count_makes_it_unknown_never_a_number(tmp_path: Path) -> None:
    """NEGATIVE: a worker that dies mid-run sends nothing back, so the count is stated UNKNOWN,
    with what each worker sent — never the other workers' count passed off as the run's."""
    pytest.importorskip("xdist")
    crash = _TESTS + "\n\ndef test_the_worker_dies():\n    import os\n    os._exit(3)\n"
    tail = _tail(_suite(tmp_path, hooks=True, tests=crash), "-n", "2", exit_code=1)
    assert tail[0].startswith("deselected: UNKNOWN (") and "sent none" in tail[0], tail


# ── THE GUARD ON WRITES INTO THE CHECKOUT ─────────────────────────────────────────────────────

_MARK = "mark the time before the tests"
_GUARD = "the tests wrote no file into the checkout"


def _step_names() -> list[str]:
    return [line.strip().removeprefix("- name:").strip()
            for line in GATE_YML.read_text().splitlines() if line.strip().startswith("- name:")]


def _step_script(name: str) -> str:
    """The shell a gate.yml step runs, read from gate.yml so the pin follows it: a one-line
    `run:` or the block under `run: |`, dedented."""
    lines = GATE_YML.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f"- name: {name}")
    for i in range(start + 1, len(lines)):
        text = lines[i].strip()
        if text.startswith("- name:"):
            break
        if text.startswith("run:"):
            if text != "run: |":
                return text.removeprefix("run:").strip() + "\n"
            indent = len(lines[i]) - len(lines[i].lstrip())
            block = []
            for line in lines[i + 1:]:
                if line.strip() and len(line) - len(line.lstrip()) <= indent:
                    break
                block.append(line)
            depth = min(len(b) - len(b.lstrip()) for b in block if b.strip())
            return "\n".join(b[depth:] for b in block).rstrip() + "\n"
    raise AssertionError(f"gate.yml step {name!r} runs nothing")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
                           *args], capture_output=True, text=True, check=True).stdout


def _wait_past(ns: int, probe: Path) -> None:
    """Wait until a file written now carries a status time later than ``ns``: past the clock's
    granularity, which on Linux is a kernel tick. The fixture never backdates with `os.utime`,
    because a utime moves the status time (`ctime`) the guard reads."""
    deadline = time.monotonic() + 10
    while True:
        probe.write_bytes(b"")
        if probe.stat().st_ctime_ns > ns:
            return
        assert time.monotonic() < deadline, "the clock did not move in 10 s"
        time.sleep(0.005)


def _checkout(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """A git checkout with committed files and gate.yml's mark taken by gate.yml's own step, after
    the clock has moved past every file the checkout holds; then the clock moves past the mark
    too, so what the "run" writes next is after it."""
    repo = tmp_path / "checkout"
    for rel in ("scenarios/SMPL.json", "data/dossiers/AMZN/dossier.json", "tests/test_x.py"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text('{"committed": true}\n')
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".gitignore").write_text(".pytest_cache/\n.hypothesis/\n__pycache__/\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()
    env = {**os.environ, "RUNNER_TEMP": str(runner_temp)}
    probe = tmp_path / "clock-probe"
    _wait_past(max(p.lstat().st_ctime_ns for p in [repo, *repo.rglob("*")]), probe)
    subprocess.run([*_GITHUB_DEFAULT_SHELL, _step_script(_MARK)], cwd=repo, env=env, check=True)
    _wait_past((runner_temp / "before-the-tests").stat().st_mtime_ns, probe)
    return repo, env


def _the_run_writes(repo: Path, *rels: str) -> None:
    """Write each file as a test run would, dated after the mark."""
    for rel in rels:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(path.read_bytes() if path.exists() else b"cache\n")


#: How GitHub runs a step that names no `shell:` on Linux: `bash -e {0}`, with NO pipefail
#: (`-eo pipefail` is only for an explicit `shell: bash`). The pins run the steps the same way.
_GITHUB_DEFAULT_SHELL = ("bash", "-e", "-c")


def _guard(repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """gate.yml's guard step, run as GitHub runs it."""
    return subprocess.run([*_GITHUB_DEFAULT_SHELL, _step_script(_GUARD)], cwd=repo, env=env,
                          capture_output=True, text=True, timeout=60)


_CACHES = (".pytest_cache/v/cache/nodeids", ".hypothesis/constants/0a1b",
           "vinci/__pycache__/m.cpython-312.pyc", "tests/__pycache__/test_x.cpython-312-pytest.pyc")


def test_the_guard_sits_between_the_mark_and_the_mirror_build() -> None:
    """The mark is taken just before the tests and checked just after them, before the mirror
    build, which rewrites frontend/ by design."""
    names = _step_names()
    i = names.index("pytest (offline)")
    assert names[i - 1:i + 3] == [_MARK, "pytest (offline)", _GUARD,
                                  "frontend mirror is in sync with committed data"], names


def test_a_committed_file_rewritten_and_restored_trips_the_guard(tmp_path: Path) -> None:
    """POSITIVE: a test that writes a committed file back byte for byte leaves git clean, and the
    guard still names it — the shape #1065 accepted as a risk."""
    repo, env = _checkout(tmp_path)
    _the_run_writes(repo, *_CACHES, "scenarios/SMPL.json")
    assert _git(repo, "status", "--porcelain") == ""  # git cannot see it
    out = _guard(repo, env)
    assert out.returncode == 1, out.stdout + out.stderr
    assert "the tests wrote 1 file(s) into the checkout" in out.stdout
    assert out.stdout.splitlines()[-1] == "./scenarios/SMPL.json", out.stdout


def test_a_committed_file_restored_with_its_old_times_trips_the_guard(tmp_path: Path) -> None:
    """POSITIVE: a test that backs a committed file up with `shutil.copy2`, rewrites it and
    restores it with `copy2` puts back the bytes AND the old modification time, so a check on
    modification times (`find -newer`) saw nothing, while another worker could still have read the
    file mid-write. Its status-change time moves on every write and no call sets it back
    (coordinator B's review of #1072, round 2)."""
    repo, env = _checkout(tmp_path)
    _the_run_writes(repo, *_CACHES)
    committed = repo / "scenarios" / "SMPL.json"
    backup = tmp_path / "backup.json"
    shutil.copy2(committed, backup)
    committed.write_text('{"mid": "write"}\n')
    shutil.copy2(backup, committed)
    assert _git(repo, "status", "--porcelain") == ""  # git cannot see it
    out = _guard(repo, env)
    assert out.returncode == 1, out.stdout + out.stderr
    assert out.stdout.splitlines()[-1] == "./scenarios/SMPL.json", out.stdout


def test_a_file_the_run_adds_outside_the_caches_trips_the_guard(tmp_path: Path) -> None:
    """POSITIVE: a new file in a committed folder — a marker beside a dossier — is named too,
    git-ignored or not."""
    repo, env = _checkout(tmp_path)
    _the_run_writes(repo, *_CACHES, "data/dossiers/AMZN/known_wrong.json")
    out = _guard(repo, env)
    assert out.returncode == 1 and "./data/dossiers/AMZN/known_wrong.json" in out.stdout, out


def test_the_caches_and_git_are_left_out(tmp_path: Path) -> None:
    """NEGATIVE: what a real run of the suite writes — `.pytest_cache`, `.hypothesis`, every
    `__pycache__` — and git's own files pass, and the log says how many it saw."""
    repo, env = _checkout(tmp_path)
    _the_run_writes(repo, *_CACHES, ".git/index")
    out = _guard(repo, env)
    assert out.returncode == 0, out.stdout + out.stderr
    assert out.stdout.strip() == (f"{len(_CACHES)} files are newer than the mark, every one in "
                                  ".pytest_cache, .hypothesis or a __pycache__")


def test_a_mark_that_sees_nothing_is_refused(tmp_path: Path) -> None:
    """NEGATIVE: if nothing at all is newer than the mark, not even the bytecode every run
    writes, the check is blind (a mark taken after the tests, a filesystem that keeps no times)
    and says so, rather than passing."""
    repo, env = _checkout(tmp_path)
    out = _guard(repo, env)
    assert out.returncode == 1 and "this check cannot see the run" in out.stdout, out


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a folder its mode forbids")
def test_a_folder_the_guard_cannot_read_fails_it_never_passes_it(tmp_path: Path) -> None:
    """NEGATIVE: a find that errors part-way (a test left a folder it may not read, holding a file
    it wrote) fails the step. Without pipefail, under GitHub's default shell, `find | sort` keeps
    sort's 0 and the guard passed green over the file it could not see (review of this change)."""
    repo, env = _checkout(tmp_path)
    _the_run_writes(repo, *_CACHES, "data/locked/written.json")
    (repo / "data" / "locked").chmod(0)
    try:
        out = _guard(repo, env)
    finally:
        (repo / "data" / "locked").chmod(0o755)
    assert out.returncode != 0, out.stdout + out.stderr
    assert "every one in" not in out.stdout, out.stdout
