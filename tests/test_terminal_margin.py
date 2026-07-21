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
