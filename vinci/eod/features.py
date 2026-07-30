"""Screen-2 price features, derived from a security's EOD bar history.

Pure functions over a ``list[PriceBar]`` so the math is unit-testable without the network. Each
feature is enveloped: insufficient history → **UNKNOWN** (never a misleading partial-window value —
e.g. a "52-week high" computed from 3 months would understate it, so we defer instead).

What is computable from price alone (filled here): last, 52w high/low, drawdown-from-high,
distance-from-low, trailing returns (3/6/12m), 90D ADV (shares & USD), volume spike. What needs
external inputs is left UNKNOWN here and filled by the assembler: ``rel_ret_vs_market`` (set vs the
IWM benchmark in :func:`vinci.screens.assemble.build_price_record`) and ``turnover`` (needs market
cap, unless passed in).
"""

from __future__ import annotations

from datetime import date, timedelta

from vinci.schemas.data_record import PriceFeatures
from vinci.schemas.envelope import DataField, SourceTier
from vinci.schemas.market import PriceBar

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
            ret_3m=u, ret_6m=u, ret_12m=u, rel_ret_vs_market=u,
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
        rel_ret_vs_market=DataField.unknown(
            source="EOD", tier=SourceTier.DERIVED, note="set vs IWM benchmark in assemble"
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

    **BOTH LEGS END ON THE COMMON LAST BAR** (2026-07-30). The first cut ran each series to its own
    latest bar via ``_close_on_or_before(bars, reference_date)``, so a stale benchmark contributed a
    return that stopped early while every name's ran to the reference date — an ASYMMETRIC
    comparison rather than merely a stale one, and the difference decides the failure mode:

      * asymmetric → a DIRECTIONAL bias whose sign is set by whichever way the market moved in the
        missing days, mis-ranking every name the same way;
      * common end → a SHORTER window, measured honestly on both sides.

    MEASURED, not hypothetical. The 2026-07-27 screen ran with IWM's frontier at 07-21 while
    names ran to 07-24 or later. The market fell 1.22% in that gap, so ``bench_ret`` was
    overstated, every name's ``rel`` was understated by ~1.22pp, and **four of 318 candidates
    passed G2 only because of it** — CABA, GO, NOMD, TROX. None reached a dossier; NOMD ranked
    227 of 275. A market DECLINE admits names that fell with it, the permissive direction.

    THE WINDOW IS STAMPED. ``as_of`` is the effective END — the common last bar — not the
    reference date. The old value claimed ``reference_date`` even when the data stopped days
    earlier: the stamp-names-a-different-object class, in the field that feeds a gate. ``note``
    carries the window and each side's frontier so a later recompute can reconstruct what the
    screen actually saw. The 07-27 bound was possible only because the committed ``rel`` values
    survived; the store-side evidence had already been refreshed away.

    UNKNOWN if either series lacks coverage over the window (graceful, never a corrupted number).
    """
    name_bars = sorted(name_bars, key=lambda b: b.bar_date)
    bench_bars = sorted(bench_bars, key=lambda b: b.bar_date)
    start = reference_date - timedelta(days=lookback_days)

    def frontier(bars: list[PriceBar]) -> date | None:
        """This side's own end — its latest bar at or before the reference date."""
        usable = [b.bar_date for b in bars if b.bar_date <= reference_date]
        return max(usable) if usable else None

    n_end, b_end = frontier(name_bars), frontier(bench_bars)
    if n_end is None or b_end is None:
        return DataField.unknown(
            source="EOD", tier=SourceTier.DERIVED, note="insufficient coverage over window"
        )
    end = min(n_end, b_end)  # THE COMMON LAST BAR — never each side's own

    def ret(bars: list[PriceBar]) -> float | None:
        then = _close_on_or_before(bars, start)
        now = _close_on_or_before(bars, end)
        if then is None or now is None or then <= 0:
            return None
        return now / then - 1.0

    name_ret, bench_ret = ret(name_bars), ret(bench_bars)
    if name_ret is None or bench_ret is None:
        return DataField.unknown(
            source="EOD", tier=SourceTier.DERIVED, note="insufficient coverage over window"
        )
    lag = (reference_date - end).days
    return DataField.present(
        name_ret - bench_ret, as_of=end, source="EOD", tier=SourceTier.DERIVED,
        note=(f"window {start.isoformat()}→{end.isoformat()} (common last bar; name frontier "
              f"{n_end.isoformat()}, benchmark frontier {b_end.isoformat()}"
              + (f"; {lag}d short of the {reference_date.isoformat()} reference)"
                 if lag else ")")),
    )
