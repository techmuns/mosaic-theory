"""THE COVERAGE MAP CREDITS EACH FAMILY WITH ITS OWN UNITS (2026-11-09, audit RBC-D9).

`core.scorecard` copied a check's fleet totals into every family listing it. `currency_stated_usd`
judges one unit per CIQ money panel, and 14 families list it, so the committed snapshot of
2026-11-05 printed "currency_stated_usd on 25/27 pages, 449 of 449 confirmed" under Segments — a
family whose panel a page carries once. And a family's class came from the checks it DECLARES, so
two pages with no money block at all still showed nine families "independent" on zero units.

Now a check states how it credits the families listing it (`Check.per_family` / `Check.joint`), the
currency check credits each panel's unit to the families citing that panel's sheet
(`ciq.PANEL_CITES`), a row says whose counts it shows (`credited`), and a family's class and guards
come from the checks that judged at least one of its units on the run.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import ciq_sheets
from vinci.quality import core
from vinci.quality.sources import ciq

ROOT = Path(__file__).resolve().parents[1]
PAGES = {p.parent.name: json.loads(p.read_text())
         for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))}


def _card(pages: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return core.scorecard(ciq.SOURCE, ciq.corpus(pages, "0" * 64), measured_on="2026-11-09",
                          git_head="abc1234", inputs_match_head=True)


def _family(card: dict[str, Any], fid: str) -> dict[str, Any]:
    return next(e for e in card["coverage"] if e["family"] == fid)


def _row(entry: dict[str, Any], cid: str) -> dict[str, Any]:
    return next(r for r in entry["checks"] if r["id"] == cid)


def _panels(page: dict[str, Any]) -> list[str]:
    return [p["panel"] for p in ((page["mechanical"].get("ciq_currency") or {}).get("panels")
                                 or [])]


def test_segments_is_credited_with_its_own_panel_not_the_whole_check() -> None:
    """(+) ON THE COMMITTED PAGES: Segments' currency row counts the Segments panels the pages
    carry — one a page — never the check's units over every panel."""
    card = _card(PAGES)
    row = _row(_family(card, "financials.segments"), "currency_stated_usd")
    fleet = next(c for c in card["checks"] if c["id"] == "currency_stated_usd")["fleet"]
    want = sum(1 for p in PAGES.values() for x in _panels(p) if x.endswith("→Segments"))
    assert want and row["units"] == want and row["credited"] == "family"
    assert row["items_run"] == sum(1 for p in PAGES.values()
                                   if any(x.endswith("→Segments") for x in _panels(p)))
    assert fleet["units"] > row["units"]


def test_a_page_whose_only_currency_panel_is_the_income_statement() -> None:
    """THE AUDIT'S REPRODUCTION (BC-D9, `family_credit.py`), on a committed page's REAL record cut
    to its Income Statement panel: Segments is credited nothing, so its class falls back — it is
    no longer "internal" on a unit it never had — and the Income Statement families keep theirs."""
    t, page = next((t, p) for t, p in PAGES.items()
                   if "Financials (annual)→Income Statement" in _panels(p))
    page = json.loads(json.dumps(page))
    cur = page["mechanical"]["ciq_currency"]
    cur["panels"] = [p for p in cur["panels"]
                     if p["panel"] == "Financials (annual)→Income Statement"]
    card = _card({t: page})
    seg = _family(card, "financials.segments")
    assert _row(seg, "currency_stated_usd") == {
        "id": "currency_stated_usd", "independence": core.INTERNAL, "items_run": 0, "units": 0,
        "confirmed": 0, "credited": "family"}
    assert seg["classification"] == core.UNVERIFIED
    assert seg["failure_guard"]["wrong_unit"] == "none"
    for fid in ("financials.quarterly_ebitda", "financials.annual_income_statement",
                "financials.rent"):
        assert _row(_family(card, fid), "currency_stated_usd")["units"] == 1, fid


