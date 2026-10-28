"""FPI1a (STATE §5.0 row 4, step 2): a 20-F or 40-F is an annual report, and a figure in another
currency is never read as dollars.

THE DEFECT (`docs/records/2026-10-28-fpi-readiness-measured-per-name.md`). The dossier's annual
readers asked for a 10-K, so a foreign filer's annual report was never read. Opening them without a
currency guard would have served QFIN's newest annual revenue, CNY 19,205,059,000, to readers that
print dollars, because `concepts.extract_points` returned every unit under a concept. The screen
already did that to the P/E: QFIN's level divided $5.67 per ADS by a CNY EPS.

Every pin reads a REAL filing:
- `tests/fixtures/fpi1a_companyfacts/`: four issuers' companyfacts as served on 2026-10-28, cut to
  the tags read here, every row unchanged.
  - QFIN reports in CNY with USD convenience translations.
  - JOYY moved from CNY to USD with its FY2021 20-F.
  - AQN reported in CAD before it moved to USD, and files a 40-F.
  - SIMO's 2012 20-F/A is in TWD.
- `tests/fixtures/fpi1a_instances/`: two 20-F XBRL instances.
  - ARCO's is trimmed to the facts segment_facts reads; it was proven to read identically to the
    full instance.
  - LPL's is cut to verbatim slices: its own root, which declares us-gaap and uses only ifrs-full,
    plus its period, its revenue, and their contexts and unit.
- `tests/fixtures/fpi1a_exhibit_indexes.json`: three filings' exhibit lists, as served.
"""
from __future__ import annotations

import ast
import json
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.dossier import mechanical as mech
from vinci.edgar import concepts as cc
from vinci.edgar import segment_facts as sf
from vinci.edgar.client import Filing, compute_fundamental_snapshot
from vinci.graph.filings import latest_10k_excerpts
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import pe_current_and_percentile

ROOT = Path(__file__).resolve().parents[1]
_CF = ROOT / "tests" / "fixtures" / "fpi1a_companyfacts"
_INST = ROOT / "tests" / "fixtures" / "fpi1a_instances"
_IDX = json.loads((ROOT / "tests" / "fixtures" / "fpi1a_exhibit_indexes.json").read_text())
REF = date(2026, 10, 16)


def _cf(ticker: str) -> dict[str, Any]:
    facts: dict[str, Any] = json.loads((_CF / f"{ticker}.json").read_text())
    return facts


def _raw_units(facts: dict[str, Any], tag: str) -> set[str]:
    return set(facts["facts"]["us-gaap"][tag]["units"])


# --- the reporting currency ----------------------------------------------------------------------

def test_qfin_reports_in_yuan_though_its_newest_balance_sheet_also_carries_dollars() -> None:
    """The first cut of #837 read the unit of `Assets` and put QFIN in USD. Its newest 20-F tags
    its balance sheet in CNY at two year-ends and in USD at one, the convenience translation."""
    f = _cf("QFIN")
    assert cc.reporting_currency(f) == "CNY"
    acc = "0001104659-26-049501"
    rows = f["facts"]["us-gaap"]["Assets"]["units"]
    assert {u: sum(r["accn"] == acc for r in rs) for u, rs in rows.items()} == {"CNY": 2, "USD": 1}


def test_a_dollar_reporter_with_foreign_figures_in_its_past_reports_in_dollars() -> None:
    """AQN's 40-Fs were in CAD before it moved to USD; SIMO's 2012 20-F/A is in TWD. Both carry
    those figures under the same tags today."""
    for ticker, foreign in (("AQN", "CAD"), ("SIMO", "TWD")):
        f = _cf(ticker)
        assert cc.reporting_currency(f) == "USD", ticker
        assert foreign in _raw_units(f, "CashAndCashEquivalentsAtCarryingValue"), ticker


def test_the_currency_is_judged_as_of_the_blob_it_is_given() -> None:
    """JOYY's statements were in CNY through its FY2020 20-F and in USD from its FY2021 20-F,
    filed 2022-04-29: a blob cut before that filing reads CNY."""
    f = _cf("JOYY")
    assert cc.reporting_currency(cc.facts_as_of(f, date(2022, 4, 28))) == "CNY"
    assert cc.reporting_currency(cc.facts_as_of(f, date(2022, 4, 29))) == "USD"


