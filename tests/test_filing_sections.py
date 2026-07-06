"""(RC-1 B) Filing-section parser regression pins — committed REAL MVST Q1-26 10-Q excerpts (public
domain, CI-verifiable, no network). A miss fails LOUD (qa_flags) and NEVER fabricates: the
'no customer exceeded 10%' healthy-roster phrasing must NOT read as a 'Customer EXCEEDED 10%'.
"""
from __future__ import annotations

from vinci.edgar import filing_sections as fs

_SRC = "10-Q 0000000000-00-000000"

_MVST_10Q = (
    "The Company will not have sufficient liquidity through the next twelve months. These "
    "conditions and events raise substantial doubt about the Company's ability to continue as a "
    "going concern. The Company's primary plans to alleviate the substantial doubt include "
    "1) obtaining sufficient funding through operations and financing. As of March 31, 2026, the "
    "Company had outstanding borrowings of $138.8 million, with $111.2 million due within the next "
    "12 months, a bond payable of $41.7 million that matures in January 2027, a convertible loan "
    "with repayment amount of $26.7 million that matures in May 2026, and other current "
    "liabilities of $214.8 million. Revenue concentration for the three months ended March 31, "
    "2026 and 2025: Customer A 52 % 31 % Customer B 18 % 16 %. Additionally, as of March 31, 2026, "
    "the Company had $29.1 million in purchase commitments primarily related to inventory, and "
    "$17.3 million in "
    "capital commitments with $15.0 million due within the next 12 months."
)


def test_filing_sections_mvst_q1_26() -> None:
    """MVST Q1-26 pins: substantial-doubt (verbatim + plans); the filing-basis wall (111.2 ≤12m,
    bond 41.7/Jan-2027 + convertible 26.7/May-2026); Customer A 52/31 · B 18/16; commitments."""
    ex = fs.parse_filing_sections(_MVST_10Q, source_ref=_SRC)
    gc = ex.going_concern
    assert gc is not None and gc.substantial_doubt
    assert "substantial doubt" in gc.verbatim and "going concern" in gc.verbatim
    assert "alleviate" in gc.plans
    w = ex.maturity_wall
    assert w is not None and w.within_12m_total == 111.2 and w.state == "located"  # C3
    tr = {t.name: (t.amount, t.maturity) for t in w.tranches}
    assert tr["bond payable"] == (41.7, "January 2027")
    assert tr["convertible loan"] == (26.7, "May 2026")
    conc = ex.concentration
    assert conc is not None
    cust = {c.name: (c.pct, c.prior_pct, c.value_kind) for c in conc.customers}
    assert cust["Customer A"] == (52.0, 31.0, "exact")  # C2: a stated % is exact
    assert cust["Customer B"] == (18.0, 16.0, "exact")
    commits = {c.kind: (c.amount, c.within_12m) for c in ex.commitments}
    assert commits["purchase"] == (29.1, None)
    assert commits["capital"] == (17.3, 15.0)
    assert ex.qa_flags == []


def test_concentration_rejects_no_customer_exceeded_phrasing() -> None:
    """A healthy roster ('no single customer exceeded 10% of revenue') must NOT fabricate a
    concentration — the customer LABEL is a short id (A/B/1), never a word like 'exceeded'. It
    fails loud UNKNOWN (concentration None + a qa_flag), never a guessed 'Customer EXCEEDED 10%'."""
    text = ("During the period, no single Government Solutions customer exceeded 10 % of total "
            "revenue. The City of New York and other municipalities were significant.")
    ex = fs.parse_filing_sections(text, source_ref=_SRC)
    assert ex.concentration is None
    assert any("customer concentration" in f for f in ex.qa_flags)


_VRRM_CONC = (
    "Revenue from a single Government Solutions customer exceeded 10 % of total revenue. The City "
    "of New York Department of Transportation (NYCDOT) represented 15.2 % and 15.4 % of total "
    "revenue for the three months ended March 31, 2026 and 2025. No other Government Solutions "
    "customer exceeded 10 % of total accounts receivable, net as of March 31, 2026."
)


def test_concentration_prose_exact_prefers_stated_value() -> None:
    """(C2) VRRM discloses the EXACT figure (NYCDOT 15.2%/15.4%), not just the '>10%' floor lead-in:
    extract the stated value (never understate to '>10%'); the 'No other … exceeded 10%' negative is
    NOT taken as a concentration."""
    ex = fs.parse_filing_sections(_VRRM_CONC, source_ref=_SRC)
    assert ex.concentration is not None and len(ex.concentration.customers) == 1
    c = ex.concentration.customers[0]
    assert c.name.startswith("City of New York") and c.value_kind == "exact"
    assert (c.pct, c.prior_pct) == (15.2, 15.4)


def test_concentration_prose_floor_when_no_stated_value() -> None:
    """(C2) A disclosure that gives ONLY 'a single customer exceeded 10%' (no stated %) → value_kind
    'floor' (a disclosed floor), so the render shows '> 10% (disclosed floor)', not a bare 10%."""
    ex = fs.parse_filing_sections(
        "Revenue from a single OEM customer exceeded 10 % of total revenue during the period.",
        source_ref=_SRC)
    assert ex.concentration is not None
    c = ex.concentration.customers[0]
    assert c.value_kind == "floor" and c.pct == 10.0


def test_maturity_wall_two_state_located_vs_not_stated() -> None:
    """(C3) A ≤12m-wall statement ⇒ state='located'; a debt section present with NO near-term wall
    (a long-dated composition table — VRRM-class) ⇒ state='not_stated' (a KNOWN, value-free note),
    NEVER an unknown and NEVER a thousands-units number. No debt section at all ⇒ None (UNKNOWN)."""
    located = fs.parse_filing_sections(
        "Borrowings of $138.8 million, with $111.2 million due within the next 12 months.",
        source_ref=_SRC).maturity_wall
    assert located is not None and located.state == "located" and located.within_12m_total == 111.2
    not_stated = fs.parse_filing_sections(
        "Long-term debt consisted of: Term Loan $685,360 Senior Notes 350,000 Amended Revolver "
        "26,000 Other debt 2,869.", source_ref=_SRC).maturity_wall
    assert not_stated is not None and not_stated.state == "not_stated"
    assert not_stated.within_12m_total is None and "see CIQ panel" in not_stated.note
    absent = fs.parse_filing_sections("An unremarkable quarter.", source_ref=_SRC)
    assert absent.maturity_wall is None  # no debt section ⇒ true UNKNOWN + a qa_flag
    assert any("maturity wall" in f for f in absent.qa_flags)


def test_filing_sections_fail_loud_no_pattern() -> None:
    """A filing with none of the anchored sections fails LOUD (qa_flags name the misses) and
    fabricates nothing — a miss is UNKNOWN, never an analyst caveat (the PR-2 lesson)."""
    ex = fs.parse_filing_sections("An unremarkable quarter with routine operating results.",
                                  source_ref=_SRC)
    assert ex.going_concern is None and ex.maturity_wall is None and ex.concentration is None
    assert ex.commitments == []
    assert any("maturity wall" in f for f in ex.qa_flags)
