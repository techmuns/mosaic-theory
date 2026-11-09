"""SPLITS — every return the fund scores divides two prices on ONE split basis (audit item F-D1,
2026-10-29).

WHY. A ledger row seals its entry price on the day it is logged, on that day's split basis, and the
row is append-only: the price is never rewritten. The price series it is divided into is kept on
the source's CURRENT basis instead — Polygon's ``adjusted=true`` bars, and `eod.client.restate_held`
rescaling held bars when Polygon restates them (#796, #846). Once a name splits inside a holding
window, the sealed entry is the one price left on the old basis, and ``exit ÷ sealed`` mixes two
bases: a flat stock that splits 2-for-1 scored −50%, and one that reverse-splits 1-for-10 scored
+900%, resolved, with no note. Scoring, the monitor's marks and its realized view, and
`close-position` all divided that way.

THE RULE (`entry_on_basis`). The entry a return divides by is the sealed price, unless a split the
exchange recorded after the entry session has moved the series' basis. The series' own close for
the entry session is set beside the sealed price: ``f = close ÷ sealed``.

- No split recorded after the entry session: f must be ~1, and the sealed price is used unchanged.
- Splits recorded: f must equal their product (each ``split_from ÷ split_to``), and the return
  divides by the series' entry-session close — both prices then on the series' basis — with a note
  naming f and each split. The ledger still holds the sealed price; only the read changes.
- Anything else raises `SplitBasisError`: an f no recorded split explains, or a recorded split the
  series was never restated for. Neither price is scored.

A CLOSE has no series to read (`close_on_basis`): the operator's exit price is a quote on its own
date, so the sealed entry is put on that date's basis by the splits recorded in (entry, exit].

THE EVIDENCE IS THE SPLITS REFERENCE, NOT THE ``+restated`` TAG. `Store.restate_bars` tags a bar
this repo rescaled, but a bar the source re-served after the split is on the new basis with no tag:
`Store.write_prices` replaces the whole row, source column included, so every session inside a
refresh's `RESTATE_WINDOW_DAYS` and every bar of a store built after the split reads plain
``polygon-grouped``. Requiring the tag would refuse a correct store. The tag is named in the note
when the bar carries it; what decides is that f equals a split the reference records.

A SPLIT IS CONFIRMED BY A SECOND VENDOR (TeamNostra fix request 2, RF-D1 and RF-D2, 2026-11-09).
The rule above reads ONE record. When Polygon is late on both feeds — its bars served as traded and
never restated, its reference silent — the sealed price equals the store's unrestated entry close,
f is 1, no split is recorded, and the return divides across a ×0.5 step: a flat 2-for-1 scored
−50%, resolved, with no note. With the reference late alone, `close_on_basis` had nothing to scale
by and `close-position` printed −50% and wrote the close. So every production source is now
`ConfirmedSplits`: Polygon's reference, CONFIRMED by Tiingo's ``splitFactor`` rows over the span
the run reads. Tiingo puts the factor on the execution date — measured on GOOGL's real rows,
20.0 on 2022-07-18, the date Polygon records (``tests/fixtures/splits_reference/``). The two must
record the same splits, on the same dates, at the same ratio; anything else raises
`SplitsUnconfirmedError`, a `SplitsUnknownError`, so every caller that refuses an unread
reference refuses a split one vendor alone records. A ratio of two STORED closes — a benchmark, a
basket member — has no sealed price to hold the store against; across a confirmed split it is held
against Tiingo's unadjusted close for its first session instead (`leg_on_basis`).

What no rule here can see: a split NO vendor records — both Polygon feeds and Tiingo late at once.
The store's step is then the only trace, and the price scorecard (`quality.sources.prices`) is what
flags it.
"""
from __future__ import annotations

import math
import os
from collections.abc import Callable, Sequence
from datetime import date
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from vinci.config import Config
from vinci.eod.client import RESTATE_TOL, EodError, PolygonEodClient, SessionCalendar
from vinci.eod.dividends import TIINGO_LEAD
from vinci.eod.tiingo import TiingoEodClient
from vinci.netcache import HttpError


