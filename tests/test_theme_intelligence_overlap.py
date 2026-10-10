"""§8 overlap and change-management tests — the registry's identity, dedup and versioning rules.

Every article here is a HYPOTHETICAL test fixture (title "[HYPOTHETICAL TEST FIXTURE] …", URL
`https://example.test/hypothetical/…`), built from the REAL extraction types. Company rows come
from the AUTHENTIC frozen SEC subset; nothing is resolved from a made-up map.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from tests.theme_intelligence_support import (
    JPM_AS_OF,
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    ingest_jpm,
    make_pipeline,
    mention,
    table_counts,
)
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import (
    card_context,
    render_html,
    render_json,
    write_run_outputs,
)
from vinci.theme_intelligence.schemas import (
    ChangeClass,
    EvidenceDirection,
    IssueSeverity,
    LinkRole,
    RelationType,
    ResearchAction,
    RetrievalState,
    RunStatus,
    ThesisStatus,
    VerificationIssue,
)
from vinci.theme_intelligence.store import Store

W1 = date(2026, 3, 2)
W2 = date(2026, 3, 9)

DRAM_SENTENCE = ("DRAM contract prices rose 15% quarter over quarter in 1Q26, according to "
                 "TrendForce, as AI servers absorbed supply.")


def _memory_article(slug: str, publisher: str, published: date,
                    extra: list[tuple[str, str]] | None = None) -> Hypo:
    return Hypo(slug=slug, publisher=publisher, published=published, blocks=[
        ("paragraph", DRAM_SENTENCE),
        ("paragraph", "Micron Technology said lead times for high-bandwidth memory now stretch "
                      "into 2027."),
        *(extra or [])])


def _memory_extraction(*, more_claims: list[dict] | None = None,
                       more_support: list[str] | None = None,
                       catalyst: list[str] | None = None) -> dict:
    c1 = claim("c1", "b001", "DRAM contract prices rose 15% quarter over quarter in 1Q26, "
                             "according to TrendForce", "DRAM contract prices rose 15% QoQ in 1Q26",
               metric="DRAM contract price change", value=15, value_text="15%", unit="%",
               period="1Q26", scope="DRAM contract", source="TrendForce")
    return extraction(
        [c1, *(more_claims or [])],
        [hyp("h1", "AI demand tightens DRAM pricing", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1", *(more_support or [])],
             catalyst=catalyst, affected=[("Micron Technology", "potential_beneficiary")])],
        [mention("Micron Technology", "b002", "Micron Technology said lead times for "
                                              "high-bandwidth memory now stretch into 2027",
                 ticker="MU")])


@pytest.fixture()
def pipe(tmp_path: Path) -> Pipeline:
    p = make_pipeline(tmp_path)
    p.start_run("fixture", as_of=W2)
    return p


def _memory_thesis(pipe: Pipeline):
    ts = [t for t in pipe.store.theses() if t.key_node == "ai_infrastructure.memory"]
    assert len(ts) == 1
    return ts[0]


# --- 1. re-ingest --------------------------------------------------------------------------------

def test_reingesting_the_same_article_writes_nothing(pipe: Pipeline) -> None:
    a = _memory_article("dram-a", "Hypo Research A", W1)
    first = ingest(pipe, a.doc(), _memory_extraction(), as_of=W1, publisher=a.publisher)
    assert first.status == "PROCESSED"
    before = table_counts(pipe)
    action = pipe.store.thesis_version(_memory_thesis(pipe).thesis_id, 1).priority
    again = ingest(pipe, a.doc(), _memory_extraction(), as_of=W1, publisher=a.publisher)
    assert again.status == "ALREADY_INGESTED"
    assert table_counts(pipe) == before  # no new records of any kind
    t = _memory_thesis(pipe)
    assert t.current_version == 1
    after = pipe.store.thesis_version(t.thesis_id, 1)
    assert after is not None and after.priority == action  # no changed priority
    assert not [c for c in pipe.store.contributions(t.thesis_id)
                if c.contribution is ChangeClass.INDEPENDENT_CONFIRMATION]  # no false confirm


# --- 2. two publishers, one upstream source ------------------------------------------------------

def test_two_publishers_repeating_one_source_are_one_origin(pipe: Pipeline) -> None:
    a = _memory_article("dram-a", "Hypo Research A", W1)
    b = Hypo(slug="dram-b", publisher="Hypo Daily B", published=W1, blocks=[
        ("paragraph", "Citing TrendForce, the newsletter notes DRAM contract prices rose 15% "
                      "quarter over quarter in 1Q26."),
        ("paragraph", "Micron Technology said lead times for high-bandwidth memory now stretch "
                      "into 2027.")])
    ingest(pipe, a.doc(), _memory_extraction(), as_of=W1, publisher=a.publisher)
    t = _memory_thesis(pipe)
    v1 = pipe.store.thesis_version(t.thesis_id, 1)
    assert v1 is not None
    xb = _memory_extraction()
    xb["claims"][0].update(quote="DRAM contract prices rose 15% quarter over quarter in 1Q26",
                           statement="DRAM contract prices rose 15% QoQ in 1Q26 (via "
                                     "TrendForce)")
    res = ingest(pipe, b.doc(), xb, as_of=W1, publisher=b.publisher)
    assert res.status == "PROCESSED"
    assert len(pipe.store.theses()) == 1  # ONE thesis
    t = _memory_thesis(pipe)
    assert t.current_version == 1  # no new version: nothing material
    contribs = pipe.store.contributions(t.thesis_id)
    assert sorted(c.article_id for c in contribs) == sorted({c.article_id for c in contribs})
    assert len(contribs) == 2  # two article attributions
    assert [c.contribution for c in contribs if c.version is None] == [ChangeClass.REPEATED]
    origins = {pipe.store.claim(lk.claim_id).origin_id
               for lk in pipe.store.links(t.thesis_id) if lk.role is LinkRole.SUPPORTS}
    assert len(origins) == 1  # ONE underlying evidence origin
    assert res.outcomes[0].evidence_direction is EvidenceDirection.UNCHANGED
    assert res.outcomes[0].action is v1.priority.research_action  # no artificial strength
    # the card shows one evidence row, with the repeat as an attribution
    row = pipe.store.thesis_version(t.thesis_id, 1).content.s04_key_evidence
    assert len([r for r in row if r.value_text == "15%"]) == 1


# --- 3. independent evidence a week later --------------------------------------------------------

def test_independent_evidence_next_week_versions_the_same_thesis(pipe: Pipeline) -> None:
    a = _memory_article("dram-a", "Hypo Research A", W1)
    ingest(pipe, a.doc(), _memory_extraction(), as_of=W1, publisher=a.publisher)
    tid = _memory_thesis(pipe).thesis_id
    c = Hypo(slug="hbm-orders", publisher="Hypo Wire C", published=W2, blocks=[
        ("paragraph", "Samsung Electronics said it received orders worth $2 billion for HBM "
                      "supply in 2027, according to the company's statement."),
        ("paragraph", "Micron Technology said lead times for high-bandwidth memory now stretch "
                      "into 2027.")])
    order = claim("c2", "b001", "Samsung Electronics said it received orders worth $2 billion "
                                "for HBM supply in 2027", "Samsung booked $2bn of 2027 HBM orders",
                  kind="event", metric="HBM order intake", value=2, value_text="$2 billion",
                  unit="$bn", period="2027", scope="Samsung HBM", source="Samsung Electronics")
    xc = _memory_extraction(more_claims=[order], more_support=["c2"])
    xc["claims"] = [order]  # this article does not repeat the TrendForce figure
    xc["hypotheses"][0]["supporting_claim_ids"] = ["c2"]
    xc["hypotheses"][0]["bottom_line_fact"]["claim_ids"] = ["c2"]
    res = ingest(pipe, c.doc(), xc, as_of=W2, publisher=c.publisher)
    t = _memory_thesis(pipe)
    assert t.thesis_id == tid and t.current_version == 2  # same id, new version
    v2 = pipe.store.thesis_version(tid, 2)
    assert v2 is not None and v2.prior_content_sha == pipe.store.thesis_version(
        tid, 1).content_sha
    assert res.outcomes[0].contribution is ChangeClass.NEW
    fields = {d.field_id for d in v2.diffs}
    assert fields and fields <= {"s01_bottom_line", "s02_what_changed", "s04_key_evidence",
                                 "s06_why_now.catalyst_window", "header.research_action",
                                 "s05_affected.companies"}  # a NARROW diff
    assert "s05_affected.companies" not in fields  # Micron was already there
    assert v2.priority.change_reason  # any priority change is explained


# --- 4. later contradiction: a moved launch date -------------------------------------------------

def _launch(slug: str, published: date, when: str, verb: str) -> tuple[Hypo, dict]:
    text = f"Vendor Corp {verb} the commercial launch of its HBM4 stacks to {when}."
    art = Hypo(slug=slug, publisher="Hypo Research A", published=published,
               blocks=[("paragraph", text)])
    x = extraction(
        [claim("c1", "b001", text.rstrip("."), f"HBM4 commercial launch {when}", kind="event",
               metric="commercial launch", value_text=when, period=when,
               scope="Vendor Corp HBM4", source="Vendor Corp")],
        [hyp("h1", "HBM4 ramp lifts memory pricing", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1"], catalyst=["c1"])])
    return art, x


def test_later_delay_is_a_timing_change_with_both_claims_kept(pipe: Pipeline) -> None:
    a, xa = _launch("launch-on-time", W1, "2Q26", "scheduled")
    ingest(pipe, a.doc(), xa, as_of=W1, publisher=a.publisher)
    tid = _memory_thesis(pipe).thesis_id
    b, xb = _launch("launch-delayed", W2, "4Q26", "delayed")
    res = ingest(pipe, b.doc(), xb, as_of=W2, publisher=b.publisher)
    assert res.outcomes[0].contribution is ChangeClass.TIMING_CHANGE
    assert res.outcomes[0].evidence_direction in (EvidenceDirection.WEAKER,
                                                   EvidenceDirection.MIXED)
    held = [pipe.store.claim(lk.claim_id) for lk in pipe.store.links(tid)]
    assert sorted(c.period for c in held if c) == ["2Q26", "4Q26"]  # both preserved
    v2 = pipe.store.thesis_version(tid, 2)
    assert v2 is not None
    item = next(i for i in v2.content.s02_what_changed.items
                if i.change_class is ChangeClass.TIMING_CHANGE)
    assert "2Q26" in item.text and "4Q26" in item.text  # the changed reason is logged
    assert "held:" in item.text  # scope / definition of both claims is shown side by side
    events = {e.event_type for e in pipe.store.events(thesis_id=tid)}
    assert events & {"CHALLENGED", "DOWNGRADED"}


# --- 5. siblings, parent / child -----------------------------------------------------------------

def test_memory_optics_and_grid_are_siblings_never_merged(pipe: Pipeline) -> None:
    art = Hypo(slug="three-bottlenecks", publisher="Hypo Research A", published=W1, blocks=[
        ("paragraph", "DRAM contract prices rose 15% in 1Q26."),
        ("paragraph", "800G optical transceiver shipments doubled in 2025."),
        ("paragraph", "Utility interconnection queues reached 2,600 GW in 2025.")])
    x = extraction(
        [claim("c1", "b001", "DRAM contract prices rose 15% in 1Q26", "DRAM +15% in 1Q26",
               metric="DRAM price", value=15, value_text="15%", unit="%", period="1Q26"),
         claim("c2", "b002", "800G optical transceiver shipments doubled in 2025",
               "800G shipments doubled", metric="800G shipments growth", value_text="doubled",
               period="2025"),
         claim("c3", "b003", "Utility interconnection queues reached 2,600 GW in 2025",
               "Queues 2,600 GW", metric="interconnection queue", value=2600,
               value_text="2,600 GW", unit="GW", period="2025")],
        [hyp("h1", "Memory pricing upcycle", node="ai_infrastructure.memory",
             mechanism="pricing_cycle", supporting=["c1"]),
         hyp("h2", "Optics volume ramp", node="ai_infrastructure.optical_networking",
             mechanism="demand_volume_shift", supporting=["c2"]),
         hyp("h3", "Grid bottleneck", node="ai_infrastructure.power_grid",
             mechanism="supply_constraint", supporting=["c3"])])
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher)
    ts = pipe.store.theses()
    assert sorted(t.key_node for t in ts) == ["ai_infrastructure.memory",
                                              "ai_infrastructure.optical_networking",
                                              "ai_infrastructure.power_grid"]
    rels = pipe.store.relations()
    assert len(rels) == 3 and {r.relation for r in rels} == {RelationType.SIBLING}
    # one article, many theses — each links back to the same article id
    assert len({c.article_id for c in pipe.store.contributions()}) == 1
    assert len(pipe.store.contributions()) == 3


# --- 6. competing hypotheses ---------------------------------------------------------------------

def test_bullish_recovery_and_bearish_disruption_are_linked_competitors(
        tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=W1)
    ingest_jpm(pipe)
    bull = next(t for t in pipe.store.theses() if t.key_node.startswith("software"))
    bear = Hypo(slug="seat-compression", publisher="Hypo Research B", published=W1, blocks=[
        ("paragraph", "Seat counts at large SaaS vendors fell 8% in 4Q25 as coding agents "
                      "replaced junior developer licenses.")])
    x = extraction(
        [claim("c1", "b001", "Seat counts at large SaaS vendors fell 8% in 4Q25",
               "SaaS seat counts -8% in 4Q25", metric="SaaS seat count change", value=8,
               value_text="8%", unit="%", period="4Q25", scope="large SaaS vendors")],
        [hyp("h1", "Agents erode SaaS seat revenue", node=bull.key_node,
             mechanism="disruption_revenue_erosion", direction="negative", supporting=["c1"])])
    ingest(pipe, bear.doc(), x, as_of=W1, publisher=bear.publisher)
    softs = [t for t in pipe.store.theses() if t.key_node == bull.key_node]
    assert len(softs) == 2  # NOT mashed into one thesis
    rel = [r for r in pipe.store.relations(bull.thesis_id)
           if r.relation is RelationType.COMPETING]
    assert len(rel) == 1
    inc = pipe.store.thesis(bull.thesis_id)
    assert inc is not None and inc.current_version == 2  # the incumbent is challenged
    contra = [lk for lk in pipe.store.links(bull.thesis_id)
              if lk.role is LinkRole.CONTRADICTS and lk.first_version == 2]
    assert contra and all(lk.change_class is ChangeClass.CONTRADICTORY for lk in contra)


# --- 7. a sector-only paper ----------------------------------------------------------------------

def test_a_sector_only_paper_adds_no_company(pipe: Pipeline) -> None:
    art = Hypo(slug="sector-only", publisher="Hypo Research A", published=W1, blocks=[
        ("paragraph", "Semiconductor equipment makers should see orders rise 12% in 2026 as "
                      "foundries add capacity.")])
    x = extraction(
        [claim("c1", "b001", "Semiconductor equipment makers should see orders rise 12% in 2026",
               "Equipment orders +12% in 2026", epistemic="forecast",
               metric="equipment order growth", value=12, value_text="12%", unit="%",
               period="2026")],
        [hyp("h1", "Fab capacity adds lift equipment orders",
             node="ai_infrastructure.semicap_foundry", mechanism="demand_volume_shift",
             supporting=["c1"], affected=[("ASML", "potential_beneficiary")])],
        # the model "helpfully" names a company the paper never mentions
        [mention("ASML", "b001", "ASML will benefit", ticker="ASML")])
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher)
    t = pipe.store.theses()[0]
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None
    av = v.content.s05_affected
    assert av.companies == () and av.instruments == () and av.also_named == ()
    codes = {i.code for i in pipe.store.issues()}
    assert "UNSUPPORTED_ENTITY" in codes or "MENTION_NOT_IN_TEXT" in codes or \
        any("ASML" in i.detail for i in pipe.store.issues())


# --- 8. a paper citing an earlier study ----------------------------------------------------------

def test_a_cited_earlier_study_counts_once(pipe: Pipeline) -> None:
    study = "a 2025 survey by Hypo Consulting found 40% of firms piloting AI agents"
    a = Hypo(slug="study-a", publisher="Hypo Research A", published=W1,
             blocks=[("paragraph", f"Adoption is broadening: {study}.")])
    b = Hypo(slug="study-b", publisher="Hypo Daily B", published=W2,
             blocks=[("paragraph", f"As {study}, budgets are moving.")])

    def x() -> dict:
        return extraction(
            [claim("c1", "b001", study, "40% of firms piloting AI agents (2025 survey)",
                   metric="share of firms piloting AI agents", value=40, value_text="40%",
                   unit="%", period="2025", scope="firms", source="Hypo Consulting survey")],
            [hyp("h1", "Agent adoption broadens", node="ai_adoption",
                 mechanism="margin_expansion_adoption", supporting=["c1"])])
    ingest(pipe, a.doc(), x(), as_of=W1, publisher=a.publisher)
    res = ingest(pipe, b.doc(), x(), as_of=W2, publisher=b.publisher)
    t = pipe.store.theses()[0]
    assert t.current_version == 1
    assert res.outcomes[0].contribution is ChangeClass.REPEATED
    assert res.outcomes[0].evidence_direction is EvidenceDirection.UNCHANGED


# --- 9-11. missing fields, partial / paywalled, changed URL --------------------------------------

def test_missing_author_date_and_figure_stay_unknown(pipe: Pipeline) -> None:
    art = Hypo(slug="no-metadata", publisher="Hypo Research A", published=None, author=None,
               blocks=[("paragraph", "Optical module demand is accelerating into 2026.")])
    x = extraction(
        [claim("c1", "b001", "Optical module demand is accelerating into 2026",
               "Optical demand accelerating", kind="assertion", epistemic="opinion"),
         # a figure the text does not state
         claim("c2", "b001", "Optical module demand is accelerating", "Optical demand +35%",
               metric="optical demand growth", value=35, value_text="35%", unit="%")],
        [hyp("h1", "Optics demand accelerates", node="ai_infrastructure.optical_networking",
             mechanism="demand_volume_shift", supporting=["c1", "c2"])])
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher)
    a = pipe.store.articles()[0]
    assert a.authors == () and a.authors_status.value == "UNKNOWN"
    assert a.published_at is None and a.published_status.value == "UNKNOWN"
    bad = [c for c in pipe.store.claims_for_article(a.article_id) if c.value_text == "35%"]
    assert bad and bad[0].number_verified is False
    linked = {lk.claim_id for t in pipe.store.theses() for lk in pipe.store.links(t.thesis_id)}
    assert bad[0].claim_id not in linked  # never evidence
    t = pipe.store.theses()[0]
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None
    html = render_html(v.content, card_context(pipe.store, t, v, generated="t"))
    assert "UNKNOWN" in html  # author and date print as UNKNOWN, never invented


def test_partial_retrieval_never_claims_full_verification(pipe: Pipeline) -> None:
    art = Hypo(slug="paywalled", publisher="Hypo Research A", published=W1,
               state=RetrievalState.PARTIAL, blocks=[
                   ("paragraph", "Hyperscaler capex guidance rose 30% for 2026, the preview "
                                 "says, before the paywall.")])
    x = extraction(
        [claim("c1", "b001", "Hyperscaler capex guidance rose 30% for 2026",
               "Capex guidance +30% for 2026", epistemic="forecast", metric="capex guidance",
               value=30, value_text="30%", unit="%", period="2026")],
        [hyp("h1", "Capex lifts AI infrastructure", node="ai_infrastructure.hyperscaler_capex",
             mechanism="capex_spending_cycle", supporting=["c1"], dislocation=["c1"],
             affected=[("Microsoft", "spending_customer")])],
        [mention("Microsoft", "b001", "Hyperscaler capex guidance", ticker="MSFT")])
    res = ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher)
    assert res.status == "PARTIAL_PROCESSED"
    av = pipe.store.article_versions(res.article_id or "")[0]
    assert av.retrieval_state is RetrievalState.PARTIAL
    assert "PARTIAL_RETRIEVAL" in {i.code for i in pipe.store.issues()}
    t = pipe.store.theses()[0]
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None and v.priority.research_action is not ResearchAction.RESEARCH_NOW
    assert any("retrieval PARTIAL" in r for r in v.priority.rules_fired)


def test_same_body_under_a_changed_url_is_one_article(pipe: Pipeline) -> None:
    a = _memory_article("dram-a", "Hypo Research A", W1)
    ingest(pipe, a.doc(), _memory_extraction(), as_of=W1, publisher=a.publisher)
    moved = a.doc()
    moved.canonical_url = "https://example.test/hypothetical/dram-a-moved"
    before = table_counts(pipe)
    res = ingest(pipe, moved, _memory_extraction(), as_of=W1, publisher=a.publisher)
    assert res.status == "DUPLICATE_CONTENT"
    assert table_counts(pipe) == before


# --- 12-13. stale series, multiple as-of dates, look-ahead ---------------------------------------

def test_a_stale_series_is_labelled_on_the_card(pipe: Pipeline) -> None:
    art = Hypo(slug="stale", publisher="Hypo Research A", published=W1, blocks=[
        ("paragraph", "Server shipments grew 12% according to the survey."),
        ("chart_source", "Source: Hypo Survey. Data as of June 30, 2024.")])
    x = extraction(
        [claim("c1", "b001", "Server shipments grew 12%", "Server shipments +12%",
               metric="server shipment growth", value=12, value_text="12%", unit="%",
               measured_as_of="2024-06-30", as_of_block="b002", source="Hypo Survey")],
        [hyp("h1", "Server demand", node="ai_infrastructure.compute_semis",
             mechanism="demand_volume_shift", supporting=["c1"])])
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher)
    c = pipe.store.claims_for_article(pipe.store.articles()[0].article_id)[0]
    assert any(q.startswith("stale series") for q in c.qualifiers)
    assert "STALE_SERIES" in {i.code for i in pipe.store.issues()}
    t = pipe.store.theses()[0]
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None
    assert any("STALE series" in it.text for it in v.content.s02_what_changed.items)


def test_multiple_as_of_dates_no_lookahead_no_forecast_as_actual(pipe: Pipeline) -> None:
    art = Hypo(slug="two-dates", publisher="Hypo Research A", published=date(2026, 2, 1),
               blocks=[("paragraph", "NTM EPS for the group is $12.40 and revenue grew 9%."),
                       ("chart_source", "Data as of January 15, 2026."),
                       ("chart_source", "Data as of February 5, 2026.")])
    x = extraction(
        [claim("c1", "b001", "NTM EPS for the group is $12.40", "NTM EPS $12.40",
               epistemic="actual", metric="NTM EPS", value=12.4, value_text="$12.40",
               unit="$", period="NTM", measured_as_of="2026-01-15", as_of_block="b002"),
         claim("c2", "b001", "revenue grew 9%", "Revenue +9%", metric="revenue growth",
               value=9, value_text="9%", unit="%", measured_as_of="2026-02-05",
               as_of_block="b003")],
        [hyp("h1", "Group earnings", node="ai_infrastructure.compute_semis",
             mechanism="demand_volume_shift", supporting=["c1", "c2"])])
    ingest(pipe, art.doc(), x, as_of=date(2026, 2, 1), publisher=art.publisher)
    cl = {c.value_text: c for c in pipe.store.claims_for_article(
        pipe.store.articles()[0].article_id)}
    assert cl["$12.40"].epistemic.value == "forecast"  # NTM is never an actual
    assert cl["$12.40"].measured_as_of == date(2026, 1, 15)
    assert cl["9%"].span_verified is False  # dated after the run's as-of: look-ahead
    assert "LOOKAHEAD_FIGURE" in {i.code for i in pipe.store.issues()}


def test_an_article_published_after_the_as_of_is_refused(pipe: Pipeline) -> None:
    a = _memory_article("future", "Hypo Research A", date(2026, 4, 1))
    res = ingest(pipe, a.doc(), _memory_extraction(), as_of=W1, publisher=a.publisher)
    assert res.status == "LOOKAHEAD"
    assert pipe.store.theses() == []


# --- 14-16. no material change, long facts, RESEARCH NOW without valuation -----------------------

def test_a_long_critical_fact_survives_in_full(pipe: Pipeline) -> None:
    long = ("The operator disclosed that its 2027 capacity plan, which spans eleven sites across "
            "three regions and assumes a 40% increase in liquid-cooled racks, depends on "
            "transformer deliveries that are now quoted at 30 months, and that any slip would "
            "move first revenue from those sites from 2Q27 to 2028 — a condition it called the "
            "single largest risk to its guidance, ahead of chip supply, power prices and "
            "permitting, all of which it described as manageable within the plan.")
    art = Hypo(slug="long-fact", publisher="Hypo Research A", published=W1,
               blocks=[("paragraph", long)])
    x = extraction(
        [claim("c1", "b001", long[:-1], long, kind="assertion", epistemic="actual")],
        [hyp("h1", "Transformer lead times gate AI capacity", node="ai_infrastructure.power_grid",
             mechanism="supply_constraint", supporting=["c1"])])
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher)
    t = pipe.store.theses()[0]
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None
    rc = card_context(pipe.store, t, v, generated="t")
    assert long[:-1] in render_html(v.content, rc, print_mode=True)  # the printable card
    assert any(long[:-1] in r["quote"] for r in render_json(v.content, rc)["card"][
        "s04_key_evidence"])
    assert pipe.store.claims_for_article(t and pipe.store.articles()[0].article_id)[0] \
        .statement == long  # the evidence ledger


def test_research_now_without_valuation_is_research_only(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    for t in pipe.store.theses():
        v = pipe.store.thesis_version(t.thesis_id, t.current_version)
        assert v is not None
        assert v.priority.investment_readiness.value == "NOT_ASSESSED"
        if v.priority.research_action is ResearchAction.RESEARCH_NOW:
            assert "not a trade" in v.priority.rules_fired[0]


# --- 17. A → B on PRESERVED state ----------------------------------------------------------------

def _capex_b() -> tuple[Hypo, dict]:  # type: ignore[type-arg]
    """HYPOTHETICAL article B: an independent company disclosure supporting the JPM AI
    infrastructure thesis. The publisher name carries parentheses AND digits — the shape that
    broke the live A→B run on 2026-10-10."""
    b = Hypo(slug="capex-reaffirmed", publisher="Hypo Wire (B) 24/7", published=date(2026, 2, 20),
             blocks=[("paragraph", "Microsoft reaffirmed that its fiscal 2027 capital "
                                   "expenditure will grow 25%, the company said, even as AI "
                                   "infrastructure shares stayed near their February lows.")])
    x = extraction(
        [claim("c1", "b001", "Microsoft reaffirmed that its fiscal 2027 capital expenditure "
                             "will grow 25%", "Microsoft: FY27 capex +25%", kind="event",
               epistemic="forecast", metric="capex growth guidance", value=25,
               value_text="25%", unit="%", period="FY27", scope="Microsoft",
               source="Microsoft")],
        [hyp("h1", "AI infrastructure still sold despite reaffirmed capex",
             node="ai_infrastructure", mechanism="valuation_dislocation", supporting=["c1"],
             affected=[("Microsoft", "spending_customer")])],
        [mention("Microsoft", "b001", "Microsoft reaffirmed that its fiscal 2027 capital "
                                      "expenditure will grow 25%", role="spending_customer",
                 ticker="MSFT")])
    return b, x


def test_article_a_then_b_on_preserved_state(tmp_path: Path) -> None:
    """Run 1 ingests the real JPM article; its registry is EXPORTED and re-IMPORTED into a fresh
    database (the durable-state path the scheduler uses); run 2 applies hypothetical article B."""
    one = make_pipeline(tmp_path / "one")
    one.start_run("article", as_of=JPM_AS_OF)
    ingest_jpm(one)
    one.finish_run(RunStatus.SUCCEEDED)
    infra = next(t for t in one.store.theses() if t.key_node == "ai_infrastructure")
    v1_sha = one.store.thesis_version(infra.thesis_id, 1).content_sha
    one.store.export_jsonl(tmp_path / "state")

    two = make_pipeline(tmp_path / "two")
    two.store.close()
    two.store = Store.import_jsonl(tmp_path / "state", tmp_path / "two" / "imported.db")
    two.engine.store = two.store
    two.start_run("article", as_of=date(2026, 2, 20))
    b, x = _capex_b()
    res = ingest(two, b.doc(), x, as_of=date(2026, 2, 20), publisher=b.publisher)
    out = next(o for o in res.outcomes if o.thesis_id == infra.thesis_id)
    assert not out.created and out.new_version == 2  # matched, not re-created
    assert out.contribution is ChangeClass.NEW
    v1 = two.store.thesis_version(infra.thesis_id, 1)
    assert v1 is not None and v1.content_sha == v1_sha  # the prior version is untouched
    v2 = two.store.thesis_version(infra.thesis_id, 2)
    assert v2 is not None and v2.diffs and v2.prior_content_sha == v1_sha
    assert len(two.store.theses()) == 3  # no fourth thesis
    # REGRESSION (live A→B runs, 2026-10-10): the card's own "Update (2026-02-20, <publisher>):"
    # prefix was number-checked as if the sentence asserted 2026 / 02 / 20 — first unstripped,
    # then mis-stripped when the publisher name held parentheses — and turned independent
    # SUPPORTING evidence into a RESEARCH NOW → WATCH demotion
    assert out.evidence_direction is EvidenceDirection.STRONGER
    assert v2.priority.research_action is ResearchAction.RESEARCH_NOW
    assert not [i for i in two.store.issues() if i.code == "NUMBER_NOT_IN_CITED_CLAIMS"
                and i.ref_id.endswith(":s01.2")]


# --- hold, archive -------------------------------------------------------------------------------

def test_a_material_review_block_holds_promotion_and_a_narrative_one_does_not(
        tmp_path: Path) -> None:
    def blocker(sid: str):
        def review(card, claims):
            from datetime import UTC, datetime
            return [VerificationIssue(
                issue_id=f"VI-test-{card.header.thesis_id}-{sid}", run_id="t",
                scope="card_sentence", ref_id=f"{card.header.thesis_id}:{sid}",
                severity=IssueSeverity.BLOCK, code="REVIEW_UNSUPPORTED", detail="test block",
                created_at=datetime.now(tz=UTC))]
        return review

    actions = {}
    for sid in ("s01.0", "s03.0"):
        pipe = make_pipeline(tmp_path / sid)
        pipe.engine.reviewer = blocker(sid)
        pipe.start_run("fixture", as_of=JPM_AS_OF)
        ingest_jpm(pipe)
        infra = next(t for t in pipe.store.theses() if t.key_node == "ai_infrastructure")
        v = pipe.store.thesis_version(infra.thesis_id, 1)
        assert v is not None
        actions[sid] = v.priority.research_action
    assert actions["s01.0"] is ResearchAction.WATCH  # a decision-bearing sentence: held
    assert actions["s03.0"] is ResearchAction.RESEARCH_NOW  # narrative prose: withheld only


def test_skip_and_stale_theses_are_archived_and_reactivated(pipe: Pipeline) -> None:
    art = Hypo(slug="opinion-only", publisher="Hypo Research A", published=W1,
               blocks=[("paragraph", "We think robotics could matter one day.")])
    x = extraction(
        [claim("c1", "b001", "We think robotics could matter one day", "Robotics may matter",
               kind="assertion", epistemic="opinion")],
        [hyp("h1", "Robotics someday", node="industrials", mechanism="demand_volume_shift",
             supporting=["c1"], horizon="longer_term")])
    ingest(pipe, art.doc(), x, as_of=W1, publisher=art.publisher)
    t = pipe.store.theses()[0]
    v = pipe.store.thesis_version(t.thesis_id, 1)
    assert v is not None and v.priority.research_action is ResearchAction.SKIP
    assert pipe.run is not None
    pipe.engine.archive_pass(run_id=pipe.run.run_id, as_of=W1)
    t = pipe.store.thesis(t.thesis_id)
    assert t is not None and t.status is ThesisStatus.ARCHIVED  # skip, but still archived
    assert "ARCHIVED" in {e.event_type for e in pipe.store.events(thesis_id=t.thesis_id)}
    # a stale ACTIVE thesis is archived after a quarter without material evidence
    a = _memory_article("dram-a", "Hypo Research A", W1)
    ingest(pipe, a.doc(), _memory_extraction(), as_of=W1, publisher=a.publisher)
    mem = _memory_thesis(pipe)
    pipe.engine.archive_pass(run_id=pipe.run.run_id, as_of=date(2026, 7, 1))
    assert pipe.store.thesis(mem.thesis_id).status is ThesisStatus.ARCHIVED
    # new material evidence re-activates it
    c = Hypo(slug="dram-later", publisher="Hypo Wire C", published=date(2026, 7, 6), blocks=[
        ("paragraph", "DRAM contract prices rose 9% quarter over quarter in 3Q26, according "
                      "to TrendForce."),
        ("paragraph", "Micron Technology said lead times for high-bandwidth memory now stretch "
                      "into 2027.")])
    xc = _memory_extraction()
    xc["claims"][0].update(quote="DRAM contract prices rose 9% quarter over quarter in 3Q26, "
                                 "according to TrendForce", value=9, value_text="9%",
                           period="3Q26", statement="DRAM +9% QoQ in 3Q26")
    ingest(pipe, c.doc(), xc, as_of=date(2026, 7, 6), publisher=c.publisher)
    back = pipe.store.thesis(mem.thesis_id)
    assert back is not None and back.current_version == 2
    if pipe.store.thesis_version(mem.thesis_id, 2).priority.research_action is not \
            ResearchAction.SKIP:
        assert back.status is ThesisStatus.ACTIVE
        assert "REACTIVATED" in {e.event_type for e in pipe.store.events(
            thesis_id=mem.thesis_id)}


def test_rerendering_an_old_run_shows_what_that_run_recorded(tmp_path: Path) -> None:
    """`report --run` on an OLD run must reproduce it: the version its snapshot recorded, not a
    later one (found when re-rendering the first live scan after the second had versioned on)."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    first = pipe.finish_run(RunStatus.SUCCEEDED)
    infra = next(t for t in pipe.store.theses() if t.key_node == "ai_infrastructure")
    pipe.start_run("article", as_of=date(2026, 3, 2))
    b, x = _capex_b()
    ingest(pipe, b.doc(), x, as_of=date(2026, 2, 20), publisher=b.publisher)
    later = _memory_article("born-later", "Hypo Research A", W1)  # a thesis run 1 never saw
    ingest(pipe, later.doc(), _memory_extraction(), as_of=W1, publisher=later.publisher)
    second = pipe.finish_run(RunStatus.SUCCEEDED)
    assert pipe.store.thesis(infra.thesis_id).current_version == 2
    write_run_outputs(pipe.store, second.run_id, tmp_path / "first")  # a later render, same dir
    out = write_run_outputs(pipe.store, first.run_id, tmp_path / "first")
    names = {p.name.split(".")[0] for p in (tmp_path / "first" / "cards").iterdir()}
    assert names == {t.thesis_id for t in pipe.store.theses()
                     if t.key_node != "ai_infrastructure.memory"}  # no card born after run 1
    card = json.loads((tmp_path / "first" / "cards" / f"{infra.thesis_id}.json").read_text())
    assert [h["version"] for h in card["history"]] == [1]  # v2 did not exist yet
    row = next(r for r in out["dashboard"].archive if r["thesis_id"] == infra.thesis_id)
    assert row["versions"] == 1
