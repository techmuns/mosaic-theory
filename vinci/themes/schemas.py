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
