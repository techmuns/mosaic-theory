"""A DECISION SEALED ON A STALE CLOSE IS CORRECTED BY AN APPENDED ROW, READ BY SCORING AND THE
MONITOR (TeamNostra fix request 2, RF-D7; operator ruling 2026-11-09: "yes to all").

THE DEFECT, on the committed ledger: GOOGL's BUY was decided 2026-08-28 and sealed the 2026-08-14
close; VRRM's AVOID was decided 2026-06-21 and sealed 06-17 while 06-18 had closed. Each row's
forward clock started at its sealed close. The ledger is append-only, so neither row may change.

THE FIX: ONE RULE FOR EVERY ROW (`vinci.ledger.correction.rule_session`) — the last US close
completed at the decision moment — and a CORRECTION row (`EVENT_CORRECTION`) carrying it, which
scoring and the monitor read the decision at (`schemas.ledger.corrected`). The rule is pinned on
all five committed decisions with Polygon's real bars (`tests/fixtures/prices/`): GOOGL and VRRM
move, IT and both SMPL decisions do not.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.dividend_support import no_dividends, no_splits
from vinci.config import Config
from vinci.ledger.correction import correct_entry, decision_moment, rule_session
from vinci.ledger.workflow import LedgerError
from vinci.schemas.ledger import (
    EVENT_CORRECTION,
    LedgerEntry,
    LedgerFact,
    corrected,
    corrections_by_decision,
    origin_of,
    sleeve_of,
)
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"


def _committed_lines() -> list[str]:
    """The committed ledger's lines AS SEALED: its CORRECTION rows left out. These tests write the
    corrections themselves, so they hold before the two are appended to the committed ledger and
    after; the rows they read are append-only and never change."""
    return [ln for ln in LEDGER.read_text().splitlines() if ln.strip()
            and json.loads(json.loads(ln)["payload"]).get("event") != EVENT_CORRECTION]


def _committed() -> list[LedgerEntry]:
    return [LedgerEntry.model_validate(json.loads(json.loads(ln)["payload"]))
            for ln in _committed_lines()]


def _bars(ticker: str) -> list[dict[str, Any]]:
    return [json.loads(ln) for ln in (ROOT / "tests/fixtures/prices" / f"{ticker}.jsonl")
            .read_text().splitlines() if ln.strip()]


# --- the rule, on every committed decision --------------------------------------------------------


_EXPECTED = {   # decision → (the rule's session, its Polygon close)
    "V-GOOGL": (date(2026, 8, 27), 340.65),
    "V-VRRM-screen2-20260617": (date(2026, 6, 18), 4.44),
    "V-IT-screen2-20260706": (date(2026, 7, 20), 141.06),
    "V-SMPL-screen2-20260706": (date(2026, 7, 20), 10.92),
    "V-SMPL-screen2-20260729": (date(2026, 8, 4), 11.33),
}


@pytest.mark.parametrize("entry_id", sorted(_EXPECTED))
def test_the_rule_on_every_committed_decision(entry_id: str) -> None:
    """THE CORPUS. GOOGL (9 sessions stale) and VRRM (1: the 06-18 close existed, 06-19 a holiday)
    move; IT and both SMPL decisions read their sealed close. Sessions and closes are Polygon's
    own bars, committed."""
    d = next(e for e in _committed() if e.entry_id == entry_id)
    closes = {date.fromisoformat(b["bar_date"]): float(b["close"]) for b in _bars(d.ticker)}
    session = rule_session(d.decided_at, list(closes))
    assert (session, closes[session]) == _EXPECTED[entry_id]
    assert closes[d.entry_price_as_of] == d.entry_price          # the seal read the same bars
    moved = session != d.entry_price_as_of
    assert moved == (entry_id in ("V-GOOGL", "V-VRRM-screen2-20260617"))


def test_how_a_decision_time_is_read() -> None:
    """IST, set against the 16:00 ET close; a date-only stamp is read at the end of its IST day."""
    # GOOGL: 2026-08-28 11:24 IST is 01:54 ET — before that day's open
    googl = decision_moment(datetime(2026, 8, 28, 11, 24, 47))
    assert googl.strftime("%m-%d %H:%M") == "08-28 01:54"
    # a date-only 2026-07-21 reads 23:59:59 IST = 14:29 ET, before 07-21's close
    assert decision_moment(datetime(2026, 7, 21)).strftime("%m-%d %H:%M") == "07-21 14:29"
    # a decision made after a session's close uses that close
    sessions = [date(2026, 10, 1), date(2026, 10, 2)]
    assert rule_session(datetime(2026, 10, 3, 5, 0), sessions) == date(2026, 10, 2)  # 19:30 ET
    assert rule_session(datetime(2026, 10, 2, 22, 0), sessions) == date(2026, 10, 1)  # 12:30 ET
    assert rule_session(datetime(2026, 9, 30, 12, 0), sessions) is None


# --- the row -------------------------------------------------------------------------------------


def _store(tmp_path: Path) -> Store:
    store = Store(tmp_path / "l.db")
    for e in _committed():
        store.append_ledger(e)
    return store


def test_a_correction_is_appended_and_the_decision_row_is_untouched(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        row = correct_entry(store, entry_id="V-GOOGL", entry_price=340.65,
                            entry_price_as_of=date(2026, 8, 27), reason="RF-D7: the rule's close",
                            corrected_at=datetime(2026, 11, 10, 12))
        assert (row.entry_id, row.event, row.corrects_entry_id) == (
            "R-GOOGL", EVENT_CORRECTION, "V-GOOGL")
        rows = list(store.iter_ledger())
        googl = next(e for e in rows if e.entry_id == "V-GOOGL")
        assert (googl.entry_price, googl.entry_price_as_of) == (345.9, date(2026, 8, 14))
        read = corrected(googl, corrections_by_decision(rows)["V-GOOGL"])
        assert (read.entry_price, read.entry_price_as_of) == (340.65, date(2026, 8, 27))


@pytest.mark.parametrize("kw, expect", [
    ({"entry_id": "V-NOPE"}, "no decision row"),
    ({"entry_id": "C-IT-screen2-20260706"}, "no decision row"),
    ({"entry_price": 345.9, "entry_price_as_of": date(2026, 8, 14)}, "nothing to correct"),
    ({"entry_price_as_of": date(2026, 8, 31)}, "could not have been made at"),
    ({"reason": "  "}, "no reason"),
])
def test_a_correction_that_does_not_belong_is_refused(tmp_path: Path, kw: dict[str, Any],
                                                     expect: str) -> None:
    base: dict[str, Any] = {"entry_id": "V-GOOGL", "entry_price": 340.65,
                            "entry_price_as_of": date(2026, 8, 27), "reason": "RF-D7",
                            "corrected_at": datetime(2026, 11, 10, 12)}
    with _store(tmp_path) as store:
        n = len(list(store.iter_ledger()))
        with pytest.raises(LedgerError, match=expect):
            correct_entry(store, **{**base, **kw})
        assert len(list(store.iter_ledger())) == n


def test_a_second_correction_is_refused(tmp_path: Path) -> None:
    with _store(tmp_path) as store:
        correct_entry(store, entry_id="V-GOOGL", entry_price=340.65,
                      entry_price_as_of=date(2026, 8, 27), reason="RF-D7",
                      corrected_at=datetime(2026, 11, 10, 12))
        with pytest.raises(LedgerError, match="already corrected"):
            correct_entry(store, entry_id="V-GOOGL", entry_price=340.0,
                          entry_price_as_of=date(2026, 8, 26), reason="again",
                          corrected_at=datetime(2026, 11, 10, 13))


# --- scoring reads it ----------------------------------------------------------------------------
# VRRM's real row and its real bars (`tests/fixtures/horizon_close/vrrm_iwm_bars.jsonl`, frozen at
# #820: VRRM and IWM, 2026-06-15 → 2026-10-16). Where a horizon must land inside that window it is
# shortened ON A COPY, as `test_scoring_horizon_close` does; the committed ledger is never written.

_HC = ROOT / "tests/fixtures/horizon_close/vrrm_iwm_bars.jsonl"
_VRRM = "V-VRRM-screen2-20260617"


def _hc_close(iid: str, on: date) -> float:
    return next(float(r["close"]) for r in map(json.loads, _HC.read_text().splitlines())
                if r["internal_id"] == iid and r["bar_date"] == on.isoformat())


def _vrrm_score(tmp_path: Path, *, as_of: date, correct: bool,
                horizon_days: int | None = None) -> tuple[Any, Any]:
    (row,) = [e for e in _committed() if e.entry_id == _VRRM]
    if horizon_days is not None:
        row = row.model_copy(update={"horizon_days": horizon_days})
    tmp_path.mkdir(parents=True, exist_ok=True)
    with Store(tmp_path / "s.db") as store:
        store.write_prices([PriceBar.model_validate(json.loads(ln))
                            for ln in _HC.read_text().splitlines()])
        store.append_ledger(row)
        if correct:
            correct_entry(store, entry_id=_VRRM, entry_price=4.44,
                          entry_price_as_of=date(2026, 6, 18), reason="RF-D7: the rule's close",
                          corrected_at=datetime(2026, 11, 10, 12))
        scores, report = score_ledger(store, as_of=as_of, dividends=no_dividends,
                                      splits=no_splits)
    (score,) = scores           # the correction row is not a decision, so it is never scored
    return score, report


def test_scoring_reads_the_decision_at_its_correction(tmp_path: Path) -> None:
    """VRRM's AVOID, corrected to the 4.44 close of 2026-06-18, divides by 4.44; uncorrected (the
    negative pin) it divides by 4.71. The row and the report both name the two entries."""
    on = date(2026, 10, 14)
    now = _hc_close("SEC-0001682745-VRRM", on)
    before, _ = _vrrm_score(tmp_path / "a", as_of=on, correct=False)
    after, report = _vrrm_score(tmp_path / "b", as_of=on, correct=True)
    assert before.name_price_return == pytest.approx(now / 4.71 - 1)
    assert after.name_price_return == pytest.approx(now / 4.44 - 1)
    assert after.entry_id == _VRRM
    for note in (after.note or "", " ".join(report.row_notes)):
        assert "ENTRY CORRECTED by R-VRRM-screen2-20260617" in note
        assert "sealed 4.71 on 2026-06-17" in note and "4.44 on 2026-06-18" in note
    assert "ENTRY CORRECTED" not in (before.note or "")


def test_the_corrected_horizon_runs_from_the_corrected_date(tmp_path: Path) -> None:
    """A 120-day horizon from 06-17 is 10-15; from 06-18, 10-16. On 10-15 the sealed row resolves
    and the corrected one does not; on 10-16 the corrected one resolves at 10-16's close. (So VRRM's
    real 180-day row resolves on 2026-12-15's close once corrected, not 12-14's — STATE row 38.)"""
    sealed, _ = _vrrm_score(tmp_path / "a", as_of=date(2026, 10, 15), correct=False,
                            horizon_days=120)
    early, _ = _vrrm_score(tmp_path / "b", as_of=date(2026, 10, 15), correct=True,
                           horizon_days=120)
    late, _ = _vrrm_score(tmp_path / "c", as_of=date(2026, 10, 16), correct=True,
                          horizon_days=120)
    assert (sealed.resolved, early.resolved, late.resolved) == (True, False, True)
    assert late.name_price_return == pytest.approx(
        _hc_close("SEC-0001682745-VRRM", date(2026, 10, 16)) / 4.44 - 1)
    assert date(2026, 6, 18) + timedelta(days=180) == date(2026, 12, 15)


# --- the monitor reads it -------------------------------------------------------------------------


def test_the_monitor_marks_the_decision_at_its_correction(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """END TO END: `vinci monitor --out` over VRRM's committed line, its real bars, and a correction
    row appended to a COPY of the ledger — the mark divides by 4.44 from 06-18, the correction row
    is not marked as a position, and the day names both entries. The committed ledger is never
    written."""
    from vinci import cli
    (tmp_path / "s").mkdir()
    with Store(tmp_path / "s" / "l.db") as store:
        store.append_ledger(next(e for e in _committed() if e.entry_id == _VRRM))
        fix = correct_entry(store, entry_id=_VRRM, entry_price=4.44,
                            entry_price_as_of=date(2026, 6, 18), reason="RF-D7",
                            corrected_at=datetime(2026, 11, 10, 12))
    book = tmp_path / "book"
    (book / "data/snapshots").mkdir(parents=True)
    (book / "data/monitor").mkdir(parents=True)
    (book / "scenarios").mkdir()
    vrrm = [ln for ln in _committed_lines() if json.loads(ln)["entry_id"] == _VRRM]
    line = {"entry_id": fix.entry_id, "ticker": fix.ticker, "verdict": fix.verdict.value,
            "entry_price": fix.entry_price, "entry_price_as_of": fix.entry_price_as_of.isoformat(),
            "horizon_days": fix.horizon_days, "payload": fix.model_dump_json()}
    (book / "data/snapshots/decision_ledger.jsonl").write_text(
        "\n".join([*vrrm, json.dumps(line)]) + "\n")
    for rel in ("data/snapshots/securities.jsonl", "data/monitor/benchmark_assignments.json"):
        shutil.copy(ROOT / rel, book / rel)
    sym = {"SEC-0001682745-VRRM": "VRRM", "IDX-IWM": "IWM"}
    days: dict[date, dict[str, Any]] = {}
    for r in map(json.loads, _HC.read_text().splitlines()):
        days.setdefault(date.fromisoformat(r["bar_date"]), {})[sym[r["internal_id"]]] = (
            SimpleNamespace(close=float(r["close"])))

    class _Eod:
        @classmethod
        def from_config(cls, _cfg: object) -> _Eod:
            return cls()

        def grouped_daily(self, d: date) -> dict[str, Any]:
            return dict(days.get(d, {}))

    class _Edgar:
        @classmethod
        def from_config(cls, _cfg: object) -> _Edgar:
            return cls()

        def recent_filings(self, *_a: object, **_k: object) -> list[object]:
            return []
    monkeypatch.chdir(book)
    monkeypatch.setattr(cli, "PolygonEodClient", _Eod)
    monkeypatch.setattr(cli, "EdgarClient", _Edgar)
    monkeypatch.setattr(cli, "default_dividends", lambda **_kw: no_dividends)
    monkeypatch.setattr(cli, "default_splits", lambda *_a, **_k: no_splits)
    assert cli._cmd_monitor(argparse.Namespace(ref="2026-10-16", out=str(tmp_path / "out"))) == 0
    (day,) = [json.loads(p.read_text()) for p in (tmp_path / "out/data/monitor").glob("*.json")]
    (mark,) = day["rows"]
    assert (mark["entry_price"], mark["entry_date"]) == (4.44, "2026-06-18")
    assert mark["days_elapsed"] == 120
    assert mark["position_return"] == pytest.approx(
        _hc_close("SEC-0001682745-VRRM", date(2026, 10, 16)) / 4.44 - 1)
    assert any("ENTRY CORRECTED" in n and "sealed 4.71 on 2026-06-17" in n for n in day["notes"])


# --- the command ---------------------------------------------------------------------------------


@pytest.fixture
def tree(tmp_path: Path) -> Config:
    data = tmp_path / "data"
    data.mkdir()
    shutil.copytree(ROOT / "data" / "snapshots", data / "snapshots")
    (data / "snapshots" / "decision_ledger.jsonl").write_text("\n".join(_committed_lines()) + "\n")
    cfg = Config(data_dir=data)
    cfg.ensure_dirs()
    return cfg


def _run(tree: Config, monkeypatch: pytest.MonkeyPatch, entry_id: str, *, dry: bool) -> int:
    """The real command on a COPY of the committed tree; Polygon's daily bars are the committed
    fixtures (real aggregates), served by ticker."""
    from vinci import cli

    class _Eod:
        @classmethod
        def from_config(cls, _cfg: object) -> _Eod:
            return cls()

        def daily_bars(self, symbol: str, a: date, b: date) -> list[tuple[date, Any]]:
            return [(d, SimpleNamespace(close=float(r["close"]))) for r in _bars(symbol)
                    if a <= (d := date.fromisoformat(r["bar_date"])) <= b]
    monkeypatch.setattr(cli, "get_config", lambda: tree)
    monkeypatch.setattr(cli, "PolygonEodClient", _Eod)
    return cli._cmd_correct_entry(argparse.Namespace(entry_id=entry_id, dry_run=dry,
                                                     reason="RF-D7: the rule's close"))


def _rows(tree: Config) -> list[dict[str, Any]]:
    return [json.loads(ln) for ln in (tree.snapshots_dir / "decision_ledger.jsonl").read_text()
            .splitlines() if ln.strip()]


def test_the_dry_run_prints_the_rule_and_writes_nothing(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    before = _rows(tree)
    assert _run(tree, monkeypatch, "V-GOOGL", dry=True) == 0
    out = capsys.readouterr().out
    assert "sealed     345.9 on 2026-08-14" in out and "340.65 on 2026-08-27" in out
    assert "9 session(s)" in out and "DRY RUN" in out
    assert _rows(tree) == before and not tree.db_path.exists()


def test_the_command_appends_and_exports_the_correction(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """On an EMPTY working store: the ledger table is re-seeded from the committed snapshot first,
    so the export keeps every committed row and adds the one correction."""
    before = _rows(tree)
    assert _run(tree, monkeypatch, "V-VRRM-screen2-20260617", dry=False) == 0
    after = _rows(tree)
    assert len(after) == len(before) + 1
    (new,) = [r for r in after if r["entry_id"] == "R-VRRM-screen2-20260617"]
    assert json.loads(new["payload"])["corrects_entry_id"] == "V-VRRM-screen2-20260617"
    assert {r["entry_id"]: r for r in after}["V-VRRM-screen2-20260617"] == {
        r["entry_id"]: r for r in before}["V-VRRM-screen2-20260617"]     # the sealed row, as was
    assert _run(tree, monkeypatch, "V-VRRM-screen2-20260617", dry=False) == 1   # one per decision
    assert "already corrected" in capsys.readouterr().out


def test_a_decision_the_rule_does_not_move_is_left_alone(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """THE NEGATIVE PIN: IT's sealed close is the rule's — nothing is written."""
    before = _rows(tree)
    assert _run(tree, monkeypatch, "V-IT-screen2-20260706", dry=False) == 0
    assert "nothing to correct" in capsys.readouterr().out
    assert _rows(tree) == before


# --- review round 0: the correction's edges ------------------------------------------------------


def test_a_correction_naming_no_decision_is_refused_by_every_reader() -> None:
    """A correction must correct something: one naming no decision row raises (as an unpairable
    close does), rather than leaving its decision read at the stale close in silence. The positive
    pin: the same correction beside its decision is read."""
    from vinci import monitor as mon

    rows = _committed()
    googl = next(e for e in rows if e.entry_id == "V-GOOGL")
    fix = googl.model_copy(update={
        "entry_id": "R-GOOGL", "event": EVENT_CORRECTION, "corrects_entry_id": "V-GOOGL",
        "entry_price": 340.65, "entry_price_as_of": date(2026, 8, 27), "reason": "RF-D7"})
    assert corrections_by_decision([*rows, fix])["V-GOOGL"] is fix
    orphan = [e for e in rows if e.entry_id != "V-GOOGL"] + [fix]
    with pytest.raises(ValueError, match="name no decision row"):
        corrections_by_decision(orphan)
    raw = [{"payload": e.model_dump_json()} for e in orphan]
    with pytest.raises(ValueError, match="name no decision row"):
        mon.apply_corrections(raw)


def test_a_decision_closed_before_its_corrected_entry_is_not_corrected(tmp_path: Path) -> None:
    """IT's real close, its exit moved ON A COPY to 2026-07-20 (its sealed entry session): a
    correction moving the entry to 07-21 would pair an exit before its entry in the realized view,
    so it is refused and nothing is written."""
    with Store(tmp_path / "l.db") as store:
        for e in _committed():
            if e.entry_id == "C-IT-screen2-20260706":
                e = e.model_copy(update={"exit_price_as_of": date(2026, 7, 20)})
            store.append_ledger(e)
        n = len(list(store.iter_ledger()))
        with pytest.raises(LedgerError, match="cannot close before it opened"):
            correct_entry(store, entry_id="V-IT-screen2-20260706", entry_price=140.0,
                          entry_price_as_of=date(2026, 7, 21), reason="RF-D7",
                          corrected_at=datetime(2026, 11, 10, 12))
        assert len(list(store.iter_ledger())) == n


def test_a_close_after_a_correction_is_read_at_the_corrected_entry(tmp_path: Path) -> None:
    """GOOGL corrected to 2026-08-27: a close dated 08-20 (after the sealed entry, before the
    corrected one) is refused, and a close dated after it repeats the corrected entry."""
    from vinci.ledger.workflow import close_position

    with _store(tmp_path) as store:
        correct_entry(store, entry_id="V-GOOGL", entry_price=340.65,
                      entry_price_as_of=date(2026, 8, 27), reason="RF-D7",
                      corrected_at=datetime(2026, 11, 10, 12))
        with pytest.raises(LedgerError, match="precedes the frozen entry date 2026-08-27"):
            close_position(store, candidate_id="GOOGL", exit_price=350.0,
                           exit_price_as_of=date(2026, 8, 20), reason="test",
                           closed_at=datetime(2026, 11, 10, 13))
        close = close_position(store, candidate_id="GOOGL", exit_price=350.0,
                               exit_price_as_of=date(2026, 9, 1), reason="test",
                               closed_at=datetime(2026, 11, 10, 13))
        assert (close.entry_price, close.entry_price_as_of) == (340.65, date(2026, 8, 27))


def test_the_dry_run_on_a_corrected_decision_refuses(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """A dry run of an already-corrected decision says so, rather than printing the correction as
    though it were still to be written."""
    assert _run(tree, monkeypatch, "V-GOOGL", dry=False) == 0
    capsys.readouterr()
    assert _run(tree, monkeypatch, "V-GOOGL", dry=True) == 1
    out = capsys.readouterr().out
    assert "already corrected by R-GOOGL" in out and "DRY RUN" not in out


# --- the row's shape (schema) --------------------------------------------------------------------


def _correction_of_googl(**update: Any) -> dict[str, Any]:
    googl = next(e for e in _committed() if e.entry_id == "V-GOOGL")
    row = googl.model_copy(update={
        "entry_id": "R-GOOGL", "event": EVENT_CORRECTION, "corrects_entry_id": "V-GOOGL",
        "entry_price": 340.65, "entry_price_as_of": date(2026, 8, 27), "reason": "RF-D7",
        "facts": {}, "machine_proposal": None, "machine_lean": None,
        "proposal_assembled_at": None, "disposition": None, "stated_limit": None})
    return {**row.model_dump(), **update}


def test_a_well_formed_correction_row_validates() -> None:
    """THE POSITIVE PIN for the shape guards below: GOOGL's correction, as the writer builds it."""
    row = LedgerEntry.model_validate(_correction_of_googl())
    assert (row.event, row.corrects_entry_id, row.entry_price) == (EVENT_CORRECTION, "V-GOOGL",
                                                                   340.65)


