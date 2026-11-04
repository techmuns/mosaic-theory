"""THE SEC FILING DECIDES A MATERIAL LTM CIQ DISAGREES WITH ITSELF ON (2026-11-04, operator
approval).

`ltm_quarters` refuses a material annual-summary row whose LTM in CIQ's annual export disagrees
with its four quarters in CIQ's quarterly export. `filed_tiebreak` lets the filer's XBRL figure for
the same four quarters decide when it reproduces one of the two readings, and refuses as before
when it cannot be read or reproduces neither.

Every pin runs on REAL data (CORPUS BEFORE SYNTHETIC), frozen in
`tests/fixtures/filed_tiebreak.json`: the operator's Drive exports, cut to derived cells through
the real decode path and built into the REAL `CiqBundle`, beside SEC's companyfacts cut by
concept, each concept's rows unmodified (`scripts/build_filed_tiebreak_fixture.py`). The cases:

* CELH (+): Other Unusual Items -418.8 annual against -405.0 quarterly. The filed
  RestructuringCharges come to -412.748 and reproduce both, so the page states the filed figure;
  this is the name refused since 2026-11-02.
* EPAM (+): the filed figure sides with the ANNUAL export (restructuring -53.5 against -28.5;
  filed -53.474). NKE was meant to be this case, but it files no restructuring fact in its window.
* NFLX (-): the merger fee is filed only inside the whole non-operating line, which the mapping
  leaves out, so the name stays refused.
* BDX (-): a mapped concept far from both CIQ readings refuses. So does EPAM's Other Unusual Items,
  where the band catches the mapping misreading a name.
"""
from __future__ import annotations

import ast
import copy
import inspect
import json
import pathlib
import textwrap
import typing
from datetime import date

import pytest

from vinci.dossier import ciq_sheets as cs
from vinci.dossier import filed_tiebreak as ft
from vinci.dossier import flags as dossier_flags
from vinci.dossier import ltm_quarters as lq
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.schemas import (
    Dossier,
    FinancialSummary,
    MechanicalLayer,
    Sourced,
    StockInfo,
)
from vinci.edgar.concepts import points_for_tag

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX: dict[str, typing.Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "filed_tiebreak.json").read_text())
OUI, RESTR = "Other Unusual Items ($M)", "Restructuring Charges ($M)"
MERGER = "Merger & Related Restruct. Charges ($M)"
CELH_ACCESSIONS = ("0001341766-25-000144", "0001341766-26-000024", "0001341766-26-000039",
                   "0001341766-26-000050")
ANNUAL_REF = "CIQ Financials→Income Statement + Cash Flow (annual) + Estimates→Trends (FY E)"


def _bundle(name: str) -> CiqBundle:
    """The frozen rows as a REAL bundle: one workbook per period type, served from its cache."""
    workbooks, cache = [], {}
    for key, rows in FIX["names"][name]["sheets"].items():
        _kind, freq, sheet = key.split("|")
        path = pathlib.Path("/frozen") / f"{name}-{freq}.xls"
        workbooks.append(CiqWorkbook(kind="financials", path=path, fmt=CiqFormat.BIFF_XLS,
                                     freq=freq))
        cache[path] = {sheet: copy.deepcopy(rows)}
    return CiqBundle(ticker=name, workbooks=tuple(workbooks), _cache=cache)


def _facts(name: str) -> dict[str, typing.Any]:
    return copy.deepcopy(FIX["names"][name]["companyfacts"])


def _cut(name: str) -> date:
    """The export's own stamp — a stand-in for the page's price date, which a build reads off its
    stored close; every export here was priced on or after it."""
    return date.fromisoformat(FIX["names"][name]["comps_export_stamp"])


def _mech(name: str) -> MechanicalLayer:
    """The fields the check, the marker and the tiebreak read, on the REAL layer types."""
    table = cs.financial_summary_annual(_bundle(name)).value
    assert table is not None
    built: MechanicalLayer = typing.cast(typing.Any, MechanicalLayer).model_construct(
        financial_summary=typing.cast(typing.Any, FinancialSummary).model_construct(
            annual=Sourced.present(table, source_ref=ANNUAL_REF)),
        stock_info=typing.cast(typing.Any, StockInfo).model_construct(
            market_cap=Sourced.present(FIX["names"][name]["market_cap"], source_ref="CIQ comps"),
            as_of=_cut(name)))
    return built


def _material(mech: MechanicalLayer) -> set[str]:
    from vinci.dossier.assemble import _mark_material
    from vinci.dossier.synthesis import demanded_material_figures

    return {f.label for f in demanded_material_figures(_mark_material(mech))}


