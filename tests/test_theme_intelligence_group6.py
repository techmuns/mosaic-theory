"""Group 6 of the review leads — VERIFICATION AND EXTRACTION CHECKS (U17, U19, U20, U48). Verified
on main d304ea16 (`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`); the
corpus runs (the pilot's text, its mentions and cards, every cached answer, every local registry's
geographies) are in the build record.

End to end through the REAL verifier and engine on HYPOTHETICAL articles (invented text on the
reserved `.test` domain), extractions in the REAL type. No network, no model call.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.theme_intelligence_support import (
    Hypo,
    claim,
    extraction,
    hyp,
    ingest,
    make_pipeline,
    mention,
)
from vinci.theme_intelligence.completeness import quote_covers, scan_article
from vinci.theme_intelligence.engine import geographies_overlap, norm_geo
from vinci.theme_intelligence.extract import answer_list
from vinci.theme_intelligence.schemas import RecommendationStatus, RunStatus
from vinci.theme_intelligence.verify import (
    _RECO,
    card_sentences,
    review_card,
    without_named_indices,
)

AS_OF = date(2026, 10, 14)
MEM = "ai_infrastructure.memory"


# --- U17a: a date is found whole, never inside a longer one ---------------------------------------

@pytest.mark.parametrize(("note", "kept"), [
    ("Source: Test Data. Data as of 15 February 2026.", False),  # "5 February" inside it
    ("Source: Test Data. Data as of 5 February 2026.", True),
])
def test_an_as_of_date_is_found_whole_in_its_source_note(tmp_path: Path, note: str,
                                                         kept: bool) -> None:
    """A claim measured as of 5 February 2026 whose cited source note says 15 February: the as-of
    was "found" inside the longer date and kept. NEGATIVE pin: the note's own date is kept."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    line = "Memory contract prices rose 9% in the quarter."
    art = Hypo("asof", "Test Publisher", date(2026, 10, 1),
               [("paragraph", line), ("paragraph", note)])
    x = extraction([claim("c1", "b001", line.rstrip("."), "Memory prices +9%",
                          metric="memory price", value=9, value_text="9%", unit="%",
                          period="the quarter", measured_as_of="2026-02-05", as_of_block="b002")],
                   [hyp("h1", "Memory prices climb", node=MEM, mechanism="pricing_cycle",
                        supporting=["c1"])])
    r = ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert r.article_id is not None
    (c,) = pipe.store.claims_for_article(r.article_id)
    assert (c.measured_as_of == date(2026, 2, 5)) is kept


# --- U17b: recommendation language is read as words -----------------------------------------------

@pytest.mark.parametrize(("quote", "reco"), [
    ("We upgraded the shares to Overweight after the print", True),
    ("Analysts downgrade Micron to Neutral", True),
    ("We rate the stock Buy", True),
    ("It remains our top pick in the group", True),
    ("Investors may add to positions on weakness", True),
    ("operating margins expanded on mix", False),  # "rating" inside "operating"
    ("grid upgrades will lift utility capex", False),  # an upgrade TO no rating
    ("the contract could add to revenue next year", False),  # "add to" no position
    ("We upgrade the stock to Buy, citing HBM pricing", True),
    ("utilities plan grid upgrades to add 20 GW of capacity", False),  # "add" names no rating
    ("grid upgrades to hold down losses", False),  # nor "hold" (review of #724)
])
def test_recommendation_language_is_words_never_a_fragment(quote: str, reco: bool) -> None:
    assert (_RECO.search(quote) is not None) is reco


