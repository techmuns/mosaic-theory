"""Manual-data access — a swappable interface over the PM's licensed CIQ exports.

CIQ is depth-only (no programmatic feed), so its exports are read from a manual store. The interface
is swappable (a local folder now; a Google-Drive adapter later — not built yet). File **format** is
detected with ``file`` and never trusted from the extension (per ``ciq_extraction_notes.md``): the
Business Relationships export is real RTF → ``striprtf``; the OLE-disguised-``.doc`` variant needs
LibreOffice and fails loud if it isn't installed.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from striprtf.striprtf import rtf_to_text

_SOFFICE_CANDIDATES = (
    "soffice",
    "libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)


class CiqFormatError(RuntimeError):
    """A CIQ export whose actual format can't be parsed in this environment (fail loud)."""


def _file_type(path: Path) -> str:
    out = subprocess.run(["file", "-b", str(path)], capture_output=True, text=True, check=False)
    return out.stdout.strip().lower()


def _find_soffice() -> str | None:
    for cand in _SOFFICE_CANDIDATES:
        found = shutil.which(cand) if "/" not in cand else (cand if Path(cand).exists() else None)
        if found:
            return found
    return None


def extract_text(path: Path) -> str:
    """Format-detect (never trust the extension) and return plain text from a CIQ export."""
    ftype = _file_type(path)
    if "rich text" in ftype:  # real RTF (Business Relationships, Key Developments)
        text: str = rtf_to_text(path.read_text(errors="ignore"))  # type: ignore[no-untyped-call]
        return text
    if "composite document" in ftype or "msword" in ftype or "ole" in ftype:
        # OLE-disguised .doc (transcripts/some reports): striprtf returns garbage → LibreOffice
        soffice = _find_soffice()
        if soffice is None:
            raise CiqFormatError(
                f"{path.name}: OLE-disguised doc requires LibreOffice, which is not installed"
            )
        return _libreoffice_to_text(path, soffice)
    raise CiqFormatError(f"{path.name}: unrecognised CIQ format {ftype!r}")


def _libreoffice_to_text(path: Path, soffice: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "txt:Text", "--outdir", tmp, str(path)],
            capture_output=True, check=True,
        )
        out = Path(tmp) / (path.stem + ".txt")
        return out.read_text(errors="ignore") if out.exists() else ""


class ManualDataStore(ABC):
    """Yields the PM's manual documents as ``(relative_name, extracted_text)``."""

    @abstractmethod
    def iter_documents(self) -> Iterator[tuple[str, str]]: ...


class LocalFolderManualStore(ManualDataStore):
    """Local-folder adapter — recursively reads every (non-hidden) file under ``root``."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)

    def iter_documents(self) -> Iterator[tuple[str, str]]:
        for p in sorted(self._root.rglob("*")):
            if not p.is_file() or p.name.startswith("."):
                continue
            yield str(p.relative_to(self._root)), extract_text(p)
