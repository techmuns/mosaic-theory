"""TeamNostra fix request 2, order 5, prices: RF-D5, RF-D10, RF-D11, RF-D12 — each behind a test
that fails on the code before it, on real data wherever the corpus holds it.

- RF-D5: a partial `refresh --aggs` after a split spliced two split bases, at either edge of its
  window, and so did the grouped path at its right edge. The anchor session is IESC's real
  2026-08-05 bar, as the primary store held it and as Polygon re-served it after its 2-for-1
  (`tests/fixtures/splits_reference/restated_2026-08-05.json`).
- RF-D10: price features read bars after the reference date when no frontier was passed. The
  bars are GOOGL's committed Polygon bars (`tests/fixtures/prices/GOOGL.jsonl`).
- RF-D11: Tiingo's dividend-adjusted bars would carry each dividend twice. The rows are Tiingo's
  own: SPY over its 2026-09-18 ex-date, and GOOGL over its 2022-07-18 20-for-1.
- RF-D12: a 403 NOT_AUTHORIZED inside the plan's window read as a holiday. The refusal is the one
  Polygon served on 2026-11-11 for a date past the window, replayed verbatim.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.eod.client import (
    PLAN_HISTORY_DAYS,
    EodError,
    PolygonEodClient,
    RawBar,
    ingest_prices,
    ingest_prices_per_symbol,
)
from vinci.eod.dividends import growth
from vinci.eod.features import compute_price_features
from vinci.eod.tiingo import parse_tiingo_prices
from vinci.netcache import HttpError
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"


# --- RF-D5: a partial aggregates refresh is anchored -------------------------------------------

_IESC = next(p for p in json.loads((FIX / "splits_reference" / "restated_2026-08-05.json")
                                   .read_text())["pairs"] if p["ticker"] == "IESC")
_ANCHOR = date(2026, 8, 5)
_IDENT = Identity(internal_id="SEC-0001048268-IESC", issuer_id="ISS-IESC", cik="0001048268",
                  ticker="IESC", mic="XNAS", exchange="Nasdaq", eod_symbol="IESC",
                  name="IES Holdings")


def _held(d: date, *, scale: float = 1.0) -> PriceBar:
    h = _IESC["held"]
    return PriceBar(internal_id=_IDENT.internal_id, bar_date=d, open=h["open"] * scale,
                    high=h["high"] * scale, low=h["low"] * scale, close=h["close"] * scale,
                    volume=h["volume"] / scale, source="polygon-grouped")


class _Aggs:
    """Polygon's per-symbol aggregates over ``[start, end]``: the anchor session as Polygon served
    it after the split, and the sessions after it on that basis. Records each call's window."""

    def __init__(self, fresh: dict[str, float]) -> None:
        self.fresh = fresh
        self.calls: list[tuple[str, date, date]] = []

    def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
        self.calls.append((symbol, start, end))
        days = [_ANCHOR, date(2026, 8, 6), date(2026, 8, 7)]
        return [(d, RawBar(ticker=symbol, **self.fresh)) for d in days if start <= d <= end]


def _store_with_old_basis(path: Path) -> Store:
    store = Store(path)
    store.upsert_security(_IDENT)
    store.write_prices([_held(date(2026, 8, 3)), _held(date(2026, 8, 4)), _held(_ANCHOR)])
    return store


