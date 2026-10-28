"""FPI4 — a depositary line's per-share figures are read per ADS, on its own filing's ratio.

THE DEFECT (STATE §5.0 row 4, `docs/records/2026-10-28-fpi-readiness-measured-per-name.md`). A
depositary line is priced per ADS and its filer reports per ORDINARY share, and nothing converted
between them: QFIN's screened P/E divided $5.67 an ADS by a per-ordinary-share EPS, GPCR's anchor
would divide its equity by 213,929,572 ordinary shares under a price for 71,309,857 ADSs. The
universe's cap was never wrong — it sizes on Polygon's ADS-denominated count (#541) — so the ratio
is applied where a PER-SHARE figure meets the ADS price, and nowhere else.

Every ratio pin reads a REAL filing (`tests/fixtures/ads_ratio_covers.json`: each name's cover
lines and the real text around its depositary mentions; `ratio_from` on them equals `read_ratio`
on the whole document, recorded per name).
"""
from __future__ import annotations

import ast
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import anchor as an
from vinci.dossier.mechanical import in_traded_units
from vinci.edgar.concepts import ConceptPoint
from vinci.resolver.ads_ratio import ratio_from, statements, title_statements
from vinci.resolver.instrument import match_line
from vinci.schemas.listing import AdsRatio
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import pe_current_and_percentile
from vinci.screens.run import _gate_inputs, listing_basis

_FIX = json.loads(Path("tests/fixtures/ads_ratio_covers.json").read_text())
_BY = {n["ticker"]: n for n in _FIX["names"]}


def _read(ticker: str) -> AdsRatio:
    n = _BY[ticker]
    return ratio_from([tuple(x) for x in n["cover_lines"]], n["depositary_text"], form=n["form"],
                      filed=date.fromisoformat(n["filed"]), accession=n["accession"])


# --- the reader, on real filings -----------------------------------------------------------------

@pytest.mark.parametrize(("ticker", "ratio", "source"), [
    # the hand-checked ratios of the #837 measurement
    ("TSM", 5.0, "filing text"), ("BABA", 8.0, "12(b) title"), ("TM", 10.0, "filing text"),
    ("HMC", 3.0, "filing text"), ("BP", 6.0, "filing text"), ("SHEL", 2.0, "12(b) title"),
    ("HSBC", 5.0, "12(b) title"), ("SMFG", 0.6, "filing text"), ("KT", 0.5, "filing text"),
    ("LPL", 0.5, "filing text"), ("QFIN", 2.0, "12(b) title"), ("GPCR", 3.0, "12(b) title"),
    # the three the measurement itself read wrong, and this reader reads right
    ("RERE", 2 / 3, "12(b) title"), ("TAL", 1 / 3, "12(b) title"), ("SKM", 5 / 9, "filing text"),
])
def test_each_ratio_is_read_from_the_issuers_own_filing(ticker: str, ratio: float,
                                                        source: str) -> None:
    """POSITIVE, one per shape: a title ("each representing two Class A ordinary shares"), the text
    ("each ADS represents five (5) common shares"), a fraction ("one-half of one share", "3/5 of
    one share", "five-ninths of one share"), N-for-M ("every three ADSs represent two"; "each
    three representing one")."""
    got = _read(ticker)
    assert got.status == "known", got.reason
    assert got.ordinary_per_ads == pytest.approx(ratio, rel=1e-5)
    assert got.source == source
    assert got.accession == _BY[ticker]["accession"] and got.quote
    # the fixture's cut text reads exactly as the whole document did
    whole = _BY[ticker]["read_on_whole_document"]
    assert (whole["status"], whole["source"]) == ("known", source)


def test_the_fixture_reads_as_the_whole_document_for_every_name() -> None:
    """The frozen text is a cut of each filing; the cut changes no answer (a guard on the
    fixture, so a pin never passes on text the real document does not hold)."""
    for n in _FIX["names"]:
        got, whole = _read(n["ticker"]), n["read_on_whole_document"]
        assert (got.status, got.source) == (whole["status"], whole["source"]), n["ticker"]
        if got.known:
            assert got.ordinary_per_ads == pytest.approx(whole["ordinary_per_ads"], rel=1e-5)


