"""The COVERAGE ROSTER — which names the fund covers, read from one dated, committed file.

COVERAGE IS A DECISION, NOT A DIRECTORY LISTING (W27, issue #1004 item 6). Until this module the
code held no list of covered names: coverage was whichever ``data/dossiers/<T>/dossier.json`` was
committed. Retiring a name therefore meant changing everything that had quietly used a page as
its definition: MVST's retirement (#1044) touched 32 files, and AORT's (#942) went the same way.
``data/coverage_roster.jsonl`` is the list, and every reader that asks "which names" asks here.

THE FILE IS AN APPEND-ONLY LOG OF MOVES. One JSON object per line: a ``date``, a ``ticker``, the
``status`` it moves to, the operator's ``ruling`` in their own words, the ``source`` that carries
it (a PR, or an issue comment), and the ``record`` under ``docs/records/`` that explains it (or
null). A name's status is its LATEST line. A move is one appended line, never an edit and never a
delete — the way ``followed_until`` already works for the follow list — so the roster's history
is the file itself. Lines run in the order they were appended, their dates never running
backwards, with one move per name per day; each is written in one canonical form
(``render_line``), so the file is deterministic and a hand edit that reorders or reformats it is
refused rather than read.

THREE STATUSES (the operator's marking, 2026-11-13, "go ahead", issue #1004):
- ``active``  — covered and worked: the only status a page is assembled for.
- ``watch``   — covered, with its committed page kept as it is and no paid rebuild until the name
  goes active. NOT the scenario record's ``watch`` verdict status (``vinci/scenarios.py``), which
  is a standing-trigger record that is not a position: IT's record is a ``watch`` and IT is
  coverage-``active``.
- ``retired`` — out of coverage: no page, no assembly, and no freshness row for its record.

COVERAGE IS NOT A VERDICT. A status decides the work a name gets; it is never a scored call. A
retired name's live ledger decision is still scored to its horizon (otherwise retiring would be
a quiet void), so nothing here touches the book, the ledger or the spread.

THE PAGE IS CHECKED AGAINST THE ROSTER, NEVER THE DEFINITION. ``covered_pages`` returns the
covered names only once the committed pages agree, and otherwise raises naming every
disagreement: a page whose name has no line, a page for a retired name, and a covered name with
no page. A page is its ``dossier.json``, never its folder: a git-ignored ``llm_call.log`` outlives
a retired page in a checkout that held it.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

#: the roster's file name, under the data directory (``data/coverage_roster.jsonl``)
ROSTER_NAME = "coverage_roster.jsonl"
#: every status a move can name, in the order the module docstring defines them
STATUSES = ("active", "watch", "retired")
#: the statuses whose names have a committed page
COVERED = frozenset({"active", "watch"})
#: a line's keys, in the order ``render_line`` writes them
FIELDS = ("date", "ticker", "status", "ruling", "source", "record")

_TICKER = re.compile(r"[A-Z][A-Z0-9.\-]{0,9}")


class CoverageRosterError(ValueError):
    """The roster is absent, or cannot be read as a roster."""


class CoverageMismatchError(CoverageRosterError):
    """The committed pages disagree with the roster."""


class NotActiveError(CoverageRosterError):
    """A name was asked to be assembled while its roster status is not ``active``."""


@dataclass(frozen=True)
class Move:
    """One line of the roster: a name moved to a status on a date, by a ruling."""

    date: date
    ticker: str
    status: str
    ruling: str
    source: str
    record: str | None

    def cite(self) -> str:
        """The move as one line a refusal can print."""
        where = self.source + (f", {self.record}" if self.record else "")
        return f"{self.ticker} {self.status} since {self.date} (\"{self.ruling}\"; {where})"


def roster_path(data_dir: Path) -> Path:
    return data_dir / ROSTER_NAME


def render_line(move: Move) -> str:
    """The one canonical form of a line. ``read_moves`` refuses any line not written this way."""
    return json.dumps({"date": move.date.isoformat(), "ticker": move.ticker,
                       "status": move.status, "ruling": move.ruling, "source": move.source,
                       "record": move.record}, ensure_ascii=False)


def _text(obj: Mapping[str, object], key: str, where: str) -> str:
    value = obj[key]
    if not isinstance(value, str) or not value.strip():
        raise CoverageRosterError(f"{where}: {key} must be a non-empty string, got {value!r}")
    return value


def _move(line: str, where: str) -> Move:
    try:
        obj = json.loads(line)
    except ValueError as exc:
        raise CoverageRosterError(f"{where}: not JSON: {exc}") from exc
    if not isinstance(obj, dict) or tuple(obj) != FIELDS:
        got = tuple(obj) if isinstance(obj, dict) else type(obj).__name__
        raise CoverageRosterError(f"{where}: a move carries exactly {FIELDS}, in that order; "
                                  f"got {got}")
    raw_date = _text(obj, "date", where)
    try:
        when = date.fromisoformat(raw_date)
    except ValueError as exc:
        raise CoverageRosterError(f"{where}: date is not an ISO date: {raw_date!r}") from exc
    ticker = _text(obj, "ticker", where)
    if not _TICKER.fullmatch(ticker):
        raise CoverageRosterError(f"{where}: ticker {ticker!r} is not an upper-case symbol")
    status = _text(obj, "status", where)
    if status not in STATUSES:
        raise CoverageRosterError(f"{where}: {ticker}'s status {status!r} is not one of "
                                  f"{STATUSES}")
    record = obj["record"]
    if record is not None and not (isinstance(record, str) and record.startswith("docs/records/")
                                   and record.endswith(".md")):
        raise CoverageRosterError(f"{where}: {ticker}'s record must be null or a "
                                  f"docs/records/*.md path, got {record!r}")
    move = Move(date=when, ticker=ticker, status=status, ruling=_text(obj, "ruling", where),
                source=_text(obj, "source", where), record=record)
    if render_line(move) != line:
        raise CoverageRosterError(f"{where}: not in the canonical form render_line writes — "
                                  f"expected {render_line(move)}")
    return move


def read_moves(data_dir: Path) -> tuple[Move, ...]:
    """Every move, in file order, after the whole file is checked.

    AN ABSENT ROSTER RAISES. With no roster nothing can be said to be covered, and reading that as
    "no names" would let every reader below walk an empty fleet in silence."""
    path = roster_path(data_dir)
    if not path.is_file():
        raise CoverageRosterError(f"no coverage roster at {path} — every covered name is a line "
                                  f"there, so nothing can be read as covered without it")
    text = path.read_text(encoding="utf-8")
    if text and not text.endswith("\n"):
        raise CoverageRosterError(f"{path}: the last line has no newline — every move ends one")
    moves: list[Move] = []
    last: dict[str, Move] = {}
    for n, line in enumerate(text.split("\n")[:-1], 1):
        where = f"{path}:{n}"
        if not line:
            raise CoverageRosterError(f"{where}: a blank line — every line is one move")
        move = _move(line, where)
        if moves and move.date < moves[-1].date:
            raise CoverageRosterError(
                f"{where}: {move.ticker} {move.date} is dated before the line above it "
                f"({moves[-1].ticker} {moves[-1].date}) — a move is appended at the end, never "
                f"inserted, so the dates never run backwards")
        prior = last.get(move.ticker)
        if prior is not None and prior.date == move.date:
            raise CoverageRosterError(
                f"{where}: {move.ticker} moves twice on {move.date} — one move per name per day")
        if prior is not None and prior.status == move.status:
            raise CoverageRosterError(
                f"{where}: {move.ticker} is already {move.status} (since {prior.date}) — a move "
                f"changes a status, so this line records nothing")
        moves.append(move)
        last[move.ticker] = move
    if not moves:
        raise CoverageRosterError(f"{path} holds no move")
    return tuple(moves)


def current(data_dir: Path) -> dict[str, Move]:
    """Each name's latest move, by ticker."""
    out: dict[str, Move] = {}
    for move in read_moves(data_dir):
        out[move.ticker] = move
    return out


