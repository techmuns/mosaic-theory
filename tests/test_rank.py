"""Ranker / triage-layer verification — the structural sort key, fail-loud UNKNOWNs, the Tier-2/3
overlays, the tradeability gate, deterministic ordering, and the no-forward-returns guard.

All synthetic and deterministic. The ranker ORDERS; it never predicts returns — and a structural
test (``test_ranker_reads_no_forward_returns``) asserts that mechanically, mirroring the project's
own lookahead guards.
"""

from __future__ import annotations

import ast
from datetime import date, datetime
from pathlib import Path

from mosaic.rank import (
    CauseClass,
    LiquidityTier,
    RankWeights,
    character_axis,
    depth_axis,
    idiosyncrasy_axis,
    multiple_axis,
    parse_cause_reply,
    rank_candidate,
    rank_candidates,
    render_profile_block,
    volume_overlay,
)
from mosaic.rank.cause import annotations_from_raw, classify_cause
from mosaic.schemas.candidate import CandidateRecord, GateResult, TriageBand
from mosaic.schemas.data_record import (
    CoverageTier,
    DataRecord,
    EventType,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
    TypedEvent,
)
from mosaic.schemas.envelope import DataField, SourceTier

REF = date(2026, 6, 17)
RUN_AT = datetime(2026, 6, 17, 0, 0)


def _f(v: float | None) -> DataField[float]:
    if v is None:
        return DataField.unknown(source="EOD", tier=SourceTier.DERIVED, note="n/a")
    return DataField.present(v, as_of=REF, source="EOD", tier=SourceTier.DERIVED)


def _cand(
    *,
    ticker: str = "FOO",
    drawdown: float | None = -0.50,
    rel: float | None = -0.40,
    pe_pctile: float | None = 0.05,
    gap_dates: tuple[date, ...] = (date(2026, 6, 5),),
    volume_spike: float = 1.0,
    adv_usd: float = 30_000_000.0,
    band: TriageBand = TriageBand.A,
) -> CandidateRecord:
    ident = Identity(
        internal_id=f"SEC-X-{ticker}", issuer_id="ISS-X", cik="0000000001", ticker=ticker,
        mic="XNAS", exchange="Nasdaq", eod_symbol=ticker, name=f"{ticker} Inc.",
    )
    prices = PriceFeatures(
        last=_f(50.0), high_52w=_f(120.0), low_52w=_f(40.0),
        drawdown_from_high=_f(drawdown), dist_from_low=_f(0.25),
        ret_3m=_f(-0.2), ret_6m=_f(-0.3), ret_12m=_f(-0.45),
        rel_ret_vs_sector=_f(rel),
        adv_90d_shares=_f(adv_usd / 50.0), adv_90d_usd=_f(adv_usd),
        turnover=_f(None), volume_spike=_f(volume_spike),
    )
    funds = Fundamentals(
        ev_ebitda=_f(None),
        ev_ebitda_pctile_vs_history=_f(None),  # EV percentile is never wired today
        pe=_f(8.0), pe_pctile_vs_history=_f(pe_pctile),
        fcf_sign=DataField.present(-1, as_of=REF, source="EDGAR", tier=SourceTier.EDGAR),
        op_income_sign=DataField.present(-1, as_of=REF, source="EDGAR", tier=SourceTier.EDGAR),
        net_leverage=_f(None),
    )
    u: DataField[float] = DataField.unknown(source="IBKR", tier=SourceTier.IBKR, note="deferred")
    events = [
        TypedEvent(event_type=EventType.EARNINGS_GAP_DOWN, event_date=d, source="EOD gap-down")
        for d in gap_dates
    ]
    rec = DataRecord(
        identity=ident,
        market_cap=DataField.unknown(source="DERIVED", tier=SourceTier.DERIVED, note="no shares"),
        prices=prices, fundamentals=funds, stress=StressSignals(iv_pctile=u, short_interest=u),
        events=events, overall_coverage_tier=CoverageTier.US_FULL, as_of=REF,
    )
    return CandidateRecord(
        candidate_id=f"{ticker}-screen2-20260617", data_record=rec, screens_fired=["screen_2"],
        gate_results={"G1_drawdown": GateResult.PASS, "G2_idiosyncratic": GateResult.PASS,
                      "G3_multiple_floor": GateResult.PASS if pe_pctile is not None
                      else GateResult.UNKNOWN},
        trigger_reason="t", unknown_gates_for_depth=[], twin_to_rule_out="terminal decline",
        triage_band=band, screen_run_at=RUN_AT,
    )


# --- Tier-1 axis mappings ---------------------------------------------------------------------
def test_depth_axis_monotone_and_clipped() -> None:
    shallow = depth_axis(_cand(drawdown=-0.30).data_record.prices)
    deep = depth_axis(_cand(drawdown=-0.85).data_record.prices)
    mid = depth_axis(_cand(drawdown=-0.575).data_record.prices)
    assert shallow.score == 0.0  # at the −30% gate → no depth credit
    assert deep.score == 1.0  # at the −85% terminal floor → full credit
    assert shallow.score < mid.score < deep.score  # deeper ranks higher


