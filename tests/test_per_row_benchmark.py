"""EACH ROW AGAINST ITS OWN BENCHMARK (2026-10-29) — STATE §5.0 row 39.

`score_ledger` applied ONE series to every row (IWM) and refused a resolved row that sealed
another. Two rows were exposed: GOOGL, sealed SPY, would have stopped scoring at its horizon
(2027-03-01); IT, sealed IWM but assigned MDY by its cap band, would have been scored against IWM
from 2027-01-16 while the monitor marked it against MDY. The operator ruled IT on 2026-10-29:
"Use MDY" — on its committed assignment, not on any return.

THE RULE (`scoring.harness.row_benchmark`): the committed assignment governs, as it does in the
monitor; a row with none is measured against the benchmark it sealed; a sealed benchmark and an
assignment that disagree are measured on the assignment only once the operator's ruling stands on
it, and are otherwise surfaced, never chosen between. A row's series must hold the calendar's
sessions at both ends. `run-monthly` ingests every benchmark a row needs.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.dividend_support import no_dividends, no_splits
from vinci.config import Config
from vinci.eod.client import RawBar
from vinci.monitor import BenchmarkAssignment, read_assignments_file
from vinci.schemas.data_record import Identity
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.scoring.harness import BenchmarkMismatchError, BenchmarkMissingError, row_benchmark
from vinci.store import Store
from vinci.universe import benchmark_identity

ROOT = Path(__file__).resolve().parents[1]
ENTRY, HORIZON = date(2026, 1, 5), date(2026, 3, 6)      # a Monday, a Friday: 60 days
AS_OF = date(2026, 3, 13)


def _weekdays(a: date, b: date) -> list[date]:
    return [date.fromordinal(o) for o in range(a.toordinal(), b.toordinal() + 1)
            if date.fromordinal(o).weekday() < 5]


def _bars(iid: str, first: float, last: float, *, until: date = AS_OF) -> list[PriceBar]:
    """A series that steps from ``first`` to ``last`` after the entry session."""
    return [PriceBar(internal_id=iid, bar_date=d, open=c, high=c, low=c, close=c, volume=1e6,
                     source="polygon-grouped")
            for d in _weekdays(ENTRY, until) for c in [first if d == ENTRY else last]]


def _row(ticker: str, benchmark: str | None, *, origin: str | None = None) -> LedgerEntry:
    return LedgerEntry(
        entry_id=f"V-{ticker}", candidate_id=f"{ticker}-c", internal_id=f"SEC-{ticker}",
        ticker=ticker, verdict=Verdict.BUY, twin_call="t", entry_price=100.0,
        entry_price_as_of=ENTRY, thesis="t", kill_criteria="k", horizon_days=60,
        confidence=Confidence.MEDIUM, decided_at=datetime(2026, 1, 5),
        **({"benchmark": benchmark} if benchmark else {}), **({"origin": origin} if origin else {}))


def _assignment(ticker: str, benchmark: str, *, ruled: bool, supersedes: str | None = None
                ) -> BenchmarkAssignment:
    return BenchmarkAssignment(
        ticker=ticker, entry_date=ENTRY, entry_price=100.0, shares=1e8, shares_source="t",
        cap_at_entry_usd=1e10, band="mid ($4–25B)", benchmark=benchmark, rationale="t",
        assigned_at=date(2026, 1, 6), supersedes=supersedes,
        ruled_on=date(2026, 10, 29) if ruled else None, ruling="Use MDY" if ruled else None)


def _store(tmp_path: Path, *, mdy_until: date = AS_OF) -> Store:
    """A flat name, a flat IWM, MDY +10% and SPY +20% after the entry session."""
    store = Store(tmp_path / "s.db")
    for t in ("NAME",):
        store.write_prices(_bars(f"SEC-{t}", 100.0, 100.0))
    store.write_prices(_bars("IDX-IWM", 50.0, 50.0))
    store.write_prices(_bars("IDX-MDY", 50.0, 55.0, until=mdy_until))
    store.write_prices(_bars("IDX-SPY", 50.0, 60.0))
    return store


def _score(store: Store, *rows: LedgerEntry, as_of: date = AS_OF,
           assignments: dict[str, BenchmarkAssignment] | None = None) -> Any:
    for r in rows:
        store.append_ledger(r)
    return score_ledger(store, as_of=as_of, dividends=no_dividends, splits=no_splits,
                        assignments=assignments)


def test_a_row_sealed_spy_is_measured_against_spy(tmp_path: Path) -> None:
    """GOOGL's shape. On main this raised `BenchmarkMismatchError` the moment the row resolved."""
    with _store(tmp_path) as store:
        (s,), _r = _score(store, _row("NAME", "SPY"))
    assert s.resolved and s.benchmark == "SPY"
    assert s.bench_return == pytest.approx(0.20) and s.excess_gross == pytest.approx(-0.20)


