"""SP-D21's population: the G17/G17b names (FPI, US GAAP, USD) and the proxies the data held offers
for a home-market primary listing. CIQ's primary listing is NOT in this data, so nothing here counts
affected names; it states what EDGAR's submissions carry. Reads `<OUT>/census.json` (classify.py)
and
`<OUT>/subs_extract.jsonl` (census_fetch.py); fetches nothing.

    python scripts/archetype_probe/aqnclass5b.py
"""

from __future__ import annotations

import json
from collections import Counter

from probe_common import OUT, grid_code

US_VENUES = {"NYSE", "Nasdaq", "OTC", "NYSE American", "NYSE MKT", "CBOE"}


def main() -> None:
    import vinci

    print("vinci:", vinci.__file__)
    subs = {}
    for line in (OUT / "subs_extract.jsonl").read_text().splitlines():
        if line.strip():
            o = json.loads(line)
            subs[o["cik"]] = o
    census = json.loads((OUT / "census.json").read_text())
    g = [x for x in census if grid_code(x) in ("G17", "G17b")]
    print(
        f"POPULATION: G17 + G17b, union of both bands: {len(g)} | screen band "
        f"{sum('primary' in x['bands'] for x in g)} | large-cap band "
        f"{sum('theme' in x['bands'] for x in g)}"
    )
    non_us = [x["ticker"] for x in g if set(subs[x["cik"]].get("exchanges") or []) - US_VENUES]
    print(f"EDGAR exchanges field lists a non-US venue: {len(non_us)} of {len(g)} {sorted(non_us)}")
    f40 = sorted(x["ticker"] for x in g if x["latest_annual"][0] == "40-F")
    print(f"40-F filers: {len(f40)} {f40}")
    can = sorted(
        (x["ticker"], x["latest_annual"][0])
        for x in g
        if "Canada" in (subs[x["cik"]].get("inc_desc") or "")
    )
    print(f"incorporated in Canada (EDGAR inc_desc): {len(can)} {can}")
    ads = sorted(x["ticker"] for x in g if any("depositary" in f for f in x["flags"]))
    print(f"with an ADS line: {len(ads)} {ads}")
    print(
        "inc_desc, all:",
        Counter(subs[x["cik"]].get("inc_desc") or "(blank)" for x in g).most_common(),
    )


if __name__ == "__main__":
    main()
