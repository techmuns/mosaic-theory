"""Schemas-as-code — the contracts the whole system rides on.

- :mod:`vinci.schemas.envelope`  — the per-datum ``(value, as_of, source, coverage)`` envelope.
- :mod:`vinci.schemas.data_record` — contract A: the name data-record the gates consume.
- :mod:`vinci.schemas.candidate`   — contract B: the screen→depth candidate-record.
- :mod:`vinci.schemas.ledger`      — the decision-ledger entry (BUY / AVOID verdicts alike).
"""

from vinci.schemas.candidate import CandidateRecord, GateResult, TriageBand
from vinci.schemas.data_record import (
    DataRecord,
    EventType,
    Fundamentals,
    Identity,
    PriceFeatures,
    StressSignals,
    TypedEvent,
)
from vinci.schemas.envelope import CoverageStatus, DataField, SourceTier
from vinci.schemas.ledger import LedgerEntry, Verdict

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
