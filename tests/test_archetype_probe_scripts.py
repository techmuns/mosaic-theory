"""The archetype probe's scripts (`scripts/archetype_probe/`) keep the promises their README makes.

WHY (PR #1145, review round 1). The README and the scope pack say three things of these scripts:
every machine path comes from the environment and nothing is written into a checkout; every
script prints the `vinci` it imported, first; and the archetype rule exists once. Review found each
broken on the PR's head:
- `diff5a.py` still derived its output folder from its own path, so it read and wrote
  `scripts/out/` inside the checkout;
- 18 of the 35 scripts never printed `vinci.__file__`;
- `pages5b.py` carried a hand copy of `grid.py`'s `grid_arch`.

A fourth finding came from CLAUDE.md's truncation rule: `pdf_find.py` cut a page's text at 4,000
characters without saying so.

These are static and import-level checks, with no network and no CIQ data, so they run in CI.
"""
from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "archetype_probe"
SCRIPTS = sorted(p for p in PROBE.glob("*.py"))


def test_the_probe_folder_is_where_the_readme_says() -> None:
    """POSITIVE: the checks below read real files, so an empty glob cannot pass them."""
    assert (PROBE / "README.md").exists()
    assert len(SCRIPTS) >= 30, [p.name for p in SCRIPTS]


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_no_script_derives_a_folder_from_its_own_location(path: Path) -> None:
    """Only `probe_common.py` may read `__file__`: it finds the checkout to import `vinci` from.
    Any other script that builds a path from its own location writes into the checkout."""
    if path.name == "probe_common.py":
        return
    own_path = re.compile(r"Path\(\s*__file__|os\.path\.\w+\(\s*__file__|\b__file__\s*\)\.")
    assert not own_path.search(path.read_text()), (
        f"{path.name} builds a path from its own location; take OUT/DATA from probe_common")


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_every_script_that_uses_vinci_goes_through_the_shared_setup(path: Path) -> None:
    """A script that touches `vinci` imports `probe_common` (directly, or through a script that
    does), so it imports this checkout's `vinci` and prints it."""
    if path.name == "probe_common.py":
        return
    text = path.read_text()
    if "vinci" not in text:
        return
    assert re.search(r"^from (probe_common|pages5b|build5a|ciq5a) import", text, re.M), (
        f"{path.name} uses vinci without the shared setup")


def test_the_shared_setup_prints_the_vinci_it_imported(tmp_path: Path) -> None:
    """Importing `probe_common` prints `vinci: <path>`, and the path is this checkout's."""
    env = {**os.environ, "ARCHETYPE_PROBE_WORK": str(tmp_path / "work"),
           "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("ARCHETYPE_PROBE_DOTENV", None)
    out = subprocess.run([sys.executable, "-c", "import probe_common"], cwd=PROBE, env=env,
                         capture_output=True, text=True, check=True).stdout
    first = out.splitlines()[0] if out else ""
    assert first.startswith("vinci: "), out
    assert Path(first[len("vinci: "):]).resolve().is_relative_to(ROOT), first


def test_the_shared_setup_refuses_a_work_folder_inside_the_checkout() -> None:
    """NEGATIVE: a work folder inside the checkout is refused, so no cache lands in it."""
    env = {**os.environ, "ARCHETYPE_PROBE_WORK": str(ROOT / "scratch-probe-work"),
           "PYTHONDONTWRITEBYTECODE": "1"}
    res = subprocess.run([sys.executable, "-c", "import probe_common"], cwd=PROBE, env=env,
                         capture_output=True, text=True)
    assert res.returncode != 0 and "OUTSIDE the checkout" in res.stderr
    assert not (ROOT / "scratch-probe-work").exists()


def test_the_archetype_rule_is_defined_once() -> None:
    defs = [p.name for p in SCRIPTS if re.search(r"^def grid_arch\(", p.read_text(), re.M)]
    assert defs == ["probe_common.py"], defs


def _load(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, PROBE / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_cut_page_says_it_was_cut() -> None:
    """`pdf_find.shown` states the cut, and leaves a short page whole."""
    pdf_find = _load("pdf_find")
    long = "x" * 4500
    cut = pdf_find.shown(long, 4000)
    assert cut.startswith("x" * 4000) and "4,000 of 4,500" in cut
    assert pdf_find.shown("short", 4000) == "short"
