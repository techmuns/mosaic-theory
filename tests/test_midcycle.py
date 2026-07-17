"""Mid-cycle & scenarios — deterministic math, network-free (stubbed EDGAR facts).

Pins: the margin series + median; the <10y coverage read (actual coverage, never extrapolated); the
longest-alias selection (the WERN first-hit-wins truncation); peer exclusion for a short history
(named loudly); the fuel-surcharge split BOTH ways (and that a fuel COST tag is not a surcharge
disclosure); the anchor-default base; the refusal to compute a deviated scenario with no reason; the
reward/risk CONVENTION on a worked example (incl. both degenerate cases); and the sensitivity grid.
"""
from __future__ import annotations

from typing import Any

import pytest

from vinci.dossier import midcycle as mc


def _facts(**tags: dict[int, float]) -> dict[str, Any]:
    """A minimal companyfacts stub: {tag: {year: value}} → us-gaap annual (FY) rows."""
    ns: dict[str, Any] = {}
    for tag, by_year in tags.items():
        ns[tag] = {"units": {"USD": [
            {"start": f"{y}-01-01", "end": f"{y}-12-31", "val": v, "fy": y, "fp": "FY",
             "form": "10-K", "accn": f"acc-{tag}-{y}", "filed": f"{y + 1}-02-15"}
            for y, v in by_year.items()]}}
    return {"facts": {"us-gaap": ns}}


_YEARS = list(range(2015, 2025))                      # 10 years
_REV = dict.fromkeys(_YEARS, 1000.0)
_OI = dict(zip(_YEARS, [50., 60., 70., 80., 90., 100., 110., 120., 130., 140.], strict=True))
# margins 5%…14%


def test_margin_series_and_median() -> None:
    f = _facts(Revenues=_REV, OperatingIncomeLoss=_OI)
    a = mc.margin_anchor(mc.annual_series(f, "revenue"), mc.annual_series(f, "operating_income"))
    assert a.n_years == 10 and a.covers_window
    assert a.years == _YEARS
    assert a.median == pytest.approx(0.095)           # median of 5%…14%
    assert a.trough == pytest.approx(0.05) and a.peak == pytest.approx(0.14)
    q = a.quartiles()
    assert q is not None and q[0] == pytest.approx(0.0725) and q[1] == pytest.approx(0.1175)
    assert "10y (2015–2024)" in a.coverage_note


def test_longest_alias_wins_not_first_hit() -> None:
    """The WERN bug class: a filer that switched tags. The priority-first alias has 4y, `Revenues`
    has 10y — the anchor must take the LONGEST coverage (one tag, one basis; never a splice)."""
    short = dict.fromkeys(range(2021, 2025), 1000.0)
    f = _facts(RevenueFromContractWithCustomerExcludingAssessedTax=short, Revenues=_REV,
               OperatingIncomeLoss=_OI)
    rev = mc.annual_series(f, "revenue")
    assert rev.tag == "Revenues" and rev.n_years == 10     # NOT the 4y priority alias
    a = mc.margin_anchor(rev, mc.annual_series(f, "operating_income"))
    assert a.revenue_tag == "Revenues" and a.n_years == 10


def test_short_history_prints_actual_coverage_never_extrapolates() -> None:
    yrs = list(range(2021, 2025))                      # 4y only
    f = _facts(Revenues=dict.fromkeys(yrs, 1000.0),
               OperatingIncomeLoss=dict(zip(yrs, [40., 60., 80., 100.], strict=True)))
    a = mc.margin_anchor(mc.annual_series(f, "revenue"), mc.annual_series(f, "operating_income"))
    assert a.n_years == 4 and not a.covers_window
    assert "SHORT of the 10y window" in a.coverage_note and "NOT extrapolated" in a.coverage_note
    assert a.median == pytest.approx(0.07)             # the ACTUAL 4y median — no synthetic years
    assert a.years == yrs


def _anchor(f: dict[str, Any]) -> mc.MarginAnchor:
    return mc.margin_anchor(mc.annual_series(f, "revenue"), mc.annual_series(f, "operating_income"))


