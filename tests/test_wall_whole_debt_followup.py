"""The #956 follow-up (TeamNostra fix request 2): a ≤12-month wall #956's whole-debt gate refused
on Werner's Q3, and a whole-debt form no version read on Microvast's Q3. Found by the impact sweep
of 2026-11-12 and checked against each filing's own words (coordinator, operator: "Accept, verify
the values (Recommended)").

Every excerpt is the filing's own text, cut at sentence edges and joined where marked [cut].
"""
from __future__ import annotations

from vinci.edgar.filing_sections import _balance_sheet_debt, _maturity_wall

# --- Werner (WERN), 10-Q 0000793074-26-000172, verbatim: the balance sheet's heading and its
# liabilities, then the two debt sentences [cut] -------------------------------------------------
_WERN_HEAD = ("CONSOLIDATED CONDENSED BALANCE SHEETS (In thousands, except share amounts) "
              "September 30, 2026 December 31, 2025 (Unaudited)")
_WERN_LIAB = ("Current liabilities: Accounts payable $ 129,053 $ 95,084 Insurance and claims "
              "accruals 114,676 99,827 Accrued payroll 77,834 51,442 Accrued expenses 18,908 "
              "16,199 Current maturities of finance lease liabilities 24,574 — Current maturities "
              "of operating lease liabilities 51,703 15,451 Other current liabilities 74,089 "
              "36,781 Total current liabilities 490,837 314,784 Long-term debt, net of current "
              "portion 803,000 752,000 Finance lease liabilities, less current maturities 19,779 "
              "— Operating lease liabilities, less current maturities 95,742 26,470 Other "
              "long-term liabilities 20,828 26,080 Insurance and claims accruals, net of current "
              "portion 138,316 112,126 Deferred income taxes 278,317 266,209 Total liabilities "
              "1,846,819 1,497,669")
_WERN_TOTAL = ("We had net borrowings on our debt under our Credit Facilities of $51.0 million "
               "during the nine months ended September 30, 2026, increasing our outstanding debt "
               "under our Credit Facilities to $803.0 million at September 30, 2026.")
_WERN_DUE = ("Debt Obligations and Interest Payments – As of September 30, 2026, we had "
             "outstanding debt under the Credit Facilities with an aggregate principal amount of "
             "$803.0 million, with no principal amount expected to be paid within 12 months.")
_WERN_Q3 = " ".join([_WERN_HEAD, _WERN_LIAB, _WERN_TOTAL, _WERN_DUE])


def test_wern_q3_the_balance_sheet_total_makes_the_credit_facilities_the_whole_debt() -> None:
    """(+) THE RED, on main: not_stated, "$0.0M due ≤12m is stated for part of it only". The prose
    total is qualified ("under our Credit Facilities"), but the balance sheet's only debt row is
    "Long-term debt, net of current portion 803,000" (thousands), with the current maturities it
    lists all leases, which are not debt (#956). So $803.0M is the whole debt and its $0 is the
    company's wall."""
    w = _maturity_wall(_WERN_Q3, "10-Q 0000793074-26-000172")
    assert w is not None and w.state == "located", (w.state if w else None, w.note if w else None)
    assert w.within_12m_total == 0.0
    assert _balance_sheet_debt(_WERN_Q3) == (("September", "30", "2026"), 803.0)


def test_wern_neg_another_borrowing_row_reads_no_balance_sheet_total() -> None:
    """(-) CONSTRUCTED from the same balance sheet: with any other borrowing row the two debt rows
    are not the whole debt, so no total is read and the wall stays refused as part of the debt."""
    liab = _WERN_LIAB.replace("Accrued expenses", "Short-term borrowings 50,000 — Accrued expenses")
    text = " ".join([_WERN_HEAD, liab, _WERN_TOTAL, _WERN_DUE])
    assert _balance_sheet_debt(text) is None
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "not_stated" and "part of it only" in w.note


def test_wern_neg_a_total_at_another_date_covers_nothing() -> None:
    """(-) CONSTRUCTED: a balance-sheet total whose own column is another date (the prior year
    end) is not the instrument's date, as #956's round-1 rule already holds for a prose total."""
    head = _WERN_HEAD.replace("September 30, 2026 December 31, 2025", "December 31, 2025")
    w = _maturity_wall(" ".join([head, _WERN_LIAB, _WERN_TOTAL, _WERN_DUE]), "10-Q x")
    assert w is not None and w.state == "not_stated"


