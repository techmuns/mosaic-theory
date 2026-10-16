"""The universal nine-section Living Thesis Card — composed from records, rendered three ways.

COMPOSE. `compose_card` builds a `CardContent` from persisted records only: the thesis key, the
verified hypothesis view of the contributing article(s), verified claims, source-named mentions,
sector spans and their point-in-time SEC resolutions, the deterministic priority, and the
contribution history. An update overlays the new article on the PRIOR version's content (which
stays immutable in its own row). Nothing on a card is hand-written: every line the source supports
cites claim ids and is labelled by WHAT those claims are — MEASURED OBSERVATION, FORECAST or SOURCE
OPINION, the weakest of them — and every line this tool composed says MODEL INFERENCE.

RENDER. HTML (web), HTML (print: every section and audit detail expanded), Markdown and JSON all
walk the SAME `CardContent`, in the SAME fixed order 01→09, with the same field ids — so the four
cannot disagree, and a cross-consistency test pins it. The web view is a COMPACT DECISION VIEW:
the header and 01 / 02 / 06 / 08 open, 03-05 / 07 / 09 folded IN PLACE (the order never changes),
and engine codes, claim ids, change classes and the rule trace hidden behind one "audit" toggle.
The print view opens everything, so the printed record carries every field with no silent loss.

A sentence that failed verification (a BLOCK issue) is never rendered as the source's word: it is
shown as WITHHELD with the reason, its text kept only behind a disclosure for audit.
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any, TypeVar

from vinci.theme_intelligence.display import clip
from vinci.theme_intelligence.parse import clean_title
from vinci.theme_intelligence.priority import (
    F8_CONTESTED,
    F8_OUTWEIGHS,
    counter_verdict,
    exposures_counted,
    unverified_words,
    watch_label,
    watch_reasons_of,
)
from vinci.theme_intelligence.schemas import (
    EXPOSURE_ROLES,
    SECTION_IDS,
    SOURCE_LABELS,
    AffectedCompany,
    AffectedView,
    Article,
    CardContent,
    CardHeader,
    CardSentence,
    ChangeClass,
    ChangeItem,
    Claim,
    ClaimKind,
    Decision,
    Direction,
    EnrichmentCandidate,
    EnrichmentSet,
    Epistemic,
    EvidenceDirection,
    EvidenceRow,
    Horizon,
    LinkRole,
    Listing,
    MentionRole,
    PitStatus,
    Provenance,
    ResearchPriority,
    ResolutionStatus,
    SectorExposure,
    SourceRef,
    Thesis,
    ThesisClaimLink,
    ThesisKind,
    ThesisVersion,
    TransmissionStep,
    WhatChanged,
    WhatCouldGoWrong,
    WhyNow,
)
from vinci.theme_intelligence.verify import (
    VerifiedHypothesis,
    VerifiedSector,
    card_sentences,
    is_market_reaction,
    label_for,
    norm_name,
    provenance_of,
    same_sentence_reread,
)

HORIZON_LABEL = {Horizon.NEXT_2_4_QUARTERS: "Next 2-4 quarters",
                 Horizon.LONGER_TERM: "Longer term (beyond 4 quarters)",
                 Horizon.UNCLEAR: "Unclear in the source"}
_EARNINGS_UNKNOWN = ("UNKNOWN — the source does not quantify an effect on listed-company "
                     "earnings; any earnings impact is a hypothesis to test, not a finding")
_REGIME_EARNINGS = ("NOT APPLICABLE — a market-regime record argues a market structure "
                    "(breadth, correlation, dispersion), not an earnings mechanism; its research "
                    "use is SELECTION, not an earnings call")
_NO_CATALYST = "UNKNOWN — the source names no dated catalyst or earnings window"
STEP_ORDER = ("industry_shift", "volumes", "pricing", "costs", "margins", "cash_flow",
              "listed_earnings", "market_reaction")
STEP_LABEL = {"industry_shift": "Industry shift", "volumes": "Volumes", "pricing": "Pricing",
              "costs": "Costs", "margins": "Margins", "cash_flow": "Cash flow",
              "listed_earnings": "Listed-company earnings",
              "market_reaction": "Market reaction — a price / valuation move, NOT an earnings "
                                 "mechanism"}
KIND_LABEL = {ThesisKind.INVESTMENT_THESIS: "Investment thesis",
              ThesisKind.MARKET_REGIME: "Market-regime record"}


def _cs(text: str, prov: Provenance, ids: Iterable[str] = ()) -> CardSentence:
    return CardSentence(text=text.strip(), provenance=prov, claim_ids=tuple(dict.fromkeys(ids)))


def _src(ids: Iterable[str], claims: dict[str, Claim]) -> Provenance:
    """The label of a line that restates verified source claims: the weakest of them."""
    return label_for(ids, claims) or Provenance.MODEL_INFERENCE


#: SYSTEM-LABEL brackets: everything inside ⟨…⟩ is composed by this code (figure labels, an
#: update's date and publisher), never asserted by the source. The number check in `verify.py`
#: ignores what sits inside them.
LABEL_OPEN, LABEL_CLOSE = "⟨", "⟩"
_FIGURES = f"{LABEL_OPEN}cited figures:"
_FIG_SUFFIX = re.compile(r"\s*⟨cited figures:[^⟩]*⟩\s*$")


def figure_labels(claims: Iterable[Claim]) -> str:
    """Labels for the FIGURES a sentence cites, read from the structured claims — never from the
    prose — so a sentence cannot present a forecast as an actual, or a chart reading as exact."""
    tags: list[str] = []
    for c in claims:
        if c.value_text is None:
            continue
        for t in ("forecast" if c.epistemic is Epistemic.FORECAST else None,
                  "approximate, read from a chart" if c.approximate and c.chart_derived
                  else "approximate" if c.approximate else None,
                  f"data as of {c.measured_as_of.isoformat()}" if c.measured_as_of else None,
                  "STALE series" if any(q.startswith("stale series") for q in c.qualifiers)
                  else None):
            if t and t not in tags:
                tags.append(t)
    return "; ".join(tags)


def labelled(s: CardSentence, claims: dict[str, Claim]) -> CardSentence:
    if _FIGURES in s.text:
        return s
    tags = figure_labels(claims[c] for c in s.claim_ids if c in claims)
    if not tags:
        return s
    return s.model_copy(update={"text": f"{s.text} {LABEL_OPEN}cited figures: {tags}"
                                        f"{LABEL_CLOSE}"})


#: A CONDITIONAL line says what could, might or would happen, or what follows IF — the source's
#: argument, never a measured observation, whatever claims it cites. Capitalised "May" is the
#: month and is not matched.
_CONDITIONAL = re.compile(r"\b(?:could|might|would|may|if|Could|Might|Would|If)\b")
_FACT_LABELS = frozenset({Provenance.MEASURED_OBSERVATION, Provenance.EXTERNALLY_VERIFIED,
                          Provenance.ARTICLE_FACT})
_L = TypeVar("_L", CardSentence, ChangeItem, TransmissionStep)


def capped_label(prov: Provenance, text: str) -> Provenance:
    """The label a line may carry: a conditional line is at most SOURCE OPINION."""
    if prov in _FACT_LABELS and _CONDITIONAL.search(_FIG_SUFFIX.sub("", text)):
        return Provenance.SOURCE_OPINION
    return prov


def capped_conditionals(card: CardContent) -> CardContent:
    """Every line of the card under `capped_label`. Observed in the pilot (2026-10-12): two risk
    lines on a Nomura card — "Rising UST yields could create a feedback loop…" — read MEASURED
    OBSERVATION because the claims they cited were observations; the reviewer flagged both."""

    def cap(xs: tuple[_L, ...]) -> tuple[_L, ...]:
        return tuple(x if (p := capped_label(x.provenance, x.text)) is x.provenance
                     else x.model_copy(update={"provenance": p}) for x in xs)

    n, w, d = card.s06_why_now, card.s07_what_could_go_wrong, card.s08_decision
    return card.model_copy(update={
        "s01_bottom_line": cap(card.s01_bottom_line),
        "s02_what_changed": card.s02_what_changed.model_copy(
            update={"items": cap(card.s02_what_changed.items)}),
        "s03_transmission": cap(card.s03_transmission),
        "s06_why_now": n.model_copy(update={"near_term": cap(n.near_term),
                                            "structural": cap(n.structural)}),
        "s07_what_could_go_wrong": w.model_copy(update={
            "counter_evidence": cap(w.counter_evidence),
            "alternative_mechanisms": cap(w.alternative_mechanisms),
            "market_risks": cap(w.market_risks), "price_context": cap(w.price_context)}),
        "s08_decision": d.model_copy(update={"next_step": cap((d.next_step,))[0]})})


def replace_sentence(card: CardContent, sid: str, new: CardSentence) -> CardContent:
    """The card with ONE line replaced — `sid` as `verify.card_sentences` numbers it (s01.i,
    s02.i, s03.i, s06.i over near + structural, s07.i over counter + alternatives + risks + price
    context, s08.next). An unknown id raises."""
    sec, _, idx = sid.partition(".")
    upd = {"text": new.text, "provenance": new.provenance, "claim_ids": new.claim_ids}

    def put(xs: tuple[_L, ...], i: int) -> tuple[_L, ...]:
        if not 0 <= i < len(xs):
            raise ValueError(f"no card line {sid}")
        return xs[:i] + (xs[i].model_copy(update=upd),) + xs[i + 1:]

    if sid == "s08.next":
        return card.model_copy(update={"s08_decision": card.s08_decision.model_copy(
            update={"next_step": new})})
    i = int(idx) if idx.isdigit() else -1
    if sec == "s01":
        return card.model_copy(update={"s01_bottom_line": put(card.s01_bottom_line, i)})
    if sec == "s02":
        wc = card.s02_what_changed
        return card.model_copy(update={"s02_what_changed": wc.model_copy(
            update={"items": put(wc.items, i)})})
    if sec == "s03":
        return card.model_copy(update={"s03_transmission": put(card.s03_transmission, i)})
    if sec == "s06":
        n = card.s06_why_now
        k = len(n.near_term)
        part = {"near_term": put(n.near_term, i)} if i < k else {
            "structural": put(n.structural, i - k)}
        return card.model_copy(update={"s06_why_now": n.model_copy(update=part)})
    if sec == "s07":
        w = card.s07_what_could_go_wrong
        for name in ("counter_evidence", "alternative_mechanisms", "market_risks",
                     "price_context"):
            xs = getattr(w, name)
            if i < len(xs):
                return card.model_copy(update={"s07_what_could_go_wrong": w.model_copy(
                    update={name: put(xs, i)})})
            i -= len(xs)
    raise ValueError(f"no card line {sid}")


def is_price_line(s: CardSentence, claims: dict[str, Claim]) -> bool:
    """A line every cited claim of which states a SHARE-PRICE / index performance move."""
    cited = [claims[c] for c in s.claim_ids if c in claims]
    return bool(cited) and all(is_market_reaction(c.quote) for c in cited)


def refile_price_moves(card: CardContent, claims: dict[str, Claim]) -> CardContent:
    """Counter-evidence lines that state only a price move become PRICE CONTEXT: a share-price
    move is not earnings evidence for or against a thesis (the same rule that keeps a price move
    out of the earnings transmission). J.P. Morgan acceptance, 2026-10-12: "the Magnificent 7 have
    risen roughly 12% vs the index's ~15%" sat under counter-evidence to EARNINGS broadening."""
    w = card.s07_what_could_go_wrong
    moved = tuple(s for s in w.counter_evidence if is_price_line(s, claims))
    if not moved:
        return card
    return card.model_copy(update={"s07_what_could_go_wrong": w.model_copy(update={
        "counter_evidence": tuple(s for s in w.counter_evidence if s not in moved),
        "price_context": w.price_context + moved})})


def _labelled_item(it: ChangeItem, claims: dict[str, Claim]) -> ChangeItem:
    if _FIGURES in it.text:
        return it
    tags = figure_labels(claims[c] for c in it.claim_ids if c in claims)
    if not tags:
        return it
    return it.model_copy(update={"text": f"{it.text} {LABEL_OPEN}cited figures: {tags}"
                                         f"{LABEL_CLOSE}"})


def _dedupe(sents: Iterable[CardSentence]) -> tuple[CardSentence, ...]:
    seen: set[str] = set()
    out: list[CardSentence] = []
    for s in sents:
        k = s.text.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(s)
    return tuple(out)


@dataclass
class CardInputs:
    thesis: Thesis
    version: int
    as_of: date
    hyp: VerifiedHypothesis | None  # the article view contributing THIS version (None: no new view)
    article: Article | None  # the article contributing this version
    prev: CardContent | None
    claims: dict[str, Claim]
    links: list[ThesisClaimLink]
    affected: AffectedView
    change_items: list[ChangeItem]
    vs_prior: str
    novelty: str
    priority: ResearchPriority
    evidence_direction: EvidenceDirection
    sources: list[SourceRef]
    market_risks: list[CardSentence]
    relation_notes: list[CardSentence]
    counter_claims: list[Claim]
    last_material_update: date


def evidence_rows(claims: dict[str, Claim],
                  links: list[ThesisClaimLink]) -> tuple[EvidenceRow, ...]:
    """One row per piece of evidence: claims repeating the SAME origin + measure + value
    collapse into the first, which lists the repeats as `also_reported_in` (attribution, not new
    evidence); a sentence read again from another version of the same article collapses into
    the row its first reading made."""
    roles = (LinkRole.DISLOCATION, LinkRole.SUPPORTS, LinkRole.CATALYST)
    rows: dict[str, EvidenceRow] = {}
    order = sorted((lk for lk in links if lk.role in roles and lk.claim_id in claims),
                   key=lambda lk: (roles.index(lk.role), lk.first_version, lk.claim_id))
    for lk in order:
        c = claims[lk.claim_id]
        if not c.span_verified:
            continue
        if c.fingerprint in rows:
            r = rows[c.fingerprint]
            if c.article_id != r.article_id and c.article_id not in r.also_reported_in:
                rows[c.fingerprint] = r.model_copy(
                    update={"also_reported_in": (*r.also_reported_in, c.article_id)})
            continue
        if any(same_sentence_reread(claims[r.claim_id], c) for r in rows.values()):
            continue
        label =" — ".join(x for x in (c.scope, c.metric) if x) or c.statement
        rows[c.fingerprint] = EvidenceRow(
            claim_id=c.claim_id, label=label, value_text=c.value_text, value=c.value,
            unit=c.unit, period=c.period, measured_as_of=c.measured_as_of, epistemic=c.epistemic,
            approximate=c.approximate, chart_derived=c.chart_derived, comparator=c.comparator,
            qualifiers=c.qualifiers, origin=origin_label(c.attributed_source_text),
            article_id=c.article_id,
            block_id=c.block_id, quote=c.quote, role=lk.role, change_class=lk.change_class)
    metric_first = sorted(rows.values(), key=lambda r: (r.value_text is None,
                                                        roles.index(r.role)))
    return tuple(metric_first)


