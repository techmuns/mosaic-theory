"""Step 6 verification — the decision-ledger entry workflow.

Confirms the entry price is frozen from the store at decision time, both BUY and AVOID verdicts
persist, the ledger is append-only (re-logging fails loud), and missing candidate / missing price
raise rather than recording a verdict with no anchor.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from vinci.ledger import LedgerError, log_verdict
from vinci.schemas.candidate import CandidateRecord, GateResult, TriageBand
from vinci.schemas.data_record import (
    CoverageTier,
    DataRecord,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
)
from vinci.schemas.envelope import DataField, SourceTier
from vinci.schemas.ledger import Confidence, Disposition, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.scoring.metrics import VerdictScore, spread_by_sector
from vinci.store import Store


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


def test_log_verdict_seals_proposal_and_disposition(tmp_path: Path) -> None:
    """(2026-07-13 pivot) The machine's SEALED proposal + the confirm/override disposition are
    stamped ONCE at log time, frozen into the entry, and survive the store round-trip. All three
    dispositions pinned; the HUMAN's verdict stays the verdict of record in every one."""
    with Store(tmp_path / "t.db") as store:
        # OVERRIDDEN — human BUY against a machine AVOID: the disagreement leg
        c1 = _seed(store, _ident("OVR", "SEC-0000000021-OVR", "0000000021"))
        e1 = log_verdict(store, candidate_id=c1, verdict=Verdict.BUY,
                         decided_at=datetime(2026, 7, 13, 10, 0),
                         machine_proposal=Verdict.AVOID_TERMINAL,
                         machine_lean="strongly-bearish",
                         proposal_assembled_at=datetime(2026, 7, 10, 6, 54), **_KW)
        assert e1.verdict is Verdict.BUY  # the human's verdict IS the verdict of record
        assert e1.disposition is Disposition.OVERRIDDEN
        stored = store.get_ledger_entry(e1.entry_id)
        assert stored is not None
        assert stored.machine_proposal is Verdict.AVOID_TERMINAL
        assert stored.machine_lean == "strongly-bearish"
        assert stored.proposal_assembled_at == datetime(2026, 7, 10, 6, 54)
        assert stored.disposition is Disposition.OVERRIDDEN
        # CONFIRMED — human and machine agree
        c2 = _seed(store, _ident("CNF", "SEC-0000000022-CNF", "0000000022"))
        e2 = log_verdict(store, candidate_id=c2, verdict=Verdict.AVOID_TERMINAL,
                         decided_at=datetime(2026, 7, 13, 10, 0),
                         machine_proposal=Verdict.AVOID_TERMINAL,
                         machine_lean="strongly-bearish", **_KW)
        assert e2.disposition is Disposition.CONFIRMED
        # NO_PROPOSAL — the machine abstained (mixed / no read); the human decided cold
        c3 = _seed(store, _ident("NOP", "SEC-0000000023-NOP", "0000000023"))
        e3 = log_verdict(store, candidate_id=c3, verdict=Verdict.BUY,
                         decided_at=datetime(2026, 7, 13, 10, 0),
                         machine_lean="mixed", **_KW)
        assert e3.machine_proposal is None and e3.disposition is Disposition.NO_PROPOSAL


def test_log_verdict_stamps_revealed_pre_verdict_anti_anchoring(tmp_path: Path) -> None:
    """(anti-anchoring, 2026-07-13) The brief HIDES the proposal so the human decides blind; the
    ledger records whether they peeked (dossier --show-proposal → log-verdict --saw-proposal) BEFORE
    logging. Default False == an uncontaminated human-vs-machine comparison; True flags an anchored
    disposition to down-weight. Frozen with the verdict, survives the store round-trip."""
    with Store(tmp_path / "t.db") as store:
        c1 = _seed(store, _ident("BLD", "SEC-0000000031-BLD", "0000000031"))
        e1 = log_verdict(store, candidate_id=c1, verdict=Verdict.AVOID_TERMINAL,
                         decided_at=datetime(2026, 7, 13, 10, 0),
                         machine_proposal=Verdict.AVOID_TERMINAL, machine_lean="strongly-bearish",
                         **_KW)
        assert e1.revealed_pre_verdict is False  # normal flow — decided blind
        c2 = _seed(store, _ident("PEK", "SEC-0000000032-PEK", "0000000032"))
        e2 = log_verdict(store, candidate_id=c2, verdict=Verdict.BUY,
                         decided_at=datetime(2026, 7, 13, 10, 0),
                         machine_proposal=Verdict.AVOID_TERMINAL, machine_lean="strongly-bearish",
                         revealed_pre_verdict=True, **_KW)
        assert e2.revealed_pre_verdict is True  # peeked — anchored, down-weight
        stored = store.get_ledger_entry(e2.entry_id)
        assert stored is not None and stored.revealed_pre_verdict is True  # frozen + round-trips


