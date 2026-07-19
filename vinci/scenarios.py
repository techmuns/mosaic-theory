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
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "1.0"
BAR = 2.0
VerdictStatus = Literal["pending_analyst", "confirmed", "overridden", "passed"]


class Fact(BaseModel):
    """One source-bound input. ``basis`` names WHAT the number is; ``source`` names WHERE it came
    from (form + accession + statement line) so the human can verify rather than trust."""

    value: float
    unit: str                      # "$M" | "shares" | "$/share" | "x" | "rate"
    basis: str                     # e.g. "consolidated FY2025" | "incl. operating + finance leases"
    source: str                    # e.g. "10-K acc 0000793074-26-000071 income statement"

    model_config = {"frozen": True}


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
    """The human's call. The machine NEVER sets anything but ``pending_analyst``."""

    status: VerdictStatus = "pending_analyst"
    recorded: str | None = None            # ISO date the human recorded it; None while pending


class ScenarioRecord(BaseModel):
    """``scenarios/<TICKER>.json`` — the full versioned underwrite record."""

    schema_version: str = SCHEMA_VERSION
    ticker: str
    recipe_id: str                         # e.g. "R1_midcycle_margin_evebitda"
    recipe_desc: str
    multiple_basis: str                    # "EV/EBITDA" — stamped so the unit cannot be misread
    underwrite_date: str                   # ISO date
    analyst: str
    spot: float
    spot_source: str
    facts: dict[str, Fact]                 # d_and_a, net_debt, diluted_shares (+ any recipe extras)
    scenarios: dict[str, ScenarioInput]    # bear | base | bull
    result: Result = Field(default_factory=Result)
    verdict: Verdict = Field(default_factory=Verdict)


RECIPE_R1 = "R1_midcycle_margin_evebitda"


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
    return rec.model_copy(update={"result": res})


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
