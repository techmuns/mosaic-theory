"""Step 2 verification — the SQLite store.

Covers: schema init; entity/universe/candidate/ledger round-trips; the **coverage default**
(an absent price reads back UNKNOWN, never a silent 0); price staleness; append-only ledger;
and the durable **snapshot → rebuild** round-trip (with bulk prices intentionally NOT snapshotted).
"""

from __future__ import annotations

import json
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


# --- the ledger is append-only IN THE ENGINE (triggers, 2026-10-26) ---------------------------
_APPEND_ONLY = "decision_ledger is append-only"
_TRIGGERS = {"decision_ledger_no_update", "decision_ledger_no_delete", "decision_ledger_no_rewrite"}


def _ledger_rows(s: Store) -> list[dict[str, object]]:
    return [dict(r) for r in s._conn.execute(                              # noqa: SLF001
        "SELECT * FROM decision_ledger ORDER BY entry_id")]


def test_the_engine_refuses_every_rewrite_of_a_logged_verdict(store: Store) -> None:
    """NEGATIVE PIN. Until now `decision_ledger` was append-only only because no caller happened to
    issue an UPDATE or a DELETE. Each SQL shape that can change a logged row is refused now:
    UPDATE, DELETE, an UPSERT (whose DO UPDATE fires the update trigger), and `INSERT OR REPLACE`
    with a different row under the same entry_id. The last one matters most. REPLACE deletes the
    conflicting row WITHOUT firing delete triggers (recursive_triggers is off), so with only the
    two theme-intelligence-style triggers it rewrites a verdict silently, and it is the very
    statement `rebuild_from_snapshots` runs."""
    store.append_ledger(_ledger_entry(_identity()))
    before = _ledger_rows(store)
    conn = store._conn                                                     # noqa: SLF001
    rewrites = [
        ("UPDATE decision_ledger SET verdict = 'AVOID_TERMINAL' WHERE entry_id = 'led-0001'", ()),
        ("DELETE FROM decision_ledger WHERE entry_id = 'led-0001'", ()),
        ("DELETE FROM decision_ledger", ()),
        ("INSERT INTO decision_ledger SELECT * FROM decision_ledger WHERE entry_id = 'led-0001' "
         "ON CONFLICT(entry_id) DO UPDATE SET entry_price = 1.0", ()),
        ("INSERT OR REPLACE INTO decision_ledger (entry_id, candidate_id, internal_id, ticker, "
         "verdict, entry_price, entry_price_as_of, horizon_days, decided_at, payload) "
         "SELECT entry_id, candidate_id, internal_id, ticker, verdict, ?, entry_price_as_of, "
         "horizon_days, decided_at, payload FROM decision_ledger", (1.0,)),
    ]
    for sql, params in rewrites:
        with pytest.raises(sqlite3.IntegrityError, match=_APPEND_ONLY):
            conn.execute(sql, params)
    assert _ledger_rows(store) == before, "a refused rewrite must leave the logged row untouched"


def test_the_legitimate_writes_still_land(store: Store, tmp_path: Path) -> None:
    """POSITIVE PIN — the triggers must not break a write the fund relies on. A new entry appends;
    re-seeding a DB that already holds the identical rows (what the weekly screen and the monthly
    score do on every run, via `rebuild_from_snapshots`) is a no-op, not an error; and a re-seed
    that brings a NEW entry_id appends it."""
    ident = _identity()
    store.append_ledger(_ledger_entry(ident))
    second = _ledger_entry(ident).model_copy(update={"entry_id": "led-0002"})
    store.append_ledger(second)
    snaps = tmp_path / "snaps"
    store.export_snapshots(snaps, tables=["decision_ledger"])
    before = _ledger_rows(store)
    assert store.rebuild_from_snapshots(snaps, tables=["decision_ledger"]) == {
        "decision_ledger": 2}
    assert _ledger_rows(store) == before
    with Store(tmp_path / "other.db") as other:               # a DB holding only the first row
        other.append_ledger(_ledger_entry(ident))
        other.rebuild_from_snapshots(snaps, tables=["decision_ledger"])
        assert _ledger_rows(other) == before


