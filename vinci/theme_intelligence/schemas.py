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

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

DB_SCHEMA_VERSION = 8


def _aware(d: datetime | None) -> datetime | None:
    """A publication instant is always timezone-aware: a date-only or offset-less stamp reads as
    UTC (documents.py's convention). Naive and aware instants cannot be compared, and one naive
    date in a registry crashed every desk render beside an aware one — stored records too."""
    return d.replace(tzinfo=UTC) if d is not None and d.tzinfo is None else d


PublishedAt = Annotated[datetime | None, AfterValidator(_aware)]


def utc_day(t: datetime) -> date:
    """The UTC calendar day of an instant — the day a run's as-of (a UTC date) is compared
    with. A +08:00 post stamped after 16:00 UTC is on the NEXT day by its own clock: read that
    way, it was refused as published after the as-of (2026-10-14)."""
    return (t if t.tzinfo else t.replace(tzinfo=UTC)).astimezone(UTC).date()


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
    #: opposite predictions of the same thesis claim whose CLAIMS could not be shown either
    #: contradictory or compatible — held for a human; nothing changes automatically
    CONTRADICTION_REVIEW = "CONTRADICTION_REVIEW"


def same_area(a: str, b: str) -> bool:
    """Two value-chain nodes that share a broader area and nothing more: an area root and a node
    in it, or two nodes of one area neither of which is the other's parent. ONE rule for the
    engine (it counts such theses, never links them — U43) and the desk (its "same broader area"
    fold)."""
    if a == b or a.split(".")[0] != b.split(".")[0]:
        return False
    if "." not in a or "." not in b:
        return True
    return not (a.startswith(b + ".") or b.startswith(a + "."))


def identity_key(node: str, mechanism: str, direction: str, geography: str,
                 segment: str = "", review: str = "", product: str = "",
                 retired: str = "") -> str:
    """The ONE thesis identity: node | mechanism | direction | geography, plus the SEGMENT within
    the node when the taxonomy defines segments for it (evidence about NAND / SSD is not the same
    claim as evidence about DRAM / HBM), plus a review tag for an unclassified (`other`) thesis,
    plus a PRODUCT only when one key held two technologies with distinct evidence (engine.py).
    Without a segment, review tag or product the key is exactly the first build's — its ids are
    kept. A RETIRED thesis (re-analysis, `retired` = the run that retired it) carries the run in
    its key, which frees the bare key for the theses its articles' re-analysis creates."""
    key = f"{node}|{mechanism}|{direction}|{geography}"
    if segment:
        key += f"|seg:{segment}"
    if review:
        key += f"|review:{review}"
    if product:
        key += f"|prod:{product}"
    if retired:
        key += f"|retired:{retired}"
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

#: an author's `source_field` when the OPERATOR states it — at upload (`--author`) or later
#: (`author`, attribution.py) — never read from the page
OPERATOR_STATED = "operator-stated"


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
    #: the PAGE of a manual document (PDF) the block was read from — None for a web page
    page: int | None = None


