"""Screen retention — the persistence layer for CALIBRATION DATA, not an audit trail.

WHAT THIS IS FOR. `candidate_records.jsonl` is rewritten on every run, so the only screen evidence
that has ever existed is the survivor set of the latest run. The 2026-07-27 benchmark bound was
possible only because those values happened to survive — luck, not method. More importantly,
**survivors-only retention can only ever confirm the screen**: a screen discarding names that later
outperform has NEGATIVE alpha and nothing in the current design would show it. The reject set is the
population that makes the gates falsifiable, which is why this exists.

TWO GRAINS, because "every name" and "one row per candidate" are not the same set — they differ by
~1,482 names, and the difference is the biggest filter in the funnel:

* :class:`CandidateRow` (≈318/run) — every gate, its inputs each with their OWN stamp, per-gate
  outcome. The screen's own decisions.
* :class:`UniverseRow` (≈1,800/run) — ticker, the stage that dropped it, the reason, and the one
  input that decided it. **A name filtered at the universe stage is also a DISCARDED name**, and
  `universe.py`'s falsely-stamped market cap (STATE S3) is exactly a universe-stage defect, so
  candidate-grain retention would leave the deepest queued item with no evidence trail at all.

THREE OUTCOMES, NOT TWO. :class:`Outcome` carries ``NOT_EVALUATED`` beside ``PASS``/``FAIL``, and it
is never written without a reason. A name whose window was start-truncated **could not be assessed**
and must never be indistinguishable from one that was assessed and rejected — item 22 applied to the
screen path. The screen's own :class:`~vinci.schemas.candidate.GateResult` spells this ``UNKNOWN``;
:func:`outcome_from_gate` is the one place that mapping happens, so the vocabularies cannot drift.

STAMPS, TWO KINDS, AND BOTH ARE LOAD-BEARING.
* **Inputs carry their OWN as-of**, never the run's. A gate input claiming the reference date while
  its data stopped days earlier is precisely what made the benchmark incident invisible for weeks.
* **Rows carry the CONFIGURATION that produced them** — thresholds, benchmark and lookback on the
  candidate grain; the band rule and its cap bounds on the universe grain. Without it, comparing two
  runs compares two different screens and nothing says so: if G2's ceiling moves off −15%, every
  earlier row silently means something else. The record must say what TEST was applied, not only
  what went into it.

APPEND-ONLY AND IMMUTABLE. :func:`append_rows` opens for append and never rewrites; a run gets its
own file, and :func:`next_run_id` gives a monotonic suffix so two runs on one reference date cannot
collide. The round-trip pin covers both halves — rows written are rows read back, **and appending a
run leaves every prior byte untouched**, which is the property calibration actually depends on.

READ-ONLY EVIDENCE (the guardrail that binds hardest here). Retention may FALSIFY a design; any
parameter chosen after looking at it must be validated FORWARD, on runs retention had not recorded
when the choice was made. Nothing in this module reads a forward return, and nothing may ever set a
threshold from these rows — a fitted gate is the replicable signal this fund is not.
"""

from __future__ import annotations

import enum
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter

from vinci.schemas.candidate import GateResult

#: Where a run's rows live. Under ``data/snapshots/`` because that path is committed (the rest of
#: ``data/`` is git-ignored) — retention is durable evidence or it is nothing.
RETENTION_SUBDIR = "screen_runs"
_RUN_ID = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{2})$")


