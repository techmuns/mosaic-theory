"""The J.P. Morgan acceptance corrections and the product redesign (2026-10-12) — PR #703.

1. NUMBERS. A named index carries a number that is part of its NAME ("S&P 500", "Q3"); a figure
   written in words beside digits ("five of the 11") is read as written. Every other number on a
   line is still checked against its cited claims.
2. PRICE CONTEXT. A share-price / index performance line the source states is market context —
   never counter-evidence to an EARNINGS thesis (the Magnificent 7 lagging the index was filed
   against earnings broadening).
3. ANALYST CORRECTIONS. An operator's text for one card line, citing verified claims the thesis
   links and passing the card's own checks — or refused whole. The bottom line read "beat
   expectations for eight consecutive quarters" where the source projects an eighth consecutive
   quarter of double-digit growth.
4. THE OVERVIEW AND THE CARD. A thesis new and downgraded in one week is ONE row showing both
   events; a line the review questioned is linked from the card's Review Required indicator and
   from the review queue; nothing reads "page None" or a double-escaped entity; the card's
   at-a-glance answers carry no engine codes.

The articles are HYPOTHETICAL and labelled as such, built from the REAL extraction types. No
network, no model call.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import timewindow, verify
from vinci.theme_intelligence.cards import render_html, render_markdown, replace_sentence
from vinci.theme_intelligence.engine import CorrectionError, SentenceCorrection
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import (
    build_dashboard,
    card_context,
    render_dashboard_html,
    write_run_outputs,
)
from vinci.theme_intelligence.schemas import (
    CardSentence,
    IssueSeverity,
    Provenance,
    ResearchAction,
    RunStatus,
    ThesisVersion,
    VerificationIssue,
    page_prefix,
)
from vinci.theme_intelligence.verify import card_sentences, deterministic_card_checks

AS_OF = date(2026, 10, 12)
PUBLISHED = date(2026, 10, 6)
GROWTH = ("Analysts project S&P 500 earnings to grow 11% in the third quarter, an eighth "
          "consecutive quarter of double-digit growth.")
SECTORS = "Earnings rose in five of the 11 sectors last quarter."
PRICE = "Magnificent 7 stocks have risen 12% this year, underperforming the index's 15% gain."
SLOWING = "Magnificent 7 earnings growth slowed to 18% last quarter."


def _broadening(*, title: str = "Earnings broaden beyond megacap tech",
                sectors_value: float = 5) -> tuple[Hypo, dict[str, Any]]:
    """An earnings-broadening thesis in the J.P. Morgan pilot's shape: a projected growth figure,
    a sector count written partly in words, a share-price line and an earnings line against."""
    art = Hypo(slug="broadening", publisher="Hypo Research A", published=PUBLISHED,
               blocks=[("paragraph", GROWTH), ("paragraph", SECTORS), ("paragraph", PRICE),
                       ("paragraph", SLOWING)])
    x = extraction(
        [claim("c1", "b001", GROWTH.rstrip("."), "S&P 500 earnings growth 11% in 3Q",
               kind="forecast", epistemic="forecast", metric="earnings growth", value=11,
               value_text="11%", unit="% YoY", period="3Q26", scope="S&P 500"),
         claim("c2", "b002", SECTORS.rstrip("."), "earnings rose in 5 of 11 sectors",
               metric="sectors with rising earnings", value=sectors_value,
               value_text="five of the 11", unit="sectors", period="2Q26"),
         claim("c3", "b003", PRICE.rstrip("."), "Magnificent 7 up 12% YTD vs index 15%",
               metric="price return", value=12, value_text="12%", unit="%", period="YTD 2026"),
         claim("c4", "b004", SLOWING.rstrip("."), "Magnificent 7 earnings growth 18%",
               metric="earnings growth", value=18, value_text="18%", unit="% YoY",
               period="2Q26")],
        [hyp("h1", title, node="macro_market", mechanism="earnings_revision",
             supporting=["c1", "c2"], counter=["c3", "c4"])])
    return art, x


def _one(pipe: Pipeline) -> ThesisVersion:
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    return v


def _cid(pipe: Pipeline, local_quote: str) -> str:
    (a,) = pipe.store.articles()
    return next(c.claim_id for c in pipe.store.claims_for_article(a.article_id)
                if c.quote == local_quote.rstrip("."))


def _ingested(tmp_path: Path, **kw: Any) -> Pipeline:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art, x = _broadening(**kw)
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


# --- 1. numbers --------------------------------------------------------------------------------

@pytest.mark.parametrize(("value", "verified"), [(5, True), (11, True), (7, False)])
def test_a_figure_written_in_words_beside_digits_is_read_as_written(
        tmp_path: Path, value: float, verified: bool) -> None:
    """ "five of the 11" states 5 (and 11) — before the fix only the digit was read, and the
    verbatim figure failed its number check. A value the text does not state still fails."""
    pipe = _ingested(tmp_path, sectors_value=value)
    c = pipe.store.claim(_cid(pipe, SECTORS))
    assert c is not None and c.span_verified
    assert c.number_verified is verified


def test_a_named_index_or_quarter_label_is_no_figure_and_every_other_number_is_checked(
        tmp_path: Path) -> None:
    """On the card itself, through the production check: "S&P 500", "Russell 2000" and "Q2" are
    names; "500 companies" and "31%" are figures the cited claim must carry."""
    pipe = _ingested(tmp_path)
    v = _one(pipe)
    c2 = _cid(pipe, SECTORS)
    claims = {c.claim_id: c for a in pipe.store.articles()
              for c in pipe.store.claims_for_article(a.article_id)}

    def check(text: str) -> list[str]:
        card = replace_sentence(v.content, "s01.0", CardSentence(
            text=text, provenance=Provenance.MEASURED_OBSERVATION, claim_ids=(c2,)))
        return [i.detail.split(" prints ")[1].split(",")[0] for i in
                deterministic_card_checks(card, claims, "R-test")
                if i.ref_id.endswith(":s01.0") and i.code == "NUMBER_NOT_IN_CITED_CLAIMS"]

    assert check("Across the S&P 500, earnings rose in five of the 11 sectors in Q2") == []
    assert check("Russell 2000 and Nasdaq 100 earnings rose in 11 sectors in 2Q26") == []
    assert check("Across the S&P 500, earnings rose at 500 companies") == ["'500'"]
    assert check("Russell 2000 earnings rose 31% in 11 sectors") == ["'31'"]


# --- 2. a price move is market context --------------------------------------------------------

def test_a_share_price_line_is_price_context_never_counter_evidence_to_earnings(
        tmp_path: Path) -> None:
    pipe = _ingested(tmp_path)
    v = _one(pipe)
    w = v.content.s07_what_could_go_wrong
    price, slowing = _cid(pipe, PRICE), _cid(pipe, SLOWING)
    assert [s.claim_ids for s in w.price_context] == [(price,)]
    assert all(price not in s.claim_ids for s in w.counter_evidence)
    assert any(slowing in s.claim_ids for s in w.counter_evidence)  # an earnings line stays
    f8 = next(f for f in v.priority.factors if f.factor_id == "F8_counterevidence")
    assert f8.value == "1"  # the earnings line only
    last = len(w.counter_evidence) + len(w.alternative_mechanisms) + len(w.market_risks)
    assert card_sentences(v.content)[f"s07.{last}"][2] == (price,)  # numbered LAST: ids stable
    out = write_run_outputs(pipe.store, pipe.store.runs()[-1].run_id, tmp_path / "out")
    html = next(Path(out["dir"]).glob("cards/TH-*.html")).read_text()
    soup = BeautifulSoup(html, "html.parser")
    s07 = soup.select_one('[data-field="s07_what_could_go_wrong"]')
    group = "Price performance — market context, not earnings evidence"
    assert s07 is not None
    sub = next(x for x in s07.select(".sub") if x.get_text() == group)
    line = sub.find_next_sibling()  # the price line, under it, by its id and its citation
    assert line is not None and line["id"] == f"L-s07-{last}"
    assert line.select_one(f'a.ref[href="#{price}"]') is not None
    md = next(Path(out["dir"]).glob("cards/TH-*.md")).read_text()
    block = md.split(f"**{group}:**", 1)[1].split("\n**", 1)[0]  # the group's own lines
    assert price in block


# --- 3. analyst corrections -------------------------------------------------------------------

def _flagging(pipe: Pipeline, run_id: str, problem: str) -> None:
    """The card review in its real issue format: s01.0 and s01.1 questioned (PARTIAL)."""
    def review(card, claims):  # type: ignore[no-untyped-def]
        out = []
        for sid in ("s01.0", "s01.1"):
            text = card_sentences(card)[sid][0]
            out.append(VerificationIssue(
                issue_id=f"VI-test-{sid}", run_id=run_id, scope="card_sentence",
                ref_id=f"{card.header.thesis_id}:{sid}", severity=IssueSeverity.WARN,
                code="REVIEW_PARTIAL", detail=f"{sid}: {problem} | {text[:100]!r}",
                created_at=datetime.now(tz=UTC)))
        return out

    pipe.engine.reviewer = review


#: the pilot reviewer's habit: a claim id, cut short, inside its finding
CITING = "the span in C-71cbea09e3099d… and C-1d67... does not say this (test)"


def _reviewed(tmp_path: Path, problem: str = "overstates the source (test)") -> Pipeline:
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("ingest", as_of=AS_OF)
    _flagging(pipe, run.run_id, problem)
    art, x = _broadening()
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.engine.reviewer = None
    return pipe


FIXED = ("S&P 500 earnings are projected to grow 11% in Q3 — an eighth consecutive quarter of "
         "double-digit growth")


def test_an_analyst_correction_replaces_one_line_and_records_why(tmp_path: Path) -> None:
    pipe = _reviewed(tmp_path)
    v1 = _one(pipe)
    c1 = _cid(pipe, GROWTH)
    corr = SentenceCorrection(thesis_id=v1.thesis_id, sentence_id="s01.0", text=FIXED,
                              claim_ids=(c1,), reason="the source projects growth (test)")
    run, outs = pipe.run_reassess(as_of=AS_OF, corrections=[corr])
    assert run.status is RunStatus.SUCCEEDED and pipe.store.llm_calls(run.run_id) == []
    assert len(outs) == 1
    v2 = _one(pipe)
    assert v2.version == v1.version + 1
    text, prov, cids = card_sentences(v2.content)["s01.0"]
    assert text.startswith(FIXED) and cids == (c1,)
    assert prov == Provenance.FORECAST.value  # derived from the cited claim, never asserted
    keep = {k: x for k, x in card_sentences(v1.content).items() if k not in ("s01.0", "s08.next")}
    assert {k: card_sentences(v2.content)[k] for k in keep} == keep  # one line only
    assert "ANALYST CORRECTION s01.0 — the source projects growth (test)" in v2.change_summary
    again = pipe.store.thesis_version(v1.thesis_id, v1.version)
    assert again is not None and again.content_sha == v1.content_sha  # history stands
    out = write_run_outputs(pipe.store, run.run_id, tmp_path / "out")
    js = json.loads(next(Path(out["dir"]).glob("cards/TH-*.json")).read_text())
    assert js["analyst_corrections"] == {"s01.0": "the source projects growth (test)"}
    assert js["review_warnings"] == {"s01.1": "overstates the source (test)"}  # carried; the
    # corrected line's old finding no longer applies
    html = next(Path(out["dir"]).glob("cards/TH-*.print.html")).read_text()
    line = BeautifulSoup(html, "html.parser").select_one("#L-s01-0")
    assert line is not None
    assert "Corrected by the analyst — the source projects growth (test)" in line.get_text(" ")
    assert "UNRESOLVED REVIEW" not in line.get_text(" ")
    md = next(Path(out["dir"]).glob("cards/TH-*.md")).read_text()
    assert "the source projects growth (test)" in md
    d = build_dashboard(pipe.store, run.run_id, cards={}, generated="t")
    (row,) = [r for rs in d.categories.values() for r in rs]
    assert "Analyst correction" in row.events


@pytest.mark.parametrize("bad", ["unlinked", "no_claims", "unknown_line", "unstated_number",
                                 "unverified_number"])
def test_a_correction_that_would_add_an_unverified_fact_is_refused_whole(
        tmp_path: Path, bad: str) -> None:
    pipe = _reviewed(tmp_path)
    v1 = _one(pipe)
    c1, c2 = _cid(pipe, GROWTH), _cid(pipe, SECTORS)
    if bad == "unverified_number":  # a linked claim whose number failed its check
        pipe2 = _ingested(tmp_path / "x", sectors_value=7)
        pipe, v1 = pipe2, _one(pipe2)
        c2 = _cid(pipe, SECTORS)
    sid, text, ids = {
        "unlinked": ("s01.0", FIXED, ("C-0000000000000a",)),
        "no_claims": ("s01.0", FIXED, ()),
        "unknown_line": ("s01.9", FIXED, (c1,)),
        "unstated_number": ("s01.0", "S&P 500 earnings are projected to grow 31% in Q3", (c1,)),
        "unverified_number": ("s01.0", "Earnings rose in five of the 11 sectors", (c2,)),
    }[bad]
    corr = SentenceCorrection(thesis_id=v1.thesis_id, sentence_id=sid, text=text,
                              claim_ids=ids, reason="test")
    with pytest.raises(CorrectionError):
        pipe.run_reassess(as_of=AS_OF, corrections=[corr])
    assert _one(pipe).version == v1.version  # nothing applied in part
    assert pipe.store.runs()[-1].status is RunStatus.FAILED


def test_a_correction_citing_a_claim_whose_number_failed_is_refused_even_when_linked(
        tmp_path: Path) -> None:
    """Ingestion never links a claim whose number failed (so the end-to-end case above is refused
    as unlinked); the correction refuses it on its own as well — a second wall, pinned here."""
    pipe = _ingested(tmp_path, sectors_value=7)
    v = _one(pipe)
    c2 = _cid(pipe, SECTORS)
    held = pipe.store.claim(c2)
    assert held is not None and held.span_verified and held.number_verified is False
    corr = SentenceCorrection(thesis_id=v.thesis_id, sentence_id="s01.0",
                              text="Earnings rose in five of the 11 sectors", claim_ids=(c2,),
                              reason="test")
    with pytest.raises(CorrectionError, match="verified claims"):
        pipe.engine._corrected(v.content, corr, {c2: held}, "R-test")



def test_a_re_grade_relabels_a_stored_conditional_fact_and_says_so(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A card stored before the conditional rule (the pilot's Nomura risk lines: "Rising UST
    yields could create a feedback loop…", MEASURED OBSERVATION): the re-grade relabels it, and
    the new version's summary SAYS so — never just "no change in action"."""
    from vinci.theme_intelligence import cards

    monkeypatch.setattr(cards, "capped_label", lambda prov, text: prov)  # the rules of the day
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo(slug="conditional-stored", publisher="Hypo Research A", published=PUBLISHED,
               blocks=[("paragraph", SECTORS)])
    h = hyp("h1", "Earnings broaden", node="macro_market", mechanism="earnings_revision",
            supporting=["c1"])
    h["bottom_line_fact"] = {"text": "Broadening earnings could lift the equal-weight index",
                             "provenance": "source_stated", "claim_ids": ["c1"]}
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", SECTORS.rstrip("."), "earnings rose in 5 of 11 sectors", value=5,
               value_text="five of the 11", unit="sectors", period="2Q26")], [h]),
        as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    v1 = _one(pipe)
    assert card_sentences(v1.content)["s01.0"][1] == Provenance.MEASURED_OBSERVATION.value
    monkeypatch.undo()
    pipe.run_reassess(as_of=AS_OF)
    v2 = _one(pipe)
    assert v2.version == 2
    assert card_sentences(v2.content)["s01.0"][1] == Provenance.SOURCE_OPINION.value
    assert "1 conditional line(s) relabelled SOURCE OPINION" in v2.change_summary