def test_a_ruled_assignment_governs_the_sealed_benchmark(tmp_path: Path) -> None:
    """IT's shape: sealed IWM, assigned MDY, ruled "Use MDY" — measured against MDY. On main every
    row was measured against IWM."""
    asg = {"NAME": _assignment("NAME", "MDY", ruled=True, supersedes="ledger row benchmark IWM")}
    with _store(tmp_path) as store:
        (s,), _r = _score(store, _row("NAME", "IWM"), assignments=asg)
        sealed = [e.benchmark for e in store.iter_ledger()]
    assert s.benchmark == "MDY" and s.bench_return == pytest.approx(0.10)
    assert sealed == ["IWM"]                       # the sealed field is read, never rewritten


def test_an_unruled_disagreement_is_surfaced_never_chosen(tmp_path: Path) -> None:
    asg = {"NAME": _assignment("NAME", "MDY", ruled=False)}
    (tmp_path / "r").mkdir()
    with _store(tmp_path / "r") as store, pytest.raises(BenchmarkMismatchError,
                                                        match="no operator ruling"):
        _score(store, _row("NAME", "IWM"), assignments=asg)
    (tmp_path / "u").mkdir()
    with _store(tmp_path / "u") as store:
        scores, report = _score(store, _row("NAME", "IWM"), assignments=asg,
                                as_of=date(2026, 2, 2))
    assert scores == [] and report.n_pending == 1
    assert any("no operator ruling" in n and "PENDING" in n for n in report.row_notes)


def test_a_row_benchmark_the_store_holds_only_in_part_is_not_measured(tmp_path: Path) -> None:
    """The primary's MDY ended 2026-08-05: a series that stops short would lend its last close as
    the exit. Refused at resolution, pending before it."""
    asg = {"NAME": _assignment("NAME", "MDY", ruled=True)}
    (tmp_path / "r").mkdir()
    with _store(tmp_path / "r", mdy_until=date(2026, 2, 20)) as store, pytest.raises(
            BenchmarkMissingError, match="has no bar on the session"):
        _score(store, _row("NAME", "IWM"), assignments=asg)
    (tmp_path / "u").mkdir()
    with _store(tmp_path / "u", mdy_until=date(2026, 1, 30)) as store:
        scores, report = _score(store, _row("NAME", "IWM"), assignments=asg,
                                as_of=date(2026, 2, 13))
    assert scores == [] and any("MDY" in n and "PENDING" in n for n in report.row_notes)


