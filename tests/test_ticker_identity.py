"""WHOSE BAR IS IT (2026-10-28) — a reused ticker's former holder's bars leave the current id, and
a re-domiciled line is given its old filer's history.

L7 (#835) measured both on the 2026-10-28 prices scorecard: ten hole-steps where Tiingo's series
under the ticker is another security's (CALY held a BlackRock muni ETF's 2023–24 bars), and two
re-domiciles (XPRO, CLBK) whose histories broke across two ids.

Every record and bar here is REAL, frozen in `tests/fixtures/ticker_identity.json`: Polygon's
ticker details as of each date, EDGAR's filing lists for the four filers, Polygon's per-symbol
bars for the two carries, and bars cut from the store the scorecard measured. The market
calendar is that store's sessions; only the twelve names that make it one carry synthetic prices.
"""

from __future__ import annotations

import ast
import inspect
import json
import textwrap
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.eod import RawBar
from vinci.eod.client import EodClient, holders, ingest_prices, ingest_prices_per_symbol
from vinci.eod.identity import reconcile, series_holes
from vinci.quality import core
from vinci.quality.sources import prices
from vinci.resolver.aliases import (
    ShareClassAlias,
    TickerTenure,
    another_security,
    detect_reuse,
    detect_successions,
    first_sessions,
    load_aliases,
    load_tenures,
    write_tenures,
)
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store import Store

_FIX: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures" / "ticker_identity.json").read_text())
D = date.fromisoformat

CALY, BANFP, CORZ = "SEC-0000837465-CALY", "SEC-0000760498-BANFP", "SEC-0001839341-CORZ"
WLTH, INHD = "SEC-0001524566-WLTH", "SEC-0001961847-INHD"
OLD_XPRO, NEW_XPRO = "SEC-0001575828-XPRO", "SEC-0002126198-XPRO"
OLD_CLBK, NEW_CLBK = "SEC-0001723596-CLBK", "SEC-0002115119-CLBK"
_HOLE = {CALY: (D("2024-10-09"), D("2026-01-16")), BANFP: (D("2026-07-10"), D("2026-07-29")),
         CORZ: (D("2022-12-30"), D("2024-01-24")), WLTH: (D("2023-06-12"), D("2025-12-12")),
         INHD: (D("2026-06-08"), D("2026-07-31"))}
_REF = D("2026-10-16")
_CALENDAR = [f"SEC-{i:010d}-MKT{i:02d}" for i in range(1, 13)]


def _ident(iid: str) -> Identity:
    _sec, cik, ticker = iid.split("-")
    return Identity(internal_id=iid, issuer_id=f"ISS-{cik}", cik=cik, ticker=ticker, mic="XNYS",
                    exchange="NYSE", eod_symbol=ticker, name=ticker)


def _details(overrides: dict[str, dict[str, Any] | None] | None = None,
             ) -> tuple[list[tuple[str, date | None]], Any]:
    asked: list[tuple[str, date | None]] = []

    def details(t: str, on: date | None) -> dict[str, Any] | None:
        asked.append((t, on))
        key = f"{t}@{on.isoformat()}" if on else t
        if overrides and key in overrides:
            return overrides[key]
        rec = _FIX["details"].get(key)
        return None if rec is None else {**rec, **((overrides or {}).get(key + "+") or {})}
    return asked, details


def _filings(cik: str) -> list[tuple[str, date, str]]:
    return [(f, D(d), a) for f, d, a in _FIX["filings"].get(cik, [])]


def _holes(*iids: str) -> dict[str, list[tuple[date, date]]]:
    return {i: [_HOLE[i]] for i in iids}


# --- the reuse rule (`another_security` through `detect_reuse`) ----------------------------------

def test_another_filers_cik_before_the_hole_is_another_security() -> None:
    """POSITIVE (CIK) — CALY as of its last bar before the hole is BlackRock's California muni ETF
    (CIK 1804196); Callaway (837465) trades under it after. Decided on the CIK, so the line's own
    record is never asked."""
    asked, details = _details()
    [t] = detect_reuse([_ident(CALY)], _holes(CALY), details)
    assert (t.first_session, t.prior_last) == (D("2026-01-16"), D("2024-10-09"))
    assert (t.prior_id, t.prior_cik) == ("SEC-0001804196-CALY", "0001804196")
    assert asked == [("CALY", D("2024-10-09"))]


