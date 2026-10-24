"""THE PRICES SOURCE for the data-quality scorecard (`vinci.quality.core`): "are the Polygon EOD
prices credible?".

WHY (2026-10-24). Prices feed the screens, every page's spot, the monitor and the scoring of the
BUY−AVOID spread (its first ledger outcome is VRRM on 2026-12-14). The only guard on them was a
COUNT: `eod.client.parse_grouped_daily` refuses a day with 0 < rows < `grouped_daily_min_results`.
A count asks whether data is PRESENT, never whether it is REAL — CLAUDE.md: "a count test catches
sparse corruption and cannot catch dense". These checks read the VALUES.

WHAT IT READS. The working store, ``data/vinci.db`` (`prices` and `securities`), opened READ-ONLY.
It is git-ignored, so CI and a fresh worktree have none: the corpus is then empty, and the command
refuses an empty corpus rather than print a clean card. Beside it, Tiingo's raw closes and split
factors for the names with a committed page (`data/dossiers/*` — every ledger name and scenario
record has one), through the fund's Tiingo adapter (`eod.tiingo`) and only where
``TIINGO_API_KEY`` is set; without the key that check is ``not_run`` on each of them, by name.

ITEMS ARE SECURITIES, named by ticker. A ticker that two securities carry bars for is named by
internal id instead — both of them, never merged into one series.

``independent`` here means Tiingo: another provider's close for the same session. ``internal`` means
the store against itself: a bar's own fields, or a series against its neighbouring bars and the
store's calendar.

COUNTS AND STATUSES ONLY. Polygon's and Tiingo's prices are licensed and the repo is public
(2026-10-22): no price, volume or ratio reaches the snapshot — dates and counts only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from vinci.dossier.freshness import _INTEGER_TOLERANCE, whole_number_ratio
from vinci.eod.client import _SESSION_PRESENT_FRACTION
from vinci.eod.tiingo import TiingoEodClient
from vinci.netcache import HttpError
from vinci.quality.core import (
    CONFIRMED,
    DIFFERS_UNEXPLAINED,
    INDEPENDENT,
    INTERNAL,
    UNCHECKED,
    Check,
    Corpus,
    Family,
    ItemResult,
    Source,
)

#: A series hole longer than this many market sessions is longer than any trading suspension the
#: SEC may order (Exchange Act §12(k)(1)(A): up to 10 business days). Past it the name left the
#: market, and the bars either side may belong to two securities under one ticker.
GAP_SESSIONS = 10

#: A close unchanged to the cent for this many consecutive stored bars — two trading weeks — is not
#: a traded price. The longest run on the store measured 2026-10-24 was 8 bars, CCO, pinned at a
#: pending cash deal's price; a carried-forward placeholder runs as long as its outage.
FLAT_RUN_SESSIONS = 10

#: Polygon's close agrees with Tiingo's within this fraction of Tiingo's: half a percent, the band
#: `freshness.date_of_close` accepts as one price (its default ``tol``). Theme intelligence joins
#: the same two providers on the same band (`market.OVERLAP_TOLERANCE`), but a fund module may not
#: import it (`tests/test_theme_intelligence_isolation.py`), so the figure stands here on its own.
CLOSE_TOL = 0.005

READS = "data/vinci.db"

#: (symbol, first day, last day) → Tiingo's daily rows as served.
Fetch = Callable[[str, date, date], list[dict[str, Any]]]


@dataclass(frozen=True)
class Series:
    """One security's stored bars, oldest first, and what the source compares them with."""

    internal_id: str
    days: array[int]               # date ordinals
    open: array[float]
    high: array[float]
    low: array[float]
    close: array[float]
    volume: array[float]
    missed: array[int]             # per step: market sessions between the two bars with no bar here
    # Tiingo's split-adjusted closes by day ordinal; a str is why none were read; None when the
    # name is not in the sample
    tiingo: dict[int, float] | str | None = None


def _tally(units: int, differs: int, excluded: int = 0) -> ItemResult:
    return ItemResult(counts={CONFIRMED: units - differs, DIFFERS_UNEXPLAINED: differs},
                      excluded=excluded)


# --- the checks ---------------------------------------------------------------------------------


def _ohlc_ordering(s: Series) -> ItemResult:
    bad = sum(1 for o, h, lo, c, v in zip(s.open, s.high, s.low, s.close, s.volume, strict=True)
              if not (0 < lo <= o <= h and lo <= c <= h and v >= 0))
    return _tally(len(s.days), bad)