# --- the shared reader serves one currency, and by default only dollars -------------------------

def test_a_yuan_reporter_serves_no_money_fact_not_even_its_dollar_translation() -> None:
    """NEGATIVE, the observed failure shape: QFIN's CNY revenue is never served to a dollar
    reader, and neither is its USD convenience translation, which is in the same filing."""
    f = _cf("QFIN")
    tag = "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert _raw_units(f, tag) == {"CNY", "USD"}
    assert cc.extract_points(f, "revenue") == []
    assert cc.points_for_tag(f, tag) == []
    # the filer's own currency is there for a reading the currency cannot move
    own = cc.latest_annual(cc.extract_points(f, "revenue", currency=cc.REPORTING))
    assert own is not None and own.unit == "CNY" and own.value == 19_205_059_000
    # a unit with no currency is served either way
    assert cc.extract_points(f, "shares")


def test_a_dollar_reporter_is_served_its_dollars_and_none_of_its_foreign_figures() -> None:
    """POSITIVE: AQN's and SIMO's dollar series still read, and their CAD / TWD rows are gone."""
    for ticker in ("AQN", "SIMO"):
        f = _cf(ticker)
        cash = cc.extract_points(f, "cash")
        eps = cc.extract_points(f, "eps_diluted")
        assert cash and {p.unit for p in cash} == {"USD"}, ticker
        assert eps and {p.unit for p in eps} == {"USD/shares"}, ticker
        assert cc.extract_points(f, "cash", currency=cc.REPORTING) == cash, ticker


def test_a_switched_reporter_reads_one_currency() -> None:
    """JOYY's EPS is tagged in CNY and USD; its series is now USD alone. On its five-year closes
    125 of 256 observations read a CNY EPS before this guard (the record's real run)."""
    f = _cf("JOYY")
    assert _raw_units(f, "EarningsPerShareDiluted") == {"CNY/shares", "USD/shares"}
    assert {p.unit for p in cc.extract_points(f, "eps_diluted", currency=cc.REPORTING)} == {
        "USD/shares"}


def test_the_fiscal_calendar_reads_a_yuan_reporter() -> None:
    """A period's dates are the same in any currency, so the calendar is not withheld."""
    years = cc.fiscal_year_ends(_cf("QFIN"))
    assert years and date(2025, 12, 31) in years[max(years)]


# --- the P/E level --------------------------------------------------------------------------------

def _bars(price: float) -> list[PriceBar]:
    start = REF - timedelta(days=5 * 365)
    return [PriceBar(internal_id="X", bar_date=start + timedelta(days=i), open=price, high=price,
                     low=price, close=price, volume=0.0, source="test")
            for i in range(5 * 365 + 1)]


def test_a_yuan_eps_makes_no_level_and_keeps_its_percentile() -> None:
    """NEGATIVE: QFIN's EPS in CNY never makes a P/E level against a USD price. The percentile
    ranks one series in one currency, so it is the same as for the identical series in dollars;
    POSITIVE: that dollar series makes a level."""
    eps = [p for p in cc.extract_points(_cf("QFIN"), "eps_diluted", currency=cc.REPORTING)
           if p.is_annual]
    assert {p.unit for p in eps} == {"CNY/shares"}
    pe, pct = pe_current_and_percentile(_bars(5.67), eps, reference_date=REF)
    assert pe.value is None and "CNY" in str(pe.note) and "FPI1b" in str(pe.note)
    dollars = [p.model_copy(update={"unit": "USD/shares"}) for p in eps]
    pe_usd, pct_usd = pe_current_and_percentile(_bars(5.67), dollars, reference_date=REF)
    assert pe_usd.value is not None
    assert pct.value is not None and pct.value == pct_usd.value


