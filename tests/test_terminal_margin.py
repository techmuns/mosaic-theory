"""Tests for the R2 terminal-margin engine (vinci.dossier.terminal_margin).

R2 exists because R1 needs a history worth reverting to and the R2 cohort has none. What it adds
over R1 — a discount, a projected share count, a projected net debt, and a survival gate — is
exactly what these tests pin, because each is a place a pre-profit name can be flattered.

The two unit traps are pinned by MAGNITUDE, not by "is not None": both bugs found on 2026-07-21
(the anchor passing EDGAR dollars into a $M guard, and this engine dividing $M by a raw share
count) produced numbers that were silently plausible rather than obviously broken.
"""
from __future__ import annotations

import pytest

from vinci.dossier import terminal_margin as tm
from vinci.dossier.midcycle import BAR, reward_risk


def _leg(name: str = "base", **kw: object) -> tm.TerminalLeg:
    d: dict = {"name": name, "years": 4.0, "revenue": 900.0, "margin": 0.12, "multiple": 14.0,
               "reason": "illustrative terminal case"}
    d.update(kw)
    return tm.TerminalLeg(**d)


_BRIDGE = {"d_and_a_ratio_": 0.069264, "net_debt_now": 223.899, "burn_to_breakeven": 0.0,
           "shares_now": 109_458_472.0, "g_sbc": 0.011119}


# --- the worked example, pinned end to end ------------------------------------------------------
def test_pv_worked_example() -> None:
    """THE ARITHMETIC, pinned on the NCNO-shaped worked example printed in the PR. Every step is
    checked separately so a regression names the step it broke, not just the answer."""
    v = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **_BRIDGE)
    assert v.ebit_t == pytest.approx(108.0)                       # 900 × 12%
    assert v.d_and_a_t == pytest.approx(62.3376, abs=1e-4)        # 0.069264 × 900
    assert v.ebitda_t == pytest.approx(170.3376, abs=1e-4)
    assert v.denominator_t == v.ebitda_t                          # EBITDA basis
    assert v.ev_t == pytest.approx(2384.7264, abs=1e-3)           # × 14
    assert v.net_debt_t == pytest.approx(223.899)                 # no burn
    assert v.equity_t == pytest.approx(2160.8274, abs=1e-3)
    assert v.shares_t == pytest.approx(114_408_546, rel=1e-6)     # × (1.011119)^4
    assert v.value_t == pytest.approx(18.8869, abs=1e-3)
    assert v.pv == pytest.approx(10.7987, abs=1e-3)               # ÷ 1.15^4
    assert v.pv == pytest.approx(v.value_t / (1 + tm.HURDLE) ** 4, rel=1e-12)


def test_value_per_share_is_dollars_not_millionths() -> None:
    """UNIT PIN. ``equity_t`` is $M and ``shares_t`` is a raw COUNT, so the engine must scale before
    dividing. The bug (found 2026-07-21 by running the worked example) produced $0.0000 per share
    off a $2.16bn equity — plausible-looking as 'cheap' rather than obviously broken, which is why
    this asserts a MAGNITUDE and not merely that a number came back."""
    v = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **_BRIDGE)
    assert 1.0 < v.value_t < 1000.0, f"value/share {v.value_t} is not a share price"
    # and it equals the explicit hand computation, in dollars
    assert v.value_t == pytest.approx(v.equity_t * 1e6 / v.shares_t, rel=1e-12)


def test_hurdle_is_the_house_rate_and_discounts_with_the_horizon() -> None:
    """A longer horizon must be worth LESS today at the same terminal value — the whole reason the
    PV convention exists. And the hurdle is the module constant, never a per-record field."""
    assert tm.HURDLE == 0.15
    near = tm.terminal_value(_leg(years=2.0), basis=tm.BASIS_EBITDA, **_BRIDGE)
    far = tm.terminal_value(_leg(years=8.0), basis=tm.BASIS_EBITDA, **_BRIDGE)
    assert far.value_t < near.value_t          # more dilution by year 8
    assert far.pv < near.pv
    assert near.pv == pytest.approx(near.value_t / 1.15**2, rel=1e-12)


# --- EV/EBIT basis ------------------------------------------------------------------------------
def test_ev_ebit_basis_applies_the_multiple_to_ebit_not_ebitda() -> None:
    """VITL's EBITDA band is vendor-defective while its TEV/LTM EBIT row reconciles exactly, so the
    EBIT basis has to be a first-class option — the formula adjusts, it is not an EBITDA run with a
    different label. On the same leg the EBIT basis must value LOWER (a smaller denominator)."""
    ebitda = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **_BRIDGE)
    ebit = tm.terminal_value(_leg(), basis=tm.BASIS_EBIT, **_BRIDGE)
    assert ebit.denominator_t == pytest.approx(108.0)      # EBIT_T, not EBITDA_T
    assert ebit.basis == tm.BASIS_EBIT
    assert ebit.ev_t == pytest.approx(108.0 * 14.0)
    assert ebit.value_t < ebitda.value_t
    # D&A is still computed and reported on both — it is disclosure, not just an input
    assert ebit.d_and_a_t == pytest.approx(ebitda.d_and_a_t)


