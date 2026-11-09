"""A SPLIT IS CONFIRMED ON TWO VENDORS' RECORDS, OR NO RETURN IS READ ACROSS IT (TeamNostra fix
request 2: RF-D1 and RF-D2, 2026-11-09).

THE DEFECTS, reproduced on main 7c87164a before the fix — the real scoring, `vinci monitor --out`
and `close-position` paths, every vendor faked at `CachedHttp.get_json`:

- RF-D1. A 2-for-1 that Polygon reports late on BOTH feeds — its bars served as traded (100, then
  50) and never restated, its splits reference silent — scored −0.5000, RESOLVED, with no note; the
  basket read −0.5 and the monitor marked −0.5000. The sealed 100 equals the store's unrestated
  entry close, so `entry_on_basis` saw f = 1 and no recorded split, and passed it.
- RF-D2. With the reference late alone, `close-position` printed "−50.00% realized" and appended
  the close: `close_on_basis` scaled the sealed entry by the reference's splits and nothing else.

THE FIX (`vinci.eod.splits.ConfirmedSplits`). Tiingo's daily rows carry ``splitFactor`` on the
execution date — measured on GOOGL's real rows: 20.0 on 2022-07-18, the date Polygon records. Every
production split source is now Polygon's reference CONFIRMED by those rows over the span the run
reads: the two must record the same splits on the same dates, or the symbol's record raises
`SplitsUnconfirmedError`. It is a `SplitsUnknownError`, so every surface that already refused an
unread reference refuses it: scoring (resolved → `SplitsUnreadError`; interim → pending, named),
the basket (refused, with the reason), the monitor (stops) and close-position (refused, nothing
written). A ratio of two STORED closes — a benchmark, a basket member — has no sealed price to hold
the store against, so across a confirmed split it is held against Tiingo's unadjusted close
(`leg_on_basis`), and refused when that does not show the store restated.

WHAT IT CANNOT SEE: a split no vendor records. Both Polygon feeds and Tiingo late together leave
nothing to confirm against; the store's step is then the only trace, and the price scorecard
(`quality.sources.prices`) is what flags it.
"""
from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tests.dividend_support import no_dividends, weekday_calendar, weekday_sessions
from vinci.config import Config
from vinci.eod.client import EodClient, PolygonEodClient, RawBar, ingest_prices
from vinci.eod.splits import (
    ConfirmedSplits,
    Split,
    SplitBasisError,
    SplitsUnconfirmedError,
    SplitsUnknownError,
    default_splits,
    leg_on_basis,
    parse_splits,
    tiingo_split_record,
)
from vinci.netcache import HttpError
from vinci.schemas.data_record import Identity
from vinci.schemas.ledger import Confidence, LedgerEntry, Verdict
from vinci.scoring import score_ledger
from vinci.scoring.baseline import Basket, basket_return
from vinci.scoring.harness import SplitsUnreadError
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
_FIX = ROOT / "tests" / "fixtures" / "splits_reference"

X = Identity(internal_id="SEC-0000000009-SPLT", issuer_id="ISS-0000000009", cik="0000000009",
             ticker="SPLT", mic="XNAS", exchange="Nasdaq", eod_symbol="SPLT", name="Split Test Co")
IWM = Identity(internal_id="IDX-IWM", issuer_id="IDX", cik="", ticker="IWM", mic="ARCX",
               exchange="ETF", eod_symbol="IWM", name="IWM")

ENTRY = date(2026, 1, 5)              # a Monday
SPLIT_DAY = date(2026, 4, 1)
AS_OF = date(2026, 7, 10)             # 180 days from ENTRY is Saturday 07-04: exit Friday 07-03
INTERIM = date(2026, 5, 1)
TWO_FOR_ONE = Split(execution_date=SPLIT_DAY, split_from=1, split_to=2)


# --- the vendors, served as they serve ----------------------------------------------------------


def _raw(sym: str, px: float, vol: float) -> RawBar:
    return RawBar(ticker=sym, open=px, high=px, low=px, close=px, volume=vol)


