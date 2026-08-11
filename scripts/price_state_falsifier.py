"""Price-state falsifier — do MA/RSI/new-low states carry information on the ranked queue?

PURPOSE. The operator asked whether technical states (50/200-day MA, RSI, fresh-low) should join
the pipeline as supportive flags. This script answers that on the fund's OWN reconstructed queues
(the 36 G3-complete backdated months) with rules pre-registered below, BEFORE computation.

NOTHING HERE IS PROMOTABLE. Operator decision 2026-08-11: price states may never move a rank —
only filing-based structural signals demote. This measurement can only ANSWER and KILL; whatever
separates, no gate/weight/sort is built from it. Constants are market convention, fixed ex ante,
never tuned (CLAUDE.md: face-validity, never forward returns).

PRE-REGISTration (written into the report header before any number is computed):
  Expectations: E1 "below 200d MA" is near-universal (the queue is deep-drawdown by construction);
  E2 RSI-14 mass sits below 50; E3 fresh-52w-low is a meaningful minority; E4 off-low >= +15%
  varies. Decision rules: R1 a binary state covering >90% or <10% of covered names in >=2/3 of
  months is DEAD as a filter dimension. R2 (record only) per-state forward SECTOR-relative
  separation at 30/60/120/180d with a 300-shuffle within-month control. R3 cost-of-waiting:
  entry at first appearance vs entry deferred to the first close above the 50d MA (<=126 sessions;
  never reclaims -> never entered, excess 0), both marked at the same calendar exits, vs MDY.

DATA. Backdated queues (CSV, one per as-of) + full-tape daily bars. Bars come from --bars-dir
(one gzip per day, lines "ticker,open,high,low,close,volume") or, absent that, from the netcache
at data/cache/polygon (grouped-daily JSON; the date is recovered from each entry's url). Sector
benchmarks are built from ALL liquid securities in a sector (securities.jsonl + sector_for_sic),
never from queue members — queue members were selected for having fallen.

LOADER SANITY GATE (corpus-before-synthetic): before believing any new number, the loader must
reproduce three months of the independently-computed sector-relative sweep (sector_relative.json,
written by an earlier, separate script) to <0.1 pt. Mismatch -> hard stop.

Usage:
    PYTHONPATH=. python scripts/price_state_falsifier.py \
        --queues-dir ~/Desktop/ranked-queue-price-check/backdated \
        --bars-dir  <day-file dir> \
        --gate-file ~/Desktop/ranked-queue-price-check/sector_relative.json \
        --out       ~/Desktop/ranked-queue-price-check/price_states
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import random
import statistics as st
import sys
from array import array
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from vinci.sectors import sector_for_sic

# --- market-convention constants, fixed ex ante (never tuned) ---------------------------------
MA_SHORT = 50
MA_LONG = 200
SLOPE_LOOKBACK = 21          # sessions between the two MA_SHORT readings
RSI_PERIOD = 14              # Wilder
LOW_WINDOW = 252             # trading sessions ~ 52 weeks
FRESH_LOW_SESSIONS = 21      # "the 52w low was set within the last month"
OFF_LOW_MIN = 0.15           # S6: >= +15% off the 52w low
MIN_BARS = 200               # uniform coverage requirement for every state
RECLAIM_LIMIT = 126          # R3: sessions allowed for the 50d-MA reclaim (~6 months)
HORIZONS = (30, 60, 120, 180)  # calendar days
ADV_FLOOR_BENCH = 1_000_000.0  # sector-benchmark membership floor (mirrors the earlier sweep)
MIN_SECTOR_MEMBERS = 5
SHUFFLES = 300
SEED = 20260811
FIRST_ASOF = "2023-09-01"    # the G3-complete months
GATE_TOLERANCE = 0.1         # pts; loader must reproduce the independent sweep this closely

PREREG = f"""## Pre-registration (fixed before computation)

Constants: MA {MA_SHORT}/{MA_LONG} sessions - slope over {SLOPE_LOOKBACK} - RSI-{RSI_PERIOD}
(Wilder) - 52w low over {LOW_WINDOW} sessions - fresh-low window {FRESH_LOW_SESSIONS} -
off-low floor +{OFF_LOW_MIN:.0%} - coverage requires >= {MIN_BARS} bars - reclaim limit
{RECLAIM_LIMIT} sessions - horizons {HORIZONS} calendar days - shuffle control n={SHUFFLES},
seed {SEED}.

