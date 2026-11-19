"""W80 — a $0 refresh may not move a basis-block figure the kept synthesis quotes (2026-11-19).

THE GAP (found by W65's GOOGL refresh check, 2026-11-19). `refresh_dossier` refuses a refresh that
moves a figure the stored prose cites, but its guards read the financial tables, revision
counts, returns and release actuals — never the two basis blocks `valuation_bases_transform`
rewrites. GOOGL's kept synthesis says CIQ's 22.9x "divides TEV $3,316,548M by an implied
$144,827M denominator that reproduces NEITHER …"; W65's rebuild nulls that quotient (its TEV and
multiple are 30 days apart), and a scratch-copy refresh PASSED. The page would have carried two
explanations of one multiple. Coordinator B held GOOGL for a paid rebuild instead; this closes the
gap.

THE CORPUS (main 2ecf6da0, 26 committed pages). 21 pages' prose cites a basis figure
dollar-anchored (mostly reported LTM EBITDA; 13 cite the ex-lease block too). A pure basis rebuild
moves a figure on 2: GOOGL (its cited $144,827M → refused) and AMZN ($184,739M, which its prose
does not cite → passes).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from tests.frozen_support import CUT, frozen_doc
from vinci.dossier import refresh as rf
from vinci.dossier import schemas as ds
from vinci.dossier.ev_ebitda_basis import headline_basis

ROOT = Path(__file__).resolve().parents[1]
_PAGES = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))


def _rebuild_basis(mech: dict[str, Any]) -> dict[str, Any]:
    """The headline-basis block rebuilt by the head code, with nothing read but the page: the block
    `valuation_bases_transform` writes on GOOGL (W65's input proof: identical with no CIQ store and
    no EDGAR facts)."""
    out: dict[str, Any] = json.loads(json.dumps(mech))
    got = headline_basis(ds.MechanicalLayer.model_validate(out))
    if got is not None:
        out["valuation"]["ev_ebitda_basis"] = json.loads(got.model_dump_json())
    return out


def _page_copy(tmp_path: Path, ticker: str) -> Path:
    """``ticker``'s page as frozen at the cut, in a scratch repository layout with the roster
    `refresh_dossier` reads."""
    dest = tmp_path / "data" / "dossiers" / ticker
    shutil.copytree(CUT / ticker, dest)
    shutil.copy(ROOT / "data" / "coverage_roster.jsonl",
                tmp_path / "data" / "coverage_roster.jsonl")
    return dest / "dossier.json"


# --- the positive pins: a moved figure the prose quotes refuses ----------------------------------

def test_googls_basis_refresh_is_refused_on_the_quotient_its_prose_quotes(tmp_path: Path) -> None:
    """THE RED, end to end on GOOGL's page as frozen at the cut: the basis rebuild nulls the
    $144,827M quotient its synthesis quotes, so the refresh refuses, names the figure, and writes
    nothing. On main the same refresh passed."""
    page = _page_copy(tmp_path, "GOOGL")
    before = page.read_bytes()
    assert "144,827" in json.dumps(json.loads(before)["synthesis"])
    with pytest.raises(rf.RefreshRefusedError) as err:
        rf.refresh_dossier(page, transform=_rebuild_basis)
    assert "ev_ebitda_basis.implied_denominator = 144,827.4 → absent" in str(err.value)
    assert page.read_bytes() == before


def test_only_the_moved_cited_figure_is_named() -> None:
    """GOOGL's prose also quotes the comps TEV, reported LTM EBITDA and EBITDA plus rent; none of
    them moves, so only the quotient is named."""
    doc = frozen_doc("GOOGL")
    before = doc["mechanical"]
    hits = rf.moved_cited_basis_figures(before, _rebuild_basis(before), doc)
    assert hits == ["ev_ebitda_basis.implied_denominator = 144,827.4 → absent"], hits


def test_the_ex_lease_block_and_the_printed_sum_are_watched_too() -> None:
    """One field moved on a real page at a time. TJX's prose quotes its ex-lease EV; GOOGL's quotes
    EBITDA plus rent ($190,600M), a sum the basis line prints, so a moved rent refuses on it."""
    tjx = frozen_doc("TJX")
    at = tjx["mechanical"]["valuation"]["ev_ebitda_ex_lease_at_price"]
    assert rf._total_cited(rf._prose(tjx), at["ev"])
    moved = json.loads(json.dumps(tjx["mechanical"]))
    moved["valuation"]["ev_ebitda_ex_lease_at_price"]["ev"] = at["ev"] * 1.1
    hits = rf.moved_cited_basis_figures(tjx["mechanical"], moved, tjx)
    assert [h.split(" = ")[0] for h in hits] == ["ev_ebitda_ex_lease_at_price.ev"], hits

    googl = frozen_doc("GOOGL")
    moved = json.loads(json.dumps(googl["mechanical"]))
    moved["valuation"]["ev_ebitda_basis"]["rent"] = 6000.0
    hits = rf.moved_cited_basis_figures(googl["mechanical"], moved, googl)
    assert [h.split(" = ")[0] for h in hits] == [
        "ev_ebitda_basis.reported_ltm_ebitda + rent"], hits


# --- the negative pins: a basis that does not move, or a move nobody quotes ----------------------

def test_a_basis_refresh_that_moves_no_figure_passes_and_writes(tmp_path: Path) -> None:
    """NEGATIVE, end to end on IT at the cut: one date, so the rebuild moves no figure (it adds the
    dates it measured on). IT's prose quotes its quotient, reported EBITDA and EBITDA plus rent;
    the refresh passes and the page carries the new fields."""
    page = _page_copy(tmp_path, "IT")
    prose = rf._prose(json.loads(page.read_text()))
    assert rf._total_cited(prose, 1473.936)                  # its quotient, quoted
    assert rf.refresh_dossier(page, transform=_rebuild_basis)
    eb = json.loads(page.read_text())["mechanical"]["valuation"]["ev_ebitda_basis"]
    assert (eb["reading"], eb["implied_denominator"], eb["days_apart"]) == (
        "indistinguishable", 1473.936, 0)


def test_a_moved_figure_the_prose_does_not_quote_passes() -> None:
    """NEGATIVE: AMZN's quotient ($184,739M) moves to absent, but its prose never quotes it."""
    doc = frozen_doc("AMZN")
    before = doc["mechanical"]
    after = _rebuild_basis(before)
    assert after["valuation"]["ev_ebitda_basis"]["implied_denominator"] is None
    assert rf.moved_cited_basis_figures(before, after, doc) == []


