"""A CIQ PRESS-RELEASE INCOME STATEMENT IS REFUSED, AND EACH LTM IS CHECKED AGAINST ITS QUARTERS
(2026-10-30, operator ruling "go ahead with this fix then").

CIQ heads a column built from an earnings release 'Press Release', and the release carries fewer
lines than the filing: GOOGL's LTM to Sep-30-2026 read its FY25 gain on investments, 24,620.0,
where its quarters sum to 138,156.0 without Q3. The filed LTM it replaced reconciles exactly. The
reader dropped the word ('LTM' either way), so the page, the materiality guard and the anchor read
a preliminary column as a filed one.

The pins run on FROZEN rows of real exports (`tests/fixtures/ciq_ltm_quarters.json`: each Income
Statement's period-header row whole, and the few rows a pin reads with values only in the LTM,
newest-fiscal-year and newest-five-quarter cells), built into the REAL `CiqBundle`, and on the
REAL schema types for the materiality selection. In order: the status field, the refusal and its
call site, the value check and its call site.
"""
from __future__ import annotations

import ast
import copy
import inspect
import json
import pathlib
import re
import textwrap
import typing
from datetime import date

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import flags as dossier_flags
from vinci.dossier import ltm_quarters as lq
from vinci.dossier.ciq import (
    CiqAmbiguousError,
    CiqBundle,
    CiqFormat,
    CiqPreliminaryError,
    CiqUnavailableError,
    CiqWorkbook,
)
from vinci.dossier.schemas import (
    FinancialSummary,
    MechanicalLayer,
    Sourced,
    StockInfo,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX: dict[str, typing.Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "ciq_ltm_quarters.json").read_text())
ANNUAL, QUARTERLY = "financials|annual|Income Statement", "financials|quarterly|Income Statement"
REFUSED = ("GOOGL", "LLY", "SMPL")
PASSES = ("GOOGL-filed", "NFLX", "NKE", "ROST", "TJX", "CNXC")


def _bundle(name: str, *, annual_of: str | None = None) -> CiqBundle:
    """The frozen rows as a REAL bundle: one workbook per period type, its sheet served from the
    bundle's own cache. ``annual_of`` takes the annual export from another fixture name."""
    sheets = {ANNUAL: FIX["names"][annual_of or name]["sheets"][ANNUAL],
              QUARTERLY: FIX["names"][name]["sheets"][QUARTERLY]}
    workbooks, cache = [], {}
    for key, rows in sheets.items():
        _kind, freq, sheet = key.split("|")
        path = pathlib.Path("/frozen") / f"{name}-{freq}.xls"
        workbooks.append(CiqWorkbook(kind="financials", path=path, fmt=CiqFormat.BIFF_XLS,
                                     freq=freq))
        cache[path] = {sheet: copy.deepcopy(rows)}
    return CiqBundle(ticker=name.split("-")[0], workbooks=tuple(workbooks), _cache=cache)


def _header(name: str, key: str) -> list[str]:
    return list(FIX["names"][name]["sheets"][key][0])


# --- the status field ---------------------------------------------------------------------------

@pytest.mark.parametrize(("name", "key", "index", "kind", "status"), [
    ("GOOGL", ANNUAL, -1, "LTM", "press_release"),        # 'LTM\nPress Release\n12 months\n…'
    ("GOOGL", QUARTERLY, -1, "Q", "press_release"),       # 'Press Release\n3 months\nQ3\n…'
    ("SMPL", ANNUAL, -1, "FY", "press_release"),          # a fiscal year built from a release
    ("GOOGL", ANNUAL, -2, "FY", "filed"),                 # '12 months\nDec-31-2025'
    ("GOOGL-filed", ANNUAL, -1, "LTM", "filed"),          # the LTM the release column replaced
    ("NFLX", ANNUAL, 1, "FY", "reclassified"),            # 'Reclassified\n12 months\nDec-31-2017'
    ("SMPL", ANNUAL, 2, "FY", "restated"),                # 'Restated\n12 months\nAug-25-2018'
])
def test_the_header_carries_its_status_as_a_field(
    name: str, key: str, index: int, kind: str, status: str,
) -> None:
    """(+/−) Every status word CIQ writes, read off real headers; a header with none is filed."""
    p = cs.header_period(_header(name, key)[index])
    assert (p.kind, p.status) == (kind, status)


