"""DriveStore (Google Drive CIQ adapter) + the CIQ_STORE selector. Offline: a fake DriveApi seam
stands in for the Google SDK, so these run without creds or the '.[drive]' extra."""
from __future__ import annotations

from pathlib import Path

import pytest

from vinci.dossier.manual_store import DriveStore, LocalFolderStore, make_manual_store


class _FakeDriveApi:
    """In-memory DriveApi: tree = {TICKER: {filename: bytes}}."""

    def __init__(self, tree: dict[str, dict[str, bytes]]) -> None:
        self._tree = tree

    def subfolder_id(self, parent_id: str, name: str) -> str | None:
        return f"{parent_id}:{name}" if name in self._tree else None

    def list_files(self, folder_id: str) -> list[tuple[str, str]]:
        ticker = folder_id.split(":", 1)[1]
        return [(f"{ticker}/{fn}", fn) for fn in self._tree[ticker]]

    def download(self, file_id: str, dest: Path) -> None:
        ticker, fn = file_id.split("/", 1)
        dest.write_bytes(self._tree[ticker][fn])


def test_drivestore_available(tmp_path: Path) -> None:
    api = _FakeDriveApi({"VRRM": {"financials.xls": b"abc"}})
    store = DriveStore("PARENT", api, tmp_path)
    assert store.available("vrrm") is True  # case-insensitive
    assert store.available("ZZZZ") is False


def test_drivestore_files_download_to_temp(tmp_path: Path) -> None:
    api = _FakeDriveApi({"VRRM": {"financials.xls": b"abc", ".hidden": b"x"}})
    store = DriveStore("PARENT", api, tmp_path)
    paths = store.files("vrrm")
    assert [p.name for p in paths] == ["financials.xls"]  # dotfiles skipped
    assert paths[0].read_bytes() == b"abc"
    assert tmp_path in paths[0].parents  # downloaded to the temp root, never the repo tree


def test_drivestore_missing_folder_is_empty(tmp_path: Path) -> None:
    store = DriveStore("PARENT", _FakeDriveApi({}), tmp_path)
    assert store.available("AAPL") is False
    assert store.files("AAPL") == []


def test_drivestore_location_mentions_ticker(tmp_path: Path) -> None:
    store = DriveStore("PARENT", _FakeDriveApi({}), tmp_path)
    assert "VRRM" in store.location("vrrm")


def test_make_manual_store_defaults_to_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CIQ_STORE", raising=False)
    assert isinstance(make_manual_store(), LocalFolderStore)


def test_make_manual_store_drive_requires_folder_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIQ_STORE", "drive")
    monkeypatch.delenv("CIQ_DRIVE_FOLDER_ID", raising=False)
    with pytest.raises(RuntimeError, match="CIQ_DRIVE_FOLDER_ID"):
        make_manual_store()


def test_make_manual_store_unknown_kind_fails_loud(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIQ_STORE", "ftp")
    with pytest.raises(RuntimeError, match="Unknown CIQ_STORE"):
        make_manual_store()
