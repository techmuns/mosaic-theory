"""The shared which-export-is-on-disk checks (`tests/ciq_export_support.py`), pinned both ways.

Runs everywhere: the exports here are constructed files (only their bytes are hashed, never
parsed), and the page is SMPL's real committed one. The shape these pins encode is the one observed
on 2026-11-04 with the Drive folder linked: SMPL's page records Estimates export 06670995ba and the
folder held c50fddc012, its 2026-10-28 re-export.

The floor (`OWN_EXPORT_FLOOR`) and the archive lookup answer the cross-review of #889: a skip is not
a pass, so when the page-keyed tests skip as a class something must fail, and a frozen pin whose
export sits in the operator's `ciq-archive/` must run there instead of skipping.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests import ciq_export_support as ces
from tests.ciq_export_support import (
    OWN_EXPORT_FLOOR,
    ROOT,
    export_sha,
    floor_breach,
    own_export_census,
    skip_unless_export,
    skip_unless_pages_export,
)
from tests.test_ev_gap_transform_idempotent import COMPUTED
from vinci.config import get_config
from vinci.dossier import manual_store as ms
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


def _must_not_skip(check: Any, *args: Any, **kwargs: Any) -> Any:
    """A POSITIVE pin on a skip helper must be able to FAIL: a wrongful skip raised inside the test
    body would otherwise report this test as SKIPPED, never red. Returns what the check returns."""
    try:
        return check(*args, **kwargs)
    except pytest.skip.Exception as exc:
        pytest.fail(f"skipped where it must run: {exc}")


def _store_at(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    """The configured CIQ folder is ``root`` — so no pin here reads, or searches beside, the
    machine's real folder."""
    monkeypatch.setattr(ms.LocalFolderStore, "from_config",
                        staticmethod(lambda _cfg=None: ms.LocalFolderStore(root)))


def _export(folder: Path, content: bytes, *, with_other: bool = False) -> tuple[Path, str]:
    """An Estimates export (and, with ``with_other``, a comps export beside it) in ``folder``."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "Netflix,IncNasdaqGSNFLXEstimatesReport.xls"
    path.write_bytes(content)
    if with_other:
        (folder / "Company Comparable Analysis Netflix Inc.xls").write_bytes(b"comps " + content)
    sha = file_provenance(path)[0]
    assert sha is not None
    return path, sha


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
    _must_not_skip(skip_unless_pages_export, "SMPL", "estimates", page=page, bundle=bundle)


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
    _must_not_skip(skip_unless_pages_export, "SMPL", "estimates",
                   bundle=CiqBundle.from_files("SMPL", []))


def test_the_folder_lookup_is_the_path_the_suite_uses(tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    """WITHOUT AN INJECTED BUNDLE — how the parity and EV-gap tests call it: the configured folder
    is read, an empty one is no export, and a held one is hashed by the file the bundle picks."""
    monkeypatch.setattr(ms.LocalFolderStore, "from_config",
                        staticmethod(lambda _cfg=None: ms.LocalFolderStore(tmp_path)))
    assert export_sha("SMPL", "estimates") is None
    (tmp_path / "SMPL").mkdir()
    _, sha = _bundle_with_estimates(tmp_path / "SMPL", b"a folder export")
    assert export_sha("SMPL", "estimates") == sha
    with pytest.raises(pytest.skip.Exception):
        skip_unless_pages_export("SMPL", "estimates")


def test_an_unreadable_export_fails_rather_than_reading_as_absent(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: an export on disk that cannot be hashed is not "no export" — read that way, the
    page comparison would run against an unidentified file and the pin skip would say "absent"."""
    bundle, _ = _bundle_with_estimates(tmp_path, b"unhashable")
    monkeypatch.setattr(ces, "file_provenance", lambda _p: (None, None))
    with pytest.raises(pytest.fail.Exception, match="could not be hashed"):
        skip_unless_pages_export("SMPL", "estimates", bundle=bundle)


def test_a_kind_no_page_stamps_is_refused_without_the_folder() -> None:
    """NEGATIVE: the kind is checked before the disk, so a misuse is refused on every machine."""
    with pytest.raises(KeyError, match="PAGE_STAMPS"):
        skip_unless_pages_export("SMPL", "comps", bundle=CiqBundle.from_files("SMPL", []))


