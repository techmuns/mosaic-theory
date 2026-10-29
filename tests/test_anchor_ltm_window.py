"""The anchor's D&A covers the window its LTM EBIT and revenue cover — the same twelve months,
ending on the same day, or none (2026-10-28).

The anchor adds D&A to LTM EBIT (the market reconciliation's recorded EBITDA), divides it by LTM
revenue (the recorded-D&A check), and adds it to LTM revenue × margin (R1's base). It read the
latest fiscal year's D&A, so on 24 of the 27 committed anchors those three paired two windows.
EDGAR's D&A is now built over the page's window (`anchor._window_dep_amort`: the guarded annual
when it ends there, else fiscal year + year-to-date − prior year-to-date through
`statement_recon.twelve_months`); the CIQ bridge fills only with a figure over the same window
(`docs/records/2026-10-28-the-anchors-d-and-a-covers-its-ltm-window.md`).

Pins run on FROZEN real filers (`tests/fixtures/ltm_window/`, README there).
"""
from __future__ import annotations

import json
import pathlib
from datetime import date
from typing import Any

import pytest

from vinci.dossier import ciq_balance as cb
from vinci.dossier.anchor import Window, _bridge_inputs, _latest_dep_amort, _window_dep_amort

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ltm_window"


def _facts(ticker: str) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((FIXTURES / f"{ticker}.json").read_text())
    return facts


def _page(end: str, is_ltm: bool) -> dict[str, Any]:
    """The part of a committed page that states its LTM EBIT / revenue window."""
    col = "LTM" if is_ltm else "FY"
    return {"financial_summary": {
        "annual": {"value": {"columns": [col], "is_estimate": [False], "rows": []}},
        "statement_reconciliation": {"rows": [
            {"line": "revenue", "column": col, "period_end": end, "is_ltm": is_ltm}]}}}


def _fact(value: float, period: str | None, end: date | None) -> cb.CiqFact:
    return cb.CiqFact(value=value, unit="$M", basis="b", source="s", period=period,
                      period_end=end)


def _ciq(**facts: cb.CiqFact) -> cb.CiqFacts:
    return cb.CiqFacts(ticker="X", as_of=None, source_file="wb.xls", source_sha256="sha",
                       facts=facts)


def test_a_10q_filer_gets_its_trailing_d_and_a_over_the_pages_window() -> None:
    """BURL: the page's LTM EBIT and revenue end 2026-08-01. The anchor read FY2025's D&A
    ($417.871M, the year to 2026-01-31); it now reads the twelve months to 2026-08-01, the fiscal
    year + the year-to-date − the prior year-to-date on `DepreciationDepletionAndAmortization`:
    $449.908M."""
    facts = _facts("BURL")
    old = _latest_dep_amort(facts)
    assert isinstance(old, tuple) and old[0] == 417_871_000.0
    got = _window_dep_amort(facts, Window(date(2026, 8, 1), True))
    assert isinstance(got, tuple)
    assert got[0] == 449_908_000.0
    assert got[2] == ("consolidated trailing twelve months to 2026-08-01 (EDGAR: fiscal year + "
                      "year-to-date − prior year-to-date)")
    assert _bridge_inputs(_page("2026-08-01", True), facts)["d_and_a"].value == 449.908


def test_a_fiscal_year_window_reads_the_fiscal_year() -> None:
    """Where the page's last actual column IS a fiscal year (NKE's FY26), the guarded annual that
    ends there is the window's D&A — BURL's year to 2026-01-31 on that window."""
    got = _window_dep_amort(_facts("BURL"), Window(date(2026, 1, 31), False))
    assert isinstance(got, tuple) and got[0] == 417_871_000.0


def test_no_quarterly_d_and_a_to_the_window_is_refused_never_the_fiscal_year() -> None:
    """V: the page's window ends 2026-06-30, and V's D&A year-to-date reaches only 2026-03-31 on
    any alias. EDGAR has no D&A over the window, and the fiscal year's $1,220M is NOT read in its
    place; CIQ's LTM over the same window fills it."""
    facts = _facts("V")
    got = _window_dep_amort(facts, Window(date(2026, 6, 30), True))
    assert isinstance(got, str)
    assert got.startswith("no EDGAR D&A over the trailing twelve months to 2026-06-30")
    page = _page("2026-06-30", True)
    assert _bridge_inputs(page, facts)["d_and_a"].value is None
    filled = _bridge_inputs(page, facts, _ciq(d_and_a=_fact(1342.0, "LTM", date(2026, 6, 30))))
    assert filled["d_and_a"].value == 1342.0 and "d_and_a" in filled["vendor_filled"]


