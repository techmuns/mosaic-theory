"""Test 1 — does propagation lag exist? (the moat-existence test, gated behind Test 0).

Test 1 lives or dies on the SHOCK side, so that is what this defines first. A **hub shock** is a
cleanly-dated, idiosyncratic, adverse single-day *surprise* in a shared hub: the hub's
market-adjusted return (hub return minus the IWM small-cap benchmark) on a day falls at or below a
material threshold.

Two design choices carry the validity:
- **Market-adjusted, not raw.** We subtract the market so a broad sell-off — which hits the
  dependent small-caps *directly* via beta — cannot masquerade as propagation. Only hub news counts.
- **Single-day + deduped.** A surprise arrives in one day (a gap), not a drift; we keep only the
  most negative day in a refractory window so one event's fallout isn't counted several times.

Thresholds are face-validity choices (what counts as a *material surprise*), never tuned on the CAR
outcome. The CAR / control-vs-live machinery is added after the shock definition is sanity-checked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from mosaic.schemas.market import PriceBar


@dataclass(frozen=True)
class Shock:
    """One idiosyncratic adverse single-day surprise in a hub."""

    hub: str
    shock_date: date
    abnormal_return: float  # hub return minus IWM on the day (the surprise magnitude)
    hub_return: float
    market_return: float


def _daily_returns(bars: list[PriceBar]) -> list[tuple[date, float]]:
    bs = sorted(bars, key=lambda b: b.bar_date)
    return [(bs[i].bar_date, bs[i].close / bs[i - 1].close - 1.0) for i in range(1, len(bs))]


def detect_shocks(
    hub: str,
    hub_bars: list[PriceBar],
    bench_bars: list[PriceBar],
    *,
    abnormal_threshold: float = -0.06,
    refractory_days: int = 21,
) -> list[Shock]:
    """Idiosyncratic adverse single-day surprises in ``hub`` — market-adjusted vs IWM, deduped.

    ``abnormal_threshold`` (default −6% market-adjusted) is the face-validity bar for "a material
    surprise"; ``refractory_days`` (calendar) collapses an event's fallout to its most-negative day.
    """
    mkt = dict(_daily_returns(bench_bars))
    candidates = [
        Shock(hub, d, r - mkt[d], r, mkt[d])
        for d, r in _daily_returns(hub_bars)
        if d in mkt and (r - mkt[d]) <= abnormal_threshold
    ]
    candidates.sort(key=lambda s: s.abnormal_return)  # most negative first
    kept: list[Shock] = []
    for s in candidates:
        if all(abs((s.shock_date - k.shock_date).days) > refractory_days for k in kept):
            kept.append(s)
    return sorted(kept, key=lambda s: s.shock_date)


def cumulative_abnormal_return(
    dep_bars: list[PriceBar],
    bench_bars: list[PriceBar],
    shock_date: date,
    *,
    lo: int = 1,
    hi: int = 10,
    own_gap: float = 0.20,
) -> float | None:
    """Dependent's cumulative abnormal return over trading days [shock+lo, shock+hi].

    Skips the shock day itself (``lo``≥1) so we measure LAG, not same-day co-movement. ``abnormal``
    = dependent return minus the benchmark (market IWM *or* sector SOXX — the caller picks which,
    and the gap between the two is the finding). Returns None on insufficient data, or when the
    dependent has its own ``own_gap``+ single-day move in the window (its own news, not the hub's).
    """
    dep = [(d, r) for d, r in _daily_returns(dep_bars) if d > shock_date][lo - 1 : hi]
    if len(dep) < hi - lo + 1:
        return None  # not enough post-shock history
    if any(abs(r) >= own_gap for _, r in dep):
        return None  # the dependent's own earnings/news contaminate the window
    bench = dict(_daily_returns(bench_bars))
    abn = [r - bench[d] for d, r in dep if d in bench]
    return sum(abn) if abn else None