class Split(BaseModel, frozen=True):
    """One split as Polygon's reference records it: ``split_from`` old shares became ``split_to``
    new ones on ``execution_date`` (2-for-1: from 1, to 2; 1-for-10: from 10, to 1)."""

    execution_date: date
    split_from: float
    split_to: float

    @property
    def price_factor(self) -> float:
        """What the split does to a price: ``split_from ÷ split_to`` (a 2-for-1 halves it)."""
        return self.split_from / self.split_to

    def label(self) -> str:
        return f"{self.split_to:g}-for-{self.split_from:g} on {self.execution_date}"


#: symbol → every split the reference records for it, in any order. Raises `SplitsUnknownError`
#: when the reference cannot be read — never an empty list for a symbol it could not read.
SplitSource = Callable[[str], list[Split]]


class SplitsUnknownError(ValueError):
    """The splits reference could not be read for a symbol. Never a "no splits": the caller fails
    loud, as it does on unknown dividends."""


class SplitsUnconfirmedError(SplitsUnknownError):
    """Polygon's splits reference and Tiingo's ``splitFactor`` rows record different splits over
    the span read. A split one vendor alone records is not confirmed on one basis, so the record is
    UNKNOWN: every caller refuses it exactly as it refuses an unread reference (RF-D1, RF-D2)."""


class SplitBasisError(RuntimeError):
    """The sealed entry and the price series disagree, and no recorded split explains it."""