@pytest.mark.parametrize(("ocf", "capex", "basis"), [
    (("LTM", date(2026, 6, 30)), ("LTM", date(2026, 6, 30)),
     "trailing twelve months to 2026-06-30 (vendor basis)"),
    (("FY", date(2026, 5, 31)), ("FY", date(2026, 5, 31)),
     "fiscal year to 2026-05-31 (vendor basis)"),
    (("LTM", date(2026, 6, 30)), ("FY", date(2025, 12, 31)), None),
])
def test_the_ciq_fcf_fill_pairs_one_period(ocf: tuple[str, date], capex: tuple[str, date],
                                           basis: str | None) -> None:
    """The CIQ FCF fill reads OCF and capex off the annual sheet's rightmost valued column, which
    can differ by row: an LTM OCF less a fiscal-year capex never existed. One period → filled and
    named; two → refused, naming both."""
    facts = _facts("V")    # no EDGAR capex: the fill is reached
    ciq = _ciq(ocf=_fact(25_000.0, *ocf), capex=_fact(1_500.0, *capex))
    fcf = _bridge_inputs(_page("2026-06-30", True), facts, ciq)["ltm_fcf"]
    if basis is None:
        assert fcf.value is None
        assert "CIQ's operating cash flow and capex are not one period" in (fcf.source or "")
    else:
        assert fcf.value == 23_500.0 and fcf.basis == basis


def test_extract_carries_each_cash_flow_legs_period(monkeypatch: pytest.MonkeyPatch) -> None:
    """`extract` stamps OCF and capex with the period of the column each was read from, as it
    stamps D&A (#834), and keeps `ltm_ocf`'s one-decimal rounding so no value moves."""
    wb = (("A.xls", "a"),)   # each cell's export (audit A-D6)
    cells = {"Cash from Ops.": (25_000.04, "LTM", date(2026, 6, 30), wb),
             "Capital Expenditure": (-1_500.0, "FY", date(2025, 12, 31), wb)}
    monkeypatch.setattr(cb, "_bs", lambda b, label: (None, None, ()))
    monkeypatch.setattr(cb, "_cf_row", lambda b, label, annual: None)
    monkeypatch.setattr(cb, "_cf_cell", lambda b, label, annual: cells.get(label))
    monkeypatch.setattr(cb, "_sourced", lambda b, fn: None)

    class _NoWorkbook:
        def workbook(self, kind: str, freq: str | None = None) -> None:
            return None

    got = cb.extract(_NoWorkbook(), "X")  # type: ignore[arg-type]
    assert (got.facts["ocf"].value, got.facts["ocf"].period, got.facts["ocf"].period_end) == (
        25_000.0, "LTM", date(2026, 6, 30))
    assert (got.facts["capex"].value, got.facts["capex"].period) == (1_500.0, "FY")
    assert got.facts["ocf"].workbooks == got.facts["capex"].workbooks == wb


def test_the_window_is_the_last_actual_column_and_a_kind_mismatch_is_refused() -> None:
    """The window is the column LTM EBIT and revenue are read from — the annual table's LAST actual
    column, never its first — and a CIQ figure must be the same KIND of twelve months as well as
    end on the same day: an LTM column ending on a fiscal year's last day is not that year."""
    from vinci.dossier.anchor import _page_window

    two = {"financial_summary": {
        "annual": {"value": {"columns": ["FY25", "LTM", "FY26E"],
                             "is_estimate": [False, False, True], "rows": []}},
        "statement_reconciliation": {"rows": [
            {"line": "revenue", "column": "FY25", "period_end": "2026-01-31", "is_ltm": False},
            {"line": "revenue", "column": "LTM", "period_end": "2026-08-01", "is_ltm": True}]}}}
    assert _page_window(two) == Window(date(2026, 8, 1), True)
    same_day_wrong_kind = _ciq(d_and_a=_fact(747.0, "LTM", date(2026, 5, 31)))
    assert _bridge_inputs(_page("2026-05-31", False), _facts("V"),
                          same_day_wrong_kind)["d_and_a"].value is None


def test_a_bridged_input_names_the_export_it_was_read_from() -> None:
    """Audit A-D6, at the anchor: the CIQ bridge stamped D&A and FCF with the QUARTERLY export
    (GOOGL's D&A, IT's FCF), though both are read off the ANNUAL Cash Flow. Read here through the
    real reader on the synthetic issuer's exports (`tests/fixtures/ciq_synthetic/`), whose LTM
    column ends 2026-08-31, against V's frozen filings, which carry neither D&A nor capex to that
    day, so the bridge fills both."""
    from tests.fixtures.ciq_synthetic import generate as gen
    from vinci.dossier.ciq import CiqBundle

    annual, quarterly = (gen.HERE / gen.ANNUAL_XLS), (gen.HERE / gen.QUARTERLY_XLS)
    ciq = cb.extract(CiqBundle.from_files(gen.TICKER, [annual, quarterly]), gen.TICKER)
    got = _bridge_inputs(_page("2026-08-31", True), _facts("V"), ciq)
    assert {"d_and_a", "ltm_fcf"} <= set(got["vendor_filled"])
    for key in ("d_and_a", "ltm_fcf"):
        assert annual.name in got[key].source, got[key].source
        assert quarterly.name not in got[key].source, got[key].source
