"""SYNTHETIC CIQ-LAYOUT EXPORTS FOR AN INVENTED ISSUER — the decode layer CI can open.

WHY THIS EXISTS (audit items H-D2, H-D3). Every real CIQ export is licensed and git-ignored
(`data/manual/ciq/`), so a fresh checkout — every CI run — holds no file in any CIQ format. On
0fa8ce4a that left 480 tests skipping in CI and not one test able to open a BIFF `.xls`, an RTF
or an `.xlsx` through the reader. This module writes small
workbooks in the formats CIQ ships, laid out the way the readers address them (sheet names, the
"Period Type:" / "Currency" cells, the period-header shapes, the row labels), for ONE INVENTED
issuer. The contract suite `tests/test_ciq_reader_contract.py` reads them with zero skips.

NOTHING HERE IS LICENSED DATA. The issuer, its ticker, every number, every counterparty name and
every date is invented. What is CIQ's is only the LAYOUT VOCABULARY the readers key on — generic row
labels ("Total Revenue", "Net Debt"), sheet names, the header labels ("Period Type:", "Balance Sheet
as of:") and the header-cell SHAPES ('3 months\\nFQ4/CQ2\\nMay-31-2026'). The provenance cells that
would name a data vendor say "Synthetic fixture" instead.

THE FORMATS, as the real corpus ships them: legacy BIFF `.xls` (Financials, Annual and Quarterly;
the Estimates report's Consensus, Trends and Guidance sheets, added 2026-10-29 for audit A-D8 and
A-D10), real RTF (the Business-Relationships Customers and Suppliers views), and one OOXML `.xlsx`
— no real export is OOXML today, but `ciq.read_sheets` has a branch for it and nothing ever
exercised it. A
second BIFF workbook uses the 1904 date system, which only a real BIFF file can carry.

THE BIFF WRITER IS `xlwt` (a dev-only dependency): pure Python, writes BIFF8 that `xlrd` reads, and
its output is byte-for-byte deterministic. It has been frozen at 1.3.0 since 2017, which here is a
property — the bytes cannot drift under a release. The `.xlsx` is written by `openpyxl`, the
library `ciq.read_sheets` reads it with; its zip timestamps and document dates are pinned so a
re-run is a no-op in git.

    python -m tests.fixtures.ciq_synthetic.generate           # rewrite the committed outputs
    python -m tests.fixtures.ciq_synthetic.generate --check   # exit 1 if they would change

Run from the repository root. It imports nothing from `vinci`.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tempfile
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

ISSUER = "Zinnober Fixture Works Inc"
EXCHANGE = "NasdaqGS"
TICKER = "ZZFX"
STEM = f"{ISSUER} {EXCHANGE} {TICKER}"

#: Where each output lands, relative to this directory. `ZZFX/` mirrors one real ticker folder
#: (`data/manual/ciq/<TICKER>/`) and is the bundle the suite loads whole; the `.xlsx` and the 1904
#: workbook each restate the Quarterly export in another encoding, so they sit apart — beside it
#: they would be a second quarterly Financials export, which `CiqBundle.from_files` refuses.
ANNUAL_XLS = f"{TICKER}/{STEM} Financials_Annual.xls"
QUARTERLY_XLS = f"{TICKER}/{STEM} Financials_Quarterly.xls"
CUSTOMERS_RTF = f"{TICKER}/{STEM} Customers.rtf"
SUPPLIERS_RTF = f"{TICKER}/{STEM} Suppliers.rtf"
QUARTERLY_XLSX = f"xlsx/{STEM} Financials_Quarterly.xlsx"
QUARTERLY_1904_XLS = f"date1904/{STEM} Financials_Quarterly.xls"
#: The Estimates export, named as CIQ names it (the issuer's name with its spaces removed). It sits
#: apart so the ZZFX folder keeps pinning a bundle that holds no estimates.
ESTIMATES_XLS = f"estimates/{ISSUER.replace(' ', '')}{EXCHANGE}{TICKER}EstimatesReport.xls"
OUTPUTS = (ANNUAL_XLS, QUARTERLY_XLS, CUSTOMERS_RTF, SUPPLIERS_RTF, QUARTERLY_XLSX,
           QUARTERLY_1904_XLS, ESTIMATES_XLS)

#: CIQ's words for "no value" — the reader treats every one as UNAVAILABLE, never 0. They sit in one
#: probe row of the Quarterly Income Statement, one per period column; the first is a cell never
#: written, which BIFF reads back as '' and OOXML as None.
MARKERS = ("", "-", "—", "NM", "NA", "N/A", "Entitlement Needed", "No Data Available")
MARKER_ROW = "UNAVAILABLE markers (synthetic probe)"

NBSP = "\xa0"
Cell = str | float | date | None
Rows = list[list[Cell]]

# --- the invented issuer: fiscal year ends May 31, so its quarters carry CIQ's FQ/CQ pairing ----

Q_DATES = (date(2024, 8, 31), date(2024, 11, 30), date(2025, 2, 28), date(2025, 5, 31),
           date(2025, 8, 31), date(2025, 11, 30), date(2026, 2, 28), date(2026, 5, 31),
           date(2026, 8, 31))
_FQ = ("FQ1/CQ3", "FQ2/CQ4", "FQ3/CQ1", "FQ4/CQ2")
Q_TAGS = tuple(_FQ[i % 4] for i in range(len(Q_DATES)))
RESTATED_Q = 3  # the FQ4 2025 column carries CIQ's 'Restated' prefix
Q_REVENUE = (101.2, 104.8, 98.6, 112.3, 108.9, 113.4, 105.1, 121.7, 117.5)
Q_GROSS = (40.1, 41.9, 38.7, 45.2, 43.8, 45.9, 41.6, 49.3, 47.6)
Q_EBITDA = (15.3, 16.4, 14.1, 18.2, 17.0, 18.1, 15.5, 20.4, 19.2)
Q_CFO = (12.0, 13.1, 9.8, 16.4, 13.5, 14.2, 11.9, 18.8, 15.7)
Q_CASH = (52.4, 55.1, 49.8, 61.0, 58.3, 60.7, 57.2, 66.9, 64.5)
Q_DEBT = (185.0, 183.5, 182.0, 180.5, 179.0, 177.5, 176.0, 174.5, 173.0)
Q_MINORITY = (2.9, 2.9, 3.0, 3.0, 3.1, 3.1, 3.2, 3.3, 3.3)

#: Fiscal years FY22..FY26 (May 31) and an LTM column to the latest quarter. FY25, FY26 and LTM are
#: the sums of the quarters above, so the two exports agree with each other as a real pair does.
A_DATES = (date(2022, 5, 31), date(2023, 5, 31), date(2024, 5, 31), date(2025, 5, 31),
           date(2026, 5, 31))
LTM_DATE = Q_DATES[-1]
#: Two flow rows only the ANNUAL Cash Flow carries, FY22..FY26 then LTM: the anchor bridge reads
#: D&A and capex off the annual sheet while it reads the balance sheet off the quarterly one, so a
#: fact's provenance names a different export from its neighbour's (audit A-D6).
A_DA = (9.8, 10.4, 11.1, 11.9, 12.6, 12.8)
A_CAPEX = (-14.2, -15.0, -15.9, -16.8, -17.5, -17.9)

#: The Multiples sheet's columns: each quarter end, then CIQ's partial-period snapshot column.
M_DATES = (*Q_DATES, date(2026, 10, 23))
M_TEV_EBITDA_CLOSE = (11.8, 12.4, 11.1, 12.9, 13.6, 12.2, 11.5, 12.8, 13.3, 14.1)
M_PE_CLOSE: tuple[float | str, ...] = (24.5, 25.9, 23.0, "NM", 27.4, 26.1, 24.8, 28.0, 29.2, "NM")


def _sum4(series: tuple[float, ...], end: int) -> float:
    """The four quarters ending at index ``end`` (inclusive), to one decimal."""
    return round(sum(series[end - 3:end + 1]), 1)


def _annual(early: tuple[float, float, float], q: tuple[float, ...]) -> list[float]:
    """FY22-FY24 as given, then FY25, FY26 and LTM summed from the quarters."""
    return [*early, _sum4(q, 3), _sum4(q, 7), _sum4(q, 8)]


def _mdy(d: date) -> str:
    return d.strftime("%b-%d-%Y")  # 'May-31-2026' — the string-date shape of the period headers


def _preamble(title: str, period_type: str) -> Rows:
    """Rows 0-13 of a Financials statement sheet: the title, the export-settings block (the
    "Period Type:" and "Currency:" cells the readers read), and the sheet's own heading at row
    13."""
    return [[], [], [], [],
            [f"{ISSUER} ({EXCHANGE}:{TICKER}) > Financials > {title}"], [],
            ["In Millions of the reported currency, except per share items.", "Template:",
             "Standard", NBSP, "Restatement:", "Latest Filings"],
            ["", "Period Type:", period_type, NBSP, "Order:", "Latest on Right"],
            ["", "Currency:", "Reported Currency", NBSP, "Conversion:", "Historical"],
            ["", "Units:", "Default", NBSP, "Decimals:", "Default"],
            ["", "Source:", "Synthetic fixture — every value invented"],
            [], [], [title]]


def _currency_row(n: int, currency: str) -> list[Cell]:
    return ["Currency", *([currency] * n)]


def _no_data_shell(title: str, period_type: str) -> Rows:
    """CIQ's header-only subsheet: the export pulled the tab and CIQ returned no rows for it."""
    rows = _preamble(title, period_type)
    rows[13] = ["No Data Available"]
    return rows


