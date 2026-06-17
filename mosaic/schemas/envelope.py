"""The data-record envelope — the single most load-bearing contract in the system.

Every *datum* (a pulled or derived value, never an identity key) carries:

    (value, as_of, source, coverage_status)  + a source-reliability tier

This is what makes **UNKNOWN → defer** mechanical rather than a matter of remembering: a gate
asks ``field.is_evaluable`` and, if not, returns UNKNOWN instead of imputing or silently
failing. A stale price, a missing filing, or an absent fundamental becomes an explicit
coverage state, never a confident zero.

Design rules enforced here (validated, not merely documented):
- ``PRESENT`` ⇒ ``value`` is not None and ``as_of`` is set.
- ``UNKNOWN`` ⇒ ``value`` is None (you cannot have an "unknown" that also carries a number).
- ``STALE``   ⇒ ``value`` may be present but is too old to trust as current.
"""

from __future__ import annotations

import enum
from datetime import date
from typing import Generic, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar("T")


class CoverageStatus(enum.StrEnum):
    """Whether a datum is usable. The spec's ``{present, unknown, stale}``."""

    PRESENT = "present"
    UNKNOWN = "unknown"
    STALE = "stale"


class SourceTier(enum.IntEnum):
    """Source reliability, highest first. EDGAR is authoritative; news is fenced.

    Ordered so a higher value == more authoritative (``EDGAR > IBKR > EOD > NEWS``), letting
    callers compare/prefer sources numerically when the same field has multiple origins.
    """

    EDGAR = 4
    IBKR = 3
    EOD = 2
    NEWS = 1
    DERIVED = 0  # computed from other enveloped fields (e.g. drawdown from price)


class DataField(BaseModel, Generic[T]):
    """A single enveloped datum.

    Construct via the classmethods (:meth:`present`, :meth:`unknown`, :meth:`stale`) rather than
    the raw initialiser — they encode the coverage contract so callers can't create an
    inconsistent envelope by accident.
    """

    value: T | None = None
    as_of: date | None = None
    source: str
    coverage_status: CoverageStatus
    source_tier: SourceTier
    # Optional human-readable note — e.g. *why* a field is UNKNOWN ("no XBRL EV/EBITDA tag").
    note: str | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _check_coverage_contract(self) -> DataField[T]:
        if self.coverage_status is CoverageStatus.PRESENT:
            if self.value is None:
                raise ValueError("PRESENT datum must carry a non-None value")
            if self.as_of is None:
                raise ValueError("PRESENT datum must carry an as_of date")
        elif self.coverage_status is CoverageStatus.UNKNOWN and self.value is not None:
            raise ValueError("UNKNOWN datum must not carry a value (would be a silent impute)")
        return self

    # --- ergonomic constructors ---------------------------------------------------------------
    @classmethod
    def present(
        cls,
        value: T,
        *,
        as_of: date,
        source: str,
        tier: SourceTier,
        note: str | None = None,
    ) -> DataField[T]:
        return cls(
            value=value,
            as_of=as_of,
            source=source,
            coverage_status=CoverageStatus.PRESENT,
            source_tier=tier,
            note=note,
        )

    @classmethod
    def unknown(
        cls, *, source: str, tier: SourceTier, note: str | None = None
    ) -> DataField[T]:
        return cls(
            value=None,
            as_of=None,
            source=source,
            coverage_status=CoverageStatus.UNKNOWN,
            source_tier=tier,
            note=note,
        )

    @classmethod
    def stale(
        cls,
        value: T,
        *,
        as_of: date,
        source: str,
        tier: SourceTier,
        note: str | None = None,
    ) -> DataField[T]:
        return cls(
            value=value,
            as_of=as_of,
            source=source,
            coverage_status=CoverageStatus.STALE,
            source_tier=tier,
            note=note,
        )

    # --- predicates the gates use -------------------------------------------------------------
    @property
    def is_evaluable(self) -> bool:
        """True iff a gate may rely on this datum (present and current)."""
        return self.coverage_status is CoverageStatus.PRESENT

    @property
    def is_known(self) -> bool:
        """True iff a value exists at all (present *or* stale)."""
        return self.value is not None
