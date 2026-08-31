"""Two versions a reader could actually have traded, against the fixed-window scorer.

Everything measured so far holds each call for a FIXED number of days regardless of what he said
afterwards. That is right for comparing calls to each other and wrong as a model of following him:
he posts exits, and he repeats himself. These are the two obvious corrections.

CASE 1 — HIS EXITS. Each directional call is held until his NEXT `exit` or `trim` on that ticker,
then scored over the realised holding period. Compared against the identical entries held 63 days,
so the difference is attributable to his exit timing and nothing else.

CASE 2 — ONE POSITION PER NAME. The first bullish call on a ticker opens a position; every later
bullish call on the same name while the position is open is a RE-STATEMENT and is ignored rather
than opening a second one. The position closes on the first of: his stated target being touched, a
bearish call on that name, a `pnl_report` on that name, or an explicit `exit`/`trim`. After it
closes, the next bullish call can open a new one.

NO LOOKAHEAD, IN BOTH. An entry is the OPEN of the next trading day after the post — the scorer's
pre-registered convention. An EXIT SIGNAL is treated the same way: you read the post, you act the
next morning. The one exception is a target exit, which fills at the target price on the day the
high touches it, because that is a resting limit order and needs no reading.

THE CONTROL IS THE POINT. A version with exits will differ from a fixed window whether or not his
exits carry information, because the holding period changes. So each case is reported beside a
RANDOM-EXIT control: the same entries, held for a random duration drawn from the same realised
holding-period distribution. His timing is worth only the gap between them.

    python -m scripts.calls.traded_versions [handle]
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
from vinci.calls.score import Bar
from vinci.calls.targets import parse_target

FIXED = 63
SEED = 20260831
Z = 1.959964
EXIT_ACTIONS = {"exit", "trim"}


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def bars_after(bars: list[Bar], when: date) -> list[Bar]:
    return [b for b in bars if b[0] > when]


def leg(bars: list[Bar], bench: list[Bar], entry_bar: Bar, exit_i: int,
        window: list[Bar]) -> dict[str, Any] | None:
    """Return the trade's return and SPY's over the identical dates, or None if SPY misses it."""
    entry, entry_date = entry_bar[1], entry_bar[0]
    if entry <= 0:
        return None
    exit_bar = window[exit_i]
    exit_date, exit_px = exit_bar[0], exit_bar[4]
    ret = exit_px / entry - 1.0
    b_win = [b for b in bench if entry_date <= b[0] <= exit_date]
    spans = bool(bench) and bench[0][0] <= entry_date and bench[-1][0] >= exit_date
    if not (spans and len(b_win) > 1 and b_win[0][4] > 0):
        return None
    spy = b_win[-1][4] / b_win[0][4] - 1.0
    return {"ret": ret, "spy": spy, "excess": ret - spy,
            "days": exit_i + 1, "exit_date": exit_date}


def report(title: str, trades: list[dict[str, Any]]) -> None:
    print(f"\n  {title:<34}", end="")
    if not trades:
        print("(no trades)")
        return
    ex = [t["excess"] for t in trades]
    beat = sum(1 for e in ex if e > 0)
    lo, hi = wilson(beat, len(ex))
    print(f"{len(trades):>6,}{beat / len(ex):>9.0%} [{lo:.0%},{hi:.0%}]"
          f"{statistics.median(t['ret'] for t in trades):>+10.2%}"
          f"{statistics.median(t['spy'] for t in trades):>+10.2%}"
          f"{statistics.median(ex):>+11.2%}"
          f"{statistics.fmean(ex):>+10.2%}"
          f"{statistics.median(t['days'] for t in trades):>8.0f}")


def header() -> None:
    print(f"  {'':<34}{'n':>6}{'beat SPY':>9}{'':>11}{'med ret':>10}{'med SPY':>10}"
          f"{'med excess':>11}{'mean ex':>10}{'med days':>8}")


def main() -> int:  # noqa: C901
    handle = sys.argv[1] if len(sys.argv) > 1 else "pdicarlotrader"
    d = pathlib.Path("data/calls") / handle
    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    posts: dict[str, Any] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posts[str(p["id"])] = p
    bench = load_bars(handle, BENCHMARK)
    cache: dict[str, list[Bar]] = {}

    # every labelled row, by ticker, in time order — entries and exit signals both live here
    by_ticker: dict[str, list[dict[str, Any]]] = {}
    for key, lab in labels.items():
        tid, _, tk = key.partition("|")
        post = posts.get(tid)
        if post is None:
            continue
        by_ticker.setdefault(tk, []).append({
            "when": date.fromisoformat(post["d"]), "bias": lab.get("bias"),
            "action": lab.get("action") or "none", "cls": lab.get("post_class"),
            "target": lab.get("target"), "ttype": lab.get("target_type")})
    for v in by_ticker.values():
        v.sort(key=lambda r: r["when"])

    rng = random.Random(SEED)
    case1: dict[str, list[dict[str, Any]]] = {"his": [], "fixed": [], "random": []}
    case2: list[dict[str, Any]] = []
    case2_fixed: list[dict[str, Any]] = []
    case2_reason: dict[str, int] = {}
    naive: list[dict[str, Any]] = []

    for tk, rows in by_ticker.items():
        if tk not in cache:
            cache[tk] = load_bars(handle, tk)
        bars = cache[tk]
        if not bars:
            continue

        # ---------- CASE 1 : every directional call, exited on his next exit/trim ----------
        for i, r in enumerate(rows):
            if r["bias"] not in {"bullish", "bearish"}:
                continue
            fwd = bars_after(bars, r["when"])
            if not fwd:
                continue
            entry_bar, window = fwd[0], fwd[1:]
            if not window:
                continue
            sig = next((x for x in rows[i + 1:] if x["action"] in EXIT_ACTIONS), None)
            # act the morning AFTER the exit post, same rule as the entry
            idx = None
            if sig is not None:
                later = [j for j, b in enumerate(window) if b[0] > sig["when"]]
                idx = later[0] if later else None
            exited = idx is not None
            if idx is None:
                idx = len(window) - 1          # never exited: held to the last committed bar
            his = leg(bars, bench, entry_bar, idx, window)
            fix = leg(bars, bench, entry_bar, min(FIXED - 1, len(window) - 1), window)
            if his and fix:
                sign = 1.0 if r["bias"] == "bullish" else -1.0
                for name, t in (("his", his), ("fixed", fix)):
                    case1[name].append({**t, "ret": sign * t["ret"], "spy": sign * t["spy"],
                                        "excess": sign * t["excess"], "exited": exited})

        # ---------- CASE 2 : one position per name, state machine ----------
        open_pos: dict[str, Any] | None = None
        for r in rows:
            if open_pos is None:
                if r["bias"] != "bullish":
                    continue
                fwd = bars_after(bars, r["when"])
                if len(fwd) < 2:
                    continue
                tp = parse_target(r["target"], r["ttype"], entry=fwd[0][1], bias="bullish")
                open_pos = {"entry_bar": fwd[0], "window": fwd[1:], "target": tp.price,
                            "opened": r["when"], "repeats": 0}
                held = leg(bars, bench, fwd[0], min(FIXED - 1, len(fwd) - 2), fwd[1:])
                if held:
                    case2_fixed.append(held)
                continue
            # a position is open: later bullish posts are re-statements, not new entries
            if r["bias"] == "bullish":
                open_pos["repeats"] += 1
                continue
            if r["bias"] == "bearish" or r["cls"] == "pnl_report" or r["action"] in EXIT_ACTIONS:
                reason = ("bearish" if r["bias"] == "bearish" else
                          "pnl_report" if r["cls"] == "pnl_report" else "exit/trim")
                win = open_pos["window"]
                later = [j for j, b in enumerate(win) if b[0] > r["when"]]
                idx = later[0] if later else len(win) - 1
                # a resting limit at the target fills first if the high reached it en route
                tgt, tgt_i = open_pos["target"], None
                if tgt is not None:
                    hit = [j for j, b in enumerate(win[:idx + 1]) if b[2] >= tgt]
                    tgt_i = hit[0] if hit else None
                if tgt_i is not None:
                    t = leg(bars, bench, open_pos["entry_bar"], tgt_i, win)
                    if t:
                        e = open_pos["entry_bar"][1]
                        t = {**t, "ret": tgt / e - 1.0, "excess": (tgt / e - 1.0) - t["spy"]}
                    reason = "target"
                else:
                    t = leg(bars, bench, open_pos["entry_bar"], idx, win)
                if t:
                    case2.append({**t, "repeats": open_pos["repeats"], "reason": reason})
                    case2_reason[reason] = case2_reason.get(reason, 0) + 1
                open_pos = None
        if open_pos is not None:                      # still open at the end of the data
            win = open_pos["window"]
            t = leg(bars, bench, open_pos["entry_bar"], len(win) - 1, win)
            if t:
                case2.append({**t, "repeats": open_pos["repeats"], "reason": "still open"})
                case2_reason["still open"] = case2_reason.get("still open", 0) + 1

        # ---------- the naive comparison : EVERY bullish call, held 63d ----------
        for r in rows:
            if r["bias"] != "bullish":
                continue
            fwd = bars_after(bars, r["when"])
            if len(fwd) < 2:
                continue
            t = leg(bars, bench, fwd[0], min(FIXED - 1, len(fwd) - 2), fwd[1:])
            if t:
                naive.append(t)

    # a random-exit control for case 1, drawn from the SAME realised holding periods
    days_pool = [t["days"] for t in case1["his"]]
    for tk, rows in by_ticker.items():
        bars = cache.get(tk) or []
        if not bars:
            continue
        for r in rows:
            if r["bias"] not in {"bullish", "bearish"}:
                continue
            fwd = bars_after(bars, r["when"])
            if len(fwd) < 2:
                continue
            window = fwd[1:]
            t = leg(bars, bench, fwd[0], min(rng.choice(days_pool) - 1, len(window) - 1), window)
            if t:
                sign = 1.0 if r["bias"] == "bullish" else -1.0
                case1["random"].append({**t, "ret": sign * t["ret"], "spy": sign * t["spy"],
                                        "excess": sign * t["excess"]})

    print("CASE 1 — HELD UNTIL HIS NEXT exit/trim ON THAT TICKER")
    print("  (all directional calls; returns signed by bias; identical entries in every row)")
    header()
    report("his exits", case1["his"])
    report(f"same entries, fixed {FIXED}d", case1["fixed"])
    report("same entries, RANDOM duration", case1["random"])
    real = [t for t in case1["his"] if t["exited"]]
    keys = {(t["days"], t["exit_date"]) for t in real}
    print("\n  --- only where he ACTUALLY posted an exit (the rest never got one) ---")
    report("his exits, real signals only", real)
    report(f"those entries, fixed {FIXED}d",
           [f for f, h in zip(case1["fixed"], case1["his"], strict=True) if h["exited"]])
    del keys

    print("\n\nCASE 2 — ONE POSITION PER NAME, re-statements ignored")
    print("  (first bullish call opens; target / bearish / pnl_report / exit closes)")
    header()
    report("one position per name", case2)
    report(f"THE SAME entries, fixed {FIXED}d", case2_fixed)
    report(f"every bullish call, fixed {FIXED}d", naive)
    if case2:
        rep = [t["repeats"] for t in case2]
        print(f"\n  positions {len(case2):,} · re-statements absorbed {sum(rep):,} "
              f"(median {statistics.median(rep):.0f} per position, max {max(rep)})")
        print(f"  closed by: {dict(sorted(case2_reason.items(), key=lambda x: -x[1]))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