def test_the_screen_withholds_a_yuan_level_and_keeps_g3s_percentile() -> None:
    """END TO END through the screen's own enrich: QFIN's record carries no P/E level, names the
    currency, and keeps the percentile G3 reads; its snapshot names the currency too."""
    from vinci.schemas.data_record import DataRecord, Identity
    from vinci.screens.assemble import enrich_with_fundamentals

    facts = _cf("QFIN")

    class _Edgar:
        def companyfacts(self, cik: str) -> dict[str, Any]:
            return facts

        def fundamental_snapshot(self, cik: str) -> Any:
            return compute_fundamental_snapshot("0001741530", facts)

    # QFIN's own identity as the 2026-10-16 store holds it
    ident = Identity(internal_id="SEC-0001741530-QFIN", issuer_id="ISS-0001741530",
                     cik="0001741530", ticker="QFIN", mic="XNAS", exchange="Nasdaq",
                     eod_symbol="QFIN", name="Qfin Holdings, Inc.", sic="6199")
    rec = DataRecord.model_construct(identity=ident, ads=None)
    got = enrich_with_fundamentals(rec, edgar=_Edgar(), price_bars=_bars(5.67),  # type: ignore[arg-type]
                                   reference_date=REF).fundamentals
    assert got.pe.value is None and "CNY" in str(got.pe.note)
    assert got.pe_pctile_vs_history.value is not None
    assert got.op_income_sign.value is None and "CNY" in str(got.op_income_sign.note)


@pytest.mark.parametrize(("path", "function"), [
    ("vinci/screens/assemble.py", "enrich_with_fundamentals"),
    ("vinci/dossier/mechanical.py", "_at_latest_close"),
    ("vinci/cli.py", "_pc_valuation"),
    ("vinci/theme_intelligence/market.py", "edgar_eps"),
])
def test_every_reader_that_ranks_a_pe_reads_eps_in_the_filers_own_currency(
        path: str, function: str) -> None:
    """Each caller of `pe_current_and_percentile` reads EPS with ``currency=REPORTING``. Read in
    dollars, a yuan reporter's series would be empty and its percentile UNKNOWN, dropping a
    G3-gated name for a currency the percentile cannot see."""
    fn = next(n for n in ast.walk(ast.parse((ROOT / path).read_text()))
              if isinstance(n, ast.FunctionDef) and n.name == function)
    reads = [c for c in ast.walk(fn) if isinstance(c, ast.Call)
             and getattr(c.func, "id", None) == "extract_points"
             and any(isinstance(a, ast.Constant) and a.value == "eps_diluted" for a in c.args)]
    assert reads, f"{function} no longer reads eps_diluted"
    for c in reads:
        kw = {k.arg: k.value for k in c.keywords}
        assert isinstance(kw.get("currency"), ast.Name) and kw["currency"].id == "REPORTING", (
            f"{function} reads EPS in dollars only")


# --- the screen's snapshot and SBC ----------------------------------------------------------------

def test_a_yuan_reporters_snapshot_names_its_currency_and_a_dollar_reporters_reads() -> None:
    snap = compute_fundamental_snapshot("0001741530", _cf("QFIN"))
    for field in ("op_income_sign", "fcf_sign", "net_leverage", "net_debt_to_ocf",
                  "ebitda_annual", "net_debt", "eps_diluted_annual"):
        f = getattr(snap, field)
        assert f.value is None and "CNY" in str(f.note), field
    assert compute_fundamental_snapshot("0001174169", _cf("AQN")).op_income_sign.value is not None


def test_sbc_reads_a_40f_and_refuses_a_yuan_translation() -> None:
    """POSITIVE: AQN's 40-F states SBC of $13.0M for 2025, read with the form named.
    NEGATIVE: QFIN's 20-F tags SBC in USD only as a convenience translation, and it is refused,
    naming the currency, rather than read raw."""
    aqn = mech._sbc_line(_cf("AQN"), REF)
    assert aqn is not None and aqn.expense.value == pytest.approx(13.0)
    assert "40-F" in str(aqn.expense.source_ref)
    qfin = _cf("QFIN")
    assert "20-F" in {r["form"] for r in
                      qfin["facts"]["us-gaap"]["ShareBasedCompensation"]["units"]["USD"]}
    out = mech._sbc_line(qfin, REF)
    assert out is not None and out.expense.value is None and "CNY" in str(out.expense.note)


# --- the annual-report gates ----------------------------------------------------------------------

def _filing(form: str, acc: str, *, filed: str = "2026-04-01", doc: str | None = "doc.htm",
            report: str | None = "2025-12-31") -> Filing:
    return Filing(cik="0000000001", form=form, filing_date=date.fromisoformat(filed),
                  accession=acc, items=[], primary_doc=doc,
                  report_date=date.fromisoformat(report) if report else None)