class _Feed(EodClient):
    """Grouped-daily on the day of the pull. ``restated``: every day on the post-split basis, as
    `adjusted=true` serves once Polygon has restated; otherwise the bars as traded (the RF-D1 lag:
    100 before the split, 50 after, nothing restated)."""

    def __init__(self, *, split: bool, restated: bool) -> None:
        self.split, self.restated = split, restated

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        if day.weekday() >= 5:
            return {}
        if not self.split:
            px, vol = 100.0, 1000.0
        elif self.restated or day >= SPLIT_DAY:
            px, vol = 50.0, 2000.0
        else:
            px, vol = 100.0, 1000.0
        return {"SPLT": _raw("SPLT", px, vol), "IWM": _raw("IWM", 200.0, 1e6)}


def _tiingo_row(d: date, close: float, factor: float = 1.0, cash: float = 0.0) -> dict[str, Any]:
    """A Tiingo daily row in the served field set (`fixtures/splits_reference/
    tiingo_googl_2022-07.json`): the UNADJUSTED close as traded, ``splitFactor`` on the
    execution date."""
    return {"date": f"{d.isoformat()}T00:00:00.000Z", "close": close, "high": close,
            "low": close, "open": close, "volume": 1000, "adjClose": close, "adjHigh": close,
            "adjLow": close, "adjOpen": close, "adjVolume": 1000, "divCash": cash,
            "splitFactor": factor}


class _Tiingo:
    """`TiingoEodClient.daily_rows` for SPLT (as traded; ``factor`` on SPLIT_DAY when ``split``)
    and IWM (flat). ``lost`` drops rows Tiingo did not serve."""

    def __init__(self, *, split: bool, lost: frozenset[date] = frozenset()) -> None:
        self.split, self.lost, self.asked = split, lost, []

    def daily_rows(self, symbol: str, *, start: date, end: date,
                   ttl_seconds: float | None = 86_400.0) -> list[dict[str, Any]]:
        self.asked.append((symbol, start, end))
        out = []
        for d in weekday_sessions(start, end):
            if d in self.lost:
                continue
            if symbol.lower() == "iwm":
                out.append(_tiingo_row(d, 200.0))
            elif not self.split:
                out.append(_tiingo_row(d, 100.0))
            else:
                out.append(_tiingo_row(d, 100.0 if d < SPLIT_DAY else 50.0,
                                       2.0 if d == SPLIT_DAY else 1.0))
        return out


class _Reference:
    """`CachedHttp.get_json` as Polygon's splits endpoint serves it, per ticker."""

    def __init__(self, by_ticker: dict[str, list[Split]]) -> None:
        self.by_ticker = by_ticker

    def get_json(self, url: str, *, ttl_seconds: float | None = None,
                 params: dict[str, Any] | None = None) -> dict[str, Any]:
        sym = str((params or {}).get("ticker"))
        return {"status": "OK", "results": [
            {"execution_date": s.execution_date.isoformat(), "split_from": s.split_from,
             "split_to": s.split_to, "ticker": sym} for s in self.by_ticker.get(sym, [])]}


def _source(*, reference: list[Split], tiingo: _Tiingo, start: date = ENTRY,
            end: date = AS_OF) -> Callable[[str], list[Split]]:
    """THE PRODUCTION SOURCE (`default_splits`), on the two vendors' clients."""
    client = PolygonEodClient(_Reference({"SPLT": reference}), min_results=1)  # type: ignore[arg-type]
    return default_splits(client=client, tiingo=tiingo,  # type: ignore[arg-type]
                          start=start, end=end, sessions=weekday_calendar)


def _scored(tmp_path: Path, *, feed: _Feed, splits: Callable[[str], list[Split]],
            sealed: float = 100.0, as_of: date = AS_OF) -> dict[str, Any]:
    with Store(tmp_path / "split.db") as store:
        store.append_ledger(LedgerEntry(
            entry_id="V-SPLT", candidate_id="SPLT-c", internal_id=X.internal_id, ticker="SPLT",
            verdict=Verdict.BUY, twin_call="t", entry_price=sealed, entry_price_as_of=ENTRY,
            thesis="t", kill_criteria="k", horizon_days=180,
            confidence=Confidence.MEDIUM, decided_at=datetime(2026, 1, 5)))
        ingest_prices(feed, store, [X, IWM], start=ENTRY, end=as_of)
        hist = store.get_price_history(X.internal_id)
        scores, report = score_ledger(store, as_of=as_of, dividends=no_dividends, splits=splits)
    return {"scores": scores, "report": report, "hist": hist}


