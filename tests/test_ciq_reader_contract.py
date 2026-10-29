"""THE CIQ READER CONTRACT, ON FILES CI CAN OPEN (audit items H-D2, H-D3).

Every real CIQ export is licensed and git-ignored, so CI had never opened a file in any CIQ format:
on 0fa8ce4a the 480 tests that read one skipped there, and rounding a fractional date serial in
`ciq.excel_date` instead of truncating it left the whole offline suite green. This suite reads
the SYNTHETIC exports `tests/fixtures/ciq_synthetic/generate.py` writes for an invented issuer
(ZZFX) — BIFF `.xls`, real RTF and one `.xlsx`, laid out the way the readers address them — through
the real decode path: bytes → `classify` → xlrd / openpyxl / striprtf → `CiqBundle` → the readers.
It never skips; it needs nothing git-ignored.

TODAY'S BEHAVIOUR IS PINNED AS IT IS. Where today's behaviour is a known defect, the pin is
``xfail(strict=True, raises=AssertionError)`` naming the defect: the fix turns it into an unexpected
pass, which fails the run until the marker is removed, and any OTHER exception (a fix that changed a
signature) fails it too rather than hiding behind the xfail.

The fixture is FROZEN, so value-level pins are allowed here (CLAUDE.md TEST-LAYER RULE). Expected
figures are read from the generator's own constants; the only literals are calendar facts (the
1900-system serials of the issuer's year ends) and the readers' own output strings.
"""

from __future__ import annotations

import re
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.dossier import ciq_balance
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import (
    CiqAmbiguousError,
    CiqBundle,
    CiqFormat,
    CiqMislabelledError,
    CiqParseError,
    CiqUnavailableError,
    CiqWorkbook,
    classify,
    clean_num,
    excel_date,
    is_empty_view,
    period_type,
    read_sheets,
    read_text,
    stated_period_type,
)
from vinci.dossier.schemas import CHECK_AGREE, CHECK_DIFFER, SourceStatus

FIX = gen.HERE
ANNUAL = FIX / gen.ANNUAL_XLS
QUARTERLY = FIX / gen.QUARTERLY_XLS
CUSTOMERS = FIX / gen.CUSTOMERS_RTF
SUPPLIERS = FIX / gen.SUPPLIERS_RTF
XLSX = FIX / gen.QUARTERLY_XLSX
XLS_1904 = FIX / gen.QUARTERLY_1904_XLS
ESTIMATES = FIX / gen.ESTIMATES_XLS
HEADER_ROW = 14  # the period-header row of every Financials statement sheet, as CIQ lays it out


def _bundle(*paths: Path) -> CiqBundle:
    return CiqBundle.from_files(gen.TICKER, sorted(paths))


@pytest.fixture
def bundle() -> CiqBundle:
    """The whole ZZFX folder, as the assembler loads a real ticker folder."""
    return _bundle(*(FIX / gen.TICKER).iterdir())


def _row(rows: list[list[Any]], label: str) -> list[Any]:
    ri = cs._find_row(rows, label)
    assert ri is not None, label
    return rows[ri]


# --- the fixture itself -------------------------------------------------------------------------


def test_the_committed_exports_are_exactly_what_the_generator_writes(tmp_path: Path) -> None:
    """Bytes for BIFF and RTF; decoded cell values for the `.xlsx` (its XML may change across
    openpyxl releases, its values may not). A hand edit to a committed file fails here."""
    gen.build_all(tmp_path)
    assert gen.drift(FIX, tmp_path) == []


def test_the_fixture_folder_holds_only_generator_outputs() -> None:
    held = {p.relative_to(FIX).as_posix() for p in FIX.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith(".")}
    assert held == {*gen.OUTPUTS, "generate.py"}


def test_the_drift_check_closes_each_xlsx_it_opens(monkeypatch: pytest.MonkeyPatch) -> None:
    """A read-only openpyxl workbook holds its zip open until it is closed or collected, so the
    drift check's reader closes it itself (PR #853 review, round 1)."""
    import openpyxl

    opened: list[Any] = []
    real = openpyxl.load_workbook

    def spy(*args: Any, **kwargs: Any) -> Any:
        opened.append(book := real(*args, **kwargs))
        return book

    monkeypatch.setattr(openpyxl, "load_workbook", spy)
    gen.ooxml_values(XLSX)
    assert len(opened) == 1
    assert opened[0]._archive.fp is None, "the .xlsx is still open after ooxml_values returned"


@pytest.mark.parametrize(("path", "magic", "fmt"), [
    (ANNUAL, b"\xd0\xcf\x11\xe0", CiqFormat.BIFF_XLS),
    (QUARTERLY, b"\xd0\xcf\x11\xe0", CiqFormat.BIFF_XLS),
    (XLS_1904, b"\xd0\xcf\x11\xe0", CiqFormat.BIFF_XLS),
    (XLSX, b"PK\x03\x04", CiqFormat.OOXML),
    (CUSTOMERS, b"{\\rt", CiqFormat.RTF_TEXT),
    (SUPPLIERS, b"{\\rt", CiqFormat.RTF_TEXT),
], ids=lambda v: v.name if isinstance(v, Path) else None)
def test_each_export_is_the_real_format_its_extension_names(path: Path, magic: bytes,
                                                            fmt: CiqFormat) -> None:
    assert path.read_bytes()[:4] == magic
    assert classify(path) is fmt


def test_an_ole_container_named_rtf_is_classified_as_the_disguised_word_doc(tmp_path: Path) -> None:
    """CIQ's transcripts are OLE Word documents with an `.rtf` extension. The sniff reads the bytes,
    not the name — an OLE container under `.rtf` is never handed to striprtf."""
    disguised = tmp_path / f"{gen.ISSUER}, Q1 2027 Earnings Call, Sep 22, 2026.rtf"
    shutil.copyfile(QUARTERLY, disguised)
    assert classify(disguised) is CiqFormat.OLE_DISGUISED
    (wb,) = _bundle(disguised).workbooks
    assert (wb.kind, wb.fmt) == ("transcript", CiqFormat.OLE_DISGUISED)


# --- read_sheets / read_text, per format ----------------------------------------------------------


def test_read_sheets_on_biff_returns_every_sheet_by_its_name() -> None:
    assert list(read_sheets(ANNUAL)) == ["Income Statement", "Balance Sheet", "Cash Flow",
                                         "Capital Structure Summary",
                                         "Capital Structure Details", "Segments"]
    assert list(read_sheets(QUARTERLY)) == ["Income Statement", "Balance Sheet", "Cash Flow",
                                            "Multiples", "Capital Structure Summary"]


