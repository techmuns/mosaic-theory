"""Manual-document ingestion — a supplied PDF / HTML / Markdown / text report enters the SAME
pipeline, registry and dashboard as an automatically retrieved article.

The documents read here are SYNTHETIC test fixtures (`synthetic_documents/`): invented content,
every page bannered "[SYNTHETIC TEST FIXTURE …]", printed to real PDF bytes by a real PDF engine.
They stand in for licensed documents this build cannot obtain — a SemiAnalysis paid post, a
Morgan Stanley report — and are NEVER presented as research by any publisher. The extractions
below are hypothetical and built from the REAL extraction types, so a schema change breaks them
loudly. The real end-to-end runs on public PDFs are in the record, not in CI.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import (
    FIXTURES,
    Hypo,
    claim,
    extraction,
    fetched,
    hyp,
    ingest,
    make_pipeline,
    table_counts,
)
from vinci.theme_intelligence.config import load_sources
from vinci.theme_intelligence.documents import Declared, DocumentError, read_document
from vinci.theme_intelligence.extract import Extraction
from vinci.theme_intelligence.ingest import containment, ingest_file, shingles
from vinci.theme_intelligence.parse import ParsedDocument
from vinci.theme_intelligence.pipeline import ArticleResult, Pipeline
from vinci.theme_intelligence.schemas import (
    ChangeClass,
    FieldStatus,
    HealthStatus,
    RetrievalState,
    SourceHealthCheck,
)

SYN = FIXTURES / "synthetic_documents"
SA_FULL = SYN / "semianalysis_full_synthetic.pdf"
SA_PREVIEW = SYN / "semianalysis_preview_synthetic.txt"
MS_PDF = SYN / "ms_report_synthetic.pdf"
MS_HTML = SYN / "ms_report_synthetic.html"
SCANNED = SYN / "scanned_page_synthetic.pdf"
UNDATED = SYN / "undated_synthetic.pdf"
SA_TITLE = "Synthetic Memory Note: Inference Keeps Memory Tight"
PREVIEW_URL = "https://example.test/synthetic/semianalysis/inference-keeps-memory-tight"
AS_OF = date(2026, 10, 11)
MEMORY = "ai_infrastructure.memory"
GRID = "ai_infrastructure.power_grid"


class LiveNetworkError(BaseException):
    """A BaseException on purpose: a broad `except Exception` must not swallow it."""


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test here may reach a real host — manual ingestion needs none."""
    import httpx

    def refuse(self: Any, request: Any) -> Any:
        raise LiveNetworkError(f"live network request in an offline test: {request.url}")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", refuse)


@pytest.fixture()
def pipe(tmp_path: Path) -> Pipeline:
    p = make_pipeline(tmp_path)
    p.start_run("ingest", as_of=AS_OF)
    return p


def _ok(ext: dict[str, Any]) -> dict[str, Any]:
    Extraction.model_validate(ext)  # fixtures are the REAL type — fail loud on drift
    return ext


# --- hypothetical extractions over the synthetic documents ---------------------------------------

PREVIEW_QUOTE = ("Synthetic memory demand keeps rising as inference workloads scale across "
                 "hyperscale clusters")


def _memory_hyp(supporting: list[str]) -> dict[str, Any]:
    return hyp("h1", "Inference demand keeps memory supply tight", node=MEMORY,
               mechanism="supply_constraint", geography="Global", supporting=supporting)


def _preview_extraction() -> dict[str, Any]:
    c1 = claim("c1", "b001", PREVIEW_QUOTE, "Memory demand keeps rising with inference",
               kind="assertion")
    return _ok(extraction([c1], [_memory_hyp(["c1"])]))