# --- the second record, read off Tiingo's real rows ---------------------------------------------


def test_tiingo_records_googls_split_where_polygon_does() -> None:
    """GOOGL's 20-for-1, as each vendor served it: Tiingo's ``splitFactor`` 20.0 on 2022-07-18
    (read 2026-11-09) and Polygon's reference row (read 2026-10-29). One split, one date, one
    ratio — the agreement the confirmation rests on."""
    rows = json.loads((_FIX / "tiingo_googl_2022-07.json").read_text())["rows"]
    days = [date.fromisoformat(r["date"][:10]) for r in rows]
    tiingo = tiingo_split_record(rows, start=date(2022, 7, 13), end=date(2022, 7, 20),
                                 sessions=days, symbol="GOOGL")
    polygon = parse_splits(json.loads((_FIX / "ledger_names.json").read_text())["GOOGL"]["results"],
                           symbol="GOOGL")
    assert tiingo == polygon == [Split(execution_date=date(2022, 7, 18), split_from=1,
                                       split_to=20)]
    # THE NEGATIVE PIN: the same rows with the split day outside the window record nothing
    assert tiingo_split_record(rows, start=date(2022, 7, 18), end=date(2022, 7, 20),
                               sessions=days, symbol="GOOGL") == []


def test_a_reverse_split_reads_the_right_way_up() -> None:
    rows = [_tiingo_row(date(2026, 3, 31), 1.0), _tiingo_row(SPLIT_DAY, 10.0, factor=0.1)]
    (s,) = tiingo_split_record(rows, start=date(2026, 3, 31), end=SPLIT_DAY,
                               sessions=[date(2026, 3, 31), SPLIT_DAY], symbol="RVS")
    assert s.execution_date == SPLIT_DAY and s.price_factor == pytest.approx(10.0)


def test_a_session_tiingo_did_not_serve_is_unknown_never_no_split() -> None:
    """A split on a row Tiingo lost would read as no split: the record is UNKNOWN instead."""
    rows = [_tiingo_row(d, 100.0) for d in weekday_sessions(ENTRY, AS_OF) if d != SPLIT_DAY]
    with pytest.raises(SplitsUnknownError, match="no row for 1 session"):
        tiingo_split_record(rows, start=ENTRY, end=AS_OF,
                            sessions=weekday_sessions(ENTRY, AS_OF), symbol="SPLT")
    with pytest.raises(SplitsUnknownError, match="splitFactor"):
        tiingo_split_record([{**_tiingo_row(ENTRY, 100.0), "splitFactor": None}], start=ENTRY,
                            end=ENTRY, sessions=[ENTRY], symbol="SPLT")


# --- RF-D1: scoring --------------------------------------------------------------------------


def test_a_split_late_on_both_polygon_feeds_stops_a_resolved_row(tmp_path: Path) -> None:
    """RF-D1. On main: −0.5000, resolved, no note. Tiingo records the 2-for-1 the reference does
    not, so the record is unconfirmed and the row is not scored."""
    with pytest.raises(SplitsUnreadError, match="cannot be confirmed") as err:
        _scored(tmp_path, feed=_Feed(split=True, restated=False),
                splits=_source(reference=[], tiingo=_Tiingo(split=True)))
    assert TWO_FOR_ONE.label() in str(err.value) and "Tiingo" in str(err.value)


def test_an_interim_row_across_an_unconfirmed_split_is_pending_and_named(tmp_path: Path) -> None:
    r = _scored(tmp_path, feed=_Feed(split=True, restated=False), as_of=INTERIM,
                splits=_source(reference=[], tiingo=_Tiingo(split=True), end=INTERIM))
    assert r["scores"] == [] and r["report"].n_pending == 1
    (note,) = r["report"].row_notes
    assert "PENDING" in note and "cannot be confirmed" in note and TWO_FOR_ONE.label() in note