def test_read_sheets_on_biff_decodes_text_numbers_dates_and_blanks() -> None:
    inc = read_sheets(QUARTERLY)["Income Statement"]
    assert inc[HEADER_ROW][0] == "For the Fiscal Period Ending\n"
    assert inc[HEADER_ROW][8] == "3 months\nFQ4/CQ2\nMay-31-2026"
    assert _row(inc, "Total Revenue")[1:] == list(gen.Q_REVENUE)
    # a BIFF date cell reads as its float SERIAL; an unwritten cell as ''; rows pad to sheet width
    bs = read_sheets(ANNUAL)["Balance Sheet"]
    # the 1900-system serials of May 31, 2022..2026
    assert bs[HEADER_ROW][1:] == [44712.0, 45077.0, 45443.0, 45808.0, 46173.0]
    assert inc[0] == [""] * len(inc[HEADER_ROW])


def test_read_sheets_on_xlsx_returns_the_same_sheets_and_header_text() -> None:
    xl, bi = read_sheets(XLSX), read_sheets(QUARTERLY)
    assert list(xl) == list(bi)
    assert xl["Income Statement"][HEADER_ROW] == bi["Income Statement"][HEADER_ROW]
    assert xl["Multiples"][HEADER_ROW - 1][2] == datetime(2024, 8, 31)  # openpyxl: a datetime


def test_every_cell_means_the_same_number_and_date_in_both_encodings() -> None:
    """The format-agnostic half of the contract: whatever the library hands back for a cell
    (xlrd '' vs openpyxl None, a float serial vs a datetime), `clean_num` and `excel_date` must read
    the same value out of it, cell for cell, on every sheet. A DATE cell is compared as a date only:
    BIFF stores it as a bare serial that `clean_num` will also read as a number, OOXML as a datetime
    it will not, and no reader asks a date header for a number."""
    xl, bi = read_sheets(XLSX), read_sheets(QUARTERLY)
    dates = 0
    for name, rows in bi.items():
        assert len(xl[name]) == len(rows), name
        for r, (brow, xrow) in enumerate(zip(rows, xl[name], strict=True)):
            for c, bcell in enumerate(brow):
                xcell = xrow[c] if c < len(xrow) else None
                where = f"{name}!r{r}c{c}"
                assert excel_date(xcell) == excel_date(bcell), where
                if isinstance(xcell, datetime):
                    dates += 1
                    continue
                assert clean_num(xcell) == clean_num(bcell), where
    assert dates == len(gen.M_DATES)  # the Multiples header, and nothing else, is date-typed


def test_each_reader_refuses_a_format_that_is_not_its_own() -> None:
    with pytest.raises(CiqParseError, match="not a spreadsheet"):
        read_sheets(CUSTOMERS)
    with pytest.raises(CiqParseError, match="not text"):
        read_text(ANNUAL)


def test_read_text_on_real_rtf_renders_the_relationship_table_as_pipes() -> None:
    text = read_text(CUSTOMERS)
    assert "Customer Name|Relationship Type|Primary Industry|Source|" in text
    assert not is_empty_view(text)


def test_an_empty_relationships_view_says_so_in_its_own_words() -> None:
    assert is_empty_view(read_text(SUPPLIERS))


# --- CiqBundle.from_files -------------------------------------------------------------------------


def test_from_files_kinds_every_export_and_reads_period_type_from_the_name(
        bundle: CiqBundle) -> None:
    got = sorted((w.path.name, w.kind, w.fmt, w.freq) for w in bundle.workbooks)
    assert got == sorted([
        (ANNUAL.name, "financials", CiqFormat.BIFF_XLS, "annual"),
        (QUARTERLY.name, "financials", CiqFormat.BIFF_XLS, "quarterly"),
        (CUSTOMERS.name, "customers", CiqFormat.RTF_TEXT, None),
        (SUPPLIERS.name, "customers", CiqFormat.RTF_TEXT, None),
    ])
    assert bundle.unrecognised == ()
    assert not bundle.is_empty
    wb_a, wb_q = (bundle.workbook("financials", freq=f) for f in ("annual", "quarterly"))
    assert (wb_a and wb_a.path, wb_q and wb_q.path) == (ANNUAL, QUARTERLY)
    assert len(bundle.all_workbooks("customers")) == 2


def test_from_files_reads_period_type_from_the_sheet_when_the_name_carries_none(
        tmp_path: Path) -> None:
    """An export whose filename has no `_Annual`/`_Quarterly` token falls back to the verbatim
    "Period Type:" cell of its Income Statement — read here off a real BIFF file."""
    for src, want in ((ANNUAL, "annual"), (QUARTERLY, "quarterly")):
        unnamed = tmp_path / want / f"{gen.STEM} Financials.xls"
        unnamed.parent.mkdir()
        shutil.copyfile(src, unnamed)
        (wb,) = _bundle(unnamed).workbooks
        assert wb.freq == want
        assert period_type(read_sheets(unnamed)["Income Statement"]) == want


def test_from_files_skips_sync_droppings_and_names_what_it_cannot_kind(tmp_path: Path) -> None:
    for p in (ANNUAL, QUARTERLY):
        shutil.copyfile(p, tmp_path / p.name)
    for dropping in (".DS_Store", f"~${ANNUAL.name}", "operator notes.txt"):
        (tmp_path / dropping).write_bytes(b"x")
    got = _bundle(*tmp_path.iterdir())
    assert sorted(w.freq or "" for w in got.workbooks) == ["annual", "quarterly"]
    assert got.unrecognised == ("operator notes.txt",)


def test_from_files_refuses_two_exports_of_one_period_type(tmp_path: Path) -> None:
    second = tmp_path / f"{gen.STEM} Financials_Quarterly (1).xls"
    shutil.copyfile(QUARTERLY, second)
    with pytest.raises(CiqAmbiguousError, match="financials \\(quarterly\\)"):
        _bundle(QUARTERLY, second)


def test_sheet_fails_loud_for_an_absent_sheet_kind_or_unreadable_format(bundle: CiqBundle) -> None:
    with pytest.raises(CiqUnavailableError, match="has no 'Ratios' sheet"):
        bundle.sheet("financials", "Ratios", freq="annual")
    with pytest.raises(CiqUnavailableError, match="no 'estimates' CIQ workbook"):
        bundle.sheet("estimates", "Consensus")
    with pytest.raises(CiqUnavailableError, match="not a spreadsheet"):
        bundle.sheet("customers", "Customers")


