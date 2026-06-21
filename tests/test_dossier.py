"""Dossier-assembler verification — the assemble-not-conclude line, held by STRUCTURE.

The load-bearing tests here are structural, not behavioural: the dossier schema has nowhere to put a
conclusion, and the dossier package imports nothing that could write a verdict to the ledger. Same
discipline as the ranker's no-forward-returns AST guard.
"""

from __future__ import annotations

import ast
import typing
from datetime import date
from pathlib import Path

import pytest
from pydantic import BaseModel

from mosaic.dossier import assemble as dass
from mosaic.dossier import ciq, manual_store
from mosaic.dossier import ciq_sheets as cs
from mosaic.dossier import mechanical as dm
from mosaic.dossier import render as dr
from mosaic.dossier import requirements as dreq
from mosaic.dossier import schemas as ds
from mosaic.dossier import synthesis as syn
from mosaic.edgar.client import EdgarClient, FundamentalSnapshot, all_unknown_snapshot
from mosaic.graph.llm import AnthropicLlmClient, LlmClient, LlmError
from mosaic.schemas import data_record as sdr
from mosaic.schemas.envelope import DataField, SourceTier

# A conclusion = verdict / recommendation / direction / score / rating / probability (or a synonym).
# No dossier field may carry one: the LLM can't conclude because there is nowhere to put it.
_FORBIDDEN = (
    "verdict", "recommend", "rating", "score", "direction", "probability", "conviction",
    "buy", "sell", "avoid", "target_price", "price_target", "fair_value", "upside", "downside",
)


def _reachable_models(root: type[BaseModel]) -> set[type[BaseModel]]:
    """Every pydantic model reachable from ``root`` via its field annotations (incl. generics)."""
    seen: set[type[BaseModel]] = set()
    stack: list[type[BaseModel]] = [root]
    while stack:
        model = stack.pop()
        if model in seen:
            continue
        seen.add(model)
        for field in model.model_fields.values():
            for anno in [field.annotation, *typing.get_args(field.annotation or object)]:
                origin = typing.get_origin(anno) or anno
                for cand in [origin, *typing.get_args(anno)]:
                    if isinstance(cand, type) and issubclass(cand, BaseModel):
                        stack.append(cand)
    return seen


def test_dossier_schema_has_no_conclusion_field() -> None:
    """No field anywhere in the Dossier tree may name a verdict/score/direction/probability/etc."""
    models = _reachable_models(ds.Dossier)
    # sanity: the walk actually reached the synthesis sub-models (else the guard is vacuous)
    expected = {ds.Synthesis, ds.SourcedPoint, ds.TwinCase, ds.DecisiveQuestion, ds.MechanicalLayer}
    assert expected <= models
    offenders: list[str] = []
    for model in models:
        for fname in model.model_fields:
            low = fname.lower()
            if any(tok in low for tok in _FORBIDDEN):
                offenders.append(f"{model.__name__}.{fname}")
    assert not offenders, f"dossier schema carries conclusion-shaped field(s): {offenders}"


def test_synthesis_is_the_only_llm_output_and_carries_no_conclusion() -> None:
    """The synthesis model's fields are exactly the spec'd five — no place for a conclusion."""
    assert set(ds.Synthesis.model_fields) == {
        "bull_points", "bear_points", "twin_reference_cases", "decisive_question", "key_unknowns",
    }


def test_twin_cases_are_never_numeric() -> None:
    """Analogues inform reasoning; they never carry a recovery rate / base rate / probability."""
    for fname, field in ds.TwinCase.model_fields.items():
        assert field.annotation is str, f"TwinCase.{fname} must be a string, not a number"


def test_dossier_package_imports_no_ledger_or_scoring() -> None:
    """The assembler must not be able to write a verdict: it imports no ledger/scoring module."""
    pkg = Path(__file__).resolve().parents[1] / "mosaic" / "dossier"
    forbidden = {"mosaic.ledger", "mosaic.scoring"}
    offenders: list[str] = []
    for py in sorted(pkg.glob("*.py")):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
            elif isinstance(node, ast.Import):
                mod = node.names[0].name
            else:
                continue
            if any(mod == f or mod.startswith(f + ".") for f in forbidden):
                offenders.append(f"{py.name}: imports {mod}")
    assert not offenders, f"dossier must not import ledger/scoring: {offenders}"


def test_sourced_contract_forbids_fabricated_values() -> None:
    """An UNKNOWN/MISSING fact must not carry a value — fail-loud, never a silent impute."""
    ok = ds.Sourced.present(1.0, source_ref="EOD bars …")
    assert ok.value == 1.0 and ok.status is ds.SourceStatus.PRESENT
    assert ds.Sourced.unknown(note="no XBRL tag").value is None
    assert ds.Sourced.missing(note="CIQ not pulled").value is None
    with pytest.raises(ValueError):
        ds.Sourced(value=1.0, source_ref=None, status=ds.SourceStatus.UNKNOWN)  # value on UNKNOWN
    with pytest.raises(ValueError):
        ds.Sourced(value=1.0, source_ref=None, status=ds.SourceStatus.PRESENT)  # PRESENT w/o ref


# --- behavioural: CIQ parsing, the manual store, and the synthesis guardrails ----------------


def test_ciq_format_classification(tmp_path: Path) -> None:
    """Real format is sniffed from header bytes, never the extension (ciq_extraction_notes rule)."""
    cases = {
        "real.rtf": (rb"{\rtf1\ansi hi}", ciq.CiqFormat.RTF_TEXT),
        "legacy.xls": (ciq._OLE_MAGIC + b"\x00" * 16, ciq.CiqFormat.BIFF_XLS),
        "transcript.rtf": (ciq._OLE_MAGIC + b"\x00" * 16, ciq.CiqFormat.OLE_DISGUISED),  # OLE, .rtf
        "book.pdf": (b"%PDF-1.7\n", ciq.CiqFormat.PDF),
        "sheet.xlsx": (b"PK\x03\x04rest", ciq.CiqFormat.OOXML),
        "filing.doc": (b"MIME-Version: 1.0\nContent-Type: text/html\n\n", ciq.CiqFormat.MIME_DOC),
    }
    for fname, (head, expected) in cases.items():
        p = tmp_path / fname
        p.write_bytes(head)
        assert ciq.classify(p) is expected, fname


def test_ciq_reads_real_rtf(tmp_path: Path) -> None:
    p = tmp_path / "kd.rtf"
    p.write_text(r"{\rtf1\ansi the quick brown fox jumped over the lazy dog many times indeed}")
    assert "quick brown fox" in ciq.read_text(p)


