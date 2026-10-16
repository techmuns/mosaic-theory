"""MARKET CONTEXT — "is it priced?" (operator, 2026-10-16).

For a thesis's exposures — the listed companies whose listing is verified as of the date, and the
ETFs, indices and baskets the source attaches (`cards.listed_exposures`, `exposure_instruments`:
the names the count takes) — where each price stands AS OF a date:

- PRICE POSITION: the close against its 200-day average, and against its highest close of the 52
  weeks to the date;
- RETURN AGAINST THE BENCHMARK (SPY) over 3 and 12 months — the fund's
  `vinci.eod.features.relative_return`: both legs end on their common last bar;
- P/E AGAINST ITS OWN HISTORY — the fund's `vinci.screens.assemble.pe_current_and_percentile`: only
  annual diluted EPS filed on or before each day. Over the price history the plan serves (two
  years: Polygon, 2026-10-16), whose dates are stated beside every value;
- CONSENSUS REVISIONS: NOT HELD — no point-in-time estimates source exists here (the fund's CIQ
  exports are snapshots, for its dossier names only).

DISPLAY ONLY. This is the ONE module of the package that reads prices or returns — the isolation
test pins that, and that nothing on the research-action path imports it. No rule reads a market
figure, so the rules stay set by face validity, never by what has paid. POINT IN TIME: no bar after
the date and no filing filed after it is read. A figure that cannot be measured is None with why —
never a guess.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from vinci.edgar.concepts import ConceptPoint
from vinci.eod.features import relative_return
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import MAX_EPS_AGE_DAYS, pe_current_and_percentile
from vinci.theme_intelligence.cards import exposure_instruments, listed_exposures
from vinci.theme_intelligence.schemas import (
    AffectedCompany,
    AffectedView,
    ExposureMarket,
    MarketContext,
    MarketFigure,
    PitStatus,
    ResolutionStatus,
)

#: daily (date, split-adjusted close) of one ticker over [start, end], oldest first
Closes = list[tuple[date, float]]
PriceSource = Callable[[str, date, date], Closes]
#: a company's annual diluted EPS points (SEC XBRL), by CIK
EpsSource = Callable[[str], list[ConceptPoint]]
Kind = Literal["listed", "fund", "index", "basket"]

BENCHMARK = "SPY"
#: the 200-day average reads the 200 daily closes up to the date
AVERAGE_DAYS = 200
#: a 52-week window is covered when its first close falls within this many days of its start (a
#: weekend and a holiday)
WINDOW_SLACK_DAYS = 7
#: no figure is measured from a last close older than this before the date
STALE_DAYS = 7
#: the price history requested: the fund's P/E range (`pe_current_and_percentile`, five years)
HISTORY_DAYS = 1825
RETURN_WINDOWS = {"3m": 91, "12m": 365}
NOT_HELD_REVISIONS = ("not held — no point-in-time consensus source here (the fund's CIQ exports "
                      "are snapshots, for its dossier names only)")


def polygon_prices() -> PriceSource:
    """Polygon daily bars (the fund's client: its key, pacing and on-disk cache)."""
    from vinci.eod.client import PolygonEodClient

    client = PolygonEodClient.from_config()

    def get(symbol: str, start: date, end: date) -> Closes:
        return [(d, b.close) for d, b in client.daily_bars(symbol, start, end)]
    return get


def edgar_eps() -> EpsSource:
    """Annual diluted EPS from SEC XBRL companyfacts (the fund's client and concept reader)."""
    from vinci.edgar.client import EdgarClient
    from vinci.edgar.concepts import extract_points

    edgar = EdgarClient.from_config()

    def get(cik: str) -> list[ConceptPoint]:
        return [p for p in extract_points(edgar.companyfacts(cik), "eps_diluted") if p.is_annual]
    return get


def _held(closes: Closes, as_of: date) -> Closes:
    """The closes on or before the date, oldest first — a later bar is never read."""
    return sorted((d, c) for d, c in closes if d <= as_of and c > 0)


def _not_held(why: str) -> MarketFigure:
    return MarketFigure(value=None, basis=f"not held — {why}")


def _fresh(held: Closes, as_of: date) -> tuple[date, float] | None:
    return held[-1] if held and (as_of - held[-1][0]).days <= STALE_DAYS else None


def vs_average(closes: Closes, as_of: date) -> MarketFigure:
    """The close against the average of the 200 daily closes up to the date."""
    held = _held(closes, as_of)
    last = _fresh(held, as_of)
    if last is None:
        return _not_held(f"no close within {STALE_DAYS} days before {as_of.isoformat()}")
    if len(held) < AVERAGE_DAYS:
        return _not_held(f"{len(held)} daily closes held to {as_of.isoformat()} — the average "
                         f"needs {AVERAGE_DAYS}")
    win = held[-AVERAGE_DAYS:]
    avg = sum(c for _, c in win) / len(win)
    return MarketFigure(value=last[1] / avg - 1.0,
                        basis=f"close {last[0].isoformat()} against the average of the "
                              f"{AVERAGE_DAYS} daily closes {win[0][0].isoformat()} to "
                              f"{win[-1][0].isoformat()}")


def from_high(closes: Closes, as_of: date) -> MarketFigure:
    """The close against the highest CLOSE of the 52 weeks to the date (closes, never intraday
    highs: the panel compares closes throughout)."""
    held = _held(closes, as_of)
    last = _fresh(held, as_of)
    if last is None:
        return _not_held(f"no close within {STALE_DAYS} days before {as_of.isoformat()}")
    start = as_of - timedelta(days=365)
    win = [(d, c) for d, c in held if d > start]
    if (win[0][0] - start).days > WINDOW_SLACK_DAYS:
        return _not_held(f"closes held from {held[0][0].isoformat()} — the 52 weeks to "
                         f"{as_of.isoformat()} start {start.isoformat()}")
    hd, hc = max(win, key=lambda x: (x[1], x[0]))
    return MarketFigure(value=last[1] / hc - 1.0,
                        basis=f"close {last[0].isoformat()} against the highest close of the 52 "
                              f"weeks to {as_of.isoformat()} ({hc:,.2f} on {hd.isoformat()})")


def _bars(ticker: str, closes: Closes) -> list[PriceBar]:
    return [PriceBar(internal_id=ticker, bar_date=d, open=c, high=c, low=c, close=c, volume=0.0,
                     source="polygon-aggregates") for d, c in closes if c > 0]


def against(name: Closes, bench: Closes, as_of: date, days: int, ticker: str) -> MarketFigure:
    """The name's return less the benchmark's over `days` to the date, in fraction points — both
    legs ending on their common last bar (the fund's `relative_return`, whose note states the
    window and each side's frontier)."""
    df = relative_return(_bars(ticker, _held(name, as_of)), _bars(BENCHMARK, _held(bench, as_of)),
                         reference_date=as_of, lookback_days=days)
    if df.value is None:
        return _not_held(df.note or "no coverage over the window")
    return MarketFigure(value=df.value, basis=df.note or "")


def pe_against_history(closes: Closes, eps: list[ConceptPoint], as_of: date,
                       ticker: str) -> tuple[MarketFigure, MarketFigure]:
    """(P/E, its percentile among its own daily P/Es over the prices held) — the fund's
    `pe_current_and_percentile`, which reads only EPS filed by each day. The window stated is the
    one the prices cover, never the helper's nominal five years."""
    held = _held(closes, as_of)
    if not held:
        none = _not_held(f"no close held to {as_of.isoformat()}")
        return none, none
    # THE HELPER'S OWN WINDOW RULE, ON THE PRICES HELD: a share-basis change refuses the range
    # when it falls inside "the range plus the EPS reach-back". Its range is nominally five years;
    # the prices held here start later, so the periods they can consume start at the first held
    # close less the reach-back — a 2022 split refused AMZN's and GOOGL's two-year range
    # (2026-10-16) though no observation in it divides across the split.
    consumed = held[0][0] - timedelta(days=MAX_EPS_AGE_DAYS)
    pe, pct = pe_current_and_percentile(_bars(ticker, held),
                                        [p for p in eps if p.period_end >= consumed],
                                        reference_date=as_of)
    pe_f = (MarketFigure(value=pe.value, basis=pe.note or "") if pe.value is not None
            else _not_held(pe.note or "no P/E"))
    first = max(held[0][0], as_of - timedelta(days=HISTORY_DAYS))
    pct_f = (MarketFigure(value=pct.value,
                          basis=f"share of its daily P/Es from {first.isoformat()} to "
                                f"{as_of.isoformat()} (the prices held) at or below today's")
             if pct.value is not None else _not_held(pct.note or "no P/E history"))
    return pe_f, pct_f


def _ticker(c: AffectedCompany) -> str | None:
    """The line priced: the first verified common-equity line of a company, a fund's first."""
    verified = [x.ticker for x in c.listings if x.pit_status is PitStatus.VERIFIED]
    lines = verified or [x.ticker for x in c.listings]
    return lines[0] if lines else None


def _row(c: AffectedCompany, kind: Kind, *, as_of: date, bench: Closes | None,
         prices: PriceSource, eps: EpsSource, errors: list[str]) -> ExposureMarket:
    ticker = _ticker(c)
    revisions = MarketFigure(value=None, basis=NOT_HELD_REVISIONS)
    if ticker is None:
        why = _not_held(f"{'an index' if kind == 'index' else 'a basket'} with no traded ticker "
                        f"named by the source — not priced")
        return ExposureMarket(name=c.name_as_written, ticker=None, kind=kind,
                              last_close=None, last_bar=None, vs_200d=why, from_52w_high=why,
                              rel_3m=why, rel_12m=why, pe=why, pe_percentile=why,
                              revisions=revisions)
    try:
        closes = prices(ticker, as_of - timedelta(days=HISTORY_DAYS), as_of)
    except Exception as exc:  # noqa: BLE001 — a failed request is said, never filled
        errors.append(f"{ticker}: price request failed — {type(exc).__name__}: {str(exc)[:120]}")
        closes = []
    held = _held(closes, as_of)
    last = _fresh(held, as_of)
    if bench is None:
        rel = {k: _not_held(f"{BENCHMARK} price request failed") for k in RETURN_WINDOWS}
    else:
        rel = {k: against(closes, bench, as_of, d, ticker) for k, d in RETURN_WINDOWS.items()}
    if kind != "listed":
        pe = pct = _not_held("not applicable — a fund, not a company")
    elif c.cik is None:
        pe = pct = _not_held("no SEC CIK for this listing")
    else:
        try:
            points = eps(c.cik)
        except Exception as exc:  # noqa: BLE001 — absent XBRL is said, never substituted
            errors.append(f"{ticker}: SEC companyfacts failed — {type(exc).__name__}: "
                          f"{str(exc)[:120]}")
            pe = pct = _not_held("SEC companyfacts could not be read")
        else:
            pe, pct = pe_against_history(closes, points, as_of, ticker)
    return ExposureMarket(
        name=c.name_as_written, ticker=ticker, kind=kind,
        last_close=last[1] if last else None, last_bar=last[0] if last else None,
        vs_200d=vs_average(closes, as_of), from_52w_high=from_high(closes, as_of),
        rel_3m=rel["3m"], rel_12m=rel["12m"], pe=pe, pe_percentile=pct, revisions=revisions)


def market_context(av: AffectedView, *, thesis_id: str, version: int, run_id: str, as_of: date,
                   prices: PriceSource, eps: EpsSource
                   ) -> tuple[MarketContext, list[str]]:
    """The market context of one thesis version as of `as_of`, and the requests that failed
    (each said on its row as well). Every exposure the count takes is a row, in the card's order:
    listed companies, then the instruments."""
    errors: list[str] = []
    try:
        bench: Closes | None = prices(BENCHMARK, as_of - timedelta(days=HISTORY_DAYS), as_of)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{BENCHMARK}: price request failed — {type(exc).__name__}: "
                      f"{str(exc)[:120]}")
        bench = None
    rows = [_row(c, "listed", as_of=as_of, bench=bench, prices=prices, eps=eps, errors=errors)
            for c in listed_exposures(av)]
    for c in exposure_instruments(av):
        kind: Kind = ("fund" if c.resolution_status is ResolutionStatus.FUND
                      else "index" if c.resolution_status is ResolutionStatus.INDEX
                      else "basket")
        rows.append(_row(c, kind, as_of=as_of, bench=bench, prices=prices, eps=eps,
                         errors=errors))
    held = _held(bench or [], as_of)
    window = (f"prices held {held[0][0].isoformat()} to {held[-1][0].isoformat()}" if held
              else f"no {BENCHMARK} prices held")
    now = datetime.now(tz=UTC)
    key = f"{thesis_id}|{version}|{run_id}|{as_of}"
    cid = "MC-" + hashlib.sha256(key.encode()).hexdigest()[:14]
    return MarketContext(
        context_id=cid, thesis_id=thesis_id, thesis_version=version, run_id=run_id, as_of=as_of,
        created_at=now, benchmark=BENCHMARK, rows=tuple(rows),
        source=(f"Polygon daily bars, split-adjusted closes ({window}); SEC XBRL annual diluted "
                f"EPS filed on or before each day; consensus revisions not held")), errors
