"""The monitor marks a row past its horizon at its HORIZON SESSION'S close (2026-10-27).

The scoring harness scores a resolved row on the last session on or before its horizon (#820); the
monitor marked every row to the RUN's session, so from the first run after 2026-12-14 VRRM would
have read RESOLVED on the web with a return through whatever day the monitor ran (record
2026-10-27-score-on-the-horizon-close, FOUND 1). The rules, each pinned here end to end through the
real `vinci monitor` command:

1. A row the run's session has reached is marked at `session_on_or_before(horizon)` — the name's
   close, the benchmark's close, and dividends over entry → that session.
2. ``resolved`` is the RUN's session, never the marked one: a Saturday horizon resolves on Monday's
   run and is priced at Friday's close — the harness's rule 1.
3. A name missing from the horizon session raises, as scoring does; it is never marked on another
   bar. A name missing only AFTER its horizon no longer stops the run.
4. The cross-surface pin: on the same bars, `score_ledger` and the monitor give the SAME resolved
   return for the same row.

FROZEN FIXTURES: VRRM's and IWM's real Polygon bars, 2026-06-15 → 2026-10-16
(`tests/fixtures/horizon_close/vrrm_iwm_bars.jsonl`, #820), served as grouped-daily days (empty on
any day the fixture holds no bar, as Polygon is on a weekend). The ledger is a COPY in the test's
tmp dir holding only VRRM's real row, its horizon shortened where a rule needs it inside the window.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Callable
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.dividend_support import no_dividends, no_splits
from vinci import monitor as mon
from vinci.schemas.ledger import LedgerEntry
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.store import Store

ROOT = Path(__file__).resolve().parent.parent
_BARS = ROOT / "tests" / "fixtures" / "horizon_close" / "vrrm_iwm_bars.jsonl"
_SYM = {"SEC-0001682745-VRRM": "VRRM", "IDX-IWM": "IWM"}
_VRRM_ID = "V-VRRM-screen2-20260617"


def _close(sym: str, on: date) -> float:
    for ln in _BARS.read_text().splitlines():
        r = json.loads(ln)
        if _SYM[r["internal_id"]] == sym and r["bar_date"] == on.isoformat():
            return float(r["close"])
    raise AssertionError(f"no {sym} bar on {on}")


def _vrrm_ledger_row(horizon_days: int) -> dict[str, Any]:
    """VRRM's real committed ledger line, its horizon shortened on the COPY (both the indexed
    column and the payload, which the monitor reads separately)."""
    for ln in (ROOT / "data/snapshots/decision_ledger.jsonl").read_text().splitlines():
        row = json.loads(ln) if ln.strip() else {}
        if row.get("entry_id") == _VRRM_ID:
            payload = json.loads(row["payload"])
            payload["horizon_days"] = horizon_days
            return {**row, "horizon_days": horizon_days, "payload": json.dumps(payload)}
    raise AssertionError(f"{_VRRM_ID} is not in the committed ledger")


def _monitor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, horizon_days: int, ref: str,
             vrrm_missing: Callable[[date], bool] = lambda _d: False,
             dividends: Any = no_dividends) -> dict[str, Any]:
    """`vinci monitor --ref <ref> --out <scratch>` over a book holding only VRRM's row; returns the
    written day's VRRM row with the day's spread beside it."""
    from vinci import cli
    book = tmp_path / "book"
    (book / "data/snapshots").mkdir(parents=True)
    (book / "data/monitor").mkdir(parents=True)
    (book / "scenarios").mkdir()
    (book / "data/snapshots/decision_ledger.jsonl").write_text(
        json.dumps(_vrrm_ledger_row(horizon_days)) + "\n")
    for rel in ("data/snapshots/securities.jsonl", "data/monitor/benchmark_assignments.json"):
        shutil.copy(ROOT / rel, book / rel)
    days: dict[date, dict[str, Any]] = {}
    for ln in _BARS.read_text().splitlines():
        r = json.loads(ln)
        d, sym = date.fromisoformat(r["bar_date"]), _SYM[r["internal_id"]]
        if not (sym == "VRRM" and vrrm_missing(d)):
            days.setdefault(d, {})[sym] = SimpleNamespace(close=float(r["close"]))

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
    monkeypatch.setattr(cli, "default_dividends", lambda **_kw: dividends)
    monkeypatch.setattr(cli, "default_splits", lambda *_a, **_k: no_splits)
    scratch = tmp_path / "scratch"
    assert cli._cmd_monitor(argparse.Namespace(ref=ref, out=str(scratch))) == 0
    (day,) = [json.loads(p.read_text()) for p in (scratch / "data/monitor").glob("*.json")]
    (row,) = day["rows"]
    return {**row, "_day": day}


# --- rule 1: a resolved row is marked at its horizon session ----------------------------------


def test_a_row_past_its_horizon_is_marked_at_the_horizon_close_not_the_runs(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Horizon 119 days → Wednesday 2026-10-14; the run reaches Friday 10-16. The row resolves and
    is marked on 10-14 — the name's close, the benchmark's — and the spread reads that mark."""
    row = _monitor(tmp_path, monkeypatch, horizon_days=119, ref="2026-10-16")
    assert row["_day"]["as_of"] == "2026-10-16"
    assert row["resolved"] is True
    assert (row["current_date"], row["current_price"]) == ("2026-10-14",
                                                           _close("VRRM", date(2026, 10, 14)))
    assert row["benchmark_now"] == _close("IWM", date(2026, 10, 14))
    assert row["days_elapsed"] == 119
    assert row["position_return"] == pytest.approx(_close("VRRM", date(2026, 10, 14)) / 4.71 - 1)
    spread = row["_day"]["spread"]
    assert spread["resolved_n"] == 1 and spread["avoid_mean_excess"] == pytest.approx(row["excess"])
    table = mon.render_table(mon.MonitorSnapshot.model_validate(row["_day"]))
    assert "RESOLVED · marked at its horizon close 2026-10-14" in table


