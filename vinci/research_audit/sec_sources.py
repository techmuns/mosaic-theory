"""SEC primary sources the audit leans on — never a guess where a filing can answer.

1. ``sec_tickers`` — SEC's own ticker → CIK → registrant-name map. The SECOND opinion on identity:
   when Polygon's name fails the workbook name check (Polygon spells MAR "Marriot International"),
   the security is confirmed only if Polygon's CIK IS the SEC registrant for that ticker AND the
   SEC registrant name contains the workbook's company name.

2. ``assign_sectors`` — a stock's sector is read from WHICH Vanguard sector fund holds it, per that
   fund's N-PORT-P holdings filing (Vanguard World Fund, CIK 52848; the funds track MSCI US IMI
   25/50 GICS sector indexes). That fund's ETF is then the stock's sector PROXY benchmark. A stock
   no sector fund holds (a foreign issuer, an MLP) gets NO sector benchmark — reported, not
   substituted from a SIC-code heuristic.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, cast

from vinci.config import sec_user_agent
from vinci.netcache import CachedHttp

SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVE_DOC = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/primary_doc.xml"
TICKERS = "https://www.sec.gov/files/company_tickers.json"
TICKERS_MF = "https://www.sec.gov/files/company_tickers_mf.json"


def sec_http(cache_dir: Path) -> CachedHttp:
    return CachedHttp(cache_dir=cache_dir, user_agent=sec_user_agent(), min_interval_sec=0.15,
                      max_retries=4, timeout_sec=60.0, namespace="sec")


# --- names ----------------------------------------------------------------------------------------

_STOP = frozenset({
    "inc", "incorporated", "corp", "corporation", "co", "company", "plc", "ltd", "limited", "the",
    "class", "a", "b", "c", "common", "stock", "shares", "share", "ordinary", "lp", "l", "p", "n",
    "v", "nv", "s", "sa", "ag", "se", "new", "units", "unit", "representing", "partnership",
    "partner", "interests", "&", "and", "md", "de", "ny", "nj", "va", "pa", "oh", "tx", "ca", "del",
})
_SYN = {"cos": "companies", "intl": "international", "hldgs": "holdings", "grp": "group",
        "labs": "laboratories", "svcs": "services", "technolog": "technologies"}


def name_tokens(name: str) -> frozenset[str]:
    toks = re.findall(r"[a-z0-9&]+", name.lower())
    return frozenset(_SYN.get(t, t) for t in toks if _SYN.get(t, t) not in _STOP)


def names_match(a: str, b: str) -> bool:
    """Equal significant-token sets, or one a subset of the other when the smaller has ≥2 tokens.
    Deliberately strict: a single shared word ('United') is never a match."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    small, big = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return len(small) >= 2 and small <= big


# --- SEC ticker map -------------------------------------------------------------------------------

def sec_tickers(http: CachedHttp) -> dict[str, tuple[str, str]]:
    """``{TICKER: (cik10, registrant title)}`` from SEC's company_tickers.json."""
    raw = cast(dict[str, Any], http.get_json(TICKERS, ttl_seconds=7 * 86_400.0))
    return {str(r["ticker"]).upper(): (str(r["cik_str"]).zfill(10), str(r["title"]))
            for r in raw.values()}


# --- Vanguard sector funds via N-PORT -------------------------------------------------------------

@dataclass(frozen=True)
class Holding:
    etf: str
    series_id: str
    series_name: str
    report_date: str
    accession: str
    name: str
    cusip: str
    isin: str
    pct_of_fund: float


@dataclass(frozen=True)
class SectorAssignment:
    audit_ticker: str
    status: str  # ASSIGNED | NOT_HELD_BY_ANY_SECTOR_FUND | AMBIGUOUS
    sector: str = ""
    etf: str = ""
    holding_name: str = ""
    cusip: str = ""
    report_date: str = ""
    accession: str = ""
    detail: str = ""


def _series_of(http: CachedHttp, etfs: tuple[str, ...]) -> dict[str, tuple[str, str]]:
    """ETF ticker → (cik, seriesId) from SEC's mutual-fund ticker map; every ETF must resolve."""
    raw = cast(dict[str, Any], http.get_json(TICKERS_MF, ttl_seconds=7 * 86_400.0))
    out = {str(r[3]): (str(r[0]), str(r[1])) for r in raw["data"] if str(r[3]) in etfs}
    missing = sorted(set(etfs) - set(out))
    if missing:
        raise RuntimeError(f"SEC fund ticker map has no series for {missing}")
    return out