def test_a_partial_aggs_refresh_after_a_split_puts_the_held_bars_on_the_current_basis(
        tmp_path: Path) -> None:
    """THE DEFECT: refreshed from 08-06, the held 08-03..08-05 bars stayed on the pre-split basis
    beside new-basis bars — a ×0.5 step on 08-06, a day with no corporate action. Now the fetch
    reaches back to the anchor (08-05), the source's restatement is read off it (IESC's real 0.5),
    and every held bar through it is put on the current basis, named in the summary."""
    client = _Aggs(_IESC["fresh"])
    with _store_with_old_basis(tmp_path / "s.db") as store:
        summary = ingest_prices_per_symbol(client, store, [_IDENT], start=date(2026, 8, 6),
                                           end=date(2026, 8, 7), today=date(2026, 11, 11))
        hist = store.get_price_history(_IDENT.internal_id)
    assert client.calls == [("IESC", _ANCHOR, date(2026, 8, 7))]       # one call, from the anchor
    assert summary["restated"] == {"IESC": [pytest.approx(_IESC["factor"], rel=1e-6)]}
    closes = [b.close for b in hist]
    steps = [b / a for a, b in zip(closes, closes[1:], strict=False)]
    assert all(s == pytest.approx(1.0, rel=1e-6) for s in steps), steps   # no splice anywhere
    assert hist[0].source == "polygon-grouped+restated"


def test_a_price_only_move_at_the_anchor_restates_nothing_and_is_named(tmp_path: Path) -> None:
    """THE NEGATIVE PIN: the anchor re-served 4% higher with the SAME volume is a correction, not a
    split — nothing is rescaled, and the summary names it."""
    h = _IESC["held"]
    corrected = {k: h[k] * 1.04 for k in ("open", "high", "low", "close")} | {"volume": h["volume"]}
    with _store_with_old_basis(tmp_path / "s.db") as store:
        summary = ingest_prices_per_symbol(_Aggs(corrected), store, [_IDENT],
                                           start=date(2026, 8, 6), end=date(2026, 8, 7),
                                           today=date(2026, 11, 11))
        held = [b for b in store.get_price_history(_IDENT.internal_id) if b.bar_date <= _ANCHOR]
    assert summary["restated"] == {} and summary["price_only"] == {"IESC": [pytest.approx(1.04)]}
    assert all(b.close == h["close"] and b.source == "polygon-grouped" for b in held)


def test_an_anchor_beyond_the_plan_window_is_not_fetched_and_is_named(tmp_path: Path) -> None:
    """The plan cannot serve an anchor older than its window: the fetch starts at ``start`` and the
    name is listed as unanchored, never silently treated as checked."""
    client = _Aggs(_IESC["fresh"])
    later = _ANCHOR + timedelta(days=PLAN_HISTORY_DAYS + 30)
    with _store_with_old_basis(tmp_path / "s.db") as store:
        summary = ingest_prices_per_symbol(client, store, [_IDENT], start=date(2026, 8, 6),
                                           end=date(2026, 8, 7), today=later)
    assert client.calls == [("IESC", date(2026, 8, 6), date(2026, 8, 7))]
    assert summary["unanchored"] == ["IESC"] and summary["restated"] == {}


# --- RF-D5's RIGHT EDGE: the held bars after ``end`` (coordinator, 2026-11-11: "Fix both edges") --

_WEEK = [date(2026, 8, d) for d in range(3, 8)]          # Mon 08-03 .. Fri 08-07


class _Served:
    """The source after IESC's 2-for-1: every session of the week on the current basis, as
    Polygon re-served 08-05 — per symbol (``daily_bars``) and whole-market (``grouped_daily``)."""

    def __init__(self, fresh: dict[str, float]) -> None:
        self.fresh = fresh
        self.aggs: list[tuple[str, date, date]] = []
        self.grouped: list[date] = []

    def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
        self.aggs.append((symbol, start, end))
        return [(d, RawBar(ticker=symbol, **self.fresh)) for d in _WEEK if start <= d <= end]

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        self.grouped.append(day)
        return {"IESC": RawBar(ticker="IESC", **self.fresh)} if day in _WEEK else {}


def _store_holding_the_week(path: Path, *, current: tuple[date, ...] = ()) -> Store:
    """The week held on the PRE-split basis — except the ``current`` sessions, already on the
    current one (a later pull made after the split)."""
    store = Store(path)
    store.upsert_security(_IDENT)
    store.write_prices([_held(d, scale=_IESC["factor"] if d in current else 1.0) for d in _WEEK])
    return store


