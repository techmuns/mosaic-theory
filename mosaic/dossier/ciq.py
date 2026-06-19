"""CIQ parsing — file-check → format-branch, per ``docs/ciq_extraction_notes.md``.

The cardinal rule from the notes: **CIQ extensions mislead; verify the real format before parsing.**
We sniff header bytes (portable + testable) rather than trust the extension, then branch:
``.rtf`` real-RTF → ``striprtf``; OLE-disguised ``.rtf``/``.doc`` transcript → needs LibreOffice
(fail loud, never the ~12-word ``striprtf`` garbage); MIME-wrapped ``.doc`` → quoted-printable +
BeautifulSoup; legacy ``.xls`` BIFF → ``xlrd``; ``.xlsx`` → ``openpyxl``; ``.pdf`` → ``pdftotext``.

``xlrd``/``openpyxl``/``pandas`` are imported lazily inside their branch and fail loud with an
actionable message if absent (they're optional until real CIQ data lands). Every extractor fails
loud to UNKNOWN — a missing or unrecognised cell is never a fabricated number.
"""

from __future__ import annotations

import enum
import html as _html
import quopri
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_OLE_MAGIC = b"\xd0\xcf\x11\xe0"
_ZIP_MAGIC = b"PK\x03\x04"
_MIN_RTF_WORDS = 50  # below this from a multi-KB file ⇒ striprtf hit an OLE-disguised doc (garbage)


class CiqFormat(enum.StrEnum):
    """The REAL format behind a CIQ file (sniffed from bytes, not the extension)."""

    BIFF_XLS = "biff_xls"  # legacy Excel binary → xlrd
    OOXML = "ooxml"  # .xlsx/.docx zip → openpyxl
    RTF_TEXT = "rtf_text"  # real RTF → striprtf
    OLE_DISGUISED = "ole_disguised"  # .doc/.rtf that is really an OLE Word doc → needs LibreOffice
    MIME_DOC = "mime_doc"  # MIME-wrapped quoted-printable HTML filing → quopri + bs4
    HTML = "html"
    PDF = "pdf"
    UNKNOWN = "unknown"


class CiqParseError(RuntimeError):
    """A CIQ file could not be parsed in this environment (e.g. a needed library/tool is absent)."""


def classify(path: Path) -> CiqFormat:
    """Sniff the real format from header bytes (the notes' 'never trust the extension' rule)."""
    head = path.read_bytes()[:512]
    ext = path.suffix.lower()
    if head[:4] == _OLE_MAGIC:
        # OLE compound doc: a legacy .xls IS BIFF; an OLE-backed .rtf/.doc is a disguised Word doc.
        return CiqFormat.BIFF_XLS if ext == ".xls" else CiqFormat.OLE_DISGUISED
    if head[:4] == _ZIP_MAGIC:
        return CiqFormat.OOXML
    if head[:4] == b"%PDF":
        return CiqFormat.PDF
    stripped = head.lstrip()
    if stripped[:5] == b"{\\rtf":
        return CiqFormat.RTF_TEXT
    low = stripped[:200].lower()
    if low[:6] == b"<html>" or low[:9] == b"<!doctype" or low[:5] == b"<html":
        return CiqFormat.HTML
    if any(m in head[:200] for m in (b"MIME-Version", b"X-Sender", b"Content-Type", b"------=")):
        return CiqFormat.MIME_DOC
    return CiqFormat.UNKNOWN


