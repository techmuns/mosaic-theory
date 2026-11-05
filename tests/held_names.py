"""THE HELD NAMES — six CIQ export packs no test reads until their auditor freezes its answer key.

TeamNostra, the independent auditor, keeps six CIQ export packs (exported 2026-10-28) as a BLIND
test set: BURL, MTB, RIVN, PCVX, NVO and PLD. A blind test proves an extractor only if nothing was
fitted to those exact files, so the standing operator rule is that no mosaic-theory code runs on
them — assemble, precheck, any extractor or CIQ reader — until TeamNostra freezes its key. This
suite is mosaic-theory code. On 2026-11-05 (#911) a run with `data/manual` linked to a CIQ folder
read BURL's real export: the suite parametrizes over every committed page, and nothing in it knew
the rule.

EVERY TEST THAT CAN REACH A CIQ EXPORT GOES THROUGH THIS LIST, and decides on the NAME, before any
file in the name's folder is opened:

* a PARAMETRIZATION over pages or CIQ folders takes `page_params(...)`. A held name keeps its case
  id and is SKIPPED with `held_reason`, so `-rs` says what was left out and why;
* a LOOP over pages or CIQ folders takes `without_held(...)`. The held names are dropped before the
  body runs, and the terminal summary lists every loop that dropped one, so a loop's total never
  silently means "every name but one".

Two checks hold the list in place:

* `refuse_held_open`, an audit hook `tests/conftest.py` installs, FAILS any test that opens a file
  under a held name's folder in this checkout's `data/manual` anyway — through a production path,
  a helper, a copy — before the file is read. It refuses OPENS: listing a folder's names reads no
  export, and `rglob` over `ciq-archive/` walks every folder in it;
* `tests/test_held_names.py` refuses a new loop or parametrization over pages or CIQ folders whose
  values reach a CIQ reader without passing through this module.

THE COMMITTED PAGE IS NOT THE EXPORT. BURL's committed `dossier.json` is public, and re-rendering a
committed page from its committed JSON is allowed (operator ruling D-D4). A test that reads only
committed JSON keeps the held pages. Where the guard cannot tell — the test names a CIQ reader it
never points at a page's export, or its page path is a temporary copy — the enumeration's statement
carries `# held-names: reads no CIQ export`: the author's declaration, which the audit hook still
checks in every linked run.

LIFTING IT: when TeamNostra freezes the key, remove the name from `HELD_NAMES` (and from its pin in
`tests/test_held_names.py`). Every skip and every left-out loop then runs the name again,
`test_the_real_burl_export_is_read_as_empty_not_broken` among them.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar

import pytest
from _pytest.mark.structures import ParameterSet

#: The six blind audit packs (TeamNostra, exported 2026-10-28). CIQ folder names are tickers.
HELD_NAMES: frozenset[str] = frozenset({"BURL", "MTB", "NVO", "PCVX", "PLD", "RIVN"})

#: The declaration that a page enumeration's values never reach a CIQ export.
NO_CIQ_READ = "# held-names: reads no CIQ export"

#: (where, ticker) for every name `without_held` dropped — the running test's id, or the calling
#: module at collection — printed in the terminal summary.
LEFT_OUT: list[tuple[str, str]] = []

#: (test id, path) for every open `refuse_held_open` refused.
REFUSED_OPENS: list[tuple[str, str]] = []

#: The running test's id; `tests/conftest.py` keeps it current.
CURRENT_TEST: list[str] = ["<collection>"]

ROOT = Path(__file__).resolve().parents[1]

T = TypeVar("T")


def held_reason(ticker: str) -> str:
    """The skip reason: the name, the rule, and where the list lives."""
    return (f"{ticker.upper()} is a held audit pack — TeamNostra's blind CIQ test set, which no "
            "mosaic-theory code reads until its answer key is frozen (tests/held_names.py)")


def tickers_named(item: object) -> set[str]:
    """Every ticker an enumerated item can name: a ticker string; for a path — a page folder, its
    `dossier.json`, a served `frontend/dossiers/<T>.json`, a CIQ folder or a file inside one —
    each folder on it and its own stem; for a multi-argument case (a tuple, a `pytest.param`),
    every element's. Only the intersection with `HELD_NAMES` is ever used."""
    if isinstance(item, ParameterSet):
        return tickers_named(item.values)
    if isinstance(item, tuple | list):
        return set().union(*(tickers_named(part) for part in item))
    if isinstance(item, str) and "/" not in item:
        return {item.upper()}
    if isinstance(item, str | os.PathLike):
        p = Path(item)
        return {part.upper() for part in p.parent.parts} | {p.name.upper(), p.stem.upper()}
    return set()


def held_in(item: object) -> str | None:
    """The held ticker ``item`` names (the first, sorted, if several), else None."""
    held = sorted(tickers_named(item) & HELD_NAMES)
    return held[0] if held else None


