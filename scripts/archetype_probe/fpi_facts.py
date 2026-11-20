"""For every universe CIK whose latest annual report is a 20-F or 40-F: its reporting currency and
namespace, by the repo's own `concepts.reporting_currency` on its companyfacts. Reads a read-only
SEC
cache another checkout holds (ARCHETYPE_PROBE_SEC_CACHE) when it has the document, else fetches
through the repo's client into the probe's own cache. Records which source and its fetched_at."""

from __future__ import annotations

import datetime as dt
import hashlib
import json

from probe_common import OUT, edgar, sec_cache_readonly

READONLY = sec_cache_readonly()  # optional; never written
CF = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def primary_read(url: str) -> tuple[dict, float] | None:
    if READONLY is None:
        return None
    p = READONLY / f"{hashlib.sha256(url.encode()).hexdigest()}.json"
    if not p.exists():
        return None
    entry = json.loads(p.read_text())  # read only; never written
    return json.loads(entry["text"]), float(entry["fetched_at"])


def main() -> None:
    from vinci.edgar.concepts import IFRS_NAMESPACE, filer_fiscal_year, reporting_currency

    subs = [
        json.loads(x) for x in (OUT / "subs_extract.jsonl").read_text().splitlines() if x.strip()
    ]
    fpis = [s for s in subs if s.get("latest_annual") and s["latest_annual"][0] in ("20-F", "40-F")]
    print("FPI annual filers:", len(fpis), flush=True)
    ed = edgar()
    prev = OUT / "fpi_facts.json"
    out = json.loads(prev.read_text()) if prev.exists() else {}  # resumable
    for s in fpis:
        cik = s["cik"]
        if cik in out and "error" not in out[cik]:
            continue
        url = CF.format(cik=cik)
        rec: dict = {}
        try:
            got = primary_read(url)
            if got is not None:
                facts, fa = got
                rec["source"] = "read-only cache (ARCHETYPE_PROBE_SEC_CACHE)"
                rec["fetched_at"] = dt.datetime.fromtimestamp(fa, dt.UTC).date().isoformat()
            else:
                facts = ed.companyfacts(cik)
                rec["source"] = "fetched via EdgarClient"
                rec["fetched_at"] = dt.date.today().isoformat()
            ns = facts.get("facts") or {}
            rec["ns"] = {k: len(v) for k, v in ns.items() if k in ("us-gaap", IFRS_NAMESPACE)}
            rec["reporting_currency"] = reporting_currency(facts)
            fy = filer_fiscal_year(facts)
            rec["fy_end"] = str(fy.period_end) if fy else None
            rec["fy_tag"] = fy.tag if fy else None
            rec["fy_unit"] = fy.unit if fy else None
            rec["ifrs_end"] = str(fy.ifrs_end) if fy and fy.ifrs_end else None
        except Exception as exc:  # noqa: BLE001 — unread, never guessed
            rec["error"] = f"{type(exc).__name__}: {exc}"[:200]
        out[cik] = rec
    (OUT / "fpi_facts.json").write_text(json.dumps(out, indent=1))
    print("done", len(out), flush=True)


if __name__ == "__main__":
    main()