def test_peer_excluded_for_short_history_and_named() -> None:
    f_long = _facts(Revenues=_REV, OperatingIncomeLoss=_OI)
    yrs = list(range(2021, 2025))
    f_short = _facts(Revenues=dict.fromkeys(yrs, 1000.0),
                     OperatingIncomeLoss=dict.fromkeys(yrs, 80.0))
    band = mc.peer_anchor({"LONG": _anchor(f_long), "SHORTY": _anchor(f_short)})
    assert list(band.included) == ["LONG"]
    assert "SHORTY" in band.excluded and "EXCLUDED" in band.excluded["SHORTY"]
    assert "only 4y" in band.excluded["SHORTY"]        # named loudly, with the reason
    assert band.band_median == pytest.approx(0.095)    # short peer never averaged in


def test_fuel_split_both_ways_when_disclosed() -> None:
    f = _facts(Revenues=_REV, OperatingIncomeLoss=_OI,
               FuelSurchargeRevenue=dict.fromkeys(_YEARS, 200.0))
    split = mc.fuel_split(f, mc.annual_series(f, "revenue"),
                          mc.annual_series(f, "operating_income"))
    assert split.disclosed and split.tags_found == ["us-gaap:FuelSurchargeRevenue"]
    assert split.incl is not None and split.excl is not None
    # same operating income over a SMALLER denominator → the ex-surcharge margin is higher
    assert split.incl.median == pytest.approx(0.095)          # 95 / 1000
    assert split.excl.median == pytest.approx(0.11875)        # 95 / 800
    ex_med, in_med = split.excl.median, split.incl.median
    assert ex_med is not None and in_med is not None and ex_med > in_med  # neither picked


def test_fuel_cost_tag_is_not_a_surcharge_disclosure() -> None:
    """WERN's real shape: only `FuelCosts` (an expense) exists. A cost tag must NOT be read as a
    surcharge-revenue disclosure — the split is simply not available."""
    f = _facts(Revenues=_REV, OperatingIncomeLoss=_OI, FuelCosts=dict.fromkeys(_YEARS, 150.0))
    split = mc.fuel_split(f, mc.annual_series(f, "revenue"),
                          mc.annual_series(f, "operating_income"))
    assert not split.disclosed and split.tags_found == []
    assert split.excl is None and "NOT separately XBRL-tagged" in split.note


def test_anchor_default_base_is_labelled() -> None:
    s = mc.build_scenario("base", revenue=1000.0, multiple=8.0, anchor_margin=0.09)
    assert s.margin == pytest.approx(0.09) and s.source == "anchor default"


def test_deviation_without_reason_is_refused() -> None:
    with pytest.raises(mc.ScenarioError) as ei:
        mc.build_scenario("bull", revenue=1000.0, multiple=8.0, anchor_margin=0.09, margin=0.12)
    assert "--reason-bull is required" in str(ei.value)
    ok = mc.build_scenario("bull", revenue=1000.0, multiple=8.0, anchor_margin=0.09, margin=0.12,
                           reason="freight recovery to prior-peak rate per mile")
    assert ok.source == "analyst" and ok.reason


def test_reward_risk_matches_the_convention() -> None:
    """CONVENTION: reward = base − spot; risk = spot − bear, both at SPOT. Bull NEVER in it."""
    rr = mc.reward_risk(base_vps=90.0, bear_vps=20.0, spot=30.0)
    assert rr.reward == pytest.approx(60.0)      # base − spot (NOT bull − spot)
    assert rr.risk == pytest.approx(10.0)        # spot − bear
    assert rr.ratio == pytest.approx(6.0) and rr.clears_bar
    # a bull of any size cannot move the ratio — it is not an input
    assert mc.reward_risk(base_vps=90.0, bear_vps=20.0, spot=30.0).ratio == pytest.approx(6.0)
    assert mc.BAR == 2.0
    assert mc.reward_risk(base_vps=45.0, bear_vps=20.0, spot=30.0).clears_bar is False  # 15/10=1.5