def test_rows_on_the_default_benchmark_score_as_before(tmp_path: Path) -> None:
    """THE NEGATIVE PIN: an assignment that agrees with the sealed IWM, and a row with no
    assignment (sealed at the schema's default, IWM), are measured against IWM alike."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    asg = {"NAME": _assignment("NAME", "IWM", ruled=False)}
    with _store(tmp_path / "a") as store:
        (with_asg,), _r = _score(store, _row("NAME", "IWM"), assignments=asg)
    with _store(tmp_path / "b") as store:
        (without,), _r = _score(store, _row("NAME", None))
    assert with_asg.benchmark == without.benchmark == "IWM"
    assert with_asg.bench_return == without.bench_return == 0.0
    assert with_asg.name_return == without.name_return


def test_the_committed_ledger_reads_its_committed_assignments_without_a_conflict() -> None:
    """CORPUS: every committed decision's benchmark — VRRM and SMPL IWM, IT MDY (ruled), GOOGL SPY
    (sealed and assigned alike) — and no disagreement left unruled."""
    asg = read_assignments_file(ROOT / "data" / "monitor" / "benchmark_assignments.json")
    rows = [LedgerEntry.model_validate(json.loads(json.loads(ln)["payload"]))
            for ln in (ROOT / "data/snapshots/decision_ledger.jsonl").read_text().splitlines()
            if ln.strip()]
    got = {e.entry_id: row_benchmark(e, asg.get(e.ticker), "IWM")
           for e in rows if e.event is None}
    assert got == {
        "V-VRRM-screen2-20260617": ("IWM", None), "V-IT-screen2-20260706": ("MDY", None),
        "V-SMPL-screen2-20260706": ("IWM", None), "V-SMPL-screen2-20260729": ("IWM", None),
        "V-GOOGL": ("SPY", None)}
    assert asg["IT"].ruled_on == date(2026, 10, 29) and asg["IT"].ruling == "Use MDY"


def test_a_ruling_carries_its_date_and_its_words() -> None:
    base = _assignment("NAME", "MDY", ruled=False).model_dump()
    for half in ({"ruled_on": "2026-10-29"}, {"ruling": "Use MDY"}):
        with pytest.raises(ValueError, match="AND its words"):
            BenchmarkAssignment.model_validate({**base, **half})


# --- run-monthly: every row's benchmark ingested, every row measured against its own -----------


class _Feed:
    """Polygon as `run_monthly` reads it: grouped-daily days for the two names and three ETFs."""

    px = {"NAME": (100.0, 100.0), "GOOG": (100.0, 100.0), "IWM": (50.0, 50.0),
          "MDY": (50.0, 55.0), "SPY": (50.0, 60.0)}

    @classmethod
    def from_config(cls, _cfg: object) -> _Feed:
        return cls()

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        if day.weekday() >= 5 or not ENTRY <= day <= AS_OF:
            return {}
        return {s: RawBar(ticker=s, open=c, high=c, low=c, close=c, volume=1e6)
                for s, (a, b) in self.px.items() for c in [a if day == ENTRY else b]}

    def splits_reference(self, _symbol: str) -> list[dict[str, Any]]:
        return []


def _ident(t: str) -> Identity:
    return Identity(internal_id=f"SEC-{t}", issuer_id=f"ISS-{t}", cik="0000000009", ticker=t,
                    mic="XNAS", exchange="Nasdaq", eod_symbol=t, name=t)


def test_run_monthly_ingests_every_rows_benchmark_and_measures_each_against_its_own(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """End to end through the real `run_monthly`: a screen BUY sealed IWM and assigned MDY with a
    ruling, and a followed BUY sealed SPY. On main the run ingested IWM alone and measured both
    against it — the screen BUY's excess read 0.0 where it is −10% against MDY."""
    from vinci import orchestrator
    cfg = Config(data_dir=tmp_path / "data")
    cfg.ensure_dirs()
    with Store(cfg.db_path) as store:
        for t in ("NAME", "GOOG"):
            store.upsert_security(_ident(t))
        store.append_ledger(_row("NAME", "IWM"))
        store.append_ledger(_row("GOOG", "SPY", origin="followed"))
        store.export_snapshots(cfg.snapshots_dir)
    (cfg.data_dir / "monitor").mkdir()
    (cfg.data_dir / "monitor" / "benchmark_assignments.json").write_text(json.dumps(
        {"NAME": json.loads(_assignment("NAME", "MDY", ruled=True).model_dump_json())}))
    monkeypatch.setattr(orchestrator, "PolygonEodClient", _Feed)
    monkeypatch.setattr(orchestrator, "default_dividends", lambda **_kw: no_dividends)
    monkeypatch.setattr(orchestrator, "default_splits", lambda *_a, **_k: no_splits)
    report = orchestrator.run_monthly(cfg, as_of=AS_OF)
    with Store(cfg.db_path) as store:
        held = {b: len(store.get_price_history(benchmark_identity(b).internal_id))
                for b in ("IWM", "MDY", "SPY")}
    assert all(n == len(_weekdays(ENTRY, AS_OF)) for n in held.values()), held
    assert report["n_resolved_buy"] == 1                     # the screen book's one BUY
    assert report["buy_excess_gross"] == pytest.approx(-0.10)  # against MDY, not IWM


def test_both_production_callers_supply_the_assignments() -> None:
    """`vinci score` and `run_monthly` pass `assignments=` — without it every assigned row falls
    back to its sealed benchmark, IT to the IWM the operator ruled away from."""
    import inspect

    from vinci import cli, orchestrator
    assert "assignments=mon_assignments(" in inspect.getsource(cli._cmd_score)
    assert "assignments=assignments," in inspect.getsource(orchestrator.run_monthly)