@pytest.mark.parametrize("update, expect", [
    ({"corrects_entry_id": None}, "names no decision"),
    ({"corrects_entry_id": "R-GOOGL"}, "corrects itself"),
    ({"reason": "  "}, "has no reason"),
    ({"exit_price": 350.0}, "a correction is not a close"),
    ({"facts": "a sealed fact"}, "carries facts"),
])
def test_a_malformed_correction_row_is_refused(update: dict[str, Any], expect: str) -> None:
    """Each shape guard, on GOOGL's real correction. No committed decision carries facts, so the
    fact is the real type, `LedgerFact`, as `log_verdict` would seal one."""
    if update.get("facts") == "a sealed fact":
        fact = LedgerFact(value=340.65, unit="$/share", basis="GOOGL close, 2026-08-27",
                          source="Polygon daily aggregates, GOOGL, 2026-08-27")
        update = {"facts": {"entry_close": fact.model_dump()}}
    with pytest.raises(ValueError, match=expect):
        LedgerEntry.model_validate(_correction_of_googl(**update))


def test_only_a_correction_names_a_decision_it_corrects() -> None:
    """A decision row or a close row carrying ``corrects_entry_id`` is refused: the field means one
    thing, on one kind of row."""
    rows = {e.entry_id: e for e in _committed()}
    for eid, expect in (("V-GOOGL", "on a DECISION row"), ("C-IT-screen2-20260706", "a close")):
        with pytest.raises(ValueError, match=expect):
            LedgerEntry.model_validate({**rows[eid].model_dump(), "corrects_entry_id": "V-GOOGL"})


