"""The automatic source channels → dated article candidates, with honest per-source coverage.

One adapter per publisher LAYOUT (never per article), selected by `adapter` in `sources.toml`:

  citi_next_data     Must C page's embedded CMS data (`__NEXT_DATA__`): series items + publishDate
  jpm_tmt            Top Market Takeaways listing cards (dated); sitemap lastmod as fallback
  generic_listing    entry page anchors matching `link_pattern` (dated cards or page date)
  trendforce_press   press-center pages ?page=N (date in the article URL)
  semianalysis_feed  the newsletter's RSS feed (pubDate)

DATES. A candidate's date is the publication date the SOURCE states — a listing card, the CMS
record, an RSS pubDate, the date in a dated URL, or the article page's own metadata. A sitemap
`lastmod` is a MODIFICATION date: it can only rule an article OUT (modified before the window ⇒
published before it), never in. A candidate whose date cannot be established is counted UNDATED
and not analysed — a date is never invented.

COVERAGE. Every source reports discovered / in window / undated / new / already known / out of
window / inaccessible / errors / warnings and any truncation, whether it worked or not. A source
that cannot be reached is BLOCKED with the reason — it is never a silent zero. Nothing here
bypasses a paywall, a robots rule or an access control: the fetcher is the honest, robots-aware
`PoliteFetcher`, and a refusal is recorded, not retried around.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from vinci.theme_intelligence.config import SourceConfig
from vinci.theme_intelligence.fetch import FetchResult, PoliteFetcher
from vinci.theme_intelligence.parse import parse_document
from vinci.theme_intelligence.schemas import RetrievalState, SourceCoverage
from vinci.theme_intelligence.store import Store

#: Listing pages, feeds and sitemaps change weekly; article pages do not. A short cache keeps a
#: resumed run from re-hitting a publisher without ever serving last week's listing.
LISTING_TTL_S = 6 * 3600.0

_MONTH = ("jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
          "aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?")
_DATE_PATTERNS = (
    (re.compile(rf"\b({_MONTH})\.?\s+(\d{{1,2}}),?\s+(20\d\d)\b", re.I), "mdy"),
    (re.compile(rf"\b(\d{{1,2}})\s+({_MONTH})\.?,?\s+(20\d\d)\b", re.I), "dmy"),
    (re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b"), "iso"),
)
_MONTHS = {m: i + 1 for i, m in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"))}

METHOD = {
    "citi_next_data": "Must C page embedded CMS data (__NEXT_DATA__ contentMap: series items with "
                      "CMS publishDate)",
    "jpm_tmt": "Top Market Takeaways listing cards (card date); sitemap lastmod as fallback",
    "generic_listing": "entry page links matching the configured pattern → card or page date",
    "trendforce_press": "press-center listing pages ?page=N (date in the article URL)",
    "semianalysis_feed": "newsletter RSS feed (item pubDate)",
}


class SourceBlockedError(RuntimeError):
    """The source's entry point could not be retrieved — recorded as BLOCKED, never a zero."""


@dataclass
class Candidate:
    url: str
    source_id: str
    title: str | None = None
    listed_date: date | None = None
    date_basis: str = "undated"
    lastmod: date | None = None  # sitemap modification date — never a publication date
    status: str = "DISCOVERED"  # IN_WINDOW | OUT_OF_WINDOW | UNDATED | INACCESSIBLE | KNOWN
    note: str = ""


@dataclass
class Discovery:
    coverage: SourceCoverage
    candidates: list[Candidate]

    @property
    def selected(self) -> list[Candidate]:
        return [c for c in self.candidates if c.status in ("IN_WINDOW", "INACCESSIBLE")]


# --- helpers -----------------------------------------------------------------------------------

def canon(url: str) -> str:
    """Canonical candidate URL: no fragment, no tracking query, lower-case host, no trailing
    slash (except the root). Query strings are kept only when they carry the page identity."""
    p = urlparse(url.strip())
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    query = "" if not p.query or re.search(r"utm_|ref=|cmp=", p.query) else p.query
    return urlunparse((p.scheme.lower() or "https", p.netloc.lower(), path, "", query, ""))


def date_in_text(text: str) -> date | None:
    for pat, kind in _DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        try:
            if kind == "mdy":
                return date(int(m.group(3)), _MONTHS[m.group(1)[:3].lower()], int(m.group(2)))
            if kind == "dmy":
                return date(int(m.group(3)), _MONTHS[m.group(2)[:3].lower()], int(m.group(1)))
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
    return None


def _soup(fr: FetchResult) -> BeautifulSoup:
    return BeautifulSoup(fr.text or "", "html.parser")


def _get(f: PoliteFetcher, url: str, cov: SourceCoverage, *, listing: bool = True) -> FetchResult:
    fr = f.fetch(url, ttl_s=LISTING_TTL_S if listing else 7 * 86_400.0)
    if url not in cov.entry_points:
        cov.entry_points.append(url)
    return fr


