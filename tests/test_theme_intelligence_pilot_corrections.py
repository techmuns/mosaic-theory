"""The supervised pilot's material defects (2026-10-12), corrected — PR #703.

1. RESEARCH NOW ELIGIBILITY. The pilot's one RESEARCH NOW (a TrendForce HBM price forecast) rested
   on a page CATEGORY TAG as its "source-named exposure" and on next year's undifferentiated
   full-year figure as its 2-4-quarter window. A bare page label is no exposure; a window that
   runs past the next four quarters is no near-term window — and, mostly inside them, not
   longer-term only either: WATCH. A stored RESEARCH NOW is re-graded from stored evidence.
2. REVIEW WARNINGS. Seven lines the card review questioned printed with no qualification, two of
   them conditional opinions labelled MEASURED OBSERVATION.
3. RETRIEVAL. A long paid-post preview recorded FULL before the parser fix keeps its row, and is
   read as PARTIAL.

The articles are HYPOTHETICAL and labelled as such, built from the REAL extraction types in the
pilot's shapes. No network, no model call.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import (
    Hypo,
    claim,
    extraction,
    fetched,
    hyp,
    ingest,
    make_pipeline,
)
from vinci.theme_intelligence import timewindow, verify
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import build_dashboard, research_verification
from vinci.theme_intelligence.schemas import (
    IssueSeverity,
    Provenance,
    ResearchAction,
    RetrievalState,
    RunStatus,
    ThesisVersion,
    VerificationIssue,
)
from vinci.theme_intelligence.timewindow import straddles, window_of
from vinci.theme_intelligence.verify import bare_label, card_sentences

AS_OF = date(2026, 10, 12)
TAG = "Semiconductors"  # the page's category line, as TrendForce's pages carry it
DATA_REPORT = "trendforce"  # an industry data report: a price tracker forecasting its own price


def _forecast(period: str) -> str:
    return (f"Our HBM price tracker projects blended HBM prices to jump 121% YoY in {period} as "
            f"supply stays tight.")


def _pilot_shape(period: str, *, exposure: str = "tag") -> tuple[Hypo, dict[str, Any]]:
    """The pilot's RESEARCH NOW: a category line (b001), the tracker's forecast (b002), the pricing
    step stated by the source, and ONE sector exposure — the tag, or a span of the forecast."""
    text = _forecast(period)
    art = Hypo(slug=f"hbm-{period}-{exposure}".lower(), publisher="Hypo Research A",
               published=date(2026, 9, 29), blocks=[("paragraph", TAG), ("paragraph", text)])
    sector = ((TAG, "b001", TAG) if exposure == "tag" else ("HBM", "b002", "blended HBM prices"))
    x = extraction(
        [claim("c1", "b002", text.rstrip("."), f"HBM blended price +121% {period}",
               kind="forecast", epistemic="forecast", metric="HBM blended price change",
               value=121, value_text="121%", unit="% YoY", period=period, scope="HBM")],
        [hyp("h1", "HBM supply tightness lifts prices", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", geography="Global", supporting=["c1"],
             step_list=[{"step": "pricing", "text": "HBM prices rise",
                         "provenance": "source_stated", "claim_ids": ["c1"]}],
             sectors=[sector])])
    return art, x


def _one(pipe: Pipeline) -> ThesisVersion:
    (t,) = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    return v


def _factor(v: ThesisVersion, fid: str) -> str:
    return next(f.value for f in v.priority.factors if f.factor_id == fid)


def _run(tmp_path: Path, period: str, *, exposure: str = "tag") -> Pipeline:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=AS_OF)
    art, x = _pilot_shape(period, exposure=exposure)
    ingest(pipe, art.doc(), x, as_of=AS_OF, source_id=DATA_REPORT)
    return pipe


# --- 1. RESEARCH NOW eligibility ---------------------------------------------------------------

def test_the_pilot_shape_is_watch_its_category_tag_refused_as_an_exposure(
        tmp_path: Path) -> None:
    pipe = _run(tmp_path, "2027")
    v = _one(pipe)
    assert v.priority.research_action is ResearchAction.WATCH
    assert v.content.s05_affected.sector_exposures == ()  # the tag never reaches the card
    refused = [i for i in pipe.store.issues() if i.code == "SECTOR_LABEL_ONLY"]
    assert len(refused) == 1 and refused[0].severity is IssueSeverity.WARN
    assert "'Semiconductors'" in refused[0].detail and "b001" in refused[0].detail
    assert _factor(v, "F5_near_term_relevance") == "runs_past"
    assert _factor(v, "F12_fundamental_inflection") == "absent"
    assert "run past the next 2-4 quarters" in v.priority.rules_fired[0]


@pytest.mark.parametrize(("period", "action", "near"), [
    ("2027", ResearchAction.WATCH, "runs_past"),  # most of it inside the horizon: WATCH
    ("1H27", ResearchAction.RESEARCH_NOW, "yes"),  # a window inside the next 4 quarters
    ("2030", ResearchAction.SKIP, "longer_term_only"),  # longer-term only: SKIP-3, as before
])
def test_with_a_stated_exposure_only_a_window_inside_the_next_four_quarters_is_near_term(
        tmp_path: Path, period: str, action: ResearchAction, near: str) -> None:
    v = _one(_run(tmp_path, period, exposure="stated"))
    assert [s.name for s in v.content.s05_affected.sector_exposures] == ["HBM"]  # kept
    assert v.priority.research_action is action, v.priority.rules_fired
    assert _factor(v, "F5_near_term_relevance") == near


@pytest.mark.parametrize(("kind", "text", "name", "label"), [
    ("paragraph", "Semiconductors", "Semiconductors", True),  # the pilot's TrendForce tag
    ("paragraph", "Semiconductors / LED", "Semiconductors / LED", True),  # a stored one
    ("tag", "Semiconductors", "Semiconductors (memory)", True),
    ("heading", "China Power Plant Equipment", "China Power Plant Equipment", False),  # Citi
    ("chart_title", "S&P 500 Utilities sector", "S&P 500 Utilities sector", False),
    ("dek", "DRAM suppliers continue to prioritise capacity", "DRAM", False),
    ("paragraph", _forecast("2027"), "HBM", False),  # a statement, not a label
    ("paragraph", "Semiconductors and memory makers will benefit", "Semiconductors", False),
])
def test_only_a_line_saying_nothing_but_the_sectors_name_is_a_bare_label(
        kind: str, text: str, name: str, label: bool) -> None:
    assert bare_label(kind, text, name) is label


@pytest.mark.parametrize(("period", "ref", "want"), [
    ("2027", date(2026, 10, 12), True),  # 9½ of 12 months inside the next four quarters
    ("2H27", date(2026, 10, 12), True),
    ("through 2027", date(2026, 10, 12), True),
    ("4Q26", date(2026, 10, 10), False),  # inside them: near-term, not straddling
    ("2028", date(2027, 1, 2), False),  # starts inside, runs almost wholly past: long-range
    ("2025-2031", date(2026, 2, 9), False),
])
def test_a_window_straddles_when_it_runs_past_the_horizon_mostly_inside_it(
        period: str, ref: date, want: bool) -> None:
    w = window_of(period, ref)
    assert w is not None and straddles(w, ref) is want


def test_a_stored_research_now_is_re_graded_from_stored_evidence_to_watch(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The pilot's RESEARCH NOW as the OLD rules made it (a 549-day near-term window; no label
    test), then `reassess` under the current rules: a NEW version, WATCH, every reviewed sentence
    kept word for word, the tag exposure refused, v1 untouched — $0 (no model client exists)."""
    monkeypatch.setattr(timewindow, "NEAR_TERM_END_DAYS", 549)
    monkeypatch.setattr(verify, "bare_label", lambda kind, text, name: False)
    pipe = make_pipeline(tmp_path)
    first = pipe.start_run("fixture", as_of=AS_OF)

    def review(card, claims):  # type: ignore[no-untyped-def]  # one line questioned, as in 2
        text = card_sentences(card)["s01.0"][0]
        return [VerificationIssue(
            issue_id="VI-test-review", run_id=first.run_id, scope="card_sentence",
            ref_id=f"{card.header.thesis_id}:s01.0", severity=IssueSeverity.WARN,
            code="REVIEW_PARTIAL", detail=f"s01.0: not in the cited span (test) | {text[:100]!r}",
            created_at=datetime.now(tz=UTC))]

    pipe.engine.reviewer = review
    art, x = _pilot_shape("2027")
    ingest(pipe, art.doc(), x, as_of=AS_OF, source_id=DATA_REPORT)
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.engine.reviewer = None
    v1 = _one(pipe)
    assert v1.priority.research_action is ResearchAction.RESEARCH_NOW  # the pilot's outcome
    monkeypatch.undo()
    run, outs = pipe.run_reassess(as_of=AS_OF)
    assert run.status is RunStatus.SUCCEEDED and pipe.store.llm_calls(run.run_id) == []
    assert [(o.previous_action, o.action, o.events) for o in outs] == [
        (ResearchAction.RESEARCH_NOW, ResearchAction.WATCH, ["DOWNGRADED"])]
    v2 = _one(pipe)
    assert v2.version == 2 and v2.priority.research_action is ResearchAction.WATCH
    assert v2.content.header.research_action is v2.content.s08_decision.research_action \
        is ResearchAction.WATCH
    assert v2.content.s05_affected.sector_exposures == ()
    assert "REASSESSED" in v2.change_summary and "page label" in v2.change_summary
    keep = {k: v for k, v in card_sentences(v1.content).items() if k != "s08.next"}
    assert {k: card_sentences(v2.content)[k] for k in keep} == keep  # reviewed text untouched
    again = pipe.store.thesis_version(v1.thesis_id, 1)
    assert again is not None and again.content_sha == v1.content_sha  # history stands
    (ev,) = [e for e in pipe.store.events(thesis_id=v1.thesis_id) if e.run_id == run.run_id
             and e.event_type == "DOWNGRADED"]
    assert ev.version == 2
    md, _html, js = _rendered(pipe, run.run_id)  # the review's warning stays on its line
    assert js["review_warnings"] == {"s01.0": "not in the cited span (test)"}
    assert "UNRESOLVED REVIEW — not in the cited span (test)" in md
    _, outs2 = pipe.run_reassess(as_of=AS_OF)  # nothing left to change: no new version
    assert outs2 == [] and _one(pipe).version == 2


