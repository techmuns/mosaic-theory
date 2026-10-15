"""PDF verification quality — deterministic causes of OPEN evidence, corrected where the evidence
itself is sound, and left OPEN where it is not.

Observed 2026-10-11 on Citi's 60-page "Overcoming Gridlock 2.0" report (real run): 17 of 851
stated figures open; on its ETF report 5 of 232. Three causes were defects of the CHECK, not of
the evidence — every one re-derived from cached model answers, no new model call:

1. a decline stated in WORDS read as a negative value — "U.S. EV sales in 1Q 2026 were down ~27%
   YoY" with value -27 failed the number check (three claims);
2. a figure written with an ELLIPSIS — "12 ... 30 or more" for "wait times can extend to 12
   months, or even 30 or more" failed it (one claim);
3. a figure RESTATED in a chart caption, a table or a summary was looked for only in its own
   block, while the completeness pass had named the claim where the prose states it (most of the
   capture_not_verified figures).

Quoted sentences are verbatim from that public Citi GPS report, one sentence each; the lines
marked HYPOTHETICAL are composed for the test (a different fact sharing a figure).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.completeness import Figure, states_figure
from vinci.theme_intelligence.pipeline import Pipeline
from vinci.theme_intelligence.report import research_verification
from vinci.theme_intelligence.verify import _number_check

EV = "U.S. EV sales in 1Q 2026 were down ~27% YoY"
EU = "EU27+UK demand down ~10% over the past 15 years"
WAIT = ("Depending on the voltage and class, wait times can extend to 12 months, or even 30 or "
        "more.")


# --- 1. a decline stated in words ------------------------------------------------------------

@pytest.mark.parametrize(("value", "vt", "quote"), [
    (-27.0, "~27%", EV),
    (-10.0, "~10%", EU),
    (-20.0, "~20%", "with industrial demand down ~20%"),
    (-4.0, "4%", "Unit shipments fell by about 4% in the quarter"),
    (-27.0, "27%", "a 27% drop in orders"),
])
def test_a_decline_stated_in_words_carries_the_minus(value: float, vt: str, quote: str) -> None:
    assert _number_check(value, vt, "%", quote)[0] is True


@pytest.mark.parametrize(("value", "vt", "quote"), [
    (-4.0, "4%", "the policy rate fell to 4%"),  # a level, not a change
    (-27.0, "~27%", "U.S. EV sales in 1Q 2026 were up ~27% YoY"),  # a rise
    (-27.0, "~27%", "EV sales were ~27% of new car sales, down from the prior year"),  # far off
    (-28.0, "~27%", EV),  # the wrong magnitude
])
def test_a_negative_value_without_a_stated_decline_still_fails(value: float, vt: str,
                                                                quote: str) -> None:
    assert _number_check(value, vt, "%", quote)[0] is False


def test_a_positive_reading_of_a_stated_decline_is_unchanged() -> None:
    assert _number_check(27.0, "~27%", "%", EV)[0] is True  # "a 27% decline", as before


# --- 2. a figure written with an ellipsis ----------------------------------------------------

def test_an_elided_figure_is_verbatim_piece_by_piece() -> None:
    assert _number_check(None, "12 ... 30 or more", "months", WAIT)[0] is True
    assert _number_check(None, "12 … 30 or more", "months", WAIT)[0] is True


@pytest.mark.parametrize("vt", ["12 - 30+",  # a reformatted range is not in the sentence
                                "12 ... 40 or more",  # a piece the sentence does not state
                                "30 or more ... 12",  # out of order
                                "2 ... 30 or more",  # '2' is not a piece of '12'
                                "12 ..."])  # an ellipsis with nothing after it
def test_an_elided_figure_with_a_piece_not_in_the_quote_fails(vt: str) -> None:
    assert _number_check(None, vt, "months", WAIT)[0] is False
    # an empty piece places nowhere, even where the quote has a free-standing dash
    assert _number_check(None, vt, "months", "lead times of 12 months - or even 30 or more")[0] \
        is False


# --- 3. a restated figure is captured where the article states it -----------------------------

INFOGRAPHIC = ("Large Power Transformers Medium/High-Voltage Substation Transformers Used in "
               "utility substations, Prices are about 80% higher over Large Unit Lead Times = "
               "the last five years 24-48 months")


@pytest.mark.parametrize(("sentence", "core", "quote", "same"), [
    ("Wood Mackenzie estimates that power transformers are in a supply deficit of 30% based on "
     "annual supply and demand estimates in 2025.", "30%", "an assumed 30% deficit", True),
    ("Figure 12. 2025 market share by capacity total 2,358.5GVA", "2,358.5",
     "based on global transformer supply of 2,358.5GVA", True),  # the same precise number
    ("The U.S. is the exception: 1Q 2026 sales were down ~27% YoY, although the decline slowed "
     "from 4Q 2025.", "27%", EV, True),
    # CONSERVATIVE: the same fact in different words beside the figure ("are about 80% higher"
    # / "have risen about 80% over") stays open for a human — a missed restatement leaves a gap
    # visible; a false match would hide one
    (INFOGRAPHIC, "80%", "transformer prices have risen about 80% over five years", False),
    # the same number, a different fact — imports share "power" with the long infographic text,
    # but nothing beside the figure
    (INFOGRAPHIC, "80%", "imports account for an estimated 80% of U.S. power transformer "
                         "supply and 50% of distribution transformer supply", False),
    # a unit glued to the figure is part of it, not a word beside it (the real table text)
    ("| 50-GW+ of data center capacity was | | | | 24% CAGR increase since | |", "50",
     "U.S. data center capacity exceeded 50 GW in 2025, growing at a 24% CAGR since 2020", True),
    # HYPOTHETICAL: the same number measuring something else
    ("Gross margins reached 30% in 2025.", "30%", "an assumed 30% deficit", False),
    ("Lead times reached 2,358 days.", "2,358", "a backlog of 2,358 units", False),
    # HYPOTHETICAL: the shared SUBJECT right beside a different MEASURE
    ("Power transformers: prices are about 80% higher than they were over the past cycle.",
     "80%", "imports account for an estimated 80% of U.S. power transformer supply", False),
])
def test_a_named_claim_states_a_restated_figure_only_when_it_is_the_same_fact(
        sentence: str, core: str, quote: str, same: bool) -> None:
    f = Figure(f"b099#{core}", "b099", core, core, sentence)
    assert states_figure(quote, f) is same


# --- end to end: registry → completeness ledger → research verification -----------------------

GRID = "ai_infrastructure.power_grid"
SUPPLY = ("Wood Mackenzie estimates a 707.5GVA annual shortfall in 2025, based on global "
          "transformer supply of 2,358.5GVA and an assumed 30% deficit, implying that some "
          "current demand is being deferred until additional supply comes online.")
RESTATED = ("Wood Mackenzie estimates that power transformers are in a supply deficit of 30% "
            "based on annual supply and demand estimates in 2025.")
IMPORTS = ("Imports account for an estimated 80% of U.S. power transformer supply and 50% of "
           "distribution transformer supply.")
#: HYPOTHETICAL — composed for the test: the shared subject beside a different measure
PRICES = "Power transformers: prices are about 80% higher than they were over the past cycle."
DOC = Hypo("citi-gridlock-restated", "Citi", date(2026, 9, 24), [
    ("paragraph", SUPPLY), ("paragraph", RESTATED), ("paragraph", IMPORTS),
    ("paragraph", "Figure 12. 2025 market share by capacity total 2,358.5GVA"),
    ("paragraph", PRICES)])


def _x() -> dict:
    cs = [claim("c1", "b001", "an assumed 30% deficit", "Transformer supply deficit of 30%",
                metric="transformer supply deficit", value=30, value_text="30%", unit="%"),
          claim("c2", "b001", "based on global transformer supply of 2,358.5GVA",
                "Global transformer supply 2,358.5 GVA", metric="global transformer supply",
                value=2358.5, value_text="2,358.5", unit="GVA"),
          claim("c3", "b003", "Imports account for an estimated 80% of U.S. power transformer "
                              "supply", "Imports are ~80% of US power transformer supply",
                metric="import share", value=80, value_text="80%", unit="%")]
    return extraction(cs, [hyp("h1", "Transformer shortage", node=GRID,
                               mechanism="supply_constraint", supporting=["c1", "c2", "c3"])])


def _review(figure_id: str, claim_ids: list[str]) -> dict:
    return {"figure_id": figure_id, "verdict": "captured_by_added_claim",
            "claim_ids": claim_ids, "reason": "the same figure, stated elsewhere"}


@pytest.fixture()
def pipe(tmp_path: Path) -> Pipeline:
    p = make_pipeline(tmp_path)
    p.start_run("article", as_of=date(2026, 10, 11))
    return p


def test_a_restated_figure_is_captured_where_stated_and_a_different_fact_stays_open(
        pipe: Pipeline) -> None:
    # the ledger reads "2,358.5GVA" whole (it was cut to "2,358" until GVA was a known unit)
    comp = {"figure_reviews": [_review("b002#30%", ["c1"]), _review("b004#2,358.5", ["c2"]),
                               _review("b005#80%", ["c3"])]}  # c3 is a DIFFERENT 80%
    res = ingest(pipe, DOC.doc(), _x(), as_of=date(2026, 10, 11), publisher="Citi",
                 completeness=comp)
    assert res.status == "PROCESSED" and pipe.run is not None
    (rep,) = pipe.store.completeness_for_run(pipe.run.run_id)
    got = {(f.block_id, f.figure): f for f in rep.figures}
    assert got[("b002", "30%")].status == "captured" and "b001" in got[("b002", "30%")].reason
    assert got[("b004", "2,358.5GVA")].status == "captured"
    prices = got[("b005", "80%")]
    assert prices.status == "uncaptured" and prices.open_cause == "capture_not_verified"
    v = research_verification(pipe.store, pipe.run)
    assert v["status"] == "INCOMPLETE" and "capture_not_verified 1" in v["summary"]


def test_an_unnamed_restatement_is_never_captured_by_coincidence(pipe: Pipeline) -> None:
    """Only a claim the completeness pass NAMES can capture a restated figure."""
    ingest(pipe, DOC.doc(), _x(), as_of=date(2026, 10, 11), publisher="Citi",
           completeness={"figure_reviews": []})
    assert pipe.run is not None
    (rep,) = pipe.store.completeness_for_run(pipe.run.run_id)
    assert {(f.block_id, f.status) for f in rep.figures if f.block_id == "b002"} == {
        ("b002", "uncaptured")}


def test_only_an_account_of_capture_can_name_the_capturing_claim(pipe: Pipeline) -> None:
    """An 'immaterial' verdict with no reason leaves the figure open, whatever claim it names."""
    bad = {"figure_id": "b002#30%", "verdict": "immaterial", "claim_ids": ["c1"], "reason": ""}
    ingest(pipe, DOC.doc(), _x(), as_of=date(2026, 10, 11), publisher="Citi",
           completeness={"figure_reviews": [bad]})
    assert pipe.run is not None
    (rep,) = pipe.store.completeness_for_run(pipe.run.run_id)
    assert [f.status for f in rep.figures if f.block_id == "b002"] == ["uncaptured"]
