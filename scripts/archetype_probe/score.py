"""Score each probed name, per layer: W works / R refuses loudly / X produces something wrong /
N not reachable — from out/probe/*.json by the explicit rules below, plus the overrides the
second-look diagnostics (diag.py) established, each with its evidence. Writes out/scores.md."""

from __future__ import annotations

import json

from probe_common import OUT

# name → probe archetype label (statement form / regime / model), stated by hand from the probe
ARCH = {
    "LLY": "operating · pharma (OI untagged)",
    "PFE": "operating · pharma (OI untagged)",
    "GILD": "operating · biopharma",
    "ISRG": "operating · medtech, debt-free",
    "HSY": "operating · staples, 2 classes",
    "EL": "operating · staples, 2 classes, June FY",
    "BRBR": "operating · staples, Sept FY (page control)",
    "TTWO": "operating · March FY, GAAP losses recent",
    "SPGI": "operating · data/ratings",
    "FICO": "operating · Sept FY, neg. equity",
    "FDS": "operating · Aug FY",
    "VRSK": "operating · data",
    "MORN": "asset mgr / data (SIC 6282)",
    "LOW": "operating · Jan FY, neg. equity",
    "ORCL": "operating · May FY, capex/RPO heavy",
    "CRWV": "pre-profit · capex/lease heavy, IPO 2025",
    "RIVN": "pre-profit",
    "PCVX": "pre-revenue biotech",
    "VKTX": "pre-revenue biotech",
    "MTB": "bank",
    "JPM": "bank",
    "RY": "bank · FPI 40-F IFRS CAD",
    "AXP": "lender (SIC 6199)",
    "SYF": "lender (SIC 6199)",
    "CB": "insurer",
    "PGR": "insurer",
    "BRK-B": "insurer-led conglomerate · 2 classes",
    "UNH": "managed care (SIC 6324)",
    "CNC": "managed care (SIC 6324)",
    "AJG": "insurance broker",
    "GS": "broker-dealer (SIC 6211)",
    "SCHW": "broker-dealer + bank (SIC 6211)",
    "BLK": "asset manager (SIC 6211)",
    "CME": "exchange (SIC 6200)",
    "PLD": "REIT (co-registrant OP)",
    "O": "REIT",
    "INVH": "REIT (SIC 6510)",
    "VMRK": "REIT · merged 2026 (ex-EQR)",
    "NEE": "utility (co-registrant)",
    "AWK": "utility",
    "EPD": "MLP",
    "MPLX": "MLP",
    "TPL": "royalty",
    "RGLD": "royalty",
    "FNV": "royalty · FPI 40-F IFRS",
    "NVO": "FPI 20-F IFRS (DKK)",
    "TSM": "FPI 20-F IFRS (TWD), ADS 5:1",
    "ASML": "FPI 20-F US GAAP EUR",
    "BABA": "FPI 20-F US GAAP CNY, ADS 8:1",
    "NBIS": "FPI 20-F US GAAP USD · transformed 2024",
    "FCX": "reserve-based (mining)",
    "DVN": "reserve-based (E&P)",
    "XOM": "successor registrant (2026)",
    "CODGF": "non-SEC (Saint-Gobain OTC line)",
    "AVB": "deregistered 2026-08-27 (Form 15)",
    "ABB": "deregistered 20-F filer",
    "EQR": "renamed VMRK",
    "BFC": "bank · screen-band median cap",
    "NMIH": "insurer (6351) · screen-band median cap",
    "PEB": "REIT · screen-band median cap",
    "AQN": "utility · 40-F US GAAP USD · screen-band median cap",
    "SECZ": "lender · no 10-K yet · screen-band median cap",
    "DRD": "FPI 20-F IFRS (ZAR), ADS 10:1 · screen-band median cap",
}

OVERRIDE = {
    ("INVH", "anchor"): (
        "X",
        "R1 margin 192.1% (FY2015 OperatingIncomeLoss over a $59.5M ASC 606 component chosen as "
        "total "
        "revenue; `Revenues` $2,729M FY2025 has 10y) — printed as the mid-cycle margin; R1 value "
        "then "
        "refused for no D&A tag",
    ),
    ("NBIS", "anchor"): (
        "X",
        "R1 margin +15.2% from FY2018–19 (Yandex-era revenue tag); OperatingIncomeLoss negative "
        "every year 2021–25 — a divested business's margin passes the R2 gate (flagged "
        "revenue_tag_conflict, capped weak)",
    ),
    ("SCHW", "net_debt"): (
        "X",
        "net debt −$12.85bn computed for a savings-and-loan holding company (SIC 6211 escapes the "
        "60/61/63 rule); its borrowings fund a bank book",
    ),
    ("DRD", "fiscal_year"): (
        "R",
        "newest fiscal year read FY2025-06 (ifrs-full, ZAR) though the 20-F filed "
        "2026-10-02 covers FY2026 — companyfacts lacks it (FPI1c)",
    ),
    ("TSM", "fiscal_year"): (
        "R",
        "newest fiscal year read FY2024 (ifrs-full) though the FY2025 20-F was filed 2026-04-16 — "
        "companyfacts lacks it (FPI1c); dates only, no value read",
    ),
}


