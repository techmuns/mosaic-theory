"""Publisher-specific discovery and retrieval — the gaps the source-health checks found
(2026-10-11), each pinned at the shape it was observed in:

- Citi: the article body sits inside `div.template-apply-sidebar`; the noise filter's substring
  match dropped all 7,316 characters of the ETF page (0 words, "parser failure suspected").
  Each Must C page links its full report ("Download Here", ir.citi.com) — read where permitted.
- Nomura: "To read the full report, click here" leads to the client portal — requested, never
  fetched.
- Undated pages (observed on Bank of America's insight pages, a channel since retired, and on
  Nomura): a page's last-modified date bounds it (before the window → out of it), the rest are
  listed for date verification, never silently dropped.
- J.P. Morgan and TrendForce: working adapters, pinned on trimmed copies of their REAL listing
  pages (scripts, styles and images removed; DOM, hrefs and printed text kept — the adapter
  sees identical candidates on the original and the trimmed copy, verified when trimmed).

Page HTML built here is SYNTHETIC: the real class names and link shapes, invented sentences.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import FIXTURES, claim, extraction, hyp
from vinci.theme_intelligence.config import load_sources, load_taxonomy
from vinci.theme_intelligence.discovery import discover_source
from vinci.theme_intelligence.extract import Extraction
from vinci.theme_intelligence.fetch import FetchResult, FetchStats
from vinci.theme_intelligence.health import _UPLOAD
from vinci.theme_intelligence.parse import parse_document
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.schemas import RetrievalState, RunStatus
from vinci.theme_intelligence.securities import SecResolver
from vinci.theme_intelligence.store import Store

LISTINGS = FIXTURES / "listings"
SYN_PDF = FIXTURES / "synthetic_documents" / "ms_report_synthetic.pdf"
AS_OF = date(2026, 10, 11)
PAGE = "https://example.test/synthetic/citi-shaped/must-c-page"
REPORT = "https://example.test/synthetic/citi-shaped/report-download"
PARA = ("Synthetic paragraph {i}: an invented sentence standing in for the article body, long "
        "enough to count as paragraph text for the container scoring rule in the parser.")


class LiveNetworkError(BaseException):
    """A BaseException on purpose: a broad `except Exception` must not swallow it."""


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def refuse(self: Any, request: Any) -> Any:
        raise LiveNetworkError(f"live network request in an offline test: {request.url}")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)


class Fetcher:
    """Serves bytes by URL; anything else is a 403. Records every URL asked for."""

    def __init__(self, pages: dict[str, tuple[bytes, str]]) -> None:
        self.pages = pages
        self.stats = FetchStats()
        self.calls: list[str] = []

    def set_host_floor(self, url: str, seconds: float) -> None:
        pass

    def fetch(self, url: str, *, ttl_s: float | None = None) -> FetchResult:
        self.calls.append(url)
        now = datetime.now(tz=UTC)
        if url not in self.pages:
            return FetchResult(url, None, 403, RetrievalState.BLOCKED, "HTTP 403 (test)", None,
                               None, now, None, None, False, 0.0)
        body, ctype = self.pages[url]
        return FetchResult(url, url, 200, RetrievalState.FULL, "fetched (test)", body, ctype,
                           now, hashlib.sha256(body).hexdigest(), None, False, 0.0)


def _src(sid: str, **kw: Any) -> Any:
    return replace(next(s for s in load_sources() if s.id == sid), **kw)


def _pipe(tmp_path: Path, fetcher: Fetcher, *srcs: Any) -> Pipeline:
    sources = tuple({**{s.id: s for s in load_sources()}, **{s.id: s for s in srcs}}.values())
    p = Pipeline(tmp_path / "ti", sources=sources, taxonomy=load_taxonomy(), client=None,
                 resolver=SecResolver(tmp_path / "sec"), review=False,
                 fetcher=fetcher)  # type: ignore[arg-type]
    p.start_run("article", as_of=AS_OF)
    return p


# --- Citi: the page template named like a sidebar ----------------------------------------------

def citi_shaped(*, link_text: str = "Download Here", report: str = REPORT) -> str:
    """The REAL class chain of citigroup.com/global/insights pages (observed 2026-10-11), with
    invented text: body inside `template-apply-sidebar`, a related-stories block after it."""
    body = "".join(f"<p>{PARA.format(i=i)}</p>" for i in range(8))
    related = "".join(f'<div class="insightsMediaCard insightCard"><a class="linkwrapper" '
                      f'href="/related-{i}"><div class="summary___W_dTb"><p>Related story {i}: '
                      f'a different article teaser that must never be read as this page body '
                      f'text.</p></div></a></div>' for i in range(3))
    return (
        '<html><head><title>Synthetic Citi-shaped page</title><meta property="og:title" '
        'content="Synthetic Citi-shaped page"></head><body class="icgds"><div id="__next">'
        '<div class="InsightDetail lmn-theme-light InsightDetail___tHQhT" id="InsightDetail">'
        '<div class="insight-detail-templates-common-style template-apply-sidebar '
        'NewDefaultInsightsTemplate___p8WIR"><div class="bodyExtension lmn-collapse">'
        '<div class="citigroup-container-sm-center"><h1>Synthetic Citi-shaped page</h1>'
        '<p>April 10, 2026</p><div class="TextBlock"><p>Must C: Synthetic Report Title</p>'
        f'<a href="{report}">{link_text}</a></div>'
        f'<div class="rich-text-wrapper bodyContent">{body}</div></div></div></div>'
        f'<div class="relatedStories___ZUppW"><h2>Related Stories</h2>{related}</div>'
        '</div></div></body></html>')


def test_citi_body_inside_a_sidebar_named_template_is_read() -> None:
    doc = parse_document(citi_shaped(), PAGE)
    assert doc.word_count > 200, doc.notes  # was 0: the whole body dropped as "sidebar"
    texts = " ".join(b.text for b in doc.blocks)
    assert "Synthetic paragraph 7" in texts
    assert "Related story" not in texts  # a real related-content block is still noise
    assert doc.linked_reports == (("Download Here", REPORT),)
    assert doc.retrieval_state is RetrievalState.PARTIAL
    assert any("summarises a fuller report it links to" in n and REPORT in n for n in doc.notes)


def test_a_real_sidebar_holding_a_minority_of_the_text_is_still_dropped() -> None:
    body = "".join(f"<p>{PARA.format(i=i)}</p>" for i in range(6))
    html = (f'<html><body><main><h1>T</h1>{body}<div class="sidebar"><p>Sidebar promo text that '
            f'is long enough to be scored as a paragraph but is not the article itself at '
            f'all.</p></div></main></body></html>')
    doc = parse_document(html, PAGE)
    assert "Sidebar promo" not in " ".join(b.text for b in doc.blocks)
    assert doc.word_count > 100


@pytest.mark.parametrize(("html_link", "expected"), [
    ('<a href="/content/dam/x/quantum-technology.pdf">Download PDF</a>', ()),  # a print copy
    ('<footer><a href="https://www.jpmorgan.com/directdoc/form_crs.pdf">Form CRS</a></footer>',
     ()),  # J.P. Morgan regulatory footer
    ('<p>To read the full report, click</p><a href="https://portal.example.test/pub/1">here</a>',
     (("here", "https://portal.example.test/pub/1"),)),  # Nomura's client-portal link
    ('<a href="https://ir.example.test/r">Download Here</a>',
     (("Download Here", "https://ir.example.test/r"),)),  # Citi's report link
], ids=["print-copy-pdf", "jpm-form-crs", "nomura-click-here", "citi-download-here"])
def test_which_links_are_a_fuller_report(html_link: str, expected: tuple[Any, ...]) -> None:
    """A link is the fuller report only when the page SAYS so — never because a PDF exists
    (the bare-PDF rule marked every J.P. Morgan page partial in the 2026-10-11 corpus check)."""
    body = "".join(f"<p>{PARA.format(i=i)}</p>" for i in range(6))
    doc = parse_document(f"<html><body><main>{body}{html_link}</main></body></html>", PAGE)
    assert doc.linked_reports == expected


# --- linked reports through the pipeline ---------------------------------------------------------

def _ok(ext: dict[str, Any]) -> dict[str, Any]:
    Extraction.model_validate(ext)
    return ext


PAGE_EXT = _ok(extraction([], []))
REPORT_EXT = _ok(extraction(
    [claim("c1", "b009", "On-site gas turbine orders are projected to grow 30% in 2027",
           "On-site gas turbine orders +30% in 2027", kind="forecast", epistemic="forecast",
           metric="on-site gas turbine order growth", value=30, value_text="30%", unit="%",
           period="2027")],
    [hyp("h1", "AI power demand moves generation on-site", node="ai_infrastructure.power_grid",
         mechanism="demand_volume_shift", geography="US", supporting=["c1"])]))


def _citi_fetcher(report: tuple[bytes, str] | None = None) -> Fetcher:
    pages = {PAGE: (citi_shaped().encode(), "text/html")}
    if report is not None:
        pages[REPORT] = report
    return Fetcher(pages)


def test_a_linked_report_is_read_as_a_fuller_version_of_the_same_article(
        tmp_path: Path) -> None:
    f = _citi_fetcher((SYN_PDF.read_bytes(), "application/pdf"))
    pipe = _pipe(tmp_path, f)
    res = pipe.process_url(PAGE, source_id="citi_must_c", as_of=AS_OF, fixture=PAGE_EXT,
                           linked_fixture=REPORT_EXT)
    assert res.status in ("PROCESSED", "PARTIAL_PROCESSED"), res
    assert f.calls == [PAGE, REPORT]  # the page, then its report — nothing else
    versions = pipe.store.article_versions(res.article_id or "")
    assert [v.retrieval_state for v in versions] == [RetrievalState.PARTIAL,
                                                     RetrievalState.FULL]
    assert len(pipe.store.articles()) == 1  # the report is the page's article, not a new one
    [doc] = pipe.store.documents()
    assert doc.status == "UPGRADED" and doc.article_id == res.article_id
    assert REPORT in doc.declared["via"] and "robots.txt obeyed" in doc.declared["via"]
    # provenance says how it arrived — never "the operator states" for an automatic fetch
    assert "own page links to" in (doc.match_basis or "")
    assert "operator" not in (doc.match_basis or "") and doc.filename.startswith("linked-report-")
    quotes = [c.quote for c in pipe.store.claims_for_article(res.article_id or "")]
    assert quotes == ["On-site gas turbine orders are projected to grow 30% in 2027"]
    # the next run reads the page again: the report is not fetched a second time
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.start_run("article", as_of=AS_OF)
    f.calls.clear()
    pipe.process_url(PAGE, source_id="citi_must_c", as_of=AS_OF, fixture=PAGE_EXT,
                     linked_fixture=REPORT_EXT)
    assert REPORT not in f.calls


def test_a_report_that_cannot_be_read_is_listed_for_upload(tmp_path: Path) -> None:
    f = _citi_fetcher()  # the report link answers 403
    pipe = _pipe(tmp_path, f)
    res = pipe.process_url(PAGE, source_id="citi_must_c", as_of=AS_OF, fixture=PAGE_EXT)
    [i] = [i for i in pipe.store.issues() if i.code == "LINKED_REPORT_UPLOAD"]
    assert i.ref_id == res.article_id and REPORT in i.detail and "ingest-file" in i.detail
    assert len(pipe.store.article_versions(res.article_id or "")) == 1
    assert pipe.store.documents() == []


def test_the_per_run_cap_defers_a_linked_report(tmp_path: Path) -> None:
    f = _citi_fetcher((SYN_PDF.read_bytes(), "application/pdf"))
    pipe = _pipe(tmp_path, f, _src("citi_must_c", max_linked_reports=0))
    pipe.process_url(PAGE, source_id="citi_must_c", as_of=AS_OF, fixture=PAGE_EXT)
    assert REPORT not in f.calls
    [i] = [i for i in pipe.store.issues() if i.code == "LINKED_REPORT_UPLOAD"]
    assert "max_linked_reports=0" in i.detail


def test_a_linked_report_estimated_above_the_cost_limit_is_held_and_listed(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A scan never spends past the per-document limit unattended: the report is fetched and
    stored, HELD with its estimate, and listed for a deliberate import."""
    from vinci.theme_intelligence import ingest as ingest_mod

    monkeypatch.setattr(ingest_mod, "DOC_COST_LIMIT_USD", 0.01)
    f = _citi_fetcher((SYN_PDF.read_bytes(), "application/pdf"))
    pipe = _pipe(tmp_path, f)
    res = pipe.process_url(PAGE, source_id="citi_must_c", as_of=AS_OF, fixture=PAGE_EXT,
                           linked_fixture=REPORT_EXT)
    assert len(pipe.store.article_versions(res.article_id or "")) == 1  # not analysed
    [doc] = pipe.store.documents()
    assert doc.status == "HELD" and doc.stored_path
    [i] = [i for i in pipe.store.issues() if i.code == "LINKED_REPORT_UPLOAD"]
    assert "HELD, not analysed" in i.detail and "COST: estimated $" in i.detail


