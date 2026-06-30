"""Regression tests for Stage 2 — Components B (theme-type signals) + C (megacap confirmation).

Offline / synthetic. Pins the load-bearing behaviour: leader designation needs BOTH SIC-match AND
co-movement; the price-pattern discriminates leader-first vs synchronous; the defer state fires on
ambiguity; the forward baseline; and the confirmation grid + its dual-benchmark (Finding-2) spread.
"""

from __future__ import annotations

from datetime import date, timedelta
from random import Random

from vinci.themes.classify import assemble_type_signals, compute_price_pattern, historical_analog
from vinci.themes.confirmation import confirmation_signal, forward_baseline
from vinci.themes.leaders import MegaCap, MegaContext, designate_leaders
from vinci.themes.schemas import (
    ConfirmationSignal,
    LeaderSet,
    MegaLeader,
    ThemeStage2,
    TypeSignals,
)


def _cal(n: int) -> list[date]:
    base = date(2025, 1, 1)
    return [base + timedelta(days=i) for i in range(n)]


def _path(cal: list[date], anchors: dict[int, float]) -> dict[date, float]:
    """A close series hitting ``anchors`` (index→price) with linear interpolation between them."""
    idx = sorted(anchors)
    out: dict[date, float] = {}
    for i, d in enumerate(cal):
        lo = max(a for a in idx if a <= i)
        hi = min(a for a in idx if a >= i)
        if lo == hi:
            out[d] = anchors[lo]
        else:
            out[d] = anchors[lo] + (anchors[hi] - anchors[lo]) * (i - lo) / (hi - lo)
    return out


def _leader(ticker: str) -> MegaLeader:
    return MegaLeader(ticker=ticker, name=ticker, cik="1", market_cap=2e10, sic="1531",
                      sector="Industrials", residual_corr_to_cluster=0.4, source_ref="x")


# --------------------------------------------------------------------------------------------------
# SUB-STEP 0 — leader designation: BOTH SIC-match AND co-movement
# --------------------------------------------------------------------------------------------------
def test_designate_leaders_needs_sic_and_comovement() -> None:
    cal = _cal(120)
    rng = Random(11)
    theme = {d: rng.gauss(0, 0.02) for d in cal}
    cluster = {f"C{i}": {d: theme[d] + rng.gauss(0, 0.008) for d in cal} for i in range(4)}
    mega_resid = {
        "M1": {d: theme[d] + rng.gauss(0, 0.01) for d in cal},  # SIC-match + co-moves → leader
        "M2": {d: rng.gauss(0, 0.02) for d in cal},  # SIC-match but independent → excluded
        "M3": {d: theme[d] + rng.gauss(0, 0.01) for d in cal},  # co-moves but wrong SIC → excluded
    }
    mega = [
        MegaCap("M1", "M1", "1", "Mega1", 2e10, "1531", "Industrials"),
        MegaCap("M2", "M2", "2", "Mega2", 2e10, "1531", "Industrials"),
        MegaCap("M3", "M3", "3", "Mega3", 2e10, "9999", "Other"),
    ]
    ctx = MegaContext(mega=mega, residuals=mega_resid, closes={},
                      by_id={m.internal_id: m for m in mega})
    ls = designate_leaders(list(cluster), cluster, ctx, {"1531"}, cal)
    assert {x.ticker for x in ls.leaders} == {"M1"}
    assert ls.leaders[0].residual_corr_to_cluster > 0.5  # the co-movement evidence is surfaced


# --------------------------------------------------------------------------------------------------
# Component B — price-pattern discriminates leader-first (emergence) vs synchronous (cyclical)
# --------------------------------------------------------------------------------------------------
def test_price_pattern_leader_first_vs_synchronous() -> None:
    cal = _cal(252)
    n = 252
    # leader-first: leaders strong across long horizons (+60%); members weak long (−10%) but turning
    # up short (+15% 1mo). A single mega-cap leader is valid (e.g. uranium = CCJ).
    leader = _path(cal, {0: 100, n - 126: 130, n - 63: 145, n - 21: 152, n - 1: 160})
    member = _path(cal, {0: 100, n - 126: 84.9, n - 63: 81.8, n - 21: 78.3, n - 1: 90})
    pp = compute_price_pattern({"L": leader}, {"m1": member, "m2": member}, calendar=cal,
                               reference_date=cal[-1])
    assert pp.read.startswith("LEADER-FIRST")

    # synchronous: leaders and members share the same path → no lead-lag
    same = _path(cal, {0: 100, n - 1: 120})
    pp2 = compute_price_pattern({"L": same}, {"m1": same, "m2": same}, calendar=cal,
                                reference_date=cal[-1])
    assert pp2.read.startswith("SYNCHRONOUS")