def test_a_title_on_the_ads_row_counts_when_the_symbol_sits_on_the_ordinary_row() -> None:
    """HSBC tags its symbol to "Ordinary Shares, nominal value US$0.50 each" AND to its ADS row,
    and the one row a symbol match keeps (`match_line`, what `registered_line` reads) is the
    ordinary one — which states no ratio. Every depositary title is read, so the ADS row's ratio is
    found."""
    lines = [tuple(x) for x in _BY["HSBC"]["cover_lines"]]
    kept = match_line(lines, "HSBC", form="20-F", filed=date(2026, 2, 25), accession="a")
    assert kept is not None and kept.title and kept.title.startswith("Ordinary Shares")
    assert not title_statements(kept.title).ratios
    assert _read("HSBC").ordinary_per_ads == 5.0


def test_a_fraction_is_never_read_as_its_numerator() -> None:
    """NEGATIVE: the count patterns refuse a number followed by a fraction — KT's "one-half of one
    share" is 0.5, never 1; SMFG's "3/5 of one share" is 0.6, never 3."""
    assert [v for v, _q in statements(
        "American Depositary Shares, each representing one-half of one share").ratios] == [0.5]
    assert [round(v, 6) for v, _q in statements(
        "each American Depositary Share representing 3/5 of one share").ratios] == [0.6]
    assert [round(v, 6) for v, _q in title_statements(
        "ADSs, each representing five-ninths of one share of Common Stock").ratios] == [0.555556]
    # where the fraction is phrased so no fraction rule reads it, the numerator guard ALONE keeps
    # its "one" from being counted: nothing is stated, rather than 1
    assert statements("American Depositary Shares, each representing one half share").ratios == []
    assert title_statements("American Depositary Shares, each representing one half share"
                            ).ratios == []


def test_several_ratios_are_refused_with_every_value_named() -> None:
    """NEGATIVE: BIDU's 20-F states its current ratio (eight shares per ADS) beside the ones it
    replaced (ten ADSs per share, one per share); GRFS states 1 and 0.5. Which is current cannot be
    told from the words — refused, each value named, never the first one taken."""
    for ticker, values in (("BIDU", ("0.1", "1", "8")), ("GRFS", ("0.5", "1"))):
        got = _read(ticker)
        assert got.status == "refused" and got.ordinary_per_ads is None, ticker
        assert got.reason and all(v in got.reason for v in values), got.reason


def test_two_titles_that_disagree_are_refused() -> None:
    """NEGATIVE, at the title tier: two depositary titles with different ratios decide nothing."""
    got = ratio_from([("X", "American Depositary Shares, each representing two ordinary shares"),
                      ("XP", "American Depositary Shares, each representing four ordinary shares")],
                     "", form="20-F", filed=date(2026, 4, 1), accession="0000000000-26-000001")
    assert got.status == "refused" and "2, 4" in (got.reason or "")


def test_a_filing_that_states_no_ratio_is_refused() -> None:
    """NEGATIVE (ASML, as filed): its cover registers only its ordinary shares and its text never
    says what an ADS represents. Refused with that reason — never 1:1 by default."""
    got = _read("ASML")
    assert got.status == "refused" and "neither" in (got.reason or "")


def test_an_ads_of_units_is_refused_never_read_as_shares() -> None:
    """NEGATIVE (KOF, as filed): "American Depositary Shares, each representing 10 units" — a unit
    is a bundle of shares, and how many is not in these words. Refused, never read as 10 shares."""
    got = _read("KOF")
    assert got.status == "refused" and "UNITS" in (got.reason or "")