class Article(Frozen):
    article_id: str
    canonical_url: str
    source_id: str
    publisher: str
    title: str | None
    title_source: str | None
    authors: tuple[Author, ...]
    authors_status: FieldStatus
    published_at: PublishedAt
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
    #: the publication date THIS version's own document states, and where it was read — a page
    #: and the report it links can be dated differently; both are kept, never conflated
    document_date: date | None = None
    document_date_source: str | None = None
    #: the ONLY unread part is back matter by the document's own contents list (the basis) — the
    #: analysis text is then complete for the research-action gate; the version stays PARTIAL
    unread_back_matter: str = ""


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
    never appears in a card's source-explicit company list, and no priority rule reads it."""

    enrichment_id: str
    thesis_id: str
    name: str
    #: how the thesis's step reaches this company's earnings, in the model's words
    rationale: str
    #: the card line the proposal rests on ("s03.1: <the step's text>") — the thesis, not a source
    evidence: str
    label: Literal["EXTERNAL HYPOTHESIS — not named by the source"] = (
        "EXTERNAL HYPOTHESIS — not named by the source")
    # (2026-10-14, the enrichment step) — defaults keep every stored card's empty list valid
    direction: Direction = Direction.UNCLEAR
    step_id: str = ""  # the card's transmission line it rests on (s03.N)
    business: str = ""  # what the company does, as the model states it (the identity check's input)
    ticker_hint: str | None = None  # the model's ticker — never shown unless the SEC verifies it
    resolution_status: ResolutionStatus = ResolutionStatus.UNRESOLVED
    listings: tuple[Listing, ...] = ()  # point-in-time verified common-equity lines only
    registrant: str | None = None
    resolution_note: str = ""
    #: the SEC files the issuer as a FOREIGN private issuer (20-F / 40-F): its US line is an ADR
    #: or a cross-listing, never substituted for verified common equity
    foreign_filer: bool = False
    # (2026-10-15) — defaults keep every stored set valid
    #: the label of the step it rests on, as the card stated it when proposed. A step that is
    #: not a fact (an opinion, a forecast, our inference) makes the direction a CONDITION: the
    #: company is exposed, and would benefit / be hurt only IF the step holds. None: proposed
    #: before the label was recorded (read from the card version the set rests on)
    step_label: Provenance | None = None
    #: the BASIS the model states: how the company earns from the exposed line (`BASIS_MODELS`)
    #: and which line it is — checked against the company's own annual report
    revenue_model: str = ""
    revenue_line: str = ""
    #: IN_FILING — the filing's revenue-source sentence names that model; FILING_NAMES_OTHER — it
    #: names another and not this one; NOT_DESCRIBED — the filing was read and states no
    #: revenue-source sentence in these words; UNCHECKED — not read (`basis_note` says why)
    basis_check: Literal["IN_FILING", "FILING_NAMES_OTHER", "NOT_DESCRIBED", "UNCHECKED"] = (
        "UNCHECKED")
    #: the filing's own revenue-source sentence(s), verbatim and capped — what the check read
    basis_quote: tuple[str, ...] = ()
    basis_source: str = ""  # "10-K filed 2025-02-26 (0001447669-25-000014)"
    basis_note: str = ""


class EnrichmentSet(Frozen):
    """One enrichment pass over ONE thesis version: the companies its mechanism implies, as the
    model proposes them — each an EXTERNAL HYPOTHESIS, never a source fact. Append-only; a later
    pass over a later version is a new set. What validation refused is kept beside it."""

    set_id: str
    thesis_id: str
    thesis_version: int
    run_id: str
    as_of: date
    created_at: datetime
    model: str
    prompt_version: str
    candidates: tuple[EnrichmentCandidate, ...]
    refused: tuple[str, ...] = ()  # proposals validation set aside, each with why
    label: Literal["EXTERNAL HYPOTHESIS — not named by the source"] = (
        "EXTERNAL HYPOTHESIS — not named by the source")


# --- market context ("is it priced?") ---------------------------------------------------------

#: what every market-context surface says first: evidence for the reader, outside the rules
MARKET_LABEL = ("MARKET CONTEXT — evidence for your judgement; never read by the research "
                "action")


class MarketFigure(Frozen):
    """One market figure as of a date — or None and why it is not held. `basis` says how it was
    measured (its window and dates), or what is missing; never a guessed number."""

    value: float | None
    basis: str
    #: a short structured suffix shown beside the value (revisions: "21↑ 2↓"), never parsed
    detail: str = ""
    #: when not held, why — the cause alone, for a caller that cites it (never parsed out of
    #: `basis`)
    why: str = ""


class ExposureMarket(Frozen):
    """Where one exposure's price stands, as of the context's date: price position (against its
    200-day average and its 52-week high), its return against the benchmark, its P/E against its
    own history, and consensus revisions. An index or basket with no traded ticker is named, not
    priced."""

    name: str
    ticker: str | None
    kind: Literal["listed", "fund", "index", "basket"]
    last_close: float | None
    last_bar: date | None
    vs_200d: MarketFigure
    from_52w_high: MarketFigure
    rel_3m: MarketFigure
    rel_12m: MarketFigure
    pe: MarketFigure
    pe_percentile: MarketFigure
    revisions: MarketFigure
    #: what the reader must check before trusting the row (a one-day move the size of a split)
    warnings: tuple[str, ...] = ()