# --- the two Financials exports ---------------------------------------------------------------


def _annual_sheets(currency: str) -> dict[str, Rows]:
    a_head = ["For the Fiscal Period Ending\n",
              *[("Reclassified\n" if i == 0 else "") + f"12 months\n{_mdy(d)}"
                for i, d in enumerate(A_DATES)],
              f"LTM\n12 months\n{_mdy(LTM_DATE)}"]
    income = _preamble("Income Statement", "Annual") + [
        a_head, _currency_row(6, currency), [" "],
        ["  Total Revenue", *_annual((352.0, 377.5, 398.2), Q_REVENUE)],
        ["Gross Profit", *_annual((139.0, 149.9, 158.8), Q_GROSS)],
        ["EBITDA", *_annual((51.8, 56.3, 60.9), Q_EBITDA)],
    ]
    cash_flow = _preamble("Cash Flow", "Annual") + [
        a_head, _currency_row(6, currency), [" "],
        ["  Cash from Ops.", *_annual((38.4, 44.0, 47.9), Q_CFO)],
        ["Depreciation & Amort., Total", *A_DA],
        ["Capital Expenditure", *A_CAPEX],
        ["Levered Free Cash Flow", 21.6, 25.3, 27.0, 30.8, 35.2, 36.9],
    ]
    a_cash = (38.2, 41.5, 45.0, Q_CASH[3], Q_CASH[7])
    a_debt = (196.0, 192.0, 188.5, Q_DEBT[3], Q_DEBT[7])
    balance = _preamble("Balance Sheet", "Annual") + [
        # the ANNUAL balance-sheet header is a row of date SERIALS, not label strings
        ["Balance Sheet as of:\n", *A_DATES], _currency_row(5, currency),
        ["Total Cash & ST Investments", *a_cash],
        ["Total Debt", *a_debt],
        ["Net Debt", *[round(d - c, 1) for d, c in zip(a_debt, a_cash, strict=True)]],
        ["Total Pref. Equity", *(["-"] * 5)],
        ["Total Minority Interest", 2.4, 2.6, 2.8, Q_MINORITY[3], Q_MINORITY[7]],
    ]
    return {
        "Income Statement": income,
        "Balance Sheet": balance,
        "Cash Flow": cash_flow,
        "Capital Structure Summary": _cap_summary(
            [f" 12 months {_mdy(A_DATES[-2])}", f" 12 months {_mdy(A_DATES[-1])}"],
            [a_debt[-2], a_debt[-1]], "Annual", currency),
        "Capital Structure Details": _cap_details(currency),
        "Segments": _no_data_shell("Segments", "Annual"),
    }


