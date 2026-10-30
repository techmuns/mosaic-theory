"""ONE LATEST-CELL CONTRACT (audit RC3: A-D5, A-D7, A-D12, D-D2, D-D3; 2026-10-30).

THE DEFECT. `ciq_sheets._latest_col` took the rightmost VALUED cell of a row, so a CIQ marker
('-', 'NA', 'NM', …) in the latest column stepped the read back to an older period with nothing
said, and its order guard decoded only serial headers, so it ran on the annual balance sheet alone.
Live on two committed pages: LLY's press-release LTM cash flow reads 'NA' / '-', so its free cash
flow (1,951.0), its net-debt/OCF (2.7, a Q3 net debt over FY2025 OCF) and its anchor's vendor FCF
(8,972.0) were read off FY Dec-2025; ORKA's interest coverage (−59.5x) was read off FY Dec-2024
because its LTM interest expense reads '-'. Four sibling readers re-implemented the same step-back
(`interest_coverage`'s scan, `ebitda_recon`'s window, `midcycle.multiple_anchor`'s band, and
`ciq_balance`'s revenue, whose fact carried no period).

THE CONTRACT. `ciq_sheets.latest_cell` reads a row's cell at the column whose header states the
LATEST DATE (`header_period`), never a position, and returns (value, column, period, label, state,
reason): a marker there is UNAVAILABLE with a reason, never an older value; a header that dates no
column, or two columns at the latest date, places nothing. The period carries the column's STATUS,
so a press-release column is visible to every caller.

The synthetic exports are FROZEN, so value pins are allowed on them (CLAUDE.md TEST-LAYER RULE):
each test edits a fresh bundle's cells IN MEMORY, the marker taken as the BIFF probe row decodes it.
The corpus checks at the end read the licensed workbooks and skip where they are absent.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_balance, ebitda_recon, midcycle
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.anchor import _bridge_inputs
from vinci.dossier.ciq import CiqBundle, CiqUnavailableError, read_sheets
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import SourceStatus

FIX = gen.HERE
ANNUAL = FIX / gen.ANNUAL_XLS
QUARTERLY = FIX / gen.QUARTERLY_XLS
LTM_LABEL = f"LTM 12 months {gen._mdy(gen.LTM_DATE)}"


@pytest.fixture
def bundle() -> CiqBundle:
    """The two Financials exports, freshly loaded: each test's in-memory edits stay its own."""
    return CiqBundle.from_files(gen.TICKER, sorted([ANNUAL, QUARTERLY]))


def _probe(marker: str) -> Any:
    """The marker AS DECODED from the committed BIFF probe row."""
    inc = read_sheets(QUARTERLY)["Income Statement"]
    ri = cs._find_row(inc, gen.MARKER_ROW)
    assert ri is not None
    return inc[ri][gen.MARKERS.index(marker) + 1]


def _row(rows: list[list[Any]], label: str) -> list[Any]:
    ri = cs._find_row(rows, label)
    assert ri is not None, label
    return rows[ri]


def _sheet(b: CiqBundle, sheet: str, freq: str) -> list[list[Any]]:
    return b.sheet("financials", sheet, freq=freq)


# --- the reader itself ---------------------------------------------------------------------------


def test_the_latest_cell_is_the_latest_dated_column_whatever_its_position() -> None:
    rows = [["For the Fiscal Period Ending", "12 months\nMay-31-2025",
             "LTM\n12 months\nAug-31-2026", "12 months\nMay-31-2026", ""],
            ["EBITDA", 1.0, 3.0, 2.0, ""]]
    got = cs.latest_cell(rows, 1, 0)
    assert (got.state, got.value, got.col, got.label) == (
        "present", 3.0, 2, "LTM 12 months Aug-31-2026")
    assert got.period is not None and got.period.end == date(2026, 8, 31)
    assert got.reason is None


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
def test_a_marker_at_the_latest_column_is_unavailable_never_an_older_value(marker: str) -> None:
    rows = [["For the Fiscal Period Ending", "12 months\nMay-31-2025", "12 months\nMay-31-2026",
             "LTM\n12 months\nAug-31-2026"],
            ["Cash from Ops.", 10.0, 20.0, _probe(marker)]]
    got = cs.latest_cell(rows, 1, 0)
    assert got.state == "unavailable" and got.value is None
    assert got.col == 3 and got.label == "LTM 12 months Aug-31-2026"
    assert got.reason is not None and "[LTM 12 months Aug-31-2026]" in got.reason
    assert "20.0" not in got.reason and "May-31-2026" not in got.reason


