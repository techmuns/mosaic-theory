"""The living-thesis engine — match, version, attribute, re-prioritise. Deterministic throughout.

IDENTITY. A thesis is keyed by (value-chain node, profit mechanism, direction, geography) from the
controlled taxonomy. Same key → the SAME thesis is updated; nothing else ever merges. Similarity is
never a merge licence: a different mechanism on the same node is a SIBLING, the opposite direction
is COMPETING (linked, never mashed into one), a parent and a child node are PARENT_CHILD, theses
that only share a broader area are never linked pair by pair (the area is read from their keys —
U43), and an `other` hypothesis is created REVIEW_NEEDED with lexically similar theses flagged —
never merged.
The thesis id is a hash of the key, so a re-run on an empty registry reproduces the same ids, and a
populated registry MATCHES an earlier thesis instead of minting a new id.

WHAT AN INCOMING CLAIM IS, relative to what the thesis already holds:
  repeated                — same claim, or same measure + value + upstream ORIGIN (attribution
                            only), or one sentence and figure read again from another VERSION of
                            the same article (a re-read, a preview's full text), however labelled
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
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from vinci.theme_intelligence.cards import (
    LABEL_CLOSE,
    LABEL_OPEN,
    MORE_POINTER,
    CardInputs,
    affected_from,
    capped_conditionals,
    capped_label,
    card_sha,
    compose_card,
    counted_exposures,
    diff_cards,
    labelled,
    origin_label,
    refile_price_moves,
    replace_sentence,
    sector_exposures_from,
    with_citations,
)
from vinci.theme_intelligence.config import ENGINE_VERSION, STALE_AFTER_DAYS, Segment, Taxonomy
from vinci.theme_intelligence.contradiction import (
    AMBIGUOUS,
    CONTRADICTS,
    assess,
    products_in,
    products_of,
)
from vinci.theme_intelligence.priority import ThesisState, compute_priority
from vinci.theme_intelligence.schemas import (
    ACTION_RANK,
    EXPOSURE_ROLES,
    MATERIAL_CLASSES,
    AffectedCompany,
    AffectedView,
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
    SectorExposure,
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
    same_area,
)
from vinci.theme_intelligence.store import Store
from vinci.theme_intelligence.timewindow import Window, window_of
from vinci.theme_intelligence.verify import (
    ReviewOutcome,
    VerifiedExtraction,
    VerifiedHypothesis,
    VerifiedRisk,
    bare_label,
    card_sentences,
    deterministic_card_checks,
    label_for,
    locate,
    norm_name,
    overlap_anchor,
    passage_anchor,
    passage_claim,
    reanchor_sentence,
    same_sentence_reread,
)

#: ONE vocabulary of place names (U48: the identity key and the overlap test had two, and
#: disagreed) — `norm_geo` keys a thesis by it, `geographies_overlap` reads it
_GEO = {"us": "US", "u.s.": "US", "u.s": "US", "united states": "US", "usa": "US",
        "america": "US", "global": "Global", "worldwide": "Global", "world": "Global",
        "china": "China", "europe": "Europe", "eu": "Europe", "japan": "Japan", "asia": "APAC",
        "apac": "APAC", "asia pacific": "APAC", "taiwan": "Taiwan", "korea": "Korea",
        "south korea": "Korea", "india": "India", "uk": "UK", "united kingdom": "UK",
        "latin america": "Latin America", "south america": "Latin America",
        "central america": "Latin America"}
#: names inside a region: they overlap it, but a thesis about them keeps its own key
_PART_OF = {"north america": "US", "texas": "US"}
#: "Global ex-US", "Asia excluding Japan": what follows is LEFT OUT of the place
_EXCLUDING = re.compile(r"\s*(?:\bex\b[-\s.]*|\bexcluding\b|\bexcept\b)\s*", re.I)
#: "(esp. Texas)", "(led by …)": an emphasis inside the place, never another place
_EMPHASIS = re.compile(r"\s*\((?:esp\.?|especially|notably|mainly|primarily|led by|"
                       r"incl\.?|including)\b[^)]*\)", re.I)
_STANCE_RANK = {StanceInSource.ASSERTED: 3, StanceInSource.REPORTED_VIEW: 2,
                StanceInSource.CONDITIONAL: 1, StanceInSource.SPECULATIVE: 0}
_ROLE_FOR = (("dislocation", LinkRole.DISLOCATION), ("catalyst", LinkRole.CATALYST),
             ("supporting", LinkRole.SUPPORTS), ("strongest", LinkRole.SUPPORTS),
             ("counter", LinkRole.CONTRADICTS))


def norm_geo(g: str) -> str:
    """The geography a thesis is KEYED by. A known name is its region; an exclusion of known
    names is one key however it is spelt ("Global ex-U.S." and "Global ex-US" were two); an
    emphasis inside a place is the place ("United States (esp. Texas)" was its own key). Any
    other text — a list, an unknown place — is kept as written."""
    k = re.sub(r"\s+", " ", _EMPHASIS.sub("", g).strip().lower())
    m = _EXCLUDING.search(k)
    if m and m.start() > 0:
        head, tail = _GEO.get(k[:m.start()].strip()), _GEO.get(k[m.end():].strip(" ."))
        return f"{head} ex-{tail}" if head and tail else g.strip()
    return _GEO.get(k, g.strip() or "Unspecified")


def _published(ctx: ArticleContext) -> date | None:
    """The source's publication date — None when it states none (never the run's as-of)."""
    return ctx.article.published_at.date() if ctx.article.published_at else None


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d is not None else None


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


def segment_of(h: VerifiedHypothesis, claims: dict[str, Claim], taxonomy: Taxonomy,
               product: str = "") -> str:
    """The segment(s) within the node the hypothesis is ABOUT (`subject_segment`), from its
    statement, its product, the sector spans the source names, then its verified evidence."""
    quotes = [claims[c].quote for c in (*h.supporting, *h.dislocation, *h.catalyst)
              if c in claims and claims[c].span_verified]
    return subject_segment(h.raw.value_chain_node, h.raw.title, product,
                           [x.quote for x in h.sectors], quotes, taxonomy)


def subject_segment(node: str, statement: str, product: str, exposure: Sequence[str],
                    quotes: Sequence[str], taxonomy: Taxonomy) -> str:
    """The segment(s) a thesis is ABOUT, in order: (1) the economic subject its statement names;
    (2) the segment of its product, or of the sectors the source names as exposed; (3) segments
    at least PRODUCT_MIN_SHARE of its verified quotes name. "" — unassigned — rather than a wrong
    one: an incidental comparison, a customer application or industry background never sets it
    (observed 2026-10-12: the transformer thesis keyed `onsite_generation` from one CCGT mention
    in 67 cited claims, under the rule that took every segment any quote named)."""
    segs = taxonomy.segments_of(node)
    if not segs:
        return ""
    found = _segments_named(statement, segs)
    if not found and product:
        found = _segments_named(" ".join(next((p.terms for p in taxonomy.products_of(node)
                                               if p.id == product), ())), segs)
    if not found and exposure:
        found = _segments_named(" ".join(exposure), segs)
    if not found and quotes:
        counts = Counter(s for q in quotes for s in _segments_named(q, segs))
        found = {s for s, n in counts.items() if n >= PRODUCT_MIN_SHARE * len(quotes)}
    return "+".join(sorted(found))


def _segments_named(text: str, segs: Sequence[Segment]) -> set[str]:
    return {sg.id for sg in segs
            if any(re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", text, re.I)
                   for term in sg.terms)}


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


def thesis_key(h: VerifiedHypothesis, segment: str = "", product: str = "") -> str:
    raw = h.raw
    return identity_key(raw.value_chain_node, raw.mechanism, raw.direction.value,
                        norm_geo(raw.geography), segment, review_tag(h), product)


#: Regions a geography string names. "Global" overlaps every region; APAC contains its members.
#: Regions a geography string names: the one vocabulary, without its "Global" names (Global
#: overlaps every region), with the names inside a region. APAC contains its members.
_REGION_WORDS = {**{k: v for k, v in _GEO.items() if v != "Global"}, **_PART_OF}
_REGION_CONTAINS = {"APAC": {"China", "Japan", "Taiwan", "Korea", "India"}}


def _region_set(part: str) -> set[str]:
    """The regions one part of a geography names — the LONGEST name first, so "Latin America"
    is never read as "America" (the US)."""
    if re.search(r"\b(global|world|worldwide)\b", part):
        return {"*"}
    found: set[str] = set()
    rest = part
    for k in sorted(_REGION_WORDS, key=len, reverse=True):
        pat = rf"(?<![a-z]){re.escape(k)}(?![a-z])"
        if re.search(pat, rest):
            found.add(_REGION_WORDS[k])
            rest = re.sub(pat, " ", rest)
    return found or {part.strip(" .") or "unspecified"}


def _regions(g: str) -> tuple[set[str], set[str]]:
    """(the regions a geography names, the regions it LEAVES OUT): "Global ex-US" is everywhere
    but the US; "Asia ex-Japan" is APAC without Japan (U48: both overlapped what they exclude)."""
    low = _EMPHASIS.sub("", g).lower()
    m = _EXCLUDING.search(low)
    if m and m.start() > 0:
        return _region_set(low[:m.start()]), _region_set(low[m.end():])
    return _region_set(low), set()


def _within(r: str, regions: set[str]) -> bool:
    return r in regions or any(r in _REGION_CONTAINS.get(x, ()) for x in regions)


def _places(inc: set[str], exc: set[str]) -> set[str]:
    """The named regions and their members, less what is left out."""
    every = inc | {m for x in inc for m in _REGION_CONTAINS.get(x, ())}
    return {r for r in every if not _within(r, exc)}


def geographies_overlap(a: str, b: str) -> bool:
    """Whether two theses can be about the same place: equal or containing regions, or a Global
    one that does not leave the other's places out."""
    (ia, ea), (ib, eb) = _regions(a), _regions(b)
    if "*" in ia and "*" in ib:
        return True
    if "*" in ia or "*" in ib:
        (_ig, eg), (io, eo) = ((ia, ea), (ib, eb)) if "*" in ia else ((ib, eb), (ia, ea))
        return any(not _within(r, eg) for r in _places(io, eo))
    return bool(_places(ia, ea) & _places(ib, eb))


