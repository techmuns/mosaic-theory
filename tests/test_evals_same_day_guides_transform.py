"""RA-D4's panel transform (`variants.same_day_guides`, split from #967): the identity at a ref
without the change, a refusal with no CIQ folder, and — on the panel's real exports — each field
it writes is exactly what the candidate's own builder reads from the page's export, written only
where the read, with the change's additions taken out, is the committed field (RUNBOOKS §n step 2).
Skips where the licensed folder is absent, as on CI."""
from __future__ import annotations

import contextlib
import io
from datetime import date
from pathlib import Path

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import mechanical
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import Sourced
from vinci.evals import builds as bd
from vinci.evals import replay as rp
from vinci.evals import variants as v
from vinci.evals.capture_child import pre_synthesis_mech

_ROOT = Path("data/manual/ciq")


def _panel(t: str) -> tuple[dict[str, object], CiqBundle]:
    if not (_ROOT / t).is_dir():
        pytest.skip(f"licensed CIQ bundle for {t} unavailable (never committed)")
    with contextlib.redirect_stdout(io.StringIO()):
        page, _tx = rp.panel_inputs(t, ciq_root=_ROOT)
        b = CiqBundle.from_files(t, sorted(f for f in (_ROOT / t).iterdir()
                                           if f.is_file() and not f.name.startswith(".")))
    return page, b


def test_the_identity_at_a_ref_without_the_change(monkeypatch: pytest.MonkeyPatch) -> None:
    page, b = _panel("SMPL")
    mech = pre_synthesis_mech(page)
    monkeypatch.setattr(cs, "_GuidanceRead", type("Old", (), {"_fields": ("period",)}))
    assert v.same_day_guides(mech, v.Context(page=page, ciq=b)) is mech


def test_it_refuses_without_the_pages_ciq_folder() -> None:
    page, _b = _panel("SMPL")
    with pytest.raises(v.TransformError, match="--ciq"):
        v.same_day_guides(pre_synthesis_mech(page), v.Context(page=page))


@pytest.mark.parametrize("ticker", ["CNXC", "MCK", "SMPL"])
def test_each_written_field_is_the_candidate_builders_own(ticker: str) -> None:
    page, b = _panel(ticker)
    mech = pre_synthesis_mech(page)
    new = v.same_day_guides(mech, v.Context(page=page, ciq=b))
    cp, si = new.catalyst_path, mech.stock_info
    assert cp is not None and si is not None and si.as_of
    ref = date.fromisoformat(str(page["reference_date"])[:10])
    cut = date.fromisoformat(str(si.as_of)[:10])
    assert cp.guidance_bridge_rows == cs.guidance_bridge_rows(
        b, reference_date=ref, stale_after_days=mechanical._STALE_CLOSE_DAYS, cut=cut)
    # (review) the bridge is the other field written, and was pinned nowhere
    assert cp.guidance_bridge == cs.guidance_bridge(
        b, as_of=cs.estimates_as_of(b).value, reference_date=ref,
        stale_after_days=mechanical._STALE_CLOSE_DAYS, cut=cut)


def test_burls_guidance_is_left_as_committed() -> None:
    """BURL's committed bridge predates A-D8's block discovery (2026-10-29), so no code at this ref
    rebuilds it: the transform leaves it exactly as committed in both arms."""
    page, b = _panel("BURL")
    mech = pre_synthesis_mech(page)
    new = v.same_day_guides(mech, v.Context(page=page, ciq=b))
    assert new.catalyst_path is not None and mech.catalyst_path is not None
    assert new.catalyst_path.guidance_bridge is mech.catalyst_path.guidance_bridge


def test_it_touches_no_dividend_field() -> None:
    """RA-D2 is measured on its own: this transform leaves the ratios as committed."""
    page, b = _panel("SMPL")
    mech = pre_synthesis_mech(page)
    new = v.same_day_guides(mech, v.Context(page=page, ciq=b))
    assert new.return_ratios is mech.return_ratios and new.key_ratios is mech.key_ratios


def test_the_addition_on_the_last_segment_stops_at_the_as_of_suffix() -> None:
    """(review) The bridge ends in its as-of suffix ("  [as-of …]", no "; " before it), so a
    same-day list on the LAST metric took the suffix with it, and the field went unwritten."""
    seg = "Revenue: latest guide '322.00 - 332.00' for FQ4 2026 (dated 2026-07-09)"
    new = Sourced.present(seg + "; same day: '1,345.00 - 1,355.00' for FY 2026  [as-of 2026-11-04]",
                          source_ref="x")
    old = Sourced.present(seg + "  [as-of 2026-11-04]", source_ref="x")
    assert v._bridge_primary(new) == v._bridge_primary(old)
    mid = Sourced.present(seg + "; same day: '1 - 2' for FY 2026; most recent guidance outcome: "
                          "FQ3 2026 MET", source_ref="x")
    assert v._bridge_primary(mid) == v._bridge_primary(Sourced.present(
        seg + "; most recent guidance outcome: FQ3 2026 MET", source_ref="x"))


def test_a_build_registration_hands_the_child_the_pages_ciq_folder(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """(review) `register-run` captured without `--ciq`, so this transform refused every page."""
    (tmp_path / "SMPL").mkdir()
    seen: dict[str, object] = {}
    monkeypatch.setattr(rp, "panel_inputs", lambda t, **k: ({}, None))
    monkeypatch.setattr(rp, "comps_export", lambda t, **k: None)
    monkeypatch.setattr(rp, "capture_at", lambda *a, **k: seen.update(k))
    bd.capture_request("HEAD", "SMPL", transforms=["same_day_guides"], draws=1, ciq_root=tmp_path)
    assert seen["ciq"] == tmp_path / "SMPL"
    bd.capture_request("HEAD", "SMPL", transforms=[], draws=1, ciq_root=tmp_path)
    assert seen["ciq"] is None
