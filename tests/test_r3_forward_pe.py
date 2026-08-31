"""R3 — the forward-P/E recipe, and the first EQUITY-basis one.

R1 and R2 both build an ENTERPRISE value and subtract net debt to reach equity. A P/E multiple is
already an equity multiple: leverage sits inside the earnings. Everything distinctive about R3 is
what it therefore must NOT do, so most of these pins are refusals.
"""
from __future__ import annotations

import pytest

from vinci.scenarios import (
    BASIS_PE,
    RECIPE_R1,
    RECIPE_R3,
    AssumptionDerivation,
    Fact,
    ScenarioInput,
    ScenarioRecord,
    axes_for,
    run_recipe,
)

#: The IC memo's own frozen fundamental legs (2026-08-17 §7A) — EPS, multiple, and the value the
#: memo states. Used as the positive case because it was computed OUTSIDE this repo: reproducing it
#: tests the recipe against an independent arithmetic, not against itself.
MEMO_LEGS = {"bear": (15.388, 20.5, 315.45),
             "base": (16.221, 24.5, 397.41),
             "bull": (16.649, 26.0, 432.87)}


def _record(**over: object) -> ScenarioRecord:
    kw: dict[str, object] = {
        "ticker": "GOOGL",
        "recipe_id": RECIPE_R3,
        "recipe_desc": "forward P/E",
        "multiple_basis": BASIS_PE,
        "underwrite_date": "2026-08-17",
        "analyst": "operator",
        "spot": 345.90,
        "spot_source": "Aug-14-2026 completed regular-session close",
        "facts": {},
        "assumptions": {
            "earnings": AssumptionDerivation(
                method="normalized EPS on the ~Aug-2027 horizon"),
            "multiple": AssumptionDerivation(
                method="P/NTM turns; bear de-rates to 20.5x"),
        },
        "scenarios": {
            n: ScenarioInput(revenue=0.0, eps=e, multiple=m, reason=f"memo {n} leg")
            for n, (e, m, _) in MEMO_LEGS.items()
        },
    }
    kw.update(over)
    return ScenarioRecord(**kw)  # type: ignore[arg-type]


def test_it_reproduces_the_memo_that_was_computed_outside_this_repo() -> None:
    out = run_recipe(_record())
    for name, (_eps, _mult, stated) in MEMO_LEGS.items():
        got = out.result.per_scenario[name].value_per_share
        assert abs(got - stated) < 0.02, f"{name}: computed {got}, memo states {stated}"


def test_the_reward_risk_lands_on_the_ratio_the_memo_states_independently() -> None:
    """The memo reports ~1.69x at $345.90 and that it FAILS the asymmetry threshold. The recipe was
    built from the per-leg arithmetic and never from this ratio, so agreeing is real evidence."""
    r = run_recipe(_record()).result
    assert r.ratio is not None and abs(r.ratio - 1.69) < 0.01, r.ratio
    assert r.pass_fail == "FAIL"


def test_no_enterprise_output_is_invented_for_an_equity_leg() -> None:
    """A P/E leg produces no enterprise value and no equity TOTAL. Absent, never fabricated."""
    base = run_recipe(_record()).result.per_scenario["base"]
    assert base.ev is None and base.equity is None
    assert base.value_per_share is not None


# --- the refusals, which are most of what this recipe is ---------------------------------------


@pytest.mark.parametrize("fact", ["net_debt", "d_and_a", "diluted_shares"])
def test_an_enterprise_fact_is_refused_rather_than_ignored(fact: str) -> None:
    """DOUBLE-COUNTING IS THE FAILURE THIS GUARDS. Subtracting net debt from a P/E value counts
    leverage twice — it is already in the earnings. Refused rather than ignored, because a record
    carrying it is not an extra field: it is someone having believed this was an enterprise recipe,
    and a silent ignore lets that belief survive into the next record.
    """
    rec = _record(facts={fact: Fact(value=1.0, unit="$M", basis="test", source="test")})
    with pytest.raises(ValueError, match="ENTERPRISE recipe"):
        run_recipe(rec)


def test_an_enterprise_basis_is_refused() -> None:
    with pytest.raises(ValueError, match="EQUITY-basis recipe"):
        run_recipe(_record(multiple_basis="EV/EBITDA"))


def test_a_leg_without_eps_cannot_be_computed() -> None:
    legs = {n: ScenarioInput(revenue=0.0, eps=e, multiple=m, reason="x")
            for n, (e, m, _) in MEMO_LEGS.items()}
    legs["base"] = ScenarioInput(revenue=0.0, multiple=24.5, reason="no eps")
    with pytest.raises(ValueError, match="values a leg from its EPS"):
        run_recipe(_record(scenarios=legs))


def test_a_leg_stating_a_margin_is_refused() -> None:
    """EPS already contains the margin. A leg stating both shows a driver the value never reads —
    the same objection the EV/Revenue note makes against requiring a margin methodology on R2."""
    legs = {n: ScenarioInput(revenue=0.0, eps=e, multiple=m, reason="x")
            for n, (e, m, _) in MEMO_LEGS.items()}
    legs["base"] = ScenarioInput(revenue=0.0, eps=16.221, margin=0.36, multiple=24.5, reason="x")
    with pytest.raises(ValueError, match="already contains the margin"):
        run_recipe(_record(scenarios=legs))


def test_it_models_two_axes_and_neither_is_revenue_or_margin() -> None:
    """Requiring a revenue or margin methodology would ask the analyst to write up how they derived
    an input the arithmetic never reads."""
    assert axes_for(RECIPE_R3, BASIS_PE) == ("earnings", "multiple")
    assert axes_for(RECIPE_R1, "EV/EBITDA") == ("revenue", "margin", "multiple")


def test_the_stamped_formula_shows_the_two_steps_it_does_not_take() -> None:
    out = run_recipe(_record())
    assert out.recipe_formula == ["value/share = EPS × forward P/E multiple"]
    joined = " ".join(out.recipe_formula)
    assert "net debt" not in joined and "diluted shares" not in joined
