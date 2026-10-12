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
          or catalyst — OR a NEAR-TERM FUNDAMENTAL INFLECTION (below); the source ASSERTS the
          premise (not conditional / speculative / merely reported); counter-evidence does not
          outweigh support; FULL retrieval; source reliability not low; no verification hold
  INFLECTION — the narrow second route (review of PR #703, round 3). ALL of: (1) a verified
          claim stating a CHANGE in a FUNDAMENTAL (its verbatim quote names a price / revenue /
          margin / demand / supply / shipments … AND says rise / fall / grow / QoQ / YoY …, with
          a figure; never a share-price or valuation move, never a technical metric) whose
          window is inside the next 2-4 quarters or was measured in the last one; (2) CREDIBLE —
          not a forecast alone: a corroborating MEASURED CHANGE (a measured observation whose
          quote states a change, with a figure) in the thesis's verified evidence, or the
          change is the publisher's OWN data in an industry data report (a
          price tracker forecasting the price it tracks), never a commentator's projection;
          (3) CLEAR ECONOMICS — a fundamental transmission step the source itself states; (4) a
          CONCRETE RESEARCH QUESTION — a source-named exposure to ask it about, composed into
          the decision trace ("do expectations for X already reflect Y in Z?"). A market-regime
          record never takes this route (it argues no earnings mechanism).
  WATCH   everything else — the failed NOW conditions are listed as the reason

