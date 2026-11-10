"""(audit E2-D19) A covenant term's VALUE must not state what its own QUOTE does not.

#804 checks that a term's quote is a span of its exhibit. The value beside it was never compared
with that quote, so a model answer of {"value": "June 15, 2031", "quote": "The Notes shall mature
on June 15, 2030"} read PRESENT: a year the exhibit's own clause contradicts, shown as the term. Now
every YEAR and every DOLLAR FIGURE the value states must be stated by the quote, or the term is a
visible UNKNOWN with an (E5) flag naming what the quote does not state. TeamNostra fix request 2
(RE2-D16) widened it to every class: whole dates, ratios, percents and basis points, and unmarked
amounts, each compared in its own unit.

LLM-ADJACENT, SO NO LIVING PIN. Each case is a model answer stubbed through the real
`_extract_from_exhibit`; the value/quote pairs below are frozen literals copied from committed
pages at 8e6b12b1 (named per case), never read from the re-drawn artifacts. Every assertion reads
status, a constant prefix, or a figure the case itself supplies.
"""

from __future__ import annotations

import json
import pathlib
import typing

import pytest

from tests.test_covenant_refused_newer import _node_render
from vinci.dossier import covenant_extract as ce
from vinci.dossier.render import _refused_newer_text, render_markdown
from vinci.dossier.schemas import CovenantPointer, CovenantTerm, Dossier, Sourced, SourceStatus
from vinci.graph.llm import LlmClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
_SRC = "8-K 0000000001-26-000001 · ex101.htm"


class _FakeLlm(LlmClient):
    def __init__(self, payload: dict[str, typing.Any]) -> None:
        self._payload = payload

    @property
    def model(self) -> str:
        return "fake-model-1"

    def extract(
        self, *, system: str, user: str, tool: dict[str, typing.Any], cache: bool = False
    ) -> dict[str, typing.Any]:
        return self._payload


def _one(value: str, quote: str, exhibit: str | None = None,
         name: str = "Maturity date") -> tuple[CovenantTerm, list[str]]:
    """One model answer through the real extractor, against an exhibit that holds the quote."""
    payload = {"terms": [{"name": name, "present": True, "value": value, "quote": quote}]}
    (row,), flags, _ = ce._extract_from_exhibit(
        _FakeLlm(payload), exhibit if exhibit is not None else f"Preamble. {quote} Signatures.",
        name="Example Co", ticker="EXM", source_ref=_SRC, title="CREDIT AGREEMENT")
    return row, flags


def _refused(row: CovenantTerm, flags: list[str], *named: str) -> None:
    v = row.value
    assert v.status is SourceStatus.UNKNOWN and v.value is None, v
    assert (v.note or "").startswith(ce.VALUE_REFUSED_NOTE_PREFIX), v.note
    assert (v.note or "").startswith(ce.REFUSED_NOTE_PREFIX)  # the collapse reads it as a refusal
    assert ce._acc_of(v.note) == "0000000001-26-000001"
    (flag,) = [f for f in flags if "refused" in f]
    assert flag.startswith("(E5)") and row.name in flag and _SRC in flag, flag
    for figure in named:
        assert figure in (v.note or "") and figure in flag, (figure, v.note, flag)


def _kept(row: CovenantTerm, flags: list[str], value: str) -> None:
    assert row.value.status is SourceStatus.PRESENT and row.value.value == value, row.value
    assert not [f for f in flags if "refused" in f], flags


# --- the rule -------------------------------------------------------------------------------------


def test_a_year_the_quote_does_not_state_is_refused() -> None:
    """(−/+) The audit's stub: 2031 against a quote reading 2030 is UNKNOWN + a flag naming 2031;
    the value the quote states is kept."""
    quote = "The Notes shall mature on June 15, 2030"
    _refused(*_one("June 15, 2031", quote), "2031")
    _kept(*_one("June 15, 2030", quote), "June 15, 2030")