def test_the_title_outranks_the_text() -> None:
    """A ratio a title states decides, whatever the text says: QFIN's own title (two) against
    BIDU's text, which states three different ratios on its own."""
    got = ratio_from([tuple(x) for x in _BY["QFIN"]["cover_lines"]],
                     _BY["BIDU"]["depositary_text"], form="20-F", filed=date(2026, 4, 27),
                     accession=_BY["QFIN"]["accession"])
    assert got.status == "known" and got.ordinary_per_ads == 2.0 and got.source == "12(b) title"


# --- the screen's P/E ----------------------------------------------------------------------------

def _eps(value: float, end: str, filed: str) -> ConceptPoint:
    e = date.fromisoformat(end)
    return ConceptPoint(concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares",
                        value=value, period_start=e - timedelta(days=364), period_end=e,
                        filed=date.fromisoformat(filed), fy=e.year, fp="FY", form="20-F",
                        accession="acc")


def _bars(n: int, ref: date) -> list[PriceBar]:
    return [PriceBar(internal_id="SEC-0001741530-QFIN", bar_date=ref - timedelta(days=n - 1 - i),
                     open=5.0 + i * 0.01, high=5.1 + i * 0.01, low=4.9 + i * 0.01,
                     close=5.0 + i * 0.01, volume=1000.0, source="EOD")
            for i in range(n)]


_REF = date(2026, 10, 16)
_QFIN_EPS = [_eps(3.15, "2025-12-31", "2026-04-27"), _eps(2.83, "2024-12-31", "2025-03-25"),
             _eps(1.84, "2023-12-31", "2024-04-26")]
_QFIN_ADS = AdsRatio(status="known", ordinary_per_ads=2.0, source="12(b) title",
                     quote="American depositary shares, each representing two Class A ordinary "
                           "shares", form="20-F", filed=date(2026, 4, 27),
                     accession="0001104659-26-049501")


def test_a_depositary_lines_pe_is_price_per_ads_over_eps_per_ads() -> None:
    """QFIN's USD convenience EPS, 3.15 per ordinary share, two per ADS: the level is the price ÷
    6.30, half the per-ordinary reading, and it names the ratio's filing. The PERCENTILE IS
    RATIO-FREE: every observation divides by the same constant, so it is identical."""
    bars = _bars(400, _REF)
    raw_pe, raw_pct = pe_current_and_percentile(bars, _QFIN_EPS, reference_date=_REF, min_points=5)
    pe, pct = pe_current_and_percentile(bars, _QFIN_EPS, reference_date=_REF, min_points=5,
                                        ads=_QFIN_ADS)
    assert raw_pe.value is not None and pe.value == pytest.approx(raw_pe.value / 2.0)
    assert "× 2" in (pe.note or "") and "0001104659-26-049501" in (pe.note or "")
    assert pct == raw_pct


def test_a_refused_ratio_withholds_the_level_and_keeps_the_percentile() -> None:
    """NEGATIVE: no stated ratio, no per-ADS level — UNKNOWN with the refusal's reason, never the
    per-ordinary figure under an ADS price. The percentile cannot be moved by a constant ratio, so
    it stands."""
    bars = _bars(400, _REF)
    refused = AdsRatio(status="refused", reason="neither a depositary 12(b) title … states",
                       form="20-F", filed=date(2026, 4, 1), accession="acc")
    raw_pe, raw_pct = pe_current_and_percentile(bars, _QFIN_EPS, reference_date=_REF, min_points=5)
    pe, pct = pe_current_and_percentile(bars, _QFIN_EPS, reference_date=_REF, min_points=5,
                                        ads=refused)
    assert raw_pe.value is not None and pe.value is None
    assert "REFUSED" in (pe.note or "") and "neither a depositary" in (pe.note or "")
    assert pct == raw_pct


def test_a_line_that_is_not_a_depositary_is_read_as_before() -> None:
    """NEGATIVE: ``ads`` None is every common stock — unchanged, byte for byte."""
    bars = _bars(400, _REF)
    assert (pe_current_and_percentile(bars, _QFIN_EPS, reference_date=_REF, min_points=5)
            == pe_current_and_percentile(bars, _QFIN_EPS, reference_date=_REF, min_points=5,
                                         ads=None))


