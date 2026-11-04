"""A FISCAL-YEAR CHANGE IS NO COLUMN (2026-11-04).

THE DEFECT. SMPL's 2026-11-04 CIQ Financials export reaches back to 2015, past its 2016–17
fiscal-year change, so every period header carries an undated 'Fiscal\\nYear\\nChange' column
between the old calendar (the Conyers Park SPAC's December periods) and the new one (the Atkins
predecessor's August years, then SMPL's own). `ciq_sheets.latest_cell` (PR #872 round 2) refuses
any undated header cell, so every latest read on the page came back "unplaced": net debt, total
debt, LTM EBITDA and OCF, free cash flow, interest coverage, the balance-sheet posture, book value
per share, the key ratios, segments, geography — and the EV bridge, which said nothing at all. The
Capital Structure Summary refused on order, since the old calendar sits out of date order with the
new. The summary tables printed the marker as a column labelled 'Fiscal Y'.

THE CONTRACT. `ciq_sheets.PERIOD_HEADER_MARKERS` is a CLOSED registry of known non-period header
cells, matched whitespace-normalised and exactly. A registered cell is no column to any reader that
walks a header; any other undated cell still places nothing (#872's 'Jun-30-2026A' protection).
The marker's break survives it: no growth, step or order check spans the two calendars. A page
with no EV bridge carries why (`ev_bridge_unbuilt`).

THE HEADER CELLS BELOW ARE SMPL'S, VERBATIM — period labels only (layout vocabulary and public
fiscal period ends); every value is invented. The corpus checks at the end read the licensed
workbooks and skip where they are absent.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_balance
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
from vinci.dossier.propose import ProposalRefusedError, r4_bridge_fact
from vinci.dossier.schemas import EvBridge, EvBridgeUnbuilt, SourceStatus
from vinci.dossier.valuation_basis import RECIPE_R4, derive
from vinci.quality.sources.ciq import _ev_bridge_vs_ciq_tev

MARKER = "Fiscal\nYear\nChange"

#: SMPL's annual Income Statement period header, 2026-11-04 export — all 14 period cells.
SMPL_ANNUAL_IS = [
    "For the Fiscal Period Ending\n", "12 months\nDec-31-2016", MARKER, "12 months\nAug-29-2015",
    "Reclassified\n12 months\nAug-27-2016", "Reclassified\n12 months\nAug-26-2017",
    "Restated\n12 months\nAug-25-2018", "Restated\n12 months\nAug-31-2019",
    "Restated\n12 months\nAug-29-2020", "Reclassified\n12 months\nAug-28-2021",
    "Reclassified\n12 months\nAug-27-2022", "Reclassified\n12 months\nAug-26-2023",
    "Reclassified\n12 months\nAug-31-2024", "12 months\nAug-30-2025", "12 months\nAug-29-2026"]
#: Its annual Balance Sheet header: date serials and labelled dates, the marker among them.
SMPL_ANNUAL_BS = [
    "Balance Sheet as of:\n", 42735.0, MARKER, 42245.0, 42609.0, 42973.0,
    "Reclassified\nAug-25-2018", "Restated\nAug-31-2019", "Restated\nAug-29-2020", 44436.0,
    44800.0, 45164.0, 45535.0, 45899.0, 46263.0]
#: Its quarterly Income Statement header: the first eight period cells and the last three of 44.
SMPL_QUARTERLY_IS = [
    "For the Fiscal Period Ending\n", "3 months\nQ3\nSep-30-2016", "3 months\nQ4\nDec-31-2016",
    "3 months\nQ1\nMar-31-2017", MARKER, "3 months\nFQ1/CQ4\nNov-26-2016",
    "3 months\nFQ2/CQ1\nFeb-25-2017", "3 months\nFQ3/CQ2\nMay-27-2017",
    "3 months\nFQ4/CQ3\nAug-26-2017", "3 months\nFQ2/CQ1\nFeb-28-2026",
    "3 months\nFQ3/CQ2\nMay-30-2026", "3 months\nFQ4/CQ3\nAug-29-2026"]
#: Its annual Capital Structure Summary header — all 29 cells, each period an amount + share pair.
SMPL_ANNUAL_CS = [
    " For the Fiscal Period Ending\n", " 12 months Dec-31-2016", "", " Fiscal Year Change", "",
    *[c for d in ("Aug-29-2015", "Aug-27-2016", "Aug-26-2017", "Aug-25-2018", "Aug-31-2019",
                  "Aug-29-2020", "Aug-28-2021", "Aug-27-2022", "Aug-26-2023", "Aug-31-2024",
                  "Aug-30-2025", "Aug-29-2026") for c in (f" 12 months {d}", "")]]


def _row(header: list[Any]) -> list[list[Any]]:
    """The header over one invented row: the marker column reads 'FYC', as SMPL's rows do."""
    return [header, ["EBITDA", *["FYC" if cs.is_period_marker(c) else float(j)
                                 for j, c in enumerate(header[1:], 1)]]]


