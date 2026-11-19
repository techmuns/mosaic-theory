"""One GRID archetype per company, by stated precedence, with its weight in each band.

Precedence (first match wins): no annual report → FPI IFRS → FPI US GAAP non-USD → FPI US GAAP USD
(then by form when not an operating company) → statement form (non-operating forms) → economic
model (operating companies). A 10-K filer whose incorporation is blank counts as 10-K."""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from probe_common import OUT, grid_arch

C = json.loads((OUT / "census.json").read_text())


rows = defaultdict(
    lambda: {
        "primary": 0,
        "theme": 0,
        "union": 0,
        "cap_u": 0.0,
        "cap_p": 0.0,
        "cap_t": 0.0,
        "eg": [],
    }
)
tot = Counter()
capt = Counter()
for x in C:
    g = grid_arch(x)
    x["grid"] = g
    row = rows[g]
    row["union"] += 1
    row["cap_u"] += max(x["caps"].values())
    for b in x["bands"]:
        row[b] += 1
        row["cap_p" if b == "primary" else "cap_t"] += x["caps"][b]
        tot[b] += 1
        capt[b] += x["caps"][b]
    tot["union"] += 1
    capt["union"] += max(x["caps"].values())
    if len(row["eg"]) < 4 and x.get("ticker"):
        row["eg"].append(x["ticker"])
print(
    "| grid archetype | screen band n (%) | screen cap % | large-cap band n (%) | large-cap cap % "
    "| union n | e.g. |"
)
print("|---|---|---|---|---|---|---|")
for g in sorted(rows):
    r = rows[g]
    print(
        f"| {g} | {r['primary']} ({r['primary'] / tot['primary']:.1%}) | "
        f"{r['cap_p'] / capt['primary']:.1%} | "
        f"{r['theme']} ({r['theme'] / tot['theme']:.1%}) | {r['cap_t'] / capt['theme']:.1%} | "
        f"{r['union']} | "
        f"{', '.join(r['eg'])} |"
    )
print(
    f"| **total** | {tot['primary']} | ${capt['primary'] / 1e12:,.2f}T | {tot['theme']} | "
    f"${capt['theme'] / 1e12:,.2f}T | {tot['union']} | |"
)
(OUT / "census_grid.json").write_text(json.dumps({x["cik"]: x["grid"] for x in C}))