def _stale_bar(s: Series) -> ItemResult:
    bars = list(zip(s.open, s.high, s.low, s.close, s.volume, strict=True))
    bad = sum(1 for i, b in enumerate(bars) if b[4] == 0 or (i > 0 and b == bars[i - 1]))
    return _tally(len(bars), bad)


def _flat_close_run(s: Series) -> ItemResult:
    bad, i, n = 0, 0, len(s.close)
    while i < n:
        j = i
        while j + 1 < n and s.close[j + 1] == s.close[i]:
            j += 1
        if j - i + 1 >= FLAT_RUN_SESSIONS:
            bad += j - i + 1
        i = j + 1
    return _tally(n, bad)


def _split_shaped_step(s: Series) -> ItemResult:
    if len(s.close) < 2:
        return ItemResult(not_applicable="one bar — no step to test")
    bad = excluded = 0
    for i in range(1, len(s.close)):
        if s.missed[i - 1] > GAP_SESSIONS:
            excluded += 1
            continue
        a, b = s.close[i - 1], s.close[i]
        # a non-positive close has no ratio, and is no price move either
        if a <= 0 or b <= 0 or whole_number_ratio(b / a):
            bad += 1
    return _tally(len(s.close) - 1 - excluded, bad, excluded)


def _series_gap(s: Series) -> ItemResult:
    if len(s.close) < 2:
        return ItemResult(not_applicable="one bar — no step to test")
    return _tally(len(s.missed), sum(1 for m in s.missed if m > GAP_SESSIONS))


_NOT_SAMPLED = "not in the Tiingo sample — Tiingo is fetched per name, for the names with a page"