def test_the_latest_cell_carries_its_column_status() -> None:
    rows = [["For the Fiscal Period Ending", "12 months\nDec-31-2025",
             "LTM\nPress Release\n12 months\nSep-30-2026"],
            ["Levered Free Cash Flow", 1951.0, 2400.0]]
    got = cs.latest_cell(rows, 1, 0)
    assert got.state == "present" and got.value == 2400.0
    assert got.period is not None and got.period.status == "press_release"
    assert "Press Release" in got.label


def test_two_columns_at_the_latest_date_are_never_guessed_between() -> None:
    rows = [["Balance Sheet as of:", "Jun-30-2026", "Restated Sep-30-2026", "Sep-30-2026"],
            ["Net Debt", 1.0, 2.0, 3.0]]
    got = cs.latest_cell(rows, 1, 0)
    assert got.state == "unplaced" and got.value is None and got.col is None
    assert got.reason is not None and "Sep-30-2026" in got.reason


def test_a_header_that_dates_no_column_places_nothing() -> None:
    rows = [["Fiscal Period", "LTM", "FY2025"], ["EBITDA", 1.0, 2.0]]
    got = cs.latest_cell(rows, 1, 0)
    assert got.state == "unplaced" and got.value is None
    assert cs.latest_cell(rows, 1, None).state == "unplaced"


# --- every reader that took the latest cell, on the synthetic exports -----------------------------


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
@pytest.mark.parametrize(("reader", "label"), [
    (cs.free_cash_flow, "Levered Free Cash Flow"),
    (cs.ltm_ocf, "Cash from Ops."),
], ids=["free_cash_flow", "ltm_ocf"])
def test_a_cash_flow_figure_never_steps_back_past_a_marker(
        bundle: CiqBundle, reader: Any, label: str, marker: str) -> None:
    _row(_sheet(bundle, "Cash Flow", "annual"), label)[-1] = _probe(marker)
    got = reader(bundle)
    assert got.status is SourceStatus.UNKNOWN and got.value is None, got.source_ref
    assert f"[{LTM_LABEL}]" in (got.note or ""), got.note


def test_ltm_ebitda_never_steps_back_past_a_marker(bundle: CiqBundle) -> None:
    _row(_sheet(bundle, "Income Statement", "annual"), "EBITDA")[-1] = _probe("NA")
    got = cs.ltm_ebitda(bundle)
    assert got.status is SourceStatus.UNKNOWN and f"[{LTM_LABEL}]" in (got.note or "")


def test_a_filed_latest_column_still_reads(bundle: CiqBundle) -> None:
    """(+) the fixture as written: every reader lands on the LTM column."""
    fcf = cs.free_cash_flow(bundle)
    assert fcf.status is SourceStatus.PRESENT and f"[{LTM_LABEL}]" in (fcf.source_ref or "")
    assert cs.ltm_ocf(bundle).value == gen._annual((38.4, 44.0, 47.9), gen.Q_CFO)[-1]
    nd = cs.net_debt(bundle)
    assert nd.value == round(gen.Q_DEBT[-1] - gen.Q_CASH[-1], 1)


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
def test_a_balance_sheet_line_never_steps_back_or_falls_to_an_older_sheet(
        bundle: CiqBundle, marker: str) -> None:
    """The quarterly sheet carries the row, so the annual sheet (latest May-31-2026, a quarter
    older) never answers for it."""
    _row(_sheet(bundle, "Balance Sheet", "quarterly"), "Net Debt")[-1] = _probe(marker)
    got = cs.net_debt(bundle)
    assert got.status is SourceStatus.UNKNOWN and got.value is None, got.source_ref
    assert gen._mdy(gen.Q_DATES[-1]) in (got.note or ""), got.note


def test_interest_coverage_reads_both_legs_at_the_latest_column(bundle: CiqBundle) -> None:
    """ORKA's shape: EBITDA at the LTM column, interest expense '-' there and valued a year back."""
    inc = _sheet(bundle, "Income Statement", "annual")
    inc.append(["Interest Expense", -2.0, -2.1, -2.2, -2.3, -2.4, "-"])
    got = cs.interest_coverage(bundle)
    assert got.status is SourceStatus.UNKNOWN and got.value is None, got.source_ref
    assert f"[{LTM_LABEL}]" in (got.note or "") and "Interest Expense" in (got.note or "")
    inc[-1][-1] = -2.5   # (+) both legs at the LTM column
    ok = cs.interest_coverage(bundle)
    assert ok.status is SourceStatus.PRESENT and f"[{LTM_LABEL}]" in (ok.source_ref or "")
    assert ok.value == round(gen._annual((51.8, 56.3, 60.9), gen.Q_EBITDA)[-1] / 2.5, 1)


