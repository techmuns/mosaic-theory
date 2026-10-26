"""THE CROSS-CHECK OUTCOMES (`schemas.CrossCheck`, 2026-10-23) — five checks whose verdict a reader
could not tell from "it passed" or read without parsing prose, now stored beside the line or flag
that prints it: `self_funding_check`, `wall_coherence_check` (+ `wall_coherence_near_boundary`),
`guide_verification_check`, `vintage_check`, `net_debt_check`.

* The PRODUCER: each outcome comes out of the same decision as its line or flag — every branch
  pinned, and the two bools that read True when nothing ran (the negative pins).
* The WRITE: absent until built, so a committed page round-trips byte for byte; present, beside its
  sibling.
* The BACK-FILL (`refresh.cross_check_transform`): run over every committed page with EDGAR answered
  from the committed fixtures and the network refused. It writes an outcome only where the stored
  line reproduces, names every one it does not, and never contradicts an outcome a page carries.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.sec_offline_support import COMPANYFACTS, no_network
from vinci.dossier import mechanical as dm
from vinci.dossier.ciq_sheets import _fig, revenue_guide_from_rows
from vinci.dossier.refresh import RefreshRefusedError, cross_check_transform
from vinci.dossier.schemas import (
    CHECK_AGREE,
    CHECK_DIFFER,
    CHECK_NOT_RUN,
    Dossier,
    GuidanceRow,
    ImpliedValuation,
    ReleaseExtract,
    Sourced,
    dossier_json,
)
from vinci.edgar import primary_source as ps

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
OUTCOMES = ("self_funding_check", "wall_coherence_check", "guide_verification_check")
IE_OUTCOMES = ("vintage_check", "net_debt_check")


# --- the producer: one decision, its line and its outcome ---------------------------------------


def test_self_funding_check_asks_whether_the_signs_agree() -> None:
    assert ps.self_funding_check(True, True) == CHECK_AGREE
    assert ps.self_funding_check(True, False) == CHECK_DIFFER
    assert ps.self_funding_check(False, True) == CHECK_DIFFER
    # two negative legs AGREE as a cross-check while the line still reads MIXED: a different
    # question ("do the sources point the same way", not "does the name fund itself")
    assert ps.self_funding_check(False, False) == CHECK_AGREE
    assert "MIXED" in ps.self_funding(False, False)
    for legs in ((None, True), (True, None), (None, None)):
        assert ps.self_funding_check(*legs) == CHECK_NOT_RUN
        assert "UNKNOWN" in ps.self_funding(*legs)


# --- the OCF leg: the LATEST quarter, made discrete from the year-to-date (2026-10-26) ------------
# Every value below is the committed companyfacts fixture (frozen 2026-10-23) read as filed by the
# date named — a frozen fixture, so the pins are values, never the living pages.


def _facts(ticker: str) -> dict[str, Any]:
    out: dict[str, Any] = json.loads((COMPANYFACTS / f"{ticker}.json").read_text())
    return out


def _ocf(facts: dict[str, Any], start: date, end: date, filed_by: date) -> list[float]:
    from vinci.edgar.concepts import extract_points

    return [p.value / 1e6 for p in extract_points(facts, "operating_cash_flow")
            if p.period_start == start and p.period_end == end and p.filed <= filed_by]


def test_the_ocf_leg_is_the_latest_quarter_not_the_last_one_tagged_alone() -> None:
    """A 10-Q tags cash flow YEAR-TO-DATE, so the one quarter most filers tag on its own is the
    first. Westlake's page, assembled 2026-09-28, read its Q1 (−$94M) three months after the
    second quarter had been filed. The latest quarter is the six months less the first:
    $224M − (−$94M) = +$318M."""
    wlk, asof = _facts("WLK"), date(2026, 9, 28)
    assert _ocf(wlk, date(2026, 1, 1), date(2026, 3, 31), asof) == [-94.0]
    assert dm._latest_quarter_ocf(wlk, filed_by=asof) == (318.0, date(2026, 6, 30))
    assert dm._latest_quarter_ocf_positive(wlk, filed_by=asof) is True


def test_a_fourth_quarter_is_the_year_less_its_nine_months() -> None:
    """No 10-Q covers a fourth quarter: the 10-K's year less the third 10-Q's nine months does.
    PARR's FY2024 (10-K filed 2025-02-28) is $83.8M less $99.2M = −$15.5M — a NEGATIVE quarter in
    a positive year whose first quarter was positive too, so neither the year-to-date's own sign
    nor the old single-quarter read can give it."""
    parr, asof = _facts("PARR"), date(2025, 3, 15)
    assert _ocf(parr, date(2024, 1, 1), date(2024, 12, 31), asof) == [pytest.approx(83.776)]
    assert _ocf(parr, date(2024, 1, 1), date(2024, 3, 31), asof)[0] > 0
    got = dm._latest_quarter_ocf(parr, filed_by=asof)
    assert got is not None and got[1] == date(2024, 12, 31)
    assert got[0] == pytest.approx(83.776 - 99.242)
    assert dm._latest_quarter_ocf_positive(parr, filed_by=asof) is False


def test_the_quarter_not_the_year_to_date_carries_the_sign() -> None:
    """The other direction: AORT's first half of 2025 is −$1.9M and its second quarter +$15.0M
    (less a first quarter of −$17.0M). The leg reads the quarter."""
    aort, asof = _facts("AORT"), date(2025, 8, 31)
    assert _ocf(aort, date(2025, 1, 1), date(2025, 6, 30), asof) == [pytest.approx(-1.942)]
    got = dm._latest_quarter_ocf(aort, filed_by=asof)
    assert got is not None and got[1] == date(2025, 6, 30)
    assert got[0] == pytest.approx(-1.942 + 16.953)
    assert dm._latest_quarter_ocf_positive(aort, filed_by=asof) is True


def test_a_quarter_the_filer_tags_on_its_own_is_read_as_tagged() -> None:
    """AMZN tags its second quarter discretely: that fact is the quarter, no difference taken."""
    got = dm._latest_quarter_ocf(_facts("AMZN"), filed_by=date(2026, 10, 9))
    assert got == (45387.0, date(2026, 6, 30))


def test_both_legs_of_the_difference_are_read_as_filed_by_the_same_date() -> None:
    """HWM's first quarter of 2020 was filed at −$291M and RESTATED to −$208M a year later. Read as
    filed by 2020-08-31, the second quarter is the first half (−$260M) less the first quarter AS
    THEN FILED: +$31M. The restated figure would make it −$52M — a sign the reader of that day
    could not have seen.

    And where BOTH legs were restated: the third quarter of 2017, read as filed by 2017-11-09, is
    +$172M; from the year-to-dates as later recast it is −$57M. A cut on one leg alone would not
    see that, nor would one on neither."""
    hwm, asof = _facts("HWM"), date(2020, 8, 31)
    assert _ocf(hwm, date(2020, 1, 1), date(2020, 3, 31), date(2099, 1, 1)) == [-291.0, -208.0]
    assert dm._latest_quarter_ocf(hwm, filed_by=asof) == (31.0, date(2020, 6, 30))
    assert dm._latest_quarter_ocf_positive(hwm, filed_by=asof) is True
    assert dm._latest_quarter_ocf(hwm, filed_by=date(2017, 11, 9)) == (172.0, date(2017, 9, 30))
    assert dm._latest_quarter_ocf_positive(hwm, filed_by=date(2017, 11, 9)) is True


def test_the_tag_is_chosen_from_the_filings_of_that_day_too() -> None:
    """AORT (then CryoLife) moved its operating cash flow to the continuing-operations tag in the
    10-K filed 2014-02-21, kept it until 2017, then went back. Chosen from today's blob, the plain
    tag wins (it reaches 2026), and read as filed by 2014-04-30 it serves its last quarter there:
    Q3 2013, +$7.3M, seven months old. The filings of that day carry Q1 2014 on the other tag,
    −$2.0M — and that blob is what an assembly on that day read (`concepts.facts_as_of`)."""
    aort, asof = _facts("AORT"), date(2014, 4, 30)
    got = dm._latest_quarter_ocf(aort, filed_by=asof)
    assert got is not None and got[1] == date(2014, 3, 31)
    assert got[0] == pytest.approx(-2.038)
    assert dm._latest_quarter_ocf_positive(aort, filed_by=asof) is False


def test_a_tag_the_filer_moved_back_to_mid_year_carries_the_latest_quarter() -> None:
    """BURL moved its operating cash flow back to the plain tag from its second quarter of 2018.
    As filed by 2018-11-28 (its third-quarter 10-Q) that tag's newest ANNUAL is FY2013 against the
    continuing-operations tag's FY2017, so the annual-grain alias walk (`extract_points`) calls the
    plain tag left behind and serves the other — whose newest quarter is the FIRST, to 2018-05-05
    (+$60.2M). The latest quarter is the plain tag's nine months less its half: $375.4M − $166.3M,
    to 2018-11-03."""
    burl, asof = _facts("BURL"), date(2018, 11, 28)
    got = dm._latest_quarter_ocf(burl, filed_by=asof)
    assert got is not None and got[1] == date(2018, 11, 3)
    assert got[0] == pytest.approx(375.353 - 166.307)


def test_an_abandoned_alias_is_never_served_for_a_later_period() -> None:
    """The other direction: UBER stopped tagging `RevenueFromContractWithCustomerExcludingAssessed
    Tax` after 2019-06-30 and has used `Revenues` since. The latest period is the newest any alias
    carries, so the abandoned one can never supply it once a later period is filed — read at every
    date UBER filed a revenue row. As filed by 2019-11-05 the alias walk still served the abandoned
    tag (its newest, 2019-06-30, inside the sibling allowance), with the quarter to 2019-09-30 filed
    under `Revenues`."""
    from vinci.edgar.concepts import CONCEPT_ALIASES, extract_points, facts_as_of, points_for_tag

    uber, gone = _facts("UBER"), "RevenueFromContractWithCustomerExcludingAssessedTax"
    tags = CONCEPT_ALIASES["revenue"]
    dates = sorted({p.filed for t in tags for p in points_for_tag(uber, t)})
    assert len(dates) == 32
    for d in dates:
        cut = facts_as_of(uber, d)
        newest = max(p.period_end for t in tags for p in points_for_tag(cut, t)
                     if p.period_start is not None)
        got = dm._latest_quarter(cut, "revenue")
        assert got is not None and got[1] == newest, d
        assert not (got[2] == gone and got[1] > date(2019, 6, 30)), d
    cut = facts_as_of(uber, date(2019, 11, 5))
    assert extract_points(cut, "revenue")[0].tag == gone
    got = dm._latest_quarter(cut, "revenue")
    assert got is not None and got[1:] == (date(2019, 9, 30), "Revenues")
    got = dm._latest_quarter(uber, "revenue")
    assert got is not None and got[1:] == (date(2026, 6, 30), "Revenues")


def test_a_period_two_aliases_carry_is_read_from_the_first_that_can_be_differenced() -> None:
    """FUBO tagged its operating cash flow under BOTH aliases for a while. As filed by 2017-08-21
    both carry the half to 2017-06-30 and both can be differenced: the plain tag wins by priority,
    −$0.179M less −$0.083M (the continuing-operations one would read +$0.102M). As filed by
    2015-11-16 both carry the nine months to 2015-09-30, but only the continuing-operations tag
    carries the half to take from it: −$0.739M less −$0.581M. Never mixed across the two."""
    fubo = _facts("FUBO")
    got = dm._latest_quarter_ocf(fubo, filed_by=date(2017, 8, 21))
    assert got is not None and got[1] == date(2017, 6, 30)
    assert got[0] == pytest.approx(-0.179 + 0.083, abs=1e-3)
    got = dm._latest_quarter_ocf(fubo, filed_by=date(2015, 11, 16))
    assert got is not None and got[1] == date(2015, 9, 30)
    assert got[0] == pytest.approx(-0.739 + 0.581, abs=1e-3)


def test_only_an_alias_carrying_the_latest_period_end_itself_is_read() -> None:
    """`_quarter` matches a period ending within a week. AORT as filed by 2014-04-30 carries the
    quarter to 2014-03-31 on the continuing-operations tag only (−$2.0M). Give the higher-priority
    plain tag a quarter closing three days earlier and it must not be read under 2014-03-31: it
    does not carry that period."""
    from vinci.edgar.concepts import facts_as_of

    aort = facts_as_of(_facts("AORT"), date(2014, 4, 30))
    rows = aort["facts"]["us-gaap"]["NetCashProvidedByUsedInOperatingActivities"]["units"]["USD"]
    rows.append({"start": "2013-12-29", "end": "2014-03-28", "val": 99_000_000,
                 "filed": "2014-04-30", "form": "10-Q", "fy": 2014, "fp": "Q1", "accn": "x"})
    got = dm._latest_quarter_ocf(aort)
    assert got is not None and got[1] == date(2014, 3, 31)
    assert got[0] == pytest.approx(-2.038)


def test_a_latest_period_that_cannot_be_differenced_is_unknown_never_an_older_quarter() -> None:
    """NKE's latest period on its 2026-09-30 page is the year to 2026-05-31. Without the nine
    months to take from it there is no fourth quarter, and the leg is UNKNOWN — never the first
    quarter to 2025-08-31 (+$222M) that the old read served, nine months stale."""
    from vinci.edgar.concepts import CONCEPT_ALIASES

    nke = _facts("NKE")
    for tag in CONCEPT_ALIASES["operating_cash_flow"]:
        for rows in (((nke["facts"].get("us-gaap") or {}).get(tag) or {}).get("units")
                     or {}).values():
            rows[:] = [r for r in rows
                       if (r.get("start"), r.get("end")) != ("2025-06-01", "2026-02-28")]
    asof = date(2026, 9, 30)
    assert _ocf(nke, date(2025, 6, 1), date(2025, 8, 31), asof) == [222.0]
    assert dm._latest_quarter_ocf(nke, filed_by=asof) is None
    assert dm._latest_quarter_ocf_positive(nke, filed_by=asof) is None
    # and with the nine months in place, the fourth quarter: $2,868M − $1,231M
    assert dm._latest_quarter_ocf(_facts("NKE"), filed_by=asof) == (1637.0, date(2026, 5, 31))


def test_the_self_funding_cite_names_the_quarter_it_read() -> None:
    """The stale quarter went unseen behind a cite that said only 'latest-Q'. The cite assembly
    writes names it — and falls back to the old words only where there is no quarter to name."""
    assert dm._self_funding_ref(_facts("WLK")) == (
        "EDGAR OCF sign, quarter to 2026-06-30 + CIQ LTM FCF sign")
    assert dm._self_funding_ref(None) == "EDGAR latest-Q OCF sign + CIQ LTM FCF sign"


_BAL = date(2026, 6, 30)


def _inst(name: str, principal: float, maturity: date) -> ps.PanelInstrument:
    return ps.PanelInstrument(name, principal, maturity)


def test_wall_read_outcome_and_the_boundary_reason() -> None:
    panel = [_inst("Term Loan", 100.0, date(2026, 12, 31))]
    agree = ps.wall_coherence_read(102.0, panel, balance=_BAL)
    assert (agree.check, agree.near_boundary) == (CHECK_AGREE, None)
    far = ps.wall_coherence_read(150.0, panel, balance=_BAL)
    assert (far.check, far.near_boundary, far.qa) == (CHECK_DIFFER, False, [])
    # an instrument maturing three days past +12m: the divergence STATES its reason, in the QA flag
    # and now structurally beside the outcome
    edge = [*panel, _inst("Bank Facility", 40.0, date(2027, 7, 3))]
    near = ps.wall_coherence_read(150.0, edge, balance=_BAL)
    assert (near.check, near.near_boundary) == (CHECK_DIFFER, True) and len(near.qa) == 1
    assert near.qa[0].startswith(ps.WALL_FLAG)        # the prefix the back-fill selects by
    none = ps.wall_coherence_read(None, panel, balance=_BAL)
    assert (none.check, none.near_boundary) == (CHECK_NOT_RUN, None)
    # the line-only API is the read's own line, never a second composition
    for r, w in ((far, 150.0), (none, None)):
        assert ps.wall_coherence(w, panel, balance=_BAL) == (r.line, r.qa)
    assert dm._wall_read(None, panel, None).check == CHECK_NOT_RUN       # no balance date


def test_a_panel_with_no_dated_principal_is_not_a_second_figure() -> None:
    """Codex, #793 round 1: with no CIQ instrument carrying BOTH a principal and a maturity, the
    panel's same-window total cannot be established — it summed to $0.0 against the filing and
    was stored as `differ`, an unexplained mismatch with no second figure. Not run, and the line
    says so. A panel whose dated instruments all mature outside the window still compares."""
    undated = [ps.PanelInstrument("Revolver", None, date(2027, 1, 31)),
               ps.PanelInstrument("Notes Payable", 78.3, None)]
    for panel in ([], undated):
        r = ps.wall_coherence_read(150.0, panel, balance=_BAL)
        assert (r.check, r.near_boundary, r.qa) == (CHECK_NOT_RUN, None, []), panel
        assert "UNKNOWN" in r.line and "DIVERGES" not in r.line
    later = [ps.PanelInstrument("Term Loan", 100.0, date(2029, 12, 31))]
    assert ps.wall_coherence_read(150.0, later, balance=_BAL).check == CHECK_DIFFER


def _guide(**kw: Any) -> ps.GuideVerification:
    args: dict[str, Any] = {"ciq_low": 100.0, "ciq_high": 110.0, **kw}
    lo, hi = args.pop("ciq_low"), args.pop("ciq_high")
    r = ps.guide_verification_read("revenue", lo, hi, **args)
    assert ps.guide_verification("revenue", lo, hi, **args) == r.line
    return r


def test_guide_read_agrees_only_when_verified_and_differs_only_on_a_mismatch() -> None:
    assert _guide(release_low=100.0, release_high=110.0).check == CHECK_AGREE
    assert _guide(release_low=100.0, release_high=110.0 + ps.GUIDE_MATCH).check == CHECK_DIFFER
    assert _guide(release_low=100.0 + ps.GUIDE_MATCH, release_high=110.0).check == CHECK_DIFFER
    not_run = {
        "no CIQ guide": _guide(ciq_low=None, ciq_high=None, release_low=100.0, release_high=110.0),
        "cross-basis": _guide(release_low=-2.0, release_high=2.0, release_basis="change"),
        "cross-period": _guide(release_low=400.0, release_high=440.0, ciq_period="FQ3 2026",
                               release_period="2026"),
        "vendor echo": _guide(ciq_low=100.0, ciq_high=100.0, prior_fy_actual=100.0),
        "qualitative": _guide(release_qualitative=True),
        "no number": _guide(),
    }
    assert {k: r.check for k, r in not_run.items()} == dict.fromkeys(not_run, CHECK_NOT_RUN)
    assert "VENDOR-ECHO" in not_run["vendor echo"].line          # a flag, and still not a check


def test_vintage_probe_reads_coherent_when_it_cannot_run() -> None:
    """THE NEGATIVE PIN (the bug this field answers): `vintage_coherent` is True with no consensus,
    a non-positive one, or no ladder level — the outcome says the probe never ran."""
    for a26, direct26 in ((None, 100.0), (100.0, None), (100.0, 0.0), (100.0, -5.0)):
        coherent, _note, check = dm._vintage_probe(a26, direct26)
        assert coherent is True and check == CHECK_NOT_RUN, (a26, direct26)
    edge = 100.0 * (1 + dm._IE_TOL)
    assert dm._vintage_probe(edge - 1e-6, 100.0)[2] == CHECK_AGREE
    assert dm._vintage_probe(edge + 1e-6, 100.0)[:3:2] == (False, CHECK_DIFFER)


def _iv(cash: float | None, debt: float | None) -> ImpliedValuation:
    return ImpliedValuation(
        implied_equity=Sourced.unknown(note="synthetic"), bridge=Sourced.unknown(note="synthetic"),
        bridge_cash=cash, bridge_debt=debt, market_cap=Sourced.present(1.0, source_ref="synthetic"),
        comparability_gate=Sourced.unknown(note="synthetic"))


def test_net_debt_probe_reads_reconciled_with_no_bridge() -> None:
    """THE NEGATIVE PIN: `net_debt_reconciled` is True with no bridge to test (`bridge_nd is None
    or …`); the outcome says not run."""
    assert dm._net_debt_probe(_iv(None, None), 50.0)[:2] == (True, CHECK_NOT_RUN)
    assert dm._net_debt_probe(_iv(10.0, 60.0), 50.0)[:2] == (True, CHECK_AGREE)
    assert dm._net_debt_probe(_iv(10.0, 70.0), 50.0)[:2] == (False, CHECK_DIFFER)


def test_a_point_guide_cannot_be_read_back_off_the_page() -> None:
    """A range row keeps CIQ's cell verbatim; a point row keeps `_fig`'s rounding — lossy."""
    row = GuidanceRow(metric="Revenue", latest_guide="'197,000.00 - 202,000.00'",
                      period="FQ3 2026", dated="2026-07-30", age="fresh", record="—",
                      most_recent="—")
    assert revenue_guide_from_rows([row]) == (197000.0, 202000.0, "FQ3 2026")
    point = row.model_copy(update={"latest_guide": _fig(427.516)})
    assert revenue_guide_from_rows([point]) == (427.5, 427.5, "FQ3 2026")
    other = row.model_copy(update={"metric": "EBITDA"})
    assert revenue_guide_from_rows([other, row])[2] == "FQ3 2026"   # the first REVENUE row
    assert revenue_guide_from_rows([other]) == (None, None, None)


# --- the write: absent until built, beside its sibling when built --------------------------------


def _doc(path: Path) -> Dossier:
    return Dossier.model_validate(json.loads(path.read_text()))


def _without_outcomes(page: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(json.dumps(page))
    mech = out["mechanical"]
    for k in (*OUTCOMES, "wall_coherence_near_boundary"):
        (mech.get("primary_source") or {}).pop(k, None)
    for k in IE_OUTCOMES:
        ((mech.get("valuation") or {}).get("implied_expectations") or {}).pop(k, None)
    return out


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_a_page_without_the_outcomes_round_trips_and_one_with_them_writes_them_beside() -> None:
    raw = json.loads(PAGES[0].read_text())
    bare = Dossier.model_validate(_without_outcomes(raw))
    text = dossier_json(bare)
    for k in (*OUTCOMES, *IE_OUTCOMES, "wall_coherence_near_boundary"):
        assert f'"{k}"' not in text, k                     # ABSENT, never null
    m = bare.mechanical
    assert m.valuation.implied_expectations is not None and m.primary_source is not None
    built = bare.model_copy(update={"mechanical": m.model_copy(update={
        "valuation": m.valuation.model_copy(update={
            "implied_expectations": m.valuation.implied_expectations.model_copy(
                update={"vintage_check": CHECK_NOT_RUN, "net_debt_check": CHECK_AGREE})}),
        "primary_source": m.primary_source.model_copy(update={
            "guide_verification_check": CHECK_DIFFER})})})
    out = json.loads(dossier_json(built))
    ie = list(out["mechanical"]["valuation"]["implied_expectations"])
    assert ie[ie.index("vintage_coherent") + 1] == "vintage_check"
    assert ie[ie.index("net_debt_reconciled") + 1] == "net_debt_check"
    keys = list(out["mechanical"]["primary_source"])
    assert keys[keys.index("guide_verification") + 1] == "guide_verification_check"
    assert "self_funding_check" not in keys                 # the ones left None stay absent


# --- the back-fill, end to end over the committed pages -----------------------------------------


class _FixtureEdgar:
    """EDGAR answered from the committed companyfacts fixtures; the submissions feed is not among
    them, so no 10-Q is found and the window falls back to the latest balance-sheet instant."""

    def __init__(self) -> None:
        self.by_cik = {str(json.loads(p.read_text())["cik"]).zfill(10): p
                       for p in COMPANYFACTS.glob("*.json")}

    def companyfacts(self, cik: str) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(self.by_cik[str(cik).zfill(10)].read_text())
        return out

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",)) -> list[Any]:
        return []


def _backfill(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    refused: list[str] = []
    with no_network():
        out = cross_check_transform(raw, edgar=_FixtureEdgar(), refused=refused)(
            raw["mechanical"])
    return out, refused


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_the_backfill_writes_or_names_every_outcome_and_never_contradicts_a_page() -> None:
    """Every outcome on every committed page is either written or named as not reproducing, and
    none disagrees with an outcome the page already carries — so a committed outcome is the one
    its page's own stored inputs give. The net-debt and vintage outcomes need nothing outside the
    page, so they are written on every page that carries the block."""
    contradictions: list[str] = []
    for path in PAGES:
        raw = json.loads(path.read_text())
        out, refused = _backfill(_without_outcomes(raw))
        contradictions += [r for r in _backfill(raw)[1] if "on the page" in r]
        t = raw["ticker"]
        ps_out = out.get("primary_source") or {}
        ie = (out.get("valuation") or {}).get("implied_expectations")
        for k in OUTCOMES:
            named = any(r.startswith(f"{t}: {k.removesuffix('_check')} ") for r in refused)
            assert (k in ps_out) != named, (t, k, refused)
        if ie is not None:
            assert all(k in ie for k in IE_OUTCOMES), (t, refused)
        for k in (*OUTCOMES, *IE_OUTCOMES):
            v = (ps_out.get(k) if k in OUTCOMES else (ie or {}).get(k))
            assert v in (None, CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN), (t, k, v)
    assert contradictions == []


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_the_flag_that_passed_without_running_is_not_run_on_real_pages() -> None:
    """CORPUS BEFORE SYNTHETIC: committed pages whose vintage probe never ran carry
    `vintage_coherent: true` — the shape the scorecard could not tell from a pass. The back-fill
    calls each of them not run; the flag is False exactly where the probe ran and differed."""
    cannot: list[str] = []
    ran: list[str] = []
    for path in PAGES:
        raw = json.loads(path.read_text())
        ie = (_backfill(_without_outcomes(raw))[0].get("valuation") or {}).get(
            "implied_expectations")
        if ie is None:
            continue
        (cannot if ie["vintage_check"] == CHECK_NOT_RUN else ran).append(raw["ticker"])
        assert ie["vintage_coherent"] is (ie["vintage_check"] != CHECK_DIFFER), raw["ticker"]
    assert cannot, "no committed page exercises the not-run probe — the pin is vacuous"
    assert ran


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_a_line_that_does_not_reproduce_is_named_and_left_absent() -> None:
    """A committed page with its CIQ revenue guide a 3-decimal POINT: the page rows keep it
    rounded, so the guide line assembly printed cannot be rebuilt — refused, never guessed. The
    other outcomes on the page are unaffected."""
    raw = _without_outcomes(json.loads(PAGES[0].read_text()))
    mech = raw["mechanical"]
    models = [ReleaseExtract.model_validate(r) for r in mech["primary_source"]["releases"]]
    fy = dm._fy_reconciliation(models)
    rel_lo, rel_hi, rel_qual, rel_basis, rel_period = dm._release_revenue_guide(models)
    assembled = ps.guide_verification(
        "revenue", 427.516, 427.516, prior_fy_actual=fy.get("revenue"),
        release_qualitative=rel_qual, release_low=rel_lo, release_high=rel_hi,
        release_basis=rel_basis, ciq_period="FY 2026", release_period=rel_period)
    mech["primary_source"]["guide_verification"]["value"] = assembled
    mech["catalyst_path"]["guidance_bridge_rows"] = Sourced.present(
        [GuidanceRow(metric="Revenue", latest_guide=_fig(427.516), period="FY 2026",
                     dated="2026-07-30", age="fresh", record="—", most_recent="—")],
        source_ref="synthetic").model_dump(mode="json")
    out, refused = _backfill(raw)
    t = raw["ticker"]
    assert "guide_verification_check" not in out["primary_source"]
    assert f"{t}: guide_verification does not reproduce from the page's stored inputs" in refused
    assert "net_debt_check" in out["valuation"]["implied_expectations"]


# --- each proof refuses on its own -------------------------------------------------------------


def _one_page_backfilled(pick: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """The first committed page `pick` accepts once back-filled from the fixtures: (raw page
    without outcomes, the back-filled mechanical layer)."""
    for path in PAGES:
        raw = _without_outcomes(json.loads(path.read_text()))
        out, _ = _backfill(raw)
        if pick(raw, out):
            return raw, out
    pytest.fail("no committed page fits — the pin is vacuous")


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_an_outcome_the_page_already_holds_is_kept_and_named_never_overwritten() -> None:
    raw, out = _one_page_backfilled(
        lambda r, o: "net_debt_check" in ((o.get("valuation") or {}).get("implied_expectations")
                                          or {}))
    real = out["valuation"]["implied_expectations"]["net_debt_check"]
    wrong = CHECK_DIFFER if real != CHECK_DIFFER else CHECK_AGREE
    raw["mechanical"]["valuation"]["implied_expectations"]["net_debt_check"] = wrong
    planted, refused = _backfill(raw)
    assert planted["valuation"]["implied_expectations"]["net_debt_check"] == wrong
    assert f"{raw['ticker']}: net_debt_check is {wrong!r} on the page, the reproduction gives " \
           f"{real!r}" in refused


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_a_vintage_note_that_does_not_reproduce_refuses_only_the_vintage_outcome() -> None:
    raw, _out = _one_page_backfilled(
        lambda r, o: "vintage_check" in ((o.get("valuation") or {}).get("implied_expectations")
                                         or {}))
    raw["mechanical"]["valuation"]["implied_expectations"]["coherence_note"] += " (edited)"
    out, refused = _backfill(raw)
    ie = out["valuation"]["implied_expectations"]
    assert "vintage_check" not in ie and "net_debt_check" in ie
    assert f"{raw['ticker']}: coherence_note does not reproduce from the page's stored " \
           "inputs" in refused


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_a_wall_flag_the_rebuild_does_not_give_back_refuses_the_wall_outcome() -> None:
    """The wall's QA flags are part of what must reproduce: the boundary reason is stored
    beside the outcome, so a page whose stored flag the rebuild does not give back is refused."""
    raw, _out = _one_page_backfilled(
        lambda r, o: (o.get("primary_source") or {}).get("wall_coherence_check") == CHECK_NOT_RUN)
    raw["mechanical"]["primary_source"]["qa_flags"].append(
        "wall coherence: divergence with an instrument maturing within ±7d of the +12m boundary "
        "(planted) — possible window-convention artifact, not a true divergence")
    out, refused = _backfill(raw)
    assert "wall_coherence_check" not in out["primary_source"]
    assert f"{raw['ticker']}: wall_coherence does not reproduce from the page's stored " \
           "inputs" in refused


def _with_a_later_quarter(facts: dict[str, Any], filed: date) -> dict[str, Any]:
    """The facts plus one more single quarter of the OTHER sign, after the latest quarter the leg
    reads, filed on ``filed``."""
    from vinci.edgar.concepts import CONCEPT_ALIASES

    last = dm._latest_quarter_ocf(facts)
    assert last is not None
    start = last[1].toordinal() + 1
    late = {"accn": "0000000000-26-999999", "start": date.fromordinal(start).isoformat(),
            "end": date.fromordinal(start + 90).isoformat(), "filed": filed.isoformat(),
            "form": "10-Q", "fp": "Q3", "fy": last[1].year,
            "val": -1.0 if last[0] > 0 else 1.0}
    out: dict[str, Any] = json.loads(json.dumps(facts))
    for tag in CONCEPT_ALIASES["operating_cash_flow"]:
        for unit in ((out["facts"].get("us-gaap") or {}).get(tag) or {}).get("units", {}).values():
            unit.append(late)
    return out


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_the_ocf_sign_is_read_as_it_stood_when_the_page_was_assembled() -> None:
    """A quarter filed AFTER the page was assembled is not the one its line was built on: read as
    filed by the assembly date, a later quarter of the other sign neither moves the outcome nor
    refuses the line. Read as of today, it would."""
    raw, out = _one_page_backfilled(
        lambda r, o: "self_funding_check" in (o.get("primary_source") or {}))
    assembled = date.fromisoformat(raw["assembled_at"][:10])
    edgar = _FixtureEdgar()
    facts = _with_a_later_quarter(edgar.companyfacts(raw["cik"]),
                                  date.fromordinal(assembled.toordinal() + 1))
    assert (dm._latest_quarter_ocf_positive(facts, filed_by=assembled)
            != dm._latest_quarter_ocf_positive(facts))

    class _Later(_FixtureEdgar):
        def companyfacts(self, cik: str) -> dict[str, Any]:
            return facts

    refused: list[str] = []
    with no_network():
        late = cross_check_transform(raw, edgar=_Later(), refused=refused)(raw["mechanical"])
    assert late["primary_source"]["self_funding_check"] == out["primary_source"][
        "self_funding_check"]
    assert not any("self_funding" in r for r in refused)


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_a_page_with_no_assembly_date_is_refused_whole_never_a_crash() -> None:
    """Review of this PR: `date.fromisoformat('None')` raised a bare ValueError that
    `refresh_fleet` does not catch, so one such page would stop the pass for every name."""
    raw = _without_outcomes(json.loads(PAGES[0].read_text()))
    del raw["assembled_at"]
    with pytest.raises(RefreshRefusedError, match="no assembled_at"):
        cross_check_transform(raw, edgar=_FixtureEdgar(), refused=[])


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_an_implied_block_without_its_inputs_is_named_not_skipped() -> None:
    """Review of this PR: with the comps name row's net debt gone, both implied-expectations
    outcomes were skipped and nothing was named — a clean-looking pass."""
    raw, _out = _one_page_backfilled(
        lambda r, o: "net_debt_check" in ((o.get("valuation") or {}).get("implied_expectations")
                                          or {}))
    for row in raw["mechanical"]["peer_comps"]["peer_grid"]["value"]:
        if row.get("is_name"):
            row["net_debt"] = None
    out, refused = _backfill(raw)
    ie = out["valuation"]["implied_expectations"]
    assert "net_debt_check" not in ie and "vintage_check" not in ie
    assert any(r.startswith(f"{raw['ticker']}: implied_expectations carries no comps name row")
               for r in refused)