def test_a_dollar_figure_the_quote_does_not_state_is_refused() -> None:
    """(−) AMZN's committed principal row (8-K 0001104659-23-113444): the value adds a
    US$5,000,000,000 sublimit its quote never states. The commitment it does state is not enough —
    the value is withheld whole, as a quote refusal withholds it."""
    value = ("Aggregate Commitments equal to US$15,000,000,000 (with an Alternative Currency "
             "Sublimit equal to the lesser of the Aggregate Commitments and US$5,000,000,000)")
    quote = "As of the Closing Date, the Aggregate Commitments equal to US$15,000,000,000."
    row, flags = _one(value, quote, name="Principal / commitment amount")
    _refused(row, flags, "$5,000,000,000")
    assert "$15,000,000,000" not in (row.value.note or "")  # only what the quote does NOT state


def test_a_year_added_as_context_is_refused() -> None:
    """(−) V's committed maturity row (8-K 0001193125-13-032823): '(Agreement dated as of January
    31, 2013)' is in the value, not in the Termination Date clause quoted for it."""
    value = ("Termination Date = 364 days from the date of this Agreement (Agreement dated as of "
             "January 31, 2013). Swing Loan Maturity Date = earlier of (a) the fourth Business Day "
             "after the making of such Loan and (b) the Termination Date.")
    quote = ("\"Termination Date\" means 364 days from the date of this Agreement, or, if such day "
             "is not a Business Day, the next preceding Business Day or any earlier date on which "
             "the Total Commitment is reduced to zero or otherwise terminated pursuant to the "
             "terms hereof.")
    _refused(*_one(value, quote), "2013")


@pytest.mark.parametrize(("value", "quote"), [
    # UBER, 8-K 0001552781-22-000307: the conformed copy prints the struck $1.5bn beside the
    # $1.0bn that replaced it; the replacement carries no "$" of its own
    ("Section 6.05 Minimum Liquidity: The Borrower shall not permit Liquidity to be less than "
     "$1,000,000,000 as of the last day of any fiscal quarter of the Borrower ending after the "
     "Amendment No. 5 Effective Date.",
     "Section 6.05 Minimum Liquidity . The Borrower shall not permit Liquidity to be less than "
     "$ 1,500,000,000 1,000,000,000 as of the last day of any fiscal quarter of the Borrower "
     "ending after the Amendment No. 5 Effective Date."),
    # NFLX, 8-K 0001193125-19-094705: struck and replacement separated by " . "
    ("$750,000,000 (as amended; prior $500,000,000) aggregate Revolving Commitments",
     "The initial aggregate amount of the Lenders' Revolving Commitments as of the First "
     "Amendment Effective Date is $ 500,000,000 . 750,000,000."),
    # NFLX, 8-K 0001193125-21-193187: separated by ", "
    ("No financial-maintenance covenants; incurrence-based Aggregate Debt basket in Sections "
     "6.01, 6.02, 6.04: greater of (a) $6,000,000,000 and (b) 3.50 times Consolidated EBITDA for "
     "the Measurement Period",
     "any Domestic Restricted Subsidiary may create, incur, issue or assume Subsidiary Debt that "
     "would otherwise be subject to the restrictions set forth in Section 6.01(a) , without "
     "Guaranteeing the payment of the Obligations, if after giving effect thereto, Aggregate Debt "
     "does not exceed an amount equal to the greater of (a) $ 3,750,000,000, 6,000,000,000, and "
     "(b) 2.75 3.50 times Consolidated EBITDA of the Borrower for the Measurement Period "
     "immediately preceding the date of the creation or incurrence of the Subsidiary Debt."),
], ids=["UBER-liquidity", "NFLX-2019-commitments", "NFLX-2021-debt-basket"])
def test_a_conformed_replacement_figure_is_stated(value: str, quote: str) -> None:
    """(+) A conformed amendment prints the replacement figure right after the struck one, with
    no "$" of its own. That figure IS stated: the three committed values reading it stay PRESENT."""
    _kept(*_one(value, quote, name="Principal / commitment amount"), value)


