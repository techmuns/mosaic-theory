"""Freeze the Estimates→Surprise cells the listing-block pins read
(`tests/test_surprise_listing_block.py`, audit RA-D1).

DERIVED VALUES ONLY. The licensed workbooks are never committed (CLAUDE.md, operator ruling
2026-11-04 on cut-down fixtures). Each Surprise sheet is read through `vinci.dossier.ciq`'s real
decode path and cut as follows:
- every row keeps its POSITION, because a block's extent is read from where its header sits;
- the rows `ciq_sheets.surprise_history` reads keep their cells: each fiscal-year header row (a
  listing's or "Company Level"'s), the "Fiscal Years" / "Calendar Years" dividers, each
  "EPS (GAAP)" row and the "Revenue" row, and the "Actual" and "Estimate" rows CIQ prints under
  each of those (`ciq_sheets._surprise_basis`: a 0.0 surprise beside an actual and an estimate
  that differ is CIQ's placeholder — fix request 2, prompt-fix 2);
- every other row is blanked to an empty list, and the sheet ends at the last row kept.
The rows are the operator's licensed exports, each named in `_about` with its sha256.

    python scripts/build_surprise_listings_fixture.py <ciq-folder>

`<ciq-folder>` holds one folder per ticker (the operator's Drive `manual/ciq`). It is an operator
tool, never imported by the suite.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from typing import Any

from vinci.dossier.ciq import CiqBundle, clean_num

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "ciq_surprise_listings.json"
#: PARR: the predecessor's OTC block first (the defect). GOOGL: two blocks of its own listing and a
#: second share class's. NFLX: one listing, the shape of every other name on file.
NAMES = ("PARR", "GOOGL", "NFLX")


def _kept(row: list[Any]) -> bool:
    label = str(row[0]).strip() if row else ""
    years = sum(1 for c in row[1:10] if (n := clean_num(c)) is not None and 2000 < n < 2100)
    divider = any(str(c).strip() in ("Fiscal Years", "Calendar Years") for c in row[:3])
    return years >= 3 or divider or label.startswith("EPS (GAAP)") or label == "Revenue"


def _label(row: list[Any]) -> str:
    return str(row[0]).strip() if row and row[0] is not None else ""


def _basis_rows(rows: list[list[Any]]) -> set[int]:
    """The "Actual" / "Estimate" rows within the four rows after each "EPS (GAAP)" or "Revenue"
    row, past its "Difference" row, before the next labelled row — the rows
    `ciq_sheets._surprise_basis` reads."""
    out: set[int] = set()
    for i, r in enumerate(rows):
        if not (_label(r).startswith("EPS (GAAP)") or _label(r) == "Revenue"):
            continue
        for k in range(i + 1, min(i + 5, len(rows))):
            lab = _label(rows[k])
            if lab in ("Actual", "Estimate"):
                out.add(k)
            elif lab and lab != "Difference":
                break
    return out


def _cell(c: Any) -> Any:
    return c if c is None or isinstance(c, (str, int, float)) else str(c)


def cut(folder: pathlib.Path) -> dict[str, Any]:
    out: dict[str, Any] = {"_about": {
        "what": "Estimates→Surprise rows the listing-block pins read; every other row blanked "
                "in place (scripts/build_surprise_listings_fixture.py)",
        "exports": {}}, "names": {}}
    for t in NAMES:
        files = sorted(p for p in (folder / t).iterdir()
                       if p.is_file() and not p.name.startswith("."))
        bundle = CiqBundle.from_files(t, files)
        wb = bundle.workbook("estimates")
        rows = bundle.sheet("estimates", "Surprise")
        keep = {i for i, r in enumerate(rows) if _kept(r)} | _basis_rows(rows)
        last = max(keep)
        cut_rows = [[_cell(c) for c in r] if i in keep else [] for i, r in
                    enumerate(rows[: last + 1])]
        out["names"][t] = {"sheet": "Surprise", "rows": cut_rows}
        out["_about"]["exports"][t] = {
            "file": wb.path.name, "sha256": hashlib.sha256(wb.path.read_bytes()).hexdigest()}
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    OUT.write_text(json.dumps(cut(pathlib.Path(argv[0])), indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