def test_two_pages_with_no_block_leave_no_family_classed_on_zero_units() -> None:
    """THE AUDIT'S REPRODUCTION (BC-D9, `coverage_claim.py`): two pages carrying none of the blocks
    the checks read. Every check judges zero units, so no family is "independent" or "internal" —
    each takes its fallback, the class it has when nothing compared it."""
    blank = {"ticker": "AAA", "mechanical": {}}
    card = _card({"AAA": blank, "BBB": {**blank, "ticker": "BBB"}})
    assert sum(c["fleet"]["units"] for c in card["checks"]) == 0
    classes = {e["family"]: e["classification"] for e in card["coverage"]}
    assert core.INDEPENDENT not in classes.values() and core.INTERNAL not in classes.values()
    fallback = {f.id: f.fallback for f in ciq.SOURCE.families}
    assert classes == fallback


def test_a_joint_check_credits_every_family_listing_it_in_full() -> None:
    """The EV bridge against CIQ's TEV is ONE comparison of both families' figures: each is
    credited the whole of it, and the row says so."""
    card = _card(PAGES)
    fleet = next(c for c in card["checks"] if c["id"] == "ev_bridge_vs_ciq_tev")["fleet"]
    for fid in ("financials.balance_sheet_claims", "comps.tev_net_debt"):
        row = _row(_family(card, fid), "ev_bridge_vs_ciq_tev")
        assert row["credited"] == "joint" and row["units"] == fleet["units"], fid


def test_the_panel_table_is_closed_against_the_reader() -> None:
    """Every money panel `ciq_sheets` reads is named in `PANEL_CITES`, and nothing else; each maps
    to a sheet some family listing the currency check cites."""
    assert set(ciq.PANEL_CITES) == {label for label, _how, _read in ciq_sheets._MONEY_PANELS}
    for panel in ciq.PANEL_CITES:
        assert ciq._panel_families(panel), panel


def test_a_panel_the_table_does_not_know_raises_never_drops_its_unit() -> None:
    """(-) NEGATIVE PIN: a panel label outside the table is refused when scored."""
    t, page = next(iter(PAGES.items()))
    page = json.loads(json.dumps(page))
    page["mechanical"]["ciq_currency"] = {"panels": [
        {"panel": "Financials (annual)→Some New Sheet", "stated": ["USD"], "where": "x",
         "check": "agree"}], "check": "agree"}
    with pytest.raises(ValueError, match="not in PANEL_CITES"):
        _card({t: page})


def _source(check: core.Check, families: tuple[core.Family, ...]) -> core.Source:
    return core.Source(id="t", title="t", reads_note="", load=lambda _r: None,  # type: ignore[arg-type, return-value]
                       checks=(check,), families=families)


def _check(run: Any, **kw: Any) -> core.Check:
    return core.Check("c", "t", "s", "s2", core.INTERNAL, "unit", "tol", "pop", None, None,
                      ("wrong_unit",), run, **kw)


def test_a_per_family_check_must_say_whose_its_units_are() -> None:
    """(-) A per-family check that credits no family, or one that does not list it, raises — a unit
    is never silently dropped or handed to a family that never read it."""
    fams = (core.Family("a", "o", (), "x", checks=("c",)), core.Family("b", "o", (), "y",
                                                                         checks=("c",)))
    src = _source(_check(lambda _p: core.one(core.CONFIRMED), per_family=True), fams)
    with pytest.raises(ValueError, match="no by_family"):
        core.scorecard(src, core.Corpus({"X": {}}, "r", "page", "0"), measured_on="d",
                       git_head=None, inputs_match_head=None)
    stray = _source(_check(lambda _p: core.ItemResult(
        counts={core.CONFIRMED: 1}, by_family={"z": {core.CONFIRMED: 1}}), per_family=True), fams)
    with pytest.raises(ValueError, match="which do not list it"):
        core.scorecard(stray, core.Corpus({"X": {}}, "r", "page", "0"), measured_on="d",
                       git_head=None, inputs_match_head=None)
    # the credits reconcile to the counts: a unit credited to no family, or a family handed more
    # units than the name has, raises
    dropped = _source(_check(lambda _p: core.ItemResult(
        counts={core.CONFIRMED: 2}, by_family={"a": {core.CONFIRMED: 1}}), per_family=True), fams)
    invented = _source(_check(lambda _p: core.ItemResult(
        counts={core.CONFIRMED: 1}, by_family={"a": {core.CONFIRMED: 2}}), per_family=True), fams)
    for bad in (dropped, invented):
        with pytest.raises(ValueError, match="credited the families"):
            core.scorecard(bad, core.Corpus({"X": {}}, "r", "page", "0"), measured_on="d",
                           git_head=None, inputs_match_head=None)
    # a shared unit credited to both families reconciles
    shared = _source(_check(lambda _p: core.ItemResult(
        counts={core.CONFIRMED: 1}, by_family={"a": {core.CONFIRMED: 1}, "b": {core.CONFIRMED: 1}}),
        per_family=True), fams)
    core.scorecard(shared, core.Corpus({"X": {}}, "r", "page", "0"), measured_on="d",
                   git_head=None, inputs_match_head=None)
    # by_family from a check that does not credit per family would be ignored: refused
    ignored = _source(_check(lambda _p: core.ItemResult(
        counts={core.CONFIRMED: 1}, by_family={"a": {core.CONFIRMED: 1}})), fams)
    with pytest.raises(ValueError, match="does not credit per family"):
        core.scorecard(ignored, core.Corpus({"X": {}}, "r", "page", "0"), measured_on="d",
                       git_head=None, inputs_match_head=None)
    with pytest.raises(ValueError, match="per_family and joint"):
        core.validate(_source(_check(lambda _p: core.one(core.CONFIRMED), per_family=True,
                                     joint=True), fams))


