"""Ranker / triage layer — orders the screen's ~307 Edge-2 candidates into a priority queue.

Orders, never decides; a transparent weighted composite of the Tier-1 structural axes (drawdown
depth+shape, idiosyncrasy, multiple-vs-own-history, de-rating cause, tradeability), sharpened by a
minor Tier-2 volume overlay and coloured by a Tier-3 LLM cause-annotation. Tuned by face-validity,
NEVER by forward returns. Replaces the bare A/B/C band with a legible per-name structural profile.
"""

from mosaic.rank.cause import (
    classify_cause,
    load_cause_annotations,
    parse_cause_reply,
)
from mosaic.rank.profile import (
    AxisCoverage,
    AxisScore,
    CauseClass,
    LiquidityTier,
    RankedCandidate,
)
from mosaic.rank.ranker import (
    RankWeights,
    character_axis,
    depth_axis,
    idiosyncrasy_axis,
    liquidity_tier,
    load_candidates_from_snapshot,
    load_market_caps_from_snapshot,
    multiple_axis,
    rank_candidate,
    rank_candidates,
    render_profile_block,
    render_queue_markdown,
    volume_overlay,
)

__all__ = [
    "AxisCoverage",
    "AxisScore",
    "CauseClass",
    "LiquidityTier",
    "RankWeights",
    "RankedCandidate",
    "character_axis",
    "classify_cause",
    "depth_axis",
    "idiosyncrasy_axis",
    "liquidity_tier",
    "load_candidates_from_snapshot",
    "load_cause_annotations",
    "load_market_caps_from_snapshot",
    "multiple_axis",
    "parse_cause_reply",
    "rank_candidate",
    "rank_candidates",
    "render_profile_block",
    "render_queue_markdown",
    "volume_overlay",
]
