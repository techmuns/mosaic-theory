"""A sheet's settings block is found wherever its first filled row is, and a missing tab is said
(fix request 2, order 5: audits RA-D12 and RA-D7; 2026-11-10).

* RA-D12 — the unit line, the "Period Type:" cell, the Capital Structure `Source` note, the comps
  "As-Of Date:", the Estimates banner and the Market Summary were each searched in a fixed span from
  row 0. With 30 blank rows inserted above the company line (document 7's "header moved down"),
  every span read blanks: the bridge said "unit: unstated" of sheets stating Millions, the Capital
  Structure source read "()", and `consensus_levels` read empty. Each span now starts at
  `ciq.sheet_top`, the first filled row, and keeps its length.
* RA-D7 — with 'Cash Flow' or 'Trends' renamed, the annual summary stayed PRESENT with fewer rows, a
  note and a source naming the sheet it had not read; the recommendation and the rating counts
  dropped from the consensus lines; and the bridge's operating cash flow and capex were missing
  with no reason. Each now names the sheet the export lacks.

The real-export pins mutate SMPL's and LLY's sheets in memory, read-only, and skip where the
licensed folder is absent, as on CI. The synthetic twins run everywhere.
"""
from __future__ import annotations

import contextlib
import io
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_balance as cb
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, CiqFormat, period_type, read_sheets, sheet_top, stated_unit
from vinci.dossier.manual_store import LocalFolderStore

_SHEETY = {CiqFormat.BIFF_XLS, CiqFormat.OOXML}


def _loaded(b: CiqBundle) -> CiqBundle:
    """Every spreadsheet of the bundle read into its cache, so a mutation reaches each sheet."""
    for w in b.workbooks:
        if w.fmt in _SHEETY and w.path not in b._cache:
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


def _shift(b: CiqBundle, n: int) -> CiqBundle:
    """Document 7's mutation: `n` blank rows inserted above every sheet's first row."""
    for sheets in b._cache.values():
        for name, rows in list(sheets.items()):
            width = max((len(r) for r in rows[:20]), default=1)
            sheets[name] = [[""] * width for _ in range(n)] + rows
    return b


def _rename(b: CiqBundle, kind: str, freq: str | None, sheet: str) -> CiqBundle:
    w = b.workbook(kind, freq=freq)
    assert w is not None, kind
    sheets = b._cache[w.path]
    sheets[f"{sheet} (renamed)"] = sheets.pop(sheet)
    return b


def _header_reads(b: CiqBundle) -> dict[str, Any]:
    """The readers whose header search was a fixed span from row 0."""
    facts = cb.extract(b, b.ticker)
    instruments, _summary, detail_as_of = cs.capital_structure_ciq(b)
    return {
        "bridge unit lines": [c for c in facts.checks if c.startswith("unit")]
                             + [f for f in facts.failures if f.startswith("UNIT")],
        "stated units": cb._stated_units(b),
        "period types": {w.freq: [period_type(rows) for rows in b._cache[w.path].values()]
                         for w in b.workbooks if w.kind == "financials"},
        "capital structure as-of": (detail_as_of, instruments.source_ref),
        "consensus levels": sorted(cs.consensus_levels(b)),
        "consensus block found": cs.consensus_block(b) is not None,
        "comps as-of": cs.comps_as_of_date(b),
        "comps stamp": cs.comps_export_stamp(b),
        "consensus net-debt check ran": cs._consensus_net_debt_check(b) is not None,
        "stated currency": cs.stated_currency(b),
    }


# --- RA-D12: the settings block is found from the sheet's first filled row ----------------------


@pytest.mark.parametrize("ticker", ["SMPL", "LLY"])
def test_ra_d12_thirty_blank_rows_above_every_sheet_change_no_header_read(ticker: str) -> None:
    """(+) Before: 9 of these 10 reads moved on every folder on disk (the unit said "unstated", the
    Capital Structure source read "()", the consensus levels and the comps as-of were empty)."""
    want = _header_reads(_real(ticker))
    assert want["capital structure as-of"][0], "the unshifted export states a Source note"
    assert want["consensus levels"], "the unshifted export identifies its consensus block"
    assert _header_reads(_shift(_real(ticker), 30)) == want


def test_ra_d12_twin_the_synthetic_exports_read_the_same_thirty_rows_down() -> None:
    want = _header_reads(_synthetic())
    assert [u for _w, u in want["stated units"]] == ["Millions"] * 6
    got = _shift(_synthetic(), 30)
    assert _header_reads(got) == want
    assert cs._declared_current_fy(got.sheet("estimates", "Consensus")) == 2027


