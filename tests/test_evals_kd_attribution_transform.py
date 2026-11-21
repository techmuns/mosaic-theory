"""W85's panel transform (`variants.kd_attribution`): the identity at a ref without the change,
a refusal with no CIQ folder, a refusal when the folder's export is not the page's own, a refusal
when the attributed rows would move the page's catalyst calendar (which it does not rewrite), and
— on the panel's real exports, at a ref with W85's reader — each row's attribution is exactly what
the candidate's own builder reads from the page's export (RUNBOOKS §n step 2). The real-export
pin skips where the licensed folder is absent, as on CI, and at a ref without W85.

The frozen pages are the cut's (`tests/frozen_support`), so no pin reads a living page."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import Any

import pytest

from tests.frozen_support import frozen_doc
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import mechanical
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import MechanicalLayer
from vinci.evals import replay as rp
from vinci.evals import variants as v

_ROOT = Path("data/manual/ciq")
_KD = "CIQ Key Developments"


def _frozen(t: str) -> tuple[dict[str, Any], MechanicalLayer]:
    page = frozen_doc(t)
    return page, MechanicalLayer.model_validate(page["mechanical"])


def _with_reader(monkeypatch: pytest.MonkeyPatch, rows: list[Any]) -> None:
    """A ref WITH W85's reader, reading ``rows`` from the folder — so the refusals are pinned on
    main too, where the transform would otherwise stop at its identity check."""
    monkeypatch.setattr(cs, "kd_attribution", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(cs, "key_developments", lambda b: (rows, None))


def test_the_identity_at_a_ref_without_the_change(monkeypatch: pytest.MonkeyPatch) -> None:
    page, mech = _frozen("MCK")
    monkeypatch.delattr(cs, "kd_attribution", raising=False)
    assert v.kd_attribution(mech, v.Context(page=page)) is mech


def test_it_refuses_without_the_pages_ciq_folder(monkeypatch: pytest.MonkeyPatch) -> None:
    page, mech = _frozen("MCK")
    _with_reader(monkeypatch, [])
    with pytest.raises(v.TransformError, match="--ciq"):
        v.kd_attribution(mech, v.Context(page=page))


def test_it_refuses_an_export_that_is_not_the_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) A folder whose export lacks one of the page's rows is not the page's own."""
    page, mech = _frozen("MCK")
    assert mech.operating_drivers is not None
    kd = [r for r in mech.operating_drivers.rows if r.source_ref.startswith(_KD)]
    assert len(kd) > 1
    _with_reader(monkeypatch, kd[1:])
    with pytest.raises(v.TransformError, match=f"1 of the page's {len(kd)} Key Development rows"):
        v.kd_attribution(mech, v.Context(page=page, ciq=CiqBundle(ticker="MCK", workbooks=())))


def test_it_refuses_where_the_calendar_would_move(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) It does not rewrite the calendar, so a page whose calendar the attributed rows would
    move is refused rather than replayed as if it would not. (-) Nothing left off: it writes."""
    page, mech = _frozen("MCK")
    assert mech.operating_drivers is not None
    kd = [r for r in mech.operating_drivers.rows if r.source_ref.startswith(_KD)]
    _with_reader(monkeypatch, kd)
    ctx = v.Context(page=page, ciq=CiqBundle(ticker="MCK", workbooks=()))
    monkeypatch.setattr(mechanical, "_operating_events", lambda od, ref: ([], ["2027-01 …"]),
                        raising=False)
    with pytest.raises(v.TransformError, match="leave 1 dated event"):
        v.kd_attribution(mech, ctx)
    monkeypatch.setattr(mechanical, "_operating_events", lambda od, ref: ([], []), raising=False)
    assert v.kd_attribution(mech, ctx).operating_drivers is not None


def test_it_is_registered() -> None:
    assert v.TRANSFORMS["kd_attribution"] is v.kd_attribution
    assert v.W85 == ("kd_attribution",)


@pytest.mark.parametrize("ticker", ["BURL", "CNXC", "LLY", "MCK", "ROST", "SMPL"])
def test_each_row_s_attribution_is_the_candidate_builders_own(ticker: str) -> None:
    """(+) On each panel page, frozen, with its own CIQ folder: every Key Development row carries
    exactly the attribution `key_developments` reads for it, and no other field moves."""
    if getattr(cs, "kd_attribution", None) is None:
        pytest.skip("W85's reader is not on this ref")
    if not (_ROOT / ticker).is_dir():
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    with contextlib.redirect_stdout(io.StringIO()):
        page = rp.page_at(ticker, rp.load_panel_file()["freeze_ref"])
    b = CiqBundle.from_files(ticker, sorted(f for f in (_ROOT / ticker).iterdir()
                                            if f.is_file() and not f.name.startswith(".")))
    mech = MechanicalLayer.model_validate(page["mechanical"])
    new = v.kd_attribution(mech, v.Context(page=page, ciq=b))
    assert new.operating_drivers is not None and mech.operating_drivers is not None
    read = {v._kd_key(r): r for r in cs.key_developments(b)[0]}
    for old, row in zip(mech.operating_drivers.rows, new.operating_drivers.rows, strict=True):
        if old.source_ref.startswith(_KD):
            assert row.attribution == read[v._kd_key(old)].attribution
        assert row.model_copy(update={"attribution": None}) == old.model_copy(
            update={"attribution": None})
    assert new.model_copy(update={"operating_drivers": None}) == mech.model_copy(
        update={"operating_drivers": None})