def test_an_existing_working_db_gains_the_triggers_when_opened(tmp_path: Path) -> None:
    """THE MIGRATION. Every operator DB predates the triggers; `init_schema` runs on each open and
    the DDL says `IF NOT EXISTS`, so opening one installs them with its rows intact. Simulated by
    dropping them from a DB that already holds a verdict — the shape of every DB built before
    2026-10-26 (the two real working DBs holding the 7-row ledger carried no trigger at all)."""
    db = tmp_path / "old.db"
    with Store(db) as s:
        s.append_ledger(_ledger_entry(_identity()))
        for t in _TRIGGERS:
            s._conn.execute(f"DROP TRIGGER {t}")                           # noqa: SLF001
        s._conn.commit()                                                   # noqa: SLF001
        before = _ledger_rows(s)
    with Store(db) as s:
        names = {r[0] for r in s._conn.execute(                            # noqa: SLF001
            "SELECT name FROM sqlite_master WHERE type = 'trigger'")}
        assert names >= _TRIGGERS
        assert _ledger_rows(s) == before
        with pytest.raises(sqlite3.IntegrityError, match=_APPEND_ONLY):
            s._conn.execute("DELETE FROM decision_ledger")                 # noqa: SLF001
    with Store(db) as s:     # every LATER open meets the triggers already there — and must not fail
        assert _ledger_rows(s) == before


def test_the_committed_ledger_cannot_be_rewritten_once_loaded(tmp_path: Path) -> None:
    """CORPUS, NOT A FIXTURE. Loads the LIVE committed `decision_ledger.jsonl` the way the weekly
    screen and the monthly score do, then tries to change every real row three ways. Each is
    refused, a second identical load is a no-op, and every row still equals its committed line."""
    committed = Path(__file__).resolve().parents[1] / "data" / "snapshots" / "decision_ledger.jsonl"
    lines = [json.loads(ln) for ln in committed.read_text().splitlines() if ln.strip()]
    assert len(lines) >= 7, f"the committed ledger read {len(lines)} rows — it only grows"
    snaps = tmp_path / "snaps"
    snaps.mkdir()
    (snaps / "decision_ledger.jsonl").write_text(committed.read_text())
    with Store(tmp_path / "w.db") as s:
        s.rebuild_from_snapshots(snaps, tables=["decision_ledger"])
        conn = s._conn                                                     # noqa: SLF001
        for row in lines:
            eid = row["entry_id"]
            for sql, params in (
                ("UPDATE decision_ledger SET payload = '{}' WHERE entry_id = ?", (eid,)),
                ("DELETE FROM decision_ledger WHERE entry_id = ?", (eid,)),
                ("INSERT OR REPLACE INTO decision_ledger (entry_id, candidate_id, internal_id, "
                 "ticker, verdict, entry_price, entry_price_as_of, horizon_days, decided_at, "
                 "payload) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (eid, row["candidate_id"], row["internal_id"], row["ticker"], row["verdict"],
                  row["entry_price"] * 2, row["entry_price_as_of"], row["horizon_days"],
                  row["decided_at"], row["payload"])),
            ):
                with pytest.raises(sqlite3.IntegrityError, match=_APPEND_ONLY):
                    conn.execute(sql, params)
        s.rebuild_from_snapshots(snaps, tables=["decision_ledger"])      # identical re-seed
        assert _ledger_rows(s) == sorted(lines, key=lambda r: r["entry_id"])
        assert len(list(s.iter_ledger())) == len(lines)


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


