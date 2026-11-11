"""Period columns are read in time order, and a column's stated duration is read (fix request 2,
order 5: audits RA-D5 and V1-O2; 2026-11-10).

* RA-D5 — sheet order was read as time order. Growth was taken between neighbouring columns, the
  estimate base was the last fiscal-year column, a trajectory ran left to right, and the "current"
  and forward Estimates years were the first FY columns by position. With the period columns
  reversed, SMPL's FY23 revenue growth read -7% (the true figure is +6%), its EPS revisions named
  FY 2033, and the listing's recommendation read "no Trends block". Financials columns now come
  from `ciq_sheets.period_columns` (within each fiscal calendar by stated end, the calendars by
  their latest end); Estimates columns by the year and quarter each label states; the listing's
  'Current' column by its header.
* V1-O2 — the period parser read the quarter token and not the duration, so '6 months FQ2/CQ4
  Nov-30-2025' was the quarter 'Q2-26' to every label, same-quarter match and LTM sum. It is now a
  year-to-date column, '6M-26', and no quarter.

The real-export pins mutate SMPL's and AMZN's exports in memory, read only, and skip where the
licensed folder is absent, as on CI. The synthetic twins run everywhere.
"""
from __future__ import annotations

import contextlib
import io
from datetime import date
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqFormat, read_sheets
from vinci.dossier.manual_store import LocalFolderStore

_FIN = ("Income Statement", "Balance Sheet", "Cash Flow", "Segments", "Ratios")
_EST = ("Trends", "Guidance", "Revisions", "Surprise")


def _loaded(b: CiqBundle) -> CiqBundle:
    for w in b.workbooks:
        if w.fmt in {CiqFormat.BIFF_XLS, CiqFormat.OOXML} and w.path not in b._cache:
            b._cache[w.path] = read_sheets(w.path, w.fmt)
    return b


def _real(ticker: str) -> CiqBundle:
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    with contextlib.redirect_stdout(io.StringIO()):
        return _loaded(CiqBundle.from_files(ticker, files))


def _synthetic() -> CiqBundle:
    paths = sorted([*(gen.HERE / gen.TICKER).iterdir(), gen.HERE / gen.ESTIMATES_XLS])
    return _loaded(CiqBundle.from_files(gen.TICKER, paths))


def _reversed(b: CiqBundle) -> CiqBundle:
    """Document 7's "period columns reordered": on the Financials statement sheets from the period
    header down, and on the Estimates Trends/Guidance/Revisions/Surprise sheets from the first
    period row down, every row's cells after column 0 in reverse order."""
    for w in b.workbooks:
        sheets = b._cache.get(w.path)
        if sheets is None:
            continue
        for name, rows in list(sheets.items()):
            if w.kind == "financials" and name in _FIN:
                h = cs._period_header(rows)
            elif w.kind == "estimates" and name in _EST:
                h = next((i for i, r in enumerate(rows) if any(
                    isinstance(c, str) and c.strip().startswith(("FY", "FQ")) for c in r[1:])),
                    None)
            else:
                h = None
            if h is None:
                continue
            width = max((len(r) for r in rows[h:]), default=0)
            new = [list(r) for r in rows]
            for i in range(h, len(new)):
                r = new[i] + [""] * (width - len(new[i]))
                new[i] = [r[0], *reversed(r[1:width])]
            sheets[name] = new
    return b


def _order_reads(b: CiqBundle) -> dict[str, Any]:
    """The readers whose output depended on the sheet's column order."""
    return {
        "annual": cs.financial_summary_annual(b, as_of="2026-11-10"),
        "quarterly": cs.financial_summary_quarterly(b),
        "trajectory": cs.multi_year_trajectory(b),
        # the margin % series is paired in one field with the absolute series `trajectory` reads
        "margin trend": cs.margin_trend(b),
        "return ratios": cs.return_ratios(b),
        "eps revisions": cs.eps_revisions(b),
        "revenue revisions": cs.revenue_revisions(b),
        "forward consensus": cs.forward_consensus(b),
        "consensus view": cs.consensus_view(b),
        "consensus stats": cs.consensus_stats(b),
    }


# --- RA-D5: time order, never sheet order --------------------------------------------------------


@pytest.mark.parametrize("ticker", ["SMPL", "AMZN"])
def test_ra_d5_reversed_period_columns_read_as_the_export_does(ticker: str) -> None:
    """(+) Before: all nine readers moved. SMPL's FY23 growth read -7% (true +6%), its EPS revisions
    named FY 2033, its trajectory ran 2026 → 2015, and the recommendation read "no Trends block"."""
    want = _order_reads(_real(ticker))
    assert want["annual"].value is not None and want["eps revisions"].value is not None
    assert _order_reads(_reversed(_real(ticker))) == want