def evidence_windows(claims: list[Claim], ref: date,
                     published: Mapping[str, date] | None = None) -> list[Window]:
    """The calendar windows a thesis's verified evidence states (period first; a forecast or
    event may state it in its quote) — a "since X" window ending at its article's date."""
    out: list[Window] = []
    for c in claims:
        to = (published or {}).get(c.article_id)
        w = window_of(c.period, ref, source_date=to)
        if w is None and (c.epistemic is Epistemic.FORECAST
                          or c.kind in (ClaimKind.FORECAST, ClaimKind.EVENT)):
            w = window_of(c.quote, ref, source_date=to)
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
class SentenceCorrection:
    """An ANALYST CORRECTION of one card line (`Engine.reassess`): the operator's text for line
    `sentence_id` (as `verify.card_sentences` numbers it), citing verified claims the thesis
    already links, with the reason recorded. J.P. Morgan acceptance, 2026-10-12: the bottom line
    read "beat expectations for eight consecutive quarters" where the source projects an eighth
    consecutive quarter of double-digit growth."""
    thesis_id: str
    sentence_id: str
    text: str
    claim_ids: tuple[str, ...]
    reason: str


class CorrectionError(ValueError):
    """A correction that cites no verified linked claim, names no card line, or fails the card's
    deterministic checks — refused, never applied in part."""


