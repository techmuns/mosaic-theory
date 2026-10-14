"""Publication dates are never conflated — each article VERSION keeps the date its own document
states, and where it was read; the card's sources table shows every version's date when they
differ; a difference is recorded with its explanation, or flagged for review.

Observed 2026-10-11 (Citi LatAm, real run): the web page is dated 2026-09-14, the report PDF it
links states 2026-09-10. The article kept the page's date and the PDF's date survived only in a
free-text note — the version carried no date of its own.

The documents here are SYNTHETIC fixtures (the ingestion tests' SemiAnalysis-style preview and
full PDF; the PDF states 2026-09-28); the page date is varied to exercise each case.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from tests.test_theme_intelligence_ingestion import (
    AS_OF,
    PREVIEW_URL,
    SA_FULL,
    _full_extraction,
    _preview_doc,
    _preview_extraction,
    _sa,
    _theses,
)
from tests.theme_intelligence_support import fetched, make_pipeline
from vinci.theme_intelligence.cards import render_html, render_markdown
from vinci.theme_intelligence.ingest import REPORT_BEFORE_PAGE_DAYS, ingest_file
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import card_context, research_intake
from vinci.theme_intelligence.schemas import IssueSeverity, RetrievalState

REPORT_DATE = date(2026, 9, 28)  # what the synthetic full PDF states on its first page
MEMORY = "ai_infrastructure.memory"


@pytest.fixture()
def pipe(tmp_path: Path) -> Pipeline:
    p = make_pipeline(tmp_path)
    p.start_run("ingest", as_of=AS_OF)
    return p


def _page_then_report(pipe: Pipeline, page_date: date) -> str:
    doc = replace(_preview_doc(), published_at=datetime(page_date.year, page_date.month,
                                                        page_date.day, 12, tzinfo=UTC),
                  published_raw=page_date.isoformat())
    as_of = max(AS_OF, page_date)  # never a lookahead
    pre = pipe.process_document(doc, fetched(doc, state=RetrievalState.PARTIAL),
                                url=PREVIEW_URL, source_id="semianalysis", as_of=as_of,
                                fixture=_preview_extraction())
    res = ingest_file(pipe, SA_FULL, _sa(url=PREVIEW_URL), as_of=as_of,
                      fixture=_full_extraction())
    assert res.status == "UPGRADED" and res.article_id == pre.article_id, res.note
    return str(pre.article_id)


def _date_issues(pipe: Pipeline, aid: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for i in pipe.store.issues():
        if i.ref_id == aid and i.code in ("VERSION_DATES_DIFFER", "PUBLICATION_DATE_CONFLICT"):
            out.setdefault(i.code, []).append(f"{i.severity.value}: {i.detail}")
    return out


def test_each_version_keeps_its_own_documents_date_and_where_it_was_read(pipe: Pipeline) -> None:
    aid = _page_then_report(pipe, date(2026, 10, 2))
    art = pipe.store.article(aid)
    assert art is not None and art.published_at is not None
    assert art.published_at.date() == date(2026, 10, 2)  # the article's own date is kept
    v1, v2 = pipe.store.article_versions(aid)
    assert (v1.document_date, v1.document_date_source) == (date(2026, 10, 2),
                                                           "feed pubDate (synthetic)")
    assert (v2.document_date, v2.document_date_source) == (REPORT_DATE,
                                                           "the document text (page 1-2)")


def test_a_report_dated_shortly_before_its_page_is_recorded_not_flagged(pipe: Pipeline) -> None:
    aid = _page_then_report(pipe, date(2026, 10, 2))  # the page 4 days after the report
    issues = _date_issues(pipe, aid)
    assert list(issues) == ["VERSION_DATES_DIFFER"] and issues["VERSION_DATES_DIFFER"][0] \
        .startswith(IssueSeverity.INFO.value)
    assert "2026-10-02" in issues["VERSION_DATES_DIFFER"][0]
    assert "2026-09-28" in issues["VERSION_DATES_DIFFER"][0]


@pytest.mark.parametrize("page_date", [date(2026, 9, 20),  # the report AFTER its page
                                       REPORT_DATE + timedelta(days=REPORT_BEFORE_PAGE_DAYS + 1)],
                         ids=["report-after-page", "too-far-apart"])
def test_an_unexplained_date_difference_is_flagged_for_review(pipe: Pipeline,
                                                              page_date: date) -> None:
    aid = _page_then_report(pipe, page_date)
    issues = _date_issues(pipe, aid)
    assert list(issues) == ["PUBLICATION_DATE_CONFLICT"]
    assert issues["PUBLICATION_DATE_CONFLICT"][0].startswith(IssueSeverity.WARN.value)
    assert pipe.run is not None
    intake = research_intake(pipe.store, pipe.run, [pipe.run], {"sources": []})
    assert any(aid in line and page_date.isoformat() in line
               for line in intake["needs_metadata"]["items"])


def test_the_same_date_on_both_versions_records_nothing(pipe: Pipeline) -> None:
    aid = _page_then_report(pipe, REPORT_DATE)
    assert _date_issues(pipe, aid) == {}
    t = _theses(pipe, MEMORY)[0]
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None and all(s.version_dates == () for s in v.content.s09_sources)


def test_the_card_shows_both_dates_with_their_provenance(pipe: Pipeline) -> None:
    """End to end — registry → card → rendered HTML and Markdown."""
    aid = _page_then_report(pipe, date(2026, 10, 2))
    t = _theses(pipe, MEMORY)[0]
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    src = next(s for s in v.content.s09_sources if s.article_id == aid)
    assert len(src.version_dates) == 2
    assert "2026-10-02" in src.version_dates[0] and "feed pubDate" in src.version_dates[0]
    assert "2026-09-28" in src.version_dates[1] and "page 1-2" in src.version_dates[1]
    rc = card_context(pipe.store, t, v, generated="t")
    table = render_html(v.content, rc).split('data-field="s09_sources"', 1)[1] \
        .split("Version history", 1)[0]
    md = render_markdown(v.content, rc)
    for shown in (table, md):
        assert "2026-10-02" in shown and "2026-09-28" in shown and "page 1-2" in shown


# --- one kind of instant (code review of PR #703, 2026-10-14) -----------------------------------

def test_every_publication_instant_is_timezone_aware_so_two_sources_never_crash_a_render(
        tmp_path: Path) -> None:
    """A date-only stamp (Citi's Next.js publishDate "2026-07-01") parsed NAIVE, every other
    source AWARE: once one thesis cited both, `write_desk` raised "can't compare offset-naive and
    offset-aware datetimes" — and every later render with it. 14 local registries already held
    such rows. Now the parser, the listing / declared dates and the stored records are aware.
    NEGATIVE pin: an aware stamp keeps its own offset."""
    from bs4 import BeautifulSoup  # noqa: F401  (the render below writes real pages)

    from tests.test_theme_intelligence_corrections import CITI_URL
    from tests.theme_intelligence_support import FIXTURES, Hypo, claim, extraction, hyp, ingest
    from vinci.theme_intelligence.parse import parse_document, parse_iso, parse_text_date
    from vinci.theme_intelligence.report import write_run_outputs
    from vinci.theme_intelligence.schemas import Article, RunStatus

    citi = parse_document((FIXTURES / "citi_page_data.html").read_text(), CITI_URL, CITI_URL)
    assert citi.published_at == datetime(2026, 7, 1, tzinfo=UTC)
    assert parse_text_date("Oct 2, 2026") == datetime(2026, 10, 2, tzinfo=UTC)
    assert parse_iso("2026-10-02T07:00:00") == datetime(2026, 10, 2, 7, tzinfo=UTC)
    plus8 = parse_iso("2026-10-15T07:00:00+08:00")
    assert plus8 is not None and plus8.utcoffset() == timedelta(hours=8)
    # end to end: one thesis cites a date-only (formerly naive) source and an aware one
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("ingest", as_of=date(2026, 10, 14))
    for slug, when in (("naive", datetime(2026, 9, 1)),
                       ("aware", datetime(2026, 9, 20, tzinfo=UTC))):
        art = Hypo(slug, "Test Publisher", date(2026, 9, 1), [
            ("paragraph", f"DRAM contract prices rose 9% in 3Q26 ({slug}).")])
        doc = art.doc()
        doc.published_at = when  # the shape the date-only parser produced
        ingest(pipe, doc, extraction(
            [claim("c1", "b001", f"DRAM contract prices rose 9% in 3Q26 ({slug})",
                   "DRAM prices rose 9%", value=9, value_text="9%", unit="%", period="3Q26")],
            [hyp("h1", "DRAM prices are rising", node=MEMORY, mechanism="pricing_cycle",
                 supporting=["c1"])]), as_of=date(2026, 10, 14), publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    assert t.current_version == 2  # both sources on one thesis
    out = Path(write_run_outputs(pipe.store, run.run_id, tmp_path / "out")["dir"])
    assert (out / "theses" / f"{t.thesis_id}.html").exists()
    # a record stored naive by the earlier parser reads back aware
    stored = pipe.store.articles()[0].model_dump(mode="json")
    legacy = Article.model_validate({**stored, "published_at": "2026-07-01T00:00:00"})
    assert legacy.published_at == datetime(2026, 7, 1, tzinfo=UTC)
