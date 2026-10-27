"""Tests for the persisted R1 anchor (vinci.dossier.anchor).

Pins the schema, the EBITDA-basis value math (the anchor recomputes from its OWN stored inputs and
uses EV = (EBIT + D&A) × multiple, not EBIT — the same guard as the WERN scenario pin), the
positivity guard (non-positive margin → R2_NEEDED), and the byte-preserving backfill insert.
"""
from __future__ import annotations

import json
import re
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
    per_share_shares,
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
        # ltm_fcf (2026-07-21, R2 cohort): the SURVIVAL input — a negative value IS the burn the
        # R2 gate divides cash by, so it is source-bound and basis-stamped like every other input.
        "ltm_fcf",
        "anchor_base_value_per_share", "anchor_ev_ebit", "overall_confidence", "note",
        # midcycle_gap (2026-09-21): R1's central assumption stated where it is STRETCHED — set
        # only when the LTM margin sits MIDCYCLE_GAP_PTS or more from the median, else absent.
        "midcycle_gap",
        # (2026-10-21) the per-share denominator — the point-in-time count where the filer's basic
        # weighted average corroborates it — and the dilution test struck beside the base.
        "shares_outstanding", "dilutive_increment", "anchor_base_value_per_share_diluted",
        # (2026-10-22) the operator's recipe decision in its own block, and the machine's own
        # recipe beside it — absent on a page no operator has decided.
        "operator_decision", "machine_recipe_hint",
        # (2026-10-27) the two band guards' outcomes beside the flag — absent where not reached
        "band_checks",
        # (2026-10-27) the CIQ bridge's scale-check outcome — absent where the bridge was not read
        "ciq_scale_check",
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
    # the count the base was struck on (`per_share_shares`: point-in-time since 2026-10-21)
    shares = per_share_shares(a)
    assert shares is not None
    sv = mc.scenario_value(
        mc.Scenario(name="base", revenue=a["ltm_revenue"]["value"], margin=a["margin"]["value"],
                    multiple=a["multiple"]["value"], source="anchor default",
                    d_and_a=a["d_and_a"]["value"]),
        net_debt=a["net_debt"]["value"], shares=shares)
    recomputed = sv.equity * 1e6 / shares
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
    value, source, _basis = aligned
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


def _real(ticker: str) -> dict[str, object]:
    """A frozen REAL companyfacts subset (scripts/build_companyfacts_fixture.py)."""
    facts: dict[str, object] = json.loads(
        (_ROOT / "tests" / "fixtures" / "companyfacts" / f"{ticker}.json").read_text())
    return facts


def test_the_flagged_years_leave_the_median_wlk() -> None:
    """The anchor flagged WLK's FY2011–15 revenue-tag conflict and capped the margin weak — and
    still took its median over those years: 16.31% on fifteen, where the clean decade gives 9.78%.
    A flag beside a contaminated number is not a guard. The years go, the source names them, and
    the flag and the cap stay (real companyfacts)."""
    a = compute_anchor(_MECH_OK, facts=_real("WLK"), computed_at=_now())
    assert a.margin is not None
    assert a.margin.value == pytest.approx(0.097831, abs=5e-7) and a.margin.anchor_years == 10
    assert a.data_quality == anc.DQ_REVENUE_TAG_CONFLICT and a.margin.confidence == "weak"
    assert sum("apart" in d for d in a.data_quality_detail) == 5
    assert all(f"FY{y}" in a.margin.source for y in range(2011, 2016))


def test_a_disputed_year_the_preferred_tag_wins_stays_in_the_median_vrrm() -> None:
    """VRRM's 606 total is the LARGER figure in all six disputed years, so the partial line is the
    other tag: the committed eight-year 20.9061% stands, still flagged (real companyfacts)."""
    a = compute_anchor(_MECH_OK, facts=_real("VRRM"), computed_at=_now())
    assert a.margin is not None
    assert a.margin.value == pytest.approx(0.209061, abs=5e-7) and a.margin.anchor_years == 8
    assert a.data_quality == anc.DQ_REVENUE_TAG_CONFLICT
    assert sum("apart" in d for d in a.data_quality_detail) == 6
    assert "EXCLUDED" not in a.margin.source