def test_a_request_channel_never_fetches_its_linked_report(tmp_path: Path) -> None:
    """Nomura's full reports sit on its client portal: listed for upload, never fetched."""
    f = _citi_fetcher((SYN_PDF.read_bytes(), "application/pdf"))
    pipe = _pipe(tmp_path, f)
    res = pipe.process_url(PAGE, source_id="nomura_connects", as_of=AS_OF, fixture=PAGE_EXT)
    assert f.calls == [PAGE]
    [i] = [i for i in pipe.store.issues() if i.code == "LINKED_REPORT_UPLOAD"]
    assert i.ref_id == res.article_id and "never to fetch it" in i.detail


def test_the_channel_policies_as_configured() -> None:
    by = {s.id: s for s in load_sources()}
    assert by["citi_must_c"].linked_reports == "fetch"
    assert by["nomura_connects"].linked_reports == "request"
    assert all(by[s].linked_reports == "request" for s in by if s != "citi_must_c")
    assert "ingest-file" in _UPLOAD  # the health hint points at the document route


# --- a page that states no publication date (Nomura's layout) ----------------------------------

def _undated_page(title: str, modified: str | None) -> bytes:
    meta = f'<meta name="last_modified_date" content="{modified}">' if modified else ""
    body = "".join(f"<p>{PARA.format(i=i)}</p>" for i in range(6))
    return (f"<html><head>{meta}</head><body><main><h1>{title}</h1>{body}</main></body></html>"
            ).encode()


