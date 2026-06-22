"""Step 6 verification — the decision-ledger entry workflow.

Confirms the entry price is frozen from the store at decision time, both BUY and AVOID verdicts
persist, the ledger is append-only (re-logging fails loud), and missing candidate / missing price
raise rather than recording a verdict with no anchor.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

import pytest

from mosaic.ledger import LedgerError, log_verdict
from mosaic.schemas.candidate import CandidateRecord, GateResult, TriageBand
from mosaic.schemas.data_record import (
    CoverageTier,
    DataRecord,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
)
from mosaic.schemas.envelope import DataField, SourceTier
from mosaic.schemas.ledger import Confidence, Verdict
from mosaic.schemas.market import PriceBar
from mosaic.scoring.metrics import VerdictScore, spread_by_sector
from mosaic.store import Store


def _u() -> DataField[float]:
    return DataField.unknown(source="X", tier=SourceTier.DERIVED)


def _ident(ticker: str, iid: str, cik: str) -> Identity:
    return Identity(
        internal_id=iid, issuer_id=f"ISS-{cik}", cik=cik, ticker=ticker,
        mic="XNYS", exchange="NYSE", eod_symbol=ticker, name=f"{ticker} Inc.",
    )


def _min_record(ident: Identity) -> DataRecord:
    ui: DataField[int] = DataField.unknown(source="X", tier=SourceTier.EDGAR)
    prices = PriceFeatures(
        last=_u(), high_52w=_u(), low_52w=_u(), drawdown_from_high=_u(), dist_from_low=_u(),
        ret_3m=_u(), ret_6m=_u(), ret_12m=_u(), rel_ret_vs_market=_u(),
        adv_90d_shares=_u(), adv_90d_usd=_u(), turnover=_u(), volume_spike=_u(),
    )
    funds = Fundamentals(
        ev_ebitda=_u(), ev_ebitda_pctile_vs_history=_u(), pe=_u(), pe_pctile_vs_history=_u(),
        fcf_sign=ui, op_income_sign=ui, net_leverage=_u(),
    )
    return DataRecord(
        identity=ident, market_cap=_u(), prices=prices, fundamentals=funds,
        stress=StressSignals(iv_pctile=_u(), short_interest=_u()),
        overall_coverage_tier=CoverageTier.US_FULL, as_of=date(2026, 6, 12),
    )


def _candidate(ident: Identity) -> CandidateRecord:
    return CandidateRecord(
        candidate_id=f"{ident.ticker}-screen2-20260612",
        data_record=_min_record(ident),
        screens_fired=["screen_2"],
        gate_results={"G1_drawdown": GateResult.PASS, "G3_multiple_floor": GateResult.UNKNOWN},
        trigger_reason="drawdown -44%",
        unknown_gates_for_depth=["G3_multiple_floor"],
        twin_to_rule_out="terminal decline",
        triage_band=TriageBand.B,
        screen_run_at=datetime(2026, 6, 12, 12, 0),
    )


def _seed(store: Store, ident: Identity, *, close: float = 44.93) -> str:
    store.upsert_security(ident)
    cand = _candidate(ident)
    store.save_candidate(cand)
    store.write_prices([
        PriceBar(internal_id=ident.internal_id, bar_date=date(2026, 6, 12), open=44.0, high=45.0,
                 low=43.0, close=close, volume=1e7, source="polygon-grouped")
    ])
    return cand.candidate_id


class _StubResolver:
    """A minimal SicSource for tests — returns a fixed SIC so sector-tagging is deterministic."""

    def __init__(self, sic: str = "7372") -> None:  # 7372 = prepackaged software → Technology
        self._sic = sic

    def sic_for(self, cik: int | str) -> tuple[str | None, str | None]:
        return self._sic, None


_KW = dict(  # noqa: C408 — common verdict kwargs
    resolver=_StubResolver(),
    twin_call="One-off demand air-pocket; brand intact; reversal = inventory reset.",
    thesis="Overshoot on a transient guidance miss.",
    kill_criteria="Two consecutive quarters of accelerating revision cuts.",
    horizon_days=180,
    confidence=Confidence.MEDIUM,
    reference_date=date(2026, 6, 15),
    staleness_days=5,
)


def test_log_buy_freezes_entry_price(tmp_path: Path) -> None:
    with Store(tmp_path / "t.db") as store:
        ident = _ident("NKE", "SEC-0000320187-NKE", "0000320187")
        cid = _seed(store, ident, close=44.93)
        entry = log_verdict(
            store, candidate_id=cid, verdict=Verdict.BUY,
            decided_at=datetime(2026, 6, 15, 10, 0), **_KW,
        )
        assert entry.entry_price == pytest.approx(44.93)  # frozen from the 2026-06-12 close
        assert entry.entry_price_as_of == date(2026, 6, 12)
        stored = store.get_ledger_entry("V-NKE-screen2-20260612")
        assert stored is not None and stored.verdict is Verdict.BUY


def test_log_avoid_and_append_only(tmp_path: Path) -> None:
    with Store(tmp_path / "t.db") as store:
        ident = _ident("XYZ", "SEC-0000000009-XYZ", "0000000009")
        cid = _seed(store, ident)
        log_verdict(store, candidate_id=cid, verdict=Verdict.AVOID_TERMINAL,
                    decided_at=datetime(2026, 6, 15, 10, 0), **_KW)
        assert [e.verdict for e in store.iter_ledger()] == [Verdict.AVOID_TERMINAL]
        # re-logging the same candidate must fail loud (a verdict is never silently overwritten)
        with pytest.raises(sqlite3.IntegrityError):
            log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                        decided_at=datetime(2026, 6, 16, 10, 0), **_KW)


def test_unknown_candidate_raises(tmp_path: Path) -> None:
    with Store(tmp_path / "t.db") as store, pytest.raises(LedgerError):
        log_verdict(store, candidate_id="NOPE-screen2-20260612", verdict=Verdict.BUY,
                    decided_at=datetime(2026, 6, 15), **_KW)


def test_no_price_raises(tmp_path: Path) -> None:
    with Store(tmp_path / "t.db") as store:
        ident = _ident("DRY", "SEC-0000000010-DRY", "0000000010")
        store.upsert_security(ident)
        store.save_candidate(_candidate(ident))  # candidate saved but NO price bars written
        with pytest.raises(LedgerError):
            log_verdict(store, candidate_id="DRY-screen2-20260612", verdict=Verdict.BUY,
                        decided_at=datetime(2026, 6, 15), **_KW)


def test_verdict_carries_its_sector(tmp_path: Path) -> None:
    """A verdict is sector-tagged at log time from the name's EDGAR SIC, frozen + round-tripped."""
    with Store(tmp_path / "t.db") as store:
        ident = _ident("PHRM", "SEC-0000000011-PHRM", "0000000011")
        cid = _seed(store, ident)
        kw = {**_KW, "resolver": _StubResolver("2834")}  # 2834 = pharmaceuticals → Health Care
        entry = log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                            decided_at=datetime(2026, 6, 15, 10, 0), **kw)
        assert entry.sector == "Health Care"  # captured from the SIC at log time
        stored = store.get_ledger_entry(entry.entry_id)
        assert stored is not None and stored.sector == "Health Care"  # frozen + survives round-trip


