"""Group 7 of the verified review leads (`docs/records/2026-10-14-theme-intelligence-unverified-
leads-verified.md`) — the documents as read, and the files the answers are cached in:

- U30 the readers: (a) each line of a two-column PDF ran across both columns, interleaving their
  sentences; (b) "Microsoft Office User" and "2030" were read as authors; (c) a footer's
  "subscribe to read" marked a full page PARTIAL; (d) a table cell repeating an earlier value was
  dropped, shifting its row; (e) "AI-" + "driven" was joined "AIdriven"; (f) `og:title` was cut at
  its first dash; (g) a line repeated on ONE page was dropped from every page as a running header;
- U15 a report linked from a page, on a retired channel's host, was fetched and stored; a replay
  of an upload from a since-retired channel was refused, so it stayed pending for ever;
- U22 a cache file torn by a kill raised JSONDecodeError on every later run.

The PDFs are the SYNTHETIC fixtures (`synthetic_documents/README.md`); the web pages are
HYPOTHETICAL and labelled.
"""

from __future__ import annotations

import os
import re
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_theme_intelligence_enrichment import StandIn
from tests.test_theme_intelligence_enrichment import _memory_thesis as _thesis
from tests.test_theme_intelligence_ingestion import _ms_extraction
from tests.test_theme_intelligence_long_articles import LONG, FakeLlm, _extract, _pass1
from tests.test_theme_intelligence_publishers import (
    PAGE,
    PAGE_EXT,
    REPORT,
    REPORT_EXT,
    SYN_PDF,
    Fetcher,
    _pipe,
    citi_shaped,
)
from tests.test_theme_intelligence_review_carry import FakeReviewer
from tests.test_theme_intelligence_robots import Web, _fetcher
from tests.theme_intelligence_support import FIXTURES, JPM_DIR, FrozenSecHttp, make_pipeline
from vinci.theme_intelligence import config, enrich
from vinci.theme_intelligence.cachefile import read_json, write_json
from vinci.theme_intelligence.completeness import run_completeness, scan_article
from vinci.theme_intelligence.config import RetiredSource, load_sources, load_taxonomy
from vinci.theme_intelligence.documents import Declared, read_document
from vinci.theme_intelligence.extract import Extraction, _answer_named, marker_holds
from vinci.theme_intelligence.ingest import InactiveSourceError, ingest_file
from vinci.theme_intelligence.parse import parse_document
from vinci.theme_intelligence.schemas import RetrievalState
from vinci.theme_intelligence.securities import SecResolver
from vinci.theme_intelligence.verify import review_card

SYN = FIXTURES / "synthetic_documents"
AS_OF = date(2026, 10, 16)
URL = "https://example.test/hypothetical/group-7-page"


def _read(name: str) -> Any:
    return read_document(SYN / name, Declared(source_id="ms_research"))


# --- U30a: two columns -------------------------------------------------------------------------

def test_a_two_column_page_is_read_one_column_at_a_time() -> None:
    paras = [b.text for b in _read("two_column_synthetic.pdf").doc.blocks
             if b.kind == "paragraph" and "column paragraph" in b.text]
    assert [p.split(":")[0] for p in paras] == [  # main: two blocks, each mixing both columns
        "Left column paragraph one", "Left column paragraph two",
        "Right column paragraph one", "Right column paragraph two"]
    assert all(("Left" in p) != ("Right" in p) for p in paras)
    assert paras[2].endswith("stretched beyond two years.")  # each read through to its end


def test_a_bullet_or_a_page_number_beside_its_line_is_no_gutter() -> None:
    """NEGATIVE — the two real shapes that fooled a looser rule on a 60-page Citi report (read
    2026-10-16): a contents page, each title then its page number at the right edge, and a list
    set right of a margin, each bullet 14pt before its text. Split, the numbers left their
    titles and the bullets became blocks of their own ("• • • •")."""
    blocks = _read("two_column_synthetic.pdf").doc.blocks
    contents = next(b.text for b in blocks if b.page == 2 and b.kind == "paragraph")
    assert "Synthetic Grid Bottlenecks 18 Synthetic Transformers 19" in contents
    items = next(b.text for b in blocks if b.page == 3 and b.kind == "paragraph")
    assert items.startswith("• Synthetic lead times: two-year backlogs. • Synthetic custom")


