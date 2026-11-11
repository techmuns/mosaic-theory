"""TeamNostra fix request 2, order 4's E2 remainder: RE2-D20's unread guide periods, and RE2-D17's
one-offs with no period.

RE2-D20. #976 flagged every guide filed under the `next-fy` default. On the 27 committed pages
there were 21, and every one sat where its release DOES state the period. Each shape below is the
real text of one of them, from the cited EX-99.1, cut to the sentences the reader sees.

RE2-D17. A one-off item carried no period, so a six-month impairment, or a charge "recorded in the
second quarter" quoted in a third-quarter release, was stored exactly as the quarter's. It is now
read the way an actual's period is.
"""
from __future__ import annotations

import json
import pathlib

from vinci.dossier.mechanical import _compose_gap_drivers, _fy_impairment
from vinci.dossier.schemas import OneOffItem, ReleaseExtract
from vinci.edgar.release_parse import GUIDANCE_PERIOD_DEFAULT_PREFIX, parse_release


def _guides(text: str, src: str = "8-K x EX-99.1") -> dict[str, str]:
    r = parse_release(text, source_ref=src)
    return {g.metric: g.period for g in r.guidance}


def _defaults(text: str) -> list[str]:
    r = parse_release(text, source_ref="8-K x EX-99.1")
    return [f for f in r.qa_flags if f.startswith(GUIDANCE_PERIOD_DEFAULT_PREFIX)]


# --- RE2-D20: a guide's period is read where its release states it --------------------------------

#: Simply Good Foods, 8-K 0001702744-26-000010 EX-99.1, verbatim: the outlook's header is written
#: straight after the summary list's last bullet, with no stop between.
_SMPL = ("Second Quarter Summary: (1) • Net sales of $326.0 million versus $359.7 million • Net "
         "loss of $159.7 million versus net income of $36.7 million • Loss per diluted share of "
         "$1.73 versus earnings per diluted share of $0.36 • Adjusted Diluted EPS (2) of $0.45 "
         "versus $0.46 • Adjusted EBITDA (3) of $55.5 million versus $68.0 million Updating "
         "Fiscal Year 2026 (4) Outlook: • Net sales expected to range between $1.31 and $1.35 "
         "billion, or -10% to -7% year-over-year • Gross margins expected to decline between 300 "
         "and 350 basis points year-over-year • Adjusted EBITDA expected to range between $217 "
         "and $225 million, or -22% to -19% year-over-year")


def test_re2_d20_a_header_glued_to_the_last_bullet_heads_its_own_list() -> None:
    """(+) THE RED, on base: adjusted EBITDA and gross margin `next-fy`, flagged. The walk-back read
    the summary list's header ("Second Quarter Summary: (1)"), a results heading, for the outlook's
    bullets. All three now read the year the outlook's own header states."""
    got = _guides(_SMPL)
    assert got["adjusted ebitda"] == "Fiscal 2026" and got["gross margin"] == "Fiscal 2026"
    assert got["net sales"] == "Fiscal 2026"
    assert _defaults(_SMPL) == []


#: Burlington, 8-K 0001193125-26-369502 EX-99.1, verbatim from the sentence before the list: one
#: bullet holds a second sentence ending ";".
_BURL = ("As we noted earlier, we believe it is important to pass on those savings to our "
         "customers and drive even stronger value offerings. For Fiscal Year 2026 (the 52-weeks "
         "ending January 30, 2027), the Company now expects: • Total sales to increase in the "
         "range of 10% to 11% on top of the 9% increase during Fiscal 2025; this assumes "
         "comparable store sales will increase in the range of 3% to 4%, on top of the 2% "
         "increase during Fiscal 2025; • Capital expenditures, net of landlord allowances, to be "
         "approximately $875 million. This excludes any potential costs related to the "
         "relocation of our corporate headquarters, which is currently being evaluated. The "
         "timing and amount of such relocation expenditures are still uncertain; • To open "
         "approximately 115 net new stores; • Depreciation and amortization to be approximately "
         "$460 million; • Adjusted EBIT margin to increase in the range of 20 to 40 basis points "
         "versus Fiscal 2025; excluding $16 million of anticipated expenses associated with "
         "bankruptcy acquired leases in Fiscal 2026 and $35 million in Fiscal 2025; • Net "
         "interest expense to be approximately $55 million; • An Adjusted Effective Tax Rate of "
         "approximately 25%; and • Adjusted EPS in the range of $11.77 to $11.97")


