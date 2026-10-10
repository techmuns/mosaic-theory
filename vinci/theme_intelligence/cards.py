"""The universal nine-section Living Thesis Card — composed from records, rendered three ways.

COMPOSE. `compose_card` builds a `CardContent` from persisted records only: the thesis key, the
verified hypothesis view of the contributing article(s), verified claims, source-named mentions
and their SEC resolutions, the deterministic priority, and the contribution history. An update
overlays the new article on the PRIOR version's content (which stays immutable in its own row).
Nothing on a card is hand-written: every fact line cites claim ids; inference lines say so.

RENDER. HTML (web), HTML (print: every section expanded), Markdown and JSON all walk the SAME
`CardContent`, in the SAME fixed order 01→09, with the same field ids — so the four cannot
disagree, and a cross-consistency test pins it. The web view keeps the header and 01 / 02 / 06 / 08
open and folds 03-05 / 07 / 09 into <details> IN PLACE (the order never changes); the print view
opens them all, so the printed report carries every field with no silent loss.

A sentence that failed verification (a BLOCK issue) is never rendered as a fact: it is shown as
WITHHELD with the reason, its text kept only behind a disclosure for audit.
"""

from __future__ import annotations

import html
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any

from vinci.theme_intelligence.schemas import (
    SECTION_IDS,
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
    Provenance,
    ResearchPriority,
    SourceRef,
    Thesis,
    ThesisClaimLink,
    ThesisVersion,
    TransmissionStep,
    WhatChanged,
    WhatCouldGoWrong,
    WhyNow,
)
from vinci.theme_intelligence.verify import VerifiedHypothesis, norm_name, provenance_of

HORIZON_LABEL = {Horizon.NEXT_2_4_QUARTERS: "Next 2-4 quarters",
                 Horizon.LONGER_TERM: "Longer term (beyond 4 quarters)",
                 Horizon.UNCLEAR: "Unclear in the source"}
_EARNINGS_UNKNOWN = ("UNKNOWN — the source does not quantify an effect on listed-company "
                     "earnings; any earnings impact is a hypothesis to test, not a finding")
_NO_CATALYST = "UNKNOWN — the source names no dated catalyst or earnings window"
STEP_ORDER = ("industry_shift", "volumes", "pricing", "costs", "margins", "cash_flow",
              "listed_earnings")


def _cs(text: str, prov: Provenance, ids: Iterable[str] = ()) -> CardSentence:
    return CardSentence(text=text.strip(), provenance=prov, claim_ids=tuple(dict.fromkeys(ids)))