def test_a_restated_year_filed_with_its_operating_income_stays_hwm() -> None:
    """Howmet's FY2018 is $6,778M in its 2021 10-K — restated to continuing operations after the
    Arconic separation, filed beside that year's $775M operating income — against Arconic's
    $14,014M from the 2019 10-K. Size alone dropped the SMALLER figure, which is the right basis
    here; the filing decides it, and the ten-year 13.47% stands (real companyfacts)."""
    a = compute_anchor(_MECH_OK, facts=_real("HWM"), computed_at=_now())
    assert a.margin is not None
    assert a.margin.value == pytest.approx(0.134738, abs=5e-7) and a.margin.anchor_years == 10
    assert a.data_quality == anc.DQ_REVENUE_TAG_CONFLICT and "EXCLUDED" not in a.margin.source


def test_a_larger_figure_from_an_older_filing_than_its_operating_income_leaves_wor() -> None:
    """Worthington's preferred tag holds FY2022–23 as first reported, steel included ($5,242M,
    $4,916M, 2023 10-K). The operating income beside those years ($49M, $30M) comes from later 10-Ks
    restated without steel, which restated revenue too ($1,309M, $1,418M, under `Revenues`). Pairing
    them pulled the median to 0.93%. The mismatched figure is the LARGER one, so size alone kept it;
    the filing test drops both years (real companyfacts)."""
    a = compute_anchor(_MECH_OK, facts=_real("WOR"), computed_at=_now())
    assert a.margin is not None
    assert a.margin.anchor_years == 3 and a.margin.value == pytest.approx(0.038506, abs=5e-7)
    assert all(f"FY{y}" in a.margin.source for y in (2022, 2023))


def test_a_margin_emptied_by_excluded_years_says_so_in_its_reason() -> None:
    """When every overlapping year is one the preferred tag may be partial in, 'no fiscal year where
    both report' would be false — they did report. The refusal names the years it dropped."""
    facts = _facts(**{
        _TOTAL: dict.fromkeys(range(2016, 2022), 40e6),    # the preferred tag, partial throughout
        "Revenues": dict.fromkeys(range(2016, 2022), 160e6),
        "OperatingIncomeLoss": dict.fromkeys(range(2016, 2022), 16e6),
    })
    a = compute_anchor(_MECH_OK, facts=facts, computed_at=_now())
    assert a.recipe_hint == anc.RECIPE_UNRESOLVED and a.margin is None
    assert all(f"FY{y}" in (a.reason or "") for y in range(2016, 2022))


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
    # (31b) FILTERED sweep — its subject is the names carrying BOTH readings, so no relational
    # floor is expressible (counting them independently just re-runs the filter). The claim is a
    # cross-artifact coherence one that only exists on committed data, so it cannot move to a
    # fixture either: the whole fix is refusing to pass when the filter matches nothing.
    agreed = 0
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
        agreed += 1
    assert agreed, (
        "no committed dossier carries BOTH own_history and range_position as present — this "
        "coherence sweep compared ZERO pairs and would have passed however far the rendered "
        "string had drifted from the band it is built from")


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



# --- (2026-09-21) the period a ~12-month EDGAR point COVERS, not the fiscal year of its FILING ---
def _ttm_facts(tag: str, fy: float, ttm: float) -> dict[str, object]:
    """One tag carrying Amazon's REAL pair: the FY2025 10-K value and the trailing-twelve-month
    column of the Q2-2026 10-Q (2025-07-01 → 2026-06-30), which companyfacts stamps fy=2026."""
    return {"units": {"USD": [
        {"start": "2025-01-01", "end": "2025-12-31", "val": fy, "filed": "2026-02-06",
         "fy": 2025, "fp": "FY", "form": "10-K", "accn": "0001018724-26-000004"},
        {"start": "2025-07-01", "end": "2026-06-30", "val": ttm, "filed": "2026-07-31",
         "fy": 2026, "fp": "Q2", "form": "10-Q", "accn": "0001018724-26-000025"}]}}