def _full_extraction() -> dict[str, Any]:
    c1 = claim("c1", "b005", PREVIEW_QUOTE, "Memory demand keeps rising with inference",
               kind="assertion")
    c2 = claim("c2", "b007", "Conventional DRAM contract prices are projected to rise 14% QoQ "
                             "in 4Q26", "Conventional DRAM contract prices +14% QoQ in 4Q26",
               kind="forecast", epistemic="forecast", metric="conventional DRAM contract price "
               "change", value=14, value_text="14%", unit="%", period="4Q26")
    c3 = claim("c3", "b008", "HBM shipments are projected to grow 35% YoY in 2026",
               "HBM shipments +35% YoY in 2026", kind="forecast", epistemic="forecast",
               metric="HBM shipment growth", value=35, value_text="35%", unit="%",
               period="2026")
    return _ok(extraction([c1, c2, c3], [_memory_hyp(["c1", "c2", "c3"])]))


def _ms_extraction(*, table_block: str = "b008", turbine_block: str = "b009") -> dict[str, Any]:
    c1 = claim("c1", "b006", "Grid interconnection queues reached 2,600 GW in our synthetic "
                             "dataset", "Interconnection queues at 2,600 GW",
               metric="grid interconnection queue", value=2600, value_text="2,600 GW",
               unit="GW")
    c2 = claim("c2", turbine_block, "On-site gas turbine orders are projected to grow 30% in "
                                    "2027", "On-site gas turbine orders +30% in 2027",
               kind="forecast", epistemic="forecast", metric="on-site gas turbine order growth",
               value=30, value_text="30%", unit="%", period="2027")
    c3 = claim("c3", table_block, "3Q26 | $48.3bn | 41%", "AI capex $48.3bn in 3Q26",
               metric="AI capex", value=48.3, value_text="$48.3bn", unit="USD bn",
               period="3Q26")
    h1 = hyp("h1", "AI power demand moves generation on-site", node=GRID,
             mechanism="demand_volume_shift", geography="US", supporting=["c1", "c2", "c3"])
    return _ok(extraction([c1, c2, c3], [h1]))


def _preview_doc() -> ParsedDocument:
    """The SemiAnalysis-style PREVIEW as the automatic feed delivers it: a paid post's free
    paragraphs, recorded PARTIAL — the shape `semianalysis_feed` produces."""
    r = read_document(SA_PREVIEW, Declared(source_id="semianalysis"))
    return replace(r.doc, canonical_url=PREVIEW_URL, title=SA_TITLE,
                   title_source="feed item title (synthetic)",
                   published_at=datetime(2026, 9, 28, 12, 0, tzinfo=UTC),
                   published_raw="2026-09-28", published_source="feed pubDate (synthetic)",
                   published_status=FieldStatus.KNOWN, retrieval_state=RetrievalState.PARTIAL,
                   notes=["SYNTHETIC preview: a paid post's free paragraphs only"])


def _ingest_preview(pipe: Pipeline) -> ArticleResult:
    doc = _preview_doc()
    res = pipe.process_document(doc, fetched(doc, state=RetrievalState.PARTIAL),
                                url=PREVIEW_URL, source_id="semianalysis", as_of=AS_OF,
                                fixture=_preview_extraction())
    assert res.status in ("PROCESSED", "PARTIAL_PROCESSED"), res
    return res


def _sa(**kw: Any) -> Declared:
    return Declared(source_id="semianalysis", llm_permitted=True, **kw)


def _ms(**kw: Any) -> Declared:
    return Declared(source_id="ms_research", **{"llm_permitted": True, **kw})


def _theses(pipe: Pipeline, node: str) -> list[Any]:
    return [t for t in pipe.store.theses() if t.key_node == node]


# --- 1. reading: formats, pages, tables, footnotes, flags, dates ---------------------------------