def test_a_one_column_page_is_read_as_before() -> None:
    """NEGATIVE: a page with no gutter is untouched — every paragraph whole, in order."""
    paras = [b.text for b in _read("semianalysis_full_synthetic.pdf").doc.blocks
             if b.kind == "paragraph"]
    assert paras[3].startswith("Synthetic memory demand keeps rising")
    assert paras[-1].startswith("The main risk to this view") and paras[-1].endswith(
        "within two quarters.")


# --- U30b / U30e / U30g: an office suite's export ----------------------------------------------

def test_an_authoring_tools_placeholder_and_a_sentence_opening_by_are_no_authors() -> None:
    r = _read("office_export_synthetic.pdf")
    assert r.meta["Author"] == "Microsoft Office User"  # the fixture carries the placeholder
    assert any(b.text.startswith("By 2030, synthetic") for b in r.doc.blocks)
    assert r.doc.authors == ()  # main: "Microsoft Office User", "2030" and two clauses


@pytest.mark.parametrize(("line", "names"), [
    ("By Émile Durand and Jane Doe", ["Émile Durand", "Jane Doe"]),  # review of #725: ASCII-only
    ("By Ángel Ruiz", ["Ángel Ruiz"]),
    ("By Ursula von der Leyen", ["Ursula von der Leyen"]),
    ("By 2030, synthetic demand doubles", []),  # NEGATIVE: still no one
])
def test_a_byline_name_may_begin_with_any_capital_letter(line: str, names: list[str]) -> None:
    from vinci.theme_intelligence.documents import _byline

    assert [a.name for a in _byline([line])] == names


def test_a_real_byline_and_real_metadata_are_still_read() -> None:
    """POSITIVE: a byline of names, and a person in the Author field."""
    assert [a.name for a in _read("semianalysis_full_synthetic.pdf").doc.authors] == [
        "Synthetic Analyst One", "Synthetic Analyst Two"]
    assert [a.name for a in _read("glyph_mixed_synthetic.pdf").doc.authors] == [
        "Synthetic Strategist"]


def test_a_hyphen_after_a_capital_is_a_compound_after_a_lowercase_letter_a_split_word() -> None:
    text = " ".join(b.text for b in _read("office_export_synthetic.pdf").doc.blocks)
    assert "an AI-driven build-out" in text and "AIdriven" not in text  # main: "AIdriven"
    assert "the signal from" in text and "sig-nal" not in text  # NEGATIVE: still joined


def test_a_line_repeated_on_one_page_is_text_and_a_footer_on_every_page_is_chrome() -> None:
    blocks = _read("office_export_synthetic.pdf").doc.blocks
    quote = [b.page for b in blocks if b.text == "Grid queues doubled in two synthetic years."]
    assert quote == [2, 2]  # main: dropped from the document as a "running header"
    assert not any("internal draft" in b.text for b in blocks)  # POSITIVE: on 3 of 3 pages


# --- U30c / U30d / U30f: web pages -------------------------------------------------------------

BODY = "".join(f"<p>[HYPOTHETICAL] Paragraph {i}: an invented sentence standing in for the body "
               f"of a research article, long enough to count as paragraph text when the parser "
               f"scores the container that holds it.</p>" for i in range(8))


def _page(*, head: str = "", article: str = "", after: str = "") -> str:
    return (f"<html><head><title>Hypothetical page</title>{head}</head><body><article>"
            f"<h1>Hypothetical page</h1><p>October 14, 2026</p>{BODY}{article}</article>"
            f"{after}</body></html>")


@pytest.mark.parametrize("footer", [
    "<footer><p>Subscribe to read our hypothetical newsletter.</p></footer>",
    "<div class='site-footer'><p>Subscribe to read our hypothetical newsletter.</p></div>"])
