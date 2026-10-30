"""A guidance range is read as its sentence states it — its scale, its line, its standing, its
unit and its partner range (audit E2-D1, D2, D7, D8, D13; Phase 2 batch B1).

Five defects in `release_parse._guidance`, each a stated number stored as something it is not:

  D1  SCALE. "$500 to $550 thousand", "$500,000 to $550,000" and "$80 to $100" were stored as $M —
      a 1000x overstatement or a guess. A $M guide must state its scale in millions or billions;
      anything else is refused aloud.
  D2  LINE. "subscription revenue", "North America revenue" were stored as the company's revenue.
      The guide now reads the word before the metric with the actuals' own allowlist
      (`_REVENUE_LEAD_OK`). nCino lists "Subscription revenues between …" under every outlook.
  D7  STANDING. "Previously, the Company expected revenue of … The Company now expects …" kept the
      FIRST range — the superseded one. A range its sentence states as the prior outlook never
      takes the metric's slot.
  D8  UNIT. A gross margin stated in dollars was stored as a percentage (1.2–1.3 %).
  D13 PARTNER. "… $250 million to $260 million in the third quarter and $1.00 billion to $1.10
      billion for the full year 2026" lost its second range with no note.

The constructed sentences are the audit's own probes (G1–G5, G11, G13 and the D8 inline case,
`data/session-notes/audit-verification/E2.md`); no committed page carries any of the five today.
The NEGATIVE pins quote filed EX-99.1 sentences wherever the shape exists in one (Amazon, Verra
Mobility, nCino, EPAM, Simply Good, Artivion, Vital Farms, BellRing) — filing text is immutable, so
those are value pins that cannot rot; the rest are marked constructed where they stand.
"""
from __future__ import annotations

import pytest

from vinci.dossier import mechanical
from vinci.edgar.release_parse import GUIDANCE_REFUSAL_PREFIX, parse_release

_SRC = "8-K 0000000000-26-000001 EX-99.1"


def _guides(text: str) -> list[tuple[str, str, float | None, float | None, str]]:
    r = parse_release(text, source_ref=_SRC)
    return [(g.metric, g.period, g.low, g.high, g.unit) for g in r.guidance]


def _refusals(text: str) -> list[str]:
    return [f for f in parse_release(text, source_ref=_SRC).qa_flags
            if f.startswith(GUIDANCE_REFUSAL_PREFIX)]


# --- D1: a $M guide states its scale ------------------------------------------------------------
G1 = ("Acme Reports Third Quarter 2026 Results. Outlook: The Company expects revenue to be in "
      "the range of $500 to $550 thousand for the fourth quarter of 2026.")
G2 = ("Acme Reports Third Quarter 2026 Results. Outlook: The Company expects revenue to be in "
      "the range of $500,000 to $550,000 for the fourth quarter of 2026.")
G3 = ("Acme Reports Third Quarter 2026 Results. Outlook: For fiscal 2026, adjusted EBITDA of "
      "$80 to $100.")


def test_a_guide_stated_in_thousands_is_not_stored_as_millions() -> None:
    assert _guides(G1) == []
    notes = _refusals(G1)
    assert len(notes) == 1 and "thousand" in notes[0]


def test_a_dollar_guide_with_no_scale_word_is_refused_aloud() -> None:
    for text in (G2, G3):
        assert _guides(text) == []
        notes = _refusals(text)
        assert len(notes) == 1 and "scale" in notes[0]


def test_a_stated_billion_and_million_still_scale() -> None:
    """NEGATIVE PIN. Amazon, 8-K 0001018724-26-000024 EX-99.1 (2026-07-30), and Verra Mobility's
    outlook bullets (8-K 0001193125-26-239351 EX-99.1), each verbatim — both state their scale,
    both stay exactly as committed."""
    amzn = ("Third Quarter 2026 Guidance • Net sales are expected to be between $197.0 billion "
            "and $202.0 billion, or to grow between 9% and 12% compared with third quarter 2025.")
    assert _guides(amzn) == [("net sales", "Q3 2026", 197000.0, 202000.0, "$M")]
    vrrm = ("Verra Mobility is revising its 2026 full-year financial outlook to the following: "
            "• Total Revenue of $985 million to $995 million • Adjusted EBITDA of $380 million "
            "to $385 million • Adjusted EPS of $1.19 to $1.25 • Free Cash Flow of $140 million to "
            "$150 million")
    assert ("revenue", "2026", 985.0, 995.0, "$M") in _guides(vrrm)
    assert [g[2:] for g in _guides(vrrm) if g[0] == "adjusted eps"] == [(1.19, 1.25, "$/sh")]


