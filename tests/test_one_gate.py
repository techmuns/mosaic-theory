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

import os
import shlex
import subprocess
from pathlib import Path

from tests.test_no_local_paths import local_paths

ROOT = Path(__file__).resolve().parents[1]
BIN_COMMIT = ROOT / "bin" / "commit"
GATE_YML = ROOT / ".github" / "workflows" / "gate.yml"
#: Options that take the next token as their value.
_VALUED = {"-m", "-p", "-k"}


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
    required = _gate_flags()
    missing = {f"{p.name}: {' '.join(argv)}": [" ".join(f) for f in required if not _has(argv, f)]
               for p in gates for argv in _pytest_commands(p)}
    assert not {k: v for k, v in missing.items() if v}, missing


def test_the_local_gate_carries_no_machines_path() -> None:
    """RH-D3: a public repository's gate names no one's home folder."""
    assert local_paths(BIN_COMMIT.read_text()) == []


_FAKE_PYTHON = """#!/bin/sh
printf '%s\\n' "$*" >> "$FAKE_LOG"
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
    (repo / "change.txt").write_text("a change\n")
    subprocess.run(["git", "-C", str(repo), "add", "change.txt"], check=True)
    return repo


def _commit(repo: Path, **env: str) -> subprocess.CompletedProcess[str]:
    base = {k: v for k, v in os.environ.items() if k != "VENV"}
    base.update({"FAKE_LOG": str(repo.parent / "calls.log"), "GIT_AUTHOR_NAME": "t",
                 "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                 "GIT_COMMITTER_EMAIL": "t@t"}, **env)
    return subprocess.run(["bash", str(BIN_COMMIT), "-qm", "probe"], cwd=repo, capture_output=True,
                          text=True, timeout=120, env=base)


def _commits(repo: Path) -> int:
    return int(subprocess.run(["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
                              capture_output=True, text=True, check=True).stdout)


def test_the_local_gate_finds_the_checkouts_own_interpreter(tmp_path: Path) -> None:
    """RH-D3, run: with VENV unset it uses the checkout's .venv, runs every check gate.yml runs —
    ruff, mypy, pytest, then the mirror build — and commits."""
    repo = _checkout(tmp_path)
    out = _commit(repo)
    assert out.returncode == 0, out.stderr
    calls = (repo.parent / "calls.log").read_text().splitlines()
    assert [c.split()[1] if c.startswith("-m") else c.split()[0] for c in calls] == [
        "ruff", "mypy", "pytest", "frontend/build.py"], calls
    assert _commits(repo) == 2


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