# --- 2. review warnings on the card ------------------------------------------------------------

COUNT = "Fed funds futures price three cuts by June 2027."
CONDITIONAL = "Rising yields could deepen the deficit"


def _reviewed(tmp_path: Path, bottom_fact: str) -> tuple[Pipeline, str]:
    """A bottom line citing a MEASURED claim, its first line flagged PARTIAL by the card review in
    the real issue format and run (`verify.review_card`): "<sid>: <problem> | <the sentence>"."""
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("fixture", as_of=date(2026, 3, 2))

    def review(card, claims):  # type: ignore[no-untyped-def]
        text = card_sentences(card)["s01.0"][0]
        return [VerificationIssue(
            issue_id=f"VI-test-{card.header.thesis_id}", run_id=run.run_id,
            scope="card_sentence", ref_id=f"{card.header.thesis_id}:s01.0",
            severity=IssueSeverity.WARN, code="REVIEW_PARTIAL",
            detail=f"s01.0: the span does not show it (test) | {text[:100]!r}",
            created_at=datetime.now(tz=UTC))]

    pipe.engine.reviewer = review
    art = Hypo(slug="flagged", publisher="Hypo Research A", published=date(2026, 3, 2),
               blocks=[("paragraph", COUNT)])
    h = hyp("h1", "Rate cuts lift duration", node="macro_market", mechanism="rates_policy",
            supporting=["c1"])
    h["bottom_line_fact"] = {"text": bottom_fact, "provenance": "source_stated",
                             "claim_ids": ["c1"]}
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", COUNT.rstrip("."), "three cuts priced", value=3, value_text="three",
               unit="cuts", period="June 2027", epistemic="actual", kind="metric")], [h]),
        as_of=date(2026, 3, 2), publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe, run.run_id