# --- the reader, on SMPL's real header shapes ----------------------------------------------------


@pytest.mark.parametrize(("header", "label"), [
    (SMPL_ANNUAL_IS, "12 months Aug-29-2026"),
    (SMPL_ANNUAL_BS, "Aug-29-2026"),
    (SMPL_QUARTERLY_IS, "3 months FQ4/CQ3 Aug-29-2026"),
], ids=["annual-income", "annual-balance", "quarterly-income"])
def test_smpls_header_places_its_latest_column(header: list[Any], label: str) -> None:
    """POSITIVE, on SMPL's header cells: the marker is skipped, the latest column is the one that
    states the latest date — not the old calendar's Dec-31-2016 sitting first. On main cfedcb39
    every one of these was "unplaced"."""
    got = cs.latest_cell(_row(header), 1, 0)
    assert (got.state, got.col, got.label) == ("present", len(header) - 1, label), got.reason
    assert got.value == float(len(header) - 1)


@pytest.mark.parametrize("cell", [
    "Fiscal Period Change", "Fiscal Year Changed", "fiscal year change", "FYC", "Transition Period",
])
def test_an_unregistered_undated_cell_still_places_nothing(cell: str) -> None:
    """NEGATIVE: the registry is closed and exact — a near miss, a case change, the 'FYC' a data
    cell carries, or any other undated label still refuses, naming the cell."""
    header = [c if c != MARKER else cell for c in SMPL_ANNUAL_IS]
    got = cs.latest_cell(_row(header), 1, 0)
    assert got.state == "unplaced" and got.value is None and got.col is None
    assert got.reason is not None and repr(cell) in got.reason


def test_a_marker_never_hides_a_suffixed_newest_column() -> None:
    """#872's step-back stays closed beside a marker: the suffixed newest column is still named,
    and the marker is not."""
    header = [*SMPL_ANNUAL_IS[:-1], "12 months\nAug-29-2026A"]
    got = cs.latest_cell(_row(header), 1, 0)
    assert got.state == "unplaced" and got.reason is not None
    assert "'12 months Aug-29-2026A'" in got.reason and "Fiscal" not in got.reason


def test_the_registry_holds_the_one_shape_the_corpus_carries() -> None:
    """A new marker enters by a reviewed edit to the registry, never by a pattern: this pin moves
    with it. Both spellings CIQ writes are the one entry."""
    assert frozenset({"Fiscal Year Change"}) == cs.PERIOD_HEADER_MARKERS
    assert cs.is_period_marker(MARKER) and cs.is_period_marker(" Fiscal Year Change")
    assert not cs.is_period_marker(None) and not cs.is_period_marker(42735.0)
    assert cs.calendar_segments(SMPL_QUARTERLY_IS) == [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]
    assert cs.calendar_segments(["x", "12 months\nAug-29-2026"]) == [0, 0]


def test_the_marker_is_no_period_column() -> None:
    periods = cs._fin_periods(SMPL_ANNUAL_IS)
    assert len(periods) == len(SMPL_ANNUAL_IS) - 2  # the label cell and the marker
    assert 2 not in [c for c, _s, _l, _r in periods]
    assert not any("Fiscal" in s for _c, s, _l, _r in periods)


# --- the frozen synthetic bundle, with SMPL's shape written into it -------------------------------

#: The old calendar's column for each statement header, CIQ's way: dated AFTER the new calendar's
#: first column (as SMPL's Dec-31-2016 is after Aug-29-2015) and printed before the marker.
_OLD_ANNUAL = "Reclassified\n12 months\nDec-31-2022"
_OLD_QUARTER = "3 months\nQ4\nDec-31-2024"