def test_unknown_basis_refuses() -> None:
    with pytest.raises(tm.TerminalError, match="unknown multiple basis"):
        tm.terminal_value(_leg(), basis="EV/Sales", **_BRIDGE)


# --- EV/Revenue basis ---------------------------------------------------------------------------
# FUBO has no trailing EBITDA, no trailing EBIT, no EPS and ZERO committed own-history bands, so
# every earnings basis would have to invent the terminal margin it then values. This basis asks the
# smaller, answerable question — worth if it merely survives at peer-thin margins — and the pins
# below are all about ONE property: margin and D&A must be incapable of touching the answer.
_REV_BRIDGE = {"d_and_a_ratio_": None, "net_debt_now": 170.4, "burn_to_breakeven": 400.0,
               "shares_now": 30_715_000.0, "g_sbc": 0.04}


def test_ev_revenue_matches_a_hand_computation_exactly() -> None:
    """COHERENCE PIN — the whole chain against arithmetic done by hand, step by step, so a
    regression names the step it broke rather than just the answer."""
    v = tm.terminal_value(_leg(margin=None, revenue=6100.0, multiple=0.7),
                          basis=tm.BASIS_REVENUE, **_REV_BRIDGE)
    assert v.denominator_t == pytest.approx(6100.0)          # REVENUE is the denominator
    assert v.ev_t == pytest.approx(4270.0)                   # 6100 × 0.7
    assert v.net_debt_t == pytest.approx(570.4)              # 170.4 + 400.0 burn
    assert v.equity_t == pytest.approx(3699.6)               # 4270.0 − 570.4
    assert v.shares_t == pytest.approx(30_715_000.0 * 1.04**4, rel=1e-12)
    assert v.value_t == pytest.approx(3699.6e6 / (30_715_000.0 * 1.04**4), rel=1e-12)
    assert v.pv == pytest.approx(v.value_t / 1.15**4, rel=1e-12)
    # the earnings fields are ABSENT, not zero — nothing for a card to render as a driver
    assert v.ebit_t is None and v.d_and_a_t is None and v.ebitda_t is None


def test_ev_revenue_ignores_margin_because_it_never_accepts_one() -> None:
    """THE DEAD-INPUT PIN, stated the only way it can be true: a margin cannot move the value
    because the engine REFUSES to take one. Testing "value is unchanged when margin changes" on a
    silently-ignored field would pass just as happily on a renderer that still printed it."""
    for bad in (0.0, 0.12, -0.30):
        with pytest.raises(tm.TerminalError, match="carries terminal margin"):
            tm.terminal_value(_leg(margin=bad), basis=tm.BASIS_REVENUE, **_REV_BRIDGE)
    # ...and the same for the D&A ratio, the other leg of the earnings bridge
    with pytest.raises(tm.TerminalError, match="carries a D&A ratio"):
        tm.terminal_value(_leg(margin=None), basis=tm.BASIS_REVENUE,
                          **{**_REV_BRIDGE, "d_and_a_ratio_": 0.069264})


def test_earnings_bases_still_demand_the_margin_they_value() -> None:
    """The NEGATIVE pin of the same guard, both directions: nullable margin must not become an
    optional margin on the bases whose entire arithmetic runs through it."""
    for basis in (tm.BASIS_EBITDA, tm.BASIS_EBIT):
        with pytest.raises(tm.TerminalError, match="THROUGH its terminal margin"):
            tm.terminal_value(_leg(margin=None), basis=basis, **_BRIDGE)
    with pytest.raises(tm.TerminalError, match="needs a D&A ratio"):
        tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **{**_BRIDGE, "d_and_a_ratio_": None})


def test_ev_revenue_keeps_every_non_valuation_mechanic() -> None:
    """EV/Revenue changes the TERMINAL VALUATION and nothing else — the burn still lands in
    terminal net debt, dilution still compounds, and the hurdle still discounts. A basis that
    quietly switched those off would flatter exactly the names it is reserved for."""
    dry = tm.terminal_value(_leg(margin=None, revenue=6100.0, multiple=0.7),
                            basis=tm.BASIS_REVENUE, **{**_REV_BRIDGE, "burn_to_breakeven": 0.0})
    burning = tm.terminal_value(_leg(margin=None, revenue=6100.0, multiple=0.7),
                                basis=tm.BASIS_REVENUE, **_REV_BRIDGE)
    assert burning.net_debt_t > dry.net_debt_t and burning.value_t < dry.value_t
    undiluted = tm.terminal_value(_leg(margin=None, revenue=6100.0, multiple=0.7),
                                  basis=tm.BASIS_REVENUE, **{**_REV_BRIDGE, "g_sbc": 0.0})
    assert undiluted.shares_t < burning.shares_t and undiluted.value_t > burning.value_t
    assert burning.pv < burning.value_t                       # still discounted