# --- ledger-export guard (the 2026-07-13 near-miss) -------------------------------------------
def test_export_snapshots_refuses_to_shrink_ledger(store: Store, tmp_path: Path) -> None:
    """The #121 near-miss, mechanized: a committed 1-entry decision_ledger.jsonl on disk + an EMPTY
    working-DB ledger. A full export would write 0 rows over 1 — a ledger DELETE — so it RAISES and
    leaves the committed file untouched (the guard fires BEFORE the write). E2e: guard wired in."""
    snaps = tmp_path / "snaps"
    snaps.mkdir()
    (snaps / "decision_ledger.jsonl").write_text(json.dumps({"entry_id": "led-0001"}) + "\n")
    with pytest.raises(RuntimeError, match="ROW-DROP"):
        store.export_snapshots(snaps)  # 0 DB rows over 1 committed → ledger DELETE → refused
    assert "led-0001" in (snaps / "decision_ledger.jsonl").read_text()  # never overwritten


def test_export_snapshots_refuses_to_shrink_securities(store: Store, tmp_path: Path) -> None:
    """The guard also protects the securities/issuers ENTITY MASTER (accumulate-only): a build on a
    stale DB that would drop committed identities RAISES — the #121 lossy-backup mechanism."""
    snaps = tmp_path / "snaps"
    snaps.mkdir()
    rows = [json.dumps({"internal_id": i}) for i in ("SEC-1-A", "SEC-2-B")]
    (snaps / "securities.jsonl").write_text("\n".join(rows) + "\n")
    with pytest.raises(RuntimeError, match="ROW-DROP"):
        store.export_snapshots(snaps)  # 0 DB securities over 2 committed → refused
    assert "SEC-2-B" in (snaps / "securities.jsonl").read_text()  # entity master untouched


def test_ledger_guard_raises_on_missing_row(tmp_path: Path) -> None:
    """Same row COUNT but an existing entry dropped (b gone, c added) still violates — the guard
    compares by primary key, not just length."""
    from vinci.store.store import _assert_no_row_drop

    p = tmp_path / "decision_ledger.jsonl"
    p.write_text(json.dumps({"entry_id": "a"}) + "\n" + json.dumps({"entry_id": "b"}) + "\n")
    new = [json.dumps({"entry_id": "a"}), json.dumps({"entry_id": "c"})]  # b dropped
    with pytest.raises(RuntimeError, match="ROW-DROP"):
        _assert_no_row_drop(p, new, ["entry_id"])


def test_ledger_guard_passes_on_pure_append(tmp_path: Path) -> None:
    """A pure append (superset of the existing rows) is allowed — returns without raising."""
    from vinci.store.store import _assert_no_row_drop

    p = tmp_path / "decision_ledger.jsonl"
    p.write_text(json.dumps({"entry_id": "a"}) + "\n" + json.dumps({"entry_id": "b"}) + "\n")
    superset = [json.dumps({"entry_id": e}) for e in ("a", "b", "c")]
    _assert_no_row_drop(p, superset, ["entry_id"])  # {a,b} ⊆ {a,b,c} → no raise


def test_selective_export_writes_only_build_universe_tables(store: Store, tmp_path: Path) -> None:
    """build_universe's selective export writes ONLY issuers/securities/universe_snapshot — never
    candidate_records or decision_ledger — so a stale-DB build can't rewrite the ledger."""
    from vinci.universe import BUILD_UNIVERSE_TABLES

    snaps = tmp_path / "snaps"
    store.export_snapshots(snaps, tables=BUILD_UNIVERSE_TABLES)
    written = {p.name for p in snaps.glob("*.jsonl")}
    assert written == {f"{t}.jsonl" for t in BUILD_UNIVERSE_TABLES}
    assert "decision_ledger.jsonl" not in written and "candidate_records.jsonl" not in written


