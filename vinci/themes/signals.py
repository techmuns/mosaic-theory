"""§7.1 strength & lifecycle signals — assembled-and-presented INPUTS, never an auto-rank.

For each admissible theme the layer surfaces machine-assessed price-derivable signals so the analyst
need not hand-assess strength/lifecycle — but the **boundary is critical** (`theme_admissibility.md`
§7.1): these are INPUTS THE HUMAN JUDGES, **never an auto-rank that becomes the decision** ("rank by
momentum and auto-bet the top" is the dead-signal / replicable failure, STATE.md §3). So there is
**no composite and no score** here — only the individual signals, each fail-loud (UNKNOWN on
insufficient history, never a partial-window number — the ``vinci/eod/features`` discipline) and
trailing-only (no lookahead past ``reference_date``).
"""

from __future__ import annotations

import statistics
from datetime import date

from vinci.schemas.envelope import DataField, SourceTier
from vinci.themes.schemas import StrengthSignals

_RECENT_DAYS = 21  # ~1 month — the recent window for "fresh-high participation" (breadth expanding)
_MA_DAYS = 50  # the trailing moving-average for over-extension / crowding
_MIN_MEMBERS = 2  # a signal needs at least this many members with coverage, else UNKNOWN


def _unknown(note: str) -> DataField[float]:
    return DataField.unknown(source="EOD", tier=SourceTier.DERIVED, note=note)


def _present(value: float, as_of: date) -> DataField[float]:
    return DataField.present(value, as_of=as_of, source="EOD", tier=SourceTier.DERIVED)


def _window_return(closes: dict[date, float], calendar: list[date]) -> float | None:
    """Total return over the window: first available close → last available close (trailing)."""
    seq = [closes[d] for d in calendar if d in closes and closes[d] > 0]
    if len(seq) < 2:
        return None
    return seq[-1] / seq[0] - 1.0


def compute_strength_signals(
    members: list[str],
    closes_by_name: dict[str, dict[date, float]],
    *,
    market_closes: dict[date, float],
    calendar: list[date],
    reference_date: date,
) -> StrengthSignals:
    """Assemble the §7.1 signals for one theme. Aggregates only members with enough coverage."""
    rets = {
        n: r
        for n in members
        if (r := _window_return(closes_by_name.get(n, {}), calendar)) is not None
    }
    market_ret = _window_return(market_closes, calendar)

    # momentum / relative-strength — cluster medians
    if len(rets) >= _MIN_MEMBERS:
        momentum = _present(statistics.median(rets.values()), reference_date)
        rel = (
            _present(statistics.median(r - market_ret for r in rets.values()), reference_date)
            if market_ret is not None
            else _unknown("no market (IWM) window return")
        )
    else:
        momentum = rel = _unknown(
            f"only {len(rets)} members with a window return (< {_MIN_MEMBERS})"
        )

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
        momentum_median=momentum,
        rel_strength_vs_market=rel,
        breadth_expanding=breadth,
        crowding_overextension=crowding,
    )
