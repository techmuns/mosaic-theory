"""A covenant rate component is shown only when a quote STATES it — the term's own, or a clause of
the component's own that is a span of the exhibit.

#804 proved every covenant quote is a span of its exhibit. #829's `figure_in_own_quote` then found
29 of 48 committed rate components that their quote does not state: the quote says "LIBO Rate …
plus the Applicable Rate", the row says margin 0.50% and floor 0%. Each figure IS in its exhibit,
in another clause — or is one level of a pricing grid. `covenant_extract.rate_components` keeps a
component its own clause states and WITHHOLDS the rest with the reason
(`docs/records/2026-10-28-a-label-names-its-own-year-and-a-rate-its-own-quote.md`).

Every pin runs on FROZEN real text: the committed rows as the model wrote them, and windows of the
real exhibits (`tests/fixtures/covenant_components/`, README there).
"""
from __future__ import annotations

import json
import pathlib
from collections import Counter
from typing import Any

import pytest

from vinci.dossier import covenant_extract as ce
from vinci.dossier.render import _compose_interest_lead
from vinci.dossier.schemas import CovenantPointer, CovenantTerm
from vinci.quality.sources import release
from vinci.verbatim import SourceText

FIX = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "covenant_components"
ROWS: dict[str, Any] = json.loads((FIX / "rows.json").read_text())
AMZN_2020 = "8-K 0001193125-20-176528 · d948849dex101.htm"


def _text(name: str) -> str:
    return (FIX / f"{name}.txt").read_text().strip()


def _quote(row: dict[str, Any]) -> str:
    return str(row["value"]["note"])[len("verbatim: “"):-1]


def _model_output(row: dict[str, Any], **own: str) -> dict[str, Any]:
    """The tool answer a committed row was built from: its components, as the model gave them."""
    out = {k: row.get(k) for k in ce.RATE_COMPONENTS}
    return {**out, **own}


def _amzn_2020() -> dict[str, Any]:
    rows = ROWS["AMZN"]["covenant_term_rows"]
    return next(r for r in rows if r["value"]["source_ref"] == AMZN_2020)


#: The clauses the AMZN 2020 agreement states its margin and floor in, read off the real exhibit.
AMZN_MARGIN_CLAUSE = ("“ Applicable Rate ” means (a) with respect to Base Rate Loans, 0.00% per "
                      "annum, (b) with respect to Eurocurrency Rate Loans, 0.50% per annum, and "
                      "(c) with respect to the commitment fee set forth in Section 2.07(a) , 0.04% "
                      "per annum.")
AMZN_FLOOR_CLAUSE = ("if any Screen Rate, determined as provided above, would be less than zero, "
                     "such Screen Rate shall be deemed to be zero")
AMZN_TEXT = " ".join(_text(n) for n in (
    "AMZN-2020-interest", "AMZN-2020-applicable-rate", "AMZN-2020-screen-rate"))
AMZN_SOURCE = SourceText(AMZN_TEXT)


# --- THE CORPUS: the 48 committed components, through the gate -----------------------------------


def _gate_committed() -> tuple[Counter[str], Counter[str]]:
    kept: Counter[str] = Counter()
    withheld: Counter[str] = Counter()
    for ticker, page in ROWS.items():
        for row in page["covenant_term_rows"]:
            rc = ce.rate_components(_model_output(row), _quote(row), SourceText(""))
            kept[ticker] += sum(v is not None for v in rc.values.values())
            withheld[ticker] += len(rc.withheld)
    return kept, withheld


def test_the_committed_components_no_quote_states_are_withheld() -> None:
    """The 29 #829 counted differs-unexplained, by name, and the 19 it confirmed — the gate and the
    scorecard read one test (`release_parse.figure_stated`)."""
    kept, withheld = _gate_committed()
    assert sum(kept.values()) == 19 and sum(withheld.values()) == 29
    assert +withheld == Counter({"AMZN": 3, "AORT": 2, "BRBR": 1, "BURL": 2, "CNXC": 1, "EPAM": 2,
                                 "IT": 2, "NCNO": 2, "NFLX": 5, "NKE": 1, "PARR": 1, "TJX": 1,
                                 "UBER": 3, "WERN": 1, "WLK": 2})


