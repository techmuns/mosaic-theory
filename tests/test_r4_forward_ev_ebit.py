"""R4 — the EV/NTM EBIT recipe (operator ruling 2026-10-08).

value/share = (NTM EBIT at exit × EV/NTM EBIT − net debt at exit) ÷ diluted shares. The multiple is
CIQ's, so the bridge is CIQ's net debt; it is carried to the exit by the operator's rule (a reliable
same-basis consensus where one exists, else today's figure held). Non-operating investments stay
inside the multiple. Two axes, `ebit` and `multiple`.

The positive pins run on REAL inputs frozen from the committed pages (main @55762d9f,
2026-10-08): the NTM EV/EBIT and FY2028 EBIT consensus from `forward_consensus`, CIQ's net debt as
the page's implied-valuation bridge (Total Debt − Total Cash & ST Investments), and the anchor's
diluted shares.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier.propose import (
    ProposalRefusedError,
    check_tier_agreement,
    record_legs_for_validation,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: (NTM EV/EBIT, FY2028 EBIT $M, CIQ total debt $M, CIQ cash & ST investments $M, diluted shares M)
#: read off each committed page — AMZN on Estimates ≥2026-10-06 (e10ed62223), UBER ≥2026-08-05
#: (265b3a9f59); the balance sheets are CIQ's Q2 Jun-30-2026.
PAGE = {
    "AMZN": (23.3376710756376, 183485.95, 251635.0, 122988.0, 10903.0),
    "UBER": (15.4268429712723, 13161.67, 14731.0, 5391.0, 2050.225),
}


def _record(ticker: str = "AMZN", *, legs: dict[str, dict[str, Any]] | None = None,
            facts: dict[str, sc.Fact] | None = None, **over: Any) -> sc.ScenarioRecord:
    mult, ebit, debt, cash, shares = PAGE[ticker]
    kw: dict[str, Any] = {
        "ticker": ticker, "recipe_id": sc.RECIPE_R4, "recipe_desc": "forward EV/NTM EBIT",
        "multiple_basis": sc.BASIS_EV_NTM_EBIT, "underwrite_date": "2026-10-08",
        "analyst": "test", "spot": 256.29, "spot_source": "test",
        "facts": facts if facts is not None else {
            "net_debt": sc.Fact(value=debt - cash, unit="$M", basis="CIQ net debt held to exit",
                                source="CIQ balance sheet Q2 Jun-30-2026"),
            "diluted_shares": sc.Fact(value=shares, unit="M shares", basis="diluted WA",
                                      source="EDGAR")},
        "assumptions": {"ebit": sc.AssumptionDerivation(method="FY2028 consensus EBIT"),
                        "multiple": sc.AssumptionDerivation(method="displaced from today's")},
        "scenarios": {n: sc.ScenarioInput(**{"multiple": mult, "ebit": ebit,
                                             "reason": f"{n} leg", "years_to_terminal": 1.25,
                                             **(legs or {}).get(n, {})})
                      for n in ("bear", "base", "bull")},
    }
    kw.update(over)
    return sc.ScenarioRecord(**kw)


# --- the arithmetic, on real inputs -------------------------------------------------------------

@pytest.mark.parametrize("ticker", sorted(PAGE))
def test_the_hold_leg_values_todays_multiple_on_exit_ebit_through_the_ciq_bridge(
    ticker: str,
) -> None:
    """AMZN: 23.34x × $183,486M − $128,647M, ÷ 10,903M shares = $380.95. Units are the whole risk
    here — $M over millions of shares is $/share with no scale factor, the R1 convention."""
    mult, ebit, debt, cash, shares = PAGE[ticker]
    out = sc.run_recipe(_record(ticker)).result.per_scenario["bull"]
    assert out.value_per_share == pytest.approx((mult * ebit - (debt - cash)) / shares, abs=1e-4)
    if ticker == "AMZN":
        assert out.value_per_share == pytest.approx(380.95, abs=0.01)


def test_an_enterprise_leg_carries_its_enterprise_figures() -> None:
    """Unlike R3, R4 builds an EV and an equity total — a leg walks from driver to value."""
    mult, ebit, debt, cash, shares = PAGE["AMZN"]
    out = sc.run_recipe(_record()).result.per_scenario["base"]
    assert out.op_income == pytest.approx(ebit) and out.ev_ebit == pytest.approx(mult, abs=1e-4)
    assert out.ev == pytest.approx(mult * ebit, abs=0.01)
    assert out.equity == pytest.approx(mult * ebit - (debt - cash), abs=0.01)
    assert out.ebitda is None, "no EBITDA is invented for an EBIT recipe"


def test_the_formula_is_stamped_and_the_axes_are_ebit_and_multiple() -> None:
    out = sc.run_recipe(_record())
    assert out.recipe_formula == list(sc.R4_FORMULA)
    assert sc.axes_for(sc.RECIPE_R4, sc.BASIS_EV_NTM_EBIT) == ("ebit", "multiple")
    assert sc.axes_for(sc.RECIPE_R3, sc.BASIS_PE) == ("earnings", "multiple"), (
        "R3's `earnings` axis is EPS — R4 must not share the name")


# --- the refusals -------------------------------------------------------------------------------

def _refuses(match: str, **kw: Any) -> None:
    with pytest.raises(ValueError, match=match):
        sc.run_recipe(_record(**kw))


def test_it_refuses_any_other_multiple_basis() -> None:
    _refuses("is not 'EV/NTM EBIT'", multiple_basis=sc.BASIS_PE)


def test_it_refuses_a_leg_without_ebit() -> None:
    _refuses("without one cannot be computed", legs={"base": {"ebit": None}})


def test_it_refuses_a_non_positive_ebit() -> None:
    _refuses("POSITIVE NTM EBIT", legs={"bear": {"ebit": -5.0}})


@pytest.mark.parametrize("field,val", [("eps", 13.27), ("revenue", 1_015_580.7), ("margin", 0.18)])
def test_it_refuses_a_driver_the_value_never_reads(field: str, val: float) -> None:
    _refuses(f"stating {field}", legs={"base": {field: val}})


def test_it_refuses_a_d_and_a_fact() -> None:
    base = _record().facts
    _refuses("belongs to an EBITDA recipe", facts={**base, "d_and_a": sc.Fact(
        value=75200.0, unit="$M", basis="FY2025", source="EDGAR")})


@pytest.mark.parametrize("missing", ["net_debt", "diluted_shares"])
def test_it_refuses_to_assume_a_bridge_fact(missing: str) -> None:
    facts = {k: v for k, v in _record().facts.items() if k != missing}
    _refuses(f"needs fact '{missing}'", facts=facts)


def test_it_refuses_a_misstated_formula() -> None:
    _refuses("does not match R4_FORMULA",
             recipe_formula=["value/share = EPS × forward P/E multiple"])


# --- reachable: the create path, the supersede guard, the tier gate ---------------------------

def test_scenario_create_writes_an_r4_record_end_to_end(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE PATH THAT CREATES RECORDS, run for real (2026-10-08). The first cut built every leg
    without `ebit`, so `_run_r4` refused every R4 template — the unwired-capability class R3's
    create path was found in. AMZN's committed page is copied with its tag set to R4 (the re-tag an
    operator makes), and a template built from its real figures goes through `scenario-create`."""
    from vinci.cli import _cmd_scenario_create

    page = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    page["anchor"]["recipe_hint"] = sc.RECIPE_R4
    (tmp_path / "data" / "dossiers" / "AMZN").mkdir(parents=True)
    (tmp_path / "data" / "dossiers" / "AMZN" / "dossier.json").write_text(json.dumps(page))
    (tmp_path / "scenarios").mkdir()
    mult, ebit, debt, cash, shares = PAGE["AMZN"]
    leg = {"multiple": round(mult, 4), "ebit": ebit, "reason": "hold today's multiple",
           "years_to_terminal": 1.25, "leg_fy": "FY2028",
           "ebit_derivation": "FY2028 consensus EBIT, the NTM year at an end-2027 exit",
           "multiple_derivation": "today's NTM EV/EBIT held"}
    tpl = {"ticker": "AMZN", "recipe_id": sc.RECIPE_R4, "multiple_basis": sc.BASIS_EV_NTM_EBIT,
           "entry_basis": "NTM", "entry_denominator": 123966.0,
           "underwrite_date": "2026-10-08", "analyst": "test", "spot": 256.29,
           "spot_source": "test", "spot_as_of": "2026-10-06",
           "facts": {"net_debt": {"value": debt - cash, "unit": "$M", "basis": "net debt held",
                                  "source": "balance sheet Q2 Jun-30-2026"},
                     "diluted_shares": {"value": shares, "unit": "M shares",
                                        "basis": "diluted WA", "source": "10-Q"}},
           "scenarios": {"bear": {**leg, "bear_basis": "analyst"}, "base": dict(leg),
                         "bull": dict(leg)}}
    src = tmp_path / "tpl.json"
    src.write_text(json.dumps(tpl))
    monkeypatch.chdir(tmp_path)
    assert _cmd_scenario_create(argparse.Namespace(ticker="AMZN", from_file=str(src))) == 0
    rec = json.loads((tmp_path / "scenarios" / "AMZN.json").read_text())
    assert rec["recipe_id"] == sc.RECIPE_R4 and rec["recipe_formula"] == list(sc.R4_FORMULA)
    assert all(leg["ebit"] == ebit for leg in rec["scenarios"].values())
    assert set(rec["assumptions"]) == {"ebit", "multiple"}


