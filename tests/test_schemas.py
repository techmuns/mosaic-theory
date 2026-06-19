"""Step 0 verification — config loads; both schemas instantiate + round-trip; the envelope
coverage contract is enforced (no silent imputes)."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from mosaic.config import get_config
from mosaic.schemas import (
    CandidateRecord,
    CoverageStatus,
    DataField,
    DataRecord,
    Fundamentals,
    GateResult,
    Identity,
    LedgerEntry,
    PriceFeatures,
    SourceTier,
    StressSignals,
    TriageBand,
    TypedEvent,
    Verdict,
)
from mosaic.schemas.candidate import derive_unknown_gates
from mosaic.schemas.data_record import EventType
from mosaic.schemas.ledger import Confidence

AS_OF = date(2026, 6, 1)


# --- config -----------------------------------------------------------------------------------
def test_config_loads_and_paths_derive() -> None:
    cfg = get_config()
    assert cfg.universe.market_cap_min_usd < cfg.universe.market_cap_max_usd
    assert "Nasdaq" in cfg.universe.exchanges
    assert cfg.db_path.name == "mosaic.db"
    assert cfg.snapshots_dir.name == "snapshots"


# --- envelope coverage contract ---------------------------------------------------------------
def test_present_field_is_evaluable() -> None:
    f = DataField.present(-0.42, as_of=AS_OF, source="EOD", tier=SourceTier.DERIVED)
    assert f.is_evaluable and f.is_known
    assert f.coverage_status is CoverageStatus.PRESENT


def test_unknown_field_defers() -> None:
    f: DataField[float] = DataField.unknown(
        source="EDGAR", tier=SourceTier.EDGAR, note="no XBRL tag"
    )
    assert not f.is_evaluable and not f.is_known
    assert f.value is None


def test_stale_field_is_known_but_not_evaluable() -> None:
    f = DataField.stale(101.5, as_of=AS_OF, source="EOD", tier=SourceTier.EOD)
    assert f.is_known and not f.is_evaluable


def test_present_requires_value_and_as_of() -> None:
    with pytest.raises(ValidationError):
        DataField(  # value missing
            value=None,
            as_of=AS_OF,
            source="EOD",
            coverage_status=CoverageStatus.PRESENT,
            source_tier=SourceTier.EOD,
        )
    with pytest.raises(ValidationError):
        DataField(  # as_of missing
            value=1.0,
            as_of=None,
            source="EOD",
            coverage_status=CoverageStatus.PRESENT,
            source_tier=SourceTier.EOD,
        )


def test_unknown_must_not_carry_value() -> None:
    with pytest.raises(ValidationError):
        DataField(
            value=1.0,
            as_of=None,
            source="EDGAR",
            coverage_status=CoverageStatus.UNKNOWN,
            source_tier=SourceTier.EDGAR,
        )


def test_source_tier_ordering() -> None:
    assert SourceTier.EDGAR > SourceTier.IBKR > SourceTier.EOD > SourceTier.NEWS


# --- builders for the composite records -------------------------------------------------------
def _identity() -> Identity:
    return Identity(
        internal_id="SEC-0000320193-AAPL",
        issuer_id="ISS-0000320193",
        cik="0000320193",
        ticker="AAPL",
        mic="XNAS",
        exchange="Nasdaq",
        eod_symbol="AAPL",
        name="Apple Inc.",
        sic="3571",
        sic_description="Electronic Computers",
    )


def _present(v: float) -> DataField[float]:
    return DataField.present(v, as_of=AS_OF, source="EOD", tier=SourceTier.EOD)


def _price_features() -> PriceFeatures:
    return PriceFeatures(
        last=_present(100.0),
        high_52w=_present(180.0),
        low_52w=_present(95.0),
        drawdown_from_high=DataField.present(
            -0.44, as_of=AS_OF, source="EOD", tier=SourceTier.DERIVED
        ),
        dist_from_low=_present(0.05),
        ret_3m=_present(-0.30),
        ret_6m=_present(-0.40),
        ret_12m=_present(-0.45),
        rel_ret_vs_market=DataField.present(
            -0.35, as_of=AS_OF, source="EOD", tier=SourceTier.DERIVED
        ),
        adv_90d_shares=_present(5_000_000.0),
        adv_90d_usd=_present(500_000_000.0),
        turnover=_present(0.01),
        volume_spike=_present(2.1),
    )


def _fundamentals(known: bool = True) -> Fundamentals:
    if known:
        return Fundamentals(
            ev_ebitda=DataField.present(6.0, as_of=AS_OF, source="EDGAR", tier=SourceTier.EDGAR),
            ev_ebitda_pctile_vs_history=DataField.present(
                0.05, as_of=AS_OF, source="EDGAR", tier=SourceTier.DERIVED
            ),
            pe=DataField.present(8.0, as_of=AS_OF, source="EDGAR", tier=SourceTier.EDGAR),
            pe_pctile_vs_history=DataField.present(
                0.08, as_of=AS_OF, source="EDGAR", tier=SourceTier.DERIVED
            ),
            fcf_sign=DataField.present(1, as_of=AS_OF, source="EDGAR", tier=SourceTier.EDGAR),
            op_income_sign=DataField.present(1, as_of=AS_OF, source="EDGAR", tier=SourceTier.EDGAR),
            net_leverage=DataField.present(1.5, as_of=AS_OF, source="EDGAR", tier=SourceTier.EDGAR),
        )
    u: DataField[float] = DataField.unknown(
        source="EDGAR", tier=SourceTier.EDGAR, note="sparse XBRL"
    )
    ui: DataField[int] = DataField.unknown(source="EDGAR", tier=SourceTier.EDGAR)
    return Fundamentals(
        ev_ebitda=u,
        ev_ebitda_pctile_vs_history=u,
        pe=u,
        pe_pctile_vs_history=u,
        fcf_sign=ui,
        op_income_sign=ui,
        net_leverage=u,
    )


def _stress() -> StressSignals:
    return StressSignals(
        iv_pctile=DataField.unknown(source="IBKR", tier=SourceTier.IBKR, note="deferred in Loop 1"),
        short_interest=DataField.unknown(source="IBKR", tier=SourceTier.IBKR),
    )


def _data_record(known_fundamentals: bool = True) -> DataRecord:
    return DataRecord(
        identity=_identity(),
        market_cap=_present(1_600_000_000.0),
        prices=_price_features(),
        fundamentals=_fundamentals(known_fundamentals),
        stress=_stress(),
        events=[
            TypedEvent(
                event_type=EventType.GUIDANCE_CUT,
                event_date=date(2026, 5, 20),
                source="EDGAR 8-K",
                accession="0000320193-26-000050",
            )
        ],
        as_of=AS_OF,
    )


# --- data-record + candidate round-trips ------------------------------------------------------
def test_data_record_round_trip() -> None:
    rec = _data_record()
    restored = DataRecord.model_validate_json(rec.model_dump_json())
    assert restored == rec
    assert restored.prices.drawdown_from_high.value == pytest.approx(-0.44)


def test_candidate_admissibility_and_unknowns() -> None:
    gates = {
        "G1_drawdown": GateResult.PASS,
        "G2_idiosyncratic": GateResult.PASS,
        "G3_multiple_floor": GateResult.UNKNOWN,
    }
    cand = CandidateRecord(
        candidate_id="AAPL-screen2-20260601",
        data_record=_data_record(known_fundamentals=False),
        screens_fired=["screen_2"],
        gate_results=gates,
        trigger_reason="guidance-cut 8-K + -44% drawdown",
        unknown_gates_for_depth=derive_unknown_gates(gates),
        twin_to_rule_out="terminal decline",
        triage_band=TriageBand.A,
        screen_run_at=datetime(2026, 6, 1, 12, 0, 0),
    )
    assert cand.is_admissible  # no FAIL
    assert cand.has_unresolved_depth_tasks
    assert cand.unknown_gates_for_depth == ["G3_multiple_floor"]
    restored = CandidateRecord.model_validate_json(cand.model_dump_json())
    assert restored == cand


def test_candidate_with_fail_is_not_admissible() -> None:
    gates = {"G1_drawdown": GateResult.FAIL, "G2_idiosyncratic": GateResult.PASS}
    cand = CandidateRecord(
        candidate_id="X-screen2",
        data_record=_data_record(),
        screens_fired=["screen_2"],
        gate_results=gates,
        trigger_reason="t",
        unknown_gates_for_depth=[],
        twin_to_rule_out="terminal decline",
        triage_band=TriageBand.C,
        screen_run_at=datetime(2026, 6, 1, 12, 0, 0),
    )
    assert not cand.is_admissible


# --- ledger round-trip + invariants -----------------------------------------------------------
def test_ledger_entry_round_trip_and_freeze() -> None:
    entry = LedgerEntry(
        entry_id="led-0001",
        candidate_id="AAPL-screen2-20260601",
        internal_id="SEC-0000320193-AAPL",
        ticker="AAPL",
        verdict=Verdict.BUY,
        twin_call="Not terminal: one-off supply hit, demand intact; reversal = restocking.",
        entry_price=100.0,
        entry_price_as_of=AS_OF,
        thesis="Overshoot on a transient guidance miss.",
        kill_criteria="Two consecutive quarters of accelerating revision cuts.",
        horizon_days=180,
        confidence=Confidence.MEDIUM,
        decided_at=datetime(2026, 6, 1, 15, 30, 0),
    )
    restored = LedgerEntry.model_validate_json(entry.model_dump_json())
    assert restored == entry
    assert restored.entry_price_as_of == AS_OF


def test_ledger_rejects_nonpositive_price() -> None:
    with pytest.raises(ValidationError):
        LedgerEntry(
            entry_id="x",
            candidate_id="c",
            internal_id="i",
            ticker="T",
            verdict=Verdict.AVOID_TERMINAL,
            twin_call="t",
            entry_price=0.0,
            entry_price_as_of=AS_OF,
            thesis="t",
            kill_criteria="k",
            horizon_days=90,
            confidence=Confidence.LOW,
            decided_at=datetime(2026, 6, 1, 0, 0, 0),
        )