def test_ra_d5_smpls_growth_is_its_own_under_reversal() -> None:
    """Before, reversed: FY25 read +7% across the Reclassified boundary, FY24 (R) read '— (basis)',
    and FY23 (R) read -7%."""
    fs = cs.financial_summary_annual(_reversed(_real("SMPL")))
    assert fs.value is not None
    cols = fs.value.columns
    growth = dict(zip(cols, next(r.cells for r in fs.value.rows if r.label == "Revenue growth"),
                      strict=True))
    assert cols.index("FY23 (R)") < cols.index("FY24 (R)") < cols.index("FY25") < cols.index("FY26")
    assert (growth["FY23 (R)"], growth["FY24 (R)"], growth["FY25"]) == ("+6%", "+7%", "— (basis)")


def test_ra_d5_twin_the_synthetic_exports_read_the_same_reversed() -> None:
    want = _order_reads(_synthetic())
    assert _order_reads(_reversed(_synthetic())) == want


def test_ra_d5_twin_two_fiscal_calendars_keep_their_order_reversed() -> None:
    """SMPL's shape: an old December calendar, CIQ's marker, then the August calendar. Reversed, the
    columns still come back calendar by calendar, the old one first, each in time order."""
    head = ["For the Fiscal Period Ending", "12 months\nDec-31-2016", "Fiscal\nYear\nChange",
            "12 months\nAug-29-2015", "Reclassified\n12 months\nAug-27-2016",
            "12 months\nAug-26-2017", "LTM\n12 months\nAug-26-2017"]
    want = [1, 3, 4, 5, 6]
    assert cs.period_columns(head) == want
    rev = [head[0], *reversed(head[1:])]
    assert [rev[j] for j in cs.period_columns(rev)] == [head[j] for j in want]


def test_ra_d5_twin_a_calendar_with_an_undated_column_keeps_the_sheets_order() -> None:
    """(−) A column stating no end cannot be placed, so its calendar is left as the sheet has it."""
    head = ["For the Fiscal Period Ending", "12 months\nDec-31-2025", "12 months", "12 months\n"
            "Dec-31-2024"]
    assert cs.period_columns(head) == [1, 2, 3]


def test_ra_d5_twin_a_calendar_with_no_dated_column_keeps_its_place() -> None:
    """(−) A calendar stating no end cannot be ordered among the others, so the calendars keep the
    sheet's order (review round 0: it was moved first, read as the oldest periods)."""
    head = ["For the Fiscal Period Ending", "12 months\nDec-31-2024", "12 months\nDec-31-2025",
            "Fiscal\nYear\nChange", "12 months", "12 months"]
    assert cs.period_columns(head) == [1, 2, 4, 5]


def test_v1_o2_twin_a_stub_through_a_quarter_is_year_to_date_never_a_fiscal_year() -> None:
    """(−) Review round 0: '4 months FQ4' fell to no kind and was labelled 'FY25', so it could be
    the estimate base. It is year to date, labelled by its months."""
    cell = "4 months\nFQ4\nDec-31-2025"
    assert cs.header_period(cell).kind == "YTD" and cs._fin_short(cell) == "4M-25"


def test_v1_o2_twin_a_one_month_stub_states_its_month() -> None:
    """(+) Codex round 1 (P2): '1 month', the singular, stated no duration, so a one-month stub
    read as its quarter and joined quarter-on-quarter and same-quarter comparisons. SYNTHETIC: no
    export on disk carries it (72 Financials workbooks, 2026-11-11: only '3 months' and
    '12 months'). The shape is the stated-duration rule's own, in the singular."""
    cell = "1 month\nFQ1\nJan-31-2026"
    assert cs.stated_months(cell) == 1
    assert cs.header_period(cell).kind == "YTD"


def test_ra_d5_twin_estimates_years_are_read_by_the_year_they_state() -> None:
    head = ["", "FY 2028", "FY 2027", "FY 2026", "FQ2 2027", "FQ1 2027"]
    assert head[cs._first_fy_col(head) or 0] == "FY 2026"
    assert [head[j] for j in cs._first_fq_cols(head)] == ["FQ1 2027", "FQ2 2027"]
    assert [p for _j, p in cs._forward_cols(head)][:2] == ["FY 2026", "FY 2027"]


def test_ra_d5_twin_an_estimates_label_stating_no_year_keeps_the_sheets_order() -> None:
    """(−) Nothing is guessed: with one label unreadable the sheet's own order stands."""
    head = ["", "FY 2028", "FY Current", "FY 2026"]
    assert cs._first_fy_col(head) == 1


def test_ra_d5_twin_the_listings_current_column_is_found_by_its_header() -> None:
    def trends(cells: list[list[Any]]) -> CiqBundle:
        b = _synthetic()
        w = b.workbook("estimates")
        assert w is not None
        b._cache[w.path]["Trends"] = [["Non-Periodic Trends", "", ""], *cells]
        return b

    head = [["NasdaqGS:ZZFX", "Current", "1 Month Ago"], ["Recommendation", "Buy (1.80)", "Hold"],
            ["Buy", 4.0, 3.0], ["Hold", 1.0, 2.0]]
    flipped = [[r[0], r[2], r[1]] for r in head]
    want = cs._listing_rating(trends(head))
    assert want == ("Buy (1.80)", "Buy 4, Hold 1", None)
    assert cs._listing_rating(trends(flipped)) == want