def test_one_filers_hole_with_no_figi_to_tell_proves_nothing() -> None:
    """NEGATIVE (CIK) — BANFP's 12-session hole: the same filer either side, no FIGI on either
    record (a trust preferred). One security with a hole; nothing moves."""
    assert detect_reuse([_ident(BANFP)], _holes(BANFP), _details()[1]) == []


def test_another_share_class_of_the_same_filer_is_another_security() -> None:
    """POSITIVE (FIGI) — CORZ before Core Scientific's 2024 reorganisation carries share-class FIGI
    BBG00Z5H4479; the equity issued at emergence, BBG01L5GH1G3. Tiingo starts a new CORZ series
    at the hole, and L7 measured it among the ten."""
    [t] = detect_reuse([_ident(CORZ)], _holes(CORZ), _details()[1])
    assert t.first_session == D("2024-01-24")
    # the record names the line's own filer, so the former class gets an id of its own
    assert (t.prior_id, t.prior_cik) == ("PRIOR-CORZ-2022-12-30", "0001839341")
    assert "share_class_figi BBG00Z5H4479" in t.evidence


def test_the_same_figi_either_side_is_one_security() -> None:
    """NEGATIVE (FIGI) — INHD's 36-session hole: the same filer and the same FIGIs either side."""
    assert detect_reuse([_ident(INHD)], _holes(INHD), _details()[1]) == []


def test_an_etf_where_the_line_is_an_operating_security_is_another_security() -> None:
    """POSITIVE (type) — WLTH as of 2023-06-12 is the LifeGoal Wealth Builder ETF, a record with no
    CIK and no FIGI at all; Wealthfront, common stock, trades under WLTH from 2025-12-12."""
    [t] = detect_reuse([_ident(WLTH)], _holes(WLTH), _details()[1])
    assert (t.first_session, t.prior_id) == (D("2025-12-12"), "PRIOR-WLTH-2023-06-12")


def test_a_fund_on_both_sides_is_not_proven_by_type() -> None:
    """NEGATIVE (type) — counterfactual: the line itself a fund. A fund before proves nothing."""
    _, details = _details({"WLTH@2025-12-12+": {"type": "ETF"}})
    assert detect_reuse([_ident(WLTH)], _holes(WLTH), details) == []


def test_a_line_whose_own_type_is_unknown_is_not_proven_by_type() -> None:
    """CODEX, #839 round 1. The type rule needs the LINE's type stated and not a fund: a line
    record Polygon cannot serve after the hole, or one with no type, is unknown, never 'not a
    fund' — else a fund's own history would leave it."""
    for after in ({"WLTH@2025-12-12": None}, {"WLTH@2025-12-12+": {"type": None}}):
        assert detect_reuse([_ident(WLTH)], _holes(WLTH), _details(after)[1]) == [], after


def test_a_record_polygon_cannot_serve_proves_nothing() -> None:
    _, details = _details({"CALY@2024-10-09": None})
    assert detect_reuse([_ident(CALY)], _holes(CALY), details) == []


def test_holes_are_read_newest_first_and_a_known_line_costs_no_call() -> None:
    """Counterfactual: CORZ given BANFP's later one-security hole too. The newer hole proves
    nothing, the walk reaches the older one, and the tenure begins after IT."""
    asked, details = _details({"CORZ@2026-07-10": {"cik": "0001839341"}})
    [t] = detect_reuse([_ident(CORZ)], {CORZ: [_HOLE[CORZ], _HOLE[BANFP]]}, details)
    assert t.first_session == D("2024-01-24")
    assert asked[0] == ("CORZ", D("2026-07-10"))
    asked2, details2 = _details()
    assert detect_reuse([_ident(CORZ)], _holes(CORZ), details2, known=[t]) == []
    assert asked2 == []


def test_another_security_reads_the_line_only_when_the_cik_cannot_decide() -> None:
    called: list[bool] = []

    def line() -> dict[str, Any]:
        called.append(True)
        return {}
    assert another_security({"cik": "0000000002"}, "0000000001", line) is not None
    assert called == []
    assert another_security({"cik": "0000000001"}, "0000000001", line) is None
    assert called == [True]