def test_a_filename_that_contradicts_the_period_type_cell_is_not_trusted(tmp_path: Path) -> None:
    """A-X1, FIXED 2026-10-29 (was a strict xfail): LLY's shape — its annual file saved under the
    quarterly name — is refused at construction, naming both period types."""
    misnamed = tmp_path / QUARTERLY.name
    shutil.copyfile(ANNUAL, misnamed)
    try:
        got = _bundle(misnamed)
    except RuntimeError as exc:
        # Refused at construction is one acceptable fix, but only a refusal that names the
        # disagreement. Anything else re-raises: a failure the xfail (raises=AssertionError)
        # does not absorb, so an unrelated regression cannot pass here as the fix.
        if not {"annual", "quarterly"} <= set(re.findall(r"[a-z]+", str(exc).lower())):
            raise
        return
    assert [w.freq for w in got.workbooks] == ["annual"]


def test_the_a_x1_pin_never_takes_an_unrelated_failure_for_its_fix(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The A-X1 pin accepts a refusal at construction as a fix — but only a refusal ABOUT the
    disagreement. An unrelated loader failure must surface, not pass the pin as 'fixed' (an XPASS
    a reviewer would read as the defect closing). PR #853 review, round 1."""
    def unrelated(cls: type[CiqBundle], ticker: str, paths: list[Path]) -> CiqBundle:
        raise CiqParseError("an unrelated loader failure")

    monkeypatch.setattr(CiqBundle, "from_files", classmethod(unrelated))
    with pytest.raises(CiqParseError, match="unrelated"):  # the mark leaves the function unwrapped
        test_a_filename_that_contradicts_the_period_type_cell_is_not_trusted(tmp_path)


@pytest.mark.parametrize(("src", "misname"), [
    (ANNUAL, QUARTERLY.name),   # LLY's pair: its annual file under the quarterly name
    (QUARTERLY, ANNUAL.name),   # MCK's pair: its quarterly file under the annual name
])
def test_a_mislabelled_export_is_refused_either_way_round(
        tmp_path: Path, src: Path, misname: str) -> None:
    """A-X1, both real shapes in the 34 non-test folders (2026-10-29). Refused at construction as
    a `CiqAmbiguousError`, so every caller that stops a name on two exports of one kind stops it
    here too, rather than degrading the page to a missing section."""
    shutil.copyfile(src, tmp_path / misname)
    with pytest.raises(CiqMislabelledError) as refused:
        _bundle(tmp_path / misname)
    assert isinstance(refused.value, CiqAmbiguousError)
    named, stated = (("quarterly", "annual") if src == ANNUAL else ("annual", "quarterly"))
    assert f"names a {named} export" in str(refused.value)
    assert f"state Period Type '{stated}'" in str(refused.value)


def test_one_statement_misreporting_its_period_type_is_not_a_mislabel(tmp_path: Path) -> None:
    """NEGATIVE PIN — AORT's recorded shape: a quarterly export whose EMPTY Income Statement reads
    Annual beside a Balance Sheet and Cash Flow reading Quarterly. A 'No Data Available' shell
    states nothing, so the export states Quarterly and agrees with its name; refusing it would
    stop a name on one empty sheet's boilerplate. With the shell the ONLY statement, nothing is
    stated and the filename stands."""
    sheets = gen._quarterly_sheets("USD")
    sheets["Income Statement"] = gen._no_data_shell("Income Statement", "Annual")
    path = tmp_path / QUARTERLY.name
    gen.write_biff(path, sheets)
    assert stated_period_type(read_sheets(path)) == "quarterly"
    assert [w.freq for w in _bundle(path).workbooks] == ["quarterly"]
    lone = tmp_path / "lone" / QUARTERLY.name
    gen.write_biff(lone, {"Income Statement": sheets["Income Statement"]})
    assert stated_period_type(read_sheets(lone)) is None
    assert [w.freq for w in _bundle(lone).workbooks] == ["quarterly"]


def test_a_side_sheet_stating_another_period_type_is_not_a_mislabel(tmp_path: Path) -> None:
    """NEGATIVE PIN — FUBO's Annual export carries a Capital Structure Details sheet reading
    Quarterly. Only the Income Statement, Balance Sheet and Cash Flow speak for the export."""
    sheets = gen._annual_sheets("USD")
    sheets["Capital Structure Details"] = [
        ["Quarterly" if c == "Annual" else c for c in row]
        for row in sheets["Capital Structure Details"]]
    path = tmp_path / ANNUAL.name
    gen.write_biff(path, sheets)
    assert period_type(read_sheets(path)["Capital Structure Details"]) == "quarterly"
    assert [w.freq for w in _bundle(path).workbooks] == ["annual"]


def test_a_lone_export_never_answers_for_the_other_period_type() -> None:
    """A-D11: an annual-only folder answered a quarterly request with its annual workbook, so its
    fiscal years printed as 'quarterly' columns. The request now reads UNKNOWN, naming what the
    folder holds."""
    lone = _bundle(ANNUAL)
    assert lone.workbook("financials", freq="quarterly") is None
    assert lone.workbook("financials", freq="annual") is not None
    with pytest.raises(CiqUnavailableError, match="export is annual, and another period type"):
        lone.sheet("financials", "Income Statement", freq="quarterly")
    got = cs.financial_summary_quarterly(lone)
    assert got.status is SourceStatus.UNKNOWN and got.value is None
    assert "no quarterly 'financials' CIQ workbook" in (got.note or "")


def test_a_lone_export_whose_period_type_is_unread_still_answers() -> None:
    """NEGATIVE PIN — the recorded choice A-D11 narrowed is kept where it was scoped: a lone
    export whose period type is UNREAD (no filename token, no statement saying) answers either
    request, as before."""
    unread = CiqWorkbook(kind="financials", path=ANNUAL, fmt=CiqFormat.BIFF_XLS, freq=None)
    b = CiqBundle(ticker=gen.TICKER, workbooks=(unread,))
    assert b.workbook("financials", freq="quarterly") is unread
    assert b.workbook("financials", freq="annual") is unread


def test_read_sheets_releases_every_workbook_it_opens(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deferred from #853's review: `read_sheets` left xlrd's mapped file and openpyxl's read-only
    zip open until garbage collection. Every row is copied out first, so both are released before
    it returns."""
    import openpyxl
    import xlrd  # type: ignore[import-untyped]

    opened: list[Any] = []

    def spy(real: Any) -> Any:
        def opener(*args: Any, **kwargs: Any) -> Any:
            opened.append(book := real(*args, **kwargs))
            return book
        return opener

    monkeypatch.setattr(xlrd, "open_workbook", spy(xlrd.open_workbook))
    monkeypatch.setattr(openpyxl, "load_workbook", spy(openpyxl.load_workbook))
    assert read_sheets(QUARTERLY) and read_sheets(XLSX)
    biff, ooxml = opened
    assert biff._resources_released, "the .xls is still mapped after read_sheets returned"
    assert ooxml._archive.fp is None, "the .xlsx is still open after read_sheets returned"


# --- excel_date --------------------------------------------------------------------------------


def test_excel_date_decodes_the_biff_balance_sheet_serials() -> None:
    """THE MUTATION TARGET of this build: the annual Balance Sheet header is a row of 1900-system
    serials, and every one must land on the issuer's fiscal year end."""
    head = read_sheets(ANNUAL)["Balance Sheet"][HEADER_ROW]
    assert [excel_date(c) for c in head[1:]] == list(gen.A_DATES)


def test_excel_date_decodes_the_multiples_serials_in_both_encodings() -> None:
    for path in (QUARTERLY, XLSX):
        head = read_sheets(path)["Multiples"][HEADER_ROW - 1]
        assert head[0] == "For Quarter Ending"
        assert [excel_date(c) for c in head[2:]] == list(gen.M_DATES), path.suffix


@pytest.mark.parametrize(("cell", "want"), [
    (46173, date(2026, 5, 31)),
    (46173.75, date(2026, 5, 31)),         # a time-of-day fraction never moves the day
    (datetime(2026, 5, 31, 16, 0), date(2026, 5, 31)),
    ("May-31-2026", date(2026, 5, 31)),
    ("2026-05-31", date(2026, 5, 31)),
    ("05/31/2026", date(2026, 5, 31)),
    (" May-31-2026 ", date(2026, 5, 31)),
    (True, None),                          # a bool is not a serial
    (1e12, None),                          # overflow → None, never a raise
    ("12 months\nMay-31-2026", None),      # a whole header cell is not a date — see _column_date
    (None, None),
])
def test_excel_date_shapes(cell: Any, want: date | None) -> None:
    assert excel_date(cell) == want


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "A-D4: `excel_date` assumes the 1900 date system; a workbook saved in the 1904 system "
    "decodes every serial 1,462 days early"))
