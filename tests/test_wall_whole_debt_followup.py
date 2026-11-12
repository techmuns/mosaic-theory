"""The #956 follow-up (TeamNostra fix request 2): a ≤12-month wall #956's whole-debt gate refused
on Werner's Q3, and a whole-debt form no version read on Microvast's Q3. Found by the impact sweep
of 2026-11-12 and checked against each filing's own words (coordinator, operator: "Accept, verify
the values (Recommended)").

Review round 1 (A's independent review of #1039, 2026-11-12) dropped the Microvast read — its
$120.8M counts the bank borrowings only — and narrowed the balance-sheet read; its pins are below.

Every excerpt is the filing's own text, cut at sentence edges and joined where marked [cut].
"""
from __future__ import annotations

from vinci.dossier.schemas import MaturityWall
from vinci.edgar.filing_sections import _balance_sheet_debt, _maturity_wall


def _k(w: MaturityWall | None) -> tuple[str, float | None] | None:
    """A wall's (state, ≤12m figure), for an assertion's message."""
    return None if w is None else (w.state, w.within_12m_total)

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
    assert tuple(_balance_sheet_debt(_WERN_Q3) or ())[:2] == (("September", "30", "2026"), 803.0)


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

#: The sentence Werner's statements end with (verbatim) — so a sentence after the sheet is read as
#: a sentence, never run back into the sheet's lease rows.
_WERN_END = "See Notes to Consolidated Financial Statements (Unaudited)."


def _wern_bs(row: str = "", *, long_term: str = "803,000") -> str:
    """Werner's real balance sheet with one row put in before "Accrued expenses" (CONSTRUCTED:
    the row only), and its long-term debt row's first column set to ``long_term``."""
    liab = _WERN_LIAB.replace("Accrued expenses", f"{row} Accrued expenses" if row else
                              "Accrued expenses").replace(
        "Long-term debt, net of current portion 803,000", f"Long-term debt, net of current "
        f"portion {long_term}")
    return " ".join([_WERN_HEAD, liab, _WERN_END])


#: Werner's ≤12m sentence with a $10.0M figure for its $803.0M (CONSTRUCTED: the figure only).
_WERN_DUE_10 = _WERN_DUE.replace("with no principal amount expected to be paid within 12 months",
                                 "of which $10.0 million is due within the next 12 months")


