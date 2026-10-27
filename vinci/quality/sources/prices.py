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
And Tiingo's raw rows over every name an internal check FLAGS (a split-shaped step, a hole, a
zero-volume bar — 2026-10-27), one request a name, so each flag gets a second provider's verdict.

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
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from math import prod
from pathlib import Path
from typing import Any

from vinci.dossier.freshness import _INTEGER_TOLERANCE, whole_number_ratio
from vinci.eod.client import _SESSION_PRESENT_FRACTION
from vinci.eod.tiingo import _ONE_DAY, TiingoEodClient, TiingoRefusedError
from vinci.netcache import HttpError
from vinci.quality.core import (
    CONFIRMED,
    DIFFERS_STATED,
    DIFFERS_UNEXPLAINED,
    INDEPENDENT,
    INTERNAL,
    UNCHECKED,
    Check,
    Corpus,
    Family,
    ItemResult,
    Source,
    one,
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

#: A Tiingo window that ENDED this many days ago is kept once read (`daily_rows(ttl_seconds=None)`)
#: instead of re-read after a day. Its sessions have all posted and their raw closes, volumes and
#: split factors are settled, and the flagged names' windows are mostly years old: re-reading them
#: every run would spend the plan's ~50 requests an hour (`theme_intelligence/market.py`) and its
#: 500 distinct symbols a month — shared by every user of the key — on answers that cannot change.
#: Face validity — a month is longer than any posting or correction delay this repo has met; it
#: was not measured.
CLOSED_WINDOW_DAYS = 30

#: A flagged name's Tiingo window starts this long before its first flagged session, so a verdict
#: can see whether Tiingo's series is already running then (two weeks ≈ `GAP_SESSIONS` sessions).
FLAGGED_LEAD = timedelta(days=14)

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
    # Tiingo's RAW (close, volume, split factor) by day ordinal over the window of everything the
    # internal checks flag on this name (`flagged_window`); a str is why none were read; None when
    # nothing is flagged
    flagged: dict[int, tuple[float, float, float]] | str | None = None
    # the fewest market sessions between this security's bars and those of another security
    # carrying the same ticker (-1 when they overlap); None when no other carries it
    shared_ticker: int | None = None


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


def _split_shaped(a: float, b: float) -> bool:
    # a non-positive close has no ratio, and is no price move either
    return a <= 0 or b <= 0 or whole_number_ratio(b / a)


def _split_shaped_step(s: Series) -> ItemResult:
    if len(s.close) < 2:
        return ItemResult(not_applicable="one bar — no step to test")
    bad = excluded = 0
    for i in range(1, len(s.close)):
        if s.missed[i - 1] > GAP_SESSIONS:
            excluded += 1
            continue
        if _split_shaped(s.close[i - 1], s.close[i]):
            bad += 1
    return _tally(len(s.close) - 1 - excluded, bad, excluded)


def _series_gap(s: Series) -> ItemResult:
    if len(s.close) < 2:
        return ItemResult(not_applicable="one bar — no step to test")
    return _tally(len(s.missed), sum(1 for m in s.missed if m > GAP_SESSIONS))


def flagged_steps(s: Series) -> list[int]:
    """Each ``i`` whose step from bar ``i - 1`` to bar ``i`` an internal check flags: across a hole
    longer than `GAP_SESSIONS` (series_gap), or by a whole-number ratio (split_shaped_step)."""
    return [i for i in range(1, len(s.close)) if s.missed[i - 1] > GAP_SESSIONS
            or _split_shaped(s.close[i - 1], s.close[i])]


def zero_volume_bars(s: Series) -> list[int]:
    return [j for j, v in enumerate(s.volume) if v == 0]


def flagged_window(s: Series) -> tuple[date, date] | None:
    """The one Tiingo window that covers everything flagged on this name: from `FLAGGED_LEAD`
    before the first flagged session to the last — or None when nothing is flagged."""
    days = [s.days[j] for i in flagged_steps(s) for j in (i - 1, i)]
    days += [s.days[j] for j in zero_volume_bars(s)]
    if not days:
        return None
    return date.fromordinal(min(days)) - FLAGGED_LEAD, date.fromordinal(max(days))


def _flagged_rows(s: Series) -> dict[int, tuple[float, float, float]] | ItemResult:
    if isinstance(s.flagged, dict):
        return s.flagged
    return ItemResult(not_run=s.flagged or "Tiingo was not read for this name")


_NOTHING_TO_ASK = "no step here is split-shaped or crosses a hole — nothing to ask Tiingo"


def _step_vs_tiingo(s: Series) -> ItemResult:
    steps = flagged_steps(s)
    if not steps:
        return ItemResult(not_applicable=_NOTHING_TO_ASK)
    rows = _flagged_rows(s)
    if isinstance(rows, ItemResult):
        return rows
    if not rows:
        return ItemResult(counts={UNCHECKED: len(steps)})
    first = min(rows)
    c: Counter[str] = Counter()
    for i in steps:
        a, b = s.days[i - 1], s.days[i]
        ra, rb = rows.get(a), rows.get(b)
        if rb is None:
            c[UNCHECKED] += 1                 # Tiingo has no bar for the later session
        elif ra is None:
            # Tiingo's series under this ticker began after the earlier bar: that bar is another
            # security's. A session missing from a series already running is no verdict.
            c[DIFFERS_UNEXPLAINED if first > a else UNCHECKED] += 1
        elif s.close[i - 1] <= 0 or s.close[i] <= 0:
            c[DIFFERS_UNEXPLAINED] += 1
        else:
            stored, raw = s.close[i] / s.close[i - 1], rb[0] / ra[0]
            split = prod(r[2] for d, r in rows.items() if a < d <= b)
            if abs(stored / (raw * split) - 1) <= CLOSE_TOL:
                c[CONFIRMED] += 1             # one move, both providers
            elif abs(stored / raw - 1) <= CLOSE_TOL:
                # Tiingo's RAW ratio and not its adjusted one, so a split lies between them: the
                # split Tiingo reports, held unadjusted
                c[DIFFERS_STATED] += 1
            else:
                c[DIFFERS_UNEXPLAINED] += 1
    return ItemResult(counts=dict(c))


def _zero_volume_vs_tiingo(s: Series) -> ItemResult:
    zero = zero_volume_bars(s)
    if not zero:
        return ItemResult(not_applicable="no zero-volume bar")
    rows = _flagged_rows(s)
    if isinstance(rows, ItemResult):
        return rows
    if not rows:
        return ItemResult(counts={UNCHECKED: len(zero)})
    first = min(rows)
    c: Counter[str] = Counter()
    for j in zero:
        d = s.days[j]
        r = rows.get(d)
        if first > d:
            c[UNCHECKED] += 1                 # Tiingo carries no series under this ticker yet
        elif r is None or r[1] == 0:
            c[CONFIRMED] += 1                 # Tiingo records no trading that session either
        else:
            c[DIFFERS_UNEXPLAINED] += 1       # Tiingo records trades the stored bar does not
    return ItemResult(counts=dict(c))


def _history_across_ids(s: Series) -> ItemResult:
    if s.shared_ticker is None:
        return ItemResult(not_applicable="no other security in the store carries its ticker")
    return one(DIFFERS_UNEXPLAINED if s.shared_ticker <= GAP_SESSIONS else CONFIRMED)


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
    Check("step_vs_tiingo", "Each flagged step against Tiingo's same two sessions",
          "a step split_shaped_step or series_gap flags: the stored close before it and after it",
          "Tiingo's unadjusted closes on the same two sessions, times every split factor it "
          "reports after the first and up to the second", INDEPENDENT, "step",
          f"the stored ratio within {CLOSE_TOL:.1%} of Tiingo's split-adjusted ratio "
          "(prices.CLOSE_TOL) is one move both providers report. Tiingo serving the later session "
          "but no row on or before the earlier one differs: the security it carries under the "
          "ticker had not begun trading, so the earlier bar is another's. No Tiingo bar for the "
          "later session, or for the earlier one inside a series already running, is unchecked",
          "every step split_shaped_step or series_gap flags, where TIINGO_API_KEY is set — one "
          "request a name, over its flagged sessions (prices.flagged_window)",
          "the stored ratio is Tiingo's UNADJUSTED ratio across a split Tiingo reports between "
          "the two sessions: the store holds that split unadjusted", None,
          ("wrong_file", "wrong_unit", "wrong_period"), _step_vs_tiingo),
    Check("zero_volume_vs_tiingo", "Each zero-volume bar against Tiingo's same session",
          "a stored bar reporting zero volume",
          "Tiingo's row for the same session: its volume, or its absence inside a series already "
          "running", INDEPENDENT, "bar",
          "exact: Tiingo reporting no trading that session (no row, or volume 0) confirms the "
          "zero; Tiingo reporting trades differs. Before Tiingo's series under the ticker begins, "
          "unchecked", "every stored bar with zero volume, where TIINGO_API_KEY is set — the same "
          "one request a name as step_vs_tiingo", None, None, ("wrong_cell",),
          _zero_volume_vs_tiingo),
    Check("history_across_ids", "One ticker's bars held apart from another security's",
          "a security's stored span of bars",
          "the spans of every other security in the store carrying the same ticker, on the "
          "store's market-session calendar", INTERNAL, "security",
          f"two securities in turn, more than {GAP_SESSIONS} market sessions apart "
          "(prices.GAP_SESSIONS), are kept apart. Spans that abut or overlap differ: one "
          "history broken across two ids (a re-domicile under a new filer), or two series at once",
          "every security whose ticker another security with bars also carries", None, None,
          ("wrong_file",), _history_across_ids),
)
CHECK_IDS = tuple(c.id for c in CHECKS)