def test_a_trailing_10q_window_is_labelled_by_its_period_not_its_filing_year() -> None:
    """AMZN's anchor read "latest FY2026 (not LTM)" for a free cash flow that is neither: FY2026
    had not ended, and the figure IS the trailing twelve months — Amazon's 10-Q carries that column,
    and companyfacts stamps it with the FILING's fiscal year. Its D&A said "FY2026" the same way.
    The values were right (the trailing window is the fresher, period-matched figure); the claims
    about them were not. Real values, verbatim from Amazon's filings."""
    facts = {"facts": {"us-gaap": {
        "NetCashProvidedByUsedInOperatingActivities": _ttm_facts("ocf", 139_514e6, 161_403e6),
        "PaymentsToAcquirePropertyPlantAndEquipment": _ttm_facts("capex", 131_819e6, 173_028e6),
        "DepreciationDepletionAndAmortization": _ttm_facts("da", 65_756e6, 75_200e6)}}}
    fcf = anc._latest_fcf(facts)
    assert isinstance(fcf, tuple), fcf
    value, basis, source = fcf
    assert value == pytest.approx(-11_625e6)                      # the value never changed
    assert "12m to 2026-06-30" in basis and "12m to 2026-06-30" in source
    assert "FY2026" not in basis + source, "a filing's fiscal year is not the period's"
    assert "not LTM" not in basis, "a trailing twelve-month window IS an LTM"

    da = _latest_dep_amort(facts)
    assert da is not None
    da_value, da_source, da_basis = da
    assert da_value == pytest.approx(75_200e6)
    assert "12m to 2026-06-30" in da_source and "FY2026" not in da_source
    assert da_basis == "consolidated trailing twelve months (the filer's own 10-Q column)"

    # ⊖ a filer with no trailing column keeps exactly the label it had
    fy_only = {"facts": {"us-gaap": {
        "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [_ttm_facts(
            "", 139_514e6, 0)["units"]["USD"][0]]}},                # type: ignore[index]
        "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": [_ttm_facts(
            "", 131_819e6, 0)["units"]["USD"][0]]}}}}}              # type: ignore[index]
    fy = anc._latest_fcf(fy_only)
    assert isinstance(fy, tuple) and fy[1] == "latest FY2025 (not LTM)"


# --- (2026-09-21) the R1 mid-cycle flag — real values, frozen as of the day it shipped --------
#: (median, years, LTM EBIT $M, LTM revenue $M) from the committed pages on 2026-09-21
_AMZN = (0.053144, 10, 93_712.0, 775_680.0)
_WLK = (0.097831, 10, 120.0, 11_294.0)
_LLY = (0.298207, 10, 39_608.0, 79_666.0)
_EPAM = (0.118997, 10, 627.861, 5_616.749)
#: GOOGL on the day its R1 published NO value ("R1 inputs incomplete"), from main at f4b0264
_GOOGL = (0.262717, 9, 147_628.0, 445_866.0)


def _gap(v: tuple[float, int, float, float], **kw: object) -> anc.AnchorMidcycleGap | None:
    return anc.midcycle_gap(v[0], v[1], ltm_ebit=v[2], ltm_revenue=v[3], **kw)  # type: ignore[arg-type]


def test_midcycle_flag_fires_both_ways_and_says_what_it_cannot_know() -> None:
    """R1 reverts the margin to its own median and pairs it with the multiple from the SAME history
    — internally consistent, and only as good as that history. AMZN's 5.3% median against a 12.1%
    LTM lands its anchor at $245.46 against a $245.96 price: two stale inputs offsetting, not a
    right answer. The page must say so, in BOTH directions, and never decide structural vs
    cyclical — that is the human's call."""
    up = _gap(_AMZN, basis=(2025, 0.112, 0.112))
    assert up is not None and up.ltm_side == "above"
    assert up.gap_pts == pytest.approx(6.77, abs=0.01)
    assert "ABOVE" in up.read and "12.1%" in up.read and "5.3%" in up.read
    # both readings offered, neither chosen
    assert "STRUCTURAL" in up.read and "PEAK" in up.read
    assert "agree within 0.0 points on FY2025" in up.read

    down = _gap(_WLK, basis=(2025, -0.141, -0.016))
    assert down is not None and down.ltm_side == "below" and down.gap_pts < -5
    assert "BELOW" in down.read and "TROUGH" in down.read
    # ⊖ the basis the flag cannot hide: WLK's GAAP carries 12.5 points of charges CIQ's EBIT strips
    assert down.basis_gap_pts == pytest.approx(12.5, abs=0.01)
    # … which pushes the shown gap UP, so on a gap BELOW it can only be hiding part of it. The first
    # version pinned "may be basis, not business" here — the defect itself, pinned as the expected
    # output (test_basis_sentence_follows_which_way_the_sources_disagree has the four cases)
    assert "may be basis, not business" not in down.read
    assert "narrows this gap rather than creating it" in down.read

    # ⊖ inside the threshold, and whenever a leg is missing: SILENT, never "checked and held"
    assert _gap(_EPAM, basis=(2025, 0.095, 0.107)) is None       # −0.7 points
    assert anc.midcycle_gap(0.053144, 10, ltm_ebit=None, ltm_revenue=775_680.0) is None
    assert anc.midcycle_gap(0.053144, 10, ltm_ebit=93_712.0, ltm_revenue=0.0) is None
    assert anc.midcycle_gap(None, 10, ltm_ebit=93_712.0, ltm_revenue=775_680.0) is None