def _old_column(sheet: str, freq: str) -> Any:
    if sheet == "Balance Sheet":
        return (float((date(2022, 12, 31) - date(1899, 12, 30)).days) if freq == "annual"
                else "Q4\nDec-31-2024")
    return _OLD_ANNUAL if freq == "annual" else _OLD_QUARTER


def _with_old_calendar(b: CiqBundle, marker: str = MARKER) -> CiqBundle:
    """Every statement of both exports, in memory, as SMPL's reads: an old-calendar column and the
    marker inserted before the first period column. The old column's figures are invented and
    nonzero; the marker column reads 'FYC' on every row."""
    for freq in ("annual", "quarterly"):
        for sheet in ("Income Statement", "Balance Sheet", "Cash Flow"):
            rows = b.sheet("financials", sheet, freq=freq)
            hdr = (cs._bs_period_header(rows) if sheet == "Balance Sheet"
                   else cs._period_header(rows))
            assert hdr is not None, (freq, sheet)
            for r in range(hdr, len(rows)):
                if len(rows[r]) < 2:
                    continue
                old = (_old_column(sheet, freq) if r == hdr
                       else rows[r][1] if isinstance(rows[r][1], str) else 50.0)
                rows[r][1:1] = [old, marker if r == hdr else "FYC"]
    return b


@pytest.fixture
def bundle() -> CiqBundle:
    return CiqBundle.from_files(gen.TICKER, sorted([gen.HERE / gen.ANNUAL_XLS,
                                                    gen.HERE / gen.QUARTERLY_XLS]))


_LATEST_READERS: tuple[tuple[str, Any], ...] = (
    ("net_debt", cs.net_debt), ("total_debt", cs.total_debt), ("ltm_ebitda", cs.ltm_ebitda),
    ("ltm_ocf", cs.ltm_ocf), ("free_cash_flow", cs.free_cash_flow),
    ("balance_sheet_posture", cs.balance_sheet_posture),
    ("ev_bridge", lambda b: cs.ev_bridge(b, fy_periods=["FY27"])),
    ("ciq_balance", lambda b: ciq_balance.extract(b, gen.TICKER)),
)


def test_an_old_calendar_and_its_marker_move_no_latest_read_e2e(bundle: CiqBundle) -> None:
    """END TO END through the BIFF exports: with SMPL's shape written into every statement, each
    latest read is exactly what the export without it reads — present, same value, same period."""
    plain = CiqBundle.from_files(gen.TICKER, sorted([gen.HERE / gen.ANNUAL_XLS,
                                                     gen.HERE / gen.QUARTERLY_XLS]))
    edited = _with_old_calendar(bundle)
    for name, read in _LATEST_READERS:
        want, got = read(plain), read(edited)
        assert getattr(want, "status", SourceStatus.PRESENT) is SourceStatus.PRESENT, name
        assert not isinstance(want, EvBridgeUnbuilt), name
        assert got == want, name


def test_an_unregistered_marker_in_the_same_place_still_refuses_e2e(bundle: CiqBundle) -> None:
    """NEGATIVE, end to end: the same shape under a label the registry does not hold reads nothing
    as the latest, and says which cell it would not guess past."""
    edited = _with_old_calendar(bundle, marker="Fiscal\nPeriod\nChange")
    for name, read in _LATEST_READERS[:5]:
        got = read(edited)
        assert got.status is SourceStatus.UNKNOWN, name
        assert "'Fiscal Period Change'" in (got.note or ""), (name, got.note)
    bridge = cs.ev_bridge(edited, fy_periods=["FY27"])
    assert isinstance(bridge, EvBridgeUnbuilt) and "'Fiscal Period Change'" in bridge.reason


def test_the_summary_tables_carry_no_marker_column_e2e(bundle: CiqBundle) -> None:
    plain = CiqBundle.from_files(gen.TICKER, sorted([gen.HERE / gen.ANNUAL_XLS,
                                                     gen.HERE / gen.QUARTERLY_XLS]))
    edited = _with_old_calendar(bundle)
    for read in (cs.financial_summary_annual, cs.financial_summary_quarterly):
        want, got = read(plain).value, read(edited).value
        assert want is not None and got is not None
        # one more column: the old calendar's, never the marker
        assert len(got.columns) == len(want.columns) + 1
        assert not any("Fiscal" in c for c in got.columns), got.columns
        assert got.columns[1:] == want.columns


