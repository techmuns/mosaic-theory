"""What a CIQ Financials export says it is: for each named workbook in a pack, its sha256 prefix,
its
sheets, and on the Income Statement and Balance Sheet the header lines (Period Type, Template,
Currency) and the first and last column headers. This is how DVN's 2026-11-19 re-export was read as
an annual export a second time. The workbooks are copied from ARCHETYPE_PROBE_CIQ into the work
folder, hash-checked, and deleted at the end; no cell value is printed.

    python scripts/archetype_probe/xls_headers5b.py DVN Financials_Annual.xls
    Financials_Quarterly.xls
"""

from __future__ import annotations

import hashlib
import shutil
import sys

from probe_common import SCRATCH, ciq_root

KEYS = ("Period Type", "Template", "Currency:", "Order:", "Frequency")


def main(args: list[str]) -> None:
    import vinci
    from vinci.dossier.ciq import classify, read_sheets

    print("vinci:", vinci.__file__)
    if len(args) < 2:
        raise SystemExit("usage: xls_headers5b.py TICKER FILE_SUFFIX [FILE_SUFFIX ...]")
    ticker, suffixes = args[0], args[1:]
    tmp = SCRATCH / "xls_headers_tmp"
    try:
        tmp.mkdir(exist_ok=True)
        for suf in suffixes:
            src = next((p for p in (ciq_root() / ticker).iterdir() if p.name.endswith(suf)), None)
            if src is None:
                raise SystemExit(f"{ticker}: no file ending {suf!r} under the CIQ root")
            dst = tmp / src.name
            shutil.copy2(src, dst)
            sha = hashlib.sha256(src.read_bytes()).hexdigest()
            assert sha == hashlib.sha256(dst.read_bytes()).hexdigest(), src.name
            sheets = read_sheets(dst, classify(dst))
            print(
                f"== {sha[:10]} {src.name} ({src.stat().st_size} bytes): {len(sheets)} sheets "
                f"{list(sheets)}"
            )
            for name in ("Income Statement", "Balance Sheet"):
                rows = sheets.get(name) or []
                for r in rows[:16]:
                    line = " | ".join(str(c).strip() for c in r if str(c).strip())
                    if any(k in line for k in KEYS):
                        print(f"   {name}: {line[:150]}")
                hdr = next((r for r in rows if r and sum(1 for c in r if "20" in str(c)) > 3), None)
                if hdr is not None:
                    cells = [str(c).replace("\n", " ") for c in hdr[1:] if str(c).strip()]
                    print(f"   {name}: {len(cells)} columns, first {cells[:2]}, last {cells[-3:]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        print("scratch copies deleted:", not tmp.exists())


if __name__ == "__main__":
    main(sys.argv[1:])