# --- D2: a sub-line is not the company's revenue ------------------------------------------------
G4 = ("Acme Reports Third Quarter 2026 Results. Outlook: For fiscal 2027, the Company expects "
      "subscription revenue to be in the range of $500 million to $510 million.")
G5 = ("Acme Reports Third Quarter 2026 Results. Outlook: For fiscal 2027, the Company expects "
      "North America revenue of $1.2 billion to $1.3 billion.")
#: nCino, 8-K 0001902733-25-000130 EX-99.1, verbatim.
NCNO_LIST = ("Financial Outlook nCino is providing guidance for its fourth quarter ending January "
             "31, 2026, as follows: • Total revenues between $146.75 million and $148.25 million. "
             "• Subscription revenues between $130.75 million and $132.25 million. • Non-GAAP "
             "operating income between $32.5 million and $33.5 million.")


def test_a_sub_line_revenue_guide_is_refused_not_stored_as_revenue() -> None:
    for text, word in ((G4, "subscription"), (G5, "america")):
        assert [g for g in _guides(text) if g[0] == "revenue"] == []
        notes = _refusals(text)
        assert len(notes) == 1 and f"'{word}'" in notes[0]


def test_ncino_subscription_bullet_alone_is_not_the_company_total() -> None:
    """THE REAL LINE. nCino's subscription bullet, under its own header, without the total's
    bullet above it: main stored $130.75–132.25M as nCino's fourth-quarter REVENUE."""
    alone = NCNO_LIST.replace("• Total revenues between $146.75 million and $148.25 million. ", "")
    assert [g for g in _guides(alone) if g[0] == "revenue"] == []
    assert any("'subscription'" in n for n in _refusals(alone))


def test_ncino_list_keeps_the_total_and_only_the_total() -> None:
    """NEGATIVE PIN, the filed order: the total stays, the sub-line never reads as revenue."""
    revenue = [g for g in _guides(NCNO_LIST) if g[0] == "revenue"]
    assert revenue == [("revenue", "Q4 2026", 146.75, 148.25, "$M")]


def test_a_total_guide_led_by_an_allowed_word_stays() -> None:
    """NEGATIVE PINS, EPAM 8-K 0001352010-25-000053 and 0001352010-26-000043: the lead words
    'expected' and 'year-over-year' qualify the statement, not the line."""
    level = ("• Based on the strength of organic constant currency revenue growth and updates to "
             "our foreign exchange rate assumptions, the Company raises its expected revenues to "
             "be in the range of $5.430 billion to $5.445 billion, reflecting a year-over-year "
             "growth")
    assert [g[2:] for g in _guides(level) if g[0] == "revenue"] == [(5430.0, 5445.0, "$M")]
    rate = ("• For the full year, EPAM now expects the year-over-year revenue growth rate to be in "
            "the range of 3.2% to 4.2% and now expects")
    r = parse_release(rate, source_ref=_SRC)
    assert [(g.metric, g.low, g.high, g.unit, g.basis) for g in r.guidance] == [
        ("revenue", 3.2, 4.2, "%", "change")]


# --- D7: a superseded range does not take the slot ------------------------------------------------
G11 = ("Acme Reports Third Quarter 2026 Results. Previously, the Company expected revenue of "
       "$1.00 billion to $1.05 billion. The Company now expects revenue of $1.10 billion to "
       "$1.15 billion.")
#: Simply Good Foods, 8-K 0001702744-26-000010 EX-99.1 (2026-04-09), verbatim.
SMPL_UPDATE = ("Fiscal Year 2026 Outlook The Company is updating its previously provided outlook "
               "for fiscal year 2026: • Net Sales expected to range between $1.31 to $1.35 "
               "billion, or -10% to -7% year-over-year • Gross Margins expected to decline "
               "between 300 and 350 basis points year-over-year • Adjusted EBITDA expected to "
               "range between $217 to $225 million")


def test_the_current_range_replaces_the_one_it_supersedes() -> None:
    r = parse_release(G11, source_ref=_SRC)
    assert [(g.metric, g.low, g.high) for g in r.guidance] == [("revenue", 1100.0, 1150.0)]
    # said to the READER (review round 2): the note carries the refusal prefix the rollup reads
    assert any("prior outlook" in f and "1.00 billion" in f
               for f in mechanical.guidance_refusal_flags([r]))


