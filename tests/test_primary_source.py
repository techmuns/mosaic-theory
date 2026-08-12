"""(RC-1 C) Pins for the cross-source derivations (offline, no network) — the checkpoint-adjudicated
acceptance gates: self-funding two-input read, same-window wall coherence (Option A, tranche-match,
exclusive boundary + safety valve), EBITDA-basis triangulation (basis-labeled), guide verification.
"""
from __future__ import annotations

from datetime import date

import pytest

from vinci.dossier import mechanical as mech
from vinci.dossier import schemas as ds
from vinci.edgar import primary_source as ps
from vinci.edgar import release_parse as rp

# committed REAL-TEXT fixtures (public-domain EDGAR excerpts) — the assembly helpers derive offline.
_FY25 = (
    "Microvast Reports 2025 Financial Results • Full Year revenue of $427.5 million, up 12.6% "
    "compared to $379.8 million in 2024 • Gross margin decreased to 28.6%, compared to 31.5% in "
    "2024, from a $32.5 million inventory impairment charge related to ESS components. • Non-GAAP "
    "adjusted EBITDA of positive $44.7 million, compared to Non-GAAP adjusted EBITDA of negative "
    "$44.8 million in 2024. 2026 Outlook • we expect continued revenue growth in 2026."
)
_Q1_26 = (
    "Microvast Reports First Quarter 2026 Financial Results • Non-GAAP adjusted EBITDA of negative "
    "$5.5 million in Q1 2026, compared to non-GAAP adjusted EBITDA of $28.5 million in Q1 2025."
)


def test_ltm_adj_ebitda_production_path() -> None:
    """The 18.7x LTM input computed END-TO-END from the parsed releases (not fed): LTM adjusted
    EBITDA = FY 44.7 − prior-Q 28.5 + current-Q (−5.5) = 10.7 — the parser now captures the
    prior-year comparison distinctly, so the whole chain is deterministic from real text."""
    releases = [rp.parse_release(_FY25, source_ref="fy"), rp.parse_release(_Q1_26, source_ref="q1")]
    assert mech._ltm_adj_ebitda(releases) == 10.7
    # the FY margin inputs also come straight off the parse (no re-derivation)
    fy = mech._fy_reconciliation(releases)
    assert fy["gross margin"] == 28.6 and fy["revenue"] == 427.5
    assert mech._fy_impairment(releases) == 32.5
    # a missing leg is fail-loud, never a partial guess
    assert mech._ltm_adj_ebitda([rp.parse_release(_Q1_26, source_ref="q1")]) is None


def _adj_ebitda_release(rows: list[tuple[str, float]]) -> ds.ReleaseExtract:
    return ds.ReleaseExtract(source_ref="t", reconciliation=[
        ds.ReconciliationValue(metric="adjusted ebitda", period=p, value=v, verbatim="v",
                               source_ref="t")
        for p, v in rows])


def test_ltm_adj_ebitda_refuses_misperiodized_fy() -> None:
    """SMPL regression (committed 2026-07-23 artifact): a prior-year QUARTER row stamped with the
    bare year '2025' (66.2) composed LTM = 66.2 − 73.9 + 57.0 = $49.3M — a quarter-scale 'LTM'
    that printed a bogus ~6.6x net-debt/EBITDA in basis_triangulation beside a real ~$220M LTM.
    A FULL-YEAR below one of its own quarters is a mis-periodized row — refused (None → 'LTM
    unavailable'), never a quarter-scale LTM. A plausible FY (≥ its quarters) still composes."""
    poisoned = _adj_ebitda_release([("2025", 66.2), ("Q3 2025", 73.9), ("Q3 2026", 57.0)])
    assert mech._ltm_adj_ebitda([poisoned]) is None
    sane = _adj_ebitda_release([("2025", 261.9), ("Q3 2025", 73.9), ("Q3 2026", 57.0)])
    assert mech._ltm_adj_ebitda([sane]) == 245.0


