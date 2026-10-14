"""The final evidence and UX acceptance corrections (2026-10-12) — PR #703.

1. EVIDENCE NAVIGATION. A line's citation linked to `#C-…` while only the key-evidence rows had
   ids: the four pilot cards carried 27 broken links (14 targets). Every cited claim now has a row;
   an id with no record is printed, never linked; a link into a collapsed section opens it.
2. BUSINESS GROUPS. TrendForce names "GPU and ASIC manufacturers" and memory "suppliers" — groups,
   not companies. They are listed apart from listed-company exposures, verbatim and cited; no
   ticker is implied and the research action never reads them.
3. CURRENT vs HISTORICAL. A review finding that questioned a fact label the line no longer
   carries, and a figure whose claim failed a since-corrected number check, are history — kept,
   never edited, never counted as open findings of the current card.
4. READABILITY. The overview says HOW a thesis works in the source's words (not a taxonomy
   category); the review queue leads with the current cards' findings, the rest grouped below.

The articles are HYPOTHETICAL and labelled as such, built from the REAL extraction types. No
network, no model call.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from bs4 import BeautifulSoup

from tests.test_theme_intelligence_product_redesign import (
    AS_OF,
    PRICE,
    PUBLISHED,
    SECTORS,
    SLOWING,
    _cid,
    _ingested,
    _one,
)
from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence import cards, verify
from vinci.theme_intelligence.cards import REVEAL_JS, cited_claim_ids, render_html
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import (
    build_dashboard,
    card_context,
    line_findings,
    render_dashboard_html,
    research_verification,
    write_run_outputs,
)
from vinci.theme_intelligence.schemas import IssueSeverity, RunStatus, VerificationIssue
from vinci.theme_intelligence.verify import card_sentences


def _outputs(pipe: Pipeline, tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    out = write_run_outputs(pipe.store, pipe.store.runs()[-1].run_id, tmp_path / "out")
    return Path(out["dir"]), out


# --- 1. evidence navigation ---------------------------------------------------------------------

def test_every_evidence_link_on_a_card_reaches_its_evidence(tmp_path: Path) -> None:
    pipe = _ingested(tmp_path)
    run_dir, _ = _outputs(pipe, tmp_path)
    v = _one(pipe)
    cited = cited_claim_ids(v.content)
    key = {r.claim_id for r in v.content.s04_key_evidence}
    assert set(cited) - key, "the fixture must cite a claim outside the key rows"
    for name in ("TH-*[!t].html", "TH-*.print.html"):
        soup = BeautifulSoup(next((run_dir / "cards").glob(name)).read_text(), "html.parser")
        ids = {str(x["id"]) for x in soup.select("[id]")}
        hrefs = [str(a["href"])[1:] for a in soup.select('a[href^="#"]')]
        assert hrefs and [h for h in hrefs if h not in ids] == []  # no link to a missing target
        assert set(cited) <= ids  # every cited claim has its row
    soup = BeautifulSoup(next((run_dir / "cards").glob("TH-*[!t].html")).read_text(),
                         "html.parser")
    more = soup.select_one('[data-field="s04_key_evidence"] details.more')
    assert more is not None and not more.has_attr("open")  # collapsed on screen …
    for c in (_cid(pipe, PRICE), _cid(pipe, SLOWING)):
        row = more.select_one(f"tr#{c}")
        assert row is not None and "counter-evidence" in row.get_text(" ")  # … with its role
        assert soup.select_one(f'a.ref[href="#{c}"]') is not None  # and its citation links
    assert REVEAL_JS in str(soup)  # a link into a collapsed section opens it


def test_a_cited_id_with_no_record_is_printed_never_linked(tmp_path: Path) -> None:
    pipe = _ingested(tmp_path)
    (t,) = pipe.store.theses()
    v = _one(pipe)
    rc = card_context(pipe.store, t, v, generated="t")
    gone = _cid(pipe, SLOWING)
    rc.claims.pop(gone)  # the record is missing: the id must not become a dead link
    soup = BeautifulSoup(render_html(v.content, rc), "html.parser")
    ids = {str(x["id"]) for x in soup.select("[id]")}
    assert all(str(a["href"])[1:] in ids for a in soup.select('a[href^="#"]'))
    assert soup.select_one(f'a[href="#{gone}"]') is None
    assert any(x.get_text() == gone for x in soup.select(".ref.nolink"))


# --- 2. business groups the source names -----------------------------------------------------

TRACKER = "Our tracker sees HBM prices rising 50% in 2027 as suppliers hold firm on pricing."
BUYERS = "GPU and ASIC manufacturers are evaluating cheaper 8-Hi stacks for 2027 designs."
ELSEWHERE = "Memory makers elsewhere expanded capacity this year."


def _groups_case(tmp_path: Path) -> Pipeline:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo(slug="named-groups", publisher="Hypo Research A", published=PUBLISHED,
               blocks=[("paragraph", TRACKER), ("paragraph", BUYERS), ("paragraph", ELSEWHERE)])
    x = extraction(
        [claim("c1", "b001", TRACKER.split(" as ")[0], "HBM prices +50% in 2027", value=50,
               value_text="50%", unit="%", period="2027", kind="forecast", epistemic="forecast"),
         claim("c2", "b002", BUYERS.rstrip("."), "GPU/ASIC makers evaluate 8-Hi", period="2027")],
        [hyp("h1", "HBM prices rise on tight supply", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1", "c2"])])
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    return pipe


def test_business_groups_the_source_names_are_listed_apart_from_listed_exposures(
        tmp_path: Path) -> None:
    import json

    pipe = _groups_case(tmp_path)
    v = _one(pipe)
    f6 = next(f.value for f in v.priority.factors if f.factor_id == "F6_recognizable_exposures")
    assert f6 == "0 listed · 0 sector"  # the stored priority never reads a group
    run_dir, _ = _outputs(pipe, tmp_path)
    js = json.loads(next((run_dir / "cards").glob("TH-*.json")).read_text())
    groups = {g["name"]: g for g in js["named_business_groups"]}
    assert list(groups) == ["suppliers", "GPU and ASIC manufacturers"]  # verbatim, in order
    assert "makers" not in groups  # a paragraph holding no evidence of this thesis is not read
    assert groups["suppliers"]["excerpt"] == (  # a bare noun carries the words around it
        "…tracker sees HBM prices rising 50% in 2027 as suppliers hold firm on pricing.")
    assert groups["GPU and ASIC manufacturers"]["claim_ids"] == [
        c.claim_id for c in pipe.store.claims_for_article(pipe.store.articles()[0].article_id)
        if c.quote.startswith("GPU and ASIC")]
    why = " ".join(js["why_action"])
    assert "business groups only (suppliers; GPU and ASIC manufacturers), not companies" in why
    soup = BeautifulSoup(next((run_dir / "cards").glob("TH-*[!t].html")).read_text(),
                         "html.parser")
    s05 = soup.select_one('[data-field="s05_affected"]')
    assert s05 is not None
    heads = [x.get_text() for x in s05.select(".sub")]
    assert heads[1].startswith("Business groups the source names — not companies")
    assert heads.index(heads[1]) < heads.index("Stock exposures of this thesis (source-named "
                                               "companies)")
    d = build_dashboard(pipe.store, pipe.store.runs()[-1].run_id, cards={}, generated="t")
    (row,) = [r for rs in d.categories.values() for r in rs]
    assert row.groups == ["suppliers", "GPU and ASIC manufacturers"] and row.action == "WATCH"


@pytest.mark.parametrize(("text", "names"), [
    ("Rising input costs pressure suppliers this year.", ["suppliers"]),  # a verb is no name
    ("Many GPU and ASIC vendors will adopt it.", ["GPU and ASIC vendors"]),
    ("The HBM suppliers raised prices.", ["HBM suppliers"]),
    ("Prices rose on tight supply.", []),
])
def test_a_group_name_is_read_as_written_and_never_from_ordinary_words(
        text: str, names: list[str]) -> None:
    from vinci.theme_intelligence.schemas import Claim

    c = Claim.model_construct(claim_id="C-0000000000000a", article_id="A-1",
                              article_version_id="AV-1", block_id="b001", quote=text,
                              span_verified=True)
    assert [g.name for g in cards.named_groups([c], {("AV-1", "b001"): text})] == names
    unverified = c.model_copy(update={"span_verified": False})  # never read its paragraph
    assert cards.named_groups([unverified], {("AV-1", "b001"): text}) == ()


# --- 3. current vs historical review status ------------------------------------------------------

LABEL_FINDING = "Labelled MEASURED OBSERVATION but the line is conditional (test)"


def _relabelled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, finding: str) -> Pipeline:
    """A conditional bottom line stored as MEASURED OBSERVATION (the rules of the day) and
    questioned by the card review; the inference line questioned for its content. Then the
    re-grade relabels the conditional line SOURCE OPINION."""
    monkeypatch.setattr(cards, "capped_label", lambda prov, text: prov)
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("ingest", as_of=AS_OF)

    def review(card, claims):  # type: ignore[no-untyped-def]
        sents = card_sentences(card)
        return [VerificationIssue(
            issue_id=f"VI-test-{sid}", run_id=run.run_id, scope="card_sentence",
            ref_id=f"{card.header.thesis_id}:{sid}", severity=IssueSeverity.WARN,
            code="REVIEW_PARTIAL", detail=f"{sid}: {said} | {sents[sid][0][:100]!r}",
            created_at=datetime.now(tz=UTC))
            for sid, said in (("s01.0", finding), ("s01.1", "overstates the source (test)"))]

    pipe.engine.reviewer = review
    art = Hypo(slug="relabelled", publisher="Hypo Research A", published=PUBLISHED,
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
    pipe.engine.reviewer = None
    monkeypatch.undo()
    pipe.run_reassess(as_of=AS_OF)
    return pipe


def test_a_finding_on_a_label_a_later_version_corrected_is_history_not_open(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = _relabelled(tmp_path, monkeypatch, LABEL_FINDING)
    (t,) = pipe.store.theses()
    v = _one(pipe)
    assert v.version == 2
    _b, flagged, _c, resolved = line_findings(pipe.store, t.thesis_id, v)
    assert list(resolved) == ["s01.0"] and list(flagged) == ["s01.1"]  # content findings stay
    assert resolved["s01.0"][1] == LABEL_FINDING  # the review's words are kept
    run_dir, _ = _outputs(pipe, tmp_path)
    soup = BeautifulSoup(next((run_dir / "cards").glob("TH-*[!t].html")).read_text(),
                         "html.parser")
    line = soup.select_one("#L-s01-0")
    assert line is not None and "✓ Resolved" in line.get_text(" ")
    assert "UNRESOLVED REVIEW" not in line.get_text(" ")
    hdr = soup.select_one(".hdr .vline")
    assert hdr is not None and "Review required · 1 line(s)" in hdr.get_text(" ")
    assert "1 earlier review finding(s) resolved" in hdr.get_text(" ")
    d = build_dashboard(pipe.store, pipe.store.runs()[-1].run_id, cards={}, generated="t")
    dash = BeautifulSoup(render_dashboard_html(d), "html.parser")
    review = dash.select_one("#review")
    assert review is not None
    assert "lines withheld or questioned (1)" in review.select_one(".rq h3").get_text()
    hist = review.select("details.rqd")[-1]
    assert hist.summary is not None and "Resolved or historical (1)" in hist.summary.get_text()
    assert hist.select_one('a[href$="#L-s01-0"]') is not None
    assert "None." not in hist.get_text()


@pytest.mark.parametrize("finding", [
    "the span does not show the equal-weight index (test)",  # about content: not the label
    "Labelled FORECAST but conditional (test)",  # names a label the line never carried
])
def test_a_finding_that_does_not_name_the_corrected_label_stays_open(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, finding: str) -> None:
    pipe = _relabelled(tmp_path, monkeypatch, finding)
    (t,) = pipe.store.theses()
    _b, flagged, _c, resolved = line_findings(pipe.store, t.thesis_id, _one(pipe))
    assert resolved == {} and set(flagged) == {"s01.0", "s01.1"}


#: FAIL-SAFE resolution (review of PR #703, 2026-10-12): a finding naming the label AND objecting
#: to content was retired whole. Only a label-only finding is resolved by the relabel.
LABEL_ONLY = ("Labelled MEASURED OBSERVATION but 'could lift the index' is conditional opinion, "
              "stronger than warranted. The sector count is a cited observation; the inference is "
              "not measured (test).")
MIXED = ("Labelled MEASURED OBSERVATION but the line is conditional. The cited observations "
         "support only parts; the index effect is not measured (test).")
MIXED_SPAN = ("Labelled MEASURED OBSERVATION, and the 'equal-weight' clause is not in the cited "
              "span (test).")
AMBIGUOUS = ("Labelled MEASURED OBSERVATION but conditional. Check the wording against the sector "
             "chart (test).")


@pytest.mark.parametrize(("finding", "resolved_now"), [
    (LABEL_ONLY, True),  # every clause is about the label, or affirms support
    (MIXED, False),  # also: the cited spans support only part of the line
    (MIXED_SPAN, False),  # also: a clause not in the cited span
    (AMBIGUOUS, False),  # a clause that is neither about the label nor an affirmation
])
def test_only_a_label_only_finding_is_resolved_by_the_relabel(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, finding: str,
        resolved_now: bool) -> None:
    pipe = _relabelled(tmp_path, monkeypatch, finding)
    (t,) = pipe.store.theses()
    v = _one(pipe)
    _b, flagged, _c, resolved = line_findings(pipe.store, t.thesis_id, v)
    assert ("s01.0" in resolved) is resolved_now and ("s01.0" in flagged) is not resolved_now
    kept = resolved["s01.0"][1] if resolved_now else flagged["s01.0"]
    assert kept == finding  # the reviewer's words, whole, either way
    v1 = pipe.store.thesis_version(t.thesis_id, 1)
    assert v1 is not None and any(  # the original finding stands in its run, unedited
        i.detail.startswith(f"s01.0: {finding} | ") for i in pipe.store.issues(run_id=v1.run_id))
    run_dir, _ = _outputs(pipe, tmp_path)
    soup = BeautifulSoup(next((run_dir / "cards").glob("TH-*[!t].html")).read_text(),
                         "html.parser")
    line = soup.select_one("#L-s01-0")
    assert line is not None
    text = line.get_text(" ")
    if resolved_now:
        assert "✓ Resolved" in text and "UNRESOLVED REVIEW" not in text
    else:
        assert "UNRESOLVED REVIEW" in text and "✓ Resolved" not in text
        assert " ".join(finding.split()) in " ".join(text.split())  # shown whole on the line


@pytest.mark.parametrize(("said", "scope"), [
    ("Labelled MEASURED OBSERVATION but conditional", "label_only"),
    ("Labelled MEASURED OBSERVATION — stronger label than content, which is opinion", "label_only"),
    ("Labelled MEASURED OBSERVATION; the figures are supported; the inference is not measured",
     "label_only"),
    ("Labelled MEASURED OBSERVATION; it overstates the cited growth", "mixed"),
    ("Labelled MEASURED OBSERVATION; the cited spans support only parts", "mixed"),
    ("Labelled MEASURED OBSERVATION; the 2027 date is missing", "mixed"),
    ("Labelled MEASURED OBSERVATION; the figures are supported only for 2026", "mixed"),
    ("Labelled MEASURED OBSERVATION; the figures are supported but partly", "ambiguous"),
    ("Labelled MEASURED OBSERVATION. Revisit later.", "ambiguous"),
    ("The span does not show the index effect", "not_label"),
])
def test_a_finding_is_read_fail_safe_from_its_own_words(said: str, scope: str) -> None:
    from vinci.theme_intelligence.report import finding_scope

    assert finding_scope(said, "MEASURED OBSERVATION") == scope


def _figure_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: float) -> Pipeline:
    """"five of the 11" read under the number rule of the day (digits only, beside digits): the
    claim fails, so figure '11' is open as `verification_failed`. Today's rule is then back."""
    monkeypatch.setattr(verify, "word_numbers", lambda text: [])
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    art = Hypo(slug=f"sector-count-{value:g}", publisher="Hypo Research A", published=PUBLISHED,
               blocks=[("paragraph", SECTORS)])
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", SECTORS.rstrip("."), "earnings rose in 5 of 11 sectors",
               value=value, value_text="five of the 11", unit="sectors", period="2Q26")],
        [hyp("h1", "Earnings broaden", node="macro_market", mechanism="earnings_revision",
             supporting=["c1"])]),
        as_of=AS_OF, publisher=art.publisher,
        completeness={"figure_reviews": [], "block_reviews": []})
    pipe.finish_run(RunStatus.SUCCEEDED)
    monkeypatch.undo()
    return pipe