@pytest.mark.parametrize(("value", "quote"), [
    ("Commitments of $1.5 billion", "the Aggregate Commitments equal $1,500,000,000."),
    ("Commitments of $1,500,000,000", "the Aggregate Commitments equal $1.5 billion."),
    ("Maturity: 6/30/2029", "the Maturity Date shall be June 30, 2029"),
    ("tested through fiscal year 2030", "tested quarterly through FY2030"),  # review round 1
])
def test_a_figure_stated_at_another_scale_or_a_year_in_another_date_form_is_stated(
        value: str, quote: str) -> None:
    """(+) The same figure at another scale, and the same year in another date form, are stated."""
    _kept(*_one(value, quote), value)


def test_a_bare_number_that_follows_no_dollar_figure_is_not_a_dollar_figure() -> None:
    """(−) Only a conformed REPLACEMENT inherits the "$": a bare 1,000,000,000 standing alone (a
    share count, a notional) does not state $1,000,000,000."""
    _refused(*_one("Commitments of $1,000,000,000",
                   "the Borrower may issue up to 1,000,000,000 shares of common stock"),
             "$1,000,000,000")


def test_a_rate_figure_the_quote_does_not_state_is_refused() -> None:
    """(−/+) TeamNostra fix request 2, RE2-D16: a percent or bps figure in the value WAS left to the
    rate-component check, so "Term SOFR + 1.75%" stood PRESENT beside a quote stating only "the
    Applicable Margin" (the scope call #873 deferred, STATE row 34). It is now refused; the
    components keep their own check, and "zero" still states a 0% floor."""
    _refused(*_one("Term SOFR + 1.75%", "Term SOFR plus the Applicable Margin",
                   name="Interest / coupon rate"), "1.75%")
    # review round 2 of #873: "zero" is a rate floor, never "$0"; the rate components ride along
    payload = {"terms": [{"name": "Interest / coupon rate", "present": True,
                          "value": "Term SOFR + 1.75%; floor of zero",
                          "quote": "Term SOFR plus 1.75%; if Term SOFR is less than zero, it "
                                   "shall be deemed to be zero", "margin_pct": 1.75,
                          "floor_pct": 0.0}]}
    quote = payload["terms"][0]["quote"]
    (row,), flags, _ = ce._extract_from_exhibit(
        _FakeLlm(payload), f"x {quote} y", name="Example Co", ticker="EXM", source_ref=_SRC,
        title="CREDIT AGREEMENT")
    _kept(row, flags, "Term SOFR + 1.75%; floor of zero")
    assert (row.margin_pct, row.floor_pct) == (1.75, 0.0)
    # ...and the "2000" inside "0.2000%" is not a year, and 0.2000% is 0.20%
    _kept(*_one("Commitment fee: 0.2000% per annum",
                "the Commitment Fee Rate shall be 0.20% per annum", name="Commitment Fee"),
          "Commitment fee: 0.2000% per annum")


# --- RE2-D16: every class of figure, in its own unit ---------------------------------------------
@pytest.mark.parametrize(("value", "quote", "named"), [
    ("Maximum Consolidated Leverage Ratio of 5.00x",
     "the Consolidated Leverage Ratio shall not exceed 4.50 to 1.00", "5.00x"),
    ("Minimum Interest Coverage Ratio of 2.50x",
     "the Interest Coverage Ratio shall not be less than 3.00 to 1.00", "2.50x"),
    ("Term SOFR plus 2.00%", "a rate per annum equal to Term SOFR plus 1.75%", "2.00%"),
    ("July 25, 2030", "“Maturity Date” means December 22, 2030.", "July 25, 2030"),
    ("Commitments of 1,000,000,000", "the Aggregate Commitments are $750,000,000.",
     "1,000,000,000"),
    ("Conversion rate: 50.0000 shares per $1,000 principal amount",
     "an initial conversion rate of 45.4545 shares of Common Stock per $1,000 principal amount",
     "50.0000"),
], ids=["ratio-x", "ratio-coverage", "percent", "whole-date", "unmarked-amount", "share-count"])
def test_re2_d16_each_constructed_case_is_refused(value: str, quote: str, named: str) -> None:
    """(−) TeamNostra's constructed cases (document 14 E2-D16; V2's residual): each figure differs
    from its own quote and stood PRESENT, because only years and currency figures were read."""
    _refused(*_one(value, quote, name="Financial-maintenance covenants"), named)


