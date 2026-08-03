"""A1's transform — asserted BY READING BACK FROM THE WRITTEN ARTIFACT.

#310's DEFECT, NOT REPEATED. There, the pin exercised the helper and never asserted the field was
ON the row: the value was computed and had nowhere to go, and the suite stayed green. Here the
failure mode is identical in shape — the transform runs, the extractor works, and the value never
reaches `consensus_context`. Comparing the transform's output to the extractor's would pass
straight through that.

So every assertion below reads the value back out of a dossier.json this test wrote. Nothing
renders `consensus_levels` until A2, which makes this the ONLY thing between a working transform
and a silent no-op.
"""
from __future__ import annotations

import json
import shutil

import pytest

from tests.test_consensus_rows import REVENUE_BASELINE, _bundle
from vinci.dossier.refresh import CONSENSUS_METRICS, consensus_transform, refresh_dossier
from vinci.dossier.schemas import Dossier

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("ticker", ["SMPL", "EPAM", "VITL"])
def test_the_levels_reach_the_written_dossier(ticker: str, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """READ BACK, never compared to the extractor. The eleven-name baseline already verifies the
    extractor; what is unverified is whether the value lands."""
    _bundle(ticker)                                   # skips if the CIQ bundle is unavailable
    src = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not src.is_file():
        pytest.skip(f"{ticker}: no committed dossier")
    work = tmp_path / "dossier.json"
    shutil.copy(src, work)
    shutil.copy(src.with_name("dossier.md"), tmp_path / "dossier.md")

    assert refresh_dossier(work, transform=consensus_transform(ticker)) is True

    # THE ARTIFACT, not the transform's return value.
    written = json.loads(work.read_text())
    levels = written["mechanical"]["consensus_context"]["consensus_levels"]
    assert levels is not None, f"{ticker}: consensus_levels never reached the artifact"
    assert set(levels) == set(CONSENSUS_METRICS)

    fy, median, pair = REVENUE_BASELINE[ticker]
    first = levels["Revenue"][0]
    assert first["fy"] == fy
    assert first["median"] == pytest.approx(median, rel=1e-3)
    assert first["estimates"] == pair, "the RAW pair must survive the write, not a re-derived count"
    assert all(int(c["fy"]) >= int(fy) for c in levels["Revenue"]), "forward years only"

    # It must also survive VALIDATION — a dict that loads is not the same as a typed field.
    model = Dossier.model_validate_json(work.read_text())
    assert model.mechanical.consensus_context.consensus_levels is not None


def test_an_unrefreshed_dossier_reads_as_none_not_empty(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """`None` means NOT REFRESHED; `[]` would mean THE STREET HAS NO VIEW. Different claims, and
    the committed eleven are all in the first state until the fleet pass runs."""
    src = ROOT / "data" / "dossiers" / "AORT" / "dossier.json"
    model = Dossier.model_validate_json(src.read_text())
    assert model.mechanical.consensus_context.consensus_levels is None