def _in_chrome(a: Tag) -> bool:
    return any(isinstance(p, Tag) and p.name in ("nav", "header", "footer")
               for p in a.parents)


def card_links(soup: BeautifulSoup, base: str, pattern: re.Pattern[str],
               *, min_text: int = 0) -> list[tuple[str, str, date | None]]:
    """(url, anchor text, card date) for every matching link outside page chrome. The card is the
    largest ancestor that contains no OTHER matching link, so a date is only ever read from the
    link's own card — never from a neighbour or a site-wide date banner."""
    anchors: list[tuple[Tag, str]] = []
    for a in soup.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue
        href = canon(urljoin(base, str(a["href"])))
        if pattern.search(href) and not _in_chrome(a) and canon(base) != href:
            anchors.append((a, href))
    hrefs = {h for _, h in anchors}
    out: dict[str, tuple[str, str, date | None]] = {}
    for a, href in anchors:
        text = " ".join(a.get_text(" ", strip=True).split())
        card: Tag = a
        for p in a.parents:
            if not isinstance(p, Tag) or p.name in ("body", "html", "main"):
                break
            inner = {canon(urljoin(base, str(x["href"]))) for x in p.find_all("a", href=True)
                     if isinstance(x, Tag)} & hrefs
            if inner - {href}:
                break
            card = p
        d = date_in_text(card.get_text(" ", strip=True))
        prev = out.get(href)
        if prev is None or (len(text) > len(prev[1])) or (prev[2] is None and d is not None):
            out[href] = (href, text if prev is None or len(text) > len(prev[1]) else prev[1],
                         d if d is not None else (prev[2] if prev else None))
    return [v for v in out.values() if len(v[1]) >= min_text]


def _xml(fr: FetchResult) -> ET.Element:
    if fr.content is None:
        raise SourceBlockedError(fr.note)
    return ET.fromstring(fr.content)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def sitemap_entries(root: ET.Element) -> list[tuple[str, date | None]]:
    out: list[tuple[str, date | None]] = []
    for el in root.iter():
        if _local(el.tag) != "url":
            continue
        loc = lastmod = None
        for ch in el:
            if _local(ch.tag) == "loc" and ch.text:
                loc = ch.text.strip()
            elif _local(ch.tag) == "lastmod" and ch.text:
                lastmod = ch.text.strip()
        if loc:
            lm = None
            if lastmod:
                try:
                    lm = datetime.fromisoformat(lastmod.replace("Z", "+00:00")).date()
                except ValueError:
                    lm = None
            out.append((loc, lm))
    return out


# --- adapters ------------------------------------------------------------------------------------

Adapter = Callable[[SourceConfig, PoliteFetcher, SourceCoverage], list[Candidate]]


def _entry(src: SourceConfig, f: PoliteFetcher, cov: SourceCoverage,
           url: str | None = None) -> FetchResult:
    fr = _get(f, url or src.entry_url, cov)
    if fr.state is RetrievalState.BLOCKED or fr.content is None:
        raise SourceBlockedError(f"{url or src.entry_url}: {fr.note}")
    return fr


def citi_next_data(src: SourceConfig, f: PoliteFetcher, cov: SourceCoverage) -> list[Candidate]:
    fr = _entry(src, f, cov)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', fr.text or "", re.S)
    if not m:
        raise RuntimeError("page data (__NEXT_DATA__) not found — the page layout changed")
    cmap = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("contentMap", {})
    series = next((v for v in cmap.values() if isinstance(v, dict) and canon(
        str(v.get("content_json", {}).get("url", ""))) == canon(src.entry_url)), None)
    if series is None:
        raise RuntimeError("the series record for the entry page is missing from its page data")
    cj = series["content_json"]
    ids = list(cj.get("relatedInsights", [])) + list(cj.get("nextInsight", []))
    out: list[Candidate] = []
    for i in dict.fromkeys(ids):
        rec = cmap.get(i)
        if not isinstance(rec, dict):
            cov.warnings.append(f"series item {i} is referenced but not embedded in the page")
            continue
        c = rec.get("content_json", {})
        url = c.get("url")
        if not url:
            continue
        pd_raw = c.get("publishDate")
        try:
            pdate = date.fromisoformat(pd_raw) if pd_raw else None
        except ValueError:
            pdate = None
        out.append(Candidate(url=canon(url), source_id=src.id, title=rec.get("title"),
                             listed_date=pdate,
                             date_basis="Citi CMS publishDate (page data)" if pdate
                             else "undated"))
    cov.truncation = (f"the Must C page embeds its {len(ids)} linked series items; older items "
                      f"are not listed there")
    return out


