"""ONE GATE, AND IT RUNS ANYWHERE (fix request 2, RH-D3 and RH-D4).

gate.yml says it runs "THE SAME COMMANDS `bin/commit` RUNS … If you change one, change the other".
Two things made that false:

* RH-D4. `bin/commit` never ran the frontend-mirror check gate.yml runs, so a commit passed the
  local gate and failed CI; and the gates in weekly-screen, monthly-score and
  theme-intelligence-weekly ran pytest without `-rs`, so their skips printed no reason. Only
  `bin/commit`'s `-rs` was pinned.
* RH-D3. `bin/commit` defaulted `VENV` to one Mac's absolute path, which failed on every other
  machine (exit 127 at the ruff step) and published a username in a public repository.

These pins read every gate's pytest line, and drive `bin/commit` itself in a scratch checkout whose
interpreter is a stand-in that records what it was asked to run.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_no_local_paths import local_paths

ROOT = Path(__file__).resolve().parents[1]
BIN_COMMIT = ROOT / "bin" / "commit"
GATE_YML = ROOT / ".github" / "workflows" / "gate.yml"
#: Options that take the next token as their value.
_VALUED = {"-m", "-p", "-k", "-n"}
#: HOW the suite is spread over processes, never WHICH tests run or what a log reports: `-n`,
#: pytest-xdist's worker count. gate.yml runs the suite over the runner's cores (2026-11-13), and
#: `bin/commit` over the machine's when its venv imports pytest-xdist (W83, 2026-11-20; the shared
#: venv has carried 3.8.0 since 2026-11-16). Every other gate, and `bin/commit` on a venv without
#: it, may run it on one.
_SCHEDULING = {"-n"}


def _pytest_commands(path: Path) -> list[list[str]]:
    """Each uncommented `-m pytest` command in a workflow or script, as argv."""
    out = []
    for line in path.read_text().splitlines():
        text = line.strip().removeprefix("run:").strip()
        if "-m pytest" in text and not text.startswith("#"):
            out.append(shlex.split(text))
    return out


def _flags(argv: list[str]) -> list[tuple[str, ...]]:
    """The options after `pytest` in ``argv``, a valued one paired with its value."""
    rest = argv[argv.index("pytest") + 1:]
    out: list[tuple[str, ...]] = []
    i = 0
    while i < len(rest):
        n = 2 if rest[i] in _VALUED and i + 1 < len(rest) else 1
        out.append(tuple(rest[i:i + n]))
        i += n
    return out


def _gate_flags() -> list[tuple[str, ...]]:
    """The flags gate.yml's pytest step runs with — read from it, so the pin follows gate.yml."""
    (argv,) = _pytest_commands(GATE_YML)
    flags = _flags(argv)
    assert ("-rs",) in flags and ("-m", "not network") in flags, flags
    return flags


def _required_flags() -> list[tuple[str, ...]]:
    """gate.yml's flags less its scheduling ones: what every gate must run with too."""
    return [f for f in _gate_flags() if f[0] not in _SCHEDULING]


def _gates() -> list[Path]:
    workflows = [p for p in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
                 if _pytest_commands(p)]
    return [*workflows, BIN_COMMIT]


def _has(argv: list[str], flag: tuple[str, ...]) -> bool:
    n = len(flag)
    return any(tuple(argv[i:i + n]) == flag for i in range(len(argv)))


def test_every_gate_runs_pytest_with_the_gates_own_flags() -> None:
    """RH-D4: gate.yml, bin/commit and every workflow that gates before it pushes run pytest with
    the same flags — `-rs` among them, so a skip prints its reason in every log."""
    gates = _gates()
    assert {p.name for p in gates} >= {"gate.yml", "weekly-screen.yml", "monthly-score.yml",
                                        "theme-intelligence-weekly.yml", "commit"}, gates
    required = _required_flags()
    missing = {f"{p.name}: {' '.join(argv)}": [" ".join(f) for f in required if not _has(argv, f)]
               for p in gates for argv in _pytest_commands(p)}
    assert not {k: v for k, v in missing.items() if v}, missing


def test_only_the_worker_count_is_left_to_each_gate() -> None:
    """The scheduling exemption admits a gate that runs the suite on one process, and nothing
    else: a gate dropping `-rs`, the `not network` selection or `-p no:warnings` is still caught,
    with or without workers of its own."""
    required = _required_flags()
    assert not any(f[0] in _SCHEDULING for f in required), required
    one_process = shlex.split('python -m pytest -m "not network" -p no:warnings --tb=short -rs')
    assert [f for f in required if not _has(one_process, f)] == []
    workers = shlex.split('python -m pytest -m "not network" -p no:warnings --tb=short -rs -n 4')
    for dropped in (("-rs",), ("-p", "no:warnings"), ("-m", "not network")):
        argv = ["python", "-m", "pytest",
                *(a for f in _flags(workers) if f != dropped for a in f)]
        assert [f for f in required if not _has(argv, f)] == [dropped], argv


