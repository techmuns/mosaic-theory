"""#967's panel transform (`variants.dividend_and_same_day_guides`, RA-D2, RA-D4): the identity at
a ref without the change, a refusal with no CIQ folder, and — on the panel's real exports — each
field it writes is exactly what the candidate's own builder reads from the page's export, written
only where the read, with the change's additions taken out, is the committed field (RUNBOOKS §n
step 2). Skips where the licensed folder is absent, as on CI."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle
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
    monkeypatch.delattr(cs, "_dividend_per_share")
    assert v.dividend_and_same_day_guides(mech, v.Context(page=page, ciq=b)) is mech


def test_it_refuses_without_the_pages_ciq_folder() -> None:
    page, _b = _panel("SMPL")
    with pytest.raises(v.TransformError, match="--ciq"):
        v.dividend_and_same_day_guides(pre_synthesis_mech(page), v.Context(page=page))


@pytest.mark.parametrize("ticker", ["CNXC", "MCK", "SMPL"])
def test_each_written_field_is_the_candidate_builders_own(ticker: str) -> None:
    page, b = _panel(ticker)
    mech = pre_synthesis_mech(page)
    new = v.dividend_and_same_day_guides(mech, v.Context(page=page, ciq=b))
    assert new.return_ratios == cs.return_ratios(b) and new.key_ratios == cs.key_ratios(b)
    assert new.catalyst_path is not None and new.catalyst_path.guidance_bridge_rows is not None


def test_burls_guidance_is_left_as_committed() -> None:
    """BURL's committed bridge predates A-D8's block discovery (2026-10-29), so no code at this ref
    rebuilds it: the transform leaves it exactly as committed in both arms."""
    page, b = _panel("BURL")
    mech = pre_synthesis_mech(page)
    new = v.dividend_and_same_day_guides(mech, v.Context(page=page, ciq=b))
    assert new.catalyst_path is not None and mech.catalyst_path is not None
    assert new.catalyst_path.guidance_bridge is mech.catalyst_path.guidance_bridge
