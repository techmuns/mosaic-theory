"""EVERY SCRIPT THAT TOUCHES THE DATA TREE RUNS FROM THE REPO ROOT.

THE CONVENTION. `Config.data_dir` defaults to a bare relative `Path("data")`, and so do ~28 other
roots — `vinci/scenarios.py`, `vinci/monitor.py`, `vinci/dossier/refresh.py`, and the
`Path("data/…")` literals throughout `cli.py`. That is deliberate and uniform: four test modules
use `monkeypatch.chdir` for isolation precisely because it holds. The price is that a process must
START in the repo root, and a file under `scripts/` does not.

WHAT WENT WRONG WITHOUT THIS. Running the triage cost gate from `scripts/` built a second, empty
tree at `scripts/data/` and refilled it — 4.6MB of SEC responses re-fetched into a cache nothing
would read again.

WHY NOT ANCHOR `data_dir` INSTEAD (tried, reverted — #526 review). Anchoring moves ONE of those
~28 roots and leaves the rest, which is worse than either endpoint: `vinci dossier IT` from
`scripts/` would read the underwrite record from `scripts/scenarios` — absent, and absent means
"not underwritten" BY DESIGN — while writing to the now-absolute COMMITTED `data/dossiers/IT/`.
A tracked artifact loses its thesis and the run reports success. Uniformly wrong beats half-right,
and `parents[1]` is not the repo root under `pip install .` anyway (hatchling wheel, `vinci`
console script) — it is site-packages.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

#: Names whose appearance means the file resolves a data root and therefore cares about the CWD.
DATA_ROOT_MARKERS = ("get_config", "from_config", "ensure_dirs", "data_dir", "snapshots_dir",
                     "cache_dir")


def _touches_data_tree(src: str) -> bool:
    return any(m in src for m in DATA_ROOT_MARKERS)


def _chdirs(tree: ast.Module) -> bool:
    return any(isinstance(n, ast.Call) and ast.unparse(n.func).endswith("os.chdir")
               for n in ast.walk(tree))


@pytest.mark.parametrize("path", sorted(SCRIPTS.glob("*.py")), ids=lambda p: p.name)
def test_a_script_that_reads_the_data_tree_runs_from_the_repo_root(path: pathlib.Path) -> None:
    """A script resolving a data root must `os.chdir` to the repo root before it does."""
    src = path.read_text()
    if not _touches_data_tree(src):
        pytest.skip("does not resolve a data root")
    assert _chdirs(ast.parse(src)), (
        f"{path.name} resolves a data root but never chdirs to the repo root. Run from "
        f"`scripts/` it addresses a second tree at `scripts/data/` — and a cache REFILLS what it "
        f"misses, so the failure looks like a slow run rather than an error.")


@pytest.mark.parametrize("path", sorted(SCRIPTS.glob("*.py")), ids=lambda p: p.name)
def test_the_chdir_cannot_leak_into_an_importing_process(path: pathlib.Path) -> None:
    """IN `__main__` (or before the first module-level data read), NEVER inside an importable
    function. `tests/test_cohort_pool.py` loads `build_cohort_pool` via importlib to exercise
    `select_run`; an import-time chdir inside a def would move the whole suite's CWD and break the
    four modules that use `monkeypatch.chdir` for isolation."""
    tree = ast.parse(path.read_text())
    if not _chdirs(tree):
        pytest.skip("no chdir")
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        assert not _chdirs(fn), (
            f"{path.name}: os.chdir sits inside {fn.name}() — calling it from a test moves the "
            f"suite's working directory out from under every other test")
