"""Capital created or destroyed — goodwill/intangibles remaining, buyback economics, acquisitions.

WHY. SMPL wrote off $391.9M of acquired brand value, borrowed ~$148M, and repurchased 11.65M
shares at an average $18.29 against an $11.33 market. The dossier could show none of it.

THE COVERAGE PROBE IS PART OF THE BUILD, and the first one was wrong in the direction that kills a
build: one tag per concept said "impairment 2/11, acquisition 3/11, SMPL has neither". Reading
SMPL's actual tag list found four impairment tags and a DIRECT average-price tag. Every pin below
runs against the LIVE COMMITTED CORPUS for that reason — a synthetic fixture would have agreed with
the wrong probe.
"""
from __future__ import annotations

import pathlib

import pytest

from vinci.dossier.capital_allocation import (
    ACQUISITION,
    BUYBACK_AVG_PRICE,
    build_capital_allocation,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.network        # reads EDGAR companyfacts (cached)


def _facts(ticker: str) -> dict:
    from vinci.edgar.client import EdgarClient
    from vinci.resolver import EntityResolver
    return EdgarClient.from_config().companyfacts(
        EntityResolver.from_config().resolve_ticker(ticker).cik)


def _names() -> list[str]:
    return sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))


def test_balances_are_read_as_instants_not_annual_flows() -> None:
    """THE BUG THE CORPUS CAUGHT. Goodwill and intangibles are BALANCE-SHEET INSTANTS — SMPL
    reports 83 and 79 of them and ZERO annual durations — so the first cut asked `latest_annual`
    and rendered UNKNOWN on a name carrying a $1.5bn balance. A synthetic fixture built from the
    shape the code expected would have passed."""
    ca = build_capital_allocation(_facts("SMPL"))
    assert ca.goodwill.value and ca.goodwill.value > 500, ca.goodwill.note
    assert ca.intangibles.value and ca.intangibles.value > 900, ca.intangibles.note
    for f in (ca.goodwill, ca.intangibles):
        assert "as at" in (f.source_ref or ""), (
            f"a balance is stamped with a duration span: {f.source_ref}")


def test_smpl_reconciles_with_the_figures_already_on_its_page() -> None:
    """THE RECONCILIATION, against numbers a human already ruled on. `11.65M shares at $18.29` and
    the `$60.9M` intangible charge are on the committed page; if this block disagreed with them one
    of the two would be wrong and a reader could not tell which."""
    ca = build_capital_allocation(_facts("SMPL"))
    assert ca.buyback_shares.value == pytest.approx(11_651_767)
    assert ca.buyback_avg_price.value == pytest.approx(18.29)
    # …and the write-off the page calls "$391.9M LTM" is TWO periods, 60.9 + 331.0
    assert ca.intangible_impairment.value == pytest.approx(331.0, rel=1e-3)


def test_an_acquisition_is_the_largest_positive_never_the_latest_residual() -> None:
    """SIGN AND RECENCY BOTH MATTER, and 'latest' gets both wrong. SMPL carries +280.4 (FY2024) and
    −280.4 (FY2025, restating the SAME period_end), plus a −1.7 residual. Taking the latest annual
    point returned **−1.713** — a negative acquisition price, which is not a thing. Magnitude alone
    would coin-flip between the acquisition and its own reversal."""
    ca = build_capital_allocation(_facts("SMPL"))
    assert ca.acquisition_consideration.value == pytest.approx(280.409, rel=1e-4)
    for t in _names():
        v = build_capital_allocation(_facts(t)).acquisition_consideration.value
        assert v is None or v > 0, f"{t}: negative acquisition consideration {v}"


def test_the_average_price_is_labelled_a_period_average_not_a_purchase_price() -> None:
    """SMPL's $18.29 spans a stock that fell from roughly $30 to $11. Buying at $30 in September
    and $12 in June are OPPOSITE judgements and one number hides both, so the caveat travels ON the
    value — a reader must not take it as evidence of WHEN they bought."""
    ca = build_capital_allocation(_facts("SMPL"))
    note = ca.buyback_avg_price.note or ""
    assert "NOT a purchase price" in note and "timing" in note, note