def test_a_1904_date_system_workbook_decodes_to_the_true_dates() -> None:
    assert cs.ev_ebitda_asof(_bundle(XLS_1904)) == gen.M_DATES[-1]


# --- period headers ------------------------------------------------------------------------------


def test_every_quarterly_header_cell_decodes_to_its_quarter_end() -> None:
    """Incl. the off-calendar shape '3 months\\nFQ4/CQ2\\nMay-31-2026' and a 'Restated' prefix."""
    inc = read_sheets(QUARTERLY)["Income Statement"]
    head = inc[HEADER_ROW][1:]
    assert "3 months\nFQ4/CQ2\nMay-31-2026" in head
    assert head[gen.RESTATED_Q].startswith("Restated\n")
    assert [cs._column_date(c) for c in head] == list(gen.Q_DATES)
    assert [ciq_balance.header_period(c) for c in head] == [(None, d) for d in gen.Q_DATES]
    assert not any(cs._is_ltm(c) for c in head)


def test_annual_header_cells_carry_fy_ltm_and_the_reclassified_basis() -> None:
    head = read_sheets(ANNUAL)["Income Statement"][HEADER_ROW]
    assert [ciq_balance.header_period(c) for c in head[1:]] == (
        [("FY", d) for d in gen.A_DATES] + [("LTM", gen.LTM_DATE)])
    assert cs._reclassified_cols(head) == {1}
    assert [cs._is_ltm(c) for c in head[1:]] == [False] * 5 + [True]


def test_the_quarterly_balance_sheet_header_is_found_and_dated() -> None:
    bs = read_sheets(QUARTERLY)["Balance Sheet"]
    assert cs._dated_header(bs) == cs._bs_period_header(bs) == HEADER_ROW
    assert bs[HEADER_ROW][8] == "FQ4/CQ2\nMay-31-2026"
    assert [cs._column_date(c) for c in bs[HEADER_ROW][1:]] == list(gen.Q_DATES)


def test_period_type_reads_the_verbatim_cell_of_each_export() -> None:
    assert period_type(read_sheets(ANNUAL)["Income Statement"]) == "annual"
    assert period_type(read_sheets(QUARTERLY)["Income Statement"]) == "quarterly"
    assert period_type(read_sheets(XLSX)["Income Statement"]) == "quarterly"


def test_a_latest_value_is_stamped_with_its_own_period_header(bundle: CiqBundle) -> None:
    nd = cs.net_debt(bundle)
    assert nd.status is SourceStatus.PRESENT
    assert nd.value == round(gen.Q_DEBT[-1] - gen.Q_CASH[-1], 1)
    assert nd.source_ref == "CIQ Financials→Balance Sheet 'Net Debt' [FQ1/CQ3 Aug-31-2026]"
    eb = cs.ltm_ebitda(bundle)
    assert eb.value == gen._sum4(gen.Q_EBITDA, 8)
    assert eb.source_ref == "CIQ Financials→Income Statement 'EBITDA' [LTM 12 months Aug-31-2026]"


def test_fq_cq_quarters_are_not_labelled_as_fiscal_years(bundle: CiqBundle) -> None:
    """A-D3, FIXED 2026-10-29 (was a strict xfail)."""
    table = cs.financial_summary_quarterly(bundle).value
    assert table is not None
    assert not [c for c in table.columns if c.startswith("FY")], table.columns


def test_fq_cq_quarters_still_yield_a_same_quarter_revenue_yoy(bundle: CiqBundle) -> None:
    """A-D3, FIXED 2026-10-29 (was a strict xfail)."""
    traj = cs.multi_year_trajectory(bundle).value
    assert traj is not None and "Revenue YoY (latest same-quarter)" in traj, traj
    yoy = gen.Q_REVENUE[-1] / gen.Q_REVENUE[-5] - 1   # FQ1 against the FQ1 a year earlier
    assert (f"Revenue YoY (latest same-quarter): {yoy:+.1%} (Q1 {gen._mdy(gen.Q_DATES[-1])} vs "
            f"Q1 {gen._mdy(gen.Q_DATES[-5])})") in traj


def test_a_yoy_never_reaches_past_the_prior_fiscal_year(tmp_path: Path) -> None:
    """Found with A-D3 (2026-10-29): with the prior year's quarter on another basis, the YoY took
    the nearest same-quarter column on the reader's basis — two to four years back on six of the 34
    non-test exports (AORT read +50.7% against Q1 2022), under a "YoY" label. Here the FQ1 a year
    before the latest is reclassified, as AORT's was: there is no same-basis comparison, so there
    is no YoY line — never the FQ1 two years back."""
    sheets = gen._quarterly_sheets("USD")
    head = sheets["Income Statement"][HEADER_ROW]
    prior = 1 + len(gen.Q_DATES) - 5           # the FQ1 a year before the latest FQ1
    head[prior] = f"Reclassified\n{head[prior]}"
    path = tmp_path / QUARTERLY.name
    gen.write_biff(path, sheets)
    b = _bundle(path)
    traj = cs.multi_year_trajectory(b).value or ""
    assert "Revenue YoY" not in traj, traj
    table = cs.financial_summary_quarterly(b).value
    assert table is not None
    (yoy,) = [r.cells for r in table.rows if "YoY" in r.label]
    assert yoy[-1] == "— (basis)"