def test_local_folder_store_missing_is_not_a_crash(tmp_path: Path) -> None:
    """A missing CIQ folder yields no files (caller flags MISSING) — never an exception."""
    store = manual_store.LocalFolderStore(tmp_path)
    assert store.available("FUBO") is False
    assert store.files("FUBO") == []
    assert ciq.CiqBundle.from_files("FUBO", store.files("FUBO")).is_empty


def test_drive_store_is_an_unimplemented_interface() -> None:
    with pytest.raises(NotImplementedError):
        manual_store.DriveStore().files("FUBO")


def _u() -> typing.Any:
    return ds.Sourced.unknown(note="placeholder")


def _minimal_mech() -> ds.MechanicalLayer:
    """A mech layer with two PRESENT facts (the name's & rel returns) — the rest UNKNOWN/MISSING."""
    return ds.MechanicalLayer(
        valuation=ds.Valuation(
            pe=_u(), pe_percentile_5y=_u(), ev_ebitda=_u(), ev_ebitda_percentile_5y=_u(),
            ev_ebitda_adjusted_fwd=_u(), adjusted_eps=_u(), range_position=_u(),
        ),
        quality=ds.Quality(
            fcf_sign=_u(), free_cash_flow=_u(), margin_trend=_u(), net_debt_to_ebitda=_u(),
            net_debt_to_ebitda_adjusted=_u(), interest_coverage=_u(), share_count_trend=_u(),
            liquidity_covenant_flags=_u(), multi_year_trajectory=_u(),
        ),
        concentration=ds.Concentration(
            segments=_u(), segment_ebitda=_u(), customers=_u(), geographic=_u()
        ),
        drawdown_cause=ds.DrawdownCause(
            shape=_u(), gap_down_dates=_u(), filings=[], revised_guidance=_u()
        ),
        idiosyncratic_vs_shared=ds.IdiosyncraticVsShared(
            name_180d_return=ds.Sourced.present(-0.726, source_ref="EOD FUBO 180d"),
            market_180d_return=ds.Sourced.present(0.156, source_ref="EOD IWM 180d"),
            rel_vs_market=ds.Sourced.present(-0.882, source_ref="EOD name-IWM 180d"),
            cohort=_u(), read=_u(),
        ),
        consensus_context=ds.ConsensusContext(
            eps_trend=_u(), revenue_trend=_u(), revision_history=_u(), surprise_history=_u()
        ),
        management_commentary=_u(),
    )


class _FakeLlm(LlmClient):
    def __init__(self, payload: dict[str, typing.Any]) -> None:
        self._payload = payload

    @property
    def model(self) -> str:
        return "fake-model-1"

    def extract(
        self, *, system: str, user: str, tool: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        return self._payload


def test_synthesis_guardrails_flag_uncited_directional_and_numeric_twins() -> None:
    """Post-LLM guardrails: uncited point, directional language, numeric/untraceable twin all flag;
    a percentage rendering of a stored fraction (−72.6% from −0.726) does NOT false-flag."""
    payload = {
        "bull_points": [{"claim": "fell -72.6% vs IWM +15.6%", "source_ref": "EOD name-IWM 180d"}],
        "bear_points": [{"claim": "BUY now, clearly undervalued", "source_ref": "MADE-UP-REF"}],
        "twin_reference_cases": [
            {"name": "ExampleCo", "outcome": "recovered 50%", "distinguishing_fact": "x",
             "source": "fabricated source"},
        ],
        "decisive_question": {"question": "does the cause reverse?", "evidence_for": [],
                              "evidence_against": []},
        "key_unknowns": ["CIQ not pulled"],
    }
    synth, flags, log = syn.synthesize(
        _minimal_mech(), llm=_FakeLlm(payload), ticker="FUBO", name="FuboTV"
    )
    assert synth is not None
    assert synth.bull_points[0].cited is True  # source_ref present in the mech
    assert synth.bear_points[0].cited is False  # MADE-UP-REF does not trace
    text = " ".join(flags)
    assert "UNCITED bear_point" in text
    assert "DIRECTIONAL" in text
    assert any("TWIN" in f and "non-numeric" in f for f in flags)  # "recovered 50%" is numeric
    assert not any("UNTRACEABLE" in f for f in flags)  # -72.6 / 15.6 trace to -0.726 / 0.156
    assert "fake-model-1" in log and "RAW OUTPUT" in log


def test_synthesis_fails_loud_when_llm_errors() -> None:
    """An LLM with no usable output → None synthesis + a flag, never a fabricated dossier."""
    class _BadLlm(LlmClient):
        @property
        def model(self) -> str:
            return "bad"

        def extract(
            self, *, system: str, user: str, tool: dict[str, typing.Any]
        ) -> dict[str, typing.Any]:
            raise LlmError("no tool_use block")

    synth, flags, _ = syn.synthesize(_minimal_mech(), llm=_BadLlm(), ticker="X", name="X")
    assert synth is None
    assert any("synthesis failed" in f for f in flags)


# --- cause-parsing fixes surfaced by the VRRM run --------------------------------------------


def test_cause_labels_reflect_item_codes_not_blanket_earnings() -> None:
    """Fix #1: a gap-down is labelled by its 8-K item codes — never 'earnings' without 2.02."""
    assert dm._gap_label(["5.02", "9.01"]) == "management change (5.02)"  # CEO change, NOT earnings
    assert "earnings" in dm._gap_label(["2.02", "9.01"])  # 2.02 → earnings
    assert dm._gap_label(["1.02", "8.01"]) == "agreement termination (1.02) + other event (8.01)"
    assert dm.item_labels(["5.02"]) == ["5.02 Departure/Election of Directors or Certain Officers"]


def test_parse_8k_events_surfaces_catalyst_and_fails_loud() -> None:
    """Fix #2: the catalyst is parsed from the filing TEXT (source-bound); unparseable → by-hand."""
    body = (
        "Item 5.02 Departure of Directors or Certain Officers. On May 6, 2026, the Company's Chief "
        "Executive Officer notified the Board of his resignation, effective immediately. "
        "Item 8.01 Other Events. On May 6, 2026, the Company received an Avis Budget Group notice "
        "terminating the master services agreement. SIGNATURE"
    )
    events = dm.parse_8k_events(body, ["5.02", "8.01", "9.01"], "0001-26-00")
    text = " ".join(events)
    assert "resignation" in text or "Chief Executive Officer" in text  # CEO departure surfaced
    assert "Avis" in text  # the customer-termination catalyst surfaced
    assert not any("UNKNOWN" in e for e in events)  # both narrative items parsed
    assert all("9.01" not in e for e in events)  # exhibits carry no event
    # fail loud: a body with no item text → read-by-hand marker, never fabricated
    bad = dm.parse_8k_events("(no parseable content)", ["8.01"], "0001-26-99")
    assert "UNKNOWN" in bad[0] and "0001-26-99" in bad[0]


def test_cite_check_flags_missing_claim_bound_to_present_field() -> None:
    """Fix #5: a 'data is missing' point citing a PRESENT field's ref is flagged + uncited."""
    payload = {
        "bull_points": [],
        # claim asserts missing data but cites a PRESENT field's ref (not the MISSING marker)
        "bear_points": [{"claim": "Segment concentration data is unavailable",
                         "source_ref": "EOD name-IWM 180d"}],
        "twin_reference_cases": [],
        "decisive_question": {"question": "?", "evidence_for": [], "evidence_against": []},
        "key_unknowns": [],
    }
    synth, flags, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(payload), ticker="X", name="X")
    assert synth is not None
    assert synth.bear_points[0].cited is False
    assert any("MISMATCH" in f for f in flags)


