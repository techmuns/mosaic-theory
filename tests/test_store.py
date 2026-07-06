"""Step 2 verification — the SQLite store.

Covers: schema init; entity/universe/candidate/ledger round-trips; the **coverage default**
(an absent price reads back UNKNOWN, never a silent 0); price staleness; append-only ledger;
and the durable **snapshot → rebuild** round-trip (with bulk prices intentionally NOT snapshotted).
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

import pytest

from vinci.schemas.candidate import CandidateRecord, GateResult, TriageBand
from vinci.schemas.data_record import (
    CoverageTier,
    DataRecord,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
)
from vinci.schemas.envelope import CoverageStatus, DataField, SourceTier
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.store import Store

AS_OF = date(2026, 6, 10)


def _identity(internal_id: str = "SEC-0000320193-AAPL") -> Identity:
    return Identity(
        internal_id=internal_id,
        issuer_id="ISS-0000320193",
        cik="0000320193",
        ticker="AAPL",
        mic="XNAS",
        exchange="Nasdaq",
        eod_symbol="AAPL",
        name="Apple Inc.",
        sic="3571",
        sic_description=None,  # not stored on the security row
        currency="USD",
    )


def _u(source: str = "EDGAR") -> DataField[float]:
    return DataField.unknown(source=source, tier=SourceTier.EDGAR)


def _data_record(ident: Identity) -> DataRecord:
    def p(v: float) -> DataField[float]:
        return DataField.present(v, as_of=AS_OF, source="EOD", tier=SourceTier.EOD)

    def d(v: float) -> DataField[float]:
        return DataField.present(v, as_of=AS_OF, source="EOD", tier=SourceTier.DERIVED)

    prices = PriceFeatures(
        last=p(100.0), high_52w=p(180.0), low_52w=p(95.0),
        drawdown_from_high=d(-0.44),
        dist_from_low=p(0.05), ret_3m=p(-0.3), ret_6m=p(-0.4), ret_12m=p(-0.45),
        rel_ret_vs_market=d(-0.35),
        adv_90d_shares=p(5e6), adv_90d_usd=p(5e8), turnover=p(0.01), volume_spike=p(2.1),
    )
    fund = Fundamentals(
        ev_ebitda=_u(), ev_ebitda_pctile_vs_history=_u(), pe=_u(),
        pe_pctile_vs_history=_u(), fcf_sign=_u(), op_income_sign=_u(), net_leverage=_u(),
    )
    stress = StressSignals(iv_pctile=_u("IBKR"), short_interest=_u("IBKR"))
    return DataRecord(
        identity=ident, market_cap=p(1.6e9), prices=prices, fundamentals=fund,
        stress=stress, overall_coverage_tier=CoverageTier.US_FULL, as_of=AS_OF,
    )


def _candidate(ident: Identity) -> CandidateRecord:
    gates = {"G1_drawdown": GateResult.PASS, "G3_multiple_floor": GateResult.UNKNOWN}
    return CandidateRecord(
        candidate_id="AAPL-screen2-20260610",
        data_record=_data_record(ident),
        screens_fired=["screen_2"],
        gate_results=gates,
        trigger_reason="guidance-cut 8-K + -44% drawdown",
        unknown_gates_for_depth=["G3_multiple_floor"],
        twin_to_rule_out="terminal decline",
        triage_band=TriageBand.A,
        screen_run_at=datetime(2026, 6, 10, 12, 0, 0),
    )


def _ledger_entry(ident: Identity) -> LedgerEntry:
    return LedgerEntry(
        entry_id="led-0001",
        candidate_id="AAPL-screen2-20260610",
        internal_id=ident.internal_id,
        ticker="AAPL",
        verdict=Verdict.BUY,
        twin_call="Not terminal: one-off supply hit; reversal = restocking.",
        entry_price=100.0,
        entry_price_as_of=AS_OF,
        thesis="Overshoot on transient miss.",
        kill_criteria="Two quarters of accelerating cuts.",
        horizon_days=180,
        confidence=Confidence.MEDIUM,
        decided_at=datetime(2026, 6, 10, 15, 30, 0),
    )


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "test.db")


# --- entity master ----------------------------------------------------------------------------
def test_security_round_trip(store: Store) -> None:
    ident = _identity()
    store.upsert_security(ident, first_seen=AS_OF)
    got = store.get_security(ident.internal_id)
    assert got == ident
    assert [s.internal_id for s in store.iter_securities()] == [ident.internal_id]


def test_get_missing_security_is_none(store: Store) -> None:
    assert store.get_security("SEC-0000000000-NOPE") is None


# --- coverage default: the core reliability property ------------------------------------------
def test_absent_price_reads_back_unknown_not_zero(store: Store) -> None:
    field = store.latest_close("SEC-0000000000-NOPE", reference_date=AS_OF, staleness_days=5)
    assert field.coverage_status is CoverageStatus.UNKNOWN
    assert field.value is None  # never a silent 0


def test_price_round_trip_and_staleness(store: Store) -> None:
    ident = _identity()
    store.upsert_security(ident, first_seen=AS_OF)
    bars = [
        PriceBar(internal_id=ident.internal_id, bar_date=date(2026, 6, 8), open=99, high=101,
                 low=98, close=100, volume=5e6, source="polygon-grouped"),
        PriceBar(internal_id=ident.internal_id, bar_date=date(2026, 6, 9), open=100, high=102,
                 low=99, close=101, volume=4e6, source="polygon-grouped"),
    ]
    assert store.write_prices(bars) == 2
    assert len(store.get_price_history(ident.internal_id)) == 2

    fresh = store.latest_close(
        ident.internal_id, reference_date=date(2026, 6, 11), staleness_days=5
    )
    assert fresh.coverage_status is CoverageStatus.PRESENT
    assert fresh.value == pytest.approx(101.0)

    old = store.latest_close(ident.internal_id, reference_date=date(2026, 7, 1), staleness_days=5)
    assert old.coverage_status is CoverageStatus.STALE
    assert old.value == pytest.approx(101.0)  # value retained, but flagged stale


def test_close_as_of_never_looks_ahead_and_fails_loud(store: Store) -> None:
    """The entry-price freeze must clamp to bar_date <= reference_date and fail loud on no bar."""
    ident = _identity()
    store.upsert_security(ident, first_seen=AS_OF)
    store.write_prices([
        PriceBar(internal_id=ident.internal_id, bar_date=date(2026, 1, 5), open=100, high=100,
                 low=100, close=100.0, volume=1e6, source="t"),  # the as-of bar
        PriceBar(internal_id=ident.internal_id, bar_date=date(2026, 1, 12), open=120, high=120,
                 low=120, close=120.0, volume=1e6, source="t"),  # a FUTURE bar
    ])
    # the lookahead guard: freezing as of 2026-01-05 returns the 100 bar, NOT the future 120
    frozen = store.close_as_of(ident.internal_id, reference_date=date(2026, 1, 5), staleness_days=5)
    assert frozen.coverage_status is CoverageStatus.PRESENT
    assert frozen.value == pytest.approx(100.0)
    assert frozen.as_of == date(2026, 1, 5)
    # contrast: the unclamped latest_close WOULD grab the future 120 bar — the trapdoor we shut
    assert store.latest_close(
        ident.internal_id, reference_date=date(2026, 1, 5), staleness_days=30
    ).value == pytest.approx(120.0)
    # fail-loud: no bar on or before the date → raise (never reach forward, never return nothing)
    with pytest.raises(LookupError):
        store.close_as_of(ident.internal_id, reference_date=date(2026, 1, 1), staleness_days=5)
    # staleness still applies on top: a too-old PRIOR bar comes back STALE (surfaced)
    stale = store.close_as_of(ident.internal_id, reference_date=date(2026, 3, 1), staleness_days=5)
    assert stale.coverage_status is CoverageStatus.STALE
    assert stale.value == pytest.approx(120.0)  # latest bar <= 2026-03-01 is the 2026-01-12 one


# --- universe membership ----------------------------------------------------------------------
def test_universe_membership(store: Store) -> None:
    ident = _identity()
    store.upsert_security(ident, first_seen=AS_OF)
    cap = DataField.present(1.6e9, as_of=AS_OF, source="DERIVED", tier=SourceTier.DERIVED)
    store.record_universe(
        as_of=AS_OF, internal_id=ident.internal_id, in_universe=True, market_cap=cap
    )
    other = _identity("SEC-0000000001-XXXX")
    store.record_universe(
        as_of=AS_OF, internal_id=other.internal_id, in_universe=False,
        market_cap=DataField.unknown(source="DERIVED", tier=SourceTier.DERIVED),
    )
    assert store.get_universe(AS_OF) == [ident.internal_id]


# --- candidate + ledger -----------------------------------------------------------------------
def test_candidate_round_trip(store: Store) -> None:
    ident = _identity()
    store.upsert_security(ident, first_seen=AS_OF)
    cand = _candidate(ident)
    store.save_candidate(cand)
    assert store.get_candidate(cand.candidate_id) == cand


def test_clear_candidates_is_a_full_replace(store: Store) -> None:
    # a re-screen is a clean snapshot: clear_candidates() is a FULL replace (not run-scoped), so
    # ANY prior candidate is dropped — a name removed from the universe, or a whole earlier screen
    # generation, never lingers as a stale candidate (no cross-run accretion).
    ident = _identity()
    store.upsert_security(ident, first_seen=AS_OF)
    cand = _candidate(ident)
    store.save_candidate(cand)
    store.clear_candidates()
    assert store.get_candidate(cand.candidate_id) is None


def test_clear_universe_is_a_full_replace(store: Store) -> None:
    # a universe REBUILD is a clean snapshot: clear_universe() is a FULL replace across ALL as_of,
    # so a prior generation never lingers. The old per-as_of clear let an earlier build's rows
    # survive on a persistent DB (run_weekly reloads last build's snapshot, then build_universe
    # writes today's → both lingered), doubling the exported universe_snapshot with duplicate
    # internal_ids across as_of. Simulate a rebuild (day1 → clear → day2); ONLY day2 may remain.
    ident = _identity()
    store.upsert_security(ident, first_seen=AS_OF)
    cap = DataField.present(1.6e9, as_of=AS_OF, source="DERIVED", tier=SourceTier.DERIVED)
    day1, day2 = date(2026, 6, 17), date(2026, 7, 6)
    store.record_universe(
        as_of=day1, internal_id=ident.internal_id, in_universe=True, market_cap=cap
    )
    store.clear_universe()  # rebuild = FULL replace (old clear(day2) left the day1 generation)
    store.record_universe(
        as_of=day2, internal_id=ident.internal_id, in_universe=True, market_cap=cap
    )
    assert store.get_universe(day1) == []                    # prior generation gone (no accretion)
    assert store.get_universe(day2) == [ident.internal_id]   # only the rebuilt generation remains
    assert store.latest_universe(day2) == [ident.internal_id]


def test_ledger_append_get_iter_and_no_dup(store: Store) -> None:
    ident = _identity()
    store.upsert_security(ident, first_seen=AS_OF)
    entry = _ledger_entry(ident)
    store.append_ledger(entry)
    assert store.get_ledger_entry("led-0001") == entry
    assert [e.entry_id for e in store.iter_ledger()] == ["led-0001"]
    with pytest.raises(sqlite3.IntegrityError):  # append-only: no overwriting a verdict
        store.append_ledger(entry)


# --- durable snapshot round-trip --------------------------------------------------------------
def test_snapshot_export_and_rebuild(tmp_path: Path) -> None:
    snap = tmp_path / "snapshots"
    ident = _identity()
    with Store(tmp_path / "a.db") as a:
        a.upsert_security(ident, first_seen=AS_OF)
        cap = DataField.present(1.6e9, as_of=AS_OF, source="DERIVED", tier=SourceTier.DERIVED)
        a.record_universe(
            as_of=AS_OF, internal_id=ident.internal_id, in_universe=True, market_cap=cap
        )
        a.save_candidate(_candidate(ident))
        a.append_ledger(_ledger_entry(ident))
        a.write_prices([
            PriceBar(internal_id=ident.internal_id, bar_date=AS_OF, open=99, high=101, low=98,
                     close=100, volume=5e6, source="polygon-grouped")
        ])
        counts = a.export_snapshots(snap)

    assert counts["securities"] == 1 and counts["decision_ledger"] == 1
    assert "prices" not in counts  # bulk prices are re-pullable, not snapshotted

    # rebuild into a fresh DB and confirm the durable state matches
    with Store(tmp_path / "b.db") as b:
        b.rebuild_from_snapshots(snap)
        assert b.get_security(ident.internal_id) == ident
        assert b.get_universe(AS_OF) == [ident.internal_id]
        assert b.get_candidate("AAPL-screen2-20260610") is not None
        assert b.get_ledger_entry("led-0001") == _ledger_entry(ident)
        # prices were not snapshotted → absent in the rebuilt DB (re-pull from Polygon)
        assert b.get_price_history(ident.internal_id) == []