def test_a_pdf_keeps_pages_tables_footnotes_and_values_as_printed() -> None:
    r = read_document(MS_PDF, Declared(source_id="ms_research"))
    blocks = r.doc.blocks
    assert r.fmt == "pdf" and r.pages == 2 and r.tables == 1
    assert all(b.page in (1, 2) for b in blocks)
    table = [b for b in blocks if b.kind == "table"]
    assert len(table) == 1 and table[0].page == 1
    # every cell as printed, rows in order — units and estimates markers kept
    for cell in ("1Q26 | $41.2bn | 38%", "3Q26 | $48.3bn | 41%", "4Q26E | $52.0bn | 42%"):
        assert cell in table[0].text
    # the table sits where it is printed: after its exhibit heading, before the next paragraph
    kinds = [(b.kind, b.text[:20]) for b in blocks]
    i = next(n for n, b in enumerate(blocks) if b.kind == "table")
    assert blocks[i - 1].kind == "heading" and blocks[i - 1].text.startswith("Exhibit 1")
    assert blocks[i + 1].text.startswith("On-site gas turbine"), kinds
    foot = [b for b in blocks if b.kind == "footnote"]
    assert len(foot) == 1 and foot[0].text.startswith("1 Synthetic interconnection data")
    risks = [b for b in blocks if b.text == "Risks"]
    assert risks and risks[0].kind == "heading" and risks[0].page == 2
    assert any("2,600 GW" in b.text and "48 months" in b.text for b in blocks)
    assert r.doc.retrieval_state is RetrievalState.FULL


def test_a_scanned_page_is_flagged_and_makes_the_document_partial() -> None:
    r = read_document(SCANNED, Declared(source_id="semianalysis"))
    assert r.doc.retrieval_state is RetrievalState.PARTIAL
    flagged = [i for i in r.issues if i.startswith("page 2:")]
    assert flagged and "no usable text layer" in flagged[0] and "NOT read" in flagged[0]
    assert any(n.startswith("PARTIAL:") for n in r.doc.notes)
    # page 1's text is still read — the gap is flagged, the rest never discarded
    assert any("rose 9% QoQ in 3Q26" in b.text and b.page == 1 for b in r.doc.blocks)


def test_the_publication_date_comes_from_the_document_never_the_file(tmp_path: Path) -> None:
    """Never from the upload time, the file name or the PDF's file metadata (CreationDate)."""
    named = tmp_path / "2026-09-30 Morgan Stanley report.pdf"
    shutil.copyfile(UNDATED, named)
    r = read_document(named, Declared(source_id="ms_research"))
    assert r.doc.published_at is None and r.doc.published_status is FieldStatus.UNKNOWN
    assert "never used as the publication date" in r.meta["CreationDate"]
    # the operator's statement fills the gap — and says it is the operator's
    r2 = read_document(named, Declared(source_id="ms_research", published=date(2026, 9, 2)))
    assert r2.doc.published_at is not None and r2.doc.published_at.date() == date(2026, 9, 2)
    assert r2.doc.published_source == "operator-stated (the document states no date)"
    # a dated document: the date its own text states
    r3 = read_document(MS_PDF, Declared(source_id="ms_research"))
    assert r3.doc.published_raw == "2026-10-01"
    assert r3.doc.published_source == "the document text (page 1-2)"


def test_an_operator_date_that_disagrees_with_the_document_is_flagged() -> None:
    r = read_document(MS_PDF, Declared(source_id="ms_research", published=date(2026, 9, 15)))
    assert r.doc.published_raw == "2026-10-01"  # the document's own date is used
    assert r.date_disagreement and "2026-09-15" in r.date_disagreement
    assert r.date_disagreement in r.doc.notes


def test_html_keeps_a_table_as_one_block_and_reads_its_printed_date() -> None:
    r = read_document(MS_HTML, Declared(source_id="ms_research"))
    tables = [b for b in r.doc.blocks if b.kind == "table"]
    assert r.tables == 1 and len(tables) == 1
    assert "2Q26 | $44.9bn | 39%" in tables[0].text
    assert r.doc.published_raw == "2026-10-01"
    assert r.doc.published_source == "the document text (opening lines)"