def test_re2_d20_a_semicolon_tail_is_the_last_items_end_never_a_header() -> None:
    """(+) THE RED, on base: adjusted EPS `next-fy`. "The timing and amount of such relocation
    expenditures are still uncertain;" was taken for the list's header. The header is the
    sentence that opens the list."""
    assert _guides(_BURL)["adjusted eps"] == "Fiscal 2026"
    assert _defaults(_BURL) == []


#: Verra Mobility, 8-K 0001193125-26-335111 EX-99.1: the header says what its outlook rests on.
_VRRM_H1 = ("We are providing the following forward-looking guidance, which includes Adjusted "
            "EBITDA, Adjusted EPS, and Free Cash Flow, all of which are non-GAAP financial "
            "measures (defined below). Based on our first half 2026 results and our outlook for "
            "the remainder of the year, we are revising our 2026 full year financial outlook to "
            "the following: • Total Revenue of $945 million to $965 million • Adjusted EBITDA of "
            "$360 million to $370 million • Adjusted EPS of $1.11 to $1.17")
#: ...and 8-K 0001628280-26-068453 EX-99.1, the next quarter's.
_VRRM_Q3 = ("2026 Full Year Guidance Based on year-to-date 2026 results and our outlook for the "
            "fourth quarter, we are reaffirming 2026 full year guidance for all financial "
            "measures, provided in our second quarter earnings announcement, dated August 5, "
            "2026. • Total Revenue of $945 million to $965 million • Adjusted EBITDA of $360 "
            "million to $370 million • Adjusted EPS of $1.11 to $1.17")


def test_re2_d20_a_header_that_names_its_basis_states_one_period() -> None:
    """(+) THE RED, on base, for both: every guide `next-fy`, flagged. "first half 2026 results"
    and "year-to-date 2026 results" name the REPORTED basis, and the clause the forward verb opens
    ("reaffirming 2026 full year guidance for all financial measures") names the guided one."""
    for text in (_VRRM_H1, _VRRM_Q3):
        got = _guides(text)
        assert got["adjusted ebitda"] == "2026" and got["adjusted eps"] == "2026", got
        assert _defaults(text) == []
    assert _guides(_VRRM_Q3)["revenue"] == "2026"


#: EPAM, 8-K 0001352010-25-000053 EX-99.1, verbatim from the sentence before: a section title, a
#: sub-title, and the sentence.
_EPAM = ("Included in this number were approximately 56,100 delivery professionals, an increase "
         "of 0.5% from June 30, 2025. 2025 Outlook - Full Year and Fourth Quarter Full Year EPAM "
         "expects the following for the full year: • Based on the strength of organic constant "
         "currency revenue growth and updates to our foreign exchange rate assumptions, the "
         "Company raises its expected revenues to be in the range of $5.430 billion to $5.445 "
         "billion")


def test_re2_d20_a_full_year_clause_under_a_two_period_title_is_the_year() -> None:
    """(+) THE RED, on base: revenue `next-fy`. The header names the full year AND the fourth
    quarter; the clause "expects the following for the full year" names the one these bullets are,
    and the title names its year."""
    assert _guides(_EPAM)["revenue"] == "2025"
    assert _defaults(_EPAM) == []


#: Vital Farms, 8-K 0001193125-26-336692 EX-99.1, verbatim: the headline states the year once, for
#: two.
_VITL = ("Announces Termination of Stock Repurchase Program Reiterates Fiscal Year 2026 Net "
         "Revenue Outlook of $775 Million to $800 Million and Adjusted EBITDA Outlook of $0 "
         "Million to $10 Million AUSTIN, TX – August 6, 2026 – Vital Farms (Nasdaq: VITL), a "
         "Certified B Corporation that offers a range of ethically produced foods nationwide,")


def test_re2_d20_a_guide_joined_by_and_takes_its_partners_period() -> None:
    """(+) THE RED, on base: adjusted EBITDA `next-fy` beside a revenue guide read as 2026. The two
    are one phrase, joined by "and", and its year sits beyond the second's 60-character lead-in."""
    got = _guides(_VITL)
    assert got["adjusted ebitda"] == got["revenue"] == "2026"
    assert _defaults(_VITL) == []


