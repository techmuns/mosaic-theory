"""Manual documents — read a PDF / HTML / Markdown / text file into the SAME `ParsedDocument` the
web pipeline produces, so an uploaded report goes through every check an automatically
retrieved article does.

What is preserved: the text in reading order with a PAGE reference on every block, tables as
their own blocks (cells kept, numbers as written), footnotes, headings; the document's own
title, authors and publication date WITH the place each was read from.

What is flagged, never silently dropped: a page with no text layer (a scanned image — OCR is not
available here), a page whose graphics carry values the text does not (charts: their labels are
read, their plotted values are not), a table the extractor could not structure (its text is kept
as paragraphs). Any such gap makes the document PARTIAL.

What is NEVER used as a publication date: the upload time, the file name, or the PDF's file
metadata (CreationDate / ModDate say when the FILE was made). The date comes from the document's
own text (the first dated line of page 1-2) or, failing that, the operator's statement — said so.
An HTML file goes through the web parser, with two additions for a manual copy: each <table> is
kept as ONE table block, and a page whose metadata states no date takes the date its own opening
text states. A "By …" byline in the opening lines is read as the authors, in every format.
DOCX is not supported: no compatible library is installed (save the report as PDF).
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from vinci.theme_intelligence.discovery import date_in_text
from vinci.theme_intelligence.parse import ParsedDocument, parse_document
from vinci.theme_intelligence.schemas import Author, Block, FieldStatus, RetrievalState

SUPPORTED = {".pdf": "pdf", ".html": "html", ".htm": "html", ".md": "markdown",
             ".markdown": "markdown", ".txt": "text"}
#: a page whose text layer carries fewer words than this, but which holds images, is treated as
#: scanned (no text layer)
SCANNED_MAX_WORDS = 15
#: vector objects (curves / rects) on one page above which it is said to carry a chart
CHART_MIN_OBJECTS = 40
_GENERIC_TITLE = re.compile(r"^(untitled|microsoft (word|powerpoint)|document\d*|slide \d+)\b|"
                            r"\.(docx?|pdf|pptx?|html?|txt|md)$", re.I)


class DocumentError(ValueError):
    """The file cannot be read as a research document (format, encryption, emptiness)."""


@dataclass(frozen=True)
class Declared:
    """What the OPERATOR states about a document — kept apart from what the document says."""

    source_id: str
    url: str | None = None
    title: str | None = None
    authors: tuple[str, ...] = ()
    published: date | None = None
    #: may this document's text be sent to the third-party LLM under its licence? None = not
    #: stated → the document is HELD for review, never processed on an assumption
    llm_permitted: bool | None = None


@dataclass
class DocumentRead:
    path: Path
    sha256: str  # of the FILE bytes — the same file under another name is the same document
    fmt: str
    size: int
    doc: ParsedDocument
    pages: int | None = None
    tables: int = 0
    issues: list[str] = field(default_factory=list)  # what could not be read, said plainly
    meta: dict[str, str] = field(default_factory=dict)  # the file's own metadata, as found
    #: the operator-stated publication date disagreed with the one the document states
    date_disagreement: str | None = None


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _block(blocks: list[Block], kind: str, text: str, page: int | None,
           section: str | None) -> None:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return
    blocks.append(Block(block_id=f"b{len(blocks) + 1:03d}", kind=kind, text=text,
                        sha256=hashlib.sha256(text.encode()).hexdigest(), section=section,
                        order=len(blocks) + 1, page=page))


def _date_from(texts: list[str]) -> date | None:
    for t in texts:
        d = date_in_text(t)
        if d is not None:
            return d
    return None


_BYLINE = re.compile(r"^(?:by|written by|authors?:)\s+(.{3,200})$", re.I)


def _byline(texts: list[str]) -> list[Author]:
    """Authors from a byline in the document's own opening lines ("By A and B")."""
    for t in texts:
        m = _BYLINE.match(t.strip())
        if m and len(m.group(1).split()) <= 20:
            return [Author(name=n.strip(), source_field="a byline in the document text")
                    for n in re.split(r",|;| and | & ", m.group(1)) if n.strip()]
    return []


