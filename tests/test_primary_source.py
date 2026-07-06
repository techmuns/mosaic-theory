"""(RC-1 C) Pins for the cross-source derivations (offline, no network) — the checkpoint-adjudicated
acceptance gates: self-funding two-input read, same-window wall coherence (Option A, tranche-match,
exclusive boundary + safety valve), EBITDA-basis triangulation (basis-labeled), guide verification.
"""
from __future__ import annotations

from datetime import date

from vinci.edgar import primary_source as ps

_MVST_PANEL = [
    ps.PanelInstrument("Convertible Bond", 41.7, date(2027, 1, 31)),
    ps.PanelInstrument("Conv Loan Delaware", 13.0, date(2026, 5, 28)),
    ps.PanelInstrument("Conv Loan Init", 12.0, date(2026, 5, 28)),
    ps.PanelInstrument("Loan Facilities", 42.9, date(2026, 12, 10)),
    ps.PanelInstrument("Long-term Loan", 13.9, date(2027, 6, 19)),
    ps.PanelInstrument("Short-term Bank Facility", 49.5, date(2027, 3, 31)),  # at +12m → excluded
]


def test_self_funding_two_input_read() -> None:
    """MVST = MIXED (latest-Q OCF < 0), superseding the committed 'self-funding'; both-positive =
    YES; a missing leg = UNKNOWN. A single positive leg never reads self-funding."""
    assert "MIXED" in ps.self_funding(False, True) and "self-fund" in ps.self_funding(False, True)
    assert ps.self_funding(True, True).startswith("self-funding: YES")
    assert "UNKNOWN" in ps.self_funding(None, True)


def test_wall_coherence_option_a_agrees_tranche_matched() -> None:
    """Option A pin: panel same-window $109.6M (principal: 41.7+42.9+25.0, exclusive boundary) vs
    filing $111.2M (repayment) → 1.4% < tol → AGREES, 'filing cross-validates panel'; BOTH basis
    labels; the $49.5M facility at +12m is excluded; convertible delta +$1.7M accrued PIK."""
    line, qa = ps.wall_coherence(
        111.2, _MVST_PANEL, balance=date(2026, 3, 31),
        filing_convertible=26.7, panel_convertible_principal=25.0)
    assert "109.6" in line and "111.2" in line
    assert "AGREES" in line and "cross-validates" in line
    assert "principal basis" in line and "repayment basis" in line
    assert "EXCLUSIVE" in line  # the 49.5 boundary facility excluded both sides
    assert "25.0" in line and "26.7" in line and "+$1.7M accrued PIK" in line
    assert qa == []  # agreement → no artifact flag


def test_wall_coherence_divergence_fires_with_boundary_safety_valve() -> None:
    """A genuine divergence ≥ tolerance fires the DIVERGES line; and when an instrument matures
    within ±7d of the +12m boundary, the QA flag names a possible window-convention artifact (no
    false-fire on convention for future names)."""
    line, qa = ps.wall_coherence(60.0, _MVST_PANEL, balance=date(2026, 3, 31))
    assert "DIVERGES" in line
    assert qa and "window-convention artifact" in qa[0] and "Short-term Bank Facility" in qa[0]


def test_basis_triangulation_labels_are_part_of_each_pin() -> None:
    """3.9x (CIQ, GAAP) · 5.8x (comps, GAAP) · net debt / company-adj LTM EBITDA ($10.7M) ~18.7x ·
    covenant UNKNOWN (not disclosed). Margins: GAAP 28.6% · impairment-excluded 36% (CIQ) with the
    labeled 28.6 + 32.5/427.5 cross-check. Labels are load-bearing."""
    t = ps.basis_triangulation(
        "3.9x", "5.8x", 199.9, 10.7,
        gaap_gross_margin=28.6, impairment=32.5, revenue=427.5, ciq_adjusted_margin=36.0)
    assert "net debt / EBITDA (CIQ, GAAP basis)" in t and "3.9x" in t
    assert "total debt / EBITDA (CIQ comps, GAAP basis)" in t and "5.8x" in t
    assert "company-adjusted LTM EBITDA ($10.7M)" in t and "~18.7x" in t
    assert "covenant basis" in t and "UNKNOWN (not disclosed)" in t
    assert "GAAP 28.6%" in t and "impairment-excluded 36.0%" in t
    assert "28.6 + 32.5/427.5 = 36.2%" in t


def test_guide_verification_vendor_echo_and_cross_source_verified() -> None:
    """MVST: CIQ FY26 revenue guide 427.516 == prior-FY actual 427.516 (3dp) → VENDOR-ECHO + the
    release QUALITATIVE-only line. VRRM: CIQ 985–995 vs release 985–995 → cross-source VERIFIED."""
    mvst = ps.guide_verification("revenue", 427.516, 427.516,
                                 prior_fy_actual=427.516, release_qualitative=True)
    assert "VENDOR-ECHO" in mvst and "427.516" in mvst and "QUALITATIVE" in mvst
    vrrm = ps.guide_verification("revenue", 985.0, 995.0, release_low=985.0, release_high=995.0)
    assert "cross-source VERIFIED" in vrrm and "985" in vrrm and "995" in vrrm