def _cap_summary(periods: list[str], debt: list[float], period_type: str,
                 currency: str) -> Rows:
    """Each period spans TWO columns (the amount, then its share of the total), so the header and
    'Currency' rows alternate a label with an EMPTY cell — CIQ's own shape on this sheet."""
    head: list[Cell] = [" For the Fiscal Period Ending\n"]
    cur: list[Cell] = [" Currency"]
    total: list[Cell] = ["Total Debt"]
    for p, d in zip(periods, debt, strict=True):
        head += [p, ""]
        cur += [f" {currency}", ""]
        total += [d, 100.0]
    return _preamble("Capital Structure Summary", period_type) + [head, cur, total]


def _cap_details(currency: str) -> Rows:
    rows: Rows = [[], [], [], [], [f"{ISSUER} ({EXCHANGE}:{TICKER}) > Capital Structure Details"],
                  [],
                  ["Principal Due in Millions of the reported currency.", "Period Type:", "Annual"],
                  [], [], [], [], []]
    rows.append(["Description", "Type", f"Principal Due ({currency})", "Coupon/Base Rate",
                 f"Floating{NBSP}Rate", "Maturity", "Repayment Currency"])
    rows.append(["4.250% Senior Notes due 2031", "Senior Notes", 150.0, 4.25, "",
                 _mdy(date(2031, 9, 15)), currency])
    rows.append(["Revolving Credit Facility", "Revolving Credit", 24.5, "-", "SOFR+1.250%",
                 _mdy(date(2029, 3, 1)), currency])
    return rows


