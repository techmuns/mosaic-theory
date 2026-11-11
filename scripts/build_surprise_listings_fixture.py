"""Freeze the Estimates→Surprise cells the listing-block pins read
(`tests/test_surprise_listing_block.py`, audit RA-D1).

DERIVED VALUES ONLY. The licensed workbooks are never committed (CLAUDE.md, operator ruling
2026-11-04 on cut-down fixtures). Each Surprise sheet is read through `vinci.dossier.ciq`'s real
decode path and cut as follows:
- every row keeps its POSITION, because a block's extent is read from where its header sits;
- the rows `ciq_sheets.surprise_history` reads keep their cells: each fiscal-year header row (a
  listing's or "Company Level"'s), the "Fiscal Years" / "Calendar Years" dividers, each
  "EPS (GAAP)" row and the "Revenue" row;
- the "Actual" and "Estimate" rows `surprise_history` itself reads (a 0.0 surprise beside an
  actual and an estimate that differ is CIQ's placeholder — fix request 2, prompt-fix 2), found
  by running it and recording each surprise row whose basis it reads, then cut by the reader's
  own walk (`ciq_sheets._surprise_basis_rows`). Only the selected listing's fiscal-year block is
  read, so no other listing's, Company Level's or Calendar Years' rows are kept; within a kept
  row, only the columns where its surprise row states a number keep their cells, and the others
  are blanked to null in place (review round 2: the first cut kept 46 rows, 12 of them read);
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
from unittest import mock

from vinci.dossier import ciq_sheets as cs
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


def _basis_cells(bundle: CiqBundle, rows: list[list[Any]]) -> dict[int, set[int]]:
    """The "Actual" / "Estimate" rows `ciq_sheets.surprise_history` reads in ``rows``, each with
    the columns where its surprise row states a number — the cells `_surprise_cell` compares."""
    read: list[int] = []
    real = cs._surprise_basis

    def spy(r: Any, ri: int) -> tuple[dict[int, float], dict[int, float]]:
        read.append(ri)
        return real(r, ri)

    with mock.patch.object(cs, "_surprise_basis", spy):
        cs.surprise_history(bundle)
    out: dict[int, set[int]] = {}
    for ri in read:
        cols = {j for j in range(1, len(rows[ri])) if clean_num(rows[ri][j]) is not None}
        for _label, i in cs._surprise_basis_rows(rows, ri):
            out.setdefault(i, set()).update(cols)
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
        basis = _basis_cells(bundle, rows)
        keep = {i for i, r in enumerate(rows) if _kept(r)}
        last = max(keep | set(basis))
        cut_rows = [
            [_cell(c) if j == 0 or j in basis[i] else None for j, c in enumerate(r)]
            if i in basis else [_cell(c) for c in r] if i in keep else []
            for i, r in enumerate(rows[: last + 1])]
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
