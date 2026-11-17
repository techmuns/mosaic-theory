"""A page's `analysis_as_of` counts the CIQ Financials sheets' own `Filing Date` row (2026-11-17,
STATE row 64(a), the half #1087 left open).

THE GAP. A CIQ fact is knowable from its export date or from its column's stated filing date, never
from the period the column describes (CLAUDE.md, PUBLISHED DATA). CIQ stamps no Financials export
date, and each period column of its Balance Sheet, Income Statement and Cash Flow sheets states a
`Filing Date` instead — the column behind `ev_bridge.balance_sheet_date` among them. No reader read
it and no page carried it, so a page whose price and exports all predated its latest balance-sheet
column's filing would read early.

THE FIX. `ciq_sheets.financials_filed_through` reads the latest date those columns state, off the
decoded cell, with its workbook sha256, sheet, row and column, or UNKNOWN naming why. The build
records it per Financials export (`inputs.ciq[].filed_through`), `date_semantics` counts it where it
is later than every other date, and `refresh.filed_through_transform` writes it onto a page built
before the field, from the export the page records by sha256.

Value pins read the cut-down sheets in `fixtures/ciq_financials_filed_through.json` (IT's and
UBER's quarterly Financials exports, the ones their pages record by sha256) through the production
reader, and IT's page as committed at main `c58d5b2f`, frozen byte-identical and checked by its git
blob. The corpus pins read the living pages and assert only what holds however they move.
"""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_analysis_as_of_knowable import _frozen
from tests.test_analysis_as_of_skips_and_filings import _fleet, _no_local_path
from vinci import provenance
from vinci.dossier import ciq_sheets, inputs, refresh
from vinci.dossier import valuation_basis as vb
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.inputs_schema import FiledThrough
from vinci.dossier.schemas import Dossier, Sourced, dossier_json

