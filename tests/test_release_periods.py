"""Release figures carry the period THEIR OWN TEXT names — never the header's by default.

THE DEFECT, measured 2026-09-17 over the committed fleet: a reconciliation figure took its release
header's period, and a header naming a fourth quarter AND its full year ("Fourth Quarter and Full
Year 2025") fell through to the bare year. 43 rows on committed pages carried a bare year and 34 of
them were wrong. Q4 figures filed as the full year (BellRing's $117.4M, Concentrix's $378.6M,
Uber's quarterly $2.5bn, Simply Good Foods' $66.2M — the fund's position); year-to-date figures
filed as the full year (Microvast); prior-year quarters filed as a bare year, two with the
DATELINE's year (Werner "$0.53 in the prior year OMAHA, Neb., February 5, 2026" became 2026); and
the true full-year figure DROPPED as a duplicate of the Q4 row wearing its label (Par Pacific's
$633.5M). Every consumer reads a bare year as a full year: ``_fy_reconciliation`` took Simply Good
Foods' Q4 $66.2M as its FY margin input, and a synthesis would read "adjusted ebitda 2025:
113.1" for
Par Pacific.

THE FIXTURES are real exhibit text, cut at sentence or bullet boundaries and joined in filing
order. Each was verified at generation to emit, for every figure pinned here, exactly what its FULL
filing emits — so a pin cannot pass on an excerpt while production fails, which a hand-trimmed
fixture did twice while these were being cut (a join that removed a sentence break moved Uber's Q4
figure).
"""
from __future__ import annotations

from vinci.dossier import mechanical as mech
from vinci.edgar import release_parse as rp

#: 8-K 0001628280-26-011234 EX-99.1
_PARR_FY25 = (
    "PAR PACIFIC REPORTS FOURTH QUARTER AND 2025 RESULTS HOUSTON, February 24, 2026 - Par "
    "Pacific Holdings, Inc. (NYSE: PARR) (“Par Pacific” or the “Company”) today reported "
    "its financial results for the fourth quarter and twelve months ended December 31, "
    "2025. • Adjusted EBITDA of $113.1 million for the fourth quarter and $633.5 million "
    "for the full year Fourth quarter 2025 Adjusted EBITDA was $113.1 million, compared to "
    "$10.9 million in the fourth quarter of 2024. 2025 Adjusted EBITDA was $633.5 million, "
    "compared to $238.7 million for 2024."
)


#: 8-K 0001628280-25-052773 EX-99.1
_BRBR_FY25 = (
    "BellRing Brands Reports Results for the Fourth Quarter and Fiscal Year 2025; Provides "
    "Fiscal Year 2026 Outlook and Updates Long-Term Financial Algorithm St. Louis - "
    "November 18, 2025 - BellRing Brands, Inc. (NYSE:BRBR) (“BellRing”), a holding company "
    "operating in the global convenient nutrition category, today reported results for the "
    "fourth fiscal quarter and fiscal year ended September 30, 2025, provided its 2026 "
    "outlook and updated its long-term financial algorithm. Fourth Quarter and Fiscal Year "
    "2025 Highlights: • Fourth quarter net sales of $648.2 million, up 16.6% "
    "year-over-year • Fourth quarter operating profit of $102.2 million, net earnings of "
    "$59.6 million and Adjusted EBITDA* of $117.4 million • Fiscal year net sales of "
    "$2,316.6 million, up 16.1% year-over-year • Fiscal year operating profit of $357.4 "
    "million, net earnings of $216.2 million and Adjusted EBITDA* of $481.6 million"
)


#: 8-K 0001803599-26-000003 EX-99.1
_CNXC_FY25 = (
    "Concentrix Reports Fourth Quarter and Fiscal Year 2025 Results Fourth Quarter Fiscal "
    "2025 Highlights: • Revenue of $2,552.9 million, an increase of 4.3% year-on-year on "
    "an as reported basis compared to revenue of $2,448.0 million in the prior year fourth "
    "quarter. The Company grew revenue 3.1% year-on-year on a constant currency basis, "
    "exceeding the guidance range previously provided. • Adjusted EBITDA of $378.6 "
    "million, or 14.8% of revenue, compared with $402.9 million, or 16.5% of revenue, in "
    "the prior year fourth quarter. Fiscal Year 2025 Highlights: • Revenue of $9,825.8 "
    "million, an increase of 2.2% year-on-year on an as reported basis compared to revenue "
    "of $9,618.9 million in the prior fiscal year. The Company grew revenue 2.1% on a "
    "constant currency basis, which is above its guidance range previously provided. • "
    "Adjusted EBITDA of $1,469.3 million, or 15.0% of revenue, compared with $1,554.9 "
    "million, or 16.2% of revenue, in the prior fiscal year."
)


#: 8-K 0001543151-26-000011 EX-99.1
_UBER_FY25 = (
    "Uber Announces Results for Fourth Quarter and Full Year 2025 Quarterly trips grew 22% "
    "year-over-year and Gross Bookings grew 22% year-over-year Record quarterly GAAP "
    "Income from operations of $1.8 billion; Adjusted EBITDA of $2.5 billion, up 35% "
    "year-over-year Record quarterly operating cash flow of $2.9 billion and Free cash "
    "flow of $2.8 billion SAN FRANCISCO – February 4, 2026 – Uber Technologies, Inc. For "
    "Q1 2026, we anticipate: • Gross Bookings of $52.0 billion to $53.5 billion, "
    "representing growth of 17% to 21% YoY on a constant currency basis. ◦ Our outlook "
    "assumes a roughly 4 percentage-point currency tailwind to total reported YoY growth. "
    "• Non-GAAP EPS of $0.65 to $0.72, representing growth of 37% YoY at the midpoint. ◦ "
    "Our outlook translates to Adjusted EBITDA of $2.37 billion to $2.47 billion."
)


