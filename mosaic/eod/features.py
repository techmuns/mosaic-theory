"""Screen-2 price features, derived from a security's EOD bar history.

Pure functions over a ``list[PriceBar]`` so the math is unit-testable without the network. Each
feature is enveloped: insufficient history → **UNKNOWN** (never a misleading partial-window value —
e.g. a "52-week high" computed from 3 months would understate it, so we defer instead).

What is computable from price alone (filled here): last, 52w high/low, drawdown-from-high,
distance-from-low, trailing returns (3/6/12m), 90D ADV (shares & USD), volume spike. What needs
external inputs is left UNKNOWN for step 5: ``rel_ret_vs_sector`` (SIC peers) and ``turnover``
(needs market cap, unless passed in).
"""

from __future__ import annotations

from datetime import date, timedelta

from mosaic.schemas.data_record import PriceFeatures
from mosaic.schemas.envelope import DataField, SourceTier
from mosaic.schemas.market import PriceBar

# Calendar lookbacks. 52w features need ~a full year of history to be meaningful.
_YEAR_DAYS = 365
_MIN_52W_SPAN = 330  # require at least this much history before reporting 52w-based features
_RET_LOOKBACK = {"3m": 91, "6m": 182, "12m": 365}
_ADV_WINDOW = 90
_ADV_MIN_BARS = 20  # need at least this many bars in the 90d window for a meaningful ADV


def _eod(value: float, as_of: date) -> DataField[float]:
    return DataField.present(value, as_of=as_of, source="EOD", tier=SourceTier.EOD)


def _derived(value: float, as_of: date) -> DataField[float]:
    return DataField.present(value, as_of=as_of, source="EOD", tier=SourceTier.DERIVED)


def _unknown(note: str) -> DataField[float]:
    return DataField.unknown(source="EOD", tier=SourceTier.DERIVED, note=note)


def _close_on_or_before(bars: list[PriceBar], target: date) -> float | None:
    """Latest close at or before ``target`` (bars sorted ascending). None if none qualify."""
    chosen: float | None = None
    for b in bars:
        if b.bar_date <= target:
            chosen = b.close
        else:
            break
    return chosen


def compute_price_features(
    bars: list[PriceBar],
    *,
    reference_date: date,
    staleness_days: int,
    market_cap: float | None = None,
) -> PriceFeatures:
    """Compute the Screen-2 price features from a bar history (any order; sorted internally)."""
    bars = sorted(bars, key=lambda b: b.bar_date)
    if not bars:
        u = _unknown("no price bars")
        return PriceFeatures(
            last=u, high_52w=u, low_52w=u, drawdown_from_high=u, dist_from_low=u,
            ret_3m=u, ret_6m=u, ret_12m=u, rel_ret_vs_sector=u,
            adv_90d_shares=u, adv_90d_usd=u, turnover=u, volume_spike=u,
        )

    latest = bars[-1]
    as_of = latest.bar_date
    age = (reference_date - latest.bar_date).days
    if age > staleness_days:
        last = DataField.stale(
            latest.close, as_of=as_of, source="EOD", tier=SourceTier.EOD,
            note=f"{age}d old (> {staleness_days}d)",
        )
    else:
        last = _eod(latest.close, as_of)

    span_days = (latest.bar_date - bars[0].bar_date).days
    have_year = span_days >= _MIN_52W_SPAN

    # 52-week high/low + drawdown/distance (only if we actually have ~a year of history)
    if have_year:
        window = [b for b in bars if b.bar_date >= reference_date - timedelta(days=_YEAR_DAYS)]
        hi = max(b.high for b in window)
        lo = min(b.low for b in window)
        high_52w = _eod(hi, as_of)
        low_52w = _eod(lo, as_of)
        drawdown = _derived(latest.close / hi - 1.0, as_of)
        dist_low = _derived(latest.close / lo - 1.0, as_of)
    else:
        note = f"only {span_days}d history (< {_MIN_52W_SPAN}d)"
        high_52w = low_52w = drawdown = dist_low = _unknown(note)

    # trailing returns
    rets: dict[str, DataField[float]] = {}
    for label, lookback in _RET_LOOKBACK.items():
        then = _close_on_or_before(bars, reference_date - timedelta(days=lookback))
        if then and then > 0 and span_days >= lookback - 7:
            rets[label] = _derived(latest.close / then - 1.0, as_of)
        else:
            rets[label] = _unknown(f"no close ~{lookback}d ago")

    # 90D ADV + volume spike
    adv_window = [b for b in bars if b.bar_date >= reference_date - timedelta(days=_ADV_WINDOW)]
    if len(adv_window) >= _ADV_MIN_BARS:
        adv_shares_v = sum(b.volume for b in adv_window) / len(adv_window)
        adv_usd_v = sum(b.close * b.volume for b in adv_window) / len(adv_window)
        adv_shares = _derived(adv_shares_v, as_of)
        adv_usd = _derived(adv_usd_v, as_of)
        spike = (
            _derived(latest.volume / adv_shares_v, as_of)
            if adv_shares_v > 0
            else _unknown("zero ADV")
        )
        turnover = (
            _derived(adv_usd_v / market_cap, as_of)
            if market_cap and market_cap > 0
            else DataField.unknown(source="DERIVED", tier=SourceTier.DERIVED, note="no market cap")
        )
    else:
        note = f"only {len(adv_window)} bars in 90d (< {_ADV_MIN_BARS})"
        adv_shares = adv_usd = spike = turnover = _unknown(note)

    return PriceFeatures(
        last=last,
        high_52w=high_52w,
        low_52w=low_52w,
        drawdown_from_high=drawdown,
        dist_from_low=dist_low,
        ret_3m=rets["3m"],
        ret_6m=rets["6m"],
        ret_12m=rets["12m"],
        rel_ret_vs_sector=DataField.unknown(
            source="EOD", tier=SourceTier.DERIVED, note="needs SIC peers (step 5)"
        ),
        adv_90d_shares=adv_shares,
        adv_90d_usd=adv_usd,
        turnover=turnover,
        volume_spike=spike,
    )


def relative_return(
    name_bars: list[PriceBar],
    bench_bars: list[PriceBar],
    *,
    reference_date: date,
    lookback_days: int,
) -> DataField[float]:
    """Name return minus benchmark return over a window (the G2 idiosyncratic input).

    UNKNOWN if either series lacks coverage over the window (graceful, never a corrupted number).
    """
    name_bars = sorted(name_bars, key=lambda b: b.bar_date)
    bench_bars = sorted(bench_bars, key=lambda b: b.bar_date)
    start = reference_date - timedelta(days=lookback_days)

    def ret(bars: list[PriceBar]) -> float | None:
        if not bars:
            return None
        then = _close_on_or_before(bars, start)
        now = _close_on_or_before(bars, reference_date)
        if then is None or now is None or then <= 0:
            return None
        return now / then - 1.0

    name_ret, bench_ret = ret(name_bars), ret(bench_bars)
    if name_ret is None or bench_ret is None:
        return DataField.unknown(
            source="EOD", tier=SourceTier.DERIVED, note="insufficient coverage over window"
        )
    return DataField.present(
        name_ret - bench_ret, as_of=reference_date, source="EOD", tier=SourceTier.DERIVED
    )