def test_a_shared_check_that_declares_neither_says_its_counts_are_the_whole_checks() -> None:
    """A check two families list, crediting neither way: each row carries the whole check's counts
    AND says so — the boundary is stated, never implied."""
    fams = (core.Family("a", "o", (), "x", checks=("c",)), core.Family("b", "o", (), "y",
                                                                         checks=("c",)))
    card = core.scorecard(_source(_check(lambda _p: core.one(core.CONFIRMED)), fams),
                          core.Corpus({"X": {}, "Y": {}}, "r", "page", "0"), measured_on="d",
                          git_head=None, inputs_match_head=None)
    for e in card["coverage"]:
        assert e["checks"][0]["credited"] == "whole_check" and e["checks"][0]["units"] == 2
    assert "(the whole check's, shared with the other families listing it)" in core.render(card)


def test_the_newest_committed_ciq_snapshot_credits_each_family_its_own_units() -> None:
    """END TO END on the committed artifact (the snapshot of 2026-11-05 printed 449 of 449 under
    all fourteen): in the newest committed CIQ snapshot, every family's currency row is its own,
    and equals the sum of its by-name credits."""
    snaps = sorted((ROOT / "data" / "snapshots" / "data_quality" / "ciq").glob("*.json"))
    assert snaps, "no committed CIQ quality snapshot"
    card = json.loads(snaps[-1].read_text())
    check = next(c for c in card["checks"] if c["id"] == "currency_stated_usd")
    listing = [e for e in card["coverage"]
               if any(r["id"] == "currency_stated_usd" for r in e["checks"])]
    assert len(listing) == 14
    for e in listing:
        row = _row(e, "currency_stated_usd")
        got = sum(sum(r["by_family"].get(e["family"], {}).values())
                  for r in check["by_name"].values() if "by_family" in r)
        assert row.get("credited") == "family" and row["units"] == got, e["family"]
    seg = _row(_family(card, "financials.segments"), "currency_stated_usd")
    assert seg["units"] < check["fleet"]["units"]


def test_a_family_whose_every_unit_is_unchecked_takes_no_class_from_that_check() -> None:
    """(review round 0) An UNCHECKED unit had no second figure, so it stored no verdict: a family
    whose only check found every unit unchecked is not classed by it — on a committed page's real
    record, its currency panels all set to `not_run`."""
    t, page = next((t, p) for t, p in PAGES.items() if _panels(p))
    page = json.loads(json.dumps(page))
    for pnl in page["mechanical"]["ciq_currency"]["panels"]:
        pnl["check"] = "not_run"
    seg = _family(_card({t: page}), "financials.segments")
    assert _row(seg, "currency_stated_usd")["units"] >= 1
    assert seg["classification"] == core.UNVERIFIED
    assert seg["failure_guard"]["wrong_unit"] == "none"


def test_the_printed_map_says_a_joint_row_is_one_comparison() -> None:
    text = core.render(_card(PAGES))
    assert "(one comparison per unit, credited in full to every family listing it)" in text

