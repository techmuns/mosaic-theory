"""WHICH EXPORT IS ON DISK — the one rule the CIQ-workbook tests share for it.

The licensed CIQ exports live in a git-ignored folder (`data/manual/ciq/`) that the operator
re-exports ahead of re-assembling a page. So a test that reads the folder can meet an export that
is NOT the one its expectation came from, and fail with nothing broken: on 2026-11-04, with the
Drive folder linked, eight tests failed on main `9e996d7f` because SMPL's and NCNO's exports were
2026-10-28's while their pages were built in August, and NFLX's carried a quarter its pin predates.

Two kinds of expectation, and each gets its own check:

* A COMPARISON WITH THE COMMITTED PAGE (the page's vintages against the export's) holds only on
  the export the page was built from — `skip_unless_pages_export`. It reads the sha256 the page
  itself records, the SAME stamp the refresh transforms check before they write from the folder
  (`ev_bridge_transform`, `historical_forecast_error_transform`, `ciq_currency_transform`), so a
  test and the code agree on what "the page's export" means. With no export of that kind on disk
  it does nothing: the test's own no-folder handling stands, so a machine without the folder runs
  exactly what it ran before.
* A VALUE PINNED FROM ONE EXPORT (a figure, a period label) holds only on that export, whatever
  the page has moved on to — `skip_unless_export`, keyed on the sha256 of an export the value is
  verified on (not always the one it was first written on: that may be gone). The TEST-LAYER
  rule: a value pin lives on a frozen fixture, never on the living export. The licensed bytes
  cannot be committed, so the fixture is frozen by IDENTITY instead. Before skipping it looks
  under the operator's `ciq-archive/`, where each replaced export is kept, and runs the pin there.

A SKIP, NEVER A LOOSER ASSERTION: every skip names both sha256s, so re-pinning is one deliberate
edit. AND A SKIP IS NOT A PASS: between a re-export and the artifact pass every page can drift at
once, and the page-keyed tests then skip as a class. `floor_breach` is the check that fails then
(cross-review of #889, 2026-11-04).

The identity is `ciq_sheets.file_provenance` — the first 10 hex digits of the file's sha256, the
form every page stamp takes — of the workbook `CiqBundle.workbook` picks, so the file hashed is the
file the code under test reads.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from tests.held_names import HELD_NAMES
from vinci.config import get_config
from vinci.dossier.ciq import CiqAmbiguousError, CiqBundle
from vinci.dossier.ciq_sheets import file_provenance
from vinci.dossier.manual_store import LocalFolderStore

ROOT = Path(__file__).resolve().parents[1]

#: Where a committed page records the export it was built from, per workbook kind: the top-level
#: block and the key holding the sha256 prefix. Only the kinds a test keys on today.
PAGE_STAMPS: dict[str, tuple[str, str]] = {
    "estimates": ("forward_consensus", "source_sha256"),
}


def export_sha(ticker: str, kind: str, *, freq: str | None = None,
               bundle: CiqBundle | None = None) -> str | None:
    """The sha256 prefix of the one ``kind`` export (of period type ``freq``) the folder holds for
    ``ticker`` — read through ``bundle`` when the test already built one — or None when it holds
    none. Several candidates raise (`CiqAmbiguousError`), as they do for the code under test."""
    if bundle is None:
        files = LocalFolderStore.from_config(get_config()).files(ticker)
        if not files:
            return None
        bundle = CiqBundle.from_files(ticker, files)
    wb = bundle.workbook(kind, freq=freq)
    if wb is None:
        return None
    sha = file_provenance(wb.path)[0]
    if sha is None:
        # AN UNREADABLE EXPORT IS NOT AN ABSENT ONE: read as None it would run a comparison
        # against an export nobody identified, or report "absent" for a file that is there
        pytest.fail(f"{ticker}: the {kind} export {wb.path.name} is on disk but could not be "
                    "hashed, so this test cannot tell which export it is")
    return sha


def page_export_sha(ticker: str, kind: str, *, page: dict[str, Any] | None = None) -> str:
    """The sha256 prefix the committed page records for its ``kind`` export. A page that records
    none FAILS the test: it cannot say which export it was built from, so no comparison with it
    can be told apart from a comparison with another export."""
    doc = page if page is not None else json.loads(
        (ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    block, key = PAGE_STAMPS[kind]
    sha = (doc.get(block) or {}).get(key)
    if not sha:
        pytest.fail(f"{ticker}: the committed page records no {kind} export ({block}.{key}), so "
                    "this test cannot tell whether the export on disk is the page's")
    return str(sha)


def skip_unless_pages_export(ticker: str, kind: str, *, page: dict[str, Any] | None = None,
                             bundle: CiqBundle | None = None) -> None:
    """SKIP when the folder holds a ``kind`` export for ``ticker`` that is not the one the committed
    page was built from. No such export on disk: nothing happens."""
    # THE KIND IS CHECKED FIRST, so a kind no page stamps is refused on every machine — not only
    # on the one holding the licensed folder, where it would otherwise surface alone
    if kind not in PAGE_STAMPS:
        raise KeyError(f"no page stamp is known for {kind!r} exports — add it to PAGE_STAMPS")
    disk = export_sha(ticker, kind, bundle=bundle)
    if disk is None:
        return
    want = page_export_sha(ticker, kind, page=page)
    if disk != want:
        pytest.skip(f"{ticker}: the {kind} export on disk ({disk}) is not the one the committed "
                    f"page was built from ({want}) — re-assemble the page on it, or link the "
                    "page's own export")


def archive_roots(ticker: str) -> list[Path]:
    """The operator's `ciq-archive/` folders: beside the CIQ folder the store reads, and beside
    the folder it links to (the Drive folder is linked into a checkout as `data/manual/ciq`). Each
    replaced export is kept there as `ciq-archive/replaced-<date>/<TICKER>/` (on the afternoon of
    2026-11-04 it held five dated folders; the exports SMPL's, NCNO's and NFLX's pins are
    verified on sit under `replaced-2026-10-28/`)."""
    root = Path(LocalFolderStore.from_config(get_config()).location(ticker)).parent
    out: list[Path] = []
    for cand in (root.parent / "ciq-archive", root.resolve().parent / "ciq-archive"):
        if cand.is_dir() and all(cand.resolve() != seen.resolve() for seen in out):
            out.append(cand)
    return out


def archived_folders(root: Path, ticker: str) -> list[Path]:
    """Every folder named ``ticker`` below ``root`` — the walk `root.rglob(ticker)` makes, symlinked
    folders matched but never descended into — that never LISTS a held name's folder
    (tests/held_names.py). `rglob` lists every folder it passes, so a search for SMPL's archived
    export read the names in an archived BURL folder (measured 2026-11-05 on a fake one: two tests,
    four listings, no file opened)."""
    want = ticker.upper()
    out: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d.upper() not in HELD_NAMES)
        out += [Path(dirpath) / d for d in dirnames if d == want]
    return sorted(out)


def archived_bundle(ticker: str, kind: str, sha: str, *,
                    freq: str | None = None) -> CiqBundle | None:
    """The bundle of the one archived folder for ``ticker`` whose ``kind`` export has sha256
    prefix ``sha``, or None. The WHOLE folder is the bundle — one pull, never one archived
    workbook spliced into the live folder's other exports."""
    for root in archive_roots(ticker):
        for folder in archived_folders(root, ticker):
            files = sorted(p for p in folder.iterdir()
                           if p.is_file() and not p.name.startswith("."))
            try:
                bundle = CiqBundle.from_files(ticker, files)
                held = export_sha(ticker, kind, freq=freq, bundle=bundle) if files else None
            except CiqAmbiguousError:
                # a folder of several exports of one kind is no pin's export — `from_files`
                # refuses it for the code under test too — and must not stop the search of the
                # other archived folders
                continue
            if held == sha:
                return bundle
    return None


