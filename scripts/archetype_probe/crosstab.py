"""Cross-tabs over out/census.json: the proven-path count, model x regime, REIT-like balance sheets
outside SIC 6798, and the operator's named names' census rows."""

from __future__ import annotations

import json
from collections import Counter

from probe_common import OUT

C = json.loads((OUT / "census.json").read_text())
F = {}
for p in (OUT / "frames").glob("*.json"):
    _ns, concept, _u, period = p.stem.split("__")
    F[f"{concept}@{period}"] = json.loads(p.read_text())

DOM = ("10-K, US-incorporated", "10-K, foreign-incorporated")
PROVEN = "operating, positive operating income in a recent year"


def cap(x, band=None):
    return x["caps"][band] if band else max(x["caps"].values())


for band in ("primary", "theme", None):
    pop = [x for x in C if band is None or band in x["bands"]]
    tot_n, tot_c = len(pop), sum(cap(x, band) for x in pop)
    pp = [
        x
        for x in pop
        if x["regime"] in DOM and x["form"] == "operating company" and x["model"] == PROVEN
    ]
    pp_c = sum(cap(x, band) for x in pp)
    lbl = band or "union"
    print(
        f"\n[{lbl}] PROVEN PATH (10-K filer x operating company x positive recent operating "
        "income): "
        f"{len(pp)} of {tot_n} ({len(pp) / tot_n:.1%}), cap {pp_c / tot_c:.1%}"
    )
    # of which carry a share-count or OI caveat
    sc = sum(
        1
        for x in pp
        if any(
            f.startswith(("multiple share classes", "no filed point-in-time")) for f in x["flags"]
        )
    )
    print(f"   of which flagged share-count unreadable/approximate: {sc}")
    ops = [x for x in pop if x["form"] == "operating company"]
    ct = Counter((x["regime"].split(" —")[0], x["model"]) for x in ops)
    print(f"   operating companies, model x regime ({len(ops)}):")
    for (r, m), n in sorted(ct.items(), key=lambda kv: -kv[1])[:14]:
        print(f"     {n:5d}  {r:38s} | {m}")
    if len(ct) > 14:
        print(f"     …showing 14 of {len(ct)} cells")

# REIT-like balance sheets outside SIC 6798
reit_like = []
for x in C:
    a = F.get("Assets@CY2025Q4I", {}).get(x["cik"])
    re_ = F.get("RealEstateInvestmentPropertyNet@CY2025Q4I", {}).get(x["cik"])
    if a and re_ and re_ / a >= 0.5 and x["sic"] != "6798":
        reit_like.append((x["ticker"], x["sic"], x["form"], round(re_ / a, 2)))
print(f"\nRealEstateInvestmentPropertyNet >= 50% of assets but SIC != 6798: {len(reit_like)}")
print(
    "  ",
    sorted(reit_like, key=lambda r: r[0])[:25],
    f"…showing {min(25, len(reit_like))} of {len(reit_like)}",
)
six798 = [x for x in C if x["sic"] == "6798"]
with_tag = sum(
    1 for x in six798 if F.get("RealEstateInvestmentPropertyNet@CY2025Q4I", {}).get(x["cik"])
)
print(
    f"SIC 6798 companies: {len(six798)}; carrying RealEstateInvestmentPropertyNet at CY2025Q4I: "
    f"{with_tag}"
)

NAMED = [
    "TTWO",
    "EL",
    "BRBR",
    "HSY",
    "LLY",
    "ISRG",
    "GILD",
    "PFE",
    "SPGI",
    "FICO",
    "FDS",
    "VRSK",
    "BRK-B",
    "MORN",
    "INVH",
    "AVB",
    "LOW",
    "ORCL",
    "CRWV",
    "NBIS",
]
print("\nOperator-named names in the committed universes:")
by_t = {x["ticker"]: x for x in C}
for t in NAMED:
    x = by_t.get(t)
    if not x:
        print(f"  {t:6s} — not in either committed universe")
        continue
    print(
        f"  {t:6s} {','.join(x['bands']):14s} {x['regime']:28s} | {x['form']:22s} | "
        f"{x['model'] or '-':52s} | "
        f"{'; '.join(f.split(' (')[0] for f in x['flags'])[:160]}"
    )