#: 8-K 0001702744-25-000043 EX-99.1
_SMPL_FY25 = (
    "The Simply Good Foods Company Reports Fiscal Fourth Quarter and Full Fiscal Year 2025 "
    "Financial Results and Provides Fiscal Year 2026 Outlook Denver, CO, October 23, 2025 "
    "- The Simply Good Foods Company (Nasdaq: SMPL) (“Simply Good Foods,” or the "
    "“Company”), a leader in the Nutritional Snacking category, today reported financial "
    "results for the thirteen and fifty-two weeks ended August 30, 2025. Fourth Quarter "
    "2025 Results (1) Net sales of $369.0 million decreased $6.6 million, or 1.8%, versus "
    "the year ago period driven by a 6.9% headwind from lapping the extra week in the "
    "fourth quarter of fiscal year 2024. Adjusted EBITDA of $66.2 million decreased 14.5% "
    "versus $77.5 million in the comparable year ago period. Fiscal Year 2025 Summary: • "
    "Net sales were $1,450.9 million versus $1,331.3 million • Net income of $103.6 "
    "million versus $139.3 million • Earnings per diluted share of $1.02 versus $1.38 • "
    "Adjusted Diluted EPS (2) of $1.92 versus $1.83 • Adjusted EBITDA (3) of $278.2 "
    "million versus $269.1 million Net sales of $1,450.9 million increased 9.0% versus the "
    "comparable year ago period driven by the 7.9% contribution from the OWYN Acquisition "
    "and 3.0% organic growth. 2 Adjusted EBITDA of $278.2 million increased 3.4% versus "
    "$269.1 million in the comparable year ago period."
)


#: 8-K 0001702744-25-000035 EX-99.1
_SMPL_Q3FY25_YTD = (
    "The Simply Good Foods Company Reports Fiscal Third Quarter 2025 Financial Results "
    "Year-to-Date Third Quarter Fiscal Year 2025 Summary: • Net sales of $1,081.9 million "
    "versus $955.6 million • Net income of $116.0 million versus $110.0 million • Earnings "
    "per diluted share (“EPS”) of $1.14 versus $1.09 • Adjusted Diluted EPS of $1.46 "
    "versus $1.33 • Adjusted EBITDA of $211.9 million versus $191.7 million Net sales of "
    "$1,081.9 million increased 13.2% versus the comparable year ago period."
)


#: 8-K 0001628280-26-055471 EX-99.1
_MVST_Q2_26_YTD = (
    "Microvast Reports Second Quarter 2026 Financial Results Houston, Texas, USA — "
    "Microvast Holdings, Inc. • Non-GAAP adjusted EBITDA* of negative $1.9 million in YTD "
    "2026, compared to non-GAAP adjusted EBITDA* of $54.4 million in YTD 2025."
)


#: 8-K 0000793074-26-000092 EX-99.1
_WERN_Q1_26 = (
    "Werner Enterprises Reports First Quarter 2026 Results First Quarter 2026 Highlights "
    "(all metrics compared to first quarter 2025 ) • Total revenues of $808.6 million, "
    "increased $96.5 million, or 14% • Operating income was $4.0 million compared to a "
    "$5.8 million operating loss in the prior year; non-GAAP adjusted operating income of "
    "$11.9 million compared to non-GAAP adjusted operating loss of $1.8 million in the "
    "prior year • Operating margin of 0.5%, increased 130 basis points from (0.8)%; "
    "non-GAAP adjusted operating margin of 1.5%, increased 180 basis points from (0.3)% • "
    "Diluted loss per share was $0.07 compared to diluted loss per share of $0.16 in the "
    "prior year; non-GAAP adjusted diluted earnings per share was $0.02 compared to "
    "non-GAAP adjusted diluted loss per share of $0.12 in the prior year OMAHA, Neb., "
    "April 28, 2026 -- Werner Enterprises, Inc. • Operating income was $4.0 million "
    "compared to a $5.8 million operating loss in the prior year; non-GAAP adjusted "
    "operating income of $11.9 million compared to non-GAAP adjusted operating loss of "
    "$1.8 million in the prior year • Operating margin of 0.5%, increased 130 basis points "
    "from (0.8)%; non-GAAP adjusted operating margin of 1.5%, increased 180 basis points "
    "from (0.3)% • Diluted loss per share was $0.07 compared to diluted loss per share of "
    "$0.16 in the prior year; non-GAAP adjusted diluted earnings per share was $0.02 "
    "compared to non-GAAP adjusted diluted loss per share of $0.12 in the prior year "
    "OMAHA, Neb., April 28, 2026 -- Werner Enterprises, Inc. Werner Logistics had "
    "operating loss of $2.0 million compared to $0.5 million operating loss in the prior "
    "year, and Werner Logistics had a non-GAAP adjusted operating loss of $0.9 million, "
    "compared to Non-GAAP adjusted operating income of $0.7 million in the prior year."
)


