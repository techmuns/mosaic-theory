"""A release actual the reader cannot place is refused with a note, never dropped silently, and
four shapes it misread are read as stated (TeamNostra fix request 2).

* E2-D11's residual (order 3): an unplaced NON-revenue actual was skipped with no note, while a
  revenue figure in the same bullets got one. EPAM's headline "Non-GAAP Diluted EPS of $3.26"
  under "Fourth Quarter 2025" (8-K 0001352010-26-000010) was dropped beside two refused
  "Revenues of". The note is written once per figure, and only when no other sentence places it.
* RE2-D2: "Revenue of $850.0 million and $300.0 million for the nine and three months ended …,
  respectively" stored the nine-month figure as the quarter. Refused.
* RE2-D5 (the actuals half): "Adjusted EBITDA of $480 million for calendar year 2025" in a
  "Fiscal 2026 Results" release was labelled 2026. Refused.
* RE2-D6: "$(5.5) million", "($5.5) million" and "-$5.5 million" did not match. Read, signed.
* RE2-D8: a retailer's "fiscal year ended January 31, 2026" under "Fiscal 2025 Results" was
  labelled 2026, refused as postdating the release, and dropped. It is fiscal 2025.

Real release text (public EDGAR, cut at phrase boundaries) where the corpus has the shape; the
rest are TeamNostra's constructed cases (document 14, E2), named as such.
"""
from __future__ import annotations

from vinci.edgar import release_parse as rp

_SRC = "8-K 0000000000-00-000000 EX-99.1"

#: 8-K 0001352010-26-000010 (EPAM, Q4 and FY 2025), the headline block before the dateline
_EPAM_HEAD = (
    "EPAM Reports Results for Fourth Quarter and Full Year 2025 Fourth Quarter 2025 • Revenues "
    "of $1.408 billion, up 12.8% year-over-year • GAAP Income from Operations was 10.6% of "
    "revenues and Non-GAAP Income from Operations was 16.3% of revenues • GAAP Diluted EPS of "
    "$1.98, an increase of 10.0%, and Non-GAAP Diluted EPS of $3.26, an increase of 14.8% on a "
    "year-over-year basis Full Year 2025 • Revenues of $5.457 billion, up 15.4% year-over-year "
    "• GAAP Income from Operations was 9.5% of revenues and Non-GAAP Income from Operations was "
    "15.2% of revenues • GAAP Diluted EPS of $6.72, a decrease of 14.3%, and Non-GAAP Diluted "
    "EPS of $11.50, an increase of 5.9% on a year-over-year basis "
)
#: 8-K 0001193125-26-092488 (Burlington, Q4 and FY 2025): a headline FY25 figure the release
#: places later, under "Full Year Fiscal 2025 Results"
_BURL = (
    "Burlington Stores, Inc. Reports Fourth Quarter and Full Year 2025 Earnings o Q4 total "
    "sales grew 11%, and comparable store sales increased 4% ▪ FY25 Adjusted EPS of $10.17, an "
    "increase of 22% versus FY24 BURLINGTON, New Jersey. Full Year Fiscal 2025 Results • Total "
    "sales increased 9% compared to Fiscal 2024. Adjusted EPS was $10.17 vs. $8.35 in Fiscal "
    "2024, an increase of 22%."
)
_Q3 = "Acme Reports Third Quarter 2026 Results. "


def _parse(text: str) -> rp.ReleaseExtract:
    return rp.parse_release(text, source_ref=_SRC)


def _rows(text: str) -> list[tuple[str, str, float]]:
    return [(r.metric, r.period, r.value) for r in _parse(text).reconciliation]


def _refusals(text: str) -> list[str]:
    return [f for f in _parse(text).qa_flags if f.startswith(rp.RECON_REFUSAL_PREFIX)]


# --- E2-D11's residual: an unplaced actual is said ------------------------------------------------
def test_e2_d11_an_unplaced_non_revenue_actual_is_noted() -> None:
    """Real text: EPAM's headline EPS figures, skipped beside its two refused revenues, are said."""
    notes = _refusals(_EPAM_HEAD)
    eps = [n for n in notes if "adjusted eps figure skipped" in n]
    assert len(eps) == 2, notes
    assert any("$3.26" in n for n in eps) and any("$11.50" in n for n in eps)
    assert sum("revenue figure skipped" in n for n in notes) == 2  # as before


