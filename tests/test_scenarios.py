"""Versioned scenario records — schema, round-trip, recipe run, and the unit guards.

Pins: the record round-trips byte-stably; the recipe REFUSES a mismatched multiple_basis or a
missing source-bound fact (never assumes); the machine records PASS/FAIL honestly and never moves
the verdict off ``pending_analyst``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from vinci import scenarios as sc


def _rec(**over: object) -> sc.ScenarioRecord:
    base = {
        "ticker": "TEST", "recipe_id": sc.RECIPE_R1,
        "recipe_desc": "mid-cycle operating margin x exit EV/EBITDA",
        "multiple_basis": "EV/EBITDA", "underwrite_date": "2026-07-19", "analyst": "tester",
        "spot": 46.0, "spot_source": "test",
        "facts": {
            "d_and_a": sc.Fact(value=286.321, unit="$M", basis="consolidated FY2025",
                               source="10-K"),
            "net_debt": sc.Fact(value=979.776, unit="$M", basis="incl leases", source="10-Q"),
            "diluted_shares": sc.Fact(value=59.91, unit="M shares", basis="Q1-2026", source="10-Q"),
        },
        "scenarios": {
            "bear": sc.ScenarioInput(revenue=2850.0, margin=0.015, multiple=6.0, reason="trough"),
            "base": sc.ScenarioInput(revenue=3100.0, margin=0.0625, multiple=6.5, reason="mid"),
            "bull": sc.ScenarioInput(revenue=3400.0, margin=0.080, multiple=7.0, reason="turn"),
        },
    }
    base.update(over)
    return sc.ScenarioRecord(**base)  # type: ignore[arg-type]


def test_record_roundtrips(tmp_path: Path) -> None:
    rec = _rec()
    p = sc.write_record(rec, root=tmp_path)
    back = sc.read_record("TEST", root=tmp_path)
    assert back == rec
    assert p.read_text().endswith("\n")                 # newline-terminated, diff-able
    assert sc.all_records(root=tmp_path)["TEST"] == rec


def test_schema_file_excluded_from_records(tmp_path: Path) -> None:
    sc.write_record(_rec(), root=tmp_path)
    sc.write_json_schema(root=tmp_path)
    assert (tmp_path / "scenarios" / "_schema.json").exists()
    assert list(sc.all_records(root=tmp_path)) == ["TEST"]   # `_schema.json` is not a record


def test_recipe_computes_on_ebitda_and_records_fail() -> None:
    """The WERN shape: reward negative at spot → an honest FAIL, recorded not hidden."""
    out = sc.run_recipe(_rec())
    per = out.result.per_scenario
    assert per["base"].ebitda == pytest.approx(480.071)      # EBIT 193.75 + D&A 286.321
    assert per["base"].value_per_share == pytest.approx(35.73, abs=0.02)
    assert per["bear"].value_per_share == pytest.approx(16.60, abs=0.02)
    assert per["bull"].value_per_share == pytest.approx(48.88, abs=0.02)
    assert out.result.reward == pytest.approx(-10.27, abs=0.02)
    assert out.result.risk == pytest.approx(29.40, abs=0.02)
    assert out.result.ratio == pytest.approx(-0.349, abs=0.005)
    assert out.result.pass_fail == "FAIL" and out.result.bar == 2.0
    # the machine records, it does NOT ratify
    assert out.verdict.status == "pending_analyst" and out.verdict.recorded is None


def test_recipe_refuses_mismatched_basis() -> None:
    with pytest.raises(ValueError, match="multiple_basis"):
        sc.run_recipe(_rec(multiple_basis="EV/EBIT"))


def test_recipe_refuses_missing_fact() -> None:
    r = _rec()
    facts = {k: v for k, v in r.facts.items() if k != "d_and_a"}
    with pytest.raises(ValueError, match="d_and_a"):
        sc.run_recipe(r.model_copy(update={"facts": facts}))


def test_recipe_refuses_unknown_recipe() -> None:
    with pytest.raises(ValueError, match="unknown recipe_id"):
        sc.run_recipe(_rec(recipe_id="R9_not_a_recipe"))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
