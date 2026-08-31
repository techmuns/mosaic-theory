"""Which KINDS of his bullish calls beat SPY — searched on one period, tested on another.

THIS SCRIPT IS DATA MINING, AND IS BUILT SO THAT SHOWS. Slicing a 2,459-row corpus by ten
attributes and reporting the best cells will ALWAYS produce winners: at 40 cells and p<0.05 you
expect two by chance alone, and the corpus is small enough that a single good week inside one cell
carries it. The fund's own rule is that nothing is set by what would have paid. So the search runs
on a DISCOVERY window and every surviving claim is re-measured, untouched, on a HOLDOUT window it
never saw. A pattern that does not repeat out of sample is reported as failed, not omitted.

WHAT COUNTS AS A FEATURE. Only what a reader knew AT POST TIME: the tags, the post's own shape, and
where the stated target sat relative to the last printed close. Nothing derived from the outcome —
no realised return, no "did it hit", no forward window. That is the boundary the whole exercise
depends on, so each feature below is one a person could have evaluated the moment the post landed.

THE SPLIT IS BY TIME, NOT AT RANDOM. A random split leaks: the same name posted twice in a week
lands on both sides, and the market regime is shared. Splitting at a date makes the holdout a
genuine "what happened next", which is the only question worth asking of a signal.

    python -m scripts.calls.what_works [handle]
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
from vinci.calls.sheet import _price_context

LADDER = [5, 21, 63, 126]          # under a year, per the question
SPLIT = date(2025, 9, 1)           # discovery before, holdout on or after
MIN_N = 25                         # a cell smaller than this is not a claim
Z = 1.959964


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def features(lab: dict[str, Any], post: dict[str, Any], anchor: float | None,
             target_px: float | None) -> dict[str, str]:
    """Everything a reader knew when the post landed. No outcome touches this function."""
    f: dict[str, str] = {
        "class": str(lab.get("post_class") or "(none)"),
        "specificity": str(lab.get("spec") or "(none)"),
        "action": str(lab.get("action") or "none"),
        "target_type": str(lab.get("target_type") or "none"),
        "conditional": "yes" if lab.get("is_conditional") else "no",
        "retrospective": "yes" if lab.get("is_retrospective") else "no",
        "has_video": "yes" if post.get("v") else "no",
        "cashtags": "1" if len(post.get("tk") or []) <= 1 else
                    ("2" if len(post.get("tk") or []) == 2 else "3+"),
        "horizon_stated": "yes" if (lab.get("hhi") or lab.get("hlo")) else "no",
    }
    if anchor and target_px and anchor > 0:
        gap = target_px / anchor - 1.0
        f["target_gap"] = ("below spot" if gap < 0 else
                           "0-10% above" if gap <= 0.10 else
                           "10-25% above" if gap <= 0.25 else "25%+ above")
    return f


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
        if lab.get("bias") != "bullish":
            continue
        tid, _, tk = key.partition("|")
        post = posts.get(tid)
        if post is None:
            continue
        if tk not in cache:
            cache[tk] = load_bars(handle, tk)
        scores = {}
        for hz in LADDER:
            r = score_call(tweet_id=tid, ticker=tk, posted=date.fromisoformat(post["d"]),
                           bias="bullish", target=lab.get("target"),
                           target_type=lab.get("target_type"), horizon_lo=None, horizon_hi=hz,
                           bars=cache[tk], bench=bench)
            if r.status == "CLOSED" and r.excess is not None:
                scores[hz] = r.excess
        if not scores:
            continue
        ctx = _price_context(cache[tk], str(post.get("t") or ""))
        first = next(iter(scores))
        tp = score_call(tweet_id=tid, ticker=tk, posted=date.fromisoformat(post["d"]),
                        bias="bullish", target=lab.get("target"),
                        target_type=lab.get("target_type"), horizon_lo=None, horizon_hi=first,
                        bars=cache[tk], bench=bench).target_px
        rows.append({"when": date.fromisoformat(post["d"]), "excess": scores,
                     "f": features(lab, post, ctx.get("px_at_post"), tp)})

    disc = [r for r in rows if r["when"] < SPLIT]
    hold = [r for r in rows if r["when"] >= SPLIT]
    print(f"bullish rows scored: {len(rows):,}")
    print(f"  DISCOVERY  before {SPLIT}: {len(disc):,}")
    print(f"  HOLDOUT    from   {SPLIT}: {len(hold):,}\n")

    def cell(sample: list[dict[str, Any]], name: str, val: str, hz: int) -> dict[str, Any] | None:
        ex = [r["excess"][hz] for r in sample if r["f"].get(name) == val and hz in r["excess"]]
        if len(ex) < MIN_N:
            return None
        beat = sum(1 for e in ex if e > 0)
        return {"n": len(ex), "beat": beat, "rate": beat / len(ex),
                "ci": wilson(beat, len(ex)), "median": statistics.median(ex)}

    names = sorted({k for r in rows for k in r["f"]})
    found = []
    for name in names:
        for val in sorted({r["f"].get(name) for r in rows if r["f"].get(name)}):
            for hz in LADDER:
                c = cell(disc, name, val, hz)
                # A CLAIM IS "beats SPY MORE OFTEN THAN NOT, and the interval says so."
                if c and c["ci"][0] > 0.50:
                    found.append((name, val, hz, c))
    tested = sum(1 for name in names
                 for val in {r["f"].get(name) for r in rows if r["f"].get(name)}
                 for hz in LADDER if cell(disc, name, val, hz))
    print(f"cells tested in discovery (n>={MIN_N}): {tested}")
    print(f"cells whose 95% CI clears 50% beat-SPY: {len(found)}")
    print(f"  expected by chance at this many tests: about {tested * 0.025:.1f}\n")
    if not found:
        print("  NOTHING SURVIVED DISCOVERY. There is no cell to carry to the holdout.")
        return 0
    print(f"{'feature':<16}{'value':<15}{'hz':>5}{'DISCOVERY':>28}{'HOLDOUT':>28}")
    for name, val, hz, c in sorted(found, key=lambda x: -x[3]["rate"]):
        h = cell(hold, name, val, hz)
        ds = f"{c['beat']}/{c['n']} {c['rate']:.0%} [{c['ci'][0]:.0%},{c['ci'][1]:.0%}]"
        hs = (f"{h['beat']}/{h['n']} {h['rate']:.0%} [{h['ci'][0]:.0%},{h['ci'][1]:.0%}]"
              if h else f"n<{MIN_N} — untestable")
        mark = "  HELD" if h and h["ci"][0] > 0.50 else ("  failed" if h else "")
        print(f"{name:<16}{val:<15}{hz:>4}d{ds:>28}{hs:>28}{mark}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