def _growth(table: Any, label: str) -> list[str]:
    return next(r.cells for r in table.rows if r.label == label)


def test_no_growth_spans_the_fiscal_year_change_e2e(bundle: CiqBundle) -> None:
    """The column goes, its break stays. Both sides of the change are on one basis here (the old
    year is Reclassified as the new calendar's first is; both quarters are filed), so only the
    calendar breaks the comparison. NEGATIVE: the same old column with no marker beside it is one
    calendar, and its growth is computed — which is what the marker stops."""
    edited = _with_old_calendar(bundle)
    ann = cs.financial_summary_annual(edited).value
    qtr = cs.financial_summary_quarterly(edited).value
    assert ann is not None and qtr is not None
    assert _growth(ann, "Revenue growth")[1] == "— (basis)"
    assert _growth(qtr, "Revenue QoQ")[1] == "— (basis)"

    one_calendar = CiqBundle.from_files(gen.TICKER, sorted([gen.HERE / gen.ANNUAL_XLS,
                                                            gen.HERE / gen.QUARTERLY_XLS]))
    for freq in ("annual", "quarterly"):
        rows = one_calendar.sheet("financials", "Income Statement", freq=freq)
        hdr = cs._period_header(rows)
        assert hdr is not None
        for r in range(hdr, len(rows)):
            if len(rows[r]) >= 2:
                rows[r].insert(1, _old_column("Income Statement", freq) if r == hdr
                               else rows[r][1] if isinstance(rows[r][1], str) else 50.0)
    ann1 = cs.financial_summary_annual(one_calendar).value
    qtr1 = cs.financial_summary_quarterly(one_calendar).value
    assert ann1 is not None and qtr1 is not None
    assert _growth(ann1, "Revenue growth")[1].endswith("%")
    assert _growth(qtr1, "Revenue QoQ")[1].endswith("%")


class _QStub:
    """A quarterly Income Statement: the header given over one revenue row."""

    def __init__(self, header: list[Any], revenue: list[Any]) -> None:
        self.rows = [header, ["Total Revenue", *revenue]]

    def sheet(self, kind: str, name: str, *, freq: str | None = None) -> list[list[Any]]:
        return self.rows


def test_the_latest_same_quarter_yoy_never_spans_the_change() -> None:
    """The old calendar's Q2 (fiscal 2025) is the one column naming the latest quarter's number a
    fiscal year earlier, so the year-on-year read reached across the change to it. NEGATIVE: the
    same columns with no marker are one calendar, and the comparison is made."""
    header = ["For the Fiscal Period Ending\n", "3 months\nQ2\nJun-30-2025", MARKER,
              "3 months\nFQ1/CQ4\nNov-29-2025", "3 months\nFQ2/CQ1\nFeb-28-2026"]
    got = cs._quarterly_revenue_yoy(_QStub(header, [100.0, "FYC", 110.0, 120.0]))  # type: ignore[arg-type]
    assert got is None, got
    one_calendar = [c for c in header if c != MARKER]
    got1 = cs._quarterly_revenue_yoy(_QStub(one_calendar, [100.0, 110.0, 120.0]))  # type: ignore[arg-type]
    assert got1 is not None and got1.startswith("+20.0%"), got1


def test_an_old_calendar_namesake_is_no_second_candidate_for_the_yoy() -> None:
    """SMPL's shape: the old calendar's 'Q1 Mar-31-2017' and the new calendar's 'FQ1/CQ4
    Nov-26-2016' both read Q1 FY2017, so a latest FQ1 FY2018 saw two candidates a fiscal year
    earlier and read nothing. The old-calendar column is never comparable, so it is no candidate:
    the in-calendar FQ1 is the one comparison."""
    header = ["For the Fiscal Period Ending\n", "3 months\nQ1\nMar-31-2017", MARKER,
              "3 months\nFQ1/CQ4\nNov-26-2016", "3 months\nFQ1/CQ4\nNov-25-2017"]
    got = cs._quarterly_revenue_yoy(_QStub(header, [500.0, "FYC", 100.0, 125.0]))  # type: ignore[arg-type]
    assert got is not None and got.startswith("+25.0%"), got