def test_markdown_and_plain_text(tmp_path: Path) -> None:
    md = tmp_path / "note.md"
    md.write_text("---\ntitle: Synthetic Markdown Note\nauthor: Synthetic Writer; Second Writer\n"
                  "date: 2026-08-14\n---\n\n# Ignored As Title\n\nOpening paragraph of the "
                  "synthetic markdown note.\n\n| Year | Units |\n|---|---|\n| 2025 | 1,200 |\n"
                  "| 2026E | 1,450 |\n\n- first point\n- second point\n")
    r = read_document(md, Declared(source_id="manual"))
    assert r.doc.title == "Synthetic Markdown Note"
    assert [a.name for a in r.doc.authors] == ["Synthetic Writer", "Second Writer"]
    assert r.doc.published_raw == "2026-08-14"
    assert r.doc.published_source == "Markdown front matter (date)"
    kinds = [b.kind for b in r.doc.blocks]
    assert kinds.count("table") == 1 and kinds.count("list_item") == 2
    assert "2026E | 1,450" in next(b.text for b in r.doc.blocks if b.kind == "table")
    txt = read_document(SA_PREVIEW, Declared(source_id="semianalysis"))
    assert txt.fmt == "text" and len(txt.doc.blocks) == 2
    assert txt.doc.published_at is None  # nothing in the text states a date


def test_a_byline_is_read_as_the_authors() -> None:
    r = read_document(SA_FULL, Declared(source_id="semianalysis"))
    assert [(a.name, a.source_field) for a in r.doc.authors] == [
        ("Synthetic Analyst One", "a byline in the document text"),
        ("Synthetic Analyst Two", "a byline in the document text")]


def test_unsupported_files_are_refused_plainly(tmp_path: Path) -> None:
    docx = tmp_path / "report.docx"
    docx.write_bytes(b"PK\x03\x04 not really a docx")
    with pytest.raises(DocumentError, match="DOCX is not supported"):
        read_document(docx, Declared(source_id="manual"))
    xls = tmp_path / "model.xlsx"
    xls.write_bytes(b"x")
    with pytest.raises(DocumentError, match="unsupported format"):
        read_document(xls, Declared(source_id="manual"))
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    with pytest.raises(DocumentError, match="empty"):
        read_document(empty, Declared(source_id="manual"))
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4 truncated")
    with pytest.raises(DocumentError, match="cannot be opened"):
        read_document(broken, Declared(source_id="manual"))


# --- 2. Case A: an automatic preview, then the full document --------------------------------------

@pytest.mark.parametrize("stated_url", [True, False], ids=["url-stated", "matched-by-content"])
def test_case_a_a_full_pdf_upgrades_the_partial_preview(pipe: Pipeline, stated_url: bool) -> None:
    pre = _ingest_preview(pipe)
    before = _theses(pipe, MEMORY)
    assert len(before) == 1
    res = ingest_file(pipe, SA_FULL, _sa(url=PREVIEW_URL) if stated_url else _sa(),
                      as_of=AS_OF, fixture=_full_extraction())
    assert res.status == "UPGRADED", res.note
    assert res.article_id == pre.article_id  # the SAME article — never a second one
    assert len(pipe.store.articles()) == 1
    versions = pipe.store.article_versions(pre.article_id)
    assert [v.retrieval_state for v in versions] == [RetrievalState.PARTIAL, RetrievalState.FULL]
    assert versions[0].version_id == pre.version_id  # the earlier version is kept
    # the article's own identity and metadata are kept; the document's are on its record
    art = pipe.store.article(pre.article_id)
    assert art is not None and art.canonical_url == PREVIEW_URL and art.title == SA_TITLE
    after = _theses(pipe, MEMORY)
    assert [t.thesis_id for t in after] == [before[0].thesis_id]  # no duplicate thesis
    links = pipe.store.links(after[0].thesis_id)
    assert len({lk.independence_group for lk in links}) == 1  # one source, counted once
    assert not [lk for lk in links if lk.change_class is ChangeClass.INDEPENDENT_CONFIRMATION]
    # the full text restates the preview's sentence (REPEATED — attribution, not new evidence)
    # and adds two claims (NEW, from an origin already counted)
    v2 = sorted(lk.change_class.value for lk in links if lk.first_version == 2)
    assert v2 == sorted([ChangeClass.REPEATED.value, ChangeClass.NEW.value, ChangeClass.NEW.value])
    rec = pipe.store.document(res.doc_id)
    assert rec is not None and rec.status == "UPGRADED" and rec.article_id == pre.article_id


