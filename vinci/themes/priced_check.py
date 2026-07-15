"""Priced-check — the PRICE AXIS of a basket (assemble numbers; conclude nothing).

Pure, network-free computation ported VERBATIM from the ad-hoc session scripts that produced
``data/priced_check/report_*.txt`` (the validated method): split-adjusted daily closes →
basket-MEDIAN cumulative return over 6/12/18mo, excess vs SPY / IWM, per-member coverage, a
quarter-by-quarter excess-vs-IWM trajectory, market-model residual dispersion, and a MECHANICAL
tag from a fixed rule. ``<`` MIN_PRICED priced members in a window → UNDEFINED-with-reason, never a
fabricated 0. Stale/delisted members (last bar older than RECENCY_DAYS) get no "now" and drop out.

The CLI (``themes-priced-check``) fetches the closes via the repo Polygon client and adds the
valuation-percentile read (cached EDGAR); everything numeric here is deterministic and testable.
"""
from __future__ import annotations

import bisect
import calendar
import statistics as st
from datetime import date, timedelta
from typing import Any

WINDOWS = (6, 12, 18)          # trailing months for the priced read
RECENCY_DAYS = 7               # last bar older than this → stale/delisted, no "now"
MIN_PRICED = 3                 # < this many priced members in a window → UNDEFINED
DISP_MIN_OBS = 20             # min overlapping daily residuals to admit a pair into the dispersion
_TRAJ_BOUNDS = (18, 15, 12, 9, 6, 3, 0)  # 7 month-boundaries → 6 quarters, oldest→newest
_PRICED_TAG = 0.20             # 12mo excess-vs-BOTH threshold for the mechanical tag


def months_ago(d: date, m: int) -> date:
    y, mo = d.year, d.month - m
    while mo <= 0:
        mo += 12
        y -= 1
    return date(y, mo, min(d.day, calendar.monthrange(y, mo)[1]))


class PriceCtx:
    """Per-ticker close series on a shared market trading-day calendar. All lookups are
    close-on-or-before; nothing is filled, smoothed, or substituted."""

    def __init__(self, bars: dict[str, dict[str, float]], trading_days: list[str],
                 latest: date) -> None:
        self.bars = bars
        self.trading = trading_days           # sorted iso list of market trading days
        self.latest = latest
        self._sorted = {t: sorted(m) for t, m in bars.items()}

    def close_ob(self, t: str, target: date) -> tuple[str, float] | None:
        """(iso, close) for t on the latest trading day <= target; None if none."""
        ds = self._sorted.get(t) or []
        i = bisect.bisect_right(ds, target.isoformat()) - 1
        if i < 0:
            return None
        return ds[i], self.bars[t][ds[i]]

    def close_now(self, t: str) -> float | None:
        """Current close = close on/before LATEST, but only if the name is not stale/delisted."""
        ob = self.close_ob(t, self.latest)
        if ob is None:
            return None
        iso, c = ob
        if date.fromisoformat(iso) < self.latest - timedelta(days=RECENCY_DAYS):
            return None  # last bar too old → delisted/halted, refuse a stale "now"
        return c

    def ret_over(self, t: str, anchor: date) -> float | None:
        """Cumulative return of t from close-on/before(anchor) to current close."""
        c_now = self.close_now(t)
        if c_now is None:
            return None
        ob = self.close_ob(t, anchor)
        if ob is None or ob[1] <= 0:
            return None
        return c_now / ob[1] - 1.0

    def ret_between(self, t: str, a: date, b: date) -> float | None:
        """Return of t between close-on/before(a) and close-on/before(b)."""
        oa, ob = self.close_ob(t, a), self.close_ob(t, b)
        if oa is None or ob is None or oa[1] <= 0:
            return None
        return ob[1] / oa[1] - 1.0

    def coverage(self, t: str, lo: date, hi: date) -> tuple[int, int]:
        """(bars_found, gaps) for t over market trading days in [lo, hi]."""
        expected = [d for d in self.trading if lo.isoformat() <= d <= hi.isoformat()]
        found = sum(1 for d in expected if d in self.bars.get(t, {}))
        return found, len(expected) - found


def priced_read(ctx: PriceCtx, members: list[str]) -> dict[int, dict[str, Any]]:
    """Per window: basket-MEDIAN cumulative return + excess vs SPY / IWM; UNDEFINED if < MIN_PRICED
    members are priced (never a fabricated 0)."""
    out: dict[int, dict[str, Any]] = {}
    for w in WINDOWS:
        a = months_ago(ctx.latest, w)
        priced = [r for r in (ctx.ret_over(t, a) for t in members) if r is not None]
        spy, iwm = ctx.ret_over("SPY", a), ctx.ret_over("IWM", a)
        if len(priced) < MIN_PRICED:
            out[w] = {"undef": f"only {len(priced)} priced members (<{MIN_PRICED})",
                      "n": len(priced), "spy": spy, "iwm": iwm}
        else:
            med = st.median(priced)
            out[w] = {"med": med, "n": len(priced),
                      "ex_spy": (med - spy) if spy is not None else None,
                      "ex_iwm": (med - iwm) if iwm is not None else None,
                      "spy": spy, "iwm": iwm}
    return out


