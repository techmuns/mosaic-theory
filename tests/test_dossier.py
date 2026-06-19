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

from mosaic.dossier import ciq, manual_store
from mosaic.dossier import ciq_sheets as cs
from mosaic.dossier import mechanical as dm
from mosaic.dossier import schemas as ds
from mosaic.dossier import synthesis as syn
from mosaic.graph.llm import LlmClient, LlmError

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
            range_position=_u(),
        ),
        quality=ds.Quality(
            fcf_sign=_u(), free_cash_flow=_u(), margin_trend=_u(), net_debt_to_ebitda=_u(),
            interest_coverage=_u(), share_count_trend=_u(), liquidity_covenant_flags=_u(),
        ),
        concentration=ds.Concentration(segments=_u(), customers=_u(), geographic=_u()),
        drawdown_cause=ds.DrawdownCause(shape=_u(), gap_down_dates=_u(), filings=[]),
        idiosyncratic_vs_shared=ds.IdiosyncraticVsShared(
            name_180d_return=ds.Sourced.present(-0.726, source_ref="EOD FUBO 180d"),
            market_180d_return=ds.Sourced.present(0.156, source_ref="EOD IWM 180d"),
            rel_vs_market=ds.Sourced.present(-0.882, source_ref="EOD name-IWM 180d"),
            cohort=_u(), read=_u(),
        ),
        consensus_context=ds.ConsensusContext(
            eps_trend=_u(), revenue_trend=_u(), revision_history=_u()
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


def test_reclassified_boundary_blocks_cross_basis_yoy() -> None:
    inc: list[list[typing.Any]] = [
        ["For the Fiscal Period", "Reclassified\n12 months\nDec-2023", "12 months\nDec-2024"],
        ["Total Revenue", 700, 800],
        ["Gross Profit", 300, 360],
        ["EBITDA", 320, 360],
    ]
    assert cs._reclassified_cols(inc[0]) == {1}  # col1 carries the restated basis
    mt = cs.margin_trend(_fin_bundle({"Income Statement": inc}, freq="annual"))
    assert "UNAVAILABLE (reclassified-basis boundary)" in (mt.value or "")  # YoY refused


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
