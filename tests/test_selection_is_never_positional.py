"""DOCUMENT ORDER IS NOT A CONTRACT — the invariant this incident owes.

THE INCIDENT (2026-09-11). `panels_payload.multiple_and_price` read `hist[0]`. Most dossiers carry
TWO valuation histories — `EV/EBITDA (TEV/LTM)` and `P/LTM EPS` — so the panel showed EV/EBITDA for
every name, while GOOGL's underwrite is P/E-basis (its ledger: *"the underwrite is P/E-basis"*;
its bear case: *"almost pure multiple compression 26x -> 22x"*). The tile read 25.8x at the 100th
percentile of its range; the metric the case rests on read 27.3x at the 49th — a number that says
"extreme" standing in for one that says "unremarkable", with the right entry sitting unread at
index 1.

THE REPO HAD ALREADY WRITTEN THIS DOWN, in `edgar/segments.py`, about the same company: *"DOCUMENT
ORDER IS NOT A CONTRACT. GOOGL's 10-K carries TWO '(Details)' reports naming segments … So the
ECONOMICS report is NAMED, not positioned."* The panel layer repeated it one level up.

THE TEST IS ORDER-INDEPENDENCE, not a value pin. A selector that picks by name gives the same
answer however the list is shuffled; one that picks by position does not. That property holds for
any future list-reading builder, which a pin on today's metric label would not.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.panels_payload import (
    DEFAULT_VALUATION_METRIC,
    MetricNotFoundError,
    multiple_and_price,
    pick_metric,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _valuation(ticker: str) -> dict:
    return json.loads(
        (ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text()
    )["mechanical"]["valuation"]


def test_shuffling_the_history_does_not_change_the_metric_shown() -> None:
    """THE CLASS INVARIANT. Reversal is the cheapest shuffle that breaks positional selection, and
    it is exactly what a re-assembly could do without anyone noticing."""
    val = _valuation("GOOGL")
    hist = val["own_history"]["value"]
    assert len(hist) > 1, (
        "GOOGL now carries one valuation history — this check cannot distinguish name-based from "
        "positional selection any more; point it at a name that carries two")

    forward = multiple_and_price(val, metric="P/LTM EPS")
    reversed_val = {**val, "own_history": {**val["own_history"],
                                           "value": list(reversed(hist))}}
    backward = multiple_and_price(reversed_val, metric="P/LTM EPS")
    assert forward == backward, "selection depends on list order"
    assert forward is not None and forward["metric"] == "P/LTM EPS"

    # ...and the same holds for the DEFAULT path, which has no config to lean on.
    assert (multiple_and_price(val) == multiple_and_price(reversed_val)), (
        "the default selection is positional")


def test_the_default_is_a_named_metric_not_an_index() -> None:
    """A default is a decision; an index is an accident. `hist[0]` looked like a default and was
    whichever metric the assembler happened to emit first."""
    val = _valuation("GOOGL")
    got = multiple_and_price(val)
    assert got is not None
    assert got["metric"] == DEFAULT_VALUATION_METRIC
    assert got["metric_is_declared"] is False


def test_a_declared_metric_that_is_absent_refuses_rather_than_substituting() -> None:
    """Showing a different multiple under a heading the name chose is the defect, not the fix."""
    val = _valuation("GOOGL")
    with pytest.raises(MetricNotFoundError) as got:
        multiple_and_price(val, metric="EV/Sales")
    assert "EV/Sales" in str(got.value)
    assert "P/LTM EPS" in str(got.value), "the refusal names what the name DOES carry"


def test_a_near_match_is_not_a_match() -> None:
    """Two valuation metrics whose labels differ by a word are different numbers — the basis
    confusion this repo has already shipped a defect from."""
    hist = [{"metric": "P/NTM EPS", "current": 1.0}, {"metric": "P/LTM EPS", "current": 2.0}]
    assert pick_metric(hist, "P/LTM EPS")["current"] == 2.0
    with pytest.raises(MetricNotFoundError):
        pick_metric(hist, "P/E")


def test_googl_shows_the_metric_its_case_is_underwritten_on() -> None:
    """CORPUS: the committed artifact must carry P/E for GOOGL, not the enterprise multiple.

    Pinned as the DECLARED-ness plus the label, not the level: the number moves daily, the basis
    does not. If the operator re-declares the basis this reddens, which is correct — that is a
    decision worth seeing in a diff.
    """
    snap = json.loads((ROOT / "data" / "monitor" / "2026-09-10.json").read_text())
    rows = [p for p in snap["panels"]
            if p["ticker"] == "GOOGL" and p["key"] == "multiple_and_price"]
    assert rows, "no multiple panel for GOOGL"
    v = rows[0]["value"]
    assert v["metric"] == "P/LTM EPS"
    assert v["metric_is_declared"] is True
    assert "EV/EBITDA (TEV/LTM)" in v["metrics_available"], (
        "the metric NOT chosen is still listed, so a reader can see the panel had a choice")


def test_every_name_shown_a_default_metric_is_marked_as_such() -> None:
    """A reader must be able to tell "the multiple the case rests on" from "the multiple we show
    when nobody said". Invariant over the living artifact, phrasing-independent."""
    snap = json.loads((ROOT / "data" / "monitor" / "2026-09-10.json").read_text())
    seen_default = seen_declared = False
    for p in snap["panels"]:
        if p["key"] != "multiple_and_price" or p["state"] != "ready":
            continue
        v = p["value"]
        assert "metric_is_declared" in v, f"{p['ticker']}: cannot tell declared from default"
        assert v["metric"] in (v.get("metrics_available") or []), (
            f"{p['ticker']}: shows a metric its own history does not list")
        seen_default |= not v["metric_is_declared"]
        seen_declared |= v["metric_is_declared"]
    assert seen_default and seen_declared, (
        "the corpus no longer exercises both paths — this check would prove nothing")


