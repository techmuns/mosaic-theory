"""Freeze the balance-sheet companyfacts the impairment-headroom pins read
(`tests/test_impairment_headroom.py`, audit RD-D1).

SEC's public data, cut two ways:
- BY CONCEPT: only the tags `capital_allocation` reads for the headroom and the peer intensity
  (`GOODWILL`, `INTANGIBLES`, `TOTAL_ASSETS`), each concept's rows unmodified;
- AS FILED BY each page's price date (`facts_as_of`, the cut assembly reads EDGAR at), so a pin
  reads what the page could have read, never a later filing.

    python scripts/build_balance_fixture.py            # the four names below
    python scripts/build_balance_fixture.py MCK        # just these

It needs network (SEC) and the SEC user agent in the environment. It is an operator tool, never
imported by the suite.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
from datetime import date
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "capital_allocation_balances.json"
#: The four committed pages whose two balances sat at different dates (2026-11-10): MCK, AMZN and
#: TGT from the audit's scan, BURL from the same scan over every committed page.
NAMES = ("MCK", "AMZN", "TGT", "BURL")


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(ROOT))
    from vinci.dossier.anchor import price_as_of
    from vinci.dossier.capital_allocation import GOODWILL, INTANGIBLES, TOTAL_ASSETS
    from vinci.edgar.asof import page_price_date
    from vinci.edgar.client import EdgarClient
    from vinci.edgar.concepts import facts_as_of

    tags = (*GOODWILL, *INTANGIBLES, *TOTAL_ASSETS)
    edgar = EdgarClient.from_config()
    out: dict[str, Any] = {"_about": {
        "what": "SEC companyfacts, cut to the balance tags capital_allocation reads and as filed "
                "by each page's price date (scripts/build_balance_fixture.py)",
        "tags": list(tags)}, "names": {}}
    for t in [a.upper() for a in argv] or list(NAMES):
        page = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
        cut = page_price_date(price_as_of(page["mechanical"]),
                              date.fromisoformat(str(page["reference_date"])))
        facts = facts_as_of(edgar.companyfacts(page["cik"]), cut)
        gaap = (facts.get("facts") or {}).get("us-gaap") or {}
        out["names"][t] = {"cik": page["cik"], "cut": cut.isoformat(),
                           "facts": {"us-gaap": {k: gaap[k] for k in tags if k in gaap}}}
        print(f"  {t:5} cut {cut} · {sorted(k for k in tags if k in gaap)}")
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    os.chdir(ROOT)
    raise SystemExit(main(sys.argv[1:]))
