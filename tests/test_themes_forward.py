"""Regression tests for the Stage-4 forward-validation harness (vinci/themes/forward.py).

Offline / fixture-based (injected price + membership functions — no network, no real dispositions).
Pins the load-bearing behaviour: the ledger is append-only (a correction is a new row, last wins);
the worksheet loader NEVER fabricates a disposition (empty -> pending); a basket cannot freeze until
every name is RATIFIED/PASSED (the DIG-DEEPER guard); spreads are computed BOTH pooled AND by chain
layer (§4); the §3c partial-kill state is sign-based and (the honest §3b-i property) UNREACHABLE
from the equal-weight baseline with both legs present; every report carries the §4 power label;
onset is logged forward append-only, null for a never-co-mover; and the schemas cannot conclude.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from vinci.themes.forward import (
    HOLD_NONE_HONESTY,
    Diagnostic,
    Disposition,
    FrozenBaskets,
    HoldNoneReport,
    LayerSplit,
    LayerSpread,
    PowerLabel,
    PriceFn,
    RatificationRecord,
    SpreadReport,
    append_record,
    classify_state,
    current_dispositions,
    diagnostic_avoid_discipline,
    early_vs_late,
    freeze_baskets,
    load_ledger,
    measure_hold_none,
    measure_horizon,
    naive_by_layer,
    power_label,
    records_from_worksheet,
    undefined_ratified_measures,
    update_onsets,
    watchlist_onset_baselines,
)


def _rec(ticker: str, disp: Disposition, layer: str = "chips/GPU",
         onset: date | None = None) -> RatificationRecord:
    return RatificationRecord(
        ticker=ticker, cik="1", driver="AI-DC", chain_layer=layer,
        machine_grade="committed-capacity",
        driver_tie="chain-layer-specific", grade_fact="f", source_ref="acc", disposition=disp,
        rationale="r", ratification_date=date(2026, 1, 1), comovement_onset_date=onset)


def _price_fn(prices: dict[tuple[str, str], float]) -> PriceFn:
    def fn(ticker: str, day: date) -> float | None:
        return prices.get((ticker, day.isoformat()))
    return fn


# ---- Component 1: the append-only ledger --------------------------------------------------------
def test_ledger_append_only_last_wins(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    append_record(p, _rec("AAA", Disposition.PASSED))
    append_record(p, _rec("BBB", Disposition.RATIFIED))
    append_record(p, _rec("AAA", Disposition.RATIFIED))  # a CORRECTION — new row, never a mutation
    rows = load_ledger(p)
    assert len(rows) == 3  # all three rows persist (append-only — nothing overwritten)
    cur = current_dispositions(rows)
    assert cur["AAA"].disposition is Disposition.RATIFIED  # the latest AAA row wins
    assert cur["BBB"].disposition is Disposition.RATIFIED


def test_records_from_worksheet_skips_empty_never_fabricates(tmp_path: Path) -> None:
    csv = tmp_path / "ws.csv"
    csv.write_text(
        "chain_layer,ticker,cik,machine_grade,grade_driver_tie,grade_fact,grade_accession,"
        "DISPOSITION,RATIONALE\n"
        "chips/GPU,AAA,1,committed-capacity,chain-layer-specific,fact-a,acc-a,"
        "RATIFIED,real enabler\n"
        "power/electrical,BBB,2,committed-capacity,indirect,fact-b,acc-b,PASSED,generic power\n"
        "HBM/memory,CCC,3,committed-capacity,chain-layer-specific,fact-c,acc-c,,\n")  # CCC pending
    recs, pending = records_from_worksheet(csv, driver="AI-DC", ratification_date=date(2026, 1, 1))
    assert pending == 1  # CCC has no disposition — pending, NOT fabricated
    assert {r.ticker for r in recs} == {"AAA", "BBB"}
    assert next(r for r in recs if r.ticker == "AAA").disposition is Disposition.RATIFIED
    assert next(r for r in recs if r.ticker == "BBB").disposition is Disposition.PASSED


# ---- Component 2: the frozen baskets + DIG-DEEPER guard -----------------------------------------
def test_freeze_guard_blocks_until_all_resolved() -> None:
    layer_of = {"AAA": "chips/GPU", "BBB": "power/electrical", "CCC": "HBM/memory"}
    all_committed = ["AAA", "BBB", "CCC"]
    # a DIG-DEEPER present → cannot freeze
    recs = [_rec("AAA", Disposition.RATIFIED), _rec("BBB", Disposition.PASSED),
            _rec("CCC", Disposition.DIG_DEEPER)]
    with pytest.raises(ValueError, match="cannot freeze"):
        freeze_baskets(recs, all_committed, driver="AI-DC", freeze_timestamp="2026-07-01T00:00:00",
                       layer_of=layer_of)
    # a MISSING disposition → cannot freeze
    with pytest.raises(ValueError, match="cannot freeze"):
        freeze_baskets(recs[:2], all_committed, driver="AI-DC",
                       freeze_timestamp="2026-07-01T00:00:00", layer_of=layer_of)
    # all resolved → freezes with the correct legs
    recs2 = [_rec("AAA", Disposition.RATIFIED), _rec("BBB", Disposition.PASSED),
             _rec("CCC", Disposition.RATIFIED)]
    b = freeze_baskets(recs2, all_committed, driver="AI-DC", freeze_timestamp="2026-07-01T00:00:00",
                       layer_of=layer_of)
    assert b.ratified == ("AAA", "CCC") and b.passed == ("BBB",)
    assert b.all_committed == ("AAA", "BBB", "CCC")
    assert b.entry_dates["AAA"] == "2026-01-01"
    assert b.deferred_controls  # the §3b-ii keyword/co-movement control recorded as deferred


# ---- Component 3: layer-aware spreads, partial-kill, power --------------------------------------
def test_classify_state_is_sign_based() -> None:
    assert classify_state(0.05, 0.02, 2) == "EDGE-DIRECTIONAL"   # both positive
    assert classify_state(0.05, -0.01, 2) == "PARTIAL-KILL"  # naive not beaten (§3c)
    assert classify_state(0.05, 0.0, 2) == "PARTIAL-KILL"        # rmn == 0 counts as not-beaten
    assert classify_state(-0.01, 0.9, 2) == "NO-SELECTION"       # human did not sort the tier
    assert classify_state(0.05, 0.02, 0) == "INSUFFICIENT"       # no ratified names


def _two_layer_baskets() -> FrozenBaskets:
    layer_of = {"T1": "thermal/cooling", "T2": "thermal/cooling",
                "C1": "chips/GPU", "C2": "chips/GPU"}
    return FrozenBaskets(
        driver="AI-DC", freeze_timestamp="2026-07-01T00:00:00", ratified=("T1", "C1"),
        passed=("T2", "C2"), all_committed=("T1", "T2", "C1", "C2"),
        entry_dates=dict.fromkeys(("T1", "T2", "C1", "C2"), "2026-01-01"), layer_of=layer_of)


def test_measure_is_layer_aware_and_power_labelled() -> None:
    b = _two_layer_baskets()
    prices = {
        ("IWM", "2026-01-01"): 100.0, ("IWM", "2026-04-01"): 110.0,   # benchmark +10%
        ("T1", "2026-01-01"): 100.0, ("T1", "2026-04-01"): 130.0,     # +30% → adj +20%
        ("T2", "2026-01-01"): 100.0, ("T2", "2026-04-01"): 105.0,     # +5%  → adj -5%
        ("C1", "2026-01-01"): 100.0, ("C1", "2026-04-01"): 120.0,     # +20% → adj +10%
        ("C2", "2026-01-01"): 100.0, ("C2", "2026-04-01"): 118.0,     # +18% → adj +8%
    }
    rep = measure_horizon(b, price_fn=_price_fn(prices), horizon_days=90, as_of=date(2026, 7, 1))
    assert isinstance(rep, SpreadReport)
    layers = {ls.scope: ls for ls in rep.by_layer}
    assert set(layers) == {"thermal/cooling", "chips/GPU"}  # broken out BY LAYER (§4)
    # the thin layer shows a bigger rat-passed spread than the obvious layer (the layer-aware point)
    assert layers["thermal/cooling"].ratified_minus_passed is not None
    assert layers["chips/GPU"].ratified_minus_passed is not None
    assert (layers["thermal/cooling"].ratified_minus_passed
            > layers["chips/GPU"].ratified_minus_passed)
    # EVERY report carries the §4 power label; one driver / fresh freeze → UNPOWERED
    assert rep.power.label == "UNPOWERED"
    assert "DIRECTIONAL" in rep.power.note


def test_equal_weight_partial_kill_unreachable_with_both_legs() -> None:
    """The honest §3b-i property: with both legs present, RATIFIED-NAIVE(equal-weight) shares the
    sign of RATIFIED-PASSED, so measure can NOT surface a strict partial-kill from the equal-weight
    baseline. apparatus_fraction (= n_passed/N) surfaces the '~0' case for the human to judge."""
    b = _two_layer_baskets()
    prices = {
        ("IWM", "2026-01-01"): 100.0, ("IWM", "2026-04-01"): 100.0,
        ("T1", "2026-01-01"): 100.0, ("T1", "2026-04-01"): 120.0,
        ("T2", "2026-01-01"): 100.0, ("T2", "2026-04-01"): 105.0,
        ("C1", "2026-01-01"): 100.0, ("C1", "2026-04-01"): 112.0,
        ("C2", "2026-01-01"): 100.0, ("C2", "2026-04-01"): 108.0,
    }
    rep = measure_horizon(b, price_fn=_price_fn(prices), horizon_days=90, as_of=date(2026, 7, 1))
    assert rep.partial_kill_scopes == ()  # cannot fire from equal-weight with both legs present
    # apparatus_fraction is populated where ratified-minus-passed > 0 (the human reads it for '~0')
    assert rep.pooled.apparatus_fraction is not None


def test_power_label_floor() -> None:
    # below the floor → UNPOWERED (and the label vocabulary never says "significant")
    lo = power_label(theme_quarters=2, drivers=1, sign_consistent=True)
    assert lo.label == "UNPOWERED"
    assert "significant" not in lo.label.lower()
    # at the a-priori floor → POWERED-DIRECTIONAL (still directional, never a significance claim)
    hi = power_label(theme_quarters=8, drivers=4, sign_consistent=True)
    assert hi.label == "POWERED-DIRECTIONAL"
    # sign inconsistency alone keeps it unpowered even with size
    mix = power_label(theme_quarters=12, drivers=5, sign_consistent=False)
    assert mix.label == "UNPOWERED"


# ---- Component 4: early-detection onset ----------------------------------------------------------
def test_onset_logged_forward_append_only(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    recs = [_rec("AAA", Disposition.RATIFIED), _rec("BBB", Disposition.RATIFIED),
            _rec("CCC", Disposition.PASSED)]
    for r in recs:
        append_record(p, r)
    # AAA co-moves as of 2026-06-01; BBB never; CCC is PASSED (not tracked for onset)
    def member(ticker: str, as_of: date) -> bool:
        return ticker == "AAA"
    new = update_onsets(load_ledger(p), p, member, as_of=date(2026, 6, 1))
    assert [r.ticker for r in new] == ["AAA"]  # only the co-moving ratified name gets a new row
    cur = current_dispositions(load_ledger(p))
    assert cur["AAA"].comovement_onset_date == date(2026, 6, 1)  # stamped forward
    assert cur["BBB"].comovement_onset_date is None  # never co-moved → logged null, not an error


def test_early_vs_late_split_and_null() -> None:
    prices = {
        ("IWM", "2026-01-01"): 100.0, ("IWM", "2026-04-01"): 100.0, ("IWM", "2026-07-01"): 100.0,
        ("AAA", "2026-01-01"): 100.0, ("AAA", "2026-04-01"): 130.0, ("AAA", "2026-07-01"): 140.0,
    }
    pf = _price_fn(prices)
    # onset stamped → early (ratification→onset) and late (onset→forward) both computed
    with_onset = _rec("AAA", Disposition.RATIFIED, onset=date(2026, 4, 1))
    r1 = early_vs_late(with_onset, price_fn=pf, benchmark="IWM", forward_asof=date(2026, 7, 1))
    assert r1["late_adj"] is not None and r1["onset"] == "2026-04-01"
    # never co-moved → late is None, a logged null (not an error)
    no_onset = _rec("AAA", Disposition.RATIFIED, onset=None)
    r2 = early_vs_late(no_onset, price_fn=pf, benchmark="IWM", forward_asof=date(2026, 7, 1))
    assert r2["late_adj"] is None and r2["onset"] is None


# ---- the dead-signal firewall: the schemas cannot conclude --------------------------------------
def test_schemas_cannot_conclude() -> None:
    forbidden = ("score", "rank", "verdict", "recommend", "buy", "sell", "priority", "target")
    models = (RatificationRecord, FrozenBaskets, LayerSpread, SpreadReport, PowerLabel,
              Diagnostic, LayerSplit, HoldNoneReport)
    for model in models:
        for name in model.model_fields:
            for tok in forbidden:
                assert tok not in name.lower(), f"{model.__name__}.{name}: verdict token {tok}"


# ------------------------------------------------------------------------------------------------
# Empty-BUY (zero-RATIFIED / hold-none) — the scoped modification for the all-PASSED triage
# ------------------------------------------------------------------------------------------------
def _passed(ticker: str, layer: str) -> RatificationRecord:
    """A PASSED record whose ratification_date IS the freeze date (Component 1: hold-none entry)."""
    return RatificationRecord(
        ticker=ticker, cik="1", driver="AI-DC", chain_layer=layer,
        machine_grade="committed-capacity", driver_tie="chain-layer-specific", grade_fact="f",
        source_ref="acc", disposition=Disposition.PASSED, rationale="passed",
        ratification_date=date(2026, 7, 2))


def _empty_buy_baskets() -> FrozenBaskets:
    """All PASSED, zero RATIFIED — the real triage reality; 4 names across thin + obvious layers."""
    layer_of = {"A": "thermal/cooling", "B": "chips/GPU",
                "C": "HBM/memory", "D": "power/electrical"}
    recs = [_passed(t, layer_of[t]) for t in ("A", "B", "C", "D")]
    return freeze_baskets(recs, ["A", "B", "C", "D"], driver="AI-DC",
                          freeze_timestamp="2026-07-02T00:00:00", layer_of=layer_of,
                          watchlist=["A", "C"], watchlist_triggers={"A": "t-A", "C": "t-C"})


_HN_PRICES = {
    ("IWM", "2026-07-02"): 100.0, ("IWM", "2026-09-30"): 110.0,   # benchmark +10%
    ("A", "2026-07-02"): 100.0, ("A", "2026-09-30"): 150.0,       # +50% adj +40%
    ("B", "2026-07-02"): 100.0, ("B", "2026-09-30"): 120.0,       # +20% adj +10%
    ("C", "2026-07-02"): 100.0, ("C", "2026-09-30"): 130.0,       # +30% adj +20%
    ("D", "2026-07-02"): 100.0, ("D", "2026-09-30"): 105.0,       # +5%  adj -5%
}


def test_empty_buy_freezes_without_error() -> None:
    b = _empty_buy_baskets()
    assert b.ratified == ()                       # empty BUY leg — does NOT error
    assert set(b.passed) == {"A", "B", "C", "D"}
    assert b.watchlist == ("A", "C") and b.watchlist_triggers == {"A": "t-A", "C": "t-C"}


def test_watchlist_must_be_in_committed() -> None:
    with pytest.raises(ValueError, match="not in the committed tier"):
        freeze_baskets([_passed("A", "chips/GPU")], ["A"], driver="d",
                       freeze_timestamp="2026-07-02T00:00:00", layer_of={"A": "chips/GPU"},
                       watchlist=["ZZZ"])


def test_undefined_ratified_measures_never_zero() -> None:
    b = _empty_buy_baskets()
    und = undefined_ratified_measures(b)
    assert len(und) == 3 and all(reason for _, reason in und)  # each has a reason, never 0.0
    assert any("RATIFIED-PASSED" in m for m, _ in und)
    assert undefined_ratified_measures(b.model_copy(update={"ratified": ("A",)})) == ()  # BUY→none


def test_hold_none_diagnostics_compute() -> None:
    rep = measure_hold_none(_empty_buy_baskets(), exposure_names=["A", "C"],
                            price_fn=_price_fn(_HN_PRICES), horizon_days=90,
                            as_of=date(2026, 9, 30))
    assert isinstance(rep, HoldNoneReport)
    # DIAGNOSTIC 1 (avoid-discipline): NAIVE-4 raw mean = (50+20+30+5)/4 = 26.25%
    assert rep.avoid_discipline.value == pytest.approx(0.2625, abs=1e-6)
    assert "BETA-CONFOUNDED" in rep.avoid_discipline.confound
    # DIAGNOSTIC 2 (exposure-carry): [A,C] adj 30% − [B,D] adj 2.5% = 27.5%
    assert rep.exposure_carry.value == pytest.approx(0.275, abs=1e-6)
    assert "PARTIALLY beta-controlled" in rep.exposure_carry.confound
    # LAYER-AWARE (not pooled): thin [A,C] adj 30% vs obvious [B,D] adj 2.5%
    assert rep.layer_split.thin_return == pytest.approx(0.30, abs=1e-6)
    assert rep.layer_split.obvious_return == pytest.approx(0.025, abs=1e-6)
    # RATIFIED-dependent spreads UNDEFINED, not 0.0; honesty label present
    assert len(rep.undefined_measures) == 3
    assert "UNDEFINED" in rep.honesty_label and "NOT a validation" in rep.honesty_label


def test_forward_only_pending_at_freeze_and_ignores_pre_freeze() -> None:
    b = _empty_buy_baskets()
    # as_of == freeze → no horizon reached → pending (None), NOT 0.0
    now = measure_hold_none(b, exposure_names=["A", "C"], price_fn=_price_fn(_HN_PRICES),
                            horizon_days=90, as_of=date(2026, 7, 2))
    assert now.avoid_discipline.value is None and now.avoid_discipline.n == 0
    # a pre-freeze price is NEVER used: A at 2026-06-01 = 25 is ignored; entry = freeze (100)
    pre = dict(_HN_PRICES)
    pre[("A", "2026-06-01")] = 25.0
    rep = measure_hold_none(b, exposure_names=["A", "C"], price_fn=_price_fn(pre),
                            horizon_days=90, as_of=date(2026, 9, 30))
    assert rep.layer_split.thin_return == pytest.approx(0.30, abs=1e-6)  # A = 150/100, not 150/25


def test_forward_only_skips_entry_before_freeze() -> None:
    b = FrozenBaskets(driver="d", freeze_timestamp="2026-07-02T00:00:00", ratified=(),
                      passed=("A", "OLD"), all_committed=("A", "OLD"),
                      entry_dates={"A": "2026-07-02", "OLD": "2026-06-01"},
                      layer_of={"A": "chips/GPU", "OLD": "chips/GPU"})
    prices = {("IWM", "2026-07-02"): 100.0, ("IWM", "2026-09-30"): 100.0,
              ("A", "2026-07-02"): 100.0, ("A", "2026-09-30"): 120.0,
              ("OLD", "2026-06-01"): 100.0, ("OLD", "2026-07-02"): 100.0,
              ("OLD", "2026-09-30"): 200.0}
    d1 = diagnostic_avoid_discipline(b, _price_fn(prices), horizon_days=90, as_of=date(2026, 9, 30))
    assert d1.n == 1 and d1.value == pytest.approx(0.20, abs=1e-6)  # OLD (entry<freeze) skipped


def test_watchlist_onset_baseline() -> None:
    base = watchlist_onset_baselines(("A", "C"), lambda t, d: t == "A", as_of=date(2026, 7, 2))
    assert base == {"A": "2026-07-02", "C": None}  # A already co-moving; C not-yet (the anchor)


def test_hold_none_honesty_is_not_an_edge_verdict() -> None:
    assert "UNDEFINED" in HOLD_NONE_HONESTY and "NOT a validation" in HOLD_NONE_HONESTY
    assert "zero RATIFIED" in HOLD_NONE_HONESTY


# ---- 2nd-driver generalization: demand-shaped schema + avoid-controls + category split ----------
def test_records_from_worksheet_reads_demand_shaped_schema(tmp_path: Path) -> None:
    """The defense worksheet uses category / grade_concreteness / driver_tie for the SAME fields the
    AI-datacenter worksheet calls chain_layer / machine_grade / grade_driver_tie — the loader reads
    either (driver-agnostic), so the 2nd driver freezes without a schema rewrite."""
    csv = tmp_path / "defense_ws.csv"
    csv.write_text(
        "category,ticker,cik,grade_concreteness,driver_tie,grade_fact,grade_accession,"
        "DISPOSITION,RATIONALE\n"
        "attritable-air,RCAT,1,binding-contract,driver-specific,Teal $9.5M Army SRR,acc-r,"
        "PASSED,real but priced\n"
        "munitions-scale,NEU,2,committed-capacity,driver-specific,AP +50% line,acc-n,PASSED,rich\n")
    recs, pending = records_from_worksheet(csv, driver="defense-demand-shift",
                                           ratification_date=date(2026, 7, 3))
    assert pending == 0 and {r.ticker for r in recs} == {"RCAT", "NEU"}
    rcat = next(r for r in recs if r.ticker == "RCAT")
    assert rcat.chain_layer == "attritable-air"        # category -> chain_layer
    assert rcat.machine_grade == "binding-contract"    # grade_concreteness -> machine_grade
    assert rcat.driver_tie == "driver-specific"         # driver_tie -> driver_tie


def _defense_baskets() -> FrozenBaskets:
    """Zero-RATIFIED defense-shaped freeze: parallel capability CATEGORIES (not chain layers), with
    an avoid-controls near-miss cohort inside the PASSED leg."""
    layer_of = {"RCAT": "attritable-air", "NEU": "munitions-scale",
                "LASR": "counter-uas", "DCO": "defense-autonomy"}
    recs = [_rec(t, Disposition.PASSED, layer_of[t]).model_copy(
        update={"driver": "defense-demand-shift", "ratification_date": date(2026, 7, 3)})
        for t in layer_of]
    return freeze_baskets(recs, list(layer_of), driver="defense-demand-shift",
                          freeze_timestamp="2026-07-03T00:00:00", layer_of=layer_of,
                          watchlist=["NEU"], real_tier=["RCAT"],
                          avoid_controls=["LASR", "DCO"])


def test_avoid_controls_freeze_and_must_be_passed() -> None:
    b = _defense_baskets()
    assert b.avoid_controls == ("LASR", "DCO")          # labeled near-miss control cohort frozen
    assert set(b.avoid_controls) <= set(b.passed)        # within the AVOID leg
    # a RATIFIED (or unknown) name cannot be an avoid-control — fail loud
    recs = [_rec("RCAT", Disposition.RATIFIED), _rec("NEU", Disposition.PASSED)]
    with pytest.raises(ValueError, match="avoid_controls must be PASSED"):
        freeze_baskets(recs, ["RCAT", "NEU"], driver="d", freeze_timestamp="2026-07-03T00:00:00",
                       layer_of={"RCAT": "attritable-air", "NEU": "munitions-scale"},
                       avoid_controls=["RCAT"])          # RCAT is RATIFIED, not PASSED


def test_naive_by_layer_is_category_aware_and_driver_agnostic() -> None:
    """The per-category NAIVE split works over defense's PARALLEL categories (not chain layers),
    forward-only from the freeze date; benchmark-adjusted per name."""
    b = _defense_baskets()
    prices = {("IWM", "2026-07-03"): 100.0, ("IWM", "2026-10-01"): 100.0,
              ("RCAT", "2026-07-03"): 100.0, ("RCAT", "2026-10-01"): 130.0,   # +30%
              ("NEU", "2026-07-03"): 100.0, ("NEU", "2026-10-01"): 110.0,     # +10%
              ("LASR", "2026-07-03"): 100.0, ("LASR", "2026-10-01"): 90.0,    # -10%
              ("DCO", "2026-07-03"): 100.0, ("DCO", "2026-10-01"): 105.0}     # +5%
    by = naive_by_layer(b, _price_fn(prices), horizon_days=90, as_of=date(2026, 10, 1))
    got = {lr.layer: (lr.mean_return, lr.n) for lr in by}
    assert set(got) == {"attritable-air", "munitions-scale", "counter-uas", "defense-autonomy"}
    assert got["attritable-air"][0] == pytest.approx(0.30, abs=1e-6)  # RCAT alone
    assert got["counter-uas"][0] == pytest.approx(-0.10, abs=1e-6)    # LASR alone
    assert all(n == 1 for _, n in got.values())


def test_diagnostic_confound_names_the_driver() -> None:
    """The beta-confound is DRIVER-labelled (defense-beta, not AI-datacenter-beta), while keeping
    the 'BETA-CONFOUNDED' marker + the correct committed-tier size in the detail."""
    b = _defense_baskets()
    d = diagnostic_avoid_discipline(b, _price_fn({}), horizon_days=90, as_of=date(2026, 7, 3))
    assert "BETA-CONFOUNDED" in d.confound            # the marker the honesty label depends on
    assert "defense-demand-shift" in d.confound        # driver-labelled, not hardcoded
    assert "AI-datacenter" not in d.confound
    assert "NAIVE-4" in d.detail                       # committed-tier size, not hardcoded 56