class Outcome(enum.StrEnum):
    """PASS / FAIL / NOT_EVALUATED — the third is why this enum is not ``GateResult``.

    ``NOT_EVALUATED`` means *the assessment could not be made*, and it is written only with a
    reason. Collapsing it into ``FAIL`` is the defect this whole grain exists to prevent: a name
    with too little history looks identical to a name the screen judged and rejected, and the
    calibration population is silently poisoned with names that were never actually tested.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT_EVALUATED"


def outcome_from_gate(result: GateResult) -> Outcome:
    """The ONE mapping from the screen's vocabulary to retention's, so the two cannot drift.

    ``GateResult.UNKNOWN`` is not a third judgement — it is the gate saying it had nothing to judge
    with — so it lands on ``NOT_EVALUATED`` rather than ``FAIL``.
    """
    return {
        GateResult.PASS: Outcome.PASS,
        GateResult.FAIL: Outcome.FAIL,
        GateResult.UNKNOWN: Outcome.NOT_EVALUATED,
    }[result]


class StampedInput(BaseModel, frozen=True):
    """One gate input with ITS OWN as-of — never the run's.

    ``as_of`` is nullable because an absent input is a real state, but a PRESENT value with a null
    stamp is refused: an unstamped number is exactly the shape that let a stale benchmark pass for a
    current one. ``note`` carries the field's own caveat (a shortened window, a frontier gap) so the
    row explains itself without a join.
    """

    value: float | str | None
    as_of: date | None = None
    source: str
    note: str | None = None
    #: WHAT THE NUMBER COVERS, not only when it ends. `as_of` is the window's END — it cannot say
    #: that a "180-day" relative return actually spanned 296 days over 28 bars, which is exactly
    #: what OPI's row claimed. Structured, not parsed back out of `note`: two consumers of one
    #: string is the twin-drift class this repo keeps finding.
    span_days: int | None = None
    observations: int | None = None

    def model_post_init(self, _ctx: Any) -> None:
        if (self.span_days is None) != (self.observations is None):
            raise ValueError(
                f"{self.source!r}: a window is described by its SPAN and its BAR COUNT together — "
                "296 days is innocuous at 124 bars and a hole at 28, so one without the other "
                "cannot say which")
        if self.value is not None and self.as_of is None:
            raise ValueError(
                f"a present input must carry its own as-of ({self.source!r} has value "
                f"{self.value!r} and no stamp) — an unstamped input is how a stale benchmark "
                "passed for a current one")


class GateOutcome(BaseModel, frozen=True):
    """One gate's verdict on one name, with the gate's own sentence for it.

    ``reason`` is REQUIRED, including on PASS: a row that records only the outcome cannot later
    answer *why*, and the reason string is the gate's own — never re-derived here.
    """

    outcome: Outcome
    reason: str

    def model_post_init(self, _ctx: Any) -> None:
        if not self.reason.strip():
            raise ValueError("a gate outcome must carry the gate's own reason, including on PASS")


class ScreenConfig(BaseModel, frozen=True):
    """The screen's parameters at the moment the row was written — what TEST was applied."""

    thresholds: dict[str, float]
    benchmark: str
    lookback_days: int


class BandConfig(BaseModel, frozen=True):
    """The universe rule at the moment the row was written."""

    market_cap_min_usd: float
    market_cap_max_usd: float
    exchanges: tuple[str, ...]


class RunManifest(BaseModel, frozen=True):
    """The configuration a run was executed under — written ONCE, not copied onto 1,800 rows.

    Every row carries the ``run_id`` and a row filed under another run's id is refused, so the
    reference already exists; duplicating the config per row buys nothing and makes a config change
    look like 1,800 changes in a diff.

    What it must answer is unchanged: **what TEST was applied?** If G2's ceiling moves off −15%,
    every row of an earlier run means something else, and the manifest is what says so.
    """

    run_id: str
    reference_date: date
    screen: ScreenConfig
    band: BandConfig
    stages: tuple[str, ...] = ()   # the drop stages this run could emit, in funnel order

    def model_post_init(self, _ctx: Any) -> None:
        if not _RUN_ID.match(self.run_id):
            raise ValueError(f"run_id {self.run_id!r} is not <YYYY-MM-DD>-<NN>")


