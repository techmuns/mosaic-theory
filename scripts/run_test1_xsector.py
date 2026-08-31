"""Test 1, cross-sector read — the cheap DECISION INPUT for extend-vs-park (NOT a moat verdict).

Cross-sector cross-sections: a hub whose dependents sit in DIFFERENT sectors, so a post-shock
co-move can't be common sector beta. Each dependent's CAR is reported BOTH vs IWM (market) and vs
its OWN sector ETF (documented map) — the own-sector number de-confounds a shared-factor cluster
(e.g. the two defense dependents both ride ITA). Degree is low-single-digit, so this is
DIRECTIONAL-ONLY, n labelled, and the one positive cross-section is never mined.
"""

from __future__ import annotations

import os
import pathlib
import statistics

from vinci.config import get_config
from vinci.graph.test1 import cumulative_abnormal_return, detect_shocks
from vinci.resolver import EntityResolver
from vinci.store import Store
from vinci.universe import benchmark_identity

# hub -> [(dependent, its own sector ETF)] — documented; genuinely cross-sector cross-sections.
XSECTOR = {
    "PCG": [("ATEN", "XLK"), ("NRGV", "ICLN")],  # utility hub → networking + energy-storage
    "NOC": [("FEIM", "ITA"), ("LASR", "ITA")],  # defense prime → defense-electronics (share ITA)
    "RTX": [("KOPN", "ITA"), ("LASR", "ITA")],  # aero/defense → defense-electronics
    "TM": [("AIOT", "XLK"), ("CTS", "XLI")],  # auto → telematics + components
    "AMZN": [("CRSR", "XLK"), ("NN", "XLI"), ("SPB", "XLP")],  # retail → gaming/industrial/consumer
}
LO, HI = 1, 10

# NO `main()` HERE — this file runs at module level, so the chdir goes before the first
# data-root read rather than in a `__main__` block. Nothing imports it (checked); if
# anything ever does, give it a main() first.
os.chdir(pathlib.Path(__file__).resolve().parents[1])
cfg = get_config()
r = EntityResolver.from_config(cfg)


def _bars(store: Store, ticker: str, *, etf: bool = False) -> list:
    ident = benchmark_identity(ticker) if etf else r.resolve_ticker(ticker)
    return store.get_price_history(ident.internal_id)


with Store(cfg.db_path) as store:
    iwm = _bars(store, "IWM", etf=True)
    print("Test 1 cross-sector — dependent post-shock CAR [D+1,+10] (mean/median), n labelled\n")
    hdr = f"{'cross-section':<22}{'n':>4}   {'CAR vs IWM':>18}   {'CAR vs own-sector':>20}"
    print(hdr + "\n" + "-" * len(hdr))
    pooled_iwm: list[float] = []
    pooled_sec: list[float] = []
    for hub, deps in XSECTOR.items():
        hub_bars = _bars(store, hub)
        shocks = detect_shocks(hub, hub_bars, iwm)  # market-idiosyncratic hub move
        ci_all: list[float] = []
        cs_all: list[float] = []
        for dep, etf in deps:
            db = _bars(store, dep)
            sec = _bars(store, etf, etf=True)
            for s in shocks:
                ci = cumulative_abnormal_return(db, iwm, s.shock_date, lo=LO, hi=HI)
                cs = cumulative_abnormal_return(db, sec, s.shock_date, lo=LO, hi=HI)
                if ci is not None and cs is not None:
                    ci_all.append(ci)
                    cs_all.append(cs)
        label = f"{hub}<-{'/'.join(d for d, _ in deps)}"
        if not ci_all:
            print(f"{label[:22]:<22}{0:>4}")
            continue
        pooled_iwm += ci_all
        pooled_sec += cs_all
        print(
            f"{label[:22]:<22}{len(ci_all):>4}   "
            f"{statistics.mean(ci_all):>+8.1%}/{statistics.median(ci_all):>+7.1%}   "
            f"{statistics.mean(cs_all):>+9.1%}/{statistics.median(cs_all):>+8.1%}"
        )
    print("-" * len(hdr))
    print(
        f"{'POOLED':<22}{len(pooled_iwm):>4}   "
        f"{statistics.mean(pooled_iwm):>+8.1%}/{statistics.median(pooled_iwm):>+7.1%}   "
        f"{statistics.mean(pooled_sec):>+9.1%}/{statistics.median(pooled_sec):>+8.1%}"
    )