def test_a_page_that_records_no_export_fails_loud(tmp_path: Path) -> None:
    """NEGATIVE: a page that cannot say which export it came from fails — a skip would hide that
    no comparison with it can be trusted."""
    bundle, _ = _bundle_with_estimates(tmp_path, b"any export")
    page = _page()
    page["forward_consensus"]["source_sha256"] = None
    with pytest.raises(pytest.fail.Exception, match="records no estimates export"):
        skip_unless_pages_export("SMPL", "estimates", page=page, bundle=bundle)


def test_a_frozen_pin_runs_only_on_its_own_export(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    """POSITIVE and NEGATIVE for a value verified on one export: its own export runs, another is
    skipped naming both, and an absent one is skipped saying so."""
    _store_at(monkeypatch, tmp_path / "ciq")
    bundle, sha = _bundle_with_estimates(tmp_path, b"the pin's export")
    got = _must_not_skip(skip_unless_export, "SMPL", "estimates", sha, why="w", bundle=bundle)
    assert got is bundle, "the folder holds the pin's export, so the pin runs on the folder's"
    with pytest.raises(pytest.skip.Exception) as got:
        skip_unless_export("SMPL", "estimates", "0000000000", why="w", bundle=bundle)
    assert sha in str(got.value) and "0000000000" in str(got.value)
    with pytest.raises(pytest.skip.Exception, match="absent"):
        skip_unless_export("SMPL", "estimates", sha, why="w",
                           bundle=CiqBundle.from_files("SMPL", []))


def test_a_frozen_pin_runs_on_the_archived_export_when_the_folder_holds_another(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """POSITIVE, the NFLX shape: the folder holds a later export, `ciq-archive/` holds the pin's.
    The pin runs on the archived folder — the whole folder, one pull. On main this SKIPPED."""
    _store_at(monkeypatch, tmp_path / "ciq")
    _export(tmp_path / "ciq" / "NFLX", b"the 2026-10-28 export")
    held, sha = _export(tmp_path / "ciq-archive" / "replaced-2026-10-28" / "NFLX",
                        b"the 2026-10-07 export", with_other=True)
    got = _must_not_skip(skip_unless_export, "NFLX", "estimates", sha, why="w")
    assert got.workbook("estimates").path == held
    assert got.workbook("comps") is not None, "the archived folder is read whole"


def test_the_archive_is_found_beside_the_folder_a_checkout_links_to(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """POSITIVE, the real topology: `data/manual/ciq` is a link to the Drive folder, and the
    archive sits beside the Drive folder, not beside the link."""
    drive = tmp_path / "drive" / "manual"
    _export(drive / "ciq" / "NFLX", b"the later export")
    held, sha = _export(drive / "ciq-archive" / "replaced-2026-10-28" / "NFLX", b"the pin's")
    link = tmp_path / "checkout" / "data" / "manual" / "ciq"
    link.parent.mkdir(parents=True)
    link.symlink_to(drive / "ciq")
    _store_at(monkeypatch, link)
    got = _must_not_skip(skip_unless_export, "NFLX", "estimates", sha, why="w")
    assert got.workbook("estimates").path == held


def test_a_frozen_pin_skips_when_neither_the_folder_nor_the_archive_holds_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE: an archive holding only other exports is no match — the pin skips, saying the
    archive was searched, and never runs on an export it was not verified on."""
    _store_at(monkeypatch, tmp_path / "ciq")
    _, live = _export(tmp_path / "ciq" / "NFLX", b"the later export")
    _export(tmp_path / "ciq-archive" / "replaced-2026-10-28" / "NFLX", b"another export")
    with pytest.raises(pytest.skip.Exception, match="no folder under ciq-archive/") as got:
        skip_unless_export("NFLX", "estimates", "0000000000", why="w")
    assert live in str(got.value)


def test_the_floor_holds_at_half_and_names_every_drifted_page_below_it() -> None:
    """POSITIVE and NEGATIVE for the floor itself: half the pages on their own export holds; one
    fewer fails naming every drifted page; no pages at all fails (nothing would run)."""
    assert OWN_EXPORT_FLOOR == 0.5
    assert floor_breach(["A", "B", "C", "D"], ["E", "F", "G", "H"]) is None
    msg = floor_breach(["A", "B", "C"], ["D", "E", "F", "G", "H"])
    assert msg is not None and "3 of 8" in msg
    assert all(t in msg for t in "DEFGH")
    assert floor_breach([], []) is not None


def test_the_census_reads_the_page_stamp_against_the_folder(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A page is OWN only when the folder's Estimates export is the one it stamps: a constructed
    export is drifted, a name with no folder is drifted, and the stamp itself is own."""
    _store_at(monkeypatch, tmp_path / "ciq")
    (tmp_path / "ciq" / "SMPL").mkdir(parents=True)
    _bundle_with_estimates(tmp_path / "ciq" / "SMPL", b"a re-export")
    assert own_export_census(["SMPL", "NCNO"]) == ([], ["SMPL", "NCNO"])
    stamp = _page()["forward_consensus"]["source_sha256"]
    monkeypatch.setattr(ces, "export_sha", lambda t, k, **_kw: stamp if t == "SMPL" else None)
    assert own_export_census(["SMPL", "NCNO"]) == (["SMPL"], ["NCNO"])


def test_most_computed_pages_hold_the_estimates_export_they_stamp() -> None:
    """THE FLOOR, on the live folder. Between a re-export and the artifact pass every page can
    drift at once; the page-keyed tests then skip as a class and a CIQ-reader mutation fails no
    behavioural test (cross-review of #889). This fails instead. Without the folder (CI) there is
    nothing to measure, and the skip says so. The folder checked is the one the census reads (the
    configured store), so a run from another directory skips rather than counting every page
    drifted against a folder it never looked in."""
    root = get_config().data_dir / "manual" / "ciq"
    if not root.is_dir() or not any(p.is_dir() for p in root.iterdir()):
        pytest.skip("no CIQ folder holding tickers on this machine — no export to measure")
    assert COMPUTED, "no committed page carries a computed ev_gap — the population is gone"
    breach = floor_breach(*own_export_census(COMPUTED))
    if breach:
        pytest.fail(breach)


def test_the_commit_gate_prints_every_skip_reason() -> None:
    """`bin/commit` adds `-q` to addopts' `-q`, which prints no skip reasons — so a class of
    skips passed the gate unread (cross-review of #889). Its pytest line carries `-rs`."""
    lines = [ln for ln in (ROOT / "bin" / "commit").read_text().splitlines()
             if "-m pytest" in ln and not ln.lstrip().startswith("#")]
    assert lines, "bin/commit no longer runs pytest"
    assert all("-rs" in ln.split() for ln in lines), lines


def test_an_ambiguous_archived_folder_does_not_stop_the_search(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """NEGATIVE then POSITIVE: an archived folder holding two Estimates exports is no pin's export
    (the code under test refuses it), so the search passes it by and runs the pin on the later
    archived folder that holds it — it neither raises nor skips."""
    _store_at(monkeypatch, tmp_path / "ciq")
    _export(tmp_path / "ciq" / "NFLX", b"the later export")
    twice = tmp_path / "ciq-archive" / "replaced-2026-10-20" / "NFLX"
    _export(twice, b"one export")
    (twice / "Netflix,IncNasdaqGSNFLXEstimatesReport (1).xls").write_bytes(b"another export")
    held, sha = _export(tmp_path / "ciq-archive" / "replaced-2026-10-28" / "NFLX", b"the pin's")
    got = _must_not_skip(skip_unless_export, "NFLX", "estimates", sha, why="w")
    assert got.workbook("estimates").path == held


def test_the_floor_looks_in_the_folder_the_census_reads(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run from a directory with no CIQ folder, the floor SKIPS — it never counts every page drifted
    against a folder it never looked in (it checked the checkout's folder while the census read the
    configured, cwd-relative one, and failed 0 of 8 run from /tmp)."""
    if get_config().data_dir.is_absolute():
        pytest.skip("the configured data_dir is absolute — no cwd to move")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(pytest.skip.Exception, match="no CIQ folder"):
        test_most_computed_pages_hold_the_estimates_export_they_stamp()
