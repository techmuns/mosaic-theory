"""Review of PR #703, round 3 — FIX 4 (QA honesty) and FIX 5 (point-in-time date labels).

FIX 4: a SUCCEEDED scan with open completeness gaps must never read as verified. The run's
RESEARCH-VERIFICATION status is reported apart from its EXECUTION status; every open gap states
its cause; an account that names VERIFIED claims is checkable and closes its paragraph; the %
unit rule binds the number the value reads. Observed in the 2026-10-10 weekly sample (registry
weekly-12): three figures of one paragraph left open because "22 (52%)" read as 22 *texts* was
failed on the parenthetical's % sign, and a paragraph left open although pass 1b's account named
the verified claims c1–c3.

FIX 5: the publisher's date, the registry's ACTUAL first ingestion (wall clock, UTC) and the
analysis as-of are three fields; a historical replay is said to be one.

The articles are HYPOTHETICAL and labelled as such, built from the REAL extraction types; the
"22 (52%)" sentence reproduces the observed SHAPE, not the article.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.qa import run_qa
from vinci.theme_intelligence.report import (
    build_dashboard,
    render_dashboard_html,
    render_dashboard_md,
    research_verification,
    write_run_outputs,
)
from vinci.theme_intelligence.schemas import (
    LinkRole,
    RetrievalState,
    RunStatus,
    ThesisClaimLink,
)
from vinci.theme_intelligence.verify import _number_check

W1 = date(2026, 3, 2)

COUNT = ("Of those 42 papers, 22 (52%) argue that safety must precede or gate development, and "
         "only five are development-first.")
ACCOUNTED = ("Furthermore, because subscription plans are so heavily subsidized, they can have a "
             "large impact on margins and revenue per megawatt despite a small share of revenue.")
UNNAMED = ("A single static snapshot is not enough either, because labs publicly change their "
           "usage limits all the time with promotions and new model releases.")


def _article(state: RetrievalState = RetrievalState.FULL) -> Hypo:
    return Hypo(slug=f"verification-{state.value.lower()}", publisher="Hypo Research A",
                published=W1, state=state,
                blocks=[("paragraph", COUNT), ("paragraph", ACCOUNTED), ("paragraph", UNNAMED)])


def _extraction() -> dict:
    return extraction(
        [claim("c1", "b001", COUNT.split(", and")[0], "22 of 42 put safety first", value=22,
               value_text="22 (52%)", unit="texts", scope="technical-background papers")],
        [hyp("h1", "Safety-first research shapes AI policy", node="ai_adoption.enterprise_margins",
             mechanism="margin_expansion_adoption", supporting=["c1"])])


def _completeness(*, name_claims: bool) -> dict:
    return {"figure_reviews": [], "added_claims": [], "added_mentions": [],
            "hypothesis_additions": [], "added_hypotheses": [], "added_risks": [],
            "block_reviews": [
                {"block_id": "b002", "verdict": "covered", "hypothesis_ids": [],
                 "claim_ids": ["c1"] if name_claims else [],
                 "reason": "carried by claim c1"},
                {"block_id": "b003", "verdict": "covered", "hypothesis_ids": [], "claim_ids": [],
                 "reason": "carried by a first-pass market risk on silent limit changes"}]}


def _run(tmp_path: Path, *, state: RetrievalState = RetrievalState.FULL,
         name_claims: bool = True) -> Pipeline:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=W1)
    art = _article(state)
    ingest(pipe, art.doc(), _extraction(), as_of=W1, publisher=art.publisher,
           completeness=_completeness(name_claims=name_claims))
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


# --- the % unit rule binds the number the value reads ---------------------------------------------

@pytest.mark.parametrize(("value", "value_text", "unit", "ok"), [
    (22, "22 (52%)", "texts", True),    # observed 2026-10-10: a count, its % parenthetical
    (52, "22 (52%)", "texts", False),   # the value reads the % figure: a count unit disagrees
    (52, "22 (52%)", "%", True),
    (None, "22 (52%)", "texts", False),  # no value to read: any % binds (the strict reading)
    (15, "15%", "units", False),         # the original rule, unchanged
])
def test_the_percent_unit_rule_binds_the_number_the_value_reads(
        value: float | None, value_text: str, unit: str, ok: bool) -> None:
    got, notes = _number_check(value, value_text, unit, COUNT)
    assert got is ok, notes
    assert any("disagrees with a % figure" in n for n in notes) is (not ok)


# --- every gap is accounted for or states its cause -----------------------------------------------

def test_open_gaps_state_their_cause_and_a_claim_named_account_closes_its_paragraph(
        tmp_path: Path) -> None:
    pipe = _run(tmp_path)
    run = pipe.store.runs()[-1]
    (rep,) = pipe.store.completeness_for_run(run.run_id)
    c1 = next(c for c in pipe.store.claims_for_article(pipe.store.contributions()[0].article_id)
              if c.block_id == "b001")
    assert c1.number_verified is True  # "22 (52%)" read as 22 texts
    figs = {f.figure: f for f in rep.figures if f.block_id == "b001"}
    assert {"42", "22", "52%"} <= set(figs)
    assert all(figs[f].status == "captured" and figs[f].claim_ids == (c1.claim_id,)
               for f in ("42", "22", "52%"))
    blocks = {b.block_id: b for b in rep.blocks}
    assert blocks["b002"].status == "covered" and blocks["b002"].claim_ids == (c1.claim_id,)
    assert blocks["b002"].open_cause == ""
    # an account naming NO record cannot be checked: it stays open, its cause and words kept
    assert blocks["b003"].status == "unreviewed"
    assert blocks["b003"].open_cause == "account_names_no_record"
    assert "silent limit changes" in blocks["b003"].reason


def test_an_account_naming_no_claim_leaves_its_paragraph_open(tmp_path: Path) -> None:
    """The negative pin of the claim-named account: the same review without its claim ids."""
    pipe = _run(tmp_path, name_claims=False)
    (rep,) = pipe.store.completeness_for_run(pipe.store.runs()[-1].run_id)
    b2 = next(b for b in rep.blocks if b.block_id == "b002")
    assert b2.status == "unreviewed" and b2.open_cause == "account_names_no_record"


def test_a_figure_whose_claim_failed_verification_says_so(tmp_path: Path) -> None:
    """A claim quoting the figure exists but failed its number check: the figure stays open with
    cause `verification_failed` — never a plain "nobody captured it"."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=W1)
    art = Hypo(slug="failed-number", publisher="Hypo Research A", published=W1,
               blocks=[("paragraph", "DRAM contract prices rose 15% quarter over quarter in "
                                     "1Q26 as AI servers absorbed most new supply.")])
    x = extraction([claim("c1", "b001", "DRAM contract prices rose 15% quarter over quarter",
                          "DRAM +15%", value=51, value_text="51%", unit="%", period="1Q26")],
                   [hyp("h1", "DRAM up-cycle", node="ai_infrastructure.memory",
                        mechanism="pricing_cycle", supporting=["c1"])])
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher,
           completeness={"figure_reviews": [], "block_reviews": []})
    (rep,) = pipe.store.completeness_for_run(pipe.store.runs()[-1].run_id)
    f15 = next(f for f in rep.figures if f.figure == "15%")
    assert f15.status == "uncaptured" and f15.open_cause == "verification_failed"