def test_a_stale_average_is_either_replaced_by_a_current_derivation_or_flagged() -> None:
    """VINTAGE BEATS DIRECTNESS — `_latest_dep_amort`'s rule, same failure. EPAM's own
    average-price tag last reported **Q1 2023** ($283.69, on a stock now near $112) beside **Q1
    2026** repurchase cash. Two outcomes are acceptable and a silent third is not: derive over the
    current period when BOTH legs align there, else keep the stale figure and SAY the periods
    disagree. What must never happen is the two printed side by side as one window."""
    seen = 0
    for t in _names():
        ca = build_capital_allocation(_facts(t))
        avg, cash = ca.buyback_avg_price, ca.buyback_cash
        if avg.value is None or cash.value is None:
            continue
        seen += 1
        derived = str(avg.source_ref).startswith("DERIVED")
        same_window = str(avg.source_ref).split("(")[-1] == str(cash.source_ref).split("(")[-1]
        flagged = "PERIOD MISMATCH" in (avg.note or "")
        assert derived or same_window or flagged, (
            f"{t}: a direct average over a different window than the cash beside it, with nothing "
            f"saying so — avg {avg.source_ref} vs cash {cash.source_ref}")
    assert seen >= 5, f"only {seen} names exercised this — near-vacuous"


def test_every_absence_names_the_tags_that_were_tried() -> None:
    """"Not found" invites nothing; naming the family invites a correction. A reader who knows the
    filer uses a fifth tag can only say so if the four tried are on the page."""
    for t in _names():
        for name, f in build_capital_allocation(_facts(t)):
            if name == "brand_split" or f.value is not None:
                continue
            assert f.note and "EDGAR XBRL companyfacts" in f.note, f"{t}.{name}: {f.note}"
            if name == "acquisition_consideration":
                assert all(tag in f.note for tag in ACQUISITION), f"{t}: {f.note}"


def test_the_brand_split_is_a_stated_gap_on_every_name() -> None:
    """WHAT IS NOT HERE MUST SAY SO. Goodwill separates from intangibles by TAG, but the per-BRAND
    dimension (SMPL's $391.9M across Atkins and OWYN) is footnote prose with no XBRL axis. Left
    silent, the aggregate reads as though the split simply were not interesting."""
    for t in _names():
        bs = build_capital_allocation(_facts(t)).brand_split
        assert bs.value is None and bs.note
        assert "no XBRL axis" in bs.note and "10-K" in bs.note, bs.note


def test_the_derivation_is_refused_rather_than_imputed_from_one_leg() -> None:
    """FAIL LOUD, NEVER FABRICATE. Cash without a share count says nothing about price. An average
    invented from one leg would be a decision figure in the strict sense."""
    cash_only = {"facts": {"us-gaap": {"PaymentsForRepurchaseOfCommonStock": {"units": {"USD": [
        {"start": "2025-01-01", "end": "2025-12-31", "val": 1e8, "filed": "2026-01-15",
         "fy": 2025, "fp": "FY", "form": "10-K", "accn": "x"}]}}}}}
    ca = build_capital_allocation(cash_only)
    assert ca.buyback_cash.value == pytest.approx(100.0)
    assert ca.buyback_avg_price.value is None
    assert "imputed" in (ca.buyback_avg_price.note or "")


def test_an_empty_facts_dict_yields_a_fully_stated_block_not_a_crash() -> None:
    """TOTAL ON ITS INPUT. The assembler passes `{}` when companyfacts is unavailable, so every
    field must degrade to UNKNOWN-with-reason rather than raising into the build."""
    ca = build_capital_allocation({})
    for name, f in ca:
        assert f.value is None and f.note, name
    assert BUYBACK_AVG_PRICE[0] in (ca.buyback_avg_price.note or "")
