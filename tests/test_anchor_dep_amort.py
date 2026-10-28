"""The anchor's D&A reads the screen's guarded line, and must be the filer's newest fiscal year.

`anchor._latest_dep_amort` picked among the combined D&A aliases and the `Depreciation` +
`AmortizationOfIntangibleAssets` split by vintage alone, so a split fresher than every combined
alias won however little of D&A it held. It now reads `concepts.current_annual` (the split only
where the filer proved it continues the combined line, #822), and refuses a year behind the
filer's newest, because the anchor adds this D&A to LTM EBIT. A refusal is the reason; the CIQ
bridge then fills the hole
(`docs/records/2026-10-27-the-anchors-dep-amort-reads-the-guarded-line.md`).

Pins run on FROZEN real filers (`tests/fixtures/retagged_legs/`, README there). The one CIQ figure
used is CNXC's, as its workbook's bridge read it on 2026-10-27.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date
from typing import Any

from vinci.dossier import ciq_balance as cb
from vinci.dossier.anchor import NO_COMBINED_DEP_AMORT, _bridge_inputs, _latest_dep_amort
from vinci.edgar.concepts import ANNUAL_STALE_DAYS

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "retagged_legs"

#: CNXC's D&A as `anchor.ciq_bridge` read its workbook on 2026-10-27 — the workbook's last annual
#: column, which is the LTM to 2026-08-31 ($660.433M is its FY25 column).
CNXC_CIQ_DA = 642.82


def _facts(ticker: str) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((FIXTURES / f"{ticker}.json").read_text())
    return facts


def _ciq(da: float, period: str | None = None, end: date | None = None) -> cb.CiqFacts:
    return cb.CiqFacts(ticker="X", as_of=None, source_file="wb.xls", source_sha256="sha",
                       facts={"d_and_a": cb.CiqFact(value=da, unit="$M", basis="b", source="s",
                                                    period=period, period_end=end)})


def _page(end: str, is_ltm: bool) -> dict[str, Any]:
    """The part of a committed page `_bridge_inputs` reads for the window: the annual table's last
    actual column and the end `statement_reconciliation` states for it — the twelve months the
    anchor's LTM EBIT and revenue cover, which its D&A must cover too (2026-10-28)."""
    col = "LTM" if is_ltm else "FY"
    return {"financial_summary": {
        "annual": {"value": {"columns": [col], "is_estimate": [False], "rows": []}},
        "statement_reconciliation": {"rows": [
            {"line": "revenue", "column": col, "period_end": end, "is_ltm": is_ltm}]}}}


#: The windows the five filers' pages state (CNXC's and WERN's committed pages; Scotts', Ecovyst's
#: and FUBO's fiscal years, which are not committed pages).
WINDOWS = {"SMG": _page("2025-09-30", False), "ECVT": _page("2025-12-31", False),
           "CNXC": _page("2026-08-31", True), "WERN": _page("2026-06-30", True)}


def test_a_proven_split_is_the_anchors_d_and_a() -> None:
    """Scotts: the split continues `DepreciationAndAmortization`, which stops at FY2024 where the
    two match exactly ($80.6M). The anchor reads FY2025's $75.0M and names the line it continues."""
    da = _bridge_inputs(WINDOWS["SMG"], _facts("SMG"))["d_and_a"]
    assert da.value == 75.0
    src = da.source or ""
    assert "split, FY2025" in src and "continues DepreciationAndAmortization" in src
    assert "CHOSEN BY VINTAGE" not in src, "the split continues that line; it did not beat it"


def test_a_component_split_and_a_year_old_line_are_both_refused() -> None:
    """Ecovyst: the old reader took the split for FY2025 ($76.432M), which was $68.383M against a
    combined $89.362M in FY2024 — a component. The split is refused (#822), and the combined line's
    FY2024 is a year behind the filer's FY2025, so it is refused too: the anchor adds D&A to LTM
    EBIT. EDGAR has no D&A, and says why — never the stale combined figure."""
    got = _latest_dep_amort(_facts("ECVT"))
    assert isinstance(got, str)
    assert got.startswith("newest D&A is DepreciationDepletionAndAmortization for the year to "
                          "2024-12-31, 365d behind the filer's newest fiscal year")
    da = _bridge_inputs(WINDOWS["ECVT"], _facts("ECVT"))["d_and_a"]
    assert da.value is None and da.source == (
        f"UNKNOWN — no EDGAR D&A over the fiscal year to 2025-12-31 — {got}")


