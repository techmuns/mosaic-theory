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

from vinci.dossier import anchor as anc
from vinci.dossier import midcycle as mc
from vinci.dossier.anchor import (
    ANCHOR_FIRM_MIN_YEARS,
    RECIPE_R1,
    RECIPE_R2,
    Anchor,
    AnchorInput,
    AnchorMargin,
    AnchorMultiple,
    _latest_dep_amort,
    compute_anchor,
    insert_anchor_block,
    replace_anchor_block,
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
        "data_quality", "data_quality_detail",
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
def test_positivity_guard_sets_r2_when_margin_nonpositive() -> None:
    """A name with no positive normalizable operating margin → recipe_hint R2_NEEDED, applicable
    False, and nothing else stored (the guard for future pre-profit names; it does NOT try to catch
    turnarounds — that is the analyst's override). Uses a REAL total-revenue tag so the guard is
    reached (an absent revenue tag is the separate UNRESOLVED path)."""
    facts = _facts(**{
        _TOTAL: dict.fromkeys(range(2018, 2026), 100e6),
        "OperatingIncomeLoss": dict.fromkeys(range(2018, 2026), -8e6),  # persistently loss-making
    })
    a = compute_anchor(_MECH_OK, facts=facts, computed_at=_now())
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


# --- revenue-denominator tag selection (the AORT defect) ---------------------------------------
def _facts(**tags: dict[int, float]) -> dict[str, object]:
    """companyfacts carrying the given us-gaap tags → {fiscal_year: value}, as ~12-month annuals."""
    node: dict[str, object] = {}
    for tag, by_year in tags.items():
        node[tag] = {"units": {"USD": [
            {"start": f"{y - 1}-12-31", "end": f"{y}-12-31", "val": v, "filed": f"{y + 1}-02-01",
             "fy": y, "fp": "FY", "form": "10-K", "accn": "x"} for y, v in by_year.items()]}}
    return {"facts": {"us-gaap": node}}


def _band(**kw: object) -> dict[str, object]:
    """An own-history EV/EBITDA band. Defaults describe a FIRM band: >=5y span, quarterly cadence,
    no data-quality flag — the multiple leg is firm on the WINDOW, not the raw close count."""
    return {"metric": "EV/EBITDA (TEV/LTM)", "median": 10.0, "n_closes": 40,
            "window_span_years": 9.0, "periodicity": "quarterly", "data_quality": None, **kw}


def _mech(**kw: object) -> dict[str, object]:
    return {"valuation": {"own_history": {"value": [_band(**kw)]}}}


_MECH_OK = _mech()   # a firm own-history band
_TOTAL = "RevenueFromContractWithCustomerExcludingAssessedTax"   # the ASC-606 total-revenue tag


def test_revenue_tag_preference_picks_total_not_longest() -> None:
    """The denominator is chosen by MEANING (total revenue), never by longest series — the defect
    that let AORT's partial `Revenues` (13y) beat the 606 total (10y). Fewer VALID years wins."""
    facts = _facts(**{
        "Revenues": dict.fromkeys(range(2011, 2022), 40e6),   # 11y PARTIAL (the longer series)
        _TOTAL: dict.fromkeys(range(2016, 2026), 180e6),      # 10y TOTAL (the correct one)
    })
    s, conflicts = anc._total_revenue_series(facts)
    assert s is not None
    assert s.tag == "RevenueFromContractWithCustomerExcludingAssessedTax"   # total, not longest
    assert s.n_years == 10 and conflicts                                     # and it is recorded


def test_revenue_tag_conflict_guard_fires_and_total_tag_wins() -> None:
    """A partial-vs-total disagreement is never silently resolved: the guard flags it, records the
    tags and the gap, and the TOTAL tag supplies the denominator (margin 10%, not a partial 40%)."""
    facts = _facts(**{
        "Revenues": dict.fromkeys(range(2016, 2022), 40e6),   # partial
        _TOTAL: dict.fromkeys(range(2016, 2026), 160e6),
        "OperatingIncomeLoss": dict.fromkeys(range(2016, 2026), 16e6),
    })
    a = compute_anchor(_MECH_OK, facts=facts, computed_at=_now())
    assert a.data_quality == anc.DQ_REVENUE_TAG_CONFLICT
    assert a.data_quality_detail and any("Revenues" in d and "apart" in d
                                         for d in a.data_quality_detail)
    assert a.margin is not None
    assert a.margin.value == pytest.approx(0.10, abs=1e-9)   # 16/160 total — NOT 16/40 partial


def test_data_quality_flag_caps_confidence_at_weak() -> None:
    """Confidence has a VALIDITY component: 10 clean years (≥7) and 40 closes (≥20) would read
    'firm' on counts alone — a fired flag caps the margin leg, and the overall, at weak. AORT read
    'firm' on fabricated years; that must not recur."""
    facts = _facts(**{
        "Revenues": dict.fromkeys(range(2016, 2022), 40e6),
        _TOTAL: dict.fromkeys(range(2016, 2026), 160e6),
        "OperatingIncomeLoss": dict.fromkeys(range(2016, 2026), 16e6),
    })
    a = compute_anchor(_MECH_OK, facts=facts, computed_at=_now())
    assert a.margin is not None and a.margin.anchor_years >= ANCHOR_FIRM_MIN_YEARS
    assert a.multiple is not None and a.multiple.confidence == "firm"   # the count leg IS firm
    assert a.margin.confidence == "weak" and a.overall_confidence == "weak"
    assert "CAPPED weak" in a.margin.source


def test_revenue_tag_preference_covers_every_known_revenue_alias() -> None:
    """DRIFT GUARD: every revenue alias the shared resolver knows must be RANKED here. An alias
    added to CONCEPT_ALIASES but not to _REVENUE_TAG_PREFERENCE would be silently INVISIBLE — never
    a candidate (so never chosen even when it is the true total) and never conflict-checked — i.e.
    exactly the failure this module exists to prevent, re-entering through another door."""
    from vinci.edgar.concepts import CONCEPT_ALIASES
    unranked = set(CONCEPT_ALIASES["revenue"]) - set(anc._REVENUE_TAG_PREFERENCE)
    assert not unranked, f"revenue alias(es) not ranked in _REVENUE_TAG_PREFERENCE: {unranked}"


def test_uncomputable_margin_is_unresolved_not_r2() -> None:
    """A margin we could not COMPUTE (no fiscal year where both series report) is a DIFFERENT fact
    from one computed and found non-positive — never lumped into R2_NEEDED, which would tell the
    analyst 'use the revenue-anchored recipe' when the truth is 'there is no margin data'."""
    facts = _facts(**{
        _TOTAL: dict.fromkeys(range(2018, 2022), 100e6),
        "OperatingIncomeLoss": dict.fromkeys(range(2010, 2014), 5e6),   # NO overlapping FY
    })
    a = compute_anchor(_MECH_OK, facts=facts, computed_at=_now())
    assert a.recipe_hint == anc.RECIPE_UNRESOLVED and a.applicable is False
    assert "not computable" in (a.reason or "")
    assert a.margin is None and a.anchor_base_value_per_share is None


def test_no_total_revenue_tag_flips_applicability_to_unresolved() -> None:
    """Only partial/absent revenue tags → ANCHOR_UNRESOLVED, applicable False. The anchor refuses to
    emit a margin off a partial denominator rather than publishing a fabricated one."""
    facts = _facts(OperatingIncomeLoss=dict.fromkeys(range(2016, 2026), 5000000.0))
    a = compute_anchor(_MECH_OK, facts=facts, computed_at=_now())
    assert a.recipe_hint == anc.RECIPE_UNRESOLVED and a.applicable is False
    assert "total-revenue tag" in (a.reason or "")
    assert a.margin is None and a.anchor_base_value_per_share is None


def test_anchor_changed_ignores_only_the_timestamp() -> None:
    """A re-validation that moves nothing must not rewrite the artifact (computed_at alone is not a
    change); any material move must."""
    a1 = Anchor(recipe_hint=RECIPE_R1, applicable=True, computed_at=_now())
    same = a1.model_copy(update={"computed_at": datetime(2027, 5, 5, tzinfo=UTC)})
    moved = a1.model_copy(update={"anchor_base_value_per_share": 9.99})
    assert anc.anchor_changed(a1, same) is False
    assert anc.anchor_changed(a1, moved) is True


# --- periodicity + window-span (the 2026-07-21 staleness fix) ----------------------------------
def test_periodicity_classifies_quarterly_and_annual_spacing() -> None:
    """The shared loader stamps close cadence: ~91-day gaps → quarterly (no flag); ~365-day gaps on
    the quarterly Multiples tab → annual + a fail-loud periodicity_mismatch (a mislabel)."""
    from datetime import date, timedelta

    from vinci.dossier.ciq_sheets import PERIODICITY_MISMATCH, _own_history_band
    q = [(date(2020, 1, 1) + timedelta(days=91 * i), 10.0 + i) for i in range(12)]
    b = _own_history_band("EV/EBITDA (TEV/LTM)", q, source_file="q.xls")
    assert b is not None and b.periodicity == "quarterly" and b.data_quality is None
    assert 88 <= (b.periodicity_days_median or 0) <= 94 and b.source_file == "q.xls"
    ann = [(date(2005, 1, 1) + timedelta(days=365 * i), 10.0 + i) for i in range(12)]
    ba = _own_history_band("EV/EBITDA (TEV/LTM)", ann)
    assert ba is not None and ba.periodicity == "annual"
    assert ba.data_quality == PERIODICITY_MISMATCH   # annual spacing on a quarterly tab → fail loud


def test_multiple_leg_confidence_is_span_based_not_point_count() -> None:
    """The multiple leg is firm on the WINDOW it spans + quarterly cadence, NEVER the raw close
    count. A band with 40 closes but only 4y span (or annual periodicity, or a mismatch flag, or NO
    span metadata) is weak — the exact failure the window-staleness incident exposed."""
    facts = _facts(**{
        _TOTAL: dict.fromkeys(range(2016, 2026), 100e6),
        "OperatingIncomeLoss": dict.fromkeys(range(2016, 2026), 20e6),
    })
    firm = compute_anchor(_mech(window_span_years=9.0, periodicity="quarterly"),
                          facts=facts, computed_at=_now())
    assert firm.multiple is not None and firm.multiple.confidence == "firm"
    short = compute_anchor(_mech(window_span_years=4.0, periodicity="quarterly"),
                           facts=facts, computed_at=_now())
    assert short.multiple is not None and short.multiple.confidence == "weak"   # < 5y span
    ann = compute_anchor(
        _mech(window_span_years=20.0, periodicity="annual", data_quality="periodicity_mismatch"),
        facts=facts, computed_at=_now())
    assert ann.multiple is not None and ann.multiple.confidence == "weak"       # annual, flagged
    assert ann.data_quality and "periodicity_mismatch" in ann.data_quality      # flag rides anchor
    legacy = compute_anchor({"valuation": {"own_history": {"value": [
        {"metric": "EV/EBITDA (TEV/LTM)", "median": 10.0, "n_closes": 40}]}}},  # pre-metadata JSON
        facts=facts, computed_at=_now())
    assert legacy.multiple is not None and legacy.multiple.confidence == "weak"  # span-UNKNOWN


def test_own_history_band_carries_periodicity_and_provenance_fields() -> None:
    """Schema pin: the band exposes the self-describing metadata a consumer needs to judge the
    window — cadence/span/periodicity/data_quality — PLUS the provenance of the bytes it was read
    from (source_file is not identity: a stale same-named copy gave SMPL a phantom 4.98y band)."""
    from vinci.dossier.schemas import OwnHistoryBand
    assert {"periodicity_days_median", "window_span_years", "periodicity", "data_quality",
            "source_file", "source_sha256", "source_mtime"} <= set(OwnHistoryBand.model_fields)


def test_canonical_sync_always_overwrites_a_stale_local_copy(tmp_path: Path) -> None:
    """COPY DISCIPLINE — the SMPL incident. A stale same-named file already in the working location
    must be OVERWRITTEN from canonical (no skip-if-present), so the band carries the CANONICAL
    file's hash. A missing canonical folder FAILS LOUD rather than reading unknown-vintage bytes."""
    import hashlib

    from vinci.cli import sync_canonical_ciq
    from vinci.dossier.ciq_sheets import file_provenance
    canonical, local = tmp_path / "canon", tmp_path / "local"
    (canonical / "XYZ").mkdir(parents=True)
    (local / "XYZ").mkdir(parents=True)
    (canonical / "XYZ" / "f.xls").write_bytes(b"CANONICAL-CURRENT")
    (local / "XYZ" / "f.xls").write_bytes(b"STALE-OLD-COPY")          # the skip-if-present trap
    sync_canonical_ciq(canonical, local, ["XYZ"])
    assert (local / "XYZ" / "f.xls").read_bytes() == b"CANONICAL-CURRENT"   # overwritten, not kept
    sha, _mt = file_provenance(local / "XYZ" / "f.xls")
    assert sha == hashlib.sha256(b"CANONICAL-CURRENT").hexdigest()[:10]     # canonical hash stamped
    with pytest.raises(FileNotFoundError, match="canonical CIQ folder missing"):
        sync_canonical_ciq(canonical, local, ["ABSENT"])            # fail loud, no fallback


def test_replace_valuation_fields_is_byte_preserving() -> None:
    """The refresh writer swaps ONLY the named valuation fields; every other field keeps its
    committed bytes (json.dump(indent=2, ensure_ascii=False) reproduces the committed style — a
    unicode arrow stays literal, not \\u2192). An absent field → refuses rather than no-ops."""
    from vinci.dossier.anchor import replace_valuation_fields
    text = ('{\n  "ticker": "X",\n  "mechanical": {\n    "valuation": {\n'
            '      "own_history": {"value": [1]},\n      "range_position": {"value": "old→x"},\n'
            '      "pe": {"value": 3}\n    }\n  }\n}')
    out = replace_valuation_fields(text, {"own_history": {"value": [{"median": 9.9}]},
                                          "range_position": {"value": "new→y"}})
    parsed = json.loads(out)
    v = parsed["mechanical"]["valuation"]
    assert parsed["ticker"] == "X" and v["pe"] == {"value": 3}            # untouched
    assert v["own_history"]["value"] == [{"median": 9.9}]                 # replaced
    assert v["range_position"]["value"] == "new→y"                        # replaced together
    assert "new→y" in out and "\\u2192" not in out                        # unicode kept literal
    with pytest.raises(ValueError, match="valuation.nope absent"):
        replace_valuation_fields(text, {"nope": {}})


def test_committed_own_history_agrees_with_its_sibling_range_position() -> None:
    """COHERENCE PIN (the drift this PR's first pass introduced). own_history, range_position and
    ev_ebitda all read the SAME Multiples close series and the module guarantees they "can't drift".
    Refreshing the band ALONE left a 35-close band beside a string still reading "over 20 closes".
    Every committed dossier must quote the SAME median and close-count in both places."""
    import re
    for doss in sorted((_ROOT / "data" / "dossiers").glob("*/dossier.json")):
        val = (json.loads(doss.read_text()).get("mechanical") or {}).get("valuation") or {}
        oh, rp = val.get("own_history") or {}, val.get("range_position") or {}
        if oh.get("status") != "present" or rp.get("status") != "present":
            continue
        band = next((b for b in oh["value"] if "EBITDA" in str(b.get("metric", ""))), None)
        if not band:
            continue
        m = re.search(r"median ([\d.]+)x\) over (\d+) closes", str(rp.get("value") or ""))
        assert m, f"{doss.parent.name}: range_position string not parseable — {rp.get('value')!r}"
        assert round(float(m.group(1)), 1) == round(band["median"], 1), (
            f"{doss.parent.name}: range_position median {m.group(1)} != band {band['median']:.2f}")
        assert int(m.group(2)) == band["n_closes"], (
            f"{doss.parent.name}: range_position {m.group(2)} closes != band {band['n_closes']}")


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


def test_replace_anchor_block_is_byte_preserving_and_does_not_duplicate() -> None:
    """The re-backfill REPLACES a trailing anchor in place: other fields keep their committed bytes
    and the key is never duplicated (a second insert would produce two 'anchor' keys)."""
    a1 = Anchor(recipe_hint=RECIPE_R1, applicable=True, computed_at=_now())
    text = insert_anchor_block('{\n  "ticker": "X",\n  "midcycle": null\n}', a1)
    a2 = a1.model_copy(update={"anchor_base_value_per_share": 12.34})
    out = replace_anchor_block(text, a2)
    parsed = json.loads(out)
    assert parsed["ticker"] == "X" and parsed["midcycle"] is None          # untouched
    assert parsed["anchor"]["anchor_base_value_per_share"] == 12.34        # replaced
    assert out.count('"anchor":') == 1                                     # not duplicated
    assert out.startswith('{\n  "ticker": "X",\n  "midcycle": null,\n  "anchor": {')
