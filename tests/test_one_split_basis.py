"""ONE SPLIT BASIS — every return the fund scores divides two prices on the same split basis
(audit item F-D1, with the two it rests on, F-D5 and F-D3; 2026-10-29).

THE DEFECT, reproduced on main 0fa8ce4a before the fix. Scoring, the monitor's marks, its realized
view and `close-position` divided a split-adjusted exit close by the entry price sealed at purchase.
The price store is kept on Polygon's CURRENT basis (`adjusted=true`, and `restate_held` rescaling
held bars), and the sealed price stays on the entry date's, so a flat stock that split 2-for-1
inside its window scored −50.00%, resolved, with no note, and one that reverse-split 1-for-10
scored +900%. The rule that replaces it is `vinci.eod.splits.entry_on_basis` (its module note).

Every pin here runs a real path: `ingest_prices` (its anchor restatement included) into a store
and then `score_ledger`; the real `vinci monitor` command over VRRM's committed ledger row and its
frozen Polygon bars; the real `close-position` command over a copy of the committed ledger. The
splits are supplied as the reference would record them; `parse_splits` is pinned on the real
responses.

F-D5 — a split read from prices alone. `restatement_factor` took any bar whose four prices moved by
one factor for a split, so a one-print correction of 1.04 rescaled the name's whole held history;
once scoring trusts a restatement, that flows into a scored return. A split now needs volume to move
inversely by the same factor.

F-D3 — dividend coverage measured in calendar days. A weekday missing from Tiingo's rows is a gap
shorter than a holiday weekend, so a window missing its one ex-date row read as covered and returned
no dividend. Coverage is now checked against the market's sessions.
"""
from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.dividend_support import no_dividends, no_splits, weekday_sessions
from vinci.config import Config
from vinci.eod.client import EodClient, RawBar, ingest_prices, restatement_factor
from vinci.eod.dividends import DividendsUnknownError, ex_date_yields, tiingo_dividends
from vinci.eod.splits import (
    Split,
    SplitBasisError,
    SplitsUnknownError,
    entry_on_basis,
    parse_splits,
)
from vinci.monitor import pair_closes
from vinci.schemas.data_record import Identity
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.schemas.market import PriceBar
from vinci.scoring import score_ledger
from vinci.scoring.harness import SplitsUnreadError
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
_SPLITS = ROOT / "tests" / "fixtures" / "splits_reference" / "ledger_names.json"
_RESTATED = ROOT / "tests" / "fixtures" / "splits_reference" / "restated_2026-08-05.json"

X = Identity(internal_id="SEC-0000000009-SPLT", issuer_id="ISS-0000000009", cik="0000000009",
             ticker="SPLT", mic="XNAS", exchange="Nasdaq", eod_symbol="SPLT", name="Split Test Co")
IWM = Identity(internal_id="IDX-IWM", issuer_id="IDX", cik="", ticker="IWM", mic="ARCX",
               exchange="ETF", eod_symbol="IWM", name="IWM")

ENTRY = date(2026, 1, 5)              # a Monday
FIRST_PULL_END = date(2026, 3, 31)    # the store's first pull ends here, on the pre-split basis
SPLIT_DAY = date(2026, 4, 1)          # the split executes after it
AS_OF = date(2026, 7, 10)             # 180 days from ENTRY is Saturday 07-04: exit Friday 07-03


def _raw(sym: str, px: float, vol: float) -> RawBar:
    return RawBar(ticker=sym, open=px, high=px * 1.01, low=px * 0.99, close=px, volume=vol)


class _Feed(EodClient):
    """Grouped-daily as `adjusted=true` serves it on the day of the pull: EVERY day on that day's
    basis (a split restates the whole history), volume moving inversely to price."""

    def __init__(self, price: Callable[[date], float] | float, volume: float) -> None:
        self.price = price if callable(price) else (lambda _d, p=price: p)
        self.volume = volume

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        if day.weekday() >= 5:
            return {}
        return {"SPLT": _raw("SPLT", self.price(day), self.volume),
                "IWM": _raw("IWM", 200.0, 1e6)}


