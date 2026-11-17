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

FOUR STATUSES — three from the operator's marking (2026-11-13, "go ahead", issue #1004), and
``intake`` for a name's way in (W27 review, #1092):
- ``intake``  — taken into coverage, its first page not yet committed: assembled like an active
  name, and its page optional, so a first build refused or failed after its spend leaves every
  reader working. The PR that commits its first page appends its move to ``active`` (or ``watch``).
- ``active``  — covered and worked: assembled, and its page required, so an active page that
  vanishes is refused.
- ``watch``   — covered, with its committed page kept as it is and no paid rebuild until the name
  goes active. NOT the scenario record's ``watch`` verdict status (``vinci/scenarios.py``), which
  is a standing-trigger record that is not a position: IT's record is a ``watch`` and IT is
  coverage-``active``.
- ``retired`` — out of coverage: no page, no assembly, and its underwrite record archived.

COVERAGE IS NOT A VERDICT. A status decides the work a name gets; it is never a scored call. A
retired name's live ledger decision is still scored to its horizon (otherwise retiring would be
a quiet void), so nothing here touches the book, the ledger or the spread.

THE PAGE IS CHECKED AGAINST THE ROSTER, NEVER THE DEFINITION. ``covered_pages`` returns the
covered names only once the committed pages agree, and otherwise raises naming every
disagreement: a page whose name has no line, a page for a retired name, and a covered name with
no page. A page is its ``dossier.json``, never its folder: a git-ignored ``llm_call.log`` outlives
a retired page in a checkout that held it.