#: verification-issue codes a re-grade carries to the lines they were made on (besides the card
#: review's REVIEW_*); the deterministic card checks are recomputed instead
CARRIED_CODES = frozenset({"SENTENCE_REANCHORED", "ANALYST_CORRECTION"})


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
                 reviewer: Reviewer | None = None,
                 reliability_of: Callable[[str], str | None] | None = None,
                 relist: Callable[[AffectedCompany, date], AffectedCompany] | None = None
                 ) -> None:
        self.store = store
        self.taxonomy = taxonomy
        self.reviewer = reviewer
        #: a channel's CURRENT reliability tier (sources.toml), for `reassess` — None (no lookup,
        #: or a channel no longer configured): the tier the previous version recorded
        self.reliability_of = reliability_of
        #: a named listed company resolved AGAIN, as of a date — for one whose listing no line
        #: verifies (resolved before point-in-time verification, or with the SEC unreachable);
        #: None (an engine without the pipeline's resolver): the stored listing stands
        self.relist = relist
        self.node_label = {n.id: n.label for n in taxonomy.nodes}
        #: thesis id -> when this registry FIRST ingested it, for a `state pull` replay: a thesis
        #: it re-creates keeps its original date, never the replay's clock
        self.first_ingested: dict[str, datetime] = {}
        #: the last `apply`: hypothesis local id -> (thesis id, "" or how it was merged)
        self.destinations: dict[str, tuple[str, str]] = {}
        #: the last `apply`: earlier versions' theses it re-verified and re-assessed (_reverify)
        self.reverified: list[str] = []
        #: what a deferred `_build_version` held back: (review issues, context links)
        self.deferred: tuple[list[VerificationIssue], list[ThesisClaimLink]] = ([], [])

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
        self.destinations = {}
        self.reverified = []
        if ctx.article.published_at is None:
            st.add_issue(self._issue(
                ctx, "article", ctx.article.article_id, IssueSeverity.WARN, "UNDATED_SOURCE",
                f"{ctx.article.article_id} states no publication date: a thesis it creates starts "
                f"its clock at this run's as-of {ctx.as_of.isoformat()}; a thesis it updates keeps "
                f"its own last-evidence date — the run date is never taken for the source's"))

        for h in ve.hypotheses:  # the record type is checked before any thesis is touched
            kind, why = record_kind(h, claims)
            if why:
                h.raw = h.raw.model_copy(update={"kind": kind})
                st.add_issue(self._issue(ctx, "hypothesis", f"{ctx.version.version_id}:"
                                         f"{h.raw.local_id}", IssueSeverity.INFO,
                                         "RECORD_KIND_CORRECTED", f"“{h.raw.title}”: {why}"))
        groups: dict[str, list[VerifiedHypothesis]] = {}
        segments: dict[str, str] = {}
        products: dict[str, str] = {}
        # theses this article's EARLIER versions contributed to (before this version applies)
        earlier = [tid for tid in dict.fromkeys(c.thesis_id for c in st.contributions(
            article_id=ctx.article.article_id))
            if (prior_t := st.thesis(tid)) is not None and not prior_t.retired]  # retired: never
        for h in ve.hypotheses:
            seg = segment_of(h, claims, self.taxonomy, self.product_signature(h, claims))
            key = thesis_key(h, seg)
            groups.setdefault(key, []).append(h)
            segments[key] = seg
        # ONE KEY, TWO TECHNOLOGIES: a hypothesis whose evidence is all its own AND names another
        # product than the first's is a different proposition — split, never merged (observed
        # 2026-10-12: fuel-cell adoption merged into gas-generation equipment, 0 of 17 shared)
        for key, hs in list(groups.items()):
            first = self.product_signature(hs[0], claims)
            for x in list(hs[1:]):
                shared, distinct = _evidence_overlap(hs[0], x)
                px = self.product_signature(x, claims)
                if shared == 0 and distinct and px and first and px != first:
                    k2 = thesis_key(x, segments[key], px)
                    hs.remove(x)
                    groups.setdefault(k2, []).append(x)
                    segments[k2], products[k2] = segments[key], px
                    moved = self._risks_follow_product(ve.risks, hs[0], x, first, px)
                    st.add_issue(self._issue(
                        ctx, "hypothesis", k2, IssueSeverity.INFO, "PRODUCT_SPLIT",
                        f"“{x.raw.title}” and “{hs[0].raw.title}” share one identity key but no "
                        f"supporting claim, and their evidence names different products ({px} vs "
                        f"{first}) — separate theses"
                        + (f"; {moved} market risk(s) naming {px} follow it" if moved else "")))
        outcomes: list[ThesisOutcome] = []
        created_now: list[str] = []
        applied: set[str] = set()  # theses this article version has contributed to so far
        for key0, hs in groups.items():
            key, seg, prod = key0, segments[key0], products.get(key0, "")
            h = hs[0]
            merged_notes: dict[str, str] = {}
            if len(hs) > 1:
                for extra in hs[1:]:
                    shared, distinct = _evidence_overlap(h, extra)
                    merged_notes[extra.raw.local_id] = (
                        f"merged with {h.raw.local_id} “{h.raw.title}” under one identity key — "
                        f"{shared} supporting claim(s) shared, {distinct} its own"
                        + (" — DISTINCT EVIDENCE: review whether it is the same thesis"
                           if distinct > shared else ""))
                    h.supporting += [c for c in extra.supporting if c not in h.supporting]
                    h.dislocation += [c for c in extra.dislocation if c not in h.dislocation]
                    h.counter += [c for c in extra.counter if c not in h.counter]
                    h.affected += [a for a in extra.affected if a not in h.affected]
                    # every role the merged hypothesis gave its evidence comes with it — a
                    # catalyst, a sector the source names, the strongest evidence, an earnings
                    # step the kept chain lacks (2026-10-14: a merge dropped a live thesis's
                    # catalyst and two sectors, and with them its RESEARCH NOW route)
                    h.strongest += [c for c in extra.strongest if c not in h.strongest]
                    h.catalyst += [c for c in extra.catalyst if c not in h.catalyst]
                    h.implication_claims += [c for c in extra.implication_claims
                                             if c not in h.implication_claims]
                    h.sectors += [x for x in extra.sectors
                                  if norm_name(x.name) not in {norm_name(y.name)
                                                               for y in h.sectors}]
                    h.steps += [x for x in extra.steps if x.step not in {y.step for y in h.steps}]
                st.add_issue(self._issue(ctx, "hypothesis", key, IssueSeverity.WARN,
                                         "SAME_KEY_IN_ARTICLE",
                                         f"{len(hs)} hypotheses share one identity key in one "
                                         f"article — merged as one thesis contribution: "
                                         + "; ".join(f"“{x.raw.title}” "
                                                     f"({merged_notes.get(x.raw.local_id, 'kept')})"
                                                     for x in hs)))
            merged_ids = {x.raw.local_id for x in hs}  # a risk tied to ANY merged hypothesis
            risks = [r for r in ve.risks if not r.related or merged_ids & set(r.related)]
            existing = self._by_key(key)
            if (existing is not None and not seg and not existing.key_segment
                  and self.taxonomy.segments_of(existing.key_node)
                  and existing.thesis_id not in earlier
                  and not self._shares_evidence(h, existing, claims)):
                # a segmented node's BARE key names no subject: two theses that each name none of
                # its segments share it, and the second updates the first. Said, never silent.
                today = self.thesis_segment(existing)
                st.add_issue(self._issue(
                    ctx, "hypothesis", key, IssueSeverity.WARN, "UNSEGMENTED_KEY",
                    f"“{h.raw.title}” names none of {existing.key_node}'s segments and shares no "
                    f"evidence with {existing.thesis_id} “{existing.title}”"
                    + (f" (which today reads as {today})" if today else "")
                    + " — updated under one bare key: check whether it is the same thesis"))
            if existing is not None and not prod:
                # the key is necessary, not sufficient: the thesis it names must be about the same
                # PRODUCT, or share the source's sentences — else this is another proposition
                pe, ph = self.thesis_product(existing), self.product_signature(h, claims)
                if pe and ph and pe != ph and not self._shares_evidence(h, existing, claims):
                    st.add_issue(self._issue(
                        ctx, "hypothesis", key, IssueSeverity.INFO, "PRODUCT_SPLIT",
                        f"“{h.raw.title}” has the key of {existing.thesis_id} “{existing.title}” "
                        f"but its evidence names {ph}, that thesis's {pe}, and they share no "
                        f"evidence — a separate thesis"))
                    prod = ph
                    key = thesis_key(h, seg, prod)
                    existing = self._by_key(key)
            if existing is None and (prior := self._same_article_thesis(h, seg, prod, earlier,
                                                                        claims)):
                existing = prior
                st.add_issue(self._issue(
                    ctx, "thesis", prior.thesis_id, IssueSeverity.INFO, "SAME_ARTICLE_VERSION",
                    f"a later version of {ctx.article.article_id} names segment(s) "
                    f"{seg or 'none'}; its earlier version created this thesis "
                    f"(segment {prior.key_segment or 'none'}) — updated, never a second thesis "
                    f"from one article"))
            review = ""
            if existing is None and (match := self._earlier_match(h, seg, prod, claims, earlier)):
                old, (diffs, labels), shared, n = match
                if not diffs:  # the same economic claim from the same article: update, keep its id
                    existing = old
                    st.add_issue(self._issue(
                        ctx, "thesis", old.thesis_id, IssueSeverity.INFO, "SAME_ARTICLE_MATCH",
                        f"a later version of {ctx.article.article_id} keyed “{h.raw.title}” as "
                        f"{key}; {shared} of its {n} sentence(s) are already on this thesis and "
                        f"direction, geography, mechanism family, segment, product and horizon "
                        f"agree — updated, never a second thesis"
                        + "".join(f"; {x}" for x in labels)))
                else:  # the same sentences, a different claim on some dimension: a human decides
                    review = (f"SIBLING of “{old.title}”: {shared} of its {n} sentence(s) were "
                              f"already on that thesis from an earlier version of this article, "
                              f"but it differs in {'; '.join(diffs)} — not merged, held for "
                              f"review (never an independent research opportunity)")
            if existing is None and seg and not review:
                # a thesis keyed BEFORE a segment it is about existed holds another segment set
                # (the bare key, or one that has since grown): found by what it reads as TODAY,
                # and re-keyed below — never a duplicate under the new key
                existing = self._stale_holder(h, seg, prod)
            sibling = ""
            if existing is None:
                out = self._create(ctx, key, h, claims, mentions, resolutions, risks, seg,
                                   product=prod, review=review)
                created_now.append(out.thesis_id)
                applied.add(out.thesis_id)
                if review:
                    sibling = review
                    st.add_issue(self._issue(
                        ctx, "thesis", out.thesis_id, IssueSeverity.WARN, "SAME_ARTICLE_SIBLING",
                        f"{match[0].thesis_id if match else '?'} / {out.thesis_id} "
                        f"({ctx.article.article_id}): {review}"))
            else:
                part = ""
                if existing.thesis_id in applied:
                    # another hypothesis of this version, under another key, already reached it:
                    # its evidence is a contribution of its own — the version's one contribution
                    # id dropped it as ALREADY_INGESTED, its claims linked nowhere (2026-10-14)
                    part = h.raw.local_id
                    st.add_issue(self._issue(
                        ctx, "thesis", existing.thesis_id, IssueSeverity.WARN,
                        "SAME_THESIS_IN_ARTICLE",
                        f"“{h.raw.title}” (key {key}) reached {existing.thesis_id} "
                        f"“{existing.title}”, which another hypothesis of this article already "
                        f"updated under another key — applied as a second contribution: review "
                        f"whether they are one thesis"))
                out = self._update(ctx, existing, h, claims, mentions, resolutions, risks,
                                   part=part)
                applied.add(out.thesis_id)
                if existing.identity != key:  # reached by another key: is its own one stale?
                    self._correct_segment(ctx, out.thesis_id)
            outcomes.append(out)
            for x in hs:  # where every proposition of the source landed (mechanism coverage)
                self.destinations[x.raw.local_id] = (
                    out.thesis_id, merged_notes.get(x.raw.local_id, "") or sibling)
        for tid in created_now:
            outcomes.extend(self._challenge_competitors(ctx, tid, claims, mentions, resolutions,
                                                        created_now))
        # an EARLIER version's thesis this version proposed nothing for, whose sentences this
        # version re-verifies, is kept and re-assessed — never silently left on the old reading
        touched = {tid for tid, _ in self.destinations.values()} | set(created_now)
        for tid in earlier:
            t = st.thesis(tid)
            if (tid not in touched and t is not None and t.status is not ThesisStatus.ARCHIVED
                    and (out2 := self._reverify(ctx, t, claims)) is not None):
                outcomes.append(out2)
                self._correct_segment(ctx, tid)
        return outcomes

    # -- identity -----------------------------------------------------------------------------
    def product_signature(self, h: VerifiedHypothesis, claims: dict[str, Claim]) -> str:
        """The PRODUCT a hypothesis is about (taxonomy `[[product]]` of its node, generic products
        left out): the one its own statement names, when it names exactly one; else the one its
        verified quotes name most ("" when none or a tie). The statement comes first because
        evidence for one technology is often a COMPARISON with another — a fuel-cell thesis's
        quotes name CCGTs as often as fuel cells (observed 2026-10-12: 8 vs 7)."""
        return (self._named_product(h.raw.value_chain_node, h.raw.title)
                or self._dominant_product(h.raw.value_chain_node,
                                          [claims[c] for c in (*h.supporting, *h.dislocation,
                                                               *h.catalyst) if c in claims]))

    def _risks_follow_product(self, risks: list[VerifiedRisk], kept: VerifiedHypothesis,
                              split: VerifiedHypothesis, kept_product: str,
                              split_product: str) -> int:
        """A market risk the model tied to the hypothesis that KEPT the key, whose statement
        names the split-off product and not the kept one, goes with the split-off thesis (a
        fuel-cell supply-chain risk is not a risk to gas-turbine demand). Returns how many."""
        prods = [p for p in self.taxonomy.products_of(kept.raw.value_chain_node) if not p.covers]
        moved = 0
        for r in risks:
            if kept.raw.local_id not in r.related:
                continue
            named = products_in(r.raw.statement, prods)
            if split_product in named and kept_product not in named:
                r.related = [split.raw.local_id if i == kept.raw.local_id else i
                             for i in r.related]
                moved += 1
        return moved

    def thesis_product(self, t: Thesis) -> str:
        if t.key_product:
            return t.key_product
        cited = (LinkRole.SUPPORTS, LinkRole.DISLOCATION, LinkRole.CATALYST)
        return (self._named_product(t.key_node, t.title)
                or self._dominant_product(t.key_node, [c for lk in self.store.links(t.thesis_id)
                                                       if lk.role in cited
                                                       and (c := self.store.claim(lk.claim_id))]))

    def thesis_segment(self, t: Thesis) -> str:
        """The segment a held thesis is about under TODAY's rule (`subject_segment`): its
        statement, its product, then its cited evidence."""
        cited = (LinkRole.SUPPORTS, LinkRole.DISLOCATION, LinkRole.CATALYST)
        quotes = [c.quote for lk in self.store.links(t.thesis_id) if lk.role in cited
                  and (c := self.store.claim(lk.claim_id)) is not None and c.span_verified]
        return subject_segment(t.key_node, t.title, self.thesis_product(t), (), quotes,
                               self.taxonomy)

    def _stale_holder(self, h: VerifiedHypothesis, seg: str, prod: str) -> Thesis | None:
        """The thesis on this hypothesis's node, mechanism, direction, geography and product
        whose key names ANOTHER segment set than it reads as today — `seg` — because a segment
        was added after it was keyed (2026-10-15: a thesis keyed bare, or keyed `obesity_metabolic`
        before a second segment its statement names existed)."""
        raw = h.raw
        for t in self.store.theses():
            if (t.retired or t.key_segment == seg
                    or (t.key_node, t.key_mechanism, t.key_direction.value, t.key_geography,
                        t.key_review, t.key_product) != (
                        raw.value_chain_node, raw.mechanism, raw.direction.value,
                        norm_geo(raw.geography), review_tag(h), prod)):
                continue
            if self.thesis_segment(t) == seg:
                return t
        return None

    def _by_key(self, key: str) -> Thesis | None:
        """The thesis holding an identity key — or the one CREATED with it before its key was
        corrected (its id is that key's hash): a former key finds its thesis, never a duplicate
        that would overwrite it."""
        t = self.store.thesis_by_key(key)
        if t is None:
            # the key's id, past every RETIRED holder (`_create` salts past them the same way): a
            # thesis created there with this key and re-keyed since is found, never collided with
            # (2026-10-14: a re-keyed thesis at the salted id failed every later bare-key article)
            tid = thesis_id_for(key)
            while (t := self.store.thesis(tid)) is not None and t.retired:
                tid = thesis_id_for(f"{key}|after:{t.thesis_id}")
        # a RETIRED thesis is never matched again: its articles' re-analysis replaces it
        return None if t is None or t.retired else t

    def _correct_segment(self, ctx: ArticleContext, tid: str) -> None:
        """A thesis a later reading reached by ANOTHER key, whose own segment under today's rule
        differs from the one in its key (an earlier rule read it off an incidental mention), is
        re-keyed — the same id, versions, evidence and history; the old key recorded. Never onto
        a key another thesis holds (that is flagged for review instead)."""
        t = self.store.thesis(tid)
        if t is None:
            return
        seg = self.thesis_segment(t)
        if seg == t.key_segment:
            return
        new = t.model_copy(update={"key_segment": seg})
        holder = self.store.thesis_by_key(new.identity)
        if holder is not None and holder.thesis_id != tid:
            self.store.add_issue(self._issue(
                ctx, "thesis", tid, IssueSeverity.WARN, "KEY_NOT_CORRECTED",
                f"its segment under today's rule is {seg or 'none'} (key says "
                f"{t.key_segment or 'none'}), but {holder.thesis_id} holds that key — review"))
            return
        why = (f"segment {t.key_segment or 'none'} → {seg or 'none (unassigned)'}: read from the "
               f"thesis statement, product and evidence — never an incidental mention")
        with self.store.tx():
            self.store.rekey_thesis(new)
            self.store.add_event(self._event(ctx, tid, None, "KEY_CORRECTED",
                                             f"identity key {t.identity} → {new.identity} ({why})"))
            self.store.add_issue(self._issue(ctx, "thesis", tid, IssueSeverity.INFO,
                                             "KEY_CORRECTED", why))

    def _named_product(self, node: str, text: str) -> str:
        named = products_in(text, [p for p in self.taxonomy.products_of(node) if not p.covers])
        return next(iter(named)) if len(named) == 1 else ""

    def _dominant_product(self, node: str, claims: list[Claim]) -> str:
        prods = [p for p in self.taxonomy.products_of(node) if not p.covers]
        if not prods:
            return ""
        counts: Counter[str] = Counter()
        n = 0
        for c in claims:
            if c.span_verified:
                n += 1
                counts.update(products_of(c, prods))
        top = counts.most_common(2)
        if not top or (len(top) == 2 and top[0][1] == top[1][1]) \
                or top[0][1] < PRODUCT_MIN_SHARE * n:
            return ""
        return top[0][0]

    def _shares_evidence(self, h: VerifiedHypothesis, t: Thesis,
                         claims: dict[str, Claim]) -> bool:
        held = [c for lk in self.store.links(t.thesis_id) if (c := self.store.claim(lk.claim_id))]
        ids = {c.claim_id for c in held}
        mine = [claims[c] for c in (*h.supporting, *h.dislocation, *h.catalyst) if c in claims]
        return any(c.claim_id in ids or any(same_sentence_reread(o, c) for o in held)
                   for c in mine)

    def _earlier_match(self, h: VerifiedHypothesis, seg: str, prod: str,
                       claims: dict[str, Claim],
                       earlier: list[str],
                       ) -> tuple[Thesis, tuple[list[str], list[str]], int, int] | None:
        """The thesis an EARLIER version of this article created that already holds at least
        SIBLING_SHARE of this hypothesis's sentences (the best such), with the identity
        dimensions on which they differ — overlapping sentences alone never make them one."""
        mine = [claims[c] for c in (*h.supporting, *h.dislocation, *h.catalyst)
                if c in claims and claims[c].span_verified]
        if not mine:
            return None
        cited = (LinkRole.SUPPORTS, LinkRole.DISLOCATION, LinkRole.CATALYST)
        best: tuple[Thesis, int, tuple[int, int, int, int]] | None = None
        for tid in earlier:
            t = self.store.thesis(tid)
            if t is None:
                continue
            held = [c for lk in self.store.links(tid) if lk.role in cited
                    and (c := self.store.claim(lk.claim_id))]
            shared = sum(1 for c in mine if any(same_sentence_reread(o, c) for o in held))
            # the THESIS side too: how much of what it cites from this article comes back
            here = list({c.claim_id: c for c in held
                         if c.article_id == mine[0].article_id}.values())
            back = sum(1 for o in here if any(same_sentence_reread(o, c) for c in mine))
            if shared and shared >= SIBLING_SHARE * len(mine) and (best is None
                                                                   or shared > best[1]):
                best = (t, shared, (shared, len(mine), back, len(here)))
        if best is None:
            return None
        return best[0], self._identity_differences(h, seg, prod, claims, best[0],
                                                   best[2]), best[1], len(mine)

    def _identity_differences(self, h: VerifiedHypothesis, seg: str, prod: str,
                              claims: dict[str, Claim], t: Thesis,
                              evidence: tuple[int, int, int, int] = (0, 0, 0, 0),
                              ) -> tuple[list[str], list[str]]:
        """(where a hypothesis and a thesis are NOT the same economic claim, what is only
        labelled differently). Blocking: direction, geography, mechanism FAMILY (a label within
        one family is the same kind of economics), segment, product and time horizon. The
        value-chain NODE is not: two reads of the SAME sentences place one proposition at
        different nodes (observed 2026-10-12: a midstream capex cycle read as `energy`, then as
        `ai_infrastructure.power_grid`, 15 of 20 sentences the same) — it is stated, and the
        thesis keeps its key. Nor is the mechanism family when the two readings rest on the SAME
        evidence (`evidence` = shared / this reading's / come back / the thesis's sentences, each
        side at least SAME_EVIDENCE_SHARE): the source then shows ONE causal chain read at two
        steps — Citi's fuel cells, "share gain" in one reading and "demand volume" in the next,
        14 of 17 sentences the same. With evidence of their own on either side, the source may
        hold two separately falsifiable mechanisms: a human decides, told what each would
        mean for earnings."""
        raw = h.raw
        out: list[str] = []
        labels: list[str] = []
        if t.key_review or review_tag(h):
            out.append("an unclassified (`other`) thesis")
        if t.key_node != raw.value_chain_node:
            labels.append(f"the two reads place it at different value-chain nodes "
                          f"({raw.value_chain_node} vs {t.key_node}; the thesis keeps "
                          f"{t.key_node})")
        if t.key_direction.value != raw.direction.value:
            out.append(f"direction ({raw.direction.value} vs {t.key_direction.value})")
        if not geographies_overlap(t.key_geography, norm_geo(raw.geography)):
            out.append(f"geography ({norm_geo(raw.geography)} vs {t.key_geography})")
        fn, fo = self.taxonomy.family_of(raw.mechanism), self.taxonomy.family_of(t.key_mechanism)
        if fn != fo:
            shared, n, back, held = evidence
            if n and held and shared >= SAME_EVIDENCE_SHARE * n \
                    and back >= SAME_EVIDENCE_SHARE * held:
                labels.append(
                    f"one causal chain read at two steps — {t.key_mechanism} "
                    f"({FAMILY_CONSEQUENCE.get(fo, fo)}) and {raw.mechanism} "
                    f"({FAMILY_CONSEQUENCE.get(fn, fn)}) on the same evidence ({shared} of this "
                    f"reading's {n} sentences, {back} of the thesis's {held}): no second, "
                    f"separately falsifiable mechanism in the source; the thesis keeps "
                    f"{t.key_mechanism}")
            else:
                out.append(
                    f"economic mechanism ({raw.mechanism}, {fn}: "
                    f"{FAMILY_CONSEQUENCE.get(fn, fn)} — vs {t.key_mechanism}, {fo}: "
                    f"{FAMILY_CONSEQUENCE.get(fo, fo)}); each reading cites evidence of its own "
                    f"({n - shared} of {n} vs {held - back} of {held} sentences), so the source "
                    f"may hold two separately falsifiable mechanisms")
        if not (_nests(seg, t.key_segment) or _same_subject(seg, self.thesis_segment(t))):
            out.append(f"segment ({seg or 'none'} vs {t.key_segment or 'none'})")
        pn, po = prod or self.product_signature(h, claims), self.thesis_product(t)
        if pn and po and pn != po:
            out.append(f"product ({pn} vs {po})")
        definite = (Horizon.NEXT_2_4_QUARTERS, Horizon.LONGER_TERM)
        if raw.horizon in definite and t.horizon in definite and raw.horizon != t.horizon:
            out.append(f"time horizon ({raw.horizon.value} vs {t.horizon.value})")
        return out, labels

    def _reverify(self, ctx: ArticleContext, t: Thesis,
                  claims: dict[str, Claim]) -> ThesisOutcome | None:
        """A later version of the article re-states at least SIBLING_SHARE of the sentences this
        thesis cites from it, though its analysis proposed nothing for them: the thesis is kept,
        those sentences are linked as REPEATED (attribution, never a confirmation), and it is
        RE-ASSESSED under the current rules — a new version only when the assessment changes."""
        st = self.store
        aid = ctx.article.article_id
        cited = (LinkRole.SUPPORTS, LinkRole.DISLOCATION, LinkRole.CATALYST)
        links = st.links(t.thesis_id)
        own = [(lk, c) for lk in links if lk.role in cited
               and (c := st.claim(lk.claim_id)) is not None and c.article_id == aid]
        mine = [c for c in claims.values() if c.span_verified and c.article_id == aid
                and c.article_version_id == ctx.version.version_id]
        found: dict[str, LinkRole] = {}
        restated = 0
        for lk, old in own:
            hit = next((c for c in mine if same_sentence_reread(old, c)), None)
            if hit is not None:
                restated += 1
                found.setdefault(hit.claim_id, lk.role)
        cid_contrib = "AC-" + _sha(ctx.version.version_id, t.thesis_id)[:14]
        if (not own or restated < SIBLING_SHARE * len(own)
                or any(c.contribution_id == cid_contrib for c in st.contributions(t.thesis_id))):
            return None
        prev_v = st.thesis_version(t.thesis_id, t.current_version)
        assert prev_v is not None
        held = {lk.claim_id for lk in links}
        published = _published(ctx)  # None for an undated source — never the run's as-of

        def new_links(first: int) -> list[ThesisClaimLink]:
            return [ThesisClaimLink(thesis_id=t.thesis_id, claim_id=cid, role=role,
                                    first_version=first, change_class=ChangeClass.REPEATED,
                                    independence_group=claims[cid].origin_id or aid)
                    for cid, role in found.items() if cid not in held]

        next_v = t.current_version + 1
        item = ChangeItem(change_class=ChangeClass.REPEATED,
                          text=(f"{LABEL_OPEN}re-read{LABEL_CLOSE} {restated} of the {len(own)} "
                                f"sentence(s) this thesis cites from {aid} were re-verified in "
                                f"version {ctx.version.version_id} ({ctx.version.parser_version}),"
                                f" whose analysis proposed no thesis for them — kept and "
                                f"re-assessed under the current rules; no new evidence"),
                          provenance=Provenance.MODEL_INFERENCE,
                          claim_ids=tuple(list(found)[:6]), article_id=aid,
                          original_date=_iso(published))
        version = self._build_version(
            ctx, t.model_copy(update={"current_version": next_v}), next_v, None, prev_v.content,
            links + new_links(next_v), claims, {}, {}, [item],
            f"re-read of {aid}: {restated} of {len(own)} cited sentence(s) re-verified, nothing "
            f"new", "relative to the registry's prior version", EvidenceDirection.UNCHANGED,
            prev_v.priority.research_action, prev_v.priority.factors, [], [], [],
            change_summary=f"{aid}: re-verified ×{restated} (re-read) — re-assessed",
            classes=dict.fromkeys(found, ChangeClass.REPEATED),
            contribution=ChangeClass.REPEATED, prev_sha=prev_v.content_sha, defer=True)
        review_issues, context = self.deferred
        changed = (version.priority.research_action is not prev_v.priority.research_action
                   or version.priority.rules_fired != prev_v.priority.rules_fired)
        first = next_v if changed else t.current_version
        contribution = ArticleThesisContribution(
            contribution_id=cid_contrib, article_id=aid, thesis_id=t.thesis_id,
            version=next_v if changed else None, contribution=ChangeClass.REPEATED,
            claim_ids=tuple(found), run_id=ctx.run_id, as_of=ctx.as_of)
        ev = self._event(ctx, t.thesis_id, next_v if changed else None,
                         "REASSESSED" if changed else "ATTRIBUTION",
                         f"re-read of {aid}: {restated} of {len(own)} cited sentence(s) "
                         f"re-verified; " + (f"re-assessed {prev_v.priority.research_action.value}"
                                             f" → {version.priority.research_action.value} under "
                                             f"the current rules" if changed
                                             else "assessment unchanged — no new version"))
        with st.tx():
            if changed:  # the version is kept: its review and its context links with it
                st.upsert_thesis(t.model_copy(update={"current_version": next_v}))
                st.add_thesis_version(version)
                for i in review_issues:
                    st.add_issue(i)
                for lk in context:
                    st.add_link(lk)
            for lk in new_links(first):
                st.add_link(lk)
            st.add_contribution(contribution)
            st.add_event(ev)
        self.reverified.append(t.thesis_id)
        return ThesisOutcome(t.thesis_id, t.title, False, next_v if changed else None,
                             ChangeClass.REPEATED, version.priority.research_action,
                             prev_v.priority.research_action, EvidenceDirection.UNCHANGED,
                             [ev.event_type])

    def _same_article_thesis(self, h: VerifiedHypothesis, segment: str, product: str,
                             earlier: list[str], claims: dict[str, Claim]) -> Thesis | None:
        """The thesis an EARLIER VERSION of this same article created for this hypothesis, when
        the fuller version's evidence names more (or fewer) segments — a preview naming none,
        its full text naming DRAM. Every other identity dimension must match and the segment
        sets must nest; disjoint segments are different claims and stay separate theses. When
        the segments are not identical, the thesis must also hold one of the hypothesis's
        sentences: a thesis with NO segment nests with every one, and would otherwise absorb any
        story of the article on the same node, mechanism and place (2026-10-12)."""
        raw = h.raw
        for tid in earlier:
            t = self.store.thesis(tid)
            if t is None or (t.key_node, t.key_mechanism, t.key_direction.value,
                             t.key_geography, t.key_review, t.key_product) != (
                    raw.value_chain_node, raw.mechanism, raw.direction.value,
                    norm_geo(raw.geography), review_tag(h), product):
                continue
            # its key's segment, or its segment under today's rule (a key the earlier rule read
            # off an incidental mention is corrected once matched — `_correct_segment`)
            if not (_nests(segment, t.key_segment)
                    or _same_subject(segment, self.thesis_segment(t))):
                continue
            if segment == t.key_segment or self._shares_evidence(h, t, claims):
                return t
        return None

    # -- create -------------------------------------------------------------------------------
    def _create(self, ctx: ArticleContext, key: str, h: VerifiedHypothesis,
                claims: dict[str, Claim], mentions: dict[str, Mention],
                resolutions: dict[str, SecurityResolution],
                risks: list[VerifiedRisk], segment: str = "", *, product: str = "",
                review: str = "") -> ThesisOutcome:
        raw = h.raw
        tid = thesis_id_for(key)
        # the key's id may belong to a RETIRED thesis (re-analysis): a new id, derived from the
        # key and the retired one's — never the retired record overwritten
        while (held := self.store.thesis(tid)) is not None and held.retired:
            tid = thesis_id_for(f"{key}|after:{held.thesis_id}")
        other = raw.value_chain_node == "other" or raw.mechanism == "other"
        now = self.first_ingested.get(tid) or datetime.now(tz=UTC)
        published = _published(ctx)  # None for an undated source — never the run's as-of
        thesis = Thesis(
            thesis_id=tid, key_node=raw.value_chain_node, key_mechanism=raw.mechanism,
            key_direction=Direction(raw.direction.value), key_geography=norm_geo(raw.geography),
            title=raw.title.strip(), sector=self.node_label.get(raw.value_chain_node,
                                                                raw.value_chain_node),
            region=norm_geo(raw.geography),
            status=ThesisStatus.REVIEW_NEEDED if other or review else ThesisStatus.ACTIVE,
            current_version=1, created_at=now, created_as_of=ctx.as_of,
            # an undated source dates nothing: the thesis's clock starts at this run's as-of, said
            # (UNDATED_SOURCE) — the only date the registry has for it
            last_material_update=published or ctx.as_of,
            ancestry=self.taxonomy.ancestry(raw.value_chain_node),
            stance=raw.stance_in_source, horizon=raw.horizon, kind=raw.kind,
            key_segment=segment, key_review=review_tag(h), key_product=product)
        assert thesis.identity == key, (thesis.identity, key)  # one identity, store and engine
        roles = self._roles(h, risks)
        links = [ThesisClaimLink(thesis_id=tid, claim_id=cid, role=role, first_version=1,
                                 change_class=ChangeClass.NOVELTY_UNVERIFIED,
                                 independence_group=claims[cid].origin_id or ctx.article.article_id)
                 for cid, role in roles.items()]
        own = [claims[cid] for cid, role in roles.items() if cid in claims
                and role in (LinkRole.SUPPORTS, LinkRole.DISLOCATION, LinkRole.CATALYST)]
        relations, n_area = self._relations_for(thesis, ctx, own)
        rel_notes = [CardSentence(text=f"Registry link — {relation_label(r)} "
                                       f"{r.to_thesis if r.from_thesis == tid else r.from_thesis}"
                                       f": {r.reason}", provenance=Provenance.MODEL_INFERENCE)
                     for r in relations]
        if n_area:  # ONE line for the broader area, never one per thesis in it (U43)
            rel_notes.append(CardSentence(
                text=f"Registry link — {n_area} other {'thesis' if n_area == 1 else 'theses'} "
                     f"in the same broader area ({thesis.key_node.split('.')[0]}) — context only, "
                     f"never evidence; the desk lists them",
                provenance=Provenance.MODEL_INFERENCE))
        head, n_evidence = self._headline_claims(h, claims)
        items = [ChangeItem(change_class=ChangeClass.NOVELTY_UNVERIFIED,
                            text=claims[c].statement, provenance=_label([c], claims),
                            claim_ids=(c,), article_id=ctx.article.article_id,
                            original_date=_iso(published), period=claims[c].period)
                 for c in head]
        if n_evidence > len(head):
            items.append(_more_item(len(head), n_evidence, ctx.article.article_id))
        vs_prior = (f"New to the registry — first ingested {now:%Y-%m-%d %H:%M} UTC, analysed as "
                    f"of {ctx.as_of.isoformat()}, from "
                    + (f"a source published {published.isoformat()}" if published else
                       "an UNDATED source (it states no publication date)")
                    + "; not necessarily new to the market.")
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
        elif review:
            events.append(self._event(ctx, tid, 1, "REVIEW_NEEDED", review))
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
                risks: list[VerifiedRisk], *, part: str = "") -> ThesisOutcome:
        """`part`: a SECOND hypothesis of this article version reaching the thesis — its own
        contribution id, so the version's first contribution does not swallow it."""
        st = self.store
        cid_contrib = "AC-" + _sha(ctx.version.version_id, thesis.thesis_id,
                                   *([part] if part else []))[:14]
        prev_v = st.thesis_version(thesis.thesis_id, thesis.current_version)
        assert prev_v is not None
        if any(c.contribution_id == cid_contrib for c in st.contributions(thesis.thesis_id)):
            return ThesisOutcome(thesis.thesis_id, thesis.title, False, None,
                                 ChangeClass.REPEATED, prev_v.priority.research_action,
                                 prev_v.priority.research_action, EvidenceDirection.UNCHANGED,
                                 ["ALREADY_INGESTED"])
        existing_links = st.links(thesis.thesis_id)
        held = {lk.claim_id: st.claim(lk.claim_id) for lk in existing_links}
        # in the order the thesis took them in (oldest first): `classify_claim` reads a new claim
        # against the latest reading, never against whichever claim id sorts last (U5)
        linked = sorted(existing_links, key=lambda lk: (lk.first_version, lk.claim_id))
        held_claims = [x for x in (held[lk.claim_id] for lk in linked) if x is not None]
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
        published = _published(ctx)  # None for an undated source — never the run's as-of
        thesis = thesis.model_copy(update={
            # undated evidence never resets the stale clock: its date is unknown (2026-10-14: an
            # old undated report read as current last evidence)
            "current_version": next_v, "last_material_update": (
                max(thesis.last_material_update, published) if published
                else thesis.last_material_update),
            "stance": max(thesis.stance, h.raw.stance_in_source, key=lambda s: _STANCE_RANK[s]),
            "horizon": h.raw.horizon if h.raw.horizon is not Horizon.UNCLEAR else thesis.horizon})
        items = [ChangeItem(change_class=classes[cid],
                            text=f"{claims[cid].statement} {LABEL_OPEN}{notes[cid]}{LABEL_CLOSE}",
                            provenance=_label([cid], claims), claim_ids=(cid,),
                            article_id=ctx.article.article_id,
                            original_date=_iso(published), period=claims[cid].period)
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
                                    original_date=_iso(published)))
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
            # back to what it was: a thesis archived while held for review comes back held
            # (2026-10-14: it came back ACTIVE, its identity hold gone for good)
            review = self._under_review(thesis)
            thesis = thesis.model_copy(update={
                "status": ThesisStatus.REVIEW_NEEDED if review else ThesisStatus.ACTIVE})
            events.append(self._event(ctx, thesis.thesis_id, next_v, "REACTIVATED",
                                      f"material new evidence from {ctx.article.article_id} "
                                      f"moved an archived thesis back to "
                                      f"{version.priority.research_action.value}"
                                      + (" — still held for review" if review else "")))
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
    def _under_review(self, t: Thesis) -> bool:
        """REVIEW_NEEDED — or ARCHIVED while it was (a REVIEW_NEEDED event, set at creation and
        never cleared): archiving takes a thesis off the active list, never out of review."""
        if t.status is ThesisStatus.REVIEW_NEEDED:
            return True
        return t.status is ThesisStatus.ARCHIVED and any(
            e.event_type == "REVIEW_NEEDED" for e in self.store.events(thesis_id=t.thesis_id))

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

    def _corrected(self, card: CardContent, corr: SentenceCorrection,
                   claims: dict[str, Claim], run_id: str) -> CardContent:
        """One ANALYST CORRECTION applied: the line's new text must cite claims already LINKED to
        the thesis and verified, and pass the same deterministic number check as every card line
        — a correction is never a way to add an unverified fact. Its label is derived from its
        cited claims (the weakest), capped for a conditional line; raises when it fails."""
        bad = [c for c in corr.claim_ids if c not in claims or not claims[c].span_verified
               or claims[c].number_verified is False]
        if not corr.claim_ids or bad:
            raise CorrectionError(f"{corr.thesis_id} {corr.sentence_id}: a correction must cite "
                                  f"verified claims the thesis links — not {bad or 'none'}")
        if corr.sentence_id not in card_sentences(card):
            raise CorrectionError(f"{corr.thesis_id}: no card line {corr.sentence_id}")
        prov = capped_label(label_for(corr.claim_ids, claims) or Provenance.MODEL_INFERENCE,
                            corr.text)
        new = labelled(CardSentence(text=corr.text, provenance=prov,
                                    claim_ids=tuple(corr.claim_ids)), claims)
        fixed = replace_sentence(card, corr.sentence_id, new)
        fails = [i.detail for i in deterministic_card_checks(fixed, claims, run_id)
                 if i.ref_id == f"{corr.thesis_id}:{corr.sentence_id}"]
        if fails:
            raise CorrectionError(f"{corr.thesis_id} {corr.sentence_id}: the correction fails "
                                  f"the card checks — {fails[0]}")
        return fixed

    def reassess(self, thesis_id: str, *, run_id: str, as_of: date,
                 corrections: Sequence[SentenceCorrection] = ()) -> ThesisOutcome | None:
        """Re-apply the CURRENT research-action rules to a thesis's STORED evidence — no article
        read, no model call. Asked for by the operator after the 2026-10-12 pilot, whose one
        RESEARCH NOW rested on a page category tag as its exposure and on next year's full-year
        forecast as its near-term window, both since corrected.

        Every input comes from the registry: the linked, span-verified claims by role; the
        current card's exposures, transmission and sources; the contributing version's retrieval
        as read now; the previous priority's channel reliability and verification hold. A
        sector exposure is re-checked against its stored block and REFUSED when that block is a
        bare page label (`verify.bare_label`). The card's deterministic rules are re-applied (a
        price move is market context, not counter-evidence; a conditional line is never a fact)
        and any ANALYST CORRECTIONS (`SentenceCorrection`) applied. A NEW VERSION is appended only
        when something changes; every other line is kept word for word. The card review's
        findings are carried to the lines they were made on; the deterministic card checks are
        recomputed. None when nothing changes."""
        t = self.store.thesis(thesis_id)
        prev_v = self.store.thesis_version(thesis_id, t.current_version) if t else None
        if t is None or prev_v is None:
            raise ValueError(f"no thesis {thesis_id} with a current version to reassess")
        if t.retired:  # replaced by its articles' re-analysis: never updated again
            return None
        card, prev = prev_v.content, prev_v.priority
        links = self.store.links(thesis_id)
        all_claims = {lk.claim_id: c for lk in links if (c := self.store.claim(lk.claim_id))}
        by_role: dict[LinkRole, list[Claim]] = {}
        for lk in links:
            c = all_claims.get(lk.claim_id)
            if c is not None and c.span_verified:
                held = by_role.setdefault(lk.role, [])
                if not any(same_sentence_reread(o, c) for o in held):
                    held.append(c)
        kept: list[SectorExposure] = []
        refused: list[str] = []
        for se in card.s05_affected.sector_exposures:
            vs = self.store.article_versions(se.article_id)
            homes = [b for b in (vs[-1].blocks if vs else ())
                     if b.text and locate(se.quote, b.text)]
            if homes and all(bare_label(b.kind, b.text, se.name) for b in homes):
                refused.append(f"{se.name!r} rests only on a page label ({homes[0].block_id}: "
                               f"{homes[0].text[:40]!r}) — refused")
            else:
                kept.append(se)
        contributed = [c.article_id for c in self.store.contributions(thesis_id=thesis_id)
                       if c.version == prev_v.version]
        aid = contributed[0] if contributed else card.s09_sources[-1].article_id
        versions = self.store.article_versions(aid)
        if not versions:
            raise ValueError(f"{thesis_id}: no stored version of its source {aid}")
        av = versions[-1]
        retrieval = (av.retrieval_state if av.retrieval_state is not RetrievalState.BLOCKED
                     else RetrievalState.PARTIAL)
        retrieval_note = ""
        if retrieval is RetrievalState.PARTIAL and av.unread_back_matter:
            retrieval = RetrievalState.FULL
            retrieval_note = (f"analysis text complete — {av.unread_back_matter}; the document "
                              f"itself stays PARTIAL")
        factor = {f.factor_id: f for f in prev.factors}
        # the holds the update path derives, derived again — never the old note re-joined, which
        # doubled every reason and kept a cleared HOLD forever (U55); only the review's withheld
        # lines carry over, since a reassess runs no review
        holds = self._hold_reasons(links, all_claims)
        if not t.key_review and self._under_review(t):
            holds.append(IDENTITY_HOLD)
        hold = factor.get("F10_verification_hold")
        if hold is not None and hold.value == "HOLD":
            holds += review_holds(hold.note)
        art = self.store.article(aid)
        reliability = ((self.reliability_of(art.source_id) if self.reliability_of and art
                        else None) or factor["F1_source_reliability"].value)
        aff = self._relisted(card.s05_affected, as_of)
        counted = counted_exposures(aff, kept)
        state = ThesisState(
            reliability=reliability,
            supporting=tuple(by_role.get(LinkRole.SUPPORTS, [])),
            counter=tuple(by_role.get(LinkRole.CONTRADICTS, [])),
            dislocation=tuple(by_role.get(LinkRole.DISLOCATION, [])),
            catalyst=tuple(by_role.get(LinkRole.CATALYST, [])),
            listed_exposures=counted.listed, instrument_exposures=counted.instruments,
            transmission=card.s03_transmission, horizon=t.horizon, stance=t.stance,
            verification_hold=bool(holds), hold_reasons=tuple(holds), retrieval=retrieval,
            retrieval_note=retrieval_note, kind=t.kind,
            sector_exposures=counted.sectors, unverified_listings=counted.unverified,
            as_of=as_of,
            published=tuple((s.article_id, s.published_at.date()) for s in card.s09_sources
                            if s.published_at is not None),
            data_report_articles=tuple(s.article_id for s in card.s09_sources if s.article_class
                                       is ArticleClass.INDUSTRY_DATA_REPORT),
            # the contributing article's claims are read from the store, as the update path
            # reads them from its extraction
            timing_context=self._timing_context(
                by_role, {**all_claims, **{c.claim_id: c for c in
                                           self.store.claims_for_article(aid)}}, aid))
        pr = compute_priority(state, previous=prev.research_action,
                              evidence_direction=prev_v.evidence_direction,
                              previous_factors=prev.factors)
        refiled = refile_price_moves(card, all_claims)
        base = capped_conditionals(refiled)
        # a version says what changed: a conditional line stored as a fact is relabelled
        capped = sum(x[1] != y[1] for x, y in zip(card_sentences(refiled).values(),
                                                  card_sentences(base).values(), strict=True))
        mine = [c for c in corrections if c.thesis_id == thesis_id]
        for corr in mine:
            base = self._corrected(base, corr, all_claims, run_id)
        d = base.s08_decision
        new_card = base.model_copy(update={
            "header": base.header.model_copy(update={"research_action": pr.research_action}),
            "s05_affected": aff.model_copy(update={"sector_exposures": tuple(kept)}),
            "s06_why_now": base.s06_why_now.model_copy(
                update={"valuation_status": pr.valuation_status}),
            "s08_decision": d.model_copy(update={
                "research_action": pr.research_action,
                "investment_readiness": pr.investment_readiness,
                "readiness_note": pr.valuation_status, "rule_trace": pr.rules_fired})})
        if pr.research_action is prev.research_action and card_sha(new_card) == card_sha(card):
            return None
        new_card = new_card.model_copy(update={"header": new_card.header.model_copy(
            update={"analysis_as_of": as_of})})
        next_v = t.current_version + 1
        moved = len(card.s07_what_could_go_wrong.counter_evidence) \
            - len(new_card.s07_what_could_go_wrong.counter_evidence)
        summary = ("REASSESSED under the current research-action rules from stored evidence — no "
                   "article read, no model call: " + pr.change_reason
                   + ("; " + "; ".join(refused) if refused else "")
                   + (f"; {moved} price-move line(s) moved from counter-evidence to price context"
                      if moved else "")
                   + (f"; {capped} conditional line(s) relabelled SOURCE OPINION — a conditional "
                      f"is never a measured fact" if capped else "")
                   + "".join(f"; ANALYST CORRECTION {c.sentence_id} — {c.reason}" for c in mine))
        version = ThesisVersion(
            thesis_id=thesis_id, version=next_v, as_of=as_of, created_at=datetime.now(tz=UTC),
            run_id=run_id, engine_version=ENGINE_VERSION, content=new_card, priority=pr,
            evidence_direction=prev_v.evidence_direction, change_summary=summary,
            diffs=tuple(FieldDiff(field_id=f, change_class=c, old=o, new=n, claim_ids=ids)
                        for f, c, o, n, ids in diff_cards(card, new_card, {})),
            prior_content_sha=prev_v.content_sha, content_sha=card_sha(new_card))
        etype = event_type(prev.research_action, pr.research_action, {})
        ev = ChangeEvent(event_id="CE-" + _sha(thesis_id, str(next_v), etype, run_id)[:14],
                         thesis_id=thesis_id, version=next_v, event_type=etype, run_id=run_id,
                         as_of=as_of, created_at=datetime.now(tz=UTC), detail=summary,
                         diffs=version.diffs)
        # the card review's findings stand on the lines they were made on — found by their TEXT
        # (a refiled line has a new id) and carried to this run; a corrected line's old findings
        # no longer apply; the deterministic card checks are recomputed on the new card
        old_s, new_s = card_sentences(card), card_sentences(new_card)
        sid_of = {txt: sid for sid, (txt, _p, _c) in new_s.items()}
        carried: list[VerificationIssue] = []
        for i in self.store.issues(run_id=prev_v.run_id):
            tid, _, old_sid = i.ref_id.partition(":")
            if i.scope != "card_sentence" or tid != thesis_id or not (
                    i.code.startswith("REVIEW_") or i.code in CARRIED_CODES):
                continue
            sid = sid_of.get(old_s.get(old_sid, ("",))[0])
            if sid is None or any(c.sentence_id == sid for c in mine):
                continue
            carried.append(i.model_copy(update={
                "issue_id": "VI-" + _sha(run_id, i.issue_id)[:14], "run_id": run_id,
                "created_at": datetime.now(tz=UTC), "ref_id": f"{thesis_id}:{sid}",
                "detail": i.detail if sid == old_sid
                else i.detail.replace(f"{old_sid}:", f"{sid}:", 1),
                # a copy, not a new review: its finding keeps the origin of the one it copies
                # (report._findings), so a reviewer's dismissal survives the re-grade
                "copied_from": i.issue_id}))
        carried += deterministic_card_checks(new_card, all_claims, run_id)
        carried += [VerificationIssue(
            issue_id="VI-" + _sha(run_id, thesis_id, c.sentence_id, "correction")[:14],
            run_id=run_id, scope="card_sentence", ref_id=f"{thesis_id}:{c.sentence_id}",
            severity=IssueSeverity.INFO, code="ANALYST_CORRECTION",
            detail=f"{c.sentence_id}: {c.reason} | {new_s[c.sentence_id][0][:100]!r}",
            created_at=datetime.now(tz=UTC)) for c in mine]
        with self.store.tx():
            self.store.upsert_thesis(t.model_copy(update={"current_version": next_v}))
            self.store.add_thesis_version(version)
            self.store.add_event(ev)
            for i in carried:
                self.store.add_issue(i)
        return ThesisOutcome(thesis_id, t.title, False, next_v, ChangeClass.NO_MATERIAL_CHANGE,
                             pr.research_action, prev.research_action,
                             prev_v.evidence_direction, [etype])

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
    def _timing_context(self, by_role: dict[LinkRole, list[Claim]],
                        all_claims: dict[str, Claim], article_id: str) -> tuple[Claim, ...]:
        """Verified source evidence beyond the card's selected citations, for the TIMING test
        (priority.ThesisState.timing_context): the thesis's other linked claims (context,
        counter …) and every verified claim in a paragraph its evidence sits in. Observed
        2026-10-12: the same Citi sentence ("unlikely to clear before 2030") was a supporting,
        long-dated claim in one run and an undated context line in the next, which turned SKIP-3
        into WATCH."""
        cited = (LinkRole.SUPPORTS, LinkRole.DISLOCATION, LinkRole.CATALYST)
        blocks = {(c.article_id, c.block_id) for r in cited for c in by_role.get(r, [])}
        pool: dict[str, Claim] = {c.claim_id: c for r, cs in by_role.items() if r not in cited
                                  for c in cs}
        others = {a for a, _b in blocks} - {article_id}
        candidates = list(all_claims.values()) + [c for a in sorted(others)
                                                  for c in self.store.claims_for_article(a)]
        for c in candidates:
            if c.span_verified and (c.article_id, c.block_id) in blocks:
                pool.setdefault(c.claim_id, c)
        return tuple(pool.values())

    def _build_version(self, ctx: ArticleContext, thesis: Thesis, version: int,
                       h: VerifiedHypothesis | None, prev: CardContent | None,
                       links: list[ThesisClaimLink], claims: dict[str, Claim],
                       mentions: dict[str, Mention], resolutions: dict[str, SecurityResolution],
                       items: list[ChangeItem], vs_prior: str, novelty: str,
                       direction: EvidenceDirection, previous: ResearchAction | None,
                       prev_factors: tuple[object, ...], risk_sents: list[CardSentence],
                       rel_notes: list[CardSentence], counter: list[Claim], *,
                       change_summary: str, classes: dict[str, ChangeClass],
                       contribution: ChangeClass, prev_sha: str | None = None,
                       defer: bool = False) -> ThesisVersion:
        """The next version of a thesis. Its review issues and the CONTEXT links its card's
        citations need are written here — or, with `defer`, held in `self.deferred` for a caller
        that may DISCARD the version (a re-read that changes nothing), which writes them with the
        version or not at all (U6: a discarded version's links and review issues were stored)."""
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
        affected = self._relisted(affected, ctx.as_of)
        sources = self._sources(thesis.thesis_id, ctx, links, all_claims, contribution)
        hold_reasons = self._hold_reasons(links, all_claims)
        if not thesis.key_review and self._under_review(thesis):
            # an identity held for review is never an independent research opportunity — archived
            # or not
            hold_reasons = [*hold_reasons, IDENTITY_HOLD]

        published = tuple((s.article_id, s.published_at.date()) for s in sources
                          if s.published_at is not None)
        data_reports = tuple(s.article_id for s in sources
                             if s.article_class is ArticleClass.INDUSTRY_DATA_REPORT)

        def make(hold_extra: list[str]) -> tuple[CardContent, ResearchPriority]:
            holds = hold_reasons + hold_extra
            # an EXPOSURE is a point-in-time-verified common-equity line (a current-day ticker
            # map never counts), an ETF / index / basket the source attaches, or a sector it
            # names — ONE definition for both paths (cards.counted_exposures)
            counted = counted_exposures(affected)
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
                    held = by_role.setdefault(lk.role, [])
                    # one sentence read again from another version of the article is ONE piece
                    # of evidence — never counted twice (observed 2026-10-12: a re-read took a
                    # thesis's material evidence 4 → 8 with nothing new)
                    if not any(same_sentence_reread(o, c) for o in held):
                        held.append(c)
            timing_context = self._timing_context(by_role, all_claims, ctx.article.article_id)
            # the research-action gate needs the ANALYSIS text whole: a version whose only unread
            # pages are back matter BY THE DOCUMENT'S OWN CONTENTS LIST passes it, said so; it
            # stays PARTIAL everywhere else (verification still says "read only in part")
            retrieval = (ctx.version.retrieval_state
                         if ctx.version.retrieval_state is not RetrievalState.BLOCKED
                         else RetrievalState.PARTIAL)
            retrieval_note = ""
            if retrieval is RetrievalState.PARTIAL and ctx.version.unread_back_matter:
                retrieval = RetrievalState.FULL
                retrieval_note = (f"analysis text complete — {ctx.version.unread_back_matter}; "
                                  f"the document itself stays PARTIAL")
            state = ThesisState(
                reliability=max((ctx.reliability, *self._source_reliabilities(thesis.thesis_id)),
                                key=lambda r: {"high": 2, "medium": 1, "low": 0}[r]),
                supporting=tuple(by_role.get(LinkRole.SUPPORTS, [])),
                counter=tuple(by_role.get(LinkRole.CONTRADICTS, [])),
                dislocation=tuple(by_role.get(LinkRole.DISLOCATION, [])),
                catalyst=tuple(by_role.get(LinkRole.CATALYST, [])),
                listed_exposures=counted.listed, instrument_exposures=counted.instruments,
                transmission=draft.s03_transmission, horizon=thesis.horizon,
                stance=thesis.stance, verification_hold=bool(holds),
                hold_reasons=tuple(holds), retrieval=retrieval, retrieval_note=retrieval_note,
                kind=thesis.kind,
                sector_exposures=counted.sectors,
                unverified_listings=counted.unverified, as_of=ctx.as_of, published=published,
                data_report_articles=data_reports, timing_context=timing_context)
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
                card, pr = make([f"{REVIEW_HOLD}{len(material)} decision-bearing "
                                 f"sentence(s): " + ", ".join(material)])
                if anchors:
                    card = with_citations(card, anchors, all_claims)
        context = self._context_links(ctx, thesis.thesis_id, version, card, links, all_claims)
        if defer:
            self.deferred = (review_issues, context)
        else:
            with self.store.tx():
                for i in review_issues:
                    self.store.add_issue(i)
                for lk in context:
                    self.store.add_link(lk)
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

    def _relisted(self, av: AffectedView, as_of: date) -> AffectedView:
        """The card's exposures with every named listed company whose listing no line verifies
        resolved AGAIN, as of `as_of` (`relist`). 2026-10-16: four hyperscalers resolved before
        point-in-time verification existed stayed "not verified" for good, and their thesis read
        "no exposure"; resolved again as of its date, each verifies from its own 10-K / 10-Q."""
        if self.relist is None:
            return av
        stale = [c for c in av.companies if c.resolution_status is ResolutionStatus.LISTED_EQUITY
                 and c.role in EXPOSURE_ROLES
                 and not any(x.pit_status is PitStatus.VERIFIED for x in c.listings)]
        if not stale:
            return av
        return av.model_copy(update={"companies": tuple(
            self.relist(c, as_of) if c in stale else c for c in av.companies)})

    def _context_links(self, ctx: ArticleContext, tid: str, version: int, card: CardContent,
                       links: list[ThesisClaimLink], claims: dict[str, Claim]
                       ) -> list[ThesisClaimLink]:
        """Every claim the card cites is LINKED to the thesis. A citation outside the role lists
        — a source implication, a why-now view, a transmission step, a sector span, a re-anchored
        line — becomes a CONTEXT link, so the evidence trail QA re-derives from the registry is the
        one the card shows (found by QA on the real corpus, 2026-10-10)."""
        cited = [c for _t, _p, cids in card_sentences(card).values() for c in cids]
        cited += [c for se in card.s05_affected.sector_exposures for c in se.claim_ids]
        cited += [c for b in card.s05_affected.baskets for c in b.claim_ids]
        held = {lk.claim_id for lk in links} | {lk.claim_id for lk in self.store.links(tid)}
        return [ThesisClaimLink(
            thesis_id=tid, claim_id=cid, role=LinkRole.CONTEXT, first_version=version,
            change_class=ChangeClass.NO_MATERIAL_CHANGE,
            independence_group=claims[cid].origin_id or ctx.article.article_id)
            for cid in dict.fromkeys(cited) if cid not in held and cid in claims]

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
                        # its id hashes its content: a passage re-anchored by an earlier run (a
                        # re-analysis) is the claim first written, kept — never a clash
                        held = self.store.claim(pc.claim_id)
                        if held is None:
                            with self.store.tx():
                                self.store.add_claim(pc)
                        else:
                            pc = held
                        claims[pc.claim_id] = pool[pc.claim_id] = pc
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

    def _published_of(self, claims: list[Claim]) -> dict[str, date]:
        """Each claim's article's publication date — where a "since X" window ends."""
        out: dict[str, date] = {}
        for aid in {c.article_id for c in claims}:
            a = self.store.article(aid)
            if a is not None and a.published_at is not None:
                out[aid] = a.published_at.date()
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
                       own: list[Claim]) -> tuple[list[ThemeRelation], int]:
        """How a new thesis relates to every other. COMPETING — the only relation whose evidence
        is filed as CONTRADICTS — needs a DIRECT contradiction: the SAME claim (node, mechanism,
        segment, geography, timeframe) predicted the opposite way. Opposite directions that
        differ in any of those are RELATED: linked, never counter-evidence, never a weakening
        (review of PR #703, round 3: a fall in utility share prices does not contradict rising
        demand for on-site power). Same-direction theses that are not the same claim are
        ADJACENT SUPPORT: context, never a strengthening. Theses that only share a broader area
        (two children of one sector, or an area root and a child) are COUNTED, never linked: the
        pair is read from their keys, and a link per pair grew with the square of the theses in a
        sector (U43: 15,204 of 18,259 links and 42,182 card lines at 52 weeks)."""
        rels: list[ThemeRelation] = []
        now = datetime.now(tz=UTC)
        seg_label = {sg.id: sg.label for sg in self.taxonomy.segments}
        t_windows = evidence_windows(own, ctx.as_of, self._published_of(own))
        cids: tuple[str, ...] = ()
        n_area = 0
        for o in self.store.theses():
            if o.thesis_id == t.thesis_id or o.retired:  # a retired thesis is history only
                continue
            rel: RelationType | None = None
            role = ""
            why = ""
            opposite = {o.key_direction, t.key_direction} == {Direction.POSITIVE,
                                                              Direction.NEGATIVE}
            same_dir = o.key_direction == t.key_direction
            if o.key_node == t.key_node:
                o_claims = self._evidence_of(o.thesis_id)
                diffs = claim_differences(t, o, t_windows,
                                          evidence_windows(o_claims, ctx.as_of,
                                                           self._published_of(o_claims)),
                                          seg_label)
                if t.key_product != o.key_product:  # one key, two technologies: say which
                    pt, po = self.thesis_product(t), self.thesis_product(o)
                    if (pt and po and pt != po) or not diffs:  # never "US vs US" for a product
                        diffs = [*diffs, f"a different product ({pt or 'none named'} vs "
                                         f"{po or 'none named'})"]
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
            elif same_area(o.key_node, t.key_node):
                # an area root and a child, or two children of one sector: they share an area and
                # nothing more — counted, never linked (U43; U47: an area-root link had printed
                # "ADJACENT SUPPORT (parent / child)")
                n_area += 1
                continue
            elif o.key_node.startswith(t.key_node + ".") or t.key_node.startswith(o.key_node + "."):
                rel = RelationType.PARENT_CHILD
                role = (EvidenceRole.ADJACENT_SUPPORT.value if same_dir
                        else EvidenceRole.RELATED.value if opposite else "")
                why = (f"{o.key_node} and {t.key_node} are parent and child economics — never "
                       f"merged" + (" — adjacent support, never a confirmation" if same_dir
                                    else " — related, never counter-evidence" if opposite else ""))
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
        return rels, n_area

    def _event(self, ctx: ArticleContext, tid: str, version: int | None, etype: str,
               detail: str, diffs: tuple[FieldDiff, ...] = ()) -> ChangeEvent:
        return ChangeEvent(event_id="CE-" + _sha(tid, str(version), etype, ctx.run_id,
                                                 ctx.version.version_id)[:14],
                           thesis_id=tid, version=version, event_type=etype, run_id=ctx.run_id,
                           as_of=ctx.as_of, created_at=datetime.now(tz=UTC), detail=detail,
                           diffs=diffs)

    def _issue(self, ctx: ArticleContext, scope: str, ref: str, sev: IssueSeverity, code: str,
               detail: str) -> VerificationIssue:
        # the DETAIL is part of the id, as in verify._issue: two articles of one run on one key
        # (PRODUCT_SPLIT, SAME_KEY_IN_ARTICLE …) carry different details, and without it they
        # shared an id the append-only store refused — the second article failed (2026-10-13)
        return VerificationIssue(issue_id="VI-" + _sha(ctx.run_id, scope, ref, code, detail)[:14],
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
                           f"the rest are in {MORE_POINTER}",
                      provenance=Provenance.UNKNOWN, article_id=article_id)


