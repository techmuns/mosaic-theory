"""Step 8 verification — the scheduled orchestration (weekly screen, monthly score).

Network-marked end-to-end test: it copies the committed seed snapshots + the warm grouped-daily
cache into a temp data dir (so it neither mutates the repo nor re-pulls), then runs both jobs. Skips
cleanly where the local cache/seed isn't present (e.g. a fresh clone)."""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest

from mosaic.config import Config
from mosaic.orchestrator import run_monthly, run_weekly

_REPO_DATA = Path("data")


@pytest.mark.network
def test_run_weekly_then_monthly(tmp_path: Path) -> None:
    if not (_REPO_DATA / "snapshots").exists() or not (_REPO_DATA / "cache").exists():
        pytest.skip("no local seed snapshots / warm cache (fresh clone)")
    shutil.copytree(_REPO_DATA / "snapshots", tmp_path / "snapshots")
    shutil.copytree(_REPO_DATA / "cache", tmp_path / "cache")
    cfg = Config(data_dir=tmp_path)

    weekly = run_weekly(cfg, end=date(2026, 6, 12))
    assert weekly["universe"] == 9  # the seeded thin universe
    assert isinstance(weekly["candidates"], int) and weekly["candidates"] >= 1  # NKE at minimum

    # lookback_days kept within the warm cache window (the seed cache starts 2025-05-01)
    monthly = run_monthly(cfg, as_of=date(2026, 6, 12), lookback_days=380)
    assert "buy_avoid_spread" in monthly  # report shape
    assert (tmp_path / "snapshots" / "scoring_report.md").exists()
