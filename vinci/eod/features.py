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
YEAR_DAYS = 365  # the 52-week window G1's high/low is drawn over
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


#: How far before the window start an anchor bar may sit before the comparison is refused.
#:
#: DERIVED FROM THE MARKET CALENDAR, read off the data rather than encoded — the same trick as
#: ``MAX_STORE_LAG_DAYS``. **The relevant gap is MARKET-WIDE, not store-wide** (review correction):
#: the store's 5–9d tail is per-name HALTS, and a halted name is exactly what this bound exists to
#: refuse, so deriving from it would have set the bound by the population it screens out. Measured
#: on IWM and MDY — identical, which is what makes them the calendar — consecutive-bar gaps are
#: 1d ×994, 2d ×14, 3d ×228, 4d ×37 and **nothing beyond 4**. The bound is 10, leaving six days of
#: margin over the worst holiday weekend the market actually produces.
#:
#: THE POPULATION CONFIRMS IT IS NOWHERE NEAR THE BOUNDARY. Of the 596 names that reached G2 on the
#: 2026-07-29 run, **593 anchor exactly ON the window start** and the next three sit at 108d, 116d
#: and 1,472d. Nothing occupies 1–107, so any value in that range yields the same outcomes today;
#: the constant is set from market structure so that it also refuses a smaller abnormal gap, rather
#: than being fitted to the three names that happen to fail it.
MAX_ANCHOR_LAG_DAYS = 10


def window_facts(bars: list[PriceBar], *, start: date, end: date,
                 anchor_before: bool = True) -> tuple[int, int] | None:
    """(span_days, bar_count) for the window a return over ``[start, end]`` ACTUALLY covered.

    ONE IMPLEMENTATION, called by both the field that reports the number and the retention row that
    records it (review finding — the first cut computed this twice, in `features` and in
    `screens.run`. They agreed, but two computations of one quantity is the twin-drift class this
    repo keeps finding, and the risk was never string-parsing, it was duplication).

    ``anchor_before=True`` (the default) anchors on the bar the return STARTED from — the latest at
    or before ``start`` — so a hole in the series shows up as a span wider than the target instead
    of being invisible. That is the right anchor for a RETURN, which needs a start price.

    ``anchor_before=False`` measures the window ``[start, end]`` itself. That is the right anchor
    for an EXTREMUM — a 52-week high is a max over the bars INSIDE the window, and there is no
    start price to reach back for. The flag lives here rather than in a second function because one
    quantity deserves one implementation (#294), and the two anchors differ by exactly one bar.
    """
    if anchor_before:
        prior = [b for b in bars if b.bar_date <= start]
        if not prior:
            return None
        a = prior[-1].bar_date
    else:
        inside = [b for b in bars if start <= b.bar_date <= end]
        if not inside:
            return None
        a = inside[0].bar_date
    return (end - a).days, sum(1 for b in bars if a <= b.bar_date <= end)


def _bar_on_or_before(bars: list[PriceBar], target: date) -> PriceBar | None:
    """Latest BAR at or before ``target`` (bars sorted ascending). None if none qualify.

    Returns the bar, not the close, because the caller needs its DATE: a close alone cannot say how
    far back the series had to reach to find it.
    """
    chosen: PriceBar | None = None
    for b in bars:
        if b.bar_date <= target:
            chosen = b
        else:
            break
    return chosen