def test_degenerate_cases_fail_loud() -> None:
    bear_above = mc.reward_risk(base_vps=90.0, bear_vps=35.0, spot=30.0)
    assert bear_above.ratio is None
    assert bear_above.undefined == "risk undefined (bear at or above spot)"
    assert bear_above.clears_bar is None
    base_below = mc.reward_risk(base_vps=25.0, bear_vps=20.0, spot=30.0)   # reward negative
    assert base_below.reward == pytest.approx(-5.0) and base_below.risk == pytest.approx(10.0)
    assert base_below.ratio == pytest.approx(-0.5) and base_below.clears_bar is False


def test_scenario_value_bridge() -> None:
    s = mc.Scenario(name="base", revenue=1000.0, margin=0.09, multiple=8.0, source="anchor default")
    v = mc.scenario_value(s, net_debt=200.0, shares=100.0)
    assert v.op_income == pytest.approx(90.0) and v.ev == pytest.approx(720.0)
    assert v.equity == pytest.approx(520.0) and v.vps == pytest.approx(5.2)


def test_sensitivity_grid_math() -> None:
    base = mc.Scenario("base", 1000.0, 0.09, 8.0, "anchor default")
    bear = mc.Scenario("bear", 1000.0, 0.05, 6.0, "analyst", reason="trough")
    rows = mc.sensitivity(base, bear, net_debt=200.0, shares=100.0, spot=3.0)
    assert len(rows) == 9                                   # 3 margins × 3 multiples
    assert {r["d_margin"] for r in rows} == {-0.01, 0.0, 0.01}
    assert {r["d_multiple"] for r in rows} == {-1.0, 0.0, 1.0}
    centre = next(r for r in rows if r["d_margin"] == 0.0 and r["d_multiple"] == 0.0)
    # base vps 5.2, bear vps (1000*.05*6-200)/100 = 1.0 → reward 2.2 / risk 2.0 = 1.1
    assert centre["ratio"] == pytest.approx(1.1)
    up = next(r for r in rows if r["d_margin"] == 0.01 and r["d_multiple"] == 1.0)
    # margin .10 × mult 9 → (900-200)/100 = 7.0 → reward 4.0 / risk 2.0 = 2.0
    assert up["ratio"] == pytest.approx(2.0)


class _StubBundle:
    """A CiqBundle stand-in for the multiple-anchor path — returns Multiples rows or raises."""

    def __init__(self, rows: list[list[Any]] | None) -> None:
        self._rows = rows

    def sheet(self, kind: str, sheet_name: str, *, freq: str | None = None) -> list[list[Any]]:
        from vinci.dossier.ciq import CiqUnavailableError
        if self._rows is None:
            raise CiqUnavailableError("no Multiples sheet")
        return self._rows


def _mult_rows(closes: list[float]) -> list[list[Any]]:
    """A minimal CIQ 'Multiples' block in the shape _multiples_close parses: a period-header row
    (dates at col 2+), the metric label row, then the 'Close' subrow (col 1 == 'Close')."""
    n = len(closes)
    dates = list(range(45000, 45000 + n))                    # serial-date headers at col 2+
    return [
        ["For Quarter Ending", "", *dates],
        ["TEV/LTM EBITDA", "", *([""] * n)],
        ["", "Close", *closes],
    ]


def test_multiple_anchor_absent_ciq_degrades_loudly() -> None:
    """No bundle / no CIQ sheet → UNAVAILABLE, said plainly; never fabricated, never blocks A/B."""
    a = mc.multiple_anchor(None)
    assert not a.available and "UNAVAILABLE — CIQ absent" in a.note and a.median is None
    a2 = mc.multiple_anchor(_StubBundle(None))
    assert not a2.available and "UNAVAILABLE — CIQ absent" in a2.note


def test_multiple_anchor_too_few_closes_is_unavailable() -> None:
    a = mc.multiple_anchor(_StubBundle(_mult_rows([8.0, 9.0, 10.0])))   # <4
    assert not a.available and "too short for a band" in a.note and a.n_quarters == 3