@pytest.mark.parametrize(("value", "historical"), [(5, True), (7, False)])
def test_a_figure_that_failed_a_since_corrected_check_is_history_not_an_open_gap(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: float, historical: bool) -> None:
    pipe = _figure_case(tmp_path, monkeypatch, value)
    run = pipe.store.runs()[-1]
    (rep,) = pipe.store.completeness_for_run(run.run_id)
    f11 = next(f for f in rep.figures if f.figure == "11")
    assert f11.status == "uncaptured" and f11.open_cause == "verification_failed"  # recorded
    rv = research_verification(pipe.store, run)
    assert rv["figures_open"] >= 1 and rv["status"] == "INCOMPLETE"  # the record is unchanged
    assert rv["figures_superseded"] == (1 if historical else 0)
    plain = " ".join(rv["open_items_plain"])
    sup = " ".join(rv["superseded_items_plain"])
    assert ("figure '11'" in sup) is historical and ("figure '11'" in plain) is not historical
    if historical:
        assert "today's check passes it" in sup and "not used as evidence" in sup
    d = build_dashboard(pipe.store, run.run_id, cards={}, generated="t")
    soup = BeautifulSoup(render_dashboard_html(d), "html.parser")
    stat = soup.select_one('.summary a.stat[href="#review"] b')
    assert stat is not None and stat.get_text() == "0"  # no current-card finding
    groups = {g.summary.get_text().split(" (")[0]: g.summary.get_text()
              for g in soup.select("#review details.rqd") if g.summary}
    assert ("Resolved or historical (1)" in groups["Resolved or historical"]) is historical
    assert ("Incomplete sources (0)" in groups["Incomplete sources"]) is historical