def test_a_component_its_term_quote_states_is_kept_with_no_quote_of_its_own() -> None:
    row = next(r for r in ROWS["UBER"]["covenant_term_rows"] if r.get("margin_pct") == 2.75)
    rc = ce.rate_components(_model_output(row), _quote(row), SourceText(""))
    assert rc.values["margin_pct"] == 2.75
    assert rc.quotes == {}
    assert set(rc.withheld) == {"floor_pct"}           # its floor of 0, which the quote never says


def test_a_deferred_margin_and_floor_with_no_quote_of_their_own_are_withheld_and_named() -> None:
    row = _amzn_2020()
    rc = ce.rate_components(_model_output(row), _quote(row), AMZN_SOURCE)
    assert rc.values["margin_pct"] is None and rc.values["floor_pct"] is None
    assert rc.withheld == {
        "margin_pct": "margin 0.5% withheld — the term's quote does not state it and no quote of "
                      "its own was given",
        "floor_pct": "floor 0% withheld — the term's quote does not state it and no quote of its "
                     "own was given"}


# --- A COMPONENT'S OWN CLAUSE: kept when it is in the exhibit and states the figure ---------------


def test_a_deferred_component_is_kept_with_the_clause_that_states_it() -> None:
    row = _amzn_2020()
    out = _model_output(row, margin_quote=AMZN_MARGIN_CLAUSE, floor_quote=AMZN_FLOOR_CLAUSE)
    rc = ce.rate_components(out, _quote(row), AMZN_SOURCE)
    assert rc.values["margin_pct"] == 0.5 and rc.values["floor_pct"] == 0.0
    assert rc.quotes == {"margin_pct": AMZN_MARGIN_CLAUSE, "floor_pct": AMZN_FLOOR_CLAUSE}
    assert rc.withheld == {}


def test_a_floor_in_the_base_rates_definition_is_kept_with_it() -> None:
    """AORT's 2.00% floor sits in "Adjusted Term SOFR", not in the margin clause its row quotes."""
    rows = ROWS["AORT"]["covenant_term_rows"]
    row = next(r for r in rows if r.get("margin_pct") == 4.75)
    clause = ("if Adjusted Term SOFR at any time would otherwise be less than two percent (2.00%), "
              "such rate shall be deemed to be two percent (2.00%)")
    rc = ce.rate_components(_model_output(row, floor_quote=clause), _quote(row),
                            SourceText(_text("AORT-2025-adjusted-term-sofr")))
    assert rc.values == {"margin_pct": 4.75, "margin_bps": None, "floor_pct": 2.0, "pik_pct": None}
    assert rc.quotes == {"floor_pct": clause}


def test_an_own_quote_that_is_not_in_the_exhibit_withholds() -> None:
    """The model's own stitched summary — AMZN's committed `value` — is no clause of the document
    (checked against the whole exhibit when the fixture was cut): it cannot vouch for 0.50%."""
    row = _amzn_2020()
    stitched = str(row["value"]["value"])
    assert "0.50% per annum" in stitched and not AMZN_SOURCE.match(stitched).found
    rc = ce.rate_components(_model_output(row, margin_quote=stitched), _quote(row), AMZN_SOURCE)
    assert rc.values["margin_pct"] is None
    assert rc.withheld["margin_pct"] == "margin 0.5% withheld — its own quote is not in the exhibit"


def test_an_own_quote_that_states_another_figure_withholds() -> None:
    row = _amzn_2020()
    rc = ce.rate_components(_model_output(row, margin_quote=AMZN_FLOOR_CLAUSE), _quote(row),
                            AMZN_SOURCE)
    assert rc.values["margin_pct"] is None
    assert rc.withheld["margin_pct"] == "margin 0.5% withheld — its own quote does not state it"


def test_a_grid_tier_quoted_with_its_grid_passes_and_says_so() -> None:
    """THE LIMIT, PINNED. The gate proves a quote STATES the figure, not that the figure is the
    one in force: NCNO's 2.00% is the first of three leverage levels, and its grid states it. The
    prompt asks the model to omit a grid margin unless the document names the level; nothing
    deterministic checks that. Falsifier: a grid rule here, and this test then fails."""
    row = next(r for r in ROWS["NCNO"]["covenant_term_rows"] if r.get("margin_pct") == 2.0)
    text = _text("NCNO-2024-pricing-grid")
    grid = text[text.index("Level Consolidated Total Leverage Ratio"):text.index(" Any increase")]
    rc = ce.rate_components(_model_output(row, margin_quote=grid), _quote(row), SourceText(text))
    assert rc.values["margin_pct"] == 2.0 and rc.quotes == {"margin_pct": grid}


