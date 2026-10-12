"""Analytical safeguards after the PDF cost reduction (review of PR #703, 2026-10-12).

The cleaned paid run of Citi's 60-page Gridlock report cost $11.70 instead of $46.67 — and showed
what a cheaper, re-read analysis can lose without anyone noticing:
  * one malformed field threw away a whole completeness answer (14 claims, 50 reviews);
  * Citi's low-cost US natural gas argument (page 37) stayed verified and carried by no thesis;
  * a fuel-cell share hypothesis merged into a gas-generation thesis on one identity key;
  * three SKIP-3 theses read WATCH because the cards dropped their long-dated sentences;
  * the cost preflight held the cleaned report at $31.40 against $11.70 measured.
The real-data demonstrations are in docs/theme_intelligence/analytical-safeguards-2026-10-12/
(licensed text is not committed); the fixtures here are SYNTHETIC, built from the REAL types and
the real failure shapes.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.completeness import CompletenessOutput, scan_article
from vinci.theme_intelligence.documents import FINE_PRINT_DENSITY, classify_unread
from vinci.theme_intelligence.extract import LostItem, salvage_fields, validate_items
from vinci.theme_intelligence.ingest import estimate_from
from vinci.theme_intelligence.priority import ThesisState, compute_priority
from vinci.theme_intelligence.schemas import (
    Block,
    Claim,
    ClaimKind,
    Confidence,
    Epistemic,
    EvidenceDirection,
    Horizon,
    IssueSeverity,
    QuarantinedText,
    ResearchAction,
    RetrievalState,
    StanceInSource,
)
from vinci.theme_intelligence.timewindow import timing_of, window_of

AS_OF = date(2026, 10, 11)

# --- P0 · a malformed field costs that field, never the answer ------------------------------

BROKEN = ('[{"local_id": "hx4_1", "title": "Regulatory reform to accelerate large-load grid '
          'connection creates electric wires and generation investment opportunity", "kind": '
          '"market_regime", "bottom_line_fact": {"text": "t", "provenance": "source_stated", '
          '"claim_ids": ["k4_7"]}, {"text": "u", "claim_ids": ["k4_7"]}, '
          '"source_implication": {"text": "v"}}]')


def _real_shape() -> dict[str, Any]:
    """The shape of Citi Gridlock's paid completeness part 4 (2026-10-12): every field valid but
    `added_hypotheses`, which came back as text that is not valid JSON."""
    return {
        "figure_reviews": [{"figure_id": "b003#25", "verdict": "captured_by_added_claim",
                            "claim_ids": ["k4_9"], "reason": ""}],
        "block_reviews": [{"block_id": "b003", "verdict": "added", "hypothesis_ids": ["hx4_1"],
                           "claim_ids": ["k4_9"], "reason": "cancellations"}],
        "added_claims": [
            claim("k4_1", "b002", "More than 50GW of data center capacity was operating",
                  "US data center capacity above 50GW", value=50, value_text="More than 50GW",
                  unit="GW", period="2025"),
            {**claim("k4_9", "b003", "Project cancellations jumped to 25 in 2025",
                     "Cancellations 25 in 2025", value=25, value_text="25"), "kind": "bogus"}],
        "added_mentions": [{"name_as_written": "NERC", "block_id": "b002", "quote": "NERC",
                            "entity_type": "government_or_agency", "role": "data_source",
                            "role_detail": "grid reliability body", "direction": "neutral",
                            "recommendation_status": "not_a_recommendation",
                            "ticker_hint": None, "issuer_name_hint": None, "claim_ids": []}],
        "hypothesis_additions": [{"hypothesis_id": "h1", "supporting_claim_ids": ["k4_1"],
                                  "dislocation_claim_ids": [], "counter_claim_ids": [],
                                  "catalyst_claim_ids": [], "affected_mentions": [],
                                  "sector_exposures": []}],
        "added_hypotheses": BROKEN,
        "added_risks": [{"statement": "AI data center load swings create grid reliability risk",
                         "scope_qualification": "U.S. grid", "claim_ids": ["k4_1"],
                         "related_hypothesis_ids": []}],
    }


def test_the_real_malformed_shape_loses_only_its_bad_field_and_its_bad_item() -> None:
    with pytest.raises(ValidationError):
        validate_items(CompletenessOutput, _real_shape())  # the whole answer fails as before
    parsed, notes, lost = salvage_fields(CompletenessOutput, _real_shape())
    assert [c.local_id for c in parsed.added_claims] == ["k4_1"]  # k4_9 is malformed: dropped
    assert [m.name_as_written for m in parsed.added_mentions] == ["NERC"]
    assert len(parsed.added_risks) == 1 and len(parsed.hypothesis_additions) == 1
    assert len(parsed.figure_reviews) == 1 and len(parsed.block_reviews) == 1
    assert parsed.added_hypotheses == []
    try:
        json.loads(BROKEN)
    except json.JSONDecodeError as exc:
        where = f"line {exc.lineno} column {exc.colno}, character {exc.pos}"
    assert notes[0] == (f"added_hypotheses: the whole field discarded — {len(BROKEN):,} "
                        f"characters of text where a list belongs, not valid JSON (Expecting "
                        f"property name enclosed in double quotes: {where}); it named 1 "
                        f"item(s): hx4_1")
    assert any(n.startswith("added_claims[1] dropped — kind") for n in notes)
    assert lost == [LostItem("added_hypotheses", "hx4_1",
                             "Regulatory reform to accelerate large-load grid connection "
                             "creates electric wires and generation investment opportunity")]


def test_a_list_written_as_json_text_is_decoded_never_guessed() -> None:
    ans = _real_shape()
    ans["added_hypotheses"] = []
    ans["added_claims"] = json.dumps(ans["added_claims"])
    parsed, notes, lost = salvage_fields(CompletenessOutput, ans)
    assert [c.local_id for c in parsed.added_claims] == ["k4_1"] and lost == []
    assert notes[0].startswith("added_claims: the list arrived as JSON text")
    with pytest.raises(ValidationError):
        salvage_fields(CompletenessOutput, ["not", "an", "object"])


SALVAGE_DOC = Hypo(slug="safeguard-salvage", publisher="Hypo Research S", published=AS_OF,
                   blocks=[("paragraph", "Grid operators expect transmission capital "
                            "expenditure to rise 18% in 2026 to $42 billion as queues lengthen."),
                           ("paragraph", "More than 50GW of data center capacity was operating "
                            "at the end of 2025 across the surveyed markets, says NERC."),
                           ("paragraph", "Project cancellations jumped to 25 in 2025 from six "
                            "in 2024, mainly due to power access and local pushback.")])


def test_a_rejected_claim_never_vouches_for_a_figure_or_a_paragraph(tmp_path: Path) -> None:
    """END TO END: the salvaged answer through the real pipeline — the review naming the
    discarded claim k4_9 stays OPEN (its account names no record); the kept claim is evidence."""
    pipe = make_pipeline(tmp_path)
    doc = SALVAGE_DOC.doc()
    led = scan_article(doc)
    fid = next(f.figure_id for f in led.figures if f.block_id == "b003" and f.core == "25")
    ans = _real_shape()
    ans["figure_reviews"][0]["figure_id"] = fid
    parsed, _notes, _lost = salvage_fields(CompletenessOutput, ans)
    x = extraction([claim("c1", "b001", "transmission capital expenditure to rise 18% in 2026",
                          "Transmission capex +18%", kind="forecast", epistemic="forecast",
                          value=18, value_text="18%", unit="%", period="2026")],
                   [hyp("h1", "Grid capex keeps rising", node="ai_infrastructure.power_grid",
                        mechanism="capex_spending_cycle", supporting=["c1"])])
    pipe.start_run("article", as_of=AS_OF)
    res = ingest(pipe, doc, x, as_of=AS_OF, completeness=parsed.model_dump(mode="json"))
    [rep] = pipe.store.completeness_for_run(pipe.run.run_id)  # type: ignore[union-attr]
    fig = next(f for f in rep.figures if f.block_id == "b003" and f.figure == "25")
    assert fig.status == "uncaptured" and fig.open_cause == "capture_not_verified"
    blk = next(b for b in rep.blocks if b.block_id == "b003")
    assert blk.status == "unreviewed" and blk.open_cause == "account_names_no_record"
    linked = {c.quote for t in pipe.store.theses() for lk in pipe.store.links(t.thesis_id)
              if (c := pipe.store.claim(lk.claim_id)) is not None}
    assert "More than 50GW of data center capacity was operating" in linked  # the kept claim
    assert res.status in ("PROCESSED", "PARTIAL_PROCESSED")


# --- P0 · no distinct mechanism disappears without an alert --------------------------------

def _paged(h: Hypo, pages: list[int]) -> Any:
    doc = h.doc()
    return replace(doc, blocks=tuple(b.model_copy(update={"page": p})
                                     for b, p in zip(doc.blocks, pages, strict=True)))


COVER_DOC = Hypo(slug="safeguard-coverage", publisher="Hypo Research C", published=AS_OF, blocks=[
    ("paragraph", "Grid operators expect transmission capital expenditure to rise 18% in 2026 to "
                  "$42 billion, with orders placed across Renault, Volvo, Carwow and OLX "
                  "(CBRE, Feb 25)."),
    ("paragraph", "Reciprocating engine orders reached 33.8GW in 2025 as hyperscalers bought "
                  "speed to power for new campuses across Texas and Georgia."),
    ("paragraph", "Fuel cell stack replacement costs equal ~$1,000/kW and installs of 100MW can "
                  "be delivered in 120 days at campuses."),
    ("paragraph", "U.S. benchmark gas prices are generally within a range of $2 to $4/MMBtu, far "
                  "below overseas benchmarks for buyers."),
    ("paragraph", "Asian LNG prices did fall to around $8/MMBtu in recent years but surged to "
                  "~$20/MMBtu in the crisis."),
    ("paragraph", "Data center electricity demand rose 17% in 2025 according to the invented "
                  "utility survey cited here."),
    ("paragraph", "Behind-the-meter installs of 100MW can be delivered in 120 days at new "
                  "campuses, the invented survey adds.")])


def _cover_extraction() -> dict[str, Any]:
    return extraction(
        [claim("c1", "b001", "transmission capital expenditure to rise 18% in 2026",
               "Transmission capex +18%", kind="forecast", epistemic="forecast", value=18,
               value_text="18%", unit="%", period="2026"),
         claim("c2", "b002", "Reciprocating engine orders reached 33.8GW in 2025",
               "Engine orders 33.8GW", value=33.8, value_text="33.8GW", unit="GW",
               period="2025"),
         claim("c3", "b003", "Fuel cell stack replacement costs equal ~$1,000/kW",
               "Stack cost $1,000/kW", value=1000, value_text="~$1,000/kW", unit="$/kW"),
         claim("c4", "b004", "within a range of $2 to $4/MMBtu", "US gas $2-4/MMBtu", value=2,
               value_text="$2 to $4", unit="$/MMBtu"),
         claim("c5", "b005", "surged to ~$20/MMBtu in the crisis", "Asian LNG ~$20/MMBtu",
               value=20, value_text="~$20", unit="$/MMBtu"),
         claim("c6", "b006", "Data center electricity demand rose 17% in 2025",
               "DC power demand +17%", value=17, value_text="17%", unit="%", period="2025")],
        [hyp("h1", "Grid capex keeps rising", node="ai_infrastructure.power_grid",
             mechanism="capex_spending_cycle", supporting=["c1"]),
         hyp("h2", "Gas generation equipment cycle", node="ai_infrastructure.power_grid",
             mechanism="demand_volume_shift", supporting=["c2"]),
         hyp("h3", "Fuel cells gain data center share", node="ai_infrastructure.power_grid",
             mechanism="demand_volume_shift", supporting=["c3"])])


def _covered(tmp_path: Path, x: dict[str, Any] | None = None) -> tuple[Any, Any]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    ingest(pipe, _paged(COVER_DOC, [1, 2, 3, 37, 37, 40, 3]), x or _cover_extraction(),
           as_of=AS_OF)
    assert pipe.run is not None
    [rep] = pipe.store.completeness_for_run(pipe.run.run_id)
    return pipe, rep


def test_verified_material_facts_no_thesis_carries_raise_an_alert_by_page(
        tmp_path: Path) -> None:
    """The low-cost US gas shape (Citi Gridlock p37, 2026-10-12): verified, and on no card."""
    pipe, rep = _covered(tmp_path)
    cov = rep.coverage
    assert cov is not None
    groups = {(g.page, g.status): len(g.claim_ids) for g in cov.uncarried}
    assert groups == {(37, "unexplained"): 2, (40, "unexplained"): 1}
    p37 = [a for a in cov.alerts
           if a.startswith("page 37: 2 verified material facts no thesis carries")]
    assert len(p37) == 1
    # the SOURCE's evidence named, every figure as written, kept apart from any assessment
    assert "Source evidence: $2 to $4; ~$20 — verified, UNASSESSED" in p37[0]
    assert not any(a.startswith("page 40") for a in cov.alerts)  # a lone fact: listed only
    codes = [i.detail for i in pipe.store.issues(run_id=pipe.run.run_id)
             if i.code == "MECHANISM_COVERAGE"]
    assert any("page 37" in d for d in codes)
    from vinci.theme_intelligence.report import research_verification

    rv = research_verification(pipe.store, pipe.run)
    assert rv["status"] == "INCOMPLETE" and "mechanism coverage: " in rv["summary"]
    assert any("page 37" in a and "TH-" not in a for a in rv["coverage_alerts_plain"])


def test_two_technologies_on_one_key_with_their_own_evidence_are_separate_theses(
        tmp_path: Path) -> None:
    """The fuel-cell shape (Citi Gridlock, 2026-10-12): one identity key, no shared evidence, and
    the evidence names different PRODUCTS (reciprocating engines vs fuel cells) — two theses, the
    second qualified by its product; never merged. No product is special-cased."""
    pipe, rep = _covered(tmp_path)
    cov = rep.coverage
    assert cov is not None
    fates = {p.hypothesis_id: (p.fate, p.thesis_id) for p in cov.propositions}
    assert fates["h2"][0] == "card" and fates["h3"][0] == "card"
    assert fates["h3"][1] != fates["h2"][1]
    fuel = pipe.store.thesis(fates["h3"][1])
    gas = pipe.store.thesis(fates["h2"][1])
    assert fuel is not None and fuel.key_product == "fuel_cells" and fuel.identity.endswith(
        "|prod:fuel_cells")
    assert gas is not None and gas.key_product == ""  # the first keeps the key it always had
    assert not [a for a in cov.alerts if a.startswith("propositions merged")]
    split = [i.detail for i in pipe.store.issues(run_id=pipe.run.run_id)
             if i.code == "PRODUCT_SPLIT"]
    assert len(split) == 1 and "(fuel_cells vs reciprocating_engines)" in split[0]
    # the card's registry link says WHAT separates them — the product — never "a different
    # geography (US vs US)" (the real fuel-cell card said so before this was pinned)
    v = pipe.store.thesis_version(fuel.thesis_id, fuel.current_version)
    assert v is not None
    links = [s.text for s in v.content.s07_what_could_go_wrong.alternative_mechanisms
             if s.text.startswith("Registry link") and "a different product" in s.text]
    assert links == [s for s in links if "(fuel_cells vs reciprocating_engines)" in s] != []
    assert gas.thesis_id in links[0]  # said on the link to the gas thesis, nowhere else
    assert not [s.text for s in v.content.s07_what_could_go_wrong.alternative_mechanisms
                if "(US vs US)" in s.text]


def test_a_risk_naming_the_split_off_product_goes_with_its_thesis(tmp_path: Path) -> None:
    """The scandium shape (Citi Gridlock, 2026-10-12): the model tied a fuel-cell supply-chain
    risk to the gas-generation hypothesis; once fuel cells are their own thesis, the risk naming
    them is on THAT card — never on the gas card. A risk naming neither stays where it was."""
    x = _cover_extraction()
    x["market_risks"] = [
        {"statement": "Scandium supply concentration constrains SOFC production if scaled.",
         "scope_qualification": "fuel-cell supply chain", "claim_ids": [],
         "related_hypothesis_ids": ["h2"]},
        {"statement": "Engine lead times could slip as campuses compete for slots.",
         "scope_qualification": "engine supply", "claim_ids": [],
         "related_hypothesis_ids": ["h2"]},
        {"statement": "Recips and SOFC stacks share one constrained machining supply chain.",
         "scope_qualification": "both technologies", "claim_ids": [],
         "related_hypothesis_ids": ["h2"]}]
    pipe, rep = _covered(tmp_path, x)
    fates = {p.hypothesis_id: p.thesis_id for p in rep.coverage.propositions}

    def risks(h: str) -> list[str]:
        t = pipe.store.thesis(fates[h])
        assert t is not None
        v = pipe.store.thesis_version(t.thesis_id, t.current_version)
        assert v is not None
        return [r.text for r in v.content.s07_what_could_go_wrong.market_risks]

    assert any("Scandium" in r for r in risks("h3")) and not any("Scandium" in r
                                                                 for r in risks("h2"))
    assert any("Engine lead times" in r for r in risks("h2"))
    assert not any("Engine lead times" in r for r in risks("h3"))
    # naming BOTH products: it is not the split-off product's alone — it stays where it was
    assert any("machining" in r for r in risks("h2")) and not any("machining" in r
                                                                  for r in risks("h3"))
    [split] = [i.detail for i in pipe.store.issues(run_id=pipe.run.run_id)
               if i.code == "PRODUCT_SPLIT"]
    assert "1 market risk(s) naming fuel_cells follow it" in split


def test_a_comparison_heavy_thesis_is_identified_by_the_product_its_statement_names() -> None:
    """A fuel-cell thesis's evidence names CCGTs as often as fuel cells (cost comparisons; the
    real one: 8 vs 7) — its own statement decides; the evidence count only when it names none."""
    from vinci.theme_intelligence.config import load_taxonomy
    from vinci.theme_intelligence.engine import Engine

    eng = Engine.__new__(Engine)
    eng.taxonomy = load_taxonomy()
    node = "ai_infrastructure.power_grid"
    assert eng._named_product(node, "Fuel cells gain data center share") == "fuel_cells"
    assert eng._named_product(node, "Fuel cells gain share despite the CCGT cost edge") == ""
    assert eng._named_product(node, "Speed-to-power drives gas generation equipment") == ""
    assert eng._named_product(node, "Behind-the-meter power wins") == ""  # generic: not a product
    # from the evidence: what it is ABOUT, never a passing mention (the real transformer thesis
    # named a CCGT once in 67 claims and read as a gas-turbine thesis)
    from tests.test_theme_intelligence_glyph_quarantine import _c

    plain = [_c(f"p{i}", "AV-1", f"transformer lead times reached {30 + i} months", 30, "30")
             for i in range(9)]
    once = [_c("g", "AV-1", "a CCGT unit also ordered one", 1, "1")]
    thrice = [_c(f"g{i}", "AV-1", f"CCGT order number {i} was placed", 1, "1") for i in range(3)]
    assert eng._dominant_product(node, plain + once) == ""
    assert eng._dominant_product(node, plain[:7] + thrice) == "gas_turbines"


def test_one_key_with_distinct_evidence_but_no_distinguishing_product_merges_and_alerts(
        tmp_path: Path) -> None:
    """Without a product to tell them apart the identity rule merges them — and says so."""
    x = _cover_extraction()
    x["claims"].append(claim("c7", "b007", "Behind-the-meter installs of 100MW can be delivered "
                                           "in 120 days", "100MW in 120 days", value=100,
                             value_text="100MW", unit="MW"))
    x["hypotheses"][2]["supporting_claim_ids"] = ["c7"]
    x["hypotheses"][2]["bottom_line_fact"]["claim_ids"] = ["c7"]
    x["hypotheses"][2]["title"] = "Speed-to-power wins data center share"  # names no product
    pipe, rep = _covered(tmp_path, x)
    cov = rep.coverage
    assert cov is not None
    fates = {p.hypothesis_id: (p.fate, p.thesis_id) for p in cov.propositions}
    assert fates["h3"] == ("merged", fates["h2"][1])
    merged = next(p for p in cov.propositions if p.hypothesis_id == "h3")
    assert "0 supporting claim(s) shared, 1 its own — DISTINCT EVIDENCE" in merged.detail
    assert any(a.startswith("propositions merged: “Speed-to-power wins data center share”")
               for a in cov.alerts)


def test_a_carried_fact_and_a_merged_fact_raise_nothing(tmp_path: Path) -> None:
    _pipe, rep = _covered(tmp_path)
    cov = rep.coverage
    assert cov is not None
    pages = {g.page for g in cov.uncarried}
    assert 1 not in pages and 2 not in pages and 3 not in pages  # c1, c2, c3 are on cards


def test_organisations_named_in_cited_sentences_but_unrecorded_are_listed(
        tmp_path: Path) -> None:
    _pipe, rep = _covered(tmp_path)
    cov = rep.coverage
    assert cov is not None
    names = [n.split(" (")[0] for n in cov.unrecorded_names]
    assert names == ["Renault", "Volvo", "Carwow", "OLX", "CBRE"]
    assert cov.unrecorded_names[-1] == "CBRE (a dated source, b001)"


def test_a_place_or_a_recorded_company_is_never_listed_as_unrecorded() -> None:
    from vinci.theme_intelligence.coverage import _CITED, _LIST, _NOT_ORG

    m = _LIST.search("demand rose across Europe, Asia and Texas this year")
    assert m is not None and all(n.lower() in _NOT_ORG for n in
                                 [x.strip() for x in m.group(1).replace(" and ", ", ").split(",")])
    assert _CITED.search("(Reuters, Feb 25)") and not _CITED.search("(in 2025, mostly)")


# --- P0 · missing timing never upgrades a thesis --------------------------------------------

@pytest.mark.parametrize(("text", "end"), [
    ("over the next five years", date(2031, 10, 11)),
    ("over the next decade", date(2036, 10, 10)),
    ("unlikely to clear before 2030", date(2029, 12, 31)),
    ("demand grows into the 2030s", date(2039, 12, 31)),
    ("by the end of the decade", date(2029, 12, 31)),
])
def test_long_horizons_written_in_words_are_read(text: str, end: date) -> None:
    w = window_of(text, AS_OF)
    assert w is not None and w.start == AS_OF and w.end == end


@pytest.mark.parametrize("text", ["over the past five years", "a decade-old plant",
                                  "before the crisis", "the next generation of turbines"])
def test_ordinary_prose_names_no_window(text: str) -> None:
    assert window_of(text, AS_OF) is None


def _c(cid: str, quote: str, *, epistemic: Epistemic = Epistemic.OPINION,
       kind: ClaimKind = ClaimKind.ASSERTION, period: str | None = None,
       value: float | None = None, block: str = "b001") -> Claim:
    return Claim(claim_id=cid, article_id="A-1", article_version_id="AV-1", block_id=block,
                 char_start=0, char_end=len(quote), quote=quote, statement=quote, kind=kind,
                 epistemic=epistemic, period=period, value=value,
                 value_text=None if value is None else str(value),
                 confidence=Confidence.HIGH, span_verified=True, number_verified=True,
                 measure_key=f"k|{cid}", fingerprint=f"f|{cid}", extraction_id="X-1")


def test_a_view_naming_a_far_horizon_is_long_dated_and_never_near_term() -> None:
    far = _c("c1", "The shortage is unlikely to clear before 2030 for structural reasons")
    assert timing_of(far, AS_OF, None)[0] == "long_range"
    near = _c("c2", "We think orders improve next quarter")
    assert timing_of(near, AS_OF, None)[0] == "undated"  # a view never shows near-term


def _state(supporting: tuple[Claim, ...], context: tuple[Claim, ...] = (), *,
           retrieval: RetrievalState = RetrievalState.FULL) -> ThesisState:
    from vinci.theme_intelligence.schemas import Provenance, TransmissionStep

    step = TransmissionStep(step="costs", text="labour costs rise",
                            provenance=Provenance.SOURCE_OPINION, claim_ids=())
    return ThesisState(reliability="high", supporting=supporting, counter=(), dislocation=(),
                       catalyst=(), listed_exposures=(), instrument_exposures=(),
                       transmission=(step,), horizon=Horizon.LONGER_TERM,
                       stance=StanceInSource.ASSERTED, verification_hold=False, hold_reasons=(),
                       retrieval=retrieval, sector_exposures=("Construction",), as_of=AS_OF,
                       timing_context=context)


METRIC = _c("c0", "a shortage of at least 222,600 workers in various trades", value=222600,
            epistemic=Epistemic.FORECAST, kind=ClaimKind.METRIC)


def test_a_long_dated_sentence_left_off_the_card_still_holds_the_thesis_at_skip() -> None:
    """The skilled-labour shape (2026-10-12): the source's 'before 2030' sat in the paragraph and
    as a context line, off the card's citations — the thesis read WATCH."""
    beside = _c("c9", "The shortage is unlikely to clear before 2030 for structural reasons")
    pr = compute_priority(_state((METRIC,), (beside,)), previous=None,
                          evidence_direction=EvidenceDirection.NEW)
    assert pr.research_action is ResearchAction.SKIP
    assert pr.rules_fired[0].startswith("SKIP-3 longer-term only")
    assert "beside the cited evidence: c9" in pr.rules_fired[0]
    without = compute_priority(_state((METRIC,)), previous=None,
                               evidence_direction=EvidenceDirection.NEW)
    assert without.research_action is ResearchAction.WATCH  # no dated window anywhere …
    assert "timing UNKNOWN in the source evidence" in without.rules_fired[0]  # … said so


