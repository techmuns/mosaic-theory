"""Annotations on a COMMITTED screen run — what a reader must know about a result that stands.

WHY (operator ruling 2026-10-26, STATE.md §5.0 row 32 item 16). A committed screen run is history:
its results are never rewritten. But when a later finding shows a result rested on bad data, the
reader of the queue that run produced must see it beside the name. The first case: the price
store took a 2:1 split at 2026-08-06 as a price fall, and SFBS (band A, rank 5) and IESC (band A,
rank 48) passed the 2026-10-16 screen on those bars. On the repaired bars neither is a candidate
(`docs/records/2026-10-26-split-restatement-and-total-return.md`).

WHERE. ``<snapshots>/screen_runs/<run id>.annotations.json``, beside the run it annotates. It is
hand-authored decision data, like ``data/followed.json``: an operator ruling plus the measured gate
values, each with how it was measured. Both queue surfaces read it — `ranked_queue.md`
(`vinci.rank.ranker.render_queue_markdown`) and the app's queue (`frontend/build.py`). The results
themselves are untouched.

FAIL LOUD. A file that does not parse, an unknown field, or two annotations for one ticker in the
same run raise. An annotation that silently fails to load is a warning the reader never sees.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

ANNOTATIONS_GLOB = "screen_runs/*.annotations.json"


class GateReading(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    value: float  # the gate's input as a fraction (−0.571 is −57.1%)
    passes: bool


class GateNote(BaseModel):
    """One gate's input, as the committed run read it and as the corrected data reads it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    gate: str  # the gate's id, e.g. "G1"
    label: str  # what it measures, for the reader
    threshold: float  # a name passes when its value is at or below this
    as_committed: GateReading
    repaired: GateReading

    @model_validator(mode="after")
    def _passes_agrees_with_the_threshold(self) -> GateNote:
        """A hand-typed PASS that its own value contradicts is refused, never shown."""
        for side, r in (("as_committed", self.as_committed), ("repaired", self.repaired)):
            if r.passes != (r.value <= self.threshold):
                raise ValueError(f"{self.gate} {side}: value {r.value} against threshold "
                                 f"{self.threshold} contradicts passes={r.passes}")
        return self


class ScreenAnnotation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ticker: str
    annotated_on: date
    ruling: str
    finding: str
    gates: list[GateNote]
    measured: str  # how the corrected values were produced: data, reference date, thresholds
    record: str  # the record that carries the full account


class RunAnnotations(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    reference_date: date
    annotations: list[ScreenAnnotation]


def load_all(snapshots_dir: Path) -> list[RunAnnotations]:
    """Every committed annotation file, in path order. Raises on any file that does not parse."""
    runs = []
    for path in sorted(snapshots_dir.glob(ANNOTATIONS_GLOB)):
        run = RunAnnotations.model_validate_json(path.read_text())
        seen: set[str] = set()
        for a in run.annotations:
            if a.ticker in seen:
                raise ValueError(f"{path.name}: two annotations for {a.ticker} in one run")
            seen.add(a.ticker)
        runs.append(run)
    return runs


def for_screen_date(snapshots_dir: Path, screen_date: date) -> dict[str, ScreenAnnotation]:
    """The annotations on the run screened on ``screen_date``, keyed by ticker."""
    out: dict[str, ScreenAnnotation] = {}
    for run in load_all(snapshots_dir):
        if run.reference_date != screen_date:
            continue
        for a in run.annotations:
            if a.ticker in out:
                raise ValueError(f"{a.ticker} is annotated twice for the {screen_date} screen")
            out[a.ticker] = a
    return out
