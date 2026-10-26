"""Scoring harness — the BUY−AVOID spread and supporting metrics over the decision ledger."""

from vinci.scoring.harness import score_ledger
from vinci.scoring.metrics import (
    ScoreReport,
    VerdictScore,
    aggregate,
    ols_beta_alpha,
    price_return,
    total_return,
)

__all__ = [
    "ScoreReport",
    "VerdictScore",
    "aggregate",
    "ols_beta_alpha",
    "price_return",
    "score_ledger",
    "total_return",
]
