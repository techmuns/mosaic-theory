"""Swappable store for the **manual** CIQ exports — the one human step the funnel can't automate.

CIQ is licensed: exports are pulled by hand into ``data/manual/ciq/<ticker>/`` (git-ignored) and
NEVER auto-fetched. This module only *reads* what the human placed there.
:class:`LocalFolderStore` is the live adapter; :class:`DriveStore` is an unimplemented interface so
the swap point exists without a second code path built before it's earned (STATE.md §4).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from vinci.config import Config, get_config

_DEFERRED = "DriveStore is a deferred interface — use LocalFolderStore (STATE.md §4)"


class ManualDataStore(ABC):
    """Read-only access to a name's manually-exported CIQ files. Never fetches; never writes."""

    @abstractmethod
    def available(self, ticker: str) -> bool:
        """True iff the human has placed at least one CIQ file for ``ticker``."""

    @abstractmethod
    def files(self, ticker: str) -> list[Path]:
        """The CIQ files for ``ticker`` (empty if none — caller flags MISSING, never fabricates)."""

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


class DriveStore(ManualDataStore):
    """Unimplemented Google-Drive adapter — the swap point, deferred (STATE.md §4).

    Building it now would be a premature second data path. It exists so the interface is honoured;
    every method fails loud rather than silently degrading to a partial implementation.
    """

    def available(self, ticker: str) -> bool:
        raise NotImplementedError(_DEFERRED)

    def files(self, ticker: str) -> list[Path]:
        raise NotImplementedError(_DEFERRED)

    def location(self, ticker: str) -> str:
        raise NotImplementedError(_DEFERRED)
