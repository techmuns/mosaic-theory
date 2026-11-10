"""A ≤12-month figure for PART of the debt is never the company's wall (TeamNostra fix request 2).

Three defects in `filing_sections._maturity_wall`, each reproduced on public 10-Q text:

* V2-N1 — the regression #860 (`7e1fb468`) brought with its widened forms. One instrument's
  sentence ("Of the term loan, $45.0 million is due within one year") was read as the company's
  whole twelve-month wall beside $500M of notes, and the coherence check then read AGREES against a
  CIQ panel that lacked the notes too. Helmerich & Payne's 10-Q for the quarter ended 2026-06-30
  states the same shape for its term loans, and a second facility's own "$3.4 million … payable
  within one year" two paragraphs later: main stored $6.9M as HP's wall.
* RE2-D13 — the original "$X million due within the next 12 months" form was tried first with no
  debt or lease filter, so Archer Aviation's "future lease payments of $19.1 million due within the
  next 12 months" was located as its debt wall.
* E2-D15's residual — the tranche and commitment readers read millions only: "$2.1 billion of
  purchase commitments" gave nothing.

THE RULE. A ≤12m figure is the company's wall only when the clause before it names the company's
debt in aggregate ("our total debt", "outstanding borrowings", "our outstanding notes"). A clause
naming one instrument ("under our secured term loan credit agreements") is that instrument's —
unless its own principal is the company's total debt as the filing states it elsewhere, unqualified
(Werner: "outstanding debt under the Credit Facilities … $793.0 million" and "increasing our
outstanding debt to $793.0 million"). Anything else is `not_stated`, with a note naming the figure.
"""
from __future__ import annotations

from datetime import date

from vinci.dossier import mechanical as dm
from vinci.dossier.schemas import CHECK_AGREE, CHECK_NOT_RUN
from vinci.edgar import filing_sections as fs
from vinci.edgar import primary_source as ps

_SRC = "10-Q 0000000000-00-000000"

#: 10-Q 0000046765-26-000042 (Helmerich & Payne, quarter ended 2026-06-30), MD&A liquidity
_HP_TERM_LOANS = (
    "If needed, we may decide to obtain additional funding from our $950.0 million Amended Credit "
    "Facility. Our indebtedness under our unsecured senior notes totaled $1.8 billion at June 30, "
    "2026 and comprised of the following maturities: $350.0 million due December 2027, $350.0 "
    "million due December 2029, $550.0 million due September 2031, and $550.0 million due December "
    "2034. Our indebtedness under our secured term loan credit agreements totaled $77.7 million at "
    "June 30, 2026, of which $6.9 million is due within one year, and the remaining balance is "
    "required to be paid on a quarterly basis through the respective maturity dates of December "
    "2033 and December 2034."
)
#: 10-Q 0001824502-26-000089 (Archer Aviation, quarter ended 2026-09-30): its MD&A lease
#: obligations sentence, then its debt note's maturity sentence (two real sentences, one filing)
_ACHR_LEASES = (
    "Under our operating leases as noted in Note 9 - Commitments and Contingencies in the "
    "accompanying notes to our condensed consolidated financial statements, we have undiscounted "
    "future lease payments of $19.1 million due within the next 12 months and $189.7 million due "
    "thereafter. The Credit Agreement matures on the earlier of October 5, 2033 or the date on "
    "which the outstanding borrowings under the Credit Agreement have been declared or "
    "automatically become due and payable pursuant to the terms of the Credit Agreement."
)
#: 10-Q 0000793074-26-000140 (Werner, quarter ended 2026-06-30): the obligations bullet, and the
#: liquidity sentence that states the same principal as the company's whole outstanding debt
_WERN_BULLET = (
    "• Debt Obligations and Interest Payments – As of June 30, 2026, we had outstanding debt under "
    "the Credit Facilities with an aggregate principal amount of $793.0 million, with no principal "
    "amount expected to be paid within 12 months."
)
_WERN_TOTAL = (
    "We had net borrowings on our debt under our Credit Facilities of $41.0 million during the six "
    "months ended June 30, 2026, increasing our outstanding debt to $793.0 million at June 30, "
    "2026."
)
#: TeamNostra's constructed note (V2-N1), balance date 2026-06-30
_V2_N1 = ("Of the term loan, $45.0 million is due within one year. Our 4.0% Senior Notes, $500.0 "
          "million in principal, mature on March 1, 2027.")
#: V2-N1's notes sentence alone — the debt beside each constructed part-of-the-debt clause below
_NOTES_500 = "Our 4.0% Senior Notes, $500.0 million in principal, mature on March 1, 2027."