def _no_step(store: Store) -> list[float]:
    closes = [b.close for b in store.get_price_history(_IDENT.internal_id)]
    return [b / a for a, b in zip(closes, closes[1:], strict=False)]


def test_a_partial_aggs_refresh_puts_the_held_bars_after_its_end_on_the_current_basis(
        tmp_path: Path) -> None:
    """THE DEFECT, RIGHT EDGE: refreshed over 08-03..08-04, the window was rewritten on the current
    basis while the held 08-05..08-07 kept the pre-split one — a ×2 step on 08-05. Now the one call
    reaches through the last held bar, both ends after ``end`` read IESC's real 0.5, and every held
    bar after ``end`` is put on the current basis, named in the summary."""
    client = _Served(_IESC["fresh"])
    with _store_holding_the_week(tmp_path / "s.db") as store:
        summary = ingest_prices_per_symbol(client, store, [_IDENT], start=_WEEK[0], end=_WEEK[1],
                                           today=date(2026, 11, 11))
        steps = _no_step(store)
        hist = store.get_price_history(_IDENT.internal_id)
    assert client.aggs == [("IESC", _WEEK[0], _WEEK[-1])]               # still ONE call
    assert summary["restated"] == {"IESC": [pytest.approx(_IESC["factor"], rel=1e-6)]}
    assert all(x == pytest.approx(1.0, rel=1e-6) for x in steps), steps
    assert [b.source for b in hist] == ["polygon-aggs"] * 2 + ["polygon-grouped+restated"] * 3


def test_a_partial_grouped_refresh_puts_the_held_bars_after_its_end_on_the_current_basis(
        tmp_path: Path) -> None:
    """THE SAME DEFECT ON THE GROUPED PATH (a screen replay at an earlier reference date is one):
    the right edge is fetched at its first and last held sessions, one call each."""
    client = _Served(_IESC["fresh"])
    with _store_holding_the_week(tmp_path / "s.db") as store:
        summary = ingest_prices(client, store, [_IDENT], start=_WEEK[0],  # type: ignore[arg-type]
                                end=_WEEK[1])
        steps = _no_step(store)
    assert client.grouped == [_WEEK[0], _WEEK[1], _WEEK[2], _WEEK[-1]]
    assert summary["restated"] == {"IESC": [pytest.approx(_IESC["factor"], rel=1e-6)]}
    assert all(x == pytest.approx(1.0, rel=1e-6) for x in steps), steps


@pytest.mark.parametrize("path", ["aggs", "grouped"])
def test_held_bars_after_end_on_two_bases_are_restated_nothing_and_named(
        tmp_path: Path, path: str) -> None:
    """THE NEGATIVE PIN: 08-05 held pre-split, 08-06..08-07 already on the current basis (a pull
    after the split). One factor over all three would make a step at 08-06, not remove one — so
    nothing after ``end`` is rescaled, and the name is listed unanchored."""
    client = _Served(_IESC["fresh"])
    with _store_holding_the_week(tmp_path / "s.db", current=tuple(_WEEK[3:])) as store:
        before = {b.bar_date: b.close for b in store.get_price_history(_IDENT.internal_id)}
        if path == "aggs":
            summary = ingest_prices_per_symbol(client, store, [_IDENT], start=_WEEK[0],
                                               end=_WEEK[1], today=date(2026, 11, 11))
        else:
            summary = ingest_prices(client, store, [_IDENT], start=_WEEK[0],  # type: ignore[arg-type]
                                    end=_WEEK[1])
        after = {b.bar_date: b.close for b in store.get_price_history(_IDENT.internal_id)}
    assert summary["unanchored"] == ["IESC"] and summary["restated"] == {}
    assert all(after[d] == before[d] for d in _WEEK[2:])


