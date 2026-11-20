"""Stage-2 SEC-filing status, per name, MEASURED through the repo's own SEC clients.

Three searches per name (CLAUDE.md: never assert absence off one search):
  (a) the US ticker, if one is supplied, in SEC company_tickers(.json/_exchange.json) — the repo
  index;
  (b) every name token as a SUBSTRING of every issuer name in that index (broader than the
      resolver's exact-match `resolve_name`);
  (c) EDGAR full-text search for the token in 20-F/40-F/6-K/10-K filed 2024-01-01 → 2026-11-19,
      counting a hit only when the token is in the FILER's display name (a mention in another
      company's filing is not a filing).
A filer found → its submissions (latest annual form) and companyfacts (reporting currency,
namespaces) through the same clients. The SELECTION of names is general knowledge of each market's
largest listed companies, NOT a measured market-cap ranking (stated in the findings)."""

from __future__ import annotations

import datetime as dt
import json
from collections import Counter

from probe_common import OUT, edgar, sec_http

NAMES = [
    # market, display name, substring tokens (upper-case), US ticker to try (or None)
    ("EU-FR", "EssilorLuxottica", ["ESSILOR"], None),
    ("EU-FR", "Saint-Gobain", ["SAINT GOBAIN", "SAINT-GOBAIN", "GOBAIN"], None),
    ("EU-FR", "LVMH", ["LVMH", "MOET HENNESSY"], None),
    ("EU-FR", "Hermes International", ["HERMES INTERNATIONAL"], None),
    ("EU-FR", "L'Oreal", ["L'OREAL", "LOREAL"], None),
    ("EU-FR", "TotalEnergies", ["TOTALENERGIES"], "TTE"),
    ("EU-FR", "Schneider Electric", ["SCHNEIDER ELECTRIC"], None),
    ("EU-FR", "Airbus", ["AIRBUS"], None),
    ("EU-FR", "Sanofi", ["SANOFI"], "SNY"),
    ("EU-FR", "Safran", ["SAFRAN"], None),
    ("EU-FR", "BNP Paribas", ["BNP PARIBAS"], None),
    ("EU-NL", "ASML Holding", ["ASML"], "ASML"),
    ("EU-NL", "Prosus", ["PROSUS"], None),
    ("EU-NL", "ING Groep", ["ING GROEP"], "ING"),
    ("EU-NL", "Stellantis", ["STELLANTIS"], "STLA"),
    ("EU-NL", "Ferrari", ["FERRARI"], "RACE"),
    ("EU-DE", "SAP", ["SAP SE"], "SAP"),
    ("EU-DE", "Siemens", ["SIEMENS AG", "SIEMENS AKTIENGESELLSCHAFT"], None),
    ("EU-DE", "Allianz", ["ALLIANZ"], None),
    ("EU-DE", "Deutsche Telekom", ["DEUTSCHE TELEKOM"], None),
    ("EU-DE", "Rheinmetall", ["RHEINMETALL"], None),
    ("EU-DE", "Deutsche Bank", ["DEUTSCHE BANK AKTIENGESELLSCHAFT", "DEUTSCHE BANK AG"], "DB"),
    ("EU-DK", "Novo Nordisk", ["NOVO NORDISK"], "NVO"),
    ("EU-ES", "Inditex", ["INDITEX", "INDUSTRIA DE DISENO"], None),
    ("EU-ES", "Iberdrola", ["IBERDROLA"], None),
    ("EU-ES", "Banco Santander", ["BANCO SANTANDER S"], "SAN"),
    ("EU-LU", "Spotify Technology", ["SPOTIFY"], "SPOT"),
    ("CH", "Nestle", ["NESTLE S"], None),
    ("CH", "Roche Holding", ["ROCHE HOLDING"], None),
    ("CH", "Novartis", ["NOVARTIS"], "NVS"),
    ("CH", "UBS Group", ["UBS GROUP"], "UBS"),
    ("CH", "ABB", ["ABB LTD"], None),
    ("CH", "Zurich Insurance", ["ZURICH INSURANCE"], None),
    ("UK", "AstraZeneca", ["ASTRAZENECA"], "AZN"),
    ("UK", "Shell", ["SHELL PLC"], "SHEL"),
    ("UK", "HSBC Holdings", ["HSBC HOLDINGS"], "HSBC"),
    ("UK", "Unilever", ["UNILEVER"], "UL"),
    ("UK", "Rio Tinto", ["RIO TINTO"], "RIO"),
    ("UK", "BP", ["BP PLC", "BP P.L.C"], "BP"),
    ("UK", "GSK", ["GSK PLC"], "GSK"),
    ("UK", "Arm Holdings", ["ARM HOLDINGS"], "ARM"),
    ("UK", "Diageo", ["DIAGEO"], "DEO"),
    ("UK", "Barclays", ["BARCLAYS PLC"], "BCS"),
    ("JP", "Toyota Motor", ["TOYOTA MOTOR"], "TM"),
    ("JP", "Sony Group", ["SONY GROUP"], "SONY"),
    ("JP", "Mitsubishi UFJ Financial", ["MITSUBISHI UFJ"], "MUFG"),
    ("JP", "Sumitomo Mitsui Financial", ["SUMITOMO MITSUI FINANCIAL"], "SMFG"),
    ("JP", "Mizuho Financial", ["MIZUHO FINANCIAL"], "MFG"),
    ("JP", "Hitachi", ["HITACHI LTD", "HITACHI, LTD"], None),
    ("JP", "Keyence", ["KEYENCE"], None),
    ("JP", "Fast Retailing", ["FAST RETAILING"], None),
    ("JP", "SoftBank Group", ["SOFTBANK GROUP"], None),
    ("JP", "Tokyo Electron", ["TOKYO ELECTRON"], None),
    ("JP", "Nintendo", ["NINTENDO"], None),
    ("JP", "Mitsubishi Corporation", ["MITSUBISHI CORP"], None),
    ("JP", "Honda Motor", ["HONDA MOTOR"], "HMC"),
    ("JP", "Takeda Pharmaceutical", ["TAKEDA PHARMACEUTICAL"], "TAK"),
    ("CN/HK", "Tencent Holdings", ["TENCENT HOLDINGS"], None),
    ("CN/HK", "Alibaba Group", ["ALIBABA GROUP"], "BABA"),
    ("CN/HK", "PDD Holdings", ["PDD HOLDINGS"], "PDD"),
    ("CN/HK", "JD.com", ["JD.COM"], "JD"),
    ("CN/HK", "NetEase", ["NETEASE"], "NTES"),
    ("CN/HK", "Baidu", ["BAIDU"], "BIDU"),
    ("CN/HK", "Trip.com Group", ["TRIP.COM"], "TCOM"),
    ("CN/HK", "BYD", ["BYD CO"], None),
    ("CN/HK", "CATL", ["CONTEMPORARY AMPEREX"], None),
    ("CN/HK", "Kweichow Moutai", ["KWEICHOW MOUTAI"], None),
    (
        "CN/HK",
        "ICBC",
        ["INDUSTRIAL & COMMERCIAL BANK OF CHINA", "INDUSTRIAL AND COMMERCIAL BANK OF CHINA"],
        None,
    ),
    ("CN/HK", "China Mobile", ["CHINA MOBILE"], None),
    ("CN/HK", "PetroChina", ["PETROCHINA"], None),
    ("CN/HK", "Xiaomi", ["XIAOMI"], None),
    ("CN/HK", "Meituan", ["MEITUAN"], None),
    ("CN/HK", "AIA Group", ["AIA GROUP"], None),
    ("CN/HK", "Hong Kong Exchanges", ["HONG KONG EXCHANGES"], None),
    ("CN/HK", "Ping An Insurance", ["PING AN INSURANCE"], None),
    ("CN/HK", "Yum China", ["YUM CHINA"], "YUMC"),
    ("CN/HK", "BeOne Medicines (BeiGene)", ["BEONE MEDICINES", "BEIGENE"], "ONC"),
    ("IN", "Reliance Industries", ["RELIANCE INDUSTRIES"], None),
    ("IN", "HDFC Bank", ["HDFC BANK"], "HDB"),
    ("IN", "Tata Consultancy Services", ["TATA CONSULTANCY"], None),
    ("IN", "Bharti Airtel", ["BHARTI AIRTEL"], None),
    ("IN", "ICICI Bank", ["ICICI BANK"], "IBN"),
    ("IN", "Infosys", ["INFOSYS"], "INFY"),
    ("IN", "State Bank of India", ["STATE BANK OF INDIA"], None),
    ("IN", "Hindustan Unilever", ["HINDUSTAN UNILEVER"], None),
    ("IN", "Wipro", ["WIPRO"], "WIT"),
    ("IN", "Dr. Reddy's Laboratories", ["DR. REDDY", "DR REDDY"], "RDY"),
    ("IN", "MakeMyTrip", ["MAKEMYTRIP"], "MMYT"),
    ("CA", "Royal Bank of Canada", ["ROYAL BANK OF CANADA"], "RY"),
    ("CA", "Toronto-Dominion Bank", ["TORONTO DOMINION"], "TD"),
    ("CA", "Shopify", ["SHOPIFY"], "SHOP"),
    ("CA", "Enbridge", ["ENBRIDGE INC"], "ENB"),
    ("CA", "Canadian Natural Resources", ["CANADIAN NATURAL RESOURCES"], "CNQ"),
    ("CA", "Brookfield Corporation", ["BROOKFIELD CORP"], "BN"),
    ("TW", "Taiwan Semiconductor", ["TAIWAN SEMICONDUCTOR"], "TSM"),
]