def _finish(read: DocumentRead, *, blocks: list[Block], title: str | None, title_src: str | None,
            authors: list[Author], doc_date: date | None, date_src: str | None,
            declared: Declared, canonical: str, partial: bool) -> DocumentRead:
    """Assemble the ParsedDocument: the document's own metadata first, the operator's statement
    only where the document is silent — every value says where it was read."""
    notes = list(read.issues)
    names = {a.name.lower() for a in authors}
    authors = authors + [a for a in _byline([b.text for b in blocks[:10]])
                         if a.name.lower() not in names]
    if declared.title and not title:
        title, title_src = declared.title, "operator-stated"
    if declared.authors:
        names = {a.name.lower() for a in authors}
        authors += [Author(name=n, source_field="operator-stated") for n in declared.authors
                    if n.lower() not in names]
    pub_src = date_src
    if doc_date is not None and declared.published and declared.published != doc_date:
        read.date_disagreement = (f"the operator states {declared.published.isoformat()} but the "
                                  f"document states {doc_date.isoformat()} ({date_src}) — the "
                                  f"document's own date is used")
        notes.append(read.date_disagreement)
    if doc_date is None and declared.published is not None:
        doc_date, pub_src = declared.published, "operator-stated (the document states no date)"
    published = (datetime(doc_date.year, doc_date.month, doc_date.day, tzinfo=UTC)
                 if doc_date else None)
    if partial:
        notes.append("PARTIAL: part of this document could not be read — see the issues")
    body_words = sum(len(b.text.split()) for b in blocks)
    state = (RetrievalState.BLOCKED if body_words < 40 else
             RetrievalState.PARTIAL if partial else RetrievalState.FULL)
    read.doc = ParsedDocument(
        canonical_url=canonical, title=title, title_source=title_src, authors=tuple(authors),
        authors_status=FieldStatus.KNOWN if authors else FieldStatus.UNKNOWN,
        published_at=published, published_raw=doc_date.isoformat() if doc_date else None,
        published_source=pub_src,
        published_status=FieldStatus.KNOWN if published else FieldStatus.UNKNOWN,
        modified_at=None, modified_source=None, blocks=tuple(blocks), retrieval_state=state,
        notes=notes)
    return read


# --- PDF -----------------------------------------------------------------------------------------

def _pdf_date(raw: str | None) -> str | None:
    """A PDF metadata date (D:YYYYMMDD…) for the record — NEVER a publication date."""
    if not raw:
        return None
    m = re.search(r"(\d{4})(\d{2})(\d{2})", str(raw))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def _outside(boxes: list[Any]) -> Any:
    """A pdfplumber object filter keeping what lies OUTSIDE the given table boxes."""
    def keep(obj: dict[str, Any]) -> bool:
        return not _inside(obj, boxes)
    return keep


def _inside(obj: dict[str, Any], boxes: list[Any]) -> bool:
    x = (float(obj.get("x0", 0)) + float(obj.get("x1", 0))) / 2
    y = (float(obj.get("top", 0)) + float(obj.get("bottom", 0))) / 2
    return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in boxes)