#: 8-K 0000793074-26-000009 EX-99.1
_WERN_FY25 = (
    "Werner Enterprises Reports Fourth Quarter and Annual 2025 Results Fourth Quarter 2025 "
    "Highlights (all metrics compared to fourth quarter 2024) • Total revenues of $737.6 "
    "million, decreased $17.0 million, or 2% • Operating loss was $35.8 million compared "
    "to $13.4 million operating income in the prior year; non-GAAP adjusted operating "
    "income of $11.3 million, down $0.9 million, or 8% • Operating margin of (4.9)%, "
    "decreased 670 basis points from 1.8%; non-GAAP adjusted operating margin of 1.5%, "
    "decreased 10 basis points from 1.6% • Diluted loss per share was $0.46 compared to "
    "diluted earnings per share of $0.19 in the prior year; non-GAAP adjusted diluted "
    "earnings per share was $0.05, down 29% 2025 Highlights (all metrics compared to 2024) "
    "• Total revenues of $2.97 billion, decreased $55.9 million, or 2% • Operating income "
    "of $11.7 million, down $54.5 million, or 82%; non-GAAP adjusted operating income of "
    "$37.0 million, down $36.7 million, or 50% • Operating margin of 0.4%, decreased 180 "
    "basis points from 2.2%; non-GAAP adjusted operating margin of 1.2%, decreased 120 "
    "basis points from 2.4% • Diluted loss per share was $0.24 compared to diluted "
    "earnings per share of $0.55 in the prior year; non-GAAP adjusted diluted loss per "
    "share was $0.02 compared to non-GAAP adjusted diluted earnings per share of $0.53 in "
    "the prior year OMAHA, Neb., February 5, 2026 -- Werner Enterprises, Inc."
)


#: 8-K 0001193125-26-336692 EX-99.1
_VITL_Q2_26 = (
    "Vital Farms Reports Second Quarter 2026 Financial Results Second Quarter Net Revenue "
    "of $166.0 Million Announces Successful Execution of Previously Disclosed Supply "
    "Control and Targeted Cost Savings Initiatives Grew Retail Dollar Share of the Shell "
    "Egg Category by More Than 200 Basis Points Year-Over-Year, Even as Category Pricing "
    "Fell Sharply Amid Industry-Wide Oversupply Announces New Aggregate $185 Million "
    "Credit Facilities, Fortifying Financial Flexibility Announces Termination of Stock "
    "Repurchase Program Reiterates Fiscal Year 2026 Net Revenue Outlook of $775 Million to "
    "$800 Million and Adjusted EBITDA Outlook of $0 Million to $10 Million AUSTIN, TX – "
    "August 6, 2026 – Vital Farms (Nasdaq: VITL), a Certified B Corporation that offers a "
    "range of ethically produced foods nationwide, today reported financial results for "
    "its second quarter ended June 28, 2026. Adjusted net loss was $20.0 million for the "
    "second quarter of 2026, compared to adjusted net income of $16.6 million in the "
    "prior-year quarter. Adjusted EBITDA was a loss of $26.6 million in the second quarter "
    "of 2026, compared to Adjusted EBITDA of $29.9 million in the second quarter of 2025."
)


#: 8-K 0001493152-26-015252 EX-99.1
_FUBO_FORECAST = (
    "FUBO RELEASES ADJUSTED EBITDA OUTLOOK AND LONG-TERM FINANCIAL TARGETS Co-Founder & "
    "CEO David Gandler Issues Shareholder Letter NEW YORK – APRIL 6, 2026 – FuboTV Inc. "
    "(NYSE: FUBO) today announced Adjusted EBITDA outlook for Fiscal 2026 and 2028 and "
    "affirmed its cash forecast. We currently expect: ● Fiscal 2026 Pro Forma Adjusted "
    "EBITDA of $80-100 million."
)


#: 8-K 0001193125-26-067015 EX-99.1
_VRRM_FY25 = (
    "Verra Mobility Announces Fourth Quarter and Full Year 2025 Financial Results Fourth "
    "Quarter 2025 Financial Highlights • Revenue : Total revenue for the fourth quarter of "
    "2025 was $257.9 million, an increase of 16% compared to $221.5 million for the fourth "
    "quarter of 2024. • Adjusted EBITDA* : Adjusted EBITDA was $101.8 million for the "
    "fourth quarter of 2025 compared to $102.0 million for the same period in 2024. Fourth "
    "Quarter 2025 Segment Detail • The Commercial Services segment generated total revenue "
    "of $108.1 million, a 10% increase compared to $98.7 million in the same period in "
    "2024. Segment profit was $69.1 million, a 7% increase from $64.6 million in the prior "
    "year period. Full Year 2025 Financial Highlights • Revenue : Total revenue for fiscal "
    "year 2025 was $979.1 million, an increase of 11% compared to $879.2 million for "
    "fiscal year 2024. • Adjusted EBITDA* : Adjusted EBITDA was $415.9 million for fiscal "
    "year 2025 compared to $401.6 million for fiscal year 2024."
)