# --- 4. readability: how it works, the review queue first ------------------------------------

LONG = ("The cited span supports the price forecast but not the mechanism the line states: "
        "nothing in it says supply stays tight because next-generation yields ramp slowly, and "
        "the pool holds no span that does (test).")


def _stated_case(tmp_path: Path, *, stated: bool, flagged: bool,
                 finding: str = "not in the span (test)") -> Pipeline:
    """A thesis whose first earnings step the SOURCE states (or not), optionally questioned by
    the card review."""
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("ingest", as_of=AS_OF)
    if flagged:
        def review(card, claims):  # type: ignore[no-untyped-def]
            text = card_sentences(card)["s03.0"][0]
            return [VerificationIssue(
                issue_id="VI-test-s03", run_id=run.run_id, scope="card_sentence",
                ref_id=f"{card.header.thesis_id}:s03.0", severity=IssueSeverity.WARN,
                code="REVIEW_PARTIAL", detail=f"s03.0: {finding} | {text[:100]!r}",
                created_at=datetime.now(tz=UTC))]

        pipe.engine.reviewer = review
    art = Hypo(slug=f"stated-{stated}-{flagged}", publisher="Hypo Research A",
               published=PUBLISHED, blocks=[("paragraph", TRACKER)])
    prov = "source_stated" if stated else "model_inference"
    x = extraction(
        [claim("c1", "b001", TRACKER.split(" as ")[0], "HBM prices +50% in 2027", value=50,
               value_text="50%", unit="%", period="2027", kind="forecast", epistemic="forecast")],
        [hyp("h1", "HBM prices rise on tight supply", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1"],
             step_list=[{"step": "pricing", "text": "Tight supply lifts HBM prices 50% in 2027",
                         "provenance": prov, "claim_ids": ["c1"] if stated else []}])])
    ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    pipe.engine.reviewer = None
    return pipe