def _read_pdf(path: Path, read: DocumentRead, declared: Declared) -> DocumentRead:
    import pdfplumber  # imported here: only a PDF needs it

    try:
        pdf = pdfplumber.open(path)
    except Exception as exc:  # noqa: BLE001 — an unreadable PDF is a refusal, said plainly
        raise DocumentError(f"the PDF cannot be opened ({type(exc).__name__})") from exc
    with pdf:
        meta = {k: str(v) for k, v in (pdf.metadata or {}).items()
                if isinstance(v, str | int | float)}
        read.meta = {k: meta[k] for k in ("Title", "Author", "Subject", "Producer", "Creator")
                     if meta.get(k)}
        for k in ("CreationDate", "ModDate"):
            if (d := _pdf_date(meta.get(k))) is not None:
                read.meta[k] = f"{d} (a FILE date — never used as the publication date)"
        read.pages = len(pdf.pages)
        lines_by_page: list[list[dict[str, Any]]] = []
        tables_by_page: list[list[tuple[float, list[list[str | None]]]]] = []
        sizes: list[float] = []
        partial = False
        for n, page in enumerate(pdf.pages, 1):
            try:
                found = page.find_tables()
                boxes = [t.bbox for t in found]
                tables = [(float(t.bbox[1]), t.extract()) for t in found]
                body = page.filter(_outside(boxes)) if boxes else page
                lines = body.extract_text_lines(strip=True, return_chars=True)
            except Exception as exc:  # noqa: BLE001 — one bad page never loses the document
                read.issues.append(f"page {n}: could not be read ({type(exc).__name__})")
                partial = True
                lines, tables = [], []
            words = sum(len(str(ln.get("text", "")).split()) for ln in lines)
            if words < SCANNED_MAX_WORDS and page.images and not tables:
                read.issues.append(f"page {n}: no usable text layer ({len(page.images)} image(s)) "
                                   f"— a scanned page is NOT read: OCR is not available here")
                partial = True
            vectors = len(page.curves) + len(page.rects)
            if (page.images or vectors >= CHART_MIN_OBJECTS) and words >= SCANNED_MAX_WORDS:
                read.issues.append(
                    f"page {n}: carries graphics ({len(page.images)} image(s), {vectors} "
                    f"vector object(s)) — chart labels are read as text, plotted values are "
                    f"NOT; figures shown only in a chart are not verifiable")
            for ln in lines:
                for ch in ln.get("chars", []) or []:
                    if ch.get("size"):
                        sizes.append(float(ch["size"]))
            lines_by_page.append(lines)
            tables_by_page.append(tables)
        body_size = Counter(round(s, 1) for s in sizes).most_common(1)[0][0] if sizes else 0.0
        # running headers / footers: the same short line on more than half the pages
        counts = Counter(str(ln.get("text", "")).strip() for page_lines in lines_by_page
                         for ln in page_lines)
        n_pages = max(1, len(lines_by_page))
        chrome = {t for t, c in counts.items() if c > n_pages / 2 and n_pages > 2
                  and len(t.split()) <= 12}
        dropped = 0
        blocks: list[Block] = []
        section: str | None = None
        title_lines: list[tuple[float, str]] = []
        page1_texts: list[str] = []
        for n, (page_lines, tables) in enumerate(zip(lines_by_page, tables_by_page,
                                                     strict=True), 1):
            para: list[str] = []
            last_bottom: float | None = None
            last_size = body_size
            heading_bottom: float | None = None
            pending = sorted(tables, key=lambda tb: tb[0])
            for ln in page_lines:
                top = float(ln.get("top", 0))
                while pending and pending[0][0] <= top:  # a table above this line: in order
                    _flush(blocks, para, n, section)
                    read.tables += _table_block(blocks, pending.pop(0)[1], n, section)
                    heading_bottom = None
                text = str(ln.get("text", "")).strip()
                if not text:
                    continue
                if text in chrome or re.fullmatch(r"(page\s*)?\d{1,4}(\s*(of|/)\s*\d{1,4})?",
                                                   text, re.I):
                    dropped += 1
                    continue
                chars = ln.get("chars") or []
                size = (sum(float(c.get("size", 0)) for c in chars) / len(chars)) if chars \
                    else body_size
                if n <= 2:
                    page1_texts.append(text)
                if n == 1 and size > body_size * 1.15:
                    title_lines.append((size, text))
                gap = (top - last_bottom) if last_bottom is not None else 0.0
                heading = (size >= body_size * 1.2 and len(text.split()) <= 18
                           and body_size > 0)
                footnote = (body_size > 0 and size <= body_size * 0.85
                            and re.match(r"^(\d{1,3}|[*†‡§])\s", text) is not None)
                new_para = (last_bottom is None or gap > max(4.0, body_size * 0.9)
                            or abs(size - last_size) > 1.0)
                if heading and heading_bottom is not None and blocks \
                        and blocks[-1].kind == "heading" and top - heading_bottom < size:
                    # a heading wrapped onto a second line is ONE heading
                    section = f"{blocks.pop().text} {text}"
                    _block(blocks, "heading", section, n, section)
                    heading_bottom = float(ln.get("bottom", top))
                elif heading:
                    _flush(blocks, para, n, section)
                    section = text
                    _block(blocks, "heading", text, n, section)
                    heading_bottom = float(ln.get("bottom", top))
                elif footnote:
                    _flush(blocks, para, n, section)
                    _block(blocks, "footnote", text, n, section)
                else:
                    if new_para:
                        _flush(blocks, para, n, section)
                    para.append(text)
                if not heading:
                    heading_bottom = None
                last_bottom = float(ln.get("bottom", top))
                last_size = size
            _flush(blocks, para, n, section)
            for _top, t in pending:
                read.tables += _table_block(blocks, t, n, section)
        if dropped:
            read.issues.append(f"{dropped} running header / footer / page-number line(s) "
                               f"left out")
    title_src = None
    title = None
    meta_title = read.meta.get("Title")
    if meta_title and not _GENERIC_TITLE.search(meta_title.strip()) and len(meta_title) > 3:
        title, title_src = meta_title.strip(), "PDF document metadata (Title)"
    elif title_lines:
        top_size = max(s for s, _ in title_lines)
        title = " ".join(t for s, t in title_lines if s >= top_size - 0.5)[:300]
        title_src = "the largest text on page 1"
    authors = ([Author(name=a.strip(), source_field="PDF document metadata (Author)")
                for a in re.split(r"[;,]| and ", read.meta.get("Author", "")) if a.strip()
                and not _GENERIC_TITLE.search(a)])
    doc_date = _date_from(page1_texts[:80])
    return _finish(read, blocks=blocks, title=title, title_src=title_src, authors=authors,
                   doc_date=doc_date, date_src="the document text (page 1-2)" if doc_date
                   else None, declared=declared, canonical=_canonical(declared, read),
                   partial=partial)


