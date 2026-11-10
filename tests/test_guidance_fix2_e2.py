"""A guide is read only where the release states one, for the period it states, and a guide the
reader cannot read is said aloud (TeamNostra fix request 2: RE2-D1, RE2-D3, RE2-D4 = E2-D3, RE2-D5's
guide half, RE2-D7, RE2-D19, RE2-D20).

* RE2-D1 — "Total revenues of $412.0 million and $1,180.5 million for the three and nine months
  ended …" is two actuals; `_GUIDE_RANGE` read it as a 412.0–1,180.5 revenue guide.
* RE2-D3 — a release that WITHDRAWS its outlook still had the prior range read as the current guide.
* RE2-D4 / E2-D3 — the period came from a clause about a deal ("the 2025 acquisition", "the fourth
  quarter acquisition"), so a full-year guide was filed under 2025 and a fiscal 2027 one as Q4 2027.
* RE2-D5 (guide half) — "For calendar 2027" was filed as the fiscal year 2027; every period label
  downstream is the filer's FISCAL period, the rule #962 applied to the actuals.
* RE2-D7 — four guide shapes were dropped with no note: a qualifier before the low side, "is
  expected to increase 5% to 7%", a single point, and "guidance to $X to $Y".
* RE2-D19 — "raised … outlook to $1.10 billion to $1.15 billion from its prior outlook of …" stored
  no guide at all.
* RE2-D20 — a guide whose period was read nowhere is filed under the `next-fy` default with no trace
  that the period was assumed.

Constructed sentences are TeamNostra's (document 14). The real ones are cut from committed pages'
cited exhibits and name their accession.
"""
from __future__ import annotations

from vinci.edgar.release_parse import (
    GUIDANCE_PERIOD_DEFAULT_PREFIX,
    GUIDANCE_REFUSAL_PREFIX,
    parse_release,
)

_HEAD = "Acme Reports Third Quarter 2026 Results. "


def _guides(text: str) -> list[tuple[str, str, float | None, float | None, str]]:
    r = parse_release(_HEAD + text, source_ref="8-K X EX-99.1")
    return [(g.metric, g.period, g.low, g.high, g.unit) for g in r.guidance]


def _refusals(text: str) -> list[str]:
    r = parse_release(_HEAD + text, source_ref="8-K X EX-99.1")
    return [f for f in r.qa_flags if f.startswith(GUIDANCE_REFUSAL_PREFIX)]


def _defaults(text: str) -> list[str]:
    r = parse_release(_HEAD + text, source_ref="8-K X EX-99.1")
    return [f for f in r.qa_flags if f.startswith(GUIDANCE_PERIOD_DEFAULT_PREFIX)]


# --- RE2-D1: two actuals joined by "and" are not a range --------------------------------------
def test_re2_d1_two_actuals_joined_by_and_are_not_a_guide() -> None:
    text = ("Total revenues of $412.0 million and $1,180.5 million for the three and nine months "
            "ended September 30, 2026.")
    assert _guides(text) == []


def test_re2_d1_a_between_range_is_still_read() -> None:
    """NEGATIVE PIN — "between $X and $Y" is a range, and stays one."""
    assert _guides("For the fourth quarter, revenue is expected to be between $412.0 million and "
                   "$430.0 million.") == [("revenue", "Q4", 412.0, 430.0, "$M")]


# --- RE2-D3: a withdrawn outlook is not a guide -----------------------------------------------
def test_re2_d3_a_withdrawn_outlook_is_refused_aloud() -> None:
    text = ("The Company has withdrawn its fiscal 2026 outlook. Previously, the Company expected "
            "revenue of $1.00 billion to $1.05 billion for fiscal 2026.")
    assert _guides(text) == []
    assert any("withdraw" in f for f in _refusals(text)), _refusals(text)


def test_re2_d3_a_prior_range_with_no_withdrawal_reads_as_before() -> None:
    """NEGATIVE PIN — review round 2's rule (`_superseded_refused`): a range stated as the prior
    outlook, with no new one and no withdrawal, is the only figure there is and is read."""
    assert _guides("Previously, the Company expected revenue of $1.00 billion to $1.05 billion for "
                   "fiscal 2026.") == [("revenue", "fiscal 2026", 1000.0, 1050.0, "$M")]


# --- RE2-D4 / E2-D3: a deal's period is not the guide's ---------------------------------------
def test_re2_d4_a_year_naming_an_acquisition_is_not_the_period() -> None:
    text = ("Including the 2025 acquisition of Beta Corp, the Company expects revenue of $1.10 "
            "billion to $1.20 billion for the full year.")
    assert [p for _, p, *_ in _guides(text)] == ["next-fy"]
    assert len(_defaults(text)) == 1