def _recorded(*splits: Split) -> Callable[[str], list[Split]]:
    def source(symbol: str) -> list[Split]:
        return list(splits) if symbol == "SPLT" else []
    return source


def _unreadable(symbol: str) -> list[Split]:
    raise SplitsUnknownError(f"{symbol}: the splits reference request failed (HttpError)")


def _scored(tmp_path: Path, *, after: _Feed, splits: Callable[[str], list[Split]],
            before: _Feed | None = None, sealed: float | None = None, as_of: date = AS_OF,
            horizon_days: int = 180) -> dict[str, Any]:
    """The store's first pull (``before``, through FIRST_PULL_END) and the entry sealed at its
    close on ENTRY (or ``sealed``, for a ledger written off another store); then the second pull
    (``after``, every day to ``as_of``) through the real anchor restatement; then `score_ledger`."""
    with Store(tmp_path / "split.db") as store:
        if before is not None:
            ingest_prices(before, store, [X, IWM], start=ENTRY, end=FIRST_PULL_END)
        if sealed is None:
            sealed = store.close_as_of(X.internal_id, reference_date=ENTRY,
                                       staleness_days=5).value
        assert sealed is not None
        store.append_ledger(LedgerEntry(
            entry_id="V-SPLT", candidate_id="SPLT-c", internal_id=X.internal_id, ticker="SPLT",
            verdict=Verdict.BUY, twin_call="t", entry_price=sealed, entry_price_as_of=ENTRY,
            thesis="t", kill_criteria="k", horizon_days=horizon_days,
            confidence=Confidence.MEDIUM, decided_at=datetime(2026, 1, 5)))
        summary = ingest_prices(after, store, [X, IWM], start=ENTRY, end=as_of)
        hist = store.get_price_history(X.internal_id)
        scores, report = score_ledger(store, as_of=as_of, dividends=no_dividends, splits=splits)
        ledger = [e.entry_price for e in store.iter_ledger()]
    return {"scores": scores, "report": report, "summary": summary, "hist": hist,
            "ledger": ledger, "sealed": sealed}


def _bar(hist: list[PriceBar], on: date) -> PriceBar:
    return next(b for b in hist if b.bar_date == on)


# --- scoring: the fix -------------------------------------------------------------------------


@pytest.mark.parametrize("before, after, split, factor", [
    (_Feed(100.0, 1000.0), _Feed(50.0, 2000.0), Split(execution_date=SPLIT_DAY, split_from=1,
                                                       split_to=2), 0.5),
    (_Feed(10.0, 10_000.0), _Feed(100.0, 1000.0), Split(execution_date=SPLIT_DAY, split_from=10,
                                                         split_to=1), 10.0),
], ids=["2-for-1", "1-for-10"])
def test_a_split_inside_the_window_scores_the_economics_not_the_split(
        tmp_path: Path, before: _Feed, after: _Feed, split: Split, factor: float) -> None:
    """A flat stock that splits inside its window returned nothing. On main the 2-for-1 scored
    −0.5000 and the 1-for-10 +9.0000, each resolved with no note."""
    r = _scored(tmp_path, before=before, after=after, splits=_recorded(split))
    # the store did what #796 built it to: one basis, the held bars restated and tagged
    assert r["summary"]["restated"] == {"SPLT": [pytest.approx(factor)]}
    entry_bar = _bar(r["hist"], ENTRY)
    assert entry_bar.source == "polygon-grouped+restated"
    assert entry_bar.close == pytest.approx(r["sealed"] * factor)
    (s,) = r["scores"]
    assert s.resolved
    assert s.name_return == pytest.approx(0.0, abs=1e-12)
    assert s.name_price_return == pytest.approx(0.0, abs=1e-12)
    # the note names the sealed price, f and the split — and reaches the report the reader opens
    assert s.note is not None and "ON ONE SPLIT BASIS" in s.note
    assert split.label() in s.note and f"×{factor:.6g}" in s.note
    assert f"{r['sealed']:g}" in s.note and "polygon-grouped+restated" in s.note
    assert any(split.label() in n for n in r["report"].row_notes)
    assert r["report"].buy_mean_return == pytest.approx(0.0, abs=1e-12)
    # the ledger's sealed field is read, never rewritten
    assert r["ledger"] == [r["sealed"]]


