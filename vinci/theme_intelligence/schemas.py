"""Typed records for the theme-intelligence registry (brief §5) and the nine-section card (§3).

Three times are kept apart on every record that has them, because conflating them is how a
look-ahead happens: PUBLICATION time (when the source says it was published), AS-OF time (the date
a figure describes — "data as of February 5, 2026"), and INGESTION time (when this tool read it).

Every claim carries the exact quote span it came from (block id + character offsets) and the
structured value / unit / period it states — renderers print from those fields, never by
re-parsing a display string (CLAUDE.md: parsers consume structured values).

NO RECORD HERE CAN EXPRESS A TRADE. `research_action` is RESEARCH NOW / WATCH / SKIP — where to
spend analyst attention — and `investment_readiness` tops out at UNDERWRITE_CANDIDATE. There is no
buy / sell / target / weight field anywhere (pinned by a schema-walk test).
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DB_SCHEMA_VERSION = 2


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Mutable(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- enums -------------------------------------------------------------------------------------

class RetrievalState(StrEnum):
    FULL = "FULL"  # the article body was retrieved and parsed
    PARTIAL = "PARTIAL"  # a teaser / paywalled excerpt / truncated body — never analysed as full
    BLOCKED = "BLOCKED"  # refused, failed, or robots-disallowed — kept in coverage counts


class FieldStatus(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


class ArticleClass(StrEnum):
    PUBLISHER_COMMENTARY = "publisher_commentary"
    INSTITUTIONAL_RESEARCH = "institutional_research"
    INDUSTRY_DATA_REPORT = "industry_data_report"
    INDEPENDENT_RESEARCH = "independent_research"
    NEWS = "news"
    OTHER = "other"


class ClaimKind(StrEnum):
    METRIC = "metric"
    EVENT = "event"
    ASSERTION = "assertion"
    OPINION = "opinion"
    FORECAST = "forecast"
    RECOMMENDATION = "recommendation"
    RISK = "risk"


class Epistemic(StrEnum):
    ACTUAL = "actual"
    FORECAST = "forecast"
    OPINION = "opinion"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EntityType(StrEnum):
    COMPANY = "company"
    PRIVATE_COMPANY = "private_company"
    ETF_OR_FUND = "etf_or_fund"
    INDEX = "index"
    PRODUCT = "product"
    DATA_PROVIDER = "data_provider"
    PUBLISHER = "publisher"
    GOVERNMENT_OR_AGENCY = "government_or_agency"
    BASKET = "basket"
    OTHER_ORGANIZATION = "other_organization"
    SECTOR = "sector"  # an industry / sector / theme the source names as a population


class MentionRole(StrEnum):
    POTENTIAL_BENEFICIARY = "potential_beneficiary"
    POTENTIALLY_HARMED = "potentially_harmed"
    SECTOR_EXAMPLE = "sector_example"
    SPENDING_CUSTOMER = "spending_customer"
    INVESTOR = "investor"
    SUPPLIER = "supplier"
    CITED_BASKET = "cited_basket"
    RECOMMENDATION = "recommendation"
    RISK = "risk"
    DISRUPTOR = "disruptor"
    DATA_SOURCE = "data_source"
    COMPARATOR = "comparator"
    MARKET_INSTRUMENT = "market_instrument"
    PUBLISHER = "publisher"
    CONTEXT = "context"


#: Roles that make a named company an EXPOSURE of a thesis (vs a data source / context mention).
EXPOSURE_ROLES = frozenset({
    MentionRole.POTENTIAL_BENEFICIARY, MentionRole.POTENTIALLY_HARMED, MentionRole.SECTOR_EXAMPLE,
    MentionRole.SPENDING_CUSTOMER, MentionRole.SUPPLIER, MentionRole.RECOMMENDATION,
    MentionRole.DISRUPTOR, MentionRole.INVESTOR,
})


class Direction(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNCLEAR = "unclear"


class RecommendationStatus(StrEnum):
    NOT_A_RECOMMENDATION = "not_a_recommendation"
    EXPLICIT_RECOMMENDATION = "explicit_recommendation"
    RATING_STATED = "rating_stated"


class ResolutionStatus(StrEnum):
    LISTED_EQUITY = "LISTED_EQUITY"
    FUND = "FUND"
    INDEX = "INDEX"
    PRIVATE = "PRIVATE"
    UNRESOLVED = "UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_A_SECURITY = "NOT_A_SECURITY"


class Provenance(StrEnum):
    """How a card line is supported. What a SOURCE says is never one undifferentiated "fact": a
    publisher's ARGUMENT is not an established market fact, and a forecast is not an observation.
    The label of a line citing several claims is its WEAKEST support (opinion < forecast <
    observation), so an interpretation can never ride in on a measured figure beside it."""

    SOURCE_OPINION = "SOURCE OPINION"  # the publisher's interpretation, argument or recommendation
    MEASURED_OBSERVATION = "MEASURED OBSERVATION"  # a measured / reported actual the source states
    FORECAST = "FORECAST"  # a projection, estimate or forward (e.g. NTM) figure in the source
    MODEL_INFERENCE = "MODEL INFERENCE"  # this tool's own reasoning
    EXTERNALLY_VERIFIED = "EXTERNALLY VERIFIED"  # confirmed against an independent primary source
    UNKNOWN = "UNKNOWN"
    ARTICLE_FACT = "ARTICLE FACT"  # LEGACY label (ti-engine-1 records) — loads, never written now


#: Labels that assert the SOURCE says it — each must cite verified claims (pass-2 checks).
SOURCE_LABELS = frozenset({Provenance.SOURCE_OPINION, Provenance.MEASURED_OBSERVATION,
                           Provenance.FORECAST, Provenance.ARTICLE_FACT})


class ThesisKind(StrEnum):
    """An INVESTMENT THESIS argues a profit-transmission mechanism for listed equities. A
    MARKET-REGIME record captures a market-structure condition (breadth, correlation, dispersion,
    volatility, cross-asset correlation) together with the research implication the source draws
    — never forced into a buy thesis, never dropped because it names no stock."""

    INVESTMENT_THESIS = "investment_thesis"
    MARKET_REGIME = "market_regime"


class InstrumentClass(StrEnum):
    """What a listed line IS, read from the issuer's own registration title (SEC cover page)."""

    COMMON_EQUITY = "common_equity"
    PREFERRED = "preferred"  # incl. depositary shares representing preferred stock
    DEBT = "debt"
    DEPOSITARY_RECEIPT = "depositary_receipt"  # ADS / ADR of ordinary shares
    WARRANT_OR_RIGHT = "warrant_or_right"
    UNIT = "unit"
    FUND_SHARE = "fund_share"
    UNKNOWN = "unknown"