def test_a_split_only_the_reference_records_is_unconfirmed_too(tmp_path: Path) -> None:
    """The other way round: the reference lists a split Tiingo's rows do not. A split one vendor
    alone records is not confirmed."""
    with pytest.raises(SplitsUnreadError, match="cannot be confirmed"):
        _scored(tmp_path, feed=_Feed(split=True, restated=True),
                splits=_source(reference=[TWO_FOR_ONE], tiingo=_Tiingo(split=False)))


def test_a_split_both_vendors_record_scores_the_economics(tmp_path: Path) -> None:
    """THE CONTROL: everything on time — the store restated, both records agree — scores 0.0
    with the split named, exactly as before the fix."""
    r = _scored(tmp_path, feed=_Feed(split=True, restated=True),
                splits=_source(reference=[TWO_FOR_ONE], tiingo=_Tiingo(split=True)))
    (s,) = r["scores"]
    assert s.resolved and s.name_return == pytest.approx(0.0, abs=1e-12)
    assert s.note is not None and "ON ONE SPLIT BASIS" in s.note and TWO_FOR_ONE.label() in s.note


def test_with_no_split_on_either_record_nothing_changes(tmp_path: Path) -> None:
    """THE NEGATIVE PIN: no split anywhere — the sealed price, no note, both vendors read."""
    tiingo = _Tiingo(split=False)
    r = _scored(tmp_path, feed=_Feed(split=False, restated=False),
                splits=_source(reference=[], tiingo=tiingo))
    (s,) = r["scores"]
    assert s.resolved and s.name_return == 0.0 and s.note is None
    assert r["report"].row_notes == ()
    assert {sym for sym, _a, _b in tiingo.asked} == {"SPLT", "IWM"}   # name and benchmark legs


def test_each_symbol_is_read_once_on_the_span_the_dividends_read() -> None:
    """One Tiingo request per symbol, on the span `default_dividends` asks for — so the rows are
    the cached ones the dividend read already fetched, and no lookup is added to the plan's cap."""
    tiingo = _Tiingo(split=False)
    src = _source(reference=[], tiingo=tiingo)
    assert src("SPLT") == [] and src("SPLT") == []
    assert tiingo.asked == [("SPLT", ENTRY - timedelta(days=7), AS_OF)]


def test_a_failed_read_is_read_once_too() -> None:
    """Every row sharing a benchmark asks for it: a failed read is kept, as `tiingo_dividends`
    keeps one, so the vendors are not re-asked (retries and pacing included) per row."""
    asked: list[str] = []

    def rows(symbol: str) -> list[dict[str, Any]]:
        asked.append(symbol)
        raise HttpError("Tiingo 503")
    src = ConfirmedSplits(lambda s: [], rows, start=ENTRY, end=AS_OF, sessions=weekday_calendar)
    for _ in range(3):
        with pytest.raises(SplitsUnknownError, match="Tiingo request failed"):
            src("IWM")
    assert asked == ["IWM"]


def test_without_a_tiingo_key_the_record_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    client = PolygonEodClient(_Reference({}), min_results=1)  # type: ignore[arg-type]
    src = default_splits(client=client, start=ENTRY, end=AS_OF, sessions=weekday_calendar)
    with pytest.raises(SplitsUnknownError, match="no TIINGO_API_KEY"):
        src("SPLT")


# --- RF-D1: the basket and the benchmark — ratios of two stored closes -------------------------


def _basket_bars(tmp_path: Path, feed: _Feed) -> dict[str, Any]:
    with Store(tmp_path / "b.db") as store:
        ingest_prices(feed, store, [X, IWM], start=ENTRY, end=AS_OF)
        return {"SPLT": store.get_price_history(X.internal_id)}


def _basket() -> Basket:
    from vinci.followed import FollowRecord
    return Basket("overshoot", (FollowRecord("SPLT", "overshoot", date(2025, 12, 1)),),
                  {"SPLT": X.internal_id})


def test_the_basket_refuses_a_member_whose_split_is_unconfirmed(tmp_path: Path) -> None:
    """RF-D1's basket: on main −0.5 for a flat member. Refused, with the member's record named."""
    got, note, members = basket_return(
        _basket(), _basket_bars(tmp_path, _Feed(split=True, restated=False)), ENTRY,
        date(2026, 7, 3), dividends=no_dividends,
        splits=_source(reference=[], tiingo=_Tiingo(split=True)))
    assert got is None and members == ("SPLT",)
    assert note is not None and "cannot be confirmed" in note and TWO_FOR_ONE.label() in note