def _read(name: str) -> dict[str, lq.LtmCheck]:
    b = _bundle(name)
    return {r.label: r for r in lq.check(b, cs.financial_summary_annual(b).value).rows}


def _decide(name: str, label: str, *, cut: date | None = None) -> ft.Decision:
    return ft.decide(_read(name)[label], _facts(name), as_filed_by=cut or _cut(name))


# --- CELH: the refused name, now stated as filed ------------------------------------------------

def test_the_fixture_reproduces_celhs_refusal() -> None:
    """The fixture is CELH's real refusal: the material row DIFFERs, -418.8 against -405.0."""
    row = _read("CELH")[OUI]
    assert (row.outcome, row.ltm, round(row.carried or 0, 3)) == ("differ", -418.8, -405.027)
    mech = _mech("CELH")
    b = _bundle("CELH")
    assert [r.label for r in lq.check(b, cs.financial_summary_annual(b).value)
            .refused(_material(mech))] == [OUI]


def test_celhs_filed_restructuring_decides_it() -> None:
    """(+) The filed RestructuringCharges, quarter by quarter, in CIQ's sign: Q3-25 and Q2-26 are
    the 10-Qs' own 3-month facts, Q4-25 the 10-K's year less the nine months; -412.748 reproduces
    BOTH readings (1.4% and 1.9%)."""
    d = _decide("CELH", OUI)
    f = d.figure
    assert f is not None and d.reason is None
    assert (f.value.value, f.tag, f.supports) == (-412.748, "RestructuringCharges", "both")
    assert (f.ciq_annual, f.ciq_quarterly) == (-418.8, -405.027)
    assert [(q.end, q.value, q.derived) for q in f.quarters] == [
        ("2025-09-30", -246.707, False), ("2025-12-31", -80.754, True),
        ("2026-03-31", -4.427, False), ("2026-06-30", -80.86, False)]
    assert f.value.source_ref is not None
    assert all(acc in f.value.source_ref for acc in CELH_ACCESSIONS)


def test_q4_is_the_10ks_year_less_the_nine_months() -> None:
    """(+) Q4-25 = FY25 327.461 (10-K 0001341766-26-000024) − 9M 246.707 (10-Q
    0001341766-25-000144): both filings named on the quarter."""
    f = _decide("CELH", OUI).figure
    assert f is not None
    q4 = f.quarters[1]
    assert q4.derived and q4.value == round(-(327.461 - 246.707), 3)
    assert "2025-01-01..2025-12-31 (10-K 0001341766-26-000024" in q4.source_ref
    assert "2025-01-01..2025-09-30 (10-Q 0001341766-25-000144" in q4.source_ref


def test_the_filing_is_read_as_filed_by_the_pages_price_date() -> None:
    """(−/+) The cut: as filed by 2026-08-05 the Q2 2026 10-Q (filed 2026-08-06) does not exist,
    so its quarter has no fact and the row stays refused; on 2026-08-06 it decides."""
    before = _decide("CELH", OUI, cut=date(2026, 8, 5))
    assert before.figure is None and before.reason is not None
    assert "states no quarter to 2026-06-30 as filed by 2026-08-05" in before.reason
    assert _decide("CELH", OUI, cut=date(2026, 8, 6)).figure is not None


def test_celhs_page_states_the_filed_figure_and_prints_the_caveat() -> None:
    """(+) THROUGH THE ASSEMBLY'S OWN SETTLEMENT (`_settle_ltm_refusals`), on CELH's real rows:
    - the LTM cell holds the filed figure as value and cell;
    - the table's source names the accessions, and the row stays material;
    - the figure 19c demands is the filed one, cited to the filings;
    - the caveat is a decision caveat, never QA, so it prints in the main body's caveats."""
    from vinci.dossier.assemble import _settle_ltm_refusals
    from vinci.dossier.render import _flags_section
    from vinci.dossier.synthesis import demanded_material_figures

    mech = _mech("CELH")
    out, caveats = _settle_ltm_refusals("CELH", mech, [_decide("CELH", OUI)])
    fs = out.financial_summary
    assert fs is not None and fs.annual.value is not None
    table = fs.annual.value
    col = [str(c) for c in table.columns].index("LTM")
    row = next(r for r in table.rows if r.label == OUI)
    assert (row.values[col], row.cells[col]) == (-412.748, "-413")
    before = next(r for r in typing.cast(typing.Any, mech.financial_summary).annual.value.rows
                  if r.label == OUI)
    assert [v for i, v in enumerate(row.values) if i != col] == [
        v for i, v in enumerate(before.values) if i != col]
    assert fs.filed_ltm is not None and [f.label for f in fs.filed_ltm] == [OUI]
    assert fs.annual.source_ref is not None and fs.annual.source_ref.startswith(ANNUAL_REF)
    assert all(acc in fs.annual.source_ref for acc in CELH_ACCESSIONS)
    assert OUI in _material(out)
    from vinci.dossier.assemble import _mark_material

    demanded = [f for f in demanded_material_figures(_mark_material(out)) if f.label == OUI]
    assert [f.value for f in demanded] == [-412.748]
    assert demanded[0].source_ref is not None and CELH_ACCESSIONS[0] in demanded[0].source_ref
    assert len(caveats) == 1
    shown, qa = dossier_flags.partition(caveats)
    assert qa == [] and len(shown) == 1
    page = "\n".join(_flags_section(typing.cast(typing.Any, Dossier).model_construct(
        caveats=shown)))
    for needle in ("-412.7", "-418.8", "-405.0", *CELH_ACCESSIONS):
        assert needle in page, needle


