"""The dividend per share is the dividend, and CIQ's 'NA' is not stated (fix request 2, order 4:
audit RA-D2; the operator's ruling on #967's Codex P1, 2026-11-11). Split from #967.

* RA-D2 — CIQ's Ratios sheet has no dividend level: its 'Dividend per Share' rows are growth rates
  (YoY, then two-, three- and five-year CAGRs), and the first was printed as "Dividend/sh". V's
  page read 0.19, 0.15, 0.13, 0.14 against dividends of 1.87, 2.15, 2.44, 2.79; GOOGL's 0.38 and
  0.05 against 0.83 and 0.86. The level is the Income Statement's 'Dividends per Share', for the
  same periods. A growth cell at 'NM' printed "dividend: none" for a payer.
* THE 'NA' RULING — CIQ's 'NA' in 'Dividends per Share' means NOT STATED: it reads "—" (UNKNOWN),
  never zero and never "none". A page says no dividend only where CIQ states 0 or a dash. On the
  exports on disk CIQ writes neither: every non-payer's cell, and quarters that payers paid (MCK's
  to 2026-09-30), read 'NA'.

Real-export pins read the export on disk as it stands (skip where absent, as on CI); constructed
twins run everywhere.
"""
from __future__ import annotations

from typing import Any

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, clean_num
from vinci.dossier.manual_store import LocalFolderStore


def _tnote(s: cs.Sourced[Any]) -> str:
    """The ratio TABLE's own note, which the renderers print under it (never the field's)."""
    assert s.note is None, f"a note on the field is never rendered: {s.note}"
    return (s.value.note if s.value is not None else None) or ""


def _real(ticker: str) -> CiqBundle:
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)



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
    # a level CIQ marks 'NA' is not stated: "—", never "none" (the operator's ruling, 2026-11-11)
    assert row.cells == [f"{v:.2f}" if v is not None else "—" for v in want]
    growth = cs._find_row(rat, "Dividend per Share")
    assert growth is not None
    paid = [(v, clean_num(rat[growth][c])) for v, c in zip(want, cols, strict=True) if v]
    assert paid and all(f"{v:.2f}" != f"{g:.2f}" for v, g in paid if g is not None), paid


def test_ra_d2_a_payer_whose_growth_reads_nm_is_not_said_to_pay_none() -> None:
    """(+) V's Ratios growth cell at the pinned column set to 'NM': no "dividend: none". (−) AMZN,
    whose Income Statement reads 'NA', is not said to pay none either: 'NA' is not stated."""
    b = _real("V")
    rat = b.sheet("financials", "Ratios", freq="annual")
    for r in rat:
        if r and str(r[0]).strip() == "Dividend per Share":
            r[-1] = "NM"
    assert "dividend: none" not in (cs.key_ratios(b).value or "")
    amzn = cs.key_ratios(_real("AMZN")).value or ""
    assert "dividend: none" not in amzn
    assert "dividend: not stated (the Income Statement reads 'NA')" in amzn, amzn



def test_ra_d2_twin_a_period_the_income_statement_does_not_state_is_no_read_never_none() -> None:
    """(review) (+) A Ratios column whose period no Income Statement column states — absent, or
    stated twice — reads "—", and the key ratios say nothing of a dividend: no column is not a
    non-payer. (−) The Income Statement's own 'NA' at that period reads "—" and "not stated" —
    'NA' is not stated (the operator's ruling, 2026-11-11)."""
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
    assert next(r for r in table.rows if r.label == "Dividend/sh").cells == ["1.00", "1.10", "—"]
    assert "dividend: not stated" in (cs.key_ratios(b).value or "")


def test_ra_d2_the_dividend_cites_the_income_statement_it_is_read_from() -> None:
    """Review round 0b: the row and the "dividend: none" status come from the Income Statement, so
    each source_ref names it (CLAUDE.md: source-bind everything)."""
    v = cs.return_ratios(_real("V"))
    assert "Income Statement 'Dividends per Share'" in (v.source_ref or ""), v.source_ref
    amzn = cs.key_ratios(_real("AMZN"))
    assert "dividend: not stated" in (amzn.value or "")
    assert "Income Statement 'Dividends per Share'" in (amzn.source_ref or ""), amzn.source_ref


def test_ra_d2_mcks_ltm_dividend_is_ciqs_figure_and_says_which_quarter_it_lacks() -> None:
    """The operator's ruling (2026-11-10): MCK's LTM dividend is printed as CIQ states it, with a
    note. On MCK's export as it stands, a quarter of the four ending at the LTM column reads no
    figure; the note names it and the sum of the quarters stated, never what CIQ summed. (−) A
    payer whose four quarters are all stated (V) carries no note."""
    note = _tnote(cs.return_ratios(_real("MCK")))
    assert "is CIQ's own LTM figure, printed as stated" in note, note
    assert "for the quarter to" in note and "it states sum" in note, note
    assert _tnote(cs.return_ratios(_real("V"))) == ""