def test_the_short_label_drops_the_status_so_no_consumer_may_read_it() -> None:
    """The defect's mechanism, kept: the printed label is a bare 'LTM' for both columns, which is
    why the status has to travel as a field."""
    pr, filed = _header("GOOGL", ANNUAL)[-1], _header("GOOGL-filed", ANNUAL)[-1]
    assert cs._fin_short(pr) == cs._fin_short(filed) == "LTM"
    assert (cs.header_period(pr).status, cs.header_period(filed).status) == (
        "press_release", "filed")


def test_the_basis_flag_is_the_status_field() -> None:
    for name in ("NFLX", "SMPL", "GOOGL"):
        for key in (ANNUAL, QUARTERLY):
            hdr = _header(name, key)
            assert [r for _c, _s, _l, r in cs._fin_periods(hdr)] == [
                cs.header_period(c).status == "reclassified" for c in hdr[1:] if c.strip()]


#: A status word tested against a header's text — the read every consumer made before the field.
_LABEL_READ = re.compile(r"""["'](?:Reclassified|Restated|Press Release)["']\s+(?:not\s+)?in\b""")


def test_no_consumer_reads_a_status_word_off_a_label() -> None:
    """(−) Every status read goes through `header_period`. (+) The scan finds the removed form:
    `_fin_periods` read `"Reclassified" in str(hdr[j])` until this build."""
    assert _LABEL_READ.search('_is_ltm(hdr[j]), "Reclassified" in str(hdr[j]))')
    hits = [f"{p.relative_to(ROOT)}:{i}" for p in sorted((ROOT / "vinci").rglob("*.py"))
            for i, line in enumerate(p.read_text().splitlines(), 1) if _LABEL_READ.search(line)]
    assert hits == []


# --- the refusal ---------------------------------------------------------------------------------

@pytest.mark.parametrize("name", REFUSED)
def test_a_press_release_income_statement_is_refused(name: str) -> None:
    """(−) GOOGL's and LLY's 2026-10-29 exports (a release LTM), and SMPL's, whose newest fiscal
    year is itself a release column with no LTM beside it."""
    with pytest.raises(CiqPreliminaryError) as exc:
        cs.require_filed_income_statement(_bundle(name), name)
    msg = str(exc.value)
    assert "BOTH Financials workbooks" in msg and "ciq-archive/replaced-" in msg
    assert "annual export" in msg and "quarterly export" in msg


def test_the_refusal_names_the_period_end_and_the_filing_it_waits_for() -> None:
    with pytest.raises(CiqPreliminaryError) as googl:
        cs.require_filed_income_statement(_bundle("GOOGL"), "GOOGL")
    assert "the 10-Q for the period ending 2026-09-30" in str(googl.value)
    with pytest.raises(CiqPreliminaryError) as smpl:
        cs.require_filed_income_statement(_bundle("SMPL"), "SMPL")
    assert "the 10-K for the period ending 2026-08-29" in str(smpl.value)
    found = cs.press_release_income_columns(_bundle("GOOGL"))
    assert [(c.export, c.period.kind, c.period.end) for c in found] == [
        ("annual", "LTM", date(2026, 9, 30)), ("quarterly", "Q", date(2026, 9, 30))]


@pytest.mark.parametrize("name", PASSES)
def test_a_filed_income_statement_passes(name: str) -> None:
    """(+) GOOGL's filed export that the release replaced, and five live filed exports."""
    assert cs.press_release_income_columns(_bundle(name)) == []
    cs.require_filed_income_statement(_bundle(name), name)


def test_the_refusal_stops_the_name_and_is_never_a_missing_export() -> None:
    assert issubclass(CiqPreliminaryError, CiqAmbiguousError)
    assert not issubclass(CiqPreliminaryError, CiqUnavailableError)