def test_midcycle_flag_threshold_is_inclusive_at_five_points() -> None:
    """The boundary, pinned both sides: 4.99 points is silent, 5.00 fires."""
    assert anc.midcycle_gap(0.10, 10, ltm_ebit=14.99, ltm_revenue=100.0) is None
    hit = anc.midcycle_gap(0.10, 10, ltm_ebit=15.0, ltm_revenue=100.0)
    assert hit is not None and hit.gap_pts == pytest.approx(5.0)


def test_midcycle_flag_names_one_source_when_r1_already_fell_back_to_ciq() -> None:
    """LLY tags no OperatingIncomeLoss, so R1's median ALREADY came from the committed CIQ panel —
    both legs are one source. Calling that median 'EDGAR GAAP' would state a false provenance, and
    reporting 'no common fiscal year' would imply a comparison was attempted and failed."""
    g = _gap(_LLY, median_from_ciq=True)
    assert g is not None and g.same_source and g.basis_year is None
    assert "(CIQ EBIT)" in g.read and "EDGAR GAAP" not in g.read
    assert "no source difference to discount" in g.read


def test_basis_check_takes_the_latest_common_actual_year() -> None:
    """Estimates and the LTM column are never a fiscal year; the latest year BOTH sources report
    wins; no common year → None (the page then says so rather than guessing)."""
    mech = {"financial_summary": {"annual": {"value": {
        "columns": ["FY23", "FY24 (R)", "FY25", "LTM", "FY26E"],
        "is_estimate": [False, False, False, False, True],
        "rows": [{"label": "Revenue ($M)", "values": [100.0, 110.0, 120.0, 125.0, 130.0]},
                 {"label": "EBIT ($M)", "values": [10.0, 11.0, 18.0, 19.0, 99.0]}]}}}}
    assert anc.basis_check({2023: 0.10, 2024: 0.09, 2025: 0.12}, mech) == (2025, 0.12, 0.15)
    assert anc.basis_check({2023: 0.10, 2024: 0.09}, mech) == (2024, 0.09, 0.1)
    assert anc.basis_check({2019: 0.10}, mech) is None
    # ⊖ THE TIMING MISMATCH: EDGAR has filed FY2026 while the CIQ export still carries it as an
    #   ESTIMATE ("FY26E", is_estimate True). An estimate is not a reported year — the check
    #   stays on FY2025 — and it is the STRUCTURED flag that says so, not the label's "E".
    assert anc.basis_check({2024: 0.09, 2025: 0.12, 2026: 0.20}, mech) == (2025, 0.12, 0.15)


def test_an_anchor_that_does_not_fire_serialises_without_the_key() -> None:
    """The field is additive: an anchor it does not apply to writes NO key, so the committed pages
    it does not fire on stay byte-identical — and one it fires on carries the whole block."""
    quiet = Anchor(recipe_hint=RECIPE_R1, applicable=True, computed_at=_now())
    # the KEY is absent — the anchor's `scenario_eligibility` now NAMES the field, as one of R1's
    assert "midcycle_gap" not in json.loads(
        insert_anchor_block('{\n  "ticker": "X"\n}\n', quiet))["anchor"]
    loud = quiet.model_copy(update={"midcycle_gap": _gap(_AMZN, basis=(2025, 0.112, 0.112))})
    assert '"midcycle_gap"' in insert_anchor_block('{\n  "ticker": "X"\n}\n', loud)


