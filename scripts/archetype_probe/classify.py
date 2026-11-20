"""Step 3 — count the two committed universes into archetypes. Pure: reads the committed universe
snapshots (READ only), out/subs_extract.jsonl, out/frames/*, out/fpi_facts.json. Writes
out/census.json (per company) and prints the tables. Every threshold is a descriptive,
face-validity cut stated beside its count — nothing here feeds any decision path."""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from probe_common import OUT, universe_rows

US = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "PR",
    "VI",
    "GU",
}
BANK = {"6021", "6022", "6029", "6035", "6036"}
LENDER = {"6099", "6111", "6141", "6153", "6159", "6162", "6163", "6172", "6189", "6199"}
INSURER = {"6311", "6321", "6331", "6351", "6361", "6399"}
MANAGED_CARE = {"6324"}
INS_BROKER = {"6411"}
BROKER_DEALER = {"6211"}
ASSET_MGR = {"6200", "6282", "6221"}
REIT = {"6798"}
REAL_ESTATE_OP = {"6500", "6510", "6512", "6513", "6519", "6531", "6532", "6552"}
UTILITY = {"4911", "4924", "4931", "4932", "4941", "4961", "4991"}
MIDSTREAM_GAS = {"4922", "4923"}
ROYALTY = {"6792", "6794", "6795"}
RESERVE = {"1000", "1040", "1090", "1220", "1221", "1311", "1400"}
REV_TAGS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
)


def frames() -> dict[str, dict[str, float]]:
    out = {}
    for p in (OUT / "frames").glob("*.json"):
        _ns, concept, _unit, period = p.stem.split("__")
        out[f"{concept}@{period}"] = json.loads(p.read_text())
    return out