def compose_card(ci: CardInputs) -> CardContent:
    h, prev, claims = ci.hyp, ci.prev, ci.claims
    pr = ci.priority
    regime = ci.thesis.kind is ThesisKind.MARKET_REGIME

    # header ------------------------------------------------------------------------------------
    horizon = (HORIZON_LABEL[h.raw.horizon] if h else prev.header.horizon if prev else
               HORIZON_LABEL[Horizon.UNCLEAR])
    dates = [s.published_at.date() for s in ci.sources if s.published_at]
    header = CardHeader(
        thesis_id=ci.thesis.thesis_id, title=ci.thesis.title, sector=ci.thesis.sector,
        region=ci.thesis.region, research_action=pr.research_action,
        evidence_direction=ci.evidence_direction, horizon=horizon,
        last_material_update=ci.last_material_update, status=ci.thesis.status,
        ancestry=ci.thesis.ancestry, kind=ci.thesis.kind,
        first_detected=ci.thesis.created_at.date(),
        first_ingested_at=ci.thesis.created_at, analysis_as_of=ci.as_of,
        latest_article_date=max(dates) if dates else None)

    # 01 bottom line ----------------------------------------------------------------------------
    s01: list[CardSentence] = []
    if prev is not None:
        s01.extend(s for s in prev.s01_bottom_line[:2])
    if h is not None:
        fact = _cs(h.raw.bottom_line_fact.text,
                   provenance_of(h.raw.bottom_line_fact, h.bottom_fact_claims, claims),
                   h.bottom_fact_claims)
        implication = (_cs(h.raw.source_implication.text,
                           provenance_of(h.raw.source_implication, h.implication_claims, claims),
                           h.implication_claims)
                       if h.raw.source_implication and h.raw.source_implication.text.strip()
                       else None)
        if prev is None:
            s01.append(fact)
            if implication is not None:
                s01.append(implication)
            s01.append(_cs(h.raw.bottom_line_inference.text, Provenance.MODEL_INFERENCE))
        else:
            when = (ci.article.published_at.date().isoformat()
                    if ci.article and ci.article.published_at else "date UNKNOWN")
            pub = ci.article.publisher if ci.article else "source"
            # the update's date and publisher are composed METADATA, so they sit inside the
            # system-label brackets — never read as figures the sentence asserts
            s01.append(_cs(f"{LABEL_OPEN}update {when} · {pub}{LABEL_CLOSE} {fact.text}",
                           fact.provenance, fact.claim_ids))

    # 02 what changed ---------------------------------------------------------------------------
    s02 = WhatChanged(items=tuple(_labelled_item(it, claims) for it in ci.change_items),
                      vs_prior=ci.vs_prior, novelty=ci.novelty)

    # 03 transmission ---------------------------------------------------------------------------
    steps: dict[str, TransmissionStep] = {s.step: s for s in (prev.s03_transmission if prev else ())
                                          if s.provenance is not Provenance.UNKNOWN}
    if h is not None:
        for st in h.steps:
            prov = _src(st.claim_ids, claims) if st.source_stated and st.claim_ids \
                else Provenance.MODEL_INFERENCE
            text = st.text
            if st.reclassified_from:
                text = (f"{LABEL_OPEN}re-filed from {st.reclassified_from}: a price or valuation "
                        f"move is not an earnings step{LABEL_CLOSE} {text}")
            new = TransmissionStep(step=st.step, text=text, provenance=prov,
                                   claim_ids=tuple(st.claim_ids))
            old = steps.get(st.step)
            if old is None or (old.provenance is Provenance.MODEL_INFERENCE
                               and prov in SOURCE_LABELS):
                steps[st.step] = new
    if "listed_earnings" not in steps:
        steps["listed_earnings"] = TransmissionStep(
            step="listed_earnings", text=_REGIME_EARNINGS if regime else _EARNINGS_UNKNOWN,
            provenance=Provenance.UNKNOWN)
    s03 = tuple(sorted((st.model_copy(update={"text": labelled(
        CardSentence(text=st.text, provenance=st.provenance, claim_ids=st.claim_ids),
        claims).text}) for st in steps.values()),
        key=lambda s: STEP_ORDER.index(s.step) if s.step in STEP_ORDER else 99))

    # 04 evidence -------------------------------------------------------------------------------
    s04 = evidence_rows(claims, ci.links)

    # 06 why now --------------------------------------------------------------------------------
    near: list[CardSentence] = list(prev.s06_why_now.near_term) if prev else []
    structural: list[CardSentence] = list(prev.s06_why_now.structural) if prev else []
    window = prev.s06_why_now.catalyst_window if prev else _NO_CATALYST
    if h is not None:
        if h.raw.near_term_view:
            ids = [h.claim_map[c] for c in h.raw.near_term_view.claim_ids if c in h.claim_map]
            near.insert(0, _cs(h.raw.near_term_view.text,
                               provenance_of(h.raw.near_term_view, ids, claims), ids))
        for cid in h.dislocation:
            c = claims.get(cid)
            if c is not None:
                near.append(_cs(f"Dislocation evidence: {c.statement}", _src([cid], claims),
                                [cid]))
        if h.raw.structural_view:
            ids = [h.claim_map[c] for c in h.raw.structural_view.claim_ids if c in h.claim_map]
            structural.insert(0, _cs(h.raw.structural_view.text,
                                     provenance_of(h.raw.structural_view, ids, claims), ids))
        if h.raw.catalyst.window_text:
            dated = [c for c in h.catalyst if c in claims and claims[c].kind is ClaimKind.EVENT
                     and (claims[c].period or claims[c].measured_as_of)]
            prov = (_src(dated, claims) if h.raw.catalyst.provenance in ("source_stated",
                                                                         "article_fact")
                    and dated else Provenance.MODEL_INFERENCE)
            window = f"{h.raw.catalyst.window_text} [{prov.value}]" + (
                "" if dated else " — the source names no dated catalyst or earnings window")
    s06 = WhyNow(near_term=_dedupe(labelled(s, claims) for s in near),
                 structural=_dedupe(labelled(s, claims) for s in structural),
                 catalyst_window=window, valuation_status=pr.valuation_status)

    # 07 what could go wrong --------------------------------------------------------------------
    pw = prev.s07_what_could_go_wrong if prev else None
    counter = list(pw.counter_evidence) if pw else []
    alts = list(pw.alternative_mechanisms) if pw else []
    obs = list(pw.disconfirming_observables) if pw else []
    unk = list(pw.unknowns) if pw else []
    for c in ci.counter_claims:
        counter.append(_cs(c.statement, _src([c.claim_id], claims), [c.claim_id]))
    if h is not None:
        for t in h.raw.opposing_explanations:
            ids = [h.claim_map[x] for x in t.claim_ids if x in h.claim_map]
            alts.append(_cs(t.text, provenance_of(t, ids, claims), ids))
        obs.extend(_cs(o, Provenance.MODEL_INFERENCE) for o in h.raw.disconfirming_observables)
        unk.extend(_cs(u, Provenance.MODEL_INFERENCE) for u in h.raw.unknowns)
        if h.raw.premise_condition:
            unk.insert(0, _cs(f"Premise the source makes it conditional on: "
                              f"{h.raw.premise_condition}", Provenance.MODEL_INFERENCE))
    alts.extend(ci.relation_notes)
    risks = list(pw.market_risks) if pw else []
    risks.extend(ci.market_risks)
    s07 = WhatCouldGoWrong(counter_evidence=_dedupe(labelled(s, claims) for s in counter),
                           alternative_mechanisms=_dedupe(alts),
                           disconfirming_observables=_dedupe(obs), unknowns=_dedupe(unk),
                           market_risks=_dedupe(risks),
                           price_context=pw.price_context if pw else ())

    # 08 decision -------------------------------------------------------------------------------
    pd = prev.s08_decision if prev else None
    if h is not None:
        nxt = _cs(h.raw.next_research_step, Provenance.MODEL_INFERENCE)
        raise_if = [_cs(x, Provenance.MODEL_INFERENCE) for x in h.raw.raise_priority_if]
        lower_if = [_cs(x, Provenance.MODEL_INFERENCE) for x in h.raw.lower_priority_if]
    else:
        assert pd is not None
        nxt = pd.next_step
        raise_if, lower_if = list(pd.raise_priority_if), list(pd.lower_priority_if)
    if pd is not None and h is not None:
        raise_if = list(pd.raise_priority_if) + raise_if
        lower_if = list(pd.lower_priority_if) + lower_if
    s08 = Decision(research_action=pr.research_action, next_step=nxt,
                   raise_priority_if=_dedupe(raise_if), lower_priority_if=_dedupe(lower_if),
                   investment_readiness=pr.investment_readiness,
                   readiness_note=pr.valuation_status, rule_trace=pr.rules_fired)

    return capped_conditionals(refile_price_moves(CardContent(
        header=header, s01_bottom_line=_dedupe(labelled(s, claims) for s in s01),
        s02_what_changed=s02, s03_transmission=s03, s04_key_evidence=s04,
        s05_affected=ci.affected, s06_why_now=s06, s07_what_could_go_wrong=s07,
        s08_decision=s08, s09_sources=tuple(ci.sources)), claims))


def with_citations(card: CardContent, anchors: dict[str, list[str]],
                   claims: dict[str, Claim]) -> CardContent:
    """RE-ANCHOR before withholding: add verified claim ids to the source-labelled sentences
    `anchors` names (sentence id -> extra claim ids) and re-derive their label (the weakest of
    ALL cited claims) and figure labels. A MODEL INFERENCE line is never touched — re-anchoring
    can never turn an inference into the source's word."""

    def fix_sent(s: CardSentence, sid: str) -> CardSentence:
        extra = anchors.get(sid)
        if not extra or s.provenance not in SOURCE_LABELS:
            return s
        ids = tuple(dict.fromkeys((*s.claim_ids, *extra)))
        base = _FIG_SUFFIX.sub("", s.text)
        return labelled(CardSentence(text=base, provenance=_src(ids, claims), claim_ids=ids),
                        claims)

    s01 = tuple(fix_sent(s, f"s01.{i}") for i, s in enumerate(card.s01_bottom_line))
    items = []
    for i, it in enumerate(card.s02_what_changed.items):
        extra = anchors.get(f"s02.{i}")
        if extra and it.provenance in SOURCE_LABELS:
            ids = tuple(dict.fromkeys((*it.claim_ids, *extra)))
            it = _labelled_item(it.model_copy(update={
                "text": _FIG_SUFFIX.sub("", it.text), "claim_ids": ids,
                "provenance": _src(ids, claims)}), claims)
        items.append(it)
    s03 = []
    for i, st in enumerate(card.s03_transmission):
        s = fix_sent(CardSentence(text=st.text, provenance=st.provenance,
                                  claim_ids=st.claim_ids), f"s03.{i}")
        s03.append(st.model_copy(update={"text": s.text, "provenance": s.provenance,
                                         "claim_ids": s.claim_ids}))
    wn = card.s06_why_now
    n_near = len(wn.near_term)
    w = card.s07_what_could_go_wrong
    n0, n1 = len(w.counter_evidence), len(w.alternative_mechanisms)
    n2 = len(w.market_risks)
    d = card.s08_decision
    return capped_conditionals(card.model_copy(update={  # a re-derived label is capped again
        "s01_bottom_line": s01,
        "s02_what_changed": card.s02_what_changed.model_copy(update={"items": tuple(items)}),
        "s03_transmission": tuple(s03),
        "s06_why_now": wn.model_copy(update={
            "near_term": tuple(fix_sent(s, f"s06.{i}") for i, s in enumerate(wn.near_term)),
            "structural": tuple(fix_sent(s, f"s06.{n_near + i}")
                                for i, s in enumerate(wn.structural))}),
        "s07_what_could_go_wrong": w.model_copy(update={
            "counter_evidence": tuple(fix_sent(s, f"s07.{i}")
                                      for i, s in enumerate(w.counter_evidence)),
            "alternative_mechanisms": tuple(fix_sent(s, f"s07.{n0 + i}")
                                            for i, s in enumerate(w.alternative_mechanisms)),
            "market_risks": tuple(fix_sent(s, f"s07.{n0 + n1 + i}")
                                  for i, s in enumerate(w.market_risks)),
            "price_context": tuple(fix_sent(s, f"s07.{n0 + n1 + n2 + i}")
                                   for i, s in enumerate(w.price_context))}),
        "s08_decision": d.model_copy(update={"next_step": fix_sent(d.next_step, "s08.next")}),
    }))


_PERCENT_UNITS = frozenset({"%", "percent", "per cent", "pct"})
#: a share written as a fraction word carries its percent: "roughly half", "four-fifths"
_SHARE_WORDS = r"half|halves|thirds?|quarters?|fifths?|tenths?"
#: the written forms of one unit — a value written in any of them already carries it, so
#: "$10 billion" with unit "$bn" never prints "$10 billion bn" (published 2026-10-14, U52)
_UNIT_FORMS = (
    ("tn", "trn", "t", "trillion"), ("bn", "b", "billion"), ("m", "mn", "mm", "million"),
    ("k", "thousand"),
    ("x", "times", "fold", "twice", "double", "doubled", "doubling", "triple", "tripled",
     "tripling"),
    ("ppt", "pp", "percentage point"), ("bp", "bps", "basis point"),
)


def _forms(token: str) -> tuple[str, ...]:
    """`token` as a value may write it: its other written forms, singular or plural ("month" for
    "months")."""
    t = token.lower()
    group = next((g for g in _UNIT_FORMS if t in g or t.rstrip("s") in g), (t,))
    return tuple({y for x in group for y in (x, x + "s")} | {t, t.rstrip("s") or t})


def unit_shown(value_text: str | None, unit: str | None) -> str:
    """The unit to print after a figure — without what the written value already carries, so
    "~43%" with unit "%" prints "~43%", never "~43% %", and "15–20%" with unit "% QoQ" prints
    "15–20% QoQ" (both observed 2026-10-10). A unit written another way is carried too ("$10
    billion" with "$bn", "8.5 month" with "months", "more than four times" with "x"), and a
    value written in words keeps a unit it does not carry ("more than 60" countries). ONE helper
    for the card and the desk (U52). Display only: the card keeps value and unit as separate
    fields."""
    u = (unit or "").strip()
    v = value_text or ""
    # a currency the written value already carries: "$413" with unit "$/year" prints "$413 per
    # year", never "$413 $/year" (2026-10-14)
    sym = next((x for x in ("$", "€", "£", "¥") if u.startswith(x) and x in v), "")
    if sym:
        u = u[len(sym):].strip()
        u = f"per {u[1:].strip()}" if u.startswith("/") else u

    def carried(token: str) -> bool:
        if token.lower() in _PERCENT_UNITS:
            return re.search(rf"%|percent|per cent|\b(?:{_SHARE_WORDS})\b", v, re.I) is not None
        return any(re.search(rf"(?<![A-Za-z]){re.escape(f)}(?![A-Za-z])", v, re.I)
                   for f in _forms(token))

    if not u or carried(u):
        return ""
    head, _, rest = u.partition(" ")
    return rest.strip() if rest and carried(head) else u


def value_with_unit(value_text: str | None, unit: str | None) -> str:
    return " ".join(x for x in (value_text or "", unit_shown(value_text, unit)) if x)


def card_sha(card: CardContent) -> str:
    import hashlib
    return hashlib.sha256(card.model_dump_json().encode()).hexdigest()


# --- field-by-field diff ---------------------------------------------------------------------

def diff_cards(old: CardContent, new: CardContent, classes: dict[str, ChangeClass]) -> list[
        tuple[str, ChangeClass, str | None, str | None, tuple[str, ...]]]:
    """(field_id, change class, old summary, new summary, claim ids) for every field that moved."""
    out: list[tuple[str, ChangeClass, str | None, str | None, tuple[str, ...]]] = []

    def cls_for(ids: Iterable[str]) -> ChangeClass:
        found = [classes[i] for i in ids if i in classes]
        for c in (ChangeClass.CONTRADICTORY, ChangeClass.CORRECTION, ChangeClass.TIMING_CHANGE,
                  ChangeClass.INDEPENDENT_CONFIRMATION, ChangeClass.NEW, ChangeClass.REPEATED):
            if c in found:
                return c
        return ChangeClass.NO_MATERIAL_CHANGE

    o_rows = {r.claim_id: r for r in old.s04_key_evidence}
    n_rows = {r.claim_id: r for r in new.s04_key_evidence}
    added = [i for i in n_rows if i not in o_rows]
    for i in added:
        r = n_rows[i]
        out.append(("s04_key_evidence", cls_for([i]), None,
                    f"{r.label}: {value_with_unit(r.value_text, r.unit)}".strip(), (i,)))
    o_cnt = {s.text for s in old.s07_what_could_go_wrong.counter_evidence}
    for s in new.s07_what_could_go_wrong.counter_evidence:
        if s.text not in o_cnt:
            out.append(("s07_what_could_go_wrong.counter_evidence", cls_for(s.claim_ids), None,
                        s.text, s.claim_ids))
    if old.s06_why_now.catalyst_window != new.s06_why_now.catalyst_window:
        ids = tuple(i for s in new.s06_why_now.near_term for i in s.claim_ids)
        out.append(("s06_why_now.catalyst_window",
                    ChangeClass.TIMING_CHANGE if any(classes.get(i) is ChangeClass.TIMING_CHANGE
                                                     for i in classes) else cls_for(ids),
                    old.s06_why_now.catalyst_window, new.s06_why_now.catalyst_window, ids))
    if old.header.research_action != new.header.research_action:
        out.append(("header.research_action", ChangeClass.NO_MATERIAL_CHANGE
                    if not classes else cls_for(classes), old.header.research_action.value,
                    new.header.research_action.value, ()))
    o_co = {entity_key(c) for c in old.s05_affected.companies}
    for c in new.s05_affected.companies:
        if entity_key(c) not in o_co:
            out.append(("s05_affected.companies", ChangeClass.NEW, None,
                        f"{c.name_as_written} ({c.role.value})", ()))
    o_sec = {norm_name(x.name) for x in old.s05_affected.sector_exposures}
    for se in new.s05_affected.sector_exposures:
        if norm_name(se.name) not in o_sec:
            out.append(("s05_affected.sector_exposures", ChangeClass.NEW, None,
                        f"{se.name} ({se.direction.value})", se.claim_ids))
    if [s.text for s in old.s01_bottom_line] != [s.text for s in new.s01_bottom_line]:
        out.append(("s01_bottom_line", cls_for(i for s in new.s01_bottom_line
                                                for i in s.claim_ids),
                    old.s01_bottom_line[-1].text if old.s01_bottom_line else None,
                    new.s01_bottom_line[-1].text if new.s01_bottom_line else None,
                    tuple(i for s in new.s01_bottom_line for i in s.claim_ids)))
    return out