def test_idiosyncrasy_axis_anchor_and_clip() -> None:
    a = idiosyncrasy_axis(_cand(rel=-0.15).data_record.prices)
    b = idiosyncrasy_axis(_cand(rel=-0.60).data_record.prices)
    c = idiosyncrasy_axis(_cand(rel=-0.95).data_record.prices)
    assert a.score is not None and abs(a.score - 0.25) < 1e-9  # −15% / 0.60 anchor
    assert b.score == 1.0  # −60% → full credit
    assert c.score == 1.0  # beyond the anchor stays clipped at 1.0


def test_multiple_axis_at_floor_is_higher() -> None:
    cheap = multiple_axis(_cand(pe_pctile=0.00).data_record.fundamentals)
    top = multiple_axis(_cand(pe_pctile=0.25).data_record.fundamentals)
    assert cheap.score == 1.0  # cheapest vs its own history → full credit
    assert top.score == 0.0  # top of the admitted bottom-quartile band → no credit


def test_multiple_axis_unknown_is_surfaced_not_imputed() -> None:
    ax = multiple_axis(_cand(pe_pctile=None).data_record.fundamentals)
    assert ax.score is None
    assert ax.coverage.value == "unknown"
    assert "UNKNOWN" in ax.label


def test_character_axis_sharp_recent_beats_grind() -> None:
    # ONE axis today: shape (sharp vs grind) + cause (discrete vs bleed) share the gap-down feed.
    grind = character_axis(_cand(gap_dates=()).data_record, CauseClass.UNCLASSIFIED)
    recent = character_axis(
        _cand(gap_dates=(date(2026, 6, 12),)).data_record, CauseClass.UNCLASSIFIED
    )
    stale = character_axis(
        _cand(gap_dates=(date(2026, 1, 1),)).data_record, CauseClass.UNCLASSIFIED
    )
    assert grind.score is not None and recent.score is not None and stale.score is not None
    assert grind.score < stale.score < recent.score  # discrete > grind/bleed; fresher → higher
    assert "grind" in grind.label and "sharp discrete" in recent.label
    assert "LLM: —" in recent.label  # unclassified by default


def test_character_axis_many_gaps_eased_off() -> None:
    one = character_axis(_cand(gap_dates=(date(2026, 6, 12),)).data_record, CauseClass.UNCLASSIFIED)
    many = character_axis(
        _cand(gap_dates=tuple(date(2026, 6, d) for d in range(2, 13))).data_record,
        CauseClass.UNCLASSIFIED,
    )
    assert one.score is not None and many.score is not None
    assert many.score < one.score  # repeated gaps are messier — a single clean drop ranks higher


# --- Tier-3 LLM annotation (colours the character axis; never the sort key) -------------------
def test_llm_structural_break_demotes_mean_revert_boosts() -> None:
    # An older gap → a mid-range discrete baseline, so both the demote and the boost are visible
    # (a very recent gap is already above the mean-revert confirmation floor, making the boost a
    # deliberate no-op — confirmation never *lowers* a name).
    older = _cand(gap_dates=(date(2026, 3, 1),))
    base = character_axis(older.data_record, CauseClass.UNCLASSIFIED).score
    broke = character_axis(older.data_record, CauseClass.STRUCTURAL_BREAK).score
    rev = character_axis(older.data_record, CauseClass.MEAN_REVERT).score
    assert base is not None and broke is not None and rev is not None
    assert broke < base < rev  # terminal-looking demoted; mean-revert boosted
    assert broke < 0.1  # strong demotion toward the structural-break floor


def test_unclassified_annotation_does_not_change_score() -> None:
    # The honest default: no LLM read → cause unchanged from its structural baseline (no fab).
    with_default = rank_candidate(_cand(), cause_class=CauseClass.UNCLASSIFIED).priority_score
    without = rank_candidate(_cand()).priority_score
    assert with_default == without


def test_annotations_from_raw_drops_unknown_labels() -> None:
    ann = annotations_from_raw({"AAA": "structural_break", "BBB": "mean_revert", "CCC": "garbage"})
    assert ann == {"AAA": CauseClass.STRUCTURAL_BREAK, "BBB": CauseClass.MEAN_REVERT}


def test_parse_cause_reply_falls_back_to_unclassified() -> None:
    assert parse_cause_reply({"cause_class": "mean_revert"}) is CauseClass.MEAN_REVERT
    assert parse_cause_reply({"cause_class": "nonsense"}) is CauseClass.UNCLASSIFIED
    assert parse_cause_reply({}) is CauseClass.UNCLASSIFIED


def test_classify_cause_uses_tool_and_empty_text_is_unclassified() -> None:
    class FakeLlm:
        model = "fake"

        def extract(self, *, system: str, user: str, tool: dict[str, object]) -> dict[str, object]:
            return {"cause_class": "structural_break", "rationale": "lost its largest customer"}

    assert classify_cause(FakeLlm(), ticker="X", derate_text="lost AAPL") is (
        CauseClass.STRUCTURAL_BREAK
    )
    assert classify_cause(FakeLlm(), ticker="X", derate_text="   ") is CauseClass.UNCLASSIFIED