# --- CIQ workbook-aware loader (the export structure ≠ one-file-per-module) -------------------


_Sheets = dict[str, list[list[typing.Any]]]


def _fin_bundle(sheets: _Sheets, freq: str = "quarterly") -> ciq.CiqBundle:
    """A CiqBundle with one Financials workbook whose sheets are pre-seeded (no .xls on disk)."""
    p = Path("/fake/Financials.xls")
    wb = ciq.CiqWorkbook(kind="financials", path=p, fmt=ciq.CiqFormat.BIFF_XLS, freq=freq)
    return ciq.CiqBundle(ticker="X", workbooks=(wb,), _cache={p: sheets})


def _fin_bundle2(annual: _Sheets, quarterly: _Sheets) -> ciq.CiqBundle:
    """A CiqBundle with an annual AND a quarterly Financials workbook (for the quarterly YoY)."""
    pa, pq = Path("/fake/A.xls"), Path("/fake/Q.xls")
    wa = ciq.CiqWorkbook(kind="financials", path=pa, fmt=ciq.CiqFormat.BIFF_XLS, freq="annual")
    wq = ciq.CiqWorkbook(kind="financials", path=pq, fmt=ciq.CiqFormat.BIFF_XLS, freq="quarterly")
    return ciq.CiqBundle(ticker="X", workbooks=(wa, wq), _cache={pa: annual, pq: quarterly})


def _est_bundle(sheets: _Sheets) -> ciq.CiqBundle:
    """A CiqBundle with one Estimates workbook (for the Surprise / Consensus / Revisions sheets)."""
    p = Path("/fake/Estimates.xls")
    wb = ciq.CiqWorkbook(kind="estimates", path=p, fmt=ciq.CiqFormat.BIFF_XLS, freq="quarterly")
    return ciq.CiqBundle(ticker="X", workbooks=(wb,), _cache={p: sheets})


def _eps_pt(year: int, val: float) -> dict[str, typing.Any]:
    return {"end": f"{year}-12-31", "start": f"{year}-01-01", "val": val,
            "filed": f"{year + 1}-02-15", "fp": "FY", "form": "10-K"}


def _facts(eps: list[tuple[int, float]], shares: float) -> dict[str, typing.Any]:
    """A minimal companyfacts dict: annual diluted-EPS points + a shares-outstanding instant."""
    return {"facts": {
        "us-gaap": {"EarningsPerShareDiluted": {
            "units": {"USD/shares": [_eps_pt(y, v) for y, v in eps]}}},
        "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            {"end": "2026-03-31", "val": shares, "filed": "2026-04-01", "form": "10-K"}]}}},
    }}


class _StubEdgar:
    """Duck-types the two EdgarClient methods _adjusted_facts / _pe_reconciliation use."""

    def __init__(self, facts: dict[str, typing.Any], net_debt: float) -> None:
        self._facts, self._net_debt = facts, net_debt

    def companyfacts(self, cik: int | str) -> dict[str, typing.Any]:
        return self._facts

    def fundamental_snapshot(self, cik: int | str) -> FundamentalSnapshot:
        return all_unknown_snapshot("0001682745").model_copy(update={
            "net_debt": DataField.present(
                self._net_debt, as_of=date(2026, 3, 31), source="EDGAR", tier=SourceTier.EDGAR
            )
        })


def _min_record(pe: float, *, price: float | None = None) -> sdr.DataRecord:
    """A DataRecord with fundamentals.pe (and optionally the last price) set — the rest UNKNOWN."""
    u: DataField[float] = DataField.unknown(source="x", tier=SourceTier.DERIVED)
    ui: DataField[int] = DataField.unknown(source="x", tier=SourceTier.EDGAR)
    last = (
        DataField.present(price, as_of=date(2026, 6, 17), source="EOD", tier=SourceTier.DERIVED)
        if price is not None else u
    )
    prices = sdr.PriceFeatures(
        last=last, high_52w=u, low_52w=u, drawdown_from_high=u, dist_from_low=u, ret_3m=u,
        ret_6m=u, ret_12m=u, rel_ret_vs_market=u, adv_90d_shares=u, adv_90d_usd=u,
        turnover=u, volume_spike=u,
    )
    funds = sdr.Fundamentals(
        ev_ebitda=u, ev_ebitda_pctile_vs_history=u,
        pe=DataField.present(pe, as_of=date(2026, 6, 17), source="EOD", tier=SourceTier.DERIVED),
        pe_pctile_vs_history=u, fcf_sign=ui, op_income_sign=ui, net_leverage=u,
    )
    return sdr.DataRecord(
        identity=sdr.Identity(
            internal_id="SEC-X", issuer_id="I", cik="0001682745", ticker="VRRM", mic="XNAS",
            exchange="Nasdaq", eod_symbol="VRRM", name="VRRM Inc.",
        ),
        market_cap=u, prices=prices, fundamentals=funds,
        stress=sdr.StressSignals(iv_pctile=u, short_interest=u),
        overall_coverage_tier=sdr.CoverageTier.US_FULL, as_of=date(2026, 6, 17),
    )