def test_each_quarter_column_carries_its_fiscal_quarter_and_fiscal_year(bundle: CiqBundle) -> None:
    """A-D3 and A-X2 on the real format, value-level (the fixture is frozen): the invented
    issuer's year ends May 31, so its fiscal year is the calendar year of the end date for a
    quarter ending by May, and the next one after — derived here from that fact, independently of
    the reader's own rule. Its same-quarter YoY row is computed for every quarter with a prior."""
    table = cs.financial_summary_quarterly(bundle).value
    assert table is not None
    assert table.columns == [f"Q{tag[2]}-{(d.year + (d.month > 5)) % 100:02d}"
                             for tag, d in zip(gen.Q_TAGS, gen.Q_DATES, strict=True)]
    (yoy,) = [r.cells for r in table.rows if "YoY" in r.label]
    assert yoy[:4] == ["—"] * 4
    assert yoy[-1] == f"{(gen.Q_REVENUE[-1] / gen.Q_REVENUE[-5] - 1) * 100:+.0f}%"


@pytest.mark.parametrize(("cell", "want"), [
    # 'FQx/CQy' (A-D3): the FISCAL quarter, under the fiscal year its year end names
    ("3 months\nFQ4/CQ2\nMay-31-2026", "Q4-26"),
    ("3 months\nFQ1/CQ3\nAug-31-2026", "Q1-27"),
    ("Restated\n3 months\nFQ1/CQ4\nDec-31-2025", "Q1-26"),   # a September year end's first quarter
    ("FQ4/CQ2\nMay-31-2026", "Q4-26"),                      # the quarterly balance sheet's shape
    ("Press Release\n3 months\nFQ3/CQ1\nMay-03-2026", "Q3-26"),  # a 52/53-week July year end
    # a bare 'Qn' under a January year end (A-X2): the calendar year of the end was printed
    ("3 months\nQ1\nApr-30-2025", "Q1-26"),
    ("3 months\nQ3\nNov-01-2025", "Q3-26"),
    ("3 months\nQ4\nJan-31-2026", "Q4-26"),
    # NEGATIVE PINS: December quarters, and a 4-4-5 quarter ending days into the next month, keep
    # the calendar year; fiscal years and LTM read as they always did
    ("3 months\nQ2\nJun-30-2026", "Q2-26"),
    ("3 months\nQ1\nApr-04-2026", "Q1-26"),
    ("Reclassified\n3 months\nQ4\nDec-28-2025", "Q4-25"),
    ("12 months\nDec-31-2022", "FY22"),
    ("12 months\nFeb-01-2025", "FY25"),
    ("12 months\nOct-01-2022", "FY22"),
    ("Reclassified\n12 months\nSep-30-2017", "FY17"),
    ("LTM\n12 months\nJun-30-2026", "LTM"),
])
def test_one_parser_labels_every_financials_header_shape(cell: str, want: str) -> None:
    """Every quarter and year shape the 34 non-test exports carry (census 2026-10-29), through the
    one header parser. The dates are period ends; nothing here is an export's data."""
    assert cs._fin_short(cell) == want


def test_the_same_quarter_match_reads_the_fiscal_quarter_never_the_calendar_one() -> None:
    """A 'FQ1/CQ3' column is fiscal quarter 1 — the 3 is the calendar quarter, which a September
    year end's 'FQ3/CQ2' shares with no other column of that fiscal quarter."""
    assert cs.header_period("3 months\nFQ1/CQ3\nAug-31-2026").quarter == 1
    assert cs.header_period("3 months\nQ2\nJun-30-2026").quarter == 2
    assert cs.header_period("12 months\nMay-31-2026").quarter is None
    assert cs.header_period("LTM\n12 months\nAug-31-2026").kind == "LTM"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "DEFERRED (PR #861 round 1): a 52/53-week year ending Jan 1-15 — its Q4 takes the nominal "
    "month (fiscal year N-1) while its fiscal-year column keeps the calendar year of its end (N), "
    "the label `statement_recon`'s same-label drop rule reads; no committed page and no -ta export "
    "has such a year end (2026-10-29)"))
def test_an_early_january_year_ends_q4_and_fy_columns_name_one_year() -> None:
    q4, fy = cs._fin_short("3 months\nQ4\nJan-02-2027"), cs._fin_short("12 months\nJan-02-2027")
    assert q4[-2:] == fy[-2:], (q4, fy)


def test_a_balance_sheet_period_label_is_never_a_raw_serial() -> None:
    """A-D11, FIXED 2026-10-29 (was a strict xfail): the annual balance sheet's serial header
    prints as the date it encodes."""
    ref = cs.net_debt(_bundle(ANNUAL)).source_ref or ""
    assert not re.search(r"\[\d{5}\.0\]", ref), ref
    assert ref == f"CIQ Financials→Balance Sheet 'Net Debt' [{gen._mdy(gen.A_DATES[-1])}]"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "A-D5: the 'latest' column is the rightmost one, and the export's 'Order:' cell is never "
    "read, so a right-to-left sheet serves its OLDEST period as the latest"))
def test_a_right_to_left_sheet_never_serves_its_oldest_period_as_latest() -> None:
    b = _bundle(ANNUAL)
    inc = b.sheet("financials", "Income Statement", freq="annual")
    for r in range(HEADER_ROW, len(inc)):  # the period columns only; the settings block stays put
        inc[r] = [inc[r][0], *reversed(inc[r][1:])]
    order = inc[7].index("Order:")
    inc[7][order + 1] = "Latest on Left"  # the export's own statement of its column order
    got = cs.ltm_ebitda(b)
    assert got.status is not SourceStatus.PRESENT or "Aug-31-2026" in (got.source_ref or ""), (
        got.source_ref)


# --- stated_currency -----------------------------------------------------------------------------

_PANELS = [f"Financials ({freq})→{sheet}" for freq, sheet in (
    ("annual", "Income Statement"), ("annual", "Balance Sheet"), ("annual", "Cash Flow"),
    ("annual", "Capital Structure Summary"), ("annual", "Capital Structure Details"),
    ("quarterly", "Income Statement"), ("quarterly", "Balance Sheet"), ("quarterly", "Cash Flow"),
    ("quarterly", "Capital Structure Summary"))]