def parse_splits(rows: list[dict[str, Any]], *, symbol: str) -> list[Split]:
    """Polygon's ``/v3/reference/splits`` result rows → `Split`s. A row for another ticker, or one
    without a date or a positive ratio, raises `SplitsUnknownError`: a guessed ratio is worse than
    none. Pure, so it is pinned on the real responses offline."""
    out: list[Split] = []
    for r in rows:
        try:
            s = Split(execution_date=date.fromisoformat(str(r["execution_date"])),
                      split_from=float(r["split_from"]), split_to=float(r["split_to"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise SplitsUnknownError(f"{symbol}: an unreadable split row ({exc!r})") from exc
        if str(r.get("ticker", symbol)) != symbol:
            raise SplitsUnknownError(f"{symbol}: the reference answered with a split for "
                                     f"{r.get('ticker')!r} ({s.execution_date})")
        if not (s.split_from > 0 and s.split_to > 0):
            raise SplitsUnknownError(f"{symbol} {s.execution_date}: split ratio "
                                     f"{s.split_from:g}→{s.split_to:g} is not positive")
        out.append(s)
    return out


def polygon_splits(client: PolygonEodClient) -> SplitSource:
    """A `SplitSource` over Polygon's splits reference: one cached request per symbol (a day), every
    split it records, read once per source."""
    seen: dict[str, list[Split]] = {}

    def source(symbol: str) -> list[Split]:
        if symbol not in seen:
            try:
                seen[symbol] = parse_splits(client.splits_reference(symbol), symbol=symbol)
            except (HttpError, EodError) as exc:
                raise SplitsUnknownError(f"{symbol}: the splits reference request failed "
                                         f"({type(exc).__name__})") from exc
        return list(seen[symbol])
    return source


def _polygon_reference(config: Config | None,
                       client: PolygonEodClient | None) -> SplitSource:
    """Polygon's reference where ``POLYGON_API_KEY`` is set — through ``client`` when the caller
    already holds one, so its requests share that client's pacing (the plan serves ~5 a minute).
    Without a key, a source that raises on every symbol — so a basis that cannot be checked fails
    where it is used, never as an unchecked sealed price."""
    if client is not None:
        return polygon_splits(client)
    if not os.environ.get("POLYGON_API_KEY"):
        def unavailable(symbol: str) -> list[Split]:
            raise SplitsUnknownError(f"{symbol}: no POLYGON_API_KEY in the environment — the "
                                     f"split basis is read from Polygon's splits reference")
        return unavailable
    return polygon_splits(PolygonEodClient.from_config(config))


def _positive_number(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def tiingo_split_record(rows: list[dict[str, Any]], *, start: date, end: date,
                        sessions: Sequence[date], symbol: str) -> list[Split]:
    """THE SECOND RECORD: the splits Tiingo's daily rows hold in (``start``, ``end``], oldest
    first — each row whose ``splitFactor`` is not 1, as ``factor``-for-1 on that row's date (the
    execution date; a reverse 1-for-10 serves 0.1). Pure, so it is pinned on real rows offline.

    UNKNOWN IS NEVER "NO SPLIT": a split on a row Tiingo did not serve would read as none, so every
    session in ``sessions`` (the name's own, a `SessionCalendar`'s answer) inside [start, end]
    needs a row, the calendar must hold one, and every factor must be a positive number — else
    `SplitsUnknownError`."""
    have: dict[date, float] = {}
    for r in rows:
        try:
            d = date.fromisoformat(str(r["date"])[:10])
            factor = r["splitFactor"]
        except (KeyError, TypeError, ValueError) as exc:
            raise SplitsUnknownError(f"{symbol}: an unreadable Tiingo row ({exc!r})") from exc
        if not _positive_number(factor):
            raise SplitsUnknownError(f"{symbol} {d}: Tiingo's splitFactor {factor!r} is not a "
                                     f"positive number")
        have[d] = float(factor)
    window = [s for s in sessions if start <= s <= end]
    if not window:
        raise SplitsUnknownError(f"{symbol}: the calendar holds no session in {start} → {end}, so "
                                 f"Tiingo's split record cannot be checked")
    missing = [s for s in window if s not in have]
    if missing:
        raise SplitsUnknownError(
            f"{symbol}: Tiingo holds no row for {len(missing)} session(s) the name traded in "
            f"{start} → {end} (first {missing[0]}) — a split there would be missed, so its split "
            f"record is unknown")
    return [Split(execution_date=d, split_from=1.0 / f if f < 1 else 1.0,
                  split_to=1.0 if f < 1 else f)
            for d, f in sorted(have.items()) if start < d <= end and f != 1.0]


def _row_day(r: dict[str, Any], symbol: str) -> date:
    try:
        return date.fromisoformat(str(r["date"])[:10])
    except (KeyError, TypeError, ValueError) as exc:
        raise SplitsUnknownError(f"{symbol}: an unreadable Tiingo row ({exc!r})") from exc


def _agree(a: Sequence[Split], b: Sequence[Split]) -> bool:
    """The same splits on the same dates, each ratio within `RESTATE_TOL`."""
    return len(a) == len(b) and all(
        x.execution_date == y.execution_date
        and abs(x.price_factor / y.price_factor - 1.0) <= RESTATE_TOL
        for x, y in zip(a, b, strict=True))


def _named(splits: Sequence[Split]) -> str:
    return ", ".join(s.label() for s in splits) or "no split"


@runtime_checkable
class AnchoredSplitSource(Protocol):
    """A `SplitSource` that also holds a second vendor's close AS TRADED — what `leg_on_basis`
    holds a stored ratio to across a split. Structural, so a wrapper that forwards
    ``unadjusted_close`` keeps the anchor (`ConfirmedSplits` is the production one)."""

    def __call__(self, symbol: str) -> list[Split]: ...

    def unadjusted_close(self, symbol: str, day: date) -> float | None: ...


class ConfirmedSplits:
    """A `SplitSource` whose answer two vendors agree on (RF-D1, RF-D2; see the module note).

    ``reference`` is Polygon's splits reference; ``rows(symbol)`` Tiingo's daily rows over
    [``start``, ``end``], the span every window the caller asks about falls inside; ``sessions``
    the name's own sessions, against which Tiingo's coverage is checked (`tiingo_split_record`).
    Asked for a symbol, it returns EVERY split the reference records, once the splits it records
    in (start, end] are the ones Tiingo records there; otherwise `SplitsUnconfirmedError`. A
    reference or rows that cannot be read raise `SplitsUnknownError`. Each symbol is read once.

    A split the reference records AFTER ``end`` is outside every window the caller reads and is
    returned unconfirmed, as before: `entry_on_basis` still holds it to the series' own close."""

    def __init__(self, reference: SplitSource, rows: Callable[[str], list[dict[str, Any]]], *,
                 start: date, end: date, sessions: SessionCalendar) -> None:
        self._reference, self._rows, self._sessions = reference, rows, sessions
        self.start, self.end = start, end
        self._seen: dict[str, list[Split]] = {}
        self._failed: dict[str, SplitsUnknownError] = {}
        self._closes: dict[str, dict[date, float]] = {}

    def _read_rows(self, symbol: str) -> list[dict[str, Any]]:
        try:   # Tiingo spells a share class with a hyphen (brk-b), as `tiingo_dividends` asks
            return self._rows(symbol.replace(".", "-"))
        except (HttpError, ValueError) as exc:
            raise SplitsUnknownError(f"{symbol}: the Tiingo request failed "
                                     f"({type(exc).__name__}), so its split record cannot be "
                                     f"confirmed") from exc

    def __call__(self, symbol: str) -> list[Split]:
        if symbol in self._failed:
            raise self._failed[symbol]
        if symbol not in self._seen:
            try:
                self._seen[symbol] = self._confirm(symbol)
            except SplitsUnknownError as exc:
                # a failure is read once too, as `tiingo_dividends` keeps one: every row sharing a
                # benchmark would otherwise re-request both vendors, retries and pacing included
                self._failed[symbol] = exc
                raise
        return list(self._seen[symbol])

    def _confirm(self, symbol: str) -> list[Split]:
        recorded = self._reference(symbol)
        rows = self._read_rows(symbol)
        try:
            sessions = self._sessions(symbol, self.start, self.end)
        except (HttpError, EodError, ValueError) as exc:
            raise SplitsUnknownError(f"{symbol}: the calendar could not be read "
                                     f"({type(exc).__name__})") from exc
        # A SESSION TIINGO HAS NOT SERVED IS UNKNOWN UNTIL IT HAS (review round 1, Codex P1 on
        # #943). Round 0 let Tiingo trail the calendar by a market closure and read its record only
        # through the last day it served. But a split ON a session it had not served, with Polygon
        # late on both feeds, left both compared records empty — confirmed — and a flat 2-for-1
        # scored −50% again: RF-D1 through the lag. So every session the calendar holds in the
        # span needs Tiingo's row. The cost is a loud, temporary refusal in the hours between
        # Polygon posting a session and Tiingo posting it: re-run once Tiingo has.
        served = [d for r in rows if self.start <= (d := _row_day(r, symbol)) <= self.end]
        newest = max((d for d in sessions if self.start <= d <= self.end), default=None)
        if served and newest is not None and max(served) < newest:
            raise SplitsUnknownError(
                f"{symbol}: Tiingo's rows end {max(served)}, and the name's newest session "
                f"{newest} is not served yet — a split there could not be confirmed, so its split "
                f"record is unknown until Tiingo serves it (re-run once it has)")
        second = tiingo_split_record(rows, start=self.start, end=self.end,
                                     sessions=sessions, symbol=symbol)
        first = splits_between(recorded, self.start, self.end)
        if not _agree(first, second):
            raise SplitsUnconfirmedError(
                f"{symbol}: in ({self.start}, {self.end}] Polygon's splits reference records "
                f"{_named(first)} and Tiingo's rows record {_named(second)}, so the split record "
                f"cannot be confirmed — a split one vendor alone records may be one the other has "
                f"not caught up with, and no return is read across it.")
        self._closes[symbol] = {date.fromisoformat(str(r["date"])[:10]): float(r["close"])
                                for r in rows if _positive_number(r.get("close"))}
        return recorded

    def unadjusted_close(self, symbol: str, day: date) -> float | None:
        """Tiingo's close for ``day`` AS TRADED (unadjusted), once ``symbol``'s record is
        confirmed — the anchor a stored ratio is held to (`leg_on_basis`). None when not served."""
        self(symbol)
        return self._closes[symbol].get(day)


def default_splits(config: Config | None = None, *, start: date, end: date,
                   sessions: SessionCalendar, client: PolygonEodClient | None = None,
                   tiingo: TiingoEodClient | None = None) -> SplitSource:
    """THE PRODUCTION SPLIT SOURCE: Polygon's reference CONFIRMED by Tiingo's ``splitFactor``
    (`ConfirmedSplits`) over [``start`` − `TIINGO_LEAD`, ``end``] — the span `default_dividends`
    reads, so Tiingo's rows are the response the dividend read already cached and no symbol is
    added to the plan's monthly lookups. ``client`` / ``tiingo`` share a caller's clients (and their
    pacing); without one, each is built from ``config``. Without ``TIINGO_API_KEY``, a source that
    raises on every symbol: a split basis one vendor cannot confirm is never read as checked."""
    reference = _polygon_reference(config, client)
    if tiingo is None and not os.environ.get("TIINGO_API_KEY"):
        def unconfirmable(symbol: str) -> list[Split]:
            raise SplitsUnknownError(f"{symbol}: no TIINGO_API_KEY in the environment — a split "
                                     f"is confirmed against Tiingo's splitFactor before any "
                                     f"return is read across it")
        return unconfirmable
    lead = start - TIINGO_LEAD
    held = tiingo

    def rows(symbol: str) -> list[dict[str, Any]]:
        nonlocal held
        if held is None:
            held = TiingoEodClient.from_config(config)
        return held.daily_rows(symbol, start=lead, end=end)
    return ConfirmedSplits(reference, rows, start=lead, end=end, sessions=sessions)


def splits_between(splits: Sequence[Split], after: date, through: date) -> list[Split]:
    """The splits executed in ``(after, through]``, oldest first. A split ON ``after`` is already in
    that day's prices, so it is never counted."""
    return sorted((s for s in splits if after < s.execution_date <= through),
                  key=lambda s: s.execution_date)


def entry_on_basis(*, who: str, sealed: float, session: date, session_close: float | None,
                   basis_through: date, splits: Sequence[Split],
                   session_source: str | None = None) -> tuple[float, str | None]:
    """The entry a return divides by, and the note that says why when it is not the sealed price
    (see the module note). ``session`` is the entry session the series resolves the sealed date to
    and ``session_close`` the series' close there (None when the series holds none);
    ``basis_through`` the last day whose splits the series can carry — the newest bar a store holds,
    or the day a source was read."""
    inside = splits_between(splits, session, basis_through)
    expected = math.prod(s.price_factor for s in inside)
    named = ", ".join(s.label() for s in inside)
    src = f" [{session_source}]" if session_source else ""
    if session_close is None:
        if not inside:
            return sealed, None
        raise SplitBasisError(
            f"{who}: the splits reference records {named} after the entry session {session}, and "
            f"the price series holds no close for that session to set beside the sealed "
            f"{sealed:g} — the entry cannot be put on the exit's basis, so it is not scored")
    if not (sealed > 0 and session_close > 0):
        raise SplitBasisError(f"{who}: sealed {sealed!r} and entry-session close "
                              f"{session_close!r} must both be positive")
    f = session_close / sealed
    if not inside:
        if abs(f - 1.0) <= RESTATE_TOL:
            return sealed, None
        raise SplitBasisError(
            f"{who}: the sealed entry is {sealed:g} but the series' close for the entry session "
            f"{session} is {session_close:g}{src} (×{f:.6g}), and the splits reference records no "
            f"split in ({session}, {basis_through}] — a gap nothing explains, so neither price is "
            f"scored")
    if abs(f / expected - 1.0) <= RESTATE_TOL:
        return session_close, (
            f"{who}: ON ONE SPLIT BASIS — the sealed entry is {sealed:g} ({session}); the series' "
            f"close for that session is {session_close:g}{src}, ×{f:.6g}, which the splits "
            f"reference explains ({named}: ×{expected:.6g}). The return divides by "
            f"{session_close:g}; the ledger keeps the sealed price.")
    if abs(f - 1.0) <= RESTATE_TOL:
        raise SplitBasisError(
            f"{who}: the splits reference records {named} in ({session}, {basis_through}], but the "
            f"series' close for the entry session, {session_close:g}{src}, still equals the sealed "
            f"{sealed:g} — the series was not restated for it, so its later closes are on another "
            f"basis than its entry. Not scored.")
    raise SplitBasisError(
        f"{who}: the series' close for the entry session, {session_close:g}{src}, is ×{f:.6g} the "
        f"sealed {sealed:g}, but the splits reference records {named} (×{expected:.6g}) — the gap "
        f"is not the recorded split(s). Not scored.")


def leg_on_basis(*, who: str, symbol: str, start: date, start_close: float, end: date,
                 basis_through: date, splits: SplitSource,
                 start_source: str | None = None) -> str | None:
    """A ratio of two STORED closes over (``start``, ``end``] — a benchmark leg, a basket member —
    on one split basis (RF-D1). It has no sealed price to hold the store against, so it is checked
    only where it can go wrong: with no split recorded inside the window the ratio stands (None),
    exactly as before. Across a confirmed split, ``start_close`` (the store's close for ``start``,
    on the basis of ``basis_through``) is held against TIINGO'S UNADJUSTED close for the same
    session (`ConfirmedSplits.unadjusted_close`) as `entry_on_basis` holds a sealed price: ×the
    recorded splits → the store restated, the ratio stands, and the note says so; ×1 → not
    restated, and anything else → unexplained: `SplitBasisError`. A source with no second vendor's
    close raises too — a stored ratio across a split is never read unconfirmed. ``splits``
    raising `SplitsUnknownError` propagates."""
    recorded = splits(symbol)
    inside = splits_between(recorded, start, end)
    if not inside:
        return None
    anchor = (splits.unadjusted_close(symbol, start)
              if isinstance(splits, AnchoredSplitSource) else None)
    if anchor is None:
        raise SplitBasisError(
            f"{who}: {_named(inside)} falls inside ({start}, {end}], and no second vendor's close "
            f"for {start} is held to set the stored close against — a ratio of two stored closes "
            f"across a split is not read unconfirmed")
    if not start_close > 0:
        raise SplitBasisError(f"{who}: the stored close for {start}, {start_close!r}, is not "
                              f"positive")
    carried = splits_between(recorded, start, basis_through)
    expected = math.prod(s.price_factor for s in carried)
    f = start_close / anchor
    src = f" [{start_source}]" if start_source else ""
    if abs(f / expected - 1.0) <= RESTATE_TOL:
        return (f"{who}: ON ONE SPLIT BASIS — {_named(inside)} falls inside ({start}, {end}]; the "
                f"stored close for {start}, {start_close:g}{src}, is ×{f:.6g} Tiingo's {anchor:g} "
                f"as traded, which the recorded split(s) explain ({_named(carried)}: "
                f"×{expected:.6g}), so the store was restated and its two closes are read.")
    if abs(f - 1.0) <= RESTATE_TOL:
        raise SplitBasisError(
            f"{who}: {_named(inside)} falls inside ({start}, {end}], but the stored close for "
            f"{start}, {start_close:g}{src}, still equals Tiingo's {anchor:g} as traded — the "
            f"store was not restated for it, so its two closes sit on two bases. Not read.")
    raise SplitBasisError(
        f"{who}: the stored close for {start}, {start_close:g}{src}, is ×{f:.6g} Tiingo's "
        f"{anchor:g} as traded, but the recorded split(s) are ×{expected:.6g} "
        f"({_named(carried)}) — the gap is not the recorded split(s). Not read.")


def close_on_basis(*, who: str, sealed: float, entry_as_of: date, exit_as_of: date,
                   splits: Sequence[Split]) -> tuple[float, str | None]:
    """A close's sealed entry on its exit's basis: the exit price is a quote on its own date, so
    the entry is scaled by the splits recorded in (entry, exit]. Returns the entry and a note naming
    the splits, or the sealed price and None when there were none."""
    inside = splits_between(splits, entry_as_of, exit_as_of)
    if not inside:
        return sealed, None
    factor = math.prod(s.price_factor for s in inside)
    entry = sealed * factor
    return entry, (
        f"{who}: ON ONE SPLIT BASIS — the sealed entry {sealed:g} ({entry_as_of}) is put on the "
        f"exit's basis by {', '.join(s.label() for s in inside)} (×{factor:.6g}) = {entry:g}; "
        f"the realized return divides by {entry:g}, and the ledger keeps the sealed price.")