def test_clean_num_treats_ciq_blanks_as_unavailable() -> None:
    for blank in ("", "-", "—", "NM", "NA", "Entitlement Needed"):
        assert ciq.clean_num(blank) is None  # UNAVAILABLE — never coerced to 0
    assert ciq.clean_num("1,234.5") == 1234.5
    assert ciq.clean_num(5) == 5.0


def test_excel_date_handles_serial_and_string() -> None:
    assert ciq.excel_date(44377.0) == date(2021, 6, 30)  # Excel serial
    assert ciq.excel_date("Jan-31-2024") == date(2024, 1, 31)  # string
    assert ciq.excel_date("-") is None


def test_workbook_routing_finds_multiples_and_segments_inside_financials() -> None:
    """Core fix: Multiples + Segments are SUBSHEETS of the Financials workbook, by address."""
    mult: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44377.0, 44469.0, 44561.0, 44651.0],
        ["TEV/LTM EBITDA", "Average", 30, 25, 22, 11],
        ["", "High", 33, 28, 25, 13],
        ["", "Low", 28, 22, 18, 9],
        ["", "Close", 30.0, 20.0, 10.0, 10.0],  # history [30,20,10]; last col = current, excluded
    ]
    seg: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2024", "12 months Dec-31-2025"],
        ["Revenues", "", ""],
        ["Commercial Services", 372.0, 407.0],
        ["Government Solutions", 358.0, 390.0],
        ["  Total Revenues", 730.0, 797.0],
    ]
    b = _fin_bundle({"Multiples": mult, "Segments": seg})
    pct = cs.ev_ebitda_percentile(b)
    assert pct.status is ds.SourceStatus.PRESENT
    assert pct.value == round(1 / 3, 3)  # would be 0.5 if the partial last col were NOT excluded
    segs = cs.segments(b)
    assert segs.status is ds.SourceStatus.PRESENT
    assert "Commercial Services" in (segs.value or "") and "797" in (segs.value or "")


def test_quarterly_yoy_refuses_cross_basis_prior() -> None:
    """The same-quarter revenue YoY refuses a prior on a different (reclassified) basis — the
    trajectory then omits the YoY rather than computing across a basis change (notes ~line 204)."""
    quarterly: list[list[typing.Any]] = [
        ["For the Fiscal Period", "Reclassified\n3 months\nQ1 Mar-2025", "3 months\nQ4 Dec-2025",
         "3 months\nQ1 Mar-2026"],
        ["Total Revenue", 223.0, 262.0, 224.0],
    ]
    assert cs._reclassified_cols(quarterly[0]) == {1}  # the prior Q1 is on the restated basis
    annual: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-2025"],
        ["Total Revenue", 979.0], ["EBITDA", 362.0],
    ]
    b = _fin_bundle2({"Income Statement": annual}, {"Income Statement": quarterly})
    assert cs._quarterly_revenue_yoy(b) is None  # the only prior Q1 is cross-basis → refused


def test_interest_coverage_and_fcf_from_subsheets() -> None:
    inc: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12mo 2024", "12mo 2025"], ["EBITDA", 360, 400],
        ["Interest Expense", 40, 50],
    ]
    cf: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12mo 2024", "12mo 2025"],
        ["Levered Free Cash Flow", 120.0, 150.0],
    ]
    ic = cs.interest_coverage(_fin_bundle({"Income Statement": inc}, freq="annual"))
    assert ic.status is ds.SourceStatus.PRESENT and ic.value == 8.0  # 400 / 50
    fcf = cs.free_cash_flow(_fin_bundle({"Cash Flow": cf}, freq="annual"))
    assert fcf.status is ds.SourceStatus.PRESENT and fcf.value == 150.0


def test_missing_workbook_is_missing_absent_sheet_is_unknown() -> None:
    empty = ciq.CiqBundle(ticker="X", workbooks=())
    assert cs.ev_ebitda_percentile(empty).status is ds.SourceStatus.MISSING  # no financials wb
    absent: list[list[typing.Any]] = [["For the Fiscal Period", "x"]]  # wb present, no Multiples
    r = cs.ev_ebitda_percentile(_fin_bundle({"Income Statement": absent}))
    assert r.status is ds.SourceStatus.UNKNOWN and "Multiples" in (r.note or "")


def test_segment_ebitda_section_surfaces_profit_share() -> None:
    """The Segments EBITDA section parses to EBITDA share — the decision-relevant concentration:
    a segment can be 45% of revenue but 68% of profit (the Avis-in-Commercial-Services case)."""
    seg: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2025"],
        ["Revenues", ""],
        ["Commercial Services", 435.791],
        ["Government Solutions", 460.707],
        ["  Total Revenues", 979.079],
        ["EBITDA", ""],
        ["Commercial Services", 282.513],
        ["Government Solutions", 121.907],
        ["  Total EBITDA", 415.905],
    ]
    b = _fin_bundle({"Segments": seg}, freq="annual")
    rev, eb = cs.segments(b), cs.segment_ebitda(b)
    assert rev.status is ds.SourceStatus.PRESENT
    assert "Commercial Services 436 (45%)" in (rev.value or "")  # revenue share
    assert eb.status is ds.SourceStatus.PRESENT
    assert "Commercial Services 283 (68%)" in (eb.value or "")  # 282.5/415.9 — profit, not revenue
    assert "Segments (EBITDA" in (eb.source_ref or "")


def test_margin_trend_is_a_margin_trajectory() -> None:
    """'Margin trend' is the gross/EBITDA-margin trajectory across years (the trend), not single-
    period levels with a misfiled revenue YoY — growth is top-line, kept out of this field."""
    inc: list[list[typing.Any]] = [
        ["For the Fiscal Period", "Reclassified\n12 months\nDec-2023", "12 months\nDec-2024",
         "12 months\nDec-2025"],
        ["Total Revenue", 817.0, 879.0, 979.0],
        ["Gross Profit", 504.0, 537.0, 572.0],
        ["EBITDA", 306.0, 342.0, 362.0],
    ]
    mt = cs.margin_trend(_fin_bundle({"Income Statement": inc}, freq="annual"))
    assert mt.status is ds.SourceStatus.PRESENT
    v = mt.value or ""
    assert "EBITDA margin:" in v and "37%" in v  # 362/979 ≈ 37% — the margin trajectory
    assert "(R)" in v  # the reclassified basis is marked
    assert "YoY" not in v  # revenue growth is NOT reported under a margin label