def test_the_local_gate_carries_no_machines_path() -> None:
    """RH-D3: a public repository's gate names no one's home folder."""
    assert local_paths(BIN_COMMIT.read_text()) == []


_FAKE_PYTHON = """#!/bin/sh
printf '%s\\n' "$*" >> "$FAKE_LOG"
if [ "$1" = "-c" ] && [ -n "$FAKE_NO_XDIST" ]; then
  exit 1
fi
if [ "$2" = "pytest" ] && [ -n "$FAKE_RED" ]; then
  exit 1
fi
if [ "$1" = "frontend/build.py" ] && [ -n "$FAKE_STALE" ]; then
  echo rebuilt >> frontend/page.txt
fi
exit 0
"""


def _checkout(tmp_path: Path, *, venv: bool = True) -> Path:
    """A git checkout with one tracked frontend file, one staged change, and — when ``venv`` — a
    `.venv/bin/python` that logs its arguments and passes."""
    repo = tmp_path / "checkout"
    (repo / "frontend").mkdir(parents=True)
    (repo / "frontend" / "page.txt").write_text("built\n")
    # main's guard: the protected-file check reads what is protected from the base's copy, and a
    # base without one is a check that cannot run (#1104 round 1)
    guard = repo / ".claude" / "hooks" / "decision_path_guard.py"
    guard.parent.mkdir(parents=True)
    shutil.copy(ROOT / ".claude" / "hooks" / "decision_path_guard.py", guard)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    if venv:
        py = repo / ".venv" / "bin" / "python"
        py.parent.mkdir(parents=True)
        py.write_text(_FAKE_PYTHON)
        py.chmod(0o755)
        (repo / ".gitignore").write_text(".venv/\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit",
                    "-qm", "base"], check=True)
    # the base bin/commit's protected-file check reads the branch against (2026-11-17)
    subprocess.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", "HEAD"],
                   check=True)
    (repo / "change.txt").write_text("a change\n")
    subprocess.run(["git", "-C", str(repo), "add", "change.txt"], check=True)
    return repo