#: 8-K 0001193125-26-073373 EX-99.1
_VITL_FY25 = (
    "Vital Farms Reports Fourth Quarter and Fiscal Year 2025 Financial Results Financial "
    "highlights for the fourth quarter ended December 28, 2025, compared to the fourth "
    "quarter ended December 29, 2024, include: • Net Revenue increased 28.7% to $213.6 "
    "million, compared to $166.0 million • Gross Margin of 35.8%, compared to 36.1% • Net "
    "Income of $16.3 million, compared to $10.6 million • Net Income per Diluted Share of "
    "$0.35, compared to $0.23 • Adjusted EBITDA of $29.2 million, compared to $19.1 "
    "million 1 Financial highlights for the fiscal year ended December 28, 2025, compared "
    "to the fiscal year ended December 29, 2024, include: Net income per diluted share was "
    "$0.35 for the fourth quarter of 2025, compared to net income per diluted share of "
    "$0.23 in the fourth quarter of 2024. Adjusted EBITDA was $29.2 million, or 13.7% of "
    "net revenue, in the fourth quarter of 2025, compared to $19.1 million, or 11.5% of "
    "net revenue, in the fourth quarter of 2024. Net income per diluted share was $1.44 "
    "for fiscal year 2025, compared to net income per diluted share of $1.18 in fiscal "
    "year 2024. Adjusted EBITDA was $114.0 million, or 15.0% of net revenue, in fiscal "
    "year 2025, compared to $86.7 million, or 14.3% of net revenue, in fiscal year 2024."
)


#: 8-K 0001352010-26-000010 EX-99.1
_EPAM_FY25 = (
    "EPAM Reports Results for Fourth Quarter and Full Year 2025 Fourth Quarter 2025 • "
    "Revenues of $1.408 billion, up 12.8% year-over-year • GAAP Income from Operations was "
    "10.6% of revenues and Non-GAAP Income from Operations was 16.3% of revenues • GAAP "
    "Diluted EPS of $1.98, an increase of 10.0%, and Non-GAAP Diluted EPS of $3.26, an "
    "increase of 14.8% on a year-over-year basis Full Year 2025 • Revenues of $5.457 "
    "billion, up 15.4% year-over-year • Non-GAAP diluted EPS was $11.50, an increase of "
    "$0.64, or 5.9%, compared to $10.86 in 2024."
)


#: 8-K 0001493152-26-036098 EX-99.1
_FUBO_Q3_26 = (
    "August 5, 2026 Fellow Shareholders: I am honored to be writing to you as FuboTV’s 1 "
    "new Chief Executive Officer. Q3 Fiscal 2026 Highlights To facilitate comparability "
    "between periods, the following presents FuboTV’s Q3 fiscal 2026 results compared to "
    "FuboTV’s results for the corresponding three month period ended June 30, 2025 (“Q3 "
    "fiscal 2025”) on an as-reported basis and pro forma basis, which gives effect to the "
    "Company’s business combination with Hulu + Live TV as if it had been completed at the "
    "beginning of the first period presented. ● Revenue of $1.482 billion, compared to "
    "$1.074 billion in Q3 fiscal 2025 ○ Compared to Q3 fiscal 2025 Pro Forma Revenue of "
    "$1.484 billion"
)


#: 8-K 0001493152-26-004826 EX-99.1
_FUBO_Q1_26 = (
    "February 3, 2026 Fellow Shareholders: Fiscal 2026 marks a step change in our "
    "trajectory. Q1 Fiscal 2026 Highlights To facilitate comparability between periods, "
    "the following presents our Q1 fiscal 2026 results compared to Q1 fiscal 2025 results "
    "on an as-reported basis and pro forma basis, which gives effect to the Company’s "
    "business combination with Hulu + Live TV as if it had been completed at the beginning "
    "of the first period presented. 1 ● Reported Revenue of $1.549 billion, compared to "
    "$1.106 billion (up 40% Y/Y) ● Pro Forma Revenue of $1.683 billion, compared to $1.588 "
    "billion (up 6% Y/Y) ● Total North America (NA) Subscribers of 6.2 million, compared "
    "to 6.3 million 1 As-reported financial results and information included herein, "
    "including historical periods and a portion of the current period, (x) reflect the "
    "results of the Hulu Live Business prepared on a carve-out basis, excluding the "
    "results of the historical Fubo business, for periods prior to October 29, 2025 (the "
    "“Closing Date”) and (y) the results of the combined Fubo and Hulu Live businesses as "
    "of and after the Closing Date. See “Basis of Presentation” and “Reconciliation of Key "
    "Performance Metrics and Non-GAAP Financial Measures” for further information. 1 ● "
    "Reported Net Loss of $19.1 million, compared to $38.6 million ● Pro Forma Net Loss of "
    "$46.4 million, compared to $130.4 million ● Pro Forma Adjusted EBITDA 2 of $41.4 "
    "million, compared to $22.0 million ● Cash Position: Fubo ended the quarter with "
    "$458.6 million in cash, cash equivalents and restricted cash on hand. ● Over the "
    "trailing twelve months: ○ Reported Revenue of $4.9 billion, and Pro Forma Revenue of "
    "$6.2 billion ○ Reported Net Loss of $136.8 million, and Pro Forma Net Loss of $94.0 "
    "million ○ Pro Forma Adjusted EBITDA of $77.9 million"
)


def _rows(text: str) -> set[tuple[str, str, float]]:
    return {(v.metric, v.period, v.value)
            for v in rp.parse_release(text, source_ref="t").reconciliation}


