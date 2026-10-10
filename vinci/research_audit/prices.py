"""Build one total-return price series per symbol: raw closes → ``adjClose`` / ``divCash`` /
``splitFactor`` — and report everything about it that could make a return wrong.

THE CONVENTION (stated once, used everywhere). ``close`` is the AS-TRADED price. On a session ``t``
with split ratio ``k`` (new shares per old; 1.0 when none) and cash dividends ``D`` going ex on
``t``, the one-session gross return is ``k * (close_t + D) / close_{t-1}`` — dividends reinvested at
the ex-date close (the CRSP / Tiingo convention). ``adjClose`` is the cumulative product of those
gross returns, scaled so ``adjClose == close`` on the last bar; so for any two bars
``adjClose_b / adjClose_a - 1`` IS the total return between them. ``divCash`` and ``splitFactor``
are the per-session ``D`` and ``k`` (Tiingo's field names, as the brief asks).

NOTHING IS CARRIED FORWARD. A session the stock has no bar for stays absent; the engine refuses an
entry or exit on an absent or zero-volume bar instead of borrowing a neighbour's close.

WHAT BLOCKS, WHAT WARNS.
- BLOCK (a return spanning the day is not computed): a one-session move whose size is a clean
  split ratio with NO split on record (``SUSPECTED_UNRECORDED_SPLIT``); a recorded split the raw
  prices do not show (``SPLIT_NOT_REFLECTED``); a non-USD dividend (no FX path here).
- WARN (reported, not blocking): any other one-session move beyond ±40%, a dividend whose ex-date
  is not a bar of this series, a dividend going ex on a split day, session gaps.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from vinci.research_audit.polygon import DailyBar, Dividend, GroupedDay, Split, read_grouped_cache

#: A one-session |log move| beyond this is checked against clean split ratios and reported.
LARGE_MOVE = math.log(1.4)
#: Clean split ratios a mis-recorded split would show up as (and their inverses). NOT 1.5 or 2.5:
#: those are ordinary earnings moves (-33% / +50%), and the first full run flagged TTD's real
#: -33.0% post-earnings session on 2025-02-13 as an unrecorded 3:2 split. A 3:2 split Polygon has
#: on record (PACCAR 2023-02-08) is still applied; only an UNRECORDED one at those ratios is missed.
_SPLIT_RATIOS = (2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0)
_SPLIT_TOL = 0.03
#: Overlap reconciliation: a cache bar (un-adjusted) and a live bar for the same session must agree
#: on close within this relative tolerance (Polygon rounds to the cent; 1bp covers it on any price).
OVERLAP_TOL = 1e-4


@dataclass(frozen=True)
class PricePoint:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    adj_close: float
    div_cash: float
    split_factor: float
    source: str
    source_ref: str


@dataclass(frozen=True)
class Block:
    """``step``: the move from session ``lo`` to session ``hi`` is suspect — a window containing
    both is blocked. Not ``step``: every price in [lo, hi] is suspect — a window touching it is."""

    lo: date
    hi: date
    reason: str
    step: bool


@dataclass
class OverlapReport:
    n_overlap: int = 0
    n_mismatch: int = 0
    max_rel_diff: float = 0.0
    examples: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.n_mismatch == 0


@dataclass
class Series:
    symbol: str
    points: list[PricePoint]
    by_day: dict[date, PricePoint]
    first_live_day: date | None
    overlap: OverlapReport
    blocks: list[Block] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    gaps: list[date] = field(default_factory=list)
    dividends_used: list[Dividend] = field(default_factory=list)
    splits_used: list[Split] = field(default_factory=list)

    def blocked_between(self, a: date, b: date) -> str | None:
        """The reason a return from ``a`` to ``b`` must not be computed, or ``None``."""
        for blk in self.blocks:
            if blk.step and a <= blk.lo and b >= blk.hi:  # the window contains the bad step
                return blk.reason
            if not blk.step and a <= blk.hi and b >= blk.lo:  # the window touches suspect prices
                return blk.reason
        return None


def load_grouped_window(cache_ns_dir: Path, start: date, end: date,
                        symbols: set[str]) -> dict[date, GroupedDay | None]:
    """Read every weekday's cached grouped-daily response in [start, end] ONCE for all symbols."""
    out: dict[date, GroupedDay | None] = {}
    d = start
    while d <= end:
        if d.weekday() < 5:
            out[d] = read_grouped_cache(cache_ns_dir, d, symbols)
        d += timedelta(days=1)
    return out


def unadjust_cached(bar: DailyBar, fetched_at: date, splits: Iterable[Split]) -> DailyBar:
    """Undo ``adjusted=true`` on a cached bar: multiply back every split executed AFTER the bar's
    session and ON/BEFORE the day the response was fetched (those are the splits the provider had
    already applied to it). A split after the fetch date was not applied and is left alone."""
    k = 1.0
    for s in splits:
        if bar.day < s.execution_date <= fetched_at:
            k *= s.ratio
    if k == 1.0:
        return bar
    return DailyBar(day=bar.day, open=bar.open * k, high=bar.high * k, low=bar.low * k,
                    close=bar.close * k, volume=bar.volume / k,
                    source=bar.source + f" un-adjusted x{k:g}", source_ref=bar.source_ref)


def _is_split_like(ratio: float) -> bool:
    r = ratio if ratio >= 1 else 1.0 / ratio
    return any(abs(r / s - 1.0) <= _SPLIT_TOL for s in _SPLIT_RATIOS)