def test_ev_revenue_formula_stamp_is_its_own_chain() -> None:
    """The stamp states the arithmetic a record ACTUALLY ran. An EV/Revenue record stamped with
    R2's EBIT line would be describing a computation that never happened — and the EBITDA/EBIT
    records must keep the stamp they were committed with, byte for byte."""
    rev = tm.formula_for(tm.BASIS_REVENUE)
    assert rev == tm.R2_FORMULA_REVENUE
    assert tm.formula_for(tm.BASIS_EBITDA) == tm.R2_FORMULA == tm.formula_for(tm.BASIS_EBIT)
    joined = " ".join(rev)
    assert "terminal revenue × exit multiple" in joined
    for absent in ("EBIT_T", "D&A_T", "EBITDA_T", "terminal margin"):
        assert absent not in joined, f"the EV/Revenue chain must not claim {absent}"
    # every non-valuation mechanic is still stated
    for token in ("net debt_T", "shares_T", "share growth", "hurdle"):
        assert token in joined


# --- dilution and the cash between here and there -----------------------------------------------
def test_share_growth_is_a_floored_three_year_cagr() -> None:
    """The floor is ASYMMETRIC on purpose: a buyback history is not evidence of future shrinkage,
    and negative dilution in a terminal year is a silent gift to a pre-profit valuation."""
    # NCNO's real diluted weighted-average shape, rounded to the tenth of a million printed in the
    # worked example. The window is the trailing FOUR points => a THREE-year span (2023 -> 2026):
    # (114.3/110.6)^(1/3) − 1. The earlier 2022 point is deliberately outside it.
    growing = {2022: 96.7e6, 2023: 110.6e6, 2024: 112.7e6, 2025: 115.2e6, 2026: 114.3e6}
    g = tm.share_growth(growing)
    assert g == pytest.approx((114.3 / 110.6) ** (1 / 3) - 1, rel=1e-9)
    assert g == pytest.approx(0.011029, abs=1e-5)
    shrinking = {2023: 120e6, 2024: 110e6, 2025: 100e6, 2026: 90e6}
    assert tm.share_growth(shrinking) == 0.0               # floored, never negative
    assert tm.share_growth({2026: 100e6}) == 0.0           # one point: no trend to read
    assert tm.share_growth({}) == 0.0


def test_announced_raise_adds_shares_on_top_of_compounding() -> None:
    """A raise is a discrete event, not a growth rate — it lands on top of the compounded count."""
    base = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **_BRIDGE)
    with_raise = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, raise_shares=20e6, **_BRIDGE)
    assert with_raise.shares_t == pytest.approx(base.shares_t + 20e6)
    assert with_raise.value_t < base.value_t


def test_burn_to_breakeven_only_ever_increases_terminal_net_debt() -> None:
    """Cash spent getting to the terminal year is not available to equity when it arrives."""
    dry = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **_BRIDGE)
    burning = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA,
                                **{**_BRIDGE, "burn_to_breakeven": 150.0})
    assert burning.net_debt_t == pytest.approx(dry.net_debt_t + 150.0)
    assert burning.equity_t < dry.equity_t
    assert burning.pv < dry.pv


def test_d_and_a_ratio_scales_with_terminal_revenue() -> None:
    """Carried as a RATIO, so a business that has doubled by the terminal year carries doubled D&A
    — a dollar level frozen from today would understate it exactly when the company has scaled."""
    r = tm.d_and_a_ratio(latest_d_and_a=42.255, latest_revenue=610.058)
    assert r == pytest.approx(0.069264, abs=1e-6)
    small = tm.terminal_value(_leg(revenue=600.0), basis=tm.BASIS_EBITDA, **_BRIDGE)
    big = tm.terminal_value(_leg(revenue=1200.0), basis=tm.BASIS_EBITDA, **_BRIDGE)
    assert big.d_and_a_t == pytest.approx(2 * small.d_and_a_t)
    with pytest.raises(tm.TerminalError, match="latest revenue must be > 0"):
        tm.d_and_a_ratio(latest_d_and_a=10.0, latest_revenue=0.0)


# --- degenerate guards --------------------------------------------------------------------------
@pytest.mark.parametrize(("kw", "match"), [
    ({"years": 0.0}, "years to terminal must be > 0"),
    ({"years": -2.0}, "years to terminal must be > 0"),
    ({"revenue": 0.0}, "terminal revenue must be > 0"),
    ({"multiple": 0.0}, "exit multiple must be > 0"),
    ({"reason": "   "}, "needs a stated reason"),
])
def test_degenerate_legs_fail_loud(kw: dict, match: str) -> None:
    """Same discipline as R1: refuse, never fudge. A blank reason is refused for the same reason
    build_scenario refuses one — an assumption nobody explained cannot be reviewed."""
    with pytest.raises(tm.TerminalError, match=match):
        tm.terminal_value(_leg(**kw), basis=tm.BASIS_EBITDA, **_BRIDGE)


