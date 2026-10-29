"""A release figure is read from what its own text STATES — its span, its sign, its role, its name.

Four defects from one family (audit E2), each a figure a committed page carried wrong or not at all:

* SPAN (E2-D5) — FuboTV's trailing-twelve-month adjusted EBITDA ($77.9M) was filed as Q1 2026
  while the quarter's own "Pro Forma Adjusted EBITDA 2 of $41.4 million" was refused for its
  footnote digit.
* SIGN (E2-D10) — Vital Farms' "Adjusted EBITDA loss of $26.6 million" was dropped: the sign was
  read from the metric NAME, and a loss stated in words matched nothing.
* ROLE (E2-D12) — Verra Mobility's "$94.3 million mainly due to the impairments" (a change in the
  cash-flow reconciliation) was stored as a one-off impairment beside the real $64.0M and $40.4M.
* NAME (E2-D11) — "Revenues of" was not read: EPAM, Werner and Microvast lost their headline
  revenue.

THE FIXTURES are real exhibit text, cut at sentence or bullet boundaries, and each was checked at
generation to emit, for every figure pinned here, what its FULL exhibit emits from the SEC cache.
Every pin below fails on main at c51c286a; each guard carries the negative pin it must not break.
"""
from __future__ import annotations

from vinci.dossier.schemas import ReleaseExtract
from vinci.edgar import release_parse as rp

#: 8-K 0001193125-26-336692 EX-99.1 (Vital Farms, Q2 2026) — the highlights list
_VITL_Q2_26 = (
    "Vital Farms Reports Second Quarter 2026 Financial Results AUSTIN, TX – August 6, 2026 – Vital "
    "Farms (Nasdaq: VITL), a Certified B Corporation that offers a range of ethically produced "
    "foods nationwide, today reported financial results for its second quarter ended June 28, "
    "2026. Financial highlights for the second quarter ended June 28, 2026, compared to the second "
    "quarter ended June 29, 2025, where applicable, include: • Net Revenue decreased 10.1% to "
    "$166.0 million, compared to $184.8 million • Gross Margin of 6.6%, compared to 38.9% • Net "
    "Loss of $31.1 million, compared to Net Income of $16.6 million • Net Loss per Diluted Share "
    "of "
    "$0.72, compared to Net Income per Diluted Share of $0.36 • Adjusted EBITDA loss of $26.6 "
    "million and Adjusted Net Loss of $20.0 million, including $24.8 million in certain pre-tax "
    "expenses not added back to Adjusted EBITDA or Adjusted Net Loss: $19.5 million from excess "
    "breaker sales, $1.5 million of related shipping and distribution costs, $0.8 million of "
    "farmer contract amendment amortization, and $3.0 million of consulting fees associated with "
    "our feed cost savings program 1 • Adjusted Net Loss per Diluted Share of $0.47, compared to "
    "Adjusted Net Income per Diluted Share of $0.36 1"
)
#: the same exhibit's prose — the loss stated the second way
_VITL_Q2_26_PROSE = (
    "Vital Farms Reports Second Quarter 2026 Financial Results Net loss per diluted share was "
    "$0.72 "
    "for the second quarter of 2026, compared to net income per diluted share of $0.36 in the "
    "prior-year quarter. Adjusted EBITDA was a loss of $26.6 million in the second quarter of "
    "2026, "
    "compared to Adjusted EBITDA of $29.9 million in the second quarter of 2025."
)

#: 8-K 0001493152-26-021406 EX-99.1 (FuboTV, Q2 fiscal 2026) — a footnote digit on a current figure
_FUBO_Q2_26 = (
    "May 6, 2026 Fellow Shareholders: The second quarter of the 2026 fiscal year marked an "
    "important milestone as the first full quarter of our combined Fubo and Hulu + Live TV "
    "business "
    "following the successful close of the transaction. From a profitability standpoint, we "
    "delivered a Net Loss of $6.2 million and Adjusted EBITDA 1 of $37.7 million for the quarter, "
    "compared to Pro Forma "
    "Net Loss of $40.9 million and Pro Forma Adjusted EBITDA 1 of $1.4 million in the prior year "
    "period, reflecting operating leverage in the business."
)