class MarketContext(Frozen):
    """"Is it priced?" for ONE thesis version, point in time as of `as_of`: a bar or a filing after
    it is never read. DISPLAY ONLY (operator, 2026-10-16) — stored apart from the thesis, like an
    enrichment set; no research-action rule reads it (the isolation test pins the boundary).
    Append-only; a later pass is a new context."""

    context_id: str
    thesis_id: str
    thesis_version: int
    run_id: str
    as_of: date
    created_at: datetime
    benchmark: str
    rows: tuple[ExposureMarket, ...]
    #: where the figures come from, and the price window the plan serves
    source: str
    #: the companies the thesis IMPLIES (the latest enrichment set's verified listings) — an
    #: EXTERNAL HYPOTHESIS, not named by the source: priced apart, never counted
    hypotheses: tuple[ExposureMarket, ...] = ()
    label: Literal["MARKET CONTEXT — evidence for your judgement; never read by the research "
                   "action"] = ("MARKET CONTEXT — evidence for your judgement; never read by the "
                                "research action")


class ReviewResolution(Frozen):
    """A REVIEWER's disposition of ONE card-review finding (resolve.py): "dismissed" — read and
    accepted as not changing the line's use — or "reopened". Append-only, every row kept; a
    finding's state is its HEAD — the row no later row supersedes (`report.resolution_state`),
    never the latest clock across two machines. It binds to the finding as it
    stands (`finding_key`: the version whose review made it, its words, and the line's words and
    cited evidence now), so a changed line or a new review's finding is OPEN again.
    A dismissal closes the finding as an open item and NOTHING else: the line keeps the label the
    finding capped (at most SOURCE OPINION), a withheld line is never dismissible, and no
    research-action rule reads this record."""

    resolution_id: str
    run_id: str
    thesis_id: str
    #: the version whose card carried the finding when it was resolved
    version: int
    sentence_id: str
    finding_key: str
    finding_code: str
    #: the version whose card review made the finding
    finding_version: int
    #: the stored finding's own words, whole
    finding_detail: str
    #: the line, and the evidence it cites, as they read when it was resolved
    line_text: str
    claim_ids: tuple[str, ...]
    action: Literal["dismissed", "reopened"]
    reviewer: Annotated[str, Field(min_length=1)]
    reason: Annotated[str, Field(min_length=1)]
    created_at: datetime
    #: the resolution(s) of this finding the reviewer saw as its state when deciding — the rows
    #: this one replaces. A reopening made on another machine after it pulled a dismissal
    #: supersedes it, whatever the two clocks say (review of #768, 2026-10-21)
    supersedes: tuple[str, ...] = ()


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
    #: a SHARE-PRICE / index performance line the source states — market context, never earnings
    #: evidence for or against the thesis (J.P. Morgan acceptance, 2026-10-12: the Magnificent 7
    #: lagging the index was filed as counter-evidence to EARNINGS broadening)
    price_context: tuple[CardSentence, ...] = ()


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
    published_at: PublishedAt
    published_status: FieldStatus
    url: str
    article_class: ArticleClass
    retrieval_state: RetrievalState
    upstream_origins: tuple[str, ...]
    claim_ids: tuple[str, ...]
    contribution: ChangeClass
    #: each version's own date when they differ ("version 2 (report PDF): 2026-09-10 — the
    #: document text (page 1-2)"); empty when every version states the article's date
    version_dates: tuple[str, ...] = ()


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


class WatchReason(Frozen):
    """One RESEARCH NOW condition a WATCH thesis does not meet, as a VALUE: what it is (`code`),
    whether it is MISSING DATA (the record could not establish it — an unverified listing, part of
    the text, no dated window found) or a SUBSTANTIVE HOLD (the evidence itself falls short — a
    conditional premise, no catalyst, contested), and its words. So WATCH says WHY (2026-10-16:
    three J.P. Morgan theses all read "Watch", which said nothing about what each waited for)."""

    code: str
    kind: Literal["missing_data", "held"]
    text: str