def test_non_positive_terminal_denominator_refuses() -> None:
    """A multiple on a negative denominator yields a NEGATIVE enterprise value, which is not a
    valuation — it is the arithmetic quietly inverting. This is the live risk for the R2 cohort,
    every one of which is loss-making today."""
    with pytest.raises(tm.TerminalError, match="non-positive denominator|is not a valuation"):
        tm.terminal_value(_leg(margin=-0.30), basis=tm.BASIS_EBIT, **_BRIDGE)


def test_zero_shares_refuses() -> None:
    with pytest.raises(tm.TerminalError, match="diluted shares must be > 0"):
        tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **{**_BRIDGE, "shares_now": 0.0})


# --- the survival gate --------------------------------------------------------------------------
_FCF_ARGS = {"fcf_basis": "latest FY2025 (not LTM)", "fcf_source": "EDGAR OCF − capex"}


def test_survival_positive_fcf_is_a_trivial_pass_and_says_so() -> None:
    """A company funding itself has no runway question; dressing that up as a computed gate would
    imply a risk assessment nobody made."""
    s = tm.survival_gate(fcf=82.564, cash=200.0, **_FCF_ARGS)
    assert s.status == "PASS"
    assert "trivial pass" in s.note and s.burn is None
    assert s.runway_years is None


def test_survival_fails_when_runway_falls_short_with_no_raise() -> None:
    """THE FAIL PATH. $100M of cash against an $80M burn is 1.25y of runway; breakeven is 3y away
    and nothing is committed."""
    s = tm.survival_gate(fcf=-80.0, cash=100.0, years_to_breakeven=3.0, **_FCF_ARGS)
    assert s.status == "FAIL"
    assert s.burn == pytest.approx(80.0)
    assert s.runway_years == pytest.approx(1.25)
    assert "no announced or committed raise" in s.note


def test_survival_passes_on_an_announced_raise_with_an_accession() -> None:
    """A raise bridges the gap ONLY with an accession — an intention reported in a press cycle is
    not committed capital, and the gate exists to refuse the assumption that money will appear."""
    ok = tm.survival_gate(fcf=-80.0, cash=100.0, years_to_breakeven=3.0, announced_raise=True,
                          raise_accession="0001104659-26-012345", **_FCF_ARGS)
    assert ok.status == "PASS" and "0001104659-26-012345" in ok.note
    naked = tm.survival_gate(fcf=-80.0, cash=100.0, years_to_breakeven=3.0, announced_raise=True,
                             **_FCF_ARGS)
    assert naked.status == "FAIL" and "NO ACCESSION" in naked.note


def test_survival_counts_committed_undrawn_facilities() -> None:
    """Facilities are real runway when committed and undrawn — and they are source-stamped."""
    s = tm.survival_gate(fcf=-80.0, cash=100.0, facilities=150.0,
                         facilities_source="10-Q revolver, undrawn", years_to_breakeven=3.0,
                         **_FCF_ARGS)
    assert s.status == "PASS"
    assert s.runway_years == pytest.approx(250.0 / 80.0)


@pytest.mark.parametrize(("kw", "why"), [
    ({"fcf": None, "cash": 100.0}, "fcf UNKNOWN"),
    ({"fcf": -80.0, "cash": 100.0}, "no years_to_breakeven"),
])
def test_survival_refuses_to_clear_on_missing_inputs(kw: dict, why: str) -> None:
    """Absence never clears the gate. A company whose burn or breakeven year is unknown is not a
    company that has been shown to survive."""
    s = tm.survival_gate(**{**_FCF_ARGS, **kw})
    assert s.status == "FAIL", why


# --- the bar and the convention are UNCHANGED by the recipe --------------------------------------
def test_r2_uses_the_same_bar_and_reward_risk_convention_as_r1() -> None:
    """The bar does not move because the recipe did. reward/risk is computed on the PV legs by the
    SAME shared function R1 uses — bull is printed and never in the ratio."""
    assert tm.BAR == BAR == 2.0
    bear = tm.terminal_value(_leg("bear", revenue=720.0, margin=0.06, multiple=10.0),
                             basis=tm.BASIS_EBITDA, **_BRIDGE)
    base = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **_BRIDGE)
    rr = reward_risk(base_vps=base.pv, bear_vps=bear.pv, spot=6.0)
    assert rr.reward == pytest.approx(base.pv - 6.0)
    assert rr.risk == pytest.approx(6.0 - bear.pv)
    assert rr.ratio == pytest.approx(rr.reward / rr.risk)


