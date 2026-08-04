"""(`scenario-create`) THE PROPOSER — anchors a new underwrite record from a committed dossier.

WHY THIS EXISTS. The underwrite is the critical path and had **no writer**: `scenario-refresh` and
`scenario-supersede` both require an existing record, `write_record()` had zero callers, and every
record in this repo's history was hand-authored. So the one place analyst judgment enters the fund
bypassed every guard the rest of the pipeline is built out of.

WHAT IT PROPOSES, AND WHAT IT REFUSES TO. Of the nine modelled numbers (three legs × revenue /
margin / multiple) **exactly three have a safe computed anchor, and all three are MEDIANS**:

    revenue base   consensus median at the anchor FY   (`consensus_levels`)
    margin  base   operating-margin median over 8 FY   (`anchor.margin`)
    multiple base  own-history trailing median         (`valuation.own_history`)

**The other six are REQUIRED INPUTS with no proposal**, for two different reasons:

* **UNANCHORED** — revenue bear, revenue bull, multiple bull. No statistic anchors them.
  `consensus_levels` carries low/high and they look usable; measured on SMPL they are not.
  Its FY2026 consensus range is 1,345.0–1,357.0 — 0.9% wide — against an analyst bear of 1,180.0.
  Defaulting to the consensus low would propose a bear **14% too generous**, in the leg that sets
  the risk denominator. The reason is structural: **consensus dispersion measures DISAGREEMENT AMONG
  FORECASTERS, not the downside scenario.** The two are not the same kind of quantity.

* **CONTAMINABLE** — margin bear, margin bull, multiple bear. These DO have a statistic
  (min / max / band-low) and it is the wrong kind. **The median absorbs one bad year; a min or a max
  IS the statistic a single observation defines.** SMPL's per-FY margin series carries a year whose
  raw value needed a +4.20pp adjustment to be called clean, and its FY2026 carries a $391.9M
  writedown: adding one such year moves the **min by −26.63pp** and the **median by −0.06pp**. A
  raw-min default would propose a NEGATIVE bear margin. Cleaning the series is judgment, and
  **judgment does not belong in a proposer** — so these are refused rather than guessed.

THE INVARIANT THAT HOLDS ON ALL NINE REGARDLESS OF HOW MANY DEFAULT, and the reason the count does
not decide the design: **every number either derives from an anchor carrying its `source_ref`, or
carries a stated basis — and both are refused if absent.** That is what makes the §D defect
structurally impossible: `14%` can no longer be written as a bare number, only as
*anchor 15.4481%, −1.45pp, reason stated*.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vinci.scenarios import RefPoint

#: A supplied leg value further than this from its anchor is a DEVIATION and must state why.
#: Relative, so it reads the same on a 1,330 revenue and a 12.5x multiple. Not tuned on outcomes —
#: it is a "did the analyst mean to move it" threshold, set at a quarter of a percent.
DEVIATION_TOL = 0.0025

#: The three axes a dossier can anchor, and the three legs. `(axis, leg)` pairs absent from
#: ANCHORED are required inputs — see the module docstring for which are unanchored and which are
#: contaminable, a distinction that is recorded but does NOT change the behaviour: both refuse.
ANCHORED: tuple[tuple[str, str], ...] = (("revenue", "base"), ("margin", "base"),
                                         ("multiple", "base"))
AXES: tuple[str, ...] = ("revenue", "margin", "multiple")
LEGS: tuple[str, ...] = ("bear", "base", "bull")

#: WHY each unproposed cell is unproposed. Carried into the refusal so the analyst is told the
#: reason, not merely that a value is missing — the difference between a guard and an obstacle.
UNPROPOSED_REASON: dict[tuple[str, str], str] = {
    ("revenue", "bear"): "no statistic anchors a downside revenue — consensus low measures "
                         "forecaster disagreement (SMPL: 0.9% wide), not a bear case",
    ("revenue", "bull"): "no statistic anchors an upside revenue — consensus high is the same "
                         "disagreement band read from the other end",
    ("margin", "bear"): "the per-FY minimum is defined by ONE observation and a single "
                        "writedown year moves it tens of points — cleaning the series is judgment",
    ("margin", "bull"): "the per-FY maximum is defined by ONE observation — same class as the "
                        "minimum, read from the other end",
    ("multiple", "bear"): "own-history band-low is defined by ONE close; dropping it moves the "
                          "low 3.6x further than it moves the median",
    ("multiple", "bull"): "no established anchor — p75 and the band high are both candidates and "
                          "neither reflects committed practice",
}


class ProposalRefusedError(RuntimeError):
    """A proposal or a write that cannot be made honestly. Never a partial record."""


@dataclass(frozen=True)
class Anchor:
    """One computed default, with everything needed to write it as a `RefPoint`.

    `vintage` is carried from the dossier, not stamped at write time (schema 1.4 requires it): a
    reference whose vintage is 'today' would be a lie about a figure struck from a FY2025 filing,
    and the whole reason SMPL's committed references cannot be re-checked is that they carry none.
    """

    axis: str
    leg: str
    value: float
    unit: str
    role: str
    label: str
    source: str
    vintage: str

    def as_refpoint(self) -> RefPoint:
        return RefPoint(label=self.label, value=self.value, unit=self.unit, source=self.source,
                        vintage=self.vintage, role=self.role, leg=self.leg)


def _get(d: Any, *path: str) -> Any:
    for k in path:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def propose_anchors(doc: dict[str, Any]) -> list[Anchor]:
    """The three safe defaults, read from a committed `dossier.json`.

    Returns only what the dossier actually supports — a name whose `consensus_levels` are absent
    gets two anchors, not a fabricated third. The caller reports what is missing; it never fills in.
    """
    out: list[Anchor] = []

    # revenue base — the consensus MEDIAN at the gap's own anchor FY, so the proposal and the
    # decomposition are on one horizon rather than two.
    fy = _get(doc, "mechanical", "ev_gap", "anchor_fy")
    rows = _get(doc, "mechanical", "consensus_context", "consensus_levels", "Revenue") or []
    row = next((r for r in rows if str(r.get("fy")) == str(fy)), None)
    if row and isinstance(row.get("median"), (int, float)):
        as_of = _get(doc, "mechanical", "ev_gap", "vintages", "consensus_as_of") or f"FY{fy}"
        out.append(Anchor("revenue", "base", float(row["median"]), "$M", "consensus",
                          f"consensus FY{fy} revenue median",
                          f"CIQ Estimates→consensus_levels Revenue FY{fy} "
                          f"(median of {row.get('estimates')} estimates)", str(as_of)))

    # margin base — `anchor.margin`, the ONE candidate that asserts its own basis in a field.
    mg = _get(doc, "anchor", "margin")
    if isinstance(mg, dict) and isinstance(mg.get("value"), (int, float)):
        out.append(Anchor("margin", "base", round(float(mg["value"]) * 100, 4), "%", "median",
                          f"operating-margin median over {mg.get('anchor_years')} FY",
                          str(mg.get("source")), f"{mg.get('anchor_years')} FY through the "
                          "latest reported fiscal year"))

    # multiple base — own-history trailing median. The band LOW is deliberately NOT proposed even
    # though it sits in the same object: see UNPROPOSED_REASON.
    oh = (_get(doc, "mechanical", "valuation", "own_history", "value") or [None])[0]
    if isinstance(oh, dict) and isinstance(oh.get("median"), (int, float)):
        out.append(Anchor("multiple", "base", round(float(oh["median"]), 4), "x", "median",
                          f"{oh.get('metric')} trailing median",
                          f"valuation.own_history {oh.get('metric')} "
                          f"({oh.get('n_closes')} closes, {oh.get('source_file')})",
                          str(oh.get("as_of"))))
    return out


def check_tier_agreement(doc: dict[str, Any], recipe_id: str) -> None:
    """REFUSE when the dossier's recipe hint and the record's recipe disagree.

    AORT is the live case on day one: its dossier reads `recipe_hint: R1_midcycle_margin_evebitda`,
    `applicable: True`, while its committed record is R2 (`tier: B`). The record governs — but a
    disagreement that nobody is told about is how a record acquires the wrong arithmetic silently,
    so the write stops and the human resolves it.
    """
    hint = _get(doc, "anchor", "recipe_hint")
    if not hint or hint in ("unknown", "R2_NEEDED"):
        if hint == "R2_NEEDED" and not recipe_id.startswith("R2"):
            raise ProposalRefusedError(
                f"{doc.get('ticker')}: the dossier hint is R2_NEEDED but the record claims "
                f"{recipe_id!r} — resolve the recipe before writing, never write across the "
                "disagreement")
        return
    if not recipe_id.startswith("R1") and hint.startswith("R1"):
        raise ProposalRefusedError(
            f"{doc.get('ticker')}: dossier hint {hint!r} disagrees with record recipe "
            f"{recipe_id!r}. The record governs, but the disagreement is resolved by a human — "
            "AORT already carries this shape, so it is a real state and not a hypothetical.")


def validate_legs(supplied: dict[str, dict[str, Any]], anchors: list[Anchor]) -> list[str]:
    """Every problem with a supplied leg set, as a list — never the first one only.

    A partial answer sends the analyst round the loop once per defect; the whole list is one pass.
    """
    by: dict[tuple[str, str], Anchor] = {(a.axis, a.leg): a for a in anchors}
    problems: list[str] = []

    for leg in LEGS:
        if leg not in supplied:
            problems.append(f"leg {leg!r} is missing — refusing to default it; a two-leg "
                            "underwrite has no reward:risk")
            continue
        s = supplied[leg]
        for axis in AXES:
            if s.get(axis) is None:
                why = UNPROPOSED_REASON.get((axis, leg))
                problems.append(
                    f"{leg}.{axis} is required and absent"
                    + (f" — not proposed because {why}" if why else ""))
                continue
            a = by.get((axis, leg))
            if a is None:
                # unanchored/contaminable: the number stands on a stated BASIS instead
                if not str(s.get(f"{axis}_basis") or "").strip():
                    problems.append(
                        f"{leg}.{axis} has no anchor, so it must state its basis "
                        f"({axis}_basis) — a number with neither an anchor nor a basis cannot "
                        "be reviewed")
                continue
            # anchored: equal to the anchor, or an explicit adjustment with its reason
            val = float(s[axis])
            drift = abs(val - a.value) / abs(a.value) if a.value else 0.0
            if drift > DEVIATION_TOL and not str(s.get(f"{axis}_adjustment") or "").strip():
                problems.append(
                    f"{leg}.{axis} = {val:g} deviates from its anchor {a.value:g}{a.unit} by "
                    f"{val - a.value:+g} and states no reason — set {axis}_adjustment. "
                    "(This is the §D defect: an averaged number whose derivation is unstated.)")
    return problems
