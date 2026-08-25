"""Pre-registered falsifier: does industry co-movement carry actionable signal for the queue?

MEASURE-FIRST, NOTHING BUILT. Recorded in STATE.md as the 2026-08-25 experiment record. Run from
COMMITTED DATA ALONE — no store, no keys, no network, and no forward returns are read at any point
(this measures de-confounding, never what would have paid).

THE QUESTION. G2 strips MARKET beta (name vs IWM) but not SECTOR, so a name that fell with its
whole industry still lands in the candidate set looking idiosyncratic — PR #84 named this on
2026-07-06 and nothing closed it. Decompose each name's `rel_ret_vs_market` into its industry
cohort's median plus a residual, and ask whether either half is stable enough to act on.

WHY THE COHORT MEDIAN IS UNBIASED. `screen_runs/*.jsonl` at `grain=candidate` logs the gate inputs
for every universe member that reached the gates — PASS AND FAIL. Taking the median over that full
set, rather than over admitted candidates, keeps the cohort from being defined by the very selection
being tested.

TWO CONTROLS, because a stability claim without one is decoration:
  * three SAME-DAY runs on 2026-07-29 — must read ~0, and does (corr 0.998, 0 sign flips);
  * the 2-day 08-12 -> 08-14 gap as the NOISE FLOOR that real intervals are judged against.

    python scripts/cohort_decomposition_falsifier.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import statistics as st

from vinci.sectors import industry_for_sic

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"
#: Dated snapshots, oldest first. 07-29-03 is the last of three same-day runs; -01 is its control.
RUNS = ("2026-07-29-03", "2026-08-12-01", "2026-08-14-01", "2026-08-24-01")
SAME_DAY = ("2026-07-29-01", "2026-07-29-03")
NOISE_FLOOR = ("2026-08-12-01", "2026-08-14-01")
MIN_COHORT = 6          # below this a median is not a cohort, it is an anecdote
DOWN = -0.15            # "a human would look at this" — the G2 threshold itself
NEAR_TIE = 0.10         # |cohort|-|residual| under this is a coin-flip -> UNRESOLVED


def _sic_by_ticker() -> dict[str, str | None]:
    return {r.get("ticker"): r.get("sic")
            for r in (json.loads(x) for x in (SNAP / "securities.jsonl").read_text().splitlines()
                      if x.strip())}


def relative_returns(run: str) -> dict[str, float]:
    """`rel_ret_vs_market` for every name that reached the gates in ``run`` — pass and fail."""
    out: dict[str, float] = {}
    for line in (SNAP / "screen_runs" / f"{run}.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("grain") != "candidate":
            continue
        v = ((row.get("gate_inputs") or {}).get("rel_ret_vs_market") or {}).get("value")
        if v is not None:
            out[row["ticker"]] = v
    return out


def decompose(run: str, sic: dict[str, str | None]) -> dict[str, tuple[float, float]]:
    """ticker -> (cohort median, residual). A cohort under MIN_COHORT is dropped, never faked."""
    rel = relative_returns(run)
    grouped: dict[str, list[float]] = collections.defaultdict(list)
    for t, v in rel.items():
        grouped[industry_for_sic(sic.get(t))].append(v)
    med = {k: st.median(v) for k, v in grouped.items() if len(v) >= MIN_COHORT}
    return {t: (med[industry_for_sic(sic.get(t))], v - med[industry_for_sic(sic.get(t))])
            for t, v in rel.items() if industry_for_sic(sic.get(t)) in med}


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else float("nan")


def main() -> int:
    sic = _sic_by_ticker()
    dec = {r: decompose(r, sic) for r in (*RUNS, SAME_DAY[0])}

    print("STABILITY OF THE RESIDUAL  (controls first — a claim without one is decoration)")
    pairs = ((SAME_DAY, "same day (control)"), (NOISE_FLOOR, "2 days (noise floor)"),
             ((RUNS[0], RUNS[1]), "14 days"), ((RUNS[2], RUNS[3]), "10 days"))
    for (a, b), label in pairs:
        common = sorted(set(dec[a]) & set(dec[b]))
        # FAIL LOUD, never print a divide-by-zero traceback as if the measurement had run. Two runs
        # with no shared cohorted name means the snapshot set changed under the script, not that
        # the stability is 0 — say which pair, and stop.
        if not common:
            raise SystemExit(f"{label}: {a} and {b} share no cohorted name — the run set changed")
        ra = [dec[a][t][1] for t in common]
        rb = [dec[b][t][1] for t in common]
        flips = sum(1 for x, y in zip(ra, rb, strict=True) if x * y < 0)
        delta = st.median([abs(x - y) for x, y in zip(ra, rb, strict=True)])
        print(f"  {label:<22} n={len(common):>5}  corr={_pearson(ra, rb):>6.3f}  "
              f"med|delta|={delta:>5.1%}  sign-flips={flips / len(common):>4.0%}")

    print("\nFALSIFIED — RESIDUAL AS A RE-RANKING KEY (top-25 overlap, higher = more stable)")
    for a, b in zip(RUNS, RUNS[1:], strict=False):
        def top(run: str, residual: bool) -> set[str]:
            s = {t: (v[1] if residual else v[0] + v[1]) for t, v in dec[run].items()}
            return {t for t, _ in sorted(s.items(), key=lambda kv: kv[1])[:25]}
        raw = len(top(a, False) & top(b, False)) / 25
        res = len(top(a, True) & top(b, True)) / 25
        verdict = "residual WORSE" if res < raw else "residual better"
        print(f"  {a[5:10]} -> {b[5:10]}   raw={raw:>4.0%}  residual={res:>4.0%}   {verdict}")

    print("\nSURVIVES — THE CALL, CONDITIONED ON MARGIN")
    common = set.intersection(*[set(dec[r]) for r in RUNS])
    # every run down >DOWN, so threshold-crossing churn cannot masquerade as an unstable call
    pool = [t for t in common if all(sum(dec[r][t]) <= DOWN for r in RUNS)]

    def call(t: str, r: str) -> str:
        c, s = dec[r][t]
        return "cohort" if abs(c) > abs(s) else "idio"

    labs = {t: {call(t, r) for r in RUNS} for t in pool}
    stable = [t for t in pool if len(labs[t]) == 1]
    ctrl = sum(1 for t in pool if call(t, NOISE_FLOOR[0]) == call(t, NOISE_FLOOR[1]))
    print(f"  {len(pool)} names down >{abs(DOWN):.0%} vs IWM in ALL FOUR runs")
    print(f"  same call all four times: {len(stable) / len(pool):.0%}   "
          f"(2-day control {ctrl / len(pool):.0%})")
    for lo, hi, name in ((0.0, NEAR_TIE, f"near-tie  (<{NEAR_TIE:.0%})"),
                         (NEAR_TIE, 0.25, "clear     (10-25pt)"),
                         (0.25, 9.99, "decisive  (>25pt)")):
        grp = [t for t in pool
               if lo <= abs(abs(dec[RUNS[-1]][t][0]) - abs(dec[RUNS[-1]][t][1])) < hi]
        if grp:
            ok = sum(1 for t in grp if len(labs[t]) == 1) / len(grp)
            print(f"    {name:<22} n={len(grp):>3}  stable {ok:>4.0%}")
    print("\n  -> a near-tie must report UNRESOLVED, never a forced call "
          "(the rule `mixed` already follows).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