def _values(text: str) -> set[tuple[str, float]]:
    return {(m, v) for m, _, v in _rows(text)}


# --- the header: a combined release names TWO periods --------------------------------------------
def test_a_fourth_quarter_and_full_year_header_is_combined_not_a_bare_year() -> None:
    """Every real combined header in the fleet, each of which fell through to the bare year."""
    for header in ("PAR PACIFIC REPORTS FOURTH QUARTER AND 2025 RESULTS",
                   "Westlake Corporation Reports Fourth Quarter and Full Year 2025 Results",
                   "Concentrix Reports Fourth Quarter and Fiscal Year 2025 Results",
                   "The Simply Good Foods Company Reports Fiscal Fourth Quarter and Full Fiscal "
                   "Year 2025 Financial Results",
                   "Uber Announces Results for Fourth Quarter and Full Year 2025",
                   "BellRing Brands Reports Results for the Fourth Quarter and Fiscal Year 2025",
                   "Werner Enterprises Reports Fourth Quarter and Annual 2025 Results"):
        frame = rp._release_frame(header)
        assert (frame.kind, frame.quarter, frame.year) == ("combined", 4, "2025"), header
        assert rp._release_period(header) == "Q4 2025", header


def test_single_period_headers_are_unchanged() -> None:
    assert rp._release_frame("Par Pacific Reports Second Quarter 2026 Results").kind == "quarter"
    assert rp._release_frame("Microvast Reports 2025 Financial Results").kind == "annual"


# --- Q4 and FY side by side: each figure keeps its own period, and neither is dropped ------------
def test_par_pacific_q4_is_the_quarter_and_the_full_year_is_no_longer_dropped() -> None:
    rows = _rows(_PARR_FY25)
    assert ("adjusted ebitda", "Q4 2025", 113.1) in rows
    assert ("adjusted ebitda", "2025", 633.5) in rows  # was DROPPED as a duplicate of the Q4 row


def test_bellring_bullets_led_by_their_period_word() -> None:
    rows = _rows(_BRBR_FY25)
    assert ("adjusted ebitda", "Q4 2025", 117.4) in rows
    assert ("adjusted ebitda", "2025", 481.6) in rows


def test_concentrix_section_headings_and_prior_year_quarter_comparison() -> None:
    rows = _rows(_CNXC_FY25)
    assert {("adjusted ebitda", "Q4 2025", 378.6), ("adjusted ebitda", "2025", 1469.3),
            ("revenue", "Q4 2025", 2552.9), ("revenue", "Q4 2024", 2448.0),
            ("revenue", "2025", 9825.8)} <= rows


def test_uber_quarterly_figure_and_its_outlook_is_not_an_actual() -> None:
    """"Non-GAAP EPS of $0.65 to $0.72" under "For Q1 2026, we anticipate:" was stored as $0.60.
    (2026-10-22) And "Adjusted EBITDA of $2.5 billion" is $2,500M — this pin held 2.5, the
    unscaled-billions defect frozen as an expectation."""
    assert ("adjusted ebitda", "Q4 2025", 2500.0) in _rows(_UBER_FY25)
    assert not any(m == "adjusted eps" for m, _ in _values(_UBER_FY25))


def test_simply_good_foods_quarter_section_and_fiscal_year_summary() -> None:
    rows = _rows(_SMPL_FY25)
    assert ("adjusted ebitda", "Q4 2025", 66.2) in rows
    assert ("adjusted ebitda", "2025", 278.2) in rows


def test_the_consumer_receives_the_true_full_year_not_the_fourth_quarter() -> None:
    """THE CONSEQUENCE, not the helper: ``_fy_reconciliation`` is the full-year margin input."""
    for text, fy in ((_PARR_FY25, 633.5), (_BRBR_FY25, 481.6), (_CNXC_FY25, 1469.3),
                     (_SMPL_FY25, 278.2), (_VRRM_FY25, 415.9)):
        got = mech._fy_reconciliation([rp.parse_release(text, source_ref="t")])
        assert got.get("adjusted ebitda") == fy, (fy, got)


def test_a_combined_release_figure_with_no_period_of_its_own_is_not_filed_as_the_year() -> None:
    """THE ORIGINAL DEFECT in its purest shape. Vital Farms' combined release lists "• Gross Margin
    of 35.8%, compared to 36.1%" with no period in the bullet and no section heading above it, so
    the header was the only evidence — and it named two periods. The Q4 margin was filed as FY2025;
    it is now left unlabelled rather than guessed."""
    assert not any(m == "gross margin" and v == 35.8 for m, _, v in _rows(_VITL_FY25))


# --- year-to-date is not a period any consumer reads ---------------------------------------------
def test_year_to_date_figures_are_not_labelled() -> None:
    """Microvast "negative $1.9 million in YTD 2026, compared to … $54.4 million in YTD 2025" — the
    $54.4M stood on its page as FY2025. Simply Good Foods' 39-week $211.9M sat under a
    "Year-to-Date Third Quarter Fiscal Year 2025 Summary" whose hyphenated word hid the YTD."""
    assert not ({("adjusted ebitda", 54.4), ("adjusted ebitda", -1.9)} & _values(_MVST_Q2_26_YTD))
    assert ("adjusted ebitda", 211.9) not in _values(_SMPL_Q3FY25_YTD)