def test_stated_currency_reads_every_money_panel_the_exports_carry(bundle: CiqBundle) -> None:
    cur = cs.stated_currency(bundle)
    assert cur is not None
    assert [p.panel for p in cur.panels] == _PANELS
    assert all(p.stated == ["USD"] and p.check == CHECK_AGREE for p in cur.panels)
    assert cur.check == CHECK_AGREE
    cs.require_usd(cur, gen.TICKER)  # does not raise


def test_a_no_data_available_shell_is_not_listed_as_a_money_panel(bundle: CiqBundle) -> None:
    seg = bundle.sheet("financials", "Segments", freq="annual")
    assert cs._no_data_available(seg)
    cur = cs.stated_currency(bundle)
    assert cur is not None and not [p for p in cur.panels if "Segments" in p.panel]


def test_stated_currency_finds_a_panel_stating_another_currency(tmp_path: Path) -> None:
    """The check can FIRE: the same layout written in CHF is refused, panel by panel."""
    chf = tmp_path / gen.ANNUAL_XLS
    gen.build_financials(chf, freq="annual", currency="CHF")
    cur = cs.stated_currency(_bundle(chf, QUARTERLY))
    assert cur is not None and cur.check == CHECK_DIFFER
    assert [p.panel for p in cur.panels if p.stated == ["CHF"]] == _PANELS[:5]
    with pytest.raises(cs.CiqCurrencyError, match="5 CIQ money panel"):
        cs.require_usd(cur, gen.TICKER)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "H-D3, found by this suite: openpyxl hands an empty cell back as None, `_currency_rows` "
    "reads it with str(), and a two-column 'Currency' row then states the currency 'None'"))
def test_stated_currency_agrees_on_the_xlsx_export() -> None:
    cur = cs.stated_currency(_bundle(XLSX))
    assert cur is not None
    assert cur.check == CHECK_AGREE, [(p.panel, p.stated) for p in cur.panels]


# --- the UNAVAILABLE markers ---------------------------------------------------------------------


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
def test_each_unavailable_marker_survives_decoding_and_reads_as_no_value(marker: str) -> None:
    col = gen.MARKERS.index(marker) + 1
    biff = _row(read_sheets(QUARTERLY)["Income Statement"], gen.MARKER_ROW)[col]
    xlsx = _row(read_sheets(XLSX)["Income Statement"], gen.MARKER_ROW)[col]
    assert biff == marker
    assert (xlsx if xlsx is not None else "") == marker  # an empty .xlsx cell reads as None
    for cell in (biff, xlsx):
        assert clean_num(cell) is None
        assert excel_date(cell) is None
        assert cs._column_date(cell) is None


@pytest.mark.parametrize("path", [QUARTERLY, XLSX], ids=lambda p: p.suffix)
def test_a_row_of_nothing_but_markers_has_no_latest_value(path: Path) -> None:
    inc = read_sheets(path)["Income Statement"]
    ri = cs._find_row(inc, gen.MARKER_ROW)
    assert ri is not None
    assert cs._latest_col(inc, ri, cs._period_header(inc)) is None


def test_nm_at_the_latest_close_refuses_rather_than_reaching_back(bundle: CiqBundle) -> None:
    pe = cs.pe_ltm_current(bundle)
    assert pe.status is SourceStatus.UNKNOWN and pe.value is None
    assert pe.note == (f"P/LTM EPS is NM at the latest Close [{gen.M_DATES[-1].isoformat()}] — "
                       "no meaningful trailing P/E")
    assert cs.pe_ltm_asof(bundle) is None


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "A-D2: an UNAVAILABLE 'Total Pref. Equity' cell is added to the EV bridge as 0.0 — the "
    "marker becomes a stated zero claim"))
def test_a_marker_in_the_ev_bridge_is_never_a_zero_claim(bundle: CiqBundle, marker: str) -> None:
    bs = bundle.sheet("financials", "Balance Sheet", freq="quarterly")
    pref = _row(bs, "Total Pref. Equity")
    # the marker cell AS DECODED from the committed BIFF probe row, placed in the latest column
    pref[-1] = _row(read_sheets(QUARTERLY)["Income Statement"],
                    gen.MARKER_ROW)[gen.MARKERS.index(marker) + 1]
    bridge = cs.ev_bridge(bundle, fy_periods=["FY27"])
    assert bridge is not None
    assert [ln for ln in bridge.lines
            if ln.label == "Total Pref. Equity" and ln.value == 0.0] == []


# --- the readers, end to end ---------------------------------------------------------------------


def test_the_multiples_readers_take_the_latest_close_by_date(bundle: CiqBundle) -> None:
    ev = cs.ev_ebitda_current(bundle)
    assert ev.status is SourceStatus.PRESENT
    assert ev.value == gen.M_TEV_EBITDA_CLOSE[-1]
    assert cs.ev_ebitda_asof(bundle) == gen.M_DATES[-1]


def test_the_ev_bridge_reads_the_latest_dated_balance_sheet_column(bundle: CiqBundle) -> None:
    bridge = cs.ev_bridge(bundle, fy_periods=["FY27"])
    assert bridge is not None
    assert bridge.balance_sheet_date == gen.Q_DATES[-1].isoformat()
    assert bridge.net_debt == round(gen.Q_DEBT[-1] - gen.Q_CASH[-1], 1)
    assert bridge.source_file == QUARTERLY.name


def test_customers_parses_the_rtf_table_and_skips_description_rows(bundle: CiqBundle) -> None:
    got = cs.customers(bundle)
    assert got.status is SourceStatus.PRESENT
    assert got.value == (
        "Quillfeather Freight Ltd — Customer · Air Freight and Logistics · src: Company Filing; "
        "Brantwick Municipal Power — Customer · Electric Utilities · src: Press Release; "
        "Tamsworth Kettle Works — Customer · Industrial Machinery · src: Company Filing")
    assert got.source_ref == f"CIQ Customers&Suppliers {CUSTOMERS.name}"


# --- the .xlsx path, end to end through CiqBundle -------------------------------------------------


def test_an_xlsx_export_loads_through_the_bundle() -> None:
    (wb,) = _bundle(XLSX).workbooks
    assert (wb.kind, wb.fmt, wb.freq) == ("financials", CiqFormat.OOXML, "quarterly")


@pytest.mark.parametrize("reader", [
    cs.net_debt, cs.total_debt, cs.ev_ebitda_current, cs.ev_ebitda_asof, cs.pe_ltm_current,
    cs.pe_ltm_asof, cs.financial_summary_quarterly,
], ids=lambda f: f.__name__)
def test_the_xlsx_export_reads_exactly_as_its_biff_twin(reader: Any) -> None:
    assert reader(_bundle(XLSX)) == reader(_bundle(QUARTERLY))