def test_a_row_short_of_its_horizon_is_still_marked_at_the_runs_session(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE PIN: VRRM's real 180-day row (2026-12-14) marks to the run's own close."""
    row = _monitor(tmp_path, monkeypatch, horizon_days=180, ref="2026-10-16")
    assert row["resolved"] is False
    assert (row["current_date"], row["current_price"]) == ("2026-10-16",
                                                           _close("VRRM", date(2026, 10, 16)))
    assert "RESOLVED" not in mon.render_table(mon.MonitorSnapshot.model_validate(row["_day"]))


def test_a_resolved_rows_dividends_stop_at_its_horizon_session(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An IWM payment on 2026-10-15 — after the 10-14 horizon, before the 10-16 run — is not in
    the resolved row's window; the same payment on 10-13 is. Each leg's window is entry → the
    MARKED session, as the scoring harness reads it."""
    def paying(on: date) -> Callable[[str, date, date], list[tuple[date, float]]]:
        def src(symbol: str, start: date, end: date) -> list[tuple[date, float]]:
            return [(on, 0.01)] if symbol == "IWM" and start < on <= end else []
        return src
    iwm = _close("IWM", date(2026, 10, 14)) / _close("IWM", date(2026, 6, 17))
    after = _monitor(tmp_path / "a", monkeypatch, horizon_days=119, ref="2026-10-16",
                     dividends=paying(date(2026, 10, 15)))
    assert after["benchmark_return"] == pytest.approx(iwm - 1)
    inside = _monitor(tmp_path / "b", monkeypatch, horizon_days=119, ref="2026-10-16",
                      dividends=paying(date(2026, 10, 13)))
    assert inside["benchmark_return"] == pytest.approx(iwm * 1.01 - 1)


# --- rule 2: resolved by the run's session; a weekend horizon priced at Friday -----------------


def test_a_weekend_horizon_resolves_on_mondays_run_at_fridays_close(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Horizon 115 days → Saturday 2026-10-10. Monday's run resolves it, priced at Friday 10-09."""
    row = _monitor(tmp_path, monkeypatch, horizon_days=115, ref="2026-10-12")
    assert row["_day"]["as_of"] == "2026-10-12"
    assert row["resolved"] is True
    assert (row["current_date"], row["current_price"]) == ("2026-10-09",
                                                           _close("VRRM", date(2026, 10, 9)))


def test_a_weekend_horizon_is_not_resolved_by_fridays_run(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE PIN: a run on Sunday 10-11 reaches Friday's session, short of the Saturday horizon
    — unresolved, an ordinary mark at that session."""
    row = _monitor(tmp_path, monkeypatch, horizon_days=115, ref="2026-10-11")
    assert row["_day"]["as_of"] == "2026-10-09"
    assert row["resolved"] is False and row["current_date"] == "2026-10-09"


# --- rule 3: the horizon session is the only bar a resolved row is marked on ------------------


def test_a_name_missing_at_its_horizon_session_raises_naming_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """VRRM has no bar on 2026-10-14 alone; it trades again on 10-15 and 10-16. The row is never
    marked on the run's later bar, nor on the 10-13 bar before it."""
    with pytest.raises(RuntimeError, match="2026-10-14 is its HORIZON session"):
        _monitor(tmp_path, monkeypatch, horizon_days=119, ref="2026-10-16",
                 vrrm_missing=lambda d: d == date(2026, 10, 14))


def test_a_name_that_stops_trading_after_its_horizon_still_marks_at_the_horizon(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE PIN: VRRM has no bar after 10-14. The resolved row needs only its horizon session,
    so the run marks it there; it used to stop the whole run for want of the run's own bar."""
    row = _monitor(tmp_path, monkeypatch, horizon_days=119, ref="2026-10-16",
                   vrrm_missing=lambda d: d > date(2026, 10, 14))
    assert row["resolved"] is True and row["current_date"] == "2026-10-14"


# --- rule 4: the cross-surface pin ------------------------------------------------------------


def test_the_monitor_and_the_scoring_report_give_the_same_resolved_return(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ONE ROW, ONE RESOLVED NUMBER. The same bars and the same row, scored by `score_ledger` and
    marked by `vinci monitor`: the name's return, the benchmark's and the excess agree."""
    row = _monitor(tmp_path, monkeypatch, horizon_days=119, ref="2026-10-16")
    entry = LedgerEntry.model_validate(json.loads(_vrrm_ledger_row(119)["payload"]))
    with Store(tmp_path / "s.db") as store:
        store.write_prices([PriceBar.model_validate(json.loads(ln))
                            for ln in _BARS.read_text().splitlines()])
        store.append_ledger(entry)
        (score,), _report = score_ledger(store, as_of=date(2026, 10, 16), dividends=no_dividends,
                                         splits=no_splits)
    assert score.resolved is True and row["resolved"] is True
    assert row["position_return"] == pytest.approx(score.name_return, abs=1e-12)
    assert row["benchmark_return"] == pytest.approx(score.bench_return, abs=1e-12)
    assert row["excess"] == pytest.approx(score.excess_gross, abs=1e-12)


# --- the three web views label a resolved row's mark as its horizon close ---------------------


def test_the_three_views_label_a_resolved_mark_as_the_horizon_close_node(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-LAYER RULE, end to end: the rows the real command wrote — VRRM resolved at its 10-14
    horizon, and its real 180-day row unresolved — rendered by the decision log (the mark row and
    the spread card), the panels page (`the_call`, through the real payload) and the dossier's
    implied-odds line. ⊕ resolved reads "horizon close"; ⊖ unresolved keeps "Current"/"now"."""
    import subprocess

    from vinci import panels_payload as pay
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    done = _monitor(tmp_path / "a", monkeypatch, horizon_days=119, ref="2026-10-16")
    live = _monitor(tmp_path / "b", monkeypatch, horizon_days=180, ref="2026-10-16")
    marks = tmp_path / "marks.json"
    marks.write_text(json.dumps({
        "done": {k: v for k, v in done.items() if k != "_day"}, "doneDay": done["_day"],
        "live": {k: v for k, v in live.items() if k != "_day"}, "liveDay": live["_day"],
        "doneCall": pay.the_call(done), "liveCall": pay.the_call(live)}))
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const imp = (f) => import(pathToFileURL(path.resolve(`frontend/views/shared/${f}`)).href);
const { liveRow, spreadCard } = await imp("decision-log.js");
const { panelGridHtml } = await imp("panels.js");
const { uwCard } = await imp("uw-card.js");
const m = JSON.parse(readFileSync(process.argv[1]));
const card = JSON.parse(readFileSync("frontend/scenarios/IT.json"));
const base = { ticker: "VRRM", tier: "universal", changes_the_call: "c", caveat: "",
  cadence: "event", missing: [], reason: "", sources: [] };
const call = (v) => panelGridHtml([{ ...base, key: "the_call", title: "The call",
  state: "ready", value: v }], { ticker: "VRRM" });
console.log(JSON.stringify({
  logDone: liveRow(m.done), logLive: liveRow(m.live),
  spreadDone: spreadCard(m.doneDay), spreadLive: spreadCard(m.liveDay),
  callDone: call(m.doneCall), callLive: call(m.liveCall),
  oddsDone: uwCard(card, { mark: m.done }), oddsLive: uwCard(card, { mark: m.live }),
}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver, str(marks)],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    r = json.loads(out.stdout)
    assert ">Horizon close<" in r["logDone"] and ">Current<" not in r["logDone"]
    assert ">Current<" in r["logLive"] and "Horizon close" not in r["logLive"]
    assert "resolved rows at their horizon close" in r["spreadDone"]
    assert "horizon close" not in r["spreadLive"]
    assert "horizon close $2.94" in r["callDone"] and ">now " not in r["callDone"]
    assert ">now $2.86" in r["callLive"] and "horizon close" not in r["callLive"]
    assert "bear weight at its horizon close" in r["oddsDone"]
    assert "Market-implied bear weight" in r["oddsLive"] and "horizon close" not in r["oddsLive"]


# --- review round 0 ---------------------------------------------------------------------------


def test_a_run_on_the_horizon_session_itself_names_it_when_the_name_is_missing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The run's own session IS the 10-14 horizon: a missing VRRM bar there is still the resolved
    row's only valid mark, and the error says so."""
    with pytest.raises(RuntimeError, match="2026-10-14 is its HORIZON session"):
        _monitor(tmp_path, monkeypatch, horizon_days=119, ref="2026-10-14",
                 vrrm_missing=lambda d: d == date(2026, 10, 14))


def test_the_spread_card_notes_a_resolved_row_outside_the_screen_scope_node() -> None:
    """`resolved_n` counts screen-origin rows only; a followed row resolved alone still carries a
    horizon-close mark, so the card's 'marked <date>' line must say so. ⊖ none resolved: no note."""
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const view = path.resolve("frontend/views/shared/decision-log.js");
const { spreadCard } = await import(pathToFileURL(view).href);
const day = (resolved) => ({ as_of: "2026-10-26", spread: { resolved_n: 0, scoped_n: 1 },
  rows: [{ ticker: "VRRM", origin: "screen", resolved: false },
         { ticker: "GOOGL", origin: "followed", resolved }] });
console.log(JSON.stringify({ followed: spreadCard(day(true)), none: spreadCard(day(false)) }));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver], capture_output=True,
                         text=True, check=True, cwd=ROOT)
    r = json.loads(out.stdout)
    assert "resolved rows at their horizon close" in r["followed"]
    assert "horizon close" not in r["none"]