def test_previously_provided_as_the_object_of_an_update_is_not_a_prior_range() -> None:
    """NEGATIVE PIN, the real shape. Simply Good says "updating its previously provided outlook"
    and then states the NEW ranges; every one of them stays."""
    got = _guides(SMPL_UPDATE)
    assert ("net sales", "2026", 1310.0, 1350.0, "$M") in got
    assert [g[2:] for g in got if g[0] == "adjusted ebitda"] == [(217.0, 225.0, "$M")]


def test_a_prior_range_reaffirmed_or_followed_by_now_is_current() -> None:
    """NEGATIVE PINS, constructed: a prior word that is not the range's own standing."""
    for text in (
        "The Company is updating its previously provided outlook and now expects revenue of "
        "$1.10 billion to $1.15 billion.",
        "The Company is reaffirming its prior guidance: revenue of $1.10 billion to $1.15 "
        "billion.",
        "Including the previously announced acquisition, the Company expects revenue of $1.10 "
        "billion to $1.15 billion.",
        "Reflecting higher than previously anticipated promotional spending, the Company expects "
        "revenue of $1.10 billion to $1.15 billion.",
    ):
        assert [g[2:4] for g in _guides(text)] == [(1100.0, 1150.0)], text


def test_vital_farms_previously_anticipated_after_its_range_is_still_current() -> None:
    """NEGATIVE PIN, Vital Farms 8-K 0001193125-26-210294 EX-99.1, verbatim: the prior word sits
    AFTER the range and qualifies spending, not the guide."""
    vitl = ("It also assumes that competitive activity does not intensify further. • Adjusted "
            "EBITDA of $0 to $10 million, reflecting higher than previously anticipated "
            "promotional spending and price investments")
    assert [g[2:] for g in _guides(vitl)] == [(0.0, 10.0, "$M")]


def test_artivion_keeps_its_current_range_beside_the_previously_articulated_one() -> None:
    """NEGATIVE PIN, Artivion 8-K 0001628280-25-050164 EX-99.1, verbatim."""
    aort = ("Growth rates are compared to 2024. The Company expects adjusted EBITDA to be in the "
            "range of $88 to $91 million, compared to the previously articulated range of $86 to "
            "$91 million.")
    assert [g[2:] for g in _guides(aort)] == [(88.0, 91.0, "$M")]


# --- D8: a gross margin in dollars is not a percentage -------------------------------------------
def test_a_gross_margin_stated_in_dollars_is_refused_not_stored_as_percent() -> None:
    text = ("Acme Reports Third Quarter 2026 Results. For fiscal 2026, the Company expects gross "
            "margin of $1.2 billion to $1.3 billion.")
    assert [g for g in _guides(text) if g[0] == "gross margin"] == []
    notes = _refusals(text)
    assert len(notes) == 1 and "dollars" in notes[0]


def test_a_gross_margin_stated_in_percent_stays() -> None:
    """NEGATIVE PINS: a percent level (constructed), and Simply Good's filed basis-point change."""
    text = ("Acme Reports Third Quarter 2026 Results. For fiscal 2026, the Company expects gross "
            "margin of 40% to 42%.")
    assert _guides(text) == [("gross margin", "fiscal 2026", 40.0, 42.0, "%")]
    smpl = [g for g in _guides(SMPL_UPDATE) if g[0] == "gross margin"]
    assert [g[2:] for g in smpl] == [(-350.0, -300.0, "bps")]


# --- D13: a second range in one sentence ---------------------------------------------------------
G13 = ("Acme Reports Second Quarter 2026 Results. The Company expects revenue of $250 million to "
       "$260 million in the third quarter and $1.00 billion to $1.10 billion for the full year "
       "2026.")


def test_a_second_range_with_its_own_period_is_read() -> None:
    assert _guides(G13) == [("revenue", "Q3 2026", 250.0, 260.0, "$M"),
                            ("revenue", "2026", 1000.0, 1100.0, "$M")]


def test_the_first_range_never_takes_the_second_ranges_period() -> None:
    """Reversed, the full-year range must not read the quarter that follows its partner — a
    full-year range labelled a quarter is the ~4x error `_period_for` exists to prevent."""
    text = ("Acme Reports Second Quarter 2026 Results. The Company expects revenue of $1.00 "
            "billion to $1.10 billion for the full year 2026 and $250 million to $260 million in "
            "the third quarter.")
    assert _guides(text) == [("revenue", "2026", 1000.0, 1100.0, "$M"),
                             ("revenue", "Q3 2026", 250.0, 260.0, "$M")]


