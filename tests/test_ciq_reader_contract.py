"""THE CIQ READER CONTRACT, ON FILES CI CAN OPEN (audit items H-D2, H-D3).

Every real CIQ export is licensed and git-ignored, so CI had never opened a file in any CIQ format:
on 0fa8ce4a the 480 tests that read one skipped there, and rounding a fractional date serial in
`ciq.excel_date` instead of truncating it left the whole offline suite green. This suite reads the SYNTHETIC exports `tests/fixtures/ciq_synthetic/generate.py` writes for an
invented issuer (ZZFX) — BIFF `.xls`, real RTF and one `.xlsx`, laid out the way the readers address
them — through the real decode path: bytes → `classify` → xlrd / openpyxl / striprtf →
`CiqBundle` → the readers. It never skips; it needs nothing git-ignored.

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
    CiqParseError,
    CiqUnavailableError,
    classify,
    clean_num,
    excel_date,
    is_empty_view,
    period_type,
    read_sheets,
    read_text,
)
from vinci.dossier.schemas import CHECK_AGREE, CHECK_DIFFER, SourceStatus

FIX = gen.HERE
ANNUAL = FIX / gen.ANNUAL_XLS
QUARTERLY = FIX / gen.QUARTERLY_XLS
CUSTOMERS = FIX / gen.CUSTOMERS_RTF
SUPPLIERS = FIX / gen.SUPPLIERS_RTF
XLSX = FIX / gen.QUARTERLY_XLSX
XLS_1904 = FIX / gen.QUARTERLY_1904_XLS
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
            if p.is_file() and "__pycache__" not in p.parts}
    assert held == {*gen.OUTPUTS, "generate.py"}


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


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "A-X1: the filename's `_Quarterly` token outranks the export's own 'Period Type: Annual' "
    "cell, so an annual workbook saved under a quarterly name is served as quarterly"))
def test_a_filename_that_contradicts_the_period_type_cell_is_not_trusted(tmp_path: Path) -> None:
    misnamed = tmp_path / QUARTERLY.name
    shutil.copyfile(ANNUAL, misnamed)
    try:
        got = _bundle(misnamed)
    except RuntimeError:  # refused at construction — one acceptable fix
        return
    assert [w.freq for w in got.workbooks] == ["annual"]


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


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "A-D3: the quarter is read only from a bare 'Q4' token, so CIQ's 'FQ4/CQ2' quarters are "
    "labelled as fiscal years in the quarterly summary"))
def test_fq_cq_quarters_are_not_labelled_as_fiscal_years(bundle: CiqBundle) -> None:
    table = cs.financial_summary_quarterly(bundle).value
    assert table is not None
    assert not [c for c in table.columns if c.startswith("FY")], table.columns


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "A-D3: no quarter token is found in an 'FQ1/CQ3' header, so the same-quarter revenue YoY "
    "is dropped from the multi-year trajectory"))
def test_fq_cq_quarters_still_yield_a_same_quarter_revenue_yoy(bundle: CiqBundle) -> None:
    traj = cs.multi_year_trajectory(bundle).value
    assert traj is not None and "Revenue YoY (latest same-quarter)" in traj, traj


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "A-D11: a lone annual export answers a quarterly request, and the annual Balance Sheet's "
    "serial header is printed raw as the period label"))
def test_a_balance_sheet_period_label_is_never_a_raw_serial() -> None:
    ref = cs.net_debt(_bundle(ANNUAL)).source_ref or ""
    assert not re.search(r"\[\d{5}\.0\]", ref), ref


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "A-D5: the 'latest' column is the rightmost one, and the export's 'Order:' cell is never "
    "read, so a right-to-left sheet serves its OLDEST period as the latest"))
def test_a_right_to_left_sheet_never_serves_its_oldest_period_as_latest() -> None:
    b = _bundle(ANNUAL)
    inc = b.sheet("financials", "Income Statement", freq="annual")
    for r, row in enumerate(inc):
        if len(row) > 1:
            inc[r] = [row[0], *reversed(row[1:])]
    inc[7][5] = "Latest on Left"  # the export's own statement of its column order
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
