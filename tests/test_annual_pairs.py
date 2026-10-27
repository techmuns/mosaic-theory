"""§5.0 row 11, its open half — a combined annual figure reads ONE fiscal year, and no annual more
than one fiscal year behind the filer is served as current.

#817 withheld an annual its own concept had been reported past. A concept that stopped on EVERY
alias passed that check, and the screen's snapshot combined each leg's own latest annual, so two
fiscal years went into one number. Measured 2026-10-27 on 2,161 cached companyfacts: 132 filers'
FCF sign and 150 filers' EBITDA paired two years. Johnson & Johnson's EBITDA added FY2014
operating income to FY2025 D&A; SL Green's FCF sign took FY2019 capex off FY2025 operating cash
flow (`docs/records/2026-10-27-combined-annual-figures-read-one-fiscal-year.md`).

Every pin runs on a FROZEN real filer (`tests/fixtures/annual_pairs/`, README there), never on a
page or a tracking fixture.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date
from typing import Any

from vinci.dossier.anchor import _bridge_inputs, _latest_fcf
from vinci.dossier.edgar_fundamentals import EdgarFundamentals
from vinci.edgar.client import compute_fundamental_snapshot
from vinci.edgar.concepts import (
    CONCEPT_ALIASES,
    FILER_STALE_DAYS,
    StaleAnnual,
    current_annual,
    current_pair,
    extract_points,
    facts_as_of,
    filer_fiscal_year,
    filer_frontier,
    latest_annual,
    points_for_tag,
)
from vinci.schemas.envelope import CoverageStatus

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "annual_pairs"
OI, DA, OCF, CX = "operating_income", "dep_amort", "operating_cash_flow", "capex"


def _facts(ticker: str) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((FIXTURES / f"{ticker}.json").read_text())
    return facts


def _latest_end(facts: dict[str, Any], concept: str) -> date | None:
    p = latest_annual(extract_points(facts, concept))
    return p.period_end if p else None


# --- POSITIVE: a pair of two fiscal years goes UNKNOWN, naming the year -----------------------


def test_jnj_ebitda_no_longer_adds_fy2014_operating_income_to_fy2025_d_and_a() -> None:
    """Johnson & Johnson's `OperatingIncomeLoss` ends at FY2014; its D&A runs to FY2025. EBITDA
    was the sum of the two ($29.09bn) and net leverage divided a real net debt by it (0.94x).
    Both are UNKNOWN now, for the reason that is true: the newest year both legs carry is FY2014,
    more than one fiscal year behind the filer's newest — never "no EBITDA in XBRL"."""
    facts = _facts("JNJ")
    assert (_latest_end(facts, OI), _latest_end(facts, DA)) == (
        date(2014, 12, 28), date(2025, 12, 28)), "the mixed pair must be in the data"
    snap = compute_fundamental_snapshot("JNJ", facts)
    assert snap.ebitda_annual.coverage_status is CoverageStatus.UNKNOWN
    note = snap.ebitda_annual.note or ""
    assert note.startswith("newest year both operating_income and dep_amort carry ends 2014-12-28")
    assert "behind the filer's newest fiscal year" in note and "2025-12-28" in note
    assert snap.net_debt.coverage_status is CoverageStatus.PRESENT, "the net debt must be real"
    assert snap.net_leverage.coverage_status is CoverageStatus.UNKNOWN
    assert snap.net_leverage.note == note
    assert "no EBITDA in XBRL" not in (snap.net_leverage.note or "")


def test_a_single_leg_more_than_a_fiscal_year_behind_is_withheld() -> None:
    """J&J's operating-income sign read its FY2014 annual as current. Rule (b) on one leg: the
    year is 4,018d behind the filer's newest fiscal year (2025-12-28), so it is withheld."""
    point, stale = current_annual(_facts("JNJ"), OI)
    assert point is None
    assert stale == StaleAnnual(
        concept=OI, tag="OperatingIncomeLoss", period_end=date(2014, 12, 28),
        newer_tag="RevenueFromContractWithCustomerExcludingAssessedTax",
        newer_end=date(2025, 12, 28), lag_days=4018, against_filer=True)
    snap = compute_fundamental_snapshot("JNJ", _facts("JNJ"))
    assert snap.op_income_sign.coverage_status is CoverageStatus.UNKNOWN
    assert snap.op_income_sign.note == stale.note


