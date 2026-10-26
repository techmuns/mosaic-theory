"""CIQ's annual revenue and operating cash flow against the filings — `statement_recon`, pinned.

THE GAP (2026-10-26). Nothing set the financial summary's Revenue and CFO rows against the filings:
revenue reached a check only inside a margin and a guide, and cash flow only as the SIGN of CIQ's
LTM levered FCF against one quarter's OCF. Measured before any code, on the 27 committed pages and
the workbooks they were built from: every page's Revenue and CFO rows reproduce exactly from its
export, and CIQ carries the filer's LATEST-filed figure wherever both sides report the period.

FROZEN FIXTURES. The EDGAR side is the REAL companyfacts committed under
`tests/fixtures/companyfacts/` (public; the dates and figures below are the filers' own). The CIQ
side is a figure the test PLACES — at, beside or away from the filing figure — so no CIQ value is
copied into this file (the repo is public).
"""
from __future__ import annotations

import json
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import statement_recon as sr
from vinci.dossier.ciq import CiqUnavailableError
from vinci.dossier.refresh import statement_recon_transform

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "companyfacts"
_TJX_10K = "0000109198-26-000008"      # FY ending 2026-01-31, filed 2026-03-31
_TJX_Q2 = "0000109198-26-000048"       # 26 weeks to 2026-08-01, filed 2026-08-28


@cache
def _facts(ticker: str) -> dict[str, Any]:
    out: dict[str, Any] = json.loads((FIXTURES / f"{ticker}.json").read_text())
    return out


def _one(ticker: str, line: str, column: str, end: str, value: float, *, ltm: bool = False,
         filed_by: str = "2026-10-21") -> Any:
    fig = sr.CiqFigure(line, column, date.fromisoformat(end), ltm, value)
    rec = sr.reconcile([fig], _facts(ticker), filed_by=date.fromisoformat(filed_by))
    assert rec is not None and len(rec.rows) == 1
    return rec.rows[0]


# --- the filing figure, per period ---------------------------------------------------------------


def test_a_fiscal_year_is_the_filers_twelve_month_fact() -> None:
    """TJX's FY ending 2026-01-31: $60,372M in the 10-K — on the first alias TJX tags."""
    r = _one("TJX", "revenue", "FY26", "2026-01-31", 60372.0)
    assert (r.filing, r.construction, r.accession) == (60372.0, sr.FISCAL_YEAR, _TJX_10K)
    assert r.tag == "RevenueFromContractWithCustomerIncludingAssessedTax"
    assert r.gap == 0.0 and r.different is False and r.note is None


def test_the_ltm_is_the_year_plus_the_ytd_less_the_prior_ytd() -> None:
    """A 10-Q tags no twelve months, so TJX's LTM to 2026-08-01 is composed on ONE tag: FY $60,372M
    + 26 weeks to 2026-08-01 $29,503M − 26 weeks to 2025-08-02 $27,512M = $62,363M."""
    r = _one("TJX", "revenue", "LTM", "2026-08-01", 62363.0, ltm=True)
    assert (r.filing, r.construction, r.accession) == (62363.0, sr.COMPOSED, _TJX_Q2)
    assert r.is_ltm and r.different is False


def test_a_10q_twelve_month_column_is_read_as_the_filer_states_it() -> None:
    """Amazon's 10-Q carries its own trailing-twelve-month cash flow: read, never re-composed."""
    r = _one("AMZN", "operating_cash_flow", "LTM", "2026-06-30", 161403.0, ltm=True,
             filed_by="2026-10-09")
    assert (r.filing, r.construction) == (161403.0, sr.TRAILING)
    assert r.tag == "NetCashProvidedByUsedInOperatingActivities"


def test_a_fact_filed_after_the_date_is_never_read() -> None:
    """AS FILED BY the date: the 10-K was filed 2026-03-31 and the Q2 10-Q 2026-08-28, so the day
    before each, the period has no filing figure — stated, never filled from a later filing."""
    fy = _one("TJX", "revenue", "FY26", "2026-01-31", 60372.0, filed_by="2026-03-30")
    assert fy.filing is None and fy.note and "as filed by 2026-03-30" in fy.note
    ltm = _one("TJX", "revenue", "LTM", "2026-08-01", 62363.0, ltm=True, filed_by="2026-08-27")
    assert ltm.filing is None and ltm.note and "no twelve-month figure" in ltm.note
    assert _one("TJX", "revenue", "FY26", "2026-01-31", 60372.0, filed_by="2026-03-31").filing