# --- rendering -------------------------------------------------------------------------------

#: THE THEME-INTELLIGENCE THEME — one palette (light and dark), one type, one nav bar and one audit
#: switch for every page the package writes: the research desk, the Living Thesis Card and the
#: weekly report (option A, 2026-10-13 — before it the desk had its own palette and nav, showed
#: Research Now in green where the card showed it in red, and had no dark mode).
THEME_CSS = """
:root{--bg:#f5f5f2;--panel:#fff;--ink:#16181d;--ink2:#3b4049;--muted:#676d78;--line:#e0e2e6;
--soft:#f0f1f3;--accent:#1f3a5f;--accent-bg:#eef2f7;--now:#8c1d18;--now-bg:#f8e7e5;
--watch:#7a5200;--watch-bg:#f6eedc;--skip:#555b65;--skip-bg:#eceef1;--warn:#9a3412;
--warn-bg:#fff3ea;--ok:#1f6f43;--ok-bg:#e6f2eb;--bad:#9b1c1c;--bad-bg:#fbe9e7;--info:#0f5f6e;
--info-bg:#e3f1f3;--obs:#1f6f43;--fc:#0f5f6e;--op:#6b3fa0;--inf:#8a5a00;--ext:#1d4f91;
--unk:#676d78;--block:#9b1c1c}
@media (prefers-color-scheme: dark){:root{--bg:#111316;--panel:#181b1f;--ink:#eceef1;
--ink2:#c9cdd4;--muted:#9aa1ab;--line:#2b2f35;--soft:#20242a;--accent:#9cc2f5;
--accent-bg:#1a2433;--now:#ffb4ab;--now-bg:#3a1916;--watch:#f0c36b;--watch-bg:#33280f;
--skip:#c9cdd4;--skip-bg:#24282e;--warn:#fdba74;--warn-bg:#2c1c10;--ok:#7fd4a4;--ok-bg:#132621;
--bad:#ffb4ab;--bad-bg:#3a1916;--info:#8fd6e0;--info-bg:#10272b;--obs:#7fd4a4;--fc:#8fd6e0;
--op:#c9a8f0;--inf:#f0c36b;--ext:#9cc2f5;--unk:#9aa1ab;--block:#ffb4ab}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scroll-padding-top:60px}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,-apple-system,
BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;font-variant-numeric:tabular-nums}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.topnav{position:sticky;top:0;z-index:5;background:var(--panel);border-bottom:1px solid var(--line)}
.topnav .in{max-width:1120px;margin:0 auto;padding:0 16px;display:flex;align-items:center;
gap:20px;min-height:50px}
.brand{font-weight:700;white-space:nowrap;color:var(--ink)}.brand small{font-weight:500;
color:var(--muted);margin-left:6px}
.links{display:flex;gap:18px;overflow-x:auto;white-space:nowrap;flex:1;min-width:0;
scrollbar-width:none}.links::-webkit-scrollbar{display:none}
.links a{color:var(--ink2);font-size:14px;padding:14px 0;border-bottom:2px solid transparent}
.links a:hover{color:var(--ink);text-decoration:none;border-bottom-color:var(--line)}
.links a.on{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}
.subnav{max-width:1120px;margin:0 auto;padding:10px 16px 0;font-size:13px;color:var(--muted)}
.subnav a{margin:0 4px}
.auditbar{font-size:13px;color:var(--muted);white-space:nowrap;cursor:pointer;
border:1px solid var(--line);border-radius:6px;padding:4px 9px}
#audit:checked~.topnav .auditbar{background:var(--accent-bg);color:var(--accent)}
.wrap{max-width:1120px;margin:0 auto;padding:28px 16px 64px;overflow-wrap:break-word}
.wrap.narrow{max-width:940px}
.pill{display:inline-block;font-size:12px;font-weight:650;letter-spacing:.02em;padding:3px 10px;
border-radius:999px;white-space:nowrap;vertical-align:1px}
.pill.now{background:var(--now-bg);color:var(--now)}.pill.watch{background:var(--watch-bg);
color:var(--watch)}.pill.skip,.pill.dir{background:var(--skip-bg);color:var(--skip)}
.pill.kind{background:var(--accent-bg);color:var(--accent)}
.aud{display:none}#audit:checked~.wrap .aud,#audit:checked~.topnav .aud{display:revert}
#audit:checked~.wrap .nonaud{display:none}
@media (max-width:720px){.topnav .in{gap:0 12px;flex-wrap:wrap;padding-top:8px}
.brand small{display:none}.auditbar{margin-left:auto}
.links{order:3;flex-basis:100%;flex-wrap:wrap;gap:0 16px;white-space:normal;overflow:visible}
.links a{padding:6px 0 8px}.wrap{padding:18px 12px 48px}}
@media print{.topnav,.subnav{display:none}body{background:#fff}.aud{display:revert!important}
.nonaud{display:none!important}}
"""
#: the research desk's screens — the ONE nav bar of every theme-intelligence page
DESK_NAV = (("This week", "index.html"), ("Themes", "themes.html"), ("Articles", "articles.html"),
            ("Review", "review.html"), ("Uploads", "uploads.html"), ("Sources", "sources.html"))
#: every page the package writes is internal research, never for search engines
ROBOTS = '<meta name="robots" content="noindex, nofollow">'

_CSS = THEME_CSS + """
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
color:var(--muted)}
h1{font-size:27px;line-height:1.22;margin:6px 0 8px;font-weight:680;letter-spacing:-.01em}
h2{font-size:19px;margin:36px 0 12px;font-weight:660;letter-spacing:-.005em}
h3{font-size:16px;margin:0 0 6px;font-weight:640;line-height:1.3}
.tag{display:inline-block;font-size:12px;color:var(--ink2);border:1px solid var(--line);
border-radius:999px;padding:1px 9px;white-space:nowrap}.tag.down{color:var(--now)}
.tag.up{color:var(--ok)}
.flag{display:inline-block;font-size:12px;font-weight:650;color:var(--warn);
background:var(--warn-bg);border-radius:6px;padding:3px 9px;white-space:nowrap}
.okflag{font-size:12px;color:var(--muted)}
.hdr .hline{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin:6px 0 4px}
.hdr .meta{color:var(--ink2);font-size:13.5px}
.dates{color:var(--muted);font-size:13px;margin-top:6px}.vline{margin-top:10px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:24px 26px;margin:0 0 18px}
.glance{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:22px 0 8px}
.glance .g{border:1px solid var(--line);border-radius:10px;padding:14px 16px;
background:var(--panel)}
.glance .g.wide{grid-column:1/-1}
details.glancefold{margin:18px 0 6px}details.glancefold>summary{cursor:pointer;font-size:13px;
color:var(--muted)}details.glancefold .glance{margin-top:10px}
.glance h3{font-size:12px;font-weight:650;letter-spacing:.07em;text-transform:uppercase;
color:var(--muted);margin:0 0 8px}
.glance ul{margin:0;padding-left:18px}.glance li{margin:3px 0}
.more{font-size:12.5px;display:inline-block;margin-top:6px}
.sec{border-top:1px solid var(--line);padding:16px 0 6px}
.sec h2,.sec summary{font-size:13px;font-weight:650;letter-spacing:.07em;text-transform:uppercase;
margin:0 0 10px;color:var(--ink2);cursor:pointer}
.sec summary small{font-weight:400;text-transform:none;letter-spacing:0;color:var(--muted)}
details.sec>summary{list-style:none}details.sec>summary::-webkit-details-marker{display:none}
details.sec>summary::before{content:"▸ ";color:var(--muted)}
details.sec[open]>summary::before{content:"▾ "}
.s{margin:4px 0 10px}.lab{display:inline-block;font-size:11.5px;font-weight:500;
letter-spacing:0;text-transform:lowercase;color:var(--muted);margin-right:6px;white-space:nowrap}
.sys{color:var(--muted);font-size:12.5px}
.lab::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;
margin-right:5px;background:var(--unk);vertical-align:1px}
.lab.obs::before,.lab.fact::before{background:var(--obs)}.lab.fc::before{background:var(--fc)}
.lab.op::before{background:var(--op)}.lab.inf::before{background:var(--inf)}
.lab.ext::before{background:var(--ext)}
.cc{font:600 11px/1.3 ui-monospace,Menlo,monospace;color:var(--muted)}
.step{font-size:12px;font-weight:600;color:var(--ink2);margin-right:6px}
.ref{font:11px ui-monospace,Menlo,monospace;color:var(--muted);text-decoration:none}
.hscroll{overflow-x:auto;max-width:100%;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:13px;margin:4px 0 12px}
th,td{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left;vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
font-weight:600}
.q{color:var(--muted);font-style:italic}.withheld{color:var(--block);font-weight:650}
.rw{color:var(--warn);background:var(--warn-bg);font-size:13px;margin:4px 0 0;padding:6px 9px;
border-radius:6px}.flagged{border-left:3px solid var(--warn);padding-left:10px}
.corr{color:var(--accent);font-size:12.5px;margin-top:3px}
.rv{color:var(--muted);font-size:12.5px;margin-top:3px}.rv details{display:inline}
.rv summary{display:inline;cursor:pointer;margin-left:6px;text-transform:none;
letter-spacing:0;font-weight:400;color:var(--accent)}
details.more{margin-top:10px;max-width:100%;min-width:0;overflow-x:auto}
details.more>summary{cursor:pointer;color:var(--accent);font-size:13px;text-transform:none;
letter-spacing:0}
.ref.nolink{color:var(--muted)}.hit{outline:2px solid var(--accent);outline-offset:3px}
tr.hit>td{background:var(--accent-bg)}
.note{color:var(--muted);font-size:13px}.sub{font-weight:650;font-size:12px;margin:14px 0 4px;
color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.foot{color:var(--muted);font-size:12px;margin-top:14px}
.statusnote{margin-top:10px;padding:7px 10px;border-radius:6px;background:var(--soft);
font-weight:600;font-size:13px}
.legend{font-size:12.5px;color:var(--muted);margin:14px 0 4px}
.legend summary{cursor:pointer}
@media (max-width:720px){.hscroll table{min-width:620px}
.glance{grid-template-columns:minmax(0,1fr)}h1{font-size:22px}
.card{padding:16px 14px;border-radius:10px}}
@media print{details>*{display:block!important}
details.sec>summary::before{content:""}body{background:#fff}.card{border:0;padding:0}
.aud{display:revert!important}.nonaud{display:none!important}.hscroll{overflow:visible}
.glance{grid-template-columns:repeat(2,minmax(0,1fr))}.g,.thesis{break-inside:avoid}}
"""

_BADGE = {Provenance.MEASURED_OBSERVATION: "obs", Provenance.FORECAST: "fc",
          Provenance.SOURCE_OPINION: "op", Provenance.MODEL_INFERENCE: "inf",
          Provenance.EXTERNALLY_VERIFIED: "ext", Provenance.UNKNOWN: "unk",
          Provenance.ARTICLE_FACT: "fact"}
_PILL = {"RESEARCH NOW": "now", "WATCH": "watch", "SKIP": "skip"}
_FOLDED = {"s03_transmission", "s04_key_evidence", "s05_affected", "s07_what_could_go_wrong",
           "s09_sources"}
#: change classes as a reader says them; `novelty_unverified` needs no per-line tag — section 02
#: says once that a new thesis is new TO THE REGISTRY, not necessarily new to the market. Evidence
#: reaching a thesis's own history is DIRECT (the same identity — node, mechanism, segment,
#: geography); adjacent support and related opposite reads stay in the registry links, never here.
_CHANGE_TAG = {ChangeClass.NEW: "Direct confirmation — new evidence",
               ChangeClass.INDEPENDENT_CONFIRMATION: "Direct confirmation — independent source",
               ChangeClass.REPEATED: "Repeated source — attribution only",
               ChangeClass.CONTRADICTORY: "Contradiction — evidence against this thesis",
               ChangeClass.CORRECTION: "Correction", ChangeClass.TIMING_CHANGE: "Timing change",
               ChangeClass.NO_MATERIAL_CHANGE: "No material change",
               ChangeClass.NOVELTY_UNVERIFIED: ""}
LEGEND = ("Labels: MEASURED OBSERVATION — a figure or dated event the source reports · FORECAST "
          "— a projection or estimate in the source · SOURCE OPINION — the publisher's "
          "interpretation or argument, not an established market fact · MODEL INFERENCE — this "
          "tool's reasoning · EXTERNALLY VERIFIED — checked against an independent primary "
          "source. A line citing several claims carries the weakest label among them.")
AUDIT_TOGGLE = '<input type="checkbox" id="audit" hidden>'


def e(x: object) -> str:
    """Escaped for HTML — ONCE: text a source page already entity-encoded ("America&#039;s",
    the pilot's Nomura title) is decoded first, so it never prints as "&#039;"."""
    return html.escape(html.unescape("" if x is None else str(x)))


def origin_label(attributed: str | None) -> str:
    """How a figure's upstream origin reads on a card: the data source the article names, the
    publisher's own analysis, or — when the article attributes nothing — said plainly."""
    if not attributed:
        return "not attributed by the source"
    if attributed.strip().lower() in ("publisher_own", "publisher own"):
        return "publisher's own analysis"
    return attributed


_ENTITY = re.compile(r"&(?:#\d+|#[xX][0-9a-fA-F]+|amp|lt|gt|quot|apos);")


def plain_entities(text: str) -> str:
    """Markdown as a reader sees it: a stored HTML entity a source page carried ("America&#039;s",
    the pilot's Nomura title) is decoded. Only well-formed references — "S&P" and "AT&T" are text.
    The JSON keeps the stored value."""
    return _ENTITY.sub(lambda m: html.unescape(m.group(0)), text)


def foot_html(note: str) -> str:
    """The page's generated line: WHEN and FROM WHAT in the default view; the engine versions and
    the run id it names in parentheses sit in the audit layer (shown in print)."""
    head, sep, tail = note.partition(" (")
    return (f'<div class="foot">{e(head)}'
            + (f'<span class="aud"> ({e(tail)}</span>' if sep else "") + "</div>")


#: an investment-readiness value as a reader says it (the stored enum stays in the JSON)
READINESS_WORD = {"NOT_ASSESSED": "Not assessed"}


def readiness_text(value: str, note: str) -> str:
    """`Readiness — note`, in words, without repeating a label the note already starts with."""
    word = READINESS_WORD.get(value, value)
    rest = note[len(value):].lstrip(" —") if note.startswith(value) else note
    return f"{word} — {rest}" if rest else word


def _once(label: str, note: str) -> str:
    """`LABEL — note`, without repeating a label the note already starts with."""
    return note if note.startswith(label) else f"{label} — {note}"


def first_detected_line(h: CardHeader) -> str:
    """Three dates, never conflated (review of PR #703, round 3): the publisher's (the latest
    contributing source), the moment this registry ACTUALLY first ingested the thesis (wall
    clock, UTC) and the analysis as-of. A historical replay sets the as-of BEFORE ingestion — a
    simulated date is never called a detection."""
    art = (h.latest_article_date.isoformat() if h.latest_article_date else "UNKNOWN")
    ing = (f"{h.first_ingested_at:%Y-%m-%d %H:%M} UTC" if h.first_ingested_at else
           f"{h.first_detected.isoformat()} (UTC date)" if h.first_detected else "UNKNOWN")
    replay = (h.analysis_as_of is not None and h.first_ingested_at is not None
              and h.analysis_as_of < h.first_ingested_at.date())
    return (f"Published {art} (latest source) · first ingested by this registry {ing} (new to "
            f"the registry, not necessarily to the market) · analysed as of "
            f"{h.analysis_as_of.isoformat() if h.analysis_as_of else 'UNKNOWN'}"
            + (" (a historical replay — a simulated date, not a detection)" if replay else "")
            + f" · last material update {h.last_material_update.isoformat()}")


