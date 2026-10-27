"""§5.0 row 11 — an annual reader never serves a stale annual AS CURRENT.

`extract_points` picks an alias by how far its ANNUAL series reaches against its siblings'. It
cannot see that the annual it serves is old, so `latest_annual(extract_points(...))` handed the
screen a year that closed long ago. Measured 2026-10-26 on 2,161 cached companyfacts: Climb
Global's FY2019 capex subtracted from its FY2025 operating cash flow, AbCellera's FY2023 D&A added
to its FY2025 operating income. `current_annual` withholds an annual that its own concept has
been reported past by a fiscal year, and names it
(`docs/records/2026-10-27-annual-readers-withhold-a-stale-annual.md`).

Every pin runs on a FROZEN real filer (`tests/fixtures/stale_annual/`, README there), never on a
page or a tracking fixture: the values pinned are what those files hold, and nothing refreshes
them.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date
from typing import Any

import pytest

from vinci.dossier.edgar_fundamentals import EdgarFundamentals
from vinci.edgar.client import compute_fundamental_snapshot
from vinci.edgar.concepts import (
    ANNUAL_STALE_DAYS,
    CONCEPT_ALIASES,
    StaleAnnual,
    current_annual,
    extract_points,
    facts_as_of,
    latest_annual,
    points_for_tag,
)
from vinci.schemas.envelope import CoverageStatus

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "stale_annual"


def _facts(ticker: str) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((FIXTURES / f"{ticker}.json").read_text())
    return facts


# --- POSITIVE: each of the six measured cases is withheld, naming both ends ------------------

#: (ticker, concept, served alias, its annual's end, alias with the newest period, that end, lag)
_MEASURED = [
    ("CLMB", "capex", "PaymentsToAcquireProductiveAssets", "2019-12-31",
     "PaymentsToAcquirePropertyPlantAndEquipment", "2026-06-30", 2373),
    ("LODE", "capex", "PaymentsToAcquireProductiveAssets", "2023-12-31",
     "PaymentsToAcquirePropertyPlantAndEquipment", "2026-06-30", 912),
    ("ABCL", "dep_amort", "DepreciationAndAmortization", "2023-12-31",
     "DepreciationDepletionAndAmortization", "2026-06-30", 912),
    ("DRH", "dep_amort", "DepreciationAndAmortization", "2017-12-31",
     "DepreciationDepletionAndAmortization", "2026-06-30", 3103),
    ("SLG", "pretax_income",
     "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterest"
     "AndIncomeLossFromEquityMethodInvestments", "2017-12-31",
     "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
     "2024-03-31", 2282),
    ("KALV", "revenue", "Revenues", "2024-04-30",
     "RevenueFromContractWithCustomerExcludingAssessedTax", "2026-03-31", 700),
]


@pytest.mark.parametrize(("ticker", "concept", "tag", "end", "newer_tag", "newer_end", "lag"),
                         _MEASURED, ids=[f"{m[0]}-{m[1]}" for m in _MEASURED])
def test_each_measured_stale_annual_is_withheld_and_named(
    ticker: str, concept: str, tag: str, end: str, newer_tag: str, newer_end: str, lag: int,
) -> None:
    """The six cases of row 11, each on its own real filer.

    The first assertion is the DEFECT, still in the data: the alias walk serves exactly this old
    annual. If it stops doing so the case has changed, and this pin says so rather than passing
    on a filer that no longer has the shape. AbCellera and KalVista are the two `stale_served`
    could never name: their served alias still carries recent quarters."""
    facts = _facts(ticker)
    served = latest_annual(extract_points(facts, concept))
    assert served is not None and served.tag == tag
    assert served.period_end == date.fromisoformat(end), (
        f"{ticker} {concept}: the walk now serves the year to {served.period_end} — re-measure")

    point, stale = current_annual(facts, concept)
    assert point is None, f"{ticker} {concept}: the year to {end} was served as current"
    assert stale == StaleAnnual(concept=concept, tag=tag, period_end=date.fromisoformat(end),
                                newer_tag=newer_tag, newer_end=date.fromisoformat(newer_end),
                                lag_days=lag)
    assert end in stale.note and newer_end in stale.note and concept in stale.note


def test_one_fiscal_year_behind_is_stale_at_the_boundary() -> None:
    """The shortest lag the check must catch: ONE fiscal year. PennyMac's `Revenues` carries the
    year to 2018-12-31 as its newest annual, and its quarters of 2019 from the FY2019 10-K, to
    2019-12-31: 365 days. FY2019 closed and was reported, so FY2018 is not the current year. A
    threshold of 'more than a year' (>365d), or `stale_served`'s 550d, would serve it."""
    point, stale = current_annual(_facts("PMT"), "revenue")
    assert point is None and stale is not None
    assert (stale.period_end, stale.newer_end, stale.lag_days) == (
        date(2018, 12, 31), date(2019, 12, 31), 365)