#: a thesis a later version creates is a SIBLING of an earlier version's thesis when at least
#: this share of its sentences already sat on that thesis (face validity, 2026-10-12: on Citi's
#: re-read one shared sentence of twenty was cross-citation, 60 of 67 the same story re-keyed)
SIBLING_SHARE = 0.5
#: a product is what a thesis's evidence is ABOUT only when at least this share of its cited
#: claims name it — a passing mention is not its subject (face validity, Citi Gridlock
#: 2026-10-12: fuel cells 8 of 17 claims, gas turbines 10 of 33 — vs the transformer thesis's
#: one CCGT mention in 67 and the regulation thesis's one "utilities" in 10)
PRODUCT_MIN_SHARE = 0.2
#: two readings of one article rest on the SAME evidence when at least this share of EACH side's
#: cited sentences is shared — then a different mechanism family is one causal chain read at two
#: steps, not two theses (face validity, Citi Gridlock 2026-10-12: the fuel-cell readings, 14 of
#: 17 sentences one way; a reading with a third of its evidence its own is a second claim to judge)
SAME_EVIDENCE_SHARE = 2 / 3
#: what each mechanism family means for a listed company's earnings — said when a human is asked
#: whether two readings are one thesis or two separately falsifiable ones
FAMILY_CONSEQUENCE = {
    "volume": "earnings move with units or capacity sold",
    "price_cost": "earnings move with prices or input costs",
    "competition": "earnings move with share taken from rivals",
    "valuation": "the share price moves with the multiple, not with earnings",
    "policy": "rules change what can be earned",
    "market_structure": "how the market prices the group",
}