def test_multiple_anchor_band_from_own_history() -> None:
    a = mc.multiple_anchor(_StubBundle(_mult_rows([6.0, 8.0, 10.0, 12.0, 14.0])))
    assert a.available and a.n_quarters == 5
    assert a.trough == pytest.approx(6.0) and a.median == pytest.approx(10.0)
    assert a.upper_quartile == pytest.approx(12.0)          # 75th pct of 6,8,10,12,14
    assert a.source_ref and "TEV/LTM EBITDA" in a.source_ref


def test_assemble_midcycle_units_and_ratio() -> None:
    """End-to-end: $M revenue/net-debt + raw share count → $/share value; ratio per convention;
    sensitivity centre agrees with the main ratio (scale-invariant — pins the unit math)."""
    f = _facts(Revenues=_REV, OperatingIncomeLoss=_OI)   # own margins 5%…14%, median 9.5%
    margin = _anchor(f)
    peers = mc.peer_anchor({"P": _anchor(f)})
    mult = mc.multiple_anchor(None)                       # CIQ absent → anchors still record
    fuel = mc.fuel_split(f, mc.annual_series(f, "revenue"), mc.annual_series(f, "operating_income"))
    scen = [
        mc.build_scenario("bear", revenue=3000.0, multiple=5.0, anchor_margin=0.095, margin=0.03,
                          reason="freight trough persists"),
        mc.build_scenario("base", revenue=3200.0, multiple=6.5, anchor_margin=0.095),  # default
        mc.build_scenario("bull", revenue=3400.0, multiple=8.0, anchor_margin=0.095, margin=0.12,
                          reason="rate recovery to prior peak"),
    ]
    m = mc.assemble_midcycle(margin=margin, fuel=fuel, peers=peers, mult=mult, scenarios=scen,
                             spot=25.0, net_debt_musd=500.0, shares=60_000_000.0)
    base = next(s for s in m.scenarios if s.name == "base")
    # base: 3200×.095=304 op-inc $M ×6.5=1976 EV −500=1476 eq $M → ×1e6/60e6 = $24.60
    assert base.op_income_musd == pytest.approx(304.0) and base.ev_musd == pytest.approx(1976.0)
    assert base.value_per_share == pytest.approx(24.60, abs=0.01)
    assert base.source == "anchor default"
    bear = next(s for s in m.scenarios if s.name == "bear")
    # bear: 3000×.03=90 ×5=450 −500=−50 eq → −$0.833/sh (below spot → real risk)
    assert bear.value_per_share == pytest.approx(-0.833, abs=0.01)
    # reward = 24.60−25 = −0.40 ; risk = 25−(−0.833) = 25.833 → ratio < 0 (base ~ at spot)
    assert m.reward == pytest.approx(-0.40, abs=0.01) and m.risk == pytest.approx(25.833, abs=0.01)
    assert m.ratio is not None and m.clears_bar is False
    # base margin 9.5% → 5 of 10 own margins (5–9%) at-or-below → 50th pct
    assert base.margin_pct_of_own == pytest.approx(0.5)
    # sensitivity centre must equal the main ratio (unit consistency across the two bases)
    centre = next(r for r in m.sensitivity if r["d_margin"] == 0.0 and r["d_multiple"] == 0.0)
    assert centre["ratio"] == pytest.approx(m.ratio)


def test_midcycle_roundtrips_json() -> None:
    """The record is pydantic-serializable (persists in dossier.json, re-loads)."""
    f = _facts(Revenues=_REV, OperatingIncomeLoss=_OI)
    m = mc.assemble_midcycle(margin=_anchor(f), fuel=mc.fuel_split(
        f, mc.annual_series(f, "revenue"), mc.annual_series(f, "operating_income")),
        peers=mc.peer_anchor({}), mult=mc.multiple_anchor(None))     # anchors alone, no scenarios
    dumped = m.model_dump_json()
    back = mc.MidCycle.model_validate_json(dumped)
    assert back.margin_median == pytest.approx(0.095)
    assert back.scenarios == [] and back.ratio is None


def test_percentile_placement() -> None:
    sample = [0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14]
    assert mc.percentile_of(0.13, sample) == pytest.approx(0.9)   # 9 of 10 at-or-below
    assert mc.percentile_of(0.04, sample) == pytest.approx(0.0)
    assert mc.percentile_of(0.5, []) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