def _quarterly_sheets(currency: str) -> dict[str, Rows]:
    n = len(Q_DATES)
    q_head = ["For the Fiscal Period Ending\n",
              *[("Restated\n" if i == RESTATED_Q else "") + f"3 months\n{tag}\n{_mdy(d)}"
                for i, (tag, d) in enumerate(zip(Q_TAGS, Q_DATES, strict=True))]]
    income = _preamble("Income Statement", "Quarterly") + [
        q_head, _currency_row(n, currency), [" "],
        ["  Total Revenue", *Q_REVENUE],
        ["Gross Profit", *Q_GROSS],
        ["EBITDA", *Q_EBITDA],
        [MARKER_ROW, *MARKERS],
    ]
    cash_flow = _preamble("Cash Flow", "Quarterly") + [
        q_head, _currency_row(n, currency), [" "],
        ["  Cash from Ops.", *Q_CFO],
    ]
    balance = _preamble("Balance Sheet", "Quarterly") + [
        # the QUARTERLY balance-sheet header is label strings ('FQ4/CQ2\nMay-31-2026'), no serials
        ["Balance Sheet as of:\n",
         *[("Restated\n" if i == RESTATED_Q else "") + f"{tag}\n{_mdy(d)}"
           for i, (tag, d) in enumerate(zip(Q_TAGS, Q_DATES, strict=True))]],
        _currency_row(n, currency),
        ["Total Cash & ST Investments", *Q_CASH],
        ["Total Debt", *Q_DEBT],
        ["Net Debt", *[round(d - c, 1) for d, c in zip(Q_DEBT, Q_CASH, strict=True)]],
        ["Total Pref. Equity", *(["-"] * n)],
        ["Total Minority Interest", *Q_MINORITY],
    ]
    return {
        "Income Statement": income,
        "Balance Sheet": balance,
        "Cash Flow": cash_flow,
        "Multiples": _multiples(),
        "Capital Structure Summary": _cap_summary(
            [f" 3 months {_mdy(Q_DATES[-2])}", f" 3 months {_mdy(Q_DATES[-1])}"],
            [Q_DEBT[-2], Q_DEBT[-1]], "Quarterly", currency),
    }


def _multiples() -> Rows:
    """The Multiples sheet: a header of date SERIALS from column 2, then per metric four rows —
    the metric label beside 'Average', and 'High' / 'Low' / 'Close' under it with column 0 blank."""
    rows: Rows = [[], [], [], [], [f"{ISSUER} ({EXCHANGE}:{TICKER}) > Financials > Multiples"],
                  [],
                  ["", "View:", "Data", NBSP, "Frequency:", "Quarterly"],
                  ["", "Order:", "Latest on Right", NBSP, "Decimals:", "Default"],
                  ["", "Dilution:", "Basic"],
                  [], [],
                  ["Multiples Detail"],
                  [],
                  ["For Quarter Ending", "", *M_DATES]]
    close_rows: tuple[tuple[str, tuple[float | str, ...]], ...] = (
        ("TEV/LTM EBITDA", M_TEV_EBITDA_CLOSE), ("P/LTM EPS", M_PE_CLOSE))
    for metric, close in close_rows:
        for label, offset in ((metric, -0.3), ("", 0.9), ("", -1.2)):
            stat = "Average" if label else ("High" if offset > 0 else "Low")
            rows.append([label, stat, *[round(c + offset, 1) if isinstance(c, float) else c
                                        for c in close]])
        rows.append(["", "Close", *close])
    return rows


# --- the Estimates export ---------------------------------------------------------------------
#
# Laid out as the real exports are (census of the 34 non-test folders, 2026-10-29): Consensus
# carries an 'Industry Recommendation' row beside the listing's own rating block; Trends' 'Non-
# Periodic Trends' section holds ONE BLOCK PER LISTING — each headed '<EXCHANGE>:<TICKER> |
# Current', its 'Recommendation' and counts, then an 'Ind. Recommendation' and ITS counts — with a
# depositary receipt carrying the industry rows only and a second share class after it (GOOGL's
# shape); Guidance holds one block per guided metric, each a label row over 'As Of Guidance',
# under a company-level header and then each listing's, a per-share block repeated identically
# under the listing's second header (GOOGL's again).