@pytest.mark.parametrize(("stated", "flagged", "expect"), [
    (True, False, "Tight supply lifts HBM prices 50% in 2027"),  # the source's own step
    (True, True, "Category: "),  # a questioned step is never the summary
    (False, False, "Category: "),  # no step stated by the source: the category, said to be one
])
def test_the_overview_says_how_it_works_in_the_source_words(
        tmp_path: Path, stated: bool, flagged: bool, expect: str) -> None:
    pipe = _stated_case(tmp_path, stated=stated, flagged=flagged)
    d = build_dashboard(pipe.store, pipe.store.runs()[-1].run_id, cards={}, generated="t")
    (row,) = [r for rs in d.categories.values() for r in rs]
    assert row.mechanism.startswith(expect)
    if expect.startswith("Category"):
        assert row.mechanism == "Category: Contract or average selling price moves from the " \
                                "supply-demand balance"


def test_the_review_queue_leads_with_the_current_cards_and_groups_the_rest(
        tmp_path: Path) -> None:
    pipe = _stated_case(tmp_path, stated=True, flagged=True, finding=LONG)
    d = build_dashboard(pipe.store, pipe.store.runs()[-1].run_id, cards={}, generated="t")
    soup = BeautifulSoup(render_dashboard_html(d), "html.parser")
    (item,) = soup.select("#review .rq li li")  # one line per finding …
    said = item.get_text(" ", strip=True).split(" — ", 1)[1]
    assert said.endswith("…") and said[:-1].strip() in LONG and LONG not in item.get_text()
    run_dir, _ = _outputs(pipe, tmp_path)  # … whole on its card line
    card = BeautifulSoup(next((run_dir / "cards").glob("TH-*[!t].html")).read_text(),
                         "html.parser")
    line = card.select_one("#L-s03-0")
    assert line is not None and LONG in line.get_text(" ")
    review = soup.select_one("#review")
    assert review is not None
    first = review.find(["div", "details"], recursive=False)
    assert first is not None and first.name == "div" and "rq" in first["class"]  # current first
    assert "lines withheld or questioned (1)" in first.get_text()
    groups = review.select("details.rqd")
    assert [g.summary.get_text().split(" (")[0] for g in groups if g.summary] == [
        "Incomplete sources", "Background alerts", "Resolved or historical"]
    assert not any(g.has_attr("open") for g in groups)  # collapsed on screen …
    printed = BeautifulSoup(render_dashboard_html(d, print_mode=True), "html.parser")
    assert all(g.has_attr("open") for g in printed.select("#review details.rqd"))  # … in print
    stat = soup.select_one('.summary a.stat[href="#review"] b')
    assert stat is not None and stat.get_text() == "1"  # the summary counts the current cards