def test_a_move_across_the_split_survives_it(tmp_path: Path) -> None:
    """Not only the flat case: +20% across a 2-for-1 scores +20%, not −40%."""
    r = _scored(tmp_path, before=_Feed(100.0, 1000.0),
                after=_Feed(lambda d: 50.0 if d < SPLIT_DAY else 60.0, 2000.0),
                splits=_recorded(Split(execution_date=SPLIT_DAY, split_from=1, split_to=2)))
    (s,) = r["scores"]
    assert s.name_return == pytest.approx(0.2)


def test_with_no_split_the_sealed_price_is_used_unchanged(tmp_path: Path) -> None:
    """THE NEGATIVE PIN. The sealed 100.20 sits 0.2% off the store's 100.00 — inside the basis
    tolerance — and no split is recorded, so the return divides by the SEALED price, exactly as
    before, with no note and nothing restated."""
    r = _scored(tmp_path, before=_Feed(100.0, 1000.0),
                after=_Feed(lambda d: 100.0 if d < SPLIT_DAY else 120.0, 1000.0),
                splits=no_splits, sealed=100.2)
    assert r["summary"]["restated"] == {}
    (s,) = r["scores"]
    assert s.name_return == 120.0 / 100.2 - 1.0
    assert s.name_price_return == 120.0 / 100.2 - 1.0
    assert s.note is None and r["report"].row_notes == ()


def test_a_store_read_after_the_split_needs_no_restated_tag(tmp_path: Path) -> None:
    """A store built after the split holds the entry bar on the new basis with NO `+restated`
    tag (`write_prices` replaces the row, source included), so the tag cannot be what decides:
    the recorded split does."""
    r = _scored(tmp_path, after=_Feed(50.0, 2000.0), sealed=100.0,
                splits=_recorded(Split(execution_date=SPLIT_DAY, split_from=1, split_to=2)))
    assert _bar(r["hist"], ENTRY).source == "polygon-grouped"
    (s,) = r["scores"]
    assert s.name_return == pytest.approx(0.0, abs=1e-12)
    assert s.note is not None and "[polygon-grouped]" in s.note


def test_a_split_on_the_entry_session_is_already_in_the_sealed_price(tmp_path: Path) -> None:
    r = _scored(tmp_path, after=_Feed(50.0, 2000.0), sealed=50.0,
                splits=_recorded(Split(execution_date=ENTRY, split_from=1, split_to=2)))
    (s,) = r["scores"]
    assert s.name_return == 0.0 and s.note is None


def test_a_split_after_the_exit_restated_both_ends(tmp_path: Path) -> None:
    """A 60-day horizon (exit 2026-03-06) and a split on 04-01: the store restated the exit bar
    with the entry bar, so the two are on one basis — the split explains f all the same."""
    r = _scored(tmp_path, before=_Feed(100.0, 1000.0), after=_Feed(50.0, 2000.0),
                horizon_days=60,
                splits=_recorded(Split(execution_date=SPLIT_DAY, split_from=1, split_to=2)))
    (s,) = r["scores"]
    assert s.resolved and s.name_return == pytest.approx(0.0, abs=1e-12)


# --- scoring: what it refuses -----------------------------------------------------------------


def test_a_gap_no_recorded_split_explains_raises_once_resolved(tmp_path: Path) -> None:
    """Fail loud, never fabricate: the sealed 100 against a store close of 50 with no split
    recorded is a contradiction, not a split."""
    with pytest.raises(SplitBasisError, match="nothing explains"):
        _scored(tmp_path, after=_Feed(50.0, 2000.0), sealed=100.0, splits=no_splits)


