"""W81's panel transform on main (`variants.w81_ebitda_names`, #1147's measurement): it is
registered, and it is the IDENTITY wherever `ev_ebitda_basis` has no `FOUR_QUARTER` — main, until
#1147 merges. So the harness can carry it while main's production code and the scorer fingerprint
stay exactly as they are (RUNBOOKS §n, RG-D12: a registration runs on origin/main's harness).

The name is removed for the test, so the pin holds on #1147's head too, where the full transform
tests (`tests/test_evals_w81_transform.py`) pin what it writes. Real pages, as frozen at the cut."""
from __future__ import annotations

import pytest

from tests.frozen_support import frozen_doc
from vinci.dossier import ev_ebitda_basis as eb
from vinci.dossier.schemas import MechanicalLayer
from vinci.evals import variants as v

PANEL = ("BURL", "CNXC", "LLY", "MCK", "ROST", "SMPL")


def test_it_is_registered() -> None:
    assert v.TRANSFORMS["w81_ebitda_names"] is v.w81_ebitda_names
    assert v.W81 == ("w81_ebitda_names",)


@pytest.mark.parametrize("t", PANEL)
def test_the_identity_where_the_w81_names_do_not_exist(t: str,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) With no `ev_ebitda_basis.FOUR_QUARTER`, each panel page's layer comes back as the very
    object it went in as: nothing read, nothing written."""
    monkeypatch.delattr(eb, "FOUR_QUARTER", raising=False)
    page = frozen_doc(t)
    mech = MechanicalLayer.model_validate(page["mechanical"])
    assert v.w81_ebitda_names(mech, v.Context(page=page)) is mech
