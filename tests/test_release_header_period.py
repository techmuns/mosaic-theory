"""A guide in a bullet list reads its period from the LIST'S HEADER — STATE.md §5.0 row 30.

THE DEFECT, measured 2026-10-27 over the 119 EX-99.1 exhibits the committed pages cite: the clause
and the 60-character lead-in reach only a list's FIRST bullet, so every later guide fell to
`next-fy`, which `period_scope` reads as ANNUAL — Uber's quarterly adjusted-EBITDA guide of
$2.86–2.96bn sits on its page as a full year — and the lead-in read the year inside nCino's DATE
("second quarter ending July 31, 2026") as the guide's year. With the held vocabulary (operating
income, non-GAAP EPS) added, 17 ranges landed on `next-fy`; with `_header_period` every one reads
its period, and the vocabulary is admitted.

THE FIXTURES are real exhibit text (tests/fixtures/release_headers/cases.json), cut at sentence
boundaries; each was verified at generation to emit, for every guide pinned here, exactly what its
FULL filing emits (the `test_release_periods` convention). EDGAR filings are public domain.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.edgar import release_parse as rp
from vinci.edgar.primary_source import period_scope

CASES: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures" / "release_headers" / "cases.json").read_text())


def _guides(name: str) -> dict[tuple[str, str], tuple[float | None, float | None]]:
    c = CASES[name]
    x = rp.parse_release(c["text"], source_ref=c["source_ref"])
    return {(g.metric, g.period): (g.low, g.high) for g in x.guidance}


def _flags(name: str) -> list[str]:
    c = CASES[name]
    return rp.parse_release(c["text"], source_ref=c["source_ref"]).qa_flags


@pytest.mark.parametrize(("name", "metric", "period", "low", "high"), [
    # the SECOND bullet of "Third Quarter 2026 Guidance • … • Operating income is expected…"
    ("amzn_q3_2026", "operating income", "Q3 2026", 22500.0, 26500.0),
    ("amzn_q3_2026", "net sales", "Q3 2026", 197000.0, 202000.0),
    # a quarter named only by its end date keeps no year: the year is the date's, not a label's
    ("ncno_q2_fy27", "revenue", "Q2", 157.75, 159.75),
    ("ncno_q2_fy27", "adjusted operating income", "Q2", 35.5, 37.5),
    # the next list's header, not the first one's: "…for its fiscal year 2027 ending …, as follows:"
    ("ncno_q2_fy27", "revenue", "Fiscal 2027", 642.0, 646.0),
    ("ncno_q2_fy27", "adjusted operating income", "Fiscal 2027", 166.0, 171.0),
    ("ncno_q2_fy27", "free cash flow", "Fiscal 2027", 135.0, 140.0),
    # "Outlook for Q3 2026 For Q3 2026, we anticipate: • … ◦ … • Non-GAAP EPS … ◦ … Adjusted EBITDA"
    ("uber_q3_2026", "adjusted eps", "Q3 2026", 0.84, 0.88),
    ("uber_q3_2026", "adjusted ebitda", "Q3 2026", 2860.0, 2960.0),
    ("cnxc_q4_fy26", "operating income", "Q4 2026", 174.0, 184.0),
    ("cnxc_q4_fy26", "adjusted eps", "Q4 2026", 2.86, 2.98),
    # a header that is a whole SENTENCE before the list: "…reaffirming 2026 full year guidance…"
    ("vrrm_fy26_reaffirmed", "revenue", "2026", 1020.0, 1030.0),
    # items that end in semicolons, under "For the third quarter of Fiscal 2025 (…), …expects:"
    ("burl_q3_fy25", "adjusted eps", "Q3 2025", 1.5, 1.6),
    ("tgt_fy26", "adjusted eps", "2026", 7.5, 8.5),
    ("vitl_fy26", "revenue", "Fiscal 2026", 775.0, 800.0),
    # "…in Fiscal 2026 vs. $35 million incurred in Fiscal 2025; •" is an item, not a header: "vs."
    # ends no sentence and a header states no figure (this was read as Fiscal 2025)
    ("burl_fy26_vs_is_no_stop", "adjusted eps", "Fiscal 2026", 10.95, 11.45),
    ("burl_fy26_vs_is_no_stop", "adjusted eps", "Q1 2026", 1.6, 1.75),
    # "For the fourth quarter of fiscal year 2026: • The Company expects …" — the colon opens the
    # list, and the bullets carry the forward verb (this quarterly guide was dropped)
    ("smpl_q4_colon_header", "adjusted ebitda", "Q4 2026", 52.0, 57.0),
])
def test_a_guide_reads_its_period_from_its_lists_header(
        name: str, metric: str, period: str, low: float, high: float) -> None:
    assert _guides(name).get((metric, period)) == (low, high)


def test_no_bullet_header_guide_is_left_on_the_annual_default() -> None:
    """The row-30 shape itself: a quarterly guide filed under `next-fy` is the ~4x error. In every
    bullet-header case pinned here, no guide is left on the default."""
    for name in ("amzn_q3_2026", "ncno_q2_fy27", "uber_q3_2026", "cnxc_q4_fy26"):
        assert [k for k in _guides(name) if k[1] == "next-fy"] == [], name


def test_a_quarterly_guide_is_never_scoped_as_a_year() -> None:
    for name, metric, low in (("ncno_q2_fy27", "revenue", 157.75), ("uber_q3_2026",
                                                                    "adjusted ebitda", 2860.0)):
        period = next(p for (m, p), (lo, _h) in _guides(name).items() if m == metric and lo == low)
        assert period_scope(period) == "quarter", (name, period)


def test_a_double_footnote_marker_does_not_hide_a_guide() -> None:
    """Nike: "Adjusted Diluted earnings per share** is expected to be in the range of $1.15 to
    $1.35" — the slot took ONE marker, so a vocabulary metric was missed and the release read as
    stating no numeric outlook."""
    assert _guides("nke_fy27_double_footnote") == {("adjusted eps", "fiscal 2027"): (1.15, 1.35)}


def test_a_results_list_header_names_no_guided_period() -> None:
    """NEGATIVE: "Third Quarter Fiscal 2026 Highlights: • Revenue of $2,453.7 million…" is a list of
    RESULTS. Its header must never label a figure under it as guided."""
    text = CASES["cnxc_results_list"]["text"]
    assert rp._header_period(text, text.index("Revenue of $2,453.7")) is None


def test_a_header_naming_two_periods_is_no_answer() -> None:
    """NEGATIVE, a mutation of Amazon's real header: a list headed for a quarter AND its year
    cannot say which a bullet is (TJX heads its prose "Second Quarter and Full Year Fiscal 2027
    Outlook"). Neither period may be chosen."""
    text = CASES["amzn_q3_2026"]["text"].replace("Third Quarter 2026 Guidance",
                                                 "Third Quarter and Full Year 2026 Guidance")
    assert rp._header_period(text, text.index("Operating income is expected")) is None


def test_a_guide_inside_prose_has_no_list_header() -> None:
    """NEGATIVE: a guide that does not open a bullet item takes nothing from a list above it."""
    text = CASES["vrrm_fy26_reaffirmed"]["text"]
    at = text.index("Total Revenue of $1,020")
    assert rp._header_period(text, at) == "2026"
    prose = text[:at - 2] + ". The Company sees " + text[at:]
    assert rp._header_period(prose, prose.index("Total Revenue of $1,020")) is None


def test_prefix_free_eps_stays_held() -> None:
    """NEGATIVE, Ross (one of the seven releases that parse no guide): "2024 fourth quarter and full
    year earnings per share of $1.79 and $6.32" is two ACTUALS joined by "and" — the prefix-free
    form would read it as a range — so "earnings per share" alone is not vocabulary."""
    assert _guides("rost_prefix_free_eps_held") == {}


def test_a_bullet_naming_two_metrics_refuses_its_second_range_loudly() -> None:
    """Lilly's "…revenue in the range of $80 billion to $83 billion and non-GAAP EPS in the range of
    $33.50 to $35.00": the revenue range is read and the EPS range is REFUSED with a note, never
    dropped silently — the ambiguity check counts every metric from the bullet's start."""
    assert _guides("lly_shared_bullet_refused") == {("revenue", "2026"): (80000.0, 83000.0)}
    assert any(f.startswith(rp.GUIDANCE_REFUSAL_PREFIX) and "adjusted eps" in f
               for f in _flags("lly_shared_bullet_refused"))


def test_non_gaap_operating_income_and_eps_have_their_own_names() -> None:
    """GAAP and non-GAAP figures never share a name: "non-GAAP diluted EPS" is ADJUSTED EPS, not
    GAAP diluted EPS (the word after the prefix), and GAAP operating income is not adjusted."""
    assert rp._guide_metric("Non-GAAP diluted EPS") == "adjusted eps"
    assert rp._guide_metric("Non-GAAP operating income") == "adjusted operating income"
    assert rp._guide_metric("Operating income") == "operating income"
    assert rp._guide_metric("GAAP diluted EPS") == "gaap diluted eps"


def test_a_header_must_introduce_its_list() -> None:
    """NEGATIVE, a mutation of Simply Good's real header: without its colon "For the fourth quarter
    of fiscal year 2026" neither looks forward nor opens a list, so it labels nothing."""
    text = CASES["smpl_q4_colon_header"]["text"].replace("fiscal year 2026:", "fiscal year 2026")
    assert rp._header_period(text, text.index("Adjusted EBITDA expected to range from $52")) is None


def test_a_results_heading_with_an_outlook_word_is_still_no_header() -> None:
    """NEGATIVE, a mutation of Concentrix's real results list: "…Highlights and Outlook:" opens a
    section of RESULTS; an outlook word beside it does not make its figures guides."""
    text = CASES["cnxc_results_list"]["text"].replace(
        "Third Quarter Fiscal 2026 Highlights:",
        "Third Quarter Fiscal 2026 Highlights and Outlook:")
    assert rp._header_period(text, text.index("Revenue of $2,453.7")) is None


def test_a_header_naming_two_quarters_is_no_answer() -> None:
    """NEGATIVE, a mutation of Amazon's real header in Ross's real words ("for both the third and
    fourth quarters"): `_PHRASE` would read the second quarter alone."""
    for joined in ("Third and Fourth Quarters 2026 Guidance",
                   "Third and Fourth Quarter 2026 Guidance"):
        text = CASES["amzn_q3_2026"]["text"].replace("Third Quarter 2026 Guidance", joined)
        assert rp._header_period(text, text.index("Operating income is expected")) is None, joined


def test_a_closing_quote_ends_the_sentence_before_a_header() -> None:
    """NEGATIVE, a mutation of Vital Farms' real text: its header follows the CEO's quote
    ("…our trusted brand.” For fiscal year 2026, we expect:"). Read as one sentence with the quote,
    a period the quote names would make the header name two."""
    text = CASES["vitl_fy26"]["text"].replace("based on our trusted brand.”",
                                              "based on our trusted brand in the fourth quarter.”")
    assert "fourth quarter.”" in text
    assert rp._header_period(text, text.index("Net revenue of $775")) == "Fiscal 2026"


def test_vs_is_no_sentence_end() -> None:
    """NEGATIVE, a mutation of Burlington's real item with the figure taken out of its comparison:
    "…in Fiscal 2026 vs. the amount incurred in Fiscal 2025;" — "vs." ends no sentence, so the
    item's tail is never read as the list's header."""
    text = CASES["burl_fy26_vs_is_no_stop"]["text"].replace(
        "vs. $35 million incurred in Fiscal 2025", "vs. the amount incurred in Fiscal 2025")
    assert "vs. the amount incurred" in text
    at = text.index("Adjusted EPS in the range of $10.95")
    assert rp._header_period(text, at) == "Fiscal 2026"


def test_a_tail_stating_a_figure_is_an_item_not_a_header() -> None:
    """NEGATIVE, a mutation of the same item into two real sentences: "…in Fiscal 2026. That
    compares with $35 million incurred in Fiscal 2025;" — text after a full stop that states a
    figure is the rest of an item, and the walk goes on to the list's real header."""
    text = CASES["burl_fy26_vs_is_no_stop"]["text"].replace(
        "in Fiscal 2026 vs. $35 million incurred", "in Fiscal 2026. That compares with $35 million "
        "incurred")
    assert "That compares with $35 million" in text
    at = text.index("Adjusted EPS in the range of $10.95")
    assert rp._header_period(text, at) == "Fiscal 2026"