def test_the_supersede_guard_sees_the_ebit_axis() -> None:
    legs = record_legs_for_validation(_record(), axes=sc.axes_for(sc.RECIPE_R4, None))
    assert legs["base"]["ebit"] == PAGE["AMZN"][1]
    assert legs["base"]["ebit_derivation"] == "FY2028 consensus EBIT"


def _page(ticker: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(
        (ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    return doc


def test_a_record_across_the_pages_forward_recipe_is_refused() -> None:
    """AMZN's page carries the operator's R3 tag; an R4 record must not be written across it
    until the page is re-tagged — the first cut let it through, because the gate only knew R1."""
    with pytest.raises(ProposalRefusedError, match="disagrees with record recipe"):
        check_tier_agreement(_page("AMZN"), sc.RECIPE_R4)
    doc = _page("AMZN")
    doc["anchor"]["recipe_hint"] = sc.RECIPE_R4
    with pytest.raises(ProposalRefusedError, match="disagrees with record recipe"):
        check_tier_agreement(doc, sc.RECIPE_R3)


def test_a_record_on_the_pages_own_recipe_passes() -> None:
    check_tier_agreement(_page("GOOGL"), sc.RECIPE_R3)
    doc = _page("AMZN")
    doc["anchor"]["recipe_hint"] = sc.RECIPE_R4
    check_tier_agreement(doc, sc.RECIPE_R4)


def test_a_record_without_ebit_writes_no_ebit_key(tmp_path: pathlib.Path) -> None:
    """Absent, never null: GOOGL's committed R3 record round-trips with no `ebit` key."""
    committed = (ROOT / "scenarios" / "GOOGL.json").read_text()
    rec = sc.ScenarioRecord.model_validate_json(committed)
    path = sc.write_record(rec, root=tmp_path)
    assert '"ebit"' not in path.read_text()