#: 8-K 0000027419-26-000034 EX-99 (Target, Q2 2026) — the digit on a per-share figure
_TGT_Q2_26 = (
    "Target Corporation Reports Second Quarter Earnings • Second quarter net sales grew 5.3 "
    "percent "
    "over last year, with comparable sales growth of 3.8 percent driven by a 3.6 percent increase "
    "in comparable traffic. ◦ Non-merchandise sales grew over 20 percent, reflecting strong growth "
    "in Roundel ad revenue, Target Circle 360 membership revenue, and the Target+ marketplace. • "
    "Second quarter GAAP and Adjusted EPS 1 was $4.11, compared with prior-year GAAP and Adjusted "
    "EPS of $2.05, an increase of 100 percent, which included tariff refund 2 benefits of $1.65 "
    "for "
    "Q2 2026."
)

#: 8-K 0001193125-26-335111 EX-99.1 (Verra Mobility, Q2 2026) — the cash-flow sentence and the
#: impairment note it was confused with
_VRRM_Q2_26 = (
    "Verra Mobility Announces Second Quarter 2026 Financial Results • Total revenue of $263.6 "
    "million Net (loss) income quarter-over-quarter decreased by $86.8 million, from $38.6 million "
    "in 2025 to $(48.2) million in 2026. The aggregate adjustments to reconcile net (loss) "
    "income to net cash provided by operating activities increased $94.3 million mainly due to the "
    "impairments on goodwill and intangible assets recorded for the current period, a prior period "
    "uncertain tax position reserve release and the mark-to-market adjustment on the share-based "
    "proceeds, partially offset by decreases in stock-based compensation, deferred income taxes "
    "and "
    "credit loss expense. Goodwill and Intangible Assets Impairments We recorded a $64.0 million "
    "impairment to goodwill in our Parking Solutions segment during the six months ended June 30, "
    "2026, which is presented in a separate line item on the consolidated statements of "
    "operations. This was in connection with our 2026 assessment of goodwill impairment which "
    "determined that the Parking Solutions reporting unit carrying value exceeded the estimated "
    "fair value. As part of this assessment, we determined that the carrying value of certain "
    "intangibles within the Parking Solutions segment were not recoverable and recorded a $40.4 "
    "million impairment to intangibles in our Parking Solutions segment during the six months "
    "ended June 30, 2026, which is presented in a separate line item on the consolidated "
    "statements of operations."
)
#: 8-K 0001628280-26-018235 EX-99.1 (Microvast, FY2025) — a CAUSE word beside a real charge
_MVST_FY25_CHARGE = (
    "Microvast Reports 2025 Financial Results • Gross margin decreased to 28.6%, compared to 31.5% "
    "in 2024, this change was primarily attributable to a $32.5 million inventory impairment "
    "charge related to specialized ESS components, which negatively impacted our gross margin by "
    "7.6 percentage points"
)

#: 8-K 0001352010-26-000043 EX-99.1 (EPAM, Q2 2026)
_EPAM_Q2_26 = (
    "EPAM Reports Results for Second Quarter 2026 • Second quarter revenues of $1.415 billion, up "
    "4.5% year-over-year • Second quarter GAAP income from operations increased to 10.8% of "
    "revenues from 9.3%, and non-GAAP income from operations increased to 16.4% of revenues from "
    "15.0%, on a year-over-year basis"
)
#: 8-K 0000793074-26-000129 EX-99.1 (Werner, Q2 2026)
_WERN_Q2_26 = (
    "Werner Enterprises Reports Second Quarter 2026 Results Second Quarter 2026 Highlights (all "
    "metrics compared to second quarter 2025 ) • Total revenues of $933.9 million, increased "
    "$180.8 million, or 24% • Operating income of $16.9 million, decreased $49.4 million, or 74%; "
    "non-GAAP adjusted operating income of $27.6 million, increased $11.0 million, or 67%"
)
#: 8-K 0001628280-26-055471 EX-99.1 (Microvast, Q2 2026)
_MVST_Q2_26 = (
    "Microvast Reports Second Quarter 2026 Financial Results Q2 2026 Results • Revenues of $87.3 "
    "million, compared to $91.3 million in Q2 2025, decreasing by $4.1 million, or 4.5%."
)
#: 8-K 0001902733-26-000064 EX-99.1 (nCino, Q1 fiscal 2027) — a total and a sub-line, both plural
_NCNO_Q1_27 = (
    "nCino Reports First Quarter Fiscal Year 2027 Financial Results • Total Revenues of $159.4M, "
    "up "
    "11% year-over-year • Subscription Revenues of $140.9M, up 12% year-over-year"
)
#: 8-K 0000745732-26-000038 EX-99.1 (Ross Stores, Q2 2026) — the closing company profile
_ROST_ABOUT = (
    "Ross Stores Reports Strong Second Quarter Sales and Earnings Results Raises Second Half and "
    "Fiscal 2026 Outlook We disclaim any obligation to update or revise these forward-looking "
    "statements. About Ross Stores, Inc. Ross Stores, Inc. is an S&P "
    "500, Fortune 500, and Nasdaq 100 (ROST) company headquartered in Dublin, California, with "
    "fiscal 2025 revenues of $22.8 billion."
)