SECOND_CLASS = f"{TICKER}K"  # the invented issuer's second share class, its own Trends block
REC_OWN, REC_INDUSTRY, REC_SECOND = "Hold (2.75)", "Outperform (2.25)", "Buy (1.50)"
#: (category label, the listing's count, the industry's count), Current column.
RATINGS = (("Buy (1)", 2.0, 1.0), ("Outperform (2)", 1.0, 1.0), ("Hold (3)", 4.0, 2.0),
           ("Underperform (4)", 1.0, 0.0), ("Sell (5)", 0.0, 0.0), ("No Opinion", 1.0, None))
SECOND_RATINGS = (("Buy (1)", 3.0), ("Outperform (2)", 1.0), ("Hold (3)", 0.0),
                  ("Underperform (4)", 0.0), ("Sell (5)", 0.0), ("No Opinion", 0.0))
G_PERIODS = ("FQ1 2027", "FQ2 2027", "FY 2026", "FY 2027")
G_DATED, G_PRIOR = date(2026, 9, 24), date(2025, 9, 25)  # this year's guides; last year's
#: Each guided block: (metric, {period: (guide cell, its guidance date)}, {period: actual}). Same-
#: store sales is OUTSIDE the fifteen metrics the reader once listed (audit A-D8); revenue and capex
#: were in it.
Guide = tuple[str, dict[str, tuple[Cell, date]], dict[str, float]]
GUIDES: tuple[Guide, ...] = (
    ("Same Store Sales Growth %", {"FQ2 2027": (3.5, G_DATED)}, {}),
    ("Revenue", {"FY 2026": ("440.00 - 450.00", G_PRIOR), "FY 2027": ("460.00 - 470.00", G_DATED)},
     {"FY 2026": 455.0}),
    ("Capital Expenditure", {"FY 2027": ("(30.00) - (25.00)", G_DATED)}, {}),
)
LISTING_GUIDES: tuple[Guide, ...] = (("EPS Normalized", {"FY 2027": (1.2, G_DATED)}, {}),)
SECOND_GUIDES: tuple[Guide, ...] = (("DPS", {"FY 2027": (0.4, G_DATED)}, {}),)


def _estimates_preamble(title: str) -> Rows:
    return [[], [], [], [], [f"{ISSUER} ({EXCHANGE}:{TICKER}) > Estimates > {title}"], [], [], [],
            ["Currency: Reported Currency", "Conversion: Today's Spot Rate"],
            ["Units: Capital IQ (Default)", "Decimals: Capital IQ (Default)"],
            ["Consolidation: Consolidated", "Acctg. Standard: US GAAP"], [],
            [f"Current Fiscal Year End: {_mdy(date(2027, 5, 31))}"]]


def _consensus() -> Rows:
    own = f"{EXCHANGE}:{TICKER}"
    counts = [f"{n} - {c.split(' (')[0]}" for n, c in
              zip(("1", "2", "3", "4", "5", "0"), (r[0] for r in RATINGS), strict=True)]
    rows = _estimates_preamble("Consensus") + [
        [],
        [f"{own} (USD)", "Mean", "Median", "High/Low", "Std. Dev.", "No. of Estimates.", "",
         f"{own} - Recommendation: {REC_OWN}"],
        ["Target Price", 31.4, 30.0, "38.00/24.00", 4.1, "8/8", "", counts[0], RATINGS[0][1]],
        ["LT Growth", 0.081, 0.08, "10.00%/6.00%", 1.2, "3/3", "", counts[1], RATINGS[1][1]],
        ["Price Volatility", "Average (3.00)", "", "", "", "", "", counts[2], RATINGS[2][1]],
        ["Industry Recommendation", REC_INDUSTRY, "", "", "", "", "", counts[3], RATINGS[3][1]],
        ["", "", "", "", "", "", "", counts[4], RATINGS[4][1]],
        ["", "", "", "", "", "", "", counts[5], RATINGS[5][1]],
    ]
    return rows


