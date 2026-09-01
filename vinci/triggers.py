"""Evaluate a MEASURED re-underwrite trigger against a committed dossier.

(ruling 3, 2026-08-31) The operator ruled that the machine may EVALUATE a deterministic,
pre-registered criterion and HIGHLIGHT one that has fired, while the disposition — exit, trim,
hold, re-underwrite — stays the human's. This module is that evaluation and nothing else: it
returns a state and its reason, and it takes no action.

IT NARROWS `monitor.py`'s STATED RULE, IT DOES NOT ABOLISH IT. That module says "the
freshness/trigger panel FLAGS; it never adjudicates a trigger as fired". The narrowing is exactly
one clause wide: a criterion carrying a metric, a comparator and a threshold is arithmetic, and
arithmetic can be checked. A criterion whose firing turns on a causal clause is not, and no
MeasuredTrigger is written for it — it stays a sentence a human reads.

THE THREE STATES ARE THE POINT. `FIRED` and `NOT_FIRED` are both answers; `UNKNOWN` is the refusal
to answer, and it must never be reachable by accident. A criterion the machine cannot read has to
say so, because "I could not measure this" and "this has not fired" recommend opposite actions and
look identical when a check returns a bare False.
"""
from __future__ import annotations

import math
import operator
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

from vinci.scenarios import MeasuredTrigger

FIRED = "FIRED"
NOT_FIRED = "NOT_FIRED"
UNKNOWN = "UNKNOWN"

#: Returned by `resolve_metric` when the PATH itself does not resolve. Distinct from ``None``,
#: which is a metric that IS recorded and whose value is null — the two have different causes and
#: the reason text has to say which one it met.
MISSING: Final = object()

_OPS: dict[str, Callable[[float, float], bool]] = {
    "<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge,
}


def _same_unit(a: str, b: str) -> bool:
    """Units match if they are the same token ignoring case and surrounding space.

    Deliberately NOT an alias table: equating ``$M`` with ``$mm`` is a judgment about the
    analyst's intent, and a wrong equivalence here silently restores the comparison this refusal
    exists to stop. Unmatched spellings refuse, and the operator restates the threshold.
    """
    return a.strip().casefold() == b.strip().casefold()


@dataclass(frozen=True)
class Observation:
    """One prior reading of a criterion, as recorded on a committed monitor day.

    ``source`` is the metric's own ``source_ref``, carried WHOLE and treated as an opaque identity
    token — never parsed. It already names the period ("CIQ Net Debt $325M [FQ3/CQ2 May-30-2026] ÷
    …"), and reaching into that string for the quarter would be the display-string-as-data class
    this module exists to refuse. Used only for EQUALITY: two readings sharing a source_ref are
    the same observation looked at twice.
    """

    source: str | None
    #: `None` = THIS READING WAS UNKNOWN — the comparison was never made, because the metric could
    #: not be read that day. It is NOT `False`. `MeasuredTriggerRow.satisfied` is `bool | None` for
    #: exactly this reason and the history must carry the third state through, or the module built
    #: to keep FIRED / NOT_FIRED / UNKNOWN apart flattens them back to two on the one path where a
    #: kill criterion is actually counted.
    satisfied: bool | None


@dataclass(frozen=True)
class TriggerState:
    """The evaluation, its reason, and what was read to reach it.

    `reason` is populated on EVERY state, not only on UNKNOWN: a human reading FIRED needs the
    number that fired it as much as a human reading UNKNOWN needs the cause.
    """

    state: str
    reason: str
    #: Did the COMPARISON hold on this reading — a different fact from whether the criterion FIRED.
    #: On a sustain criterion they diverge: the comparison can hold while the streak is still short,
    #: which is NOT_FIRED. Recording only the state would make that reading look like one where the
    #: comparison failed, and the next day's streak would count from the wrong place.
    satisfied: bool | None = None
    observed: float | None = None
    unit: str | None = None
    source: str | None = None

    @property
    def fired(self) -> bool:
        """True only on FIRED. UNKNOWN is NOT a quiet no — call sites must branch on `state`."""
        return self.state == FIRED


