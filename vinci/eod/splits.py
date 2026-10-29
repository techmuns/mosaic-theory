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
"""
from __future__ import annotations

import math
import os
from collections.abc import Callable, Sequence
from datetime import date
from typing import Any

from pydantic import BaseModel

from vinci.config import Config
from vinci.eod.client import RESTATE_TOL, EodError, PolygonEodClient
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


def default_splits(config: Config | None = None, *,
                   client: PolygonEodClient | None = None) -> SplitSource:
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