@dataclass(frozen=True)
class CarriedFinding:
    """An open card-review finding of an earlier version, read onto a version written WITHOUT the
    card review (its run recorded REVIEW_NOT_RUN): the stored finding is never copied or edited —
    it is read from the run that made it (report.review_carry)."""
    code: str
    detail: str  # the stored finding's own words, whole
    said: str  # the part shown on the line
    blocked: bool  # the review withheld the line (REVIEW_UNSUPPORTED)
    origin_version: int  # the version whose review made it
    origin_as_of: date
    origin_text: str  # the line as it read when the review made it
    #: the line's words or cited evidence changed since that review, and no review has run on the
    #: new form: NOT RE-REVIEWED, never clean
    changed: bool


@dataclass(frozen=True)
class ReviewCarry:
    """The card-review status of one version: why its review did not run (None — it ran), the
    earlier open findings read onto its lines, and those whose line it removed."""
    not_run: str | None = None
    carried: dict[str, CarriedFinding] = field(default_factory=dict)
    removed: tuple[CarriedFinding, ...] = ()


#: why a card review did not run, in words (the stored REVIEW_NOT_RUN detail stays in the audit)
def review_not_run_words(detail: str) -> str:
    if "--no-review" in detail:
        return "the review was switched off for the run (--no-review)"
    if "budget" in detail:
        return "the run's review budget was exhausted"
    if "no LLM client" in detail or "no cached" in detail:
        return "no model client and no cached review were available"
    return "the card review did not run"


@dataclass
class RenderContext:
    history: list[ThesisVersion]
    attributions: list[tuple[str, str, str]]  # (article id, class, note) — non-material
    blocked: dict[str, str]  # sentence id -> reason
    articles: dict[str, Article]
    generated_note: str
    status_note: str | None = None  # the CURRENT registry status, when it moved after this version
    #: sentence id -> the card review's UNRESOLVED warning (it questioned the line, which stays
    #: printed): shown ON the line, and the line is never labelled a verified fact
    flagged: dict[str, str] = field(default_factory=dict)
    #: article id -> its retrieval as READ NOW, when a correction record changed what this
    #: version's source row stored (a preview recorded FULL)
    retrieval_now: dict[str, str] = field(default_factory=dict)
    #: sentence id -> the reason of an ANALYST CORRECTION of that line (shown on it)
    corrected: dict[str, str] = field(default_factory=dict)
    #: the version's stored research priority — its FACTORS give the plain "why this action"
    priority: ResearchPriority | None = None
    #: sentence id -> (why it is resolved, the earlier review's words): a review finding a LATER
    #: version resolved (report.line_findings decides) — kept on the line as history, never
    #: counted as an open finding
    resolved: dict[str, tuple[str, str]] = field(default_factory=dict)
    #: every claim the card cites, by id, so every evidence link has a target — section 04 lists
    #: the ones outside the key-evidence rows; a cited id with no record is never a link
    claims: dict[str, Claim] = field(default_factory=dict)
    #: claim id -> its role on this thesis (supports, contradicts, context …)
    roles: dict[str, str] = field(default_factory=dict)
    #: business groups the source names in the paragraphs holding this thesis's evidence
    groups: tuple[NamedGroup, ...] = ()
    #: paragraphs holding this thesis's evidence whose text is NOT HELD on this machine (an
    #: exported registry carries none): business groups there are "not checkable", never "none"
    groups_unread: int = 0
    #: the claim ids with an evidence row on the rendered card (set by `render_html`)
    targets: frozenset[str] = frozenset()
    #: the version's card-review status: not run, and the earlier findings read onto its lines
    carry: ReviewCarry = field(default_factory=ReviewCarry)
    #: the latest ENRICHMENT set of the thesis (enrich.py) — external hypotheses, stored apart
    #: from the version: shown labelled, never counted
    enrichment: EnrichmentSet | None = None


@dataclass(frozen=True)
class NamedGroup:
    """A BUSINESS GROUP the source names ("GPU and ASIC manufacturers", "suppliers"), as written,
    in a paragraph holding this thesis's verified evidence. Not a company and not an exposure: no
    ticker is looked up or implied, and the research action never reads it."""
    name: str
    article_id: str
    block_ids: tuple[str, ...]
    excerpt: str  # the words around its first mention, verbatim — a bare "suppliers" says whose
    claim_ids: tuple[str, ...]  # verified claims whose quote contains the name


#: a group noun, optionally led by ACRONYM qualifiers ("GPU and ASIC", "HBM", "AI") — an ordinary
#: word before the noun is left to the excerpt, so a verb is never read as part of a name
_ACR = r"[A-Z0-9][A-Z0-9/+-]*[A-Z0-9]"
_GROUP = re.compile(rf"(?:\b({_ACR}(?:\s+(?:and|&|or)\s+{_ACR})*)\s+)?"
                    r"\b((?i:suppliers|manufacturers|makers|vendors|producers|chipmakers|"
                    r"foundries|hyperscalers))\b")


def named_groups(claims: Iterable[Claim], blocks: dict[tuple[str, str], str]
                 ) -> tuple[NamedGroup, ...]:
    """Business groups named in the paragraphs (`blocks`: (article version, block id) -> text)
    that hold the given span-verified claims — deterministic and verbatim, first mention first."""
    cl = [c for c in claims if c.span_verified]
    seen: dict[str, NamedGroup] = {}
    for c in cl:
        text = blocks.get((c.article_version_id, c.block_id), "")
        for m in _GROUP.finditer(text):
            name = " ".join(x for x in (m.group(1), m.group(2)) if x)
            key = name.lower()
            if key in seen:
                g = seen[key]
                if c.block_id not in g.block_ids:
                    seen[key] = replace(g, block_ids=(*g.block_ids, c.block_id))
                continue
            a, b = max(0, m.start() - 45), min(len(text), m.end() + 35)
            a = text.rfind(" ", 0, a) + 1 if a else 0
            b = (text.find(" ", b) if text.find(" ", b) != -1 else len(text)) if b < len(text) \
                else len(text)
            excerpt = ("…" if a else "") + text[a:b].strip() + ("…" if b < len(text) else "")
            ids = tuple(x.claim_id for x in cl if name.lower() in x.quote.lower())
            seen[key] = NamedGroup(name=name, article_id=c.article_id, block_ids=(c.block_id,),
                                   excerpt=excerpt, claim_ids=ids)
    return tuple(seen.values())


def groups_unchecked_note(n: int) -> str:
    """Business groups where the evidence text is not held (an exported registry, the runner)."""
    return (f"Not checkable on this machine — the text of {n} paragraph(s) holding this thesis's "
            f"evidence is not held here (an exported registry carries no article text), so "
            f"business groups the source names there cannot be read.")


def cited_claim_ids(card: CardContent) -> list[str]:
    """Every claim id the card cites, in order of first appearance (lines, rows, exposures)."""
    out: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("claim_ids", "claim_id"):
                    for c in ([v] if isinstance(v, str) else v or []):
                        if c not in out:
                            out.append(c)
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(json.loads(card.model_dump_json()))
    return out


def shown_label(prov: Provenance, sid: str, rc: RenderContext) -> Provenance:
    """The label a line is printed with: a line the review questioned is at most SOURCE OPINION
    — a conditional opinion must never read as a verified measured observation."""
    return Provenance.SOURCE_OPINION if sid in rc.flagged and prov in _FACT_LABELS else prov


def carried_note(f: CarriedFinding) -> str:
    """Where a finding read onto an unreviewed version comes from, in words."""
    return (f"raised by the review of version {f.origin_version} ({f.origin_as_of.isoformat()})"
            + (f", when the line read “{clip(f.origin_text, 160)}”" if f.changed else "")
            + "; not re-reviewed since")


def _warn_label(sid: str, rc: RenderContext) -> str:
    f = rc.carry.carried.get(sid)
    return "NOT RE-REVIEWED" if f is not None and f.changed else "UNRESOLVED REVIEW"


def _warn_html(sid: str, rc: RenderContext) -> str:
    if sid not in rc.flagged:
        return ""
    f = rc.carry.carried.get(sid)
    return (f'<div class="rw">⚠ {_warn_label(sid, rc)} — {ids_to_audit(e(rc.flagged[sid]))}'
            + (f'<div class="note">{e(carried_note(f))}</div>' if f is not None else "")
            + "</div>")


def _warn_md(sid: str, rc: RenderContext) -> str:
    if sid not in rc.flagged:
        return ""
    f = rc.carry.carried.get(sid)
    return (f" ⚠ **{_warn_label(sid, rc)} — {rc.flagged[sid]}**"
            + (f" _({carried_note(f)})_" if f is not None else ""))


def review_status_html(rc: RenderContext) -> str:
    """A version written without the card review SAYS so — never read as a clean review — with
    the earlier findings on lines it removed (not re-reviewed, never resolved)."""
    c = rc.carry
    if c.not_run is None:
        return ""
    return (f'<div class="statusnote">Not reviewed — the card review did not run for this '
            f'version: {e(review_not_run_words(c.not_run))}. Earlier findings stay on their '
            f'lines until a review runs.<span class="aud"> ({e(c.not_run)})</span>'
            + (f'<details><summary class="note">{len(c.removed)} earlier finding(s) on lines '
               f'this version removed — not re-reviewed</summary>' + "".join(
                   f'<div class="s">“{e(clip(f.origin_text, 200))}” — '
                   f'{ids_to_audit(e(f.said))} <span class="note">({e(carried_note(f))})</span>'
                   f'</div>' for f in c.removed) + "</details>" if c.removed else "")
            + "</div>")


def _resolved_html(sid: str, rc: RenderContext) -> str:
    """A review finding a later version resolved: said as history, with the review's words."""
    if sid not in rc.resolved:
        return ""
    why, said = rc.resolved[sid]
    return (f'<div class="rv">✓ Resolved — {e(why)}<details><summary class="note">the earlier '
            f'review</summary>{ids_to_audit(e(said))}</details></div>')


def _resolved_md(sid: str, rc: RenderContext) -> str:
    return (f" ✓ _Resolved — {rc.resolved[sid][0]} (earlier review: {rc.resolved[sid][1]})_"
            if sid in rc.resolved else "")


def _refs(ids: Iterable[str], rc: RenderContext) -> str:
    """A line's citations (audit view): each links to its claim's evidence row on this card; an
    id with no row is printed as text, never as a link to a missing target."""
    ids = list(ids)
    if not ids:
        return ""
    return (' <span class="aud">' + " ".join(
        f'<a class="ref" href="#{e(c)}">{e(c)}</a>' if c in rc.targets else
        f'<span class="ref nolink" title="no evidence record held for this id">{e(c)}</span>'
        for c in ids) + "</span>")


#: A run of registry ids inside a line — a challenger thesis, an article ("TH-98FD8D046C,
#: A-46796449712e"). They belong in the audit view, not the first view (review P2.12): the line
#: reads "⟨competing hypothesis⟩" and the ids show behind the toggle and in print. Observed
#: 2026-10-10 on the first challenged cards.
_ID_ONE = (r"(?:TH-[0-9A-F]{6,}|A-[0-9a-f]{8,}|C-[0-9a-f]{5,}(?:\.{3}|…)?"
           r"|C-[0-9a-f]{3,4}(?:\.{3}|…))")  # a reviewer's shortened id: "C-1d67..."
#: a run in its OWN parentheses goes with them — "automatic (A-…)" never reads "automatic ()"
_RUN = r"(?:pool\s+)?" + _ID_ONE + r"(?:,\s*" + _ID_ONE + r")*"
_ID_RUN = re.compile(r"(\s*\(" + _RUN + r"\)|\s*" + _RUN + ")")


def ids_to_audit(escaped: str) -> str:
    """Escaped card text with every run of registry ids wrapped in an audit span."""
    return _ID_RUN.sub(lambda m: f'<span class="aud">{m.group(1)}</span>', escaped)


_SYS_LABEL = re.compile("(" + LABEL_OPEN + "[^" + LABEL_CLOSE + "]*" + LABEL_CLOSE + ")")


def quiet_labels(html_text: str) -> str:
    """A card line's SYSTEM labels ⟨…⟩ set quieter than the source's words they qualify — the
    words read first; the label is still on the line (its text unchanged)."""
    return _SYS_LABEL.sub(r'<span class="sys">\1</span>', html_text)


def _sent(s: CardSentence, sid: str, rc: RenderContext, *, anchor: bool = True,
          step: str = "") -> str:
    """One card line: its label, its text, its citations (audit view), and — ON the line — an
    unresolved review warning or an analyst correction. `anchor` gives the line its linkable id
    (the at-a-glance summary repeats lines without one)."""
    aid = f' id="{_anchor(sid)}"' if anchor and sid != "-" else ""
    stp = f'<span class="step">{e(step)}</span>' if step else ""
    if sid in rc.blocked:
        return (f'<div class="s flagged"{aid}>{stp}<span class="withheld">WITHHELD — failed '
                f'source verification</span><span class="aud"> {e(rc.blocked[sid])}</span>'
                f'<details><summary class="note">audit text</summary><span class="q">'
                f'{e(_clean_display(s.text))}</span></details></div>')
    p = shown_label(s.provenance, sid, rc)
    cls = " flagged" if sid in rc.flagged else ""
    return (f'<div class="s{cls}"{aid}>{stp}<span class="lab {_BADGE[p]}">{e(p.value)}</span> '
            f'{quiet_labels(ids_to_audit(e(_clean_display(s.text))))}{_refs(s.claim_ids, rc)}'
            f'{_warn_html(sid, rc)}{_resolved_html(sid, rc)}{_corr_html(sid, rc)}</div>')


def _section(fid: str, title: str, body: str, *, print_mode: bool, summary: str = "") -> str:
    if fid in _FOLDED:
        op = " open" if print_mode else ""
        small = f" <small>— {e(summary)}</small>" if summary else ""
        return (f'<details class="sec" data-field="{fid}"{op}><summary id="sec-{fid}">'
                f'{e(title)}{small}</summary>{body}</details>')
    return (f'<section class="sec" data-field="{fid}"><h2 id="sec-{fid}">{e(title)}</h2>{body}'
            f'</section>')


def _listing_text(ls: Iterable[Listing]) -> str:
    return ", ".join(f"{x.ticker}" + (f" ({x.exchange})" if x.exchange else "") for x in ls)


def card_steps(card: CardContent) -> dict[str, str]:
    """The card's transmission lines: sentence id (s03.N) -> step name."""
    return {f"s03.{i}": st.step for i, st in enumerate(card.s03_transmission)}


def without_labels(text: str) -> str:
    """A card line without its system labels ⟨…⟩."""
    return re.sub(r"\s*⟨[^⟩]*⟩\s*", " ", text).strip()


#: how a company earns from a line of business, in words (enrich.BASIS_MODELS' keys)
BASIS_LABEL = {"subscription": "subscription", "usage_based": "usage-based",
               "transaction_fees": "transaction fees", "licences": "licences and maintenance",
               "product_sales": "product sales", "advertising": "advertising",
               "services": "services", "other": "other"}


def set_card(es: EnrichmentSet | None, history: Iterable[ThesisVersion]) -> CardContent | None:
    """The card version an enrichment set was proposed from — None when it is not held."""
    if es is None:
        return None
    return next((h.content for h in history if h.version == es.thesis_version), None)


def proposal_step(x: EnrichmentCandidate,
                  card: CardContent | None) -> tuple[str, Provenance | None]:
    """The step a proposal rests on: its text as recorded with the proposal, and its label —
    recorded when proposed, else read from the card version the set rests on (only when that
    card's step is the recorded one); None when neither holds it."""
    text = x.evidence.split(": ", 1)[1] if ": " in x.evidence else x.evidence
    if x.step_label is not None:
        return text, x.step_label
    m = re.fullmatch(r"s03\.(\d+)", x.step_id)
    if card is not None and m and int(m.group(1)) < len(card.s03_transmission):
        st = card.s03_transmission[int(m.group(1))]
        if without_labels(st.text) == text:
            return text, capped_label(st.provenance, st.text)
    return text, None