def test_a_current_bar_between_two_stale_ones_after_end_is_never_rescaled(tmp_path: Path) -> None:
    """REVIEW, FINDING 2: 08-05 and 08-07 held pre-split, 08-06 already current — a store spliced
    before this fix. Both ends read 0.5, and one factor over all three would halve 08-06 a second
    time. The aggregates path already holds every served session through the last one, so it sets
    EVERY held bar after ``end`` beside the source: two bases there restate nothing, named."""
    client = _Served(_IESC["fresh"])
    with _store_holding_the_week(tmp_path / "s.db", current=(_WEEK[3],)) as store:
        before = {b.bar_date: b.close for b in store.get_price_history(_IDENT.internal_id)}
        summary = ingest_prices_per_symbol(client, store, [_IDENT], start=_WEEK[0], end=_WEEK[1],
                                           today=date(2026, 11, 11))
        after = {b.bar_date: b.close for b in store.get_price_history(_IDENT.internal_id)}
    assert summary["unanchored"] == ["IESC"] and summary["restated"] == {}
    assert all(after[d] == before[d] for d in _WEEK[2:])


def test_a_held_session_after_end_the_source_did_not_serve_restates_nothing(
        tmp_path: Path) -> None:
    """CODEX P1 ON #991: 08-05 and 08-07 re-served on the current basis, but 08-06 — held, between
    them — not served at all. Its basis cannot be read, so nothing after ``end`` is rescaled and the
    name is listed unanchored; it is never inferred from the bars around it."""

    class _Gap(_Served):
        def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
            return [(d, b) for d, b in super().daily_bars(symbol, start, end) if d != _WEEK[3]]

    with _store_holding_the_week(tmp_path / "s.db") as store:
        before = {b.bar_date: b.close for b in store.get_price_history(_IDENT.internal_id)}
        summary = ingest_prices_per_symbol(_Gap(_IESC["fresh"]), store, [_IDENT], start=_WEEK[0],
                                           end=_WEEK[1], today=date(2026, 11, 11))
        after = {b.bar_date: b.close for b in store.get_price_history(_IDENT.internal_id)}
    assert summary["unanchored"] == ["IESC"] and summary["restated"] == {}
    assert all(after[d] == before[d] for d in _WEEK[2:])


def test_a_name_whose_window_writes_nothing_has_neither_edge_restated(tmp_path: Path) -> None:
    """REVIEW, FINDING 3: every served session of the window falls before the id's own first
    session (`holders`), so nothing in ``[start, end]`` is written — and the held window stays on
    the old basis. Restating the edges around an unwritten window MAKES the two steps it exists to
    remove; the name raises as empty with every held bar as it was."""
    client = _Served(_IESC["fresh"])
    with _store_holding_the_week(tmp_path / "s.db") as store:
        before = [(b.bar_date, b.close) for b in store.get_price_history(_IDENT.internal_id)]
        with pytest.raises(EodError, match="NO bars"):
            ingest_prices_per_symbol(client, store, [_IDENT], start=_WEEK[1], end=_WEEK[2],
                                     first_sessions={_IDENT.internal_id: _WEEK[3]},
                                     today=date(2026, 11, 11))
        after = [(b.bar_date, b.close) for b in store.get_price_history(_IDENT.internal_id)]
    assert after == before


def test_a_grouped_replay_with_no_split_reads_only_the_first_session_after_end(
        tmp_path: Path) -> None:
    """REVIEW, FINDING 4: on the backed-up primary store a replay's names end on 15 to 18 distinct
    dates (the names that stopped trading), so reading every name's LAST session cost 18 to 24
    whole-market calls. The last session guards only a restatement; a name that reads none at its
    first session after ``end`` needs no second read."""
    client = _Served(_IESC["fresh"])
    with _store_holding_the_week(tmp_path / "s.db", current=tuple(_WEEK)) as store:
        summary = ingest_prices(client, store, [_IDENT], start=_WEEK[0],  # type: ignore[arg-type]
                                end=_WEEK[1])
    assert client.grouped == [_WEEK[0], _WEEK[1], _WEEK[2]]
    assert summary["restated"] == {} and summary["unanchored"] == []


