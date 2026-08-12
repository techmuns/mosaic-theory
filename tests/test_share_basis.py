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

#: The basis every name is expected to be on. A name appearing here has stopped maintaining its
#: undimensioned cover-page tag and takes the CIQ panel's own share column instead.
#:
#: FUBO JOINED KNOWINGLY (2026-08-12) — the wording the collateral-damage pin below asked for. It
#: went dual-class (10-Q of 2026-08-05: 30,204,277 Class A + 78,992,518 Class B), its `dei` tag
#: stopped at 2025-07-31, and the stale single-class total of 342,433,118 was being divided into a
#: Class-A-basis cap. Same shape as Visa, one year instead of sixteen.
BRIDGED = {"V", "FUBO"}

#: Bridged in CODE but not yet in the committed ARTIFACT — the page still carries the pre-fix basis
#: until the operator re-assembles it (FUBO's licensed CIQ workbook is not in this worktree, so the
#: build cannot run here). Listed rather than skipped silently: the artifact pin below states what
#: is owed instead of asserting a basis the file does not yet have.
BRIDGED_PENDING_REASSEMBLY = {"FUBO"}


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


def test_fubos_pre_restructuring_count_is_refused_at_the_new_bound() -> None:
    """THE REGRESSION FOR THIS PR, on FUBO's REAL committed fixture.

    FUBO went dual-class in the year after its last undimensioned tag: the 10-Q of 2026-08-05 states
    30,204,277 Class A and 78,992,518 Class B, and `dei` stops at 2025-07-31 with the single-class
    total of 342,433,118. That total was being divided into a CIQ cap struck on the Class A basis
    ($256.4M), implying $0.75/sh against an $8.33 close — 11.1x wrong, on every per-share and EV
    figure. At the previous 540d bound it was accepted; at 180 it is refused into the bridge.

    Asserted on the real fixture because the defect is a property of what this filer actually
    reports — a synthetic one would only prove the arithmetic in this test."""
    facts = _facts("FUBO")
    pt = latest_instant(extract_points(facts, "shares"))
    assert pt is not None, "FUBO's fixture carries no share points — re-point this pin"
    assert pt.value == pytest.approx(342_433_118), (
        "the pre-restructuring count changed — re-read the filer before touching the bound")
    age = (date(2026, 8, 10) - pt.period_end).days
    assert age > _SHARES_MAX_AGE_DAYS, (
        f"FUBO's newest undimensioned share fact is {age}d old, inside the {_SHARES_MAX_AGE_DAYS}d "
        f"bound — if the filer resumed tagging it, this pin's premise is gone")
    assert 101 < _SHARES_MAX_AGE_DAYS < age, (
        "the bound must sit in the empty band between the healthy fleet's oldest count (101d) and "
        "FUBO's (375d) — outside it, the bound either re-bases healthy names or misses the defect")

    got = _edgar_shares_outstanding(_stub_edgar(facts), "0001484769", as_of=date(2026, 8, 10))
    assert got is None, (
        f"a pre-restructuring share count was accepted as current ({got:,.0f}). FUBO now reports "
        f"per class, so this is a different share basis, not a stale number.")


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
    """THE COLLATERAL-DAMAGE PIN. It said the bound was 540 because the fleet ran 10–375 days old —
    and the 375 was FUBO, the one name whose count was from a different share basis. The bound was
    protecting the defect. At 180 the healthy fleet (10–101d, AORT/WERN at 101) is untouched and
    FUBO is refused into the bridge, which is what this pin asked for in its own words: "widen the
    bound or bridge them knowingly." Measured against the real fixtures, not asserted."""
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
        if p.name in BRIDGED_PENDING_REASSEMBLY:
            # The code refuses this name's EDGAR count as of this PR; the committed page still
            # carries it. Pin the OWED state rather than a false pass — and fail the moment the
            # re-assembly lands, so the name is removed from the pending set instead of lingering.
            assert "EDGAR" in ref, (
                f"{p.name} has been re-assembled onto {ref!r} — drop it from "
                f"BRIDGED_PENDING_REASSEMBLY; the page and the code now agree")
        elif p.name in BRIDGED:
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


# ─── the bound is a CADENCE, not a constant (review finding, #432) ────────────────────────────────

