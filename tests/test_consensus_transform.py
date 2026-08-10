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

from tests.test_consensus_rows import REVENUE_BASELINE, _bundle, data_vintage
from vinci.dossier.refresh import CONSENSUS_METRICS, consensus_transform, refresh_dossier
from vinci.dossier.schemas import Dossier

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("ticker", ["SMPL", "EPAM", "VITL"])
def test_the_levels_reach_the_written_dossier(ticker: str, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """READ BACK, never compared to the extractor. The eleven-name baseline already verifies the
    extractor; what is unverified is whether the value lands."""
    bundle = _bundle(ticker)                          # skips if the CIQ bundle is unavailable
    src = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not src.is_file():
        pytest.skip(f"{ticker}: no committed dossier")
    work = tmp_path / "dossier.json"
    shutil.copy(src, work)
    shutil.copy(src.with_name("dossier.md"), tmp_path / "dossier.md")

    # NOT `is True`. The first cut asserted the refresh CHANGED something, which encoded
    # "before the fleet pass" as an invariant — and the fleet pass then made it false. What
    # matters is that the levels are IN the artifact, whether this write put them there or a
    # previous one did. The read-back is the assertion; `changed` is an implementation detail.
    refresh_dossier(work, transform=consensus_transform(ticker))

    # THE ARTIFACT, not the transform's return value.
    written = json.loads(work.read_text())
    levels = written["mechanical"]["consensus_context"]["consensus_levels"]
    assert levels is not None, f"{ticker}: consensus_levels never reached the artifact"
    assert set(levels) == set(CONSENSUS_METRICS)

    fy, median, pair, verified_at = REVENUE_BASELINE[ticker]
    first = levels["Revenue"][0]
    assert first["fy"] == fy
    # LANDING is what this test owns, and it stays strict: the row is present, carries the right
    # forward year, and both value fields survived the write as fields.
    assert first["estimates"], "the RAW pair did not survive the write"
    assert isinstance(first["median"], (int, float)), "median did not survive the write as a number"
    assert all(int(c["fy"]) >= int(fy) for c in levels["Revenue"]), "forward years only"

    # The EXACT numbers are gated on the export vintage for the same reason as the baseline this
    # imports from — they move when brokers revise. Shared helper, never a second copy of the
    # rule: two tests disagreeing about when a baseline is current is how one of them starts lying.
    vintage = data_vintage(bundle)
    if vintage is not None and vintage > verified_at:
        pytest.skip(
            f"{ticker}: export re-pulled since the baseline was verified (data ≥{vintage} > "
            f"pinned {verified_at}); landing assertions above still ran. Reads now: "
            f"median {first['median']!r}, pair {first['estimates']!r}")
    assert first["median"] == pytest.approx(median, rel=1e-3)
    assert first["estimates"] == pair, "the RAW pair must survive the write, not a re-derived count"

    # It must also survive VALIDATION — a dict that loads is not the same as a typed field.
    model = Dossier.model_validate_json(work.read_text())
    assert model.mechanical.consensus_context.consensus_levels is not None


def test_an_unrefreshed_dossier_reads_as_none_not_empty(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """`None` means NOT REFRESHED; `[]` would mean THE STREET HAS NO VIEW. Different claims, and
    the committed eleven are all in the first state until the fleet pass runs."""
    # FUBO, not AORT. AORT received the fleet pass; FUBO is sealed by its standing rule and is
    # therefore the ONLY name still in the unrefreshed state — which also makes it the only name
    # exercising omit-when-None on the write path.
    src = ROOT / "data" / "dossiers" / "FUBO" / "dossier.json"
    model = Dossier.model_validate_json(src.read_text())
    assert model.mechanical.consensus_context.consensus_levels is None


def test_a_broken_bundle_fails_loud_and_a_missing_one_skips(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """REVIEW FINDING (#312). The first cut caught bare `Exception` around the bundle load and
    returned `mech` unchanged for ANY failure — so a CORRUPT export made the fleet pass report
    success while silently injecting nothing. Nothing renders `consensus_levels` until A2, so that
    silence would have been invisible: #308's vanishing-marker defect in a new place.

    ABSENT and BROKEN are different states. Missing export -> skip. Anything else -> propagate."""
    import vinci.dossier.ciq as ciq_mod
    from vinci.dossier.refresh import consensus_transform

    mech = {"consensus_context": {"consensus_levels": None}}

    def _missing(*_a: object, **_k: object) -> object:
        raise FileNotFoundError("no export for this name")

    monkeypatch.setattr(ciq_mod.CiqBundle, "from_files", staticmethod(_missing))
    assert consensus_transform("NOPE")(mech) == mech, "a missing export must skip silently"

    def _corrupt(*_a: object, **_k: object) -> object:
        raise ValueError("workbook is truncated")

    monkeypatch.setattr(ciq_mod.CiqBundle, "from_files", staticmethod(_corrupt))
    with pytest.raises(ValueError, match="truncated"):
        consensus_transform("NOPE")(mech)


def test_every_dossier_carries_levels_except_the_standing_rule_exemptions() -> None:
    """EXEMPTIONS, NOT A ROSTER. A hardcoded list of ten lets a FUTURE name's absence pass
    silently — the roster would still be ten and still be green. Keyed on the reason instead, so
    a new dossier is in scope the day it lands and FUBO self-clears if its rule ever lifts.

    MVST IS CARRIED, DELIBERATELY. Its consensus is `2/2` on Revenue and `1/1` on EBITDA — thinly
    covered DATA, not absence. The extraction layer records; the render layer judges. Treating
    thin coverage as missing would delete the evidence that coverage is thin."""
    import json

    #: WHY each name is exempt — never a bare list. FUBO's record is sealed by its standing rule
    #: (STATE.md 2026-07-22) until a post-combination re-assembly exists, so it cannot receive A1.
    exempt = {"FUBO": "standing rule: no record written until a post-combination re-assembly"}

    missing = []
    for f in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        t = f.parent.name
        cc = json.loads(f.read_text())["mechanical"].get("consensus_context") or {}
        has = bool(cc.get("consensus_levels"))
        if t in exempt:
            assert not has, f"{t} carries levels but is exempt ({exempt[t]}) — the rule was broken"
            continue
        if not has:
            missing.append(t)
    assert not missing, (
        f"dossiers without consensus_levels and without an exemption: {missing} — either the "
        "fleet pass missed them, or they need an exemption recorded WITH ITS REASON")
