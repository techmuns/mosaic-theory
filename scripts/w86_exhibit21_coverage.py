"""W86 — can a 10-K's Exhibit 21 tell a filer's own units from the companies it invests in? A
measurement over `vinci.edgar.exhibit21`, $0 (EDGAR only, through the repo's paced SEC client and
its HTTP cache). Nothing here attributes a Key Development; B's W85 wires the reader after it
merges.

    PYTHONPATH=. python scripts/w86_exhibit21_coverage.py survey [--out <path.json>]
    PYTHONPATH=. python scripts/w86_exhibit21_coverage.py measure --rows <rows.jsonl> \\
        [--through YYYY-MM-DD] [--out <path.json>]
    PYTHONPATH=. python scripts/w86_exhibit21_coverage.py fixtures --out tests/fixtures/exhibit21

- ``survey`` reads the Exhibit 21 of every committed page's filer (``data/dossiers/*``): its
  status, how many names it lists, whether it states that it omits insignificant subsidiaries,
  whether it lists affiliates too, and how many rows state an ownership share below 100%.
- ``measure`` reads a JSONL of rows, each ``{"ticker": …, "entity": …}`` plus optional ``own``
  (true/false: a human's label) and any other keys, which are carried through. Each row's entity is
  matched against its page filer's list (`exhibit21.match_entity`), and the tiers are counted:
  overall, and by ``own`` label when rows carry one.
- ``fixtures`` writes the real documents `tests/test_exhibit21.py` reads (see its README).

Every count printed states its population: the rows file (or the committed pages), the filer's
newest original 10-K filed by ``--through`` (any day when omitted), and the date the run read
EDGAR. (`PYTHONPATH=.` imports THIS checkout's `vinci`; run from the repo root.)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from vinci.edgar.client import EdgarClient
from vinci.edgar.exhibit21 import (
    Exhibit21Read,
    ex21_documents,
    match_entity,
    read_exhibit21,
)
from vinci.netcache import CachedHttp
from vinci.sec import build_sec_http

_DOSSIERS = Path("data/dossiers")
TIERS = ("registrant", "exact", "normalised", "word_prefix", "not_listed", "no_ex21",
         "no_names", "unread", "no_10k")


def _page_cik(ticker: str) -> str:
    page = _DOSSIERS / ticker / "dossier.json"
    if not page.exists():
        raise SystemExit(f"no committed page for {ticker}: {page} is absent")
    cik = json.loads(page.read_text()).get("cik")
    if not cik:
        raise SystemExit(f"{page} carries no cik")
    return str(cik)


def _client() -> tuple[EdgarClient, CachedHttp]:
    http = build_sec_http()
    return EdgarClient(http), http


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def cmd_survey(args: argparse.Namespace) -> int:
    edgar, http = _client()
    out: dict[str, Any] = {}
    tickers = sorted(p.name for p in _DOSSIERS.iterdir() if (p / "dossier.json").exists())
    for t in tickers:
        r = read_exhibit21(edgar, http, _page_cik(t), through=args.through)
        part = sum(1 for n in r.names if n.stated_percent is not None and n.stated_percent < 100)
        out[t] = r.model_dump(mode="json")
        print(f"{t:6} {r.status:8} 10-K {r.accession} filed {r.filing_date}  names={len(r.names):3}"
              f"  omission={'stated' if r.states_omission else '—':6}"
              f"  affiliates={'yes' if r.names_affiliates else '—':3}  share<100%={part}")
    status = Counter(v["status"] for v in out.values())
    omits = sum(1 for v in out.values() if v["states_omission"])
    print(f"\n{len(tickers)} filers (every committed page under {_DOSSIERS}/), newest original "
          f"10-K filed by {args.through or 'any day'}, EDGAR read {_stamp()}:")
    print(f"  status: {dict(status)}")
    print(f"  the exhibit states it omits insignificant subsidiaries: {omits} of {len(tickers)}")
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


def cmd_measure(args: argparse.Namespace) -> int:
    rows = [json.loads(x) for x in Path(args.rows).read_text().splitlines() if x.strip()]
    for i, row in enumerate(rows, 1):
        if "ticker" not in row or "entity" not in row:
            raise SystemExit(f"{args.rows} row {i} carries no ticker or entity: {row}")
        if row.get("own") not in (True, False, None):
            raise SystemExit(f"{args.rows} row {i}: `own` must be true, false or absent, "
                             f"not {row['own']!r}")
    edgar, http = _client()
    reads: dict[str, Exhibit21Read] = {}
    results: list[dict[str, Any]] = []
    for row in rows:
        t = str(row["ticker"])
        if t not in reads:
            reads[t] = read_exhibit21(edgar, http, _page_cik(t), through=args.through)
        m = match_entity(str(row["entity"]), reads[t])
        results.append({**row, "tier": m.tier,
                        "listed": m.listed.model_dump(mode="json") if m.listed else None,
                        "list_states_omission": m.list_states_omission,
                        "accession": reads[t].accession})
    print(f"{'ticker':6} {'own':5} {'tier':11} {'omits':5}  entity → listed name")
    for r in results:
        listed = r["listed"]["name"] if r["listed"] else ""
        pct = (f" ({r['listed']['stated_percent']:g}%)" if r["listed"]
               and r["listed"]["stated_percent"] is not None else "")
        own = {True: "own", False: "not", None: "—"}[r.get("own")]
        omits = "yes" if r["list_states_omission"] else "—"
        print(f"{r['ticker']:6} {own:5} {r['tier']:11} {omits:5}  {r['entity']} → {listed}{pct}")
    filers = sorted(reads)
    print(f"\n{len(results)} rows from {args.rows}, {len(filers)} filers ({', '.join(filers)}), "
          f"each filer's newest original 10-K filed by {args.through or 'any day'}, EDGAR read "
          f"{_stamp()}:")

    def counts(sub: list[dict[str, Any]]) -> str:
        c = Counter(r["tier"] for r in sub)
        return ", ".join(f"{k} {c[k]}" for k in TIERS if c[k])

    print(f"  all {len(results)}: {counts(results)}")
    for label, name in ((True, "own"), (False, "not own"), (None, "unlabelled")):
        sub = [r for r in results if r.get("own") is label]
        if sub:
            print(f"  {name} {len(sub)}: {counts(sub)}")
    if args.out:
        Path(args.out).write_text(json.dumps({"rows": results, "through": str(args.through),
                                              "read": _stamp()}, indent=1) + "\n")
    return 0


#: The fixtures `tests/test_exhibit21.py` reads: ticker → rows kept when the document is cut
#: (None = the whole document). A cut keeps the exhibit's prose and its header rows, and the
#: table rows whose first cell is named here or among the first `_CUT_KEEP` data rows.
FIXTURES: dict[str, tuple[str, ...] | None] = {
    "AMZN": None, "GOOGL": None, "TGT": None, "SMPL": None, "PARR": None, "WERN": None,
    "V": None, "UBER": None,
    "LLY": ("LillyDirect Pharmacy, LLC", "Eli Lilly (Philippines), Incorporated", "Aparito LLC",
            "Eli Lilly and Company Limited", "Eli Lilly S.A."),
    "TJX": ("Leasing Subsidiaries", "NBC Sixth Realty Corp.", "NBC Apparel"),
    "EPAM": ("EPAM Systems LLC",),
}
_CUT_KEEP = 6
#: The SGML headers kept whole: a 10-K that types its EX-21, and a 10-Q that files none.
HEADER_FILINGS = (("GOOGL", "0001652044-26-000018"), ("GOOGL", "0001652044-26-000084"))


def _cut(doc: str, keep: tuple[str, ...]) -> str:
    soup = BeautifulSoup(doc, "html.parser")
    for table in soup.find_all("table"):
        data = 0
        for tr in table.find_all("tr"):
            first = next((c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])
                          if c.get_text(strip=True)), "")
            if not first:
                continue
            if any(k in first for k in keep):
                continue
            data += 1
            if data > _CUT_KEEP + 2:  # header rows count toward the first few kept
                tr.decompose()
    return str(soup)


def cmd_fixtures(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    edgar, http = _client()
    cases: dict[str, Any] = {}
    for t, keep in FIXTURES.items():
        cik = _page_cik(t)
        r = read_exhibit21(edgar, http, cik)
        if r.status != "listed" or len(r.exhibit_urls) != 1 or r.accession is None:
            raise SystemExit(f"{t}: expected one listed exhibit, read {r.status} "
                             f"{r.exhibit_urls}")
        docs = ex21_documents(http, cik, r.accession) or []
        ty, url = docs[0]
        doc = http.get_text(url, ttl_seconds=None)
        if keep is not None:
            doc = _cut(doc, keep)
        (out / f"{t}.htm").write_text(doc)
        cases[t] = {"cik": r.cik, "registrant": edgar.registrant_history(cik).current,
                    "form": "10-K", "accession": r.accession, "filing_date": str(r.filing_date),
                    "type": ty, "url": url, "cut": keep is not None, "kept_rows": list(keep or ())}
    headers: dict[str, Any] = {}
    for t, acc in HEADER_FILINGS:
        cik = _page_cik(t)
        a = acc.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a}/{acc}-index-headers.html"
        name = f"{t}_{acc}-index-headers.html"
        (out / name).write_text(http.get_text(url, ttl_seconds=None))
        headers[acc] = {"ticker": t, "cik": cik, "url": url, "file": name}
    (out / "cases.json").write_text(json.dumps({"read": _stamp(), "exhibits": cases,
                                                "headers": headers}, indent=1) + "\n")
    print(f"wrote {len(cases)} exhibits and {len(headers)} headers to {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("survey")
    s.add_argument("--through", type=date.fromisoformat)
    s.add_argument("--out")
    m = sub.add_parser("measure")
    m.add_argument("--rows", required=True)
    m.add_argument("--through", type=date.fromisoformat)
    m.add_argument("--out")
    f = sub.add_parser("fixtures")
    f.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"survey": cmd_survey, "measure": cmd_measure, "fixtures": cmd_fixtures}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
