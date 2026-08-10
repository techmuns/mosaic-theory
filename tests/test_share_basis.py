"""The share basis — refusing a count from a different era, and what may stand in for it.

VISA IS THE CASE THIS EXISTS FOR. Visa stopped tagging the undimensioned
``dei:EntityCommonStockSharesOutstanding`` after 2010 (it reports per share CLASS, which the
company-facts API view does not surface), so the newest fact available is 469,280,842 shares dated
2010-01-27 — and Visa split 4-for-1 in March 2015. Taken at face value it makes the cap imply
$1,417.93/sh against a $362.50 close: every per-share and EV figure on the page wrong by ~4x.

The freshness guard caught it and refused the build, which is the system working. These pins hold
the FIX in place: the count is refused for being from another era, the CIQ panel's own share
column stands in (same row as the cap, so the reconciliation is coherent by construction), and no
other name's basis moves.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date, timedelta
from typing import Any

import pytest

from vinci.dossier.mechanical import _SHARES_MAX_AGE_DAYS, _edgar_shares_outstanding
from vinci.edgar.concepts import extract_points, latest_instant

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "companyfacts"
DOSSIERS = ROOT / "data" / "dossiers"

#: The basis every name is expected to be on. V is the ONLY bridged name; a second one appearing
#: here means another filer stopped maintaining its cover-page tag and wants the same look.
BRIDGED = {"V"}


def _facts(ticker: str) -> dict[str, Any]:
    p = FIXTURES / f"{ticker}.json"
    if not p.is_file():
        pytest.skip(f"no committed companyfacts fixture for {ticker}")
    return json.loads(p.read_text())  # type: ignore[no-any-return]


def _stub_edgar(facts: dict[str, Any]) -> Any:
    class _E:
        def companyfacts(self, _cik: str) -> dict[str, Any]:
            return facts
    return _E()


def test_visas_cover_page_count_is_from_another_era_and_is_refused() -> None:
    """THE REGRESSION. Asserted on Visa's REAL committed fixture, not a synthetic one — the whole
    defect is a property of what this filer actually reports, and a hand-made fixture would only
    prove the arithmetic I wrote."""
    facts = _facts("V")
    pt = latest_instant(extract_points(facts, "shares"))
    assert pt is not None, "V's fixture carries no share points — re-point this pin"
    age = (date(2026, 8, 10) - pt.period_end).days
    assert age > _SHARES_MAX_AGE_DAYS, (
        f"V's newest undimensioned share fact is only {age}d old — if Visa resumed tagging it, "
        f"this pin's premise is gone and the bridge below should be reconsidered")
    assert pt.value == pytest.approx(469_280_842), (
        "the pre-split 2010 count changed — re-read the filer before touching the bound")

    got = _edgar_shares_outstanding(_stub_edgar(facts), "0001403161", as_of=date(2026, 8, 10))
    assert got is None, (
        f"a share count from {pt.period_end} was accepted as current ({got:,.0f}). Visa split "
        f"4-for-1 in 2015, so this is a different share basis, not a stale number — every "
        f"per-share and EV figure built on it is wrong by ~4x.")


def test_a_current_count_is_still_accepted() -> None:
    """The bound must refuse an ERA, not a few quarters. Without this the fix could pass by
    refusing everything, and the fleet pin below would then be the only thing noticing."""
    facts = _facts("UBER")
    pt = latest_instant(extract_points(facts, "shares"))
    assert pt is not None
    got = _edgar_shares_outstanding(_stub_edgar(facts), "0001543151", as_of=date(2026, 8, 10))
    assert got == pytest.approx(pt.value), "a current cover-page count was refused"
    # …and it is refused once the as-of walks past the bound, so the gate is the AGE, not the name
    far = pt.period_end + timedelta(days=_SHARES_MAX_AGE_DAYS + 1)
    assert _edgar_shares_outstanding(_stub_edgar(facts), "0001543151", as_of=far) is None


def test_the_bound_moves_no_committed_name_off_edgar() -> None:
    """THE COLLATERAL-DAMAGE PIN, and the reason the bound is 540 and not a rounder number: the
    twelve pre-existing names' counts run 10–375 days old, so any bound below ~375 would silently
    re-base names that were never in question. Measured against the real fixtures, not asserted."""
    ref = date(2026, 8, 10)
    refused = []
    for f in sorted(FIXTURES.glob("*.json")):
        if f.stem in BRIDGED:
            continue
        pt = latest_instant(extract_points(json.loads(f.read_text()), "shares"))
        if pt is not None and (ref - pt.period_end).days > _SHARES_MAX_AGE_DAYS:
            refused.append((f.stem, (ref - pt.period_end).days))
    assert not refused, (
        f"the staleness bound newly refuses {refused} — those names' share counts, and every "
        f"per-share figure on their pages, would move. Widen the bound or bridge them knowingly.")


def test_every_committed_dossier_states_which_share_basis_it_used() -> None:
    """A bridged basis is a DIFFERENT VENDOR's number and must never be silent. Read back from the
    committed artifacts, so this pins what a human actually receives."""
    if not DOSSIERS.is_dir():
        pytest.skip("no committed dossiers in this worktree")
    for p in sorted(DOSSIERS.iterdir()):
        doc = p / "dossier.json"
        if not doc.is_file():
            continue
        so = json.loads(doc.read_text())["mechanical"]["stock_info"]["shares_out"]
        if so.get("value") is None:
            continue
        ref = so.get("source_ref") or ""
        assert ref.strip(), f"{p.name}: a share count with no stated source"
        if p.name in BRIDGED:
            assert "CIQ" in ref, f"{p.name} is expected on the CIQ bridge; source says {ref!r}"
        else:
            assert "EDGAR" in ref, (
                f"{p.name} moved off the EDGAR cover-page count to {ref!r} — if that is intended, "
                f"add it to BRIDGED with the reason; a silent vendor swap changes every per-share "
                f"figure on the page")


def test_every_consumer_of_the_raw_share_concept_bounds_it() -> None:
    """REVIEW FINDING on this PR. The first cut guarded `_edgar_shares_outstanding` and left two
    other readers of the same concept extracting points directly — one of them computing
    `ev = price * shares + net_debt`, which is precisely the multiplication that turns a pre-split
    count into a 4x-wrong enterprise value, on a page whose HEADLINE share basis had just been
    correctly refused.

    Guarding one consumer of a bad number and leaving its neighbour is the half-landed fix this
    repo keeps re-meeting. So the pin is on the CLASS: every site that reaches for the raw concept
    must bound it by age, and a new unbounded reader reddens here rather than in an EV.

    Read from the SOURCE, so a future reader added anywhere in the module is in scope the moment
    it lands — a roster of known call sites would go stale the day someone adds one."""
    import ast
    import re

    src = (ROOT / "vinci" / "dossier" / "mechanical.py").read_text()
    # SCOPED BY FUNCTION, VIA AST — not by a line window. Two earlier cuts of this pin failed for
    # reasons worth keeping: `[^)]*` could not cross the nested paren in
    # `extract_points(edgar.companyfacts(cik), "shares")` and so matched only the guarded helper;
    # then a ±N-line window put the bound out of range the moment a comment grew above it. A
    # function is the unit the rule is actually about, and it has no such edges.
    reader = re.compile(r'extract_points\(.*?"shares"\)', re.S)
    bounds = ("_SHARES_MAX_AGE_DAYS", "_SHARES_WINDOW_DAYS")

    funcs = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)]
    readers = [f for f in funcs if reader.search(ast.get_source_segment(src, f) or "")]
    assert len(readers) >= 3, (
        f"only {len(readers)} functions read the raw share concept "
        f"({[f.name for f in readers]}) — the module has had three since this pin was written, so "
        f"the pattern has stopped matching rather than the readers having gone away")

    unbounded = [
        f.name for f in readers
        if f.name != "_edgar_shares_outstanding"          # the guarded helper IS the bound
        and not any(b in (ast.get_source_segment(src, f) or "") for b in bounds)
    ]
    assert not unbounded, (
        f"{unbounded} read the raw share concept without an age bound. A pre-split count from a "
        f"multi-class filer reaches whatever they compute — the Visa case is a 4x error in every "
        f"per-share and EV figure downstream.")


def test_the_bridged_name_reconciles_cap_shares_and_price_exactly() -> None:
    """WHY THE BRIDGE IS THE CIQ PANEL AND NOT SOME OTHER CURRENT COUNT. Its share column sits in
    the SAME ROW as the cap, so cap ÷ shares reproduces that row's own close — the coherence
    `reconcile_cap` tests holds by construction rather than by luck. Mixing an EDGAR count with a
    CIQ cap is precisely what produced the 3.91x that started this."""
    doc = DOSSIERS / "V" / "dossier.json"
    if not doc.is_file():
        pytest.skip("no committed V dossier")
    si = json.loads(doc.read_text())["mechanical"]["stock_info"]
    cap, shares, spot = si["market_cap"]["value"], si["shares_out"]["value"], si["price"]["value"]
    implied = cap * 1e6 / shares
    assert implied == pytest.approx(spot, rel=0.01), (
        f"cap/shares implies ${implied:,.2f}/sh against a ${spot:,.2f} close — the bridged basis "
        f"does not agree with the cap it sits beside")
