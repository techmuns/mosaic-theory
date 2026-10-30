"""A release figure's SPAN, its release's FRAME and its gross margin's BASIS are read as stated
(audit E2-D4, D6, D9; Phase 2 batch B2).

  D4  SPAN. A nine- or six-month figure was filed as the quarter: a section heading "Nine Months
      Highlights" / "Six Month Operating Results" / "Nine-Month Results" was not read as a
      year-to-date span (`_PHRASE` needed "… months ENDED"; `_PERIOD_WORD` had no "month"), and a
      bullet run's year-to-date lead-in was read only for a trailing-twelve-month span.
  D6  FRAME. `_release_frame` took the first quarter phrase in the release's head, and Amazon's
      head carries its comparison first — "compared with $167.7 billion in second quarter 2025" —
      so both 2026 releases framed as 2025.
  D9  BASIS. "Non-GAAP gross margin was 47.0%" was stored as the GAAP gross margin, and the first
      gross-margin statement was the only one read, so a GAAP figure after a year-to-date or a
      non-GAAP one was never reached.

The constructed sentences are the audit's probes (A5–A7, A9–A11,
`data/session-notes/audit-verification/E2.md`). Every real-text fixture quotes a filed EX-99.1
verbatim (whitespace collapsed); two fragments of one filing are joined where a test says so.
"""
from __future__ import annotations

import pytest

from vinci.edgar import release_parse as rp
from vinci.edgar.release_parse import parse_release

_SRC = "8-K 0000000000-26-000001 EX-99.1"


def _actuals(text: str) -> list[tuple[str, str, float]]:
    return [(x.metric, x.period, x.value)
            for x in parse_release(text, source_ref=_SRC).reconciliation]


# --- D4: a year-to-date section is not the quarter -----------------------------------------------
A5 = ("Acme Reports Third Quarter 2026 Results. Third Quarter Highlights • Revenue increased 10% "
      "to $100.0 million. Nine Months Highlights • Revenue of $290.0 million, up 8%.")
A6 = ("Acme Reports Second Quarter 2026 Results. Second Quarter Highlights • Adjusted EBITDA "
      "increased to $20.0 million. Six Months Highlights • Adjusted EBITDA of $38.0 million, "
      "up 5%.")
A7 = ("Acme Reports Third Quarter 2026 Results. Third Quarter Highlights • Net sales rose 4%. "
      "Nine-Month Results • Adjusted EBITDA of $55.0 million.")


def test_a_figure_under_a_year_to_date_heading_is_not_the_quarter() -> None:
    for text, value in ((A5, 290.0), (A6, 38.0), (A7, 55.0)):
        assert [a for a in _actuals(text) if a[2] == value] == [], text


#: BellRing, 8-K 0001628280-26-052137 EX-99.1: its head, and its "Nine Month Operating Results"
#: heading joined to that section's adjusted-EBITDA sentence (two verbatim fragments). In the full
#: release main labels the $222.4M nine-month figure Q3 2026 and then drops it only because the
#: quarter's own $78.3M already holds that slot.
BRBR_HEAD = ("BellRing Brands Reports Results for the Third Quarter of Fiscal Year 2026; Updates "
             "Fiscal Year 2026 Outlook St. Louis - August 4, 2026 - BellRing Brands, Inc. "
             "(NYSE:BRBR) (“BellRing”), a holding company operating in the global proactive "
             "wellness category, today reported results for the third fiscal quarter ended June "
             "30, 2026.")
BRBR_NINE = ("Nine Month Operating Results Net sales were $1,706.4 million, an increase of 2.3%, "
             "or $38.0 million, compared to the prior year period, driven by 4.7% increase in "
             "volume and 2.4% decrease in price/mix. Adjusted EBITDA* was $222.4 million, a "
             "decrease of $141.8 million, compared to $364.2 million in the prior year period, and "
             "was impacted by")


def test_bellrings_nine_month_section_is_not_its_third_quarter() -> None:
    got = _actuals(f"{BRBR_HEAD} {BRBR_NINE}")
    assert [a for a in got if a[2] in (222.4, 364.2)] == [], got


def test_a_figure_under_a_year_to_date_lead_in_takes_no_quarter() -> None:
    """The bullet run states its span once, in the parent's lead-in — the TTM rule of audit
    E2-D5 (FuboTV), now read for a year-to-date span too."""
    text = ("Acme Reports Third Quarter 2026 Results. Third Quarter Highlights ● For the nine "
            "months ended September 30, 2026: ○ Adjusted EBITDA of $55.0 million ○ Revenue of "
            "$290.0 million")
    assert [a for a in _actuals(text) if a[2] in (55.0, 290.0)] == []