def test_a_basket_member_restated_for_a_confirmed_split_is_priced(tmp_path: Path) -> None:
    got, note, _m = basket_return(
        _basket(), _basket_bars(tmp_path, _Feed(split=True, restated=True)), ENTRY,
        date(2026, 7, 3), dividends=no_dividends,
        splits=_source(reference=[TWO_FOR_ONE], tiingo=_Tiingo(split=True)))
    assert note is None and got == pytest.approx(0.0, abs=1e-12)


def test_a_stored_ratio_across_a_confirmed_split_is_held_to_tiingos_close() -> None:
    """`leg_on_basis`: the store's entry close beside Tiingo's unadjusted close for the same
    session. Restated (×0.5, the split) → read, with a note; unrestated (×1) → refused; a source
    with no second vendor's close → refused, never priced unconfirmed."""
    src = _source(reference=[TWO_FOR_ONE], tiingo=_Tiingo(split=True))
    assert isinstance(src, ConfirmedSplits)
    kw: dict[str, Any] = {"who": "IWM leg", "symbol": "SPLT", "start": ENTRY, "end": AS_OF,
                          "basis_through": AS_OF, "splits": src}
    note = leg_on_basis(start_close=50.0, **kw)
    assert note is not None and "ON ONE SPLIT BASIS" in note and TWO_FOR_ONE.label() in note
    with pytest.raises(SplitBasisError, match="not restated"):
        leg_on_basis(start_close=100.0, **kw)
    with pytest.raises(SplitBasisError, match="no second vendor"):
        leg_on_basis(**{**kw, "splits": lambda _s: [TWO_FOR_ONE]}, start_close=50.0)
    # no split inside the window: nothing to confirm, the stored ratio stands as before
    assert leg_on_basis(**{**kw, "end": date(2026, 3, 31), "basis_through": date(2026, 3, 31)},
                        start_close=100.0) is None


# --- RF-D1: the monitor --------------------------------------------------------------------------


_SMPL_SPLIT = Split(execution_date=date(2026, 9, 1), split_from=1, split_to=2)


class _Polygon:
    """`PolygonEodClient` for the CLI: grouped-daily days, per-symbol sessions, and the splits
    reference per symbol — what `vinci monitor` and `close-position` ask Polygon."""

    def __init__(self, days: dict[date, dict[str, Any]], reference: dict[str, list[Split]]) -> None:
        self.days, self.reference = days, reference

    def grouped_daily(self, d: date) -> dict[str, Any]:
        return dict(self.days.get(d, {}))

    def daily_bars(self, symbol: str, a: date, b: date) -> list[tuple[date, Any]]:
        return [(d, None) for d in weekday_sessions(a, b)]

    def splits_reference(self, symbol: str) -> list[dict[str, Any]]:
        return [{"execution_date": s.execution_date.isoformat(), "split_from": s.split_from,
                 "split_to": s.split_to, "ticker": symbol} for s in self.reference.get(symbol, [])]


class _TiingoFor:
    """Tiingo for a committed ledger name: flat, with a 2-for-1 on ``split_on`` (None: none)."""

    def __init__(self, name: str, close: float, split_on: date | None) -> None:
        self.name, self.close, self.split_on = name, close, split_on

    def daily_rows(self, symbol: str, *, start: date, end: date,
                   ttl_seconds: float | None = 86_400.0) -> list[dict[str, Any]]:
        out = []
        for d in weekday_sessions(start, end):
            if symbol.upper() != self.name:
                out.append(_tiingo_row(d, 200.0))
                continue
            after = self.split_on is not None and d >= self.split_on
            out.append(_tiingo_row(d, self.close / 2 if after else self.close,
                                   2.0 if d == self.split_on else 1.0))
        return out