def test_ledger_disposition_coherence_negative_pins() -> None:
    """(pivot negative pins) A stored disposition that contradicts its (proposal, verdict) pair is
    REJECTED at construction — an incoherent record would silently corrupt all three spread
    curves — and a proposal without a stamped disposition is malformed."""
    base: dict[str, object] = dict(  # noqa: C408 — common entry kwargs
        entry_id="V-X", candidate_id="X", internal_id="SEC-X", ticker="X",
        verdict=Verdict.BUY, twin_call="t", entry_price=10.0,
        entry_price_as_of=date(2026, 7, 1), thesis="th", kill_criteria="k",
        horizon_days=90, confidence=Confidence.LOW, decided_at=datetime(2026, 7, 13, 10, 0),
    )
    with pytest.raises(ValidationError):  # claims confirmed, but proposal != verdict
        LedgerEntry(**base, machine_proposal=Verdict.AVOID_TERMINAL,  # type: ignore[arg-type]
                    disposition=Disposition.CONFIRMED)
    with pytest.raises(ValidationError):  # a proposal without a stamped disposition
        LedgerEntry(**base, machine_proposal=Verdict.BUY)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):  # claims no-proposal while a proposal is present
        LedgerEntry(**base, machine_proposal=Verdict.BUY,  # type: ignore[arg-type]
                    disposition=Disposition.NO_PROPOSAL)
    # and the coherent pairs construct fine (positive leg of the same pin)
    ok = LedgerEntry(**base, machine_proposal=Verdict.BUY,  # type: ignore[arg-type]
                     disposition=Disposition.CONFIRMED)
    assert ok.disposition is Disposition.CONFIRMED


def test_legacy_ledger_payload_loads_with_none_proposal() -> None:
    """A PRE-pivot payload (no proposal fields at all) still loads, all four fields None — the
    ledger's history is never invalidated by the pivot, and None-disposition == 'logged before
    the pivot existed' stays a readable state."""
    legacy = {
        "entry_id": "V-VRRM-screen2-20260501", "candidate_id": "VRRM-screen2-20260501",
        "internal_id": "SEC-0001682745-VRRM", "ticker": "VRRM", "verdict": "BUY",
        "twin_call": "t", "entry_price": 21.5, "entry_price_as_of": "2026-05-01",
        "thesis": "th", "kill_criteria": "k", "horizon_days": 180, "confidence": "medium",
        "decided_at": "2026-05-01T10:00:00",
    }
    e = LedgerEntry.model_validate_json(json.dumps(legacy))
    assert e.machine_proposal is None and e.machine_lean is None
    assert e.proposal_assembled_at is None and e.disposition is None


def test_underwrite_provenance_fields_are_additive() -> None:
    """``ratio_at_entry``/``underwrite_ref`` are additive: the pre-feature payload shape (VRRM)
    still loads with both None, and a row that carries them round-trips. The ledger's history is
    never invalidated by a new field."""
    legacy = {
        "entry_id": "V-X", "candidate_id": "X", "internal_id": "SEC-0000000001-X", "ticker": "X",
        "verdict": "BUY", "twin_call": "t", "entry_price": 21.5, "entry_price_as_of": "2026-05-01",
        "thesis": "th", "kill_criteria": "k", "horizon_days": 180, "confidence": "medium",
        "decided_at": "2026-05-01T10:00:00",
    }
    e = LedgerEntry.model_validate_json(json.dumps(legacy))
    assert e.ratio_at_entry is None and e.underwrite_ref is None
    withref = LedgerEntry.model_validate_json(
        json.dumps({**legacy, "ratio_at_entry": 6.69, "underwrite_ref": "scenarios/X.json"}))
    rt = LedgerEntry.model_validate_json(withref.model_dump_json())
    assert (rt.ratio_at_entry, rt.underwrite_ref) == (6.69, "scenarios/X.json")


def test_committed_ledger_is_coherent_and_append_only() -> None:
    """E2E on the COMMITTED ledger — the artifact the whole BUY−AVOID spread is measured from.

    Every row must re-validate as a ``LedgerEntry`` (so the disposition-coherence validator runs on
    real committed data), every entry price must be a real price, entry_ids must be unique, and the
    ORIGINAL row must still be present — the ledger is append-only, so a row that ever existed can
    never stop existing. A row whose payload disagrees with its own columns is corruption."""
    p = Path(__file__).resolve().parents[1] / "data" / "snapshots" / "decision_ledger.jsonl"
    rows = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    assert rows, "the committed ledger is empty — the spread has nothing to accumulate from"
    ids = [r["entry_id"] for r in rows]
    assert len(ids) == len(set(ids)), f"duplicate entry_id in the ledger: {ids}"
    assert "V-VRRM-screen2-20260617" in ids, "the first logged verdict vanished — NOT append-only"
    for r in rows:
        e = LedgerEntry.model_validate_json(r["payload"])   # runs disposition coherence
        assert e.entry_price > 0
        for col in ("entry_id", "candidate_id", "internal_id", "ticker"):
            assert r[col] == getattr(e, col), f"{r['entry_id']}: col {col} disagrees with payload"
        assert r["verdict"] == e.verdict.value and r["entry_price"] == e.entry_price


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