@pytest.mark.parametrize(("value", "quote", "named"), [
    # AMZN, committed (8-K 0001104659-23-113444): the grid's levels are in another clause
    ("Eurocurrency Rate Loans: LIBO Rate plus the Applicable Rate; Base Rate Loans: Base Rate "
     "plus the Applicable Rate. Applicable Rate: (a) Base Rate Loans 0.00% per annum, (b) "
     "Eurocurrency Rate Loans 0.50% per annum",
     "(i) each Eurocurrency Rate Loan shall bear interest on the outstanding principal amount "
     "thereof for each Interest Period at a rate per annum equal to the LIBO Rate for such "
     "Interest Period plus the Applicable Rate; and (ii) each Base Rate Loan shall bear interest "
     "on the outstanding principal amount thereof from the applicable borrowing or conversion "
     "date at a rate per annum equal to the Base Rate plus the Applicable Rate.", "0.50%"),
    # PARR, committed: the quote states June 6, 2023; the value adds a June 5 its quote never does
    ("Mandatory prepayment: if Billings Acquisition Date does not occur on or before June 5, 2023, "
     "Revolving Commitments automatically and permanently reduced on June 6, 2023",
     "(iii) If a reduction in Revolving Commitments pursuant to Section 2.4(c)(iii) occurs, "
     "Borrowers shall prepay the Obligations by causing ... the proceeds of the Billings "
     "Acquisition Borrowing to be released from the Billings Acquisition Escrow Account to Agent "
     "on June 6, 2023 ...", "June 5, 2023"),
], ids=["AMZN-grid-percent", "PARR-whole-date"])
def test_re2_d16_a_committed_value_adding_a_figure_is_refused(
        value: str, quote: str, named: str) -> None:
    """(−) Real committed pairs (pages at 5e3def4a) the new classes refuse at re-assembly."""
    row, flags = _one(value, quote, name="Interest / coupon rate")
    _refused(row, flags, named)
    assert "June 6, 2023" not in (row.value.note or "")  # only what the quote does NOT state