Publication COUNT is not a factor anywhere: repeated articles about one origin add nothing,
because evidence is counted by INDEPENDENT ORIGIN. `investment_readiness` stays NOT_ASSESSED — this
tool holds no consensus, market-expectation or valuation data, and says so on every card.
"""

from __future__ import annotations

import re
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
from vinci.theme_intelligence.verify import EARNINGS_STEPS, claim_provenance, is_market_reaction

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
    #: articles classed INDUSTRY DATA REPORT — a publisher reporting its own market data
    data_report_articles: tuple[str, ...] = ()
    #: verified source evidence BEYOND the card's selected citations — the thesis's other linked
    #: claims (context, counter) and the verified claims in the paragraphs its evidence sits in.
    #: Read for LONG-DATED timing only (SKIP-3), never for near-term relevance: leaving a
    #: long-dated sentence off the card must not upgrade a thesis.
    timing_context: tuple[Claim, ...] = ()
    #: why `retrieval` reads FULL for a PARTIAL document (only back matter unread), said plainly
    retrieval_note: str = ""


#: A claim states a CHANGE when its VERBATIM quote says so — read from the source, never from the
#: model's wording.
_CHANGE = re.compile(r"\b(?:increas|rise|rising|rose|grow|grew|growth|accelerat|decelerat|"
                     r"declin|fall|fell|drop|jump|surg|plung|rebound|recover|expand|"
                     r"contracted|contracting|contraction|"  # never the noun: "contract prices"
                     r"QoQ|YoY|y-o-y|q-o-q|MoM|sequential)\w*", re.I)
#: …and the changing variable is a FUNDAMENTAL: the verbatim quote names one (a price, revenue,
#: margin, demand, supply, shipments, inventory, capex …). A technical or workload metric — "the
#: share of prompt tokens reused from GPU memory falls from 90.3% to 54.8%" (SemiAnalysis,
#: 2026-09-28, observed qualifying in the 2026-10-10 run) — is not an earnings variable.
_FUNDAMENTAL = re.compile(r"\b(?:prices?|pricing|ASPs?|revenues?|sales|margins?|earnings|EPS|"
                          r"profits?|demand|shipments?|orders?|bookings?|backlog|capex|"
                          r"capital expenditures?|spending|supply|inventor(?:y|ies)|volumes?|"
                          r"utili[sz]ation|lead times?|costs?)\b", re.I)
#: the publisher's own data, as the extractor records an unattributed figure
_OWN = frozenset({"publisher_own", "publisher's own analysis", ""})


def _fundamental_change(c: Claim) -> bool:
    """A verified figure whose verbatim quote states a CHANGE in a FUNDAMENTAL — never a market
    reaction (a share-price or valuation move)."""
    return ((c.value is not None or any(ch.isdigit() for ch in (c.value_text or "")))
            and c.number_verified is not False
            and _CHANGE.search(c.quote) is not None
            and _FUNDAMENTAL.search(c.quote) is not None
            and not is_market_reaction(c.quote))


def inflection_question(c: Claim, exposures: list[str]) -> str:
    """The concrete research question an inflection poses — composed from the claim's STRUCTURED
    fields and the source-named exposures, never written by a model."""
    what = c.metric or "the change"
    vt = c.value_text or ""
    # the unit's words the figure does not already carry: "10–15%" + "% QoQ" → "10–15% QoQ"
    unit = " ".join(w for w in (c.unit or "").split() if w not in vt)
    fig = " ".join(x for x in (vt, unit) if x)
    return (f"do current earnings estimates and market expectations for {', '.join(exposures)} "
            f"already reflect {what} of {fig}" + (f" in {c.period}" if c.period else "") + "?")


def _material(c: Claim) -> bool:
    return c.kind in (ClaimKind.METRIC, ClaimKind.EVENT, ClaimKind.FORECAST) or (
        c.epistemic in (Epistemic.ACTUAL, Epistemic.FORECAST) and c.kind is not ClaimKind.OPINION)


def compute_priority(st: ThesisState, *, previous: ResearchAction | None,
                     evidence_direction: EvidenceDirection,
                     previous_factors: tuple[PriorityFactor, ...] = ()) -> ResearchPriority:
    regime = st.kind is ThesisKind.MARKET_REGIME
    support_mat = [c for c in st.supporting + st.dislocation + st.catalyst if _material(c)]
    counter_mat = [c for c in st.counter if _material(c)]
    # OBSERVATIONS, not claims: a claim restating the same measure and value from the same
    # original source (its fingerprint) counts once — and a contradiction from OTHER sources is
    # weighed by independent origins, never by how many claims one publisher wrote
    support_obs = {c.fingerprint for c in support_mat}
    support_origins = {c.origin_id or c.article_id for c in support_mat}
    own_counter_obs = {c.fingerprint for c in counter_mat
                       if (c.origin_id or c.article_id) in support_origins}
    external_origins = {c.origin_id or c.article_id for c in counter_mat} - support_origins
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
    # a NEAR-TERM FUNDAMENTAL INFLECTION (the narrow second route — see the module docstring)
    candidates = [c for c in list({c.claim_id: c for c in st.supporting + st.dislocation
                                   + st.catalyst}.values())
                  if timing[c.claim_id][0] in ("near_term", "current")
                  and claim_provenance(c) in (Provenance.FORECAST,
                                              Provenance.MEASURED_OBSERVATION)
                  and _fundamental_change(c)]
    # corroboration is itself a MEASURED change in a fundamental, with a figure — an unrelated
    # measured fact in the same thesis never vouches for a forecast
    corroborating = [c for c in st.supporting + st.dislocation
                     if claim_provenance(c) is Provenance.MEASURED_OBSERVATION
                     and timing[c.claim_id][0] in ("current", "near_term")
                     and _fundamental_change(c)]
    primary = [c for c in candidates if c.article_id in st.data_report_articles
               and (c.attributed_source_text or "").strip().lower() in _OWN]
    credible = [c for c in candidates if c in primary
                or any(m.claim_id != c.claim_id for m in corroborating)]
    # current MEASURED evidence of the thesis's own condition (the sell-off happened this week;
    # the regime is the market's state now) shows it can be investigated now
    current = [c for c in st.supporting if timing[c.claim_id][0] == "current"
               and claim_provenance(c) is Provenance.MEASURED_OBSERVATION]
    near_claims = list({c.claim_id: c for c in forward + disl + current}.values())
    long_range = [c for c in st.supporting + st.dislocation + st.catalyst
                  if timing[c.claim_id][0] == "long_range"]
    # the SOURCE's own long-dated statements beside the evidence the card cites: an omission from
    # the card can hide them, never cancel them (they can only hold a thesis back)
    own = {c.claim_id for c in st.supporting + st.dislocation + st.catalyst}
    for c in st.timing_context:
        if c.claim_id not in own:
            timing.setdefault(c.claim_id, timing_of(c, ref, pub.get(c.article_id)))
    context_long = list({c.claim_id: c for c in st.timing_context if c.claim_id not in own
                         and timing[c.claim_id][0] == "long_range"}.values())
    # the model's horizon LABEL is recorded, never decisive — in either direction
    if near_claims:
        near = "yes"
    elif long_range or context_long:
        near = "longer_term_only"
    else:
        near = "not shown"

    def ids(cs: list[Claim]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(c.claim_id for c in cs))

    windows = "; ".join(f"{c.claim_id}: {timing[c.claim_id][1]}" for c in near_claims[:4])
    exposures = ([f"{n} ({t})" for n, t in st.listed_exposures]
                 + [f"sector: {s}" for s in st.sector_exposures])
    exposure_names = [n for n, _ in st.listed_exposures] + list(st.sector_exposures)
    inflection_ok = bool(credible) and transmission == "source-shown" and bool(
        exposure_names) and not regime
    if not candidates:
        inflection_note = "none — no verified near-term change in a fundamental"
    elif regime:
        inflection_note = "n/a — a market-regime record argues no earnings mechanism"
    elif not credible:
        inflection_note = (f"{len(candidates)} near-term change(s) but NOT credible — a forecast "
                           f"alone: no corroborating measured observation, and not the "
                           f"publisher's own data in an industry data report")
    elif transmission != "source-shown":
        inflection_note = "credible change but the source states no fundamental step"
    elif not exposure_names:
        inflection_note = "credible change but no source-named exposure to research"
    else:
        best = credible[0]
        basis = ("the publisher's own data in an industry data report" if best in primary
                 else "corroborated by a measured observation")
        inflection_note = (f"{best.claim_id}: {timing[best.claim_id][1]} — {basis}; research "
                           f"question: {inflection_question(best, exposure_names)}")
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
                             + f"; {len(long_range)} long-range claim(s)"
                             + (f"; {len(context_long)} long-dated statement(s) of the source "
                                f"beside the cited evidence, not on the card: "
                                f"{', '.join(ids(context_long)[:4])}"
                                + (f" (showing 4 of {len(context_long)})"
                                   if len(context_long) > 4 else "")
                                if context_long else "")
                             + (" — timing UNKNOWN: no dated window anywhere in the source "
                                "evidence" if near == "not shown" else "")
                             + f"; model horizon label {st.horizon.value} (recorded, not "
                               f"decisive)"),
                       claim_ids=ids(near_claims or long_range or context_long)),
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
        PriorityFactor(factor_id="F12_fundamental_inflection",
                       value="qualifies" if inflection_ok else
                       "not credible" if candidates and not credible else
                       "absent" if not candidates else "incomplete",
                       note=inflection_note, claim_ids=ids(credible or candidates)),
        PriorityFactor(factor_id="F8_counterevidence", value=str(len(counter_mat)),
                       note=f"material counter-claims ({len(st.counter)} counter-claims in total); "
                            f"{len(own_counter_obs)} distinct counter-observation(s) from the "
                            f"supporting sources vs {len(support_obs)} supporting; "
                            f"{len(external_origins)} independent contradicting source(s) vs "
                            f"{len(support_origins)} supporting",
                       claim_ids=ids(list(st.counter))),
        PriorityFactor(factor_id="F9_premise_in_source", value=st.stance.value,
                       note="asserted | conditional | speculative | reported_view"),
        PriorityFactor(factor_id="F10_verification_hold",
                       value="HOLD" if st.verification_hold else "clear",
                       note="; ".join(st.hold_reasons) or "no blocking verification issue"),
        PriorityFactor(factor_id="F11_retrieval", value=st.retrieval.value,
                       note="PARTIAL text is never analysed as full"
                            + (f"; {st.retrieval_note}" if st.retrieval_note else "")),
    )

    fired: list[str] = []
    action: ResearchAction
    if not support_mat:
        action, fired = ResearchAction.SKIP, ["SKIP-1 no verified material evidence"]
    elif transmission == "absent":
        action, fired = ResearchAction.SKIP, ["SKIP-2 no fundamental transmission step (a price "
                                              "or valuation move is not one)"]
    elif near == "longer_term_only":
        action, fired = ResearchAction.SKIP, [
            "SKIP-3 longer-term only — no dated window inside the next 2-4 quarters"
            + ("" if long_range else
               f" (the long-dated window is the source's, beside the cited evidence: "
               f"{', '.join(ids(context_long)[:4])} — {timing[context_long[0].claim_id][1]})")]
    else:
        unmet: list[str] = []
        if near != "yes":
            unmet.append("near-term relevance not shown by any dated window — timing UNKNOWN "
                         "in the source evidence; a review should establish it")
        if not st.listed_exposures and not st.sector_exposures:
            unmet.append("no source-named exposure (no point-in-time-verified listed company, no "
                         "sector the source names)")
        if not disl and not inflection_ok:
            unmet.append("no verified dislocation or catalyst" + (
                f", and the near-term inflection does not qualify ({inflection_note})"
                if candidates else ""))
        if st.stance is not StanceInSource.ASSERTED:
            unmet.append(f"premise is {st.stance.value} in the source")
        if external_origins and len(external_origins) >= len(support_origins):
            unmet.append(f"contested: {len(external_origins)} independent source(s) directly "
                         f"contradict it, against {len(support_origins)} supporting")
        elif own_counter_obs and len(own_counter_obs) >= len(support_obs):
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
            route = (f"verified dislocation/catalyst ({len(disl)} claim(s))" if disl else
                     f"a near-term fundamental inflection — {inflection_note}")
            fired = ["NOW all conditions met — near-term window(s) " + windows
                     + "; source-named exposure(s): " + ", ".join(exposures)
                     + f"; {route}; premise asserted; retrieval FULL; reliability "
                       f"{st.reliability}; no hold — an INVESTIGATION of the thesis, not a trade "
                       f"(valuation NOT_ASSESSED)"]

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