def _nests(a: str, b: str) -> bool:
    """Two segment sets ("x+y") where one contains the other — none nests with anything (a
    preview naming no segment, its full text naming one: the same thesis)."""
    sa, sb = set(filter(None, a.split("+"))), set(filter(None, b.split("+")))
    return sa <= sb or sb <= sa


def _same_subject(a: str, b: str) -> bool:
    """A segment RE-DERIVED for a held thesis agrees only when equal, or both named and nested —
    an unassigned one is no evidence of a shared subject (observed 2026-10-12: the transformer
    reading matched the skilled-labour thesis, whose re-derived segment is none)."""
    return a == b or (bool(a) and bool(b) and _nests(a, b))


def _evidence_overlap(a: VerifiedHypothesis, b: VerifiedHypothesis) -> tuple[int, int]:
    """(evidence `b` shares with `a`, evidence only `b` has) — supporting and dislocation claims,
    counted before `b` is folded into `a`. Observed 2026-10-12: a fuel-cell share hypothesis and
    a gas-generation equipment hypothesis shared one identity key and merged silently."""
    sa = set(a.supporting) | set(a.dislocation)
    sb = set(b.supporting) | set(b.dislocation)
    return len(sb & sa), len(sb - sa)


#: Sentences the DECISION rests on: the bottom line, the what-changed facts, the decision itself,
#: and dislocation evidence (a RESEARCH NOW condition). A review BLOCK on one of these HOLDS
#: promotion ("hold promotion if material claims lack source evidence"). A blocked NARRATIVE
#: sentence — transmission hypothesis, why-now prose, a risk line — is withheld from the card and
#: logged, but the action rests on the verified structured evidence, not on that prose.
MATERIAL_SECTIONS = ("s01.", "s02.", "s08.")


