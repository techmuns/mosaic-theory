"""The living-thesis engine — match, version, attribute, re-prioritise. Deterministic throughout.

IDENTITY. A thesis is keyed by (value-chain node, profit mechanism, direction, geography) from the
controlled taxonomy. Same key → the SAME thesis is updated; nothing else ever merges. Similarity is
never a merge licence: a different mechanism on the same node is a SIBLING, the opposite direction
is COMPETING (linked, never mashed into one), a parent and a child node are PARENT_CHILD, and an
`other` hypothesis is created REVIEW_NEEDED with lexically similar theses flagged — never merged.
The thesis id is a hash of the key, so a re-run on an empty registry reproduces the same ids, and a
populated registry MATCHES an earlier thesis instead of minting a new id.

WHAT AN INCOMING CLAIM IS, relative to what the thesis already holds:
  repeated                — same claim, or same measure + value + upstream ORIGIN (attribution only)
  independent confirmation — same measure and value from a DIFFERENT origin
  contradictory           — the source contradicts the thesis, or a different origin disagrees
  correction              — same origin + measure, different value, no later as-of
  timing change           — an event whose date moved
  new                     — evidence not held before (updated readings of a series included)
  novelty_unverified      — everything on a brand-new thesis: no verified baseline existed
Only MATERIAL classes create a new version; a repeat is recorded as an attribution with no new
version, no changed priority and no false confirmation. Prior versions are immutable rows; each new
version carries a field-by-field diff against the one before.

RE-ANCHOR BEFORE WITHHOLDING. When a source-labelled card line fails its check (a number its cited
claims lack, no verified citation, or the pass-2 reviewer judging its cited spans insufficient),
the engine first looks for OTHER verified claims of the same source(s) that carry it — the
reviewer's suggestions, then a deterministic number-and-words match — re-cites the line, re-derives
its label, and reviews it again. Only a line that is still unsupported is withheld. A MODEL
INFERENCE line is never re-anchored into a source label.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from vinci.theme_intelligence.cards import (
    LABEL_CLOSE,
    LABEL_OPEN,
    CardInputs,
    affected_from,
    card_sha,
    compose_card,
    diff_cards,
    origin_label,
    sector_exposures_from,
    with_citations,
)
from vinci.theme_intelligence.config import ENGINE_VERSION, STALE_AFTER_DAYS, Taxonomy
from vinci.theme_intelligence.contradiction import AMBIGUOUS, CONTRADICTS, assess
from vinci.theme_intelligence.priority import ThesisState, compute_priority
from vinci.theme_intelligence.schemas import (
    ACTION_RANK,
    EXPOSURE_ROLES,
    MATERIAL_CLASSES,
    Article,
    ArticleClass,
    ArticleThesisContribution,
    ArticleVersion,
    CardContent,
    CardSentence,
    ChangeClass,
    ChangeEvent,
    ChangeItem,
    Claim,
    ClaimKind,
    Direction,
    Epistemic,
    EvidenceDirection,
    EvidenceRole,
    FieldDiff,
    Horizon,
    InvestmentReadiness,
    IssueSeverity,
    LinkRole,
    Mention,
    PitStatus,
    Provenance,
    RelationType,
    ResearchAction,
    ResearchPriority,
    ResolutionStatus,
    RetrievalState,
    SecurityResolution,
    SourceRef,
    StanceInSource,
    ThemeRelation,
    Thesis,
    ThesisClaimLink,
    ThesisKind,
    ThesisStatus,
    ThesisVersion,
    VerificationIssue,
    identity_key,
)
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.timewindow import Window, window_of
from vinci.theme_intelligence.verify import (
    ReviewOutcome,
    VerifiedExtraction,
    VerifiedHypothesis,
    VerifiedRisk,
    card_sentences,
    label_for,
    overlap_anchor,
    passage_anchor,
    passage_claim,
    reanchor_sentence,
)

_GEO = {"us": "US", "u.s.": "US", "united states": "US", "usa": "US", "america": "US",
        "global": "Global", "worldwide": "Global", "world": "Global", "china": "China",
        "europe": "Europe", "eu": "Europe", "japan": "Japan", "asia": "APAC", "apac": "APAC",
        "asia pacific": "APAC", "taiwan": "Taiwan", "korea": "Korea", "south korea": "Korea",
        "india": "India", "uk": "UK", "united kingdom": "UK"}
_STANCE_RANK = {StanceInSource.ASSERTED: 3, StanceInSource.REPORTED_VIEW: 2,
                StanceInSource.CONDITIONAL: 1, StanceInSource.SPECULATIVE: 0}
_ROLE_FOR = (("dislocation", LinkRole.DISLOCATION), ("catalyst", LinkRole.CATALYST),
             ("supporting", LinkRole.SUPPORTS), ("strongest", LinkRole.SUPPORTS),
             ("counter", LinkRole.CONTRADICTS))


def norm_geo(g: str) -> str:
    k = re.sub(r"\s+", " ", g.strip().lower())
    return _GEO.get(k, g.strip() or "Unspecified")


def _sha(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode())
        h.update(b"\x00")
    return h.hexdigest()


def review_tag(h: VerifiedHypothesis) -> str:
    """An unclassified (`other`) hypothesis never shares an identity with another by key alone."""
    raw = h.raw
    if raw.value_chain_node == "other" or raw.mechanism == "other":
        return _sha(raw.title.lower())[:8]
    return ""


def segment_of(h: VerifiedHypothesis, claims: dict[str, Claim], taxonomy: Taxonomy) -> str:
    """The segment(s) within the node that the hypothesis's VERIFIED evidence names — read from
    the verbatim quotes of its supporting / dislocation / catalyst claims and its source-named
    sector spans, never from the model's wording. "" when the node defines no segments or the
    evidence names none."""
    segs = taxonomy.segments_of(h.raw.value_chain_node)
    if not segs:
        return ""
    texts = [claims[c].quote for c in (*h.supporting, *h.dislocation, *h.catalyst)
             if c in claims and claims[c].span_verified]
    texts += [x.quote for x in h.sectors]
    blob = " ".join(texts)
    found = [sg.id for sg in segs
             if any(re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", blob, re.I)
                    for term in sg.terms)]
    return "+".join(sorted(found))


#: what an equity-market STRUCTURE measure looks like in a claim's quote or metric
_MARKET_STRUCTURE = re.compile(
    r"correlation|dispersion|\bbreadth\b|\bvix\b|% of (?:the )?stocks|share of "
    r"stocks|stocks? (?:trading )?(?:above|below)|moving average|\bbeta\b|index concentration|"
    r"equal[- ]weight|"
    # volatility OF PRICES — "political volatility" is not market structure (Citi LatAm,
    # 2026-10-11: the only match on a fiscal-credibility record)
    r"(?:implied|realized|realised|market|equity|equities|stock|index|price|return)s?\s+"
    r"volatilit|volatilit\w*\s+(?:index|of (?:the )?(?:market|index|stocks|equities|returns))",
    re.I)


def record_kind(h: VerifiedHypothesis, claims: dict[str, Claim]) -> tuple[ThesisKind, str | None]:
    """MARKET_REGIME only for equity-market structure: a record whose evidence MEASURES it
    (correlation, dispersion, breadth, price volatility) — on any node, the market-wide one
    included. A sector or macro mechanism — regulation, capacity, demand, capex, rates — is an
    investment thesis, so its earnings transmission is tested like any other. Observed
    2026-10-11: Citi's "LatAm capex demand broadens across energy, minerals, infrastructure and
    agriculture" sat on `macro_market` and was kept a regime by node alone. (The reason when
    corrected.)"""
    raw = h.raw
    if raw.kind is not ThesisKind.MARKET_REGIME:
        return raw.kind, None
    ev = [claims[c] for c in (*h.supporting, *h.dislocation, *h.catalyst) if c in claims]
    if any(_MARKET_STRUCTURE.search(f"{c.metric or ''} {c.quote}") for c in ev):
        return raw.kind, None
    return ThesisKind.INVESTMENT_THESIS, (
        f"extracted as a market-regime record on {raw.value_chain_node}, but none of its "
        f"{len(ev)} evidence claim(s) measures equity-market structure (correlation, dispersion, "
        f"breadth, volatility) — a sector mechanism is an investment thesis: its earnings "
        f"transmission is tested like any other")


def thesis_key(h: VerifiedHypothesis, segment: str = "") -> str:
    raw = h.raw
    return identity_key(raw.value_chain_node, raw.mechanism, raw.direction.value,
                        norm_geo(raw.geography), segment, review_tag(h))


#: Regions a geography string names. "Global" overlaps every region; APAC contains its members.
_REGION_WORDS = {"us": "US", "u.s.": "US", "u.s": "US", "united states": "US", "usa": "US",
                 "america": "US", "north america": "US", "texas": "US", "china": "China",
                 "europe": "Europe", "eu": "Europe", "japan": "Japan", "asia": "APAC",
                 "apac": "APAC", "asia pacific": "APAC", "taiwan": "Taiwan", "korea": "Korea",
                 "south korea": "Korea", "india": "India", "uk": "UK",
                 "united kingdom": "UK"}
_REGION_CONTAINS = {"APAC": {"China", "Japan", "Taiwan", "Korea", "India"}}


def _regions(g: str) -> set[str]:
    low = g.lower()
    if re.search(r"\b(global|world|worldwide)\b", low):
        return {"*"}
    found = {v for k, v in _REGION_WORDS.items()
             if re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", low)}
    return found or {low.strip() or "unspecified"}


def geographies_overlap(a: str, b: str) -> bool:
    """Whether two theses can be about the same place: equal or containing regions, or Global."""
    ra, rb = _regions(a), _regions(b)
    if "*" in ra or "*" in rb or ra & rb:
        return True
    return any(x in _REGION_CONTAINS.get(y, set()) for x in ra for y in rb) or any(
        y in _REGION_CONTAINS.get(x, set()) for x in ra for y in rb)


def evidence_windows(claims: list[Claim], ref: date) -> list[Window]:
    """The calendar windows a thesis's verified evidence states (period first; a forecast or
    event may state it in its quote)."""
    out: list[Window] = []
    for c in claims:
        w = window_of(c.period, ref)
        if w is None and (c.epistemic is Epistemic.FORECAST
                          or c.kind in (ClaimKind.FORECAST, ClaimKind.EVENT)):
            w = window_of(c.quote, ref)
        if w is not None:
            out.append(w)
    return out


def claim_differences(a: Thesis, b: Thesis, wa: list[Window], wb: list[Window],
                      seg_label: dict[str, str]) -> list[str]:
    """What separates two theses on ONE value-chain node from being the same economic claim —
    the dimensions the review names: the business segment, the measured variable (the profit
    mechanism), the geography and the timeframe. Empty = the same claim (a direct
    contradiction when the directions oppose)."""
    diffs: list[str] = []
    if a.key_review or b.key_review:
        diffs.append("an unclassified thesis (no taxonomy node or mechanism) — not comparable "
                     "by key")
    if a.key_mechanism != b.key_mechanism:
        diffs.append(f"a different mechanism ({b.key_mechanism} vs {a.key_mechanism})")
    sa = set(filter(None, a.key_segment.split("+")))
    sb = set(filter(None, b.key_segment.split("+")))

    def names(x: set[str]) -> str:
        return " + ".join(seg_label.get(i, i) for i in sorted(x)) or "no named segment"

    if sa != sb:
        if not sa or not sb or not (sa & sb):
            diffs.append(f"a different segment ({names(sb)} vs {names(sa)})")
        else:
            diffs.append(f"overlapping but different segments ({names(sb)} vs {names(sa)})")
    if not geographies_overlap(a.key_geography, b.key_geography):
        diffs.append(f"a different geography ({b.key_geography} vs {a.key_geography})")
    if wa and wb:
        if not any(x.start <= y.end and y.start <= x.end for x in wa for y in wb):
            diffs.append("no overlapping timeframe")
    elif wa or wb:
        diffs.append("a timeframe only one of them states")
    return diffs


def thesis_id_for(key: str) -> str:
    return "TH-" + _sha(key)[:10].upper()


@dataclass
class ArticleContext:
    article: Article
    version: ArticleVersion
    reliability: str
    run_id: str
    as_of: date


@dataclass
class ThesisOutcome:
    thesis_id: str
    title: str
    created: bool
    new_version: int | None
    contribution: ChangeClass
    action: ResearchAction
    previous_action: ResearchAction | None
    evidence_direction: EvidenceDirection
    events: list[str] = field(default_factory=list)


#: A reviewer returns its issues — or a ReviewOutcome that also carries re-anchoring suggestions.
Reviewer = Callable[[CardContent, dict[str, Claim]], list[VerificationIssue] | ReviewOutcome]
#: The deterministic card checks whose failure re-anchoring can cure.
_REANCHORABLE = frozenset({"NUMBER_NOT_IN_CITED_CLAIMS", "FACT_WITHOUT_CLAIM"})


class Engine:
    def __init__(self, store: Store, taxonomy: Taxonomy, *,
                 reviewer: Reviewer | None = None) -> None:
        self.store = store
        self.taxonomy = taxonomy
        self.reviewer = reviewer
        self.node_label = {n.id: n.label for n in taxonomy.nodes}
        #: thesis id -> when this registry FIRST ingested it, for a `state pull` replay: a thesis
        #: it re-creates keeps its original date, never the replay's clock
        self.first_ingested: dict[str, datetime] = {}

    # -- public --------------------------------------------------------------------------------
    def apply(self, ctx: ArticleContext, ve: VerifiedExtraction,
              resolutions: dict[str, SecurityResolution]) -> list[ThesisOutcome]:
        st = self.store
        with st.tx():
            for o in ve.origins.values():
                st.add_origin(o)
            for c in ve.claims:
                st.add_claim(c)
            for m in ve.mentions:
                st.add_mention(m)
            for r in resolutions.values():
                st.add_resolution(r)
            for i in ve.issues:
                st.add_issue(i)
        claims = {c.claim_id: c for c in ve.claims}
        mentions = {m.mention_id: m for m in ve.mentions}

        for h in ve.hypotheses:  # the record type is checked before any thesis is touched
            kind, why = record_kind(h, claims)
            if why:
                h.raw = h.raw.model_copy(update={"kind": kind})
                st.add_issue(self._issue(ctx, "hypothesis", f"{ctx.version.version_id}:"
                                         f"{h.raw.local_id}", IssueSeverity.INFO,
                                         "RECORD_KIND_CORRECTED", f"“{h.raw.title}”: {why}"))
        groups: dict[str, list[VerifiedHypothesis]] = {}
        segments: dict[str, str] = {}
        # theses this article's EARLIER versions contributed to (before this version applies)
        earlier = list(dict.fromkeys(c.thesis_id for c in st.contributions(
            article_id=ctx.article.article_id)))
        for h in ve.hypotheses:
            seg = segment_of(h, claims, self.taxonomy)
            key = thesis_key(h, seg)
            groups.setdefault(key, []).append(h)
            segments[key] = seg
        outcomes: list[ThesisOutcome] = []
        created_now: list[str] = []
        for key, hs in groups.items():
            h = hs[0]
            if len(hs) > 1:
                for extra in hs[1:]:
                    h.supporting += [c for c in extra.supporting if c not in h.supporting]
                    h.dislocation += [c for c in extra.dislocation if c not in h.dislocation]
                    h.counter += [c for c in extra.counter if c not in h.counter]
                    h.affected += [a for a in extra.affected if a not in h.affected]
                st.add_issue(self._issue(ctx, "hypothesis", key, IssueSeverity.WARN,
                                         "SAME_KEY_IN_ARTICLE",
                                         f"{len(hs)} hypotheses share one identity key in one "
                                         f"article — merged as one thesis contribution"))
            risks = [r for r in ve.risks if not r.related or h.raw.local_id in r.related]
            existing = st.thesis_by_key(key)
            if existing is None and (prior := self._same_article_thesis(h, segments[key],
                                                                        earlier)):
                existing = prior
                st.add_issue(self._issue(
                    ctx, "thesis", prior.thesis_id, IssueSeverity.INFO, "SAME_ARTICLE_VERSION",
                    f"a later version of {ctx.article.article_id} names segment(s) "
                    f"{segments[key] or 'none'}; its earlier version created this thesis "
                    f"(segment {prior.key_segment or 'none'}) — updated, never a second thesis "
                    f"from one article"))
            if existing is None:
                out = self._create(ctx, key, h, claims, mentions, resolutions, risks,
                                   segments[key])
                created_now.append(out.thesis_id)
            else:
                out = self._update(ctx, existing, h, claims, mentions, resolutions, risks)
            outcomes.append(out)
        for tid in created_now:
            outcomes.extend(self._challenge_competitors(ctx, tid, claims, mentions, resolutions,
                                                        created_now))
        return outcomes

    def _same_article_thesis(self, h: VerifiedHypothesis, segment: str,
                             earlier: list[str]) -> Thesis | None:
        """The thesis an EARLIER VERSION of this same article created for this hypothesis, when
        the fuller version's evidence names more (or fewer) segments — a preview naming none,
        its full text naming DRAM. Every other identity dimension must match and the segment
        sets must nest; disjoint segments are different claims and stay separate theses."""
        raw = h.raw
        new = set(filter(None, segment.split("+")))
        for tid in earlier:
            t = self.store.thesis(tid)
            if t is None or (t.key_node, t.key_mechanism, t.key_direction.value,
                             t.key_geography, t.key_review) != (
                    raw.value_chain_node, raw.mechanism, raw.direction.value,
                    norm_geo(raw.geography), review_tag(h)):
                continue
            old = set(filter(None, t.key_segment.split("+")))
            if old <= new or new <= old:
                return t
        return None

    # -- create -------------------------------------------------------------------------------
    def _create(self, ctx: ArticleContext, key: str, h: VerifiedHypothesis,
                claims: dict[str, Claim], mentions: dict[str, Mention],
                resolutions: dict[str, SecurityResolution],
                risks: list[VerifiedRisk], segment: str = "") -> ThesisOutcome:
        raw = h.raw
        tid = thesis_id_for(key)
        other = raw.value_chain_node == "other" or raw.mechanism == "other"
        now = self.first_ingested.get(tid) or datetime.now(tz=UTC)
        published = (ctx.article.published_at.date() if ctx.article.published_at else ctx.as_of)
        thesis = Thesis(
            thesis_id=tid, key_node=raw.value_chain_node, key_mechanism=raw.mechanism,
            key_direction=Direction(raw.direction.value), key_geography=norm_geo(raw.geography),
            title=raw.title.strip(), sector=self.node_label.get(raw.value_chain_node,
                                                                raw.value_chain_node),
            region=norm_geo(raw.geography),
            status=ThesisStatus.REVIEW_NEEDED if other else ThesisStatus.ACTIVE,
            current_version=1, created_at=now, created_as_of=ctx.as_of,
            last_material_update=published,
            ancestry=self.taxonomy.ancestry(raw.value_chain_node),
            stance=raw.stance_in_source, horizon=raw.horizon, kind=raw.kind,
            key_segment=segment, key_review=review_tag(h))
        assert thesis.identity == key, (thesis.identity, key)  # one identity, store and engine
        roles = self._roles(h, risks)
        links = [ThesisClaimLink(thesis_id=tid, claim_id=cid, role=role, first_version=1,
                                 change_class=ChangeClass.NOVELTY_UNVERIFIED,
                                 independence_group=claims[cid].origin_id or ctx.article.article_id)
                 for cid, role in roles.items()]
        own = [claims[cid] for cid, role in roles.items() if cid in claims
                and role in (LinkRole.SUPPORTS, LinkRole.DISLOCATION, LinkRole.CATALYST)]
        relations = self._relations_for(thesis, ctx, own)
        rel_notes = [CardSentence(text=f"Registry link — {relation_label(r)} "
                                       f"{r.to_thesis if r.from_thesis == tid else r.from_thesis}"
                                       f": {r.reason}", provenance=Provenance.MODEL_INFERENCE)
                     for r in relations]
        head, n_evidence = self._headline_claims(h, claims)
        items = [ChangeItem(change_class=ChangeClass.NOVELTY_UNVERIFIED,
                            text=claims[c].statement, provenance=_label([c], claims),
                            claim_ids=(c,), article_id=ctx.article.article_id,
                            original_date=published.isoformat(), period=claims[c].period)
                 for c in head]
        if n_evidence > len(head):
            items.append(_more_item(len(head), n_evidence, ctx.article.article_id))
        vs_prior = (f"New to the registry — first ingested {now:%Y-%m-%d %H:%M} UTC, analysed as "
                    f"of {ctx.as_of.isoformat()}, from a source published "
                    f"{published.isoformat()}; not necessarily new to the market.")
        novelty = ("novelty_unverified — the registry held no earlier verified baseline, so this "
                   "is new TO THE REGISTRY, not demonstrated new to the market")
        version = self._build_version(
            ctx, thesis, 1, h, None, links, claims, mentions, resolutions, items, vs_prior,
            novelty, EvidenceDirection.NEW, None, (), self._risk_sentences(risks, claims),
            rel_notes, [claims[c] for c in h.counter if c in claims], change_summary=(
                "Initial record — created from " + ctx.article.article_id), classes={},
            contribution=ChangeClass.NOVELTY_UNVERIFIED)
        contribution = ArticleThesisContribution(
            contribution_id="AC-" + _sha(ctx.version.version_id, tid)[:14],
            article_id=ctx.article.article_id, thesis_id=tid, version=1,
            contribution=ChangeClass.NOVELTY_UNVERIFIED, claim_ids=tuple(roles),
            run_id=ctx.run_id, as_of=ctx.as_of)
        events = [self._event(ctx, tid, 1, "CREATED", f"new thesis from "
                              f"{ctx.article.article_id}: {thesis.title}")]
        if other:
            events.append(self._event(ctx, tid, 1, "REVIEW_NEEDED",
                                      "taxonomy node or mechanism is `other` — a human must "
                                      "classify it; it will never merge by similarity"))
        with self.store.tx():
            self.store.upsert_thesis(thesis)
            self.store.add_thesis_version(version)
            for lk in links:
                self.store.add_link(lk)
            self.store.add_contribution(contribution)
            for r in relations:
                self.store.add_relation(r)
            for ev in events:
                self.store.add_event(ev)
        return ThesisOutcome(tid, thesis.title, True, 1, ChangeClass.NOVELTY_UNVERIFIED,
                             version.priority.research_action, None, EvidenceDirection.NEW,
                             [ev.event_type for ev in events])

    # -- update -------------------------------------------------------------------------------
    def _update(self, ctx: ArticleContext, thesis: Thesis, h: VerifiedHypothesis,
                claims: dict[str, Claim], mentions: dict[str, Mention],
                resolutions: dict[str, SecurityResolution],
                risks: list[VerifiedRisk]) -> ThesisOutcome:
        st = self.store
        cid_contrib = "AC-" + _sha(ctx.version.version_id, thesis.thesis_id)[:14]
        prev_v = st.thesis_version(thesis.thesis_id, thesis.current_version)
        assert prev_v is not None
        if any(c.contribution_id == cid_contrib for c in st.contributions(thesis.thesis_id)):
            return ThesisOutcome(thesis.thesis_id, thesis.title, False, None,
                                 ChangeClass.REPEATED, prev_v.priority.research_action,
                                 prev_v.priority.research_action, EvidenceDirection.UNCHANGED,
                                 ["ALREADY_INGESTED"])
        existing_links = st.links(thesis.thesis_id)
        held = {lk.claim_id: st.claim(lk.claim_id) for lk in existing_links}
        held_claims = [c for c in held.values() if c is not None]
        roles = self._roles(h, risks)
        classes: dict[str, ChangeClass] = {}
        notes: dict[str, str] = {}
        for cid, role in roles.items():
            if cid in held:
                classes[cid], notes[cid] = ChangeClass.REPEATED, "claim already linked"
                continue
            classes[cid], notes[cid] = classify_claim(claims[cid], role, held_claims)
        material = any(c in MATERIAL_CLASSES for c in classes.values())
        next_v = thesis.current_version + (1 if material else 0)
        new_links = [ThesisClaimLink(thesis_id=thesis.thesis_id, claim_id=cid, role=role,
                                     first_version=next_v, change_class=classes[cid],
                                     independence_group=claims[cid].origin_id
                                     or ctx.article.article_id)
                     for cid, role in roles.items() if cid not in held]
        if not material:
            cls = ChangeClass.REPEATED if classes else ChangeClass.NO_MATERIAL_CHANGE
            contribution = ArticleThesisContribution(
                contribution_id=cid_contrib, article_id=ctx.article.article_id,
                thesis_id=thesis.thesis_id, version=None, contribution=cls,
                claim_ids=tuple(roles), run_id=ctx.run_id, as_of=ctx.as_of)
            ev = self._event(ctx, thesis.thesis_id, None, "ATTRIBUTION",
                             f"{ctx.article.article_id} repeats evidence the thesis already "
                             f"holds ({cls.value}) — attribution recorded, no new version, "
                             f"priority unchanged")
            with st.tx():
                for lk in new_links:
                    st.add_link(lk)
                st.add_contribution(contribution)
                st.add_event(ev)
            return ThesisOutcome(thesis.thesis_id, thesis.title, False, None, cls,
                                 prev_v.priority.research_action,
                                 prev_v.priority.research_action, EvidenceDirection.UNCHANGED,
                                 ["ATTRIBUTION"])

        direction = evidence_direction_of(classes, roles)
        published = (ctx.article.published_at.date() if ctx.article.published_at else ctx.as_of)
        thesis = thesis.model_copy(update={
            "current_version": next_v, "last_material_update": max(thesis.last_material_update,
                                                                   published),
            "stance": max(thesis.stance, h.raw.stance_in_source, key=lambda s: _STANCE_RANK[s]),
            "horizon": h.raw.horizon if h.raw.horizon is not Horizon.UNCLEAR else thesis.horizon})
        items = [ChangeItem(change_class=classes[cid],
                            text=f"{claims[cid].statement} {LABEL_OPEN}{notes[cid]}{LABEL_CLOSE}",
                            provenance=_label([cid], claims), claim_ids=(cid,),
                            article_id=ctx.article.article_id,
                            original_date=published.isoformat(), period=claims[cid].period)
                 for cid in roles if classes[cid] is not ChangeClass.REPEATED]
        n_changed = len(items)
        items = items[:UPDATE_ITEMS]
        if n_changed > len(items):
            items.append(_more_item(len(items), n_changed, ctx.article.article_id))
        repeated = [cid for cid in roles if classes[cid] is ChangeClass.REPEATED]
        if repeated:
            # registry bookkeeping, not a statement of the source: never source-labelled
            items.append(ChangeItem(change_class=ChangeClass.REPEATED,
                                    text=f"{len(repeated)} claim(s) repeat evidence already held "
                                         f"(same origin) — attribution only"
                                         + (f" (showing 6 of {len(repeated)} claim refs)"
                                            if len(repeated) > 6 else ""),
                                    provenance=Provenance.MODEL_INFERENCE,
                                    claim_ids=tuple(repeated[:6]),
                                    article_id=ctx.article.article_id,
                                    original_date=published.isoformat()))
        counts: dict[str, int] = {}
        for c in classes.values():
            counts[c.value] = counts.get(c.value, 0) + 1
        vs_prior = (f"v{thesis.current_version - 1} held {len(held_claims)} claim(s); this "
                    f"source adds: " + ", ".join(f"{k} ×{v}" for k, v in sorted(counts.items())))
        novelty = ("assessed against the registry's prior version — classes are relative to what "
                   "the thesis already held, not to market knowledge")
        counter = [claims[cid] for cid, r in roles.items() if r is LinkRole.CONTRADICTS]
        all_links = existing_links + new_links
        version = self._build_version(
            ctx, thesis, next_v, h, prev_v.content, all_links, claims, mentions, resolutions,
            items, vs_prior, novelty, direction, prev_v.priority.research_action,
            prev_v.priority.factors, self._risk_sentences(risks, claims), [], counter,
            change_summary=f"{ctx.article.article_id}: " + ", ".join(
                f"{k} ×{v}" for k, v in sorted(counts.items())), classes=classes,
            contribution=dominant_class(classes), prev_sha=prev_v.content_sha)
        etype = event_type(prev_v.priority.research_action, version.priority.research_action,
                           classes)
        contribution = ArticleThesisContribution(
            contribution_id=cid_contrib, article_id=ctx.article.article_id,
            thesis_id=thesis.thesis_id, version=next_v,
            contribution=dominant_class(classes), claim_ids=tuple(roles), run_id=ctx.run_id,
            as_of=ctx.as_of)
        ev = self._event(ctx, thesis.thesis_id, next_v, etype, version.change_summary,
                         version.diffs)
        events = [ev]
        if thesis.status is ThesisStatus.ARCHIVED and \
                version.priority.research_action is not ResearchAction.SKIP:
            thesis = thesis.model_copy(update={"status": ThesisStatus.ACTIVE})
            events.append(self._event(ctx, thesis.thesis_id, next_v, "REACTIVATED",
                                      f"material new evidence from {ctx.article.article_id} "
                                      f"moved an archived thesis back to "
                                      f"{version.priority.research_action.value}"))
        with st.tx():
            st.upsert_thesis(thesis)
            st.add_thesis_version(version)
            for lk in new_links:
                st.add_link(lk)
            st.add_contribution(contribution)
            for ev in events:
                st.add_event(ev)
        return ThesisOutcome(thesis.thesis_id, thesis.title, False, next_v,
                             contribution.contribution, version.priority.research_action,
                             prev_v.priority.research_action, direction,
                             [x.event_type for x in events])

    # -- archive ------------------------------------------------------------------------------
    def archive_pass(self, *, run_id: str, as_of: date) -> list[ChangeEvent]:
        """Move a thesis OFF the active list — never out of the registry. Two face-validity rules,
        neither tuned on outcomes: (1) its research action is SKIP ("skip, but still archive");
        (2) no material evidence for more than STALE_AFTER_DAYS, so its 2-4-quarter "why now" has
        lapsed. Each archive is an ARCHIVED event the weekly report shows in its own section; the
        thesis, its versions and its evidence stay searchable, and new material evidence
        re-activates it."""
        out: list[ChangeEvent] = []
        now = datetime.now(tz=UTC)
        for t in self.store.theses():
            if t.status is ThesisStatus.ARCHIVED:
                continue
            v = self.store.thesis_version(t.thesis_id, t.current_version)
            if v is None:
                continue
            idle = (as_of - t.last_material_update).days
            if v.priority.research_action is ResearchAction.SKIP:
                why = ("research action is SKIP — kept in the searchable archive, off the active "
                       "list")
            elif idle > STALE_AFTER_DAYS:
                why = (f"no material evidence for {idle} days (> {STALE_AFTER_DAYS}) as of "
                       f"{as_of.isoformat()} — the 2-4-quarter window has lapsed")
            else:
                continue
            ev = ChangeEvent(event_id="CE-" + _sha(t.thesis_id, str(t.current_version),
                                                   "ARCHIVED", run_id)[:14],
                             thesis_id=t.thesis_id, version=t.current_version,
                             event_type="ARCHIVED", run_id=run_id, as_of=as_of, created_at=now,
                             detail=why)
            with self.store.tx():
                self.store.upsert_thesis(t.model_copy(update={"status": ThesisStatus.ARCHIVED}))
                self.store.add_event(ev)
            out.append(ev)
        return out

    # -- competing hypotheses -----------------------------------------------------------------
    def _challenge_competitors(self, ctx: ArticleContext, new_tid: str, claims: dict[str, Claim],
                               mentions: dict[str, Mention],
                               resolutions: dict[str, SecurityResolution],
                               created_now: list[str]) -> list[ThesisOutcome]:
        """A new opposite-direction thesis CHALLENGES the existing one: its support is linked to
        the incumbent as CONTRADICTS evidence (a new incumbent version), never merged."""
        out: list[ThesisOutcome] = []
        for rel in self.store.relations(new_tid):
            if rel.relation is not RelationType.COMPETING:
                continue
            other_id = rel.to_thesis if rel.from_thesis == new_tid else rel.from_thesis
            if other_id in created_now:
                continue  # both sides came from this very article — linked, nothing to challenge
            inc = self.store.thesis(other_id)
            if inc is None or inc.status is ThesisStatus.ARCHIVED:
                continue
            if rel.evidence_role == EvidenceRole.CONTRADICTION_REVIEW.value:
                ev = self._event(ctx, inc.thesis_id, None, "CONTRADICTION_REVIEW",
                                 f"competing thesis {new_tid}: {rel.reason}")
                with self.store.tx():
                    self.store.add_event(ev)
                continue
            # ONLY the claims that directly contradict the incumbent's own evidence are filed —
            # never the challenger's whole support, never by how many claims it has
            support = list(rel.claim_ids)
            if not support:
                continue
            fake = _ChallengeHyp(support)
            out.append(self._apply_challenge(ctx, inc, fake, claims, new_tid))
        return out

    def _apply_challenge(self, ctx: ArticleContext, inc: Thesis, ch: _ChallengeHyp,
                         claims: dict[str, Claim], challenger: str) -> ThesisOutcome:
        st = self.store
        prev_v = st.thesis_version(inc.thesis_id, inc.current_version)
        assert prev_v is not None
        held = {lk.claim_id for lk in st.links(inc.thesis_id)}
        add = [c for c in ch.claim_ids if c not in held]
        if not add:
            return ThesisOutcome(inc.thesis_id, inc.title, False, None, ChangeClass.REPEATED,
                                 prev_v.priority.research_action,
                                 prev_v.priority.research_action, EvidenceDirection.UNCHANGED)
        next_v = inc.current_version + 1
        links = [ThesisClaimLink(thesis_id=inc.thesis_id, claim_id=c, role=LinkRole.CONTRADICTS,
                                 first_version=next_v, change_class=ChangeClass.CONTRADICTORY,
                                 independence_group=claims[c].origin_id or ctx.article.article_id)
                 for c in add]
        all_links = st.links(inc.thesis_id) + links
        classes = dict.fromkeys(add, ChangeClass.CONTRADICTORY)
        inc = inc.model_copy(update={"current_version": next_v})
        items = [ChangeItem(change_class=ChangeClass.CONTRADICTORY,
                            text=f"{LABEL_OPEN}competing hypothesis {challenger}, "
                                 f"{ctx.article.article_id}{LABEL_CLOSE} {claims[c].statement}",
                            provenance=_label([c], claims), claim_ids=(c,),
                            article_id=ctx.article.article_id,
                            original_date=(ctx.article.published_at.date().isoformat()
                                           if ctx.article.published_at else None))
                 for c in add[:UPDATE_ITEMS]]
        if len(add) > UPDATE_ITEMS:
            items.append(_more_item(UPDATE_ITEMS, len(add), ctx.article.article_id))
        version = self._build_version(
            ctx, inc, next_v, None, prev_v.content, all_links, claims, {}, {}, items,
            f"challenged by competing thesis {challenger} — evidence linked as CONTRADICTS, "
            f"the two theses stay separate", "relative to the registry's prior version",
            EvidenceDirection.WEAKER, prev_v.priority.research_action, prev_v.priority.factors,
            [], [CardSentence(text=f"Registry link — CONTRADICTION — competing hypothesis "
                                   f"{challenger}: {_competing_basis(inc, st.thesis(challenger))}",
                              provenance=Provenance.MODEL_INFERENCE)],
            [claims[c] for c in add], change_summary=f"challenged by {challenger}",
            classes=classes, contribution=ChangeClass.CONTRADICTORY, prev_sha=prev_v.content_sha)
        contribution = ArticleThesisContribution(
            # one id per CHALLENGER: an article whose two new theses both compete with this one
            # challenges it twice (observed 2026-10-10 — the shared id stopped the weekly run)
            contribution_id="AC-" + _sha(ctx.version.version_id, inc.thesis_id, "challenge",
                                         challenger)[:14],
            article_id=ctx.article.article_id, thesis_id=inc.thesis_id, version=next_v,
            contribution=ChangeClass.CONTRADICTORY, claim_ids=tuple(add), run_id=ctx.run_id,
            as_of=ctx.as_of)
        etype = event_type(prev_v.priority.research_action, version.priority.research_action,
                           classes)
        ev = self._event(ctx, inc.thesis_id, next_v, etype, version.change_summary,
                         version.diffs)
        with st.tx():
            st.upsert_thesis(inc)
            st.add_thesis_version(version)
            for lk in links:
                st.add_link(lk)
            st.add_contribution(contribution)
            st.add_event(ev)
        return ThesisOutcome(inc.thesis_id, inc.title, False, next_v, ChangeClass.CONTRADICTORY,
                             version.priority.research_action, prev_v.priority.research_action,
                             EvidenceDirection.WEAKER, [etype])

    # -- shared -------------------------------------------------------------------------------
    def _build_version(self, ctx: ArticleContext, thesis: Thesis, version: int,
                       h: VerifiedHypothesis | None, prev: CardContent | None,
                       links: list[ThesisClaimLink], claims: dict[str, Claim],
                       mentions: dict[str, Mention], resolutions: dict[str, SecurityResolution],
                       items: list[ChangeItem], vs_prior: str, novelty: str,
                       direction: EvidenceDirection, previous: ResearchAction | None,
                       prev_factors: tuple[object, ...], risk_sents: list[CardSentence],
                       rel_notes: list[CardSentence], counter: list[Claim], *,
                       change_summary: str, classes: dict[str, ChangeClass],
                       contribution: ChangeClass, prev_sha: str | None = None) -> ThesisVersion:
        all_claims = dict(claims)
        for lk in links:
            if lk.claim_id not in all_claims and (c := self.store.claim(lk.claim_id)):
                all_claims[lk.claim_id] = c
        affected = affected_from(
            mention_ids=h.affected if h else [], mentions=mentions, resolutions={
                mid: resolutions[mid] for mid in mentions if mid in resolutions},
            sectors=list(h.raw.sectors) if h else [],
            baskets=[CardSentence(text=b.description + " (constituents not named by the source)",
                                  provenance=_label([h.claim_map[x] for x in b.claim_ids
                                                     if x in h.claim_map], all_claims),
                                  claim_ids=tuple(h.claim_map[x] for x in b.claim_ids
                                                  if x in h.claim_map))
                     for b in h.raw.cited_baskets] if h else [],
            prev=prev.s05_affected if prev else None,
            article_mentions=tuple(mentions),
            sector_exposures=sector_exposures_from(
                h.sectors if h else [], all_claims, ctx.article.article_id,
                prev.s05_affected if prev else None))
        sources = self._sources(thesis.thesis_id, ctx, links, all_claims, contribution)
        hold_reasons = self._hold_reasons(links, all_claims)

        published = tuple((s.article_id, s.published_at.date()) for s in sources
                          if s.published_at is not None)
        data_reports = tuple(s.article_id for s in sources
                             if s.article_class is ArticleClass.INDUSTRY_DATA_REPORT)

        def make(hold_extra: list[str]) -> tuple[CardContent, ResearchPriority]:
            holds = hold_reasons + hold_extra
            # an EXPOSURE is a point-in-time-verified common-equity line — a current-day ticker
            # map never counts (the listings carry only VERIFIED common equity by construction;
            # the filter restates it so a future resolver change cannot widen it silently)
            listed = tuple((c.name_as_written, "/".join(
                x.ticker for x in c.listings if x.pit_status is PitStatus.VERIFIED))
                for c in affected.companies
                if c.resolution_status is ResolutionStatus.LISTED_EQUITY
                and c.role in EXPOSURE_ROLES
                and any(x.pit_status is PitStatus.VERIFIED for x in c.listings))
            unverified = tuple(c.name_as_written for c in affected.companies
                               if c.resolution_status is ResolutionStatus.LISTED_EQUITY
                               and c.role in EXPOSURE_ROLES
                               and not any(x.pit_status is PitStatus.VERIFIED
                                           for x in c.listings))
            instruments = tuple(c.name_as_written for c in affected.instruments)
            stub = CardInputs(thesis=thesis, version=version, as_of=ctx.as_of, hyp=h,
                              article=ctx.article, prev=prev, claims=all_claims, links=links,
                              affected=affected, change_items=items, vs_prior=vs_prior,
                              novelty=novelty, priority=_PLACEHOLDER, evidence_direction=direction,
                              sources=sources, market_risks=risk_sents, relation_notes=rel_notes,
                              counter_claims=counter,
                              last_material_update=thesis.last_material_update)
            draft = compose_card(stub)
            by_role: dict[LinkRole, list[Claim]] = {}
            for lk in links:
                c = all_claims.get(lk.claim_id)
                if c is not None and c.span_verified:
                    by_role.setdefault(lk.role, []).append(c)
            state = ThesisState(
                reliability=max((ctx.reliability, *self._source_reliabilities(thesis.thesis_id)),
                                key=lambda r: {"high": 2, "medium": 1, "low": 0}[r]),
                supporting=tuple(by_role.get(LinkRole.SUPPORTS, [])),
                counter=tuple(by_role.get(LinkRole.CONTRADICTS, [])),
                dislocation=tuple(by_role.get(LinkRole.DISLOCATION, [])),
                catalyst=tuple(by_role.get(LinkRole.CATALYST, [])),
                listed_exposures=listed, instrument_exposures=instruments,
                transmission=draft.s03_transmission, horizon=thesis.horizon,
                stance=thesis.stance, verification_hold=bool(holds),
                hold_reasons=tuple(holds), retrieval=ctx.version.retrieval_state
                if ctx.version.retrieval_state is not RetrievalState.BLOCKED
                else RetrievalState.PARTIAL, kind=thesis.kind,
                sector_exposures=tuple(s.name for s in affected.sector_exposures),
                unverified_listings=unverified, as_of=ctx.as_of, published=published,
                data_report_articles=data_reports)
            pr = compute_priority(state, previous=previous, evidence_direction=direction,
                                  previous_factors=prev_factors)  # type: ignore[arg-type]
            return compose_card(CardInputs(**{**stub.__dict__, "priority": pr})), pr

        card, pr = make([])
        review_issues: list[VerificationIssue] = []
        anchors: dict[str, list[str]] = {}
        if self.reviewer is not None:
            sents = card_sentences(card)
            for _t, _p, cids in sents.values():  # a line carried from an earlier version keeps
                for cid in cids:                 # citing its claims — judge it against them
                    if cid not in all_claims and (c := self.store.claim(cid)):
                        all_claims[cid] = c
            review_issues, anchors = self._review_and_reanchor(ctx, thesis.thesis_id, version,
                                                               card, all_claims)
            if anchors:
                card = with_citations(card, anchors, all_claims)
                sents = card_sentences(card)
            blocks = [i for i in review_issues if i.severity is IssueSeverity.BLOCK]
            material = list(dict.fromkeys(
                sid for i in blocks if material_sentence(
                    sid := i.ref_id.partition(":")[2], sents.get(sid, ("",))[0])))
            if material:
                card, pr = make([f"review withheld {len(material)} decision-bearing "
                                 f"sentence(s): " + ", ".join(material)])
                if anchors:
                    card = with_citations(card, anchors, all_claims)
            with self.store.tx():
                for i in review_issues:
                    self.store.add_issue(i)
        self._link_cited(ctx, thesis.thesis_id, version, card, links, all_claims)
        diffs: list[FieldDiff] = []
        if prev is not None:
            diffs = [FieldDiff(field_id=f, change_class=c, old=o, new=n, claim_ids=ids)
                     for f, c, o, n, ids in diff_cards(prev, card, classes)]
        return ThesisVersion(
            thesis_id=thesis.thesis_id, version=version, as_of=ctx.as_of,
            created_at=datetime.now(tz=UTC), run_id=ctx.run_id, engine_version=ENGINE_VERSION,
            content=card, priority=pr, evidence_direction=direction,
            change_summary=change_summary, diffs=tuple(diffs), prior_content_sha=prev_sha,
            content_sha=card_sha(card))

    def _link_cited(self, ctx: ArticleContext, tid: str, version: int, card: CardContent,
                    links: list[ThesisClaimLink], claims: dict[str, Claim]) -> None:
        """Every claim the card cites is LINKED to the thesis. A citation outside the role lists
        — a source implication, a why-now view, a transmission step, a sector span, a re-anchored
        line — becomes a CONTEXT link, so the evidence trail QA re-derives from the registry is the
        one the card shows (found by QA on the real corpus, 2026-10-10)."""
        cited = [c for _t, _p, cids in card_sentences(card).values() for c in cids]
        cited += [c for se in card.s05_affected.sector_exposures for c in se.claim_ids]
        cited += [c for b in card.s05_affected.baskets for c in b.claim_ids]
        held = {lk.claim_id for lk in links} | {lk.claim_id for lk in self.store.links(tid)}
        extra = [ThesisClaimLink(
            thesis_id=tid, claim_id=cid, role=LinkRole.CONTEXT, first_version=version,
            change_class=ChangeClass.NO_MATERIAL_CHANGE,
            independence_group=claims[cid].origin_id or ctx.article.article_id)
            for cid in dict.fromkeys(cited) if cid not in held and cid in claims]
        if extra:
            with self.store.tx():
                for lk in extra:
                    self.store.add_link(lk)

    def _review_and_reanchor(self, ctx: ArticleContext, tid: str, version: int,
                             card: CardContent, claims: dict[str, Claim],
                             ) -> tuple[list[VerificationIssue], dict[str, list[str]]]:
        """Review; RE-ANCHOR every failing source-labelled line before anything is withheld —
        the reviewer's suggested spans, then a verified claim carrying its numbers or words, then
        the verbatim SOURCE PASSAGE that carries it (minted as a source-opinion claim, linked as
        context); a line the reviewer found only partly supported takes its suggested spans too.
        The re-anchored card is reviewed once more. Returns the issues that stand (plus an INFO
        record per re-anchored line) and the anchors applied. A MODEL INFERENCE line is never
        re-anchored (`with_citations` leaves it untouched)."""
        assert self.reviewer is not None
        out = self.reviewer(card, claims)
        issues, suggested = (out.issues, dict(out.anchors)) if isinstance(out, ReviewOutcome) \
            else (out, {})
        # only a VERIFIED claim — span AND number — may vouch for a line, whoever proposes it.
        # Observed 2026-10-10 (weekly sample, Nomura): the reviewer suggested two claims whose
        # number checks had failed as anchors; they kept a decision-bearing line from being
        # withheld, so unverified material reached the priority's hold test.
        pool = {cid: c for cid, c in claims.items()
                if c.span_verified and c.number_verified is not False}
        suggested = {sid: [c for c in ids if c in pool] for sid, ids in suggested.items()}
        sents = card_sentences(card)
        anchors: dict[str, list[str]] = {}
        for i in issues:
            if i.severity is not IssueSeverity.BLOCK or i.scope != "card_sentence":
                continue
            sid = i.ref_id.partition(":")[2]
            if sid not in sents or sid in anchors:
                continue
            text, _prov, cids = sents[sid]
            extra = suggested.get(sid)
            if not extra and i.code in _REANCHORABLE:
                extra = reanchor_sentence(text, cids, pool)
            if not extra and i.code == "REVIEW_UNSUPPORTED":
                extra = overlap_anchor(text, cids, pool)  # candidates; the re-review decides
            if not extra and i.code == "REVIEW_UNSUPPORTED":
                got = passage_anchor(text, ctx.version.blocks)
                if got is not None:
                    pc = passage_claim(got[0], got[1], article_id=ctx.article.article_id,
                                       article_version_id=ctx.version.version_id,
                                       origin_id=None, run_id=ctx.run_id)
                    if pc.span_verified:
                        claims[pc.claim_id] = pool[pc.claim_id] = pc
                        with self.store.tx():
                            self.store.add_claim(pc)
                        extra = [pc.claim_id]
            if extra:
                anchors[sid] = extra
        partial = {i.ref_id.partition(":")[2] for i in issues if i.code == "REVIEW_PARTIAL"}
        for sid, ids in suggested.items():
            if sid in partial and sid not in anchors:
                anchors[sid] = ids
        if not anchors:
            return issues, {}
        card2 = with_citations(card, anchors, claims)
        out2 = self.reviewer(card2, claims)
        issues2 = out2.issues if isinstance(out2, ReviewOutcome) else out2
        still = {i.ref_id.partition(":")[2] for i in issues2
                 if i.severity is IssueSeverity.BLOCK and i.scope == "card_sentence"}
        tid = card.header.thesis_id
        first = {i.ref_id.partition(":")[2]: i for i in issues
                 if i.scope == "card_sentence" and (i.severity is IssueSeverity.BLOCK
                                                    or i.code == "REVIEW_PARTIAL")}
        notes = [self._issue(ctx, "card_sentence", f"{tid}:{sid}", IssueSeverity.INFO,
                             "SENTENCE_REANCHORED",
                             f"{sid}: first check {first[sid].code} ({first[sid].detail[:160]}) "
                             f"— re-anchored to {', '.join(extra)}; after re-anchoring: "
                             + ("STILL UNSUPPORTED — withheld" if sid in still
                                else "supported"))
                 for sid, extra in anchors.items() if sid in first]
        return issues2 + notes, anchors

    def _roles(self, h: VerifiedHypothesis | _ChallengeHyp,
               risks: list[VerifiedRisk]) -> dict[str, LinkRole]:
        roles: dict[str, LinkRole] = {}
        if isinstance(h, VerifiedHypothesis):
            for attr, role in _ROLE_FOR:
                for cid in getattr(h, attr):
                    if cid not in roles:
                        roles[cid] = role
            for r in risks:
                for cid in r.claim_ids:
                    roles.setdefault(cid, LinkRole.RISK)
        return roles

    def _headline_claims(self, h: VerifiedHypothesis,
                         claims: dict[str, Claim]) -> tuple[list[str], int]:
        """(the claims 02 WHAT CHANGED lists, how many distinct pieces of evidence exist). One
        claim per evidence identity (fingerprint) — two quotes of one figure are one change."""
        ordered = list(dict.fromkeys(h.strongest + h.dislocation + h.supporting))
        seen: set[str] = set()
        uniq = []
        for c in ordered:
            if claims[c].fingerprint not in seen:
                seen.add(claims[c].fingerprint)
                uniq.append(c)
        metric = [c for c in uniq if claims[c].kind in (ClaimKind.METRIC, ClaimKind.FORECAST,
                                                        ClaimKind.EVENT)]
        rest = [c for c in uniq if c not in metric]
        return (metric + rest)[:HEADLINE_ITEMS], len(uniq)

    def _risk_sentences(self, risks: list[VerifiedRisk],
                        claims: dict[str, Claim]) -> list[CardSentence]:
        out = []
        for r in risks:
            out.append(CardSentence(text=f"{r.raw.statement} (scope: {r.raw.scope_qualification})",
                                    provenance=_label(r.claim_ids, claims),
                                    claim_ids=tuple(r.claim_ids)))
        return out

    def _sources(self, tid: str, ctx: ArticleContext, links: list[ThesisClaimLink],
                 claims: dict[str, Claim], current: ChangeClass) -> list[SourceRef]:
        """One line per contributing article. The article building THIS version shows the
        contribution it makes now — its contribution row is written only after the card is
        built, and the fallback had shown every update as an initial record (observed
        2026-10-10: TrendForce's independent confirmation of a SemiAnalysis thesis)."""
        contribs = {c.article_id: c for c in self.store.contributions(tid)}
        art_ids = list(dict.fromkeys([*contribs, ctx.article.article_id]))
        out: list[SourceRef] = []
        for aid in art_ids:
            a = ctx.article if aid == ctx.article.article_id else self.store.article(aid)
            if a is None:
                continue
            cids = tuple(lk.claim_id for lk in links if lk.claim_id in claims
                         and claims[lk.claim_id].article_id == aid)
            origins = sorted({origin_label(claims[c].attributed_source_text) for c in cids})
            vers = self.store.article_versions(aid)
            state = vers[-1].retrieval_state if vers else ctx.version.retrieval_state
            dated = [(i, v) for i, v in enumerate(vers, 1) if v.document_date]
            vdates = (tuple(f"version {i} ({v.retrieval_state.value.lower()}): "
                            f"{v.document_date.isoformat() if v.document_date else '?'} — "
                            f"{v.document_date_source or '?'}" for i, v in dated)
                      if len({v.document_date for _i, v in dated}) > 1 else ())
            contrib = (current if aid == ctx.article.article_id
                       else contribs[aid].contribution if aid in contribs
                       else ChangeClass.NOVELTY_UNVERIFIED)
            out.append(SourceRef(
                article_id=aid, title=a.title, authors=tuple(
                    x.name + (f" ({x.title})" if x.title else "") for x in a.authors),
                authors_status=a.authors_status, publisher=a.publisher,
                published_at=a.published_at, published_status=a.published_status,
                url=a.canonical_url, article_class=a.article_class, retrieval_state=state,
                upstream_origins=tuple(origins), claim_ids=cids, contribution=contrib,
                version_dates=vdates))
        return out

    def _source_reliabilities(self, tid: str) -> list[str]:
        return []  # contributing channels' tiers are folded in by the pipeline's ctx.reliability

    def _hold_reasons(self, links: list[ThesisClaimLink],
                      claims: dict[str, Claim]) -> list[str]:
        out: list[str] = []
        for lk in links:
            c = claims.get(lk.claim_id)
            if c is not None and not c.span_verified and lk.role is not LinkRole.RISK:
                out.append(f"{lk.claim_id} failed span verification")
        return out

    def _evidence_of(self, tid: str) -> list[Claim]:
        out: list[Claim] = []
        for lk in self.store.links(tid):
            if lk.role in (LinkRole.SUPPORTS, LinkRole.DISLOCATION, LinkRole.CATALYST):
                c = self.store.claim(lk.claim_id)
                if c is not None and c.span_verified:
                    out.append(c)
        return out

    def _relations_for(self, t: Thesis, ctx: ArticleContext,
                       own: list[Claim]) -> list[ThemeRelation]:
        """How a new thesis relates to every other. COMPETING — the only relation whose evidence
        is filed as CONTRADICTS — needs a DIRECT contradiction: the SAME claim (node, mechanism,
        segment, geography, timeframe) predicted the opposite way. Opposite directions that
        differ in any of those are RELATED: linked, never counter-evidence, never a weakening
        (review of PR #703, round 3: a fall in utility share prices does not contradict rising
        demand for on-site power). Same-direction theses that are not the same claim are
        ADJACENT SUPPORT: context, never a strengthening."""
        rels: list[ThemeRelation] = []
        now = datetime.now(tz=UTC)
        seg_label = {sg.id: sg.label for sg in self.taxonomy.segments}
        t_windows = evidence_windows(own, ctx.as_of)
        cids: tuple[str, ...] = ()
        for o in self.store.theses():
            if o.thesis_id == t.thesis_id:
                continue
            rel: RelationType | None = None
            role = ""
            why = ""
            opposite = {o.key_direction, t.key_direction} == {Direction.POSITIVE,
                                                              Direction.NEGATIVE}
            same_dir = o.key_direction == t.key_direction
            if o.key_node == t.key_node:
                diffs = claim_differences(t, o, t_windows,
                                          evidence_windows(self._evidence_of(o.thesis_id),
                                                           ctx.as_of), seg_label)
                if opposite and not diffs:
                    # the same thesis claim predicted the opposite way — but a thesis is only
                    # weakened by CLAIMS that directly contradict its own (contradiction.py)
                    asmt = assess(own, self._evidence_of(o.thesis_id),
                               products=list(self.taxonomy.products_of(t.key_node)),
                               ref=ctx.as_of, overlap_geo=geographies_overlap,
                               geo_ch=t.key_geography, geo_inc=o.key_geography)
                    basis = (f"the same thesis claim (node {t.key_node}, mechanism "
                             f"{t.key_mechanism}"
                             + (f", segment {t.key_segment}" if t.key_segment else "")
                             + ", overlapping geography and timeframe) predicted the opposite way")
                    if asmt.verdict == CONTRADICTS:
                        rel, role = RelationType.COMPETING, EvidenceRole.CONTRADICTION.value
                        cids = tuple(asmt.contradicting)
                        first = next(p for p in asmt.pairs if p.kind == CONTRADICTS)
                        why = (f"a direct contradiction — {basis}; {len(cids)} claim(s) directly "
                               f"contradict its evidence ({first.challenger} vs "
                               f"{first.incumbent}: {'; '.join(first.reasons)}) — only those "
                               f"are filed against it; linked, never merged")
                    elif asmt.verdict == AMBIGUOUS:
                        rel = RelationType.COMPETING
                        role = EvidenceRole.CONTRADICTION_REVIEW.value
                        first_a = asmt.ambiguous[0]
                        why = (f"held for review — {basis}, but no claim pair is clearly "
                               f"comparable ({first_a.challenger} vs {first_a.incumbent}: "
                               f"{'; '.join(first_a.reasons)}); nothing is filed against it "
                               f"automatically")
                    else:
                        rel, role = RelationType.RELATED, EvidenceRole.RELATED.value
                        first_c = asmt.pairs[0] if asmt.pairs else None
                        why = (f"{basis}, but every claim pair is compatible"
                               + (f" ({first_c.challenger} vs {first_c.incumbent}: "
                                  f"{'; '.join(first_c.reasons)})" if first_c else "")
                               + " — related, never used as counter-evidence")
                elif opposite:
                    rel, role = RelationType.RELATED, EvidenceRole.RELATED.value
                    why = (f"the opposite direction on the same value-chain node, but not the "
                           f"same claim — {'; '.join(diffs)} — related, never used as "
                           f"counter-evidence")
                elif diffs:
                    rel = RelationType.SIBLING
                    role = EvidenceRole.ADJACENT_SUPPORT.value if same_dir else ""
                    why = (f"same value-chain node, not the same claim — {'; '.join(diffs)}"
                           + (" — adjacent support: context, never a confirmation"
                              if same_dir else ""))
                elif same_dir:  # the same claim at an overlapping but different geography
                    rel, role = RelationType.SIBLING, EvidenceRole.ADJACENT_SUPPORT.value
                    why = (f"the same claim at an overlapping but different geography "
                           f"({t.key_geography} vs {o.key_geography}) — a separate thesis, never "
                           f"merged; adjacent support, never an automatic confirmation")
            elif o.key_node.startswith(t.key_node + ".") or t.key_node.startswith(o.key_node + "."):
                rel = RelationType.PARENT_CHILD
                role = (EvidenceRole.ADJACENT_SUPPORT.value if same_dir
                        else EvidenceRole.RELATED.value if opposite else "")
                why = (f"{o.key_node} and {t.key_node} are parent and child economics — never "
                       f"merged" + (" — adjacent support, never a confirmation" if same_dir
                                    else " — related, never counter-evidence" if opposite else ""))
            elif "." in o.key_node and "." in t.key_node and \
                    o.key_node.split(".")[0] == t.key_node.split(".")[0]:
                rel, why = RelationType.SIBLING, (f"same parent sector "
                                                  f"({o.key_node.split('.')[0]}), different child "
                                                  f"economics ({o.key_node} vs {t.key_node})")
            if t.status is ThesisStatus.REVIEW_NEEDED and rel is None:
                a = set(re.findall(r"[a-z]{4,}", t.title.lower()))
                b = set(re.findall(r"[a-z]{4,}", o.title.lower()))
                if a and b and len(a & b) / len(a | b) >= 0.3:
                    rel, why = RelationType.REVIEW_NEEDED, ("lexically similar to an existing "
                                                            "thesis — a human decides; similarity "
                                                            "never merges")
            if rel is None:
                continue
            pair = sorted([t.thesis_id, o.thesis_id])
            rels.append(ThemeRelation(
                relation_id="TR-" + _sha(*pair, rel.value)[:14], from_thesis=t.thesis_id,
                to_thesis=o.thesis_id, relation=rel, reason=why, run_id=ctx.run_id,
                created_at=now, evidence_role=role,
                claim_ids=cids if role == EvidenceRole.CONTRADICTION.value else ()))
            cids = ()
        return rels

    def _event(self, ctx: ArticleContext, tid: str, version: int | None, etype: str,
               detail: str, diffs: tuple[FieldDiff, ...] = ()) -> ChangeEvent:
        return ChangeEvent(event_id="CE-" + _sha(tid, str(version), etype, ctx.run_id,
                                                 ctx.version.version_id)[:14],
                           thesis_id=tid, version=version, event_type=etype, run_id=ctx.run_id,
                           as_of=ctx.as_of, created_at=datetime.now(tz=UTC), detail=detail,
                           diffs=diffs)

    def _issue(self, ctx: ArticleContext, scope: str, ref: str, sev: IssueSeverity, code: str,
               detail: str) -> VerificationIssue:
        return VerificationIssue(issue_id="VI-" + _sha(ctx.run_id, scope, ref, code)[:14],
                                 run_id=ctx.run_id, scope=scope, ref_id=ref, severity=sev,
                                 code=code, detail=detail, created_at=datetime.now(tz=UTC))


def _label(ids: list[str], claims: dict[str, Claim]) -> Provenance:
    """The label of a line restating source claims: the WEAKEST of what they are (measured
    observation / forecast / source opinion); MODEL INFERENCE when none verified."""
    return label_for(ids, claims) or Provenance.MODEL_INFERENCE


#: 02 WHAT CHANGED lists at most this many items; the rest are counted in a closing item that
#: points at 04 KEY EVIDENCE (every claim stays in the ledger and the evidence table).
HEADLINE_ITEMS = 6
UPDATE_ITEMS = 10


def _more_item(shown: int, total: int, article_id: str) -> ChangeItem:
    return ChangeItem(change_class=ChangeClass.NOVELTY_UNVERIFIED,
                      text=f"showing {shown} of {total} pieces of evidence from {article_id} — "
                           f"the rest are in 04 KEY EVIDENCE and the evidence ledger",
                      provenance=Provenance.UNKNOWN, article_id=article_id)


#: Sentences the DECISION rests on: the bottom line, the what-changed facts, the decision itself,
#: and dislocation evidence (a RESEARCH NOW condition). A review BLOCK on one of these HOLDS
#: promotion ("hold promotion if material claims lack source evidence"). A blocked NARRATIVE
#: sentence — transmission hypothesis, why-now prose, a risk line — is withheld from the card and
#: logged, but the action rests on the verified structured evidence, not on that prose.
MATERIAL_SECTIONS = ("s01.", "s02.", "s08.")


def material_sentence(sid: str, text: str) -> bool:
    return sid.startswith(MATERIAL_SECTIONS) or text.startswith("Dislocation evidence:")


@dataclass
class _ChallengeHyp:
    claim_ids: list[str]


def _num_close(a: float, b: float) -> bool:
    return abs(a - b) <= 0.05 * max(abs(a), abs(b), 1e-9)


def classify_claim(new: Claim, role: LinkRole, held: list[Claim]) -> tuple[ChangeClass, str]:
    same_fp = [e for e in held if e.fingerprint == new.fingerprint]
    if same_fp:
        return ChangeClass.REPEATED, (f"same measure, value and upstream origin as "
                                      f"{same_fp[0].claim_id} — attribution, not new evidence")
    if role is LinkRole.CONTRADICTS:
        return ChangeClass.CONTRADICTORY, "the source states evidence against this thesis"
    same_measure = [e for e in held if e.measure_key == new.measure_key
                    and not e.measure_key.startswith("stmt|")]
    if same_measure:
        e = same_measure[-1]
        scope_note = (f"held: {e.scope or '—'} / {e.metric or '—'} / {e.period or '—'} / "
                      f"{e.unit or '—'} ({e.claim_id}); new: {new.scope or '—'} / "
                      f"{new.metric or '—'} / {new.period or '—'} / {new.unit or '—'}")
        if new.measure_key.startswith("event|"):
            if (new.period or "") != (e.period or ""):
                return ChangeClass.TIMING_CHANGE, (f"the dated event moved: "
                                                   f"{e.period} → {new.period}; both claims kept "
                                                   f"— {scope_note}")
            return ChangeClass.INDEPENDENT_CONFIRMATION if e.origin_id != new.origin_id else \
                ChangeClass.REPEATED, f"same event and timing — {scope_note}"
        if e.origin_id == new.origin_id:
            if new.measured_as_of and e.measured_as_of and new.measured_as_of > e.measured_as_of:
                return ChangeClass.NEW, f"a later reading of the same series — {scope_note}"
            return ChangeClass.CORRECTION, (f"same origin and measure, different value "
                                            f"({e.value_text} → {new.value_text}) — "
                                            f"{scope_note}")
        if new.value is not None and e.value is not None:
            if _num_close(new.value, e.value):
                return ChangeClass.INDEPENDENT_CONFIRMATION, (f"a different origin reports the "
                                                              f"same figure — {scope_note}")
            return ChangeClass.CONTRADICTORY, (f"a different origin reports a different figure "
                                               f"({e.value_text} vs {new.value_text}) — "
                                               f"{scope_note}")
        return ChangeClass.INDEPENDENT_CONFIRMATION, (f"same measure, different origin — "
                                                      f"{scope_note}")
    if any(e.origin_id == new.origin_id for e in held):
        return ChangeClass.NEW, ("new evidence from an origin already counted — not an "
                                 "independent confirmation")
    return ChangeClass.NEW, "new evidence from an origin the thesis did not yet hold"


def evidence_direction_of(classes: dict[str, ChangeClass],
                          roles: dict[str, LinkRole]) -> EvidenceDirection:
    pos = any(c in (ChangeClass.NEW, ChangeClass.INDEPENDENT_CONFIRMATION)
              and roles.get(cid) is not LinkRole.CONTRADICTS for cid, c in classes.items())
    neg = any(c in (ChangeClass.CONTRADICTORY, ChangeClass.CORRECTION, ChangeClass.TIMING_CHANGE)
              for c in classes.values())
    if pos and neg:
        return EvidenceDirection.MIXED
    if neg:
        return EvidenceDirection.WEAKER
    if pos:
        return EvidenceDirection.STRONGER
    return EvidenceDirection.UNCHANGED


def dominant_class(classes: dict[str, ChangeClass]) -> ChangeClass:
    for c in (ChangeClass.CONTRADICTORY, ChangeClass.CORRECTION, ChangeClass.TIMING_CHANGE,
              ChangeClass.INDEPENDENT_CONFIRMATION, ChangeClass.NEW, ChangeClass.REPEATED):
        if c in classes.values():
            return c
    return ChangeClass.NO_MATERIAL_CHANGE


def event_type(prev: ResearchAction, new: ResearchAction,
               classes: dict[str, ChangeClass]) -> str:
    if ACTION_RANK[new] > ACTION_RANK[prev]:
        return "UPGRADED"
    if ACTION_RANK[new] < ACTION_RANK[prev]:
        return "DOWNGRADED"
    if any(c in (ChangeClass.CONTRADICTORY, ChangeClass.CORRECTION, ChangeClass.TIMING_CHANGE)
           for c in classes.values()):
        return "CHALLENGED"
    return "UPDATED"


_PLACEHOLDER = ResearchPriority(
    research_action=ResearchAction.WATCH, evidence_direction=EvidenceDirection.NEW,
    investment_readiness=InvestmentReadiness.NOT_ASSESSED, factors=(),
    rules_fired=("placeholder — replaced before persisting",), previous_action=None,
    change_reason="", valuation_status="")


def _competing_basis(inc: Thesis, ch: Thesis | None) -> str:
    """Why two theses are COMPETING: the same claim predicted the opposite way."""
    if ch is None:
        return "a direct contradiction of this thesis's claim"
    return (f"a direct contradiction — the same claim (node {inc.key_node}, mechanism "
            f"{inc.key_mechanism}" + (f", segment {inc.key_segment}" if inc.key_segment else "")
            + ", overlapping geography and timeframe) predicted the opposite way — linked, never "
              "merged")


_RELATION_LABEL = {
    (RelationType.COMPETING, EvidenceRole.CONTRADICTION.value):
        "CONTRADICTION — competing hypothesis",
    (RelationType.COMPETING, EvidenceRole.CONTRADICTION_REVIEW.value):
        "COMPETING, held for review (not applied) —",
    (RelationType.RELATED, EvidenceRole.RELATED.value): "RELATED, not a contradiction —",
    (RelationType.SIBLING, EvidenceRole.ADJACENT_SUPPORT.value): "ADJACENT SUPPORT (sibling) —",
    (RelationType.PARENT_CHILD, EvidenceRole.ADJACENT_SUPPORT.value):
        "ADJACENT SUPPORT (parent / child) —",
    (RelationType.PARENT_CHILD, EvidenceRole.RELATED.value):
        "RELATED (parent / child), not a contradiction —",
}


def relation_label(r: ThemeRelation) -> str:
    """The card's words for a registry link: its evidence role first, the structure after."""
    return _RELATION_LABEL.get((r.relation, r.evidence_role), f"{r.relation.value} with")