def test_an_undated_page_is_bounded_by_its_last_modification(tmp_path: Path) -> None:
    src = _src("nomura_connects", max_listing_pages=1)
    base = "https://www.nomuraconnects.com/focused-thinking-posts"
    listing = (f'<html><body><main><div class="card"><a href="{base}/old-insight">An old '
               f'insight whose title is long enough for the card rule</a></div><div '
               f'class="card"><a href="{base}/recent-insight">A recent insight whose title '
               f'is long enough for the card rule</a></div><div class="card"><a '
               f'href="{base}/bare-insight">A bare insight whose title is long enough for '
               f'the card rule</a></div></main></body></html>').encode()
    f = Fetcher({src.listing_url: (listing, "text/html"),
                 f"{base}/old-insight": (_undated_page("Old", "2025-09-26T10:20:25-04:00"),
                                         "text/html"),
                 f"{base}/recent-insight": (_undated_page("Recent", "2026-10-05T09:00:00-04:00"),
                                            "text/html"),
                 f"{base}/bare-insight": (_undated_page("Bare", None), "text/html")})
    st = Store(tmp_path / "r.db")
    d = discover_source(src, f, st, window_from=date(2026, 10, 2),  # type: ignore[arg-type]
                        window_to=AS_OF)
    by = {c.url.rsplit("/", 1)[-1]: c for c in d.candidates}
    old, recent, bare = by["old-insight"], by["recent-insight"], by["bare-insight"]
    assert old.status == "OUT_OF_WINDOW" and "last modified 2025-09-26" in old.note
    assert recent.status == "UNDATED" and "last modified 2026-10-05" in recent.note
    assert "VERIFY" in recent.note and "--published" in recent.note
    assert bare.status == "UNDATED" and "VERIFY" in bare.note
    assert d.coverage.undated == 2 and d.coverage.skipped_out_of_window == 1