def test_the_posture_never_anchors_on_an_older_cash_column(bundle: CiqBundle) -> None:
    _row(_sheet(bundle, "Balance Sheet", "quarterly"), "Total Cash & ST Investments")[-1] = "NA"
    got = cs.balance_sheet_posture(bundle)
    assert got.status is SourceStatus.UNKNOWN and got.value is None, got.value
    assert gen._mdy(gen.Q_DATES[-1]) in (got.note or ""), got.note


def test_book_value_per_share_never_steps_back(bundle: CiqBundle) -> None:
    _sheet(bundle, "Balance Sheet", "annual").append(
        ["Book Value/Share", 4.1, 4.3, 4.6, 4.8, "NA"])
    got = cs.book_value_per_share(bundle)
    assert got.status is SourceStatus.UNKNOWN and got.value is None, got.source_ref
    assert gen._mdy(gen.A_DATES[-1]) in (got.note or ""), got.note


def _with_ratios(b: CiqBundle, rows: list[list[Any]]) -> CiqBundle:
    _sheet(b, "Income Statement", "annual")   # loads the annual export into the bundle's cache
    wb = b.workbook("financials", freq="annual")
    assert wb is not None
    b._cache[wb.path]["Ratios"] = rows
    return b


def test_key_ratios_pin_the_latest_column_and_never_step_back(bundle: CiqBundle) -> None:
    head = ["For the Fiscal Period Ending", "12 months\nMay-31-2026", f"LTM\n12 months\n"
            f"{gen._mdy(gen.LTM_DATE)}"]
    _with_ratios(bundle, [head, ["Return on Equity %", 0.12, "NM"], ["Current Ratio", 1.4, "NA"]])
    got = cs.key_ratios(bundle)
    assert got.status is SourceStatus.UNKNOWN and got.value is None, got.value
    assert f"[{LTM_LABEL}]" in (got.note or ""), got.note
    # (+) one ratio at the latest column pins it; the other is named, never back-filled
    bundle2 = CiqBundle.from_files(gen.TICKER, sorted([ANNUAL, QUARTERLY]))
    _with_ratios(bundle2, [head, ["Return on Equity %", 0.12, 0.15],
                           ["Current Ratio", 1.4, "NA"]])
    ok = cs.key_ratios(bundle2)
    assert ok.status is SourceStatus.PRESENT and "RoE 15.0%" in (ok.value or "")
    assert "not reported this period: current ratio" in (ok.value or "")


def test_quarterly_revenue_yoy_never_steps_back_a_quarter(bundle: CiqBundle) -> None:
    assert cs._quarterly_revenue_yoy(bundle) is not None   # (+) as written
    _row(_sheet(bundle, "Income Statement", "quarterly"), "Total Revenue")[-1] = "NA"
    assert cs._quarterly_revenue_yoy(bundle) is None


# --- the anchor's CIQ bridge (decision path) ----------------------------------------------------


def test_the_bridge_revenue_fact_states_its_period(bundle: CiqBundle) -> None:
    """A-D7: the scale reference is the annual sheet's LTM column, and its fact says so."""
    rev = ciq_balance.extract(bundle, gen.TICKER).facts["revenue"]
    assert (rev.period, rev.period_end) == ("LTM", gen.LTM_DATE)
    assert "latest full year" not in rev.basis


@pytest.mark.parametrize("marker", gen.MARKERS, ids=lambda m: repr(m))
def test_the_bridge_never_pairs_an_older_ocf_and_capex(bundle: CiqBundle, marker: str) -> None:
    """LLY's shape: OCF and capex '-' at the press-release LTM column, valued at the fiscal year
    before it — the anchor's vendor FCF must be unavailable with the reason, never FY's figure."""
    cf = _sheet(bundle, "Cash Flow", "annual")
    _row(cf, "Cash from Ops.")[-1] = _probe(marker)
    _row(cf, "Capital Expenditure")[-1] = _probe(marker)
    ciq = ciq_balance.extract(bundle, gen.TICKER)
    assert "ocf" not in ciq.facts and "capex" not in ciq.facts
    assert f"[{LTM_LABEL}]" in ciq.unavailable["ocf"]
    bridge = _bridge_inputs({}, {}, ciq)
    fcf = bridge["ltm_fcf"]
    assert fcf.value is None and "ltm_fcf" not in bridge["vendor_filled"]
    assert f"[{LTM_LABEL}]" in fcf.source, fcf.source