def test_the_filed_block_round_trips_and_is_absent_when_none() -> None:
    """The block reaches dossier.json whole, and a page built without one carries no key (a page
    built before it round-trips byte-identically)."""
    from vinci.dossier.schemas import DROP_WHEN_NONE

    f = _decide("CELH", OUI).figure
    assert f is not None
    assert type(f).model_validate_json(f.model_dump_json()) == f
    assert ("financial_summary", "filed_ltm") in DROP_WHEN_NONE


# --- EPAM: the filing sides with the ANNUAL export ----------------------------------------------

def test_epams_filed_restructuring_sides_with_the_annual_export() -> None:
    """(+) EPAM's restructuring LTM reads -53.5 in the annual export and -28.5 on the two quarters
    the quarterly export carries; the filed figure, -53.474, is the annual's. (Not material, so no
    build turns on it: the case shows the tiebreak picks the side the filing supports, whichever
    it is.)"""
    row = _read("EPAM")[RESTR]
    assert (row.outcome, row.ltm, row.carried) == ("differ", -53.5, pytest.approx(-28.5))
    f = _decide("EPAM", RESTR).figure
    assert f is not None and (f.value.value, f.supports) == (-53.474, "annual")


def test_a_partial_quarterly_reading_is_not_called_four_quarters() -> None:
    """(−) EPAM's quarterly export carries the restructuring row in only 2 of its 4 quarters, so
    the caveat says so — it never calls -28.5 the four quarters' sum."""
    d = _decide("EPAM", RESTR)
    text = d.caveat()
    assert "quarterly export's 2 of 4 quarters carrying a figure sum to -28.5" in text
    assert "quarterly export's four quarters" not in text
    assert "quarterly export's four quarters sum to -405.0" in _decide("CELH", OUI).caveat()


def test_a_restated_quarter_names_only_the_filing_it_was_read_from() -> None:
    """(−/+) A quarter restated by a later filing: its source_ref still says what it restates
    (`concepts.filed_at`), but the figure's accessions — its source and its caveat — name only the
    filing the value was READ from. CELH's real Q3 2025 fact, with an earlier first filing of the
    same period at another value inserted ahead of it."""
    facts = _facts("CELH")
    rows = facts["facts"]["us-gaap"]["RestructuringCharges"]["units"]["USD"]
    first = "0001341766-25-000999"
    rows.append({"start": "2025-07-01", "end": "2025-09-30", "val": 240000000, "accn": first,
                 "fy": 2025, "fp": "Q3", "form": "10-Q", "filed": "2025-11-01"})
    d = ft.decide(_read("CELH")[OUI], facts, as_filed_by=_cut("CELH"))
    f = d.figure
    assert f is not None and f.value.value == -412.748
    assert first in f.quarters[0].source_ref and "restating" in f.quarters[0].source_ref
    assert first not in f.quarters[0].accessions
    assert f.value.source_ref is not None and first not in f.value.source_ref
    assert first not in d.caveat()


# --- the refusals that stand --------------------------------------------------------------------

def test_a_filed_figure_far_from_both_readings_refuses() -> None:
    """(−) BDX's Other Unusual Items read -184.0 and -143.0; its filed RestructuringCharges over
    the same quarters, -693.0, reproduces neither — not shown to be the same item."""
    d = _decide("BDX", OUI)
    assert d.figure is None and d.reason is not None
    assert "-693.0, reproduces neither CIQ reading (-184.0 annual, -143.0 quarterly" in d.reason