# --- the screen's record -------------------------------------------------------------------------

class _Rec:
    """The two attributes `_gate_inputs` reads beside ``ads``."""

    def __init__(self, ads: AdsRatio | None) -> None:
        self.prices, self.fundamentals, self.ads = None, None, ads


def test_the_ratio_rides_on_the_screens_row_with_its_filing() -> None:
    """The run's row carries the ratio G3's level used — value, filing date, accession, quote — or
    the refusal (value None, the reason as the note). A common stock's row carries no such key."""
    row = _gate_inputs(_Rec(_QFIN_ADS), [], window_start={})
    got = row["ads_ratio"]
    assert got.value == 2.0 and got.as_of == date(2026, 4, 27)
    assert "0001104659-26-049501" in got.source and "two Class A" in (got.note or "")
    refused = AdsRatio(status="refused", reason="states 2 different ones", form="20-F",
                       filed=date(2026, 4, 1), accession="acc-1")
    r = _gate_inputs(_Rec(refused), [], window_start={})["ads_ratio"]
    assert r.value is None and r.as_of is None and r.note == "states 2 different ones"
    assert "ads_ratio" not in _gate_inputs(_Rec(None), [], window_start={})


class _Ident:
    def __init__(self, eod_symbol: str, cik: str) -> None:
        self.eod_symbol, self.cik = eod_symbol, cik


class _Resolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def ads_ratio(self, cik: str, as_of: date) -> AdsRatio:
        self.calls.append(cik)
        return _QFIN_ADS


def test_only_a_line_typed_depositary_reads_a_ratio_once_per_issuer() -> None:
    """The SAME type test the universe sizes on (#541): an `ADRC`/`GDR` line reads its issuer's
    ratio, once; a `CS` line — including an FPI's own ordinary share (ZIM) — reads none."""
    res = _Resolver()
    read = listing_basis({"QFIN": "ADRC", "ZIM": "CS", "TV": "GDR"}, res, _REF)
    assert read(_Ident("ZIM", "0001654126")) is None  # type: ignore[arg-type]
    assert read(_Ident("QFIN", "0001741530")) == _QFIN_ADS  # type: ignore[arg-type]
    assert read(_Ident("QFIN", "0001741530")) == _QFIN_ADS  # type: ignore[arg-type]
    assert read(_Ident("TV", "0000912892")) is not None  # type: ignore[arg-type]
    assert res.calls == ["0001741530", "0000912892"]


def test_both_production_screens_pass_the_listing_basis() -> None:
    """`screen_universe` reads every line as its own unit when no ``listing`` is passed, so the two
    production call sites — the weekly run and `vinci screen` — must pass it."""
    for path in ("vinci/orchestrator.py", "vinci/cli.py"):
        calls = [n for n in ast.walk(ast.parse(Path(path).read_text()))
                 if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "screen_universe"]
        assert calls, path
        for c in calls:
            assert any(k.arg == "listing" for k in c.keywords), f"{path}:{c.lineno}"


def test_a_stored_candidate_carries_the_key_only_for_a_depositary_line() -> None:
    """A common stock's stored record has NO `ads` key — absent, never null — so every committed
    candidate row written before the field round-trips unchanged; a depositary line's has it."""
    rows = [json.loads(json.loads(line)["payload"])
            for line in Path("data/snapshots/candidate_records.jsonl").read_text().splitlines()
            if line.strip()]
    assert rows and all("ads" not in r["data_record"] for r in rows)
    from vinci.schemas.candidate import CandidateRecord
    from vinci.store import Store
    rec = CandidateRecord.model_validate(rows[0])
    with Store(":memory:") as st:
        st.save_candidate(rec)
        plain = json.loads(st._conn.execute("SELECT payload FROM candidate_records").fetchone()[0])
        st.save_candidate(rec.model_copy(update={
            "data_record": rec.data_record.model_copy(update={"ads": _QFIN_ADS})}))
        dep = json.loads(st._conn.execute("SELECT payload FROM candidate_records").fetchone()[0])
    assert "ads" not in plain["data_record"]
    assert dep["data_record"]["ads"]["ordinary_per_ads"] == 2.0