# --- review round 0 (B, adopting A's draft): the guard reads every borrowing row, whatever its
# label, and the long-term row is never read inside the current-portion row ------------------------

def _wern_with(row: str, *, long_term: str = "803,000") -> str:
    """Werner's real balance sheet with one row put in before "Accrued expenses" (CONSTRUCTED:
    the row only), and its long-term debt row's first column set to ``long_term``."""
    liab = _WERN_LIAB.replace("Accrued expenses", f"{row} Accrued expenses").replace(
        "Long-term debt, net of current portion 803,000", f"Long-term debt, net of current "
        f"portion {long_term}")
    return " ".join([_WERN_HEAD, liab, _WERN_TOTAL, _WERN_DUE])


def test_wern_neg_a_borrowing_row_under_any_label_reads_no_total() -> None:
    """(-) A borrowing row whose label runs on before its figure is still another borrowing: with
    "Revolving credit facility 50,000" (or a current notes-payable row, or a current row combining
    debt and leases) the long-term row is not the whole debt. On A's draft each read 803.0 and a
    located $0.0 wall beside $50M of other debt."""
    for row in ("Revolving credit facility 50,000 —", "Notes payable, current 50,000 —",
                "Current maturities of long-term debt and finance lease obligations 50,000 —"):
        text = _wern_with(row)
        assert _balance_sheet_debt(text) is None, row
        w = _maturity_wall(text, "10-Q x")
        assert w is not None and w.state == "not_stated", (row, w.state if w else None)


def test_wern_a_current_portion_is_summed_not_read_as_the_long_term_row() -> None:
    """(+) Long-term debt 793,000 and its current portion 10,000 are $803.0M, the facilities'
    principal: the whole debt, and the wall is located. The current row comes FIRST on a balance
    sheet, and A's draft read "long-term debt 10,000" inside it as the long-term row — 20.0."""
    text = _wern_with("Current portion of long-term debt 10,000 —", long_term="793,000")
    assert _balance_sheet_debt(text) == (("September", "30", "2026"), 803.0)
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "located" and w.within_12m_total == 0.0


def test_wern_an_asset_row_is_not_a_borrowing() -> None:
    """(-) for the guard: the body read is the LIABILITIES, so an asset's "Notes receivable" is
    no other borrowing and the total still reads."""
    head = _WERN_HEAD + " Current assets: Cash and cash equivalents $ 61,047 $ 51,036 Notes " \
        "receivable 4,512 3,980 Total current assets 650,331 540,118"
    text = " ".join([head, _WERN_LIAB, _WERN_TOTAL, _WERN_DUE])
    assert _balance_sheet_debt(text) == (("September", "30", "2026"), 803.0)


# --- Microvast (MVST), 10-Q 0001628280-26-072316, verbatim: two sentences [cut] ------------------
_MVST_BORROWINGS = ("As of September 30, 2026, our bank borrowings were $135.3 million, our "
                    "bonds payable were $41.7 million and $120.8 million of our borrowings were "
                    "due within the next 12 months.")
_MVST_CAPITAL = ("Additionally, as of September 30, 2026, the Company had $ 34.7 million in "
                 "purchase commitments primarily related to inventory, and $ 6.5 million in "
                 "capital commitments with $ 5.6 million due within the next 12 months.")


def test_mvst_q3_of_our_borrowings_due_within_12_months_is_the_wall() -> None:
    """(+) THE RED, on main: not_stated, no form read "$120.8 million of our borrowings were due
    within the next 12 months". The clause before the figure lists the parts; "of our
    borrowings" makes the figure the whole's."""
    w = _maturity_wall(" ".join([_MVST_CAPITAL, _MVST_BORROWINGS]), "10-Q 0001628280-26-072316")
    assert w is not None and w.state == "located", (w.state if w else None, w.note if w else None)
    assert w.within_12m_total == 120.8


def test_mvst_neg_a_capital_commitment_is_never_the_wall() -> None:
    """(-) The same filing's "$6.5 million in capital commitments with $5.6 million due within the
    next 12 months" is a commitment, not debt (#956): alone it reads no wall, and beside the
    borrowings sentence the wall is the borrowings' $120.8M, never $5.6M."""
    alone = _maturity_wall(_MVST_CAPITAL, "10-Q x")
    assert alone is None or alone.state != "located", (alone.state, alone.within_12m_total)
    both = _maturity_wall(" ".join([_MVST_BORROWINGS, _MVST_CAPITAL]), "10-Q x")
    assert both is not None and both.within_12m_total == 120.8