def test_case_a_the_same_upgrade_imported_again_adds_nothing(pipe: Pipeline,
                                                             tmp_path: Path) -> None:
    _ingest_preview(pipe)
    ingest_file(pipe, SA_FULL, _sa(url=PREVIEW_URL), as_of=AS_OF, fixture=_full_extraction())
    counts = table_counts(pipe)
    copy = tmp_path / "renamed copy of the same report.pdf"
    shutil.copyfile(SA_FULL, copy)
    again = ingest_file(pipe, copy, _sa(), as_of=AS_OF, fixture=_full_extraction())
    assert again.status == "DUPLICATE" and "the same file" in again.note
    assert table_counts(pipe) == counts


# --- 3. Case B: a report from a blocked channel, with no URL -------------------------------------

def test_case_b_an_uploaded_report_is_analysed_while_its_channel_is_blocked(
        pipe: Pipeline) -> None:
    pipe.store.add_health_check(SourceHealthCheck(
        check_id="SH-test-ms", source_id="ms_research", publisher="Morgan Stanley",
        checked_at=datetime(2026, 10, 11, 6, 0, tzinfo=UTC), trigger="manual",
        status=HealthStatus.BLOCKED, reason="connection dropped (test)",
        next_action="manual upload", expect_blocked=True))
    res = ingest_file(pipe, MS_PDF, _ms(), as_of=AS_OF, fixture=_ms_extraction())
    assert res.status == "INGESTED", res.note
    art = pipe.store.article(res.article_id or "")
    assert art is not None
    assert art.canonical_url.startswith("urn:document:sha256:")  # no public URL: content identity
    assert art.publisher == "Morgan Stanley"
    assert art.published_at is not None and art.published_at.date() == date(2026, 10, 1)
    assert art.published_source == "the document text (page 1-2)"
    grid = _theses(pipe, GRID)
    assert len(grid) == 1
    claims = {c.quote: c for c in pipe.store.claims_for_article(art.article_id)}
    table_claim = claims["3Q26 | $48.3bn | 41%"]  # a value read from the TABLE, as printed
    assert table_claim.span_verified and table_claim.value == 48.3
    rec = pipe.store.document(res.doc_id)
    assert rec is not None and rec.pages == 2 and rec.tables == 1 and rec.publisher == \
        "Morgan Stanley"


# --- 4. Case C: the same report twice ------------------------------------------------------------

def test_case_c_html_and_pdf_of_one_report_are_one_article(pipe: Pipeline) -> None:
    first = ingest_file(pipe, MS_PDF, _ms(), as_of=AS_OF, fixture=_ms_extraction())
    assert first.status == "INGESTED"
    counts = table_counts(pipe)
    second = ingest_file(pipe, MS_HTML, _ms(), as_of=AS_OF,
                         fixture=_ms_extraction(table_block="b008", turbine_block="b009"))
    assert second.status == "DUPLICATE", second.note
    assert second.article_id == first.article_id and "another file or format" in second.note
    after = table_counts(pipe)
    assert {k: v for k, v in after.items() if k != "documents"} == \
        {k: v for k, v in counts.items() if k != "documents"}
    assert after["documents"] == counts["documents"] + 1  # the second FILE is recorded