#: Simply Good Foods, 8-K 0001702744-25-000035 EX-99.1, verbatim: an outlook stated in prose.
_SMPL_PROSE = ("Fiscal Year 2025 Outlook Considering our year-to-date performance on the top and "
               "bottom line, and trends to begin the fourth quarter, we are narrowing our "
               "full-year outlook. The Company continues to expect organic net sales growth to "
               "be driven primarily by volume. In addition, the Company is maintaining its "
               "outlook for full year gross margin to decline by approximately 200 basis points "
               "year-over-year.")


def test_re2_d20_a_full_year_its_own_clause_states_is_the_full_year() -> None:
    """(+) THE RED, on base: gross margin `next-fy`. "outlook for full year gross margin" states the
    scope with no year: FY, never the unread default."""
    assert _guides(_SMPL_PROSE)["gross margin"] == "FY"
    assert _defaults(_SMPL_PROSE) == []


def test_re2_d20_neg_a_forward_clause_naming_a_quarter_gives_the_quarter() -> None:
    """(-) CONSTRUCTED, in Verra Mobility's shape. The fence that keeps a quarterly list off an
    annual label: the same basis-and-clause reading, with a clause that names the third quarter,
    gives the third quarter."""
    text = ("Results were reported above. 2026 Outlook Based on our first half 2026 results, we "
            "expect the following for the third quarter: • Total Revenue of $245 million to $250 "
            "million • Adjusted EBITDA of $90 million to $95 million")
    got = _guides(text)
    assert got["adjusted ebitda"] == "Q3 2026", got


def test_re2_d20_neg_a_glued_run_without_an_outlook_noun_is_not_a_header() -> None:
    """(-) CONSTRUCTED. Only a run ending in an OUTLOOK noun and a colon heads a list: a highlights
    heading glued to the last bullet is not taken for one, so the guide with no period of its own
    stays on the flagged default rather than borrow the heading's quarter."""
    text = ("Results were reported above. Second Quarter Summary: • Net sales of $326.0 million "
            "versus $359.7 million Third Quarter Highlights: • Net sales expected to range "
            "between $1.31 and $1.35 billion")
    assert _guides(text)["net sales"] == "next-fy"
    assert len(_defaults(text)) == 1


def test_re2_d20_neg_a_joined_guide_with_its_own_period_keeps_it() -> None:
    """(-) CONSTRUCTED. A partner's period fills only an UNREAD one: a joined guide that states its
    own quarter keeps that quarter."""
    text = ("The Company expects fiscal 2026 revenue of $1.0 billion to $1.1 billion and fourth "
            "quarter adjusted EBITDA of $40 million to $45 million.")
    assert _guides(text)["adjusted ebitda"] == "Q4"


# --- RE2-D17: a one-off carries the period its release places it in ------------------------------

#: BellRing Brands, 8-K 0001628280-26-052137 EX-99.1 — a third-quarter release: its headline and one
#: later sentence, verbatim, joined [cut].
_BRBR = ("BellRing Brands Reports Results for the Third Quarter of Fiscal Year 2026; Updates "
         "Fiscal Year 2026 Outlook. In addition, gross profit and adjusted gross profit were "
         "impacted by a $10.0 million charge for excess bottle inventory recorded in the third "
         "quarter and an $11.3 million inventory-related charge recorded in the second quarter "
         "associated with a third-party supplied ingredient that did not meet BellRing’s quality "
         "requirements")


def _one_offs(text: str) -> dict[float, str | None]:
    return {o.amount: o.period for o in parse_release(text, source_ref="8-K x EX-99.1").one_offs}


def test_re2_d17_a_charge_carries_the_period_its_release_places_it_in() -> None:
    """(+) THE RED, on base: neither item had a period, so the second quarter's $11.3M charge read
    as this quarter's beside it."""
    got = _one_offs(_BRBR)
    assert got[11.3] == "Q2 2026", got


def test_re2_d17_a_year_to_date_charge_keeps_its_span() -> None:
    """(+) Verra Mobility, 8-K 0001193125-26-335111 EX-99.1: a six-month impairment in a
    second-quarter release. An actual has no label for the span, so the item keeps the release's
    words — it is never filed as the quarter's."""
    text = ("Goodwill and Intangible Assets Impairments We recorded a $64.0 million impairment to "
            "goodwill in our Parking Solutions segment during the six months ended June 30, 2026, "
            "which is presented in a separate line item on the consolidated statements of "
            "operations.")
    assert _one_offs(text)[64.0] == "six months ended June 30, 2026"