def skip_if_held(item: object) -> None:
    """SKIP the running test when ``item`` names a held ticker — for a test that takes its one
    name from somewhere other than a parametrization."""
    t = held_in(item)
    if t is not None:
        pytest.skip(held_reason(t))


def page_params(items: Iterable[Any]) -> list[Any]:
    """A parametrization's values with every held name SKIPPED, the reason naming the rule. A
    non-held value is returned as it came, so its case id does not move; a held one becomes a
    `pytest.param` of the same values, so its id does not move either."""
    out: list[Any] = []
    for item in items:
        t = held_in(item)
        if t is None:
            out.append(item)
            continue
        mark = pytest.mark.skip(reason=held_reason(t))
        if isinstance(item, ParameterSet):
            out.append(pytest.param(*item.values, marks=(*item.marks, mark), id=item.id))
        elif isinstance(item, tuple):
            out.append(pytest.param(*item, marks=mark))
        else:
            out.append(pytest.param(item, marks=mark))
    return out


def without_held(items: Iterable[T]) -> list[T]:
    """A loop's items with every held name DROPPED, before the loop body can open its folder.
    Each drop is recorded for the terminal summary."""
    kept: list[T] = []
    for item in items:
        t = held_in(item)
        if t is None:
            kept.append(item)
            continue
        where = CURRENT_TEST[0]
        if where == "<collection>":
            caller = Path(sys._getframe(1).f_code.co_filename)  # noqa: SLF001 — the caller's module
            where = f"{caller.name} (at collection)"
        LEFT_OUT.append((where, t))
    return kept


# --- the backstop: no open of a held name's export, whatever path reached it --------------------

def ciq_roots(manual: Path = ROOT / "data" / "manual") -> tuple[tuple[str, ...], dict[str, str]]:
    """(roots, held folders) of the CIQ folder in this checkout, each path ending in a separator.
    The roots are `data/manual` as spelled and as resolved, the resolved `ciq` and `ciq-archive`
    in it (a checkout may link `data/manual`, or either of those), and the `ciq-archive` beside
    the resolved `ciq` (where `ciq_export_support.archive_roots` looks). The held folders
    map the resolved folder of each held name the live folder holds to its ticker: a ticker
    folder can itself be a link, whose target need not carry the ticker (Drive's GOOGL was one)."""
    roots = {str(manual)}
    for p in (manual, manual / "ciq", manual / "ciq-archive"):
        if p.exists():
            roots.add(os.path.realpath(p))
    if (manual / "ciq").exists():
        # the archive `ciq_export_support.archive_roots` also searches: beside the linked folder
        roots.add(os.path.join(os.path.dirname(os.path.realpath(manual / "ciq")), "ciq-archive"))
    held = {}
    for t in HELD_NAMES:
        folder = manual / "ciq" / t
        if folder.exists():
            held[os.path.realpath(folder).rstrip(os.sep) + os.sep] = t
    return tuple(sorted(r.rstrip(os.sep) + os.sep for r in roots)), held


#: Set once, when `tests/conftest.py` installs the hook.
CIQ_ROOTS: tuple[str, ...] = ()
HELD_FOLDERS: dict[str, str] = {}


def held_path(path: str, roots: tuple[str, ...], held_folders: dict[str, str]) -> str | None:
    """The held ticker whose folder ``path`` (absolute) lies in: under a held folder, or under one
    of ``roots`` with a held ticker among the folders between."""
    key = path.casefold()     # the checkout's disk may not tell case apart (APFS does not)
    for folder, t in held_folders.items():
        if key.startswith(folder.casefold()):
            return t
    for root in roots:
        if key.startswith(root.casefold()):
            folders = path[len(root):].split(os.sep)[:-1]
            held = sorted({f.upper() for f in folders} & HELD_NAMES)
            if held:
                return held[0]
    return None


def refuse_held_open(event: str, args: tuple[Any, ...]) -> None:
    """The audit hook: an `open` of a file in a held name's CIQ folder FAILS the running test
    before the file is read. Recorded too, so a test that swallows the failure still fails at its
    teardown (`tests/conftest.py`)."""
    if event != "open" or not args or isinstance(args[0], int) or not CIQ_ROOTS:
        return
    try:
        raw = os.fspath(args[0])
    except TypeError:
        return
    path = os.path.abspath(os.fsdecode(raw))
    t = held_path(path, CIQ_ROOTS, HELD_FOLDERS)
    if t is None and HELD_NAMES & {part.upper() for part in path.split(os.sep)[:-1]}:
        # a held-named folder reached through a link from outside the roots — a test's scratch
        # data folder whose `manual` links here (`test_maintenance_path`): judge where it leads.
        # Resolved only for such a path, so an ordinary open costs no extra system call.
        t = held_path(os.path.realpath(path), CIQ_ROOTS, HELD_FOLDERS)
    if t is None:
        return
    REFUSED_OPENS.append((CURRENT_TEST[0], path))
    pytest.fail(f"opened {path}: {held_reason(t)}. Route the test's loop through without_held() "
                "or its parametrization through page_params().", pytrace=False)
