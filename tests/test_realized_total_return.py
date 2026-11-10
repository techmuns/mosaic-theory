"""THE REALIZED VIEW IS A TOTAL RETURN, THE BASIS ITS DAY DECLARES (TeamNostra fix request 2,
RF-D3, 2026-11-09).

THE DEFECT, reproduced on main 7c87164a before the fix: a flat stock that paid a $20 special
dividend — 100, then 80 ex-dividend, flat on total return — closed at 80 printed "−20.00%
realized" from `close-position`, and the monitor's realized row read −0.2000 beside a mark of
+0.0000 on the same name, inside a day whose ``price_basis`` reads "TOTAL return both sides".
`pair_closes` derived ``exit / entry − 1`` and `close-position` printed the same ratio; operator
ruling B (2026-10-26) named scoring, the basket and the marks, and never the realized view.

THE FIX. Both read the dividends the position went ex in (entry, exit] — Tiingo, through the same
`DividendSource` every mark uses — and reinvest them on the ex-date: ``exit / entry × growth − 1``.
The price return rides beside (``realized_price_return``). A window whose dividends cannot be read
stops the monitor and refuses the close; neither falls back to a price return.

Pinned on the real types: Tiingo's rows through the real `tiingo_dividends`, the committed ledger's
two closes, the real `close-position` and `vinci monitor` commands.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.dividend_support import no_dividends, no_splits, weekday_calendar, weekday_sessions
from tests.test_split_confirmed_by_tiingo import _Polygon, _tiingo_row
from vinci.config import Config
from vinci.eod.dividends import DividendsUnknownError, tiingo_dividends
from vinci.ledger import close_position
from vinci.monitor import RealizedRow, pair_closes
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
ENTRY, EX, EXIT = date(2026, 1, 5), date(2026, 4, 1), date(2026, 6, 1)


class _Tiingo:
    """Tiingo's rows for one name: ``before`` until ``ex``, ``after`` from it, ``cash`` paid on
    ``ex`` — the unadjusted close and divCash as served."""

    def __init__(self, name: str, before: float, after: float, ex: date, cash: float) -> None:
        self.name, self.before, self.after, self.ex, self.cash = name, before, after, ex, cash

    def daily_rows(self, symbol: str, *, start: date, end: date,
                   ttl_seconds: float | None = 86_400.0) -> list[dict[str, Any]]:
        if symbol.upper() != self.name:
            return [_tiingo_row(d, 200.0) for d in weekday_sessions(start, end)]
        return [_tiingo_row(d, self.before if d < self.ex else self.after,
                            cash=self.cash if d == self.ex else 0.0)
                for d in weekday_sessions(start, end)]


def _book(tmp_path: Path, exit_price: float) -> list[dict[str, Any]]:
    """A decision sealed at 100 and its close at ``exit_price``, through the real writer, exported
    as the committed ledger is."""
    with Store(tmp_path / "l.db") as store:
        store.append_ledger(LedgerEntry(
            entry_id="V-DIV-c", candidate_id="DIV-c", internal_id="SEC-0000000010-DIV",
            ticker="DIV", verdict=Verdict.BUY, twin_call="t", entry_price=100.0,
            entry_price_as_of=ENTRY, thesis="t", kill_criteria="k", horizon_days=180,
            confidence=Confidence.MEDIUM, decided_at=datetime(2026, 1, 5)))
        close_position(store, candidate_id="DIV-c", exit_price=exit_price, exit_price_as_of=EXIT,
                       reason="closed", closed_at=datetime(2026, 6, 2))
        store.export_snapshots(tmp_path, tables=["decision_ledger"])
    return [json.loads(ln) for ln in (tmp_path / "decision_ledger.jsonl").read_text().splitlines()
            if ln.strip()]


def test_a_flat_stock_with_a_20pct_special_dividend_realizes_zero(tmp_path: Path) -> None:
    """THE DONE-WHEN: 100 → 80 ex a $20 dividend, closed at 80 — 0% total return. On main
    −0.2000."""
    divs = tiingo_dividends(_Tiingo("DIV", 100.0, 80.0, EX, 20.0),  # type: ignore[arg-type]
                            start=ENTRY, end=EXIT, sessions=weekday_calendar)
    (row,) = pair_closes(_book(tmp_path, 80.0), splits=no_splits, dividends=divs)
    assert row["realized_return"] == pytest.approx(0.0, abs=1e-12)
    assert row["realized_price_return"] == pytest.approx(-0.2)
    rr = RealizedRow.model_validate(row)
    assert rr.realized_return == pytest.approx(0.0, abs=1e-12) and "REALIZED +0.0%" in rr.note()


def test_with_no_dividend_the_realized_return_is_the_two_price_ratio(tmp_path: Path) -> None:
    """THE NEGATIVE PIN: no ex-date in the window — total and price return are one number."""
    divs = tiingo_dividends(_Tiingo("DIV", 100.0, 100.0, EX, 0.0),  # type: ignore[arg-type]
                            start=ENTRY, end=EXIT, sessions=weekday_calendar)
    (row,) = pair_closes(_book(tmp_path, 90.0), splits=no_splits, dividends=divs)
    assert row["realized_return"] == row["realized_price_return"] == 90.0 / 100.0 - 1.0


def test_a_window_whose_dividends_cannot_be_read_is_never_a_price_return(tmp_path: Path) -> None:
    lost = _Tiingo("DIV", 100.0, 80.0, EX, 20.0)
    real = lost.daily_rows

    def without_the_ex_date(symbol: str, **kw: Any) -> list[dict[str, Any]]:
        return [r for r in real(symbol, **kw) if not r["date"].startswith(EX.isoformat())]
    lost.daily_rows = without_the_ex_date  # type: ignore[method-assign,assignment]
    divs = tiingo_dividends(lost, start=ENTRY, end=EXIT,  # type: ignore[arg-type]
                            sessions=weekday_calendar)
    with pytest.raises(DividendsUnknownError, match="no row for 1 session"):
        pair_closes(_book(tmp_path, 80.0), splits=no_splits, dividends=divs)


def test_the_committed_closes_read_as_they_always_did() -> None:
    """THE CORPUS: IT and SMPL pay no dividend, and their committed closes' realized returns are
    the ratios they were — the fix moves no committed number."""
    rows = [json.loads(ln) for ln in (ROOT / "data/snapshots/decision_ledger.jsonl").read_text()
            .splitlines() if ln.strip()]
    by_id = {r["entry_id"]: r for r in pair_closes(rows, splits=no_splits, dividends=no_dividends)}
    assert by_id["V-IT-screen2-20260706"]["realized_return"] == 0.0
    assert by_id["V-SMPL-screen2-20260706"]["realized_return"] == 10.53 / 10.92 - 1.0
    assert all(r["realized_return"] == r["realized_price_return"] for r in by_id.values())


# --- close-position -------------------------------------------------------------------------------


_OPEN = "SMPL-screen2-20260729"          # SMPL's open decision: sealed $11.33 on 2026-08-04


@pytest.fixture
def tree(tmp_path: Path) -> Config:
    data = tmp_path / "data"
    data.mkdir()
    shutil.copytree(ROOT / "data" / "snapshots", data / "snapshots")
    cfg = Config(data_dir=data)
    cfg.ensure_dirs()
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
    return cfg


def _rows(tree: Config) -> list[dict[str, Any]]:
    path = tree.snapshots_dir / "decision_ledger.jsonl"
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def _close(tree: Config, monkeypatch: pytest.MonkeyPatch, tiingo: _Tiingo,
           exit_price: float, as_of: str = "2026-10-01") -> int:
    """The real command, its vendors faked at their clients: Polygon's sessions and an empty
    splits reference, Tiingo's rows — so its own `default_dividends` and `default_splits` run."""
    from vinci import cli
    from vinci.eod.tiingo import TiingoEodClient
    monkeypatch.setenv("POLYGON_API_KEY", "fake-not-a-key")
    monkeypatch.setenv("TIINGO_API_KEY", "fake-not-a-key")
    monkeypatch.setattr(cli, "get_config", lambda: tree)
    monkeypatch.setattr(cli.PolygonEodClient, "from_config",
                        classmethod(lambda _c, _cfg=None: _Polygon({}, {})))
    monkeypatch.setattr(TiingoEodClient, "from_config", classmethod(lambda _c, _cfg=None: tiingo))
    return cli._cmd_close_position(argparse.Namespace(
        candidate_id=_OPEN, exit_price=exit_price, as_of=as_of, reason="constructed"))


