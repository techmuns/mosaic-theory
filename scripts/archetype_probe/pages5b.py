"""5b: each defect's reach on the LIVE corpus — the committed pages at the worktree's HEAD.

POPULATION: every `data/dossiers/*/dossier.json` (the committed pages), each with its coverage-
roster status (`coverage_roster.current`) and its census archetype (`out/census.json` of step 3,
read 2026-11-19 from the universes as_of 2026-10-16 / 2026-08-24; a page whose CIK is in neither
universe says so). Each defect is measured by a signature on the page's own fields — stated per
defect below — never by name. Read-only; prints every page it counts (no truncation)."""

from __future__ import annotations

import json
import subprocess
from collections import defaultdict

from probe_common import OUT, WT, grid_code

CENSUS = OUT / "census.json"  # written by classify.py


def s(x) -> str:
    return json.dumps(x, default=str) if not isinstance(x, str) else x


def main() -> None:
    import vinci
    from vinci import coverage_roster as roster

    print("vinci:", vinci.__file__)
    head = subprocess.run(
        ["git", "-C", str(WT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    census = {x["cik"]: x for x in json.loads(CENSUS.read_text())}
    status = {t: m.status for t, m in roster.current(WT / "data").items()}
    pages = sorted((WT / "data" / "dossiers").glob("*/dossier.json"))
    hits: dict[str, list[str]] = defaultdict(list)
    table = []
    for p in pages:
        d = json.loads(p.read_text())
        t, cik = d["ticker"], d["cik"]
        c = census.get(cik)
        g = grid_code(c) if c else "not in either universe"
        m = d.get("mechanical") or {}
        a = d.get("anchor") or {}
        v = m.get("valuation") or {}
        table.append((t, status.get(t, "not on roster"), g, (c or {}).get("sic")))
        if g in ("G13", "G13b"):
            hits["D1 REIT/real-estate archetype"].append(t)
        if g in ("G17", "G17b", "G18", "G19"):
            hits["D2/D8/D10/D16 FPI archetype"].append(t)
        if (c or {}).get("sic") == "6211":
            hits["D3 SIC 6211"].append(t)
        if g == "G20":
            hits["D9 no annual on file"].append(t)
        if g in ("G06", "G07", "G08", "G10"):
            hits["D14 bank/lender/insurer/B-D"].append(t)
        nd = a.get("net_debt")
        why = (
            s(a.get("data_quality_detail") or "")
            + " "
            + s(a.get("reason") or "")
            + " "
            + s(a.get("note") or "")
        )
        if nd is None:
            hits["D4/D5 anchor net debt absent"].append(f"{t}: {why.strip()[:140]}")
        elif not s(nd.get("source")).startswith("EDGAR"):
            hits["D4/D5 EDGAR net debt refused, another source used"].append(
                f"{t}: {s(nd.get('source'))[:110]}"
            )
        so = (m.get("stock_info") or {}).get("shares_out") or {}
        if so.get("status") != "present" or "EDGAR" not in (so.get("source_ref") or ""):
            hits["D6 page share count not from EDGAR's cover count"].append(
                f"{t}: {so.get('status')} · {(so.get('source_ref') or so.get('note') or '')[:90]}"
            )
        mg = a.get("margin") or {}
        if mg and ("CIQ" in s(mg.get("source")) or "financial_summary" in s(mg.get("source"))):
            hits["D7 anchor margin from CIQ (OI untagged)"].append(t)
        if a.get("recipe_hint") == "unknown" and "own-history multiple missing" in s(
            a.get("reason")
        ):
            hits["D12 anchor unknown: own-history multiple missing"].append(t)
        if "older than one filing cycle" in s((v.get("pe") or {}).get("note")):
            hits["D13 P/E note prints the 'newer negative' cause"].append(t)
        eb = d.get("ev_bridge") or {}
        if "states no 'Total Cash & ST Investments'" in s(eb):
            hits["D17 bridge unbuilt for the cash subtotal"].append(t)
        for cav in d.get("caveats") or []:
            if s(cav).startswith("pull CIQ '"):
                hits["D19 a required CIQ export missing (caveat only)"].append(
                    f"{t}: {s(cav)[:60]}"
                )
        if v.get("ev_ebitda_basis"):
            hits["D20 'reported LTM EBITDA' label present"].append(t)
    out = {"head": head, "pages": len(pages), "table": table, "hits": dict(hits)}
    (OUT / "pages5b.json").write_text(json.dumps(out, indent=1))
    print(f"main {head}: {len(pages)} committed pages")
    for row in table:
        print("  ", " | ".join(str(x) for x in row))
    for k in sorted(hits):
        print(f"{k}: {len(hits[k])} of {len(pages)} — all listed")
        for h in hits[k]:
            print("     ", h)


if __name__ == "__main__":
    main()