# --- V1-O2: a column's duration is read ----------------------------------------------------------


@pytest.mark.parametrize(("cell", "label", "fiscal_year"), [
    ("6 months\nFQ2/CQ4\nNov-30-2025", "6M-26", 2026),
    ("9 months\nFQ3/CQ1\nFeb-28-2026", "9M-26", 2026),
])
def test_v1_o2_a_six_or_nine_month_column_is_year_to_date_never_a_quarter(
        cell: str, label: str, fiscal_year: int) -> None:
    """(+) Before: 'Q2-26' and 'Q3-26', kind "Q" — a quarter to every same-quarter match."""
    p = cs.header_period(cell)
    assert (p.kind, p.quarter, p.fiscal_year) == ("YTD", None, fiscal_year)
    assert cs._fin_short(cell) == label


def test_v1_o2_twin_a_three_month_column_is_still_its_quarter() -> None:
    """(−) The quarter is read as before where the column states three months, or no duration."""
    for cell, label in (("3 months\nFQ2/CQ4\nNov-30-2025", "Q2-26"),
                        ("3 months Q1 Mar-31-2026", "Q1-26"), ("FQ4 2026\nAug-31-2026", "Q4-26")):
        assert cs.header_period(cell).kind == "Q" and cs._fin_short(cell) == label, cell


def _six_month_quarter(b: CiqBundle, col: int) -> CiqBundle:
    """The quarterly Income Statement with one column's '3 months' stated as '6 months'."""
    w = b.workbook("financials", freq="quarterly")
    assert w is not None
    rows = b._cache[w.path]["Income Statement"]
    h = cs._period_header(rows)
    assert h is not None
    col = col % len(rows[h])
    assert "3 months" in str(rows[h][col]), rows[h][col]
    rows[h][col] = str(rows[h][col]).replace("3 months", "6 months")
    return b


def test_v1_o2_twin_no_quarter_on_quarter_change_spans_a_year_to_date_column() -> None:
    """A half year is never compared with the quarter beside it, and no YoY is read for it."""
    want = cs.financial_summary_quarterly(_synthetic())
    got = cs.financial_summary_quarterly(_six_month_quarter(_synthetic(), 6))
    assert want.value is not None and got.value is not None
    assert want.value.columns[5] == "Q2-26" and got.value.columns[5] == "6M-26"
    qoq = next(r.cells for r in got.value.rows if r.label == "Revenue QoQ")
    yoy = next(r.cells for r in got.value.rows if r.label == "Revenue YoY")
    assert qoq[5] == qoq[6] == "— (basis)" and yoy[5] == "—", (qoq, yoy)


def test_v1_o2_twin_no_annual_growth_spans_two_year_to_date_columns() -> None:
    """(+) Two year-to-date columns side by side cover different months: before, '9M' read a
    growth against '6M' because both carried the one 'ytd' basis."""
    b = _synthetic()
    w = b.workbook("financials", freq="annual")
    assert w is not None
    rows = b._cache[w.path]["Income Statement"]
    h = cs._period_header(rows)
    assert h is not None
    rows[h][4], rows[h][5] = "6 months\nFQ2\nNov-30-2024", "9 months\nFQ3\nFeb-28-2025"
    fs = cs.financial_summary_annual(b, as_of="2026-11-10")
    assert fs.value is not None
    cols = fs.value.columns
    growth = dict(zip(cols, next(r.cells for r in fs.value.rows if r.label == "Revenue growth"),
                      strict=True))
    assert cols.index("6M-25") + 1 == cols.index("9M-25")
    assert growth["6M-25"] == growth["9M-25"] == "— (basis)", growth


def test_v1_o2_a_year_to_date_column_on_a_real_export_is_no_quarter() -> None:
    """SMPL's latest quarter stated as six months: labelled by its months, and no QoQ."""
    fs = cs.financial_summary_quarterly(_six_month_quarter(_real("SMPL"), -1))
    assert fs.value is not None
    assert fs.value.columns[-1].startswith("6M-"), fs.value.columns[-3:]
    qoq = next(r.cells for r in fs.value.rows if r.label == "Revenue QoQ")
    yoy = next(r.cells for r in fs.value.rows if r.label == "Revenue YoY")
    assert qoq[-1] == "— (basis)" and yoy[-1] == "—", (qoq[-3:], yoy[-3:])


def test_v1_o2_the_stated_months_reader() -> None:
    assert cs.stated_months("6 months\nFQ2/CQ4\nNov-30-2025") == 6
    assert cs.stated_months("12 months Dec-31-2025") == 12
    assert cs.stated_months("Fiscal\nYear\nChange") is None
    assert cs.header_period("12 months\nDec-31-2025").end == date(2025, 12, 31)