def jpm_tmt(src: SourceConfig, f: PoliteFetcher, cov: SourceCoverage) -> list[Candidate]:
    fr = _entry(src, f, cov)
    base = canon(src.entry_url)
    pat = re.compile("^" + re.escape(base) + r"/[^/]+$")
    links = card_links(_soup(fr), fr.final_url or src.entry_url, pat)
    out = [Candidate(url=u, source_id=src.id, title=t, listed_date=d,
                     date_basis="listing card date" if d else "undated") for u, t, d in links]
    if out and any(c.listed_date for c in out) or not src.sitemap_url:
        return out
    cov.warnings.append("listing cards carried no dates — falling back to the sitemap")
    sm = _get(f, src.sitemap_url, cov)
    for loc, lm in sitemap_entries(_xml(sm)):
        if pat.search(canon(loc)):
            out.append(Candidate(url=canon(loc), source_id=src.id, lastmod=lm,
                                 date_basis="undated (sitemap lastmod is a modification date)"))
    return out


def generic_listing(src: SourceConfig, f: PoliteFetcher,
                    cov: SourceCoverage) -> list[Candidate]:
    fr = _entry(src, f, cov)
    if not src.link_pattern:
        raise RuntimeError("generic_listing needs a link_pattern in sources.toml")
    return [Candidate(url=u, source_id=src.id, title=t, listed_date=d,
                      date_basis="listing card date" if d else "undated")
            for u, t, d in card_links(_soup(fr), fr.final_url or src.entry_url,
                                      re.compile(src.link_pattern))]


def trendforce_press(src: SourceConfig, f: PoliteFetcher, cov: SourceCoverage,
                     *, oldest_needed: date | None = None) -> list[Candidate]:
    pat = re.compile(r"/presscenter/news/(20\d{6})-\d+\.html$")
    out: dict[str, Candidate] = {}
    read: list[int] = []
    for n in range(1, src.max_listing_pages + 1):
        url = src.entry_url if n == 1 else f"{src.entry_url}?page={n}"
        fr = _get(f, url, cov)
        if fr.state is RetrievalState.BLOCKED or fr.content is None:
            if n == 1:
                raise SourceBlockedError(f"{url}: {fr.note}")
            cov.warnings.append(f"listing page {n}: {fr.note}")
            break
        read.append(n)
        dates: list[date] = []
        for u, t, _ in card_links(_soup(fr), fr.final_url or url, pat):
            m = pat.search(u)
            assert m is not None
            d = datetime.strptime(m.group(1), "%Y%m%d").date()
            dates.append(d)
            out.setdefault(u, Candidate(url=u, source_id=src.id, title=t, listed_date=d,
                                        date_basis="date in the article URL"))
        if oldest_needed is not None and dates and min(dates) < oldest_needed:
            break
    else:
        if oldest_needed is not None and out and min(
                c.listed_date for c in out.values() if c.listed_date) >= oldest_needed:
            cov.truncation = (f"read {len(read)} listing page(s) (max_listing_pages="
                              f"{src.max_listing_pages}); the window may extend past them")
    return list(out.values())


def semianalysis_feed(src: SourceConfig, f: PoliteFetcher,
                      cov: SourceCoverage) -> list[Candidate]:
    feed = src.feed_url
    if not feed:
        fr = _entry(src, f, cov)
        hrefs = [str(a["href"]) for a in _soup(fr).find_all("a", href=True)
                 if isinstance(a, Tag) and "newsletter." in str(a["href"])]
        if not hrefs:
            raise RuntimeError("no newsletter link found on the entry page")
        p = urlparse(hrefs[0])
        feed = f"https://{p.netloc}/feed"
    fr = _get(f, feed, cov)
    if fr.state is RetrievalState.BLOCKED or fr.content is None:
        raise SourceBlockedError(f"{feed}: {fr.note}")
    out: list[Candidate] = []
    for item in _xml(fr).iter("item"):
        link = (item.findtext("link") or "").strip()
        if not link:
            continue
        pub = item.findtext("pubDate")
        d = None
        if pub:
            try:
                d = parsedate_to_datetime(pub).date()
            except (TypeError, ValueError):
                d = None
        out.append(Candidate(url=canon(link), source_id=src.id,
                             title=(item.findtext("title") or "").strip() or None,
                             listed_date=d, date_basis="RSS pubDate" if d else "undated"))
    return out


ADAPTERS: dict[str, Adapter] = {
    "citi_next_data": citi_next_data,
    "jpm_tmt": jpm_tmt,
    "generic_listing": generic_listing,
    "trendforce_press": trendforce_press,
    "semianalysis_feed": semianalysis_feed,
}


# --- one source, with the window applied -------------------------------------------------------

