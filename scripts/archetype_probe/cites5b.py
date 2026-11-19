"""5b: the source_ref (workbook sha256[:10], sheet, row index, column index + header) of every
CIQ-derived figure the scope pack quotes. Reads through the loader; scratch copies hash-checked
against Drive and deleted at the end. Row/column indices are the loader's 0-based sheet indices."""

from __future__ import annotations

import hashlib
import shutil

from probe_common import SCRATCH, ciq_root

FRESH = ciq_root()  # ARCHETYPE_PROBE_CIQ: <root>/<TICKER>/<files>, read only
TMP = SCRATCH / "cites_tmp"
WANT = [  # (ticker, file suffix, freq, sheet, row labels, how many latest columns)
    (
        "PLD",
        "Financials_Quarterly.xls",
        "quarterly",
        "Balance Sheet",
        ("Cash And Equivalents", "Total Debt", "Net Debt", "Total Cash & ST Investments"),
        1,
    ),
    (
        "AWK",
        "Financials_Quarterly.xls",
        "quarterly",
        "Balance Sheet",
        (
            "Cash And Equivalents",
            "Short Term Investments",
            "Total Debt",
            "Net Debt",
            "Total Cash & ST Investments",
        ),
        1,
    ),
    (
        "RIVN",
        "Financials_Annual.xls",
        "annual",
        "Income Statement",
        ("Gain (Loss) On Sale Of Invest.",),
        2,
    ),
    (
        "RIVN",
        "Financials_Quarterly.xls",
        "quarterly",
        "Income Statement",
        ("Gain (Loss) On Sale Of Invest.",),
        4,
    ),
    (
        "AQN",
        "Financials_Quarterly.xls",
        "quarterly",
        "Historical Capitalization",
        ("Currency", "Total Enterprise Value (TEV)"),
        1,
    ),
    ("AQN", "Financials_Quarterly.xls", "quarterly", "Income Statement", ("Currency",), 1),
]


def main() -> None:
    import vinci
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import _dated_header

    print("vinci:", vinci.__file__)
    try:
        for t, suf, freq, sheet, labels, k in WANT:
            src = next(p for p in (FRESH / t).iterdir() if p.name.endswith(suf))
            (TMP / t).mkdir(parents=True, exist_ok=True)
            dst = TMP / t / src.name
            shutil.copy2(src, dst)
            sha = hashlib.sha256(src.read_bytes()).hexdigest()
            assert sha == hashlib.sha256(dst.read_bytes()).hexdigest()
            rows = CiqBundle.from_files(t, [dst]).sheet("financials", sheet, freq=freq)
            h = _dated_header(rows)
            cols = [i for i, c in enumerate(rows[h]) if i > 0 and str(c).strip()][-k:]
            title = next((str(r[0]).strip() for r in rows[:4] if r and str(r[0]).strip()), "")
            print(f"== {t} `{sha[:10]}` {freq} {sheet} (title: {title[:70]}); header row {h}")
            found = {str(r[0]).strip(): ri for ri, r in enumerate(rows) if ri > h and r}
            for lbl in labels:
                ri = found.get(lbl)
                if ri is None:
                    print(f"   {lbl!r}: ROW ABSENT from the sheet")
                    continue
                cells = "; ".join(
                    f"col {i} [{str(rows[h][i]).replace(chr(10), ' ')}] = "
                    f"{str(rows[ri][i]).strip()}"
                    for i in cols
                )
                print(f"   {lbl!r}: row {ri}: {cells}")
            for r in rows[:h]:
                c = " | ".join(str(x).strip() for x in r if str(x).strip())
                if "Currency" in c or "In Millions" in c:
                    print(f"   header line: {c[:120]}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
        print("scratch copies deleted:", not TMP.exists())


if __name__ == "__main__":
    main()
