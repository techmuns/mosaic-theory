"""The two measure scripts hold back no name (operator ruling 2026-11-05, #919; #922's precedent).

`scripts/debt_maturity_moves.py` and `scripts/ads_ratio_moves.py` REQUIRED a `--skip-file` of held
test-pack tickers from before the ruling: "mosaic-theory holds back no name" (document 15 §4 says
the same). A required list nobody holds made each run invent an empty file. Now neither takes one,
and — as #922 refused a copied `--exclude` — a copied command that still passes `--skip-file` is
refused by argparse before anything is read.
"""
from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("script", ["debt_maturity_moves.py", "ads_ratio_moves.py"])
def test_a_copied_skip_file_is_refused(script: str, tmp_path: Path) -> None:
    skip = tmp_path / "skip.txt"
    skip.write_text("")
    own = (["--types-cache", str(tmp_path), "--types-date", "2026-10-17"]
           if script == "ads_ratio_moves.py" else [])
    got = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), "--cache-dir", str(tmp_path), *own,
         "--out", str(tmp_path / "out.json"), "--skip-file", str(skip)],
        capture_output=True, text=True, cwd=ROOT, env={"PYTHONPATH": str(ROOT)}, timeout=120)
    assert got.returncode == 2, got.stderr[-500:]
    assert "unrecognized arguments: --skip-file" in got.stderr


@pytest.mark.parametrize("module", ["debt_maturity_moves", "ads_ratio_moves"])
def test_the_run_takes_no_skip(module: str) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        mod = __import__(module)
    finally:
        sys.path.pop(0)
    params = inspect.signature(mod.run).parameters
    assert not {"skip", "skip_ciks"} & set(params), list(params)
    assert not hasattr(mod, "held_ciks")