@pytest.mark.parametrize(("value", "quote"), [
    # BURL, committed: a conformed copy prints the struck date beside its replacement
    ("July 25, 2030 (amended from December 22, 2026)",
     "“ Maturity Date ” means December 22 July 25 , 2026 2030 ."),
    # NFLX, committed: the struck ratio beside its replacement, and section numbers in the value
    ("Aggregate Debt not to exceed the greater of (a) $3,750,000,000 (as amended from "
     "$2,500,000,000) and (b) 2.75 times (as amended from 2.50 times) Consolidated EBITDA for the "
     "Measurement Period immediately preceding — used as the incurrence threshold under Sections "
     "6.01, 6.02 and 6.04",
     "Notwithstanding Sections 6.01(a) and (b) , any Domestic Restricted Subsidiary may create, "
     "incur, issue or assume Subsidiary Debt that would otherwise be subject to the restrictions "
     "set forth in Section 6.01(a) , without Guaranteeing the payment of the Obligations, if after "
     "giving effect thereto, Aggregate Debt does not exceed an amount equal to the greater of (a) "
     "$ 2,500,000,000 , 3,750,000,000, and (b) 2.50 2.75 times Consolidated EBITDA of the Borrower "
     "for the Measurement Period immediately preceding the date of the creation or incurrence of "
     "the Subsidiary Debt."),
    # NCNO, committed: a ratio at the end of its sentence ("4.00:1.00.")
    ("Consolidated Total Leverage Ratio not greater than 4.00:1.00; Consolidated Interest Coverage "
     "Ratio not less than 3.00:1.00 (each commencing fiscal quarter ending January 31, 2025)",
     "(a) Consolidated Total Leverage Ratio . Permit the Consolidated Total Leverage Ratio as of "
     "the end of any fiscal quarter of Holdings (commencing with the fiscal quarter ending January "
     "31, 2025) to be greater than 4.00:1.00. (b) Consolidated Interest Coverage Ratio . Permit "
     "the Consolidated Interest Coverage Ratio as of the end of any four fiscal quarter period of "
     "Holdings (commencing with the fiscal quarter ending January 31, 2025) to be less than "
     "3.00:1.00."),
], ids=["BURL-conformed-date", "NFLX-conformed-ratio", "NCNO-ratio-at-sentence-end"])
def test_re2_d16_a_committed_value_its_quote_states_is_kept(value: str, quote: str) -> None:
    """(+) NEGATIVE PINS — committed values whose quote states every figure, in a form the new
    classes must read: a conformed date, a struck ratio, a ratio before a full stop."""
    _kept(*_one(value, quote, name="Financial-maintenance covenants"), value)


@pytest.mark.parametrize(("value", "quote"), [
    ("Maximum Leverage Ratio of 4.50x", "shall not exceed 4.50 to 1.00"),
    ("Maximum Leverage Ratio of 4.50:1.00", "shall not exceed 4.50 to 1.00"),
    ("Applicable Margin of 175 bps", "the Applicable Margin shall be 1.75% per annum"),
    ("First Extension: Nov 1, 2039", "will commence on November 1, 2039"),
    ("Maturity: the 30th day of June, 2029", "the Maturity Date shall be June 30, 2029"),
    ("Section 6.02 restricts Liens for 3 to 5 years", "Liens are restricted by this Agreement"),
    ("Facility of 500 million", "an aggregate principal amount of €500,000,000"),
], ids=["x-is-to-one", "colon-is-to-one", "bps-is-percent", "abbreviated-month",
        "ordinal-day", "section-and-span-not-read", "unmarked-scaled"])
def test_re2_d16_the_same_figure_in_another_form_is_stated(value: str, quote: str) -> None:
    """(+) The same figure in another form is stated; a section number, a small count and a span
    are not figures this check reads."""
    _kept(*_one(value, quote, name="Financial-maintenance covenants"), value)


@pytest.mark.parametrize(("value", "quote"), [
    ("Facility of 500 million", "a facility of 500 million, which may be increased"),
    ("Commitments of 1,000,000,000", "the Aggregate Commitments are 1,000,000,000, as reduced"),
    ("Maturity: December 22, 2030", "“Maturity Date” means December 22,2030."),
    ("Interest at 5.25% per annum", "the Notes bear interest at 5 1/4% per annum"),
], ids=["scaled-before-comma", "grouped-before-comma", "date-comma-no-space", "fraction-percent"])
def test_review_round_0_a_figure_the_quote_states_before_a_comma_or_as_a_fraction_is_stated(
        value: str, quote: str) -> None:
    """(+) Review round 0: an unmarked amount followed by a comma was never read in the quote, a
    date written "22,2030" was not a date, and "5 1/4%" was read as "4%" — each refused a value its
    quote states."""
    _kept(*_one(value, quote, name="Financial-maintenance covenants"), value)


