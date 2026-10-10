"""Deterministic research priority — where to spend ANALYST ATTENTION, never a trade.

`research_action` (RESEARCH NOW / WATCH / SKIP) is a pure function of a thesis's verified state.
No model votes. Each factor is computed from records (verified claims, point-in-time-verified
listings, source-named sector spans, the card's transmission chain, verification issues), carries
the claim ids behind it, and every rule that fires is written into `rules_fired` — so a promotion
or demotion is traceable to facts.

THE RULES (face-validity, ordered, first decisive match wins; NEVER tuned on forward returns, and
nothing here reads prices, returns, or any other package's outcomes):
  SKIP-1  no verified MATERIAL evidence (a metric / event / forecast, not opinion alone)
  SKIP-2  an investment thesis with no FUNDAMENTAL transmission step (volumes / pricing / costs /
          margins / cash flow / earnings). A share-price, valuation or index move is a MARKET
          REACTION and never counts as one. A market-regime record is exempt: it argues a market
          structure, not an earnings mechanism.
  SKIP-3  longer-term only: every dated window in its evidence reaches beyond the next 4 quarters
  NOW     RESEARCH NOW only if ALL hold: near-term relevance shown by a REAL time window (a
          forecast / catalyst window inside the next 2-4 quarters, or a dislocation measured in
          the last quarter — the model's horizon label is recorded, never decisive); a
          source-named EXPOSURE — a point-in-time-verified listed common equity OR a sector /
          theme the source names (a sector opportunity needs no ticker); a verified dislocation
          or catalyst; the source ASSERTS the premise (not conditional / speculative / merely
          reported); counter-evidence does not outweigh support; FULL retrieval; source
          reliability not low; no verification hold
  WATCH   everything else — the failed NOW conditions are listed as the reason

Publication COUNT is not a factor anywhere: repeated articles about one origin add nothing,
because evidence is counted by INDEPENDENT ORIGIN. `investment_readiness` stays NOT_ASSESSED — this
tool holds no consensus, market-expectation or valuation data, and says so on every card.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from vinci.theme_intelligence.schemas import (
    ACTION_RANK,
    SOURCE_LABELS,
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
    ThesisKind,
    TransmissionStep,
)
from vinci.theme_intelligence.timewindow import timing_of
from vinci.theme_intelligence.verify import EARNINGS_STEPS, claim_provenance

VALUATION_STATUS = ("NOT_ASSESSED — the registry holds no consensus, market-expectation or "
                    "valuation data; an opportunity here is not valuation proof")


@dataclass(frozen=True)
class ThesisState:
    reliability: str  # best of the contributing sources: high | medium | low
    supporting: tuple[Claim, ...]
    counter: tuple[Claim, ...]
    dislocation: tuple[Claim, ...]
    catalyst: tuple[Claim, ...]
    #: (name as written, tickers) — POINT-IN-TIME-VERIFIED common equity only
    listed_exposures: tuple[tuple[str, str], ...]
    instrument_exposures: tuple[str, ...]
    transmission: tuple[TransmissionStep, ...]
    horizon: Horizon
    stance: StanceInSource
    verification_hold: bool
    hold_reasons: tuple[str, ...]
    retrieval: RetrievalState
    kind: ThesisKind = ThesisKind.INVESTMENT_THESIS
    #: sectors / themes the source names as exposed (verified spans)
    sector_exposures: tuple[str, ...] = ()
    #: named companies whose listing could NOT be verified as of the date — never an exposure
    unverified_listings: tuple[str, ...] = ()
    as_of: date | None = None
    #: article id -> publication date (dates an observation that states no data date)
    published: tuple[tuple[str, date], ...] = ()


def _material(c: Claim) -> bool:
    return c.kind in (ClaimKind.METRIC, ClaimKind.EVENT, ClaimKind.FORECAST) or (
        c.epistemic in (Epistemic.ACTUAL, Epistemic.FORECAST) and c.kind is not ClaimKind.OPINION)


def compute_priority(st: ThesisState, *, previous: ResearchAction | None,
                     evidence_direction: EvidenceDirection,
                     previous_factors: tuple[PriorityFactor, ...] = ()) -> ResearchPriority:
    regime = st.kind is ThesisKind.MARKET_REGIME
    support_mat = [c for c in st.supporting + st.dislocation + st.catalyst if _material(c)]
    counter_mat = [c for c in st.counter if _material(c)]
    origins = sorted({c.origin_id or c.article_id for c in st.supporting + st.dislocation
                      + st.catalyst})
    fundamental = [s for s in st.transmission if s.step in EARNINGS_STEPS
                   and s.provenance is not Provenance.UNKNOWN]
    reactions = [s for s in st.transmission if s.step == "market_reaction"]
    shown = [s for s in fundamental if s.provenance in SOURCE_LABELS]
    if regime:
        transmission = "n/a (market-regime record)"
    else:
        transmission = "source-shown" if shown else "inferred" if fundamental else "absent"

    if st.as_of is None:
        raise ValueError("ThesisState.as_of is required — the near-term test reads windows "
                         "relative to the run's as-of date, never today's")
    ref = st.as_of
    pub = dict(st.published)
    timing: dict[str, tuple[str, str]] = {}
    for c in st.supporting + st.dislocation + st.catalyst:
        timing.setdefault(c.claim_id, timing_of(c, ref, pub.get(c.article_id)))
    forward = [c for c in st.supporting + st.dislocation + st.catalyst
               if timing[c.claim_id][0] == "near_term"]
    # a DISLOCATION is a mispricing MEASURED in the last quarter; a CATALYST is a dated EVENT
    # inside the next 2-4 quarters. The model's role label is not enough: an opinion, a forecast
    # figure or a stale reading offered as either is listed, never counted
    offered = list({c.claim_id: c for c in st.dislocation + st.catalyst}.values())
    disl = [c for c in offered
            if (timing[c.claim_id][0] == "current"
                and claim_provenance(c) is Provenance.MEASURED_OBSERVATION)
            or (timing[c.claim_id][0] == "near_term" and c.kind is ClaimKind.EVENT)]
    not_counted = [c for c in offered if c not in disl]
    # current MEASURED evidence of the thesis's own condition (the sell-off happened this week;
    # the regime is the market's state now) shows it can be investigated now
    current = [c for c in st.supporting if timing[c.claim_id][0] == "current"
               and claim_provenance(c) is Provenance.MEASURED_OBSERVATION]
    near_claims = list({c.claim_id: c for c in forward + disl + current}.values())
    long_range = [c for c in st.supporting + st.dislocation + st.catalyst
                  if timing[c.claim_id][0] == "long_range"]
    # the model's horizon LABEL is recorded, never decisive — in either direction
    if near_claims:
        near = "yes"
    elif long_range:
        near = "longer_term_only"
    else:
        near = "not shown"

    def ids(cs: list[Claim]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(c.claim_id for c in cs))

    windows = "; ".join(f"{c.claim_id}: {timing[c.claim_id][1]}" for c in near_claims[:4])
    exposures = ([f"{n} ({t})" for n, t in st.listed_exposures]
                 + [f"sector: {s}" for s in st.sector_exposures])
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
                       note=(f"{len(shown)} fundamental step(s) shown by the source, "
                             f"{len(fundamental)} in total"
                             + (f"; {len(reactions)} market-reaction step(s) NOT counted — a price "
                                f"or valuation move is not an earnings mechanism"
                                if reactions else ""))
                       if not regime else "a market-regime record argues a market structure, "
                                          "not an earnings mechanism"),
        PriorityFactor(factor_id="F5_near_term_relevance", value=near,
                       note=(f"{len(near_claims)} claim(s) inside the next 2-4 quarters"
                             + (f" ({windows}" + (f"; showing 4 of {len(near_claims)}"
                                                  if len(near_claims) > 4 else "") + ")"
                                if near_claims else "")
                             + f"; {len(long_range)} long-range claim(s); model horizon label "
                               f"{st.horizon.value} (recorded, not decisive)"),
                       claim_ids=ids(near_claims)),
        PriorityFactor(factor_id="F6_recognizable_exposures",
                       value=f"{len(st.listed_exposures)} listed · {len(st.sector_exposures)} "
                             f"sector",
                       note="source-named, point-in-time-verified listed common equity, and "
                            "sectors / themes the source names: " + (", ".join(exposures)
                                                                     or "none")
                            + (f"; instruments: {', '.join(st.instrument_exposures)}"
                               if st.instrument_exposures else "")
                            + (f"; NOT counted (listing not point-in-time verified): "
                               f"{', '.join(st.unverified_listings)}"
                               if st.unverified_listings else "")),
        PriorityFactor(factor_id="F7_dislocation_or_catalyst",
                       value="present" if disl else "absent",
                       note=f"{len(disl)} counted — a mispricing measured in the last quarter, or "
                            f"a dated event inside the next 2-4 quarters"
                            + (f"; {len(not_counted)} offered but NOT counted (opinion, forecast "
                               f"figure or stale reading): {', '.join(ids(not_counted))}"
                               if not_counted else ""), claim_ids=ids(disl)),
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
        action, fired = ResearchAction.SKIP, ["SKIP-2 no fundamental transmission step (a price "
                                              "or valuation move is not one)"]
    elif near == "longer_term_only":
        action, fired = ResearchAction.SKIP, ["SKIP-3 longer-term only — no dated window inside "
                                              "the next 2-4 quarters"]
    else:
        unmet: list[str] = []
        if near != "yes":
            unmet.append("near-term relevance not shown by any dated window")
        if not st.listed_exposures and not st.sector_exposures:
            unmet.append("no source-named exposure (no point-in-time-verified listed company, no "
                         "sector the source names)")
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
            fired = ["NOW all conditions met — near-term window(s) " + windows
                     + "; source-named exposure(s): " + ", ".join(exposures)
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
