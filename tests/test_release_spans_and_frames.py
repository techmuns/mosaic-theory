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
