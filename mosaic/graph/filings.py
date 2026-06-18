"""Fetch a name's latest 10-K and pull the customer/supplier-relevant excerpts for extraction.

The full 10-K is huge; named supply-chain relationships live in a few places (Item 1 Business,
customer-concentration, key-suppliers). We keyword-filter to those paragraphs and cap the length so
the LLM sees signal, not 200 pages — cheaper and more accurate than feeding the whole filing.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from mosaic.edgar.client import EdgarClient
from mosaic.netcache import CachedHttp
from mosaic.resolver.index import pad_cik
from mosaic.sec import build_sec_http

_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
# paragraphs mentioning these are where named customers/suppliers/partners are disclosed
_KEYWORDS = re.compile(
    r"\b(customer|client|supplier|vendor|distributor|reseller|partner|"
    r"manufactur|contract manufactur|accounted for|% of (?:our |net )?revenue|concentrat)\w*",
    re.IGNORECASE,
)


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


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