def test_case_c_an_uncertain_match_goes_to_review_never_a_merge(pipe: Pipeline,
                                                                tmp_path: Path) -> None:
    ingest_file(pipe, MS_PDF, _ms(), as_of=AS_OF, fixture=_ms_extraction())
    other = tmp_path / "other.md"
    other.write_text("# Synthetic Utilities Note: AI Power Demand\n\n" + " ".join(
        f"Unrelated synthetic sentence number {i} about a different subject entirely."
        for i in range(12)) + "\n")
    counts = table_counts(pipe)
    res = ingest_file(pipe, other, _ms(), as_of=AS_OF, fixture=_ms_extraction())
    assert res.status == "REVIEW", res.note
    assert "uncertain match" in res.note and "--same-as" in res.note
    after = table_counts(pipe)
    assert after["articles"] == counts["articles"] and after["claims"] == counts["claims"]
    assert any(i.code == "DOCUMENT_REVIEW" for i in pipe.store.issues())
    # the human decides: a new article
    res2 = ingest_file(pipe, other, _ms(), as_of=AS_OF, force_new=True,
                       fixture=_ok(extraction([], [])))
    assert res2.status == "INGESTED" and res2.article_id != res.article_id
    assert table_counts(pipe)["articles"] == counts["articles"] + 1


def test_shingle_containment_is_directional() -> None:
    a = shingles("one two three four five six seven eight nine ten")
    b = shingles("one two three four five six seven eight nine ten eleven twelve thirteen")
    assert containment(a, b) == 1.0 and containment(b, a) < 1.0


# --- 5. Case D: a manual report updates another publisher's thesis -------------------------------

def _grid_article() -> tuple[Hypo, dict[str, Any]]:
    text = ("Large-load interconnection requests in the US rose 110% in 2026, pushing "
            "data-centre developers to plan on-site generation.")
    art = Hypo(slug="grid-requests", publisher="Hypothetical Grid Research",
               published=date(2026, 9, 20), blocks=[("paragraph", text)])
    c1 = claim("c1", "b001", text.rstrip("."), "Large-load requests +110% in 2026",
               metric="large-load interconnection requests", value=110, value_text="110%",
               unit="%", period="2026")
    h1 = hyp("h1", "Grid queues push AI power on-site", node=GRID,
             mechanism="demand_volume_shift", geography="US", supporting=["c1"])
    return art, _ok(extraction([c1], [h1]))


def test_case_d_a_manual_report_strengthens_another_publishers_thesis(pipe: Pipeline) -> None:
    art, ext = _grid_article()
    first = ingest(pipe, art.doc(), ext, as_of=AS_OF, publisher=art.publisher)
    [thesis] = _theses(pipe, GRID)
    res = ingest_file(pipe, MS_PDF, _ms(), as_of=AS_OF, fixture=_ms_extraction())
    assert res.status == "INGESTED"
    assert [t.thesis_id for t in _theses(pipe, GRID)] == [thesis.thesis_id]  # joined, not split
    contributors = {c.article_id for c in pipe.store.contributions(thesis.thesis_id)}
    assert contributors == {first.article_id, res.article_id}
    groups = {lk.independence_group for lk in pipe.store.links(thesis.thesis_id)}
    assert len(groups) == 2  # two publishers, two independent groups
    assert pipe.store.thesis_versions(thesis.thesis_id)[-1].version == 2


def test_the_input_method_never_changes_research_priority(tmp_path: Path) -> None:
    """The same report, once as an automatically retrieved article and once as an upload:
    the same thesis, the same Research Now / Watch / Skip, the same score."""
    web = make_pipeline(tmp_path / "web")
    web.start_run("article", as_of=AS_OF)
    doc = read_document(MS_PDF, _ms(url="https://example.test/synthetic/ms-ai-power")).doc
    ingest(web, doc, _ms_extraction(), as_of=AS_OF, source_id="ms_research")
    up = make_pipeline(tmp_path / "upload")
    up.start_run("ingest", as_of=AS_OF)
    ingest_file(up, MS_PDF, _ms(url="https://example.test/synthetic/ms-ai-power"), as_of=AS_OF,
                fixture=_ms_extraction())

    def prio(p: Pipeline) -> tuple[Any, ...]:
        [t] = _theses(p, GRID)
        v = p.store.thesis_versions(t.thesis_id)[-1]
        pr = v.priority
        return (t.thesis_id, pr.research_action, pr.investment_readiness, pr.rules_fired,
                pr.factors, v.evidence_direction)

    assert prio(web) == prio(up)


