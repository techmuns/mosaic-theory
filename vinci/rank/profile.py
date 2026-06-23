"""The ranked-candidate **profile** — the legible per-name structural artifact that REPLACES the
bare A/B/C triage band as the headline.

The priority *score* and the *profile* are the **same artifact**: a transparent weighted composite
of the Tier-1 structural axes (the score) PLUS the human-readable per-axis breakdown that explains
*why* a name sits where it does in the queue. The legacy A/B/C drawdown-depth band collapses into
ONE axis of the profile (``depth_band``, kept as a quick tag), never the headline.

Nothing here predicts returns. The profile **describes the setup that already exists** so a human
can prioritise scarce deep-analysis time — a lagging/coincident act by design. The leading judgment
("will this overshoot revert?") is the human's downstream, never a number computed here.
"""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel


class CauseClass(enum.StrEnum):
    """Tier-3 LLM cause-classification — an ANNOTATION that *colours* the queue, never the sort key.

    Populated only by an explicit, separate LLM read of a name's de-rating text (8-K/news). It is
    ``UNCLASSIFIED`` by default: an unclassified name is **not** demoted (we never fabricate a
    terminal verdict from a model's confident, unfalsifiable opinion — same discipline as the
    assembler not rendering verdicts). It can DEMOTE a terminal-looking name; it is never the
    primary sort key.
    """

    MEAN_REVERT = "mean_revert"  # guidance miss / one-time charge / sentiment overreaction
    STRUCTURAL_BREAK = "structural_break"  # lost-largest-customer / regulatory kill-shot / fraud
    UNCLASSIFIED = "unclassified"  # no LLM read available — the honest default (no demotion)


class StructuralDisqualifier(BaseModel, frozen=True):
    """A TERMINAL/STRUCTURAL signal read deterministically from a name's 8-K filings (item codes +
    text) or its shares-outstanding series — **DEMOTE-ONLY**. It sinks a structurally-dead name so
    scarce deep-analysis time isn't wasted on it; it can NEVER raise a name's rank. Source-bound to
    the specific 8-K (accession + item + date) — or the EDGAR shares series — so the human verifies.
    Not a return predictor; the default for every name is *no flag* (None), never fabricated.
    """

    signal: str  # e.g. "non-reliance/restatement (4.02)", "going-concern", "dilution-spiral"
    source: str  # source-bound: "8-K <accession> item <code> filed <date>" or "EDGAR XBRL shares …"
    detail: str  # one grounded line


class LiquidityTier(enum.StrEnum):
    """A *display* band for tradeability (face-validity, NOT a filter). The GATE is separate."""

    AMPLE = "ample"  # deep enough to build a concentrated position without friction
    WORKABLE = "workable"
    THIN = "thin"  # buildable but slow — the deep-work payoff is capacity-limited


class AxisCoverage(enum.StrEnum):
    PRESENT = "present"
    UNKNOWN = "unknown"


class AxisScore(BaseModel, frozen=True):
    """One structural axis of a name's profile: its 0..1 sub-score, coverage, and a legible label.

    ``score is None`` **iff** ``coverage is UNKNOWN`` — a missing Tier-1 input is surfaced, never
    imputed (the screen's UNKNOWN→defer discipline, carried into the ranker).
    """

    axis: str
    score: float | None  # 0..1 sub-score (None when the input is UNKNOWN)
    coverage: AxisCoverage
    label: str  # human-readable, e.g. "−73% from 52w high" or "sharp — 1 gap-down"
    raw: float | None = None  # the underlying datum, for audit / tie-breaking


class RankedCandidate(BaseModel, frozen=True):
    """A screen candidate placed in the priority queue, with the full structural profile attached.

    Self-describing for audit: the sub-scores (``axes``), their weighted ``contributions`` (which
    sum to ``quality``), the ``volume_overlay`` (Tier-2), and the tradeability gate together
    reconstruct ``priority_score`` with no hidden step — the queue is readable top-to-bottom.
    """

    candidate_id: str
    ticker: str
    name: str
    priority_score: float  # the composite sort key (0..1; after Tier-2 overlay + tradeability gate)
    rank: int  # 1-based position in the emitted queue (assigned after the sort)
    depth_band: str  # the legacy A/B/C drawdown-depth tag — ONE axis, kept as a quick tag
    axes: dict[str, AxisScore]  # depth, shape, idiosyncrasy, multiple, cause
    contributions: dict[str, float]  # weight·sub-score per axis (Σ == quality)
    quality: float  # Σ contributions — the Tier-1 composite, before overlay/gate
    volume_overlay: float  # Tier-2 ± adjustment added to quality
    liquidity_tier: LiquidityTier
    adv_usd: float
    market_cap: float | None  # size, joined from the universe snapshot (None if unresolved)
    volume_state: str  # Tier-2 read, e.g. "exhausted (0.68×)" / "heavy distribution (12.4×)"
    cause_class: CauseClass  # Tier-3 annotation (UNCLASSIFIED by default)
    structurally_disqualified: bool  # a deterministic 8-K structural signal fired → sunk
    structural_flag: StructuralDisqualifier | None  # the source-bound signal (None = no flag)
    unknown_axes: list[str]  # Tier-1 axes that were UNKNOWN — depth tasks (flagged, never imputed)
    tradeability_gated: bool  # below the deep-work ADV floor → de-prioritised + flagged
    profile_line: str  # the one-line legible summary
    screen_run_at: datetime
