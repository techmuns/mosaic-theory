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
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from vinci.theme_intelligence.display import first_of
from vinci.theme_intelligence.schemas import (
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
    WatchReason,
)
from vinci.theme_intelligence.timewindow import timing_of
from vinci.theme_intelligence.verify import EARNINGS_STEPS, claim_provenance, is_market_reaction

#: the two counter-evidence verdicts that hold a thesis back from RESEARCH NOW, kept as the F8
#: factor's VALUE when one applies (U53) — so every surface reads the verdict from the stored
#: factor, never from the rule trace's words. Otherwise F8's value is the count of material
#: counter-claims, as it always was.
F8_CONTESTED = "contested"
F8_OUTWEIGHS = "outweighs support"
#: how the WATCH trace states each verdict — read ONLY for a version stored before the verdict was
#: a value (`counter_verdict`), and written by the rule from these same words
_CONTESTED_TRACE = "contested: "
_OUTWEIGHS_TRACE = "counter-evidence outweighs support"

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
    #: ETFs, indices and cited baskets the source attaches to the thesis — they COUNT as its
    #: exposure (cards.counted_exposures, 2026-10-16)
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
#: Whole WORD FORMS of the original stems, never open stems: "accelerat\w*" read "AI accelerator
#: revenue was $10bn" as a change, "surg\w*" "surgical procedure volumes", "MoM\w*" "momentum"
#: and "moment", "contracted" "contracted capacity" — level statements that then corroborated each
#: other into a RESEARCH NOW inflection route. The vocabulary is unchanged; only the forms are.
_CHANGE = re.compile(
    r"\b(?:increas(?:e|es|ed|ing|ingly)|ris(?:e|es|en|ing)|rose|gr(?:ow|ows|ew|own|owing|owth)"
    r"|accelerat(?:e|es|ed|ing|ion)|decelerat(?:e|es|ed|ing|ion)|declin(?:e|es|ed|ing)"
    r"|f(?:all|alls|ell|allen|alling)|drop(?:s|ped|ping)?|jump(?:s|ed|ing)?|surg(?:e|es|ed|ing)"
    r"|plung(?:e|es|ed|ing)|rebound(?:s|ed|ing)?|recover(?:s|ed|ing|y|ies)?"
    r"|expand(?:s|ed|ing)?"
    r"|contracted(?=\s+(?:by\s+)?[~≈]?\s?\d)|contracting|contraction"  # never "contract prices"
    r"|QoQ|YoY|y-o-y|q-o-q|MoM|sequential(?:ly)?)\b", re.I)
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
    # a share-price / index performance move is market context, never earnings evidence against
    # the thesis (cards.refile_price_moves; J.P. Morgan acceptance, 2026-10-12)
    counter_mat = [c for c in st.counter if _material(c) and not is_market_reaction(c.quote)]
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
    # a window MOSTLY inside the next 4 quarters that runs past them (an undifferentiated full-year
    # figure for next year): never near-term evidence, never longer-term only (timewindow)
    straddling = list({c.claim_id: c for c in st.supporting + st.dislocation + st.catalyst
                       if timing[c.claim_id][0] == "straddling"}.values())
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
    elif straddling:
        near = "runs_past"
    elif long_range or context_long:
        near = "longer_term_only"
    else:
        near = "not shown"

    def ids(cs: list[Claim]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(c.claim_id for c in cs))

    # the counter-evidence verdict (F8's value when it applies; the WATCH rule's condition below)
    if external_origins and len(external_origins) >= len(support_origins):
        counter: str | None = F8_CONTESTED
    elif own_counter_obs and len(own_counter_obs) >= len(support_obs):
        counter = F8_OUTWEIGHS
    else:
        counter = None
    windows = "; ".join(f"{c.claim_id}: {timing[c.claim_id][1]}" for c in near_claims[:4])
    exposures = ([f"{n} ({t})" for n, t in st.listed_exposures]
                 + [f"instrument: {s}" for s in st.instrument_exposures]
                 + [f"sector: {s}" for s in st.sector_exposures])
    exposure_names = ([n for n, _ in st.listed_exposures] + list(st.instrument_exposures)
                      + list(st.sector_exposures))
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
                             + (f"; {len(straddling)} claim(s) whose window runs past them"
                                if straddling else "")
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
                       claim_ids=ids(near_claims or straddling or long_range or context_long)),
        PriorityFactor(factor_id="F6_recognizable_exposures",
                       value=f"{len(st.listed_exposures)} listed · {len(st.sector_exposures)} "
                             f"sector · {len(st.instrument_exposures)} instrument",
                       note="source-named, point-in-time-verified listed common equity, the "
                            "ETFs / indices / baskets the source attaches, and sectors / themes "
                            "the source names: " + (", ".join(exposures) or "none")
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
        PriorityFactor(factor_id="F8_counterevidence", value=counter or str(len(counter_mat)),
                       note=(f"{len(counter_mat)} " if counter else "")
                       + f"material counter-claims ({len(st.counter)} counter-claims in total); "
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
    watch: tuple[WatchReason, ...] = ()
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
               f"{first_of(list(ids(context_long)), 4, ', ')} — "
               f"{timing[context_long[0].claim_id][1]})")]
    else:
        unmet: list[WatchReason] = []

        def held(code: str, text: str) -> None:  # the evidence itself falls short
            unmet.append(WatchReason(code=code, kind="held", text=text))

        def missing(code: str, text: str) -> None:  # the record could not establish it
            unmet.append(WatchReason(code=code, kind="missing_data", text=text))

        if near == "runs_past":
            held("window_runs_past",
                 "near-term relevance not established — the dated window(s) run past the next "
                 "2-4 quarters (an undifferentiated full-year or multi-quarter figure is not a "
                 "2-4-quarter window): " + "; ".join(
                     f"{c.claim_id}: {timing[c.claim_id][1]}" for c in straddling[:4])
                 + (f" (showing 4 of {len(straddling)})" if len(straddling) > 4 else ""))
        elif near != "yes":
            missing("no_window", "near-term relevance not shown by any dated window — timing "
                                 "UNKNOWN in the source evidence; a review should establish it")
        if not exposure_names:
            if st.unverified_listings:  # named, but no listing verified as of the date
                missing("listing_unverified",
                        "no source-named exposure counted — the listing of "
                        + ", ".join(st.unverified_listings) + " could not be verified as of "
                        "the date (re-checked when the thesis is next assessed)")
            else:
                held("no_exposure", "no source-named exposure (no point-in-time-verified listed "
                                    "company, no ETF, index or basket attached, no sector the "
                                    "source names)")
        if not disl and not inflection_ok:
            held("no_catalyst", "no verified dislocation or catalyst" + (
                f", and the near-term inflection does not qualify ({inflection_note})"
                if candidates else ""))
        if st.stance is not StanceInSource.ASSERTED:
            held("premise_" + st.stance.value, f"premise is {st.stance.value} in the source")
        if counter == F8_CONTESTED:
            held("contested", f"{_CONTESTED_TRACE}{len(external_origins)} independent "
                              f"source(s) directly contradict it, against "
                              f"{len(support_origins)} supporting")
        elif counter == F8_OUTWEIGHS:
            held("outweighed", _OUTWEIGHS_TRACE)
        if st.retrieval is not RetrievalState.FULL:
            missing("partial_text", f"retrieval {st.retrieval.value}")
        if st.reliability == "low":
            held("low_reliability", "low-reliability source only")
        if st.verification_hold:
            missing("verification_hold", "verification hold")
        if unmet:
            action, watch = ResearchAction.WATCH, tuple(unmet)
            fired = ["WATCH (RESEARCH NOW unmet: " + "; ".join(u.text for u in unmet) + ")"]
        else:
            action = ResearchAction.RESEARCH_NOW
            route = (f"verified dislocation/catalyst ({len(disl)} claim(s))" if disl else
                     f"a near-term fundamental inflection — {inflection_note}")
            fired = ["NOW all conditions met — near-term window(s) " + windows
                     + (f" (showing 4 of {len(near_claims)})" if len(near_claims) > 4 else "")
                     + "; source-named exposure(s): " + ", ".join(exposures)
                     + f"; {route}; premise asserted; retrieval FULL; reliability "
                       f"{st.reliability}; no hold — an INVESTIGATION of the thesis, not a trade "
                       f"(valuation NOT_ASSESSED)"]

    reason = f"initial assessment — {fired[0]}" if previous is None else (
        f"no change in action ({_diff_reason(previous_factors, factors)})"
        if previous is action else
        f"{previous.value} → {action.value}: " + _diff_reason(previous_factors, factors))
    # pinned invariant: a hold blocks RESEARCH NOW (it is one of its unmet conditions) — a
    # SKIP → WATCH move under a hold is the rules' own result, never a violation
    if st.verification_hold and action is ResearchAction.RESEARCH_NOW:
        raise AssertionError("a verification hold can never yield RESEARCH NOW")
    return ResearchPriority(
        research_action=action, evidence_direction=evidence_direction,
        investment_readiness=InvestmentReadiness.NOT_ASSESSED, factors=factors,
        rules_fired=tuple(fired), previous_action=previous, change_reason=reason,
        valuation_status=VALUATION_STATUS, watch_reasons=watch)


