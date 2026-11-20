"""5a, RIVN: what RIVN FILED for the row CIQ's LTM check refuses ('Gain (Loss) On Sale Of Invest.').
Every us-gaap duration fact whose tag names a gain/loss on investments / sale / disposal / equity
securities / deconsolidation, with an end date from 2025-01-01, filed by 2026-11-19 — through the
repo's EDGAR client (companyfacts, cached). All matching tags printed; values in $M."""

from __future__ import annotations

import datetime as dt
import re

from probe_common import edgar

CIK = "0001874178"
PAT = re.compile(
    r"(Gain|Loss).*(Invest|Sale|Dispos|Securit|Deconsolid|Divest)|"
    r"(Invest|Securit).*(Gain|Loss)",
    re.I,
)


def main() -> None:
    import vinci

    print("vinci:", vinci.__file__)
    f = edgar().companyfacts(CIK)
    gaap = f["facts"]["us-gaap"]
    tags = sorted(t for t in gaap if PAT.search(t))
    print(f"{len(tags)} matching tag(s); every one listed")
    for t in tags:
        rows = []
        for unit, rs in gaap[t]["units"].items():
            if unit != "USD":
                continue
            for r in rs:
                if not r.get("start"):
                    continue
                en = dt.date.fromisoformat(r["end"])
                if en >= dt.date(2025, 1, 1):
                    days = (en - dt.date.fromisoformat(r["start"])).days
                    rows.append((r["end"], days, r["val"] / 1e6, r["form"], r["filed"], r["accn"]))
        rows = sorted(set(rows))
        print(f"== {t}: {len(rows)} fact(s) ending ≥2025-01-01")
        for e, d, v, form, filed, acc in rows:
            print(f"   end {e} ({d:>3}d) {v:>10,.1f}  {form:5} filed {filed}  {acc}")


if __name__ == "__main__":
    main()