def test_re2_d4_a_quarter_naming_an_acquisition_is_not_the_period() -> None:
    assert _guides("Reflecting the fourth quarter acquisition of Beta Corp, the Company expects "
                   "fiscal 2027 revenue of $1.10 billion to $1.20 billion.") == [
        ("revenue", "fiscal 2027", 1100.0, 1200.0, "$M")]


def test_re2_d4_a_period_of_the_guide_is_still_read() -> None:
    """NEGATIVE PINS — a quarter or a year that names no deal is the guide's period."""
    assert _guides("For the fourth quarter, the Company expects revenue of $300 million to $310 "
                   "million.") == [("revenue", "Q4", 300.0, 310.0, "$M")]
    assert _guides("The Company expects 2027 revenue of $1.10 billion to $1.20 billion, including "
                   "Beta Corp.") == [("revenue", "2027", 1100.0, 1200.0, "$M")]


# --- RE2-D5 (guide half): a calendar period is not a fiscal one -------------------------------
def test_re2_d5_a_calendar_period_is_refused_aloud() -> None:
    text = "For calendar 2027, the Company expects revenue of $1.20 billion to $1.30 billion."
    assert _guides(text) == []
    assert any("calendar" in f for f in _refusals(text)), _refusals(text)


def test_re2_d5_a_fiscal_period_is_read() -> None:
    """NEGATIVE PIN."""
    assert _guides("For fiscal 2027, the Company expects revenue of $1.20 billion to $1.30 "
                   "billion.") == [("revenue", "fiscal 2027", 1200.0, 1300.0, "$M")]


# --- RE2-D7: no guide shape is dropped in silence --------------------------------------------
_EBITDA = " The Company expects adjusted EBITDA of $80 million to $90 million for fiscal 2026."


def test_re2_d7a_a_qualifier_before_the_low_side_is_read() -> None:
    got = _guides("For fiscal 2026, the Company expects revenue to be approximately $500 million "
                  "to $550 million." + _EBITDA)
    assert ("revenue", "fiscal 2026", 500.0, 550.0, "$M") in got


def test_re2_d7b_is_expected_to_increase_is_read_as_a_change() -> None:
    r = parse_release(_HEAD + "For fiscal 2026, revenue is expected to increase 5% to 7%."
                      + _EBITDA, source_ref="8-K X EX-99.1")
    rev = [(g.period, g.low, g.high, g.unit, g.basis) for g in r.guidance if g.metric == "revenue"]
    assert rev == [("fiscal 2026", 5.0, 7.0, "%", "change")]


def test_re2_d7c_a_single_point_guide_is_refused_aloud() -> None:
    text = "For fiscal 2026, the Company expects revenue of approximately $520 million." + _EBITDA
    assert [m for m, *_ in _guides(text)] == ["adjusted ebitda"]
    assert any("single" in f and "$520 million" in f for f in _refusals(text)), _refusals(text)


def test_re2_d7c_vital_farms_single_point_guides_are_refused_aloud() -> None:
    """REAL TEXT — Vital Farms' 8-K 0001193125-26-444348 EX-99.1 cuts its outlook to single points.
    Main stored no guide for the release and wrote no note: the page had no current outlook and no
    sign that one had been stated."""
    text = ("For fiscal year 2026, we expect: • Net revenue of around $730 million, compared to "
            "prior outlook of $775 million to $800 million. • Adjusted EBITDA loss of around "
            "$(15) million, compared to prior outlook of a gain between $0 and $10 million. • "
            "Capital expenditures in the range of $70 million to $75 million, reaffirmed from our "
            "prior outlook.")
    assert _guides(text) == []
    notes = _refusals(text)
    assert any("$730 million" in f for f in notes), notes
    assert any("$(15) million" in f for f in notes), notes


def test_re2_d7c_an_actual_single_figure_is_no_guide_and_no_note() -> None:
    """NEGATIVE PIN — a results figure with no forward word before it is neither."""
    text = "Revenue of approximately $520 million increased 8% year-over-year."
    assert _guides(text) == [] and _refusals(text) == []


def test_re2_d7d_guidance_to_a_range_is_read() -> None:
    got = _guides("The Company raises its fiscal 2026 revenue guidance to $1.10 billion to $1.15 "
                  "billion." + _EBITDA)
    assert ("revenue", "fiscal 2026", 1100.0, 1150.0, "$M") in got


