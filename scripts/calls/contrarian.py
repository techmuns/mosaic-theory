"""Fading his calls: is there money in taking the other side?

THE ARITHMETIC IS NOT THE TEST. Market-neutral fading — short what he likes, long SPY against it —
returns exactly MINUS his excess, so a beat-SPY rate of 48% for him is 52% for the fader by
definition. Reporting that as a discovery would be reporting his 48% twice. The three things that
are NOT determined in advance, and are therefore what this script measures:

  1. SIGNIFICANCE  — 52% on 3,000 rows may or may not exclude 50%.
  2. STABILITY     — his weakness was concentrated in particular quarters (74% -> 22% beat-SPY by
                     quarter). A fade that only works when he was cold is the regime again, so the
                     same time split used everywhere else applies here.
  3. COST          — a 21-day round trip is ~12 turns a year, and the short leg pays borrow. An
                     edge of a few tenths of a percent per trade does not survive that, and saying
                     so is the point of the exercise.

TWO WAYS TO FADE, AND THEY ARE DIFFERENT BETS.

  neutral  short the name, long SPY against it. Return = -(his excess). No market exposure; this
           isolates whether his SELECTION is bad.
  outright short the name, hold cash. Return = -(his return). This is short a 1.59x-beta book in a
           market that rose, so it should lose badly — and if it does, that is confirmation the
           book's returns are beta rather than selection, not a separate finding.

Costs are applied as a per-trade round-trip haircut on the neutral leg only, at three levels, so
the reader can see where the edge dies rather than being handed one assumption.

    python -m scripts.calls.contrarian [handle]
"""
from __future__ import annotations

import json
import math
import pathlib
import statistics
import sys
from datetime import date
from typing import Any

from vinci.calls.bars import BENCHMARK, load_bars
from vinci.calls.score import Bar, score_call

LADDER = [5, 21, 63, 126]
SPLIT = date(2025, 9, 1)
COSTS_BPS = [0, 25, 50]          # round-trip, both legs, in basis points
Z = 1.959964


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def stats(xs: list[float]) -> dict[str, Any]:
    n = len(xs)
    wins = sum(1 for x in xs if x > 0)
    lo, hi = wilson(wins, n)
    mean = statistics.fmean(xs)
    sd = statistics.pstdev(xs) if n > 1 else 0.0
    return {"n": n, "win": wins / n, "lo": lo, "hi": hi,
            "median": statistics.median(xs), "mean": mean,
            "t": (mean / (sd / math.sqrt(n))) if sd > 0 else 0.0}


def line(label: str, s: dict[str, Any]) -> None:
    star = " *" if abs(s["t"]) >= 1.96 else "  "
    print(f"  {label:<26}{s['n']:>6,}{s['win']:>8.0%} [{s['lo']:.0%},{s['hi']:.0%}]"
          f"{s['median']:>+11.2%}{s['mean']:>+11.2%}{s['t']:>+8.2f}{star}")


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

    rows: list[dict[str, Any]] = []
    for key, lab in labels.items():
        if lab.get("bias") not in {"bullish", "bearish"}:
            continue
        tid, _, tk = key.partition("|")
        post = posts.get(tid)
        if post is None:
            continue
        if tk not in cache:
            cache[tk] = load_bars(handle, tk)
        when = date.fromisoformat(post["d"])
        rec: dict[str, Any] = {"when": when, "neutral": {}, "outright": {}}
        for hz in LADDER:
            r = score_call(tweet_id=tid, ticker=tk, posted=when, bias=lab["bias"],
                           target=lab.get("target"), target_type=lab.get("target_type"),
                           horizon_lo=None, horizon_hi=hz, bars=cache[tk], bench=bench)
            if r.status != "CLOSED":
                continue
            if r.excess is not None:
                rec["neutral"][hz] = -r.excess
            if r.ret is not None:
                rec["outright"][hz] = -r.ret
        if rec["neutral"] or rec["outright"]:
            rows.append(rec)

    disc = [r for r in rows if r["when"] < SPLIT]
    hold = [r for r in rows if r["when"] >= SPLIT]
    print(f"FADING HIS CALLS — {len(rows):,} directional rows"
          f"  (discovery {len(disc):,} before {SPLIT}, holdout {len(hold):,} after)\n")
    print(f"  {'':<26}{'n':>6}{'win rate':>8}{'':>10}{'median':>11}{'mean':>11}{'t':>8}")

    for leg in ("neutral", "outright"):
        title = ("MARKET-NEUTRAL: short the name, long SPY" if leg == "neutral"
                 else "OUTRIGHT SHORT: short the name, hold cash")
        print(f"\n{'=' * 92}\n{title}\n{'=' * 92}")
        for hz in LADDER:
            xs = [r[leg][hz] for r in rows if hz in r[leg]]
            if len(xs) < 25:
                continue
            line(f"{hz}d  all", stats(xs))
            for name, sample in (("discovery", disc), ("holdout", hold)):
                sub = [r[leg][hz] for r in sample if hz in r[leg]]
                if len(sub) >= 25:
                    line(f"      {name}", stats(sub))
            print()

    print(f"{'=' * 92}\nCOSTS — market-neutral leg, round-trip haircut on both sides\n{'=' * 92}")
    print(f"  {'':<26}" + "".join(f"{str(c) + 'bp':>14}" for c in COSTS_BPS) + f"{'turns/yr':>11}")
    for hz in LADDER:
        xs = [r["neutral"][hz] for r in rows if hz in r["neutral"]]
        if len(xs) < 25:
            continue
        turns = 252 / hz
        cells = []
        for c in COSTS_BPS:
            net = statistics.fmean(xs) - c / 10000.0
            cells.append(f"{net * turns:>+13.1%} ")
        print(f"  {str(hz) + 'd annualised':<26}" + "".join(cells) + f"{turns:>10.1f}")
    print("\n  Annualised = mean net return per trade x turns per year. It ignores compounding,")
    print("  variance drag, borrow beyond the haircut, and slippage on names this illiquid —")
    print("  every one of which makes the real figure WORSE than the one printed here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
