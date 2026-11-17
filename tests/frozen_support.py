"""Test support: where a test reads a page when it must not name a LIVING one (W27 follow-up,
STATE row 41 (a); CLAUDE.md TEST-LAYER RULE).

A test that reads `data/dossiers/<T>/…` by name breaks when <T> leaves coverage. A value it pins
also rots the next time that page is re-assembled. Two ways out, by what the test states:

- **A frozen copy** serves a VALUE pin (a figure, a date or a phrase read off a page), or a test
  about something only that page has (its exhibit, its tag, its refusal shape). Such a test is a
  value pin in substance (A's ruling, 2026-11-17). Read the page through `frozen_page(T)` (its
  folder) or `frozen_doc(T)` (its parsed `dossier.json`). Every pin on a page shares its one copy.
- **A roster walk** serves an INVARIANT that every page with some property must meet. It walks all
  of them, `covered_where(…)`, and fails loud when none has the property, since a check that finds
  nothing is suspect. It never skips. `covered_pages()` gives every page.

THE CUT. `tests/fixtures/frozen_pages/cut-<sha8>/<T>/` holds every committed page's `dossier.json`
and `dossier.md` at main <sha>, byte for byte: the same git blobs, and so 0 new objects in the
repository. `tests/test_frozen_pages_are_cuts.py` holds each copy to the commit its folder names,
and the cut's own README to the copies. A cut is never regenerated or edited. When a page moves on
main and a pin on it is re-pinned to the new state, the page gets a NEW cut. The old copy stays.

Which pins read a copy is derived, never listed (`grep 'frozen_doc("T")'`), so no list rots.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from vinci import coverage_roster as roster

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FROZEN_PAGES = ROOT / "tests" / "fixtures" / "frozen_pages"

#: The commit the cut was taken at: main after #1092 (the coverage roster), 2026-11-17.
CUT_SHA = "4889ddba632f34b0479fdb4e6e6e1b32c095cb10"
CUT = FROZEN_PAGES / f"cut-{CUT_SHA[:8]}"


def frozen_page(ticker: str) -> Path:
    """The folder of ``ticker``'s frozen copy in the cut. It raises when there is none, never
    falling back to the living page."""
    folder = CUT / ticker
    if not (folder / "dossier.json").is_file():
        raise FileNotFoundError(
            f"no frozen copy of {ticker} in {CUT.relative_to(ROOT)} — a page enters a cut only "
            f"as committed at that cut's commit (tests/fixtures/frozen_pages/README.md)")
    return folder


def frozen_doc(ticker: str) -> dict[str, Any]:
    """``ticker``'s frozen ``dossier.json``, parsed: a fresh object on every call."""
    doc: dict[str, Any] = json.loads((frozen_page(ticker) / "dossier.json").read_text())
    return doc


def covered_pages(data_dir: Path = DATA) -> list[str]:
    """The roster's covered names, sorted. It raises when the committed pages disagree with the
    roster (`vinci.coverage_roster.covered_pages`)."""
    return roster.covered_pages(data_dir)


def roster_names(status: str, data_dir: Path = DATA) -> list[str]:
    """The names whose latest roster move is ``status``, sorted, with at least one."""
    if status not in roster.STATUSES:
        raise ValueError(f"{status!r} is not a roster status {roster.STATUSES}")
    names = sorted(t for t, m in roster.current(data_dir).items() if m.status == status)
    assert names, f"no {status} name on the coverage roster — a pin that needs one is vacuous"
    return names


def living_doc(ticker: str, data_dir: Path = DATA) -> dict[str, Any]:
    """A covered name's LIVING page, parsed. Use it only on a name a roster walk handed back."""
    doc: dict[str, Any] = json.loads(
        (data_dir / "dossiers" / ticker / "dossier.json").read_text())
    return doc


def covered_where(has: Callable[[str, dict[str, Any]], bool], what: str,
                  data_dir: Path = DATA) -> list[tuple[str, dict[str, Any]]]:
    """Every covered page (ticker, parsed living page) for which ``has`` holds, sorted by
    ticker. It fails loud when there is none: ``what`` names the property, as in "no covered page
    {what}". Never a skip, because an invariant that walks nothing proves nothing."""
    out = [(t, d) for t in covered_pages(data_dir) if has(t, d := living_doc(t, data_dir))]
    assert out, (f"no covered page {what} — the invariant walks nothing; if the last page with "
                 f"it left, pin the shape on a frozen copy (tests/frozen_support.py)")
    return out
