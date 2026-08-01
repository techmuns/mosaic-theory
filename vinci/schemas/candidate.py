"""Contract B — the **candidate-record** (the screen→depth contract, per ``INGESTION_LAYER.md`` §B).

Emitted when a screen's gates admit a name. It carries the full data-record plus *why* the name
qualified and *what depth must resolve*. A verdict is **never** the output of a screen — the
candidate-record hands a structured setup to the manual discriminator, which owns the judgment.

The gate vocabulary is exactly ``PASS / FAIL / UNKNOWN`` (gates, never a composite score):
- **PASS** — the (evaluable) gate is satisfied.
- **FAIL** — the gate is violated; the name is excluded.
- **UNKNOWN** — the gate could not be evaluated (missing data) → carried forward as a depth task,
  it does not block admission.
"""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel

from vinci.schemas.data_record import DataRecord


class GateResult(enum.StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class RoutingPolicy(enum.StrEnum):
    """What the ROUTER does with a name no gate could assess. One setting, two values.

    The gates already record NOT_EVALUATED; this is the separate question of whether such a name
    enters the candidate set. On the 2026-07-29 run **282 of the 331 admitted had a G3 the screen
    could not evaluate**, and 3 more were forwarded past a G2 that returned NOT_EVALUATED — so the
    router was admitting on "not FAIL" while the gates said "could not judge".

    ``CARRY`` is the DEFAULT and is today's behaviour exactly, so a run reproduces byte-for-byte.
    Making it a named setting does not change what the screen does; it makes what the screen does
    STATEABLE, and a pool count meaningless without it is now recorded beside the count.
    """

    CARRY = "carry_not_evaluated"
    DROP = "drop_not_evaluated"


class TriageBand(enum.StrEnum):
    """Coarse triage band to size the shortlist to depth's throughput. Never a continuous score."""

    A = "A"  # strongest face-validity (e.g. deepest drawdown + multiple at floor)
    B = "B"
    C = "C"


class CandidateRecord(BaseModel, frozen=True):
    """A screen-admitted candidate handed to the manual depth discriminator."""

    candidate_id: str  # stable id for the (name, screen, screen_run) triple
    data_record: DataRecord
    screens_fired: list[str]  # e.g. ["screen_2"]
    gate_results: dict[str, GateResult]  # gate name -> result
    trigger_reason: str  # what fired the screen (event + price drop)
    unknown_gates_for_depth: list[str]  # gates depth must resolve (the UNKNOWNs)
    twin_to_rule_out: str  # the specific look-alike depth must kill, e.g. "terminal decline"
    triage_band: TriageBand
    screen_run_at: datetime  # when the screen produced this candidate (point-in-time)

    @property
    def is_admissible(self) -> bool:
        """A name is a candidate iff **no gate FAILs**. UNKNOWNs are carried, not blocking."""
        return GateResult.FAIL not in self.gate_results.values()

    @property
    def has_unresolved_depth_tasks(self) -> bool:
        return len(self.unknown_gates_for_depth) > 0


def derive_unknown_gates(gate_results: dict[str, GateResult]) -> list[str]:
    """Convenience: the UNKNOWN gates, in stable order, for ``unknown_gates_for_depth``."""
    return [g for g, r in gate_results.items() if r is GateResult.UNKNOWN]