def test_a_quarter_heading_still_labels_its_figure() -> None:
    """NEGATIVE PIN: the quarter's own section keeps its label."""
    text = ("Acme Reports Third Quarter 2026 Results. Third Quarter Highlights • Adjusted EBITDA "
            "of $20.0 million, up 5%.")
    assert _actuals(text) == [("adjusted ebitda", "Q3 2026", 20.0)]


#: NIKE, 8-K 0000320187-26-000026 EX-99.1: its head, and its income statement from the column
#: header to the gross-margin row (two verbatim fragments). The row's first column is the quarter
#: (4,530 / 11,279 = 40.2%), under a header that also names NINE MONTHS ENDED.
NKE_HEAD = ("NIKE, INC. REPORTS FISCAL 2026 THIRD QUARTER RESULTS BEAVERTON, Ore., Mar. 31, 2026 — "
            "NIKE, Inc. (NYSE:NKE) today reported fiscal 2026 financial results for its third "
            "quarter ended February 28, 2026.")
NKE_TABLE = ("NIKE, Inc. CONSOLIDATED STATEMENTS OF INCOME (Unaudited) THREE MONTHS ENDED % NINE "
             "MONTHS ENDED % (In millions, except per share data) 2/28/2026 2/28/2025 Change "
             "2/28/2026 2/28/2025 Change Revenues $ 11,279 $ 11,269 0 % $ 35,426 $ 35,212 1 % Cost "
             "of sales 6,749 6,594 2 % 20,908 19,891 5 % Gross profit 4,530 4,675 -3 % 14,518 "
             "15,321 -5 % Gross margin 40.2 % 41.5 % 41.0 % 43.5 %")


def test_nike_keeps_its_third_quarter_gross_margin() -> None:
    """NEGATIVE PIN (the brief's): the quarter's 40.2 stays under a nine-month column header."""
    assert [a for a in _actuals(f"{NKE_HEAD} {NKE_TABLE}") if a[0] == "gross margin"] == [
        ("gross margin", "Q3 2026", 40.2)]


def test_a_gaap_gross_margin_after_a_year_to_date_one_is_read() -> None:
    """A10: the first statement is the nine months', the second the quarter's."""
    text = ("Acme Reports Third Quarter 2026 Results. Gross margin was 40.0% for the nine months "
            "ended September 30, 2026. Gross margin was 41.0% for the third quarter of 2026.")
    assert [a for a in _actuals(text) if a[0] == "gross margin"] == [
        ("gross margin", "Q3 2026", 41.0)]


# --- D6: the release's frame is its own period, never its comparison's ---------------------------
#: Amazon, 8-K 0001018724-26-000024 and 0001018724-26-000012 EX-99.1: each release's first 600
#: characters, verbatim.
AMZN_Q2 = ("EX-99.1 2 amzn-20260630xex991.htm EX-99.1 Document Exhibit 99.1 AMAZON.COM ANNOUNCES "
           "SECOND QUARTER RESULTS Net sales increased 20% year-over-year Operating income was "
           "$27.5 billion, up 43% year-over-year AWS net sales increased 37%—its fastest growth in "
           "18 quarters—to a $169 billion annualized revenue run rate SEATTLE—(BUSINESS WIRE) July "
           "30, 2026—Amazon.com, Inc. (NASDAQ: AMZN) today announced financial results for its "
           "second quarter ended June 30, 2026. • Net sales increased 20% to $200.6 billion in the "
           "second quarter, compared with $167.7 billion in second quarter 2025. Excluding the "
           "$0.1 ")
AMZN_Q1 = ("EX-99.1 2 amzn-20260331xex991.htm EX-99.1 Document Exhibit 99.1 AMAZON.COM ANNOUNCES "
           "FIRST QUARTER RESULTS SEATTLE—(BUSINESS WIRE) April 29, 2026—Amazon.com, Inc. (NASDAQ: "
           "AMZN) today announced financial results for its first quarter ended March 31, 2026. • "
           "Net sales increased 17% to $181.5 billion in the first quarter, compared with $155.7 "
           "billion in first quarter 2025. Excluding the $2.9 billion favorable impact from "
           "year-over-year changes in foreign exchange rates throughout the quarter, net sales "
           "increased 15% compared with first quarter 2025. • North America segment sales "
           "increased 12% ye")