def test_a_right_edge_the_grouped_source_did_not_serve_is_named(tmp_path: Path) -> None:
    """REVIEW, FINDING 10: the first held session after ``end`` absent from the whole-market day is
    never counted as checked: named unanchored, nothing restated."""

    class _Gap(_Served):
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            return {} if day == _WEEK[2] else super().grouped_daily(day)

    with _store_holding_the_week(tmp_path / "s.db") as store:
        summary = ingest_prices(_Gap(_IESC["fresh"]), store, [_IDENT],  # type: ignore[arg-type]
                                start=_WEEK[0], end=_WEEK[1])
    assert summary["unanchored"] == ["IESC"] and summary["restated"] == {}


def test_a_price_only_move_after_end_restates_nothing_and_is_named(tmp_path: Path) -> None:
    """REVIEW, FINDING 10: every held bar after ``end`` re-served 4% higher with the SAME volume is
    a correction, not a split — nothing after ``end`` is rescaled, and the summary names it."""
    h = _IESC["held"]
    corrected = {k: h[k] * 1.04 for k in ("open", "high", "low", "close")} | {"volume": h["volume"]}
    with _store_holding_the_week(tmp_path / "s.db") as store:
        summary = ingest_prices_per_symbol(_Served(corrected), store, [_IDENT], start=_WEEK[0],
                                           end=_WEEK[1], today=date(2026, 11, 11))
        after = [b for b in store.get_price_history(_IDENT.internal_id) if b.bar_date > _WEEK[1]]
    assert summary["restated"] == {} and summary["price_only"] == {"IESC": [pytest.approx(1.04)]}
    assert all(b.close == h["close"] and b.source == "polygon-grouped" for b in after)


def test_a_refresh_ending_on_the_last_held_session_reaches_no_further(tmp_path: Path) -> None:
    """THE ROUTINE CASE COSTS NOTHING: nothing is held after ``end``, so the call's window is
    ``[start, end]`` as before, and no edge is checked."""
    client = _Served(_IESC["fresh"])
    with _store_holding_the_week(tmp_path / "s.db") as store:
        summary = ingest_prices_per_symbol(client, store, [_IDENT], start=_WEEK[0], end=_WEEK[-1],
                                           today=date(2026, 11, 11))
    assert client.aggs == [("IESC", _WEEK[0], _WEEK[-1])]
    assert summary["restated"] == {} and summary["unanchored"] == []


# --- RF-D10: no bar after the reference date is read without a frontier -------------------------

def _googl_bars() -> list[PriceBar]:
    rows = [json.loads(ln) for ln in (FIX / "prices" / "GOOGL.jsonl").read_text().splitlines()
            if ln.strip()]
    return [PriceBar(internal_id="SEC-GOOGL", bar_date=date.fromisoformat(r["bar_date"]),
                     open=r["open"], high=r["high"], low=r["low"], close=r["close"],
                     volume=r["volume"], source=r["source"]) for r in rows]


def test_features_read_no_bar_after_the_reference_date_without_a_frontier() -> None:
    """THE DEFECT: GOOGL's committed bars run to 2026-10-16; read at 2026-06-30 with no frontier,
    `last` was the 10-16 close stamped PRESENT and the 3-month return ran past the reference date.
    Now the features are those of the bars cut at the reference date — the screen's own cut
    (`screens/run.py`), so a caller that cuts and one that does not read the same."""
    ref = date(2026, 6, 30)
    bars = _googl_bars()
    assert max(b.bar_date for b in bars) > ref + timedelta(days=60)      # the fixture runs past it
    uncut = compute_price_features(bars, reference_date=ref, staleness_days=5)
    cut = compute_price_features([b for b in bars if b.bar_date <= ref], reference_date=ref,
                                 staleness_days=5)
    assert uncut.last.as_of <= ref
    assert uncut == cut


