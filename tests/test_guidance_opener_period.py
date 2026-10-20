"""TJX's adjusted-EPS guide, read — and the period it governs, from the sentence that opens its run.

THE DEFECT (an IC memo on TJX, 2026-10-19). The Q2 FY27 release states "the Company is increasing
its full year outlook for adjusted diluted earnings per share to be in the range of $5.15 to $5.20",
and the page said the release carried NO NUMERIC OUTLOOK. Four causes, each pinned below on the
filings' own sentences:

  1. VOCABULARY — `adjusted DILUTED earnings per share` was not a metric name.
  2. THE FULL STOP — a range closing its sentence ("$5.15 to $5.20.") read its high side as
     '5.20.', which does not parse, so the guide vanished without a refusal (Target's March guide
     the same way).
  3. THE PERIOD — neither TJX range names its period; "For the third quarter of Fiscal 2027," sits
     four sentences above the quarter's range. Read the old way, the quarter's $1.30–$1.32 would
     have landed on `next-fy`, which `period_scope` reads as ANNUAL: the ~4x error.
  4. FIRST-WINS — one range per metric per release kept the quarter and dropped the year.

THE CORPUS, measured before any pin (2026-10-21, main 07665419): the 118 EX-99.1 releases the 27
committed pages cite, re-parsed old vs new — 82 → 100 guidance items, 21 added and 3 relabelled
(Burlington's `next-fy` → its own "Fiscal 2025"/"Fiscal 2026"), 0 lost. Every added item was read
against its sentence: TJX ×2, Burlington ×3 (each quarter beside its year), Concentrix ×4,
nCino ×5 and EPAM ×1 (the year beside the quarter, or the quarter beside the year), Simply Good ×2,
Target ×1.
"""
from __future__ import annotations

import pytest

from vinci.dossier.schemas import GuidanceItem
from vinci.edgar.release_parse import _guidance, parse_release

#: TJX 8-K 0000109198-26-000045 EX-99.1 (filed 2026-08-19), the outlook section, verbatim.
_TJX = (
    "For the third quarter of Fiscal 2027, the Company is planning consolidated comparable sales "
    "to be up 2% to 3%. The Company expects pretax profit margin to be in the range of 12.8% to "
    "12.9%. Excluding an expected net benefit of 0.5 percentage points from tariff refunds, the "
    "Company expects adjusted pretax profit margin to be in the range of 12.3% to 12.4%. The "
    "Company expects diluted earnings per share to be in the range of $1.36 to $1.38. Excluding an "
    "expected net benefit of $.06 from tariff refunds, the Company expects adjusted diluted "
    "earnings per share to be in the range of $1.30 to $1.32. For the full year Fiscal 2027, the "
    "Company continues to expect consolidated comparable sales to be up 3% to 4%. The Company is "
    "increasing its full-year pretax profit margin outlook to be in the range of 12.3% to 12.4%. "
    "Excluding an expected net benefit of 0.3 percentage points from tariff refunds, the Company "
    "is increasing its full-year adjusted pretax profit margin outlook to be in the range of 12.0% "
    "to 12.1%. The Company is increasing its full-year diluted earnings per share outlook to be in "
    "the range of $5.31 to $5.36. Excluding an expected net benefit of $.16 from tariff refunds, "
    "the Company is increasing its full year outlook for adjusted diluted earnings per share to be "
    "in the range of $5.15 to $5.20. Beginning in Fiscal 2028, the Company is planning to "
    "accelerate its store opening growth to 4%.")