def test_a_footers_subscribe_link_leaves_a_full_page_full(footer: str) -> None:
    doc = parse_document(_page(after=footer), URL)
    assert doc.retrieval_state is RetrievalState.FULL, doc.notes  # main: PARTIAL


def test_a_subscriber_notice_on_the_page_itself_still_marks_it_partial() -> None:
    """NEGATIVE: the marker outside the footer — after a long preview — still counts."""
    doc = parse_document(_page(after="<div class='gate'><p>This post is for paid subscribers"
                                     "</p></div>"), URL)
    assert doc.retrieval_state is RetrievalState.PARTIAL


def test_a_table_cell_repeating_a_value_keeps_its_place_in_the_row() -> None:
    table = ("<table><tr><th>Segment</th><th>2025</th><th>2026</th></tr>"
             "<tr><td>Memory</td><td>5%</td><td>5%</td></tr></table>")
    doc = parse_document(_page(article=table), URL)
    texts = [b.text for b in doc.blocks]
    i = texts.index("Segment")
    assert texts[i:i + 6] == ["Segment", "2025", "2026", "Memory", "5%", "5%"]  # main: one 5%


def test_text_repeated_outside_a_table_is_still_read_once() -> None:
    """NEGATIVE: a page repeating its chart description for another layout keeps one copy."""
    alt = "<p>[HYPOTHETICAL] Chart: invented memory prices by quarter, rising in each.</p>"
    doc = parse_document(_page(article=alt + alt), URL)
    assert sum(b.text == alt[3:-4] for b in doc.blocks) == 1


@pytest.mark.parametrize(("og", "title"), [
    ("Hypothetical Note | Example", "Hypothetical Note"),  # the page's own host names the site
    ("Hypothetical Note | Another Desk", "Hypothetical Note | Another Desk"),  # NEGATIVE
])
def test_with_no_site_name_og_title_loses_a_part_naming_the_host(og: str, title: str) -> None:
    """Review of #725: with no og:site_name the " | Site" suffix the old split removed was kept."""
    head = f"<meta property='og:title' content='{og}'>"
    assert parse_document(_page(head=head), URL).title == title  # URL: https://example.test/…