ANNUAL = ("10-K", "10-KT", "20-F", "40-F")


def main() -> None:
    from vinci.edgar.concepts import IFRS_NAMESPACE, filer_fiscal_year, reporting_currency
    from vinci.resolver.index import ResolverIndex, normalize_ticker

    http = sec_http()
    ct = http.get_json("https://www.sec.gov/files/company_tickers.json", ttl_seconds=7 * 86400)
    cte = http.get_json(
        "https://www.sec.gov/files/company_tickers_exchange.json", ttl_seconds=7 * 86400
    )
    idx = ResolverIndex.from_sec_files(ct, cte)
    names = {}
    for t in idx.all_tickers():
        for e in idx.ticker_entries(t):
            names.setdefault(e.cik, e.name.upper())
    ed = edgar()
    results = []
    for market, disp, toks, tkr in NAMES:
        r = {"market": market, "name": disp, "tokens": toks, "ticker_tried": tkr}
        by_ticker = sorted(idx.ticker_ciks(normalize_ticker(tkr))) if tkr else []
        by_name = sorted({c for c, n in names.items() if any(t in n for t in toks)})
        r["ticker_ciks"], r["name_ciks"] = by_ticker, by_name
        cands = sorted(set(by_ticker) | set(by_name))
        r["candidate_names"] = {c: names.get(c) for c in cands}
        if not cands:
            hits_by = Counter()
            total = None
            for tok in toks[:2]:
                try:
                    res = ed.fulltext_search(
                        tok.title() if tok.isupper() else tok,
                        forms="20-F,40-F,6-K,10-K",
                        startdt="2024-01-01",
                        enddt="2026-11-19",
                        max_pages=1,
                    )
                    hits = res.hits()
                    total = (total or 0) + len(hits)
                    for h in hits:
                        dn = " ".join(h.display_names).upper()
                        if any(t in dn for t in toks):
                            hits_by[dn[:80]] += 1
                except Exception as exc:  # noqa: BLE001 — recorded as unread, never as absent
                    r.setdefault("fts_errors", []).append(
                        f"{tok}: {type(exc).__name__}: {exc}"[:200]
                    )
            r["fts_hits_read"] = total
            r["fts_self_filer_hits"] = dict(hits_by)
        else:
            per = []
            for cik in cands:
                d = {"cik": cik, "index_name": names.get(cik)}
                try:
                    sub = ed._submissions(cik)
                    rec = sub["filings"]["recent"]
                    rows = list(zip(rec["form"], rec["filingDate"], strict=False))
                    ann = [(f, x) for f, x in rows if f in ANNUAL]
                    d["latest_annual"] = max(ann, key=lambda z: z[1]) if ann else None
                    d["n_6k_365"] = sum(1 for f, x in rows if f == "6-K" and x >= "2025-11-19")
                    d["n_10q_365"] = sum(1 for f, x in rows if f == "10-Q" and x >= "2025-11-19")
                    d["fye"] = sub.get("fiscalYearEnd")
                    d["sic"] = sub.get("sic")
                    d["inc"] = sub.get("stateOfIncorporationDescription") or sub.get(
                        "stateOfIncorporation"
                    )
                    d["tickers"] = sub.get("tickers")
                    d["exchanges"] = sub.get("exchanges")
                except Exception as exc:  # noqa: BLE001
                    d["submissions_error"] = f"{type(exc).__name__}: {exc}"[:200]
                try:
                    facts = ed.companyfacts(cik)
                    ns = facts.get("facts") or {}
                    d["ns_concepts"] = {k: len(v) for k, v in ns.items()}
                    d["reporting_currency"] = reporting_currency(facts)
                    fy = filer_fiscal_year(facts)
                    d["fiscal_year"] = (
                        None
                        if fy is None
                        else {
                            "tag": fy.tag,
                            "unit": fy.unit,
                            "end": fy.period_end.isoformat(),
                            "form": fy.form,
                            "ifrs_end": fy.ifrs_end.isoformat() if fy.ifrs_end else None,
                        }
                    )
                    d["ifrs"] = bool(ns.get(IFRS_NAMESPACE))
                except Exception as exc:  # noqa: BLE001
                    d["companyfacts_error"] = f"{type(exc).__name__}: {exc}"[:200]
                per.append(d)
            r["filers"] = per
        results.append(r)
        print(
            disp,
            "→",
            "ticker" if by_ticker else "",
            "name" if by_name else "",
            "fts" if not cands else "",
            flush=True,
        )
    (OUT / "stage2.json").write_text(json.dumps(results, indent=1, default=str))
    print("written", len(results), "names; fetched", dt.datetime.now().isoformat())


if __name__ == "__main__":
    main()