def test_an_unresolved_contradiction_is_pending_and_named(tmp_path: Path) -> None:
    """Gated on `resolved`, as every guard here is: an interim row feeds no number, so it is held
    pending and named rather than stopping the report."""
    r = _scored(tmp_path, after=_Feed(50.0, 2000.0), sealed=100.0, splits=no_splits,
                as_of=date(2026, 5, 1))
    assert r["scores"] == [] and r["report"].n_pending == 1
    assert any("nothing explains" in n and "PENDING" in n for n in r["report"].row_notes)


def test_a_recorded_split_the_store_never_restated_raises(tmp_path: Path) -> None:
    """F-D5's cost, caught here: bars with no volume cannot show a split, so the anchor restates
    nothing and the store holds a splice — the entry at 100, the exit at 50. The recorded split
    says so, and the row is not scored on either."""
    with pytest.raises(SplitBasisError, match="not restated"):
        r = _scored(tmp_path, before=_Feed(100.0, 0.0), after=_Feed(50.0, 0.0),
                    splits=_recorded(Split(execution_date=SPLIT_DAY, split_from=1, split_to=2)))
        assert r["summary"]["restated"] == {}


def test_a_factor_that_is_not_the_recorded_split_raises(tmp_path: Path) -> None:
    with pytest.raises(SplitBasisError, match="not the recorded split"):
        _scored(tmp_path, before=_Feed(100.0, 1000.0), after=_Feed(50.0, 2000.0),
                splits=_recorded(Split(execution_date=SPLIT_DAY, split_from=1, split_to=3)))