def _vendors(monkeypatch: pytest.MonkeyPatch, polygon: _Polygon, tiingo: _TiingoFor) -> None:
    """Fake the vendors at their clients, so the CLI's own `default_splits` wiring runs."""
    from vinci import cli
    from vinci.eod import splits as sp
    monkeypatch.setenv("POLYGON_API_KEY", "fake-not-a-key")
    monkeypatch.setenv("TIINGO_API_KEY", "fake-not-a-key")
    monkeypatch.setattr(cli.PolygonEodClient, "from_config",
                        classmethod(lambda _c, _cfg=None: polygon))
    monkeypatch.setattr(sp.TiingoEodClient, "from_config",
                        classmethod(lambda _c, _cfg=None: tiingo))
    monkeypatch.setattr(cli, "default_dividends", lambda **_kw: no_dividends)


_VRRM_ID = "V-VRRM-screen2-20260617"


def _monitor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, scale_after: float,
             reference: list[Split], split_on: date | None) -> int:
    """`vinci monitor --ref 2026-10-16 --out <scratch>` over VRRM's committed row and its frozen
    bars, every VRRM close from ``split_on`` on × ``scale_after`` (Polygon serving the post-split
    sessions, the earlier ones never restated)."""
    from vinci import cli
    book = tmp_path / "book"
    (book / "data/snapshots").mkdir(parents=True)
    (book / "data/monitor").mkdir(parents=True)
    (book / "scenarios").mkdir()
    for ln in (ROOT / "data/snapshots/decision_ledger.jsonl").read_text().splitlines():
        if ln.strip() and json.loads(ln).get("entry_id") == _VRRM_ID:
            (book / "data/snapshots/decision_ledger.jsonl").write_text(ln + "\n")
    for rel in ("data/snapshots/securities.jsonl", "data/monitor/benchmark_assignments.json"):
        shutil.copy(ROOT / rel, book / rel)
    sym = {"SEC-0001682745-VRRM": "VRRM", "IDX-IWM": "IWM"}
    days: dict[date, dict[str, Any]] = {}
    for ln in (ROOT / "tests/fixtures/horizon_close/vrrm_iwm_bars.jsonl").read_text().splitlines():
        r = json.loads(ln)
        d, s = date.fromisoformat(r["bar_date"]), sym[r["internal_id"]]
        late = s == "VRRM" and split_on is not None and d >= split_on
        days.setdefault(d, {})[s] = SimpleNamespace(
            close=float(r["close"]) * (scale_after if late else 1.0))

    class _Edgar:
        @classmethod
        def from_config(cls, _cfg: object) -> _Edgar:
            return cls()

        def recent_filings(self, *_a: object, **_k: object) -> list[object]:
            return []

    monkeypatch.chdir(book)
    _vendors(monkeypatch, _Polygon(days, {"VRRM": reference}),
             _TiingoFor("VRRM", 4.71, split_on))
    monkeypatch.setattr(cli, "EdgarClient", _Edgar)
    return cli._cmd_monitor(argparse.Namespace(ref="2026-10-16", out=str(tmp_path / "scratch")))