def test_the_xlsx_ev_bridge_matches_its_biff_twin_and_names_its_own_file() -> None:
    xl = cs.ev_bridge(_bundle(XLSX), fy_periods=["FY27"])
    bi = cs.ev_bridge(_bundle(QUARTERLY), fy_periods=["FY27"])
    assert xl is not None and bi is not None
    provenance = {"source_file", "source_sha256"}
    assert xl.model_dump(exclude=provenance) == bi.model_dump(exclude=provenance)
    assert xl.source_file == XLSX.name


# --- the anchor bridge's provenance (audit A-D6) ------------------------------------------------


def test_each_bridged_fact_names_the_export_it_was_read_from(bundle: CiqBundle) -> None:
    """A-D6: the bridge stamped every fact with the QUARTERLY export, so a D&A, OCF or capex read
    off the ANNUAL Cash Flow named a file it never came from (GOOGL's D&A, IT's FCF). Each fact
    now carries its own export's name and hash; a figure built from both names both."""
    got = ciq_balance.extract(bundle, gen.TICKER)
    annual = ((ANNUAL.name, cs.file_provenance(ANNUAL)[0]),)
    quarterly = ((QUARTERLY.name, cs.file_provenance(QUARTERLY)[0]),)
    for key in ("d_and_a", "ocf", "capex", "revenue"):
        assert got.facts[key].workbooks == annual, key
    for key in ("cash", "total_debt", "net_debt"):
        assert got.facts[key].workbooks == quarterly, key
    assert got.facts["d_and_a"].value == gen.A_DA[-1]
    assert got.facts["capex"].value == abs(gen.A_CAPEX[-1])
    assert got.stamp("ocf", "capex") == f"{annual[0][0]} sha {annual[0][1]}"
    assert got.stamp("net_debt") == f"{quarterly[0][0]} sha {quarterly[0][1]}"


def test_a_fact_recording_no_export_never_borrows_the_bundles(bundle: CiqBundle) -> None:
    """NEGATIVE PIN: a fact with no provenance says so; the bundle's first export — the
    quarterly, which is what every fact used to carry — is never put in its place."""
    got = ciq_balance.extract(bundle, gen.TICKER)
    bare = ciq_balance.CiqFacts(
        ticker=gen.TICKER, as_of=None, source_file=got.source_file,
        source_sha256=got.source_sha256,
        facts={"d_and_a": ciq_balance.CiqFact(value=1.0, unit="$M", basis="b", source="s")})
    assert bare.stamp("d_and_a") == "workbook unrecorded"
    assert QUARTERLY.name not in bare.stamp("d_and_a")


# --- the Estimates export: the listing's own rating (A-D10), every guided block (A-D8) ----------


def _estimates(ticker: str = gen.TICKER) -> CiqBundle:
    return CiqBundle.from_files(ticker, [ESTIMATES])


def test_the_recommendation_is_the_listings_own_never_the_industrys() -> None:
    """A-D10: Consensus's 'Industry Recommendation' row was printed as the stock's own on all 20
    pages carrying one (NKE: Outperform (2.50) where its own is Hold (2.73))."""
    v = cs.consensus_view(_estimates()).value or ""
    assert f"Recommendation: {gen.REC_OWN} (CIQ score" in v
    assert gen.REC_INDUSTRY not in v


def test_the_rating_counts_are_the_listings_alone() -> None:
    """A-D10: every category row on the Trends sheet was read, so the industry's counts — and
    every other listing's — were appended to the listing's own with no label."""
    v = cs.consensus_stats(_estimates(), as_of=None).value or ""
    own = ", ".join(f"{c.split(' (')[0]} {int(n)}" for c, n, _ in gen.RATINGS)
    assert v.endswith(f"Ratings: {own}"), v


def test_each_share_class_reads_its_own_block() -> None:
    """The block is chosen by the TICKER in its header, never by position: the second share class
    reads its own rating and counts from the same export."""
    b = _estimates(gen.SECOND_CLASS)
    assert f"Recommendation: {gen.REC_SECOND} (CIQ score" in (cs.consensus_view(b).value or "")
    own = ", ".join(f"{c.split(' (')[0]} {int(n)}" for c, n in gen.SECOND_RATINGS)
    assert (cs.consensus_stats(b, as_of=None).value or "").endswith(f"Ratings: {own}")


def test_a_ticker_with_no_block_borrows_no_rating_and_says_so() -> None:
    """NEGATIVE PIN: an export with no block for the name prints no recommendation and no counts,
    rather than the first listing's or the industry's — and says it found no block, naming the
    blocks it holds, instead of dropping the line unremarked (PR #861 round 1)."""
    b = _estimates("ZZFQ")
    view = cs.consensus_view(b).value or ""
    stats = cs.consensus_stats(b, as_of=None).value or ""
    for rating in (gen.REC_OWN, gen.REC_INDUSTRY, gen.REC_SECOND):
        assert rating not in view and rating not in stats
    for text in (view, stats):
        assert "no Trends block headed with ZZFQ" in text, text
        assert f"{gen.EXCHANGE}:{gen.TICKER}" in text, text


def test_every_guided_block_the_sheet_lays_out_is_read() -> None:
    """A-D8: a fixed list of fifteen metrics dropped 17 guided blocks across 11 of the 34 non-test
    exports — same-store sales among them. Blocks are found by structure, in sheet order, each
    label once (the listing's repeated per-share block is read at its first); a section header
    is never a block."""
    rows = cs.guidance_bridge_rows(_estimates(), reference_date=gen.G_DATED).value or []
    assert [r.metric for r in rows] == [
        g[0] for g in (*gen.GUIDES, *gen.LISTING_GUIDES, *gen.SECOND_GUIDES)]


def test_a_metric_with_no_decided_direction_shows_its_guide_and_no_record() -> None:
    """NEGATIVE PIN: a discovered metric absent from `_GUIDANCE_HIGHER_IS_DELIVERY` keeps its guide
    and records no MET/MISSED — the direction is decided by name, never guessed — while a
    directed one keeps its record."""
    rows = {r.metric: r for r in cs.guidance_bridge_rows(
        _estimates(), reference_date=gen.G_DATED).value or []}
    sss = rows["Same Store Sales Growth %"]
    assert "Same Store Sales Growth %" not in cs._GUIDANCE_HIGHER_IS_DELIVERY
    assert (sss.latest_guide, sss.period, sss.record, sss.most_recent) == ("3.50", "FQ2 2027",
                                                                           "—", "—")
    assert rows["Revenue"].record == "actual ≥ floor 1/1"


def test_the_revenue_guide_is_still_the_revenue_block() -> None:
    """The guide-verification input reads the 'Revenue' block exactly — a widened set of blocks
    never hands it another metric's numbers."""
    assert cs.revenue_guide_lohi(_estimates(), reference_date=gen.G_DATED) == (
        460.0, 470.0, "FY 2027", gen.G_DATED)