def _rendered(pipe: Pipeline, run_id: str) -> tuple[str, str, dict[str, Any]]:
    import json

    from vinci.theme_intelligence.report import write_run_outputs

    out = write_run_outputs(pipe.store, run_id)
    md = next(Path(out["dir"]).glob("cards/TH-*.md")).read_text()
    html = next(Path(out["dir"]).glob("cards/TH-*.print.html")).read_text()
    js = json.loads(next(Path(out["dir"]).glob("cards/TH-*.json")).read_text())
    return md, html, js


def test_a_line_the_review_questioned_carries_its_warning_and_is_never_a_verified_fact(
        tmp_path: Path) -> None:
    pipe, run_id = _reviewed(tmp_path, "Futures price three cuts by June 2027")
    v = _one(pipe)
    assert v.content.s01_bottom_line[0].provenance is Provenance.MEASURED_OBSERVATION  # stored
    md, html, js = _rendered(pipe, run_id)
    line = next(x for x in md.splitlines() if "Futures price three cuts" in x)
    assert line.startswith("- **SOURCE OPINION:**")  # a questioned line is no verified fact
    assert "⚠ **UNRESOLVED REVIEW — the span does not show it (test)**" in line
    assert "UNRESOLVED REVIEW — the span does not show it (test)" in html  # print shows it
    assert js["review_warnings"] == {"s01.0": "the span does not show it (test)"}