#: SYSTEM-LABEL brackets: everything inside ⟨…⟩ is composed by this code (figure labels, an
#: update's date and publisher), never asserted by the source. The number check in `verify.py`
#: ignores what sits inside them.
LABEL_OPEN, LABEL_CLOSE = "⟨", "⟩"
_FIGURES = f"{LABEL_OPEN}cited figures:"


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

    # header ------------------------------------------------------------------------------------
    horizon = (HORIZON_LABEL[h.raw.horizon] if h else prev.header.horizon if prev else
               HORIZON_LABEL[Horizon.UNCLEAR])
    header = CardHeader(
        thesis_id=ci.thesis.thesis_id, title=ci.thesis.title, sector=ci.thesis.sector,
        region=ci.thesis.region, research_action=pr.research_action,
        evidence_direction=ci.evidence_direction, horizon=horizon,
        last_material_update=ci.last_material_update, status=ci.thesis.status,
        ancestry=ci.thesis.ancestry)

    # 01 bottom line ----------------------------------------------------------------------------
    s01: list[CardSentence] = []
    if prev is not None:
        s01.extend(s for s in prev.s01_bottom_line[:2])
    if h is not None:
        fact = _cs(h.raw.bottom_line_fact.text,
                   provenance_of(h.raw.bottom_line_fact, h.bottom_fact_claims),
                   h.bottom_fact_claims)
        if prev is None:
            s01.append(fact)
            s01.append(_cs(h.raw.bottom_line_inference.text, Provenance.MODEL_INFERENCE))
        else:
            when = (ci.article.published_at.date().isoformat()
                    if ci.article and ci.article.published_at else "date UNKNOWN")
            pub = ci.article.publisher if ci.article else "source"
            # the update's date and publisher are composed METADATA, so they sit inside the
            # system-label brackets — never read as figures the sentence asserts
            s01.append(_cs(f"{LABEL_OPEN}update {when} · {pub}{LABEL_CLOSE} {fact.text}",
                           fact.provenance,
                           fact.claim_ids))

    # 02 what changed ---------------------------------------------------------------------------
    s02 = WhatChanged(items=tuple(_labelled_item(it, claims) for it in ci.change_items),
                      vs_prior=ci.vs_prior, novelty=ci.novelty)

    # 03 transmission ---------------------------------------------------------------------------
    steps: dict[str, TransmissionStep] = {s.step: s for s in (prev.s03_transmission if prev else ())
                                          if s.provenance is not Provenance.UNKNOWN}
    if h is not None:
        for st in h.raw.transmission_chain:
            ids = [h.claim_map[c] for c in st.claim_ids if c in h.claim_map]
            prov = Provenance.ARTICLE_FACT if (st.provenance == "article_fact" and ids) \
                else Provenance.MODEL_INFERENCE
            new = TransmissionStep(step=st.step, text=st.text, provenance=prov,
                                   claim_ids=tuple(ids))
            old = steps.get(st.step)
            if old is None or (old.provenance is Provenance.MODEL_INFERENCE
                               and prov is Provenance.ARTICLE_FACT):
                steps[st.step] = new
    if "listed_earnings" not in steps:
        steps["listed_earnings"] = TransmissionStep(step="listed_earnings",
                                                    text=_EARNINGS_UNKNOWN,
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
                               provenance_of(h.raw.near_term_view, ids), ids))
        for cid in h.dislocation:
            c = claims.get(cid)
            if c is not None:
                near.append(_cs(f"Dislocation evidence: {c.statement}", Provenance.ARTICLE_FACT,
                                [cid]))
        if h.raw.structural_view:
            ids = [h.claim_map[c] for c in h.raw.structural_view.claim_ids if c in h.claim_map]
            structural.insert(0, _cs(h.raw.structural_view.text,
                                     provenance_of(h.raw.structural_view, ids), ids))
        if h.raw.catalyst.window_text:
            dated = [c for c in h.catalyst if c in claims and claims[c].kind is ClaimKind.EVENT
                     and (claims[c].period or claims[c].measured_as_of)]
            prov = (Provenance.ARTICLE_FACT if h.raw.catalyst.provenance == "article_fact"
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
        counter.append(_cs(c.statement, Provenance.ARTICLE_FACT, [c.claim_id]))
    if h is not None:
        for t in h.raw.opposing_explanations:
            ids = [h.claim_map[x] for x in t.claim_ids if x in h.claim_map]
            alts.append(_cs(t.text, provenance_of(t, ids), ids))
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
                    f"{r.label}: {r.value_text or ''} {r.unit or ''}".strip(), (i,)))
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
--fact:#1f6f43;--fact-bg:#e6f3ec;--inf:#8a5a00;--inf-bg:#fbf0d9;--ext:#1d4f91;--ext-bg:#e4edf9;
--unk:#555;--unk-bg:#ececec;--now:#9b1c1c;--now-bg:#fde8e8;--watch:#8a5a00;--watch-bg:#fbf0d9;
--skip:#555;--skip-bg:#ececec;--block:#9b1c1c}
@media (prefers-color-scheme: dark){:root{--bg:#141412;--ink:#ecebe7;--muted:#a19e97;--line:#2f2d29;
--card:#1c1b19;--fact:#7fd4a4;--fact-bg:#173325;--inf:#f0c36b;--inf-bg:#3a2d10;--ext:#9cc2f5;
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
.pill{display:inline-block;font:700 12px/1 ui-sans-serif,system-ui;padding:5px 8px;
border-radius:5px;letter-spacing:.03em}
.pill.now{background:var(--now-bg);color:var(--now)}.pill.watch{background:var(--watch-bg);
color:var(--watch)}.pill.skip{background:var(--skip-bg);color:var(--skip)}
.pill.dir{background:var(--unk-bg);color:var(--ink)}
.sec{border-top:1px solid var(--line);padding:12px 0 4px}
.sec h2,.sec summary{font:700 13px/1.3 ui-sans-serif,system-ui;letter-spacing:.06em;
text-transform:uppercase;margin:0 0 8px;cursor:pointer}
details.sec>summary{list-style:none}details.sec>summary::before{content:"▸ ";color:var(--muted)}
details.sec[open]>summary::before{content:"▾ "}
.s{margin:4px 0 8px}.b{display:inline-block;font:700 10px/1 ui-sans-serif,system-ui;
padding:3px 5px;border-radius:4px;margin-right:6px;vertical-align:1px;letter-spacing:.03em}
.b.fact{background:var(--fact-bg);color:var(--fact)}.b.inf{background:var(--inf-bg);color:var(--inf)}
.b.ext{background:var(--ext-bg);color:var(--ext)}.b.unk{background:var(--unk-bg);color:var(--unk)}
.cc{font:600 11px/1 ui-monospace,Menlo,monospace;color:var(--muted)}
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
a{color:var(--ext)}
@media (max-width:640px){table{display:block;overflow-x:auto}}
@media print{details.sec>*{display:block!important}details.sec>summary::before{content:""}
body{background:#fff}.card{border:0}}
"""

_BADGE = {Provenance.ARTICLE_FACT: "fact", Provenance.MODEL_INFERENCE: "inf",
          Provenance.EXTERNALLY_VERIFIED: "ext", Provenance.UNKNOWN: "unk"}
_PILL = {"RESEARCH NOW": "now", "WATCH": "watch", "SKIP": "skip"}
_FOLDED = {"s03_transmission", "s04_key_evidence", "s05_affected", "s07_what_could_go_wrong",
           "s09_sources"}


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


@dataclass
class RenderContext:
    history: list[ThesisVersion]
    attributions: list[tuple[str, str, str]]  # (article id, class, note) — non-material
    blocked: dict[str, str]  # sentence id -> reason
    articles: dict[str, Article]
    generated_note: str
    status_note: str | None = None  # the CURRENT registry status, when it moved after this version


def _sent(s: CardSentence, sid: str, rc: RenderContext) -> str:
    refs = " ".join(f'<a class="ref" href="#{e(c)}">{e(c)}</a>' for c in s.claim_ids)
    if sid in rc.blocked:
        return (f'<div class="s"><span class="withheld">WITHHELD — failed source verification: '
                f'{e(rc.blocked[sid])}</span><details><summary class="note">audit text</summary>'
                f'<span class="q">{e(s.text)}</span></details></div>')
    return (f'<div class="s"><span class="b {_BADGE[s.provenance]}">{e(s.provenance.value)}'
            f'</span>{e(s.text)} {refs}</div>')


def _section(fid: str, title: str, body: str, *, print_mode: bool) -> str:
    if fid in _FOLDED:
        op = " open" if print_mode else ""
        return (f'<details class="sec" data-field="{fid}"{op}><summary>{e(title)}</summary>'
                f'{body}</details>')
    return f'<section class="sec" data-field="{fid}"><h2>{e(title)}</h2>{body}</section>'


def _company_rows(cs: Iterable[AffectedCompany]) -> str:
    rows = []
    for c in cs:
        lst = ", ".join(f"{x.ticker}" + (f" ({x.exchange})" if x.exchange else "")
                        for x in c.listings) or "—"
        rows.append(f"<tr><td>{e(c.name_as_written)}</td><td>{e(lst)}</td>"
                    f"<td>{e(c.resolution_status.value)}</td><td>{e(c.role.value)}"
                    f"<div class=note>{e(c.role_detail)}</div></td><td>{e(c.direction.value)}</td>"
                    f"<td>{e(c.recommendation_status.value)}</td></tr>")
    return ("<table><tr><th>Named in source</th><th>Listing (SEC-verified)</th><th>Status</th>"
            "<th>Stated role</th><th>Direction</th><th>Recommendation status</th></tr>"
            + "".join(rows) + "</table>") if rows else '<div class="note">None named.</div>'


def render_html(card: CardContent, rc: RenderContext, *, print_mode: bool = False) -> str:
    h = card.header
    parts: list[str] = []
    pill = _PILL.get(h.research_action.value, "skip")
    parts.append(
        f'<div class="hdr"><div class="id">{e(h.thesis_id)} · {e(" › ".join(h.ancestry))}</div>'
        f'<h1>{e(h.title)}</h1><div class="meta"><span class="pill {pill}">'
        f'{e(h.research_action.value)}</span><span class="pill dir">Evidence: '
        f'{e(h.evidence_direction.value)}</span><span>{e(h.sector)}</span><span>{e(h.region)}'
        f'</span><span>Horizon: {e(h.horizon)}</span><span>Last material update: '
        f'{e(h.last_material_update.isoformat())}</span><span>Status: {e(h.status.value)}</span>'
        f'</div>' + (f'<div class="statusnote">{e(rc.status_note)}</div>' if rc.status_note
                     else "") + '</div>')
    bodies: dict[str, str] = {}
    bodies["s01_bottom_line"] = "".join(_sent(s, f"s01.{i}", rc)
                                        for i, s in enumerate(card.s01_bottom_line))
    wc = card.s02_what_changed
    items = "".join(
        f'<div class="s"><span class="cc">[{e(it.change_class.value)}]</span> '
        f'<span class="b {_BADGE[it.provenance]}">{e(it.provenance.value)}</span>'
        + (f'<span class="withheld">WITHHELD — {e(rc.blocked[f"s02.{i}"])}</span>'
           if f"s02.{i}" in rc.blocked else e(it.text))
        + (f' <span class="note">(source date {e(it.original_date)}'
           + (f"; period {e(it.period)}" if it.period else "") + ")</span>"
           if it.original_date else "")
        + " " + " ".join(f'<a class="ref" href="#{e(c)}">{e(c)}</a>' for c in it.claim_ids)
        + "</div>" for i, it in enumerate(wc.items))
    bodies["s02_what_changed"] = (f'<div class="note">vs prior: {e(wc.vs_prior)}</div>'
                                  f'<div class="note">novelty: {e(wc.novelty)}</div>{items}')
    bodies["s03_transmission"] = "".join(
        f'<div class="s"><span class="cc">{e(st.step)}</span> '
        + _sent(CardSentence(text=st.text, provenance=st.provenance, claim_ids=st.claim_ids),
                f"s03.{i}", rc)[len('<div class="s">'):]
        for i, st in enumerate(card.s03_transmission))
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
            f'{also}</td><td><b>{e(r.value_text or "—")}</b> {e(r.unit or "")}'
            + (f"<div class=note>{e(r.comparator)}</div>" if r.comparator else "")
            + f'</td><td>{e(r.period or "—")}<div class=note>as of {e(asof)}</div></td>'
              f'<td>{e(" · ".join(flags))}</td><td>{e(r.origin or "—")}</td><td>'
              f'<span class="ref">{e(r.article_id)} {e(r.block_id)}</span><div class=cc>'
              f'{e(r.role.value)} · {e(r.change_class.value)}</div></td></tr>')
    bodies["s04_key_evidence"] = (
        f'<div class="note">{len(card.s04_key_evidence)} evidence row(s); every figure links to '
        f'its verbatim source span. Figures repeating one origin are one row.</div>'
        "<table><tr><th>Evidence</th><th>Value</th><th>Period / as-of</th><th>Type</th>"
        "<th>Upstream origin</th><th>Anchor</th></tr>" + "".join(rows) + "</table>")
    av = card.s05_affected
    bodies["s05_affected"] = (
        '<div class="sub">Source-explicit companies</div>' + _company_rows(av.companies)
        + '<div class="sub">Named instruments / indices</div>' + _company_rows(av.instruments)
        + '<div class="sub">Private or unlisted (stay private)</div>'
        + _company_rows(av.private_or_unlisted)
        + '<div class="sub">Named, not securities (products, baskets, agencies)</div>'
        + _company_rows(av.not_securities)
        + '<div class="sub">Also named in the source — NOT exposures of this thesis</div>'
        + _company_rows(av.also_named)
        + '<div class="sub">Sectors</div><div class="s">' + e(", ".join(av.sectors) or "—")
        + "</div>" + '<div class="sub">Cited baskets (members NOT named by the source)</div>'
        + ("".join(_sent(s, f"s05.b{i}", rc) for i, s in enumerate(av.baskets)) or
           '<div class="note">None.</div>')
        + '<div class="sub">Enrichment — EXTERNAL HYPOTHESES, not named by the source</div>'
        + ("".join(f'<div class="s"><span class="b unk">{e(x.label)}</span>{e(x.name)} — '
                   f'{e(x.rationale)}</div>' for x in av.enrichment)
           or '<div class="note">None recorded. Unnamed companies are never added to the '
              'source lists above.</div>'))
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
          '<div class="sub">Decision trace (deterministic rules)</div>'
        + "".join(f'<div class="s cc">{e(t)}</div>' for t in d.rule_trace))
    src_rows = "".join(
        f"<tr><td><a href=\"{e(s.url)}\">{e(s.title or 'title UNKNOWN')}</a>"
        f"<div class=note>{e(s.article_id)} · {e(s.article_class.value)} · retrieval "
        f"{e(s.retrieval_state.value)}</div></td><td>"
        f"{e('; '.join(s.authors) if s.authors else 'UNKNOWN')}</td><td>{e(s.publisher)}</td>"
        f"<td>{e(s.published_at.isoformat() if s.published_at else 'UNKNOWN')}</td>"
        f"<td>{e(', '.join(s.upstream_origins) or '—')}</td><td>{e(s.contribution.value)}"
        f"<div class=note>{e(len(s.claim_ids))} claim ref(s)</div></td></tr>"
        for s in card.s09_sources)
    hist_rows = "".join(
        f"<tr><td>v{v.version}</td><td>{e(v.as_of.isoformat())}</td>"
        f"<td>{e(v.priority.research_action.value)}</td><td>{e(v.evidence_direction.value)}</td>"
        f"<td>{e(v.change_summary)}<div class=note>{e(v.priority.change_reason)}</div>"
        + "".join(f"<div class=cc>{e(dd.field_id)}: {e(dd.change_class.value)} — "
                  f"{e(clip(dd.new or '', 140))}</div>" for dd in v.diffs)
        + "</td></tr>" for v in rc.history)
    attr = "".join(f'<div class="s cc">{e(a)} — {e(c)}: {e(n)}</div>'
                   for a, c, n in rc.attributions)
    bodies["s09_sources"] = (
        "<table><tr><th>Source</th><th>Author(s)</th><th>Publisher</th><th>Published</th>"
        "<th>Upstream origin(s)</th><th>Contribution</th></tr>" + src_rows + "</table>"
        '<div class="sub">Version history (immutable)</div><table><tr><th>Ver</th><th>As of</th>'
        "<th>Action</th><th>Evidence</th><th>Why it changed</th></tr>" + hist_rows + "</table>"
        + ('<div class="sub">Attributions without a new version</div>' + attr if attr else ""))
    for fid, title in SECTION_IDS:
        parts.append(_section(fid, title, bodies[fid], print_mode=print_mode))
    parts.append(f'<div class="foot">{e(rc.generated_note)}</div>')
    script = ("<script>window.addEventListener('beforeprint',()=>document.querySelectorAll("
              "'details').forEach(d=>d.open=true));</script>")
    body = "".join(parts)
    if print_mode:  # the print file is the COMPLETE record: every nested audit toggle opens too
        body = body.replace("<details>", "<details open>")
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport "
            "content='width=device-width,initial-scale=1'><title>" + e(h.title)
            + "</title><style>" + _CSS + "</style></head><body><div class=wrap><article "
            "class=card>" + body + "</article></div>" + script + "</body></html>")


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
         f"`{h.thesis_id}` · {' › '.join(h.ancestry)} · **{h.research_action.value}** · "
         f"evidence {h.evidence_direction.value} · {h.sector} · {h.region} · horizon "
         f"{h.horizon} · last material update {h.last_material_update.isoformat()} · status "
         f"{h.status.value}", ""]
    if rc.status_note:
        md += [f"> **{rc.status_note}**", ""]
    titles = dict(SECTION_IDS)
    md += [f"## {titles['s01_bottom_line']}"] + _md_sents(card.s01_bottom_line, "s01", rc) + [""]
    wc = card.s02_what_changed
    md += [f"## {titles['s02_what_changed']}", f"- vs prior: {wc.vs_prior}",
          f"- novelty: {wc.novelty}"]
    for i, it in enumerate(wc.items):
        txt = (f"WITHHELD — {rc.blocked[f's02.{i}']}" if f"s02.{i}" in rc.blocked else it.text)
        md.append(f"- [{it.change_class.value}] **{it.provenance.value}:** {txt}"
                 + (f" (source date {it.original_date}" + (f"; period {it.period}"
                                                             if it.period else "") + ")"
                    if it.original_date else "")
                 + (" [" + ", ".join(it.claim_ids) + "]" if it.claim_ids else ""))
    md += ["", f"## {titles['s03_transmission']}"]
    for i, st in enumerate(card.s03_transmission):
        md += [f"- `{st.step}` " + _md_sents([CardSentence(text=st.text, provenance=st.provenance,
                                                          claim_ids=st.claim_ids)], "s03", rc,
                                            i)[0][2:]]
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
                 + f" | {r.value_text or '—'} {r.unit or ''} {r.comparator or ''} | "
                 f"{r.period or '—'} / as of {r.measured_as_of or '—'} | {' · '.join(flags)} | "
                 f"{r.origin or '—'} | {r.article_id} {r.block_id} ({r.claim_id}; "
                 f"{r.role.value}; {r.change_class.value}) |")
    av = card.s05_affected
    md += ["", f"## {titles['s05_affected']}"]
    # (label, group) PAIRS — never `grp is av.instruments`: every empty tuple is the same object,
    # so identity matched one empty group to another's heading
    for label, grp in (("Source-explicit companies", av.companies),
                       ("Named instruments / indices", av.instruments),
                       ("Private or unlisted", av.private_or_unlisted),
                       ("Named, not securities (products, baskets, agencies)", av.not_securities),
                       ("Also named in the source — NOT exposures of this thesis",
                        av.also_named)):
        md.append(f"**{label}:**")
        for c in grp:
            lst = ", ".join(x.ticker + (f" ({x.exchange})" if x.exchange else "")
                            for x in c.listings) or "—"
            md.append(f"- {c.name_as_written} — {lst} — {c.resolution_status.value} — role "
                     f"{c.role.value} ({c.role_detail}) — {c.direction.value} — "
                     f"{c.recommendation_status.value}")
        if not grp:
            md.append("- none")
    md.append(f"**Sectors:** {', '.join(av.sectors) or '—'}")
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
          "**Decision trace:**", *[f"- {t}" for t in d.rule_trace]]
    md += ["", f"## {titles['s09_sources']}"]
    for s in card.s09_sources:
        md.append(f"- [{s.title or 'title UNKNOWN'}]({s.url}) — "
                 f"{'; '.join(s.authors) if s.authors else 'author UNKNOWN'} — {s.publisher} — "
                 f"published {s.published_at.isoformat() if s.published_at else 'UNKNOWN'} — "
                 f"{s.article_class.value} — retrieval {s.retrieval_state.value} — origins: "
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


def affected_from(*, mention_ids: list[tuple[str, str]], mentions: dict[str, Any],
                  resolutions: dict[str, Any], sectors: list[str],
                  baskets: list[CardSentence], prev: AffectedView | None,
                  enrichment: tuple[EnrichmentCandidate, ...] = (),
                  article_mentions: tuple[str, ...] = ()) -> AffectedView:
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
        # the article's STATED role stays the role; the thesis-specific reading (e.g. a capex
        # spender read as a potential beneficiary) sets the direction and is noted beside it
        direction = _CONTEXT_DIRECTION.get(thesis_role, m.direction)
        detail = m.role_detail
        if thesis_role and thesis_role != m.role.value:
            detail = f"{detail} — in this thesis: {thesis_role.replace('_', ' ')}"
        ac = AffectedCompany(mention_id=mid, name_as_written=m.name_as_written,
                             resolution_status=status, listings=r.listings if r else (),
                             cik=r.cik if r else None, role=m.role, role_detail=detail,
                             direction=direction, recommendation_status=m.recommendation_status,
                             article_id=m.article_id, quote=m.quote)
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
            quote=m.quote)
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
                        not_securities=tuple(nsec.values()), also_named=tuple(also.values()))


def entity_key(c: AffectedCompany) -> str:
    """One named entity across articles: its SEC CIK when resolved, else its normalised name."""
    return f"cik:{c.cik}" if c.cik else "name:" + (norm_name(c.name_as_written)
                                                   or c.name_as_written.lower())


_CONTEXT_DIRECTION = {"potential_beneficiary": Direction.POSITIVE,
                      "potentially_harmed": Direction.NEGATIVE}


_ = ClaimKind  # re-exported for callers that classify evidence rows
