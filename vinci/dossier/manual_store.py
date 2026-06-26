"""Swappable store for the **manual** CIQ exports — the one human step the funnel can't automate.

CIQ is licensed: exports are pulled by hand into a per-ticker folder and NEVER auto-fetched, never
committed. This module only *reads* what the human placed there.
:class:`LocalFolderStore` reads a local disk folder (the default); :class:`DriveStore` reads a
private Google Drive folder, downloading to an ephemeral temp dir. Both implement the same
:class:`ManualDataStore` interface, so the assembler is agnostic — the store is selected by the
``CIQ_STORE`` env var (see :func:`make_manual_store`). Design: docs/CLOUD_DOSSIER_TRIGGER.md §5a.
"""

from __future__ import annotations

import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol

from vinci.config import Config, get_config


class ManualDataStore(ABC):
    """Read-only access to a name's manually-exported CIQ files. Never fetches the data itself
    (the human exports it); never writes back to the source."""

    @abstractmethod
    def available(self, ticker: str) -> bool:
        """True iff the human has placed at least one CIQ file for ``ticker``."""

    @abstractmethod
    def files(self, ticker: str) -> list[Path]:
        """LOCAL file paths for ``ticker`` (empty if none — caller flags MISSING, never fabricates).

        A remote store downloads to a local temp dir and returns those paths: the CIQ readers
        (``xlrd``, the LibreOffice subprocess) consume local file paths, not remote handles.
        """

    @abstractmethod
    def location(self, ticker: str) -> str:
        """A human-readable pointer to where the files should live (for the 'pull CIQ' flag)."""


class LocalFolderStore(ManualDataStore):
    """Reads ``<root>/<ticker>/`` on the local disk. The root is git-ignored licensed CIQ data."""

    def __init__(self, root: Path) -> None:
        self._root = root

    @classmethod
    def from_config(cls, config: Config | None = None) -> LocalFolderStore:
        cfg = config or get_config()
        return cls(cfg.data_dir / "manual" / "ciq")

    def _folder(self, ticker: str) -> Path:
        return self._root / ticker.upper()

    def available(self, ticker: str) -> bool:
        folder = self._folder(ticker)
        return folder.is_dir() and any(p.is_file() for p in folder.iterdir())

    def files(self, ticker: str) -> list[Path]:
        folder = self._folder(ticker)
        if not folder.is_dir():
            return []
        return sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))

    def location(self, ticker: str) -> str:
        return str(self._folder(ticker))


class DriveApi(Protocol):
    """The minimal Google-Drive operations :class:`DriveStore` needs — a seam so the store is unit-
    testable without the Google SDK or live credentials (tests inject a fake)."""

    def subfolder_id(self, parent_id: str, name: str) -> str | None:
        """The id of the ``name`` subfolder directly under ``parent_id``, or None if absent."""

    def list_files(self, folder_id: str) -> list[tuple[str, str]]:
        """``[(file_id, filename), ...]`` for the non-folder files directly in ``folder_id``."""

    def download(self, file_id: str, dest: Path) -> None:
        """Download ``file_id`` to the local path ``dest``."""