class _Row(BaseModel, frozen=True):
    ticker: str
    run_id: str
    reference_date: date
    outcome: Outcome
    not_evaluated_reason: str | None = None

    def model_post_init(self, _ctx: Any) -> None:
        if self.outcome is Outcome.NOT_EVALUATED and not (self.not_evaluated_reason or "").strip():
            raise ValueError(
                f"{self.ticker}: NOT_EVALUATED requires its reason — an unexplained "
                "not-evaluated is indistinguishable from a rejection, which is the whole "
                "distinction this grain exists to keep")
        if self.outcome is not Outcome.NOT_EVALUATED and self.not_evaluated_reason:
            raise ValueError(
                f"{self.ticker}: not_evaluated_reason is set on a {self.outcome} row — a reason "
                "for a state the row is not in will be read as if it were")
        if not _RUN_ID.match(self.run_id):
            raise ValueError(f"run_id {self.run_id!r} is not <YYYY-MM-DD>-<NN>")


def rollup(per_gate: Mapping[str, GateOutcome]) -> Outcome:
    """The row's overall outcome, DERIVED from its gates — never asserted alongside them.

    FAIL dominates: a name that failed any gate failed the screen, regardless of what a later gate
    said or whether it ran at all. Then NOT_EVALUATED, because a screen that could not assess a name
    has not passed it. All-PASS is the only way through.

    Only gates PRESENT in the map are considered — a short-circuiting screen legitimately never
    reaches G3, and an absent gate is not a silent PASS.
    """
    if not per_gate:
        raise ValueError("a candidate row with no gate outcomes records nothing — refusing")
    outcomes = {g.outcome for g in per_gate.values()}
    if Outcome.FAIL in outcomes:
        return Outcome.FAIL
    if Outcome.NOT_EVALUATED in outcomes:
        return Outcome.NOT_EVALUATED
    return Outcome.PASS


class CandidateRow(_Row, frozen=True):
    """The full grain: every gate, its inputs, its outcome, and the config that judged it."""

    grain: Literal["candidate"] = "candidate"
    gate_inputs: dict[str, StampedInput]
    per_gate: dict[str, GateOutcome]

    def model_post_init(self, _ctx: Any) -> None:
        """THE AGGREGATE MUST AGREE WITH ITS DETAIL (review finding).

        The first cut let ``outcome`` be set independently of ``per_gate``, so a row could read PASS
        while a gate it carries read FAIL — the record saying two things, in the one artifact whose
        purpose is to be re-read later. It matters more here than elsewhere: a calibration query
        GROUPS BY the aggregate and EXPLAINS with the detail, so a disagreement is not a cosmetic
        inconsistency, it is an analysis that is silently wrong.
        """
        super().model_post_init(_ctx)
        expected = rollup(self.per_gate)
        if self.outcome is not expected:
            failed = sorted(g for g, o in self.per_gate.items() if o.outcome is Outcome.FAIL)
            unrun = sorted(g for g, o in self.per_gate.items()
                           if o.outcome is Outcome.NOT_EVALUATED)
            raise ValueError(
                f"{self.ticker}: row outcome {self.outcome} contradicts its gates (expected "
                f"{expected}; failed={failed or 'none'}, not-evaluated={unrun or 'none'}). Build "
                "the outcome with `rollup(per_gate)` — never assert it beside the detail")


class UniverseRow(_Row, frozen=True):
    """The thin grain: what dropped it, why, and the single input that decided it.

    Deliberately NOT a candidate row with fields omitted — a name that never reached the screen has
    no gate outcomes, and modelling it as a candidate with empty gates would make "not run" and
    "ran and found nothing" the same shape.
    """

    grain: Literal["universe"] = "universe"
    stage: str
    reason: str
    deciding_input: StampedInput


Row = Annotated[CandidateRow | UniverseRow, Field(discriminator="grain")]
_ROW_ADAPTER: TypeAdapter[Row] = TypeAdapter(Row)


def retention_dir(snapshots_dir: Path) -> Path:
    return snapshots_dir / RETENTION_SUBDIR