def watch_reasons_of(pr: ResearchPriority,
                     unverified: Sequence[str] = ()) -> tuple[WatchReason, ...]:
    """A WATCH's unmet conditions: the stored values, or — for a version stored before they were
    values (2026-10-16) — derived from its stored factor VALUES, as `compute_priority` derives
    them (pinned to agree). `unverified`: the card's named listed companies whose listing no line
    verifies (`cards.counted_exposures`). () for any other action."""
    if pr.research_action is not ResearchAction.WATCH:
        return ()
    if pr.watch_reasons:
        return pr.watch_reasons
    f = {x.factor_id: x.value for x in pr.factors}
    out: list[WatchReason] = []

    def add(code: str, kind: Literal["missing_data", "held"], text: str) -> None:
        out.append(WatchReason(code=code, kind=kind, text=text))

    near = f.get("F5_near_term_relevance", "yes")
    if near == "runs_past":
        add("window_runs_past", "held", "its dated windows run past the next 2-4 quarters")
    elif near != "yes":
        add("no_window", "missing_data", "no dated window in the source evidence")
    if exposures_counted(pr) == 0:
        if unverified:
            add("listing_unverified", "missing_data",
                "the listing of " + ", ".join(unverified) + " could not be verified as of the "
                "date (re-checked when the thesis is next assessed)")
        else:
            add("no_exposure", "held", "no source-named exposure")
    if f.get("F7_dislocation_or_catalyst") != "present" \
            and f.get("F12_fundamental_inflection") != "qualifies":
        add("no_catalyst", "held", "no verified dislocation or catalyst")
    stance = f.get("F9_premise_in_source", "asserted")
    if stance != "asserted":
        add("premise_" + stance, "held", f"premise is {stance} in the source")
    verdict = counter_verdict(pr)
    if verdict == F8_CONTESTED:
        add("contested", "held", "contested by independent sources")
    elif verdict == F8_OUTWEIGHS:
        add("outweighed", "held", _OUTWEIGHS_TRACE)
    if f.get("F11_retrieval", "FULL") != "FULL":
        add("partial_text", "missing_data", f"retrieval {f['F11_retrieval']}")
    if f.get("F1_source_reliability") == "low":
        add("low_reliability", "held", "low-reliability source only")
    if f.get("F10_verification_hold") == "HOLD":
        add("verification_hold", "missing_data", "verification hold")
    return tuple(out)