@pytest.mark.parametrize(("value", "quote", "named"), [
    ("Commitments of 1,000,000,000, as reduced", "the Aggregate Commitments are $750,000,000.",
     "1,000,000,000"),
    ("Facility of 500 million, increasing", "a facility of $750,000,000", "500 million"),
    ("5 1/4% Senior Notes", "the 5 1/2% Senior Notes due 2030", "5 1/4%"),
    # MCK, committed: a slash between two percents is no fraction — "0%" is still read
    ("Net Proceeds Percentage 100%, stepping down to 50%/0%",
     "Term Loans equal to 100% (such percentage as it may be reduced as described below) or 50%",
     "0%"),
], ids=["grouped-before-comma", "scaled-before-comma", "fraction-percent", "MCK-slashed-percents"])
def test_review_round_0_a_figure_before_a_comma_or_as_a_fraction_is_read(
        value: str, quote: str, named: str) -> None:
    """(−) Review round 0: the same shapes in the VALUE were not read at all, so a figure the quote
    contradicts stood PRESENT."""
    _refused(*_one(value, quote, name="Financial-maintenance covenants"), named)


def test_review_round_0_a_clause_boundary_is_not_a_conformed_strike() -> None:
    """(−) Review round 0: the quote and a rate component's own clause were joined by a space, so
    the quote's last decimal read as a ratio STRUCK for the clause's first — "5.00x" stood PRESENT
    beside a quote stating 5.00 only as a price."""
    quote = "the purchase price shall be 5.00"
    own = "4.50 to 1.00 is the Leverage Ratio for the purposes of the Applicable Margin"
    payload = {"terms": [{"name": "Financial-maintenance covenants", "present": True,
                          "value": "Maximum Leverage Ratio of 5.00x", "quote": quote,
                          "margin_pct": 1.0, "margin_quote": own}]}
    (row,), flags, _ = ce._extract_from_exhibit(
        _FakeLlm(payload), f"Preamble. {quote}. {own}. Signatures.", name="Example Co",
        ticker="EXM", source_ref=_SRC, title="CREDIT AGREEMENT")
    _refused(row, flags, "5.00x")


@pytest.mark.parametrize(("value", "quote"), [
    ("Facility: €500 million", "an aggregate principal amount of €500,000,000"),
    ("Commitments of $5,000,000,000", "Commitments of USD 5,000,000,000"),
    ("Total Commitment $3,000,000,000", "The initial Total Commitment is U.S.$3,000,000,000."),
    # MVST, committed: a bracketed RMB figure
    ("RMB 800,000,000.00 yuan (Eight hundred million)",
     "a medium / long-term loan facility in an aggregate amount up to RMB [800,000,000.00] yuan"),
], ids=["EUR-scales", "USD-code", "U.S.$", "RMB-bracketed"])
def test_a_figure_is_compared_in_its_own_currency(value: str, quote: str) -> None:
    """(+) Review round 2: like currencies compare ($ = US$ = U.S.$ = USD), at any scale."""
    _kept(*_one(value, quote, name="Principal / commitment amount"), value)


def test_a_figure_in_another_currency_is_named_in_it_never_as_dollars() -> None:
    """(−) Review round 2: €500 million is not stated by $500,000,000, and the note names the
    figure as the value states it — never a "$" the value never wrote."""
    row, flags = _one("Facility: €500 million", "an aggregate principal amount of $500,000,000",
                      name="Principal / commitment amount")
    _refused(row, flags, "€500 million")
    assert "$500" not in (row.value.note or "")


@pytest.mark.parametrize(("value", "quote"), [
    # WERN, 8-K 0000793074-26-000120, as html_to_text reads it: struck and new figure fused
    ("Facility Limit: $350,000,000",
     "“Facility Limit” means $325,000,000350,000,000 as reduced or increased from time to time"),
    ("Commitment $15,000,000", "the Commitment shall be $ 12,000,000.00 15,000,000.00"),
], ids=["fused", "with-cents"])
def test_a_conformed_replacement_fused_or_with_cents_is_stated(value: str, quote: str) -> None:
    """(+) Review round 2: the two forms of a conformed replacement the first rule missed."""
    _kept(*_one(value, quote, name="Principal / commitment amount"), value)