# --- the succession rule (`detect_successions`) --------------------------------------------------

def _spans(over: dict[str, tuple[date, date]] | None = None) -> Any:
    """Each id's first and last stored bar, as the measured store held them."""
    real = {OLD_XPRO: (D("2021-10-04"), D("2026-08-05")), NEW_XPRO: (D("2026-08-06"), _REF),
            OLD_CLBK: (D("2021-09-01"), D("2026-08-05")), NEW_CLBK: (D("2026-08-06"), _REF),
            **(over or {})}
    return real.get


def _succ(new: str, old: str, *, filings: Any = _filings, spans: Any = None,
          overrides: dict[str, dict[str, Any] | None] | None = None) -> list[ShareClassAlias]:
    return detect_successions([_ident(new)], [_ident(old), _ident(new)], _details(overrides)[1],
                              filings, spans or _spans(), as_of=_REF)


def test_a_redomicile_is_proven_by_the_new_filers_8k12b() -> None:
    """POSITIVE (8-K12B) — Expro Ltd (CIK 2126198) filed its 8-K12B on 2026-07-13; the old N.V.'s
    bars end 2026-08-05 and the new id's begin 2026-08-06. Polygon carries no FIGI for XPRO at any
    date, so the filing is the only proof there is."""
    [a] = _succ(NEW_XPRO, OLD_XPRO)
    assert (a.predecessor_id, a.successor_id, a.listed) == (OLD_XPRO, NEW_XPRO, D("2026-08-06"))
    assert a.predecessor_cik == "0001575828" and a.share_class_figi is None
    assert "8-K12B 0001104659-26-083106" in a.evidence


def test_no_succession_filing_is_no_succession() -> None:
    """NEGATIVE (8-K12B) — the same pair with the new filer's list replaced by the OLD filer's,
    which holds only a plain 8-K: the shared ticker alone proves nothing."""
    assert _succ(NEW_XPRO, OLD_XPRO, filings=lambda cik: _filings("0001575828")) == []


def test_a_stale_filing_or_a_history_that_ended_long_before_is_another_event() -> None:
    """NEGATIVE (window) — counterfactuals: the 8-K12B a year and a day before the boundary; the
    old filer's bars ending fifteen days before it (a reuse, not a succession); the two spans
    overlapping."""
    def aged(cik: str) -> list[tuple[str, date, str]]:
        return [(f, D("2025-08-05") if f == "8-K12B" else d, a) for f, d, a in _filings(cik)]
    assert _succ(NEW_XPRO, OLD_XPRO, filings=aged) == []
    assert _succ(NEW_XPRO, OLD_XPRO,
                 spans=_spans({OLD_XPRO: (D("2021-10-04"), D("2026-07-22"))})) == []
    assert _succ(NEW_XPRO, OLD_XPRO,
                 spans=_spans({OLD_XPRO: (D("2021-10-04"), D("2026-08-06"))})) == []


def test_a_second_step_conversion_carries_another_figi_and_its_8k12b_proves_it() -> None:
    """NEGATIVE (FIGI), REAL — CLBK's old filer carried share-class FIGI BBG003222R95 (as of
    2026-06-12); the conversion's new shares carry BBG023TM45X9. Polygon's record as of the day
    before the boundary already names the new filer, so no FIGI proof exists; the 8-K12B (filed
    2026-07-21) proves the succession, and the row claims no FIGI."""
    assert _FIX["details"]["CLBK@2026-06-12"]["share_class_figi"] != \
        _FIX["details"]["CLBK@2026-10-16"]["share_class_figi"]
    [a] = _succ(NEW_CLBK, OLD_CLBK)
    assert a.share_class_figi is None and "8-K12B 0001193125-26-309602" in a.evidence
    assert _succ(NEW_CLBK, OLD_CLBK, filings=lambda cik: []) == []


def test_one_figi_under_both_filers_proves_a_succession() -> None:
    """POSITIVE (FIGI) — counterfactual: the old filer's record the day before the boundary
    carrying the new line's FIGI. No filing is read."""
    [a] = _succ(NEW_CLBK, OLD_CLBK, filings=lambda cik: [], overrides={"CLBK@2026-08-05": {
        **_FIX["details"]["CLBK@2026-06-12"], "share_class_figi": "BBG023TM45X9"}})
    assert a.share_class_figi == "BBG023TM45X9" and "carry share_class_figi" in a.evidence


