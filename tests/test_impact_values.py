"""The value comparator (`vinci.impact.values`): every leaf, list members by identity.

THE NEGATIVE PIN runs on the live committed corpus: every page compared with a copy of itself
moves nothing. THE POSITIVE PINS mutate real pages, and one replays TeamNostra's construction for
RD-D4 (a value whose period moves, a list member that goes UNKNOWN).
"""
from __future__ import annotations

import copy
import json
import pathlib
from typing import Any

import pytest

from vinci.impact.values import ABSENT, show, sourced_pairs, value_changes

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))


def _load(p: pathlib.Path) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(p.read_text())
    return doc


@pytest.mark.parametrize("page", PAGES, ids=[p.parent.name for p in PAGES])
def test_every_committed_page_against_itself_moves_nothing(page: pathlib.Path) -> None:
    doc = _load(page)
    assert value_changes(doc, copy.deepcopy(doc)) == []
    assert all(not p.changes() for p in sourced_pairs(doc, copy.deepcopy(doc)))


def test_a_moved_number_carries_its_citation() -> None:
    doc = _load(ROOT / "data" / "dossiers" / "MCK" / "dossier.json")
    moved = copy.deepcopy(doc)
    moved["mechanical"]["capital_allocation"]["goodwill"]["value"] = 1.0
    [c] = value_changes(doc, moved)
    assert c.path == "mechanical.capital_allocation.goodwill.value"
    assert (c.base, c.head, c.kind) == (11272.0, 1.0, "changed")
    assert c.source_ref == "EDGAR companyfacts Goodwill (as at 2026-09-30)"
    assert c.sourced == "mechanical.capital_allocation.goodwill"


def test_list_members_are_matched_by_identity_not_position() -> None:
    """A row inserted at the top of a keyed list moves ONE row, not every row after it."""
    base = {"rows": [{"label": "Revenue", "v": 1}, {"label": "EBIT", "v": 2}]}
    head = {"rows": [{"label": "Gross", "v": 9}, {"label": "Revenue", "v": 1},
                     {"label": "EBIT", "v": 3}]}
    got = [(c.path, c.base, c.head) for c in value_changes(base, head)]
    assert got == [("rows[label=EBIT].v", 2, 3),
                   ("rows[label=Gross]", ABSENT, {"label": "Gross", "v": 9})]


def test_an_unkeyed_list_pairs_equal_members_first() -> None:
    base = {"xs": [{"a": 1}, {"a": 2}, {"a": 3}]}
    head = {"xs": [{"a": 2}, {"a": 3}, {"a": 4}]}
    assert [(c.path, c.base, c.head) for c in value_changes(base, head)] == [
        ("xs[#0].a", 1, 4)]


def test_a_scalar_list_reports_members_and_order() -> None:
    assert [(c.path, c.base, c.head) for c in value_changes(
        {"caveats": ["a", "b"]}, {"caveats": ["b", "c"]})] == [
        ("caveats[-]", "a", ABSENT), ("caveats[+]", ABSENT, "c")]
    assert [c.path for c in value_changes({"xs": [1, 2]}, {"xs": [2, 1]})] == ["xs[order]"]


def test_a_type_change_is_a_change_and_the_build_clock_is_not() -> None:
    assert [c.path for c in value_changes({"a": 1}, {"a": 1.0})] == ["a"]
    assert value_changes({"assembled_at": "x", "anchor": {"computed_at": "y"}},
                         {"assembled_at": "z", "anchor": {"computed_at": "w"}}) == []


def test_rd_d4_teamnostras_construction_is_seen_by_the_comparator() -> None:
    def s(v: object, ref: str) -> dict[str, object]:
        return {"value": v, "status": "present", "source_ref": ref, "note": None}
    committed = {"mechanical": {
        "valuation": {"ev_ebitda": s(12.3, "CIQ Multiples TEV/LTM EBITDA [Jun-30-2026]")},
        "segments": [{"name": "A", "revenue": s(500.0, "CIQ Segments FY2025")}]}}
    fresh = {"mechanical": {
        "valuation": {"ev_ebitda": s(19.8, "CIQ Multiples TEV/LTM EBITDA [Dec-31-2024]")},
        "segments": [{"name": "A", "revenue": {"value": None, "status": "unknown",
                                                "source_ref": None, "note": "row missing"}}]}}
    paths = {c.path for c in value_changes(committed, fresh)}
    assert {"mechanical.valuation.ev_ebitda.value", "mechanical.valuation.ev_ebitda.source_ref",
            "mechanical.segments[name=A].revenue.status"} <= paths
    by = {p.path: p for p in sourced_pairs(committed, fresh)}
    seg = by["mechanical.segments[name=A].revenue"]
    assert (seg.in_list, seg.member_moved, seg.status("base"), seg.status("head")) == (
        True, False, "present", "unknown")