def _trends() -> Rows:
    head = ["Current", "1 month ago"]
    rows = _estimates_preamble("Trends") + [[], ["Non-Periodic Trends"],
                                            [f"{EXCHANGE}:{TICKER}", *head],
                                            ["Recommendation", REC_OWN, REC_OWN]]
    rows += [[c, n, n] for c, n, _ in RATINGS]
    rows.append(["Ind. Recommendation", REC_INDUSTRY, REC_INDUSTRY])
    rows += [[c, n, n] for c, _, n in RATINGS if n is not None]
    rows += [["Price Volatility", "Average (3.00)", "Average (3.00)"], ["Low (1)", 0.0, 0.0],
             ["LT Growth (%)", "8.10 %", "8.30 %"], ["Target Price", 31.4, 30.9],
             [f"BOVESPA:{TICKER}34", *head],  # a depositary receipt: the industry rows only
             ["Ind. Recommendation", REC_INDUSTRY, REC_INDUSTRY]]
    rows += [[c, n, n] for c, _, n in RATINGS if n is not None]
    rows += [[f"{EXCHANGE}:{SECOND_CLASS}", *head],
             ["Recommendation", REC_SECOND, REC_SECOND]]
    rows += [[c, n, n] for c, n in SECOND_RATINGS]
    rows.append(["Ind. Recommendation", REC_INDUSTRY, REC_INDUSTRY])
    rows += [[c, n, n] for c, _, n in RATINGS if n is not None]
    return rows


def _guidance_block(metric: str, guide: dict[str, tuple[Cell, date]],
                    actual: dict[str, float]) -> Rows:
    def per(cells: dict[str, Cell]) -> list[Cell]:
        return [cells.get(p, "-") for p in G_PERIODS]

    dates: dict[str, Cell] = {p: d for p, (_g, d) in guide.items()}
    guides: dict[str, Cell] = {p: g for p, (g, _d) in guide.items()}
    actuals: dict[str, Cell] = dict(actual)
    return [[metric, *per({})], ["As Of Guidance", *per({})],
            ["    Guidance Date", *per(dates)], ["    Consensus Estimate", *per({})],
            ["    Guidance", *per(guides)], ["        % Difference", *per({})],
            ["    Days before actual", *per({})],
            ["Actual/Latest", *per({})], ["    Actual/Latest Date", *per({})],
            ["    Guidance", *per(guides)], ["    Consensus Estimate", *per({})],
            ["        % Difference", *per({})], ["    Actual", *per(actuals)],
            ["        % Difference", *per({})]]


def _guidance() -> Rows:
    rows = _estimates_preamble("Guidance") + [
        ["Date", "Type", "Headline", "Situation"],
        [G_DATED, "Corporate Guidance - Raised", f"{ISSUER} Raises Guidance",
         "Synthetic fixture: an invented guidance event."], [],
        ["Company Level (USD)", *G_PERIODS]]
    for g in GUIDES:
        rows += _guidance_block(*g)
    for listing in (TICKER, TICKER, SECOND_CLASS):  # the listing's header twice, as GOOGL's is
        rows.append([f"{EXCHANGE}:{listing} (USD)", *G_PERIODS])
        for g in (SECOND_GUIDES if listing == SECOND_CLASS else LISTING_GUIDES):
            rows += _guidance_block(*g)
    return rows


#: (2026-10-30, audit A-D1) the Revisions sheet: per metric block, a title row, the listing's period
#: header, then three windows each carrying '# of Analysts', '# of Analysts still in Consensus',
#: 'Upward' and 'Downward' — the layout of every real export's Revisions sheet. Counts are floats,
#: as CIQ writes them; an explicit 0.0 is a count of none (CIQ writes zeros; a marker is no count).
R_PERIODS = ("FQ1 2027", "FQ2 2027", "FY 2027", "FY 2028")
#: (window label, {metric: (analysts, in consensus, up, down) per R_PERIODS column}).
REVISIONS: tuple[tuple[str, dict[str, tuple[tuple[float, float, float, float], ...]]], ...] = (
    ("Last Month", {"EPS (GAAP)": ((8.0, 7.0, 2.0, 1.0), (8.0, 7.0, 1.0, 0.0),
                                   (9.0, 8.0, 3.0, 1.0), (6.0, 5.0, 1.0, 1.0)),
                    "Revenue": ((9.0, 8.0, 1.0, 2.0), (9.0, 8.0, 0.0, 1.0),
                                (10.0, 9.0, 2.0, 2.0), (7.0, 6.0, 0.0, 0.0))}),
    ("Last 2 Months", {"EPS (GAAP)": ((8.0, 7.0, 3.0, 1.0), (8.0, 7.0, 2.0, 0.0),
                                      (9.0, 8.0, 4.0, 1.0), (6.0, 5.0, 1.0, 2.0)),
                       "Revenue": ((9.0, 8.0, 2.0, 2.0), (9.0, 8.0, 1.0, 1.0),
                                   (10.0, 9.0, 3.0, 2.0), (7.0, 6.0, 1.0, 0.0))}),
    ("Last 3 Months", {"EPS (GAAP)": ((8.0, 7.0, 4.0, 2.0), (8.0, 7.0, 2.0, 1.0),
                                      (9.0, 8.0, 5.0, 2.0), (6.0, 5.0, 2.0, 2.0)),
                       "Revenue": ((9.0, 8.0, 3.0, 2.0), (9.0, 8.0, 1.0, 2.0),
                                   (10.0, 9.0, 4.0, 3.0), (7.0, 6.0, 1.0, 1.0))}),
)
R_ROWS = ("# of Analysts", "# of Analysts still in Consensus", "Upward", "Downward")