# --- the research-verification status, apart from the scan's --------------------------------------

def test_a_completed_scan_with_open_gaps_is_not_verified_end_to_end(tmp_path: Path) -> None:
    pipe = _run(tmp_path)
    run = pipe.store.runs()[-1]
    assert run.status is RunStatus.SUCCEEDED
    v = research_verification(pipe.store, run)
    assert v["status"] == "INCOMPLETE"
    assert (v["paragraphs_open"], v["figures_open"]) == (1, 0)
    assert v["open_causes"] == {"account_names_no_record": 1}
    assert len(v["open_items"]) == 1 and "b003" in v["open_items"][0]
    out = write_run_outputs(pipe.store, run.run_id, tmp_path / "out")
    html = (tmp_path / "out" / "dashboard.html").read_text()
    md = (tmp_path / "out" / "dashboard.md").read_text()
    assert "scan execution SUCCEEDED · research verification INCOMPLETE" in html
    assert ('<b class="vt">Incomplete</b><span>Verification · 0 figure(s), 1 paragraph(s) '
            'open') in html
    assert "- Scan execution: SUCCEEDED" in md and "- Research verification: INCOMPLETE" in md
    assert out["manifest"]["status"] == "SUCCEEDED"
    assert out["manifest"]["research_verification"]["status"] == "INCOMPLETE"


