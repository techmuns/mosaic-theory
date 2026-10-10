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
from dataclasses import dataclass
from datetime import date
from typing import Any

from vinci.theme_intelligence.schemas import (
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
    label_for,
    norm_name,
    provenance_of,
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
    evidence)."""
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
        label = " — ".join(x for x in (c.scope, c.metric) if x) or c.statement
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
        first_detected=ci.thesis.created_as_of,
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
                           market_risks=_dedupe(risks))

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

    return CardContent(header=header,
                       s01_bottom_line=_dedupe(labelled(s, claims) for s in s01),
                       s02_what_changed=s02,
                       s03_transmission=s03, s04_key_evidence=s04, s05_affected=ci.affected,
                       s06_why_now=s06, s07_what_could_go_wrong=s07, s08_decision=s08,
                       s09_sources=tuple(ci.sources))


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
    d = card.s08_decision
    return card.model_copy(update={
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
                                  for i, s in enumerate(w.market_risks))}),
        "s08_decision": d.model_copy(update={"next_step": fix_sent(d.next_step, "s08.next")}),
    })


_PERCENT_UNITS = frozenset({"%", "percent", "per cent", "pct"})


def unit_shown(value_text: str | None, unit: str | None) -> str:
    """The unit to print after a figure — without what the written value already carries, so
    "~43%" with unit "%" prints "~43%", never "~43% %", and "15–20%" with unit "% QoQ" prints
    "15–20% QoQ" (both observed 2026-10-10). Display only: the card keeps value and unit as
    separate fields."""
    u = (unit or "").strip()
    v = value_text or ""

    def carried(token: str) -> bool:
        if token.lower() in _PERCENT_UNITS:
            return re.search(r"%|percent|per cent", v, re.I) is not None
        return re.search(rf"(?<![A-Za-z]){re.escape(token)}(?![A-Za-z])", v, re.I) is not None

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

_CSS = """
:root{--bg:#fbfaf7;--ink:#1c1b19;--muted:#6b6862;--line:#e3dfd6;--card:#fff;
--obs:#1f6f43;--obs-bg:#e6f3ec;--fc:#0f5f6e;--fc-bg:#e2f2f4;--op:#6b3fa0;--op-bg:#efe8f8;
--inf:#8a5a00;--inf-bg:#fbf0d9;--ext:#1d4f91;--ext-bg:#e4edf9;
--unk:#555;--unk-bg:#ececec;--now:#9b1c1c;--now-bg:#fde8e8;--watch:#8a5a00;--watch-bg:#fbf0d9;
--skip:#555;--skip-bg:#ececec;--block:#9b1c1c}
@media (prefers-color-scheme: dark){:root{--bg:#141412;--ink:#ecebe7;--muted:#a19e97;--line:#2f2d29;
--card:#1c1b19;--obs:#7fd4a4;--obs-bg:#173325;--fc:#8fd6e0;--fc-bg:#123238;--op:#c9a8f0;
--op-bg:#2c1f3d;--inf:#f0c36b;--inf-bg:#3a2d10;--ext:#9cc2f5;
--ext-bg:#172a45;--unk:#c9c6c0;--unk-bg:#2b2a27;--now:#ffb4b4;--now-bg:#4a1717;--watch:#f0c36b;
--watch-bg:#3a2d10;--skip:#c9c6c0;--skip-bg:#2b2a27;--block:#ffb4b4}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:20px 16px 48px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;
margin:0 0 18px}
.hdr .id{font:600 12px/1.2 ui-monospace,Menlo,monospace;color:var(--muted);letter-spacing:.02em}
.hdr h1{font-size:21px;line-height:1.25;margin:4px 0 8px}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;color:var(--muted);font-size:13px}
.dates{color:var(--muted);font-size:13px;margin-top:6px}
.pill{display:inline-block;font:700 12px/1 ui-sans-serif,system-ui;padding:5px 8px;
border-radius:5px;letter-spacing:.03em}
.pill.now{background:var(--now-bg);color:var(--now)}.pill.watch{background:var(--watch-bg);
color:var(--watch)}.pill.skip{background:var(--skip-bg);color:var(--skip)}
.pill.dir{background:var(--unk-bg);color:var(--ink)}.pill.kind{background:var(--op-bg);
color:var(--op)}
.sec{border-top:1px solid var(--line);padding:12px 0 4px}
.sec h2,.sec summary{font:700 13px/1.3 ui-sans-serif,system-ui;letter-spacing:.06em;
text-transform:uppercase;margin:0 0 8px;cursor:pointer}
.sec summary small{font-weight:400;text-transform:none;letter-spacing:0;color:var(--muted)}
details.sec>summary{list-style:none}details.sec>summary::before{content:"▸ ";color:var(--muted)}
details.sec[open]>summary::before{content:"▾ "}
.s{margin:4px 0 8px}.b{display:inline-block;font:700 10px/1 ui-sans-serif,system-ui;
padding:3px 5px;border-radius:4px;margin-right:6px;vertical-align:1px;letter-spacing:.03em}
.b.obs,.b.fact{background:var(--obs-bg);color:var(--obs)}.b.fc{background:var(--fc-bg);
color:var(--fc)}.b.op{background:var(--op-bg);color:var(--op)}
.b.inf{background:var(--inf-bg);color:var(--inf)}
.b.ext{background:var(--ext-bg);color:var(--ext)}.b.unk{background:var(--unk-bg);color:var(--unk)}
.cc{font:600 11px/1 ui-monospace,Menlo,monospace;color:var(--muted)}
.tag{font:600 11px/1.2 ui-sans-serif,system-ui;color:var(--muted);margin-right:6px}
.ref{font:11px ui-monospace,Menlo,monospace;color:var(--muted);text-decoration:none}
table{border-collapse:collapse;width:100%;font-size:13px;margin:4px 0 10px}
th,td{border-bottom:1px solid var(--line);padding:6px 6px;text-align:left;vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.q{color:var(--muted);font-style:italic}.withheld{color:var(--block);font-weight:600}
.note{color:var(--muted);font-size:13px}.sub{font-weight:700;font-size:12px;margin:10px 0 2px;
color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.foot{color:var(--muted);font-size:12px;margin-top:10px}
.statusnote{margin-top:8px;padding:6px 8px;border-radius:5px;background:var(--unk-bg);
font-weight:600;font-size:13px}
.legend{font-size:12px;color:var(--muted);margin:2px 0 10px}
.auditbar{max-width:980px;margin:0 auto;padding:10px 16px 0;font-size:13px;color:var(--muted)}
.aud{display:none}#audit:checked~.wrap .aud,#audit:checked~.auditbar .aud{display:revert}
#audit:checked~.wrap .nonaud{display:none}
a{color:var(--ext)}
@media (max-width:640px){table{display:block;overflow-x:auto}}
@media print{details.sec>*{display:block!important}details.sec>summary::before{content:""}
body{background:#fff}.card{border:0}.aud{display:revert!important}.nonaud{display:none!important}
.auditbar{display:none}}
"""

_BADGE = {Provenance.MEASURED_OBSERVATION: "obs", Provenance.FORECAST: "fc",
          Provenance.SOURCE_OPINION: "op", Provenance.MODEL_INFERENCE: "inf",
          Provenance.EXTERNALLY_VERIFIED: "ext", Provenance.UNKNOWN: "unk",
          Provenance.ARTICLE_FACT: "fact"}
_PILL = {"RESEARCH NOW": "now", "WATCH": "watch", "SKIP": "skip"}
_FOLDED = {"s03_transmission", "s04_key_evidence", "s05_affected", "s07_what_could_go_wrong",
           "s09_sources"}
#: change classes as a reader says them; `novelty_unverified` needs no per-line tag — section 02
#: says once that a new thesis is new TO THE REGISTRY, not necessarily new to the market
_CHANGE_TAG = {ChangeClass.NEW: "New evidence",
               ChangeClass.INDEPENDENT_CONFIRMATION: "Independent confirmation",
               ChangeClass.REPEATED: "Repeats evidence already held",
               ChangeClass.CONTRADICTORY: "Contradicts the thesis",
               ChangeClass.CORRECTION: "Correction", ChangeClass.TIMING_CHANGE: "Timing change",
               ChangeClass.NO_MATERIAL_CHANGE: "No material change",
               ChangeClass.NOVELTY_UNVERIFIED: ""}
LEGEND = ("Labels: MEASURED OBSERVATION — a figure or dated event the source reports · FORECAST "
          "— a projection or estimate in the source · SOURCE OPINION — the publisher's "
          "interpretation or argument, not an established market fact · MODEL INFERENCE — this "
          "tool's reasoning · EXTERNALLY VERIFIED — checked against an independent primary "
          "source. A line citing several claims carries the weakest label among them.")
AUDIT_TOGGLE = ('<input type="checkbox" id="audit" hidden><div class="auditbar">'
                '<label for="audit"><u>Show evidence IDs, engine codes and the decision trace'
                '</u></label> <span class="aud">— audit view on</span></div>')


def e(x: object) -> str:
    return html.escape("" if x is None else str(x))


def origin_label(attributed: str | None) -> str:
    """How a figure's upstream origin reads on a card: the data source the article names, the
    publisher's own analysis, or — when the article attributes nothing — said plainly."""
    if not attributed:
        return "not attributed by the source"
    if attributed.strip().lower() in ("publisher_own", "publisher own"):
        return "publisher's own analysis"
    return attributed


def _once(label: str, note: str) -> str:
    """`LABEL — note`, without repeating a label the note already starts with."""
    return note if note.startswith(label) else f"{label} — {note}"


def clip(text: str, n: int) -> str:
    """A shortened display line PRINTS ITS OWN TRUNCATION — the full value stays in the JSON."""
    if len(text) <= n:
        return text
    return f"{text[:n].rstrip()}… [+{len(text) - n} chars — full text in the JSON export]"


def first_detected_line(h: CardHeader) -> str:
    """Article date and registry date, kept apart — new to the registry is not new to market."""
    art = (h.latest_article_date.isoformat() if h.latest_article_date else "UNKNOWN")
    det = h.first_detected.isoformat() if h.first_detected else "UNKNOWN"
    return (f"Article date {art} · first detected by the registry {det} (new to the registry "
            f"does not mean new to the market) · last material update "
            f"{h.last_material_update.isoformat()}")


@dataclass
class RenderContext:
    history: list[ThesisVersion]
    attributions: list[tuple[str, str, str]]  # (article id, class, note) — non-material
    blocked: dict[str, str]  # sentence id -> reason
    articles: dict[str, Article]
    generated_note: str
    status_note: str | None = None  # the CURRENT registry status, when it moved after this version


def _refs(ids: Iterable[str]) -> str:
    ids = list(ids)
    if not ids:
        return ""
    return (' <span class="aud">' + " ".join(f'<a class="ref" href="#{e(c)}">{e(c)}</a>'
                                             for c in ids) + "</span>")


def _sent(s: CardSentence, sid: str, rc: RenderContext) -> str:
    if sid in rc.blocked:
        return (f'<div class="s"><span class="withheld">WITHHELD — failed source verification'
                f'</span><span class="aud"> {e(rc.blocked[sid])}</span><details><summary '
                f'class="note">audit text</summary><span class="q">{e(s.text)}</span></details>'
                f'</div>')
    return (f'<div class="s"><span class="b {_BADGE[s.provenance]}">{e(s.provenance.value)}'
            f'</span>{e(s.text)}{_refs(s.claim_ids)}</div>')


def _section(fid: str, title: str, body: str, *, print_mode: bool, summary: str = "") -> str:
    if fid in _FOLDED:
        op = " open" if print_mode else ""
        small = f" <small>— {e(summary)}</small>" if summary else ""
        return (f'<details class="sec" data-field="{fid}"{op}><summary>{e(title)}{small}'
                f'</summary>{body}</details>')
    return f'<section class="sec" data-field="{fid}"><h2>{e(title)}</h2>{body}</section>'


def _listing_text(ls: Iterable[Listing]) -> str:
    return ", ".join(f"{x.ticker}" + (f" ({x.exchange})" if x.exchange else "") for x in ls)


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
            reading = (f"<td><span class=\"b {_BADGE[label]}\">{e(label.value)}</span>"
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
    return ("<table>" + head + "".join(rows) + "</table>") if rows else \
        '<div class="note">None named.</div>'


def render_html(card: CardContent, rc: RenderContext, *, print_mode: bool = False) -> str:
    h = card.header
    parts: list[str] = []
    pill = _PILL.get(h.research_action.value, "skip")
    kind = (f'<span class="pill kind">{e(KIND_LABEL[h.kind])}</span>'
            if h.kind is ThesisKind.MARKET_REGIME else "")
    parts.append(
        f'<div class="hdr"><div class="id aud">{e(h.thesis_id)} · {e(" › ".join(h.ancestry))}'
        f'</div><h1>{e(h.title)}</h1><div class="meta"><span class="pill {pill}">'
        f'{e(h.research_action.value)}</span><span class="pill dir">Evidence: '
        f'{e(h.evidence_direction.value)}</span>{kind}<span>{e(h.sector)}</span>'
        f'<span>{e(h.region)}</span><span>Horizon: {e(h.horizon)}</span>'
        + (f'<span>Status: {e(h.status.value)}</span>' if h.status.value != "ACTIVE" else "")
        + f'</div><div class="dates">{e(first_detected_line(h))}</div>'
        + (f'<div class="statusnote">{e(rc.status_note)}</div>' if rc.status_note else "")
        + f'<div class="legend">{e(LEGEND)}</div></div>')
    bodies: dict[str, str] = {}
    summaries: dict[str, str] = {}
    bodies["s01_bottom_line"] = "".join(_sent(s, f"s01.{i}", rc)
                                        for i, s in enumerate(card.s01_bottom_line))
    wc = card.s02_what_changed

    def item(i: int, it: ChangeItem) -> str:
        tag = _CHANGE_TAG.get(it.change_class, it.change_class.value)
        body = (f'<span class="withheld">WITHHELD — failed source verification</span>'
                f'<span class="aud"> {e(rc.blocked[f"s02.{i}"])}</span>'
                if f"s02.{i}" in rc.blocked else e(it.text))
        return ('<div class="s">' + (f'<span class="tag">{e(tag)}</span>' if tag else "")
                + f'<span class="b {_BADGE[it.provenance]}">{e(it.provenance.value)}</span>'
                + body
                + (f' <span class="note">(article date {e(it.original_date)}'
                   + (f"; period {e(it.period)}" if it.period else "") + ")</span>"
                   if it.original_date else "")
                + f'<span class="aud"> <span class="cc">[{e(it.change_class.value)}]</span>'
                  f'</span>{_refs(it.claim_ids)}</div>')
    first = [item(i, it) for i, it in enumerate(wc.items)]
    shown, rest = first[:3], first[3:]
    bodies["s02_what_changed"] = (
        f'<div class="note">{e(wc.vs_prior)}</div>'
        f'<div class="note aud">novelty: {e(wc.novelty)}</div>' + "".join(shown)
        + (('<details' + (" open" if print_mode else "") + f'><summary class="note">show the '
            f'other {len(rest)} of {len(first)}</summary>' + "".join(rest) + "</details>")
           if rest else ""))
    bodies["s03_transmission"] = "".join(
        f'<div class="s"><span class="tag">{e(STEP_LABEL.get(st.step, st.step))}</span>'
        + _sent(CardSentence(text=st.text, provenance=st.provenance, claim_ids=st.claim_ids),
                f"s03.{i}", rc)[len('<div class="s">'):]
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
              f'<span class="ref">{e(r.article_id)} {e(r.block_id)}</span><div class="cc aud">'
              f'{e(r.claim_id)} · {e(r.role.value)} · {e(r.change_class.value)}</div></td></tr>')
    bodies["s04_key_evidence"] = (
        f'<div class="note">{len(card.s04_key_evidence)} evidence row(s); every figure links to '
        f'its verbatim source span. Figures repeating one origin are one row.</div>'
        "<table><tr><th>Evidence</th><th>Value</th><th>Period / as-of</th><th>Type</th>"
        "<th>Upstream origin</th><th>Source passage</th></tr>" + "".join(rows) + "</table>")
    summaries["s04_key_evidence"] = f"{len(card.s04_key_evidence)} evidence row(s)"
    av = card.s05_affected
    sector_rows = "".join(
        f'<div class="s"><span class="b {_BADGE[s.provenance]}">{e(s.provenance.value)}</span>'
        f'<b>{e(s.name)}</b> — {e(s.direction.value)} <span class="q">“{e(s.quote)}”</span>'
        f'{_refs(s.claim_ids)}</div>' for s in av.sector_exposures)
    bodies["s05_affected"] = (
        '<div class="sub">Sectors / themes the source names as exposed</div>'
        + (sector_rows or '<div class="note">None named by the source.</div>')
        + '<div class="sub">Stock exposures of this thesis (source-named companies)</div>'
        + _company_rows(av.companies, exposures=True)
        + '<div class="sub">Named instruments / indices</div>' + _company_rows(av.instruments)
        + '<div class="sub">Private or unlisted (stay private)</div>'
        + _company_rows(av.private_or_unlisted)
        + '<div class="sub">Named, not securities (products, baskets, agencies)</div>'
        + _company_rows(av.not_securities)
        + '<div class="sub">Also named in the source — mentions, NOT exposures of this thesis'
          '</div>' + _company_rows(av.also_named)
        + '<div class="sub">Sector labels</div><div class="s">' + e(", ".join(av.sectors) or "—")
        + "</div>" + '<div class="sub">Cited baskets (members NOT named by the source)</div>'
        + ("".join(_sent(s, f"s05.b{i}", rc) for i, s in enumerate(av.baskets)) or
           '<div class="note">None.</div>')
        + '<div class="sub">Enrichment — EXTERNAL HYPOTHESES, not named by the source</div>'
        + ("".join(f'<div class="s"><span class="b unk">{e(x.label)}</span>{e(x.name)} — '
                   f'{e(x.rationale)}</div>' for x in av.enrichment)
           or '<div class="note">None recorded. Unnamed companies are never added to the '
              'source lists above.</div>'))
    summaries["s05_affected"] = (f"{len(av.sector_exposures)} sector(s) · {len(av.companies)} "
                                 f"company exposure(s) · {len(av.also_named)} other mention(s)")
    wn = card.s06_why_now
    bodies["s06_why_now"] = (
        '<div class="sub">Near term (2-4 quarters)</div>'
        + "".join(_sent(s, f"s06.{i}", rc) for i, s in enumerate(wn.near_term))
        + '<div class="sub">Longer-term / structural (kept separate)</div>'
        + "".join(_sent(s, f"s06.{len(wn.near_term) + i}", rc)
                  for i, s in enumerate(wn.structural))
        + f'<div class="sub">Catalyst / repricing window</div><div class="s">'
          f'{e(wn.catalyst_window)}</div><div class="sub">Consensus / valuation</div>'
          f'<div class="s"><span class="b unk">NOT ASSESSED</span>'
          f'{e(_once("NOT_ASSESSED", wn.valuation_status)[len("NOT_ASSESSED — "):])}</div>')
    w = card.s07_what_could_go_wrong
    n0, n1 = len(w.counter_evidence), len(w.alternative_mechanisms)
    bodies["s07_what_could_go_wrong"] = (
        '<div class="sub">Strongest counter-evidence in the sources</div>'
        + ("".join(_sent(s, f"s07.{i}", rc) for i, s in enumerate(w.counter_evidence))
           or '<div class="note">None in the sources so far.</div>')
        + '<div class="sub">Alternative mechanisms / competing hypotheses</div>'
        + "".join(_sent(s, f"s07.{n0 + i}", rc) for i, s in enumerate(w.alternative_mechanisms))
        + '<div class="sub">Market-level risks (kept as risks, not theses)</div>'
        + ("".join(_sent(s, f"s07.{n0 + n1 + i}", rc) for i, s in enumerate(w.market_risks))
           or '<div class="note">None recorded.</div>')
        + '<div class="sub">Observable disconfirming signals</div>'
        + "".join(_sent(s, "-", rc) for s in w.disconfirming_observables)
        + '<div class="sub">Unknowns</div>'
        + "".join(_sent(s, "-", rc) for s in w.unknowns))
    summaries["s07_what_could_go_wrong"] = (f"{len(w.counter_evidence)} counter-evidence · "
                                            f"{len(w.alternative_mechanisms)} alternatives · "
                                            f"{len(w.market_risks)} market risk(s)")
    d = card.s08_decision
    bodies["s08_decision"] = (
        f'<div class="s"><span class="pill {_PILL.get(d.research_action.value, "skip")}">'
        f'{e(d.research_action.value)}</span> <span class="note">research attention only — this '
        f'card never directs a purchase or sale</span></div>'
        '<div class="sub">Next investigable step</div>' + _sent(d.next_step, "s08.next", rc)
        + '<div class="sub">Would raise priority</div>'
        + "".join(_sent(s, "-", rc) for s in d.raise_priority_if)
        + '<div class="sub">Would lower priority</div>'
        + "".join(_sent(s, "-", rc) for s in d.lower_priority_if)
        + f'<div class="sub">Investment readiness</div><div class="s">'
          f'{e(_once(d.investment_readiness.value, d.readiness_note))}</div>'
          '<div class="aud"><div class="sub">Decision trace (deterministic rules)</div>'
        + "".join(f'<div class="s cc">{e(t)}</div>' for t in d.rule_trace) + "</div>")
    src_rows = "".join(
        f"<tr><td><a href=\"{e(s.url)}\">{e(s.title or 'title UNKNOWN')}</a>"
        f"<div class=note>{e(s.article_class.value.replace('_', ' '))} · retrieval "
        f"{e(s.retrieval_state.value)}</div><div class=\"cc aud\">{e(s.article_id)}</div></td>"
        f"<td>{e('; '.join(s.authors) if s.authors else 'UNKNOWN')}</td><td>{e(s.publisher)}</td>"
        f"<td>{e(s.published_at.date().isoformat() if s.published_at else 'UNKNOWN')}</td>"
        f"<td>{e(', '.join(s.upstream_origins) or '—')}</td><td>"
        f"{e(_CHANGE_TAG.get(s.contribution) or 'Initial record')}"
        f"<div class=\"note aud\">{e(s.contribution.value)} · {e(len(s.claim_ids))} claim "
        f"ref(s)</div></td></tr>"
        for s in card.s09_sources)
    hist_rows = "".join(
        f"<tr><td>v{v.version}</td><td>{e(v.as_of.isoformat())}</td>"
        f"<td>{e(v.priority.research_action.value)}</td><td>{e(v.evidence_direction.value)}</td>"
        f"<td>{e(v.change_summary)}<div class=\"note aud\">{e(v.priority.change_reason)}</div>"
        + "".join(f'<div class="cc aud">{e(dd.field_id)}: {e(dd.change_class.value)} — '
                  f"{e(clip(dd.new or '', 140))}</div>" for dd in v.diffs)
        + "</td></tr>" for v in rc.history)
    attr = "".join(f'<div class="s cc">{e(a)} — {e(c)}: {e(n)}</div>'
                   for a, c, n in rc.attributions)
    bodies["s09_sources"] = (
        "<table><tr><th>Source</th><th>Author(s)</th><th>Publisher</th><th>Article date</th>"
        "<th>Upstream origin(s)</th><th>Contribution</th></tr>" + src_rows + "</table>"
        '<div class="sub">Version history (immutable)</div><table><tr><th>Ver</th><th>As of</th>'
        "<th>Action</th><th>Evidence</th><th>Why it changed</th></tr>" + hist_rows + "</table>"
        + ('<div class="sub">Attributions without a new version</div>' + attr if attr else ""))
    summaries["s09_sources"] = (f"{len(card.s09_sources)} source(s) · {len(rc.history)} "
                                f"version(s)")
    for fid, title in SECTION_IDS:
        parts.append(_section(fid, title, bodies[fid], print_mode=print_mode,
                              summary=summaries.get(fid, "")))
    parts.append(f'<div class="foot">{e(rc.generated_note)}</div>')
    script = ("<script>window.addEventListener('beforeprint',()=>document.querySelectorAll("
              "'details').forEach(d=>d.open=true));</script>")
    body = "".join(parts)
    if print_mode:  # the print file is the COMPLETE record: every nested audit toggle opens too
        body = body.replace("<details>", "<details open>")
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
            "content='width=device-width,initial-scale=1'><title>" + e(h.title)
            + "</title><style>" + _CSS + "</style></head><body>" + AUDIT_TOGGLE
            + "<div class=wrap><article class=card>" + body + "</article></div>" + script
            + "</body></html>")


def _md_sents(ss: Iterable[CardSentence], prefix: str, rc: RenderContext,
              start: int = 0) -> list[str]:
    out = []
    for i, s in enumerate(ss, start):
        sid = f"{prefix}.{i}"
        refs = (" [" + ", ".join(s.claim_ids) + "]") if s.claim_ids else ""
        if sid in rc.blocked:
            out.append(f"- **WITHHELD — failed source verification:** {rc.blocked[sid]}")
        else:
            out.append(f"- **{s.provenance.value}:** {s.text}{refs}")
    return out


def render_markdown(card: CardContent, rc: RenderContext) -> str:
    h = card.header
    md = [f"# {h.title}", "",
         f"**{h.research_action.value}** · {KIND_LABEL[h.kind]} · evidence "
         f"{h.evidence_direction.value} · {h.sector} · {h.region} · horizon {h.horizon} · status "
         f"{h.status.value}", "", first_detected_line(h), "",
         f"`{h.thesis_id}` · {' › '.join(h.ancestry)}", "", f"_{LEGEND}_", ""]
    if rc.status_note:
        md += [f"> **{rc.status_note}**", ""]
    titles = dict(SECTION_IDS)
    md += [f"## {titles['s01_bottom_line']}"] + _md_sents(card.s01_bottom_line, "s01", rc) + [""]
    wc = card.s02_what_changed
    md += [f"## {titles['s02_what_changed']}", f"- {wc.vs_prior}", f"- novelty: {wc.novelty}"]
    for i, it in enumerate(wc.items):
        txt = (f"WITHHELD — {rc.blocked[f's02.{i}']}" if f"s02.{i}" in rc.blocked else it.text)
        tag = _CHANGE_TAG.get(it.change_class, it.change_class.value)
        md.append("- " + (f"[{tag}] " if tag else "") + f"**{it.provenance.value}:** {txt}"
                 + (f" (article date {it.original_date}" + (f"; period {it.period}"
                                                              if it.period else "") + ")"
                    if it.original_date else "")
                 + (" [" + ", ".join(it.claim_ids) + "]" if it.claim_ids else ""))
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
    av = card.s05_affected
    md += ["", f"## {titles['s05_affected']}", "**Sectors / themes the source names as exposed:**"]
    md += [f"- **{s.provenance.value}:** {s.name} — {s.direction.value} — “{s.quote}”"
           + (" [" + ", ".join(s.claim_ids) + "]" if s.claim_ids else "")
           for s in av.sector_exposures] or ["- none named by the source"]
    # (label, group) PAIRS — never `grp is av.instruments`: every empty tuple is the same object,
    # so identity matched one empty group to another's heading
    for label, grp, expo in (("Stock exposures of this thesis", av.companies, True),
                             ("Named instruments / indices", av.instruments, False),
                             ("Private or unlisted", av.private_or_unlisted, False),
                             ("Named, not securities (products, baskets, agencies)",
                              av.not_securities, False),
                             ("Also named in the source — mentions, NOT exposures of this thesis",
                              av.also_named, False)):
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
    md.append("**Enrichment — external hypotheses, not named by the source:** "
             + ("; ".join(f"{x.name} ({x.rationale})" for x in av.enrichment) or "none"))
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
        md.append(f"- [{s.title or 'title UNKNOWN'}]({s.url}) — "
                 f"{'; '.join(s.authors) if s.authors else 'author UNKNOWN'} — {s.publisher} — "
                 f"article date {art_date}"
                 f" — {s.article_class.value} — retrieval {s.retrieval_state.value} — origins: "
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
    return "\n".join(md)


def render_json(card: CardContent, rc: RenderContext) -> dict[str, Any]:
    return {
        "status_note": rc.status_note,
        "card": json.loads(card.model_dump_json()),
        "section_order": [fid for fid, _ in SECTION_IDS],
        "history": [json.loads(v.model_dump_json()) for v in rc.history],
        "attributions_without_version": [
            {"article_id": a, "contribution": c, "note": n} for a, c, n in rc.attributions],
        "withheld_sentences": rc.blocked,
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
    from vinci.theme_intelligence.schemas import ResolutionStatus

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
        group.setdefault(key, ac)
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


def entity_key(c: AffectedCompany) -> str:
    """One named entity across articles: its SEC CIK when resolved, else its normalised name."""
    return f"cik:{c.cik}" if c.cik else "name:" + (norm_name(c.name_as_written)
                                                   or c.name_as_written.lower())


_CONTEXT_DIRECTION = {"potential_beneficiary": Direction.POSITIVE,
                      "potentially_harmed": Direction.NEGATIVE}


_ = (ClaimKind, MentionRole)  # re-exported for callers that classify evidence rows