class _Tripwire:
    """Any attribute read means assembly went past the refusal."""

    def __getattr__(self, name: str) -> typing.Any:
        raise AssertionError(f"assembly read .{name} before refusing the press-release column")


def test_assembly_refuses_before_it_reads_anything() -> None:
    """(−) The CALL SITE: `assemble_mechanical` on GOOGL's 2026-10-29 rows raises before it touches
    the store, EDGAR, the network, the graph or the price."""
    from vinci.dossier.mechanical import assemble_mechanical

    record = typing.cast(typing.Any, type("R", (), {"identity": type("I", (), {
        "ticker": "GOOGL", "cik": None, "internal_id": None})()})())
    trip = typing.cast(typing.Any, _Tripwire())
    with pytest.raises(CiqPreliminaryError, match="GOOGL: 2 CIQ Financials Income Statement"):
        assemble_mechanical(record, store=trip, edgar=trip, http=trip, finra=trip, graph=trip,
                            resolver=trip, bundle=_bundle("GOOGL"),
                            reference_date=date(2026, 10, 30))


# --- the value check ------------------------------------------------------------------------------

def _read(name: str, *, annual_of: str | None = None) -> lq.LtmQuarterRead:
    b = _bundle(name, annual_of=annual_of)
    return lq.check(b, cs.financial_summary_annual(b).value)


def _mech(name: str) -> MechanicalLayer:
    """The two fields the materiality marker reads, on the REAL layer types."""
    table = cs.financial_summary_annual(_bundle(name)).value
    assert table is not None
    built: MechanicalLayer = typing.cast(typing.Any, MechanicalLayer).model_construct(
        financial_summary=typing.cast(typing.Any, FinancialSummary).model_construct(
            annual=Sourced.present(table, source_ref="CIQ Financials→Income Statement (annual)")),
        stock_info=typing.cast(typing.Any, StockInfo).model_construct(market_cap=Sourced.present(
            FIX["names"][name]["market_cap"], source_ref="CIQ comps")))
    return built


def _material(name: str) -> set[str]:
    """Item 19c's own selection, through the same two calls assembly makes."""
    from vinci.dossier.assemble import _mark_material
    from vinci.dossier.synthesis import demanded_material_figures

    return {f.label for f in demanded_material_figures(_mark_material(_mech(name)))}


def _by_label(read: lq.LtmQuarterRead) -> dict[str, lq.LtmCheck]:
    return {r.label: r for r in read.rows}


GAIN, MERGER = "Gain (Loss) On Sale Of Invest. ($M)", "Merger & Related Restruct. Charges ($M)"


def test_a_material_ltm_its_quarters_contradict_refuses_on_a_filed_column() -> None:
    """(−) NFLX's LTM to Sep-30-2026 is FILED, so the status gate passes it; its merger charge reads
    -2,800.0 where its quarterly export books +2,800.0 in Q1 2026 — and that quarterly export's net
    income sums to the LTM's exactly, so the quarters are self-consistent. Material: refused."""
    rows = _by_label(_read("NFLX"))
    assert rows[MERGER].outcome == "differ"
    assert (rows[MERGER].ltm, rows[MERGER].carried) == (-2800.0, 2800.0)
    assert rows["Net income ($M)"].outcome == "agree"
    material = _material("NFLX")
    assert MERGER in material
    assert [r.label for r in _read("NFLX").refused(material)] == [MERGER]


def test_the_release_gain_carried_from_fy25_is_caught_by_value_too() -> None:
    """(−) The value test pairs the status gate: GOOGL's 24,620.0 against 138,156.0 on the three
    quarters carrying a figure, Q3 reading '-'."""
    row = _by_label(_read("GOOGL"))[GAIN]
    assert (row.outcome, row.ltm, row.carried) == ("differ", 24620.0, 138156.0)
    assert [q.value is None for q in row.quarters] == [False, False, False, True]
    assert [r.label for r in _read("GOOGL").refused(_material("GOOGL"))] == [GAIN]