def resolve_metric(mechanical: dict[str, Any], path: str) -> tuple[Any, str | None]:
    """Walk a dotted path into the mechanical layer. Returns ``(node, source_ref)``.

    Returns the NODE, not a float: whether it carries a usable number is the evaluator's judgment
    to make and to explain, and a resolver that returned None for both "absent" and "present but
    not a number" would collapse the distinction this module exists to keep.

    An UNRESOLVED path returns the ``MISSING`` sentinel, never ``None`` — a metric recorded as a
    JSON ``null`` IS in the dossier, and reporting it as "the path does not resolve" sends the
    operator hunting a typo that is not there.
    """
    node: Any = mechanical
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return MISSING, None
        node = node[part]
    src = node.get("source_ref") if isinstance(node, dict) else None
    return node, (src if isinstance(src, str) else None)


def _streak(current_source: str | None, history: list[Observation]) -> int | None:
    """How many DISTINCT consecutive readings have satisfied the criterion, current one included.

    THE COUNT IS IN READINGS, NOT IN MONITOR DAYS, and that distinction is the whole reason this
    function exists. "Two consecutive quarters" is stated in the ANALYST's cadence; the monitor can
    run twice in an afternoon, and counting those as two would satisfy a two-quarter criterion in a
    single day — firing a kill on one observation the analyst deliberately wrote to need two.
    Distinct readings are separated by their ``source_ref``, which already carries the period.

    Returns None when the readings cannot be told apart — a metric with no ``source_ref`` gives no
    way to distinguish a fresh period from the same number seen again, and guessing would rebuild
    the defect above. The caller turns that into UNKNOWN.

    ...AND EQUALLY WHEN A READING IS UNKNOWN. `satisfied is None` means that day's comparison was
    never made, not that it failed. Treating it as a failure silently RESTARTS the clock on a kill
    criterion the analyst wrote to need N consecutive periods: the count begins again, the reader
    is told "1 of 2", and nothing says the missing period was unreadable rather than benign. This
    function already refuses to guess when it cannot tell two readings apart; it cannot honestly
    count through one it could not read either.
    """
    if current_source is None:
        return None
    seen: list[str] = [current_source]
    for obs in history:                      # most recent first
        if obs.satisfied is None:
            return None                      # unreadable: the run cannot be counted, only refused
        if not obs.satisfied:
            break                            # the streak is broken; older readings cannot extend it
        if obs.source is None:
            return None
        if obs.source == seen[-1]:
            continue                         # the same reading again, not another period
        seen.append(obs.source)
    return len(seen)