# --- 4. the overview and the card ---------------------------------------------------------------

TAG = "Semiconductors"


def _hbm(period: str) -> tuple[Hypo, dict[str, Any]]:
    text = (f"Our HBM price tracker projects blended HBM prices to jump 121% YoY in {period} as "
            f"supply stays tight.")
    art = Hypo(slug=f"hbm-{period}".lower(), publisher="Hypo Research A",
               published=date(2026, 9, 29), blocks=[("paragraph", TAG), ("paragraph", text)])
    x = extraction(
        [claim("c1", "b002", text.rstrip("."), f"HBM blended price +121% {period}",
               kind="forecast", epistemic="forecast", metric="HBM blended price change",
               value=121, value_text="121%", unit="% YoY", period=period, scope="HBM")],
        [hyp("h1", "HBM supply tightness lifts prices", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", geography="Global", supporting=["c1"],
             step_list=[{"step": "pricing", "text": "HBM prices rise",
                         "provenance": "source_stated", "claim_ids": ["c1"]}],
             sectors=[(TAG, "b001", TAG)])])
    return art, x


def test_a_thesis_new_and_downgraded_in_one_week_is_one_row_showing_both(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The pilot's week: an article ingested (RESEARCH NOW under the rules of the day), then
    re-graded to WATCH, then the weekly scan. One row; both events; counted once each."""
    monkeypatch.setattr(timewindow, "NEAR_TERM_END_DAYS", 549)
    monkeypatch.setattr(verify, "bare_label", lambda kind, text, name: False)
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art, x = _hbm("2027")
    ingest(pipe, art.doc(), x, as_of=AS_OF, source_id="trendforce")
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert _one(pipe).priority.research_action is ResearchAction.RESEARCH_NOW
    monkeypatch.undo()
    pipe.run_reassess(as_of=AS_OF)
    assert _one(pipe).priority.research_action is ResearchAction.WATCH
    scan = pipe.start_run("scan", as_of=AS_OF, window_from=AS_OF - timedelta(days=7),
                          window_to=AS_OF)
    pipe.finish_run(RunStatus.SUCCEEDED)
    d = build_dashboard(pipe.store, scan.run_id, cards={}, generated="t")
    rows = [r for rs in d.categories.values() for r in rs]
    assert len(rows) == 1  # one thesis, one row — never once under NEW and again under DOWNGRADED
    assert rows[0].events == ["New", "Downgraded: Research Now → Watch"]
    assert (d.kpi["new"], d.kpi["downgraded"], d.kpi["upgraded"]) == (1, 1, 0)
    html = render_dashboard_html(d)
    soup = BeautifulSoup(html, "html.parser")
    (card,) = soup.select("#theses .thesis.row")
    tags = [t.get_text() for t in card.select(".tag")]
    assert tags == ["New", "Downgraded: Research Now → Watch"]
    activity = soup.select_one("#activity")
    assert activity is not None and "1 new · 0 upgraded · 1 downgraded" in activity.get_text(" ")


def test_review_required_links_to_the_exact_line_and_the_default_view_carries_no_codes(
        tmp_path: Path) -> None:
    pipe = _reviewed(tmp_path, CITING)
    run = pipe.store.runs()[-1]
    out = write_run_outputs(pipe.store, run.run_id, tmp_path / "out")
    html = next(Path(out["dir"]).glob("cards/TH-*[!t].html")).read_text()
    soup = BeautifulSoup(html, "html.parser")
    flag = soup.select_one(".hdr a.flag")
    assert flag is not None and flag["href"] == "#L-s01-0"
    assert "Review required · 2 line(s)" in flag.get_text()
    names = [x.get_text() for x in soup.select(".hdr .vline .note a")]
    assert names == ["bottom line 1", "bottom line 2"]  # one section twice: numbered
    for sid in ("s01-0", "s01-1"):  # each finding names its line, and the line exists
        assert soup.select_one(f'.hdr .vline a[href="#L-{sid}"]') is not None
        line = soup.select_one(f"#L-{sid}")
        assert line is not None and "UNRESOLVED REVIEW" in line.get_text(" ")
        ids = line.select(".rw .aud")  # the finding's claim id: behind the audit switch
        assert [x.get_text(strip=True) for x in ids] == ["C-71cbea09e3099d…", "C-1d67..."]
    # the at-a-glance answers: all seven, risks and the next check open — not in a <details>
    glance = soup.select_one(".glance")
    assert glance is not None and glance.find_parent("details") is None
    assert [h.get_text() for h in glance.select("h3")] == [
        "The thesis", "What changed", "Effect on profits, margins or demand",
        "Strongest evidence", "Why Watch", "What could invalidate it", "Next check"]
    nine = [s["data-field"] for s in soup.select("[data-field]")]
    assert nine == ["s01_bottom_line", "s02_what_changed", "s03_transmission",
                    "s04_key_evidence", "s05_affected", "s06_why_now",
                    "s07_what_could_go_wrong", "s08_decision", "s09_sources"]
    d = build_dashboard(pipe.store, run.run_id, cards={}, generated="t")
    dash = BeautifulSoup(render_dashboard_html(d), "html.parser")
    links = [str(a["href"]) for a in dash.select("#review a") if "#L-" in str(a["href"])]
    assert [h.rsplit("#", 1)[1] for h in links] == ["L-s01-0", "L-s01-1"]
    assert "Not assessed — " in soup.select_one('[data-field="s08_decision"]').get_text(" ")
    assert soup.select_one(".foot .aud") is not None  # the run id and engine: audit layer
    assert any("How this evidence arrived" in x.get_text() for x in dash.select(".dates"))
    for s in (soup, dash):
        for el in s.select(".aud, .auditbar, script, input, #ops"):
            el.decompose()
        first = s.get_text(" ", strip=True)
        for code in ("REVIEW_PARTIAL", "F5_", "F7_", "F8_", "NOT_ASSESSED", "ti-engine",
                     "page None", "&#039;", "&amp;"):
            assert code not in first, code
        assert re.search(r"\b(?:TH|A|C|R)-[0-9A-Za-z]{8,}", first) is None  # no registry id
        assert re.search(r"\bC-[0-9a-f]{3,}", first) is None  # nor a reviewer's shortened one
        assert re.search(r"\(\s*\)", first) is None  # an id gone from its parentheses: both go


def test_a_stored_page_none_and_an_encoded_entity_never_reach_the_reader(tmp_path: Path) -> None:
    """Stored before the fix: a web article's risk line reading "page None", and a page title
    the source had entity-encoded. The record keeps them; the reader sees neither."""
    pipe = _ingested(tmp_path, title="America&#039;s earnings broaden")
    v = _one(pipe)
    (t,) = pipe.store.theses()
    stored = "a risk the source states (Hypo Research A, page None)"
    card = replace_sentence(v.content, "s01.1", CardSentence(
        text=stored, provenance=Provenance.MODEL_INFERENCE, claim_ids=()))
    rc = card_context(pipe.store, t, v, generated="t")
    html = render_html(card, rc)
    assert "page None" not in html and "&amp;#039;" not in html
    assert "America&#x27;s earnings broaden" in html
    md = render_markdown(card, rc)  # the Markdown reader: decoded, "S&P" untouched
    assert "&#039;" not in md and "America's earnings broaden" in md and "page None" not in md
    assert "S&P 500" in md
    assert page_prefix(None) == "" and page_prefix(4) == "page 4: "