def test_ev_ebitda_current_is_a_multiple_not_dollars() -> None:
    """ev_ebitda_current returns the TEV/LTM EBITDA MULTIPLE (~8.5x), never a dollar figure."""
    mult: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44377.0, 44469.0, 46112.0],
        ["TEV/LTM EBITDA", "Average", 15.0, 12.0, 8.6],
        ["", "Close", 15.7, 12.0, 8.5],
    ]
    ev = cs.ev_ebitda_current(_fin_bundle({"Multiples": mult}))
    assert ev.status is ds.SourceStatus.PRESENT and ev.value == 8.5  # the latest Close, a multiple


# --- item 1: the catalyst 8-K's Exhibit 99.1 revised-guidance fetch (offline parts) -----------
def test_revised_guidance_extracts_figures_block_not_lede() -> None:
    """Skips the press-release lede; surfaces the revised-outlook figures block verbatim. Absent a
    revised-outlook section → None (→ fail-loud UNKNOWN upstream). Numbers are never parsed here."""
    lede = (
        "Provides revised 2026 full-year outlook. Received a termination notice from Avis Budget "
        "Group, effective September 2026. "
    )
    filler = "The company is taking immediate actions to reduce costs and adapt operations. " * 12
    figures = (
        "Revised 2026 Full-Year Guidance the Company is revising its 2026 full-year financial "
        "outlook to the following: Total Revenue of $985 million to $995 million; Adjusted EBITDA "
        "of $380 million to $385 million; Adjusted EPS of $1.19 to $1.25; Free Cash Flow of $140 "
        "million to $150 million."
    )
    block = dm._extract_revised_guidance(lede + filler + figures)
    assert block is not None
    assert all(s in block for s in ("985", "380", "1.19", "140"))  # all four figures, verbatim
    assert "termination notice from Avis" not in block  # lede skipped (no figures in its window)
    assert dm._extract_revised_guidance("An earnings call. Revenue grew. No outlook given.") is None


def test_ex_991_name_matcher() -> None:
    assert dm._is_ex991("d123116dex991.htm")  # RR Donnelley 'dex991' form (VRRM's filer)
    assert dm._is_ex991("ex-99.1.htm") and dm._is_ex991("ex99d1.htm")
    assert not dm._is_ex991("ex99.2.htm")  # 99.2 is a different exhibit
    assert not dm._is_ex991("ex99.10.htm")  # 99.10, not 99.1
    assert not dm._is_ex991("FilingSummary.xml")  # not a readable document


# --- item 3: render formatters (raw float → legible at render; source value untouched) --------
def test_render_formatters() -> None:
    assert dr._mult(2.861674241263681) == "2.9x"
    assert dr._pctile(0.01036682615629984) == "1st %ile" and dr._pctile(0.0) == "0th %ile"
    assert dr._pct(-0.7263) == "-72.6%"
    assert dr._signword(1) == "positive" and dr._signword(-1) == "negative"


def test_render_formats_display_only_keeps_full_precision() -> None:
    """The hard fence: format at render; the stored Sourced.value keeps full precision."""
    s = ds.Sourced.present(2.861674241263681, source_ref="EDGAR net-debt/EBITDA")
    assert "2.9x" in dr._fact("Net debt / EBITDA", s, dr._mult)  # display formatted
    assert s.value == 2.861674241263681  # source value untouched


# --- item 4: customers Business-Relationships parse (no raw pipe-dump) -------------------------
def test_customers_relationship_parse() -> None:
    raw = (
        "Recently disclosed customers only|\n\nCustomers|\n|\n"
        "Customer Name|Relationship Type|Primary Industry|Source|\n"
        "Avis Budget Group, Inc. (NasdaqGS:CAR)|Customer|Passenger Ground Transportation|10-K|\n"
        "Business Description: Avis Budget Group, Inc. provides car rentals...|\n"
    )
    rows = cs._parse_business_relationships(raw)
    assert rows is not None and len(rows) == 1  # the 'Business Description' prose row is skipped
    assert rows[0].startswith("Avis Budget Group, Inc. (NasdaqGS:CAR) — Customer · Passenger")
    assert cs._parse_business_relationships("no table here|just text") is None  # fail loud


# --- item 2: transcript surfaces REMARKS, not the S&P estimates table / TOC -------------------
def test_transcript_prose_skips_estimates_table_and_toc() -> None:
    """management_commentary leads with management's prose — never CIQ's leading S&P estimates table
    or the dotted table-of-contents (qualitative window, no numbers table)."""
    text = (
        "FQ1 2026 Earnings Call S&P Global Estimates EPS 0.14 0.17 Revenue 223.40\n"
        "Call Participants .......... 3\nPresentation .......... 4\n"
        "Presentation \nOperator \nGood afternoon, and welcome to the First Quarter call."
    )
    prose = cs._transcript_prose(text)
    assert prose.lstrip().startswith("Operator")  # the real call opening, not the TOC/estimates
    assert "S&P Global Estimates" not in prose and "0.14" not in prose  # estimates table skipped
    assert "...." not in prose  # the dotted TOC skipped


def test_transcript_prose_anchors_past_legalese_and_carries_qa() -> None:
    """Anchor at the IR hand-off (past the operator intro + forward-looking-statements legalese) and
    carry the prepared remarks AND Q&A — the call's substance, surfaced in full, never curated."""
    text = (
        "S&P Estimates EPS 0.14 Revenue 223.40\nCall Participants ..... 3\n"
        "Operator Good afternoon and welcome to the call. I'll turn the presentation over to IR. "
        "IR: Thank you. Forward-looking statements involve risks and uncertainties; actual results "
        "may differ materially. With that, I will turn the call over to our CEO. "
        "CEO: Good afternoon, we had a solid quarter. " + "Prepared remarks continue. " * 40 +
        "Question and Answer Operator: first question. Analyst: the significant-customer renewal? "
        "CEO: those negotiations remain constructive."
    )
    prose = cs._transcript_prose(text)
    assert prose.startswith("turn the call over to our CEO")  # past operator + FLS legalese
    assert "risks and uncertainties" not in prose  # the legalese is skipped
    assert "turn the presentation over to IR" not in prose  # operator→IR hand-off skipped too
    assert all(s in prose for s in ("Question and Answer", "renewal", "constructive"))


