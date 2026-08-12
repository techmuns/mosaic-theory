"""Ranker / triage-layer verification — the structural sort key, fail-loud UNKNOWNs, the Tier-2/3
overlays, the tradeability gate, deterministic ordering, and the no-forward-returns guard.

All synthetic and deterministic. The ranker ORDERS; it never predicts returns — and a structural
test (``test_ranker_reads_no_forward_returns``) asserts that mechanically, mirroring the project's
own lookahead guards.
"""

from __future__ import annotations

import ast
import json
from datetime import date, datetime
from pathlib import Path

from vinci.edgar.client import Filing
from vinci.rank import (
    CauseClass,
    FilingText,
    LiquidityTier,
    RankWeights,
    StructuralDisqualifier,
    character_axis,
    classify_structural_disqualifier,
    depth_axis,
    idiosyncrasy_axis,
    multiple_axis,
    parse_cause_reply,
    rank_candidate,
    rank_candidates,
    render_profile_block,
    scan_structural,
    volume_overlay,
)
from vinci.rank.cause import annotations_from_raw, classify_cause
from vinci.schemas.candidate import CandidateRecord, GateResult, TriageBand
from vinci.schemas.data_record import (
    CoverageTier,
    DataRecord,
    EventType,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
    TypedEvent,
)
from vinci.schemas.envelope import DataField, SourceTier

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
    cik: str = "0000000001",
) -> CandidateRecord:
    ident = Identity(
        internal_id=f"SEC-X-{ticker}", issuer_id="ISS-X", cik=cik, ticker=ticker,
        mic="XNAS", exchange="Nasdaq", eod_symbol=ticker, name=f"{ticker} Inc.",
    )
    prices = PriceFeatures(
        last=_f(50.0), high_52w=_f(120.0), low_52w=_f(40.0),
        drawdown_from_high=_f(drawdown), dist_from_low=_f(0.25),
        ret_3m=_f(-0.2), ret_6m=_f(-0.3), ret_12m=_f(-0.45),
        rel_ret_vs_market=_f(rel),
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


# --- Tier-3 DETERMINISTIC structural-disqualifier channel (DEMOTE-ONLY, source-bound) ---------
def _prices(dd: float | None = -0.50) -> PriceFeatures:
    return _cand(drawdown=dd).data_record.prices


def test_structural_restatement_4_02_fires_source_bound() -> None:
    # Item 4.02 (non-reliance) is a pure item-code signal — no body text needed.
    f = FilingText(
        accession="0001-26-000042", filing_date=date(2026, 5, 1), items=("4.02",), body=""
    )
    flag = classify_structural_disqualifier([f], [], _prices())
    assert flag is not None and "4.02" in flag.signal
    assert "0001-26-000042" in flag.source and "2026-05-01" in flag.source  # source-bound


def test_structural_going_concern_fires_from_filing_text() -> None:
    f = FilingText(
        accession="0001-26-000043", filing_date=date(2026, 5, 2), items=("8.01",),
        body="The Company has concluded there is substantial doubt about its ability to continue "
        "as a going concern.",
    )
    flag = classify_structural_disqualifier([f], [], _prices())
    assert flag is not None and "going-concern" in flag.signal
    assert "0001-26-000043" in flag.source  # bound to the 8-K that carried the language


def test_structural_delisting_3_01_fires() -> None:
    f = FilingText(
        accession="0001-26-000044", filing_date=date(2026, 5, 3), items=("3.01",), body=""
    )
    flag = classify_structural_disqualifier([f], [], _prices())
    assert flag is not None and "3.01" in flag.signal


def _auditor_4_01(body: str) -> StructuralDisqualifier | None:
    """Run the classifier on a single Item-4.01 8-K with the given body."""
    f = FilingText(accession="0001-26-000045", filing_date=date(2026, 5, 4), items=("4.01",),
                   body=body)
    return classify_structural_disqualifier([f], [], _prices())


def test_structural_auditor_exit_4_01_needs_the_resign_dismiss_verb() -> None:
    # A routine rotation (engaging a NEW firm, no verb) is NOT a disqualifier.
    assert _auditor_4_01("The Company engaged a new independent registered public accounting "
                         "firm.") is None
    # A genuine auditor RESIGNATION fires (auditor-initiated → distress).
    flag = _auditor_4_01("Our independent registered public accounting firm resigned effective "
                         "immediately.")
    assert flag is not None and "4.01" in flag.signal


def test_structural_auditor_exit_does_not_fire_on_non_auditor_events() -> None:
    """The bug fix: _AUDITOR_EXIT must detect an AUDITOR exit, not ANY resignation/dismissal. A
    wrong demote sinks a good name out of the human's sight — worse than a miss."""
    # (a) Big-4 UPGRADE — a routine company-initiated switch ("dismissed X, appointed Y, no
    # disagreements"). This is NOT distress; it must NOT fire (the PODD/FUBO false positive).
    assert _auditor_4_01(
        "On May 20, 2025 the Audit Committee dismissed KPMG LLP as the Company's independent "
        "registered public accounting firm and appointed PricewaterhouseCoopers LLP. There were "
        "no disagreements or reportable events with KPMG."
    ) is None
    # (b) A co-filed DIRECTOR resignation (5.02-style text sharing a 4.01 body) must NOT fire —
    # 'resigned' is nowhere near an auditor token.
    assert _auditor_4_01(
        "On May 1, 2026, Jane Doe resigned from the Board of Directors. Separately, the Company "
        "engaged a new independent registered public accounting firm."
    ) is None


def test_structural_auditor_dismissal_for_cause_fires() -> None:
    """A genuine auditor exit DOES fire: a dismissal accompanied by an affirmative cause marker
    (disagreement / material weakness), and an auditor-initiated resignation."""
    for_cause = _auditor_4_01(
        "The Company dismissed its independent registered public accounting firm following "
        "disagreements regarding revenue recognition."
    )
    assert for_cause is not None and "4.01" in for_cause.signal
    material_weakness = _auditor_4_01(
        "The registered public accounting firm was dismissed; management identified a material "
        "weakness in internal control over financial reporting."
    )
    assert material_weakness is not None  # affirmative cause → distress dismissal fires


class _ScanFakeEdgar:
    """EdgarClient stand-in for scan_structural: raises errors uncaught by the per-extractor
    helpers for the 'boom' CIKs (to exercise the scan-level guard), and returns a clean 4.02
    filing (→ restatement flag, no body needed) for the healthy one."""

    def recent_filings(
        self, cik: str, *, forms: tuple[str, ...] = ("8-K",), since: date | None = None
    ) -> list[Filing]:
        if cik == "CIK-IDX":  # IndexError ∉ _filings_for's (HttpError, KeyError, ValueError)
            raise IndexError("malformed parallel SEC arrays")
        if cik == "CIK-GOOD":
            return [Filing(cik=cik, form="8-K", filing_date=date(2026, 3, 1),
                           accession="0001-26-000099", items=["4.02"], primary_doc=None)]
        return []  # CIK-JSON / CIK-TYPE: no filings, so the failure surfaces from companyfacts

    def companyfacts(self, cik: str) -> dict[str, object]:
        if cik == "CIK-JSON":  # JSONDecodeError ⊂ ValueError — not in _shares_for's catch tuple
            raise json.JSONDecodeError("corrupt cache body", "", 0)
        if cik == "CIK-TYPE":  # TypeError ∉ _shares_for's catch tuple
            raise TypeError("bad XBRL 'val' shape")
        return {}


def test_scan_structural_skips_a_name_whose_edgar_fetch_raises() -> None:
    """#1 robustness regression: one bad EDGAR response / corrupt cache must NOT kill the whole
    pass. A candidate whose fetch raises an error the per-extractor helpers don't catch
    (IndexError from mismatched arrays, JSONDecodeError from a corrupt body/cache, TypeError from a
    bad XBRL val) is SKIPPED by scan_structural's per-name guard; the scan completes and still flags
    the healthy names. Mirrors assemble_cohort's per-name resilience."""
    cands = [
        _cand(ticker="IDX", cik="CIK-IDX"),
        _cand(ticker="JSON", cik="CIK-JSON"),
        _cand(ticker="TYPE", cik="CIK-TYPE"),
        _cand(ticker="GOOD", cik="CIK-GOOD"),
    ]
    # http is unused (the GOOD filing has primary_doc=None → no body fetch); None proves that.
    flags = scan_structural(cands, edgar=_ScanFakeEdgar(), http=None)  # type: ignore[arg-type]
    assert set(flags) == {"SEC-X-GOOD"}  # 3 boom names skipped, no crash; healthy name survives
    assert "4.02" in flags["SEC-X-GOOD"].signal


def test_structural_dilution_spiral_fires_on_shares_into_drawdown() -> None:
    # Shares rising materially INTO a falling price = death-spiral signature (FUBO-shaped).
    shares = [(date(2024, 6, 1), 30_000_000.0), (date(2026, 3, 1), 90_000_000.0)]  # +200%
    flag = classify_structural_disqualifier([], shares, _prices(dd=-0.70))
    assert flag is not None and "dilution" in flag.signal
    assert "30,000,000" in flag.source and "90,000,000" in flag.source  # source-bound to the series


def test_structural_dilution_needs_both_legs() -> None:
    grown = [(date(2024, 6, 1), 30_000_000.0), (date(2026, 3, 1), 90_000_000.0)]
    flat = [(date(2024, 6, 1), 30_000_000.0), (date(2026, 3, 1), 31_000_000.0)]
    # price barely down → the "into a falling price" leg fails (a buyer might WANT cheap dilution):
    assert classify_structural_disqualifier([], grown, _prices(dd=-0.20)) is None
    # shares ~flat → no dilution even into a deep drawdown:
    assert classify_structural_disqualifier([], flat, _prices(dd=-0.70)) is None


def test_structural_default_is_unclassified_none_never_fabricated() -> None:
    # A benign results 8-K with no terminal language and no dilution → None (zero effect).
    benign = FilingText(
        accession="BEN", filing_date=date(2026, 5, 5), items=("2.02", "7.01"),
        body="Quarterly results were in line with prior guidance; the outlook is reaffirmed.",
    )
    assert classify_structural_disqualifier([benign], [], _prices()) is None


def test_structural_severity_prefers_restatement_over_co_present_signals() -> None:
    # 4.02 (financials can't be trusted) outranks a co-present 3.01 and a dilution spiral.
    delist = FilingText(accession="D", filing_date=date(2026, 5, 7), items=("3.01",), body="")
    restate = FilingText(accession="R", filing_date=date(2026, 5, 6), items=("4.02",), body="")
    shares = [(date(2024, 6, 1), 30_000_000.0), (date(2026, 3, 1), 90_000_000.0)]
    flag = classify_structural_disqualifier([delist, restate], shares, _prices(dd=-0.70))
    assert flag is not None and "4.02" in flag.signal


def test_structural_flag_has_no_promote_path() -> None:
    """The load-bearing fence: a fired flag can ONLY lower (or leave) a score — NEVER raise it."""
    flag = StructuralDisqualifier(
        signal="going-concern / substantial doubt", source="8-K test", detail="d"
    )
    # Across strong AND weak base setups, the flagged score is always ≤ the unflagged score.
    for dd, rel, pe in [(-0.80, -0.70, 0.01), (-0.45, -0.25, 0.20), (-0.55, -0.45, None)]:
        base = rank_candidate(_cand(drawdown=dd, rel=rel, pe_pctile=pe))
        flagged = rank_candidate(_cand(drawdown=dd, rel=rel, pe_pctile=pe), structural_flag=flag)
        assert flagged.priority_score <= base.priority_score  # demote-only — never promotes
        assert flagged.priority_score <= 0.05  # sunk to/under the structural cap
        assert flagged.structurally_disqualified and flagged.structural_flag is flag


def test_structural_disqualified_sinks_below_a_clean_name_in_the_queue() -> None:
    # A structurally-dead name sinks BELOW a mediocre-but-alive one despite a stronger raw setup.
    flag = StructuralDisqualifier(
        signal="non-reliance/restatement (4.02)", source="8-K 0001-26-000042 item 4.02", detail="d"
    )
    dead = _cand(ticker="DEAD", drawdown=-0.85, rel=-0.80, pe_pctile=0.01,
                 gap_dates=(date(2026, 6, 12),))
    alive = _cand(ticker="ALIVE", drawdown=-0.45, rel=-0.30, pe_pctile=0.20)
    ranked = rank_candidates([dead, alive], structural_flags={"SEC-X-DEAD": flag})
    assert [r.ticker for r in ranked] == ["ALIVE", "DEAD"]  # dead sinks despite the stronger setup
    sunk = next(r for r in ranked if r.ticker == "DEAD")
    assert sunk.structurally_disqualified and sunk.priority_score <= 0.05
    assert sunk.structural_flag is not None and "4.02" in sunk.structural_flag.signal  # carried
    # ticker-keyed flags resolve too (scan_structural emits internal_id; the CLI may pass either):
    by_ticker = rank_candidates([dead, alive], structural_flags={"DEAD": flag})
    assert next(r for r in by_ticker if r.ticker == "DEAD").structurally_disqualified


def test_structural_no_flag_leaves_score_and_sort_untouched() -> None:
    # The honest default: no structural_flags arg → identical to a plain rank (zero effect).
    plain = rank_candidates([_cand(ticker="A"), _cand(ticker="B", drawdown=-0.80, rel=-0.70)])
    none_passed = rank_candidates(
        [_cand(ticker="A"), _cand(ticker="B", drawdown=-0.80, rel=-0.70)], structural_flags=None
    )
    assert [r.ticker for r in plain] == [r.ticker for r in none_passed]
    assert all(not r.structurally_disqualified for r in plain)
    assert all(r.structural_flag is None for r in plain)


# --- Tier-2 volume overlay (minor, bounded) ---------------------------------------------------
def test_volume_overlay_bounded_and_directional() -> None:
    exhausted, _ = volume_overlay(_cand(volume_spike=0.6).data_record.prices)
    normal, _ = volume_overlay(_cand(volume_spike=1.1).data_record.prices)
    heavy, _ = volume_overlay(_cand(volume_spike=12.0).data_record.prices)
    assert exhausted == 0.05 and normal == 0.0 and heavy == -0.05  # small, directional
    assert abs(exhausted) <= 0.05 and abs(heavy) <= 0.05  # an overlay, never a pillar


def test_the_volume_label_describes_magnitude_and_never_names_a_mechanism() -> None:
    """AUDIT 2026-08-12 (STATE.md §5). The input is ONE session's share volume over a 90d average —
    it carries no price direction — so the label may describe HOW MUCH and never WHO or WHY. The
    old strings said "exhausted" and "heavy distribution"; on the 2026-07-29 queue 2 of the 10 names
    labelled "heavy distribution" closed UP that session (VRRM +22.0% on 3.6×, at rank 5).

    POSITIVE: every band states its ratio AND the basis it is a ratio OF — "0.39×" alone cannot
    answer "relative to what", which is the question that opened the audit.
    NEGATIVE: the retired mechanism words never come back."""
    labels = [volume_overlay(_cand(volume_spike=v).data_record.prices)[1]
              for v in (0.39, 1.04, 1.87, 3.60, 12.0)]
    for lab in labels:
        assert "90d avg" in lab, f"label states no basis — 'relative to what?': {lab!r}"
        assert "×" in lab, f"label carries no ratio: {lab!r}"
        for word in ("distribution", "exhausted", "accumulation", "panic", "smart money"):
            assert word not in lab.lower(), (
                f"{lab!r} names a MECHANISM the input cannot contain — one session's volume has no "
                "direction. Describe the magnitude instead.")
    # the bands are still distinguishable by name, and UNKNOWN is still the un-imputed sentinel
    assert len({lab.split(" (")[0] for lab in labels}) == 4
    unevaluable = _cand(volume_spike=None).data_record.prices
    assert volume_overlay(unevaluable) == (0.0, "UNKNOWN")


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
    """No code path in ``vinci.rank`` may import the returns/ledger machinery — the backtest trap.

    Weights are tuned by face-validity only; this asserts mechanically that the package cannot reach
    forward returns, the BUY−AVOID spread, or the post-screen price freeze.
    """
    forbidden = {"vinci.scoring", "vinci.ledger", "vinci.store"}
    pkg = Path(__file__).resolve().parent.parent / "vinci" / "rank"
    scanned = {src.name for src in pkg.glob("*.py")}
    # the Tier-3 deterministic structural-disqualifier channel must be in scope of this guard:
    assert {"structural.py", "ranker.py", "cause.py"} <= scanned
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


# --- the sector fence: coarse SIC sector is assemble/inform, never a scoring/gate input -----------
def test_sector_never_enters_the_scorer_or_the_gate() -> None:
    """``vinci.sectors`` must NOT be imported by the ranker (``vinci.rank``) or the screen gate
    (``vinci.screens``). The coarse sector is a derived view attached in the CLI writer for the
    human-facing cluster roll-up; the moment it reaches a weight / threshold / sort it becomes a
    dressed-up sector-momentum screen — the exact trap Edge-3 was falsified into. This fences it.
    """
    root = Path(__file__).resolve().parent.parent / "vinci"
    scanned: set[str] = set()
    for pkg in ("rank", "screens"):
        for src in (root / pkg).glob("*.py"):
            scanned.add(src.name)
            for node in ast.walk(ast.parse(src.read_text())):
                if isinstance(node, ast.ImportFrom) and node.module is not None:
                    bad = any(node.module == m or node.module.startswith(m + ".")
                              for m in ("vinci.sectors", "vinci.labels", "vinci.sic_table"))
                    assert not bad, f"{src.name} imports {node.module} — labels must not gate/score"
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not any(alias.name.startswith(m) for m in
                                       ("vinci.sectors", "vinci.labels", "vinci.sic_table")), (
                            f"{src.name} imports {alias.name} — labels must not gate/score"
                        )
    assert {"ranker.py", "screen2.py"} <= scanned  # sanity: the scorer + gate files were scanned