def test_slg_fcf_sign_no_longer_subtracts_fy2019_capex() -> None:
    """SL Green: no capex alias carries a period after 2019-12-31, so #817's check passed it, and
    the FCF sign was FY2025 operating cash flow less FY2019 capex (−1). It is UNKNOWN now, and the
    anchor's FCF names the same year."""
    facts = _facts("SLG")
    assert (_latest_end(facts, OCF), _latest_end(facts, CX)) == (
        date(2025, 12, 31), date(2019, 12, 31)), "the mixed pair must be in the data"
    fcf = compute_fundamental_snapshot("SLG", facts).fcf_sign
    assert fcf.coverage_status is CoverageStatus.UNKNOWN
    note = fcf.note or ""
    assert note.startswith("newest year both operating_cash_flow and capex carry ends 2019-12-31, "
                           "2192d behind the filer's newest fiscal year (Revenues to 2025-12-31)")
    anchor = _bridge_inputs({}, facts)["ltm_fcf"]
    assert anchor.value is None and anchor.source == f"UNKNOWN — {note}"


def test_the_fallback_fcf_names_the_year_against_the_filer() -> None:
    """The CIQ-empty fallback reads the same pairing, so its refusal names the same year the same
    way. Its STATUS moves on none of the 2,161 cached filers: #817's per-leg check already refused
    every pair this one does."""
    fcf = EdgarFundamentals(_facts("SLG")).free_cash_flow()
    assert fcf.status.value == "unknown"
    assert (fcf.note or "").startswith(
        "EDGAR: newest year both operating_cash_flow and capex carry ends 2019-12-31, 2192d behind")


def test_a_pair_a_year_apart_goes_unknown_when_one_leg_moved_on() -> None:
    """The shared year may be within a year of the filer's newest, and still refused: Valero's
    capex ends at FY2024 while its operating cash flow reaches FY2025, and USA TODAY's operating
    income ends at FY2024 while its D&A reaches FY2025. The newest year both carry is FY2024; the
    other leg's own concept has been reported past it (#817's check, kept at the shared year), so
    FY2024 is not that leg's current year. 52 such pairs on the census, none served."""
    for ticker, (a, b), why in (("VLO", (OCF, CX), OCF), ("TDAY", (OI, DA), DA)):
        legs, stale = current_pair(_facts(ticker), a, b)
        assert legs is None and stale is not None, ticker
        assert stale.period_end == date(2024, 12, 31) and stale.behind is None, ticker
        assert [s.concept for s in stale.legs] == [why], ticker
    assert compute_fundamental_snapshot("VLO", _facts("VLO")).fcf_sign.coverage_status is (
        CoverageStatus.UNKNOWN)
    assert compute_fundamental_snapshot("TDAY", _facts("TDAY")).ebitda_annual.coverage_status is (
        CoverageStatus.UNKNOWN)


def test_the_anchor_fcf_refuses_a_same_period_pair_a_fiscal_year_behind_its_quarters() -> None:
    """Rule (c). FUBO moved its year end to September; both legs' newest annual is calendar 2024
    while both concepts carry quarters to 2026-06-30. The anchor served "operating_cash_flow −
    capex (FY2024, same period)", −$82.2M, and the R2 survival gate divides cash by it. Read off
    `_bridge_inputs`, the block the committed anchor carries."""
    facts = _facts("FUBO")
    assert _latest_end(facts, OCF) == _latest_end(facts, CX) == date(2024, 12, 31)
    fcf = _bridge_inputs({}, facts)["ltm_fcf"]
    assert fcf.value is None
    src = fcf.source or ""
    assert src.startswith("UNKNOWN — newest year both operating_cash_flow and capex carry ends "
                          "2024-12-31")
    assert "stale annual operating_cash_flow" in src and "stale annual capex" in src


# --- NEGATIVE: what stays --------------------------------------------------------------------


