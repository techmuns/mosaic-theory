"""Priced-check price-axis math — network-free, stubbed bars.

Pins the validated method ported into `vinci/themes/priced_check.py`: basket-median / excess math,
the `< MIN_PRICED → UNDEFINED` rule (never a fabricated 0), the mechanical tag at its ±20%
boundaries, stale-member exclusion, and residual dispersion on a synthetic series.
"""
from __future__ import annotations

from datetime import date, timedelta

from vinci.themes import priced_check as pc


def _iso(d: date) -> str:
    return d.isoformat()


def test_median_and_excess_math() -> None:
    """12mo basket median = median of member returns; excess = median − benchmark return."""
    latest = date(2026, 1, 15)
    a12 = pc.months_ago(latest, 12)  # 2025-01-15
    lo, hi = _iso(a12), _iso(latest)
    bars = {
        "A": {lo: 100.0, hi: 150.0},   # +50%
        "B": {lo: 100.0, hi: 130.0},   # +30% (median)
        "C": {lo: 100.0, hi: 110.0},   # +10%
        "SPY": {lo: 100.0, hi: 120.0},  # +20%
        "IWM": {lo: 100.0, hi: 115.0},  # +15%
    }
    ctx = pc.PriceCtx(bars, [lo, hi], latest)
    pr = pc.priced_read(ctx, ["A", "B", "C"])
    assert pr[12]["n"] == 3
    assert abs(pr[12]["med"] - 0.30) < 1e-9
    assert abs(pr[12]["ex_spy"] - 0.10) < 1e-9   # 0.30 − 0.20
    assert abs(pr[12]["ex_iwm"] - 0.15) < 1e-9   # 0.30 − 0.15


def test_under_min_priced_is_undefined_not_zero() -> None:
    """Fewer than MIN_PRICED priced members in a window → UNDEFINED-with-reason, never a fake 0."""
    latest = date(2026, 1, 15)
    a12 = pc.months_ago(latest, 12)
    lo, hi = _iso(a12), _iso(latest)
    bars = {
        "A": {lo: 100.0, hi: 150.0},   # priced
        "B": {lo: 100.0, hi: 130.0},   # priced
        "C": {lo: 100.0},              # no current close → NOT priced
        "SPY": {lo: 100.0, hi: 120.0}, "IWM": {lo: 100.0, hi: 115.0},
    }
    ctx = pc.PriceCtx(bars, [lo, hi], latest)
    pr = pc.priced_read(ctx, ["A", "B", "C"])
    assert "undef" in pr[12] and pr[12]["n"] == 2
    assert "med" not in pr[12]                       # no fabricated median
    assert pc.tag(pr).startswith("UNDEFINED")        # tag defers, never invents


def test_tag_rule_at_boundaries() -> None:
    """Mechanical tag: both excess > +20% → PRICED; both <= +20% → NOT-PRICED; else MIXED.
    +20% itself is NOT > +20% (boundary is <=)."""
    def pr(es: float, ei: float) -> dict[int, dict[str, object]]:
        return {12: {"ex_spy": es, "ex_iwm": ei, "med": 0.0, "n": 5}}
    assert pc.tag(pr(0.21, 0.21)) == "PRICED"
    assert pc.tag(pr(0.20, 0.20)) == "NOT-PRICED"     # exactly +20% both → NOT-PRICED
    assert pc.tag(pr(0.201, 0.20)) == "MIXED"         # one just over, one at boundary
    assert pc.tag(pr(0.25, 0.15)) == "MIXED"
    assert pc.tag(pr(-0.30, -0.40)) == "NOT-PRICED"
    assert pc.tag({12: {"undef": "only 2 priced members (<3)", "n": 2}}).startswith("UNDEFINED")
    assert pc.tag({12: {"ex_spy": None, "ex_iwm": 0.3, "med": 0.0, "n": 5}}).startswith("UNDEFINED")


def test_stale_member_excluded_from_now() -> None:
    """A member whose last bar is older than RECENCY_DAYS gets no 'now' → dropped from the priced
    set (never a stale return); the median is over the fresh members only."""
    latest = date(2026, 1, 15)
    a12 = pc.months_ago(latest, 12)
    lo, hi = _iso(a12), _iso(latest)
    stale_iso = _iso(latest - timedelta(days=14))  # > RECENCY_DAYS(7) before latest
    bars = {
        "A": {lo: 100.0, hi: 150.0}, "B": {lo: 100.0, hi: 130.0}, "C": {lo: 100.0, hi: 110.0},
        "D": {lo: 100.0, stale_iso: 400.0},  # last bar 14d old → stale/delisted
        "SPY": {lo: 100.0, hi: 120.0}, "IWM": {lo: 100.0, hi: 115.0},
    }
    ctx = pc.PriceCtx(bars, [lo, stale_iso, hi], latest)
    assert ctx.close_now("D") is None                 # stale → no 'now'
    assert ctx.close_now("A") == 150.0                # fresh → current close
    pr = pc.priced_read(ctx, ["A", "B", "C", "D"])
    assert pr[12]["n"] == 3                            # D excluded, not counted
    assert abs(pr[12]["med"] - 0.30) < 1e-9           # median of A/B/C only (D's +300% ignored)


def _weekdays_ending(latest: date, n: int) -> list[str]:
    out: list[str] = []
    d = latest
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return sorted(out)


def _series(days: list[str], rets: list[float], start: float = 100.0) -> dict[str, float]:
    closes = {days[0]: start}
    p = start
    for k in range(1, len(days)):
        p *= 1 + rets[k]
        closes[days[k]] = p
    return closes


def test_dispersion_identical_residuals_is_unit_corr() -> None:
    """Three members that all move as IWM + the SAME idiosyncratic shock have IDENTICAL market-model
    residuals → every pairwise corr = 1.0 → median 1.0 (n_members 3, n_pairs 3)."""
    latest = date(2026, 6, 30)
    days = _weekdays_ending(latest, 30)               # 30 obs, inside the 6mo window
    n = len(days)
    iwm_r = [0.0] + [0.012 if k % 2 else -0.009 for k in range(1, n)]
    shock = [0.0] + [0.006 if k % 3 == 0 else -0.004 for k in range(1, n)]
    member_r = [iwm_r[k] + shock[k] for k in range(n)]  # beta≈1 + a common non-market shock
    bars = {
        "IWM": _series(days, iwm_r),
        "A": _series(days, member_r), "B": _series(days, member_r), "C": _series(days, member_r),
    }
    ctx = pc.PriceCtx(bars, days, latest)
    d = pc.dispersion(ctx, ["A", "B", "C"])
    assert d["n_members"] == 3 and d["n_pairs"] == 3
    assert abs(d["median"] - 1.0) < 1e-6


def test_dispersion_window_too_short_is_undefined() -> None:
    latest = date(2026, 6, 30)
    days = _weekdays_ending(latest, 5)                # < DISP_MIN_OBS + 1
    bars = {"IWM": _series(days, [0.0] * len(days)), "A": _series(days, [0.0] * len(days))}
    assert pc.dispersion(pc.PriceCtx(bars, days, latest), ["A"])["undef"] == "window too short"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
