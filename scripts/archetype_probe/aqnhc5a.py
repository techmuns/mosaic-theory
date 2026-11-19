"""5a, AQN: what the one CAD panel is. Prints the quarterly Historical Capitalization sheet's top
rows (header, currency/unit lines) and its rows at the latest four dated columns, through the
loader; and the same columns' 'Currency' row in the quarterly Income Statement. Scratch copy,
hash-checked, deleted at the end."""

from __future__ import annotations

import hashlib
import shutil

from probe_common import SCRATCH, ciq_root

SRC = ciq_root() / "AQN" / "Algonquin Power Utilities Corp TSX AQN Financials_Quarterly.xls"
TMP = SCRATCH / "hc_tmp"


def main() -> None:
    import vinci
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import _dated_header

    print("vinci:", vinci.__file__)
    try:
        TMP.mkdir(exist_ok=True)
        dst = TMP / SRC.name
        shutil.copy2(SRC, dst)
        assert (
            hashlib.sha256(SRC.read_bytes()).digest() == hashlib.sha256(dst.read_bytes()).digest()
        )
        b = CiqBundle.from_files("AQN", [dst])
        for sheet in ("Historical Capitalization", "Income Statement"):
            rows = b.sheet("financials", sheet, freq="quarterly")
            hdr = _dated_header(rows)
            cols = [i for i, c in enumerate(rows[hdr]) if i > 0 and str(c).strip()][-4:]
            print(f"== {sheet}: {len(rows)} rows; header row {hdr}; latest 4 columns shown")
            for r in rows[:hdr]:
                cells = [str(c).strip() for c in r if str(c).strip()]
                if cells:
                    print("   top |", " | ".join(cells)[:200])
            for r in rows[hdr:]:
                if not r or not str(r[0]).strip():
                    continue
                lbl = str(r[0]).strip()
                if sheet == "Income Statement" and lbl not in (
                    "Currency",
                    "Total Revenue",
                    "EBITDA",
                ):
                    continue
                print(
                    f"   {lbl[:40]:40} "
                    + " | ".join(str(r[i]).strip()[:12] if i < len(r) else "∅" for i in cols)
                )
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
        print("scratch copy deleted:", not TMP.exists())


if __name__ == "__main__":
    main()