def test_formula_stamp_matches_the_engine_shape() -> None:
    """The stated recipe can never drift from the computed one (the R1 stamp/refuse precedent)."""
    joined = " ".join(tm.R2_FORMULA)
    for token in ("terminal revenue × terminal margin", "EBITDA_T = EBIT_T + D&A_T",
                  "net debt_T = current net debt + cumulative burn", "(1 + share growth)^years",
                  "PV = value_T ÷ (1 + hurdle)^years"):
        assert token in joined, f"R2_FORMULA no longer states: {token}"
    assert tm.RECIPE_R2 == "R2_terminal_margin"
    assert set(tm.TIER_DESC) == {tm.TIER_A, tm.TIER_B}


# --- the RECORD layer: dispatch, stamping, and the gate that blocks a confirmed BUY -------------
def _r2_record(**kw: object):
    """A minimal but VALID R2 record. Units follow the R1 record convention: $M for money,
    MILLIONS for the share count — the engine's raw-count conversion happens inside _run_r2."""
    from vinci import scenarios as sc
    d: dict = {
        "ticker": "DEMO", "recipe_id": sc.RECIPE_R2, "recipe_desc": "terminal-margin",
        "multiple_basis": tm.BASIS_EBITDA, "underwrite_date": "2026-07-21", "analyst": "test",
        "spot": 6.00, "spot_source": "test close",
        "facts": {
            "net_debt": sc.Fact(value=223.9, unit="$M", basis="lease-inclusive", source="EDGAR"),
            "diluted_shares": sc.Fact(value=109.458, unit="shares", basis="diluted WA",
                                      source="EDGAR"),
            "d_and_a_ratio": sc.Fact(value=0.069264, unit="rate", basis="latest FY D&A/revenue",
                                     source="EDGAR"),
            "share_growth": sc.Fact(value=0.011119, unit="rate", basis="3y diluted CAGR",
                                    source="EDGAR"),
            # Held at an explicit NIL so the record arithmetic matches the engine's worked-example
            # pin above; the burn-specific tests override it. An explicit 0.0 is the analyst
            # stating it, which is exactly what the burn guard demands.
            "burn_to_breakeven": sc.Fact(value=0.0, unit="$M", basis="held nil for the pin",
                                         source="analyst")},
        "scenarios": {
            "bear": sc.ScenarioInput(revenue=720, margin=0.06, multiple=10, years_to_terminal=4,
                                     reason="slower ramp"),
            "base": sc.ScenarioInput(revenue=900, margin=0.12, multiple=14, years_to_terminal=4,
                                     reason="plan"),
            "bull": sc.ScenarioInput(revenue=1080, margin=0.18, multiple=18, years_to_terminal=4,
                                     reason="upside")},
        "assumptions": {a: sc.AssumptionDerivation(method="stated for the test run")
                        for a in ("revenue", "margin", "multiple", "horizon")},
        "tier": tm.TIER_B,
        "survival_input": sc.SurvivalInput(fcf=-80.0, fcf_basis="latest FY2025",
                                           fcf_source="EDGAR OCF−capex", cash=100.0,
                                           years_to_breakeven=3.0)}
    d.update(kw)
    return sc.ScenarioRecord(**d)


def test_run_recipe_dispatches_r2_and_stamps_its_formula() -> None:
    """The record states the recipe its numbers came from — an R2 record must carry R2_FORMULA,
    not R1's (the multiple_basis precedent: a misstated recipe refuses rather than renders)."""
    from vinci import scenarios as sc
    r = sc.run_recipe(_r2_record())
    assert r.recipe_formula == list(tm.R2_FORMULA)
    assert r.result.hurdle == tm.HURDLE
    assert r.result.survival is not None
    base = r.result.per_scenario["base"]
    assert base.value_per_share == pytest.approx(10.7987, abs=1e-3)     # the PV drives the ratio
    assert base.value_terminal == pytest.approx(18.8869, abs=1e-3)      # undiscounted, alongside
    assert base.shares_t == pytest.approx(114.4085, abs=1e-3)           # MILLIONS on the record


def test_r2_record_refuses_a_misstated_formula() -> None:
    from vinci import scenarios as sc
    with pytest.raises(ValueError, match="recipe_formula does not match"):
        sc.run_recipe(_r2_record(recipe_formula=["EBIT = revenue × margin"]))


@pytest.mark.parametrize("missing", ["net_debt", "diluted_shares", "d_and_a_ratio", "share_growth"])
def test_r2_refuses_to_assume_a_missing_fact(missing: str) -> None:
    from vinci import scenarios as sc
    rec = _r2_record()
    facts = {k: v for k, v in rec.facts.items() if k != missing}
    with pytest.raises(ValueError, match=f"needs fact '{missing}'"):
        sc.run_recipe(rec.model_copy(update={"facts": facts}))


