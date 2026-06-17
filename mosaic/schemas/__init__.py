"""Schemas-as-code — the contracts the whole system rides on.

- :mod:`mosaic.schemas.envelope`  — the per-datum ``(value, as_of, source, coverage)`` envelope.
- :mod:`mosaic.schemas.data_record` — contract A: the name data-record the gates consume.
- :mod:`mosaic.schemas.candidate`   — contract B: the screen→depth candidate-record.
- :mod:`mosaic.schemas.ledger`      — the decision-ledger entry (BUY / AVOID verdicts alike).
"""

from mosaic.schemas.candidate import CandidateRecord, GateResult, TriageBand
from mosaic.schemas.data_record import (
    DataRecord,
    EventType,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
    TypedEvent,
)
from mosaic.schemas.envelope import CoverageStatus, DataField, SourceTier
from mosaic.schemas.ledger import LedgerEntry, Verdict

__all__ = [
    "CandidateRecord",
    "CoverageStatus",
    "DataField",
    "DataRecord",
    "EventType",
    "Fundamentals",
    "GateResult",
    "Identity",
    "LedgerEntry",
    "PriceFeatures",
    "SourceTier",
    "StressSignals",
    "TriageBand",
    "TypedEvent",
    "Verdict",
]