# --- V2-N1: one instrument's figure is not the wall -------------------------------------------
def test_v2_n1_one_term_loans_figure_is_not_the_wall() -> None:
    w = fs._maturity_wall(_V2_N1, _SRC)
    assert w is not None and w.state == "not_stated" and w.within_12m_total is None
    # LOUD, never silent: the note names the figure it did not take as the wall, and its sentence
    assert "$45.0M" in w.note and "Of the term loan" in w.note


def test_v2_n1_never_agrees_with_a_panel_that_lacks_the_notes_too() -> None:
    """The coherence read V2-N1 showed: a panel holding only the term loan AGREED with $45.0M,
    and the $500M of notes due in the window never appeared. Now it is not run."""
    filing = fs.parse_filing_sections(_V2_N1, source_ref=_SRC)
    panel = [ps.PanelInstrument("Term Loan", 45.0, date(2027, 3, 31))]
    read = dm._wall_read(filing, panel, date(2026, 6, 30))
    assert read.check == CHECK_NOT_RUN and "AGREES" not in read.line


def test_helmerich_and_payne_term_loans_are_part_of_its_debt() -> None:
    """Real text: HP's term-loan sentence follows $1.8bn of senior notes it does not cover."""
    w = fs._maturity_wall(_HP_TERM_LOANS, _SRC)
    assert w is not None and w.state == "not_stated" and w.within_12m_total is None
    assert "$6.9M" in w.note and "secured term loan credit agreements" in w.note


def test_one_instrument_covering_all_the_debt_is_the_wall() -> None:
    """NEGATIVE PIN — Werner's Credit Facilities ARE its debt: the filing states the same $793.0M
    as its outstanding debt, unqualified, so the stated $0 stays located (E2-D15's WERN half)."""
    w = fs._maturity_wall(f"{_WERN_BULLET} {_WERN_TOTAL}", _SRC)
    assert w is not None and (w.state, w.within_12m_total) == ("located", 0.0)
    # without the unqualified total, the same sentence is one instrument's — refused, named
    alone = fs._maturity_wall(_WERN_BULLET, _SRC)
    assert alone is not None and alone.state == "not_stated" and "$0.0M" in alone.note


def test_a_qualified_total_does_not_cover_an_instrument() -> None:
    """NEGATIVE PIN — Bellring's real sentence (10-Q 0001772016-26-000022) states $300.0M of
    "outstanding borrowings … under its Revolving Credit Facility": the revolver's, not a company
    total. Beside a CONSTRUCTED revolver ≤12m figure of the same principal it covers nothing."""
    text = ("Additionally, the Company had outstanding borrowings of $300.0 million and $250.0 "
            "million under its Revolving Credit Facility as of June 30, 2026 and September 30, "
            "2025, respectively. Of the $300.0 million outstanding under the Revolving Credit "
            "Facility, $25.0 million is due within one year.")
    w = fs._maturity_wall(text, _SRC)
    assert w is not None and w.state == "not_stated" and "$25.0M" in w.note
    # the same principal stated UNQUALIFIED as the company's debt does cover it
    w = fs._maturity_wall(text + " Our total debt was $300.0 million at June 30, 2026.", _SRC)
    assert w is not None and (w.state, w.within_12m_total) == ("located", 25.0)


def test_an_aggregate_subject_is_still_the_wall() -> None:
    """NEGATIVE PINS — Microvast's "outstanding borrowings" and Netflix's "our outstanding notes"
    name the company's debt in aggregate, as does audit E2's "Of our total debt"."""
    mvst = ("As of June 30, 2026, the Company had outstanding borrowings of $ 118.6 million, with "
            "$ 104.2 million due within the next 12 months, a bond payable of $ 41.7 million that "
            "matures in January 2027 and other current liabilities of $ 197.9 million.")
    w = fs._maturity_wall(mvst, _SRC)
    assert w is not None and (w.state, w.within_12m_total) == ("located", 104.2)
    nflx = ("The amount of principal and interest on our outstanding notes due in the next twelve "
            "months is $3,194 million.")
    w = fs._maturity_wall(nflx, _SRC)
    assert w is not None and (w.state, w.within_12m_total) == ("located", 3194.0)
    w = fs._maturity_wall("Of our total debt, $1.2 billion is due within the next 12 months.", _SRC)
    assert w is not None and (w.state, w.within_12m_total) == ("located", 1200.0)