def test_the_monitor_stops_on_a_split_only_tiingo_records(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """RF-D1's monitor: VRRM's real row, a 2-for-1 on 2026-09-01 that Polygon's bars and
    reference both missed. On main this marked the leg off the halved closes over the sealed
    $4.71, with no note."""
    with pytest.raises(RuntimeError, match="UNCONFIRMED"):
        _monitor(tmp_path, monkeypatch, scale_after=0.5, reference=[], split_on=date(2026, 9, 1))


def test_the_monitor_with_no_split_on_either_record_marks_as_before(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert _monitor(tmp_path, monkeypatch, scale_after=1.0, reference=[], split_on=None) == 0


# --- RF-D2: close-position -----------------------------------------------------------------------


_OPEN = "SMPL-screen2-20260729"          # SMPL's open decision: sealed $11.33 on 2026-08-04


@pytest.fixture
def tree(tmp_path: Path) -> Config:
    """A COPY of the committed snapshot tree."""
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


def _close(tree: Config, monkeypatch: pytest.MonkeyPatch, *, reference: list[Split],
           split_on: date | None, exit_price: float) -> int:
    from vinci import cli
    monkeypatch.setattr(cli, "get_config", lambda: tree)
    _vendors(monkeypatch, _Polygon({}, {"SMPL": reference}), _TiingoFor("SMPL", 11.33, split_on))
    return cli._cmd_close_position(argparse.Namespace(
        candidate_id=_OPEN, exit_price=exit_price, as_of="2026-10-01",
        reason="constructed: closed after a 2-for-1 at the post-split quote"))


def test_close_position_refuses_a_split_the_reference_does_not_record(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """RF-D2. On main: "= -50.00% realized", and the close appended. Tiingo records the 2-for-1
    the reference does not, so the close is refused and nothing is written."""
    before = _rows(tree)
    assert _close(tree, monkeypatch, reference=[], split_on=_SMPL_SPLIT.execution_date,
                  exit_price=5.665) == 1
    out = capsys.readouterr().out
    assert "REFUSED" in out and _SMPL_SPLIT.label() in out and "realized" not in out.split(
        "REFUSED")[0]
    assert _rows(tree) == before


def test_close_position_across_a_confirmed_split_reports_the_economics(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """THE CONTROL: both records hold the split — flat, with the split named."""
    assert _close(tree, monkeypatch, reference=[_SMPL_SPLIT], split_on=_SMPL_SPLIT.execution_date,
                  exit_price=5.665) == 0
    out = capsys.readouterr().out
    assert "+0.00% realized" in out and "ON ONE SPLIT BASIS" in out


def test_close_position_with_no_split_on_either_record_is_unchanged(
        tree: Config, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    assert _close(tree, monkeypatch, reference=[], split_on=None, exit_price=10.86) == 0
    assert f"{10.86 / 11.33 - 1:+.2%} realized" in capsys.readouterr().out


def test_an_unconfirmed_record_is_an_unknown_one_for_every_caller() -> None:
    """Why no caller needed a new `except`: the disagreement IS an unknown record."""
    assert issubclass(SplitsUnconfirmedError, SplitsUnknownError)


# --- review round 0: Tiingo posts a session after Polygon does ---------------------------------


def test_tiingo_a_session_behind_the_calendar_is_no_hole() -> None:
    """Polygon has posted the newest session and Tiingo has not yet: on the whole-span reading
    every symbol was unknown, and a resolved row whose window ended months earlier stopped the
    run. Tiingo's record is read through the last day it served, within a market closure."""
    newest = date(2026, 7, 10)
    tiingo = _Tiingo(split=False, lost=frozenset({newest}))
    assert _source(reference=[], tiingo=tiingo, end=newest)("SPLT") == []


def test_a_split_the_reference_records_after_tiingos_last_row_is_unconfirmed() -> None:
    """...but a split the reference records on the session Tiingo has not served has nothing to
    confirm it — refused, as any split one vendor alone records is."""
    newest = date(2026, 7, 10)
    on_it = Split(execution_date=newest, split_from=1, split_to=2)
    tiingo = _Tiingo(split=False, lost=frozenset({newest}))
    with pytest.raises(SplitsUnconfirmedError, match="served through 2026-07-09"):
        _source(reference=[on_it], tiingo=tiingo, end=newest)("SPLT")


def test_a_tiingo_silence_longer_than_a_closure_is_a_hole() -> None:
    newest = date(2026, 7, 10)
    lost = frozenset(newest - timedelta(days=i) for i in range(10))
    with pytest.raises(SplitsUnknownError, match="longer than any market closure"):
        _source(reference=[], tiingo=_Tiingo(split=False, lost=lost), end=newest)("SPLT")


def test_a_wrapper_that_forwards_the_close_keeps_the_anchor() -> None:
    """Review round 0: the anchor was found by `isinstance(…, ConfirmedSplits)`, so any wrapper
    lost it. It is structural now (`AnchoredSplitSource`)."""
    inner = _source(reference=[TWO_FOR_ONE], tiingo=_Tiingo(split=True))
    assert isinstance(inner, ConfirmedSplits)

    class _Logged:
        def __call__(self, symbol: str) -> list[Split]:
            return inner(symbol)

        def unadjusted_close(self, symbol: str, day: date) -> float | None:
            return inner.unadjusted_close(symbol, day)
    note = leg_on_basis(who="w", symbol="SPLT", start=ENTRY, start_close=50.0, end=AS_OF,
                        basis_through=AS_OF, splits=_Logged())
    assert note is not None and "ON ONE SPLIT BASIS" in note