# --- the entity master accumulates FACTS, not just rows (#464 regression, found 2026-08-31) -----
def test_an_unenriched_upsert_never_nulls_a_known_sic(store: Store) -> None:
    """THE REAL FAILURE SHAPE, replayed on the real name it hit. `vinci refresh IT NFLX` resolves
    WITHOUT `enrich=True`, so it upserted Gartner carrying `sic=None` and `INSERT OR REPLACE`
    rewrote 8741 to NULL in the committed entity master. The row survived — the no-row-drop guard
    counts PKs, not fields — so nothing raised, and the monitor read the destroyed fact as a
    resolved sector of "Unknown" for two weeks.

    IT is the exposed class: ledgered but OUT of the cap band, so no later `build_universe` ever
    came back to rewrite its SIC.
    """
    enriched = _identity("SEC-0000749251-IT").model_copy(update={
        "issuer_id": "ISS-0000749251", "cik": "0000749251", "ticker": "IT", "eod_symbol": "IT",
        "name": "GARTNER INC", "sic": "8741", "sic_description": "Services-Management Services"})
    store.upsert_security(enriched, first_seen=AS_OF)
    assert store.get_security("SEC-0000749251-IT").sic == "8741"

    # the `refresh` path: same identity, no SIC fetched
    store.upsert_security(enriched.model_copy(update={"sic": None, "sic_description": None}))
    got = store.get_security("SEC-0000749251-IT")
    assert got is not None and got.sic == "8741", (
        "a writer that does not KNOW the SIC must leave the known one standing")
    issuer = store._conn.execute(                                        # noqa: SLF001 — the
        "SELECT sic, sic_description FROM issuers WHERE cik='0000749251'").fetchone()
    assert (issuer["sic"], issuer["sic_description"]) == (
        "8741", "Services-Management Services"), "the issuer row is preserved alongside"


def test_the_issuer_row_lands_column_for_column(store: Store) -> None:
    """THE ISSUERS INSERT HAS NO OTHER READER. `_row_to_identity` reads the SECURITIES table only,
    so `test_security_round_trip`'s `got == ident` cannot cover the issuer side — and the issuers
    VALUES clause is now three interleaved COALESCE sub-selects over ten positional parameters,
    which is exactly the shape where a future edit transposes two same-typed columns (`name` and
    `country` are adjacent in the tuple and both plain strings) and nothing notices until the
    corruption reaches the committed `issuers.jsonl` on the next export."""
    ident = _identity().model_copy(update={
        "name": "Apple Inc.", "sic": "3571", "sic_description": "Electronic Computers"})
    store.upsert_security(ident, first_seen=AS_OF)
    row = dict(store._conn.execute(                                      # noqa: SLF001
        "SELECT * FROM issuers WHERE cik = ?", (ident.cik,)).fetchone())
    assert row == {
        "cik": "0000320193", "issuer_id": "ISS-0000320193", "name": "Apple Inc.",
        "sic": "3571", "sic_description": "Electronic Computers", "country": "US",
        "first_seen": AS_OF.isoformat(),
    }


def test_a_real_sic_change_still_overwrites_and_a_new_row_still_writes_none(store: Store) -> None:
    """THE NEGATIVE PIN. Preserving must not become freezing: a genuine RE-CLASSIFICATION (a
    non-NULL value) still overwrites, and a name whose SIC was never known still stores NULL —
    otherwise `sector_for_display` could never report an absence at all."""
    ident = _identity()
    store.upsert_security(ident.model_copy(update={"sic": "3571"}), first_seen=AS_OF)
    store.upsert_security(ident.model_copy(update={"sic": "7372"}))     # EDGAR re-classified it
    assert store.get_security(ident.internal_id).sic == "7372"

    fresh = _identity("SEC-0001065280-NFLX").model_copy(update={
        "issuer_id": "ISS-0001065280", "cik": "0001065280", "ticker": "NFLX",
        "eod_symbol": "NFLX", "name": "NETFLIX INC", "sic": None, "sic_description": None})
    store.upsert_security(fresh, first_seen=AS_OF)
    assert store.get_security("SEC-0001065280-NFLX").sic is None, (
        "a never-known SIC stays NULL — COALESCE preserves, it does not fabricate")
