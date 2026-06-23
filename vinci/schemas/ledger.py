"""The decision-ledger entry — one recorded verdict per candidate the discriminator judges.

The discriminator itself is **manual** (the PM's A/B/C source-binding + CIQ process). This schema
is only the *record* of its verdict. Two disciplines are load-bearing for the validation:

1. **Log AVOIDs as well as BUYs** — the AVOID-terminal verdicts are half the validation set; the
   primary metric is the BUY−AVOID forward-return spread, which needs both legs.
2. **Freeze the entry price + as_of at decision time** — the scoring harness measures forward
   return from this frozen point, so it must be stamped once and never moved.
"""

from __future__ import annotations

import enum
from datetime import date, datetime

from pydantic import BaseModel, model_validator


class Verdict(enum.StrEnum):
    """The two verdicts Loop 1 records for Screen 2 (overshot de-rating)."""

    BUY = "BUY"  # overshoot — the de-rating is exaggerated-and-temporary; a reversal is nameable
    AVOID_TERMINAL = "AVOID_TERMINAL"  # the twin — real-and-permanent decline; no trade


class Confidence(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LedgerEntry(BaseModel, frozen=True):
    """A single recorded paper verdict. Append-only; never mutated after logging."""

    entry_id: str
    candidate_id: str  # links back to the CandidateRecord that was judged
    internal_id: str  # the security judged
    ticker: str
    # Sector (coarse GICS-like, from EDGAR SIC) — captured at log time so the spread can be read
    # PER-SECTOR (where the edge is real). Optional: None == a verdict logged before sector-tagging
    # existed (VRRM). Frozen with the verdict; never derived later.
    sector: str | None = None

    verdict: Verdict
    twin_call: str  # how the twin was ruled out / why it is the twin (the central judgement)

    # Frozen at decision time — the anchor for forward-return scoring.
    entry_price: float
    entry_price_as_of: date

    thesis: str  # short written thesis (BUY) or rationale (AVOID)
    kill_criteria: str  # what would falsify the thesis
    horizon_days: int  # thesis horizon in calendar days (the de-rating twin resolves in months)
    confidence: Confidence

    decided_at: datetime  # when the verdict was logged
    # The benchmark the BUY−AVOID/excess-return metrics will use (e.g. "IWM").
    benchmark: str = "IWM"

    @model_validator(mode="after")
    def _sane(self) -> LedgerEntry:
        if self.entry_price <= 0:
            raise ValueError("entry_price must be positive")
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        return self
