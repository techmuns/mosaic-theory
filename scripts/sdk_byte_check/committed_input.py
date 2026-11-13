"""A FALLBACK input for a page whose $0 build refuses (on 2026-11-13, PARR: `CiqMislabelledError`).

It is the COMMITTED page with one change: the transcript driver rows whose words are off the page
(RG-D19) are removed. Its transcripts are read by production's reader and checked against the
page's own input record, or not sent, and the input says why. It is not the request a build would
send: it is one input sent through both SDKs, so the page's committed content still reaches them.

    PYTHONPATH=$PWD python -P scripts/sdk_byte_check/committed_input.py TICKER CIQ_ROOT OUT_DIR
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from vinci.evals import replay as rp


def main(ticker: str, ciq_root: Path, out: Path) -> int:
    rp.refuse_inside_repo(out, "the fallback input (it can carry transcript text)")
    page = json.loads(Path(f"data/dossiers/{ticker}/dossier.json").read_text(encoding="utf-8"))
    od = page["mechanical"].get("operating_drivers") or {}
    rows = od.get("rows") or []
    keep = [r for r in rows if not (r.get("tier") == "llm-fenced" and not r.get("verbatim"))]
    od["rows"] = keep
    try:
        tx = rp.transcript_for(ticker, ciq_root=ciq_root, page=page)
        why = "read and checked against the page's input record"
    except Exception as exc:   # the bundle refuses the same export the build refused on
        tx, why = None, f"NOT sent: {type(exc).__name__}: {str(exc)[:120]}"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{ticker}.json").write_text(json.dumps({
        "page": page, "transcript": tx, "kw": {"draws": 5},
        "fallback": {"rows_removed": len(rows) - len(keep), "rows_kept": len(keep),
                     "transcript": why}}), encoding="utf-8")
    print(f"{ticker}: removed {len(rows) - len(keep)} of {len(rows)} driver rows; "
          f"transcript {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])))
