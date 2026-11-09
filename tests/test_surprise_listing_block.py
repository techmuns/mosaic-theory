"""THE SURPRISE HISTORY IS THE COMPANY'S OWN LISTING'S (2026-11-09, audit RA-D1).

`ciq_sheets.surprise_history` read the first "EPS (GAAP)" row anywhere on Estimates→Surprise. CIQ
heads each listing's per-share rows with the listing ("NYSE:PARR (USD)"), and Par Pacific's sheet
opens with its predecessor's OTC listing, OTCPK:DPTR.Q. So PARR's committed page stated that
listing's FY2006–FY2010 ("+0%" each) as PARR's own surprise history, and NYSE:PARR's FY2014–FY2025
(FY2023 +52%, FY2025 +18%) never reached it.

Every value pin runs on REAL rows frozen in `tests/fixtures/ciq_surprise_listings.json` (the
operator's exports cut through the real decode path, `scripts/build_surprise_listings_fixture.py`)
and built into the REAL `CiqBundle`. PARR is the case; GOOGL (two blocks of its own listing, then
GOOG's) and NFLX (one listing, the shape of every other export on file) must not move.
"""
from __future__ import annotations

import copy
import json
import pathlib
from typing import Any

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.schemas import Dossier, SourceStatus

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX: dict[str, Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_surprise_listings.json").read_text())


def _rows(name: str) -> list[list[Any]]:
    return copy.deepcopy(FIX["names"][name]["rows"])


def _bundle(name: str, rows: list[list[Any]] | None = None) -> CiqBundle:
    """The frozen Surprise rows as a REAL bundle, served from its cache."""
    path = pathlib.Path("/frozen") / FIX["_about"]["exports"][name]["file"]
    wb = CiqWorkbook(kind="estimates", path=path, fmt=CiqFormat.BIFF_XLS, freq=None)
    return CiqBundle(ticker=name, workbooks=(wb,),
                     _cache={path: {"Surprise": rows if rows is not None else _rows(name)}})


def test_parrs_surprise_history_is_read_from_its_own_listings_block() -> None:
    """(+) THE CASE. The GAAP-EPS series is NYSE:PARR's, FY2014–FY2025, and none of the OTC
    predecessor's FY2006–FY2010 survives. The stamp names the block read and the one passed over."""
    got = cs.surprise_history(_bundle("PARR"))
    assert got.status is SourceStatus.PRESENT and got.value is not None
    eps = got.value.split("; Revenue surprise:")[0]
    assert eps == ("GAAP-EPS surprise: FY2014 +0%, FY2015 +0%, FY2016 +0%, FY2018 -15%, "
                   "FY2020 +0%, FY2021 +0%, FY2022 -7%, FY2023 +52%, FY2024 +0%, FY2025 +18%")
    assert got.source_ref == ("CIQ Estimates→Surprise (annual; GAAP EPS from the NYSE:PARR (USD) "
                              "block — the sheet's first, OTCPK:DPTR.Q (USD), is another "
                              "listing's)")
    assert got.note is None


def test_the_company_level_revenue_series_is_unchanged() -> None:
    """The Revenue row sits under "Company Level", which is no listing: its series is read as it
    always was (the predecessor years are the company's own revenue history)."""
    got = cs.surprise_history(_bundle("PARR"))
    assert got.value is not None
    assert got.value.split("; Revenue surprise: ")[1].startswith(
        "FY2003 -3%, FY2004 -0%, FY2006 -3%, FY2007 -20%")


def test_a_sheet_whose_blocks_name_no_listing_of_the_company_refuses_the_eps_read() -> None:
    """(-) NEGATIVE PIN, SYNTHETIC ON THE REAL TYPE: PARR's real rows with its own block's header
    renamed to another listing. No block is PARR's, so no GAAP-EPS series is stated — never the
    first block's — and the note says which listings the sheet holds. Revenue still reads."""
    rows = _rows("PARR")
    own = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "NYSE:PARR (USD)")
    rows[own][0] = "NYSE:PARX (USD)"
    got = cs.surprise_history(_bundle("PARR", rows))
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert "GAAP-EPS surprise" not in got.value
    assert got.value.startswith("Revenue surprise: ")
    assert got.note is not None and got.note.startswith(
        "the Surprise sheet heads no block with PARR's own listing (its listings: "
        "OTCPK:DPTR.Q (USD), NYSE:PARX (USD)")
    assert got.source_ref == "CIQ Estimates→Surprise (annual)"


