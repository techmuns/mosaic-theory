"""Deterministic research priority — where to spend ANALYST ATTENTION, never a trade.

`research_action` (RESEARCH NOW / WATCH / SKIP) is a pure function of a thesis's verified state.
No model votes. Each factor is computed from records (verified claims, resolved listings, the
card's transmission chain, verification issues), carries the claim ids behind it, and every rule
that fires is written into `rules_fired` — so a promotion or demotion is traceable to facts.

THE RULES (face-validity, ordered, first decisive match wins; NEVER tuned on forward returns, and
nothing here reads prices, returns, or any other package's outcomes):
  SKIP-1  no verified MATERIAL evidence (a metric / event / forecast, not opinion alone)
  SKIP-2  no profit-transmission step beyond the industry shift
  SKIP-3  explicitly longer-term only, with no near-term evidence and no dislocation / catalyst
  NOW     RESEARCH NOW only if ALL hold: near-term relevance; ≥1 recognizable LISTED exposure the
          source names; a verified dislocation or catalyst; the source ASSERTS the premise (not
          conditional / speculative / merely reported); counter-evidence does not outweigh
          support; FULL retrieval; source reliability not low; no verification hold
  WATCH   everything else — the failed NOW conditions are listed as the reason

Publication COUNT is not a factor anywhere: repeated articles about one origin add nothing,
because evidence is counted by INDEPENDENT ORIGIN. `investment_readiness` stays NOT_ASSESSED — this
tool holds no consensus, market-expectation or valuation data, and says so on every card.
"""

from __future__ import annotations

from dataclasses import dataclass

from vinci.theme_intelligence.schemas import (
    ACTION_RANK,
    Claim,
    ClaimKind,
    Epistemic,
    EvidenceDirection,
    Horizon,
    InvestmentReadiness,
    PriorityFactor,
    Provenance,
    ResearchAction,
    ResearchPriority,
    RetrievalState,
    StanceInSource,
    TransmissionStep,
)

VALUATION_STATUS = ("NOT_ASSESSED — the registry holds no consensus, market-expectation or "
                    "valuation data; an opportunity here is not valuation proof")
_FORWARD_TOKENS = ("ntm", "next twelve", "next 12", "forward", "forecast", "estimate",
                   "next quarter", "coming quarter", "this year", "next year", "guidance")


@dataclass(frozen=True)
class ThesisState:
    reliability: str  # best of the contributing sources: high | medium | low
    supporting: tuple[Claim, ...]
    counter: tuple[Claim, ...]
    dislocation: tuple[Claim, ...]
    catalyst: tuple[Claim, ...]
    listed_exposures: tuple[tuple[str, str], ...]  # (name as written, tickers)
    instrument_exposures: tuple[str, ...]
    transmission: tuple[TransmissionStep, ...]
    horizon: Horizon
    stance: StanceInSource
    verification_hold: bool
    hold_reasons: tuple[str, ...]
    retrieval: RetrievalState


def _material(c: Claim) -> bool:
    return c.kind in (ClaimKind.METRIC, ClaimKind.EVENT, ClaimKind.FORECAST) or (
        c.epistemic in (Epistemic.ACTUAL, Epistemic.FORECAST) and c.kind is not ClaimKind.OPINION)


def _near_term_claim(c: Claim) -> bool:
    probe = " ".join(filter(None, [c.period, c.measure_key, c.quote])).lower()
    return c.epistemic is Epistemic.FORECAST or any(t in probe for t in _FORWARD_TOKENS)