def test_e2_d11_a_figure_placed_by_another_sentence_is_not_noted() -> None:
    """NEGATIVE PIN — real text: Burlington's headline "FY25 Adjusted EPS of $10.17" is placed by
    its full-year section's own sentence, so it is not dropped and no note is written."""
    assert ("adjusted eps", "2025", 10.17) in _rows(_BURL)
    assert not [n for n in _refusals(_BURL) if "$10.17" in n]


def test_e2_d11_one_note_per_figure() -> None:
    """A figure the release repeats unplaced is noted once."""
    text = ("Acme Reports Fourth Quarter and Full Year 2025 Results Fourth Quarter 2025 • "
            "Adjusted EBITDA of $211.9 million Full Year 2025 • Adjusted EBITDA of $211.9 "
            "million")
    assert sum("$211.9" in n for n in _refusals(text)) == 1


# --- RE2-D2: a "respectively" list is refused -----------------------------------------------------
def test_re2_d2_a_respectively_list_is_refused() -> None:
    """CONSTRUCTED (TeamNostra): the nine-month figure was stored as Q3 2026."""
    for text in (
        _Q3 + "Revenue of $850.0 million and $300.0 million for the nine and three months ended "
              "September 30, 2026, respectively.",
        _Q3 + "Adjusted EBITDA was $55.0 million and $20.0 million for the nine months and three "
              "months ended September 30, 2026, respectively.",
    ):
        assert _rows(text) == [], text
        assert any("'respectively' list" in n for n in _refusals(text)), text


def test_re2_d2_a_comparison_is_still_read() -> None:
    """NEGATIVE PIN — an amount joined to its own prior period is not a respectively list."""
    text = _Q3 + ("Adjusted EBITDA was $20.0 million, compared to $15.0 million in the third "
                  "quarter of 2025.")
    assert ("adjusted ebitda", "Q3 2026", 20.0) in _rows(text)


# --- RE2-D5: a calendar period is not a fiscal one ------------------------------------------------
_FY26 = "Acme Widgets Reports Fiscal 2026 Results. "


def test_re2_d5_a_calendar_year_actual_is_refused() -> None:
    """CONSTRUCTED (TeamNostra): calendar 2025, under a fiscal-2026 header, was labelled 2026."""
    text = _FY26 + "Adjusted EBITDA of $480 million for calendar year 2025."
    assert _rows(text) == []
    assert any("calendar 2025" in n for n in _refusals(text))


def test_re2_d5_a_fiscal_year_is_still_read() -> None:
    """NEGATIVE PIN."""
    text = _FY26 + "Adjusted EBITDA of $480 million for fiscal 2026."
    assert _rows(text) == [("adjusted ebitda", "2026", 480.0)]


# --- RE2-D6: a negative written as a sign ---------------------------------------------------------
_Q3_LEAD = _Q3 + "For the third quarter of 2026, "


def test_re2_d6_a_bracketed_or_minus_negative_is_read_signed() -> None:
    """CONSTRUCTED (TeamNostra's three shapes)."""
    text = _Q3_LEAD + ("Adjusted EBITDA of -$5.5 million and adjusted net loss per share of "
                       "$(0.12).")
    assert ("adjusted ebitda", "Q3 2026", -5.5) in _rows(text)
    assert ("adjusted eps", "Q3 2026", -0.12) in _rows(text)
    assert _rows(_Q3_LEAD + "Adjusted EBITDA of ($5.5) million.") == [
        ("adjusted ebitda", "Q3 2026", -5.5)]


def test_re2_d6_par_pacifics_bracketed_loss_is_matched_signed() -> None:
    """Real text: 8-K 0001628280-25-048903 (Par Pacific). The amount token now reads it, signed.
    (The clause's comparison is still not stored: `_sub_unit` takes the SRE impact for the
    current figure — a separate, pre-existing limit, recorded.)"""
    text = ("Third quarter 2025 Adjusted Net Income was $302.6 million, including an SRE impact "
            "of $195.9 million, compared to an Adjusted Net Loss of $(5.5) million in the third "
            "quarter of 2024.")
    hit = [m for m in rp._RECON.finditer(text) if "Loss" in m.group(0)]
    assert len(hit) == 1 and hit[0]["negp"] and hit[0]["num"] == "5.5"


def test_re2_d6_a_range_dash_is_not_a_sign() -> None:
    """NEGATIVE PIN — a range's dash belongs to the range tail, which is refused as before."""
    text = _Q3_LEAD + "Adjusted EBITDA of $5.0 - $5.5 million."
    assert _rows(text) == []
    assert any("a range where an actual was read" in n for n in _refusals(text))


