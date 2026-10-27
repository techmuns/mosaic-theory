"""Fetch a name's latest 10-K and pull the customer/supplier-relevant excerpts for extraction.

The full 10-K is huge; named supply-chain relationships live in a few places (Item 1 Business,
customer-concentration, key-suppliers). We keyword-filter to those paragraphs and cap the length so
the LLM sees signal, not 200 pages — cheaper and more accurate than feeding the whole filing.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from vinci.edgar.client import EdgarClient
from vinci.netcache import CachedHttp
from vinci.resolver.index import pad_cik
from vinci.sec import build_sec_http

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
# paragraphs mentioning these are where named customers/suppliers/partners are disclosed
_KEYWORDS = re.compile(
    r"\b(customer|client|supplier|vendor|distributor|reseller|partner|"
    r"manufactur|contract manufactur|accounted for|% of (?:our |net )?revenue|concentrat)\w*",
    re.IGNORECASE,
)


_WS = re.compile(r"[      ﻿]")


def normalize_text(text: str) -> str:
    """Fold non-breaking / narrow / unicode spaces to a plain space so downstream ANCHORED parsers
    see consistent whitespace (an EDGAR press release renders '$44.7\xa0million' with a nbsp, which
    a ``\\s`` in a regex does NOT match). Shared here — every consumer (covenant / release / section
    parsers) reads normalized text, never a parser-local fix."""
    return _WS.sub(" ", text)


#: A CSS page break — how EDGAR's HTML marks the end of a printed page
#: (`<p style='page-break-before:always'><HR>`, `<hr style="page-break-after:always">`).
_PAGE_BREAK = re.compile(r"\b(?:page-)?break-(before|after)\s*:\s*(?:always|page)\b", re.I)
#: Marks a page break in the flattened text, then removed with the furniture beside it.
_SENTINEL = "\x00"
#: How many words at a page's edge may be furniture: a page number, a running title and a document
#: id ("33 364-Day Revolving Credit Agreement", "104 DB1/ 98023701.7"). Werner's running header is
#: eleven ("Werner Enterprises, Inc. - Release of July 28, 2026 Page 2"), Target's fourteen.
_EDGE_WORDS = 16
#: A furniture run must recur at this share of a document's page breaks (and at least 3): a running
#: footer is on nearly every page, and a phrase that merely happens to end some pages is not.
_RECUR_SHARE = 0.3
#: A word that can be a page number: "76", "-56-", "–3–". Only such a word is read as a number when
#: runs are compared; every other word — a figure, a date, a document id — must recur LITERALLY.
_PAGE_WORD = re.compile(r"[-–—]?(\d{1,4})[-–—]?")
#: The words a page number is printed with ("- 31 -", "Page 12 of 140") — a run may end on one.
_PAGE_FILLER = frozenset({"#", "page", "-", "–", "—"})


def _furniture(edges: list[list[str]], *, tail: bool) -> list[int]:
    """Per page edge, how many of its words are furniture — 0 when none is.

    A run of edge words is furniture when it sits at that edge of at least `_RECUR_SHARE` of the
    pages, WORD FOR WORD except for page-number words ("33 364-Day Revolving Credit Agreement",
    "Page 12 of 140"), and holds a digit — a running footer is printed with its number. Each
    page-number word must then behave like one against the nearest other page carrying the run:
    advance one per page (75, 76) or stay the same (the year in a running title). A table row that
    happens to end three pages ("$ 1,234 $ 1,180 12") recurs nowhere word for word, and a figure
    that ends one page is never taken for a page number."""
    def run(words: list[str], n: int) -> list[str]:
        return words[-n:] if tail else words[:n]

    def key(words: list[str]) -> tuple[str, ...]:
        return tuple("#" if _PAGE_WORD.fullmatch(w) else w.lower() for w in words)

    def numbers(words: list[str]) -> list[int]:
        return [int(m.group(1)) for w in words if (m := _PAGE_WORD.fullmatch(w))]

    at: dict[tuple[str, ...], list[int]] = {}
    for i, words in enumerate(edges):
        for k in {key(run(words, n)) for n in range(1, min(_EDGE_WORDS, len(words)) + 1)}:
            at.setdefault(k, []).append(i)
    need = max(3, int(_RECUR_SHARE * len(edges) + 0.999))
    cut = []
    for i, words in enumerate(edges):
        best = 0
        for n in range(1, min(_EDGE_WORDS, len(words)) + 1):
            k = key(run(words, n))
            # the run ENDS where the furniture does: its innermost word is a number, never a word
            # of the page's text that happens to recur there ("…Page 5 of 11 TARGET CORPORATION
            # Consolidated Statements" keeps its statement title)
            inner = k[0] if tail else k[-1]
            if len(at[k]) < need or not (inner in _PAGE_FILLER or re.search(r"\d", inner)):
                continue
            j = min((j for j in at[k] if j != i), key=lambda j: abs(j - i))
            moves = [b - a for a, b in zip(numbers(run(words, n)), numbers(run(edges[j], n)),
                                           strict=True)]
            literal = [w for w in k if w not in ("#", "page", "of")]
            # every page-number word pages or holds still; a run of numbers alone must page
            if all(d in (0, j - i) for d in moves) and (literal or (j - i) in moves):
                best = n
        cut.append(best)
    return cut


def _drop_page_furniture(text: str) -> str:
    """The flattened text with each page's running footer and header removed (see `html_to_text`),
    and otherwise CHARACTER FOR CHARACTER the text without the marks: only furniture words leave.
    A document with fewer than three page breaks keeps every word — nothing can recur three times
    (`_furniture`)."""
    pages = [p.strip() for p in text.split(_SENTINEL)]
    spans = [[m.span() for m in re.finditer(r"\S+", p)] for p in pages]
    words = [[p[a:b] for a, b in s] for p, s in zip(pages, spans, strict=True)]
    feet = [*_furniture(words[:-1], tail=True), 0]
    heads = [0, *_furniture(words[1:], tail=False)]
    for i, (p, s) in enumerate(zip(pages, spans, strict=True)):
        hi = s[-feet[i]][0] if feet[i] else len(p)
        lo = s[heads[i] - 1][1] if heads[i] else 0
        pages[i] = p[lo:hi].strip() if lo < hi else ""
    return " ".join(p for p in pages if p)


def html_to_text(html: str) -> str:
    """The document's text, one space between text nodes, without its PAGE FURNITURE.

    PAGE FURNITURE (2026-10-27). A filing printed for paper carries a page number, and often a
    running title, at every page break, and the flattened text kept them inside the clause they
    interrupt — "…in an aggregate 76 amount sufficient to reduce…" (EPAM's credit agreement). An
    extractor quoting that clause quotes it without them, so a span check refused 11 of 49
    covenant quotes for furniture alone (`vinci.verbatim`, #804), and a figure read across a break
    could take the page number for a digit. Each CSS page break now marks the text, and the words at
    a page's edge are dropped only when the same run, digits aside, recurs at the edge of many pages
    and carries a number (`_furniture`). Text the filer wrote is never dropped for its position."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    marked = False
    for el in soup.find_all(style=_PAGE_BREAK):
        for side in {m.group(1).lower() for m in _PAGE_BREAK.finditer(str(el.get("style")))}:
            (el.insert_after if side == "after" else el.insert_before)(_SENTINEL)
            marked = True
    text = soup.get_text(" ", strip=True)
    return normalize_text(_drop_page_furniture(text) if marked else text)


def relevant_excerpts(text: str, *, max_chars: int = 24_000) -> str:
    """Keep sentences mentioning supply-chain terms, concatenated up to ``max_chars``."""
    sentences = re.split(r"(?<=[.;])\s+", text)
    kept: list[str] = []
    total = 0
    for s in sentences:
        if _KEYWORDS.search(s) and 20 < len(s) < 1200:
            kept.append(s.strip())
            total += len(s)
            if total >= max_chars:
                break
    return "\n".join(kept)


def latest_10k_excerpts(
    edgar: EdgarClient, cik: int | str, *, http: CachedHttp | None = None
) -> tuple[str, str] | None:
    """(accession, relevant-excerpt text) for the issuer's latest 10-K, or None if none on file."""
    filings = edgar.recent_filings(cik, forms=("10-K",))
    if not filings:
        return None
    latest = max(filings, key=lambda f: f.filing_date)
    if not latest.primary_doc:
        return None
    sec = http or build_sec_http()
    url = _ARCHIVE.format(
        cik=int(pad_cik(latest.cik)), acc=latest.accession.replace("-", ""), doc=latest.primary_doc
    )
    html = sec.get_text(url, ttl_seconds=None)  # filings are immutable → cache forever
    return latest.accession, relevant_excerpts(html_to_text(html))