def _r2_revenue_record(**kw: object):
    """The same minimal record on the EV/Revenue basis: no margin on any leg, no d_and_a_ratio
    fact, and a three-axis methodology — the shape a real EV/Revenue record must take.

    Built through the CONSTRUCTOR, never ``model_copy``: model_copy does not re-run validators, so
    a helper that used it would silently skip the very axes guard these tests exist to pin."""
    from vinci import scenarios as sc
    rec = _r2_record()
    d: dict = {
        "ticker": "DEMO", "recipe_id": sc.RECIPE_R2, "recipe_desc": "terminal-margin",
        "multiple_basis": tm.BASIS_REVENUE, "underwrite_date": "2026-07-21", "analyst": "test",
        "spot": 6.00, "spot_source": "test close",
        "facts": {k: v for k, v in rec.facts.items() if k != "d_and_a_ratio"},
        "scenarios": {
            n: sc.ScenarioInput(revenue=s.revenue, multiple=m, years_to_terminal=4,
                                reason=s.reason)
            for (n, s), m in zip(rec.scenarios.items(), (0.5, 0.7, 1.0), strict=True)},
        "assumptions": {a: sc.AssumptionDerivation(method="stated for the test run")
                        for a in ("revenue", "multiple", "horizon")},
        "tier": tm.TIER_B, "survival_input": rec.survival_input}
    d.update(kw)
    return sc.ScenarioRecord(**d)


def test_r2_revenue_record_runs_and_stamps_the_revenue_chain() -> None:
    """END TO END on the record layer: an EV/Revenue record computes, stamps ITS OWN chain, and
    carries no earnings figures for a renderer to mistake for value drivers."""
    from vinci import scenarios as sc
    r = sc.run_recipe(_r2_revenue_record())
    assert r.recipe_formula == list(tm.R2_FORMULA_REVENUE)
    base = r.result.per_scenario["base"]
    assert base.op_income is None and base.ebitda is None and base.d_and_a_t is None
    assert base.ev_ebit is None            # no EBIT to cross-check against
    assert base.value_terminal is not None and base.value_per_share is not None


def test_r2_revenue_record_refuses_a_dead_d_and_a_fact() -> None:
    """A d_and_a_ratio fact on an EV/Revenue record is a driver nothing reads. Refuse it at the
    record layer too — the engine's refusal never sees it, because _run_r2 stops passing it."""
    from vinci import scenarios as sc
    rec = _r2_revenue_record()
    facts = {**rec.facts, "d_and_a_ratio": sc.Fact(value=0.0113, unit="rate", basis="latest FY",
                                                   source="EDGAR")}
    with pytest.raises(ValueError, match="no computation reads"):
        sc.run_recipe(rec.model_copy(update={"facts": facts}))


def test_r2_revenue_axes_drop_margin_both_directions() -> None:
    """The methodology axes follow the BASIS, not just the recipe. Requiring a margin write-up on a
    basis that never reads a margin would produce a reviewable-looking paragraph attached to
    nothing; accepting one silently would do the same. Both are refused."""
    from vinci import scenarios as sc
    assert sc.axes_for(sc.RECIPE_R2, tm.BASIS_REVENUE) == ("revenue", "multiple", "horizon")
    assert sc.axes_for(sc.RECIPE_R2, tm.BASIS_EBITDA) == sc.AXES_BY_RECIPE[sc.RECIPE_R2]
    with pytest.raises(ValueError, match="unknown assumption axis"):
        _r2_revenue_record(assumptions={
            a: sc.AssumptionDerivation(method="stated for the test run")
            for a in ("revenue", "margin", "multiple", "horizon")})
    with pytest.raises(ValueError, match="must cover exactly"):
        _r2_revenue_record(assumptions={
            a: sc.AssumptionDerivation(method="stated for the test run")
            for a in ("revenue", "multiple")})


def test_r1_still_demands_the_margin_it_values() -> None:
    """`margin` became nullable for EV/Revenue. R1 is a mid-cycle MARGIN recipe end to end, so an
    absent one must refuse rather than reach the block as a silent zero."""
    from tests.test_scenarios import _rec
    from vinci import scenarios as sc

    rec = _rec()
    legs = dict(rec.scenarios)
    legs["base"] = sc.ScenarioInput(revenue=legs["base"].revenue, multiple=legs["base"].multiple,
                                    reason=legs["base"].reason)
    with pytest.raises(ValueError, match="mid-cycle MARGIN recipe"):
        sc.run_recipe(rec.model_copy(update={"scenarios": legs}))


def test_r2_refuses_a_leg_with_no_horizon() -> None:
    from vinci import scenarios as sc
    rec = _r2_record()
    legs = dict(rec.scenarios)
    legs["base"] = sc.ScenarioInput(revenue=900, margin=0.12, multiple=14, reason="plan")
    with pytest.raises(ValueError, match="needs years_to_terminal"):
        sc.run_recipe(rec.model_copy(update={"scenarios": legs}))