# --- comparisons take the period THEIR clause names ----------------------------------------------
def test_a_prior_year_comparison_never_takes_the_dateline_year() -> None:
    """Werner: "…loss per share of $0.12 in the prior year OMAHA, Neb., April 28, 2026" was 2026."""
    assert ("adjusted eps", "Q1 2025", -0.12) in _rows(_WERN_Q1_26)


def test_the_prior_year_quarter_is_a_quarter_not_a_year() -> None:
    rows = _rows(_VITL_Q2_26)
    assert ("adjusted net income", "Q2 2025", 16.6) in rows  # "in the prior-year quarter" was 2026
    assert ("adjusted ebitda", "Q2 2025", 29.9) in rows  # "in the second quarter of 2025" was 2025


def test_the_next_sections_heading_does_not_bleed_into_the_last_bullet() -> None:
    """Werner's Q4 EPS bullet ends "$0.05, down 29%" and stripped HTML runs straight into "2025
    Highlights (all metrics compared to 2024)" — which read the Q4 figure as the full year."""
    rows = _rows(_WERN_FY25)
    assert ("adjusted eps", "Q4 2025", 0.05) in rows
    assert ("adjusted eps", "2025", -0.02) in rows


def test_a_trailing_period_counts_only_when_a_preposition_introduces_it() -> None:
    """EPAM's Q4 bullet runs straight into the next section: "Non-GAAP Diluted EPS of $3.26, an
    increase of 14.8% on a year-over-year basis Full Year 2025 • Revenues…". Read as the Q4 EPS's
    own period, "Full Year 2025" filed $3.26 as FY2025 and pushed out the true $11.50."""
    rows = _rows(_EPAM_FY25)
    assert ("adjusted eps", "2025", 11.5) in rows
    assert ("adjusted eps", "2025", 3.26) not in rows


def test_an_actual_cannot_postdate_the_release_that_reports_it() -> None:
    """Vital Farms' Q4 list ends "Adjusted EBITDA of $29.2 million, compared to $19.1 million 1" and
    runs into "Financial highlights for the fiscal year ended December 28, 2025…" — which made the
    comparison fiscal 2025 and the Q4 figure fiscal 2026, in a release reporting 2025."""
    assert not any(period == "2026" for _, period, _ in _rows(_VITL_FY25))


def test_a_comparison_marker_far_before_its_metric_still_makes_a_comparison() -> None:
    """FuboTV: "○ Compared to Q3 fiscal 2025 Pro Forma Revenue of $1.484 billion" puts 36 characters
    between the marker and the metric; a 26-character look-back missed it, and under the section
    heading "Q3 Fiscal 2026 Highlights" the prior-year value was filed as the current quarter. The
    same heading, read with letters-only words, had been "Fiscal 2026" — a full-year section.
    (2026-10-22) The comparison is PRO FORMA revenue — the combined company's, not fuboTV's — and
    is now refused as a sub-line rather than stored as Q3 2025 revenue; either way it never takes
    the current quarter's slot. The figures are $M (they were stored unscaled, 1.482)."""
    rows = _rows(_FUBO_Q3_26)
    assert ("revenue", "Q3 2026", 1482.0) in rows
    assert not any(v == 1484.0 for _m, _p, v in rows)  # the pro forma figure, under no period
    assert ("revenue", "2026", 1484.0) not in rows


def test_quarter_and_fiscal_year_prose_each_keep_their_own_period() -> None:
    """Vital Farms states each figure with its own period, in its highlights list and again in prose
    ("…in the fourth quarter of 2025", "…in fiscal year 2025"). Neither may take the other's slot:
    the list's Q4 $29.2M, filed as FY2025, pushed out the true $114.0M."""
    rows = _rows(_VITL_FY25)
    assert ("adjusted ebitda", "Q4 2025", 29.2) in rows
    assert ("adjusted ebitda", "2025", 114.0) in rows
    assert ("adjusted ebitda", "2025", 29.2) not in rows


def test_a_section_heading_that_names_its_quarter_with_a_digit_is_that_quarter() -> None:
    """FuboTV heads its highlights "Q1 Fiscal 2026 Highlights", and neither figure below it states a
    period of its own. Reading heading words as letters only broke the run at "Q1" and left "Fiscal
    2026 Highlights" — a full-year section — so both Q1 figures were filed as fiscal 2026.

    (audit E2-D5) The quarter's adjusted EBITDA is "Pro Forma Adjusted EBITDA 2 of $41.4 million" —
    a footnote digit after the name. This pin asserted $77.9M, the "● Over the trailing twelve
    months: ○ … of $77.9 million" figure that took the slot while the digit was refused."""
    rows = _rows(_FUBO_Q1_26)
    assert ("revenue", "Q1 2026", 1549.0) in rows  # "$1.549 billion", in $M since 2026-10-22
    assert ("adjusted ebitda", "Q1 2026", 41.4) in rows
    assert not any(v == 77.9 for _m, _p, v in rows)  # the trailing twelve months, under no period


# --- what must not become a labelled actual ------------------------------------------------------
def test_a_segments_comparison_is_not_the_companys() -> None:
    """"Werner Logistics had a non-GAAP adjusted operating loss of $0.9 million, compared to …
    income of $0.7 million in the prior year" follows the company's own $11.9M — so the $0.7M is
    one segment's."""
    rows = _rows(_WERN_Q1_26)
    assert ("adjusted operating income", "Q1 2026", 11.9) in rows
    assert ("adjusted operating income", 0.7) not in _values(_WERN_Q1_26)