# --- the Capital Structure Summary's order check -------------------------------------------------


class _CsStub:
    """A Capital Structure Summary sheet: the header given, then term loans and total debt."""

    def __init__(self, header: list[str], loans: list[float]) -> None:
        cells: list[Any] = []
        for c in header[1:]:
            cells.append(("FYC" if cs.is_period_marker(c) else loans.pop(0)) if c.strip() else "")
        self.rows = [header, ["Total Term Loans", *cells], ["Total Debt Outstanding", *cells]]

    def sheet(self, kind: str, name: str, *, freq: str | None = None) -> list[list[Any]]:
        return self.rows


def test_smpls_capital_structure_summary_reads_its_latest_calendar() -> None:
    """POSITIVE, on SMPL's header: refused on main cfedcb39 ("NOT in ascending date order"), since
    the old calendar's Dec-31-2016 precedes Aug-29-2015. Read within the new calendar, the last
    column is the latest and the step's other end is the year before it."""
    got = cs._capital_summary(_CsStub(SMPL_ANNUAL_CS, [float(i) for i in range(1, 14)]))  # type: ignore[arg-type]
    assert got.status is SourceStatus.PRESENT, got.note
    assert "(12 months Aug-30-2025 12.0 → 12 months Aug-29-2026 13.0)" in str(got.value)


def test_a_step_never_crosses_the_change() -> None:
    header = [" For the Fiscal Period Ending\n", " 12 months Dec-31-2016", "",
              " Fiscal Year Change", "", " 12 months Aug-29-2026", ""]
    got = cs._capital_summary(_CsStub(header, [1.0, 2.0]))  # type: ignore[arg-type]
    assert got.status is SourceStatus.PRESENT, got.note
    assert "term loans 2.0;" in str(got.value) and "→" not in str(got.value)


def test_the_capital_structure_summary_still_refuses_what_it_refused() -> None:
    """NEGATIVE ×3. Out of order within the latest calendar; an old calendar stating a LATER date
    than the last column (the guarantee the whole-row check gave); and SMPL's shape with an
    unregistered label in the marker's place, which is one calendar and out of order."""
    descending = [*SMPL_ANNUAL_CS[:5], " 12 months Aug-29-2026", "", " 12 months Aug-30-2025", ""]
    later_old = [" For the Fiscal Period Ending\n", " 12 months Dec-31-2027", "",
                 " Fiscal Year Change", "", " 12 months Aug-30-2025", "",
                 " 12 months Aug-29-2026", ""]
    unregistered = [c if c != " Fiscal Year Change" else " Fiscal Period Change"
                    for c in SMPL_ANNUAL_CS]
    for header, why in ((descending, "NOT in ascending date order"),
                        (later_old, "a column before the fiscal-year change states a later date"),
                        (unregistered, "NOT in ascending date order")):
        n = sum(1 for c in header[1:] if c.strip() and not cs.is_period_marker(c))
        got = cs._capital_summary(_CsStub(header, [float(i) for i in range(1, n + 1)]))  # type: ignore[arg-type]
        assert got.status is SourceStatus.UNKNOWN and why in (got.note or ""), (header, got.note)


# --- the EV bridge says why it is unbuilt ---------------------------------------------------------


def _q_balance(b: CiqBundle) -> list[list[Any]]:
    return b.sheet("financials", "Balance Sheet", freq="quarterly")


def _set_latest(b: CiqBundle, label: str, value: Any) -> None:
    rows = _q_balance(b)
    ri = cs._find_row(rows, label)
    assert ri is not None
    rows[ri][-1] = value


LATEST_Q = f"FQ1/CQ3 {gen._mdy(gen.Q_DATES[-1])}"


