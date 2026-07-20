"""Versioned scenario records — ``scenarios/<TICKER>.json``.

The DURABLE record of one underwrite: the recipe used, the source-bound facts, the analyst's
bear/base/bull assumptions with reasons, the computed result, and the verdict status. It is the
reproducibility unit — re-running the recipe against the same record must reproduce the numbers.

WHY THE BASIS IS STAMPED. ``multiple_basis`` is written INTO every record. The first WERN run
uncovered a defect where an EV/EBITDA anchor band was applied to EBIT — a ~7.5x value error on a
capital-heavy carrier. A record whose unit is implicit can be misread; one that carries its own
basis cannot. ``recipe_id`` is stamped for the same reason: the arithmetic is pinned to a named
recipe, not to whatever the code happened to do that day.

The machine COMPUTES and RECORDS; it never ratifies. ``verdict.status`` starts
``pending_analyst`` and only a human moves it.

SCHEMA 1.1 — METHODOLOGY BINDS FORWARD. A record now carries HOW each assumption axis was
modeled: ``assumptions`` (per axis: a one-sentence method + source-bound reference values the
legs were chosen against) and ``recipe_formula`` (the arithmetic chain, stamped from the ONE
engine constant ``midcycle.R1_FORMULA`` — stated recipe can never drift from computed recipe).
1.0 records stay valid (the completeness gate binds only from 1.1 on — the reward/risk
convention's binds-forward pattern); an unknown axis is refused at ANY version, because a typo'd
axis silently dropping from the render is data loss.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ONE bar / ONE formula. The compute layer (vinci.dossier.midcycle) owns the ratified
# convention; the record layer re-exports — judge (clears_bar) and stamp (Result.bar) can no
# longer diverge, and the stamped recipe_formula is the SAME constant the engine states.
from vinci.dossier.midcycle import BAR, R1_FORMULA

SCHEMA_VERSION = "1.1"
# "watch" = the name is not underwritable at TODAY's price but the franchise is intact — a
# re-underwrite candidate, explicitly NOT an avoid. Distinct from "passed" (declined outright).
VerdictStatus = Literal["pending_analyst", "confirmed", "overridden", "passed", "watch"]


class Fact(BaseModel):
    """One source-bound input. ``basis`` names WHAT the number is; ``source`` names WHERE it came
    from (form + accession + statement line) so the human can verify rather than trust."""

    value: float
    unit: str                      # "$M" | "shares" | "$/share" | "x" | "rate"
    basis: str                     # e.g. "consolidated FY2025" | "incl. operating + finance leases"
    source: str                    # e.g. "10-K acc 0000793074-26-000071 income statement"

    model_config = {"frozen": True}


class RefPoint(BaseModel):
    """One source-bound REFERENCE value an assumption was modeled against (a history median, an
    anchor, a floor, a peak). ``label`` names what it is (the ``basis`` role); recorded in
    display-natural units (``4.06`` + ``"%"``, ``6.56`` + ``"x"``) — no consumer re-scales it."""

    label: str
    value: float
    unit: str                      # "%" | "$M" | "x" | ...
    source: str                    # the filing/tag/run that produced the value

    model_config = {"frozen": True}

    @field_validator("label", "unit", "source")
    @classmethod
    def _ref_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("a reference value with no label/unit/source cannot be verified — "
                             "refusing to record it")
        return v


class AssumptionDerivation(BaseModel):
    """HOW one assumption axis was modeled: a one-sentence analyst method + the reference frame.
    ``references`` MAY be empty — a pure-judgment method honestly stated beats a fabricated
    reference; a blank method is refused like a blank reason."""

    method: str
    references: list[RefPoint] = Field(default_factory=list)

    model_config = {"frozen": True}

    @field_validator("method")
    @classmethod
    def _method_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("method is required and must not be blank — an assumption whose "
                             "modeling cannot be stated cannot be reviewed")
        return v


class ScenarioInput(BaseModel):
    """One analyst-supplied leg. ``margin`` is a DECIMAL fraction (0.0625 = 6.25%)."""

    revenue: float                 # $M
    margin: float                  # decimal fraction of revenue (operating margin)
    multiple: float                # turns, on `multiple_basis`
    reason: str                    # WHY this deviates from the anchor — required, never blank

    model_config = {"frozen": True}

    @field_validator("reason")
    @classmethod
    def _reason_not_blank(cls, v: str) -> str:
        """The record is the durable artifact, so the refusal binds HERE — ``run_recipe`` builds
        its Scenario directly and would otherwise bypass ``build_scenario``'s no-reason guard.
        An assumption without a recorded reason is exactly what this fund refuses to compute."""
        if not v.strip():
            raise ValueError("reason is required and must not be blank — refusing to record a "
                             "scenario assumption with no stated reason")
        return v


class ScenarioOutcome(BaseModel):
    """One computed leg + its capital-intensity cross-checks."""

    value_per_share: float
    op_income: float               # EBIT ($M)
    ebitda: float                  # EBIT + D&A ($M) — what the multiple is applied to
    ev: float                      # $M
    equity: float                  # $M
    ev_ebit: float | None = None   # CROSS-CHECK
    norm_fcf: float | None = None  # CROSS-CHECK ($M)


class Result(BaseModel):
    """Filled by the run. ``pass_fail`` records the bar test honestly — a FAIL is a result."""

    per_scenario: dict[str, ScenarioOutcome] = Field(default_factory=dict)
    reward: float | None = None            # base − spot
    risk: float | None = None              # spot − bear
    ratio: float | None = None             # reward / risk (price ratio only)
    ratio_undefined: str | None = None     # set when the risk leg is degenerate
    bar: float = BAR
    pass_fail: Literal["PASS", "FAIL", "UNDEFINED"] | None = None


class Verdict(BaseModel):
    """The human's call. The machine NEVER sets anything but ``pending_analyst``.

    A verdict that says only "no" decays into a number nobody can re-check. ``rationale`` records
    WHY, and ``reunderwrite_triggers`` records what would have to change for the answer to change —
    so a WATCH is a standing instruction rather than a shrug."""

    status: VerdictStatus = "pending_analyst"
    recorded: str | None = None            # ISO date the human recorded it; None while pending
    rationale: str | None = None           # WHY — the human's reasoning, in their own words
    reunderwrite_triggers: list[str] = Field(default_factory=list)  # what would reopen the name
    # (avoid-leg) the asymmetry is inverted at today's price — track for short-alpha on PAPER.
    # Recording it does NOT create a position: no code path here approaches execution.
    avoid_priced: bool = False
    avoid_priced_note: str | None = None


class ScenarioRecord(BaseModel):
    """``scenarios/<TICKER>.json`` — the full versioned underwrite record."""

    schema_version: str = SCHEMA_VERSION
    ticker: str
    recipe_id: str                         # e.g. "R1_midcycle_margin_evebitda"
    recipe_desc: str
    # the arithmetic chain, stamped by run_recipe from midcycle.R1_FORMULA (the multiple_basis
    # precedent: the record states the recipe its numbers came from; a mismatch refuses loud)
    recipe_formula: list[str] = Field(default_factory=list)
    multiple_basis: str                    # "EV/EBITDA" — stamped so the unit cannot be misread
    underwrite_date: str                   # ISO date
    analyst: str
    spot: float
    spot_source: str
    facts: dict[str, Fact]                 # d_and_a, net_debt, diluted_shares (+ any recipe extras)
    scenarios: dict[str, ScenarioInput]    # bear | base | bull
    # per-AXIS methodology (revenue | margin | multiple for R1): how each modeled input was
    # derived, with its source-bound reference frame — the reviewable "why these numbers"
    assumptions: dict[str, AssumptionDerivation] = Field(default_factory=dict)
    result: Result = Field(default_factory=Result)
    verdict: Verdict = Field(default_factory=Verdict)

    @model_validator(mode="after")
    def _assumption_axes_guarded(self) -> ScenarioRecord:
        """Axes guard, both directions. Unknown axis for a KNOWN recipe → refuse at ANY version
        (a typo'd axis silently dropping from the render is data loss). Completeness (exactly
        the recipe's axes) binds FORWARD from schema 1.1 — 1.0 records predate the field and
        stay valid. An unknown recipe_id is unconstrained until it declares its axes."""
        axes = AXES_BY_RECIPE.get(self.recipe_id)
        if axes is None:
            return self
        unknown = set(self.assumptions) - set(axes)
        if unknown:
            raise ValueError(
                f"unknown assumption axis {sorted(unknown)} for recipe {self.recipe_id!r} — "
                f"the axes are {'/'.join(axes)}")
        if (self.schema_version != "1.0" and self.assumptions
                and set(self.assumptions) != set(axes)):
            raise ValueError(
                f"assumptions must cover exactly {'/'.join(axes)} for recipe "
                f"{self.recipe_id!r} (methodology binds forward from schema 1.1)")
        if self.schema_version != "1.0" and not self.assumptions:
            raise ValueError(
                f"a schema-{self.schema_version} record must state how each axis was modeled — "
                f"assumptions must cover {'/'.join(axes)} (methodology binds forward from 1.1)")
        return self


RECIPE_R1 = "R1_midcycle_margin_evebitda"

# The assumption AXES each known recipe models. The axes guard binds per-recipe: unknown axes are
# refused for a known recipe at any schema version; completeness (all axes present) binds from
# schema 1.1. A future recipe declares its axes here when it exists — never speculatively.
AXES_BY_RECIPE: dict[str, tuple[str, ...]] = {RECIPE_R1: ("revenue", "margin", "multiple")}


def run_recipe(rec: ScenarioRecord) -> ScenarioRecord:
    """Compute ``result{}`` for a record via the mid-cycle block, and return a NEW record with it.

    Recipe R1: revenue × margin → EBIT; + D&A → EBITDA; × multiple → EV; − net debt → equity ÷
    diluted shares. Reward/risk per the ratified convention (base−spot / spot−bear, bull excluded).
    Units: ``d_and_a``/``net_debt`` in $M, ``diluted_shares`` in MILLIONS → value/share in $.

    The machine records the bar test; it does NOT touch ``verdict``."""
    from vinci.dossier import midcycle as mc

    if rec.recipe_id != RECIPE_R1:
        raise ValueError(f"unknown recipe_id {rec.recipe_id!r} — this runner implements "
                         f"{RECIPE_R1}")
    if rec.multiple_basis != mc.MULTIPLE_BASIS:
        raise ValueError(f"record multiple_basis {rec.multiple_basis!r} != block basis "
                         f"{mc.MULTIPLE_BASIS!r} — refusing to compute on a mismatched unit")
    for key in ("d_and_a", "net_debt", "diluted_shares"):
        if key not in rec.facts:
            raise ValueError(f"recipe {RECIPE_R1} needs fact {key!r} — refusing to assume it")
    # a record CLAIMING a different arithmetic than the engine's is a lie — refuse, never
    # silently overwrite (the multiple_basis pattern); an unstamped record gets stamped below
    if rec.recipe_formula and rec.recipe_formula != list(R1_FORMULA):
        raise ValueError("record's recipe_formula does not match R1_FORMULA — refusing to "
                         "compute under a misstated recipe")
    dna = rec.facts["d_and_a"].value
    net_debt = rec.facts["net_debt"].value
    shares = rec.facts["diluted_shares"].value            # MILLIONS → $M/M = $/share
    if shares <= 0:
        raise ValueError("diluted_shares must be > 0")
    # Absent -> None (NOT 0.0): with both zero the FCF formula collapses to EBIT, and a "norm
    # FCF" that is silently EBIT is a fabricated number. Both required, or the cross-check is None.
    interest = rec.facts["cash_interest"].value if "cash_interest" in rec.facts else None
    tax_rate = rec.facts["cash_tax_rate"].value if "cash_tax_rate" in rec.facts else None

    per: dict[str, ScenarioOutcome] = {}
    for name, s in rec.scenarios.items():
        sc = mc.Scenario(name=name, revenue=s.revenue, margin=s.margin, multiple=s.multiple,
                         source="analyst", reason=s.reason, d_and_a=dna)
        v = mc.scenario_value(sc, net_debt=net_debt, shares=shares,
                              cash_interest=interest, cash_tax_rate=tax_rate)
        per[name] = ScenarioOutcome(value_per_share=v.vps, op_income=v.op_income, ebitda=v.ebitda,
                                    ev=v.ev, equity=v.equity, ev_ebit=v.ev_ebit,
                                    norm_fcf=v.norm_fcf)
    res = Result(per_scenario=per, bar=BAR)
    if "base" in per and "bear" in per:
        rr = mc.reward_risk(base_vps=per["base"].value_per_share,
                            bear_vps=per["bear"].value_per_share, spot=rec.spot)
        res = Result(per_scenario=per, reward=rr.reward, risk=rr.risk, ratio=rr.ratio,
                     ratio_undefined=rr.undefined, bar=BAR,
                     pass_fail=("UNDEFINED" if rr.ratio is None else
                                ("PASS" if rr.clears_bar else "FAIL")))
    # stamp result + the formula (machine assembly, like multiple_basis — never judgment)
    return rec.model_copy(update={"result": res, "recipe_formula": list(R1_FORMULA)})


def records_dir(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / "scenarios"


def write_record(rec: ScenarioRecord, *, root: Path | None = None) -> Path:
    """Persist to ``scenarios/<TICKER>.json`` — pretty + diff-able, so committed state reads."""
    d = records_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{rec.ticker.upper()}.json"
    path.write_text(rec.model_dump_json(indent=2) + "\n")
    return path


def read_record(ticker: str, *, root: Path | None = None) -> ScenarioRecord:
    path = records_dir(root) / f"{ticker.upper()}.json"
    return ScenarioRecord.model_validate_json(path.read_text())


def all_records(*, root: Path | None = None) -> dict[str, ScenarioRecord]:
    """Every committed record, keyed by ticker — what the frontend card renderer reads."""
    d = records_dir(root)
    if not d.is_dir():
        return {}
    out: dict[str, ScenarioRecord] = {}
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):        # _schema.json and friends
            continue
        rec = ScenarioRecord.model_validate_json(p.read_text())
        out[rec.ticker.upper()] = rec
    return out


def json_schema() -> dict[str, Any]:
    return ScenarioRecord.model_json_schema()


def write_json_schema(*, root: Path | None = None) -> Path:
    d = records_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "_schema.json"
    path.write_text(json.dumps(json_schema(), indent=2) + "\n")
    return path