def test_price_pattern_no_leaders() -> None:
    cal = _cal(120)
    member = _path(cal, {0: 100, 119: 110})
    pp = compute_price_pattern({}, {"m1": member, "m2": member}, calendar=cal,
                               reference_date=cal[-1])
    assert "no co-moving mega-cap leaders" in pp.read


# --------------------------------------------------------------------------------------------------
# Component B — the DEFER state (do not force a type when the signals are ambiguous)
# --------------------------------------------------------------------------------------------------
def test_defer_state_on_ambiguous_signals() -> None:
    cal = _cal(252)
    n = 252
    # a mixed/choppy shape: leaders ≈ members at the LONG horizons (small gap → not leader-first)
    # but diverging at the SHORT horizons (→ not synchronous) + no analog (llm None) → DEFER
    leader = _path(cal, {0: 100, n - 126: 101.85, n - 63: 115.79, n - 21: 91.67, n - 1: 110})
    member = _path(cal, {0: 100, n - 126: 101.89, n - 63: 98.18, n - 21: 127.06, n - 1: 108})
    pp = compute_price_pattern({"L": leader}, {"m1": member, "m2": member}, calendar=cal,
                               reference_date=cal[-1])
    analog = historical_analog("note", ["L"], ["m1"], llm=None)  # unavailable
    ts = assemble_type_signals(pp, vol_strip_survived=True, vol_strip_note="x", analog=analog)
    assert ts.ambiguous
    assert "watch, do not fire" in ts.defer_note


# --------------------------------------------------------------------------------------------------
# Component C — forward baseline + the confirmation grid (Part-7 thresholds × Finding-2 benchmarks)
# --------------------------------------------------------------------------------------------------
def test_forward_baseline_is_window_start() -> None:
    cal = _cal(252)
    base, why = forward_baseline(cal)
    assert base == cal[0]
    assert "detection window" in why


def test_confirmation_grid_and_dual_benchmark_spread() -> None:
    cal = _cal(120)
    leaders = [_leader("L1"), _leader("L2")]
    closes = {
        "L1": _path(cal, {0: 100, 119: 145}),  # +45%
        "L2": _path(cal, {0: 100, 119: 125}),  # +25%  → median leader +35%
    }
    iwm = _path(cal, {0: 100, 119: 125})  # +25%
    spy = _path(cal, {0: 100, 119: 110})  # +10%
    c = confirmation_signal(leaders, closes, iwm_closes=iwm, spy_closes=spy, calendar=cal)
    assert c.n_leaders == 2
    cells = {cell.basis: cell for cell in c.grid}
    assert abs(cells["absolute"].value - 0.35) < 1e-6
    assert cells["absolute"].clears["+20%"] and cells["absolute"].clears["+30%"]
    assert not cells["absolute"].clears["+50%"]
    assert abs(cells["vs IWM"].value - 0.10) < 1e-6  # +35% − IWM +25%
    assert abs(cells["vs SPY"].value - 0.25) < 1e-6  # +35% − SPY +10%
    # Finding-2: benchmarking mega-caps against IWM costs (SPY − IWM) = +15pp vs the broad benchmark
    assert abs((cells["vs SPY"].value - cells["vs IWM"].value) - 0.15) < 1e-6
    # and that materially moves the call at +20%: clears vs SPY, NOT vs IWM
    assert cells["vs SPY"].clears["+20%"] and not cells["vs IWM"].clears["+20%"]


def test_confirmation_no_leaders_is_empty() -> None:
    cal = _cal(120)
    c = confirmation_signal([], {}, iwm_closes={}, spy_closes={}, calendar=cal)
    assert c.n_leaders == 0 and c.grid == []


# --------------------------------------------------------------------------------------------------
# Guard — Stage-2 records carry no auto-classification / type-verdict / autonomous-trigger field
# --------------------------------------------------------------------------------------------------
_FORBIDDEN = ("verdict", "recommendation", "buy", "sell", "avoid", "theme_type", "type_verdict",
              "auto", "score", "rank", "priority", "trigger", "decision")


def _fields(model: type) -> set[str]:
    names: set[str] = set()
    fields = getattr(model, "model_fields", None)
    if not fields:
        return names
    for fname, info in fields.items():
        names.add(fname)
        ann = info.annotation
        for sub in (ann, *getattr(ann, "__args__", ())):
            if isinstance(sub, type) and hasattr(sub, "model_fields"):
                names |= _fields(sub)
    return names


def test_stage2_schema_cannot_conclude() -> None:
    names = (_fields(ThemeStage2) | _fields(TypeSignals) | _fields(ConfirmationSignal)
             | _fields(LeaderSet))
    assert names
    for n in names:
        for tok in _FORBIDDEN:
            assert tok not in n.lower(), f"field {n!r} smuggles a conclusion ({tok})"