def compute_priority(st: ThesisState, *, previous: ResearchAction | None,
                     evidence_direction: EvidenceDirection,
                     previous_factors: tuple[PriorityFactor, ...] = ()) -> ResearchPriority:
    support_mat = [c for c in st.supporting + st.dislocation + st.catalyst if _material(c)]
    counter_mat = [c for c in st.counter if _material(c)]
    origins = sorted({c.origin_id or c.article_id for c in st.supporting + st.dislocation
                      + st.catalyst})
    beyond = [s for s in st.transmission if s.step != "industry_shift"
              and s.provenance is not Provenance.UNKNOWN]
    shown = [s for s in beyond if s.provenance is Provenance.ARTICLE_FACT]
    transmission = "source-shown" if shown else "inferred" if beyond else "absent"
    near_claims = [c for c in st.supporting + st.dislocation + st.catalyst if _near_term_claim(c)]
    disl = list(st.dislocation) + list(st.catalyst)
    if st.horizon is Horizon.NEXT_2_4_QUARTERS or disl or near_claims:
        near = "yes"
    elif st.horizon is Horizon.LONGER_TERM:
        near = "longer_term_only"
    else:
        near = "unclear"

    def ids(cs: list[Claim]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(c.claim_id for c in cs))

    factors = (
        PriorityFactor(factor_id="F1_source_reliability", value=st.reliability,
                       note="face-validity tier of the contributing channel(s)"),
        PriorityFactor(factor_id="F2_material_evidence", value=str(len(support_mat)),
                       note="verified metric / event / forecast claims supporting the thesis "
                            "(opinion alone is not material)", claim_ids=ids(support_mat)),
        PriorityFactor(factor_id="F3_independent_origins", value=str(len(origins)),
                       note="distinct upstream origins behind the support — counted by ORIGIN, "
                            "never by article count: " + ", ".join(origins)),
        PriorityFactor(factor_id="F4_profit_transmission", value=transmission,
                       note=f"{len(shown)} step(s) shown by the source, {len(beyond)} beyond the "
                            f"industry shift in total"),
        PriorityFactor(factor_id="F5_near_term_relevance", value=near,
                       note=f"horizon {st.horizon.value}; {len(near_claims)} forward/near-term "
                            f"claim(s); {len(disl)} dislocation/catalyst claim(s)",
                       claim_ids=ids(near_claims)),
        PriorityFactor(factor_id="F6_recognizable_listed_exposures",
                       value=str(len(st.listed_exposures)),
                       note="source-named, SEC-resolved listed companies with an exposure role: "
                            + (", ".join(f"{n} ({t})" for n, t in st.listed_exposures) or "none")
                            + (f"; instruments: {', '.join(st.instrument_exposures)}"
                               if st.instrument_exposures else "")),
        PriorityFactor(factor_id="F7_dislocation_or_catalyst",
                       value="present" if disl else "absent",
                       note="verified dislocation / dated catalyst evidence", claim_ids=ids(disl)),
        PriorityFactor(factor_id="F8_counterevidence", value=str(len(counter_mat)),
                       note=f"material counter-claims ({len(st.counter)} counter-claims in total)",
                       claim_ids=ids(list(st.counter))),
        PriorityFactor(factor_id="F9_premise_in_source", value=st.stance.value,
                       note="asserted | conditional | speculative | reported_view"),
        PriorityFactor(factor_id="F10_verification_hold",
                       value="HOLD" if st.verification_hold else "clear",
                       note="; ".join(st.hold_reasons) or "no blocking verification issue"),
        PriorityFactor(factor_id="F11_retrieval", value=st.retrieval.value,
                       note="PARTIAL text is never analysed as full"),
    )

    fired: list[str] = []
    action: ResearchAction
    if not support_mat:
        action, fired = ResearchAction.SKIP, ["SKIP-1 no verified material evidence"]
    elif transmission == "absent":
        action, fired = ResearchAction.SKIP, ["SKIP-2 no profit-transmission step"]
    elif near == "longer_term_only":
        action, fired = ResearchAction.SKIP, ["SKIP-3 longer-term only, nothing near-term"]
    else:
        unmet: list[str] = []
        if near != "yes":
            unmet.append("near-term relevance not shown")
        if not st.listed_exposures:
            unmet.append("no source-named listed company exposure")
        if not disl:
            unmet.append("no verified dislocation or catalyst")
        if st.stance is not StanceInSource.ASSERTED:
            unmet.append(f"premise is {st.stance.value} in the source")
        if counter_mat and len(counter_mat) >= len(support_mat):
            unmet.append("counter-evidence outweighs support")
        if st.retrieval is not RetrievalState.FULL:
            unmet.append(f"retrieval {st.retrieval.value}")
        if st.reliability == "low":
            unmet.append("low-reliability source only")
        if st.verification_hold:
            unmet.append("verification hold")
        if unmet:
            action = ResearchAction.WATCH
            fired = ["WATCH (RESEARCH NOW unmet: " + "; ".join(unmet) + ")"]
        else:
            action = ResearchAction.RESEARCH_NOW
            fired = ["NOW all conditions met — near-term relevance; source-named listed "
                     "exposure(s): " + ", ".join(f"{n} ({t})" for n, t in st.listed_exposures)
                     + f"; verified dislocation/catalyst ({len(disl)} claim(s)); premise "
                     f"asserted; retrieval FULL; reliability {st.reliability}; no hold — an "
                     f"INVESTIGATION of the thesis, not a trade (valuation NOT_ASSESSED)"]

    reason = f"initial assessment — {fired[0]}" if previous is None else (
        f"no change in action ({_diff_reason(previous_factors, factors)})"
        if previous is action else
        f"{previous.value} → {action.value}: " + _diff_reason(previous_factors, factors))
    if previous is not None and ACTION_RANK[action] > ACTION_RANK[previous] \
            and st.verification_hold:
        raise AssertionError("a verification hold can never promote")  # pinned invariant
    return ResearchPriority(
        research_action=action, evidence_direction=evidence_direction,
        investment_readiness=InvestmentReadiness.NOT_ASSESSED, factors=factors,
        rules_fired=tuple(fired), previous_action=previous, change_reason=reason,
        valuation_status=VALUATION_STATUS)


def _diff_reason(old: tuple[PriorityFactor, ...], new: tuple[PriorityFactor, ...]) -> str:
    before = {f.factor_id: f.value for f in old}
    changed = [f"{f.factor_id} {before.get(f.factor_id, '?')}→{f.value}" for f in new
               if before.get(f.factor_id) != f.value]
    return "; ".join(changed) or "factor values unchanged (rule re-evaluation)"
