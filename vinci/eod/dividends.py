"""DIVIDENDS FOR TOTAL RETURN — the ex-date yields every return in scoring and the monitor carries.

WHY (operator ruling B, 2026-10-26). The scoring harness called a price return "total return":
`exit / entry − 1` on Polygon closes, which `adjusted=true` restates for splits and never for
dividends. The ruling makes TOTAL RETURN WITH DIVIDENDS the primary basis, names and benchmarks
alike, with price return printed beside it. Registered before the first ledger outcome (VRRM,
2026-12-14).

THE DEFINITION. Dividends are reinvested on the ex-date, the standard holding-period total return:
over a window (entry, exit], growth = ∏ (1 + divCash ÷ close) across the ex-dates inside it, and
total return = (exit ÷ entry) × growth − 1. Both figures in each yield are Tiingo's own unadjusted
cash and close for that day, so the yield needs no split basis and multiplies onto the fund's own
price ratio. That ratio is on one split basis (`eod.splits`, 2026-10-29): the sealed entry price
stays in the ledger, and is read on the exit's basis when a recorded split has moved the series.

UNKNOWN IS NEVER ZERO. Tiingo serves one row per session with ``divCash`` (0.0 when none was
paid), so a window counts as READ only when Tiingo's rows cover it: a row ON the entry session, ON
the exit session and ON EVERY SESSION BETWEEN ON WHICH THE NAME TRADED, read from a calendar the
caller supplies (`eod.client.SessionCalendar`: the name's bars in the store, or its Polygon bars),
and no two neighbouring rows more than `MAX_SESSION_GAP_DAYS` apart. Anything less — no key, a
failed request, an unreadable row, a missing session — raises `DividendsUnknownError`, and the
caller fails loud. Nothing here returns an empty list for a window it could not read.

WHY THE CALENDAR (audit item F-D3, 2026-10-29). Coverage was the gap rule alone, which measures
CALENDAR days: a weekday missing from Tiingo's rows is a two-day gap, shorter than a holiday
weekend, so a window missing its one ex-date row read as covered and returned no dividend — a zero
where the record had a hole. Only a list of the market's own sessions can tell a missing session
from a closed market. It is the name's own sessions (review of #855): a full-day halt is a
market session with no trade in the name, and Tiingo serves no row for it.
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from vinci.eod.client import EodError, SessionCalendar
from vinci.eod.tiingo import TiingoEodClient, tiingo_symbol
from vinci.netcache import HttpError

#: The longest a US market regularly stays shut between two sessions: a Friday close to the Tuesday
#: after a Monday holiday (Good Friday's Thursday-to-Monday is the same span). A longer hole in
#: Tiingo's rows is a hole in the record, not a holiday.
MAX_SESSION_GAP_DAYS = 4

#: (symbol, entry session, exit session) → the ex-date yields in (entry, exit], each
#: ``divCash ÷ close``. Raises `DividendsUnknownError` for a window it cannot read.
DividendSource = Callable[[str, date, date], list[tuple[date, float]]]


class DividendsUnknownError(ValueError):
    """A window whose dividends could not be read. Never a zero: the caller fails loud."""


def growth(yields: list[tuple[date, float]]) -> float:
    """∏ (1 + yield) — the factor reinvested dividends add to a price ratio."""
    g = 1.0
    for _d, y in yields:
        g *= 1.0 + y
    return g


def ex_date_yields(rows: list[dict[str, Any]], start: date, end: date, *,
                   sessions: Sequence[date], symbol: str = "") -> list[tuple[date, float]]:
    """The ex-date yields in (start, end] from Tiingo's daily rows, or `DividendsUnknownError` when
    the rows do not cover the window (see the module note). ``sessions`` are the sessions the name
    traded (a `SessionCalendar`'s answer); each one inside [start, end] needs a row. Pure, so it is
    pinned offline."""
    if end < start:
        raise ValueError(f"{symbol}: window ends {end} before it starts {start}")
    days: list[tuple[date, float, float]] = []
    for r in rows:
        try:
            d = date.fromisoformat(str(r["date"])[:10])
            close, cash = r["close"], r["divCash"]
        except (KeyError, TypeError, ValueError) as exc:
            raise DividendsUnknownError(f"{symbol}: an unreadable Tiingo row ({exc!r})") from exc
        if not (isinstance(close, (int, float)) and not isinstance(close, bool) and close > 0
                and isinstance(cash, (int, float)) and not isinstance(cash, bool) and cash >= 0):
            raise DividendsUnknownError(f"{symbol} {d}: close/divCash not readable numbers")
        if start <= d <= end:
            days.append((d, float(close), float(cash)))
    days.sort()
    if not days or days[0][0] != start or days[-1][0] != end:
        held = f"{days[0][0]} → {days[-1][0]}" if days else "no rows"
        raise DividendsUnknownError(f"{symbol}: Tiingo's rows do not cover {start} → {end} "
                                    f"({held})")
    gaps = [(a, b) for (a, _c, _x), (b, _c2, _x2) in zip(days, days[1:], strict=False)
            if (b - a).days > MAX_SESSION_GAP_DAYS]
    if gaps:
        a, b = gaps[0]
        raise DividendsUnknownError(f"{symbol}: Tiingo holds no row between {a} and {b} — a hole "
                               f"longer than any market closure, so the dividends there are "
                               f"unknown")
    have = {d for d, _c, _x in days}
    window = [s for s in sessions if start <= s <= end]
    if not window:
        # a window holds at least its own entry session, so a calendar with none in it is no
        # calendar — and an empty one would pass every window unchecked
        raise DividendsUnknownError(f"{symbol}: the calendar holds no session in {start} → {end}, "
                                    f"so Tiingo's coverage cannot be checked")
    missing = [s for s in window if s not in have]
    if missing:
        raise DividendsUnknownError(
            f"{symbol}: Tiingo holds no row for {len(missing)} session(s) the name traded in "
            f"{start} → {end} (first {missing[0]}) — an ex-date there would be missed, so the "
            f"dividends are unknown")
    return [(d, cash / close) for d, close, cash in days if d > start and cash > 0]


def tiingo_dividends(client: TiingoEodClient, *, start: date, end: date,
                     sessions: SessionCalendar) -> DividendSource:
    """A `DividendSource` over Tiingo, fetching each symbol ONCE across [start, end] — the span
    every window the caller will ask about falls inside — and slicing it per window. ``sessions``
    is asked once per symbol, for the span, when its first window is read."""
    span: dict[str, list[dict[str, Any]] | str] = {}
    calendar: dict[str, list[date]] = {}

    def source(symbol: str, a: date, b: date) -> list[tuple[date, float]]:
        if a < start or b > end:
            raise DividendsUnknownError(f"{symbol}: window {a} → {b} is outside the span fetched "
                                   f"({start} → {end})")
        if symbol not in span:
            try:   # Tiingo spells a share class with a hyphen (brk-b) where Polygon uses a dot
                span[symbol] = client.daily_rows(symbol.replace(".", "-"), start=start, end=end)
            except (HttpError, ValueError) as exc:
                span[symbol] = f"the Tiingo request failed ({type(exc).__name__})"
        rows = span[symbol]
        if isinstance(rows, str):
            raise DividendsUnknownError(f"{symbol}: {rows}")
        if symbol not in calendar:
            try:
                calendar[symbol] = sessions(symbol, start, end)
            except (HttpError, EodError, ValueError) as exc:
                raise DividendsUnknownError(f"{symbol}: the calendar could not be read "
                                            f"({type(exc).__name__})") from exc
        return ex_date_yields(rows, a, b, sessions=calendar[symbol], symbol=symbol)
    return source


#: why a symbol is reserved, as the scorecard prints it
LEDGER, BENCHMARK, FOLLOWED = "ledger", "benchmark", "followed"


def reserved_symbols(data_dir: Path) -> dict[str, tuple[str, ...]]:
    """THE SYMBOLS SCORING AND THE MONITOR MUST BE ABLE TO READ, each with why — in Tiingo's
    spelling (`tiingo_symbol`), the key its monthly cap counts (2026-10-28).

    Tiingo's plan refuses every symbol NEW to the key once 500 have been looked up in a calendar
    month, and every reader here fails loud on a refusal: a RESOLVED ledger row stops scoring
    (`TotalReturnUnknownError`), a basket is refused, a monitor leg stops the run. So these are
    the symbols nothing else may spend the month's lookups ahead of:

    - every ledger row's name (``snapshots/decision_ledger.jsonl``, the committed record) and the
      benchmark a row names, when it names one;
    - the monitor's three benchmarks (`vinci.monitor` IWM / MDY / SPY — IWM is also scoring's
      default) and every benchmark its committed assignments name;
    - every name ever on the follow list (``followed.json``): a sleeve's passive basket reads
      each member's dividends, an unfollowed one too for a verdict entered while it was followed.

    ``data_dir`` is a checkout's ``data/``. An absent file adds nothing; a file that cannot be
    read raises."""
    from vinci.followed import follow_records
    from vinci.monitor import (
        BENCHMARK_LARGE,
        BENCHMARK_MID,
        BENCHMARK_SMALL,
        BenchmarkAssignment,
    )

    why: dict[str, set[str]] = {}

    def add(symbol: str, reason: str) -> None:
        why.setdefault(tiingo_symbol(symbol), set()).add(reason)

    ledger = data_dir / "snapshots" / "decision_ledger.jsonl"
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                add(str(row["ticker"]), LEDGER)
                if row.get("benchmark"):
                    add(str(row["benchmark"]), BENCHMARK)
    for b in (BENCHMARK_SMALL, BENCHMARK_MID, BENCHMARK_LARGE):
        add(b, BENCHMARK)
    # read beside ``data_dir`` itself: `monitor.read_assignments` takes a checkout root and would
    # read nothing, quietly, under any folder not named ``data``
    assignments = data_dir / "monitor" / "benchmark_assignments.json"
    if assignments.exists():
        for raw in json.loads(assignments.read_text()).values():
            add(BenchmarkAssignment.model_validate(raw).benchmark, BENCHMARK)
    for r in follow_records(data_dir / "followed.json"):
        add(r.ticker, FOLLOWED)
    return {s: tuple(sorted(r)) for s, r in sorted(why.items())}


def default_dividends(*, start: date, end: date, sessions: SessionCalendar) -> DividendSource:
    """Tiingo where ``TIINGO_API_KEY`` is set, its coverage checked against ``sessions``. Without
    it, a source that raises on every window — so a total return that cannot be read fails where it
    is used, never as a quiet price return."""
    if not os.environ.get("TIINGO_API_KEY"):
        def unavailable(symbol: str, a: date, b: date) -> list[tuple[date, float]]:
            raise DividendsUnknownError(f"{symbol}: no TIINGO_API_KEY in the environment — total "
                                   f"return needs Tiingo's dividends")
        return unavailable
    # a week of slack before the earliest window, so its entry session's row is always inside
    return tiingo_dividends(TiingoEodClient.from_config(), start=start - timedelta(days=7),
                            end=end, sessions=sessions)