def test_a_line_continues_only_a_line_of_its_own_share_class() -> None:
    old = _ident(OLD_XPRO).model_copy(update={"share_class": "B"})
    assert detect_successions([_ident(NEW_XPRO)], [old], _details()[1], _filings, _spans(),
                              as_of=_REF) == []


def test_the_tenure_table_only_ever_grows(tmp_path: Path) -> None:
    """ACCUMULATE-ONLY, as the alias table is: a row once written is never dropped or rewritten,
    so a line's tenure always traces to the record that proved it."""
    [t] = detect_reuse([_ident(CALY)], _holes(CALY), _details()[1])
    assert write_tenures(tmp_path, [t]) == 1
    assert write_tenures(tmp_path, [replace(t, evidence="a later, different reading")]) == 0
    assert write_tenures(tmp_path, []) == 0
    assert load_tenures(tmp_path) == [t]


def test_first_sessions_take_the_later_of_a_tenure_and_a_listing() -> None:
    t = TickerTenure(internal_id=CALY, ticker="CALY", cik="0000837465",
                     first_session=D("2026-01-16"), prior_id="x", prior_cik=None,
                     prior_last=D("2024-10-09"), evidence="fixture")
    a = ShareClassAlias(predecessor_id="SEC-0000837465-MODG", successor_id=CALY,
                        cik="0000837465", share_class_figi="BBG001S70DV8",
                        predecessor_symbol="MODG", successor_symbol="CALY",
                        listed=D("2024-10-28"), evidence="counterfactual")
    assert first_sessions([a], [t]) == {CALY: D("2026-01-16")}
    assert first_sessions([a], []) == {CALY: D("2024-10-28")}


# --- the store: re-filing ------------------------------------------------------------------------

def _bar(iid: str, row: list[Any]) -> PriceBar:
    d, o, h, lo, c, v, s = row
    return PriceBar(internal_id=iid, bar_date=D(d), open=o, high=h, low=lo, close=c, volume=v,
                    source=s)


def test_refiled_bars_keep_their_prices_and_name_where_they_came_from(tmp_path: Path) -> None:
    with Store(tmp_path / "v.db") as store:
        store.write_prices(_bar(CALY, r) for r in _FIX["held"][CALY])
        prior = "SEC-0001804196-CALY"
        # the former holder already holds one of the sessions: its own bar is kept
        store.write_prices([_bar(prior, [*_FIX["held"][CALY][0][:6], "polygon-grouped"])])
        assert store.refile_bars(CALY, prior, before=D("2026-01-16")) == 4
        assert [b.bar_date for b in store.get_price_history(CALY)] == [
            D(r[0]) for r in _FIX["held"][CALY][4:]]
        moved = store.get_price_history(prior)
        assert [(b.bar_date, b.close) for b in moved] == [
            (D(r[0]), r[4]) for r in _FIX["held"][CALY][:4]]
        assert moved[0].source == "polygon-grouped"
        assert {b.source for b in moved[1:]} == {f"polygon-grouped+refiled:{CALY}"}
        assert store.refile_bars(CALY, prior, before=D("2026-01-16")) == 0


# --- the ingest: a bar is filed under the id that held its symbol that day -----------------------

class _Grouped(EodClient):
    """Serves the frozen bars as whole-market days."""

    def __init__(self, by_symbol: dict[str, list[list[Any]]]) -> None:
        self.days: dict[date, dict[str, RawBar]] = {}
        for sym, rows in by_symbol.items():
            for d, o, h, lo, c, v, *_ in rows:
                self.days.setdefault(D(d), {})[sym] = RawBar(ticker=sym, open=o, high=h, low=lo,
                                                             close=c, volume=v)

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        return self.days.get(day, {})

    def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
        return sorted((d, b[symbol]) for d, b in self.days.items()
                      if symbol in b and start <= d <= end)