def proposal_reading(x: EnrichmentCandidate, steps: dict[str, str],
                     card: CardContent | None) -> tuple[bool, str]:
    """(conditional, the words) for a proposal's direction. A step that is a FACT (a measured
    or externally verified line): "could be hurt, through Pricing [s03.1]". Any other — the
    source's opinion, a forecast, our inference, or a label not recorded — makes the direction
    a CONDITION: "exposed — would be hurt IF this holds: “…” (source opinion) [s03.0]". Never a
    bare direction on a step that is not established (2026-10-15)."""
    text, label = proposal_step(x, card)
    side = {Direction.POSITIVE: "benefit", Direction.NEGATIVE: "be hurt"}.get(x.direction)
    if label in _FACT_LABELS and side:
        return False, (f"could {side}, through "
                       f"{STEP_LABEL.get(steps.get(x.step_id, ''), x.step_id)} [{x.step_id}]")
    support = label.value.lower() if label is not None else "its support was not recorded"
    return True, (f"exposed — would {side or 'be affected'} IF this holds: “{text}” ({support})"
                  f" [{x.step_id}]")


def basis_line(x: EnrichmentCandidate) -> str:
    """The basis the model stated and what the company's own annual report says of it — ""
    for a proposal made before the basis was asked for."""
    if not x.revenue_model:
        return ""
    stated = (f"basis (the model's): {BASIS_LABEL.get(x.revenue_model, x.revenue_model)}"
              + (f" — {x.revenue_line}" if x.revenue_line else ""))
    found = {"IN_FILING": f"{x.basis_source}: {x.basis_note}",
             "FILING_NAMES_OTHER": f"{x.basis_source}: {x.basis_note}",
             "NOT_DESCRIBED": f"{x.basis_source}: {x.basis_note}",
             }.get(x.basis_check, f"not checked — {x.basis_note}")
    return f"{stated} · {found}"


def enrichment_lines(es: EnrichmentSet | None, version: int, steps: dict[str, str],
                     card: CardContent | None = None) -> tuple[str, list[str]]:
    """(the set's provenance line, one line per proposed company) — the words every surface
    shows for an enrichment set. A ticker the SEC did not verify is said unverified; a direction
    resting on a step that is not a fact is said as the condition it is (`proposal_reading`).
    `card`: the card version the set was proposed from."""
    if es is None:
        return "", []
    head = (f"Proposed by the model on {es.as_of.isoformat()} from the thesis's own steps"
            + (f" (version {es.thesis_version}; the card is now version {version})"
               if es.thesis_version != version else "")
            + " — not named by the source, never counted toward the research action.")
    rows = []
    for x in es.candidates:
        _cond, how = proposal_reading(x, steps, card)
        basis = basis_line(x)
        rows.append(f"{x.name} ({enrichment_listing(x)}) — {how}: {x.rationale}"
                    + (f" · {basis}" if basis else ""))
    return head, rows


def enrichment_listing(x: EnrichmentCandidate) -> str:
    """A proposed company's listing as the SEC verified it — or why there is none."""
    if x.listings:
        return ", ".join(dict.fromkeys(v.ticker for v in x.listings))
    if x.ticker_hint and x.foreign_filer:
        return f"{x.ticker_hint} — the US line of a foreign filer, not checked point-in-time"
    if x.ticker_hint:
        return f"{x.ticker_hint} — not verified by the SEC"
    return "no verified US listing"


def enrichment_html(es: EnrichmentSet | None, card: CardContent, rc: RenderContext) -> str:
    if es is None:
        return ('<div class="note">Not proposed yet. Unnamed companies are never added to the '
                'source lists above.</div>')
    version = rc.history[-1].version if rc.history else es.thesis_version
    head, rows = enrichment_lines(es, version, card_steps(card), set_card(es, rc.history))
    # the filing's own sentence prints with its proposal: the card is the complete record
    quotes = [x.basis_quote for x in es.candidates]
    return (f'<div class="note">{e(head)}</div>'
            + ("".join(f'<div class="s"><span class="lab unk">our hypothesis</span> {e(r)}'
                       + "".join(f'<div class="note aud">the filing: “{e(q)}”</div>' for q in qs)
                       + "</div>" for r, qs in zip(rows, quotes, strict=True))
               or '<div class="note">None proposed.</div>')
            + (f'<div class="note aud">set aside: {e("; ".join(es.refused))}</div>'
               if es.refused else ""))


def distinct_sectors(av: AffectedView) -> list[SectorExposure]:
    """The sectors a card names, each ONCE. The extraction can name one sector twice in near
    words ("Diagnostics and care delivery, as well as the retirement and insurance industries" /
    "Diagnostics and care delivery, retirement and insurance industries", 2026-10-14): two
    names are one sector when one's content words are all the other's and at least two-thirds of
    them. The one with a stated direction is kept, else the first. Two that say OPPOSITE ways
    both stay: that is a contradiction to read, never one to hide. A single sector inside a list
    of several ("semiconductors" in "automation, robotics, semiconductors, …") stays apart.
    Display only: the card's JSON keeps every entry as extracted."""
    from vinci.theme_intelligence.verify import content_words

    ways = (Direction.POSITIVE, Direction.NEGATIVE)

    def same(x: SectorExposure, y: SectorExposure) -> bool:
        a, b = content_words(x.name), content_words(y.name)
        small, large = (a, b) if len(a) <= len(b) else (b, a)
        return (bool(small) and small <= large and 3 * len(small) >= 2 * len(large)
                and (x.direction == y.direction or ways.count(x.direction)
                     + ways.count(y.direction) < 2))

    out: list[SectorExposure] = []
    for x in av.sector_exposures:
        i = next((i for i, y in enumerate(out) if same(x, y)), None)
        if i is None:
            out.append(x)
        elif out[i].direction not in ways and x.direction in ways:
            out[i] = x  # the entry that says which way wins
    return out


def exposures_of(av: AffectedView) -> tuple[list[AffectedCompany], list[AffectedCompany]]:
    """The named companies that ARE exposures of the thesis — a role the source states as one
    (beneficiary, harmed, supplier, customer, disruptor …) — and those merely named on it (the
    publisher, a data source, context). The priority rules count only the first
    (`EXPOSURE_ROLES`); every surface lists them the same way. On 2026-10-14 Morgan Stanley, the
    PUBLISHER, sat in the Alzheimer thesis's list of exposures on the card and the desk."""
    return ([c for c in av.companies if c.role in EXPOSURE_ROLES],
            [c for c in av.companies if c.role not in EXPOSURE_ROLES])


#: roles that make a named FUND / INDEX / basket attached to the thesis its INVESTABLE FORM — the
#: ETF or index a sector view is expressed through (a sector opportunity needs no single ticker)
INSTRUMENT_ROLES = EXPOSURE_ROLES | {MentionRole.MARKET_INSTRUMENT, MentionRole.CITED_BASKET}


#: the card's two instrument headings (HTML and Markdown): attached to the thesis, or only named
INSTRUMENT_EXPOSURES = ("Instrument exposures of this thesis (ETFs, indices and baskets the "
                        "source attaches)")
NAMED_INSTRUMENTS = "Named instruments / indices — not attached to this thesis"


@dataclass(frozen=True)
class CountedExposures:
    """What the research-action rules count as the thesis's EXPOSURE — ONE definition, read by
    both engine paths and named on the card and the desk."""

    #: (name as written, tickers) — POINT-IN-TIME-VERIFIED common equity only
    listed: tuple[tuple[str, str], ...]
    #: ETFs, indices and cited baskets the source attaches to the thesis
    instruments: tuple[str, ...]
    #: sectors / themes the source names as exposed (verified spans)
    sectors: tuple[str, ...]
    #: named listed companies whose listing could NOT be verified as of the date — never counted
    unverified: tuple[str, ...]


def _with_tickers(c: AffectedCompany) -> str:
    """A named instrument with its listed ticker(s), unless its name already carries them
    ("iShares Expanded Tech-Software Sector ETF (IGV)")."""
    tickers = [x.ticker for x in c.listings if f"({x.ticker})" not in c.name_as_written]
    return c.name_as_written + (f" ({'/'.join(tickers)})" if tickers else "")


def exposure_instruments(av: AffectedView) -> list[AffectedCompany]:
    """The ETFs, indices and cited baskets the source ATTACHES to the thesis — its exposure, the
    form a sector view is expressed through. ONE definition for the count (`counted_exposures`)
    and every surface that lists who is exposed: on 2026-10-16 the count took the software ETF
    and index while the card and the desk still listed them as "named, not exposures"."""
    return [c for c in av.instruments if c.role in INSTRUMENT_ROLES] + [
        c for c in av.not_securities if c.role is MentionRole.CITED_BASKET]


def counted_exposures(av: AffectedView,
                      sectors: Iterable[SectorExposure] | None = None) -> CountedExposures:
    """The thesis's counted exposures (`sectors`: the verified sector exposures still standing,
    when the caller has re-checked them; else the card's). An ETF, index or cited basket the
    source attaches to the thesis COUNTS (2026-10-16: "software may be oversold" named the
    software ETF and index it would be expressed through, and read "no exposure")."""
    exp = [c for c in av.companies
           if c.resolution_status is ResolutionStatus.LISTED_EQUITY and c.role in EXPOSURE_ROLES]
    verified = [c for c in exp if any(x.pit_status is PitStatus.VERIFIED for x in c.listings)]
    inst = exposure_instruments(av)
    return CountedExposures(
        listed=tuple((c.name_as_written, "/".join(x.ticker for x in c.listings
                                                  if x.pit_status is PitStatus.VERIFIED))
                     for c in verified),
        instruments=tuple(_with_tickers(c) for c in inst),
        sectors=tuple(s.name for s in (av.sector_exposures if sectors is None else sectors)),
        unverified=tuple(c.name_as_written for c in exp if c not in verified))


def _company_rows(cs: Iterable[AffectedCompany], *, exposures: bool = False) -> str:
    rows = []
    for c in cs:
        lst = _listing_text(c.listings)
        if not lst:
            unver = [x for x in c.other_securities if x.pit_status is PitStatus.UNVERIFIED]
            lst = (f"not point-in-time verified ({_listing_text(unver)})" if unver else "—")
        cls = "; ".join(sorted({x.security_class for x in c.listings if x.security_class}))
        other = "; ".join(f"{x.ticker}: {x.pit_status.value}"
                          + (f" — {x.security_class}" if x.security_class else "")
                          for x in c.other_securities)
        reading = ""
        if exposures:
            label = c.exposure_provenance or Provenance.MODEL_INFERENCE
            # the badge class the card styles (`lab`), and a space: "b" had no rule, and the
            # label ran into the reading ("MODEL INFERENCEcited basket", 2026-10-16 preview)
            reading = (f"<td><span class=\"lab {_BADGE[label]}\">{e(label.value)}</span> "
                       f"{e(c.exposure_reading or c.role.value.replace('_', ' '))}</td>")
        rows.append(f"<tr><td>{e(c.name_as_written)}</td><td>{e(lst)}"
                    + (f"<div class=note>{e(cls)}</div>" if cls else "")
                    + (f'<div class="note aud">other lines: {e(other)}</div>' if other else "")
                    + f"</td><td>{e(c.role.value.replace('_', ' '))}<div class=note>"
                      f"{e(c.role_detail)}</div></td>{reading}<td>{e(c.direction.value)}</td>"
                      f"<td>{e(c.recommendation_status.value.replace('_', ' '))}</td></tr>")
    head = ("<tr><th>Named in source</th><th>Listing (point-in-time, SEC cover page)</th>"
            "<th>Role the source states</th>"
            + ("<th>This thesis's reading</th>" if exposures else "")
            + "<th>Direction</th><th>Recommendation</th></tr>")
    return ('<div class="hscroll"><table>' + head + "".join(rows) + "</table></div>") if rows \
        else '<div class="note">None named.</div>'


_ACTION_WORD = {"RESEARCH NOW": "Research Now", "WATCH": "Watch", "SKIP": "Skip"}
_LINE_NAMES = {"s01": "bottom line", "s02": "what changed", "s03": "economics",
               "s06": "why now", "s07": "what could go wrong", "s08": "next step"}


def _anchor(sid: str) -> str:
    """The id of a card line, linkable from the Review Required indicator and the review queue."""
    return "L-" + sid.replace(".", "-")


def _line_name(sid: str) -> str:
    return _LINE_NAMES.get(sid.partition(".")[0], sid)


def finding_names(sids: list[str]) -> list[str]:
    """Each line's section name — numbered where a section holds more than one, so every link
    says which line it opens ("what could go wrong 1", "what could go wrong 2")."""
    names = [_line_name(s) for s in sids]
    seen: dict[str, int] = {}
    out = []
    for n in names:
        seen[n] = seen.get(n, 0) + 1
        out.append(f"{n} {seen[n]}" if names.count(n) > 1 else n)
    return out


def _clean_display(text: str) -> str:
    """A stored line as a reader sees it: the "page None" a web article carried before 2026-10-12
    (it has no pages) is dropped. The stored text stays in the JSON."""
    return re.sub(r"page None(?:: | )?", "", re.sub(r",\s*page None\b", "", text))


def _corr_html(sid: str, rc: RenderContext) -> str:
    return (f'<div class="corr">Corrected by the analyst — {e(rc.corrected[sid])}</div>'
            if sid in rc.corrected else "")


def _source_name(card: CardContent, article_id: str) -> str:
    s = next((x for x in card.s09_sources if x.article_id == article_id), None)
    if s is None:
        return "source"
    return s.publisher + (f", {s.published_at.date().isoformat()}" if s.published_at else "")


def _para(block_id: str) -> str:
    """A block id as a reader says it: "b006" -> "6"."""
    return block_id[1:].lstrip("0") or "0" if re.fullmatch(r"b\d+", block_id) else block_id


def topnav(base: str, *, active: str = "", sections: Iterable[tuple[str, str]] = ()) -> str:
    """The product navigation — the research desk's six screens — on every page the package
    writes: the desk (`base` ""), a card or a reading page ("../") and the weekly report (""), with
    the audit switch (evidence ids, engine codes, decision traces). `sections`: the page's own
    in-page links, in a second row (the weekly report)."""
    on = ' class="on"'
    links = "".join(f'<a href="{base}{h}"{on if t == active else ""}>{e(t)}</a>'
                    for t, h in DESK_NAV)
    sub = ('<div class="subnav">On this page: ' + " · ".join(
        f'<a href="{h}">{e(t)}</a>' for t, h in sections) + "</div>") if sections else ""
    return ('<nav class="topnav" id="top"><div class="in"><a class="brand" href="'
            f'{base}index.html">Mosaic Theory<small>Research desk</small></a><div class="links">'
            + links + '</div><label for="audit" class="auditbar" title="Show evidence IDs, engine '
              'codes and the decision trace">Audit view</label></div></nav>' + sub)


def watch_of(pr: ResearchPriority, av: AffectedView) -> str:
    """A WATCH's "needs data" / "on hold" — from the stored reasons, or derived from the stored
    factor values for an older version (priority.watch_reasons_of). "" for any other action."""
    return watch_label(watch_reasons_of(pr, counted_exposures(av).unverified))


def _action_words(action: str, pr: ResearchPriority | None, av: AffectedView) -> str:
    """The action as the card names it, a WATCH with what it waits for ("Watch · needs data")."""
    q = watch_of(pr, av) if pr is not None and pr.research_action.value == action else ""
    return _ACTION_WORD.get(action, action) + (f" · {q}" if q else "")