def test_every_gap_accounted_for_is_fully_verified(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=W1)
    art = Hypo(slug="all-accounted", publisher="Hypo Research A", published=W1,
               blocks=[("paragraph", COUNT), ("paragraph", ACCOUNTED)])
    ingest(pipe, art.doc(), _extraction(), as_of=W1, publisher=art.publisher,
           completeness={"figure_reviews": [], "block_reviews": [
               {"block_id": "b002", "verdict": "covered", "hypothesis_ids": [],
                "claim_ids": ["c1"], "reason": "carried by claim c1"}]})
    pipe.finish_run(RunStatus.SUCCEEDED)
    run = pipe.store.runs()[-1]
    v = research_verification(pipe.store, run)
    assert v["status"] == "FULLY_VERIFIED" and v["open_items"] == []
    d = build_dashboard(pipe.store, run.run_id, cards={}, generated="t")
    assert "research verification FULLY_VERIFIED" in render_dashboard_html(d)
    assert '<div class="vstat">' not in render_dashboard_html(d)  # no warning box
    assert '<b class="vt">Fully verified</b>' in render_dashboard_html(d)


def test_a_preview_only_article_is_verified_within_the_preview_at_most(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=W1)
    art = Hypo(slug="preview", publisher="Hypo Research A", published=W1,
               state=RetrievalState.PARTIAL, blocks=[("paragraph", COUNT)])
    ingest(pipe, art.doc(), _extraction(), as_of=W1, publisher=art.publisher,
           completeness={"figure_reviews": [], "block_reviews": []})
    pipe.finish_run(RunStatus.SUCCEEDED)
    v = research_verification(pipe.store, pipe.store.runs()[-1])
    assert v["status"] == "VERIFIED_WITHIN_PREVIEW" and v["articles_preview_only"] == 1
    md = render_dashboard_md(build_dashboard(pipe.store, pipe.store.runs()[-1].run_id, cards={},
                                             generated="t"))
    assert "- Research verification: VERIFIED_WITHIN_PREVIEW" in md


# --- unverified material never reaches a thesis ---------------------------------------------------

def test_qa_fails_if_an_unverified_claim_is_ever_linked_to_a_thesis(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("fixture", as_of=W1)
    art = Hypo(slug="unverified-link", publisher="Hypo Research A", published=W1,
               blocks=[("paragraph", COUNT)])
    x = _extraction()
    x["claims"].append(claim("c2", "b001", "a sentence this article never prints", "x",
                             value=7, value_text="7%", unit="%"))
    x["hypotheses"][0]["supporting_claim_ids"].append("c2")
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher,
           completeness={"figure_reviews": [], "block_reviews": []})
    name = "no unverified claim is linked to a thesis"
    check = next(c for c in run_qa(pipe.store, run.run_id).checks if c.name == name)
    assert check.ok, check.detail  # the engine never links it
    bad = next(c for c in pipe.store.claims_for_article(pipe.store.contributions()[0].article_id)
               if not c.span_verified)
    tid = pipe.store.theses()[0].thesis_id
    pipe.store.add_link(ThesisClaimLink(thesis_id=tid, claim_id=bad.claim_id,
                                        role=LinkRole.SUPPORTS, first_version=1,
                                        change_class=pipe.store.links(tid)[0].change_class,
                                        independence_group="x"))
    check = next(c for c in run_qa(pipe.store, run.run_id).checks if c.name == name)
    assert not check.ok and bad.claim_id in check.detail


# --- FIX 5: three dates, and a replay says so -----------------------------------------------------

