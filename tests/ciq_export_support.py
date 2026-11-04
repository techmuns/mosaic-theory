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
  the page has moved on to — `skip_unless_export`, keyed on the sha256 of the export the value was
  drawn from. The TEST-LAYER rule: a value pin lives on a frozen fixture, never on the living
  export. The licensed bytes cannot be committed, so the fixture is frozen by IDENTITY instead.

A SKIP, NEVER A LOOSER ASSERTION: every skip names both sha256s, so re-pinning is one deliberate
edit. The identity is `ciq_sheets.file_provenance` — the first 10 hex digits of the file's sha256,
the form every page stamp takes — of the workbook `CiqBundle.workbook` picks, so the file hashed is
the file the code under test reads.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.config import get_config
from vinci.dossier.ciq import CiqBundle
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
    return None if wb is None else file_provenance(wb.path)[0]


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
    disk = export_sha(ticker, kind, bundle=bundle)
    if disk is None:
        return
    want = page_export_sha(ticker, kind, page=page)
    if disk != want:
        pytest.skip(f"{ticker}: the {kind} export on disk ({disk}) is not the one the committed "
                    f"page was built from ({want}) — re-assemble the page on it, or link the "
                    "page's own export")


def skip_unless_export(ticker: str, kind: str, sha: str, *, why: str, freq: str | None = None,
                       bundle: CiqBundle | None = None) -> None:
    """SKIP unless the folder's ``kind`` export for ``ticker`` is the one with sha256 prefix
    ``sha`` — the export a pinned value was drawn from. ``why`` says what the pin depends on."""
    disk = export_sha(ticker, kind, freq=freq, bundle=bundle)
    if disk != sha:
        pytest.skip(f"{ticker}: {why} — this pin was drawn from the {kind} export {sha}, and the "
                    f"one on disk is {disk or 'absent'}")