# --- review round 0 (code-review high, 2026-10-29) ----------------------------------------------


def test_an_empty_xlsx_period_type_cell_states_nothing(tmp_path: Path) -> None:
    """openpyxl hands an empty cell back as None, and `period_type` read it as the text 'none' —
    which the mislabel check then took for a period type disagreeing with the filename, refusing
    the name. An empty cell states nothing; the filename stands."""
    sheets = gen._quarterly_sheets("USD")
    for name in ("Income Statement", "Balance Sheet", "Cash Flow"):
        sheets[name][7] = ["", "Period Type:", "", gen.NBSP, "Order:", "Latest on Right"]
    path = tmp_path / XLSX.name
    gen.write_ooxml(path, sheets)
    assert period_type(read_sheets(path)["Income Statement"]) is None
    assert [w.freq for w in _bundle(path).workbooks] == ["quarterly"]


def test_extract_hashes_each_export_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every fact names its export, but the export is hashed once per file version, not once per
    fact (a dozen full reads of a 500 KB workbook on every extract)."""
    for src in (ANNUAL, QUARTERLY):
        shutil.copyfile(src, tmp_path / src.name)
    calls: list[Path] = []
    real = cs.file_provenance
    monkeypatch.setattr(cs, "file_provenance", lambda p: calls.append(p) or real(p))
    got = ciq_balance.extract(_bundle(*tmp_path.iterdir()), gen.TICKER)
    assert {k for k, f in got.facts.items() if f.workbooks} >= {"d_and_a", "net_debt"}
    assert sorted(p.name for p in calls if p.parent == tmp_path) == sorted(
        [ANNUAL.name, QUARTERLY.name] + [QUARTERLY.name])  # the bundle-level stamp, then once each


def test_a_share_class_ticker_spelt_with_a_separator_finds_its_block() -> None:
    """CIQ heads a block 'NYSE:BRK.B' where the fund writes BRK-B: the separator is not part of
    the symbol, so the block is found rather than silently missed."""
    b = _estimates(f"{gen.TICKER}-K")
    assert f"Recommendation: {gen.REC_SECOND} (CIQ score" in (cs.consensus_view(b).value or "")


# --- the stated unit (audit BC-D10) -------------------------------------------------------------

_MILLIONS = "In Millions of the reported currency, except per share items."
_STATEMENTS = ("Income Statement", "Balance Sheet", "Cash Flow")


def _stated_in(sheets: dict[str, Any], unit: str | None) -> dict[str, Any]:
    """The export's statements restated as CIQ would label another unit (None: no unit line)."""
    for name in _STATEMENTS:
        row = sheets[name][6]
        assert row[0] == _MILLIONS
        row[0] = "" if unit is None else _MILLIONS.replace("Millions", unit)
    return sheets


def _pair(tmp_path: Path, annual_unit: str | None, quarterly_unit: str | None) -> CiqBundle:
    for name, sheets, unit in ((ANNUAL.name, gen._annual_sheets("USD"), annual_unit),
                               (QUARTERLY.name, gen._quarterly_sheets("USD"), quarterly_unit)):
        gen.write_biff(tmp_path / name, _stated_in(sheets, unit))
    return _bundle(tmp_path / ANNUAL.name, tmp_path / QUARTERLY.name)


def test_a_whole_export_in_thousands_is_refused(tmp_path: Path) -> None:
    """BC-D10: every figure and the revenue it is measured against in one other unit leaves every
    ratio unchanged, so the magnitude screen passed it. The statements' own unit line says so."""
    got = ciq_balance.extract(_pair(tmp_path, "Thousands", "Thousands"), gen.TICKER)
    assert not got.ok and got.scale_check == CHECK_DIFFER
    assert any(f.startswith("UNIT:") and "Thousands" in f for f in got.failures), got.failures


def test_two_exports_in_different_units_are_refused(tmp_path: Path) -> None:
    """BC-D10: the balance sheet read from the quarterly export, the revenue from the annual one —
    thousands against millions sits inside the magnitude band and passed."""
    got = ciq_balance.extract(_pair(tmp_path, "Thousands", "Millions"), gen.TICKER)
    assert not got.ok and got.scale_check == CHECK_DIFFER
    assert any(f.startswith("UNIT:") for f in got.failures), got.failures


def test_exports_stated_in_millions_pass_and_say_so(bundle: CiqBundle) -> None:
    """NEGATIVE PIN — the shape of all 204 statement sheets in the 34 non-test folders
    (2026-10-29): each states millions, the bridge reads $M, nothing is refused."""
    got = ciq_balance.extract(bundle, gen.TICKER)
    assert got.ok and got.scale_check == CHECK_AGREE
    assert any(c.startswith("unit: every statement read states Millions") for c in got.checks)


def test_an_export_stating_no_unit_is_left_to_the_magnitude_screen(tmp_path: Path) -> None:
    """NEGATIVE PIN: no unit line is not a mismatch — the magnitude screen still runs, and the
    check line says the unit was unstated."""
    got = ciq_balance.extract(_pair(tmp_path, None, None), gen.TICKER)
    assert got.ok and got.scale_check == CHECK_AGREE
    assert any(c.startswith("unit: unstated") for c in got.checks), got.checks


@pytest.mark.parametrize(("annual", "quarterly", "says_dollar_millions"), [
    ("Thousands", "Thousands", False),
    ("Thousands", "Millions", False),
    ("Millions", "Millions", True),       # NEGATIVE PIN: a clean pair still says so
])
def test_a_unit_refusal_never_prints_beside_a_dollar_millions_pass(
        tmp_path: Path, annual: str, quarterly: str, says_dollar_millions: bool) -> None:
    """Review round 1: the magnitude line ("consistent with a $M sheet") printed whenever no SCALE
    failure stood — so a refused Thousands export carried the refusal and a $M pass side by side."""
    got = ciq_balance.extract(_pair(tmp_path, annual, quarterly), gen.TICKER)
    assert any("consistent with a $M sheet" in c for c in got.checks) is says_dollar_millions, \
        got.checks


@pytest.mark.parametrize(("line", "want"), [
    ("In Millions of the reported currency, except per share items.", "Millions"),
    ("In Thousands of US Dollar, except per share items.", "Thousands"),   # a converted export
    ("In Millions of Euro, except per share items.", "Millions"),
    ("Units: S&P Capital IQ (Default)", None),
])
def test_the_unit_line_is_read_whatever_currency_it_names(line: str, want: str | None) -> None:
    """Review round 0: an export converted to a stated currency names that currency, not "the
    reported currency" — its unit must still be read, never fall back to unstated."""
    from vinci.dossier.ciq import stated_unit
    assert stated_unit([[], [line]]) == want
