"""The forward ladder applied to a BUCKET rather than one call: same windows, aggregated.

WHY THE STATED HORIZON IS IGNORED. Each call names its own window, so a single aggregate over
stated horizons compares a 5-day call against a 12-month one and calls the result a hit-rate.
Putting every call on the same clock is the only way two buckets compare — and it turns one number
into a shape. The flow-print bucket read 59% at its stated horizons; on the ladder that is 67% at
21 days and 51% by 126, which is a different claim entirely.

``score_call`` is reused UNCHANGED, once per (call, horizon), so every convention here — entry at
the next open, exit at the close n bars later, SPY over the identical window, returns signed by the
stated bias — is the scorer's rather than something re-derived beside it.

A CELL WITH FEW ROWS IS A DIFFERENT MARKET, NOT A LONGER HOLD. At 252 days only the oldest calls
have elapsed, so that column is survivorship: it is printed with its `n` for exactly that reason,
and both buckets rise there together.

    python -m scripts.calls.forward_ladder [handle]

(as a module, like every other script here — a plain `python scripts/...` run puts the script's own
directory on `sys.path` and `vinci` is then unimportable.)
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
DIRECTIONAL = {"bullish", "bearish"}
Z = 1.959964


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / d
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return centre - half, centre + half


def run(handle: str) -> dict[str, dict[int, dict[str, Any]]]:
    d = pathlib.Path("data/calls") / handle
    labels: dict[str, Any] = json.loads((d / "labels.json").read_text())
    posts: dict[str, Any] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for p in json.loads(f.read_text()):
            posts[str(p["id"])] = p

    def n_tickers(key: str) -> int:
        return len(posts.get(key.partition("|")[0], {}).get("tk") or [])

    buckets = {
        "flow prints": [k for k, v in labels.items()
                        if v.get("post_class") == "flow_spam"
                        and v.get("bias") in DIRECTIONAL and n_tickers(k) <= 2],
        "his own calls": [k for k, v in labels.items()
                          if v.get("post_class") == "signal_candidate"
                          and v.get("bias") in DIRECTIONAL],
    }
    bench = load_bars(handle, BENCHMARK)
    cache: dict[str, list[Bar]] = {}
    out: dict[str, dict[int, dict[str, Any]]] = {}
    for name, keys in buckets.items():
        out[name] = {}
        for hz in LADDER:
            scored = []
            for key in keys:
                tid, _, tk = key.partition("|")
                post, lab = posts.get(tid), labels[key]
                if post is None:
                    continue
                if tk not in cache:
                    cache[tk] = load_bars(handle, tk)
                r = score_call(
                    tweet_id=tid, ticker=tk, posted=date.fromisoformat(post["d"]),
                    bias=lab["bias"], target=lab.get("target"),
                    target_type=lab.get("target_type"), horizon_lo=None, horizon_hi=hz,
                    bars=cache[tk], bench=bench)
                if r.status == "CLOSED":
                    scored.append(r)
            excess = [r.excess for r in scored if r.excess is not None]
            ok = sum(1 for r in scored if r.direction_correct)
            out[name][hz] = {
                "n": len(scored), "ok": ok,
                "hit": ok / len(scored) if scored else None,
                "ci": wilson(ok, len(scored)) if scored else None,
                "median_excess": statistics.median(excess) if excess else None,
                "beat_spy": sum(1 for e in excess if e > 0) / len(excess) if excess else None,
            }
    return out


def main() -> int:
    handle = sys.argv[1] if len(sys.argv) > 1 else "pdicarlotrader"
    out = run(handle)
    print(f"{'':<16}" + "".join(f"{str(h) + 'd':>17}" for h in LADDER))
    for name, rows in out.items():
        print(f"\n{name}")
        print(f"  {'n (closed)':<14}" + "".join(f"{rows[h]['n']:>17,}" for h in LADDER))
        print(f"  {'direction ok':<14}" + "".join(
            f"{rows[h]['hit']:>16.0%} " if rows[h]["hit"] is not None else f"{'-':>17}"
            for h in LADDER))
        cis = [f"[{rows[h]['ci'][0]:.0%},{rows[h]['ci'][1]:.0%}]" for h in LADDER]
        print(f"  {'  95% CI':<14}" + "".join(f"{c:>17}" for c in cis))
        print(f"  {'median excess':<14}" + "".join(
            f"{rows[h]['median_excess']:>+16.2%} " if rows[h]["median_excess"] is not None
            else f"{'-':>17}" for h in LADDER))
        print(f"  {'% beat SPY':<14}" + "".join(
            f"{rows[h]['beat_spy']:>16.0%} " if rows[h]["beat_spy"] is not None else f"{'-':>17}"
            for h in LADDER))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
