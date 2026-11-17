"""FAIL FIRST (`vinci.impact.run.fail_first`): head's changed tests on base's code and on head's,
end to end on a two-commit repository — the runner's mechanics. Its corpus run is #976's own test
file (the record's acceptance runs)."""
from __future__ import annotations

import os
import pathlib
import signal
import subprocess
import sys
import time
from typing import Any

import pytest

from vinci.impact import report as rp
from vinci.impact import run as rn


def _git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def _commit(repo: pathlib.Path, files: dict[str, str]) -> str:
    for rel, text in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "c")
    return _git(repo, "rev-parse", "HEAD")


def test_each_node_fails_at_base_on_its_own_line_and_passes_at_head(
        tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    base = _commit(repo, {"vinci/__init__.py": "", "vinci/m.py": "def f():\n    return 1\n",
                          "tests/__init__.py": ""})
    head = _commit(repo, {
        "vinci/m.py": "def f():\n    return 2\n\n\nNEW = 3\n",
        "tests/test_m.py": ("from vinci.m import NEW, f\n\n\n"
                            "def test_the_fix() -> None:\n    assert f() == 2\n\n\n"
                            "def test_the_new_name() -> None:\n    assert NEW == 3\n\n\n"
                            "def test_a_negative_pin() -> None:\n    assert f() > 0\n")})
    s = rn.Settings(repo=repo, base=base, head=head, out=tmp_path / "out", ciq_root=tmp_path,
                    cache_root=tmp_path, store=tmp_path, env_file=None, python=sys.executable)
    res = rn.fail_first(s, {"base": base, "head": head})
    assert res["tests"] == ["tests/test_m.py"]
    assert res["missing_at_base"] == ["vinci.m.NEW"]
    by = {c["node"]: c for c in res["cases"]}
    fix = by["tests/test_m.py::test_the_fix"]
    assert (fix["base"]["outcome"], fix["base"]["where"]) == ("failed", "tests/test_m.py:5")
    assert fix["base"]["message"].startswith("assert 1 == 2")
    new = by["tests/test_m.py::test_the_new_name"]
    assert (new["base"]["outcome"], new["base"]["where"]) == ("failed", "tests/test_m.py:9")
    assert "vinci.m.NEW does not exist at base" in new["base"]["message"]
    neg = by["tests/test_m.py::test_a_negative_pin"]
    assert (neg["base"]["outcome"], neg["head"]["outcome"]) == ("passed", "passed")
    assert all(c["head"]["outcome"] == "passed" for c in res["cases"])


def test_a_pr_that_changes_no_test_says_so(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    base = _commit(repo, {"vinci/m.py": "X = 1\n"})
    head = _commit(repo, {"vinci/m.py": "X = 2\n"})
    s = rn.Settings(repo=repo, base=base, head=head, out=tmp_path / "out", ciq_root=tmp_path,
                    cache_root=tmp_path, store=tmp_path, env_file=None)
    assert rn.fail_first(s, {"base": base, "head": head}) == {
        "tests": [], "cases": [], "note": "the PR changes no test file"}


#: A changed test file whose tests ask git about their own checkout (#1104's shape: the hooks find
#: their checkout with `git rev-parse`), beside a pin that fails at both refs for a real reason.
_ASKS_GIT = '''import pathlib
import subprocess

import pytest

from vinci.m import NEW, f

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()


def _in_a_checkout() -> bool:
    try:
        return _git("rev-parse", "--is-inside-work-tree") == "true"
    except (OSError, subprocess.CalledProcessError):
        return False


def test_a_git_pin_that_fails_first() -> None:
    assert pathlib.Path(_git("rev-parse", "--show-toplevel")).resolve() == ROOT
    assert f() == 2


def test_a_name_only_head_defines() -> None:
    assert NEW == 3


def test_a_git_pin_that_passes_at_both() -> None:
    assert _git("rev-list", "--count", "HEAD") == "2"


def test_git_lists_exactly_the_modules_on_disk() -> None:
    on_disk = {p.relative_to(ROOT).as_posix() for p in (ROOT / "vinci").rglob("*.py")}
    assert set(_git("ls-files", "vinci").splitlines()) == on_disk != set()


@pytest.mark.skipif(not _in_a_checkout(), reason="not a git checkout")
def test_head_is_heads_commit_and_the_refs_are_the_repositorys() -> None:
    assert _git("rev-parse", "HEAD") == _git("rev-parse", "main")
    assert _git("rev-parse", "origin/main") == _git("rev-parse", "HEAD~1")


def test_a_test_that_writes_git_keeps_it_in_its_own_checkout() -> None:
    _git("tag", "impact-probe")
    _git("config", "impact.probe", "written")
    assert _git("tag", "--list", "impact-probe") == "impact-probe"
    pushed = subprocess.run(["git", "push", "origin", "HEAD:refs/heads/impact-pushed"], cwd=ROOT,
                            capture_output=True, text=True)
    assert pushed.returncode != 0, "a push from the checkout reached its origin"


def test_the_checkout_is_clean() -> None:
    dirty = sorted(_git("status", "--porcelain", "--untracked-files=all").splitlines())
    assert not dirty, " ; ".join(dirty)


def test_a_real_failure_at_both_refs() -> None:
    assert f() == 99
'''


def _asks_git_pr(tmp_path: pathlib.Path) -> tuple[rn.Settings, dict[str, str]]:
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    base = _commit(repo, {"vinci/__init__.py": "", "vinci/m.py": "def f():\n    return 1\n",
                          "tests/__init__.py": ""})
    head = _commit(repo, {"vinci/m.py": "def f():\n    return 2\n\n\nNEW = 3\n",
                          "vinci/only_at_head.py": "X = 1\n",
                          "tests/test_g.py": _ASKS_GIT})
    # main has not merged the branch yet: `origin/main` names base, as in an operator's clone
    _git(repo, "update-ref", "refs/remotes/origin/main", base)
    s = rn.Settings(repo=repo, base=base, head=head, out=tmp_path / "out", ciq_root=tmp_path,
                    cache_root=tmp_path, store=tmp_path, env_file=None, python=sys.executable)
    return s, {"base": base, "head": head}


def _state(repo: pathlib.Path) -> dict[str, Any]:
    """What a run must leave as it found it: refs, local config, linked worktrees, the index."""
    return {"refs": _git(repo, "for-each-ref", "--format=%(refname) %(objectname)"),
            "config": _git(repo, "config", "--local", "--list"),
            "worktrees": _git(repo, "worktree", "list", "--porcelain"),
            "index": _git(repo, "ls-files", "--stage"),
            "status": _git(repo, "--no-optional-locks", "status", "--porcelain",
                           "--untracked-files=all")}


@pytest.fixture(scope="module")
def asks_git(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    s, shas = _asks_git_pr(tmp_path_factory.mktemp("asks-git"))
    before = _state(s.repo)
    return {"res": rn.fail_first(s, shas), "before": before, "after": _state(s.repo)}


def _line(text: str) -> str:
    """Where ``text`` sits in the fixture test file, as junit reports it."""
    return f"tests/test_g.py:{_ASKS_GIT.splitlines().index(text) + 1}"


def _outcomes(res: dict[str, Any]) -> dict[str, tuple[str, str]]:
    return {c["node"].removeprefix("tests/test_g.py::"): (c["base"]["outcome"],
                                                         c["head"]["outcome"])
            for c in res["cases"]}


def test_a_test_that_asks_git_runs_in_a_real_checkout_at_both_refs(
        asks_git: dict[str, Any]) -> None:
    """THE FOLLOW-UP TO #1104. Part 1 ran in a `git archive` extract with no `.git`: every test
    here that asks git FAILED at both refs or SKIPPED there, and the report printed that as a
    result. Each side is now its own clone of the repository at head's commit, its refs the
    repository's own (`origin/main` included), base's with its `vinci/` swapped in its index too,
    so git there lists the modules base has (not head's, nor none)."""
    res = asks_git["res"]
    got = _outcomes(res)
    assert len(got) == len(res["cases"]) == 8
    assert res["missing_at_base"] == ["vinci.m.NEW"]   # the placeholder ran, beside the checkout
    first = next(c for c in res["cases"] if c["node"].endswith("::test_a_git_pin_that_fails_first"))
    assert got["test_a_git_pin_that_fails_first"] == ("failed", "passed")
    assert (first["base"]["where"], first["base"]["message"]) == (
        _line("    assert f() == 2"), "assert 1 == 2")
    assert got["test_a_name_only_head_defines"] == ("failed", "passed")
    for name in ("test_a_git_pin_that_passes_at_both", "test_git_lists_exactly_the_modules_on_disk",
                 "test_head_is_heads_commit_and_the_refs_are_the_repositorys"):
        assert got[name] == ("passed", "passed"), name
    assert res["checkout"] == "clone"


def test_a_test_that_writes_git_leaves_the_repository_as_it_was(asks_git: dict[str, Any]) -> None:
    """REVIEW ROUND 1 (A, item 3). Linked worktrees share the repository's refs and config: a test
    that writes a tag or a config key wrote it into the operator's repository, and the second side
    to write it failed on timing alone. Each side's git writes now stay in its own clone."""
    assert _outcomes(asks_git["res"])["test_a_test_that_writes_git_keeps_it_in_its_own_checkout"] \
        == ("passed", "passed")
    before, after = asks_git["before"], asks_git["after"]
    assert "impact-probe" not in after["refs"] and "impact.probe" not in after["config"]
    assert "impact-pushed" not in after["refs"]
    assert after == before


def test_bases_checkout_is_heads_commit_with_bases_vinci_staged(asks_git: dict[str, Any]) -> None:
    """THE ACCEPTED LIMITATION, PINNED (review round 1, A item 4). Base's checkout is head's commit
    with base's `vinci/` staged over it: `git rev-parse HEAD` is head's sha there, and `git status`
    and `git diff HEAD` show base's `vinci/` as staged. A test that asserts a clean checkout
    therefore FAILS AT BASE ALONE, and reads as "fails first" for a reason no code gave. This pin
    states that outcome exactly, so a regression (anything else in the status) and a later fix (a
    clean base) both turn it red, differently."""
    res = asks_git["res"]
    clean = next(c for c in res["cases"] if c["node"].endswith("::test_the_checkout_is_clean"))
    assert (clean["base"]["outcome"], clean["head"]["outcome"]) == ("failed", "passed")
    assert clean["base"]["message"] == "AssertionError: D  vinci/only_at_head.py ; M  vinci/m.py"


def test_a_real_failure_at_both_refs_is_still_reported_as_one(asks_git: dict[str, Any]) -> None:
    res = asks_git["res"]
    real = next(c for c in res["cases"] if c["node"].endswith("::test_a_real_failure_at_both_refs"))
    at = _line("    assert f() == 99")
    assert (real["base"]["outcome"], real["base"]["where"], real["base"]["message"]) == (
        "failed", at, "assert 1 == 99")
    assert (real["head"]["outcome"], real["head"]["where"], real["head"]["message"]) == (
        "failed", at, "assert 2 == 99")
    md = "\n".join(rp.fail_first_lines(res, 40))
    assert "### 1. Fail first — 3 of 8 test(s) fail on base code and pass on head code" in md
    assert "Pass at both: 4" in md and "**fail at head: 1**" in md and "skipped: 0." in md
    assert "each in its own clone of the repository at head's commit" in md
    assert (f"| `tests/test_g.py::test_a_real_failure_at_both_refs` | FAILED at `{at}` — "
            f"assert 1 == 99 | FAILED at `{at}` — assert 2 == 99 |") in md


def test_part_one_touches_no_other_worktree_of_the_repository(tmp_path: pathlib.Path) -> None:
    """REVIEW ROUND 1 (A, item 1): the negative pin. Decoys with names like part 1's own — beside
    its folder, a prefix of it, the same folder under another root, locked and not — are every
    other session's worktrees as far as git can tell, and a run must leave each one registered."""
    s, shas = _asks_git_pr(tmp_path)
    decoys = {s.out / "failfirst-decoy" / "head-tree": False, s.out / "failfirstX": True,
              tmp_path / "other" / "failfirst" / "head-tree": True}
    for path, locked in decoys.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        _git(s.repo, "worktree", "add", "--detach", "-q", str(path), shas["base"])
        if locked:
            _git(s.repo, "worktree", "lock", "--reason", "another session", str(path))
    before = _git(s.repo, "worktree", "list", "--porcelain")
    rn.fail_first(s, shas)
    assert _git(s.repo, "worktree", "list", "--porcelain") == before
    assert all(p.is_dir() for p in decoys)
    assert sorted(p.name for p in (s.out / "failfirst").iterdir()) == [
        "junit-base.xml", "junit-head.xml", "pytest-base.log", "pytest-head.log", "shim"]


_WAITS = '''import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_waits_to_be_killed() -> None:
    (ROOT.parent / f"started-{ROOT.name}").touch()
    time.sleep(300)
'''


def test_a_run_killed_mid_stage_leaves_nothing_in_the_repository(tmp_path: pathlib.Path) -> None:
    """REVIEW ROUND 1 (A, item 2). A run killed while its tests run (a tool's timeout kills the
    process group) never reaches a `finally`. With linked worktrees both stayed registered in the
    shared repository, ~280 MB each and listed by every session's `git worktree list`. Through
    `run()`: kill the group once both sides' pytest is running, and the repository is as it was;
    what is left is two folders under `--out`, each a clone of its own."""
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    base = _commit(repo, {"vinci/__init__.py": "", "tests/__init__.py": ""})
    head = _commit(repo, {"tests/test_waits.py": _WAITS})
    before = _state(repo)
    out = tmp_path / "out"
    env = {**os.environ, "PYTHONPATH": str(pathlib.Path(__file__).resolve().parents[1])}
    proc = subprocess.Popen(
        [sys.executable, "-m", "vinci.impact", "run", "--repo", str(repo), "--base", base,
         "--head", head, "--out", str(out), "--store", str(tmp_path / "no.db"),
         "--ciq-root", str(tmp_path), "--cache-root", str(tmp_path),
         "--env-file", str(tmp_path / "no.env")],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        started = [out / "failfirst" / f"started-{side}-tree" for side in ("base", "head")]
        deadline = time.monotonic() + 120
        while not all(p.exists() for p in started):
            assert proc.poll() is None, (proc.stdout.read() if proc.stdout else b"").decode()
            assert time.monotonic() < deadline, "both sides' pytest never started"
            time.sleep(0.2)
    finally:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=60)
    assert proc.returncode == -signal.SIGTERM
    assert _state(repo) == before
    for side in ("base", "head"):
        assert (out / "failfirst" / f"{side}-tree" / ".git").is_dir()


def test_a_run_started_inside_a_git_hook_never_touches_that_repository(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """REVIEW ROUND 1 (A, item 5). Git sets `GIT_DIR` and `GIT_INDEX_FILE` for a hook it runs, and
    those override `git -C`: base's `git rm -r vinci` would have run on the hook's own repository
    and index, and each side's tests would have asked git about that repository instead of their
    checkout. The stage's git and its pytest drop every repository-local variable git names
    (`git rev-parse --local-env-vars`)."""
    s, shas = _asks_git_pr(tmp_path)
    before = _state(s.repo)
    git_dir = s.repo / ".git"
    with monkeypatch.context() as m:
        for name, value in (("GIT_DIR", git_dir), ("GIT_COMMON_DIR", git_dir),
                            ("GIT_WORK_TREE", s.repo), ("GIT_INDEX_FILE", git_dir / "index")):
            m.setenv(name, str(value))
        res = rn.fail_first(s, shas)
    assert _state(s.repo) == before
    assert (s.repo / "vinci" / "only_at_head.py").is_file()
    got = _outcomes(res)
    assert got["test_a_git_pin_that_fails_first"] == ("failed", "passed")
    assert got["test_git_lists_exactly_the_modules_on_disk"] == ("passed", "passed")


def test_an_archive_run_report_says_its_tree_had_no_git() -> None:
    """A report written before part 1 ran in clones carries no `checkout`: re-rendered, it says how
    it was run rather than claiming a checkout it never had."""
    old = {"tests": ["tests/t.py"], "seconds": 1.0, "cases": [
        {"node": "tests/t.py::test_x", "base": {"outcome": "failed", "where": "tests/t.py:1",
                                                "message": "m"},
         "head": {"outcome": "passed", "where": None, "message": ""}}]}
    md = "\n".join(rp.fail_first_lines(old, 40))
    assert "a `git archive` extract with no `.git`" in md and "clone" not in md