def test_a_withheld_edgar_d_and_a_is_filled_by_the_ciq_bridge_and_says_why() -> None:
    """The bridge fills the hole, stamped as vendor, and its source says EDGAR's figure was
    WITHHELD (not absent), naming the reason."""
    bridge = _bridge_inputs(WINDOWS["ECVT"], _facts("ECVT"), _ciq(100.0, "FY", date(2025, 12, 31)))
    assert bridge["d_and_a"].value == 100.0 and "d_and_a" in bridge["vendor_filled"]
    assert ("EDGAR D&A withheld — no EDGAR D&A over the fiscal year to 2025-12-31 — newest D&A is "
            "DepreciationDepletionAndAmortization") in (bridge["d_and_a"].source or "")


def test_a_filer_with_no_combined_line_reads_the_ciq_bridge() -> None:
    """CNXC never tagged a combined D&A line, so its split has nothing to continue and nothing to
    be checked against: EDGAR has no D&A, and says that — not "no D&A tag", which would send a
    reader looking for a tag CNXC does file. The bridge supplies the workbook's figure, $642.82M —
    the LTM to 2026-08-31 — where the page carried the EDGAR split's FY2025 $660.433M."""
    facts = _facts("CNXC")
    assert _latest_dep_amort(facts) == NO_COMBINED_DEP_AMORT
    da = _bridge_inputs(WINDOWS["CNXC"], facts, _ciq(CNXC_CIQ_DA, "LTM", date(2026, 8, 31)))[
        "d_and_a"]
    assert da.value == CNXC_CIQ_DA
    src = da.source or ""
    assert src.startswith("CIQ Financials->Cash Flow (vendor basis; EDGAR D&A withheld — no "
                          "EDGAR D&A over the trailing twelve months to 2026-08-31 — no combined "
                          "D&A line")


def test_the_newest_year_cutoff_sits_in_the_measured_gap() -> None:
    """Anchor D&A years against the filer's newest fiscal year, 2,161 filers: 1,620 within 29 days,
    one at 181, NONE from 300 to 349, then 11 at 350–371. The cutoff (a whole shortest fiscal year)
    sits at the top of that gap."""
    assert 299 < ANNUAL_STALE_DAYS <= 350


def test_a_d_and_a_its_concept_has_reported_past_is_refused() -> None:
    """FUBO moved its year end to September: its newest annual D&A is calendar 2024 ($38.548M, on
    the committed anchor) while the concept carries quarters to 2026-06-30. That year is not the
    current one (#817's check), though it IS the filer's newest fiscal year — so the newest-year
    cutoff alone would serve it."""
    got = _latest_dep_amort(_facts("FUBO"))
    assert isinstance(got, str)
    assert got.startswith("stale annual dep_amort: DepreciationAndAmortization for the year to "
                          "2024-12-31, 546d behind")


#: The header cells over the column `ciq_balance` reads, verbatim from each workbook's annual Cash
#: Flow sheet (2026-10-27): a trailing column on CNXC and WERN, a fiscal year on NKE.
HEADERS = {"CNXC": "LTM\n12 months\nAug-31-2026", "WERN": "LTM\n12 months\nJun-30-2026",
           "NKE": "12 months\nMay-31-2026"}
#: The bridge's D&A for CNXC and WERN on those columns — the figures `anchor.ciq_bridge` returned.
BRIDGE_DA = {"CNXC": 642.82, "WERN": 313.717}


