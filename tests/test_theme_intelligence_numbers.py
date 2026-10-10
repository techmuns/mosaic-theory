"""How a number is READ — false number failures found by the 2026-10-10 live runs.

- "GLM-5.3" was read as the figure 5.3: it blocked a SemiAnalysis card's bottom line ("prints
  '5.3', which none of its cited claims carry") and put eight false figures in the ledger.
- A verbatim "doubling memory footprint" claimed as 2 failed its number check and was dropped,
  leaving its paragraph unaccounted for.
- The ledger split the word range "three-four months" into "four months", and missed unit-glued
  figures: "75GW", "930MW", "744B", and J.P. Morgan's "99th percentile".

Every number check reads ONE shared helper (`stated_numbers`, `word_numbers`); the articles are
HYPOTHETICAL and labelled as such.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from tests.theme_intelligence_support import Hypo, claim, extraction, hyp, ingest, make_pipeline
from vinci.theme_intelligence.completeness import scan_article
from vinci.theme_intelligence.extract import Extraction
from vinci.theme_intelligence.verify import stated_numbers, verify_extraction, word_numbers

AS_OF = date(2026, 9, 28)


# --- the shared readings ----------------------------------------------------------------------

@pytest.mark.parametrize(("text", "want"), [
    ("GLM-5.3 serving lifts GB300 throughput 1.8x", ["1.8"]),  # a version is part of a name
    ("COVID-19 cut output 12% and an S-1 followed", ["12"]),
    ("GPT-5 and Llama-3.1 are model names", []),
    ("capacity rises in 2027-2028", ["2027", "2028"]),  # a range is two numbers
    ("margins of 5-10% by mid-2028", ["5", "10", "2028"]),  # lower-case prefix: not a name
    ("prices fell -10% on the week", ["-10"]),
    ("B200 and H100 ship 2,600 units", ["2,600"]),
])
def test_stated_numbers_are_figures_never_parts_of_a_name(text: str, want: list[str]) -> None:
    assert stated_numbers(text) == want


@pytest.mark.parametrize(("text", "want"), [
    ("twenty-four months", [24.0]),
    ("twenty four months", [24.0]),
    ("seven straight quarters", [7.0]),
    ("three-four months", [3.0, 4.0]),
    ("a hike", []),
])
def test_number_words_are_read_whole(text: str, want: list[float]) -> None:
    assert word_numbers(text) == want


# --- the claim number check, through verification ---------------------------------------------

def _verify(quote: str, value: float, value_text: str, unit: str | None = None) -> list[str]:
    art = Hypo(slug="numbers", publisher="Hypo Research A", published=AS_OF,
               blocks=[("paragraph", f"Sparse attention comes {quote} in serving, the "
                                     f"benchmark shows across every tested configuration.")])
    x = extraction([claim("c1", "b001", quote, "memory footprint", value=value,
                          value_text=value_text, unit=unit)], [])
    x["attributed_authors"] = []
    ve = verify_extraction(art.doc(), Extraction.model_validate(x), article_id="A-1",
                           article_version_id="AV-1", extraction_id="X-1",
                           publisher=art.publisher, as_of=AS_OF, run_id="R-1")
    return [i.code for i in ve.issues if i.code.startswith("NUMBER")]


@pytest.mark.parametrize(("quote", "value", "value_text", "unit"), [
    ("at the cost of doubling memory footprint", 2.0, "doubling", None),
    ("at the cost of doubling memory footprint", 100.0, "doubling", "%"),  # +100% is the same
    ("with memory footprint halved", 0.5, "halved", None),
    ("after twenty-four months of delay", 24.0, "twenty-four months", "months"),
])
def test_a_figure_written_in_words_passes_its_number_check(quote: str, value: float,
                                                           value_text: str,
                                                           unit: str | None) -> None:
    assert _verify(quote, value, value_text, unit) == []


@pytest.mark.parametrize(("quote", "value", "value_text"), [
    ("at the cost of doubling memory footprint", 3.0, "doubling"),
    ("after twenty-four months of delay", 4.0, "twenty-four months"),  # never the tail word
])
def test_a_wrong_value_for_a_word_figure_still_fails(quote: str, value: float,
                                                     value_text: str) -> None:
    assert _verify(quote, value, value_text) == ["NUMBER_NOT_IN_SPAN"]


# --- the ledger ---------------------------------------------------------------------------------

def test_the_ledger_reads_unit_figures_ranges_and_percentiles_and_skips_names() -> None:
    doc = Hypo(slug="ledger-units", publisher="Hypo Research A", published=AS_OF, blocks=[
        ("paragraph", "GLM-5.3 cut KV-cache reads by 40% while the 744B model served 77K "
                      "tokens on B200 and 5G links."),
        ("paragraph", "Developers ordered 75 GW of turbines, a 1.5GW site needs 930MW firm, and "
                      "the top ten sat in the 99th percentile."),
        ("paragraph", "Texas adds perhaps three-four months of delay and new lines take "
                      "twenty-four months to energise."),
    ]).doc()
    by_block: dict[str, list[str]] = {}
    for f in scan_article(doc).figures:
        by_block.setdefault(f.block_id, []).append(f.text)
    assert by_block["b001"] == ["40%", "744B", "77K"]  # no "5.3", no "5", nothing from "B200"
    assert by_block["b002"] == ["75 GW", "1.5GW", "930MW", "99th percentile"]
    assert by_block["b003"] == ["three-four months", "twenty-four months"]


# --- the card-line check, end to end ----------------------------------------------------------

def _card_number_blocks(tmp_path: Path, title: str) -> list[str]:
    pipe = make_pipeline(tmp_path)
    run = pipe.start_run("fixture", as_of=AS_OF)
    art = Hypo(slug="name-number", publisher="Hypo Research A", published=AS_OF,
               blocks=[("paragraph", "DRAM contract prices rose 9% in the quarter as GLM-5.3 "
                                     "serving and other inference workloads absorbed supply.")])
    ingest(pipe, art.doc(), extraction(
        [claim("c1", "b001", "DRAM contract prices rose 9% in the quarter", "DRAM +9%",
               value=9, value_text="9%", unit="%", period="the quarter")],
        [hyp("h1", title, node="ai_infrastructure.memory", mechanism="pricing_cycle",
             supporting=["c1"])]), as_of=AS_OF, publisher=art.publisher)
    return [i.detail for i in pipe.store.issues(run_id=run.run_id)
            if i.code == "NUMBER_NOT_IN_CITED_CLAIMS"]


def test_a_model_version_in_a_card_line_is_not_a_figure_its_claims_must_carry(
        tmp_path: Path) -> None:
    assert _card_number_blocks(tmp_path, "GLM-5.3 serving keeps DRAM demand rising") == []


def test_a_real_figure_its_claims_lack_still_blocks_the_line(tmp_path: Path) -> None:
    got = _card_number_blocks(tmp_path, "DRAM prices up 5.3% on GLM-5.3 serving")
    assert got and all("'5.3'" in d for d in got)
