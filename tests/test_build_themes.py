"""Pin the theme viewer's build.py display-transform to the backend it MIRRORS.

frontend/build.py stays stdlib-only (deploy-safe — Cloudflare Pages runs it with no pydantic/vinci),
so it re-declares the zero-RATIFIED honesty label, the UNDEFINED-spread reasons, and the driver-tie
gate as literals. This test runs where the backend IS importable and asserts those literals have NOT
drifted from vinci.themes.forward / vinci.themes.exposure — the honest-framing strings are
load-bearing (the viewer must not oversell the theme edge), so a silent divergence is a real defect.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from vinci.themes.exposure import _BASIS_FOR, _effective_rank
from vinci.themes.forward import HOLD_NONE_HONESTY, FrozenBaskets, undefined_ratified_measures
from vinci.themes.schemas import DriverTie, ExposureConcreteness

_BUILD_PY = Path(__file__).resolve().parents[1] / "frontend" / "build.py"


def _load_build() -> Any:
    """Load frontend/build.py by path (frontend/ is not a package). Importing does NOT run main()
    (guarded by __main__), and the module body does only path math — no I/O."""
    spec = importlib.util.spec_from_file_location("_viewer_build", _BUILD_PY)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_BUILD: Any = _load_build()


def test_honesty_label_matches_backend() -> None:
    assert _BUILD._HOLD_NONE_HONESTY == HOLD_NONE_HONESTY


def test_undefined_measures_match_backend() -> None:
    baskets = FrozenBaskets(
        driver="d", freeze_timestamp="2026-07-03T00:00:00", ratified=(), passed=("A",),
        all_committed=("A",), entry_dates={"A": "2026-07-03"}, layer_of={"A": "x"})
    backend = [[m, r] for m, r in undefined_ratified_measures(baskets)]
    assert backend == _BUILD._UNDEFINED_MEASURES
    # and the empty BUY leg is what makes them undefined (guards the premise)
    assert baskets.ratified == ()


def test_tie_gate_matches_backend() -> None:
    """build._eff_basis(grade, tie) must equal the backend's _BASIS_FOR[_effective_rank(...)] for
    every (concreteness, tie) — so the viewer's tier shape derives identically to exposure_basis."""
    for conc in ExposureConcreteness:
        for tie in DriverTie:
            backend_basis = _BASIS_FOR[_effective_rank(conc, tie)].value  # e.g. committed-capacity…
            short = _BUILD._eff_basis(conc.value, tie.value)
            # map the backend's long ExposureBasis to the viewer's short bucket for comparison
            expect = {
                "binding-contracts-with-terms": "binding",
                "quantified-revenue-share": "quantified",
                "committed-capacity-or-capex": "committed",
                "aspirational-intent-only": "aspirational",
                "no-theme-exposure-disclosed": "none",
            }[backend_basis]
            assert short == expect, f"tie-gate drift at ({conc.value}, {tie.value})"


def test_eff_basis_caps_by_tie() -> None:
    # a binding-contract fact: driver-specific keeps it binding, indirect caps at committed,
    # not-driver caps at aspirational (the direction the tie gate encodes)
    assert _BUILD._eff_basis("binding-contract", "driver-specific") == "binding"
    assert _BUILD._eff_basis("binding-contract", "indirect") == "committed"
    assert _BUILD._eff_basis("binding-contract", "not-driver") == "aspirational"


def test_edgar_url_shape() -> None:
    u = _BUILD._edgar_url("0001493152", "0001493152-26-022095")
    assert u == ("https://www.sec.gov/Archives/edgar/data/1493152/"
                 "000149315226022095/0001493152-26-022095-index.htm")
    assert _BUILD._edgar_url("0001493152", "no accession here") is None  # no accession → no link


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