def test_the_ciq_period_is_read_off_the_columns_own_header() -> None:
    """REVIEW FINDING (Codex, #830; operator ruling): the bridge reads the annual sheet's LAST
    column, which is `LTM 12 months` on 33 of the 35 workbooks on file, and the anchor labelled
    it "consolidated latest FY". The period is now a STRUCTURED value read from that column's own
    header cell — never re-parsed from a display string — and a fiscal-year column says so."""
    assert cb.header_period(HEADERS["CNXC"]) == ("LTM", date(2026, 8, 31))
    assert cb.header_period(HEADERS["WERN"]) == ("LTM", date(2026, 6, 30))
    assert cb.header_period(HEADERS["NKE"]) == ("FY", date(2026, 5, 31))
    assert cb.header_period("") == (None, None)
    rows = [["For the Fiscal Period Ending\n", "12 months\nAug-31-2025", HEADERS["CNXC"]],
            ["Depreciation & Amort., Total", 660.433, BRIDGE_DA["CNXC"]]]
    assert cb.pick_with_period(rows, "Depreciation & Amort., Total") == (
        BRIDGE_DA["CNXC"], "LTM", date(2026, 8, 31))


def test_a_bridged_d_and_a_is_stored_with_its_trailing_period() -> None:
    """End to end on CNXC's and WERN's frozen companyfacts: EDGAR's D&A is withheld (no combined
    line for the split to continue), the bridge fills it, and the stored basis names the trailing
    twelve months to the column's date — CNXC's to 2026-08-31, WERN's to 2026-06-30."""
    for t, end in (("CNXC", "2026-08-31"), ("WERN", "2026-06-30")):
        period, period_end = cb.header_period(HEADERS[t])
        ciq = cb.CiqFacts(ticker=t, as_of=None, source_file="wb.xls", source_sha256="sha",
                          facts={"d_and_a": cb.CiqFact(value=BRIDGE_DA[t], unit="$M", basis="b",
                                                       source="s", period=period,
                                                       period_end=period_end)})
        da = _bridge_inputs(WINDOWS[t], _facts(t), ciq)["d_and_a"]
        assert da.value == BRIDGE_DA[t]
        assert da.basis == (f"consolidated trailing twelve months to {end} (CIQ workbook, "
                            f"vendor basis)"), t
    # ⊖ a fiscal-year column is stated as one, where the page's window is that fiscal year
    fy = _ciq(747.0, "FY", date(2026, 5, 31))
    assert _bridge_inputs(_page("2026-05-31", False), _facts("CNXC"), fy)["d_and_a"].basis == (
        "consolidated fiscal year to 2026-05-31 (CIQ workbook, vendor basis)")
    # ⊖ a CIQ D&A whose header states no period, or no date, is not over the window: no fill, and
    #   the UNKNOWN says what CIQ's column was
    for ciq, says in ((_ciq(1.0), "period not stated"),
                      (_ciq(1.0, "LTM"), "trailing twelve months, end date not read")):
        da = _bridge_inputs(WINDOWS["CNXC"], _facts("CNXC"), ciq)["d_and_a"]
        assert da.value is None
        assert "CIQ's D&A is not over that window either" in (da.source or "")
        assert says in (da.source or "")


def test_the_anchors_d_and_a_covers_the_window_its_ltm_ebit_covers() -> None:
    """THE RULE (2026-10-28): the anchor adds D&A to LTM EBIT and divides it by LTM revenue, so it
    must cover the same twelve months. A CIQ D&A over another window — the workbook's fiscal year
    where the page's column is the LTM — is refused, never mixed; and a page that states no window
    gets no D&A at all."""
    fy_col = _ciq(BRIDGE_DA["CNXC"], "FY", date(2025, 8, 31))
    da = _bridge_inputs(WINDOWS["CNXC"], _facts("CNXC"), fy_col)["d_and_a"]
    assert da.value is None
    assert (da.source or "").startswith(
        "UNKNOWN — no EDGAR D&A over the trailing twelve months to 2026-08-31")
    off_by_a_quarter = _ciq(BRIDGE_DA["CNXC"], "LTM", date(2026, 5, 31))
    assert _bridge_inputs(WINDOWS["CNXC"], _facts("CNXC"), off_by_a_quarter)[
        "d_and_a"].value is None
    no_window = _bridge_inputs({}, _facts("CNXC"), _ciq(BRIDGE_DA["CNXC"], "LTM",
                                                         date(2026, 8, 31)))["d_and_a"]
    assert no_window.value is None
    assert "the page states no window" in (no_window.source or "")