@pytest.mark.parametrize("replay", [True, False])
def test_a_historical_replay_is_never_labelled_a_detection(tmp_path: Path, replay: bool) -> None:
    from bs4 import BeautifulSoup

    from vinci.theme_intelligence.cards import render_html
    from vinci.theme_intelligence.report import card_context

    as_of = W1 if replay else datetime.now(tz=UTC).date()
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("fixture", as_of=as_of)
    art = Hypo(slug="replay", publisher="Hypo Research A", published=W1,
               blocks=[("paragraph", COUNT)])
    ingest(pipe, art.doc(), _extraction(), as_of=as_of, publisher=art.publisher,
           completeness={"figure_reviews": [], "block_reviews": []})
    pipe.finish_run(RunStatus.SUCCEEDED)
    t = pipe.store.theses()[0]
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None
    h = v.content.header
    assert (h.latest_article_date, h.first_ingested_at, h.analysis_as_of) == (
        W1, t.created_at, as_of)
    assert h.first_detected == t.created_at.date()  # the wall clock, never the replayed as-of
    soup = BeautifulSoup(render_html(v.content, card_context(pipe.store, t, v, generated="t")),
                         "html.parser")
    for el in soup.select(".aud, .auditbar, script, input, details.sec"):
        el.decompose()
    first = soup.get_text(" ", strip=True)
    write_run_outputs(pipe.store, run.run_id, tmp_path / "out")
    dash = (tmp_path / "out" / "dashboard.html").read_text()
    for page in (first, dash):
        assert f"Published {W1.isoformat()}" in page
        assert f"{t.created_at:%Y-%m-%d %H:%M} UTC" in page
        assert f"analysed as of {as_of.isoformat()}" in page
        assert ("historical replay" in page) is replay
        assert "first detected by the registry" not in page


def test_a_reviewer_cannot_anchor_a_line_to_a_claim_whose_number_failed(tmp_path: Path) -> None:
    """Found by the new QA check on the 2026-10-10 weekly sample (Nomura, registry weekly-15): the
    card reviewer suggested two claims whose NUMBER checks had failed as anchors for a partly
    supported bottom line; re-anchoring accepted them, the line was not withheld, and the claims
    were linked as context — unverified material reaching the hold test. Here the scripted
    reviewer would pass the line once the failed claim is cited; it must never be."""
    from vinci.theme_intelligence.schemas import IssueSeverity, VerificationIssue
    from vinci.theme_intelligence.verify import ReviewOutcome

    calls: list[bool] = []

    def review(card, claims):  # type: ignore[no-untyped-def]
        bad = next(c.claim_id for c in claims.values() if c.number_verified is False)
        cited = {c for s in card.s01_bottom_line for c in s.claim_ids}
        calls.append(bad in cited)
        if bad in cited:
            return ReviewOutcome([], {})
        return ReviewOutcome([VerificationIssue(
            issue_id=f"VI-test-{len(calls)}", run_id="t", scope="card_sentence",
            ref_id=f"{card.header.thesis_id}:s01.0", severity=IssueSeverity.BLOCK,
            code="REVIEW_PARTIAL", detail="partly supported (test)",
            created_at=datetime.now(tz=UTC))], {"s01.0": [bad]})

    pipe = make_pipeline(tmp_path)
    pipe.engine.reviewer = review
    run = pipe.start_run("fixture", as_of=W1)
    art = Hypo(slug="failed-anchor", publisher="Hypo Research A", published=W1,
               blocks=[("paragraph", COUNT),
                       ("paragraph", "None for the second group against market pricing of "
                                     "around four for each of the other groups.")])
    x = _extraction()
    x["claims"].append(claim("c2", "b002", "None for the second group against market pricing "
                                           "of around four", "none vs four priced", value=0,
                             value_text="None", unit="hikes"))
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher,
           completeness={"figure_reviews": [], "block_reviews": []})
    assert calls and not any(calls)  # the reviewer never saw the failed claim cited
    (t,) = pipe.store.theses()
    art_id = pipe.store.contributions()[0].article_id
    bad = next(c for c in pipe.store.claims_for_article(art_id) if c.number_verified is False)
    assert bad.claim_id not in {lk.claim_id for lk in pipe.store.links(t.thesis_id)}
    name = "no unverified claim is linked to a thesis"
    assert next(c for c in run_qa(pipe.store, run.run_id).checks if c.name == name).ok
