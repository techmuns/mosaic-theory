"""5a, MORN: does Morningstar hold quarterly earnings calls? Read from its OWN filings through the
repo's EDGAR client (full-text search scoped to MORN's CIK, and its 8-K list with items).
Several vocabularies: the call words AND the written-answer words."""

from __future__ import annotations

import datetime as dt
import json

from probe_common import OUT, edgar

CIK = "0001289419"
PHRASES = [
    "earnings call",
    "conference call",
    "earnings conference call",
    "shareholder questions",
    "questions from shareholders",
    "investor questions",
    "responses to shareholder",
    "written responses",
    "does not host",
    "do not hold",
]


def main() -> None:
    import vinci

    print("vinci:", vinci.__file__)
    e = edgar()
    out: dict = {"cik": CIK, "window": "2023-01-01..2026-11-19", "fts": {}}
    for ph in PHRASES:
        for forms in ("8-K", "10-K"):
            r = e.fulltext_search(
                ph, forms=forms, ciks=CIK, startdt="2023-01-01", enddt="2026-11-19"
            )
            hits = list(r)
            out["fts"][f"{forms}|{ph}"] = {
                "read": len(hits),
                "total": getattr(r, "total", None),
                "capped": r.capped,
                "hits": [
                    {"acc": h.accession, "form": h.form, "date": str(h.file_date)}
                    for h in hits[:40]
                ],
                "shown": f"{min(len(hits), 40)} of {len(hits)}",
            }
            print(f"{forms:5} {ph!r:34} read {len(hits)} capped {r.capped}")
    fil = e.recent_filings(CIK, forms=("8-K",), since=dt.date(2025, 1, 1))
    out["8k_since_2025"] = [
        {
            "date": str(f.filing_date),
            "acc": f.accession,
            "items": getattr(f, "items", None),
            "doc": getattr(f, "primary_document", None),
        }
        for f in fil
    ]
    print(f"8-Ks since 2025-01-01: {len(fil)}")
    for f in out["8k_since_2025"]:
        print("  ", f)
    (OUT / "morn5a.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
