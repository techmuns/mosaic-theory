"""5a: why PLD's and AWK's fresh packs build no `ev_bridge`. Reads each quarterly Financials
Balance Sheet through the loader (`CiqBundle.sheet`) and prints, for every row whose label carries
'Cash', 'Debt' or 'Invest', its cells at the latest four dated columns as exported. Scratch copies
(hash-checked against Drive), deleted at the end. Also MORN and RIVN as controls that state the
row."""

from __future__ import annotations

import hashlib
import re
import shutil
import sys
from pathlib import Path

from probe_common import SCRATCH, ciq_root

FRESH = ciq_root()  # ARCHETYPE_PROBE_CIQ: <root>/<TICKER>/<files>, read only
TMP = SCRATCH / "bs_tmp"
PAT = re.compile(r"(cash|debt|invest)", re.I)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(names: list[str]) -> None:
    import vinci
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import _dated_header

    print("vinci:", vinci.__file__)
    try:
        for t in names:
            src = next(
                p for p in (FRESH / t).iterdir() if p.name.endswith("Financials_Quarterly.xls")
            )
            (TMP / t).mkdir(parents=True, exist_ok=True)
            dst = TMP / t / src.name
            shutil.copy2(src, dst)
            assert sha(src) == sha(dst), t
            b = CiqBundle.from_files(t, [dst])
            bs = b.sheet("financials", "Balance Sheet", freq="quarterly")
            hdr = _dated_header(bs)
            head = bs[hdr]
            cols = [i for i, c in enumerate(head) if i > 0 and str(c).strip()][-4:]
            print(
                f"== {t} ({src.name[:40]}…, sha {sha(src)[:10]}) header: "
                f"{[str(head[i])[:24] for i in cols]}"
            )
            hits = [r for r in bs if r and PAT.search(str(r[0]))]
            print(f"   {len(hits)} row(s) matching cash/debt/invest; all shown")
            for r in hits:
                print(
                    f"   {str(r[0]).strip()[:44]:44} "
                    + " | ".join(str(r[i]).strip()[:10] if i < len(r) else "∅" for i in cols)
                )
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
        print("scratch copies deleted:", not TMP.exists())


if __name__ == "__main__":
    main(sys.argv[1:])