def build_series(
    symbol: str,
    *,
    live: list[DailyBar],
    grouped: dict[date, GroupedDay | None],
    dividends: list[Dividend],
    splits: list[Split],
    sessions: list[date] | None,
) -> Series:
    """Splice cache (before the first live bar) onto live raw bars, reconcile the overlap, then
    build the total-return chain. ``sessions`` (the exchange calendar) is used for gap detection."""
    first_live = live[0].day if live else None
    cache_raw: dict[date, DailyBar] = {}
    for d, g in grouped.items():
        if g is None or symbol not in g.bars:
            continue
        cache_raw[d] = unadjust_cached(g.bars[symbol], g.fetched_at, splits)

    overlap = OverlapReport()
    live_by_day = {b.day: b for b in live}
    for d, cb in sorted(cache_raw.items()):
        lb = live_by_day.get(d)
        if lb is None:
            continue
        overlap.n_overlap += 1
        rel = abs(cb.close / lb.close - 1.0)
        overlap.max_rel_diff = max(overlap.max_rel_diff, rel)
        if rel > OVERLAP_TOL:
            overlap.n_mismatch += 1
            if len(overlap.examples) < 5:
                overlap.examples.append(f"{d}: cache {cb.close:.4f} vs live {lb.close:.4f}")

    bars = [b for d, b in sorted(cache_raw.items()) if first_live is None or d < first_live]
    bars += live
    s = Series(symbol=symbol, points=[], by_day={}, first_live_day=first_live, overlap=overlap)
    if not overlap.ok and bars:
        s.blocks.append(Block(bars[0].day, first_live or bars[-1].day,
                              f"CACHE_LIVE_OVERLAP_MISMATCH ({overlap.n_mismatch}/"
                              f"{overlap.n_overlap})", step=False))
    if not bars:
        return s

    day_set = {b.day for b in bars}
    if sessions is not None:
        s.gaps = [d for d in sessions if bars[0].day <= d <= bars[-1].day and d not in day_set]
        if s.gaps:
            s.warnings.append(f"{len(s.gaps)} exchange session(s) with no bar (first: {s.gaps[0]})"
                              " — never filled; entry/exit on such a day is refused")
        after = [d for d in sessions if d > bars[-1].day]
        if after:
            s.warnings.append(f"SERIES ENDS {bars[-1].day}: {len(after)} later session(s) have no "
                              f"bar (delisting / ticker change / halt) — any exit after it is "
                              f"refused, nothing is carried forward")

    # Assign each corporate action to the first bar on/after its date (and say so when that is
    # not the action's own date).
    def bar_on_or_after(d: date) -> date | None:
        for b in bars:
            if b.day >= d:
                return b.day
        return None

    div_at: dict[date, float] = {}
    for dv in dividends:
        if dv.ex_date <= bars[0].day or dv.ex_date > bars[-1].day:
            continue  # before the first bar's return or after the series — no effect on it
        if dv.currency.upper() != "USD":
            s.blocks.append(Block(dv.ex_date, dv.ex_date, f"NON_USD_DIVIDEND {dv.currency}",
                                  step=False))
            continue
        at = bar_on_or_after(dv.ex_date)
        if at is None:
            continue
        if at != dv.ex_date:
            s.warnings.append(f"dividend ex {dv.ex_date} ({dv.cash}) is not a bar day; "
                              f"applied at {at}")
        div_at[at] = div_at.get(at, 0.0) + dv.cash
        s.dividends_used.append(dv)
    split_at: dict[date, float] = {}
    for sp in splits:
        if sp.execution_date <= bars[0].day or sp.execution_date > bars[-1].day:
            continue
        at = bar_on_or_after(sp.execution_date)
        if at is None:
            continue
        split_at[at] = split_at.get(at, 1.0) * sp.ratio
        s.splits_used.append(sp)
    for d in div_at:
        if d in split_at:
            s.warnings.append(f"dividend and split both effective {d} — dividend basis assumed "
                              "post-split; review")

    tr = [1.0]
    for prev, cur in zip(bars, bars[1:], strict=False):
        k = split_at.get(cur.day, 1.0)
        cash = div_at.get(cur.day, 0.0)
        gross = k * (cur.close + cash) / prev.close
        move = math.log(gross)
        if k != 1.0 and abs(math.log(cur.close / prev.close)) < LARGE_MOVE / 2 \
                and abs(math.log(k)) > LARGE_MOVE / 2:
            s.blocks.append(Block(prev.day, cur.day,
                                  f"SPLIT_NOT_REFLECTED {k:g} on {cur.day} (raw move "
                                  f"{cur.close / prev.close - 1:+.1%})", step=True))
        elif abs(move) > LARGE_MOVE:
            if k == 1.0 and _is_split_like(gross):
                s.blocks.append(Block(prev.day, cur.day,
                                      f"SUSPECTED_UNRECORDED_SPLIT {gross:.3f}x on {cur.day} "
                                      f"({prev.source.split()[0]} -> {cur.source.split()[0]})",
                                      step=True))
            else:
                s.warnings.append(f"large one-session move {gross - 1:+.1%} on {cur.day}")
        tr.append(tr[-1] * gross)

    scale = bars[-1].close / tr[-1]
    for b, t in zip(bars, tr, strict=True):
        p = PricePoint(day=b.day, open=b.open, high=b.high, low=b.low, close=b.close,
                       volume=b.volume, adj_close=t * scale, div_cash=div_at.get(b.day, 0.0),
                       split_factor=split_at.get(b.day, 1.0), source=b.source,
                       source_ref=b.source_ref)
        s.points.append(p)
        s.by_day[b.day] = p
    return s