def test_a_member_that_leaves_its_list_is_told_apart_from_a_field_that_goes_missing() -> None:
    sv = {"value": 1, "status": "present", "source_ref": "r", "note": None}
    base = {"fs": [{"accession": "A", "d": sv}, {"accession": "B", "d": sv}]}
    left = {"fs": [{"accession": "B", "d": sv}]}
    lost = {"fs": [{"accession": "A"}, {"accession": "B", "d": sv}]}
    [a] = [p for p in sourced_pairs(base, left) if p.head is ABSENT]
    assert (a.path, a.member_moved) == ("fs[accession=A].d", True)
    [b] = [p for p in sourced_pairs(base, lost) if p.head is ABSENT]
    assert (b.path, b.member_moved) == ("fs[accession=A].d", False)


def test_a_long_value_says_how_much_it_leaves_out() -> None:
    assert show("x" * 200, 10) == "'xxxxxxxxxx'…(+190 chars)"
    assert show(ABSENT) == "ABSENT"


def test_the_fetch_time_an_assembly_log_prints_is_the_builds_clock() -> None:
    """Found on the first corpus run (#955, MCK): two builds of one page on one input differed
    only by "(+1.5s fetch)" → "(+1.7s fetch)" in the assembly-log flag."""
    a = {"qa_flags": ["primary-source: 3 EX-99.1 release(s) + 1 10-Q parsed (+1.5s fetch)"]}
    b = {"qa_flags": ["primary-source: 3 EX-99.1 release(s) + 1 10-Q parsed (+1.7s fetch)"]}
    assert value_changes(a, b) == []
    c = {"qa_flags": ["primary-source: 2 EX-99.1 release(s) + 1 10-Q parsed (+1.7s fetch)"]}
    assert [x.path for x in value_changes(a, c)] == ["qa_flags[-]", "qa_flags[+]"]


def test_two_filings_of_one_accession_are_told_apart_by_their_gap_dates() -> None:
    """SMPL's two drawdown filings share one accession (review of this PR, finding 2): paired by
    position, a new filing at the front would be compared with an old one and its unknown
    drivers read as a loss. Keyed by gap date, the old filing is compared with itself."""
    sv = {"value": "x", "status": "present", "source_ref": "8-K", "note": None}
    unk = {"value": None, "status": "unknown", "source_ref": None, "note": "not read"}
    old = [{"gap_date": "2026-04-09", "accession": "A", "drivers": sv},
           {"gap_date": "2026-04-10", "accession": "A", "drivers": sv}]
    new = [{"gap_date": "2026-05-01", "accession": "B", "drivers": unk}, *old]
    pairs = {p.path: p for p in sourced_pairs({"f": old}, {"f": new})}
    assert pairs["f[gap_date=2026-04-09].drivers"].status("head") == "present"
    assert pairs["f[gap_date=2026-05-01].drivers"].base is ABSENT


def test_a_reordered_list_of_records_is_a_change() -> None:
    """A list of records is matched by identity, so a pure reordering moved no member and read as
    no change. MCK's real peer grid (keyed by ticker), reversed: one ``[order]`` change, the
    shared members in each side's order. A member joining is not a reorder (negative pin)."""
    base = _load(ROOT / "data" / "dossiers" / "MCK" / "dossier.json")
    grid = base["mechanical"]["peer_comps"]["peer_grid"]["value"]
    assert len(grid) >= 3
    head = copy.deepcopy(base)
    head["mechanical"]["peer_comps"]["peer_grid"]["value"] = list(reversed(grid))
    [c] = value_changes(base, head)
    assert c.path == "mechanical.peer_comps.peer_grid.value[order]"
    tickers = [[m["ticker"]] for m in grid]
    assert (c.base, c.head) == (tickers, list(reversed(tickers)))
    joined = copy.deepcopy(base)
    joined["mechanical"]["peer_comps"]["peer_grid"]["value"] = [
        *grid, {**grid[0], "ticker": "ZZZZ"}]
    assert [x.path for x in value_changes(base, joined)] == [
        "mechanical.peer_comps.peer_grid.value[ticker=ZZZZ]"]
