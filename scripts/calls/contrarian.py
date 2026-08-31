"""Fade the calls, and score the cleaned cohort.

THE FADE IS A PAIR, NOT A MOOD. "Trading against him" has to be an actual position or the number
means nothing. The one used here is LONG SPY / SHORT THE NAME, sized equal, held over the same
window — a market-neutral pair whose return is exactly ``-excess``. That identity is the point: the
fade's hit-rate is the mirror of his (100% minus it), so nothing new is discovered by flipping the
sign. What IS new is the DISTRIBUTION, and that is where a fade differs from the call it inverts.

WHY THE MEAN MATTERS HERE AND THE MEDIAN DOES NOT. Stock excess returns are right-skewed: most
names drift, a few multiply. Fading converts that right tail into a LEFT tail — a short in PLTR
across its +738% run is not a bad quarter, it is the end of the account. A fade can therefore win
on the median, on the hit-rate, and still have a negative mean, which is the only statistic that
compounds. Both are printed side by side for exactly that reason.

THE CLEANED COHORT. Two exclusions the operator asked for, and both have a stated reason:
  - `pnl_report` is dropped. Those posts exist BECAUSE a trade already worked, so their forward
    window is selected on the past and they flatter whatever they are counted in.
  - a 30-day cool-down per ticker over what remains, keeping only the first call in each window.
    He restates positions for days; without it the aggregate measures his posting rate.

    python -m scripts.calls.contrarian [handle]
"""
from __future__ import annotations

import json
import math
import pathlib
import statistics
import sys
from datetime import date, timedelta
from typing import Any

from vinci.calls.bars import BENCHMARK, load_bars
from vinci.calls.score import Bar, score_call

LADDER = [5, 21, 63, 126, 252]
COOLDOWN = 30
Z = 1.959964


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def row(label: str, ex: list[float]) -> None:
    if not ex:
        print(f"  {label:<26}{'-':>10}")
        return
    beat = sum(1 for e in ex if e > 0)
    lo, hi = wilson(beat, len(ex))
    mean = statistics.fmean(ex)
    print(f"  {label:<26}{len(ex):>7,}{beat / len(ex):>9.0%}"
          f"  {'[' + format(lo, '.0%') + ',' + format(hi, '.0%') + ']':>12}"
          f"{statistics.median(ex):>+12.2%}{mean:>+12.2%}"
          f"{min(ex):>+11.1%}{max(ex):>+11.1%}")


def main() -> int:
    handle = sys.argv[1] if len(sys.argv) > 1 else "pdicarlotrader"
    d = pathlib.Path("data/calls") / handle
    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    posts: dict[str, Any] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posts[str(p["id"])] = p

    cohort = [(k, v) for k, v in labels.items()
              if v.get("bias") in {"bullish", "bearish"} and k.partition("|")[0] in posts]
    ex_pnl = [(k, v) for k, v in cohort if v.get("post_class") != "pnl_report"]
    last: dict[str, date] = {}
    cleaned: list[tuple[str, Any]] = []
    for k, v in sorted(ex_pnl, key=lambda kv: (posts[kv[0].partition("|")[0]]["d"], kv[0])):
        tk = k.partition("|")[2]
        when = date.fromisoformat(posts[k.partition("|")[0]]["d"])
        prev = last.get(tk)
        if prev is None or (when - prev) >= timedelta(days=COOLDOWN):
            cleaned.append((k, v))
            last[tk] = when

    print(f"cohort            all directional : {len(cohort):,}")
    print(f"                  minus pnl_report: {len(ex_pnl):,}")
    print(f"    then a {COOLDOWN}-day cool-down per name: {len(cleaned):,}\n")

    bench = load_bars(handle, BENCHMARK)
    cache: dict[str, list[Bar]] = {}
    excess: dict[int, list[float]] = {h: [] for h in LADDER}
    for key, lab in cleaned:
        tid, _, tk = key.partition("|")
        if tk not in cache:
            cache[tk] = load_bars(handle, tk)
        for hz in LADDER:
            r = score_call(tweet_id=tid, ticker=tk,
                           posted=date.fromisoformat(posts[tid]["d"]), bias=lab["bias"],
                           target=lab.get("target"), target_type=lab.get("target_type"),
                           horizon_lo=None, horizon_hi=hz, bars=cache[tk], bench=bench)
            if r.status == "CLOSED" and r.excess is not None:
                excess[hz].append(r.excess)

    hdr = (f"  {'':<26}{'n':>7}{'beat SPY':>9}{'95% CI':>13}{'median':>12}"
           f"{'MEAN':>12}{'worst':>11}{'best':>11}")
    print("FOLLOW HIM  —  long the name / short SPY, the cleaned cohort")
    print(hdr)
    for hz in LADDER:
        row(f"{hz}d", excess[hz])
    print("\nFADE HIM  —  long SPY / short the name (the same rows, position inverted)")
    print(hdr)
    for hz in LADDER:
        row(f"{hz}d", [-e for e in excess[hz]])
    print("\n  The two tables are mirrors by construction: fading is -excess, so the hit-rates sum")
    print("  to 100% and the medians negate. Read the MEAN and the WORST column, not the hit-rate:")
    print("  that is where a fade stops resembling the call it inverts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