# --- RE2-D8: a fiscal year that ends in the next calendar year ------------------------------------
def test_re2_d8_a_retail_fiscal_year_is_its_fiscal_year() -> None:
    """CONSTRUCTED (TeamNostra): the FY figure was refused as postdating the release, silently."""
    text = ("Acme Retail Reports Fourth Quarter and Fiscal 2025 Results. For the fourth quarter "
            "of fiscal 2025, Adjusted EBITDA of $150 million. Adjusted EBITDA of $480 million for "
            "the fiscal year ended January 31, 2026.")
    assert _rows(text) == [("adjusted ebitda", "Q4 2025", 150.0),
                           ("adjusted ebitda", "2025", 480.0)]


def test_re2_d8_a_calendar_filer_and_a_quarter_release_are_unchanged() -> None:
    """NEGATIVE PINS — a calendar filer's year ends in its own year; a quarter release's "year
    ended" names a prior year and never shifts the frame."""
    text = ("Acme Reports Fourth Quarter and Full Year 2025 Results. Adjusted EBITDA of $480 "
            "million for the year ended December 31, 2025.")
    assert _rows(text) == [("adjusted ebitda", "2025", 480.0)]
    text = ("Acme Reports First Quarter 2026 Results. For the first quarter of 2026, Adjusted "
            "EBITDA of $120 million. Adjusted EBITDA of $480 million for the year ended December "
            "31, 2025.")
    assert ("adjusted ebitda", "Q1 2026", 120.0) in _rows(text)
    assert rp._release_frame(text).fy_offset == 0


# --- review round 0 (/code-review high --fix) ----------------------------------------------------
def test_review_a_quarter_offset_never_shifts_a_year_end() -> None:
    """CONSTRUCTED: a first quarter that ends in the prior calendar year (+1) does not move the
    fiscal year its "year ended" names — fiscal 2025 ended May 31, 2025 and is 2025, not 2026."""
    head = ("Acme Reports Fiscal 2026 First Quarter Results. For the three months ended August 31, "
            "2025, Adjusted EBITDA of $1,200 million. ")
    assert rp._release_frame(head).fy_offset == 1
    assert ("adjusted ebitda", "2025", 4800.0) in _rows(
        head + "Adjusted EBITDA of $4,800 million for the fiscal year ended May 31, 2025.")
    assert ("adjusted ebitda", "2025", 4800.0) in _rows(
        head + "Adjusted EBITDA was $4,800 million, compared to $4,500 million for the fiscal "
               "year ended May 31, 2024.")


def test_review_a_signed_or_longer_respectively_list_is_refused() -> None:
    """CONSTRUCTED: the bracketed second amount, and a three-amount list, are both lists."""
    for text in (
        _Q3 + "Adjusted EBITDA of $(55.0) million and $(20.0) million for the nine and three "
              "months ended September 30, 2026, respectively.",
        _Q3 + "Revenue of $850.0 million, $550.0 million and $300.0 million for the nine, six "
              "and three months ended September 30, 2026, respectively.",
    ):
        assert _rows(text) == [], text
        assert any("'respectively' list" in n for n in _refusals(text)), text


def test_review_a_signed_range_is_a_range() -> None:
    """CONSTRUCTED: a negative range's high side is signed too; its low end is not an actual."""
    for text in (_Q3_LEAD + "adjusted net loss per share of $(0.15) to $(0.10).",
                 _Q3_LEAD + "Adjusted EBITDA of -$5.0 million to -$3.0 million."):
        assert _rows(text) == [], text
        assert any("a range where an actual was read" in n for n in _refusals(text)), text


def test_review_a_calendar_year_in_the_comparison_is_not_the_figures() -> None:
    """NEGATIVE PIN: a calendar year inside the comparison does not refuse the fiscal figure."""
    text = _FY26 + ("Adjusted EBITDA of $480 million for fiscal 2026, compared to $400 million "
                    "for calendar year 2025.")
    assert ("adjusted ebitda", "2026", 480.0) in _rows(text)


def test_review_an_unplaced_comparison_is_not_noted_as_a_skipped_actual() -> None:
    """A compared amount the reader cannot place is the prior, not a skipped actual — as revenue."""
    text = ("Acme Reports Fourth Quarter and Full Year 2025 Results. Adjusted EBITDA was $20.0 "
            "million, compared to Adjusted EBITDA of $15.0 million in the prior year.")
    assert not [n for n in _refusals(text) if "$15.0" in n]
