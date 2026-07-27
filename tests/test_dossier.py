"""Dossier-assembler verification — the assemble-not-conclude line, held by STRUCTURE.

The load-bearing tests here are structural, not behavioural: the dossier schema has nowhere to put a
conclusion, and the dossier package imports nothing that could write a verdict to the ledger. Same
discipline as the ranker's no-forward-returns AST guard.
"""

from __future__ import annotations

import ast
import json
import os
import re
import tempfile
import typing
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from vinci import cli
from vinci.dossier import assemble as dass
from vinci.dossier import ciq, manual_store
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import covenant_extract as ce
from vinci.dossier import edgar_fundamentals as efb
from vinci.dossier import flags as dflags
from vinci.dossier import mechanical as dm
from vinci.dossier import render as dr
from vinci.dossier import requirements as dreq
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.edgar.client import (
    EdgarClient,
    Filing,
    FtsHit,
    FundamentalSnapshot,
    all_unknown_snapshot,
)
from vinci.graph.llm import AnthropicLlmClient, LlmClient, LlmError
from vinci.schemas import data_record as sdr
from vinci.schemas.envelope import DataField, SourceTier
from vinci.sec import build_sec_http
from vinci.universe import benchmark_identity

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
    # sanity: the walk actually reached the synthesis sub-models AND the new catalyst-path models
    # (else the guard is vacuous — catalyst_path must be covered by the no-conclusion check too)
    expected = {
        ds.Synthesis, ds.SourcedPoint, ds.TwinCase, ds.DecisiveQuestion, ds.MechanicalLayer,
        ds.CatalystPath, ds.RevisionEvent,
        # PR B — the no-conclusion walk must reach the comps blocks (no upside/discount field)
        ds.PeerRow, ds.LeverageSurvival, ds.ImpliedRow, ds.ImpliedValuation,
        # PR C — the walk must reach the financial-summary appendix (a table of facts, no verdict)
        ds.FinRow, ds.FinTable, ds.FinancialSummary,
        # PR E — the walk must reach the structured capital structure (instruments + wall/covenant
        # pointers are FACTS, never a solvency verdict — no probability/risk/direction field);
        # RC-1.5d — CovenantTerm's new rate components (margin_pct/bps, floor_pct, pik_pct) are
        # numeric FACTS, not conclusions — the guard must reach it to prove none is verdict-shaped
        ds.CapitalStructure, ds.CapitalInstrument, ds.CovenantTerm,
        # PR G — the walk must reach the implied-expectations block (fundamentals-space; the block-
        # scoped fence forbids price/equity/value/upside/discount fields — asserted separately)
        ds.ImpliedExpectations, ds.ImpliedExpectationRow,
        # RC-1 — the walk must reach the primary-source extracts + derived surfaces: FACTS /
        # verbatims, no verdict field (EventImpact carries 'effect', not the forbidden 'direction')
        ds.PrimarySource, ds.ReleaseExtract, ds.GuidanceItem, ds.ReconciliationValue,
        ds.OneOffItem, ds.EventImpact, ds.FilingSectionExtract, ds.GoingConcern, ds.DebtTranche,
        ds.MaturityWall, ds.ConcentrationCustomer, ds.CustomerConcentration, ds.Commitment,
    }
    assert expected <= models
    # match a forbidden token only at snake_case WORD boundaries (^/_/$), not as a bare substring —
    # so a factual 'operating_drivers' isn't flagged for the 'rating' inside 'ope-RATING' (the
    # substring hazard: 'operating'⊃'rating', 'grating'⊃'rating', …), while 'buy_rating' /
    # 'conviction_score' / a lone 'direction' still trip. Field names here are snake_case, so a
    # boundary match is exact, not a loosening.
    offenders: list[str] = []
    for model in models:
        for fname in model.model_fields:
            low = fname.lower()
            if any(re.search(rf"(?:^|_){re.escape(tok)}(?:$|_)", low) for tok in _FORBIDDEN):
                offenders.append(f"{model.__name__}.{fname}")
    assert not offenders, f"dossier schema carries conclusion-shaped field(s): {offenders}"


def test_synthesis_is_the_only_llm_output_and_carries_no_conclusion() -> None:
    """The synthesis model's fields are exactly the spec'd six — no place for a conclusion.
    evidence_balance is a committed balance read, NOT a verdict/score/direction."""
    assert set(ds.Synthesis.model_fields) == {
        "evidence_balance", "bull_points", "bear_points", "twin_reference_cases",
        "decisive_question", "key_unknowns",
    }


def test_synthesis_surfaces_operating_drivers_digest_and_rule() -> None:
    """(PR-B B) Synthesis makes the operating drivers SALIENT so the bull/bear ground in them: a
    term→value→source_ref digest (each row's real source_ref, for the LLM to copy) and a MECHANISM
    system rule telling it to cite the specific driver. Deterministic — the DIGEST + prompt, not an
    LLM-composed output string."""
    rows = [
        _drv("attribution", metric="revenue", value="$55.9M, or 48.0%", value_num=-48.0, unit="%",
             verbatim="Revenue decreased.", source_ref="10-Q Z"),
        _drv("leading_indicator", metric="sales volume", value="approximately 274 MWh",
             source_ref="CIQ transcript: MVST Q1 2026 Call"),
    ]
    od = ds.OperatingDriversExtract(rows=rows, qa_flags=[])
    digest = syn._operating_drivers_digest(od)
    assert "OPERATING DRIVERS" in digest
    # each row surfaced with its REAL source_ref (the thing the LLM copies to cite)
    assert "[attribution] revenue: $55.9M, or 48.0% → 10-Q Z" in digest
    assert "→ CIQ transcript: MVST Q1 2026 Call" in digest
    # the system rule instructs grounding operating points in a driver + its source_ref
    assert "MECHANISM" in syn._SYSTEM and "source_ref" in syn._SYSTEM
    assert "load-bearing driver" in syn._SYSTEM


def test_twin_cases_are_never_numeric() -> None:
    """Analogues inform reasoning; they never carry a recovery rate / base rate / probability."""
    for fname, field in ds.TwinCase.model_fields.items():
        assert field.annotation is str, f"TwinCase.{fname} must be a string, not a number"


def test_dossier_package_imports_no_ledger_or_scoring() -> None:
    """The assembler must not be able to write a verdict: it imports no ledger/scoring module."""
    pkg = Path(__file__).resolve().parents[1] / "vinci" / "dossier"
    forbidden = {"vinci.ledger", "vinci.scoring"}
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
            cross_sectional=_u(), pe=_u(), pe_percentile_5y=_u(), ev_ebitda=_u(),
            ev_ebitda_percentile_5y=_u(), ev_ebitda_adjusted_fwd=_u(), adjusted_eps=_u(),
            range_position=_u(),
        ),
        quality=ds.Quality(
            fcf_sign=_u(), free_cash_flow=_u(), margin_trend=_u(), net_debt_to_ebitda=_u(),
            net_debt_to_ocf=_u(), net_debt_to_ebitda_adjusted=_u(), survival_capacity=_u(),
            interest_coverage=_u(), share_count_trend=_u(), liquidity_covenant_flags=_u(),
            multi_year_trajectory=_u(),
        ),
        concentration=ds.Concentration(
            segments=_u(), segment_ebitda=_u(), customers=_u(), geographic=_u()
        ),
        peer_comps=ds.PeerComps(
            peer_set=_u(), comparability=_u(), trading_multiples=_u(), fundamental_deltas=_u()
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


def test_transcript_figure_soft_flagged_structured_misbinding_hard_flagged() -> None:
    """Source-aware figure trace. A number cited to the earnings-call TRANSCRIPT (prose, not in the
    structured layer) earns a soft TRANSCRIPT-FIGURE 'verify against the call' note, NOT a hard
    UNTRACEABLE — so a high-value transcript-only point survives. A number cited to a STRUCTURED
    source the facts don't contain still hard-flags UNTRACEABLE (a real source-misbinding)."""
    tref = "CIQ transcript(s): Acme, Inc., Q1 2026 Earnings Call.rtf"
    # management_commentary PRESENT so the transcript citation traces (the point is cited)
    mech = _minimal_mech().model_copy(
        update={"management_commentary": ds.Sourced.present("posture", source_ref=tref)}
    )
    payload = {
        "bull_points": [],
        "bear_points": [
            # 48.2 lives in the call, cited to the transcript -> soft note, point kept
            {"claim": "The GAAP net profit of $48.2M is a non-cash fair-value artifact",
             "source_ref": tref},
            # 47.3 cited to a STRUCTURED EOD ref that doesn't contain it -> hard UNTRACEABLE
            {"claim": "Reported volume of 47.3 thousand units", "source_ref": "EOD name-IWM 180d"},
        ],
        "decisive_question": {"question": "does it reverse?", "evidence_for": [],
                              "evidence_against": []},
        "twin_reference_cases": [], "key_unknowns": [],
    }
    _, flags, _ = syn.synthesize(mech, llm=_FakeLlm(payload), ticker="ACME", name="Acme")
    # transcript-cited 48.2 -> soft 'verify' note, NOT untraceable (the point is preserved)
    assert any("TRANSCRIPT-FIGURE '48.2'" in f and "verify against the call" in f for f in flags)
    assert not any("UNTRACEABLE figure '48.2'" in f for f in flags)
    # structured-cited 47.3 -> hard untraceable, NOT softened to a transcript note
    assert any("UNTRACEABLE figure '47.3'" in f for f in flags)
    assert not any("TRANSCRIPT-FIGURE '47.3'" in f for f in flags)


def test_directional_lint_exempts_analyst_rating_context() -> None:
    """#1: 'buy'/'sell' that merely report the analyst rating (a Buy (1.00) recommendation, a
    1=buy…5=sell scale, the sell-side, and — Fix 6 — the consensus_stats 'Ratings: Buy N' count
    distribution) are NOT directional-flagged; a real conclusion still is. #2: a long claim is
    quoted to a word boundary + '…', never mid-word."""
    base = {
        "twin_reference_cases": [], "key_unknowns": [],
        "decisive_question": {
            "question": "does it reverse?", "evidence_for": [], "evidence_against": []
        },
    }
    rating = {
        **base,
        "bull_points": [{"claim": "Sell-side still carries a Buy (1.00) recommendation "
                         "versus the current price", "source_ref": "x"},
                        {"claim": "Consensus stats show Ratings: Buy 2, Outperform 0, Hold 0, "
                         "Sell 0", "source_ref": "x"}],  # Fix 6 — rating-count distribution
        "bear_points": [{"claim": "The analyst recommendation is only Hold (3.00 on a "
                         "1=buy…5=sell scale), not an endorsement", "source_ref": "x"}],
    }
    _, flags, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(rating), ticker="X", name="X")
    hits = {f.split("'")[1] for f in flags if "DIRECTIONAL language" in f}
    assert "buy" not in hits and "sell" not in hits  # rating context, not a conclusion

    concl = {**base, "bear_points": [],
             "bull_points": [{"claim": "BUY now, undervalued", "source_ref": "x"}]}
    _, flags2, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(concl), ticker="X", name="X")
    assert any("DIRECTIONAL language 'buy'" in f for f in flags2)  # a real conclusion still flags

    assert syn._snip("alpha beta gamma delta", 12) == "alpha beta…"  # cuts at a word boundary + …
    assert syn._snip("short", 70) == "short"  # short claim unchanged


def test_directional_lint_exempts_reported_posture_not_verdicts() -> None:
    """Flag-noise reduction (validated across 10 dossiers). A directional token that REPORTS
    consensus/analyst posture or names the CPG 'buy-rate' metric is redacted; a real verdict — incl.
    'high/low-conviction <call>' — still flags. This is the adversarial probe battery, frozen."""
    def fires(s: str) -> bool:
        return bool(syn._DIRECTIONAL.search(syn._RATING_CTX.sub(" ", s)))
    for reported in [  # reported external posture / domain/market term -> NOT a conclusion
        "existing households' buy-rate fell 2%",
        "the drawdown is idiosyncratic, not a shared sell-off",  # market term
        "a brand that absorbed a sharp sell-in scare and re-rated",  # CPG channel term
        "Consensus carries a Buy recommendation (CIQ 2.1)",
        "Sell-side consensus carries a Buy (1.00) recommendation and a $17.00 target",
        "recommendation sits at Outperform (2.00) with mean target $11.67",  # reversed-order rec
        "the consensus recommendation is unchanged",
        "the Outperform rating may be stale",
        "a low-conviction external target of $11",
        "the $5.50 target carries unknown conviction",
        "analysts hold an Underweight rating",
    ]:
        assert not fires(reported), f"false-positive on reported posture: {reported!r}"
    for verdict in [  # the dossier concluding -> MUST still flag (the core guardrail)
        "BUY now, clearly undervalued",
        "we expect the stock to outperform peers",
        "this is a high-conviction long",
        "this is a low-conviction long",
        "we recommend buying the stock",
        "our recommendation is to sell",  # narrow rec-arm must NOT swallow a genuine verdict
        # the #45-audit CRITICAL holes: a verdict near analyst/consensus + "recommendation" wording
        "Consensus aside, we buy now before any recommendation lands",  # was swallowed by broad arm
        "Our recommendation is a buy (initiate now)",  # was swallowed by reversed arm
        "Final recommendation: hold (await catalyst)",
        "our highest-conviction idea this year",
        "we rate it Outperform on the fundamentals",
    ]:
        assert fires(verdict), f"MISSED a real verdict: {verdict!r}"


def test_leverage_basis_flag_gated_on_magnitude() -> None:
    """Flag-noise reduction: the reported-vs-covenant leverage caveat is immaterial below ~1x (incl.
    net cash, a negative ratio) — suppressed there, kept for materially-levered names."""
    mk = ds.Sourced.present
    assert dm._leverage_basis_flag(mk(3.9, source_ref="x")) is not None  # levered -> flag
    assert dm._leverage_basis_flag(mk(1.5, source_ref="x")) is not None  # boundary kept
    assert dm._leverage_basis_flag(mk(1.3, source_ref="x")) is None      # modest -> silent (IT FP)
    assert dm._leverage_basis_flag(mk(0.0, source_ref="x")) is None      # unlevered -> silent
    assert dm._leverage_basis_flag(mk(-1.0, source_ref="x")) is None     # net cash -> silent
    assert dm._leverage_basis_flag(ds.Sourced.unknown(note="x")) is None


def test_unreconciled_accepts_falling_absolute_ebitda() -> None:
    """Flag-noise reduction: a bear point that reconciles margin compression against absolute EBITDA
    in DOLLARS — even when absolute EBITDA FELL — is NOT flagged UNRECONCILED; a margin-compression
    claim with no absolute-EBITDA check still is."""
    reconciled = ("LTM EBITDA margin fell to 10% but absolute EBITDA has fallen from $103M to $79M "
                  "— a real drop, not an optical effect")
    bare = "LTM EBITDA margin fell to 10% on price competition, a clear deterioration"
    def pay(claim: str) -> dict[str, typing.Any]:
        return {
            "bull_points": [],
            "bear_points": [{"claim": claim, "source_ref": "EOD name-IWM 180d"}],
            "decisive_question": {"question": "?", "evidence_for": [], "evidence_against": []},
            "twin_reference_cases": [], "key_unknowns": [],
        }
    _, ok, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(pay(reconciled)), ticker="X", name="X")
    _, bad, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(pay(bare)), ticker="X", name="X")
    assert not any("UNRECONCILED" in f for f in ok)  # reconciled via $abs (falling) -> silent
    assert any("UNRECONCILED" in f for f in bad)     # no absolute-EBITDA check -> flagged
    # the MVST form #42 missed: "slipped from 74 to 52" (no $, no arrow) — broadened _ABS_RECON
    slipped = ("LTM EBITDA margin fell to 10%, but absolute EBITDA also slipped from 74 to 52 — a "
               "real deterioration")
    _, ok2, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(pay(slipped)), ticker="X", name="X")
    assert not any("UNRECONCILED" in f for f in ok2)
    # the negation guard: a "not just a falling margin %" disclaimer is asserting deterioration, not
    # citing bare margin compression — even with no absolute-EBITDA figure present
    negation = "EBITDA margin fell to 10%, a real deterioration, not just a falling margin"
    _, ok3, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(pay(negation)), ticker="X", name="X")
    assert not any("UNRECONCILED" in f for f in ok3)
    # #45-audit HIGH fix: weak tokens must NOT over-suppress (easily / to-2024 aren't reconciles)
    weak = "EBITDA margin fell to 10%; absolute EBITDA gains are easily reversed next year"
    _, bad2, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(pay(weak)), ticker="X", name="X")
    assert any("UNRECONCILED" in f for f in bad2)  # 'easily' is not a movement-verb reconciliation


def test_claim_figures_skips_calendar_labels() -> None:
    """Flag-noise reduction: the figure-trace skips calendar/period labels _NUM would otherwise
    extract (FY21->21, 90 days ago->90) and would wrongly flag; real figures pass through."""
    figs = syn._claim_figures("Absolute revenue rose from 5,587 (FY21) to 9,954 LTM (FY25)")
    assert 5587.0 in figs and 9954.0 in figs  # real figures kept
    assert 21.0 not in figs and 25.0 not in figs  # FY21 / FY25 year labels dropped
    assert syn._claim_figures("more macro uncertainty than 90 days ago") == []  # '90 days' dropped
    assert 48.2 in syn._claim_figures("GAAP net profit of $48.2M was a non-cash artifact")  # kept


def test_twin_numbers_skips_proper_noun_digits() -> None:
    """Flag-noise reduction: a twin's numeric check ignores digits bound to letters in an identifier
    (GLP-1), but still catches a free-standing figure (a stray multiple/rate)."""
    assert syn._twin_numbers("a GLP-1 weight-loss demand shock") == set()  # proper-noun digit
    assert syn._twin_numbers("COVID-19 reopening analogue") == set()
    assert syn._twin_numbers("recovered 50% on the rebound") == {"50"}  # free-standing figure
    assert "3.2" in syn._twin_numbers("framed as a Phase 3.2 timing gap")  # free-standing decimal
    # #45-audit fix: a UNIT-SUFFIXED figure must still be caught (old after.isalpha() dropped it)
    assert syn._twin_numbers("traded at a 1.5x multiple") == {"1.5"}
    assert syn._twin_numbers("a 200M run-rate and 50bps of margin") == {"200", "50"}


def test_anchors_suppressed_when_claim_acknowledges_distortion() -> None:
    """Flag-noise reduction: ANCHORS-ON-DISTORTED-P/E suppresses a bull claim that itself NAMES the
    distortion and pivots off it (the VRRM FP), but still fires on a trough-anchor that reads the
    distorted multiple AS cheap (the CNXC catch)."""
    val = _minimal_mech().valuation.model_copy(
        update={"pe": ds.Sourced.present(112.0, source_ref="x", note="distorted")}
    )
    mech = _minimal_mech().model_copy(update={"valuation": val})
    acks = ("the GAAP basis that distorts the headline P/E understates earnings; the forward adj "
            "basis is far cheaper at the 0th percentile")
    anchors = "the P/E sits at the 0th percentile, near its multi-year floor — a cheap entry"
    def pay(claim: str) -> dict[str, typing.Any]:
        return {
            "bull_points": [{"claim": claim, "source_ref": "EOD name-IWM 180d"}], "bear_points": [],
            "decisive_question": {"question": "?", "evidence_for": [], "evidence_against": []},
            "twin_reference_cases": [], "key_unknowns": [],
        }
    # #45-audit: ack-guard is negation-aware — 'NOT one-time' while anchoring on cheap P/E is the
    # trap, so it MUST still flag
    denied = "the P/E looks cheap here, and importantly this charge is not one-time"
    _, ack_flags, _ = syn.synthesize(mech, llm=_FakeLlm(pay(acks)), ticker="X", name="X")
    _, anc_flags, _ = syn.synthesize(mech, llm=_FakeLlm(pay(anchors)), ticker="X", name="X")
    _, den_flags, _ = syn.synthesize(mech, llm=_FakeLlm(pay(denied)), ticker="X", name="X")
    assert not any("ANCHORS-ON-DISTORTED" in f for f in ack_flags)  # warns of distortion -> off
    assert any("ANCHORS-ON-DISTORTED" in f for f in anc_flags)      # trough-anchor -> still fires
    assert any("ANCHORS-ON-DISTORTED" in f for f in den_flags)      # "not one-time" -> still fires


def test_hetero_suppressed_when_gap_resolved_to_earned() -> None:
    """Flag-noise reduction: HETEROGENEOUS-BENCHMARK suppresses a bear claim that RESOLVES the peer
    gap to EARNED/value-trap (the CNXC FP), but still fires on a directional 'NOT cheap / premium vs
    peers' read (the FUBO catch)."""
    pc = _minimal_mech().peer_comps.model_copy(
        update={"comparability": ds.Sourced.present("HETEROGENEOUS peer set", source_ref="x")}
    )
    mech = _minimal_mech().model_copy(update={"peer_comps": pc})
    earned = "the discount to peers is earned — a value trap, EBITDA margin below the peer median"
    premium = "on the forward multiple it is NOT cheap, trading at a premium to the peer median"
    def pay(claim: str) -> dict[str, typing.Any]:
        return {
            "bull_points": [], "bear_points": [{"claim": claim, "source_ref": "EOD name-IWM 180d"}],
            "decisive_question": {"question": "?", "evidence_for": [], "evidence_against": []},
            "twin_reference_cases": [], "key_unknowns": [],
        }
    # #45-audit: negation-aware — 'NOT earned … cheap vs peers' IS the clean-benchmark misread the
    # gate must catch, so it MUST still fire
    denied = "the discount is not earned; it screens cheap vs the peer median"
    _, earned_flags, _ = syn.synthesize(mech, llm=_FakeLlm(pay(earned)), ticker="X", name="X")
    _, prem_flags, _ = syn.synthesize(mech, llm=_FakeLlm(pay(premium)), ticker="X", name="X")
    _, den_flags, _ = syn.synthesize(mech, llm=_FakeLlm(pay(denied)), ticker="X", name="X")
    assert not any("HETEROGENEOUS-BENCHMARK" in f for f in earned_flags)  # earned/value-trap -> off
    assert any("HETEROGENEOUS-BENCHMARK" in f for f in prem_flags)        # directional -> fires
    assert any("HETEROGENEOUS-BENCHMARK" in f for f in den_flags)         # 'not earned' -> fires


def test_figure_trace_dedups_decisive_mirror() -> None:
    """Flag-noise reduction: the decisive question restates the bull/bear crux, so the SAME figure
    would fire a second figure-trace flag — deduped to one."""
    payload = {
        "bull_points": [],
        "bear_points": [{"claim": "cash fell to 999", "source_ref": "EOD name-IWM 180d"}],
        "decisive_question": {
            "question": "?", "evidence_for": [],
            "evidence_against": [
                {"claim": "cash dropped to 999 against the wall", "source_ref": "EOD name-IWM 180d"}
            ],
        },
        "twin_reference_cases": [], "key_unknowns": [],
    }
    _, flags, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(payload), ticker="X", name="X")
    assert len([f for f in flags if "999" in f]) == 1  # decisive mirror deduped, not double-flagged


def test_figure_trace_dedup_keys_on_signed_value_and_type() -> None:
    """#45-audit HIGH fix: the dedup must NOT collapse +N/-N (distinct facts) or let a soft
    TRANSCRIPT-FIGURE on one point swallow a hard UNTRACEABLE on another of the same magnitude."""
    eod = "EOD name-IWM 180d"
    tref = "CIQ transcript(s): Acme Q1 2026 Earnings Call.rtf"
    mech = _minimal_mech().model_copy(
        update={"management_commentary": ds.Sourced.present("posture", source_ref=tref)}
    )
    # +777 (bull) and -777 (decisive.against) are DIFFERENT facts — both must flag (no abs collapse)
    sign = {
        "bull_points": [{"claim": "headcount grew to 777 people", "source_ref": eod}],
        "bear_points": [],
        "decisive_question": {
            "question": "?", "evidence_for": [],
            "evidence_against": [{"claim": "margin fell 777 bps", "source_ref": eod}],
        },
        "twin_reference_cases": [], "key_unknowns": [],
    }
    _, f_sign, _ = syn.synthesize(mech, llm=_FakeLlm(sign), ticker="X", name="X")
    assert len([f for f in f_sign if "777" in f]) == 2  # +777 and 777bps both flag
    # a soft TRANSCRIPT-FIGURE (bull, transcript ref) must NOT suppress a hard UNTRACEABLE on a
    # decisive structured-cited figure of the same value
    xtype = {
        "bull_points": [{"claim": "the call cited 678 in savings", "source_ref": tref}],
        "bear_points": [],
        "decisive_question": {
            "question": "?", "evidence_for": [],
            "evidence_against": [{"claim": "a 678 unit shortfall", "source_ref": eod}],
        },
        "twin_reference_cases": [], "key_unknowns": [],
    }
    _, f_xt, _ = syn.synthesize(mech, llm=_FakeLlm(xtype), ticker="X", name="X")
    assert any("TRANSCRIPT-FIGURE '678'" in f for f in f_xt)  # soft note on the bull (transcript)
    assert any("UNTRACEABLE figure '678'" in f for f in f_xt)  # hard flag on decisive — kept


def test_anchors_on_distorted_pe_flags_bull_case_leaning_on_the_multiple() -> None:
    """When the mechanical P/E is marked distorted, a BULLISH claim that leans on that multiple/
    percentile as cheap/mean-reverting is flagged (the FUBO trap) — but NOT when the P/E is clean,
    and not a bull claim that doesn't touch the P/E."""
    mech = _minimal_mech()
    distorted = ds.Sourced.present(
        12.1, source_ref="EDGAR XBRL", note="distorted — rests on a non-current positive EPS"
    )
    mech_d = mech.model_copy(
        update={"valuation": mech.valuation.model_copy(update={"pe": distorted})}
    )
    payload = {
        "bull_points": [
            {"claim": "The P/E sits at the 0.2nd percentile, a depressed valuation that "
                      "could revert", "source_ref": "EDGAR/EOD P/E pctile"},
            {"claim": "Gross margin expanded 300bps as the mix shifted to subscription",
             "source_ref": "x"},
        ],
        "bear_points": [], "twin_reference_cases": [], "key_unknowns": [],
        "decisive_question": {
            "question": "does it reverse?", "evidence_for": [], "evidence_against": []
        },
    }
    _, flags, _ = syn.synthesize(mech_d, llm=_FakeLlm(payload), ticker="FUBO", name="FuboTV")
    anchors = [f for f in flags if "ANCHORS-ON-DISTORTED-P/E" in f]
    assert len(anchors) == 1 and "depressed valuation" in anchors[0]  # only the P/E-leaning point

    # clean P/E (no distortion note) → the SAME claim does NOT fire the anchor flag
    _, clean, _ = syn.synthesize(mech, llm=_FakeLlm(payload), ticker="FUBO", name="FuboTV")
    assert not any("ANCHORS-ON-DISTORTED-P/E" in f for f in clean)


def test_verification_assertion_tripwire_flags_machine_claiming_it_verified() -> None:
    """The dossier cites, it never verifies. A claim asserting the machine verified/proved something
    is flagged; honest negations ('cannot be verified') and benign domain terms ('proven track
    record') are not — fires only on real over-assertion (today it fires nothing live)."""
    payload = {
        "bull_points": [
            {"claim": "We verified the revenue and it proves that the thesis holds",
             "source_ref": "x"},
            {"claim": "The company has a proven track record and an established brand",
             "source_ref": "x"},
            {"claim": "The mean-reversion is demonstrably underway", "source_ref": "x"},  # genuine
        ],
        "bear_points": [
            {"claim": "Adjusted leverage cannot be verified from the parsed facts",
             "source_ref": "x"},
            # FIX 2: a NEGATED over-assertion adverb is a hedge/derivation, not an over-claim —
            # incl. contractions (the \B + mandatory-apostrophe arm: "doesn't conclusively")
            {"claim": "the equity is not demonstrably earning on a GAAP basis", "source_ref": "x"},
            {"claim": "the thesis doesn't conclusively hold yet", "source_ref": "x"},
        ],
        "twin_reference_cases": [], "key_unknowns": [],
        "decisive_question": {
            "question": "does it reverse?", "evidence_for": [], "evidence_against": []
        },
    }
    _, flags, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(payload), ticker="X", name="X")
    vc = [f for f in flags if "VERIFICATION-CLAIM" in f]
    assert any("We verified" in f for f in vc)            # the over-assertion fires
    assert any("demonstrably underway" in f for f in vc)  # a POSITIVE 'demonstrably' still fires
    assert not any("not demonstrably" in f for f in vc)   # FIX 2: the negated hedge does NOT fire
    assert not any("doesn't conclusively" in f for f in vc)  # contraction hedge does NOT fire
    assert not any("proven track record" in f for f in vc)  # benign domain term, not flagged
    assert not any("cannot be verified" in f for f in vc)   # honest negation, not flagged


def test_twin_contract_keeps_analogues_qualitative() -> None:
    """FIX 1: the contract keeps twins QUALITATIVE — figures (caps/multiples/ratios) live
    source-bound in peer_set / fundamental_deltas, not restated in twin prose — so the (unchanged,
    still-sharp) TWIN-non-numeric guard isn't fed verifiable roster numbers it then over-flags."""
    assert "QUALITATIVE" in syn._SYSTEM and "fundamental_deltas" in syn._SYSTEM
    twin = syn.SYNTHESIS_TOOL["input_schema"]["properties"]["twin_reference_cases"]
    assert "QUALITATIVE" in twin["items"]["properties"]["distinguishing_fact"]["description"]
    assert "fundamental_deltas" in twin["description"] or "peer_set" in twin["description"]


def test_consensus_reproduction_guardrails_unreconciled_and_false_balance() -> None:
    """Mechanism B guardrails: (G.1) a bear point citing margin COMPRESSION without the
    absolute-EBITDA reconciliation flags UNRECONCILED, but a reconciled one does not; (G.2) a
    missing evidence_balance flags (required of the LLM, flagged not blocked), and 'mixed' over a
    split flags FALSE-BALANCE."""
    base = {"twin_reference_cases": [], "key_unknowns": [], "bull_points": [],
            "decisive_question": {"question": "q?", "evidence_for": [], "evidence_against": []}}
    # G.1: margin compression cited WITHOUT the absolute EBITDA → UNRECONCILED
    unrec = {**base, "evidence_balance": "strongly-bearish — margins",
             "bear_points": [{"claim": "EBITDA margin compressed from 42% to 37%, deteriorating",
                              "source_ref": "x"}]}
    _, f1, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(unrec), ticker="X", name="X")
    assert any("UNRECONCILED bear_point" in f for f in f1)
    # reconciled (cites the absolute EBITDA RISING) → NOT flagged
    rec = {**base, "evidence_balance": "mixed — see notes",
           "bear_points": [{"claim": "EBITDA margin fell 42%→37% WHILE absolute EBITDA rose "
                            "229→362", "source_ref": "x"}]}
    _, f2, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(rec), ticker="X", name="X")
    assert not any("UNRECONCILED" in f for f in f2)
    # a bare 'absolute' intensifier ("absolute disaster") must NOT count as reconciliation → flagged
    byp = {**base, "evidence_balance": "strongly-bearish",
           "bear_points": [{"claim": "EBITDA margin compressed to 37%, an absolute disaster",
                            "source_ref": "x"}]}
    _, fb, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(byp), ticker="X", name="X")
    assert any("UNRECONCILED" in f for f in fb)
    # G.2: missing evidence_balance is flagged
    noeb = {**base, "bear_points": [{"claim": "revenue fell", "source_ref": "x"}]}
    _, f3, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(noeb), ticker="X", name="X")
    assert any("evidence_balance MISSING" in f for f in f3)
    # G.2: 'mixed' label over a 0-bull / 3-bear split → FALSE-BALANCE
    lop = {**base, "evidence_balance": "mixed",
           "bear_points": [{"claim": "a", "source_ref": "x"}, {"claim": "b", "source_ref": "x"},
                           {"claim": "c", "source_ref": "x"}]}
    _, f4, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(lop), ticker="X", name="X")
    assert any("FALSE-BALANCE" in f for f in f4)
    # (regression) 'mixed' in the dash-REASON, not the LABEL — a bearish read '… eroding, mixed cash
    # generation' over a lopsided bear split must NOT trip FALSE-BALANCE (the check reads the label;
    # this is the MVST re-assembly false positive that fired on a mid-sentence 'mixed').
    reason_mixed = {
        **base,
        "evidence_balance": "strongly-bearish — a wall against eroding, mixed cash generation",
        "bull_points": [{"claim": "a", "source_ref": "x"}, {"claim": "b", "source_ref": "x"}],
        "bear_points": [{"claim": f"bear {i}", "source_ref": "x"} for i in range(7)],
    }
    _, f5, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(reason_mixed), ticker="X", name="X")
    assert not any("FALSE-BALANCE" in f for f in f5)


def test_false_balance_flags_strong_lean_with_symmetric_body_both_directions() -> None:
    """G.2 (DIRECTION-AGNOSTIC, the MVST defect): a COMMITTED strong lean over a near-symmetric body
    whose MINORITY side isn't qualified-as-outweighed launders a one-sided case — flagged the same
    whether the lean is bearish (bull minority padded) or bullish (bear minority padded). A
    qualified minority, or a genuinely lopsided body, does NOT fire — proving the fix SIZES rather
    than counts, and never demands deleting a genuine counter-point."""
    base = {"twin_reference_cases": [], "key_unknowns": [],
            "decisive_question": {"question": "q?", "evidence_for": [], "evidence_against": []}}

    def pt(c: str) -> dict[str, str]:
        return {"claim": c, "source_ref": "x"}

    # (A) strongly-BEARISH but 3-bull / 4-bear with an UNqualified bull minority → FALSE-BALANCE
    bearish = {**base, "evidence_balance": "strongly-bearish — a major customer terminated",
               "bull_points": [pt("FCF is positive"), pt("the buyback shrinks the share count"),
                               pt("guidance holds the top line")],
               "bear_points": [pt("a major customer terminated"), pt("estimates are being cut"),
                               pt("an interim CEO was named"), pt("the decline is idiosyncratic")]}
    _, fa, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(bearish), ticker="X", name="X")
    assert any("FALSE-BALANCE" in f and "near-symmetric" in f and "bull_points" in f for f in fa)

    # (B) SYMMETRIC, not bull-biased: strongly-BULLISH with an UNqualified bear minority fires too
    bullish = {**base, "evidence_balance": "strongly-bullish — durable compounding",
               "bear_points": [pt("leverage is elevated"), pt("customer concentration exists"),
                               pt("a soft recent quarter")],
               "bull_points": [pt("revenue is compounding"), pt("FCF is inflecting"),
                               pt("it is gaining share"), pt("the balance sheet is net cash")]}
    _, fb, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(bullish), ticker="X", name="X")
    assert any("FALSE-BALANCE" in f and "near-symmetric" in f and "bear_points" in f for f in fb)

    # (C) a QUALIFIED minority (sized-as-outweighed) does NOT fire — the genuine point survives
    qualified = {**base, "evidence_balance": "strongly-bearish — a major customer terminated",
                 "bull_points": [
                     pt("FCF-positive is a genuine counter-point, OUTWEIGHED by the customer loss"),
                     pt("the buyback continues but does not offset the lost revenue"),
                     pt("guidance holds — what would have to be true is the loss is one-off")],
                 "bear_points": [pt("a major customer terminated"), pt("estimates are being cut"),
                                 pt("an interim CEO was named"),
                                 pt("the decline is idiosyncratic")]}
    _, fc, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(qualified), ticker="X", name="X")
    assert not any("near-symmetric" in f for f in fc)

    # (D) a genuinely LOPSIDED body (1 bull / 4 bear) does NOT fire even with the bull unqualified
    lopsided = {**base, "evidence_balance": "strongly-bearish — terminal",
                "bull_points": [pt("FCF is positive")],
                "bear_points": [pt("a major customer terminated"), pt("estimates are being cut"),
                                pt("an interim CEO was named"), pt("the decline is idiosyncratic")]}
    _, fd, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(lopsided), ticker="X", name="X")
    assert not any("near-symmetric" in f for f in fd)


def test_synthesis_contract_requires_balance_and_treats_opacity_as_risk() -> None:
    """Mechanism B lives in the synthesis CONTRACT (prompt + tool schema): evidence_balance is a
    required tool field; opacity is a bearish risk; anti-balance + contrarian-reconciliation are
    instructed. evidence_balance carries no conclusion token (the no-verdict line still holds)."""
    assert "evidence_balance" in syn.SYNTHESIS_TOOL["input_schema"]["required"]
    sys = syn._SYSTEM
    assert "OPACITY-AS-SIGNAL" in sys and "BEARISH risk" in sys
    assert "ANTI-BALANCE" in sys and "CONTRARIAN-RECONCILIATION" in sys
    assert not any(tok in "evidence_balance" for tok in _FORBIDDEN)  # not a verdict-shaped field


def test_survival_capacity_blocks_leverage_with_runway() -> None:
    """Mechanism A.3: leverage is promoted to a SURVIVAL block — net-debt/EBITDA + self-funding in
    one field; a missing leg fails loud as a risk. (H3) The coarse 'nearest maturity wall' line
    is retired — the month-precision E2 wall supersedes it in the survival super-section."""
    present, unknown = ds.Sourced.present, ds.Sourced.unknown
    sc = dm._survival_capacity(
        present(2.9, source_ref="EDGAR"), present("~2.6x fwd-adj", source_ref="99.1"),
        present(1.0, source_ref="EDGAR"),  # FCF sign +1 → self-funding
    )
    v = sc.value or ""
    assert "net-debt/EBITDA 2.9x" in v and "self-funding" in v
    assert "nearest maturity wall" not in v  # (H3) retired
    # a missing leg fails loud as a risk, never silently dropped
    risky = dm._survival_capacity(
        unknown(note="no debt/cash"), unknown(note="no guide"), unknown(note="no FCF"))
    rv = risky.value or ""
    assert "UNKNOWN" in rv and "risk" in rv


def test_net_debt_to_ebitda_prefers_ciq(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deterministic source hierarchy: CIQ Net Debt ÷ CIQ LTM EBITDA wins outright over the EDGAR
    XBRL screen figure (which under-captures scattered debt). The MVST shape: 200 / 52 = 3.9x,
    never the EDGAR false net-cash; no judge, no manual reconciliation."""
    monkeypatch.setattr(
        cs, "net_debt",
        lambda _b: ds.Sourced.present(199.9, source_ref="CIQ ... 'Net Debt' [Q1 Mar-31-2026]"),
    )
    monkeypatch.setattr(
        cs, "ltm_ebitda",
        lambda _b: ds.Sourced.present(51.9, source_ref="IS [LTM 12 months Mar-31-2026]"),
    )
    edgar = ds.Sourced.present(-1.5, source_ref="EDGAR XBRL (screen)")  # the false net-cash
    ratio, ciq_nd = dm._net_debt_to_ebitda(None, edgar)  # type: ignore[arg-type]
    assert ratio.status is ds.SourceStatus.PRESENT and ratio.value == pytest.approx(3.9, abs=0.05)
    src = ratio.source_ref or ""
    assert "CIQ Net Debt" in src and "EDGAR" not in src
    assert "[Q1 Mar-31-2026]" in src and "[LTM 12 months Mar-31-2026]" in src  # both periods bound
    assert "LTM EBITDA" not in src  # no hardcoded 'LTM' label; the period bracket tells the truth
    assert ciq_nd.value == pytest.approx(199.9)  # fed to the survival readout


def test_net_debt_to_ebitda_edgar_fallback_then_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """CIQ absent → the EDGAR XBRL figure as a LABELLED breadth fallback (the caveat rides in the
    SOURCE_REF, which renders on a PRESENT fact, not only the note); both absent → fail loud."""
    monkeypatch.setattr(cs, "net_debt", lambda _b: ds.Sourced.unknown(note="no CIQ"))
    monkeypatch.setattr(cs, "ltm_ebitda", lambda _b: ds.Sourced.unknown(note="no CIQ"))
    edgar = ds.Sourced.present(2.5, source_ref="EDGAR XBRL (screen)")
    fallback, _ = dm._net_debt_to_ebitda(None, edgar)  # type: ignore[arg-type]
    assert fallback.value == pytest.approx(2.5)
    assert "pull CIQ" in (fallback.source_ref or "")  # caveat rendered via source_ref, not lost
    no_edgar = ds.Sourced.unknown(note="no EBITDA in XBRL")
    unk, _ = dm._net_debt_to_ebitda(None, no_edgar)  # type: ignore[arg-type]
    assert unk.status is ds.SourceStatus.UNKNOWN and "pull CIQ" in (unk.note or "")


def test_survival_capacity_ciq_basis_and_net_cash_readout() -> None:
    """The CIQ-sourced ratio is labelled '(CIQ)'; and when the ratio can't form but the CIQ net-debt
    position IS known, the block shows it instead of a bare 'solvency risk' — a known balance sheet
    is not a blind risk."""
    present, unknown = ds.Sourced.present, ds.Sourced.unknown
    sc = dm._survival_capacity(
        present(3.9, source_ref="CIQ Net Debt $200M ÷ CIQ LTM EBITDA $52M"),
        unknown(note="no guide"), present(1.0, source_ref="EDGAR"),
    )
    assert "net-debt/EBITDA 3.9x (CIQ)" in (sc.value or "")
    sc2 = dm._survival_capacity(
        unknown(note="no EBITDA in XBRL"), unknown(note="no guide"),
        present(1.0, source_ref="EDGAR"), net_debt=present(200.0, source_ref="CIQ BS"),
    )
    v2 = sc2.value or ""
    assert "net debt $200M (CIQ)" in v2 and "N/A" in v2 and "solvency risk" not in v2


def test_net_debt_to_ocf_prefers_ciq() -> None:
    """net-debt/OCF uses the SAME CIQ net-debt as net-debt/EBITDA (CIQ Net Debt ÷ CIQ OCF), so the
    two leverage rows can't disagree on whether net debt exists. MVST: 200 / 46 ~ 4.4x."""
    nd = ds.Sourced.present(199.9, source_ref="CIQ ... 'Net Debt' [Q1 Mar-31-2026]")
    ocf = ds.Sourced.present(45.9, source_ref="CIQ ... 'Cash from Ops.' [LTM Mar-31-2026]")
    r = dm._net_debt_to_ocf(nd, ocf, ds.Sourced.present(-1.5, source_ref="EDGAR (false net-cash)"))
    assert r.status is ds.SourceStatus.PRESENT and r.value == pytest.approx(4.4, abs=0.1)
    src = r.source_ref or ""
    assert "CIQ Net Debt" in src and "CIQ OCF" in src and "[Q1 Mar-31-2026]" in src


def test_net_debt_to_ocf_edgar_fallback_then_unknown() -> None:
    """CIQ absent → EDGAR figure as a labelled breadth fallback (caveat in the source_ref); both
    absent → fail loud 'pull CIQ'."""
    no = ds.Sourced.unknown(note="no CIQ")
    fb = dm._net_debt_to_ocf(no, no, ds.Sourced.present(2.5, source_ref="EDGAR XBRL (screen)"))
    assert fb.value == pytest.approx(2.5) and "pull CIQ" in (fb.source_ref or "")
    unk = dm._net_debt_to_ocf(no, no, ds.Sourced.unknown(note="no net-debt"))
    assert unk.status is ds.SourceStatus.UNKNOWN and "pull CIQ" in (unk.note or "")


def test_synthesis_decodes_literal_unicode_escapes() -> None:
    """opus occasionally emits a literal '\\u2014' as TEXT in a synthesis string; it must render as
    the character, not the raw escape — while real chars and non-hex backslashes are left alone."""
    assert syn._decode_escapes("mixed \\u2014 a turn") == "mixed — a turn"
    assert syn._decode_escapes({"k": ["x \\u2019 y"]}) == {"k": ["x ’ y"]}  # recurses
    assert syn._decode_escapes("real — dash") == "real — dash"  # real char untouched
    assert syn._decode_escapes("\\underway") == "\\underway"  # non-hex \\u left alone
    # a lone surrogate (would crash model_dump_json) and a C0 control (would corrupt the .json/.md)
    # are LEFT as the literal escape, not decoded:
    assert syn._decode_escapes("x \\ud83d y") == "x \\ud83d y"  # lone surrogate kept literal
    assert syn._decode_escapes("x \\u0000 y") == "x \\u0000 y"  # NUL / C0 control kept literal


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


def test_liquidity_flags_surface_maturity_wall() -> None:
    """'Maturity' is located by HEADER LABEL (not a fixed index) and surfaced as 'Due YYYY'; a
    mis-parsed garbage cell can't fabricate an implausible 'Due 1900' (year window). Serials:
    46170 = 2026-05-28, 46418 = 2027-01-31."""
    # 'Maturity' deliberately at index 6 (not 5) — proves the header-label lookup, not a fixed col.
    rows = [
        ["Description", "Type", "Principal", "Coupon", "Float", "Currency", "Maturity"],
        ["Convertible Loan", "Term Loans", 13.0, "NA", "SOFR+9.75%", "USD", 46170.0],
        ["Convertible Bond", "Bonds and Notes", 42.0, "3.0%", "NA", "CNY", 46418.0],
        ["Garbage serial", "x", 1.0, "NA", "NA", "NA", 5.0],  # serial 5 -> 1900, rejected
    ]
    liq = cs.liquidity_covenant_flags(
        _fin_bundle({"Capital Structure Details": rows}, freq="annual")
    )
    assert "Due 2026" in (liq.value or "") and "Due 2027" in (liq.value or "")
    assert "Due 1900" not in (liq.value or "")  # the year window rejects the garbage serial


def test_liquidity_flags_maturity_date_string() -> None:
    """A Maturity cell rendered as a DATE STRING (not a serial) is still parsed — excel_date handles
    it directly; the old clean_num wrapper would have dropped it to UNKNOWN."""
    rows = [
        ["Description", "Type", "Principal", "Coupon", "Maturity"],
        ["Senior Notes", "Bonds and Notes", 500.0, "5.0%", "Jan-31-2028"],
    ]
    liq = cs.liquidity_covenant_flags(
        _fin_bundle({"Capital Structure Details": rows}, freq="annual")
    )
    assert "Due 2028" in (liq.value or "")


def test_all_workbooks_lists_every_match() -> None:
    """all_workbooks lists EVERY workbook of a kind (both earnings calls) where workbook() returns
    one — so the synthesis can read more than the latest quarter on file."""
    f = ciq.CiqFormat.UNKNOWN
    t1 = ciq.CiqWorkbook(kind="transcript", path=Path("/fake/Q1.rtf"), fmt=f, freq=None)
    t2 = ciq.CiqWorkbook(kind="transcript", path=Path("/fake/Q4.rtf"), fmt=f, freq=None)
    fin = ciq.CiqWorkbook(kind="financials", path=Path("/fake/F.xls"), fmt=f, freq="annual")
    b = ciq.CiqBundle(ticker="X", workbooks=(t1, t2, fin))
    assert len(b.all_workbooks("transcript")) == 2 and b.workbook("transcript") is t1
    assert b.all_workbooks("nope") == ()


# --- PR E: structured capital structure + month-precision maturity wall + covenant pointers ----
# The panel format is real MVST (serials 46170=2026-05-28, 46366=2026-12-10, etc.); the values
# reproduce the verified MVST pins (matured $25.0M / ≤12m $42.9M / 2027 $105.1M / undated $95.6M).

_CS_DETAILS: list[list[typing.Any]] = [
    ["Source", "A 2025 filed Mar-16-2026"],
    # 'Floating\xa0Rate' carries the NON-BREAKING space CIQ emits — the column lookup must normalise
    # it (else the floating-rate column is silently blank), and 'Principal Due (USD)' / 'Repayment
    # Currency' are matched by PREFIX (the header carries a trailing qualifier).
    ["Description", "Type", "Principal Due (USD)", "Coupon/Base Rate", "Floating\xa0Rate",
     "Maturity", "Seniority", "Secured", "Convertible", "Repayment Currency"],
    ["Convertible Loan With Shareholder - Initial Term Loan", "Term Loans", 12.0, "NA",
     "SOFR + 9.750%", 46170.0, "Senior", "Yes", "Convertible", "USD"],
    ["Loan Facilities Agreement With a Group of Lenders", "Term Loans", 42.9, "NA",
     "New Benchmark", 46366.0, "Senior", "Yes", "No", "CNY"],
    ["Notes Payable", "Bonds and Notes", 78.3, "NA", "NA", "-", "Senior", "No", "No", "USD"],
    ["FY 2024", "", "", "", "", "", "", "", "", ""],  # next-panel row TERMINATES the latest panel
]

_CS_SUMMARY: list[list[typing.Any]] = [
    ["Fiscal Period", "FY 2024 (12 months)", "FY 2025 (12 months)"],
    ["Total Term Loans", 131.3, 215.2],
    ["Total Senior Bonds and Notes", 100.0, 78.3],
    ["Total Principal Due", 300.0, 326.0],
    ["Total Debt Outstanding", 300.0, 326.0],
]


def test_capital_structure_ciq_parses_instruments_and_summary() -> None:
    """(E1) The latest per-fiscal-period panel parses by header LABEL: the \\xa0 float header is
    normalised (SOFR shows), serials decode to ISO, '-' is undated (None, never a fabricated date),
    Secured=='Yes'→True and the Convertible column's 'Convertible'/'No' string maps to the bool. The
    Summary aggregates carry the term-loan QoQ movement + the latest-quarter total debt."""
    bundle = _fin_bundle(
        {"Capital Structure Details": _CS_DETAILS, "Capital Structure Summary": _CS_SUMMARY},
        freq="annual")
    insts, summary, asof = cs.capital_structure_ciq(bundle)
    assert asof == "A 2025 filed Mar-16-2026"
    got = insts.value or []
    assert len(got) == 3
    loan, facility, notes = got
    assert loan.description.startswith("Convertible Loan With Shareholder")
    assert loan.type == "Term Loans" and loan.principal_musd == 12.0
    assert loan.floating_rate == "SOFR + 9.750%"  # the \xa0 header normalisation worked
    assert loan.maturity_date == "2026-05-28"  # serial 46170 decoded
    assert loan.secured is True and loan.convertible is True and loan.currency == "USD"
    assert facility.convertible is False and facility.maturity_date == "2026-12-10"
    assert notes.maturity_date is None  # '-' is undated, NOT a fabricated date
    assert notes.secured is False
    s = summary.value or ""
    assert "term loans 215.2" in s and "131.3→215.2 QoQ" in s
    assert "total debt 326.0 (latest quarter)" in s and s.endswith("($M)")


def _inst(
    desc: str, principal: float | None, mat: str | None, **kw: typing.Any
) -> ds.CapitalInstrument:
    return ds.CapitalInstrument(
        description=desc, type=kw.get("type", "Term Loans"), principal_musd=principal,
        coupon=kw.get("coupon", ""), floating_rate=kw.get("floating_rate", ""), maturity_date=mat,
        seniority="Senior", secured=kw.get("secured", True),
        convertible=kw.get("convertible", False), currency=kw.get("currency", "USD"))


def _mvst_capital_structure() -> ds.CapitalStructure:
    """The verified MVST instrument set (synthetic — no licensed-workbook dependency), reproducing
    the maturity-wall pins against a 2026-07-03 reference."""
    insts = [
        _inst("Convertible Loan - Delayed Draw", 13.0, "2026-05-28"),
        _inst("Convertible Loan - Initial", 12.0, "2026-05-28"),
        _inst("Loan Facilities Agreement", 42.9, "2026-12-10"),
        _inst("Convertible Bond - CNY", 41.7, "2027-01-31", currency="CNY", convertible=True),
        _inst("Long-term Loan Agreement", 13.9, "2027-06-19"),
        _inst("Short-term Loan Agreements", 49.5, "2027-03-31"),
        _inst("Notes Payable", 78.3, None, type="Bonds and Notes", secured=False),
        _inst("Operating Lease Liabilities", 17.3, None, type="Capital Lease"),
    ]
    return ds.CapitalStructure(
        instruments=ds.Sourced.present(insts, source_ref="CIQ→Capital Structure Details (A 2025)"),
        summary=ds.Sourced.present("term loans 215.2 ($M)", source_ref="CIQ→Summary"),
        detail_as_of="A 2025 filed Mar-16-2026",
        maturity_filings=ds.Sourced.unknown(note="offline"),
        covenant_pointers=ds.Sourced.unknown(note="offline"),
        covenant_terms=ds.Sourced.unknown(note="offline"))


def test_maturity_wall_groups_by_calendar_year_with_pins() -> None:
    """(E2) Deterministic month-precision wall vs a 2026-07-03 reference: matured-pre-reference
    ($25.0M, verify-the-8-K, NEVER 'repaid'/'defaulted'), due-this-ref-year ≤12m ($42.9M), later
    years grouped ($105.1M in 2027), undated floor ($95.6M), and the itemized reconciliation
    ($268.6M). Calendar-year grouping — a rolling-12m window would wrongly lump 2027-01..06 into
    ≤12m. NO probability / risk / conclusion language."""
    lines = dr._maturity_wall_lines(_mvst_capital_structure(), date(2026, 7, 3))
    text = "\n".join(lines)
    assert "matured (pre-reference): $25.0M" in text
    assert "verify each against its 8-K (NEVER assume repaid or defaulted)" in text
    assert "2026-05-28 (36d before ref): $13.0M" in text
    assert "due ≤12m (through 2026): $42.9M" in text
    assert "due 2027: $105.1M" in text  # 41.7 + 13.9 + 49.5, calendar-grouped
    assert "undated (floor — no panel maturity): $95.6M" in text  # 78.3 + 17.3
    assert "itemized $268.6M" in text
    assert not re.search(r"\b(probabilit|likel|distress|risk of|we expect|default risk)\w*", text,
                         re.IGNORECASE)


def test_capital_structure_render_shows_table_not_flat_string() -> None:
    """(E1 · K1) The MAIN-body instruments render as the shared-idiom table (marked), under the
    curated 'Live instruments — near-dated' label — replacing the old flat liquidity string."""
    out = "\n".join(dr._capital_structure_lines(_mvst_capital_structure(), date(2026, 7, 3)))
    assert dr._TABLE_MARK in out
    assert "Live instruments — near-dated (≤12m + 2027) — panel A 2025 filed Mar-16-2026" in out
    assert "SOFR" not in out or "Convertible Bond - CNY" in out  # the table body renders rows


def _primary_source_fixture(*, doubt: bool) -> ds.PrimarySource:
    """A representative RC-1 primary-source layer for the render pins: doubt=True → MVST-shaped
    (going-concern LEADS, Customer A/B); doubt=False → VRRM (checked-absence, NYCDOT + Avis)."""
    gc = ds.GoingConcern(
        substantial_doubt=doubt,
        verbatim=("These conditions raise substantial doubt about the Company's ability to "
                  "continue as a going concern.") if doubt else "",
        plans="obtain funding through operations; refinance near-term facilities" if doubt else "",
        source_ref="10-Q GC")
    cust = ([ds.ConcentrationCustomer(name="Customer A", pct=52.0, prior_pct=31.0),
             ds.ConcentrationCustomer(name="Customer B", pct=18.0, prior_pct=16.0)] if doubt
            else [ds.ConcentrationCustomer(name="City of New York Department of Transportation",
                                           pct=15.2, prior_pct=15.4)])
    fil = ds.FilingSectionExtract(
        source_ref="10-Q 0001628280-26-033590", going_concern=gc,
        concentration=ds.CustomerConcentration(
            customers=cust, top5_pct=None,
            terms="purchase orders subject to cancellation" if doubt else "", source_ref="10-Q c"))
    rel = ds.ReleaseExtract(source_ref="8-K x EX-99.1", event_impacts=(
        [] if doubt else [ds.EventImpact(
            metric="revenue", effect="reduce", low=135.0, high=145.0, period="2026 annualized",
            verbatim="expects to reduce revenue", source_ref="8-K x EX-99.1")]))
    p = ds.Sourced.present
    return ds.PrimarySource(
        releases=[rel], filing=fil,
        self_funding=p("self-funding: MIXED — latest-Q OCF < 0, LTM FCF > 0", source_ref="x"),
        wall_coherence=p("wall coherence — filing cross-validates panel: panel same-window $109.6M "
                         "vs filing $111.2M — 1.4% < 5% tol → AGREES.", source_ref="x"),
        basis_triangulation=p("EBITDA-basis triangulation (each leverage basis-labeled):\n"
                              "  net debt / company-adjusted LTM EBITDA ($10.7M): ~18.7x\n"
                              "  covenant basis: UNKNOWN (not disclosed)", source_ref="x"),
        guide_verification=p("guide verification (revenue): CIQ 427.516 → VENDOR-ECHO flag",
                             source_ref="x"),
        qa_flags=[])


def test_primary_source_render_surfaces_and_supersede() -> None:
    """(RC-1 C render) The cross-checks block renders going-concern LEADING, wall coherence AGREES,
    the triangulation, guide VENDOR-ECHO, concentration; the two-input self-funding SUPERSEDES the
    survival line; the Avis event impact renders in the drawdown section; and the doubt=False path
    renders the CHECKED-ABSENCE + the NYCDOT exact concentration."""
    lv = ds.LeverageSurvival(net_debt_to_ebitda=_u(), total_debt_to_ebitda=_u(),
                             interest_coverage=_u(), survival=_u(), credit_health=_u())
    m = _minimal_mech().model_copy(update={
        "primary_source": _primary_source_fixture(doubt=True), "leverage_survival": lv})
    block = "\n".join(dr._primary_source_block(m))
    assert "SUBSTANTIAL DOUBT" in block and "going concern" in block.lower()
    assert "~18.7x" in block and "covenant basis: UNKNOWN" in block
    assert "Customer A: 52.0% (prior 31.0%)" in block
    # (declutter) the VERIFICATION flags moved to the appendix block — not between decision sections
    assert "Wall coherence" not in block and "Guide verification" not in block
    ver = "\n".join(dr._verification_lines(m))
    assert "109.6" in ver and "AGREES" in ver, "wall coherence must survive in the appendix"
    assert "VENDOR-ECHO" in ver, "guide verification must survive in the appendix"
    # (declutter) the two-input read REPLACES the one-input survival line (no superseded line left)
    lev = "\n".join(dr._leverage_block(m))
    assert "Self-funding:**" in lev and "MIXED" in lev  # (terse label) rule reads in the value
    assert "supersedes the line above" not in lev
    assert "Survival:**" not in lev  # the one-input line stays replaced, under its terse label too
    m2 = _minimal_mech().model_copy(update={"primary_source": _primary_source_fixture(doubt=False)})
    block2 = "\n".join(dr._primary_source_block(m2))
    assert "none in latest 10-Q — checked, absent" in block2
    assert "City of New York Department of Transportation: 15.2% (prior 15.4%)" in block2
    ei = "\n".join(dr._event_impact_lines(m2))
    assert "reduce revenue by $135–145M" in ei and "2026 annualized" in ei


# --- E3 / E4: EDGAR-anchored fetch — offline fixtures + network-marked live pins ---------------


class _FakeEdgar:
    """A duck-typed EdgarClient for the offline E3/E4 fixtures (only the two methods used)."""

    def __init__(self, *, filings: list[Filing] | None = None,
                 tenks: list[Filing] | None = None, hits: list[FtsHit] | None = None) -> None:
        self._filings, self._tenks, self._hits = filings or [], tenks or [], hits or []

    def recent_filings(self, cik: str, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        return self._tenks if "10-K" in forms else self._filings

    def fulltext_search(self, phrase: str, forms: str = "8-K", ciks: str | None = None,
                        startdt: date | None = None, enddt: date | None = None) -> list[FtsHit]:
        return self._hits


class _FakeHttp:
    def __init__(self, index_json: dict[str, typing.Any]) -> None:
        self._index = index_json

    def get_json(self, url: str, ttl_seconds: int | None = None) -> dict[str, typing.Any]:
        return self._index


class _FakeIndexHttp:
    """A fake SEC http mapping an accession (no dashes) → its index.json — so a per-accession
    exhibit lookup distinguishes the Wu 8-K, the 10-K, and a cross-CIK hit (H1 pointer test)."""

    def __init__(self, by_accession: dict[str, dict[str, typing.Any]]) -> None:
        self._by = by_accession

    def get_json(self, url: str, ttl_seconds: int | None = None) -> dict[str, typing.Any]:
        for accn, idx in self._by.items():
            if accn in url:
                return idx
        return {"directory": {"item": []}}


def test_maturity_8ks_offline_anchors_to_trailing_12m_maturity() -> None:
    """(E3) An 8-K filed within ±10d of an instrument's maturity (in the trailing 12m of the
    reference) is surfaced as a POINTER ('read for resolution') — never an assumption of repayment
    or default. A maturity with no nearby 8-K yields a fail-loud UNKNOWN, not a fabricated line."""
    insts = [_inst("Convertible Loan", 25.0, "2026-05-28")]
    fake = _FakeEdgar(filings=[Filing(
        cik="0001760689", form="8-K", filing_date=date(2026, 5, 28),
        accession="0000947871-26-000585", items=["5.02", "8.01", "9.01"], primary_doc="a.htm")])
    got = dm._maturity_8ks(typing.cast(EdgarClient, fake), "0001760689", insts, date(2026, 7, 3))
    assert got.status is ds.SourceStatus.PRESENT
    assert "8-K at maturity 2026-05-28" in (got.value or "")
    assert "0000947871-26-000585" in (got.value or "")
    assert "read for resolution" in (got.value or "")
    empty = dm._maturity_8ks(typing.cast(EdgarClient, _FakeEdgar()), "0001760689", insts,
                             date(2026, 7, 3))
    assert empty.status is ds.SourceStatus.UNKNOWN and empty.value is None


def test_covenant_query_maps_class_to_a_canonical_agreement_phrase() -> None:
    """(H1b) The CIQ label rarely matches the filing's contract name, so query the class's canonical
    agreement term — a loan → 'Loan Agreement' (surfaces the Wu 8-K), a bond → 'Indenture'."""
    assert dm._covenant_query("Convertible Loan With Shareholder - Term Loan") == "Loan Agreement"
    assert dm._covenant_query("Loan Facilities Agreement With Lenders") == "Loan Agreement"
    assert dm._covenant_query("Convertible Bond - CNY") == "Indenture"


def test_covenant_pointers_reject_cross_cik_and_locate_the_wu_execution_8k() -> None:
    """(H1a-c) The load-bearing fix: efts is CIK-scoped AND a cross-CIK hit is REJECTED — AXESSTEL's
    2005 8-K (0001193125-05-034397, a DIFFERENT filer) the old unscoped search matched for
    'Convertible Bond' is dropped; only the subject's EXHIBIT-BEARING execution filing (the Wu Loan
    & Security 8-K) is kept. A generic BS line (Notes Payable) renders a no-filing note."""
    insts = [_inst("Convertible Loan With Shareholder - Initial Term Loan", 12.0, "2026-05-28"),
             _inst("Notes Payable", 78.3, None, type="Bonds and Notes", secured=False)]
    indexes = {
        "000162828026018264": {"directory": {"item": [
            {"name": "mvst20251231-ex1013.htm"}, {"name": "mvst20251231-ex1021.htm"},
            {"name": "mvst20251231.htm"}]}},                                          # latest 10-K
        "000176068924000021": {"directory": {"item": [
            {"name": "mvst-20240603.htm"}, {"name": "wu_microvast-loanandsecuri.htm"},
            {"name": "wu_microvast-guarantyagree.htm"}]}},                            # the Wu 8-K
        "000119312505034397": {"directory": {"item": [{"name": "axesstel-ex101.htm"}]}},  # AXESSTEL
    }
    edgar = _FakeEdgar(
        tenks=[Filing(cik="0001760689", form="10-K", filing_date=date(2026, 3, 16),
                      accession="0001628280-26-018264", items=[], primary_doc="x.htm")],
        hits=[FtsHit(accession="0001193125-05-034397", cik="0001092492", form="8-K",
                     file_date=date(2005, 2, 22), display_names=["AXESSTEL INC"]),
              FtsHit(accession="0001760689-24-000021", cik="0001760689", form="8-K",
                     file_date=date(2024, 6, 4), display_names=["Microvast"])])
    got = dm._covenant_pointers(
        typing.cast(EdgarClient, edgar), typing.cast(typing.Any, _FakeIndexHttp(indexes)),
        "0001760689", insts)
    assert got.status is ds.SourceStatus.PRESENT
    accs = {r.accession for r in got.value}
    assert "0001193125-05-034397" not in accs  # cross-CIK AXESSTEL 2005 REJECTED (the bug it fixes)
    assert "0001760689-24-000021" in accs  # the Wu execution 8-K located
    assert "0001628280-26-018264" in accs  # the latest-10-K material-contract exhibits
    wu = next(r for r in got.value if r.accession == "0001760689-24-000021")
    assert any("loanandsecuri" in e for e in wu.exhibits)  # the E5 extraction target
    notes = next(r for r in got.value if r.family == "Notes Payable")
    assert notes.accession == "" and "no contract-level filing expected" in notes.note


def test_audit_covenant_pointers_accept_html_named_agreement_exhibit() -> None:
    """(audit PR68/69) An agreement exhibit named '…loanandsecurity.html' (some filers use the
    5-letter extension) MUST be kept — the pre-fix '.htm'/'.txt'-only filter dropped it, flipping a
    DOCUMENTED facility to 'undocumented' (opacity-as-signal inverted)."""
    insts = [_inst("Convertible Loan With Shareholder", 12.0, "2026-05-28")]
    indexes = {"000176068924000021": {"directory": {"item": [
        {"name": "mvst-20240603.htm"}, {"name": "wu_loanandsecurity.html"}]}}}  # .html exhibit
    edgar = _FakeEdgar(hits=[FtsHit(
        accession="0001760689-24-000021", cik="0001760689", form="8-K",
        file_date=date(2024, 6, 4), display_names=["Microvast"])])
    got = dm._covenant_pointers(
        typing.cast(EdgarClient, edgar), typing.cast(typing.Any, _FakeIndexHttp(indexes)),
        "0001760689", insts)
    assert got.status is ds.SourceStatus.PRESENT
    wu = next(r for r in got.value if r.accession == "0001760689-24-000021")
    assert any(e.endswith(".html") for e in wu.exhibits)  # the .html agreement exhibit is kept


def test_capital_structure_covenant_terms_note_is_opacity_as_signal() -> None:
    """(E5) covenant TERMS stay UNKNOWN in the mechanical (deterministic, no-LLM) layer, but the
    note is informative: it says whether an exhibit was located (something to read) or whether the
    facility is wholly undocumented (nothing to extract) — extraction is fenced to the LLM phase."""
    bundle = _fin_bundle(
        {"Capital Structure Details": _CS_DETAILS, "Capital Structure Summary": _CS_SUMMARY},
        freq="annual")
    rec = _min_record(pe=5.0)
    idx = {"directory": {"item": [{"name": "mvst20251231-ex1013.htm"}]}}
    with_ex = _FakeEdgar(
        tenks=[Filing(cik="0001760689", form="10-K", filing_date=date(2026, 3, 16),
                      accession="0001628280-26-018264", items=[], primary_doc="x.htm")])
    cap = dm._capital_structure(
        rec, typing.cast(EdgarClient, with_ex), typing.cast(typing.Any, _FakeHttp(idx)), bundle,
        date(2026, 7, 3))
    assert cap.instruments.status is ds.SourceStatus.PRESENT  # E1 assembly end-to-end
    assert cap.covenant_terms.status is ds.SourceStatus.UNKNOWN
    assert "extract in the LLM phase" in (cap.covenant_terms.note or "")
    bare = dm._capital_structure(
        rec, typing.cast(EdgarClient, _FakeEdgar()), typing.cast(typing.Any, _FakeHttp({})),
        bundle, date(2026, 7, 3))
    assert "no covenant exhibit located" in (bare.covenant_terms.note or "")


class _FakeExhibitHttp:
    """A fake SEC http whose get_text returns fixed exhibit text (or raises, for fail-loud)."""

    def __init__(self, *, fail: bool = False, text: str = "LOAN AND SECURITY AGREEMENT …") -> None:
        self._fail, self._text = fail, text

    def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
        if self._fail:
            raise RuntimeError("simulated fetch failure")
        return self._text


def _pointer_rows() -> list[ds.CovenantPointer]:
    """The located pointers the mechanical layer hands E5 — the Wu 8-K (loanandsecuri + guaranty),
    the 10-K, and a Notes-Payable aggregate line (no accession — never extracted)."""
    return [
        ds.CovenantPointer(family="Convertible Loan", filing="8-K", filing_date="2024-06-04",
                           accession="0001760689-24-000021",
                           exhibits=["mvst-20240603.htm", "wu_microvast-loanandsecuri.htm",
                                     "wu_microvast-guarantyagree.htm"]),
        ds.CovenantPointer(family="material contracts (10-K exhibit index)", filing="latest 10-K",
                           filing_date="2026-03-16", accession="0001628280-26-018264",
                           exhibits=["mvst20251231-ex1013.htm"]),
        ds.CovenantPointer(family="Notes Payable", filing="—", filing_date="—", accession="",
                           exhibits=[],
                           note="no contract-level filing expected (aggregate line item)"),
    ]


def _cs_with_pointers(rows: list[ds.CovenantPointer]) -> ds.CapitalStructure:
    u = ds.Sourced[str].unknown(note="n/a")
    return ds.CapitalStructure(
        instruments=ds.Sourced.unknown(note="n/a"), summary=u, detail_as_of="2026-07-03",
        maturity_filings=u, covenant_pointers=ds.Sourced.present("located", source_ref="efts"),
        covenant_pointer_rows=ds.Sourced.present(rows, source_ref="efts"),
        covenant_terms=ds.Sourced.unknown(note="(E5) pending"))


def test_core_agreement_exhibits_prefers_the_loan_security_doc() -> None:
    """(E5) The picker extracts the CORE agreement exhibit — the loan & security doc, NOT the
    ancillary guaranty — and puts the loan/convertible family first (conversion price is the
    deliverable). The Notes-Payable aggregate (no accession) is never picked."""
    picked = ce._core_agreement_exhibits(_pointer_rows())
    assert picked[0][0].family == "Convertible Loan"
    assert picked[0][1] == "wu_microvast-loanandsecuri.htm"  # loan&security, not guaranty
    assert all(fam.accession for fam, _ in picked)  # Notes Payable (no accession) excluded


def test_covenant_extract_present_is_verbatim_source_bound_and_absent_is_unknown() -> None:
    """(E5/H1d, cond. b) The fenced extraction renders each term as {value, source_ref} or UNKNOWN:
    a stated conversion price is the VERBATIM formula bound to the exhibit it was read from (the
    source_ref is MACHINE-set, not the model's), and a term the exhibit omits is a visible UNKNOWN —
    never a fabricated $/share."""
    payload = {"terms": [
        {"name": "Conversion price / mechanics", "present": True,
         "value": "$1.00 divided by the applicable Conversion Rate",
         "quote": "“Conversion Price” means … an amount equal to $1.00 divided by the applicable "
                  "Conversion Rate at such time."},
        {"name": "Interest / coupon rate", "present": False, "value": "", "quote": ""},
    ]}
    cs_in = _cs_with_pointers([_pointer_rows()[0], _pointer_rows()[2]])  # one extractable exhibit
    term_rows, summary, flags, log = ce.extract_covenant_terms(
        cs_in, llm=_FakeLlm(payload), http=typing.cast(typing.Any, _FakeExhibitHttp()),
        cik="0001760689", ticker="MVST", name="Microvast")
    assert term_rows is not None and term_rows.status is ds.SourceStatus.PRESENT
    conv = next(r for r in term_rows.value if r.name.startswith("Conversion"))
    assert conv.value.status is ds.SourceStatus.PRESENT
    assert conv.value.value == "$1.00 divided by the applicable Conversion Rate"  # verbatim formula
    assert conv.value.source_ref == "8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm"
    assert "verbatim" in (conv.value.note or "")
    intr = next(r for r in term_rows.value if r.name.startswith("Interest"))
    assert intr.value.status is ds.SourceStatus.UNKNOWN and intr.value.value is None
    assert "not stated" in (intr.value.note or "")
    assert summary.status is ds.SourceStatus.PRESENT and "1 of 2" in (summary.value or "")
    assert not flags and "COVENANT EXTRACT" in log


def test_covenant_extract_fetch_failure_fails_loud_unknown_never_blank() -> None:
    """(E5) A fetch failure degrades to UNKNOWN + a flag — the row set is never a silent blank and
    never a fabricated value."""
    cs_in = _cs_with_pointers([_pointer_rows()[0]])
    term_rows, summary, flags, _ = ce.extract_covenant_terms(
        cs_in, llm=_FakeLlm({"terms": []}),
        http=typing.cast(typing.Any, _FakeExhibitHttp(fail=True)),
        cik="0001760689", ticker="MVST", name="Microvast")
    assert term_rows is None
    assert summary.status is ds.SourceStatus.UNKNOWN
    assert any("fetch failed" in f for f in flags)


def test_covenant_extract_no_located_pointer_is_a_noop() -> None:
    """(E5) With no located pointer rows (nothing to read), extraction returns the mechanical
    covenant_terms unchanged and no rows — it never invents an extraction target."""
    u = ds.Sourced[str].unknown(note="n/a")
    cs_in = ds.CapitalStructure(
        instruments=ds.Sourced.unknown(note="n/a"), summary=u, detail_as_of="2026-07-03",
        maturity_filings=u, covenant_pointers=u, covenant_pointer_rows=None,
        covenant_terms=ds.Sourced.unknown(note="(E5) no covenant exhibit located"))
    term_rows, summary, flags, log = ce.extract_covenant_terms(
        cs_in, llm=_FakeLlm({"terms": []}), http=typing.cast(typing.Any, _FakeExhibitHttp()),
        cik="0001760689", ticker="MVST", name="Microvast")
    assert term_rows is None and not flags and log == ""
    assert summary.note == "(E5) no covenant exhibit located"


# --- PR 3 · Commit A: pipeline core (P4 round-robin · governing · P1 digest · maturity) ---


def _pr3_pointers() -> list[ds.CovenantPointer]:
    """Two convertible-family pointers (base 2024 + amendment 2025) + a DISTINCT syndicated facility
    (2022) — the shape that starved the syndicated under the old first-2 picker."""
    return [
        ds.CovenantPointer(family="Convertible Loan", filing="8-K", filing_date="2024-06-04",
                           accession="0001760689-24-000021", exhibits=["wu_loanandsecuri.htm"]),
        ds.CovenantPointer(family="Convertible Loan", filing="8-K", filing_date="2025-03-17",
                           accession="0000947871-25-000313", exhibits=["ss_ex1001.htm"]),
        ds.CovenantPointer(family="Loan Facilities Agreement", filing="8-K",
                           filing_date="2022-09-29", accession="0001760689-22-000094",
                           exhibits=["exhibit101-syndicatedloana.htm"]),
    ]


def test_p4_round_robin_extracts_every_family_before_amendments() -> None:
    """(P4) The picker is a ROUND-ROBIN by family: every DISTINCT live-wall instrument's primary
    exhibit is picked BEFORE any facility's second (amendment), so the syndicated facility can't be
    starved by the convertible's original+amendment eating both slots."""
    picked = ce._core_agreement_exhibits(_pr3_pointers())
    fams = [p.family for p, _ in picked]
    assert fams == ["Convertible Loan", "Loan Facilities Agreement", "Convertible Loan"]
    assert fams.index("Loan Facilities Agreement") == 1  # syndicated slot 2, before the amendment
    assert picked[1][1] == "exhibit101-syndicatedloana.htm"


def test_governing_terms_amendment_overrides_base_and_kills_unknown_above_answer() -> None:
    """(P5 core / FIX-1) Per-exhibit rows collapse to ONE governing value per (family, term): the
    latest-dated PRESENT value wins (the amendment's May-2026 maturity overrides the base's
    Nov-2025), a base PRESENT value is NEVER overridden by an amendment UNKNOWN, and each term
    appears exactly once (no UNKNOWN row above the present answer)."""
    base = "8-K 0001760689-24-000021 · wu_loanandsecuri.htm"
    amd = "8-K 0000947871-25-000313 · ss_ex1001.htm"
    rows = [
        ds.CovenantTerm(name="Maturity date",
                        value=ds.Sourced.present("Nov 28, 2025", source_ref=base)),
        ds.CovenantTerm(name="Conversion price / mechanics",
                        value=ds.Sourced.present("2 shares per $1.00 principal", source_ref=base)),
        ds.CovenantTerm(name="Conversion price / mechanics",
                        value=ds.Sourced.unknown(note=f"not stated in {amd}")),  # amendment: absent
        ds.CovenantTerm(name="Maturity date",
                        value=ds.Sourced.present("May 28, 2026", source_ref=amd)),
    ]
    gov = ce.governing_terms(rows, _pr3_pointers())
    mat = [g for g in gov if g.term == "Maturity date"]
    assert len(mat) == 1 and mat[0].value.value == "May 28, 2026"  # amendment governs
    assert "0000947871-25-000313" in mat[0].amended_by
    conv = [g for g in gov if g.term.startswith("Conversion")]
    assert len(conv) == 1 and conv[0].value.status is ds.SourceStatus.PRESENT  # base survives
    assert "2 shares" in str(conv[0].value.value)  # NOT the amendment UNKNOWN


def test_p1_covenant_digest_is_term_to_value_derives_conversion_and_fails_honest() -> None:
    """(P1/FIX-0) The synthesis digest is TERM→VALUE (never a pointer/count), leads the conversion
    line with the derived $/share, chains 'amended by', fits the cap — and on extraction failure an
    honest 'extraction failed' line, NEVER a 'see the table' pointer to data the LLM can't see."""
    src = "8-K 0001760689-24-000021 · wu.htm"
    gov = [
        ce.GoverningTerm("Convertible Loan", "Conversion price / mechanics",
                         ds.Sourced.present("Rate = two (2) shares of Common Stock per $1.00",
                                            source_ref=src), src, ("0000947871-25-000313",)),
        ce.GoverningTerm("Convertible Loan", "Interest / coupon rate",
                         ds.Sourced.present("SOFR + 9.75% + 3.75% PIK", source_ref=src), src, ()),
    ]
    digest = ce.covenant_digest(gov, None, fail_reason=None)
    assert "see the" not in digest.lower() and "of 20" not in digest  # not a pointer, not a count
    assert "~$0.50/sh" in digest  # derived conversion price leads the line
    assert "amended by 0000947871-25-000313" in digest and "9.75%" in digest
    assert len(digest) <= ce._DIGEST_CAP + 60
    fail = ce.covenant_digest([], None, fail_reason="all located exhibits failed to fetch")
    assert fail.startswith("COVENANT DIGEST — extraction failed:") and "see the" not in fail.lower()


def test_p1_derive_conversion_price_from_stated_rate() -> None:
    """(P1) '$1.00 ÷ N shares' → $/share, tolerating the spelled-out 'two (2) shares' and a long
    parenthetical between 'shares' and 'per $1.00'; '' (never a fabricated number) when unclear."""
    assert "~$0.50/sh" in ce._derive_conversion("two (2) shares Common Stock per $1.00 principal")
    assert "~$0.10/sh" in ce._derive_conversion("a rate of 10 shares per $1.00")
    assert ce._derive_conversion(
        "two (2) shares of Common Stock (subject to adjustment per Section 2.12.4) per $1.00") != ""
    assert ce._derive_conversion("conversion price to be determined by the board") == ""


class _FakeMaturityHttp:
    """Fake SEC http for the maturity-event path: an index.json (get_json) with a primary 8-K body +
    the body text (get_text). ``fail`` makes the body fetch raise (fail-loud path)."""

    def __init__(self, *, body: str, fail: bool = False) -> None:
        self._body, self._fail = body, fail

    def get_json(self, url: str, ttl_seconds: object = None) -> dict[str, typing.Any]:
        return {"directory": {"item": [{"name": "mvst-20260528.htm"}, {"name": "ex99-1.htm"}]}}

    def get_text(self, url: str, ttl_seconds: object = None) -> str:
        if self._fail:
            raise RuntimeError("body fetch failed")
        return self._body


def test_p3_extract_maturity_event_verbatim_or_unknown() -> None:
    """(P3/FIX-3) The fenced maturity-event extractor reads the maturity 8-K's PRIMARY body and
    returns the verbatim resolution PRESENT (bound to '8-K <acc> (<date>)'), or a fail-loud UNKNOWN
    when the body states none / the fetch fails — never a fabricated resolution."""
    u = ds.Sourced[str].unknown(note="n/a")
    cs = ds.CapitalStructure(
        instruments=ds.Sourced.unknown(note="n/a"), summary=u, detail_as_of="d",
        maturity_filings=ds.Sourced.present(
            "8-K at maturity 2026-05-28: filed 2026-05-28 [0000947871-26-000585] 8.01 Other Events",
            source_ref="EDGAR"),
        covenant_pointers=u, covenant_terms=u)
    http = _FakeMaturityHttp(body="Item 8.01. On May 28, 2026 the $25.0M principal was converted.")
    ev, flags, _ = ce.extract_maturity_event(
        cs, llm=_FakeLlm({"present": True,
                          "verbatim": "On May 28, 2026 the $25.0M principal converted to common "
                          "stock (Notice of Conversion)."}),
        http=typing.cast(typing.Any, http), cik="0001760689", ticker="MVST", name="Microvast")
    assert ev is not None and ev.status is ds.SourceStatus.PRESENT and not flags
    assert "converted to common stock" in (ev.value or "")
    assert ev.source_ref == "8-K 0000947871-26-000585 (2026-05-28)"
    # body states none → UNKNOWN
    ev2, _, _ = ce.extract_maturity_event(
        cs, llm=_FakeLlm({"present": False}), http=typing.cast(typing.Any, http),
        cik="0001760689", ticker="MVST", name="Microvast")
    assert ev2 is not None and ev2.status is ds.SourceStatus.UNKNOWN
    # fetch failure → UNKNOWN + flag (fail-loud)
    ev3, flags3, _ = ce.extract_maturity_event(
        cs, llm=_FakeLlm({"present": True, "verbatim": "x"}),
        http=typing.cast(typing.Any, _FakeMaturityHttp(body="", fail=True)),
        cik="0001760689", ticker="MVST", name="Microvast")
    assert ev3 is not None and ev3.status is ds.SourceStatus.UNKNOWN
    assert any("fetch failed" in f for f in flags3)


# --- PR 3 · Commit C: render/policy (P5 governed table · FIX-2 caveat relocation) -----------------


def _cs_two_family_terms() -> ds.CapitalStructure:
    """A capital_structure whose covenant_term_rows span TWO families (convertible base+amendment +
    a syndicated facility), with the convertible maturity amended — the P5 governed-merge shape."""
    base, amd, synd = ("8-K 0001760689-24-000021 · w.htm", "8-K 0000947871-25-000313 · a.htm",
                       "8-K 0001760689-22-000094 · s.htm")
    rows = [
        ds.CovenantTerm(name="Maturity date",
                        value=ds.Sourced.present("Nov 28, 2025", source_ref=base)),
        ds.CovenantTerm(name="Conversion price / mechanics",
                        value=ds.Sourced.present("2 shares per $1.00", source_ref=base)),
        ds.CovenantTerm(name="Maturity date",
                        value=ds.Sourced.present("May 28, 2026", source_ref=amd)),
        ds.CovenantTerm(name="Interest / coupon rate",
                        value=ds.Sourced.present("SOFR + 6.5%", source_ref=synd)),
    ]
    u = ds.Sourced[str].unknown(note="n/a")
    return ds.CapitalStructure(
        instruments=ds.Sourced.unknown(note="n/a"), summary=u, detail_as_of="d", maturity_filings=u,
        covenant_pointers=ds.Sourced.present("x", source_ref="e"),
        covenant_pointer_rows=ds.Sourced.present(_pr3_pointers(), source_ref="efts"),
        covenant_terms=ds.Sourced.present("digest", source_ref="d"),
        covenant_term_rows=ds.Sourced.present(rows, source_ref="fenced"))


def test_p5_covenant_render_is_one_governed_table_per_family() -> None:
    """(P5/FIX-1) The covenant render is TERM-GOVERNED — ONE table per family, the maturity
    shows the AMENDMENT's governing value with an 'amended by' cite, and no UNKNOWN row sits above a
    present answer (the old per-exhibit shape is gone)."""
    lines = dr._covenant_term_lines(_cs_two_family_terms())
    md = "\n".join(lines)
    assert md.count("Covenant terms — Convertible Loan (governing") == 1
    assert md.count("Covenant terms — Loan Facilities Agreement (governing") == 1  # distinct family
    mat = next(ln for ln in lines if ln.startswith("| Maturity date"))
    assert "May 28, 2026" in mat and "amended by 0000947871-25-000313" in mat  # governing=amendment
    assert "| UNKNOWN " not in md  # no UNKNOWN data cell — no UNKNOWN-above-answer (header exempt)


def test_fix2_cost_bound_note_in_covenant_block_and_flag_routed_to_qa() -> None:
    """(FIX-2) A Tier-2 cost-bound / fetch-fail note is a QA self-check (dev/JSON), NOT an analyst
    caveat; the human sees ONE summary line INSIDE the covenant block for any located exhibit not
    extracted this run."""
    caveats, qa = dflags.partition([
        "(E5) exhibit not extracted (cost bound): Loan Facilities·s.htm",
        "(P3) maturity 8-K fetch failed — UNKNOWN: 8-K y"])
    assert caveats == [] and len(qa) == 2  # both routed to QA, none to analyst caveats
    # the covenant block surfaces a not-extracted summary when a pointer has no extracted rows
    extra = _pr3_pointers() + [ds.CovenantPointer(
        family="material contracts (10-K exhibit index)", filing="latest 10-K",
        filing_date="2026-03-16",
        accession="0001628280-26-018264", exhibits=["ex1013.htm"])]  # located but never extracted
    cs = _cs_two_family_terms().model_copy(update={
        "covenant_pointer_rows": ds.Sourced.present(extra, source_ref="efts")})
    md = "\n".join(dr._covenant_term_lines(cs))
    assert "not extracted this run" in md and "0001628280-26-018264" in md  # the un-read 10-K


def test_audit_derive_conversion_no_fabrication_on_bond_convention_and_stray_matches() -> None:
    """(audit M-1/M-4/M-5) The conversion derivation must NEVER fabricate or mis-scale a $/share.
    M-1: the '$1,000 principal' BOND convention is $22.00/sh (1000 ÷ 45.4545), NOT $0.02 — the old
    regex matched '$1' inside '$1,000' and mis-scaled by 1000× the exact dilution figure the digest
    leads synthesis with. M-4/M-5: a cross-clause bridge or a comma-grouped share COUNT yields ''
    (the LLM reads the verbatim), never a wrong number."""
    m1 = ce._derive_conversion("conversion rate of 45.4545 shares per $1,000 principal amount")
    assert "~$22.00/sh" in m1 and "$0.02" not in m1  # denomination CAPTURED, not assumed $1.00
    assert "~$1.20/sh" in ce._derive_conversion("833.3333 shares per $1,000")
    assert "~$0.50/sh" in ce._derive_conversion("two (2) shares per $1.00")  # legit per-$1 kept
    # M-4 — a ';' clause break stops the 'shares'→'per' bridge (an unrelated 'per $1.00')
    assert ce._derive_conversion("issued 5 shares under the plan; interest accrues per $1.00") == ""
    # M-5 — a comma-grouped share COUNT is not a rate (boundary-anchored numerator)
    assert ce._derive_conversion("1,250,000 shares issuable per $1.00 of par value") == ""
    # (RC-1.5 artifact-pass regression) the CURRENT MVST fresh-draw phrasing states the rate ACROSS
    # SENTENCES ("$1.00 divided by … Conversion Rate: two (2) shares"), so no "shares per $"
    # bridge → "" (the raw clause carries it), NOT a fabricated $/sh — the exact rewording that
    # reddened test_t2's old literal-token pin.
    assert ce._derive_conversion(
        '"Conversion Price" means at any time an amount equal to $1.00 divided by the applicable '
        'Conversion Rate at such time. Conversion Rate: two (2) shares of Common Stock') == ""


def test_audit_covenant_digest_honest_on_empty_body_and_boundary_safe_truncation() -> None:
    """(audit CC-1/CC-2/M-2) The digest never emits a bare header implying unseen data (the FIX-0
    failure mode): an all-UNKNOWN governing set — or one with only non-decision terms (security) —
    maps to an HONEST 'no survival-critical … terms' line, not a header alone. And a value truncates
    on a whitespace boundary, so a dollar figure is never chopped mid-digit into a wrong number."""
    src = "8-K 0001760689-24-000021 · wu.htm"
    all_unknown = [ce.GoverningTerm("Convertible Loan", "Conversion price / mechanics",
                                    ds.Sourced[str].unknown(note="not stated"), None, ())]
    d1 = ce.covenant_digest(all_unknown, None, fail_reason=None)
    assert "no survival-critical" in d1 and "not pending" in d1 and d1.count("\n") == 0
    security = [ce.GoverningTerm("Convertible Loan", "Security / collateral / guarantors",
                                 ds.Sourced.present("Guarantors: Holdco, Subco", source_ref=src),
                                 src, ())]
    assert "no survival-critical" in ce.covenant_digest(security, None, fail_reason=None)
    long_val = ("Interest accrues at 9.00% per annum on the outstanding principal balance of "
                "$5,000,000 payable quarterly in arrears")
    dig = ce.covenant_digest(
        [ce.GoverningTerm("Term Loan", "Interest / coupon rate",
                          ds.Sourced.present(long_val, source_ref=src), src, ())], None,
        fail_reason=None)
    assert "…" in dig and "$5,000,00…" not in dig and "$5,00…" not in dig  # no mid-number cut


def test_audit_governing_terms_no_fabricated_amendment_on_tied_or_empty_dates() -> None:
    """(audit X-4) An 'amended by' chain is a REAL base→amendment claim — asserted ONLY on a true
    chronology (distinct, non-empty filing dates). Two PRESENT rows with the SAME (or empty) date
    cannot establish supersession, so no amendment is fabricated from input order; DISTINCT dates
    still yield the real chain."""
    ptrs = [ds.CovenantPointer(family="Term Loan", filing="8-K", filing_date="2025-01-01",
                               accession="0001111111-25-000001", exhibits=["a.htm"]),
            ds.CovenantPointer(family="Term Loan", filing="8-K", filing_date="2025-01-01",
                               accession="0002222222-25-000002", exhibits=["b.htm"])]
    rows = [ds.CovenantTerm(name="Principal", value=ds.Sourced.present(
                "$50M", source_ref="8-K 0001111111-25-000001 · a.htm")),
            ds.CovenantTerm(name="Principal", value=ds.Sourced.present(
                "$300M", source_ref="8-K 0002222222-25-000002 · b.htm"))]
    prin = next(g for g in ce.governing_terms(rows, ptrs) if g.term == "Principal")
    assert prin.amended_by == ()  # tied dates → NO fabricated amendment chain
    ptrs_empty = [p.model_copy(update={"filing_date": ""}) for p in ptrs]
    assert next(g for g in ce.governing_terms(rows, ptrs_empty)
                if g.term == "Principal").amended_by == ()  # empty dates likewise
    ptrs_ok = [ptrs[0], ptrs[1].model_copy(update={"filing_date": "2025-06-01"})]
    prin_ok = next(g for g in ce.governing_terms(rows, ptrs_ok) if g.term == "Principal")
    assert prin_ok.amended_by == ("0002222222-25-000002",) and prin_ok.value.value == "$300M"


def test_audit_contradiction_no_false_positive_when_all_covenant_values_unknown() -> None:
    """(audit CC-3) contradiction_flags keys 'covenant present' on an actually-PRESENT term VALUE,
    not merely the row CONTAINER: an all-UNKNOWN covenant_term_rows block is a genuine opacity gap,
    so an honest 'conversion price must be read from the 8-K' about it is NOT a contradiction."""
    u = ds.Sourced[str].unknown(note="x")
    cs = ds.CapitalStructure(
        instruments=u, summary=u, detail_as_of="d", maturity_filings=u, covenant_pointers=u,
        covenant_terms=ds.Sourced.present("digest", source_ref="d"),
        covenant_term_rows=ds.Sourced.present(  # container PRESENT, every VALUE UNKNOWN
            [ds.CovenantTerm(name="Conversion price / mechanics",
                             value=ds.Sourced[str].unknown(note="not stated in the exhibit"))],
            source_ref="fenced"))
    mech = _minimal_mech().model_copy(update={"capital_structure": cs})
    f = syn.contradiction_flags(
        _bear_synth(["The conversion price mechanics must be read from the 8-K exhibit"]), mech)
    assert f == []  # genuine gap (all values UNKNOWN) → no false CONTRADICTION
    cs2 = cs.model_copy(update={"covenant_term_rows": ds.Sourced.present(
        [ds.CovenantTerm(name="Conversion price / mechanics",
                         value=ds.Sourced.present("2 sh/$1.00", source_ref="8-K x"))],
        source_ref="f")})
    mech2 = _minimal_mech().model_copy(update={"capital_structure": cs2})
    f2 = syn.contradiction_flags(
        _bear_synth(["The conversion price mechanics must be read from the 8-K exhibit"]), mech2)
    assert len(f2) == 1 and f2[0].startswith("CONTRADICTION")  # a PRESENT value still flags


def test_audit_maturity_event_verbatim_is_single_line() -> None:
    """(audit D-2) The stored maturity verbatim collapses whitespace so it renders as ONE markdown
    list item — an embedded newline otherwise breaks the .md item (the web HTML collapses it), a
    py↔js render divergence."""
    u = ds.Sourced[str].unknown(note="n/a")
    cs = ds.CapitalStructure(
        instruments=u, summary=u, detail_as_of="d", covenant_pointers=u, covenant_terms=u,
        maturity_filings=ds.Sourced.present(
            "8-K at maturity 2026-05-28: filed 2026-05-28 [0000947871-26-000585] 8.01",
            source_ref="EDGAR"))
    ev, _f, _l = ce.extract_maturity_event(
        cs, llm=_FakeLlm({"present": True,
                          "verbatim": "On May 28, 2026 the\nprincipal was\n\nconverted to stock."}),
        http=typing.cast(typing.Any, _FakeMaturityHttp(body="Item 8.01. Resolution.")),
        cik="0001760689", ticker="MVST", name="Microvast")
    assert ev is not None and ev.status is ds.SourceStatus.PRESENT
    assert "\n" not in str(ev.value) and "  " not in str(ev.value)  # one clean, single-spaced line


def test_audit_js_covenant_block_mirrors_fix2_not_extracted_line() -> None:
    """(audit D-1) The web renderer (views/dossier.js) MUST mirror the Python FIX-2 covenant-
    completeness line ('N located agreement exhibit(s) not extracted this run'), computed from the
    same located−extracted accession set difference. Without it the web view silently drops a signal
    the .md/PDF shows — the divergence the parity suite did not catch."""
    import pathlib
    js = pathlib.Path("frontend/views/shared/dossier.js").read_text()
    assert "not extracted this run" in js  # the FIX-2 transparency line now exists in JS
    assert "!extracted.has(a)" in js  # the located−extracted set-difference logic is mirrored


@pytest.mark.network
def test_maturity_8ks_real_mvst_anchors_the_may_2026_8k() -> None:
    """(E3, live) A trailing-12m instrument maturity on 2026-05-28 anchors MVST's 8-K filed that
    day. Pins accession 0000947871-26-000585."""
    edgar = EdgarClient.from_config()
    insts = [_inst("Convertible Loan", 25.0, "2026-05-28")]
    got = dm._maturity_8ks(edgar, "0001760689", insts, date(2026, 7, 3))
    assert got.status is ds.SourceStatus.PRESENT
    assert "0000947871-26-000585" in (got.value or "")


@pytest.mark.network
def test_covenant_pointers_real_mvst_cik_scoped_finds_wu_8k_no_cross_cik() -> None:
    """(H1, live) CIK-scoped efts + exhibit verification on real MVST: the latest-10-K exhibits, the
    2024 Wu Loan & Security 8-K (0001760689-24-000021), and ZERO cross-CIK accessions (the AXESSTEL
    2005 hit the old unscoped search returned is gone)."""
    edgar, http = EdgarClient.from_config(), build_sec_http()
    insts = [_inst("Convertible Loan With Shareholder - Initial Term Loan", 12.0, "2026-05-28"),
             _inst("Notes Payable", 78.3, None, type="Bonds and Notes", secured=False)]
    got = dm._covenant_pointers(edgar, http, "0001760689", insts)
    assert got.status is ds.SourceStatus.PRESENT
    accs = [r.accession for r in got.value if r.accession]
    assert "0001760689-24-000021" in accs  # the Wu execution 8-K
    assert any("ex1013" in " ".join(r.exhibits) for r in got.value)  # latest-10-K exhibits
    assert "0001193125-05-034397" not in accs  # AXESSTEL cross-CIK gone
    assert all(a[:10] in ("0001760689", "0001628280", "0000947871")
               for a in accs), f"cross-CIK accession leaked: {accs}"


# --- R1 / R2: keyword-tier interposition + self-twin year-in-name rule ------------------------


def test_point_tier_regex_catches_interposed_negative_ebitda() -> None:
    """(R1/H2) The tier regex tolerates words between 'EBITDA' and 'negative' — the draw's exact
    EXACT phrasing 'adjusted EBITDA of NEGATIVE $5.5M' is a solvency/cash claim (Tier 1), not
    unclassified (4.5), via the '(adjusted) EBITDA … negative' arm ('of' = the 1 interposed word). A
    plain revenue-growth claim is unaffected."""
    assert dr._point_tier("adjusted EBITDA of NEGATIVE $5.5M") == 1.0  # H2: exact string pinned
    assert dr._point_tier("adjusted EBITDA of NEGATIVE $5.5M in the quarter") == 1.0
    assert dr._point_tier("EBITDA turned negative this year") == 1.0
    assert dr._point_tier("revenue grew 20% year over year") != 1.0


def test_point_tier_turned_negative_requires_a_solvency_subject() -> None:
    """(R1 audit) 'turned negative' is Tier-1 ONLY with a solvency/cash SUBJECT — a subject-less
    'competitor guidance turned negative' no longer false-classifies as solvency. The real cases
    (EBITDA / cash flow / FCF turned negative) still land Tier 1."""
    assert dr._point_tier("cash flow turned negative in Q3") == 1.0  # scoped subject
    assert dr._point_tier("free cash flow turned negative") == 1.0  # via the FCF keyword
    assert dr._point_tier("EBITDA was strong; competitor guidance turned negative") != 1.0
    assert dr._point_tier("market sentiment turned negative on the sector") != 1.0


def test_point_tier_going_concern_hyphen_and_space_both_tier1() -> None:
    """(A4) A stated going-concern classifies Tier-1 (solvency/cash) whether written 'going-concern'
    (hyphen) or 'going concern' (space). The hyphen variant was previously missed by the space-only
    keyword — so a claim carrying ONLY that phrase sank to 'unclassified' at the bottom of the
    Analysis bull/bear list. Deterministic classifier pin on FIXED strings (not committed text)."""
    assert dr._point_tier("Substantial doubt about going-concern was raised in the 10-Q") == 1.0
    assert dr._point_tier("Substantial doubt about going concern was raised in the 10-Q") == 1.0
    # a bare hyphen phrase with no OTHER tier-1 keyword must still land Tier-1 (the real regression)
    assert dr._point_tier("The auditor flagged going-concern") == 1.0


# --- PR 3 · Commit B: guards (P2 lint · P6 e2e position pin + py↔JS parity) ---


def _mech_with_covenant_and_maturity() -> ds.MechanicalLayer:
    """A minimal mech whose capital_structure carries covenant_term_rows AND maturity_event —
    the post-FIX-0 state where a lingering 'pending' synthesis claim IS a contradiction."""
    u = ds.Sourced[str].unknown(note="x")
    cs = ds.CapitalStructure(
        instruments=ds.Sourced.unknown(note="x"), summary=u, detail_as_of="d", maturity_filings=u,
        covenant_pointers=u, covenant_terms=ds.Sourced.present("digest", source_ref="d"),
        covenant_term_rows=ds.Sourced.present(
            [ds.CovenantTerm(name="Conversion price / mechanics",
                             value=ds.Sourced.present("2 sh/$1.00", source_ref="8-K x"))],
            source_ref="fenced"),
        maturity_event=ds.Sourced.present(
            "Notice of Conversion: $25.0M principal → common stock",
            source_ref="8-K y (2026-05-28)"))
    return _minimal_mech().model_copy(update={"capital_structure": cs})


def _bear_synth(unknowns: list[str], bears: tuple[str, ...] = ()) -> ds.Synthesis:
    return ds.Synthesis(
        evidence_balance="", bull_points=[],
        bear_points=[ds.SourcedPoint(claim=b, source_ref="r") for b in bears],
        twin_reference_cases=[],
        decisive_question=ds.DecisiveQuestion(question="?", evidence_for=[], evidence_against=[]),
        key_unknowns=list(unknowns))


def test_p2_contradiction_lint_flags_present_blocks_but_not_genuine_gaps() -> None:
    """(P2) The durable guard the FIX-0 incident earns: a synthesis pending-claim ('pending',
    'must be read') is QA-flagged when its SUBJECT is a mechanical block that IS present
    (covenant_term_rows / maturity_event). Pins BOTH incident shapes — and leaves a GENUINE opacity
    gap (no 99.1 revised-guidance exhibit parsed) and a clean draw untouched."""
    mech = _mech_with_covenant_and_maturity()
    # shape 1 — covenant terms called pending, but covenant_term_rows IS present
    f1 = syn.contradiction_flags(
        _bear_synth(["Covenant terms are UNKNOWN (extract pending from located exhibits)"]), mech)
    assert len(f1) == 1 and f1[0].startswith("CONTRADICTION") and "covenant" in f1[0].lower()
    # shape 2 — the maturity/term-loan resolution called must-be-read, but maturity_event IS present
    f2 = syn.contradiction_flags(_bear_synth(
        [], bears=("The 2026-05-28 term loan resolution must be read from the 8-K",)), mech)
    assert len(f2) == 1 and "maturity resolution" in f2[0]
    # genuine opacity gap — revised_guidance really IS UNKNOWN → NOT flagged (specific subject)
    f3 = syn.contradiction_flags(
        _bear_synth(["No revised-outlook 99.1 exhibit was parsed for either earnings 8-K — "
                     "revised forward guidance is UNKNOWN"]), mech)
    assert f3 == []
    # a clean draw that REASONS with the conversion (no pending claim) → not flagged
    f4 = syn.contradiction_flags(_bear_synth(
        [], bears=("Conversion at ~$0.50/sh implies ~50M shares, ~15% dilution",)), mech)
    assert f4 == []
    # the CONTRADICTION flag routes to the QA channel (dev/JSON only), never a human caveat
    _caveats, qa = dflags.partition(f1)
    assert qa == f1 and _caveats == []


def test_rc1_primary_source_digest_shape_verbatims_excluded() -> None:
    """(RC-1 C) The synthesis digest is term → value → source_ref with VERBATIMS EXCLUDED: both
    going-concern states, the QUALITATIVE guide marker, and the quantified event impact appear; the
    verbatim going-concern sentence does NOT."""
    dig = syn._primary_source_digest(_primary_source_fixture(doubt=False))
    assert "term → value → source_ref" in dig and "verbatims EXCLUDED" in dig
    assert "going-concern: none stated (checked, absent)" in dig  # the checked-absence state
    assert "event impact: reduce revenue 135.0–145.0 (2026 annualized)" in dig
    assert "→ 8-K x EX-99.1" in dig  # a source_ref terminates the line
    dig2 = syn._primary_source_digest(_primary_source_fixture(doubt=True))
    assert "going-concern: SUBSTANTIAL DOUBT stated" in dig2
    assert "raise substantial doubt" not in dig2.lower()  # the verbatim SENTENCE is excluded


def test_rc1_contradiction_lint_primary_source_subjects() -> None:
    """(RC-1 C) The three new lint subjects each fire against a PRESENT primary-source fact: an
    event impact the 8-K QUANTIFIES can't be called 'not quantified' (VRRM Avis Key-Unknown
    extinction); a survival-safe framing can't survive a 10-Q SUBSTANTIAL DOUBT; a wall claimed to
    diverge can't survive a filing that AGREES with the CIQ panel. Faithful claims do NOT flag."""
    doubt = _minimal_mech().model_copy(
        update={"primary_source": _primary_source_fixture(doubt=True)})
    avis = _minimal_mech().model_copy(
        update={"primary_source": _primary_source_fixture(doubt=False)})
    f1 = syn.contradiction_flags(
        _bear_synth(["The revenue impact of the Avis termination is not quantified in the facts"]),
        avis)
    assert any("event impact unquantified" in f for f in f1)
    f2 = syn.contradiction_flags(
        _bear_synth([], bears=("Liquidity is adequate — there is no going-concern risk",)), doubt)
    assert any("SUBSTANTIAL DOUBT" in f for f in f2)
    f3 = syn.contradiction_flags(
        _bear_synth([], bears=("The 10-Q maturity wall understates the CIQ panel by ~2x",)), avis)
    assert any("AGREES with the CIQ panel" in f for f in f3)
    # faithful claims — the quantified impact acknowledged, doubt acknowledged — do NOT flag
    clean = syn.contradiction_flags(_bear_synth(
        ["The Avis revenue impact is ~$135–145M (quantified in the 8-K)"],
        bears=("Going-concern doubt is stated; survival hinges on refinancing",)), avis)
    assert clean == []


def test_survival_lint_no_proximity_overmatch() -> None:
    """(incident closure) The going_concern_vs_survival guard no longer PROXIMITY-over-matches, yet
    still catches the genuine 'going-concern <predicate> is/does not <denial>' class. The dropped
    bare '.{0,15} not' arm fired on benign gap-acknowledgments; the predicate-keyed replacement is
    gated on a DENIAL-word whitelist — fires on real denials, quiet on 'plans not synthesized'."""
    # (i) MUST-NOT-FIRE — benign gap-acknowledgments (the negated verb is NOT a denial word)
    benign = "the specifics of the going-concern 'plans' are not synthesized here and must be read"
    assert not syn._SURVIVAL_SAFE_RE.search(benign)  # the exact MVST-draw sentence
    for quiet in (
        "the going-concern plans are not extracted",
        "going-concern mitigation plans are not read into the summary",
        "the going-concern plans, which address the liquidity risk, are not synthesized",
    ):
        assert not syn._SURVIVAL_SAFE_RE.search(quiet), quiet
    # (ii) MUST-FIRE — genuine denials: the no/not-a arms AND the recovered predicate-keyed class
    for denial in (
        "there is no going-concern risk",
        "this is not a going concern for the business",
        "there is no substantial doubt about the company continuing",
        "survival is not at risk given the liquidity runway",
        "the balance sheet is comfortably solvent",
        "the going-concern doubt does not apply after the raise",
        "going-concern risk is not present given the runway",
        "the going-concern warning is not material",
        "the going-concern qualification is not warranted given the recent financing",
    ):
        assert syn._SURVIVAL_SAFE_RE.search(denial), denial
    # end-to-end vs a 10-Q SUBSTANTIAL DOUBT: the benign KU yields NO going-concern contradiction,
    # a real denial still does — the guard fires on denials, stays quiet on gap acknowledgments.
    doubt = _minimal_mech().model_copy(
        update={"primary_source": _primary_source_fixture(doubt=True)})
    assert not any("SUBSTANTIAL DOUBT" in f
                   for f in syn.contradiction_flags(_bear_synth([benign]), doubt))
    # a recovered predicate-keyed denial fires the contradiction end-to-end
    assert any("SUBSTANTIAL DOUBT" in f for f in syn.contradiction_flags(
        _bear_synth([], bears=("the going-concern doubt does not apply after the raise",)), doubt))


def test_p6_py_js_tier_classifier_parity() -> None:
    """(P6) The JS point-tier classifier (views/dossier.js) MUST mirror render.py. PR-E's R1
    interposition regex + the 'turned negative' audit were NEVER mirrored, so the web classified
    the 'adjusted EBITDA of NEGATIVE $5.5M' GAAP point T2 (ordered #4) while the .md had it T1 (#2).
    Structural parity: the JS Tier-1 keyword list and the R1 regex equal Python's."""
    import json
    import pathlib
    js = pathlib.Path("frontend/views/shared/dossier.js").read_text()
    py_t1 = set(dr._TIER_KEYWORDS[0][1])
    m = re.search(r"\[1,\s*\[(.*?)\]\]", js, re.DOTALL)
    assert m is not None
    js_t1 = set(re.findall(r'"([^"]+)"', m.group(1)))
    assert js_t1 == py_t1, f"JS↔PY Tier-1 drift — PY-only={py_t1 - js_t1}, JS-only={js_t1 - py_t1}"
    jm = re.search(r"const _TIER_RE = /(.*?)/i;", js)
    assert jm is not None and jm.group(1) == dr._TIER_REGEX[0][1].pattern, \
        "JS _TIER_RE must equal render.py _TIER_REGEX[0] (the R1 interposition mirror)"
    # behavioural parity through node, when available (same fixtures → same tier)
    import shutil
    import subprocess
    if shutil.which("node"):
        fx = ["adjusted EBITDA of NEGATIVE $5.5M in Q1", "competitor guidance turned negative",
              "operating cash flow turned negative", "revenue grew 20%", "EBITDA turned negative"]
        block = js[js.index("const _TIERKW"):js.index("function _citRank")]
        src = f"{block}\nconsole.log(JSON.stringify({json.dumps(fx)}.map(_pointTier)))"
        out = subprocess.run(["node", "-e", src], capture_output=True, text=True, check=True)
        assert json.loads(out.stdout) == [dr._point_tier(c) for c in fx]  # zero divergence


def test_smpl_pltm_basis_caveat_present_in_committed_artifact_e2e() -> None:
    """(claim #7, TEST-LAYER artifact pin) The P/LTM basis incoherence was observed IN THE
    COMMITTED ARTIFACT (SMPL printed P/LTM 16.0x + EDGAR P/E 10.9x beside LTM GAAP dil EPS −2.08
    with no flag), so the rule owes an artifact-level pin — unit pins on the guard never prove the
    pipeline DELIVERED the caveat into the committed record (a disconnected call site keeps every
    unit test green while artifacts silently lose the warning).

    Invariant, conditional on the SHAPE (never a value pin on the living artifact): IF the
    committed SMPL dossier's STRUCTURED LTM GAAP diluted EPS is negative, its caveats MUST carry
    the basis warning. A future re-assembly where SMPL's LTM turns positive passes legitimately
    (the caveat rightly disappears with the shape). The matched fragment is a code-generated
    TEMPLATE (mechanical.py, the (d) branch) — deterministic, never LLM prose, so the substring
    cannot rot on a reword."""
    p = Path("data/dossiers/SMPL/dossier.json")
    if not p.exists():
        pytest.skip("no committed SMPL dossier.json")
    doss = ds.Dossier.model_validate_json(p.read_text())
    ltm = dm._ltm_gaap_eps(doss.mechanical.financial_summary)
    if ltm is None or ltm >= 0:
        return  # the shape that bit is gone from the artifact — nothing to guard here
    assert any("rest on normalized/adjusted earnings" in c for c in doss.caveats), (
        f"SMPL LTM GAAP dil EPS {ltm} < 0 but the P/LTM basis caveat is ABSENT from the "
        "committed artifact — the guard is disconnected from the pipeline (claim-#7 regression)"
    )


def test_p6_ordered_points_hybrid_invariants_and_recon_present_e2e() -> None:
    """(P6, relayered for the HYBRID — TEST-LAYER invariant-only) On the LIVING committed
    dossiers, assert the PHRASING-INDEPENDENT invariants the hybrid `_ordered_points` guards —
    never any LLM claim's tier (a classifier result on LLM text is an LLM-string pin IN DISGUISE).
    (a) BEAR: side-rank is non-decreasing — the survival-first guarantee (a T1 fact can never sit
    below a narrative point); within an equal-rank run, crux-linked points precede non-crux.
    (b) BULL: crux-prefix — once a non-crux point appears, no crux-linked point follows; within
    each crux group the bull side-rank is non-decreasing (mechanism before the enabler).
    (c) py==JS on the SAME refs (the orderPoints mirror) — zero order drift.
    (d) a cited bear point citing the EX-99.1 reconciliation EXISTS on MVST (presence only).
    Tier/order VALUES stay pinned at the deterministic layer on frozen fixtures."""
    import json
    import pathlib
    import shutil
    import subprocess
    tickers = [t for t in ("MVST", "VRRM")
               if pathlib.Path(f"data/dossiers/{t}/dossier.json").exists()]
    if not tickers:
        pytest.skip("no committed dossier.json")
    js = pathlib.Path("frontend/views/shared/dossier.js").read_text()
    order_block = js[js.index("const _TIERKW"):js.index("function trajectoryTable")]
    have_node = shutil.which("node") is not None

    def js_order(pts: list[typing.Any], side: str, crux: frozenset[str],
                 drv: frozenset[str]) -> list[str]:
        rows = [{"claim": p.claim, "source_ref": p.source_ref, "cited": getattr(p, "cited", True)}
                for p in pts]
        driver = (f"const O=orderPoints({json.dumps(rows)},{json.dumps(side)},"
                  f"new Set({json.dumps(sorted(crux))}),new Set({json.dumps(sorted(drv))}));"
                  "console.log(JSON.stringify(O.map((p)=>p.claim)));")
        out = subprocess.run(["node", "-e", order_block + "\n" + driver],
                             capture_output=True, text=True, check=True)
        return list(json.loads(out.stdout))

    for t in tickers:
        doss = ds.Dossier.model_validate_json(
            pathlib.Path(f"data/dossiers/{t}/dossier.json").read_text())
        if doss.synthesis is None:
            continue
        s = doss.synthesis
        drv = dr._driver_refs_of(doss.mechanical)
        for side, case in (("bull", list(s.bull_points)), ("bear", list(s.bear_points))):
            crux = dr._decisive_refs(s, side)
            ordered = dr._ordered_points(case, side=side, crux_refs=crux, driver_refs=drv)
            rank = dr._BULL_TIER_RANK if side == "bull" else dr._BEAR_TIER_RANK
            ranks = [rank[tier] for _p, tier, _cr, _cx, _mb in ordered]
            cruxes = [cx for _p, _t, _cr, cx, _mb in ordered]
            if side == "bear":
                # (a) survival-first: bear rank non-decreasing; crux-prefix inside equal-rank runs
                assert ranks == sorted(ranks), f"{t} bear: rank demotion {ranks}"
                for r in set(ranks):
                    run = [cx for rk, cx in zip(ranks, cruxes, strict=True) if rk == r]
                    assert run == sorted(run, reverse=True), f"{t} bear: crux order in rank {r}"
            else:
                # (b) crux-prefix over the whole list; rank monotone within each crux group
                assert cruxes == sorted(cruxes, reverse=True), f"{t} bull: crux prefix broken"
                for grp in (True, False):
                    sub = [rk for rk, cx in zip(ranks, cruxes, strict=True) if cx is grp]
                    assert sub == sorted(sub), f"{t} bull: rank demotion in crux={grp}"
            if have_node:  # (c) py==JS with the same refs → identical claim ordering
                py_claims = [p.claim for p, *_ in ordered]
                assert js_order(case, side, crux, drv) == py_claims, f"{t}: py↔js order drift"
        # (d) presence: a cited bear point citing the EX-99.1 recon exists (MVST — the P6 subject)
        if t == "MVST":
            recon = [p for p in doss.synthesis.bear_points
                     if "EX-99.1" in (p.source_ref or "") and getattr(p, "cited", False)]
            assert recon, "MVST: no cited EX-99.1-reconciliation bear point"


def test_brief_financial_snapshot_right_aligns_all_period_columns() -> None:
    """(audit fix) The Brief 'Financial snapshot' table right-aligns EVERY period column. The
    num_cols off-by-one (range(1, len+1) instead of range(len)) left the FIRST period column
    left-aligned. e2e on the committed MVST artifact, phrasing-independent (alignment structure,
    no value pinned). Pre-fix: cells[1] == '---' → this fails."""
    import pathlib
    p = pathlib.Path("data/dossiers/MVST/dossier.json")
    if not p.exists():
        pytest.skip("no committed MVST dossier.json")
    md = dr.render_markdown(ds.Dossier.model_validate_json(p.read_text()))
    lines = md.splitlines()
    head_i = next((i for i, ln in enumerate(lines)
                   if "**Financial snapshot**" in ln and dr._TABLE_MARK in ln), None)
    assert head_i is not None, "no Financial-snapshot ds-table in the MVST Brief"
    align = next(ln for ln in lines[head_i + 1:head_i + 6] if ln.startswith("|-"))
    cells = [c.strip() for c in align.strip().strip("|").split("|")]
    assert cells[0] == "---", f"label column should stay left-aligned: {cells}"
    assert len(cells) >= 3, f"expected label + >=2 period columns: {cells}"
    assert all(c == "---:" for c in cells[1:]), f"every period column must right-align: {cells}"


def test_customer_concentration_floor_keeps_ge_qualifier() -> None:
    """(audit fix) A disclosed customer FLOOR (value_kind='floor', a filing's 'exceeded N%') renders
    with its ≥ qualifier — never as an exact N%; an all-exact set carries no qualifier. Source
    fidelity: the human sees what the filing stated, not a spuriously exact number."""
    base = _primary_source_fixture(doubt=True)
    assert base.filing is not None and base.filing.concentration is not None

    def _mech_with(custs: list[ds.ConcentrationCustomer]) -> ds.MechanicalLayer:
        conc = base.filing.concentration.model_copy(update={"customers": custs})
        fil = base.filing.model_copy(update={"concentration": conc})
        ps = base.model_copy(update={"filing": fil})
        return _minimal_mech().model_copy(update={"primary_source": ps})

    floor = _mech_with([
        ds.ConcentrationCustomer(name="A", pct=52.0, prior_pct=31.0, value_kind="floor"),
        ds.ConcentrationCustomer(name="B", pct=18.0, prior_pct=16.0)])
    line = dr._customer_concentration(floor)
    assert line is not None and "top customer ≥52%" in line and "top-2 ~≥70%" in line
    exact = _mech_with([
        ds.ConcentrationCustomer(name="A", pct=52.0, prior_pct=31.0),
        ds.ConcentrationCustomer(name="B", pct=18.0, prior_pct=16.0)])
    line2 = dr._customer_concentration(exact)
    assert line2 is not None and "top customer 52%" in line2 and "≥" not in line2


def test_brief_snapshot_renders_present_and_omits_unknown() -> None:
    """(tier redesign) The Brief snapshot line leads with the exchange, renders each PRESENT
    stock-info field, and OMITS an UNKNOWN one (fail-honest — never a fabricated placeholder);
    nothing present → no line. CIK is NOT here — it moved to Record & reproduce (an identifier,
    not a decision figure). Value pin on a FROZEN fixture (the redraw-safe layer)."""
    import datetime as _dt
    p, u = ds.Sourced.present, ds.Sourced.unknown
    si = ds.StockInfo(
        price=p(4.22, source_ref="EOD"), high_52w=p(25.83, source_ref="EOD"),
        low_52w=p(3.40, source_ref="EOD"), shares_out=p(151906653.0, source_ref="EDGAR"),
        book_value_ps=p(1.79, source_ref="CIQ"), market_cap=p(668.4, source_ref="CIQ"),
        as_of=_dt.date(2026, 7, 8))
    body = " ".join(dr._brief_snapshot("Nasdaq", si))
    assert body.startswith("- **Snapshot:** Nasdaq · ")  # exchange leads
    assert "CMP $4.22 (2026-07-08)" in body and "cap $668M" in body
    assert "52-wk $3.40–$25.83" in body
    assert "shares 151.9M" in body and "book value/sh $1.79" in body
    assert "CIK" not in body  # moved to Record & reproduce — never in the snapshot line
    # fail-honest: an UNKNOWN price/book → those chunks drop; the rest still render
    si2 = si.model_copy(update={"price": u(note="no bars"), "book_value_ps": u(note="no CIQ")})
    body2 = " ".join(dr._brief_snapshot("NYSE", si2))
    assert "CMP" not in body2 and "book value/sh" not in body2
    assert "52-wk $3.40–$25.83" in body2 and "shares 151.9M" in body2 and "NYSE" in body2
    # nothing present at all → the whole line is omitted (no empty snapshot)
    allu = ds.StockInfo(price=u(note="x"), high_52w=u(note="x"), low_52w=u(note="x"),
                        shares_out=u(note="x"), book_value_ps=u(note="x"), market_cap=u(note="x"))
    assert dr._brief_snapshot(None, allu) == []


# --- (PR-B) operating-drivers: A3 Key Developments, fail-loud transcript, Mechanism render --------

# SYNTHETIC Key-Developments text (real CIQ text is licensed → never committed). 5-column layout
# ('Date|Company|Type|Headline|…') — the header-driven parse must find Type at index 2, not assume.
_KD_5COL = (
    "Report Criteria|\n"
    "Selected Categories:|Company Forecasts and Ratings, Customer/Product|\n"
    "Key Developments|\n"
    "Date|Company|Type|Headline|Other Parties|\n"
    "May-07-2026|Acme Co. (NasdaqGM:ACME)|Corporate Guidance - Raised|Acme Raises "
    "FY2026 Guidance|-|\n"
    "Situation: On May 7, 2026, Acme raised its full-year guidance on strong demand.\n"
    "Apr-23-2026|Acme Co.|Product-Related Announcement|Acme Launches New Product Line|-|\n"
    "Jun-29-2026|Acme Co.|Index Constituent Drop|Acme dropped from Russell 2000|-|\n"
    "May-01-2026|Acme Co.|Executive/Board Change - Other|Acme CFO transition|-|\n"
)
# 4-column layout ('Date|Type|Headline|…') — Type at index 1. Same rows, no Company column.
_KD_4COL = (
    "Date|Type|Headline|Other Parties|\n"
    "Mar-16-2026|Corporate Guidance - New/Confirmed|Co Provides 2026 Guidance|-|\n"
    "Jan-02-2026|Index Constituent Add|Co added to an index|-|\n"
)


def _kd_bundle(monkeypatch: pytest.MonkeyPatch, text: str) -> ciq.CiqBundle:
    """A bundle carrying one key_developments workbook; read_text is stubbed to `text` (the RTF
    decode itself is covered by test_ciq — here we pin the parse/filter/header logic)."""
    from pathlib import Path
    monkeypatch.setattr(cs, "read_text", lambda path, fmt=None: text)
    wb = ciq.CiqWorkbook(
        kind="key_developments", path=Path("kd.rtf"), fmt=ciq.CiqFormat.RTF_TEXT, freq=None)
    return ciq.CiqBundle(ticker="ACME", workbooks=(wb,))


def test_a3_key_developments_header_driven_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    """(PR-B A3) EVENT rows from the KD export: header-driven column detection (5-col vs 4-col
    layouts), the INCLUDE filter (guidance/product KEPT; index-constituent / exec-change DROPPED),
    the Situation detail as verbatim, and a source_ref bound to the file + date."""
    rows = cs.key_development_drivers(_kd_bundle(monkeypatch, _KD_5COL))
    kept = {r.metric for r in rows}
    assert "Corporate Guidance - Raised" in kept and "Product-Related Announcement" in kept
    assert "Index Constituent Drop" not in kept  # ⊖ index mechanics dropped
    assert "Executive/Board Change - Other" not in kept  # ⊖ governance dropped
    guid = next(r for r in rows if r.metric == "Corporate Guidance - Raised")
    assert guid.kind.value == "event" and guid.period == "May-07-2026" and guid.tier == "anchored"
    assert guid.value == "Acme Raises FY2026 Guidance"
    assert "raised its full-year guidance" in guid.verbatim  # the Situation line
    assert guid.source_ref == "CIQ Key Developments: kd.rtf · May-07-2026"
    # 4-column layout resolves Type at a DIFFERENT index — header-driven, not positional
    rows4 = cs.key_development_drivers(_kd_bundle(monkeypatch, _KD_4COL))
    assert [r.metric for r in rows4] == ["Corporate Guidance - New/Confirmed"]  # index add dropped


def test_a3_headerless_kd_is_honest_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """(PR-B A3 ⊖) A KD text with no recognizable Date|Type|Headline header → honest empty, never a
    guessed column position."""
    assert cs.key_development_drivers(
        _kd_bundle(monkeypatch, "Report Criteria|\nrandom text\n")) == []


def test_transcript_fail_loud_unparsed_flag_and_routing() -> None:
    """(PR-B §3-now) Transcripts ON FILE but unparsed (LibreOffice missing) → a QA flag routed to
    dev (not an analyst caveat); no transcript on file → NO flag (absence is not failure); a parsed
    slice → NO flag. The 2026-07-10 silent-swallow can't recur."""
    from pathlib import Path

    from vinci.dossier.flags import partition
    tr = ciq.CiqBundle(ticker="X", workbooks=(ciq.CiqWorkbook(
        kind="transcript", path=Path("c.rtf"), fmt=ciq.CiqFormat.OLE_DISGUISED, freq=None),))
    flag = cs.unparsed_transcript_flag(tr, None)  # on file, slice failed → flag
    assert flag is not None and "unparseable" in flag
    caveats, qa = partition([flag])
    assert flag in qa and caveats == []  # dev/QA, never a human caveat
    assert cs.unparsed_transcript_flag(tr, "--- call ---\nremarks") is None  # parsed → no flag
    assert cs.unparsed_transcript_flag(  # absent → no flag
        ciq.CiqBundle(ticker="X", workbooks=()), None) is None


def _drv(kind: str, **kw: object) -> ds.OperatingDriver:
    base: dict[str, object] = {"metric": "m", "value": "v", "verbatim": "vb",
                               "source_ref": "8-K X EX-99.1", "tier": "anchored"}
    return ds.OperatingDriver(kind=ds.DriverKind(kind), **{**base, **kw})  # type: ignore[arg-type]


def test_operating_drivers_feed_synthesis_but_render_no_standalone_block() -> None:
    """(PR-B — decision 2026-07-13) The operating drivers are EXTRACTION that FEEDS SYNTHESIS, not a
    standalone rendered surface: a mechanically-extracted fact list can't render the directional
    CALL (that is the human's verdict). So the field stays machine-complete in the JSON, the
    synthesis digest surfaces it (the LLM is told to ground the bull/bear in it), and NO standalone
    Mechanism block renders in the md — REAL invariants, not the absence of never-existed tokens."""
    from vinci.dossier.synthesis import _operating_drivers_digest
    rows = [_drv("attribution", metric="revenue", value="$5m, or 48%", value_num=-48.0, unit="%",
                 verbatim="Revenue decreased 48% due to a sales-volume reduction.",
                 source_ref="10-Q Z")]
    import pathlib as _pl
    pth = _pl.Path("data/dossiers/AORT/dossier.json")
    if not pth.exists():
        pytest.skip("AORT committed dossier absent")
    d = ds.Dossier.model_validate_json(pth.read_text())
    od = ds.OperatingDriversExtract(rows=rows, qa_flags=[])
    inj = d.model_copy(update={"mechanical": d.mechanical.model_copy(
        update={"operating_drivers": od})})
    # (1) drivers FEED synthesis — the digest carries the metric/value/source_ref
    digest = _operating_drivers_digest(od)
    assert "revenue" in digest.lower() and "48" in digest and "10-Q Z" in digest
    # (2) but NOT as a standalone block — no Mechanism heading in the brief/analysis md
    md = dr.render_markdown(inj)
    assert "## Mechanism" not in md and "## Operating drivers (mechanism)" not in md
    # (3) machine-complete: the field rides in the JSON, never deleted
    assert inj.mechanical.operating_drivers is not None
    assert len(inj.mechanical.operating_drivers.rows) == 1


# --- (PR-B Tier B) LLM-fenced transcript extractor — validator behavior (deterministic FakeLlm) ---
# SYNTHETIC transcript slice (real CIQ transcript text is licensed → never committed; the real-slice
# validation ran live against MVST's transcript). Two fenced calls; the validator is pinned here.
_TB_SLICE = (
    "--- Acme Q1 2026 Earnings Call, May 1, 2026 ---\n"
    "Thanks operator. We shipped approximately 266 megawatt hours in the quarter, up 16% "
    "year over year. Average selling price rose 7% effective March 1 across the fleet.\n"
    "--- Acme Q4 2025 Earnings Call, Feb 1, 2026 ---\n"
    "We added 40,000 members during the fourth quarter."
)


class _TBFakeLlm(LlmClient):
    def __init__(self, payload: dict[str, typing.Any], *, raise_err: bool = False) -> None:
        self._payload, self._raise = payload, raise_err

    @property
    def model(self) -> str:
        return "fake-tb-1"

    def extract(  # type: ignore[override]
        self, *, system: str, user: str, tool: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        if self._raise:
            raise LlmError("simulated")
        return self._payload


def test_tier_b_validator_keeps_valid_drops_bad_and_binds_source() -> None:
    """(PR-B Tier B) The code-level validator — the load-bearing UPGRADE over covenant extraction:
    a real quote + a value whose numbers trace to that quote is KEPT (tier=llm-fenced, verbatim,
    source_ref machine-set to the enclosing call); a fabricated quote, an invented number, and a
    kind outside the fenced set are each DROPPED to a flag. Deterministic — no LLM-string pin."""
    from vinci.dossier.driver_extract import extract_transcript_drivers
    payload = {"drivers": [
        {"kind": "leading_indicator", "metric": "shipments", "period": "Q1 2026",
         "value": "266 megawatt hours",
         "quote": "We shipped approximately 266 megawatt hours in the quarter, up 16% "
                  "year over year."},
        {"kind": "pricing_action", "metric": "ASP",
         "value": "rose 7% effective March 1",
         "quote": "Average selling price rose 7% effective March 1 across the fleet."},
        {"kind": "leading_indicator", "metric": "deliveries",  # ⊖ fabricated quote
         "value": "800 MWh",
         "quote": "We delivered a record 800 MWh to Europe this quarter."},
        {"kind": "leading_indicator", "metric": "shipments",  # ⊖ 999 not in quote
         "value": "999 MWh",
         "quote": "We added 40,000 members during the fourth quarter."},
        {"kind": "attribution", "metric": "x", "value": "1",  # ⊖ kind outside the fenced set
         "quote": "We added 40,000 members during the fourth quarter."},
    ]}
    rows, flags, _log = extract_transcript_drivers(
        _TB_SLICE, llm=_TBFakeLlm(payload), ticker="ACME", name="Acme")
    assert len(rows) == 2
    kpi = next(r for r in rows if r.metric == "shipments")
    assert kpi.tier == "llm-fenced" and kpi.value_num is None and kpi.unit is None  # verbatim-only
    # source_ref machine-set to the enclosing call
    assert kpi.source_ref == "CIQ transcript: Acme Q1 2026 Earnings Call, May 1, 2026"
    assert kpi.kind.value == "leading_indicator"
    # each bad row dropped with a reason (fabricated quote, untraced number, bad kind)
    assert len(flags) == 3
    joined = " ".join(flags)
    assert "quote not in transcript" in joined
    assert "not in its quote" in joined
    assert "unknown kind" in joined


def test_tier_b_llm_error_and_absent_slice_fail_loud() -> None:
    """(PR-B Tier B ⊖) An LLM error or an absent slice yields NO rows + a naming flag — never a
    fabricated driver, never a silent empty (the FIX-0 shape)."""
    from vinci.dossier.driver_extract import extract_transcript_drivers
    rows, flags, _ = extract_transcript_drivers(None, llm=_TBFakeLlm({}), ticker="X", name="X")
    assert rows == [] and any("no transcript slice" in f for f in flags)
    rows2, flags2, _ = extract_transcript_drivers(
        _TB_SLICE, llm=_TBFakeLlm({}, raise_err=True), ticker="X", name="X")
    assert rows2 == [] and any("LLM error" in f for f in flags2)


def test_tier_b_row_cap_flags_excess() -> None:
    """(PR-B Tier B ⊖) The row cap bounds cost/space — the excess is FLAGGED, never silently cut."""
    from vinci.dossier.driver_extract import _MAX_ROWS, extract_transcript_drivers
    one = {"kind": "leading_indicator", "metric": "shipments", "value": "266 megawatt hours",
           "quote": "We shipped approximately 266 megawatt hours in the quarter, up 16% "
                    "year over year."}
    payload = {"drivers": [dict(one) for _ in range(_MAX_ROWS + 3)]}
    rows, flags, _ = extract_transcript_drivers(
        _TB_SLICE, llm=_TBFakeLlm(payload), ticker="X", name="X")
    assert len(rows) == _MAX_ROWS
    assert sum("capped" in f for f in flags) == 3  # the 3 excess rows each flagged


def test_dossier_top_redesign_no_duplication_static() -> None:
    """(tier redesign 2026-07-21) The dossier top: a SLIM header — company identity in the
    institutional format "Name (Exchange: TICKER)" + the DOCUMENT date, NO process meta — and an
    opener card ("At a glance") whose company block never repeats the header identity. Node-free
    source pins (the render is deterministic HTML)."""
    src = Path("frontend/views/shared/dossier.js").read_text()
    # the opener layout + the key-figures sidebar
    assert 'class="brief-body"' in src and "briefSnapshot(d, m)" in src
    assert 'class="brief-snap"' in src
    # identity renders ONCE: the header carries Name (Exchange: TICKER); the sidebar's identity
    # line is gone, and so is its Exchange row (the header is the exchange's one home)
    assert 'class="page-h-id"' in src
    assert 'class="brief-snap-idn"' not in src
    assert 'push("Exchange"' not in src
    # the OLD duplicated bits stay gone (idn dup, meta cap dup, inline stock line, queue rank)
    assert '"brief-idn"' not in src and '"brief-meta"' not in src and '"brief-stock"' not in src
    assert "function stockInfoLine" not in src
    assert "Queue rank" not in src
    # the old header meta line (process telemetry as a subtitle) is GONE — the document date is
    # the header; the vintage map + model live in Record & reproduce
    assert "Assembled facts" not in src
    assert "function recordAndReproduce" in src
    # the card's own title dup + machine-read pill stay gone
    assert "Brief — first cut" not in src
    assert "machine read · not a verdict" not in src and '"brief-tag"' not in src
    # the lean word is tinted by DIRECTION (bear→danger, bull→live, else grey) — the machine's
    # evidence READ, still not a verdict (the verdict of record stays the human's, via the ledger)
    assert "function machineReadHtml" in src
    assert 'includes("bear") ? "var(--danger)"' in src
    assert 'includes("bull") ? "var(--live)"' in src


def test_brief_machine_read_lean_bold_sentence_cased() -> None:
    """(brief) The teaser's machine READ leads with its lean word bold + Sentence-cased (the web
    mirror colors it; markdown has no tint). The old '**Machine read**
    _(not a verdict)_' prefix is gone; the 'not a verdict' framing lives in the doc header + the
    Recommendation slot below. Unit pins the shared parser; an e2e sweep pins the wiring on every
    committed dossier (phrasing-independent — it derives the expected line from the value)."""
    # unit — lean bold + Sentence case, internal hyphen kept, rationale verbatim, fail-soft
    assert dr._machine_read_md("strongly-bearish — doubt") == "**Strongly-bearish** — doubt"
    assert dr._machine_read_md("mixed — a loss") == "**Mixed** — a loss"
    assert dr._machine_read_md("bullish — a moat") == "**Bullish** — a moat"
    assert dr._machine_read_md("no separator here") == "no separator here"  # fail-soft → verbatim
    # e2e — every committed dossier: the rendered read IS _machine_read_md(eb), never the old prefix
    import pathlib
    seen = 0
    for jp in sorted(pathlib.Path("data/dossiers").glob("*/dossier.json")):
        d = ds.Dossier.model_validate_json(jp.read_text())
        s = d.synthesis
        if s is None or not s.evidence_balance:
            continue
        seen += 1
        md = dr.render_markdown(d)
        assert "**Machine read** _(not a verdict)_" not in md, f"{jp.parent.name}: old prefix"
        assert dr._machine_read_md(s.evidence_balance) in md, f"{jp.parent.name}: not bold-lean"
    assert seen >= 2, "expected >=2 committed dossiers with an evidence_balance"


def test_machine_proposal_derivation_deterministic() -> None:
    """(2026-07-13 pivot, unit) derive_proposal is a FROZEN 3-row face-validity mapping over the
    lean LABEL — deterministic, fail-honest on everything else, never a guessed direction.
    Positive pins (the three rows + label normalization + the display word) AND negative pins
    (mixed / empty / None / unsplit / unrecognized each yield NO proposal)."""
    from vinci.dossier.verdict import derive_proposal
    from vinci.schemas.ledger import Verdict as Vd

    assert derive_proposal("strongly-bearish — reason").action is Vd.AVOID_TERMINAL
    assert derive_proposal("strongly-bullish — reason").action is Vd.BUY
    assert derive_proposal("Strongly bearish — reason").action is Vd.AVOID_TERMINAL  # normalized
    assert derive_proposal("strongly-bearish — reason").action_word == "AVOID"  # display word
    assert derive_proposal("strongly-bullish — reason").action_word == "BUY"
    # NO-proposal legs — each fail-honest, each with its why in the note
    mixed = derive_proposal("mixed — two-sided evidence")
    assert mixed.action is None and "two-sided" in mixed.note
    assert derive_proposal("").action is None
    assert derive_proposal(None).action is None
    assert derive_proposal("no separator here").action is None
    unknown = derive_proposal("neutral — nothing decisive")
    assert unknown.action is None and "unrecognized" in unknown.note
    # a directional REASON must never flip a read — the label alone drives the mapping
    assert derive_proposal("mixed — strongly-bearish tail risks dominate").action is None


def test_machine_proposal_frozen_fixture_values() -> None:
    """(pivot value pins — FROZEN fixtures) The committed MVST/AORT leans AS OF 2026-07-13, frozen
    here as literals. Ticker→verdict VALUE pins live HERE, never on the living artifacts (a
    re-assembly re-words a lean; the living-artifact e2e below pins invariants only)."""
    from vinci.dossier.verdict import derive_proposal
    from vinci.schemas.ledger import Verdict as Vd

    mvst = ("strongly-bearish — stated going-concern doubt with a near-term maturity wall against "
            "thin cash while adjusted EBITDA has turned negative and revenue is contracting.")
    aort = ("mixed — growing absolute EBITDA and above-peer growth collide with a -78% "
            "forward-EPS collapse, worse-than-peer leverage, and negative forward FCF.")
    p = derive_proposal(mvst)
    assert p.action is Vd.AVOID_TERMINAL and p.lean == "strongly-bearish"
    assert p.reason is not None and p.reason.startswith("stated going-concern doubt")
    q = derive_proposal(aort)
    assert q.action is None and q.lean == "mixed"  # two-sided → the human decides cold


def test_brief_hides_proposal_until_verdict_but_reveals_on_show_proposal() -> None:
    """(anti-anchoring, 2026-07-13 — LIVING artifacts, phrasing-independent invariants ONLY) The
    brief HIDES the machine's proposed verdict by default so it can't anchor the human before they
    log theirs: the default render carries the sealed-note (never the AVOID/BUY proposal line), the
    human confirm/override slot, and the pre-pivot slot gone. With ``show_proposal=True`` the SAME
    dossier reveals EXACTLY the proposal line its own committed lean derives (both sides run
    derive_proposal, so a re-worded lean can't rot this); a non-None proposal only ever derives from
    a strongly-* label. NO ticker→verdict value pin here (those are frozen on the fixture below)."""
    import pathlib

    from vinci.dossier.verdict import derive_proposal

    seen = 0
    for jp in sorted(pathlib.Path("data/dossiers").glob("*/dossier.json")):
        d = ds.Dossier.model_validate_json(jp.read_text())
        s = d.synthesis
        p = derive_proposal(s.evidence_balance if s is not None else None)
        hidden = dr.render_markdown(d)  # default: NO proposal surface at all (2026-07-21 round)
        revealed = dr.render_markdown(d, show_proposal=True)  # the operator's explicit peek
        # DEFAULT carries no proposal surface — no line, no sealed-note, no section header. The
        # mechanism is sealed at assembly and revealed by the ledger CLI post-log; this document
        # shows nothing it could anchor with.
        assert "Machine proposal" not in hidden, f"{jp.parent.name}: proposal surfaced by default"
        assert "machine proposal sealed" not in hidden, f"{jp.parent.name}: stale sealed-note"
        assert "## Scenario analysis" not in hidden, (
            f"{jp.parent.name}: the proposal section must exist only under --show-proposal")
        # --show-proposal REVEALS exactly the derived line, under its own section header
        assert dr._machine_proposal_md(p) in revealed, f"{jp.parent.name}: reveal missing/diverged"
        assert "## Scenario analysis" in revealed, f"{jp.parent.name}: peek section header missing"
        # the standing Recommendation/Target slot is GONE (redundant with the verdict surfaces)
        assert "Recommendation / Target" not in hidden, (
            f"{jp.parent.name}: the retired recommendation slot survived")
        if p.action is not None:
            assert p.lean is not None and p.lean.lower().replace(" ", "-") in (
                "strongly-bearish", "strongly-bullish"), f"{jp.parent.name}: proposal off-mapping"
        if s is not None and s.evidence_balance:
            seen += 1
    assert seen >= 2, "expected >=2 committed dossiers with an evidence_balance"


def test_web_brief_proposal_mirror_static() -> None:
    """(pivot web parity, re-pinned for the 2026-07-21 tier redesign) dossier.js keeps verdict.py's
    frozen 3-row mapping (a mixed lean proposes NOTHING — never a coin-flip) and the ONE shared
    lean parser — but renders NO proposal surface at all: the standing line was retired (user
    decision); the seal/reveal lives in the ledger CLI and the md --show-proposal peek. The header
    meta line is gone too (the document date is the header; process meta lives in Record &
    reproduce). Node-free source pins; the mapping is OUR frozen code, never LLM."""
    src = Path("frontend/views/shared/dossier.js").read_text()
    assert "function deriveProposal" in src
    assert '"strongly-bearish": "AVOID"' in src and '"strongly-bullish": "BUY"' in src
    assert '"mixed": null' in src  # two-sided → NO proposal
    # (review) ONE shared JS lean parser (splitLean) — machineReadHtml + deriveProposal both call it
    assert "function splitLean" in src
    assert src.count(r"[A-Za-z\- ]*?") == 1, "the lean regex must live in ONE parser (splitLean)"
    # (review) Object.hasOwn, not `key in` — `in` walks Object.prototype (a parity break vs Python)
    assert "Object.hasOwn(PROPOSAL_BY_LEAN" in src and "key in PROPOSAL_BY_LEAN" not in src
    # NO proposal surface on the web brief — no slot, no sealed-note, no reveal gate
    assert 'class="brief-proposal"' not in src and "propSlot" not in src
    assert "Machine proposal" not in src
    assert "revealed after your verdict is logged" not in src
    # the old header meta (process telemetry as a subtitle) is gone
    assert "Assembled facts" not in src
    # the NARRATIVE slot (buy-side cover): a logged name leads the narrative column with the
    # analyst's rationale under the THESIS heading (the machine assessment is NEVER titled as a
    # thesis — authorship stays marked); pending names keep the machine read inside the About
    # block; the detail card suppresses its rationale copy so the words appear ONCE
    assert "function thesisBlock" in src
    assert "Thesis — our rationale" in src
    # SINGLE REGISTER (2026-07-22): `rationale` is the one field; `rationalePlain` is retired and
    # must not creep back into any reader path.
    assert "const thesis = v.rationale;" in src
    assert "v.rationalePlain" not in src, "the retired field must not be READ (comments are fine)"
    assert "rationale: false" in src


def test_vrrm_brief_stock_info_panel_present_and_cited() -> None:
    """(Phase-2 e2e) VRRM's committed Brief carries the market-data stock-info line, source-bound
    (via an endnote [n] marker — A2). Presence + citation + CMP-present only — phrasing/value-
    independent so a re-draw of the living artifact can't rot it (values on the frozen fixture)."""
    import pathlib
    import re as _re
    p = pathlib.Path("data/dossiers/VRRM/dossier.json")
    if not p.exists():
        pytest.skip("no committed VRRM dossier.json")
    d = ds.Dossier.model_validate_json(p.read_text())
    if d.mechanical.stock_info is None:
        pytest.skip("VRRM not re-assembled with stock_info yet")
    lines = dr.render_markdown(d).splitlines()
    idx = next((i for i, ln in enumerate(lines) if "**Snapshot:**" in ln), None)
    assert idx is not None, "no Snapshot line in VRRM Brief"
    assert "CMP $" in lines[idx]  # VRRM has committed EOD bars
    assert "CIK" not in lines[idx]  # CIK moved to Record & reproduce (tier redesign)
    md = "\n".join(lines)
    assert "## Record & reproduce" in md and "**Identifiers:** CIK" in md, (
        "the identifier must live in Record & reproduce")
    assert _re.search(r"\[\d+\]", lines[idx]), "snapshot not source-bound (no endnote [n])"


def test_endnotes_complete_on_every_committed_dossier() -> None:
    """(A2) The endnote system is COMPLETE on every committed dossier that loads: ZERO inline ↳
    remain, a single document-end '# Sources' list exists, every [n] marker in the body resolves
    to a Source entry (1..len), and the list is deduped (a repeated source_ref → one). This is the
    safety net that reddens if ANY citation emitter is not routed through _cite / _cite_inline."""
    import pathlib
    import re as _re
    committed = sorted(pathlib.Path("data/dossiers").glob("*/dossier.json"))
    assert len(committed) >= 2, "expected at least MVST + VRRM committed"
    for jp in committed:
        t = jp.parent.name
        # (L4) load must SUCCEED — a corrupt/stale committed dossier fails LOUD here, never a silent
        # `continue` that would shrink coverage invisibly.
        d = ds.Dossier.model_validate_json(jp.read_text())
        lines = dr.render_markdown(d).splitlines()
        assert "↳" not in "\n".join(lines), f"{t}: a stray inline ↳ escaped the endnote registry"
        si = next((i for i, ln in enumerate(lines) if ln == "# Sources"), None)
        srcs = [ln for ln in lines[si:] if _re.match(r"^\[\d+\] `", ln)] if si is not None else []
        # (L4) strip inline-code spans (source_refs + verbatim filing text live in backticks) before
        # the marker scan, so a filing quote like `[123]` can't false-positive as an unresolved [n].
        raw = "\n".join(lines[:si]) if si is not None else "\n".join(lines)
        body = _re.sub(r"`[^`]*`", "", raw)
        referenced = {int(m) for m in _re.findall(r"\[(\d+)\]", body)}
        # (review #4) every Source ENTRY must be cited by an in-body [i] marker (orphan-Sources — an
        # entry with no visible marker; the print-orphan L3 guards). ROBUST: a non-marker bracketed
        # int in free text (a filing "[2024]") only ADDS to `referenced`, never false-fails. A [n]
        # marker is a table index by construction, so n>len is only filing text (no separate check).
        for i in range(1, len(srcs) + 1):
            assert i in referenced, f"{t}: Source [{i}] is listed but never cited in the body"
        refs = [m.group(1) for ln in srcs if (m := _re.match(r"^\[\d+\] `(.*)`$", ln))]
        assert len(refs) == len(set(refs)), f"{t}: duplicate source in the Sources list"


def test_endnote_scope_restores_fallback_after_a_render() -> None:
    """(review #3) @_endnote_scope resets the _ENDNOTES ContextVar after render_markdown, so a
    direct emitter OUTSIDE a render still gets the documented '↳ `ref`' fallback — was a stale '[n]'
    leaking into the leftover table (order-dependent pollution). Fallback holds BEFORE and AFTER a
    render; INSIDE the scope it numbers (proving the scope activates)."""
    import pathlib
    before = dr._cite("CIQ x")
    d = ds.Dossier.model_validate_json(
        sorted(pathlib.Path("data/dossiers").glob("*/dossier.json"))[0].read_text())
    _ = dr.render_markdown(d)
    after = dr._cite("CIQ x")
    assert before == after == "\n  - ↳ `CIQ x`"  # fallback both sides — no [n] leak post-render
    assert dr._endnote_scope(lambda: dr._cite_inline("CIQ y"))() == "[1]"  # scope numbers


def test_web_cite_machinery_static_invariants_no_node() -> None:
    """(review #6/#9/#10) the web cite machinery ships UNVERIFIED when node is absent (the
    node-gated parity tests skip), so pin its structural contracts by source inspection — NODE-FREE:
      #9  the citeMark placeholder is parsed in exactly ONE place (citePlaceholders), called by BOTH
          withEndnotes and auditCitesInline — no second ad-hoc parser that can drift from citeMark;
      #10 no citeMark sits INSIDE a print-excluded <details>…</details> literal (its [n] marker is
          hidden by the print CSS → an orphan Sources entry in a Full PDF — the L3 bug).
    (Behavioural numbering is still checked by the node-gated parity tests when node is present.)

    The machinery now lives in frontend/lib/cites.js (lifted out of dossier.js, which kept it
    private and so forced uw-card.js to hardcode the inline form). #9 therefore pins the LIB; #10
    sweeps EVERY frontend module, because citeMark is now importable anywhere — the orphan-in-print
    mistake is no longer dossier.js's alone to make."""
    import pathlib
    import re as _re
    src = pathlib.Path("frontend/lib/cites.js").read_text()
    # #9 — the placeholder REGEX source exists exactly once (inside citePlaceholders); both call it.
    assert src.count(r'data-ref="([^"]*)">\[\?\]<\/sup>') == 1, "cite regex must live in one place"
    assert src.count("citePlaceholders =") == 1, "citePlaceholders must be defined once"
    assert src.count("citePlaceholders()") >= 2, "withEndnotes + auditCitesInline must both call it"
    # citeMark's EMITTED placeholder matches the parser's expected shape (emitter↔parser contract)
    assert 'class="cite-n" data-ref="${escapeHtml(sourceRef)}">[?]</sup>' in src
    # #10 — THE REAL INVARIANT: a cite's [n] marker and its Sources entry must share PRINT FATE.
    # Print hides a COLLAPSED block (`details:not([open])`) but still prints the enclosing tier's
    # Sources list, so a citeMark inside a <details> that resolves into an OUTER scope orphans its
    # entry — an [n] in the printed list pointing at a marker the reader cannot see.
    #
    # This used to be pinned as the blunter proxy "no citeMark inside <details>, ever". That proxy
    # also forbade the SAFE construction: a block carrying its OWN withEndnotes scope, where marker
    # and list are both inside the details and therefore vanish (or print) together. The uw-card's
    # Inputs block uses exactly that, so the guard now states the invariant instead of the proxy.
    # Strip full-line // comments first — prose mentioning "<details>" is not a real tag.
    for p in sorted(pathlib.Path("frontend").rglob("*.js")):
        text = p.read_text()
        if "citeMark(" not in text:
            continue
        code = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("//"))
        for seg in _re.findall(r"<details\b.*?</details>", code, _re.S):
            if "citeMark(" not in seg and "withEndnotes(" not in seg:
                continue
            assert "withEndnotes(" in seg, (
                f"{p.name}: a citeMark in a <details> resolves into an OUTER Sources list and "
                "orphans its [n] in a collapsed-block print — give the block its own "
                "withEndnotes scope, or cite inline (auditCitesInline)")


def test_self_referential_twin_requires_resolved_period_in_the_name() -> None:
    """(R2) A twin naming the subject itself is suppressed UNLESS the resolved period is in the twin
    NAME ('Microvast (2021–2025 arc)'); a bare self-name ('Microvast Holdings') is suppressed even
    when a year hides in the outcome/fact. A genuine peer twin is never touched."""
    bare = ds.TwinCase(name="Microvast Holdings", outcome="the 2021 SPAC listing de-rated",
                       distinguishing_fact="x", source=syn._UNVERIFIED)
    assert syn._self_referential_twin(bare, "MVST", "Microvast Holdings, Inc.") is True
    arc = ds.TwinCase(name="Microvast (2021–2025 arc)", outcome="de-rated post-SPAC",
                      distinguishing_fact="x", source=syn._UNVERIFIED)
    assert syn._self_referential_twin(arc, "MVST", "Microvast Holdings, Inc.") is False
    peer = ds.TwinCase(name="QuantumScape", outcome="pre-revenue battery peer",
                       distinguishing_fact="x", source=syn._UNVERIFIED)
    assert syn._self_referential_twin(peer, "MVST", "Microvast Holdings, Inc.") is False


def test_leverage_survival_falls_back_to_legacy_liquidity_without_capital_structure() -> None:
    """Back-compat: a pre-E dossier.json (capital_structure absent → None) renders the legacy
    Quality.liquidity_covenant_flags line, not the structured table — never crashes."""
    mech = _minimal_mech()
    assert mech.capital_structure is None
    dossier = ds.Dossier(
        ticker="X", name="X", cik="0", reference_date=date(2026, 7, 3), rank=1,
        mechanical=mech, synthesis=None, caveats=[], qa_flags=[], llm_model=None,
        assembled_at=datetime(2026, 6, 1, 12, 0))
    md = dr.render_markdown(dossier)
    assert "Liquidity / covenant flags" in md
    assert "Capital structure (instruments)" not in md


def test_fresh_capital_structure_renders_table_and_wall_in_place_of_liquidity() -> None:
    """A dossier WITH capital_structure renders the instruments table + maturity wall in the
    Leverage & survival section, replacing the flat liquidity line."""
    mech = _minimal_mech().model_copy(update={"capital_structure": _mvst_capital_structure()})
    dossier = ds.Dossier(
        ticker="X", name="X", cik="0", reference_date=date(2026, 7, 3), rank=1,
        mechanical=mech, synthesis=None, caveats=[], qa_flags=[], llm_model=None,
        assembled_at=datetime(2026, 6, 1, 12, 0))
    md = dr.render_markdown(dossier)
    assert "Live instruments — near-dated" in md and dr._TABLE_MARK in md  # (K1) curated main table
    assert "matured (pre-reference): $25.0M" in md
    assert "Liquidity / covenant flags" not in md


# --- PR F: positioning inputs — EDGAR Form-4 insider activity + FINRA short interest -----------

# One real-shaped Form 4 ownership XML with four non-derivative transactions across the code classes
# the block partitions: open-market P (buy) / S (sell), routine grant A, and 'other' conversion C.
_FORM4_XML = """<?xml version="1.0"?>
<ownershipDocument>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
      <transactionAmounts><transactionShares><value>1000</value></transactionShares>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts><transactionDate><value>2026-06-10</value></transactionDate>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <transactionCoding><transactionCode>S</transactionCode></transactionCoding>
      <transactionAmounts><transactionShares><value>6403</value></transactionShares></transactionAmounts>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <transactionCoding><transactionCode>A</transactionCode></transactionCoding>
      <transactionAmounts><transactionShares><value>15503</value></transactionShares></transactionAmounts>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <transactionCoding><transactionCode>C</transactionCode></transactionCoding>
      <transactionAmounts><transactionShares><value>50000</value></transactionShares></transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

_SI_ROWS: list[dict[str, typing.Any]] = [
    {"settlementDate": "2026-06-15", "currentShortPositionQuantity": 26323600,
     "previousShortPositionQuantity": 21410534, "changePercent": 22.95,
     "daysToCoverQuantity": 6.25},
    {"settlementDate": "2026-05-29", "currentShortPositionQuantity": 21410534,
     "previousShortPositionQuantity": 21608177, "changePercent": -0.91,
     "daysToCoverQuantity": 4.35},
]


class _FakeForm4Http:
    """A fake SEC http: one Form 4's index.json (get_json) + its ownership XML (get_text)."""

    def __init__(self, index: dict[str, typing.Any], xml: str) -> None:
        self._index, self._xml = index, xml

    def get_json(self, url: str, ttl_seconds: float | None = None) -> dict[str, typing.Any]:
        return self._index

    def get_text(self, url: str, ttl_seconds: float | None = None) -> str:
        return self._xml


class _FakeFinra:
    def __init__(self, rows: list[dict[str, typing.Any]]) -> None:
        self._rows = rows

    def post_json(
        self, url: str, *, json_body: dict[str, typing.Any], ttl_seconds: float | None = None
    ) -> list[dict[str, typing.Any]]:
        return self._rows


def _record_with_adv(adv_shares: float | None) -> sdr.DataRecord:
    rec = _min_record(pe=5.0)
    if adv_shares is None:
        return rec
    adv = DataField.present(
        adv_shares, as_of=date(2026, 6, 26), source="EOD", tier=SourceTier.DERIVED)
    return rec.model_copy(
        update={"prices": rec.prices.model_copy(update={"adv_90d_shares": adv})})


def test_insider_activity_partitions_open_market_routine_and_other_codes() -> None:
    """(F1/H5) Form 4 non-derivative codes → PLAIN LABELS: open-market buys/sells drive the counts +
    net shares (net = ΣP − ΣS); grants = the A (award) code; any other code (here a conversion C) is
    LABELED under 'other', never dropped. Sign-descriptors only, source-bound to the latest
    accession."""
    edgar = _FakeEdgar(filings=[Filing(
        cik="0001760689", form="4", filing_date=date(2026, 6, 12),
        accession="0000947871-26-000620", items=[], primary_doc="xslF345X06/ownership.xml")])
    http = _FakeForm4Http({"directory": {"item": [{"name": "ownership.xml"}]}}, _FORM4_XML)
    got = dm._insider_activity(
        typing.cast(EdgarClient, edgar), typing.cast(typing.Any, http),
        "0001760689", date(2026, 7, 3))
    assert got.status is ds.SourceStatus.PRESENT
    # buys 1 · sells 1 · net (1000 − 6403)/1000 = -5.4K · grants A×1 · last 2026-06-12 · other C×1
    assert got.value == ("Open-market buys 1 · sells 1 (net -5.4K sh) · grants 1 · "
                         "last 2026-06-12 · other C×1")
    assert "0000947871-26-000620" in (got.source_ref or "")


def test_insider_activity_fail_loud_when_no_form4_in_window() -> None:
    """(F1) No Form 4s in the trailing 6m → fail-loud UNKNOWN, never a fabricated 'no activity'."""
    got = dm._insider_activity(
        typing.cast(EdgarClient, _FakeEdgar()), typing.cast(typing.Any, _FakeForm4Http({}, "")),
        "0001760689", date(2026, 7, 3))
    assert got.status is ds.SourceStatus.UNKNOWN
    assert "no Form 4" in (got.note or "")


def test_short_interest_block_computes_dtc_against_the_screen_adv() -> None:
    """(F2/H5) Latest FINRA settlement → prior→latest with a rising/falling descriptor + FINRA's
    Δ% + % of shares out (EDGAR XBRL count) + days-to-cover vs the SCREEN 90d ADV (not FINRA's, no
    recompute) + the latest-4 settlements mini-row. Dated; the DTC basis is in the citation."""
    got = dm._short_interest(
        typing.cast(typing.Any, _FakeFinra(_SI_ROWS)), _record_with_adv(4607454.0),
        date(2026, 7, 3), shares_out=333_157_384.0)
    assert got.status is ds.SourceStatus.PRESENT
    assert got.value == (
        "Short interest (FINRA, settle 2026-06-15): 21.4M → 26.3M sh (+22.9%, rising) · "
        "7.9% of shares out (EDGAR XBRL) · DTC 5.7d · "
        "recent: 2026-06-15 26.3M · 2026-05-29 21.4M")
    assert "screen 90d ADV" in (got.source_ref or "")  # DTC basis bound in the citation


def test_short_interest_block_omits_dtc_and_pct_when_inputs_unknown() -> None:
    """(F2/H5) DTC needs the screen ADV and the % needs the EDGAR share count; when either is absent
    the shares/Δ%/trend still render and that leg is honestly omitted (never recomputed)."""
    got = dm._short_interest(
        typing.cast(typing.Any, _FakeFinra(_SI_ROWS)), _record_with_adv(None), date(2026, 7, 3))
    assert got.status is ds.SourceStatus.PRESENT
    assert "21.4M → 26.3M sh (+22.9%, rising)" in (got.value or "")
    assert "DTC" not in (got.value or "") and "of shares out" not in (got.value or "")
    assert "screen 90d ADV unavailable" in (got.source_ref or "")


def test_positioning_strings_are_sign_descriptors_only_no_interpretation() -> None:
    """(H5) The no-conclusion walk EXTENDED to the positioning strings: the insider + short-interest
    lines carry sign-descriptors only (counts, +/-, %, rising/falling) — never interpretive.
    Neither matches the synthesis directional regex, nor an interpretive-token list."""
    edgar = _FakeEdgar(filings=[Filing(
        cik="0001760689", form="4", filing_date=date(2026, 6, 12),
        accession="0000947871-26-000620", items=[], primary_doc="xslF345X06/ownership.xml")])
    http = _FakeForm4Http({"directory": {"item": [{"name": "ownership.xml"}]}}, _FORM4_XML)
    insider = (dm._insider_activity(
        typing.cast(EdgarClient, edgar), typing.cast(typing.Any, http),
        "0001760689", date(2026, 7, 3)).value or "")
    short = (dm._short_interest(
        typing.cast(typing.Any, _FakeFinra(_SI_ROWS)), _record_with_adv(4607454.0),
        date(2026, 7, 3), shares_out=333_157_384.0).value or "")
    interpretive = ("bullish", "bearish", "concerning", "alarming", "squeeze", "conviction",
                    "signal", "worrying", "red flag", "suggests", "implies", "warns")
    for line in (insider, short):
        assert not syn._DIRECTIONAL.search(line), line  # no buy/sell verdict / directional language
        assert not any(t in line.lower() for t in interpretive), line


def test_short_interest_fail_loud_when_no_settlement_on_file() -> None:
    """(F2) No settlement in the window → fail-loud UNKNOWN, never a faked zero."""
    got = dm._short_interest(
        typing.cast(typing.Any, _FakeFinra([])), _record_with_adv(4607454.0), date(2026, 7, 3))
    assert got.status is ds.SourceStatus.UNKNOWN and "no FINRA short-interest" in (got.note or "")


def test_positioning_fields_live_on_the_walked_catalyst_path() -> None:
    """(F) The no-conclusion walk reaches CatalystPath (asserted above); these positioning fields
    are therefore covered by the forbidden-token guard — assert they're actually present + optional
    (so a pre-F dossier.json still validates)."""
    fields = ds.CatalystPath.model_fields
    assert "insider_activity" in fields and "short_interest" in fields
    assert not fields["insider_activity"].is_required()  # optional → pre-F JSON round-trips
    cp = ds.CatalystPath(
        as_of=_u(), horizon_read=_u(), acceleration_read=_u(), cross_name_anchor=_u(),
        guidance_bridge=_u(), revision_events=_u(), consensus_stats=_u())
    assert cp.insider_activity is None and cp.short_interest is None  # default absent


@pytest.mark.network
def test_insider_activity_real_mvst() -> None:
    """(F1/H5, live) MVST's trailing-6m Form 4s — 18 on file incl. 3× on 2026-06-12; grants dominate
    (no open-market buys). Plain-label render; pins the latest accession 0000947871-26-000620."""
    edgar, http = EdgarClient.from_config(), build_sec_http()
    got = dm._insider_activity(edgar, http, "0001760689", date(2026, 7, 3))
    assert got.status is ds.SourceStatus.PRESENT
    assert got.value is not None and got.value.startswith("Open-market buys 0 · sells ")
    assert "grants " in got.value and "last " in got.value
    assert "0000947871-26-000620" in (got.source_ref or "")


# --- PR G: implied expectations (price-inverted, multiples-space) ------------------------------
# MVST-shaped synthetic inputs (values I control; they reproduce the verified real triangle). TEV =
# mcap 423.1 + net debt 199.9 = 623.0 → the identity/peer triangle 82.6 / 48.3 / 43.0.

_IE_CNA = (  # cross_name_anchor: the name's OWN forward-multiple ladder
    "NTM: TEV/REV 1.26 · TEV/EBITDA 7.54 · TEV/EBIT 17.55 | "
    "FY 2026: TEV/REV 1.42 · TEV/EBITDA 10.14 · TEV/EBIT 31.54 | "
    "FY 2027: TEV/REV 1.06 · TEV/EBITDA 4.26 · TEV/EBIT 9.17")
_IE_TM = (  # trading_multiples: peer-median LTM (no prefix) + NTM
    "TEV/Rev: name 1.7 vs peers Low 0.7 / Median 3.2 / Mean 5.8 / High 22; "
    "TEV/EBITDA: name 11.1 vs peers Low 7.9 / Median 14.5 / Mean 18.5 / High 38.4; "
    "NTM TEV/Rev: name 1.25 vs peers Low 1.06 / Median 2.55 / Mean 3.64 / High 13.47; "
    "NTM TEV/EBITDA: name 7.46 vs peers Low 7.63 / Median 12.9 / Mean 43.3 / High 198.12")
_IE_AR = "FY 2026 EBITDA: 129.7 (12m) → 146.5 (6m) → 62.1 (latest); net -52% [3m, 2m n/a]"
# (H7/P8) the Estimates→Trends sheet the DIRECT EBITDA + REVENUE anchors read (latest snapshot) —
# the single source of truth for BOTH metrics, distinct from the TEV÷ladder path.
_IE_TRENDS = [
    ["EBITDA", None, None],
    ["Company Level", "FY 2026", "FY 2027"],
    ["Current", 62.1, 147.7],
    ["3 months ago", 146.5, 150.0],
    ["12 months ago", 129.7, 160.0],
    ["Revenue", None, None],
    ["Company Level", "FY 2026", "FY 2027"],
    ["Current", 440.0, 580.0],
    ["12 months ago", 500.0, 620.0],
]
_IE_GATE = "market caps span $34M–$275.0B (8063x); the name is $423M → HETEROGENEOUS — low comp."
_IE_MCAP_REF = (
    "CIQ Comparable Analysis→Financial Data (name Market Capitalization Latest) · as-of 2026-06-24")
_IE_BRIDGE = "TEV→equity bridge: + cash $126.10M, − total debt $326.00M"


def _iv(bridge: str = "", *, cash: float | None = None,
        debt: float | None = None) -> ds.ImpliedValuation:
    """A minimal ImpliedValuation for the bridge probes: STRUCTURED floats are the load-bearing
    path; the display string is present for the legacy _parse_money fallback (structured absent)."""
    u: ds.Sourced[typing.Any] = ds.Sourced.unknown(note="n/a")
    return ds.ImpliedValuation(
        implied_equity=u, bridge=(ds.Sourced.present(bridge, source_ref="x") if bridge else u),
        bridge_cash=cash, bridge_debt=debt, market_cap=u, comparability_gate=u,
    )


def _ie_inputs(
    *, cna: str = _IE_CNA, tm: str = _IE_TM, ar: str = _IE_AR, market_cap: float = 423.1,
    net_debt: float = 199.9, bridge: str = _IE_BRIDGE,
    trends: _Sheets | None = None,
) -> tuple[ds.PeerComps, ds.CatalystPath, ds.ImpliedValuation, ciq.CiqBundle]:
    pc = ds.PeerComps(
        peer_set=_u(), comparability=ds.Sourced.present(_IE_GATE, source_ref="CIQ FD"),
        trading_multiples=ds.Sourced.present(tm, source_ref="CIQ→Trading Multiples"),
        fundamental_deltas=_u(),
        peer_grid=ds.Sourced.present(
            [ds.PeerRow(name="X", ticker="X", is_name=True, market_cap=market_cap,
                        net_debt=net_debt)],
            source_ref="CIQ FD · as-of 2026-06-24"))
    cp = ds.CatalystPath(
        as_of=ds.Sourced.present("≥2026-05-15", source_ref="CIQ Estimates"),
        horizon_read=_u(), acceleration_read=ds.Sourced.present(ar, source_ref="CIQ→Trends"),
        cross_name_anchor=ds.Sourced.present(cna, source_ref="CIQ Estimates→Multiples"),
        guidance_bridge=_u(), revision_events=_u(), consensus_stats=_u())
    iv = ds.ImpliedValuation(
        implied_equity=_u(),
        bridge=ds.Sourced.present(bridge, source_ref="CIQ→Implied Valuation"),
        market_cap=ds.Sourced.present(market_cap, source_ref=_IE_MCAP_REF),
        comparability_gate=ds.Sourced.present(_IE_GATE, source_ref="CIQ FD"))
    bundle = _est_bundle({"Trends": trends if trends is not None else _IE_TRENDS})
    return pc, cp, iv, bundle


def test_ie_parsers_read_the_assembled_fields() -> None:
    """(G) The parsers cross-reference already-assembled STRINGS (no workbook): the name ladder, the
    peer-median LTM vs NTM (distinguished by the exact segment label), the direct FY26 read, the
    as-of stamp, and the bridge net-debt."""
    assert dm._ie_ladder(_IE_CNA, "NTM", "TEV/EBITDA") == 7.54
    assert dm._ie_ladder(_IE_CNA, "FY 2026", "TEV/EBITDA") == 10.14
    assert dm._ie_peer_median(_IE_TM, "NTM TEV/EBITDA") == 12.9
    assert dm._ie_peer_median(_IE_TM, "TEV/EBITDA") == 14.5  # the LTM one (no 'NTM' prefix)
    assert dm._ie_peer_median(_IE_TM, "TEV/Rev") == 3.2
    assert dm._ie_consensus_latest(_IE_AR, "FY 2026", "EBITDA") == 62.1
    assert dm._ie_asof(_IE_MCAP_REF) == "2026-06-24"
    assert dm._ie_bridge_net_debt(_iv(_IE_BRIDGE, cash=126.1, debt=326.0)) == 199.9


def test_trends_fy_level_reads_the_named_year_latest_snapshot() -> None:
    """(H7) The direct-Trends accessor returns the LATEST snapshot for a SPECIFIC fiscal year — FY26
    AND next-FY FY27 (acceleration_read only reaches the first FY column), and None when the year or
    metric is absent (fail-loud — never a fabricated level)."""
    b = _est_bundle({"Trends": _IE_TRENDS})
    assert cs.trends_fy_level(b, metric="EBITDA", fy_label="FY 2026") == 62.1
    assert cs.trends_fy_level(b, metric="EBITDA", fy_label="FY 2027") == 147.7  # the next-FY column
    assert cs.trends_fy_level(b, metric="EBITDA", fy_label="FY 2028") is None  # absent column
    assert cs.trends_fy_level(b, metric="Revenue", fy_label="FY 2026") == 440.0  # (P8) revenue too
    assert cs.trends_fy_level(b, metric="EBIT", fy_label="FY 2026") is None  # absent metric block


def test_ie_builder_triangle_anchors_and_identity() -> None:
    """(G1/G3/H7/P8) TEV ÷ multiple for the fixed set → the triangle; the two NAME rows are the
    identity; BOTH the EBITDA and REVENUE anchors are the DIRECT Estimates→Trends levels (H7/P8, NOT
    TEV÷ladder — the ladder FY26 lives only in the vintage-guard line); the TEV/Rev † identity row
    still stands in the table; vintage + net-debt gates pass; TEV is DERIVED."""
    ie = dm._implied_expectations(*_ie_inputs())
    assert ie is not None
    assert ie.tev.value == 623.0 and "simple-TEV basis" in (ie.tev.source_ref or "")
    got = {r.label: r.implied_level for r in ie.rows}
    assert got["name NTM TEV/EBITDA"] == 82.6  # 623 / 7.54  (identity ≈ consensus NTM)
    assert got["peer-median NTM TEV/EBITDA"] == 48.3  # 623 / 12.9
    assert got["peer-median LTM TEV/EBITDA"] == 43.0  # 623 / 14.5
    assert got["name NTM TEV/Rev"] == 494.4 and got["peer-median NTM TEV/Rev"] == 244.3
    assert got["peer-median LTM TEV/Rev"] == 194.7
    assert {r.label for r in ie.rows if r.is_identity} == {
        "name NTM TEV/EBITDA", "name NTM TEV/Rev"}
    # (H7) EBITDA anchors = DIRECT Estimates→Trends latest (FY26E 62.1 / FY27E 147.7), NOT ladder;
    # the ladder-derived FY26 ($61.4M) now appears ONLY in the vintage-guard line below.
    assert "FY26E $62.1M · FY27E $147.7M" in (ie.anchors.value or "")
    av = ie.anchors.value or ""
    assert "direct consensus EBITDA" in av and "ladder" not in av
    assert "$61.4M" in ie.coherence_note  # the ladder-derived FY26 lives in the vintage-guard line
    # (P8) REVENUE anchors are now DIRECT Estimates→Trends too (FY26E 440 / FY27E 580), NOT ladder;
    # the TEV/Rev † identity row ($494.4M) still stands in the table above.
    assert ie.rev_anchors is not None
    rv = ie.rev_anchors.value or ""
    assert "FY26E $440.0M · FY27E $580.0M" in rv and "direct consensus Revenue" in rv
    assert "ladder" not in rv
    assert got["name NTM TEV/Rev"] == 494.4  # the † identity row survives in the table
    assert ie.vintage_coherent is True and ie.net_debt_reconciled is True
    assert "vintage-coherent" in ie.coherence_note and "%" not in ie.coherence_note
    assert ie.tev_as_of == "2026-06-24" and ie.multiples_as_of == "2026-05-15"


def test_ie_vintage_incoherent_fires_caveat_and_stamps_both_asofs() -> None:
    """(G5) A STALE multiples vintage — the FY26 forward multiple no longer reproduces the direct
    FY26 EBITDA consensus (residual > 0.10) → the row-caveat fires and BOTH as-ofs are stamped, so a
    TEV / multiples pricing-vintage mismatch can't ship silently (the failure class that made my
    spec's targets stale)."""
    cna = _IE_CNA.replace("FY 2026: TEV/REV 1.42 · TEV/EBITDA 10.14",
                          "FY 2026: TEV/REV 1.42 · TEV/EBITDA 5.00")  # derived FY26 623/5 = 124.6
    ie = dm._implied_expectations(*_ie_inputs(cna=cna))
    assert ie is not None and ie.vintage_coherent is False
    assert "multiple-pricing vintage differs from TEV as-of — re-pull comps" in ie.coherence_note
    assert ie.tev_as_of == "2026-06-24" and ie.multiples_as_of == "2026-05-15"


def test_ie_net_debt_gate_soft_caveats_when_bridge_disagrees() -> None:
    """(condition b) The net_debt input is coherence-gated against the cash/debt bridge; a mismatch
    renders a soft caveat on the TEV source_ref (C3-pattern) rather than silently trusting it."""
    ie = dm._implied_expectations(
        *_ie_inputs(bridge="TEV→equity bridge: + cash $126.10M, − total debt $500.00M"))
    assert ie is not None and ie.net_debt_reconciled is False
    assert "⚠" in (ie.tev.source_ref or "") and "reconcile" in (ie.tev.source_ref or "")


def test_h3_gate_shortref_and_dedupe_unknown_reasons() -> None:
    """(H3) The gate is cited SHORT away from the Peer-comps head (verbatim only there);
    and repeated UNKNOWN fact reasons fold to ONE line with the affected-fields list (no fact
    suppressed). Pins the 99.1-shaped case (3 fields, one reason → 1 line)."""
    assert (dr._gate_shortref("caps span 8063x → HETEROGENEOUS — low comp")
            == "comparability: HETEROGENEOUS (see Peer comps gate)")
    assert dr._gate_shortref("homogeneous peer set") == "homogeneous peer set"  # short → verbatim
    # the G header cites the gate SHORT, never repeating the verbatim gate text
    ie = dm._implied_expectations(*_ie_inputs())
    v = _minimal_mech().valuation.model_copy(update={"implied_expectations": ie})
    g_block = "\n".join(dr._implied_expectations_lines(v))
    assert "comparability: HETEROGENEOUS (see Peer comps gate)" in g_block
    assert "market caps span" not in g_block  # the verbatim gate is NOT repeated at the G header
    # dedupe: 3 fields sharing one reason → a single line naming all three; a lone reason untouched
    lines = [
        "- **Net debt / EBITDA (fwd-adj):** _UNKNOWN_ — adjusted figure not in the 99.1 guidance",
        "- **EV/EBITDA (adjusted, forward):** _UNKNOWN_ — adjusted figure not in the 99.1 guidance",
        "- **Adjusted EPS:** _UNKNOWN_ — adjusted figure not in the 99.1 guidance",
        "- **Solo:** _UNKNOWN_ — a unique reason (kept)",
    ]
    out = dr._dedupe_unknown_reasons(list(lines))
    folded = [ln for ln in out if "99.1" in ln]  # (K6) 3 fields fold to the canonical 99.1 reason
    assert len(folded) == 1  # 3 renders → 1
    assert "Net debt / EBITDA (fwd-adj) · EV/EBITDA (adjusted, forward) · Adjusted EPS" in folded[0]
    assert any("Solo" in ln for ln in out)  # a non-repeated reason is left alone
    assert len(out) == 2  # the two duplicate lines removed


def test_k6_99_1_unknown_reason_renders_once_on_real_mvst() -> None:
    """(K6, pin restated per operator) The 99.1 revised-guidance UNKNOWN REASON folds to exactly ONE
    render (all affected fields named); graph-cohort likewise. Pin: unknown-reason occurrences == 1
    (NOT a grep of '99.1' — the drawdown 8-K's own 'Exhibit 99.1' filing text is legitimate)."""
    import pathlib
    p = pathlib.Path("data/dossiers/MVST/dossier.json")
    if not p.exists():
        pytest.skip("no committed MVST dossier.json")
    md = dr.render_markdown(ds.Dossier.model_validate_json(p.read_text()))
    unk = [ln for ln in md.splitlines()
           if ln.startswith("- **") and "_UNKNOWN_" in ln and "99.1" in ln]
    assert len(unk) == 1, f"99.1 unknown-reason occurrences must be 1, got {len(unk)}"
    assert "Revised guidance" in unk[0] and "FWD-ADJ" in unk[0]  # all affected fields named
    # (declutter) the reason reads plain — no Python list-repr survives anywhere in the render
    # (the repr→plain transform itself is pinned on a frozen string in
    # test_display_transforms_read_plain; MVST's own note never carried one)
    assert "['" not in unk[0]
    # (declutter) the graph-cohort absence renders as ONE plain line, no internal filename
    assert "graph_coverage.json" not in md
    # (buy-side restructure) cohort absence is ONE quiet footnote line, never a labelled fact row
    assert md.count("no supplier/customer cohort mapped") == 1
    assert "Supplier/customer cohort:**" not in md


def test_k1_covenant_value_lead_extracts_the_decision_figure_before_clip() -> None:
    """(K1 generalized · audit-hardened) EVERY curated covenant line leads with its extractable
    VALUE before the ≤120c clip — RIGHT or ABSENT, never wrong. Anchored: a test-anchored cadence, a
    maturity-anchored date, a contiguous 1..k enumeration. Never fabricates. (RC-1.5d: the INTEREST
    lead now composes from structured rate components, NOT a clause re-parse — pinned in
    test_rc15d_interest_lead_composed_from_structure; a bare (label, raw) interest call ⇒ '')."""
    lead = dr._covenant_value_lead
    # happy paths (real MVST shapes)
    assert "~$0.50/sh" in lead("Conversion", "Conversion Rate = two (2) shares per $1.00 principal")
    assert lead("Financial maintenance", "Liquidity as of Friday of each calendar week not less "
                "than $5,000,000.") == "not less than $5,000,000 weekly"
    assert lead("Maturity", '"November 28, 2025" is deleted and replaced with "May 28, 2026".'
                ) == "May 28, 2026"  # the amendment governs, not the deleted date
    # audit-hardened: never present a WRONG value
    assert lead("Maturity", "Commitment Termination Date is March 31, 2025 and the Maturity Date "
                "is December 15, 2027.") == "December 15, 2027"  # P2: maturity-anchored, not first
    assert lead("Events of default", "1. Payment. 2. Covenant. 3. Insolvency. See Section 15."
                ).startswith("3 enumerated")  # P4: 'Section 15.' doesn't inflate the count
    assert lead("Financial maintenance", "not less than $10,000,000, tested as of the last day of "
                "each fiscal quarter, and deliver a 13-week forecast each week."
                ) == "not less than $10,000,000 quarterly"  # P5: the TEST cadence, not the forecast
    # (RC-1.5d) a bare interest call with NO structured term ⇒ no lead (the clause carries it); the
    # fixed-rate lead is now an accepted residual (lapses to the clause) — no '8.25% fixed' compose.
    assert lead("Interest / coupon", "The Notes bear interest at a fixed rate of 8.25%.") == ""
    assert lead("Conversion", "price to be set by the board") == ""  # no fabrication


def test_k3_credit_health_renders_mini_table_or_falls_back() -> None:
    """(K3 · audit T1) Credit health parses the prose into a mini-table (dimension row-label | name
    | peer), scale footnote; header and every data row have the SAME cell count (dimension is the
    ROW LABEL, not a col — else scores shift left). Unparseable → the plain fact, no fab."""
    import types
    lv = types.SimpleNamespace(credit_health=ds.Sourced.present(
        "name Overall/Operational/Solvency/Liquidity 3/3/2/2 (S&P issuer rating unrated); "
        "peer-median O/Op/S/L 2.5/2.5/3/3; scale 1=strongest … 4=weakest (S&P-MI PD model)",
        source_ref="CIQ Credit Health"))
    md = "\n".join(dr._credit_health_lines(typing.cast(typing.Any, lv)))
    assert dr._TABLE_MARK in md and "| Overall | 3 | 2.5 |" in md and "S&P-MI PD model" in md
    tbl = [ln for ln in md.splitlines() if ln.startswith("|") and "---" not in ln]
    assert len({ln.count("|") for ln in tbl}) == 1, "credit-health header/row column mismatch"
    lv2 = types.SimpleNamespace(
        credit_health=ds.Sourced.present("unrated; no panel", source_ref="x"))
    assert dr._TABLE_MARK not in "\n".join(dr._credit_health_lines(typing.cast(typing.Any, lv2)))


def test_audit_appendix_never_drops_relocated_facts() -> None:
    """(audit C1) The capital-structure appendix renders the relocated 8-K/pointer/covenant facts
    even when the instrument PANEL is empty — the old guard dropped them from the surface (in
    neither the curated main NOR the appendix), a nothing-deleted violation."""
    u = ds.Sourced[str].unknown(note="n/a")
    cs = ds.CapitalStructure(
        instruments=u, summary=u, detail_as_of="d",
        maturity_filings=ds.Sourced.present("8-K 2026-05-28 at maturity", source_ref="EDGAR"),
        covenant_pointers=ds.Sourced.present("Credit Agreement exhibit 10.1", source_ref="10-K"),
        covenant_terms=ds.Sourced.present("liquidity not less than $50M weekly", source_ref="8-K"))
    appx = "\n".join(dr._capital_structure_appendix_lines(cs))
    for fact in ("8-K 2026-05-28 at maturity", "Credit Agreement exhibit 10.1", "$50M weekly"):
        assert fact in appx, f"relocated fact dropped from appendix: {fact}"


def test_audit_gfm_cell_sanitizes_pipe_and_newline() -> None:
    """(audit PR68/69) A GFM table cell escapes a literal '|' and collapses newlines — a verbatim E5
    covenant value/quote can carry both, which would otherwise open a spurious column or shatter the
    row across physical lines."""
    assert dr._gfm_cell("a | b") == r"a \| b"
    assert dr._gfm_cell("line1\nline2") == "line1 line2"
    assert dr._gfm_cell("  x\ty\n z ") == "x y z"
    rows = [ds.CovenantTerm(name="Conversion", value=ds.Sourced.present(
        "rate = SOFR | floor\n3%", source_ref="8-K x"))]
    u = ds.Sourced[str].unknown(note="n/a")
    cs = ds.CapitalStructure(
        instruments=ds.Sourced.unknown(note="n/a"), summary=u, detail_as_of="d", maturity_filings=u,
        covenant_pointers=ds.Sourced.present("x", source_ref="e"), covenant_pointer_rows=None,
        covenant_terms=ds.Sourced.present("s", source_ref="f"),
        covenant_term_rows=ds.Sourced.present(rows, source_ref="fenced"))
    row = next(ln for ln in dr._covenant_term_lines(cs) if ln.startswith("| Conversion"))
    assert "\n" not in row  # newline collapsed → the row stays on one physical line
    assert r"\|" in row  # the literal pipe was escaped, not left to open a column
    unescaped_bars = len(re.findall(r"(?<!\\)\|", row))  # only real column separators
    assert unescaped_bars == 4  # 3 cells (label + value + source) → 4 separators


def test_audit_dedupe_only_folds_distinctive_not_generic_reasons() -> None:
    """(audit PR68/69) The cross-section reason-fold is limited to DISTINCTIVE reasons (≥30). A
    SHORT generic reason shared by two UNRELATED fields is NOT folded — it must not relocate a fact
    under another section's header."""
    short = ["- **Field A:** _UNKNOWN_ — no XBRL data",
             "- **Field B:** _UNKNOWN_ — no XBRL data"]
    assert dr._dedupe_unknown_reasons(list(short)) == short  # short generic → untouched
    reason = "the adjusted covenant figure is absent from the parsed 99.1 revised guidance"
    assert len(reason) >= dr._DEDUPE_MIN_REASON_LEN
    longl = [f"- **Field A:** _UNKNOWN_ — {reason}", f"- **Field B:** _UNKNOWN_ — {reason}"]
    out = dr._dedupe_unknown_reasons(list(longl))
    assert len(out) == 1 and "Field A · Field B" in out[0]  # distinctive → folded


def test_audit_ie_anchors_unknown_renders_note_not_the_word_none() -> None:
    """(audit PR68/69) H7 made EBITDA anchors UNKNOWN-able (Trends may lack FY26/FY27); the render
    shows the NOTE, never the bare word 'None' (a raw {value} on an UNKNOWN Sourced)."""
    assert (dr._sourced_str(ds.Sourced.unknown(note="no direct FY26/FY27 EBITDA consensus"))
            == "no direct FY26/FY27 EBITDA consensus")
    assert dr._sourced_str(ds.Sourced.present("FY26E $62.1M", source_ref="T")) == "FY26E $62.1M"
    ie = dm._implied_expectations(*_ie_inputs())
    assert ie is not None
    ie2 = ie.model_copy(update={
        "anchors": ds.Sourced[str].unknown(note="no direct FY26/FY27 EBITDA in Trends")})
    v = _minimal_mech().valuation.model_copy(update={"implied_expectations": ie2})
    block = "\n".join(dr._implied_expectations_lines(v))
    assert "difference):** None" not in block  # the bug: bare 'None' rendered
    assert "no direct FY26/FY27 EBITDA in Trends" in block  # the note is shown instead


def test_ie_nm_or_negative_multiple_renders_unknown_not_a_synthetic_level() -> None:
    """(G3) An NM / non-positive multiple → the row is UNKNOWN with a reason; division is guarded,
    never a fabricated level and never a synthetic multiple."""
    tm = _IE_TM.replace("NTM TEV/EBITDA: name 7.46 vs peers Low 7.63 / Median 12.9",
                        "NTM TEV/EBITDA: name 7.46 vs peers Low 7.63 / Median NM")
    ie = dm._implied_expectations(*_ie_inputs(tm=tm))
    assert ie is not None
    nm_row = next(r for r in ie.rows if r.label == "peer-median NTM TEV/EBITDA")
    assert nm_row.implied_level is None and nm_row.note
    cna = _IE_CNA.replace("TEV/EBITDA 7.54", "TEV/EBITDA -5.00")
    neg = dm._implied_expectations(*_ie_inputs(cna=cna))
    assert neg is not None
    neg_row = next(r for r in neg.rows if r.label == "name NTM TEV/EBITDA")
    assert neg_row.implied_level is None and "non-positive" in (neg_row.note or "")


def test_ie_schema_is_fundamentals_space_only_block_scoped() -> None:
    """(G3) The block's two models carry NO price/equity/value/upside/discount field. The check is
    BLOCK-SCOPED — adding 'value' to the GLOBAL no-conclusion walk would false-flag Sourced.value
    everywhere; here we assert only the two G models' own field names."""
    forbidden = ("price", "equity", "value", "upside", "discount")
    for model in (ds.ImpliedExpectations, ds.ImpliedExpectationRow):
        for fname in model.model_fields:
            assert not any(t in fname.lower() for t in forbidden), f"{model.__name__}.{fname}"


def test_ie_render_table_identity_anchors_and_zero_percent_tokens() -> None:
    """(G2) The shared table renders (identity † marked), the consensus anchors juxtaposed, both
    as-ofs stamped — and ZERO percentage / value-space tokens anywhere in the block (the gate is
    rendered verbatim, so it's excluded from the fence scan)."""
    ie = dm._implied_expectations(*_ie_inputs())
    v = _minimal_mech().valuation.model_copy(update={"implied_expectations": ie})
    block = "\n".join(dr._implied_expectations_lines(v))
    assert dr._TABLE_MARK in block
    assert "$82.6M EBITDA †" in block and "$48.3M EBITDA" in block
    assert "Consensus path anchors (EBITDA" in block and "FY26E $62.1M" in block  # H7 direct
    # (P8) the revenue anchors are direct Trends too (FY26E 440), no longer the ladder NTM identity
    assert "Consensus path anchors (Revenue" in block and "FY26E $440.0M" in block
    assert "TEV as-of 2026-06-24 · multiples as-of 2026-05-15" in block
    # REGRESSION (the audit bug): every table row must have the SAME cell count as the header row —
    # `_table` prepends a blank label column, so a 2-cell row under a 2-col header put the implied
    # level under the WRONG header. Header cells == data cells for every '|' row.
    table_rows = [ln for ln in block.splitlines() if ln.startswith("|") and "---" not in ln]
    counts = {ln.count("|") for ln in table_rows}
    assert len(counts) == 1, f"table column mismatch — cell counts differ across rows: {counts}"
    assert "| **name NTM TEV/EBITDA** | **7.54x** | **$82.6M EBITDA †** |" in block  # 3 cells
    body = block.replace(ie.heterogeneity_gate, "<GATE>")  # gate is verbatim, excluded from fence
    assert "%" not in body
    assert not re.search(r"\bupside\b|\bdiscount\b|\bimplied price\b|\bequity value\b|\bgap\b",
                         body, re.IGNORECASE)


def test_ie_flows_into_synthesis_trace_universe() -> None:
    """(G4) The block rides the full mech dump into BOTH the synthesis input and the number-trace
    universe — no synthesis code change. Its implied levels + derived TEV are traceable auto,
    so an LLM citing them isn't false-flagged as untraceable."""
    ie = dm._implied_expectations(*_ie_inputs())
    mech = _minimal_mech()
    mech = mech.model_copy(
        update={"valuation": mech.valuation.model_copy(update={"implied_expectations": ie})})
    nums = syn._floats(mech.model_dump_json())
    assert 82.6 in nums and 623.0 in nums  # implied EBITDA level + the derived TEV are traceable


def test_ie_absent_for_pre_g_valuation_and_when_market_cap_missing() -> None:
    """Back-compat + fail-soft: a pre-G Valuation (no implied_expectations) renders nothing; the
    builder returns None when market cap is absent (TEV underivable) — never a fabricated TEV."""
    assert dr._implied_expectations_lines(_minimal_mech().valuation) == []
    pc, cp, iv, bundle = _ie_inputs()
    assert dm._implied_expectations(
        pc, cp, iv.model_copy(update={"market_cap": _u()}), bundle) is None


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
    # lean concentration view: %-only mix (largest first) — no absolutes/total, no inline period
    assert (segs.value or "") == "Commercial Services 51%; Government Solutions 49%"
    assert "797" not in (segs.value or "") and "[" not in (segs.value or "")
    assert "Dec-31-2025" in (segs.source_ref or "")  # the as-of period rides the citation


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


def test_range_position_thin_sample_flags_low_confidence() -> None:
    """A handful of quarterly closes (post-drawdown, <2y) → the floor VERDICT is suppressed and the
    line reads LOW-CONFIDENCE, but the current multiple + trailing RANGE are still shown (the
    analyst's 'floor %ile of 4 closes adds little' — a floor read on 3 points is unreliable)."""
    mult: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44377.0, 44469.0, 44561.0, 44651.0],
        ["TEV/LTM EBITDA", "Close", 20.0, 18.0, 16.0, 10.0],  # history [20,18,16]; current 10.0
    ]
    rp = cs.range_position(_fin_bundle({"Multiples": mult}))
    assert rp.status is ds.SourceStatus.PRESENT
    v = rp.value or ""
    assert "LOW-CONFIDENCE" in v and "3 closes" in v  # 3 historical closes < 8q ≈ 2y
    assert "trailing range 16.0" in v and "median 18.0x" in v  # range gives the %ile its context
    assert "near-floor" not in v  # the tautological floor verdict is suppressed on a thin sample


def test_range_position_rich_sample_shows_band_and_range() -> None:
    """With ≥2y of closes the floor band IS a meaningful verdict — shown alongside the range."""
    mult: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44000.0, 44100.0, 44200.0, 44300.0, 44400.0, 44500.0,
         44600.0, 44700.0, 44800.0],
        ["TEV/LTM EBITDA", "Close", 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0, 16.0, 8.0],
    ]
    v = (cs.range_position(_fin_bundle({"Multiples": mult})).value) or ""
    assert "8 closes" in v and "near-floor" in v  # 8 historical closes ≥ 8q → the band is trusted
    assert "trailing range 16.0" in v and "30.0x" in v and "median 23.0x" in v
    assert "LOW-CONFIDENCE" not in v


def test_cross_sectional_valuation_name_vs_peer_median() -> None:
    """The Valuation LEAD — the fund's edge: name EV/EBITDA & P/E vs the peer MEDIAN with the
    discount, NUMBERS ONLY — no fixed earned-vs-residual framing tail (that lives in Peer comps;
    repeating it on every dossier is boilerplate). (L1) the peer median is SELF-COMPUTED from the
    per-peer rows (verifiable, agreeing with the grid footer), NOT CIQ's opaque summary 'Median'
    row: the fixture's CIQ Median (10.8/16.4) is set DIFFERENT from the peer median (14/22) to
    prove we use the peer rows."""
    tm: list[list[typing.Any]] = [
        ["Company Name", "TEV/Rev", "TEV/EBITDA", "", "P/E", "", "NTM TEV/Rev", "NTM TEV/EBITDA",
         "NTM P/E"],
        ["Peer A (X:A)", 3.0, 12.0, "", 20.0, "", 2.5, 10.0, 18.0],
        ["Peer B (X:B)", 4.0, 16.0, "", 24.0, "", 3.5, 14.0, 22.0],
        ["", "", "", "", "", "", "", "", ""],
        ["Target Co (X:TGT)", 2.0, 7.5, "", 13.0, "", 1.8, 6.5, 11.0],
        ["Summary Statistics", "", "", "", "", "", "", "", ""],
        ["Low", 2.0, 7.5, "", 13.0, "", 1.8, 6.5, 11.0],
        ["Median", 3.0, 10.8, "", 16.4, "", 2.5, 9.5, 18.0],
        ["High", 4.0, 16.0, "", 24.0, "", 3.5, 14.0, 22.0],
    ]
    bundle = _FakeCompsBundle({("comps", "Trading Multiples"): tm})
    cx = cs.cross_sectional_valuation(typing.cast(ciq.CiqBundle, bundle))
    assert cx.status is ds.SourceStatus.PRESENT
    v = cx.value or ""
    assert "EV/EBITDA 7.5x vs peer median 14.0x (-46%)" in v  # median([12,16]), NOT CIQ's 10.8 row
    assert "P/E 13x vs peer median 22.0x (-41%)" in v  # median([20,24]), NOT CIQ's 16.4 row
    # numbers only — the repetitive earned-vs-residual framing tail is dropped (lives in Peer comps)
    assert "EARNED" not in v and "RESIDUAL" not in v and "see Peer comps" not in v


def test_comps_ev_ebitda_reads_target_tev_ebitda() -> None:
    """The name's LTM TEV/EBITDA from the comps Trading-Multiples target row (col 2), as a value —
    the input the reconciliation compares against the Financials→Multiples TEV/LTM."""
    tm: list[list[typing.Any]] = [
        ["Company Name", "TEV/Rev", "TEV/EBITDA", "", "P/E", "", "NTM TEV/Rev", "NTM TEV/EBITDA",
         "NTM P/E"],
        ["Peer A (X:A)", 3.0, 12.0, "", 20.0, "", 2.5, 10.0, 18.0],
        ["", "", "", "", "", "", "", "", ""],
        ["Target Co (X:TGT)", 2.0, 7.5, "", 13.0, "", 1.8, 6.5, 11.0],
        ["Summary Statistics", "", "", "", "", "", "", "", ""],
        ["Median", 3.0, 10.8, "", 16.4, "", 2.5, 9.5, 18.0],
    ]
    bundle = _FakeCompsBundle({("comps", "Trading Multiples"): tm})
    r = cs.comps_ev_ebitda(typing.cast(ciq.CiqBundle, bundle))
    assert r.status is ds.SourceStatus.PRESENT and r.value == pytest.approx(7.5)


def test_comps_layout_matches_subject_by_ticker() -> None:
    """The MVST failure mode: a no-ticker peer breaks the contiguous block, so the OLD positional
    'first company row after a gap' heuristic pinned the WRONG company (Samsung SDI) as the subject
    and dropped the real name. The subject must instead be matched by the bundle ticker in the col-0
    '(EXCH:SYMBOL)' paren; the mis-pick becomes an ordinary peer; the real name's numbers render."""
    tm: list[list[typing.Any]] = [
        ["Company Name", "TEV/Rev", "TEV/EBITDA", "", "P/E"],
        ["Peer One (X:P1)", 3.0, 12.0, "", 20.0],
        ["Peer Two (X:P2)", 4.0, 13.0, "", 22.0],
        ["Proterra Inc.", "", "", "", ""],          # no-ticker peer → false positional gap
        ["Wrong Pick (X:WRONG)", 9.0, 38.4, "", 50.0],  # what the old heuristic picked as subject
        ["Subject Co (X:SUBJ)", 2.0, 11.1, "", 13.0],   # the REAL subject — CIQ places it last
        ["Summary Statistics", "", "", "", ""],
        ["Median", 3.5, 12.5, "", 21.0],
    ]
    # ticker match → the real subject (row 5), NOT the positional first-after-gap (row 4)
    _hdr, peers, tgt = cs._comps_layout(tm, "SUBJ")
    assert tgt is not None and "Subject Co" in str(tm[tgt][0])
    assert 4 in peers  # the old mis-pick is now an ordinary peer, not the subject
    # the subject's OWN multiple renders (11.1x), never the mis-picked 38.4x
    bundle = _FakeCompsBundle({("comps", "Trading Multiples"): tm}, ticker="SUBJ")
    ev = cs.comps_ev_ebitda(typing.cast(ciq.CiqBundle, bundle))
    assert ev.status is ds.SourceStatus.PRESENT and ev.value == pytest.approx(11.1)
    xs = cs.cross_sectional_valuation(typing.cast(ciq.CiqBundle, bundle)).value or ""
    assert "EV/EBITDA 11.1x" in xs and "38.4x" not in xs
    # fallback: an unknown ticker still resolves to the LAST company row (CIQ convention)
    _h, _p, tgt2 = cs._comps_layout(tm, "NOTHERE")
    assert tgt2 is not None and "Subject Co" in str(tm[tgt2][0])


def test_ev_ebitda_asof_returns_latest_dated_close() -> None:
    """``ev_ebitda_asof`` reports the DATE of the latest TEV/LTM EBITDA Close — the input the
    stale-price check compares against the reference date."""
    mult: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44377.0, 44469.0, 44561.0],  # 2021-06-30, 09-30, 12-31
        ["TEV/LTM EBITDA", "Close", 20.0, 18.0, 10.0],
    ]
    assert cs.ev_ebitda_asof(_fin_bundle({"Multiples": mult})) == date(2021, 12, 31)


def test_range_position_renders_asof_date() -> None:
    """The own-history range carries the DATE its 'current' multiple is priced at — so a stale Close
    (the VRRM case) is visible in the line, not read as today's multiple."""
    mult: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44377.0, 44469.0, 44561.0, 44651.0],
        ["TEV/LTM EBITDA", "Close", 20.0, 18.0, 16.0, 10.0],
    ]
    v = cs.range_position(_fin_bundle({"Multiples": mult})).value or ""
    assert "as-of 2022-03-31" in v  # 44651.0 → 2022-03-31, the latest Close date


def test_own_history_bands_structured_current_vs_trailing() -> None:
    """(P3, #105) The STRUCTURED own-history bands the multiple-band chart consumes — current vs the
    TRAILING low/median/high (current EXCLUDED) + percentile + n_closes, for EV/EBITDA and P/E.
    Shares _own_history_band with range_position's string, so the two can't drift."""
    mult: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44000.0, 44100.0, 44200.0, 44300.0, 44400.0],
        ["TEV/LTM EBITDA", "Close", 30.0, 28.0, 26.0, 24.0, 10.0],
        ["P/LTM EPS", "Close", 40.0, 38.0, 36.0, 34.0, 20.0],
    ]
    s = cs.own_history_bands(_fin_bundle({"Multiples": mult}))
    assert s.status is ds.SourceStatus.PRESENT
    band = {b.metric: b for b in (s.value or [])}
    assert set(band) == {"EV/EBITDA (TEV/LTM)", "P/LTM EPS"}
    ev = band["EV/EBITDA (TEV/LTM)"]
    # current 10 EXCLUDED from the [30,28,26,24] history → low 24 / high 30 / median 27
    assert (ev.current, ev.low, ev.high, ev.median) == (10.0, 24.0, 30.0, 27.0)
    assert (ev.percentile, ev.n_closes) == (0.0, 4)  # current below the entire trailing range
    # (Phase-3b line chart) mean of history + the FULL (date, multiple) close path — current is the
    # LAST series point; mean/min/max are over history (current excluded), like low/high.
    assert ev.mean == 27.0  # mean([30, 28, 26, 24])
    assert [v for _, v in ev.series] == [30.0, 28.0, 26.0, 24.0, 10.0]  # full path, current last
    assert ev.series[-1][1] == ev.current and len(ev.series) == ev.n_closes + 1


def test_own_history_bands_skip_thin_metric_and_unknown_when_none() -> None:
    """(P3, #105) A metric with <4 closes is SKIPPED (not fabricated); a P/E-only ≥4 band still
    renders (that name's sole own-history surface); no metric ≥4 → UNKNOWN, never an empty chart."""
    mixed: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44000.0, 44100.0, 44200.0, 44300.0],
        ["TEV/LTM EBITDA", "Close", 30.0, 28.0, 26.0, ""],  # 3 closes → skipped
        ["P/LTM EPS", "Close", 40.0, 38.0, 36.0, 20.0],  # 4 closes → the only band
    ]
    s = cs.own_history_bands(_fin_bundle({"Multiples": mixed}))
    assert s.status is ds.SourceStatus.PRESENT
    assert [b.metric for b in (s.value or [])] == ["P/LTM EPS"]  # EV/EBITDA thin → skipped
    thin: list[list[typing.Any]] = [
        ["For Quarter Ending", "", 44000.0, 44100.0, 44200.0],
        ["TEV/LTM EBITDA", "Close", 30.0, 28.0, 26.0],
        ["P/LTM EPS", "Close", 40.0, 38.0, 36.0],
    ]
    assert cs.own_history_bands(_fin_bundle({"Multiples": thin})).status is ds.SourceStatus.UNKNOWN


def test_roic_trend_structured_series_preserves_fraction() -> None:
    """(P3, #105) The STRUCTURED per-period ROIC series the ROIC chart consumes — the RAW FRACTION
    (0.05, not 5.0); the chart applies ×100 once. Shares _trajectory_series with the trajectory
    string. <2 points or a missing row → UNKNOWN, never a one-point 'trend'."""
    rat: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2022", "12 months Dec-31-2023",
         "12 months Dec-31-2024"],
        ["Return on Capital %", 0.05, 0.08, 0.11],
    ]
    s = cs.roic_trend(_fin_bundle({"Ratios": rat}, "annual"))
    assert s.status is ds.SourceStatus.PRESENT
    assert [p.value for p in (s.value or [])] == [0.05, 0.08, 0.11]  # RAW fractions, not ×100
    assert all("202" in p.period for p in (s.value or []))  # period carries its fiscal year
    unk = ds.SourceStatus.UNKNOWN
    no_roic: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2022", "12 months Dec-31-2023"],
        ["Return on Assets %", 0.03, 0.04],
    ]
    assert cs.roic_trend(_fin_bundle({"Ratios": no_roic}, "annual")).status is unk
    single: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2022"], ["Return on Capital %", 0.05],
    ]
    assert cs.roic_trend(_fin_bundle({"Ratios": single}, "annual")).status is unk


def test_return_ratios_fintable_structured_and_fail_honest() -> None:
    """(P4) The per-period return-ratio FinTable the exhibit + YoY table consume. The three
    return-ratio rows carry structured `values` (RAW fractions — chart applies ×100); the x-ratios
    are display-only (empty `values`); dividend NA → 'none'. is_estimate all-False (ACTUALS ONLY, no
    consensus splice). A missing row is omitted (never a guessed 0); no header, or no return-ratio
    row at all, → UNKNOWN (a table with only x-ratios is not a return-ratio exhibit)."""
    rat: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2023", "12 months Dec-31-2024",
         "LTM 12 months Mar-31-2025"],
        ["Return on Equity %", -0.18, -0.41, -0.09],
        ["Return on Capital %", -0.087, -0.021, 0.015],
        ["Return on Assets %", -0.065, -0.016, 0.012],
        ["Total Debt/Equity", 0.36, 0.85, 0.70],
        ["Current Ratio", 1.05, 1.30, 0.96],
        ["Dividend per Share", "NA", "NA", "NA"],
    ]
    s = cs.return_ratios(_fin_bundle({"Ratios": rat}, "annual"))
    assert s.status is ds.SourceStatus.PRESENT and s.value is not None
    t = s.value
    assert t.columns == ["FY23", "FY24", "LTM"]
    assert t.is_estimate == [False, False, False]  # ACTUALS ONLY — no consensus splice
    rows = {r.label: r for r in t.rows}
    # return ratios: RAW fractions in `values` (chart ×100 once), formatted % in `cells`
    assert rows["RoE %"].values == [-0.18, -0.41, -0.09]
    assert rows["RoE %"].cells == ["-18.0%", "-41.0%", "-9.0%"]
    assert rows["RoCE %"].values[-1] == 0.015 and rows["RoA %"].values[-1] == 0.012
    # x-ratios: display-only (NOT charted) → cells but empty `values`; dividend NA → "none"
    assert rows["Total debt/equity"].cells == ["0.36x", "0.85x", "0.70x"]
    assert rows["Total debt/equity"].values == []
    assert rows["Dividend/sh"].cells == ["none", "none", "none"]
    unk = ds.SourceStatus.UNKNOWN
    no_hdr: list[list[typing.Any]] = [["Return on Equity %", -0.1, -0.2]]
    assert cs.return_ratios(_fin_bundle({"Ratios": no_hdr}, "annual")).status is unk  # no header
    x_only: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2023", "12 months Dec-31-2024"],
        ["Total Debt/Equity", 0.3, 0.4],
    ]
    assert cs.return_ratios(_fin_bundle({"Ratios": x_only}, "annual")).status is unk  # no returns


def test_return_ratios_committed_reconciles_and_actuals_only() -> None:
    """(P4 e2e) Every committed dossier that carries a return_ratios series: ACTUALS-ONLY
    (is_estimate all-False — the guardrail against splicing the different-basis Estimates ROE/ROA),
    return-ratio rows column-aligned, and the LATEST column RECONCILES with the key_ratios latest
    string (both read the same CIQ column, so a divergence would mean a fabricated series)."""
    import pathlib
    import re as _re
    seen = 0
    for jp in sorted(pathlib.Path("data/dossiers").glob("*/dossier.json")):
        d = ds.Dossier.model_validate_json(jp.read_text())
        rr = d.mechanical.return_ratios
        if rr is None or rr.status is not ds.SourceStatus.PRESENT or rr.value is None:
            continue
        seen += 1
        t = rr.value
        assert t.is_estimate == [False] * len(t.columns), f"{jp.parent.name}: an E column snuck in"
        rows = {r.label: r for r in t.rows}
        assert any(k in rows for k in ("RoE %", "RoCE %", "RoA %")), f"{jp.parent.name}: no row"
        for lbl in ("RoE %", "RoCE %", "RoA %"):
            if lbl in rows:
                assert len(rows[lbl].values) == len(t.columns), f"{jp.parent.name}: {lbl} unaligned"
        kr = d.mechanical.key_ratios
        if kr is not None and kr.status is ds.SourceStatus.PRESENT and kr.value:
            for lbl, tag in (("RoE %", "RoE"), ("RoCE %", "RoCE"), ("RoA %", "RoA")):
                latest = rows[lbl].cells[-1] if lbl in rows else "—"
                m = _re.search(rf"{tag} (-?\d+\.\d+%)", kr.value)
                if m and latest != "—":
                    assert latest == m.group(1), f"{jp.parent.name}: {tag} {latest}!={m.group(1)}"
    assert seen >= 5, "expected the return-ratio series on most committed dossiers"


def test_return_ratios_render_replaces_key_ratios_fact() -> None:
    """(P4) In a committed dossier WITH the series, the markdown renders the per-period YoY table
    and DROPS the latest-only 'Key ratios (latest)' fact (the web adds the line panels above it). A
    name WITHOUT the series keeps the latest-period fallback — never a blank."""
    import pathlib
    p = pathlib.Path("data/dossiers/MVST/dossier.json")
    if not p.exists():
        pytest.skip("no committed MVST dossier.json")
    d = ds.Dossier.model_validate_json(p.read_text())
    rr = d.mechanical.return_ratios
    if rr is None or rr.status is not ds.SourceStatus.PRESENT:
        pytest.skip("MVST not re-derived with return_ratios yet")
    md = dr.render_markdown(d)
    assert "Return ratios — per fiscal period" in md
    assert "**Key ratios (latest):**" not in md  # subsumed by the per-period table
    assert "| RoE % |" in md  # the table carries the return-ratio rows


def test_return_ratios_exhibit_two_panel_static_no_node() -> None:
    """(P4) dossier.js's return-ratios exhibit ships node-unverified, so pin its contracts by source
    inspection — NODE-FREE: it exists, splits into TWO scale-grouped panels (RoE | RoCE + RoA),
    consumes the structured `values` (×100, never a cell re-parse), and financialSnapshot renders it
    in place of the old latest-only 'Key ratios' fact with a fail-honest fallback."""
    src = Path("frontend/views/shared/dossier.js").read_text()
    assert "function returnRatiosExhibit" in src
    # two panels grouped by SCALE — RoE on its own axis, RoCE + RoA sharing one
    assert 'panel(roeS, 44, 366, "RoE %")' in src and 'panel(capS, 412, 748, "RoCE · RoA %")' in src
    assert 'pts("RoE %")' in src and "v * 100" in src  # structured values, ×100 (no re-parse)
    # references the SHARED EXHIBIT frame (lib/exhibit.js), not its own canvas/fonts — so the
    # Financial-Snapshot exhibits stay one visual system (see test_exhibit_shared_frame_tokens).
    assert "= EXHIBIT, n = cols.length" in src  # destructures the shared frame
    # wired into the snapshot as the replacement for the latest-only fact, with a fallback
    assert "returnRatiosExhibit(rr)" in src
    assert 'finTable("Return ratios — per fiscal period", rr)' in src
    assert 'fact("Key ratios (latest)", m.key_ratios)' in src  # fail-honest fallback retained


def test_exhibit_shared_frame_tokens_no_node() -> None:
    """(P4) The shared EXHIBIT design frame (lib/exhibit.js) is the ONE source for canvas / y-band /
    typography the dossier's panel exhibits reference, so their size/padding/spacing/labelling are
    identical by construction (not hand-matched). Pin the token values AND that revEbitda + return-
    ratios + own-history ALL DESTRUCTURE it rather than re-declaring their own literals (the drift
    that made them look different). NODE-FREE — the wiring ships unverified when node is absent."""
    ex = Path("frontend/lib/exhibit.js").read_text()
    assert "export const EXHIBIT" in ex
    for tok in ("H: 276", "cy0: 54, cy1: 234", "wSingle: 430, wDual: 760", "title: 15",
                "panel: 11.5", "axis: 10.5", "xlabel: 10", "point: 10", "legend: 11.5"):
        assert tok in ex, f"EXHIBIT frame token missing: {tok}"
    # revEbitda's margin-point labels / haloes / card spacing consume fs.point + halo + margin — pin
    # their VALUES too, so a change can't silently alter revEbitda's byte-identical output (which is
    # otherwise only preview-verified, never regression-pinned). (#110 review)
    assert 'stroke-width="2.8"' in ex  # EXHIBIT.halo
    assert 'margin: "18px 0 16px"' in ex  # EXHIBIT.margin
    src = Path("frontend/views/shared/dossier.js").read_text()
    assert "EXHIBIT } from" in src  # imported alongside the scale/domain primitives
    assert "= EXHIBIT, W = EXHIBIT.wDual, H = EXHIBIT.H" in src  # revEbitda references the frame
    assert "= EXHIBIT, n = cols.length" in src  # returnRatiosExhibit references the frame
    assert "single ? EXHIBIT.wSingle : EXHIBIT.wDual" in src  # ownHistory references the frame
    assert src.count("} = EXHIBIT") >= 3  # all three panel exhibits destructure the shared frame
    # neither re-declares the old per-exhibit canvas literal (the reinvention this centralises)
    assert "const W = 760, H = 276, cy0 = 54, cy1 = 234" not in src
    assert "H = 240, cy0 = 62, cy1 = 214" not in src  # own-history's old per-exhibit frame is gone


# --- Brief stock-performance exhibit (52-week rebased path: name vs IWM) -----------------------
def _perf_bar(iid: str, d: date, c: float) -> typing.Any:
    from vinci.schemas.market import PriceBar
    return PriceBar(
        internal_id=iid, bar_date=d, open=c, high=c, low=c, close=c, volume=1.0, source="t"
    )


def _perf_ident() -> typing.Any:
    return sdr.Identity(
        internal_id="SEC-X-FOO", issuer_id="I", cik="1", ticker="FOO", mic="XNAS",
        exchange="Nasdaq", eod_symbol="FOO", name="Foo Inc.",
    )


def test_stock_performance_rebases_to_100_and_aligns_benchmark(tmp_path: Path) -> None:
    """(Brief) _stock_performance indexes BOTH the name and IWM to 100 at the window start, aligns
    the benchmark to the name's trading days via as-of closes, and reports each series' windowed
    return — the same EOD closes the G2 idio comparison cites (assemble, never conclude). VALUE
    pins on a SYNTHETIC store (a frozen fixture; the committed artifact test asserts invariants)."""
    from datetime import timedelta

    from vinci.store import Store
    ref = date(2026, 7, 6)
    store = Store(tmp_path / "sp.db")
    # name: 50 → 40 → 25 over the window (base 50) → rebased 100, 80, 50; windowed return −50%
    store.write_prices([_perf_bar("SEC-X-FOO", ref - timedelta(days=350), 50.0),
                        _perf_bar("SEC-X-FOO", ref - timedelta(days=100), 40.0),
                        _perf_bar("SEC-X-FOO", ref, 25.0)])
    # IWM under its canonical benchmark id: 200 → 220 → 260 (base 200) → rebased 100, 110, 130; +30%
    store.write_prices([_perf_bar("IDX-IWM", ref - timedelta(days=350), 200.0),
                        _perf_bar("IDX-IWM", ref - timedelta(days=100), 220.0),
                        _perf_bar("IDX-IWM", ref, 260.0)])
    sp = dm._stock_performance(_perf_ident(), store, ref, bench=benchmark_identity("IWM"))
    assert sp is not None
    assert sp.name_symbol == "FOO" and sp.benchmark_symbol == "IWM"
    assert sp.as_of == ref and sp.window_days == 364
    assert [p.name for p in sp.points] == [100.0, 80.0, 50.0]
    assert [p.benchmark for p in sp.points] == [100.0, 110.0, 130.0]
    assert sp.name_return == pytest.approx(-0.5) and sp.benchmark_return == pytest.approx(0.30)
    assert "FOO" in sp.source_ref and "IWM" in sp.source_ref and "rebased to 100" in sp.source_ref


def test_stock_performance_none_under_two_window_bars(tmp_path: Path) -> None:
    """(Brief · fail-loud) A name with <2 bars in the 52w window yields NO exhibit — None on the
    layer, never a fabricated one-point series. Bars OUTSIDE the window don't count."""
    from datetime import timedelta

    from vinci.store import Store
    ref = date(2026, 7, 6)
    store = Store(tmp_path / "sp.db")
    store.write_prices([_perf_bar("SEC-X-FOO", ref, 25.0),  # one in-window bar
                        _perf_bar("SEC-X-FOO", ref - timedelta(days=500), 90.0)])  # pre-window: out
    assert dm._stock_performance(
        _perf_ident(), store, ref, bench=benchmark_identity("IWM")) is None


def test_stock_performance_benchmark_none_when_iwm_absent(tmp_path: Path) -> None:
    """(Brief · fail-loud) With NO IWM bars stored, the name path still renders (rebased to 100) but
    every benchmark point is None and benchmark_return is None — a loud gap, never bridged/faked."""
    from datetime import timedelta

    from vinci.store import Store
    ref = date(2026, 7, 6)
    store = Store(tmp_path / "sp.db")
    store.write_prices([_perf_bar("SEC-X-FOO", ref - timedelta(days=200), 50.0),
                        _perf_bar("SEC-X-FOO", ref, 30.0)])
    sp = dm._stock_performance(_perf_ident(), store, ref, bench=benchmark_identity("IWM"))
    assert sp is not None
    assert [p.name for p in sp.points] == [100.0, 60.0]
    assert all(p.benchmark is None for p in sp.points)
    assert sp.benchmark_return is None


def test_stock_perf_exhibit_static_contract_no_node() -> None:
    """(Brief) dossier.js's stock-performance exhibit ships node-unverified, so pin its contracts by
    source inspection — NODE-FREE: it exists, reuses the shared EXHIBIT design language (fs · halo ·
    margin), draws the name in --accent and the benchmark in --ink-3, indexes to 100 (extent-based
    domain, NOT lineDomain's floor-at-0 which would waste the 0..min band), and reads the structured
    points/returns. It sits in .brief-snap (briefSnapshot renders it below the scalar table)."""
    src = Path("frontend/views/shared/dossier.js").read_text()
    assert "function stockPerfExhibit" in src
    assert "extent, EXHIBIT } from" in src  # extent imported for the index-domain (not floor-at-0)
    assert "const { fs, halo } = EXHIBIT" in src  # shared design language (margin: a fixed
    # 14px top so the sidebar chart shares the Key-figures rhythm — the uniform-padding decision)
    assert 'style="margin:14px 0 0;"' in src
    assert 'nameCol = "var(--accent)", benchCol = "var(--ink-3)"' in src  # the specified colours
    assert "ds-exhibit brief-perf" in src  # the exhibit card class
    assert "sp.name_return" in src and "sp.benchmark_return" in src  # structured, no re-parse
    assert "extent([...nameS, ...benchS])" in src  # index-domain over the flattened series
    assert "stockPerfExhibit(m.stock_performance)" in src  # wired into briefSnapshot
    # the >Source: guard (no inline caption) is enforced globally by
    # test_exhibits_cite_via_endnotes_not_inline_source_caption — this exhibit must not add one.


def test_stock_perf_exhibit_renders_from_committed_cnxc_e2e() -> None:
    """(Brief · TEST-LAYER end-to-end) The committed CNXC dossier.json → the REAL renderDossier →
    the stock-performance exhibit appears in the HTML. A production failure of the render is pinned
    here, not only by source inspection. Phrasing-independent: presence of the chart card + title +
    the rebased-100 aria-label, and ≥2 polylines (name + benchmark) — never an exact coordinate."""
    import json
    import pathlib
    import shutil
    import subprocess
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    if not pathlib.Path("data/dossiers/CNXC/dossier.json").exists():
        pytest.skip("no committed CNXC dossier.json")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const html = renderDossier(JSON.parse(readFileSync("data/dossiers/CNXC/dossier.json")), null);
console.log(JSON.stringify({
  has_card: html.includes("ds-exhibit brief-perf"),
  has_title: html.includes("Stock performance"),
  has_aria: html.includes("rebased to 100"),
  polylines: (html.match(/<polyline/g) || []).length,
}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    res = json.loads(out.stdout)
    assert res["has_card"] and res["has_title"] and res["has_aria"], f"chart missing: {res}"
    assert res["polylines"] >= 2, f"expected name + benchmark polylines, got {res['polylines']}"


def test_stock_performance_committed_cnxc_artifact_invariants() -> None:
    """(Brief · living-artifact) The re-assembled CNXC dossier carries a structurally-valid
    stock_performance: both series start at exactly 100 (the rebase anchor), dates are strictly
    ascending, the name symbol IS the ticker, IWM is the benchmark, and name_return reconciles with
    the last plotted point. Phrasing/value-INDEPENDENT — the exact returns live on the frozen unit
    fixture above, never on the re-drawn artifact (CLAUDE.md TEST-LAYER rule)."""
    import pathlib
    p = pathlib.Path("data/dossiers/CNXC/dossier.json")
    if not p.exists():
        pytest.skip("no committed CNXC dossier.json")
    d = ds.Dossier.model_validate_json(p.read_text())
    sp = d.mechanical.stock_performance
    assert sp is not None and len(sp.points) >= 2
    assert sp.name_symbol == d.ticker and sp.benchmark_symbol == "IWM"
    assert sp.points[0].name == 100.0  # the rebase anchor — always 100 at the window start
    if sp.points[0].benchmark is not None:
        assert sp.points[0].benchmark == 100.0
    dates = [pt.date for pt in sp.points]
    assert dates == sorted(dates) and len(set(dates)) == len(dates)  # strictly ascending, unique
    # reconciles with the last plotted point (which is rounded to 2 dp → allow that rounding slack)
    assert sp.name_return == pytest.approx(sp.points[-1].name / 100.0 - 1.0, abs=1e-3)


def test_own_history_chart_low_confidence_threshold_matches_string() -> None:
    """(P3, #105) The own-history CHART de-escalates its marker below the SAME close count the
    range_position STRING caveats (_MIN_CONFIDENT_CLOSES) — pinned so the thresholds can't drift.
    A chart reading MORE confident than its caveated sibling is exactly the failure this guards."""
    src = Path("frontend/views/shared/dossier.js").read_text()
    m = re.search(r"LOW_CONF_CLOSES = (\d+)", src)
    assert m, "ownHistoryExhibit must define LOW_CONF_CLOSES"
    assert int(m.group(1)) == cs._MIN_CONFIDENT_CLOSES  # JS threshold == the Python string's
    # the de-escalation is wired (neutral marker + '*' tag + footnote) — phrasing-independent
    assert "anyLowConf" in src and "low-confidence" in src.lower()


def test_ev_ebitda_integrity_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Data-integrity flag on the name's current EV/EBITDA. (1) A STALE Financials Close +
    disagreeing comps → a stale-price caveat naming the date, the gap, and which to prefer; the old
    'different EBITDA/EV' wording is gone. (2) A fresh but disagreeing pair → a plain cross-sheet
    gap. (3) A fresh, agreeing pair → nothing. (4) A STALE Close whose staleness an agreeing present
    comps confirms immaterial → SUPPRESSED (the MVST case; the inline as-of date still shows it).
    (5) A stale Close with comps ABSENT → the soft stale caveat still fires (can't cross-check)."""
    ref = date(2026, 6, 22)

    def patch(fin: float | None, comp: float | None, asof: date | None) -> None:
        monkeypatch.setattr(
            cs, "ev_ebitda_current",
            lambda _b: ds.Sourced.present(fin, source_ref="fin") if fin is not None
            else ds.Sourced.unknown(note="no fin"),
        )
        monkeypatch.setattr(
            cs, "comps_ev_ebitda",
            lambda _b: ds.Sourced.present(comp, source_ref="comp") if comp is not None
            else ds.Sourced.unknown(note="no comp"),
        )
        monkeypatch.setattr(cs, "ev_ebitda_asof", lambda _b: asof)

    # (1) stale Close (83d) + disagreeing comps → stale-price caveat, names date/gap/prefer-comps
    patch(8.5, 4.7, date(2026, 3, 31))
    f = dm._ev_ebitda_integrity_flag(None, ref)  # type: ignore[arg-type]
    assert f is not None and "stale-price caveat" in f
    assert "2026-03-31" in f and "83d" in f and "4.7x" in f and "prefer" in f
    assert "EBITDA/EV bases" not in f  # the inaccurate old wording is gone
    # (2) fresh Close but the two sheets disagree → a plain cross-sheet gap (no stale claim)
    patch(12.0, 7.0, date(2026, 6, 18))
    f2 = dm._ev_ebitda_integrity_flag(None, ref)  # type: ignore[arg-type]
    assert f2 is not None and "cross-sheet gap" in f2 and "stale-price caveat" not in f2
    # (3) fresh Close + the two agree → no flag (never a fabricated conflict)
    patch(11.3, 11.1, date(2026, 6, 18))
    assert dm._ev_ebitda_integrity_flag(None, ref) is None  # type: ignore[arg-type]
    # (4) stale Close (83d) but an agreeing present comps → staleness immaterial → SUPPRESSED (MVST)
    patch(10.0, 11.1, date(2026, 3, 31))
    assert dm._ev_ebitda_integrity_flag(None, ref) is None  # type: ignore[arg-type]
    # (5) stale Close with comps ABSENT → can't confirm current → the soft stale caveat still fires
    patch(10.0, None, date(2026, 3, 31))
    f5 = dm._ev_ebitda_integrity_flag(None, ref)  # type: ignore[arg-type]
    assert f5 is not None and "stale-price caveat" in f5 and "prefer" not in f5


def test_flags_partition_routes_qa_from_caveats() -> None:
    """The audience-split: machine-QA self-checks (citation/twin/overstep/LLM-state) route to
    qa_flags (dev/JSON only); decision caveats + the 'pull CIQ …' incomplete-input notes stay in
    caveats. UNTRACEABLE is a DATA-INTEGRITY caveat (a figure mis-cited to STRUCTURED data that
    lacks it — the source_ref looks legit, so the human must see it); TRANSCRIPT-FIGURE stays QA
    (its 'CIQ transcript' source_ref is honest). Unknown flags default to caveat (transparency)."""
    qa = [
        "UNCITED bull_point: '...' (ref not in mechanical facts)",
        "TRANSCRIPT-FIGURE '55' in bear_point: '...' — from the cited earnings call, verify",
        "TWIN 'Acme' source doesn't trace — should be tagged unverified",
        "DIRECTIONAL language 'buy' — human review (dossier frames, not concludes)",
        "VERIFICATION-CLAIM bull_point: '...' — the dossier cites, it does not verify",
        "evidence_balance MISSING — the synthesis must commit a balance read",
        "LLM synthesis failed (no usable output)",
    ]
    caveat_src = [
        "UNTRACEABLE figure '42' in bear_point: '...'",  # data-integrity: mis-cited to structured
        "RESOLVED (P/E basis) — trailing GAAP P/E 5.0x is one-time-distorted: ...",
        "EDGAR P/E (5.0x) conflicts ~3x with CIQ P/LTM EPS (1.7x) — ...",
        "EV/EBITDA stale-price caveat — CIQ's Financials→Multiples current TEV/LTM 8.5x ...",
        "pull CIQ 'Estimates Report' for MVST — consensus set; expected at data/manual/ciq/MVST",
        "SOME-NEW-FLAG bull_point: '...' — a flag the classifier hasn't seen",  # unknown → caveat
    ]
    caveats, qa_flags = dflags.partition(qa + caveat_src)
    assert qa_flags == qa  # every QA self-check routed out of the human view, unchanged
    assert len(caveats) == len(caveat_src)  # every non-QA flag kept for the human
    assert any("pull CIQ 'Estimates Report'" in c for c in caveats)  # incomplete-input visible
    assert any("SOME-NEW-FLAG" in c for c in caveats)  # unknown flag defaults to visible
    assert not any("UNTRACEABLE" in q for q in qa_flags)  # data-integrity is NOT hidden
    unt = next(c for c in caveats if "ntraceable figure 42" in c)  # visible + re-voiced
    assert "UNTRACEABLE" not in unt and "a bear point" in unt


def test_flags_revoice_strips_validator_token_keeps_explanation() -> None:
    """Re-voicing swaps the ALL-CAPS token (and humanises the field name) for a plain lead while
    keeping the post-'—' explanation; already-plain caveats pass through unchanged."""
    raw = (
        "ANCHORS-ON-DISTORTED-P/E bull_point: 'trades at 5x' — the P/E is distorted "
        "(rests on a non-current/non-recurring EPS); don't read it as cheap"
    )
    out = dflags.revoice(raw)
    assert "ANCHORS-ON-DISTORTED-P/E" not in out and "bull_point:" not in out
    assert out.startswith("Distorted-P/E anchor (a bull point):")
    assert "don't read it as cheap" in out  # the load-bearing explanation is retained
    # FALSE-BALANCE? (no {where}) → plain lead; the two-sided detail is kept
    fb = dflags.revoice("FALSE-BALANCE? evidence_balance reads 'mixed' but the split is lopsided")
    assert fb.startswith("Possible false balance —") and "lopsided" in fb
    # an already-plain caveat is untouched
    plain = "EV/EBITDA stale-price caveat — priced at its last Close 2026-03-31"
    assert dflags.revoice(plain) == plain


def test_flags_section_renders_caveats_hides_qa() -> None:
    """The human render shows only d.caveats (re-voiced) under the analyst-caveats heading; the
    machine-QA self-checks in d.qa_flags never reach the human markdown."""
    dossier = ds.Dossier(
        ticker="X", name="X", cik="0", reference_date=date(2026, 6, 1), rank=1,
        mechanical=_minimal_mech(), synthesis=None,
        caveats=["Distorted-P/E anchor (a bull point): 'trades at 5x' — don't read it as cheap"],
        qa_flags=["UNCITED bull_point: '...' (ref not in mechanical facts)"],
        llm_model=None, assembled_at=datetime(2026, 6, 1, 12, 0),
    )
    md = dr.render_markdown(dossier)
    assert "Analyst caveats — verify before the verdict" in md
    assert "Distorted-P/E anchor" in md  # the re-voiced caveat renders
    assert "UNCITED" not in md  # the QA self-check is absent from the human view


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
    assert "Commercial Services 45%" in (rev.value or "")  # revenue share (lean %-only)
    assert eb.status is ds.SourceStatus.PRESENT
    assert "Commercial Services 283 (68%)" in (eb.value or "")  # 282.5/415.9 — profit, not revenue
    assert "Segments (EBITDA" in (eb.source_ref or "")


def test_margin_trend_carries_its_absolute_ebitda_reconciler() -> None:
    """Mechanism A.1: margin_trend pairs the margin % WITH the absolute EBITDA + revenue trajectory
    in the SAME field, so a falling margin % is never presentable without the absolute EBITDA that
    reconciles it (a % can fall while absolute EBITDA RISES — scaling, not deterioration)."""
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
    assert "EBITDA margin:" in v and "37%" in v  # 362/979 ≈ 37% — the margin % trajectory
    # the RECONCILER is INLINE, as its own clean series: absolute EBITDA (306 → 342 → 362) + revenue
    assert "absolute EBITDA:" in v and "306" in v and "362" in v and "absolute revenue:" in v
    assert "(R)" in v  # the reclassified basis is marked
    assert "YoY" not in v  # the quarterly same-quarter YoY stays in the trajectory, not here


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


def test_revised_guidance_updating_verb_matches_and_initial_does_not() -> None:
    """SMPL 2026-04-09 regression (verbatim from Ex-99.1 a991_pressreleasexq2x2026.htm): the
    release's verb is 'updating' — 'revis…' appears nowhere — and the revis-only anchor read a
    PARSED exhibit as no-outlook while the gap card extracted these same figures from the same
    exhibit (an internal contradiction in one committed dossier). 'updat…' now anchors the block.
    The TOP headline ('Updates … Outlook Denver, CO') passes the money+metric test on the RESULTS
    lede behind it — the colon-introduced outlook heading must win over it, so the surfaced block
    is the guidance bullets, not the quarter's results. An INITIAL outlook ('provides…') still
    returns None."""
    smpl = (
        "Updates Fiscal Year 2026 Outlook Denver, CO, April 9, 2026 - The Simply Good Foods "
        "Company today reported financial results: net sales of $301.9 million and Adjusted "
        "EBITDA of $55.5 million for the second quarter. "
        + "The company is taking actions to adapt operations to current demand. " * 12
        + "As a result of its second quarter performance, the Company is updating its previously "
        "provided outlook for fiscal year 2026: Net Sales expected to range between $1.31 to "
        "$1.35 billion, or -10% to -7% year-over-year Gross Margins expected to decline between "
        "300 and 350 basis points year-over-year Adjusted EBITDA expected to range between $217 "
        "to $225 million, or -22% to -19% year-over-year"
    )
    block = dm._extract_revised_guidance(smpl)
    assert block is not None and "$1.31" in block and "$217" in block
    assert "reported financial results" not in block  # the results-lede headline window lost
    initial = (
        "The Company provides its fiscal year 2027 outlook: Net sales expected between $1.40 "
        "and $1.45 billion with Adjusted EBITDA of approximately $230 million."
    )
    assert dm._extract_revised_guidance(initial) is None


def test_revised_guidance_note_honest_and_accessions_deduped(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(1) Two gap-downs sharing ONE 8-K list its accession ONCE (SMPL's committed note listed
    '0001702744-26-000010' twice). (2) A parsed 99.1 with no matching block says the BLOCK did not
    match — never the old 'no … exhibit parsed', which was false whenever a 99.1 WAS parsed.
    (3) With no 99.1 located, the note says located."""
    f = ds.FilingRef(gap_date="2026-04-09", filing_date="2026-04-09", form="8-K", items=["2.02"],
                     item_types=["2.02 Results of Operations"], accession="A-1", url="u",
                     events=[])
    twin = f.model_copy(update={"gap_date": "2026-04-10"})

    class _Http:
        def get_text(self, url: str, ttl_seconds: object = None) -> str:
            return "<p>An earnings call transcript. No outlook discussed.</p>"

    monkeypatch.setattr(dm, "_exhibit_991_url", lambda http, cik, acc: "http://x/ex991.htm")
    got = dm._revised_guidance(_Http(), "1", [f, twin])  # type: ignore[arg-type]
    assert got.status is ds.SourceStatus.UNKNOWN
    note = str(got.note)
    assert "block matched" in note and note.count("A-1") == 1
    assert "exhibit parsed" not in note
    monkeypatch.setattr(dm, "_exhibit_991_url", lambda http, cik, acc: None)
    got2 = dm._revised_guidance(_Http(), "1", [f])  # type: ignore[arg-type]
    assert "no 99.1 exhibit located" in str(got2.note)


def test_ex_991_detector_lives_in_exactly_one_place() -> None:
    """This module used to carry its OWN copy of the Ex-99.1 filename regex, and the two copies
    DRIFTED — the one here never learned the '_' separator class, so it missed 'ex99_1.htm' that
    the other matched. The rule now lives once, in release_parse; mechanical delegates."""
    src = Path("vinci/dossier/mechanical.py").read_text()
    assert "_EX991" not in src, "the duplicate detector must not come back"
    assert "def _is_ex991" not in src
    assert "release_parse.exhibit_991_urls(http, cik, accession)" in src


# --- item 3: render formatters (raw float → legible at render; source value untouched) --------
def test_render_formatters() -> None:
    assert dr._mult(2.861674241263681) == "2.9x"
    assert dr._pctile(0.01036682615629984) == "1st %ile" and dr._pctile(0.0) == "0th %ile"
    assert dr._pct(-0.7263) == "-72.6%"
    assert dr._signword(1) == "positive" and dr._signword(-1) == "negative"


def test_fmt_assembled_stamps_utc_and_flags_legacy_naive() -> None:
    """The assembly stamp carries a TIME so two same-day re-assemblies are distinguishable. A fresh
    UTC-aware build renders with 'UTC' (an offset datetime is converted to UTC first); a naive
    datetime keeps its wall-clock and is honestly labeled '(local)', never a false UTC claim."""
    assert dr._fmt_assembled(datetime(2026, 7, 3, 14, 22, tzinfo=UTC)) == "2026-07-03 14:22 UTC"
    ist = timezone(timedelta(hours=5, minutes=30))
    assert dr._fmt_assembled(datetime(2026, 7, 3, 19, 52, tzinfo=ist)) == "2026-07-03 14:22 UTC"
    assert dr._fmt_assembled(datetime(2026, 7, 3, 14, 22)) == "2026-07-03 14:22 (local)"


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


# --- item 1: adjusted-basis figures parse; the boilerplate GAAP-EPS caveat is now dropped ----
def test_adjusted_guidance_parse_and_eps_caveat_dropped() -> None:
    text = (
        "revising its outlook to: Total Revenue of $985 million to $995 million; Adjusted EBITDA "
        "of $380 million to $385 million; Adjusted EPS of $1.19 to $1.25."
    )
    eb, eps = dm._ADJ_EBITDA.search(text), dm._ADJ_EPS.search(text)
    assert eb is not None and (float(eb.group(1)), float(eb.group(2))) == (380.0, 385.0)
    assert eps is not None and (float(eps.group(1)), float(eps.group(2))) == (1.19, 1.25)
    # the bare 'GAAP EPS understates earnings power' caveat was DROPPED in the flag-noise audit
    # (boilerplate; its only fact, adjusted-EPS-unavailable, already rides in a key_unknown), so it
    # no longer fires whether or not the adjusted basis is resolved.
    rec, empty = _min_record(pe=5.5), ciq.CiqBundle(ticker="VRRM", workbooks=())
    for resolved in (False, True):
        flags = dm._eps_caveat_flags(rec, empty, eps_resolved=resolved)
        assert not any("understates earnings power" in f for f in flags)


def test_ciq_pltm_without_gaap_pe_fires_basis_caveat(monkeypatch: pytest.MonkeyPatch) -> None:
    """SMPL regression: CIQ P/LTM EPS printed 16.0x while LTM GAAP EPS was −2.08 — EDGAR P/E
    absent, the peers row said 'NM' — three EPS readings with no shared basis and no flag. The
    existing conflict check needs BOTH multiples present, so the negative-GAAP-EPS shape slipped
    through. CIQ-present + EDGAR-absent fires the basis caveat — the LTM-GAAP-EPS-UNAVAILABLE
    fallback (c) of the newer sign-keyed (d) guard, so it's called here WITHOUT ``ltm_gaap_eps``; a
    known EDGAR P/E near CIQ stays quiet; CIQ absent stays quiet."""
    bundle = ciq.CiqBundle(ticker="SMPL", workbooks=())
    monkeypatch.setattr(dm.ciq_sheets, "pe_ltm_current",
                        lambda b: ds.Sourced.present(16.0, source_ref="t"))
    rec = _min_record(5.5)
    funds_no_pe = rec.fundamentals.model_copy(update={
        "pe": DataField.unknown(source="x", tier=SourceTier.DERIVED)})
    rec_no_pe = rec.model_copy(update={"fundamentals": funds_no_pe})
    flags = dm._eps_caveat_flags(rec_no_pe, bundle, eps_resolved=False)
    assert any("P/LTM EPS prints 16.0x" in f and "different earnings definition" in f
               for f in flags)
    assert dm._eps_caveat_flags(_min_record(15.0), bundle, eps_resolved=False) == []
    monkeypatch.setattr(dm.ciq_sheets, "pe_ltm_current",
                        lambda b: ds.Sourced.unknown(note="no value"))
    assert dm._eps_caveat_flags(rec_no_pe, bundle, eps_resolved=False) == []


def _fin_summary_ltm_eps(rows: list[ds.FinRow], cols: tuple[str, ...] = ("FY25", "LTM")
                         ) -> ds.FinancialSummary:
    u: ds.Sourced[typing.Any] = ds.Sourced.unknown(note="n/a")
    return ds.FinancialSummary(
        annual=ds.Sourced.present(ds.FinTable(columns=list(cols), rows=rows), source_ref="t"),
        quarterly=u, balance_sheet=u, coherence=u, as_of=u)


def test_ltm_gaap_eps_reads_structured_ltm_column() -> None:
    """``_ltm_gaap_eps`` reads the STRUCTURED ``values`` at the 'LTM' column of the 'EPS (GAAP,
    dil.)' row — never the display ``cells`` (parsers-consume-structured-values). None when the
    table/row/LTM-column/value is absent."""
    eps = ds.FinRow(label="EPS (GAAP, dil.)", cells=["1.02", "(2.08)"], values=[1.02, -2.08])
    assert dm._ltm_gaap_eps(_fin_summary_ltm_eps([eps])) == -2.08
    # values WIN over a divergent display cell (the rule: never parse the rendered string)
    tricky = ds.FinRow(label="EPS (GAAP, dil.)", cells=["1.02", "1.00"], values=[1.02, -2.08])
    assert dm._ltm_gaap_eps(_fin_summary_ltm_eps([tricky])) == -2.08
    # the LTM header may carry a Reclassified '(R)' suffix — prefix-match must still find it
    # (else a reclassified twin silently reintroduces the claim-#7 blind spot)
    assert dm._ltm_gaap_eps(_fin_summary_ltm_eps([eps], cols=("FY25", "LTM (R)"))) == -2.08
    rev = ds.FinRow(label="Revenue ($M)", cells=["1", "2"], values=[1.0, 2.0])
    assert dm._ltm_gaap_eps(_fin_summary_ltm_eps([rev])) is None            # no EPS row
    no_ltm = _fin_summary_ltm_eps([eps], cols=("FY24", "FY25"))             # no LTM column at all
    assert dm._ltm_gaap_eps(no_ltm) is None
    empty = ds.FinRow(label="EPS (GAAP, dil.)", cells=["1.02", "—"], values=[])
    assert dm._ltm_gaap_eps(_fin_summary_ltm_eps([empty])) is None             # no structured value
    unk: ds.Sourced[typing.Any] = ds.Sourced.unknown(note="no ciq")
    assert dm._ltm_gaap_eps(ds.FinancialSummary(
        annual=unk, quarterly=unk, balance_sheet=unk, coherence=unk, as_of=unk)) is None


def test_pltm_basis_caveat_on_negative_ltm_gaap_eps(monkeypatch: pytest.MonkeyPatch) -> None:
    """SMPL claim-#7 — the shape #198's guard MISSED. A POSITIVE trailing P/E multiple shown while
    the LTM GAAP dil EPS is a LOSS: SMPL had EDGAR P/E 10.86x + CIQ P/LTM 16.0x beside LTM GAAP EPS
    −2.08. Both multiples present (so #198's EDGAR-absent (c) never fired) and ANNUAL EPS in line
    (so ``_pe_reconciliation`` stayed quiet). Keyed on the LTM GAAP EPS SIGN, (d) fires naming every
    positive multiple shown; a positive LTM GAAP EPS stays quiet; the (c) fallback survives when the
    sign is UNAVAILABLE, with NO double caveat when it is present."""
    bundle = ciq.CiqBundle(ticker="SMPL", workbooks=())

    def set_ciq(v: float | None) -> None:
        monkeypatch.setattr(dm.ciq_sheets, "pe_ltm_current", lambda b: (
            ds.Sourced.present(v, source_ref="t") if v is not None
            else ds.Sourced.unknown(note="none")))

    def rec_pe(v: float | None) -> sdr.DataRecord:
        r = _min_record(v if v is not None else 5.0)
        if v is None:
            r = r.model_copy(update={"fundamentals": r.fundamentals.model_copy(update={
                "pe": DataField.unknown(source="x", tier=SourceTier.DERIVED)})})
        return r

    # (1) the SMPL shape — EDGAR 10.86 + CIQ 16.0 + LTM GAAP −2.08 → names BOTH multiples
    set_ciq(16.0)
    f1 = dm._eps_caveat_flags(rec_pe(10.86), bundle, eps_resolved=False, ltm_gaap_eps=-2.08)
    assert any("EDGAR P/E 10.9x and CIQ P/LTM EPS 16.0x" in f and "NEGATIVE (-2.08)" in f
               and "do not read them" in f for f in f1)
    # (2) only EDGAR positive (CIQ absent) → names EDGAR only, singular "it"
    set_ciq(None)
    f2 = dm._eps_caveat_flags(rec_pe(10.86), bundle, eps_resolved=False, ltm_gaap_eps=-2.08)
    assert any("EDGAR P/E 10.9x rest" in f and "do not read it" in f and "CIQ" not in f for f in f2)
    # (3) EDGAR absent + CIQ present + negative LTM → (d) names CIQ; NO (c) double
    set_ciq(16.0)
    f3 = dm._eps_caveat_flags(rec_pe(None), bundle, eps_resolved=False, ltm_gaap_eps=-2.08)
    assert any("CIQ P/LTM EPS 16.0x rest" in f and "NEGATIVE (-2.08)" in f for f in f3)
    assert not any("different earnings definition" in f for f in f3)
    # (4) positive LTM GAAP EPS → (d) stays quiet (multiples coherent with a positive GAAP trail)
    f4 = dm._eps_caveat_flags(rec_pe(10.86), bundle, eps_resolved=False, ltm_gaap_eps=1.15)
    assert not any("rest on normalized" in f for f in f4)
    # (5) sign UNAVAILABLE + EDGAR absent + CIQ present → the (c) #198 fallback is preserved
    f5 = dm._eps_caveat_flags(rec_pe(None), bundle, eps_resolved=False, ltm_gaap_eps=None)
    assert any("different earnings definition" in f for f in f5)
    # (6) (b) EDGAR-vs-CIQ conflict (ratio ≥ 2) is SUPPRESSED when GAAP LTM is a known loss — the
    # 'inflated' framing is wrong there and (d) owns it; with the sign UNKNOWN (b) still fires.
    set_ciq(16.0)  # EDGAR 6.0x vs CIQ 16.0x → ratio 2.67 ≥ 2
    b_loss = dm._eps_caveat_flags(rec_pe(6.0), bundle, eps_resolved=False, ltm_gaap_eps=-2.08)
    assert not any("one-time-inflated" in f for f in b_loss)             # (b) yields to (d)
    assert any("rest on normalized" in f for f in b_loss)               # (d) fires instead
    b_unknown = dm._eps_caveat_flags(rec_pe(6.0), bundle, eps_resolved=False, ltm_gaap_eps=None)
    assert any("one-time-inflated" in f for f in b_unknown)             # sign unknown → (b) kept


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
    # lean %-only mix, largest first, no inline period; the geographic block is read (not business)
    assert (geo.value or "") == "United States 86%; Australia 7%"
    assert "Geographic" in (geo.source_ref or "") and "Dec-31-2025" in (geo.source_ref or "")
    # the lone business segment is 436/979 = 45% (rest unlisted) → a share, NOT "single segment"
    assert (cs.segments(b).value or "") == "Commercial Services 45%"


def test_segment_lean_collapse_and_ebitda_stays_detailed() -> None:
    """(concentration) A lone segment/geography at ~100% is tautological ('X val (100%) of Total
    val') → collapses to a plain marker; the '12 months' period is compacted. segment_ebitda is NOT
    leaned — its reconciliation needs the per-segment values, the pre-corporate sum, and the
    consolidated EBITDA. Deterministic formatter on frozen fixtures → value-level pins fit."""
    single = [
        ["For the Fiscal Period", "12 months Nov-30-2025"],
        ["Revenues", ""], ["Software & Programming", 9826.0], ["  Total Revenues", 9826.0],
    ]
    s = cs.segments(_fin_bundle({"Segments": single}, freq="annual"))
    assert s.value == "Software & Programming — single segment"  # no inline period prefix
    assert "100%" not in s.value and "of Total" not in s.value and "9,826" not in s.value
    assert "Nov-30-2025" in (s.source_ref or "")  # the as-of vintage rides the citation

    geo1 = [
        ["For the Fiscal Period", "12 months Sep-27-2025"],
        ["Geographic Segments", ""],
        ["For the Fiscal Period", "12 months Sep-27-2025"],
        ["Revenues", ""], ["United States", 4413.0], ["  Total Revenues", 4413.0],
    ]
    g = cs.geographic(_fin_bundle({"Segments": geo1}, freq="annual"))
    assert g.value == "United States — single geography"

    seg_eb = [
        ["For the Fiscal Period", "12 months Dec-31-2025"],
        ["EBITDA", ""], ["Commercial Services", 283.0], ["Government Solutions", 122.0],
        ["  Total EBITDA", 405.0],
    ]
    inc = [["For the Fiscal Period", "12 months Dec-31-2025"], ["EBITDA", 362.0]]
    b_eb = _fin_bundle({"Segments": seg_eb, "Income Statement": inc}, freq="annual")
    eb = cs.segment_ebitda(b_eb)
    assert eb.status is ds.SourceStatus.PRESENT
    assert "Commercial Services 283 (70%)" in (eb.value or "")  # absolutes + share KEPT
    assert "of segment-EBITDA sum (pre-corporate) 405" in (eb.value or "")  # pre-corporate sum KEPT
    assert "consolidated EBITDA 362" in (eb.value or "") and "~43 unallocated" in (eb.value or "")
    assert not (eb.value or "").startswith("[") and "Dec-31-2025" in (eb.source_ref or "")


# --- item 3: clean same-quarter YoY from the quarterly file; annual margins + guards kept --------
def test_quarterly_revenue_yoy_lives_in_trajectory_not_margin() -> None:
    """The clean same-quarter revenue YoY (Q1-2026 vs Q1-2025) lives in the trajectory/growth field;
    margin_trend carries the margin % + its absolute EBITDA reconciler (A.1) but never the quarterly
    YoY (that growth metric is top-line, not a margin-field item)."""
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
    mv = mt.value or ""
    assert "EBITDA margin:" in mv and "absolute EBITDA:" in mv  # margin % + its reconciler (A.1)
    assert "YoY" not in mv  # the quarterly YoY stays in the trajectory, never under a margin label


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
    statement (not an open 'verify'); without it the original flag stands. Each return now also
    carries a SHORT caveat on the P/E field, so a distorted multiple never renders 'naked'."""
    edgar = _StubEdgar(
        _facts([(2021, 0.28), (2022, 0.28), (2023, 0.28), (2024, 0.85)], shares=1.5e8), net_debt=1e9
    )
    rec, empty = _min_record(pe=5.5, price=4.71), ciq.CiqBundle(ticker="X", workbooks=())
    rg = ds.Sourced.present("Adjusted EPS of $1.19 to $1.25", source_ref="EDGAR 8-K X Ex-99.1")
    resolved = dm._pe_reconciliation(rec, typing.cast(EdgarClient, edgar), empty, rg)
    assert resolved is not None
    flag, pe_note = resolved
    assert flag.startswith("RESOLVED") and "~3.9x" in flag  # 4.71 / 1.22 (mid of $1.19–1.25)
    assert "not a clean multiple" in pe_note  # the SHORT caveat now carried ON the P/E field
    no_guide = dm._pe_reconciliation(rec, typing.cast(EdgarClient, edgar), empty, _u())
    assert no_guide is not None and "verify against normalized/forward EPS" in no_guide[0]
    assert "not a clean multiple" in no_guide[1]  # caveat present on the open-flag path too
    # FUBO-style structurally loss-making: latest annual EPS negative → the caveat names that the
    # P/E rests on a NON-CURRENT positive EPS (the screen reached back past the loss years).
    loss = _StubEdgar(
        _facts([(2021, -2.78), (2022, -3.08), (2023, -1.04), (2024, -0.54)], shares=3e8),
        net_debt=0.0,
    )
    fubo = dm._pe_reconciliation(
        _min_record(pe=12.1, price=6.5), typing.cast(EdgarClient, loss), empty, _u()
    )
    assert fubo is not None and "non-current positive EPS" in fubo[1]
    assert "latest annual EPS is negative" in fubo[1]


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


# --- Catalyst path: the five newly-parsed CIQ Estimates sheets (PR A) -------------------------
#
# Synthetic fixtures ONLY — the licensed CIQ export is never committed. These pin the load-bearing
# behaviours: FQ/FY column mapping, ragged-snapshot handling (never interpolated), serial-date and
# paren-negative range decode, present-but-empty omission, track-record over resolved-only periods,
# event-log ordering + render cap, and the shared staleness caveat at its boundary.


def _trends_ragged() -> list[list[typing.Any]]:
    """Trends with EBITDA MISSING its 2m & 3m snapshots (the real ragged shape) plus a Revenue block
    — same FQ2 / FQ3 / FY-2026 / FQ1-2027 columns."""
    return [
        ["EBITDA", "", "", "", ""],
        ["Company Level (USD)", "FQ2 2026", "FQ3 2026", "FY 2026", "FQ1 2027"],
        ["Current", 10.0, 11.0, 62.1, 5.0],
        ["1 month ago", 10.0, 11.0, 62.1, 5.0],
        ["6 months ago", 20.0, 22.0, 146.5, 8.0],
        ["9 months ago", 20.0, 22.0, 146.5, 8.0],
        ["12 months ago", 25.0, 27.0, 129.7, 9.0],
        ["Revenue", "", "", "", ""],
        ["Company Level (USD)", "FQ2 2026", "FQ3 2026", "FY 2026", "FQ1 2027"],
        ["Current", 100.0, 110.0, 444.4, 50.0],
        ["3 months ago", 120.0, 130.0, 480.5, 60.0],
        ["12 months ago", 150.0, 160.0, 609.0, 70.0],
    ]


def test_acceleration_read_ragged_snapshots_never_interpolated() -> None:
    """(b) ACCELERATION READ walks the current-FY column across ONLY the snapshots present. EBITDA
    missing 2m/3m renders 146.5(6m)→62.1(1m) with a '[3m, 2m n/a]' gap note and NO fabricated
    points. Column mapping: it reads FY 2026 (62.1), not the FQ2 column (10.0)."""
    s = cs.acceleration_read(_est_bundle({"Trends": _trends_ragged()}), as_of="2026-05-15")
    assert s.status is ds.SourceStatus.PRESENT
    v = s.value or ""
    assert "FY 2026 EBITDA:" in v and "146.5 (6m) → 62.1 (1m)" in v  # 3m/2m skipped, not filled
    ebitda_seg = v.split("EBITDA:")[1].split(" | ")[0]  # entries join with ' | ' (table-parseable)
    assert "(3m)" not in ebitda_seg and "(2m)" not in ebitda_seg  # no fabricated snapshot points
    assert "[3m, 2m n/a]" in ebitda_seg and "62.1 (now)" in ebitda_seg  # read FY col, not FQ2
    assert "[as-of 2026-05-15]" in v  # header basis (no '≥') → plain as-of suffix, 'now' labels


def _revisions_fx() -> list[list[typing.Any]]:
    """A Revisions block with all three windows; FY 2026 (col3) carries a distinct downward count so
    a mis-mapped read of the FY column instead of the FQ columns would show up."""
    return [
        ["EPS Normalized", "", "", "", ""],
        ["NasdaqCM:X", "FQ2 2026", "FQ3 2026", "FY 2026", "FQ1 2027"],
        ["Last Month", "", "", "", ""],
        ["# of Analysts", 2, 2, 2, 2],
        ["Upward", 0, 1, 0, 0],
        ["Downward", 0, 0, 0, 0],
        ["Last 2 Months", "", "", "", ""],
        ["# of Analysts", 2, 2, 2, 2],
        ["Upward", 0, 0, 0, 0],
        ["Downward", 1, 2, 3, 0],
        ["Last 3 Months", "", "", "", ""],
        ["# of Analysts", 2, 2, 2, 2],
        ["Upward", 0, 0, 0, 0],
        ["Downward", 1, 2, 3, 0],
    ]


def test_horizon_read_maps_fq_columns_and_surfaces_2month_downgrades() -> None:
    """(a) HORIZON READ shows the next-2-FQ breadth across all three windows; the 2-month-window
    downward revisions the old FY-only line hid are surfaced. Column mapping: it reads the FQ
    columns, never the FY-2026 column (whose 3↓ must therefore never appear)."""
    s = cs.horizon_read(_est_bundle({"Revisions": _revisions_fx()}), as_of="2026-05-15")
    assert s.status is ds.SourceStatus.PRESENT
    v = s.value or ""
    assert "EPS Normalized FQ2 2026:" in v and "2m 0↑/1↓" in v
    assert "EPS Normalized FQ3 2026:" in v and "2m 0↑/2↓" in v
    assert "3↓" not in v  # never reads the FY-2026 column (col3 Downward=3) — FQ mapping only


def test_cross_name_anchor_renders_forward_multiple_ladder() -> None:
    """(c) CROSS-NAME ANCHOR builds the NTM + FY ladder from Multiples; '-' renders absent."""
    mult = [
        ["X > Estimates > Multiples", "", "", "", "", ""],
        ["Based on Market Price", "TEV/REV", "TEV/EBITDA", "TEV/EBIT", "Price/Earnings", "PEG"],
        ["NTM", 1.26, 7.54, 17.55, 14.33, "-"],
        ["FY 2026", 1.42, 10.14, 31.54, 32.25, "-"],
        ["FY 2027", 1.06, 4.26, 9.17, 8.6, "-"],
    ]
    s = cs.cross_name_anchor(_est_bundle({"Multiples": mult}), as_of="2026-05-15")
    assert s.status is ds.SourceStatus.PRESENT
    v = s.value or ""
    assert "NTM:" in v and "Price/Earnings 14.33" in v
    assert "FY 2026:" in v and "Price/Earnings 32.25" in v
    assert "FY 2027:" in v and "Price/Earnings 8.60" in v
    assert "PEG –" in v  # '-' → absent, never 0


def test_parse_range_handles_points_ranges_and_paren_negatives() -> None:
    """Guidance range decode: bare point, range, and parentheses-as-negative."""
    assert cs._parse_range("145.00 - 155.00") == (145.0, 155.0)
    assert cs._parse_range("(120.00) - (150.00)") == (-150.0, -120.0)
    assert cs._parse_range("427.516") == (427.516, 427.516)
    assert cs._parse_range("-") is None and cs._parse_range("") is None


def test_guidance_bridge_sign_aware_recency_and_stale_guide() -> None:
    """(d) + Fixes 2b/2c/3: decodes serials + ranges (paren-negatives); counts ONLY resolved;
    revenue-like uses '≥ floor', cost-like (negative) uses '≤ ceiling'; surfaces the MOST-RECENT
    resolved MET/MISSED; flags a guide older than stale_before. Empty block omitted."""
    guidance = [
        ["X > Estimates > Guidance", "", "", ""],
        ["", "FY 2023", "FY 2024", "FY 2025"],
        ["Revenue", "", "", ""],
        ["As Of Guidance", "", "", ""],
        ["Guidance Date", 44900.0, 45300.0, 45600.0],
        ["Consensus Estimate", 100.0, 200.0, 300.0],
        ["Guidance", "95.0 - 105.0", "190.0 - 210.0", "290.0 - 310.0"],
        ["Actual/Latest", "", "", ""],
        ["Actual", 110.0, 150.0, "-"],  # FY23 beat; FY24 miss; FY25 unresolved (no actual)
        ["Capital Expenditure", "", "", ""],
        ["As Of Guidance", "", "", ""],
        ["Guidance Date", 44950.0, "", ""],
        ["Consensus Estimate", -100.0, "", ""],
        ["Guidance", "(120.00) - (150.00)", "", ""],  # paren-negative → (-150, -120)
        ["Actual/Latest", "", "", ""],
        ["Actual", -130.0, "", ""],  # -130 ≥ -150 guided floor → met
        ["Gross Margin %", "", "", ""],  # present-but-empty
        ["As Of Guidance", "", "", ""],
        ["Guidance Date", "", "", ""],
        ["Guidance", "-", "-", "-"],
    ]
    s = cs.guidance_bridge(
        _est_bundle({"Guidance": guidance}), as_of=None,
        reference_date=date(2026, 1, 1), stale_after_days=45,
    )
    assert s.status is ds.SourceStatus.PRESENT
    v = s.value or ""
    assert "Revenue: latest guide '290.0 - 310.0' for FY 2025 (dated 20" in v  # range kept verbatim
    assert "actual ≥ guided floor 1/2 resolved" in v  # revenue-like; resolved-only (FY25 excluded)
    assert "most recent resolved: FY 2024 MISSED" in v  # Fix 2c — max-dated resolved is a miss
    assert "Capital Expenditure: latest guide '(120.00) - (150.00)'" in v
    assert "spend ≤ guided ceiling 1/1 resolved" in v  # Fix 2b — cost-like (negative) guide label
    assert "most recent resolved: FY 2023 MET" in v
    # R3: '(stale — Nd old)' once, no duplicated date; capex 2023 guide is far older than 45d
    import re as _re
    assert _re.search(r"Capital Expenditure:.*\(stale — \d+d old\)", v)
    assert "(stale guide —" not in v  # the old duplicated-date form is gone
    assert "Gross Margin" not in v  # present-but-empty block omitted, no flag


def test_guidance_bridge_rows_structure_the_same_reads_as_the_string() -> None:
    """(H4) guidance_bridge_rows carries the SAME reads as the flat string, structured for the table
    (metric | latest guide | for | dated | age | record | most recent) — sign-aware record, stale
    age, most-recent outcome. Present-but-empty block omitted; the render is a tagged table."""
    guidance = [
        ["X > Estimates > Guidance", "", "", ""],
        ["", "FY 2023", "FY 2024", "FY 2025"],
        ["Revenue", "", "", ""], ["As Of Guidance", "", "", ""],
        ["Guidance Date", 44900.0, 45300.0, 45600.0],
        ["Consensus Estimate", 100.0, 200.0, 300.0],
        ["Guidance", "95.0 - 105.0", "190.0 - 210.0", "290.0 - 310.0"],
        ["Actual/Latest", "", "", ""], ["Actual", 110.0, 150.0, "-"],
        ["Capital Expenditure", "", "", ""], ["As Of Guidance", "", "", ""],
        ["Guidance Date", 44950.0, "", ""], ["Consensus Estimate", -100.0, "", ""],
        ["Guidance", "(120.00) - (150.00)", "", ""],
        ["Actual/Latest", "", "", ""], ["Actual", -130.0, "", ""],
        ["Gross Margin %", "", "", ""], ["As Of Guidance", "", "", ""],
        ["Guidance Date", "", "", ""], ["Guidance", "-", "-", "-"],  # present-but-empty
    ]
    rows = cs.guidance_bridge_rows(
        _est_bundle({"Guidance": guidance}), reference_date=date(2026, 1, 1), stale_after_days=45)
    assert rows.status is ds.SourceStatus.PRESENT and rows.value is not None
    by = {r.metric: r for r in rows.value}
    assert "Gross Margin %" not in by  # present-but-empty omitted, never a fabricated row
    rev = by["Revenue"]
    assert rev.latest_guide == "'290.0 - 310.0'" and rev.period == "FY 2025"
    assert rev.record == "actual ≥ floor 1/2" and rev.most_recent == "FY 2024 MISSED"
    assert "stale" in rev.age
    cap = by["Capital Expenditure"]
    assert cap.record == "spend ≤ ceiling 1/1" and cap.most_recent == "FY 2023 MET"  # cost-like
    # render is a tagged table with the H4 columns; a pre-H4 CatalystPath (no rows) falls back
    cp = ds.CatalystPath(
        as_of=_u(), horizon_read=_u(), acceleration_read=_u(), cross_name_anchor=_u(),
        guidance_bridge=ds.Sourced.present("flat", source_ref="x"), guidance_bridge_rows=rows,
        revision_events=_u(), consensus_stats=_u())
    block = "\n".join(dr._guidance_bridge_lines(cp))
    assert dr._TABLE_MARK in block and "Record (met/resolved)" in block
    assert "FY 2024 MISSED" in block
    cp_old = cp.model_copy(update={"guidance_bridge_rows": None})
    assert "flat" in "\n".join(dr._guidance_bridge_lines(cp_old))  # old-JSON fallback to the string


def _recent_changes_fx(n: int) -> list[list[typing.Any]]:
    """A Recent-Changes sheet with n dated events in ASCENDING serial order (so the extractor's
    most-recent-first sort is actually exercised)."""
    rows: list[list[typing.Any]] = [
        ["", "", ""],
        ["Change Type", "Date", "Broker", "Analyst", "Data Point", "Period",
         "Broker Value Current", "Broker Value Prior", "Consensus After", "Consensus Before"],
    ]
    for i in range(n):
        rows.append([
            "Downward Revision", 46100.0 + i, f"Broker {i}", "-", "EBITDA", "FY 2026",
            62.0 - i, 146.0, 62.0 - i, 146.0,
        ])
    return rows


def test_estimates_as_of_floor_vs_header_wins_over_events() -> None:
    """Fix 1: with NO As-Of header the as-of is a FLOOR ('≥' + max event date) + an 'unverified'
    note; an explicit 'As-Of Date:' header WINS over the event date (the event never wins). Plus:
    the event log maps columns and sorts newest-first."""
    b = _est_bundle({"Recent Changes": _recent_changes_fx(3)})
    asof = cs.estimates_as_of(b)
    ev = cs.revision_events(b)
    assert asof.status is ds.SourceStatus.PRESENT and ev.status is ds.SourceStatus.PRESENT
    events = ev.value or []
    assert len(events) == 3
    dates = [e.date for e in events]
    assert dates == sorted(dates, reverse=True)  # most-recent-first
    e0 = events[0]
    assert e0.metric == "EBITDA" and e0.period == "FY 2026"
    assert e0.broker_prior == "146.0" and e0.broker_current  # prior=col7, current=col6
    # FLOOR basis: no As-Of header → '≥'-prefixed floor from the max event date + an unverified note
    assert asof.value == "≥" + dates[0] and "unverified" in (asof.note or "")
    # HEADER basis: an explicit 'As-Of Date:' (46197 → 2026-06-24) WINS; the event date is ignored
    consensus = [["X > Estimates > Consensus", ""], ["As-Of Date:", 46197.0]]
    hb = cs.estimates_as_of(
        _est_bundle({"Consensus": consensus, "Recent Changes": _recent_changes_fx(3)})
    )
    assert hb.value == "2026-06-24" and not hb.value.startswith("≥")  # header, not the event floor


def test_revision_events_render_groups_by_date_broker_and_caps() -> None:
    """(4d · T3) The render COMPRESSES to ONE line per broker-day: header count + an action mix
    (n↑/n↓, initiations) + the largest-|Δ| headline + '+N items in JSON'; cap 6 broker-days, the
    rest counted. Serials decoded, never shown raw."""
    rows: list[list[typing.Any]] = [
        ["", "", ""],
        ["Change Type", "Date", "Broker", "Analyst", "Data Point", "Period",
         "Broker Value Current", "Broker Value Prior", "Consensus After", "Consensus Before"],
    ]
    for i, d in enumerate([1, 50, 3, 2, 4, 7]):  # |Δ| sizes; the 50 (M1) is the headline
        rows.append(["Downward Revision", 46100.0, "HCW", "-", f"M{i}", "FY 2026",
                     float(100 - d), 100.0, 0.0, 0.0])
    lines = dr._grouped_events_lines(cs.revision_events(_est_bundle({"Recent Changes": rows})))
    text = "\n".join(lines)
    assert "6 events · 1 broker-days" in text and "46100" not in text  # header + serial decoded
    bd = next(ln for ln in lines if "· HCW" in ln)
    assert "0↑/6↓" in bd  # action mix (all downward, no initiations)
    assert "M1 FY 2026 100.0→50.0" in bd  # headline = the largest |Δ|
    assert "+5 items in JSON" in bd  # the remaining line items counted (one line per broker-day)
    # group cap: 12 distinct broker-days → 6 rendered + the rest noted
    ml = "\n".join(dr._grouped_events_lines(cs.revision_events(_est_bundle(
        {"Recent Changes": _recent_changes_fx(12)}))))
    assert "12 events · 12 broker-days" in ml and "+6 more broker-days in JSON" in ml


def _rev(m: str, p: typing.Any, c: typing.Any) -> ds.RevisionEvent:
    return ds.RevisionEvent(
        date="2026-05-15", change_type="Downward Revision", broker="X", metric=m, period="FY 2026",
        broker_prior=str(p), broker_current=str(c), consensus_before="-", consensus_after="-")


def test_t3_headline_priority_ebitda_over_revenue_and_pct_delta() -> None:
    """(T3) The revision headline ranks on |%Δ| (NEVER raw |Δ| — cross-metric raw deltas are
    unit-incoherent) with metric PRIORITY EBITDA > Revenue > EPS-Normalized. Pin: Revenue's raw |Δ|
    dwarfs EBITDA's, yet EBITDA headlines (priority)."""
    h = dr._revision_headline([_rev("Revenue", 1000, 500), _rev("EBITDA", 100, 50)])
    assert h is not None and h.metric == "EBITDA"  # Revenue |Δ|=500 ≫ EBITDA |Δ|=50, EBITDA wins
    h2 = dr._revision_headline([_rev("EBITDA", 100, 90), _rev("EBITDA", 100, 40),
                                _rev("EBITDA", "-", 5)])  # 10% vs 60% vs excluded (non-numeric)
    assert h2 is not None and h2.broker_current == "40"  # the largest |%Δ| within the metric
    h3 = dr._revision_headline([_rev("EBIT", 100, 90), _rev("Net Income", 100, 20)])
    assert h3 is not None and h3.metric == "Net Income"  # no priority metric → largest |%Δ| (80%)
    assert dr._revision_headline([_rev("EBITDA", "-", "-")]) is None  # all non-numeric → None


# (RC-1.5d) shared fixtures for the interest value-lead: each is a covenant term row (structured
# rate components + the verbatim clause) → the expected [lead, qa]. Drives BOTH the Python unit pin
# and the py↔js parity pin, fed through the real governing_terms collapse (so the field-propagation
# crux is exercised, not a hand-built GoverningTerm).
_RC15D_INTEREST_FIXTURES: list[dict[str, object]] = [
    # (a) pct composite: base + margin_pct + floor + PIK → the full parenthetical lead
    {"name": "Interest / coupon rate",
     "value": "Term SOFR plus 9.75% per annum, subject to a 3.00% floor; 3.75% of interest paid "
              "in kind (PIK).",
     "base_rate_label": "Term SOFR", "margin_pct": 9.75, "floor_pct": 3.0, "pik_pct": 3.75,
     "lead": "Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK)", "qa": ""},
    # (b) bps margin — the LIVE syndicated instrument's shape; bps renders AS DISCLOSED (no convert)
    {"name": "Interest / coupon rate",
     "value": "Interest equal to one-year LPR plus 115 basis points.",
     "base_rate_label": "LPR", "margin_bps": 115.0,
     "lead": "LPR + 115 bps", "qa": ""},
    # (c) incomplete — base present but NO margin → no lead (complete-or-absent); clause carries it
    {"name": "Interest / coupon rate",
     "value": "Term SOFR plus the Applicable Margin (to be set at closing).",
     "base_rate_label": "Term SOFR",
     "lead": "", "qa": ""},
    # (d1) consistency guard — margin_pct's digits ABSENT from the clause (a slip) → no lead + QA
    {"name": "Interest / coupon rate",
     "value": "Term SOFR plus 9.50% per annum.",
     "base_rate_label": "Term SOFR", "margin_pct": 9.75,
     "lead": "", "qa": "rate component 9.75 not stated in the clause — lead suppressed"},
    # (d2) both a pct AND a bps margin → ambiguous, lead suppressed + QA
    {"name": "Interest / coupon rate",
     "value": "Term SOFR plus 9.75% (equivalently 975 basis points).",
     "base_rate_label": "Term SOFR", "margin_pct": 9.75, "margin_bps": 975.0,
     "lead": "", "qa": "both a percent and a bps margin given — ambiguous, lead suppressed"},
    # (e) pre-RC-1.5d JSON — NO structured components at all → no lead, the clause renders, no crash
    {"name": "Interest / coupon rate",
     "value": "Term SOFR plus 9.75%, 3.00% floor, 3.75% PIK.",
     "lead": "", "qa": ""},
    # (f) eighth-of-a-point coupon (X.125/X.625) — the EXACT decimal, NOT a lossy 2dp round: pins
    # the formatter fidelity + py↔js parity (f"{v:.2f}" mis-rounds 9.125→'9.12' and diverges from JS
    # toFixed(2)→'9.13'; _fmt_pct/fmtPct render the shortest exact decimal on both engines)
    {"name": "Interest / coupon rate",
     "value": "Term SOFR plus 9.125% per annum, subject to a 3.625% floor; 2.125% PIK.",
     "base_rate_label": "Term SOFR", "margin_pct": 9.125, "floor_pct": 3.625, "pik_pct": 2.125,
     "lead": "Term SOFR + 9.125% (Floor 3.625%, +2.125% PIK)", "qa": ""},
    # (g) a 0.125 component — exactly representable, the .2f/toFixed(2) half-even-vs-half-up tie
    {"name": "Interest / coupon rate",
     "value": "Fixed spread of 0.125% over the base LPR rate.",
     "base_rate_label": "LPR", "margin_pct": 0.125,
     "lead": "LPR + 0.125%", "qa": ""},
]

_RC15D_SRC = "Credit Agreement 0001111111-25-000001 ex10-1.htm"


def _rc15d_row(fx: dict[str, object]) -> ds.CovenantTerm:
    """The CovenantTerm a fixture describes (structured components + the verbatim clause)."""
    keys = ("base_rate_label", "margin_pct", "margin_bps", "floor_pct", "pik_pct")
    comp = {k: fx[k] for k in keys if k in fx}
    val = ds.Sourced.present(str(fx["value"]), source_ref=_RC15D_SRC)
    return ds.CovenantTerm(name=str(fx["name"]), value=val, **comp)


def _rc15d_gov(fx: dict[str, object]) -> ce.GoverningTerm:
    """The ONE GoverningTerm a fixture collapses to, THROUGH the real governing_terms — so the test
    exercises the component-propagation crux, not a hand-built GoverningTerm."""
    gov = ce.governing_terms([_rc15d_row(fx)], [])
    assert len(gov) == 1
    return gov[0]


def test_rc15d_interest_lead_composed_from_structure() -> None:
    """(RC-1.5d) The interest value-lead is COMPOSED from CovenantTerm's structured rate parts —
    the string-parser (_labelled_rate) is deleted. Complete-or-absent holds (base + one margin
    required); the component-consistency guard suppresses a lead whose digits are absent from the
    clause, or that carries BOTH a pct and a bps margin (a slip must never headline the row); bps
    renders AS DISCLOSED (no pct conversion). Pre-RC-1.5d JSON (no components) lapses to the raw
    clause, no crash. Components propagate through the real governing_terms collapse (the crux)."""
    for fx in _RC15D_INTEREST_FIXTURES:
        gov = _rc15d_gov(fx)
        raw = str(gov.value.value)
        assert dr._compose_interest_lead(gov, raw) == (fx["lead"], fx["qa"]), fx["value"]
        # the interest branch of _covenant_value_lead delegates to the same composition (lead only)
        assert dr._covenant_value_lead("Interest / coupon", raw, gov) == fx["lead"]
    # propagation crux: a present interest row's components survive the collapse onto the gov term
    gov_a = _rc15d_gov(_RC15D_INTEREST_FIXTURES[0])
    assert (gov_a.base_rate_label, gov_a.margin_pct, gov_a.floor_pct, gov_a.pik_pct) == (
        "Term SOFR", 9.75, 3.0, 3.75)
    # back-compat: the pre-RC-1.5d fixture (no structured keys) collapses to None components
    bc = next(fx for fx in _RC15D_INTEREST_FIXTURES
              if not any(k in fx for k in ("base_rate_label", "margin_pct", "margin_bps")))
    gov_e = _rc15d_gov(bc)
    assert gov_e.base_rate_label is None and gov_e.margin_pct is None


def test_rc15d_interest_lead_py_js_parity() -> None:
    """(RC-1.5d · py↔js) render._compose_interest_lead and dossier.js composeInterestLead MUST agree
    on every fixture — the composed lead AND the QA note — feeding the SAME covenant_term_rows JSON
    through each engine's governing_terms collapse (mirror drift is the H2 lesson). Structural: the
    JS carries composeInterestLead and no longer carries the deleted _labelledRate string-parser."""
    import json
    import pathlib
    import shutil
    import subprocess
    js = pathlib.Path("frontend/views/shared/dossier.js").read_text()
    assert "function composeInterestLead(" in js  # the structured composer exists
    assert "_labelledRate" not in js  # the deleted string-parser mirror is gone
    py_out = [list(dr._compose_interest_lead(_rc15d_gov(fx), str(_rc15d_gov(fx).value.value)))
              for fx in _RC15D_INTEREST_FIXTURES]
    assert py_out == [[fx["lead"], fx["qa"]] for fx in _RC15D_INTEREST_FIXTURES]  # matches spec
    if not shutil.which("node"):
        return
    rows = [_rc15d_row(fx).model_dump(mode="json") for fx in _RC15D_INTEREST_FIXTURES]
    # the two JS surfaces the render call site composes from: the collapse (_accOf + governingTerms)
    # and the composer (clauseNumbers … composeInterestLead), sliced by their function boundaries.
    collapse = js[js.index("const _accOf"):js.index("function covenantTerms")]
    composer = js[js.index("function clauseNumbers"):js.index("function covenantValueLead")]
    driver = ("const out=" + json.dumps(rows) + ".map((r)=>{"
              "const g=governingTerms([r],[])[0];"
              "return composeInterestLead(g,String(g.value.value));});"
              "console.log(JSON.stringify(out));")
    # governingTerms keys its Map on a fam+separator+term string where the separator is a literal
    # NUL char (behaviour-identical to Python's tuple key). node -e rejects a NUL in argv, so
    # replace it with its JS unicode escape (parses to the same NUL) so the grouping, and thus
    # the composed lead, is unchanged.
    node_src = (collapse + "\n" + composer + "\n" + driver).replace(chr(0), "\\u0000")
    out = subprocess.run(["node", "-e", node_src], capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == py_out  # zero py↔js divergence on lead AND qa


def test_rc15d_optional_field_coercion_rejects_wrong_shapes() -> None:
    """(RC-1.5d · adversarial-audit) The extractor's fail-soft coercers DROP wrong-shape LLM output
    rather than fabricate a lead or crash the render. _opt_float rejects: a bool (float(True)==1.0
    would headline a fabricated '+1.00%' coupon when a stray '1' sits in the clause), a non-finite
    (nan/inf would crash the bps int() formatter and abort the dossier render), and unparseable
    junk. _opt_str rejects a non-str (a list would str()-ify into a garbage "['Term SOFR']" lead).
    Legit numeric strings / numbers / plain strings still pass (the deterministic path intact)."""
    of, ostr = ce._opt_float, ce._opt_str
    assert of(True) is None and of(False) is None  # bool → dropped, never 1.0 / 0.0
    assert of(float("nan")) is None and of(float("inf")) is None and of(float("-inf")) is None
    assert of("n/a") is None and of(None) is None and of("") is None and of("  ") is None  # junk
    assert of("9.75") == 9.75 and of(9.75) == 9.75 and of(115) == 115.0 and of(0) == 0.0  # legit
    assert ostr(["Term SOFR"]) is None and ostr({"x": 1}) is None and ostr(9.75) is None  # non-str
    assert ostr(True) is None and ostr(None) is None and ostr("") is None and ostr("   ") is None
    assert ostr("Term SOFR") == "Term SOFR" and ostr("  LPR  ") == "LPR"  # legit strings kept
    # root-fix reachability: _opt_float gates non-finite, model_dump_json coerces stray nan/inf to
    # null — so a non-finite component never reaches _compose_interest_lead from the extract path or
    # a committed dossier.json, and the bps int() formatter is never handed one.


def test_rc15d_non_finite_component_suppressed_no_crash_py_js() -> None:
    """(RC-1.5d · audit fix #2, defence-in-depth) Even if a non-finite rate component reaches the
    composer directly (bypassing the _opt_float root gate), _compose_interest_lead AND
    composeInterestLead SUPPRESS the lead with a QA note and NEVER crash — the bps int() formatter
    is never handed a nan/inf. Byte-identical QA note in both engines."""
    import json
    import pathlib
    import shutil
    import subprocess
    qa = "a rate component is not a finite number — lead suppressed"
    clause = "Term SOFR plus 9.75%."

    def gov(**k: object) -> ce.GoverningTerm:
        row = ds.CovenantTerm(name="Interest / coupon rate",
                              value=ds.Sourced.present(clause, source_ref=_RC15D_SRC), **k)
        return ce.governing_terms([row], [])[0]
    for bad in (float("nan"), float("inf"), float("-inf")):
        # non-finite in the REQUIRED margin slot → no lead + QA, no crash
        assert dr._compose_interest_lead(gov(base_rate_label="Term SOFR", margin_pct=bad),
                                         clause) == ("", qa)
        # non-finite in an OPTIONAL slot (floor) with a valid margin → still suppressed, no crash
        assert dr._compose_interest_lead(
            gov(base_rate_label="Term SOFR", margin_pct=9.75, floor_pct=bad), clause) == ("", qa)
    if not shutil.which("node"):
        return
    js = pathlib.Path("frontend/views/shared/dossier.js").read_text()
    composer = js[js.index("function clauseNumbers"):js.index("function covenantValueLead")]
    driver = ("const T=(m)=>({baseRateLabel:'Term SOFR',marginPct:m});"
              "console.log(JSON.stringify([NaN,Infinity,-Infinity].map("
              "(m)=>composeInterestLead(T(m),'Term SOFR plus 9.75%.'))));")
    out = subprocess.run(["node", "-e", composer + "\n" + driver],
                         capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == [["", qa]] * 3  # JS: same QA, no crash, byte-identical to py


def test_frontend_modules_load_as_esm_and_render_smoke() -> None:
    """(HOTFIX gate — MODULE-LOAD integrity, the gate #92 lacked). Node dynamically imports EVERY
    frontend module (lib/ + views/) asserting no throw — catching a top-level import/declaration
    COLLISION like the #92 `fmtPct` (a local coupon formatter re-declaring lib/format.js's imported
    signed-% `fmtPct`) that took the live dossier view down ('Identifier fmtPct has already been
    declared'), which slice-based function-parity tests AND `node --check` both missed. Then it
    renders the committed MVST dossier via renderDossier, asserting a non-error HTML string carrying
    the composed 'LPR + 115 bps' lead. A fixture module with an import+const collision MUST fail
    this smoke (the pinned failure shape) — function-level parity is not load-level integrity."""
    import json
    import pathlib
    import shutil
    import subprocess
    import urllib.parse
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    if not pathlib.Path("data/dossiers/MVST/dossier.json").exists():
        pytest.skip("no committed MVST dossier.json")
    driver = r"""
import { readFileSync, readdirSync, statSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
function walk(dir){ let out=[]; for(const e of readdirSync(dir)){ const p=path.join(dir,e);
  if(statSync(p).isDirectory()) out=out.concat(walk(p));
  else if(p.endsWith(".js")) out.push(p);}
  return out;}
const mods = walk("frontend/lib").concat(walk("frontend/views"));
const failed = [];
for (const m of mods) { try { await import(pathToFileURL(path.resolve(m)).href); }
  catch (e) { failed.push([m, e.name + ": " + e.message.slice(0, 80)]); } }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const html = renderDossier(JSON.parse(readFileSync("data/dossiers/MVST/dossier.json")), null);
console.log(JSON.stringify({nmods: mods.length, failed,
  render_ok: typeof html === "string" && html.length > 0,
  has_lpr: html.includes("LPR + 115 bps")}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    res = json.loads(out.stdout)
    assert res["failed"] == [], f"frontend modules failed to load: {res['failed']}"
    assert res["nmods"] >= 10, f"module walk found too few modules: {res['nmods']}"
    assert res["render_ok"] and res["has_lpr"], f"dossier render smoke failed: {res}"
    # (pin the failure shape) an import+const collision — the #92 bug class — MUST fail the load,
    # or this gate is theatre: a data:-URL module importing the real fmtPct + re-declaring it.
    fmt = pathlib.Path("frontend/lib/format.js").resolve().as_uri()
    fixture = f'import {{ fmtPct }} from "{fmt}";\nconst fmtPct = 1;\nexport const x = 1;\n'
    data_url = "data:text/javascript," + urllib.parse.quote(fixture)
    probe = (f'import({json.dumps(data_url)}).then(()=>console.log("LOADED"))'
             f'.catch((e)=>console.log("THREW:"+e.name));')
    fx = subprocess.run(["node", "--input-type=module", "-e", probe],
                        capture_output=True, text=True, check=True)
    assert "THREW:SyntaxError" in fx.stdout, f"collision fixture must fail, got {fx.stdout!r}"


def test_t2_covenant_table_footer_source_and_value_lead_mvst() -> None:
    """(T2) The covenant table slims: header names the ≤200c clause; the family source lineage moves
    to the table FOOTER; a base row points at the footer; a trimmed clause notes 'full verbatim in
    JSON'; the governing values lead their rows. ANCHOR-STYLE (post-incident): asserts the T2 INTENT
    — the deterministic covenant COMPONENTS present, order/phrasing-free — NOT the LLM's exact
    composite (which reworders on every re-assembly; CLAUDE.md TEST-LAYER rule)."""
    import pathlib
    p = pathlib.Path("data/dossiers/MVST/dossier.json")
    if not p.exists():
        pytest.skip("no committed MVST dossier.json")
    d = ds.Dossier.model_validate_json(p.read_text())
    md = dr.render_markdown(d)
    assert "Governing value (lead · clause ≤200c)" in md  # slimmed header
    assert ("_Source §: 8-K 0001760689-24-000021 · wu_microvast-loanandsecuri.htm · amended by "
            "0000947871-25-000313_") in md  # family lineage in the FOOTER
    assert "| base (footer) |" in md and "full verbatim in JSON" in md
    lines = md.splitlines()
    # defaulted next() → clean AssertionError (not StopIteration) if a draw renders the row UNKNOWN
    def _row(label, extra=""):  # first PRESENT covenant row for `label` (with `extra`), else None
        return next((ln for ln in lines if ln.startswith("| " + label + " |")
                     and "UNKNOWN" not in ln and extra in ln), None)
    # (value-lead · guard-conditional — TEST-LAYER, PER ASSERTION) the conversion row is
    # DETERMINISTICALLY present + base-footer sourced; the derived $/sh leads ONLY when
    # _derive_conversion parses THIS draw's clause. LLM wording varies: an "N shares per $D" clause
    # parses → the $/sh leads before the ' · ' sep; a cross-sentence "$1.00 divided by … Conversion
    # Rate: N shares" does NOT bridge → raw clause, NO fabricated $/sh (anti-fabrication). We
    # DROP the reworded literal tokens ("$0.50/sh"/"2 sh"/"$1.00") and re-derive from the governing
    # verbatim, so any future rewording is covered without a red.
    conv = _row("Conversion price / mechanics")
    assert conv is not None, "no PRESENT Conversion-price covenant row"
    assert "base (footer)" in conv  # deterministic: present + base-sourced
    cs = d.mechanical.capital_structure
    assert cs is not None and cs.covenant_term_rows is not None
    ptrs = (list(cs.covenant_pointer_rows.value)
            if cs.covenant_pointer_rows and cs.covenant_pointer_rows.value else [])
    gov = ce.governing_terms(list(cs.covenant_term_rows.value), ptrs)
    conv_gov = next((g for g in gov if "conversion" in g.term.lower()
                     and g.value.status is ds.SourceStatus.PRESENT), None)
    assert conv_gov is not None, "no PRESENT governing conversion term"
    derived = dr._derive_conversion(str(conv_gov.value.value)).strip().lstrip("(").rstrip(")")
    cell = conv.split(" | ")[1]  # the value cell (lead · clause); " | " is the GFM col delimiter
    if derived:  # clause parsed → the derived $/sh IS the value-lead, before the clause separator
        assert " · " in cell and cell.split(" · ", 1)[0] == derived
    else:  # cross-sentence clause → raw clause carries it, NO fabricated $/sh value-lead
        assert "/sh" not in cell.split(" · ", 1)[0]
    # (deterministic) the interest COVENANT row is PRESENT (non-UNKNOWN, footer). Its lead now
    # COMPOSES from RC-1.5d structured components, but that composite is clause/LLM-adjacent — per
    # TEST-LAYER assert the RATE via the deterministic machine-extracted instrument floating_rate.
    intr = _row("Interest / coupon rate", "SOFR")
    assert intr is not None and "base (footer)" in intr
    assert "SOFR + 9.750%" in md  # instrument floating_rate — deterministic, not the LLM clause


def test_t3_revision_log_compression_pin_mvst() -> None:
    """(T3, pin) MVST renders EXACTLY 3 compressed broker-day lines with the EBITDA-preferred
    headline EBITDA FY26 146.5→62.1 on 2026-05-15."""
    import pathlib
    p = pathlib.Path("data/dossiers/MVST/dossier.json")
    if not p.exists():
        pytest.skip("no committed MVST dossier.json")
    md = dr.render_markdown(ds.Dossier.model_validate_json(p.read_text()))
    bd = [ln for ln in md.splitlines()
          if ln.strip().startswith("- **2026-") and "↑/" in ln and "in JSON" in ln]
    assert len(bd) == 3  # exactly 3 broker-day lines
    assert any("2026-05-15" in ln and "EBITDA FY 2026 146.5→62.1" in ln for ln in bd)


def test_t1_provenance_on_demand_marker_print_exclusion_and_nothing_deleted() -> None:
    """(T1) The md marks the provenance section on-demand (kept in FULL — the md is the audit
    surface); the WEB wraps it in a collapsed <details> and the print CSS excludes non-open details;
    nothing-deleted — the full covenant verbatims + accessions stay in the md (and JSON)."""
    import pathlib
    md = dr.render_markdown(ds.Dossier.model_validate_json(
        pathlib.Path("data/dossiers/MVST/dossier.json").read_text()))
    assert "Capital structure & debt terms — instruments · pointers · covenants" in md
    # anchor-style (audit #2): the verbatim covenant AMOUNT + accession are kept — assert the digits
    # + accession, not the LLM's exact 'RMB …' formatting of the amount (TEST-LAYER rule)
    assert "800,000,000" in md and "0001760689-24-000021" in md
    js = pathlib.Path("frontend/views/shared/dossier.js").read_text()
    css = pathlib.Path("frontend/assets/styles.css").read_text()
    assert "provenance" in js.lower() and "<details" in js  # web on-demand wrap
    assert "details:not([open])" in css and "display: none" in css  # print-exclusion rule


def test_print_reasserts_light_palette_so_dark_never_prints() -> None:
    """(PR5 INVARIANT) Dark mode must NEVER reach paper. The dossier has a dark theme, and
    `@media print { * { print-color-adjust: exact } }` would otherwise bleed the dark canvas onto
    the PDF. Guard: under @media print the dark selector re-declares EVERY token it overrides back
    to its base :root LIGHT value, so a PDF printed while data-theme=dark is fully light. Fully
    deterministic source pin — catches a removed re-assert, a drifted value, or a NEW dark token
    added without a matching print re-assert (the bleed regression)."""
    import pathlib
    import re

    css = pathlib.Path("frontend/assets/styles.css").read_text()

    def hexmap(block: str) -> dict[str, str]:
        return {k: v.lower() for k, v in re.findall(r"(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", block)}

    base = css[css.index(":root {") : css.index("\n}", css.index(":root {"))]
    light = hexmap(base)
    assert (light.get("--bg") and light.get("--surface")
            and light.get("--ink")), "base light tokens missing"

    dstart = css.index(':root[data-theme="dark"]')
    dark = hexmap(css[dstart : css.index("\n}", dstart)])
    # the dark theme must genuinely differ from light (else the whole re-assert is a no-op)
    assert (dark["--bg"] != light["--bg"]
            and dark["--surface"] != light["--surface"]), "dark == light?"

    # the @media print re-assert rule (targets the dark selector, sets light values). Anchor on the
    # block's opening brace — bare "@media print" also appears in the :root header comment above.
    pstart = css.index("@media print {")
    reassert_i = css.index(':root[data-theme="dark"]', pstart)
    reassert = hexmap(css[reassert_i : css.index("}", reassert_i)])

    # EVERY token that differs light-vs-dark MUST be re-asserted to its light value under print
    bleeders = {t: dark[t] for t in dark if light.get(t) and light[t] != dark[t]}
    assert bleeders, "expected the dark theme to override hex tokens"
    for tok, dark_val in bleeders.items():
        assert reassert.get(tok) == light[tok], (
            f"@media print must re-assert {tok} to light {light[tok]} — dark {dark_val} would "
            "bleed onto the PDF (print-color-adjust:exact)"
        )


def test_t3_py_js_revision_headline_parity() -> None:
    """(T3 · py↔js) The revision-headline PRIORITY + |%Δ| logic MUST stay identical in render.py and
    dossier.js — mirror drift is the H2 lesson. Structural: the JS `_HEADLINE_PRIORITY` equals
    Python's; behavioural (node): shared fixtures pick the same headline event on both engines."""
    import json
    import pathlib
    import shutil
    import subprocess
    js = pathlib.Path("frontend/views/shared/dossier.js").read_text()
    m = re.search(r"_HEADLINE_PRIORITY\s*=\s*(\[\[.*?\]\])", js)
    assert m is not None and json.loads(m.group(1)) == [list(t) for t in dr._HEADLINE_PRIORITY]
    if not shutil.which("node"):
        return
    fx = [
        [{"metric": "Revenue", "broker_prior": "1000", "broker_current": "500"},
         {"metric": "EBITDA", "broker_prior": "100", "broker_current": "50"}],  # priority → EBITDA
        [{"metric": "EBITDA", "broker_prior": "100", "broker_current": "90"},
         {"metric": "EBITDA", "broker_prior": "100", "broker_current": "40"}],  # within → 60% move
        [{"metric": "EBIT", "broker_prior": "100", "broker_current": "90"},
         {"metric": "Net Income", "broker_prior": "100", "broker_current": "20"}],  # fallback
        [{"metric": "EBITDA", "broker_prior": "-", "broker_current": "-"}],  # → null/None
    ]
    block = js[js.index("const _pctDelta"):js.index("}", js.index("return numeric.reduce")) + 1]
    src = (block + "\nconst pick=g=>{const h=_revisionHeadline(g);"
           "return h?[h.metric,h.broker_prior,h.broker_current]:null;};"
           f"console.log(JSON.stringify({json.dumps(fx)}.map(pick)))")
    out = subprocess.run(["node", "-e", src], capture_output=True, text=True, check=True)

    def py_pick(g: list[dict[str, str]]) -> object:
        evs = [ds.RevisionEvent(
            date="d", change_type="Downward Revision", broker="X", metric=e["metric"],
            period="FY 2026", broker_prior=e["broker_prior"], broker_current=e["broker_current"],
            consensus_before="-", consensus_after="-") for e in g]
        h = dr._revision_headline(evs)
        return [h.metric, h.broker_prior, h.broker_current] if h else None
    assert json.loads(out.stdout) == [py_pick(g) for g in fx]  # zero divergence


def test_consensus_stats_reads_target_and_ratings_skips_potential_upside() -> None:
    """(f) CONSENSUS STATS reads the target-price stats + rating distribution (from Trends, its real
    home in this export) and NEVER reads CIQ's conclusion-shaped 'Potential Upside/Downside' row."""
    consensus = [
        ["X > Estimates > Consensus", "", "", "", "", ""],
        ["NasdaqCM:X (USD)", "Mean", "Median", "High/Low", "Std. Dev.", "No. of Estimates."],
        ["Target Price", 5.5, 5.5, "6.00/5.00", 0.5, "2/2"],
        ["Potential Upside/Diff. from Target Price", "386.73 %/4.37", "", "", "", ""],
    ]
    trends = [
        ["Non-Periodic Trends", "", ""],
        ["NasdaqCM:X", "Current", "1 month ago"],
        ["Recommendation", "Buy (1.00)", "Buy (1.00)"],
        ["Buy (1)", 2.0, 2.0],
        ["Outperform (2)", 0.0, 0.0],
        ["Hold (3)", 1.0, 1.0],
    ]
    s = cs.consensus_stats(_est_bundle({"Consensus": consensus, "Trends": trends}), as_of=None)
    assert s.status is ds.SourceStatus.PRESENT
    v = s.value or ""
    assert "Target price: mean $5.50, median $5.50" in v and "N 2/2" in v
    assert "Buy 2" in v and "Hold 1" in v  # rating distribution pulled from Trends
    assert "Potential Upside" not in v and "386.73" not in v  # conclusion-shaped row skipped


def test_catalyst_stale_flag_header_hard_gate_floor_bound_caveat() -> None:
    """Fix 1 staleness: on a HEADER basis the shared 45d knob is a hard gate (silent 45d, fire 46d).
    On a FLOOR basis ('≥' as-of) the floor UPPER-BOUNDS staleness — the true export E >= floor F, so
    worst-case staleness is (R - F). A floor WITHIN the 45d window is PROVABLY fresh → silent (the
    '≥F · export date unverified' suffix on each read still flags the un-stamped vintage); a floor
    BEYOND it cannot rule out staleness → soft 'UNVERIFIABLE' caveat carrying the worst-case bound.
    A floor at/after the reference means the export post-dates the screen → fresher → silent.
    UNKNOWN as-of never fires. Supersedes the prior 'any floor fires' rule: a recent floor bounds
    staleness even though it can't pin the exact export date."""
    cp = ds.CatalystPath(
        as_of=ds.Sourced.present("2026-05-15", source_ref="CIQ Estimates→Recent Changes"),
        horizon_read=_u(), acceleration_read=_u(), cross_name_anchor=_u(),
        guidance_bridge=_u(), revision_events=_u(), consensus_stats=_u(),
    )
    assert dm._catalyst_stale_flag(cp, date(2026, 6, 29)) is None  # header, exactly 45d → silent
    fired = dm._catalyst_stale_flag(cp, date(2026, 6, 30))  # header, 46d → hard gate fires
    assert fired is not None and "staleness caveat" in fired and "2026-05-15" in fired

    def floor(f: str) -> ds.CatalystPath:
        return cp.model_copy(update={"as_of": ds.Sourced.present(
            f, source_ref="CIQ Estimates→Recent Changes")})

    # FLOOR within tolerance → PROVABLY FRESH (worst-case staleness ≤ 45d) → silent:
    assert dm._catalyst_stale_flag(floor("≥2026-05-15"), date(2026, 5, 20)) is None   # 5d gap
    assert dm._catalyst_stale_flag(floor("≥2026-05-15"), date(2026, 6, 22)) is None  # MVST 38d
    assert dm._catalyst_stale_flag(floor("≥2026-06-09"), date(2026, 6, 22)) is None  # VRRM 13d
    assert dm._catalyst_stale_flag(floor("≥2026-05-15"), date(2026, 6, 29)) is None   # exactly 45d
    # FLOOR at/after the reference → export post-dates the screen → fresher still → silent:
    assert dm._catalyst_stale_flag(floor("≥2026-06-23"), date(2026, 6, 22)) is None   # floor > ref
    # FLOOR beyond tolerance → cannot rule out staleness → soft UNVERIFIABLE caveat WITH the bound:
    soft = dm._catalyst_stale_flag(floor("≥2026-05-15"), date(2026, 6, 30))  # 46d worst case
    assert soft is not None and "UNVERIFIABLE" in soft and "staleness caveat" not in soft
    assert "46d" in soft  # the worst-case staleness bound is stated, not a bare 'unverifiable'

    unknown = cp.model_copy(update={"as_of": _u()})
    assert dm._catalyst_stale_flag(unknown, date(2027, 1, 1)) is None  # no as-of → no fire


def test_old_dossier_without_catalyst_path_still_renders() -> None:
    """Back-compat: a mechanical layer / dossier.json predating catalyst_path (field absent) parses
    (defaults None) and renders the legacy 'Consensus context' slot — never crashes, never invents a
    catalyst path (the flags-PR fallback precedent)."""
    mech = _minimal_mech()
    assert mech.catalyst_path is None  # constructing without the field works (default None)
    blob = mech.model_dump()
    blob.pop("catalyst_path", None)  # simulate a pre-PR JSON with the key entirely absent
    restored = ds.MechanicalLayer.model_validate(blob)
    assert restored.catalyst_path is None
    dossier = ds.Dossier(
        ticker="X", name="X", cik="0", reference_date=date(2026, 6, 1), rank=1,
        mechanical=restored, synthesis=None, caveats=[], qa_flags=[],
        llm_model=None, assembled_at=datetime(2026, 6, 1, 12, 0),
    )
    md = dr.render_markdown(dossier)
    assert "### Consensus context" in md and "### Catalyst path" not in md


def test_fresh_dossier_renders_catalyst_path_in_place_of_consensus_slot() -> None:
    """A dossier WITH catalyst_path renders the 'Catalyst path' section (as-of on the header) in
    place of the old thin slot. Fix 5: the legacy 'Consensus context' block is GONE; Surprise folds
    in. Fix 4d: events render GROUPED by (date · broker)."""
    cp = ds.CatalystPath(
        as_of=ds.Sourced.present("2026-05-15", source_ref="CIQ Estimates→Recent Changes"),
        horizon_read=ds.Sourced.present("EPS FQ2 2026: 1m 0↑/1↓", source_ref="CIQ→Revisions"),
        acceleration_read=ds.Sourced.present(
            "FY 2026 EBITDA: 146.5 (6m) → 62.1 (now)", source_ref="CIQ→Trends"
        ),
        cross_name_anchor=_u(), guidance_bridge=_u(),
        revision_events=ds.Sourced.present(
            [ds.RevisionEvent(
                date="2026-05-15", change_type="Downward Revision", broker="HCW",
                metric="EBITDA", period="FY 2026", broker_prior="146.5",
                broker_current="62.08", consensus_before="-", consensus_after="62.08",
            )],
            source_ref="CIQ Estimates→Recent Changes (1 event)",
        ),
        consensus_stats=_u(),
    )
    mech = _minimal_mech().model_copy(update={"catalyst_path": cp})
    dossier = ds.Dossier(
        ticker="X", name="X", cik="0", reference_date=date(2026, 6, 1), rank=1,
        mechanical=mech, synthesis=None, caveats=[], qa_flags=[], llm_model=None,
        assembled_at=datetime(2026, 6, 1, 12, 0),
    )
    md = dr.render_markdown(dossier)
    # (re-order 2026-07-27) H2: the "## Mechanical layer" wrapper is gone, so the analysis
    # section heads promoted from H3 to H2.
    assert "## The street — estimates & guidance" in md
    assert "_as-of 2026-05-15_" in md  # (declutter) the vintage is a line, not heading furniture
    assert "146.5 (6m) → 62.1 (now)" in md
    # events COMPRESSED (T3): one line per broker-day with the action mix + the headline revision
    assert "2026-05-15 · HCW" in md and "EBITDA FY 2026 146.5→62.1" in md
    # Fix 5: the legacy 'Consensus context' block is GONE; only Surprise history is folded in
    assert "legacy light facts" not in md and "### Consensus context" not in md
    assert "Surprise history (annual beat/miss)" in md


def test_net_change_is_sign_aware() -> None:
    """Fix 2a: positive series → signed %; negative series → magnitude direction; zero-crossing →
    'crossed'. A bare signed % must never describe a shrinking expense as a 'decline'."""
    assert cs._net_change(100.0, 150.0) == "net +50%"
    assert "improving" in cs._net_change(-13.7, -4.9)  # expense magnitude toward zero
    assert "worsening" in cs._net_change(-4.0, -13.0)  # magnitude away from zero
    assert "crossed" in cs._net_change(-5.0, 3.0) and "crossed" in cs._net_change(5.0, -3.0)


def test_acceleration_negative_series_reads_as_improvement_not_signed_pct() -> None:
    """Fix 2a end-to-end: an all-negative interest-expense path renders 'improving', never a bare
    signed % (which would misread the shrinking expense as a decline)."""
    trends = [
        ["Interest Expense", "", ""],
        ["Company Level (USD)", "FY 2026", "FQ1 2027"],
        ["Current", -4.9, -1.0],
        ["12 months ago", -13.7, -3.0],
    ]
    v = cs.acceleration_read(_est_bundle({"Trends": trends})).value or ""
    assert "Interest Expense:" in v and "-13.7 (12m) → -4.90 (now)" in v  # small vals → 2 decimals
    assert "improving" in v and "net -" not in v  # never a bare signed % on a negative series


def test_render_horizon_collapses_zero_breadth_rows() -> None:
    """Fix 4a: non-zero breadth rows render individually; rows with zero breadth across ALL windows
    collapse to one 'no revisions in any window' line, and the trailing as-of suffix is stripped."""
    s = ds.Sourced.present(
        "Revenue FQ2 2026: 1m 0↑/1↓, 2m 0↑/1↓; EPS FQ2 2026: 1m 0↑/0↓, 2m 0↑/0↓"
        "  [as-of 2026-06-24]",
        source_ref="CIQ Estimates→Revisions",
    )
    text = "\n".join(dr._horizon_lines(s))
    assert "Revenue FQ2 2026:" in text  # non-zero row shown
    assert "no revisions in any window: EPS FQ2 2026" in text  # zero row collapsed
    assert "as-of" not in text  # suffix stripped (the as-of shows once on the section header)


def test_render_ladder_trims_to_ntm_and_near_years() -> None:
    """Fix 4c: the forward-multiple ladder renders NTM + FY26–FY28 only; later years are noted."""
    s = ds.Sourced.present(
        "NTM: P/E 14.33 | FY 2026: P/E 32.25 | FY 2027: P/E 8.60 | FY 2028: P/E 5.35 | "
        "FY 2029: P/E 4.17 | FY 2030: P/E 3.36  [as-of 2026-06-24]",
        source_ref="CIQ Estimates→Multiples",
    )
    text = "\n".join(dr._ladder_lines(s))
    assert "NTM: P/E 14.33" in text and "FY 2028: P/E 5.35" in text
    assert "FY 2029" not in text and "+2 later fiscal years in JSON" in text


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


def test_ciq_modules_covers_every_address_the_extractors_consume() -> None:
    """Drift-PROOF the hand-maintained manifest against the CODE it mirrors: every (kind, freq,
    sheet) address the dossier extractors actually consume must be declared in CIQ_MODULES. A new
    extractor wiring an UNDECLARED kind/freq — or a non-literal address the scan can't see — fails
    HERE, forcing the tuple to be updated (so a folder can't pass the manifest yet fail extraction).

    Same static-guard idiom as the ranker's no-forward-returns AST test. It scans the whole dossier
    package, so addressing can't escape the guard by moving out of ciq_sheets.py. STATE.md §2 logs
    the trigger to migrate to a self-registering address registry once NEW document kinds start
    landing — until then this test is the binding."""
    pkg = Path(__file__).resolve().parents[1] / "vinci" / "dossier"
    declared_kf = {(m.workbook_kind, m.freq) for m in dreq.CIQ_MODULES}
    sheets_by_kf = {(m.workbook_kind, m.freq): set(m.sheets) for m in dreq.CIQ_MODULES}

    def _lit(node: ast.expr) -> str:
        assert isinstance(node, ast.Constant) and isinstance(node.value, str), (
            f"a bundle-address arg must be a string literal, got {ast.dump(node)} — a computed "
            "kind/freq is invisible to this drift guard"
        )
        return node.value

    consumed_kf: set[tuple[str, str | None]] = set()
    consumed_sheets: set[tuple[str, str | None, str]] = set()
    for py in sorted(pkg.glob("*.py")):
        for node in ast.walk(ast.parse(py.read_text())):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if (
                isinstance(fn, ast.Attribute) and fn.attr in ("sheet", "workbook")
                and isinstance(fn.value, ast.Name) and fn.value.id == "bundle"
            ):  # bundle.sheet(kind, sheet, freq=?) / bundle.workbook(kind, freq=?)
                kw = {k.arg: k.value for k in node.keywords}
                kind = _lit(node.args[0])
                freq = _lit(kw["freq"]) if "freq" in kw else None
                consumed_kf.add((kind, freq))
                if fn.attr == "sheet":
                    consumed_sheets.add((kind, freq, _lit(node.args[1])))
            elif (
                isinstance(fn, ast.Name) and fn.id == "_miss_or_unknown" and len(node.args) >= 2
            ):  # the MISSING-fallback helper — its kind must be literal too (it feeds bundle.has)
                _lit(node.args[1])

    assert consumed_kf, "scan found no bundle addresses — the guard is mis-wired"
    undeclared = consumed_kf - declared_kf
    assert not undeclared, (
        f"extractors consume CIQ addresses absent from CIQ_MODULES: {sorted(map(str, undeclared))} "
        "— declare them in requirements.CIQ_MODULES (or, if this is a NEW document KIND, see the "
        "STATE.md registry trigger)"
    )
    missing_sheets = sorted(
        f"{k}/{f}:{s}" for (k, f, s) in consumed_sheets if s not in sheets_by_kf.get((k, f), set())
    )
    assert not missing_sheets, (
        f"sheets consumed but not listed in CIQ_MODULES.sheets: {missing_sheets} — add them so the "
        "manifest's documented subsheets stay honest"
    )


# --- Stage-2 peer-comps extractor (CIQ Company Comparable Analysis) -------------------------------
#
# The consensus comp read is the thing the fund's edge must RESIST, not ingest. These exercise the
# extractor end-to-end on a SYNTHETIC workbook (no licensed CIQ file — the raw workbooks are never
# committed): the roster + business descriptions + market-cap dispersion (so the human judges
# comparability and can re-draw the set), NM PRESERVED as a real not-meaningful state (never dropped
# to missing), and the fundamental DELTAS that let the discount be judged EARNED vs RESIDUAL. The
# fourth is a structural namespacing guard — three EV/EBITDA concepts that must never collide.

# One internally-consistent 3-peer + 1-target comp set, aligned across all four sheets. Caps span
# $478M–$306.6B (641x → HETEROGENEOUS); the target (fuboTV) carries NM on its trailing TEV/EBITDA
# and P/E (a negative base — a REAL state), and out-grows the peer median on revenue at higher beta.
_COMPS_FINANCIAL_DATA = [
    ["Company Name", "", "", "Market Cap ($M)"],
    ["Roku, Inc. (NasdaqGS:ROKU)", "", "", 19900.0],
    ["Netflix, Inc. (NasdaqGS:NFLX)", "", "", 306600.0],
    ["Vimeo, Inc. (NasdaqGS:VMEO)", "", "", 478.0],
    ["", "", "", ""],  # gap separating the peer block from the target
    ["fuboTV Inc. (NYSE:FUBO)", "", "", 256.0],
]
_COMPS_BUSINESS_DESCRIPTION = [
    ["Company Name", "Business Description", "Headquarters"],
    ["Roku, Inc. (NasdaqGS:ROKU)",
     "Roku, Inc. operates a TV streaming platform in the United States.",
     "San Jose, California, United States"],
    ["Netflix, Inc. (NasdaqGS:NFLX)",
     "Netflix, Inc. provides entertainment services worldwide.",
     "Los Gatos, California, United States"],
    ["Vimeo, Inc. (NasdaqGS:VMEO)",
     "Vimeo, Inc. operates a video software platform globally.",
     "New York, New York, United States"],
    ["", "", ""],
    ["fuboTV Inc. (NYSE:FUBO)",
     "fuboTV Inc. operates a live TV streaming platform.",
     "New York, New York, United States"],
]
# Trading Multiples cols: TEV/Rev=1, TEV/EBITDA=2, P/E=4, NTM TEV/Rev=6, NTM TEV/EBITDA=7, NTM_PE=8.
_COMPS_TRADING_MULTIPLES = [
    ["Company Name", "TEV/Rev", "TEV/EBITDA", "", "P/E", "",
     "NTM TEV/Rev", "NTM TEV/EBITDA", "NTM P/E"],
    ["Roku, Inc. (NasdaqGS:ROKU)", 3.0, 25.0, "", 40.0, "", 2.5, 20.0, 35.0],
    ["Netflix, Inc. (NasdaqGS:NFLX)", 8.0, 30.0, "", 45.0, "", 7.0, 25.0, 40.0],
    ["Vimeo, Inc. (NasdaqGS:VMEO)", 1.5, 12.0, "", 18.0, "", 1.3, 10.0, 16.0],
    ["", "", "", "", "", "", "", "", ""],
    ["fuboTV Inc. (NYSE:FUBO)", 1.2, "NM", "", "NM", "", 1.0, 15.0, 50.0],  # NM = negative base
    ["Summary Statistics", "", "", "", "", "", "", "", ""],
    ["Low", 1.5, 12.0, "", 18.0, "", 1.3, 10.0, 16.0],
    ["Median", 3.0, 25.0, "", 40.0, "", 2.5, 20.0, 35.0],
    ["Mean", 4.17, 22.33, "", 34.33, "", 3.6, 18.33, 30.33],
    ["High", 8.0, 30.0, "", 45.0, "", 7.0, 25.0, 40.0],
]
# Operating Statistics cols: EBITDA margin=2, rev growth=5, EBITDA growth=6, Debt/EBITDA=10,
# LT EPS growth=11, beta=12.
_COMPS_OPERATING_STATISTICS = [
    ["Company Name", "", "EBITDA margin", "", "", "Rev growth", "EBITDA growth", "", "", "",
     "Debt/EBITDA", "LT EPS growth", "Beta"],
    ["Roku, Inc. (NasdaqGS:ROKU)", 0.0, 0.10, 0.0, 0.0, 0.09, 0.12, 0.0, 0.0, 0.0, 2.0, 0.15, 1.4],
    ["Netflix, Inc. (NasdaqGS:NFLX)", 0.0, 0.20, 0.0, 0.0, 0.08, 0.10, 0.0, 0.0, 0.0,
     1.5, 0.12, 1.2],
    ["Vimeo, Inc. (NasdaqGS:VMEO)", 0.0, 0.05, 0.0, 0.0, 0.10, 0.15, 0.0, 0.0, 0.0, 1.0, 0.20, 1.5],
    ["", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["fuboTV Inc. (NYSE:FUBO)", 0.0, -0.05, 0.0, 0.0, 0.22, 0.30, 0.0, 0.0, 0.0, 3.0, 0.25, 2.4],
]


class _FakeCompsBundle:
    """A minimal CiqBundle stand-in serving the synthetic comp sheets (and raising the same
    fail-loud error for anything absent) — runs the extractor without a licensed workbook."""

    def __init__(
        self, sheets: dict[tuple[str, str], list[list[typing.Any]]], ticker: str = "TEST"
    ) -> None:
        self._sheets = sheets
        self.ticker = ticker
        self.workbooks: tuple[typing.Any, ...] = ()  # no AS_OF sidecar in the synthetic fixture

    def sheet(
        self, kind: str, sheet_name: str, *, freq: str | None = None
    ) -> list[list[typing.Any]]:
        try:
            return self._sheets[(kind, sheet_name)]
        except KeyError:
            raise ciq.CiqUnavailableError(f"no {kind}/{sheet_name} in fake bundle") from None

    def workbook(self, kind: str, *, freq: str | None = None) -> None:
        return None

    def has(self, kind: str) -> bool:
        return any(k == kind for k, _s in self._sheets)


def _fake_peer_comps() -> ds.PeerComps:
    bundle = _FakeCompsBundle(
        {
            ("comps", "Financial Data"): _COMPS_FINANCIAL_DATA,
            ("comps", "Business Description"): _COMPS_BUSINESS_DESCRIPTION,
            ("comps", "Trading Multiples"): _COMPS_TRADING_MULTIPLES,
            ("comps", "Operating Statistics"): _COMPS_OPERATING_STATISTICS,
        }
    )
    return cs.peer_comps(typing.cast(ciq.CiqBundle, bundle))


def test_peer_comps_field_is_present_on_the_mechanical_layer() -> None:
    """The consensus-resisting comp read has a HOME on the mechanical layer, with the four
    sub-fields the human needs: peer-set COMPOSITION, comparability gate, multiple gap, deltas."""
    assert "peer_comps" in ds.MechanicalLayer.model_fields
    assert ds.MechanicalLayer.model_fields["peer_comps"].annotation is ds.PeerComps
    assert set(ds.PeerComps.model_fields) == {
        "peer_set", "comparability", "trading_multiples", "fundamental_deltas", "peer_grid",  # +B1
    }


def test_peer_comps_carries_roster_descriptions_and_deltas_not_just_summary_stats() -> None:
    """The edge needs the COMPOSITION (every peer named, sized, described) and the fundamental
    DELTAS — NOT just the High/Low/Mean/Median the consensus comp leads with. A roster collapsed to
    four summary stats would hide exactly the heterogeneity the human must weigh."""
    pc = _fake_peer_comps()
    for peer in ("Roku", "Netflix", "Vimeo"):  # each peer named, not summary-collapsed
        assert peer in pc.peer_set.value
    assert "$306.6B" in pc.peer_set.value and "$478M" in pc.peer_set.value  # individual caps
    assert "streaming" in pc.peer_set.value  # business model carried, not just the name
    assert "HETEROGENEOUS" in pc.comparability.value and "641x" in pc.comparability.value
    # name-vs-peer-median deltas (these appear in NO summary-statistics block — they are the
    # earned-vs-residual inputs, surfaced so the human judges the discount, not the machine)
    assert "rev growth name 22% vs peer-median 9%" in pc.fundamental_deltas.value
    assert "beta name 2.4 vs peer-median 1.4" in pc.fundamental_deltas.value
    assert pc.peer_set.source_ref is not None and pc.fundamental_deltas.source_ref is not None


def test_peer_comps_preserves_nm_as_a_real_state_not_dropped_to_missing() -> None:
    """NM (not-meaningful — a negative/near-zero base) is a REAL signal of peer-set heterogeneity,
    never a blank. clean_num would lump it into UNAVAILABLE; the comp extractor keeps it verbatim
    so the human sees the name's trailing multiple does not exist at a negative base."""
    pc = _fake_peer_comps()
    tm = pc.trading_multiples.value
    assert "TEV/EBITDA: name NM" in tm  # the target's trailing EV/EBITDA preserved as NM
    assert "P/E: name NM" in tm  # and its trailing P/E
    assert tm.count("NM") >= 2  # both NM cells survived — not silently dropped to a missing em-dash


def test_three_ev_ebitda_concepts_are_distinctly_named_across_layers() -> None:
    """The three EV/EBITDA concepts must never collide: (a) the SCREEN's Fundamentals.ev_ebitda
    (a dead/quarantined float, deferred until net-debt/EV lands), (b) the DOSSIER's
    Valuation.ev_ebitda (the live single-name trailing multiple), and (c) the PEER composite —
    deliberately carried by PeerComps.trading_multiples, NOT a third field named ev_ebitda. Distinct
    container TYPES and distinct NAMES = no silent merge of dead, live single-name, and peer-set."""

    def _generic(anno: typing.Any) -> tuple[type, tuple[type, ...]]:
        meta = anno.__pydantic_generic_metadata__  # pydantic resolves Sourced[T] to a concrete cls
        return meta["origin"], meta["args"]

    screen_origin, screen_args = _generic(sdr.Fundamentals.model_fields["ev_ebitda"].annotation)
    val_origin, val_args = _generic(ds.Valuation.model_fields["ev_ebitda"].annotation)
    peer_origin, peer_args = _generic(ds.PeerComps.model_fields["trading_multiples"].annotation)

    assert screen_origin is DataField and screen_args == (float,)  # screen: DataField[float] (dead)
    assert val_origin is ds.Sourced and val_args == (float,)  # dossier valuation: Sourced[float]
    assert peer_origin is ds.Sourced and peer_args == (str,)  # peer composite: Sourced[str]
    assert screen_origin is not val_origin  # screen vs dossier: genuinely different containers
    assert "ev_ebitda" not in ds.PeerComps.model_fields  # no colliding third 'ev_ebitda' field


def test_peer_comps_section_reaches_the_rendered_markdown() -> None:
    """The consensus-resisting comp read reaches the human-facing artifact: a 'Peer comps' section
    carries the roster, the comparability gate, the multiple gap (NM intact), and the deltas — and
    the framing poses the discount as a QUESTION (earned vs residual), never a verdict."""
    mech = _minimal_mech().model_copy(update={"peer_comps": _fake_peer_comps()})
    dossier = ds.Dossier(
        ticker="FUBO", name="fuboTV", cik="0001546296", reference_date=date(2026, 6, 1),
        rank=1, mechanical=mech, synthesis=None, caveats=[], qa_flags=[], llm_model=None,
        assembled_at=datetime(2026, 6, 1, 12, 0),
    )
    md = dr.render_markdown(dossier)
    assert "## Peer comps" in md  # H2 since the re-order dropped the mechanical-layer wrapper
    assert "Roku" in md and "$306.6B" in md  # the roster + caps reach the page
    # (declutter) with the grid present the multiples table keeps its FORWARD rows only — the LTM
    # rows were the grid's own summary statistics restated. NM still reaches the artifact (the
    # grid's name row), and the NM legend rides the table that remains.
    assert "Forward multiples (name vs peer Low/Median/Mean/High · NTM)" in md
    assert "**NM**" in md  # NM survives — a real state (negative base), never silently dropped
    assert "NM = a real state" in md
    # B1: the per-peer grid replaces the median-only deltas line — name vs peers + a median footer,
    # rendered through the shared table renderer (no computed discount/delta).
    assert "Per-peer grid" in md and "Peer median" in md and dr._TABLE_MARK in md


# --- PR B: comps upgrades (per-peer grid B1, unified leverage B2, implied valuation B3, riders) ---


def _comps(
    sheets: dict[tuple[str, str], list[list[typing.Any]]], ticker: str = "SUBJ"
) -> ciq.CiqBundle:
    return typing.cast(ciq.CiqBundle, _FakeCompsBundle(sheets, ticker=ticker))


def test_peer_grid_joins_by_ticker_sorts_by_cap_with_median_footer() -> None:
    """(B1) The grid joins Financial Data (cap, net debt) to Operating Statistics (margins/growth/
    Debt-EBITDA) BY TICKER even when the sheets differ in row order; sorted by cap desc, the subject
    is flagged, NM is preserved, and a peer-median (peers-only) footer is appended."""
    fd = [
        ["Company Name", "", "", "Market Cap ($M)", "LTM Net Debt"],
        ["Alpha Corp (NYSE:AL)", "", "", 5000.0, 100.0],
        ["Beta Inc (NYSE:BE)", "", "", 1000.0, 50.0],
        ["Subj Co (NasdaqCM:SUBJ)", "", "", 200.0, 30.0],
    ]
    op = [  # DIFFERENT row order than fd — the join must be by ticker, never positional
        ["Company Name", "GM", "EBITDA", "EB", "NI", "Rg", "Eg", "e", "n", "dc", "Debt/EBITDA"],
        ["Subj Co (NasdaqCM:SUBJ)", 0.3, 0.2, 0, 0, -0.1, 0, 0, 0, 0, 5.8],
        ["Beta Inc (NYSE:BE)", 0.4, 0.1, 0, 0, 0.05, 0, 0, 0, 0, "NM"],
        ["Alpha Corp (NYSE:AL)", 0.5, 0.25, 0, 0, 0.2, 0, 0, 0, 0, 1.5],
    ]
    rows = cs.peer_grid(_comps({
        ("comps", "Financial Data"): fd, ("comps", "Operating Statistics"): op,
    })).value or []
    assert [r.name.split()[0] for r in rows] == ["Alpha", "Beta", "Subj", "Peer"]  # cap desc+footer
    subj = next(r for r in rows if r.is_name)
    assert subj.ebitda_margin == 0.2 and subj.debt_to_ebitda == "5.8"  # joined by ticker, not order
    assert next(r for r in rows if r.name.startswith("Beta")).debt_to_ebitda == "NM"  # NM preserved
    med = next(r for r in rows if r.is_median)
    assert med.market_cap == 3000.0  # median of PEERS only (Alpha 5000, Beta 1000), not the name


def test_peer_grid_valuation_multiples_from_trading_multiples() -> None:
    """(B2) The grid joins the CIQ Trading-Multiples sheet BY TICKER → LTM TEV/EBITDA (col 2),
    TEV/Rev (col 1), P/E (col 4); "NM" preserved; the median footer carries medians. An absent
    Trading-Multiples sheet leaves the multiples None (fail-honest) and the grid still builds."""
    fd = [
        ["Company Name", "", "", "Market Cap ($M)", "LTM Net Debt"],
        ["Alpha Corp (NYSE:AL)", "", "", 5000.0, 100.0],
        ["Beta Inc (NYSE:BE)", "", "", 1000.0, 50.0],
        ["Subj Co (NasdaqCM:SUBJ)", "", "", 200.0, 30.0],
    ]
    op = [
        ["Company Name", "GM", "EBITDA", "EB", "NI", "Rg", "Eg", "e", "n", "dc", "Debt/EBITDA"],
        ["Alpha Corp (NYSE:AL)", 0.5, 0.25, 0, 0, 0.2, 0, 0, 0, 0, 1.5],
        ["Beta Inc (NYSE:BE)", 0.4, 0.1, 0, 0, 0.05, 0, 0, 0, 0, 2.0],
        ["Subj Co (NasdaqCM:SUBJ)", 0.3, 0.2, 0, 0, -0.1, 0, 0, 0, 0, 5.8],
    ]
    tm = [  # col1=TEV/Rev, col2=TEV/EBITDA, col4=P/E — different row order (join must be by ticker)
        ["Company Name", "TEV/Rev", "TEV/EBITDA", "", "P/E"],
        ["Beta Inc (NYSE:BE)", 1.5, 6.0, "", "NM"],
        ["Subj Co (NasdaqCM:SUBJ)", 3.0, 12.0, "", 20.0],
        ["Alpha Corp (NYSE:AL)", 2.0, 8.0, "", 16.0],
    ]
    base = {("comps", "Financial Data"): fd, ("comps", "Operating Statistics"): op}
    rows = cs.peer_grid(_comps({**base, ("comps", "Trading Multiples"): tm})).value or []
    subj = next(r for r in rows if r.is_name)
    assert subj.tev_ebitda == "12" and subj.tev_rev == "3" and subj.pe == "20"  # joined by ticker
    assert next(r for r in rows if r.name.startswith("Beta")).pe == "NM"  # NM preserved, not 0
    assert next(r for r in rows if r.is_median).tev_ebitda == "7"  # median of PEERS (8, 6) = 7
    # fail-honest: no Trading-Multiples sheet → multiples None, the grid still builds
    rows2 = cs.peer_grid(_comps(base)).value or []
    assert all(r.tev_ebitda is None and r.tev_rev is None and r.pe is None for r in rows2)
    assert next(r for r in rows2 if r.is_name).market_cap == 200.0


def test_cross_sectional_headline_median_equals_grid_footer() -> None:
    """(review #7) The Valuation-headline peer median and the per-peer grid-footer median are the
    SAME number for one bundle — both route through the single _peer_col_median primitive, so they
    cannot drift (L1's goal). Feed ONE bundle to both and assert agreement: EV/EBITDA peers (8, 6)
    → median 7; P/E peers (16, NM→excl) → median 16 on BOTH sides."""
    fd = [
        ["Company Name", "", "", "Market Cap ($M)", "LTM Net Debt"],
        ["Alpha Corp (NYSE:AL)", "", "", 5000.0, 100.0],
        ["Beta Inc (NYSE:BE)", "", "", 1000.0, 50.0],
        ["Subj Co (NasdaqCM:SUBJ)", "", "", 200.0, 30.0],
    ]
    op = [
        ["Company Name", "GM", "EBITDA", "EB", "NI", "Rg", "Eg", "e", "n", "dc", "Debt/EBITDA"],
        ["Alpha Corp (NYSE:AL)", 0.5, 0.25, 0, 0, 0.2, 0, 0, 0, 0, 1.5],
        ["Beta Inc (NYSE:BE)", 0.4, 0.1, 0, 0, 0.05, 0, 0, 0, 0, 2.0],
        ["Subj Co (NasdaqCM:SUBJ)", 0.3, 0.2, 0, 0, -0.1, 0, 0, 0, 0, 5.8],
    ]
    tm = [
        ["Company Name", "TEV/Rev", "TEV/EBITDA", "", "P/E"],
        ["Beta Inc (NYSE:BE)", 1.5, 6.0, "", "NM"],
        ["Subj Co (NasdaqCM:SUBJ)", 3.0, 12.0, "", 20.0],
        ["Alpha Corp (NYSE:AL)", 2.0, 8.0, "", 16.0],
    ]
    sheets = {("comps", "Financial Data"): fd, ("comps", "Operating Statistics"): op,
              ("comps", "Trading Multiples"): tm}
    headline = cs.cross_sectional_valuation(_comps(sheets)).value or ""
    med = next(r for r in (cs.peer_grid(_comps(sheets)).value or []) if r.is_median)
    assert "peer median 7.0x" in headline and med.tev_ebitda == "7"  # EV/EBITDA: both = median(8,6)
    assert "peer median 16.0x" in headline and med.pe == "16"  # P/E: both = median(16), NM excluded


def test_peer_grid_renders_valuation_columns_e2e() -> None:
    """(B2 e2e) The per-peer grid carries the valuation columns (TEV/EBITDA, TEV/Rev, P/E) on
    committed VRRM — presence of the headers, phrasing/value-independent."""
    import pathlib
    p = pathlib.Path("data/dossiers/VRRM/dossier.json")
    if not p.exists():
        pytest.skip("no committed VRRM dossier.json")
    d = ds.Dossier.model_validate_json(p.read_text())
    pg = d.mechanical.peer_comps.peer_grid if d.mechanical.peer_comps else None
    if pg is None or pg.status is not ds.SourceStatus.PRESENT or not any(
            r.tev_ebitda is not None for r in (pg.value or [])):
        pytest.skip("VRRM peer_grid not re-assembled with B2 multiples yet")
    md = dr.render_markdown(d)
    for col in ("TEV/EBITDA", "TEV/Rev", "P/E"):
        assert col in md, f"peer grid missing the {col} column"


def _credit_sheet(rated_low: bool) -> list[list[typing.Any]]:
    # rated A-/BBB+ peers score 1-2; unrated distressed peers score 4 → 1=best (rated_low=True)
    lo, hi = (1.0, 4.0) if rated_low else (4.0, 1.0)
    return [
        ["Company Name", "Overall", "Op", "Solv", "Liq", "p", "u", "S&P Issuer Rating", "c", "i"],
        ["Rated Co (NYSE:RA)", lo, lo, lo, lo, "", "", "A-", "US", "x"],
        ["Distressed Co (NYSE:DI)", hi, hi, hi, hi, "", "", "-", "US", "x"],
        ["Subj Co (NasdaqCM:SUBJ)", 3.0, 3.0, 2.0, 2.0, "", "", "-", "US", "x"],
    ]


def test_credit_health_scale_direction_verified_from_data() -> None:
    """(B2) The credit scale direction is read FROM THE DATA: rated peers low, distressed high ⇒
    '1=strongest…4=weakest' (labeled); if the correlation is absent the block reads UNKNOWN."""
    ok = cs.credit_health(_comps({("comps", "Credit Health Panel"): _credit_sheet(rated_low=True)}))
    assert ok.status is ds.SourceStatus.PRESENT
    assert "1=strongest … 4=weakest" in (ok.value or "") and "3/3/2/2" in (ok.value or "")
    # inverted (rated peers score HIGH) → correlation absent → UNKNOWN, not a guess
    bad = cs.credit_health(
        _comps({("comps", "Credit Health Panel"): _credit_sheet(rated_low=False)})
    )
    assert bad.status is ds.SourceStatus.UNKNOWN and "ambiguous" in (bad.note or "")


def test_total_debt_ebitda_labels_the_comps_basis() -> None:
    """(B2) Comps total-debt/EBITDA is LABELED as such (name vs peer median) — never mixed with the
    CIQ net-debt basis. This is the fix for the net-vs-total 3.9x/5.8x incoherence."""
    op = [
        ["Company Name", "GM", "e", "b", "n", "r", "g", "x", "y", "z", "Debt/EBITDA"],
        ["Peer A (NYSE:A)", 0, 0, 0, 0, 0, 0, 0, 0, 0, 2.0],
        ["Peer B (NYSE:B)", 0, 0, 0, 0, 0, 0, 0, 0, 0, 4.0],
        ["Subj Co (NasdaqCM:SUBJ)", 0, 0, 0, 0, 0, 0, 0, 0, 0, 5.8],
    ]
    v = cs.comps_total_debt_ebitda(_comps({("comps", "Operating Statistics"): op})).value or ""
    assert "name 5.8x vs peer median 3.0x" in v and "comps TOTAL-debt/EBITDA basis" in v


def test_implied_valuation_posed_no_percentage_anywhere() -> None:
    """(B3) The implied-valuation block renders the CIQ implied-equity table + bridge + the name's
    market cap adjacent, with the heterogeneity gate — and NO computed %/discount/upside."""
    iv_sheet = [
        ["Implied Valuation"], ["As-Of Date:", 46197.0],
        ["Company Name", "LTM EBITDA", "NTM Revenue"],
        ["Subj Co (NasdaqCM:SUBJ)", 51.9, 498.96],
        ["= Implied Equity Value"],
        ["High", 1794.7, 6521.08], ["Low", 212.5, 329.6],
        ["Mean", 760.2, 1616.39], ["Median", 550.7, 1070.38],
        ["+ Total Cash & ST Investments", 126.1, 126.1], ["- Total Debt", 326.0, 326.0],
        ["/ Shares Outstanding", 333.16, 333.16],
    ]
    fd = [["Company Name", "", "", "Market Cap ($M)"], ["Subj Co (NasdaqCM:SUBJ)", "", "", 423.1]]
    gate = ds.Sourced.present("caps span 641x → HETEROGENEOUS — low comparability", source_ref="x")
    iv = cs.implied_valuation(
        _comps({("comps", "Implied Valuation"): iv_sheet, ("comps", "Financial Data"): fd}), gate,
    )
    assert iv.market_cap.value == 423.1  # the name's ACTUAL cap, adjacent to the CIQ-implied values
    rows = iv.implied_equity.value or []
    ebitda = next(r for r in rows if r.basis == "LTM EBITDA")
    assert ebitda.low == 212.5 and ebitda.median == 550.7 and ebitda.high == 1794.7
    assert "126.1" in (iv.bridge.value or "") and "326.0" in (iv.bridge.value or "")  # bridge
    # HARD FENCE: no schema field names a discount/upside, and no '%' in the rendered block
    md = "\n".join(dr._implied_lines(iv))
    assert "HETEROGENEOUS" in md and "%" not in md


def test_as_of_sidecar_precedence(monkeypatch: typing.Any) -> None:
    """R1: as-of precedence is workbook header > operator AS_OF sidecar (attested) > floor. The
    Estimates export has no header, so a sidecar (when present) beats the event-date floor."""
    est_no_header = {"Recent Changes": _recent_changes_fx(2)}
    # (a) no sidecar → floor ('≥' + event date)
    monkeypatch.setattr(cs, "_sidecar_as_of", lambda _b: None)
    assert (cs.estimates_as_of(_est_bundle(est_no_header)).value or "").startswith("≥")
    # (b) sidecar present → attested, precedence above the floor (no '≥', note says attested)
    monkeypatch.setattr(cs, "_sidecar_as_of", lambda _b: date(2026, 6, 24))
    a = cs.estimates_as_of(_est_bundle(est_no_header))
    assert a.value == "2026-06-24" and "operator-attested" in (a.note or "")
    # the staleness caveat downgrades to NONE for an attested date (trusted)
    cp = ds.CatalystPath(as_of=a, horizon_read=_u(), acceleration_read=_u(), cross_name_anchor=_u(),
                         guidance_bridge=_u(), revision_events=_u(), consensus_stats=_u())
    assert dm._catalyst_stale_flag(cp, date(2027, 1, 1)) is None  # attested → no false caveat


def test_entitlement_renders_undisclosed(monkeypatch: typing.Any) -> None:
    """R2: a CIQ 'Entitlement Needed' name → 'undisclosed (CIQ entitlement)'; a revision broker
    'Entitlement Needed' groups as 'broker undisclosed'."""
    assert cs._undisclosed_name("Entitlement Needed") == "undisclosed (CIQ entitlement)"
    assert cs._undisclosed_name("H.C. Wainwright") == "H.C. Wainwright"
    rows = [["", ""], ["Change Type", "Date", "Broker", "Analyst", "Data Point", "Period",
                       "Cur", "Pri", "After", "Before"],
            ["Downward Revision", 46100.0, "Entitlement Needed", "-", "EBITDA", "FY 2026",
             1.0, 2.0, 1.0, 2.0]]
    ev = cs.revision_events(_est_bundle({"Recent Changes": rows}))
    assert (ev.value or [])[0].broker == "broker undisclosed"


def test_guidance_stale_note_once_and_point_guide_numeric() -> None:
    """R3: a stale guide reads '(stale — Nd old)' ONCE (no duplicated date); a POINT guide renders
    numeric (427.5), a RANGE verbatim."""
    guidance = [
        ["G"], ["", "FY 2026"], ["Revenue"], ["As Of Guidance"],
        ["Guidance Date", 46097.0], ["Guidance", "427.516"], ["Actual/Latest"], ["Actual", "-"],
    ]
    v = cs.guidance_bridge(_est_bundle({"Guidance": guidance}), reference_date=date(2026, 7, 1),
                           stale_after_days=45).value or ""
    assert "latest guide 427.5 for FY 2026" in v  # point guide → numeric, not the raw '427.516'
    import re as _re
    assert _re.search(r"\(stale — \d+d old\)", v) and "(stale guide —" not in v  # once, no repeat


def test_all_rendered_tables_route_through_the_shared_renderer() -> None:
    """B.1 item 1: ENUMERATE every table in the rendered markdown — every GFM table (a '|---'
    separator row) MUST carry the shared-renderer marker. The roster + trading multiples (plain
    _fact text before B.1) now render as tables too. This FAILS before B.1 (they lacked the marker)
    and PASSES after."""
    import re as _re
    iv_sheet = [
        ["Implied Valuation"], ["Company Name", "LTM EBITDA"], ["Subj Co (NasdaqCM:SUBJ)", 51.9],
        ["= Implied Equity Value"], ["High", 1794.7], ["Low", 212.5], ["Mean", 760.2],
        ["Median", 550.7], ["+ Total Cash & ST Investments", 126.1], ["- Total Debt", 326.0],
    ]
    fd_iv = [["Company Name", "", "", "Market Cap ($M)"],
             ["Subj Co (NasdaqCM:SUBJ)", "", "", 423.1]]
    gate = ds.Sourced.present("caps span 641x → HETEROGENEOUS", source_ref="x")
    iv = cs.implied_valuation(
        _comps({("comps", "Implied Valuation"): iv_sheet, ("comps", "Financial Data"): fd_iv}),
        gate,
    )
    # PR C: attach the financial-summary appendix so its C1/C2 tables are enumerated too — every
    # appendix table must route through the shared renderer, same as the comps tables.
    fs = ds.FinancialSummary(
        annual=ds.Sourced.present(
            ds.FinTable(columns=["FY25", "FY26E"],
                        rows=[ds.FinRow(label="Revenue ($M)", cells=["430", "444"])], note="n"),
            source_ref="CIQ Financials (annual)"),
        quarterly=ds.Sourced.present(
            ds.FinTable(columns=["Q4-25", "Q1-26"],
                        rows=[ds.FinRow(label="Revenue ($M)", cells=["96", "61"])], note="n"),
            source_ref="CIQ Financials (quarterly)"),
        balance_sheet=ds.Sourced.present("as of Mar-26 ($M): cash 126", source_ref="CIQ BS"),
        coherence=ds.Sourced.present("BS cash / debt reconcile with the bridge.", source_ref="x"),
        as_of=ds.Sourced.present("2026-05-15", source_ref="x"),
    )
    mech = _minimal_mech().model_copy(update={
        "peer_comps": _fake_peer_comps(), "implied_valuation": iv, "financial_summary": fs,
    })
    dossier = ds.Dossier(
        ticker="X", name="X", cik="0", reference_date=date(2026, 6, 1), rank=1, mechanical=mech,
        synthesis=None, caveats=[], qa_flags=[], llm_model=None,
        assembled_at=datetime(2026, 6, 1, 12, 0),
    )
    md = dr.render_markdown(dossier)
    n_tables = sum(1 for ln in md.splitlines() if ln.startswith("|---"))
    assert n_tables >= 6  # roster + trading multiples + per-peer grid + implied equity + C1 + C2
    assert md.count(dr._TABLE_MARK) == n_tables  # NO table bypasses the shared renderer
    # (declutter) with the grid present the multiples table is FORWARD-only (LTM rows were the
    # grid's summary statistics restated)
    for lbl in ("Peer set", "Forward multiples", "Per-peer grid", "Implied equity at peer-median",
                "Annual financials", "Quarterly financials"):  # incl. the C1/C2 appendix tables
        assert _re.search(_re.escape(lbl) + r"[^\n]*" + _re.escape(dr._TABLE_MARK), md), lbl
    # every GFM table must be COLUMN-ALIGNED: header, separator, and each data row carry the SAME
    # column count. A header one wider than its rows (the implied-equity 'Basis'-in-cols bug) shifts
    # every value one header to the left in the rendered markdown.
    lines = md.splitlines()
    for i, ln in enumerate(lines):
        if not ln.startswith("|---"):
            continue
        ncol = ln.count("|") - 1
        assert lines[i - 1].count("|") - 1 == ncol, f"header≠separator cols:\n{lines[i - 1]}\n{ln}"
        j = i + 1
        while j < len(lines) and lines[j].startswith("|") and not lines[j].startswith("|---"):
            assert lines[j].count("|") - 1 == ncol, f"row≠{ncol} cols:\n{lines[j]}"
            j += 1


def test_numeric_hygiene_shared_formatters() -> None:
    """B.1 item 3 (ONE place): ratios to one decimal (2.0 not 2); NO negative-zero (-0.4% → 0%);
    a negative net-debt is net cash, labeled (CATL); thousands separators consistent."""
    assert dr._ratioc("2") == "2.0" and dr._ratioc("5.8") == "5.8" and dr._ratioc("NM") == "NM"
    assert dr._pctc(-0.004) == "0%" and dr._pctc(0.0006) == "0%"  # both round to a POSITIVE zero
    assert dr._pctc(0.14) == "14%" and dr._pctc(-0.0484) == "-5%"  # a real negative still shows
    assert dr._netdebt(-42108.4) == "42,108 (net cash)"  # CATL: negative net debt → net cash
    assert dr._netdebt(5058.0) == "5,058" and dr._netdebt(None) == "–"  # consistent thousands sep
    # audit fix — half-up rounding (matches the JS Math.round): x.5% with an even integer part must
    # round UP (12.5% → 13%, not banker's 12%), so the .md and the web/PDF never disagree on a %.
    assert dr._pctc(0.125) == "13%" and dr._pctc(0.025) == "3%" and dr._pctc(0.005) == "1%"
    # audit fix — _numc suppresses negative-zero (a small negative → "0.0", never "-0.0")
    assert dr._numc(-0.04) == "0.0" and dr._numc(0.0) == "0.0" and dr._numc(-12.34) == "-12.3"


def test_r1_as_of_sidecar_precedence_confirmed_present() -> None:
    """B.1 item 4: R1 (AS_OF sidecar precedence) SHIPPED in PR B — confirm the machinery is present
    (the detailed three-branch behaviour is pinned by test_as_of_sidecar_precedence)."""
    assert hasattr(cs, "_sidecar_as_of") and hasattr(cs, "comps_as_of")
    # attested basis reads 'operator-attested' and downgrades the staleness caveat to none
    cp = ds.CatalystPath(
        as_of=ds.Sourced.present("2026-06-24", source_ref="sidecar", note="operator-attested"),
        horizon_read=_u(), acceleration_read=_u(), cross_name_anchor=_u(),
        guidance_bridge=_u(), revision_events=_u(), consensus_stats=_u(),
    )
    assert dm._catalyst_stale_flag(cp, date(2027, 1, 1)) is None


def test_old_json_without_comps_blocks_falls_back() -> None:
    """Back-compat: a dossier.json predating B1/B2/B3 (leverage_survival / implied_valuation absent,
    peer_grid None) still renders — the Quality leverage lines + the median-only deltas line."""
    mech = _minimal_mech()  # no leverage_survival / implied_valuation; peer_comps has no peer_grid
    assert mech.leverage_survival is None and mech.implied_valuation is None
    dossier = ds.Dossier(
        ticker="X", name="X", cik="0", reference_date=date(2026, 6, 1), rank=1, mechanical=mech,
        synthesis=None, caveats=[], qa_flags=[], llm_model=None,
        assembled_at=datetime(2026, 6, 1, 12, 0),
    )
    md = dr.render_markdown(dossier)
    assert "## Leverage & survival" in md  # (D1) always renders; H2 since the 2026-07-27 re-order
    assert "both bases labeled" not in md  # NOT the unified block
    assert "Survival capacity (leverage + self-funding + wall)" in md  # Quality leverage fallback
    assert "Fundamental deltas" in md  # the median-only line renders (no grid)


# --- Stage-3 synthesis peer-comp contract (G.3) — the consensus comp read, RESISTED ---------------
#
# The synthesis PROMPT change is untestable directly, but its GUARDRAILS are not: a bare 'cheap vs
# the peer median' verdict (no decomposition, no composition) is the consensus misread the edge must
# resist, and a heterogeneous peer set read as a clean benchmark ignores the confidence gate. Both
# are human-review flags; the machine POSES justified-vs-residual and never computes a residual.

def test_synthesis_peer_comp_contract_flags_bare_gap_and_heterogeneous_benchmark() -> None:
    """G.3: a 'cheap vs the peer median' bull point with no earned-vs-residual decomposition and no
    peer-set composition trips PEER-COMP-BARE; and because comparability flags the set HETEROGENEOUS
    (641x cap span), reading the peer median as a clean benchmark also trips the BENCHMARK gate.
    A claim that DOES decompose the gap and names the heterogeneous set draws neither flag."""
    pc = _fake_peer_comps()  # comparability reads "HETEROGENEOUS — low comparability"
    mech = _minimal_mech().model_copy(update={"peer_comps": pc})
    payload = {
        "bull_points": [
            {"claim": "The name trades cheap versus the peer median on EV/EBITDA.",
             "source_ref": pc.trading_multiples.source_ref},
            {"claim": "Much of the discount to the heterogeneous peer set looks earned by the "
                      "name's weaker revenue growth and higher leverage, leaving a residual the "
                      "human must size.",
             "source_ref": pc.fundamental_deltas.source_ref},
        ],
        "bear_points": [], "twin_reference_cases": [],
        "decisive_question": {"question": "earned or residual?", "evidence_for": [],
                              "evidence_against": []},
        "key_unknowns": [],
    }
    _, flags, _ = syn.synthesize(mech, llm=_FakeLlm(payload), ticker="FUBO", name="FuboTV")
    contract = [f for f in flags if "PEER-COMP-BARE" in f or "HETEROGENEOUS-BENCHMARK" in f]
    assert any("PEER-COMP-BARE bull_point" in f for f in contract)  # bare gap = consensus misread
    assert any("HETEROGENEOUS-BENCHMARK bull_point" in f for f in contract)  # gate fires
    # both flags hit ONLY the bare claim — the decomposed, composition-aware claim is clean
    assert contract and all("trades cheap" in f for f in contract)


def test_synthesis_peer_comp_heterogeneity_gate_is_off_for_a_comparable_set() -> None:
    """The HETEROGENEOUS-BENCHMARK flag KEYS OFF comparability, not a blanket: over a reasonably
    comparable peer set a bare 'cheap vs peers' still trips PEER-COMP-BARE (decomposition is always
    required), but the confidence-gate flag does NOT fire — heterogeneity is a real, gated state."""
    pc = _fake_peer_comps().model_copy(update={
        "comparability": ds.Sourced.present(
            "market caps span $8B–$30B (4x); a reasonably comparable set",
            source_ref="CIQ Comparable Analysis→Financial Data (comparable)",
        )
    })
    mech = _minimal_mech().model_copy(update={"peer_comps": pc})
    payload = {
        "bull_points": [{"claim": "The name screens cheap relative to the peer median.",
                         "source_ref": pc.trading_multiples.source_ref}],
        "bear_points": [], "twin_reference_cases": [],
        "decisive_question": {"question": "q?", "evidence_for": [], "evidence_against": []},
        "key_unknowns": [],
    }
    _, flags, _ = syn.synthesize(mech, llm=_FakeLlm(payload), ticker="FUBO", name="FuboTV")
    assert any("PEER-COMP-BARE" in f for f in flags)  # decomposition still required
    assert not any("HETEROGENEOUS-BENCHMARK" in f for f in flags)  # comparable set → gate off


def test_synthesis_peer_comp_guardrail_precision_no_false_fire_on_brand_or_plural_margins() -> None:
    """G.3 precision (regression for the audit's only finding): the peer-comp guardrails must NOT
    flag (a) quality/brand uses of premium/rich/discount — a premium BRAND, a rich ROADMAP, a
    discount RETAILER are not valuation verdicts (they once tripped the broad _REL_VAL_CUE), nor (b)
    a genuinely DECOMPOSED claim reconciling via the PLURAL 'margins' (the singular-only _DECOMP_REF
    once missed it, false-flagging the very claim it should pass). A bare verdict still fires."""
    pc = _fake_peer_comps()  # comparability reads HETEROGENEOUS
    mech = _minimal_mech().model_copy(update={"peer_comps": pc})

    def contract_flags(claim: str) -> list[str]:
        payload = {
            "bull_points": [{"claim": claim, "source_ref": pc.trading_multiples.source_ref}],
            "bear_points": [], "twin_reference_cases": [],
            "decisive_question": {"question": "q", "evidence_for": [], "evidence_against": []},
            "key_unknowns": [],
        }
        _, flags, _ = syn.synthesize(mech, llm=_FakeLlm(payload), ticker="BRBR", name="BellRing")
        return [f for f in flags if "PEER-COMP-BARE" in f or "HETEROGENEOUS-BENCHMARK" in f]

    # (a) brand/quality words beside a peer mention are NOT valuation verdicts → no contract flag
    for claim in (
        "BellRing's premium protein brand outsells peers in the category.",
        "A rich product roadmap differentiates it from peers.",
        "It is the discount retailer of choice versus department-store peers.",
    ):
        assert contract_flags(claim) == [], f"false-fired on brand claim: {claim}"
    # (b) the PLURAL 'margins' now satisfies the earned-vs-residual decomposition → no bare-gap flag
    decomposed = contract_flags(
        "The name looks cheap vs peers, but its structurally higher margins explain the gap."
    )
    assert not any("PEER-COMP-BARE" in f for f in decomposed)  # 'margins' counts as decomposition
    # control: a BARE relative-valuation verdict still fires PEER-COMP-BARE (guardrail not disabled)
    assert any(
        "PEER-COMP-BARE" in f
        for f in contract_flags("The name trades cheap versus the peer median.")
    )


# --- EDGAR fundamentals fallback (fills EMPTY CIQ fundamentals; CIQ Multiples stays PRIMARY) ------


def _edgar_facts(**by_concept: list[tuple[int, float]]) -> dict[str, typing.Any]:
    """A minimal SEC companyfacts dict keyed by LOGICAL concept → [(fiscal_year, value), ...] annual
    rows (mapped to each concept's first-priority us-gaap tag, so source_refs read the real tag)."""
    from vinci.edgar.concepts import CONCEPT_ALIASES

    us_gaap: dict[str, typing.Any] = {}
    for concept, rows in by_concept.items():
        us_gaap[CONCEPT_ALIASES[concept][0]] = {"units": {"USD": [
            {"start": f"{y}-01-01", "end": f"{y}-12-31", "val": v, "filed": f"{y}-12-31",
             "fy": y, "fp": "FY", "form": "10-K", "accn": f"{concept}-{y}"}
            for (y, v) in rows
        ]}}
    return {"facts": {"us-gaap": us_gaap}}


_FULL_FACTS = _edgar_facts(  # AORT-shaped: full coverage including D&A
    revenue=[(2023, 300e6), (2024, 350e6), (2025, 400e6)],
    operating_income=[(2023, 40e6), (2024, 50e6), (2025, 60e6)],
    dep_amort=[(2023, 20e6), (2024, 22e6), (2025, 24e6)],
    operating_cash_flow=[(2023, 50e6), (2024, 60e6), (2025, 70e6)],
    capex=[(2023, 15e6), (2024, 18e6), (2025, 20e6)],
)
_NO_DNA_FACTS = _edgar_facts(  # CNXC-shaped: operating_income present, ZERO D&A datapoints
    revenue=[(2023, 8e9), (2024, 9e9)],
    operating_income=[(2023, 5e8), (2024, 6e8)],
    operating_cash_flow=[(2023, 7e8), (2024, 8e8)],
    capex=[(2023, 1e8), (2024, 1.2e8)],
)


def test_edgar_fallback_fires_only_when_multiples_present_and_a_ciq_field_empty() -> None:
    """The trigger is the verified empty-subsheet signature: CIQ Multiples PRESENT (primary intact)
    + a CIQ fundamentals field UNKNOWN. Multiples absent, or all fundamentals present, or no facts →
    no fallback (and never a fabricated number)."""
    pres = ds.Sourced.present(7.0, source_ref="CIQ Multiples")
    unk = ds.Sourced.unknown(note="header-only subsheet")
    assert efb.build_fallback(  # no CIQ multiples present → never fall back (wholly un-pulled name)
        multiples=[unk, unk], ciq_fundamentals=[unk, unk], facts_fn=lambda: _FULL_FACTS) is None
    assert efb.build_fallback(  # CIQ fundamentals all populated → no fallback needed
        multiples=[pres], ciq_fundamentals=[pres, pres], facts_fn=lambda: _FULL_FACTS) is None
    fired = efb.build_fallback(  # the trigger: a multiples signal present + a field empty + facts
        multiples=[unk, pres], ciq_fundamentals=[pres, unk], facts_fn=lambda: _FULL_FACTS)
    assert fired is not None
    assert efb.build_fallback(  # no companyfacts (no CIK / fetch failed) → None, never fabricate
        multiples=[pres], ciq_fundamentals=[unk, unk], facts_fn=lambda: None) is None


def test_edgar_full_coverage_populates_fields_with_honest_edgar_source_refs() -> None:
    ef = efb.EdgarFundamentals(_FULL_FACTS)
    fcf, margin, traj = ef.free_cash_flow(), ef.margin_trend(), ef.multi_year_trajectory()
    assert fcf.status is ds.SourceStatus.PRESENT and fcf.value == 50.0  # latest (70 − 20) $M
    assert margin.status is ds.SourceStatus.PRESENT and "EBITDA margin" in (margin.value or "")
    assert traj.status is ds.SourceStatus.PRESENT
    assert all(k in (traj.value or "") for k in ("Revenue:", "EBITDA:", "FCF:"))
    for s in (fcf, margin, traj):  # honestly tagged EDGAR, never a CIQ ref
        assert (s.source_ref or "").startswith("EDGAR XBRL companyfacts")
        assert "CIQ" not in (s.source_ref or "")


def test_edgar_ebitda_is_fail_loud_unknown_when_dna_missing_the_cnxc_case() -> None:
    ef = efb.EdgarFundamentals(_NO_DNA_FACTS)
    # EBITDA needs operating_income + aligned D&A; with ZERO D&A the EBITDA-margin is UNKNOWN…
    assert ef.margin_trend().status is ds.SourceStatus.UNKNOWN
    # …never operating_income alone. Revenue + FCF still derive (no D&A needed) — partial, honest.
    fcf, traj = ef.free_cash_flow(), ef.multi_year_trajectory()
    assert fcf.status is ds.SourceStatus.PRESENT  # OCF − capex needs no D&A
    assert traj.status is ds.SourceStatus.PRESENT and "Revenue:" in (traj.value or "")
    assert "FCF:" in (traj.value or "") and "EBITDA:" not in (traj.value or "")  # EBITDA not faked


def test_cross_source_basis_flag_lands_on_fundamental_deltas_only() -> None:
    pc = ds.PeerComps(
        peer_set=ds.Sourced.present("roster", source_ref="CIQ"),
        comparability=ds.Sourced.present("dispersion", source_ref="CIQ"),
        trading_multiples=ds.Sourced.present("name 7x vs peers", source_ref="CIQ TM"),
        fundamental_deltas=ds.Sourced.present("name 20% vs peer-median 25%", source_ref="CIQ"),
    )
    flagged = efb.flag_deltas_basis(pc)
    assert "EDGAR-GAAP basis" in (flagged.fundamental_deltas.value or "")  # flag carried here…
    assert "EDGAR-GAAP basis" not in (flagged.trading_multiples.value or "")  # …not on multiples
    assert flagged.trading_multiples == pc.trading_multiples  # multiples comparison untouched
    # a MISSING/UNKNOWN fundamental_deltas has no comparison to caveat → flag is a no-op (no note)
    none_pc = pc.model_copy(update={"fundamental_deltas": ds.Sourced.unknown(note="no comps")})
    assert efb.flag_deltas_basis(none_pc).fundamental_deltas == none_pc.fundamental_deltas


def test_financials_freq_prefers_filename_over_empty_income_statement() -> None:
    """The real AORT root cause: its Quarterly export has an EMPTY Income Statement whose
    'Period Type:' boilerplate reads 'Annual', so a content-only read mis-tagged the quarterly
    workbook 'annual' — a freq='quarterly' request then silently fell back to the Annual workbook.
    The FILENAME must win so the quarterly Multiples stay reachable."""
    misleading = [["", "Period Type:", "Annual"]]  # the empty-export boilerplate
    assert ciq._financials_freq("Artivion AORT Financials_Quarterly.xls", misleading) == "quarterly"
    assert ciq._financials_freq("Artivion AORT Financials_Annual.xls", misleading) == "annual"
    qrows = [["", "Period Type:", "Quarterly"]]  # an un-named export → read the verbatim cell
    assert ciq._financials_freq("Financials.xls", qrows) == "quarterly"
    assert ciq._financials_freq("Financials.xls", []) is None
    # a company NAME containing 'quarterly'/'annual' must NOT override the '_Quarterly'/'_Annual'
    # suffix (the match is anchored on the underscore, not a bare substring)
    assert ciq._financials_freq("Quarterly Brands Financials_Annual.xls", []) == "annual"
    assert ciq._financials_freq("Annual Corp Financials_Quarterly.xls", []) == "quarterly"


def test_edgar_ebitda_requires_same_period_start_not_just_period_end() -> None:
    """EBITDA = operating_income + D&A only when BOTH cover the SAME fiscal period. A
    same-period_end pair of different durations (a fiscal-year-transition stub) must NOT be summed —
    the misaligned period is dropped, never fabricated into a wrong EBITDA."""
    def _r(start: str, end: str, val: float) -> dict[str, typing.Any]:
        return {"start": start, "end": end, "val": val, "filed": end, "fy": int(end[:4]),
                "fp": "FY", "form": "10-K", "accn": "x"}
    facts = {"facts": {"us-gaap": {
        "OperatingIncomeLoss": {"units": {"USD": [
            _r("2023-01-01", "2023-12-31", 50e6), _r("2024-01-01", "2024-12-31", 60e6)]}},
        "DepreciationDepletionAndAmortization": {"units": {"USD": [
            _r("2023-01-01", "2023-12-31", 20e6),    # FY2023 aligned → EBITDA computable
            _r("2024-07-01", "2024-12-31", 12e6)]}},  # FY2024: SAME end, 6-month start → must drop
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
            _r("2023-01-01", "2023-12-31", 300e6), _r("2024-01-01", "2024-12-31", 350e6)]}},
    }}}
    ef = efb.EdgarFundamentals(facts)
    # only FY2023 EBITDA survives (FY2024 start-mismatched) → 1 margin point → UNKNOWN
    assert ef.margin_trend().status is ds.SourceStatus.UNKNOWN
    assert "EBITDA:" not in (ef.multi_year_trajectory().value or "")  # no fabricated FY2024 EBITDA


def test_companyfacts_or_none_swallows_valueerror_from_a_bad_cik() -> None:
    """A non-numeric CIK makes companyfacts → pad_cik → int() raise ValueError; the helper must
    return None (never raise into the assembler), per its docstring contract."""
    class _Edgar:
        def companyfacts(self, cik: object) -> dict[str, typing.Any]:
            raise ValueError("invalid literal for int()")
    assert dm._companyfacts_or_none(_Edgar(), "N/A") is None  # type: ignore[arg-type]


# --- PR C: the financial-summary appendix (C1 annual+E, C2 8Q, C3 BS posture) + riders R1/R2/R3 ---


def _fin_est_bundle(annual: _Sheets, estimates: _Sheets) -> ciq.CiqBundle:
    """A CiqBundle carrying an ANNUAL Financials workbook + an Estimates workbook — the two sources
    C1 fuses (actuals from Income Statement/Cash Flow, FY-level consensus from Estimates→Trends)."""
    pf, pe = Path("/fake/FinA.xls"), Path("/fake/Est.xls")
    wf = ciq.CiqWorkbook(kind="financials", path=pf, fmt=ciq.CiqFormat.BIFF_XLS, freq="annual")
    we = ciq.CiqWorkbook(kind="estimates", path=pe, fmt=ciq.CiqFormat.BIFF_XLS, freq="quarterly")
    return ciq.CiqBundle(ticker="X", workbooks=(wf, we), _cache={pf: annual, pe: estimates})


def _c1_trends() -> list[list[typing.Any]]:
    """Estimates→Trends with Revenue, EBITDA, and the two D5a EPS blocks (GAAP + Normalized), each
    carrying FY 2026 + FY 2027 (the FY-level E figures C1 reads from 'Current')."""
    hdr = ["Company Level (USD)", "FQ2 2026", "FQ3 2026", "FY 2026", "FY 2027", "FQ1 2027"]
    return [
        ["Revenue", "", "", "", "", ""], hdr, ["Current", 100.0, 110.0, 444.4, 520.0, 50.0],
        ["EBITDA", "", "", "", "", ""], hdr, ["Current", 10.0, 11.0, 62.1, 90.0, 5.0],
        ["EPS (GAAP)", "", "", "", "", ""], hdr, ["Current", 0.0, 0.0, 0.18, 0.17, 0.0],
        ["EPS Normalized", "", "", "", "", ""], hdr, ["Current", 0.0, 0.0, 0.04, 0.15, 0.0],
    ]


def test_financial_summary_annual_fuses_actuals_and_stamped_estimates() -> None:
    """(C1/C4) The annual table = last-4-FY + LTM actuals + FY26E/FY27E consensus. E columns are
    marked; growth never spans a basis change (Reclassified FY22→FY23 reads '— (basis)') and an FY
    estimate's growth is vs the PRIOR FY (D5c: '+3% (vs FY25)'). EPS splits into same-basis
    GAAP + Normalized rows (D5a). FY26E rev/EBITDA are the SAME Trends 'Current' cells the
    acceleration read consumes (cross-block coherence)."""
    inc: list[list[typing.Any]] = [
        ["For the Fiscal Period", "Reclassified 12 months Dec-31-2022", "12 months Dec-31-2023",
         "12 months Dec-31-2024", "12 months Dec-31-2025", "LTM 12 months Mar-31-2026"],
        ["Total Revenue", 300.0, 350.0, 400.0, 430.0, 440.0],
        ["EBITDA", 40.0, 45.0, 50.0, 55.0, 58.0],
        ["EBIT", 20.0, 25.0, 30.0, 33.0, 34.0],
        ["Net Income", 5.0, 8.0, 10.0, 12.0, 12.0],
        ["Diluted EPS", 0.05, 0.08, 0.10, 0.12, 0.12],  # D5a: GAAP diluted
        ["Normalized Diluted EPS", 0.03, 0.06, 0.08, 0.10, 0.10],  # D5a: normalized
    ]
    cf: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2022", "12 months Dec-31-2023",
         "12 months Dec-31-2024", "12 months Dec-31-2025", "LTM 12 months Mar-31-2026"],
        ["Cash from Ops.", 30.0, 35.0, 40.0, 45.0, 46.0],
        ["Capital Expenditure", -20.0, -22.0, -25.0, -28.0, -29.0],
        ["Levered Free Cash Flow", 10.0, 13.0, 15.0, 17.0, 17.0],
    ]
    trends = _c1_trends()
    b = _fin_est_bundle({"Income Statement": inc, "Cash Flow": cf}, {"Trends": trends})
    s = cs.financial_summary_annual(b, as_of="2026-05-15")
    assert s.status is ds.SourceStatus.PRESENT
    ft = s.value
    assert ft is not None
    assert ft.columns == ["FY22 (R)", "FY23", "FY24", "FY25", "LTM", "FY26E", "FY27E"]  # E marked
    row = {r.label: r.cells for r in ft.rows}
    assert row["Revenue ($M)"] == ["300", "350", "400", "430", "440", "444", "520"]  # actuals + E
    assert row["EBITDA ($M)"][-2:] == ["62", "90"]  # FY26E/FY27E EBITDA from Trends 'Current'
    # growth never spans a basis change; the estimate boundary names its TRUE base (not "actual")
    assert row["Revenue growth"][1] == "— (basis)"   # FY22(R) → FY23: no cross-basis growth
    assert row["Revenue growth"][4] == "— (basis)"   # FY25 → LTM: FY↔ttm is not a like period
    assert row["Revenue growth"][5] == "+3% (vs FY25)"  # D5c: FY26E growth vs the PRIOR FY, not LTM
    assert row["Revenue growth"][6] == "+17%"           # FY27E vs FY26E (est-vs-est, no label)
    # D5a: EPS split into same-basis GAAP + Normalized rows; each reads its OWN basis (no borrowing)
    assert row["EPS (GAAP, dil.)"] == ["0.05", "0.08", "0.10", "0.12", "0.12", "0.18", "0.17"]
    assert row["EPS (Normalized)"] == ["0.03", "0.06", "0.08", "0.10", "0.10", "0.04", "0.15"]
    assert row["CFO ($M)"][:5] == ["30", "35", "40", "45", "46"]  # C4 cash-flow essentials
    assert "as-of 2026-05-15" in ft.note                    # estimate columns carry the as-of stamp
    # cross-block coherence: FY26E EBITDA IS the Trends 'Current' FY 2026 cell (62.1 → "62")
    assert cs._est_fy_current(trends, "EBITDA", "FY 2026") == 62.1
    assert row["EBITDA ($M)"][-2] == "62"
    # (P3, #104) the STRUCTURED series the Revenue/EBITDA chart consumes — parsers rule: RAW numbers
    # behind the cells, aligned to columns, estimate columns flagged; derived rows carry none.
    assert ft.is_estimate == [False, False, False, False, False, True, True]  # only FY26E/FY27E
    assert len(ft.is_estimate) == len(ft.columns)
    rv = {r.label: r.values for r in ft.rows}
    assert rv["Revenue ($M)"] == [300.0, 350.0, 400.0, 430.0, 440.0, 444.4, 520.0]
    assert rv["EBITDA ($M)"] == [40.0, 45.0, 50.0, 55.0, 58.0, 62.1, 90.0]
    assert len(rv["Revenue ($M)"]) == len(ft.columns)  # aligned to columns
    assert rv["Revenue growth"] == [] and rv["EBITDA margin"] == []  # derived → no series


def test_financial_summary_quarterly_shows_collapse_and_basis_guarded_yoy() -> None:
    """(C2) The trailing-8-Q table makes the Q1-2026 revenue collapse (96.4 → 60.6) VISIBLE via QoQ,
    and the YoY is same-basis ONLY — a Reclassified quarter four back reads '— (basis)', a clean
    same-basis pair computes a real %."""
    q: list[list[typing.Any]] = [
        ["For the Fiscal Period",
         "3 months Q2 Jun-30-2024", "3 months Q3 Sep-30-2024",
         "Reclassified 3 months Q4 Dec-31-2024", "3 months Q1 Mar-31-2025",
         "3 months Q2 Jun-30-2025", "3 months Q3 Sep-30-2025",
         "3 months Q4 Dec-31-2025", "3 months Q1 Mar-31-2026"],
        ["Total Revenue", 80.0, 85.0, 90.0, 92.0, 94.0, 95.0, 96.4, 60.6],
        ["Gross Profit", 20.0, 22.0, 24.0, 25.0, 26.0, 27.0, 27.0, 15.0],
        ["EBITDA", 8.0, 9.0, 10.0, 11.0, 12.0, 12.0, 12.0, 3.0],
    ]
    s = cs.financial_summary_quarterly(_fin_bundle({"Income Statement": q}, freq="quarterly"))
    assert s.status is ds.SourceStatus.PRESENT
    ft = s.value
    assert ft is not None
    assert ft.columns[2] == "Q4-24 (R)" and ft.columns[-1] == "Q1-26"  # basis + collapse quarter
    row = {r.label: r.cells for r in ft.rows}
    assert row["Revenue ($M)"][-2:] == ["96", "61"]  # the collapse is visible in the row
    assert row["Revenue QoQ"][-1].startswith("-")  # Q1-26 QoQ sharply negative (the collapse)
    assert row["Revenue YoY"][6] == "— (basis)"  # Q4-25 vs Reclassified Q4-24 → basis-guard
    assert row["Revenue YoY"][7].endswith("%") and "basis" not in row["Revenue YoY"][7]  # clean YoY
    assert "EBITDA margin" in row  # quarterly EBITDA present → margin renders


def test_financial_summary_quarterly_omits_ebitda_when_absent_and_says_so() -> None:
    """(C2) When the quarterly export carries no EBITDA, the EBITDA rows are OMITTED and the note
    says so — never a fabricated/blank EBITDA row."""
    q: list[list[typing.Any]] = [
        ["For the Fiscal Period", "3 months Q4 Dec-31-2025", "3 months Q1 Mar-31-2026"],
        ["Total Revenue", 96.4, 60.6], ["Gross Profit", 27.0, 15.0],
    ]
    s = cs.financial_summary_quarterly(_fin_bundle({"Income Statement": q}, freq="quarterly"))
    assert s.status is ds.SourceStatus.PRESENT
    ft = s.value
    assert ft is not None
    assert not any("EBITDA" in r.label for r in ft.rows)   # omitted, not fabricated
    assert "EBITDA rows omitted" in ft.note                # and the omission is stated


def test_balance_sheet_posture_and_bridge_coherence_gate() -> None:
    """(C3) The posture block is period-labelled (cash/debt/net debt/equity/NWC) and cross-refs
    the leverage block (net-debt/EBITDA NOT recomputed). The coherence gate reconciles the BS
    cash/debt with the implied-valuation bridge; on disagreement it renders BOTH — never silently
    prefers one."""
    bs: list[list[typing.Any]] = [
        ["Balance Sheet as of:", "Dec-31-2025", "Mar-31-2026"],
        ["Total Cash & ST Investments", 120.0, 126.1],
        ["Total Debt", 320.0, 326.0],
        ["Net Debt", 200.0, 199.9],
        ["Total Common Equity", 50.0, 55.0],
        ["Total Current Assets", 300.0, 310.0],
        ["Total Current Liabilities", 150.0, 160.0],
    ]
    b = _fin_bundle({"Balance Sheet": bs}, freq="quarterly")
    posture = cs.balance_sheet_posture(b)
    assert posture.status is ds.SourceStatus.PRESENT
    v = posture.value or ""
    assert "as of Mar-26" in v                                    # freshest period, labelled
    assert "cash & ST inv 126" in v and "total debt 326" in v and "net debt 200" in v
    assert "net working capital 150" in v                         # TCA − TCL = 310 − 160
    assert "not recomputed" in v                                  # cross-refs the leverage block
    # coherence gate — bridge that AGREES (cash 126.1 / debt 326.0) reconciles
    ok_iv = ds.ImpliedValuation(
        implied_equity=ds.Sourced.unknown(note="n/a"),
        bridge=ds.Sourced.present("TEV → equity: + cash $126.1M − debt $326.0M", source_ref="x"),
        market_cap=ds.Sourced.unknown(note="n/a"),
        comparability_gate=ds.Sourced.unknown(note="n/a"),
    )
    coh = dm._bs_bridge_coherence(b, ok_iv)
    assert coh.status is ds.SourceStatus.PRESENT and "reconcile" in (coh.value or "")
    # a bridge that DISAGREES (debt $500M) renders BOTH with a soft caveat — never silently picks
    bad_iv = ok_iv.model_copy(update={
        "bridge": ds.Sourced.present("TEV → equity: + cash $126.1M − debt $500.0M", source_ref="x"),
    })
    dis = dm._bs_bridge_coherence(b, bad_iv)
    d = dis.value or ""
    assert "DISAGREE" in d and "326" in d and "500" in d and "neither is silently preferred" in d


# --- CIQ 'No Data Available' header-only subsheet (AORT, 2026-07) ------------------------------
# AORT's CIQ Financials export returned the literal 'No Data Available' sentinel for its Income
# Statement / Balance Sheet / Cash Flow tabs (header-only, zero numeric cells) WHILE Key Stats +
# Multiples were fully populated on the SAME workbook — a bad/partial export, not missing data. The
# builders surfaced this as a cryptic, bug-masking 'no Fiscal Period header' / bare 'Balance Sheet'
# note — indistinguishable from a genuine parse failure. The fix names the sentinel + the fix
# (re-export). Shells are SYNTHETIC reproductions of the observed shape (no licensed CIQ data).
def _no_data_shell(section: str) -> list[list[typing.Any]]:
    """CIQ's header-only 'No Data Available' subsheet — a title/meta banner, the section label, then
    the sentinel in col 0 (AORT's exact empty-tab shape). No licensed data."""
    return [
        ["Acme Co. (NYSE:XYZ) (Standard)"],
        [""],
        ["In Millions of the reporting currency", "Template:", "Standard", "", "Restatement:"],
        [""],
        [section],
        ["No Data Available"],
        [""],
    ]


def test_financial_summary_annual_no_data_available_names_the_reexport() -> None:
    """(AORT) A 'No Data Available' Income Statement → UNKNOWN whose note names the SENTINEL and the
    actionable fix (re-export) — not the cryptic 'no Fiscal Period header'."""
    b = _fin_bundle({"Income Statement": _no_data_shell("Income Statement")}, freq="annual")
    s = cs.financial_summary_annual(b, as_of="2026-05-15")
    assert s.status is ds.SourceStatus.UNKNOWN and s.value is None
    note = s.note or ""
    assert "No Data Available" in note and "re-export" in note
    assert "no Fiscal Period header" not in note  # the cryptic note is gone


def test_financial_summary_quarterly_no_data_available_names_the_reexport() -> None:
    """(AORT) Same for the quarterly Income Statement subsheet."""
    b = _fin_bundle({"Income Statement": _no_data_shell("Income Statement")}, freq="quarterly")
    s = cs.financial_summary_quarterly(b)
    assert s.status is ds.SourceStatus.UNKNOWN and s.value is None
    note = s.note or ""
    assert "No Data Available" in note and "re-export" in note
    assert "no Fiscal Period header" not in note


def test_balance_sheet_posture_no_data_available_names_the_reexport() -> None:
    """(AORT) A 'No Data Available' Balance Sheet → UNKNOWN naming the sentinel + re-export — not
    the bare 'Balance Sheet' note (which _miss_or_unknown emitted for the header-only shell)."""
    b = _fin_bundle({"Balance Sheet": _no_data_shell("Balance Sheet")}, freq="quarterly")
    s = cs.balance_sheet_posture(b)
    assert s.status is ds.SourceStatus.UNKNOWN and s.value is None
    note = s.note or ""
    assert "No Data Available" in note and "re-export" in note


def test_return_ratios_no_data_available_names_the_reexport() -> None:
    """(AORT, review #155) The Ratios FinTable panel gets the same guard — a 'No Data Available'
    Ratios sheet → UNKNOWN naming the sentinel + re-export, not the cryptic header note."""
    b = _fin_bundle({"Ratios": _no_data_shell("Ratios")}, freq="annual")
    s = cs.return_ratios(b)
    assert s.status is ds.SourceStatus.UNKNOWN and s.value is None
    note = s.note or ""
    assert "No Data Available" in note and "re-export" in note
    assert "no Fiscal Period header" not in note


def test_no_data_shell_stays_distinct_from_a_genuine_header_parse_failure() -> None:
    """The negative pin: a POPULATED sheet with real rows but NO Fiscal-Period header (a genuine
    parse failure) must STILL read 'no Fiscal Period header' — never the No-Data note. The two
    failure modes stay distinct, so a real parse bug is never masked by (nor misfiled as) the
    benign, re-exportable data gap. Also pins the guard helper directly."""
    populated_no_header: list[list[typing.Any]] = [
        ["Income Statement"],               # a section label, but no 'For the Fiscal Period' row
        ["Total Revenue", 100.0, 110.0],
        ["EBITDA", 20.0, 22.0],
    ]
    assert cs._no_data_available(_no_data_shell("Income Statement")) is True   # shell → detected
    assert cs._no_data_available(populated_no_header) is False                 # populated → not
    s = cs.financial_summary_annual(
        _fin_bundle({"Income Statement": populated_no_header}, freq="annual"), as_of="2026-05-15")
    assert s.status is ds.SourceStatus.UNKNOWN
    note = s.note or ""
    assert "no Fiscal Period header" in note and "No Data Available" not in note


def test_credit_health_completes_all_four_peer_median_dims() -> None:
    """(R1) Credit health reports the name's four dimensions AND the peer median PER dimension (not
    Overall only): peers score [1, 4] on each of O/Op/S/L → median 2.5 across the board."""
    s = cs.credit_health(_comps({("comps", "Credit Health Panel"): _credit_sheet(rated_low=True)}))
    assert s.status is ds.SourceStatus.PRESENT
    v = s.value or ""
    assert "name Overall/Operational/Solvency/Liquidity 3/3/2/2" in v      # all four name dims
    assert "peer-median O/Op/S/L 2.5/2.5/2.5/2.5" in v                     # all four peer medians


def test_comps_layout_excludes_a_bare_paren_disclaimer_row() -> None:
    """(#57 audit) A trailing prose row with a BARE paren but NO 'EXCHANGE:SYMBOL' ticker — the S&P
    'No content (including ratings…' boilerplate on the Credit Health Panel (which has no 'Summary
    Statistics' delimiter, so end=len(rows)) — must NOT be admitted as a peer, must NOT become the
    subject via the last-row fallback, and its stray numerics must NOT leak into a peer median."""
    rows: list[list[typing.Any]] = [
        ["Company Name", "Overall", "Op", "Solv", "Liq", "p", "u", "S&P Issuer Rating", "c", "i"],
        ["Rated Co (NYSE:RA)", 1.0, 1.0, 1.0, 1.0, "", "", "A-", "US", "x"],
        ["Distressed Co (NYSE:DI)", 4.0, 4.0, 4.0, 4.0, "", "", "-", "US", "x"],
        ["Subj Co (NasdaqCM:SUBJ)", 3.0, 3.0, 2.0, 2.0, "", "", "-", "US", "x"],
        # disclaimer: bare paren, no ticker, stray 9.0s in the dim cols, NO Summary-Statistics row
        ["No content (including ratings) reproduced", 9.0, 9.0, 9.0, 9.0, "", "", "-", "", ""],
    ]
    _hdr, peers, target = cs._comps_layout(rows, "SUBJ")
    assert not any("No content" in str(rows[i][0]) for i in peers)  # disclaimer is NOT a peer
    assert target == 3 and "Subj Co" in str(rows[target][0])        # the real subject, not fallback
    # end-to-end: the stray 9.0s never enter the medians — peers stay [1, 4] → median 2.5 (not 4)
    s = cs.credit_health(_comps({("comps", "Credit Health Panel"): rows}))
    assert "peer-median O/Op/S/L 2.5/2.5/2.5/2.5" in (s.value or "")


def test_self_referential_twin_dropped_as_hidden_qa_flag() -> None:
    """(R2) A twin naming the SUBJECT with no resolved past period is a hallucinated self-comparison
    — DROPPED at validation with a QA flag naming it. A dated self-arc ('2022-2024') and a
    genuine other-company twin BOTH survive."""
    payload = {
        "bull_points": [{"claim": "revenue reaccelerated last quarter", "source_ref": "10-Q"}],
        "bear_points": [],
        "twin_reference_cases": [
            {"name": "Microvast (battery-derating pattern)", "outcome": "went terminal",
             "distinguishing_fact": "the same overshoot", "source": "fab"},  # self-ref → drop
            {"name": "Microvast 2022-2024 arc", "outcome": "recovered off the 2022 low",
             "distinguishing_fact": "a dated resolved period", "source": "fab"},  # keep
            {"name": "SolarEdge", "outcome": "demand cliff", "distinguishing_fact": "x",
             "source": "fab"},  # other co → keep
        ],
        "decisive_question": {"question": "does the cause reverse?", "evidence_for": [],
                              "evidence_against": []},
        "key_unknowns": [],
    }
    synth, flags, _ = syn.synthesize(
        _minimal_mech(), llm=_FakeLlm(payload), ticker="MVST", name="Microvast Holdings, Inc."
    )
    assert synth is not None
    kept = {t.name for t in synth.twin_reference_cases}
    assert kept == {"Microvast 2022-2024 arc", "SolarEdge"}          # the self-ref twin was dropped
    drop_flag = next(f for f in flags if "self-referential 'Microvast (battery" in f)
    caveats, qa = dflags.partition(flags)
    assert drop_flag in qa and drop_flag not in caveats  # the drop is dev-only QA, hidden
    assert any(f.startswith("TWIN 1 invalid twin(s) suppressed") for f in qa)  # dev-only count line


def test_internal_rule_leak_flagged_as_hidden_qa() -> None:
    """(R3) A synthesis field that leaks an internal 'rule N' reference is caught by the QA lint —
    the reader must never see the machinery. The flag is dev-only (hidden from human caveats)."""
    payload = {
        "bull_points": [{"claim": "the balance sheet self-funds two years", "source_ref": "x"}],
        "bear_points": [],
        "twin_reference_cases": [],
        "decisive_question": {"question": "does the cause reverse?", "evidence_for": [],
                              "evidence_against": []},
        "key_unknowns": ["whether the thesis survives rule 8 scrutiny"],  # leaked rule ref
    }
    _synth, flags, _ = syn.synthesize(
        _minimal_mech(), llm=_FakeLlm(payload), ticker="X", name="X Co"
    )
    leak = next(f for f in flags if f.startswith("RULE-LEAK"))
    assert "rule 8" in leak
    caveats, qa = dflags.partition(flags)
    assert leak in qa and leak not in caveats  # dev-only QA, not a human caveat


# --- PR C audit fixes (post-review regressions): fail-loud coherence, same-quarter YoY, CF join,
# --- posture as-of anchoring, FY↔LTM basis, R2 false-drop -----------------------------------------


def test_bs_bridge_coherence_missing_debt_fails_loud_not_zero() -> None:
    """(C3 fix) A bridge that OMITS the debt row must not read as a disagreement and must never
    fabricate a '$0M' — the present cash leg reconciles, the absent debt leg is 'not cross-checked'.
    (The pre-fix code rendered a false DISAGREE with a made-up debt $0M.)"""
    bs: list[list[typing.Any]] = [
        ["Balance Sheet as of:", "Mar-31-2026"],
        ["Total Cash & ST Investments", 126.1], ["Total Debt", 326.0],
    ]
    b = _fin_bundle({"Balance Sheet": bs}, freq="quarterly")
    iv = ds.ImpliedValuation(
        implied_equity=ds.Sourced.unknown(note="n/a"),
        bridge=ds.Sourced.present("TEV → equity: + cash $126.1M", source_ref="x"),  # NO debt row
        market_cap=ds.Sourced.unknown(note="n/a"),
        comparability_gate=ds.Sourced.unknown(note="n/a"),
    )
    v = dm._bs_bridge_coherence(b, iv).value or ""
    assert "DISAGREE" not in v            # a missing bridge row is not a disagreement
    assert "$0" not in v                  # never fabricate a zero for an ABSENT figure
    assert "reconcile" in v and "not cross-checked" in v  # cash reconciles; debt honestly flagged


# --- PR 6 (bridge-parse + credit-health): structured floats, shared parser, tiered credit scale ---


def test_ie_bridge_net_debt_reads_structured_floats_thousands_aware() -> None:
    """(P1/P2a-b) Net debt from the bridge reads the STRUCTURED floats — a thousands value
    ($1,101.80M) no longer truncates to 1. VRRM: 1101.8 − 55.6 = 1046.2 (was −54.6 via the
    comma-blind regex → a FALSE reconcile caveat); MVST unchanged 199.9. The string-only fallback
    (shared _parse_money) yields the SAME value."""
    vrrm = "TEV→equity bridge: + cash $55.60M, − total debt $1,101.80M"
    mvst = "TEV→equity bridge: + cash $126.10M, − total debt $326.00M"

    def nd(iv: ds.ImpliedValuation) -> float:
        return round(dm._ie_bridge_net_debt(iv) or 0.0, 1)

    assert nd(_iv(vrrm, cash=55.6, debt=1101.8)) == 1046.2      # structured primary path
    assert nd(_iv(mvst, cash=126.1, debt=326.0)) == 199.9
    assert nd(_iv(vrrm)) == 1046.2   # string-only fallback (was 1 − 55.6 = −54.6 before the fix)
    assert nd(_iv(mvst)) == 199.9


def test_parse_money_roundtrips_thousands_and_handles_edges() -> None:
    """(P2c) The ONE shared money parser round-trips money()-formatted values ≥ $1,000M (the comma
    case the thousands-blind regex broke), and handles $/M/(paren-negative)/absent."""
    def money(v: int) -> str:  # mirrors the _bs_bridge_coherence display formatter f"${v:,.0f}M"
        return f"${v:,.0f}M"

    for v in (1000, 1101, 5678, 12345, 1000000):
        assert dm._parse_money(money(v)) == float(v)           # comma-aware round-trip
    assert dm._parse_money("$1,101.80M") == 1101.8             # the literal VRRM debt figure
    assert dm._parse_money("$55.60M") == 55.6
    assert dm._parse_money("(120.00)") == -120.0               # parenthetical negative
    assert dm._parse_money("—") is None
    assert dm._parse_money("") is None
    assert dm._parse_money(None) is None


def test_bridge_reconcile_gate_still_fires_on_structured_disagreement() -> None:
    """(P2d) The fix must NOT weaken the reconcile gate: a genuine BS-vs-bridge disagreement ≥ the
    5% band STILL fires the soft caveat, from the STRUCTURED bridge floats (a thousands debt, never
    the display string). Agreement stays silent."""
    bs: list[list[typing.Any]] = [
        ["Balance Sheet as of:", "Mar-31-2026"],
        ["Total Cash & ST Investments", 55.6], ["Total Debt", 1101.8],
    ]
    b = _fin_bundle({"Balance Sheet": bs}, freq="quarterly")
    agree = _iv("+ cash $55.60M, − total debt $1,101.80M", cash=55.6, debt=1101.8)
    assert "DISAGREE" not in (dm._bs_bridge_coherence(b, agree).value or "")  # agree → silent
    disagree = _iv("+ cash $55.60M, − total debt $1,500.00M", cash=55.6, debt=1500.0)
    d = dm._bs_bridge_coherence(b, disagree).value or ""
    assert "DISAGREE" in d and "1,102" in d and "1,500" in d  # both rendered, not truncated


def _credit_sheet_quality_roster() -> list[list[typing.Any]]:
    # A quality roster (the VRRM premise): the UNRATED peers are STRONG (not weak), so rated-mean >
    # unrated-mean and the rated-vs-unrated fallback reads falsely ambiguous; the scale is instead
    # verified WITHIN the rated set — an IG peer (BBB+) scores stronger than a sub-IG peer (BB).
    return [
        ["Company Name", "Overall", "Op", "Solv", "Liq", "p", "u", "S&P Issuer Rating", "c", "i"],
        ["IG Peer (NYSE:IG)", 2.0, 2.0, 2.0, 2.0, "", "", "BBB+", "US", "x"],
        ["SubIG Peer (NYSE:SB)", 4.0, 4.0, 4.0, 4.0, "", "", "BB", "US", "x"],
        ["Strong Unrated (NYSE:SU)", 1.0, 1.0, 1.0, 1.0, "", "", "-", "US", "x"],
        ["Subj Co (NasdaqCM:SUBJ)", 3.0, 2.0, 4.0, 2.0, "", "", "BB-", "US", "x"],
    ]


def test_credit_health_tier1_monotonicity_rescues_quality_roster() -> None:
    """(P3) On a quality roster the UNRATED peers score strong, so the rated-vs-unrated fallback
    reads falsely ambiguous (rated-mean 3.0 > unrated-mean 1.0 → old code UNKNOWN). Tier-1 (IG 2.0 ≤
    sub-IG 4.0 within the rated set) verifies the scale and the panel RENDERS — name BB- 3/2/4/2,
    all four peer-median dims. (unrated ≠ weak.)"""
    s = cs.credit_health(_comps({("comps", "Credit Health Panel"): _credit_sheet_quality_roster()}))
    assert s.status is ds.SourceStatus.PRESENT
    v = s.value or ""
    assert "name Overall/Operational/Solvency/Liquidity 3/2/4/2" in v   # name BB- shape (VRRM-like)
    assert "S&P issuer rating BB-" in v
    assert "peer-median O/Op/S/L 2/2/2/2" in v                          # all four medians present
    assert "1=strongest … 4=weakest" in v


def _credit_sheet_inverted_rated() -> list[list[typing.Any]]:
    # IG scores WORSE than sub-IG (inverted) AND rated > unrated → BOTH tiers fail.
    return [
        ["Company Name", "Overall", "Op", "Solv", "Liq", "p", "u", "S&P Issuer Rating", "c", "i"],
        ["IG Peer (NYSE:IG)", 4.0, 4.0, 4.0, 4.0, "", "", "BBB+", "US", "x"],
        ["SubIG Peer (NYSE:SB)", 2.0, 2.0, 2.0, 2.0, "", "", "BB", "US", "x"],
        ["Strong Unrated (NYSE:SU)", 1.0, 1.0, 1.0, 1.0, "", "", "-", "US", "x"],
        ["Subj Co (NasdaqCM:SUBJ)", 3.0, 3.0, 3.0, 3.0, "", "", "BB-", "US", "x"],
    ]


def test_credit_health_refuses_when_no_tier_verifies_direction() -> None:
    """(P3) When Tier-1 is inverted (IG scores WORSE than sub-IG) and the rated-vs-unrated fallback
    also fails, the scale direction is unverified → UNKNOWN, never a guessed direction."""
    s = cs.credit_health(_comps({("comps", "Credit Health Panel"): _credit_sheet_inverted_rated()}))
    assert s.status is ds.SourceStatus.UNKNOWN and "ambiguous" in (s.note or "")


def test_is_investment_grade_boundary() -> None:
    """(P3) IG classifier boundary: BBB and up are IG, BB and down sub-IG; unparseable → None."""
    assert cs._is_investment_grade("BBB-") is True and cs._is_investment_grade("A-") is True
    assert cs._is_investment_grade("AAA") is True
    assert cs._is_investment_grade("BB+") is False and cs._is_investment_grade("B") is False
    assert cs._is_investment_grade("CCC") is False and cs._is_investment_grade("D") is False
    assert cs._is_investment_grade("") is None and cs._is_investment_grade("NR") is None


def test_quarterly_yoy_requires_same_quarter_not_just_four_back() -> None:
    """(C2 fix) YoY is same-quarter ONLY. A duplicated/restated quarter makes 'four back' land on
    the WRONG quarter; the guard renders '—' rather than a cross-quarter number mislabelled 'YoY'.
    (The pre-fix code computed Q1-26÷Q2-25 and called it YoY.)"""
    q: list[list[typing.Any]] = [
        ["For the Fiscal Period",
         "3 months Q1 Mar-31-2025", "3 months Q2 Jun-30-2025", "3 months Q2 Jun-30-2025",
         "3 months Q3 Sep-30-2025", "3 months Q4 Dec-31-2025", "3 months Q1 Mar-31-2026"],
        ["Total Revenue", 90.0, 94.0, 94.0, 95.0, 96.0, 61.0],
        ["Gross Profit", 30.0, 31.0, 31.0, 32.0, 33.0, 20.0],
    ]
    s = cs.financial_summary_quarterly(_fin_bundle({"Income Statement": q}, freq="quarterly"))
    ft = s.value
    assert ft is not None
    qr = {r.label: r.cells for r in ft.rows}
    assert ft.columns.count("Q2-25") == 2      # the duplicate is visible in the header
    assert qr["Revenue YoY"][5] == "—"         # Q1-26 vs a Q2 four-back is NOT a YoY → suppressed


def test_financial_summary_annual_cf_duplicate_column_drops_to_dash() -> None:
    """(C4 fix) A DUPLICATE Cash-Flow fiscal-period column (a restated + an as-reported copy of one
    year) is ambiguous → its CF cell drops to '—' (fail loud), never silently keeps whichever landed
    last. The unambiguous years still match by (short, is_ltm) despite an IS/CF reclass gap."""
    inc: list[list[typing.Any]] = [
        ["For the Fiscal Period", "Reclassified 12 months Dec-31-2023", "12 months Dec-31-2024",
         "12 months Dec-31-2025"],
        ["Total Revenue", 350.0, 400.0, 430.0],
    ]
    cf: list[list[typing.Any]] = [  # FY23 as-reported (IS had it Reclassified) + FY24 TWICE
        ["For the Fiscal Period", "12 months Dec-31-2023", "12 months Dec-31-2024",
         "Reclassified 12 months Dec-31-2024", "12 months Dec-31-2025"],
        ["Cash from Ops.", 35.0, 999.0, 40.0, 45.0],
    ]
    b = _fin_est_bundle({"Income Statement": inc, "Cash Flow": cf}, {"Trends": _c1_trends()})
    ft = cs.financial_summary_annual(b, as_of="2026-05-15").value
    assert ft is not None
    cfo = {r.label: r.cells for r in ft.rows}["CFO ($M)"]
    assert cfo[0] == "35"   # FY23: IS-reclassified vs CF-as-reported still matches by period id
    assert cfo[1] == "—"    # FY24: duplicate CF column → ambiguous → fail loud, NOT 999 or 40
    assert cfo[2] == "45"   # FY25: unambiguous


def test_bs_posture_anchors_all_lines_to_the_cash_period() -> None:
    """(C3 fix) Every posture line is read AT the cash column's period (one as-of). A partial latest
    quarter (debt/TCL blank in the newest column) must NOT back-fill a stale prior-period value —
    the line is omitted, and net working capital is never stitched across two dates."""
    bs: list[list[typing.Any]] = [
        ["Balance Sheet as of:", "Dec-31-2025", "Mar-31-2026"],
        ["Total Cash & ST Investments", 120.0, 126.1],   # cash present in the latest (Mar-26)
        ["Total Debt", 320.0, ""],                    # debt BLANK latest → omit, not stale Dec-25
        ["Total Current Assets", 300.0, 310.0],
        ["Total Current Liabilities", 150.0, ""],         # TCL blank latest → NWC omitted
    ]
    v = cs.balance_sheet_posture(_fin_bundle({"Balance Sheet": bs}, freq="quarterly")).value or ""
    assert "as of Mar-26" in v and "cash & ST inv 126" in v  # anchored to the cash period
    assert "total debt" not in v                             # stale Dec-25 debt NOT back-filled
    assert "net working capital" not in v                    # never stitched across two dates


def test_twin_guard_keeps_legitimate_peer_twins() -> None:
    """(R2 fix) The self-referential guard must not DROP a legitimate other-company twin via a
    substring ticker match ('BA' in 'Alibaba', 'KO' in 'Kohl's') or a shared generic/industry lead
    ('General', 'First'/'Solar'). Whole-token matching + the denylist keep all four peers."""
    cases = [
        ("GE", "General Electric Company", "General Dynamics"),   # shared generic lead 'General'
        ("BA", "The Boeing Company", "Alibaba Group"),            # 'BA' is a substring of 'aliBAba'
        ("KO", "The Coca-Cola Company", "Kohl's Corporation"),    # 'KO' is a substring of 'KOhl's'
        ("FSLR", "First Solar, Inc.", "Canadian Solar Inc."),     # shared industry word 'Solar'
    ]
    for ticker, name, peer in cases:
        tw = ds.TwinCase(name=peer, outcome="went terminal", distinguishing_fact="x", source="fab")
        assert syn._self_referential_twin(tw, ticker, name) is False, f"{peer} wrongly dropped"
    # the true self-reference (subject named, no dated arc) is STILL caught
    selfref = ds.TwinCase(name="Boeing, again", outcome="the same overshoot",
                          distinguishing_fact="x", source="fab")
    assert syn._self_referential_twin(selfref, "BA", "The Boeing Company") is True


# --- PR D Phase 2: facts-first restructure (D1), merged trajectory (D2), deterministic bull/bear
# --- ordering (D3 + N1/N2/N3), caveat shape (D4), appendix riders (D5), twin rules (D6) ------


def _synth_min(bull: list[typing.Any], bear: list[typing.Any]) -> ds.Synthesis:
    return ds.Synthesis(
        evidence_balance="Mixed.", bull_points=bull, bear_points=bear, twin_reference_cases=[],
        decisive_question=ds.DecisiveQuestion(question="Does it reverse?", evidence_for=[],
                                              evidence_against=[]),
        key_unknowns=["CIQ not pulled"],
    )


def test_d1_section_order_facts_first() -> None:
    """(D1, re-pinned for the tier redesign) The rendered markdown is decision-logic ordered:
    caveats → what broke → survival → operating trajectory → valuation → peer comps → business
    quality → the argument (twins LAST) → appendix (reading guide … Record & reproduce closing).
    The old verdict footer is GONE — a third copy of the pivot statement."""
    dossier = ds.Dossier(
        ticker="X", name="X Co", cik="0", reference_date=date(2026, 6, 1), rank=1,
        mechanical=_minimal_mech(), synthesis=_synth_min([], []),
        caveats=["a caveat to verify"], qa_flags=[], llm_model="m",
        assembled_at=datetime(2026, 6, 1, 12, 0),
    )
    md = dr.render_markdown(dossier)

    def pos(s: str) -> int:
        assert s in md, f"missing section: {s}"
        return md.index(s)

    # (re-order 2026-07-27) DECISION order, not provenance order. Was: caveats first, the argument
    # last, everything wrapped in "## Mechanical layer" — a grouping by WHO PRODUCED the content.
    # The sequence now reads as the questions a decision asks, and with the wrapper gone these
    # section heads are H2. "Business quality" is the 2026-07-24 rename of "Ownership &
    # concentration", which carried no ownership; the real ownership data lives in the appendix.
    assert "## Mechanical layer" not in md, "the provenance wrapper must not come back"
    # The catalyst calendar and "The street" are ABSENT here by design — this minimal fixture
    # carries no calendar rows, no underwrite card and no catalyst_path, and each section omits
    # itself rather than printing an empty shell. Their placement is pinned on real committed
    # artifacts by test_analysis_tier_reads_in_decision_order_e2e below.
    assert "## Catalyst calendar" not in md and "## The street" not in md
    assert (pos("## What broke — and did it fall alone?") < pos("## Business quality")
            < pos("## The argument")
            < pos("## Valuation & own-history") < pos("## Peer comps")
            < pos("## Operating trajectory")
            < pos("## Leverage & survival") < pos("Analyst caveats"))
    assert (pos("### Bull case") < pos("### Bear case") < pos("### Decisive question")
            < pos("### Key unknowns") < pos("### Twin reference cases"))
    assert "The machine PROPOSES" not in md  # the verdict footer is retired
    assert pos("## How to read this dossier") < pos("### Management commentary") \
        < pos("## Record & reproduce"), "the appendix closes with Record & reproduce"


def test_d2_trajectory_table_merges_both_parents_no_drift() -> None:
    """(D2) 'Margin trend' + 'Multi-year trajectory' → ONE table (rev/EBITDA/margins/ROIC). Every
    parent row survives; ROIC (whose source omits the (R) marker) still fills the (R) column
    (period matched marker-insensitively); the footnote dedupes the repeated 'R reclassified'."""
    mt = ("EBITDA margin: Dec-31-2022 (R) -68% → Dec-31-2023 -28% → Dec-31-2024 1%; "
          "gross margin: Dec-31-2022 (R) 4% → Dec-31-2023 19% → Dec-31-2024 31%; "
          "absolute EBITDA: Dec-31-2022 (R) -140 → Dec-31-2023 -85 → Dec-31-2024 5; "
          "absolute revenue: Dec-31-2022 (R) 204 → Dec-31-2023 307 → Dec-31-2024 380  "
          "[R reclassified; read margin % with absolute EBITDA]")
    my = ("Revenue: Dec-31-2022 (R) 204 → Dec-31-2023 307 → Dec-31-2024 380; "
          "EBITDA: Dec-31-2022 (R) -140 → Dec-31-2023 -85 → Dec-31-2024 5; "
          "Revenue YoY (latest same-quarter): -25.5% (Q1 vs Q1); "
          "ROIC: Dec-31-2022 -12.3% → Dec-31-2023 -8.7% → Dec-31-2024 -2.2%  "
          "[R reclassified; per-period values]")
    base = _minimal_mech()
    q = base.quality.model_copy(update={
        "margin_trend": ds.Sourced.present(mt, source_ref="CIQ IS"),
        "multi_year_trajectory": ds.Sourced.present(my, source_ref="CIQ IS"),
    })
    md = "\n".join(dr._trajectory_table_lines(base.model_copy(update={"quality": q})))
    for lbl in ("Revenue ($M)", "EBITDA ($M)", "EBITDA margin", "Gross margin", "ROIC"):
        assert f"| {lbl} " in md, lbl                       # every parent row survived, merged
    roic = next(ln for ln in md.splitlines() if ln.startswith("| ROIC "))
    assert "-12.3%" in roic and "–" not in roic  # ROIC fills the (R) column
    rev = next(ln for ln in md.splitlines() if ln.startswith("| Revenue ($M) "))
    assert "204" in rev and "307" in rev and "380" in rev  # zero value drift vs the parents
    assert md.count("R reclassified") == 1                 # (N6) footnote fragment deduped
    assert "-25.5%" in md                                  # the same-quarter YoY footnote


def test_d3_point_tier_classification_and_ordering() -> None:
    """(D3 + N1/N2) tier from the claim (concession stripped first, N1); adjusted-EBITDA-negative
    → T1 (N2); a multi-tier claim takes the HIGHEST tier; unclassifiable → 4.5; ties keep emission
    order (stable)."""
    tier = dr._point_tier
    # N1: classify on the PRIMARY assertion — the T1 'Debt/EBITDA' sits after 'posing whether'/'but'
    peer = ("screens BETTER than peer median — EBITDA margin 14% and EBITDA growth 21% — posing "
            "whether the discount is residual; but Debt/EBITDA 5.8 vs 2.0")
    assert tier(peer) == 2.0                                          # 'growth' (T2) wins
    assert tier("GAAP profit is an illusion; adjusted EBITDA was negative $5.5M") == 1.0  # N2
    assert tier("net-debt/EBITDA 3.9x against a falling margin") == 1.0  # highest tier wins
    assert tier("a governance dispute with the board") == 4.5           # unclassifiable

    class _P:
        def __init__(self, claim: str, ref: str, cited: bool = True) -> None:
            self.claim, self.source_ref, self.cited = claim, ref, cited

    pts = [
        _P("valuation looks cheap on every multiple", "CIQ Multiples"),   # T5
        _P("levered free cash flow is positive", "CIQ Cash Flow"),        # T1
        _P("net profit is non-operating", "CIQ transcript(s): call"),     # T3, transcript
        _P("interest coverage is 10x", "CIQ IS"),                          # T1
    ]
    order = [p.claim[:8] for p, *_ in dr._ordered_points(pts, side="bear")]
    assert order == ["levered ", "interest", "net prof", "valuatio"]  # T1 → T3 → T5 (stable)
    # (hybrid) the BULL side demotes the balance-sheet ENABLER below the mechanism tiers:
    # bull rank 2→3→1→4→4.5→5, so T3 leads and the two T1s follow (stable), valuation last.
    bull = [p.claim[:8] for p, *_ in dr._ordered_points(pts, side="bull")]
    assert bull == ["net prof", "levered ", "interest", "valuatio"]


def test_d3_hybrid_crux_mech_and_bear_survival_guarantee() -> None:
    """(D3 hybrid, ratified 2026-07-24 on the 119-draw archive) The asymmetric sort:
    bull = (crux, side-rank, mech, citation, emission) — the crux-linked thesis LEADS, and the
    balance-sheet enabler is demoted; bear = (side-rank, crux, mech, citation, emission) — a T1
    survival fact is NEVER demoted below a narrative crux point (the guarantee that made hybrid
    beat crux-dominant A, which demoted survival in ~1 of 5 archive draws). Deterministic
    synthetic fixture — value-level pins are safe here."""

    class _P:
        def __init__(self, claim: str, ref: str) -> None:
            self.claim, self.source_ref, self.cited = claim, ref, True

    crux = frozenset({"REF-CRUX", "REF-CRUX-2"})
    drivers = frozenset({"REF-DRV"})
    bull_pts = [
        _P("interest coverage is 10x and net-debt low", "CIQ IS"),        # T1 enabler, no crux
        _P("valuation looks cheap vs the trough", "REF-CRUX"),            # T5 but CRUX-linked
        _P("revenue re-accelerated 12% on volumes", "REF-DRV"),           # T2, mechanism-bearing
        _P("revenue guide raised for FY27", "CIQ Estimates"),             # T2, plain
    ]
    got = [(p.claim[:8], cx, mb) for p, _t, _c, cx, mb
           in dr._ordered_points(bull_pts, side="bull", crux_refs=crux, driver_refs=drivers)]
    # crux first (even a T5); then T2 mech beats T2 plain; the T1 enabler sinks below both T2s
    assert got == [("valuatio", True, False), ("revenue ", False, True),
                   ("revenue ", False, False), ("interest", False, False)]

    bear_pts = [
        _P("a governance dispute over the impairment", "REF-CRUX"),       # T4.5 narrative, CRUX
        _P("free cash flow is negative and burning", "CIQ CF"),           # T1 survival
        _P("margin structure is compressing", "REF-CRUX-2"),              # T3, CRUX
        _P("opex base is bloated at the mid", "CIQ Estimates"),           # T3, plain
    ]
    order = [p.claim[:8] for p, *_ in dr._ordered_points(
        bear_pts, side="bear", crux_refs=crux, driver_refs=drivers)]
    # THE GUARANTEE: T1 survival leads even though it is not crux-linked; within the T3 pair the
    # crux-linked one wins; the crux-linked T4.5 narrative stays BELOW every classified tier.
    assert order == ["free cas", "margin s", "opex bas", "a govern"]


def test_point_tier_paren_needs_accounting_dollar() -> None:
    """(fix-4 narrowing, SMPL regression) The K6 '(' alternative fired on ANY parenthetical within
    40 chars of 'adjusted EBITDA' — SMPL's bear lead 'adjusted EBITDA -18.4%, with gross margin
    31.6% (-460bps)' classified T1 by accident (a DECLINE, not negative EBITDA; its honest tier is
    T2 via 'deteriorat'). Now '(' counts only when it opens an accounting-$ amount."""
    smpl = ("The mechanism is deteriorating in-market: Q2 net sales fell 9.4% and adjusted "
            "EBITDA -18.4%, with gross margin 31.6% (-460bps), driven by cocoa/whey/tariff "
            "inflation")
    assert dr._point_tier(smpl) == 2.0  # 'deteriorat' — no longer an accidental T1
    assert dr._point_tier("adjusted EBITDA of ($5.5) million for the quarter") == 1.0  # accounting
    assert dr._point_tier("adjusted EBITDA of $(5.5) million for the quarter") == 1.0  # $-first too
    assert dr._point_tier("adjusted EBITDA swung to -$5.5M") == 1.0                    # -$ kept
    assert dr._point_tier("adjusted EBITDA was negative in Q1") == 1.0                 # word kept


def test_d4_caveat_full_sentence_four_part_shape() -> None:
    """(D4) A guardrail caveat renders the FULL offending sentence (no mid-claim truncation) in the
    what/where/why-it-matters/how-to-verify shape; a mechanical caveat stays one full bullet."""
    claim = ("the name trades at a steep discount to its peer group on every multiple which "
             "implies a mean-reversion opportunity the market is currently mispricing outright")
    cav = (f"Bare peer-comparison (a bull point): '{claim}' — presents cheap/rich vs peers as a "
           "verdict without the earned-vs-residual decomposition; POSE justified-vs-residual")
    md = "\n".join(dr._caveat_block(cav))
    assert claim in md                                          # untruncated, in full
    assert "_where:_ a bull point" in md
    assert "_why it matters:_" in md and "decomposition" in md
    assert "_how to verify:_ POSE justified-vs-residual" in md
    mech = dr._caveat_block("Net debt/EBITDA (3.9x) is on reported EBITDA — verify the basis.")
    assert mech == ["- Net debt/EBITDA (3.9x) is on reported EBITDA — verify the basis."]


def test_d4_synthesis_emits_full_claim_no_snip() -> None:
    """(D4) The human guardrail caveats no longer _snip the claim — a long offending sentence
    the caveat in full (truncation is retained only for the dev-only QA flags)."""
    pc = _fake_peer_comps()  # comparability + a traceable trading-multiples source_ref (→ cited)
    mech = _minimal_mech().model_copy(update={"peer_comps": pc})
    long_claim = ("The name trades cheap versus its peer median on EV/EBITDA and on virtually all "
                  "other trading multiples, a widening discount the market keeps on mispricing")
    payload = {
        "bull_points": [{"claim": long_claim, "source_ref": pc.trading_multiples.source_ref}],
        "bear_points": [], "twin_reference_cases": [],
        "decisive_question": {"question": "?", "evidence_for": [], "evidence_against": []},
        "key_unknowns": [],
    }
    _synth, flags, _ = syn.synthesize(mech, llm=_FakeLlm(payload), ticker="FUBO", name="FuboTV")
    bare = next((f for f in flags if f.startswith("PEER-COMP-BARE")), None)
    assert bare is not None and long_claim in bare  # the full sentence, not a '…'-snipped prefix


def test_d5a_eps_absent_basis_renders_dash_never_borrows() -> None:
    """(D5a, condition c) GAAP EPS present but Normalized absent from Trends → the Normalized E cell
    is '—' and NEVER borrows the GAAP figure; each row reads its OWN basis."""
    inc: list[list[typing.Any]] = [
        ["For the Fiscal Period", "12 months Dec-31-2024", "12 months Dec-31-2025"],
        ["Total Revenue", 400.0, 430.0], ["EBITDA", 50.0, 74.0], ["Net Income", -196.0, -29.0],
        ["Diluted EPS", -0.61, -0.09], ["Normalized Diluted EPS", -0.22, 0.00],
    ]
    trends: list[list[typing.Any]] = [  # EPS (GAAP) present, NO 'EPS Normalized' block
        ["EPS (GAAP)", "", ""], ["Company Level (USD)", "FY 2026", "FY 2027"],
        ["Current", 0.18, 0.17],
    ]
    ft = cs.financial_summary_annual(
        _fin_est_bundle({"Income Statement": inc}, {"Trends": trends}), as_of="2026-05-15").value
    assert ft is not None
    row = {r.label: r.cells for r in ft.rows}
    assert row["EPS (GAAP, dil.)"][-2:] == ["0.18", "0.17"]
    assert row["EPS (Normalized)"][-2:] == ["—", "—"]  # absent → '—', not the borrowed 0.18


def test_d6_twin_single_entity_guard() -> None:
    """(D6a) A twin must be ONE company: a '/'-joined pair or a 'cohort' is DROPPED with a QA
    flag; an '&' name (AT&T) is a legitimate single entity → FLAGGED for QA but RENDERED."""
    def tw(n: str) -> ds.TwinCase:
        return ds.TwinCase(name=n, outcome="terminal", distinguishing_fact="x",
                           source="[LLM-suggested, unverified]")
    synth = ds.Synthesis(
        evidence_balance="", bull_points=[], bear_points=[],
        twin_reference_cases=[tw("SunPower / First Solar cohort"), tw("AT&T"), tw("SolarEdge")],
        decisive_question=ds.DecisiveQuestion(question="?", evidence_for=[], evidence_against=[]),
        key_unknowns=[])
    validated, flags = syn._validate(synth, _minimal_mech(), ticker="MVST",
                                     name="Microvast Holdings, Inc.")
    assert [t.name for t in validated.twin_reference_cases] == ["AT&T", "SolarEdge"]  # dropped
    _, qa = dflags.partition(flags)
    assert any("compound 'SunPower" in f for f in qa)      # the '/'+cohort drop is dev-only QA
    assert any("ampersand-name 'AT&T'" in f for f in qa)   # AT&T flagged for QA but KEPT


def test_twin_outcome_marks_llm_claimed_but_leaves_sourced_plain() -> None:
    """(H6) An '[LLM-suggested, unverified]' twin's outcome is the MODEL's claim → rendered
    'outcome (LLM-claimed — verify)'; a roster/self-sourced twin renders plain. Deterministic,
    render-side. Pins the QuantumScape shape (a common LLM-suggested EV/battery analogue)."""
    qs = ds.TwinCase(name="QuantumScape", outcome="terminal — dilution spiral",
                     distinguishing_fact="pre-revenue vs MVST shipping",
                     source="[LLM-suggested, unverified]")
    peer = ds.TwinCase(name="Amprius", outcome="recovered", distinguishing_fact="same peer set",
                       source="CIQ peer roster (Comparable Analysis)")
    assert dr._twin_outcome(qs) == "terminal — dilution spiral (LLM-claimed — verify)"
    assert dr._twin_outcome(peer) == "recovered"  # sourced → plain, no suffix
    # end-to-end through the synthesis render: the suffix appears on the QS line, not the peer line
    synth = ds.Synthesis(
        evidence_balance="", bull_points=[], bear_points=[], twin_reference_cases=[qs, peer],
        decisive_question=ds.DecisiveQuestion(question="?", evidence_for=[], evidence_against=[]),
        key_unknowns=[])
    doss = ds.Dossier(
        ticker="MVST", name="Microvast", cik="0", reference_date=date(2026, 6, 1), rank=1,
        mechanical=_minimal_mech(), synthesis=synth, caveats=[], qa_flags=[], llm_model="m",
        assembled_at=datetime(2026, 6, 1, 12, 0))
    md = dr.render_markdown(doss)
    assert "**QuantumScape** — terminal — dilution spiral (LLM-claimed — verify)" in md
    assert "**Amprius** — recovered\n" in md and "Amprius** — recovered (LLM" not in md


def test_exhibit_primitives_edge_cases_node() -> None:
    """(refactor) lib/exhibit.js — the shared exhibit primitives — pinned across the scenarios the
    hand-rolled per-exhibit math kept getting wrong: the coarse nice-ceiling that jumped 592->1000
    and compressed the bars; the phantom zero-side tick on an all-positive margin / all-negative
    ROIC; the Math.min(...[])->Infinity empty trap; the log non-positive fallback; sign-aware label
    placement. Node-gated (browser engine); a static test pins the contract when node is off."""
    import json
    import shutil
    import subprocess
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    url = Path("frontend/lib/exhibit.js").resolve().as_uri()
    driver = f"""
import {{ nums, extent, niceCeil, linScale, logScale, barDomain, lineDomain, labelAnchor,
  barLabelY }} from "{url}";
const r = {{}};
r.niceCeil = {{ c592: niceCeil(592), c651: niceCeil(651), c979: niceCeil(979),
  c1077: niceCeil(1077), c1000: niceCeil(1000), c1001: niceCeil(1001),
  c6: niceCeil(6), c0: niceCeil(0), cneg: niceCeil(-5) }};
r.extent = {{ empty: extent([]), nulls: extent([null, null]), single: extent([5]),
  mixed: extent([3, null, -2, NaN, 7]), notArray: extent(null) }};
r.bar = {{ allPos: barDomain([204, 592]), mixed: barDomain([-140, 592]),
  allNeg: barDomain([-200, -50]), single: barDomain([500]),
  empty: barDomain([]), allZero: barDomain([0, 0]) }};
r.line = {{ allPos: lineDomain([13, 16], {{ padFrac: 0.2, minPad: 2 }}),
  mixed: lineDomain([-68, 25], {{ padFrac: 0.2, minPad: 2 }}),
  allNeg: lineDomain([-30, -5], {{ padFrac: 0.14 }}),
  flatPos: lineDomain([8, 8], {{ padFrac: 0.14, minSpan: 2 }}),
  allZero: lineDomain([0, 0], {{ padFrac: 0.2, minPad: 2, minSpan: 2 }}),
  empty: lineDomain([], {{}}) }};
const s = linScale(0, 100, 200, 0);
r.lin = {{ at0: s(0), at50: s(50), at100: s(100), degenerate: linScale(5, 5, 0, 10)(5) }};
r.log = {{ positive: logScale(1, 100, 0, 100) != null, nonPositive: logScale(-1, 100, 0, 100),
  zeroLo: logScale(0, 100, 0, 100), mid: logScale(1, 100, 0, 2)(10) }};
r.label = {{ left: labelAnchor(10, 50), right: labelAnchor(90, 50),
  pos: barLabelY(100, false), neg: barLabelY(100, true) }};
console.log(JSON.stringify(r));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    r = json.loads(out.stdout)

    # niceCeil — FINE steps: 592→600 (not 1000, the compressed-bars bug); guards 0/negative → 1
    assert r["niceCeil"] == {"c592": 600, "c651": 700, "c979": 1000, "c1077": 1100,
                             "c1000": 1000, "c1001": 1100, "c6": 6, "c0": 1, "cneg": 1}
    # extent — empty/all-null/non-array -> null (never Infinity from Math.min(...[])); NaN filtered
    assert r["extent"] == {"empty": None, "nulls": None, "single": [5, 5],
                           "mixed": [-2, 7], "notArray": None}
    # barDomain — always spans zero; empty -> null; all-zero -> [0,1] not [0,0]
    assert r["bar"]["allPos"] == {"lo": 0, "hi": 700}
    assert r["bar"]["mixed"] == {"lo": -180, "hi": 700}
    assert r["bar"]["allNeg"] == {"lo": -250, "hi": 0}
    assert r["bar"]["single"] == {"lo": 0, "hi": 600}
    assert r["bar"]["empty"] is None
    assert r["bar"]["allZero"] == {"lo": 0, "hi": 1}
    # lineDomain — THE phantom-tick regression pins: an all-positive series floors at EXACTLY 0 (no
    # phantom negative); an all-negative series caps at EXACTLY 0 (no phantom positive).
    assert r["line"]["allPos"]["lo"] == 0 and r["line"]["allPos"]["hi"] == pytest.approx(19.2)
    assert r["line"]["allNeg"]["hi"] == 0 and r["line"]["allNeg"]["lo"] == pytest.approx(-34.2)
    assert r["line"]["mixed"]["lo"] == pytest.approx(-86.6)
    assert r["line"]["mixed"]["hi"] == pytest.approx(43.6)
    assert r["line"]["flatPos"]["lo"] == 0 and r["line"]["flatPos"]["hi"] == pytest.approx(9.12)
    # minSpan guards an all-zero (degenerate) series → a real span, never a divide-by-zero [0,0]
    assert r["line"]["allZero"] == {"lo": -1, "hi": 1}
    assert r["line"]["empty"] is None
    # linScale maps domain->range (degenerate domain -> range midpoint, never divide-by-zero)
    assert r["lin"] == {"at0": 200, "at50": 100, "at100": 0, "degenerate": 5}
    # logScale: a fn for a positive domain, null otherwise (caller falls back to linear); the
    # log-midpoint of 1..100 is 10 -> range midpoint
    assert r["log"]["positive"] is True
    assert r["log"]["nonPositive"] is None and r["log"]["zeroLo"] is None
    assert r["log"]["mid"] == pytest.approx(1.0)
    # sign-aware placement: label ABOVE a positive bar / BELOW a negative one
    assert r["label"] == {"left": "start", "right": "end", "pos": 96, "neg": 111}


def test_return_ratios_exhibit_no_phantom_negative_tick_e2e() -> None:
    """(#106 TEST-LAYER RULE; moved off the removed ROIC-trend exhibit) e2e WIRING pin: render a
    committed dossier whose return ratios are ALL POSITIVE (IT) through renderDossier and assert the
    return-ratios SVG draws NO negative % anywhere — the axis floors at 0 (no phantom negative tick,
    the bug lineDomain fixes). Catches the exhibit reverting to inline zero-padding, which the
    primitive-level lineDomain test would NOT. Phrasing-independent: asserted only when the
    committed series is all-positive (derived from the artifact)."""
    import json
    import shutil
    import subprocess
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    doss = Path("data/dossiers/IT/dossier.json")
    if not doss.exists():
        pytest.skip("no committed IT dossier")
    rr = (json.loads(doss.read_text()).get("mechanical", {}) or {}).get("return_ratios")
    if not rr or rr.get("status") != "present":
        pytest.skip("IT return_ratios absent")
    vals = [v for row in rr["value"]["rows"] for v in (row.get("values") or []) if v is not None]
    if not vals or not all(v > 0 for v in vals):
        pytest.skip("IT return ratios not all-positive — invariant N/A")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const html = renderDossier(JSON.parse(readFileSync("data/dossiers/IT/dossier.json")), null);
const m = html.match(/<svg[^>]*aria-label="Return ratios[\\s\\S]*?<\\/svg>/);
console.log(JSON.stringify({{ found: !!m, svg: m ? m[0] : "" }}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    res = json.loads(out.stdout)
    assert res["found"], "IT return-ratios exhibit did not render"
    # the invariant: an all-positive ratio panel draws NO negative percentage anywhere (the phantom
    # tick was "-2%"); the axis floors at 0.
    assert not re.search(r"-\d+(\.\d+)?%", res["svg"]), "phantom tick on all-positive ratios"


def test_exhibit_module_static_contract_no_node() -> None:
    """(refactor) When node is absent the primitive pins above skip — so pin lib/exhibit.js's
    CONTRACT by source inspection, NODE-FREE (mirrors the web-cite static backstop): the exports the
    exhibits consume, the fail-loud / honest-axis rules, and the no-CONCLUDE guardrail — this module
    ships NO trendline / regression / extrapolation / projection primitive (a fitted or forward mark
    would be the machine concluding). Catches a rename or a guardrail edit even without node."""
    src = Path("frontend/lib/exhibit.js").read_text()
    # the public surface the exhibits import — a silent rename here breaks a chart
    for name in ["export const nums", "export function extent", "export function niceCeil",
                 "export function linScale", "export function logScale",
                 "export function barDomain", "export function lineDomain",
                 "export const labelAnchor", "export const barLabelY"]:
        assert name in src, f"exhibit.js must export {name!r} (an exhibit imports it)"
    # fail-loud: extent returns null (never Infinity) when there are no values
    assert "return v.length ? [Math.min(...v), Math.max(...v)] : null" in src
    # honest LINE axis — pad beyond zero ONLY on a real side, both directions
    assert "if (rHi > 0) hi += pad" in src and "if (rLo < 0) lo -= pad" in src
    # honest BAR axis — one-sided nice ceiling, so the domain always spans zero
    assert "hi > 0 ? niceCeil(hi * head)" in src and "lo < 0 ? -niceCeil(-lo * head)" in src
    # the FINE nice-steps that fixed 592→1000 (not the coarse 1/2/2.5/5/10 grid)
    assert "1.1, 1.2, 1.5, 1.8" in src
    # no-conclude guardrail: the note NAMES the forbidden primitives ...
    low = src.lower()
    assert "deliberately absent" in low
    for banned in ("trendline", "regression", "extrapolat", "projection"):
        assert banned in low, f"the no-conclude note must name {banned!r} as forbidden"
    # ... AND the module actually ships none of them (guard against a later well-meaning addition)
    for banned_fn in ("export function trendline", "export function regress",
                      "export function forecast", "export function project", "export function fit"):
        assert banned_fn not in src, f"exhibit.js must NOT export {banned_fn!r} (concluding)"
    # the wiring is real: dossier.js imports this module and drives the exhibits through it
    dj = Path("frontend/views/shared/dossier.js").read_text()
    assert 'from "../../lib/exhibit.js"' in dj
    assert "barDomain(" in dj and "lineDomain(" in dj and "linScale(" in dj


def test_exhibits_cite_via_endnotes_not_inline_source_caption() -> None:
    """(RULE) An SVG exhibit's provenance goes to the tier's Sources list via a citeMark endnote —
    NEVER an inline 'Source: …' caption under the chart. The exhibit's data is already cited by its
    sibling table/fact (financial_summary / range_position / trajectory), so a caption duplicates
    the source in the wrong tier. Regressed on rev/EBITDA, own-history AND ROIC — each grew one — so
    guard it: a citeMark renders '[n]', never a '>Source:' label."""
    src = Path("frontend/views/shared/dossier.js").read_text()
    assert ">Source:" not in src, (
        "an exhibit inlines a 'Source:' caption — remove it; the sibling table/fact's citeMark "
        "carries the source to the Sources list (see revEbitdaExhibit for the pattern)")


def test_dossier_page_logs_anchor_and_scenario_panels() -> None:
    """(log · tier redesign) The dossier Brief carries the committed screening context (inside the
    Scenario analysis card) for any dossier that has one, and the underwrite masthead/detail ONLY
    when a scenario record is passed.

    Additive both ways: a dossier with no `anchor` renders no screening block (pre-anchor JSON is
    untouched), and the stat band never appears from the 2-arg call the other node pins use — it
    needs a fetch, so render() supplies it. Node-gated like the other render pins."""
    import json
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node not available")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const rd = (p) => JSON.parse(readFileSync(p));
const withAnchor = rd("data/dossiers/IT/dossier.json");
// The no-anchor case is CONSTRUCTED, never borrowed from whichever ticker happens to lack a block
// today: this was pinned to FUBO and went red the moment FUBO earned one (2026-07-21, the R2
// cohort backfill). The invariant under test — "an absent anchor renders nothing" — is a property
// of the RENDERER; binding it to a live ticker made it a property of the queue instead.
const noAnchor = {{ ...withAnchor, anchor: null }};
const card = rd("frontend/scenarios/IT.json");
console.log(JSON.stringify({{
  anchorPanel: renderDossier(withAnchor, null)
    .includes("Screening context — how this name surfaced"),
  anchorNotVerdict: renderDossier(withAnchor, null).includes("not a verdict"),
  anchorAbsent: renderDossier(noAnchor, null)
    .includes("Screening context — how this name surfaced"),
  cardWithout: renderDossier(withAnchor, null).includes("uw-statband"),
  cardWith: renderDossier(withAnchor, null, card).includes("uw-statband"),
}}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    r = json.loads(out.stdout)
    assert r["anchorPanel"], "committed anchor did not render its screening panel"
    assert r["anchorNotVerdict"], "the anchor panel must label itself 'not a verdict'"
    assert not r["anchorAbsent"], "a dossier without an anchor must render no anchor panel"
    assert not r["cardWithout"], "the underwrite card must not appear without a scenario record"
    assert r["cardWith"], "a passed scenario record must render the underwrite card"


def test_verify_first_skips_resolved_caveats_and_keeps_genuine_ones() -> None:
    """(regression — VRRM, 2026-07-21) A RESOLVED caveat is the record of a check that PASSED; it
    must never fire the Brief's conditional warning strip. VRRM's "RESOLVED (P/E basis)" did —
    'basis' matched the decision keywords — so both renderers now skip the RESOLVED prefix.
    Frozen-fixture unit pins (md) + a source pin (web guard present)."""
    resolved = "RESOLVED (P/E basis) — trailing GAAP P/E 5.1x is one-time-distorted"
    genuine = "Net debt/EBITDA (3.8x) is on REPORTED EBITDA, not the covenant basis; verify"
    noise = "primary-source: 1 EX-99.1 release(s) + 1 10-Q parsed (+0.1s fetch)"
    assert dr._brief_verify_first([resolved]) == [], "a RESOLVED caveat fired the warning"
    kept = dr._brief_verify_first([resolved, genuine, noise])
    assert len(kept) == 1 and kept[0].startswith("Net debt/EBITDA"), (
        "the genuine leverage caveat must still fire (lead clause only)")
    # the web guard mirrors it (node-free source pin; the shared regex class is per-renderer)
    js = Path("frontend/views/shared/dossier.js").read_text()
    import re as _re
    fn = _re.search(r"function briefVerifyFirst\(.*?\n\}", js, _re.S)
    assert fn and _re.search(r"/\^RESOLVED\\b/i\.test\(c\)", fn.group(0)), (
        "web briefVerifyFirst must skip RESOLVED caveats")


def test_opener_narrative_slot_rationale_once_and_conditional_warning_node() -> None:
    """(tier redesign e2e, re-pinned for the buy-side cover) TWO structural invariants of the
    Brief, phrasing-independent:

    1. NARRATIVE ONCE, THESIS-FIRST — with an underwrite record carrying a recorded rationale
       (IT), the Brief renders the analyst's words EXACTLY ONCE, as the THESIS block leading the
       narrative column (before the About heading), and NO machine 'Assessment' label. A pending
       name (EPAM) renders exactly one 'Assessment' and no thesis block — the machine read is
       never titled as a thesis (authorship stays marked).
    2. CONDITIONAL WARNING — on a FROZEN synthetic dossier, a decision-keyword caveat fires the
       strip once; a RESOLVED caveat and a process caveat fire nothing (living-artifact caveats
       re-word on every assembly, so the strip's fixture is synthetic by the TEST-LAYER rule)."""
    import json
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node not available")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const rd = (p) => JSON.parse(readFileSync(p));
const count = (h, n) => h.split(n).length - 1;
const it = renderDossier(rd("data/dossiers/IT/dossier.json"), null,
  rd("frontend/scenarios/IT.json"));
const epam = renderDossier(rd("data/dossiers/EPAM/dossier.json"), null,
  rd("frontend/scenarios/EPAM.json"));
const bare = {{ ticker: "X", name: "X Co", cik: "0", reference_date: "2026-06-01",
  assembled_at: "2026-06-01T12:00:00", mechanical: {{}}, synthesis: null }};
const warn = renderDossier({{ ...bare, caveats: ["leverage covenant basis — check it"] }}, null);
const clean = renderDossier({{ ...bare, caveats: [
  "RESOLVED (P/E basis) — one-time distortion, verified",
  "primary-source: 0 EX-99.1 release(s) + 1 10-Q parsed (+0.1s fetch)"] }}, null);
console.log(JSON.stringify({{
  itThesis: count(it, 'class="brief-thesis"'),
  itThesisFirst: it.indexOf("Thesis — our rationale") >= 0
    && it.indexOf("Thesis — our rationale") < it.indexOf("About the company"),
  itAssessment: count(it, ">Assessment</div>"),
  epamAssessment: count(epam, ">Assessment</div>"),
  epamThesis: count(epam, 'class="brief-thesis"'),
  warnFires: count(warn, "uw-warn"),
  cleanFires: count(clean, "uw-warn"),
}}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    r = json.loads(out.stdout)
    assert r["itThesis"] == 1 and r["itAssessment"] == 0, (
        "a logged name must carry the analyst's rationale EXACTLY once, as the thesis block")
    assert r["itThesisFirst"], "the thesis must lead the narrative column, above About"
    assert r["epamAssessment"] == 1 and r["epamThesis"] == 0, (
        "a pending name carries the machine assessment once and never a thesis block")
    assert r["warnFires"] == 1, "a decision-keyword caveat must fire the warning strip once"
    assert r["cleanFires"] == 0, "RESOLVED + process caveats must fire nothing"


def test_financial_summary_extraction_is_not_windowed() -> None:
    """(full-history) The EXTRACTOR must keep every exported period — a display window applied at
    extraction put five-plus fiscal years and up to 33 quarters beyond recovery (the licensed
    workbook is the only other copy, and the deployed surface has none). Source pins: the old
    `fy[-4:]` / `[-8:]` slices are gone, and the committed records now carry more than the old
    window on at least one name."""
    src = Path("vinci/dossier/ciq_sheets.py").read_text()
    assert "disp = fy[-4:]" not in src, "the annual extractor must not window at extraction"
    assert "_fin_periods(rows[hdr])[-8:]" not in src, "the quarterly extractor must not window"
    assert "disp = fy + ltm[:1]" in src
    wide = 0
    for jp in sorted(Path("data/dossiers").glob("*/dossier.json")):
        fs = json.loads(jp.read_text())["mechanical"].get("financial_summary") or {}
        ann = (fs.get("annual") or {}).get("value") or {}
        if len(ann.get("columns") or []) > 7:      # 4 FY + LTM + 2 estimates was the old ceiling
            wide += 1
    assert wide >= 5, f"expected the widened history on most committed dossiers, got {wide}"


def test_brief_windows_the_annual_table_and_states_what_it_hides() -> None:
    """(full-history) The BRIEF curates at the RENDER layer — last 4 actual FY + LTM + consensus —
    and NAMES the hidden count; the Appendix and the JSON keep every exported year. This is the
    inversion of the old bug: curate the view, never the record."""
    import re as _re

    d = ds.Dossier.model_validate_json(Path("data/dossiers/IT/dossier.json").read_text())
    tbl = d.mechanical.financial_summary.annual.value        # type: ignore[union-attr]
    assert tbl is not None and len(tbl.columns) > 7, "IT should carry its full exported history"
    idx = dr._brief_window(tbl)
    kept = [tbl.columns[i] for i in idx]
    actual = [c for c in kept
              if not str(c).upper().startswith("LTM") and not str(c).endswith("E")]
    assert len(actual) == dr._BRIEF_FY, f"the brief must show {dr._BRIEF_FY} actual FY, got {kept}"
    assert any(str(c).upper().startswith("LTM") for c in kept), "LTM must survive the window"
    md = dr.render_markdown(d)
    brief, appendix = md.split("# Analysis")[0], md.split("# Appendix")[1]
    assert _re.search(r"table shows the last \d+ fiscal years · \d+ earlier years? "
                      r"(is|are) in the Appendix", brief), (
        "the brief must state how many years it hid — never a silent window")
    assert "FY17" in appendix and "FY17" not in brief, (
        "the full history belongs in the Appendix, not the first cut")


def test_financials_backfill_refuses_a_newer_workbook() -> None:
    """(full-history · vintage guard) The backfill widens a WINDOW; it must never silently refresh
    VALUES. CIQ stamps no export date and the '≥' as-of is a floor, so a re-exported workbook is
    otherwise undetectable — and refreshing numbers under a synthesis written against the old ones
    makes a dossier cite figures it no longer contains. A committed cell that was '—' only because
    nothing preceded it is exempt: that derivation became computable, it was not restated."""
    committed = {"annual": {"value": {
        "columns": ["FY24", "FY25", "LTM"],
        "rows": [{"label": "Revenue ($M)", "cells": ["100", "110", "115"]},
                 {"label": "Revenue growth", "cells": ["—", "+10%", "— (basis)"]}]}}}
    # widened only: the committed series is the exact tail, and the leading '—' becomes computable
    widened = {"annual": {"value": {
        "columns": ["FY22", "FY23", "FY24", "FY25", "LTM"],
        "rows": [{"label": "Revenue ($M)", "cells": ["80", "90", "100", "110", "115"]},
                 {"label": "Revenue growth",
                  "cells": ["—", "+13%", "+11%", "+10%", "— (basis)"]}]}}}
    assert cli._fs_value_drift(committed, widened) == [], (
        "widening + a newly-computable derivation must NOT be reported as drift")
    # a genuine restatement of an existing number IS drift
    refreshed = json.loads(json.dumps(widened))
    refreshed["annual"]["value"]["rows"][0]["cells"][-1] = "119"      # LTM restated
    drift = cli._fs_value_drift(committed, refreshed)
    assert drift and "LTM" in drift[0] and "'115'" in drift[0], drift
    # duplicate period labels must not confuse the comparison (BRBR's quarterly reads FY24 ×3)
    dup_c = {"annual": {"value": {"columns": ["FY24", "FY24"],
                                  "rows": [{"label": "R", "cells": ["1", "2"]}]}}}
    dup_f = {"annual": {"value": {"columns": ["FY23", "FY24", "FY24"],
                                  "rows": [{"label": "R", "cells": ["0", "1", "2"]}]}}}
    assert cli._fs_value_drift(dup_c, dup_f) == [], (
        "positional compare must survive duplicate labels")


def test_display_transforms_read_plain() -> None:
    """(declutter P3) The display transforms turn machine dialect into reader register — display
    ONLY, dossier.json untouched. Frozen-string pins; each transform has a JS twin in dossier.js
    (source-pinned below)."""
    assert dr._fmt_insider(
        "Open-market buys 1 · sells 0 (net +0.1K sh) · grants 0 · last 2026-07-06 · "
        "other F×46/G×6/J×34/M×56"
    ).endswith("other filings 142")
    # a string with no code tail passes through verbatim
    assert dr._fmt_insider("Open-market buys 2 · sells 1") == "Open-market buys 2 · sells 1"
    dump = ("A Co (KOSE:X) — The Name · Client Services · src: Banks; "
            "B Co (IBSE:Y) — The Name Sub · Client Services · src: Software")
    out = dr._fmt_customers(dump)
    assert "2 mapped client relationship(s)" in out and "src:" not in out
    assert dr._fmt_customers("top customer 28% of revenue") == "top customer 28% of revenue"
    assert dr._fmt_shape("discrete gap-downs — 2026-02-03 earnings (2.02) + Reg-FD (7.01)") == \
        "discrete gap-downs — 2026-02-03 earnings + Reg-FD"
    assert dr._fmt_guide_verification(
        "guide verification (revenue): CIQ 6405.0–6405.0 vs release QUALITATIVE → plausibility "
        "flag; render the qualitative growth line"
    ) == "revenue: CIQ 6405.0 vs release QUALITATIVE → plausibility flag"
    assert dr._clean_note("no revised-outlook 99.1 exhibit parsed for 8-Ks "
                          "['0000749251-26-000028']") == \
        "no revised-outlook 99.1 exhibit parsed for the filed 8-K 0000749251-26-000028"
    assert "ambiguous in the export" in dr._clean_note(
        "Credit Health Panel: scale direction ambiguous — not rendered")
    # the JS twins exist (mirrored renderers — node-free source pins)
    js = Path("frontend/views/shared/dossier.js").read_text()
    for fn in ("function fmtInsider", "function fmtCustomers", "function fmtShape",
               "function cleanNote"):
        assert fn in js, f"missing JS twin: {fn}"


def test_contradiction_suppressions_on_frozen_fixtures() -> None:
    """(declutter P1) The four surface contradictions stay fixed: an UNKNOWN market row never
    renders beside a PRESENT relative; an UNKNOWN FCF-sign row never renders beside a PRESENT FCF
    value; the honest-absence cases still render both rows."""
    p, u = ds.Sourced.present, ds.Sourced.unknown
    io_mixed = ds.IdiosyncraticVsShared(
        name_180d_return=p(-0.45, source_ref="EOD"),
        market_180d_return=u(note="IWM benchmark bars unavailable"),
        rel_vs_market=p(-0.61, source_ref="EOD"),
        read=u(note="no graph cohort"), cohort=u(note="not in coverage"))
    m1 = _minimal_mech().model_copy(update={"idiosyncratic_vs_shared": io_mixed})
    d1 = ds.Dossier(ticker="X", name="X", cik="0", reference_date=date(2026, 6, 1), rank=1,
                    mechanical=m1, synthesis=None, caveats=[], qa_flags=[], llm_model=None,
                    assembled_at=datetime(2026, 6, 1, 12, 0))
    md1 = dr.render_markdown(d1)
    assert "Market (IWM) 180d return:** _UNKNOWN_" not in md1, (
        "an UNKNOWN market row beside a present relative reads as a contradiction")
    assert "Relative vs market:** -61.0%" in md1
    # honest absence: BOTH absent → the market row renders with its reason
    io_both = io_mixed.model_copy(update={"rel_vs_market": u(note="no bars")})
    m2 = m1.model_copy(update={"idiosyncratic_vs_shared": io_both})
    md2 = dr.render_markdown(d1.model_copy(update={"mechanical": m2}))
    assert "Market (IWM) 180d return:** _UNKNOWN_" in md2
    # FCF: sign UNKNOWN + value present → sign row suppressed; both absent → sign row renders
    q1 = _minimal_mech().quality.model_copy(update={
        "fcf_sign": u(note="no OCF/capex"), "free_cash_flow": p(1064.2, source_ref="CIQ CF")})
    m3 = _minimal_mech().model_copy(update={"quality": q1})
    md3 = dr.render_markdown(d1.model_copy(update={"mechanical": m3}))
    assert "FCF sign:** _UNKNOWN_" not in md3 and "Free cash flow ($M):** 1064.2" in md3
    q2 = q1.model_copy(update={"free_cash_flow": u(note="no CF sheet")})
    m4 = m3.model_copy(update={"quality": q2})
    md4 = dr.render_markdown(d1.model_copy(update={"mechanical": m4}))
    assert "FCF sign:** _UNKNOWN_" in md4


def test_release_drivers_dedup_identical_segments() -> None:
    """(audit item 8 — regression) A release that states the same one-off twice must not read as a
    stutter: the composer dedups identical segments order-preserving. IT's Feb-3 8-K stated the
    $150.0M Digital impairment in both the headline and the detail paragraph, and the committed
    dossier printed it twice. Frozen committed-artifact pin + the extractor guard."""
    import json as _json
    import pathlib
    p = pathlib.Path("data/dossiers/IT/dossier.json")
    if not p.exists():
        pytest.skip("no committed IT dossier.json")
    f = _json.loads(p.read_text())["mechanical"]["drawdown_cause"]["filings"][0]
    val = f["drivers"]["value"]
    segs = [x.strip() for x in val.split(";")]
    assert len(segs) == len(dict.fromkeys(segs)), f"duplicated driver segments: {val!r}"
    # the extractor guard exists (source pin — future assemblies can't reintroduce it)
    src = pathlib.Path("vinci/dossier/mechanical.py").read_text()
    assert "parts = list(dict.fromkeys(parts))" in src


def test_resolve_benchmark_cap_bands_and_unknown_fallback() -> None:
    """The dossier surface resolves its benchmark via the monitor's OWN cap-band policy (CIQ $M cap
    → USD): small→IWM, mid→MDY, large→SPY. An UNKNOWN cap falls back to IWM and SAYS SO in the
    basis — a stated default, never a silent guess."""
    ref = date(2026, 7, 6)
    small, _ = dm._resolve_benchmark(ds.Sourced.present(2_000.0, source_ref="CIQ cap"), ref)
    mid, m_basis = dm._resolve_benchmark(ds.Sourced.present(8_735.2, source_ref="CIQ cap"), ref)
    large, _ = dm._resolve_benchmark(ds.Sourced.present(30_000.0, source_ref="CIQ cap"), ref)
    assert (small.eod_symbol, mid.eod_symbol, large.eod_symbol) == ("IWM", "MDY", "SPY")
    assert mid.internal_id == "IDX-MDY" and "mid" in m_basis and "MDY" in m_basis
    unk, u_basis = dm._resolve_benchmark(ds.Sourced.unknown(note="no CIQ cap"), ref)
    assert unk.eod_symbol == "IWM" and "UNKNOWN" in u_basis
    # ranker-cap FALLBACK: when the CIQ cap is absent (re-assembly in an incomplete store), band by
    # the SCREEN-TIME EOD×XBRL cap the ranker already froze — so a mid-cap can't silently flip to
    # IWM (the observed IT MDY→IWM drift). Positive + negative + priority pins:
    it_fb, it_basis = dm._resolve_benchmark(  # IT's ranker cap $9.13B
        ds.Sourced.unknown(note="no CIQ cap"), ref, screen_cap_usd=9_126_881_508.48)
    assert it_fb.eod_symbol == "MDY" and "ranker" in it_basis and "screen-time" in it_basis
    small_fb, _ = dm._resolve_benchmark(  # ranker cap < $4B → still small-cap
        ds.Sourced.unknown(note="no CIQ cap"), ref, screen_cap_usd=2.03e9)
    assert small_fb.eod_symbol == "IWM"
    ciq_wins, _ = dm._resolve_benchmark(  # a PRESENT CIQ cap wins; ranker cap is only a fallback
        ds.Sourced.present(8_735.2, source_ref="CIQ cap"), ref, screen_cap_usd=500e9)
    assert ciq_wins.eod_symbol == "MDY"  # CIQ mid-band, never the absurd $500B ranker override


def test_finalist_carries_ranker_screen_cap_for_benchmark_fallback() -> None:
    """(benchmark drift pin) The ranked-queue row's screen-time market cap threads onto the Finalist
    (``market_cap_screen``) so the dossier can band the benchmark on it when the CIQ cap is absent.
    ``_cap_of`` takes only a positive numeric cap; load_finalists carries the committed value."""
    from vinci.config import get_config
    from vinci.dossier.assemble import _cap_of, load_finalists
    assert _cap_of({"market_cap": 9.13e9}) == 9.13e9
    assert _cap_of({"market_cap": 0}) is None and _cap_of({"market_cap": -5}) is None
    assert _cap_of({"market_cap": None}) is None and _cap_of({}) is None
    assert _cap_of({"market_cap": True}) is None  # bool is a subclass of int — not a real cap
    assert _cap_of({"market_cap": float("inf")}) is None  # non-finite → never bands a benchmark
    assert _cap_of({"market_cap": float("nan")}) is None
    import json as _json
    rq = Path("data/snapshots/ranked_queue.jsonl")
    if not rq.exists():
        pytest.skip("no committed ranked_queue snapshot")
    rows = {r["ticker"]: r for r in
            (_json.loads(x) for x in rq.read_text().splitlines() if x.strip())}
    if "IT" not in rows:  # threading needs IT in BOTH the queue AND candidate_records
        pytest.skip("IT not in the committed ranked_queue")
    try:
        fin = load_finalists(get_config(), ticker="IT")[0]  # IT: the canonical mid-cap case
    except LookupError:
        pytest.skip("IT not in the committed candidate set")
    assert fin.market_cap_screen is not None and fin.market_cap_screen > 0
    assert fin.market_cap_screen == pytest.approx(rows["IT"]["market_cap"])  # threaded, not dropped


def test_price_stale_note_fires_only_past_the_cadence() -> None:
    """Assembly-time staleness guard: a last stored close >7 calendar days behind TODAY (assembly
    instant, not the reference date) → loud note naming the gap; at/inside the cadence → None."""
    today = date(2026, 7, 21)
    note = dm._price_stale_note(date(2026, 7, 8), today)
    assert note is not None and "PRICE STALE AT ASSEMBLY" in note and "13 calendar days" in note
    assert dm._price_stale_note(date(2026, 7, 14), today) is None  # exactly the cadence → fresh
    assert dm._price_stale_note(date(2026, 7, 21), today) is None
    assert dm._price_stale_note(None, today) is None


def test_committed_it_dossier_capband_benchmark_and_fresh_price() -> None:
    """(benchmark unification e2e) IT's CIQ cap ($8.7B) is mid-band, so the committed artifact's
    analytical benchmark is MDY across the exhibit + the 180d relative — one yardstick, stated
    basis. And the committed CMP carries NO stale-at-assembly note (the pre-assembly refresh ran;
    the note is stamped at assembly, so this is an artifact fact, not a clock read). Deterministic
    values only: the cap-band mapping is plain code, never LLM text."""
    p = Path("data/dossiers/IT/dossier.json")
    if not p.exists():
        pytest.skip("no committed IT dossier.json")
    mech = json.loads(p.read_text())["mechanical"]
    io = mech["idiosyncratic_vs_shared"]
    assert io["benchmark_symbol"] == "MDY"
    assert "cap-band" in (io["benchmark_basis"] or "")
    sp = mech["stock_performance"]
    assert sp["benchmark_symbol"] == "MDY" and "MDY" in sp["source_ref"]
    # the relative leg is recomputed on the SAME yardstick at assembly (never the G2 IWM number
    # under a mid-band read)
    assert "MDY" in (io["rel_vs_market"].get("source_ref") or "")
    assert mech["stock_info"]["price"].get("note") in (None, "")
    md = Path("data/dossiers/IT/dossier.md").read_text()
    assert "Market (MDY) 180d return" in md


def test_buyside_cover_and_field_grids_e2e_node() -> None:
    """(buy-side layout e2e, phrasing-independent) On the committed IT artifact, the web render:

    1. CRUX ONCE, CONSISTENT — the cover carries exactly one crux block whose question text equals
       the committed ``synthesis.decisive_question.question`` (internal consistency, never a
       literal pin) plus the first two key unknowns; "The case" card carries NO question copy
       (the de-dup) and no unknowns list.
    2. FIELD GRIDS — the leverage stat grid renders with the basis TAGS VISIBLE (NET / FWD-ADJ)
       and an UNKNOWN cell's note as visible text (never tooltip-only — the PDF is the record).
    3. WALL STRIP — the year→amount chips equal per-year principal sums computed here from the
       committed structured instruments (deterministic; never hard-coded values).
    4. READ-FIRST — the what-broke card leads with the promoted Shape read (fg-read present).
    """
    import html as _html
    import json as _json
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node not available")
    p = Path("data/dossiers/IT/dossier.json")
    if not p.exists():
        pytest.skip("no committed IT dossier.json")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const rd = (p) => JSON.parse(readFileSync(p));
const h = renderDossier(rd("data/dossiers/IT/dossier.json"), null,
  rd("frontend/scenarios/IT.json"));
console.log(JSON.stringify({{ html: h }}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    h = _json.loads(out.stdout)["html"]
    d = _json.loads(p.read_text())
    s = d["synthesis"]

    # 1 — crux once + consistency + the-case de-dup. The crux carries the QUESTION + the honest
    # count-pointer ONLY — the key_unknowns[:2] teaser was REMOVED (2026-07-24 weather audit:
    # unknown-set survival ~17% / top-2 ~7% across draws — the teaser presented weather as a
    # curated top-2). Absence-of-LLM-text pins are safe (reworded content stays absent).
    assert h.count('class="brief-crux"') == 1
    q = s["decisive_question"]["question"]
    assert _html.escape(q) in h
    crux = h.split('class="brief-crux"')[1].split("</div></div>")[0]
    n_unk = len(s.get("key_unknowns") or [])
    assert f"{n_unk} key unknowns + the evidence for/against — in Analysis" in crux
    for u in (s.get("key_unknowns") or []):
        assert _html.escape(u) not in crux, "no unknown may render inside the crux teaser"
    case = h.split(">The case<")[1].split('class="card')[0] if ">The case<" in h else ""
    assert "brief-dq" not in case, "the case card must not carry a second question copy"
    assert "Key unknowns" not in case

    # 2 — leverage grid: visible basis tags + visible UNKNOWN note
    assert h.count('class="fg-grid') >= 2  # leverage (standard) + the idio returns (hero)
    assert '<span class="fg-basis">NET</span>' in h
    assert '<span class="fg-basis">FWD-ADJ</span>' in h
    fwd = h.split('<span class="fg-basis">FWD-ADJ</span>')[1].split("</div></div>")[0]
    note = (d["mechanical"]["quality"]["net_debt_to_ebitda_adjusted"].get("note") or "")
    if note:
        assert _html.escape(note) in fwd, "an UNKNOWN cell's note must be visible text"

    # 3 — wall strip totals computed from the committed instruments
    inst = ((d["mechanical"].get("capital_structure") or {}).get("instruments") or {})
    if inst.get("status") == "present":
        ref = str(d["reference_date"])
        by_yr: dict[str, float] = {}
        for i in inst["value"]:
            md = i.get("maturity_date")
            if md and md >= ref and md[:4] != ref[:4]:
                by_yr[md[:4]] = by_yr.get(md[:4], 0.0) + (i.get("principal_musd") or 0.0)
        assert by_yr, "IT carries later-year maturities"
        for yr, tot in by_yr.items():
            chip = f"<div class=\"wall-yr\"><span>{yr}</span><b>${tot:,.1f}M</b></div>"
            assert chip in h, f"wall chip for {yr} must equal the instruments sum"
        assert 'class="wall-foot"' in h  # reconciliation demoted to the footnote, still present

    # 4 — read-first on what-broke
    assert 'class="fg-read"' in h
    shape = d["mechanical"]["drawdown_cause"]["shape"]
    assert shape["status"] == "present"  # IT: the promoted read exists

    # mockup classes never leak into the app renderer
    src = Path("frontend/views/shared/dossier.js").read_text()
    assert 'class="mx-' not in src


def test_md_brief_crux_block_and_case_dedup() -> None:
    """(buy-side cover, md twin) The committed IT markdown carries the crux block inside
    'At a glance' (the question; pre-teaser-removal artifacts may still carry ≤2 unknowns until
    the next re-render — this test asserts only the shape-stable invariants) and 'The case'
    carries neither the question nor an unknowns list — content parity with the web cover."""
    p = Path("data/dossiers/IT/dossier.md")
    if not p.exists():
        pytest.skip("no committed IT dossier.md")
    md = p.read_text()
    j = json.loads(Path("data/dossiers/IT/dossier.json").read_text())
    q = j["synthesis"]["decisive_question"]["question"]
    glance = md.split("## At a glance")[1].split("\n## ")[0]
    assert "The crux — what decides this" in glance and q in glance
    case = md.split("## The case")[1].split("\n## ")[0]
    assert q not in case and "_Key unknowns:_" not in case


def test_md_crux_ku_teaser_removed_render_level() -> None:
    """(2026-07-24 weather audit) The md crux block renders the QUESTION + the honest count-pointer
    and NO unknown items — pinned at the RENDER level (committed json → render_markdown through
    CURRENT code), artifact-independent, so it is green before AND after the artifact re-render.
    Evidence for the removal: across 109 consecutive historical draw pairs the unknowns' set
    survives ~17% and the top-2 slots ~7% — the teaser presented weather as a curated top-2."""
    p = Path("data/dossiers/IT/dossier.json")
    if not p.exists():
        pytest.skip("no committed IT dossier.json")
    doss = ds.Dossier.model_validate_json(p.read_text())
    assert doss.synthesis is not None
    md = dr.render_markdown(doss)
    glance = md.split("## At a glance")[1].split("\n## ")[0]
    n = len(doss.synthesis.key_unknowns)
    assert f"_{n} key unknowns + the evidence for/against — in Analysis_" in glance
    for u in doss.synthesis.key_unknowns:
        assert u not in glance, "no unknown may render inside the crux block"


def test_what_broke_restructure_and_survival_columns_e2e_node() -> None:
    """(review-round restructure e2e, phrasing-independent) On the committed IT artifact:

    1. WHAT-BROKE ORDER — the idio comparison ("Company-specific or market-wide?") renders BEFORE
       the 8-K filing callout (read → question → evidence), the card carries NO revised-guidance
       row (it moved to the street card), and the cohort absence is a quiet footnote, not a
       labelled row.
    2. STREET — the revised-guidance fact renders on the street card exactly once (never dropped).
    3. BRIEF STRIP — 'What happened — and can it survive?' carries the stat grid with the market
       leg cell (the heading gained its survival half when the strip's triage content was named).
    4. SURVIVAL COLUMNS — the leverage grid and the maturity wall render inside the two-column
       wrapper (ls-cols), and the wall does NOT render a second time below it.
    5. PEER ROSTER — the business descriptor column is the prose class, never a numeric cell.
    """
    import json as _json
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node not available")
    p = Path("data/dossiers/IT/dossier.json")
    if not p.exists():
        pytest.skip("no committed IT dossier.json")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const rd = (p) => JSON.parse(readFileSync(p));
const h = renderDossier(rd("data/dossiers/IT/dossier.json"), null,
  rd("frontend/scenarios/IT.json"));
console.log(JSON.stringify({{ html: h }}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    h = _json.loads(out.stdout)["html"]

    # 1 — order + relocations inside the what-broke card
    card = h.split(">What broke — and did it fall alone?<")[1].split('class="card')[0]
    assert card.index("Company-specific or market-wide?") < card.index('class="filing"'), (
        "the idio comparison must precede the 8-K evidence")
    assert "Revised guidance" not in card
    assert "no supplier/customer cohort mapped" in card  # IT has no cohort — quiet footnote
    assert "Supplier/customer cohort</div>" not in card

    # 2 — the street card carries the guidance fact once
    street = h.split(">The street — estimates &amp; guidance<")[1].split('class="card')[0]
    assert street.count("Revised guidance (8-K 99.1)") == 1

    # 3 — the Brief what-happened strip has the market cell. (content relocation 2026-07-24) the
    # heading gained "— and can it survive?": the strip carries survival triage (net debt/EBITDA,
    # FCF, going concern) beside the event, and the old title described only the first half.
    wh = h.split(">What happened — and can it survive?<")[1].split('class="card')[0]
    assert 'class="fg-grid fg-hero"' in wh and "Market (" in wh  # the comparison is HERO

    # 4 — survival two-column: grid + wall inside ls-cols; the wall renders ONCE
    surv = h.split(">Survival — leverage")[1].split('class="card')[0]
    cols = surv.split('class="ls-cols"')
    assert len(cols) == 2, "the two-column wrapper must render once"
    assert 'class="fg-grid"' in cols[1]  # the scalar grid pairs with the wall
    # the long prose rows stay OUT of the columns (full-width below — no half-width cramming)
    assert "Total debt / EBITDA vs peers" not in cols[1].split('class="ls-wall"')[0]
    assert surv.count('class="wall-strip"') == 1

    # 5 — peer business column is prose-classed
    assert 'class="peer-desc"' in h
    assert 'class="peer-desc">operates' in h  # descriptor text rides the prose cell, not .num


def test_page_width_containment_css_pins() -> None:
    """(review round — page never scrolls horizontally) `.main` is a grid column: without
    min-width:0 the widest table's INTRINSIC width (appendix statements ~2.7k px) bubbles up
    through `min-width:auto` and forces the whole column wide, defeating every inner
    overflow-x:auto wrapper from above. Static pins: the containment rule + contained pre;
    the exhibits stay width-responsive (width=100%, never a bare fixed width)."""
    css = Path("frontend/assets/styles.css").read_text()
    assert ".main { min-width: 0; }" in css
    assert ".card pre { overflow-x: auto; }" in css
    src = Path("frontend/views/shared/dossier.js").read_text()
    assert 'width="100%"' in src
    for m in re.finditer(r"<svg viewBox[^>]+>", src):
        frag = m.group(0)[:70]
        assert 'width="100%"' in m.group(0), f"fixed-width svg breaks containment: {frag}"


def test_print_css_collapses_the_survival_columns() -> None:
    """(review fix) The PDF is the complete record: the two-column survival card must collapse to
    one column in print like every other split (the .uw-split precedent), and the new blocks must
    not be severed across a page."""
    css = Path("frontend/assets/styles.css").read_text()
    blocks = []
    for s in (j for j in range(len(css)) if css.startswith("@media print", j)):
        depth, k = 0, css.index("{", s)
        while k < len(css):
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        blocks.append(css[s:k])
    printed = "\n".join(blocks)
    assert ".ls-cols { grid-template-columns: 1fr !important; }" in printed
    assert "break-inside: avoid" in printed and ".wall-strip" in printed
    # and the screen rules must NOT be trapped inside a print block
    assert ".fg-hero .fg-val { font-size: 20px" not in printed


def test_desc_first_sentence_boundaries() -> None:
    """(peer-set capture) The business-descriptor capture ends at REAL boundaries — the first
    sentence (abbreviation-aware), a clause boundary under the cap for a run-on sentence, a word
    for a comma-free run-on — never the old mid-clause [:55] clip, and never sentence-two spill
    (the Netflix "worldwide. The company" case). Frozen strings; deterministic."""
    f = cs._desc_first_sentence
    # short full sentence — kept whole, terminal period intact
    assert f("operates a TV streaming platform in the United States.") == \
        "operates a TV streaming platform in the United States."
    # sentence-two spill stops at the FIRST boundary (the old [:55] grabbed "The company")
    assert f("provides entertainment services worldwide. The company also streams films.") == \
        "provides entertainment services worldwide."
    # an abbreviation does not end the sentence
    assert f("is a subsidiary of Moody's Corp. and provides risk analytics worldwide.") == \
        "is a subsidiary of Moody's Corp. and provides risk analytics worldwide."
    # run-on over the cap with clauses → cut at the LAST clause boundary inside the cap
    long = ("operates as an integrated risk assessment firm serving banks, insurers, "
            "asset managers, corporates, governments, and public agencies across the Americas, "
            "Europe, the Middle East and Africa with data and analytics.")
    out = f(long, cap=120)
    assert out == ("operates as an integrated risk assessment firm serving banks, insurers, "
                   "asset managers, corporates, governments")
    assert not out.endswith((",", ";", " "))
    # run-on over the cap with NO clause boundary → last whole word
    nocomma = "provides " + "very " * 40 + "specialized services worldwide."
    out2 = f(nocomma, cap=60)
    assert len(out2) <= 60 and not out2.endswith(" ") and " " in out2
    assert nocomma.startswith(out2)


def test_peerset_drift_guard_directions() -> None:
    """(peerset-backfill vintage guard) Same-text proves itself by a prefix relation in EITHER
    direction — widened capture (fresh extends committed) or trimmed sentence-two spill
    (committed extends fresh). Different caps / names / counts / HQ / text all refuse."""
    ok_c = "2 peers — A Co $1.0B — provides x services (US); B Inc. $2.0B — operates y (UK)"
    widened = ("2 peers — A Co $1.0B — provides x services to global clients. (US); "
               "B Inc. $2.0B — operates y platforms worldwide. (UK)")
    assert cli._peerset_drift(ok_c, widened) is None
    # trimmed spill: committed ran past the sentence end; fresh stops at it
    spill_c = "1 peers — N Co $3.0B — provides z worldwide. The company (US)"
    spill_f = "1 peers — N Co $3.0B — provides z worldwide. (US)"
    assert cli._peerset_drift(spill_c, spill_f) is None
    assert cli._peerset_drift(ok_c, ok_c) is None
    # refusals
    cap = cli._peerset_drift(ok_c, widened.replace("$1.0B", "$1.1B"))
    assert cap is not None and "peer/cap changed" in cap
    cnt = cli._peerset_drift(ok_c, "1 peers — A Co $1.0B — provides x services (US)")
    assert cnt is not None
    hq = cli._peerset_drift(ok_c, widened.replace("(UK)", "(India)"))
    assert hq is not None and "HQ suffix" in hq
    txt = cli._peerset_drift(ok_c, widened.replace("provides x services to global clients.",
                                                   "makes entirely different things."))
    assert txt is not None and "description text changed" in txt


def test_peer_roster_builder_captures_to_sentence_not_55_chars() -> None:
    """(builder-level, frozen fixture) A long first sentence survives past the old 55-char clip
    and ends at a real boundary in the composed roster line."""
    long_desc = ("Moody's Corporation operates as an integrated risk assessment firm serving "
                 "banks, insurers and corporates in the Americas and Europe with data, "
                 "analytics and research.")
    bundle = _FakeCompsBundle(
        {
            ("comps", "Financial Data"): [
                ["Company Name", "", "", "Market Cap ($M)"],
                ["Moody's Corporation (NYSE:MCO)", "", "", 78600.0],
                ["", "", "", ""],
                ["fuboTV Inc. (NYSE:FUBO)", "", "", 256.0],
            ],
            ("comps", "Business Description"): [
                ["Company Name", "Business Description", "Headquarters"],
                ["Moody's Corporation (NYSE:MCO)", long_desc,
                 "New York, New York, United States"],
                ["", "", ""],
                ["fuboTV Inc. (NYSE:FUBO)", "fuboTV Inc. operates a live TV streaming platform.",
                 "New York, New York, United States"],
            ],
        }
    )
    ps = cs.peer_comps(typing.cast(ciq.CiqBundle, bundle)).peer_set
    assert ps.status is ds.SourceStatus.PRESENT and ps.value is not None
    body = re.sub(r"^\d+ peers — ", "", str(ps.value).split(" | the name:")[0])
    seg = next(s for s in body.split("; ") if s.startswith("Moody's"))
    desc = seg.split(" — ", 1)[1]
    core = desc[: desc.rfind(" (")]
    assert len(core) > 60, f"still clipped short: {core!r}"
    assert core.endswith("."), f"must carry the full first sentence: {core!r}"
    assert "operates as an integrated risk assessment firm serving banks" in core


def test_committed_peer_rosters_have_no_midclause_clip() -> None:
    """(committed-artifact invariant, all names) No roster descriptor ends on a dangling
    function word — the mid-clause smell of the old [:55] capture ("…firm in the"). Terminal
    sentences and clause-boundary cuts both pass; "…in the" / "…of" / "…and" fail."""
    stop = {"the", "a", "an", "of", "in", "and", "or", "for", "to", "as", "its", "with",
            "on", "at", "by", "The"}
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        ps = ((json.loads(p.read_text()).get("mechanical") or {})
              .get("peer_comps") or {}).get("peer_set") or {}
        if ps.get("status") != "present" or not ps.get("value"):
            continue
        body = re.sub(r"^\d+ peers — ", "", str(ps["value"]).split(" | the name:")[0])
        for seg in body.split("; "):
            if " — " not in seg:
                continue
            desc = seg.split(" — ", 1)[1]
            core = desc[: desc.rfind(" (")] if " (" in desc else desc
            last = core.rstrip(".").rsplit(" ", 1)[-1]
            assert last not in stop, f"{p.parent.name}: mid-clause descriptor: …{core[-40:]!r}"


def test_desc_capture_never_emits_the_roster_delimiters() -> None:
    """(review fix) The roster line joins peers with '; ' and splits name/descriptor on ' — ',
    so a descriptor carrying either delimiter would corrupt the segment split for EVERY consumer
    (web parser, md table, the peerset-backfill vintage guard). The capture neutralises both, so
    the delimiters are unambiguous by construction — not by whatever a given export happens to
    contain. Negative pin with a real-shaped clause list; positive pin that normal text is
    untouched."""
    f = cs._desc_first_sentence
    out = f("provides data; analytics; and risk tools worldwide.")
    assert "; " not in out and out == "provides data, analytics, and risk tools worldwide."
    out2 = f("operates two units — retail and wholesale — across Europe.")
    assert " — " not in out2 and "–" in out2
    # normal text is untouched (no gratuitous rewriting of the record)
    plain = "operates as a data, analytics, and technology company."
    assert f(plain) == plain


def test_committed_peer_rosters_split_to_their_declared_count() -> None:
    """(review fix, committed-artifact invariant) Every roster's '; ' split must yield exactly the
    peer count the line declares, and no segment may carry a second ' — ' — the structural proof
    that no widened descriptor swallowed a delimiter."""
    for p in sorted(Path("data/dossiers").glob("*/dossier.json")):
        ps = ((json.loads(p.read_text()).get("mechanical") or {})
              .get("peer_comps") or {}).get("peer_set") or {}
        if ps.get("status") != "present" or not ps.get("value"):
            continue
        v = str(ps["value"])
        declared = int(re.match(r"^(\d+) peers", v).group(1))
        body = re.sub(r"^\d+ peers — ", "", v.split(" | the name:")[0])
        segs = body.split("; ")
        assert len(segs) == declared, f"{p.parent.name}: {declared} declared, {len(segs)} split"
        for s in segs:
            assert s.count(" — ") <= 1, f"{p.parent.name}: extra delimiter in {s[:60]!r}"


def test_md_brief_carries_the_underwrite_layer_and_suppresses_the_machine_read() -> None:
    """(md/web parity) A logged name's markdown Brief carries the underwrite layer the export used
    to drop entirely: the economics strip, the disposition, the analyst's THESIS, and the
    bear/base/bull table with each recorded reason. AUTHORSHIP: the thesis REPLACES the machine
    assessment (two voices in one slot blurs which is which) — and the disposition is never
    labelled a verdict, because the BUY/AVOID verdict of record is the ledger's.

    Phrasing-independent: the thesis is asserted to equal the COMMITTED record's own text rather
    than any literal string, and the scenario rows are checked against the record's inputs."""
    p = Path("data/dossiers/IT/dossier.json")
    sp = Path("scenarios/IT.json")
    if not (p.exists() and sp.exists()):
        pytest.skip("no committed IT dossier/scenario record")
    from vinci.scenarios import read_record
    card = read_record("IT")
    d = ds.Dossier.model_validate_json(p.read_text())
    md = dr.render_markdown(d, card=card)
    glance = md.split("## At a glance")[1].split("\n## ")[0]

    thesis = card.verdict.rationale_plain or card.verdict.rationale
    assert thesis and "### Thesis — our rationale" in glance and thesis in glance
    # authorship: the machine read is suppressed once the analyst's thesis is present
    if d.synthesis is not None and d.synthesis.evidence_balance:
        assert dr._machine_read_md(d.synthesis.evidence_balance) not in glance
    # disposition, never "verdict of record" (that is the ledger's)
    assert "Underwrite disposition:" in glance
    assert "Verdict of record:" not in glance
    assert f"{card.spot:,.2f}" in glance  # the economics strip carries the recorded spot

    scen = md.split("## Scenario analysis")[1].split("\n## ")[0]
    assert "| scenario | revenue $M | margin | multiple | value / sh | vs spot |" in scen
    for nm in ("bear", "base", "bull"):
        s = card.scenarios.get(nm)
        if s is None:
            continue
        assert f"| {nm} | {s.revenue:,.0f} |" in scen, f"{nm} row must carry its recorded revenue"
        if s.reason:
            assert s.reason in scen, f"{nm}'s recorded reason must render beside the arithmetic"


def test_md_without_a_card_is_unchanged_and_keeps_the_machine_read() -> None:
    """Fail-honest: a name with no underwrite record renders NO underwrite section and keeps the
    machine assessment — byte-identity for un-underwritten names, and the machine voice is never
    dressed as a thesis."""
    p = Path("data/dossiers/IT/dossier.json")
    if not p.exists():
        pytest.skip("no committed IT dossier.json")
    d = ds.Dossier.model_validate_json(p.read_text())
    md = dr.render_markdown(d, card=None)
    assert "Thesis — our rationale" not in md
    assert "Underwrite disposition:" not in md
    assert "## Scenario analysis" not in md
    if d.synthesis is not None and d.synthesis.evidence_balance:
        assert dr._machine_read_md(d.synthesis.evidence_balance) in md


def test_download_menu_offers_three_scopes_and_serves_the_committed_md() -> None:
    """(download menu) The button is a generic 'Download' with three scopes; the MD option fetches
    the COMMITTED render from the mirror rather than re-rendering markdown in JS (a second
    generator would drift from vinci/dossier/render.py), and the build publishes one .md per
    mirrored dossier so the fetch can succeed."""
    src = Path("frontend/views/shared/dossier.js").read_text()
    assert "&#x2913; Download &#x25be;" in src and "Download PDF" not in src
    for scope in ('data-scope="brief"', 'data-scope="full"', 'data-scope="md"'):
        assert scope in src
    assert "Brief PDF" in src and "Full dossier PDF" in src and "Full dossier MD" in src
    # the MD path fetches the committed mirror; no JS markdown generator
    assert "./dossiers/${encodeURIComponent(ticker)}.md" in src
    assert "-dossier.md" in src  # download filename
    build = Path("frontend/build.py").read_text()
    assert 'OUT_DOSS / f"{ticker}.md"' in build
    # every mirrored dossier has its markdown twin published
    mirrored = {p.stem for p in Path("frontend/dossiers").glob("*.json")} - {"index"}
    md_served = {p.stem for p in Path("frontend/dossiers").glob("*.md")}
    assert mirrored == md_served, f"missing md for: {sorted(mirrored - md_served)}"


def test_scenario_card_read_is_loud_on_a_corrupt_record() -> None:
    """(review fix) FAIL-LOUD BOUNDARY on the underwrite read: an ABSENT record is the normal
    state (most names are never underwritten) and degrades to None, but a record that EXISTS and
    will not parse must PROPAGATE — swallowing it would ship a dossier.md silently missing its
    thesis and scenarios with nothing anywhere saying so. Mirrors the repo's disclose-on-degrade
    convention ('a peer that won't resolve is EXCLUDED, named')."""
    import json as _json

    from vinci.dossier import assemble as dassemble

    cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "scenarios").mkdir()
        try:
            os.chdir(root)
            # absent → None, no raise
            assert dassemble._read_scenario_card("ZZZZ") is None
            # present but malformed → LOUD
            (root / "scenarios" / "BAD.json").write_text(_json.dumps({"ticker": "BAD"}))
            with pytest.raises(Exception) as exc:
                dassemble._read_scenario_card("BAD")
            assert not isinstance(exc.value, FileNotFoundError), (
                "a corrupt record must not be reported as an absent one")
        finally:
            os.chdir(cwd)


def test_scenario_table_renders_a_revenue_basis_leg_without_a_margin() -> None:
    """(review fix, PR #188 interaction) An R2 EV/Revenue leg applies its multiple to REVENUE and
    never reads a margin, so ``ScenarioInput.margin`` is None by design rather than missing. The
    md table must render that absence as an em-dash — formatting None raises TypeError, and
    substituting 0% would fabricate a driver the arithmetic never used."""
    class _S:
        revenue, margin, multiple, reason = 500.0, None, 2.5, "revenue-basis leg"

    class _P:
        value_per_share = 12.0

    class _R:
        per_scenario = {"base": _P()}

    class _Card:
        result, spot, recipe_desc = _R(), 10.0, "R2 EV/Revenue"
        scenarios = {"base": _S()}

    lines = dr._scenario_table_lines(typing.cast(Any, _Card()))
    row = next(x for x in lines if x.startswith("| base |"))
    cells = [c.strip() for c in row.strip("|").split("|")]
    # cells: scenario · revenue · margin · multiple · value/sh · vs spot
    assert cells[2] == "—", f"absent margin must render as an em-dash, got {cells[2]!r}"
    assert "%" not in cells[2]  # never a fabricated 0.0% margin
    assert cells[1] == "500" and cells[3] == "2.5x" and cells[4] == "$12.00"


def test_assembly_writes_no_synthesis_less_dossier_over_a_good_one_undetected() -> None:
    """(INCIDENT 2026-07-22, recorded risk) A transient LLM failure during `dossier assemble`
    makes ``synthesize`` return None; the assembler then WRITES the dossier anyway with
    ``synthesis: None``, silently replacing a committed synthesis with nothing. Observed live:
    BRBR's 6-bull/8-bear synthesis was wiped by one flaky call, and the only signal was the word
    'NO-synth' in a summary line — a retry succeeded.

    This pins the DISCLOSURE that must exist so the loss is never silent: the failure emits a flag
    naming it. The surviving risk (the write itself is not blocked) is recorded in STATE.md."""
    import inspect

    from vinci.dossier import synthesis as dsynth

    src = inspect.getsource(dsynth.synthesize)
    assert "LLM synthesis failed (no usable output)" in src, (
        "a synthesis failure must emit a named flag, never a bare None")
    asm = Path("vinci/dossier/assemble.py").read_text()
    assert "LLM synthesis skipped (no ANTHROPIC client) — mechanical layer only" in asm, (
        "a skipped synthesis must be disclosed on the dossier, not inferred from a console line")


def test_one_8k_explaining_two_gap_downs_renders_once_e2e() -> None:
    """(SMPL/CNXC) Two consecutive gap-downs can share ONE 8-K; the flat loop rendered the whole
    block per gap-date, and the md even printed 'gap 2026-04-10 → 2026-04-09' which read like a
    date error. Both renderers now group by accession: one entry per filing, naming every
    gap-down it explains. Pinned on SMPL's committed artifact (its 04-09/04-10 share one 8-K)."""
    import json as _json
    import shutil
    import subprocess

    p = Path("data/dossiers/SMPL/dossier.json")
    if not p.exists():
        pytest.skip("no committed SMPL dossier.json")
    d = _json.loads(p.read_text())
    filings = (d["mechanical"].get("drawdown_cause") or {}).get("filings") or []
    accs = [f.get("accession") for f in filings]
    if len(accs) == len(set(accs)):
        pytest.skip("SMPL no longer has a shared-accession gap pair")
    dup_acc = next(a for a in accs if accs.count(a) > 1)

    # md: one grouped entry, both dates named, no reversed 'gap X → Y' arrow
    md = Path("data/dossiers/SMPL/dossier.md").read_text()
    blk = md.split("Gap-downs — what the results showed")[1].split("###")[0]
    assert blk.count(f"`{dup_acc}`") == 1, "the shared 8-K must appear once in the md"
    assert "2026-04-09 and 2026-04-10" in blk

    # web: one .filing card for the shared accession
    if not shutil.which("node"):
        return
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const h = renderDossier(JSON.parse(readFileSync("data/dossiers/SMPL/dossier.json")), null,
  JSON.parse(readFileSync("frontend/scenarios/SMPL.json")));
const wb = h.split(">What broke")[1].split('class="card ds-section"')[0];
console.log(JSON.stringify({{
  cards: (wb.match(/class="filing"/g) || []).length,
  bothGaps: wb.includes("2026-04-09 and 2026-04-10 gap-downs"),
}}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    r = _json.loads(out.stdout)
    assert r["cards"] == 1, f"the shared 8-K must render ONE filing card, got {r['cards']}"
    assert r["bothGaps"], "the single card must name both gap-downs it explains"


def test_admin_only_8k_is_non_explanatory_with_an_honest_label() -> None:
    """(BRBR) An 8-K carrying only an administrative item — a 5.07 annual-meeting vote — does NOT
    explain a gap-down. It must classify non-explanatory, and its gap label must read the honest
    "no earnings/guidance filing (…)" — never the Python list-repr `['5.07']` the human flagged.
    A management change (5.02) genuinely moves a stock, so it stays explanatory. Deterministic:
    item codes → classification/label, no LLM text in play, so exact pins are safe here."""
    # explanatory set is exactly the price-moving item map — administrative codes fall outside it
    assert dm._is_explanatory(["2.02", "9.01"])  # earnings
    assert dm._is_explanatory(["5.02"])          # management change moves a stock
    assert not dm._is_explanatory(["5.07"])              # annual-meeting vote
    assert not dm._is_explanatory(["5.07", "9.01"])      # vote + exhibits
    assert not dm._is_explanatory(["5.03"])              # bylaw amendment
    assert not dm._is_explanatory([])                    # nothing parsed
    # the label is honest and carries NO list repr
    lbl = dm._gap_label(["5.07"])
    assert lbl == "no earnings/guidance filing (annual-meeting 8-K only)"
    assert "[" not in lbl and "'" not in lbl, f"no Python list-repr leak: {lbl!r}"
    assert dm._gap_label(["2.02", "9.01"]) == "earnings (2.02)"  # explanatory unchanged


def test_admin_only_gap_8k_card_suppressed_on_committed_brbr_e2e() -> None:
    """(BRBR) End-to-end on the committed artifact: BRBR's 2026-02-03 gap 8-K is a 5.07
    annual-meeting vote (administrative). Its card recited the vote text and its shape line leaked
    `['5.07']`; both are the noise the human flagged. The re-rendered md/web must (a) read the
    honest shape label for that gap, (b) NOT recite the annual-meeting vote, (c) NOT leak the list
    repr, while (d) KEEPING the real 2026-05-05 earnings (2.02) card. Phrasing-independent: card
    presence/absence + deterministic-label substring, never an LLM-composed string."""
    import json as _json
    import shutil
    import subprocess

    p = Path("data/dossiers/BRBR/dossier.json")
    if not p.exists():
        pytest.skip("no committed BRBR dossier.json")
    d = _json.loads(p.read_text())
    filings = (d["mechanical"].get("drawdown_cause") or {}).get("filings") or []
    admin = [f for f in filings if f.get("explanatory") is False]
    if not admin:
        pytest.skip("committed BRBR no longer carries an administrative-only gap 8-K")
    # the shape line states the honest label for the administrative gap, never the list repr
    shape = str(((d["mechanical"]["drawdown_cause"]).get("shape") or {}).get("value") or "")
    assert "no earnings/guidance filing (annual-meeting 8-K only)" in shape
    assert "['5.07']" not in shape and "non-narrative items [" not in shape

    # md: the administrative filing's card is gone; the 2.02 earnings card stays
    md = Path("data/dossiers/BRBR/dossier.md").read_text()
    assert "Submission of Matters" not in md and "['5.07']" not in md
    assert "gap-down 2026-05-05" in md, "the real earnings-gap card must survive"

    # web: exactly the explanatory filing cards render (5.07 suppressed, 2.02 kept)
    if not shutil.which("node"):
        return
    n_expl = sum(1 for f in filings if f.get("explanatory") is not False)
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    scen_path = Path("frontend/scenarios/BRBR.json")
    scen = f'JSON.parse(readFileSync("{scen_path}"))' if scen_path.exists() else "null"
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const h = renderDossier(JSON.parse(readFileSync("frontend/dossiers/BRBR.json")), null, {scen});
const wb = h.split(">What broke")[1].split('class="card ds-section"')[0];
console.log(JSON.stringify({{
  cards: (wb.match(/class="filing"/g) || []).length,
  recitesVote: /Submission of Matters|annual meeting/i.test(wb),
  keptEarnings: wb.includes("2026-05-05"),
}}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    r = _json.loads(out.stdout)
    assert r["cards"] == n_expl, (
        f"only explanatory 8-Ks render a card: {n_expl} want, {r['cards']} got"
    )
    assert not r["recitesVote"], "the administrative-only 8-K's vote text must not be recited"
    assert r["keptEarnings"], "the real 2026-05-05 earnings card must survive the suppression"


def test_caveat_dejargon_and_acronym_render_helpers() -> None:
    """(A, D) Pure render-time cleanups — deterministic, so exact pins are safe here. The human tier
    drops the synthesis field tokens and the internal rule numbers a guardrail cites, keeps the real
    AS_OF sidecar name, and uppercases financial acronyms a parser lower-cased. Word-boundary."""
    # (A) de-jargon
    assert dr._dejargon_caveat("the minority bull_points aren't outweighed (rule 7)") == \
        "the minority bull points aren't outweighed"
    assert dr._dejargon_caveat("bear_points sized (rule 12), noted") == "bear points sized, noted"
    assert dr._dejargon_caveat("evidence_balance is near-symmetric") == \
        "the written assessment is near-symmetric"
    assert dr._dejargon_caveat("attest the export date (AS_OF sidecar)") == \
        "attest the export date (AS_OF sidecar)"  # a real artifact name — NEVER stripped
    # (D) acronym casing
    assert dr._fix_acronyms("2026 adjusted ebitda outlook; adj eps 2025") == \
        "2026 adjusted EBITDA outlook; adj EPS 2025"
    assert dr._fix_acronyms("adj EBITDA $53.8M") == "adj EBITDA $53.8M"  # idempotent
    assert dr._fix_acronyms("kebitda noteps") == "kebitda noteps"  # word-boundary — never mid-word


def test_caveats_collapse_dejargon_and_acronyms_committed_brbr_e2e() -> None:
    """(Option 2 + A + B + D) End-to-end on the committed artifact as TRANSFORM invariants — the raw
    JSON carries the jargon / lowercase acronyms; the render must not. Phrasing-independent (guarded
    on the raw pattern being present), so it survives re-assembly. md + web both: same-type caveats
    collapse to one advisory, field tokens + rule numbers gone, the real AS_OF kept, the count
    equals the rendered advisory count, EBITDA/EPS uppercased in the driver line."""
    import json as _json
    import re as _re
    import shutil
    import subprocess

    p = Path("data/dossiers/BRBR/dossier.json")
    if not p.exists():
        pytest.skip("no committed BRBR dossier.json")
    d = _json.loads(p.read_text())
    raw = " ".join(c for c in (d.get("caveats") or []))
    md = dr.render_markdown(ds.Dossier.model_validate(d))
    flags_md = md.split("Analyst caveats")[1].split("\n## ")[0]

    # (A) de-jargon transform: raw carries the token, the render does not; the real AS_OF survives
    if "bull_points" in raw:
        assert "bull_points" not in flags_md and "bull points" in flags_md
    if "(rule 7)" in raw:
        assert "(rule 7)" not in flags_md and "(rule" not in flags_md
    if "AS_OF" in raw:
        assert "AS_OF" in flags_md  # never collateral-damaged by the underscore cleanup

    # (B) the header count line renders and equals the number of advisory blocks the web draws
    n_md = _re.search(r"_(\d+) to verify\._", flags_md)
    assert n_md, "the caveat count line must render"

    # (Option 2) any lead appearing >=2x in the raw caveats collapses to ONE block naming N points
    leads = [m.group("lead").strip() for c in (d.get("caveats") or [])
             if (m := dr._CAVEAT_RE.match(dr._dejargon_caveat(c)))]
    dup = next((x for x in leads if leads.count(x) > 1), None)
    if dup is not None:
        n = leads.count(dup)
        assert flags_md.count(f"**{dup}** ({n} points)") == 1, "duplicate lead must collapse once"
        assert flags_md.count(f"**{dup}**") == 1, "collapsed lead must not also render alone"

    # (D) acronym casing in the driver line (What broke section, not the caveats)
    if "adjusted ebitda outlook" in _json.dumps(d):
        assert "adjusted EBITDA outlook" in md and "adjusted ebitda outlook" not in md

    # web parity: the count equals the rendered .flag cards, and the duplicate lead renders once
    if not shutil.which("node"):
        return
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    scen_path = Path("frontend/scenarios/BRBR.json")
    scen = f'JSON.parse(readFileSync("{scen_path}"))' if scen_path.exists() else "null"
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const h = renderDossier(JSON.parse(readFileSync("frontend/dossiers/BRBR.json")), null, {scen});
const cav = h.split("Analyst caveats")[1].split('class="card ds-section"')[0];
const badge = (cav.match(/(\\d+) to verify/) || [])[1];
console.log(JSON.stringify({{
  flagCards: (cav.match(/class="flag/g) || []).length,
  badge: badge ? Number(badge) : null,
  hasJargon: /bull_points|\\(rule 7\\)/.test(cav),
  asofKept: /AS_OF/.test(cav),
  catalystLeads: /Estimates data up to \\d+d stale/.test(cav),
  catalystOpenerGone: !/Catalyst-path as-of UNVERIFIABLE/.test(cav),
  dupLeadCount: (cav.match(/Unreconciled margin-compression/g) || []).length,
  twoPointsBadges: (cav.match(/2 points/g) || []).length,
  ebitdaUpper: /adjusted EBITDA outlook/.test(h) && !/adjusted ebitda outlook/.test(h),
}}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    r = _json.loads(out.stdout)
    assert r["badge"] == int(n_md.group(1)), "web + md must agree on the advisory count"
    assert r["flagCards"] == r["badge"], "each advisory must render exactly one card (no split)"
    assert not r["hasJargon"], "the web render must not leak bull_points / (rule N)"
    if "AS_OF" in raw:
        assert r["asofKept"], "the real AS_OF sidecar name must survive the web de-jargon"
    # (twin coverage) the JS render must ALSO reword the catalyst caveat, not just the md path
    if "Catalyst-path as-of UNVERIFIABLE" in raw:
        assert r["catalystLeads"], "web catalyst caveat must lead with the staleness discriminator"
        assert r["catalystOpenerGone"], "the buried-lede opener must not survive into the web"
    # (twin coverage) the collapse renders ONE card with the N-points badge, not the count alone
    if dup is not None:
        assert r["dupLeadCount"] == 1, "the duplicate lead must render once on the web (collapsed)"
        assert r["twoPointsBadges"] >= 1, "the collapsed web card must show its N-points badge"
    # (twin coverage) the JS driver line must uppercase EBITDA/EPS, like the md path
    if "adjusted ebitda outlook" in _json.dumps(d):
        assert r["ebitdaUpper"], "the web 'what broke' driver line must uppercase EBITDA"


def test_catalyst_stale_caveat_leads_with_the_discriminator() -> None:
    """(Option 1) The catalyst-staleness caveat must LEAD with the name-specific discriminator (days
    stale vs the tolerance), not the structural 'no as-of stamp' preamble every CIQ export shares.
    Unit is a FROZEN template fixture (deterministic → exact pins safe); non-matching input fails
    through unchanged."""
    raw = (
        "Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp; "
        "its data is on/after 2026-05-14 (the latest embedded revision event), so it is up to "
        "53d before the 2026-07-06 reference — beyond the 45d tolerance — and the true export "
        "date is unknown, so freshness cannot be confirmed. Re-pull CIQ Estimates, or attest "
        "the export date (AS_OF sidecar)."
    )
    out = dr._reword_catalyst_stale(raw)
    assert out.startswith("Estimates data up to 53d stale (beyond the 45d tolerance)")
    assert "no as-of stamp" in out  # the mechanism is kept — just no longer the lede
    assert "2026-05-14" in out and "worst-case floor" in out
    assert out.endswith("Re-pull CIQ Estimates, or attest the export date (AS_OF sidecar).")
    assert "Catalyst-path as-of UNVERIFIABLE" not in out  # the buried-lede opener is gone
    # fail-through: a caveat that isn't the catalyst template is returned verbatim
    assert dr._reword_catalyst_stale("Net debt/EBITDA (3.8x) is on REPORTED EBITDA") == \
        "Net debt/EBITDA (3.8x) is on REPORTED EBITDA"


def test_catalyst_stale_caveat_reworded_on_committed_brbr_e2e() -> None:
    """(Option 1) End-to-end transform invariant on the committed artifact — guarded on the raw
    caveat carrying the old template, so it survives re-assembly. The rendered caveats section leads
    the catalyst caveat with the staleness discriminator, never the 'no as-of stamp' opener."""
    import json as _json

    p = Path("data/dossiers/BRBR/dossier.json")
    if not p.exists():
        pytest.skip("no committed BRBR dossier.json")
    d = _json.loads(p.read_text())
    raw = " ".join(c for c in (d.get("caveats") or []))
    if "Catalyst-path as-of UNVERIFIABLE" not in raw:
        pytest.skip("committed BRBR no longer carries the catalyst-staleness caveat")
    md = dr.render_markdown(ds.Dossier.model_validate(d))
    flags_md = md.split("Analyst caveats")[1].split("\n## ")[0]
    assert "Estimates data up to" in flags_md and "stale (beyond the" in flags_md
    assert "Catalyst-path as-of UNVERIFIABLE — the CIQ Estimates export carries no as-of stamp;" \
        not in flags_md, "the buried-lede opener must not survive into the render"


def test_caveat_group_block_is_lossless_when_why_or_how_differ() -> None:
    """The collapse must NEVER drop a claim's why-it-matters or how-to-verify (the 'curating never
    deletes a fact' contract). A shared why/how prints once; a why/how that DIFFERS across the group
    prints per-claim. Deterministic on frozen inputs. Twin behaviour lives in dossier.js."""
    # same why, DIFFERENT how → each how survives per-claim (the pre-fix bug dropped both)
    same_why_diff_how = [
        "Guard X (a bull point): 'claim one' — shared why; check source A",
        "Guard X (a bear point): 'claim two' — shared why; check source B",
    ]
    out = "\n".join(dr._caveat_group_block(same_why_diff_how))
    assert out.count("**Guard X** (2 points)") == 1  # collapsed to one advisory
    assert "check source A" in out and "check source B" in out  # both hows kept
    assert out.count("_why it matters:_ shared why") == 1  # shared why printed once

    # DIFFERENT why, same how → each why survives per-claim, the how prints once (shared)
    diff_why_same_how = [
        "Guard Y (a bull point): 'c1' — why alpha; same fix",
        "Guard Y (a bear point): 'c2' — why beta; same fix",
    ]
    out2 = "\n".join(dr._caveat_group_block(diff_why_same_how))
    assert "why alpha" in out2 and "why beta" in out2  # both whys kept
    assert out2.count("_how to verify:_ same fix") == 1  # shared how printed once


def test_801_offering_refinement_is_anchored_and_honest() -> None:
    """(8.01 refinement) A bare "other event" hides the one cause class 8.01 routinely carries — a
    securities offering. The refinement is a deterministic TWO-STEP anchor on the parsed body: an
    offering CONTEXT must fire first, then the instrument picks the label. No anchor → the label is
    UNCHANGED (never a guess). Deterministic on frozen strings → exact pins are safe."""
    debt = ["8.01 Other Events: entered into an underwriting agreement to issue and sell "
            "$600 million principal amount of its 6.500% Senior Notes due 2029"]
    equity = ["8.01 Other Events: underwriting agreement to issue and sell 4,000,000 shares "
              "of its common stock"]
    bare = ["8.01 Other Events: announced a public offering"]
    non = ["8.01 Other Events: announced a settlement of the patent litigation"]
    assert dm._gap_label(["8.01"], debt) == "debt offering (8.01)"
    assert dm._gap_label(["8.01"], equity) == "equity offering (8.01)"
    assert dm._gap_label(["8.01"], bare) == "securities offering (8.01)"
    assert dm._gap_label(["8.01"], non) == "other event (8.01)"  # no context anchor → unchanged
    assert dm._gap_label(["8.01"], None) == "other event (8.01)"  # no body at all → unchanged
    # non-8.01 items never touched by the refinement; composition order preserved
    assert dm._gap_label(["2.02", "9.01"], debt) == "earnings (2.02)"
    assert dm._gap_label(["1.01", "8.01"], debt) == \
        "material agreement (1.01) + debt offering (8.01)"


def test_gap_pct_derivation_refuses_downsampled_series_and_twins_js() -> None:
    """(true 1-day %) The derivation is the detector's own formula on consecutive DAILY points; a
    previous point more than a long weekend away (old weekly JSON) → None — REFUSE, never misstate
    a multi-day move as the 1-day gap. The JS twin must produce the same floats."""
    import json as _json
    import shutil
    import subprocess

    class _P:
        def __init__(self, d: str, n: float | None) -> None:
            self.date, self.name = d, n

    class _SP:
        def __init__(self, pts: list[Any]) -> None:
            self.points = pts

    daily = _SP([_P("2026-01-27", 50.0), _P("2026-01-28", 43.65)])
    weekend = _SP([_P("2026-01-23", 50.0), _P("2026-01-26", 45.0)])  # Fri→Mon: 3d, valid
    weekly = _SP([_P("2026-01-21", 50.0), _P("2026-01-28", 43.65)])  # 7d: refuse
    step2 = _SP([_P("2026-01-26", 50.0), _P("2026-01-28", 45.0)])  # Mon→Wed: 2d, Tue skipped
    assert dr._gap_pct_from_perf(daily, "2026-01-28") == pytest.approx(-0.127)
    assert dr._gap_pct_from_perf(weekend, "2026-01-26") == pytest.approx(-0.10)
    assert dr._gap_pct_from_perf(weekly, "2026-01-28") is None
    assert dr._gap_pct_from_perf(step2, "2026-01-28") is None  # step-2: a weekday skipped, refuse
    assert dr._gap_pct_from_perf(daily, "2026-02-01") is None  # date not in series
    assert dr._gap_pct_from_perf(daily, "2026-01-27") is None  # first point has no prior
    if not shutil.which("node"):
        return
    driver = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { gapPctFromPerf } = await import("__URI__");
const sp = (pts) => ({ points: pts });
console.log(JSON.stringify([
  gapPctFromPerf(sp([{date:"2026-01-27",name:50.0},{date:"2026-01-28",name:43.65}]), "2026-01-28"),
  gapPctFromPerf(sp([{date:"2026-01-23",name:50.0},{date:"2026-01-26",name:45.0}]), "2026-01-26"),
  gapPctFromPerf(sp([{date:"2026-01-21",name:50.0},{date:"2026-01-28",name:43.65}]), "2026-01-28"),
  gapPctFromPerf(sp([{date:"2026-01-26",name:50.0},{date:"2026-01-28",name:45.0}]), "2026-01-28"),
]));
""".replace("__URI__", Path("frontend/views/shared/dossier.js").resolve().as_uri())
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    js = _json.loads(out.stdout)
    assert js[0] == pytest.approx(-0.127) and js[1] == pytest.approx(-0.10)
    assert js[2] is None and js[3] is None  # weekly + step-2 both refused, twinned with Python


def test_drawdown_chart_svg_renders_markers_boundary_and_staggers_a_cluster() -> None:
    """(JS SVG renderer smoke) drawdownChart is web-only (no md twin), so nothing else exercises it.
    Drive it via node on a synthetic DAILY series: assert it emits well-formed SVG with one numbered
    marker per gap row, a detector-window boundary + a HOLLOW pre-window drop marker, no NaN/undef —
    and that a 3-in-a-row cluster staggers to THREE DISTINCT y-lanes (the flip-only bug put markers
    1 and 3 back on the same lane)."""
    import json as _json
    import re
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { drawdownChart } = await import("__URI__");
function weekdays(startISO, n) {
  const out = []; let d = new Date(startISO + "T00:00:00Z");
  while (out.length < n) {
    const wd = d.getUTCDay();
    if (wd !== 0 && wd !== 6) out.push(d.toISOString().slice(0, 10));
    d = new Date(d.getTime() + 86400000);
  }
  return out;
}
const dates = weekdays("2026-01-01", 60);
const names = dates.map(() => 100);
names[8] = 88;                       // pre-window single-day −12% → hollow pre-drop marker
for (let k = 50; k < 60; k++) names[k] = 80;   // three clustered gap-downs land in a low plateau
const pts = dates.map((date, i) => ({ date, name: names[i], benchmark: 100 }));
const sp = { points: pts, name_symbol: "TEST", benchmark_symbol: "IWM",
             name_return: -0.2, benchmark_return: 0.01 };
const rows = [[dates[50]], [dates[51]], [dates[52]]];   // 3 consecutive weekdays → tight cluster
const det = { windowDays: 20, refDate: dates[59], threshold: -0.10 };
const rich = drawdownChart(sp, rows, det);
const empty = drawdownChart({ points: [{ date: "2026-01-01", name: 100 }] }, [], null);
const noDet = drawdownChart(sp, rows, null);
console.log(JSON.stringify({
  svg: rich.svg, preDrops: rich.preDrops, emptySvg: empty.svg, noDetSvg: noDet.svg,
}));
""".replace("__URI__", Path("frontend/views/shared/dossier.js").resolve().as_uri())
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    r = _json.loads(out.stdout)
    svg = r["svg"]  # the exhibit is an <svg> wrapped in a <div class="ds-exhibit">
    assert "<svg viewBox=" in svg and "</svg>" in svg
    assert "NaN" not in svg and "undefined" not in svg  # no unformatted holes
    # one numbered gap marker (r="7.5") per row, each carrying its ordinal
    marker_cys = re.findall(r'<circle cx="[\d.]+" cy="([\d.]+)" r="7\.5"', svg)
    assert len(marker_cys) == 3, f"expected 3 gap markers, got {len(marker_cys)}"
    assert all(f">{n}</text>" in svg for n in (1, 2, 3))
    # the 3-cluster must occupy THREE distinct lanes (stagger), never re-collide
    assert len(set(marker_cys)) == 3, f"clustered markers overlap: {marker_cys}"
    # detector honesty: boundary label + at least one HOLLOW pre-window drop (the index-8 −12%)
    assert "before detector window (20d)" in svg
    assert 'r="5" fill="none"' in svg and len(r["preDrops"]) >= 1
    # guards: too-few points → empty; det=null → markers but no boundary
    assert r["emptySvg"] == ""
    assert "<svg viewBox=" in r["noDetSvg"] and "before detector window" not in r["noDetSvg"]


def test_prewindow_hollow_drop_uses_the_shared_trading_day_rule() -> None:
    """(#3) The chart's pre-window hollow-drop detector must use the SAME "true 1-day move" rule as
    the gap ledger (`isNextTradingDay`), not a loose 1–4-day spacing. A downsampled step-2 pair (a
    weekday skipped) is a MULTI-day slide, not a 1-day crash, and must NOT get a hollow marker — the
    old loose check would have marked it. Also pins the shared rule's spacing/weekday cases."""
    import json as _json
    import shutil
    import subprocess

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { drawdownChart, isNextTradingDay } = await import("__URI__");
// consecutive weekdays, but OMIT one calendar date to inject a step-2 (weekday-skipped) gap
function weekdaysSkip(startISO, n, skip) {
  const out = []; let d = new Date(startISO + "T00:00:00Z");
  while (out.length < n) {
    const wd = d.getUTCDay(); const iso = d.toISOString().slice(0, 10);
    if (wd !== 0 && wd !== 6 && iso !== skip) out.push(iso);
    d = new Date(d.getTime() + 86400000);
  }
  return out;
}
const dates = weekdaysSkip("2026-01-05", 55, "2026-01-13");  // Jan12 Mon → Jan14 Wed = step-2 pair
const names = dates.map(() => 100);
const iStep2 = dates.indexOf("2026-01-14");  // drop across the 2-day gap → must be EXCLUDED
const iCtrl = dates.indexOf("2026-01-08");    // drop across a 1-day gap (Wed→Thu) → INCLUDED
names[iStep2] = 80; names[iCtrl] = 80;        // both −20%, both pre-window
const pts = dates.map((date, i) => ({ date, name: names[i], benchmark: 100 }));
const sp = { points: pts, name_symbol: "T", benchmark_symbol: "IWM",
             name_return: -0.2, benchmark_return: 0 };
const det = { windowDays: 20, refDate: dates[dates.length - 1], threshold: -0.10 };
const { preDrops } = drawdownChart(sp, [], det);  // no gap rows → gapSet empty
console.log(JSON.stringify({
  preDates: preDrops.map((p) => p.date), step2: dates[iStep2], ctrl: dates[iCtrl],
  rule: [isNextTradingDay("2026-01-27","2026-01-28"), isNextTradingDay("2026-01-23","2026-01-26"),
         isNextTradingDay("2026-01-26","2026-01-28"), isNextTradingDay("2026-01-26","2026-01-29"),
         isNextTradingDay("2026-01-22","2026-01-26"), isNextTradingDay("2026-01-21","2026-01-28")],
}));
""".replace("__URI__", Path("frontend/views/shared/dossier.js").resolve().as_uri())
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    r = _json.loads(out.stdout)
    assert r["ctrl"] in r["preDates"], "a true 1-day pre-window drop must still get a hollow marker"
    assert r["step2"] not in r["preDates"], "a step-2 (weekday-skipped) slide must NOT be marked"
    # the shared rule: s1 / Fri→Mon-s3 accepted; s2, s3-non-Friday, s4, s7 refused
    assert r["rule"] == [True, True, False, False, False, False]


def test_clean_item_event_trims_and_drops_and_twins_js() -> None:
    """(8-K display trims) Doubled leading titles, defined-term legalese parentheticals, and
    cross-reference stubs are display noise on a parse-summary (JSON keeps the raw string). A line
    with nothing informative left → None (dropped). The JS twin must produce identical strings."""
    import json as _json
    import shutil
    import subprocess

    doubled = ("8.01 Other Events: Other Events. On February 12, 2026, Concentrix Corporation "
               "(the “Company”) entered into an underwriting agreement (the “Underwriting "
               "Agreement”) with BofA")
    want_doubled = ("8.01 Other Events: On February 12, 2026, Concentrix Corporation entered "
                    "into an underwriting agreement with BofA")
    stub_tail = ("2.03 Item 2.03: Creation of a Direct Financial Obligation or an Obligation "
                 "under an Off-Balance Sheet Arrangement of a Registrant. The information set "
                 "forth in")
    stub_only = "2.03 Item 2.03: The information set forth in Item 1.01 is incorporated"
    unparseable = "UNKNOWN — read filing 0000000000-26-000000 by hand"
    assert dr._clean_item_event(doubled) == want_doubled
    got_stub = dr._clean_item_event(stub_tail)
    assert got_stub is not None and "information set forth" not in got_stub
    assert dr._clean_item_event(stub_only) is None  # nothing informative left → dropped
    multi = ('2.02 Results of Operations and Financial Condition: Results of Operations and '
             'Financial Condition. On June 29, 2026, Concentrix Corporation (the “Company” or '
             '“Concentrix”) issued a press release')
    got_multi = dr._clean_item_event(multi)
    assert got_multi is not None and "(the" not in got_multi  # multi-term defined-term paren too
    assert dr._clean_item_event(unparseable) == unparseable  # non-item line passes through
    if not shutil.which("node"):
        return
    driver = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { cleanItemEvent } = await import("__URI__");
console.log(JSON.stringify([
  cleanItemEvent(__A__),
  cleanItemEvent(__B__),
  cleanItemEvent(__C__),
]));
""".replace("__URI__", Path("frontend/views/shared/dossier.js").resolve().as_uri()) \
    .replace("__A__", _json.dumps(doubled)).replace("__B__", _json.dumps(stub_only)) \
    .replace("__C__", _json.dumps(unparseable))
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    js = _json.loads(out.stdout)
    assert js[0] == want_doubled and js[1] is None and js[2] == unparseable


def test_drawdown_cause_detector_params_are_backcompat_and_single_source() -> None:
    """(detector params) Old committed JSON without the fields validates (defaults None → the
    renderers skip boundary/hollow marks); the constants the assembler copies are the SCREEN's own
    (one source of truth, no drifted duplicate)."""
    dc = ds.DrawdownCause(
        shape=ds.Sourced.unknown(note="x"),
        gap_down_dates=ds.Sourced.unknown(note="x"),
        filings=[],
        revised_guidance=ds.Sourced.unknown(note="x"),
    )
    assert dc.gap_threshold is None and dc.gap_window_days is None
    from vinci.screens.assemble import DECLINE_WINDOW_DAYS, GAP_DOWN_THRESHOLD
    assert dm.GAP_DOWN_THRESHOLD is GAP_DOWN_THRESHOLD
    assert dm.DECLINE_WINDOW_DAYS is DECLINE_WINDOW_DAYS


def test_what_broke_event_study_on_committed_cnxc_e2e() -> None:
    """(event study e2e) On the committed CNXC artifact: the md renders the per-gap ledger; when
    the committed series is DAILY (post-re-assembly) each row carries the true 1-day % equal to the
    detector formula recomputed from the artifact's own points, and every derived % is ≤ the
    detector threshold. Phrasing-independent: values recomputed from the artifact, never hardcoded;
    guarded skips keep it green on pre-daily JSON."""
    import json as _json

    p = Path("data/dossiers/CNXC/dossier.json")
    if not p.exists():
        pytest.skip("no committed CNXC dossier.json")
    d = _json.loads(p.read_text())
    dc = d["mechanical"].get("drawdown_cause") or {}
    gaps = (dc.get("gap_down_dates") or {}).get("value") or []
    if len(gaps) < 2:
        pytest.skip("CNXC no longer has multiple gap-downs")
    md = Path("data/dossiers/CNXC/dossier.md").read_text()
    if "**Read — what broke** · discrete gap-downs:" not in md:
        pytest.skip("committed md pre-dates the event-study render (artifact pass pending)")
    dd = ds.Dossier.model_validate(d)
    pcts = {g: dr._gap_pct_from_perf(dd.mechanical.stock_performance, g) for g in gaps}
    derivable = {g: v for g, v in pcts.items() if v is not None}
    if not derivable:
        pytest.skip("committed series is pre-daily — no derivable 1-day %s yet")
    thr = dc.get("gap_threshold")
    for g, v in derivable.items():
        assert f"- {g} **{v * 100:+.1f}%**" in md, f"md row for {g} must carry the derived %"
        if thr is not None:
            # v is recomputed from the 2dp-ROUNDED rebased index (PerfPoint.name = round(., 2)),
            # so it can differ from the detector's true-close return by ~1e-4; a gap sitting right
            # at the −10% boundary could round to just above thr. Allow that rounding slack so the
            # invariant tests direction/magnitude, not the last basis point of a boundary gap.
            assert v <= thr + 1e-3, f"{g}: derived {v} must be ≤ the detector threshold {thr}"


def test_substantive_non_earnings_items_surface_on_card_and_dropdown_dedups() -> None:
    """(#2 + #3b) The parsed EX-99.1 driver often ISN'T the catalyst — a substantive non-2.02 item
    (VRRM's 8.01 Avis termination, AORT's 1.01 agreement) must show on the visible card beside the
    metrics; 7.01/9.01 stay noise. And a filing shown as a card must NOT be repeated in the "Other
    8-Ks" dropdown (the recurring duplication). Committed-artifact e2e, guarded."""
    class _F:
        def __init__(self, events: list[str], drivers_present: bool = False) -> None:
            self.events = events
            self.drivers = (ds.Sourced.present("m", source_ref="x") if drivers_present
                            else ds.Sourced.unknown(note="n"))

    subs = dr._substantive_events(_F([
        "1.01 Entry into a Material Definitive Agreement: entered into a purchase option",
        "8.01 Other Events: received a termination notice from Avis Budget regarding the contract",
        "7.01 Regulation FD Disclosure: the Company will host a webcast",
        "2.02 Results of Operations and Financial Condition: On May 5 the company reported",
    ]))
    assert len(subs) == 2 and any("purchase option" in s for s in subs) \
        and any("termination notice" in s for s in subs)
    assert dr._substantive_events(_F(["7.01 Regulation FD Disclosure: webcast"])) == []

    pv = Path("data/dossiers/VRRM/dossier.json")
    if pv.exists() and "termination notice from Avis" in pv.read_text():
        md = dr.render_markdown(ds.Dossier.model_validate_json(pv.read_text()))
        wb = md.split("What broke — and did it fall alone?")[1].split("\n### ")[0]
        assert "termination notice from Avis" in wb, "the Avis catalyst must be on the surface"
    pc = Path("data/dossiers/CNXC/dossier.json")
    if pc.exists():
        md = dr.render_markdown(ds.Dossier.model_validate_json(pc.read_text()))
        wb = md.split("What broke — and did it fall alone?")[1].split("\n### ")[0]
        assert "Other 8-Ks at the gap dates" not in wb, "all CNXC gap filings carded → no dropdown"
        for acc in ["0001803599-26-000068", "0001803599-26-000080", "0001803599-26-000133"]:
            assert wb.count(acc) == 1, f"{acc} must appear exactly once (no card+dropdown dup)"


def test_substantive_item_set_twins_between_py_and_js() -> None:
    """The substantive-item regex must be identical in both renderers (a filing carded on one
    surface but dropdowned on the other would diverge web from PDF)."""
    import re as _re
    js = Path("frontend/views/shared/dossier.js").read_text()
    m = _re.search(r"_SUBSTANTIVE = /\^\(([^)]+)\)", js)
    assert m, "JS _SUBSTANTIVE regex not found"
    js_codes = set(m.group(1).replace("\\", "").split("|"))
    _pat = dr._SUBSTANTIVE_ITEM.pattern.split("(")[1].split(")")[0]
    py_codes = set(_pat.replace("\\", "").split("|"))
    assert js_codes == py_codes, f"substantive-item sets diverge: js={js_codes} py={py_codes}"


# --- catalyst calendar (ratified 2026-07-24 · PLACEMENT B) --------------------------------------
def test_next_print_estimate_cadence_positive_and_negative() -> None:
    """A quarterly rhythm (≥4 results 8-Ks, median gap 60–120d) rolls forward past the reference;
    too few prints or an irregular rhythm → None (a qa_flag upstream — an estimate is labeled, a
    guess is forbidden)."""
    q = [date(2025, 10, 8), date(2026, 1, 7), date(2026, 4, 9), date(2026, 7, 9)]
    est = dm._next_print_estimate(q, date(2026, 7, 24))
    assert est is not None
    est_date, basis = est
    assert date(2026, 9, 25) <= est_date <= date(2026, 10, 20)  # ~last + median ≈ 91d
    assert "results 8-Ks" in basis and "2026-07-09" in basis
    assert dm._next_print_estimate(q[:3], date(2026, 7, 24)) is None          # <4 prints
    irregular = [date(2025, 1, 1), date(2025, 1, 20), date(2026, 1, 1), date(2026, 7, 1)]
    assert dm._next_print_estimate(irregular, date(2026, 7, 24)) is None      # rhythm unreadable


def test_catalyst_calendar_assembles_rows_and_fails_loud() -> None:
    """A (cadence) + C (in-horizon stated maturities) assemble; an unreadable cadence is a LOUD
    qa_flag and NO row; an out-of-horizon or undated instrument produces no row."""
    def filing(d: date) -> Filing:
        return Filing(cik="1", form="8-K", filing_date=d, accession=f"a-{d}", items=["2.02"],
                      primary_doc=None)

    inst = ds.CapitalInstrument(
        description="Convertible Bond", type="Bonds and Notes", principal_musd=41.7,
        coupon="3%", floating_rate="NA", maturity_date="2027-01-31", seniority="Senior",
        secured=False, convertible=True, currency="CNY")
    far = inst.model_copy(update={"description": "Far Bond", "maturity_date": "2031-01-01"})
    undated = inst.model_copy(update={"description": "Lease", "maturity_date": None})
    cs = ds.CapitalStructure(
        instruments=ds.Sourced.present([inst, far, undated], source_ref="CIQ panel"),
        summary=ds.Sourced[str].unknown(note="x"), detail_as_of="d",
        maturity_filings=ds.Sourced[str].unknown(note="x"),
        covenant_pointers=ds.Sourced[str].unknown(note="x"),
        covenant_terms=ds.Sourced[str].unknown(note="x"))
    mech = _minimal_mech().model_copy(update={"capital_structure": cs})

    quarterly = [filing(d) for d in (date(2025, 10, 8), date(2026, 1, 7),
                                     date(2026, 4, 9), date(2026, 7, 9))]
    cal = dm._catalyst_calendar(
        _FakeEdgar(filings=quarterly), "1", date(2026, 7, 24), mech)  # type: ignore[arg-type]
    assert [r.date_basis for r in cal.rows] == ["cadence-estimate", "stated"]
    assert cal.rows[0].event == "Next results print" and cal.qa_flags == []
    assert cal.rows[1].expected_date == "2027-01-31" and "Convertible Bond" in cal.rows[1].event
    assert not any("Far Bond" in r.event or "Lease" in r.event for r in cal.rows)

    thin = dm._catalyst_calendar(
        _FakeEdgar(filings=quarterly[:2]), "1", date(2026, 7, 24), mech)  # type: ignore[arg-type]
    assert not any(r.date_basis == "cadence-estimate" for r in thin.rows)
    assert any("cadence unreadable" in q for q in thin.qa_flags)          # loud, never guessed


def test_catalyst_calendar_render_placement_b_and_crux_line() -> None:
    """(PLACEMENT B, re-ordered 2026-07-27) On the committed SMPL json with an injected calendar +
    an analyst dated trigger (VERDICT-nested — the recorded decision's falsifier): the section
    renders AFTER the argument and BEFORE the appendix. It was the Analysis CLOSER until the
    decision re-order; it still follows the argument, but six sections now sit between it and the
    appendix, so this pins the argument→calendar adjacency, NOT a closing position. Rows are
    dated+basis-labeled+cited; the Brief crux carries
    ONE Next-catalyst line (the earliest entry). A dossier WITHOUT the field (every pre-build
    artifact) renders NO section and NO crux line — old JSON round-trips without a phantom."""
    import vinci.scenarios as sc
    p = Path("data/dossiers/SMPL/dossier.json")
    if not p.exists():
        pytest.skip("no committed SMPL dossier.json")
    d = ds.Dossier.model_validate_json(p.read_text())
    cal = ds.CatalystCalendar(rows=[ds.CatalystRow(
        event="Next results print", expected_date="2026-10-08", date_basis="cadence-estimate",
        tests_what="the committed revised outlook", source_ref="cadence: EDGAR submissions")])
    d2 = d.model_copy(update={
        "mechanical": d.mechanical.model_copy(update={"catalyst_calendar": cal})})
    card = sc.read_record("SMPL")
    card2 = card.model_copy(update={"verdict": card.verdict.model_copy(update={
        "dated_triggers": [sc.DatedTrigger(
            trigger="Quest stalling two more quarters", deadline="2027-01-07",
            basis="second print after the 2026-07-21 verdict")]})})
    md = dr.render_markdown(d2, card=card2)
    ia, ic, iap = (md.index("## The argument"), md.index("## Catalyst calendar"),
                   md.index("# Appendix"))
    assert ia < ic < iap                                             # placement B
    sec = md[ic:iap]
    assert "~2026-10-08 `[cadence-estimate]`" in sec
    assert "Re-underwrite trigger: Quest stalling two more quarters" in sec
    assert "~2027-01-07 `[trigger-deadline]`" in sec
    assert "no probabilities, no weighting, no direction" in sec     # the constitution footer
    glance = md.split("## At a glance")[1].split("\n## ")[0]
    assert "**Next catalyst:** Next results print ~2026-10-08" in glance  # earliest entry
    # NEGATIVE: no calendar field AND no dated triggers → no phantom section, no crux line.
    # BOTH sides constructed — the LIVE record carries SMPL's first dated trigger since
    # 2026-07-24, and the LIVE artifact carries a real machine calendar since the 2026-07-24
    # fresh assembly, so the pre-build shape (the pin's subject) must be built, never read.
    bare = card.model_copy(update={"verdict": card.verdict.model_copy(
        update={"dated_triggers": []})})
    d0 = d.model_copy(update={
        "mechanical": d.mechanical.model_copy(update={"catalyst_calendar": None})})
    md0 = dr.render_markdown(d0, card=bare)
    assert "## Catalyst calendar" not in md0
    assert "Next catalyst:" not in md0


def test_catalyst_calendar_js_twin_parity_node() -> None:
    """py==JS: the web renders the SAME calendar — card after the argument, crux line, rows —
    from the same committed-json + injected fixtures (verdict-nested trigger)."""
    import shutil
    import subprocess
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    p = Path("data/dossiers/SMPL/dossier.json")
    if not p.exists():
        pytest.skip("no committed SMPL dossier.json")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const d = JSON.parse(readFileSync("data/dossiers/SMPL/dossier.json"));
d.mechanical.catalyst_calendar = {{ rows: [{{ event: "Next results print",
  expected_date: "2026-10-08", date_basis: "cadence-estimate",
  tests_what: "the committed revised outlook", source_ref: "cadence: EDGAR submissions" }}],
  qa_flags: [] }};
const card = JSON.parse(readFileSync("frontend/scenarios/SMPL.json"));
// camelCase — the PRODUCTION card shape. This fixture injected snake_case `dated_triggers`
// until 2026-07-24, a shape frontend/build.py never emits, so the test passed green while the
// real web card carried nothing and the calendar rendered SHORT of the PDF (SMPL: 2 of 3).
card.verdict.datedTriggers = [{{ trigger: "Quest stalling two more quarters",
  deadline: "2027-01-07", basis: "second print after the 2026-07-21 verdict" }}];
const h = renderDossier(d, null, card);
console.log(JSON.stringify({{
  after_argument: h.indexOf("Catalyst calendar") > h.indexOf("The argument"),
  row: h.includes("2026-10-08") && h.includes("cadence-estimate"),
  trigger: h.includes("Re-underwrite trigger: Quest stalling two more quarters")
           && h.includes("2027-01-07"),
  crux: h.split("brief-crux")[1].includes("Next catalyst:")
        && h.split("brief-crux")[1].includes("2026-10-08"),
  constitution: h.includes("no probabilities, no weighting, no direction"),
}}));"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    got = json.loads(out.stdout)
    assert got == {"after_argument": True, "row": True, "trigger": True,
                   "crux": True, "constitution": True}


def test_dated_operating_events_source_d_real_sentence_and_negatives() -> None:
    """(source D, ratified 2026-07-24 — surfaced by SMPL's September price increase) The REAL Q3
    transcript sentence yields a month-granular STATED row (2026-09; the event text is the CLAUSE
    carrying the action, not the sentence's lead-in); past-tense and backward references and
    month-free text yield NOTHING; an unstated year resolves to the NEXT occurrence of the month
    (March @ a July reference → next year); an explicit year is honored; duplicate mentions dedup
    to one row. Frozen real-text fixture — value-level pins are safe here."""
    smpl = ("Given the significant cost inflation we are experiencing this fiscal year and "
            "believe will continue into the next year, we recently announced a high "
            "single-digit price increase across most of our portfolio that will become "
            "effective in September.")

    def od(*verbatims: str) -> ds.OperatingDriversExtract:
        return ds.OperatingDriversExtract(rows=[
            ds.OperatingDriver(kind=ds.DriverKind.PRICING_ACTION, metric="m", value="v",
                               verbatim=v, source_ref="CIQ transcript: t.rtf",
                               tier="llm-fenced") for v in verbatims])

    ref = date(2026, 7, 24)
    rows = dm._dated_operating_events(od(smpl), ref)
    assert len(rows) == 1
    r = rows[0]
    assert r.expected_date == "2026-09" and r.date_basis == "stated"
    assert "high single-digit price increase" in r.event      # the clause, not the lead-in
    assert r.source_ref == "CIQ transcript: t.rtf"
    # negatives — no row, ever, on a backward or dateless statement
    assert dm._dated_operating_events(
        od("We completed the rollout in September and results were strong."), ref) == []
    assert dm._dated_operating_events(
        od("Elasticities from the increase effective last September remain in line."), ref) == []
    assert dm._dated_operating_events(
        od("We will raise prices to offset inflation."), ref) == []
    # year resolution: rollover + explicit + dedup
    assert [x.expected_date for x in dm._dated_operating_events(
        od("The new plant begins production in March."), ref)] == ["2027-03"]
    assert [x.expected_date for x in dm._dated_operating_events(
        od("The line launches in January 2028 as planned."), ref)] == ["2028-01"]
    assert len(dm._dated_operating_events(od(smpl, smpl), ref)) == 1  # dedup

    # month rows SORT correctly among day rows (lexicographic: YYYY-MM before its month's days)
    assert sorted(["2026-10-08", "2026-09", "2027-01-31"]) == ["2026-09", "2026-10-08",
                                                              "2027-01-31"]


# --- panel-freshness gate (the SMPL 2026-07-24 stale-inputs incident guard) --------------------
def _ie(multiples_as_of: str, tev_as_of: str) -> ds.ImpliedExpectations:
    """A minimal ImpliedExpectations carrying only the two as-of stamps the freshness gate reads."""
    return ds.ImpliedExpectations(
        rows=[], tev=_u(), anchors=_u(), heterogeneity_gate="", tev_as_of=tev_as_of,
        multiples_as_of=multiples_as_of, vintage_coherent=True, coherence_note="",
        net_debt_reconciled=True)


def test_panel_freshness_flag_fires_when_a_panel_predates_the_latest_print() -> None:
    """(SMPL 2026-07-24 incident guard) A CIQ valuation panel whose as-of predates the latest 8-K
    2.02 print → a loud caveat naming the stale panel(s) + the print; a panel on/after the print →
    silence. Orthogonal to the reference-date stale checks: SMPL's panels (2026-06-03 / 2026-06-25)
    sat within 45d of its 2026-07-06 reference, yet the 2026-07-09 FQ3 print postdated both — the
    exact shape this gate exists to catch. Also fail-quiet: no print / no block / odd as-of."""
    print_date = date(2026, 7, 9)
    # STALE: both panels predate the print → fires, names both, dates the oldest lag (36d)
    flag = dm._panel_freshness_flag(_ie("2026-06-03", "2026-06-25"), print_date)
    assert flag is not None
    assert "2026-07-09" in flag and "EDGAR 8-K item 2.02" in flag
    assert "valuation multiples as-of 2026-06-03" in flag
    assert "implied-TEV inputs as-of 2026-06-25" in flag
    assert "the oldest by 36d" in flag                          # 2026-07-09 − 2026-06-03
    # ONE stale panel (TEV fresh, multiples stale) → fires naming ONLY the stale one
    one = dm._panel_freshness_flag(_ie("2026-06-03", "2026-07-21"), print_date)
    assert one is not None and "1 CIQ valuation panel" in one and "implied-TEV" not in one
    # FRESH: both on/after the print → silent (the post-disposition SMPL shape: 07-21 / 07-24)
    assert dm._panel_freshness_flag(_ie("2026-07-21", "2026-07-24"), print_date) is None
    # a panel ON the print date is not "before" it → silent
    assert dm._panel_freshness_flag(_ie("2026-07-09", "2026-07-09"), print_date) is None
    # FAIL-QUIET: no print date, no block, a floor/unparseable as-of → no caveat, never a crash
    assert dm._panel_freshness_flag(_ie("2026-06-03", "2026-06-25"), None) is None
    assert dm._panel_freshness_flag(None, print_date) is None
    assert dm._panel_freshness_flag(_ie("≥2026-07-21", "unknown"), print_date) is None


def test_latest_earnings_print_picks_the_newest_202_and_fails_quiet() -> None:
    """The latest earnings print = the newest 8-K carrying item 2.02; a 7.01-only press release is
    ignored; an empty feed or a raising client → None (the gate then stays silent, never aborts)."""
    def f(d: date, items: list[str]) -> Filing:
        return Filing(cik="1", form="8-K", filing_date=d, accession=f"a-{d}", items=items,
                      primary_doc=None)
    eod = _FakeEdgar(filings=[
        f(date(2026, 4, 9), ["2.02"]), f(date(2026, 7, 9), ["2.02", "9.01"]),
        f(date(2026, 7, 15), ["7.01"])])              # 7.01 press release — NOT an earnings print
    assert dm._latest_earnings_print(eod, "1") == date(2026, 7, 9)
    assert dm._latest_earnings_print(
        _FakeEdgar(filings=[f(date(2026, 7, 15), ["7.01"])]), "1") is None
    assert dm._latest_earnings_print(_FakeEdgar(filings=[]), "1") is None

    class _Boom:
        def recent_filings(self, *a: object, **k: object) -> list[Filing]:
            raise RuntimeError("submissions feed down")
    assert dm._latest_earnings_print(_Boom(), "1") is None      # fail-quiet, no abort


def test_panel_freshness_on_the_real_smpl_panels_before_and_after_the_print() -> None:
    """Real-data before/after of the exact incident, on the committed SMPL dossier's OWN as-of
    stamps. The post-disposition (fresh) panels are SILENT at the real FQ3 print (2026-07-09);
    rewind them to the pre-disposition stale vintages (2026-06-03 / 2026-06-25) and the gate FIRES —
    the caveat that was missing when the BUY was recorded. Invariant, not a value pin: a fresh
    assembly always pulls CIQ on/after the latest print, so 'fresh is silent' is stable."""
    p = Path("data/dossiers/SMPL/dossier.json")
    if not p.exists():
        pytest.skip("no committed SMPL dossier.json")
    ie = ds.Dossier.model_validate_json(p.read_text()).mechanical.valuation.implied_expectations
    assert ie is not None, "SMPL dossier carries an implied-expectations block"
    print_date = date(2026, 7, 9)  # SMPL FQ3 8-K item 2.02 (a fixed historical fact)
    assert dm._panel_freshness_flag(ie, print_date) is None          # committed panels are fresh
    stale = ie.model_copy(update={"multiples_as_of": "2026-06-03", "tev_as_of": "2026-06-25"})
    flag = dm._panel_freshness_flag(stale, print_date)               # rewound → fires
    assert flag is not None and "2026-06-03" in flag and "2026-07-09" in flag


def test_panel_freshness_caveat_reaches_the_human_surface_not_qa() -> None:
    """DELIVERY half (the claim-#7 lesson: a guard the human never sees is useless — a caveat
    that assemble_mechanical emits must land in the human CAVEATS surface, not be swallowed as
    machine qa-telemetry). The freshness caveat carries no QA marker, so ``dossier_flags.partition``
    (the same audience-split assemble.py runs over every emitted flag) routes it to caveats. Pins
    the wiring's delivery leg without standing up the whole assembler."""
    caveat = dm._panel_freshness_flag(_ie("2026-06-03", "2026-06-25"), date(2026, 7, 9))
    assert caveat is not None
    caveats, qa = dflags.partition([caveat])
    assert caveat in caveats and caveat not in qa


def test_positioning_lands_in_the_appendix_in_both_twins_e2e() -> None:
    """(content relocation 2026-07-24) Insider activity + short interest were the ONLY real
    ownership content in the dossier, and they sat inside "The street — estimates & guidance".
    They now render in the APPENDIX as "Ownership & positioning". Pin BOTH twins end-to-end on the
    committed artifacts, because the relocation's failure mode is SILENT: deleting the single call
    site in either renderer drops both facts from the whole document and every other test still
    passes. Presence + TIER placement only — no value pins (the figures are live data)."""
    import shutil
    import subprocess

    src = Path("data/dossiers")
    names = [d.name for d in sorted(src.iterdir())
             if (d / "dossier.json").exists()
             and ((json.loads((d / "dossier.json").read_text()).get("mechanical") or {})
                  .get("catalyst_path") or {}).get("insider_activity")]
    if not names:
        pytest.skip("no committed dossier carries insider activity")

    for t in names:
        md = (src / t / "dossier.md").read_text()
        assert "### Ownership & positioning" in md, f"{t}: md lost the positioning section"
        assert "Insider activity (Form 4, 6m)" in md, f"{t}: md lost insider activity"
        # TIER: it must sit in the appendix, and NOT back in the street section it came from
        appendix = md.split("# Appendix", 1)
        assert len(appendix) == 2, f"{t}: no appendix tier in the md"
        assert "Insider activity" in appendix[1], f"{t}: insider activity is not in the appendix"
        street = md.split("## The street", 1)
        if len(street) == 2:
            # H2 bounds the section now — the section heads were promoted from H3 on 2026-07-27,
            # so splitting on "###" would run past the street into Leverage & survival.
            before_next = street[1].split("\n## ", 1)[0]
            assert "Insider activity" not in before_next, f"{t}: insider is back in the street"

    if not shutil.which("node"):
        pytest.skip("node unavailable")
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    t = names[0]
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync, existsSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const d = JSON.parse(readFileSync("frontend/dossiers/{t}.json"));
const cp = "frontend/scenarios/{t}.json";
const card = existsSync(cp) ? JSON.parse(readFileSync(cp)) : null;
const h = renderDossier(d, null, card);
const street = h.split("The street &mdash; estimates").length > 1
  ? h.split("The street")[1].split('class="card')[0] : "";
console.log(JSON.stringify({{
  hasSection: h.includes("Ownership &amp; positioning") || h.includes("Ownership & positioning"),
  hasInsider: h.includes("Insider activity"),
  hasShort: h.includes("Short interest"),
  streetStillHasIt: street.includes("Insider activity"),
  businessQuality: h.includes("Business quality"),
  oldName: h.includes("Ownership &amp; concentration") || h.includes("Ownership & concentration"),
}}));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    web = json.loads(out.stdout)
    assert web["hasSection"], f"{t}: web lost the Ownership & positioning section"
    assert web["hasInsider"] and web["hasShort"], f"{t}: web lost the positioning facts"
    assert not web["streetStillHasIt"], f"{t}: web still renders positioning inside the street"
    assert web["businessQuality"] and not web["oldName"], f"{t}: web rename missing"


def test_analysis_tier_reads_in_decision_order_e2e() -> None:
    """(re-order 2026-07-27) The Analysis tier is ordered by the QUESTIONS a decision asks, not by
    who produced the content. Pinned on the committed artifacts (the minimal-fixture pin above
    can't reach the sections that need real data) and in BOTH twins, because an order that drifts
    between md and web is the twin-divergence class this repo keeps paying for.

    Order only — no content assertions. The provenance wrapper must stay gone."""
    import shutil
    import subprocess

    want = ["## What broke — and did it fall alone?", "## Business quality", "## The argument",
            "## Catalyst calendar", "## Valuation & own-history", "## Peer comps",
            "## Operating trajectory", "## The street — estimates & guidance",
            "## Leverage & survival", "Analyst caveats"]
    from vinci.dossier.assemble import _read_scenario_card

    checked = 0
    for folder in sorted(Path("data/dossiers").iterdir()):
        jf = folder / "dossier.json"
        if not jf.exists():
            continue
        # RENDER LIVE from the committed JSON. Reading dossier.md off disk would only prove the
        # ARTIFACT is ordered, not the RENDERER — a render.py reorder would ship green until the
        # next artifact pass. Comparing the fresh render back to disk keeps the staleness check.
        dd = ds.Dossier.model_validate_json(jf.read_text())
        md = dr.render_markdown(dd, card=_read_scenario_card(dd.ticker))
        md_p = folder / "dossier.md"
        if md_p.exists():
            assert md == md_p.read_text(), (
                f"{folder.name}: committed dossier.md is STALE against its own JSON — "
                "re-run the artifact pass")
        analysis = md.split("# Analysis — full dossier", 1)
        if len(analysis) != 2:
            continue
        body = analysis[1].split("# Appendix", 1)[0]
        assert "## Mechanical layer" not in body, f"{folder.name}: the provenance wrapper is back"
        seen = [s for s in want if s in body]
        pos = [body.index(s) for s in seen]
        assert pos == sorted(pos), (
            f"{folder.name}: analysis sections out of decision order — got "
            f"{[s for _, s in sorted(zip(pos, seen, strict=True))]}, want the {want} order")
        # FLOOR: ordering a 1-element list is trivially true, so a regression that DROPPED nine of
        # the ten sections would still pass. A real dossier renders nearly all of them.
        assert len(seen) >= 8, f"{folder.name}: only {len(seen)} analysis sections: {seen}"
        checked += 1
    assert checked >= 5, f"expected several committed dossiers, checked {checked}"

    if not shutil.which("node"):
        return
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync, existsSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const d = JSON.parse(readFileSync("frontend/dossiers/SMPL.json"));
const cp = "frontend/scenarios/SMPL.json";
const full = renderDossier(d, null, existsSync(cp) ? JSON.parse(readFileSync(cp)) : null);
// scope to the ANALYSIS tier only — several of these labels also appear in the Brief (route
// hints like "full argument in Analysis"), so a whole-document indexOf finds the wrong one.
// NB the trailing '>' — the TAB buttons carry data-tier="analysis" too (followed by a space
// and role="tab"); only the <section> has it immediately before the closing angle bracket.
const h = full.split('data-tier="analysis">')[1].split('data-tier="appendix">')[0];
const at = (s) => h.indexOf(s);
console.log(JSON.stringify(["What broke", "Business quality", "The argument", "Catalyst calendar",
  "Valuation", "Peer comparison", "Operating trajectory", "The street", "Survival",
  "Analyst caveats"].map((s) => [s, at(s)])));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True)
    found = [(s, i) for s, i in json.loads(out.stdout) if i >= 0]
    idx = [i for _, i in found]
    assert len(found) >= 8, f"web rendered too few analysis sections: {found}"
    assert idx == sorted(idx), f"web analysis sections out of decision order: {found}"


def test_assumption_methodology_renders_in_both_twins_e2e() -> None:
    """(addition #1, 2026-07-27) The per-axis methodology behind an underwrite — the method
    sentence plus the SOURCE-BOUND reference points each leg was chosen against — renders in the
    APPENDIX of both twins. Schema 1.1 captured this from the day it shipped and nothing rendered
    it, so the failure mode is silent: drop the single call site in either renderer and the
    reviewable "why these numbers" vanishes with every other test still green.

    Presence + TIER + source-binding only. The method text is ANALYST prose and is never pinned."""
    import shutil
    import subprocess

    from vinci.dossier.assemble import _read_scenario_card

    names = [d.name for d in sorted(Path("data/dossiers").iterdir())
             if (d / "dossier.json").exists()
             and getattr(_read_scenario_card(d.name), "assumptions", None)]
    if not names:
        pytest.skip("no committed dossier has an underwrite record with assumptions")

    for t in names:
        dd = ds.Dossier.model_validate_json(Path(f"data/dossiers/{t}/dossier.json").read_text())
        card = _read_scenario_card(t)
        md = dr.render_markdown(dd, card=card)
        assert "## How these numbers were set" in md, f"{t}: md lost the methodology section"
        # TIER: it belongs in the appendix (it audits the analyst's inputs), never in Analysis
        head, appendix = md.split("# Appendix", 1)
        assert "## How these numbers were set" not in head, f"{t}: methodology left the appendix"
        # every axis on the record appears, each carrying at least its method sentence
        for axis, a in card.assumptions.items():
            assert f"### {axis.capitalize()}" in appendix, f"{t}: axis {axis} missing"
            assert a.method[:40] in appendix, f"{t}: axis {axis} lost its method sentence"
            # SOURCE-BINDING: a reference point without its source would be an unverifiable number
            for r in a.references:
                assert r.source in appendix, f"{t}: reference {r.label!r} lost its source"

    if not shutil.which("node"):
        pytest.skip("node unavailable")          # skip, never a silent no-op
    dj = Path("frontend/views/shared/dossier.js").resolve().as_uri()
    for t in names:                              # EVERY record, not just the first
        driver = f"""
const handler = {{ get: () => stub, apply: () => stub, construct: () => ({{}}) }};
const stub = new Proxy(function(){{}}, handler);
for (const g of ["window","document","location"]) {{ try {{ globalThis[g] = stub; }} catch {{}} }}
import {{ readFileSync }} from "node:fs";
const {{ renderDossier }} = await import("{dj}");
const d = JSON.parse(readFileSync("frontend/dossiers/{t}.json"));
const card = JSON.parse(readFileSync("frontend/scenarios/{t}.json"));
const h = renderDossier(d, null, card);
// UNESCAPE before comparing: the renderer escapeHtml()s & < > " ' , so an apostrophe in
// "the street's FY2027 figure" would make a raw substring check fail on correct output.
const ap = (h.split('data-tier="appendix">')[1] || "")
  .replace(/&#39;/g, "'").replace(/&quot;/g, '"')
  .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
console.log(JSON.stringify({{
  inAppendix: ap.includes("How these numbers were set"),
  axes: (card.assumptions || []).map((a) => ap.includes(a.method.slice(0, 40))),
  sources: (card.assumptions || []).flatMap((a) => (a.references || [])
    .map((r) => ap.includes(r.source))),
}}));
"""
        out = subprocess.run(["node", "--input-type=module", "-e", driver],
                             capture_output=True, text=True, check=True)
        web = json.loads(out.stdout)
        assert web["inAppendix"], f"{t}: web lost the methodology section from the appendix"
        assert web["axes"] and all(web["axes"]), f"{t}: web dropped an axis method: {web['axes']}"
        # `and web["sources"]` — all([]) is vacuously true, so an empty list must not pass
        assert web["sources"] and all(web["sources"]), f"{t}: web dropped a source"