# --- END TO END: the extractor's row, its flags, its JSON and the lead the page prints ------------


class _Model:
    def __init__(self, answer: dict[str, Any]) -> None:
        self.answer = answer

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        return self.answer


def _extract(**own: str) -> tuple[list[CovenantTerm], list[str]]:
    row = _amzn_2020()
    term = {"name": row["name"], "present": True, "value": row["value"]["value"],
            "quote": _quote(row), "base_rate_label": row["base_rate_label"],
            **_model_output(row, **own)}
    rows, flags, _ = ce._extract_from_exhibit(
        _Model({"terms": [term]}), AMZN_TEXT, name="Amazon", ticker="AMZN",
        source_ref=AMZN_2020, title=row["agreement_title"], amendment=False)
    return rows, flags


def _lead(rows: list[CovenantTerm]) -> str:
    pointers = [CovenantPointer.model_validate(p) for p in ROWS["AMZN"]["covenant_pointer_rows"]]
    g = next(g for g in ce.governing_terms(rows, pointers) if g.term == "Interest / coupon rate")
    return _compose_interest_lead(g, str(g.value.value))[0]


def test_the_extractor_withholds_and_the_page_prints_no_unquoted_floor() -> None:
    """The printed artifact: AMZN.md led its interest line "LIBO Rate + 0.50% (Floor 0.00%)",
    neither figure in the quote the row stored."""
    rows, flags = _extract()
    assert rows[0].margin_pct is None and rows[0].floor_pct is None
    assert flags == [f"(E5) rate component not shown — {why}: Interest / coupon rate · {AMZN_2020}"
                     for why in rows[0].withheld_components.values()] and len(flags) == 2
    assert _lead(rows) == ""
    dumped = rows[0].model_dump(mode="json")
    assert "component_quotes" not in dumped and len(dumped["withheld_components"]) == 2


def test_the_extractor_keeps_a_component_with_its_own_clause_and_stores_it() -> None:
    rows, flags = _extract(margin_quote=AMZN_MARGIN_CLAUSE, floor_quote=AMZN_FLOOR_CLAUSE)
    assert flags == []
    assert rows[0].component_quotes == {"margin_pct": AMZN_MARGIN_CLAUSE,
                                        "floor_pct": AMZN_FLOOR_CLAUSE}
    assert _lead(rows) == "LIBO Rate + 0.50% (Floor 0.00%)"
    dumped = rows[0].model_dump(mode="json")
    assert "withheld_components" not in dumped
    assert CovenantTerm.model_validate(dumped) == rows[0]


@pytest.mark.parametrize("ticker", sorted(ROWS))
def test_a_committed_row_serialises_without_the_new_keys(ticker: str) -> None:
    """The pages stay byte-identical until re-assembled: neither key is written when empty."""
    for raw in ROWS[ticker]["covenant_term_rows"]:
        assert CovenantTerm.model_validate(raw).model_dump(mode="json") == raw


# --- THE SCORECARD: a component's own clause is read; a withheld one is counted, not checked ------


def _scored(rows: list[dict[str, Any]]) -> tuple[dict[str, int], int]:
    res = release._figure_in_own_quote(release.Page("AMZN", [], rows))
    return res.counts, res.excluded


def test_the_scorecard_reads_the_clause_a_component_was_kept_by() -> None:
    kept, _ = _extract(margin_quote=AMZN_MARGIN_CLAUSE, floor_quote=AMZN_FLOOR_CLAUSE)
    assert _scored([kept[0].model_dump(mode="json")]) == ({"confirmed": 2}, 0)


def test_the_scorecard_counts_a_withheld_component_as_excluded() -> None:
    assert _scored([_amzn_2020()]) == ({"differs_unexplained": 2}, 0)        # as committed
    withheld, _ = _extract()
    assert _scored([withheld[0].model_dump(mode="json")]) == ({}, 2)