def test_an_unreadable_reference_stops_a_resolved_row_and_holds_an_interim_one(
        tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    with pytest.raises(SplitsUnreadError, match="cannot be read"):
        _scored(tmp_path / "a", before=_Feed(100.0, 1000.0), after=_Feed(100.0, 1000.0),
                splits=_unreadable)
    r = _scored(tmp_path / "b", before=_Feed(100.0, 1000.0), after=_Feed(100.0, 1000.0),
                splits=_unreadable, as_of=date(2026, 5, 1))
    assert r["scores"] == [] and r["report"].n_pending == 1


def test_the_rule_itself_on_its_edges() -> None:
    two = Split(execution_date=SPLIT_DAY, split_from=1, split_to=2)
    kw: dict[str, Any] = {"who": "T", "session": ENTRY, "basis_through": AS_OF}
    # no close for the entry session and nothing recorded: the sealed price stands
    assert entry_on_basis(sealed=10.0, session_close=None, splits=[], **kw) == (10.0, None)
    # no close for the entry session but a split recorded: it cannot be reconciled
    with pytest.raises(SplitBasisError, match="holds no close"):
        entry_on_basis(sealed=10.0, session_close=None, splits=[two], **kw)
    # a split dated after the basis the series carries is not in it
    late = Split(execution_date=date(2026, 8, 3), split_from=1, split_to=2)
    assert entry_on_basis(sealed=10.0, session_close=10.0, splits=[late], **kw) == (10.0, None)
    # two splits compound
    px, note = entry_on_basis(sealed=10.0, session_close=2.5, splits=[two, two.model_copy(
        update={"execution_date": date(2026, 5, 1)})], **kw)
    assert px == 2.5 and note is not None and "×0.25" in note


# --- the splits reference, read off Polygon's real responses ----------------------------------


def test_parse_splits_reads_the_real_reference_responses() -> None:
    """The four ledger names' responses as Polygon served them on 2026-10-29."""
    served = json.loads(_SPLITS.read_text())
    googl = parse_splits(served["GOOGL"]["results"], symbol="GOOGL")
    assert googl == [Split(execution_date=date(2022, 7, 18), split_from=1, split_to=20)]
    assert googl[0].price_factor == pytest.approx(0.05) and googl[0].label() == (
        "20-for-1 on 2022-07-18")
    assert [s.execution_date.year for s in parse_splits(served["IT"]["results"], symbol="IT")] == [
        1996, 1995, 1994]
    assert parse_splits(served["SMPL"]["results"], symbol="SMPL") == []
    assert parse_splits(served["VRRM"]["results"], symbol="VRRM") == []
    with pytest.raises(SplitsUnknownError, match="a split for 'GOOGL'"):
        parse_splits(served["GOOGL"]["results"], symbol="IT")
    with pytest.raises(SplitsUnknownError, match="unreadable"):
        parse_splits([{"execution_date": "2022-07-18", "split_from": 1}], symbol="GOOGL")


class _Http:
    """`CachedHttp.get_json` as the splits endpoint serves it: ``pages`` in order, each a body."""

    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.pages, self.asked = pages, []

    def get_json(self, url: str, *, ttl_seconds: float | None = None,
                 params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.asked.append((url, params))
        return self.pages[len(self.asked) - 1]


def test_the_polygon_source_follows_pages_reads_once_and_fails_loud(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from vinci.eod.client import PolygonEodClient
    from vinci.eod.splits import default_splits
    from vinci.netcache import HttpError
    served = json.loads(_SPLITS.read_text())["IT"]
    http = _Http([{"status": "OK", "results": served["results"][:2], "next_url": "https://n/2"},
                  {"status": "OK", "results": served["results"][2:]}])
    client = PolygonEodClient(http, min_results=1)  # type: ignore[arg-type]
    src = default_splits(client=client)
    assert len(src("IT")) == 3 and len(src("IT")) == 3
    assert [u for u, _p in http.asked] == ["https://api.polygon.io/v3/reference/splits",
                                           "https://n/2"]          # two pages, read once
    assert http.asked[0][1] == {"ticker": "IT", "limit": 1000} and http.asked[1][1] is None
    refused = default_splits(client=PolygonEodClient(_Http([{"status": "ERROR"}]),  # type: ignore[arg-type]
                                                     min_results=1))
    with pytest.raises(SplitsUnknownError, match="request failed"):
        refused("IT")

    class _Down:
        def get_json(self, *_a: object, **_k: object) -> dict[str, Any]:
            raise HttpError("Exhausted retries")
    with pytest.raises(SplitsUnknownError, match="request failed"):
        default_splits(client=PolygonEodClient(_Down(), min_results=1))("IT")  # type: ignore[arg-type]
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    with pytest.raises(SplitsUnknownError, match="no POLYGON_API_KEY"):
        default_splits()("IT")


# --- the monitor: the real `vinci monitor` over VRRM's committed row --------------------------

_BARS = ROOT / "tests" / "fixtures" / "horizon_close" / "vrrm_iwm_bars.jsonl"
_SYM = {"SEC-0001682745-VRRM": "VRRM", "IDX-IWM": "IWM"}
_VRRM_ID = "V-VRRM-screen2-20260617"


def _vrrm_row(horizon_days: int) -> dict[str, Any]:
    for ln in (ROOT / "data/snapshots/decision_ledger.jsonl").read_text().splitlines():
        row = json.loads(ln) if ln.strip() else {}
        if row.get("entry_id") == _VRRM_ID:
            payload = json.loads(row["payload"])
            payload["horizon_days"] = horizon_days
            return {**row, "horizon_days": horizon_days, "payload": json.dumps(payload)}
    raise AssertionError(f"{_VRRM_ID} is not in the committed ledger")


def _monitor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, vrrm_scale: float,
             splits: Callable[[str], list[Split]]) -> dict[str, Any]:
    """`vinci monitor --ref 2026-10-16 --out <scratch>` over a book holding only VRRM's real row
    (horizon 119 days → resolved at 2026-10-14), its frozen Polygon bars served as grouped-daily
    days with every VRRM price × ``vrrm_scale`` — what `adjusted=true` serves after a split."""
    from vinci import cli
    book = tmp_path / "book"
    (book / "data/snapshots").mkdir(parents=True)
    (book / "data/monitor").mkdir(parents=True)
    (book / "scenarios").mkdir()
    (book / "data/snapshots/decision_ledger.jsonl").write_text(json.dumps(_vrrm_row(119)) + "\n")
    for rel in ("data/snapshots/securities.jsonl", "data/monitor/benchmark_assignments.json"):
        shutil.copy(ROOT / rel, book / rel)
    days: dict[date, dict[str, Any]] = {}
    for ln in _BARS.read_text().splitlines():
        r = json.loads(ln)
        sym = _SYM[r["internal_id"]]
        close = float(r["close"]) * (vrrm_scale if sym == "VRRM" else 1.0)
        days.setdefault(date.fromisoformat(r["bar_date"]), {})[sym] = SimpleNamespace(close=close)

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
    monkeypatch.setattr(cli, "default_splits", lambda *_a, **_k: splits)
    scratch = tmp_path / "scratch"
    assert cli._cmd_monitor(argparse.Namespace(ref="2026-10-16", out=str(scratch))) == 0
    (day,) = [json.loads(p.read_text()) for p in (scratch / "data/monitor").glob("*.json")]
    (row,) = day["rows"]
    return {**row, "_day": day}


_VRRM_2_FOR_1 = Split(execution_date=date(2026, 9, 1), split_from=1, split_to=2)


def test_the_monitor_marks_a_split_leg_on_one_basis(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """On main this row marked VRRM's real AVOID leg at the halved close over the sealed $4.71 —
    every return ~−50% points too low — and the day said nothing about a split."""
    plain = _monitor(tmp_path / "plain", monkeypatch, vrrm_scale=1.0, splits=no_splits)
    split = _monitor(tmp_path / "split", monkeypatch, vrrm_scale=0.5,
                     splits=lambda s: [_VRRM_2_FOR_1] if s == "VRRM" else [])
    assert split["resolved"] and split["current_date"] == plain["current_date"] == "2026-10-14"
    assert split["position_return"] == pytest.approx(plain["position_return"], abs=1e-12)
    assert split["excess"] == pytest.approx(plain["excess"], abs=1e-12)
    assert split["position_price_return"] == pytest.approx(plain["position_price_return"],
                                                           abs=1e-12)
    assert split["_day"]["spread"]["avoid_mean_excess"] == pytest.approx(
        plain["_day"]["spread"]["avoid_mean_excess"], abs=1e-12)
    # the row's entry is on the mark's basis, and the day names the sealed price and the split
    assert split["entry_price"] == pytest.approx(4.71 * 0.5)
    notes = [n for n in split["_day"]["notes"] if "ON ONE SPLIT BASIS" in n]
    assert len(notes) == 1 and _VRRM_2_FOR_1.label() in notes[0] and "4.71" in notes[0]
    # THE NEGATIVE PIN: no split, the sealed price as before, and no split note
    assert plain["entry_price"] == 4.71
    assert not [n for n in plain["_day"]["notes"] if "SPLIT BASIS" in n]


def test_the_monitor_refuses_a_basis_gap_nothing_explains(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SplitBasisError, match="nothing explains"):
        _monitor(tmp_path, monkeypatch, vrrm_scale=0.5, splits=no_splits)


def test_the_monitor_refuses_an_unreadable_reference(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(RuntimeError, match="splits UNKNOWN"):
        _monitor(tmp_path, monkeypatch, vrrm_scale=1.0, splits=_unreadable)


# --- close-position and the realized view, over a copy of the committed ledger ----------------

_OPEN = "SMPL-screen2-20260729"          # SMPL's open decision: sealed $11.33 on 2026-08-04
_SMPL_2_FOR_1 = Split(execution_date=date(2026, 9, 1), split_from=1, split_to=2)


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


def _close(tree: Config, monkeypatch: pytest.MonkeyPatch, splits: Callable[[str], list[Split]],
           exit_price: float) -> int:
    from vinci import cli
    monkeypatch.setattr(cli, "get_config", lambda: tree)
    monkeypatch.setattr(cli, "default_splits", lambda *_a, **_k: splits)
    return cli._cmd_close_position(argparse.Namespace(
        candidate_id=_OPEN, exit_price=exit_price, as_of="2026-10-01",
        reason="constructed: closed after a 2-for-1 at the post-split quote"))


def _rows(tree: Config) -> list[dict[str, Any]]:
    path = tree.snapshots_dir / "decision_ledger.jsonl"
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def test_close_position_across_a_split_reports_the_economics(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Sealed $11.33, a 2-for-1, closed at the post-split $5.665: flat. On main the command
    printed −50.00% realized, and `pair_closes` derived −0.5000."""
    splits = lambda s: [_SMPL_2_FOR_1] if s == "SMPL" else []  # noqa: E731
    assert _close(tree, monkeypatch, splits, 5.665) == 0
    out = capsys.readouterr().out
    assert "= +0.00% realized" in out and "ON ONE SPLIT BASIS" in out
    assert _SMPL_2_FOR_1.label() in out
    (smpl,) = [r for r in pair_closes(_rows(tree), splits=splits)
               if r["entry_id"] == "V-SMPL-screen2-20260729"]
    assert smpl["realized_return"] == pytest.approx(0.0, abs=1e-12)
    assert smpl["entry_price"] == pytest.approx(11.33 * 0.5)
    assert smpl["split_note"] is not None and "11.33" in smpl["split_note"]
    # the close row stores the facts as typed, the sealed entry copied unchanged
    (close,) = [p for r in _rows(tree) if (p := json.loads(r["payload"])).get("event")
                and p["closes_entry_id"] == "V-SMPL-screen2-20260729"]
    assert (close["entry_price"], close["exit_price"]) == (11.33, 5.665)


def test_close_position_with_no_split_is_unchanged(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """THE NEGATIVE PIN, on the committed closes too: IT's and SMPL's realized returns are the
    two-price ratios they always were."""
    assert _close(tree, monkeypatch, no_splits, 10.86) == 0
    assert f"= {10.86 / 11.33 - 1:+.2%} realized" in capsys.readouterr().out
    by_id = {r["entry_id"]: r for r in pair_closes(_rows(tree), splits=no_splits)}
    assert by_id["V-SMPL-screen2-20260729"]["realized_return"] == 10.86 / 11.33 - 1.0
    assert by_id["V-IT-screen2-20260706"]["realized_return"] == 0.0
    assert by_id["V-SMPL-screen2-20260706"]["realized_return"] == 10.53 / 10.92 - 1.0
    assert all(r["split_note"] is None for r in by_id.values())


def test_close_position_refuses_when_the_reference_cannot_be_read(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    before = _rows(tree)
    assert _close(tree, monkeypatch, _unreadable, 5.665) == 1
    assert "REFUSED" in capsys.readouterr().out
    assert _rows(tree) == before


# --- F-D5: a split needs its volume ------------------------------------------------------------


def _held(px: float, vol: float) -> PriceBar:
    return PriceBar(internal_id="SEC-X", bar_date=date(2026, 8, 5), open=px, high=px * 1.01,
                    low=px * 0.99, close=px, volume=vol, source="polygon-grouped")


@pytest.mark.parametrize("fresh, expect", [
    (_raw("X", 10.4, 5000.0), None),            # a one-print correction of 1.04: prices only
    (_raw("X", 5.0, 10_000.0), 0.5),            # a 2-for-1: volume doubles
    (_raw("X", 100.0, 500.0), 10.0),            # a 1-for-10: volume a tenth
    (_raw("X", 5.0, 5000.0), None),             # prices halved, volume unmoved: not a split
    (_raw("X", 5.0, 2500.0), None),             # volume moved the WRONG way
], ids=["correction-1.04", "2-for-1", "1-for-10", "volume-unmoved", "volume-wrong-way"])
def test_a_split_needs_volume_to_move_inversely(fresh: RawBar, expect: float | None) -> None:
    got = restatement_factor(_held(10.0, 5000.0), fresh)
    assert got == (pytest.approx(expect) if expect is not None else None)


def test_a_bar_with_no_volume_cannot_show_a_split() -> None:
    assert restatement_factor(_held(10.0, 0.0), _raw("X", 5.0, 0.0)) is None


def test_a_corrected_anchor_bar_restates_nothing_through_ingest(tmp_path: Path) -> None:
    """End to end: the source corrects the anchor session by 1.04 and serves every other session
    as held. On main the anchor read it as a split and rescaled the whole held history by 1.04."""
    with Store(tmp_path / "fix.db") as store:
        ingest_prices(_Feed(100.0, 1000.0), store, [X, IWM], start=ENTRY, end=FIRST_PULL_END)
        summary = ingest_prices(
            _Feed(lambda d: 104.0 if d == FIRST_PULL_END else 100.0, 1000.0), store, [X, IWM],
            start=ENTRY, end=AS_OF)
        hist = store.get_price_history(X.internal_id)
    assert summary["anchor"] == FIRST_PULL_END.isoformat() and summary["restated"] == {}
    assert all(b.close == 100.0 and b.source == "polygon-grouped"
               for b in hist if b.bar_date < FIRST_PULL_END)


def test_every_real_restatement_of_2026_08_05_still_restates() -> None:
    """CORPUS BEFORE SYNTHETIC. The ten names `restate-prices` restated in the primary store on
    2026-10-28 (record 2026-10-28-primary-store-restated-to-polygons-basis), each as the store held
    its 2026-08-05 bar before and as Polygon served it after: the volume rule restates every one,
    by the same factor the price rule alone read."""
    pairs = json.loads(_RESTATED.read_text())["pairs"]
    assert len(pairs) == 10
    for p in pairs:
        held = PriceBar(internal_id=p["ticker"], bar_date=date(2026, 8, 5), source="t",
                        **p["held"])
        got = restatement_factor(held, RawBar(ticker=p["ticker"], **p["fresh"]))
        assert got == pytest.approx(p["factor"], rel=1e-6), p["ticker"]


# --- F-D3: dividend coverage against the market's sessions -------------------------------------


def _tiingo_row(d: date, cash: float = 0.0) -> dict[str, Any]:
    return {"date": f"{d.isoformat()}T00:00:00.000Z", "close": 50.0, "divCash": cash,
            "splitFactor": 1.0}


_A, _B, _EX = date(2026, 1, 5), date(2026, 3, 6), date(2026, 2, 11)   # the ex-date: a Wednesday


def test_a_missing_ex_date_row_is_unknown_not_zero() -> None:
    """On main this window returned [] — the 2-day hole is shorter than a holiday weekend, so the
    gap rule passed it, and the dividend paid on 02-11 was silently zero."""
    rows = [_tiingo_row(d) for d in weekday_sessions(_A, _B) if d != _EX]
    with pytest.raises(DividendsUnknownError, match="no row for 1 market session"):
        ex_date_yields(rows, _A, _B, sessions=weekday_sessions(_A, _B), symbol="PAY")


def test_a_market_holiday_is_not_a_missing_session() -> None:
    """THE NEGATIVE PIN: the calendar has no session on a holiday, so no row is owed there."""
    holiday = date(2026, 2, 16)
    rows = [_tiingo_row(d, 0.5 if d == _EX else 0.0) for d in weekday_sessions(_A, _B)
            if d != holiday]
    sessions = [d for d in weekday_sessions(_A, _B) if d != holiday]
    assert ex_date_yields(rows, _A, _B, sessions=sessions) == [(_EX, pytest.approx(0.01))]


def test_the_tiingo_source_reads_the_calendar_once_for_its_span() -> None:
    asked: list[tuple[date, date]] = []

    def calendar(a: date, b: date) -> list[date]:
        asked.append((a, b))
        return weekday_sessions(a, b)

    class _Client:
        def daily_rows(self, symbol: str, *, start: date, end: date) -> list[dict[str, Any]]:
            return [_tiingo_row(d) for d in weekday_sessions(start, end) if d != _EX]

    src = tiingo_dividends(_Client(), start=_A, end=_B, sessions=calendar)  # type: ignore[arg-type]
    assert src("PAY", _A, date(2026, 2, 10)) == []          # a window before the hole reads
    with pytest.raises(DividendsUnknownError, match="first 2026-02-11"):
        src("PAY", _A, _B)
    assert asked == [(_A, _B)]