class DriveStore(ManualDataStore):
    """Reads a name's CIQ files from a private Google Drive folder, downloading to a temp dir.

    Layout mirrors :class:`LocalFolderStore`: a parent folder holds one subfolder per ``TICKER``,
    each with that name's CIQ exports. ``files()`` downloads them to an EPHEMERAL temp dir — NEVER
    the repo working tree, so ``git add`` can't sweep licensed data — and returns local paths. Raw
    CIQ is never committed. The Drive ops go through the injectable :class:`DriveApi` seam.
    """

    def __init__(self, parent_folder_id: str, api: DriveApi, tmp_root: Path) -> None:
        self._parent = parent_folder_id
        self._api = api
        self._tmp_root = tmp_root

    @classmethod
    def from_config(cls, config: Config | None = None) -> DriveStore:
        """Build from env (fail-loud): ``CIQ_DRIVE_FOLDER_ID`` (the parent folder id) +
        ``GOOGLE_APPLICATION_CREDENTIALS`` (path to the read-only service-account JSON). The Google
        SDK is an optional extra — ``pip install '.[drive]'``."""
        folder_id = os.environ.get("CIQ_DRIVE_FOLDER_ID")
        if not folder_id:
            raise RuntimeError(
                "CIQ_STORE=drive requires CIQ_DRIVE_FOLDER_ID (the parent Google Drive folder id)."
            )
        creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds:
            raise RuntimeError(
                "CIQ_STORE=drive requires GOOGLE_APPLICATION_CREDENTIALS "
                "(path to the read-only service-account JSON key)."
            )
        tmp_root = Path(tempfile.mkdtemp(prefix="vinci-ciq-"))
        return cls(folder_id, _GoogleDriveApi(creds), tmp_root)

    def _folder_id(self, ticker: str) -> str | None:
        return self._api.subfolder_id(self._parent, ticker.upper())

    def available(self, ticker: str) -> bool:
        fid = self._folder_id(ticker)
        return fid is not None and len(self._api.list_files(fid)) > 0

    def files(self, ticker: str) -> list[Path]:
        fid = self._folder_id(ticker)
        if fid is None:
            return []
        dest_dir = self._tmp_root / ticker.upper()
        dest_dir.mkdir(parents=True, exist_ok=True)
        out: list[Path] = []
        for file_id, name in self._api.list_files(fid):
            if name.startswith("."):
                continue
            dest = dest_dir / name
            self._api.download(file_id, dest)
            out.append(dest)
        return sorted(out)

    def location(self, ticker: str) -> str:
        return f"Google Drive: folder '{ticker.upper()}' under parent id {self._parent}"


class _GoogleDriveApi:
    """Live read-only Google Drive adapter. Lazily imports the Google SDK so the core install + mypy
    need it ONLY when the Drive store is used (the optional ``.[drive]`` extra). Structurally
    satisfies :class:`DriveApi`. Thin glue — run by the operator's live pull, not the unit tests."""

    _SCOPES = ("https://www.googleapis.com/auth/drive.readonly",)
    _FOLDER_MIME = "application/vnd.google-apps.folder"

    def __init__(self, credentials_path: str) -> None:
        from google.oauth2 import service_account  # optional dep — lazy import
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=list(self._SCOPES)
        )
        self._svc: Any = build("drive", "v3", credentials=creds, cache_discovery=False)

    def subfolder_id(self, parent_id: str, name: str) -> str | None:
        safe = name.replace("'", "").replace("\\", "")  # name is an uppercased ticker
        q = (
            f"'{parent_id}' in parents and name = '{safe}' "
            f"and mimeType = '{self._FOLDER_MIME}' and trashed = false"
        )
        resp = self._svc.files().list(q=q, fields="files(id)", pageSize=1).execute()
        files = resp.get("files", [])
        return str(files[0]["id"]) if files else None

    def list_files(self, folder_id: str) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        page_token: str | None = None
        while True:
            resp = (
                self._svc.files()
                .list(
                    q=f"'{folder_id}' in parents and mimeType != '{self._FOLDER_MIME}' "
                    f"and trashed = false",
                    fields="nextPageToken, files(id, name)",
                    pageSize=100,
                    pageToken=page_token,
                )
                .execute()
            )
            for f in resp.get("files", []):
                out.append((str(f["id"]), str(f["name"])))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return out

    def download(self, file_id: str, dest: Path) -> None:
        from googleapiclient.http import MediaIoBaseDownload  # optional dep — lazy import

        request = self._svc.files().get_media(fileId=file_id)
        with open(dest, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()


def make_manual_store(config: Config | None = None) -> ManualDataStore:
    """Select the CIQ store from the ``CIQ_STORE`` env var.

    ``local`` (default) → :class:`LocalFolderStore` (unchanged behavior for existing local runs).
    ``drive`` → :class:`DriveStore` (Google Drive; needs ``CIQ_DRIVE_FOLDER_ID`` +
    ``GOOGLE_APPLICATION_CREDENTIALS`` + the ``.[drive]`` extra). Fail-loud on an unknown value.
    """
    cfg = config or get_config()
    kind = os.environ.get("CIQ_STORE", "local").strip().lower()
    if kind == "local":
        return LocalFolderStore.from_config(cfg)
    if kind == "drive":
        return DriveStore.from_config(cfg)
    raise RuntimeError(f"Unknown CIQ_STORE={kind!r}; expected 'local' or 'drive'.")