# --- the row's tags, and the committed corrections --------------------------------------------


def test_a_correction_is_tagged_as_its_decision_is_read(tmp_path: Path) -> None:
    """VRRM's decision predates `origin`/`sleeve` and carries neither; its correction is logged
    since, so it carries both — the reading the helpers give the decision (screen/overshoot), never
    the decision's absent fields (found on 2026-11-10: `tests/test_sleeves.py` refused an untagged
    `R-VRRM-screen2-20260617` before it was appended). GOOGL's tagged decision passes its own
    followed/quality through."""
    with _store(tmp_path) as store:
        vrrm = correct_entry(store, entry_id=_VRRM, entry_price=4.44,
                             entry_price_as_of=date(2026, 6, 18), reason="RF-D7",
                             corrected_at=datetime(2026, 11, 10, 12))
        googl = correct_entry(store, entry_id="V-GOOGL", entry_price=340.65,
                              entry_price_as_of=date(2026, 8, 27), reason="RF-D7",
                              corrected_at=datetime(2026, 11, 10, 12))
    decisions = {e.entry_id: e for e in _committed()}
    assert (decisions[_VRRM].origin, decisions[_VRRM].sleeve) == (None, None)   # legacy, as sealed
    assert (vrrm.origin, vrrm.sleeve) == (origin_of(decisions[_VRRM]),
                                          sleeve_of(decisions[_VRRM])) == ("screen", "overshoot")
    assert (googl.origin, googl.sleeve) == (decisions["V-GOOGL"].origin,
                                            decisions["V-GOOGL"].sleeve) == ("followed", "quality")


def test_every_committed_correction_is_the_rules_close() -> None:
    """THE COMMITTED ARTIFACT: each CORRECTION row in the committed ledger names a committed
    decision the rule moves, and carries exactly the rule's session and Polygon's close for it
    (`tests/fixtures/prices/`). Phrasing-independent; it reads whatever corrections are committed,
    so it holds before the two are appended (none) and after (R-GOOGL, R-VRRM-screen2-20260617)."""
    rows = [LedgerEntry.model_validate(json.loads(json.loads(ln)["payload"]))
            for ln in LEDGER.read_text().splitlines() if ln.strip()]
    decisions = {e.entry_id: e for e in rows if e.event is None}
    for c in (e for e in rows if e.event == EVENT_CORRECTION):
        d = decisions[str(c.corrects_entry_id)]
        closes = {date.fromisoformat(b["bar_date"]): float(b["close"]) for b in _bars(d.ticker)}
        session = rule_session(d.decided_at, list(closes))
        assert session is not None and session != d.entry_price_as_of, c.entry_id
        assert (c.entry_price_as_of, c.entry_price) == (session, closes[session]), c.entry_id
        assert (c.origin, c.sleeve) == (origin_of(d), sleeve_of(d)), c.entry_id