def test_a_period_no_alias_reports_is_stated_never_guessed() -> None:
    """UBER's FY2016 predates its XBRL; BRBR's 10-K tags `Revenues` while its 10-Qs tag the ASC 606
    line, so no ONE tag carries the year and both year-to-dates — and tags are never spliced."""
    uber = _one("UBER", "revenue", "FY16", "2016-12-31", 1.0, filed_by="2026-10-11")
    assert uber.filing is None and uber.tag is None and uber.different is False
    brbr = _one("BRBR", "revenue", "LTM", "2026-06-30", 1.0, ltm=True, filed_by="2026-09-28")
    assert brbr.filing is None and brbr.note and "no twelve-month figure" in brbr.note


# --- the comparison -----------------------------------------------------------------------------


def test_the_tolerance_is_half_a_percent_and_a_million() -> None:
    f = 60372.0
    inside = _one("TJX", "revenue", "FY26", "2026-01-31", f * (1 + sr.DIFFERENT_SHARE) - 0.01)
    beyond = _one("TJX", "revenue", "FY26", "2026-01-31", f * (1 + sr.DIFFERENT_SHARE) + 0.01)
    assert inside.different is False and beyond.different is True
    below = _one("TJX", "revenue", "FY26", "2026-01-31", f * (1 - sr.DIFFERENT_SHARE) - 0.01)
    assert below.different is True and below.gap is not None and below.gap < 0
    # THE FLOOR: a small filer's gap over the share but under $1M is rounding, not a difference
    facts = _synthetic({"Revenues": [("2025-01-01", "2025-12-31", 100e6, "2026-02-20", "USD")]})
    under = sr.reconcile([sr.CiqFigure("revenue", "FY25", date(2025, 12, 31), False, 100.99)],
                         facts, filed_by=date(2026, 3, 1))
    over = sr.reconcile([sr.CiqFigure("revenue", "FY25", date(2025, 12, 31), False, 101.0)],
                        facts, filed_by=date(2026, 3, 1))
    assert under is not None and under.rows[0].different is False
    assert over is not None and over.rows[0].different is True


def test_a_figure_on_another_alias_is_named() -> None:
    """WERNER, a real case: CIQ's revenue is the filer's `Revenues` line, 2.5% above the ASC 606
    line the alias order reads first — a definition difference the filing itself states."""
    r = _one("WERN", "revenue", "FY24", "2024-12-31", 3030.258, filed_by="2026-09-17")
    assert r.tag == "RevenueFromContractWithCustomerExcludingAssessedTax" and r.filing == 2955.201
    assert r.different is True and r.other_tag == "Revenues" and r.earlier_accession is None


def test_a_figure_an_earlier_filing_carried_is_named() -> None:
    """LILLY recast FY2017 for the Elanco separation (an 8-K, then the 2019 10-K): $22,871.3M as
    first filed, $19,973.8M now. A CIQ figure still on the first vintage names that filing."""
    r = _one("LLY", "revenue", "FY17", "2017-12-31", 22871.3, filed_by="2026-09-30")
    assert r.filing == 19973.8 and r.different is True
    assert r.earlier_accession == "0000059478-18-000089" and r.other_tag is None
    # the restated figure is the latest one, so a CIQ figure ON it confirms
    assert _one("LLY", "revenue", "FY17", "2017-12-31", 19973.8, filed_by="2026-09-30").different \
        is False


def test_a_figure_the_filings_do_not_carry_names_nothing() -> None:
    r = _one("TJX", "revenue", "FY26", "2026-01-31", 2 * 60372.0)
    assert r.different is True and r.other_tag is None and r.earlier_accession is None


def test_the_first_alias_reporting_the_period_is_the_one_read() -> None:
    facts = _synthetic({
        "Revenues": [("2025-01-01", "2025-12-31", 110e6, "2026-02-20", "USD")],
        "RevenueFromContractWithCustomerExcludingAssessedTax": [
            ("2025-01-01", "2025-12-31", 100e6, "2026-02-20", "USD")],
        "SalesRevenueNet": [("2024-01-01", "2024-12-31", 90e6, "2025-02-20", "USD")]})
    rec = sr.reconcile([sr.CiqFigure("revenue", "FY25", date(2025, 12, 31), False, 100.0),
                        sr.CiqFigure("revenue", "FY24", date(2024, 12, 31), False, 90.0)],
                       facts, filed_by=date(2026, 3, 1))
    assert rec is not None
    assert [r.tag for r in rec.rows] == ["RevenueFromContractWithCustomerExcludingAssessedTax",
                                         "SalesRevenueNet"]


def test_only_usd_facts_are_read() -> None:
    facts = _synthetic({"Revenues": [("2025-01-01", "2025-12-31", 100e6, "2026-02-20", "EUR")]})
    rec = sr.reconcile([sr.CiqFigure("revenue", "FY25", date(2025, 12, 31), False, 100.0)],
                       facts, filed_by=date(2026, 3, 1))
    assert rec is not None and rec.rows[0].filing is None