def _close_vs_tiingo(s: Series) -> ItemResult:
    if s.tiingo is None:
        return ItemResult(not_applicable=_NOT_SAMPLED)
    if isinstance(s.tiingo, str):
        return ItemResult(not_run=s.tiingo)
    c: Counter[str] = Counter()
    for d, close in zip(s.days, s.close, strict=True):
        t = s.tiingo.get(d)
        if t is None:
            c[UNCHECKED] += 1
        elif abs(close - t) <= CLOSE_TOL * t:
            c[CONFIRMED] += 1
        else:
            c[DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


_ALL_CLASSES = ("wrong_file", "wrong_cell", "wrong_unit", "wrong_period", "different_definition")
CHECKS: tuple[Check, ...] = (
    Check("ohlc_ordering", "Each bar's open and close inside its own high–low range",
          "the stored bar's open, high, low and close", "the same bar's other fields", INTERNAL,
          "bar",
          "exact: 0 < low ≤ open ≤ high, low ≤ close ≤ high, volume ≥ 0. `PriceBar` refuses a "
          "high below the low and a non-positive price at write; it does not place the open or "
          "the close", "every stored bar", None, None, ("wrong_cell", "wrong_unit"),
          _ohlc_ordering),
    Check("stale_bar", "Each bar records its own session's trading",
          "the stored bar", "the same name's previous stored bar", INTERNAL, "bar",
          "exact: a bar that repeats the previous stored bar's open, high, low, close and volume, "
          "or reports zero volume, differs", "every stored bar", None, None,
          ("wrong_file", "wrong_period"), _stale_bar),
    Check("flat_close_run", "No close frozen across a run of sessions",
          "the stored close", "the same name's neighbouring stored closes", INTERNAL, "bar",
          f"a bar inside a run of {FLAT_RUN_SESSIONS} or more consecutive stored bars with an "
          "identical close differs (prices.FLAT_RUN_SESSIONS)", "every stored bar", None, None,
          ("wrong_period",), _flat_close_run),
    Check("split_shaped_step", "No close-to-close step by a whole-number ratio",
          "the step from one stored close to the next", "the previous stored close", INTERNAL,
          "step",
          f"a step whose ratio, either way up, sits within {_INTEGER_TOLERANCE:.0%} of a whole "
          "number ≥2 differs — the rule that names a corporate action between CIQ panels "
          "(freshness.whole_number_ratio). A genuine fall of a half or rise of a double reads the "
          "same; the check cannot tell them apart", "every pair of consecutive stored bars",
          None, f"steps across a gap of more than {GAP_SESSIONS} market sessions — series_gap "
          "judges those", ("wrong_unit", "wrong_period"), _split_shaped_step),
    Check("series_gap", "No hole in a series longer than an SEC trading suspension",
          "the dates of a name's stored bars",
          "the store's market-session calendar: the days holding bars for at least "
          f"{_SESSION_PRESENT_FRACTION:.0%} of the most names any day holds", INTERNAL, "step",
          f"a step across more than {GAP_SESSIONS} market sessions with no bar for the name "
          "differs (prices.GAP_SESSIONS) — longer than the 10 business days an SEC trading "
          "suspension may run", "every pair of consecutive stored bars", None, None,
          ("wrong_file",), _series_gap),
    Check("close_vs_tiingo", "The stored close against Tiingo's close for the same session",
          "the stored close (Polygon, adjusted=true: restated for splits only)",
          "Tiingo's unadjusted close divided by the split factors Tiingo reports after that "
          "session — the same splits-only basis", INDEPENDENT, "bar",
          f"within {CLOSE_TOL:.1%} of Tiingo's close (prices.CLOSE_TOL — the band "
          "freshness.date_of_close accepts as one price)",
          "names with a committed page (data/dossiers/*), where TIINGO_API_KEY is set", None, None,
          _ALL_CLASSES, _close_vs_tiingo),
)
CHECK_IDS = tuple(c.id for c in CHECKS)


# --- the coverage map ---------------------------------------------------------------------------

FAMILIES: tuple[Family, ...] = (
    Family("bars.close", "prices (polygon-grouped, polygon-aggs)", ("EOD <ticker> last close",),
           "the daily close — every return the screens, the monitor and the BUY−AVOID spread "
           "read, and each page's spot",
           checks=("close_vs_tiingo", "split_shaped_step", "flat_close_run", "stale_bar",
                   "ohlc_ordering", "series_gap"),
           unscored=("freshness.date_of_close — CIQ's printed comps close matched against the "
                     "store to DATE the comps panel: it agrees by construction where it matches, "
                     "a miss is stated only in display text (implied_expectations.tev "
                     "source_ref), and the printed close is not on the page",
                     "eod.client.parse_grouped_daily — the row-COUNT floor at ingest "
                     "(grouped_daily_min_results): a count, not a value, and it leaves no "
                     "record in the store"),
           note="the independent check runs on the Tiingo sample only; every other name has the "
                "internal checks alone. adjusted=true restates splits, never dividends, so a "
                "return read from the store is a price return"),
    Family("bars.range", "prices (polygon-grouped, polygon-aggs)",
           ("EOD <ticker> 52-week high", "EOD <ticker> 52-week low"),
           "open, high and low — the 52-week range on each page",
           checks=("ohlc_ordering", "stale_bar", "series_gap"),
           note="Tiingo's high and low are not compared"),
    Family("bars.volume", "prices (polygon-grouped, polygon-aggs)", (),
           "volume — the liquidity the screens read", checks=("stale_bar", "series_gap"),
           note="no second volume figure is compared; a zero is the only value tested"),
)


# --- what it reads ------------------------------------------------------------------------------


def split_adjusted_closes(rows: list[dict[str, Any]]) -> dict[int, float]:
    """Tiingo's closes on Polygon's basis: each unadjusted close divided by every split factor
    Tiingo reports on a LATER day (a factor sits on the ex-date, whose close is already
    post-split). Theme intelligence derives the same (`market.split_adjusted`); it is not imported
    across the isolation wall. An unreadable row raises — never a guessed close or factor."""
    out: dict[int, float] = {}
    later = 1.0
    for r in sorted(rows, key=lambda r: str(r["date"]), reverse=True):
        close, factor = r["close"], r["splitFactor"]
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0
                   for x in (close, factor)):
            raise ValueError(f"Tiingo row {r.get('date')!r}: close/splitFactor not positive "
                             "numbers")
        out[date.fromisoformat(str(r["date"])[:10]).toordinal()] = float(close) / later
        later *= float(factor)
    return out


def _default_fetch() -> Fetch | None:
    """Tiingo's daily rows where a key is set — else None, and the comparison is not run."""
    if not os.environ.get("TIINGO_API_KEY"):
        return None
    client = TiingoEodClient.from_config()
    return lambda symbol, start, end: client.daily_rows(symbol, start=start, end=end)


def _empty(why: str) -> Corpus:
    return Corpus(items={}, reads=f"{READS} ({why})", item_noun="name",
                  sha256=hashlib.sha256(b"").hexdigest())