def test_amazons_frame_is_its_own_quarter_not_the_comparisons() -> None:
    assert len(AMZN_Q2) <= 600 and len(AMZN_Q1) <= 600
    assert rp._release_frame(AMZN_Q2).label == "Q2 2026"
    assert rp._release_frame(AMZN_Q1).label == "Q1 2026"


#: Amazon, 8-K 0001018724-26-000012 EX-99.1: its income statement's column header, verbatim.
AMZN_Q1_TABLE = ("Consolidated Statements of Operations (in millions, except per share data) "
                 "(unaudited) Three Months Ended March 31, 2025 2026")


def test_a_frame_read_from_its_quarter_end_date_has_no_fiscal_shift() -> None:
    """The column header prints the FIRST column's year; read as the quarter's end it shifted
    Amazon's calendar quarters by a year (+1), so "the quarter ended March 31, 2026" would have
    labelled Q1 2027."""
    frame = rp._release_frame(f"{AMZN_Q1} {AMZN_Q1_TABLE}")
    assert (frame.label, frame.fy_offset) == ("Q1 2026", 0)


def test_a_comparison_in_the_head_never_frames_the_release() -> None:
    """A11: the only quarter phrase in the head is the one revenue rose FROM."""
    text = ("Acme Inc. Reports Results. NEW YORK, Aug. 1, 2026 -- Acme today reported that revenue "
            "rose from second quarter 2025 levels. Adjusted EBITDA of $20.0 million.")
    assert rp._release_frame(text).label != "Q2 2025"
    assert [a for a in _actuals(text) if a[1] == "Q2 2025"] == []


def test_a_header_that_names_its_quarter_keeps_its_frame() -> None:
    """NEGATIVE PINS: BellRing's, NIKE's and Microvast's heads frame as before."""
    assert rp._release_frame(BRBR_HEAD).label == "Q3 2026"
    assert rp._release_frame(NKE_HEAD).label == "Q3 2026"
    assert rp._release_frame(MVST_HEAD).label == "Q2 2026"


# --- D9: a non-GAAP gross margin is not the GAAP one ---------------------------------------------
def test_a_non_gaap_gross_margin_is_not_the_gaap_one() -> None:
    text = ("Acme Reports Third Quarter 2026 Results. Non-GAAP gross margin was 47.0% for the "
            "third quarter of 2026.")
    assert [a for a in _actuals(text) if a[0] == "gross margin"] == []


def test_the_gaap_gross_margin_after_a_non_gaap_one_is_read() -> None:
    text = ("Acme Reports Third Quarter 2026 Results. Non-GAAP gross margin was 47.0% for the "
            "third quarter of 2026, and GAAP gross margin was 44.0%.")
    assert [a for a in _actuals(text) if a[0] == "gross margin"] == [
        ("gross margin", "Q3 2026", 44.0)]


def test_another_metrics_qualifier_does_not_make_a_gross_margin_non_gaap() -> None:
    """Review round 0: the qualifier must stand right before "gross margin"."""
    text = ("Acme Reports Third Quarter 2026 Results. Adjusted EPS and gross margin was 40.0% for "
            "the third quarter of 2026.")
    assert [a for a in _actuals(text) if a[0] == "gross margin"] == [
        ("gross margin", "Q3 2026", 40.0)]


def test_a_segments_gross_margin_is_never_the_companys() -> None:
    """Review round 0: reading past an unreadable first statement must not reach a segment's."""
    text = ("Acme Reports Third Quarter 2026 Results. Gross margin was 40.0% for the nine months "
            "ended September 30, 2026. The Products segment gross margin was 30.0% for the third "
            "quarter of 2026.")
    assert [a for a in _actuals(text) if a[0] == "gross margin"] == []



def test_a_segment_named_earlier_in_the_sentence_is_not_the_margins_line() -> None:
    """Review round 1 (in-session `/code-review high`; Codex's review failed on its usage limit):
    the segment test must read the margin's own phrase. Main stores this 40.0."""
    text = ("Acme Reports Third Quarter 2026 Results. Excluding the impact of the segment "
            "divestiture, gross margin was 40.0% for the third quarter of 2026.")
    assert [a for a in _actuals(text) if a[0] == "gross margin"] == [
        ("gross margin", "Q3 2026", 40.0)]

#: Microvast, 8-K 0001628280-26-055471 EX-99.1: its head and its gross-margin bullet (two verbatim
#: fragments) — GAAP first, then the non-GAAP adjusted figure.
MVST_HEAD = ("Microvast Reports Second Quarter 2026 Financial Results Houston, Texas, USA — "
             "Microvast Holdings, Inc. (NASDAQ:MVST) (“Microvast” or the “Company”), a global "
             "leader in advanced battery technologies, announced today its unaudited consolidated "
             "financial results for the second quarter ended June 30, 2026 (“Q2 2026”).")