def skip_unless_export(ticker: str, kind: str, sha: str, *, why: str, freq: str | None = None,
                       bundle: CiqBundle | None = None) -> CiqBundle:
    """The bundle to run a pin on whose value is verified on the ``kind`` export with sha256
    prefix ``sha``: the folder's own (``bundle`` when the test built it) when that export is
    there, else the archived folder holding it (`archived_bundle`). SKIP when neither holds it.
    RUN THE PIN ON THE BUNDLE THIS RETURNS — the live one may be another export.
    ``why`` says what the pin depends on."""
    if bundle is None:
        files = LocalFolderStore.from_config(get_config()).files(ticker)
        bundle = CiqBundle.from_files(ticker, files) if files else None
    disk = None if bundle is None else export_sha(ticker, kind, freq=freq, bundle=bundle)
    if bundle is not None and disk == sha:
        return bundle
    archived = archived_bundle(ticker, kind, sha, freq=freq)
    if archived is not None:
        return archived
    pytest.skip(f"{ticker}: {why} — this pin is verified on the {kind} export {sha}; the one on "
                f"disk is {disk or 'absent'}, and no folder under ciq-archive/ holds it")


#: The share of the computed pages that must hold the Estimates export they stamp, wherever the
#: CIQ folder holds tickers. Below it the page-keyed tests skip as a CLASS, so a CIQ-reader
#: regression fails nothing behavioural (cross-review of #889, 2026-11-04). Half, as proposed
#: there: the folder linked 2026-11-04 held 6 of 8 (NCNO and SMPL re-exported ahead of their
#: re-assembly). The house precedent is `test_ev_bridge`'s `compared >= 20`.
OWN_EXPORT_FLOOR = 0.5


def own_export_census(tickers: list[str]) -> tuple[list[str], list[str]]:
    """(own, drifted) among ``tickers``: own when the folder's Estimates export is the one the
    committed page stamps, drifted otherwise — another export, none on disk, or no stamp."""
    own: list[str] = []
    drifted: list[str] = []
    for t in tickers:
        doc = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
        block, key = PAGE_STAMPS["estimates"]
        stamp = (doc.get(block) or {}).get(key)
        held = export_sha(t, "estimates")
        (own if stamp and held == stamp else drifted).append(t)
    return own, drifted


def floor_breach(own: list[str], drifted: list[str]) -> str | None:
    """None while at least `OWN_EXPORT_FLOOR` of the pages hold their own export; else the
    failure, naming every drifted page. An empty population is a breach: nothing would run."""
    total = len(own) + len(drifted)
    if total and len(own) >= OWN_EXPORT_FLOOR * total:
        return None
    return (f"only {len(own)} of {total} computed pages hold the Estimates export they stamp, "
            f"below the floor of {OWN_EXPORT_FLOOR:.0%}: the page-keyed CIQ tests skip as a class, "
            f"so a CIQ-reader regression would pass. Drifted: {', '.join(drifted) or '—'}. "
            "Run the artifact pass on the re-exported names, or link the pages' own exports.")
