"""RA-D2's panel transform (`variants.dividend_level`, split from #967): the identity at a ref
without the change, a refusal with no CIQ folder, and — on the panel's real exports — each field
it writes is exactly what the candidate's own builder reads from the page's export, written only
where the read, with the change's additions taken out, is the committed field (RUNBOOKS §n step 2).
Skips where the licensed folder is absent, as on CI."""
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
    assert v.dividend_level(mech, v.Context(page=page, ciq=b)) is mech


def test_it_refuses_without_the_pages_ciq_folder() -> None:
    page, _b = _panel("SMPL")
    with pytest.raises(v.TransformError, match="--ciq"):
        v.dividend_level(pre_synthesis_mech(page), v.Context(page=page))


@pytest.mark.parametrize("ticker", ["CNXC", "MCK", "SMPL", "BURL"])
def test_each_written_field_is_the_candidate_builders_own(ticker: str) -> None:
    """BURL and SMPL pay none and read 'NA': their key ratios move from "dividend: none" to "not
    stated" under the 'NA' ruling, and the stripping still proves the rest of the field."""
    page, b = _panel(ticker)
    mech = pre_synthesis_mech(page)
    new = v.dividend_level(mech, v.Context(page=page, ciq=b))
    assert new.return_ratios == cs.return_ratios(b) and new.key_ratios == cs.key_ratios(b)


def test_it_touches_no_guidance_field() -> None:
    """RA-D4 is measured on its own: this transform leaves the catalyst path as committed."""
    page, b = _panel("SMPL")
    mech = pre_synthesis_mech(page)
    assert v.dividend_level(mech, v.Context(page=page, ciq=b)).catalyst_path is mech.catalyst_path


def test_an_unknown_fields_note_is_compared_never_stripped() -> None:
    """(review) (+) Only a PRESENT table's own note is the change's: two UNKNOWN return ratios with
    different notes are different fields, so the transform never writes one over the other, and a
    field's note is compared as it stands. (−) Two present tables differing only in the TABLE's
    note, where the change writes its dividend notes, compare equal. Runs everywhere."""
    from vinci.dossier.schemas import FinRow, FinTable, Sourced

    a = Sourced[FinTable].unknown(note="Ratios: no Fiscal Period header")
    b = Sourced[FinTable].unknown(note="Ratios: no period columns")
    assert v._without_dividend(a) != v._without_dividend(b)
    t = FinTable(columns=["FY24"], rows=[FinRow(label="RoE %", cells=["1.0%"], values=[0.01])],
                 is_estimate=[False])
    p = Sourced[FinTable].present(t, source_ref="CIQ Financials→Ratios")
    q = Sourced[FinTable].present(t.model_copy(update={"note": "Dividend/sh: …"}),
                                  source_ref="CIQ Financials→Ratios")
    assert v._without_dividend(p) == v._without_dividend(q)
    r = Sourced[FinTable].present(t, source_ref="CIQ Financials→Ratios", note="not the change's")
    assert v._without_dividend(p) != v._without_dividend(r)
