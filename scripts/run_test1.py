"""Test 1 event study — dual CAR (vs IWM and vs SOXX) for live cross-sections vs controls.

Shock = sector-idiosyncratic for live semis hubs (hub − SOXX), market-idiosyncratic for famous
controls (hub − IWM). Dependent CAR is measured BOTH vs IWM (includes sector co-movement) and vs
SOXX (sector-adjusted — the deciding number). The gap between them is the finding.
"""

from __future__ import annotations

import json
import os
import pathlib
import statistics

from vinci.config import get_config
from vinci.graph.coverage import shared_node_map
from vinci.graph.test1 import cumulative_abnormal_return, detect_shocks
from vinci.resolver import EntityResolver
from vinci.store import Store
from vinci.universe import benchmark_identity

CONTROL = {"AAPL", "AMZN", "WMT"}  # famous, saturated-coverage hubs → priced fast
LIVE = {"TSM", "AMAT", "LRCX", "STM", "INTC", "MU", "GFS", "JBL", "PLXS"}  # semis live test
WINDOWS = [(1, 5), (1, 10), (1, 20)]

# NO `main()` HERE — this file runs at module level, so the chdir goes before the first
# data-root read rather than in a `__main__` block. Nothing imports it (checked); if
# anything ever does, give it a main() first.
os.chdir(pathlib.Path(__file__).resolve().parents[1])
cfg = get_config()
r = EntityResolver.from_config(cfg)
with open("data/graph_coverage.json") as _f:
    d = json.load(_f)
sn = shared_node_map(
    [e for e in d["edges"] if e["verdict"] == "real_supply_chain"], super_connector_degree=8
)["shared_nodes"]


def _bars(store: Store, ticker: str) -> list:
    try:
        return store.get_price_history(r.resolve_ticker(ticker).internal_id)
    except Exception:
        return []


with Store(cfg.db_path) as store:
    iwm = store.get_price_history(benchmark_identity("IWM").internal_id)
    soxx = store.get_price_history(benchmark_identity("SOXX").internal_id)
    barcache: dict[str, list] = {}

    def bars(t: str) -> list:
        if t not in barcache:
            barcache[t] = _bars(store, t)
        return barcache[t]

    # cohort -> window -> list of (car_vs_iwm, car_vs_soxx)
    obs: dict[str, dict[tuple[int, int], list[tuple[float, float]]]] = {
        "LIVE": {w: [] for w in WINDOWS},
        "CONTROL": {w: [] for w in WINDOWS},
    }
    n_shocks = {"LIVE": 0, "CONTROL": 0}
    for node in sn:
        hub = node["ticker"]
        if hub in LIVE:
            cohort, shock_bench = "LIVE", soxx  # sector-idiosyncratic
        elif hub in CONTROL:
            cohort, shock_bench = "CONTROL", iwm  # market-idiosyncratic
        else:
            continue
        hub_bars = bars(hub)
        if not hub_bars:
            continue
        shocks = detect_shocks(hub, hub_bars, shock_bench)
        n_shocks[cohort] += len(shocks)
        for s in shocks:
            for dep in node["focals"]:
                db = bars(dep)
                if not db:
                    continue
                for w in WINDOWS:
                    ci = cumulative_abnormal_return(db, iwm, s.shock_date, lo=w[0], hi=w[1])
                    cs = cumulative_abnormal_return(db, soxx, s.shock_date, lo=w[0], hi=w[1])
                    if ci is not None and cs is not None:
                        obs[cohort][w].append((ci, cs))

print("Test 1 — post-shock dependent CAR (mean / median), de-confounded by sector adjustment\n")
hdr = f"{'cohort':<9}{'window':<9}{'n':>5}   {'CAR vs IWM':>20}   {'CAR vs SOXX (decides)':>22}"
print(hdr)
print("-" * len(hdr))
for cohort in ("LIVE", "CONTROL"):
    print(f"{cohort}  ({n_shocks[cohort]} shocks)")
    for w in WINDOWS:
        rows = obs[cohort][w]
        if not rows:
            print(f"  {'':<7}[D+{w[0]},+{w[1]}]   0")
            continue
        ci = [a for a, _ in rows]
        cs = [b for _, b in rows]
        print(
            f"  {'':<7}[D+{w[0]},+{w[1]}]{len(rows):>5}   "
            f"{statistics.mean(ci):>+8.1%} / {statistics.median(ci):>+7.1%}   "
            f"{statistics.mean(cs):>+9.1%} / {statistics.median(cs):>+8.1%}"
        )
