"""Stock-based compensation — the ratio, and the two window/basis traps it was built around.

CORPUS FIRST. Every number quoted here was measured on live EDGAR companyfacts for the 14
committed names before the pin was written.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from vinci.dossier.mechanical import _sbc_line
from vinci.dossier.schemas import SourceStatus

REF = dt.date(2026, 8, 14)


def _facts(sbc: list[dict[str, Any]], rev: list[dict[str, Any]],
           rev_tag: str = "RevenueFromContractWithCustomerExcludingAssessedTax") -> dict[str, Any]:
    """companyfacts SHAPE, built to the real API's structure — the layer under test parses this
    exact nesting, so a flatter stub would test the stub."""
    return {"facts": {"us-gaap": {
        "ShareBasedCompensation": {"units": {"USD": sbc}},
        rev_tag: {"units": {"USD": rev}}}}}


def _fact(val: float, start: str, end: str, form: str = "10-K", **kw: Any) -> dict[str, Any]:
    return {"val": val, "start": start, "end": end, "form": form, **kw}


def test_a_quarterly_revenue_fact_with_an_annual_period_is_never_the_denominator() -> None:
    """THE FUBO TRAP, VERBATIM FROM THE LIVE CORPUS. FUBO carries TWO revenue facts for
    2024-01-01→2024-12-31: $1,622.8M from the 10-K (`fp=FY`) and $402.3M from a 10-Q
    (`fp=Q1`, `frame=CY2024`) whose period STRING looks annual.

    The numerator was restricted to 10-K annuals from the first cut; the denominator was not, so
    matching on period alone picked the quarterly figure and printed FUBO at **10.6% against a
    true 2.6%**. Same window is necessary, NOT sufficient — same BASIS is the other half.

    MUTATION: drop `x.get("form") == "10-K"` from the revenue filter and this reddens."""
    out = _sbc_line(_facts(
        [_fact(42.5e6, "2024-01-01", "2024-12-31", fp="FY")],
        [_fact(402.3e6, "2024-01-01", "2024-12-31", form="10-Q", fp="Q1", frame="CY2024"),
         _fact(1622.8e6, "2024-01-01", "2024-12-31", fp="FY")]), REF)
    assert out is not None
    assert out.pct_revenue.status is SourceStatus.PRESENT
    assert abs(out.pct_revenue.value - 2.6) < 0.05, (
        f"the quarterly fact became the denominator: {out.pct_revenue.value:.1f}% "
        f"— {out.line.value}")


def test_revenue_from_a_different_period_never_forms_the_ratio() -> None:
    """THE ORIGINAL DEFECT. The first measurement divided each name's LATEST 10-K SBC by the
    dossier's LTM revenue; FUBO's FY2024 numerator over a post-merger LTM denominator read 0.7%.
    Both inputs were individually correct, which is why it was believed. No revenue fact covering
    the SBC window ⇒ UNKNOWN, and the dollars still print."""
    out = _sbc_line(_facts(
        [_fact(42.5e6, "2024-01-01", "2024-12-31")],
        [_fact(5712.0e6, "2025-01-01", "2025-12-31")]), REF)
    assert out is not None
    assert out.pct_revenue.status is SourceStatus.UNKNOWN
    assert out.expense.status is SourceStatus.PRESENT, "the dollars must survive a missing ratio"
    assert "UNKNOWN" in out.line.value


def test_restatements_that_disagree_refuse_rather_than_pick() -> None:
    """Two 10-K facts for one period with different values is ambiguity, not a tie to break.
    Choosing silently publishes a ratio whose denominator the reader cannot reconstruct."""
    out = _sbc_line(_facts(
        [_fact(50.0e6, "2025-01-01", "2025-12-31")],
        [_fact(1000.0e6, "2025-01-01", "2025-12-31"),
         _fact(1200.0e6, "2025-01-01", "2025-12-31")]), REF)
    assert out is not None
    assert out.pct_revenue.status is SourceStatus.UNKNOWN, out.line.value


def test_an_sbc_fact_after_the_as_of_never_wins() -> None:
    """The same post-as-of leak class item 9 measured: a 10-K published after the record's as-of
    belongs to a later record."""
    out = _sbc_line(_facts(
        [_fact(10.0e6, "2024-01-01", "2024-12-31"),
         _fact(99.0e6, "2026-09-01", "2027-08-31")],
        [_fact(1000.0e6, "2024-01-01", "2024-12-31")]), REF)
    assert out is not None
    assert out.window_end == "2024-12-31", f"a post-as-of year won: {out.window_end}"


def test_the_line_states_the_period_the_ratio_is_a_ratio_of() -> None:
    """A ratio without its window is unfalsifiable on the page — nothing would have shown which
    periods FUBO's 0.7% divided."""
    out = _sbc_line(_facts(
        [_fact(42.5e6, "2024-01-01", "2024-12-31")],
        [_fact(1622.8e6, "2024-01-01", "2024-12-31")]), REF)
    assert out is not None
    assert "2024-01-01" in out.line.value and "2024-12-31" in out.line.value, out.line.value


def test_the_block_reaches_the_rendered_page_not_just_the_helper() -> None:
    """PIN THE ARTIFACT, NOT THE HELPER — the lesson from #470, where deleting a call site
    reddened nothing while the block vanished from every PDF. Drives the real `render_markdown`
    over a real committed dossier and asserts the phrasing-independent label."""
    import json
    import pathlib

    import pytest

    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    root = pathlib.Path(__file__).resolve().parents[1]
    committed = sorted((root / "data" / "dossiers").glob("*/dossier.json"))
    if not committed:
        pytest.skip("no committed dossiers in this checkout")
    doc = json.loads(committed[0].read_text())
    doc["mechanical"]["sbc"] = {
        "expense": {"value": 24.4, "source_ref": "EDGAR XBRL", "status": "present", "note": None},
        "pct_revenue": {"value": 5.5, "source_ref": "EDGAR XBRL", "status": "present",
                        "note": None},
        "window_start": "2025-01-01", "window_end": "2025-12-31",
        "line": {"value": "stock-based compensation $24.4M = 5.5% of revenue",
                 "source_ref": "EDGAR XBRL", "status": "present", "note": None}}
    md = render_markdown(Dossier.model_validate(doc))
    assert "Stock-based compensation" in md, "the block is absent from the rendered page"


def test_a_fourth_quarter_fact_sharing_the_year_end_is_not_the_denominator() -> None:
    """THE SAME TRAP THROUGH THE OTHER DATE, found by mutation. Relaxing the period match to
    `end`-only survived every other pin here, because the different-period case differs on BOTH
    dates. A Q4 fact shares an annual fact's END (2025-12-31) and differs only in its START, so
    an end-only match divides a full year's SBC by one quarter's revenue and quadruples the
    ratio — the FUBO defect wearing a different date.

    MUTATION: drop the `start` half of the comparison and this reddens."""
    out = _sbc_line(_facts(
        [_fact(100.0e6, "2025-01-01", "2025-12-31")],
        [_fact(250.0e6, "2025-10-01", "2025-12-31"),      # Q4 only — shares the year END
         _fact(1000.0e6, "2025-01-01", "2025-12-31")]), REF)
    assert out is not None
    assert abs(out.pct_revenue.value - 10.0) < 0.05, (
        f"a Q4 denominator was accepted: {out.pct_revenue.value:.1f}% — {out.line.value}")
