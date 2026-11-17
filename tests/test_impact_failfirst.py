"""FAIL FIRST (`vinci.impact.run.fail_first`): head's changed tests on base's code and on head's,
end to end on a two-commit repository — the runner's mechanics. Its corpus run is #976's own test
file (the record's acceptance runs)."""
from __future__ import annotations

import pathlib
import subprocess
import sys
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
def test_a_pin_that_skips_outside_a_checkout() -> None:
    assert _git("status", "--porcelain", "--untracked-files=all", "--", ".", ":!vinci") == ""


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
    s = rn.Settings(repo=repo, base=base, head=head, out=tmp_path / "out", ciq_root=tmp_path,
                    cache_root=tmp_path, store=tmp_path, env_file=None, python=sys.executable)
    return s, {"base": base, "head": head}


@pytest.fixture(scope="module")
def asks_git(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    s, shas = _asks_git_pr(tmp_path_factory.mktemp("asks-git"))
    return rn.fail_first(s, shas)


def _line(text: str) -> str:
    """Where ``text`` sits in the fixture test file, as junit reports it."""
    return f"tests/test_g.py:{_ASKS_GIT.splitlines().index(text) + 1}"


def test_a_test_that_asks_git_runs_in_a_real_checkout_at_both_refs(
        asks_git: dict[str, Any]) -> None:
    """THE FOLLOW-UP TO #1104. Part 1 ran in a `git archive` extract with no `.git`: every test
    here that asks git FAILED at both refs or SKIPPED there, and the report printed that as a
    result. Each side is now a detached worktree of head's commit, base's with its `vinci/`
    swapped in its index too, so git there lists the modules base has (not head's, nor none) and
    nothing the harness writes is an untracked file in either checkout."""
    res = asks_git
    by = {c["node"].removeprefix("tests/test_g.py::"): c for c in res["cases"]}
    assert len(by) == len(res["cases"]) == 6
    assert res["missing_at_base"] == ["vinci.m.NEW"]   # the placeholder ran, beside the checkout

    def outcomes(name: str) -> tuple[str, str]:
        return by[name]["base"]["outcome"], by[name]["head"]["outcome"]
    first = by["test_a_git_pin_that_fails_first"]["base"]
    assert outcomes("test_a_git_pin_that_fails_first") == ("failed", "passed")
    assert (first["where"], first["message"]) == (_line("    assert f() == 2"), "assert 1 == 2")
    assert outcomes("test_a_name_only_head_defines") == ("failed", "passed")
    for name in ("test_a_git_pin_that_passes_at_both", "test_git_lists_exactly_the_modules_on_disk",
                 "test_a_pin_that_skips_outside_a_checkout"):
        assert outcomes(name) == ("passed", "passed"), name
    assert res["checkout"] == "worktree"


def test_a_real_failure_at_both_refs_is_still_reported_as_one(asks_git: dict[str, Any]) -> None:
    res = asks_git
    real = next(c for c in res["cases"] if c["node"].endswith("::test_a_real_failure_at_both_refs"))
    at = _line("    assert f() == 99")
    assert (real["base"]["outcome"], real["base"]["where"], real["base"]["message"]) == (
        "failed", at, "assert 1 == 99")
    assert (real["head"]["outcome"], real["head"]["where"], real["head"]["message"]) == (
        "failed", at, "assert 2 == 99")
    md = "\n".join(rp.fail_first_lines(res, 40))
    assert "### 1. Fail first — 2 of 6 test(s) fail on base code and pass on head code" in md
    assert "Pass at both: 3" in md and "**fail at head: 1**" in md and "skipped: 0." in md
    assert "each in a detached git worktree of head's commit" in md
    assert (f"| `tests/test_g.py::test_a_real_failure_at_both_refs` | FAILED at `{at}` — "
            f"assert 1 == 99 | FAILED at `{at}` — assert 2 == 99 |") in md


def test_part_one_leaves_no_worktree_registered_and_clears_one_a_killed_run_left(
        tmp_path: pathlib.Path) -> None:
    s, shas = _asks_git_pr(tmp_path)
    left = s.out / "failfirst" / "head-tree"
    left.parent.mkdir(parents=True)
    _git(s.repo, "worktree", "add", "--detach", "-q", str(left), shas["base"])
    # a run killed during `git worktree add` leaves it LOCKED ("initializing"): one --force
    # refuses to remove a locked worktree, and the next run would stop at its own cleanup
    _git(s.repo, "worktree", "lock", "--reason", "initializing", str(left))
    rn.fail_first(s, shas)
    listed = [ln for ln in _git(s.repo, "worktree", "list", "--porcelain").splitlines()
              if ln.startswith("worktree ")]
    assert [pathlib.Path(ln.removeprefix("worktree ")).resolve() for ln in listed] == [
        s.repo.resolve()]
    assert sorted(p.name for p in (s.out / "failfirst").iterdir()) == [
        "junit-base.xml", "junit-head.xml", "pytest-base.log", "pytest-head.log", "shim"]


def test_an_archive_run_report_says_its_tree_had_no_git() -> None:
    """A report written before part 1 ran in worktrees carries no `checkout`: re-rendered, it
    says how it was run rather than claiming a checkout it never had."""
    old = {"tests": ["tests/t.py"], "seconds": 1.0, "cases": [
        {"node": "tests/t.py::test_x", "base": {"outcome": "failed", "where": "tests/t.py:1",
                                                "message": "m"},
         "head": {"outcome": "passed", "where": None, "message": ""}}]}
    md = "\n".join(rp.fail_first_lines(old, 40))
    assert "a `git archive` extract with no `.git`" in md and "worktree" not in md
