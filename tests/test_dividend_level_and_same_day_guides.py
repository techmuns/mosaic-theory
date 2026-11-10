"""The dividend per share is the dividend, and every period guided on the latest date is kept
(fix request 2, order 4: audits RA-D2 and RA-D4; 2026-11-10). Both change what live pages print.

* RA-D2 — CIQ's Ratios sheet has no dividend level: its 'Dividend per Share' rows are growth rates
  (YoY, then two-, three- and five-year CAGRs), and the first was printed as "Dividend/sh". V's
  page read 0.19, 0.15, 0.13, 0.14 against dividends of 1.87, 2.15, 2.44, 2.79; GOOGL's 0.38 and
  0.05 against 0.83 and 0.86. The level is the Income Statement's 'Dividends per Share', for the
  same periods. A growth cell at 'NM' printed "dividend: none" for a payer.
* RA-D4 — F12 asks for every period guided on the latest date. The guidance read kept one, the
  leftmost column of that date, so SMPL's FY guide given with its quarter guide was dropped, and
  reversing the columns kept the other. The read now carries the others, each labelled, in time
  order; its own period (the one the guide check takes) is the first in time, never by column.

Real-export pins read the export on disk as it stands (skip where absent, as on CI); constructed
twins run everywhere.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, clean_num
from vinci.dossier.manual_store import LocalFolderStore


def _real(ticker: str) -> CiqBundle:
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


# --- RA-D2 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("ticker", ["V", "GOOGL", "NKE"])
def test_ra_d2_the_dividend_row_is_the_income_statements_level_never_a_growth_rate(
        ticker: str) -> None:
    """On each payer's export as it stands: every 'Dividend/sh' cell is the Income Statement's
    'Dividends per Share' for that column's period, and none is the Ratios sheet's growth row."""
    b = _real(ticker)
    table = cs.return_ratios(b).value
    assert table is not None
    row = next(r for r in table.rows if r.label == "Dividend/sh")
    rat = b.sheet("financials", "Ratios", freq="annual")
    hdr = cs._period_header(rat)
    assert hdr is not None
    cols = [c for c, *_ in cs._fin_periods(rat[hdr])]
    inc = b.sheet("financials", "Income Statement", freq="annual")
    ihdr, di = cs._period_header(inc), cs._find_row(inc, "Dividends per Share")
    assert ihdr is not None and di is not None
    level = {(p.kind, p.end): clean_num(inc[di][j]) for j, c in enumerate(inc[ihdr])
             if j and (p := cs.header_period(c)).kind and p.end}
    want = [level.get((p.kind, p.end)) for c in cols for p in (cs.header_period(rat[hdr][c]),)]
    assert row.cells == [f"{v:.2f}" if v is not None else "none" for v in want]
    growth = cs._find_row(rat, "Dividend per Share")
    assert growth is not None
    paid = [(v, clean_num(rat[growth][c])) for v, c in zip(want, cols, strict=True) if v]
    assert paid and all(f"{v:.2f}" != f"{g:.2f}" for v, g in paid if g is not None), paid


def test_ra_d2_a_payer_whose_growth_reads_nm_is_not_said_to_pay_none() -> None:
    """(+) V's Ratios growth cell at the pinned column set to 'NM': no "dividend: none". (−) AMZN,
    which pays none, still says so."""
    b = _real("V")
    rat = b.sheet("financials", "Ratios", freq="annual")
    for r in rat:
        if r and str(r[0]).strip() == "Dividend per Share":
            r[-1] = "NM"
    assert "dividend: none" not in (cs.key_ratios(b).value or "")
    assert "dividend: none" in (cs.key_ratios(_real("AMZN")).value or "")


# --- RA-D4 ---------------------------------------------------------------------------------------


def test_ra_d4_smpls_latest_guides_are_all_kept_whatever_the_column_order() -> None:
    """SMPL's export as it stands guides revenue for more than one period on its latest date (read
    off the sheet here): each is a row, labelled, in the bridge; reversing the sheet's period
    columns changes nothing, the most recent outcome included."""
    from vinci.dossier.ciq import excel_date

    b = _real("SMPL")
    rows = b.sheet("estimates", "Guidance")
    starts = cs._guidance_starts(rows)
    bi = next(k for k in starts if str(rows[k][0]).strip() == "Revenue")
    end = next((k for k in starts if k > bi), len(rows))
    gdate, guide, _actual = cs._guidance_rows(rows, bi, end)
    header = cs._nearest_period_header(rows, bi)
    assert gdate is not None and guide is not None and header is not None
    dated = [(d, str(header[j]).strip()) for j in range(1, len(header))
             if (d := excel_date(rows[gdate][j])) is not None and cs._parse_range(rows[guide][j])]
    top = max(d for d, _p in dated)
    want = sorted(p for d, p in dated if d == top)
    assert len(want) >= 2, "the export no longer guides two periods on one date"
    table = cs.guidance_bridge_rows(b).value or []
    assert sorted(r.period for r in table if r.metric == "Revenue") == want
    bridge = cs.guidance_bridge(b).value or ""
    assert all(f"for {p}" in bridge for p in want), bridge
    lohi = cs.revenue_guide_lohi(b)
    for r in rows:
        if len(r) > 2:
            r[1:] = list(reversed(r[1:]))
    assert cs.guidance_bridge_rows(b).value == table and cs.revenue_guide_lohi(b) == lohi


def _block(periods: list[str], guides: list[object], dates: list[str]) -> list[list[object]]:
    return [["", *periods], ["Revenue"], ["Guidance Date", *dates], ["Guidance", *guides],
            ["Actual/Latest"], ["Actual", *([""] * len(periods))]]


@pytest.mark.parametrize("periods", [["FQ4 2026", "FY 2026"], ["FY 2026", "FQ4 2026"]])
def test_ra_d4_twin_both_periods_of_one_day_are_kept_in_time_order(periods: list[str]) -> None:
    """The auditor's SMPL case on constructed rows, in both column orders: FQ4 2026 322-332 and
    FY 2026 1,345-1,355, both dated 2026-07-09. The read's own period is FQ4 2026 either way; FY
    2026 rides with it."""
    guides: dict[str, Any] = {"FQ4 2026": "322.00 - 332.00", "FY 2026": "1,345.00 - 1,355.00"}
    rows = _block(periods, [guides[p] for p in periods], ["2026-07-09", "2026-07-09"])
    (r,) = cs._guidance_reads(rows, cs._metric_starts(rows, ("Revenue",)), date(2026, 8, 12), 45)
    assert (r.period, r.guide_range) == ("FQ4 2026", (322.0, 332.0))
    assert r.same_day == (("FY 2026", "'1,345.00 - 1,355.00'"),)


@pytest.mark.parametrize("periods", [["FQ4 2026", "FY 2026"], ["FY 2026", "FQ4 2026"]])
def test_ra_d4_twin_an_unread_guide_of_one_day_is_chosen_by_time_order(periods: list[str]) -> None:
    """(review) The RA-D3 unread read had the same column tie: two guides dated one day whose cells
    both read 'NA' named the leftmost. It is FQ4 2026, the first in time order, either way."""
    rows = _block(periods, ["NA", "NA"], ["2026-10-27", "2026-10-27"])
    (r,) = cs._guidance_reads(rows, cs._metric_starts(rows, ("Revenue",)), date(2026, 11, 1), 45)
    assert r.unread is not None and r.guide == cs.GUIDE_UNREAD
    assert r.period == "FQ4 2026"


@pytest.mark.parametrize("periods", [["FH1 2026", "FY 2026"], ["FY 2026", "FH1 2026"]])
def test_ra_d4_twin_a_half_year_sorts_in_time_order(periods: list[str]) -> None:
    """(review) CIQ heads half-year guides 'FH1'/'FH2' (70 Guidance header cells on disk,
    2026-11-10); the order sorted them after every FY, so FY 2026 took the read from FH1 2026."""
    guides: dict[str, Any] = {"FH1 2026": "100.00 - 110.00", "FY 2026": "200.00 - 220.00"}
    rows = _block(periods, [guides[p] for p in periods], ["2026-02-10", "2026-02-10"])
    (r,) = cs._guidance_reads(rows, cs._metric_starts(rows, ("Revenue",)), date(2026, 3, 1), 45)
    assert (r.period, r.same_day) == ("FH1 2026", (("FY 2026", "'200.00 - 220.00'"),))
    ordered = ["FQ1 2026", "FQ2 2026", "FH1 2026", "FQ3 2026", "FQ4 2026", "FH2 2026", "FY 2026",
               "FQ1 2027", "Non-periodic"]
    scrambled = ["Non-periodic", "FY 2026", "FQ1 2027", "FH2 2026", "FQ4 2026", "FH1 2026",
                 "FQ3 2026", "FQ2 2026", "FQ1 2026"]
    assert sorted(scrambled, key=cs._period_order) == ordered


def _ratio_bundle(inc_header: list[str], dps: list[object]) -> CiqBundle:
    from pathlib import Path

    from vinci.dossier.ciq import CiqFormat, CiqWorkbook

    rat: list[list[Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2023", "12 months Dec-31-2024",
         "LTM 12 months Mar-31-2025"],
        ["Return on Equity %", 0.18, 0.20, 0.21],
        ["Return on Capital %", 0.08, 0.09, 0.10],
        ["Dividend per Share", 0.10, 0.12, "NM"],
    ]
    inc: list[list[Any]] = [["For the Fiscal Period", *inc_header], ["Dividends per Share", *dps]]
    p = Path("/fake/Financials.xls")
    wb = CiqWorkbook(kind="financials", path=p, fmt=CiqFormat.BIFF_XLS, freq="annual")
    return CiqBundle(ticker="X", workbooks=(wb,),
                     _cache={p: {"Ratios": rat, "Income Statement": inc}})


def test_ra_d2_twin_a_period_the_income_statement_does_not_state_is_no_read_never_none() -> None:
    """(review) (+) A Ratios column whose period no Income Statement column states — absent, or
    stated twice — reads "—", and the key ratios say nothing of a dividend: no column is not a
    non-payer. (−) The Income Statement's own 'NA' at that period still reads "none"."""
    fy = ["12 months Dec-31-2023", "12 months Dec-31-2024"]
    for header, dps in ((fy, [1.00, 1.10]),
                        ([*fy, "LTM 12 months Mar-31-2025", "LTM 12 months Mar-31-2025"],
                         [1.00, 1.10, 1.15, 1.16])):
        b = _ratio_bundle(header, dps)
        table = cs.return_ratios(b).value
        assert table is not None
        assert next(r for r in table.rows if r.label == "Dividend/sh").cells == [
            "1.00", "1.10", "—"]
        assert "dividend" not in (cs.key_ratios(b).value or "")
    b = _ratio_bundle([*fy, "LTM 12 months Mar-31-2025"], [1.00, 1.10, "NA"])
    table = cs.return_ratios(b).value
    assert table is not None
    assert next(r for r in table.rows if r.label == "Dividend/sh").cells == ["1.00", "1.10", "none"]
    assert "dividend: none" in (cs.key_ratios(b).value or "")