class PitStatus(StrEnum):
    """Was this line a registered security ON THE ARTICLE'S DATE? A current-day ticker map is not
    point-in-time; only an issuer filing dated on or before the as-of date can say so."""

    VERIFIED = "VERIFIED"  # on the cover page of the issuer's latest filing on or before the date
    NOT_REGISTERED_AS_OF = "NOT_REGISTERED_AS_OF"  # first registered after the date
    UNVERIFIED = "UNVERIFIED"  # no point-in-time source could decide


class ResearchAction(StrEnum):
    RESEARCH_NOW = "RESEARCH NOW"
    WATCH = "WATCH"
    SKIP = "SKIP"


ACTION_RANK = {ResearchAction.SKIP: 0, ResearchAction.WATCH: 1, ResearchAction.RESEARCH_NOW: 2}


class EvidenceDirection(StrEnum):
    NEW = "NEW"
    STRONGER = "STRONGER"
    WEAKER = "WEAKER"
    UNCHANGED = "UNCHANGED"
    MIXED = "MIXED"


class InvestmentReadiness(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    UNRESOLVED = "UNRESOLVED"
    UNDERWRITE_CANDIDATE = "UNDERWRITE_CANDIDATE"


class ChangeClass(StrEnum):
    NEW = "new"
    INDEPENDENT_CONFIRMATION = "independent confirmation"
    REPEATED = "repeated"
    CONTRADICTORY = "contradictory"
    CORRECTION = "correction"
    TIMING_CHANGE = "timing change"
    NO_MATERIAL_CHANGE = "no material change"
    NOVELTY_UNVERIFIED = "novelty_unverified"


#: A contribution of these classes is MATERIAL: it creates a new thesis version.
MATERIAL_CLASSES = frozenset({
    ChangeClass.NEW, ChangeClass.INDEPENDENT_CONFIRMATION, ChangeClass.CONTRADICTORY,
    ChangeClass.CORRECTION, ChangeClass.TIMING_CHANGE, ChangeClass.NOVELTY_UNVERIFIED,
})


class LinkRole(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    RISK = "risk"
    DISLOCATION = "dislocation"
    CATALYST = "catalyst"
    CONTEXT = "context"


class RelationType(StrEnum):
    SIBLING = "SIBLING"
    #: a DIRECT contradiction: the same claim (node, mechanism, segment, geography, timeframe)
    #: predicted the opposite way — the only relation that files evidence as CONTRADICTS
    COMPETING = "COMPETING"
    PARENT_CHILD = "PARENT_CHILD"
    REVIEW_NEEDED = "REVIEW_NEEDED"
    #: the opposite direction on the same node WITHOUT a direct incompatibility (another
    #: mechanism, segment, geography or timeframe) — linked, never used as counter-evidence
    RELATED = "RELATED"


class EvidenceRole(StrEnum):
    """How one thesis's evidence bears on another (review of PR #703, round 3)."""

    #: the SAME thesis identity, new or independently confirming claims — may strengthen it
    DIRECT_CONFIRMATION = "DIRECT_CONFIRMATION"
    #: same direction, related but not the same claim (another segment, mechanism or node) —
    #: shown as context, never strengthens the thesis
    ADJACENT_SUPPORT = "ADJACENT_SUPPORT"
    #: a direct contradiction — the only role that can weaken a thesis
    CONTRADICTION = "CONTRADICTION"
    #: the same upstream origin repeated — attribution only
    REPEATED_SOURCE = "REPEATED_SOURCE"
    #: the opposite direction on related economics, not a contradiction
    RELATED = "RELATED"


def identity_key(node: str, mechanism: str, direction: str, geography: str,
                 segment: str = "", review: str = "") -> str:
    """The ONE thesis identity: node | mechanism | direction | geography, plus the SEGMENT within
    the node when the taxonomy defines segments for it (evidence about NAND / SSD is not the same
    claim as evidence about DRAM / HBM), plus a review tag for an unclassified (`other`) thesis.
    Without a segment or review tag the key is exactly the first build's — its ids are kept."""
    key = f"{node}|{mechanism}|{direction}|{geography}"
    if segment:
        key += f"|seg:{segment}"
    if review:
        key += f"|review:{review}"
    return key


class ThesisStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVIEW_NEEDED = "REVIEW_NEEDED"
    ARCHIVED = "ARCHIVED"


class StanceInSource(StrEnum):
    ASSERTED = "asserted"
    CONDITIONAL = "conditional"
    SPECULATIVE = "speculative"
    REPORTED_VIEW = "reported_view"


class Horizon(StrEnum):
    NEXT_2_4_QUARTERS = "next_2_4_quarters"
    LONGER_TERM = "longer_term"
    UNCLEAR = "unclear"


class RunStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"


class IssueSeverity(StrEnum):
    BLOCK = "BLOCK"  # the fact is not supported by its source — it must not render as fact
    HOLD = "HOLD"  # promotion is held until a human looks
    WARN = "WARN"
    INFO = "INFO"


class WeeklyCategory(StrEnum):
    NEW = "NEW"
    UPGRADED = "UPGRADED"
    DOWNGRADED = "DOWNGRADED"
    CHALLENGED = "CHALLENGED"
    UNCHANGED_MATERIAL = "UNCHANGED BUT MATERIAL"
    UNCHANGED = "UNCHANGED"
    ARCHIVED = "ARCHIVED"


# --- source records ----------------------------------------------------------------------------

class Author(Frozen):
    name: str
    title: str | None = None
    source_field: str  # where on the page it was read (e.g. "json-ld author", "byline block b041")


class Block(Frozen):
    """One addressable unit of article text. `block_id` is stable for a given content hash."""

    block_id: str
    kind: str  # heading | paragraph | list_item | chart_title | chart_source | chart_description
    #           | disclaimer | byline | other
    text: str
    sha256: str
    section: str | None = None  # nearest preceding heading
    order: int


class Article(Frozen):
    article_id: str
    canonical_url: str
    source_id: str
    publisher: str
    title: str | None
    title_source: str | None
    authors: tuple[Author, ...]
    authors_status: FieldStatus
    published_at: datetime | None
    published_raw: str | None
    published_source: str | None
    published_status: FieldStatus
    article_class: ArticleClass
    article_class_basis: str
    first_seen_at: datetime


class ArticleVersion(Frozen):
    """One retrieval of one article. Immutable; a re-fetch with the same content hash is the same
    version (idempotent), a changed body is a NEW version and never overwrites the old one."""

    version_id: str
    article_id: str
    retrieved_at: datetime
    http_status: int | None
    final_url: str | None
    retrieval_state: RetrievalState
    retrieval_note: str
    raw_sha256: str | None
    content_sha256: str | None
    modified_at: datetime | None  # the page's own "updated" stamp — never the publication date
    modified_source: str | None
    evidence_location: str | None  # local path of the raw response (git-ignored)
    parser_version: str
    body_word_count: int
    blocks: tuple[Block, ...] = ()


class EvidenceSource(Frozen):
    """The UPSTREAM origin of a figure (e.g. 'Bloomberg Finance L.P.'), distinct from the article
    that repeats it. Two articles citing one origin for one measure are ONE piece of evidence."""

    origin_id: str
    name: str
    kind: str  # data_vendor | research_firm | company_disclosure | publisher_own | unattributed


class Claim(Frozen):
    claim_id: str
    article_id: str
    article_version_id: str
    block_id: str
    char_start: int
    char_end: int
    quote: str
    statement: str
    kind: ClaimKind
    epistemic: Epistemic
    metric: str | None = None
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    comparator: str | None = None
    period: str | None = None
    measured_as_of: date | None = None
    geography: str | None = None
    scope: str | None = None
    origin_id: str | None = None
    attributed_source_text: str | None = None
    qualifiers: tuple[str, ...] = ()
    approximate: bool = False
    chart_derived: bool = False
    confidence: Confidence
    span_verified: bool
    number_verified: bool | None
    verification_notes: tuple[str, ...] = ()
    measure_key: str  # scope|metric|period|unit — what is measured, independent of the value
    fingerprint: str  # measure_key|value|origin — the evidence identity for dedup / independence
    extraction_id: str


class Mention(Frozen):
    """An organization / security / instrument EXPLICITLY NAMED by the source. Nothing inferred
    lives here (inferred candidates go to the separately-labelled enrichment registry)."""

    mention_id: str
    article_id: str
    article_version_id: str
    name_as_written: str
    normalized_name: str
    entity_type: EntityType
    role: MentionRole
    role_detail: str
    direction: Direction
    recommendation_status: RecommendationStatus
    block_id: str
    quote: str
    issuer_name_hint: str | None = None
    ticker_hint: str | None = None
    claim_ids: tuple[str, ...] = ()
    source_explicit: Literal[True] = True


class Listing(Frozen):
    ticker: str
    exchange: str | None
    note: str | None = None
    security_class: str | None = None  # the issuer's own title, e.g. "Class A Common Stock"
    instrument: InstrumentClass = InstrumentClass.UNKNOWN
    pit_status: PitStatus = PitStatus.UNVERIFIED
    pit_source: str | None = None  # the filing that decided it (form, date, accession)


class SecurityResolution(Frozen):
    resolution_id: str
    normalized_name: str
    status: ResolutionStatus
    listings: tuple[Listing, ...] = ()
    cik: str | None = None
    registrant: str | None = None
    method: str
    source_ref: str
    resolved_at: datetime
    note: str = ""
    #: the issuer's OTHER lines — not common equity, or not registered on the as-of date. Kept for
    #: the audit, never presented as the company's stock exposure.
    other_securities: tuple[Listing, ...] = ()


class EnrichmentCandidate(Frozen):
    """OPTIONAL, separately-labelled external hypothesis: a company the SOURCE DID NOT NAME. It
    never appears in a card's source-explicit company list."""

    enrichment_id: str
    thesis_id: str
    name: str
    rationale: str
    evidence: str
    label: Literal["EXTERNAL HYPOTHESIS — not named by the source"] = (
        "EXTERNAL HYPOTHESIS — not named by the source")


# --- the nine-section card -------------------------------------------------------------------

class CardSentence(Frozen):
    text: str
    provenance: Provenance
    claim_ids: tuple[str, ...] = ()


class CardHeader(Frozen):
    thesis_id: str
    title: str
    sector: str
    region: str
    research_action: ResearchAction
    evidence_direction: EvidenceDirection
    horizon: str
    last_material_update: date
    status: ThesisStatus
    ancestry: tuple[str, ...]
    kind: ThesisKind = ThesisKind.INVESTMENT_THESIS
    #: the UTC DATE this registry actually first ingested the thesis (wall clock) — "new to the
    #: registry", never "new to market"; never a simulated as-of date
    first_detected: date | None = None
    #: publication date of the latest contributing source article
    latest_article_date: date | None = None
    #: the exact UTC time the registry first ingested the thesis (wall clock)
    first_ingested_at: datetime | None = None
    #: the ANALYSIS as-of date of this version — in a historical replay it precedes ingestion
    analysis_as_of: date | None = None


class ChangeItem(Frozen):
    change_class: ChangeClass
    text: str
    provenance: Provenance
    claim_ids: tuple[str, ...] = ()
    article_id: str | None = None
    original_date: str | None = None  # the source's publication / as-of date for this change
    period: str | None = None


class WhatChanged(Frozen):
    items: tuple[ChangeItem, ...]
    vs_prior: str
    novelty: str


class TransmissionStep(Frozen):
    #: industry_shift | volumes | pricing | costs | margins | cash_flow | listed_earnings — the
    #: earnings chain — or market_reaction: a share-price / valuation / index move, which is the
    #: market's RESPONSE and never itself a mechanism by which earnings change
    step: str
    text: str
    provenance: Provenance
    claim_ids: tuple[str, ...] = ()


class EvidenceRow(Frozen):
    claim_id: str
    label: str
    value_text: str | None
    value: float | None
    unit: str | None
    period: str | None
    measured_as_of: date | None
    epistemic: Epistemic
    approximate: bool
    chart_derived: bool
    comparator: str | None
    qualifiers: tuple[str, ...]
    origin: str | None
    article_id: str
    block_id: str
    quote: str
    role: LinkRole
    change_class: ChangeClass
    also_reported_in: tuple[str, ...] = ()  # article ids repeating the SAME origin + value


class AffectedCompany(Frozen):
    mention_id: str
    name_as_written: str
    resolution_status: ResolutionStatus
    listings: tuple[Listing, ...]  # point-in-time verified COMMON-EQUITY lines only
    cik: str | None
    role: MentionRole  # the role the SOURCE states (e.g. capex spender) — never rewritten
    role_detail: str
    direction: Direction
    recommendation_status: RecommendationStatus
    article_id: str
    quote: str
    #: the THESIS's reading of this name (e.g. "potential beneficiary") and what supports it:
    #: SOURCE OPINION when the source says so, MODEL INFERENCE when the thesis infers it
    exposure_reading: str | None = None
    exposure_provenance: Provenance | None = None
    other_securities: tuple[Listing, ...] = ()  # non-common or not-yet-registered lines (audit)


class SectorExposure(Frozen):
    """A sector / industry / theme the SOURCE names as exposed — a research opportunity does not
    need an individual ticker, but it does need the source to name the population."""

    name: str
    direction: Direction
    provenance: Provenance
    quote: str
    article_id: str
    claim_ids: tuple[str, ...] = ()


class AffectedView(Frozen):
    companies: tuple[AffectedCompany, ...]
    instruments: tuple[AffectedCompany, ...]  # ETFs / indices named by the source
    sectors: tuple[str, ...]
    baskets: tuple[CardSentence, ...]  # cited baskets WITHOUT members — never expanded
    private_or_unlisted: tuple[AffectedCompany, ...]
    enrichment: tuple[EnrichmentCandidate, ...] = ()
    #: named entities that are not securities (products, cited baskets, agencies) — never companies
    not_securities: tuple[AffectedCompany, ...] = ()
    #: every OTHER organization the contributing source(s) name, with its stated role — shown so
    #: the card lists all named entities, but NOT exposures of this thesis
    also_named: tuple[AffectedCompany, ...] = ()
    #: sectors / themes the source names as exposed (verified spans)
    sector_exposures: tuple[SectorExposure, ...] = ()


class WhyNow(Frozen):
    near_term: tuple[CardSentence, ...]
    structural: tuple[CardSentence, ...]
    catalyst_window: str  # "UNKNOWN" when the source names none
    valuation_status: str  # always explicit; NOT_ASSESSED without consensus/valuation data


class WhatCouldGoWrong(Frozen):
    counter_evidence: tuple[CardSentence, ...]
    alternative_mechanisms: tuple[CardSentence, ...]
    disconfirming_observables: tuple[CardSentence, ...]
    unknowns: tuple[CardSentence, ...]
    market_risks: tuple[CardSentence, ...]


class Decision(Frozen):
    research_action: ResearchAction
    next_step: CardSentence
    raise_priority_if: tuple[CardSentence, ...]
    lower_priority_if: tuple[CardSentence, ...]
    investment_readiness: InvestmentReadiness
    readiness_note: str
    rule_trace: tuple[str, ...]


class SourceRef(Frozen):
    article_id: str
    title: str | None
    authors: tuple[str, ...]
    authors_status: FieldStatus
    publisher: str
    published_at: datetime | None
    published_status: FieldStatus
    url: str
    article_class: ArticleClass
    retrieval_state: RetrievalState
    upstream_origins: tuple[str, ...]
    claim_ids: tuple[str, ...]
    contribution: ChangeClass


class CardContent(Frozen):
    """The universal nine-section Living Thesis Card. The section order and field ids are fixed;
    a section may hold UNKNOWN values but is never dropped."""

    header: CardHeader
    s01_bottom_line: tuple[CardSentence, ...]
    s02_what_changed: WhatChanged
    s03_transmission: tuple[TransmissionStep, ...]
    s04_key_evidence: tuple[EvidenceRow, ...]
    s05_affected: AffectedView
    s06_why_now: WhyNow
    s07_what_could_go_wrong: WhatCouldGoWrong
    s08_decision: Decision
    s09_sources: tuple[SourceRef, ...]


SECTION_IDS = (
    ("s01_bottom_line", "01 BOTTOM LINE"),
    ("s02_what_changed", "02 WHAT CHANGED?"),
    ("s03_transmission", "03 WHY COULD STOCKS BENEFIT OR SUFFER?"),
    ("s04_key_evidence", "04 KEY EVIDENCE & NUMBERS"),
    ("s05_affected", "05 AFFECTED COMPANIES / SECTORS"),
    ("s06_why_now", "06 WHY NOW? (NEXT 2-4 QUARTERS)"),
    ("s07_what_could_go_wrong", "07 WHAT COULD GO WRONG?"),
    ("s08_decision", "08 DECISION & NEXT TRIGGER"),
    ("s09_sources", "09 SOURCES & CHANGE HISTORY"),
)


# --- thesis registry ---------------------------------------------------------------------------

class PriorityFactor(Frozen):
    factor_id: str
    value: str
    note: str
    claim_ids: tuple[str, ...] = ()


class ResearchPriority(Frozen):
    research_action: ResearchAction
    evidence_direction: EvidenceDirection
    investment_readiness: InvestmentReadiness
    factors: tuple[PriorityFactor, ...]
    rules_fired: tuple[str, ...]
    previous_action: ResearchAction | None
    change_reason: str
    valuation_status: str


class FieldDiff(Frozen):
    field_id: str
    change_class: ChangeClass
    old: str | None
    new: str | None
    claim_ids: tuple[str, ...] = ()
    note: str = ""


class Thesis(Mutable):
    """The CURRENT pointer for one living thesis. Its history is the immutable ThesisVersion rows;
    only `current_version`, `status` and `last_material_update` move."""

    thesis_id: str
    key_node: str
    key_mechanism: str
    key_direction: Direction
    key_geography: str
    title: str
    sector: str
    region: str
    status: ThesisStatus
    current_version: int
    created_at: datetime
    created_as_of: date
    last_material_update: date
    ancestry: tuple[str, ...]
    stance: StanceInSource  # strongest stance any contributing source takes
    horizon: Horizon
    kind: ThesisKind = ThesisKind.INVESTMENT_THESIS
    #: the segment(s) within the node the evidence names ("dram_hbm+nand_ssd"); "" = none defined
    key_segment: str = ""
    #: the review tag of an unclassified (`other`) thesis — part of its identity
    key_review: str = ""

    @property
    def identity(self) -> str:
        return identity_key(self.key_node, self.key_mechanism, self.key_direction.value,
                            self.key_geography, self.key_segment, self.key_review)


class ThesisVersion(Frozen):
    thesis_id: str
    version: int
    as_of: date
    created_at: datetime
    run_id: str
    engine_version: str
    content: CardContent
    priority: ResearchPriority
    evidence_direction: EvidenceDirection
    change_summary: str
    diffs: tuple[FieldDiff, ...]
    prior_content_sha: str | None
    content_sha: str


class ThesisClaimLink(Frozen):
    thesis_id: str
    claim_id: str
    role: LinkRole
    first_version: int
    change_class: ChangeClass
    independence_group: str  # origin id, or the article id for an un-attributed claim


class ArticleThesisContribution(Frozen):
    contribution_id: str
    article_id: str
    thesis_id: str
    version: int | None  # None when the article changed nothing material (no new version)
    contribution: ChangeClass
    claim_ids: tuple[str, ...]
    run_id: str
    as_of: date


class ThemeRelation(Frozen):
    relation_id: str
    from_thesis: str
    to_thesis: str
    relation: RelationType
    reason: str
    claim_ids: tuple[str, ...] = ()
    run_id: str
    created_at: datetime
    #: how the newer thesis's evidence bears on the other (EvidenceRole value); "" = structural only
    evidence_role: str = ""


class ChangeEvent(Frozen):
    event_id: str
    thesis_id: str
    version: int | None
    event_type: str  # CREATED | UPDATED | UPGRADED | DOWNGRADED | CHALLENGED | REVIEW_NEEDED | ...
    run_id: str
    as_of: date
    created_at: datetime
    detail: str
    diffs: tuple[FieldDiff, ...] = ()


class SourceCoverage(Mutable):
    source_id: str
    publisher: str
    channel: str
    method: str
    entry_points: list[str] = Field(default_factory=list)
    checked_at: datetime | None = None
    status: str = "NOT_RUN"  # OK | PARTIAL | BLOCKED | ERROR | NOT_RUN
    discovered: int = 0
    in_window: int = 0
    undated: int = 0
    new: int = 0
    already_known: int = 0
    skipped_out_of_window: int = 0
    inaccessible: int = 0
    processed: int = 0
    queued: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    truncation: str | None = None


class WeeklyRun(Mutable):
    run_id: str
    mode: str  # scan | article | fixture
    window_from: date | None
    window_to: date | None
    as_of: date
    started_at: datetime
    finished_at: datetime | None = None
    status: RunStatus
    llm_provider: str
    llm_model: str
    extract_prompt_version: str
    review_prompt_version: str
    parser_version: str
    engine_version: str
    db_schema_version: int
    complete_prompt_version: str = ""
    sources: list[SourceCoverage] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    tokens: dict[str, int] = Field(default_factory=dict)
    cost_usd: float | None = None
    fetch_seconds: float = 0.0
    llm_seconds: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    output_dir: str | None = None
    checkpoint: dict[str, str] = Field(default_factory=dict)


class Snapshot(Frozen):
    snapshot_id: str
    run_id: str
    as_of: date
    thesis_versions: tuple[tuple[str, int], ...]
    created_at: datetime
    report_paths: tuple[str, ...]


class FigureCheck(Frozen):
    """One figure the ARTICLE states, and what happened to it — the completeness ledger is built
    from the article text, never from the claims the first model happened to select."""

    block_id: str
    figure: str
    sentence: str
    status: str  # captured | added_by_completeness_pass | immaterial | uncaptured
    claim_ids: tuple[str, ...] = ()
    reason: str = ""
    #: why an OPEN figure is open: verification_failed | capture_not_verified | no_account |
    #: pass_not_run — "" when it is accounted for
    open_cause: str = ""


class BlockCheck(Frozen):
    """One ARGUMENT block of the article and what accounts for it."""

    block_id: str
    status: str  # anchored | covered | added | immaterial | unreviewed
    hypothesis_ids: tuple[str, ...] = ()
    reason: str = ""
    #: verified claims a covered / added account names (the account is checkable through them)
    claim_ids: tuple[str, ...] = ()
    #: why an OPEN block is open: account_names_no_record | no_account | pass_not_run — or ""
    open_cause: str = ""


class CompletenessReport(Frozen):
    article_version_id: str
    run_id: str
    figures: tuple[FigureCheck, ...]
    argument_blocks: tuple[str, ...]  # body blocks carrying argument text
    blocks_without_claims: tuple[str, ...]  # argument blocks no verified claim anchors to
    added_claims: int
    added_mentions: int
    added_hypotheses: int
    added_risks: int
    prompt_version: str
    created_at: datetime
    blocks: tuple[BlockCheck, ...] = ()
    #: the LLM re-read ran (False: only the deterministic ledger — the gap is then visible)
    pass_ran: bool = True
    note: str = ""

    @property
    def uncaptured(self) -> tuple[FigureCheck, ...]:
        return tuple(f for f in self.figures if f.status == "uncaptured")

    @property
    def unaccounted_blocks(self) -> tuple[BlockCheck, ...]:
        return tuple(b for b in self.blocks if b.status == "unreviewed")


class VerificationIssue(Frozen):
    issue_id: str
    run_id: str
    scope: str  # claim | mention | card_sentence | article | thesis
    ref_id: str
    severity: IssueSeverity
    code: str
    detail: str
    created_at: datetime