def test_a_total_inside_the_clause_does_not_cover_the_instrument() -> None:
    """CONSTRUCTED (code review): the clause's last figure is the company's total, stated before
    the instrument, so it is not the term loan's own principal — the V2-N1 shape with the total in
    the same sentence. Before the fix this read located $45.0M against $500M of debt."""
    w = fs._maturity_wall("As of June 30, 2026, our total debt was $500.0 million, and of the term "
                          "loan, $45.0 million is due within one year.", _SRC)
    assert w is not None and w.state == "not_stated" and "$45.0M" in w.note


def test_an_abbreviation_does_not_cut_the_instrument_out_of_the_clause() -> None:
    """CONSTRUCTED (code review): "N.A. " is not a sentence end. Cut there, the clause kept only
    "borrowings" and the term loan's figure read as the whole wall."""
    w = fs._maturity_wall("Under the term loan with Bank of America, N.A. and other lenders, "
                          "borrowings of $45.0 million are due within one year. " + _NOTES_500,
                          _SRC)
    assert w is not None and w.state == "not_stated" and "$45.0M" in w.note


def test_debt_qualified_by_its_instrument_is_that_instruments() -> None:
    """CONSTRUCTED (code review): an aggregate word QUALIFIED by its instrument ("borrowings under
    the ABL facility"), mortgage notes and a lettered term loan are each part of the debt."""
    for subject in ("Of the borrowings under the ABL facility", "Of our mortgage notes",
                    "Of the Term A loans outstanding as borrowings"):
        w = fs._maturity_wall(f"{subject}, $45.0 million is due within one year. {_NOTES_500}",
                              _SRC)
        assert w is not None and w.state == "not_stated" and "$45.0M" in w.note, subject


# --- RE2-D13: a lease is not the wall ---------------------------------------------------------
def test_re2_d13_lease_payments_are_not_the_debt_wall() -> None:
    """Real text: Archer's lease payments, on main the original form's first match."""
    w = fs._maturity_wall(_ACHR_LEASES, _SRC)
    assert w is not None and w.state == "not_stated" and w.within_12m_total is None
    assert "lease" not in w.note  # a lease is not part of the debt: it is not named as one


def test_re2_d13_the_debt_sentence_after_a_lease_one_is_read() -> None:
    """NEGATIVE PIN — the guard skips the lease sentence; it does not stop the read."""
    w = fs._maturity_wall(f"{_ACHR_LEASES} Of our total debt, $12.0 million is due within the "
                          "next 12 months.", _SRC)
    assert w is not None and (w.state, w.within_12m_total) == ("located", 12.0)


# --- E2-D15's residual: billions in the tranche and commitment readers -------------------------
def test_e2_d15_a_commitment_in_billions_is_read() -> None:
    got = fs._commitments("As of June 30, 2026, we had $2.1 billion of purchase commitments with "
                          "$1.4 billion due within the next 12 months.", _SRC)
    assert [(c.kind, c.amount, c.within_12m) for c in got] == [("purchase", 2100.0, 1400.0)]


def test_e2_d15_a_tranche_in_billions_is_read() -> None:
    w = fs._maturity_wall("Of our total debt, $1.2 billion is due within the next 12 months; the "
                          "term loan of $1.5 billion matures in March 2027.", _SRC)
    assert w is not None
    assert [(t.name, t.amount, t.maturity) for t in w.tranches] == [
        ("term loan", 1500.0, "March 2027")]


def test_e2_d15_millions_are_read_as_before() -> None:
    """NEGATIVE PIN — Microvast's real commitments sentence reads as it did."""
    got = fs._commitments("Additionally, as of June 30, 2026, the Company had $ 37.5 million in "
                          "purchase commitments primarily related to inventory, and $ 13.2 million "
                          "in capital commitments with $ 10.7 million due within the next 12 "
                          "months.", _SRC)
    assert [(c.kind, c.amount, c.within_12m) for c in got] == [
        ("purchase", 37.5, None), ("capital", 13.2, 10.7)]


def test_e2e_werner_full_page_text_still_agrees() -> None:
    """END TO END on Werner's committed panel: both real sentences, in their 10-Q's order (the
    obligations bullet precedes the liquidity sentence), read $0 and AGREE."""
    filing = fs.parse_filing_sections(f"{_WERN_BULLET} {_WERN_TOTAL}", source_ref=_SRC)
    import json
    from pathlib import Path

    from vinci.dossier.schemas import CapitalStructure
    page = Path(__file__).resolve().parent.parent / "data" / "dossiers" / "WERN" / "dossier.json"
    mech = json.loads(page.read_text())["mechanical"]
    panel = dm._wall_panel(CapitalStructure.model_validate(mech["capital_structure"]))
    read = dm._wall_read(filing, panel, date(2026, 6, 30))
    assert read.check == CHECK_AGREE and "filing $0.0M" in read.line