def test_the_filed_gain_reconciles_with_no_flag() -> None:
    """(+) GOOGL's filed LTM to Jun-30-2026: 149,012.0, its four quarters' exact sum."""
    read = _read("GOOGL-filed")
    row = _by_label(read)[GAIN]
    assert (row.outcome, row.ltm, row.carried) == ("agree", 149012.0, 149012.0)
    assert not any(GAIN in f for f in read.flags())
    assert read.refused(_material("GOOGL-filed")) == []


def test_quarters_are_found_by_date_never_by_position() -> None:
    """(+) The filed annual (LTM to Jun-30-2026) beside the LATER quarterly export, whose newest
    column is Q3 2026: the window is Q3 2025 → Q2 2026 by date, so the gain still agrees. The last
    four columns would be Q4 2025 → Q3 2026 and read 138,156.0."""
    row = _by_label(_read("GOOGL", annual_of="GOOGL-filed"))[GAIN]
    assert [q.end for q in row.quarters] == [
        date(2025, 9, 30), date(2025, 12, 31), date(2026, 3, 31), date(2026, 6, 30)]
    assert (row.outcome, row.carried) == ("agree", 149012.0)


def test_a_non_material_disagreement_is_flagged_and_never_refuses() -> None:
    """(+) NKE's restructuring LTM -385.0 against -311.0 on the two quarters carrying a figure: the
    LTM is right and the quarterly export has the gap, so it is a QA flag only."""
    read = _read("NKE")
    row = _by_label(read)["Restructuring Charges ($M)"]
    assert (row.outcome, row.ltm, row.carried) == ("differ", -385.0, -311.0)
    assert "Restructuring Charges ($M)" not in _material("NKE")
    assert read.refused(_material("NKE")) == []
    assert [f for f in read.flags() if "Restructuring Charges" in f]


@pytest.mark.parametrize("name", ("ROST", "TJX"))
def test_a_dash_quarter_that_reconciles_is_unverified_not_refused(name: str) -> None:
    """(+) ROST's and TJX's other unusual items sit in one quarter, the other three reading '-'."""
    read = _read(name)
    row = _by_label(read)["Other Unusual Items ($M)"]
    assert row.outcome == "unverified" and row.carried == row.ltm
    assert read.refused(_material(name)) == []
    assert any("UNVERIFIED" in f for f in read.flags())


def test_a_material_dash_that_reconciles_does_not_refuse() -> None:
    """(+) The '-' rule on a MATERIAL row. CNXC's goodwill impairment, -2,573.3, is -1,523.3 and
    -1,050.0 in two quarters, with '-' in one and 0.0 in another: refusing on the '-' would select
    on how CIQ writes an empty quarter, not on the figure."""
    row = _by_label(_read("CNXC"))["Impairment of Goodwill ($M)"]
    assert (row.outcome, row.ltm, row.carried) == ("unverified", -2573.3, -2573.3)
    assert "Impairment of Goodwill ($M)" in _material("CNXC")
    assert _read("CNXC").refused(_material("CNXC")) == []


def test_lly_release_column_disagrees_off_its_material_row() -> None:
    """LLY's release LTM carries FY25's -484.0 other unusual items against -1,066.1 on its three
    filed trailing quarters, while its material in-process R&D (-8,070.0) agrees: the status gate,
    not this check, stops LLY."""
    rows = _by_label(_read("LLY"))
    other = rows["Other Unusual Items ($M)"]
    assert (other.outcome, other.ltm, round(other.carried or 0, 1)) == ("differ", -484.0, -1066.1)
    assert rows["In Process R & D Exp. ($M)"].outcome == "agree"
    assert _read("LLY").refused(_material("LLY")) == []


def test_no_ltm_column_reads_not_run_and_says_so() -> None:
    read = _read("SMPL")
    assert read.rows == () and read.not_run is not None
    assert read.flags() == [f"{lq.FLAG_PREFIX} NOT RUN — {read.not_run}"]


def _q(value: float | None) -> lq.QuarterCell:
    return lq.QuarterCell(date(2026, 6, 30), 2, value)