def evaluate(trig: MeasuredTrigger, mechanical: dict[str, Any],
             *, history: list[Observation] | None = None) -> TriggerState:
    """Evaluate one measured trigger against a dossier's mechanical layer.

    EVERY FAILURE PATH RETURNS `UNKNOWN` WITH ITS CAUSE. There is deliberately no path that
    returns NOT_FIRED because something could not be read: an unreadable criterion on a monitor
    page must look different from a quiet one, or the panel reassures where it should alarm.
    """
    node, source = resolve_metric(mechanical, trig.metric)
    if node is MISSING:
        return TriggerState(UNKNOWN, f"metric {trig.metric!r} is not in this dossier — the path "
                                     f"does not resolve, so nothing was compared")
    value = node.get("value") if isinstance(node, dict) else node
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return TriggerState(
            UNKNOWN,
            f"metric {trig.metric!r} resolved to {type(value).__name__} "
            f"({str(value)[:60]!r}), not a number — a threshold cannot be compared against it. "
            f"If this is a display string, the number it renders belongs in its own field",
            source=source)
    if not math.isfinite(value):
        # NaN loses EVERY comparison, so a non-finite reading would sail through the arithmetic
        # below and come back NOT_FIRED — the one outcome this module promises is unreachable
        # from an unreadable value. inf is refused with it: it is a placeholder, not a reading.
        return TriggerState(
            UNKNOWN,
            f"metric {trig.metric!r} resolved to {float(value)!r}, which is not a finite reading — "
            f"comparing it would return a bare False that is indistinguishable from 'has not "
            f"fired'", source=source)
    status = node.get("status") if isinstance(node, dict) else None
    if status not in (None, "present"):
        return TriggerState(UNKNOWN, f"metric {trig.metric!r} is recorded as {status!r}, so its "
                                     f"value is not a reading to compare", source=source)
    node_unit = node.get("unit") if isinstance(node, dict) else None
    if isinstance(node_unit, str) and node_unit.strip() and not _same_unit(node_unit, trig.unit):
        # THE UNIT IS CARRIED SO THIS REFUSAL CAN EXIST. A threshold typed in $bn against a value
        # recorded in $M is the scale defect this repo has recorded twice, and it is worse here
        # than elsewhere: the comparison SUCCEEDS, and `shown` would label both sides with the
        # analyst's unit, so the wrong answer reads as a confident one. Only a stated, disagreeing
        # unit refuses — a node that states none is compared as before.
        return TriggerState(
            UNKNOWN,
            f"metric {trig.metric!r} is recorded in {node_unit!r} but the threshold is stated in "
            f"{trig.unit!r} — refusing to compare across units rather than rescaling a number the "
            f"analyst did not write", source=source)
    ok = _OPS[trig.comparator](float(value), trig.threshold)
    shown = (f"{float(value):,.10g} {trig.unit} {trig.comparator} "
             f"{trig.threshold:,.10g} {trig.unit}")
    if not ok:
        return TriggerState(NOT_FIRED, f"{shown} is false", False, float(value), trig.unit, source)
    if trig.sustain > 1:
        # THE SUSTAIN COUNT IS PART OF THE CRITERION, NOT A REFINEMENT. "two consecutive quarters"
        # is a different test from "once", and treating one reading as satisfying it would fire
        # early on exactly the criteria an analyst wrote the count to protect.
        if history is None:
            return TriggerState(
                UNKNOWN,
                f"{shown} holds on this reading, but the criterion requires {trig.sustain} "
                f"consecutive readings and no history was supplied — firing on one would be a "
                f"weaker test than the analyst wrote", True, float(value), trig.unit, source)
        run = _streak(source, history)
        if run is None:
            # TWO CAUSES, NAMED APART. Both refuse to count, and a reader who cannot tell which
            # one they are looking at cannot act on either.
            if source is not None and any(o.satisfied is None for o in history):
                return TriggerState(
                    UNKNOWN,
                    f"{shown} holds now, but an earlier reading of this criterion was itself "
                    f"UNKNOWN — the comparison was never made that period, so a "
                    f"{trig.sustain}-reading run cannot be counted through it. Treating the gap "
                    f"as a failure would restart the count and read as though the criterion had "
                    f"been tested and not held", True, float(value), trig.unit, source)
            # No source_ref: a repeat of the same reading is indistinguishable from a new period,
            # and counting monitor RUNS instead would satisfy a two-quarter test in an afternoon.
            return TriggerState(
                UNKNOWN,
                f"{shown} holds, but this metric carries no source_ref, so a fresh reading cannot "
                f"be told from the same one seen again — a {trig.sustain}-reading criterion cannot "
                f"be counted without that", True, float(value), trig.unit, source)
        if run < trig.sustain:
            # A REAL ANSWER, NOT A REFUSAL. With a history in hand the criterion HAS been evaluated
            # and has not fired; the streak is stated so the reader can see how close it is.
            return TriggerState(
                NOT_FIRED,
                f"{shown} holds on {run} of the {trig.sustain} consecutive readings the criterion "
                f"requires", True, float(value), trig.unit, source)
        return TriggerState(
            FIRED, f"{shown} holds on {run} consecutive readings ({trig.sustain} required)",
            True, float(value), trig.unit, source)
    return TriggerState(FIRED, f"{shown} holds", True, float(value), trig.unit, source)