def test_re2_d17_a_bare_year_is_the_year() -> None:
    """(+) Gartner, 8-K 0000749251-26-000028 EX-99.1, in a fourth-quarter release: "$150 million of
    goodwill impairment related to Digital Markets in 2025". Its table shows "—" for the quarter and
    155 for the year, so the year is the period, not the quarter its section heading names."""
    # its headline and the footnote, verbatim, joined [cut]
    text = ("Gartner Reports Fourth Quarter 2025 Financial Results. (d) Includes "
            "$150 million of goodwill impairment related to Digital Markets in 2025 in addition to "
            "impairment loss for lease related assets, net of a reduction in lease liabilities.")
    assert _one_offs(text)[150.0] == "2025"


def test_re2_d17_a_prior_year_item_says_so() -> None:
    """(+) Eli Lilly, 8-K 0000059478-26-000043 EX-99, a first-quarter 2026 release: "In Q1 2025,
    there was a charge of $35 million related to intangible asset impairments" is last year's."""
    # its opening sentence and the two later ones, verbatim, joined [cut]
    text = ("Eli Lilly and Company (NYSE: LLY) today announced its financial results for the "
            "first quarter of 2026 and provided updated 2026 financial guidance. Asset "
            "impairment, restructuring and other special charges of $279 million in Q1 2026 were "
            "primarily related to litigation matters. In Q1 2025, there was a charge of $35 "
            "million related to intangible asset impairments.")
    assert _one_offs(text)[35.0] == "Q1 2025"


def _release(*items: OneOffItem) -> ReleaseExtract:
    return ReleaseExtract(source_ref="8-K x EX-99.1", one_offs=list(items))


def _item(amount: float, desc: str, period: str | None) -> OneOffItem:
    return OneOffItem(amount=amount, description=desc, verbatim=desc, source_ref="8-K x EX-99.1",
                      period=period)


def test_re2_d17_the_gap_driver_line_states_the_period() -> None:
    """(+) The drawdown driver line carries the period beside the item, where one is read."""
    got = _compose_gap_drivers(_release(_item(11.3, "inventory-related charge", "Q2 2026")))
    assert got is not None and "$11.3M inventory-related charge (Q2 2026)" in (got.value or "")


def test_re2_d17_the_full_year_impairment_is_never_a_quarters() -> None:
    """(+/-) The margin cross-check divides by the YEAR: a quarter's or a six-month impairment is
    passed over, a year's is taken, and one whose period is not stated is taken as before."""
    q = _item(35.0, "intangible asset impairments", "Q1 2025")
    ytd = _item(64.0, "impairment to goodwill", "six months ended June 30, 2026")
    fy = _item(150.0, "goodwill impairment", "2025")
    unread = _item(32.5, "inventory impairment charge", None)
    assert _fy_impairment([_release(q, ytd)]) is None
    assert _fy_impairment([_release(q, fy)]) == 150.0
    assert _fy_impairment([_release(unread)]) == 32.5


def test_re2_d17_neg_every_committed_one_off_round_trips_byte_identically() -> None:
    """(-) End to end on the committed pages: every one-off re-serialises to exactly its committed
    JSON — one read before the field existed with no `period` key, so no page moves until it is
    rebuilt. A STRUCTURAL invariant only: a rebuilt page carrying a period still round-trips, so
    the pin does not rot on the first re-assembly (code review)."""
    n = 0
    for p in sorted(pathlib.Path("data/dossiers").glob("*/dossier.json")):
        ps = (json.loads(p.read_text()).get("mechanical") or {}).get("primary_source") or {}
        for rel in ps.get("releases") or []:
            for held in rel.get("one_offs") or []:
                n += 1
                assert held.get("period", "unset") is not None, p.parent.name  # absent, never null
                assert json.loads(OneOffItem.model_validate(held).model_dump_json()) == held
    assert n > 0, "the committed pages carry one-offs to check"


# --- code review (round 0): the new readers' fences ----------------------------------------------


def test_review_a_partner_never_reads_the_results_clause_of_its_headline() -> None:
    """(-) CONSTRUCTED, in Vital Farms' headline shape with its results clause before the ";". The
    partner window reached "Third Quarter" and filed the full-year EBITDA guide as Q3 2026."""
    text = ("Vital Farms Reports Third Quarter 2026 Financial Results; Reiterates Fiscal Year 2026 "
            "Net Revenue Outlook of $775 Million to $800 Million and Adjusted EBITDA Outlook of $0 "
            "Million to $10 Million AUSTIN, TX")
    got = _guides(text)
    assert got["adjusted ebitda"] == got["revenue"] == "2026", got