def test_spread_groups_by_sector_and_is_honest_until_enough() -> None:
    """The spread reads PER-SECTOR; a sector returns 'insufficient data' until both legs are real,
    and an untagged verdict (sector None, like the pre-feature VRRM) buckets under 'Unknown'."""
    def vs(t: str, verdict: Verdict, ret: float, sector: str | None) -> VerdictScore:
        return VerdictScore(entry_id=f"V-{t}", ticker=t, verdict=verdict, resolved=True,
                            name_return=ret, bench_return=0.0, sector=sector)

    scores = [
        vs("A", Verdict.BUY, 0.20, "Technology"), vs("B", Verdict.BUY, 0.10, "Technology"),
        vs("C", Verdict.AVOID_TERMINAL, -0.20, "Technology"),
        vs("D", Verdict.AVOID_TERMINAL, -0.10, "Technology"),
        vs("E", Verdict.BUY, 0.30, "Energy"),  # Energy: 1 buy, 0 avoid → insufficient
        vs("F", Verdict.BUY, 0.05, None),  # untagged → buckets under "Unknown"
    ]
    by = spread_by_sector(scores, min_per_leg=2)

    tech = by["Technology"]
    assert tech.sufficient and tech.spread == pytest.approx(0.30)  # 0.15 − (−0.15)
    assert by["Energy"].sufficient is False and by["Energy"].spread is None  # honest insufficient
    assert by["Energy"].n_buy == 1 and by["Energy"].n_avoid == 0
    assert "Unknown" in by and by["Unknown"].n_buy == 1 and by["Unknown"].sufficient is False
