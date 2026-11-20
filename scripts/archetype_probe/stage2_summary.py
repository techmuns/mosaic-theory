"""Summarise out/stage2.json: one status per name, then counts by market. Status rules (stated):
- CURRENT SEC REPORTER: a candidate CIK whose latest annual (10-K/20-F/40-F) was filed on or after
  2025-06-01; classed by companyfacts namespace (IFRS when ifrs-full holds more concepts than
  us-gaap) and `concepts.reporting_currency`.
- LAPSED SEC REPORTER: latest annual before 2025-06-01.
- SEC CIK, NO REPORTS: a CIK in SEC's ticker files (an OTC line) with no annual report and no
  companyfacts — the Rule 12g3-2(b)-style case.
- NOT FOUND: no CIK by ticker or name substring AND no self-filed hit in full-text search (first
page)."""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from probe_common import OUT

BAD_MATCH = {
    "0001695295",
    "0000887028",
}  # Hydrofarm (substring 'ARM HOLDINGS'); Rio Tinto Ltd (OTC twin)
R = json.loads((OUT / "stage2.json").read_text())
rows = []
for r in R:
    st, detail = None, ""
    filers = [f for f in r.get("filers", []) if f["cik"] not in BAD_MATCH]
    cur_rep = [
        f for f in filers if f.get("latest_annual") and f["latest_annual"][1] >= "2025-06-01"
    ]
    if cur_rep:
        f = cur_rep[0]
        ns = f.get("ns_concepts") or {}
        fy = f.get("fiscal_year") or {}
        # IFRS when the filer's NEWEST fiscal year is an ifrs-full one (`filer_fiscal_year`'s
        # ifrs_end reaches its end) — a concept count misreads a filer that moved to IFRS (Toyota)
        ifrs = bool(fy.get("ifrs_end") and fy.get("end") and fy["ifrs_end"] >= fy["end"]) or str(
            fy.get("tag", "")
        ).startswith("ifrs-full")
        if not ns:
            st = f"SEC {f['latest_annual'][0]} · no companyfacts (404)"
            detail = f"{f['cik']} {f['latest_annual'][0]} {f['latest_annual'][1]}"
            rows.append((r["market"], r["name"], st, detail))
            continue
        cur = f.get("reporting_currency")
        form = f["latest_annual"][0]
        st = f"SEC {form} · IFRS" if ifrs else f"SEC {form} · US GAAP {cur or '?'}"
        detail = (
            f"{f['cik']} {form} {f['latest_annual'][1]}; 6-K/365d {f.get('n_6k_365')}; "
            f"fye {f.get('fye')}"
        )
    elif any(f.get("latest_annual") for f in filers):
        f = next(f for f in filers if f.get("latest_annual"))
        st = "LAPSED SEC reporter"
        detail = f"last {f['latest_annual'][0]} {f['latest_annual'][1]}; OTC {f.get('tickers')}"
    elif filers:
        st = "SEC CIK, no reports (OTC line only)"
        detail = f"{filers[0]['cik']} {filers[0].get('tickers')}"
    else:
        st = "NOT FOUND (ticker, name, full-text)"
        detail = f"fts hits read {r.get('fts_hits_read')}, self-filer 0"
    rows.append((r["market"], r["name"], st, detail))

by_m = defaultdict(Counter)
for m, _n, st, _d in rows:
    key = m.split("-")[0]
    by_m[key][st] += 1
print(
    "| market | names | "
    + " | ".join(sorted({st for *_, st, _ in [(0, 0, s, 0) for s in {x[2] for x in rows}]}))
    + " |"
)
cols = sorted({x[2] for x in rows})
print("| market | n | " + " | ".join(cols) + " |")
print("|---|---|" + "---|" * len(cols))
tot = Counter()
for m in sorted(by_m):
    c = by_m[m]
    tot.update(c)
    print(f"| {m} | {sum(c.values())} | " + " | ".join(str(c.get(k, 0)) for k in cols) + " |")
print(f"| all | {sum(tot.values())} | " + " | ".join(str(tot.get(k, 0)) for k in cols) + " |")
print()
for m, n, st, d in rows:
    print(f"| {m} | {n} | {st} | {d} |")
(OUT / "stage2_rows.json").write_text(json.dumps(rows, indent=1))