def test_review_a_guide_after_a_comparisons_year_borrows_no_period() -> None:
    """(-) CONSTRUCTED. "… in the third quarter of 2025 and adjusted EBITDA is expected …" joins a
    comparison's YEAR, not a partner range: Q3 2025 on a forward guide was the read, and the guide
    must stay on the flagged default."""
    text = ("Third quarter revenue was $500 million, compared to $480 million in the third quarter "
            "of 2025 and adjusted EBITDA is expected to be $90 million to $95 million.")
    assert _guides(text)["adjusted ebitda"] == "next-fy"
    assert len(_defaults(text)) == 1


def test_review_a_glued_two_period_header_is_not_cut_to_its_year() -> None:
    """(-) CONSTRUCTED, in Simply Good's glued shape. "Fourth Quarter and Fiscal Year 2026
    Outlook:" names two periods; cut at its "and" it read as Fiscal 2026 for every bullet."""
    text = ("Second Quarter Summary: • Net sales of $326.0 million versus $359.7 million • "
            "Adjusted EBITDA of $55.5 million versus $68.0 million Fourth Quarter and Fiscal "
            "Year 2026 Outlook: • Net sales expected to range between $1.31 and $1.35 billion "
            "• Adjusted EBITDA expected to range between $217 and $225 million")
    assert "Fiscal 2026" not in _guides(text).values()


def test_review_a_header_with_two_forward_clauses_is_no_answer() -> None:
    """(-) CONSTRUCTED. Two forward verbs, a quarter's and a year's: which heads the bullets is not
    stated, so neither is taken — the guides stay on the flagged default."""
    text = ("Results above. Based on our first half 2026 results, we expect third quarter 2026 "
            "revenue growth and are reaffirming full year guidance as follows: • Total Revenue of "
            "$245 million to $250 million • Adjusted EBITDA of $90 million to $95 million")
    assert set(_guides(text).values()) == {"next-fy"}


def test_review_a_year_to_date_charge_without_an_end_date_keeps_its_words() -> None:
    """(-) CONSTRUCTED. "in the first nine months of 2026" and "during the six-month period ended"
    were None — read as unstated, and so taken as the year's impairment."""
    first9 = ("XYZ Reports Third Quarter 2026 Results. The Company recorded a $40.0 million "
              "impairment charge in the first nine months of 2026.")
    six = ("XYZ Reports Second Quarter 2026 Results. We recorded a $40.0 million impairment during "
           "the six-month period ended June 30, 2026.")
    assert _one_offs(first9)[40.0] == "first nine months"
    assert _one_offs(six)[40.0] == "six-month period ended June 30, 2026"
    assert _fy_impairment([parse_release(first9, source_ref="x")]) is None


def test_review_a_forward_charges_year_is_not_its_period() -> None:
    """(-) CONSTRUCTED. A bare year on a forward charge, or one after the release's own, is the
    guard `_figure_period` applies to every actual: "expect to record … in 2027" is no period."""
    text = ("XYZ Reports Third Quarter 2026 Results. We expect to record a $40.0 million "
            "impairment charge in 2027.")
    assert _one_offs(text)[40.0] is None


def test_review_an_empty_label_is_no_period() -> None:
    """(-) CONSTRUCTED. A bare excerpt with no year: the reader's empty label is stored as no
    period, never as `"period": ""`."""
    r = parse_release("We recorded a $40.0 million impairment charge for the quarter.",
                      source_ref="x")
    assert [o.period for o in r.one_offs] == [None]
    assert "period" not in json.loads(r.one_offs[0].model_dump_json())


# --- RE2-D6's residual: a component named inside the figure is not the figure -------------------

#: Par Pacific (PARR), 8-K 0001628280-25-048903 EX-99, verbatim: its headline and the sentence,
#: joined [cut].
_PARR = ("PAR PACIFIC HOLDINGS REPORTS THIRD QUARTER 2025 RESULTS. Third quarter 2025 Adjusted Net "
         "Income was $302.6 million, including an SRE impact of $195.9 million, compared to an "
         "Adjusted Net Loss of $(5.5) million in the third quarter of 2024.")