@pytest.mark.parametrize(("name", "head"), [
    ("GOOGL", "GAAP-EPS surprise: FY2004 +33%, FY2005 +0%, FY2006 +9%, FY2007 -3%"),
    ("NFLX", "GAAP-EPS surprise: FY2004 +0%, FY2005 +0%, FY2006 +0%, FY2007 +0%"),
])
def test_a_sheet_that_opens_with_the_companys_own_listing_reads_as_before(
        name: str, head: str) -> None:
    """NO MOVE where the first block is the company's own (every export on file but PARR's,
    swept 2026-11-09 over 36 folders): the stamp is unchanged, and so is the value — the committed
    page's, whenever it was built from the export the fixture was cut from. GOOGL's sheet repeats
    its own listing's block and adds GOOG's; the first of its own is read."""
    got = cs.surprise_history(_bundle(name))
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert got.value.startswith(head)
    assert got.source_ref == "CIQ Estimates→Surprise (annual)" and got.note is None
    page = json.loads((ROOT / "data" / "dossiers" / name / "dossier.json").read_text())
    stamped = {c["kind"]: c["sha256"] for c in (page.get("inputs") or {}).get("ciq", [])}
    if stamped.get("estimates") == FIX["_about"]["exports"][name]["sha256"]:
        stored = page["mechanical"]["consensus_context"]["surprise_history"]
        assert (stored["value"], stored["source_ref"]) == (got.value, got.source_ref)


def test_parrs_committed_page_states_its_own_listings_surprise_history() -> None:
    """END TO END (TEST-LAYER RULE): the defect was observed on PARR's rendered page. Its committed
    record, rendered, prints NYSE:PARR's series and none of the predecessor's years — whenever the
    page was built from the export the fixture was cut from (its stamped sha256)."""
    from vinci.dossier.render import render_markdown

    page = json.loads((ROOT / "data" / "dossiers" / "PARR" / "dossier.json").read_text())
    stamped = {c["kind"]: c["sha256"] for c in (page.get("inputs") or {}).get("ciq", [])}
    if stamped.get("estimates") != FIX["_about"]["exports"]["PARR"]["sha256"]:
        pytest.skip("PARR's page was built from another Estimates export than the fixture's")
    want = cs.surprise_history(_bundle("PARR"))
    stored = page["mechanical"]["consensus_context"]["surprise_history"]
    assert stored["value"] == want.value and stored["source_ref"] == want.source_ref
    md = render_markdown(Dossier.model_validate(page))
    line = next(ln for ln in md.splitlines() if ln.startswith("- **Surprise history"))
    assert "GAAP-EPS surprise: FY2014 " in line, line
    for y in range(2006, 2011):
        assert f"GAAP-EPS surprise: FY{y}" not in line, line


# --- review of the branch (2026-11-09): three edges of the block read ----------------------------


def test_a_share_class_spelled_with_a_dash_still_finds_its_own_block() -> None:
    """(+) 'BRK.B' and 'BRK-B' are one share class (the Trends reader's rule, audit A-D10): a
    bundle ticker spelled with a dash still reads the block CIQ heads with the dotted symbol."""
    rows = _rows("PARR")
    own = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "NYSE:PARR (USD)")
    rows[own][0] = "NYSE:PA.RR (USD)"
    path = pathlib.Path("/frozen") / FIX["_about"]["exports"]["PARR"]["file"]
    wb = CiqWorkbook(kind="estimates", path=path, fmt=CiqFormat.BIFF_XLS, freq=None)
    got = cs.surprise_history(CiqBundle(ticker="PA-RR", workbooks=(wb,),
                                        _cache={path: {"Surprise": rows}}))
    assert got.value is not None and got.value.startswith("GAAP-EPS surprise: FY2014 +0%")
    assert got.note is None


def test_an_own_block_with_no_eps_row_says_so_and_never_cites_the_block() -> None:
    """(-) PARR's own block with its "EPS (GAAP)" row blanked: no GAAP-EPS series is stated, the
    note says why, and the stamp never claims an EPS read from the NYSE:PARR block."""
    rows = _rows("PARR")
    own = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == "NYSE:PARR (USD)")
    eps = next(i for i in range(own + 1, len(rows))
               if rows[i] and str(rows[i][0]).startswith("EPS (GAAP)"))
    rows[eps] = []
    got = cs.surprise_history(_bundle("PARR", rows))
    assert got.value is not None and got.value.startswith("Revenue surprise: ")
    assert got.source_ref == "CIQ Estimates→Surprise (annual)"
    assert got.note == ("the NYSE:PARR (USD) block carries no 'EPS (GAAP)' row, so no GAAP-EPS "
                        "surprise is read")