def test_the_threshold_sits_in_the_measured_gap() -> None:
    """Set by the gap in the corpus, never by outcomes. Above 335d, KalVista's eight-month
    transition period (its last full year IS its newest annual); at most 364d, a 52-week year
    one fiscal year behind. The 2,161-filer census found nothing between 280d and 335d."""
    assert 335 < ANNUAL_STALE_DAYS <= 364


# --- END TO END: the screen's inputs, read off the real snapshot ------------------------------


def test_the_screens_fcf_sign_no_longer_subtracts_a_years_old_capex() -> None:
    """Climb Global and Comstock: the operating-cash-flow leg is FY2025 and current, the capex leg
    is FY2019 / FY2023. The sign was served as PRESENT from the mix; it is now UNKNOWN, naming
    the capex leg and its year."""
    for ticker, capex_end in (("CLMB", "2019-12-31"), ("LODE", "2023-12-31")):
        facts = _facts(ticker)
        ocf, ocf_stale = current_annual(facts, "operating_cash_flow")
        assert ocf is not None and ocf_stale is None and ocf.period_end == date(2025, 12, 31)
        fcf = compute_fundamental_snapshot(ticker, facts).fcf_sign
        assert fcf.coverage_status is CoverageStatus.UNKNOWN, f"{ticker}: {fcf}"
        assert "stale annual capex" in (fcf.note or "") and capex_end in (fcf.note or "")


def test_the_screens_ebitda_no_longer_adds_a_years_old_d_and_a() -> None:
    """AbCellera: FY2025 operating income, FY2023 D&A. EBITDA is withheld, naming the D&A leg —
    and the current leg is still served: the operating-income sign stays PRESENT."""
    snap = compute_fundamental_snapshot("ABCL", _facts("ABCL"))
    assert snap.ebitda_annual.coverage_status is CoverageStatus.UNKNOWN
    assert "stale annual dep_amort" in (snap.ebitda_annual.note or "")
    assert snap.op_income_sign.coverage_status is CoverageStatus.PRESENT
    assert snap.op_income_sign.value == -1


def test_a_withheld_leg_is_named_in_the_ratio_it_breaks() -> None:
    """DiamondRock: a real net debt at 2026-06-30 over an FY2017 EBITDA read 4.16x as PRESENT.
    Net leverage is now UNKNOWN for the reason that is true — both earnings legs are FY2017 —
    and never the generic "no EBITDA in XBRL", which would send a reader looking for a tag."""
    snap = compute_fundamental_snapshot("DRH", _facts("DRH"))
    assert snap.net_debt.coverage_status is CoverageStatus.PRESENT, "the net debt must be real"
    lev = snap.net_leverage
    assert lev.coverage_status is CoverageStatus.UNKNOWN
    note = lev.note or ""
    assert "stale annual operating_income" in note and "stale annual dep_amort" in note
    assert "no EBITDA in XBRL" not in note
    assert snap.op_income_sign.coverage_status is CoverageStatus.UNKNOWN


def test_a_stale_cash_flow_leg_is_named_in_net_debt_to_ocf() -> None:
    """Greif: a real $748.6M net debt over operating cash flow for the year to 2024-10-31, while
    the concept carries periods to 2026-03-31. The page's EDGAR net debt / OCF fallback read
    2.10x; it is now UNKNOWN for that reason, never "no operating cash flow in XBRL"."""
    snap = compute_fundamental_snapshot("GEF", _facts("GEF"))
    assert snap.net_debt.coverage_status is CoverageStatus.PRESENT, "the net debt must be real"
    ratio = snap.net_debt_to_ocf
    assert ratio.coverage_status is CoverageStatus.UNKNOWN
    note = ratio.note or ""
    assert "stale annual operating_cash_flow" in note and "2024-10-31" in note
    assert "no operating cash flow in XBRL" not in note


def test_the_page_fallback_fcf_refuses_a_pair_that_last_met_years_ago() -> None:
    """The CIQ-empty fallback keys FCF by period, so it never mixed years — it served the LATEST
    year both legs share, however old. Climb Global's is 2019; SL Green's is 2019 too, because no
    capex alias carries a later period, and the operating-cash-flow leg's own concept has moved
    on six years. AbCellera's FY2025 pair is current and is still served."""
    for ticker in ("CLMB", "SLG"):
        fcf = EdgarFundamentals(_facts(ticker)).free_cash_flow()
        assert fcf.status.value == "unknown", f"{ticker}: {fcf}"
        assert "stale annual operating_cash_flow" in (fcf.note or "")
        assert "2019-12-31" in (fcf.note or "")
    current = EdgarFundamentals(_facts("ABCL")).free_cash_flow()
    assert current.status.value == "present", current
    assert "PaymentsToAcquirePropertyPlantAndEquipment" in (current.source_ref or "")