def test_a_frontier_still_bounds_at_itself() -> None:
    """THE NEGATIVE PIN: a page's frontier (its price date) may run past its reference date by
    design, and the features still read through it."""
    ref, frontier = date(2026, 6, 30), date(2026, 7, 31)
    f = compute_price_features(_googl_bars(), reference_date=ref, staleness_days=40,
                               frontier=frontier)
    assert ref < f.last.as_of <= frontier


# --- RF-D11: Tiingo bars carry splits only, never dividends -------------------------------------

def _rows(name: str) -> list[dict[str, Any]]:
    return list(json.loads((FIX / name).read_text())["rows"])


def test_tiingo_bars_carry_no_dividend_so_a_total_return_counts_it_once() -> None:
    """THE DEFECT: SPY's 2026-09-18 ex-date paid $1.888834. Bars read from ``adjClose`` had already
    taken it out, so the price ratio over (09-17, 09-18] plus Tiingo's ``divCash`` counted it twice.
    On the split-only bars the total return is the unadjusted close ratio grown by the dividend
    once — what `eod.dividends` assumes of the store's bars."""
    rows = _rows("tiingo/spy_2026-09-18_exdate.json")
    bars = {b.bar_date: b for b in parse_tiingo_prices(rows, "IDX-SPY")}
    raw = {date.fromisoformat(r["date"][:10]): r for r in rows}
    a, b = date(2026, 9, 17), date(2026, 9, 18)
    yld = [(b, raw[b]["divCash"] / raw[b]["close"])]
    tr = bars[b].close / bars[a].close * growth(yld) - 1
    assert tr == pytest.approx(raw[b]["close"] / raw[a]["close"] * growth(yld) - 1, rel=1e-12)
    assert all(bars[d].close == raw[d]["close"] for d in raw)              # no split in the window


def test_tiingo_bars_divide_out_a_later_split() -> None:
    """THE SPLIT HALF, on GOOGL's real 2022-07-18 20-for-1: rows before the ex-date are divided by
    its factor (volume multiplied), the ex-date and after are as served — one basis throughout."""
    rows = _rows("splits_reference/tiingo_googl_2022-07.json")
    bars = parse_tiingo_prices(rows, "SEC-GOOGL")
    split = date(2022, 7, 18)
    for r, bar in zip(sorted(rows, key=lambda r: r["date"]), bars, strict=True):
        f = 20.0 if bar.bar_date < split else 1.0
        assert bar.close == pytest.approx(r["close"] / f)
        assert bar.volume == pytest.approx(r["volume"] * f)


def test_an_unreadable_tiingo_row_raises() -> None:
    row = dict(_rows("tiingo/spy_2026-09-18_exdate.json")[0])
    del row["splitFactor"]
    with pytest.raises(ValueError, match="unreadable Tiingo row"):
        parse_tiingo_prices([row], "IDX-SPY")


# --- RF-D12: a refusal inside the plan window is a failure, not a holiday -----------------------

#: Polygon's refusal, as served on 2026-11-11 for grouped-daily 2024-11-01 (740 days back)
_REFUSAL = ('Non-retryable 403 from https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/'
            '2024-11-01?adjusted=true: {"status":"NOT_AUTHORIZED","request_id":'
            '"574f75e834bf6df5cfccebb92041ae43","message":"Attempted to request data past '
            'historical entitlements. Please upgrade your plan at https://polygon.io/pricing"}')


class _Refusing:
    def get_json(self, url: str, **_kw: Any) -> Any:
        raise HttpError(_REFUSAL)


def test_a_refusal_inside_the_plan_window_raises() -> None:
    """THE DEFECT: every refused day read as a holiday — 22 refused sessions ingested as
    ``trading_days: 0`` with nothing raised. A date the plan serves, refused, now raises."""
    client = PolygonEodClient(_Refusing(), min_results=1)  # type: ignore[arg-type]
    with pytest.raises(EodError, match="inside the plan's"):
        client.grouped_daily(date.today() - timedelta(days=30))


