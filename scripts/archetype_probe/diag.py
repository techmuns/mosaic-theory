"""Targeted second looks at the probe's anomalies, through the same readers (cached
companyfacts)."""

from __future__ import annotations

import datetime as dt

from probe_common import edgar

TODAY = dt.date(2026, 11, 19)
ed = edgar()


def facts(cik):
    from vinci.edgar.concepts import facts_as_of

    return facts_as_of(ed.companyfacts(cik), TODAY)


def revenue_detail(label, cik):
    from vinci.dossier import anchor as an
    from vinci.dossier import midcycle as mc
    from vinci.edgar.concepts import CONCEPT_ALIASES

    f = facts(cik)
    print(f"--- {label}: revenue aliases (raw annual points per alias) ---")
    for tag in CONCEPT_ALIASES["revenue"]:
        s = mc._series_from_points("revenue", tag, mc._annual_points(f, tag, "revenue"))
        print(f"  {tag}: {s.n_years}y {dict(sorted(s.by_year.items())[-6:])}")
    oi = mc.annual_series(f, "operating_income")
    print(f"  OperatingIncomeLoss: {oi.n_years}y {dict(sorted(oi.by_year.items())[-6:])}")
    rev_s, conflicts = an._total_revenue_series(f)
    print(f"  CHOSEN: {rev_s.tag if rev_s else None} {rev_s.by_year if rev_s else None}")
    for c in conflicts[:4]:
        print("   conflict:", c[:260])
    if len(conflicts) > 4:
        print(f"   …showing 4 of {len(conflicts)} conflicts")
    if rev_s:
        ma = mc.margin_anchor(rev_s, oi)
        print(
            "  margin by year:",
            {y: round(v, 3) for y, v in ma.by_year.items()},
            "median",
            ma.median,
        )
    lease = (f["facts"].get("us-gaap") or {}).get("OperatingLeasesIncomeStatementLeaseRevenue")
    if lease:
        pts = [u for u in lease["units"]["USD"] if u.get("fp") == "FY" and u.get("form") == "10-K"]
        print(
            "  OperatingLeasesIncomeStatementLeaseRevenue FY points:",
            len(pts),
            sorted({(p["end"], p["val"]) for p in pts})[-3:],
        )


def shares_detail(label, cik):
    f = facts(cik)
    print(f"--- {label}: share-count tags ---")
    for ns, tag in (
        ("dei", "EntityCommonStockSharesOutstanding"),
        ("us-gaap", "CommonStockSharesOutstanding"),
    ):
        node = (f["facts"].get(ns) or {}).get(tag)
        if not node:
            print(f"  {ns}:{tag}: absent")
            continue
        pts = [p for rows in node["units"].values() for p in rows]
        pts.sort(key=lambda p: (p["end"], p["filed"]))
        print(
            f"  {ns}:{tag}: {len(pts)} points, newest 3:",
            [(p["end"], p["val"], p["form"], p["filed"]) for p in pts[-3:]],
        )


def debt_tags(label, cik):
    f = facts(cik)
    print(f"--- {label}: us-gaap debt/notes/cash tags with an instant on or after 2026-01-01 ---")
    shown = 0
    hits = []
    for tag, node in (f["facts"].get("us-gaap") or {}).items():
        if not any(k in tag for k in ("Debt", "Notes", "Borrowing", "CashAndCashEquivalents")):
            continue
        pts = [
            p for p in node["units"].get("USD", []) if "start" not in p and p["end"] >= "2026-01-01"
        ]
        if pts:
            p = max(pts, key=lambda p: (p["end"], p["filed"]))
            hits.append((tag, p["end"], p["val"]))
    for h in sorted(hits)[:20]:
        print("  ", h)
        shown += 1
    if len(hits) > shown:
        print(f"   …showing {shown} of {len(hits)}")


def subs(label, cik):
    s = ed._submissions(cik)
    r = s["filings"]["recent"]
    print(
        f"--- {label}: {s.get('name')} tickers={s.get('tickers')} "
        f"former={[x['name'] for x in s.get('formerNames', [])][:3]}"
    )
    for f_, d, it in list(zip(r["form"], r["filingDate"], r.get("items", []), strict=False))[:8]:
        print("  ", d, f_, it)


revenue_detail("INVH", "0001687229")
revenue_detail("NBIS", "0001513845")
shares_detail("NEE", "0000753308")
shares_detail("PLD", "0001045609")
shares_detail("EL", "0001001250")
shares_detail("HSY", "0000047111")
shares_detail("BRK", "0001067983")
debt_tags("CME", "0001156375")
debt_tags("ISRG", "0001035267")
debt_tags("ORCL", "0001341439")
subs("XOM new CIK", "0002115436")
subs("XOM old CIK", "0000034088")