def _revisions() -> Rows:
    rows = _estimates_preamble("Revisions") + [[]]
    for metric in ("EPS (GAAP)", "Revenue"):
        rows += [[metric, *([""] * len(R_PERIODS))],
                 [f"{EXCHANGE}:{TICKER}", *(f"  {p}" for p in R_PERIODS)]]
        for window, by_metric in REVISIONS:
            rows.append([window, *([""] * len(R_PERIODS))])
            cols = by_metric[metric]
            rows += [[label, *(c[i] for c in cols)] for i, label in enumerate(R_ROWS)]
        rows.append([])
    return rows


def _estimates_sheets() -> dict[str, Rows]:
    return {"Consensus": _consensus(), "Trends": _trends(), "Guidance": _guidance(),
            "Revisions": _revisions()}


# --- the Business-Relationships views (real RTF) ------------------------------------------------

_RTF_HEAD = "{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0\\fswiss Arial;}}\n"
_RTF_ROW = "\\trowd\\cellx2600\\cellx4600\\cellx7000\\cellx9000\n\\pard\\intbl {}\\cell\\row\n"


def _rtf_par(text: str) -> str:
    return f"\\pard\\plain {text}\\par\n"


def _rtf_table_row(cells: list[str]) -> str:
    return _RTF_ROW.format("\\cell ".join(cells))


def customers_rtf() -> str:
    """The Customers view: a pipe-rendered table under its 'Customer Name | Relationship Type'
    header, with one 'Business Description:' row the parser must skip. Every counterparty is
    invented."""
    return (_RTF_HEAD
            + _rtf_par(f"{ISSUER} ({EXCHANGE}:{TICKER}) > Business Relationships > Customers")
            + _rtf_par("Synthetic fixture: every company named below is invented.")
            + _rtf_table_row(["Customer Name", "Relationship Type", "Primary Industry", "Source"])
            + _rtf_table_row(["Quillfeather Freight Ltd", "Customer", "Air Freight and Logistics",
                              "Company Filing"])
            + _rtf_table_row(["Business Description: an invented freight forwarder."])
            + _rtf_table_row(["Brantwick Municipal Power", "Customer", "Electric Utilities",
                              "Press Release"])
            + _rtf_table_row(["Tamsworth Kettle Works", "Customer", "Industrial Machinery",
                              "Company Filing"])
            + "}\n")


def suppliers_rtf() -> str:
    """The Suppliers view of a company with none disclosed: CIQ says so in a sentence, not a
    table."""
    return (_RTF_HEAD
            + _rtf_par(f"{ISSUER} ({EXCHANGE}:{TICKER}) > Business Relationships > Suppliers")
            + _rtf_par("There are no recently disclosed suppliers listed for this company.")
            + "}\n")


# --- writers ----------------------------------------------------------------------------------


def write_biff(path: Path, sheets: dict[str, Rows], *, dates_1904: bool = False) -> None:
    """A BIFF8 `.xls` via xlwt. A `date` cell is written as a date-formatted serial (xlrd reads a
    float); an empty string or None is left UNWRITTEN, as CIQ leaves it (xlrd reads '')."""
    import xlwt  # type: ignore[import-untyped]

    book = xlwt.Workbook(encoding="utf-8")
    book.dates_1904 = dates_1904
    date_style = xlwt.easyxf(num_format_str="mmm-dd-yyyy")
    for name, rows in sheets.items():
        ws = book.add_sheet(name)
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                if cell is None or cell == "":
                    continue
                if isinstance(cell, date):
                    ws.write(r, c, cell, date_style)
                else:
                    ws.write(r, c, cell)
    buf = io.BytesIO()
    book.save(buf)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.getvalue())


#: The one timestamp an `.xlsx` carries, pinned so a re-run rewrites identical bytes.
_PINNED = datetime(2026, 1, 1)
_CORE_STAMP = re.compile(r"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)")


