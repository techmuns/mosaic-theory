"""The CIQ scorecard reads wave 2's reasons (2026-10-27) — each status pinned on a synthetic page
AND, end to end, as an invariant of the committed pages (phrasing-independent: presence, pairing,
status — never a value the next assembly may re-draw).

BEFORE (`data/snapshots/data_quality/ciq/2026-10-27.json`, 27 pages at main 56500bb1):
`ebitda_vs_xbrl` 37 confirmed / 4 stated / 30 unexplained / 29 unchecked over 100 quarters;
`rent_vs_edgar_lease_cost` 21 / 0 / 2 / 1 over 24 pages; the scale check unscored.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

from vinci.dossier.ebitda_recon import unusual_explains
from vinci.dossier.schemas import EbitdaReconQuarter, LeaseBasis
from vinci.quality.core import CONFIRMED, DIFFERS_STATED, DIFFERS_UNEXPLAINED, UNCHECKED
from vinci.quality.sources import ciq

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _q(gap: float, **kw: Any) -> dict[str, Any]:
    return {"period_end": kw.pop("end", "2025-12-31"), "ciq_ebitda": 100.0 + gap,
            "filing_ebitda": 100.0, "gap": gap, "different": True, **kw}


def _ebitda(quarters: list[dict[str, Any]]) -> dict[str, int]:
    page = {"ticker": "X", "mechanical": {"financial_summary": {"ebitda_reconciliation": {
        "quarters": quarters}}}}
    return dict(ciq._ebitda_vs_xbrl(page).counts)


def test_each_wave2_reason_states_a_difference() -> None:
    assert _ebitda([_q(50.0, offset_by="2025-09-30")]) == {DIFFERS_STATED: 1}
    assert _ebitda([_q(50.0, ciq_unusual=49.5)]) == {DIFFERS_STATED: 1}
    assert _ebitda([_q(50.0, matching_amount="LossContingencyLossInPeriod 50,000,000 USD …",
                       matching_source="10-Q x XBRL")]) == {DIFFERS_STATED: 1}


def test_an_itemisation_off_the_gap_explains_nothing() -> None:
    """Negative pin: CIQ's unusual items 3% off the gap are not its reason."""
    assert not unusual_explains(50.0, 48.5)
    assert _ebitda([_q(50.0, ciq_unusual=48.5)]) == {DIFFERS_UNEXPLAINED: 1}


def _rent(**lb: Any) -> dict[str, int]:
    page = {"ticker": "X", "mechanical": {"valuation": {"lease_basis": lb}}}
    return dict(ciq._rent_vs_edgar_lease_cost(page).counts)


def test_a_rent_that_is_one_part_of_the_total_is_unchecked() -> None:
    """WLK's shape: 128 against 306 would read 'differs' — it is the short-term part."""
    assert _rent(rent_expense=128.0, edgar_lease_cost=306.0) == {DIFFERS_UNEXPLAINED: 1}
    assert _rent(rent_expense=128.0, edgar_lease_cost=306.0,
                 rent_component="ShortTermLeaseCost") == {UNCHECKED: 1}
    assert _rent(rent_expense=1146.0, edgar_lease_cost=1146.0) == {CONFIRMED: 1}


def _scale(anchor: Any) -> Any:
    return ciq._ciq_scale_vs_revenue({"ticker": "X", "anchor": anchor})


def test_the_scale_check_maps_each_outcome() -> None:
    assert _scale({"ciq_scale_check": "agree"}).counts == {CONFIRMED: 1}
    assert _scale({"ciq_scale_check": "differ"}).counts == {DIFFERS_UNEXPLAINED: 1}
    assert _scale({"ciq_scale_check": "not_run"}).counts == {UNCHECKED: 1}


def test_an_absent_scale_check_is_not_run_never_a_pass() -> None:
    assert _scale({}).not_run is not None and not _scale({}).counts
    assert _scale(None).not_run == "no anchor block on the page"


def test_the_new_keys_are_absent_never_null() -> None:
    """A block built before wave 2 round-trips byte-identically: no null keys appear."""
    q = EbitdaReconQuarter(period_end="2025-12-31", ciq_ebitda=1.0)
    assert "offset_by" not in q.model_dump_json() and "ciq_unusual" not in q.model_dump_json()
    lb = LeaseBasis(threshold=0.05, material=False, materiality="m", source_ref="s")
    assert "rent_component" not in lb.model_dump_json()
    assert "rent_component" in LeaseBasis(threshold=0.05, material=False, materiality="m",
                                          source_ref="s", rent_component="X").model_dump_json()


# --- end to end, on the committed pages (invariants only) ---------------------------------------


def _pages() -> dict[str, dict[str, Any]]:
    return {f.parent.name: json.loads(f.read_text())
            for f in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))}


def test_every_committed_offset_has_its_mirror() -> None:
    """An offset is a PAIR: each quarter naming another is named back by it, the gaps opposite."""
    for t, p in _pages().items():
        qs = {q["period_end"]: q for q in (((p.get("mechanical") or {}).get("financial_summary")
                                            or {}).get("ebitda_reconciliation") or {}).get(
            "quarters") or []}
        for end, q in qs.items():
            other = q.get("offset_by")
            if other is None:
                continue
            assert other in qs, (t, end)
            mirror = qs[other]
            assert mirror.get("offset_by") == end or mirror.get("matching_amount"), (t, end)
            assert q["gap"] * mirror["gap"] < 0, (t, end)


def test_every_committed_ebitda_block_is_four_quarters() -> None:
    """No committed block reads fiscal years as quarters (LLY's was removed, 2026-10-27)."""
    from datetime import date

    for t, p in _pages().items():
        er = ((p.get("mechanical") or {}).get("financial_summary") or {}).get(
            "ebitda_reconciliation")
        if not isinstance(er, dict):
            continue
        ends = sorted(date.fromisoformat(q["period_end"]) for q in er["quarters"])
        assert 240 <= (ends[-1] - ends[0]).days <= 300, t


def test_a_committed_rent_component_is_scored_unchecked() -> None:
    """Wherever a page names the part CIQ's rent is, the rent check does not count a difference."""
    for t, p in _pages().items():
        lb = ((p.get("mechanical") or {}).get("valuation") or {}).get("lease_basis")
        if isinstance(lb, dict) and lb.get("rent_component"):
            assert ciq._rent_vs_edgar_lease_cost(p).counts == {UNCHECKED: 1}, t