@pytest.mark.parametrize(("edit", "why"), [
    (lambda b: _set_latest(b, "Net Debt", "NA"),
     f"'Net Debt' reads 'NA' at the latest column [{LATEST_Q}]"),
    (lambda b: _set_latest(b, "Total Debt", "-"),
     f"states no 'Total Debt' at its latest column [{LATEST_Q}]"),
    (lambda b: _set_latest(b, "Total Cash & ST Investments", ""),
     f"states no 'Total Cash & ST Investments' at its latest column [{LATEST_Q}]"),
    (lambda b: _q_balance(b).__setitem__(cs._find_row(_q_balance(b), "Net Debt") or 0, ["Netdebt"]),
     "carries no 'Net Debt' row"),
], ids=["net-debt-marker", "total-debt-marker", "cash-blank", "no-net-debt-row"])
def test_an_unbuilt_bridge_says_why(bundle: CiqBundle, edit: Any, why: str) -> None:
    edit(bundle)
    got = cs.ev_bridge(bundle, fy_periods=["FY27"])
    assert isinstance(got, EvBridgeUnbuilt), got
    assert why in got.reason, got.reason
    assert got.source_file == Path(gen.QUARTERLY_XLS).name


def test_a_page_carries_the_bridge_or_why_never_both() -> None:
    from vinci.dossier.schemas import Dossier, dossier_json

    page = Path(__file__).resolve().parents[1] / "data" / "dossiers" / "AMZN" / "dossier.json"
    doc = Dossier.model_validate_json(page.read_text())
    assert doc.ev_bridge is not None and "ev_bridge_unbuilt" not in json.loads(dossier_json(doc))
    reason = EvBridgeUnbuilt(reason="the quarterly Balance Sheet carries no 'Net Debt' row")
    unbuilt = doc.model_copy(update={"ev_bridge": None, "ev_bridge_unbuilt": reason})
    out = dossier_json(unbuilt)
    assert {"ev_bridge_unbuilt"} <= json.loads(out).keys() and "ev_bridge" not in json.loads(out)
    assert Dossier.model_validate_json(out).ev_bridge_unbuilt == reason
    with pytest.raises(ValueError, match="both `ev_bridge` and `ev_bridge_unbuilt`"):
        Dossier.model_validate({**doc.model_dump(mode="json"),
                                "ev_bridge_unbuilt": reason.model_dump()})


def test_every_reader_of_a_missing_bridge_names_why() -> None:
    reason = "quarterly Balance Sheet 'Net Debt' reads 'NA' at the latest column [Q3 Jun-30-2026]"
    page: dict[str, Any] = {"ticker": "ZZFX", "anchor": {"recipe_hint": RECIPE_R4},
                            "ev_bridge_unbuilt": {"reason": reason}}
    assert any(reason in c for c in derive(page).conflicts)
    with pytest.raises(ProposalRefusedError, match="its assembly could not build one"):
        r4_bridge_fact(page)
    assert reason in (_ev_bridge_vs_ciq_tev(page).not_run or "")
    # a page that predates the field reads as it did
    bare = {k: v for k, v in page.items() if k != "ev_bridge_unbuilt"}
    assert (_ev_bridge_vs_ciq_tev(bare).not_run or "") == "no ev_bridge block on the page"


# --- the corpus (licensed workbooks; skipped where absent) ----------------------------------------


def _smpl() -> CiqBundle:
    folder = get_config().data_dir / "manual" / "ciq" / "SMPL"
    if not folder.is_dir():
        pytest.skip("SMPL's licensed CIQ export is unavailable (never committed)")
    b = CiqBundle.from_files("SMPL", sorted(p for p in folder.iterdir() if p.is_file()))
    rows = b.sheet("financials", "Income Statement", freq="annual")
    hdr = cs._period_header(rows)
    if hdr is None or not any(cs.is_period_marker(c) for c in rows[hdr]):
        pytest.skip("SMPL's export on disk carries no fiscal-year change (not 2026-11-04's)")
    return b


#: The thirteen readers SMPL's 2026-11-04 page read UNKNOWN (run 4f30d3a2), and the bridge.
_SMPL_UNKNOWN_ON_MAIN: tuple[tuple[str, Any], ...] = (
    ("net_debt", cs.net_debt), ("total_debt", cs.total_debt), ("ltm_ebitda", cs.ltm_ebitda),
    ("ltm_ocf", cs.ltm_ocf), ("free_cash_flow", cs.free_cash_flow),
    ("interest_coverage", cs.interest_coverage),
    ("balance_sheet_posture", cs.balance_sheet_posture),
    ("book_value_per_share", cs.book_value_per_share), ("key_ratios", cs.key_ratios),
    ("segments", cs.segments), ("geographic", cs.geographic),
    ("capital_summary", lambda b: cs._capital_summary(b, freq=cs._cs_summary_freq(b))),
)