def test_the_sources_tile_indexes_the_panels_on_its_own_page() -> None:
    """THE THIRD INSTANCE of the claim/data class, closed.

    The tile is headed "where each figure on this page comes from". Its first cut read
    `primary_source.filing` and listed the name's 10-Q and three 8-K exhibits — and **not one of
    them sourced anything on the page**. Measured at the time: zero of ten tiles' real sources
    appeared in it. The multiple comes from CIQ Multiples, the cost of borrowing from the CIQ
    capital panel, attribution from Polygon closes, the shelf count from the EDGAR filing INDEX,
    the call from the ledger row.

    Asserted as a RELATIONSHIP, not a list: the set the tile indexes must equal the set of panels
    on the page that cite anything. That holds whatever panels exist next year, which a pin on
    today's six would not.
    """
    snap = json.loads((ROOT / "data" / "monitor" / "2026-09-10.json").read_text())
    by_ticker: dict[str, list[dict]] = {}
    for p in snap["panels"]:
        by_ticker.setdefault(p["ticker"], []).append(p)

    checked = 0
    for ticker, panels in by_ticker.items():
        src = next((p for p in panels if p["key"] == "sources"), None)
        if src is None or src["state"] != "ready":
            continue
        checked += 1
        indexed = {g["key"] for g in src["value"]["by_panel"]}
        citing = {p["key"] for p in panels
                  if p["key"] != "sources" and p["state"] == "ready" and p.get("sources")}
        assert indexed == citing, (
            f"{ticker}: the sources tile indexes {sorted(indexed)} but the page's citing panels "
            f"are {sorted(citing)}")
        # ...and every ref it shows is a ref one of those panels actually carries.
        on_page = {r for p in panels for r in (p.get("sources") or [])}
        for g in src["value"]["by_panel"]:
            for ref in g["refs"]:
                assert ref in on_page, f"{ticker}: sources tile cites {ref!r}, on no panel"
    assert checked, "no ready sources tile in the corpus — this check would prove nothing"


def test_the_multiple_panel_cites_the_metric_it_shows() -> None:
    """A citation that names a different metric from the number above it is the same defect wearing
    provenance. The emitter attached `valuation.ev_ebitda`'s ref — which says TEV/LTM EBITDA — and
    once the metric became selectable that described a number the tile no longer showed."""
    snap = json.loads((ROOT / "data" / "monitor" / "2026-09-10.json").read_text())
    seen = 0
    for p in snap["panels"]:
        if p["key"] != "multiple_and_price" or p["state"] != "ready":
            continue
        seen += 1
        metric = str(p["value"]["metric"])
        refs = " ".join(p.get("sources") or [])
        if "EPS" in metric:
            assert "EBITDA" not in refs, (
                f"{p['ticker']}: shows {metric} and cites an EBITDA source")
        assert refs.strip(), f"{p['ticker']}: shows a multiple and cites nothing"
    assert seen, "no ready multiple panel — this check would prove nothing"