def test_ra_d12_twin_the_span_keeps_its_length_from_the_first_filled_row() -> None:
    """(−) The span moves with the first filled row; it does not grow into the sheet's body. A unit
    line 14 rows below the company line is outside the settings block and is not read."""
    company = ["Zinnober Fixture Works Inc. (NasdaqGS:ZZFX)", ""]
    unit = ["In Millions of the reported currency, except per share items.", ""]
    blank = ["", ""]
    assert stated_unit([blank] * 30 + [company, unit]) == "Millions"
    assert stated_unit([blank] * 30 + [company] + [["Total Revenue", "1"]] * 13 + [unit]) is None
    assert stated_unit([company] + [["Total Revenue", "1"]] * 13 + [unit]) is None


def test_ra_d12_twin_a_blank_sheet_has_no_top_and_states_nothing() -> None:
    """(−) An all-blank sheet (blank strings and None, as xlrd and openpyxl give them) has no first
    filled row: nothing is read from it."""
    rows: list[list[Any]] = [["", None, "\xa0"]] * 20
    assert sheet_top(rows) == len(rows)
    assert stated_unit(rows) is None and period_type(rows) is None


# --- RA-D7: a renamed tab is said ---------------------------------------------------------------


def test_ra_d7_a_renamed_cash_flow_tab_is_named_by_the_summary_and_the_bridge() -> None:
    """(+) Before: the summary was PRESENT with its CFO, Capex, FCF and D&A rows gone, its note
    silent and its source still naming 'Cash Flow'; the bridge's `unavailable` was empty."""
    b = _rename(_real("SMPL"), "financials", "annual", "Cash Flow")
    fs = cs.financial_summary_annual(b)
    assert fs.value is not None
    assert "no 'Cash Flow' sheet" in fs.value.note, fs.value.note
    assert "Cash Flow" not in (fs.source_ref or ""), fs.source_ref
    labels = {r.label for r in fs.value.rows}
    assert not {"CFO ($M)", "Capex ($M)"} & labels
    # the consensus-basis rows read Trends alone and stay, so the note denies only the actuals
    # (review round 0: it read "no CFO, Capex, FCF or D&A rows" above an FCF and a D&A row)
    assert {"FCF (consensus basis) ($M)", "D&A (consensus basis) ($M)"} <= labels, labels
    assert "no CFO or Capex rows, and no FCF or D&A actuals:" in fs.value.note, fs.value.note
    facts = cb.extract(b, b.ticker)
    for key in ("ocf", "capex"):
        assert key not in facts.facts
        assert "no 'Cash Flow' sheet" in facts.unavailable.get(key, ""), facts.unavailable


def test_ra_d7_a_renamed_trends_tab_is_named_where_the_recommendation_was() -> None:
    """(+) Before: the recommendation and the rating counts dropped from the consensus lines, and
    the summary's note still described estimate columns read from Trends."""
    b = _rename(_real("SMPL"), "estimates", None, "Trends")
    view = cs.consensus_view(b)
    assert view.value is not None and "Recommendation: not read" in view.value, view.value
    assert "no 'Trends' sheet" in view.value
    stats = cs.consensus_stats(b)
    assert stats.value is not None and "Ratings: not read" in stats.value, stats.value
    fs = cs.financial_summary_annual(b)
    assert fs.value is not None and fs.value.note.startswith("no estimate columns"), fs.value.note
    assert "Trends" not in (fs.source_ref or "").split("(annual)")[1], fs.source_ref


def test_ra_d7_an_export_with_every_tab_reads_as_before() -> None:
    """(−) Nothing is renamed: the note and the source are the sentences every page carries."""
    fs = cs.financial_summary_annual(_real("SMPL"), as_of="2026-11-04")
    assert fs.value is not None
    assert fs.value.note == ("E = consensus (Estimates→Trends 'Current'), as-of 2026-11-04; "
                             "(R) = Reclassified basis")
    assert fs.source_ref == ("CIQ Financials→Income Statement + Cash Flow (annual) + "
                             "Estimates→Trends (FY E)")
    view = cs.consensus_view(_real("SMPL"))
    assert view.value is not None and "Recommendation: not read" not in view.value


def test_ra_d7_twin_the_synthetic_summary_names_a_missing_cash_flow_sheet() -> None:
    b = _rename(_synthetic(), "financials", "annual", "Cash Flow")
    fs = cs.financial_summary_annual(b)
    assert fs.value is not None and "no 'Cash Flow' sheet" in fs.value.note, fs.value.note
    assert fs.source_ref == "CIQ Financials→Income Statement (annual) + Estimates→Trends (FY E)"
    facts = cb.extract(b, b.ticker)
    assert "no 'Cash Flow' sheet" in facts.unavailable.get("ocf", ""), facts.unavailable


def test_ra_d7_twin_the_synthetic_recommendation_names_a_missing_trends_sheet() -> None:
    b = _rename(_synthetic(), "estimates", None, "Trends")
    got = cs._listing_rating(b)
    assert got is not None and got[0] is None and got[2] is not None
    assert "no 'Trends' sheet" in got[2], got

