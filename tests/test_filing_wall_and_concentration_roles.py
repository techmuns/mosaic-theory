"""A 10-Q figure is read in the ROLE its own words give it — the wall's basis, the column's share.

Two defects from the filing-section parser (audit E2), each on a committed page:

* WALL (E2-D15) — Werner's and Netflix's pages printed "no near-term wall stated in filing" while
  their 10-Qs state one: Werner's Credit Facilities carry "no principal amount expected to be paid
  within 12 months" (a KNOWN $0), and Netflix states "$3,194 million" of principal AND interest due
  in the next twelve months — a different basis from the CIQ panel's principal, so it is stored
  with its basis and never compared with principal as if it were principal.
* CONCENTRATION (E2-D16) — Vital Farms' page showed "Customer C: 11.0% (prior 10.0%)" as a revenue
  concentration; in its 10-Q that row sits in the accounts-RECEIVABLE table that follows the revenue
  one. A column's role came from its POSITION; it now comes from the table's header.

THE FIXTURES are real 10-Q text (public EDGAR), cut at sentence boundaries; every pin below fails on
main at c51c286a, and each guard carries the negative pin it must not break.
"""
from __future__ import annotations

from datetime import date

from vinci.dossier import mechanical as dm
from vinci.dossier.schemas import (
    CHECK_AGREE,
    CHECK_DIFFER,
    CHECK_NOT_RUN,
    FilingSectionExtract,
)
from vinci.edgar import filing_sections as fs
from vinci.edgar import primary_source as ps

_SRC = "10-Q 0000000000-00-000000"

#: 10-Q 0000793074-26-000140 (Werner, Q2 2026), MD&A contractual obligations
_WERN_WALL = (
    "• Debt Obligations and Interest Payments – As of June 30, 2026, we had outstanding debt under "
    "the Credit Facilities with an aggregate principal amount of $793.0 million, with no principal "
    "amount expected to be paid within 12 months. As of June 30, 2026, future interest payments "
    "associated with the Credit Facilities are estimated to be $57.5 million through 2027, with "
    "$41.7 million payable within 12 months."
)
#: 10-Q 0001065280-26-000291 (Netflix, Q3 2026), MD&A liquidity
_NFLX_WALL = (
    "Debt, net of debt issuance costs, discounts and hedging impacts, increased $670 million "
    "primarily due to the issuance of debt, partially offset by the remeasurement of our "
    "Euro-denominated notes in the nine months ended September 30, 2026 and fair value hedging "
    "adjustments. The amount of principal and interest on our "
    "outstanding notes due in the next twelve months is $3,194 million. See Note 7 Debt in the "
    "accompanying notes to our consolidated financial statements."
)
#: 10-Q 0001628280-26-055372 (Microvast, Q2 2026) — a ≤12m amount that is a COMMITMENT, not debt
_MVST_COMMITMENTS = (
    "Additionally, as of June 30, 2026, the Company had $ 37.5 million in purchase commitments "
    "primarily related to inventory, and $ 13.2 million in capital commitments with $ 10.7 million "
    "due within the next 12 months."
)
#: 10-Q 0000320187-26-000193 (Nike, Q1 FY27) — securities "within one year", not a debt wall
_NKE_SECURITIES = (
    "As of August 31, 2026, the Company held $ 599 million of available-for-sale debt securities "
    "with maturity dates within one year and $ 866 million with maturity dates greater than one "
    "year and less than five years in Short-term investments on the Unaudited Condensed "
    "Consolidated Balance Sheets."
)

#: 10-Q 0001193125-26-336753 (Vital Farms, Q2 2026), Note 6 — a revenue table, then a receivable one
_VITL_CONC = (
    "During the 13-week and 26-week periods ended June 28, 2026 and June 29, 2025 , the Company "
    "had "
    "customers that individually accounted for 10% or more of the Company’s net revenue. The "
    "percentage of net revenue from significant customers during the 13-week and 26-week periods "
    "ended June 28, 2026 and June 29, 2025 is as follows: Net Revenue for the 13-Weeks Ended June "
    "28, 2026 Net Revenue for the 13-Weeks Ended June 29, 2025 Net Revenue for the 26-Weeks Ended "
    "June 28, 2026 Net Revenue for the 26-Weeks Ended June 29, 2025 Customer A 21 % 21 % 22 % 22 % "
    "Customer B 12 % * 12 % * * Net revenue was less than 10% As of June 28, 2026 and December 28, "
    "2025 , the Company had customers that individually accounted for 10% or more of the Company’s "
    "accounts receivable. The percentage of accounts receivable, net due from significant "
    "customers as of June 28, 2026 and December 28, 2025 is as follows: Accounts Receivable, Net "
    "as "
    "of June 28, 2026 Accounts Receivable, Net as of December 28, 2025 Customer A 15 % 16 % "
    "Customer B 15 % 15 % Customer C 11 % 10 % Note 7."
)
#: 10-Q 0001628280-26-055372 (Microvast, Q2 2026) — column headings that name periods, not roles
_MVST_CONC = (
    "The following table summarizes net revenues from the three largest customers that each "
    "accounted for over 10% of our net revenues for the periods indicated: Three Months Ended June "
    "30, 2026 2025 Customer A 46 % 18 % Customer B 11 % * Customer C 10 % * Six Months Ended June "
    "30, 2026 2025 Customer A 48 % 25 % Customer B 14 % 13 % Our revenues for the three and six "
    "months ended June 30, 2026 were materially concentrated with a small number of customers."
)