def test_a_second_range_whose_period_is_not_its_own_is_refused_aloud() -> None:
    for text in (
        "The Company expects revenue of $250 million to $260 million and $270 million to $280 "
        "million for the third and fourth quarters, respectively.",
        "The Company expects revenue of $250 million to $260 million and $1.00 billion to $1.10 "
        "billion.",
    ):
        got = _guides(text)
        assert all(g[2:4] != (270.0, 280.0) and g[2:4] != (1000.0, 1100.0) for g in got), text
        assert len(_refusals(text)) == 1, text


def test_bellring_shared_range_sentence_stays_one_refusal() -> None:
    """NEGATIVE PIN, BellRing 8-K 0001628280-25-052773 EX-99.1, verbatim: two metrics, two ranges,
    'respectively' — refused once, as before; the second range is not read as either metric."""
    brbr = ("Fiscal Year 2026 Outlook: • Fiscal year 2026 net sales and Adjusted EBITDA* expected "
            "to range between $2.41-$2.49 billion and $425-$455 million, respectively Long-Term")
    assert _guides(brbr) == []
    assert len(_refusals(brbr)) == 1


# --- review round 0 (`/code-review high`) ---------------------------------------------------------
def test_a_sub_line_or_superseded_growth_or_change_guide_is_not_revenue() -> None:
    """D2 and D7 hold in the growth-rate and change-basis loops too, not only for level ranges."""
    for text in (
        "For fiscal 2027, the Company expects subscription revenue growth rate to be in the range "
        "of 10% to 12%.",
        "• Subscription revenue expected to increase 10% to 12% year-over-year",
    ):
        assert [g for g in _guides(text) if g[0] == "revenue"] == [], text
        assert any("'subscription'" in n for n in _refusals(text)), text
    prior = ("Previously, the Company expected the revenue growth rate to be in the range of 4% to "
             "5%. The Company now expects the revenue growth rate to be in the range of 6% to 7%.")
    assert [g[2:4] for g in _guides(prior) if g[0] == "revenue"] == [(6.0, 7.0)]


def test_a_bare_quarter_beside_its_range_is_its_own_period() -> None:
    text = ("The Company expects revenue of $250 million to $260 million in Q3 and $1.00 billion "
            "to $1.10 billion for fiscal 2026.")
    assert _guides(text) == [("revenue", "Q3 2026", 250.0, 260.0, "$M"),
                             ("revenue", "Fiscal 2026", 1000.0, 1100.0, "$M")]


def test_the_second_ranges_quote_carries_its_own_figures_after_a_long_lead_in() -> None:
    text = ("Reflecting the strength of its subscription renewals across every region and the "
            "continued expansion of its enterprise customer base over the last several quarters, "
            "the Company expects revenue of $250 million to $260 million in the third quarter and "
            "$1.00 billion to $1.10 billion for the full year 2026.")
    second = [g for g in parse_release(text, source_ref=_SRC).guidance if g.low == 1000.0]
    assert len(second) == 1 and "$1.10 billion" in second[0].verbatim


def test_maintenance_revenue_is_not_a_reaffirmation() -> None:
    text = ("Previously, the Company expected maintenance revenue of $1.00 billion to $1.05 "
            "billion. The Company now expects revenue of $1.10 billion to $1.15 billion.")
    assert [g[2:4] for g in _guides(text) if g[0] == "revenue"] == [(1100.0, 1150.0)]


# --- review round 1 (in-session `/code-review high`; Codex's review failed on its usage limit) ----
def test_a_current_word_inside_the_prior_marker_does_not_make_it_current() -> None:
    text = ("Previously updated guidance called for revenue of $1.00 billion to $1.05 billion. The "
            "Company now expects revenue of $1.10 billion to $1.15 billion.")
    assert [g[2:4] for g in _guides(text) if g[0] == "revenue"] == [(1100.0, 1150.0)]


def test_an_unrelated_maintaining_does_not_reaffirm_a_prior_range() -> None:
    text = ("While maintaining margins, the Company previously expected revenue of $1.00 billion "
            "to $1.05 billion. The Company now expects revenue of $1.10 billion to $1.15 billion.")
    assert [g[2:4] for g in _guides(text) if g[0] == "revenue"] == [(1100.0, 1150.0)]
    kept = ("The Company is maintaining its prior guidance: revenue of $1.10 billion to $1.15 "
            "billion.")
    assert [g[2:4] for g in _guides(kept)] == [(1100.0, 1150.0)]