@pytest.mark.parametrize(("fact", "label"), [
    (CONDITIONAL, Provenance.SOURCE_OPINION),  # what could happen: the source's argument
    ("If cuts come, duration rallies", Provenance.SOURCE_OPINION),
    ("Futures price three cuts by June 2027", Provenance.MEASURED_OBSERVATION),
    ("In May 2026 futures priced three cuts", Provenance.MEASURED_OBSERVATION),  # the month
])
def test_a_conditional_line_is_never_labelled_a_measured_observation(
        tmp_path: Path, fact: str, label: Provenance) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=date(2026, 3, 2))
    art = Hypo(slug="conditional", publisher="Hypo Research A", published=date(2026, 3, 2),
               blocks=[("paragraph", COUNT)])
    h = hyp("h1", "Rate cuts lift duration", node="macro_market", mechanism="rates_policy",
            supporting=["c1"])
    h["bottom_line_fact"] = {"text": fact, "provenance": "source_stated", "claim_ids": ["c1"]}
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", COUNT.rstrip("."), "three cuts priced", value=3, value_text="three",
               unit="cuts", period="June 2027", epistemic="actual", kind="metric")], [h]),
        as_of=date(2026, 3, 2), publisher=art.publisher)
    (s,) = [s for s in _one(pipe).content.s01_bottom_line if s.text.startswith(fact)]
    assert s.provenance is label


# --- 3. a preview recorded FULL before the parser fix -----------------------------------------

def test_a_version_recorded_full_and_now_read_as_a_preview_is_corrected_never_rewritten(
        tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    art, x = _pilot_shape("1H27", exposure="stated")
    doc = art.doc()
    first = pipe.start_run("fixture", as_of=AS_OF)
    pipe.process_document(doc, fetched(doc), url=doc.canonical_url, source_id=DATA_REPORT,
                          as_of=AS_OF, fixture=x)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (a,) = pipe.store.articles()
    (v,) = pipe.store.article_versions(a.article_id)
    assert v.retrieval_state is RetrievalState.FULL
    def calls() -> int:
        return int(pipe.store.conn.execute("SELECT COUNT(*) FROM llm_calls").fetchone()[0])

    before = calls()
    for _ in range(2):  # the same content, now read as a preview — twice: one correction
        pipe.start_run("fixture", as_of=AS_OF)
        res = pipe.process_document(doc, fetched(doc, state=RetrievalState.PARTIAL),
                                    url=doc.canonical_url, source_id=DATA_REPORT, as_of=AS_OF,
                                    fixture=x)
        pipe.finish_run(RunStatus.SUCCEEDED)
        assert res.status == "ALREADY_INGESTED"
    fixes = [i for i in pipe.store.issues() if i.code == "RETRIEVAL_CORRECTED"]
    assert len(fixes) == 1 and fixes[0].ref_id == v.version_id
    now = pipe.store.article_version(v.version_id)
    assert now is not None and now.retrieval_state is RetrievalState.PARTIAL
    assert "CORRECTED to PARTIAL" in now.retrieval_note
    raw = pipe.store.conn.execute("SELECT retrieval_state FROM article_versions WHERE "
                                  "version_id=?", (v.version_id,)).fetchone()
    assert raw[0] == "FULL"  # the original row stands
    assert pipe.store.article(a.article_id) == a and calls() == before  # spend stands
    run = pipe.store.run(first.run_id)
    assert run is not None
    assert research_verification(pipe.store, run)["articles_preview_only"] == 1
    d = build_dashboard(pipe.store, first.run_id, cards={}, generated="t")
    assert (d.articles_read, d.articles_partial) == (1, 1)
    # the RESEARCH NOW granted on "retrieval FULL" is re-graded at once, from stored evidence
    v2 = _one(pipe)
    assert v2.version == 2 and v2.priority.research_action is ResearchAction.WATCH
    assert "retrieval PARTIAL" in v2.priority.rules_fired[0]
    from vinci.theme_intelligence.report import write_run_outputs

    latest = max(pipe.store.runs(), key=lambda r: r.started_at)
    out = write_run_outputs(pipe.store, latest.run_id)
    md = next(Path(out["dir"]).glob("cards/TH-*.md")).read_text()
    source = next(x for x in md.splitlines() if "industry_data_report" in x)
    assert "retrieval PARTIAL (corrected" in source and md.startswith("# HBM")
    assert "**WATCH**" in md
