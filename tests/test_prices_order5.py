"""TeamNostra fix request 2, order 5, prices: RF-D5, RF-D10, RF-D11, RF-D12 — each behind a test
that fails on the code before it, on real data wherever the corpus holds it.

- RF-D5: a partial `refresh --aggs` after a split spliced two split bases. The anchor session is
  IESC's real 2026-08-05 bar, as the primary store held it and as Polygon re-served it after its
  2-for-1 (`tests/fixtures/splits_reference/restated_2026-08-05.json`).
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


def test_a_refusal_of_a_day_not_yet_closed_in_et_is_still_no_data() -> None:
    """THE OTHER NEGATIVE PIN (review of order 5): the plan refuses "today's data before end of
    day" until midnight ET — on 2026-10-29 at 03:38 UTC it refused 2026-10-28, local yesterday in
    IST (`docs/records/2026-10-29-monitor-day-2026-10-28.md`). `last_completed_session` probes
    ``today - 1`` and must step back past it, so that refusal is no data, never a lapse."""
    client = PolygonEodClient(_Refusing(), min_results=1)  # type: ignore[arg-type]
    for back in (0, 1):
        assert client.grouped_daily(date.today() - timedelta(days=back)) == {}


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
