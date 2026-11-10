"""An export in thousands is refused, and the Consensus stats and Recent Changes are read by their
headers (fix request 2, order 4: audits RA-D9 and RA-D14; 2026-11-10).

* RA-D9 — ONLY THE BRIDGE READ THE UNIT. The anchor bridge refuses a statement whose own unit
  line is not Millions (#863), but the readers that print the page assume $M: an export in
  thousands printed "Revenue ($M) 67,357,000". `ciq_sheets.require_millions` refuses it where
  `require_usd` refuses another currency — at assembly before any fetch, and on the anchor's path.
* RA-D14 — TARGET PRICE AND RECENT CHANGES WERE READ BY COLUMN POSITION. A Mean/Median swap
  printed SMPL's target as mean $14.00 / median $14.88, and a Broker Value Prior/Current swap
  printed its Interest Expense revision the wrong way round. Every column is now found by its
  header, and a missing header leaves the read UNKNOWN, never positional.

The real-export pins mutate SMPL's export in memory as it stands, and skip where the licensed
folder is absent, as on CI. The constructed twins run everywhere.
"""
from __future__ import annotations

import re
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import SourceStatus

_PAGES = ("AMZN", "BRBR", "BURL", "CNXC", "EPAM", "FUBO", "GOOGL", "IT", "LLY", "MCK", "MVST",
          "NCNO", "NFLX", "NKE", "ORKA", "PARR", "ROST", "SMPL", "TECX", "TGT", "TJX", "UBER",
          "V", "VITL", "VRRM", "WERN", "WLK")
_IN_MILLIONS = re.compile(r"^In Millions of ")


def _real(ticker: str) -> CiqBundle:
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


def _zzfx() -> CiqBundle:
    return CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))


def _restate_unit(rows: list[list[Any]], unit: str) -> None:
    for row in rows[:14]:
        for j, cell in enumerate(row):
            if isinstance(cell, str) and _IN_MILLIONS.match(cell.strip()):
                row[j] = cell.replace("In Millions of", f"In {unit} of", 1)
                return
    raise AssertionError("the sheet states no 'In Millions of' line to restate")


# --- RA-D9 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("make", [lambda: _real("SMPL"), _zzfx], ids=["SMPL", "twin"])
def test_ra_d9_a_statement_in_thousands_is_refused_before_assembly(make: Any) -> None:
    """(+) The annual Income Statement's unit line restated as Thousands: refused, the sheet named.
    (−) As exported: nothing is refused."""
    b = make()
    cs.require_millions(b, b.ticker)
    _restate_unit(b.sheet("financials", "Income Statement", freq="annual"), "Thousands")
    with pytest.raises(cs.CiqUnitError,
                       match=r"Financials \(annual\)→Income Statement: Thousands"):
        cs.require_millions(b, b.ticker)


def test_ra_d9_no_committed_pages_export_states_another_unit() -> None:
    """(−) CORPUS BEFORE SYNTHETIC: every page's export as it stands passes (2026-11-10: all 720
    money sheets on disk state Millions)."""
    store = LocalFolderStore.from_config(get_config())
    held = [t for t in _PAGES if store.files(t)]
    if not held:
        pytest.skip("no licensed CIQ bundle on this machine (never committed)")
    for t in held:
        cs.require_millions(CiqBundle.from_files(t, store.files(t)), t)


def test_ra_d9_both_refusal_paths_call_it() -> None:
    """A SOURCE PIN, AND ITS LIMIT STATED: assembly and the anchor's CIQ path need the network and
    a store; each must refuse as `require_usd` does."""
    import inspect

    from vinci.dossier import anchor, mechanical

    assert "ciq_sheets.require_millions(bundle, record.identity.ticker)" in inspect.getsource(
        mechanical)
    src = inspect.getsource(anchor.ciq_bridge)
    assert "require_millions(bundle, ticker)" in src and "CiqUnitError" in src


# --- RA-D14 --------------------------------------------------------------------------------------


def _swap(rows: list[list[Any]], first: int, last: int, a: int, b: int) -> None:
    for r in rows[first:last]:
        if len(r) > max(a, b):
            r[a], r[b] = r[b], r[a]


def test_ra_d14_a_mean_median_swap_reads_the_same_target() -> None:
    """THE AUDIT'S CASE on SMPL's export as it stands: the Mean and Median columns swapped, header
    included. The target and LT growth read exactly as before."""
    b = _real("SMPL")
    before_view, before_stats = cs.consensus_view(b), cs.consensus_stats(b)
    rows = b.sheet("estimates", "Consensus")
    tp = cs._find_row_prefix(rows, "Target Price")
    assert tp is not None
    hdr = next(k for k in range(tp - 1, tp - 6, -1) if "Mean" in [str(c).strip() for c in rows[k]])
    cells = [str(c).strip() for c in rows[hdr]]
    _swap(rows, hdr, tp + 3, cells.index("Mean"), cells.index("Median"))
    assert cs.consensus_view(b) == before_view and cs.consensus_stats(b) == before_stats


def test_ra_d14_a_swap_in_recent_changes_reads_the_same_log() -> None:
    b = _real("SMPL")
    before = cs.revision_events(b)
    assert before.status is SourceStatus.PRESENT
    rows = b.sheet("estimates", "Recent Changes")
    hi = cs._find_row(rows, "Change Type")
    assert hi is not None
    cells = [str(c).strip() for c in rows[hi]]
    _swap(rows, hi, len(rows), cells.index("Broker Value Prior"),
          cells.index("Broker Value Current"))
    _swap(rows, hi, len(rows), cells.index("Date"), cells.index("Analyst"))
    assert cs.revision_events(b) == before
    assert cs.estimates_as_of(b) == cs.estimates_as_of(_real("SMPL"))