# --- WALL (E2-D15) -------------------------------------------------------------------------------
def test_a_stated_zero_is_a_located_wall_of_zero() -> None:
    w = fs._maturity_wall(_WERN_WALL, _SRC)
    assert w is not None and w.state == "located"
    assert w.within_12m_total == 0.0 and w.basis is None  # absent is principal
    assert "no principal amount expected to be paid within 12 months" in w.verbatim


def test_principal_and_interest_is_located_with_its_basis() -> None:
    w = fs._maturity_wall(_NFLX_WALL, _SRC)
    assert w is not None and w.state == "located"
    assert w.within_12m_total == 3194.0 and w.basis == "principal and interest"


def test_a_stated_scale_is_read_not_assumed() -> None:
    """The widened form captures its scale: billions are never stored as $M digits."""
    w = fs._maturity_wall("Of the term loan, $1.2 billion is due within the next 12 months.", _SRC)
    assert w is not None and w.within_12m_total == 1200.0


def test_a_commitment_or_a_security_due_within_a_year_is_not_the_wall() -> None:
    """NEGATIVE PINS — the debt guard's live rejection (Microvast's capital commitments) and the
    securities ladder an over-wide "within one year" would take (Nike)."""
    assert fs._stated_12m(_MVST_COMMITMENTS) is None
    assert fs._maturity_wall(_NKE_SECURITIES, _SRC) is None


def test_a_filing_that_states_no_figure_is_still_not_stated() -> None:
    """NEGATIVE PIN — a debt section with no ≤12m figure keeps the value-free KNOWN."""
    w = fs._maturity_wall("The Company's revolving credit facility matures in 2029.", _SRC)
    assert w is not None and w.state == "not_stated" and w.within_12m_total is None


def test_a_zero_wall_agrees_with_an_empty_window_and_diverges_from_a_full_one() -> None:
    """Werner's $0 against a panel with nothing due in the window AGREES; dividing by the zero read
    it as a 100% gap. A panel with principal due still DIVERGES from a stated zero."""
    bal = date(2026, 6, 30)
    later = [ps.PanelInstrument("Loan Security Agreement Facility", 325.0, date(2027, 9, 21))]
    assert ps.wall_coherence_read(0.0, later, balance=bal).check == CHECK_AGREE
    due = [ps.PanelInstrument("Term Loan", 50.0, date(2027, 1, 31))]
    assert ps.wall_coherence_read(0.0, due, balance=bal).check == CHECK_DIFFER


def test_a_principal_and_interest_figure_is_never_compared_with_principal() -> None:
    """Netflix's $3,194M against the panel's in-window principal ($1,000M + $1,526M) is a 26% gap
    that is only the coupon. Not compared — and said so, through the assembler's own reader."""
    bal = date(2026, 9, 30)
    panel = [ps.PanelInstrument("4.375% Senior Notes", 1000.0, date(2026, 11, 15)),
             ps.PanelInstrument("3.625% Senior Notes", 1526.0, date(2027, 5, 15))]
    wall = fs._maturity_wall(_NFLX_WALL, _SRC)
    read = dm._wall_read(FilingSectionExtract(source_ref=_SRC, maturity_wall=wall), panel, bal)
    assert read.check == CHECK_NOT_RUN
    assert "principal and interest" in read.line and "DIVERGES" not in read.line
    # a principal wall through the same reader is still compared
    assert ps.wall_coherence_read(2526.0, panel, balance=bal).check == CHECK_AGREE


# --- CONCENTRATION (E2-D16) ----------------------------------------------------------------------
def _customers(text: str) -> list[tuple[str, float, float | None]]:
    c = fs._concentration(text, _SRC)
    return [(x.name, x.pct, x.prior_pct) for x in (c.customers if c else [])]


def test_a_receivables_table_is_not_revenue_concentration() -> None:
    assert _customers(_VITL_CONC) == [("Customer A", 21.0, 21.0), ("Customer B", 12.0, None)]


def test_period_columns_under_a_revenue_lead_in_keep_their_prior() -> None:
    """NEGATIVE PIN — column headings that name PERIODS ("2026 2025") take the lead-in's role, so
    Microvast's second figure is still the prior period's revenue share."""
    assert _customers(_MVST_CONC) == [("Customer A", 46.0, 18.0), ("Customer B", 11.0, None),
                                      ("Customer C", 10.0, None)]


def test_a_receivable_column_beside_a_revenue_one_is_not_a_prior() -> None:
    text = ("The following customers accounted for 10% or more of revenue or accounts receivable: "
            "% of revenue % of accounts receivable Customer A 15 % 32 %")
    assert _customers(text) == [("Customer A", 15.0, None)]
    prose = ("The Department of Transportation represented 15.2% and 41.0% of revenue and accounts "
             "receivable, respectively.")
    assert _customers(prose) == [("Department of Transportation", 15.2, None)]
