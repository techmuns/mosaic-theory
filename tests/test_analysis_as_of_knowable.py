"""A page's `analysis_as_of` is the latest date at which EVERY input is knowable (2026-11-15).

THE DEFECT (the Codex P1 on #1070, deferred there). IT's page read `analysis_as_of` 2026-11-11 —
the latest of its inputs' DATA dates — while its comps panel, the source of its market cap and TEV,
was exported on 2026-11-12. A CIQ export holds history as restated up to its export, so a CIQ fact
is knowable from its export date, never from the close it describes (CLAUDE.md, PUBLISHED DATA).
The stamp reached the page only inside the TEV `source_ref`'s text, which no parser may read.

THE FIX. The build records the export date each workbook STATES of itself as a structured field
(`inputs.ciq[].export_date`, read by `inputs.export_dates` — the comps workbook's `As-Of Date:`
header), `date_semantics` counts it, and `refresh.export_date_transform` writes it onto a page
built before the field, from the export the page records by sha256.

Value pins read pages as committed at main `c58d5b2f` (`replay.page_at`: the living pages move on
re-assembly) and the stamp off the cut-down sheets in `fixtures/ciq_comps_export_date.json`
(through the production reader); the CIQ-bound pins read the real workbooks and skip without them.
"""
from __future__ import annotations

import copy
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci import provenance
from vinci.dossier import inputs
from vinci.dossier import valuation_basis as vb
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.refresh import _only_export_dates, export_date_transform, refresh_dossier
from vinci.dossier.schemas import Dossier, dossier_json

ROOT = Path(__file__).resolve().parents[1]
#: main as merged 2026-11-14 (#1078), the corpus measured: 9 of 26 pages state a comps export later
#: than their `analysis_as_of`
FREEZE = "c58d5b2f774a1afcb2edc36fcd10aefecf7aa077"
BLOBS = {"IT": "0e9ffb4a192161f9c8b79eddbafd0d08b57a4189",
         "UBER": "eb2db341a0a08fc83a06e5ae08b081f7c3f8965f",
         "NKE": "bd836c13183a5e97aeb45e1672c090cb60bb7db4"}
FIXTURE: dict[str, Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_comps_export_date.json").read_text())["names"]


def _frozen(t: str) -> dict[str, Any]:
    from vinci.evals import replay as rp
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{FREEZE}^{{commit}}"],
                      capture_output=True).returncode != 0:
        pytest.skip(f"main {FREEZE[:8]} is not in this history")
    return copy.deepcopy(rp.page_at(t, FREEZE, expect_blob=BLOBS[t]))


def _bundle(t: str) -> tuple[CiqBundle, Path]:
    """The page's comps export, cut to the cells the reader reads, through the real types."""
    path = Path(f"/fixture/{FIXTURE[t]['workbook']}")
    rows = FIXTURE[t]["sheets"]["comps|Financial Data"]
    return CiqBundle(ticker=t, workbooks=(CiqWorkbook(kind="comps", path=path,
                                                      fmt=CiqFormat.BIFF_XLS, freq=None),),
                     _cache={path: {"Financial Data": rows}}), path


def _with_stamp(t: str) -> dict[str, Any]:
    """The frozen page, its comps row given the stamp the build's reader reads off its export."""
    page = _frozen(t)
    bundle, path = _bundle(t)
    stamp = inputs.export_dates(bundle)[path]
    (row,) = [r for r in page["inputs"]["ciq"] if r["kind"] == "comps"]
    assert row["sha256"] == FIXTURE[t]["sha256"], t   # the fixture IS the export the page names
    row["export_date"] = stamp.isoformat()
    return page


# --- the reader: what the export states of itself ------------------------------------------------

def test_the_reader_takes_the_comps_header_raw_never_the_corrected_close() -> None:
    """The assembler corrects the comps date to the prior close (`resolved_comps_as_of`, the data
    date the page publishes as `tev_as_of`). The export stamp is the header itself."""
    bundle, path = _bundle("IT")
    assert inputs.export_dates(bundle) == {path: date(2026, 11, 12)}
    bundle.resolved_comps_as_of = date(2026, 11, 11)
    assert inputs.export_dates(bundle) == {path: date(2026, 11, 12)}


