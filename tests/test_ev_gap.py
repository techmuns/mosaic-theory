"""(A2a) THE EV GAP — pinned on SMPL's real recipe against real consensus.

WHY FOUR DECIMALS AND NOT THE ROUNDED TRIPLE. The operator's original target was `2.250`, struck
before the median ruling: it used consensus EBITDA **222.1**, the Market-Summary value. The median
sub-row — which A1 persists and the ruling requires — is **223.0**, and gives **2.2589**. So the
rounded triple cannot tell the two apart, and **anything landing at 2.250 means the code is reading
the mean rather than the median.** The four-decimal form is the discriminator.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.dossier.ev_gap import BasisMismatchError, EvGapInputs, anchor_year, decompose

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: SMPL's committed base leg + facts, and the stored TEV. NOT recomputed from spot x shares:
#: 931.5 / 88.46 = 10.53, the frozen underwrite spot, so recomputing mixes the record's spot with
#: its share count while the stored cap carries its own as-of and basis. 1256.07 vs 1234.0 — a
#: 1.8% difference the multiple ratio would inherit.
SMPL = EvGapInputs(
    revenue=1330.0, margin=0.14, margin_basis="operating",
    multiple=12.5, multiple_basis="EV/EBITDA", d_and_a=21.431,
    consensus_revenue=1351.7, consensus_ebitda=223.0,
    tev=1234.0, net_debt=324.582, shares=88.460545,
)


def test_smpl_decomposes_to_the_audits_own_finding() -> None:
    """THE ACCEPTANCE. If SMPL looks differentiated the feature is wrong — the audit's conclusion
    has to fall out of the arithmetic, not be argued alongside it."""
    g = decompose(SMPL)
    assert g["revenue_ratio"] == pytest.approx(0.9839, abs=5e-5)
    assert g["margin_ratio"] == pytest.approx(0.9463, abs=5e-5)
    assert g["multiple_ratio"] == pytest.approx(2.2589, abs=5e-5)
    assert g["ev_gap"] == pytest.approx(2.1032, abs=5e-5)
    # THE IDENTITY, written out: our_EV is the converted EBITDA at our multiple.
    assert g["our_ebitda"] == pytest.approx(207.631, abs=5e-4)
    assert g["our_ev"] == pytest.approx(207.631 * 12.5, abs=5e-3)
    assert g["ev_gap"] == pytest.approx((207.631 * 12.5) / 1234.0, abs=5e-5)
    # MULTIPLE-DOMINANT, and by a wide margin — the two operating ratios are within 6% of parity.
    assert g["multiple_ratio"] > 2 * max(g["revenue_ratio"], g["margin_ratio"])


def test_the_mean_for_median_substitution_is_caught() -> None:
    """222.1 is the Market-Summary value and 223.0 the Median sub-row. The rounded triple reads
    0.95/2.25 either way; the four-decimal form separates them."""
    mean_based = decompose(EvGapInputs(**{**SMPL.__dict__, "consensus_ebitda": 222.1}))
    assert mean_based["multiple_ratio"] == pytest.approx(2.2498, abs=5e-5)
    assert mean_based["multiple_ratio"] != pytest.approx(2.2589, abs=5e-5)


def test_an_operating_margin_without_d_and_a_refuses() -> None:
    """SMPL's recipe stores an OPERATING margin against an EV/EBITDA multiple. Without D&A the
    margin ratio would divide EBIT-margin by EBITDA-margin — a number that looks like a ratio."""
    with pytest.raises(BasisMismatchError, match="no D&A"):
        decompose(EvGapInputs(**{**SMPL.__dict__, "d_and_a": None}))
    with pytest.raises(BasisMismatchError, match="not EV/EBITDA"):
        decompose(EvGapInputs(**{**SMPL.__dict__, "multiple_basis": "EV/EBIT"}))


def test_the_product_identity_is_asserted_not_assumed() -> None:
    """The reconciliation is an identity, so a mismatch means an input moved between the two
    expressions. Pinned by breaking it: consensus revenue that does not multiply with the margin
    to give consensus EBITDA still satisfies each ratio individually."""
    g = decompose(SMPL)
    assert g["revenue_ratio"] * g["margin_ratio"] * g["multiple_ratio"] == pytest.approx(
        g["ev_gap"], rel=1e-12)


def test_the_anchor_is_the_nearest_year_where_both_metrics_resolve() -> None:
    """EPAM CARRIES REVENUE 5fy AGAINST EBITDA 3fy. Revenue's furthest year would leave the margin
    ratio uncomputable, so the anchor is the intersection — and NEAREST within it, because the
    closest forward year is the one the market is pricing."""
    epam = json.loads((ROOT / "data" / "dossiers" / "EPAM" / "dossier.json").read_text())
    levels = epam["mechanical"]["consensus_context"]["consensus_levels"]
    rev = {str(c["fy"]) for c in levels["Revenue"]}
    ebitda = {str(c["fy"]) for c in levels["EBITDA"]}
    assert len(rev) > len(ebitda), "EPAM is the case because its spans differ; they no longer do"
    got = anchor_year(levels)
    assert got is not None and got in rev and got in ebitda
    assert got == min(rev & ebitda, key=int)

    smpl = json.loads((ROOT / "data" / "dossiers" / "SMPL" / "dossier.json").read_text())
    assert anchor_year(smpl["mechanical"]["consensus_context"]["consensus_levels"]) == "2026"

    assert anchor_year({"Revenue": [{"fy": "2026"}]}) is None, "one metric is not an anchor"
