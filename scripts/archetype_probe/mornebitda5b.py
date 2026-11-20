"""5a addendum: MORN's two LTM EBITDAs (CIQ annual LTM vs the sum of CIQ's four quarters).

Reads, through the loader, MORN's fresh Financials Annual + Quarterly Income Statements: every row
whose label carries EBITDA / EBIT / Operating Income / Depreciation / Amort / Stock-Based /
Restructuring / Impairment / Unusual, at the annual FY2024, FY2025 and LTM columns and the
quarterly Q1 2025 .. Q3 2026 columns — each with its sheet, row index, column index and header, so
every figure carries a source_ref. Then MORN's FILED facts (EDGAR companyfacts): OperatingIncomeLoss
and the D&A tags, quarterly and annual 2024-2026, for an LTM-to-2026-09-30 reconciliation.
Scratch copies hash-checked against Drive and deleted at the end."""

from __future__ import annotations

import datetime as dt
import hashlib
import re
import shutil

from probe_common import SCRATCH, ciq_root, edgar

SRC = ciq_root() / "MORN"
FILES = (
    "Morningstar Inc NasdaqGS MORN Financials_Annual.xls",
    "Morningstar Inc NasdaqGS MORN Financials_Quarterly.xls",
)
TMP = SCRATCH / "morn_tmp"
ROWS = re.compile(
    r"(EBITDA|EBIT\b|EBITA|Operating Income|Depreciation|Amort|Stock-Based|Restructur|"
    r"Impairment|Unusual|Total Revenue|Merger|Legal|Gain \(Loss\))",
    re.I,
)
CIK = "0001289419"


def main() -> None:
    import vinci
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import _dated_header

    print("vinci:", vinci.__file__)
    try:
        TMP.mkdir(exist_ok=True)
        paths = []
        for n in FILES:
            shutil.copy2(SRC / n, TMP / n)
            a = hashlib.sha256((SRC / n).read_bytes()).hexdigest()
            assert a == hashlib.sha256((TMP / n).read_bytes()).hexdigest()
            print(f"{a[:10]}  {n}")
            paths.append(TMP / n)
        b = CiqBundle.from_files("MORN", paths)
        for freq, keep in (("annual", 3), ("quarterly", 7)):
            inc = b.sheet("financials", "Income Statement", freq=freq)
            h = _dated_header(inc)
            cols = [i for i, c in enumerate(inc[h]) if i > 0 and str(c).strip()][-keep:]
            print(
                f"== {freq} Income Statement: header row {h}; columns "
                + "; ".join(f"c{i}={str(inc[h][i]).replace(chr(10), ' ')}" for i in cols)
            )
            for ri, r in enumerate(inc):
                if ri <= h or not r or not ROWS.search(str(r[0])):
                    continue
                print(
                    f"   r{ri:<3} {str(r[0]).strip()[:46]:46} "
                    + " | ".join(str(r[i]).strip()[:9] if i < len(r) else "∅" for i in cols)
                )
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
        print("scratch copies deleted:", not TMP.exists())
    gaap = edgar().companyfacts(CIK)["facts"]["us-gaap"]
    tags = [
        t
        for t in gaap
        if re.search(
            r"^(OperatingIncomeLoss|Depreciation|AmortizationOfIntangible|"
            r"CapitalizedComputerSoftwareAmortization|ShareBasedCompensation|"
            r"RestructuringCharges|AssetImpairment|GoodwillImpairment)",
            t,
        )
    ]
    print(f"== EDGAR {len(tags)} tag(s), duration facts ending 2024-12-31..2026-09-30; all shown")
    for t in sorted(tags):
        rows = set()
        for u, rs in gaap[t]["units"].items():
            if u != "USD":
                continue
            for r in rs:
                if r.get("start") and "2024-12-31" <= r["end"] <= "2026-09-30":
                    d = (dt.date.fromisoformat(r["end"]) - dt.date.fromisoformat(r["start"])).days
                    rows.add((r["end"], d, r["val"] / 1e6, r["form"], r["accn"]))
        for e, d, v, f, a in sorted(rows):
            print(f"   {t[:52]:52} end {e} {d:>3}d {v:>9,.1f} {f:5} {a}")


if __name__ == "__main__":
    main()