def why_reasons(card: CardContent, pr: ResearchPriority | None,
                groups: Iterable[str] = (), *, groups_unchecked: bool = False) -> list[str]:
    """Why the research action is what it is, in plain words — from the STORED priority's factor
    VALUES and the card's own exposures, never from the rule trace's text (which stays in the
    audit view)."""
    if pr is None:
        return []
    f = {x.factor_id: x.value for x in pr.factors}
    a = pr.research_action.value
    # the exposure the stored RULE counted — the line never contradicts the action it explains;
    # a version that carries no readable count is read from its own card
    counted = counted_exposures(card.s05_affected)
    n = exposures_counted(pr)
    exposed = n > 0 if n is not None else bool(counted.listed or counted.instruments
                                               or counted.sectors)
    if a == "RESEARCH NOW":
        # the inflection route says WHY with its research question (composed by the priority
        # rules from the claim's structured fields)
        f12 = next((x.note for x in pr.factors if x.factor_id == "F12_fundamental_inflection"), "")
        q = re.search(r"research question: (.*?\?)", f12)
        if f.get("F7_dislocation_or_catalyst") != "present" and q:
            return ["Research Now — no recent mispricing or dated catalyst, but a credible "
                    f"near-term change in a fundamental: {q.group(1)} An investigation, not a "
                    "trade."]
        # a "dislocation" is a mispricing measured in the last quarter (priority.py)
        return ["Research Now — a mispricing measured in the last quarter or a dated catalyst, "
                "timing inside the next 2-4 quarters, an exposure the source names, a premise "
                "the source states, and the full text read. An investigation, not a trade."]
    if a == "SKIP":
        if f.get("F2_material_evidence") == "0":
            return ["Skip — no verified material evidence."]
        if f.get("F4_profit_transmission") == "absent":
            return ["Skip — no earnings mechanism (a price or valuation move is not one)."]
        return ["Skip — longer-term only: no dated window inside the next 2-4 quarters."]
    out: list[str] = []
    near = f.get("F5_near_term_relevance")
    if near == "runs_past":
        out.append("Timing — its dated figures run past the next four quarters; a full-year or "
                   "multi-quarter figure is not a 2-4-quarter window.")
    elif near and near != "yes":
        out.append("Timing — no dated window inside the next 2-4 quarters in the evidence.")
    names = list(dict.fromkeys(groups))
    unverified = any(r.code == "listing_unverified"
                     for r in watch_reasons_of(pr, counted.unverified))
    if not exposed and unverified:  # missing data, not a missing exposure
        out.append("Exposure — " + unverified_words(counted.unverified) + ".")
    elif not exposed:
        out.append("Exposure — no listed company or verified sector exposure; the source names "
                   f"business groups only ({'; '.join(names)}), not companies"
                   + ("; other evidence paragraphs are not checkable on this machine (their "
                      "article text is not held here)." if groups_unchecked else ".") if names
                   else "Exposure — no listed company or verified sector exposure; whether the "
                        "source names business groups is not checkable on this machine (the "
                        "article text is not held here)." if groups_unchecked else
                   "Exposure — the source names no company or sector as exposed.")
    if f.get("F7_dislocation_or_catalyst") != "present" and f.get(
            "F12_fundamental_inflection") != "qualifies":
        out.append({
            "not credible": "Catalyst — the near-term change is a forecast without a "
                            "corroborating measurement.",
            "incomplete": "Catalyst — the source states no fundamental step from the change to "
                          "profits."}.get(f.get("F12_fundamental_inflection", ""),
                                          "Catalyst — no verified dislocation, dated catalyst or "
                                          "near-term change in a fundamental."))
    if f.get("F9_premise_in_source", "asserted") != "asserted":
        out.append(f"Premise — {f['F9_premise_in_source'].replace('_', ' ')} in the source.")
    held = counter_verdict(pr)  # U53: the F8 VALUE the rule applied — never the trace's words
    if held == F8_CONTESTED:
        out.append("Counter-evidence — independent sources directly contradict it, at least as "
                   "many as support it.")
    elif held == F8_OUTWEIGHS:
        out.append("Counter-evidence — its own sources' counter-observations outweigh its "
                   "support.")
    if f.get("F11_retrieval", "FULL") != "FULL":
        out.append("Source — only part of the text was read.")
    if f.get("F10_verification_hold") == "HOLD":
        out.append("Verification — on hold until a failed check is resolved.")
    if f.get("F1_source_reliability") == "low":
        out.append("Reliability — a low-reliability source only.")
    return out or ["Watch — Research Now conditions not all met (see the decision trace)."]


def _glance(card: CardContent, rc: RenderContext) -> str:
    """AT A GLANCE — the seven questions an analyst asks of a thesis, answered from the card's own
    lines (labels kept), each linked to its full section."""
    act = _ACTION_WORD.get(card.header.research_action.value, card.header.research_action.value)

    def block(title: str, body: str, sec: str, *, wide: bool = False) -> str:
        return (f'<section class="g{" wide" if wide else ""}"><h3>{e(title)}</h3>{body}'
                f'<a class="more" href="#sec-{sec}">Details</a></section>')

    def line(s: CardSentence, sid: str) -> str:
        return _sent(s, sid, rc, anchor=False)

    s01 = card.s01_bottom_line
    thesis = line(s01[0], "s01.0") if s01 else '<div class="note">—</div>'
    wc = card.s02_what_changed.items
    changed = "".join(
        f'<li>{e(_clean_display(_plain_text(it.text)))}'
        + (f' <span class="note">({e(it.period)})</span>' if it.period else "") + "</li>"
        for i, it in enumerate(wc[:2]) if f"s02.{i}" not in rc.blocked)
    steps = [(i, st) for i, st in enumerate(card.s03_transmission) if st.step != "market_reaction"]
    impact = "".join(
        f'<li><span class="step">{e(STEP_LABEL.get(st.step, st.step))}</span>'
        f'{e(_clean_display(_plain_text(st.text)))}</li>'
        for i, st in steps[:3] if f"s03.{i}" not in rc.blocked)
    ev = [r for r in card.s04_key_evidence if r.value_text][:3] or list(card.s04_key_evidence[:3])
    evidence = "".join(
        f'<li><b>{e(r.value_text or "—")}</b> {e(unit_shown(r.value_text, r.unit))} — '
        f'{e(r.label)} <span class="note">({e(r.period or "—")}, {e(r.epistemic.value)}; '
        f'{e(_source_name(card, r.article_id))})</span></li>' for r in ev)
    why = "".join(f"<li>{e(x)}</li>"
                  for x in why_reasons(card, rc.priority, [g.name for g in rc.groups],
                              groups_unchecked=rc.groups_unread > 0))
    w = card.s07_what_could_go_wrong
    risks = ([line(s, f"s07.{i}") for i, s in enumerate(w.counter_evidence[:2])]
             + [f'<li>{e(_clean_display(s.text))}</li>' for s in w.disconfirming_observables[:2]])
    n0, n1 = len(w.counter_evidence), len(w.alternative_mechanisms)
    risks += [line(s, f"s07.{n0 + n1 + i}") for i, s in enumerate(w.market_risks[:1])]
    d = card.s08_decision
    nxt = (line(d.next_step, "s08.next")
           + (f'<div class="note">Would raise priority: {e(d.raise_priority_if[0].text)}</div>'
              if d.raise_priority_if else ""))
    return ('<div class="glance" aria-label="At a glance">'
            + block("The thesis", thesis, "s01_bottom_line", wide=True)
            + block("What changed", f"<ul>{changed}</ul>" if changed else
                    '<div class="note">Nothing new in this version.</div>', "s02_what_changed")
            + block("Effect on profits, margins or demand", f"<ul>{impact}</ul>" if impact else
                    '<div class="note">No earnings step stated.</div>', "s03_transmission")
            + block("Strongest evidence", f"<ul>{evidence}</ul>" if evidence else
                    '<div class="note">No figure recorded.</div>', "s04_key_evidence")
            + block(f"Why {act}", f"<ul>{why}</ul>", "s08_decision")
            + block("What could invalidate it", "<ul>" + "".join(
                x if x.startswith("<li>") else f"<li>{x}</li>" for x in risks) + "</ul>"
                    if risks else '<div class="note">None recorded.</div>',
                    "s07_what_could_go_wrong")
            + block("Next check", nxt, "s08_decision")
            + "</div>")


_ROLE_WORD = {"supports": "supports", "dislocation": "dislocation", "catalyst": "catalyst",
              "contradicts": "counter-evidence", "context": "context",
              "competing": "competing hypothesis"}


def _other_row(c: Claim, card: CardContent, rc: RenderContext) -> str:
    """One cited claim outside the key-evidence rows — the same columns, its role in place of the
    upstream origin; its row id is the claim id every link to it uses."""
    flags = [c.epistemic.value] + (["APPROXIMATE"] if c.approximate else []) \
        + (["chart-derived"] if c.chart_derived else []) + list(c.qualifiers) \
        + ([] if c.span_verified and c.number_verified is not False else ["NOT VERIFIED"])
    label = " — ".join(x for x in (c.scope, c.metric) if x) or c.statement
    role = rc.roles.get(c.claim_id, "")
    return (f'<tr id="{e(c.claim_id)}"><td>{e(label)}<div class="q">“{e(c.quote)}”</div></td>'
            f'<td><b>{e(c.value_text or "—")}</b> {e(unit_shown(c.value_text, c.unit))}</td>'
            f'<td>{e(c.period or "—")}<div class=note>as of '
            f'{e(c.measured_as_of.isoformat() if c.measured_as_of else "—")}</div></td>'
            f'<td>{e(" · ".join(flags))}</td><td>{e(_ROLE_WORD.get(role, role or "—"))}</td>'
            f'<td>{e(_source_name(card, c.article_id))}<div class="note">paragraph '
            f'{e(_para(c.block_id))}</div><div class="cc aud">{e(c.article_id)} {e(c.block_id)} · '
            f'{e(c.claim_id)}</div></td></tr>')


#: a link into a collapsed section opens it: every <details> around the target opens, the page
#: scrolls to it and marks it — on load (a link from the weekly page), on a hash change and on a
#: repeated click of the same link
REVEAL_JS = (
    "<script>function reveal(h){if(!h||h.length<2)return;var t=document.getElementById("
    "decodeURIComponent(h.slice(1)));if(!t)return;for(var d=t.closest('details');d;"
    "d=d.parentElement?d.parentElement.closest('details'):null)d.open=true;"
    "t.scrollIntoView({block:'center'});t.classList.add('hit');setTimeout(function(){"
    "t.classList.remove('hit')},2500)}"
    "addEventListener('hashchange',function(){reveal(location.hash)});"
    "addEventListener('load',function(){reveal(location.hash)});"
    "document.addEventListener('click',function(ev){var a=ev.target.closest&&"
    "ev.target.closest('a[href^=\"#\"]');if(a&&a.getAttribute('href')===location.hash)"
    "reveal(location.hash)});</script>")


def mechanism_step(card: CardContent, skip: Iterable[str] = ()) -> int | None:
    """The index of the step that says HOW the thesis works in the source's own terms: its first
    transmission step stated by the source (the industry shift, when there is one) and not
    withheld or questioned — a verified line of the card, never a taxonomy category."""
    out = [i for i, st in enumerate(card.s03_transmission)
           if st.step != "market_reaction" and st.provenance in SOURCE_LABELS
           and f"s03.{i}" not in set(skip)]
    return out[0] if out else None


def _plain_text(text: str) -> str:
    """A line without its system labels ⟨…⟩ (kept on the line in the sections below)."""
    return re.sub(r"\s*⟨[^⟩]*⟩\s*", " ", text).strip()