def read_store(root: Path, *,
               tiingo: Callable[[], Fetch | None] = _default_fetch) -> Corpus:
    """Every security with bars in ``root/data/vinci.db``, read once and read-only, plus Tiingo
    for the sampled names. ``tiingo`` is called only when a sampled name has bars."""
    db = root / "data" / "vinci.db"
    if not db.is_file():
        return _empty("absent — the working store is git-ignored, so CI and a fresh worktree "
                      "have none")
    con = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        secs = {iid: (t, sym) for iid, t, sym in con.execute(
            "SELECT internal_id, ticker, eod_symbol FROM securities")}
        per_day = dict(con.execute("SELECT bar_date, COUNT(*) FROM prices GROUP BY bar_date"))
        if not per_day:
            return _empty("its prices table holds no rows")
        top = max(per_day.values())
        market = sorted(date.fromisoformat(d).toordinal() for d, n in per_day.items()
                        if n >= _SESSION_PRESENT_FRACTION * top)
        cols: dict[str, tuple[array[int], array[float], array[float], array[float],
                              array[float], array[float]]] = {}
        for iid, d, o, h, lo, c, v in con.execute(
                "SELECT internal_id, bar_date, open, high, low, close, volume FROM prices "
                "ORDER BY internal_id, bar_date"):
            if iid not in cols:
                cols[iid] = (array("i"), array("d"), array("d"), array("d"), array("d"),
                             array("d"))
            a = cols[iid]
            a[0].append(date.fromisoformat(d).toordinal())
            for arr, x in zip(a[1:], (o, h, lo, c, v), strict=True):
                arr.append(x)
    finally:
        con.close()
    held = Counter(secs[iid][0] for iid in cols if iid in secs)
    sample = {p.parent.name.upper() for p in (root / "data" / "dossiers").glob("*/dossier.json")}
    fetch: Fetch | None = None
    asked = False
    items: dict[str, Series] = {}
    for iid, (days, o, h, lo, c, v) in cols.items():
        ticker, symbol = secs.get(iid, (None, None))
        name = ticker if ticker is not None and held[ticker] == 1 else iid
        missed = array("i", (bisect_left(market, days[i]) - bisect_right(market, days[i - 1])
                             for i in range(1, len(days))))
        closes: dict[int, float] | str | None = None
        if ticker in sample and symbol is not None:
            if not asked:
                fetch, asked = tiingo(), True
            closes = _tiingo_closes(fetch, symbol, days)
        items[name] = Series(iid, days, o, h, lo, c, v, missed, closes)
    if len(items) != len(cols):     # a ticker equal to another security's internal id
        raise ValueError(f"{db}: two securities resolve to one item name")
    digest = hashlib.sha256()
    for name in sorted(items):
        s = items[name]
        digest.update(f"{name}\n{s.internal_id}\n".encode())
        for col in (s.days, s.open, s.high, s.low, s.close, s.volume):
            digest.update(col.tobytes())
        digest.update(json.dumps(sorted(s.tiingo.items()) if isinstance(s.tiingo, dict)
                                 else s.tiingo).encode() + b"\n")
    partial = len(per_day) - len(market)
    unpriced = len(sample - set(held))
    reads = (f"{READS}, read-only: {sum(len(s.days) for s in items.values()):,} bars; "
             f"{len(market):,} market sessions {date.fromordinal(market[0])} → "
             f"{date.fromordinal(market[-1])}" + (f" (+{partial:,} partial)" if partial else "")
             + f"; latest bar {max(per_day)}. Tiingo sample: the {len(sample) - unpriced} names "
             "with a committed page"
             + (f" ({unpriced} more {'has' if unpriced == 1 else 'have'} no bars here)"
                if unpriced else ""))
    return Corpus(items=items, reads=reads, item_noun="name", sha256=digest.hexdigest())


def _tiingo_closes(fetch: Fetch | None, symbol: str,
                   days: array[int]) -> dict[int, float] | str:
    """Tiingo's split-adjusted closes over the name's stored span, or why there are none."""
    if fetch is None:
        return "no TIINGO_API_KEY in the environment"
    try:
        return split_adjusted_closes(fetch(symbol, date.fromordinal(days[0]),
                                           date.fromordinal(days[-1])))
    except (HttpError, KeyError, TypeError, ValueError) as exc:
        return f"Tiingo {symbol}: {type(exc).__name__} — no comparison"


def load(root: Path) -> Corpus:
    return read_store(root, tiingo=_default_fetch)


SOURCE = Source(
    id="prices", title="Polygon EOD prices",
    reads_note="reads the git-ignored working store read-only, and Tiingo for the sample; the "
               "sha256 names exactly what was read",
    load=load, checks=CHECKS, families=FAMILIES)
