"""Dossier-assembler verification — the assemble-not-conclude line, held by STRUCTURE.

The load-bearing tests here are structural, not behavioural: the dossier schema has nowhere to put a
conclusion, and the dossier package imports nothing that could write a verdict to the ledger. Same
discipline as the ranker's no-forward-returns AST guard.
"""

from __future__ import annotations

import ast
import typing
from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import BaseModel

from vinci.dossier import assemble as dass
from vinci.dossier import ciq, manual_store
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import edgar_fundamentals as efb
from vinci.dossier import flags as dflags
from vinci.dossier import mechanical as dm
from vinci.dossier import render as dr
from vinci.dossier import requirements as dreq
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.edgar.client import EdgarClient, FundamentalSnapshot, all_unknown_snapshot
from vinci.graph.llm import AnthropicLlmClient, LlmClient, LlmError
from vinci.schemas import data_record as sdr
from vinci.schemas.envelope import DataField, SourceTier

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
    }
    assert expected <= models
    offenders: list[str] = []
    for model in models:
        for fname in model.model_fields:
            low = fname.lower()
            if any(tok in low for tok in _FORBIDDEN):
                offenders.append(f"{model.__name__}.{fname}")
    assert not offenders, f"dossier schema carries conclusion-shaped field(s): {offenders}"