def _commit(repo: Path, message: str = "probe", **env: str) -> subprocess.CompletedProcess[str]:
    base = {k: v for k, v in os.environ.items() if k != "VENV"}
    base.update({"FAKE_LOG": str(repo.parent / "calls.log"), "GIT_AUTHOR_NAME": "t",
                 "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                 "GIT_COMMITTER_EMAIL": "t@t"}, **env)
    return subprocess.run(["bash", str(BIN_COMMIT), "-qm", message], cwd=repo, capture_output=True,
                          text=True, timeout=120, env=base)


def _commits(repo: Path) -> int:
    return int(subprocess.run(["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
                              capture_output=True, text=True, check=True).stdout)


def _steps(repo: Path) -> list[str]:
    calls = (repo.parent / "calls.log").read_text().splitlines()
    return [c.split()[1] if c.startswith("-m") else c.split()[0] for c in calls]


def _pytest_call(repo: Path) -> list[str]:
    (call,) = [c for c in (repo.parent / "calls.log").read_text().splitlines()
               if c.startswith("-m pytest")]
    return call.split()


def test_the_local_gate_finds_the_checkouts_own_interpreter(tmp_path: Path) -> None:
    """RH-D3, run: with VENV unset it uses the checkout's .venv, runs every check gate.yml runs —
    ruff, mypy, pytest, then the mirror build — and commits. Before pytest it asks the venv
    whether pytest-xdist imports (W83, 2026-11-20)."""
    repo = _checkout(tmp_path)
    out = _commit(repo)
    assert out.returncode == 0, out.stderr
    assert _steps(repo) == ["ruff", "mypy", "-c", "pytest", "frontend/build.py"], _steps(repo)
    assert _commits(repo) == 2


def test_the_local_gate_runs_the_suite_on_workers_when_the_venv_has_xdist(tmp_path: Path) -> None:
    """W83 (2026-11-20; operator: "Approve bin/commit + gate.yml comment (Recommended)"), run:
    `-n auto`, as gate.yml runs it, and no warning."""
    repo = _checkout(tmp_path)
    out = _commit(repo)
    assert out.returncode == 0, out.stderr
    argv = _pytest_call(repo)
    assert argv[argv.index("-n") + 1] == "auto", argv
    assert "WARNING" not in out.stdout + out.stderr


def test_the_local_gate_runs_on_one_process_and_says_so_without_xdist(tmp_path: Path) -> None:
    """W83, run, NEGATIVE: a venv whose pytest-xdist does not import runs the same suite on one
    process, prints one loud line saying so, and still commits: a warning, never a refusal (the
    fast gate's rule since #1086, RH-D2)."""
    repo = _checkout(tmp_path)
    out = _commit(repo, FAKE_NO_XDIST="1")
    assert out.returncode == 0, out.stderr
    assert "-n" not in _pytest_call(repo), _pytest_call(repo)
    warned = [ln for ln in out.stderr.splitlines() if "WARNING" in ln]
    assert len(warned) == 1 and "pytest-xdist" in warned[0] and "ONE process" in warned[0], (
        out.stderr)
    assert _commits(repo) == 2


@pytest.mark.parametrize("no_xdist", ["", "1"], ids=["on-workers", "on-one-process"])
def test_a_red_suite_commits_nothing_on_either_branch(tmp_path: Path, no_xdist: str) -> None:
    """W83, run, NEGATIVE: pytest now runs inside an if/else. A failing suite still stops the gate
    before the mirror build and the commit, on workers and on one process."""
    repo = _checkout(tmp_path)
    out = _commit(repo, FAKE_RED="1", FAKE_NO_XDIST=no_xdist)
    assert out.returncode != 0, out.stdout + out.stderr
    assert "gate green" not in out.stdout and "frontend/build.py" not in _steps(repo)
    assert _commits(repo) == 1


def _addopts() -> str:
    for line in (ROOT / "pyproject.toml").read_text().splitlines():
        if line.startswith("addopts"):
            return line
    raise AssertionError("pyproject.toml has no addopts line")


def test_the_local_gate_has_one_pytest_line_on_workers_and_one_on_one_process() -> None:
    commands = _pytest_commands(BIN_COMMIT)
    assert [_has(argv, ("-n", "auto")) for argv in commands] == [True, False], commands


@pytest.mark.parametrize("which", [0, 1], ids=["on-workers", "on-one-process"])
def test_every_pytest_line_of_the_local_gate_prints_its_outcome_counts(
        tmp_path: Path, which: int) -> None:
    """W83, run: each pytest command `bin/commit` can run, executed as written on a two-test
    suite under this repository's own addopts, ends with its outcome counts. bin/commit's `-q` on
    top of addopts' `-q` made `-qq`, which prints none, so its log never stated what passed."""
    argv = [sys.executable if a == "$VENV" else a for a in _pytest_commands(BIN_COMMIT)[which]]
    if _has(argv, ("-n", "auto")) and importlib.util.find_spec("xdist") is None:
        pytest.skip("pytest-xdist is not importable in this venv: bin/commit runs the other line")
    suite = tmp_path / "suite"
    (suite / "tests").mkdir(parents=True)
    (suite / "pyproject.toml").write_text(f"[tool.pytest.ini_options]\n{_addopts()}\n")
    (suite / "tests" / "test_two.py").write_text("def test_a():\n    pass\n\n"
                                                 "def test_b():\n    pass\n")
    # two workers are enough for two tests: `auto` stays in the command as written. The command is
    # run as written, so the caller's PYTEST_ADDOPTS is not passed on: a `-k` there deselected both
    # tests and the child exited 5 (found running this gate with `PYTEST_ADDOPTS="-k ..."`).
    env = {k: v for k, v in os.environ.items() if k != "PYTEST_ADDOPTS"}
    out = subprocess.run([*argv, "-p", "no:cacheprovider"], cwd=suite, capture_output=True,
                         text=True, timeout=120, env={**env, "PYTEST_XDIST_AUTO_NUM_WORKERS": "2"})
    assert out.returncode == 0, out.stdout + out.stderr
    assert re.search(r"^2 passed in [\d.]+s", out.stdout, re.M), (argv, out.stdout)


def test_the_local_gate_refuses_a_stale_mirror(tmp_path: Path) -> None:
    """RH-D4, run: a build that changes frontend/ means the data moved and the mirror was not
    rebuilt — refused before the commit, as gate.yml refuses it after the push."""
    repo = _checkout(tmp_path)
    out = _commit(repo, FAKE_STALE="1")
    assert out.returncode == 1
    assert "frontend/ is stale" in out.stderr and "frontend/page.txt" in out.stderr
    assert _commits(repo) == 1


def test_the_local_gate_refuses_without_an_interpreter(tmp_path: Path) -> None:
    """NEGATIVE: no VENV and no .venv is a refusal that says what to do, never an exit 127."""
    repo = _checkout(tmp_path, venv=False)
    out = _commit(repo)
    assert out.returncode == 1 and "no project interpreter" in out.stderr
    assert _commits(repo) == 1


def test_the_local_gate_refuses_a_protected_file_with_no_operator_approval(tmp_path: Path) -> None:
    """2026-11-17, run: a decision-line file written straight to disk, as a Bash edit writes it
    with no hook seeing it, is refused before the suite runs and nothing is committed; the same
    change whose message quotes the operator's approval goes through the whole gate and commits."""
    repo = _checkout(tmp_path)
    target = repo / "vinci" / "dossier" / "verdict.py"
    target.parent.mkdir(parents=True)
    target.write_text("# rewritten by sed\n")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    out = _commit(repo)
    assert out.returncode == 1, out.stdout + out.stderr
    assert "REFUSED" in out.stderr and "vinci/dossier/verdict.py" in out.stderr
    assert not (repo.parent / "calls.log").exists()          # refused before ruff
    assert _commits(repo) == 1
    approved = ('probe\n\nOperator-approved: vinci/dossier/verdict.py "Yes, card to fix '
                f'(Recommended)" {dt.date.today().isoformat()}')
    out = _commit(repo, approved)
    assert out.returncode == 0, out.stderr
    assert _commits(repo) == 2