@pytest.mark.parametrize(("value", "quote"), [
    ("Incremental: $300-350 million", "between $300 million and $350 million"),
    ("Incremental facilities between $250 and $500 million",
     "in an aggregate amount between $250,000,000 and $500,000,000"),
    ("Repurchases up to $500 million", "may repurchase up to $500 million of shares"),
], ids=["hyphen-range", "between-range", "dollars-of-shares"])
def test_a_range_and_a_dollar_amount_of_shares_are_read_at_their_scale(
        value: str, quote: str) -> None:
    """(+) Review round 2: a range's low side takes the high side's scale, and "$500 million of
    shares" is $500 million — a "$" makes it money whatever noun follows."""
    _kept(*_one(value, quote, name="Negative covenant"), value)


def test_a_figure_is_named_as_the_value_states_it() -> None:
    """(−) Review round 2: the flag prints "$54.6728" as stated, never rounded to cents."""
    _refused(*_one("Fee: $54.6728 per unit", "a fee per unit as set out in Schedule 2"),
             "$54.6728")


def test_a_year_fused_to_a_prefix_in_the_value_is_checked() -> None:
    """(−) Review round 2: "FY2031" in the VALUE is a year the quote must state too."""
    _refused(*_one("Notes mature FY2031", "The Notes shall mature on June 15, 2030"), "2031")


def test_a_quote_not_in_the_exhibit_keeps_its_own_reason() -> None:
    """(−) The span check runs first: a quote that is not in the exhibit is refused for THAT, and
    the value check never speaks over it."""
    row, flags = _one("June 15, 2031", "The Notes shall mature on June 15, 2030",
                      exhibit="An exhibit that holds neither clause.")
    assert (row.value.note or "").startswith(ce.REFUSED_NOTE_PREFIX)
    assert not (row.value.note or "").startswith(ce.VALUE_REFUSED_NOTE_PREFIX)
    assert any("quote is not in" in f for f in flags), flags


# --- the collapse and the page --------------------------------------------------------------------


_OLD, _NEW = "0000000001-23-000001", "0000000001-25-000002"


def _ptr(acc: str, date: str) -> CovenantPointer:
    return CovenantPointer(family="Revolving Credit Facility", filing="8-K", filing_date=date,
                           accession=acc, exhibits=["ex101.htm"])


def test_a_later_value_refusal_withholds_the_older_value_and_its_lead_says_why() -> None:
    """(−) A refusal written by the extractor is the one the collapse reads: when the NEWER exhibit
    is withheld for its value, the older one does not govern; it is the last verified value. The
    lead does not say the quote failed to match (it matched) — it says the value could not be
    verified."""
    t = "Maturity date"
    payload = {"terms": [{"name": t, "present": True, "value": "June 15, 2031",
                          "quote": "The Notes shall mature on June 15, 2030"}]}
    (later,), _, _ = ce._extract_from_exhibit(
        _FakeLlm(payload), "x The Notes shall mature on June 15, 2030 y", name="Example Co",
        ticker="EXM", source_ref=f"8-K {_NEW} · ex101.htm", title="CREDIT AGREEMENT")
    older = CovenantTerm(name=t, agreement_title="CREDIT AGREEMENT", value=Sourced.present(
        "June 15, 2028", source_ref=f"8-K {_OLD} · ex101.htm", note="verbatim: “June 15, 2028”"))
    ptrs = [_ptr(_OLD, "2023-01-05"), _ptr(_NEW, "2025-01-05")]
    (g,) = ce.governing_terms([older, later], ptrs)
    assert g.value.status is SourceStatus.UNKNOWN and g.last_verified is not None
    assert g.last_verified.value == "June 15, 2028"
    text = _refused_newer_text(g, {p.accession: p.filing_date for p in ptrs})
    assert text.startswith("UNKNOWN — not verified since 2023-01-05: a later exhibit (filed "
                           "2025-01-05) states this term, but its value could not be verified "
                           "against the filing"), text
    assert "quote could not be matched" not in text
    # the governing value's own note must not say the quote was refused either (review round 1)
    assert "quote was refused" not in (g.value.note or ""), g.value.note
    assert "2023-01-05" in (g.value.note or "") and _NEW in (g.value.note or "")