class _Edgar:
    """`recent_filings` as the real client answers it: only the forms asked for, newest first."""

    def __init__(self, filings: list[Filing], facts: dict[str, Any] | None = None) -> None:
        self.filings, self.facts = filings, facts or {}
        self.asked: list[tuple[str, ...]] = []

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        self.asked.append(forms)
        return [f for f in self.filings if f.form in forms]

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return self.facts


class _Http:
    def __init__(self, texts: dict[str, str] | None = None,
                 jsons: dict[str, Any] | None = None) -> None:
        self.texts, self.jsons = texts or {}, jsons or {}
        self.urls: list[str] = []

    def get_text(self, url: str, ttl_seconds: int | None = None) -> str:
        self.urls.append(url)
        return next((v for k, v in self.texts.items() if url.endswith(k)), "<html></html>")

    def get_json(self, url: str, ttl_seconds: int | None = None) -> Any:
        self.urls.append(url)
        return next(v for k, v in self.jsons.items() if url.endswith(k))


def test_segment_profit_reads_a_20f_instance() -> None:
    """ARCO files a 20-F: its three divisions are read off the instance, the form named."""
    acc, name = "0001628280-26-028950", "arco-20251231_htm.xml"
    http = _Http(texts={name: (_INST / f"ARCO_{acc}.xml").read_text()},
                 jsons={"index.json": {"directory": {"item": [{"name": name}]}}})
    out = mech._segment_profit(_Edgar([_filing("20-F", acc)]), http, "0001508478")  # type: ignore[arg-type]
    assert out is not None and out.value is not None
    assert [r.segment for r in out.value.rows] == [
        "Brazil", "South Latin America Division", "North Latin America Division"]
    assert "EDGAR 20-F" in str(out.source_ref) and "(20-F XBRL)" in out.value.line


def test_an_ifrs_instance_is_refused_not_read_as_a_single_segment() -> None:
    """NEGATIVE: LPL's instance declares us-gaap and tags only ifrs-full. Read on US GAAP's axis
    it shows no segment, which would read as a single-segment filer; it is refused, named."""
    text = (_INST / "LPL_0001193125-26-183413.xml").read_text()
    assert "fasb.org/us-gaap" in text and "<us-gaap:" not in text
    with pytest.raises(sf.SegmentFactsUnavailableError, match="IFRS"):
        sf.parse_instance(text, accession="0001193125-26-183413")


def _pointer_rows(ticker: str) -> list[Any]:
    f = _IDX["filings"][ticker]
    orig = mech._exhibit_names
    mech._exhibit_names = lambda http, cik, acc: f["names"]  # type: ignore[assignment]
    try:
        out = mech._covenant_pointers(_Edgar([_filing(f["form"], f["accession"])]), None,  # type: ignore[arg-type]
                                      "0000000001", [], REF)
    finally:
        mech._exhibit_names = orig  # type: ignore[assignment]
    return list(out.value or [])


def test_a_20f_files_its_material_contracts_as_exhibit_4() -> None:
    """POSITIVE: ARCO's 20-F files seven contracts as Exhibits 4.13–4.19, and only those are read.
    NEGATIVE: ASR's carries page images named inside Exhibit 4.19, and no image is read."""
    arco = _pointer_rows("ARCO")
    assert [(r.family, r.filing) for r in arco] == [
        ("material contracts (20-F exhibit index)", "latest 20-F")]
    assert arco[0].exhibits == [n for n in _IDX["filings"]["ARCO"]["names"]
                                if n.startswith("exhibit4")]
    assert len(arco[0].exhibits) == 7
    asr = _pointer_rows("ASR")
    assert asr and all(n.endswith(".htm") for n in asr[0].exhibits)
    assert any(n.endswith(".jpg") and "ex4d19" in n for n in _IDX["filings"]["ASR"]["names"])


def test_a_10ks_exhibit_4_is_not_a_material_contract() -> None:
    """NEGATIVE: a 10-K's Exhibit 4.x defines securities. ZLAB's 10-K files its description of
    securities as Exhibit 4.5, and only its Exhibit 10.x are read."""
    rows = _pointer_rows("ZLAB")
    assert rows and rows[0].filing == "latest 10-K"
    assert "ex45-descriptionofsecuriti.htm" in _IDX["filings"]["ZLAB"]["names"]
    assert "ex45-descriptionofsecuriti.htm" not in rows[0].exhibits
    assert all("ex10" in n for n in rows[0].exhibits)


