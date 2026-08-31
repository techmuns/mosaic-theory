"""Forward performance of his ACTIONABLE directional calls, against SPY.

WHAT IS REMOVED AND WHY. Three classes are excluded because their forward return cannot be read as
a signal, not because they performed badly:

  pnl_report   written BECAUSE a trade already worked. Selected on the past by construction, so a
               strong forward number is the selection showing through, not a prediction. This class
               was the single best-looking cell in earlier runs, which is exactly the reason to
               drop it rather than a reason to keep it.
  noise        commentary with no position implied; a direction tag on it is an artifact.
  engagement   polls and bait.

That leaves `signal_candidate`, `promo`, `flow_spam` and the untagged gold rows: 3,021 of the 3,305
directional rows, of which 2,979 score at one horizon or more (the rest have no elapsed window or
no bars).

THE HOLDOUT IS PRINTED BESIDE EVERY FULL-SAMPLE FIGURE, and it is not decoration. In this corpus
the posting quarter swings beat-SPY from 74% to 22%, and every pattern found so far has been that
swing wearing a costume: 65 in-sample attribute cells cleared 50% and none survived the split.
A full-sample row here means nothing until its two halves agree.

READ THE 252d COLUMN AS A DIFFERENT SAMPLE. Only calls old enough to have elapsed appear in it, so
it is both survivorship and a different market. Every class rises there, `noise` included, because
SPY rose ~17% over those windows.

    python -m scripts.calls.filtered_performance [handle]
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

LADDER = [5, 21, 63, 126, 252]
EXCLUDE = {"pnl_report", "noise", "engagement"}
SPLIT = date(2025, 9, 1)
Z = 1.959964


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def block(title: str, rows: list[dict[str, Any]]) -> None:
    print(f"\n{title}")
    if not rows:
        print("    (no rows)")
        return
    cells = {}
    for hz in LADDER:
        rs = [r for r in rows if hz in r["by"]]
        cells[hz] = {
            "n": len(rs),
            "ok": sum(1 for r in rs if r["by"][hz]["ok"]),
            "ex": [r["by"][hz]["ex"] for r in rs if r["by"][hz]["ex"] is not None],
            "call": [r["by"][hz]["ret"] for r in rs],
            "spy": [r["by"][hz]["spy"] for r in rs if r["by"][hz]["spy"] is not None],
        }
    def row(label: str, fmt: Any) -> None:
        print(f"    {label:<16}" + "".join(fmt(cells[h]) for h in LADDER))
    row("n", lambda c: f"{c['n']:>13,}")
    row("direction ok", lambda c: f"{c['ok'] / c['n']:>12.0%} " if c["n"] else f"{'-':>13}")
    def ci(c: dict[str, Any]) -> str:
        if not c["n"]:
            return f"{'-':>13}"
        lo, hi = wilson(c["ok"], c["n"])
        return f"{f'[{lo:.0%},{hi:.0%}]':>13}"
    row("  95% CI", ci)
    row("median call", lambda c: f"{statistics.median(c['call']):>+12.2%} "
        if c["call"] else f"{'-':>13}")
    row("median SPY", lambda c: f"{statistics.median(c['spy']):>+12.2%} "
        if c["spy"] else f"{'-':>13}")
    row("median excess", lambda c: f"{statistics.median(c['ex']):>+12.2%} "
        if c["ex"] else f"{'-':>13}")
    row("% beat SPY", lambda c: f"{sum(1 for e in c['ex'] if e > 0) / len(c['ex']):>12.0%} "
        if c["ex"] else f"{'-':>13}")


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
    dropped = 0
    for key, lab in labels.items():
        if lab.get("bias") not in {"bullish", "bearish"}:
            continue
        cls = str(lab.get("post_class") or "(none)")
        if cls in EXCLUDE:
            dropped += 1
            continue
        tid, _, tk = key.partition("|")
        post = posts.get(tid)
        if post is None:
            continue
        if tk not in cache:
            cache[tk] = load_bars(handle, tk)
        when = date.fromisoformat(post["d"])
        by: dict[int, dict[str, Any]] = {}
        for hz in LADDER:
            r = score_call(tweet_id=tid, ticker=tk, posted=when, bias=lab["bias"],
                           target=lab.get("target"), target_type=lab.get("target_type"),
                           horizon_lo=None, horizon_hi=hz, bars=cache[tk], bench=bench)
            if r.status == "CLOSED" and r.ret is not None:
                by[hz] = {"ok": bool(r.direction_correct), "ex": r.excess,
                          "ret": r.ret, "spy": r.bench_ret}
        if by:
            rows.append({"cls": cls, "bias": lab["bias"], "when": when, "by": by})

    print(f"ACTIONABLE DIRECTIONAL CALLS — {len(rows):,} scored"
          f"   (excluded {', '.join(sorted(EXCLUDE))}: {dropped:,} rows)")
    print(f"{'':<20}" + "".join(f"{str(h) + 'd':>13}" for h in LADDER))
    block("ALL KEPT CLASSES", rows)
    block("  discovery (pre 2025-09)", [r for r in rows if r["when"] < SPLIT])
    block("  holdout   (post)", [r for r in rows if r["when"] >= SPLIT])
    for cls in sorted({r["cls"] for r in rows}):
        block(f"class · {cls}", [r for r in rows if r["cls"] == cls])
    for bias in ("bullish", "bearish"):
        block(f"bias · {bias}", [r for r in rows if r["bias"] == bias])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
