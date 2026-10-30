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
        # in the SOURCE, never the note: the web renders any note on a present fact as a caveat
        assert field.note is None and ACC in field.source, (field.note, field.source)
    assert "PaymentsToAcquirePropertyPlantAndEquipment" in s.fcf_sign.source


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
    src = compute_fundamental_snapshot("0000108516", facts).op_income_sign.source
    assert "restating" in src and "0001193125-26-000001" in src and "2026-07-01" in src
    plain = compute_fundamental_snapshot("0000108516", WOR).op_income_sign.source
    assert "restating" not in plain  # the negative pin: filed once, nothing restated


# ─── review round 2 (coordinator) ─────────────────────────────────────────────────────────────

def _brief_warnings(doc: dict[str, Any]) -> int:
    """The production web renderer (`dossier.js` renderDossier) over a dossier: how many ⚠ it
    prints."""
    import shutil
    import subprocess

    import pytest
    if not shutil.which("node"):
        pytest.skip("node not available")
    dj = (_ROOT / "frontend" / "views" / "shared" / "dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const doc = JSON.parse(readFileSync(0, "utf8"));
console.log(JSON.stringify({{ warnings: renderDossier(doc, null).split("\u26a0").length - 1 }}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver], input=json.dumps(doc),
                         capture_output=True, text=True, check=True, cwd=_ROOT)
    return int(json.loads(out.stdout)["warnings"])


def test_a_clean_present_edgar_fact_renders_no_caveat_on_the_web_brief() -> None:
    """BLOCKER (coordinator review, round 2). The snapshot put each figure's provenance in the
    NOTE; `mechanical._sourced` carries the note onto the page and the web renders any note on a
    present fact as "⚠ …". AMZN's committed page, its quality FCF sign and leverage rebuilt from
    AMZN's real companyfacts through the production path, rendered by `dossier.js`: no ⚠ added."""
    from vinci.dossier.mechanical import _sourced
    page = json.loads((_ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    facts = json.loads((_ROOT / "tests" / "fixtures" / "companyfacts" / "AMZN.json").read_text())
    snap = compute_fundamental_snapshot("0001018724", facts)
    assert snap.fcf_sign.coverage_status is CoverageStatus.PRESENT
    before = _brief_warnings(page)
    q = page["mechanical"]["quality"]
    q["fcf_sign"] = json.loads(_sourced(
        snap.fcf_sign, source_ref="EDGAR XBRL FCF sign (screen data-record)").model_dump_json())
    assert _brief_warnings(page) == before
    assert "NetCashProvidedByUsedInOperatingActivities" in (q["fcf_sign"]["source_ref"] or "")


def test_the_margin_trend_names_a_restated_figure_too() -> None:
    """E1-D5 was half done: the margin trend prints WOR's absolute FY2022 revenue (1,309) and
    EBITDA silently; only the trajectory named the restatement."""
    mt = EdgarFundamentals(WOR).margin_trend().value or ""
    assert "[restated" in mt and "FY2022 revenue 1,309 restates 5,242" in mt


def _retagged_da(tag: str) -> dict[str, Any]:
    """WOR with its served D&A rows filed under ``tag`` instead (every other D&A tag removed)."""
    legs, _ = current_pair(WOR, "operating_income", "dep_amort")
    assert legs is not None
    facts: dict[str, Any] = json.loads(json.dumps(WOR))
    gaap = facts["facts"]["us-gaap"]
    rows = gaap[legs[1].tag]
    for t in ("DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
              "DepreciationAndAmortization", "Depreciation", "AmortizationOfIntangibleAssets"):
        gaap.pop(t, None)
    gaap[tag] = rows
    return facts


def test_an_accretion_net_tag_is_never_read_as_d_and_a() -> None:
    """The refusal selected on SIGN: a negative `DepreciationAmortizationAndAccretionNet` was
    refused for netting accretion income while 28 positive ones were read as D&A unflagged. The
    tag is a different concept, so it is never read as D&A — positive or negative."""
    s = compute_fundamental_snapshot("0000108516",
                                     _retagged_da("DepreciationAmortizationAndAccretionNet"))
    assert s.ebitda_annual.coverage_status is CoverageStatus.UNKNOWN
    assert "accretion" in (s.ebitda_annual.note or "")
    fb = EdgarFundamentals(_retagged_da("DepreciationAmortizationAndAccretionNet"))
    assert "accretion" in (fb.margin_trend().note or fb.margin_trend().value or "")
    # the negative pin: the same values under a D&A tag read as D&A
    ok = compute_fundamental_snapshot("0000108516", _retagged_da("DepreciationAndAmortization"))
    assert ok.ebitda_annual.coverage_status is CoverageStatus.PRESENT


def test_a_rounding_re_report_is_not_a_restatement() -> None:
    """Nit 8: a later filing stating the same figure at a coarser precision (−69,100,000 for
    −69,075,000) read as "restating". Compared at the coarser of the two precisions it is the same
    figure; a real restatement still reads."""
    from vinci.edgar.concepts import superseded
    op, _ = current_annual(WOR, "operating_income")
    assert op is not None
    def earlier(val: float) -> dict[str, Any]:
        facts: dict[str, Any] = json.loads(json.dumps(WOR))
        for rows in facts["facts"]["us-gaap"][op.tag]["units"].values():
            real = next(r for r in rows if r.get("accn") == op.accession
                        and r["end"] == op.period_end.isoformat() and r.get("start"))
            rows.append({**real, "val": val, "filed": "2026-07-01", "accn": "0001193125-26-000001"})
        return facts
    finer = op.value + 25_000 if op.value % 100_000 == 0 else round(op.value, -5) + 25_000
    coarse_served = op.model_copy(update={"value": float(round(op.value, -5))})
    assert superseded(earlier(finer), coarse_served) is None
    assert superseded(earlier(op.value * 0.9), op) is not None


def test_net_debt_and_a_split_substitute_say_whether_they_were_checked() -> None:
    """Nit 9: the restatement check skipped net debt's cash line (no facts passed) and, silently, a
    D&A leg the filer splits into two tags (no such tag to look up)."""
    from vinci.edgar.concepts import filed_at
    facts: dict[str, Any] = json.loads(json.dumps(WOR))
    cash_tag = "CashAndCashEquivalentsAtCarryingValue"
    s0 = compute_fundamental_snapshot("0000108516", WOR)
    cash_end = s0.net_debt.source.split(" at ")[1][:10]
    for rows in facts["facts"]["us-gaap"][cash_tag]["units"].values():
        real = next(r for r in rows if r["end"] == cash_end)
        rows.append({**real, "val": round(real["val"] * 0.8), "filed": "2026-07-01",
                     "accn": "0001193125-26-000001"})
    assert "restating" in compute_fundamental_snapshot("0000108516", facts).net_debt.source
    op, _ = current_annual(WOR, "operating_income")
    assert op is not None
    split = op.model_copy(update={"tag": "Depreciation + AmortizationOfIntangibleAssets"})
    assert "not checked" in filed_at(split, WOR)
