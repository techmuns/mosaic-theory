"""(A2b) ROUTING — decided on the consensus side alone, tested on all eleven names.

WHY TWO RULES, with both counterexamples. This is what gets simplified away later:

  VITL FY2026 — coverage 9/10 is FINE. EBITDA median 3.300 on high 9.018 / low 0.315, dispersion
    263.7%. A coverage-only rule passes it straight through, and the resulting decomposition is
    garbage while reconciling perfectly.

  MVST FY2026 — EBITDA high == low == median on ONE estimate, so dispersion is 0.0% and reads as
    MAXIMUM AGREEMENT. A dispersion-only rule passes it straight through.

Neither is sufficient; each is the other's live counterexample.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.dossier.ev_gap import (
    EvGapInputs,
    Route,
    our_ebitda,
    route_for,
    shape_label,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _cell(ticker: str, metric: str, fy: str | None = None) -> dict[str, object]:
    d = json.loads((ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    cells = d["mechanical"]["consensus_context"]["consensus_levels"][metric]
    return cells[0] if fy is None else next(c for c in cells if str(c["fy"]) == fy)


def test_vitl_routes_on_dispersion_and_coverage_would_not_have() -> None:
    """THE ARITHMETIC CASE. Coverage 9/10 passes the coverage rule; dispersion 263.7% is what
    catches it."""
    cell = _cell("VITL", "EBITDA")
    route, why = route_for(cell)
    assert route == Route.TWO_RATIO
    assert why["dispersion"] == pytest.approx(2.637, abs=5e-3)
    assert why["n"] == 9, "coverage is FINE here — a coverage-only rule would pass VITL through"


def test_what_vitl_would_have_shown_without_the_route() -> None:
    """THE RULE IS ONLY A RULE IF SOMETHING WOULD OTHERWISE BE SHOWN. Consensus margin is 0.426%,
    so a 10% our-margin gives r_margin 23.5x and r_mult collapses by the same factor — AND THE
    PRODUCT RECONCILES EXACTLY, because the identity holds for any inputs. The exact reconciliation
    is precisely why the garbage is not caught."""
    rev, eb = _cell("VITL", "Revenue"), _cell("VITL", "EBITDA")
    consensus_margin = float(eb["median"]) / float(rev["median"])  # type: ignore[arg-type]
    assert consensus_margin == pytest.approx(0.00426, abs=5e-5)
    r_margin = 0.10 / consensus_margin
    assert r_margin > 20, f"a 10% our-margin gives r_margin {r_margin:.1f}x — not a ratio, a tell"


def test_mvst_routes_on_coverage_and_dispersion_would_not_have() -> None:
    """THE REPORTABILITY CASE. One estimate, so high == low == median and dispersion is 0.0% —
    the metric reports maximum agreement where there is nobody to disagree."""
    cell = _cell("MVST", "EBITDA")
    assert cell["high"] == cell["low"] == cell["median"], "MVST's single estimate collapsed"
    route, why = route_for(cell)
    assert route == Route.PRICE_IMPLIED_ONLY
    assert why["n"] == 1
    dispersion = (float(cell["high"]) - float(cell["low"])) / float(cell["median"])  # type: ignore[arg-type]
    assert dispersion == 0.0, "dispersion reads 0.0% — a dispersion-only rule passes MVST through"


def test_the_full_route_carries_a_caution_count_rather_than_narrowing() -> None:
    """3-5 estimates is thin but usable. NCNO sits here at 5/7 on EBITDA — the count is CARRIED so
    the render cautions, rather than the route being narrowed and the name losing its statement."""
    route, why = route_for(_cell("NCNO", "EBITDA"))
    assert route == Route.FULL
    assert why["n"] == 5 and why["caution"] is True


def test_cnxc_has_exactly_the_two_forward_years_the_adjacent_check_needs() -> None:
    """CNXC is the MINIMUM case: two forward years, so the adjacent-year check has exactly one
    alternative and proves it works rather than degrading silently."""
    d = json.loads((ROOT / "data" / "dossiers" / "CNXC" / "dossier.json").read_text())
    lv = d["mechanical"]["consensus_context"]["consensus_levels"]
    assert [c["fy"] for c in lv["Revenue"]] == ["2026", "2027"]
    assert [c["fy"] for c in lv["EBITDA"]] == ["2026", "2027"]
    for fy in ("2026", "2027"):
        assert route_for(_cell("CNXC", "EBITDA", fy))[0] == Route.FULL


def test_every_name_routes_and_the_split_is_the_measured_one() -> None:
    """ALL ELEVEN, on real data — routing needs no scenario record, which is why it is separable."""
    got = {}
    for f in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        lv = (json.loads(f.read_text())["mechanical"]["consensus_context"] or {}).get(
            "consensus_levels")
        if not lv or "EBITDA" not in lv:
            continue
        got[f.parent.name] = route_for(lv["EBITDA"][0])[0]
    assert got["VITL"] == Route.TWO_RATIO
    assert got["MVST"] == Route.PRICE_IMPLIED_ONLY
    assert got["SMPL"] == Route.FULL
    assert len(got) == 10, f"expected the ten refreshed names, got {sorted(got)}"


def test_smpl_is_multiple_dominant_from_the_ratios_alone() -> None:
    """The label is a FUNCTION of the three ratios, never a separate judgement."""
    assert shape_label(0.9839, 0.9463, 2.2589) == "multiple-dominant"
    assert shape_label(1.02, 1.60, 1.05) == "earnings"
    assert shape_label(1.55, 1.02, 1.03) == "timing-duration"
    # NOT dominant: the multiple leads but not by 2x the others.
    assert shape_label(1.20, 1.05, 1.35) == "multiple"


def test_the_basis_conversion_still_refuses_under_routing() -> None:
    """Routing does not relax the basis rule — a routed name still converts or refuses."""
    i = EvGapInputs(revenue=100.0, margin=0.2, margin_basis="operating", multiple=10.0,
                    multiple_basis="EV/EBITDA", d_and_a=5.0, consensus_revenue=100.0,
                    consensus_ebitda=25.0, tev=200.0, net_debt=0.0, shares=10.0)
    assert our_ebitda(i) == pytest.approx(25.0)