def test_a_mention_marked_a_recommendation_without_its_language_is_downgraded(
        tmp_path: Path) -> None:
    """End to end: "operating" vouched for a rating label. NEGATIVE pin: an upgrade to a rating
    keeps it."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    lines = ("Micron's operating margins expanded as HBM prices rose 9% in the quarter.",
             "We upgraded SK Hynix to Overweight as HBM prices rose 9% in the quarter.")
    art = Hypo("reco", "Test Publisher", date(2026, 10, 1), [("paragraph", x) for x in lines])
    x = extraction([claim("c1", "b001", "HBM prices rose 9% in the quarter", "HBM prices +9%",
                          metric="HBM price", value=9, value_text="9%", unit="%",
                          period="the quarter")],
                   [hyp("h1", "HBM prices climb", node=MEM, mechanism="pricing_cycle",
                        supporting=["c1"])],
                   mentions=[mention("Micron", "b001", lines[0].rstrip("."), ticker="MU",
                                     reco="rating_stated"),
                             mention("SK Hynix", "b002", lines[1].rstrip("."),
                                     reco="rating_stated")])
    r = ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    assert r.article_id is not None
    by = {m.name_as_written: m.recommendation_status
          for m in pipe.store.mentions_for_article(r.article_id)}
    assert by["Micron"] is RecommendationStatus.NOT_A_RECOMMENDATION
    assert by["SK Hynix"] is RecommendationStatus.RATING_STATED


# --- U17c: a number with a unit is a figure, never an index's name --------------------------------

def test_a_figure_after_an_index_name_is_still_a_figure() -> None:
    """"DAX 30%" and "Nasdaq 25%" were excused as index names, so a card line printing them passed
    against claims that carry neither. NEGATIVE pin: the index names themselves stay excused."""
    for text, figure in (("The DAX 30% rally", "30%"), ("a Nasdaq 25% drawdown", "25%")):
        assert figure in without_named_indices(text)
    for text, name in (("The S&P 500 rose", "500"), ("the DAX 40 index", "40"),
                       ("the Nasdaq 100 and the Nikkei 225", "225")):
        assert name not in without_named_indices(text)


# --- U17d / U20: a model's list as the objects it holds -------------------------------------------

def test_a_list_field_is_read_as_its_objects_and_anything_else_is_said() -> None:
    rows = [{"a": 1}, {"b": 2}]
    assert answer_list({"x": rows}, "x") == (rows, [])
    items, notes = answer_list({"x": json.dumps(rows)}, "x")
    assert items == rows and "arrived as JSON text" in notes[0]
    items, notes = answer_list({"x": ["oops", {"a": 1}]}, "x")
    assert items == [{"a": 1}] and "1 of 2 item(s) not an object" in notes[0]
    assert answer_list({"x": "not json"}, "x")[0] == []
    assert "none read" in answer_list({"x": 7}, "x")[1][0]


class _Reviewer:
    model = "claude-opus-4-8"
    last_usage = {"input_tokens": 10, "output_tokens": 10}

    def __init__(self, answer: dict[str, Any]) -> None:
        self.answer = answer

    def extract(self, **_kw: Any) -> dict[str, Any]:
        return self.answer


def test_a_review_answer_of_strings_or_text_never_crashes_and_is_said(tmp_path: Path) -> None:
    """A verdict list sent as JSON text, or holding strings, raised AttributeError — and again on
    every cached replay. Now the text is decoded, a string is set aside and recorded, and the
    lines it left without a verdict read MISSING, as for any answer that omits one."""
    from tests.test_theme_intelligence_enrichment import _memory_thesis

    pipe, tid = _memory_thesis(tmp_path)
    v = pipe.store.thesis_version(tid, 1)
    assert v is not None
    claims = {c.claim_id: c for a in pipe.store.articles()
              for c in pipe.store.claims_for_article(a.article_id)}
    sid = next(iter(card_sentences(v.content)))
    as_text = {"verdicts": json.dumps([{"sentence_id": sid, "verdict": "SUPPORTED"}])}
    got = review_card(v.content, claims, client=_Reviewer(as_text), cache_dir=tmp_path / "a",
                      run_id="R-x")
    assert got.verdicts[sid][0] == "SUPPORTED"
    mixed = {"verdicts": ["SUPPORTED", {"sentence_id": sid, "verdict": "SUPPORTED"}]}
    for client in (_Reviewer(mixed), None):  # the call, then its cached replay
        got = review_card(v.content, claims, client=client, cache_dir=tmp_path / "b",
                          run_id="R-x")
        assert got.verdicts[sid][0] == "SUPPORTED"
        assert [i.code for i in got.issues].count("REVIEW_ANSWER_UNREADABLE") == 1


def test_an_enrichment_answer_sent_as_text_is_read_and_a_broken_one_is_said(
        tmp_path: Path) -> None:
    """`companies` as JSON text gave 0 candidates, 0 refused and an empty note. NEGATIVE pin: text
    that is not JSON gives no candidate, and the set says why."""
    from tests.test_theme_intelligence_enrichment import ANSWER, StandIn, _memory_thesis
    from vinci.theme_intelligence.budget import GuardedClient

    pipe, tid = _memory_thesis(tmp_path)
    pipe.client = GuardedClient(StandIn({"companies": json.dumps(ANSWER["companies"])}),
                                pipe.guard)
    pipe.run_enrich(as_of=date(2026, 2, 9))
    (es,) = pipe.store.enrichments(tid)
    assert {c.name for c in es.candidates} == {"Amazon", "ASML Holding"}
    assert any("arrived as JSON text" in r for r in es.refused)
    pipe2, tid2 = _memory_thesis(tmp_path / "broken")
    pipe2.client = GuardedClient(StandIn({"companies": "[{broken"}), pipe2.guard)
    pipe2.run_enrich(as_of=date(2026, 2, 9))
    (es2,) = pipe2.store.enrichments(tid2)
    assert not es2.candidates and any("not valid JSON" in r for r in es2.refused)
    # an entry set aside is numbered among the objects READ, so the count says its population
    pipe3, tid3 = _memory_thesis(tmp_path / "mixed")
    pipe3.client = GuardedClient(StandIn({"companies": ["oops", {"direction": "benefit"}]}),
                                 pipe3.guard)
    pipe3.run_enrich(as_of=date(2026, 2, 9))
    (es3,) = pipe3.store.enrichments(tid3)
    assert any(r.startswith("object 1 of 1 read: no name") for r in es3.refused), es3.refused


# --- U19: a figure after a sentence's first word, and a word figure read whole --------------------

def _doc(*lines: str) -> Any:
    return Hypo("figs", "Test Publisher", date(2026, 10, 1),
                [("paragraph", x) for x in lines]).doc()


def test_a_figure_after_a_sentence_initial_word_is_a_figure_and_a_name_still_is_not() -> None:
    """The pilot's "Another 16 were documented", "Only 3 touched", "Across 9 labs" were skipped as
    names. NEGATIVE pin: "S&P 500", "Mag 7" are still names, and a day before a month a PDF cut
    short is still a date."""
    led = scan_article(_doc("Another 16 were documented only afterwards.",
                            "Only 3 touched cyber-offence risks.",
                            "Nearly 300 companies reported it."))
    assert {f.core for f in led.figures} >= {"16", "3", "300"}
    names = scan_article(_doc("The S&P 500 rose while the Mag 7 lagged.",
                              "On 14 Septemb 2026, he wrote that fears were overdone."))
    assert not {f.core for f in names.figures} & {"500", "7", "14"}
    # NEGATIVE (review of #724): a word that only BEGINS with a month stem is no month
    not_dates = scan_article(_doc("Spend reached 14 marketing 2026 budgets across the group."))
    assert "14" in {f.core for f in not_dates.figures}


def test_a_figure_in_words_is_covered_only_by_its_words() -> None:
    """"ten years" was covered by "Their content libraries took years" ("ten" inside "content")."""
    assert not quote_covers("Their content libraries took years to build", "ten years")
    assert quote_covers("It took over ten years to build", "ten years")


# --- U48: one geography vocabulary for the key and the overlap test -------------------------------

@pytest.mark.parametrize(("written", "key"), [
    ("Global ex-U.S.", "Global ex-US"), ("Global ex-US", "Global ex-US"),
    ("Asia ex-Japan", "APAC ex-Japan"), ("United States (esp. Texas)", "US"),
    ("US", "US"), ("Canada", "Canada"), ("US, South Korea, Taiwan", "US, South Korea, Taiwan"),
    ("Texas", "Texas"),  # NEGATIVE: a place inside a region keeps its own key
])
def test_a_geography_is_keyed_one_way_however_it_is_spelt(written: str, key: str) -> None:
    assert norm_geo(written) == key


@pytest.mark.parametrize(("a", "b", "overlap"), [
    ("Global ex-US", "US", False), ("Global ex-U.S.", "Texas", False),
    ("Asia ex-Japan", "Japan", False), ("Latin America", "US", False),
    ("Global ex-US", "China", True), ("Asia ex-Japan", "Korea", True),  # NEGATIVE pins
    ("APAC", "Japan", True), ("Texas", "US", True), ("Global", "US", True),
    ("Global ex-US", "Global ex-China", True),
])
def test_a_geography_leaves_out_what_it_excludes(a: str, b: str, overlap: bool) -> None:
    assert geographies_overlap(a, b) is overlap and geographies_overlap(b, a) is overlap


def test_two_spellings_of_one_exclusion_are_one_thesis(tmp_path: Path) -> None:
    """End to end: "Global ex-U.S." and "Global ex-US" were two identity keys, two theses."""
    pipe = make_pipeline(tmp_path)
    pipe.start_run("ingest", as_of=AS_OF)
    for n, geo in enumerate(("Global ex-U.S.", "Global ex-US")):
        line = f"Memory contract prices outside the US rose {9 + n}% in the quarter."
        art = Hypo(f"geo-{n}", f"Publisher {n}", date(2026, 10, 1 + n), [("paragraph", line)])
        x = extraction([claim("c1", "b001", line.rstrip("."), f"Prices +{9 + n}%",
                              metric=f"memory price {n}", value=9 + n, value_text=f"{9 + n}%",
                              unit="%", period="the quarter")],
                       [hyp("h1", "Memory prices climb outside the US", node=MEM,
                            mechanism="pricing_cycle", geography=geo, supporting=["c1"])])
        ingest(pipe, art.doc(), x, as_of=AS_OF, publisher=art.publisher)
    pipe.finish_run(RunStatus.SUCCEEDED)
    (t,) = pipe.store.theses()
    assert t.key_geography == "Global ex-US" and t.current_version == 2