def test_close_position_prints_the_total_return(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """SMPL's real open decision ($11.33, 2026-08-04), a constructed 20% special dividend on
    2026-09-01 and a close at the ex-dividend price: 0.00% total, −20.00% price. On main the
    command printed "= -20.00% realized"."""
    tiingo = _Tiingo("SMPL", 11.33, 11.33 * 0.8, date(2026, 9, 1), 11.33 * 0.2)
    assert _close(tree, monkeypatch, tiingo, 11.33 * 0.8) == 0
    out = capsys.readouterr().out
    assert "= +0.00% realized, total return (price return -20.00%)" in out


def test_close_position_refuses_an_exit_that_is_no_posted_session(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """An exit dated a Saturday: the total return is read through the exit session, and there is
    none — refused in words, nothing written, no price return printed in place of the total."""
    before = _rows(tree)
    tiingo = _Tiingo("SMPL", 11.33, 11.33, date(2026, 9, 1), 0.0)
    assert _close(tree, monkeypatch, tiingo, 11.33, as_of="2026-10-03") == 1
    out = capsys.readouterr().out
    assert ("REFUSED: --as-of 2026-10-03 is not a session SMPL traded whose bar has posted (its "
            "last on or before is 2026-10-02)") in out and "% realized" not in out
    assert _rows(tree) == before


class _Lost(_Tiingo):
    """Tiingo's rows with the ex-date's row lost."""

    def daily_rows(self, symbol: str, *, start: date, end: date,
                   ttl_seconds: float | None = 86_400.0) -> list[dict[str, Any]]:
        return [r for r in super().daily_rows(symbol, start=start, end=end)
                if not (symbol.upper() == self.name and r["date"].startswith(self.ex.isoformat()))]


def test_close_position_refuses_when_the_dividends_cannot_be_read(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """A session exit, and Tiingo lost the ex-date's row: the dividends are unknown — refused."""
    before = _rows(tree)
    tiingo = _Lost("SMPL", 11.33, 11.33 * 0.8, date(2026, 9, 1), 11.33 * 0.2)
    assert _close(tree, monkeypatch, tiingo, 11.33 * 0.8) == 1
    out = capsys.readouterr().out
    assert "REFUSED" in out and "% realized" not in out
    assert _rows(tree) == before


# --- the monitor ---------------------------------------------------------------------------------


def test_the_monitor_day_carries_the_realized_total_return(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """END TO END through `vinci monitor --out` over the committed ledger: each realized row is
    total return with price beside it — SMPL's committed close paid nothing, so its two agree;
    give its window a dividend and the total return reads above the price return."""
    from tests.test_monitor_ref_date_bound import _wire, _written
    from tests.test_total_return import _yields
    from vinci import cli
    _wire(tmp_path, monkeypatch, [])
    paid = {"GOOGL": 0.0, "IT": 0.0, "SMPL": 0.0, "VRRM": 0.0, "SPY": 0.0, "MDY": 0.0, "IWM": 0.0}
    monkeypatch.setattr(cli, "default_dividends", lambda **_kw: _yields(paid))
    assert cli._cmd_monitor(argparse.Namespace(ref="2026-10-23", out=str(tmp_path / "a"))) == 0
    flat = {r["ticker"]: r for r in _written(tmp_path / "a" / "data/monitor")["realized"]}
    assert flat["SMPL"]["realized_return"] == flat["SMPL"]["realized_price_return"]

    monkeypatch.setattr(cli, "default_dividends", lambda **_kw: _yields({**paid, "SMPL": 0.01}))
    assert cli._cmd_monitor(argparse.Namespace(ref="2026-10-23", out=str(tmp_path / "b"))) == 0
    paid_day = {r["ticker"]: r for r in _written(tmp_path / "b" / "data/monitor")["realized"]}
    smpl = paid_day["SMPL"]
    assert smpl["realized_price_return"] == flat["SMPL"]["realized_price_return"]
    assert smpl["realized_return"] == pytest.approx(
        (1.0 + smpl["realized_price_return"]) * 1.01 - 1.0)


def test_the_monitor_refuses_a_realized_return_without_its_dividends(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.test_monitor_ref_date_bound import _wire
    from tests.test_total_return import _yields
    from vinci import cli
    _wire(tmp_path, monkeypatch, [])
    monkeypatch.setattr(cli, "default_dividends", lambda **_kw: _yields({"GOOGL": 0.0}))
    with pytest.raises(RuntimeError, match="dividends UNKNOWN.*realized return"):
        cli._cmd_monitor(argparse.Namespace(ref="2026-10-23", out=str(tmp_path / "s")))
