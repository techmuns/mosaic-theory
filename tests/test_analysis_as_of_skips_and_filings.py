"""STATE row 64(a)'s two follow-ups from #1082's review (2026-11-16).

(2) THE EXPORT-DATE PASS NAMES WHAT IT SKIPS. `refresh.export_date_transform` passed over a recorded
comps export that no file on this machine matched by sha256, and `refresh_fleet` then reported the
page as plain "unchanged": a page left undated read like a page with nothing to fill. The pass now
names each such export by page and by the sha256 the page records, never as "unchanged", and
states how many it skipped of how many it looked for, and where.

(1) A CIQ COLUMN'S OWN STATED FILING DATE COUNTS. A CIQ fact is knowable from its export date or
from its column's stated filing date, never from the period the column describes (CLAUDE.md,
PUBLISHED DATA). The one such date a page carries as a structured value, the capital-structure
panel's source filing date (`mechanical.capital_structure.maturity_check.panel_filed`), now counts
toward `analysis_as_of` where it is later than every other date, and the rule names it. Where it is
not later, the page's block, and so its bytes, do not move: 0 of the 26 committed pages had a later
one at main `ee9c4635`.

Value pins read IT's page as committed at main `c58d5b2f`, frozen byte-identical in
`fixtures/frozen_pages/` and checked by its git blob. The fleet pins read the living pages, and
assert only what holds however the pages move (TEST-LAYER RULE).
"""
from __future__ import annotations

import copy
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.roster_support import write_roster
from tests.test_analysis_as_of_knowable import FIXTURE, _frozen
from vinci import provenance
from vinci.dossier import refresh
from vinci.dossier import valuation_basis as vb
from vinci.dossier.schemas import Dossier, dossier_json

ROOT = Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
PANEL_FILED = ("mechanical", "capital_structure", "maturity_check", "panel_filed")


def _living(t: str) -> dict[str, Any]:
    page: dict[str, Any] = json.loads((DOSS / t / "dossier.json").read_text())
    return page


def _undated(t: str) -> dict[str, Any]:
    """The living page with its comps export's `export_date` taken off its record: the page as a
    build wrote it before #1082, which the pass exists to date."""
    page = _living(t)
    (row,) = [r for r in page["inputs"]["ciq"] if r["kind"] == "comps"]
    row.pop("export_date", None)
    return page


def _fleet(tmp_path: Path, pages: dict[str, dict[str, Any]]) -> Path:
    """A repository tree holding just these pages, each written through the one serializer, and
    a coverage roster naming them (the fleet is the roster's covered names, W27)."""
    for t, doc in pages.items():
        folder = tmp_path / "data" / "dossiers" / t
        folder.mkdir(parents=True)
        (folder / "dossier.json").write_text(dossier_json(Dossier.model_validate(doc)))
    write_roster(tmp_path / "data", dict.fromkeys(pages, "watch"))
    return tmp_path