def test_a_revenue_row_only_under_calendar_years_is_never_printed_as_fiscal() -> None:
    """(-) The fiscal table's Revenue row blanked: the only Revenue row left is the Calendar Years
    table's, one column off the fiscal header. It is not read — before, it printed every year
    shifted (calendar 2003's -2% as "FY2000 -2%")."""
    rows = _rows("PARR")
    cal = next(i for i, r in enumerate(rows) if r and "Calendar Years" in [str(c) for c in r[:3]])
    fiscal_rev = next(i for i in range(cal) if rows[i] and str(rows[i][0]).strip() == "Revenue")
    rows[fiscal_rev] = []
    got = cs.surprise_history(_bundle("PARR", rows))
    assert got.value is not None and "Revenue surprise" not in got.value
    assert "FY2000" not in got.value


# --- the $0 writer's surprise guards (`vinci ciq-reread --field surprise_history`) ---------------


def _reread_page(tmp: pathlib.Path, monkeypatch: pytest.MonkeyPatch, *, stamp: str | None,
                 cite: bool = False) -> tuple[pathlib.Path, str]:
    """PARR's committed page in ``tmp`` with its surprise history set back to the predecessor
    block's read, served the frozen rows from a file on disk whose sha256 the page stamps (or
    ``stamp``)."""
    import hashlib

    from vinci.dossier import ciq_reread
    from vinci.dossier.schemas import dossier_json

    export = tmp / "ciq" / "PARR" / FIX["_about"]["exports"]["PARR"]["file"]
    export.parent.mkdir(parents=True)
    export.write_bytes(b"frozen surprise rows")
    wb = CiqWorkbook(kind="estimates", path=export, fmt=CiqFormat.BIFF_XLS, freq=None)
    bundle = CiqBundle(ticker="PARR", workbooks=(wb,), _cache={export: {"Surprise": _rows("PARR")}})
    monkeypatch.setattr(ciq_reread, "_bundle", lambda _t, _root: bundle)
    page = json.loads((ROOT / "data" / "dossiers" / "PARR" / "dossier.json").read_text())
    page["mechanical"]["consensus_context"]["surprise_history"] = {
        "value": "GAAP-EPS surprise: FY2006 +0%", "source_ref": "CIQ Estimates→Surprise (annual)",
        "status": "present", "note": None}
    sha = hashlib.sha256(export.read_bytes()).hexdigest()
    for c in page["inputs"]["ciq"]:
        if c["kind"] == "estimates":
            c["sha256"] = sha if stamp is None else stamp
    if cite:
        page["synthesis"]["bull_points"][0]["source_ref"] = "CIQ Estimates→Surprise (annual)"
    jp = tmp / "dossiers" / "PARR" / "dossier.json"
    jp.parent.mkdir(parents=True)
    jp.write_text(dossier_json(Dossier.model_validate(page)))
    return jp, jp.read_text()


def test_the_writer_rereads_the_surprise_history_from_the_stamped_export(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) The export on disk hashes to the page's stamp and no claim cites the field: the field is
    re-read, recorded as `ciq-reread`, and a second run is a no-op."""
    from vinci.dossier import ciq_reread

    jp, _raw = _reread_page(tmp_path, monkeypatch, stamp=None)
    o = ciq_reread.reread(jp, "surprise_history", tmp_path / "ciq")
    assert o.status == "written", o
    doc = json.loads(jp.read_text())
    assert doc["mechanical"]["consensus_context"]["surprise_history"]["value"].startswith(
        "GAAP-EPS surprise: FY2014 +0%")
    assert doc["layer_refreshes"][-1]["writer"] == "ciq-reread"
    again = ciq_reread.reread(jp, "surprise_history", tmp_path / "ciq")
    assert again.status == "unchanged", again


@pytest.mark.parametrize(("stamp", "cite", "why"), [
    ("0" * 64, False, "is not the one the page stamps"),
    (None, True, "a synthesis claim cites the surprise history"),
])
def test_the_writer_refuses_an_unproven_export_or_a_cited_field(
        tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, stamp: str | None, cite: bool,
        why: str) -> None:
    """(-) NEGATIVE PINS: an export whose sha256 is not the page's stamp, and a page whose synthesis
    cites the field, are refused — and the page is byte-identical."""
    from vinci.dossier import ciq_reread

    jp, raw = _reread_page(tmp_path, monkeypatch, stamp=stamp, cite=cite)
    o = ciq_reread.reread(jp, "surprise_history", tmp_path / "ciq")
    assert o.status == "refused" and why in o.detail, o
    assert jp.read_text() == raw
