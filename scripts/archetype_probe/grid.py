"""One GRID archetype per company, by stated precedence, with its weight in each band.

Precedence (first match wins): no annual report → FPI IFRS → FPI US GAAP non-USD → FPI US GAAP USD
(then by form when not an operating company) → statement form (non-operating forms) → economic
model (operating companies). A 10-K filer whose incorporation is blank counts as 10-K."""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from probe_common import OUT

C = json.loads((OUT / "census.json").read_text())


def grid_arch(x: dict) -> str:
    r, f, m = x["regime"], x["form"], x["model"]
    if r.startswith("no annual") or r.startswith("UNREAD"):
        return "G20 no annual report on file (new registrant / successor)"
    if r.startswith("FPI"):
        if "IFRS" in r:
            return "G19 FPI · IFRS (any form)"
        if "US GAAP, USD" not in r:
            return "G18 FPI · US GAAP non-USD (or unread)"
        return (
            "G17 FPI · US GAAP USD · operating"
            if f == "operating company"
            else "G17b FPI · US GAAP USD · financial/other form"
        )
    forms = {
        "bank": "G06 bank",
        "lender / specialty finance": "G07 lender / specialty finance",
        "insurer (underwriting)": "G08 insurer",
        "managed care (SIC 6324)": "G09 managed care",
        "broker-dealer / investment bank": "G10 broker-dealer / IB",
        "asset manager / exchange": "G11 asset manager / exchange",
        "insurance broker": "G12 insurance broker",
        "REIT": "G13 REIT (SIC 6798)",
        "real-estate operator / developer": (
            "G13b real-estate operator (65xx; INVH-type REITs inside)"
        ),
        "regulated utility": "G14 regulated utility",
        "partnership / MLP": "G15 partnership / MLP",
        "royalty / patent owner": "G16 royalty / patent owner",
        "holding / investment office": "G16b holding / investment office",
    }
    if f in forms:
        return forms[f]
    return {
        "operating, positive operating income in a recent year": (
            "G01 PROVEN PATH · 10-K operating, positive OI"
        ),
        "profitable-or-unknown, OperatingIncomeLoss untagged": "G02 10-K operating · OI untagged",
        "pre-profit (operating loss CY2024 and CY2025)": "G03 10-K operating · pre-profit",
        "pre-revenue (< $10M revenue CY2024 and CY2025)": "G04 10-K operating · pre-revenue",
        "reserve-based (mining / E&P)": "G05 10-K operating · reserve-based",
        "no CY2024/25 us-gaap USD frame data": (
            "G05b 10-K operating · no USD frame data (non-USD 10-K / short history)"
        ),
    }.get(m or "", f"G?? {f} / {m}")


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