def covered(data_dir: Path) -> list[str]:
    """The names whose latest move is ``active`` or ``watch``, sorted. The roster alone: use
    ``covered_pages`` wherever the pages are read."""
    return sorted(t for t, m in current(data_dir).items() if m.status in COVERED)


def retired(data_dir: Path) -> dict[str, Move]:
    """The names whose latest move is ``retired``, with that move."""
    return {t: m for t, m in sorted(current(data_dir).items()) if m.status == "retired"}


def paged(dossiers_dir: Path) -> set[str]:
    """The names with a committed page: the FACT the roster is checked against."""
    return {p.parent.name for p in dossiers_dir.glob("*/dossier.json")}


def mismatches(latest: Mapping[str, Move], pages: set[str]) -> list[str]:
    """Every way the pages disagree with the roster, sorted by name; [] when they agree."""
    out: list[str] = []
    for t in sorted(set(latest) | pages):
        move = latest.get(t)
        if move is None:
            out.append(f"{t} has a committed page and no line in the coverage roster")
        elif move.status in COVERED and t not in pages:
            out.append(f"{t} is {move.status} on the roster and has no committed page "
                       f"({move.cite()})")
        elif move.status not in COVERED and t in pages:
            out.append(f"{t} is {move.status} on the roster and still has a committed page "
                       f"({move.cite()})")
    return out


def covered_pages(data_dir: Path) -> list[str]:
    """The covered names, sorted, once every committed page agrees with the roster; raises
    ``CoverageMismatchError`` naming every disagreement otherwise. The one call a reader that
    walks the covered names makes."""
    latest = current(data_dir)
    problems = mismatches(latest, paged(data_dir / "dossiers"))
    if problems:
        raise CoverageMismatchError(
            f"the committed pages disagree with {roster_path(data_dir)} on {len(problems)} "
            f"name(s): " + "; ".join(problems))
    return sorted(t for t, m in latest.items() if m.status in COVERED)


def require_active(data_dir: Path, ticker: str) -> Move:
    """The name's latest move, when it is ``active``; raises ``NotActiveError`` otherwise.

    Assembly is the work an ``active`` name gets: a ``watch`` page is kept as committed until the
    name goes active, a ``retired`` name has no page, and a name with no line has not been taken
    into coverage. Asked BEFORE any model call, so a refusal costs nothing."""
    move = current(data_dir).get(ticker.upper())
    if move is None:
        raise NotActiveError(
            f"{ticker.upper()} has no line in {roster_path(data_dir)} — append its move to "
            f"active, with the ruling, before its page is assembled")
    if move.status != "active":
        raise NotActiveError(
            f"{move.cite()} — only an active name is assembled; append a move to active, with "
            f"the ruling, first")
    return move