def test_the_bridge_fills_fcf_from_a_filed_latest_column(bundle: CiqBundle) -> None:
    """(+) the fixture as written: OCF and capex at the LTM column fill the hole, one period."""
    bridge = _bridge_inputs({}, {}, ciq_balance.extract(bundle, gen.TICKER))
    cfo = gen._annual((38.4, 44.0, 47.9), gen.Q_CFO)[-1]
    assert bridge["ltm_fcf"].value == round(cfo - abs(gen.A_CAPEX[-1]), 3)
    assert "ltm_fcf" in bridge["vendor_filled"]


# --- the two sibling readers: EBITDA reconciliation and the multiple band -------------------------


def test_the_ebitda_reconciliation_never_shifts_its_window(bundle: CiqBundle) -> None:
    """D-D2: an unavailable latest quarter refuses the block — the four quarters before it are not
    CIQ's LTM, and a reconciliation of them would be stamped as if they were."""
    rec = ebitda_recon.reconcile(bundle, {}, [], lambda _r: None)
    assert rec is not None and rec.quarters[-1].period_end == gen.Q_DATES[-1].isoformat()
    _row(_sheet(bundle, "Income Statement", "quarterly"), "EBITDA")[-1] = "NA"
    assert ebitda_recon.reconcile(bundle, {}, [], lambda _r: None) is None


def _tev_close(b: CiqBundle) -> list[Any]:
    rows = _sheet(b, "Multiples", "quarterly")
    lbl = cs._find_row(rows, "TEV/LTM EBITDA")
    assert lbl is not None
    return next(rows[i] for i in range(lbl, lbl + 6) if str(rows[i][1]).strip() == "Close")


def test_the_multiple_band_is_unavailable_when_the_latest_close_is_nm(bundle: CiqBundle) -> None:
    """D-D3: as `_own_history_band` already refuses — a band built on the closes before an NM one
    would carry no date to reveal it."""
    assert midcycle.multiple_anchor(bundle).available   # (+) as written
    _tev_close(bundle)[-1] = "NM"
    got = midcycle.multiple_anchor(bundle)
    assert not got.available
    assert gen.M_DATES[-1].isoformat() in got.note and "NM" in got.note


# --- a press-release balance sheet or cash flow: the ruling owed, as one line ---------------------


def test_a_press_release_balance_sheet_is_served_with_its_state_shown(
        bundle: CiqBundle, monkeypatch: pytest.MonkeyPatch) -> None:
    """`PRESS_RELEASE_REFUSED` holds the Income Statement alone (#868's ruling): a release column on
    the balance sheet is SERVED, and every reader names it. Naming the Balance Sheet there — the
    one-line change the operator's ruling would make — refuses the same bundle at assembly."""
    bs = _sheet(bundle, "Balance Sheet", "quarterly")
    hdr = cs._bs_period_header(bs)
    assert hdr is not None
    bs[hdr][-1] = f"Press Release\n{bs[hdr][-1]}"
    assert cs.press_release_income_columns(bundle) == []
    cs.require_filed_income_statement(bundle, gen.TICKER)   # served: no refusal
    nd = cs.net_debt(bundle)
    assert nd.status is SourceStatus.PRESENT and "[Press Release " in (nd.source_ref or "")
    assert "(press release)" in str(cs.balance_sheet_posture(bundle).value)
    every = ("Income Statement", "Balance Sheet", "Cash Flow")
    found = cs.press_release_income_columns(bundle, every)
    assert [(c.sheet, c.export, c.period.end) for c in found] == [
        ("Balance Sheet", "quarterly", gen.Q_DATES[-1])]
    monkeypatch.setattr(cs, "PRESS_RELEASE_REFUSED", every)
    with pytest.raises(cs.CiqPreliminaryError, match="quarterly export Balance Sheet"):
        cs.require_filed_income_statement(bundle, gen.TICKER)


# --- the corpus (licensed workbooks; skipped where absent) --------------------------------------


def _bundles() -> list[tuple[str, CiqBundle]]:
    root = get_config().data_dir / "manual" / "ciq"
    if not root.is_dir() or not any(root.iterdir()):
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    ms = LocalFolderStore(root)
    return [(tk, CiqBundle.from_files(tk, files))
            for tk in sorted(p.name for p in root.iterdir() if p.is_dir())
            if (files := ms.files(tk))]