MVST_GM = ("• Gross margin decreased to 29.5% from 34.7% in Q2 2025. Non-GAAP adjusted gross "
           "margin* decreased to 29.6% from 34.8% in Q2 2025, primarily due to higher raw material")


def test_microvast_keeps_its_gaap_gross_margin() -> None:
    """NEGATIVE PIN: the GAAP figure stated first stays; the adjusted one never replaces it."""
    assert [a for a in _actuals(f"{MVST_HEAD} {MVST_GM}") if a[0] == "gross margin"] == [
        ("gross margin", "Q2 2026", 29.5)]


# --- review round 2 (coordinator review of e470dd38) --------------------------------------------
_H = "Acme Reports Third Quarter 2026 Results. "
_N = "Gross margin was 40.0% for the nine months ended September 30, 2026. "


@pytest.mark.parametrize("tail", [
    "In the Products segment, gross margin was 30.0% for the third quarter of 2026.",
    "For the Products segment, gross margin was 30.0% for the third quarter of 2026.",
    "Hardware gross margin was 22.0%.",
    "Subscription gross margin was 80.0%.",
    "Product gross margin was 35.0%.",
    "Gross margin was 41.5% in the prior year period.",
])
def test_reading_past_a_year_to_date_margin_never_reaches_another_lines(tail: str) -> None:
    """Item 1 (BLOCKER): a segment's, a sub-line's or a prior period's margin is never the
    company's GAAP figure; main stores nothing for each."""
    assert [a for a in _actuals(_H + _N + tail) if a[0] == "gross margin"] == [], tail


def test_an_unplaceable_margin_stops_the_reader() -> None:
    """Item 1: a forward statement is unplaceable, and the reader stops there."""
    text = (_H + "We expect gross margin of 45.0% for the fourth quarter. Services gross margin "
            "was 20.0% in the third quarter of 2026.")
    assert [a for a in _actuals(text) if a[0] == "gross margin"] == []


#: Simply Good Foods, 8-K 0001702744-26-000010 EX-99.1: its head and its excluding-items margin
#: sentence (two verbatim fragments). The 32.8% is the quarter's margin EXCLUDING one-time items,
#: an adjusted figure; main stores it as the GAAP margin when it is the first statement.
SMPL_HEAD = ("The Simply Good Foods Company Reports Fiscal Second Quarter 2026 Financial Results "
             "and Updates Fiscal Year 2026 Outlook Denver, CO, April 9, 2026 - The Simply Good "
             "Foods Company (Nasdaq: SMPL) (“Simply Good Foods,” or the “Company”), a leader in "
             "the Nutritional Snacking Category, today reported financial results for the "
             "thirteen and twenty-six weeks ended February 28, 2026.")
SMPL_EXCLUDING = ("Excluding $3.9 million of one-time OWYN integration expenses in the current "
                  "year period and a $0.4 million non-cash inventory purchase accounting step-up "
                  "adjustment expense related to the OWYN acquisition that occurred in the "
                  "comparable prior year period, gross margin was 32.8%, a 350 basis point decline "
                  "versus the comparable year ago period.")


def test_simply_goods_excluding_items_margin_is_not_its_gaap_margin() -> None:
    assert [a for a in _actuals(f"{SMPL_HEAD} {SMPL_EXCLUDING}") if a[0] == "gross margin"] == []


@pytest.mark.parametrize(("text", "wrong"), [
    ("Acme Reports Fourth Quarter and Full Year Results. NEW YORK, Feb. 1, 2026 -- Acme today "
     "reported financial results for the fourth quarter ended December 31, 2025. • Adjusted "
     "EBITDA of $500.0 million • Revenue of $2.0 billion", "Q4 2025"),
    ("Acme Reports First Quarter Results. ST. LOUIS, Feb. 3, 2026 -- Acme today reported "
     "results for its first fiscal quarter ended December 31, 2025. • Adjusted EBITDA of $50.0 "
     "million", "Q1 2025"),
    ("Acme Stores Reports Fourth Quarter Results. DUBLIN, Calif., Mar. 3, 2026 -- Acme today "
     "reported results for its fourth quarter ended January 31, 2026, the end of fiscal 2025. • "
     "Adjusted EBITDA of $500.0 million", "Q4 2026"),
])
def test_the_quarter_end_frame_never_serves_a_fiscal_or_full_year_head(text: str,
                                                                       wrong: str) -> None:
    """Item 2: a combined Q4/full-year release (main refuses its figures), a fiscal filer's quarter
    end (its fiscal Q1 2026, not the calendar Q1 2025) and a retailer's (fiscal Q4 2025, not Q4
    2026): the quarter-end tier frames none of them, and no figure takes its calendar label."""
    assert rp._release_frame(text).kind != "quarter", text
    assert [a for a in _actuals(text) if a[1] == wrong] == [], text