# --- 6. licence: unauthorised text is never sent to the LLM, never strengthens a thesis ----------

def test_an_unstated_licence_holds_the_document_and_release_processes_it(pipe: Pipeline) -> None:
    counts = table_counts(pipe)
    held = ingest_file(pipe, MS_PDF, _ms(llm_permitted=None), as_of=AS_OF,
                       fixture=_ms_extraction())
    assert held.status == "HELD" and "not authorised" in held.note
    after = table_counts(pipe)
    assert {k: v for k, v in after.items() if k != "documents"} == \
        {k: v for k, v in counts.items() if k != "documents"}  # nothing analysed, no evidence
    assert not pipe.store.llm_calls(pipe.run.run_id if pipe.run else "")
    rec = pipe.store.document(held.doc_id)
    assert rec is not None and rec.status == "HELD" and rec.stored_path
    stored = pipe.paths.root / rec.stored_path
    assert stat.S_IMODE(stored.stat().st_mode) == 0o600  # owner-only
    assert stat.S_IMODE(stored.parent.stat().st_mode) == 0o700
    # released by the operator: the same file now runs through the pipeline
    rel = ingest_file(pipe, MS_PDF, _ms(llm_permitted=True), as_of=AS_OF,
                      fixture=_ms_extraction())
    assert rel.status == "INGESTED" and rel.doc_id == held.doc_id
    rec2 = pipe.store.document(held.doc_id)
    assert rec2 is not None and rec2.received_at == rec.received_at  # ingestion time kept
    assert [h.split(" UTC ")[1].split(":")[0] for h in rec2.history] == ["HELD", "INGESTED"]


def test_a_refused_licence_holds_and_a_channel_policy_permits(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path / "a")
    pipe.start_run("ingest", as_of=AS_OF)
    res = ingest_file(pipe, MS_PDF, _ms(llm_permitted=False), as_of=AS_OF,
                      fixture=_ms_extraction())
    assert res.status == "HELD" and "NOT permitted" in res.note
    sources = tuple(replace(s, manual_llm_processing="permitted") if s.id == "ms_research"
                    else s for s in load_sources())
    pipe2 = make_pipeline(tmp_path / "b", sources=sources)
    pipe2.start_run("ingest", as_of=AS_OF)
    res2 = ingest_file(pipe2, MS_PDF, _ms(llm_permitted=None), as_of=AS_OF,
                       fixture=_ms_extraction())
    assert res2.status == "INGESTED"


def test_a_document_with_no_readable_text_is_rejected(pipe: Pipeline, tmp_path: Path) -> None:
    tiny = tmp_path / "tiny.txt"
    tiny.write_text("Only five words here.\n")
    res = ingest_file(pipe, tiny, _ms(), as_of=AS_OF, fixture=_ms_extraction())
    assert res.status == "REJECTED" and table_counts(pipe)["articles"] == 0


# --- 7. the inbox -------------------------------------------------------------------------------

def test_the_inbox_imports_and_files_every_document(tmp_path: Path) -> None:
    from vinci.theme_intelligence.__main__ import main

    data, inbox = tmp_path / "data", tmp_path / "inbox"
    inbox.mkdir()
    shutil.copyfile(MS_PDF, inbox / "ms.pdf")
    (inbox / "ms.pdf.meta.json").write_text('{"source": "ms_research"}')  # licence unstated
    shutil.copyfile(UNDATED, inbox / "no-source.pdf")
    (inbox / "model.docx").write_bytes(b"PK\x03\x04")
    rc = main(["--data-dir", str(data), "ingest-inbox", "--inbox", str(inbox), "--as-of",
               AS_OF.isoformat(), "--cache-only", "--no-review"])
    assert rc == 2  # one refusal makes the run PARTIAL
    assert (inbox / "held" / "ms.pdf").exists() and (inbox / "held" / "ms.pdf.meta.json").exists()
    assert (inbox / "rejected" / "model.docx").exists()
    assert (inbox / "no-source.pdf").exists()  # no source stated: left where it is
    assert stat.S_IMODE((inbox / "held").stat().st_mode) == 0o700