def test_an_operator_verified_date_is_labelled_as_such(tmp_path: Path) -> None:
    url = "https://www.nomuraconnects.com/focused-thinking-posts/recent-insight"
    f = Fetcher({url: (_undated_page("Recent", "2026-10-05T09:00:00-04:00"), "text/html")})
    pipe = _pipe(tmp_path, f)
    res = pipe.process_url(url, source_id="nomura_connects", as_of=AS_OF, fixture=PAGE_EXT,
                           declared_published=date(2026, 10, 3))
    art = pipe.store.article(res.article_id or "")
    assert art is not None and art.published_at is not None
    assert art.published_at.date() == date(2026, 10, 3)
    assert art.published_source == "operator-verified (the page states no date)"


# --- J.P. Morgan and TrendForce: the working adapters, pinned ------------------------------------

def _listing(sid: str, entry: str, fixture: str, tmp_path: Path) -> Any:
    f = Fetcher({entry: ((LISTINGS / fixture).read_bytes(), "text/html")})
    return discover_source(_src(sid), f, Store(tmp_path / "r.db"),  # type: ignore[arg-type]
                           window_from=date(2026, 9, 1), window_to=AS_OF)


def test_jpm_listing_adapter_regression(tmp_path: Path) -> None:
    """Real J.P. Morgan TMT listing as served 2026-10-11 (trimmed): 51 cards, every one titled
    and dated from its OWN card; 5 inside 2026-09-01..2026-10-11; no sitemap fallback needed."""
    d = _listing("jpm_tmt", "https://privatebank.jpmorgan.com/apac/en/insights/markets-and-"
                 "investing/tmt", "jpm_tmt_2026-10-11.html", tmp_path)
    c = d.candidates
    assert len(c) == 51 and all(x.title for x in c) and all(x.listed_date for x in c)
    inw = sorted((x.listed_date, x.url.rsplit("/", 1)[-1]) for x in c if x.status == "IN_WINDOW")
    assert inw == [(date(2026, 9, 3), "toto-i-dont-think-its-the-fed-anymore"),
                   (date(2026, 9, 11), "100-dollar-oil-isnt-as-scary-as-it-used-to-be"),
                   (date(2026, 9, 18), "the-cost-of-capital-is-rising-did-stocks-get-the-memo"),
                   (date(2026, 9, 25), "one-economy-two-markets-one-message"),
                   (date(2026, 10, 2), "a-calm-index-a-restless-market")]
    assert d.coverage.status == "OK" and d.coverage.undated == 0 and not d.coverage.warnings


def test_trendforce_listing_adapter_regression(tmp_path: Path) -> None:
    """Real TrendForce press-news listing page 1 as served 2026-10-11 (trimmed): 5 releases,
    each dated by the date in its own URL."""
    d = _listing("trendforce", "https://www.trendforce.com/presscenter/news",
                 "trendforce_press_news_2026-10-11.html", tmp_path)
    c = d.candidates
    assert len(c) == 5 and all(x.title for x in c)
    for x in c:
        stamp = x.url.rsplit("/", 1)[-1][:8]
        assert x.listed_date == date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:]))
        assert x.date_basis == "date in the article URL"
    assert {x.status for x in c} == {"IN_WINDOW"}