def test_a_value_the_block_still_carries_is_not_a_move() -> None:
    """A figure that leaves its key but stays in the block (a relabel) is not a move, as for the
    release actuals: GOOGL's reported LTM EBITDA written under `rent` too."""
    doc = frozen_doc("GOOGL")
    before = doc["mechanical"]
    after = json.loads(json.dumps(before))
    eb = after["valuation"]["ev_ebitda_basis"]
    eb["rent"], eb["reported_ltm_ebitda"] = eb["reported_ltm_ebitda"], None
    hits = rf.moved_cited_basis_figures(before, after, doc)
    assert not any(h.startswith("ev_ebitda_basis.reported_ltm_ebitda =") for h in hits), hits


def test_the_same_number_in_the_other_block_does_not_mask_a_move() -> None:
    """Review round 0: "still carried" is per BLOCK. TJX's reported LTM EBITDA and its ex-lease LTM
    EBITDA are both $8,903M, and its prose quotes the reported one; moving only that one must
    refuse, though the number still prints as the ex-lease denominator, with another meaning."""
    doc = frozen_doc("TJX")
    v = doc["mechanical"]["valuation"]
    old = v["ev_ebitda_basis"]["reported_ltm_ebitda"]
    assert v["ev_ebitda_ex_lease_at_price"]["ltm_ebitda"] == old
    assert rf._total_cited(rf._prose(doc), old)
    moved = json.loads(json.dumps(doc["mechanical"]))
    moved["valuation"]["ev_ebitda_basis"]["reported_ltm_ebitda"] = old + 197.0
    hits = rf.moved_cited_basis_figures(doc["mechanical"], moved, doc)
    assert "ev_ebitda_basis.reported_ltm_ebitda" in [h.split(" = ")[0] for h in hits], hits


# --- the committed pages -------------------------------------------------------------------------

def test_no_committed_page_refuses_where_no_basis_figure_moves_e2e() -> None:
    """A ROSTER WALK, phrasing-free: on every committed page, a basis rebuild refuses only where a
    basis figure moves, and every refusal names a figure that moved."""
    seen = 0
    for p in _PAGES:
        doc = json.loads(p.read_text())
        if doc.get("synthesis") is None:
            continue
        before = doc["mechanical"]
        after = _rebuild_basis(before)
        old, new = rf._basis_figures(before), rf._basis_figures(after)
        moved = {k for k, v in old.items() if new.get(k) != v}
        hits = rf.moved_cited_basis_figures(before, after, doc)
        seen += 1
        assert {h.split(" = ")[0] for h in hits} <= moved, (p.parent.name, hits)
    assert seen >= 20, seen
