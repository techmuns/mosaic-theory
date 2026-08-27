"""Build the COHORT POOL — the peers an industry's move is measured over.

WHY IT EXISTS. The cohort was drawn only from names that reached the screen's gates, i.e. the
cap-banded $300M–$10B universe. So "what the software industry did" was computed from small-cap
software alone. Measured on SIC 7372 (2026-08-26): the narrow pool reads **+14% vs IWM**, the full
industry — the same names plus ADBE, ADSK, NOW, CRM, VEEV — reads **−6%**. A twenty-point swing,
and it flips the sign. Every queued software name's "own" move was overstated by that much: GTM
−63% narrow vs −43% wide.

The operator's example is the shape of it: GWRE fell alongside NOW, CRM and VEEV in the 2026
software de-rate, and NONE of those three are in the screened universe — so nothing in the cohort
could see the industry it fell with.

WHY THIS IS A SEPARATE STEP AND NOT A CHANGE TO THE SCREEN. `universe.py` drops `out_of_band`
BEFORE it fetches SIC, deliberately: there is no reason to spend an EDGAR call on a name already
rejected. Moving that fetch earlier would put ~2,900 calls on the screen's critical path and change
control flow in the module that decides what gets screened. This builds the pool AFTERWARDS, from
committed artifacts, and writes its own snapshot. The pool is a MEASUREMENT input; it cannot reach
selection, and keeping it outside `universe.py` is what makes that structural rather than a promise.

THE WINDOW IS READ FROM THE SCREEN, NEVER RECOMPUTED. Each screen run records its own
(`window 2026-02-25→2026-08-24 …`), and the pool uses exactly that, so a pool return and a screen
return are the same measurement. Verified on all 1,755 screened names: median, p90 and max
difference all **0.000%**.

ADRs AND FOREIGN ISSUERS ARE INCLUDED — operator ruling 2026-08-26. An industry's move is the
industry's wherever the issuer is domiciled; the fund still only BUYS US names. This changes the
yardstick, not the shopping list.

    python scripts/build_cohort_pool.py            # extend the pool for the newest screen run
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"
OUT = SNAP / "cohort_pool.jsonl"

#: Stages whose names are worth adding: they exist and trade, they are simply outside the BAND or
#: below the work floor. `no_price` / `no_shares` cannot contribute a return at all, and the SIC
#: denylist stages are excluded for the same reason the screen excludes them.
POOLABLE = ("out_of_band", "below_adv_floor")

#: The screen's own denylist, mirrored — a non-operating issuer is not part of an industry's move.
EXCLUDED_SIC = ("6189", "6221", "6722", "6726", "6770")


def window_from(run: pathlib.Path) -> tuple[dt.date, dt.date]:
    """The EXACT window the screen used, read off its own log rather than recomputed."""
    for line in run.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        note = ((row.get("gate_inputs") or {}).get("rel_ret_vs_market") or {}).get("note") or ""
        m = re.search(r"window (\d{4}-\d\d-\d\d)→(\d{4}-\d\d-\d\d)", note)
        if m:
            return dt.date.fromisoformat(m.group(1)), dt.date.fromisoformat(m.group(2))
    raise SystemExit(f"no window recorded in {run.name} — cannot match the screen's measurement")


def main(argv: list[str]) -> int:
    from vinci.config import get_config, load_local_env
    load_local_env()
    from vinci.eod import PolygonEodClient
    from vinci.monitor import BENCHMARK_SMALL
    from vinci.resolver import EntityResolver

    cfg = get_config()
    runs = sorted((SNAP / "screen_runs").glob("*.jsonl"))
    if not runs:
        print("no committed screen runs", file=sys.stderr)
        return 1
    run = runs[-1]
    start, end = window_from(run)
    run_id = run.stem
    print(f"  screen run {run_id} · window {start} -> {end} (read from the run, not recomputed)")

    already = set()
    if OUT.is_file():
        already = {json.loads(x)["ticker"] for x in OUT.read_text().splitlines()
                   if x.strip() and json.loads(x)["run_id"] == run_id}
        if already:
            print(f"  {len(already)} names already pooled for this run")

    wanted = []
    for line in run.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if (row.get("grain") == "universe" and row.get("stage") in POOLABLE
                and row["ticker"] not in already):
            wanted.append(row["ticker"])
    print(f"  {len(wanted)} names dropped at {'/'.join(POOLABLE)} to resolve")

    client = PolygonEodClient.from_config(cfg)
    bars_end, bars_start = client.grouped_daily(end), client.grouped_daily(start)
    bench = bars_end[BENCHMARK_SMALL].close / bars_start[BENCHMARK_SMALL].close - 1
    print(f"  {BENCHMARK_SMALL} over the window: {bench:+.1%} "
          f"(2 grouped-daily calls, whole market)")

    resolver = EntityResolver.from_config(cfg)
    written = skipped_sic = skipped_px = 0
    with OUT.open("a") as fh:
        for i, ticker in enumerate(wanted, 1):
            if ticker not in bars_end or ticker not in bars_start or not bars_start[ticker].close:
                skipped_px += 1
                continue
            try:
                sic, _ = resolver.sic_for(resolver.resolve_ticker(ticker).cik)
            except Exception:
                sic = None
            if not sic or sic in EXCLUDED_SIC:
                skipped_sic += 1
                continue
            rel = (bars_end[ticker].close / bars_start[ticker].close - 1) - bench
            fh.write(json.dumps({"run_id": run_id, "ticker": ticker, "sic": sic,
                                 "rel_ret_vs_market": rel, "as_of": end.isoformat(),
                                 "window_start": start.isoformat(),
                                 "source": "grouped-daily endpoints, screen window"},
                                sort_keys=True) + "\n")
            written += 1
            if i % 500 == 0:
                print(f"    {i}/{len(wanted)} · written {written}", flush=True)
    print(f"\n  WROTE {written} pool rows · skipped {skipped_sic} (no/denylisted SIC), "
          f"{skipped_px} (no price at a window endpoint)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