def _latest_label(rows: list[list[Any]], hdr: int | None) -> str | None:
    if hdr is None:
        return None
    dated = [(d, j) for j in range(1, len(rows[hdr]))
             if (d := cs._column_date(rows[hdr][j])) is not None]
    return cs._period_text(rows[hdr][max(dated)[1]]) if dated else None


_READS: tuple[tuple[str, Any, str, str], ...] = (
    ("free_cash_flow", cs.free_cash_flow, "Cash Flow", "annual"),
    ("ltm_ocf", cs.ltm_ocf, "Cash Flow", "annual"),
    ("ltm_ebitda", cs.ltm_ebitda, "Income Statement", "annual"),
    ("interest_coverage", cs.interest_coverage, "Income Statement", "annual"),
)


def test_no_reader_serves_a_period_older_than_its_sheets_latest_column() -> None:
    """THE PROPERTY, over every bundle on file: a PRESENT figure names its sheet's latest dated
    column. On main 9503c4fa it failed on FUBO and LLY (free cash flow, FY behind a 'NA' LTM), LLY
    (OCF) and ORKA (interest coverage, FY Dec-2024 behind a '-' LTM)."""
    checked, older = 0, []
    for tk, b in _bundles():
        for name, reader, sheet, freq in _READS:
            try:
                rows = b.sheet("financials", sheet, freq=freq)
            except CiqUnavailableError:
                continue
            want = _latest_label(rows, cs._period_header(rows))
            got = reader(b)
            if want is None or got.status is not SourceStatus.PRESENT:
                continue
            checked += 1
            if f"[{want}]" not in (got.source_ref or ""):
                older.append(f"{tk} {name}: {got.source_ref!r}, latest column [{want}]")
    assert checked, "no reader produced a figure — the property never ran"
    assert older == []


def test_the_bridge_never_pairs_a_period_older_than_the_latest_column() -> None:
    """The anchor's vendor OCF and capex, over every bundle on file: each fact's period is its
    sheet's latest LTM or fiscal-year column, or the fact is absent with a reason."""
    checked, older = 0, []
    for tk, b in _bundles():
        try:
            cf = b.sheet("financials", "Cash Flow", freq="annual")
        except CiqUnavailableError:
            continue
        hdr = cs._period_header(cf)
        want = _latest_label(cf, hdr)
        if want is None or hdr is None:
            continue
        latest = max(d for c in cf[hdr][1:] if (d := cs._column_date(c)) is not None)
        try:
            ciq = ciq_balance.extract(b, tk)
        except Exception:  # noqa: BLE001 — an export the bridge cannot read is not this check's
            continue
        for key in ("ocf", "capex"):
            checked += 1
            fact = ciq.facts.get(key)
            if fact is None:
                assert ciq.unavailable.get(key), f"{tk} {key}: absent and no reason given"
            elif fact.period_end != latest:
                older.append(f"{tk} {key}: {fact.period} {fact.period_end}, latest {want}")
    assert checked, "no bundle carried an annual cash flow — the property never ran"
    assert older == []


def test_corpus_markers_are_said_where_they_used_to_step_back() -> None:
    """CORPUS BEFORE SYNTHETIC: the readers above, on the files they failed on — wherever the
    latest column's cell IS a marker, the figure is UNKNOWN and says so. A name absent from this
    checkout's copy, or re-exported with the column filled, is skipped, never assumed."""
    by = dict(_bundles())
    seen = 0
    for tk, reader, sheet, label in (
            ("LLY", cs.free_cash_flow, "Cash Flow", "Levered Free Cash Flow"),
            ("LLY", cs.ltm_ocf, "Cash Flow", "Cash from Ops."),
            ("FUBO", cs.free_cash_flow, "Cash Flow", "Levered Free Cash Flow"),
            ("ORKA", cs.interest_coverage, "Income Statement", "Interest Expense")):
        if tk not in by:
            continue
        rows = by[tk].sheet("financials", sheet, freq="annual")
        cell = cs.latest_cell(rows, cs._find_row(rows, label) or 0, cs._period_header(rows))
        if cell.state != "unavailable":
            continue
        seen += 1
        got = reader(by[tk])
        assert got.status is SourceStatus.UNKNOWN, (tk, label, got.source_ref)
        assert f"at the latest column [{cell.label}]" in (got.note or ""), (tk, got.note)
    if not seen:
        pytest.skip("no name on file still carries a marker at its latest column")