def write_ooxml(path: Path, sheets: dict[str, Rows]) -> None:
    """An `.xlsx` via openpyxl, with empty cells left unwritten (openpyxl reads them as None) and
    every timestamp pinned — the zip members' and the document's own created/modified dates."""
    import openpyxl  # type: ignore[import-untyped]

    book = openpyxl.Workbook()
    book.remove(book.active)
    book.properties.created = _PINNED
    for name, rows in sheets.items():
        ws = book.create_sheet(name)
        for r, row in enumerate(rows, start=1):
            for c, cell in enumerate(row, start=1):
                if cell is None or cell == "":
                    continue
                ws.cell(row=r, column=c,
                        value=datetime(cell.year, cell.month, cell.day)
                        if isinstance(cell, date) else cell)
    raw = io.BytesIO()
    book.save(raw)
    out = io.BytesIO()
    stamp = _PINNED.strftime("%Y-%m-%dT%H:%M:%SZ")
    with zipfile.ZipFile(raw) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "docProps/core.xml":
                data = _CORE_STAMP.sub(rf"\g<1>{stamp}\g<2>", data.decode()).encode()
            dst.writestr(zipfile.ZipInfo(info.filename, date_time=(1980, 1, 1, 0, 0, 0)), data,
                         compress_type=zipfile.ZIP_DEFLATED)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out.getvalue())


def build_financials(path: Path, *, freq: str, currency: str = "USD",
                     encoding: str = "biff", dates_1904: bool = False) -> None:
    """One Financials export. Public so a test can write a VARIANT (another stated currency) into
    a temporary folder — the committed set itself is only ever written by :func:`build_all`."""
    if freq not in ("annual", "quarterly"):
        raise ValueError(f"freq must be 'annual' or 'quarterly', not {freq!r}")
    sheets = _annual_sheets(currency) if freq == "annual" else _quarterly_sheets(currency)
    if encoding == "ooxml":
        write_ooxml(path, sheets)
    else:
        write_biff(path, sheets, dates_1904=dates_1904)


def build_all(out_dir: Path) -> list[Path]:
    """Write every committed output under ``out_dir``; returns the paths, in `OUTPUTS` order."""
    build_financials(out_dir / ANNUAL_XLS, freq="annual")
    build_financials(out_dir / QUARTERLY_XLS, freq="quarterly")
    for rel, text in ((CUSTOMERS_RTF, customers_rtf()), (SUPPLIERS_RTF, suppliers_rtf())):
        (out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (out_dir / rel).write_bytes(text.encode("ascii"))
    build_financials(out_dir / QUARTERLY_XLSX, freq="quarterly", encoding="ooxml")
    build_financials(out_dir / QUARTERLY_1904_XLS, freq="quarterly", dates_1904=True)
    write_biff(out_dir / ESTIMATES_XLS, _estimates_sheets())
    return [out_dir / rel for rel in OUTPUTS]


def ooxml_values(path: Path) -> dict[str, list[tuple[Any, ...]]]:
    """An `.xlsx`'s decoded cell values per sheet — how a re-run is compared for this one format,
    since its XML serialisation may legitimately change across openpyxl releases."""
    import openpyxl

    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:  # a read-only workbook holds its zip open until closed (PR #853 review, round 1)
        return {ws.title: list(ws.iter_rows(values_only=True)) for ws in book.worksheets}
    finally:
        book.close()


def drift(committed: Path, fresh: Path) -> list[str]:
    """Outputs whose committed copy differs from a fresh build (bytes; decoded values for .xlsx)."""
    bad: list[str] = []
    for rel in OUTPUTS:
        old, new = committed / rel, fresh / rel
        if not old.exists():
            bad.append(f"{rel}: not committed")
        elif rel.endswith(".xlsx"):
            if ooxml_values(old) != ooxml_values(new):
                bad.append(f"{rel}: cell values differ")
        elif old.read_bytes() != new.read_bytes():
            bad.append(f"{rel}: bytes differ")
    return bad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--check", action="store_true",
                        help="build into a temporary folder and report drift; write nothing")
    args = parser.parse_args(argv)
    if not args.check:
        for p in build_all(HERE):
            print(f"wrote {p.relative_to(HERE)} ({p.stat().st_size} bytes)")
        return 0
    with tempfile.TemporaryDirectory() as td:
        build_all(Path(td))
        bad = drift(HERE, Path(td))
    for line in bad:
        print(f"DRIFT {line}")
    print(f"{len(OUTPUTS) - len(bad)} of {len(OUTPUTS)} outputs match the generator")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