def test_a_refusal_beyond_the_plan_window_is_still_no_data() -> None:
    """THE NEGATIVE PIN: a date past the window is the start of available history, as before."""
    client = PolygonEodClient(_Refusing(), min_results=1)  # type: ignore[arg-type]
    assert client.grouped_daily(date.today() - timedelta(days=PLAN_HISTORY_DAYS + 10)) == {}


def test_a_refusal_of_a_day_not_yet_closed_in_et_is_still_no_data(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """THE OTHER NEGATIVE PIN (review of order 5): the plan refuses "today's data before end of
    day" until midnight ET — on 2026-10-29 at 03:38 UTC it refused 2026-10-28, local yesterday in
    IST (`docs/records/2026-10-29-monitor-day-2026-10-28.md`). `last_completed_session` probes
    ``today - 1`` and must step back past it, so a refusal of the ET date still open — and of any
    later date — is no data, never a lapse. Pinned at that hour: ET's date is local yesterday."""
    from vinci.eod import client as client_mod
    monkeypatch.setattr(client_mod, "et_today", lambda: date.today() - timedelta(days=1),
                        raising=False)
    client = PolygonEodClient(_Refusing(), min_results=1)  # type: ignore[arg-type]
    for back in (0, 1):
        assert client.grouped_daily(date.today() - timedelta(days=back)) == {}


@pytest.mark.parametrize(("instant", "et_date", "refused", "raises"), [
    # THE REAL INCIDENT: 03:38 UTC on 2026-10-29 is 23:38 EDT on 10-28 — the session still open in
    # ET, so the plan's refusal of 10-28 is "today's data before end of day": no data
    ("2026-10-29T03:38:00+00:00", date(2026, 10, 28), date(2026, 10, 28), False),
    # JUST AFTER MIDNIGHT ET: 04:30 UTC on 10-29 is 00:30 EDT on 10-29 — 10-28 has closed, so the
    # same refusal of 10-28 is a lapsed plan or key, and raises (Codex round 2 on #991)
    ("2026-10-29T04:30:00+00:00", date(2026, 10, 29), date(2026, 10, 28), True),
])
def test_the_refusal_rule_reads_the_et_date_at_the_real_instants(
        monkeypatch: pytest.MonkeyPatch, instant: str, et_date: date, refused: date,
        raises: bool) -> None:
    """The ET date at each instant, and what Polygon's real 403 on ``refused`` then means. The
    plan's window is read against the local date, so ``today`` is pinned beside the instant."""
    from datetime import datetime as dt

    from vinci.eod import client as client_mod
    at = dt.fromisoformat(instant)
    assert client_mod.et_today(at) == et_date
    monkeypatch.setattr(client_mod, "et_today", lambda now=None: et_date)
    client = PolygonEodClient(_Refusing(), min_results=1)  # type: ignore[arg-type]
    if raises:
        with pytest.raises(EodError, match="inside the plan's"):
            client.grouped_daily(refused)
    else:
        assert client.grouped_daily(refused) == {}


def test_a_refusal_of_a_session_already_closed_in_et_raises(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """CODEX P2 ON #991, ROUND 2: the exemption covered local today AND yesterday for the whole
    day, so after midnight ET a refused CLOSED session — local yesterday, ET yesterday too — read
    as a holiday, and a revoked key on a one-day ingest wrote nothing and raised nothing. Only the
    ET date still open is exempt: here ET's date is local today, so yesterday's refusal is a
    lapse."""
    from vinci.eod import client as client_mod
    monkeypatch.setattr(client_mod, "et_today", lambda: date.today(), raising=False)
    client = PolygonEodClient(_Refusing(), min_results=1)  # type: ignore[arg-type]
    with pytest.raises(EodError, match="inside the plan's"):
        client.grouped_daily(date.today() - timedelta(days=1))
    assert client.grouped_daily(date.today()) == {}


def test_an_anchor_the_source_did_not_serve_is_named_unanchored(tmp_path: Path) -> None:
    """A held anchor the aggregates response does not carry was never set beside a served bar:
    the name is listed as unanchored, never silently counted as checked (review of order 5)."""

    class _NoAnchor(_Aggs):
        def daily_bars(self, symbol: str, start: date, end: date) -> list[tuple[date, RawBar]]:
            return [(d, b) for d, b in super().daily_bars(symbol, start, end) if d != _ANCHOR]

    client = _NoAnchor(_IESC["fresh"])
    with _store_with_old_basis(tmp_path / "s.db") as store:
        summary = ingest_prices_per_symbol(client, store, [_IDENT], start=date(2026, 8, 6),
                                           end=date(2026, 8, 7), today=date(2026, 11, 11))
    assert client.calls == [("IESC", _ANCHOR, date(2026, 8, 7))]
    assert summary["unanchored"] == ["IESC"] and summary["restated"] == {}


# --- RF-D5's remainder: the grouped LEFT edge names a name it could not check (#991's record) ----

class _GroupedAfterSplit:
    """Whole-market bars after IESC's 2-for-1, on the current basis, for ``served`` sessions."""

    def __init__(self, served: tuple[date, ...]) -> None:
        self.served = served
        self.grouped: list[date] = []

    def grouped_daily(self, day: date) -> dict[str, RawBar]:
        self.grouped.append(day)
        return {"IESC": RawBar(ticker="IESC", **_IESC["fresh"])} if day in self.served else {}


def test_a_grouped_left_edge_the_source_did_not_serve_is_named_unanchored(tmp_path: Path) -> None:
    """THE REMAINDER: refreshed over 08-06..08-07, the held bars through 08-05 are checked at their
    last held session (08-05). The source served IESC on 08-06 and 08-07 but not on 08-05, so the
    check had nothing to set beside the held bar — `restate_held` skipped the name, and it appeared
    in no list while its pre-split bars sat under new-basis ones. Now it is named ``unanchored``,
    as the right edge names the same case."""
    client = _GroupedAfterSplit((date(2026, 8, 6), date(2026, 8, 7)))
    with _store_with_old_basis(tmp_path / "s.db") as store:
        summary = ingest_prices(client, store, [_IDENT], start=date(2026, 8, 6),  # type: ignore[arg-type]
                                end=date(2026, 8, 7))
    assert _ANCHOR in client.grouped                      # the left edge was read, and was empty
    assert summary["unanchored"] == ["IESC"] and summary["restated"] == {}


def test_negative_a_grouped_left_edge_the_source_served_is_restated_not_named(
        tmp_path: Path) -> None:
    """(−) Served on 08-05, the same refresh restates the held bars and names nothing unanchored."""
    client = _GroupedAfterSplit((_ANCHOR, date(2026, 8, 6), date(2026, 8, 7)))
    with _store_with_old_basis(tmp_path / "s.db") as store:
        summary = ingest_prices(client, store, [_IDENT], start=date(2026, 8, 6),  # type: ignore[arg-type]
                                end=date(2026, 8, 7))
        steps = [b.close for b in store.get_price_history(_IDENT.internal_id)]
    assert summary["unanchored"] == []
    assert summary["restated"] == {"IESC": [pytest.approx(_IESC["factor"], rel=1e-6)]}
    assert all(b / a == pytest.approx(1.0, rel=1e-6)
               for a, b in zip(steps, steps[1:], strict=False))


def test_a_name_the_left_edge_skips_but_this_run_never_wrote_is_not_named(tmp_path: Path) -> None:
    """(−) A held name the source served on no session of the window got no new bars, so there is
    no splice to warn of: it is not named (the rule for names with no new bars)."""
    client = _GroupedAfterSplit(())
    with _store_with_old_basis(tmp_path / "s.db") as store:
        summary = ingest_prices(client, store, [_IDENT], start=date(2026, 8, 6),  # type: ignore[arg-type]
                                end=date(2026, 8, 7))
    assert summary["unanchored"] == [] and summary["bars_written"] == 0