# --- the dossier's share counts ------------------------------------------------------------------

def test_an_ordinary_count_is_put_in_the_unit_the_line_trades_in() -> None:
    """GPCR's cover count, 213,929,572 ordinary shares, three per ADS: 71,309,857.3 ADSs. A common
    stock's count is untouched; a depositary line with no stated ratio gets no count at all."""
    assert in_traded_units(213_929_572, None) == (213_929_572, None)
    got, why = in_traded_units(213_929_572, _gpcr(3.0))
    assert got == pytest.approx(71_309_857.33, rel=1e-9) and why is None
    refused = AdsRatio(status="refused", reason="no ratio stated", accession="a", form="10-Q",
                       filed=date(2026, 8, 6))
    got, why = in_traded_units(213_929_572, refused)
    assert got is None and why and "no ratio stated" in why
    assert in_traded_units(None, _gpcr(3.0)) == (None, None)


def _gpcr(r: float) -> AdsRatio:
    return AdsRatio(status="known", ordinary_per_ads=r, source="12(b) title",
                    quote="American Depositary Shares (ADSs), each representing three ordinary "
                          "shares", form="10-Q", filed=date(2026, 8, 6),
                    accession="0001104659-26-092057")


def _gpcr_facts() -> dict[str, Any]:
    """GPCR's 10-Q for the quarter to 2026-06-30 (0001104659-26-092057), as filed."""
    def row(v: int) -> dict[str, Any]:
        return {"start": "2026-04-01", "end": "2026-06-30", "val": v, "form": "10-Q",
                "accn": "0001104659-26-092057", "filed": "2026-08-06", "fy": 2026, "fp": "Q2"}
    return {"facts": {"us-gaap": {
        an._DILUTED_TAG: {"units": {"shares": [row(217_957_000)]}},
        an._BASIC_TAG: {"units": {"shares": [row(217_957_000)]}}}}}


def _gpcr_mech(ads: AdsRatio | None, count: float) -> dict[str, Any]:
    si: dict[str, Any] = {"shares_out": {"value": count, "status": "present",
                                         "source_ref": "EDGAR XBRL shares outstanding"}}
    if ads is not None:
        si["ads_ratio"] = ads.model_dump(mode="json")
    return {"stock_info": si}


def test_the_anchor_divides_a_depositary_lines_equity_by_ads() -> None:
    """GPCR, as filed: the page's count is 71,309,857 ADSs and the filer's basic average is
    217,957,000 ORDINARY shares — compared in one unit (72,652,333 ADSs, 1.8% above) the count is
    corroborated and used, and the diluted average the base falls back on is in ADSs too."""
    facts = _gpcr_facts()
    c = an._traded_unit_counts(_gpcr_mech(_gpcr(3.0), 213_929_572 / 3), facts)
    assert c.out == pytest.approx(213_929_572 / 3)
    assert c.dil is not None and c.dil.value == pytest.approx(217_957_000 / 3)
    assert "÷ 3 ordinary shares per ADS" in c.per_ads_source
    denom = an.share_denominator(_gpcr_mech(_gpcr(3.0), 213_929_572 / 3), facts)
    assert denom is not None and denom[0] == pytest.approx(213_929_572 / 3)


def test_left_unconverted_the_same_count_would_be_refused() -> None:
    """NEGATIVE — what the conversion of the filer's average prevents: an ADS count checked against
    an ORDINARY average sits ~67% below it and is refused, so the base would fall to the diluted
    average — in ordinary shares, under an ADS price."""
    facts = _gpcr_facts()
    out, why = an._shares_outstanding(_gpcr_mech(None, 213_929_572 / 3), facts,
                                      an._latest_point(facts, an._DILUTED_TAG))
    assert out is None and why.startswith(an.SHARES_REFUSED)