@pytest.mark.parametrize("text", [
    "Acme Delivers Record Sales Compared to Last Year, Reports Third Quarter 2026 Results NEW "
    "YORK, Nov. 1, 2026 -- Adjusted EBITDA of $20.0 million.",
    "Acme Grows Revenue 15% Versus Prior Year in Third Quarter 2026 NEW YORK, Nov. 1, 2026 -- Acme "
    "today reported. Adjusted EBITDA of $20.0 million.",
    "Acme Reports Results. NEW YORK -- Compared with the third quarter of 2025, revenue grew 10% "
    "in the third quarter of 2026. Adjusted EBITDA of $20.0 million.",
])
def test_a_comparison_governs_only_the_phrase_it_introduces(text: str) -> None:
    """Item 3: a marker earlier in a headline does not take the release's own period with it."""
    assert rp._release_frame(text).label == "Q3 2026", text
    assert _actuals(text) == [("adjusted ebitda", "Q3 2026", 20.0)], text


def test_results_from_a_combined_period_is_no_comparison() -> None:
    text = ("Acme Announces Results from the Fourth Quarter and Full Year 2025. NEW YORK, Feb. 1, "
            "2026 -- Acme today reported results for its fourth quarter ended December 31, 2025. "
            "Adjusted EBITDA of $500.0 million.")
    assert rp._release_frame(text).kind == "combined"


@pytest.mark.parametrize("qualifier", [
    "Adjusted*", "Adjusted(1)", "Non-GAAP(1)", "Non GAAP", "Non-GAAP consolidated"])
def test_a_footnoted_or_spelled_out_non_gaap_margin_is_not_the_gaap_one(qualifier: str) -> None:
    """Item 4: the qualifier's footnote mark and words between still qualify the margin."""
    text = _H + f"{qualifier} gross margin was 47.0% for the third quarter of 2026."
    assert [a for a in _actuals(text) if a[0] == "gross margin"] == [], qualifier


@pytest.mark.parametrize("text", [
    _H + "After six months of integration, adjusted EBITDA was $20.0 million.",
    _H + "Third Quarter Highlights • Adjusted EBITDA of $20.0 million, the highest in six months.",
    _H + "Third Quarter Highlights • Revenue of $100.0 million. Six-Month Backlog Overview • "
    "Adjusted EBITDA of $20.0 million",
])
def test_six_months_that_is_not_a_span_drops_nothing(text: str) -> None:
    """Item 5: main labels each figure the quarter, and so does this reader."""
    assert ("adjusted ebitda", "Q3 2026", 20.0) in _actuals(text), text


def test_a_twelve_month_heading_is_no_quarter() -> None:
    """Found re-running the review's probes: once "month" makes "Twelve Month Results" a heading,
    its figure must not fall to the frame's quarter (main reaches no label there)."""
    text = (_H + "Fourth Quarter Highlights • x. Twelve Month Results • Adjusted EBITDA of $20.0 "
            "million")
    assert _actuals(text) == []


#: NIKE's table narrowed so the NINE MONTHS ENDED header sits inside the gross-margin row's clause
#: (verbatim fragments of 0000320187-26-000026, the rows between dropped): the row's first column
#: can no longer be told from its year-to-date one, so no margin is read — never 41.0 as Q3.
NKE_TABLE_NARROW = ("THREE MONTHS ENDED % NINE MONTHS ENDED % (In millions, except per share data) "
                    "2/28/2026 2/28/2025 Change 2/28/2026 2/28/2025 Change Gross profit 4,530 "
                    "4,675 -3 % 14,518 15,321 -5 % Gross margin 40.2 % 41.5 % 41.0 % 43.5 %")


def test_nikes_narrowed_table_reads_no_margin_rather_than_a_wrong_one() -> None:
    """Item 6: the negative pin exercised through the new year-to-date path."""
    assert [a for a in _actuals(f"{NKE_HEAD} {NKE_TABLE_NARROW}") if a[0] == "gross margin"] == []
