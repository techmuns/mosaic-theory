"""The cohort split's SHAPE, deliberately separated from its computation.

`vinci/cohort.py` derives these values and imports `vinci.sectors` to do it. `vinci.rank` may hold
the RESULT — it is display context the writer attaches after ranking — but must never be able to
compute or re-derive one, because the moment a sector-derived quantity can reach a weight, a
threshold or a sort, the queue becomes a dressed-up sector-momentum screen (the trap Edge-3 was
falsified into). Keeping the schema sector-free is what lets `RankedCandidate` carry the field
while `test_sector_never_enters_the_scorer_or_the_gate` still fences the derivation.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel


class CohortCall(enum.StrEnum):
    """What the split says. ``UNRESOLVED`` and ``NO_COHORT`` are real answers, not failures."""

    OWN = "own"                  # the cohort barely moved — the fall is the name's own
    COHORT = "cohort"            # most of the fall is the industry's
    UNRESOLVED = "unresolved"    # inside the near-tie band — no call is made
    NO_COHORT = "no-cohort"      # too few screened peers, or no screen log to read


class CohortRead(BaseModel, frozen=True):
    """One name's decomposition. Every field is display context; none reaches the score."""

    key: str                       # the SIC industry title the cohort was taken over
    call: CohortCall
    median: float | None = None    # the cohort's own median return vs the market benchmark
    residual: float | None = None  # the name's return MINUS that median — what is its own
    margin: float | None = None    # |median| - |residual|; the confidence the call rests on
    peers: int = 0                 # screened names in the cohort (pass AND fail)
    trajectory: list[float] = []   # the cohort median across recent runs, oldest -> newest
