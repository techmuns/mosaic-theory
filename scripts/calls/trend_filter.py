"""Does a trend filter separate his good calls from his noise — or just import momentum's returns?

TWO QUESTIONS, AND THE SECOND ONE IS THE TRAP. Filtering his calls to those where the stock was
already above its moving average will almost certainly lift the numbers. That does not make it his
edge: time-series momentum is one of the few technical effects with genuine out-of-sample support
(Moskowitz/Ooi/Pedersen, 58 assets; a documented 1966-85 out-of-sample replication), so ANY signal
filtered by trend inherits trend's returns. Attributing that lift to the caller is the error.

SO THE FILTER IS RUN WITH A PLACEBO. For every real call, a NEARBY trading day he did not post on
(same ticker, within +/-90 days) goes through the identical pipeline. If "above the average" helps
as much on those dates as on his, the filter is doing the work and he contributes nothing. The
comparison that matters is not filtered-vs-unfiltered; it is his-lift-vs-placebo-lift.

The +/-90 day bound is the whole design. A placebo date drawn from the full history lands in a
different market, and the contrast then measures the REGIME rather than his timing — the first cut
did exactly that and reported a placebo lift of -6.9% where a matched one gives -3.9%.

WHY 50 DAYS AND NOT 200. The 200-day average is computable on only 56% of rows, and that 56% is not
a random half: bars begin ~95 days before a ticker's FIRST mention, so a long look-back exists only
for names he had already been posting about. Filtering on it would silently select his repeat names.
The 50-day is available on 100% of rows and carries the same published pedigree.

ONE FILTER, PRE-REGISTERED, NO VARIANTS. Sullivan/Timmermann/White tested 7,846 technical rules on
a century of Dow data and almost none survived correction for multiple comparisons. This script
tests exactly one rule and reports its placebo beside it, because the alternative — trying several
and reporting the best — is the method that produced those 7,846 nulls.

    python -m scripts.calls.trend_filter [handle]
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import statistics
import sys
from datetime import date
from typing import Any

from vinci.calls.bars import BENCHMARK, load_bars
from vinci.calls.score import Bar, score_call

LADDER = [21, 63]
WINDOW = 50
SEED = 20260828
Z = 1.959964


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def above_ma(bars: list[Bar], when: date, window: int) -> bool | None:
    """Was the last printed close above its `window`-bar average? Uses only bars up to `when`."""
    prior = [b for b in bars if b[0] <= when]
    if len(prior) < window:
        return None
    closes = [b[4] for b in prior[-window:]]
    return prior[-1][4] > sum(closes) / window


def cell(rows: list[tuple[bool, float]]) -> dict[str, Any] | None:
    if len(rows) < 25:
        return None
    ex = [e for _, e in rows]
    beat = sum(1 for e in ex if e > 0)
    lo, hi = wilson(beat, len(ex))
    return {"n": len(ex), "rate": beat / len(ex), "lo": lo, "hi": hi,
            "median": statistics.median(ex)}


def show(label: str, above: list[tuple[bool, float]],
         below: list[tuple[bool, float]]) -> float | None:
    a, b = cell(above), cell(below)
    if not a or not b:
        print(f"  {label:<26}{'too few rows':>46}")
        return None
    lift = a["rate"] - b["rate"]
    print(f"  {label:<26}"
          f"above {a['n']:>5,} {a['rate']:>4.0%} [{a['lo']:.0%},{a['hi']:.0%}] "
          f"med {a['median']:>+6.2%}   below {b['n']:>5,} {b['rate']:>4.0%} "
          f"med {b['median']:>+6.2%}   lift {lift:>+5.1%}")
    return lift


def main() -> int:
    handle = sys.argv[1] if len(sys.argv) > 1 else "pdicarlotrader"
    d = pathlib.Path("data/calls") / handle
    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    posts: dict[str, Any] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posts[str(p["id"])] = p
    bench = load_bars(handle, BENCHMARK)
    cache: dict[str, list[Bar]] = {}
    rng = random.Random(SEED)

    real: dict[int, dict[str, list[tuple[bool, float]]]] = {h: {} for h in LADDER}
    placebo: dict[int, list[tuple[bool, float]]] = {h: [] for h in LADDER}
    for key, lab in labels.items():
        if lab.get("bias") not in {"bullish", "bearish"}:
            continue
        tid, _, tk = key.partition("|")
        post = posts.get(tid)
        if post is None:
            continue
        if tk not in cache:
            cache[tk] = load_bars(handle, tk)
        bars = cache[tk]
        when = date.fromisoformat(post["d"])
        cls = str(lab.get("post_class") or "(none)")
        trend = above_ma(bars, when, WINDOW)
        for hz in LADDER:
            r = score_call(tweet_id=tid, ticker=tk, posted=when, bias=lab["bias"],
                           target=lab.get("target"), target_type=lab.get("target_type"),
                           horizon_lo=None, horizon_hi=hz, bars=bars, bench=bench)
            if r.status == "CLOSED" and r.excess is not None and trend is not None:
                real[hz].setdefault("ALL", []).append((trend, r.excess))
                real[hz].setdefault(cls, []).append((trend, r.excess))
        # THE PLACEBO: same ticker, same bias, a NEARBY date he did not post on. Drawn within
        # +/-90 days, because a date sampled from the whole history lands in a different market and
        # the comparison then measures the regime rather than his timing. The question the placebo
        # has to answer is narrow: on this name, around this time, was THIS day special?
        pool = [b[0] for b in bars
                if b[0] != when and abs((b[0] - when).days) <= 90]
        if not pool:
            continue
        fake = rng.choice(pool)
        ftrend = above_ma(bars, fake, WINDOW)
        if ftrend is None:
            continue
        for hz in LADDER:
            r = score_call(tweet_id=tid, ticker=tk, posted=fake, bias=lab["bias"],
                           target=None, target_type="none", horizon_lo=None, horizon_hi=hz,
                           bars=bars, bench=bench)
            if r.status == "CLOSED" and r.excess is not None:
                placebo[hz].append((ftrend, r.excess))

    print(f"THE {WINDOW}-DAY TREND FILTER, AND WHAT IT IS ACTUALLY MEASURING")
    print("  'lift' = beat-SPY rate above the average, minus the rate below it.\n")
    for hz in LADDER:
        print(f"\n{'=' * 118}\n{hz}-DAY HORIZON\n{'=' * 118}")
        lifts = {}
        for cls in ["ALL"] + sorted(k for k in real[hz] if k != "ALL"):
            lifts[cls] = show(cls, [x for x in real[hz][cls] if x[0]],
                              [x for x in real[hz][cls] if not x[0]])
        print()
        pl = show("PLACEBO (nearby dates)", [x for x in placebo[hz] if x[0]],
                  [x for x in placebo[hz] if not x[0]])
        if pl is not None and lifts.get("ALL") is not None:
            diff = lifts["ALL"] - pl
            print(f"\n  his lift {lifts['ALL']:+.1%} vs placebo lift {pl:+.1%}"
                  f"  ->  difference {diff:+.1%}")
            print("  Each rate above carries a +/-3pp interval, so a difference-of-differences of "
                  "this size\n  is NOT distinguishable from zero. Read it as 'no effect', not as "
                  "a small effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
