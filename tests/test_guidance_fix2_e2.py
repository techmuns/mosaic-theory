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


def test_re2_d20_verra_mobility_header_period_is_read() -> None:
    """REAL TEXT — Verra Mobility's 8-K 0001628280-26-068453 EX-99.1. The header states 2026. #976
    pinned the partial state here: each guide filed `next-fy`, now with a flag. The E2 remainder
    reads the header's forward clause, so each guide is 2026 and none is flagged
    (`tests/test_fix2_e2_remainder.py` pins every shape)."""
    text = ("2026 Full Year Guidance Based on year-to-date 2026 results and our outlook for the "
            "fourth quarter, we are reaffirming 2026 full year guidance for all financial "
            "measures, provided in our second quarter earnings announcement, dated August 5, "
            "2026. • Total "
            "Revenue of $945 million to $965 million • Adjusted EBITDA of $360 million to $370 "
            "million • Adjusted EPS of $1.11 to $1.17")
    r = parse_release(text, source_ref="8-K 0001628280-26-068453 EX-99.1")
    assert {g.period for g in r.guidance} == {"2026"}, [(g.metric, g.period) for g in r.guidance]
    assert not [f for f in r.qa_flags if f.startswith(GUIDANCE_PERIOD_DEFAULT_PREFIX)]


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


# --- review (code-review high): edges of the new readers -----------------------------------------
def test_re2_d1_two_actuals_are_no_current_guide_that_supersedes_a_prior_one() -> None:
    """Two figures joined by "and" state no guide (RE2-D1), so they are no CURRENT statement either:
    counted as one, they made `_superseded_refused` drop the only range the release states."""
    assert _guides("Previously, the Company expected revenue of $1.00 billion to $1.05 billion for "
                   "fiscal 2026. Total revenues of $412.0 million and $1,180.5 million for the "
                   "three and nine months ended September 30, 2026.") == [
        ("revenue", "fiscal 2026", 1000.0, 1050.0, "$M")]


def test_re2_d7d_guidance_to_shared_by_two_metrics_is_refused_aloud() -> None:
    """BellRing's shape through the "guidance to" reader: ONE range, TWO metrics — the range loop
    refuses it, and so must this one, or adjusted EBITDA takes net sales' $2.41–$2.49 billion."""
    text = ("The Company raises its fiscal 2026 net sales and adjusted EBITDA guidance to $2.41 "
            "billion to $2.49 billion.")
    assert _guides(text) == []
    assert any("shared by 2 metrics" in f for f in _refusals(text)), _refusals(text)


def test_re2_d19_a_prior_guidance_to_gives_way_to_a_current_one() -> None:
    """`_superseded_refused` governs the "guidance to" reader as it does every other: a range stated
    as the prior outlook, with a current one later, never takes the slot."""
    assert _guides("In May, the Company previously provided revenue guidance to $1.00 billion to "
                   "$1.05 billion. The Company now raises its fiscal 2026 revenue guidance to "
                   "$1.10 billion to $1.15 billion.") == [
        ("revenue", "fiscal 2026", 1100.0, 1150.0, "$M")]


def test_re2_d3_a_current_guide_beside_a_later_withdrawal_of_another_outlook_is_read() -> None:
    """A withdrawal AFTER the range in its clause withdraws the range only when no current word
    states it: "now expects revenue of … and is withdrawing its long-term outlook" keeps it."""
    assert _guides("For fiscal 2026, the Company now expects revenue of $1.10 billion to $1.15 "
                   "billion and is withdrawing its long-term outlook.") == [
        ("revenue", "fiscal 2026", 1100.0, 1150.0, "$M")]


def test_re2_d3_a_range_withdrawn_after_it_is_still_refused() -> None:
    """NEGATIVE PIN — a withdrawal after the range, no current word before it, still refuses."""
    text = ("Revenue of $1.00 billion to $1.05 billion for fiscal 2026 is no longer achievable, "
            "and the Company withdraws that outlook.")
    assert _guides(text) == []
    assert any("withdraw" in f for f in _refusals(text)), _refusals(text)


def test_re2_d5_a_calendar_period_opening_a_long_sentence_is_refused() -> None:
    """The calendar look-back fell back to the guide's own start when no sentence end sat within
    170 characters, so a long sentence's (or the text's) opening "For calendar 2027" went unread."""
    long_ = ("For calendar 2027, based on our current expectations for the macroeconomic "
             "environment, tariff policy, consumer demand and the timing of new store openings "
             "across the portfolio, the Company expects revenue of $1.20 billion to $1.30 billion.")
    assert _guides(long_) == []
    assert any("calendar" in f for f in _refusals(long_)), _refusals(long_)
    first = "For calendar 2027, the Company expects revenue of $1.20 billion to $1.30 billion."
    assert parse_release(first, source_ref="8-K X EX-99.1").guidance == []


def test_re2_d7c_as_expected_before_an_actual_is_no_forward_verb() -> None:
    """"As expected, revenue of $412 million grew 8%" is a result: "as expected" says the result met
    a forecast, it states none — no single-point refusal."""
    assert _refusals("As expected, revenue of $412 million grew 8% year-over-year.") == []
    assert _refusals("Better than anticipated, revenue of $412 million grew 8%.") == []