def s_layer(t: str, d: dict) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    i = d.get("identity", {})
    if "raised" in i:
        return {"identity": ("N", f"{i['raised']}: {i['message'][:90]}")}
    out["identity"] = ("W", f"CIK {i['cik']} SIC {i['sic']}")
    f = d.get("filings", {})
    la = f.get("latest_annual")
    out["filing_regime"] = (
        ("W", f"{la[0]} {la[1]}; 10-Q {f.get('n_10q_365')}, 6-K {f.get('n_6k_365')} in 365d")
        if la
        else ("R", f"no annual report on file (10-Q {f.get('n_10q_365')}, 6-K {f.get('n_6k_365')})")
    )
    cf = d.get("companyfacts", {})
    if "raised" in cf:
        out["companyfacts"] = ("N", f"{cf['raised']} (no XBRL companyfacts)")
    else:
        ns = cf.get("namespaces", {})
        cur = cf.get("reporting_currency")
        if ns.get("ifrs-full") and not ns.get("us-gaap"):
            out["companyfacts"] = (
                "R",
                f"ifrs-full only ({ns.get('ifrs-full')} concepts): no reader serves an IFRS value",
            )
        elif cur not in (None, "USD"):
            out["companyfacts"] = ("R", f"US GAAP in {cur}: every money figure withheld (FPI1a)")
        else:
            out["companyfacts"] = ("W", f"us-gaap {ns.get('us-gaap')} concepts, {cur}")
    fy = d.get("fiscal_year")
    if isinstance(fy, dict) and "raised" not in fy:
        out["fiscal_year"] = (
            "W",
            f"FY end {fy.get('end')} ({fy.get('days')}d) via {fy.get('tag')}",
        )
    elif fy is None and "companyfacts" in out and out["companyfacts"][0] != "N":
        out["fiscal_year"] = ("R", "no fiscal year datable")
    sf = d.get("screen_fundamentals", {})
    if sf and "raised" not in sf:
        n = sum(1 for v in sf.values() if v.get("status") == "present")
        notes = sorted(
            {(v.get("note") or "")[:70] for v in sf.values() if v.get("status") != "present"}
        )
        out["screen"] = (
            ("W" if n == 7 else "R"),
            f"{n}/7 present" + (f"; e.g. {notes[0]}" if notes else ""),
        )
    a = d.get("anchor_gates", {})
    if a and "raised" not in a:
        g = a.get("gate", "")
        da = a.get("d_and_a")
        da_note = "" if isinstance(da, dict) else f"; D&A refused ({str(da)[:50]})"
        if g.startswith("R1"):
            out["anchor"] = (
                "W",
                f"margin {a['margin_median']:.1%} over {a['margin_years']}y "
                f"({a['revenue_tag'][:28]}){da_note}",
            )
        else:
            out["anchor"] = ("R", g[:80] + da_note)
    nd = d.get("net_debt", {})
    if nd and "raised" not in nd:
        if nd.get("sic_rule"):
            out["net_debt"] = (
                "R",
                "SIC rule (banks/lenders/insurers); builder would read "
                f"${(nd.get('leverage_usd') or 0) / 1e9:,.1f}bn",
            )
        elif nd.get("builder_refusal"):
            out["net_debt"] = ("R", str(nd["builder_refusal"])[:100])
        else:
            out["net_debt"] = (
                "W",
                f"${(nd.get('leverage_usd') or 0) / 1e9:,.2f}bn at {nd.get('at')}",
            )
    sh = d.get("shares", {})
    if sh and "raised" not in sh:
        ar = sh.get("ads_ratio", {})
        ads = (
            f"; ADS {ar.get('ordinary_per_ads')}:1 ({ar.get('form')})"
            if ar.get("status") == "known"
            else ""
        )
        out["shares"] = (
            ("W", f"{sh['edgar_count']:,.0f}{ads}")
            if sh.get("edgar_count")
            else (
                "R",
                "no current filed count (absent/stale/refused) → falls back to the diluted average"
                + ads,
            )
        )
    ev = d.get("event_rule", {})
    if ev and "raised" not in ev:
        if not ev.get("events_365"):
            out["event_rule"] = ("N", "no filings to read")
        else:
            six = (ev.get("by_form") or {}).get("6-K", 0)
            note = f"{ev['events_365']} events/365d; median gap {ev.get('median_gap_days')}d"
            out["event_rule"] = (
                ("W", note + f" — {six} 6-Ks: each one outdates an export")
                if six >= 6
                else ("W", note)
            )
    pr = d.get("price", {})
    if pr and "raised" not in pr:
        out["price"] = (
            ("W", f"{pr['symbol']} {pr['close_2026_11_18']}")
            if pr.get("in_grouped_daily")
            else ("N", f"{pr['symbol']} not in Polygon grouped daily (OTC)")
        )
    for (tt, layer), v in OVERRIDE.items():
        if tt == t:
            out[layer] = v
    return out


LAYERS = [
    "identity",
    "filing_regime",
    "companyfacts",
    "fiscal_year",
    "screen",
    "shares",
    "net_debt",
    "anchor",
    "event_rule",
    "price",
]


def main() -> None:
    rows = []
    allscores = {}
    for p in sorted((OUT / "probe").glob("*.json")):
        t = p.stem
        if t == "AVB":
            continue
        d = json.loads(p.read_text())
        sc = s_layer(t, d)
        allscores[t] = sc
        rows.append((t, sc))
    (OUT / "scores.json").write_text(json.dumps(allscores, indent=1))
    lines = ["| name | archetype | " + " | ".join(LAYERS) + " |", "|" + "---|" * (len(LAYERS) + 2)]
    for t, sc in rows:
        lines.append(
            f"| {t} | {ARCH.get(t, '?')} | "
            + " | ".join(sc.get(k, ("·", ""))[0] for k in LAYERS)
            + " |"
        )
    ev = []
    for t, sc in rows:
        ev.append(f"\n**{t}** ({ARCH.get(t, '?')})")
        for k in LAYERS:
            if k in sc:
                ev.append(f"- {k}: **{sc[k][0]}** — {sc[k][1]}")
    (OUT / "scores.md").write_text("\n".join(lines) + "\n\n" + "\n".join(ev) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
