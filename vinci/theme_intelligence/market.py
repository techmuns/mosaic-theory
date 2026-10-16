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
- CONSENSUS REVISIONS — the next fiscal year's EPS consensus over 3 months, and how many analysts
  revised up and down, from the fund's committed dossiers (`data/dossiers/<TICKER>/dossier.json`,
  its CIQ Estimates export: the fund's dossier names only). Point in time: only when the export
  certainly existed by the date (the dossier was assembled by then) and is at most a month old;
- THE COMPANIES THE THESIS IMPLIES (the enrichment step's SEC-verified listings) — priced apart,
  labelled an EXTERNAL HYPOTHESIS, never counted.

DISPLAY ONLY. This is the ONE module of the package that reads prices or returns — the isolation
test pins that, and that nothing on the research-action path imports it. No rule reads a market
figure, so the rules stay set by face validity, never by what has paid. POINT IN TIME: no bar after
the date and no filing filed after it is read. A figure that cannot be measured is None with why —
never a guess.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal

from vinci.dossier.schemas import ForwardConsensus
from vinci.edgar.concepts import ConceptPoint
from vinci.eod.features import relative_return
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import MAX_EPS_AGE_DAYS, pe_current_and_percentile
from vinci.theme_intelligence.cards import exposure_instruments, listed_exposures
from vinci.theme_intelligence.schemas import (
    AffectedView,
    EnrichmentCandidate,
    ExposureMarket,
    Listing,
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
#: the fund's committed dossiers, whose CIQ Estimates layer carries the consensus path
DOSSIERS = Path("data/dossiers")
#: a consensus export older than this before the date is not "as of" it
REVISIONS_STALE_DAYS = 31
#: the EPS line read, in order of preference (the street's usual figure first)
REVISION_METRICS = ("EPS Normalized", "EPS (GAAP)")
#: a cik for a ticker (the SEC's ticker map), for the companies the thesis implies
CikOf = Callable[[str], str | None]
#: a one-day close-to-close move at least this size (up) or this size (down) is the size of a
#: share split — a 3-for-2 either way. The prices are split-ADJUSTED, so a real split never shows;
#: a move this size is either real news or an adjustment the source missed, and the row says so
#: (2026-10-16: Moderna +177% in one day, 2026-08-19 — unconfirmable from the SEC until its next
#: share count is filed)
SPLIT_SIZE_UP, SPLIT_SIZE_DOWN = 1.5, 2 / 3


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


def split_sized_moves(closes: Closes, as_of: date) -> list[str]:
    """Every one-day move in the closes held to the date the size of a share split — a value check
    beside the count checks: a series can be long enough and still be wrong."""
    held = _held(closes, as_of)
    return [f"a one-day move of {b[1] / a[1] - 1:+.0%} on {b[0].isoformat()} ({a[1]:,.2f} → "
            f"{b[1]:,.2f}) — real news, or a split the price source did not adjust: check before "
            f"reading this row" for a, b in zip(held, held[1:], strict=False)
            if b[1] / a[1] >= SPLIT_SIZE_UP or b[1] / a[1] <= SPLIT_SIZE_DOWN]


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


def consensus_revisions(ticker: str, as_of: date, dossiers: Path) -> MarketFigure:
    """How the street's EPS for the NEXT fiscal year moved over the 3 months to the CIQ export in
    the fund's dossier, with how many analysts revised it up and down — or None and why.

    POINT IN TIME, from what the dossier states: the export is dated (exactly, or a floor "≥" the
    true export is on or after) and the dossier was assembled at a known moment, so the export
    existed by then. It is read as of `as_of` only when it certainly existed by that date and is
    at most `REVISIONS_STALE_DAYS` old — never a later export read back, never a stale one."""
    path = dossiers / ticker / "dossier.json"
    if not path.is_file():
        return _not_held(f"no CIQ consensus held for {ticker} (the fund holds CIQ exports for its "
                         f"dossier names only)")
    doc = json.loads(path.read_text())
    if not doc.get("forward_consensus"):
        return _not_held(f"the fund's {ticker} dossier carries no consensus layer")
    fc = ForwardConsensus.model_validate(doc["forward_consensus"])
    raw = fc.as_of or ""
    floor = raw.startswith("≥")
    try:
        export = date.fromisoformat(raw.lstrip("≥"))
        assembled = datetime.fromisoformat(str(doc["assembled_at"])).date()
    except (KeyError, ValueError):
        return _not_held(f"the {ticker} dossier states no readable export date ({raw!r})")
    when = f"{'on or after ' if floor else ''}{export.isoformat()}"
    known_by = assembled if floor else export
    if as_of < known_by:
        return _not_held(f"the CIQ export ({when}; the fund's dossier assembled "
                         f"{assembled.isoformat()}) postdates {as_of.isoformat()} — reading it "
                         f"would look ahead")
    if (as_of - export).days > REVISIONS_STALE_DAYS:
        return _not_held(f"the CIQ export ({when}) is {(as_of - export).days} days older than "
                         f"{as_of.isoformat()}")
    metric = next((m for m in REVISION_METRICS if any(p.metric == m for p in fc.paths)), None)
    if metric is None or len(fc.periods) < 2:
        return _not_held(f"the {ticker} consensus carries no next-year EPS line")
    period = fc.periods[1]  # CIQ's forward years in order: FY+0, FY+1, FY+2
    line = next((p for p in fc.paths if p.metric == metric and p.period == period), None)
    v = {pt.months_ago: pt.value for pt in line.points} if line is not None else {}
    if 0 not in v or 3 not in v or v[3] <= 0:
        return _not_held(f"the {period} {metric} consensus has no positive 3-month-earlier "
                         f"figure to compare")
    rc = next((r for r in fc.revisions if r.metric == metric and r.period == period
               and r.window == "3m"), None)
    counts = (f"; {rc.up} analyst(s) revised up and {rc.down} down"
              + (f", of {rc.analysts}" if rc.analysts else "") if rc is not None
              else "; revision counts not held")
    return MarketFigure(
        value=v[0] / v[3] - 1.0, detail=f"{rc.up}↑ {rc.down}↓" if rc is not None else "",
        basis=(f"{period} {metric} consensus over the 3 months to the CIQ export ({when}; the "
               f"fund's dossier assembled {assembled.isoformat()}): {v[3]:g} → {v[0]:g}"
               + counts))


def _lines(listings: Sequence[Listing]) -> list[str]:
    """A company's lines in the card's order: its verified ones, or every one when none is."""
    verified = [x.ticker for x in listings if x.pit_status is PitStatus.VERIFIED]
    return verified or [x.ticker for x in listings]


def _ticker(listings: Sequence[Listing]) -> str | None:
    """The line priced: the first verified common-equity line of a company, a fund's first."""
    lines = _lines(listings)
    return lines[0] if lines else None


def _revisions(ticker: str, lines: Sequence[str], as_of: date, dossiers: Path) -> MarketFigure:
    """The consensus revisions of the company priced on `ticker`. The fund files a dossier under
    ONE of a company's share classes (Alphabet's under GOOGL, while GOOG leads its listings), and
    one company has one EPS consensus — so its other lines are tried, and the line read is said."""
    held = next((t for t in (ticker, *lines) if (dossiers / t / "dossier.json").is_file()), ticker)
    f = consensus_revisions(held, as_of, dossiers)
    if held == ticker:
        return f
    return f.model_copy(update={"basis": f"{f.basis} — read from the fund's {held} dossier, the "
                                         f"same company's other share class"})


def _row(name: str, ticker: str | None, kind: Kind, cik: str | None, *, as_of: date,
         bench: Closes | None, prices: PriceSource, eps: EpsSource, dossiers: Path,
         errors: list[str], lines: Sequence[str] = ()) -> ExposureMarket:
    if ticker is None:
        why = _not_held(f"{'an index' if kind == 'index' else 'a basket'} with no traded ticker "
                        f"named by the source — not priced")
        return ExposureMarket(name=name, ticker=None, kind=kind,
                              last_close=None, last_bar=None, vs_200d=why, from_52w_high=why,
                              rel_3m=why, rel_12m=why, pe=why, pe_percentile=why, revisions=why)
    if kind != "listed":
        revisions = _not_held("not applicable — a fund, not a company")
    else:
        try:
            revisions = _revisions(ticker, lines, as_of, dossiers)
        except Exception as exc:  # noqa: BLE001 — an unreadable dossier is said, never filled
            errors.append(f"{ticker}: the fund's dossier consensus could not be read — "
                          f"{type(exc).__name__}: {str(exc)[:120]}")
            revisions = _not_held("the fund's dossier consensus could not be read")
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
    elif cik is None:
        pe = pct = _not_held("no SEC CIK for this listing")
    else:
        try:
            points = eps(cik)
        except Exception as exc:  # noqa: BLE001 — absent XBRL is said, never substituted
            errors.append(f"{ticker}: SEC companyfacts failed — {type(exc).__name__}: "
                          f"{str(exc)[:120]}")
            pe = pct = _not_held("SEC companyfacts could not be read")
        else:
            pe, pct = pe_against_history(closes, points, as_of, ticker)
    return ExposureMarket(
        name=name, ticker=ticker, kind=kind,
        last_close=last[1] if last else None, last_bar=last[0] if last else None,
        vs_200d=vs_average(closes, as_of), from_52w_high=from_high(closes, as_of),
        rel_3m=rel["3m"], rel_12m=rel["12m"], pe=pe, pe_percentile=pct, revisions=revisions,
        warnings=tuple(split_sized_moves(closes, as_of)))


def market_context(av: AffectedView, *, thesis_id: str, version: int, run_id: str, as_of: date,
                   prices: PriceSource, eps: EpsSource,
                   hypotheses: Sequence[EnrichmentCandidate] = (), cik_of: CikOf | None = None,
                   dossiers: Path = DOSSIERS) -> tuple[MarketContext, list[str]]:
    """The market context of one thesis version as of `as_of`, and the requests that failed
    (each said on its row as well). Every exposure the count takes is a row, in the card's order:
    listed companies, then the instruments. `hypotheses`: the companies the thesis implies (the
    latest enrichment set) — priced apart, only those whose listing the SEC verified and that
    file as US issuers; `cik_of` gives their CIK for the P/E."""
    errors: list[str] = []
    try:
        bench: Closes | None = prices(BENCHMARK, as_of - timedelta(days=HISTORY_DAYS), as_of)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{BENCHMARK}: price request failed — {type(exc).__name__}: "
                      f"{str(exc)[:120]}")
        bench = None
    def row(name: str, ticker: str | None, kind: Kind, cik: str | None,
            lines: Sequence[str] = ()) -> ExposureMarket:
        return _row(name, ticker, kind, cik, as_of=as_of, bench=bench, prices=prices, eps=eps,
                    dossiers=dossiers, errors=errors, lines=lines)

    rows = [row(c.name_as_written, _ticker(c.listings), "listed", c.cik, _lines(c.listings))
            for c in listed_exposures(av)]
    for c in exposure_instruments(av):
        kind: Kind = ("fund" if c.resolution_status is ResolutionStatus.FUND
                      else "index" if c.resolution_status is ResolutionStatus.INDEX
                      else "basket")
        rows.append(row(c.name_as_written, _ticker(c.listings), kind, c.cik))
    implied = []
    for h in hypotheses:
        verified = [x for x in h.listings if x.pit_status is PitStatus.VERIFIED]
        ticker = _ticker(verified)
        if ticker is None or h.foreign_filer:
            continue
        implied.append(row(h.name, ticker, "listed", cik_of(ticker) if cik_of else None,
                           _lines(verified)))
    held = _held(bench or [], as_of)
    window = (f"prices held {held[0][0].isoformat()} to {held[-1][0].isoformat()}" if held
              else f"no {BENCHMARK} prices held")
    now = datetime.now(tz=UTC)
    key = f"{thesis_id}|{version}|{run_id}|{as_of}"
    cid = "MC-" + hashlib.sha256(key.encode()).hexdigest()[:14]
    return MarketContext(
        context_id=cid, thesis_id=thesis_id, thesis_version=version, run_id=run_id, as_of=as_of,
        created_at=now, benchmark=BENCHMARK, rows=tuple(rows), hypotheses=tuple(implied),
        source=(f"Polygon daily bars, split-adjusted closes ({window}); SEC XBRL annual diluted "
                f"EPS filed on or before each day; consensus revisions from the fund's CIQ "
                f"dossiers")), errors
