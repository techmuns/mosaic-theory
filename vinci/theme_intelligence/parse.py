"""Publisher HTML → an addressable document: metadata read from the page, never invented, and the
body as numbered blocks a claim can point back to.

METADATA ORDER (first hit wins, and the field it came from is recorded):
  title      JSON-LD headline → og:title (site suffix stripped) → <h1> → <title>
  authors    the UNION of every place the page credits an author — JSON-LD Article.author,
             schema.org/Person microdata (itemprop=author), meta[name=author] — each author
             recording every field it was found in. Sources that DISAGREE are recorded as a
             discrepancy (J.P. Morgan's "A calm index" lists Kriti Gupta in JSON-LD but credits
             Nick Roberts too in its byline microdata; first-hit-wins dropped him). Authors the
             article TEXT credits ("team led by …") are added after extraction, as verified spans.
  published  JSON-LD datePublished → meta article:published_time → the page's own Next.js page
             data (`publishDate` of the entry whose url is this page) → "Published <date>" text
             in the body → UNKNOWN
  modified   JSON-LD dateModified → meta article:modified_time  (never the publication date)
Alternate official versions the page declares (hreflang) are recorded, so a reader can see
whether another regional edition could credit someone else.
A date that states only a month ("September 2024") is kept RAW with status UNKNOWN — inventing the
1st or the 15th would fabricate an entry point.

BODY. The main content container is chosen by paragraph mass (not a site-specific selector), then
walked in document order emitting leaf text blocks. Chart titles, chart source notes ("Source:
Bloomberg… Data as of …") and accessible chart descriptions are their own block kinds, because they
carry the as-of dates and approximate chart values the brief needs labelled. Everything after a
related-content heading ("you may also like") is dropped — that is where a page's OTHER articles'
dates live (the JPM acceptance page carries an unrelated "Oct 2, 2026" there).

COMPLETENESS. PARTIAL when the page is a teaser / paywalled / a summary of a report it links to;
BLOCKED when no body survives. A PARTIAL article is analysed, but never as a full text.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import (
    Comment,
    Declaration,
    Doctype,
    NavigableString,
    ProcessingInstruction,
    Tag,
)

from vinci.theme_intelligence.schemas import (
    ArticleClass,
    Author,
    Block,
    FieldStatus,
    RetrievalState,
)

#: A PDF text layer's code for a glyph whose font carries no character map: the extractor
#: cannot say which letter it is and writes "(cid:N)" instead. Observed 2026-10-11 on a real
#: 60-page Citi report: its last 7 pages came out as 302,376 characters of such codes —
#: 242,000 input tokens of nothing, resent in every model call, and 446 false "figures".
GLYPH_CODE = re.compile(r"\(cid:\d+\)")
#: a segment (a text line, a table cell) is UNREADABLE when at least this many codes cover at
#: least this share of its non-space characters — one stray code (an unmapped ligature) or a
#: sentence that merely MENTIONS a CID never qualifies
GLYPH_MIN_CODES = 3
GLYPH_MIN_SHARE = 0.5


def unreadable_glyphs(text: str) -> bool:
    """The segment is undecodable font output, not text."""
    codes = GLYPH_CODE.findall(text)
    if len(codes) < GLYPH_MIN_CODES:
        return False
    solid = len(re.sub(r"\s", "", text))
    return sum(len(c) for c in codes) >= GLYPH_MIN_SHARE * max(1, solid)


_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "figcaption", "blockquote", "div",
               "section", "article", "td", "th", "dd", "dt", "span", "ul", "ol", "table", "tr",
               "figure", "header", "aside", "main"}
_LEAF_BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "figcaption", "blockquote", "td",
               "th", "dd", "dt"}
_DROP_TAGS = {"script", "style", "noscript", "nav", "footer", "form", "button", "svg", "iframe",
              "template", "select", "input"}
_NOISE_ATTR = re.compile(
    r"(share|social|related|recommend|newsletter|subscribe|cookie|breadcrumb|site-?footer|"
    r"site-?header|navbar|menu|promo|you-may-also|trending|sidebar|signup|modal|popup|toolbar)",
    re.I)
#: A related-content heading is the WHOLE heading — a prefix match cut articles at body headings
#: such as "Recommended positioning for 2027" or "Read more into the guidance" (recorded FULL).
#: "More from" stops only before a NAME ("More from J.P. Morgan"), never a topic ("More from the
#: data centre build-out").
_STOP_HEADINGS = re.compile(
    r"^(?:(?i:you may also like|related (?:articles|insights|content)|trending insights"
    r"|recommended(?: for you| reading| articles| insights| content)?"
    r"|read more(?: insights| articles| stories)?|explore more(?: of our [\w .&'’-]{1,40})?"
    r"|latest insights"
    r"|experience the full possibility(?: of [\w .&'’-]{1,40})?)"
    r"|(?i:more from)(?: [A-Z0-9][\w.&'’-]*){1,4})\s*[:.!…]?$")
_DISCLAIMER_HEADINGS = re.compile(
    r"^(important information|disclaimer|disclosures?|important disclosures|legal (notice|"
    r"disclaimer)|general risks)", re.I)
_UI_NOISE = re.compile(r"^(view info|hide info|\{0\} minutes?( read)?|show more|share|linkedin|"
                       r"facebook|x\(twitter\)|print|download|in this article|skip to (main )?"
                       r"content|lightbox|close|menu|search)$", re.I)
_PAYWALL = re.compile(
    r"(this post is for paid subscribers|subscribe to (continue|read)|become a (paid )?member|"
    r"log ?in to (continue|read)|sign in to (continue|read)|already a subscriber\?|"
    r"keep reading with a 7-day free trial|for subscribers only|paywall)", re.I)


def paywall_marker(text: str) -> str | None:
    """The subscriber / paywall marker in `text`, if any — ONE definition for a retrieved page
    (below) and a supplied document (documents.py)."""
    m = _PAYWALL.search(text)
    return m.group(0) if m else None


#: a trailing " | Site" / " – Site" / " - Site" part of a title
_SITE_SUFFIX = re.compile(r"\s+[|\u2013\u2014-]\s+([^|\u2013\u2014]+?)\s*$")


def clean_title(title: str | None, publisher: str = "") -> str:
    """An article title as a reader names it — ONE definition for the importer and every screen:
    HTML entities decoded ("America&#039;s"), and a trailing site part dropped when it only
    repeats the publisher. A page saved as PDF keeps its browser-tab title, so every Morgan
    Stanley article arrived as "… | Morgan Stanley" and Review read "… | Morgan Stanley Morgan
    Stanley" (2026-10-14). Any other trailing part is the title's own and stays ("Must C -
    Sizing the ETF Opportunity")."""
    t = html.unescape(title or "").strip()
    m = _SITE_SUFFIX.search(t)
    if m and publisher and m.start() > 0:
        site, pub = _name_tokens(m.group(1)), _name_tokens(publisher)
        n = min(len(site), len(pub))
        if n and site[:n] == pub[:n]:
            return t[: m.start()].rstrip()
    return t


