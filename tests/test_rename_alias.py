"""A RENAMED LINE CONTINUES ITS RECORD (2026-10-27) — the alias table and the bar carry.

Helix Energy Solutions became Hornbeck Offshore Services: HLX → HOS, CIK 866829, HOS listed on
2026-09-02. The resolver keys a line ``SEC-<cik>-<ticker>``, so HOS was a new id with no history,
and the 2026-09-22 and 2026-10-16 screens could not evaluate it ("only 20d" / "only 44d history").
Polygon's share-class FIGI survives the ticker change — HLX as of 2026-09-01 and HOS today both
read BBG001S978V8 — so the two ids are confirmed as one class, recorded in the alias table, and
HOS is given HLX's bars before its listing date. HLX itself is never re-keyed.

Every number is REAL, frozen in `tests/fixtures/rename_hlx_hos.json`: the two Polygon reference
records, both tickers' daily bars, and the HLX bars the 2026-10-16 run's own store held.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.eod import RawBar
from vinci.eod.client import EodClient, carry_forward
from vinci.eod.features import compute_price_features
from vinci.resolver.aliases import (
    ShareClassAlias,
    detect_renames,
    heirs,
    load_aliases,
    predecessors,
    write_aliases,
)
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store import Store

_FIX: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures" / "rename_hlx_hos.json").read_text())
_CIK = "0000866829"
_HLX, _HOS = f"SEC-{_CIK}-HLX", f"SEC-{_CIK}-HOS"
_LISTED = date(2026, 9, 2)
_REF = date(2026, 10, 16)


def _ident(t: str, share_class: str | None = None) -> Identity:
    return Identity(internal_id=f"SEC-{_CIK}-{t}", issuer_id=f"ISS-{_CIK}", cik=_CIK, ticker=t,
                    mic="XNYS", exchange="NYSE", eod_symbol=t, name="Hornbeck Offshore",
                    share_class=share_class)


def _details(overrides: dict[str, dict[str, Any]] | None = None
             ) -> tuple[list[tuple[str, date | None]], Any]:
    asked: list[tuple[str, date | None]] = []

    def details(t: str, on: date | None) -> dict[str, Any] | None:
        asked.append((t, on))
        key = t if on is None else f"{t}@{on.isoformat()}"
        rec = _FIX["details"].get(key)
        return {**rec, **((overrides or {}).get(key, {}))} if rec else None
    return asked, details


def _first_session(line: Identity) -> date | None:
    """HOS's first bar under its own ticker, from its frozen aggregates: 2026-09-02."""
    return _bars(line.eod_symbol)[0][0]


def _bars(t: str) -> list[tuple[date, RawBar]]:
    return [(date.fromisoformat(d), RawBar(ticker=t, open=o, high=h, low=lo, close=c, volume=v))
            for d, o, h, lo, c, v in _FIX["bars"][t]]


# --- detection -----------------------------------------------------------------------------------

def test_a_rename_is_confirmed_on_the_share_class_figi() -> None:
    """POSITIVE — HOS's record today and HLX's as of the day before HOS listed carry the same
    share-class FIGI and CIK: one class, two tickers."""
    asked, details = _details()
    [alias] = detect_renames([_ident("HOS")], [_ident("HLX"), _ident("HOS")], {"HOS": "CS"},
                             details, _first_session, as_of=_REF)
    assert (alias.predecessor_id, alias.successor_id) == (_HLX, _HOS)
    assert alias.share_class_figi == "BBG001S978V8" and alias.listed == _LISTED
    assert asked == [("HOS", _REF), ("HLX", date(2026, 9, 1))]


def test_the_boundary_is_the_new_tickers_first_session_not_its_list_date() -> None:
    """Polygon's ``list_date`` is the SHARE CLASS's listing: SVIA reads 2025-12-08, the day the
    class listed as BRR. A HOS record carrying that shape must still read HLX the day before HOS's
    first session, not before a listing the old ticker itself made."""
    asked, details = _details({"HOS@2026-10-16": {"list_date": "1997-07-01"}})
    [alias] = detect_renames([_ident("HOS")], [_ident("HLX")], {"HOS": "CS"}, details,
                             _first_session, as_of=_REF)
    assert alias.listed == _LISTED
    assert asked[-1] == ("HLX", date(2026, 9, 1))