def _wern_with(row: str, *, long_term: str = "803,000", due: str = _WERN_DUE) -> str:
    """`_wern_bs` with Werner's two debt sentences after it (the ≤12m one ``due``)."""
    return " ".join([_wern_bs(row, long_term=long_term), _WERN_TOTAL, due])


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
    sheet, and A's draft read "long-term debt 10,000" inside it as the long-term row — 20.0.
    (Round 1: the facilities' stated ≤12m figure is now the current portion's $10.0M, CONSTRUCTED;
    round 0 pinned a located $0.0 beside it, which round 1 refuses: below.)"""
    text = _wern_with("Current portion of long-term debt 10,000 —", long_term="793,000",
                      due=_WERN_DUE_10)
    assert tuple(_balance_sheet_debt(text) or ())[:2] == (("September", "30", "2026"), 803.0)
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "located" and w.within_12m_total == 10.0
    # (+) for round 1's folded-portion guard: a debt note that subtracts the current portion the
    # sheet DOES list is no portion folded elsewhere (CONSTRUCTED: the note's line)
    noted = text + " Less: current portion of long-term debt ( 10,000 ) — Long-term debt 793,000"
    assert _balance_sheet_debt(noted) == (_WERN_DATE, 803.0, 10.0)


def test_wern_an_asset_row_is_not_a_borrowing() -> None:
    """(-) for the guard: the body read is the LIABILITIES, so an asset's "Notes receivable" is
    no other borrowing and the total still reads."""
    head = _WERN_HEAD + " Current assets: Cash and cash equivalents $ 61,047 $ 51,036 Notes " \
        "receivable 4,512 3,980 Total current assets 650,331 540,118"
    text = " ".join([head, _WERN_LIAB, _WERN_TOTAL, _WERN_DUE])
    assert tuple(_balance_sheet_debt(text) or ())[:2] == (("September", "30", "2026"), 803.0)


# --- Microvast (MVST), 10-Q 0001628280-26-072316, verbatim: the balance sheet's heading and its
# liabilities, the liquidity sentence and two more sentences [cut] -------------------------------
_MVST_HEAD = ("CONSOLIDATED BALANCE SHEETS (In thousands, except per share data, unaudited) "
              "September 30, 2026 December 31, 2025")
_MVST_LIAB = ("Liabilities Accounts payable $ 48,473 $ 47,003 Notes payable 33,470 78,321 Accrued "
              "expenses and other current liabilities 106,712 123,429 Advance from customers "
              "4,492 5,605 Amounts due to related parties 212 2 Convertible loan measured at fair "
              "value — 140,929 Short-term bank borrowings 120,794 93,052 Bonds payable 41,693 — "
              "Total Current Liabilities 355,846 488,341 Long-term bonds payable — 41,693 "
              "Long-term bank borrowings 14,468 13,227 Operating lease liabilities 13,475 14,476 "
              "Other non-current liabilities 36,290 37,198 Total Liabilities $ 420,079 $ 594,935")
_MVST_CURRENT = ("Current bank borrowings, notes payable and current bonds payable totaled "
                 "approximately $ 196.0 million.")
_MVST_BORROWINGS = ("As of September 30, 2026, our bank borrowings were $135.3 million, our "
                    "bonds payable were $41.7 million and $120.8 million of our borrowings were "
                    "due within the next 12 months.")
_MVST_CAPITAL = ("Additionally, as of September 30, 2026, the Company had $ 34.7 million in "
                 "purchase commitments primarily related to inventory, and $ 6.5 million in "
                 "capital commitments with $ 5.6 million due within the next 12 months.")


_MVST_Q3 = " ".join([_MVST_HEAD, _MVST_LIAB, _MVST_CURRENT, _MVST_CAPITAL, _MVST_BORROWINGS])


def test_mvst_q3_of_our_borrowings_is_the_bank_borrowings_only_and_not_the_wall() -> None:
    """(-) ROUND 1, THE RED on the PR's head `f8117cd7` (located $120.8M): "$120.8 million of our
    borrowings were due within the next 12 months" is the balance sheet's "Short-term bank
    borrowings 120,794" alone. Beside it sit current "Notes payable 33,470" and "Bonds payable
    41,693", and the filing's own total of them is "$ 196.0 million". Part of the debt is never
    the wall (#956), so Microvast's Q3 reads not_stated, as main reads it."""
    w = _maturity_wall(_MVST_Q3, "10-Q 0001628280-26-072316")
    assert w is not None and w.state == "not_stated", _k(w)
    assert w.within_12m_total is None
    assert _balance_sheet_debt(_MVST_Q3) is None  # no long-term debt row; other borrowings


def test_mvst_neg_of_our_borrowings_after_another_subject_is_not_the_wall() -> None:
    """(-) ROUND 1, CONSTRUCTED from Microvast's sentence: "of its/our borrowings" says nothing
    about whose, or which, borrowings — a joint venture's, or one term loan's beside $500M of
    notes. The PR's head read each as the company's wall."""
    jv = ("As of September 30, 2026, our joint venture's bank borrowings were $135.3 million, and "
          "$120.8 million of its borrowings were due within the next 12 months. Our 5.0% senior "
          "notes of $500.0 million mature in 2027.")
    tl = ("Under the Term Loan, $45.0 million of our borrowings are due within the next 12 months. "
          "We also have $500.0 million of 5.0% senior notes due 2027.")
    for text in (jv, tl):
        w = _maturity_wall(text, "10-Q x")
        assert w is not None and w.state != "located", (text[:40], _k(w))


def test_mvst_neg_a_capital_commitment_is_never_the_wall() -> None:
    """(-) The same filing's "$6.5 million in capital commitments with $5.6 million due within the
    next 12 months" is a commitment, not debt (#956): alone it reads no wall, and beside the
    borrowings sentence no wall either (round 1: never $5.6M, and never the bank borrowings'
    $120.8M)."""
    alone = _maturity_wall(_MVST_CAPITAL, "10-Q x")
    assert alone is None or alone.state != "located", _k(alone)
    both = _maturity_wall(" ".join([_MVST_BORROWINGS, _MVST_CAPITAL]), "10-Q x")
    assert both is not None and both.state != "located", _k(both)


# --- review round 1 (A's independent review of #1039): the balance-sheet route holds what the prose
# route holds, the figure must BE the balance sheet's current portion, and the guard reads every
# borrowing row of the real layouts ----------------------------------------------------------------
_WERN_DATE = ("September", "30", "2026")


def test_bs_neg_a_total_inside_the_clause_covers_nothing() -> None:
    """(-) #956's pinned in-clause total ("our total debt was $500.0 million, and of the term loan,
    $45.0 million …") beside a balance sheet of $500.0M: the clause's last figure is a TOTAL, so
    the term loan's own principal is unstated and nothing shows it is the whole debt. The PR's
    head read located $45.0 — beside a $60.0M current portion, and even where the current portion
    happens to equal the figure (the second sheet). CONSTRUCTED: the rows' figures."""
    clause = ("As of September 30, 2026, our total debt was $500.0 million, and of the term loan, "
              "$45.0 million is due within one year.")
    for cur, lt in (("60,000", "440,000"), ("45,000", "455,000")):
        text = " ".join([_wern_bs(f"Current portion of long-term debt {cur} —", long_term=lt),
                         clause])
        assert tuple(_balance_sheet_debt(text) or ())[:2] == (_WERN_DATE, 500.0), cur
        w = _maturity_wall(text, "10-Q x")
        assert w is not None and w.state == "not_stated", (cur, _k(w))


def test_bs_neg_an_undrawn_facilitys_size_is_not_its_principal() -> None:
    """(-) "no borrowings outstanding under our $500.0 million Revolving Credit Facility, and no
    principal amounts are due within the next 12 months", beside a balance sheet whose $500.0M is
    ALL current: the revolver's size equals the debt, so the PR's head read a located $0.0 wall
    beside $500.0M due within the year. A whole debt's ≤12m principal is its current portion, and
    $0.0 is not 500.0. CONSTRUCTED: the sentence and the rows' figures."""
    undrawn = ("As of September 30, 2026, we had no borrowings outstanding under our $500.0 "
               "million Revolving Credit Facility, and no principal amounts are due within the "
               "next 12 months.")
    text = " ".join([_wern_bs("Current portion of long-term debt 500,000 —", long_term="—"),
                     undrawn])
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "not_stated", _k(w)
    assert _balance_sheet_debt(text) == (_WERN_DATE, 500.0, 500.0)


def test_bs_neg_a_zero_beside_a_current_portion_is_not_the_wall() -> None:
    """(-) Werner's real ≤12m sentence ("with no principal amount expected to be paid within 12
    months") beside a balance sheet that lists a $10.0M current portion of the same $803.0M: the
    PR's head read a located $0.0 — round 0 pinned it — beside $10.0M the sheet says is due
    within the year. The figure must be the sheet's current portion, or no wall is read; with a
    $10.0M figure it is (`test_wern_a_current_portion_is_summed_not_read_as_the_long_term_row`).
    CONSTRUCTED: the row."""
    text = _wern_with("Current portion of long-term debt 10,000 —", long_term="793,000")
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "not_stated", _k(w)
    assert _balance_sheet_debt(text) == (_WERN_DATE, 803.0, 10.0)


def test_bs_neg_every_borrowing_label_refuses_the_total() -> None:
    """(-) Werner's real balance sheet with ONE more borrowing row (CONSTRUCTED: the row only),
    under the singular and the common labels the round-0 guard did not read: each read 803.0 and
    a located $0.0 beside $50.0M of other debt on the PR's head."""
    for row in ("Note payable, current 50,000 —", "Convertible note payable 50,000 —",
                "Bond payable 50,000 —", "Debenture payable 50,000 —",
                "Mortgage payable 50,000 —", "Financing obligations 50,000 —",
                "Current portion of financing obligation 50,000 —",
                "Receivables securitization facility 50,000 —", "Floor plan payable 50,000 —",
                "Current maturities of long-term obligations 50,000 —",
                "Bank overdraft 50,000 —", "Credit agreement 50,000 —"):
        text = _wern_with(row)
        assert _balance_sheet_debt(text) is None, row
        w = _maturity_wall(text, "10-Q x")
        assert w is not None and w.state == "not_stated", (row, w.state if w else None)


# Uber (UBER), 10-Q for 2026-09-30, verbatim: the balance sheet's heading, its total assets and its
# liabilities [cut]. It has no "Current liabilities" heading: its first "current liabilities" is
# the ROW "Accrued and other current liabilities", below its other current rows.
_UBER_HEAD = ("CONDENSED CONSOLIDATED BALANCE SHEETS (In millions, except share amounts which are "
              "reflected in thousands, and per share amounts) (Unaudited) As of December 31, 2025 "
              "As of September 30, 2026")
_UBER_LIAB = ("Total assets $ 61,802 $ 71,067 Liabilities, redeemable non-controlling interests "
              "and equity Accounts payable $ 1,013 $ 1,479 Short-term insurance reserves 3,387 "
              "4,220 Operating lease liabilities, current 169 176 Accrued and other current "
              "liabilities 7,751 8,631 Total current liabilities 12,320 14,506 Long-term insurance "
              "reserves 9,076 9,489 Long-term debt, net of current portion 10,521 15,664 Operating "
              "lease liabilities, non-current 1,390 1,897 Other non-current liabilities 412 548 "
              "Total liabilities 33,719 42,104")
_UBER_END = ("The accompanying notes are an integral part of these condensed consolidated "
             "financial statements.")
#: Werner's ≤12m sentence at Uber's column date and long-term figure (CONSTRUCTED).
_UBER_DUE = ("As of December 31, 2025, we had outstanding debt under the Credit Facilities with "
             "an aggregate principal amount of $10,521.0 million, with no principal amount "
             "expected to be paid within 12 months.")


def test_bs_a_note_cross_reference_is_no_note_payable() -> None:
    """(+) Round 1 reads a singular "Note payable" as a borrowing; a row's "(Note 5)"
    cross-reference is not one, so Werner's sheet with one still reads its total. CONSTRUCTED: the
    cross-reference."""
    text = _WERN_Q3.replace("Accrued expenses 18,908", "Accrued expenses (Note 5) 18,908")
    assert _balance_sheet_debt(text) == (_WERN_DATE, 803.0, 0.0)
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "located" and w.within_12m_total == 0.0


def test_bs_neg_principal_and_interest_is_never_the_current_portion() -> None:
    """(-) A principal-AND-interest figure is another basis from the sheet's current portion of
    principal (`MaturityWall.basis`), so it is never matched against it, even where the two
    figures happen to agree. CONSTRUCTED: the sentence and the rows' figures."""
    pni = ("As of September 30, 2026, we had $803.0 million of senior notes outstanding, and the "
           "amount of principal and interest on our senior notes due in the next twelve months is "
           "$40.0 million.")
    text = " ".join([_wern_bs("Current portion of long-term debt 40,000 —", long_term="763,000"),
                     pni])
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "not_stated", _k(w)
    assert _balance_sheet_debt(text) == (_WERN_DATE, 803.0, 40.0)


def test_bs_neg_a_row_above_a_current_liabilities_row_is_read() -> None:
    """(-) The body is read from the liabilities' HEADING: on Uber's layout the round-0 anchor
    landed on the row "Accrued and other current liabilities" and skipped every row above it, so
    a "Short-term borrowings" row there (CONSTRUCTED) read 10,521 and a located $0.0 on the PR's
    head. (+) control: the same layout without that row reads its rows."""
    plain = " ".join([_UBER_HEAD, _UBER_LIAB, _UBER_END, _UBER_DUE])
    assert tuple(_balance_sheet_debt(plain) or ())[:2] == (("December", "31", "2025"), 10521.0)
    text = plain.replace("Short-term insurance",
                         "Short-term borrowings 2,000 — Short-term insurance")
    assert _balance_sheet_debt(text) is None
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "not_stated", _k(w)


def test_bs_neg_a_current_portion_folded_into_another_row_reads_no_total() -> None:
    """(-) REAL TEXT, verbatim [cut]: Amazon's Q3 10-Q and Alphabet's Q2 keep their current portion
    of long-term debt inside "Accrued expenses and other…" — Alphabet's note says so — and list
    only "Long-term debt" on the balance sheet. Their debt notes subtract it ("Less: current
    portion of long-term debt ( 2,748 )", "… of long-term notes (3) ( 1,996 )"). The PR's head
    read the long-term rows, 65,648 and 46,547, as the whole debt; neither is."""
    amzn = " ".join([
        "CONSOLIDATED BALANCE SHEETS (in millions, except per share data) December 31, 2025 "
        "September 30, 2026 (unaudited)",
        "Total assets $ 818,042 $ 1,243,390 LIABILITIES AND STOCKHOLDERS’ EQUITY Current "
        "liabilities: Accounts payable $ 121,909 $ 158,715 Accrued expenses and other 75,520 "
        "77,559 Unearned revenue 20,576 21,708 Total current liabilities 218,005 257,982 Long-term "
        "lease liabilities 87,339 98,824 Long-term debt 65,648 173,125 Other long-term liabilities "
        "35,985 99,858 Commitments and contingencies (Note 4) Stockholders’ equity: Preferred "
        "stock ($ 0.01 par value; 500 shares authorized; no shares issued or outstanding) — — "
        "Common stock ($ 0.01 par value; 100,000 shares authorized; 11,246 and 11,326 shares "
        "issued; 10,731 and 10,811 shares outstanding) 112 113 Treasury stock, at cost ( 7,837 ) "
        "( 7,837 ) Additional paid-in capital 140,024 154,924 Accumulated other comprehensive "
        "income (loss) 28,230 102,278 Retained earnings 250,536 364,123 Total stockholders’ equity "
        "411,065 613,601 Total liabilities and stockholders’ equity $ 818,042 $ 1,243,390 See "
        "accompanying notes to consolidated financial statements.",
        "Total face value of long-term debt 68,836 180,887 Unamortized discount and issuance "
        "costs, net ( 440 ) ( 935 ) Less: current portion of long-term debt ( 2,748 ) ( 6,827 ) "
        "Long-term debt $ 65,648 $ 173,125"])
    goog = " ".join([
        "CONSOLIDATED BALANCE SHEETS (in millions, except per share amounts) As of December 31, "
        "2025 As of June 30, 2026 (unaudited)",
        "Total assets $ 595,281 $ 921,983 Liabilities and Stockholders’ Equity Current "
        "liabilities: Accounts payable $ 12,200 $ 20,258 Accrued compensation and benefits 17,546 "
        "15,086 Accrued expenses and other current liabilities 55,557 73,014 Accrued revenue share "
        "10,864 10,599 Deferred revenue 6,578 7,154 Total current liabilities 102,745 126,111 "
        "Long-term debt 46,547 98,165 Income taxes payable, non-current 9,531 11,306 Deferred "
        "income taxes 919 22,819 Operating lease liabilities 12,744 14,591 Other long-term "
        "liabilities 7,530 8,511 Total liabilities 180,016 281,503",
        "Total face value of long-term debt 49,085 101,085 Unamortized discount and debt issuance "
        "costs (2) ( 542 ) ( 921 ) Less: current portion of long-term notes (3) ( 1,996 ) "
        "( 1,999 ) Total long-term debt $ 46,547 $ 98,165",
        "(3) Total current portion of long-term debt is included within accrued expenses and "
        "other current liabilities."])
    failures = {n: _balance_sheet_debt(t) for n, t in (("AMZN", amzn), ("GOOG", goog))}
    assert failures == {"AMZN": None, "GOOG": None}


def _millions_bs(long_term: str) -> str:
    """A balance sheet stated in millions (CONSTRUCTED)."""
    return ("CONDENSED CONSOLIDATED BALANCE SHEETS (In millions) September 30, 2026 December 31, "
            "2025 Current liabilities: Accounts payable 10.0 9.0 Total current liabilities 70.0 "
            f"9.0 Long-term debt, net of current portion {long_term} 400.0 Total liabilities 600.0 "
            "500.0 See accompanying notes.")


def test_bs_a_millions_cell_keeps_its_decimal() -> None:
    """(-) "802.6" in a millions table is $802.6M, never 802: the PR's head read it as the whole
    debt of an $802.0M facility, a located $0.0. (+) the facility of $802.6M is the whole debt.
    CONSTRUCTED: the sheet, and Werner's sentence at each figure."""
    def due(principal: str) -> str:
        return _WERN_DUE.replace("$803.0 million", f"${principal} million")
    w = _maturity_wall(" ".join([_millions_bs("802.6"), due("802.0")]), "10-Q x")
    assert w is not None and w.state == "not_stated", _k(w)
    assert _balance_sheet_debt(_millions_bs("802.6")) == (_WERN_DATE, 802.6, 0.0)
    w = _maturity_wall(" ".join([_millions_bs("802.6"), due("802.6")]), "10-Q x")
    assert w is not None and w.state == "located" and w.within_12m_total == 0.0


def test_bs_neg_an_undated_statement_covers_nothing() -> None:
    """(-) "Of the $500.0 million outstanding under the Revolving Credit Facility, $25.0 million is
    due within one year" states no date, so it is not the balance sheet's: the prose route
    already refuses a dated total for an undated statement, and the PR's head read this one
    located $25.0. (+) the same statement at the sheet's date is the whole debt's. CONSTRUCTED."""
    bs = _wern_bs("Current portion of long-term debt 25,000 —", long_term="475,000")
    undated = ("Of the $500.0 million outstanding under the Revolving Credit Facility, $25.0 "
               "million is due within one year.")
    w = _maturity_wall(" ".join([bs, undated]), "10-Q x")
    assert w is not None and w.state == "not_stated", _k(w)
    w = _maturity_wall(" ".join([bs, "As of September 30, 2026, o" + undated[1:]]), "10-Q x")
    assert w is not None and w.state == "located" and w.within_12m_total == 25.0


def test_neg_a_total_inside_the_clause_repeated_elsewhere_covers_nothing() -> None:
    """(-) The in-clause total ("our total debt was $500.0 million, and of the term loan, $45.0
    million …") repeated by another sentence at the same date: the prose route matched the
    clause's in-clause total to the repeat and read located $45.0 for the term loan alone. The
    in-clause check now runs before both routes. CONSTRUCTED: both sentences."""
    clause = ("As of September 30, 2026, our total debt was $500.0 million, and of the term loan, "
              "$45.0 million is due within one year.")
    repeat = ("As of September 30, 2026, our total debt was $500.0 million, consisting of the "
              "term loan and $300.0 million of 5.0% senior notes due 2029.")
    w = _maturity_wall(" ".join([clause, repeat]), "10-Q x")
    assert w is not None and w.state == "not_stated", _k(w)


def test_bs_neg_a_note_current_portion_with_its_dollar_or_a_run_on_label_reads_no_total() -> None:
    """(-) The folded-portion guard reads the debt note's line whatever its cell carries — "$ (
    10,000 )" — and however its label runs on ("… of long-term debt and finance leases"): on the
    review's head each read Werner's 803.0 and a located $0.0 beside $10.0M the note subtracts.
    CONSTRUCTED: the note's line."""
    for line in ("Less: current portion of long-term debt $ ( 10,000 ) $ —",
                 "Less: current maturities of long-term debt and finance leases ( 10,000 ) —"):
        text = " ".join([_WERN_Q3, line])
        assert _balance_sheet_debt(text) is None, line
        w = _maturity_wall(text, "10-Q x")
        assert w is not None and w.state == "not_stated", (line, _k(w))


def test_bs_a_footnote_marker_is_no_note_figure() -> None:
    """(+) A debt note's footnote marker is not its cell. Alphabet's Q3 writes "Less: current
    portion of long-term notes (4) ( 1,996 ) ( 1,016 )", and round 1's own sweep of the cache found
    the guard reading the "(4)" as a $4 portion — right there by accident, since ( 1,996 ) follows.
    A line whose cells are dashes ("(3) — —", CONSTRUCTED) subtracts nothing, so Werner's sheet
    still reads its total and its wall."""
    text = " ".join([_WERN_Q3, "Less: current portion of long-term debt (3) — — Long-term debt "
                                "803,000 752,000"])
    assert _balance_sheet_debt(text) == (_WERN_DATE, 803.0, 0.0)
    w = _maturity_wall(text, "10-Q x")
    assert w is not None and w.state == "located" and w.within_12m_total == 0.0