def test_a_reused_tickers_former_bars_are_never_filed_under_the_current_id(tmp_path: Path) -> None:
    """THE DEFECT AND ITS FIX, through `ingest_prices`. Without a first session (the old
    attribution, by today's symbol) the ETF's 2024 bars land under Callaway's id; with CALY's
    tenure they do not, and Callaway's own bars still do."""
    eod = _Grouped({"CALY": _FIX["held"][CALY]})
    start, end = D("2024-10-01"), D("2026-01-23")
    with Store(tmp_path / "old.db") as store:
        ingest_prices(eod, store, [_ident(CALY)], start=start, end=end)
        assert len(store.get_price_history(CALY)) == 8                   # the defect, reproduced
    with Store(tmp_path / "new.db") as store:
        ingest_prices(eod, store, [_ident(CALY)], start=start, end=end,
                      first_sessions={CALY: D("2026-01-16")})
        assert [b.bar_date for b in store.get_price_history(CALY)] == [
            D(r[0]) for r in _FIX["held"][CALY][4:]]
    with Store(tmp_path / "aggs.db") as store:
        ingest_prices_per_symbol(eod, store, [_ident(CALY)],  # type: ignore[arg-type]
                                 start=start, end=end, first_sessions={CALY: D("2026-01-16")})
        assert min(b.bar_date for b in store.get_price_history(CALY)) == D("2026-01-16")


def test_two_ids_of_one_symbol_each_get_their_own_days(tmp_path: Path) -> None:
    """`run_monthly` ingests EVERY security, both XPRO ids among them. The old dict kept whichever
    id came last for every day; by the alias's listing each gets its own."""
    rows = _FIX["held"][OLD_XPRO] + _FIX["held"][NEW_XPRO]
    eod = _Grouped({"XPRO": rows})
    with Store(tmp_path / "v.db") as store:
        ingest_prices(eod, store, [_ident(OLD_XPRO), _ident(NEW_XPRO)], start=D("2026-08-03"),
                      end=D("2026-08-07"), first_sessions={NEW_XPRO: D("2026-08-06")})
        assert [b.bar_date for b in store.get_price_history(OLD_XPRO)] == [
            D("2026-08-04"), D("2026-08-05")]
        assert [b.bar_date for b in store.get_price_history(NEW_XPRO)] == [
            D("2026-08-06"), D("2026-08-07")]
    on = holders([_ident(OLD_XPRO), _ident(NEW_XPRO)])
    assert on(D("2026-08-05")) == {"XPRO": NEW_XPRO}     # no boundary known: the last, as before


# --- end to end: the repair, then the scorecard --------------------------------------------------

class _Polygon(_Grouped):
    def __init__(self) -> None:
        super().__init__({})
        self.asked: list[tuple[str, date | None]] = []
        self._details = _details()[1]

    def ticker_details(self, ticker: str, as_of: date | None = None) -> dict[str, Any] | None:
        self.asked.append((ticker, as_of))
        return self._details(ticker, as_of)  # type: ignore[no-any-return]

    def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
        self.asked.append((symbol, None))
        return [(D(d), RawBar(ticker=symbol, open=o, high=h, low=lo, close=c, volume=v))
                for d, o, h, lo, c, v in _FIX["aggs"].get(symbol, []) if start <= D(d) <= end]


def _root(tmp_path: Path) -> Path:
    """A store holding the real bars, on the real calendar, with the securities' rows."""
    root = tmp_path / "root"
    (root / "data" / "snapshots").mkdir(parents=True)
    with Store(root / "data" / "vinci.db") as store:
        for iid in [*_CALENDAR, *_FIX["held"]]:
            store.upsert_security(_ident(iid))
        store.write_prices(PriceBar(internal_id=m, bar_date=D(d), open=1.0, high=1.0, low=1.0,
                                    close=1.0, volume=1.0, source="synthetic-calendar")
                           for m in _CALENDAR for d in _FIX["calendar"])
        for iid, rows in _FIX["held"].items():
            store.write_prices(_bar(iid, r) for r in rows)
    return root


def _reconcile(root: Path, eod: _Polygon) -> dict[str, Any]:
    lines = [_ident(i) for i in _FIX["held"]]
    with Store(root / "data" / "vinci.db") as store:
        return reconcile(store, eod, _filings, root / "data" / "snapshots", lines=lines,
                         master=lines, as_of=_REF)


