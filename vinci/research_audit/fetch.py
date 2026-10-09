"""Acquire everything the audit needs from Polygon, once, into the netcache.

Order matters only for cost: metadata first (a ticker that fails identity is never downloaded),
then raw bars + dividends + splits per verified ticker, then the sector ETFs the verified tickers'
SIC codes actually call for. A re-run reads the cache and spends no calls.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from vinci.research_audit.classify import Availability, Direction, direction_of, listing_of
from vinci.research_audit.polygon import DailyBar, Dividend, PolygonAudit, Split
from vinci.research_audit.workbook import AuditWorkbook

#: Window the brief asks for. Bars before the plan window come from the grouped cache instead.
WINDOW_START = date(2023, 1, 1)

#: The session calendar AND the S&P 500 PROXY (labelled PROXY wherever used — never "S&P 500 TR").
CALENDAR_SYMBOL = "SPY"
#: USD MSCI World ETF — PROXY, used to test the CIQ MSCI World series' currency, never as the index.
WORLD_PROXY = "URTH"

#: Vanguard sector ETFs (series of Vanguard World Fund, CIK 52848) — the sector PROXIES. Chosen
#: over the SPDR family because they track MSCI US IMI 25/50 sector indexes (large + mid + small
#: caps): a stock's sector is read from WHICH of these funds' N-PORT holdings contains it
#: (``sectors.py``), and SPDR funds hold only S&P 500 members, which would leave TTD, MELI, DKNG,
#: TRU and others with no sourced sector at all.
SECTOR_ETFS = ("VAW", "VOX", "VPU", "VCR", "VDC", "VDE", "VFH", "VHT", "VIS", "VGT")

#: FX closes used ONLY to test which currency the CIQ 'MSCI World Net' series is denominated in.
FX_PAIRS = ("C:EURUSD", "C:GBPUSD", "C:USDJPY", "C:USDCHF", "C:USDINR")


@dataclass
class Fetched:
    end: date
    details: dict[str, dict[str, Any] | None] = field(default_factory=dict)
    details_as_of: dict[str, date] = field(default_factory=dict)
    live: dict[str, list[DailyBar]] = field(default_factory=dict)
    dividends: dict[str, list[Dividend]] = field(default_factory=dict)
    splits: dict[str, list[Split]] = field(default_factory=dict)
    searches: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    fx: dict[str, list[DailyBar]] = field(default_factory=dict)


def rated_us_tickers(wb: AuditWorkbook) -> dict[str, date]:
    """US-candidate tickers carrying a stated rating → the earliest day-granular public date."""
    out: dict[str, date] = {}
    for m in wb.mentions:
        if direction_of(m.rating) is Direction.NONDIRECTIONAL:
            continue
        if listing_of(m.ticker).availability is not Availability.POLYGON_CANDIDATE:
            continue
        pd = wb.publication(m.pub_id).public_date
        if pd is None:
            continue
        out[m.ticker] = min(out.get(m.ticker, pd), pd)
    return out


def rated_unavailable(wb: AuditWorkbook) -> dict[str, str]:
    """Rated non-US primary listings → company name (for the alternatives search)."""
    return {m.ticker: m.company for m in wb.mentions
            if direction_of(m.rating) is not Direction.NONDIRECTIONAL
            and listing_of(m.ticker).availability is Availability.UNAVAILABLE_POLYGON}


def _pull(pa: PolygonAudit, f: Fetched, symbol: str, as_of: date) -> None:
    f.details_as_of[symbol] = as_of
    f.details[symbol] = pa.details(symbol, as_of)
    if f.details[symbol] is None:
        return  # no identity → never downloaded
    f.live[symbol] = pa.daily_raw(symbol, WINDOW_START, f.end)
    f.dividends[symbol] = pa.dividends(symbol, WINDOW_START)
    f.splits[symbol] = pa.splits(symbol)


def fetch_all(wb: AuditWorkbook, pa: PolygonAudit, *, today: date,
              progress: Callable[[str], None] = print) -> Fetched:
    # 1. The calendar symbol fixes the last COMPLETED session: probe from yesterday, never today.
    cal = pa.daily_raw(CALENDAR_SYMBOL, WINDOW_START, today - timedelta(days=1))
    if not cal:
        raise RuntimeError(f"{CALENDAR_SYMBOL} returned no bars — cannot date the run")
    f = Fetched(end=cal[-1].day)
    progress(f"last completed session (from {CALENDAR_SYMBOL} bars): {f.end}")

    for sym in (CALENDAR_SYMBOL, WORLD_PROXY):
        _pull(pa, f, sym, WINDOW_START + timedelta(days=2))
        progress(f"benchmark proxy {sym}: {len(f.live.get(sym, []))} live bars")

    tickers = rated_us_tickers(wb)
    for i, (sym, pub) in enumerate(sorted(tickers.items()), 1):
        _pull(pa, f, sym, pub + timedelta(days=1))
        d = f.details[sym]
        progress(f"[{i}/{len(tickers)}] {sym}: "
                 + (f"{d.get('name')} {d.get('primary_exchange')} {d.get('type')} "
                    f"sic={d.get('sic_code')} live={len(f.live[sym])} "
                    f"divs={len(f.dividends[sym])} splits={len(f.splits[sym])}"
                    if d else "NO POLYGON DETAILS at as-of date"))

    for etf in SECTOR_ETFS:
        _pull(pa, f, etf, WINDOW_START + timedelta(days=2))
        progress(f"sector proxy {etf}: {len(f.live.get(etf, []))} live bars")

    for pair in FX_PAIRS:
        f.fx[pair] = pa.daily_raw(pair, WINDOW_START, f.end)
        progress(f"fx {pair}: {len(f.fx[pair])} live bars (currency test only)")

    for sym, company in sorted(rated_unavailable(wb).items()):
        f.searches[sym] = pa.search(company)
        progress(f"non-US {sym} ({company}): {len(f.searches[sym])} Polygon lines found "
                 f"(recorded, NOT substituted)")
    return f