def test_a_workbook_that_states_no_export_date_records_none() -> None:
    """Only the comps workbook states one: a Financials export, or a comps sheet with no header,
    records nothing — never a guessed date."""
    bundle, path = _bundle("IT")
    headless = CiqBundle(ticker="IT", workbooks=bundle.workbooks,
                         _cache={path: {"Financial Data": [["Gartner Inc. (NYSE:IT)"]]}})
    assert inputs.export_dates(headless) == {}
    fin = Path("/fixture/IT-financials.xls")
    other = CiqBundle(ticker="IT", workbooks=(CiqWorkbook(kind="financials", path=fin,
                                                          fmt=CiqFormat.BIFF_XLS,
                                                          freq="annual"),),
                      _cache={fin: {"Financial Data": FIXTURE["IT"]["sheets"][
                          "comps|Financial Data"]}})
    assert inputs.export_dates(other) == {}


def test_the_build_records_the_stamp_in_its_input_record() -> None:
    """A FileRead carrying the stamp becomes the CiqExport's structured field; one without, none."""
    stamped = provenance.FileRead("ciq", "/x/comps.xls", "a" * 64, 1, "comps", None,
                                  export_date="2026-11-12")
    plain = provenance.FileRead("ciq", "/x/fin.xls", "b" * 64, 1, "financials", "annual")
    ciq, missing = inputs._ciq([stamped, plain])
    assert missing == []
    assert {e.kind: e.export_date for e in ciq} == {"comps": date(2026, 11, 12),
                                                     "financials": None}


# --- the rule: the latest KNOWABLE date ----------------------------------------------------------

def test_it_is_dated_from_its_comps_export_not_the_close_it_describes() -> None:
    """THE OBSERVED CASE. IT as committed at main c58d5b2f: every data date ≤ 2026-11-11, its comps
    export stated 2026-11-12. Counted, the page is knowable from the 12th."""
    committed = _frozen("IT")["date_semantics"]
    assert committed["analysis_as_of"] == "2026-11-11"          # the defect, as it shipped
    ds = vb.date_semantics(_with_stamp("IT"))
    assert ds.analysis_as_of == "2026-11-12"
    assert ds.ciq_exported_as_of == "2026-11-12"
    assert ds.analysis_as_of_rule == vb.RULE_KNOWABLE
    # every date the page names is the one it named: only the knowable date moves
    for k in ("price_as_of", "market_cap_as_of", "tev_as_of", "consensus_as_of",
              "balance_sheet_date", "historical_multiple_latest_observation"):
        assert getattr(ds, k) == committed[k], k


def test_a_page_whose_export_predates_its_data_keeps_its_date() -> None:
    """THE NEGATIVE. UBER at c58d5b2f: comps exported 2026-11-05, its price 2026-11-06 — the price
    is the later input, so the page's date stays, and the stamp is named beside it."""
    committed = _frozen("UBER")["date_semantics"]
    ds = vb.date_semantics(_with_stamp("UBER"))
    assert committed["analysis_as_of"] == ds.analysis_as_of == "2026-11-06"
    assert ds.ciq_exported_as_of == "2026-11-05"


def test_a_page_whose_record_states_no_export_date_is_unchanged() -> None:
    """NKE's record is a BACKFILL naming no comps export: its block is the one it carries, word for
    word, under the rule that describes it — and it writes no new key."""
    page = _frozen("NKE")
    assert not any(r.get("export_date") for r in page["inputs"]["ciq"])
    ds = vb.date_semantics(page)
    assert json.loads(ds.model_dump_json(exclude={"ciq_exported_as_of"})) == page["date_semantics"]
    assert ds.ciq_exported_as_of is None and ds.analysis_as_of_rule == vb.RULE_DATA_DATES