#: Burlington 8-K 0001193125-25-294501 EX-99.1 (Q3 FY25), the outlook section, verbatim.
_BURL = (
    "For the full Fiscal Year 2025 (the 52-weeks ending January 31, 2026), the Company now "
    "expects: • Total sales to increase by approximately 8% on top of the 11% increase for the "
    "52-weeks ended February 1, 2025; this assumes comparable store sales will increase in the "
    "range of 1% to 2%, on top of the 4% increase for the 52-weeks ended February 1, 2025; • "
    "Capital expenditures, net of landlord allowances, to be approximately $950 million; • To open "
    "104 net new stores; • Depreciation and amortization to be approximately $395 million; • "
    "Adjusted EBIT margin to increase in the range of 60 to 70 basis points versus the 52-weeks "
    "ended February 1, 2025; excludes $34 million of anticipated expenses associated with "
    "bankruptcy acquired leases in Fiscal 2025 and $16 million incurred in Fiscal 2024; • Net "
    "interest expense to be approximately $50 million; • An Adjusted Effective Tax Rate of "
    "approximately 25%; and • Adjusted EPS in the range of $9.69 to $9.89, as compared to $8.35 of "
    "Adjusted EPS last year; excludes $26 million, net of tax, of anticipated expenses associated "
    "with bankruptcy acquired leases in Fiscal 2025 and $12 million incurred in Fiscal 2024. This "
    "assumes a fully diluted share count of approximately 64 million shares. For the fourth "
    "quarter of Fiscal 2025 (the 13 weeks ending January 31, 2026), the Company now expects: • "
    "Total sales to increase in the range of 7% to 9%; this assumes comparable store sales will "
    "increase in the range of 0% to 2% versus the fourth quarter of Fiscal 2024; • Adjusted EBIT "
    "margin to increase 30 to 50 basis points versus the fourth quarter of Fiscal 2024; excludes "
    "approximately $7 million of anticipated expenses associated with bankruptcy acquired leases "
    "in the fourth quarter of Fiscal 2025 and $5 million incurred in the prior period; • An "
    "effective tax rate of approximately 26%; and • Adjusted EPS in the range of $4.50 to $4.70, "
    "as compared to $4.13 in Adjusted EPS last year;")

#: Target 8-K 0000027419-26-000012 EX-99.1 (filed 2026-03-03), verbatim.
_TGT = (
    "• Full-year 2026 operating income margin rate approximately 20 basis points higher than the "
    "4.6 percent Adjusted operating income margin rate in 2025. • GAAP and Adjusted EPS of $7.50 "
    "to $8.50. Based on the expected timing of certain costs, the company expects Q1 GAAP and "
    "Adjusted EPS will be flat to up slightly from last year’s Adjusted EPS of $1.30")


def _eps(items: list[GuidanceItem]) -> list[tuple[str, float | None, float | None, str]]:
    return [(g.period, g.low, g.high, g.unit) for g in items if g.metric == "adjusted eps"]


# --- POSITIVE: the three filings, read ------------------------------------------------------------

def test_tjx_reads_the_quarter_and_the_year_each_under_its_own_opener() -> None:
    """THE RED. Before: no item at all (the vocabulary), and once the vocabulary was in, ONE item —
    the quarter's, labelled `next-fy`. The GAAP diluted ranges ($1.36–$1.38, $5.31–$5.36) stay
    unread: prefix-free per-share forms are held back (STATE row 30)."""
    assert _eps(_guidance(_TJX, "8-K 0000109198-26-000045 EX-99.1")) == [
        ("Q3 2027", 1.30, 1.32, "$/sh"), ("Fiscal 2027", 5.15, 5.20, "$/sh")]


def test_burlington_keeps_its_year_first_and_adds_its_quarter() -> None:
    """Each range under its own opener, parenthetical and all. The year was read before as
    `next-fy` and stays FIRST, so every consumer that takes a release's first range is unmoved."""
    assert _eps(_guidance(_BURL, "x")) == [
        ("Fiscal 2025", 9.69, 9.89, "$/sh"), ("Q4 2025", 4.50, 4.70, "$/sh")]


def test_a_range_that_ends_its_sentence_keeps_its_high_side() -> None:
    """THE FULL STOP. Target's "GAAP and Adjusted EPS of $7.50 to $8.50." read '8.50.' and lost the
    guide; the same character dropped TJX's year."""
    assert _eps(_guidance(_TGT, "x")) == [("next-fy", 7.50, 8.50, "$/sh")]


# --- NEGATIVE: what an opener may NOT govern ------------------------------------------------------

def test_an_opener_that_reports_results_governs_nothing() -> None:
    """"In the second quarter, the Company repurchased…" opens a run of RESULTS. The guide below it
    keeps the default, never a closed quarter's label."""
    text = ("For the second quarter of Fiscal 2027, the Company repurchased 5.1 million shares of "
            "TJX stock. Excluding an expected net benefit of $.06 from tariff refunds, the Company "
            "expects adjusted diluted earnings per share to be in the range of $1.30 to $1.32.")
    assert _eps(_guidance(text, "x")) == [("next-fy", 1.30, 1.32, "$/sh")]


