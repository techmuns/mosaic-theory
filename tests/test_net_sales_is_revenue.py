"""A filer that guides "net sales" has guided its revenue line, and the cross-check must see it.

WHY (BRBR, found confirming five suspected guidance drops against their filings — four were not
drops at all, and this is what the fifth turned out to be).

`_guide_metric` folds "revenues" / "total revenues" into `revenue` and leaves **net sales** alone.
That is RIGHT for the page: BellRing guides net sales and its dossier should say net sales. The
defect was one metric-name away, in the consumer: `_release_revenue_guide` matched the string
`"revenue"` exactly, so a net-sales guide was invisible to it and the page reported

    guide verification (revenue): CIQ 2335.0–2375.0 vs release
    NO NUMERIC OUTLOOK → not cross-checked

while the release it cites says *"Updated fiscal year 2026 net sales outlook of $2.335-$2.375
billion"* — **2335–2375, the same numbers**, parsed correctly and sitting one synonym away from a
cross-source VERIFIED.

**A verification that silently declines to run is worse than one that fails.** "not cross-checked"
reads as *we looked and there was nothing to compare*, when the comparison was available and would
have PASSED. That is the failure mode this repo keeps closing in other places (the false UNKNOWN):
a gap invites a look, an absence closes the question.

THE FIXTURES ARE THE COMMITTED ARTIFACTS, so these hold what a human actually receives.
"""
from __future__ import annotations

import pathlib

import pytest

from vinci.dossier.mechanical import _release_revenue_guide
from vinci.dossier.schemas import Dossier
from vinci.edgar.primary_source import guide_verification

DOSSIERS = pathlib.Path(__file__).resolve().parents[1] / "data" / "dossiers"
#: SMPL's page as committed on 2026-08-18, frozen (tests/fixtures/frozen_pages/README.md). Its
#: 2026-07-09 release guides the year at $1.345–1.355bn beside a CIQ quarter — the shape the SMPL
#: pins below need, which the living page lost when the FY2026 10-K replaced the guide.
FROZEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "frozen_pages" / "2026-08-18"


def _releases(ticker: str, root: pathlib.Path = DOSSIERS) -> list:
    p = root / ticker / "dossier.json"
    if not p.is_file():
        pytest.skip(f"no committed dossier for {ticker}")
    return Dossier.model_validate_json(p.read_text()).mechanical.primary_source.releases


def test_brbrs_net_sales_guide_reaches_the_cross_check() -> None:
    """THE REGRESSION, on BRBR's committed releases. The guide was parsed all along — the consumer
    could not see it, so the page said there was no outlook."""
    lo, hi, qual, basis, period = _release_revenue_guide(_releases("BRBR"))
    assert (lo, hi) == (2335.0, 2375.0), "the net-sales guide is still invisible to the cross-check"
    assert not qual and basis == "level"
    assert period == "2026"


def test_brbr_now_verifies_instead_of_declining_to_look() -> None:
    """THE POINT OF FINDING IT. CIQ and the release state the SAME range, so the check does not
    merely run — it PASSES. The page was reporting no outlook on a name whose outlook agrees."""
    lo, hi, _q, _b, period = _release_revenue_guide(_releases("BRBR"))
    out = guide_verification("revenue", 2335.0, 2375.0, release_low=lo, release_high=hi,
                             ciq_period="FY 2026", release_period=period)
    assert "cross-source VERIFIED" in out
    assert "NO NUMERIC OUTLOOK" not in out


def test_smpls_net_sales_guide_is_seen_and_then_period_refused() -> None:
    """The two fixes compose. SMPL's release guides the YEAR ($1.345–1.355bn) and its CIQ guide is a
    QUARTER (322–332), so seeing the guide is what lets the period refusal fire at all — before
    this it read "NO NUMERIC OUTLOOK", which named neither the guide nor the mismatch."""
    lo, hi, _q, _b, period = _release_revenue_guide(_releases("SMPL", FROZEN))
    assert (lo, hi) == (1345.0, 1355.0), "SMPL's net-sales guide is still invisible"
    out = guide_verification("revenue", 322.0, 332.0, release_low=lo, release_high=hi,
                             ciq_period="FQ4 2026", release_period=period)
    assert "NOT CROSS-CHECKED" in out and "QUARTER" in out and "YEAR" in out
    assert "NO NUMERIC OUTLOOK" not in out


def test_the_synonym_set_is_the_cross_checks_vocabulary_not_the_pages() -> None:
    """THE DESIGN DECISION, pinned. The fix belongs to the consumer: normalising at parse time would
    rename the metric on the page and lose the filer's own term. If a future change moves "net
    sales" into `_guide_metric`, BRBR's page stops saying "net sales" and this pin should be the
    thing that argues about it.

    BOTH IMPORTS ARE LOCAL, on purpose: a module-level import of the symbol this fix ADDS makes the
    whole file fail to COLLECT against the pre-fix code, and an ImportError demonstrates nothing.
    The behavioural pins above must run — and fail — on the old consumer."""
    from vinci.dossier.mechanical import _REVENUE_LINE_METRICS
    from vinci.edgar.release_parse import _guide_metric

    assert _guide_metric("net sales") == "net sales", (
        "the PARSER must keep the filer's word — the page says what the filer said")
    assert "net sales" in _REVENUE_LINE_METRICS, "the CONSUMER must know it is the revenue line"
    assert "revenue" in _REVENUE_LINE_METRICS


def test_a_non_revenue_metric_is_not_swept_in() -> None:
    """The set must stay the revenue LINE. An adjusted-EBITDA or margin guide reaching the revenue
    cross-check would compare a $220M EBITDA range against a $1.3bn revenue guide — the shared-range
    confusion the parser already refuses one layer up."""
    from vinci.dossier.mechanical import _REVENUE_LINE_METRICS

    for metric in ("adjusted ebitda", "adjusted eps", "gross margin", "free cash flow"):
        assert metric not in _REVENUE_LINE_METRICS


def test_smpl_prefers_the_revenue_line_over_its_other_guides() -> None:
    """SMPL's releases carry BOTH net sales and adjusted EBITDA. The cross-check must pick the
    revenue line, not merely the first guide in the list."""
    lo, hi, *_ = _release_revenue_guide(_releases("SMPL", FROZEN))
    assert (lo, hi) == (1345.0, 1355.0), "an EBITDA guide was returned to the revenue cross-check"


def test_every_committed_page_cross_checks_a_revenue_line_guide_e2e() -> None:
    """THE INVARIANT on the living pages (TEST-LAYER RULE: a structure, never a value): whatever
    range the cross-check takes is one the page's newest guiding release states for a revenue-line
    metric — never an adjusted-EBITDA or margin range that happens to sit beside it."""
    from vinci.dossier.mechanical import _REVENUE_LINE_METRICS

    seen = 0
    for p in sorted(DOSSIERS.glob("*/dossier.json")):
        rels = Dossier.model_validate_json(p.read_text()).mechanical.primary_source.releases
        lo, hi, *_ = _release_revenue_guide(rels)
        if lo is None:
            continue
        seen += 1
        metrics = {g.metric for r in rels for g in r.guidance or []
                   if (g.low, g.high) == (lo, hi)}
        assert metrics & _REVENUE_LINE_METRICS, (
            f"{p.parent.name}: the cross-check took {lo}–{hi}, which no revenue-line guide states "
            f"(it matches {sorted(metrics)})")
    assert seen, "no committed page reached the cross-check — this pin checked nothing"