def test_a_segment_revenue_line_is_not_company_revenue() -> None:
    assert ("revenue", 108.1) not in _values(_VRRM_FY25)
    rows = _rows(_VRRM_FY25)
    assert ("adjusted ebitda", "Q4 2025", 101.8) in rows
    assert ("adjusted ebitda", "2025", 415.9) in rows


def test_an_outlook_list_is_not_reported_results() -> None:
    """FuboTV's "We currently expect: ● Fiscal 2026 Pro Forma Adjusted EBITDA of $80-100 million"
    list is an outlook; its first number must not stand as a reported figure."""
    assert not any(m == "adjusted ebitda" for m, _ in _values(_FUBO_FORECAST))


# --- a bare excerpt with no period information keeps its historical empty label ------------------
def test_text_with_no_period_information_at_all_stays_unlabelled_not_skipped() -> None:
    assert _rows("Adjusted EBITDA* of $53.8 million.") == {("adjusted ebitda", "", 53.8)}


# --- review fixes (PR #622), pinned on REAL exhibit text ----------------------------------------
# Each shape was measured on 582 EX-99.1 exhibits pulled from EDGAR full-text search, parsed with
# and without each fix; every row a fix moved was read against its sentence (record of 2026-09-17).
# The excerpts below were checked at generation to emit, for every pinned figure, what the full
# filing emits, and nothing the full filing does not.

#: 8-K 0001193125-25-269654 EX-99.1
_ORGO_Q3_25 = (
    "Organogenesis Holdings Inc. Reports Third Quarter 2025 Financial Results, Posts Record "
    "Revenue and Raises 2025 Guidance CANTON, Mass., (November 6, 2025) -- Organogenesis "
    "Holdings Inc. (Nasdaq: ORGO), a leading regenerative medicine company focused on the "
    "development, manufacture, and commercialization of product solutions for the Advanced "
    "Wound Care and Surgical & Sports Medicine markets, today reported financial results for "
    "the third quarter ended September 30, 2025. Third Quarter 2025 Financial Results "
    "Summary: • Net product revenue of $150.5 million for the third quarter of 2025, an "
    "increase of $35.3 million compared to net product revenue of $115.2 million for the "
    "third quarter of 2024."
)


#: 8-K 0001437749-26-004457 EX-99.1
_BLIN_Q1_26 = (
    "Bridgeline Announces Financial Results for the First Quarter of Fiscal 2026 Woburn, "
    "Mass. - Bridgeline Digital, Inc. (NASDAQ: BLIN ), ● Gross margin was 66% for the quarter"
    " ended December 31, 2025, as compared to 67% for the same period last year."
)


#: 8-K 0001437749-26-025436 EX-99.1
_IRT_Q2_26 = (
    "Independence Realty Trust Announces Second Quarter 2026 Financial Results PHILADELPHIA –"
    " (BUSINESS WIRE) – August 3, 2026 — Independence Realty Trust, Inc. (“IRT”) (NYSE: IRT),"
    " • Adjusted EBITDA of $90.3 million for the quarter ended June 30, 2026 compared to "
    "$87.6 million for the quarter ended June 30, 2025 ."
)


#: 8-K 0001841125-25-000154 EX-99.1
_BOLT_Q3_25 = (
    "BOLT PROJECTS HOLDINGS REPORTS Q3 2025 FINANCIAL RESULTS ● Bolt delivered revenue of "
    "$0.4 million in Q3 2025 , up 7,300% year-over-year. This implies fourth quarter gross "
    "margins in excess of 40%, well on track toward our target gross margin of 60%."
)


#: 8-K 0001324404-26-000003 EX-99.1
_CF_FY25 = (
    "CF Industries Holdings, Inc. Reports Full Year 2025 Net Earnings of $1.46 Billion, "
    "Adjusted EBITDA of $2.89 Billion • Full year 2025 net earnings (1) of $1.46 billion, or "
    "$8.97 per diluted share, EBITDA (2) of $2.78 billion, and adjusted EBITDA (2) of $2.89 "
    "billion • Fourth quarter 2025 net earnings of $404 million, or $2.59 per diluted share, "
    "EBITDA of $731 million, and adjusted EBITDA of $821 million"
)


#: 8-K 0001104659-26-013423 EX-99.1
_AM_FY25 = (
    "Antero Midstream Announces Fourth Quarter 2025 Results and 2026 Guidance Denver, "
    "Colorado, February 11, 2026—Antero Midstream Corporation (NYSE: AM) (“Antero Midstream” "
    "or the “Company”) today announced its fourth quarter 2025 financial and operating "
    "results and 2026 guidance. The Company is forecasting Adjusted EBITDA of $1.19 to $1.24 "
    "billion, which represents an 8% increase compared to 2025 at the midpoint. Adjusted "
    "EBITDA was $285 million, a 4% increase compared to the prior year quarter."
)