def test_the_band_catches_the_mapping_misreading_a_name() -> None:
    """(−) EPAM files its restructuring in CIQ's own Restructuring row, so its Other Unusual Items
    (-17.8 / -16.8) is NOT that charge. The mapping reads RestructuringCharges for the row anyway,
    and the band refuses the -53.5 it finds."""
    d = _decide("EPAM", OUI)
    assert d.figure is None and d.reason is not None and "-53.5, reproduces neither" in d.reason


def test_nflx_stays_refused_the_merger_fee_is_filed_only_inside_a_containing_line() -> None:
    """(−) NFLX: material, -2,800.0 annual against +2,800.0 in Q1 2026. No business-combination
    concept is filed, and the whole non-operating line is not mapped, so the build refuses — the
    message now says why the filing cannot decide."""
    from vinci.dossier.assemble import DossierAssemblyError, _settle_ltm_refusals

    d = _decide("NFLX", MERGER)
    assert d.figure is None and d.reason is not None
    assert "BusinessCombinationAcquisitionRelatedCosts carries no fact" in d.reason
    assert MERGER in _material(_mech("NFLX"))
    with pytest.raises(DossierAssemblyError) as exc:
        _settle_ltm_refusals("NFLX", _mech("NFLX"), [d])
    msg = str(exc.value)
    assert msg.startswith("NFLX: 1 MATERIAL annual-summary row(s)")
    assert MERGER in msg and "DIFFER" in msg and "the SEC filing cannot decide it" in msg


def test_nflxs_containing_line_is_ciqs_own_rows_and_is_not_mapped() -> None:
    """Why `NonoperatingIncomeExpense` is left out, measured on NFLX. Its Q1 2026 figure,
    2,852.166, is CIQ's interest income + FX + other non-operating + the merger row exactly. Over
    the LTM, 2,992.3 is outside the band of +2,800.0, so the band would refuse it even if mapped.
    No row maps to it."""
    assert all("NonoperatingIncomeExpense" not in line.tags for line in ft.MAPPING.values())
    facts = _facts("NFLX")
    pts = points_for_tag(facts, "NonoperatingIncomeExpense")
    q1 = ft.filed_quarter(pts, date(2026, 3, 31))
    assert q1 is not None and q1[0] / 1e6 == pytest.approx(2852.166)
    qrows = {str(r[0]).strip(): r for r in FIX["names"]["NFLX"]["sheets"][
        "financials|quarterly|Income Statement"]}
    hdr = qrows["For the Fiscal Period Ending"]
    j = next(i for i, h in enumerate(hdr) if "Mar-31-2026" in str(h))
    parts = [qrows[k][j] for k in ("Interest and Invest. Income", "Currency Exchange Gains (Loss)",
                                   "Other Non-Operating Inc. (Exp.)",
                                   "Merger & Related Restruct. Charges")]
    assert sum(parts) == pytest.approx(2852.166, abs=0.1)
    quarters = _read("NFLX")[MERGER].quarters
    got = [ft.filed_quarter(pts, q.end) for q in quarters]
    ltm = sum(g[0] for g in got if g is not None) / 1e6
    assert ltm == pytest.approx(2992.306) and not lq.agrees(ltm, 2800.0)


def test_nke_files_no_restructuring_fact_in_its_window() -> None:
    """(−) NKE, which the records call the quarterly side's error, files no RestructuringCharges
    for any of its four quarters to 2026-08-31 — so the filing cannot decide it either way. It is
    not material, so nothing refuses on it."""
    d = _decide("NKE", RESTR)
    assert d.figure is None and d.reason is not None
    assert ("us-gaap:RestructuringCharges states no quarter to 2025-11-30, 2026-02-28, "
            "2026-05-31, 2026-08-31") in d.reason
    assert RESTR not in _material(_mech("NKE"))


def test_an_unmapped_row_refuses() -> None:
    """(−) CELH's EBITDA also differs (671.7 against 632.8) and no concept is mapped for it."""
    d = _decide("CELH", "EBITDA ($M)")
    assert d.figure is None and d.reason is not None and "no reviewed mapping" in d.reason