def _stub_edgar_with_forms(facts: dict[str, Any], forms: tuple[str, ...]) -> Any:
    """The real `_shares_max_age` contract: `companyfacts` plus `recent_filings`.

    `recent_filings` returns objects with a `.form`, which is all the cadence read consumes — the
    same shape `EdgarClient.recent_filings` yields, so this stub cannot drift into asserting a
    signature production does not have.
    """
    class _F:
        def __init__(self, form: str) -> None:
            self.form = form

    class _E:
        def companyfacts(self, _cik: str) -> dict[str, Any]:
            return facts

        def recent_filings(self, _cik: Any, **_kw: Any) -> list[Any]:
            return [_F(f) for f in forms]

    return _E()


@pytest.mark.parametrize(
    ("forms", "want", "why"),
    [
        (("20-F",), 540, "a foreign private issuer restates its count once a year"),
        (("40-F",), 540, "the Canadian equivalent, same cadence"),
        (("10-Q", "10-Q"), 180, "a domestic quarterly reporter restates it every quarter"),
        # A filer that carries BOTH is judged by the tighter cadence: it IS filing quarterly, so a
        # two-quarter silence still means the tag stopped being maintained.
        (("20-F", "10-Q"), 180, "quarterly evidence wins over the annual form"),
        ((), 180, "no evidence either way ⇒ the strict bound, never the loose one"),
    ],
)
def test_the_staleness_bound_follows_the_filers_reporting_cadence(
    forms: tuple[str, ...], want: int, why: str) -> None:
    """REVIEW FINDING (#432): 180 days is a 10-Q cadence, and applying it globally refuses CURRENT
    facts from annual reporters.

    NOT HYPOTHETICAL — measured on our own universe: **ONON (On Holding) files 20-F and 6-K and no
    10-Q**, and its dei count is dated 2025-12-31, i.e. **224 days** at a 2026-08-12 reference. A
    flat 180 would refuse a perfectly current fact and strip its per-share and EV figures.
    """
    from vinci.dossier.mechanical import _shares_max_age

    edgar = _stub_edgar_with_forms({}, forms)
    assert _shares_max_age(edgar, "0000000000", date(2026, 8, 12)) == want, why


def test_an_annual_filers_count_survives_where_a_quarterly_filers_does_not() -> None:
    """THE DISCRIMINATING PAIR, on one age. The SAME 224-day-old count is CURRENT for a 20-F filer
    and STALE for a 10-Q filer — which is the whole point, and a bound that cannot tell them apart
    either strips good data or serves a wrong share basis.

    Built from a REAL committed fixture with its cover-page date shifted, so the fact's shape is the
    production one rather than something hand-rolled to suit the assertion.
    """
    facts = _facts("NFLX")
    pt = latest_instant(extract_points(facts, "shares"))
    assert pt is not None
    ref = pt.period_end + timedelta(days=224)

    annual = _edgar_shares_outstanding(_stub_edgar_with_forms(facts, ("20-F",)), "X", as_of=ref)
    quarterly = _edgar_shares_outstanding(_stub_edgar_with_forms(facts, ("10-Q",)), "X", as_of=ref)

    assert annual is not None, (
        "a 224-day-old count from an ANNUAL reporter is current and must survive — this is the "
        "ONON case, and refusing it removes per-share and EV data for no reason")
    assert quarterly is None, (
        "224 days of silence from a QUARTERLY reporter means the tag stopped being maintained — "
        "this is the FUBO case and must still be refused")


def test_a_cadence_lookup_failure_takes_the_strict_bound() -> None:
    """FAIL SAFE IN THE RIGHT DIRECTION. If EDGAR cannot be asked, we do NOT widen the bound:
    refusing a good count yields UNKNOWN, which is honest and recoverable; accepting a stale one
    puts a wrong share basis behind every per-share and EV figure — the ~4x Visa error."""
    from vinci.dossier.mechanical import _SHARES_MAX_AGE_DAYS, _shares_max_age

    class _Broken:
        def recent_filings(self, *_a: Any, **_k: Any) -> list[Any]:
            raise RuntimeError("EDGAR unreachable")

    assert _shares_max_age(_Broken(), "0000000000", date(2026, 8, 12)) == _SHARES_MAX_AGE_DAYS
    assert _shares_max_age(_Broken(), None, date(2026, 8, 12)) == _SHARES_MAX_AGE_DAYS