ROOT = Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
FIXTURE: dict[str, Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_financials_filed_through.json").read_text())["names"]
BS, IS, CF = (f"financials|{s}" for s in ciq_sheets.FILED_SHEETS)
#: the day the fixture's exports were read (cut 2026-11-17): no filing it states is later
READ_ON = date(2026, 11, 17)


def _serial(d: date) -> float:
    """A date as the Excel 1900-system serial a CIQ date cell decodes to."""
    return float((d - date(1899, 12, 30)).days)


def _sheets(t: str) -> dict[str, list[list[Any]]]:
    return copy.deepcopy(FIXTURE[t]["sheets"])


def _bundle(t: str, sheets: dict[str, list[list[Any]]] | None = None) -> tuple[CiqBundle, Path]:
    """The page's quarterly Financials export, cut to the rows the reader reads, as real types."""
    path = Path(f"/fixture/{FIXTURE[t]['workbook']}")
    held = sheets if sheets is not None else _sheets(t)
    return CiqBundle(ticker=t, workbooks=(CiqWorkbook(kind="financials", path=path,
                                                      fmt=CiqFormat.BIFF_XLS, freq="quarterly"),),
                     _cache={path: {k.split("|", 1)[1]: v for k, v in held.items()}}), path


def _read(t: str, sheets: dict[str, list[list[Any]]] | None = None) -> FiledThrough:
    bundle, _path = _bundle(t, sheets)
    return ciq_sheets.financials_filed_through(bundle, "quarterly", sha256=FIXTURE[t]["sha256"],
                                               read_on=READ_ON)


def _filing_row(sheets: dict[str, list[list[Any]]], key: str) -> list[Any]:
    (row,) = [r for r in sheets[key] if r and r[0] == "Filing Date"]
    return row


# --- the reader: what the export's columns state ------------------------------------------------

def test_it_states_the_filing_date_of_its_latest_column_with_its_cell() -> None:
    """IT's quarterly export: every column's filing date read, the latest 2026-11-03 (its Q3 2026
    10-Q), named by the Balance Sheet cell behind `ev_bridge.balance_sheet_date` (Sep-30-2026)."""
    ft = _read("IT")
    assert ft.status == "present" and ft.value == date(2026, 11, 3)
    assert ft.source_ref == (
        "CIQ Financials (quarterly)→Balance Sheet, 'Filing Date' row 85, column 40 "
        f"[Q3 Sep-30-2026], workbook sha256 {FIXTURE['IT']['sha256']}")
    assert ft.note is None
    assert ft.model_dump(mode="json") == FIXTURE["IT"]["filed_through"]   # the full read, frozen


def test_an_older_column_stating_no_filing_is_passed_over_and_counted() -> None:
    """UBER's Balance Sheet reads CIQ's 'NA' in its three oldest columns: they state no filing and
    are passed over, never read as a date, and the note counts them — the export's latest column
    still dates it."""
    ft = _read("UBER")
    assert ft.status == "present" and ft.value == date(2026, 11, 4)
    assert "'Filing Date' row 95, column 36 [Q3 Sep-30-2026]" in str(ft.source_ref)
    assert ft.note == ("passed over, never read as a filing date: Balance Sheet: 3 columns, "
                       "[Q1 Mar-31-2018] to [Q3 Sep-30-2018] read 'NA', stating no filing date")


def test_an_older_column_filed_later_than_the_newest_is_read() -> None:
    """EVERY COLUMN COUNTS. A comparative column carries the filing it was last taken from; one
    filed after the newest column (a restating amendment) dates the export, and is named."""
    sheets = _sheets("IT")
    row = _filing_row(sheets, IS)
    hdr = [r for r in sheets[IS] if r][0]
    assert hdr[38] == "3 months\nQ2\nJun-30-2026" and len(hdr) == 40   # older than the latest
    row[38] = _serial(date(2026, 11, 16))
    ft = _read("IT", sheets)
    assert ft.value == date(2026, 11, 16)
    assert ("→Income Statement, 'Filing Date' row 97, column 39 [3 months Q2 Jun-30-2026]"
            in str(ft.source_ref))


def test_the_balance_sheets_latest_column_is_named_where_several_cells_state_the_date() -> None:
    """THE NEGATIVE of the pin above: the latest date stated on all three sheets, and on an older
    comparative column too (IT's Q3 2025, dated by the same 10-Q), names the Balance Sheet's
    latest column, never another."""
    ft = _read("IT")
    hdr = [r for r in FIXTURE["IT"]["sheets"][BS] if r][0]
    filed = _filing_row(_sheets("IT"), BS)
    same = [hdr[j] for j in range(1, len(filed)) if filed[j] == _serial(date(2026, 11, 3))]
    assert len(same) >= 2, same       # an older column states the same date: the tie is real
    assert "column 40 [Q3 Sep-30-2026]" in str(ft.source_ref)


# --- a missing date is UNKNOWN and named, never imputed -----------------------------------------

def test_a_sheet_with_no_filing_date_row_is_unknown_and_named() -> None:
    sheets = _sheets("IT")
    _filing_row(sheets, CF)[0] = ""
    ft = _read("IT", sheets)
    assert ft.status == "unknown" and ft.value is None
    assert ft.note == ("CIQ Financials (quarterly)→Cash Flow carries no 'Filing Date' row, so the "
                       "day its columns were filed is unread")


def test_a_marker_in_the_latest_column_is_unknown_never_an_older_columns_date() -> None:
    """The latest column is behind the page's latest figures: 'NA' there is UNKNOWN, and the
    column before it (filed 2026-08-04) is never read in its place."""
    sheets = _sheets("IT")
    _filing_row(sheets, BS)[39] = "NA"
    ft = _read("IT", sheets)
    assert ft.status == "unknown" and ft.value is None
    assert "reads 'NA' at the latest column [Q3 Sep-30-2026]" in str(ft.note)
    assert "'Filing Date' row 85, column 40" in str(ft.source_ref)


def test_a_cell_that_is_no_date_is_unknown() -> None:
    sheets = _sheets("UBER")
    _filing_row(sheets, IS)[5] = "see note 4"
    ft = _read("UBER", sheets)
    assert ft.status == "unknown" and ft.value is None
    assert "reads 'see note 4' at [" in str(ft.note) and "which is no date" in str(ft.note)


def test_a_date_before_its_own_period_end_is_unknown() -> None:
    """A CHECK ON THE VALUE, beside the checks that a date is there: a serial that decodes but
    precedes the period its column closes files no such column."""
    sheets = _sheets("IT")
    _filing_row(sheets, BS)[39] = _serial(date(2026, 9, 1))
    ft = _read("IT", sheets)
    assert ft.status == "unknown" and ft.value is None
    assert "reads 2026-09-01 at [Q3 Sep-30-2026], before the period the column closes" in str(
        ft.note)


def test_a_date_after_the_day_it_is_read_is_unknown() -> None:
    """(review, round 0) THE OTHER BOUND ON THE VALUE. A serial that decodes to a day after the
    export is read (a corrupt 2099) is no filing yet made: it was PRESENT, later than every other
    date, and set the page's date to 2099. A filing ON the read day is still read."""
    sheets = _sheets("IT")
    _filing_row(sheets, BS)[39] = _serial(date(2099, 1, 1))
    ft = _read("IT", sheets)
    assert ft.status == "unknown" and ft.value is None
    assert "reads 2099-01-01 at [Q3 Sep-30-2026], after 2026-11-17, the day it is read" in str(
        ft.note)
    _filing_row(sheets, BS)[39] = _serial(READ_ON)
    assert _read("IT", sheets).value == READ_ON


def test_a_sheet_the_export_does_not_hold_is_named_and_none_held_is_unknown() -> None:
    sheets = _sheets("IT")
    del sheets[CF]
    ft = _read("IT", sheets)
    assert ft.value == date(2026, 11, 3)
    assert ft.note == "passed over, never read as a filing date: no Cash Flow sheet"
    none = _read("IT", {})
    assert none.status == "unknown" and none.value is None
    assert "holds none of the Balance Sheet, Income Statement, Cash Flow sheets" in str(none.note)


def test_an_export_of_unread_period_type_beside_another_is_unknown_never_a_raise() -> None:
    """(review, round 0) A Financials export whose period type is unread, beside a quarterly one:
    the reader's request names no period type, and the bundle refuses it as ambiguous. That
    refusal stopped the whole build, though every other reader names its period type and reads
    on; it is UNKNOWN, named, and the quarterly export still dates itself."""
    sheets = {k.split("|", 1)[1]: v for k, v in _sheets("IT").items()}
    q, u = Path("/fixture/IT Financials_Quarterly.xls"), Path("/fixture/IT Financials.xls")
    bundle = CiqBundle(ticker="IT", workbooks=(
        CiqWorkbook(kind="financials", path=q, fmt=CiqFormat.BIFF_XLS, freq="quarterly"),
        CiqWorkbook(kind="financials", path=u, fmt=CiqFormat.BIFF_XLS, freq=None)),
        _cache={q: sheets, u: sheets})
    unread = ciq_sheets.financials_filed_through(bundle, None, sha256="c" * 64, read_on=READ_ON)
    assert unread.status == "unknown" and unread.value is None
    assert "period type is unread" in str(unread.note)
    dated = ciq_sheets.financials_filed_through(bundle, "quarterly", sha256="c" * 64,
                                                read_on=READ_ON)
    assert dated.status == "present" and dated.value == date(2026, 11, 3)


def test_the_field_has_sourceds_shape_and_contract() -> None:
    """`inputs_schema` cannot import `Sourced` (the schema imports it), so `FiledThrough` restates
    its shape: the same keys, and every value it holds a valid `Sourced[date]`."""
    assert set(FiledThrough.model_fields) == set(Sourced.model_fields)
    for ft in (_read("IT"), _read("IT", {})):
        assert Sourced[date].model_validate(ft.model_dump()).model_dump() == ft.model_dump()
    with pytest.raises(ValueError, match="both a value and a source_ref"):
        FiledThrough(status="present", value=date(2026, 11, 3))
    with pytest.raises(ValueError, match="carries no value"):
        FiledThrough(status="unknown", value=date(2026, 11, 3), note="x")
    with pytest.raises(ValueError, match="a note saying why"):
        FiledThrough(status="unknown")


# --- the record: the build writes it, the page carries it ---------------------------------------

def test_the_build_records_the_filing_date_in_its_input_record() -> None:
    ft = _read("IT")
    fin = provenance.FileRead("ciq", "/x/fin.xls", "a" * 64, 1, "financials", "quarterly",
                              filed_through=ft)
    comps = provenance.FileRead("ciq", "/x/comps.xls", "b" * 64, 1, "comps", None)
    ciq, missing = inputs._ciq([fin, comps])
    assert missing == []
    assert {e.kind: e.filed_through for e in ciq} == {"financials": ft, "comps": None}


def _quarterly(page: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """IT's quarterly Financials row in its input record, the export the fixture is cut from."""
    (hit,) = [(i, r) for i, r in enumerate(page["inputs"]["ciq"])
              if r["kind"] == "financials" and r["freq"] == "quarterly"]
    assert hit[1]["sha256"] == FIXTURE["IT"]["sha256"]
    return hit


def _with_filed(page: dict[str, Any], ft: FiledThrough) -> dict[str, Any]:
    _i, row = _quarterly(page)
    row["filed_through"] = ft.model_dump(mode="json")
    return page


def test_the_page_writes_the_field_only_where_it_is_read() -> None:
    """ABSENT, never null: a row with none writes no key, so a page built before the field
    round-trips byte-identically; a read one writes it on its own row alone, and round-trips."""
    text = json.dumps(_frozen("IT"))
    plain = json.loads(dossier_json(Dossier.model_validate_json(text)))
    assert not any("filed_through" in r for r in plain["inputs"]["ciq"])
    written = dossier_json(Dossier.model_validate(_with_filed(_frozen("IT"), _read("IT"))))
    rows = json.loads(written)["inputs"]["ciq"]
    assert [(r["kind"], r["freq"]) for r in rows if "filed_through" in r] == [
        ("financials", "quarterly")]
    assert dossier_json(Dossier.model_validate_json(written)) == written


# --- the rule: counted where later than every other date ----------------------------------------

def test_a_later_financials_filing_date_moves_analysis_as_of_and_is_named() -> None:
    """THE POSITIVE. IT as committed at c58d5b2f reads 2026-11-11, the latest of its data dates.
    Its Balance Sheet's latest column moved to a filing of 2026-11-12, read through the production
    reader: the page is knowable from the 12th, and its rule names the record row that dates it.
    No committed page has a later one (the probe in the record), so the value is moved on a real
    page, not found on one."""
    committed = _frozen("IT")["date_semantics"]
    assert committed["analysis_as_of"] == "2026-11-11"
    sheets = _sheets("IT")
    _filing_row(sheets, BS)[39] = _serial(date(2026, 11, 12))
    page = _with_filed(_frozen("IT"), _read("IT", sheets))
    i, _row = _quarterly(page)
    ds = vb.date_semantics(page)
    assert ds.analysis_as_of == "2026-11-12"
    assert ds.analysis_as_of_rule == vb.RULE_DATA_DATES + vb.RULE_FILED_CLAUSE.format(
        where=f"inputs.ciq[{i}].filed_through")
    for k in ("price_as_of", "market_cap_as_of", "tev_as_of", "consensus_as_of",
              "balance_sheet_date", "historical_multiple_latest_observation"):
        assert getattr(ds, k) == committed[k], k       # only the knowable date moves


def test_an_earlier_financials_filing_date_leaves_the_block_word_for_word() -> None:
    """THE NEGATIVE. IT's real filing date (2026-11-03), and one ON the page's date (2026-11-11),
    are not later than the page's latest date: the block is the committed one, word for word."""
    committed = _frozen("IT")["date_semantics"]
    sheets = _sheets("IT")
    _filing_row(sheets, BS)[39] = _serial(date(2026, 11, 11))
    for ft in (_read("IT"), _read("IT", sheets)):
        ds = vb.date_semantics(_with_filed(_frozen("IT"), ft))
        assert json.loads(ds.model_dump_json(exclude={"ciq_exported_as_of"})) == committed


def test_a_missing_financials_filing_date_is_named_never_imputed() -> None:
    """THE MISSING CASE. An export whose filing date reads UNKNOWN dates nothing: the page keeps its
    date, and its rule says that date may be early and names the record row — no date is taken
    from the period the column describes, or from any other column."""
    sheets = _sheets("IT")
    _filing_row(sheets, IS)[0] = ""
    page = _with_filed(_frozen("IT"), _read("IT", sheets))
    i, _row = _quarterly(page)
    ds = vb.date_semantics(page)
    assert ds.analysis_as_of == _frozen("IT")["date_semantics"]["analysis_as_of"] == "2026-11-11"
    assert ds.analysis_as_of_rule == vb.RULE_DATA_DATES + vb.RULE_UNFILED_CLAUSE.format(
        where=f"inputs.ciq[{i}].filed_through")


# --- the backfill: from the export the page records, by sha256 -----------------------------------

def _unfiled(t: str) -> dict[str, Any]:
    """The living page with every Financials row's `filed_through` taken off: the page as a build
    wrote it before this field, which the pass exists to fill."""
    page: dict[str, Any] = json.loads((DOSS / t / "dossier.json").read_text())
    for r in page["inputs"]["ciq"]:
        r.pop("filed_through", None)
    return page


def test_the_seam_admits_only_a_filled_filing_date() -> None:
    page = _frozen("IT")
    filed = _with_filed(_frozen("IT"), _read("IT"))["inputs"]
    assert refresh._only_stated_dates(page["inputs"], filed)
    moved = copy.deepcopy(filed)
    _quarterly({"inputs": moved})[1]["filed_through"]["value"] = "2026-11-20"
    dropped = copy.deepcopy(filed)
    del _quarterly({"inputs": dropped})[1]["filed_through"]
    swapped = copy.deepcopy(filed)
    _quarterly({"inputs": swapped})[1]["sha256"] = "0" * 64
    assert not refresh._only_stated_dates(filed, moved)       # never moves one recorded
    assert not refresh._only_stated_dates(filed, dropped)     # never removes one
    assert not refresh._only_stated_dates(page["inputs"], swapped)


def test_the_seam_refuses_a_filing_date_on_a_row_that_is_no_financials_export() -> None:
    """(review, round 0) `date_semantics` counts a `filed_through` on whatever row carries it, so
    the seam admits one only on a Financials export's row."""
    page = _frozen("IT")
    comps = copy.deepcopy(page["inputs"])
    (row,) = [r for r in comps["ciq"] if r["kind"] == "comps"]
    row["filed_through"] = _read("IT").model_dump(mode="json")
    assert not refresh._only_stated_dates(page["inputs"], comps)
    assert refresh._only_stated_dates(page["inputs"],
                                      _with_filed(_frozen("IT"), _read("IT"))["inputs"])

def test_a_record_naming_no_financials_export_or_already_filed_is_left_alone(
        tmp_path: Path) -> None:
    step = refresh.filed_through_transform("IT", [tmp_path])
    comps_only = {"inputs": {"ciq": [r for r in _frozen("IT")["inputs"]["ciq"]
                                     if r["kind"] != "financials"]}}
    assert step(comps_only) == {} and step.looked_for == []
    filed = _with_filed(_frozen("IT"), _read("IT"))
    for r in filed["inputs"]["ciq"]:
        if r["kind"] == "financials":
            r["filed_through"] = _read("IT").model_dump(mode="json")
    assert step(filed) == {} and step.looked_for == []
    assert step({"inputs": ["not", "a", "record"]}) == {}


def test_the_step_fills_a_row_off_the_export_its_sha256_names(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The reader runs on the file that hashes to the record's sha256, under the record's file
    name, and is handed that sha256; only that row is filled, and nothing else in the record."""
    page = _frozen("IT")
    i, row = _quarterly(page)
    folder = tmp_path / "IT"
    folder.mkdir()
    (folder / row["file"]).write_bytes(b"one Financials export's bytes")
    row["sha256"], row["bytes"] = provenance.file_sha256(folder / row["file"])
    handed: list[str] = []
    want = _read("IT")                  # read before the reader is replaced below

    def _reader(bundle: CiqBundle, freq: str | None, *, sha256: str,
                read_on: date) -> FiledThrough:
        handed.append(sha256)
        assert read_on == date.today()            # the door reads on the day it is run
        assert freq == "quarterly" and bundle.workbook("financials", freq=freq) is not None
        return want

    monkeypatch.setattr(ciq_sheets, "financials_filed_through", _reader)
    step = refresh.filed_through_transform("IT", [tmp_path])
    out = step(page)
    assert handed == [row["sha256"]]
    assert refresh._only_stated_dates(page["inputs"], out["inputs"])
    assert out["inputs"]["ciq"][i]["filed_through"] == FIXTURE["IT"]["filed_through"]
    assert [j for j, r in enumerate(out["inputs"]["ciq"]) if "filed_through" in r] == [i]
    # the annual export is in no folder under the root: named by its sha256, with no local path
    (annual,) = [r for r in page["inputs"]["ciq"]
                 if r["kind"] == "financials" and r["freq"] == "annual"]
    assert step.skipped == [f"IT: skipped: export {annual['sha256']} not found in any IT "
                            "folder under the roots"]


def test_a_file_the_loader_does_not_read_as_that_export_is_named(tmp_path: Path) -> None:
    """The bytes the record names, held under a name the loader kinds as no Financials export,
    were never read: "not read as a quarterly Financials export", never a filing date."""
    page = _frozen("IT")
    _i, row = _quarterly(page)
    folder = tmp_path / "IT"
    folder.mkdir()
    (folder / "Gartner export.xls").write_bytes(b"one Financials export's bytes")
    row["sha256"], row["bytes"] = provenance.file_sha256(folder / "Gartner export.xls")
    step = refresh.filed_through_transform("IT", [tmp_path])
    step(page)
    assert (f"IT: skipped: export {row['sha256']} (Gartner export.xls) not read as a quarterly "
            "Financials export") in step.skipped
    # (review, round 0) a row recording no period type is named without one, never as "None"
    row["freq"] = None
    step(page)
    line = next(x for x in step.skipped if "Gartner export.xls" in x)
    assert line.endswith("not read as a Financials export") and "None" not in line, line


def test_an_export_this_machine_cannot_parse_is_a_skip_never_a_written_unknown(
        tmp_path: Path) -> None:
    """(review, round 0) The bytes the record names, under its own Financials name, that no reader
    here can open: the build read these same bytes, so "could not be read" is this machine's state,
    not what the export states. Written, it would stand for good (the seam never rewrites a
    recorded value); it is a skip, named, and the row is left unfilled."""
    page = _frozen("IT")
    _i, row = _quarterly(page)
    folder = tmp_path / "IT"
    folder.mkdir()
    (folder / row["file"]).write_bytes(b"one Financials export's bytes")
    row["sha256"], row["bytes"] = provenance.file_sha256(folder / row["file"])
    step = refresh.filed_through_transform("IT", [tmp_path])
    assert step(page) == {}
    assert (f"IT: skipped: export {row['sha256']} ({row['file']}) could not be read here"
            in step.skipped)

def test_the_pass_names_every_export_it_cannot_read_with_its_boundary(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`refresh_fleet` reports each skip and its count with what was looked for and where, and a
    page with a skip is never "unchanged" (`NamesSkips`, #1087)."""
    monkeypatch.setattr(refresh, "mirror_to_frontend", lambda: None)
    tree = _fleet(tmp_path / "repo", {"IT": _unfiled("IT")})
    empty = tmp_path / "ciq"
    empty.mkdir()
    out = refresh.refresh_fleet(
        tree, top_level_for=lambda t: refresh.filed_through_transform(t, [empty]))
    assert len(out["skipped"]) == 2 and out["unchanged"] == [] and out["moved"] == []
    (count,) = out["skip_count"]
    assert count == ("2 skipped of 2 recorded Financials export(s) with no filed_through, matched "
                     "by full sha256 in every folder named for the page's ticker under 1 root(s) "
                     "— on 1 of 1 pages refreshed")
    _no_local_path(out, tmp_path)


# --- CIQ-bound: the real workbooks (skip without them) ------------------------------------------

def test_the_reader_reads_its_date_off_the_real_workbook() -> None:
    """IT's own quarterly Financials export, found by the sha256 its page records and read by the
    build's door: the reading the cut fixture holds, cell for cell."""
    from tests.ciq_export_support import skip_unless_export
    bundle = skip_unless_export("IT", "financials", FIXTURE["IT"]["sha256"][:10], freq="quarterly",
                                why="the filing date is read off IT's quarterly Financials export")
    wb = bundle.workbook("financials", freq="quarterly")
    assert wb is not None
    got = inputs.filed_through(bundle)[wb.path]
    assert got.model_dump(mode="json") == FIXTURE["IT"]["filed_through"]


def test_the_build_records_the_date_off_the_real_workbook() -> None:
    from tests.ciq_export_support import skip_unless_export
    bundle = skip_unless_export("IT", "financials", FIXTURE["IT"]["sha256"][:10], freq="quarterly",
                                why="the filing date is read off IT's quarterly Financials export")
    with provenance.recording() as rec:
        inputs.load_bundle("IT", [w.path for w in bundle.workbooks])
    by_kind: dict[str, list[FiledThrough | None]] = {}
    for f in rec.reads().files:
        if f.kind:
            by_kind.setdefault(f.kind, []).append(f.filed_through)
    assert all(ft is not None and ft.status == "present" for ft in by_kind.pop("financials"))
    assert {ft for fts in by_kind.values() for ft in fts} == {None}


def test_the_serial_decodes_as_the_day_it_names() -> None:
    """The helper the pins write dates with is the decode the reader runs (`excel_date`)."""
    from vinci.dossier.ciq import excel_date
    for d in (date(2026, 11, 3), date(2026, 11, 12), date(2018, 5, 7)):
        assert excel_date(_serial(d)) == d
