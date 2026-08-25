"""The browser's preview scorer must agree with the Python scorer, row for row.

WHY A TWIN EXISTS AT ALL. Editing a label in the tape changed the chip and nothing else — the
readout, the target line, the horizon band and the FIT window all read `results.jsonl`, which was
scored server-side from the label as it was BEFORE the edit. Marking a call bearish left a bearish
chip beside a bullish-signed return, disagreeing on one screen with nothing saying so. So the
browser recomputes edited rows locally.

WHY THAT IS DANGEROUS, AND WHAT THIS PIN DOES. A py↔JS twin over one artifact is exactly the shape
`test_duplicate_definitions.py` exists to catch: neither side can import the other, so the
conventions get hand-copied and a one-sided edit ships two surfaces that disagree with nothing red.
`vinci calls score` stays authoritative; this asserts the preview cannot quietly diverge from it,
over the REAL committed corpus rather than a fixture built to agree.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "calls" / "pdicarlotrader"
SCORER = ROOT / "frontend" / "lib" / "callscore.js"

#: Every field both sides compute. `local` is the preview's own marker and is not compared.
FIELDS = ("status", "entry", "entry_date", "exit", "exit_date", "horizon_days", "horizon_assumed",
          "ret", "bench_ret", "excess", "mfe", "mae", "target_px", "target_status", "target_hit",
          "direction_correct", "mark", "mark_date", "elapsed_days", "unrealised",
          "bench_unrealised", "mfe_to_date", "mae_to_date", "target_hit_to_date")

_DRIVER = """
import { scoreCall } from "SCORER";
import { readFileSync } from "node:fs";
const rows = JSON.parse(readFileSync(process.argv[2], "utf8"));
const load = (p) => JSON.parse(readFileSync(p, "utf8")).bars
  .map((r) => ({ d: r[0], o: r[1], h: r[2], l: r[3], c: r[4], v: r[5] }));
const cache = new Map();
const bars = (p) => { if (!cache.has(p)) cache.set(p, load(p)); return cache.get(p); };
const out = rows.map((r) => scoreCall({
  tweetId: r.tweet_id, ticker: r.ticker, posted: r.posted, bias: r.bias,
  target: r.target, targetType: r.target_type, horizonLo: r.hlo, horizonHi: r.hhi,
  bars: bars(r.bars_path), bench: bars(r.bench_path),
}));
process.stdout.write(JSON.stringify(out));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
@pytest.mark.skipif(not (CORPUS / "results.jsonl").is_file(), reason="no scored corpus")
def test_the_preview_scorer_agrees_with_the_python_scorer_on_the_real_corpus(
    tmp_path: pathlib.Path,
) -> None:
    """Over every scored row whose bars are committed, every field must match."""
    labels = json.loads((CORPUS / "labels.json").read_text())
    raw = (CORPUS / "results.jsonl").read_text().splitlines()
    scored = [json.loads(x) for x in raw if x.strip()]
    bench_p = CORPUS / "bars" / "SPY.json"
    assert bench_p.is_file(), "SPY bars are not committed — the benchmark leg cannot be compared"

    payload = []
    for r in scored:
        bars_p = CORPUS / "bars" / f"{r['ticker']}.json"
        if not bars_p.is_file():
            continue
        lab = labels.get(f"{r['tweet_id']}|{r['ticker']}")
        if lab is None:
            continue
        payload.append({
            "tweet_id": r["tweet_id"], "ticker": r["ticker"], "posted": r["posted"],
            "bias": r["bias"], "target": lab.get("target"), "target_type": lab.get("target_type"),
            "hlo": lab.get("hlo"), "hhi": lab.get("hhi"),
            "bars_path": str(bars_p), "bench_path": str(bench_p),
        })
    assert len(payload) > 3000, f"only {len(payload)} rows to compare — the corpus shrank"

    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(payload))
    driver = tmp_path / "drive.mjs"
    driver.write_text(_DRIVER.replace("SCORER", SCORER.as_uri()))
    proc = subprocess.run(["node", str(driver), str(inp)],
                          capture_output=True, text=True, check=True)
    js_rows = json.loads(proc.stdout)
    assert len(js_rows) == len(payload)

    by_key = {(r["tweet_id"], r["ticker"]): r for r in scored}
    mismatches: list[str] = []
    for js in js_rows:
        py = by_key[(js["tweet_id"], js["ticker"])]
        for f in FIELDS:
            a, b = js.get(f), py.get(f)
            if isinstance(a, float) and isinstance(b, float):
                if abs(a - b) > 1e-9:
                    mismatches.append(f"{js['ticker']} {js['tweet_id']} {f}: js={a} py={b}")
            elif a != b:
                mismatches.append(f"{js['ticker']} {js['tweet_id']} {f}: js={a!r} py={b!r}")
    assert not mismatches, (
        f"the preview scorer diverged from the Python scorer on {len(mismatches)} field(s) — the "
        f"conventions are pre-registered and the twin must not drift:\n  "
        + "\n  ".join(mismatches[:12]))


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_the_two_target_parsers_agree_on_every_shape_that_matters(tmp_path: pathlib.Path) -> None:
    """The parser is where the twin is most likely to drift: it carries seven statuses, a
    sign rule, a plausibility band and a directional check, all hand-copied."""
    from vinci.calls.targets import parse_target

    cases = [("400", "point", 340.0, "bullish"), ("300", "point", 303.12, "bullish"),
             ("676-684", "range", 668.36, "bearish"), ("210-200", "range", 100.0, "bullish"),
             ("-10%", "pct", 100.0, "bearish"), ("-10-15%", "pct", 100.0, "bullish"),
             ("50-100%", "pct", 100.0, "bullish"), ("10%", "pct", 100.0, "none"),
             ("5000000", "point", 430.0, "bearish"), ("ATH", "qualitative", 100.0, "bullish"),
             (None, "none", 100.0, "bullish"), ("about twice", "point", 100.0, "bullish"),
             ("92.50", "point", 93.89, "bullish"), ("60-80", "range", 200.0, "bearish")]
    drv = tmp_path / "p.mjs"
    drv.write_text(f'import {{ parseTarget }} from "{SCORER.as_uri()}";\n'
                   'const cs = JSON.parse(process.argv[2]);\n'
                   'process.stdout.write(JSON.stringify(cs.map(([t, ty, e, b]) => '
                   'parseTarget(t, ty, e, b))));')
    out = subprocess.run(["node", str(drv), json.dumps(cases)],
                         capture_output=True, text=True, check=True)
    js = json.loads(out.stdout)
    for (t, ty, e, b), got in zip(cases, js, strict=True):
        py = parse_target(t, ty, e, b)
        assert got["status"] == py.status.value, (
            f"{t!r}/{ty}/{b}: js={got['status']} py={py.status.value}")
        if py.price is None:
            assert got["price"] is None, f"{t!r}: js resolved a price python refused"
        else:
            assert abs(got["price"] - py.price) < 1e-9, f"{t!r}: js={got['price']} py={py.price}"