def _table_block(blocks: list[Block], table: list[list[str | None]], page: int,
                 section: str | None) -> int:
    """A table as ONE block: rows ' ; '-separated, cells ' | '-separated, values as printed."""
    rows = [" | ".join((c or "").replace("\n", " ").strip() for c in row)
            for row in table if row and any((c or "").strip() for c in row)]
    if not rows:
        return 0
    _block(blocks, "table", " ; ".join(rows), page, section)
    return 1


def _flush(blocks: list[Block], para: list[str], page: int, section: str | None) -> None:
    """One paragraph out of the lines gathered so far (and the gathering emptied)."""
    if para:
        _block(blocks, "paragraph", _dehyphenate(para), page, section)
        para.clear()


def _dehyphenate(lines: list[str]) -> str:
    out = ""
    for ln in lines:
        if out.endswith("-") and ln[:1].islower():
            out = out[:-1] + ln
        else:
            out = f"{out} {ln}" if out else ln
    return out


# --- Markdown / text -----------------------------------------------------------------------------

def _read_markdown(text: str, read: DocumentRead, declared: Declared) -> DocumentRead:
    front: dict[str, str] = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for ln in m.group(1).splitlines():
            if ":" in ln:
                k, v = ln.split(":", 1)
                front[k.strip().lower()] = v.strip().strip('"')
        text = text[m.end():]
    blocks: list[Block] = []
    section: str | None = None
    title = front.get("title")
    title_src = "Markdown front matter (title)" if title else None
    para: list[str] = []
    table: list[str] = []

    def flush() -> None:
        if para:
            _block(blocks, "paragraph", " ".join(para), None, section)
            para.clear()
        if table:
            rows = [r.strip().strip("|").strip() for r in table
                    if not re.fullmatch(r"\|?[\s:|-]+\|?", r.strip())]
            if rows:
                read.tables += 1
                _block(blocks, "table", " ; ".join(r.replace(" | ", " | ") for r in rows),
                       None, section)
            table.clear()

    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            flush()
            continue
        if s.startswith("|"):
            if para:
                flush()
            table.append(s)
            continue
        if table:
            flush()
        h = re.match(r"^(#{1,6})\s+(.*)$", s)
        if h:
            flush()
            section = h.group(2).strip()
            if title is None and len(h.group(1)) == 1:
                title, title_src = section, "the first Markdown heading"
            _block(blocks, "heading", section, None, section)
        elif re.match(r"^([-*+]|\d+[.)])\s+", s):
            flush()
            _block(blocks, "list_item", re.sub(r"^([-*+]|\d+[.)])\s+", "", s), None, section)
        else:
            para.append(s)
    flush()
    authors = [Author(name=a.strip(), source_field="Markdown front matter (author)")
               for a in re.split(r"[;,]| and ", front.get("author", front.get("authors", "")))
               if a.strip()]
    fd = front.get("date") or front.get("published")
    doc_date = date_in_text(fd) if fd else None
    src = "Markdown front matter (date)" if doc_date else None
    if doc_date is None:
        doc_date = _date_from([b.text for b in blocks[:8]])
        src = "the document text (opening lines)" if doc_date else None
    return _finish(read, blocks=blocks, title=title, title_src=title_src, authors=authors,
                   doc_date=doc_date, date_src=src, declared=declared,
                   canonical=_canonical(declared, read), partial=False)


def _read_text(text: str, read: DocumentRead, declared: Declared) -> DocumentRead:
    blocks: list[Block] = []
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    title = None
    if paras and len(paras[0].split()) <= 20 and "\n" not in paras[0]:
        title = paras[0]
        _block(blocks, "heading", title, None, title)
        paras = paras[1:]
    for p in paras:
        _block(blocks, "paragraph", p, None, title)
    doc_date = _date_from([b.text for b in blocks[:6]])
    return _finish(read, blocks=blocks, title=title,
                   title_src="the first line" if title else None, authors=[],
                   doc_date=doc_date, date_src="the document text (opening lines)" if doc_date
                   else None, declared=declared, canonical=_canonical(declared, read),
                   partial=False)


def _canonical(declared: Declared, read: DocumentRead) -> str:
    """The article identity: the original URL when the operator knows it; otherwise the
    document's own content — a report with no public URL is still ONE article."""
    return declared.url or f"urn:document:sha256:{read.sha256}"