def test_a_finding_naming_a_label_the_line_always_carried_stays_open(tmp_path: Path) -> None:
    """The line was SOURCE OPINION when reviewed and is now: nothing was corrected, so a finding
    that names that label ("Labelled SOURCE OPINION but …") is still open — whatever the version."""
    from vinci.theme_intelligence.engine import SentenceCorrection

    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("ingest", as_of=AS_OF)

    def review(card, claims):  # type: ignore[no-untyped-def]
        text = card_sentences(card)["s01.0"][0]
        return [VerificationIssue(
            issue_id="VI-test-s01", run_id=run.run_id, scope="card_sentence",
            ref_id=f"{card.header.thesis_id}:s01.0", severity=IssueSeverity.WARN,
            code="REVIEW_PARTIAL", detail=f"s01.0: Labelled SOURCE OPINION but it overstates "
                                          f"(test) | {text[:100]!r}",
            created_at=datetime.now(tz=UTC))]

    pipe.engine.reviewer = review
    art = Hypo(slug="always-opinion", publisher="Hypo Research A", published=PUBLISHED,
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
    pipe.engine.reviewer = None
    v1 = _one(pipe)
    assert card_sentences(v1.content)["s01.0"][1] == "SOURCE OPINION"  # capped at ingestion
    c1 = pipe.store.claims_for_article(pipe.store.articles()[0].article_id)[0].claim_id
    pipe.run_reassess(as_of=AS_OF, corrections=[SentenceCorrection(  # a new version, s01.0 kept
        thesis_id=v1.thesis_id, sentence_id="s01.1", text="Earnings rose in five of the 11 "
        "sectors", claim_ids=(c1,), reason="test")])
    v2 = _one(pipe)
    assert v2.version == 2 and card_sentences(v2.content)["s01.0"] == \
        card_sentences(v1.content)["s01.0"]
    _b, flagged, _c, resolved = line_findings(pipe.store, v2.thesis_id, v2)
    assert resolved == {} and "s01.0" in flagged
