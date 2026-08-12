"""The follow list, read as a WHOLE and AS OF A DATE — which names were followed under which book.

`vinci/dossier/assemble.py` reads this same file one ticker at a time (``_follow_entry``), because
assembly asks a per-name question: is THIS name followed, and why. The passive baseline asks two
complementary ones — which names would I have held if I had simply indexed the book, and *when*.

WHY THE DATES ARE REQUIRED (operator review P1 on #409). A roster read as "whatever is in the file
today" and applied to every historical verdict makes the append-only ledger NON-REPRODUCIBLE: adding
a quality name next month silently changes the comparator for a BUY recorded last month — including
over a window in which that name was not followed at all — and removing one changes it back. The
kill test's historical answer would then depend on future roster edits, which is the same
look-ahead the fund refuses everywhere else. So every entry states ``followed_since``, and the
basket for a verdict is the roster as it stood ON THAT VERDICT'S ENTRY DATE.

REMOVING A NAME IS A TOMBSTONE, NOT A DELETE. Set ``followed_until`` rather than dropping the
entry: a deleted entry takes its history with it and silently re-dates every basket that contained
it. ``followed_until`` is EXCLUSIVE — the last day held is the day before it.

WHY NOT REUSE THE DOSSIER READER: the scoring package must not import the dossier package (the same
layering the ledger already observes — see `vinci/cli.py` `_followed_identity`, resolved in the CLI
for exactly this reason). And this module cannot live in `vinci/sleeves.py` either: that registry
states out loud that it "must stay importable from anywhere" and imports nothing but `dataclasses`,
so putting file I/O in it would cost the property its own docstring promises.

TWO PARSERS OF ONE FILE IS A BUG CLASS THIS REPO HAS ALREADY PAID FOR, so the divergence is pinned
rather than hoped away: `tests/test_quality_baseline.py` asserts this reader and the dossier's agree
on the sleeve of every ticker in the COMMITTED `data/followed.json`, and that both refuse the same
malformed shapes. This reader is deliberately the stricter-or-equal of the two — it never skips an
entry it cannot classify, because a name that silently vanishes here does not vanish loudly: it
quietly shrinks the basket the sleeve is measured against, which moves the kill test's answer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from vinci.sleeves import require_sleeve


class FollowedListError(ValueError):
    """The follow list exists but cannot be read as a follow list."""


@dataclass(frozen=True)
class FollowRecord:
    """One followed name, with the window over which it was followed."""

    ticker: str
    sleeve: str
    since: date
    until: date | None = None   # EXCLUSIVE; None == still followed

    def held_on(self, d: date) -> bool:
        return self.since <= d and (self.until is None or d < self.until)


def _read_date(value: object, *, where: str, field: str) -> date:
    if not isinstance(value, str):
        raise FollowedListError(
            f"{where}: {field} must be an ISO date string (YYYY-MM-DD), got "
            f"{type(value).__name__} — a followed name with no start date cannot be placed in "
            f"time, and treating it as 'always followed' is exactly the look-ahead this field "
            f"exists to prevent.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise FollowedListError(f"{where}: {field} is not an ISO date: {value!r}") from exc


def follow_records(path: Path) -> tuple[FollowRecord, ...]:
    """Every follow entry, dated. An ABSENT file is the normal state (nothing followed) → ``()``.

    Anything else that cannot be read raises: a follow list that half-parses would silently
    redefine the basket.
    """
    if not path.exists():
        return ()
    try:
        doc = json.loads(path.read_text())
    except ValueError as exc:
        raise FollowedListError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise FollowedListError(
            f"{path} must be a JSON object mapping TICKER → {{reason, sleeve, followed_since}}, "
            f"got {type(doc).__name__}")

    out: list[FollowRecord] = []
    seen: set[str] = set()
    for raw_key, entry in doc.items():
        ticker = str(raw_key).upper()
        # THE SAME CASE-COLLISION REFUSAL THE DOSSIER READER MAKES. Folding `{"uber":…, "UBER":…}`
        # to one key would drop a member of the basket with nothing anywhere saying so.
        if ticker in seen:
            raise FollowedListError(
                f"{path}: {ticker} is listed more than once (keys differing only by case) — one "
                f"entry would be silently discarded. Merge them into a single entry.")
        seen.add(ticker)
        # A BARE STRING IS THE PRE-SLEEVE SHAPE, and it is refused here for the reason it is
        # refused at assembly: an untagged followed name has no sleeve, so it belongs to no
        # basket, and guessing one would put a megacap in whichever book happened to ask first.
        if not isinstance(entry, dict):
            raise FollowedListError(
                f"{path}: {ticker} must be an object with 'reason', 'sleeve' and "
                f"'followed_since', got {type(entry).__name__} — every followed name states which "
                f"strategy book it is judged under, and from when.")
        where = f"{path}: {ticker}"
        sleeve = require_sleeve(entry.get("sleeve"), where=where)
        since = _read_date(entry.get("followed_since"), where=where, field="followed_since")
        raw_until = entry.get("followed_until")
        until = (None if raw_until is None
                 else _read_date(raw_until, where=where, field="followed_until"))
        if until is not None and until <= since:
            raise FollowedListError(
                f"{where}: followed_until ({until}) is not after followed_since ({since}) — the "
                f"name would have been followed for no days at all.")
        out.append(FollowRecord(ticker=ticker, sleeve=sleeve, since=since, until=until))
    return tuple(sorted(out, key=lambda r: (r.sleeve, r.ticker)))


def followed_by_sleeve(path: Path) -> dict[str, tuple[str, ...]]:
    """Map each sleeve key → every ticker EVER followed under it, sorted.

    Time-blind by construction, so it answers "which names does this book cover" and never "what
    was the basket on date D" — for that, go through :class:`FollowRecord.held_on`.
    """
    by_sleeve: dict[str, list[str]] = {}
    for r in follow_records(path):
        by_sleeve.setdefault(r.sleeve, []).append(r.ticker)
    return {k: tuple(sorted(v)) for k, v in sorted(by_sleeve.items())}
