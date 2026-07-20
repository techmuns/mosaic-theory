"""Theme-detection records — Component A (Stage 1) of the theme edge.

The whole layer is **assemble-not-conclude**, like the dossier (STATE.md §2; CLAUDE.md): detection
**proposes** candidate clusters + the candidate shared-linkage the members carry, and **surfaces**
machine-assessed strength/lifecycle signals — the **analyst judges** whether the cluster is a real,
nameable THEME (criterion 1) and which themes to act on. So these records carry, by construction,
**NO theme score, NO ranking of theme-vs-theme, NO driver name, NO buy/avoid verdict** — a
structural guard (a schema with no such field cannot conclude), pinned by a test that walks the
schema (mirrors the dossier's no-verdict-field guard and the ranker's no-forward-returns AST guard).

`theme_admissibility.md`: admissibility is a binary SCREEN on four criteria (2/3/4 machine-checkable
PASS/FAIL gates; 1 is the human's nameable-driver call). §7.1 adds strength/lifecycle SIGNALS as
human-judged inputs — assembled-and-presented, **never an auto-rank** ("rank by momentum and
auto-bet the top" is the dead-signal failure, STATE.md §3).
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from vinci.schemas.envelope import DataField


class FactorBasis(StrEnum):
    """Which confounding factors the residualization stripped before clustering (criterion 3).

    ``MARKET_SECTOR`` is the R1 control (market + broad-sector); ``FULL`` is R2 — additionally the
    size + volatility/speculative factors, the proven-selective lever (STATE.md §4 PHASE-0.7/0.8)
    that dissolves speculative-beta glue while leaving real diffuse themes intact.
    """

    MARKET_SECTOR = "market+sector"  # R1
    FULL = "market+sector+size+vol"  # R2 (default; the vol-strip is load-bearing, not optional)


class WindowSpec(BaseModel, frozen=True):
    """The trailing detection window. Trailing-only by construction — detection never reads a return
    after ``reference_date`` (no lookahead; face-validity discipline, never tuned on forward
    returns)."""

    reference_date: date
    window_days: int
    start: date
    end: date
    trading_days: int  # actual aligned observations used


class ThemeMember(BaseModel, frozen=True):
    """One name in a candidate cluster, with its source-bound classification (criterion-1
    evidence)."""

    ticker: str
    name: str
    cik: str
    sic: str | None
    sector: str  # coarse GICS-like bucket (vinci.sectors.sector_for_sic)
    # official SEC SIC industry title (vinci.labels resolver, universe scale — no CIQ at breadth).
    # Default None → pre-field committed JSONL round-trips; consumers degrade loudly, never guess.
    industry: str | None = None
    sic_source_ref: str  # where the SIC came from, so the analyst verifies (CLAUDE.md source-bind)


class CandidateLinkage(BaseModel, frozen=True):
    """Criterion 1 SURFACE — what the members SHARE, PROPOSED for the analyst to name a driver from.

    The machine assembles the candidate shared-linkage (the members' sub-sectors / the
    cross-taxonomy span) source-bound to the linkage evidence; it **never ratifies a driver**. A
    blank answer to "name the driver" is the analyst's to give — a cluster the analyst cannot name
    is a momentum bucket (inadmissible), and that judgment is theirs, not the machine's.
    """

    distinct_sics: list[str]
    distinct_sectors: list[str]
    # >1 SIC and/or >1 sector — the cross-taxonomy signal SIC alone can't make
    crosses_taxonomy: bool
    shared_note: str  # a descriptive prompt for the analyst, NOT a named driver


class Trajectory(BaseModel, frozen=True):
    """A four-horizon (1/3/6/12mo) trailing trajectory the human reads as a SHAPE — accelerating off
    a trailing low reads as an inflection, decelerating from a high as rolling over. It carries
    DELIBERATELY no slope, composite, or rank field: collapsing the vector to one number re-destroys
    the shape and crosses the dead-signal line (§7.1 — the machine PRESENTS four values; the human
    judges the lifecycle stage). Each horizon is fail-loud (UNKNOWN on insufficient history)."""

    h1mo: DataField[float]
    h3mo: DataField[float]
    h6mo: DataField[float]
    h12mo: DataField[float]

    def ordered(self) -> list[tuple[str, DataField[float]]]:
        """The four horizons shortest→longest, so the sequence reads as a trajectory."""
        return [("1mo", self.h1mo), ("3mo", self.h3mo), ("6mo", self.h6mo), ("12mo", self.h12mo)]


class StrengthSignals(BaseModel, frozen=True):
    """§7.1 strength/lifecycle signals — INPUTS THE HUMAN JUDGES, never an auto-rank.

    Price-derivable, trailing-only, fail-loud (UNKNOWN on insufficient history — never a
    partial-window number). Momentum and relative-strength are presented as a 1/3/6/12mo TRAJECTORY
    (a shape the human reads), NOT a single number — and deliberately with **no composite, no score,
    no slope, no rank** (collapsing or ordering them is the dead-signal failure the boundary
    forbids, §2 amendment / §7.1). Breadth and crowding are recent/current-state measures with no
    natural multi-horizon trajectory, so they stay single values."""

    momentum: Trajectory  # median member trailing return at 1/3/6/12mo
    rel_strength_vs_market: Trajectory  # median(member − IWM) at 1/3/6/12mo
    breadth_expanding: DataField[float]  # share of members at a fresh window-high recently
    crowding_overextension: DataField[float]  # median distance above its trailing mean


class AdmissibilityReport(BaseModel, frozen=True):
    """The four-criteria SCREEN result for one cluster (criteria 2/3/4 machine-checkable; 1 is
    human).

    PASS/FAIL only — NOT weighted, scored, or traded off (themes are not ranked against each other,
    §2). Carries the transparent values so the analyst sees *why* it passed/failed (the ranker's
    legible-profile discipline)."""

    breadth_value: int
    breadth_pass: bool
    coherence_value: float  # mean intra-cluster residual correlation
    coherence_pass: bool
    persistence_pass: bool
    persistence_note: str
    fail_reasons: list[str] = Field(default_factory=list)

    @property
    def admissible(self) -> bool:
        return self.breadth_pass and self.coherence_pass and self.persistence_pass


class CandidateTheme(BaseModel, frozen=True):
    """A candidate theme the human judges. Assembled, source-bound — NEVER concluded.

    No ``score``/``rank``/``driver``/``verdict`` field exists, by design (the structural
    assemble-not-conclude guard). Members are listed; ordering of the OUTPUT list is by breadth for
    readability only and is explicitly NOT a quality ranking (§2: themes are not ranked)."""

    cluster_id: str
    members: list[ThemeMember]
    admissibility: AdmissibilityReport
    candidate_linkage: CandidateLinkage  # criterion-1 surface (machine proposes; human names)
    strength_signals: StrengthSignals  # §7.1 (assembled, never auto-ranked)
    residual_basis: FactorBasis
    window: WindowSpec
    # τ band the cluster core survived (not 1 τ)
    tau_stability: list[float] = Field(default_factory=list)


class DetectionStats(BaseModel, frozen=True):
    """Run-level health counts — fail-loud transparency (a wrong count signals a bug)."""

    universe_size: int
    names_with_coverage: int
    names_dropped_insufficient_history: int
    sic_resolved: int
    clusters_found: int
    admissible: int
    rejected_breadth: int
    rejected_coherence: int
    rejected_persistence: int


class ThemeDetectionResult(BaseModel, frozen=True):
    """The full Stage-1 detection output: admissible candidate themes + rejected clusters +
    stats."""

    reference_date: date
    residual_basis: FactorBasis
    window: WindowSpec
    candidate_themes: list[CandidateTheme]  # admissible only
    rejected: list[CandidateTheme]  # cleared clustering but failed a gate (kept for transparency)
    stats: DetectionStats


# ==================================================================================================
# Stage 2 — Components B (theme-type signals) + C (megacap confirmation). All PRESENTED,
# human-judges; no auto-classification, no type verdict, no autonomous trigger. READ-ONLY /
# confirmation-side: the >$10B leaders never enter detection or holding (A's $10B-capped universe
# is untouched).
# ==================================================================================================
class MegaLeader(BaseModel, frozen=True):
    """A >$10B name ASSEMBLED as a candidate theme leader — SIC-matched to the cluster AND
    residually co-moving with it (the same co-movement test that defined the theme). The analyst
    ratifies."""

    ticker: str
    name: str
    cik: str
    market_cap: float
    sic: str | None
    sector: str
    residual_corr_to_cluster: float  # co-movement evidence: median residual corr with the cluster
    source_ref: str  # cap basis + SIC provenance (so the analyst verifies)


class LeaderSet(BaseModel, frozen=True):
    """Candidate mega-cap leaders for a theme — the machine ASSEMBLES (breadth across the whole
    market a human can't recall), the analyst RATIFIES (add/remove) as part of criterion-1
    driver-naming. READ-ONLY / confirmation-side: these >$10B names never enter A's detection or the
    holding book."""

    rule: str  # the transparent mechanical designation rule
    leaders: list[MegaLeader]
    ratification_note: str  # 'analyst ratifies — add/remove as part of naming the driver'


class PricePattern(BaseModel, frozen=True):
    """B price-pattern: the designated leaders' vs the members' trajectory — leader-first (the
    emergence signature: leaders re-rate BEFORE the sub-$10B members) vs synchronous (cyclical) vs
    unstable (choppy). PRESENTED: the two trajectories + a mechanical read; the human judges the
    type."""

    leader_trajectory: Trajectory
    member_trajectory: Trajectory
    # leaders − members at each horizon (the lead-lag shape)
    lead_minus_member: list[tuple[str, float]]
    read: str  # a mechanical descriptor of the shape — NOT a type verdict


class HistoricalAnalog(BaseModel, frozen=True):
    """B historical-analog (§7.2): an LLM-ASSEMBLED reference class — past themes this pattern
    resembles and how they resolved — PROPOSED for the human to weigh, source-bound, never a
    verdict."""

    reference_themes: list[str]
    note: str
    model: str | None
    status: str  # 'assembled' | 'unavailable'


class TypeSignals(BaseModel, frozen=True):
    """Component B — theme-type SIGNALS the human judges AS PART OF criterion-1. No type verdict, no
    auto-classification. When the signals are mixed, ``ambiguous`` is the explicit DEFER state."""

    price_pattern: PricePattern
    vol_strip_survived: bool  # from A — real theme (survived the vol strip) vs spec-beta-adjacent
    vol_strip_note: str
    historical_analog: HistoricalAnalog
    ambiguous: bool  # the DEFER state: signals unclear → 'watch, do not fire' (do NOT force a type)
    defer_note: str


class ConfirmationCell(BaseModel, frozen=True):
    """One basis of the confirmation grid (absolute, or excess vs a benchmark) + its threshold
    reads."""

    basis: str  # 'absolute' | 'vs IWM' | 'vs SPY'
    # leaders' median return-from-baseline (excess of the benchmark for the vs-X bases)
    value: float
    # {'+20%': …, '+30%': …, '+50%': …} — does the signal clear that threshold
    clears: dict[str, bool]


class ConfirmationSignal(BaseModel, frozen=True):
    """Component C — megacap confirmation: a SIGNAL the human reads to decide whether to fire the
    enabler search; NOT an autonomous trigger (the dead-signal line — machine computes, human acts).
    Scoped to human-judged-emergence themes; the grid surfaces the threshold × benchmark sensitivity
    (Part-7 thresholds × Finding-2 dual benchmark) so no single fragile point drives the call."""

    baseline_date: date
    baseline_rationale: str
    n_leaders: int
    grid: list[ConfirmationCell]  # absolute / vs-IWM / vs-SPY, each at +20/+30/+50
    scope_note: str


class ThemeStage2(BaseModel, frozen=True):
    """Stage-2 output for one Component-A candidate theme: the assembled leaders, the theme-type
    signals (B), and the megacap confirmation signal (C) — all PRESENTED for the analyst to
    judge."""

    cluster_id: str
    member_tickers: list[str]
    candidate_linkage_note: str  # carried from A's criterion-1 surface
    leader_set: LeaderSet
    type_signals: TypeSignals
    confirmation: ConfirmationSignal | None  # None when no co-moving mega-cap leader exists


# --------------------------------------------------------------------------------------------------
# Stage 3 — the SEMANTIC-PRIMARY exposure detector (a NEW early-detection path, parallel to A's
# co-movement). Reads a name's recent DISCLOSURE STREAM and assembles its DISCLOSED exposure to one
# driver — source-bound, the Part-6 keyword-vs-semantic discriminator baked into ``concreteness``.
# Assemble-not-conclude: NO score / rank / theme-membership / buy verdict (the human judges).
# --------------------------------------------------------------------------------------------------
class ExposureConcreteness(StrEnum):
    """How CONCRETE one disclosed exposure fact is — the Part-6 discriminator (a mere mention of the
    driver ≠ binding exposure; a tenant-less 'we appointed an SVP of X' is intent, a quantified
    share-of-revenue attributable to the driver IS exposure). Graded, never a verdict."""

    BINDING_CONTRACT = "binding-contract"  # signed agreement, named counterparty + terms (MW/years)
    COMMITTED_CAPACITY = "committed-capacity"  # committed capex/MW/capacity, no binding revenue yet
    QUANTIFIED_REVENUE = "quantified-revenue"  # a disclosed $ or % of revenue attributable to it
    STATED_INTENT = "stated-intent"  # strategy / plan / 'exploring' — aspirational, no commitment
    NONE = "none"  # no driver exposure disclosed in the cited text


class DriverTie(StrEnum):
    """How SPECIFICALLY a fact ties to THE DRIVER (defined per-theme by a ``DriverSpec``) — the
    audit's driver-tie gate, INDEPENDENT of concreteness: a terms-binding contract with only an
    INDIRECT tie is NOT real exposure (e.g. a fuel-cell CEPA that binds but ties only generically to
    'data center'). What driver-specific / indirect / not-driver MEAN is supplied by the theme's
    ``DriverSpec.tie_taxonomy``, not hardcoded here."""

    DRIVER_SPECIFIC = "driver-specific"  # tied to a named element of the driver's structure
    INDIRECT = "indirect"  # weak/generic tie to the driver
    NOT_DRIVER = "not-driver"  # NOT this driver: an adjacent-but-distinct market


class ExposureFact(BaseModel, frozen=True):
    """One disclosed exposure fact, source-bound to the filing it was read from (CLAUDE.md)."""

    fact: str  # the disclosed business activity, paraphrased from the filing (no outside facts)
    # TYPE-APPROPRIATE strength (terms-binding / quantified+driver-attributable)
    concreteness: ExposureConcreteness
    # how specifically it ties to the driver (a separate gate; meaning per the theme's DriverSpec)
    driver_tie: DriverTie
    source_ref: str  # the filing accession/ref the fact was read from (must trace to the stream)


class ExposureBasis(StrEnum):
    """The STRONGEST disclosed basis across the stream — a factual read of disclosure concreteness,
    NOT a score/rank/membership verdict (assemble-not-conclude; pinned by the no-conclude guard).
    REAL (FP bar) = binding-contract or quantified-revenue; committed/aspirational/none = not.
    UNASSESSED_ERROR = a scan FAILED to assess this name (LLM/quota) — never a genuine none."""

    BINDING_CONTRACTS = "binding-contracts-with-terms"
    COMMITTED_CAPACITY = "committed-capacity-or-capex"
    QUANTIFIED_REVENUE = "quantified-revenue-share"
    ASPIRATIONAL = "aspirational-intent-only"
    NONE_DISCLOSED = "no-theme-exposure-disclosed"
    UNASSESSED_ERROR = "unassessed-error"  # a scan/LLM FAILURE, not a genuine none (2026-07-13)


class ExposureAssessment(BaseModel, frozen=True):
    """A name's DISCLOSED exposure to ONE driver, assembled from its recent filing stream and
    source-bound, for the analyst to judge. By construction carries NO score, NO rank, NO
    theme-membership, NO buy/avoid verdict — ``exposure_basis`` is a factual characterization of
    disclosure concreteness (the Part-6 discriminator), never a recommendation."""

    ticker: str
    cik: str
    driver: str  # the driver assessed against (e.g. the AI-datacenter / compute buildout)
    exposure_basis: ExposureBasis
    disclosed_facts: list[ExposureFact]
    primary_business: str  # what the filings say the business primarily IS today (source-grounded)
    key_unknowns: list[str]
    stream_refs: list[str]  # the filing refs read — the citable universe for this assessment
    flags: list[str] = Field(default_factory=list)  # guardrail flags (uncited / over-claim / etc.)
    model: str | None = None  # the LLM that produced it (logged; never feeds the ledger)


class DriverSpec(BaseModel, frozen=True):
    """A per-theme configuration that parameterizes the semantic exposure classifier for ANY driver.

    The classifier code path (the generic system prompt + tool + the two-axis grading) is
    driver-AGNOSTIC; a DriverSpec supplies everything driver-specific. AI-datacenter is ONE instance
    (``vinci.themes.drivers.AI_DATACENTER``), NOT baked into the classifier.

    OPEN FOR EXTENSION (do not block future themes): only the four fields below are required. A
    demand-shaped theme supplies whatever ``prefilter_terms`` fit it — they need NOT be value-chain
    terms. ``tie_taxonomy`` is FREE TEXT, so a theme defines driver-specific / indirect / not-driver
    however its structure needs — sequential value-chain layers, parallel capability categories, or
    a tailwind/headwind DIRECTION — none assumed here (the tie is not presumed positive).
    ``provenance_tags`` is optional (() when a theme has no sub-structure to tag by). The schema is
    deliberately ADDITIVE: a later theme adds a field it needs; it does not retrofit this one."""

    key: str  # stable id, e.g. "ai-datacenter"
    description: str  # what the driver IS + its exposure structure (the user-message driver text)
    tie_taxonomy: str  # what driver-specific / indirect / not-driver MEAN for THIS driver
    prefilter_terms: tuple[str, ...]  # pre-filter vocabulary (shape-agnostic; whatever fits)
    # optional keyword→tag map for by-tag volume aggregation (e.g. chain layers); () if none
    provenance_tags: tuple[tuple[str, tuple[str, ...]], ...] = ()