# --- Tier-2 volume overlay (minor, bounded) ---------------------------------------------------
def test_volume_overlay_bounded_and_directional() -> None:
    exhausted, _ = volume_overlay(_cand(volume_spike=0.6).data_record.prices)
    normal, _ = volume_overlay(_cand(volume_spike=1.1).data_record.prices)
    heavy, _ = volume_overlay(_cand(volume_spike=12.0).data_record.prices)
    assert exhausted == 0.05 and normal == 0.0 and heavy == -0.05  # small, directional
    assert abs(exhausted) <= 0.05 and abs(heavy) <= 0.05  # an overlay, never a pillar


# --- composite + fail-loud + gate -------------------------------------------------------------
def test_weights_must_sum_to_one() -> None:
    RankWeights()  # default is valid
    try:
        RankWeights(idiosyncrasy=0.9, depth=0.9, character=0.0, multiple=0.0)
        raise AssertionError("expected a validation error for weights not summing to 1")
    except ValueError:
        pass


def test_unknown_axis_costs_credit_and_is_flagged() -> None:
    known = rank_candidate(_cand(pe_pctile=0.05))
    unknown = rank_candidate(_cand(pe_pctile=None))
    assert "multiple" in unknown.unknown_axes
    assert unknown.contributions["multiple"] == 0.0  # no credit, not imputed
    assert unknown.priority_score < known.priority_score  # missing data ranks lower, explicitly


def test_tradeability_gate_demotes_and_flags_thin_names() -> None:
    thick = rank_candidate(_cand(adv_usd=30_000_000.0), deep_work_adv_floor=5_000_000.0)
    thin = rank_candidate(_cand(adv_usd=2_000_000.0), deep_work_adv_floor=5_000_000.0)
    assert not thick.tradeability_gated and thick.liquidity_tier is LiquidityTier.AMPLE
    assert thin.tradeability_gated and thin.liquidity_tier is LiquidityTier.THIN
    assert thin.priority_score < thick.priority_score


def test_default_floor_gates_nobody_above_universe_floor() -> None:
    # Default deep-work floor == the universe ADV floor → a no-op re-check (NOT a second screen).
    assert not rank_candidate(_cand(adv_usd=3_000_001.0)).tradeability_gated


def test_ranking_is_deterministic_and_legible() -> None:
    # A deeper, sharper, more-idiosyncratic, at-floor name must outrank a shallow market-drop name.
    strong = _cand(ticker="STRONG", drawdown=-0.80, rel=-0.70, pe_pctile=0.01,
                   gap_dates=(date(2026, 6, 12),), volume_spike=0.6)
    weak = _cand(ticker="WEAK", drawdown=-0.31, rel=-0.16, pe_pctile=None,
                 gap_dates=(), volume_spike=8.0)
    ranked = rank_candidates([weak, strong])
    assert [r.ticker for r in ranked] == ["STRONG", "WEAK"]
    assert ranked[0].rank == 1 and ranked[1].rank == 2
    assert ranked[0].priority_score > ranked[1].priority_score
    # the queue is the same on a re-run (deterministic)
    assert [r.ticker for r in rank_candidates([strong, weak])] == ["STRONG", "WEAK"]


def test_contributions_reconstruct_quality() -> None:
    r = rank_candidate(_cand())
    assert abs(sum(r.contributions.values()) - r.quality) < 1e-9
    # score is quality + the bounded overlay, then clipped (no gate here)
    assert abs(r.priority_score - max(0.0, min(1.0, r.quality + r.volume_overlay))) < 1e-9


def test_market_cap_joined_into_profile() -> None:
    ranked = rank_candidates([_cand(ticker="MC")], market_caps={"SEC-X-MC": 1.5e9})
    assert ranked[0].market_cap == 1.5e9
    block = render_profile_block(ranked[0])
    assert "$1.50B" in block and "idiosyncrasy" in block  # size shown; profile is legible


# --- the discipline guard: the ranker reads NO forward returns --------------------------------
def test_ranker_reads_no_forward_returns() -> None:
    """No code path in ``mosaic.rank`` may import the returns/ledger machinery — the backtest trap.

    Weights are tuned by face-validity only; this asserts mechanically that the package cannot reach
    forward returns, the BUY−AVOID spread, or the post-screen price freeze.
    """
    forbidden = {"mosaic.scoring", "mosaic.ledger", "mosaic.store"}
    pkg = Path(__file__).resolve().parent.parent / "mosaic" / "rank"
    for src in pkg.glob("*.py"):
        tree = ast.parse(src.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                mod = node.module
                hit = any(mod == f or mod.startswith(f + ".") for f in forbidden)
                assert not hit, f"{src.name} imports {mod} — the ranker must not read returns"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    hit = any(alias.name.startswith(f) for f in forbidden)
                    assert not hit, f"{src.name} imports {alias.name} — ranker reads no returns"