def test_a_different_figi_is_two_classes_never_one_record() -> None:
    """NEGATIVE — the reuse shape L7 measured (UMBF / UMBFO, WTFC / WTFCN: one CIK, two classes).
    HLX's real record with a different FIGI must not splice two series into one."""
    _, details = _details({"HLX@2026-09-01": {"share_class_figi": "BBG000000000"}})
    assert detect_renames([_ident("HOS")], [_ident("HLX")], {"HOS": "CS"}, details,
                          _first_session, as_of=_REF) == []


def test_a_line_with_no_figi_is_never_aliased() -> None:
    """NEGATIVE — PLGO carries no FIGI in any pull. With no key there is no rename, only a guess."""
    _, details = _details({"HOS@2026-10-16": {"share_class_figi": None}})
    assert detect_renames([_ident("HOS")], [_ident("HLX")], {"HOS": "CS"}, details,
                          _first_session, as_of=_REF) == []


def test_only_an_inactive_sibling_of_the_same_class_costs_a_call() -> None:
    """NEGATIVE — an issuer's other LIVE line (UHAL beside UHAL.B) is not a rename, and a different
    share class is not either: neither is ever looked up."""
    asked, details = _details()
    assert detect_renames([_ident("HOS")], [_ident("HLX")], {"HOS": "CS", "HLX": "CS"},
                          details, _first_session, as_of=_REF) == []
    assert detect_renames([_ident("HOS")], [_ident("HLX", share_class="B")], {"HOS": "CS"},
                          details, _first_session, as_of=_REF) == []
    assert asked == []


def test_the_alias_table_only_ever_grows(tmp_path: Path) -> None:
    """ACCUMULATE-ONLY: a successor must always trace to its predecessor, so a row once written is
    never dropped, and writing it again adds nothing."""
    _, details = _details()
    found = detect_renames([_ident("HOS")], [_ident("HLX")], {"HOS": "CS"}, details,
                           _first_session, as_of=_REF)
    assert write_aliases(tmp_path, found) == 1
    assert write_aliases(tmp_path, found) == 0
    assert write_aliases(tmp_path, []) == 0
    assert load_aliases(tmp_path) == found
    assert predecessors(load_aliases(tmp_path)) == {_HOS: found}


# --- the carry -----------------------------------------------------------------------------------

class _Polygon(EodClient):
    """Serves the frozen aggregates and records each request."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, date, date]] = []

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        return {}

    def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
        self.asked.append((symbol, start, end))
        return [(d, b) for d, b in _bars(symbol) if start <= d <= end]


def _store(tmp_path: Path, *, held_scale: float = 1.0) -> Store:
    store = Store(tmp_path / "vinci.db")
    k = held_scale
    store.write_prices(PriceBar(internal_id=_HLX, bar_date=date.fromisoformat(d), open=o * k,
                                high=h * k, low=lo * k, close=c * k, volume=v / k, source=s)
                       for d, o, h, lo, c, v, s in _FIX["held_hlx"])
    store.write_prices(PriceBar(internal_id=_HOS, bar_date=d, open=b.open, high=b.high, low=b.low,
                                close=b.close, volume=b.volume, source="polygon-grouped")
                       for d, b in _bars("HOS"))
    return store


def test_the_new_id_is_given_the_old_ids_history(tmp_path: Path) -> None:
    """HOS held 32 bars from 2026-09-02. After the carry it holds HLX's history before that day:
    Polygon's own HLX bars across the plan's two years, and the store's older copies beyond."""
    store = _store(tmp_path)
    client = _Polygon()
    n = carry_forward(client, store, predecessor_id=_HLX, predecessor_symbol="HLX",
                      successor_id=_HOS, listed=_LISTED, end=_REF)
    hos = store.get_price_history(_HOS)
    assert client.asked == [("HLX", date(2024, 10, 16), date(2026, 9, 1))]
    assert hos[0].bar_date == date(2024, 9, 3) and hos[-1].bar_date == _REF
    assert n == len(hos) - 32
    assert {b.source for b in hos if b.bar_date >= _LISTED} == {"polygon-grouped"}
    assert {b.source for b in hos if b.bar_date < _LISTED} == {f"polygon-alias:{_HLX}"}
    # Polygon's bar wins on a session both hold; the store's copy fills only what it cannot serve
    fresh = dict(_bars("HLX"))
    on = date(2024, 10, 28)
    assert next(b.close for b in hos if b.bar_date == on) == fresh[on].close
    # the old id is untouched, and the carry runs once: a second call neither writes nor asks
    assert len(store.get_price_history(_HLX)) == len(_FIX["held_hlx"])
    assert carry_forward(client, store, predecessor_id=_HLX, predecessor_symbol="HLX",
                         successor_id=_HOS, listed=_LISTED, end=_REF) == 0
    assert len(client.asked) == 1