def _without_site(title: str, site: str | None) -> str:
    """An og:title without a trailing " | Site" part that only NAMES the site (`og:site_name`). The
    first separator was cut at, so Citi's "Overcoming Gridlock 2.0 — <subtitle>" was stored as
    its first half (U30f); a part that is not the site's name is the title's own and stays."""
    m = _SITE_SUFFIX.search(title)
    if m and site and m.start() > 0 and _name_tokens(m.group(1)) == _name_tokens(site):
        return title[:m.start()].rstrip()
    return title.strip()


def _name_tokens(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())
_FULL_REPORT_ELSEWHERE = re.compile(
    r"(read the full (article|report)|download the (full )?report|full report (is )?available)",
    re.I)
#: an anchor that leads to the full report ("Download Here", "Read the full report") — NOT
#: "Download PDF", which on BofA's pages is a print edition of the same article
_REPORT_ANCHOR = re.compile(r"^(download( (here|now|report|the (full )?report))|"
                            r"(read|view|access) the (full )?report|full report)$", re.I)
_RESEARCH_DISCLAIMER = re.compile(r"should not be regarded as a research report", re.I)
_BOILERPLATE = re.compile(r"^(past performance (does not|is not|is no)|it is not possible to "
                          r"invest directly in an index|for illustrative purposes only)", re.I)