Expectations: E1 below-{MA_LONG}d-MA is near-universal at entry; E2 RSI mass below 50;
E3 fresh-low a meaningful minority; E4 off-low >= +15% varies.

Rules: R1 a binary state covering >90% or <10% of covered names in >=2/3 of months is dead as a
filter dimension. R2 is RECORD-ONLY (operator rule: nothing price-based may ever move a rank) -
separation is reported with its shuffle percentile, and no state is promotable whatever it shows.
R3 deferral is measured against entry-at-appearance on identical calendar exits, vs MDY.
A name with no bar at an exit is carried at -100% (a real loss, never dropped); sector-benchmark
membership requires a positive close at both ends (mirrors the earlier sweep it is gated against).
"""


def wilder_rsi(closes: list[float], period: int = RSI_PERIOD) -> float | None:
    """Textbook Wilder RSI over the trailing series (uses up to 250 closes of warmup)."""
    seq = closes[-250:]
    if len(seq) < period + 1:
        return None
    gains = losses = 0.0
    for a, b in zip(seq, seq[1:period + 1], strict=False):
        d = b - a
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    ag, al = gains / period, losses / period
    for a, b in zip(seq[period:], seq[period + 1:], strict=False):
        d = b - a
        ag = (ag * (period - 1) + max(d, 0.0)) / period
        al = (al * (period - 1) + max(-d, 0.0)) / period
    if al == 0:
        return 100.0
    rs = ag / al
    return 100.0 - 100.0 / (1.0 + rs)


class Bars:
    """Full-tape daily closes/lows/dollar-volume on a shared session calendar."""

    def __init__(self, days: list[date], cl: dict[str, array], lo: dict[str, array],
                 dv: dict[str, array]) -> None:
        self.days = days
        self.idx = {d: i for i, d in enumerate(days)}
        self.cl, self.lo, self.dv = cl, lo, dv

    def series(self, t: str, upto: int) -> tuple[list[float], list[float]]:
        """(closes, lows) of the sessions the name actually traded, up to index `upto`."""
        a, b = self.cl.get(t), self.lo.get(t)
        if a is None or b is None:
            return [], []
        cs = [a[k] for k in range(upto + 1) if a[k] > 0]
        ls = [b[k] for k in range(upto + 1) if a[k] > 0]
        return cs, ls

    def fwd_index(self, i: int, horizon_days: int) -> int | None:
        tgt = self.days[i] + timedelta(days=horizon_days)
        if tgt > self.days[-1]:
            return None
        j = i
        while j + 1 < len(self.days) and self.days[j + 1] <= tgt:
            j += 1
        return j if j > i else None


def load_bars(bars_dir: Path | None, cache_dir: Path) -> Bars:
    rows: dict[str, list[tuple[date, float, float, float]]] = defaultdict(list)
    if bars_dir and bars_dir.exists():
        files = sorted(f for f in bars_dir.glob("*.csv.gz") if f.stat().st_size > 0)
        if not files:
            raise SystemExit(f"FAIL LOUD: --bars-dir {bars_dir} contains no day-files")
        days = [date.fromisoformat(f.name[:10]) for f in files]
        cl: dict[str, array] = {}
        lo: dict[str, array] = {}
        dv: dict[str, array] = {}
        blank = bytes(4 * len(days))
        for i, f in enumerate(files):
            with gzip.open(f, "rt") as fh:
                for line in fh:
                    p = line.rstrip("\n").split(",")
                    a = cl.get(p[0])
                    if a is None:
                        cl[p[0]] = array("f", blank)
                        lo[p[0]] = array("f", blank)
                        dv[p[0]] = array("f", blank)
                        a = cl[p[0]]
                    c = float(p[4])
                    a[i] = c
                    lo[p[0]][i] = float(p[3])
                    dv[p[0]][i] = c * float(p[5])
        return Bars(days, cl, lo, dv)
    # fallback: parse the netcache's grouped-daily responses (date recovered from the url)
    for f in cache_dir.glob("*.json"):
        try:
            entry = json.loads(f.read_text())
            url = entry.get("url", "")
            if "/aggs/grouped/" not in url:
                continue
            d = date.fromisoformat(url.split("/")[-1].split("?")[0])
            data = json.loads(entry["text"])
        except (ValueError, KeyError, json.JSONDecodeError):
            continue
        for r in data.get("results") or []:
            t = r.get("T")
            if t:
                rows[t].append((d, float(r["c"]), float(r["l"]), float(r["c"]) * float(r["v"])))
    if not rows:
        raise SystemExit(f"FAIL LOUD: no grouped-daily entries found in {cache_dir}")
    all_days = sorted({d for series in rows.values() for d, *_ in series})
    idx = {d: i for i, d in enumerate(all_days)}
    blank = bytes(4 * len(all_days))
    cl, lo, dv = {}, {}, {}
    for t, series in rows.items():
        cl[t] = array("f", blank)
        lo[t] = array("f", blank)
        dv[t] = array("f", blank)
        for d, c, low, dollars in series:
            i = idx[d]
            cl[t][i], lo[t][i], dv[t][i] = c, low, dollars
    return Bars(all_days, cl, lo, dv)


def load_sector_map(securities: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in securities.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            s = sector_for_sic(r.get("sic"))
            if s and s != "Unknown":
                out[r["eod_symbol"]] = s
    return out


def sector_forward(bars: Bars, sym_sec: dict[str, str], i: int, j: int) -> dict[str, float]:
    """Equal-weight forward return per sector over [i, j], liquid members only."""
    acc: dict[str, list[float]] = defaultdict(list)
    for t, sec in sym_sec.items():
        a = bars.cl.get(t)
        if a is None or a[i] <= 0 or a[j] <= 0:
            continue
        window = [x for x in bars.dv[t][max(0, i - 60):i + 1] if x > 0]
        if not window or st.mean(window) < ADV_FLOOR_BENCH:
            continue
        acc[sec].append((a[j] / a[i] - 1) * 100)
    return {s: st.mean(v) for s, v in acc.items() if len(v) >= MIN_SECTOR_MEMBERS}


def compute_states(bars: Bars, t: str, i: int) -> dict[str, float | bool] | None:
    closes, lows = bars.series(t, i)
    if len(closes) < MIN_BARS:
        return None
    px = closes[-1]
    ma_s = st.mean(closes[-MA_SHORT:])
    ma_l = st.mean(closes[-MA_LONG:])
    prev = closes[-(MA_SHORT + SLOPE_LOOKBACK):-SLOPE_LOOKBACK]
    ma_s_prev = st.mean(prev) if len(prev) == MA_SHORT else None
    rsi = wilder_rsi(closes)
    low_window = lows[-LOW_WINDOW:]
    low_252 = min(low_window)
    fresh = low_window.index(low_252) >= len(low_window) - FRESH_LOW_SESSIONS
    return {
        "above_ma50": px > ma_s,
        "above_ma200": px > ma_l,
        "ma50_rising": (ma_s_prev is not None and ma_s > ma_s_prev),
        "rsi": rsi if rsi is not None else -1.0,
        "rsi_oversold": (rsi is not None and rsi < 30),
        "fresh_low": fresh,
        "off_low_15": (low_252 > 0 and px / low_252 - 1 >= OFF_LOW_MIN),
    }


BINARY_STATES = ("above_ma50", "above_ma200", "ma50_rising", "rsi_oversold",
                 "fresh_low", "off_low_15")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queues-dir", type=Path, required=True)
    ap.add_argument("--bars-dir", type=Path, default=None)
    ap.add_argument("--gate-file", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--securities", type=Path,
                    default=Path("data/snapshots/securities.jsonl"))
    ap.add_argument("--cache-dir", type=Path, default=Path("data/cache/polygon"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report: list[str] = ["# Price-state falsifier — report", "", PREREG]

    print("loading bars ...", flush=True)
    bars = load_bars(args.bars_dir, args.cache_dir)
    print(f"  {len(bars.days)} sessions, {len(bars.cl):,} tickers", flush=True)
    sym_sec = load_sector_map(args.securities)

    qfiles = sorted(f for f in args.queues_dir.glob("ranked_queue_*.csv")
                    if f.name[13:23] >= FIRST_ASOF)
    months: list[tuple[date, list[dict[str, str]]]] = []
    for f in qfiles:
        asof = date.fromisoformat(f.name[13:23])
        if asof not in bars.idx:
            continue
        rows = [r for r in csv.DictReader(f.open())
                if r.get("structurally_disqualified") != "True"]
        months.append((asof, rows))
    report += [f"Queues: {len(months)} months, {months[0][0]} .. {months[-1][0]}; "
               f"ex-sunk rows only.", ""]

    # ---- loader sanity gate ------------------------------------------------------------------
    gate = json.loads(args.gate_file.read_text())
    gate_rows = [g for g in gate if g.get("rel30") is not None][:3]
    report.append("## Loader sanity gate (reproduce the independent sector-relative sweep)")
    report.append("")
    worst = 0.0
    for g in gate_rows:
        asof = date.fromisoformat(g["as_of"])
        i = bars.idx[asof]
        j = bars.fwd_index(i, 30)
        assert j is not None
        bench = sector_forward(bars, sym_sec, i, j)
        rows = dict(months)[asof]
        rel = []
        for r in rows:
            a = bars.cl.get(r["ticker"])
            b = bench.get(r["sector"])
            if a is None or a[i] <= 0 or b is None:
                continue
            fwd = (a[j] / a[i] - 1) * 100 if a[j] > 0 else -100.0
            rel.append(fwd - b)
        got = st.mean(rel)
        diff = abs(got - g["rel30"])
        worst = max(worst, diff)
        report.append(f"- {g['as_of']}: recomputed {got:+.3f} vs independent {g['rel30']:+.3f} "
                      f"(|diff| {diff:.3f})")
    if worst >= GATE_TOLERANCE:
        report.append(f"\n**GATE FAILED** (worst |diff| {worst:.3f} >= {GATE_TOLERANCE}) — "
                      "stopping before any state is computed.")
        (args.out / "price_states.md").write_text("\n".join(report) + "\n")
        print(f"GATE FAILED — worst |diff| {worst:.3f}", flush=True)
        return 1
    report.append(f"\nGate PASSED (worst |diff| {worst:.3f} < {GATE_TOLERANCE}).\n")
    print(f"gate passed (worst {worst:.3f})", flush=True)

    # ---- per-name states + forward sector-relative returns -----------------------------------
    per_month: list[dict[str, object]] = []
    for asof, rows in months:
        i = bars.idx[asof]
        fwd_bench = {}
        fwd_idx = {}
        for hz in HORIZONS:
            j = bars.fwd_index(i, hz)
            if j is not None:
                fwd_idx[hz] = j
                fwd_bench[hz] = sector_forward(bars, sym_sec, i, j)
        names = []
        skipped = 0
        for r in rows:
            t = r["ticker"]
            stt = compute_states(bars, t, i)
            if stt is None:
                skipped += 1
                continue
            a = bars.cl[t]
            rec: dict[str, object] = {"t": t, "sector": r["sector"], **stt}
            for hz, j in fwd_idx.items():
                b = fwd_bench[hz].get(r["sector"])
                if b is None:
                    continue
                fwd = (a[j] / a[i] - 1) * 100 if a[j] > 0 else -100.0
                rec[f"rel{hz}"] = fwd - b
            names.append(rec)
        per_month.append({"asof": asof, "names": names, "skipped": skipped})
        print(f"  {asof}  n={len(names)} (skipped {skipped} <{MIN_BARS} bars)", flush=True)

    # ---- R1 coverage / degeneracy ------------------------------------------------------------
    report.append("## R1 — coverage per state (share of covered names where the state is TRUE)")
    report.append("")
    report.append("| state | mean share | months >90% or <10% | verdict |")
    report.append("|---|---:|---:|---|")
    r1: dict[str, dict[str, float]] = {}
    for s in BINARY_STATES:
        shares = []
        extreme = 0
        for m in per_month:
            names = m["names"]
            assert isinstance(names, list)
            if not names:
                continue
            sh = sum(1 for n in names if n[s]) / len(names)
            shares.append(sh)
            if sh > 0.90 or sh < 0.10:
                extreme += 1
        dead = extreme >= (2 * len(shares)) // 3
        r1[s] = {"mean_share": st.mean(shares), "extreme_months": extreme, "dead": dead}
        report.append(f"| {s} | {100 * st.mean(shares):.1f}% | {extreme}/{len(shares)} | "
                      f"{'DEAD as a filter (R1)' if dead else 'not degenerate'} |")
    rsi_all = [float(n["rsi"]) for m in per_month
               for n in m["names"] if isinstance(n, dict) and float(n["rsi"]) >= 0]  # type: ignore[index]
    bands = {"<30": 0, "30-50": 0, "50-70": 0, ">=70": 0}
    for v in rsi_all:
        key = "<30" if v < 30 else "30-50" if v < 50 else "50-70" if v < 70 else ">=70"
        bands[key] += 1
    tot = sum(bands.values())
    report.append("")
    report.append("RSI-14 distribution across all name-months: "
                  + " · ".join(f"{k} {100 * v / tot:.0f}%" for k, v in bands.items()))
    report.append("")

    # ---- R2 separation (record-only) ---------------------------------------------------------
    rnd = random.Random(SEED)
    report.append("## R2 — forward sector-relative separation (RECORD-ONLY; nothing promotable)")
    report.append("")
    report.append("| state | horizon | months | mean diff (true−false) | se | shuffle pct |")
    report.append("|---|---:|---:|---:|---:|---:|")
    r2: dict[str, dict[int, dict[str, float]]] = defaultdict(dict)
    for s in BINARY_STATES:
        for hz in HORIZONS:
            diffs = []
            month_groups: list[tuple[list[float], list[float]]] = []
            for m in per_month:
                names = m["names"]
                assert isinstance(names, list)
                tv = [float(n[f"rel{hz}"]) for n in names if n.get(f"rel{hz}") is not None and n[s]]
                fv = [float(n[f"rel{hz}"]) for n in names
                      if n.get(f"rel{hz}") is not None and not n[s]]
                if len(tv) >= 5 and len(fv) >= 5:
                    diffs.append(st.mean(tv) - st.mean(fv))
                    month_groups.append((tv, fv))
            if len(diffs) < 6:
                continue
            actual = st.mean(diffs)
            null: list[float] = []
            for _ in range(SHUFFLES):
                sim = []
                for tv, fv in month_groups:
                    pool = tv + fv
                    rnd.shuffle(pool)
                    sim.append(st.mean(pool[:len(tv)]) - st.mean(pool[len(tv):]))
                null.append(abs(st.mean(sim)))
            pct = 100 * sum(1 for x in null if x < abs(actual)) / len(null)
            se = st.stdev(diffs) / len(diffs) ** 0.5
            r2[s][hz] = {"months": len(diffs), "diff": actual, "se": se, "shuffle_pct": pct,
                         "monthly": diffs}
            report.append(f"| {s} | {hz}d | {len(diffs)} | {actual:+.2f} | {se:.2f} | "
                          f"{pct:.0f}% |")
    report.append("")
    # POST-HOC ROBUSTNESS (added after the first run; labelled as such — not pre-registered).
    # At 120/180d horizons adjacent monthly windows OVERLAP (~3/4 and ~5/6 of the window), so
    # monthly diffs are serially correlated and the se above understates uncertainty. Check:
    # split months into k disjoint phases (every k-th month = non-overlapping windows) and ask
    # whether each phase's mean diff carries the same sign.
    report.append("## Post-hoc robustness — non-overlapping phase split (NOT pre-registered)")
    report.append("")
    report.append("| state | horizon | phase means (disjoint windows) | all same sign? |")
    report.append("|---|---:|---|---|")
    for s in BINARY_STATES:
        for hz, k in ((120, 4), (180, 6)):
            cell = r2.get(s, {}).get(hz)
            if not cell:
                continue
            monthly = cell["monthly"]
            assert isinstance(monthly, list)
            phases = [st.mean(monthly[o::k]) for o in range(k) if len(monthly[o::k]) >= 3]
            same = all(x > 0 for x in phases) or all(x < 0 for x in phases)
            report.append(f"| {s} | {hz}d | "
                          + ", ".join(f"{x:+.1f}" for x in phases)
                          + f" | {'YES' if same else 'NO'} |")
    report.append("")

    # ---- R3 cost-of-waiting ------------------------------------------------------------------
    report.append("## R3 — cost of waiting for the 50d-MA reclaim (vs entry at first appearance)")
    report.append("")
    entry: dict[str, int] = {}
    for asof, rows in months:
        i = bars.idx[asof]
        for r in rows:
            t = r["ticker"]
            if t not in entry and bars.cl.get(t) is not None and bars.cl[t][i] > 0:
                entry[t] = i
    strat: dict[str, dict[int, list[float]]] = {"appear": defaultdict(list),
                                                "reclaim": defaultdict(list)}
    reclaim_at: dict[str, int | None] = {}
    mdy = bars.cl["MDY"]
    for t, i in entry.items():
        a = bars.cl[t]
        r_idx: int | None = None
        for k in range(i + 1, min(i + RECLAIM_LIMIT + 1, len(bars.days))):
            if a[k] <= 0:
                continue
            closes, _ = bars.series(t, k)
            if len(closes) >= MA_SHORT and closes[-1] > st.mean(closes[-MA_SHORT:]):
                r_idx = k
                break
        reclaim_at[t] = r_idx
        for hz in HORIZONS:
            j = bars.fwd_index(i, hz)
            if j is None or mdy[i] <= 0 or mdy[j] <= 0:
                continue
            fwd_a = (a[j] / a[i] - 1) * 100 if a[j] > 0 else -100.0
            strat["appear"][hz].append(fwd_a - (mdy[j] / mdy[i] - 1) * 100)
            if r_idx is None or r_idx >= j or a[r_idx] <= 0:
                strat["reclaim"][hz].append(0.0)   # never entered -> no excess either way
            else:
                fwd_b = (a[j] / a[r_idx] - 1) * 100 if a[j] > 0 else -100.0
                strat["reclaim"][hz].append(fwd_b - (mdy[j] / mdy[r_idx] - 1) * 100)
    report.append("| horizon | n | buy at appearance (mean excess vs MDY) | "
                  "wait for reclaim | waiting costs |")
    report.append("|---:|---:|---:|---:|---:|")
    r3: dict[int, dict[str, float]] = {}
    for hz in HORIZONS:
        va, vb = strat["appear"][hz], strat["reclaim"][hz]
        if not va:
            continue
        cost = st.mean(va) - st.mean(vb)
        r3[hz] = {"n": len(va), "appear": st.mean(va), "reclaim": st.mean(vb), "cost": cost}
        report.append(f"| {hz}d | {len(va)} | {st.mean(va):+.2f} | {st.mean(vb):+.2f} | "
                      f"{cost:+.2f} pts |")
    # winners: names up >=50% from appearance to the last session — how much came before reclaim?
    last = len(bars.days) - 1
    shares_before: list[float] = []
    never = 0
    winners = 0
    for t, i in entry.items():
        a = bars.cl[t]
        exit_px = next((a[k] for k in range(last, -1, -1) if a[k] > 0), 0.0)
        if a[i] <= 0 or exit_px <= 0:
            continue
        total = exit_px / a[i] - 1
        if total < 0.50:
            continue
        winners += 1
        r_idx = reclaim_at[t]
        if r_idx is None:
            never += 1
            continue
        before = a[r_idx] / a[i] - 1
        shares_before.append(100 * before / total)
    report.append("")
    report.append(f"Winners (>= +50% from appearance to the last session): {winners}. "
                  f"{never} of them NEVER reclaimed the 50d MA within {RECLAIM_LIMIT} sessions "
                  f"(waiting missed them entirely). Among those that did reclaim, the median share "
                  f"of the total gain already earned BEFORE the reclaim was "
                  f"{st.median(shares_before):.0f}%.")
    report.append("")

    (args.out / "price_states.md").write_text("\n".join(report) + "\n")
    (args.out / "price_states.json").write_text(json.dumps(
        {"r1": r1, "r2": {s: {str(h): v for h, v in d.items()} for s, d in r2.items()},
         "r3": {str(h): v for h, v in r3.items()},
         "winners": {"n": winners, "never_reclaimed": never,
                     "median_share_before_reclaim": st.median(shares_before)
                     if shares_before else None}},
        indent=1))
    print(f"[written] {args.out / 'price_states.md'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