def render_html(card: CardContent, rc: RenderContext, *, print_mode: bool = False) -> str:
    """The Living Thesis Card. A short header (action, horizon, dates, a Review Required
    indicator linked to the exact lines), the AT-A-GLANCE answers folded away (they repeat the
    sections; not printed), then the nine sections in order — every line, figure and source as
    before. Claim ids, engine codes and the decision trace sit behind the audit switch; the print
    view opens everything (the complete record)."""
    h = card.header
    key_ids = [r.claim_id for r in card.s04_key_evidence]
    others = [rc.claims[c] for c in cited_claim_ids(card) if c not in key_ids and c in rc.claims]
    rc = replace(rc, targets=frozenset(key_ids) | {c.claim_id for c in others})
    pill = _PILL.get(h.research_action.value, "skip")
    kind = (f'<span class="pill kind">{e(KIND_LABEL[h.kind])}</span>'
            if h.kind is ThesisKind.MARKET_REGIME else "")
    findings = [sid for sid in card_sentences(card) if sid in rc.blocked or sid in rc.flagged]
    done = [sid for sid in card_sentences(card) if sid in rc.resolved]
    earlier = (f' <span class="note">· <a href="#{_anchor(done[0])}">{len(done)} earlier review '
               f'finding(s) resolved</a></span>' if done else "")
    review = (f'<a class="flag" href="#{_anchor(findings[0])}">Review required · '
              f'{len(findings)} line(s)</a> <span class="note">'
              + " · ".join(f'<a href="#{_anchor(s)}">{e(n)}</a>'
                           for s, n in zip(findings, finding_names(findings), strict=True))
              + "</span>" if findings else
              # a version the review never read is not clean: it says it was not reviewed
              '<span class="flag">Not reviewed</span>' if rc.carry.not_run is not None else
              '<span class="okflag">No unresolved review findings on this card</span>') + earlier
    parts = [
        f'<header class="hdr"><div class="eyebrow">Living Thesis Card · {e(h.sector)} · '
        f'{e(h.region)}</div><h1>{e(h.title)}</h1><div class="hline"><span class="pill {pill}">'
        f'{e(_action_words(h.research_action.value, rc.priority, card.s05_affected))}</span>'
        f'{kind}'
        f'<span class="meta">Horizon: {e(h.horizon)}</span><span class="meta">Evidence: '
        f'{e(h.evidence_direction.value.lower())}</span>'
        + (f'<span class="meta">Status: {e(h.status.value)}</span>'
           if h.status.value != "ACTIVE" else "")
        + f'</div><div class="dates">{e(first_detected_line(h))}</div>'
        + (f'<div class="statusnote">{e(rc.status_note)}</div>' if rc.status_note else "")
        + review_status_html(rc)
        + f'<div class="vline">{review}</div><div class="id aud cc">{e(h.thesis_id)} · '
          f'{e(" › ".join(h.ancestry))} · {e(h.research_action.value)}</div></header>',
        # the seven answers repeat the sections' own opening lines (and the desk's reading page,
        # which links here as the full record): folded away on screen, left out of the print —
        # they hold no fact the sections below do not (operator, 2026-10-14)
        "" if print_mode else (
            '<details class="glancefold"><summary>At a glance — the seven answers, repeated '
            'from the sections below</summary>' + _glance(card, rc) + "</details>"),
        f'<details class="legend"{" open" if print_mode else ""}><summary>How to read the line '
        f'labels</summary>{e(LEGEND)}</details>']
    bodies: dict[str, str] = {}
    summaries: dict[str, str] = {}
    bodies["s01_bottom_line"] = "".join(_sent(s, f"s01.{i}", rc)
                                        for i, s in enumerate(card.s01_bottom_line))
    wc = card.s02_what_changed

    def item(i: int, it: ChangeItem) -> str:
        sid = f"s02.{i}"
        tag = _CHANGE_TAG.get(it.change_class, it.change_class.value)
        body = (f'<span class="withheld">WITHHELD — failed source verification</span>'
                f'<span class="aud"> {e(rc.blocked[sid])}</span>'
                if sid in rc.blocked else quiet_labels(ids_to_audit(e(_clean_display(it.text)))))
        p = shown_label(it.provenance, sid, rc)
        flagged = " flagged" if sid in rc.blocked or sid in rc.flagged else ""
        return (f'<div class="s{flagged}" id="{_anchor(sid)}">'
                + (f'<span class="step">{e(tag)}</span>' if tag else "")
                + f'<span class="lab {_BADGE[p]}">{e(p.value)}</span> ' + body
                + (f' <span class="note">(article date {e(it.original_date)}'
                   + (f"; period {e(it.period)}" if it.period else "") + ")</span>"
                   if it.original_date else "")
                + f'<span class="aud"> <span class="cc">[{e(it.change_class.value)}]</span>'
                  f'</span>{_refs(it.claim_ids, rc)}{_warn_html(sid, rc)}'
                  f'{_resolved_html(sid, rc)}{_corr_html(sid, rc)}</div>')
    first = [item(i, it) for i, it in enumerate(wc.items)]
    shown, rest = first[:3], first[3:]
    bodies["s02_what_changed"] = (
        f'<div class="note">{ids_to_audit(e(wc.vs_prior))}</div>'
        f'<div class="note aud">novelty: {e(wc.novelty)}</div>' + "".join(shown)
        + (('<details' + (" open" if print_mode else "") + f'><summary class="note">show the '
            f'other {len(rest)} of {len(first)}</summary>' + "".join(rest) + "</details>")
           if rest else ""))
    bodies["s03_transmission"] = "".join(
        _sent(CardSentence(text=st.text, provenance=st.provenance, claim_ids=st.claim_ids),
              f"s03.{i}", rc, step=STEP_LABEL.get(st.step, st.step))
        for i, st in enumerate(card.s03_transmission))
    src_steps = sum(1 for st in card.s03_transmission if st.provenance in SOURCE_LABELS)
    summaries["s03_transmission"] = (f"{len(card.s03_transmission)} step(s), {src_steps} stated "
                                     f"by the source")
    rows = []
    for r in card.s04_key_evidence:
        flags = [r.epistemic.value]
        if r.approximate:
            flags.append("APPROXIMATE")
        if r.chart_derived:
            flags.append("chart-derived")
        flags.extend(r.qualifiers)
        asof = r.measured_as_of.isoformat() if r.measured_as_of else "—"
        also = (f'<div class="note">also reported in: {e(", ".join(r.also_reported_in))} '
                f'(same origin — attribution, not new evidence)</div>'
                if r.also_reported_in else "")
        rows.append(
            f'<tr id="{e(r.claim_id)}"><td>{e(r.label)}<div class="q">“{e(r.quote)}”</div>'
            f'{also}</td><td><b>{e(r.value_text or "—")}</b> '
            f'{e(unit_shown(r.value_text, r.unit))}'
            + (f"<div class=note>{e(r.comparator)}</div>" if r.comparator else "")
            + f'</td><td>{e(r.period or "—")}<div class=note>as of {e(asof)}</div></td>'
              f'<td>{e(" · ".join(flags))}</td><td>{e(r.origin or "—")}</td><td>'
              f'{e(_source_name(card, r.article_id))}<div class="note">paragraph '
              f'{e(_para(r.block_id))}</div><div class="cc aud">{e(r.article_id)} '
              f'{e(r.block_id)} · {e(r.claim_id)} · {e(r.role.value)} · '
              f'{e(r.change_class.value)}</div></td></tr>')
    bodies["s04_key_evidence"] = (
        f'<div class="note">{len(card.s04_key_evidence)} evidence row(s); every figure links to '
        f'its verbatim source span. Figures repeating one origin are one row.</div>'
        '<div class="hscroll"><table><tr><th>Evidence</th><th>Value</th><th>Period / as-of</th>'
        "<th>Type</th><th>Upstream origin</th><th>Source passage</th></tr>" + "".join(rows)
        + "</table></div>"
        + (f'<details class="more"{" open" if print_mode else ""}><summary>Other evidence this '
           f'card cites ({len(others)}) — counter-evidence, context and citations outside the key '
           f'rows</summary><div class="hscroll"><table><tr><th>Evidence</th><th>Value</th>'
           f'<th>Period / as-of</th><th>Type</th><th>Role on this thesis</th><th>Source passage'
           f'</th></tr>' + "".join(_other_row(c, card, rc) for c in others)
           + "</table></div></details>" if others else ""))
    summaries["s04_key_evidence"] = (f"{len(card.s04_key_evidence)} evidence row(s)"
                                     + (f" · {len(others)} more cited" if others else ""))
    av = card.s05_affected
    inst = exposure_instruments(av)
    sector_rows = "".join(
        f'<div class="s"><span class="lab {_BADGE[s.provenance]}">{e(s.provenance.value)}</span> '
        f'<b>{e(s.name)}</b> — {e(s.direction.value)} <span class="q">“{e(s.quote)}”</span>'
        f'{_refs(s.claim_ids, rc)}</div>' for s in distinct_sectors(av))
    group_rows = "".join(
        f'<div class="s"><b>{e(g.name)}</b> <span class="q">{e(g.excerpt)}</span> '
        f'<span class="note">paragraph {e(", ".join(_para(b) for b in g.block_ids))}</span>'
        f'{_refs(g.claim_ids, rc)}</div>' for g in rc.groups)
    bodies["s05_affected"] = (
        '<div class="sub">Sectors / themes the source names as exposed</div>'
        + (sector_rows or '<div class="note">None named by the source.</div>')
        + '<div class="sub">Business groups the source names — not companies; no ticker is '
          'implied and the research action does not count them</div>'
        + group_rows + (f'<div class="note">{e(groups_unchecked_note(rc.groups_unread))}</div>'
                        if rc.groups_unread else "" if group_rows else
                        '<div class="note">None named in the paragraphs holding this thesis\'s '
                        'evidence.</div>')
        + '<div class="sub">Stock exposures of this thesis (source-named companies)</div>'
        + _company_rows(exposures_of(av)[0], exposures=True)
        + f'<div class="sub">{INSTRUMENT_EXPOSURES}</div>'
        + _company_rows(inst, exposures=True)
        + f'<div class="sub">{NAMED_INSTRUMENTS}</div>'
        + _company_rows([c for c in av.instruments if c not in inst])
        + '<div class="sub">Private or unlisted (stay private)</div>'
        + _company_rows(av.private_or_unlisted)
        + '<div class="sub">Named, not securities (products, baskets, agencies)</div>'
        + _company_rows([c for c in av.not_securities if c not in inst])
        + '<div class="sub">Also named in the source — mentions, NOT exposures of this thesis'
          '</div>' + _company_rows(exposures_of(av)[1] + list(av.also_named))
        + '<div class="sub">Sector labels</div><div class="s">' + e(", ".join(av.sectors) or "—")
        + "</div>" + '<div class="sub">Cited baskets (members NOT named by the source)</div>'
        + ("".join(_sent(s, f"s05.b{i}", rc) for i, s in enumerate(av.baskets)) or
           '<div class="note">None.</div>')
        + '<div class="sub">Enrichment — EXTERNAL HYPOTHESES, not named by the source</div>'
        + enrichment_html(rc.enrichment, card, rc))
    summaries["s05_affected"] = (f"{len(distinct_sectors(av))} sector(s) · "
                                 + (f"{len(rc.groups)} business group(s) named · "
                                    if rc.groups else "business groups not checkable here · "
                                    if rc.groups_unread else "")
                                 + f"{len(exposures_of(av)[0])} company exposure(s) · "
                                 + (f"{len(inst)} instrument exposure(s) · " if inst else "")
                                 + f"{len(exposures_of(av)[1]) + len(av.also_named)} other "
                                   f"mention(s)")
    wn = card.s06_why_now
    bodies["s06_why_now"] = (
        '<div class="sub">Near term (2-4 quarters)</div>'
        + ("".join(_sent(s, f"s06.{i}", rc) for i, s in enumerate(wn.near_term))
           or '<div class="note">None in the sources.</div>')
        + '<div class="sub">Longer-term / structural (kept separate)</div>'
        + "".join(_sent(s, f"s06.{len(wn.near_term) + i}", rc)
                  for i, s in enumerate(wn.structural))
        + f'<div class="sub">Catalyst / repricing window</div><div class="s">'
          f'{e(wn.catalyst_window)}</div><div class="sub">Consensus / valuation</div>'
          f'<div class="s"><span class="lab unk">NOT ASSESSED</span> '
          f'{e(_once("NOT_ASSESSED", wn.valuation_status)[len("NOT_ASSESSED — "):])}</div>')
    w = card.s07_what_could_go_wrong
    n0, n1, n2 = len(w.counter_evidence), len(w.alternative_mechanisms), len(w.market_risks)
    bodies["s07_what_could_go_wrong"] = (
        '<div class="sub">Strongest counter-evidence in the sources</div>'
        + ("".join(_sent(s, f"s07.{i}", rc) for i, s in enumerate(w.counter_evidence))
           or '<div class="note">None in the sources so far.</div>')
        + '<div class="sub">Alternative mechanisms / competing hypotheses</div>'
        + "".join(_sent(s, f"s07.{n0 + i}", rc) for i, s in enumerate(w.alternative_mechanisms))
        + '<div class="sub">Market-level risks (kept as risks, not theses)</div>'
        + ("".join(_sent(s, f"s07.{n0 + n1 + i}", rc) for i, s in enumerate(w.market_risks))
           or '<div class="note">None recorded.</div>')
        + ('<div class="sub">Price performance — market context, not earnings evidence</div>'
           + "".join(_sent(s, f"s07.{n0 + n1 + n2 + i}", rc)
                     for i, s in enumerate(w.price_context)) if w.price_context else "")
        + '<div class="sub">Observable disconfirming signals</div>'
        + "".join(_sent(s, "-", rc) for s in w.disconfirming_observables)
        + '<div class="sub">Unknowns</div>'
        + "".join(_sent(s, "-", rc) for s in w.unknowns))
    summaries["s07_what_could_go_wrong"] = (
        f"{len(w.counter_evidence)} counter-evidence · {len(w.alternative_mechanisms)} "
        f"alternatives · {len(w.market_risks)} market risk(s)"
        + (f" · {len(w.price_context)} price-context line(s)" if w.price_context else ""))
    d = card.s08_decision
    bodies["s08_decision"] = (
        f'<div class="s"><span class="pill {_PILL.get(d.research_action.value, "skip")}">'
        f'{e(_action_words(d.research_action.value, rc.priority, card.s05_affected))}</span> '
        f'<span class="note">research attention only — this card never directs a purchase or '
        f'sale</span></div>'
        + "".join(f'<div class="s">{e(x)}</div>'
                  for x in why_reasons(card, rc.priority, [g.name for g in rc.groups],
                              groups_unchecked=rc.groups_unread > 0))
        + '<div class="sub">Next investigable step</div>' + _sent(d.next_step, "s08.next", rc)
        + '<div class="sub">Would raise priority</div>'
        + "".join(_sent(s, "-", rc) for s in d.raise_priority_if)
        + '<div class="sub">Would lower priority</div>'
        + "".join(_sent(s, "-", rc) for s in d.lower_priority_if)
        + f'<div class="sub">Investment readiness</div><div class="s">'
          f'{e(readiness_text(d.investment_readiness.value, d.readiness_note))}</div>'
          '<div class="aud"><div class="sub">Decision trace (deterministic rules)</div>'
        + "".join(f'<div class="s cc">{e(t)}</div>' for t in d.rule_trace) + "</div>")
    def src_title(s: SourceRef) -> str:
        """Linked only to a WEB address (desk.py's `_link` rule): an article's canonical URL
        comes from the page itself, and a `javascript:` one stayed clickable on the card."""
        title = e(clean_title(s.title, s.publisher) or 'title UNKNOWN')
        return (f'<a href="{e(s.url)}">{title}</a>'
                if s.url.startswith(("http://", "https://")) else title)

    src_rows = "".join(
        f"<tr><td>{src_title(s)}"
        f"<div class=note>{e(s.article_class.value.replace('_', ' '))} · retrieval "
        f"{e(rc.retrieval_now.get(s.article_id, s.retrieval_state.value))}</div>"
        f"<div class=\"cc aud\">{e(s.article_id)}</div></td>"
        f"<td>{e('; '.join(s.authors) if s.authors else 'UNKNOWN')}</td><td>{e(s.publisher)}</td>"
        f"<td>{e(s.published_at.date().isoformat() if s.published_at else 'UNKNOWN')}"
        + "".join(f"<div class=note>{e(x)}</div>" for x in s.version_dates) + "</td>"
        f"<td>{e(', '.join(s.upstream_origins) or '—')}</td><td>"
        f"{e(_CHANGE_TAG.get(s.contribution) or 'Initial record')}"
        f"<div class=\"note aud\">{e(s.contribution.value)} · {e(len(s.claim_ids))} claim "
        f"ref(s)</div></td></tr>"
        for s in card.s09_sources)
    hist_rows = "".join(
        f"<tr><td>v{v.version}</td><td>{e(v.as_of.isoformat())}</td>"
        f"<td>{e(v.priority.research_action.value)}</td><td>{e(v.evidence_direction.value)}</td>"
        f"<td>{ids_to_audit(e(_clean_display(v.change_summary)))}<div class=\"note aud\">"
        f"{e(v.priority.change_reason)}</div>"
        + "".join(f'<div class="cc aud">{e(dd.field_id)}: {e(dd.change_class.value)} — '
                  f"{e(clip(dd.new or '', 140))}</div>" for dd in v.diffs)
        + "</td></tr>" for v in rc.history)
    attr = "".join(f'<div class="s cc">{e(a)} — {e(c)}: {e(n)}</div>'
                   for a, c, n in rc.attributions)
    bodies["s09_sources"] = (
        '<div class="hscroll"><table><tr><th>Source</th><th>Author(s)</th><th>Publisher</th>'
        "<th>Article date</th><th>Upstream origin(s)</th><th>Contribution</th></tr>" + src_rows
        + '</table></div><div class="sub">Version history (immutable)</div><div class="hscroll">'
          "<table><tr><th>Ver</th><th>As of</th><th>Action</th><th>Evidence</th>"
          "<th>Why it changed</th></tr>" + hist_rows + "</table></div>"
        + ('<div class="sub">Attributions without a new version</div>' + attr if attr else ""))
    summaries["s09_sources"] = (f"{len(card.s09_sources)} source(s) · {len(rc.history)} "
                                f"version(s)")
    for fid, title in SECTION_IDS:
        parts.append(_section(fid, title, bodies[fid], print_mode=print_mode,
                              summary=summaries.get(fid, "")))
    parts.append(foot_html(rc.generated_note))
    script = ("<script>window.addEventListener('beforeprint',()=>document.querySelectorAll("
              "'details').forEach(d=>d.open=true));</script>" + REVEAL_JS)
    body = "".join(parts)
    if print_mode:  # the print file is the COMPLETE record: every nested audit toggle opens too
        body = body.replace("<details>", "<details open>")
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
            "content='width=device-width,initial-scale=1'>" + ROBOTS + "<title>" + e(h.title)
            + "</title><style>" + _CSS + "</style></head><body>" + AUDIT_TOGGLE
            + topnav("../", active="Themes") + "<div class='wrap narrow'><article class=card>"
            + body
            + "</article></div>" + script + "</body></html>")


def _md_sents(ss: Iterable[CardSentence], prefix: str, rc: RenderContext,
              start: int = 0) -> list[str]:
    out = []
    for i, s in enumerate(ss, start):
        sid = f"{prefix}.{i}"
        refs = (" [" + ", ".join(s.claim_ids) + "]") if s.claim_ids else ""
        if sid in rc.blocked:
            out.append(f"- **WITHHELD — failed source verification:** {rc.blocked[sid]}")
        else:
            out.append(f"- **{shown_label(s.provenance, sid, rc).value}:** "
                       f"{_clean_display(s.text)}{refs}" + _warn_md(sid, rc)
                       + _resolved_md(sid, rc)
                       + (f" _(corrected by the analyst — {rc.corrected[sid]})_"
                          if sid in rc.corrected else ""))
    return out


