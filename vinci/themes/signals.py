"""§7.1 strength & lifecycle signals — assembled-and-presented INPUTS, never an auto-rank.

For each admissible theme the layer surfaces machine-assessed price-derivable signals so the analyst
need not hand-assess strength/lifecycle — but the **boundary is critical** (`theme_admissibility.md`
§7.1): these are INPUTS THE HUMAN JUDGES, **never an auto-rank that becomes the decision** ("rank by
momentum and auto-bet the top" is the dead-signal / replicable failure, STATE.md §3).

Momentum and relative-strength are presented as a **1/3/6/12mo TRAJECTORY** (a shape the human
reads: accelerating off a trailing low = inflection; decelerating from a high = rolling over) — NOT
a single number, and NEVER collapsed to a slope/composite/rank (that re-destroys the shape and
crosses the dead-signal line). The four horizons map to the four decision timescales the fund
operates on (1mo now / 3mo the quarter / 6mo half-year / 12mo trailing context); a 5th answers no
new question. Each horizon is fail-loud (UNKNOWN on insufficient history — never a partial-window
number, the ``vinci/eod/features`` discipline) and trailing-only (no lookahead past
``reference_date``). Breadth and crowding are recent/current-state measures with no natural
multi-horizon trajectory, so they stay single values. Benchmark stays IWM (sub-$10B-relevant; the
Finding-2 benchmark-per-universe split is a separate Stage-2 confirmation-trigger concern, not
changed here).
"""

from __future__ import annotations

import statistics
from datetime import date

from vinci.schemas.envelope import DataField, SourceTier
from vinci.themes.schemas import StrengthSignals, Trajectory

# One horizon per distinct decision timescale (trading days): 1mo / 3mo / 6mo / 12mo.
_HORIZONS: tuple[tuple[str, int], ...] = (("1mo", 21), ("3mo", 63), ("6mo", 126), ("12mo", 252))
_COV_TOL_FRAC = 0.10  # a horizon needs coverage within this fraction of the window at each end
_RECENT_DAYS = 21  # ~1 month — the recent window for "fresh-high participation" (breadth expanding)
_MA_DAYS = 50  # the trailing moving-average for over-extension / crowding
_MIN_MEMBERS = 2  # a signal needs at least this many members with coverage, else UNKNOWN


def _unknown(note: str) -> DataField[float]:
    return DataField.unknown(source="EOD", tier=SourceTier.DERIVED, note=note)


def _present(value: float, as_of: date) -> DataField[float]:
    return DataField.present(value, as_of=as_of, source="EOD", tier=SourceTier.DERIVED)


def _horizon_return(closes: dict[date, float], calendar: list[date], n_days: int) -> float | None:
    """Trailing total return over the last ``n_days`` of the calendar (first→last close in window).

    UNKNOWN (None) when coverage does not span the horizon — a name whose closes do not reach near
    the START (or END) of the window yields None for that horizon, so a recent IPO reports real
    1mo/3mo numbers but UNKNOWN for 6mo/12mo, never a partial-window fabrication.
    """
    window = calendar if n_days >= len(calendar) else calendar[-n_days:]
    idx = [i for i, d in enumerate(window) if d in closes and closes[d] > 0]
    if len(idx) < 2:
        return None
    tol = max(3, round(_COV_TOL_FRAC * len(window)))
    if idx[0] > tol or (len(window) - 1 - idx[-1]) > tol:
        return None  # coverage doesn't span the horizon → fail-loud UNKNOWN
    return closes[window[idx[-1]]] / closes[window[idx[0]]] - 1.0


def _momentum_trajectory(
    members: list[str], closes_by_name: dict[str, dict[date, float]], calendar: list[date],
    reference_date: date,
) -> Trajectory:
    """Median member trailing return at each horizon — a shape, never collapsed to one number."""
    f: dict[str, DataField[float]] = {}
    for label, n in _HORIZONS:
        rets = [
            r for m in members
            if (r := _horizon_return(closes_by_name.get(m, {}), calendar, n)) is not None
        ]
        f[label] = (
            _present(statistics.median(rets), reference_date)
            if len(rets) >= _MIN_MEMBERS
            else _unknown(f"only {len(rets)} members with a {label} return")
        )
    return Trajectory(h1mo=f["1mo"], h3mo=f["3mo"], h6mo=f["6mo"], h12mo=f["12mo"])


def _rel_strength_trajectory(
    members: list[str], closes_by_name: dict[str, dict[date, float]],
    market_closes: dict[date, float], calendar: list[date], reference_date: date,
) -> Trajectory:
    """Median(member − IWM) trailing return at each horizon — same formula, four windows."""
    f: dict[str, DataField[float]] = {}
    for label, n in _HORIZONS:
        market_ret = _horizon_return(market_closes, calendar, n)
        rets = [
            r for m in members
            if (r := _horizon_return(closes_by_name.get(m, {}), calendar, n)) is not None
        ]
        if len(rets) >= _MIN_MEMBERS and market_ret is not None:
            f[label] = _present(statistics.median(r - market_ret for r in rets), reference_date)
        else:
            why = (
                "no market (IWM) window return" if market_ret is None
                else f"only {len(rets)} members with a {label} return"
            )
            f[label] = _unknown(why)
    return Trajectory(h1mo=f["1mo"], h3mo=f["3mo"], h6mo=f["6mo"], h12mo=f["12mo"])


def compute_strength_signals(
    members: list[str],
    closes_by_name: dict[str, dict[date, float]],
    *,
    market_closes: dict[date, float],
    calendar: list[date],
    reference_date: date,
) -> StrengthSignals:
    """Assemble the §7.1 signals for one theme. Aggregates only members with enough coverage."""
    momentum = _momentum_trajectory(members, closes_by_name, calendar, reference_date)
    rel = _rel_strength_trajectory(members, closes_by_name, market_closes, calendar, reference_date)

    # breadth expanding — share of members at a FRESH window-high in the last ~month (participation)
    fresh: list[float] = []
    for n in members:
        seq = [closes_by_name[n][d] for d in calendar if d in closes_by_name.get(n, {})]
        if len(seq) >= _RECENT_DAYS:
            hi = max(seq)
            fresh.append(1.0 if max(seq[-_RECENT_DAYS:]) >= hi else 0.0)
    breadth = (
        _present(statistics.fmean(fresh), reference_date)
        if fresh
        else _unknown("no coverage for highs")
    )

    # crowding / over-extension — median distance of last close above its trailing moving average
    overext: list[float] = []
    for n in members:
        seq = [closes_by_name[n][d] for d in calendar if d in closes_by_name.get(n, {})]
        if len(seq) >= _MA_DAYS:
            ma = statistics.fmean(seq[-_MA_DAYS:])
            if ma > 0:
                overext.append(seq[-1] / ma - 1.0)
    crowding = (
        _present(statistics.median(overext), reference_date)
        if len(overext) >= _MIN_MEMBERS
        else _unknown(f"only {len(overext)} members with {_MA_DAYS}d history")
    )

    return StrengthSignals(
        momentum=momentum,
        rel_strength_vs_market=rel,
        breadth_expanding=breadth,
        crowding_overextension=crowding,
    )