def test_no_facts_or_no_figure_is_no_block() -> None:
    fig = sr.CiqFigure("revenue", "FY26", date(2026, 1, 31), False, 1.0)
    assert sr.reconcile([fig], None, filed_by=date(2026, 10, 21)) is None
    assert sr.reconcile([], _facts("TJX"), filed_by=date(2026, 10, 21)) is None


def _synthetic(tags: dict[str, list[tuple[str, str, float, str, str]]]) -> dict[str, Any]:
    nodes: dict[str, Any] = {}
    for tag, rows in tags.items():
        units: dict[str, list[dict[str, Any]]] = {}
        for s, e, v, f, unit in rows:
            units.setdefault(unit, []).append(
                {"start": s, "end": e, "val": v, "filed": f, "form": "10-K", "accn": f"a-{f}"})
        nodes[tag] = {"units": units}
    return {"facts": {"us-gaap": nodes}}


# --- the CIQ side: the export's own period ends, the table's own cells ------------------------


class _Bundle:
    """The two annual sheets, shaped as CIQ exports them; every other sheet is unavailable."""

    def __init__(self, sheets: dict[str, list[list[Any]]]) -> None:
        self._sheets = sheets

    def sheet(self, kind: str, name: str, freq: str | None = None) -> list[list[Any]]:
        if kind == "financials" and name in self._sheets and freq in (None, "annual"):
            return self._sheets[name]
        raise CiqUnavailableError(f"{kind}/{name} not in the synthetic bundle")

    def workbook(self, kind: str, freq: str | None = None) -> object:
        return object()


_HDR = "For the Fiscal Period Ending"


def _sheets(*, collide: bool = False) -> dict[str, list[list[Any]]]:
    """FY24, a reclassified FY25, and the LTM; the cash-flow sheet orders its columns differently
    and carries one twice. With ``collide``, two 53-week years end in one calendar year."""
    years = (["12 months\nJan-01-2022", "12 months\nDec-31-2022"] if collide else
             ["12 months\nDec-31-2024", "Reclassified\n12 months\nDec-31-2025"])
    inc = [[_HDR, *years, "LTM\n12 months\nJun-30-2026"],
           ["Total Revenue", 900.5, 1000.25, 1100.125],
           ["EBITDA", 90.0, 100.0, 110.0]]
    cf = [[_HDR, "LTM\n12 months\nJun-30-2026", *years, years[0]],
          ["Cash from Ops.", 55.0, 40.0, 50.0, 41.0]]
    return {"Income Statement": inc, "Cash Flow": cf}


def test_the_export_gives_each_figure_with_the_period_end_its_header_states() -> None:
    figs = sr.ciq_figures(_Bundle(_sheets()))  # type: ignore[arg-type]
    got = {(f.line, f.column): (f.period_end.isoformat(), f.is_ltm, f.value) for f in figs}
    assert got == {
        ("revenue", "FY24"): ("2024-12-31", False, 900.5),
        ("revenue", "FY25 (R)"): ("2025-12-31", False, 1000.25),
        ("revenue", "LTM"): ("2026-06-30", True, 1100.125),
        # FY24 appears twice on the cash-flow sheet: ambiguous, so dropped (the table's rule)
        ("operating_cash_flow", "FY25 (R)"): ("2025-12-31", False, 50.0),
        ("operating_cash_flow", "LTM"): ("2026-06-30", True, 55.0)}


def test_the_export_reads_the_cells_the_annual_table_shows() -> None:
    """THE TWIN, executed: the table `financial_summary_annual` builds from an export and the
    figures `ciq_figures` reads from it are the same — the back-fill's proof rests on it."""
    from vinci.dossier.ciq_sheets import financial_summary_annual

    for collide in (False, True):
        bundle = _Bundle(_sheets(collide=collide))
        table = financial_summary_annual(bundle).value  # type: ignore[arg-type]
        assert table is not None
        figs = sr.ciq_figures(bundle)  # type: ignore[arg-type]
        assert {(f.line, f.column): f.value for f in figs} == sr.table_figures(
            table.model_dump(mode="json"))
    # two fiscal years labelled alike name no one period: neither is read on either side
    collided = {f.column for f in sr.ciq_figures(_Bundle(_sheets(collide=True)))}  # type: ignore[arg-type]
    assert collided == {"LTM"}