class ResearchPriority(Frozen):
    research_action: ResearchAction
    evidence_direction: EvidenceDirection
    investment_readiness: InvestmentReadiness
    factors: tuple[PriorityFactor, ...]
    rules_fired: tuple[str, ...]
    previous_action: ResearchAction | None
    change_reason: str
    valuation_status: str
    #: a WATCH's unmet conditions, as values (empty for any other action, and for a version
    #: stored before 2026-10-16)
    watch_reasons: tuple[WatchReason, ...] = ()


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
    #: the PRODUCT that set this thesis apart from another on the same key (engine.py); "" for
    #: every thesis that never needed it — their ids are unchanged
    key_product: str = ""
    #: the run that RETIRED this thesis (`reanalyse`): the articles it was built from were
    #: analysed again under the current taxonomy, and the theses that analysis creates replace it.
    #: It keeps its versions, evidence and history, stays ARCHIVED, and is never matched,
    #: updated or reactivated again. "" for every other thesis.
    retired: str = ""

    @property
    def identity(self) -> str:
        return identity_key(self.key_node, self.key_mechanism, self.key_direction.value,
                            self.key_geography, self.key_segment, self.key_review,
                            self.key_product, self.retired)


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
    #: the spend guard's record: limits, every paid call's bound and actual cost, refusals
    spend: dict[str, Any] = Field(default_factory=dict)
    #: a `state pull` REPLAY: the original runs whose documents this run analysed again from
    #: their private copies (its own calls come from the cache — the spend is theirs)
    replay_of: tuple[str, ...] = ()
    #: set on a run a `state pull` carried into a rebuilt registry for its identity and its
    #: paid-call record only — its evidence was replayed (see the replay naming it) or discarded
    #: by a forced pull; never reported as this week's research
    ledger_only: str = ""


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


class PropositionFate(Frozen):
    """Where one proposition (a hypothesis a model pass proposed) of the source landed."""
    hypothesis_id: str
    title: str
    fate: str  # card | merged | dropped
    thesis_id: str | None = None
    detail: str = ""


class EvidenceGroup(Frozen):
    """Verified material evidence of one page that no thesis carries."""
    page: int | None
    claim_ids: tuple[str, ...]
    status: str  # unexplained | excluded | related
    reason: str = ""
    #: each claim's figure as the source wrote it (its statement when it has none) — one per id
    figures: tuple[str, ...] = ()


class SourceRiskFlag(Frozen):
    """A risk the SOURCE states in its own words (a verbatim sentence of a readable argument
    paragraph) — the source's OPINION, never a measured fact — and what accounts for it."""
    block_id: str
    page: int | None
    sentence: str
    #: the proposed risk / counter-claim already carrying it (content-word overlap), or ""
    represented_by: str = ""
    #: when omitted: the theses whose evidence (or pass-1b account) is in the same paragraph —
    #: the ONLY cards it is put on (07, labelled SOURCE OPINION); never every card
    thesis_ids: tuple[str, ...] = ()
    thesis_titles: tuple[str, ...] = ()
    #: the completeness pass judged its paragraph immaterial: that reason (listed, not alerted)
    excluded: str = ""
    #: cut by a page / column break — alerted, never put on a card
    fragment: bool = False


def page_prefix(page: int | None, sep: str = ": ") -> str:
    """"page N" + sep for a document with pages; nothing for a web article, which has none (the
    pilot's cards and review queue printed "page None", 2026-10-12)."""
    return f"page {page}{sep}" if page is not None else ""