def _run(tree: Path, roots: list[Path], monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    # the mirror rebuilds the whole frontend tree; its own pins cover it (test_refresh_fleet_...)
    monkeypatch.setattr(refresh, "mirror_to_frontend", lambda: None)
    return refresh.refresh_fleet(
        tree, top_level_for=lambda t: refresh.export_date_transform(t, roots))


# --- (2) the pass names every export it cannot match --------------------------------------------

def test_an_export_not_on_disk_is_named_never_reported_unchanged(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE DEFECT. IT's record names its comps export by sha256 and no file under the root matches
    it: the page is named with that sha256, and is not "unchanged". NKE's record names no comps
    export (a BACKFILL), so the pass looks for nothing there and NKE is plain "unchanged"."""
    sha = _living("IT")["inputs"]["ciq"][0]["sha256"]
    assert _living("IT")["inputs"]["ciq"][0]["kind"] == "comps"
    tree = _fleet(tmp_path / "repo", {"IT": _undated("IT"), "NKE": _living("NKE")})
    empty = tmp_path / "ciq"
    empty.mkdir()
    out = _run(tree, [empty], monkeypatch)
    assert out["skipped"] == [
        f"IT: skipped: export {sha} not found in any IT folder under the roots"]
    assert "IT" not in out["unchanged"] and "IT" not in out["moved"]
    assert out["unchanged"] == ["NKE"]
    # the count, with its boundary: how many of how many, on how many pages, searched where
    (count,) = out["skip_count"]
    assert count.startswith("1 skipped of 1 recorded comps export(s) with no export_date"), count
    assert "1 of 2 pages" in count and "full sha256" in count, count
    assert "in every folder named for the page's ticker under 1 root(s)" in count, count
    _no_local_path(out, tmp_path)


#: an absolute path in printed output: a `/` opening a word (POSIX), or a drive letter (Windows)
_ABS_PATH = re.compile(r"(?:^|[\s(\[\"'])(?:/|[A-Za-z]:\\)")


def _no_local_path(out: dict[str, list[str]], tmp_path: Path) -> None:
    """No line the pass prints names a local path: a resolved CIQ root can carry the operator's
    account folder name, and these lines are pasted into records and PR bodies in a public repo
    (#1087 review, round 1)."""
    for key, lines in out.items():
        for line in lines:
            assert str(tmp_path) not in line and not _ABS_PATH.search(line), (key, line)


def test_the_skip_names_what_was_searched_never_the_whole_disk(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE SEARCH IS THE TICKER'S FOLDERS, NOT THE ROOT (#1087 review, round 1, F1). The exact bytes
    the record names, held under a root but in no folder named for the ticker, are not found, and
    the line says where it looked. It never says "not on disk": the file is on disk."""
    page = _undated("IT")
    (row,) = [r for r in page["inputs"]["ciq"] if r["kind"] == "comps"]
    root = tmp_path / "ciq"
    (root / "elsewhere" / "Gartner").mkdir(parents=True)
    export = root / "elsewhere" / "Gartner" / row["file"]
    export.write_bytes(b"one comps export's bytes")
    row["sha256"], row["bytes"] = provenance.file_sha256(export)
    out = _run(_fleet(tmp_path / "repo", {"IT": page}), [root], monkeypatch)
    assert out["skipped"] == [
        f"IT: skipped: export {row['sha256']} not found in any IT folder under the roots"]
    assert "not on disk" not in out["skipped"][0]
    _no_local_path(out, tmp_path)


def test_a_file_the_loader_does_not_read_as_comps_is_named_as_that(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TWO CAUSES, TWO LINES (#1087 review, round 1, F2). The record's exact bytes in IT's folder,
    under a name the loader kinds as no comps export: the export was never read, so it is "not
    read as a comps export", never "states no export date", a cause nothing measured. The stamp
    reader is NOT patched here; the file is turned away before it."""
    page = _undated("IT")
    (row,) = [r for r in page["inputs"]["ciq"] if r["kind"] == "comps"]
    root = tmp_path / "ciq"
    (root / "IT").mkdir(parents=True)
    export = root / "IT" / "Gartner export.xls"
    export.write_bytes(b"one comps export's bytes")
    row["file"] = export.name
    row["sha256"], row["bytes"] = provenance.file_sha256(export)
    out = _run(_fleet(tmp_path / "repo", {"IT": page}), [root], monkeypatch)
    assert out["skipped"] == [
        f"IT: skipped: export {row['sha256']} (Gartner export.xls) not read as a comps export"]
    assert out["unchanged"] == [] and out["moved"] == []
    _no_local_path(out, tmp_path)


def test_a_matched_export_is_filled_and_names_no_skip(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE NEGATIVE. The export the record names IS on disk: the page moves, nothing is skipped.
    The record's sha256 is pointed at a file the test writes, and the stamp reader at a fixed date
    (the reader itself is pinned off the real export in test_analysis_as_of_knowable)."""
    from vinci.dossier import ciq_sheets

    page = _undated("IT")
    (row,) = [r for r in page["inputs"]["ciq"] if r["kind"] == "comps"]
    root = tmp_path / "ciq"
    (root / "IT").mkdir(parents=True)
    export = root / "IT" / row["file"]
    export.write_bytes(b"one comps export's bytes")
    row["sha256"], row["bytes"] = provenance.file_sha256(export)
    monkeypatch.setattr(ciq_sheets, "comps_export_stamp",
                        lambda b: date(2026, 11, 12) if b.workbook("comps") else None)
    tree = _fleet(tmp_path / "repo", {"IT": page})
    out = _run(tree, [root], monkeypatch)
    assert out["moved"] == ["IT"] and out["skipped"] == [] and out["unchanged"] == []
    assert out["skip_count"][0].startswith("0 skipped of 1 recorded comps export(s)")
    written = json.loads((tree / "data" / "dossiers" / "IT" / "dossier.json").read_text())
    assert [r.get("export_date") for r in written["inputs"]["ciq"]
            if r["kind"] == "comps"] == ["2026-11-12"]


def test_a_matched_export_stating_no_date_is_named_never_reported_unchanged(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The export the record names IS on disk and is read as a comps export, but no export date is
    read off it (the reader returns none): the page is named with that sha256 and the file, and is
    not "unchanged". The other cause, a file not read as comps at all, has its own line (F2)."""
    from vinci.dossier import ciq_sheets

    page = _undated("IT")
    (row,) = [r for r in page["inputs"]["ciq"] if r["kind"] == "comps"]
    root = tmp_path / "ciq"
    (root / "IT").mkdir(parents=True)
    export = root / "IT" / row["file"]
    export.write_bytes(b"one comps export's bytes")
    row["sha256"], row["bytes"] = provenance.file_sha256(export)
    monkeypatch.setattr(ciq_sheets, "comps_export_stamp", lambda b: None)
    tree = _fleet(tmp_path / "repo", {"IT": page})
    out = _run(tree, [root], monkeypatch)
    assert out["skipped"] == [
        f"IT: skipped: export {row['sha256']} ({export.name}) states no export date"]
    assert out["moved"] == [] and out["unchanged"] == []
    assert out["skip_count"][0].startswith("1 skipped of 1 recorded comps export(s)")
    _no_local_path(out, tmp_path)                           # a file name, never a local path


def test_the_count_is_over_the_pages_the_step_ran_on(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A SEALED page is refused before the step runs, so it is named under "refused" and never
    counted among the pages the step looked at (code review, round 0)."""
    tree = _fleet(tmp_path / "repo", {"IT": _undated("IT"), "NKE": _living("NKE")})
    (tree / "data" / "dossiers" / "NKE" / "known_wrong.json").write_text("{}\n")
    empty = tmp_path / "ciq"
    empty.mkdir()
    out = _run(tree, [empty], monkeypatch)
    assert out["refused"] == ["NKE"] and len(out["skipped"]) == 1
    assert out["skip_count"][0].endswith("on 1 of 1 pages refreshed"), out["skip_count"]


def test_a_pass_with_no_skip_reporting_step_states_no_count(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A no-op pass, or a step that looks for no export, adds no skip count: the count is the export
    pass's, never a line every refresh prints."""
    monkeypatch.setattr(refresh, "mirror_to_frontend", lambda: None)
    tree = _fleet(tmp_path / "repo", {"NKE": _living("NKE")})
    out = refresh.refresh_fleet(tree)
    assert out == {"moved": [], "unchanged": ["NKE"], "refused": [], "skipped": []}


def test_the_step_reports_only_its_last_page() -> None:
    """The step's report describes the page it was last applied to, so one reused across pages
    cannot carry one page's skip onto the next."""
    step = refresh.export_date_transform("IT", [Path("/nonexistent-ciq-root")])
    assert isinstance(step, refresh.NamesSkips)
    step(_undated("IT"))
    assert len(step.skipped) == 1 and len(step.looked_for) == 1
    step(_living("NKE"))
    assert step.skipped == [] and step.looked_for == []


# --- (1) a CIQ column's own stated filing date counts where it is later --------------------------

def test_a_later_panel_filing_date_dates_the_page_and_is_named() -> None:
    """THE POSITIVE, off IT's page as committed at c58d5b2f (every date ≤ 2026-11-11, its panel
    filed 2026-02-12). Moved one day past the page's latest date, the panel's filing date sets
    `analysis_as_of`, and the rule names the field it came from. No committed page has one later
    today, so the value is moved on a real page rather than found on one."""
    page = _frozen("IT")
    assert page["mechanical"]["capital_structure"]["maturity_check"]["panel_filed"] == "2026-02-12"
    assert page["date_semantics"]["analysis_as_of"] == "2026-11-11"
    page["mechanical"]["capital_structure"]["maturity_check"]["panel_filed"] = "2026-11-12"
    ds = vb.date_semantics(page)
    assert ds.analysis_as_of == "2026-11-12"
    assert ds.analysis_as_of_rule == vb.RULE_DATA_DATES + vb.RULE_FILED_CLAUSE.format(
        where=".".join(PANEL_FILED))
    for k in ("price_as_of", "market_cap_as_of", "tev_as_of", "consensus_as_of",
              "balance_sheet_date", "historical_multiple_latest_observation"):
        assert getattr(ds, k) == page["date_semantics"][k], k   # only the knowable date moves


def test_a_later_panel_filing_date_counts_beside_an_export_date() -> None:
    """The clause follows either rule: on a page whose record states a comps export date, a panel
    filed later than that export dates the page too."""
    page = _frozen("IT")
    (row,) = [r for r in page["inputs"]["ciq"] if r["kind"] == "comps"]
    row["export_date"] = FIXTURE["IT"]["export_date"]               # 2026-11-12
    page["mechanical"]["capital_structure"]["maturity_check"]["panel_filed"] = "2026-11-13"
    ds = vb.date_semantics(page)
    assert (ds.analysis_as_of, ds.ciq_exported_as_of) == ("2026-11-13", "2026-11-12")
    assert ds.analysis_as_of_rule.startswith(vb.RULE_KNOWABLE + "; later than every date")


def test_only_the_filing_date_that_sets_the_page_is_named(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Two stated filing dates, both later than every other date: the rule names the one that
    sets `analysis_as_of`, never both (code review, round 0). A second field is declared for the
    test, since a page carries one today."""
    second = ("mechanical", "capital_structure", "maturity_check", "second_filed")
    monkeypatch.setattr(vb, "CIQ_FILED_DATES", (PANEL_FILED, second))
    page = _frozen("IT")
    page["mechanical"]["capital_structure"]["maturity_check"] |= {
        "panel_filed": "2026-11-13", "second_filed": "2026-11-12"}
    ds = vb.date_semantics(page)
    assert ds.analysis_as_of == "2026-11-13"
    assert ds.analysis_as_of_rule.endswith(": " + ".".join(PANEL_FILED))


@pytest.mark.parametrize("filed", ["2026-02-12", "2026-11-11"])
def test_an_earlier_or_equal_panel_filing_date_moves_nothing(filed: str) -> None:
    """THE NEGATIVE. IT's real panel date (2026-02-12), and one ON the page's latest date: the block
    is the one the page carries, word for word, and the rule gains no clause."""
    page = _frozen("IT")
    page["mechanical"]["capital_structure"]["maturity_check"]["panel_filed"] = filed
    ds = vb.date_semantics(page)
    assert json.loads(ds.model_dump_json(exclude={"ciq_exported_as_of"})) == page["date_semantics"]
    assert ds.analysis_as_of_rule == vb.RULE_DATA_DATES


def test_the_filing_date_is_read_as_a_structured_value_never_off_a_display_string() -> None:
    """The panel's `Source` note and the vintage line print the same date as text ("A 2025 filed
    Feb-12-2026"). Those strings are display: moving them alone moves nothing."""
    page = _frozen("IT")
    cs = page["mechanical"]["capital_structure"]
    cs["detail_as_of"] = "A 2025 filed Dec-31-2026"
    cs["panel_vintage"]["source_ref"] = "CIQ Capital Structure Details — A 2025 filed Dec-31-2026"
    assert vb.date_semantics(page).analysis_as_of == "2026-11-11"
    absent = copy.deepcopy(page)
    del absent["mechanical"]["capital_structure"]["maturity_check"]["panel_filed"]
    assert vb.date_semantics(absent).analysis_as_of == "2026-11-11"


def test_no_committed_page_is_dated_before_a_ciq_filing_date_it_carries() -> None:
    """END TO END, on the living corpus: every page that carries the panel's filing date is dated
    on or after it, and its rule names the panel exactly when the panel sets the date."""
    pages = sorted(DOSS.glob("*/dossier.json"))
    carried = 0
    for p in pages:
        doc = json.loads(p.read_text())
        filed = (((doc.get("mechanical") or {}).get("capital_structure") or {})
                 .get("maturity_check") or {}).get("panel_filed")
        if not filed:
            continue
        carried += 1
        ds = doc["date_semantics"]
        assert ds["analysis_as_of"] >= filed, p.parent.name
        assert (".".join(PANEL_FILED) in ds["analysis_as_of_rule"]) == (
            ds["analysis_as_of"] == filed and filed > max(
                [str(ds[k]).lstrip("≥")[:10] for k in (
                    "price_as_of", "market_cap_as_of", "tev_as_of", "consensus_as_of",
                    "balance_sheet_date", "historical_multiple_latest_observation") if ds.get(k)]
                + ([ds["ciq_exported_as_of"]] if ds.get("ciq_exported_as_of") else []))
        ), p.parent.name
    assert carried >= 20, (carried, len(pages))                  # never vacuous