# --- review findings 7–10, fixed in the PR's own round 0 ----------------------------------------
def test_re2_d3_a_withdrawal_of_another_horizon_leaves_a_prior_range_read() -> None:
    """Review finding 7: ANY withdrawn outlook refused every prior-stated range. A long-term 2030
    outlook withdrawn is not the fiscal 2026 one, and "suspended production … outlook" withdraws
    nothing."""
    for lead in ("The Company withdrew its long-term 2030 outlook. ",
                 "The Company withdrew its fiscal 2030 outlook. ",
                 "The Company suspended production at its Ohio plant, which weighs on its "
                 "outlook. "):
        assert _guides(lead + "The Company previously expected fiscal 2026 revenue of $1.10 "
                       "billion to $1.15 billion.") == [
            ("revenue", "fiscal 2026", 1100.0, 1150.0, "$M")], lead


def test_re2_d3_a_withdrawal_of_this_horizon_still_refuses() -> None:
    """NEGATIVE PIN — the same year, or no year named, withdraws this range."""
    for lead in ("The Company withdrew its fiscal 2026 outlook. ",
                 "The Company has withdrawn its outlook. "):
        text = lead + "The Company previously expected fiscal 2026 revenue of $1.10 billion to " \
                      "$1.15 billion."
        assert _guides(text) == [], lead


def test_re2_d3_a_passive_withdrawal_refuses() -> None:
    """Review finding 8: "… outlook … has been withdrawn" is RE2-D3's case in the passive voice."""
    text = ("The revenue outlook of $1.00 billion to $1.05 billion for fiscal 2026 has been "
            "withdrawn.")
    assert _guides(text) == []
    assert any("withdraw" in f for f in _refusals(text)), _refusals(text)


def test_re2_d4_a_deal_stated_before_its_period_is_not_the_guides_period() -> None:
    """Review finding 9: RE2-D4 in mirror — the deal noun BEFORE its period."""
    want = [("revenue", "fiscal 2027", 1100.0, 1200.0, "$M")]
    assert _guides("Following the acquisition of Beta Corp in the fourth quarter, the Company "
                   "expects fiscal 2027 revenue of $1.10 billion to $1.20 billion.") == want
    assert _guides("Including Beta Corp, acquired in the fourth quarter, the Company expects "
                   "fiscal 2027 revenue of $1.10 billion to $1.20 billion.") == want


def test_re2_d4_a_period_after_a_comma_from_a_deal_is_read() -> None:
    """NEGATIVE PIN — a deal in its own clause leaves the guide's period alone."""
    assert _guides("Following the acquisition of Beta Corp, for the fourth quarter the Company "
                   "expects revenue of $300 million to $310 million.") == [
        ("revenue", "Q4", 300.0, 310.0, "$M")]


def test_re2_d7d_a_percent_range_under_dollar_guidance_to_is_refused_aloud() -> None:
    """Review finding 10: "revenue guidance to 5% to 7% growth" is a growth rate; read through the
    new reader it was stored as a revenue LEVEL of 5–7 %."""
    text = "The Company raises its fiscal 2026 revenue guidance to 5% to 7% growth."
    assert _guides(text) == []
    assert any("percent" in f for f in _refusals(text)), _refusals(text)


def test_re2_d7_to_be_a_range_is_read() -> None:
    """Review note: "revenue is expected to be $X to $Y" was dropped with no note while its
    "approximately" form is read — the same RE2-D7 class."""
    assert _guides("For fiscal 2026, revenue is expected to be $500 million to $550 million.") == [
        ("revenue", "fiscal 2026", 500.0, 550.0, "$M")]


# --- Codex review, round 1 ---------------------------------------------------------------------
def test_re2_d4_a_deal_noun_before_the_guides_own_period_does_not_date_it() -> None:
    """Codex P1: a deal noun before a period dates it only when the period is the deal's
    ("acquisition of Beta Corp IN THE fourth quarter", "acquired IN THE fourth quarter"). Before,
    any deal noun within 40 characters took the guide's own stated year and filed it next-fy."""
    assert _guides("The Company expects contributions from the acquisition to support fiscal 2026 "
                   "revenue of $1.10 billion to $1.20 billion.") == [
        ("revenue", "fiscal 2026", 1100.0, 1200.0, "$M")]


# --- Codex review, round 2 ---------------------------------------------------------------------
def test_re2_d7d_a_guidance_to_range_with_no_period_read_is_refused_aloud() -> None:
    """Codex P1: the new "guidance to" reader filed a range whose period it read nowhere under the
    `next-fy` default. Main's readers keep that default by design (RE2-D20 flags it); a NEW reader
    adds no guide whose period was assumed — it refuses aloud instead."""
    text = "The Company raises its revenue guidance to $1.10 billion to $1.15 billion."
    assert _guides(text) == []
    assert any("guidance to" in f and "period" in f for f in _refusals(text)), _refusals(text)