def _parse_nport(xml_text: str) -> tuple[str, str, str, list[tuple[str, str, str, float]]]:
    root = ET.fromstring(xml_text)
    sid = root.findtext(".//{*}seriesId") or ""
    sname = root.findtext(".//{*}seriesName") or ""
    rep = root.findtext(".//{*}repPdDate") or ""
    rows: list[tuple[str, str, str, float]] = []
    for inv in root.iter():
        if not inv.tag.endswith("invstOrSec"):
            continue
        isin_el = inv.find(".//{*}isin")
        rows.append((inv.findtext("{*}name") or "", inv.findtext("{*}cusip") or "",
                     isin_el.get("value", "") if isin_el is not None else "",
                     float(inv.findtext("{*}pctVal") or 0.0)))
    return sid, sname, rep, rows


def sector_fund_holdings(http: CachedHttp, etfs: tuple[str, ...]) -> dict[str, list[Holding]]:
    """report date → holdings of every sector fund that filed a public N-PORT-P for it."""
    series = _series_of(http, etfs)
    etf_of = {sid: etf for etf, (_, sid) in series.items()}
    by_date: dict[str, list[Holding]] = {}
    for cik in sorted({c for c, _ in series.values()}):
        sub = cast(dict[str, Any], http.get_json(SUBMISSIONS.format(cik=cik.zfill(10)),
                                                ttl_seconds=86_400.0))
        r = sub["filings"]["recent"]
        for form, acc, rep in zip(r["form"], r["accessionNumber"], r["reportDate"], strict=True):
            if form != "NPORT-P" or not rep or rep < "2023-06-30":
                continue
            url = ARCHIVE_DOC.format(cik=int(cik), acc=acc.replace("-", ""))
            sid, sname, rep_doc, rows = _parse_nport(http.get_text(url, ttl_seconds=None))
            if sid not in etf_of:
                continue
            by_date.setdefault(rep_doc or rep, []).extend(
                Holding(etf=etf_of[sid], series_id=sid, series_name=sname,
                        report_date=rep_doc or rep, accession=acc, name=n, cusip=c, isin=i,
                        pct_of_fund=p) for n, c, i, p in rows)
    return by_date


def _sector_label(series_name: str) -> str:
    """'VANGUARD ENERGY INDEX FUND' → 'Energy' (the filing's own words, minus the wrapper)."""
    core = re.sub(r"^vanguard\s+|\s+index fund$", "", series_name.strip(), flags=re.IGNORECASE)
    return core.strip().title()


def assign_sectors(holdings: dict[str, list[Holding]], names: dict[str, list[str]],
                   first_entry: dict[str, date],
                   etfs: tuple[str, ...]) -> dict[str, SectorAssignment]:
    """For each ticker: the latest N-PORT report date on/before its first entry at which ALL sector
    funds filed; if no fund holds it then, later dates are tried (stated in ``detail``)."""
    complete = sorted(d for d, hs in holdings.items() if {h.etf for h in hs} >= set(etfs))
    out: dict[str, SectorAssignment] = {}
    for t, cands in sorted(names.items()):
        entry = first_entry[t].isoformat()
        before = [d for d in complete if d <= entry]
        order = ([before[-1]] if before else []) + [d for d in complete if d > entry]
        found: SectorAssignment | None = None
        for d in order:
            hits = [h for h in holdings[d] if any(names_match(h.name, c) for c in cands if c)]
            funds = sorted({h.etf for h in hits})
            if len(funds) > 1:
                found = SectorAssignment(t, "AMBIGUOUS", report_date=d,
                                         detail=f"held by {funds}: {[h.name for h in hits]}")
                break
            if funds:
                h = hits[0]
                late = "" if d == order[0] and before else f" (first found at {d}, after entry)"
                found = SectorAssignment(
                    t, "ASSIGNED", sector=_sector_label(h.series_name), etf=h.etf,
                    holding_name=h.name, cusip=h.cusip, report_date=d, accession=h.accession,
                    detail=f"N-PORT-P {h.accession} ({h.series_name}, period {d}) holds "
                           f"'{h.name}' CUSIP {h.cusip}{late}")
                break
        out[t] = found or SectorAssignment(
            t, "NOT_HELD_BY_ANY_SECTOR_FUND",
            detail=f"no Vanguard sector fund N-PORT ({len(order)} period(s) checked from "
                   f"{order[0] if order else '—'}) lists a holding matching {cands}")
    return out
