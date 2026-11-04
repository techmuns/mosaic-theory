"""The shared which-export-is-on-disk checks (`tests/ciq_export_support.py`), pinned both ways.

Runs everywhere: the exports here are constructed files (only their bytes are hashed, never
parsed), and the page is SMPL's real committed one. The shape these pins encode is the one observed
on 2026-11-04 with the Drive folder linked: SMPL's page records Estimates export 06670995ba and the
folder held c50fddc012, its 2026-10-28 re-export.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.ciq_export_support import (
    ROOT,
    export_sha,
    skip_unless_export,
    skip_unless_pages_export,
)
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.ciq_sheets import file_provenance


def _page() -> dict[str, Any]:
    page: dict[str, Any] = json.loads(
        (ROOT / "data" / "dossiers" / "SMPL" / "dossier.json").read_text())
    return page


def _bundle_with_estimates(tmp_path: Path, content: bytes) -> tuple[CiqBundle, str]:
    path = tmp_path / "TheSimplyGoodFoodsCompanyNasdaqCMSMPLEstimatesReport.xls"
    path.write_bytes(content)
    sha = file_provenance(path)[0]
    assert sha is not None
    return CiqBundle.from_files("SMPL", [path]), sha


def test_the_identity_is_the_workbook_the_bundle_picks(tmp_path: Path) -> None:
    """The file hashed is the one `CiqBundle.workbook` serves, and a kind the folder lacks is
    None — never another kind's file."""
    bundle, sha = _bundle_with_estimates(tmp_path, b"one export")
    assert export_sha("SMPL", "estimates", bundle=bundle) == sha
    assert export_sha("SMPL", "comps", bundle=bundle) is None


def test_the_pages_own_export_runs(tmp_path: Path) -> None:
    """POSITIVE: the folder holds the export the page records, so nothing is skipped."""
    bundle, sha = _bundle_with_estimates(tmp_path, b"the page's export")
    page = _page()
    page["forward_consensus"]["source_sha256"] = sha
    skip_unless_pages_export("SMPL", "estimates", page=page, bundle=bundle)


def test_another_export_than_the_pages_skips_and_names_both(tmp_path: Path) -> None:
    """NEGATIVE, on the real committed page: an export the page does not record is skipped, and
    the reason names the page's sha256 and the one on disk."""
    bundle, sha = _bundle_with_estimates(tmp_path, b"a later re-export")
    want = _page()["forward_consensus"]["source_sha256"]
    assert want and want != sha
    with pytest.raises(pytest.skip.Exception) as got:
        skip_unless_pages_export("SMPL", "estimates", bundle=bundle)
    assert sha in str(got.value) and want in str(got.value)


def test_no_export_on_disk_leaves_the_test_as_it_was() -> None:
    """Without the folder nothing changes: a test that runs there keeps running."""
    skip_unless_pages_export("SMPL", "estimates", bundle=CiqBundle.from_files("SMPL", []))


def test_a_page_that_records_no_export_fails_loud(tmp_path: Path) -> None:
    """NEGATIVE: a page that cannot say which export it came from fails — a skip would hide that
    no comparison with it can be trusted."""
    bundle, _ = _bundle_with_estimates(tmp_path, b"any export")
    page = _page()
    page["forward_consensus"]["source_sha256"] = None
    with pytest.raises(pytest.fail.Exception, match="records no estimates export"):
        skip_unless_pages_export("SMPL", "estimates", page=page, bundle=bundle)


def test_a_frozen_pin_runs_only_on_its_own_export(tmp_path: Path) -> None:
    """POSITIVE and NEGATIVE for a value drawn from one export: its own export runs, another is
    skipped naming both, and an absent one is skipped saying so."""
    bundle, sha = _bundle_with_estimates(tmp_path, b"the pin's export")
    skip_unless_export("SMPL", "estimates", sha, why="w", bundle=bundle)
    with pytest.raises(pytest.skip.Exception) as got:
        skip_unless_export("SMPL", "estimates", "0000000000", why="w", bundle=bundle)
    assert sha in str(got.value) and "0000000000" in str(got.value)
    with pytest.raises(pytest.skip.Exception, match="absent"):
        skip_unless_export("SMPL", "estimates", sha, why="w",
                           bundle=CiqBundle.from_files("SMPL", []))