# --- NEGATIVE: what the check must NOT withhold ------------------------------------------------


@pytest.mark.parametrize(("ticker", "concept", "end"), [
    ("CLMB", "operating_cash_flow", "2025-12-31"),
    ("LODE", "operating_cash_flow", "2025-12-31"),
    ("ABCL", "operating_income", "2025-12-31"),
    ("ABCL", "capex", "2025-12-31"),
    ("SLG", "operating_cash_flow", "2025-12-31"),
])
def test_a_current_annual_is_served(ticker: str, concept: str, end: str) -> None:
    """The filers above, on the concepts they still report every year. Non-vacuous: each is a
    filer the check DOES withhold something from."""
    point, stale = current_annual(_facts(ticker), concept)
    assert stale is None and point is not None and point.period_end == date.fromisoformat(end)


def test_an_alias_switch_with_a_current_annual_is_not_flagged() -> None:
    """ScanSource, the census shape with a CURRENT annual. It tags its 10-Ks on the
    continuing-operations alias and its 10-Qs on the plain one, which outranks it and carries the
    newer period (2026-03-31). The walk serves the continuing alias's year to 2025-06-30: 274d
    behind, a third-quarter 10-Q. It is the current year and must be served."""
    facts = _facts("SCSC")
    plain, cont = CONCEPT_ALIASES["operating_cash_flow"]
    newest_plain = max(p.period_end for p in points_for_tag(facts, plain))
    point, stale = current_annual(facts, "operating_cash_flow")
    assert stale is None and point is not None
    assert point.tag == cont and point.period_end == date(2025, 6, 30)
    assert newest_plain == date(2026, 3, 31), "the higher-priority alias carries the newer period"


def test_a_forward_dated_context_is_not_a_reported_period() -> None:
    """REVIEW FINDING. NAPCO's 10-Q filed 2025-05-05 tags net income for 2025-01-01..2025-09-30 —
    a period that had not ended when it was filed. Read as the concept's newest period, it put
    the current year to 2024-06-30 457d behind and withheld it. A period ending after its own
    filing date is skipped; 61 such points sit in 18 of the 2,161 cached filers."""
    facts = facts_as_of(_facts("NSSC"), date(2025, 5, 5))
    ahead = [p for t in CONCEPT_ALIASES["net_income"] for p in points_for_tag(facts, t)
             if p.period_end > p.filed]
    assert [(p.period_end, p.filed) for p in ahead] == [(date(2025, 9, 30), date(2025, 5, 5))], (
        "the forward-dated row must be in the data for this case to exist")
    point, stale = current_annual(facts, "net_income")
    assert stale is None and point is not None and point.period_end == date(2024, 6, 30)


def test_a_transition_period_is_not_a_fiscal_year() -> None:
    """KalVista moved its year end from April to December: after the year to 2025-04-30 came an
    eight-month period, then a quarter to 2026-03-31 (335d). No newer fiscal year exists, so the
    year to 2025-04-30 IS the latest — while its revenue, a year further behind, is withheld."""
    point, stale = current_annual(_facts("KALV"), "operating_income")
    assert stale is None and point is not None and point.period_end == date(2025, 4, 30)


# --- THE GAP #817 LEFT, closed: a concept stopped on every alias --------------------------------


def test_a_concept_stopped_on_every_alias_is_withheld_against_the_filer() -> None:
    """SL Green: no capex alias carries a period after 2019-12-31, so the served annual IS the
    concept's newest period and #817's check passes it — this pin was its falsifier, asserting the
    year was still served. The annual is now also measured against the filer's newest fiscal year
    (`concepts.behind_filer`), and FY2019 is 2,192d behind FY2025: withheld, and the screen's FCF
    sign no longer takes FY2025 operating cash flow less FY2019 capex
    (`docs/records/2026-10-27-combined-annual-figures-read-one-fiscal-year.md`)."""
    facts = _facts("SLG")
    capex, stale = current_annual(facts, "capex")
    assert capex is None and stale is not None and stale.against_filer
    assert (stale.period_end, stale.newer_end, stale.lag_days) == (
        date(2019, 12, 31), date(2025, 12, 31), 2192)
    fcf = compute_fundamental_snapshot("SLG", facts).fcf_sign
    assert fcf.coverage_status is CoverageStatus.UNKNOWN