def test_the_holes_are_the_scorecards_own(tmp_path: Path) -> None:
    """On the store's own calendar (the fixture's old XPRO and CLBK ids hold a cut, not a series,
    so they carry holes of the fixture's making)."""
    root = _root(tmp_path)
    with Store(root / "data" / "vinci.db") as store:
        holes = series_holes(store, list(_FIX["held"]))
    assert {i: h for i, h in holes.items() if i in _HOLE} == {i: [h] for i, h in _HOLE.items()}
    assert set(holes) - set(_HOLE) == {OLD_XPRO, OLD_CLBK, NEW_XPRO, NEW_CLBK} - {
        NEW_XPRO, NEW_CLBK}


def test_the_repair_moves_what_is_proven_and_nothing_else(tmp_path: Path) -> None:
    root = _root(tmp_path)
    eod = _Polygon()
    moved = _reconcile(root, eod)
    assert {t.internal_id for t in moved["tenures"]} == {CALY, CORZ, WLTH}
    assert moved["refiled"] == {CALY: 4, CORZ: 3, WLTH: 3}
    assert {a.successor_id for a in moved["successions"]} == {NEW_XPRO, NEW_CLBK}
    assert moved["carried"] == {NEW_XPRO: 4, NEW_CLBK: 6}
    snaps = root / "data" / "snapshots"
    assert set(load_tenures(snaps)) == set(moved["tenures"]) and len(load_aliases(snaps)) == 2
    with Store(root / "data" / "vinci.db") as store:
        for iid in (BANFP, INHD, OLD_XPRO, OLD_CLBK):     # proven one security, or never re-keyed
            assert [(b.bar_date, b.close, b.source) for b in store.get_price_history(iid)] == [
                (D(r[0]), r[4], r[6]) for r in _FIX["held"][iid]]
        assert min(b.bar_date for b in store.get_price_history(CALY)) == D("2026-01-16")
        clbk = {b.bar_date: b for b in store.get_price_history(NEW_CLBK)}
    # CLBK's conversion exchanged 2.2 new shares for each old one: Polygon's own bars carry the
    # ratio, and the held copy older than its window is restated by Polygon's own factor
    assert clbk[D("2024-10-25")].close == pytest.approx(16.69 * 7.8409 / 17.25)
    assert clbk[D("2024-10-25")].source == f"polygon-alias:{OLD_CLBK}+restated"
    assert clbk[D("2026-07-20")].close == pytest.approx(11.1364)
    # a second run moves nothing, and asks no bars: it re-reads only the records of the holes it
    # could not prove — each kept for good once read, so in a real run never a request
    n = len(eod.asked)
    again = _reconcile(root, eod)
    assert not again["tenures"] and not again["successions"]
    assert again["refiled"] == {} and again["carried"] == {}
    assert set(eod.asked[n:]) <= set(eod.asked[:n])
    assert all(on is not None for _t, on in eod.asked[n:])


def test_the_scorecard_reads_the_repaired_store(tmp_path: Path) -> None:
    """END TO END: real bars → repair → `prices.read_store` → the checks. Before the repair CALY's
    hole differs and the XPRO pair differs; after it CALY has no hole, CALY and its former holder
    are two securities in turn, and the XPRO pair is one line by a recorded succession."""
    root = _root(tmp_path)

    def card() -> dict[str, dict[str, core.ItemResult]]:
        items = prices.read_store(root, tiingo=lambda: None).items
        return {c: {n: fn(items[n]) for n in items} for c, fn in (
            ("gap", prices._series_gap), ("ids", prices._history_across_ids))}

    before = card()
    assert before["gap"]["CALY"].counts[core.DIFFERS_UNEXPLAINED] == 1
    assert before["ids"][OLD_XPRO].counts == {core.DIFFERS_UNEXPLAINED: 1}
    _reconcile(root, _Polygon())
    after = card()
    assert after["gap"]["CALY"].counts.get(core.DIFFERS_UNEXPLAINED, 0) == 0
    assert after["gap"]["BANFP"].counts[core.DIFFERS_UNEXPLAINED] == 1   # one security's hole
    assert after["ids"]["CALY"].counts == {core.CONFIRMED: 1}
    assert after["ids"]["SEC-0001804196-CALY"].counts == {core.CONFIRMED: 1}
    for iid in (OLD_XPRO, NEW_XPRO, OLD_CLBK, NEW_CLBK):
        assert after["ids"][iid].counts == {core.DIFFERS_STATED: 1}