def _parse(text: str) -> ReleaseExtract:
    return rp.parse_release(text, source_ref="t")


def _rows(text: str) -> set[tuple[str, str, float]]:
    return {(v.metric, v.period, v.value) for v in _parse(text).reconciliation}


# --- SPAN: a footnote digit, and a trailing-twelve-month lead-in (E2-D5) --------------------------
def test_a_footnote_digit_after_the_metric_name_does_not_drop_the_figure() -> None:
    """FuboTV and Target footnote the measure with a bare digit ("Adjusted EBITDA 1 of", "Adjusted
    EPS 1 was"); only "*", "†" and "‡" were tolerated, so each current figure was dropped."""
    assert ("adjusted ebitda", "Q2 2026", 37.7) in _rows(_FUBO_Q2_26)
    assert ("adjusted eps", "Q2 2026", 4.11) in _rows(_TGT_Q2_26)


def test_a_year_after_the_metric_name_is_not_a_footnote() -> None:
    """The digit is one digit, and only before the connector — a year is never swallowed as one."""
    assert rp._RECON.search("Adjusted EBITDA 2026 of $5.0 million") is None
    assert rp._RECON.search("Adjusted EBITDA 2 of $41.4 million") is not None


def test_a_figure_under_a_trailing_twelve_month_lead_in_takes_no_quarter() -> None:
    """The span lives in the parent bullet ("● Over the trailing twelve months: ○ …"), which the
    figure's own clause never sees. The quarter's list just above it keeps its quarter."""
    text = ("Q1 Fiscal 2026 Highlights ● Pro Forma Adjusted EBITDA 2 of $41.4 million, compared to "
            "$22.0 million ● Over the trailing twelve months: ○ Reported Revenue of $4.9 billion "
            "○ Pro Forma Adjusted EBITDA of $77.9 million")
    rows = _rows(text)
    assert ("adjusted ebitda", "Q1 2026", 41.4) in rows
    assert not any(v == 77.9 for _m, _p, v in rows)


def test_a_sub_bullet_whose_lead_in_names_no_span_keeps_its_heading_period() -> None:
    """NEGATIVE PIN — a nested list is not a span by being nested: only a lead-in that NAMES a
    trailing span unlabels its items."""
    text = ("Q1 Fiscal 2026 Highlights ● Profitability: ○ Pro Forma Adjusted EBITDA of $41.4 "
            "million")
    assert ("adjusted ebitda", "Q1 2026", 41.4) in _rows(text)


# --- SIGN: a loss stated in words (E2-D10) -------------------------------------------------------
def test_a_loss_stated_after_the_metric_name_is_read_as_negative() -> None:
    rows = _rows(_VITL_Q2_26)
    assert ("adjusted ebitda", "Q2 2026", -26.6) in rows
    assert ("adjusted net income", "Q2 2026", -20.0) in rows  # unchanged: the NAME says loss


def test_was_a_loss_of_is_negative_and_its_comparison_keeps_its_own_sign() -> None:
    rows = _rows(_VITL_Q2_26_PROSE)
    assert ("adjusted ebitda", "Q2 2026", -26.6) in rows
    assert ("adjusted ebitda", "Q2 2025", 29.9) in rows  # a positive prior stays positive


