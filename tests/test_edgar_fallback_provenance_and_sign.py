"""Phase 2 C2 — the EDGAR fallback says where each figure was filed (audit E1-D5), and refuses a
capex or D&A leg filed negative (E1-D12).

D5. The screen's fundamental snapshot and the CIQ-empty fallback (`edgar_fundamentals`) served
figures with no accession, and a figure a later filing restated was served silently: WOR's FY2022
revenue reads 1,309 (filed 2024-07-30) where it was first filed as 5,242, and nothing said so.

D12. Capex and D&A were taken as filed. WOR's capex negated moves its FCF from 170.2 to 282.0 while
`fcf_sign` stays PRESENT; a negative D&A — 8 of 1,241 current EBITDA pairs in the cache, 7 of them
under `DepreciationAmortizationAndAccretionNet`, which nets accretion income — lowers EBITDA.
A payment and an expense are filed positive, so a negative leg is refused, naming it, never
sign-flipped.

Every fixture is WOR's committed companyfacts subset; the negative legs are its real current legs
with the sign flipped."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vinci.dossier.edgar_fundamentals import EdgarFundamentals
from vinci.dossier.schemas import SourceStatus
from vinci.edgar.client import compute_fundamental_snapshot
from vinci.edgar.concepts import current_annual, current_pair
from vinci.schemas.envelope import CoverageStatus

_ROOT = Path(__file__).resolve().parent.parent
WOR = json.loads((_ROOT / "tests" / "fixtures" / "companyfacts" / "WOR.json").read_text())
ACC = "0001193125-26-325872"  # WOR's FY2026 10-K, filed 2026-07-30


def _negated(tag: str, end: str = "2026-05-31") -> dict[str, Any]:
    facts: dict[str, Any] = json.loads(json.dumps(WOR))
    for rows in facts["facts"]["us-gaap"][tag]["units"].values():
        for r in rows:
            if r["end"] == end:
                r["val"] = -r["val"]
    return facts


# ─── D5: every served figure says where it was filed ─────────────────────────────────────────

def test_the_snapshot_names_each_legs_filing() -> None:
    s = compute_fundamental_snapshot("0000108516", WOR)
    for field in (s.op_income_sign, s.fcf_sign, s.ebitda_annual, s.eps_diluted_annual,
                  s.net_leverage, s.net_debt_to_ocf, s.net_debt):
        assert field.coverage_status is CoverageStatus.PRESENT
        assert field.note and ACC in field.note, field.note
    assert "PaymentsToAcquirePropertyPlantAndEquipment" in (s.fcf_sign.note or "")


def test_the_fallback_fcf_names_its_filing() -> None:
    fcf = EdgarFundamentals(WOR).free_cash_flow()
    assert fcf.status is SourceStatus.PRESENT and fcf.value == 170.2
    assert ACC in (fcf.source_ref or "")


def test_a_restated_year_says_what_it_restates() -> None:
    """WOR's FY2022 revenue: 1,309 as filed 2024-07-30 after the steel spin-off, 5,242 as first
    filed 2022-08-01. The trajectory prints 1,309 and now says it restates 5,242."""
    traj = EdgarFundamentals(WOR).multi_year_trajectory().value or ""
    assert "FY2022 1,309" in traj
    restated = traj[traj.index("[restated"):]
    assert "FY2022 revenue 1,309 restates 5,242" in restated and "2022-08-01" in restated


def test_a_year_never_restated_carries_no_restatement_note() -> None:
    """The negative pin: WOR's FY2026 revenue was filed once."""
    traj = EdgarFundamentals(WOR).multi_year_trajectory().value or ""
    assert "FY2026 revenue" not in traj[traj.index("[restated"):]


# ─── D12: a capex or D&A filed negative is refused, naming it ────────────────────────────────

def test_negative_capex_is_refused_in_the_snapshot() -> None:
    """Negated, WOR's capex made FCF 282.0 and `fcf_sign` stayed PRESENT."""
    s = compute_fundamental_snapshot("0000108516", _negated(
        "PaymentsToAcquirePropertyPlantAndEquipment"))
    assert s.fcf_sign.coverage_status is CoverageStatus.UNKNOWN
    assert "PaymentsToAcquirePropertyPlantAndEquipment" in (s.fcf_sign.note or "")
    assert "negative" in (s.fcf_sign.note or "") and ACC in (s.fcf_sign.note or "")


def test_negative_capex_is_refused_in_the_fallback() -> None:
    fb = EdgarFundamentals(_negated("PaymentsToAcquirePropertyPlantAndEquipment"))
    fcf = fb.free_cash_flow()
    assert fcf.status is SourceStatus.UNKNOWN and "negative" in (fcf.note or "")
    traj = fb.multi_year_trajectory().value or ""
    assert "FY2026 170" not in traj.split("FCF:")[1].split(";")[0]
    assert "withheld" in traj and "FY2026 FCF" in traj


def test_negative_dep_amort_is_refused_and_leverage_says_why() -> None:
    legs, _ = current_pair(WOR, "operating_income", "dep_amort")
    assert legs is not None
    tag = legs[1].tag  # the D&A leg the snapshot serves
    s = compute_fundamental_snapshot("0000108516", _negated(tag))
    assert s.ebitda_annual.coverage_status is CoverageStatus.UNKNOWN
    assert tag in (s.ebitda_annual.note or "") and "negative" in (s.ebitda_annual.note or "")
    assert s.net_leverage.coverage_status is CoverageStatus.UNKNOWN
    assert "negative" in (s.net_leverage.note or "")


def test_positive_legs_are_read_as_before() -> None:
    """The negative pin: WOR's real legs are untouched — FCF 170.2, a PRESENT sign and EBITDA."""
    s = compute_fundamental_snapshot("0000108516", WOR)
    assert s.fcf_sign.value == 1 and s.ebitda_annual.value == 133_481_000.0


def test_the_snapshot_names_what_a_restated_leg_restates() -> None:
    """Review round 1: the snapshot hands `facts` to `filed_at`, so a current leg a later filing
    restated names the figure first filed. WOR's FY2026 operating income, with an earlier filing of
    the same year stating another figure (its real row, copied earlier at 90%)."""
    op, _ = current_annual(WOR, "operating_income")
    assert op is not None
    facts: dict[str, Any] = json.loads(json.dumps(WOR))
    for rows in facts["facts"]["us-gaap"][op.tag]["units"].values():
        real = next(r for r in rows if r.get("accn") == op.accession
                    and r["end"] == op.period_end.isoformat() and r.get("start"))
        rows.append({**real, "val": round(real["val"] * 0.9), "filed": "2026-07-01",
                     "accn": "0001193125-26-000001"})
    note = compute_fundamental_snapshot("0000108516", facts).op_income_sign.note or ""
    assert "restating" in note and "0001193125-26-000001" in note and "2026-07-01" in note
    plain = compute_fundamental_snapshot("0000108516", WOR).op_income_sign.note or ""
    assert "restating" not in plain  # the negative pin: filed once, nothing restated
