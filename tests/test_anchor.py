"""Tests for the persisted R1 anchor (vinci.dossier.anchor).

Pins the schema, the EBITDA-basis value math (the anchor recomputes from its OWN stored inputs and
uses EV = (EBIT + D&A) × multiple, not EBIT — the same guard as the WERN scenario pin), the
positivity guard (non-positive margin → R2_NEEDED), and the byte-preserving backfill insert.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from vinci.dossier import midcycle as mc
from vinci.dossier.anchor import (
    RECIPE_R1,
    RECIPE_R2,
    Anchor,
    AnchorInput,
    AnchorMargin,
    AnchorMultiple,
    _latest_dep_amort,
    compute_anchor,
    insert_anchor_block,
)
from vinci.dossier.schemas import Dossier

_ROOT = Path(__file__).resolve().parents[1]


def _now() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)


# --- schema pin --------------------------------------------------------------------------------
def test_anchor_schema_shape_and_dossier_field() -> None:
    """The anchor block's shape is pinned (the pydantic model IS the dossier's schema — there is no
    separate committed json-schema file), and the Dossier carries it as an OPTIONAL field so pre-
    anchor JSON round-trips."""
    assert set(Anchor.model_fields) == {
        "recipe_hint", "applicable", "multiple_basis", "computed_at", "reason",
        "margin", "multiple", "d_and_a", "net_debt", "diluted_shares", "ltm_revenue",
        "anchor_base_value_per_share", "anchor_ev_ebit", "overall_confidence", "note",
    }
    assert set(AnchorMargin.model_fields) == {"value", "unit", "basis", "source", "anchor_years",
                                              "confidence"}
    assert set(AnchorMultiple.model_fields) == {"value", "unit", "source", "history_quarters",
                                                "confidence"}
    assert set(AnchorInput.model_fields) == {"value", "unit", "basis", "source"}
    # optional on the Dossier, default None (byte-identical round-trip of pre-anchor JSON)
    assert Dossier.model_fields["anchor"].default is None
    a = Anchor(recipe_hint=RECIPE_R1, applicable=True, computed_at=_now(),
               multiple=AnchorMultiple(value=10.0, history_quarters=30, confidence="firm"))
    assert a.multiple_basis == "EV/EBITDA"  # stamped, can never be misread as EV/EBIT
    assert a.multiple is not None and a.multiple.source == "valuation.own_history.median"
    # the anchor round-trips through JSON (validate(dump) is stable)
    assert Anchor.model_validate_json(a.model_dump_json()) == a


# --- numeric regression: EBITDA basis, not EBIT (the WERN-pin guard) ---------------------------
def test_anchor_base_uses_ebitda_basis_not_ebit_frozen() -> None:
    """FROZEN IT-shape inputs → a pinned base, recomputed via the #150 block's value math. Dropping
    D&A (an EBIT basis) MATERIALLY lowers the base — proof the anchor prices off EBITDA, never EBIT
    (an EBITDA multiple silently applied to EBIT understates a name by ~(1 + D&A/EBIT)×)."""
    rev, margin, mult, dna, nd, sh = 6474.137, 0.141347, 22.7124315, 200.309, 1688.229, 69_965_000.0

    def base(d_and_a: float) -> float:
        sv = mc.scenario_value(
            mc.Scenario(name="base", revenue=rev, margin=margin, multiple=mult,
                        source="anchor default", d_and_a=d_and_a),
            net_debt=nd, shares=sh)
        return sv.equity * 1e6 / sh

    assert round(base(dna), 2) == 337.96                    # EBITDA basis (matches the backfill)
    assert base(0.0) < base(dna) - 50                       # dropping ~$200M D&A × 22.7x is ~$65/sh


def test_backfilled_anchor_base_consistent_with_stored_inputs() -> None:
    """END-TO-END on the committed artifact: the stored ``anchor_base_value_per_share`` recomputes
    EXACTLY from the anchor's OWN stored inputs (margin/multiple/D&A/net-debt/shares/LTM-rev) via
    the block's EBITDA-basis math — value-INDEPENDENT (holds whatever the numbers are, so it
    survives an EDGAR data refresh), and it re-proves the D&A (EBITDA) inclusion."""
    d = json.loads((_ROOT / "data" / "dossiers" / "IT" / "dossier.json").read_text())
    a = d.get("anchor")
    assert a and a["recipe_hint"] == RECIPE_R1 and a["applicable"]
    sv = mc.scenario_value(
        mc.Scenario(name="base", revenue=a["ltm_revenue"]["value"], margin=a["margin"]["value"],
                    multiple=a["multiple"]["value"], source="anchor default",
                    d_and_a=a["d_and_a"]["value"]),
        net_debt=a["net_debt"]["value"], shares=a["diluted_shares"]["value"])
    recomputed = sv.equity * 1e6 / a["diluted_shares"]["value"]
    assert recomputed == pytest.approx(a["anchor_base_value_per_share"], abs=0.01)
    # EBITDA basis: the stored EV/EBIT exceeds the multiple (EV/EBITDA) because EBIT < EBITDA
    assert a["anchor_ev_ebit"] > a["multiple"]["value"]


# --- positivity guard --------------------------------------------------------------------------
def test_positivity_guard_sets_r2_when_margin_nonpositive(monkeypatch: pytest.MonkeyPatch) -> None:
    """A name with no positive normalizable operating margin → recipe_hint R2_NEEDED, applicable
    False, and nothing else stored (the guard for future pre-profit names; it does NOT try to catch
    turnarounds — that is the analyst's override)."""
    monkeypatch.setattr(mc, "margin_anchor", lambda _r, _o: mc.MarginAnchor(
        by_year={2019: -0.10, 2020: -0.05}, revenue_tag="Revenues",
        opinc_tag="OperatingIncomeLoss"))
    mechanical = {"valuation": {"own_history": {"value": [
        {"metric": "EV/EBITDA (TEV/LTM)", "median": 10.0, "n_closes": 30}]}}}
    a = compute_anchor(mechanical, facts={"facts": {}}, computed_at=_now())
    assert a.recipe_hint == RECIPE_R2 and a.applicable is False
    assert "revenue-anchored" in (a.reason or "")
    assert a.anchor_base_value_per_share is None and a.margin is None  # "store nothing else"


def test_missing_own_history_multiple_is_inapplicable_not_crash() -> None:
    """No committed own-history multiple → applicable False with a reason (must not crash)."""
    a = compute_anchor({"valuation": {}}, facts={"facts": {}}, computed_at=_now())
    assert a.applicable is False and "own-history multiple missing" in (a.reason or "")


# --- D&A split-sum period alignment ------------------------------------------------------------
def _da_facts(dep_end: str, am_end: str) -> dict[str, object]:
    """Minimal companyfacts carrying only the SPLIT D&A tags (no combined tag), at the given
    period ends — the CNXC shape, which forces the split fallback."""
    def series(end: str, val: float) -> dict[str, object]:
        start = f"{int(end[:4]) - 1}{end[4:]}"  # ~12-month span → is_annual
        return {"units": {"USD": [{"start": start, "end": end, "val": val, "filed": "2026-02-01",
                                   "fy": int(end[:4]), "fp": "FY", "form": "10-K", "accn": "x"}]}}
    return {"facts": {"us-gaap": {"Depreciation": series(dep_end, 226e6),
                                  "AmortizationOfIntangibleAssets": series(am_end, 434e6)}}}


def test_dep_amort_split_requires_the_same_fiscal_period() -> None:
    """The D&A split-sum is period-ALIGNED or nothing: adding an FY2025 depreciation to an FY2024
    amortisation would fabricate a D&A that never existed (the same discipline edgar_fundamentals
    applies to its own EBITDA add-back). Misaligned → UNKNOWN, flagged, never blended."""
    aligned = _latest_dep_amort(_da_facts("2025-11-30", "2025-11-30"))   # positive pin
    assert aligned is not None
    value, source = aligned
    assert value == pytest.approx(660e6) and "split, FY2025" in source
    assert _latest_dep_amort(_da_facts("2025-11-30", "2024-11-30")) is None  # negative pin


# --- byte-preserving backfill insert -----------------------------------------------------------
def test_insert_anchor_block_is_byte_preserving() -> None:
    """The backfill insert appends ONLY the anchor field; every other byte is preserved (the sole
    edit to existing content is the trailing comma on the previously-last field)."""
    text = '{\n  "ticker": "X",\n  "midcycle": null\n}'
    a = Anchor(recipe_hint=RECIPE_R1, applicable=True, computed_at=_now())
    out = insert_anchor_block(text, a)
    parsed = json.loads(out)  # valid JSON
    assert parsed["ticker"] == "X" and parsed["midcycle"] is None       # untouched
    assert parsed["anchor"]["recipe_hint"] == RECIPE_R1                  # added
    assert out.startswith('{\n  "ticker": "X",\n  "midcycle": null,\n  "anchor": {')
    with pytest.raises(ValueError, match="not a JSON object"):
        insert_anchor_block("not json", a)