def test_r2_refuses_without_survival_input() -> None:
    from vinci import scenarios as sc
    with pytest.raises(ValueError, match="needs survival_input"):
        sc.run_recipe(_r2_record(survival_input=None))


def test_survival_fail_blocks_a_confirmed_buy_but_not_watch_or_passed() -> None:
    """THE GATE, pinned on the RECORD. It binds here rather than in the runner because the verdict
    is written by hand — a guard living only in the compute path would be edited straight past.

    'watch' and 'passed' stay reachable: they are exactly what a failing name should receive, and
    the record still computes and prints in full."""
    from vinci import scenarios as sc
    r = sc.run_recipe(_r2_record())
    assert r.result.survival is not None and r.result.survival.status == "FAIL"
    payload = r.model_dump()
    payload["verdict"] = {**payload["verdict"], "status": "confirmed"}
    with pytest.raises(ValueError, match="survival gate FAILED"):
        sc.ScenarioRecord.model_validate(payload)
    for ok in ("watch", "passed", "pending_analyst"):
        payload["verdict"] = {**payload["verdict"], "status": ok}
        assert sc.ScenarioRecord.model_validate(payload).verdict.status == ok


def test_a_cleared_gate_allows_a_confirmed_buy() -> None:
    """The block is on the FAILING gate, not on R2 as a recipe — a name that clears it confirms
    normally, or the gate would be a permanent veto on the whole cohort."""
    from vinci import scenarios as sc
    r = sc.run_recipe(_r2_record(survival_input=sc.SurvivalInput(
        fcf=82.5, fcf_basis="latest FY2026", fcf_source="EDGAR OCF−capex", cash=200.0)))
    assert r.result.survival is not None and r.result.survival.status == "PASS"
    payload = r.model_dump()
    payload["verdict"] = {**payload["verdict"], "status": "confirmed"}
    assert sc.ScenarioRecord.model_validate(payload).verdict.status == "confirmed"


def test_r2_axes_require_the_horizon() -> None:
    """The horizon is a modelled AXIS, so the axes guard demands it be explained like the others."""
    from vinci import scenarios as sc
    assert sc.AXES_BY_RECIPE[sc.RECIPE_R2] == ("revenue", "margin", "multiple", "horizon")
    with pytest.raises(ValueError, match="must cover exactly"):
        _r2_record(assumptions={a: sc.AssumptionDerivation(method="m")
                                for a in ("revenue", "margin", "multiple")})


def test_announced_raise_proceeds_reduce_terminal_net_debt() -> None:
    """A raise brings CASH as well as shares — counting only the dilution would overstate the debt
    the terminal equity carries."""
    from vinci import scenarios as sc
    plain = sc.run_recipe(_r2_record())
    raised = sc.run_recipe(_r2_record(survival_input=sc.SurvivalInput(
        fcf=-80.0, fcf_basis="latest FY2025", fcf_source="EDGAR OCF−capex", cash=100.0,
        years_to_breakeven=3.0, announced_raise=True, raise_accession="0001104659-26-1",
        raise_shares=20.0, raise_proceeds=150.0)))
    assert raised.result.survival is not None and raised.result.survival.status == "PASS"
    assert raised.result.per_scenario["base"].net_debt_t == pytest.approx(
        plain.result.per_scenario["base"].net_debt_t - 150.0)
    assert raised.result.per_scenario["base"].shares_t == pytest.approx(
        plain.result.per_scenario["base"].shares_t + 20.0, abs=1e-6)


def test_a_burning_company_must_state_the_cash_it_consumes() -> None:
    """REVIEW FIX (#176). A record whose survival block shows a burn cannot value the terminal year
    as though that burn were free. Defaulting burn_to_breakeven to zero produced the contradiction
    of a FAIL gate at 1.25y of runway sitting beside terminal net debt UNCHANGED from today — the
    exact direction of error R2 exists to prevent, and it applies to the whole cohort by definition.

    The machine refuses rather than deriving burn × years: filling it in would be the machine
    proposing an assumption. An explicit 0.0 is accepted — that is the analyst stating it."""
    from vinci import scenarios as sc
    burning = _r2_record()                      # survival_input burns 80.0 a year
    silent = {k: v for k, v in burning.facts.items() if k != "burn_to_breakeven"}
    with pytest.raises(ValueError, match="needs fact 'burn_to_breakeven'"):
        sc.run_recipe(burning.model_copy(update={"facts": silent}))
    # stated explicitly -> computes, and the burn lands on terminal net debt
    stated = dict(burning.facts)
    stated["burn_to_breakeven"] = sc.Fact(value=240.0, unit="$M",
                                          basis="three years at the stated burn", source="analyst")
    r = sc.run_recipe(burning.model_copy(update={"facts": stated}))
    assert r.result.per_scenario["base"].net_debt_t == pytest.approx(223.9 + 240.0)
    # an explicit nil is the analyst's call to make, and is honoured
    r0 = sc.run_recipe(burning)
    assert r0.result.per_scenario["base"].net_debt_t == pytest.approx(223.9)