def trajectory(ctx: PriceCtx, members: list[str]) -> list[dict[str, Any]]:
    """Quarter-by-quarter basket-median EXCESS vs IWM across 18mo (oldest→newest)."""
    qb = [months_ago(ctx.latest, m) for m in _TRAJ_BOUNDS]
    rows: list[dict[str, Any]] = []
    for q in range(1, 7):
        a, b = qb[q - 1], qb[q]
        rq = [x for x in (ctx.ret_between(t, a, b) for t in members) if x is not None]
        iwm = ctx.ret_between("IWM", a, b)
        if len(rq) < MIN_PRICED or iwm is None:
            rows.append({"q": q, "a": a, "b": b, "undef": True, "n": len(rq)})
        else:
            rows.append({"q": q, "a": a, "b": b, "ex_iwm": st.median(rq) - iwm, "n": len(rq)})
    return rows


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    mx, my = _mean(xs), _mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    return float(cov / ((vx * vy) ** 0.5))


def _paired(a: list[float | None], b: list[float | None]) -> tuple[list[float], list[float]]:
    """The (a, b) values on days where BOTH are present — no fill, no smoothing."""
    xs, ys = [], []
    for av, bv in zip(a, b, strict=True):
        if av is not None and bv is not None:
            xs.append(av)
            ys.append(bv)
    return xs, ys


def dispersion(ctx: PriceCtx, members: list[str]) -> dict[str, Any]:
    """Median pairwise Pearson corr of daily market-model (vs IWM) RESIDUAL returns, trailing 6mo.
    A residual exists only where the name and IWM share a same-day return (no fill)."""
    disp_lo = months_ago(ctx.latest, 6)
    wd = [d for d in ctx.trading if disp_lo.isoformat() <= d <= ctx.latest.isoformat()]
    if len(wd) < DISP_MIN_OBS + 1:
        return {"undef": "window too short"}
    n = len(wd)

    def rets(t: str) -> list[float | None]:
        s = ctx.bars.get(t, {})
        r: list[float | None] = [None] * n
        for k in range(1, n):
            p0, p1 = s.get(wd[k - 1]), s.get(wd[k])
            if p0 and p1 and p0 > 0:
                r[k] = p1 / p0 - 1.0
        return r

    mkt = rets("IWM")
    resid: dict[str, list[float | None]] = {}
    for t in members:
        r = rets(t)
        xs, ys = _paired(mkt, r)  # market x, name y
        if len(xs) < DISP_MIN_OBS:
            continue
        mx, my = _mean(xs), _mean(ys)
        vx = sum((x - mx) ** 2 for x in xs)
        if vx <= 0:
            continue
        beta = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / vx
        alpha = my - beta * mx
        e: list[float | None] = [None] * n
        for k in range(n):
            rk, mk = r[k], mkt[k]
            if rk is not None and mk is not None:
                e[k] = rk - alpha - beta * mk
        resid[t] = e
    used = list(resid)
    corrs: list[float] = []
    for i in range(len(used)):
        for j in range(i + 1, len(used)):
            ax, bx = _paired(resid[used[i]], resid[used[j]])
            if len(ax) < DISP_MIN_OBS:
                continue
            c = _pearson(ax, bx)
            if c is not None:
                corrs.append(c)
    if len(corrs) < 1:
        return {"undef": "no admissible pairs"}
    return {"median": st.median(corrs), "n_members": len(used), "n_pairs": len(corrs)}


def tag(pr: dict[int, dict[str, Any]]) -> str:
    """MECHANICAL, 12mo window. excess vs BOTH SPY & IWM > +20% → PRICED; both <= +20% →
    NOT-PRICED; else MIXED. UNDEFINED if the 12mo read or a benchmark is missing."""
    w = pr[12]
    if "undef" in w:
        return f"UNDEFINED (12mo: {w['undef']})"
    es, ei = w["ex_spy"], w["ex_iwm"]
    if es is None or ei is None:
        return "UNDEFINED (12mo benchmark missing)"
    if es > _PRICED_TAG and ei > _PRICED_TAG:
        return "PRICED"
    if es <= _PRICED_TAG and ei <= _PRICED_TAG:
        return "NOT-PRICED"
    return "MIXED"


def compute(ctx: PriceCtx, members: list[str]) -> dict[str, Any]:
    """The full price axis for a basket — priced read, trajectory, dispersion, coverage, the
    per-window benchmark reference, and the mechanical tag. Concludes nothing."""
    pr = priced_read(ctx, members)
    lo18 = months_ago(ctx.latest, 18)
    return {
        "latest": ctx.latest.isoformat(),
        "members": list(members),
        "anchors": {w: months_ago(ctx.latest, w).isoformat() for w in WINDOWS},
        "benchmarks": {w: {"spy": ctx.ret_over("SPY", months_ago(ctx.latest, w)),
                           "iwm": ctx.ret_over("IWM", months_ago(ctx.latest, w))}
                       for w in WINDOWS},
        "coverage": {t: ctx.coverage(t, lo18, ctx.latest) for t in members},
        "priced": pr,
        "trajectory": trajectory(ctx, members),
        "dispersion": dispersion(ctx, members),
        "tag": tag(pr),
    }
