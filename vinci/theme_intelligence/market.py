"""MARKET CONTEXT — "is it priced?" (operator, 2026-10-16).

For a thesis's exposures — the listed companies whose listing is verified as of the date, and the
ETFs, indices and baskets the source attaches (`cards.listed_exposures`, `exposure_instruments`:
the names the count takes) — where each price stands AS OF a date:

- PRICE POSITION: the close against its 200-day average, and against its highest close of the 52
  weeks to the date;
- RETURN AGAINST THE BENCHMARK (SPY) over 3 and 12 months — the fund's
  `vinci.eod.features.relative_return`: both legs end on their common last bar;
- P/E AGAINST ITS OWN HISTORY — the fund's `vinci.screens.assemble.pe_current_and_percentile`: only
  annual diluted EPS filed on or before each day. FIVE YEARS where it can be built: Tiingo's raw
  closes and split factors before Polygon's two years (`deep_history`), rebased onto Polygon's
  prices over their overlap and refused when the two disagree; else the two years Polygon serves.
  The window is stated beside every value;
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
from typing import Any, Literal

from vinci.dossier.schemas import ForwardConsensus
from vinci.edgar.concepts import ConceptPoint
from vinci.eod.features import relative_return
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import (
    MAX_EPS_AGE_DAYS,
    annual_eps_point_as_of,
    pe_current_and_percentile,
)
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
#: (date, RAW close, split factor) of one ticker — Tiingo's daily rows; None: not fetched this run
DeepRow = tuple[date, float, float]
DeepSource = Callable[[str, date, date], list[DeepRow] | None]
#: Tiingo's free plan allows 50 requests an hour (tiingo.com/about/pricing, 2026-10-16): a run
#: fetches at most this many histories it does not already hold; the rest wait for a later run
TIINGO_PER_RUN = 45
#: before Tiingo's history is joined to Polygon's, the two must agree over an overlap of at least
#: OVERLAP_MIN_DAYS trading days, every day's price ratio within OVERLAP_TOLERANCE of the median —
#: the join is a check, not a splice
OVERLAP_MIN_DAYS = 20
OVERLAP_TOLERANCE = 0.005
#: the overlap requested: the Tiingo span runs this far past Polygon's first close
OVERLAP_CALENDAR_DAYS = 60
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


def tiingo_deep(cache_dir: Path, *, budget: int = TIINGO_PER_RUN) -> DeepSource:
    """Tiingo daily rows — RAW closes and split factors, never its dividend-adjusted close (a P/E
    divides a price by an as-filed EPS; a dividend adjustment would lower every older price). The
    key travels in a header (never in a URL, the cache or a log). A span is quarter-aligned and in
    the past, so it is cached for good; at most `budget` spans not already held are requested."""
    from vinci.config import require_env, sec_user_agent
    from vinci.netcache import CachedHttp

    http = CachedHttp(cache_dir=cache_dir, user_agent=sec_user_agent(), min_interval_sec=1.0,
                      namespace="tiingo",
                      extra_headers={"Authorization": f"Token {require_env('TIINGO_API_KEY')}"})
    spent = [0]

    def get(symbol: str, start: date, end: date) -> list[DeepRow] | None:
        # Tiingo spells a share class with a hyphen (brk-b), where Polygon and the SEC use a dot
        url = f"https://api.tiingo.com/tiingo/daily/{symbol.lower().replace('.', '-')}/prices"
        params = {"startDate": start.isoformat(), "endDate": end.isoformat(), "format": "json"}
        if http.fetched_at(url, params=params) is None:
            if spent[0] >= budget:
                return None
            spent[0] += 1
        rows = http.get_json(url, ttl_seconds=None, params=params)
        return [(date.fromisoformat(str(r["date"])[:10]), float(r["close"]),
                 float(r.get("splitFactor") or 1.0)) for r in rows]
    return get


def _quarter_start(d: date) -> date:
    return date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def _quarter_end(d: date) -> date:
    q = _quarter_start(d)
    nxt = date(q.year + (q.month == 10), 1 if q.month == 10 else q.month + 3, 1)
    return nxt - timedelta(days=1)


def split_adjusted(rows: Sequence[DeepRow]) -> Closes:
    """Raw closes on the share basis of the LAST row: a close before a split is divided by every
    split factor after it (a split's own day already trades on the new basis)."""
    out: Closes = []
    factor = 1.0
    for d, close, split in sorted(rows, reverse=True):
        out.append((d, close / factor))
        factor *= split if split > 0 else 1.0
    return out[::-1]


def deep_history(ticker: str, recent: Closes, as_of: date,
                 deep: DeepSource) -> tuple[Closes | None, str]:
    """(five years of closes to the date, on Polygon's basis, and how they were joined) — or
    (None, why). Tiingo's split-adjusted closes before Polygon's first are rebased by the median
    price ratio over the overlap, and REFUSED unless every overlapping day agrees within
    `OVERLAP_TOLERANCE` (a split inside the overlap, or two sources that disagree)."""
    held = _held(recent, as_of)
    if not held:
        return None, "no recent closes to join"
    need = as_of - timedelta(days=HISTORY_DAYS)
    if (held[0][0] - need).days <= WINDOW_SLACK_DAYS:
        return held, "the recent prices already cover five years"
    end = min(_quarter_end(held[0][0] + timedelta(days=OVERLAP_CALENDAR_DAYS)), as_of)
    rows = deep(ticker, _quarter_start(need), end)
    if rows is None:
        return None, ("not fetched this run — Tiingo's free plan allows 50 requests an hour; a "
                      "later run fetches it")
    adj = split_adjusted([r for r in rows if r[0] <= end and r[1] > 0])
    poly = dict(held)
    ratios = sorted(poly[d] / c for d, c in adj if d in poly)
    if len(ratios) < OVERLAP_MIN_DAYS:
        return None, (f"Tiingo and Polygon overlap on {len(ratios)} day(s) — {OVERLAP_MIN_DAYS} "
                      f"are needed to check the join")
    med = ratios[len(ratios) // 2]
    if max(abs(r / med - 1) for r in ratios) > OVERLAP_TOLERANCE:
        return None, (f"Tiingo and Polygon disagree over their {len(ratios)}-day overlap "
                      f"(price ratios {ratios[0]:.4f} to {ratios[-1]:.4f}) — not joined")
    early = [(d, c * med) for d, c in adj if need - timedelta(days=WINDOW_SLACK_DAYS) <= d
             < held[0][0]]
    if not early or (early[0][0] - need).days > WINDOW_SLACK_DAYS:
        return None, f"Tiingo holds no closes for {ticker} from {need.isoformat()}"
    return early + held, (f"Tiingo split-adjusted closes {early[0][0].isoformat()} to "
                          f"{early[-1][0].isoformat()}, rebased onto Polygon's over "
                          f"{len(ratios)} overlapping days (ratio {med:.4f}); Polygon from "
                          f"{held[0][0].isoformat()}")


def edgar_eps(as_of: date | None = None) -> EpsSource:
    """Annual diluted EPS from SEC XBRL companyfacts (the fund's client and concept reader), with
    the cover-page share counts from the same response (concept "shares") — the per-share basis
    check reads them. ``as_of`` is the run's date: the EPS is read in the currency the filer
    reported in on it (`concepts.reporting_currency`)."""
    from vinci.edgar.client import EdgarClient

    edgar = EdgarClient.from_config()

    def get(cik: str) -> list[ConceptPoint]:
        return desk_points(edgar.companyfacts(cik), as_of)
    return get


def desk_points(facts: dict[str, Any], as_of: date | None) -> list[ConceptPoint]:
    """The annual diluted EPS and the cover-page share counts :func:`edgar_eps` serves.

    THE SHARE COUNTS ARE DATED AS COUNTED (Phase 2 C2, audit X1(a)): one tagged after its own
    filing reads at its filing day, an upper bound, marked `SHARES_FILED` so it prints "filed";
    one its own filing contradicts is kept, marked `SHARES_REFUSED`, so `basis_breaks` names it
    and never measures across it (review of #875) — no cover is fetched outside an assembly. THM's
    2023 count, tagged 2033, sorted last in `basis_breaks`' consecutive pairs."""
    from vinci.edgar.concepts import REPORTING, extract_points
    from vinci.edgar.cover_count import date_counts

    # the filer's own currency as of the run's date: the P/E level is withheld unless it is
    # USD, and the percentile ranks one series in one currency (pe_current_and_percentile)
    eps = [p for p in extract_points(facts, "eps_diluted", currency=REPORTING, as_of=as_of)
           if p.is_annual]
    counts = date_counts(extract_points(facts, "shares"), facts, read=lambda _: None)
    return eps + [c.point.model_copy(update={"concept": SHARES_REFUSED if c.refused
                                             else SHARES_FILED if c.bound else "shares"})
                  for c in counts]


#: a share count its own filing contradicts (`vinci.edgar.cover_count`), and one read at its
#: filing day because it was tagged after it — kept beside the others so neither is silent
SHARES_REFUSED = "shares (refused)"
SHARES_FILED = "shares (filed)"
_SHARES = ("shares", SHARES_FILED, SHARES_REFUSED)


#: a per-share figure restated by this factor or more (either way), or a share count that moves by
#: it between two cover pages, is a change of per-share BASIS — a split, or an issuance or
#: correction that size. Far above cents rounding: the fund's split test needs two restated
#: periods to agree within 2%, and NVDA's 10-for-1 (FY2023 1.74 → 0.17 is ×10.24, FY2024 11.93 →
#: 1.19 is ×10.03) missed it by 0.05% (2026-10-16)
BASIS_BREAK = 1.5


BreakKind = Literal["eps", "shares"]


def basis_breaks(points: Sequence[ConceptPoint], since: date,
                 as_of: date) -> list[tuple[BreakKind, str]]:
    """Every change of per-share basis the filings known by `as_of` show after `since`, as (kind,
    words): an annual EPS period a later filing restated by `BASIS_BREAK` or more ("eps"), and a
    share count that moved by it between consecutive cover pages ("shares"). Callers branch on the
    KIND, never on the words."""
    known = [p for p in points if p.filed <= as_of]
    out: list[tuple[BreakKind, str]] = []
    by: dict[date, list[ConceptPoint]] = {}
    for p in known:
        if p.concept not in _SHARES and p.is_annual and p.period_end >= since:
            by.setdefault(p.period_end, []).append(p)
    for end, ps in sorted(by.items()):
        filed = sorted({p.filed for p in ps})
        if len(filed) < 2:
            continue
        a = max(abs(p.value) for p in ps if p.filed == filed[0])
        b = max(abs(p.value) for p in ps if p.filed == filed[-1])
        if a and b and max(a / b, b / a) >= BASIS_BREAK:
            out.append(("eps", f"the year ending {end.isoformat()}: EPS {a:g} as first filed, "
                               f"{b:g} as filed {filed[-1].isoformat()} "
                               f"(×{max(a / b, b / a):.1f})"))
    shares = sorted({(p.period_end, p.value, p.concept) for p in known
                     if p.concept in _SHARES and p.value > 0})
    named: set[date] = set()
    for (d0, v0, c0), (d1, v1, c1) in zip(shares, shares[1:], strict=False):
        if d1 < since:
            continue
        # A REFUSED COUNT IS NAMED, NEVER MEASURED ACROSS (review of #875): dropped, its neighbours
        # were compared and a basis move it carried was invisible to the P/E guard — and a 1.5x
        # move IS past the cross-check, so a late-tagged one is refused by construction
        for d, v, c in ((d0, v0, c0), (d1, v1, c1)):
            if c == SHARES_REFUSED and d not in named:
                named.add(d)
                out.append(("shares", f"shares outstanding {v:,.0f} {_on(d, c)} contradicted by "
                                      f"its own filing — UNKNOWN, so no per-share basis is read "
                                      f"across it"))
        if SHARES_REFUSED in (c0, c1):
            continue
        if max(v1 / v0, v0 / v1) >= BASIS_BREAK:
            out.append(("shares", f"shares outstanding {v0:,.0f} {_on(d0, c0)}, "
                                  f"{v1:,.0f} {_on(d1, c1)} "
                                  f"(×{max(v1 / v0, v0 / v1):.1f})"))
    return out


def _on(d: date, concept: str) -> str:
    """A share count's date as the desk prints it — a filing-day bound says so (nit 7)."""
    return f"filed {d.isoformat()}" if concept == SHARES_FILED else f"on {d.isoformat()}"


def _held(closes: Closes, as_of: date) -> Closes:
    """The closes on or before the date, oldest first — a later bar is never read."""
    return sorted((d, c) for d, c in closes if d <= as_of and c > 0)


def _not_held(why: str) -> MarketFigure:
    return MarketFigure(value=None, basis=f"not held — {why}", why=why)


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


def pe_five_or_two(closes: Closes, eps: list[ConceptPoint], as_of: date, ticker: str,
                   deep: DeepSource | None,
                   errors: list[str] | None = None) -> tuple[MarketFigure, MarketFigure]:
    """The P/E and its percentile over FIVE years when they can be joined and the fund's rule
    accepts the range (it refuses one a share-basis change runs through); else over the two years
    Polygon serves — and the percentile says which, and why five were not used. A failed Tiingo
    request is said as that (and added to `errors`), never as a missing key."""
    if deep is None:
        why = "five years not held — no Tiingo key configured"
    else:
        try:
            five, how = deep_history(ticker, closes, as_of, deep)
        except Exception as exc:  # noqa: BLE001 — a failed request is said, never filled
            if errors is not None:
                errors.append(f"{ticker}: Tiingo history failed — {type(exc).__name__}: "
                              f"{str(exc)[:120]}")
            five, how = None, f"the Tiingo request failed ({type(exc).__name__})"
        if five is not None:
            pe5, pct5 = pe_against_history(five, eps, as_of, ticker, joined=how)
            if pct5.value is not None:
                return pe5, pct5.model_copy(update={"detail": "5y"})
            why = f"five years not used — {pct5.why}"
        else:
            why = f"five years not held — {how}"
    pe, pct = pe_against_history(closes, eps, as_of, ticker)
    return pe, pct.model_copy(update={"basis": f"{pct.basis}; {why}",
                                      "detail": "2y" if pct.value is not None else ""})


def pe_against_history(closes: Closes, eps: list[ConceptPoint], as_of: date,
                       ticker: str, *, joined: str = "") -> tuple[MarketFigure, MarketFigure]:
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
    annual = [p for p in eps if p.concept == "eps_diluted"]
    pe, pct = pe_current_and_percentile(_bars(ticker, held),
                                        [p for p in annual if p.period_end >= consumed],
                                        reference_date=as_of)
    pe_f = (MarketFigure(value=pe.value, basis=pe.note or "") if pe.value is not None
            else _not_held(pe.note or "no P/E"))
    # THE PER-SHARE BASIS, checked here as well as by the fund's rule (which missed NVDA): a range
    # through a basis change divides adjusted prices by as-filed EPS on the old basis; and a share
    # count that moved after the EPS in use was filed leaves even today's P/E on a stale basis
    latest = annual_eps_point_as_of(annual, as_of)
    if latest is not None and pe.value is not None:
        after = basis_breaks(eps, latest.filed + timedelta(days=1), as_of)
        moved = [words for kind, words in after if kind == "shares"]
        if moved:
            pe_f = _not_held(f"the share count moved after the EPS in use was filed "
                             f"({latest.filed.isoformat()}) — {moved[0]}: its per-share basis "
                             f"may predate the move")
    breaks = basis_breaks(eps, consumed, as_of)
    if pct.value is not None and breaks:
        return pe_f, _not_held(f"the per-share basis changes inside the window — {breaks[0][1]}"
                               + (f" (and {len(breaks) - 1} more)" if len(breaks) > 1 else ""))
    first = max(held[0][0], as_of - timedelta(days=HISTORY_DAYS))
    pct_f = (MarketFigure(value=pct.value,
                          basis=f"share of its daily P/Es from {first.isoformat()} to "
                                f"{as_of.isoformat()} at or below today's ("
                                + (joined or "the prices held") + ")")
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
    # a count CIQ states as a marker is None on the page (audit A-D1): 'n/a', never a 0
    up, down = (("n/a" if n is None else str(n)) for n in ((rc.up, rc.down) if rc is not None
                                                          else (None, None)))
    counts = (f"; {up} analyst(s) revised up and {down} down"
              + (f", of {rc.analysts}" if rc.analysts else "") if rc is not None
              else "; revision counts not held")
    return MarketFigure(
        value=v[0] / v[3] - 1.0, detail=f"{up}↑ {down}↓" if rc is not None else "",
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
         deep: DeepSource | None, errors: list[str],
         lines: Sequence[str] = ()) -> ExposureMarket:
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
            pe, pct = pe_five_or_two(closes, points, as_of, ticker, deep, errors)
    return ExposureMarket(
        name=name, ticker=ticker, kind=kind,
        last_close=last[1] if last else None, last_bar=last[0] if last else None,
        vs_200d=vs_average(closes, as_of), from_52w_high=from_high(closes, as_of),
        rel_3m=rel["3m"], rel_12m=rel["12m"], pe=pe, pe_percentile=pct, revisions=revisions,
        warnings=tuple(split_sized_moves(closes, as_of)))


def market_context(av: AffectedView, *, thesis_id: str, version: int, run_id: str, as_of: date,
                   prices: PriceSource, eps: EpsSource,
                   hypotheses: Sequence[EnrichmentCandidate] = (), cik_of: CikOf | None = None,
                   dossiers: Path = DOSSIERS, deep: DeepSource | None = None
                   ) -> tuple[MarketContext, list[str]]:
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
                    dossiers=dossiers, deep=deep, errors=errors, lines=lines)

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
        source=(f"Polygon daily bars, split-adjusted closes ({window})"
                + ("; Tiingo raw closes and split factors before them, for five years of P/E"
                   if deep is not None else "")
                + "; SEC XBRL annual diluted EPS filed on or before each day; consensus "
                  "revisions from the fund's CIQ dossiers")), errors
