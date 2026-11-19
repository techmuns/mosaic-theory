"""The substitute G17 test name: every G17 company (FPI, US GAAP, USD, operating form) with the
evidence
the pick rests on — latest annual form, incorporation, the exchanges EDGAR lists, operating income
in
the CY2024/CY2025 SEC frames, CY2025 revenue, 6-Ks in 180 days, cap and the census's overlap flags.
All rows printed (no truncation). Reads `<OUT>/census.json`, `<OUT>/subs_extract.jsonl`,
`<OUT>/fpi_facts.json` and `<OUT>/frames/` (census_fetch.py); fetches nothing.

    python scripts/archetype_probe/g17pick5b.py
"""

from __future__ import annotations

import json
from typing import Any

from pages5b import grid_arch
from probe_common import OUT

REV_TAGS = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
)


def frame(tag: str, period: str) -> dict[str, Any]:
    p = OUT / "frames" / f"us-gaap__{tag}__USD__{period}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def m(v: float | None) -> float | None:
    return None if v is None else round(v / 1e6, 1)


def main() -> None:
    import vinci

    print("vinci:", vinci.__file__)
    subs = {}
    for line in (OUT / "subs_extract.jsonl").read_text().splitlines():
        if line.strip():
            o = json.loads(line)
            subs[o["cik"]] = o
    census = json.loads((OUT / "census.json").read_text())
    fpi = json.loads((OUT / "fpi_facts.json").read_text())
    oi24, oi25 = frame("OperatingIncomeLoss", "CY2024"), frame("OperatingIncomeLoss", "CY2025")
    rev25: dict[str, Any] = {}
    for tag in REV_TAGS:
        for k, v in frame(tag, "CY2025").items():
            rev25.setdefault(k, v)
    rows = []
    for x in census:
        if grid_arch(x) != "G17":
            continue
        c, s, f = x["cik"], subs[x["cik"]], fpi.get(x["cik"], {})
        rows.append(
            {
                "ticker": x["ticker"],
                "form": x["latest_annual"][0],
                "filed": x["latest_annual"][1],
                "inc": s.get("inc_desc") or "(blank)",
                "exchanges": sorted(set(s.get("exchanges") or [])),
                "currency": f.get("reporting_currency"),
                "namespaces": sorted(f.get("ns") or {}),
                "oi_cy2024": m(oi24.get(c)),
                "oi_cy2025": m(oi25.get(c)),
                "rev_cy2025": m(rev25.get(c)),
                "6k_180d": s.get("n_6k_180"),
                "6k_365d": s.get("n_6k_365"),
                "cap_bn": round(max(x["caps"].values()) / 1e9, 2),
                "flags": x["flags"],
            }
        )
    good = [
        r
        for r in rows
        if (r["oi_cy2024"] or 0) > 0
        and (r["oi_cy2025"] or 0) > 0
        and not any("depositary" in fl for fl in r["flags"])
    ]
    print(
        f"G17 companies: {len(rows)}; positive operating income in both frames and no ADS line: "
        f"{len(good)}"
    )
    for r in sorted(rows, key=lambda r: (r not in good, r["6k_180d"] or 0, -r["cap_bn"])):
        print("  ", json.dumps(r))
    (OUT / "g17pick5b.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