A WATCH PAGE SAYS SO, AND NAMES WHAT IT KEEPS WRONG (STATE row 41 (b), B's design on issue #1004).
``watch_notice`` is what both renderers print near the top of a watch page: the move's date and
ruling, that the page is kept as committed with no paid rebuild until the name goes active, and the
page's known defects. It is read from the roster at RENDER time, never written into
``dossier.json``, so a move to active removes it at the next render with no page edit.

THE DEFECTS ARE A SECOND FILE, ``data/watch_defects.json``, NOT A FIELD ON THE MOVE. A move is a
coverage decision and is refused when it repeats a status, so a defect fixed by a $0 refresh while
its name stays on watch could not be recorded on the roster at all; and the roster's six fields
are strict on every line, so a seventh would rewrite an append-only log. A defect is a fact about
a PAGE: each entry names its STATE row and record, and the page field it lives in with the value
it holds there. ``watch_notice`` refuses a page whose field no longer holds that value, so a page
that is rebuilt or refreshed past its defect stops rendering until the entry is removed, and the
line cannot go on naming a defect the page no longer has.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

#: the roster's file name, under the data directory (``data/coverage_roster.jsonl``)
ROSTER_NAME = "coverage_roster.jsonl"
#: every status a move can name, in the order the module docstring defines them
STATUSES = ("intake", "active", "watch", "retired")
#: the statuses whose names must have a committed page
COVERED = frozenset({"active", "watch"})
#: the statuses a page is assembled for
BUILDABLE = frozenset({"intake", "active"})
#: a line's keys, in the order ``render_line`` writes them
FIELDS = ("date", "ticker", "status", "ruling", "source", "record")
#: the known-defect file's name, under the data directory (``data/watch_defects.json``)
DEFECTS_NAME = "watch_defects.json"
#: a defect's keys, in the order ``render_defects`` writes them
DEFECT_FIELDS = ("defect", "state_row", "record", "page_field", "page_value", "measured")
#: the statuses a defect may be listed for: a watch page prints it, and an active name keeps its
#: entry until the rebuild moves the page's value (which ``watch_notice``'s check then refuses)
DEFECT_STATUSES = frozenset({"watch", "active"})

_TICKER = re.compile(r"[A-Z][A-Z0-9.\-]{0,9}")


class CoverageRosterError(ValueError):
    """The roster is absent, or cannot be read as a roster."""


class CoverageMismatchError(CoverageRosterError):
    """The committed pages disagree with the roster."""


class NotActiveError(CoverageRosterError):
    """A name was asked to be assembled while its roster status is not ``active``."""


class WatchDefectError(CoverageRosterError):
    """The known-defect file is absent, cannot be read, or disagrees with a page or the roster."""


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


def retired(data_dir: Path) -> dict[str, Move]:
    """The names whose latest move is ``retired``, with that move."""
    return {t: m for t, m in sorted(current(data_dir).items()) if m.status == "retired"}


def paged(dossiers_dir: Path) -> set[str]:
    """The names with a committed page: the FACT the roster is checked against."""
    return {p.parent.name for p in dossiers_dir.glob("*/dossier.json")}


def mismatches(latest: Mapping[str, Move], pages: set[str]) -> list[str]:
    """Every way the pages disagree with the roster, sorted by name; [] when they agree. An
    ``intake`` name agrees with or without its page."""
    out: list[str] = []
    for t in sorted(set(latest) | pages):
        move = latest.get(t)
        if move is None:
            out.append(f"{t} has a committed page and no line in the coverage roster")
        elif move.status in COVERED and t not in pages:
            out.append(f"{t} is {move.status} on the roster and has no committed page "
                       f"({move.cite()})")
        elif move.status == "retired" and t in pages:
            out.append(f"{t} is {move.status} on the roster and still has a committed page "
                       f"({move.cite()})")
    return out


def covered_pages(data_dir: Path) -> list[str]:
    """The names whose pages a reader walks, sorted — every active and watch name, and an intake
    name once its first page is committed — after every committed page agrees with the roster;
    raises ``CoverageMismatchError`` naming every disagreement otherwise. The one call a reader
    that walks the covered names makes."""
    latest = current(data_dir)
    pages = paged(data_dir / "dossiers")
    problems = mismatches(latest, pages)
    if problems:
        raise CoverageMismatchError(
            f"the committed pages disagree with {roster_path(data_dir)} on {len(problems)} "
            f"name(s): " + "; ".join(problems))
    return sorted(t for t, m in latest.items()
                  if m.status in COVERED or (m.status == "intake" and t in pages))


def require_buildable(data_dir: Path, ticker: str) -> Move:
    """The name's latest move, when it is ``intake`` or ``active``; raises ``NotActiveError``
    otherwise.

    Assembly is the work an active name gets, and an intake name's first page: a ``watch`` page is
    kept as committed until the name goes active, a ``retired`` name has no page, and a name with
    no line was never taken into coverage. Asked BEFORE any model call, so a refusal costs
    nothing."""
    move = current(data_dir).get(ticker.upper())
    if move is None:
        raise NotActiveError(
            f"{ticker.upper()} has no line in {roster_path(data_dir)} — append its move to "
            f"intake (a first page) or active, with the ruling, before its page is assembled")
    if move.status not in BUILDABLE:
        raise NotActiveError(
            f"{move.cite()} — only an intake or active name is assembled; append a move to "
            f"active, with the ruling, first")
    return move


# --- the watch notice: the line a watch page prints, and the defects it names ---------------------


@dataclass(frozen=True)
class Defect:
    """One known defect a page keeps: what it is, the STATE row and record that track it, and the
    page field it lives in with the value it holds there."""

    defect: str
    state_row: int
    record: str
    page_field: str
    page_value: str | int | float | bool
    measured: str

    def cite(self) -> str:
        return f"STATE row {self.state_row}; {self.record}"

    def sentence(self) -> str:
        """The defect as the page prints it, its citation closing the sentence."""
        return f"{self.defect} ({self.cite()})."


@dataclass(frozen=True)
class WatchNotice:
    """What a watch page prints near its top: its move, and the defects it keeps until active."""

    move: Move
    defects: tuple[Defect, ...]

    def head(self) -> str:
        return f"Frozen since {self.move.date}: {self.move.ticker} is on watch."

    def ruling(self) -> str:
        where = self.move.source + (f"; {self.move.record}" if self.move.record else "")
        return f"The operator's ruling: \"{self.move.ruling}\" ({where})."

    def kept(self) -> str:
        return (f"This page is kept as committed, with no paid rebuild, until "
                f"{self.move.ticker} goes active.")

    @staticmethod
    def defects_head() -> str:
        return "Known defects it keeps until then:"


def defects_path(data_dir: Path) -> Path:
    return data_dir / DEFECTS_NAME


def render_defects(defects: Mapping[str, tuple[Defect, ...]]) -> str:
    """The one canonical form of the file: ``read_defects`` refuses any other."""
    obj = {t: [{"defect": d.defect, "state_row": d.state_row, "record": d.record,
                "page_field": d.page_field, "page_value": d.page_value,
                "measured": d.measured} for d in defects[t]] for t in sorted(defects)}
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def _defect(raw: object, where: str) -> Defect:
    if not isinstance(raw, dict) or tuple(raw) != DEFECT_FIELDS:
        got = tuple(raw) if isinstance(raw, dict) else type(raw).__name__
        raise WatchDefectError(f"{where}: a defect carries exactly {DEFECT_FIELDS}, in that "
                               f"order; got {got}")
    for key in ("defect", "measured"):
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise WatchDefectError(f"{where}: {key} must be a non-empty string, got "
                                   f"{raw[key]!r}")
    if raw["defect"].rstrip().endswith("."):
        raise WatchDefectError(f"{where}: a defect ends without a full stop — its citation "
                               f"closes the sentence (\"… (STATE row N; record).\")")
    row = raw["state_row"]
    if not isinstance(row, int) or isinstance(row, bool) or row < 1:
        raise WatchDefectError(f"{where}: state_row must be a STATE.md row number, got {row!r}")
    record = raw["record"]
    if not (isinstance(record, str) and record.startswith("docs/records/")
            and record.endswith(".md")):
        raise WatchDefectError(f"{where}: record must be a docs/records/*.md path, got "
                               f"{record!r}")
    field = raw["page_field"]
    if not isinstance(field, str) or not field.startswith("/") or field == "/":
        raise WatchDefectError(f"{where}: page_field must be a JSON pointer into dossier.json "
                               f"(\"/mechanical/...\"), got {field!r}")
    value = raw["page_value"]
    if value is None or not isinstance(value, (str, int, float, bool)):
        raise WatchDefectError(f"{where}: page_value must be the scalar the page holds at "
                               f"page_field, got {value!r}")
    return Defect(defect=raw["defect"], state_row=row, record=record, page_field=field,
                  page_value=value, measured=raw["measured"])


def read_defects(data_dir: Path) -> dict[str, tuple[Defect, ...]]:
    """Every name's known defects, after the whole file is checked.

    AN ABSENT FILE RAISES, as an absent roster does: read as "no defects", every watch page would
    print its line without the defects it keeps, and look clean. A name with no defect is simply
    not a key."""
    path = defects_path(data_dir)
    if not path.is_file():
        raise WatchDefectError(f"no known-defect file at {path} — a watch page names its known "
                               f"defects from it, so none can be shown as absent without it")
    text = path.read_text(encoding="utf-8")
    try:
        obj = json.loads(text)
    except ValueError as exc:
        raise WatchDefectError(f"{path}: not JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise WatchDefectError(f"{path}: the file maps each ticker to its defects")
    out: dict[str, tuple[Defect, ...]] = {}
    for ticker, raws in obj.items():
        if not isinstance(ticker, str) or not _TICKER.fullmatch(ticker):
            raise WatchDefectError(f"{path}: {ticker!r} is not an upper-case symbol")
        if not isinstance(raws, list) or not raws:
            raise WatchDefectError(f"{path}: {ticker} lists no defect — a name with none is "
                                   f"not a key")
        out[ticker] = tuple(_defect(r, f"{path}: {ticker}[{i}]") for i, r in enumerate(raws))
    if render_defects(out) != text:
        raise WatchDefectError(f"{path}: not in the canonical form render_defects writes "
                               f"(names sorted, two-space indent, one newline at the end)")
    return out


_MISSING = object()


def page_value(page: Mapping[str, Any], pointer: str) -> object:
    """The value at a JSON pointer (RFC 6901) into a page's JSON, or ``_MISSING``."""
    node: object = page
    for raw in pointer.split("/")[1:]:
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and key in node:
            node = node[key]
        elif isinstance(node, list) and key.isdigit() and int(key) < len(node):
            node = node[int(key)]
        else:
            return _MISSING
    return node


def defect_problems(latest: Mapping[str, Move], defects: Mapping[str, tuple[Defect, ...]],
                    pages: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Every way the defect file disagrees with the roster or the pages given, sorted by name;
    [] when they agree. ``pages`` holds the page JSON of the names to check (a renderer passes
    the one page it renders; the suite passes every committed page)."""
    out: list[str] = []
    for t in sorted(defects):
        move = latest.get(t)
        if move is None or move.status not in DEFECT_STATUSES:
            out.append(f"{t} has known defects listed and is "
                       f"{'not on the roster' if move is None else move.status} — a defect is "
                       f"listed only for a watch or active page")
            continue
        page = pages.get(t)
        if page is None:
            continue
        for d in defects[t]:
            got = page_value(page, d.page_field)
            if got is _MISSING:
                out.append(f"{t}: the page has no {d.page_field} — the defect \"{d.defect}\" "
                           f"({d.cite()}) is bound to a field the page does not hold")
            elif type(got) is not type(d.page_value) or got != d.page_value:
                out.append(f"{t}: {d.page_field} holds {got!r}, not the {d.page_value!r} the "
                           f"defect \"{d.defect}\" ({d.cite()}) was measured at — the page "
                           f"moved past it; remove or re-measure the entry")
    return out


def watch_notice(data_dir: Path, ticker: str,
                 page: Mapping[str, Any]) -> WatchNotice | None:
    """The notice a page prints near its top, or None when its name is not on watch.

    ``page`` is the page's JSON as committed (``dossier_json``), checked against every defect
    listed for it: a defect whose field no longer holds its value raises, so a watch page never
    prints a defect it no longer has. Read at render time from the tree being rendered."""
    latest = current(data_dir)
    move = latest.get(ticker.upper())
    if move is None or move.status != "watch":
        return None
    defects = read_defects(data_dir)
    problems = defect_problems(latest, defects, {move.ticker: page})
    if problems:
        raise WatchDefectError(f"{defects_path(data_dir)} disagrees with the roster or "
                               f"{move.ticker}'s page: " + "; ".join(problems))
    return WatchNotice(move=move, defects=defects.get(move.ticker, ()))