def watch_label(reasons: Sequence[WatchReason]) -> str:
    """What a WATCH waits for, in two words: "needs data" when every unmet condition is missing
    data (the record could not establish it — fixing the data could promote it), "on hold" when
    any is a substantive hold. "" when there are none (any other action)."""
    if not reasons:
        return ""
    return "needs data" if all(r.kind == "missing_data" for r in reasons) else "on hold"


#: the stored F6 value: "<n> listed · <n> sector", with " · <n> instrument" since 2026-10-16
_F6 = re.compile(r"(\d+) listed · (\d+) sector(?: · (\d+) instrument)?")


def exposures_counted(pr: ResearchPriority) -> int:
    """How many exposures the stored rule COUNTED (its F6 value) — the one reader of that value,
    so a surface states the exposure the action was decided on. 0 when the factor is absent."""
    f6 = next((f.value for f in pr.factors if f.factor_id == "F6_recognizable_exposures"), "")
    m = _F6.fullmatch(f6)
    return sum(int(g) for g in m.groups() if g) if m else 0


def counter_verdict(pr: ResearchPriority) -> str | None:
    """The counter-evidence verdict (`F8_CONTESTED` / `F8_OUTWEIGHS`) a stored priority carries, or
    None — read from the F8 factor's VALUE. A version stored before the verdict was a value has a
    count there, and the verdict only in its WATCH trace: read from the rule's own words, here and
    nowhere else (none in the pilot registry, 2026-10-16)."""
    f8 = next((f.value for f in pr.factors if f.factor_id == "F8_counterevidence"), "")
    if f8 in (F8_CONTESTED, F8_OUTWEIGHS):
        return f8
    if f8.isdigit() and pr.research_action is ResearchAction.WATCH:
        trace = " ".join(pr.rules_fired)
        if _CONTESTED_TRACE in trace:
            return F8_CONTESTED
        if _OUTWEIGHS_TRACE in trace:
            return F8_OUTWEIGHS
    return None


def _diff_reason(old: tuple[PriorityFactor, ...], new: tuple[PriorityFactor, ...]) -> str:
    before = {f.factor_id: f.value for f in old}
    changed = [f"{f.factor_id} {before.get(f.factor_id, '?')}→{f.value}" for f in new
               if before.get(f.factor_id) != f.value]
    return "; ".join(changed) or "factor values unchanged (rule re-evaluation)"
