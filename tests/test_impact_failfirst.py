"""FAIL FIRST (`vinci.impact.run.fail_first`): head's changed tests on base's code and on head's,
end to end on a two-commit repository — the runner's mechanics. Its corpus run is #976's own test
file (the record's acceptance runs)."""
from __future__ import annotations

import pathlib
import subprocess
import sys

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
