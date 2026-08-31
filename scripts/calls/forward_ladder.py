"""The forward ladder applied to a BUCKET rather than a call: same five windows, aggregated.

The stated horizon is ignored — every call is put on the same clock, which is the only way two
buckets compare. `score_call` is reused unchanged, once per (call, horizon).
"""
import json, pathlib, statistics, math
from datetime import date
from vinci.calls.bars import load_bars, BENCHMARK
from vinci.calls.score import score_call

H, LADDER = "pdicarlotrader", [5, 21, 63, 126, 252]
d = pathlib.Path(f"data/calls/{H}")
L = json.loads((d/"labels.json").read_text())
posts = {}
for f in sorted((d/"posts").glob("*.json")):
    for p in json.loads(f.read_text()): posts[str(p["id"])] = p
ntk = lambda k: len(posts.get(k.partition("|")[0], {}).get("tk") or [])
DIR = {"bullish", "bearish"}
z = 1.959964
def wil(k, n):
    p = k/n; dd = 1+z*z/n; c = (p+z*z/(2*n))/dd
    hh = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/dd
    return (c-hh, c+hh)

BUCKETS = {
 "flow prints": [k for k, v in L.items() if v.get("post_class") == "flow_spam"
                 and v.get("bias") in DIR and ntk(k) <= 2],
 "his own calls": [k for k, v in L.items() if v.get("post_class") == "signal_candidate"
                   and v.get("bias") in DIR],
}
bench, cache = load_bars(H, BENCHMARK), {}
out = {}
for name, keys in BUCKETS.items():
    out[name] = {}
    for hz in LADDER:
        rs = []
        for k in keys:
            tid, _, tk = k.partition("|"); v = L[k]; p = posts.get(tid)
            if not p: continue
            if tk not in cache: cache[tk] = load_bars(H, tk)
            r = score_call(tweet_id=tid, ticker=tk, posted=date.fromisoformat(p["d"]),
                           bias=v["bias"], target=v.get("target"),
                           target_type=v.get("target_type"), horizon_lo=None, horizon_hi=hz,
                           bars=cache[tk], bench=bench)
            if r.status == "CLOSED": rs.append(r)
        ex = [r.excess for r in rs if r.excess is not None]
        ok = sum(1 for r in rs if r.direction_correct)
        out[name][hz] = {"n": len(rs), "ok": ok,
                         "hit": ok/len(rs) if rs else None,
                         "ci": wil(ok, len(rs)) if rs else None,
                         "med_ex": statistics.median(ex) if ex else None,
                         "beat_spy": sum(1 for e in ex if e > 0)/len(ex) if ex else None}

print(f"{'':<16}" + "".join(f"{str(h)+'d':>17}" for h in LADDER))
for name in BUCKETS:
    print(f"\n{name}")
    r = out[name]
    print(f"  {'n (closed)':<14}" + "".join(f"{r[h]['n']:>17,}" for h in LADDER))
    print(f"  {'direction ✓':<14}" + "".join(
        f"{r[h]['hit']:>16.0%} " if r[h]['hit'] is not None else f"{'—':>17}" for h in LADDER))
    print(f"  {'  95% CI':<14}" + "".join(
        f"{'['+format(r[h]['ci'][0],'.0%')+','+format(r[h]['ci'][1],'.0%')+']':>17}" for h in LADDER))
    print(f"  {'median excess':<14}" + "".join(
        f"{r[h]['med_ex']:>+16.2%} " if r[h]['med_ex'] is not None else f"{'—':>17}" for h in LADDER))
    print(f"  {'% beat SPY':<14}" + "".join(
        f"{r[h]['beat_spy']:>16.0%} " if r[h]['beat_spy'] is not None else f"{'—':>17}" for h in LADDER))
pathlib.Path("/tmp/buckets.json").write_text(json.dumps(out, default=str))