def render_markdown(card: CardContent, rc: RenderContext) -> str:
    h = card.header
    q = (watch_of(rc.priority, card.s05_affected)
         if rc.priority is not None and rc.priority.research_action is h.research_action else "")
    md = [f"# {h.title}", "",
         f"**{h.research_action.value}{f' · {q}' if q else ''}** · {KIND_LABEL[h.kind]} · evidence "
         f"{h.evidence_direction.value} · {h.sector} · {h.region} · horizon {h.horizon} · status "
         f"{h.status.value}", "", first_detected_line(h), "",
         f"`{h.thesis_id}` · {' › '.join(h.ancestry)}", "", f"_{LEGEND}_", ""]
    if rc.status_note:
        md += [f"> **{rc.status_note}**", ""]
    if rc.carry.not_run is not None:
        md += [f"> **Not reviewed — the card review did not run for this version: "
               f"{review_not_run_words(rc.carry.not_run)}.** Earlier findings stay on their lines "
               f"until a review runs."]
        md += [f"> - not re-reviewed (line removed): “{clip(f.origin_text, 200)}” — {f.said} "
               f"({carried_note(f)})" for f in rc.carry.removed]
        md += [""]
    titles = dict(SECTION_IDS)
    md += [f"## {titles['s01_bottom_line']}"] + _md_sents(card.s01_bottom_line, "s01", rc) + [""]
    wc = card.s02_what_changed
    md += [f"## {titles['s02_what_changed']}", f"- {wc.vs_prior}", f"- novelty: {wc.novelty}"]
    for i, it in enumerate(wc.items):
        txt = (f"WITHHELD — {rc.blocked[f's02.{i}']}" if f"s02.{i}" in rc.blocked else it.text)
        tag = _CHANGE_TAG.get(it.change_class, it.change_class.value)
        md.append("- " + (f"[{tag}] " if tag else "")
                 + f"**{shown_label(it.provenance, f's02.{i}', rc).value}:** {txt}"
                 + (f" (article date {it.original_date}" + (f"; period {it.period}"
                                                              if it.period else "") + ")"
                    if it.original_date else "")
                 + (" [" + ", ".join(it.claim_ids) + "]" if it.claim_ids else "")
                 + _warn_md(f"s02.{i}", rc) + _resolved_md(f"s02.{i}", rc))
    md += ["", f"## {titles['s03_transmission']}"]
    for i, st in enumerate(card.s03_transmission):
        md += [f"- _{STEP_LABEL.get(st.step, st.step)}_ "
               + _md_sents([CardSentence(text=st.text, provenance=st.provenance,
                                         claim_ids=st.claim_ids)], "s03", rc, i)[0][2:]]
    md += ["", f"## {titles['s04_key_evidence']}",
          "| Evidence | Value | Period / as-of | Type | Upstream origin | Anchor |",
          "|---|---|---|---|---|---|"]
    for r in card.s04_key_evidence:
        flags = [r.epistemic.value] + (["APPROXIMATE"] if r.approximate else []) \
            + (["chart-derived"] if r.chart_derived else []) + list(r.qualifiers)
        q = r.quote.replace("|", "\\|")
        md.append(f"| {r.label} — “{q}”"
                 + (f" (also reported in {', '.join(r.also_reported_in)})"
                    if r.also_reported_in else "")
                 + f" | {r.value_text or '—'} {unit_shown(r.value_text, r.unit)} "
                 f"{r.comparator or ''} | "
                 f"{r.period or '—'} / as of {r.measured_as_of or '—'} | {' · '.join(flags)} | "
                 f"{r.origin or '—'} | {r.article_id} {r.block_id} ({r.claim_id}; "
                 f"{r.role.value}; {r.change_class.value}) |")
    key_ids = {r.claim_id for r in card.s04_key_evidence}
    others = [rc.claims[c] for c in cited_claim_ids(card) if c not in key_ids and c in rc.claims]
    if others:
        md += ["", "**Other evidence this card cites:**"] + [
            f"- {c.statement} — {c.value_text or '—'} {unit_shown(c.value_text, c.unit)} — "
            f"{c.period or '—'} — {c.epistemic.value} — "
            f"{_ROLE_WORD.get(rc.roles.get(c.claim_id, ''), rc.roles.get(c.claim_id, '—'))} — "
            f"“{c.quote}” ({c.article_id} {c.block_id}; {c.claim_id})" for c in others]
    av = card.s05_affected
    md += ["", f"## {titles['s05_affected']}", "**Sectors / themes the source names as exposed:**"]
    md += [f"- **{s.provenance.value}:** {s.name} — {s.direction.value} — “{s.quote}”"
           + (" [" + ", ".join(s.claim_ids) + "]" if s.claim_ids else "")
           for s in distinct_sectors(av)] or ["- none named by the source"]
    md.append("**Business groups the source names — not companies; no ticker implied:**")
    md += [f"- {g.name} — {g.excerpt} (paragraph {', '.join(_para(b) for b in g.block_ids)})"
           + (" [" + ", ".join(g.claim_ids) + "]" if g.claim_ids else "")
           for g in rc.groups] or ([] if rc.groups_unread else ["- none"])
    if rc.groups_unread:
        md.append(f"- {groups_unchecked_note(rc.groups_unread)}")
    # (label, group) PAIRS — never `grp is av.instruments`: every empty tuple is the same object,
    # so identity matched one empty group to another's heading
    inst = exposure_instruments(av)
    for label, grp, expo in (("Stock exposures of this thesis", exposures_of(av)[0], True),
                             (INSTRUMENT_EXPOSURES, inst, True),
                             (NAMED_INSTRUMENTS, [c for c in av.instruments if c not in inst],
                              False),
                             ("Private or unlisted", av.private_or_unlisted, False),
                             ("Named, not securities (products, baskets, agencies)",
                              [c for c in av.not_securities if c not in inst], False),
                             ("Also named in the source — mentions, NOT exposures of this thesis",
                              exposures_of(av)[1] + list(av.also_named), False)):
        md.append(f"**{label}:**")
        for c in grp:
            lst = _listing_text(c.listings) or "—"
            other = "; ".join(f"{x.ticker} {x.pit_status.value}" for x in c.other_securities)
            reading = (f" — this thesis reads it as {c.exposure_reading or c.role.value} "
                       f"[{(c.exposure_provenance or Provenance.MODEL_INFERENCE).value}]"
                       if expo else "")
            md.append(f"- {c.name_as_written} — {lst} — {c.resolution_status.value} — the source "
                     f"states: {c.role.value} ({c.role_detail}){reading} — {c.direction.value} — "
                     f"{c.recommendation_status.value}"
                     + (f" — other lines: {other}" if other else ""))
        if not grp:
            md.append("- none")
    md.append(f"**Sector labels:** {', '.join(av.sectors) or '—'}")
    md.append("**Cited baskets (members not named by the source):**")
    md += _md_sents(av.baskets, "s05.b", rc) or ["- none"]
    head, rows = enrichment_lines(rc.enrichment, rc.history[-1].version if rc.history else 0,
                                  card_steps(card), set_card(rc.enrichment, rc.history))
    md.append("**Enrichment — external hypotheses, not named by the source:** "
              + (head or "not proposed yet"))
    md += [f"- {r}" for r in rows]
    wn = card.s06_why_now
    md += ["", f"## {titles['s06_why_now']}", "**Near term:**"]
    md += _md_sents(wn.near_term, "s06", rc)
    md += ["**Longer-term / structural:**"] + _md_sents(wn.structural, "s06", rc,
                                                        len(wn.near_term))
    md += [f"**Catalyst window:** {wn.catalyst_window}",
          f"**Consensus / valuation:** NOT ASSESSED — {wn.valuation_status}"]
    w = card.s07_what_could_go_wrong
    md += ["", f"## {titles['s07_what_could_go_wrong']}", "**Counter-evidence:**"]
    md += _md_sents(w.counter_evidence, "s07", rc) or ["- none in the sources so far"]
    md += ["**Alternative mechanisms / competing hypotheses:**"]
    md += _md_sents(w.alternative_mechanisms, "s07", rc, len(w.counter_evidence))
    md += ["**Market-level risks:**"]
    md += _md_sents(w.market_risks, "s07", rc,
                   len(w.counter_evidence) + len(w.alternative_mechanisms)) or ["- none"]
    if w.price_context:
        md += ["**Price performance — market context, not earnings evidence:**"] + _md_sents(
            w.price_context, "s07", rc, len(w.counter_evidence) + len(w.alternative_mechanisms)
            + len(w.market_risks))
    md += ["**Disconfirming signals:**"] + [f"- {s.text}" for s in w.disconfirming_observables]
    md += ["**Unknowns:**"] + [f"- {s.text}" for s in w.unknowns]
    d = card.s08_decision
    md += ["", f"## {titles['s08_decision']}",
          f"**{d.research_action.value}** — research attention only; never a purchase or sale.",
          *_md_sents([d.next_step], "s08", rc), "**Would raise priority:**",
          *[f"- {s.text}" for s in d.raise_priority_if], "**Would lower priority:**",
          *[f"- {s.text}" for s in d.lower_priority_if],
          f"**Investment readiness:** {_once(d.investment_readiness.value, d.readiness_note)}",
          "**Decision trace (audit):**", *[f"- {t}" for t in d.rule_trace]]
    md += ["", f"## {titles['s09_sources']}"]
    for s in card.s09_sources:
        art_date = s.published_at.date().isoformat() if s.published_at else "UNKNOWN"
        if s.version_dates:
            art_date += f" (versions: {'; '.join(s.version_dates)})"
        md.append(f"- [{clean_title(s.title, s.publisher) or 'title UNKNOWN'}]({s.url}) — "
                 f"{'; '.join(s.authors) if s.authors else 'author UNKNOWN'} — {s.publisher} — "
                 f"article date {art_date}"
                 f" — {s.article_class.value} — retrieval "
                 f"{rc.retrieval_now.get(s.article_id, s.retrieval_state.value)} — origins: "
                 f"{', '.join(s.upstream_origins) or '—'} — {s.contribution.value} "
                 f"({len(s.claim_ids)} claim refs; {s.article_id})")
    md.append("**Version history:**")
    for v in rc.history:
        md.append(f"- v{v.version} as of {v.as_of} — {v.priority.research_action.value} — "
                 f"evidence {v.evidence_direction.value} — {v.change_summary} "
                 f"({v.priority.change_reason})")
        for dd in v.diffs:
            md.append(f"  - {dd.field_id}: {dd.change_class.value} — {clip(dd.new or '', 160)}")
    for aid, cls, note in rc.attributions:
        md.append(f"- attribution without a new version: {aid} — {cls}: {note}")
    md += ["", f"_{rc.generated_note}_", ""]
    return plain_entities("\n".join(md))


def render_json(card: CardContent, rc: RenderContext) -> dict[str, Any]:
    return {
        "status_note": rc.status_note,
        "card": json.loads(card.model_dump_json()),
        "section_order": [fid for fid, _ in SECTION_IDS],
        "history": [json.loads(v.model_dump_json()) for v in rc.history],
        "attributions_without_version": [
            {"article_id": a, "contribution": c, "note": n} for a, c, n in rc.attributions],
        "withheld_sentences": rc.blocked,
        "review_warnings": rc.flagged,
        "analyst_corrections": rc.corrected,
        "why_action": why_reasons(card, rc.priority, [g.name for g in rc.groups],
                              groups_unchecked=rc.groups_unread > 0),
        "review_resolved": {k: why for k, (why, _said) in rc.resolved.items()},
        "review_not_run": rc.carry.not_run,
        "review_carried": {k: {"code": f.code, "origin_version": f.origin_version,
                               "origin_as_of": f.origin_as_of.isoformat(),
                               "origin_text": f.origin_text, "not_re_reviewed": f.changed}
                           for k, f in rc.carry.carried.items()},
        "review_removed_lines": [{"code": f.code, "detail": f.detail,
                                  "origin_version": f.origin_version,
                                  "origin_text": f.origin_text} for f in rc.carry.removed],
        "named_business_groups_unchecked_paragraphs": rc.groups_unread,
        "named_business_groups": [
            {"name": g.name, "article_id": g.article_id, "block_ids": list(g.block_ids),
             "excerpt": g.excerpt, "claim_ids": list(g.claim_ids)} for g in rc.groups],
        "enrichment": (json.loads(rc.enrichment.model_dump_json())
                       if rc.enrichment is not None else None),
        "other_cited_evidence": [c for c in cited_claim_ids(card)
                                 if c not in {r.claim_id for r in card.s04_key_evidence}],
        "generated": rc.generated_note,
    }


def sector_exposures_from(sectors: Iterable[VerifiedSector], claims: dict[str, Claim],
                          article_id: str, prev: AffectedView | None) -> tuple[SectorExposure, ...]:
    """Verified sector spans as card exposures, unioned with the prior version's (keyed by the
    normalised name). A sector line is the SOURCE's statement: labelled by its cited claims when
    it cites any, else SOURCE OPINION (the source names the population; that it is exposed is
    the source's argument)."""
    out = {norm_name(x.name): x for x in (prev.sector_exposures if prev else ())}
    for vs in sectors:
        k = norm_name(vs.name)
        if k in out:
            continue
        out[k] = SectorExposure(name=vs.name, direction=vs.direction,
                                provenance=label_for(vs.claim_ids, claims)
                                or Provenance.SOURCE_OPINION,
                                quote=vs.quote, article_id=article_id,
                                claim_ids=tuple(vs.claim_ids))
    return tuple(out.values())


def affected_from(*, mention_ids: list[tuple[str, str]], mentions: dict[str, Any],
                  resolutions: dict[str, Any], sectors: list[str],
                  baskets: list[CardSentence], prev: AffectedView | None,
                  enrichment: tuple[EnrichmentCandidate, ...] = (),
                  article_mentions: tuple[str, ...] = (),
                  sector_exposures: tuple[SectorExposure, ...] = ()) -> AffectedView:
    """Split source-named entities into companies / instruments / private, union with the prior
    version's lists. Only ids from verified source mentions can reach here."""
    # keyed by ENTITY (SEC CIK, else normalised name), not by mention: the same company named by
    # a second article is the same exposure, listed once (the first naming is kept)
    comp = {entity_key(c): c for c in prev.companies} if prev else {}
    inst = {entity_key(c): c for c in prev.instruments} if prev else {}
    priv = {entity_key(c): c for c in prev.private_or_unlisted} if prev else {}
    nsec = {entity_key(c): c for c in prev.not_securities} if prev else {}
    for mid, thesis_role in mention_ids:
        m = mentions[mid]
        r = resolutions.get(mid)
        status = r.status if r else ResolutionStatus.UNRESOLVED
        # the article's STATED role stays the role; the THESIS's reading of the name is a separate
        # field with its own label — the source's word when the source states that role, MODEL
        # INFERENCE when the thesis infers it (e.g. a capex spender read as a beneficiary)
        direction = _CONTEXT_DIRECTION.get(thesis_role, m.direction)
        source_says = not thesis_role or thesis_role == m.role.value
        reading = (thesis_role or m.role.value).replace("_", " ")
        ac = AffectedCompany(mention_id=mid, name_as_written=m.name_as_written,
                             resolution_status=status, listings=r.listings if r else (),
                             cik=r.cik if r else None, role=m.role, role_detail=m.role_detail,
                             direction=direction, recommendation_status=m.recommendation_status,
                             article_id=m.article_id, quote=m.quote, exposure_reading=reading,
                             exposure_provenance=Provenance.SOURCE_OPINION if source_says
                             else Provenance.MODEL_INFERENCE,
                             other_securities=r.other_securities if r else ())
        key = entity_key(ac)
        group = (inst if status in (ResolutionStatus.FUND, ResolutionStatus.INDEX)
                 else priv if status is ResolutionStatus.PRIVATE
                 else nsec if status is ResolutionStatus.NOT_A_SECURITY else comp)
        old = group.setdefault(key, ac)
        if old is not ac and not _verified(old) and _verified(ac):
            # the first naming is kept, with the listing a later naming VERIFIED — a stale
            # "not verified" from an earlier article never shadows a verified one (2026-10-16)
            group[key] = old.model_copy(update={
                "resolution_status": ac.resolution_status, "listings": ac.listings,
                "cik": ac.cik, "other_securities": ac.other_securities})
    linked = set(comp) | set(inst) | set(priv) | set(nsec)
    also = {entity_key(a): a for a in prev.also_named} if prev else {}
    for mid in article_mentions:
        if mid not in mentions:
            continue
        m = mentions[mid]
        r = resolutions.get(mid)
        other = AffectedCompany(
            mention_id=mid, name_as_written=m.name_as_written,
            resolution_status=r.status if r else ResolutionStatus.UNRESOLVED,
            listings=r.listings if r else (), cik=r.cik if r else None, role=m.role,
            role_detail=m.role_detail, direction=m.direction,
            recommendation_status=m.recommendation_status, article_id=m.article_id,
            quote=m.quote, other_securities=r.other_securities if r else ())
        if entity_key(other) not in linked:
            also.setdefault(entity_key(other), other)
    for key in linked:
        also.pop(key, None)
    sec = list(prev.sectors) if prev else []
    for s in sectors:
        if s not in sec:
            sec.append(s)
    bk = list(prev.baskets) if prev else []
    bk.extend(baskets)
    return AffectedView(companies=tuple(comp.values()), instruments=tuple(inst.values()),
                        sectors=tuple(sec), baskets=_dedupe(bk),
                        private_or_unlisted=tuple(priv.values()),
                        enrichment=(prev.enrichment if prev else ()) + enrichment,
                        not_securities=tuple(nsec.values()), also_named=tuple(also.values()),
                        sector_exposures=sector_exposures or (prev.sector_exposures if prev
                                                              else ()))


def _verified(c: AffectedCompany) -> bool:
    return any(x.pit_status is PitStatus.VERIFIED for x in c.listings)


def entity_key(c: AffectedCompany) -> str:
    """One named entity across articles: its SEC CIK when resolved, else its normalised name."""
    return f"cik:{c.cik}" if c.cik else "name:" + (norm_name(c.name_as_written)
                                                   or c.name_as_written.lower())


_CONTEXT_DIRECTION = {"potential_beneficiary": Direction.POSITIVE,
                      "potentially_harmed": Direction.NEGATIVE}


_ = (ClaimKind, MentionRole)  # re-exported for callers that classify evidence rows