def test_the_page_writes_the_stamp_only_where_it_is_stated() -> None:
    """ABSENT, never null: an unstamped row and an unstamped page write no key, so a page built
    before the field round-trips byte-identically; a stamped one writes both."""
    text = json.dumps(_frozen("IT"))
    plain = json.loads(dossier_json(Dossier.model_validate_json(text)))
    assert "ciq_exported_as_of" not in plain["date_semantics"]
    assert not any("export_date" in r for r in plain["inputs"]["ciq"])
    written = json.loads(dossier_json(Dossier.model_validate(_with_stamp("IT"))))
    assert written["date_semantics"]["ciq_exported_as_of"] == "2026-11-12"
    assert written["date_semantics"]["analysis_as_of"] == "2026-11-12"
    assert [r["kind"] for r in written["inputs"]["ciq"] if "export_date" in r] == ["comps"]


# --- end to end, on the committed corpus (TEST-LAYER RULE: invariants on living pages) -----------

def test_no_committed_page_is_dated_before_a_ciq_export_it_records() -> None:
    """Every page whose input record a BUILD wrote, naming a comps export, states the date that
    export states of itself; and no page's `analysis_as_of` precedes any export date it records.
    IT's committed page read 2026-11-11 against a comps export of 2026-11-12, recorded nowhere."""
    pages = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
    checked: list[str] = []
    for p in pages:
        doc = json.loads(p.read_text())
        rows = (doc.get("inputs") or {}).get("ciq") or []
        dates = [r["export_date"] for r in rows if r.get("export_date")]
        if (doc.get("inputs") or {}).get("recorded") == "build" and any(
                r.get("kind") == "comps" for r in rows):
            assert dates, (f"{p.parent.name}: its build recorded a comps export but no export "
                           "date — a comps export with no As-Of Date header dates the page from "
                           "its data alone; say so here before accepting it")
            checked.append(p.parent.name)
        if dates:
            assert doc["date_semantics"]["analysis_as_of"] >= max(dates), p.parent.name
            assert doc["date_semantics"]["ciq_exported_as_of"] == max(dates), p.parent.name
    assert "IT" in checked and len(checked) >= 10, (checked, len(pages))   # never vacuous


# --- the backfill: from the export the page records, by sha256 -----------------------------------

def test_a_record_naming_no_comps_export_is_left_alone(tmp_path: Path) -> None:
    assert export_date_transform("NKE", [tmp_path])(_frozen("NKE")) == {}


def test_an_export_no_file_on_this_machine_matches_is_left_alone(tmp_path: Path) -> None:
    """A file of the same name whose bytes are another export's names nothing: the identity is the
    sha256 the page records, never the name."""
    (tmp_path / "IT").mkdir()
    (tmp_path / "IT" / FIXTURE["IT"]["workbook"]).write_bytes(b"another export")
    assert export_date_transform("IT", [tmp_path])(_frozen("IT")) == {}


def test_the_seam_admits_only_the_stamp() -> None:
    page = _frozen("IT")
    stamped = _with_stamp("IT")["inputs"]
    assert _only_export_dates(page["inputs"], stamped)
    swapped = copy.deepcopy(stamped)
    swapped["ciq"][0]["sha256"] = "0" * 64
    assert not _only_export_dates(page["inputs"], swapped)
    assert not _only_export_dates(page["inputs"], stamped | {"recorded": "backfill"})


def test_the_seam_never_rewrites_a_stamp_already_recorded() -> None:
    """NEGATIVE (code review): a stamp in the record is what the build READ — the seam fills an
    absent one, and neither moves nor removes one that is there."""
    stamped = _with_stamp("IT")["inputs"]
    moved = copy.deepcopy(stamped)
    dropped = copy.deepcopy(stamped)
    for rec, stamp in ((moved, "2026-11-20"), (dropped, None)):
        (row,) = [r for r in rec["ciq"] if r["kind"] == "comps"]
        if stamp is None:
            del row["export_date"]
        else:
            row["export_date"] = stamp
    assert _only_export_dates(stamped, stamped)
    assert not _only_export_dates(stamped, moved)
    assert not _only_export_dates(stamped, dropped)


def test_a_record_that_is_no_mapping_is_left_alone(tmp_path: Path) -> None:
    assert export_date_transform("IT", [tmp_path])({"inputs": ["not", "a", "record"]}) == {}