def _close_on_or_before(bars: list[PriceBar], target: date) -> float | None:
    """Latest close at or before ``target`` (bars sorted ascending). None if none qualify."""
    b = _bar_on_or_before(bars, target)
    return b.close if b else None


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
        w_start = reference_date - timedelta(days=YEAR_DAYS)
        window = [b for b in bars if b.bar_date >= w_start]
        hi = max(b.high for b in window)
        lo = min(b.low for b in window)
        # THE STAMP NAMES THE LAST BAR; THE VALUE IS A MAX OVER 365 DAYS (2026-07-31). `as_of` is
        # correct as "known at" but says nothing about what the extremum covers, so a 52-week high
        # drawn from a truncated series read exactly like one drawn from a full year — INHD's
        # covers ~10.5 months. The window is now labelled beside the value; a stamp belongs to what
        # it names.
        wf = window_facts(bars, start=w_start, end=as_of, anchor_before=False)
        win = (f"52-week window {w_start.isoformat()}→{as_of.isoformat()}: spans {wf[0]}d over "
               f"{wf[1]} bars" if wf else "52-week window not resolvable")
        high_52w = _eod(hi, as_of).model_copy(update={"note": win})
        low_52w = _eod(lo, as_of).model_copy(update={"note": win})
        # THE RATIO FIELDS REACH BACK FOR `latest` AND CLAIM TO BE CURRENT (2026-07-31).
        #
        # `drawdown_from_high` is what G1 gates on, and it is `latest.close / hi - 1` — so a name
        # whose bars stopped weeks ago is judged on a price from that day while the gate treats the
        # answer as current. INHD ran on a 2026-06-08 close, 51 days stale, and FAILED G1: recorded
        # as assessed-and-rejected when it could not be assessed at all.
        #
        # THE CONTRACT ALREADY EXISTED and this field ignored it. `staleness_days` (config default
        # 5) is applied to `last` a few lines above, which becomes a STALE field — but the derived
        # ratios were built with `_derived(...)`, which carries no staleness at all. The bound is
        # therefore not a new constant: it is the shipped contract, finally applied to the field
        # that decides. It clears the market calendar with a day to spare — IWM and MDY agree
        # exactly and neither shows a gap over 4d — and refuses anything past it.
        #
        # UNKNOWN, never a value: the gate maps UNKNOWN to NOT_EVALUATED, so a name that could not
        # be assessed stops looking like one that was assessed and rejected.
        if age > staleness_days:
            # NEVER (0, 0) ON A FAILED LOOKUP (review finding). `window_facts` returns None when
            # no bar sits at or before the window start — reachable whenever `have_year` is met by
            # a span that begins INSIDE the 52-week window — and defaulting to zeros printed
            # "spans 0d over 0 bars", which reads as a measured empty window rather than a
            # measurement that could not be made. A fabricated zero inside the fix for a
            # mislabelled value is the same defect one layer along.
            facts = window_facts(bars, start=w_start, end=as_of)
            window_desc = (f"window spans {facts[0]}d over {facts[1]} bars" if facts
                           else "window not resolvable — no bar at or before "
                                f"{w_start.isoformat()}")
            stale_note = (
                f"latest bar {as_of.isoformat()} is {age}d before the {reference_date.isoformat()} "
                f"reference (> {staleness_days}d) — the drawdown would be a ratio to a "
                f"{age}d-old close presented as current; {window_desc}")
            drawdown = dist_low = _unknown(stale_note)
        else:
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

    def leg(bars: list[PriceBar]) -> tuple[float, date] | None:
        """This side's return over the window, with the DATE its start price came from."""
        a = _bar_on_or_before(bars, start)
        now = _close_on_or_before(bars, end)
        if a is None or now is None or a.close <= 0:
            return None
        return now / a.close - 1.0, a.bar_date

    n_leg, b_leg = leg(name_bars), leg(bench_bars)
    if n_leg is None or b_leg is None:
        return DataField.unknown(
            source="EOD", tier=SourceTier.DERIVED, note="insufficient coverage over window"
        )
    name_ret, n_anchor = n_leg
    bench_ret, b_anchor = b_leg

    # THE START ANCHOR IS BOUNDED (2026-07-31). `_bar_on_or_before` reaches back with NO limit, so a
    # hole in the series silently widens the window: OPI's anchor sat 116d before the start and the
    # gate compared 296 days of move against a 180-day threshold. A longer window means a larger
    # |rel|, which makes the −15% bar EASIER — so the failure mode admits names, and with the legs
    # reversed it would have put one in the pool cohort selection draws from.
    #
    # NOT_EVALUATED, never FAIL: the name could not be assessed on the window the threshold was
    # calibrated for, and it must not look like one that was assessed and rejected.
    for side, anchor in (("name", n_anchor), ("benchmark", b_anchor)):
        back = (start - anchor).days
        if back > MAX_ANCHOR_LAG_DAYS:
            return DataField.unknown(
                source="EOD", tier=SourceTier.DERIVED,
                note=(f"{side} start anchor {anchor.isoformat()} is {back}d before the window "
                      f"start {start.isoformat()} (> {MAX_ANCHOR_LAG_DAYS}d) — the series has a "
                      f"hole there, so the comparison would span "
                      f"{(end - anchor).days}d against a {lookback_days}d threshold"),
            )

    lag = (reference_date - end).days
    facts = window_facts(name_bars, start=start, end=end)
    assert facts is not None  # an anchor was just resolved above, so this cannot be None
    span, obs = facts
    return DataField.present(
        name_ret - bench_ret, as_of=end, source="EOD", tier=SourceTier.DERIVED,
        note=(f"window {n_anchor.isoformat()}→{end.isoformat()} spans {span}d over {obs} bars "
              f"(target {lookback_days}d; common last bar; name frontier {n_end.isoformat()}, "
              f"benchmark frontier {b_end.isoformat()}"
              + (f"; {lag}d short of the {reference_date.isoformat()} reference)"
                 if lag else ")")),
    )