def test_smpls_live_export_reads_every_latest_figure() -> None:
    """CORPUS BEFORE SYNTHETIC — SMPL's 2026-11-04 export: every field that read UNKNOWN reads,
    the bridge builds and agrees with CIQ's own TEV less market cap, segment EBITDA's absence is
    the filing fact again, and no output names the marker."""
    b = _smpl()
    for name, read in _SMPL_UNKNOWN_ON_MAIN:
        got = read(b)
        assert got.status is SourceStatus.PRESENT, (name, got.note)
        assert "Fiscal" not in repr(got), name
    bridge = cs.ev_bridge(b, fy_periods=[])
    assert isinstance(bridge, EvBridge) and bridge.ciq_tev_claims is not None
    assert bridge.claims == pytest.approx(bridge.ciq_tev_claims, abs=0.5)
    assert "single-segment reporting" in (cs.segment_ebitda(b).note or "")
    for read in (cs.financial_summary_annual, cs.financial_summary_quarterly, cs.return_ratios):
        table = read(b).value
        assert table is not None and not any("Fiscal" in c for c in table.columns), read.__name__


def test_smpls_latest_reads_equal_its_export_with_the_old_calendar_cut_out() -> None:
    """The marker and the old calendar touch no latest read: cutting every column up to and
    including the marker out of every Financials sheet leaves each read unchanged — and a header
    with no marker runs exactly main's code."""
    marked, cut = _smpl(), _smpl()
    for wb in cut.workbooks:
        if wb.kind != "financials":
            continue
        cut.sheet("financials", "Income Statement", freq=wb.freq)  # loaded into the cache
        for name, rows in cut._cache[wb.path].items():
            hdrs = [h for h in (cs._period_header(rows), cs._bs_period_header(rows),
                                cs._dated_header(rows)) if h is not None]
            marks = ([j for j, c in enumerate(rows[min(hdrs)]) if cs.is_period_marker(c)]
                     if hdrs else [])
            if not marks:
                continue
            m = marks[-1] + (1 if name == "Capital Structure Summary" else 0)  # its '' pair cell
            for r in range(min(hdrs), len(rows)):
                if len(rows[r]) > 1:
                    rows[r] = [rows[r][0], *rows[r][m + 1:]]
    reads = (*_SMPL_UNKNOWN_ON_MAIN, ("segment_ebitda", cs.segment_ebitda),
             ("ev_bridge", lambda b: cs.ev_bridge(b, fy_periods=[])),
             ("ciq_balance", lambda b: ciq_balance.extract(b, "SMPL")))
    assert [n for n, read in reads if read(marked) != read(cut)] == []


def test_every_undated_header_cell_on_file_is_a_registered_marker() -> None:
    """THE CENSUS AS A CHECK: every non-empty undated cell in a header row a reader addresses, in
    every Financials export on file, is registered — so the registry is complete for the corpus
    and an export carrying a new shape is found here, not on a page. Key Stats, whose headers CIQ
    suffixes 'A'/'E' and no reader reads, and the Capital Structure Details instrument table are
    not period headers."""
    root = get_config().data_dir / "manual" / "ciq"
    if not root.is_dir() or not any(root.iterdir()):
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    cells, unregistered = 0, set()
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        try:
            b = CiqBundle.from_files(folder.name,
                                     sorted(p for p in folder.iterdir() if p.is_file()))
        except CiqUnavailableError:
            continue
        for wb in b.workbooks:
            if wb.kind != "financials":
                continue
            try:
                b.sheet("financials", "Income Statement", freq=wb.freq)
            except CiqUnavailableError:
                continue
            for name, rows in b._cache.get(wb.path, {}).items():
                if name in ("Key Stats", "Capital Structure Details"):
                    continue
                for h in {cs._period_header(rows), cs._bs_period_header(rows)} - {None}:
                    assert h is not None
                    for c in rows[h][1:]:
                        if not str(c if c is not None else "").strip():
                            continue
                        cells += 1
                        if cs._column_date(c) is None and not cs.is_period_marker(c):
                            unregistered.add((folder.name, name, " ".join(str(c).split())))
    assert cells > 1000, f"only {cells} header cells read — near-vacuous"
    assert unregistered == set()
