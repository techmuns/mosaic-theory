"""(RC-1 A) Release-parser regression pins — committed REAL EDGAR EX-99.1 excerpts (public domain),
so the pins verify in CI WITHOUT network. The 99.1 locator (tolerant + multi-variant + negative) is
pinned on real filenames. A miss fails LOUD (qa_flags), never fabricating a value (the PR-2 lesson).
"""
from __future__ import annotations

from typing import Any

from vinci.edgar import release_parse as rp

_SRC = "8-K 0000000000-00-000000 Ex-99.1"


def _by(items: list[Any], **kw: Any) -> Any:
    return next((i for i in items if all(getattr(i, k) == v for k, v in kw.items())), None)


def test_ex991_locator_tolerant_multi_and_negative() -> None:
    r"""Tolerant 99.1 filename match — the three observed forms (ex991 / dex991 / the ex99_1
    underscore the old \W* class silently dropped); 99.2 / 99_2 NEVER match (the negative pin)."""
    for name in ("mvst2025q4ex991earningspre.htm", "d123116dex991.htm", "vrrm-ex99_1.htm",
                 "ex-99.1.htm", "dex99d1.txt"):
        assert rp._is_ex991(name), name
    for name in ("vrrm-ex99_2.htm", "d1dex992.htm", "ex99_2.htm", "ex-99.2.htm",
                 "primary-doc.htm", "ex991.pdf"):
        assert not rp._is_ex991(name), name


# --- REAL EDGAR excerpts (public domain), normalized (nbsp already folded) ------------------------

_MVST_FY25 = (
    "Exhibit 99.1 Microvast Reports 2025 Financial Results • Full Year revenue of $427.5 "
    "million, an increase of 12.6% compared to $379.8 million in 2024 • Gross margin decreased "
    "to 28.6%, compared to 31.5% in 2024, this change was primarily attributable to a $32.5 "
    "million inventory impairment charge related to specialized ESS components. • Non-GAAP "
    "adjusted EBITDA of positive $44.7 million, compared to Non-GAAP adjusted EBITDA of negative "
    "$44.8 million in 2024. • Capital expenditures of $38.7 million. 2026 Outlook & "
    "Forward-Looking Information • While we are navigating evolving tariff structures, we expect "
    "continued revenue growth in 2026 • We are targeting a strong gross margin position."
)


def test_release_parse_mvst_fy25() -> None:
    """FY2025 pins: adj EBITDA +44.7 (period 2025, NOT the 'compared to … 2024' clause), GAAP gross
    margin 28.6, the $32.5M ESS impairment, and a QUALITATIVE 2026 outlook (named, no number)."""
    ex = rp.parse_release(_MVST_FY25, source_ref=_SRC)
    ebitda = _by(ex.reconciliation, metric="adjusted ebitda")
    assert ebitda is not None and ebitda.value == 44.7 and ebitda.period == "2025"
    gm = _by(ex.reconciliation, metric="gross margin")
    assert gm is not None and gm.value == 28.6
    assert len(ex.one_offs) == 1
    assert ex.one_offs[0].amount == 32.5 and "ESS" in ex.one_offs[0].description
    rev = _by(ex.guidance, metric="revenue")
    assert rev is not None and rev.qualitative and rev.low is None and rev.period == "2026"


_MVST_Q1 = (
    "Exhibit 99.1 Microvast Reports First Quarter 2026 Financial Results • Net loss of $23.0 "
    "million, compared to net profit of $61.8 million in Q1 2025. Non-GAAP adjusted net loss was "
    "$14.6 million, compared to non-GAAP adjusted net profit of $19.3 million in Q1 2025. • "
    "Non-GAAP adjusted EBITDA of negative $5.5 million in Q1 2026, compared to non-GAAP adjusted "
    "EBITDA of $28.5 million in Q1 2025."
)


def test_release_parse_mvst_q1_26() -> None:
    """Q1-26 pins: adj EBITDA −5.5 and adj net loss −14.6 ('was $14.6 million', sign from 'loss');
    the 'compared to … Q1 2025' comparisons ($19.3M profit, $28.5M) are NOT taken as current."""
    ex = rp.parse_release(_MVST_Q1, source_ref=_SRC)
    ebitda = _by(ex.reconciliation, metric="adjusted ebitda")
    assert ebitda is not None and ebitda.value == -5.5 and ebitda.period == "Q1 2026"
    ni = _by(ex.reconciliation, metric="adjusted net income")
    assert ni is not None and ni.value == -14.6  # a NET LOSS ⇒ negative, from 'was $14.6 million'


_VRRM_AVIS = (
    "Exhibit 99.1 Verra Mobility Corporation Receives Termination of Agreement Notice From Avis "
    "Budget Group. The Company expects the termination to reduce Commercial Services’ 2026 "
    "annualized revenue by approximately $135 million to $145 million and 2026 annualized segment "
    "profit by approximately $120 million to $125 million, before taking into account expected "
    "cost reduction initiatives. The Company revised its financial outlook for 2026 to the "
    "following: • Total Revenue of $985 million to $995 million • Adjusted EBITDA of $380 million "
    "to $385 million • Adjusted EPS of $1.19 to $1.25 • Free Cash Flow of $140 million to $150 "
    "million."
)


def test_release_parse_vrrm_avis() -> None:
    """VRRM Avis pins: the event-impact quantifications (revenue reduce 135–145, segment profit
    reduce 120–125, 2026 annualized) AND the revised guide (revenue 985–995, adj EBITDA 380–385)."""
    ex = rp.parse_release(_VRRM_AVIS, source_ref=_SRC)
    rev_i = _by(ex.event_impacts, metric="revenue")
    assert rev_i is not None and rev_i.direction == "reduce"
    assert (rev_i.low, rev_i.high) == (135.0, 145.0)
    seg_i = _by(ex.event_impacts, metric="segment profit")
    assert seg_i is not None and (seg_i.low, seg_i.high) == (120.0, 125.0)
    rev_g = _by(ex.guidance, metric="revenue")
    assert rev_g is not None and not rev_g.qualitative and (rev_g.low, rev_g.high) == (985.0, 995.0)
    eb_g = _by(ex.guidance, metric="adjusted ebitda")
    assert eb_g is not None and (eb_g.low, eb_g.high) == (380.0, 385.0)


def test_release_parse_fail_loud_no_pattern() -> None:
    """A release with none of the anchored patterns fails LOUD: qa_flags name the misses and NO
    value is fabricated (the PR-2 lesson — a miss is UNKNOWN, never an analyst caveat)."""
    ex = rp.parse_release("The company issued a press release with no structured guidance today.",
                          source_ref=_SRC)
    assert ex.reconciliation == [] and ex.guidance == [] and ex.event_impacts == []
    assert ex.one_offs == [] and any("no anchored pattern matched" in f for f in ex.qa_flags)