def read_text(path: Path, fmt: CiqFormat | None = None) -> str:
    """Decode a text-bearing CIQ file to clean prose. Fail loud if a needed tool is absent."""
    fmt = fmt or classify(path)
    if fmt is CiqFormat.RTF_TEXT:
        from striprtf.striprtf import rtf_to_text

        raw_text = path.read_text(encoding="utf-8", errors="replace")
        text = rtf_to_text(raw_text)  # type: ignore[no-untyped-call]
        if path.stat().st_size > 4096 and len(text.split()) < _MIN_RTF_WORDS:
            raise CiqParseError(
                f"{path.name}: striprtf yielded {len(text.split())} words from a "
                f"{path.stat().st_size}B file — this is an OLE-disguised Word doc, not real RTF; "
                "pre-convert with LibreOffice/Word (see ciq_extraction_notes.md)"
            )
        return str(text)
    if fmt in (CiqFormat.MIME_DOC, CiqFormat.HTML):
        from bs4 import BeautifulSoup

        raw = path.read_bytes()
        if fmt is CiqFormat.MIME_DOC:
            # strip MIME headers (up to the blank line), then decode quoted-printable
            sep = b"\r\n\r\n" if b"\r\n\r\n" in raw else b"\n\n"
            raw = quopri.decodestring(raw.split(sep, 1)[-1])
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return _html.unescape(soup.get_text(" ", strip=True))
    if fmt is CiqFormat.PDF:
        import shutil
        import subprocess

        if not shutil.which("pdftotext"):
            raise CiqParseError(f"{path.name}: pdftotext not installed — cannot read PDF")
        out = subprocess.run(  # noqa: S603 — fixed args, path from the local manual store
            ["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True
        )
        return out.stdout
    if fmt is CiqFormat.OLE_DISGUISED:
        raise CiqParseError(
            f"{path.name}: OLE-disguised Word doc (transcript/annual) — needs LibreOffice/Word "
            "pre-conversion; no RTF library parses it (ciq_extraction_notes.md)"
        )
    raise CiqParseError(f"{path.name}: format {fmt.value} is not text — use read_sheets()")


def read_sheets(path: Path, fmt: CiqFormat | None = None) -> dict[str, list[list[Any]]]:
    """Read a CIQ spreadsheet into ``{sheet: rows}``. Lazy xlrd/openpyxl; fail loud if absent."""
    fmt = fmt or classify(path)
    if fmt is CiqFormat.BIFF_XLS:
        try:
            import xlrd  # type: ignore[import-untyped]
        except ImportError as exc:
            raise CiqParseError(
                f"{path.name}: legacy .xls needs `xlrd` (pip install xlrd) — not installed"
            ) from exc
        book = xlrd.open_workbook(str(path))
        return {s.name: [s.row_values(r) for r in range(s.nrows)] for s in book.sheets()}
    if fmt is CiqFormat.OOXML:
        try:
            import openpyxl  # type: ignore[import-untyped]
        except ImportError as exc:
            raise CiqParseError(
                f"{path.name}: .xlsx needs `openpyxl` (pip install openpyxl) — not installed"
            ) from exc
        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        return {
            ws.title: [list(row) for row in ws.iter_rows(values_only=True)] for ws in wb.worksheets
        }
    raise CiqParseError(f"{path.name}: format {fmt.value} is not a spreadsheet")


# --- bundle: index a name's CIQ files by module ----------------------------------------------

_MODULE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "financials": ("financial", "income", "balance", "cash flow", "cashflow"),
    "multiples": ("multiple",),
    "segments": ("segment",),
    "customers": ("customer", "supplier", "business relationship"),
    "estimates": ("estimate", "consensus", "revision"),
}


@dataclass(frozen=True)
class CiqFile:
    path: Path
    fmt: CiqFormat
    module: str | None  # best-effort module guess from the filename


@dataclass(frozen=True)
class CiqBundle:
    """A name's available CIQ files, classified by real format + best-effort module."""

    ticker: str
    files: tuple[CiqFile, ...]

    @classmethod
    def from_files(cls, ticker: str, paths: list[Path]) -> CiqBundle:
        out: list[CiqFile] = []
        for p in paths:
            name = p.name.lower()
            module = next(
                (m for m, kws in _MODULE_KEYWORDS.items() if any(k in name for k in kws)), None
            )
            try:
                fmt = classify(p)
            except OSError:
                fmt = CiqFormat.UNKNOWN
            out.append(CiqFile(path=p, fmt=fmt, module=module))
        return cls(ticker=ticker, files=tuple(out))

    def for_module(self, module: str) -> list[CiqFile]:
        return [f for f in self.files if f.module == module]

    @property
    def is_empty(self) -> bool:
        return not self.files