def next_run_id(reference_date: date, snapshots_dir: Path) -> str:
    """``<reference_date>-<NN>``, one past the highest suffix already present for that date.

    MONOTONIC PER DATE, not a timestamp: two runs on one reference date are a real and ordinary
    thing (a re-run after a fixed input), and they must be distinguishable AND orderable. Scans the
    directory rather than tracking a counter, so a partially-copied checkout cannot silently reissue
    an id that already has rows under it.
    """
    d = retention_dir(snapshots_dir)
    used = [int(m.group(2)) for p in (d.glob(f"{reference_date.isoformat()}-*.jsonl") if d.is_dir()
                                      else []) if (m := _RUN_ID.match(p.stem))]
    return f"{reference_date.isoformat()}-{max(used, default=0) + 1:02d}"


def run_path(run_id: str, snapshots_dir: Path) -> Path:
    if not _RUN_ID.match(run_id):
        raise ValueError(f"run_id {run_id!r} is not <YYYY-MM-DD>-<NN>")
    return retention_dir(snapshots_dir) / f"{run_id}.jsonl"


def manifest_path(run_id: str, snapshots_dir: Path) -> Path:
    if not _RUN_ID.match(run_id):
        raise ValueError(f"run_id {run_id!r} is not <YYYY-MM-DD>-<NN>")
    return retention_dir(snapshots_dir) / f"{run_id}.manifest.json"


def write_manifest(manifest: RunManifest, *, snapshots_dir: Path) -> Path:
    """Write a run's manifest ONCE. Refuses to overwrite — a run's configuration is not editable.

    The rows are append-only and the manifest is write-once; together they mean a completed run is
    immutable end to end. Rewriting the manifest would silently re-label every row already filed
    under it, which is the one edit that could make a whole run mean something else.
    """
    path = manifest_path(manifest.run_id, snapshots_dir)
    if path.exists():
        raise ValueError(
            f"{path.name} already exists — a run's configuration is written once. Rewriting it "
            "would re-label every row already filed under this run id")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=1) + "\n", encoding="utf-8")
    return path


def read_manifest(run_id: str, snapshots_dir: Path) -> RunManifest | None:
    path = manifest_path(run_id, snapshots_dir)
    if not path.is_file():
        return None
    return RunManifest.model_validate_json(path.read_text(encoding="utf-8"))


def append_rows(rows: Iterable[Row], *, run_id: str, snapshots_dir: Path) -> int:
    """APPEND rows to a run's file. Never rewrites, never truncates. Returns the count written.

    Opens in ``"a"`` mode deliberately: there is no code path here that can shorten or modify an
    existing byte, which is the property the calibration set depends on — a retained row that a
    later run could edit is not evidence.
    """
    path = run_path(run_id, snapshots_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            if row.run_id != run_id:
                raise ValueError(
                    f"{row.ticker}: row.run_id {row.run_id!r} does not match the file it is being "
                    f"appended to ({run_id!r}) — a row filed under another run's id is evidence "
                    "attributed to the wrong screen")
            fh.write(row.model_dump_json() + "\n")
            n += 1
    return n


def read_rows(run_id: str, snapshots_dir: Path) -> list[Row]:
    """Every row of a run, in write order, validated back into its own grain.

    A malformed line RAISES rather than being skipped: a retention file that silently drops rows
    reports a smaller reject set than actually occurred, which biases calibration in the one
    direction that flatters the screen.
    """
    path = run_path(run_id, snapshots_dir)
    if not path.is_file():
        return []
    out: list[Row] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(_ROW_ADAPTER.validate_python(json.loads(line)))
        except Exception as exc:
            raise ValueError(f"{path.name}:{i} is not a valid retention row — {exc}") from exc
    return out


def list_runs(snapshots_dir: Path) -> Sequence[str]:
    """Every retained run id, oldest first — they sort lexicographically because the date leads."""
    d = retention_dir(snapshots_dir)
    return sorted(p.stem for p in d.glob("*.jsonl")) if d.is_dir() else []
