"""Scoring harness — the BUY−AVOID spread and supporting metrics over the decision ledger."""

from mosaic.scoring.harness import score_ledger
from mosaic.scoring.metrics import (
    ScoreReport,
    VerdictScore,
    aggregate,
    ols_beta_alpha,
    total_return,
)

__all__ = [
    "ScoreReport",
    "VerdictScore",
    "aggregate",
    "ols_beta_alpha",
    "score_ledger",
    "total_return",
]