def test_re2_d7d_a_headline_guidance_to_never_displaces_the_outlook_section() -> None:
    """REAL TEXT, NEGATIVE PIN — Burlington's 8-K 0001193125-26-369502 EX-99.1 states its guide in a
    headline bullet AND its outlook list; the list's bullet is the one main reads, and still is."""
    text = ("▪ Increasing full year Adjusted EPS guidance to $11.77 to $11.97 BURLINGTON, New "
            "Jersey; August 27, 2026 — Burlington Stores, Inc. For Fiscal Year 2026 (the 52-weeks "
            "ending January 30, 2027), the Company now expects: • Net interest expense to be "
            "approximately $55 million; • An Adjusted Effective Tax Rate of approximately 25%; "
            "and • Adjusted EPS in the range of $11.77 to $11.97, as compared to $10.17 of "
            "Adjusted EPS last year.")
    r = parse_release(text, source_ref="8-K 0001193125-26-369502 EX-99.1")
    assert [(g.metric, g.low, g.high, g.verbatim) for g in r.guidance] == [
        ("adjusted eps", 11.77, 11.97, "Adjusted EPS in the range of $11.77 to $11.97")]


# --- RE2-D19: a raise "to … from" reads the new range ----------------------------------------
def test_re2_d19_a_raise_reads_the_new_range_not_the_prior() -> None:
    assert _guides("The Company raised its fiscal 2026 revenue outlook to $1.10 billion to $1.15 "
                   "billion from its prior outlook of $1.00 billion to $1.05 billion.") == [
        ("revenue", "fiscal 2026", 1100.0, 1150.0, "$M")]


# --- RE2-D20: a defaulted period is said ------------------------------------------------------
def test_re2_d20_a_defaulted_period_is_flagged() -> None:
    text = "Outlook. The Company expects revenue of $250 million to $260 million."
    assert _guides(text) == [("revenue", "next-fy", 250.0, 260.0, "$M")]
    flags = _defaults(text)
    assert len(flags) == 1 and "revenue" in flags[0] and "next-fy" in flags[0], flags
    # the guide is KEPT, so the flag is no refusal and is not lifted to the reader as one
    assert _refusals(text) == []


def test_re2_d20_verra_mobility_header_period_unread_is_flagged() -> None:
    """REAL TEXT — Verra Mobility's 8-K 0001628280-26-068453 EX-99.1. The header states 2026, the
    reader does not read it, and each guide was filed `next-fy` with no trace."""
    text = ("2026 Full Year Guidance Based on year-to-date 2026 results and our outlook for the "
            "fourth quarter, we are reaffirming 2026 full year guidance for all financial "
            "measures, provided in our second quarter earnings announcement, dated August 5, "
            "2026. • Total "
            "Revenue of $945 million to $965 million • Adjusted EBITDA of $360 million to $370 "
            "million • Adjusted EPS of $1.11 to $1.17")
    r = parse_release(text, source_ref="8-K 0001628280-26-068453 EX-99.1")
    defaulted = [g.metric for g in r.guidance if g.period == "next-fy"]
    flags = [f for f in r.qa_flags if f.startswith(GUIDANCE_PERIOD_DEFAULT_PREFIX)]
    assert defaulted and len(flags) == len(defaulted), (defaulted, flags)


def test_re2_d20_a_read_period_is_not_flagged() -> None:
    """NEGATIVE PIN."""
    assert _defaults("For fiscal 2026, the Company expects revenue of $250 million to $260 "
                     "million.") == []


# --- found while building: edges of the new readers --------------------------------------------
def test_re2_d19_a_prior_range_gives_way_to_a_later_guidance_to() -> None:
    """`_superseded_refused` reads every guide statement in the release; the "guidance to" form is
    one, so a prior range stated before it never takes the metric's slot."""
    assert _guides("Previously, the Company expected revenue of $1.00 billion to $1.05 billion for "
                   "fiscal 2026. The Company now raises its fiscal 2026 revenue guidance to $1.10 "
                   "billion to $1.15 billion.") == [
        ("revenue", "fiscal 2026", 1100.0, 1150.0, "$M")]


def test_re2_d3_a_new_outlook_after_a_withdrawal_in_its_clause_is_read() -> None:
    """NEGATIVE PIN — "withdrew its prior outlook and NOW expects …" states the new outlook."""
    assert _guides("The Company withdrew its prior outlook and now expects fiscal 2026 revenue of "
                   "$1.00 billion to $1.05 billion.") == [
        ("revenue", "fiscal 2026", 1000.0, 1050.0, "$M")]


def test_re2_d7c_a_range_never_reads_as_a_point() -> None:
    """NEGATIVE PIN — `_NUM` is atomic and the look-ahead skips the scale, so "$1.10 billion to …"
    cannot backtrack into a point at "$1.10"."""
    for text in ("For fiscal 2026, the Company expects revenue of $1.10 billion to $1.15 billion.",
                 "For fiscal 2026, the Company expects revenue of $1.10 to $1.15 billion."):
        assert _refusals(text) == [], text