def _recent_changes(header: list[str]) -> list[list[Any]]:
    return [[], ["Recent Changes"], header,
            ["Estimate Revision", "2026-09-30", "Broker A", "Jane", "Revenue", "FY 2027", "101.0",
             "99.0", "100.5", "100.0"]]


_RC = ["Change Type", "Date", "Broker", "Analyst", "Data Point", "Period", "Broker Value Current",
       "Broker Value Prior", "Consensus After", "Consensus Before"]


def _with_estimates_sheet(name: str, rows: list[list[Any]]) -> CiqBundle:
    b = CiqBundle.from_files(gen.TICKER, [gen.HERE / gen.ESTIMATES_XLS])
    b.sheet("estimates", "Guidance")
    wb = b.workbook("estimates")
    assert wb is not None
    b._cache[wb.path][name] = rows
    return b


def test_ra_d14_twin_each_column_is_found_by_its_header_and_a_missing_one_is_said() -> None:
    """(+) Columns reordered (the 'Change Type' label stays first: it is the row the header is found
    by): the event reads the same. (−) A header gone: UNKNOWN naming it, the log never read by
    position."""
    (ev,) = cs.revision_events(_with_estimates_sheet("Recent Changes", _recent_changes(_RC))).value
    order = [0, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    shuffled = _recent_changes([_RC[k] for k in order])
    shuffled[3] = [shuffled[3][k] for k in order]
    (again,) = cs.revision_events(_with_estimates_sheet("Recent Changes", shuffled)).value
    assert again == ev and (ev.broker_current, ev.broker_prior) == ("101.0", "99.0")
    renamed = [h if h != "Broker Value Prior" else "Prior" for h in _RC]
    gone = cs.revision_events(_with_estimates_sheet("Recent Changes", _recent_changes(renamed)))
    assert gone.status is SourceStatus.UNKNOWN and "'Broker Value Prior'" in (gone.note or "")


# --- review of order 4 (2026-11-10): the gaps the first cut left -------------------------------


@pytest.mark.parametrize("make", [lambda: _real("SMPL"), _zzfx], ids=["SMPL", "twin"])
def test_ra_d9_capital_structure_details_in_thousands_is_refused(make: Any) -> None:
    """(+) Capital Structure Details states its unit as 'Principal Due in Millions of …', which
    `ciq.stated_unit`'s 'In … of' line never matches, so a Thousands export of it passed. Restated
    as Thousands it is now refused, the sheet named. (−) As exported: nothing is refused."""
    b = make()
    cs.require_millions(b, b.ticker)
    rows = b.sheet("financials", "Capital Structure Details", freq="annual")
    for row in rows[:14]:
        for j, cell in enumerate(row):
            if isinstance(cell, str) and cell.strip().startswith("Principal Due in Millions of"):
                row[j] = cell.replace("in Millions of", "in Thousands of", 1)
                break
        else:
            continue
        break
    else:
        raise AssertionError("the sheet states no 'Principal Due in Millions of' line")
    with pytest.raises(cs.CiqUnitError,
                       match=r"Financials \(annual\)→Capital Structure Details: Thousands"):
        cs.require_millions(b, b.ticker)


def test_ra_d9_the_backfill_path_does_not_swallow_the_unit_refusal(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """`_machine_anchor` (anchor-backfill / anchor-retag) re-raised the currency refusal but caught
    `CiqUnitError` as 'no CIQ bridge' and anchored the name EDGAR-only. It fails loud now, as
    assembly does."""
    import json
    import pathlib
    from types import SimpleNamespace

    from vinci import cli

    def _refuse(_b: Any, t: str) -> None:
        raise cs.CiqUnitError(f"{t}: Financials (annual)→Income Statement: Thousands")

    monkeypatch.setattr(cs, "require_millions", _refuse)
    root = pathlib.Path(__file__).resolve().parents[1]
    cut = json.loads((root / "tests" / "fixtures" / "anchor_ciq_bridge.json").read_text())["names"]
    page = cut["GOOGL"]["page"]
    d = SimpleNamespace(mechanical=SimpleNamespace(model_dump=lambda mode, m=page["mechanical"]: m))
    resolver = SimpleNamespace(resolve_ticker=lambda _t: SimpleNamespace(cik="0"))
    edgar = SimpleNamespace(companyfacts=lambda _cik: cut["GOOGL"]["companyfacts"])
    with pytest.raises(cs.CiqUnitError):
        cli._machine_anchor("GOOGL", d, json.dumps(page), SimpleNamespace(data_dir=tmp_path),
                            resolver, edgar)


def test_ra_d14_estimates_as_of_names_a_missing_date_header() -> None:
    """(+) Recent Changes with its 'Date' header renamed: UNKNOWN, and the note names the column
    rather than saying the log holds no dated events. (−) As built: the floor reads."""
    floor = cs.estimates_as_of(_with_estimates_sheet("Recent Changes", _recent_changes(_RC)))
    assert floor.status is SourceStatus.PRESENT and "Recent Changes" in (floor.source_ref or "")
    renamed = [h if h != "Date" else "When" for h in _RC]
    got = cs.estimates_as_of(_with_estimates_sheet("Recent Changes", _recent_changes(renamed)))
    assert got.status is SourceStatus.UNKNOWN and "'Date'" in (got.note or "")