def main() -> None:
    F = frames()  # noqa: N806 — the frames table, read as F["<concept>@<period>"]
    subs = {
        json.loads(x)["cik"]: json.loads(x)
        for x in (OUT / "subs_extract.jsonl").read_text().splitlines()
        if x.strip()
    }
    fpi = (
        json.loads((OUT / "fpi_facts.json").read_text())
        if (OUT / "fpi_facts.json").exists()
        else {}
    )
    rows = universe_rows()
    by_cik: dict[str, dict] = {}
    for r in rows:
        c = by_cik.setdefault(r["cik"], {**r, "bands": set(), "caps": {}})
        c["bands"].add(r["band"])
        c["caps"][r["band"]] = r["market_cap"]
        if r["band"] == "primary":  # the newer snapshot's row wins for shared fields
            c.update({k: r[k] for k in ("ticker", "cap_source", "as_of")})

    def g(key: str, cik: str):
        return F.get(key, {}).get(cik)

    def rev(cik: str, period: str):
        vals = [g(f"{t}@{period}", cik) for t in REV_TAGS]
        vals = [v for v in vals if v is not None]
        return max(vals) if vals else None

    census = []
    for cik, c in by_cik.items():
        s = subs.get(cik, {})
        sic = s.get("sic") or c.get("sic") or ""
        la = (s.get("latest_annual") or [None])[0]
        inc = s.get("inc")
        # --- axis A: filing regime -----------------------------------------------------------
        if not s:
            regime = "UNREAD (submissions not fetched)"
        elif la in ("20-F", "40-F"):
            f = fpi.get(cik, {})
            cur = f.get("reporting_currency")
            if "error" in f or not f:
                regime = f"FPI {la} — companyfacts unread"
            elif (f.get("ifrs_end") and f.get("fy_end") and f["ifrs_end"] >= f["fy_end"]) or str(
                f.get("fy_tag") or ""
            ).startswith("ifrs-full"):
                regime = f"FPI {la} IFRS"
            elif cur == "USD":
                regime = f"FPI {la} US GAAP, USD"
            else:
                regime = f"FPI {la} US GAAP, {cur or 'currency unread'}"
        elif la in ("10-K", "10-KT", "10-K405"):
            # incorporation first; a BLANK incorporation field (204 of 2,459 10-K filers) falls back
            # to the business address, and says so in the label
            if inc in US or not inc and s.get("biz_country") in US:
                regime = "10-K, US-incorporated"
            elif not inc:
                regime = "10-K, incorporation and address not stated"
            else:
                regime = "10-K, foreign-incorporated"
        else:
            regime = "no annual report in recent filings"
        # --- axis B: statement form ----------------------------------------------------------
        name = (s.get("name") or c.get("name") or "").upper()
        # a partnership NAME, or BOTH partnership-capital tags: one tag alone also appears on
        # corporations consolidating a partnership (CHKP, MDLN, MSEX, HASI in the first cut)
        partnership = (
            (
                g("PartnersCapital@CY2025Q4I", cik) is not None
                and g("LimitedPartnersCapitalAccount@CY2025Q4I", cik) is not None
            )
            or " L.P." in name
            or name.endswith(" LP")
            or " LP " in name
            or name.endswith(", LP")
        )  # not "PARTNERS": CCEP, GRBK, ROAD, SGRY are corporations
        if sic in BANK:
            form = "bank"
        elif sic in LENDER:
            form = "lender / specialty finance"
        elif sic in MANAGED_CARE:
            form = "managed care (SIC 6324)"
        elif sic in INSURER:
            form = "insurer (underwriting)"
        elif sic in INS_BROKER:
            form = "insurance broker"
        elif sic in BROKER_DEALER:
            form = "broker-dealer / investment bank"
        elif sic in ASSET_MGR:
            form = "asset manager / exchange"
        elif sic in REIT:
            form = "REIT"
        elif sic in REAL_ESTATE_OP:
            form = "real-estate operator / developer"
        elif partnership:
            form = "partnership / MLP"
        elif sic in UTILITY:
            form = "regulated utility"
        elif sic in ROYALTY:
            form = "royalty / patent owner"
        elif sic.startswith("67"):
            form = "holding / investment office"
        else:
            form = "operating company"
        # --- axis C: economic model (operating companies) --------------------------------------
        r25, r24 = rev(cik, "CY2025"), rev(cik, "CY2024")
        oi25, oi24 = g("OperatingIncomeLoss@CY2025", cik), g("OperatingIncomeLoss@CY2024", cik)
        model = None
        if form == "operating company":
            if r25 is None and r24 is None and oi25 is None and oi24 is None:
                model = "no CY2024/25 us-gaap USD frame data"
            elif (r25 or 0) < 10e6 and (r24 or 0) < 10e6:
                model = "pre-revenue (< $10M revenue CY2024 and CY2025)"
            elif sic in RESERVE:
                model = "reserve-based (mining / E&P)"
            elif oi25 is not None and oi24 is not None and oi25 <= 0 and oi24 <= 0:
                model = "pre-profit (operating loss CY2024 and CY2025)"
            elif oi25 is None and oi24 is None:
                model = "profitable-or-unknown, OperatingIncomeLoss untagged"
            else:
                model = "operating, positive operating income in a recent year"
        # --- overlaps --------------------------------------------------------------------------
        flags = []
        assets = g("Assets@CY2025Q4I", cik)
        if form == "operating company" and r25 and oi25 is None and oi24 is None:
            flags.append("OperatingIncomeLoss untagged (R1 margin leg needs CIQ)")
        ol = g("OperatingLeaseLiability@CY2025Q4I", cik)
        if ol and assets and ol / assets >= 0.20:
            flags.append("lease-heavy (op-lease liability >= 20% of assets)")
        dr = max(
            [
                v
                for v in (
                    g("ContractWithCustomerLiability@CY2025Q4I", cik),
                    g("ContractWithCustomerLiabilityCurrent@CY2025Q4I", cik),
                )
                if v
            ]
            or [0]
        )
        rpo = g("RevenueRemainingPerformanceObligation@CY2025Q4I", cik)
        if r25 and ((dr and dr / r25 >= 0.25) or (rpo and rpo / r25 >= 1.0)):
            flags.append("deferred-revenue / backlog heavy (CWCL >= 25% or RPO >= 100% of revenue)")
        capex = g("PaymentsToAcquirePropertyPlantAndEquipment@CY2025", cik)
        if r25 and capex and capex / r25 >= 0.15:
            flags.append("capex-heavy (capex >= 15% of revenue)")
        sbc = g("ShareBasedCompensation@CY2025", cik) or g(
            "AllocatedShareBasedCompensationExpense@CY2025", cik
        )
        if r25 and sbc and sbc / r25 >= 0.10:
            flags.append("SBC-heavy (>= 10% of revenue)")
        eq = g("StockholdersEquity@CY2025Q4I", cik)
        if eq is not None and eq < 0:
            flags.append("negative equity")
        src = c.get("cap_source") or ""
        if "PER-CLASS" in src:
            flags.append("multiple share classes (per-class cap)")
        if "ADS-denominated" in src:
            flags.append("depositary (ADS) line")
        if "PERIOD AVERAGE" in src or "FALLBACK" in src:
            flags.append("no filed point-in-time share count (cap on average/Polygon)")
        if s.get("fye") and s["fye"] != "1231":
            flags.append("non-December fiscal year")
        if s.get("transition_3y"):
            flags.append("transition period filed in 3y")
        if s.get("n_8k201_730", 0) >= 1:
            flags.append("acquisition/disposal completed (8-K 2.01) in 2y")
        if s.get("spin_reg"):
            flags.append("registered via Form 10 (spin-off / direct listing)")
        if s.get("ipo_3y"):
            flags.append("S-1/F-1/424B4 in 3y (short public history)")
        if s.get("n_6k_180", 0) >= 6:
            flags.append(">= 6 Form 6-Ks in 180d (event rule: an export lives < ~1 month)")
        if sic in MIDSTREAM_GAS:
            flags.append("SIC 4922/4923 gas transmission (midstream, not counted as utility)")
        census.append(
            {
                "cik": cik,
                "ticker": c.get("ticker"),
                "name": s.get("name") or c.get("name"),
                "bands": sorted(c["bands"]),
                "caps": c["caps"],
                "sic": sic,
                "regime": regime,
                "form": form,
                "model": model,
                "flags": flags,
                "latest_annual": s.get("latest_annual"),
                "inc": inc,
            }
        )
    (OUT / "census.json").write_text(json.dumps(census, indent=1))

    def table(title: str, key, pop: list[dict]) -> None:
        cnt, capw = Counter(), defaultdict(float)
        for x in pop:
            k = key(x)
            cnt[k] += 1
            capw[k] += max(x["caps"].values()) if x["caps"] else 0
        tot_n, tot_c = sum(cnt.values()), sum(capw.values())
        print(f"\n## {title} — {tot_n} companies, ${tot_c / 1e12:,.2f}T cap")
        for k, n in cnt.most_common():
            print(f"  {n:5d} ({n / tot_n:5.1%})  cap {capw[k] / tot_c:5.1%}  {k}")

    for band in ("primary", "theme"):
        pop = [x for x in census if band in x["bands"]]
        # within one band, weight by that band's own cap
        pop_b = [{**x, "caps": {band: x["caps"][band]}} for x in pop]
        table(f"{band}: filing regime", lambda x: x["regime"], pop_b)
        table(f"{band}: statement form", lambda x: x["form"], pop_b)
        table(
            f"{band}: economic model (operating companies only)",
            lambda x: x["model"],
            [x for x in pop_b if x["model"]],
        )
        fl = Counter(f for x in pop_b for f in x["flags"])
        print(f"\n## {band}: overlap flags (a company may carry several) — of {len(pop_b)}")
        for k, n in fl.most_common():
            print(f"  {n:5d} ({n / len(pop_b):5.1%})  {k}")
    union = census
    table(
        "union (both bands, distinct CIK): statement form x regime class",
        lambda x: (
            x["form"]
            + " | "
            + (
                "SEC-FPI"
                if x["regime"].startswith("FPI")
                else "domestic forms"
                if x["regime"].startswith("10-K")
                else x["regime"]
            )
        ),
        union,
    )


if __name__ == "__main__":
    main()