_TAG_HEADINGS = re.compile(r"^(tags|topics|related topics|filed under|categories)$", re.I)
_MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|"
           "december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
_PUBLISHED_TEXT = re.compile(rf"\bpublished\s*:?\s*((?:{_MONTHS})\.? \d{{1,2}},? \d{{4}})", re.I)
_PUBLISHED_LINE = re.compile(rf"published\s*:?\s*(?:{_MONTHS})\.? \d{{1,2}},? \d{{4}}", re.I)


@dataclass
class ParsedDocument:
    canonical_url: str
    title: str | None
    title_source: str | None
    authors: tuple[Author, ...]
    authors_status: FieldStatus
    published_at: datetime | None
    published_raw: str | None
    published_source: str | None
    published_status: FieldStatus
    modified_at: datetime | None
    modified_source: str | None
    blocks: tuple[Block, ...]
    retrieval_state: RetrievalState
    notes: list[str] = field(default_factory=list)
    article_class_hint: ArticleClass | None = None
    article_class_basis: str | None = None
    #: authors credited by one metadata source but not another, said plainly (None: they agree)
    author_discrepancy: str | None = None
    #: the date THIS document states and where it was read, when it is not `published_at`
    #: (an upgrade keeps the article's date there; this keeps the document's own)
    stated_date: tuple[date, str] | None = None
    #: alternate official versions the page declares: (hreflang, url)
    alternates: tuple[tuple[str, str], ...] = ()
    #: links to the FULLER REPORT the page summarises: (anchor text, absolute url) — read only
    #: where the channel permits (sources.toml `linked_reports`), else listed for upload
    linked_reports: tuple[tuple[str, str], ...] = ()
    #: set when the ONLY unread part is back matter by the document's own contents list (the
    #: basis, said plainly) — see documents.classify_unread
    unread_back_matter: str = ""

    @property
    def body_blocks(self) -> tuple[Block, ...]:
        return tuple(b for b in self.blocks
                     if b.kind not in ("disclaimer", "byline", "dek", "tag"))

    @property
    def word_count(self) -> int:
        return sum(len(b.text.split()) for b in self.body_blocks)

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256("\n".join(b.text for b in self.blocks).encode()).hexdigest()


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def parse_iso(raw: str) -> datetime | None:
    """Always timezone-aware: a date-only or offset-less stamp reads as UTC (a naive instant
    cannot be compared with an aware one)."""
    raw = raw.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):  # date-only → midnight UTC, flagged by caller
            return datetime.fromisoformat(raw).replace(tzinfo=UTC)
        d = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return d if d.tzinfo is not None else d.replace(tzinfo=UTC)
    except ValueError:
        return None