def test_near_term_context_never_upgrades_a_thesis() -> None:
    soon = _c("c8", "Orders are forecast to rise next quarter", epistemic=Epistemic.FORECAST,
              kind=ClaimKind.FORECAST, period="next quarter")
    pr = compute_priority(_state((METRIC,), (soon,)), previous=None,
                          evidence_direction=EvidenceDirection.NEW)
    f5 = next(f for f in pr.factors if f.factor_id.startswith("F5"))
    assert f5.value == "not shown"  # context is read for long-dated timing only


PARAGRAPH_DOC = Hypo(slug="safeguard-timing", publisher="Hypo Research T", published=AS_OF,
                     blocks=[("paragraph", "Contractors report a shortage of at least 222,600 "
                              "workers in various trades. The shortage is unlikely to clear "
                              "before 2030 for structural reasons.")])


def test_end_to_end_the_source_paragraph_supplies_the_horizon_the_card_left_out(
        tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    x = extraction(
        [claim("c1", "b001", "a shortage of at least 222,600 workers in various trades",
               "Shortage 222,600 workers", kind="forecast", epistemic="forecast",
               value=222600, value_text="222,600"),
         claim("c2", "b001", "The shortage is unlikely to clear before 2030",
               "Shortage persists", kind="assertion", epistemic="opinion")],
        [hyp("h1", "Skilled-labour shortage constrains the buildout",
             node="ai_infrastructure.power_grid", mechanism="supply_constraint",
             supporting=["c1"])])
    ingest(pipe, PARAGRAPH_DOC.doc(), x, as_of=AS_OF)
    [t] = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None and v.priority.research_action is ResearchAction.SKIP
    assert "SKIP-3" in v.content.s08_decision.rule_trace[0]


# --- P1 · unreadable disclosures are not missing research ------------------------------------

def _blocks(spec: list[tuple[int, str, str]]) -> list[Block]:
    return [Block(block_id=f"b{i:03d}", kind=k, text=t, sha256="0" * 64, order=i, page=p)
            for i, (p, k, t) in enumerate(spec, 1)]


LONG_TEXT = "The analysis argues a point about grid investment in more than twelve words here."


def _q(page: int, chars: int, size: float) -> QuarantinedText:
    return QuarantinedText(page=page, lines=10, cells=0, chars=chars, sha256="0" * 64, size=size)


def test_trailing_fine_print_after_the_last_listed_section_is_back_matter() -> None:
    blocks = _blocks([(1, "heading", "Contents"), (1, "paragraph", "Summary 2 Outlook 3"),
                      (2, "paragraph", LONG_TEXT), (3, "paragraph", LONG_TEXT)])
    [q] = classify_unread(blocks, [_q(4, 30_000, 8.0)], [200, 2_000, 2_400, 0], 10.0)
    assert q.kind == "back_matter" and "contents list names (page 3)" in q.basis
    assert FINE_PRINT_DENSITY == 2.0


def test_an_unread_page_with_analysis_after_it_is_possibly_material() -> None:
    blocks = _blocks([(1, "paragraph", LONG_TEXT), (3, "paragraph", LONG_TEXT)])
    [q] = classify_unread(blocks, [_q(2, 30_000, 8.0)], [2_000, 0, 2_400], 10.0)
    assert q.kind == "possibly_material" and "page 3" in q.basis


def test_an_unread_page_in_body_type_or_inside_a_listed_section_is_never_back_matter() -> None:
    blocks = _blocks([(1, "heading", "Contents"), (1, "paragraph", "Summary 2 Appendix 4"),
                      (2, "paragraph", LONG_TEXT)])
    [listed] = classify_unread(blocks, [_q(4, 30_000, 8.0)], [200, 2_000, 0, 0], 10.0)
    assert listed.kind == "possibly_material"  # the contents list places a section on page 4
    plain = _blocks([(1, "paragraph", LONG_TEXT), (2, "paragraph", LONG_TEXT)])
    [body] = classify_unread(plain, [_q(3, 2_100, 10.0)], [2_000, 2_400, 0], 10.0)
    assert body.kind == "unclassified"  # not fine print: a visual check decides


def test_a_report_with_only_back_matter_unread_is_never_listed_as_awaiting_a_document() -> None:
    from types import SimpleNamespace

    from vinci.theme_intelligence.report import _only_back_matter, _unread_kinds

    back = SimpleNamespace(quarantined=[_q(9, 30_000, 8.0).model_copy(update={
        "kind": "back_matter", "basis": "after the last listed section"})])
    mixed = SimpleNamespace(quarantined=[*back.quarantined, _q(4, 3_000, 10.0).model_copy(
        update={"kind": "possibly_material", "basis": "analysis follows it"})])
    assert _only_back_matter(back) and not _only_back_matter(mixed)
    assert _unread_kinds(mixed).startswith("page 4: POSSIBLY MATERIAL")


def test_only_back_matter_unread_passes_the_research_gate_but_stays_partial(
        tmp_path: Path) -> None:
    """END TO END: a version whose only unread pages are back matter by the document's own
    contents list reads FULL for the research-action gate, says why, and is still reported as
    read only in part."""
    from vinci.theme_intelligence.report import research_verification

    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    doc = replace(PARAGRAPH_DOC.doc(), retrieval_state=RetrievalState.PARTIAL,
                  unread_back_matter="pages 9–12 unread, all back matter: after the last "
                                     "section the document's contents list names (page 8)")
    x = extraction([claim("c1", "b001", "a shortage of at least 222,600 workers in various "
                          "trades", "Shortage", kind="forecast", epistemic="forecast",
                          value=222600, value_text="222,600")],
                   [hyp("h1", "Skilled-labour shortage", node="ai_infrastructure.power_grid",
                        mechanism="supply_constraint", supporting=["c1"])])
    ingest(pipe, doc, x, as_of=AS_OF)
    [t] = pipe.store.theses()
    v = pipe.store.thesis_version(t.thesis_id, t.current_version)
    assert v is not None
    f11 = next(f for f in v.priority.factors if f.factor_id == "F11_retrieval")
    assert f11.value == "FULL" and "analysis text complete — pages 9–12" in f11.note
    assert pipe.run is not None
    assert "read only in part" in research_verification(pipe.store, pipe.run)["summary"]


# --- P1 · the cost preflight, calibrated without weakening the guard ------------------------

#: measured analyses (list price, claude-opus-4-8): text characters sent, ledger figures,
#: argument paragraphs, cost of every call incl. card reviews
MEASURED = [("Gridlock as first read (glyph codes in)", 428_578, 851, 292, 46.67),
            ("Gridlock cleaned", 120_399, 403, 287, 11.70),
            ("LatAm", 162_407, 319, 208, 9.47),
            ("ETF", 101_793, 232, 144, 3.80)]


@pytest.mark.parametrize(("name", "chars", "figures", "paragraphs", "cost"), MEASURED)
def test_every_measured_cost_lies_inside_its_estimate(name: str, chars: int, figures: int,
                                                       paragraphs: int, cost: float) -> None:
    est = estimate_from(chars, figures, paragraphs)
    assert est.low <= cost <= est.high, (name, est)


def test_the_cleaned_report_is_no_longer_held_and_the_glyph_laden_one_still_is() -> None:
    from vinci.theme_intelligence.config import DOC_COST_LIMIT_USD
    from vinci.theme_intelligence.ingest import CostEstimate

    assert DOC_COST_LIMIT_USD == 30.0  # the default limit is unchanged
    assert estimate_from(120_399, 403, 287).high < DOC_COST_LIMIT_USD
    assert estimate_from(428_578, 851, 292).high > DOC_COST_LIMIT_USD
    # the arithmetic itself, frozen (list price claude-opus-4-8, 2026-10-12)
    assert estimate_from(120_399, 403, 287) == CostEstimate(14, 403, 287, 6.56, 20.77)


# --- P1 · quantities written in words -------------------------------------------------------

WORDS_DOC = Hypo(slug="safeguard-words", publisher="Hypo Research W", published=AS_OF, blocks=[
    ("paragraph", "We assume the new capacity to be added gradually over four years from 2025 "
                  "to 2028, taking total output higher."),
    ("paragraph", "This is one of the reasons the first of the new plants matters to a few of "
                  "the buyers in the region today.")])


def test_a_quantity_in_words_is_a_figure_and_ordinary_prose_is_not() -> None:
    led = scan_article(WORDS_DOC.doc())
    assert [(f.block_id, f.text) for f in led.figures if not f.text[0].isdigit()] == [
        ("b001", "four years")]
    assert not [f for f in led.figures if f.block_id == "b002"]


def test_a_figure_without_a_verdict_is_open_never_immaterial(tmp_path: Path) -> None:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    ingest(pipe, WORDS_DOC.doc(), extraction([], []), as_of=AS_OF,
           completeness=CompletenessOutput().model_dump(mode="json"))
    assert pipe.run is not None
    [rep] = pipe.store.completeness_for_run(pipe.run.run_id)
    four = next(f for f in rep.figures if f.figure == "four years")
    assert four.status == "uncaptured" and four.open_cause == "no_account"


# --- P1 · risks the source states that no model pass listed --------------------------------
# INVENTED wording in the REAL constructions of Citi Gridlock (2026-10-12): "a portion of
# announced capacity risks remaining 'bragawatts'" (p47), raw-material inflation that "might put
# downward pressure on the IRR of ESS projects" (p33), "little risk of industry oversupply"
# (p31, a risk said to be ABSENT), a sentence cut by a page break (p28)

#: the real sentence is ~300 characters — an alert must carry it WHOLE (a cut quote misreads)
IRR = ("Despite rising cost inflation in raw materials such as lithium, copper and aluminium that "
       "might put downward pressure on the IRR of storage projects this year, bringing uncertainty "
       "to the progress of those projects, we still expect secular demand growth for the storage "
       "market over the medium term.")

RISK_DOC = Hypo(slug="safeguard-risks", publisher="Hypo Research R", published=AS_OF, blocks=[
    ("paragraph", "European grid operators plan to invest €40 billion in 2027 on network upgrades "
                  "for new demand. Long connection queues and high energy costs are not easily "
                  "resolved, so a portion of announced capacity risks remaining “bragawatts” "
                  "rather than realised load."),
    ("paragraph", "Storage installations rose 40% in 2025 to 90GWh across the region. " + IRR),
    ("paragraph", "Gas engine orders reached 33.8GW in 2025 for new campuses. We see little "
                  "risk of industry oversupply through 2030 for onsite backup and prime power."),
    ("paragraph", "A repeat of the early-2000s gas overbuild is possible: demand expected then did "
                  "not materialize, leaving excess capacity and a burden for ratepayers."),
    ("paragraph", "Continued dependence on imported fuel adds headwinds for the net importers of "
                  "the region over the decade ahead."),
    ("paragraph", "Onsite turbines added 5GW of orders in 2025 at remote campuses. Community "
                  "pushback over noise and air quality often brings tighter air permitting for "
                  "the sites,"),
    ("paragraph", "Cancellations jumped to 25 in 2025 from six in 2024, mainly due to power "
                  "access and public pushback in some regions."),
    ("paragraph", "Durability of long-term demand is the key consideration, because there was an "
                  "overbuild of gas-fired generation around 2000 that later had to be written "
                  "down."),
    # the cleaned Gridlock run's shape: the model wrote the risk as an ALTERNATIVE MECHANISM, in
    # fewer words than the source's sentence — carried on the card, never a duplicate line
    ("paragraph", "Gas engine makers report that tight machining capacity at their forging "
                  "suppliers could delay engine deliveries to new campuses well into next year, "
                  "according to buyers surveyed for this note.")])


def _risk_extraction() -> dict[str, Any]:
    return extraction(
        [claim("c1", "b001", "invest €40 billion in 2027 on network upgrades", "EU grid €40bn",
               kind="forecast", epistemic="forecast", value=40, value_text="€40 billion",
               unit="€bn", period="2027"),
         claim("c2", "b002", "Storage installations rose 40% in 2025 to 90GWh",
               "Storage +40%", value=40, value_text="40%", unit="%", period="2025"),
         claim("c3", "b003", "Gas engine orders reached 33.8GW in 2025", "Engine orders 33.8GW",
               value=33.8, value_text="33.8GW", unit="GW", period="2025"),
         claim("c6", "b006", "Onsite turbines added 5GW of orders in 2025", "Turbines +5GW",
               value=5, value_text="5GW", unit="GW", period="2025"),
         # p14 shape: the risk sentence IS a cited piece of evidence — on the card already
         claim("c7", "b007", "Cancellations jumped to 25 in 2025 from six in 2024, mainly due "
                             "to power access and public pushback", "Cancellations 25",
               value=25, value_text="25", unit="projects", period="2025"),
         claim("c8", "b008", "written down", "Earlier gas build written down",
               kind="assertion", epistemic="opinion")],
        [hyp("h1", "European grid expansion", node="ai_infrastructure.power_grid",
             mechanism="capex_spending_cycle", geography="Europe", supporting=["c1"]),
         hyp("h2", "Storage demand accelerates", node="industrials",
             mechanism="demand_volume_shift", geography="Global", supporting=["c2"]),
         hyp("h3", "Onsite generation orders boom", node="ai_infrastructure.datacenter_physical",
             mechanism="demand_volume_shift", supporting=["c3", "c6", "c7"])],
        risks=[{"statement": "A repeat of the early-2000s gas overbuild: demand expected then "
                             "did not materialize, leaving excess capacity and ratepayer burden",
                "scope_qualification": "US gas generation", "claim_ids": [],
                "related_hypothesis_ids": ["h3"]},
               # p15 shape: the model's risk PARAPHRASES its paragraph (it cites the paragraph's
               # claim) — the paragraph's risk sentence is carried though few words are shared
               {"statement": "Plant buildout may outrun demand as in an earlier cycle",
                "scope_qualification": "US gas generation", "claim_ids": ["c8"],
                "related_hypothesis_ids": ["h3"]}])


def _risked(tmp_path: Path) -> tuple[Any, Any, dict[str, Any]]:
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    x = _risk_extraction()
    # a SHORT generic line sharing a few words is not the source's risk (3 of 4 words shared
    # with the bragawatts sentence — under RISK_SHARED_MIN): that sentence stays flagged
    x["hypotheses"][0]["opposing_explanations"] = [{
        "text": "Energy costs stay high", "provenance": "model_inference", "claim_ids": []}]
    x["hypotheses"][2]["opposing_explanations"] = [{
        "text": "Tight machining capacity could delay engine deliveries to new campuses",
        "provenance": "model_inference", "claim_ids": []}]
    ingest(pipe, _paged(RISK_DOC, [47, 33, 31, 15, 32, 28, 14, 16, 17]), x, as_of=AS_OF)
    assert pipe.run is not None
    [rep] = pipe.store.completeness_for_run(pipe.run.run_id)
    assert rep.coverage is not None
    fates = {p.hypothesis_id: p.thesis_id for p in rep.coverage.propositions}
    cards = {}
    for h, tid in fates.items():
        assert tid is not None
        v = pipe.store.thesis_version(tid, 1)
        assert v is not None
        cards[h] = v.content
    return pipe, rep, cards


def test_a_risk_the_source_states_beside_a_thesis_is_put_on_that_card_as_its_opinion(
        tmp_path: Path) -> None:
    pipe, rep, cards = _risked(tmp_path)

    def risks(h: str) -> list[tuple[str, str]]:
        return [(r.text, r.provenance.value) for r in cards[h].s07_what_could_go_wrong.market_risks]

    brag = [r for r in risks("h1") if "bragawatts" in r[0]]
    irr = [r for r in risks("h2") if "downward pressure on the IRR" in r[0]]
    assert len(brag) == 1 and len(irr) == 1
    assert brag[0][1] == irr[0][1] == "SOURCE OPINION"  # the source's opinion, never a fact
    # only on the card whose evidence shares its paragraph — never on every card
    assert not [r for r in risks("h1") if "IRR" in r[0]]
    assert not [r for h in ("h2", "h3") for r in risks(h) if "bragawatts" in r[0]]
    flagged = {i.ref_id for i in pipe.store.issues(run_id=pipe.run.run_id)
               if i.code == "SOURCE_RISK_OMITTED"}
    tid = {p.hypothesis_id: p.thesis_id for p in rep.coverage.propositions}
    assert flagged == {tid["h1"], tid["h2"]}
    alerts = [a for a in rep.coverage.alerts if "no model pass listed" in a]
    assert any(a.startswith("page 47:") and "now in 07 of “European grid expansion”" in a
               for a in alerts)
    assert len(IRR) > 240 and any(f"“{IRR}”" in a for a in alerts)  # whole, never cut
    # the placed line is checked like any card line and SURVIVES it: its scope names the page
    # as system text — a bare "page 33" was read as a figure its claim lacks and withheld the
    # real line (2026-10-12, Citi Gridlock's storage card)
    withheld = [i for i in pipe.store.issues(run_id=pipe.run.run_id)
                if i.scope == "card_sentence" and i.severity is IssueSeverity.BLOCK]
    assert not withheld, [i.detail for i in withheld]


def test_a_risk_said_to_be_absent_or_already_listed_is_not_flagged(tmp_path: Path) -> None:
    _pipe, rep, _cards = _risked(tmp_path)
    found = {r.page: r for r in rep.coverage.source_risks}
    assert 31 not in found  # "little risk of industry oversupply": no risk stated
    assert found[15].represented_by.startswith("proposed risk")  # the model's overbuild risk
    # quoted as evidence on a card already (the p14 cancellations shape)
    assert found[14].represented_by.startswith("evidence on its card")
    # the model's risk drawn from the paragraph, in other words (the p15 durability shape)
    assert found[16].represented_by.startswith("proposed risk drawn from this paragraph")
    # an alternative mechanism on the card, shorter than the sentence it condenses
    assert found[17].represented_by.startswith("alternative mechanism on its card")
    assert not [a for a in rep.coverage.alerts if a.startswith(("page 31:", "page 15:",
                                                                 "page 14:", "page 16:",
                                                                 "page 17:"))]


def test_a_risk_beside_no_thesis_or_cut_by_a_page_break_is_alerted_never_placed(
        tmp_path: Path) -> None:
    pipe, rep, cards = _risked(tmp_path)
    found = {r.page: r for r in rep.coverage.source_risks}
    assert found[32].thesis_ids == () and found[28].fragment and found[28].thesis_ids == ()
    alerts = [a for a in rep.coverage.alerts if "no model pass listed" in a]
    assert any(a.startswith("page 32:") and "on NO card — no thesis's evidence" in a
               for a in alerts)
    assert any(a.startswith("page 28:") and "cut by a page break" in a for a in alerts)
    on_cards = [r.text for c in cards.values() for r in c.s07_what_could_go_wrong.market_risks]
    assert not [t for t in on_cards if "imported fuel" in t or "pushback" in t]


def test_the_same_sentence_scaled_two_ways_is_one_figure() -> None:
    """Two reads of "EV sales reached ~75K units": 75,000 units and 75 thousand units (the real
    Gridlock re-read, 2026-10-12) — one sentence, one figure as WRITTEN."""
    from tests.test_theme_intelligence_glyph_quarantine import _c
    from vinci.theme_intelligence.verify import same_sentence_reread

    q = "EV sales reached ~75K units"
    assert same_sentence_reread(_c("h", "AV-1", q, 75000, "~75K"), _c("n", "AV-2", q, 75, "~75K"))
    assert not same_sentence_reread(_c("h", "AV-1", q, 75000, "~75K"),
                                    _c("n", "AV-2", q, 75, "~76K"))


# --- P0 · a thesis's segment is its SUBJECT, never an incidental mention -------------------------

@pytest.mark.parametrize("statement,product,quotes,expected,exposure", [
    # transformer equipment: the statement names it — one CCGT comparison among ten never sets it
    ("Transformer shortage drives demand and pricing for transformer makers", "",
     ["lead times reached 4 years"] * 9 + ["a CCGT unit costs more"], "grid_equipment",
     ()),
    # gas turbines / reciprocating engines: no segment in the statement — the PRODUCT decides
    ("Speed-to-power drives a multi-year cycle for gas generation equipment", "gas_turbines",
     ["orders rose"], "onsite_generation", ()),
    ("Engine makers win data-centre orders", "reciprocating_engines", ["orders rose"],
     "onsite_generation", ()),
    # fuel cells: named in the statement, whatever the cost comparison names
    ("Fuel cells gain data center share despite the CCGT cost edge", "",
     ["CCGT costs $3,000/kW"] * 5, "onsite_generation", ()),
    # a cross-sector comparison in the evidence: below a fifth of the quotes — unassigned
    ("Skilled-labor shortage constrains the power buildout", "",
     ["electricians are scarce"] * 9 + ["unlike transformer makers, contractors cannot hire"],
     "", ()),
    # the evidence IS about it when a fifth or more of the quotes name it
    ("Power demand outruns supply", "",
     ["utilities raised capex"] * 3 + ["demand grew"] * 7, "grid_utilities", ()),
    # the sectors the SOURCE names as exposed come before the evidence count
    ("Power demand outruns supply", "", ["a CCGT unit"] * 9, "grid_utilities",
     ("regulated utilities",)),
])
def test_a_thesis_segment_is_its_economic_subject(statement: str, product: str,
                                                   quotes: list[str], expected: str,
                                                   exposure: tuple[str, ...]) -> None:
    from vinci.theme_intelligence.config import load_taxonomy
    from vinci.theme_intelligence.engine import subject_segment

    assert subject_segment("ai_infrastructure.power_grid", statement, product, exposure, quotes,
                           load_taxonomy()) == expected


def test_the_product_a_thesis_names_sets_its_segment_end_to_end(tmp_path: Path) -> None:
    """No segment in the statement's words ("CCGT" is a gas-turbine PRODUCT term, not a segment
    term) and none in its evidence: the product it is about places it — on-site generation."""
    doc = Hypo(slug="ccgt-builders", publisher="Hypo Research P", published=AS_OF, blocks=[
        ("paragraph", "Orders rose 40% in 2025 across new data-centre campuses in Texas.")])
    x = extraction([claim("c1", "b001", "Orders rose 40% in 2025", "Orders +40%", value=40,
                          value_text="40%", unit="%", period="2025")],
                   [hyp("h1", "CCGT builders win data-centre orders",
                        node="ai_infrastructure.power_grid", mechanism="demand_volume_shift",
                        supporting=["c1"])])
    pipe = make_pipeline(tmp_path)
    pipe.start_run("article", as_of=AS_OF)
    ingest(pipe, doc.doc(), x, as_of=AS_OF)
    [t] = pipe.store.theses()
    assert t.key_segment == "onsite_generation"
