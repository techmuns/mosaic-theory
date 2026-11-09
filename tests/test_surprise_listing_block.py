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