@pytest.mark.parametrize(("ltm", "quarters", "outcome"), [
    (-91.7, (None, None, -60.2, -31.4), "unverified"),  # CNXC restructuring: 0.1 apart, in slack
    (-48.0, (None, None, None, -49.0), "differ"),        # WAT restructuring: 1.0 apart, 2.04%
    (0.9, (None, None, None, None), "not_run"),          # EPAM: no quarter carries a figure
])
def test_the_tolerance_is_two_percent_or_half_a_printed_million(
    ltm: float, quarters: tuple[float | None, ...], outcome: str,
) -> None:
    """Observed pairs from the 2026-10-30 corpus run (`_judge` on the real cell type)."""
    assert lq._judge("row", ltm, date(2026, 6, 30), tuple(_q(v) for v in quarters)).outcome == (
        outcome)


def test_every_flag_goes_to_the_qa_channel() -> None:
    flags = [f for n in ("NFLX", "NKE", "ROST", "CNXC", "SMPL", "LLY") for f in _read(n).flags()]
    assert len(flags) >= 6
    assert all(dossier_flags.is_qa(f) for f in flags)
    caveats, qa = dossier_flags.partition(flags)
    assert (caveats, qa) == ([], flags)


def test_the_refusal_message_names_every_row() -> None:
    refused = _read("NFLX").refused(_material("NFLX"))
    msg = lq.refusal_message("NFLX", refused)
    assert msg.startswith("NFLX: 1 MATERIAL annual-summary row(s)")
    assert MERGER in msg and "DIFFER" in msg


def test_assembly_checks_before_it_spends_and_refuses_on_the_19c_selection() -> None:
    """The CALL SITE (a helper-level test stays green when a call site is deleted): `assemble_one`
    runs the check, routes its flags, takes material from `_mark_material` +
    `demanded_material_figures`, and raises — all before the first LLM call."""
    from vinci.dossier import assemble

    src = textwrap.dedent(inspect.getsource(assemble.assemble_one))
    tree = ast.parse(src)
    calls = {(n.lineno, ast.unparse(n.func)) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    first = {name: min(ln for ln, f in calls if f == name) for _ln, name in calls}
    for name in ("ltm_quarters.check", "ltm_read.flags", "demanded_material_figures",
                 "_mark_material", "ltm_read.refused", "ltm_quarters.refusal_message"):
        assert name in first, name
    assert first["ltm_quarters.check"] > first["assemble_mechanical"]
    for spend in ("extract_covenant_terms", "extract_transcript_drivers", "synthesize"):
        assert first["ltm_quarters.refusal_message"] < first[spend], spend


def test_mechanical_refuses_right_after_the_currency() -> None:
    from vinci.dossier import mechanical

    src = textwrap.dedent(inspect.getsource(mechanical.assemble_mechanical))
    calls = sorted((n.lineno, ast.unparse(n.func)) for n in ast.walk(ast.parse(src))
                   if isinstance(n, ast.Call))
    order = [f for _ln, f in calls]
    i = order.index("ciq_sheets.require_usd")
    assert order[i + 1] == "ciq_sheets.require_filed_income_statement"


# --- round 1: the anchor's CIQ bridge refuses too ------------------------------------------------

def test_the_anchor_bridge_refuses_a_press_release_income_statement() -> None:
    """(−) `anchor-backfill` reads the export ON DISK through `ciq_bridge`, gated by no stamp —
    the one reader that does (every refresh transform reads only the page's own export, by hash or
    by reproducing its figures). One refusal on both paths, as the currency's (#819 finding 1)."""
    from vinci.dossier.anchor import ciq_bridge

    with pytest.raises(CiqPreliminaryError, match="GOOGL: 2 CIQ Financials Income Statement"):
        ciq_bridge(_bundle("GOOGL"), "GOOGL")


def test_the_anchor_bridge_still_reads_a_filed_export() -> None:
    """(+) GOOGL's filed export passes the refusal and its bridge reads: revenue off the frozen
    annual Income Statement (the rows carry no balance sheet, so the rest is reported unread)."""
    from vinci.dossier.anchor import ciq_bridge

    ciq, _note = ciq_bridge(_bundle("GOOGL-filed"), "GOOGL")
    assert ciq is not None and "revenue" in ciq.facts