# --- item 1: adjusted-basis figures parse; the GAAP-EPS caveat downgrades when they're shown ----
def test_adjusted_guidance_parse_and_eps_flag_downgrade() -> None:
    text = (
        "revising its outlook to: Total Revenue of $985 million to $995 million; Adjusted EBITDA "
        "of $380 million to $385 million; Adjusted EPS of $1.19 to $1.25."
    )
    eb, eps = dm._ADJ_EBITDA.search(text), dm._ADJ_EPS.search(text)
    assert eb is not None and (float(eb.group(1)), float(eb.group(2))) == (380.0, 385.0)
    assert eps is not None and (float(eps.group(1)), float(eps.group(2))) == (1.19, 1.25)
    rec, empty = _min_record(pe=5.5), ciq.CiqBundle(ticker="VRRM", workbooks=())
    open_warn = dm._eps_caveat_flags(rec, empty, eps_resolved=False)  # adjusted basis absent
    resolved = dm._eps_caveat_flags(rec, empty, eps_resolved=True)  # adjusted basis now shown
    assert any("understates earnings power" in f for f in open_warn)  # open warning
    assert not any("understates earnings power" in f for f in resolved)  # downgraded to a fact


# --- item 2: geographic = the 'Geographic Segments' → 'Revenues' block, not the business one ----
def test_geographic_section_parsed() -> None:
    seg: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2025"],
        ["Business Segments", ""], ["Revenues", ""], ["Commercial Services", 436.0],
        ["  Total Revenues", 979.0],
        ["Geographic Segments", ""],
        ["For the Fiscal Period", "12 months Dec-31-2025"],
        ["Revenues", ""], ["United States", 846.0], ["Australia", 66.0],
        ["  Total Revenues", 979.0],
    ]
    b = _fin_bundle({"Segments": seg}, freq="annual")
    geo = cs.geographic(b)
    assert geo.status is ds.SourceStatus.PRESENT
    assert "United States 846 (86%)" in (geo.value or "") and "Geographic" in (geo.source_ref or "")
    assert "Commercial Services 436" in (cs.segments(b).value or "")  # business block unaffected


# --- item 3: clean same-quarter YoY from the quarterly file; annual margins + guards kept --------
def test_quarterly_revenue_yoy_lives_in_trajectory_not_margin() -> None:
    """The clean same-quarter revenue YoY (Q1-2026 vs Q1-2025) now lives in the trajectory/growth
    field; margin_trend carries only the margin trajectory (no growth under a margin label)."""
    annual: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2025", "LTM 12 months Mar-31-2026"],
        ["Total Revenue", 979.0, 979.4], ["Gross Profit", 572.0, 557.0], ["EBITDA", 362.0, 358.0],
    ]
    quarterly: list[list[typing.Any]] = [
        ["For the Fiscal Period", "3 months Q1 Mar-31-2025", "3 months Q4 Dec-31-2025",
         "3 months Q1 Mar-31-2026"],
        ["Total Revenue", 223.254, 261.938, 223.568],
    ]
    b = _fin_bundle2({"Income Statement": annual}, {"Income Statement": quarterly})
    tr = cs.multi_year_trajectory(b)
    assert "Revenue YoY" in (tr.value or "") and "+0.1%" in (tr.value or "")  # YoY in trajectory
    mt = cs.margin_trend(b)
    assert "EBITDA margin:" in (mt.value or "") and "YoY" not in (mt.value or "")  # margins only


# --- item 4: multi-year arc shows per-period values, basis marked, never YoY'd across ------------
def test_multi_year_trajectory_marks_reclassified_basis() -> None:
    inc: list[list[typing.Any]] = [
        ["For the Fiscal Period", "Reclassified 12 months Dec-2023", "12 months Dec-2024",
         "LTM 12 months Mar-2026"],
        ["Total Revenue", 817.0, 879.0, 979.0], ["EBITDA", 371.0, 401.0, 358.0],
    ]
    seg: list[list[typing.Any]] = [
        ["For the Fiscal Period", "Reclassified 12 months Dec-2023", "12 months Dec-2024"],
        ["EBITDA", "", ""], ["Commercial Services", 242.0, 267.0], ["  Total EBITDA", 371.0, 401.0],
    ]
    tr = cs.multi_year_trajectory(_fin_bundle({"Income Statement": inc, "Segments": seg}, "annual"))
    v = tr.value or ""
    assert tr.status is ds.SourceStatus.PRESENT
    assert "Revenue:" in v and "817" in v and "979" in v  # per-period values surfaced
    assert "(R)" in v and "Mar-2026 (LTM)" in v  # reclassified + LTM basis marked
    assert "Commercial Services EBITDA:" in v  # segment EBITDA arc
    assert "→" in v and "%" not in v  # per-period values only — no cross-basis growth computed


# --- durability: segment-vs-consolidated EBITDA basis is labelled + reconciled ----------------
def test_segment_ebitda_reconciles_to_consolidated() -> None:
    """Segment EBITDA shares are pre-corporate (segment sum); the consolidated EBITDA + the
    unallocated-corporate reconciling item are surfaced so the two 'EBITDA' bases are distinct."""
    seg: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2025"],
        ["EBITDA", ""], ["Commercial Services", 283.0], ["Government Solutions", 122.0],
        ["  Total EBITDA", 416.0],
    ]
    inc: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2025"], ["EBITDA", 362.0],
    ]
    eb = cs.segment_ebitda(_fin_bundle({"Segments": seg, "Income Statement": inc}, freq="annual"))
    assert eb.status is ds.SourceStatus.PRESENT
    assert "segment-EBITDA sum (pre-corporate) 416" in (eb.value or "")  # the share base, labelled
    assert "consolidated EBITDA 362 (~54 unallocated corporate)" in (eb.value or "")  # reconciled


# --- durability: the adjusted-basis multiples ARITHMETIC (EV/adj-EBITDA, net-debt/adj-EBITDA) --
def test_adjusted_facts_compute_forward_ev_and_leverage() -> None:
    """_adjusted_facts computes forward EV/adj-EBITDA = (price×shares + net-debt)/FY-guide-EBITDA
    and covenant net-debt/adj-EBITDA — general arithmetic from 99.1 + EDGAR + EOD, no literals."""
    rg = ds.Sourced.present(
        "Adjusted EBITDA of $380 million to $385 million; Adjusted EPS of $1.19 to $1.25",
        source_ref="EDGAR 8-K X Ex-99.1",
    )
    edgar = _StubEdgar(_facts([(2024, 0.85)], shares=151_906_653), net_debt=1_008_723_000.0)
    adj_eps, adj_ev, adj_lev = dm._adjusted_facts(
        _min_record(pe=5.5, price=4.71), typing.cast(EdgarClient, edgar), rg
    )
    assert "~2.6x fwd-adj" in (adj_lev.value or "")  # 1008.7M / 382.5M ≈ 2.6x
    assert "~4.5x" in (adj_ev.value or "")  # (4.71×151.9M + 1008.7M) / 382.5M ≈ 4.5x
    assert "$1.19–$1.25" in (adj_eps.value or "") and "~3.9x" in (adj_eps.value or "")  # adj P/E