def test_committed_pages_round_trip_byte_identically_with_the_new_field() -> None:
    """THE CORPUS CHECK for the additive claim: every committed dossier re-serialised through the
    one writer neither GROWS the key nor loses it — a page with no flag gains no null, a page with
    one keeps it.

    Asserted as presence PARITY, not absence. The first version asserted the key never appears,
    which holds only until an artifact pass lands a real flag — and it reddened on exactly that
    pass (AMZN, 2026-09-21), a guard written for a null key refusing a legitimate one."""
    from vinci.dossier.schemas import dossier_json
    seen = 0
    for jp in sorted((_ROOT / "data" / "dossiers").glob("*/dossier.json")):
        raw = jp.read_text()
        doc = Dossier.model_validate_json(raw)
        if doc.anchor is None:
            continue
        seen += 1
        written = dossier_json(doc)
        assert ('"midcycle_gap"' in written) is ('"midcycle_gap"' in raw), (
            f"{jp.parent.name} grew or lost the key on round-trip")
        assert '"midcycle_gap": null' not in written, f"{jp.parent.name} grew a null key"
    assert seen >= 1, "no committed anchor to test against — the pin is blind"


def test_the_flag_reaches_both_rendered_pages_end_to_end() -> None:
    """TEST-LAYER RULE: the rendered artifact, from REAL committed JSON. AMZN's own page, given the
    flag its own numbers produce, prints the heading and the stored sentence in the Python renderer
    and the JS one; EPAM's page, which does not fire, prints neither."""
    import shutil
    import subprocess

    from vinci.dossier import render as dr
    amzn = Dossier.model_validate_json((_ROOT / "data/dossiers/AMZN/dossier.json").read_text())
    assert amzn.anchor is not None
    m = amzn.mechanical.model_dump(mode="json")
    gap = anc.midcycle_gap(amzn.anchor.margin.value if amzn.anchor.margin else None, 10,
                           ltm_ebit=anc._ltm_ebit_from_fs(m),
                           ltm_revenue=anc._ltm_revenue_from_fs(m))
    assert gap is not None, "AMZN's own numbers no longer fire the flag — re-check the fixture"
    flagged = amzn.anchor.model_copy(update={"midcycle_gap": gap})
    py = "\n".join(dr._screening_context_lines(flagged))
    assert "Mid-cycle assumption under strain." in py and gap.read in py
    epam = Dossier.model_validate_json((_ROOT / "data/dossiers/EPAM/dossier.json").read_text())
    assert "Mid-cycle assumption" not in "\n".join(dr._screening_context_lines(epam.anchor))

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    page = json.loads((_ROOT / "data/dossiers/AMZN/dossier.json").read_text())
    page["anchor"]["midcycle_gap"] = json.loads(gap.model_dump_json())
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const flagged = renderDossier(JSON.parse(readFileSync(process.argv[1], "utf8")), null);
const epam = JSON.parse(readFileSync("data/dossiers/EPAM/dossier.json", "utf8"));
const plain = renderDossier(epam, null);
console.log(JSON.stringify({ on: flagged.includes("Mid-cycle assumption under strain."),
  sentence: flagged.includes("sits 6.8 points ABOVE"),
  off: plain.includes("Mid-cycle assumption") }));