def test_only_a_differing_row_reaches_the_filing() -> None:
    """(−) A row the check could not run has no second CIQ reading to adjudicate. EPAM's merger
    row reads 0.875 in the annual LTM with all four quarters '-' (NOT RUN), though EPAM does file
    BusinessCombinationAcquisitionRelatedCosts: the filing is never asked."""
    row = _read("EPAM")[MERGER]
    assert (row.outcome, row.ltm, [q.value for q in row.quarters]) == (
        "not_run", 0.875, [None, None, None, None])
    assert points_for_tag(_facts("EPAM"), "BusinessCombinationAcquisitionRelatedCosts")
    d = ft.decide(row, _facts("EPAM"), as_filed_by=_cut("EPAM"))
    assert d.figure is None and "no second reading" in (d.reason or "")


def test_one_undecided_row_refuses_the_whole_build() -> None:
    """All or nothing: a decided row beside an undecided one still refuses, naming only the
    undecided; the page is never built half on the filing."""
    from vinci.dossier.assemble import DossierAssemblyError, _settle_ltm_refusals

    with pytest.raises(DossierAssemblyError) as exc:
        _settle_ltm_refusals("CELH", _mech("CELH"),
                             [_decide("CELH", OUI), _decide("CELH", "EBITDA ($M)")])
    assert "1 MATERIAL" in str(exc.value) and "EBITDA" in str(exc.value)
    assert OUI not in str(exc.value)


def test_the_mapping_is_explicit_and_signed() -> None:
    """Every entry is a summary label, names us-gaap concepts by hand and states a sign."""
    assert set(ft.MAPPING) == {OUI, RESTR, MERGER}
    for label, line in ft.MAPPING.items():
        assert label.endswith(" ($M)") and line.tags and line.sign in (-1, 1) and line.why


# --- the call site ------------------------------------------------------------------------------

def _calls(fn: typing.Any) -> dict[str, int]:
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    found: dict[str, int] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name = ast.unparse(n.func)
            found[name] = min(found.get(name, n.lineno), n.lineno)
    return found


def test_assembly_asks_the_filing_after_the_refusal_and_before_any_spend() -> None:
    """The CALL SITE: `assemble_one` asks the filing only for the rows the check refuses, settles
    them (raising or stating) and does both before the first LLM call; the settlement raises
    through the check's own refusal message; the facts are cut at the page's price date."""
    from vinci.dossier import assemble

    first = _calls(assemble.assemble_one)
    asked = (first["_filed_tiebreak"], first["_settle_ltm_refusals"])
    assert first["ltm_read.refused"] < min(asked)
    for spend in ("extract_covenant_terms", "extract_transcript_drivers", "synthesize"):
        assert max(asked) < first[spend], spend
    settle = _calls(assemble._settle_ltm_refusals)
    assert {"ltm_quarters.refusal_message", "filed_tiebreak.apply"} <= set(settle)
    ask = _calls(assemble._filed_tiebreak)
    assert {"page_price_date", "filed_tiebreak.decide"} <= set(ask)


def test_an_unreadable_edgar_leaves_the_row_refused_never_a_crash(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) EDGAR answering with a non-retryable error (a 404 for a CIK with no XBRL facts, a 5xx
    after its retries) is a filing that cannot be read: the row stays REFUSED, with the CIQ
    disagreement and the reason, exactly as before the tiebreak — never a bare exception that the
    run's cost-and-outcome series records as a failed build. A throttle still stops the run
    (`SecRateLimitedError` is not an `HttpError`)."""
    from vinci.dossier import assemble
    from vinci.netcache import HttpNotFoundError, SecRateLimitedError

    class _Edgar:
        def __init__(self, exc: Exception) -> None:
            self.exc = exc

        def companyfacts(self, cik: str) -> dict[str, typing.Any]:
            raise self.exc

    row = _read("NFLX")[MERGER]
    mech = _mech("NFLX")
    monkeypatch.setattr(assemble.EdgarClient, "from_config",
                        staticmethod(lambda cfg: _Edgar(HttpNotFoundError("404 companyfacts"))))
    decided = assemble._filed_tiebreak(typing.cast(typing.Any, None), "1065280", mech, [row],
                                       reference_date=_cut("NFLX"))
    assert [d.figure for d in decided] == [None]
    assert "EDGAR companyfacts could not be read" in (decided[0].reason or "")
    with pytest.raises(assemble.DossierAssemblyError, match="cannot decide it: EDGAR"):
        assemble._settle_ltm_refusals("NFLX", mech, decided)
    monkeypatch.setattr(assemble.EdgarClient, "from_config",
                        staticmethod(lambda cfg: _Edgar(SecRateLimitedError("blocked"))))
    with pytest.raises(SecRateLimitedError):
        assemble._filed_tiebreak(typing.cast(typing.Any, None), "1065280", mech, [row],
                                 reference_date=_cut("NFLX"))