def test_a_bar_the_old_id_holds_after_the_listing_is_never_carried(tmp_path: Path) -> None:
    """L7'S MIRROR CASE. If the old ticker is later reused and its new holder's bars land under
    the old id (L7 measured that shape), they belong to another company. A bar dated on or after
    HOS's listing — here a counterfactual one on 2026-10-19 — must not reach HOS."""
    store = _store(tmp_path)
    store.write_prices([PriceBar(internal_id=_HLX, bar_date=date(2026, 10, 19), open=50.0,
                                 high=50.0, low=50.0, close=50.0, volume=1.0, source="reuse")])
    carry_forward(_Polygon(), store, predecessor_id=_HLX, predecessor_symbol="HLX",
                  successor_id=_HOS, listed=_LISTED, end=_REF)
    assert date(2026, 10, 19) not in {b.bar_date for b in store.get_price_history(_HOS)}


def test_a_held_copy_on_an_old_split_basis_is_restated_before_it_is_carried(
    tmp_path: Path
) -> None:
    """L7's caution. The held HLX bars are put at HALF their real prices (and double the volume) —
    the shape of a store pulled before a 2-for-1 split that Polygon has since applied. Set beside
    Polygon's fresh bar for the earliest shared session, every older copy is restated."""
    store = _store(tmp_path, held_scale=0.5)
    carry_forward(_Polygon(), store, predecessor_id=_HLX, predecessor_symbol="HLX",
                  successor_id=_HOS, listed=_LISTED, end=_REF)
    first = store.get_price_history(_HOS)[0]
    real = _FIX["held_hlx"][0]
    assert first.close == pytest.approx(real[4]) and first.volume == pytest.approx(real[5])
    assert first.source == f"polygon-alias:{_HLX}+restated"


def test_the_screen_can_evaluate_the_renamed_line(tmp_path: Path) -> None:
    """THE POINT OF IT. On its own 32 bars HOS has no 52-week drawdown ("only Nd history", so the
    screen marks it NOT_EVALUATED); on the carried series it has one."""
    store = _store(tmp_path)
    before = compute_price_features(store.get_price_history(_HOS), reference_date=_REF,
                                    staleness_days=5)
    assert before.drawdown_from_high.value is None
    assert "history" in (before.drawdown_from_high.note or "")
    carry_forward(_Polygon(), store, predecessor_id=_HLX, predecessor_symbol="HLX",
                  successor_id=_HOS, listed=_LISTED, end=_REF)
    after = compute_price_features(store.get_price_history(_HOS), reference_date=_REF,
                                   staleness_days=5)
    assert after.drawdown_from_high.value is not None and after.drawdown_from_high.value < 0


def test_an_alias_round_trips_through_its_row(tmp_path: Path) -> None:
    a = ShareClassAlias(predecessor_id=_HLX, successor_id=_HOS, cik=_CIK,
                        share_class_figi="BBG001S978V8", predecessor_symbol="HLX",
                        successor_symbol="HOS", listed=_LISTED, evidence="fixture")
    write_aliases(tmp_path, [a])
    assert load_aliases(tmp_path) == [a]


# --- through the REAL universe builder -----------------------------------------------------------