"""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(page, fh)
    out = subprocess.run(["node", "--input-type=module", "-e", driver, fh.name], cwd=_ROOT,
                         capture_output=True, text=True, check=True)
    assert json.loads(out.stdout.strip().splitlines()[-1]) == {"on": True, "sentence": True,
                                                               "off": False}


def test_midcycle_basis_verdict_is_decided_on_the_stored_rounding() -> None:
    """(review of #636) The gap is decided on the rounding it is stored at; the basis disagreement
    must be too. Unrounded, a 1.996-point disagreement read "agree" while the record stored
    basis_gap_pts=2.0 — a value the threshold itself calls "differ". Sentence and record must agree.
    ⊕ just inside the threshold agrees; ⊖ a value that stores as 2.0 differs."""
    inside = _gap(_AMZN, basis=(2025, 0.100, 0.1198))            # 1.98 points
    assert inside is not None and inside.basis_gap_pts == pytest.approx(1.98)
    assert "agree within" in inside.read
    edge = _gap(_AMZN, basis=(2025, 0.100, 0.119996))            # 1.9996 → stored 2.0
    assert edge is not None and edge.basis_gap_pts == pytest.approx(2.0)
    assert "agree within" not in edge.read and "may be basis, not business" in edge.read


def test_midcycle_flag_never_points_at_a_value_that_is_not_published() -> None:
    """(review of #636) The flag rides on EVERY R1 anchor, including the ones that publish no base
    value (GOOGL, NFLX on 2026-09-21: "R1 inputs incomplete"). "so this value answers …" there
    points at nothing on the page. Both directions must name the recipe's value, not a
    demonstrative."""
    for g in (_gap(_AMZN), _gap(_WLK)):
        assert g is not None and "this value" not in g.read and "an R1 value" in g.read
    # THE UNVALUED CASE ON FROZEN NUMBERS. The first version read GOOGL's LIVING page and asserted
    # it published no base — true until the 2026-09-22 backfill's CIQ bridge gave GOOGL a value,
    # when the pin reddened for a reason that had nothing to do with the sentence. A value pin on a
    # re-drawn artifact is what the TEST-LAYER RULE forbids; the unvalued anchor is built here from
    # GOOGL's own numbers on the day it published none, and rendered through the screening block.
    from vinci.dossier import render as dr
    g = _gap(_GOOGL)
    assert g is not None and g.ltm_side == "above"
    unvalued = Anchor(recipe_hint=RECIPE_R1, applicable=False, computed_at=_now(),
                      reason="R1 inputs incomplete — see per-input source stamps", midcycle_gap=g)
    md = "\n".join(dr._screening_context_lines(unvalued))
    assert "Mid-cycle assumption under strain." in md and g.read in md
    assert "this value" not in md and "an R1 value" in md
    assert "spot-independent" not in md          # no base row: nothing is published to point at


# --- (2026-09-21, first artifact pass to carry the flag) which way the basis difference points ---
_INFLATES, _HIDES = "may be basis, not business", "narrows this gap rather than creating it"
#: the screening-block fence's own pattern (test_parity_pins)
_SIGNED_PCT = re.compile(r"[+-]\d+(\.\d+)?%")


def test_basis_sentence_follows_which_way_the_sources_disagree() -> None:
    """The twelve months are CIQ and the median GAAP, so a year where CIQ reads above GAAP pushes
    the shown gap UP: it can manufacture part of a gap ABOVE and can only NARROW a gap BELOW — and
    the mirror where CIQ reads below. The first version said "part of this gap may be basis" in all
    four cases; WLK's page (8.7 BELOW, CIQ 12.5 ABOVE GAAP on FY2025) told the reader to discount a
    gap that measures 8.8 points with CIQ on both legs and 20.8 with GAAP on both."""
    cases = [  # (median, LTM EBIT on revenue 100, (year, GAAP, CIQ), inflates?)
        (0.05, 12.0, (2025, 0.02, 0.06), True),     # ABOVE, CIQ above GAAP
        (0.10, 2.0, (2025, 0.00, 0.05), False),     # BELOW, CIQ above GAAP — WLK's quadrant
        (0.10, 2.0, (2025, 0.06, 0.02), True),      # BELOW, CIQ below GAAP
        (0.05, 12.0, (2025, 0.06, 0.02), False),    # ABOVE, CIQ below GAAP
    ]
    for med, ebit, basis, inflates in cases:
        g = anc.midcycle_gap(med, 10, ltm_ebit=ebit, ltm_revenue=100.0, basis=basis)
        assert g is not None
        assert (_INFLATES in g.read) is inflates and (_HIDES in g.read) is (not inflates), g.read
        # the cause is named only where it is the cause: charges GAAP carries put CIQ ABOVE it
        assert ("carries charges" in g.read) is (basis[2] > basis[1]), g.read
        # the direction is DATA, not only prose: both margins ride beside the unsigned gap
        assert (g.basis_gaap_margin, g.basis_ciq_margin) == (basis[1], basis[2])
    # ⊖ no year to test, or one source: no margins stored and no direction claimed
    for g in (_gap(_AMZN), _gap(_LLY, median_from_ciq=True)):
        assert g is not None and g.basis_gaap_margin is None and g.basis_ciq_margin is None
        assert _INFLATES not in g.read and _HIDES not in g.read


def test_the_flag_never_prints_a_signed_percentage() -> None:
    """The screening block is fenced against ANY signed percentage (test_parity_pins: one there
    reads as an upside against spot). WLK's FY2025 is a loss on both sources, and the first version
    printed "GAAP -14.1% vs CIQ -1.6%" — red on the first artifact pass to carry the flag. A loss
    is stated in words, and so is a loss-making twelve months; a positive margin still prints as a
    plain level."""
    wlk = _gap(_WLK, basis=(2025, -0.141, -0.016))
    assert wlk is not None
    assert not _SIGNED_PCT.search(wlk.read), wlk.read
    assert "GAAP a 14.1% loss vs CIQ a 1.6% loss" in wlk.read
    loss = anc.midcycle_gap(0.06, 10, ltm_ebit=-3.0, ltm_revenue=100.0)
    assert loss is not None
    assert not _SIGNED_PCT.search(loss.read), loss.read
    assert "operating margin of a 3.0% loss" in loss.read
    amzn = _gap(_AMZN)
    assert amzn is not None and "operating margin of 12.1%" in amzn.read


def test_wlk_flag_reaches_the_screening_block_unsigned_and_the_right_way_round_e2e() -> None:
    """TEST-LAYER RULE — the failure was OBSERVED on WLK's rendered page, so it is pinned there:
    WLK's committed JSON, the flag its own committed numbers produce (LTM and median from the page,
    the basis year checked against its committed CIQ panel), rendered through the screening block
    the fence reads. The one input frozen here is EDGAR's FY2025 GAAP margin — companyfacts
    OperatingIncomeLoss −1,578 / Revenues 11,170 ($M, fiscal year ending 2025-12-31), fetched
    2026-09-21. The direction is asserted from WHICHEVER quadrant the page's numbers land in, so a
    re-assembled page cannot turn this into a stale value pin."""
    from vinci.dossier import render as dr
    wlk = Dossier.model_validate_json((_ROOT / "data/dossiers/WLK/dossier.json").read_text())
    assert wlk.anchor is not None and wlk.anchor.margin is not None
    m = wlk.mechanical.model_dump(mode="json")
    basis = anc.basis_check({2025: -1578 / 11170}, m)
    assert basis is not None and basis[0] == 2025, "WLK's panel no longer carries FY2025 actuals"
    gap = anc.midcycle_gap(wlk.anchor.margin.value, wlk.anchor.margin.anchor_years,
                           ltm_ebit=anc._ltm_ebit_from_fs(m),
                           ltm_revenue=anc._ltm_revenue_from_fs(m), basis=basis)
    assert gap is not None, "WLK's own numbers no longer fire the flag — re-pick the fixture"
    assert gap.basis_gap_pts is not None and gap.basis_gap_pts >= anc.BASIS_AGREE_PTS
    flagged = wlk.anchor.model_copy(update={"midcycle_gap": gap})
    md = "\n".join(dr._screening_context_lines(flagged))
    assert "Mid-cycle assumption under strain." in md and gap.read in md
    assert not _SIGNED_PCT.search(md), md
    inflates = (basis[2] > basis[1]) == (gap.gap_pts > 0)
    assert (_INFLATES in md) is inflates and (_HIDES in md) is (not inflates), md


def test_every_committed_flag_states_the_basis_the_right_way_round() -> None:
    """The corpus half of the direction rule, read from the STRUCTURED margins — never parsed back
    out of the sentence: wherever a committed flag says the sources differ, it says "may be basis"
    exactly when the difference pushes the shown gap the way the gap points, and "narrows"
    otherwise. A flag written before the margins were stored has none, and is refused rather than
    excused. Until an artifact pass lands a flag this reads nothing — by design: the three pins
    above carry the rule, and this one was shown to catch WLK's page as the first pass wrote it."""
    for jp in sorted((_ROOT / "data" / "dossiers").glob("*/dossier.json")):
        a = Dossier.model_validate_json(jp.read_text()).anchor
        g = a.midcycle_gap if a is not None else None
        if g is None or g.basis_gap_pts is None or g.basis_gap_pts < anc.BASIS_AGREE_PTS:
            continue
        assert g.basis_gaap_margin is not None and g.basis_ciq_margin is not None, (
            f"{jp.parent.name}: the flag says the sources differ but stores neither margin — "
            "written before the direction was data; re-run anchor-backfill")
        inflates = (g.basis_ciq_margin > g.basis_gaap_margin) == (g.gap_pts > 0)
        assert (_INFLATES in g.read) is inflates and (_HIDES in g.read) is (not inflates), (
            jp.parent.name, g.read)