#: 8-K 0001104659-26-010898 EX-99.1
_RBBN_FY25 = (
    "Ribbon Communications Inc. Reports Fourth Quarter and Full Year 2025 Financial Results "
    "Strong Cash Flow · Revenue was $227 million, compared to $251 million for the fourth "
    "quarter of 2024 · GAAP Operating Income was $9 million, compared to $33 million for the "
    "fourth quarter of 2024 · Non-GAAP Adjusted EBITDA was $40 million, compared to $55 "
    "million for the fourth quarter of 2024 · GAAP Gross Margin was 53.3%, compared to 55.7% "
    "for the fourth quarter of 2024"
)


#: 8-K 0000749251-26-000028 EX-99.1
_IT_Q4_25 = (
    "Gartner Reports Fourth Quarter 2025 Financial Results Contract Value $5.2 billion, +1% "
    "YoY FX Neutral FOURTH QUARTER 2025 HIGHLIGHTS • Revenues: $1.8 billion, +2% as reported "
    "and unchanged FX neutral. • Net income: $242 million, -39%; adjusted EBITDA: $436 "
    "million, +5% as reported, +1% FX neutral."
)


def test_a_change_amount_before_the_comparison_is_not_read_as_a_sub_unit() -> None:
    """Organogenesis: "$150.5 million for the third quarter of 2025, an increase of $35.3 million
    compared to net product revenue of $115.2 million for the third quarter of 2024". The sub-unit
    test read the $35.3M DELTA as the clause's current figure, found it unequal to the $150.5M the
    release stated, and dropped the company's own prior-year quarter. A real segment's comparison
    still goes (Werner Logistics' $0.7M)."""
    rows = _rows(_ORGO_Q3_25)
    assert ("revenue", "Q3 2025", 150.5) in rows
    assert ("revenue", "Q3 2024", 115.2) in rows
    assert ("adjusted operating income", 0.7) not in _values(_WERN_Q1_26)


def test_a_fiscal_quarter_ended_date_takes_the_fiscal_year_not_the_calendar_year() -> None:
    """Bridgeline's first quarter of FISCAL 2026 is the quarter ended December 31, 2025, and the
    date's calendar year filed its gross margin as Q1 2025 — the prior year's quarter. A calendar
    filer's date and year agree and stay put (Independence Realty Trust, June 30, 2026)."""
    assert ("gross margin", "Q1 2026", 66.0) in _rows(_BLIN_Q1_26)
    assert ("adjusted ebitda", "Q2 2026", 90.3) in _rows(_IRT_Q2_26)


def test_projects_in_a_name_is_not_a_forecast_but_a_target_still_is() -> None:
    """Bolt PROJECTS Holdings: the noun in the company's own name read as the verb and dropped its
    reported Q3 revenue. In the same release "our target gross margin of 60%" is a goal — taking
    'target' out of the forward words with 'projects' filed it as the fourth quarter's actual."""
    assert ("revenue", "Q3 2025", 0.4) in _rows(_BOLT_Q3_25)
    assert not any(m == "gross margin" for m, _ in _values(_BOLT_Q3_25))


def test_a_forecast_in_any_form_is_not_a_reported_figure() -> None:
    """Antero Midstream: "The Company is forecasting Adjusted EBITDA of $1.19 to $1.24 billion" —
    'forecasts?' missed 'forecasting', so the range's first number stood as Q4's actual and took
    the slot the real "$285 million" needed."""
    assert ("adjusted ebitda", "Q4 2025", 285.0) in _rows(_AM_FY25)
    assert not any(m == "adjusted ebitda" and v < 10 for m, v in _values(_AM_FY25))


def test_a_middle_dot_bullet_ends_the_clause_before_it() -> None:
    """Ribbon writes its highlights as "·" bullets. Without that glyph as a clause edge each bullet
    ran into the one before it, whose "compared to … for the fourth quarter of 2024" made the next
    CURRENT figure a prior-year one: Q4 2025's $40 million adjusted EBITDA and 53.3% gross margin
    were both filed as Q4 2024."""
    rows = _rows(_RBBN_FY25)
    assert ("adjusted ebitda", "Q4 2025", 40.0) in rows
    assert ("gross margin", "Q4 2025", 53.3) in rows
    assert not any(p == "Q4 2024" for _, p, _ in rows)


def test_ltm_ending_a_fourth_quarter_is_that_full_year() -> None:
    """The LTM ending Q4 of Y IS FY(Y): refusing every Q4 left a name 'LTM unavailable' through its
    whole fourth-quarter window (Verra Mobility: FY2025 $415.9M beside its Q4 $101.8M). A Q4 with no
    full-year figure returns nothing (Gartner).

    CF INDUSTRIES (2026-10-22). This pin held "$2.89 billion" as 2.89 beside an $821 million Q4 and
    called the pair "a unit mismatch, not an LTM" — the unscaled-billions defect, frozen as the
    expectation. Scaled, FY2025 is $2,890M and IS the LTM ending its Q4."""
    def ltm(text: str) -> float | None:
        return mech._ltm_adj_ebitda([rp.parse_release(text, source_ref="t")])

    assert ltm(_VRRM_FY25) == 415.9
    cf = _rows(_CF_FY25)
    assert {("adjusted ebitda", "2025", 2890.0), ("adjusted ebitda", "Q4 2025", 821.0)} <= cf
    assert ltm(_CF_FY25) == 2890.0
    assert ("adjusted ebitda", "Q4 2025", 436.0) in _rows(_IT_Q4_25)
    assert ltm(_IT_Q4_25) is None