def test_a_positive_figure_is_not_signed_by_a_loss_word_elsewhere_in_its_sentence() -> None:
    """NEGATIVE PIN — the loss word signs only the figure it introduces."""
    rows = _rows("Acme Reports Second Quarter 2026 Results • Adjusted EBITDA of $12.0 million, "
                 "compared to a loss of $3.0 million")
    assert ("adjusted ebitda", "Q2 2026", 12.0) in rows


# --- ROLE: an amount the charge noun does not name (E2-D12) ---------------------------------------
def test_a_cash_flow_change_due_to_impairments_is_not_an_impairment() -> None:
    amounts = [o.amount for o in _parse(_VRRM_Q2_26).one_offs]
    assert 94.3 not in amounts
    assert amounts == [64.0, 40.4]


def test_a_charge_named_by_its_amount_survives_a_cause_word_before_it() -> None:
    """NEGATIVE PIN — "attributable to a $32.5 million inventory impairment charge": the cause
    precedes the amount, and the noun names the amount itself."""
    assert [o.amount for o in _parse(_MVST_FY25_CHARGE).one_offs] == [32.5]


# --- NAME: "Revenues of" (E2-D11) -----------------------------------------------------------------
def test_revenues_of_is_headline_revenue() -> None:
    assert ("revenue", "Q2 2026", 1415.0) in _rows(_EPAM_Q2_26)
    assert ("revenue", "Q2 2026", 933.9) in _rows(_WERN_Q2_26)
    assert ("revenue", "Q2 2026", 87.3) in _rows(_MVST_Q2_26)
    assert ("revenue", "Q1 2027", 159.4) in _rows(_NCNO_Q1_27)


def test_a_plural_sub_line_is_still_refused_loudly() -> None:
    """NEGATIVE PIN — the lead-word allowlist holds for the plural: "Subscription Revenues of" is
    one line of nCino's, never its total, and the refusal is stated."""
    ex = _parse(_NCNO_Q1_27)
    assert not any(v.value == 140.9 for v in ex.reconciliation)
    assert any("subscription" in f and "140.9M" in f for f in ex.qa_flags)


def test_revenue_in_the_closing_company_profile_is_not_a_reported_result() -> None:
    """NEGATIVE PIN — read as "revenues of", Ross Stores' profile became a full-year revenue row,
    rounded to $0.1bn, in five releases. It is refused, and the refusal says why."""
    ex = _parse(_ROST_ABOUT)
    assert not any(v.metric == "revenue" for v in ex.reconciliation)
    assert any("'About' company profile" in f for f in ex.qa_flags)


def test_a_headline_revenue_the_release_does_not_place_is_skipped_aloud() -> None:
    """EPAM's Q4 release lists "Fourth Quarter 2025 • Revenues of $1.408 billion" under a combined
    header and a sub-heading this reader does not take as one — no period, so no row; the skip is
    now a stated refusal rather than a page with no revenue and nothing said."""
    text = ("EPAM Reports Results for Fourth Quarter and Full Year 2025 Fourth Quarter 2025 • "
            "Revenues of $1.408 billion, up 12.8% year-over-year")
    ex = _parse(text)
    assert not any(v.metric == "revenue" for v in ex.reconciliation)
    assert any("revenue figure skipped" in f and "$1.408 billion" in f for f in ex.qa_flags)


def test_review_round_0_role_and_span_edges() -> None:
    """Review round 0, three edges of the guards above. A write-down's verb is the charge, not a
    change ("wrote down $12.0 million"); an "About Non-GAAP Financial Measures" heading is not the
    company profile; a comparison inside a trailing-twelve-month run takes no quarter either."""
    text = ("Acme Reports Second Quarter 2026 Results. In the quarter the Company wrote down $12.0 "
            "million of goodwill impairment charges.")
    assert [o.amount for o in _parse(text).one_offs] == [12.0]
    assert not rp._in_about_profile("About Non-GAAP Financial Measures We present revenues", 50)
    ttm = ("Q1 Fiscal 2026 Highlights ● Over the trailing twelve months: ○ Pro Forma Adjusted "
           "EBITDA of $77.9 million, compared to $50.0 million")
    assert not any(v in (77.9, 50.0) for _m, _p, v in _rows(ttm))