def test_synthesis_is_the_only_llm_output_and_carries_no_conclusion() -> None:
    """The synthesis model's fields are exactly the spec'd six — no place for a conclusion.
    evidence_balance is a committed balance read, NOT a verdict/score/direction."""
    assert set(ds.Synthesis.model_fields) == {
        "evidence_balance", "bull_points", "bear_points", "twin_reference_cases",
        "decisive_question", "key_unknowns",
    }


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
    1=buy…5=sell scale, the sell-side) are NOT directional-flagged; a real conclusion still is.
    #2: a long claim is quoted to a word boundary + '…', never mid-word."""
    base = {
        "twin_reference_cases": [], "key_unknowns": [],
        "decisive_question": {
            "question": "does it reverse?", "evidence_for": [], "evidence_against": []
        },
    }
    rating = {
        **base,
        "bull_points": [{"claim": "Sell-side still carries a Buy (1.00) recommendation "
                         "versus the current price", "source_ref": "x"}],
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


def test_survival_capacity_blocks_leverage_with_runway_and_wall() -> None:
    """Mechanism A.3: leverage is promoted to a SURVIVAL block — net-debt/EBITDA + self-funding +
    nearest refinancing wall in one field; a missing leg fails loud as a risk."""
    present, unknown = ds.Sourced.present, ds.Sourced.unknown
    sc = dm._survival_capacity(
        present(2.9, source_ref="EDGAR"), present("~2.6x fwd-adj", source_ref="99.1"),
        present(1.0, source_ref="EDGAR"),  # FCF sign +1 → self-funding
        present("2021 Term Loan Due 2028 (Term Loans) 687 @ 5.7%", source_ref="CIQ"),
    )
    v = sc.value or ""
    assert "net-debt/EBITDA 2.9x" in v and "self-funding" in v
    assert "nearest maturity wall: 2028" in v
    # a missing leg fails loud as a risk, never silently dropped
    risky = dm._survival_capacity(
        unknown(note="no debt/cash"), unknown(note="no guide"), unknown(note="no FCF"),
        unknown(note="no instruments"),
    )
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
        unknown(note="no guide"), present(1.0, source_ref="EDGAR"), unknown(note="no instruments"),
    )
    assert "net-debt/EBITDA 3.9x (CIQ)" in (sc.value or "")
    sc2 = dm._survival_capacity(
        unknown(note="no EBITDA in XBRL"), unknown(note="no guide"),
        present(1.0, source_ref="EDGAR"), unknown(note="no instruments"),
        net_debt=present(200.0, source_ref="CIQ BS"),
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
    """'Maturity' is located by HEADER LABEL (not a fixed index) and surfaced as 'Due YYYY' so
    _nearest_maturity reports the nearest wall; a mis-parsed garbage cell can't fabricate an
    implausible 'Due 1900' (year window). Serials: 46170 = 2026-05-28, 46418 = 2027-01-31."""
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
    assert dm._nearest_maturity(liq) == "nearest maturity wall: 2026"


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
    repeating it on every dossier is boilerplate that adds no per-name value)."""
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
    assert "EV/EBITDA 7.5x vs peer median 10.8x (-31%)" in v
    assert "P/E 13x vs peer median 16.4x (-21%)" in v
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
    assert "Commercial Services 436 (45%)" in (rev.value or "")  # revenue share
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
    ebitda_seg = v.split("EBITDA:")[1].split("; FY 2026")[0]
    assert "(3m)" not in ebitda_seg and "(2m)" not in ebitda_seg  # no fabricated snapshot points
    assert "[3m, 2m n/a]" in ebitda_seg and "62.1 (now)" in ebitda_seg  # read FY col, not FQ2
    assert "[as-of 2026-05-15]" in v


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


def test_guidance_bridge_decodes_serials_and_counts_only_resolved() -> None:
    """(d) GUIDANCE BRIDGE decodes serial dates + range strings (incl. paren-negatives), reports the
    LATEST guide, and counts the track-record ONLY over periods with BOTH a guidance and an actual.
    A present-but-empty metric block is omitted with no flag."""
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
    s = cs.guidance_bridge(_est_bundle({"Guidance": guidance}), as_of=None)
    assert s.status is ds.SourceStatus.PRESENT
    v = s.value or ""
    assert "Revenue: latest guide '290.0 - 310.0' for FY 2025 (dated 20" in v  # max-dated serial
    assert "actual ≥ guided floor 1/2 resolved periods" in v  # resolved-only (FY25 excluded)
    assert "Capital Expenditure: latest guide '(120.00) - (150.00)'" in v and "1/1 resolved" in v
    assert "Gross Margin" not in v  # present-but-empty block omitted, no flag


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


def test_estimates_as_of_and_event_log_ordering() -> None:
    """as-of = the freshest embedded revision date; the log maps columns and sorts newest-first."""
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
    assert asof.value == dates[0]  # as-of matches the freshest event date


def test_revision_event_log_render_caps_at_ten() -> None:
    """The render caps the event log at 10 rows with a '+N more in JSON' note (full list kept)."""
    ev = cs.revision_events(_est_bundle({"Recent Changes": _recent_changes_fx(12)}))
    lines = dr._revision_events_lines(ev)
    assert sum(1 for ln in lines if ln.strip().startswith("- 2")) == 10  # 10 dated rows shown
    assert any("+2 more in JSON" in ln for ln in lines)


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


def test_catalyst_stale_flag_fires_only_past_the_shared_45d() -> None:
    """The catalyst-path staleness caveat reuses the SHARED 45d knob: silent at exactly 45d, fires
    at 46d. An UNKNOWN as-of never fires (fail-quiet on absence)."""
    cp = ds.CatalystPath(
        as_of=ds.Sourced.present("2026-05-15", source_ref="CIQ Estimates→Recent Changes"),
        horizon_read=_u(), acceleration_read=_u(), cross_name_anchor=_u(),
        guidance_bridge=_u(), revision_events=_u(), consensus_stats=_u(),
    )
    assert dm._catalyst_stale_flag(cp, date(2026, 6, 29)) is None  # exactly 45d → silent
    fired = dm._catalyst_stale_flag(cp, date(2026, 6, 30))  # 46d → fires
    assert fired is not None and "staleness caveat" in fired and "2026-05-15" in fired
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
    place of the old thin slot, with the legacy consensus facts relocated UNDER it."""
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
    assert "### Catalyst path (estimates · guidance · revision events) — as-of 2026-05-15" in md
    assert "146.5 (6m) → 62.1 (now)" in md
    assert "Downward Revision · HCW · EBITDA FY 2026: 146.5→62.08" in md
    assert "#### Consensus context (legacy light facts)" in md  # relocated under catalyst path


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

    def sheet(
        self, kind: str, sheet_name: str, *, freq: str | None = None
    ) -> list[list[typing.Any]]:
        try:
            return self._sheets[(kind, sheet_name)]
        except KeyError:
            raise ciq.CiqUnavailableError(f"no {kind}/{sheet_name} in fake bundle") from None

    def workbook(self, kind: str, *, freq: str | None = None) -> None:
        return None


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
        "peer_set", "comparability", "trading_multiples", "fundamental_deltas"
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
    assert "### Peer comps" in md  # the section is wired into the mechanical-layer render
    assert "Roku" in md and "$306.6B" in md  # the roster + caps reach the page
    assert "name NM" in md  # NM survives all the way to the rendered artifact
    assert "earned-vs-residual" in md  # the discount is POSED as a question, not concluded


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