# --- the call sites (pin the artifact, not the helper) -------------------------------------------

def _kwargs_of(fn: Any, callee: str) -> list[set[str]]:
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    return [{k.arg for k in n.keywords if k.arg} for n in ast.walk(tree)
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == callee]


def test_every_refresh_files_by_the_committed_tables() -> None:
    """Each path that ingests a security's bars hands the ingest its first sessions: the weekly
    screen, the monthly scoring refresh (both XPRO ids), and `vinci refresh` either way."""
    from vinci import cli, orchestrator
    from vinci.screens import run

    assert all("first_sessions" in k for k in _kwargs_of(orchestrator.run_weekly,
                                                           "screen_universe"))
    for fn, callee in ((run.screen_universe, "ingest_prices"),
                       (orchestrator.run_monthly, "ingest_prices"),
                       (cli._cmd_refresh, "ingest_prices"),
                       (cli._cmd_refresh, "ingest_prices_per_symbol"),
                       (cli._cmd_screen, "screen_universe")):
        calls = _kwargs_of(fn, callee)
        assert calls, f"{fn.__name__} no longer calls {callee}"
        # the benchmark's own ingest (an IDX- id, never reused) is the one call that may skip it
        assert sum("first_sessions" in k for k in calls) >= 1, (fn.__name__, callee)


def test_another_checkout_refiles_from_the_committed_table_without_asking(tmp_path: Path) -> None:
    """The tables are committed so EVERY store is repaired the same way: a checkout whose store
    still holds the former holder's bars re-files them from the table alone — the reuse is never
    probed again — and carries the successions."""
    first = _root(tmp_path / "a")
    _reconcile(first, _Polygon())
    other = _root(tmp_path / "b")
    for name in ("ticker_tenure.jsonl", "share_class_aliases.jsonl"):
        (other / "data" / "snapshots" / name).write_text(
            (first / "data" / "snapshots" / name).read_text())
    eod = _Polygon()
    moved = _reconcile(other, eod)
    assert moved["tenures"] == [] and moved["successions"] == []
    assert moved["refiled"] == {CALY: 4, CORZ: 3, WLTH: 3}
    assert moved["carried"] == {NEW_XPRO: 4, NEW_CLBK: 6}
    assert not any(t in ("CALY", "CORZ", "WLTH") for t, _on in eod.asked)


def test_a_carried_history_is_never_refiled_off_its_line(tmp_path: Path) -> None:
    """REVIEW, round 0. A line can be a reused ticker's holder AND a rename's successor (CALY:
    BlackRock's ETF before it, and — counterfactually — MODG's history carried to it). The carried
    bars are its own line's and stay; only the other security's own bars move, so the next build
    neither strips the carry nor re-carries it."""
    carried = PriceBar(internal_id=CALY, bar_date=D("2025-06-02"), open=1.0, high=1.0, low=1.0,
                       close=1.0, volume=1.0, source="polygon-alias:SEC-0000837465-MODG")
    with Store(tmp_path / "v.db") as store:
        store.write_prices([*(_bar(CALY, r) for r in _FIX["held"][CALY]), carried])
        assert store.refile_bars(CALY, "SEC-0001804196-CALY", before=D("2026-01-16")) == 4
        assert store.refile_bars(CALY, "SEC-0001804196-CALY", before=D("2026-01-16")) == 0
        kept = store.get_price_history(CALY)
    assert [b.source for b in kept if b.bar_date < D("2026-01-16")] == [carried.source]


def test_the_hole_calendar_counts_every_stored_row_as_the_scorecard_does(tmp_path: Path) -> None:
    """A re-filed former holder has no securities row; the scorecard still counts its bars."""
    with Store(tmp_path / "v.db") as store:
        store.write_prices([_bar("PRIOR-X-2024-01-02", ["2024-01-02", 1, 1, 1, 1, 1, "s"])])
        assert store.bars_per_session() == {"2024-01-02": 1}
