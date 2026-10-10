"""Publisher HTML → an addressable document: metadata read from the page, never invented, and the
body as numbered blocks a claim can point back to.

METADATA ORDER (first hit wins, and the field it came from is recorded):
  title      JSON-LD headline → og:title (site suffix stripped) → <h1> → <title>
  authors    JSON-LD author Person(s) → meta[name=author] → UNKNOWN
  published  JSON-LD datePublished → meta article:published_time → <time datetime> in the article
             → "Published <date>" text in the body → UNKNOWN
  modified   JSON-LD dateModified → meta article:modified_time  (never the publication date)
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
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
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
_STOP_HEADINGS = re.compile(
    r"^(you may also like|related (articles|insights|content)|trending insights|more from|"
    r"recommended|read more|explore more|latest insights|experience the full possibility)", re.I)
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
_FULL_REPORT_ELSEWHERE = re.compile(
    r"(read the full (article|report)|download the (full )?report|full report (is )?available)",
    re.I)
_RESEARCH_DISCLAIMER = re.compile(r"should not be regarded as a research report", re.I)
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

    @property
    def body_blocks(self) -> tuple[Block, ...]:
        return tuple(b for b in self.blocks if b.kind not in ("disclaimer", "byline", "dek"))

    @property
    def word_count(self) -> int:
        return sum(len(b.text.split()) for b in self.body_blocks)

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256("\n".join(b.text for b in self.blocks).encode()).hexdigest()


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def parse_iso(raw: str) -> datetime | None:
    raw = raw.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return datetime.fromisoformat(raw)  # date-only → naive midnight, flagged by caller
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_text_date(raw: str) -> datetime | None:
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y", "%b. %d, %Y"):
        try:
            return datetime.strptime(raw.replace("Sept", "Sep"), fmt)
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


def _walk(el: Tag, out: list[tuple[str, str]]) -> None:
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
        if _noise(child):
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
        _walk(child, out)


def _kind(tag: str, text: str) -> str:
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return "heading"
    if re.match(r"^sources?\s*:", text, re.I):
        return "chart_source"
    if re.match(r"^(the )?(chart|graph|table|figure) (plots|tracks|shows|compares|displays)",
                text, re.I):
        return "chart_description"
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
        title, title_src = re.split(r"\s+[|–—-]\s+", og)[0], "meta og:title"
    elif soup.find("h1"):
        title, title_src = _clean(soup.find("h1").get_text(" ", strip=True)), "h1"  # type: ignore[union-attr]
    elif soup.title and soup.title.string:
        title, title_src = _clean(soup.title.string), "title"

    # authors
    authors = _authors_from_ld(art)
    if not authors and (m := _meta(soup, "author", "article:author", "parsely-author")) \
            and not m.startswith("http"):
            authors = [Author(name=a.strip(), title=None, source_field="meta author")
                       for a in re.split(r",| and ", m) if a.strip()]

    # dates
    pub_raw, pub_src = None, None
    if art.get("datePublished"):
        pub_raw, pub_src = str(art["datePublished"]), "json-ld Article.datePublished"
    elif (m := _meta(soup, "article:published_time", "datePublished", "publish-date",
                     "date")):
        pub_raw, pub_src = m, "meta published_time"
    mod_raw, mod_src = None, None
    if art.get("dateModified"):
        mod_raw, mod_src = str(art["dateModified"]), "json-ld Article.dateModified"
    elif (m := _meta(soup, "article:modified_time")):
        mod_raw, mod_src = m, "meta article:modified_time"

    # body
    container = _main_container(soup)
    raw: list[tuple[str, str]] = []
    _walk(container, raw)
    blocks: list[Block] = []
    section: str | None = None
    in_disclaimer = False
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
        if in_disclaimer and kind != "heading":
            kind = "disclaimer"
        if text in seen and kind not in ("heading",):
            continue  # pages repeat chart alt text / descriptions for responsive layouts
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
            nb = blocks[i + 1] if i + 1 < len(blocks) else None
            if nb and len(nb.text) <= 90 and not _PUBLISHED_TEXT.search(nb.text) \
                    and nb.kind in ("paragraph", "disclaimer"):
                relabel[nb.block_id] = "byline"
                titles[b.text.lower()] = (nb.text, nb.block_id)
        elif _PUBLISHED_LINE.fullmatch(b.text):
            relabel[b.block_id] = "byline"
        elif dek and b.text == dek:
            relabel[b.block_id] = "dek"
    if relabel:
        blocks = [b.model_copy(update={"kind": relabel[b.block_id]}) if b.block_id in relabel
                  else b for b in blocks]
    if titles:
        authors = [a.model_copy(update={"title": titles[a.name.lower()][0],
                                        "source_field": f"{a.source_field}; title from byline "
                                                        f"block {titles[a.name.lower()][1]}"})
                   if a.name.lower() in titles else a for a in authors]

    # "Published Feb 9, 2026" in the page when no structured date exists
    if pub_raw is None:
        page_text = soup.get_text(" ", strip=True)
        if (m2 := _PUBLISHED_TEXT.search(page_text)):
            pub_raw, pub_src = m2.group(1), "page text 'Published <date>'"

    published_at: datetime | None = None
    if pub_raw:
        published_at = parse_iso(pub_raw) or parse_text_date(pub_raw)
        if published_at is None:
            notes.append(f"publication date {pub_raw!r} not parseable to a day — kept raw, UNKNOWN")
        elif published_at.tzinfo is None:
            notes.append(f"publication date {pub_raw!r} carries no timezone")
    modified_at = (parse_iso(mod_raw) or parse_text_date(mod_raw)) if mod_raw else None

    # completeness
    body_words = sum(len(b.text.split()) for b in blocks if b.kind not in ("disclaimer",))
    page_text_l = " ".join(b.text for b in blocks)
    state = RetrievalState.FULL
    if not blocks or body_words < 40:
        state = RetrievalState.BLOCKED
        notes.append(f"no article body recovered ({body_words} words)")
    elif _PAYWALL.search(page_text_l) or _PAYWALL.search(soup.get_text(" ", strip=True)[:20000]):
        state = RetrievalState.PARTIAL
        notes.append("paywall / subscriber marker on the page — analysed as an excerpt only")
    elif body_words < 150:
        state = RetrievalState.PARTIAL
        notes.append(f"short body ({body_words} words) — treated as a teaser / excerpt")
    elif _FULL_REPORT_ELSEWHERE.search(page_text_l):
        state = RetrievalState.PARTIAL
        notes.append("the page summarises a fuller report it links to; that report was not read")

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
    )