def test_the_transform_reads_the_export_under_the_name_its_record_gives(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The same bytes held twice, once under a name the loader kinds as NO comps export that sorts
    first: the stamp is read off the copy under the record's own name, never dropped for the
    least-named one (code review)."""
    from vinci.dossier import ciq_sheets

    name = FIXTURE["IT"]["workbook"]
    folder = tmp_path / "IT"
    folder.mkdir()
    for n in (name, "Backup copy.xls"):
        (folder / n).write_bytes(b"one export's bytes")
    sha, size = provenance.file_sha256(folder / name)
    monkeypatch.setattr(ciq_sheets, "comps_export_stamp",
                        lambda b: date(2026, 11, 12) if b.workbook("comps") else None)
    page = {"inputs": {"ciq": [{"kind": "comps", "file": name, "sha256": sha, "bytes": size}]}}
    out = export_date_transform("IT", [tmp_path])(page)
    assert [r.get("export_date") for r in out["inputs"]["ciq"]] == ["2026-11-12"]


def test_a_comps_export_that_cannot_be_parsed_is_still_recorded(tmp_path: Path) -> None:
    """The stamp read parses the comps workbook, and a corrupt .xls raises xlrd's own error: the
    build's record still names every file it read before that propagates (code review)."""
    pytest.importorskip("xlrd")
    folder = tmp_path / "IT"
    folder.mkdir()
    comps = folder / FIXTURE["IT"]["workbook"]
    comps.write_bytes(bytes.fromhex("d0cf11e0a1b11ae1") + b"\0" * 600)   # OLE2 magic, no body
    with provenance.recording() as rec, pytest.raises(Exception):  # noqa: B017, PT011
        inputs.load_bundle("IT", [comps])
    assert [(Path(f.path).name, f.kind) for f in rec.reads().files] == [(comps.name, "comps")]


def test_refresh_refuses_an_input_record_change_beyond_the_stamp(tmp_path: Path) -> None:
    """The guard is in the writer, not only in the one transform that uses it."""
    (tmp_path / "IT").mkdir()
    path = tmp_path / "IT" / "dossier.json"
    page = _frozen("IT")
    path.write_text(dossier_json(Dossier.model_validate(page)))

    def _rewrite(doc: dict[str, Any]) -> dict[str, Any]:
        rec = copy.deepcopy(doc["inputs"])
        rec["ciq"] = rec["ciq"][1:]       # drops an export the page was built from
        return {"inputs": rec}

    before = path.read_text()
    with pytest.raises(ValueError, match="only by its CIQ exports' export_date"):
        refresh_dossier(path, top_level=_rewrite)
    assert path.read_text() == before


# --- CIQ-bound: the real workbooks (skip without them) ------------------------------------------

def test_the_transform_reads_its_export_by_sha256_off_the_real_workbook() -> None:
    """IT's own comps export, found by the sha256 its page records and read by the build's reader:
    the stamp the cut fixture holds, and the record otherwise unchanged."""
    from tests.ciq_export_support import skip_unless_export
    bundle = skip_unless_export("IT", "comps", FIXTURE["IT"]["sha256"][:10],
                                why="the export stamp is read off IT's comps export")
    wb = bundle.workbook("comps")
    assert wb is not None
    page = _frozen("IT")
    out = export_date_transform("IT", [wb.path.parent.parent])(page)
    assert _only_export_dates(page["inputs"], out["inputs"])
    assert [r.get("export_date") for r in out["inputs"]["ciq"] if r["kind"] == "comps"] == [
        FIXTURE["IT"]["export_date"]]


def test_the_build_records_the_stamp_off_the_real_workbook() -> None:
    from tests.ciq_export_support import skip_unless_export
    bundle = skip_unless_export("IT", "comps", FIXTURE["IT"]["sha256"][:10],
                                why="the export stamp is read off IT's comps export")
    wb = bundle.workbook("comps")
    assert wb is not None
    with provenance.recording() as rec:
        inputs.load_bundle("IT", [w.path for w in bundle.workbooks])
    stamps = {Path(f.path).name: f.export_date for f in rec.reads().files if f.kind}
    assert stamps.pop(wb.path.name) == FIXTURE["IT"]["export_date"]
    assert set(stamps.values()) == {None}
