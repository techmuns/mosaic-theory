"""Freeze the CIQ rows and the companyfacts the filed-tiebreak pins read
(`tests/test_filed_tiebreak.py`).

DERIVED VALUES ONLY. The licensed workbooks are never committed (CLAUDE.md). Each Income
Statement is read through `vinci.dossier.ciq`'s real decode path and cut as follows:
- the period-header row is kept whole;
- the core rows `ltm_quarters` reads (Total Revenue, EBITDA, EBIT, Net Income) are kept, plus the
  unusual-items delimiters and each name's pinned rows;
- values survive only in the annual LTM column and the newest fiscal year, and in the four
  quarters ending on the LTM's date plus the newest quarter. Every other cell is blanked.
The CIQ rows are the operator's licensed exports as of the date in `_about`.

The companyfacts are cut BY CONCEPT, as `build_companyfacts_fixture.py` does: every row of each
concept `filed_tiebreak.MAPPING` names, unmodified, plus the extra concepts a pin reads (NFLX's
whole non-operating line). They are SEC's public data, fetched on the date in `_about`.

    python scripts/build_filed_tiebreak_fixture.py <ciq-folder> <companyfacts-dir>

`<ciq-folder>` holds one folder per ticker (the operator's Drive `manual/ciq`).
`<companyfacts-dir>` holds `<TICKER>.json` (SEC's companyfacts response). It is an operator tool,
never imported by the suite.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from datetime import date
from typing import Any

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import filed_tiebreak, ltm_quarters
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.materiality import unusual_items_block

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "filed_tiebreak.json"
CORE = ("Total Revenue", "EBITDA", "EBIT", "Net Income")
#: Each name, the CIQ rows its pins read, and the companyfacts concepts beyond the mapped ones.
NAMES: dict[str, dict[str, Any]] = {
    "CELH": {"rows": ("Merger & Related Restruct. Charges", "Other Unusual Items")},
    "NFLX": {"rows": ("Merger & Related Restruct. Charges", "Interest and Invest. Income",
                      "Currency Exchange Gains (Loss)", "Other Non-Operating Inc. (Exp.)"),
             "tags": ("NonoperatingIncomeExpense",)},
    "EPAM": {"rows": ("Restructuring Charges", "Merger & Related Restruct. Charges",
                      "Other Unusual Items")},
    "BDX": {"rows": ("Other Unusual Items",)},
    "NKE": {"rows": ("Restructuring Charges",)},
}


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:10]


def _cut(sheet: list[list[Any]], keep_rows: set[str], keep_cols: set[int],
         block: tuple[int, int]) -> list[list[Any]]:
    hdr = cs._period_header(sheet)
    assert hdr is not None
    out = [list(sheet[hdr])]
    lo, hi = block
    for i, r in enumerate(sheet):
        lab = str(r[0] or "").strip() if r else ""
        delimiter = i in (lo - 1, hi)
        if not (lab in keep_rows or delimiter):
            continue
        if lab in CORE and lo <= i < hi:
            continue
        out.append([r[0]] + [("" if delimiter or j not in keep_cols else
                              (r[j] if j < len(r) else ""))
                             for j in range(1, len(sheet[hdr]))])
    return out


def build(ciq: pathlib.Path, cf_dir: pathlib.Path) -> dict[str, Any]:
    names: dict[str, Any] = {}
    for t, spec in NAMES.items():
        folder = ciq / t
        b = CiqBundle.from_files(t, sorted(folder.iterdir()))
        ann = b.sheet("financials", "Income Statement", freq="annual")
        qtr = b.sheet("financials", "Income Statement", freq="quarterly")
        ahdr, qhdr = cs._period_header(ann), cs._period_header(qtr)
        assert ahdr is not None and qhdr is not None
        periods = cs._fin_periods(ann[ahdr])
        ltm = [(c, cs.header_period(ann[ahdr][c])) for c, _s, is_ltm, _r in periods if is_ltm][0]
        fy = [c for c, _s, is_ltm, _r in periods if not is_ltm][-1]
        end = ltm[1].end
        assert end is not None
        four, why = ltm_quarters._four_quarters(qtr, qhdr, end)
        assert four is not None, why
        qcols = {j for j, _p in four} | {len(qtr[qhdr]) - 1}
        rows = set(CORE) | set(spec["rows"])
        sheets = {
            "financials|annual|Income Statement":
                _cut(ann, rows, {ltm[0], fy}, unusual_items_block(ann)),
            "financials|quarterly|Income Statement":
                _cut(qtr, rows, qcols, unusual_items_block(qtr)),
        }
        files = {p.name: p for p in folder.iterdir()}
        wb = {freq: next(n for n in files if f"Financials_{freq.title()}" in n)
              for freq in ("annual", "quarterly")}
        facts = json.loads((cf_dir / f"{t}.json").read_text())
        tags = sorted({tg for line in filed_tiebreak.MAPPING.values() for tg in line.tags}
                      | set(spec.get("tags", ())))
        gaap = facts["facts"].get("us-gaap", {})
        names[t] = {
            "folder": f"ciq/{t}",
            "workbooks": {freq: {"file": n, "sha": _sha(files[n])} for freq, n in wb.items()},
            "comps_export_stamp": str(cs.comps_export_stamp(b)),
            "market_cap": cs.comps_market_cap(b).value,
            "sheets": sheets,
            "companyfacts": {"cik": facts.get("cik"), "entityName": facts.get("entityName"),
                             "facts": {"us-gaap": {tg: gaap[tg] for tg in tags if tg in gaap}}},
        }
    return {
        "_about": (
            "The filed tiebreak for the LTM check (2026-11-04). CIQ rows cut "
            f"{date.today()} from the operator's Drive exports named here (sha256 prefixes), "
            "through vinci.dossier.ciq's real decode path: each Income Statement's period-header "
            "row whole, the core rows ltm_quarters reads, the unusual-items delimiters and the "
            "pinned rows, values kept only in the LTM and newest fiscal-year columns (annual) and "
            "the four quarters ending on the LTM date plus the newest quarter (quarterly). "
            "DERIVED values only; the workbooks are never committed. `market_cap` is "
            "ciq_sheets.comps_market_cap ($M). `companyfacts` is SEC's companyfacts response "
            f"fetched {date.today()}, cut by concept to every concept filed_tiebreak.MAPPING "
            "names (plus NFLX's NonoperatingIncomeExpense), each concept's rows unmodified. "
            "Rebuild: scripts/build_filed_tiebreak_fixture.py."),
        "names": names,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    OUT.write_text(json.dumps(build(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])),
                              indent=1, sort_keys=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