def test_release_revenue_guide_prefers_most_recent() -> None:
    """The guide-verify cross-source input = the most-recent release's revenue guide; a qualitative
    outlook (MVST FY25) yields (None, None, True), a numeric revised guide yields the range.

    THE FOURTH ELEMENT IS THE BASIS (2026-08-05). A release can guide revenue as a CHANGE, and
    handing (low, high) onward without saying which kind they are is how -2..+2 reaches a
    comparison against a 1,345..1,355 level guide.

    THE FIFTH IS THE PERIOD (2026-08-12), for the same reason: a release guiding a YEAR against a
    CIQ guide covering a QUARTER cannot agree as bare numbers (NFLX printed MISMATCH on a pair that
    corroborated). A QUALITATIVE outlook still names the period it is an outlook FOR — the period
    survives the absent numbers, so the scope check works on the qualitative path too."""
    assert mech._release_revenue_guide(
        [rp.parse_release(_FY25, source_ref="fy")]) == (None, None, True, "level", "2026")

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
    """MVST: CIQ FY26 revenue guide 427.516 ≈ prior-FY actual 427.516 AND the release outlook is
    QUALITATIVE → VENDOR-ECHO. VRRM: CIQ 985–995 vs release 985–995 → cross-source VERIFIED."""
    mvst = ps.guide_verification("revenue", 427.516, 427.516,
                                 prior_fy_actual=427.516, release_qualitative=True)
    assert "VENDOR-ECHO" in mvst and "427.516" in mvst and "QUALITATIVE" in mvst
    vrrm = ps.guide_verification("revenue", 985.0, 995.0, release_low=985.0, release_high=995.0)
    assert "cross-source VERIFIED" in vrrm and "985" in vrrm and "995" in vrrm


def test_guide_verification_echo_requires_conjunct_release_verified_suppresses() -> None:
    """GATE 2 (adjudicated): VENDOR-ECHO needs BOTH conjuncts. A NUMERIC release guide equal to the
    prior-FY actual is RELEASE-VERIFIED, not a stale echo — the corroboration SUPPRESSES the flag;
    tolerance-alone must NOT fire. When the release outlook is ABSENT (no number, not qualitative)
    the echo still fires, tailed 'uncorroborated'."""
    # tolerance MATCHES (100 ≈ prior 100) but the release NUMERICALLY confirms 100 → VERIFIED
    suppressed = ps.guide_verification("revenue", 100.0, 100.0, prior_fy_actual=100.0,
                                       release_low=100.0, release_high=100.0)
    assert "VENDOR-ECHO" not in suppressed and "cross-source VERIFIED" in suppressed
    # release outlook ABSENT (no number, not qualitative) + echo → still flags, uncorroborated
    absent = ps.guide_verification("revenue", 50.0, 50.0, prior_fy_actual=50.0)
    assert "VENDOR-ECHO" in absent and "uncorroborated" in absent


def test_guide_verification_no_release_guide_is_not_a_mismatch() -> None:
    """(review M1) A release that states NO numeric guide (release_low None, NOT qualitative, NOT a
    vendor-echo) reads 'not cross-checked' — NOT a false MISMATCH, and never puts the None low/high
    into the string (was a fabricated 'release None–None → MISMATCH flag')."""
    r = ps.guide_verification("revenue", 2325.0, 2365.0, release_low=None, release_high=None)
    assert "not cross-checked" in r and "MISMATCH" not in r and "None" not in r
    # a prior-FY actual far from the CIQ guide is NOT an echo → still falls here, not to MISMATCH
    r2 = ps.guide_verification("revenue", 2325.0, 2365.0, prior_fy_actual=1900.0, release_low=None)
    assert "not cross-checked" in r2 and "None" not in r2


@pytest.mark.network
def test_primary_source_assembly_mvst_live() -> None:
    """(live) End-to-end assembly on MVST over real EDGAR filings + the CIQ bundle — the four
    derivations, production-path. Needs the git-ignored CIQ folder + EDGAR; skips when absent."""
    import json
    from pathlib import Path
    from types import SimpleNamespace

    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.dossier.schemas import MechanicalLayer
    from vinci.edgar.client import EdgarClient
    from vinci.sec import build_sec_http

    folder, doss = Path("data/manual/ciq"), Path("data/dossiers/MVST/dossier.json")
    if not (folder / "MVST").exists() or not doss.exists():
        pytest.skip("MVST CIQ folder / committed dossier absent (git-ignored)")
    d = json.loads(doss.read_text())
    layer = MechanicalLayer.model_validate(d["mechanical"])
    bundle = CiqBundle.from_files("MVST", LocalFolderStore(folder).files("MVST"))
    http = build_sec_http()
    rec = SimpleNamespace(identity=SimpleNamespace(cik=str(d["cik"]), ticker="MVST"))
    primary, _lat = mech._primary_source(
        rec, EdgarClient(http), http, bundle, date.fromisoformat(d["reference_date"]), layer)  # type: ignore[arg-type]
    assert "MIXED" in primary.self_funding.value  # latest-Q OCF < 0
    assert "AGREES" in primary.wall_coherence.value and "109.6" in primary.wall_coherence.value
    assert "~18.7x" in primary.basis_triangulation.value  # LTM 10.7 computed end-to-end
    assert "VENDOR-ECHO" in primary.guide_verification.value