def test_a_second_range_followed_by_another_measure_is_not_the_first_metric() -> None:
    text = ("The Company expects revenue of $250 million to $260 million in the third quarter and "
            "$40 million to $45 million for fiscal 2026 in capital expenditures.")
    assert [g[2:4] for g in _guides(text)] == [(250.0, 260.0)]
    assert len(_refusals(text)) == 1


# --- review round 2 (coordinator review of 09015d80) --------------------------------------------
@pytest.mark.parametrize("text", [
    "The Company is raising its previously issued fiscal 2026 guidance for revenue to be in the "
    "range of $1.10 billion to $1.15 billion.",
    "The Company is updating its previously provided outlook for fiscal 2026 revenue to be in the "
    "range of $1.10 billion to $1.15 billion.",
    "The Company's original guidance for fiscal 2026 remains in place: revenue of $1.10 billion "
    "to $1.15 billion.",
    "As initially guided in February, revenue of $1.10 billion to $1.15 billion.",
    "The Company increased its revenue outlook from its prior range; revenue of $1.10 billion to "
    "$1.15 billion is expected for fiscal 2026.",
    "Raises Prior Full-Year Guidance. Raising prior guidance for revenue of $1.10 billion to $1.15 "
    "billion.",
])
def test_a_raised_updated_or_kept_prior_outlook_is_the_current_guide(text: str) -> None:
    """THE BLOCKER (item 1). Each sentence states the CURRENT range; main stores every one, and the
    round-1 head dropped each as superseded, behind a note no reader saw."""
    assert [g[2:4] for g in _guides(text) if g[0] == "revenue"] == [(1100.0, 1150.0)]


def test_simply_good_without_its_bullet_glyphs_keeps_both_guides() -> None:
    """`html_to_text` emits no glyph for an `<li>`: the same filed outlook, its bullets gone."""
    text = SMPL_UPDATE.replace("• ", "")
    got = [g[2:4] for g in _guides(text)]
    assert (1310.0, 1350.0) in got and (217.0, 225.0) in got


def test_an_old_range_beside_a_new_one_after_a_semicolon() -> None:
    text = ("Previously, the Company expected revenue of $1.00 billion to $1.05 billion; revenue "
            "is now expected to be between $1.10 billion and $1.15 billion.")
    assert [g[2:4] for g in _guides(text) if g[0] == "revenue"] == [(1100.0, 1150.0)]


@pytest.mark.parametrize(("text", "metric"), [
    ("The Company expects FY26 revenue of $1.2 billion to $1.3 billion.", "revenue"),
    ("The Company expects FY2026 revenue to be in the range of $1.2 billion to $1.3 billion.",
     "revenue"),
    ("The Company expects fourth-quarter revenue of $250 million to $260 million.", "revenue"),
    ("The Company expects annual revenue of $1.2 billion to $1.3 billion for 2026.", "revenue"),
    ("The Company expects second-half net sales of $600 million to $650 million.", "net sales"),
    ("The Company expects calendar 2026 revenue of $1.2 billion to $1.3 billion.", "revenue"),
    ("Acme Reports Third Quarter 2026 Results. Full Year 2026 Outlook Revenue of $1.2 billion to "
     "$1.3 billion.", "revenue"),
    ("Acme Reports Third Quarter 2026 Results. 2026 Guidance Revenue of $1.2 billion to $1.3 "
     "billion.", "revenue"),
    ("Fiscal 2026 Outlook (in millions) Revenue of $985 to $995 Adjusted EBITDA of $200 to $210",
     "revenue"),
])
def test_period_heading_and_scale_words_are_not_sub_lines(text: str, metric: str) -> None:
    """Item 2: a period, a heading or a table's stated scale before the metric qualifies the
    statement, not the line. Main stores every one."""
    assert [g for g in _guides(text) if g[0] == metric], text
    assert not [n for n in _refusals(text) if "sub-line" in n], text


def test_a_table_heading_states_the_scale_of_its_bare_ranges() -> None:
    text = ("Fiscal 2026 Outlook (in millions) Revenue of $985 to $995 Adjusted EBITDA of $200 "
            "to $210")
    assert [g[2:] for g in _guides(text) if g[0] == "revenue"] == [(985.0, 995.0, "$M")]