class MechanismCoverage(Frozen):
    """coverage.py — every proposition and every verified material fact of the source accounted
    for: on a card, merged (stated), excluded with a reason, or an ALERT for review."""
    propositions: tuple[PropositionFate, ...] = ()
    uncarried: tuple[EvidenceGroup, ...] = ()
    risks: tuple[str, ...] = ()  # each proposed market risk: on which card(s), or dropped why
    unrecorded_names: tuple[str, ...] = ()  # "<name> (<how the sentence names it>, <block>)"
    #: every risk the SOURCE states in an argument paragraph, and what carries it (coverage.py)
    source_risks: tuple[SourceRiskFlag, ...] = ()
    #: earlier versions' theses this version re-verified and re-assessed (engine._reverify)
    reverified: tuple[str, ...] = ()

    @property
    def alerts(self) -> tuple[str, ...]:
        out = [f"proposition dropped: “{p.title}” — {p.detail}" for p in self.propositions
               if p.fate == "dropped"]
        out += [f"propositions merged: “{p.title}” — {p.detail}"
                for p in self.propositions if p.fate == "merged" and "DISTINCT" in p.detail]
        out += [f"sibling thesis: “{p.title}” — {p.detail}"
                for p in self.propositions if p.fate == "card" and p.detail.startswith("SIBLING")]
        for r in self.source_risks:
            if r.represented_by or r.excluded:
                continue
            where = (f"now in 07 of “{'”, “'.join(r.thesis_titles)}” as the source's opinion — "
                     f"its paragraph holds that evidence; review" if r.thesis_titles
                     else "on NO card — a sentence cut by a page break" if r.fragment
                     else "on NO card — no thesis's evidence is in its paragraph")
            out.append(f"{page_prefix(r.page)}a risk the source states that no model pass listed — "
                       f"“{r.sentence}” ({where})")  # whole: a cut quote misreads
        # a mechanism is argued with more than one fact; a lone uncarried figure is listed, not
        # alerted (face validity, 2026-10-12: Citi's p37 gas argument = 4 facts)
        # the SOURCE's evidence is named (every figure, as written) and kept apart from any
        # assessment: no thesis here carries it, so nothing has assessed it
        out += [f"{page_prefix(g.page)}{len(g.claim_ids)} verified material facts no thesis "
                f"carries — "
                f"a mechanism no card holds?"
                + (f" Source evidence: {'; '.join(g.figures)} — verified, UNASSESSED: no thesis "
                   f"or research action in this registry rests on it" if g.figures else "")
                for g in self.uncarried
                if g.status == "unexplained" and len(g.claim_ids) >= UNCARRIED_ALERT_MIN]
        return tuple(out)


#: unexplained verified material facts on one page from which coverage ALERTS (fewer are listed)
UNCARRIED_ALERT_MIN = 2


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
    #: mechanism coverage after the theses were applied (coverage.py); None before 2026-10-12
    coverage: MechanismCoverage | None = None

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


# --- source health (Priority 1A) ----------------------------------------------------------------

class HealthStatus(StrEnum):
    """A publisher channel's OPERATIONAL health — exactly one per check. Never inferred from an
    entry page answering 200: discovery, a real article's extraction and its metadata are tested."""

    HEALTHY = "HEALTHY"  # discovery and permitted full-text extraction work as expected
    DEGRADED = "DEGRADED"  # partly works: previews, missing dates, partial extraction, parsing
    BLOCKED = "BLOCKED"  # access denied, or cannot safely proceed under access / robots policy
    ERROR = "ERROR"  # temporary technical failure, timeout, unexpected response, malfunction
    UNKNOWN = "UNKNOWN"  # not yet checked, or too little evidence


class Freshness(StrEnum):
    """CONTENT freshness, tracked apart from health: a quiet week is not an unhealthy source."""

    FRESH = "FRESH"  # the newest dated article falls inside the check window
    QUIET = "QUIET"  # discovery works; nothing dated inside the window
    UNKNOWN = "UNKNOWN"  # no dated article to judge by


class HealthTest(Frozen):
    #: access | discovery | extraction | dates_authors | completeness | freshness |
    #: parser_integrity
    name: str
    result: Literal["PASS", "WARN", "FAIL", "SKIP"]
    detail: str


class ManualAction(Frozen):
    """What the operator must do while automatic retrieval is BLOCKED or DEGRADED."""

    kind: Literal["UPLOAD_REQUIRED", "MANUAL_REVIEW"]
    issue: str
    #: affected articles as discovered — "url — title as listed"; a title is never invented. At
    #: most health.AFFECTED_SHOWN are listed, the rest counted in a closing line
    affected: tuple[str, ...] = ()
    #: how many articles are affected in all (0: a check stored before this field)
    affected_total: int = 0
    action: str


