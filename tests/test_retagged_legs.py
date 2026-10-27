"""A leg the filer RE-TAGGED is read from its new tag — only where the filer proved it is the line.

#821 withheld every annual leg more than a fiscal year behind (or reported past), and many of
those filers had not stopped reporting the line: they had moved it to another tag. Scotts
Miracle-Gro's combined D&A ends at FY2024 and its FY2025 is `Depreciation` +
`AmortizationOfIntangibleAssets`. A substitute is accepted only where it reports the old line's
figure, to rounding, in the latest year both carry, and continues unbroken from there
(`concepts.annual_line`;
`docs/records/2026-10-27-a-retagged-annual-leg-is-read-from-its-new-tag.md`).

Every pin runs on a FROZEN real filer (`tests/fixtures/retagged_legs/`, README there).
"""
from __future__ import annotations

import copy
import json
import pathlib
from datetime import date
from typing import Any

from vinci.dossier.anchor import _bridge_inputs
from vinci.dossier.edgar_fundamentals import EdgarFundamentals
from vinci.edgar.client import compute_fundamental_snapshot
from vinci.edgar.concepts import (
    SUBSTITUTE_TOLERANCE,
    annual_by_period,
    annual_line,
    current_annual,
    extract_points,
)
from vinci.schemas.envelope import CoverageStatus

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "retagged_legs"
SPLIT = ("Depreciation", "AmortizationOfIntangibleAssets")


def _facts(ticker: str) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((FIXTURES / f"{ticker}.json").read_text())
    return facts


def _aliases_end(facts: dict[str, Any], concept: str) -> date:
    return max(annual_by_period(extract_points(facts, concept)))


def _m(x: float | None) -> float:
    assert x is not None
    return round(x / 1e6, 3)


# --- POSITIVE: a proven re-tag continues the line ---------------------------------------------


def test_a_proven_split_continues_dep_amort() -> None:
    """Scotts: `DepreciationAndAmortization` ends at FY2024. At that handover the split summed to
    it exactly ($80.6M), so FY2025 is read from the split: $62.7M + $12.3M = $75.0M. EBITDA comes
    back as one fiscal year: FY2025 operating income $358.6M + $75.0M."""
    facts = _facts("SMG")
    assert _aliases_end(facts, "dep_amort") == date(2024, 9, 30), "the aliases must stop here"
    line = annual_line(facts, "dep_amort")
    assert line.substitute == SPLIT
    newest = line.by_period[date(2025, 9, 30)]
    assert _m(newest.value) == 75.0
    assert newest.tag == "Depreciation + AmortizationOfIntangibleAssets"
    # an aliased year is never replaced: FY2015's split read $62.8M against the alias's $53.5M
    assert _m(line.by_period[date(2015, 9, 30)].value) == 53.5
    ebitda = compute_fundamental_snapshot("SMG", facts).ebitda_annual
    assert ebitda.coverage_status is CoverageStatus.PRESENT
    assert _m(ebitda.value) == 433.6


def test_a_proven_capex_retag_reaches_the_screen_the_anchor_and_the_fallback() -> None:
    """Choice Hotels: `PaymentsToAcquirePropertyPlantAndEquipment` ends at FY2019, where
    `PaymentsToAcquireOtherPropertyPlantAndEquipment` carried the same $57.342M; that tag runs on
    every year to FY2025 ($38.924M). The FCF sign, the anchor's FCF and the CIQ-empty fallback all
    read FY2025, and the anchor and fallback name the tag read."""
    facts = _facts("CHH")
    assert _aliases_end(facts, "capex") == date(2019, 12, 31)
    line = annual_line(facts, "capex")
    assert line.substitute == ("PaymentsToAcquireOtherPropertyPlantAndEquipment",)
    assert _m(line.by_period[date(2025, 12, 31)].value) == 38.924
    assert compute_fundamental_snapshot("CHH", facts).fcf_sign.value == 1
    anchor = _bridge_inputs({}, facts)["ltm_fcf"]
    assert anchor.value == 231.523
    src = anchor.source or ""
    assert "capex read from PaymentsToAcquireOtherPropertyPlantAndEquipment" in src
    fb = EdgarFundamentals(facts).free_cash_flow()
    assert fb.status.value == "present" and fb.value == 231.5
    assert "PaymentsToAcquireOtherPropertyPlantAndEquipment [FY2025]" in (fb.source_ref or "")


# --- NEGATIVE: a substitute that is not the line is refused ------------------------------------


def test_a_split_that_is_a_component_is_refused() -> None:
    """Ecovyst: at the FY2024 handover the split summed to $68.383M against a combined D&A of
    $89.362M — 23% short, a component. It is refused and EBITDA stays UNKNOWN. Grocery Outlet's
    split runs 1.63% short ($106.447M vs $108.206M): close, still a different quantity."""
    for ticker in ("ECVT", "GO"):
        facts = _facts(ticker)
        assert annual_line(facts, "dep_amort").substitute == (), ticker
        snap = compute_fundamental_snapshot(ticker, facts)
        assert snap.ebitda_annual.coverage_status is CoverageStatus.UNKNOWN, ticker