def test_a_mid_sentence_period_is_not_an_opener_and_a_capitalised_one_is() -> None:
    """The opener is a SENTENCE START. Lower-case, the same words are a clause about something else.
    The pair differs in ONE character, so the period read is the opener's and nothing else's."""
    tail = (" the Company is planning growth. The Company expects comparable sales to be up 2% to "
            "3%. The Company expects adjusted diluted earnings per share to be in the range of "
            "$1.30 to $1.32.")
    # both forward-looking from the period phrase on, so the capital letter is the only difference
    lower = "Net sales grew 5%, and for the third quarter of 2026,"
    upper = "Net sales grew 5%. For the third quarter of 2026,"
    assert _eps(_guidance(lower + tail, "x")) == [("next-fy", 1.30, 1.32, "$/sh")]
    assert _eps(_guidance(upper + tail, "x")) == [("Q3 2026", 1.30, 1.32, "$/sh")]


def test_a_quarter_opener_never_labels_a_full_year_range() -> None:
    """A run that names the OTHER scope is two periods, and the opener must not win: TJX's own
    full-year sentence placed under a third-quarter opener is refused, not called Q3."""
    text = ("For the third quarter of Fiscal 2027, the Company is planning consolidated "
            "comparable sales to be up 2% to 3%. Excluding an expected net benefit of $.16 from "
            "tariff refunds, the Company is increasing its full year outlook for adjusted diluted "
            "earnings per share to be in the range of $5.15 to $5.20.")
    assert _eps(_guidance(text, "x")) == [("next-fy", 5.15, 5.20, "$/sh")]


def test_a_year_opener_never_names_a_range_its_run_ties_to_a_quarter() -> None:
    """THE OTHER DIRECTION. A full-year run that speaks of a quarter before an unlabelled range
    leaves the range unlabelled; the opener's year is not stamped on it."""
    text = ("For the full year Fiscal 2027, the Company continues to expect consolidated "
            "comparable sales to be up 3% to 4%, with the third quarter the strongest. The Company "
            "expects "
            "adjusted diluted earnings per share to be in the range of $1.30 to $1.32.")
    assert _eps(_guidance(text, "x")) == [("next-fy", 1.30, 1.32, "$/sh")]


def test_a_second_range_on_the_default_or_a_held_scope_is_still_dropped() -> None:
    """FIRST-WINS STILL HOLDS within a scope. A restated range (no period read) and a second range
    for a year already held both stay out — only a READ, NEW scope admits a second range."""
    # a quarter is held, and a later range reads no period of its own (a results sentence ends the
    # opener's run): the default is never evidence of a second scope, so it stays out rather than
    # arriving as the year
    restated = ("For the third quarter of 2026, the Company expects Adjusted EPS in the range of "
                "$1.00 to $1.10. Shares outstanding were 64 million. Adjusted EPS in the range of "
                "$4.05 to $4.15.")
    assert _eps(_guidance(restated, "x")) == [("Q3 2026", 1.00, 1.10, "$/sh")]
    same_year = ("For fiscal 2026, the Company expects Adjusted EPS in the range of $1.00 to "
                 "$1.10. For fiscal 2026, the Company now expects Adjusted EPS in the range of "
                 "$1.05 to $1.15.")
    assert [g[1:3] for g in _eps(_guidance(same_year, "x"))] == [(1.00, 1.10)]


@pytest.mark.parametrize("sentence", [
    # Simply Good 8-K 0001702744-26-000021: a RESULT with a footnote marker, then its comparison
    "• Adjusted Diluted EPS (2) of $0.42 versus $0.51 • Adjusted EBITDA (3) of $57.2 million",
    # Target 8-K 0000027419-26-000020: a position INSIDE the prior range, not a new range
    "• GAAP and Adjusted EPS near the high end of the prior guidance range of $7.50 to $8.50. "
    "Operating Results",
])
def test_the_new_vocabulary_reads_no_result_and_no_restatement(sentence: str) -> None:
    """The two corpus sentences the widened vocabulary and the full-stop fix come nearest to, and
    must still not read as guides."""
    assert _eps(_guidance(sentence, "x")) == []


def test_parse_release_carries_both_and_no_longer_says_nothing_matched() -> None:
    """At the layer the page reads: the release extract carries the two TJX guides and no
    'no anchored pattern matched — guidance' flag, which is what put NO NUMERIC OUTLOOK on the
    page."""
    rel = parse_release(_TJX, source_ref="8-K 0000109198-26-000045 EX-99.1")
    assert [(g.metric, g.period) for g in rel.guidance] == [
        ("adjusted eps", "Q3 2027"), ("adjusted eps", "Fiscal 2027")]
    assert not any("guidance/outlook" in f for f in rel.qa_flags), rel.qa_flags