# --- entry point ---------------------------------------------------------------------------------

def read_document(path: Path, declared: Declared) -> DocumentRead:
    """Read one file. Raises DocumentError for an unsupported, encrypted or empty file."""
    if not path.is_file():
        raise DocumentError(f"{path} is not a file")
    ext = path.suffix.lower()
    if ext == ".docx":
        raise DocumentError("DOCX is not supported — no compatible library is installed; save "
                            "the report as PDF and import that")
    fmt = SUPPORTED.get(ext)
    if fmt is None:
        raise DocumentError(f"unsupported format {ext or '(none)'} — PDF, HTML, Markdown or "
                            f"plain text")
    size = path.stat().st_size
    if size == 0:
        raise DocumentError(f"{path.name} is empty")
    sha = file_sha256(path)
    empty = ParsedDocument(canonical_url="", title=None, title_source=None, authors=(),
                           authors_status=FieldStatus.UNKNOWN, published_at=None,
                           published_raw=None, published_source=None,
                           published_status=FieldStatus.UNKNOWN, modified_at=None,
                           modified_source=None, blocks=(), retrieval_state=RetrievalState.BLOCKED)
    read = DocumentRead(path=path, sha256=sha, fmt=fmt, size=size, doc=empty)
    if fmt == "pdf":
        return _read_pdf(path, read, declared)
    text = path.read_bytes().decode("utf-8", errors="replace")
    if fmt == "html":
        html, tables = _html_tables(text)
        doc = parse_document(html, _canonical(declared, read), declared.url)
        if tables:
            blocks = tuple(b.model_copy(update={"kind": "table"}) if b.text in tables else b
                           for b in doc.blocks)
            read.tables = sum(1 for b in blocks if b.kind == "table")
            doc = _replace(doc, blocks=blocks)
        if doc.published_at is None and (d := _date_from([b.text for b in doc.blocks[:8]])):
            doc = _with_date(doc, d, "the document text (opening lines)")
        if not doc.authors and (by := _byline([b.text for b in doc.blocks[:10]])):
            doc = _replace(doc, authors=tuple(by), authors_status=FieldStatus.KNOWN)
        read.doc = doc
        if declared.published and doc.published_at is None:
            read.doc = _with_declared_date(doc, declared.published)
        elif declared.published and doc.published_at is not None \
                and doc.published_at.date() != declared.published:
            read.date_disagreement = (f"the operator states {declared.published.isoformat()} "
                                      f"but the page states {doc.published_at.date()} — the "
                                      f"page's own date is used")
            read.doc = _replace(doc, notes=[*doc.notes, read.date_disagreement])
        if declared.title and not doc.title:
            read.doc = _replace(read.doc, title=declared.title, title_source="operator-stated")
        if declared.authors and not doc.authors:
            read.doc = _replace(read.doc, authors=tuple(
                Author(name=a, source_field="operator-stated") for a in declared.authors),
                authors_status=FieldStatus.KNOWN)
        return read
    if fmt == "markdown":
        return _read_markdown(text, read, declared)
    return _read_text(text, read, declared)


def _replace(doc: ParsedDocument, **kw: Any) -> ParsedDocument:
    from dataclasses import replace

    return replace(doc, **kw)


def _with_date(doc: ParsedDocument, d: date, source: str) -> ParsedDocument:
    return _replace(doc, published_at=datetime(d.year, d.month, d.day, tzinfo=UTC),
                    published_raw=d.isoformat(), published_source=source,
                    published_status=FieldStatus.KNOWN)


def _with_declared_date(doc: ParsedDocument, d: date) -> ParsedDocument:
    return _with_date(doc, d, "operator-stated (the page states no date)")


def _html_tables(text: str) -> tuple[str, set[str]]:
    """Each HTML <table> as ONE paragraph of its rows (' ; ') and cells (' | '), values as
    printed — the shared web parser would split it into a paragraph per cell. Returns the
    rewritten HTML and the serialised tables (to re-label those blocks `table`)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(text, "html.parser")
    found: set[str] = set()
    for tbl in reversed(soup.find_all("table")):  # innermost first
        rows = []
        for tr in tbl.find_all("tr"):
            cells = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)).strip()
                     for c in tr.find_all(["td", "th"])]
            if any(cells):
                rows.append(" | ".join(cells))
        if not rows:
            continue
        serial = " ; ".join(rows)
        p = soup.new_tag("p")
        p.string = serial
        tbl.replace_with(p)
        found.add(serial)
    return (str(soup), found) if found else (text, set())