class SourceHealthCheck(Frozen):
    """One immutable health observation of one channel (append-only `source_health` table)."""

    check_id: str
    source_id: str
    publisher: str
    checked_at: datetime
    trigger: str  # manual | scan
    run_id: str | None = None
    status: HealthStatus
    reason: str
    next_action: str
    expect_blocked: bool = False
    tests: tuple[HealthTest, ...] = ()
    freshness: Freshness = Freshness.UNKNOWN
    newest_article_date: date | None = None
    window_from: date | None = None
    window_to: date | None = None
    #: discovery: unique article URLs found, how many carry a listing date / title, in window
    discovered: int = 0
    dated: int = 0
    titled: int = 0
    in_window: int = 0
    new_since_last_check: int | None = None
    discovered_urls: tuple[str, ...] = ()  # capped; see `discovered_urls_truncated`
    discovered_urls_truncated: bool = False
    #: the first article read of those sampled to test extraction (never fabricated)
    sample_url: str | None = None
    sample_title: str | None = None
    sample_published: date | None = None
    sample_authors: tuple[str, ...] = ()
    sample_words: int | None = None
    sample_retrieval: str | None = None
    sample_notes: tuple[str, ...] = ()
    #: every sampled article, one line each: words, retrieval, date, byline — or why not read
    samples: tuple[str, ...] = ()
    #: words read per sampled page — a LATER check compares the same page with itself
    sample_words_by_url: tuple[tuple[str, int], ...] = ()
    #: the latest SCAN that covered this channel: its articles by retrieval outcome
    last_scan_run_id: str | None = None
    last_scan_full: int = 0
    last_scan_partial: int = 0
    last_scan_undated: int = 0
    last_scan_unreadable: int = 0
    #: carried forward from earlier checks when this one did not succeed at them
    last_successful_discovery: datetime | None = None
    last_successful_extraction: datetime | None = None
    last_verified_publication_date: date | None = None
    consecutive_failed_checks: int = 0
    status_since: datetime | None = None
    manual_action: ManualAction | None = None
    #: what changed since the previous check of this channel (first check: "first check")
    changes: tuple[str, ...] = ()
    #: NEW_FAILURE | PERSISTENT_FAILURE | RECOVERED | KNOWN_RESTRICTION | "" (nothing new)
    alert: str = ""
    notified: str = ""  # what the notification hook did with the alert, if one was raised
    requests: int = 0  # HTTP requests this check made (a bounded check — never a crawl)

    @property
    def manual_upload_recommended(self) -> bool:
        return self.manual_action is not None and self.manual_action.kind == "UPLOAD_REQUIRED"


# --- manual documents (hybrid ingestion) --------------------------------------------------------

class QuarantinedText(Frozen):
    """Undecodable glyph output left out of the analysis, one PDF page at a time: never sent to
    the model, never counted as a figure or an argument — and never claimed as read."""

    page: int
    lines: int  # text lines left out
    cells: int  # table cells left out
    chars: int  # characters left out
    sha256: str  # of the text left out (the lines and cells, in order) — what was excluded
    size: float = 0.0  # the type size most of it was set in (a metric, not its content)
    #: what the READABLE document says the page is (documents.classify_unread):
    #: back_matter | possibly_material | unclassified — never read from the unreadable text
    kind: str = "unclassified"
    basis: str = ""

class DocumentRecord(Mutable):
    """One manually supplied FILE (identified by its bytes), what the operator stated about it,
    and what it became: INGESTED (a new article) · UPGRADED (a fuller version of an article
    already held) · DUPLICATE (the same file, or the same text in another format — no new
    contribution) · REVIEW (an ambiguous match: a human decides) · HELD (third-party LLM
    processing not authorised under its licence) · REJECTED (unreadable)."""

    doc_id: str  # "D-" + the first 16 hex of the file's sha256
    sha256: str
    filename: str  # the name it arrived with — never used as metadata
    fmt: str
    size: int
    received_at: datetime  # wall clock, UTC — never a publication date
    source_id: str
    publisher: str
    declared: dict[str, str] = Field(default_factory=dict)  # the operator's statements
    status: str
    article_id: str | None = None
    version_id: str | None = None
    match_basis: str = ""  # why it was matched (or not) to an article already held
    #: the operator's own identity statement as a VALUE — "same_as" / "duplicate_of" / "new" —
    #: and the article it names (U33: a replay read it back out of `match_basis`, a display
    #: sentence; a record from before 2026-10-16 has none, and `ingest.operator_decision` reads
    #: its sentence)
    decision: Literal["same_as", "duplicate_of", "new"] | None = None
    decision_article: str | None = None
    title: str | None = None
    published: date | None = None
    published_source: str | None = None
    pages: int | None = None
    tables: int = 0
    issues: tuple[str, ...] = ()  # what could not be read — scanned pages, charts, tables
    stored_path: str | None = None  # the private copy (git-ignored data dir), relative
    run_id: str | None = None
    history: list[str] = Field(default_factory=list)  # status changes, each dated
    #: pages whose text layer held undecodable glyph output — what was left out of the analysis
    quarantined: tuple[QuarantinedText, ...] = ()