def test_re2_d6_a_component_inside_the_figure_is_not_its_lead() -> None:
    """(+) THE RED, on base: the Q3 2024 comparison was set aside silently. `_sub_unit` took the
    SRE impact, the last amount before "compared to", for the current figure, so $(5.5) read as a
    sub-unit's prior. The component is skipped as a change amount is, and the comparison is read,
    signed (RE2-D6's own fix, #962)."""
    rows = {(r.metric, r.period): r.value
            for r in parse_release(_PARR, source_ref="8-K x EX-99.1").reconciliation}
    assert rows[("adjusted net income", "Q3 2025")] == 302.6
    assert rows[("adjusted net income", "Q3 2024")] == -5.5, rows


def test_re2_d6_neg_a_real_sub_units_comparison_is_still_set_aside() -> None:
    """(-) CONSTRUCTED. The sub-unit rule still holds where the lead IS a different figure: a
    segment's $0.9 million against the company's $27.6 million keeps its comparison out."""
    text = ("Fourth Quarter 2025 Results. Adjusted EBITDA was $27.6 million. Adjusted EBITDA was "
            "$0.9 million, compared to $1.2 million in the fourth quarter of 2024.")
    rows = {(r.metric, r.period): r.value
            for r in parse_release(text, source_ref="8-K x EX-99.1").reconciliation}
    assert ("adjusted ebitda", "Q4 2024") not in rows, rows


def test_re2_d6_neg_an_exclusion_naming_the_figure_is_its_lead() -> None:
    """(-) CONSTRUCTED (code review). "excluding special items, Adjusted Net Income of $302.6
    million" names the FIGURE after its exclusion, not a part of the GAAP figure before it: its
    comparison is the company's, and is read."""
    for joint in (" and, excluding", "; excluding"):
        text = ("PAR PACIFIC HOLDINGS REPORTS THIRD QUARTER 2025 RESULTS. Third quarter 2025 "
                "Adjusted Net Income was $302.6 million. Net income of $100.0 million"
                f"{joint} special items, Adjusted Net Income of $302.6 million, compared to an "
                "Adjusted Net Loss of $(5.5) million in the third quarter of 2024.")
        rows = {(r.metric, r.period): r.value
                for r in parse_release(text, source_ref="8-K x EX-99.1").reconciliation}
        assert rows.get(("adjusted net income", "Q3 2024")) == -5.5, (joint, rows)


def test_re2_d20_neg_a_lowercase_quarter_header_keeps_its_quarter() -> None:
    """(-) CONSTRUCTED (code review). A header whose period words are lowercase is still one
    header: "Fourth quarter 2026 Outlook:", glued or after a stop, and a whole header sentence
    after a stop, give the quarter — never the year a cut run leaves."""
    for head in (" Fourth quarter 2026 Outlook:", ". Fourth quarter 2026 Outlook:",
                 ". For the fourth quarter of 2026, the Company provides the following Outlook:"):
        text = ("Third Quarter 2026 Summary: • Net sales of $300.0 million versus $290.0 million"
                f"{head} • Net sales expected to be $100 million to $110 million • Adjusted "
                "EBITDA expected to be $20 million to $25 million")
        got = _guides(text)
        assert got == {"net sales": "Q4 2026", "adjusted ebitda": "Q4 2026"}, (head, got)


# --- RE2-D10's other half: a filing read with no doubt statement is CHECKED-ABSENT ---------------

#: TECX 10-Q 0001193125-26-450019, verbatim: its contents entry naming the notes (to its page
#: number), and the ASU 2014-15 evaluation sentence (an evaluation, never a doubt), joined [cut].
_TECX_10Q = ("Notes to Unaudited Condensed Consolidated Financial Statements 9. In accordance "
             "with Accounting Standards Update (“ASU”) 2014-15, Disclosure of Uncertainties "
             "about an Entity’s Ability to Continue as a Going Concern (Subtopic 205-40), the "
             "Company has evaluated whether there are conditions and events, considered in the "
             "aggregate, that raise substantial doubt about the Company’s ability to continue as "
             "a going concern within one year after the date that these condensed consolidated "
             "financial statements are issued.")


def test_re2_d10_a_filing_read_with_no_doubt_is_checked_absent() -> None:
    """(+) THE RED, on base: None, the same as a filing never read, so the digest's "none stated
    (checked, absent)" was unreachable. The read is now a state, bound to the filing."""
    from vinci.edgar.filing_sections import parse_filing_sections
    gc = parse_filing_sections(_TECX_10Q, source_ref="10-Q 0001193125-26-450019").going_concern
    assert gc is not None, "the filing was read; its answer is a state"
    assert gc.substantial_doubt is False and gc.verbatim == ""
    assert gc.source_ref == "10-Q 0001193125-26-450019"