def test_ra_d2_twin_an_ltm_dividend_over_a_marked_quarter_is_noted() -> None:
    from tests.fixtures.ciq_synthetic import generate as gen

    b = CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))
    inc = b.sheet("financials", "Income Statement", freq="annual")
    q = b.sheet("financials", "Income Statement", freq="quarterly")
    ahdr, qhdr = cs._period_header(inc), cs._period_header(q)
    assert ahdr is not None and qhdr is not None
    inc.append(["Dividends per Share", *([0.2] * (len(inc[ahdr]) - 2)), 0.4])
    q.append(["Dividends per Share", *([0.1] * (len(q[qhdr]) - 2)), "NA"])
    wb = b.workbook("financials", freq="annual")
    assert wb is not None
    b._cache[wb.path]["Ratios"] = [list(inc[ahdr]), ["Return on Equity %",
                                                      *([0.1] * (len(inc[ahdr]) - 1))]]
    note = _tnote(cs.return_ratios(b))
    assert "Dividend/sh LTM to" in note and "'NA' for the quarter to" in note, note
    assert "the 3 it states sum 0.30" in note, note

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


# --- the 'NA' ruling (the operator, 2026-11-11, on #967's Codex P1) ------------------------------


def test_ra_d2_na_is_not_stated_and_never_no_dividend_on_a_real_export() -> None:
    """(+) AMZN's Income Statement reads 'NA' in every column. Before: every cell "none" and
    "dividend: none", reading 'NA' as zero. Now every cell "—", a note says CIQ states no figure,
    and the key ratios say "not stated"."""
    b = _real("AMZN")
    got = cs.return_ratios(b)
    assert got.value is not None
    row = next(r for r in got.value.rows if r.label == "Dividend/sh")
    assert row.cells and set(row.cells) == {"—"}, row.cells
    note = _tnote(got)
    assert "reads 'NA'" in note and "never read as no dividend" in note, note
    kr = cs.key_ratios(b).value or ""
    assert "dividend: none" not in kr and "dividend: not stated" in kr, kr


def test_ra_d2_twin_a_dash_or_a_zero_states_no_dividend() -> None:
    """(+) Only CIQ's own statement says no dividend: a dash, or a 0, reads "none" and "dividend:
    none". (−) 'NA' beside them reads "—": not stated."""
    fy = ["12 months Dec-31-2023", "12 months Dec-31-2024", "LTM 12 months Mar-31-2025"]
    for none_cell in ("-", 0.0):
        b = _ratio_bundle(fy, ["NA", 0.25, none_cell])
        table = cs.return_ratios(b).value
        assert table is not None
        row = next(r for r in table.rows if r.label == "Dividend/sh")
        assert row.cells == ["—", "0.25", "none"], none_cell
        assert "dividend: none" in (cs.key_ratios(b).value or ""), none_cell


def test_ra_d2_twin_an_unplaced_column_says_why_it_reads_no_figure() -> None:
    """(review) (+) A Ratios column no single Income Statement column states reads "—" AND the note
    says why — an unexplained "—" read like any missing cell. (−) Every column placed: no such
    note."""
    fy = ["12 months Dec-31-2023", "12 months Dec-31-2024"]
    note = _tnote(cs.return_ratios(_ratio_bundle(fy, [1.00, 1.10])))
    assert "1 of 3 column(s) read no figure" in note, note
    placed = _tnote(cs.return_ratios(_ratio_bundle([*fy, "LTM 12 months Mar-31-2025"],
                                                   [1.00, 1.10, 1.15])))
    assert placed == "", placed


def test_ra_d2_twin_an_ltm_over_a_dash_quarter_is_fully_stated() -> None:
    """(review) (+) A dash STATES no dividend, so an LTM over a dash quarter is four stated
    quarters and carries no note. (−) 'NA' in that quarter is noted (the twin above)."""
    from tests.fixtures.ciq_synthetic import generate as gen

    b = CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))
    inc = b.sheet("financials", "Income Statement", freq="annual")
    q = b.sheet("financials", "Income Statement", freq="quarterly")
    ahdr, qhdr = cs._period_header(inc), cs._period_header(q)
    assert ahdr is not None and qhdr is not None
    inc.append(["Dividends per Share", *([0.2] * (len(inc[ahdr]) - 2)), 0.3])
    q.append(["Dividends per Share", *([0.1] * (len(q[qhdr]) - 2)), "-"])
    wb = b.workbook("financials", freq="annual")
    assert wb is not None
    b._cache[wb.path]["Ratios"] = [list(inc[ahdr]), ["Return on Equity %",
                                                      *([0.1] * (len(inc[ahdr]) - 1))]]
    note = _tnote(cs.return_ratios(b))
    assert "Dividend/sh LTM to" not in note, note


def test_ra_d2_the_rendered_ratio_table_says_why_its_dividend_row_reads_no_figure() -> None:
    """(+) End to end (review round 0): AMZN's ratio table, rendered as the page renders it, shows
    the Dividend/sh row of "—" AND the note saying CIQ states no figure. Before the fix the note sat
    on the field, which no renderer prints, so the row read as unexplained."""
    from vinci.dossier import render

    md = "\n".join(render._fin_table_lines("Return ratios", cs.return_ratios(_real("AMZN"))))
    assert "Dividend/sh" in md and "never read as no dividend" in md, md[-600:]