def _states_offset(raw: str) -> bool:
    """Whether a date stamp states its own UTC offset ("…Z", "…+08:00")."""
    try:
        return datetime.fromisoformat(raw.strip().replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def _own_page_text(soup: BeautifulSoup) -> str:
    """The page's text WITHOUT what is not this article: noise elements (related, sidebar,
    promo …) and everything from the first related-content heading on. A "You may also like"
    card's "Published Oct 2, 2026" dated the page it sat on."""
    s = BeautifulSoup(str(soup), "html.parser")
    for el in s.find_all(True):
        if el.parent is not None and _noise(el):
            el.extract()
    for h in s.find_all(re.compile(r"^h[1-6]$")):
        if _STOP_HEADINGS.match(h.get_text(" ", strip=True)):
            node: Any = h
            while node is not None and node is not s:
                for sib in list(node.next_siblings):
                    sib.extract()
                node = node.parent
            h.extract()
            break
    return s.get_text(" ", strip=True)


def parse_text_date(raw: str) -> datetime | None:
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y", "%b. %d, %Y"):
        try:
            return datetime.strptime(re.sub(r"\bSept\b", "Sep", raw), fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def _jsonld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and "@graph" in it and isinstance(it["@graph"], list):
                items.extend(x for x in it["@graph"] if isinstance(x, dict))
            if isinstance(it, dict):
                out.append(it)
    return out


def _meta(soup: BeautifulSoup, *names: str) -> str | None:
    for n in names:
        el = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
        if isinstance(el, Tag) and el.get("content"):
            return _clean(str(el.get("content")))
    return None


def _article_ld(ld: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The page's own Article record: any schema.org Article subtype (Article, NewsArticle,
    TechArticle, AnalysisNewsArticle, ScholarlyArticle …), a Report, or a *Posting."""
    for it in ld:
        t = it.get("@type")
        types = [str(x) for x in (t if isinstance(t, list) else [t]) if x]
        if any(x.endswith(("Article", "Posting")) or x == "Report" for x in types):
            return it
    return None


def _authors_from_ld(art: dict[str, Any]) -> list[Author]:
    raw = art.get("author")
    items = raw if isinstance(raw, list) else [raw] if raw else []
    out: list[Author] = []
    for a in items:
        if isinstance(a, dict) and a.get("name") and a.get("@type") in (None, "Person"):
            out.append(Author(name=_clean(str(a["name"])), title=None,
                              source_field="json-ld Article.author"))
        elif isinstance(a, dict) and a.get("name") and a.get("@type") == "Organization":
            # the page names an ORGANIZATION as the author — recorded as such, never as a person
            out.append(Author(name=_clean(str(a["name"])), title="organization (as stated)",
                              source_field="json-ld Article.author (Organization)"))
        elif isinstance(a, str) and a.strip():
            out.append(Author(name=_clean(a), title=None, source_field="json-ld Article.author"))
    return out


def _authors_from_microdata(soup: BeautifulSoup) -> list[Author]:
    """schema.org/Person items the page marks as an article's author (itemprop=author / creator):
    the name from itemprop=name, else the itemprop=url link's label; the title from jobTitle."""
    out: list[Author] = []
    for el in soup.find_all(itemtype=re.compile(r"schema\.org/Person", re.I)):
        if not isinstance(el, Tag):
            continue
        prop = str(el.get("itemprop") or "").lower()
        if prop not in ("author", "creator"):
            continue
        name: str | None = None
        nm = el.find(itemprop="name")
        if isinstance(nm, Tag):
            name = str(nm.get("content") or nm.get_text(" ", strip=True)) or None
        if not name:
            link = el.find(itemprop="url")
            if isinstance(link, Tag):
                name = str(link.get("data-label") or link.get_text(" ", strip=True)) or None
        if not name:
            continue
        titles = [str(j.get("content") or j.get_text(" ", strip=True)).strip()
                  for j in el.find_all(itemprop="jobTitle") if isinstance(j, Tag)]
        title = " ".join(t for t in titles if t) or None
        out.append(Author(name=_clean(name), title=_clean(title) if title else None,
                          source_field=f"microdata schema.org/Person (itemprop={prop})"))
    return out


def _name_key(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def _union_authors(sources: list[tuple[str, list[Author]]]) -> tuple[list[Author], str | None]:
    """Every author any source credits, once, with every field that credits them — and, when the
    sources disagree, a plain statement of who is missing from where."""
    merged: dict[str, Author] = {}
    found: dict[str, list[str]] = {}
    for label, authors in sources:
        for a in authors:
            k = _name_key(a.name)
            if not k:
                continue
            found.setdefault(k, [])
            if label not in found[k]:
                found[k].append(label)
            if k not in merged:
                merged[k] = a
            else:
                prev = merged[k]
                merged[k] = prev.model_copy(update={
                    "title": prev.title or a.title,
                    "source_field": prev.source_field if a.source_field in prev.source_field
                    else f"{prev.source_field} + {a.source_field}"})
    # the STRUCTURED author list (the first source, JSON-LD) is the one a reader trusts to be
    # complete — an author credited elsewhere on the page but missing from it is the discrepancy
    # (a single-valued meta tag naming only the first author is the convention, not one)
    primary = sources[0][0]
    note = None
    if sources[0][1]:
        missing = [k for k in merged if primary not in found[k]]
        if missing:
            note = (f"author metadata disagrees: {primary} credits "
                    + ", ".join(a.name for a in sources[0][1]) + "; also credited on the page: "
                    + "; ".join(f"{merged[k].name} (by {' + '.join(found[k])})"
                                for k in missing))
    return list(merged.values()), note


def _next_publish_date(soup: BeautifulSoup, urls: list[str]) -> str | None:
    """`publishDate` of THIS page's own entry in Next.js page data (`__NEXT_DATA__`) — matched by
    the entry's url, so another article's date on the same page is never taken."""
    el = soup.find("script", id="__NEXT_DATA__")
    if not isinstance(el, Tag) or not el.string:
        return None
    try:
        data = json.loads(el.string)
    except json.JSONDecodeError:
        return None
    targets = {u.rstrip("/").lower() for u in urls if u}
    stack: list[Any] = [data]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if o.get("publishDate") and str(o.get("url", "")).rstrip("/").lower() in targets:
                return str(o["publishDate"])
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
    return None


def _noise(el: Tag) -> bool:
    attrs = " ".join([str(el.get("id") or ""), " ".join(el.get("class") or [])])
    return bool(attrs.strip()) and bool(_NOISE_ATTR.search(attrs))


def _main_container(soup: BeautifulSoup) -> Tag:
    """The element holding the most paragraph text (ties → the deepest)."""
    body = soup.body or soup
    best: Tag | None = None
    best_score = 0
    for cand in body.find_all(["article", "main", "div", "section"]):
        if not isinstance(cand, Tag) or _noise(cand):
            continue
        paras = cand.find_all("p")
        score = sum(len(p.get_text(" ", strip=True)) for p in paras
                    if len(p.get_text(" ", strip=True)) > 60)
        if score > best_score * 1.15 or (best is not None and score >= best_score
                                          and best in cand.parents):
            best, best_score = cand, score
    if best is None:
        return body if isinstance(body, Tag) else soup.new_tag("div")
    # widen to an ancestor while it adds substantial paragraph text (a body split across divs)
    cur = best
    for anc in best.parents:
        if not isinstance(anc, Tag) or anc.name in ("body", "html", "[document]"):
            break
        extra = sum(len(p.get_text(" ", strip=True)) for p in anc.find_all("p")
                    if len(p.get_text(" ", strip=True)) > 60)
        if extra > best_score * 1.4 and not _noise(anc):
            cur, best_score = anc, extra
        else:
            break
    return cur


def _para_chars(el: Tag) -> int:
    """The paragraph text an element holds (paragraphs over 60 characters — the container
    scoring's measure)."""
    return sum(n for p in el.find_all("p") if (n := len(p.get_text(" ", strip=True))) > 60)


def _walk(el: Tag, out: list[tuple[str, str]], body_chars: int = 0) -> None:
    """`body_chars`: the container's paragraph text. An element whose id/class reads as noise is
    dropped — UNLESS it holds most of that text: then the name describes the page template, not
    a sidebar. (Citi wraps the whole article in `template-apply-sidebar`; the substring match
    dropped every word of a 7,300-character page, observed 2026-10-11.)"""
    for child in el.children:
        if isinstance(child, (Comment, Doctype, Declaration, ProcessingInstruction)):
            continue  # an HTML comment is markup, not article text
        if isinstance(child, NavigableString):
            t = _clean(str(child))
            if t and len(t) > 1:
                out.append(("text", t))
            continue
        if not isinstance(child, Tag) or child.name in _DROP_TAGS:
            continue
        if _noise(child) and not (body_chars and _para_chars(child) * 2 > body_chars):
            continue
        if child.name in _LEAF_BLOCK:
            t = _clean(child.get_text(" ", strip=True))
            if t:
                out.append((child.name, t))
            continue
        has_block_child = any(isinstance(c, Tag) and c.name in _BLOCK_TAGS
                              for c in child.find_all(recursive=False))
        if child.name in _BLOCK_TAGS and not has_block_child:
            t = _clean(child.get_text(" ", strip=True))
            if t:
                out.append(("div", t))
            continue
        _walk(child, out, body_chars)


def _without_chrome(soup: BeautifulSoup) -> str:
    """The whole page's text WITHOUT its footer and navigation — where the subscriber marker is
    looked for past the body (a long preview puts it beyond the article's blocks). A footer's
    "subscribe to read our newsletter" marked a full article PARTIAL (U30c)."""
    page = BeautifulSoup(str(soup), "html.parser")
    for el in page.find_all(["footer", "nav"]):
        el.decompose()
    for el in page.find_all(lambda x: any(re.fullmatch(r"(site-?)?footer", str(c), re.I)
                                          for c in (x.get("class") or []))):
        el.decompose()
    return page.get_text(" ", strip=True)


def _report_links(container: Tag, base: str) -> tuple[tuple[str, str], ...]:
    """Links in the article body to the fuller report it summarises: a report-download anchor
    ("Download Here") or "here" right after "read the full report". A bare PDF link is NOT one:
    on 2026-10-11 that rule marked every J.P. Morgan page partial for its regulatory Form CRS
    footer and BofA pages for the third-party data they cite — it selected on FORM (a PDF
    exists), not on what the page says the PDF is."""
    out: list[tuple[str, str]] = []
    for a in container.find_all("a", href=True):
        href = str(a.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue
        text = _clean(a.get_text(" ", strip=True))
        hit = bool(_REPORT_ANCHOR.match(text))
        # "Read the full article here." — the anchor's text carries the sentence's full stop
        # (Citi, 2026-10-14: missed, so the page read as a teaser and its PDF was asked for)
        if not hit and text.lower().rstrip(".:!") in ("here", "click here"):
            before = ""
            for prev in a.find_all_previous(string=True, limit=4):
                before = f"{prev} {before}"
            hit = bool(_FULL_REPORT_ELSEWHERE.search(before))
        url = urljoin(base, href)
        if hit and url not in {u for _, u in out}:
            out.append((text or "(link)", url))
    return tuple(out)


def _kind(tag: str, text: str) -> str:
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return "heading"
    if re.match(r"^sources?\s*:", text, re.I):
        return "chart_source"
    if re.match(r"^(the |this )?(chart|graph|table|figure|exhibit) (above |below )?(plots|tracks|"
                r"shows|compares|displays|illustrates|depicts)", text, re.I):
        return "chart_description"
    if _BOILERPLATE.match(text):
        return "disclaimer"
    if tag == "li":
        return "list_item"
    if tag == "figcaption":
        return "chart_title"
    return "paragraph"


def parse_document(html: str, url: str, final_url: str | None = None) -> ParsedDocument:
    soup = BeautifulSoup(html, "html.parser")
    ld = _jsonld(soup)
    art = _article_ld(ld) or {}
    notes: list[str] = []

    # canonical url
    canon_el = soup.find("link", rel="canonical")
    canonical = (str(canon_el.get("href")) if isinstance(canon_el, Tag) and canon_el.get("href")
                 else _meta(soup, "og:url") or final_url or url)
    canonical = urljoin(final_url or url, canonical)

    # title
    title, title_src = None, None
    if art.get("headline"):
        title, title_src = _clean(str(art["headline"])), "json-ld Article.headline"
    elif (og := _meta(soup, "og:title")):
        title, title_src = _without_site(og, _meta(soup, "og:site_name")), "meta og:title"
    elif soup.find("h1"):
        title, title_src = _clean(soup.find("h1").get_text(" ", strip=True)), "h1"  # type: ignore[union-attr]
    elif soup.title and soup.title.string:
        title, title_src = _clean(soup.title.string), "title"

    # authors: the union of every place the page credits one
    meta_authors: list[Author] = []
    if (m := _meta(soup, "author", "article:author", "parsely-author")) \
            and not m.startswith("http"):
        meta_authors = [Author(name=a.strip(), title=None, source_field="meta author")
                        for a in re.split(r",| and ", m) if a.strip()]
    authors, author_note = _union_authors([("JSON-LD Article.author", _authors_from_ld(art)),
                                           ("schema.org/Person microdata",
                                            _authors_from_microdata(soup)),
                                           ("meta author", meta_authors)])
    alternates = tuple(
        (str(ln.get("hreflang")), urljoin(final_url or url, str(ln.get("href"))))
        for ln in soup.find_all("link", hreflang=True)
        if isinstance(ln, Tag) and ln.get("href")
        and "alternate" in [str(r).lower() for r in (ln.get("rel") or [])])

    # dates
    pub_raw, pub_src = None, None
    if art.get("datePublished"):
        pub_raw, pub_src = str(art["datePublished"]), "json-ld Article.datePublished"
    elif (m := _meta(soup, "article:published_time", "datePublished", "publish-date",
                     "date")):
        pub_raw, pub_src = m, "meta published_time"
    elif (nd := _next_publish_date(soup, [url, final_url or "", canonical])):
        pub_raw, pub_src = nd, "Next.js page data publishDate (this page's own entry)"
    mod_raw, mod_src = None, None
    if art.get("dateModified"):
        mod_raw, mod_src = str(art["dateModified"]), "json-ld Article.dateModified"
    elif (m := _meta(soup, "article:modified_time")):
        mod_raw, mod_src = m, "meta article:modified_time"
    elif (m := _meta(soup, "last_modified_date")):
        mod_raw, mod_src = m, "meta last_modified_date (a MODIFICATION date)"

    # body
    container = _main_container(soup)
    raw: list[tuple[str, str]] = []
    _walk(container, raw, _para_chars(container))
    report_links = _report_links(container, final_url or url)
    blocks: list[Block] = []
    section: str | None = None
    in_disclaimer = in_tags = False
    seen: set[str] = set()
    for tag, text in raw:
        if _UI_NOISE.match(text):
            continue
        kind = _kind(tag, text)
        if kind == "heading" and _STOP_HEADINGS.match(text):
            notes.append(f"body truncated at related-content heading {text[:60]!r}")
            break
        if kind == "heading" and _DISCLAIMER_HEADINGS.match(text):
            in_disclaimer = True
        if kind == "heading" and _TAG_HEADINGS.match(text):
            in_tags = True  # topic tags and the byline that follows them — metadata, not body
        if in_tags and kind != "heading":
            kind = "tag"
        elif in_disclaimer and kind != "heading":
            kind = "disclaimer"
        if text in seen and kind not in ("heading",) and tag not in ("td", "th"):
            continue  # pages repeat chart alt text / descriptions for responsive layouts — a
            # table cell's value repeats in its own right ("—", "Yes", "5%"): dropping it shifted
            # its row's columns (U30d)
        seen.add(text)
        if kind == "heading":
            section = text
        blocks.append(Block(block_id=f"b{len(blocks) + 1:03d}", kind=kind, text=text,
                            sha256=hashlib.sha256(text.encode()).hexdigest(), section=section,
                            order=len(blocks) + 1))

    # chart titles: a heading immediately followed by a chart_source / chart_description
    fixed: list[Block] = []
    for i, b in enumerate(blocks):
        nxt = blocks[i + 1].kind if i + 1 < len(blocks) else ""
        if b.kind == "heading" and nxt in ("chart_source", "chart_description"):
            b = b.model_copy(update={"kind": "chart_title"})
        fixed.append(b)
    blocks = fixed

    # Byline blocks (author name, the line after it = their title, "Published <date>") and the
    # dek (the page's own standfirst, = meta description) are metadata, not body text.
    dek = _meta(soup, "description", "og:description")
    names = {a.name.lower() for a in authors}
    relabel: dict[str, str] = {}
    titles: dict[str, tuple[str, str]] = {}
    for i, b in enumerate(blocks):
        if b.text.lower() in names:
            relabel[b.block_id] = "byline"
            # the author's title: the short line(s) after the name — a line ending in a comma
            # continues on the next ("Executive Director," / "Global Investment Strategist")
            parts: list[Block] = []
            for nb in blocks[i + 1:i + 3]:
                if len(nb.text) > 90 or _PUBLISHED_TEXT.search(nb.text) \
                        or nb.text.lower() in names \
                        or nb.kind not in ("paragraph", "disclaimer", "tag"):
                    break
                parts.append(nb)
                if not nb.text.rstrip().endswith(","):
                    break
            if parts:
                for nb in parts:
                    relabel[nb.block_id] = "byline"
                titles[b.text.lower()] = (" ".join(nb.text for nb in parts),
                                          "+".join(nb.block_id for nb in parts))
        elif _PUBLISHED_LINE.fullmatch(b.text):
            relabel[b.block_id] = "byline"
        elif dek and b.text == dek:
            relabel[b.block_id] = "dek"
    if relabel:
        blocks = [b.model_copy(update={"kind": relabel[b.block_id]}) if b.block_id in relabel
                  else b for b in blocks]
    if titles:
        authors = [a.model_copy(update={"title": titles[a.name.lower()][0],
                                        "source_field": f"{a.source_field}; visible byline "
                                                        f"block {titles[a.name.lower()][1]}"})
                   if a.name.lower() in titles else a for a in authors]
    if author_note:
        notes.append(author_note)
    notes.append(f"{len(alternates)} alternate version(s) declared (hreflang) — not fetched"
                 if alternates else "no alternate publication versions declared (hreflang)")

    # "Published Feb 9, 2026" in the page when no structured date exists
    if pub_raw is None and (m2 := _PUBLISHED_TEXT.search(_own_page_text(soup))):
        pub_raw, pub_src = m2.group(1), "page text 'Published <date>'"

    published_at: datetime | None = None
    if pub_raw:
        published_at = parse_iso(pub_raw) or parse_text_date(pub_raw)
        if published_at is None:
            notes.append(f"publication date {pub_raw!r} not parseable to a day — kept raw, UNKNOWN")
        elif not _states_offset(pub_raw):
            notes.append(f"publication date {pub_raw!r} carries no timezone — read as UTC")
    modified_at = (parse_iso(mod_raw) or parse_text_date(mod_raw)) if mod_raw else None

    # completeness
    body_words = sum(len(b.text.split()) for b in blocks if b.kind not in ("disclaimer",))
    page_text_l = " ".join(b.text for b in blocks)
    state = RetrievalState.FULL
    if not blocks or body_words < 40:
        state = RetrievalState.BLOCKED
        notes.append(f"no article body recovered ({body_words} words)")
    # the WHOLE page: a long free preview puts the subscriber marker past any fixed window
    # (pilot 2026-10-12: a SemiAnalysis paid post, marker at character 29,821 — read as FULL)
    elif _PAYWALL.search(page_text_l) or _PAYWALL.search(_without_chrome(soup)):
        state = RetrievalState.PARTIAL
        notes.append("paywall / subscriber marker on the page — analysed as an excerpt only")
    elif body_words < 150:
        state = RetrievalState.PARTIAL
        notes.append(f"short body ({body_words} words) — treated as a teaser / excerpt")
    elif _FULL_REPORT_ELSEWHERE.search(page_text_l) or report_links:
        state = RetrievalState.PARTIAL
        notes.append("the page summarises a fuller report it links to; that report was not read"
                     + (f" ({report_links[0][1]})" if report_links else ""))

    hint, basis = None, None
    for b in blocks:
        if _RESEARCH_DISCLAIMER.search(b.text):
            hint = ArticleClass.PUBLISHER_COMMENTARY
            basis = f"{b.block_id}: page states it 'should not be regarded as a research report'"
            break

    return ParsedDocument(
        canonical_url=canonical, title=title, title_source=title_src,
        authors=tuple(authors),
        authors_status=FieldStatus.KNOWN if authors else FieldStatus.UNKNOWN,
        published_at=published_at, published_raw=pub_raw, published_source=pub_src,
        published_status=FieldStatus.KNOWN if published_at else FieldStatus.UNKNOWN,
        modified_at=modified_at, modified_source=mod_src, blocks=tuple(blocks),
        retrieval_state=state, notes=notes, article_class_hint=hint, article_class_basis=basis,
        author_discrepancy=author_note, alternates=alternates, linked_reports=report_links,
    )