def test_two_tags_one_filing_reports_apart_are_two_quantities() -> None:
    """Thor: its FY2025 10-K tags $121.616M under `PaymentsToAcquireProductiveAssets` and
    $122.987M under `PaymentsToAcquireOtherPropertyPlantAndEquipment` for the same year (1.13%).
    The second carries FY2026, but it is not the first line, and the FCF sign stays UNKNOWN."""
    facts = _facts("THO")
    assert _aliases_end(facts, "capex") == date(2025, 7, 31)
    assert annual_line(facts, "capex").substitute == ()
    assert compute_fundamental_snapshot("THO", facts).fcf_sign.coverage_status is (
        CoverageStatus.UNKNOWN)


def test_a_substitute_with_no_year_in_common_is_refused() -> None:
    """Pacific Biosciences: the combined D&A ends at FY2018 and the split begins at FY2019. No
    year carries both, so nothing shows the split is the line; it is refused."""
    facts = _facts("PACB")
    assert _aliases_end(facts, "dep_amort") == date(2018, 12, 31)
    assert annual_line(facts, "dep_amort").substitute == ()
    assert compute_fundamental_snapshot("PACB", facts).ebitda_annual.coverage_status is (
        CoverageStatus.UNKNOWN)


def test_a_vessel_lessors_capital_improvements_are_not_its_capex() -> None:
    """Global Ship Lease: at the FY2024 handover `PaymentsForCapitalImprovements` carried $12.840M
    against capex of $6.850M. Refused."""
    assert annual_line(_facts("GSL"), "capex").substitute == ()


def test_a_zero_ends_the_continuation() -> None:
    """Lantheus: `PaymentsToAcquireOtherProductiveAssets` matched capex at the FY2023 handover
    ($45.345M) and read $80.911M for FY2024, then $0 for FY2025 — while
    `PaymentsForCapitalImprovements` carried $36.089M. A line the filer emptied is not a year it
    spent nothing: the continuation stops at FY2024, so FY2024 capex has been reported past
    (the substitute's own FY2025 row) and is withheld, and the FCF sign stays UNKNOWN."""
    facts = _facts("LNTH")
    line = annual_line(facts, "capex")
    assert line.substitute == ("PaymentsToAcquireOtherProductiveAssets",)
    assert max(line.by_period) == date(2024, 12, 31)
    point, stale = current_annual(facts, "capex")
    assert point is None and stale is not None
    assert (stale.period_end, stale.newer_tag, stale.newer_end) == (
        date(2024, 12, 31), "PaymentsToAcquireOtherProductiveAssets", date(2025, 12, 31))
    assert compute_fundamental_snapshot("LNTH", facts).fcf_sign.coverage_status is (
        CoverageStatus.UNKNOWN)


def test_a_missing_year_ends_the_continuation() -> None:
    """DiamondRock: `PaymentsForCapitalImprovements` matched capex at the FY2013 handover
    ($107.307M) and runs FY2014–FY2018, then skips FY2019–FY2021 before reappearing. The line is
    continued only to FY2018, which is years behind, so the FCF sign stays UNKNOWN."""
    facts = _facts("DRH")
    line = annual_line(facts, "capex")
    assert line.substitute == ("PaymentsForCapitalImprovements",)
    assert max(line.by_period) == date(2018, 12, 31)
    assert compute_fundamental_snapshot("DRH", facts).fcf_sign.coverage_status is (
        CoverageStatus.UNKNOWN)


def test_two_accepted_substitutes_that_disagree_are_refused_together() -> None:
    """No filer of the 2,161 cached carries two accepted substitutes for one leg, so this runs on
    Choice Hotels' real file with ONE change: its `PaymentsForCapitalImprovements` rows are made
    to match capex at the FY2019 handover, then to read 10% above the accepted tag afterwards.
    Two readings of one line that disagree are not a reading; both are refused."""
    facts = copy.deepcopy(_facts("CHH"))
    gaap = facts["facts"]["us-gaap"]
    accepted = gaap["PaymentsToAcquireOtherPropertyPlantAndEquipment"]["units"]["USD"]
    gaap["PaymentsForCapitalImprovements"] = {"units": {"USD": [
        {**r, "val": r["val"] if r["end"] <= "2019-12-31" else r["val"] * 1.1} for r in accepted]}}
    assert annual_line(facts, "capex").substitute == ()
    # ⊖ the same second tag reading the SAME figures leaves the accepted one in place
    gaap["PaymentsForCapitalImprovements"] = {"units": {"USD": [dict(r) for r in accepted]}}
    assert annual_line(facts, "capex").substitute == (
        "PaymentsToAcquireOtherPropertyPlantAndEquipment",)


def test_the_tolerance_sits_in_the_measured_gap() -> None:
    """Substitutes against the old line at the handover, legs #821 withholds: 44 within 0.05%,
    nothing from 0.05% to 0.15%, then a continuum (0.15%, 0.40%, … Thor 1.13%, Grocery Outlet
    1.63%). The tolerance sits in that one empty band — set by it, never by outcomes."""
    assert 0.0005 < SUBSTITUTE_TOLERANCE < 0.0015
