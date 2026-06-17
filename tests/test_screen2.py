"""Step 5 verification — Screen 2 gates + the G2/G3 derived inputs (synthetic, deterministic)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from mosaic.edgar.concepts import ConceptPoint
from mosaic.schemas.candidate import GateResult
from mosaic.schemas.data_record import (
    CoverageTier,
    DataRecord,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
)
from mosaic.schemas.envelope import CoverageStatus, DataField, SourceTier
from mosaic.schemas.market import PriceBar
from mosaic.screens import (
    Screen2Thresholds,
    annual_eps_as_of,
    detect_gap_downs,
    evaluate_screen2,
    gate_g1_drawdown,
    gate_g2_idiosyncratic,
    gate_g3_multiple_floor,
    pe_current_and_percentile,
)

REF = date(2026, 6, 15)
TH = Screen2Thresholds()


def _f(v: float | None) -> DataField[float]:
    if v is None:
        return DataField.unknown(source="EOD", tier=SourceTier.DERIVED)
    return DataField.present(v, as_of=REF, source="EOD", tier=SourceTier.DERIVED)


def _rec(*, drawdown: float | None, rel: float | None, pe_pctile: float | None) -> DataRecord:
    ident = Identity(
        internal_id="SEC-X-FOO",
        issuer_id="ISS-X",
        cik="0000000001",
        ticker="FOO",
        mic="XNAS",
        exchange="Nasdaq",
        eod_symbol="FOO",
        name="Foo Inc.",
    )
    prices = PriceFeatures(
        last=_f(100.0),
        high_52w=_f(180.0),
        low_52w=_f(95.0),
        drawdown_from_high=_f(drawdown),
        dist_from_low=_f(0.05),
        ret_3m=_f(-0.3),
        ret_6m=_f(-0.4),
        ret_12m=_f(-0.45),
        rel_ret_vs_sector=_f(rel),
        adv_90d_shares=_f(5e6),
        adv_90d_usd=_f(5e8),
        turnover=_f(0.01),
        volume_spike=_f(2.0),
    )
    funds = Fundamentals(
        ev_ebitda=_f(6.0),
        ev_ebitda_pctile_vs_history=_f(None),  # EV multiple deferred
        pe=_f(8.0),
        pe_pctile_vs_history=_f(pe_pctile),
        fcf_sign=DataField.present(1, as_of=REF, source="EDGAR", tier=SourceTier.EDGAR),
        op_income_sign=DataField.present(1, as_of=REF, source="EDGAR", tier=SourceTier.EDGAR),
        net_leverage=_f(1.5),
    )
    u: DataField[float] = DataField.unknown(source="IBKR", tier=SourceTier.IBKR)
    return DataRecord(
        identity=ident,
        market_cap=_f(1.6e9),
        prices=prices,
        fundamentals=funds,
        stress=StressSignals(iv_pctile=u, short_interest=u),
        overall_coverage_tier=CoverageTier.US_FULL,
        as_of=REF,
    )


# --- gates ------------------------------------------------------------------------------------
def test_g1_drawdown() -> None:
    assert gate_g1_drawdown(_rec(drawdown=-0.44, rel=-0.3, pe_pctile=0.1), TH)[0] is GateResult.PASS
    assert gate_g1_drawdown(_rec(drawdown=-0.10, rel=-0.3, pe_pctile=0.1), TH)[0] is GateResult.FAIL
    assert (
        gate_g1_drawdown(_rec(drawdown=None, rel=-0.3, pe_pctile=0.1), TH)[0] is GateResult.UNKNOWN
    )


def test_g2_idiosyncratic() -> None:
    assert (
        gate_g2_idiosyncratic(_rec(drawdown=-0.4, rel=-0.35, pe_pctile=0.1), TH)[0]
        is GateResult.PASS
    )
    assert (
        gate_g2_idiosyncratic(_rec(drawdown=-0.4, rel=-0.05, pe_pctile=0.1), TH)[0]
        is GateResult.FAIL
    )
    assert (
        gate_g2_idiosyncratic(_rec(drawdown=-0.4, rel=None, pe_pctile=0.1), TH)[0]
        is GateResult.UNKNOWN
    )


def test_g3_multiple_floor() -> None:
    assert (
        gate_g3_multiple_floor(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.05), TH)[0]
        is GateResult.PASS
    )
    assert (
        gate_g3_multiple_floor(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.80), TH)[0]
        is GateResult.FAIL
    )
    assert (
        gate_g3_multiple_floor(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=None), TH)[0]
        is GateResult.UNKNOWN
    )


# --- admission --------------------------------------------------------------------------------
def test_admitted_clean_de_rating() -> None:
    cand = evaluate_screen2(
        _rec(drawdown=-0.44, rel=-0.35, pe_pctile=0.05), screen_run_at=datetime(2026, 6, 15, 12, 0)
    )
    assert cand is not None
    assert cand.gate_results == {
        "G1_drawdown": GateResult.PASS,
        "G2_idiosyncratic": GateResult.PASS,
        "G3_multiple_floor": GateResult.PASS,
    }
    assert cand.twin_to_rule_out == "terminal decline"


def test_admitted_with_g3_deferred() -> None:
    # G3 UNKNOWN (e.g. negative earnings) does not block — it becomes a depth task
    cand = evaluate_screen2(
        _rec(drawdown=-0.44, rel=-0.35, pe_pctile=None), screen_run_at=datetime(2026, 6, 15, 12, 0)
    )
    assert cand is not None
    assert "G3_multiple_floor" in cand.unknown_gates_for_depth


def test_not_admitted_when_a_gate_fails() -> None:
    # idiosyncratic FAIL (fell with the market) -> rejected
    assert (
        evaluate_screen2(
            _rec(drawdown=-0.44, rel=-0.02, pe_pctile=0.05), screen_run_at=datetime(2026, 6, 15)
        )
        is None
    )


def test_not_admitted_when_drawdown_too_shallow() -> None:
    assert (
        evaluate_screen2(
            _rec(drawdown=-0.10, rel=-0.35, pe_pctile=0.05), screen_run_at=datetime(2026, 6, 15)
        )
        is None
    )


# --- derived inputs (pure) --------------------------------------------------------------------
def _eps(period_end: date, filed: date, val: float) -> ConceptPoint:
    return ConceptPoint(
        concept="eps_diluted",
        tag="EarningsPerShareDiluted",
        unit="USD/shares",
        value=val,
        period_start=date(period_end.year, 1, 1),
        period_end=period_end,
        filed=filed,
        fy=period_end.year,
        fp="FY",
        form="10-K",
        accession="a",
    )


EPS_POINTS = [
    _eps(date(2024, 12, 31), date(2025, 2, 1), 10.0),
    _eps(date(2025, 12, 31), date(2026, 2, 1), 5.0),
]


def test_annual_eps_as_of_point_in_time() -> None:
    assert annual_eps_as_of(EPS_POINTS, date(2025, 6, 1)) == 10.0  # FY2025 not filed yet
    assert annual_eps_as_of(EPS_POINTS, date(2026, 6, 1)) == 5.0  # FY2025 now known
    neg = [_eps(date(2025, 12, 31), date(2026, 2, 1), -1.0)]
    assert annual_eps_as_of(neg, date(2026, 6, 1)) is None  # negative EPS -> no usable P/E


def _daily(start: date, n: int, close_fn) -> list[PriceBar]:
    return [
        PriceBar(
            internal_id="X",
            bar_date=start + timedelta(days=i),
            open=close_fn(i),
            high=close_fn(i) + 1,
            low=close_fn(i) - 1,
            close=close_fn(i),
            volume=1e6,
            source="t",
        )
        for i in range(n)
    ]


def test_pe_percentile_at_floor_when_price_declines() -> None:
    # EPS constant (10); price declines 200 -> ~55 over the window -> current P/E is the lowest
    eps = [_eps(date(2024, 12, 31), date(2025, 1, 1), 10.0)]
    bars = _daily(date(2025, 1, 5), 160, lambda i: 200.0 - i)  # 200 down to 41
    pe, pctile = pe_current_and_percentile(
        bars, eps, reference_date=date(2025, 1, 5) + timedelta(days=159), min_points=120
    )
    assert pe.value == pytest.approx((200.0 - 159) / 10.0)
    assert (
        pctile.value is not None and pctile.value <= 0.05
    )  # current P/E at the bottom of its range


def test_pe_percentile_defers_on_short_history() -> None:
    # with the production default (~2y), a ~5-month window is too short to judge "at floor" -> defer
    eps = [_eps(date(2024, 12, 31), date(2025, 1, 1), 10.0)]
    bars = _daily(date(2025, 1, 5), 160, lambda i: 200.0 - i)
    pe, pctile = pe_current_and_percentile(
        bars, eps, reference_date=date(2025, 1, 5) + timedelta(days=159)
    )
    assert pe.value is not None  # current P/E still known
    assert pctile.coverage_status is CoverageStatus.UNKNOWN  # floor judgment defers to depth


def test_pe_percentile_uses_point_in_time_eps_not_just_price() -> None:
    # price flat (100); window straddles the FY2025 10-K (filed 2026-02-01) where EPS halves 10->5,
    # so P/E steps 10 -> 20 on earnings alone. Current P/E (20) is the TOP of its own history.
    start = date(2025, 9, 1)
    bars = _daily(start, 290, lambda i: 100.0)  # spans the 2026-02-01 filing
    ref = start + timedelta(days=289)
    pe, pctile = pe_current_and_percentile(bars, EPS_POINTS, reference_date=ref, min_points=120)
    assert pe.value == pytest.approx(20.0)  # 100 / FY2025 EPS 5
    assert pctile.value is not None and pctile.value >= 0.95  # expensive vs its EPS-driven history


def test_detect_gap_downs() -> None:
    bars = [
        PriceBar(
            internal_id="X",
            bar_date=date(2026, 3, 1),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=1e6,
            source="t",
        ),
        PriceBar(
            internal_id="X",
            bar_date=date(2026, 3, 2),
            open=88,
            high=89,
            low=85,
            close=86,
            volume=1e6,
            source="t",
        ),  # -14%
        PriceBar(
            internal_id="X",
            bar_date=date(2026, 3, 3),
            open=86,
            high=88,
            low=85,
            close=85,
            volume=1e6,
            source="t",
        ),  # -1%
    ]
    assert detect_gap_downs(bars, since=date(2026, 1, 1)) == [date(2026, 3, 2)]
    assert detect_gap_downs(bars, since=date(2026, 3, 3)) == []  # since-filter excludes it