def test_a_depositary_line_with_no_stated_ratio_gets_no_count() -> None:
    """NEGATIVE: every count withheld, with the reason, so no per-share base is struck."""
    refused = AdsRatio(status="refused", reason="no ratio stated", accession="a", form="10-Q",
                       filed=date(2026, 8, 6))
    c = an._traded_unit_counts(_gpcr_mech(refused, 213_929_572), _gpcr_facts())
    assert c.dil is None and c.out is None and c.inc is None
    assert c.refused and "no ratio stated" in c.refused
    assert an.share_denominator(_gpcr_mech(refused, 213_929_572), _gpcr_facts()) is None


def test_a_common_stocks_counts_are_untouched() -> None:
    """NEGATIVE: no `ads_ratio` on the page — the counts are the filer's, exactly as before."""
    facts = _gpcr_facts()
    c = an._traded_unit_counts(_gpcr_mech(None, 213_929_572), facts)
    assert c.dil is not None and c.dil.value == 217_957_000 and c.out == 213_929_572
    assert c.per_ads_source == "" and c.refused is None


# --- the dossier's own record (#840 round 1, Codex P1) ------------------------------------------

def _stored_record(ticker: str, cik: str) -> Any:
    """A real committed candidate's data record, re-keyed to ``ticker`` — the shape both dossier
    routes hand assembly: a candidate stored before 2026-10-28, or a maintenance standalone, neither
    carrying ``ads``."""
    from vinci.schemas.candidate import CandidateRecord
    line = Path("data/snapshots/candidate_records.jsonl").read_text().splitlines()[0]
    rec = CandidateRecord.model_validate(json.loads(json.loads(line)["payload"])).data_record
    ident = rec.identity.model_copy(update={"ticker": ticker, "eod_symbol": ticker, "cik": cik})
    return rec.model_copy(update={"identity": ident})


def test_a_dossier_record_without_its_listing_basis_gets_one_at_assembly() -> None:
    """A maintained ADR with no current candidate is assembled from `_standalone_record`, which no
    screen touched, and a candidate stored before 2026-10-28 carries no `ads` either — so assembly
    reads the basis itself, through the SAME `listing_basis` the screen uses: a depositary line
    gets its ratio (QFIN 2); a common stock stays None; a record that already carries one keeps
    it."""
    from vinci.dossier import assemble as asm
    res = _Resolver()
    types = {"QFIN": "ADRC", "ZIM": "CS"}
    got = asm._with_listing_basis(_stored_record("QFIN", "0001741530"), resolver=res,
                                  reference_date=_REF, security_types=types)
    assert got.ads == _QFIN_ADS
    plain = asm._with_listing_basis(_stored_record("ZIM", "0001654126"), resolver=res,
                                    reference_date=_REF, security_types=types)
    assert plain.ads is None
    carried = _stored_record("QFIN", "0001741530").model_copy(update={"ads": _gpcr(3.0)})
    kept = asm._with_listing_basis(carried, resolver=res, reference_date=_REF,
                                   security_types=types)
    assert kept.ads == _gpcr(3.0) and res.calls == ["0001741530"]


def test_assembly_applies_the_listing_basis_to_whichever_record_it_is_given() -> None:
    """`assemble_one` passes its record — candidate or standalone — through `_with_listing_basis`
    before anything reads it, so neither route can publish an ordinary-share figure under an ADS
    price."""
    from vinci.dossier import assemble as asm
    fn = next(n for n in ast.walk(ast.parse(Path(asm.__file__).read_text()))
              if isinstance(n, ast.FunctionDef) and n.name == "assemble_one")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
             and getattr(n.func, "id", None) == "_with_listing_basis"]
    assert calls, "assemble_one does not apply the listing basis to its record"