def _build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, sibling: bool = False,
           overrides: dict[str, dict[str, Any]] | None = None,
           tenures: list[dict[str, str]] | None = None,
           ) -> tuple[dict[str, int], set[str], list[tuple[str, date | None]]]:
    """The REAL builder on 2026-10-16: the entity master holds HLX (its real committed row), the
    2026-08-24 population admitted it, and the resolver now lists HOS — plus, with ``sibling``,
    a class-B line of the same issuer that trades five times as much (a counterfactual: no real
    rename has had a live sibling)."""
    from collections.abc import Iterator

    from vinci import universe as uni
    from vinci.config import Config
    from vinci.universe import build_universe

    snaps = tmp_path / "snapshots"
    snaps.mkdir(parents=True)
    if tenures:
        (snaps / "ticker_tenure.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tenures))
    (snaps / "issuers.jsonl").write_text(json.dumps({
        "cik": _CIK, "country": "US", "first_seen": "2026-06-12", "issuer_id": f"ISS-{_CIK}",
        "name": "HORNBECK OFFSHORE SERVICES, INC.", "sic": "1389",
        "sic_description": "Oil & Gas Field Services, NEC"}) + "\n")
    (snaps / "securities.jsonl").write_text(json.dumps({
        "cik": _CIK, "currency": "USD", "eod_symbol": "HLX", "exchange": "NYSE",
        "first_seen": "2026-06-12", "internal_id": _HLX, "issuer_id": f"ISS-{_CIK}",
        "mic": "XNYS", "name": "HELIX ENERGY SOLUTIONS GROUP INC", "share_class": None,
        "sic": "1389", "ticker": "HLX"}) + "\n")
    (snaps / "universe_snapshot.jsonl").write_text(json.dumps({
        "as_of": "2026-08-24", "coverage_status": "present", "in_universe": 1,
        "internal_id": _HLX, "market_cap": 1.0, "source": "fixture"}) + "\n")
    close = _FIX["bars"]["HOS"][-1][4]
    lines = [_ident("HOS")] + ([_ident("HOS.B", share_class="B")] if sibling else [])
    asked, details = _details(overrides)

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R: return cls()
        def iter_universe(self, exchanges: object) -> Iterator[Identity]: yield from lines
        def sic_for(self, cik: str) -> tuple[str, str]: return ("1389", "Oil & Gas Field Svcs")
        def latest_report(self, *_: object) -> None: return None
        def registered_line(self, *_: object) -> None: return None

    class _E(_Polygon):
        @classmethod
        def from_config(cls, cfg: object) -> _E: return cls()
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            vol = {"HOS": 1_000_000.0, "HOS.B": 5_000_000.0}
            return ({i.eod_symbol: RawBar(ticker=i.eod_symbol, open=close, high=close, low=close,
                                          close=close, volume=vol[i.eod_symbol])
                     for i in lines} if day == _REF else {})
        def security_types(self) -> dict[str, str]: return {i.eod_symbol: "CS" for i in lines}
        def share_class_counts(self, tickers: object) -> dict[str, float]:
            return dict.fromkeys(tickers, 60_000_000.0)  # type: ignore[call-overload]
        def ticker_details(self, ticker: str, as_of: date | None = None) -> dict[str, Any] | None:
            return details(ticker, as_of)  # type: ignore[no-any-return]

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed: return cls()
        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            return {_CIK: 120_000_000.0}, {_CIK: "dei:EntityCommonStockSharesOutstanding"}

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    stats = build_universe(Config(data_dir=tmp_path), reference_date=_REF,
                           share_periods=["CY2026Q2I"])
    admitted = {json.loads(x)["internal_id"] for x in
                (snaps / "universe_snapshot.jsonl").read_text().splitlines() if x.strip()}
    return stats, admitted, asked


def test_the_builder_records_the_rename_and_carries_the_history(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """End to end: the build records the alias, carries HLX's bars to HOS, and a second build asks
    Polygon nothing more."""
    from vinci.config import Config
    from vinci.universe import build_universe

    stats, admitted, asked = _build(monkeypatch, tmp_path)
    assert stats["in_universe"] == 1 and admitted == {_HOS}
    snaps = tmp_path / "snapshots"
    [alias] = load_aliases(snaps)
    assert (alias.predecessor_id, alias.successor_id, alias.listed) == (_HLX, _HOS, _LISTED)
    with Store(tmp_path / "vinci.db") as store:
        carried = store.get_price_history(_HOS)
    assert carried and carried[0].bar_date == date(2024, 10, 28)   # Polygon's window; no held HLX
    assert all(b.source == f"polygon-alias:{_HLX}" for b in carried)
    # a second build finds the alias already known and asks nothing more
    n = len(asked)
    build_universe(Config(data_dir=tmp_path), reference_date=_REF, share_periods=["CY2026Q2I"])
    assert len(asked) == n


def test_the_heir_of_an_incumbent_keeps_its_issuers_slot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE INCUMBENT RULE FOLLOWS THE ALIAS. HLX was the issuer's line in the 2026-08-24 population;
    HOS continues it, so a more-traded sibling (counterfactual, above) does not take the slot."""
    _, admitted, _ = _build(monkeypatch, tmp_path, sibling=True)
    assert admitted == {_HOS}


def test_incumbency_follows_a_chain_of_renames() -> None:
    """A → B → C: C is the heir of an incumbent A even though B never sat in a population (review,
    round 0: a one-step test missed C). Built on the real HLX → HOS alias, extended by one step."""
    def step(a: str, b: str) -> ShareClassAlias:
        return ShareClassAlias(predecessor_id=a, successor_id=b, cik=_CIK,
                               share_class_figi="BBG001S978V8", predecessor_symbol=a[-3:],
                               successor_symbol=b[-3:], listed=_LISTED, evidence="fixture")
    chain = [step(_HLX, _HOS), step(_HOS, f"SEC-{_CIK}-HOX")]
    assert heirs(chain, {_HLX}) == {_HOS, f"SEC-{_CIK}-HOX"}
    assert heirs(chain, {"SEC-0000000001-ZZZ"}) == set()


def test_the_new_tickers_record_is_read_as_of_the_build_not_today(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CODEX, #833 round 1. A build dated 2026-10-16 must not be swayed by what Polygon says about
    HOS today. HOS's record TODAY is given another class's FIGI — the shape of a ticker reused
    after the build — while its real record as of 2026-10-16 carries BBG001S978V8: the build
    confirms the alias from the record dated to its own day, and never asks for today's."""
    _, _, asked = _build(monkeypatch, tmp_path,
                         overrides={"HOS": {"share_class_figi": "BBG000000000"}})
    [alias] = load_aliases(tmp_path / "snapshots")
    assert (alias.predecessor_id, alias.successor_id) == (_HLX, _HOS)
    assert ("HOS", _REF) in asked and ("HOS", None) not in asked


# --- a reused ticker inside the window (2026-10-28, `vinci/eod/identity.py`) ---------------------

def _reused_hos(monkeypatch: pytest.MonkeyPatch) -> None:
    """Counterfactual: another security traded as HOS inside Polygon's two-year window, so HOS's
    aggregates (the TICKER's, whoever held it) begin with its bar on 2026-08-03."""
    monkeypatch.setitem(_FIX["bars"], "HOS",
                        [["2026-08-03", 5.0, 5.0, 5.0, 5.0, 100.0], *_FIX["bars"]["HOS"]])


def test_the_listing_is_read_from_the_lines_own_tenure_not_the_tickers_first_bar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THROUGH THE REAL BUILDER. Without HOS's tenure the builder reads its first session as the
    other security's 2026-08-03 bar, asks for HLX as of 2026-08-02 and misses the rename (the
    defect: a reuse hides it). With the committed tenure row it reads 2026-09-02 and finds it."""
    _reused_hos(monkeypatch)
    _, _, asked = _build(monkeypatch, tmp_path / "without")
    assert load_aliases(tmp_path / "without" / "snapshots") == []
    assert ("HLX", date(2026, 8, 2)) in asked
    _build(monkeypatch, tmp_path / "with", tenures=[{
        "cik": _CIK, "evidence": "counterfactual", "first_session": "2026-09-02",
        "internal_id": _HOS, "prior_cik": "0000000009", "prior_id": "SEC-0000000009-HOS",
        "prior_last": "2026-08-03", "ticker": "HOS"}])
    [alias] = load_aliases(tmp_path / "with" / "snapshots")
    assert (alias.successor_id, alias.listed) == (_HOS, _LISTED)


def test_the_build_reconciles_identity_before_it_reads_a_rename() -> None:
    """ORDER IS THE CONTRACT: the reused ticker's bars leave the line and a re-domicile's history
    is carried (`identity.reconcile`) before a rename's listing is read, which reads the tenure."""
    import inspect

    from vinci import universe

    src = inspect.getsource(universe.build_universe)
    assert src.index("identity.reconcile(") < src.index("detect_renames(")