def test_the_maturity_check_reads_a_20f_or_40f_as_the_latest_periodic() -> None:
    for form in ("20-F", "40-F"):
        edgar = _Edgar([_filing(form, f"ACC-{form}")])
        http = _Http()
        src = mech._maturity_sources(edgar, http, "0000000001", None, None, REF)  # type: ignore[arg-type]
        assert [(s.form, s.accession) for s in src] == [(form, f"ACC-{form}")], form
        assert http.urls and http.urls[0].endswith("/doc.htm"), form


def _primary(edgar: _Edgar, http: _Http) -> Any:
    from vinci.dossier.ciq import CiqBundle

    rec = SimpleNamespace(identity=SimpleNamespace(cik="0000000001", ticker="X"))
    layer = SimpleNamespace(capital_structure=None, leverage_survival=None)
    ps, _lat, _drivers = mech._primary_source(rec, edgar, http, CiqBundle.from_files("X", []),  # type: ignore[arg-type]
                                              REF, layer)  # type: ignore[arg-type]
    return ps


def test_the_primary_source_pass_reads_a_20f_when_the_filer_files_no_10q() -> None:
    """POSITIVE: a dollar reporter's 20-F is read for its sections; a filer that files 10-Qs is
    still read on its newest 10-Q, as before."""
    ps = _primary(_Edgar([_filing("20-F", "ACC-20F")], _cf("AQN")), _Http())
    assert ps.filing is not None and ps.filing.source_ref == "20-F ACC-20F"
    both = _Edgar([_filing("10-Q", "ACC-10Q"), _filing("20-F", "ACC-20F")], _cf("AQN"))
    ps = _primary(both, _Http())
    assert ps.filing is not None and ps.filing.source_ref == "10-Q ACC-10Q"


def test_the_primary_source_pass_does_not_read_a_yuan_reporters_20f() -> None:
    """NEGATIVE: the section parser reads "$" amounts, and a yuan reporter's "US$" figures are
    convenience translations. Its 20-F is not fetched, and the flag names the currency."""
    http = _Http()
    ps = _primary(_Edgar([_filing("20-F", "ACC-20F")], _cf("QFIN")), http)
    assert ps.filing is None and not any(u.endswith("/doc.htm") for u in http.urls)
    assert any("ACC-20F" in q and "CNY" in q for q in ps.qa_flags), ps.qa_flags


def test_the_graph_reads_a_foreign_filers_annual_report() -> None:
    edgar = _Edgar([_filing("20-F", "ACC-20F")])
    got = latest_10k_excerpts(edgar, "0000000001", http=_Http())  # type: ignore[arg-type]
    assert got is not None and got[0] == "ACC-20F"


#: NAK's own annual reports, as its submissions index lists them: a 40-F every year since 2017,
#: and a 20-F before that. The first cut of this build read the 2016 20-F as NAK's material
#: contracts and its sections (the real run: 6 and 12 such 40-F filers, back to DNN's 2005 20-F).
_NAK = [_filing("40-F", "0001654954-26-003025", filed="2026-03-31", doc="ndm_40f.htm"),
        _filing("20-F", "0001062993-16-009358", filed="2016-05-02", doc="form20f.htm",
                report="2015-12-31")]


def test_a_filer_that_now_files_40fs_is_not_read_on_an_old_20f_for_contracts() -> None:
    """NEGATIVE: the newest annual report decides, and a 40-F has no material-contracts class."""
    orig = mech._exhibit_names
    mech._exhibit_names = lambda http, cik, acc: ["ex4-1.htm"]  # type: ignore[assignment]
    try:
        out = mech._covenant_pointers(_Edgar(_NAK), None, "0001164771", [], REF)  # type: ignore[arg-type]
    finally:
        mech._exhibit_names = orig  # type: ignore[assignment]
    assert not [r for r in (out.value or []) if r.family.startswith("material contracts")]


def test_a_filer_that_now_files_40fs_is_not_read_on_an_old_20f_for_sections() -> None:
    """NEGATIVE: NAK's sections are not read from its 2016 20-F, which is not fetched."""
    http = _Http()
    ps = _primary(_Edgar(_NAK, _cf("AQN")), http)
    assert ps.filing is None and not any("form20f.htm" in u for u in http.urls)