@pytest.mark.parametrize("text", [
    "The Company expects revenue of $250 million to $260 million in the third quarter and 8% to "
    "10% for fiscal 2026.",
    "The Company expects adjusted EBITDA of $40 million to $45 million in the third quarter and "
    "20% to 22% for fiscal 2026.",
])
def test_a_percent_range_after_a_dollar_range_is_not_that_metrics_level(text: str) -> None:
    """Item 3: a partner of another unit class is a different measure (growth, margin)."""
    got = _guides(text)
    assert [g[4] for g in got] == ["$M"], got
    assert got[0][1] == "Q3 2026"       # item 4: main's label, the year the sentence states


def test_a_dollar_range_beside_a_percent_one_is_not_refused() -> None:
    text = "• Revenue of $1.10 billion to $1.15 billion and 5% to 7% on a constant currency basis"
    assert [g[2:4] for g in _guides(text)] == [(1100.0, 1150.0)]
    assert _refusals(text) == []


def test_a_yearless_quarter_takes_the_year_its_partner_states() -> None:
    """Item 4: the gap states "the third quarter" only; main reads the year from the sentence."""
    text = ("The Company expects revenue of $250 million to $260 million in the third quarter and "
            "$1.00 billion to $1.10 billion for fiscal 2026.")
    assert _guides(text) == [("revenue", "Q3 2026", 250.0, 260.0, "$M"),
                             ("revenue", "Fiscal 2026", 1000.0, 1100.0, "$M")]


def test_a_second_range_in_a_scope_already_read_is_refused_aloud() -> None:
    """Item 5: one range per metric per scope, and the one not kept is SAID."""
    text = ("The Company expects revenue of $1.10 billion to $1.15 billion for fiscal 2026 and "
            "$1.20 billion to $1.30 billion for fiscal 2027.")
    assert [g[2:4] for g in _guides(text)] == [(1100.0, 1150.0)]
    notes = _refusals(text)
    assert len(notes) == 1 and "2027" in notes[0]


def test_an_unpaired_first_range_never_reads_its_partners_period() -> None:
    """Item 6: main and the round-1 head both filed this full-year range as Q4."""
    text = ("For fiscal 2026, the Company expects revenue of $1.00 billion to $1.10 billion and "
            "$250 million to $260 million in the fourth quarter.")
    got = _guides(text)
    assert [g[1:4] for g in got] == [("fiscal 2026", 1000.0, 1100.0)], got
    assert len(_refusals(text)) == 1
    respectively = ("The Company expects revenue of $250 million to $260 million and $270 million "
                    "to $280 million for the third and fourth quarters, respectively.")
    assert _guides(respectively) == []          # main labelled the quarterly range annual
    assert len(_refusals(respectively)) == 1


def test_one_refusal_per_stated_guide() -> None:
    """Item 7: two change patterns match one statement; the reader gets one note."""
    text = "• Subscription revenue expected to increase 10% to 12% year-over-year"
    assert len(_refusals(text)) == 1


def test_unchanged_elsewhere_in_the_clause_reaffirms_nothing() -> None:
    """Item 8, the class of round 1's "maintaining" fix."""
    text = ("With pricing unchanged, the Company previously expected revenue of $1.00 billion to "
            "$1.05 billion. The Company now expects revenue of $1.10 billion to $1.15 billion.")
    assert [g[2:4] for g in _guides(text) if g[0] == "revenue"] == [(1100.0, 1150.0)]


def test_a_verb_that_states_the_guide_is_not_a_sub_line() -> None:
    """Item 2's class, from the coordinator's probe file: main stores it."""
    text = ("The Company is raising revenue to be in the range of $1.2 billion to $1.3 billion for "
            "fiscal 2026.")
    assert [g[2:] for g in _guides(text)] == [(1200.0, 1300.0, "$M")]


def test_a_plural_scale_word_is_a_scale() -> None:
    """D1's refusal must not fire on "millions": main stores $500–550M."""
    text = "For fiscal 2026, the Company expects revenue of $500 to $550 millions."
    assert [g[2:] for g in _guides(text)] == [(500.0, 550.0, "$M")]


def test_a_comparison_after_the_second_range_keeps_both_periods() -> None:
    """The first range keeps the quarter beside it (never the annual default), and a comparison
    after its partner's period does not unpair them."""
    text = ("The Company expects revenue of $250 million to $260 million in the third quarter and "
            "$1.00 billion to $1.10 billion for the full year 2026 compared to $0.9 billion in "
            "2025.")
    assert _guides(text) == [("revenue", "Q3 2026", 250.0, 260.0, "$M"),
                             ("revenue", "2026", 1000.0, 1100.0, "$M")]