# --- the coverage map ---------------------------------------------------------------------------

FAMILIES: tuple[Family, ...] = (
    Family("bars.close", "prices (polygon-grouped, polygon-aggs)", ("EOD <ticker> last close",),
           "the daily close — every return the screens, the monitor and the BUY−AVOID spread "
           "read, and each page's spot",
           checks=("close_vs_tiingo", "step_vs_tiingo", "split_shaped_step", "flat_close_run",
                   "stale_bar", "ohlc_ordering", "series_gap", "history_across_ids"),
           unscored=("freshness.date_of_close — CIQ's printed comps close matched against the "
                     "store to DATE the comps panel: it agrees by construction where it matches, "
                     "a miss is stated only in display text (implied_expectations.tev "
                     "source_ref), and the printed close is not on the page",
                     "eod.client.parse_grouped_daily — the row-COUNT floor at ingest "
                     "(grouped_daily_min_results): a count, not a value, and it leaves no "
                     "record in the store"),
           note="every close is compared with Tiingo's on the page names only; elsewhere Tiingo "
                "judges only the steps the internal checks flag, and every other close has the "
                "internal checks alone. adjusted=true restates splits, never dividends, so a "
                "return read from the store is a price return"),
    Family("bars.range", "prices (polygon-grouped, polygon-aggs)",
           ("EOD <ticker> 52-week high", "EOD <ticker> 52-week low"),
           "open, high and low — the 52-week range on each page",
           checks=("ohlc_ordering", "stale_bar", "series_gap", "history_across_ids"),
           note="Tiingo's high and low are not compared"),
    Family("bars.volume", "prices (polygon-grouped, polygon-aggs)", (),
           "volume — the liquidity the screens read",
           checks=("zero_volume_vs_tiingo", "stale_bar", "series_gap", "history_across_ids"),
           note="Tiingo's volume is compared only where the stored volume is zero; a zero is the "
                "only value tested"),
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


def raw_rows(rows: list[dict[str, Any]]) -> dict[int, tuple[float, float, float]]:
    """Tiingo's UNADJUSTED close, volume and split factor by day ordinal. An unreadable row
    raises — never a guessed close, volume or factor."""
    out: dict[int, tuple[float, float, float]] = {}
    for r in rows:
        close, volume, factor = r["close"], r["volume"], r["splitFactor"]
        if not (all(isinstance(x, (int, float)) and not isinstance(x, bool)
                    for x in (close, volume, factor)) and close > 0 and factor > 0
                and volume >= 0):
            raise ValueError(f"Tiingo row {r.get('date')!r}: close/volume/splitFactor not "
                             "readable")
        out[date.fromisoformat(str(r["date"])[:10]).toordinal()] = (
            float(close), float(volume), float(factor))
    return out


def _default_fetch() -> Fetch | None:
    """Tiingo's daily rows where a key is set — else None, and the comparison is not run. A window
    that ended `CLOSED_WINDOW_DAYS` ago is read once and kept; any other is re-read after a day.

    ONCE TIINGO REFUSES ON A PLAN LIMIT, NOTHING MORE IS ASKED THIS RUN. A cold cache needs one
    request per sampled and flagged name — 157 on the 2026-10-27 store — against 50 an hour and
    500 distinct symbols a month for the whole key. Past the hourly limit each name would wait out
    `netcache`'s four 61-second retries before reading not_run: hours. Past the monthly one every
    new symbol is refused (`TiingoRefusedError`). Either way the names left read not_run by name
    and a later run asks for them; what was answered is kept."""
    if not os.environ.get("TIINGO_API_KEY"):
        return None
    client = TiingoEodClient.from_config()
    closed = date.today() - timedelta(days=CLOSED_WINDOW_DAYS)
    stopped: list[str] = []

    def fetch(symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        ttl = None if end <= closed else _ONE_DAY
        if stopped:
            # a kept answer is still read; only a new request is refused
            if (kept := client.cached_rows(symbol, start=start, end=end,
                                           ttl_seconds=ttl)) is not None:
                return kept
            # short enough that `_why` never cuts it; the refused name reads its own refusal
            raise HttpError(f"not asked: {stopped[0]}")
        try:
            return client.daily_rows(symbol, start=start, end=end, ttl_seconds=ttl)
        except TiingoRefusedError as exc:
            if exc.monthly_cap:               # every new symbol is refused until the month turns
                stopped.append("monthly symbol limit")
            raise
        except HttpError as exc:
            if "429" in str(exc.__cause__):
                stopped.append("hourly rate limit")
            raise

    return fetch


def market_sessions(per_day: dict[str, int]) -> list[int]:
    """The store's market sessions, as day ordinals: the days holding bars for at least
    `_SESSION_PRESENT_FRACTION` of the most names any one day holds. Others are partial days."""
    top = max(per_day.values())
    return sorted(date.fromisoformat(d).toordinal() for d, n in per_day.items()
                  if n >= _SESSION_PRESENT_FRACTION * top)


def missed_sessions(market: list[int], days: array[int]) -> array[int]:
    """Per step between consecutive bars: the market sessions strictly between them."""
    return array("i", (bisect_left(market, days[i]) - bisect_right(market, days[i - 1])
                       for i in range(1, len(days))))


def sessions_apart(market: list[int], span: tuple[int, int],
                   others: list[tuple[int, int]]) -> int | None:
    """The fewest market sessions strictly between ``span`` (first, last bar) and any of
    ``others`` — -1 when one overlaps it; None when there are no others."""
    gaps = []
    for first, last in others:
        if span[1] < first:
            gaps.append(bisect_left(market, first) - bisect_right(market, span[1]))
        elif last < span[0]:
            gaps.append(bisect_left(market, span[0]) - bisect_right(market, last))
        else:
            gaps.append(-1)
    return min(gaps) if gaps else None


def _empty(why: str) -> Corpus:
    return Corpus(items={}, reads=f"{READS} ({why})", item_noun="name",
                  sha256=hashlib.sha256(b"").hexdigest())


def read_store(root: Path, *,
               tiingo: Callable[[], Fetch | None] = _default_fetch) -> Corpus:
    """Every security with bars in ``root/data/vinci.db``, read once and read-only, plus Tiingo
    for the sampled names and the flagged ones — one request a name either way. ``tiingo`` is
    called only when a sampled or flagged name has bars."""
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
        market = market_sessions(per_day)
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
    carriers: defaultdict[str, list[tuple[str, tuple[int, int]]]] = defaultdict(list)
    for iid, cs in cols.items():
        if iid in secs:
            carriers[secs[iid][0]].append((iid, (cs[0][0], cs[0][-1])))
    sample = {p.parent.name.upper() for p in (root / "data" / "dossiers").glob("*/dossier.json")}
    fetch: Fetch | None = None
    asked = False
    flagged_names = 0
    items: dict[str, Series] = {}
    # the page names are asked first: a plan limit met later in the run leaves the flagged names
    # not_run, never the closes every page reads (the card sorts names itself)
    for iid in sorted(cols, key=lambda i: (secs.get(i, (None,))[0] not in sample, i)):
        days, o, h, lo, c, v = cols[iid]
        ticker, symbol = secs.get(iid, (None, None))
        name = ticker if ticker is not None and held[ticker] == 1 else iid
        shared = None if ticker is None else sessions_apart(
            market, (days[0], days[-1]), [sp for other, sp in carriers[ticker] if other != iid])
        s = Series(iid, days, o, h, lo, c, v, missed_sessions(market, days),
                   shared_ticker=shared)
        window = flagged_window(s) if symbol is not None else None
        sampled = ticker in sample and symbol is not None
        if window is not None:
            flagged_names += 1
        if (sampled or window is not None) and not asked:
            fetch, asked = tiingo(), True
        closes: dict[int, float] | str | None = None
        flagged: dict[int, tuple[float, float, float]] | str | None = None
        if sampled and symbol is not None:
            # ONE request covers both: the stored span, reaching back to the flagged window
            start = date.fromordinal(days[0])
            rows = _ask(fetch, symbol, start if window is None else min(start, window[0]),
                        date.fromordinal(days[-1]))
            closes = _read(split_adjusted_closes, rows, symbol)
            flagged = None if window is None else _read(raw_rows, rows, symbol)
        elif window is not None and symbol is not None:
            flagged = _read(raw_rows, _ask(fetch, symbol, *window), symbol)
        items[name] = Series(iid, days, o, h, lo, c, v, s.missed, closes, flagged, shared)
    if len(items) != len(cols):     # a ticker equal to another security's internal id
        raise ValueError(f"{db}: two securities resolve to one item name")
    digest = hashlib.sha256()
    for name in sorted(items):
        s = items[name]
        digest.update(f"{name}\n{s.internal_id}\n".encode())
        for col in (s.days, s.open, s.high, s.low, s.close, s.volume):
            digest.update(col.tobytes())
        for got in (s.tiingo, s.flagged):
            digest.update(json.dumps(sorted(got.items()) if isinstance(got, dict)
                                     else got).encode() + b"\n")
        digest.update(f"{s.shared_ticker}\n".encode())
    partial = len(per_day) - len(market)
    unpriced = len(sample - set(held))
    reads = (f"{READS}, read-only: {sum(len(s.days) for s in items.values()):,} bars; "
             f"{len(market):,} market sessions {date.fromordinal(market[0])} → "
             f"{date.fromordinal(market[-1])}" + (f" (+{partial:,} partial)" if partial else "")
             + f"; latest bar {max(per_day)}. Tiingo sample: the {len(sample) - unpriced} names "
             "with a committed page"
             + (f" ({unpriced} more {'has' if unpriced == 1 else 'have'} no bars here)"
                if unpriced else "")
             + f"; and the {flagged_names} names an internal check flags (step_vs_tiingo, "
               "zero_volume_vs_tiingo)")
    return Corpus(items=items, reads=reads, item_noun="name", sha256=digest.hexdigest())


def _ask(fetch: Fetch | None, symbol: str, start: date,
         end: date) -> list[dict[str, Any]] | str:
    """Tiingo's rows over [start, end], or why there are none."""
    if fetch is None:
        return "no TIINGO_API_KEY in the environment"
    try:
        # Tiingo spells a share class with a hyphen (brk-b) where Polygon uses a dot
        return fetch(symbol.replace(".", "-"), start, end)
    except (HttpError, KeyError, TypeError, ValueError) as exc:
        return _why(symbol, exc)


def _read(parse: Callable[[list[dict[str, Any]]], Any], rows: list[dict[str, Any]] | str,
          symbol: str) -> Any:
    if isinstance(rows, str):
        return rows
    try:
        return parse(rows)
    except (KeyError, TypeError, ValueError) as exc:
        return _why(symbol, exc)


def _why(symbol: str, exc: Exception) -> str:
    # the status, never the URL or the body: "Non-retryable 404" or "Exhausted retries"
    what = str(exc).split(" from ")[0].split(" for ")[0][:40]
    return f"Tiingo {symbol}: {type(exc).__name__} ({what}) — no comparison"


def load(root: Path) -> Corpus:
    return read_store(root, tiingo=_default_fetch)


SOURCE = Source(
    id="prices", title="Polygon EOD prices",
    reads_note="reads the git-ignored working store read-only, and Tiingo for the sample; the "
               "sha256 names exactly what was read",
    load=load, checks=CHECKS, families=FAMILIES)