# --- durability: the P/E-distortion RESOLUTION path (trailing GAAP vs forward adjusted) --------
def test_pe_reconciliation_resolves_with_forward_adjusted() -> None:
    """A one-time-distorted trailing GAAP EPS + a sourced forward adjusted EPS → a RESOLVED P/E
    statement (not an open 'verify'); without the forward adjusted EPS, the original flag stands."""
    edgar = _StubEdgar(
        _facts([(2021, 0.28), (2022, 0.28), (2023, 0.28), (2024, 0.85)], shares=1.5e8), net_debt=1e9
    )
    rec, empty = _min_record(pe=5.5, price=4.71), ciq.CiqBundle(ticker="X", workbooks=())
    rg = ds.Sourced.present("Adjusted EPS of $1.19 to $1.25", source_ref="EDGAR 8-K X Ex-99.1")
    resolved = dm._pe_reconciliation(rec, typing.cast(EdgarClient, edgar), empty, rg)
    assert resolved is not None and resolved.startswith("RESOLVED")
    assert "~3.9x" in resolved  # 4.71 / 1.22 (mid of $1.19–1.25)
    no_guide = dm._pe_reconciliation(rec, typing.cast(EdgarClient, edgar), empty, _u())
    assert no_guide is not None and "verify against normalized/forward EPS" in no_guide  # open flag


# --- durability: Surprise history parsed + GAAP-basis labelled --------------------------------
def test_surprise_history_parsed_and_gaap_labelled() -> None:
    """Annual estimate surprise (Estimates→Surprise) parses by fiscal year, EPS labelled GAAP-basis
    (distinct from the 99.1 adjusted guide); +beat / −miss."""
    surprise: list[list[typing.Any]] = [
        ["NasdaqCM:VRRM", 2023.0, 2024.0, 2025.0],
        ["EPS (GAAP)", -0.32, -0.76, -0.11],
        ["Revenue", 0.01, 0.0, 0.02],
    ]
    s = cs.surprise_history(_est_bundle({"Surprise": surprise}))
    assert s.status is ds.SourceStatus.PRESENT
    assert "GAAP-EPS surprise:" in (s.value or "") and "FY2024 -76%" in (s.value or "")
    assert "GAAP-EPS basis" in (s.value or "")  # basis distinguished from the adjusted guide