def test_the_tables_figures_are_its_actual_columns_only() -> None:
    table = {"columns": ["FY25", "LTM", "FY26E"], "is_estimate": [False, False, True],
             "rows": [{"label": "Revenue ($M)", "values": [10.0, None, 12.0]},
                      {"label": "CFO ($M)", "values": [3.0, 4.0, 5.0]},
                      {"label": "EBITDA ($M)", "values": [1.0, 1.0, 1.0]}]}
    assert sr.table_figures(table) == {("revenue", "FY25"): 10.0,
                                       ("operating_cash_flow", "FY25"): 3.0,
                                       ("operating_cash_flow", "LTM"): 4.0}
    assert sr.table_figures(None) == {}


# --- the back-fill: proved the page's own export, or refused and named -------------------------


class _Edgar:
    def __init__(self, ticker: str) -> None:
        self._ticker = ticker

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return _facts(self._ticker)


#: A page whose annual table carries TJX's FILED figures in its two actual columns — EDGAR's public
#: numbers standing in for CIQ's, so the proof and the rebuild run without a licensed figure.
def _tjx_doc(block: dict[str, Any] | None = None) -> dict[str, Any]:
    fs: dict[str, Any] = {"annual": {"value": {
        "columns": ["FY26", "LTM", "FY27E"], "is_estimate": [False, False, True],
        "rows": [{"label": "Revenue ($M)", "values": [60372.0, 62363.0, 64000.0]}]}}}
    if block is not None:
        fs["statement_reconciliation"] = block
    return {"ticker": "TJX", "cik": "0000109198", "assembled_at": "2026-10-21T11:18:48Z",
            "mechanical": {"financial_summary": fs}}


def _tjx_figures(nudge: float = 0.0) -> list[sr.CiqFigure]:
    return [sr.CiqFigure("revenue", "FY26", date(2026, 1, 31), False, 60372.0 + nudge),
            sr.CiqFigure("revenue", "LTM", date(2026, 8, 1), True, 62363.0)]


def _run(doc: dict[str, Any], figures: Any) -> tuple[dict[str, Any], list[str]]:
    refused: list[str] = []
    t = statement_recon_transform(doc, edgar=_Edgar("TJX"), refused=refused, figures_for=figures)
    return t(doc["mechanical"]), refused


def test_the_backfill_writes_the_block_when_the_export_is_the_pages() -> None:
    out, refused = _run(_tjx_doc(), lambda _t: _tjx_figures())
    assert refused == []
    blk = out["financial_summary"]["statement_reconciliation"]
    assert blk["as_filed_by"] == "2026-10-21"
    assert [(r["column"], r["filing"], r["different"]) for r in blk["rows"]] == [
        ("FY26", 60372.0, False), ("LTM", 62363.0, False)]
    # idempotent: the block it wrote is the block it rebuilds
    again, refused = _run(_tjx_doc(blk), lambda _t: _tjx_figures())
    assert refused == [] and again["financial_summary"]["statement_reconciliation"] == blk


def test_the_backfill_refuses_an_export_that_is_not_the_pages() -> None:
    out, refused = _run(_tjx_doc(), lambda _t: _tjx_figures(nudge=0.001))
    assert "statement_reconciliation" not in out["financial_summary"]
    assert len(refused) == 1 and "does not reproduce" in refused[0] and "FY26" in refused[0]
    # a figure the page has and the export lacks is the same refusal
    out, refused = _run(_tjx_doc(), lambda _t: _tjx_figures()[1:])
    assert "statement_reconciliation" not in out["financial_summary"] and refused


def test_the_backfill_refuses_without_an_export_and_never_overwrites() -> None:
    def gone(_t: str) -> list[sr.CiqFigure]:
        raise FileNotFoundError("no folder")

    out, refused = _run(_tjx_doc(), gone)
    assert "statement_reconciliation" not in out["financial_summary"]
    assert refused and "no CIQ export" in refused[0]
    held = {"rows": [], "as_filed_by": "2026-01-01", "source_ref": "an older build"}
    out, refused = _run(_tjx_doc(held), lambda _t: _tjx_figures())
    assert out["financial_summary"]["statement_reconciliation"] == held
    assert refused and "never overwritten" in refused[0]


def test_the_backfill_reads_the_facts_as_assembly_did() -> None:
    doc = _tjx_doc()
    doc["assembled_at"] = "2026-08-27T09:00:00Z"     # the day before TJX's Q2 10-Q
    out, _r = _run(doc, lambda _t: _tjx_figures())
    rows = out["financial_summary"]["statement_reconciliation"]["rows"]
    assert rows[0]["filing"] == 60372.0 and rows[1]["filing"] is None
    with pytest.raises(Exception, match="assembled_at"):
        statement_recon_transform({"ticker": "X"}, edgar=_Edgar("TJX"), refused=[])
