"""The buyback average is the filer's own figure or nothing — never cash-paid ÷ shares-acquired.

THE DEFECT (BRBR, found by underwriting it). `buyback_avg_price` read **$28.23** from
`PaymentsForRepurchaseOfCommonStock` ÷ `TreasuryStockSharesAcquired`, both over an identical
272-day window. Every period check passed and the quotient was still not a price: the $137.2M is a
CASH-FLOW line — cash actually PAID in the window — so it includes $3.9M of PRIOR-YEAR excise tax
settled there and excludes $1.2M accrued but unpaid. The filer's own figure for the same nine
months is **$27.41 on $134.5M**.

AND IT CANNOT BE REPAIRED BY FIXING ONE LEG. $134.5M ÷ 4.86M is **$27.67**, not $27.41, because the
company's implied share count is **4.907M** against the tag's 4.86M. BOTH legs sit on a different
basis from the filer's own measure, so no arithmetic over these two tags reproduces it. A figure
nobody can reproduce is worse than an absence — the absence is at least true, while this one
carried a `DERIVED:` `source_ref` that made it look computed-and-checked.

THE GUARD SHAPE THIS RECORDS. The existing check proves the two legs share a **WINDOW**. Nothing
proved they share a **BASIS**, and same-window/different-basis is invisible to a period comparison
— which is why the derivation is refused outright rather than given a tighter period test.

OFFLINE BY CONSTRUCTION. `test_capital_allocation.py` is `pytest.mark.network` at module scope, so
CI never runs it; pins that live only there cannot gate anything (#367). These build companyfacts
in the REAL EDGAR shape (`facts` → namespace → tag → `units` → rows) that `points_for_tag` parses.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest

from vinci.dossier.capital_allocation import build_capital_allocation
from vinci.dossier.schemas import SourceStatus

CASH = "PaymentsForRepurchaseOfCommonStock"
SHARES = "TreasuryStockSharesAcquired"
DIRECT = "TreasuryStockAcquiredAverageCostPerShare"

START, END = date(2025, 10, 1), date(2026, 6, 30)      # BRBR's real 272-day window


def _flow(val: float, *, start: date = START, end: date = END) -> dict[str, Any]:
    return {"start": str(start), "end": str(end), "val": val,
            "filed": str(end + timedelta(days=30)), "fy": end.year, "fp": "Q3",
            "form": "10-Q", "accn": "x"}


def _facts(**tags: list[dict[str, Any]]) -> dict[str, Any]:
    return {"facts": {"us-gaap": {t: {"units": {"USD": rows}} for t, rows in tags.items()}}}


def test_a_cash_flow_line_over_a_share_count_is_refused_however_well_the_periods_match() -> None:
    """BRBR'S EXACT SHAPE — $137.2M and 4.86M shares on one identical 272-day window. The period
    guard has nothing to complain about, and the answer is still a refusal, because the objection
    is to the BASES and not to the windows."""
    ca = build_capital_allocation(_facts(**{CASH: [_flow(137.2e6)], SHARES: [_flow(4_860_000.0)]}))
    assert ca.buyback_avg_price.status is SourceStatus.UNKNOWN, (
        f"derived a price of {ca.buyback_avg_price.value} from a cash-flow line ÷ a share count")
    assert ca.buyback_avg_price.value is None
    note = ca.buyback_avg_price.note or ""
    assert "CASH-FLOW payment line" in note and "not one BASIS" in note, note
    assert "refused rather than derived" in note


def test_the_two_legs_themselves_survive_because_each_is_sound_on_its_own_basis() -> None:
    """THE NEGATIVE HALF, and it matters: refusing the QUOTIENT must not delete the inputs. The
    repurchase cash and the share count are each a real, correctly-sourced fact — it is only their
    ratio that is not a price. Deleting them would answer the capital-allocation question with
    less than the filer actually reports."""
    ca = build_capital_allocation(_facts(**{CASH: [_flow(137.2e6)], SHARES: [_flow(4_860_000.0)]}))
    assert ca.buyback_cash.value == pytest.approx(137.2)
    assert ca.buyback_shares.value == pytest.approx(4_860_000.0)
    assert ca.buyback_cash.status is SourceStatus.PRESENT
    assert ca.buyback_shares.status is SourceStatus.PRESENT


def test_the_filers_own_purchase_cost_tag_is_still_printed_where_it_exists() -> None:
    """EPAM ($283.69) and SMPL ($18.29) keep theirs. The tag is a purchase-COST measure — the right
    one — and the ruling was to print it where it exists and state absence where it does not, never
    to drop the field wholesale."""
    ca = build_capital_allocation(_facts(**{
        DIRECT: [_flow(18.29)], CASH: [_flow(213.2e6)], SHARES: [_flow(11_651_767.0)]}))
    assert ca.buyback_avg_price.status is SourceStatus.PRESENT
    assert ca.buyback_avg_price.value == pytest.approx(18.29)
    assert DIRECT in str(ca.buyback_avg_price.source_ref)
    assert "NOT a purchase price" in (ca.buyback_avg_price.note or ""), (
        "the period-average caveat must still travel on the filer's own figure")


def test_no_average_anywhere_is_a_derived_quotient_of_the_two_legs() -> None:
    """THE CLASS PIN, not the instance. Whatever the inputs, the field must never again carry a
    `DERIVED:` ref built from the cash line and the share count — that is the shape that produced a
    number nobody could reproduce, on 2 of the 4 names that carried the field (BRBR, IT)."""
    for tags in (
        {CASH: [_flow(137.2e6)], SHARES: [_flow(4_860_000.0)]},          # both legs, one window
        {CASH: [_flow(137.2e6)], SHARES: [_flow(4_860_000.0, end=date(2026, 3, 31))]},  # mismatched
        {CASH: [_flow(137.2e6)]},                                        # cash only
        {SHARES: [_flow(4_860_000.0)]},                                  # shares only
    ):
        ref = str(build_capital_allocation(_facts(**tags)).buyback_avg_price.source_ref or "")
        assert not ref.startswith("DERIVED"), ref


def test_an_absence_still_names_what_was_tried() -> None:
    """The house rule for every absence in this module: "not found" invites nothing, naming the tag
    invites a correction from a reader who knows the filer uses a fifth one."""
    ca = build_capital_allocation(_facts(**{CASH: [_flow(137.2e6)], SHARES: [_flow(4_860_000.0)]}))
    assert DIRECT in (ca.buyback_avg_price.note or "")