def discover_source(src: SourceConfig, f: PoliteFetcher, store: Store, *, window_from: date,
                    window_to: date) -> Discovery:
    cov = SourceCoverage(source_id=src.id, publisher=src.publisher, channel=src.channel,
                         method=METHOD.get(src.adapter, src.adapter),
                         checked_at=datetime.now(tz=UTC))
    adapter = ADAPTERS.get(src.adapter)
    if adapter is None:
        cov.status = "ERROR"
        cov.errors.append(f"unknown adapter {src.adapter!r} in sources.toml")
        return Discovery(cov, [])
    try:
        if adapter is trendforce_press:
            raw = trendforce_press(src, f, cov, oldest_needed=window_from)
        else:
            raw = adapter(src, f, cov)
    except SourceBlockedError as exc:
        cov.status = "BLOCKED"
        cov.errors.append(str(exc))
        if src.expect_blocked:
            cov.warnings.append("standing access limitation recorded in sources.toml — this "
                                "channel refuses the honest research User-Agent; it is reported "
                                "every run, never bypassed")
        return Discovery(cov, [])
    except Exception as exc:  # noqa: BLE001 — a broken adapter is an ERROR row, not a crash
        cov.status = "ERROR"
        cov.errors.append(f"{type(exc).__name__}: {str(exc)[:240]}")
        return Discovery(cov, [])
    if src.expect_blocked:
        cov.warnings.append("this channel is marked expect_blocked in sources.toml but answered "
                            "— update the config")

    uniq: dict[str, Candidate] = {}
    for c in raw:
        uniq.setdefault(canon(c.url), c)
    cov.discovered = len(uniq)
    undated_seen = 0
    checks = 0
    for url, c in uniq.items():
        c.url = url
        if c.listed_date is None and c.lastmod is not None and c.lastmod < window_from:
            c.status, c.note = "OUT_OF_WINDOW", f"modified {c.lastmod} — before the window"
            cov.skipped_out_of_window += 1
            continue
        if c.listed_date is None:
            undated_seen += 1
            if checks >= src.max_date_checks:
                c.status, c.note = "UNDATED", "date check not run (per-source cap reached)"
                cov.undated += 1
                continue
            checks += 1
            fr = f.fetch(url)
            if fr.state is RetrievalState.BLOCKED or fr.text is None:
                c.status, c.note = "INACCESSIBLE", fr.note
                cov.inaccessible += 1
                continue
            doc = parse_document(fr.text, url, fr.final_url)
            if doc.published_at is None:
                mod = doc.modified_at.date() if doc.modified_at else None
                if mod is not None and mod < window_from:
                    # published no later than its last modification: certainly before the window
                    c.status = "OUT_OF_WINDOW"
                    c.note = (f"the page states no publication date; last modified {mod} "
                              f"({doc.modified_source}) — published no later than that, so "
                              f"before the window")
                    cov.skipped_out_of_window += 1
                    continue
                c.status = "UNDATED"
                c.note = ("the page states no publication date"
                          + (f"; last modified {mod} — it may be new" if mod else "")
                          + " — not placed in any window: VERIFY its date, then analyse it with "
                            "`article --url <url> --published <verified date>`")
                cov.undated += 1
                continue
            c.listed_date = doc.published_at.date()
            c.date_basis = f"article page metadata ({doc.published_source})"
        assert c.listed_date is not None
        if not window_from <= c.listed_date <= window_to:
            c.status = "OUT_OF_WINDOW"
            cov.skipped_out_of_window += 1
            continue
        cov.in_window += 1
        # a URL a scan already tried is KNOWN only when that try finished it: a fetch that timed
        # out or found no body leaves an article row (a BLOCKED record), never a handled one —
        # the article row decides only for a URL no scan has tried (an `article --url` upload)
        k = store.candidate(url)
        if (k[0] in DONE_STATES) if k is not None else store.article_by_url(url) is not None:
            c.status, c.note = "KNOWN", "already in the registry — not re-counted"
            cov.already_known += 1
            continue
        c.status = "IN_WINDOW"
        cov.new += 1
    if undated_seen > checks:
        cov.truncation = ((cov.truncation + "; ") if cov.truncation else "") + (
            f"date-checked {checks} of {undated_seen} undated candidates (cap "
            f"max_date_checks={src.max_date_checks}); the rest are counted UNDATED")
    if cov.undated:
        cov.warnings.append(f"{cov.undated} candidate(s) carry no publication date the source "
                            f"states — counted UNDATED, never placed in a window; listed on "
                            f"the dashboard for date verification (`article --url <url> "
                            f"--published <verified date>`)")
    cov.status = "PARTIAL" if (cov.inaccessible or cov.errors) else "OK"
    return Discovery(cov, list(uniq.values()))


#: Candidate states that mean "already handled" — a re-discovered URL in one of these is KNOWN.
DONE_STATES = frozenset({"PROCESSED", "PARTIAL_PROCESSED", "ALREADY_INGESTED",
                         "DUPLICATE_CONTENT"})