def test_the_chrome_free_copy_is_parsed_only_when_the_page_holds_a_marker(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Review of #725: every full page was parsed twice."""
    from vinci.theme_intelligence import parse

    def never(soup: Any) -> str:
        raise AssertionError("re-parsed a page with no subscriber marker")

    monkeypatch.setattr(parse, "_without_chrome", never)
    assert parse_document(_page(), URL).retrieval_state is RetrievalState.FULL


@pytest.mark.parametrize(("og", "site", "title"), [
    ("Hypothetical Gridlock 2.0 — Solving Invented Bottlenecks", "Hypothetical Bank",
     "Hypothetical Gridlock 2.0 — Solving Invented Bottlenecks"),  # main: "…Gridlock 2.0"
    ("Hypothetical Gridlock 2.0 — Solving Invented Bottlenecks | Hypothetical Bank",
     "Hypothetical Bank", "Hypothetical Gridlock 2.0 — Solving Invented Bottlenecks"),
    ("Hypothetical Note - Part Two", "Hypothetical Bank", "Hypothetical Note - Part Two"),
])
def test_og_title_loses_only_a_trailing_part_that_names_the_site(og: str, site: str,
                                                                  title: str) -> None:
    head = (f"<meta property='og:title' content='{og}'>"
            f"<meta property='og:site_name' content='{site}'>")
    assert parse_document(_page(head=head), URL).title == title


# --- U15: retired channels ---------------------------------------------------------------------

RETIRED_REPORT = "https://business.bofa.com/hypothetical/report-download"


@pytest.mark.parametrize(("report", "fetched"), [(RETIRED_REPORT, False), (REPORT, True)])
def test_a_report_linked_on_a_retired_channels_host_is_never_fetched(
        tmp_path: Path, report: str, fetched: bool) -> None:
    f = Fetcher({PAGE: (citi_shaped(report=report).encode(), "text/html"),
                 report: (SYN_PDF.read_bytes(), "application/pdf")})
    pipe = _pipe(tmp_path, f)
    pipe.process_url(PAGE, source_id="citi_must_c", as_of=AS_OF, fixture=PAGE_EXT,
                     linked_fixture=REPORT_EXT)
    issues = {i.code: i for i in pipe.store.issues()}
    if fetched:  # POSITIVE: a live host's report is read as before
        assert f.calls == [PAGE, report] and len(pipe.store.documents()) == 1
        assert "LINKED_REPORT_RETIRED" not in issues
    else:  # main: fetched and stored as a document of the page's article
        assert f.calls == [PAGE] and pipe.store.documents() == []
        i = issues["LINKED_REPORT_RETIRED"]
        assert "Bank of America" in i.detail and "2026-10-11" in i.detail
        assert "LINKED_REPORT_UPLOAD" not in issues  # never asked for, either


def test_an_upload_from_a_since_retired_channel_replays_and_a_new_one_is_refused(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    desk = replace(next(s for s in load_sources() if s.id == "ms_research"), id="syn_desk",
                   publisher="Synthetic Desk")
    monkeypatch.setattr(config, "load_retired_sources", lambda path=None: ())
    live = make_pipeline(tmp_path / "live", sources=(*load_sources(), desk))
    live.start_run("ingest", as_of=AS_OF)
    first = ingest_file(live, SYN_PDF, Declared(source_id="syn_desk", llm_permitted=True),
                        as_of=AS_OF, fixture=_ms_extraction())
    assert first.status == "INGESTED", first.note
    [rec] = live.store.documents()
    # the channel is retired; a later machine replays what was accepted while it was live
    monkeypatch.setattr(config, "load_retired_sources", lambda path=None: (RetiredSource(
        id="syn_desk", publisher="Synthetic Desk", retired="2026-10-15", reason="test"),))
    later = make_pipeline(tmp_path / "later")
    later.start_run("ingest", as_of=AS_OF)
    with pytest.raises(InactiveSourceError, match="retired on 2026-10-15"):  # NEGATIVE
        ingest_file(later, SYN_PDF, Declared(source_id="syn_desk", llm_permitted=True),
                    as_of=AS_OF, fixture=_ms_extraction())
    out = ingest_file(later, SYN_PDF, Declared.recorded(rec.source_id, rec.declared),
                      as_of=AS_OF, fixture=_ms_extraction(), replay_of=rec)  # main: refused
    assert out.status == "INGESTED", out.note
    [art] = later.store.articles()
    assert art.publisher == "Synthetic Desk"  # attributable to the channel it came from


def test_a_replay_from_a_channel_never_configured_is_still_refused(tmp_path: Path) -> None:
    """NEGATIVE: only a RETIRED channel's history replays — an unknown id is no history."""
    live = make_pipeline(tmp_path / "live")
    live.start_run("ingest", as_of=AS_OF)
    ingest_file(live, SYN_PDF, Declared(source_id="ms_research", llm_permitted=True),
                as_of=AS_OF, fixture=_ms_extraction())
    [rec] = live.store.documents()
    later = make_pipeline(tmp_path / "later")
    later.start_run("ingest", as_of=AS_OF)
    with pytest.raises(InactiveSourceError, match="not an active channel"):
        ingest_file(later, SYN_PDF, Declared.recorded("no_such_desk", rec.declared),
                    as_of=AS_OF, fixture=_ms_extraction(), replay_of=rec)


# --- U22: torn cache files ---------------------------------------------------------------------

def _tear(path: Path) -> None:
    text = path.read_text()
    path.write_text(text[:len(text) // 2])  # what a kill mid-write leaves


def _aside(folder: Path) -> list[Path]:
    return sorted(folder.rglob("*.torn-*"))


def test_a_torn_record_is_set_aside_and_read_as_absent_a_whole_one_is_read(
        tmp_path: Path) -> None:
    whole, torn = tmp_path / "whole.json", tmp_path / "torn.json"
    write_json(whole, {"output": {"a": 1}})
    write_json(torn, {"output": {"a": 1}})
    _tear(torn)
    assert read_json(whole) == {"output": {"a": 1}} and whole.exists()  # NEGATIVE
    with pytest.warns(UserWarning, match="torn cache file was set aside"):
        assert read_json(torn) is None
    [aside] = _aside(tmp_path)
    assert not torn.exists() and aside.read_text() == '{"output": {"a": 1}}'[:10]  # kept


def test_a_torn_file_is_recorded_on_the_run_that_set_it_aside(tmp_path: Path) -> None:
    """Review of #725: a re-paid answer was known only to stderr. NEGATIVE pin: a run that set
    nothing aside records nothing."""
    from vinci.theme_intelligence.schemas import RunStatus

    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    assert not [i for i in pipe.store.issues() if i.code == "CACHE_FILE_TORN"]
    torn = tmp_path / "answer.json"
    write_json(torn, {"output": {"a": 1}})
    _tear(torn)
    pipe.start_run("ingest", as_of=AS_OF)
    with pytest.warns(UserWarning, match="torn cache file"):
        read_json(torn)
    run = pipe.finish_run(RunStatus.SUCCEEDED)
    [i] = [i for i in pipe.store.issues() if i.code == "CACHE_FILE_TORN"]
    assert i.run_id == run.run_id and "answer.json.torn-" in i.detail
    assert any("CACHE_FILE_TORN" in w for w in run.warnings)


def test_a_write_that_fails_leaves_the_earlier_file_whole_and_no_partial_file(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "answer.json"
    write_json(path, {"output": "earlier"})

    def disk_full(fd: int) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "fsync", disk_full)
    with pytest.raises(OSError, match="No space"):
        write_json(path, {"output": "later"})
    assert read_json(path) == {"output": "earlier"} and os.listdir(tmp_path) == ["answer.json"]


def test_a_torn_extraction_answer_is_asked_again_never_a_failure_on_every_run(
        tmp_path: Path) -> None:
    assert not _extract(FakeLlm(_pass1(bad_items=False)), tmp_path).cached
    again = FakeLlm(_pass1(bad_items=False))
    assert _extract(again, tmp_path).cached and again.calls == []  # NEGATIVE: whole → cached
    [answer] = [p for p in (tmp_path / "extract").glob("*.json") if len(p.stem) == 64]
    _tear(answer)
    after = FakeLlm(_pass1(bad_items=False))
    with pytest.warns(UserWarning, match="torn cache file"):
        res = _extract(after, tmp_path)  # main: JSONDecodeError, this run and every later one
    assert not res.cached and after.calls == ["extract"] and len(_aside(tmp_path)) == 1
    xid = res.extraction_id
    _tear(answer)
    with pytest.warns(UserWarning, match="torn cache file"):  # the named-answer reuse path
        assert _answer_named(tmp_path, xid, "claude-opus-4-8", (res.prompt_version,)) is None


def test_a_torn_truncation_marker_is_no_marker(tmp_path: Path) -> None:
    marker = tmp_path / "k.truncated.json"
    write_json(marker, {"usage": {"max_tokens": 16_384}})
    assert marker_holds(marker, None)  # NEGATIVE: a whole marker holds
    _tear(marker)
    with pytest.warns(UserWarning, match="torn cache file"):
        assert not marker_holds(marker, None)  # main: JSONDecodeError


def test_a_torn_completeness_answer_is_asked_again(tmp_path: Path) -> None:
    doc = LONG.doc()

    def complete(client: FakeLlm) -> Any:
        return run_completeness(doc, Extraction.model_validate(_pass1(bad_items=False)),
                                scan_article(doc), publisher="P", as_of="2026-10-02",
                                taxonomy=load_taxonomy(), client=client, cache_dir=tmp_path)

    complete(FakeLlm(_pass1(bad_items=False)))
    again = FakeLlm(_pass1(bad_items=False))
    complete(again)
    assert again.calls == []  # NEGATIVE: whole → cached
    [answer] = (tmp_path / "complete").glob("*.json")
    _tear(answer)
    after = FakeLlm(_pass1(bad_items=False))
    with pytest.warns(UserWarning, match="torn cache file"):
        complete(after)  # main: JSONDecodeError
    assert after.calls == ["complete"] and len(_aside(tmp_path)) == 1


def test_a_torn_enrichment_answer_is_asked_again(tmp_path: Path) -> None:
    pipe, tid = _thesis(tmp_path)
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    resolver = SecResolver(tmp_path / "sec", http=FrozenSecHttp(JPM_DIR))  # type: ignore[arg-type]

    def propose(model: StandIn) -> Any:
        return enrich.enrich_thesis(v.content, version=v.version, area="Technology", groups=[],
                                    client=model, cache_dir=tmp_path / "llm", resolver=resolver,
                                    as_of=AS_OF, run_id="R-t")

    assert not propose(StandIn({"companies": []})).cached
    assert propose(StandIn({"companies": []})).cached  # NEGATIVE
    [answer] = (tmp_path / "llm" / "enrich").glob("*.json")
    _tear(answer)
    model = StandIn({"companies": []})
    with pytest.warns(UserWarning, match="torn cache file"):
        assert not propose(model).cached  # main: JSONDecodeError
    assert len(model.users) == 1


def test_a_torn_card_review_is_asked_again(tmp_path: Path) -> None:
    pipe, tid = _thesis(tmp_path)
    t = pipe.store.thesis(tid)
    assert t is not None
    v = pipe.store.thesis_version(tid, t.current_version)
    assert v is not None
    claims = {c.claim_id: c for a in pipe.store.articles()
              for c in pipe.store.claims_for_article(a.article_id)}

    def review(fake: FakeReviewer) -> Any:
        return review_card(v.content, claims, client=fake, cache_dir=tmp_path / "llm",
                           run_id="R-t")

    assert not review(FakeReviewer({})).cached
    assert review(FakeReviewer({})).cached  # NEGATIVE
    [answer] = (tmp_path / "llm" / "review").glob("*.json")
    _tear(answer)
    fake = FakeReviewer({})
    with pytest.warns(UserWarning, match="torn cache file"):
        assert not review(fake).cached  # main: JSONDecodeError
    assert fake.calls == 1


def test_a_torn_page_record_or_a_body_cut_short_is_fetched_again(tmp_path: Path) -> None:
    page = "<html><body><p>[HYPOTHETICAL] page text</p></body></html>"
    web = Web({"https://pub.test/robots.txt": (200, "User-agent: *\nAllow: /\n"),
               "https://pub.test/note": (200, page)})
    f = _fetcher(tmp_path, web)
    assert f.fetch("https://pub.test/note").content == page.encode()
    asked = web.log.count("https://pub.test/note")
    assert f.fetch("https://pub.test/note").content == page.encode()
    assert web.log.count("https://pub.test/note") == asked  # NEGATIVE: whole → cached
    body, meta = f._paths("https://pub.test/note")
    body.write_bytes(page.encode()[:20])  # the body cut short, its record whole
    assert f.fetch("https://pub.test/note").content == page.encode()  # main: the cut body
    _tear(meta)
    with pytest.warns(UserWarning, match="torn cache file"):
        assert f.fetch("https://pub.test/note").content == page.encode()  # main: raises
    assert web.log.count("https://pub.test/note") == asked + 2


CACHE_MODULES = ("extract", "completeness", "enrich", "verify", "fetch")
_RAW_IO = re.compile(r"\.(write_text|write_bytes)\(|\.read_text\(\)")


def test_the_cache_modules_read_and_write_files_only_through_the_cache_file_helpers() -> None:
    """Every answer, marker and page record is written whole or not at all and a torn one is
    set aside: no cache module touches a file with a bare `write_text` / `write_bytes` /
    `read_text`. (At main 2a794602 it finds 20 sites across the five modules.)"""
    root = Path(__file__).parents[1] / "vinci" / "theme_intelligence"
    raw = {m: _RAW_IO.findall((root / f"{m}.py").read_text()) for m in CACHE_MODULES}
    assert raw == {m: [] for m in CACHE_MODULES}