def test_re2_d10_neg_text_without_its_notes_makes_no_claim() -> None:
    """(-) Text the reader cannot show it read as a filing — no notes heading — still answers None:
    "checked, absent" is never claimed for a fragment."""
    from vinci.edgar.filing_sections import parse_filing_sections
    frag = _TECX_10Q.split("Statements 9. ", 1)[1]
    assert parse_filing_sections(frag, source_ref="10-Q x").going_concern is None


def test_re2_d10_neg_a_stated_doubt_is_unchanged() -> None:
    """(-) MVST's real conclusion (10-Q 0001628280-26-055372), under a notes heading [cut], is
    still SUBSTANTIAL DOUBT, verbatim."""
    from vinci.edgar.filing_sections import parse_filing_sections
    text = ("Notes to Condensed Consolidated Financial Statements. These conditions and events "
            "raise substantial doubt about the Company's ability to continue as a going concern "
            "within one year after the date that these consolidated financial statements are "
            "issued.")
    gc = parse_filing_sections(text, source_ref="10-Q x").going_concern
    assert gc is not None and gc.substantial_doubt is True and "substantial doubt" in gc.verbatim


# --- code review (round 0, second pass) ---------------------------------------------------------


def test_review_an_excluding_phrase_before_the_figure_itself_is_not_a_component() -> None:
    """(-) CONSTRUCTED, in Target's shape (`test_release_amount_scale`). "excluding …" before the
    ONLY figure names what the figure leaves out, so that figure is still the lead: the quarter's
    comparison with a bare year is refused, never filed as FY2024."""
    from vinci.edgar import release_parse as rp
    text = ("Target Corporation Reports Fourth Quarter and Full-Year 2025 Earnings MINNEAPOLIS "
            "(March 3, 2026) – Target today announced its results. The Company reported "
            "fourth-quarter Adjusted EPS, excluding the litigation charge, of $2.44, compared with "
            "Adjusted EPS of $2.41 in 2024.")
    r = parse_release(text, source_ref="t")
    assert ("adjusted eps", "2024") not in {(x.metric, x.period) for x in r.reconciliation}
    assert any("a quarter compared with a bare year" in f for f in r.qa_flags
               if f.startswith(rp.RECON_REFUSAL_PREFIX))


def test_review_an_excluding_sub_unit_keeps_its_comparison_out() -> None:
    """(-) CONSTRUCTED. A segment whose figure follows "excluding fuel," is still a sub-unit: its
    $1.2 million prior never stands as the company's Q4 2024."""
    text = ("Fourth Quarter 2025 Results. Adjusted EBITDA was $27.6 million. Werner Logistics, "
            "excluding fuel, had adjusted EBITDA of $0.9 million, compared to adjusted EBITDA of "
            "$1.2 million in the fourth quarter of 2024.")
    rows = {(r.metric, r.period) for r in parse_release(text, source_ref="t").reconciliation}
    assert ("adjusted ebitda", "Q4 2024") not in rows, rows


def test_review_a_fiscal_year_read_through_its_clause_keeps_fiscal() -> None:
    """(+/-) CONSTRUCTED from EPAM's header. The two-period title read at its forward clause
    labels the year as the title states it — "Fiscal 2025" where it says fiscal, as the one-period
    title does, and the bare year where it does not."""
    fiscal = _EPAM.replace("2025 Outlook - Full Year", "Fiscal 2025 Outlook - Full Year")
    one = _EPAM.replace("2025 Outlook - Full Year and Fourth Quarter",
                        "Fiscal 2025 Full Year Outlook")
    assert _guides(fiscal)["revenue"] == _guides(one)["revenue"] == "Fiscal 2025"
    assert _guides(_EPAM)["revenue"] == "2025"


def test_review_a_forward_charges_span_is_not_its_period() -> None:
    """(-) CONSTRUCTED. The forward guard covers a year-to-date span as it does a bare year."""
    text = ("XYZ Reports Third Quarter 2026 Results. We expect to record a $40.0 million "
            "impairment charge in the first half of 2027.")
    assert _one_offs(text)[40.0] is None
