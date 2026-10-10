"""Acceptance: the J.P. Morgan "Software Shock: AI's Broken Logic" article (as of 2026-02-09).

Runs the REAL engine on the AUTHENTIC fixture (an excerpt of the retrieved page, the frozen pass-1
model output, the real SEC rows) — nothing here is a hand-written card. Value pins are allowed
because every input is FROZEN (CLAUDE.md test-layer rule); the live run is the corpus check.

What the brief requires of this article, and what each test pins:
- exactly THREE theses — AI infrastructure / indiscriminate selling, software / conditional
  valuation recovery (WATCH), AI adoption / margin advantage (WATCH);
- META, AMZN, GOOGL, MSFT named as capex spenders, no chipmaker added; Anthropic private; IGV an
  ETF; the 145-member basket's NTM margins approximate + forecast + dated 2026-02-02 (22V/FactSet);
- Alphabet's exposure is GOOGL / GOOG only: GOOGM / GOOGN (depositary shares of convertible
  PREFERRED stock) were not registered on 2026-02-09 and never enter the record as stock;
- the 99th-percentile correlation stays a market RISK, never a fourth record of any kind;
- valuation and investment readiness stay NOT_ASSESSED.

AI INFRASTRUCTURE IS WATCH, NOT THE BRIEF'S RESEARCH NOW (review of PR #703, P0.4 / P0.5). Its
only offered "dislocation" is the article's rhetorical question — "why are stocks also down that
should benefit…" — which is the SOURCE's OPINION, not a measured mispricing; the corrected rule
counts only a mispricing measured in the last quarter or a dated event inside the window. The
first build's RESEARCH NOW rested on counting that opinion as evidence. Pinned from the
deterministic rule trace, so a future change to the rule has to change this test on purpose.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from tests.theme_intelligence_support import JPM_AS_OF, ingest_jpm, make_pipeline
from vinci.theme_intelligence.cards import render_html, render_json, render_markdown
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import card_context, write_run_outputs
from vinci.theme_intelligence.schemas import (
    SECTION_IDS,
    Epistemic,
    InstrumentClass,
    InvestmentReadiness,
    LinkRole,
    PitStatus,
    ResearchAction,
    ResolutionStatus,
    RunStatus,
    StanceInSource,
    Thesis,
    ThesisKind,
    ThesisVersion,
)
from vinci.theme_intelligence.verify import card_sentences


@pytest.fixture(scope="module")
def jpm(tmp_path_factory: pytest.TempPathFactory) -> Pipeline:
    pipe = make_pipeline(tmp_path_factory.mktemp("jpm"))
    pipe.start_run("article", as_of=JPM_AS_OF, window_from=JPM_AS_OF, window_to=JPM_AS_OF)
    res = ingest_jpm(pipe)
    assert res.status == "PROCESSED", res.note
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


def _by_node(pipe: Pipeline) -> dict[str, tuple[Thesis, ThesisVersion]]:
    out = {}
    for t in pipe.store.theses():
        v = pipe.store.thesis_version(t.thesis_id, t.current_version)
        assert v is not None
        out[t.key_node.split(".")[0]] = (t, v)
    return out


def test_exactly_three_theses_with_the_expected_actions(jpm: Pipeline) -> None:
    by = _by_node(jpm)
    assert sorted(by) == ["ai_adoption", "ai_infrastructure", "software"]
    assert len(jpm.store.theses()) == 3
    infra = by["ai_infrastructure"][1].priority
    assert infra.research_action is ResearchAction.WATCH
    assert "no verified dislocation or catalyst" in infra.rules_fired[0]
    f7 = next(f for f in infra.factors if f.factor_id == "F7_dislocation_or_catalyst")
    assert f7.value == "absent" and "NOT counted (opinion" in f7.note
    assert by["software"][1].priority.research_action is ResearchAction.WATCH
    assert by["ai_adoption"][1].priority.research_action is ResearchAction.WATCH
    # the correlation is a market risk, not a fourth record of either kind
    assert all(t.key_mechanism != "market_structure_risk" for t, _ in by.values())
    assert {t.kind for t, _ in by.values()} == {ThesisKind.INVESTMENT_THESIS}


def test_ai_infrastructure_names_only_the_four_spenders(jpm: Pipeline) -> None:
    t, v = _by_node(jpm)["ai_infrastructure"]
    cos = v.content.s05_affected.companies
    assert sorted(c.name_as_written for c in cos) == ["Alphabet", "Amazon", "Meta", "Microsoft"]
    tickers = {c.name_as_written: {x.ticker for x in c.listings} for c in cos}
    assert tickers["Meta"] == {"META"} and tickers["Amazon"] == {"AMZN"}
    assert tickers["Microsoft"] == {"MSFT"} and "GOOGL" in tickers["Alphabet"]
    assert all(c.resolution_status is ResolutionStatus.LISTED_EQUITY for c in cos)
    assert all(c.recommendation_status.value == "not_a_recommendation" for c in cos)
    assert all(c.role.value == "spending_customer" for c in cos)
    # POINT IN TIME: every exposure line is common equity on a cover page filed by the as-of date;
    # Alphabet's preferred depositary lines did not exist yet and never become its stock
    assert tickers["Alphabet"] == {"GOOGL", "GOOG"}
    for c in cos:
        for x in c.listings:
            assert x.pit_status is PitStatus.VERIFIED, (c.name_as_written, x)
            assert x.instrument is InstrumentClass.COMMON_EQUITY
            assert x.pit_source is not None
            assert date.fromisoformat(x.pit_source.split("filed ")[1][:10]) <= JPM_AS_OF
    goog = next(c for c in cos if c.name_as_written == "Alphabet")
    later = {x.ticker: x.pit_status for x in goog.other_securities}
    assert later == {"GOOGM": PitStatus.NOT_REGISTERED_AS_OF,
                     "GOOGN": PitStatus.NOT_REGISTERED_AS_OF}
    # chipmakers are a basket the source does NOT populate — no company was added for them
    named = {c.name_as_written for grp in (v.content.s05_affected.companies,
                                           v.content.s05_affected.instruments,
                                           v.content.s05_affected.private_or_unlisted)
             for c in grp}
    assert named == {"Meta", "Amazon", "Alphabet", "Microsoft"}
    # research-only: readiness and valuation stay NOT_ASSESSED, said on the card
    assert v.priority.investment_readiness is InvestmentReadiness.NOT_ASSESSED
    assert "NOT_ASSESSED" in v.content.s06_why_now.valuation_status
    assert t.stance is StanceInSource.ASSERTED


def test_software_thesis_is_conditional_with_no_named_company(jpm: Pipeline) -> None:
    t, v = _by_node(jpm)["software"]
    av = v.content.s05_affected
    assert av.companies == ()  # no listed pure-play software company named as a buy
    status = {c.name_as_written: c.resolution_status for c in av.instruments + av.also_named}
    igv = next(n for n in status if "IGV" in n)
    assert status[igv] is ResolutionStatus.FUND  # an ETF, not a company
    assert status["Anthropic"] is ResolutionStatus.PRIVATE  # private stays private
    assert t.stance is StanceInSource.CONDITIONAL
    figures = {c.value_text for c in _claims(jpm, v) if c.value_text}
    assert {"18", "over 20%", "8x"} <= figures
    assert any("November" in c.quote for c in _claims(jpm, v) if c.metric
               and "EV/sales" in c.metric)
    assert "conditional" in v.priority.rules_fired[0]


def test_ai_adoption_margins_are_approximate_forecasts_dated_feb_2(jpm: Pipeline) -> None:
    _, v = _by_node(jpm)["ai_adoption"]
    margins = [c for c in _claims(jpm, v) if c.metric and "margin" in c.metric.lower()
               and c.value_text and c.value_text.endswith("%") and c.period]
    assert sorted(c.value_text or "" for c in margins) == ["13.0%", "14.5%", "16.4%"]
    for c in margins:
        assert c.epistemic is Epistemic.FORECAST
        assert c.approximate and c.chart_derived
        assert c.measured_as_of == date(2026, 2, 2)
        assert "22V" in (c.attributed_source_text or "")
        assert "FactSet" in (c.attributed_source_text or "")
    assert any(c.value_text == "145" for c in _claims(jpm, v))
    assert v.content.s05_affected.companies == ()  # basket constituents never invented
    # the card says so: every margin line carries its deterministic labels
    lines = [it.text for it in v.content.s02_what_changed.items if "%" in it.text]
    assert lines and all("forecast" in x and "approximate" in x for x in lines)


def test_correlation_is_kept_as_a_market_risk(jpm: Pipeline) -> None:
    risky = [lk for t in jpm.store.theses() for lk in jpm.store.links(t.thesis_id)
             if lk.role is LinkRole.RISK]
    quotes = [c.quote for lk in risky if (c := jpm.store.claim(lk.claim_id))]
    assert any("99th percentile" in q for q in quotes)
    sents = [s.text for _, v in _by_node(jpm).values()
             for s in v.content.s07_what_could_go_wrong.market_risks]
    assert any("99th" in s for s in sents)


def test_cards_render_nine_sections_in_order_everywhere(jpm: Pipeline) -> None:
    for t, v in _by_node(jpm).values():
        rc = card_context(jpm.store, t, v, generated="test")
        web, prn, md = render_html(v.content, rc), render_html(v.content, rc, print_mode=True), \
            render_markdown(v.content, rc)
        js = render_json(v.content, rc)
        pos = [web.find(f'data-field="{fid}"') for fid, _ in SECTION_IDS]
        assert -1 not in pos and pos == sorted(pos)
        assert [md.find(f"## {title}") for _, title in SECTION_IDS] == sorted(
            md.find(f"## {title}") for _, title in SECTION_IDS)
        assert js["section_order"] == [fid for fid, _ in SECTION_IDS]
        # web: 01/02/06/08 above the fold, 03/04/05/07/09 on demand; print: everything open
        for fid in ("s03_transmission", "s04_key_evidence", "s05_affected",
                    "s07_what_could_go_wrong", "s09_sources"):
            assert f'<details class="sec" data-field="{fid}">' in web
            assert f'<details class="sec" data-field="{fid}" open>' in prn
        for fid in ("s01_bottom_line", "s02_what_changed", "s06_why_now", "s08_decision"):
            assert f'<section class="sec" data-field="{fid}">' in web
        # REGRESSION: empty groups once matched each other's headings by identity (`()` is one
        # object), repeating headings in the Markdown card — each heading exactly once, in order
        s05 = md.split("## 05")[1].split("## 06")[0]
        heads = ["Sectors / themes the source names", "Stock exposures of this thesis",
                 "Named instruments / indices", "Private or unlisted", "Named, not securities",
                 "Also named in the source"]
        assert [s05.count(f"**{h}") for h in heads] == [1] * len(heads)
        assert [s05.index(f"**{h}") for h in heads] == sorted(s05.index(f"**{h}") for h in heads)
        # the print file is the complete record: no toggle of any kind stays closed in it
        tags = [x.split(">", 1)[0] for x in prn.split("<details")[1:]]
        assert tags and all(" open" in t for t in tags), tags
        # the source, its author and date are on every card
        assert "Kriti Gupta" in web and "2026-02-09" in web and "J.P. Morgan" in web


def test_run_outputs_and_qa(jpm: Pipeline, tmp_path: Path) -> None:
    run = jpm.store.runs()[-1]
    out = write_run_outputs(jpm.store, run.run_id, tmp_path / "out")
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert manifest["status"] == "SUCCEEDED" and manifest["theses_in_registry"] == 3
    for f in ("dashboard.html", "dashboard.md", "dashboard.json", "dashboard.csv",
              "report_print.html", "validation_log.json"):
        assert (tmp_path / "out" / f).exists(), f
    assert len(out["cards"]) == 3


def _claims(pipe: Pipeline, v: ThesisVersion) -> list:
    return [c for lk in pipe.store.links(v.thesis_id) if (c := pipe.store.claim(lk.claim_id))]


def test_a_withheld_line_prints_with_its_audit_text_open(tmp_path: Path) -> None:
    """THE PRINT FILE IS THE COMPLETE RECORD (CLAUDE.md three-tier rule): a sentence the review
    withheld keeps its audit text in a nested toggle — closed on the web, OPEN in print."""
    from datetime import UTC, datetime

    from vinci.theme_intelligence.schemas import IssueSeverity, VerificationIssue

    def review(card, claims):  # type: ignore[no-untyped-def]
        return [VerificationIssue(
            issue_id=f"VI-t-{card.header.thesis_id}", run_id=pipe.run.run_id,
            scope="card_sentence", ref_id=f"{card.header.thesis_id}:s03.0",
            severity=IssueSeverity.BLOCK, code="REVIEW_UNSUPPORTED",
            detail=f"s03.0: test block | {card_sentences(card)['s03.0'][0][:100]!r}",
            created_at=datetime.now(tz=UTC))]

    pipe = make_pipeline(tmp_path)
    pipe.engine.reviewer = review
    pipe.start_run("article", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    t = next(x for x in pipe.store.theses() if x.key_node == "ai_infrastructure")
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None
    rc = card_context(pipe.store, t, v, generated="t")
    assert "s03.0" in rc.blocked
    web, prn = render_html(v.content, rc), render_html(v.content, rc, print_mode=True)
    assert "WITHHELD" in web and "<details><summary class=\"note\">audit text" in web
    assert "<details open><summary class=\"note\">audit text" in prn
    tags = [x.split(">", 1)[0] for x in prn.split("<details")[1:]]
    assert all(" open" in tag for tag in tags)