#: the hold a review's withheld decision-bearing lines put on a version — the ONE phrase its writer
#: (`_build_version`) and its reader (`review_holds`) share
REVIEW_HOLD = "review withheld "
IDENTITY_HOLD = ("identity under review — it may be the same thesis as one an earlier version of "
                 "this article created")


def review_holds(note: str) -> list[str]:
    """The review's withheld-lines holds in a stored F10 note (its hold reasons, "; "-joined):
    the only hold a reassess carries over, since it runs no review."""
    return [x for x in note.split("; ") if x.startswith(REVIEW_HOLD)]


def material_sentence(sid: str, text: str) -> bool:
    return sid.startswith(MATERIAL_SECTIONS) or text.startswith("Dislocation evidence:")


@dataclass
class _ChallengeHyp:
    claim_ids: list[str]


def _num_close(a: float, b: float) -> bool:
    return abs(a - b) <= 0.05 * max(abs(a), abs(b), 1e-9)


def _reading_for(new: Claim, same_measure: list[Claim]) -> Claim:
    """The held reading a new claim on the same measure is read against — whatever order the
    claims came in (U5: claim-id order made a third origin's confirmation of a moved date a
    "timing change" in 2 of 6 text variants): the same origin's latest (a correction, or a later
    reading of its series); else the latest it AGREES with (the same event date, or a close
    figure); else the latest. `same_measure` is in linking order, oldest first."""
    own = [e for e in same_measure if e.origin_id == new.origin_id]
    if own:
        return own[-1]
    if new.measure_key.startswith("event|"):
        agree = [e for e in same_measure if (e.period or "") == (new.period or "")]
    else:
        agree = [e for e in same_measure if new.value is not None and e.value is not None
                 and _num_close(new.value, e.value)]
    return (agree or same_measure)[-1]


def classify_claim(new: Claim, role: LinkRole, held: list[Claim]) -> tuple[ChangeClass, str]:
    """`held`: the thesis's claims in the order it took them in, oldest first."""
    same_fp = [e for e in held if e.fingerprint == new.fingerprint]
    if same_fp:
        return ChangeClass.REPEATED, (f"same measure, value and upstream origin as "
                                      f"{same_fp[0].claim_id} — attribution, not new evidence")
    reread = [e for e in held if same_sentence_reread(e, new)]
    if reread:
        return ChangeClass.REPEATED, (f"the same sentence and figure as {reread[0].claim_id}, "
                                      f"read again from another version of this article "
                                      f"({reread[0].article_version_id}) — not new evidence")
    if role is LinkRole.CONTRADICTS:
        return ChangeClass.CONTRADICTORY, "the source states evidence against this thesis"
    same_measure = [e for e in held if e.measure_key == new.measure_key
                    and not e.measure_key.startswith("stmt|")]
    if same_measure:
        e = _reading_for(new, same_measure)
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