# --- truncation fail-loud (change 1) + transcript pointer (change 3) --------------------------
class _StubLlm(LlmClient):
    """An LlmClient whose extract() returns a fixed dict — to exercise synthesize() truncation."""

    def __init__(self, result: dict[str, typing.Any]) -> None:
        self._result = result

    def extract(
        self, *, system: str, user: str, tool: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        return self._result

    @property
    def model(self) -> str:
        return "stub-model"


def test_synthesis_truncated_response_is_unavailable_not_blank() -> None:
    """A partial tool response (missing required fields) → synthesis UNAVAILABLE + a loud flag,
    never a blank decisive_question / key_unknowns indistinguishable from a genuine empty field."""
    partial = {  # missing decisive_question + key_unknowns — the truncation signature
        "bull_points": [{"claim": "x", "source_ref": "EOD FUBO 180d"}],
        "bear_points": [], "twin_reference_cases": [],
    }
    synth, flags, log = syn.synthesize(
        _minimal_mech(), llm=_StubLlm(partial), ticker="X", name="X Co"
    )
    assert synth is None  # NOT a blank synthesis
    assert any("UNAVAILABLE" in f for f in flags) and "INCOMPLETE" in log
    complete = {
        "bull_points": [], "bear_points": [], "twin_reference_cases": [],
        "decisive_question": {"question": "Q?", "evidence_for": [], "evidence_against": []},
        "key_unknowns": ["u1"],
    }
    synth2, _, _ = syn.synthesize(_minimal_mech(), llm=_StubLlm(complete), ticker="X", name="X Co")
    assert synth2 is not None and synth2.decisive_question.question == "Q?"  # complete → parses


def test_extract_fails_loud_on_max_tokens_truncation() -> None:
    """llm.extract raises (never returns a partial dict) when the tool call is cut at max_tokens."""
    from types import SimpleNamespace
    client = AnthropicLlmClient(model="claude-x", api_key="test")
    block = SimpleNamespace(type="tool_use", input={"bull_points": []})

    def made(stop: str) -> typing.Callable[..., typing.Any]:
        return lambda **kw: SimpleNamespace(content=[block], stop_reason=stop)

    client._client = SimpleNamespace(messages=SimpleNamespace(create=made("max_tokens")))  # type: ignore[assignment]
    with pytest.raises(LlmError):
        client.extract(system="s", user="u", tool={"name": "t"})
    client._client = SimpleNamespace(messages=SimpleNamespace(create=made("tool_use")))  # type: ignore[assignment]
    assert client.extract(system="s", user="u", tool={"name": "t"}) == {"bull_points": []}


def test_management_commentary_is_a_pointer_not_embedded() -> None:
    """The dossier carries a POINTER to the transcript file, never an embedded/curated excerpt."""
    p = Path("/fake/VRRM Q1 2026 Earnings Call.rtf")
    wb = ciq.CiqWorkbook(
        kind="transcript", path=p, fmt=ciq.CiqFormat.OLE_DISGUISED, freq="quarterly"
    )
    mc = cs.management_commentary(ciq.CiqBundle(ticker="VRRM", workbooks=(wb,)))
    assert mc.status is ds.SourceStatus.PRESENT
    assert "VRRM Q1 2026 Earnings Call.rtf" in (mc.value or "")
    assert "read" in (mc.value or "").lower()
    assert len(mc.value or "") < 300  # a pointer, not a 40K embed
    assert "VRRM Q1 2026 Earnings Call.rtf" in (mc.source_ref or "")
    assert cs.transcript_for_synthesis(ciq.CiqBundle(ticker="X", workbooks=())) is None  # no file


# --- the CIQ requirements manifest: ONE definition, two consumers (must not drift) ------------


def _req_bundle(*specs: tuple[str, str | None]) -> ciq.CiqBundle:
    """A CiqBundle holding workbooks of the given (kind, freq) — presence only (no sheets)."""
    wbs = tuple(
        ciq.CiqWorkbook(kind=k, path=Path(f"/fake/{k}-{f}.xls"), fmt=ciq.CiqFormat.BIFF_XLS, freq=f)
        for k, f in specs
    )
    return ciq.CiqBundle(ticker="VRRM", workbooks=wbs)


_ALL_REQUIRED: tuple[tuple[str, str | None], ...] = (
    ("financials", "annual"), ("financials", "quarterly"), ("estimates", None), ("customers", None),
)


def test_requirements_single_source_drives_both_consumers() -> None:
    """THE single-source guard: the MISSING-manifest path (assemble) and the `requirements` command
    both read :data:`CIQ_MODULES`, so they cannot drift. If the assembler's required set changes in
    one place, both outputs change together — asserted by deriving both from the same definition."""
    # the assemble module imports the SAME requirements module that defines CIQ_MODULES (one object)
    assert dass.requirements is dreq

    required_defn = {m.module for m in dreq.CIQ_MODULES if m.required}

    # consumer 1 — the MISSING-manifest path (assemble_one → manifest_flags/missing_required)
    empty = _req_bundle()
    manifest_set = {m.module for m in dreq.missing_required(empty)}
    assert manifest_set == required_defn  # an empty folder is missing exactly the required set

    # consumer 2 — the `dossier requirements` command payload
    payload = dreq.as_payload("VRRM")
    command_required = {m["module"] for m in payload["modules"] if m["required"]}
    command_all = {m["module"] for m in payload["modules"]}
    assert command_required == required_defn
    assert command_all == {m.module for m in dreq.CIQ_MODULES}

    # the two consumers agree BECAUSE they share the one definition — the anti-drift property
    assert manifest_set == command_required


def test_requirements_partial_folder_flags_only_whats_missing() -> None:
    """A partial folder (only the annual Financials present) flags exactly the still-missing
    required modules — not the one already pulled, and never the optional transcript."""
    partial = _req_bundle(("financials", "annual"))
    missing = {m.module for m in dreq.missing_required(partial)}
    assert "Financials — Annual" not in missing  # present → satisfied
    assert missing == {
        "Financials — Quarterly", "Estimates Report",
        "Business Relationships (Customers & Suppliers)",
    }
    flags = dreq.manifest_flags(partial, ticker="VRRM", location="data/manual/ciq/VRRM")
    assert len(flags) == 3 and all("pull CIQ 'Financials — Quarterly'" in f or "Estimates" in f
                                   or "Business Relationships" in f for f in flags)


def test_requirements_financials_freq_is_strict() -> None:
    """The Annual and Quarterly Financials are DISTINCT required exports (notes line ~116): an
    annual workbook satisfies the annual slot but NOT the quarterly one (no lenient fallback)."""
    annual_only = _req_bundle(("financials", "annual"))
    ann = next(m for m in dreq.CIQ_MODULES if m.freq == "annual")
    qtr = next(m for m in dreq.CIQ_MODULES if m.freq == "quarterly")
    assert dreq.module_present(annual_only, ann) is True
    assert dreq.module_present(annual_only, qtr) is False


def test_requirements_full_folder_yields_no_flags_even_without_optional() -> None:
    """Every REQUIRED module present → no MISSING flags, even though the OPTIONAL transcript is
    absent (optional modules never block — the dossier degrades gracefully)."""
    full = _req_bundle(*_ALL_REQUIRED)
    assert dreq.missing_required(full) == []
    assert dreq.manifest_flags(full, ticker="VRRM", location="x") == []
    # the transcript IS optional and IS absent from `full`
    transcript = next(m for m in dreq.CIQ_MODULES if m.workbook_kind == "transcript")
    assert transcript.required is False
    assert not dreq.module_present(full, transcript)


def test_requirements_workbook_kinds_match_bundle_vocabulary() -> None:
    """Every module's ``workbook_kind`` must be a real :class:`CiqBundle` kind — else the presence
    check could never match and a required module would be silently always-missing."""
    valid = set(ciq._WORKBOOK_KEYWORDS)
    for m in dreq.CIQ_MODULES:
        assert m.workbook_kind in valid, f"{m.module}: unknown workbook kind {m.workbook_kind}"


def test_requirements_edgar_free_documents_dont_double_pull() -> None:
    """The manifest documents the don't-double-pull rule: 10-K, 8-K, Form 4 are FREE on EDGAR and
    must NOT be manually uploaded — and none of them is asked for as a CIQ module."""
    free_blob = " ".join(e.input + " " + e.edgar_source for e in dreq.EDGAR_FREE_INPUTS).lower()
    assert "8-k" in free_blob and "10-k" in free_blob and "form 4" in free_blob
    assert all("edgar" in (e.edgar_source or "").lower() for e in dreq.EDGAR_FREE_INPUTS)
    # we never ask the human to upload an EDGAR-free filing as a CIQ module
    module_blob = " ".join(m.module for m in dreq.CIQ_MODULES).lower()
    assert "10-k" not in module_blob and "form 4" not in module_blob and "8-k" not in module_blob


def test_requirements_payload_records_carry_every_field() -> None:
    """Each module record exposes the full structured contract the frontend upload UI consumes."""
    payload = dreq.as_payload("vrrm")
    assert payload["ticker"] == "VRRM" and payload["manual_ciq_root"] == "data/manual/ciq/VRRM/"
    for m in payload["modules"]:
        assert set(m) == {
            "module", "workbook_kind", "freq", "sheets", "used_for", "granularity", "lookback",
            "required", "expected_path",
        }
        assert m["expected_path"] == "data/manual/ciq/VRRM/"
        assert m["granularity"] in {"annual", "quarterly", "both", "snapshot"}
    assert [e["input"] for e in payload["edgar_free_do_not_upload"]]  # non-empty


def test_requirements_checklist_renders_for_a_name() -> None:
    """The human checklist names the path, every required module, and the DO-NOT-upload section."""
    text = dreq.render_checklist("VRRM")
    assert "data/manual/ciq/VRRM/" in text
    for m in dreq.CIQ_MODULES:
        if m.required:
            assert m.module in text
    assert "DO NOT upload" in text and "EDGAR" in text
    # the generic (no-ticker) form uses the template placeholder
    assert "data/manual/ciq/<TICKER>/" in dreq.render_checklist(None)
