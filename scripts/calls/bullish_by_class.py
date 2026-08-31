"""Every BULLISH call, split by post class, across the forward ladder, against SPY.

WHAT THIS ANSWERS. "Does he have an edge" is unanswerable as one number: it averages a whale-flow
print against a promo against a genuine call, and it averages three weeks against a year. This
splits both ways at once — class down, horizon across — so each cell is a claim that can be checked.

THE COOL-DOWN. He posts the same name repeatedly, sometimes five times in a day, and each post
becomes a row with its OWN entry. Averaged naively, one enthusiastic week outvotes a quiet quarter,
and the aggregate measures his POSTING RATE as much as his judgement. A cool-down keeps only the
FIRST bullish row per ticker in a rolling window and drops the rest — which is also the only version
a reader could have traded, since the later posts are re-statements of a position already open.

  none  every row, as labelled
  15d   one row per ticker per 15 calendar days
  30d   one row per ticker per 30 calendar days

Applied ACROSS the whole bullish cohort, not within each class: the signal is "he turned bullish on
$X", and a `promo` restating a `signal_candidate` from three days earlier is the same position. A
class can therefore lose rows to an earlier row of another class, which is the honest version of
"what would I have held" and is stated here because it makes the per-class n's uneven.

CALENDAR days, not trading days — the cool-down models a reader's attention, not a market clock.

Every number comes from `score_call`, reused unchanged, once per (row, horizon); the stated horizon
is ignored so the columns are comparable. SPY runs the identical window, and where SPY does not
span it the row contributes no excess rather than a misleading one.

    python -m scripts.calls.bullish_by_class [handle]
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
from vinci.calls.score import Bar, CallResult, score_call

LADDER = [5, 21, 63, 126, 252]
COOLDOWNS: list[int | None] = [None, 15, 30]
Z = 1.959964


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / d
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return centre - half, centre + half


def cooldown_keep(rows: list[tuple[str, str, date]], days: int) -> set[str]:
    """Keys to KEEP: the first row for a ticker, then nothing for that ticker for `days`.

    The window restarts from each KEPT row, not from every row — otherwise a daily poster is
    silenced forever by one post rather than throttled to one signal per window.
    """
    last: dict[str, date] = {}
    keep: set[str] = set()
    for key, ticker, when in sorted(rows, key=lambda r: (r[2], r[0])):
        prev = last.get(ticker)
        if prev is None or (when - prev) >= timedelta(days=days):
            keep.add(key)
            last[ticker] = when
    return keep


def main() -> int:
    handle = sys.argv[1] if len(sys.argv) > 1 else "pdicarlotrader"
    d = pathlib.Path("data/calls") / handle
    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    posts: dict[str, Any] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posts[str(p["id"])] = p

    cohort = [(k, v) for k, v in labels.items()
              if v.get("bias") == "bullish" and k.partition("|")[0] in posts]
    dated = [(k, k.partition("|")[2], date.fromisoformat(posts[k.partition("|")[0]]["d"]))
             for k, _ in cohort]
    keeps = {c: (None if c is None else cooldown_keep(dated, c)) for c in COOLDOWNS}

    bench = load_bars(handle, BENCHMARK)
    cache: dict[str, list[Bar]] = {}
    scored: dict[tuple[str, int], CallResult] = {}
    for key, lab in cohort:
        tid, _, tk = key.partition("|")
        if tk not in cache:
            cache[tk] = load_bars(handle, tk)
        for hz in LADDER:
            r = score_call(tweet_id=tid, ticker=tk,
                           posted=date.fromisoformat(posts[tid]["d"]), bias="bullish",
                           target=lab.get("target"), target_type=lab.get("target_type"),
                           horizon_lo=None, horizon_hi=hz, bars=cache[tk], bench=bench)
            if r.status == "CLOSED":
                scored[(key, hz)] = r

    classes = sorted({(v.get("post_class") or "(none)") for _, v in cohort})
    cls_of = {k: (v.get("post_class") or "(none)") for k, v in cohort}
    for cd in COOLDOWNS:
        keep = keeps[cd]
        label = "no cool-down" if cd is None else f"{cd}-day cool-down"
        kept = len(cohort) if keep is None else len(keep)
        print(f"\n{'=' * 104}\n{label.upper()}   —   {kept:,} of {len(cohort):,} bullish rows"
              f"\n{'=' * 104}")
        print(f"{'class':<19}{'metric':<16}" + "".join(f"{str(h) + 'd':>13}" for h in LADDER))
        for cls in classes:
            keys = [k for k, _ in cohort
                    if cls_of[k] == cls and (keep is None or k in keep)]
            cells: dict[int, dict[str, Any]] = {}
            for hz in LADDER:
                rs = [scored[(k, hz)] for k in keys if (k, hz) in scored]
                ex = [r.excess for r in rs if r.excess is not None]
                ok = sum(1 for r in rs if r.direction_correct)
                cells[hz] = {"n": len(rs), "ok": ok, "ex": ex,
                             "call": [r.ret for r in rs if r.ret is not None],
                             "spy": [r.bench_ret for r in rs if r.bench_ret is not None]}
            if not any(c["n"] for c in cells.values()):
                continue
            print(f"{cls:<19}{'n':<16}" + "".join(f"{cells[h]['n']:>13,}" for h in LADDER))
            print(f"{'':<19}{'direction ok':<16}" + "".join(
                f"{cells[h]['ok'] / cells[h]['n']:>12.0%} " if cells[h]["n"] else f"{'-':>13}"
                for h in LADDER))
            cis = []
            for h in LADDER:
                if not cells[h]["n"]:
                    cis.append("-")
                    continue
                lo, hi = wilson(cells[h]["ok"], cells[h]["n"])
                cis.append(f"[{lo:.0%},{hi:.0%}]")
            print(f"{'':<19}{'  95% CI':<16}" + "".join(f"{c:>13}" for c in cis))
            print(f"{'':<19}{'median call':<16}" + "".join(
                f"{statistics.median(cells[h]['call']):>+12.2%} " if cells[h]["call"]
                else f"{'-':>13}" for h in LADDER))
            print(f"{'':<19}{'median SPY':<16}" + "".join(
                f"{statistics.median(cells[h]['spy']):>+12.2%} " if cells[h]["spy"]
                else f"{'-':>13}" for h in LADDER))
            print(f"{'':<19}{'median excess':<16}" + "".join(
                f"{statistics.median(cells[h]['ex']):>+12.2%} " if cells[h]["ex"]
                else f"{'-':>13}" for h in LADDER))
            print(f"{'':<19}{'% beat SPY':<16}" + "".join(
                f"{sum(1 for e in cells[h]['ex'] if e > 0) / len(cells[h]['ex']):>12.0%} "
                if cells[h]["ex"] else f"{'-':>13}" for h in LADDER))
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