def test_a_self_funding_company_needs_no_burn_fact() -> None:
    """The refusal is scoped to a company that actually burns — an FCF-positive name has no cash
    to consume, so demanding the fact there would be ceremony."""
    from vinci import scenarios as sc
    r = sc.run_recipe(_r2_record(survival_input=sc.SurvivalInput(
        fcf=82.5, fcf_basis="latest FY2026", fcf_source="EDGAR OCF−capex", cash=200.0)))
    assert r.result.survival is not None and r.result.survival.status == "PASS"
    assert r.result.per_scenario["base"].net_debt_t == pytest.approx(223.9)


# --- going concern: the trivial pass is FORBIDDEN (MVST is the falsifier) ------------------------
def test_going_concern_forbids_the_trivial_pass_on_positive_trailing_fcf() -> None:
    """THE MVST SHAPE, and the reason this branch exists. Trailing free cash flow was +$56.1M — a
    clean trivial pass under the old gate, which returned "the company funds itself and has no
    runway question" — while the filer's own 10-Q states substantial doubt about its ability to
    continue and the latest quarter annualises to a $102.6M BURN.

    The disclosure is about the future and the cash flow is about the past, so the past cannot
    overturn it. With going concern stated the gate evaluates on the supplied burn, never on the
    trailing sign."""
    s = tm.survival_gate(
        fcf=+56.074, fcf_basis="trailing annual", fcf_source="EDGAR",
        cash=126.1, facilities=98.0, facilities_source="at-the-market remaining capacity",
        years_to_breakeven=3.0, going_concern_stated=True,
        going_concern_accession="0001628280-26-033590",
        burn_override=102.6, burn_override_basis="latest quarter annualised",
        latest_period_fcf=-25.65)
    assert s.status == "FAIL"
    assert "trivial pass" not in s.note, "the false-pass path is still reachable"
    assert s.burn == pytest.approx(102.6), "evaluated on the trailing figure, not the stated burn"
    assert s.runway_years == pytest.approx((126.1 + 98.0) / 102.6, abs=1e-6)
    assert any("going concern" in d for d in s.detail)
    assert any("0001628280-26-033590" in d for d in s.detail)


def test_going_concern_without_a_burn_override_refuses() -> None:
    """The override is MANDATORY once going concern is stated — the trailing figure is exactly the
    number the disclosure contradicts, so falling back to it would defeat the branch."""
    s = tm.survival_gate(fcf=+56.074, fcf_basis="trailing annual", fcf_source="EDGAR",
                         cash=126.1, years_to_breakeven=3.0, going_concern_stated=True)
    assert s.status == "FAIL" and "NO burn override" in s.note


def test_sign_contradiction_is_always_printed() -> None:
    """A trailing figure and a latest period with opposite signs is reported whatever the gate
    concludes — a reader shown only the annual number would draw the opposite conclusion."""
    s = tm.survival_gate(fcf=+56.074, fcf_basis="trailing annual", fcf_source="EDGAR",
                         cash=500.0, latest_period_fcf=-25.65)
    assert s.status == "PASS"                      # not a going-concern name; trivial pass stands
    assert any("OPPOSITE SIGNS" in d for d in s.detail)


def test_facility_credit_and_the_raise_move_together() -> None:
    """COHERENCE, no half-credit. A committed facility credits RUNWAY here; where it is drawn, the
    same event must move shares_T AND terminal net debt in the engine — proceeds reduce net debt
    and the shares land on the count. Asserted jointly so neither can be taken alone."""
    s = tm.survival_gate(fcf=-100.0, fcf_basis="annual", fcf_source="EDGAR", cash=50.0,
                         facilities=100.0, facilities_source="ATM remaining",
                         years_to_breakeven=1.0)
    assert s.status == "PASS" and s.runway_years == pytest.approx(1.5)   # facility credited
    base = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA, **_BRIDGE)
    drawn = tm.terminal_value(_leg(), basis=tm.BASIS_EBITDA,
                              **{**_BRIDGE, "net_debt_now": _BRIDGE["net_debt_now"] - 100.0},
                              raise_shares=90e6)
    assert drawn.net_debt_t == pytest.approx(base.net_debt_t - 100.0), "proceeds did not land"
    assert drawn.shares_t == pytest.approx(base.shares_t + 90e6), "shares did not land"


def test_trivial_pass_still_works_for_a_clean_name() -> None:
    """REGRESSION: NCNO/AORT-shaped names must keep their trivial pass — the new branch is scoped
    to a stated going concern, not to every positive-FCF name."""
    s = tm.survival_gate(fcf=82.564, fcf_basis="latest FY", fcf_source="EDGAR", cash=200.0)
    assert s.status == "PASS" and "trivial pass" in s.note and s.burn is None