# --- 8. privacy: no document under version control except the synthetic fixtures ----------------

def test_no_research_document_is_tracked_by_git() -> None:
    root = Path(__file__).resolve().parents[1]
    if not (root / ".git").exists():
        pytest.skip("not a git checkout")
    try:
        out = subprocess.run(["git", "ls-files", "*.pdf", "*.docx", "*.PDF"], cwd=root,
                             capture_output=True, text=True, check=True, timeout=30,
                             env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.split()
    except (OSError, subprocess.SubprocessError) as exc:
        pytest.skip(f"git unavailable: {exc}")
    allowed = "tests/fixtures/theme_intelligence/synthetic_documents/"
    assert [p for p in out if not p.startswith(allowed)] == []
    ignored = subprocess.run(["git", "check-ignore", "-q", "data/theme_intelligence/x/documents/"
                              "a.pdf"], cwd=root, timeout=30)
    assert ignored.returncode == 0  # the private document store is git-ignored


# --- 9. same-article continuity: positive pin above (Case A); the negative pins ----------------

def _two_version_case(pipe: Pipeline, v1_text: str, v2_text: str) -> list[Any]:
    """One HYPOTHETICAL article read twice (a revised body under one URL), one memory thesis
    per version, each supported by the version's single claim."""
    for text in (v1_text, v2_text):
        art = Hypo(slug="memory-revision", publisher="Hypothetical Memory Research",
                   published=date(2026, 9, 28), blocks=[("paragraph", text)])
        ext = _ok(extraction([claim("c1", "b001", text.rstrip("."), text[:50],
                                    kind="assertion")], [_memory_hyp(["c1"])]))
        ingest(pipe, art.doc(), ext, as_of=AS_OF, publisher=art.publisher)
    return _theses(pipe, MEMORY)


def test_a_revision_naming_a_disjoint_segment_stays_a_separate_thesis(pipe: Pipeline) -> None:
    ts = _two_version_case(pipe, "NAND contract prices keep climbing on enterprise demand.",
                           "DRAM contract prices keep climbing on inference demand.")
    assert sorted(t.key_segment for t in ts) == ["dram_hbm", "nand_ssd"]


def test_one_versions_nested_segment_hypotheses_are_unchanged(pipe: Pipeline) -> None:
    """The rule reads only EARLIER versions' theses: within one version, two hypotheses that
    differ by a nested segment are what they were before it (two theses)."""
    t1 = "Memory makers keep supply disciplined into next year."
    t2 = "DRAM contract prices keep climbing on inference demand."
    art = Hypo(slug="one-version", publisher="Hypothetical Memory Research",
               published=date(2026, 9, 28), blocks=[("paragraph", t1), ("paragraph", t2)])
    h2 = hyp("h2", "DRAM tightness", node=MEMORY, mechanism="supply_constraint",
             geography="Global", supporting=["c2"])
    ext = _ok(extraction([claim("c1", "b001", t1.rstrip("."), t1[:40], kind="assertion"),
                          claim("c2", "b002", t2.rstrip("."), t2[:40], kind="assertion")],
                         [_memory_hyp(["c1"]), h2]))
    ingest(pipe, art.doc(), ext, as_of=AS_OF, publisher=art.publisher)
    assert sorted(t.key_segment for t in _theses(pipe, MEMORY)) == ["", "dram_hbm"]
    assert not [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_VERSION"]


def test_case_a_records_why_the_thesis_was_continued(pipe: Pipeline) -> None:
    _ingest_preview(pipe)
    ingest_file(pipe, SA_FULL, _sa(url=PREVIEW_URL), as_of=AS_OF, fixture=_full_extraction())
    notes = [i for i in pipe.store.issues() if i.code == "SAME_ARTICLE_VERSION"]
    assert len(notes) == 1 and "dram_hbm" in notes[0].detail