def _nke_host_with_a_value_refusal() -> dict[str, typing.Any]:
    """NKE's committed dossier with its frozen covenant block (tests/fixtures/refused_newer, main
    18d19bfb), its one LATER refusal — the 2024 credit agreement's interest row — rewritten as the
    value refusal this extractor now writes. Everything else on the page is the real type."""
    p = ROOT / "data" / "dossiers" / "NKE" / "dossier.json"
    if not p.exists():
        pytest.skip("no committed NKE dossier to host the frozen block")
    d: dict[str, typing.Any] = json.loads(p.read_text())
    cs = json.loads((ROOT / "tests/fixtures/refused_newer/NKE_capital_structure.json").read_text())
    acc = "0000320187-24-000009"
    hits = [r for r in cs["covenant_term_rows"]["value"]
            if r["name"] == "Interest / coupon rate" and acc in (r["value"].get("note") or "")]
    assert len(hits) == 1, hits
    hits[0]["value"]["note"] = (f"{ce.VALUE_REFUSED_NOTE_PREFIX} 2031, which the model's quote "
                                f"does not — 8-K {acc} · nike-364xdaycreditagreemen.htm")
    d["mechanical"]["capital_structure"] = cs
    return d


def test_the_page_leads_a_value_refusal_with_its_own_reason_e2e(tmp_path: pathlib.Path) -> None:
    """(−, py↔js) Real committed NKE page → render_markdown and the production web renderer: the
    main-body interest line LEADS with UNKNOWN and says the later exhibit's value could not be
    verified — never that its quote could not be matched — and both surfaces say the same."""
    host = _nke_host_with_a_value_refusal()
    md = render_markdown(Dossier.model_validate(host))
    lead = ("UNKNOWN — not verified since 2023-03-13: a later exhibit (filed 2024-03-11) states "
            "this term, but its value could not be verified against the filing, so it is withheld")
    line = next(ln for ln in md.splitlines()
                if ln.startswith("  - **Interest / coupon:** UNKNOWN — not verified since"))
    assert line.startswith(f"  - **Interest / coupon:** {lead}. Last verified: "), line
    assert "quote could not be matched" not in md

    page = _node_render(tmp_path, "NKE", host)
    assert lead.replace("UNKNOWN", "", 1) in page, page[:2000]
    assert "quote could not be matched" not in page


def test_a_withheld_components_clause_vouches_for_nothing() -> None:
    """(−) Review round 0: a value may state a figure from a component's own clause only when that
    component is KEPT, because the page stores only kept clauses (`component_quotes`). Here the
    clause states 2.00% but not the model's 1.75% margin, so the margin is withheld; the value's
    2.00% is refused, not vouched for by a clause the page would never cite."""
    clause = "the Applicable Margin shall be 2.00% per annum"
    payload = {"terms": [{"name": "Interest / coupon rate", "present": True,
                          "value": "Term SOFR + 2.00%",
                          "quote": "Term SOFR plus the Applicable Margin",
                          "margin_pct": 1.75, "margin_quote": clause}]}
    (row,), flags, _ = ce._extract_from_exhibit(
        _FakeLlm(payload), f"x Term SOFR plus the Applicable Margin. {clause}. y",
        name="Example Co", ticker="EXM", source_ref=_SRC, title="CREDIT AGREEMENT")
    _refused(row, flags, "2.00%")