def test_a_current_pair_stays() -> None:
    """The same filers, on the pairs they still report together: J&J's FCF (FY2025, $19.70bn at
    the anchor) and SL Green's EBITDA (FY2025). Non-vacuous: each filer has a pair withheld."""
    jnj = _facts("JNJ")
    assert compute_fundamental_snapshot("JNJ", jnj).fcf_sign.value == 1
    got = _latest_fcf(jnj)
    assert isinstance(got, tuple) and got[0] == 19_698_000_000.0
    assert got[2] == "EDGAR companyfacts operating_cash_flow − capex (FY2025, same period)"
    slg = _facts("SLG")
    legs, stale = current_pair(slg, OI, DA)
    assert stale is None and legs is not None and legs[0].period_end == date(2025, 12, 31)
    assert compute_fundamental_snapshot("SLG", slg).ebitda_annual.value == 914_698_000.0


def test_a_pair_reads_one_period_not_each_legs_latest() -> None:
    """Amazon's D&A carries a 10-Q's trailing column to 2026-06-30 ($75.2bn); its operating income
    carries no such column. EBITDA was FY2025 operating income plus that trailing D&A
    ($155.18bn). It is now both legs for the year to 2025-12-31: $79.975bn + $65.756bn."""
    facts = _facts("AMZN")
    da = latest_annual(extract_points(facts, DA))
    assert da is not None and (da.period_end, da.value) == (date(2026, 6, 30), 75_200_000_000.0)
    snap = compute_fundamental_snapshot("AMZN", facts)
    assert snap.ebitda_annual.coverage_status is CoverageStatus.PRESENT
    assert snap.ebitda_annual.value == 79_975_000_000.0 + 65_756_000_000.0


def test_one_fiscal_year_behind_stays() -> None:
    """USA TODAY's `OperatingIncomeLoss` ends at FY2024 and the filer's newest fiscal year is
    FY2025: 365 days, one fiscal year. Nothing newer exists for the concept, so the FY2024 sign is
    the filer's newest word on it and is served (−1). 17 single figures in 16 filers stand so on
    the census (operating-income sign 9, diluted EPS 8)."""
    facts = _facts("TDAY")
    fy = filer_fiscal_year(facts)
    assert fy is not None and fy.period_end == date(2025, 12, 31)
    point, stale = current_annual(facts, OI)
    assert stale is None and point is not None and point.period_end == date(2024, 12, 31)
    sign = compute_fundamental_snapshot("TDAY", facts).op_income_sign
    assert sign.coverage_status is CoverageStatus.PRESENT and sign.value == -1


def test_the_threshold_sits_in_the_measured_gap() -> None:
    """Served annuals against their filer's newest fiscal year, 2,161 filers: one fiscal year
    behind lands at 360–371d, two at 728d or more, and nothing between. Two shortest fiscal
    years (700d) sits in that gap — set by it, never by outcomes."""
    assert 371 < FILER_STALE_DAYS < 728


def test_a_forward_dated_annual_does_not_date_the_filers_fiscal_year() -> None:
    """Daily Journal's 10-Q filed 2013-08-14 tags pre-tax income for 2012-10-01..2013-09-30, a
    year that had not ended. Counted, it would date the filer's newest fiscal year to 2013-09-30
    and put its FY2011 EPS 731d behind. As filed that day the newest fiscal year is FY2012, and the
    FY2011 EPS ($5.68, one year behind) is served."""
    facts = facts_as_of(_facts("DJCO"), date(2013, 8, 14))
    ahead = [p for t in CONCEPT_ALIASES["pretax_income"] for p in points_for_tag(facts, t)
             if p.is_annual and p.period_end > p.filed]
    assert [(p.period_end, p.filed) for p in ahead] == [(date(2013, 9, 30), date(2013, 8, 14))]
    fy = filer_fiscal_year(facts)
    assert fy is not None and fy.period_end == date(2012, 9, 30)
    point, stale = current_annual(facts, "eps_diluted")
    assert stale is None and point is not None and point.value == 5.68


def test_the_filers_fiscal_year_is_its_annual_periods_not_its_frontier() -> None:
    """Innodata's frontier of any tag reaches 2034-03-31 (a share-option context). Measured
    against that, its FY2025 operating income would be 3,012d behind. Its newest fiscal year is
    FY2025, so the FY2025 annual is current."""
    facts = _facts("INOD")
    assert filer_frontier(facts) == date(2034, 3, 31)
    fy = filer_fiscal_year(facts)
    assert fy is not None and fy.period_end == date(2025, 12, 31)
    point, stale = current_annual(facts, OI)
    assert stale is None and point is not None and point.period_end == date(2025, 12, 31)
