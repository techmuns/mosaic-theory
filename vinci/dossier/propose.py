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

from dataclasses import dataclass, field
from typing import Any

from vinci.dossier.anchor import (
    anchor_prices_ex_lease,
    ciq_ebitda_band,
    lease_basis_mismatch,
    r1_multiple_band,
)
from vinci.dossier.schemas import PrimarySource
from vinci.dossier.synthesis import guidance_vintage_mark, newest_guidance_date
from vinci.scenarios import BASIS_EV_NTM_EBIT, RECIPE_R4, RefPoint

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

#: An axis whose LEG FIELD is named differently. `earnings` reads `eps` for the same reason the
#: card's `AXIS_LEG_KEY` maps it: the axis names the assumption an analyst states, the field names
#: the number the recipe reads, and for a forward-P/E leg those differ. Without the mapping the
#: validator asks for a leg key that does not exist and refuses every R3 record — the
#: capability-that-cannot-fire shape this create path has already produced once.
#: `horizon` -> `years_to_terminal` joins it: R2's axes include a horizon, and nothing hit this
#: before because every caller passed the R1 trio regardless of recipe. The moment the real axes
#: were passed, three committed R2 records refused on "horizon is required and absent" while
#: carrying the number under its own name. Same table as the card's `AXIS_LEG_KEY`, and it should
#: stay that way — two spellings of one mapping is how the next one goes missing.
AXIS_LEG_FIELD: dict[str, str] = {"earnings": "eps", "horizon": "years_to_terminal"}
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

#: (R4) Why NTM EBIT at exit is never proposed, on any leg. KEPT OUT OF `UNPROPOSED_REASON`, which
#: is R1's six cells exactly (pinned): that table drives R1's base-axis fallback, and an R4 entry
#: there would read as R1 base cells becoming unproposable.
R4_EBIT_WHY = ("NTM EBIT at exit is the recipe's whole leg driver — a pre-filled number would be "
               "the machine writing the underwrite (the R3 EPS rule)")


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
    #: Which multiple this anchors, STRUCTURED — `EV/EBITDA`, `P/E`. Carried rather than re-read
    #: out of `stat_label` ("EV/EBITDA trailing median"): the label is a rendered string and a
    #: parse of it is the display-formatting-as-data defect this repo has already paid for twice.
    #: `None` on an axis where basis is meaningless (revenue, margin) — never a guess.
    basis: str | None = field(default=None, kw_only=True)
    #: DISPLAY units — what the `RefPoint` renders (`15.4481` + `"%"`), per REF_UNITS.
    value: float
    unit: str
    #: SCHEMA units — what `ScenarioInput` actually stores, and the ONLY value compared against a
    #: supplied leg. `margin` is a DECIMAL FRACTION there (0.14) while it displays as 14.0%, so a
    #: single field would compare 0.14 against 15.4481 and report a 99% deviation on a leg that
    #: matches its anchor exactly. Two units, two fields — the display form is never load-bearing.
    schema_value: float
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
        out.append(Anchor("revenue", "base", float(row["median"]), "$M",
                          float(row["median"]), "consensus",
                          f"consensus FY{fy} revenue median",
                          f"CIQ Estimates→consensus_levels Revenue FY{fy} "
                          f"(median of {row.get('estimates')} estimates)", str(as_of)))

    # margin base — `anchor.margin`, the ONE candidate that asserts its own basis in a field.
    mg = _get(doc, "anchor", "margin")
    if isinstance(mg, dict) and isinstance(mg.get("value"), (int, float)):
        out.append(Anchor("margin", "base", round(float(mg["value"]) * 100, 4), "%",
                          float(mg["value"]), "median",
                          f"operating-margin median over {mg.get('anchor_years')} FY",
                          str(mg.get("source")), f"{mg.get('anchor_years')} FY through the "
                          "latest reported fiscal year"))

    # multiple base — the trailing median of the history the ANCHOR prices on (2026-10-19): the
    # record takes its net debt from the anchor, so its multiple must come from the same side of
    # the lease line. Read off the anchor, not re-decided from the page's lease basis, which can
    # land before the anchor is re-derived (review of #750); when the two disagree, or the page
    # refuses R1, nothing is proposed. The band LOW is deliberately NOT proposed even though it
    # sits in the same object: see UNPROPOSED_REASON.
    mech = _get(doc, "mechanical") or {}
    sel = r1_multiple_band(mech)
    ex = anchor_prices_ex_lease(_get(doc, "anchor"))
    oh = (None if lease_basis_mismatch(doc) is not None or sel.refusal is not None
          else sel.band if ex else ciq_ebitda_band(mech))
    where = "valuation.lease_basis.ex_lease_band" if ex else "valuation.own_history"
    if isinstance(oh, dict) and isinstance(oh.get("median"), (int, float)):
        out.append(Anchor("multiple", "base", round(float(oh["median"]), 4), "x",
                          float(oh["median"]), "median",
                          f"{oh.get('metric')} trailing median",  # basis= below
                          f"{where} {oh.get('metric')} "
                          f"({oh.get('n_closes')} closes, {oh.get('source_file')})",
                          str(oh.get("as_of")), basis=str(oh.get("metric") or "") or None))
    return out


def check_tier_agreement(doc: dict[str, Any], recipe_id: str) -> None:
    """REFUSE when the dossier's recipe hint and the record's recipe disagree.

    AORT is the live case on day one: its dossier reads `recipe_hint: R1_midcycle_margin_evebitda`,
    `applicable: True`, while its committed record is R2 (`tier: B`). The record governs — but a
    disagreement that nobody is told about is how a record acquires the wrong arithmetic silently,
    so the write stops and the human resolves it.
    """
    # `applicable: False` IS a disagreement, and missing it left a second live case unguarded.
    # VITL carries `recipe_hint: R1_midcycle_margin_evebitda` with `applicable: False` — the
    # dossier saying this recipe does NOT apply to this name (its EBITDA dispersion is 263.7%, so
    # the margin ratio is suppressed and it routes two-ratio). Checking only the hint STRING would
    # wave an R1 record through on a name the dossier has already declined to underwrite that way.
    hint = _get(doc, "anchor", "recipe_hint")
    # EXCEPT ON AN R4 TAG. `applicable` is R1's bit — whether R1's arithmetic could anchor — and
    # R4's own eligibility (ruled 2026-10-08) includes "R1 cannot anchor". So on an R4-tagged page
    # `applicable=False` is the EXPECTED state, not a disagreement: UBER, one of the two names the
    # rule admits, carries it, and would be refused by its own eligibility condition. R3 keeps the
    # coupling (§5.0 row 10, #670) — its eligibility asks nothing of R1, so that is a separate call.
    if (_get(doc, "anchor", "applicable") is False and hint and hint != "R2_NEEDED"
            and hint != RECIPE_R4):
        raise ProposalRefusedError(
            f"{doc.get('ticker')}: the dossier carries recipe hint {hint!r} but marks it "
            "applicable=False — writing a record on a recipe the dossier says does not apply is "
            "the disagreement this guard exists for. Resolve it before writing.")
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
    # A NAMED FORWARD RECIPE ON THE PAGE THAT THE RECORD DOES NOT MATCH (2026-10-08, R4). The R1
    # check above was the whole guard while R3 was the only other recipe a page could name; once R4
    # existed, a page tagged R3 and a record claiming R4 — AMZN, the day R4 landed — passed with
    # nobody told. A forward recipe on the page is an operator's tag, so writing across it is the
    # same disagreement this guard exists for.
    if hint.startswith(("R3", "R4")) and hint != recipe_id:
        raise ProposalRefusedError(
            f"{doc.get('ticker')}: dossier hint {hint!r} disagrees with record recipe "
            f"{recipe_id!r} — re-tag the page or write the record on its recipe; never write "
            "across the disagreement")


def _anchors_on_basis(anchors: list[Anchor], basis: str | None) -> list[Anchor]:
    """`anchors`, minus any struck on a DIFFERENT multiple than the record uses.

    An own-history EV/EBITDA median cannot anchor a forward P/E: 24.5 against 17.37 reports a
    +41% deviation on a leg that is not the same kind of number. Dropping it does not skip the
    check — an unanchored leg must then state its `multiple_derivation`, which is the stricter
    outcome and the right one for a turn no committed statistic supports.

    CONSERVATIVE BY CONSTRUCTION: an anchor is dropped only when both bases are known AND
    neither names the other, so `EV/EBITDA (NTM)` still anchors an `EV/EBITDA` record and an
    unknown basis keeps every anchor it had. Uncertainty leaves the check ON.

    "NAMES THE OTHER" IS A WHOLE-NAME CONTAINMENT, NOT A SUBSTRING. `BASIS_EBIT = "EV/EBIT"` is a
    literal substring of `BASIS_EBITDA = "EV/EBITDA"` — both are live R2 bases — so a bare `in`
    read the two most confusable multiples in the repo as the same one, which is the exact
    category error this filter exists to catch, one letter finer. The shorter name must end at a
    boundary inside the longer: `EV/EBITDA (NTM)` and `NTM EV/EBITDA` still name `EV/EBITDA`,
    while `EV/EBITDA` does not name `EV/EBIT`.
    """
    if not basis:
        return anchors

    def _names(long: str, short: str) -> bool:
        i = long.find(short)
        if i < 0:
            return False
        before = long[i - 1] if i else ""
        after = long[i + len(short):i + len(short) + 1]
        return not (before.isalnum() or after.isalnum())

    def names_the_same_multiple(have: str) -> bool:
        x, y = have.strip().upper(), basis.strip().upper()
        return _names(x, y) or _names(y, x)

    return [a for a in anchors if not a.basis or names_the_same_multiple(a.basis)]


def validate_legs(supplied: dict[str, dict[str, Any]], anchors: list[Anchor],
                  *, axes: tuple[str, ...] | None = None,
                  basis: str | None = None) -> list[str]:
    """Every problem with a supplied leg set, as a list — never the first one only.

    A partial answer sends the analyst round the loop once per defect; the whole list is one pass.

    ``axes`` IS PER-RECIPE; `None` — an unmapped recipe — falls back to R1/R2's trio, which is
    exactly the behaviour before this parameter existed. The fallback is not a guess covering a
    broken recipe: `run_recipe` refuses an unknown `recipe_id` on its own terms, and this pass
    should not pre-empt that refusal with a misleading list of missing-axis complaints.

    An R3 record models earnings and multiple and reads NO revenue or margin, so validating it
    against the trio demands two numbers the arithmetic never touches and refuses a well-formed
    record — a create path that cannot create. The caller supplies
    ``scenarios.axes_for(recipe_id, multiple_basis)`` rather than this module deciding, so there is
    one definition of a recipe's axes and not a second one here to drift from it.
    """
    axes = axes or AXES
    by: dict[tuple[str, str], Anchor] = {(a.axis, a.leg): a
                                         for a in _anchors_on_basis(anchors, basis)}
    problems: list[str] = []

    for leg in LEGS:
        if leg not in supplied:
            problems.append(f"leg {leg!r} is missing — refusing to default it; a two-leg "
                            "underwrite has no reward:risk")
            continue
        s = supplied[leg]
        for axis in axes:
            field = AXIS_LEG_FIELD.get(axis, axis)
            if s.get(field) is None:
                why = UNPROPOSED_REASON.get((axis, leg))
                problems.append(
                    f"{leg}.{field} is required and absent"
                    + (f" — not proposed because {why}" if why else ""))
                continue
            a = by.get((axis, leg))
            if a is None:
                # unanchored/contaminable: the number stands on a stated BASIS instead
                # `{axis}_derivation`, NOT `{axis}_basis`: `ScenarioInput.margin_basis` already
                # exists and means WHICH EARNINGS LINE (EBIT|EBITDA), not where the number came
                # from. Reusing that name would let "EBIT" satisfy a provenance requirement it
                # does not answer — one name, two meanings, which is the defect class this repo
                # keeps paying for.
                if not str(s.get(f"{field}_derivation") or "").strip():
                    problems.append(
                        f"{leg}.{field} has no anchor, so it must state where it came from "
                        f"({field}_derivation) — a number with neither an anchor nor a stated "
                        "derivation cannot be reviewed")
                continue
            # anchored: equal to the anchor, or an explicit adjustment with its reason
            # COMPARED IN SCHEMA UNITS. `a.value`/`a.unit` are the display pair; comparing a
            # supplied 0.14 against a displayed 15.4481 would flag every matching margin leg.
            val = float(s[field])
            ref = a.schema_value
            drift = abs(val - ref) / abs(ref) if ref else (0.0 if val == ref else float("inf"))
            if drift > DEVIATION_TOL and not str(s.get(f"{field}_adjustment") or "").strip():
                problems.append(
                    f"{leg}.{field} = {val:g} deviates from its anchor {a.value:g}{a.unit} by "
                    f"{val - ref:+g} and states no reason — set {field}_adjustment. "
                    "(This is the §D defect: an averaged number whose derivation is unstated.)")
    return problems


def record_legs_for_validation(rec: Any,
                               *, axes: tuple[str, ...] | None = None
                               ) -> dict[str, dict[str, Any]]:
    """A committed `ScenarioRecord`'s legs in the shape `validate_legs` reads.

    WHY AN ADAPTER RATHER THAN A DIRECT CALL. `validate_legs` was written for the TEMPLATE, whose
    provenance lives in per-cell `{axis}_derivation` / `{axis}_adjustment` keys. A `ScenarioRecord`
    has no such fields and structurally cannot: its provenance is `assumptions[axis]` (a stated
    `method` plus `references`) and its per-leg deviation reason is `ScenarioInput.reason`, whose
    own docstring is *"WHY this deviates from the anchor — required, never blank"*. Feeding a record
    straight in refuses ALL SEVEN committed records on nine phantom "must state where it came from"
    problems — measured, not predicted. That is not a guard finding defects, it is a shape mismatch.

    THE MAPPING, and it is faithful in one direction and COARSER in the other:
      * `{axis}_derivation`  <- `assumptions[axis].method`   (per AXIS — the record's own unit)
      * `{axis}_adjustment`  <- `ScenarioInput.reason`       (per LEG  — the record's own unit)

    **The coarseness is real and is not hidden.** The template demands a reason per (axis, leg)
    CELL; a record states one reason per LEG, so a leg whose `reason` explains its revenue move but
    not its multiple move passes here and would not pass `scenario-create`. This closes the §D hole
    — a bare number with no stated derivation — without pretending to be cell-level parity.

    ``axes`` IS THE RECIPE'S, defaulting to R1/R2's trio — the FOURTH consumer of the module-level
    `AXES` and the last to be taught. Emitting `revenue_derivation` for a forward-P/E record maps
    provenance onto axes it does not have while leaving `eps` unmapped entirely, so the supersede
    guard would refuse every R3 record on axes its arithmetic never reads. The leg VALUES are
    emitted unconditionally because a record simply has whichever of them it has, and the validator
    only looks at the axes it was given.
    """
    out: dict[str, dict[str, Any]] = {}
    assumptions = getattr(rec, "assumptions", None) or {}
    for leg, s in (rec.scenarios or {}).items():
        d: dict[str, Any] = {"revenue": s.revenue, "margin": s.margin, "multiple": s.multiple,
                             "eps": getattr(s, "eps", None), "ebit": getattr(s, "ebit", None),
                             "years_to_terminal": getattr(s, "years_to_terminal", None),
                             "reason": s.reason}
        for axis in (axes or AXES):
            field = AXIS_LEG_FIELD.get(axis, axis)
            ad = assumptions.get(axis)
            d[f"{field}_derivation"] = (getattr(ad, "method", "") or "") if ad else ""
            d[f"{field}_adjustment"] = s.reason or ""
        out[leg] = d
    return out


# --- the shares denominator, settled rather than picked silently --------------------------------

#: Two share counts sit in every dossier and NEITHER is what item 24 ruled the denominator must be
#: (diluted outstanding AT THE VALUATION DATE): `anchor.diluted_shares` is DILUTED but a
#: WEIGHTED AVERAGE over a period, and `stock_info.shares_out` is AT A DATE but the BASIC count.
#: A weighted average over a quarter and a point-in-time count differ by roughly the buyback pace,
#: so a small gap is expected and a large one is structural — a conversion, a raise, a split — which
#: is an analyst's problem, not a rounding one. 2% separates the two cases.
SHARE_DISAGREEMENT_TOL = 0.02

#: WHICH QUANTITY the template's `diluted_shares` is, structured — `resolve_shares` takes the
#: POINT-IN-TIME `stock_info.shares_out`, never the period weighted average, so the kind follows
#: from the construction rather than from reading the basis prose. Pinned against
#: :data:`vinci.scenarios.QUANTITY_KINDS` so a renamed kind cannot silently emit an invalid stamp.
SHARES_QUANTITY_KIND = "outstanding"


def resolve_shares(doc: dict[str, Any]) -> tuple[float, str, str]:
    """The per-share denominator, as (value_in_MILLIONS, basis, source) — never picked silently.

    TAKES `stock_info.shares_out` — the POINT-IN-TIME count — because item 24 ruled the denominator
    is measured at the valuation date, and a weighted average is measured over a period. That is the
    convention SMPL's committed record already follows (88.460545, its `stock_info.shares_out`,
    against an `anchor.diluted_shares` of 89.94M).

    RETURNS THE BASIS SAYING WHAT IT IS AND WHAT IT IS NOT, because the taken value is the BASIC
    outstanding count and the ruling asks for the DILUTED one: they coincide only when the filer
    reports no dilutive difference, which is a fact about the filing and not an assumption this code
    may make. REFUSES when the two counts disagree beyond `SHARE_DISAGREEMENT_TOL`.

    NOTE THE UNIT: `ScenarioRecord.facts["diluted_shares"]` is in MILLIONS (SMPL's is 88.460545)
    while the dossier stores 88,460,545. Converted here, once, rather than at each call site.
    """
    out = _get(doc, "mechanical", "stock_info", "shares_out", "value")
    wavg = _get(doc, "anchor", "diluted_shares", "value")
    if not isinstance(out, (int, float)) or out <= 0:
        raise ProposalRefusedError(
            f"{doc.get('ticker')}: stock_info.shares_out is absent or non-positive — the per-share "
            "denominator cannot be defaulted, and a scenario value per share computed on a guessed "
            "share count is not a number")
    basis = ("point-in-time shares outstanding at the valuation date (item 24: the denominator is "
             "measured AT the date, not averaged over a period). This is the BASIC outstanding "
             "count; it equals the diluted denominator only where the filer reports no dilutive "
             "difference — state that from the filing, do not assume it.")
    if isinstance(wavg, (int, float)) and wavg > 0:
        gap = abs(wavg - out) / out
        if gap > SHARE_DISAGREEMENT_TOL:
            raise ProposalRefusedError(
                f"{doc.get('ticker')}: the two share counts disagree by {gap:.2%} — "
                f"stock_info.shares_out {out:,.0f} against anchor.diluted_shares {wavg:,.0f} "
                f"(diluted weighted-average). Beyond {SHARE_DISAGREEMENT_TOL:.0%} that is a "
                "structural change (a conversion, a raise, a split), not the buyback pace. Resolve "
                "which count belongs in the denominator before writing a value per share.")
        basis += (f" The filer's diluted weighted average is {wavg:,.0f} — {gap:.2%} away.")
    return round(out / 1e6, 6), basis, "EDGAR XBRL shares outstanding (via committed dossier)"


# --- the evidence each refused cell needs, carried from the dossier ------------------------------


def _guidance_lines(doc: dict[str, Any]) -> list[str]:
    """Every guidance row on the page, each carrying its own vintage mark. ONE copy, read by the R1
    evidence (under revenue) and the R4 evidence (under EBIT)."""
    out: list[str] = []
    # GUIDANCE COMES FROM `primary_source`, WHICH KNOWS WHICH GUIDE IS CURRENT.
    #
    # It used to read `drawdown_cause.revised_guidance` and print whatever that held under the
    # label "current guidance". On SMPL that field holds the APRIL release, so the template told
    # the analyst — on the page they set six numbers from — that the current outlook was
    # "$1.31 to $1.35 billion, or -10% to -7%" and "300 to 350 basis points". The July guide is
    # $1.345–1.355B, -7% to -6%, roughly -375bps. That is audit defect P2 in the DECISION AID
    # rather than the prose, and it survived the 2026-08-04 fix because that fix went to the LLM
    # brief while this read a different field entirely.
    #
    # Both now derive the vintage from ONE shared helper, so they cannot drift apart again. Every
    # guide is shown — mark, never drop; the cut sequence is itself evidence — and each carries
    # its own vintage, so no line is silently promoted to "current".
    ps_raw = _get(doc, "mechanical", "primary_source")
    if isinstance(ps_raw, dict):
        ps = PrimarySource.model_validate(ps_raw)
        newest = newest_guidance_date(ps)
        for r in ps.releases:
            if not r.guidance:
                continue
            mark = guidance_vintage_mark(r.filed, newest)
            for g in r.guidance:
                if g.qualitative:
                    val = "QUALITATIVE (no number stated)"
                elif getattr(g, "basis", "level") == "change":
                    # labelled, for the same reason the brief labels it: an analyst reading
                    # "-350–-300" beside a "%" unit reads a margin, not a movement
                    val = f"CHANGE of {g.low}–{g.high}"
                else:
                    val = f"{g.low}–{g.high}"
                out.append(
                    f"guidance ({g.metric} {g.period}): {val} {g.unit or ''}".rstrip()
                    + f"{mark} → {g.source_ref}")
    return out


def _operating_driver_lines(doc: dict[str, Any]) -> list[str]:
    """The page's operating-driver rows, unsplit, NOT truncated. ONE copy, read by the R1 and R4
    evidence; empty when the page has none."""
    # --- THE OPERATING DRIVERS, UNSPLIT AND UNDER EVERY AXIS ------------------------------------
    # The rows the analyst is setting six numbers against were, until 2026-08-04, capped out of the
    # artifact entirely; they are now kept in full. They belong in the template because the page
    # having them is not the same as the ANALYST having them at the judgment.
    #
    # WHY THEY ARE NOT SPLIT BY AXIS, and why that is not laziness: `kind` describes the NATURE OF
    # THE STATEMENT, not the valuation axis it informs. Measured on SMPL's own rows — `attribution`
    # rows are all EXPENSE lines (operating expenses, S&M, G&A), which inform MARGIN and not
    # revenue; `pricing_action` ("price increase across most of portfolio") moves revenue AND margin
    # together; and `leading_indicator` is defined as a unit-volume/KPI run-rate, which is
    # revenue-shaped on SMPL today but was `adjusted gross margin` on BRBR. **No mapping is
    # derivable from the field**, and inventing a classifier here is the same move refused at
    # extraction and at render. So: the full set under each axis, and the analyst reads.
    rows = _get(doc, "mechanical", "operating_drivers", "rows") or []
    if rows:
        head = (f"OPERATING DRIVERS ({len(rows)} rows, unsplit — `kind` states what KIND of "
                "claim a row is, not which axis it informs, so no axis mapping is derivable "
                "from it and none was invented)")
        lines = [head]
        for r in rows:
            # NOT TRUNCATED. The 130-char cap here was copied from `_operating_drivers_digest`,
            # where it bounds LLM *input* and earns its keep. A template is a FILE THE ANALYST
            # READS — there is no token budget to protect, so the cap bought nothing and cost
            # something: measured across the fleet, 11 of 242 values exceeded it and TWO carried a
            # figure in the tail that the kept head did not (CNXC `30,`, VITL `2026`). Small
            # figures, but this is the row cap's argument one scale down — a bound that buys
            # nothing still drops things.
            lines.append(
                f"  [{r.get('kind')}] {r.get('metric')}: {r.get('value')} → {r.get('source_ref')}")
        return lines
    return []


def evidence_for(doc: dict[str, Any]) -> dict[str, list[str]]:
    """What the analyst needs in front of them for the six cells the machine will not propose.

    A line reading "bear revenue: required" is a FORM. The evidence is already in the dossier, and
    withholding it means the analyst goes and finds it by hand — which is where an unanchored number
    acquires an unstated derivation. Keyed by axis, since bear and bull read the same frame.
    """
    ev: dict[str, list[str]] = {"revenue": [], "margin": [], "multiple": []}

    # revenue — the consensus frame with its n and dispersion, LTM, guidance, and the reported arc
    for r in _get(doc, "mechanical", "consensus_context", "consensus_levels", "Revenue") or []:
        ev["revenue"].append(
            f"consensus FY{r.get('fy')}: median {r.get('median')} · low {r.get('low')} · "
            f"high {r.get('high')} · n {r.get('estimates')} · sd {r.get('std_dev')}")
    fs = _get(doc, "mechanical", "financial_summary", "annual", "value") or {}
    cols = fs.get("columns") or []
    for row in fs.get("rows") or []:
        # THE LEVEL ROW ONLY. `startswith("revenue")` also matches "Revenue YoY"/"Revenue QoQ",
        # which emitted a second, EMPTY arc line — evidence nobody can read is noise in a block
        # whose purpose is to be read.
        label = str(row.get("label", "")).strip().lower()
        if label.split(" (")[0] not in ("revenue", "total revenue"):
            continue
        pairs = [f"{c} {v}" for c, v in zip(cols, row.get("values") or [], strict=False)
                 if v is not None]
        if pairs:
            ev["revenue"].append("reported/estimated revenue arc: " + " → ".join(pairs))
    ev["revenue"].extend(_guidance_lines(doc))

    # margin — the RAW per-FY series, because "clean" is the judgment the machine cannot make
    mt = _get(doc, "mechanical", "quality", "margin_trend")
    if isinstance(mt, dict) and mt.get("value"):
        # BASIS LABELLED IN THE LINE. This is the ONE EBITDA figure in a block whose anchor, raw
        # series and requested leg are all EBIT — and with SMPL's D&A at ~2.7% of revenue a 16%
        # EBITDA LTM sits deceptively close to a 15.4481% EBIT anchor. This is the axis SS-D
        # happened on; an unlabelled basis is how two numbers get averaged into one.
        ev["margin"].append(
            f"margin trend (CIQ) — **EBITDA basis**, NOT the EBIT margin this leg asks for: "
            f"{str(mt['value'])[:600]}")
    mg = _get(doc, "anchor", "margin") or {}
    if mg.get("value") is not None:
        ev["margin"].append(
            f"anchor median {float(mg['value']) * 100:.4f}% over {mg.get('anchor_years')} FY — "
            f"{mg.get('source')}")
    ev["margin"].append("RAW per-FY operating margins are EDGAR OperatingIncomeLoss ÷ total "
                        "revenue; a year carrying a one-off is NOT clean, and deciding which years "
                        "are clean is the judgment this cell exists for.")

    # multiple — the own-history band AND the peer row, side by side. Anchoring on own history
    # alone is how a name reads conservative while trading at a premium to its peers.
    # BOTH histories where rent is material, each labelled, and which one R1 prices on: CIQ's
    # own and the peer row are struck on a lease-inclusive TEV, so neither is the basis of the
    # net debt this record subtracts (2026-10-19).
    sel = r1_multiple_band(_get(doc, "mechanical") or {})
    ciq_oh = (_get(doc, "mechanical", "valuation", "own_history", "value") or [None])[0]
    shown = ([("ex-lease (R1's basis)", sel.band)] if sel.ex_lease else []) + [
        ("CIQ" if sel.ex_lease or sel.refusal else "", ciq_oh)]
    for tag, oh in shown:
        if not isinstance(oh, dict):
            continue
        # `percentile` is WHERE CURRENT SITS in its own range — not a 25th-percentile LEVEL. The
        # first cut of this line labelled it `p25`, which would have put a 0.037 rank where a
        # multiple belongs: one name, two meanings, in a block whose whole job is to be read.
        pct = oh.get("percentile")
        rank = f"{float(pct) * 100:.1f}th pctile of its own range" if isinstance(
            pct, (int, float)) else "rank unknown"
        ev["multiple"].append(
            f"own history{' ' + tag if tag else ''} {oh.get('metric')}: current "
            f"{oh.get('current')} ({rank}) · low {oh.get('low')} · median {oh.get('median')} · "
            f"high {oh.get('high')} · {oh.get('n_closes')} closes over "
            f"{oh.get('window_span_years')}y")
    if sel.ex_lease:
        ev["multiple"].append(
            f"LEASE BASIS — {sel.materiality}. This record subtracts net debt EXCLUDING operating "
            "leases, so its exit multiple must be on TEV less operating leases. CIQ's own history "
            "and the peer row below put operating leases in TEV and rent back in EBITDA; a "
            "multiple read off either is on the wrong basis for this bridge.")
    elif sel.refusal:
        ev["multiple"].append(f"LEASE BASIS — {sel.materiality}. R1 refuses: {sel.refusal}.")
    tm = _get(doc, "mechanical", "peer_comps", "trading_multiples")
    if isinstance(tm, dict) and tm.get("value"):
        ev["multiple"].append(f"PEER CROSS-SECTION (LTM **and** NTM) — {tm['value']}")
        ev["multiple"].append(
            "READ THE PEER ROW BESIDE THE OWN-HISTORY "
            "BAND, AND READ NTM BESIDE LTM. An own-history "
            "anchor with a haircut can still sit at a PREMIUM to the peer median, and the LTM and "
            "NTM bases can disagree in SIGN — BRBR is the live case (LTM 8.8 vs peer 6.9, a "
            "premium; NTM 8.65 vs peer 9.44, a discount). Neither number alone tells you where the "
            "multiple sits, and a synthesis roll can "
            "drop the forward leg without saying so: SMPL's "
            "2026-08-04 re-assembly did exactly that, arguing from trailing 5.3x while the "
            "previous roll had warned trailing-only 'cannot distinguish overshoot from terminal'."
            " The template carries both so the analyst does not depend on what a roll happened to "
            "cite.")

    lines = _operating_driver_lines(doc)
    for axis in AXES:
        ev[axis].extend(lines)
    return ev


# --- the template, and reading one back ---------------------------------------------------------

#: Keys the template carries for the analyst's benefit and `scenario-create` ignores. Underscore
#: marks them, so a reviewer reading the diff can see at a glance what is input and what is context.
COMMENTARY_PREFIX = "_"

#: Why the horizon is never proposed — one sentence, read by the R1 and R4 templates alike.
HORIZON_WHY = ("no statistic anchors WHEN a thesis realises — it is the analyst's judgment about "
               "the catalyst path, and a default here would set the IRR the record is graded on. "
               "State it in years: 1.5 = 18 months.")


def _refuse_if_recipe_unresolved(doc: dict[str, Any], ticker: str) -> None:
    """REFUSE before shaping a template the dossier has already said is the wrong shape.

    WHAT WENT WRONG, and the crash was the SYMPTOM rather than the defect. NCNO and UBER both carry
    `anchor.applicable=false` with `recipe_hint="R2_NEEDED"` and the reason *"no positive operating
    margin over available history — needs revenue-anchored recipe"*. `propose_anchors` therefore
    returns no `("margin","base")` anchor — revenue and multiple still resolve, margin alone does
    not — and the template builder indexed `UNPROPOSED_REASON[("margin","base")]`, a table with only
    bear/bull entries, so it raised `KeyError: ('margin', 'base')`.

    A `.get()` FALLBACK WOULD HAVE BEEN THE WRONG FIX, and it was the first one proposed. It turns
    the crash into an R1-shaped template — revenue/margin/multiple — for a name the dossier
    explicitly marks as needing a revenue-anchored recipe. The analyst then fills in a margin the
    recipe does not read and creates a record on the wrong tier. A crash is bad; a plausible wrong
    template is worse, because it is actionable.

    THE PROPOSE PATH HAD NO TIER AWARENESS AT ALL. `check_tier_agreement` exists and knows exactly
    this state, but it is wired only into `scenario-create` and `scenario-supersede`;
    `_cmd_scenario_propose` never calls it, and `KeyError` is not in the exception set that command
    catches. So the guard for this case existed and could not reach it.

    THE REASON IS THE DOSSIER'S OWN, never composed here. It already states why the anchor refused
    and which recipe it needs; re-wording that at the refusal site would be a second author for one
    fact.
    """
    if _get(doc, "anchor", "applicable") is not False:
        return
    hint = _get(doc, "anchor", "recipe_hint")
    reason = str(_get(doc, "anchor", "reason") or "").strip()
    # THE REMEDY IS PER CAUSE, because the three live causes are not one problem. Only R2_NEEDED is
    # about the missing revenue-basis path — FUBO's anchor refused on a missing own-history
    # multiple (hint `unknown`) and VITL's on a coherence guard while still hinting R1. Appending
    # the EV/Revenue sentence to all three would send two of them to fix something unrelated, which
    # is the wrong-remediation shape this repo keeps closing one artifact over.
    remedy = (
        "Resolve the recipe first: the EV/Revenue basis exists in the R2 engine (PR #188) but this "
        "template has no path to it yet."
        if hint == "R2_NEEDED" else
        "Fix the condition the anchor names, or resolve the recipe, before underwriting this name."
    )
    raise ProposalRefusedError(
        f"{ticker}: the dossier marks its anchor applicable=False"
        + (f" with hint {hint!r}" if hint else "")
        + (f" — {reason}" if reason else "")
        + ". This template is R1-shaped (revenue/margin/multiple) and emitting it would invite an "
        f"underwrite on a recipe the dossier says does not apply. {remedy}")


def build_template(doc: dict[str, Any]) -> dict[str, Any]:
    """The emitted underwrite template: anchors pre-filled, refusals carrying their evidence.

    A FILE, not a prompt — reviewable and diffable, which is what a handful of underwrites a quarter
    actually needs. The three anchored cells arrive with their `source_ref` and `vintage`; the six
    refused ones arrive EMPTY with the reason they are empty and the dossier evidence beside them.
    """
    ticker = str(doc.get("ticker") or "")
    # AN R4-TAGGED PAGE GETS AN R4-SHAPED TEMPLATE (2026-10-09). The R1 shape below pre-fills a
    # revenue, a margin and a D&A fact — three inputs `_run_r4` REFUSES — and names an EV/EBITDA
    # basis it also refuses, so an R4 underwrite could only be written by hand-deleting half the
    # template: the hand-correction §5.0 row 10 records for R3, one recipe worse.
    if _get(doc, "anchor", "recipe_hint") == RECIPE_R4:
        return build_r4_template(doc)
    _refuse_if_recipe_unresolved(doc, ticker)
    # ONE LEASE BASIS OR NO TEMPLATE (review of #750): the facts below come from the anchor, the
    # multiple from its history; a page whose lease basis the anchor is not on would pair them
    # across the lease line
    if (why := lease_basis_mismatch(doc)) is not None:
        raise ProposalRefusedError(f"{ticker}: {why}")
    ancs = {(a.axis, a.leg): a for a in propose_anchors(doc)}
    shares, sh_basis, sh_source = resolve_shares(doc)
    ev = evidence_for(doc)

    # "M shares", NOT "shares": `resolve_shares` returns MILLIONS (SMPL's committed record says
    # "M shares" for the same reason). A unit label that disagrees with its own value is the
    # `percentile`-as-`p25` class one field over.
    # STAMPED AT BIRTH (review fix, 2026-08-21). `Fact.quantity_kind` is REQUIRED on any refresh of
    # `diluted_shares`, and `refresh_record` refuses outright when the record's own fact carries no
    # stamp ("nothing to check the incoming kind against"). A template that emits the fact unstamped
    # therefore writes a record whose denominator can never again be refreshed through the ONE
    # programmatic path — forcing back the hand-edited JSON `refresh_record` exists to end — and
    # reddens `test_every_committed_diluted_shares_declares_its_quantity` the moment it is
    # committed. `resolve_shares` takes `stock_info.shares_out`, the POINT-IN-TIME count, so the
    # quantity is `outstanding` by construction, not by a reading of the prose.
    facts: dict[str, Any] = {"diluted_shares": {"value": shares, "unit": "M shares",
                                                "basis": sh_basis, "source": sh_source,
                                                "quantity_kind": SHARES_QUANTITY_KIND}}
    for key, unit in (("d_and_a", "$M"), ("net_debt", "$M")):
        f = _get(doc, "anchor", key)
        if isinstance(f, dict) and f.get("value") is not None:
            facts[key] = {"value": f["value"], "unit": f.get("unit") or unit,
                          "basis": f.get("basis") or "", "source": f.get("source") or ""}

    scenarios: dict[str, Any] = {}
    for leg in LEGS:
        cell: dict[str, Any] = {}
        for axis in AXES:
            a = ancs.get((axis, leg))
            if a is not None:
                cell[axis] = a.schema_value
                cell[f"{COMMENTARY_PREFIX}{axis}_anchor"] = (
                    f"{a.value:g}{a.unit} — {a.label} · {a.source} · vintage {a.vintage}")
                cell[f"{axis}_adjustment"] = ""      # only needed if the value is moved
            else:
                cell[axis] = None
                # `.get()` WITH A STATED FALLBACK, matching the same lookup at `validate_legs`.
                # This was a bare index and the table holds only bear/bull entries, so a missing
                # BASE anchor raised KeyError instead of writing a cell. The recipe refusal above
                # now catches the known cause (an inapplicable anchor) far earlier — this is the
                # backstop for a base axis that goes missing for some OTHER reason, where refusing
                # the whole template would be too blunt but a crash is never the right answer.
                cell[f"{COMMENTARY_PREFIX}{axis}_why_no_anchor"] = UNPROPOSED_REASON.get(
                    (axis, leg),
                    f"no anchor was computed for {leg}.{axis} and no standing reason is recorded "
                    f"for that combination — state where this number comes from in "
                    f"{axis}_derivation")
                cell[f"{axis}_derivation"] = ""      # REQUIRED — where this number came from
        cell["reason"] = ""
        if leg == "base":
            # THE HORIZON — required, never proposed (2026-08-05). The convention is nominal 2:1
            # AND a base-case IRR floor AND a stated horizon, and the horizon is the input that
            # turns a multiple into a return: proposing one would be the machine setting the IRR
            # it is about to be tested on. Same refusal class as the other six empty cells.
            cell["years_to_terminal"] = None
            # THE LEG'S FISCAL YEAR, and this one IS proposed — because the proposer already knows
            # the answer. `propose_anchors` takes the base revenue from the consensus median AT
            # `ev_gap.anchor_fy`, so a template-built record is struck at that year BY
            # CONSTRUCTION. Pre-filling it states what the proposal already did rather than
            # guessing; leaving it blank would make every created record read "unstated" forever,
            # which is the state the flag exists to reduce. An analyst who moves the revenue to
            # another year moves this with it — and then `leg_fy_problems` asks them to say why.
            cell["leg_fy"] = str(_get(doc, "mechanical", "ev_gap", "anchor_fy") or "") or None
            cell[f"{COMMENTARY_PREFIX}years_to_terminal_why_no_anchor"] = HORIZON_WHY
        # (R3) EPS — EMPTY, NEVER PROPOSED. The P/E recipe reads this and nothing else, so a
        # pre-filled number would be the machine writing the entire underwrite. It sits alongside
        # `revenue`/`margin` rather than replacing them: the template does not know which recipe
        # the analyst will choose, and a leg carrying both is refused at compute time by whichever
        # recipe it turns out to be, which is a louder failure than a template that guessed.
        cell["eps"] = None
        # (R4) NTM EBIT at exit — EMPTY, NEVER PROPOSED, for the `eps` reason: it is the whole of
        # the EV/NTM EBIT recipe's leg driver. Without the cell the field is declared on
        # `ScenarioInput` but not writable from the path that creates records (2026-10-08).
        cell["ebit"] = None

        if leg == "bear":
            cell["bear_basis"] = ""                  # own-history | bear-state-comps | peer-… |…
        cell["margin_basis"] = ""                    # EBIT | EBITDA — WHICH LINE, not provenance
        scenarios[leg] = cell

    return {
        "ticker": ticker,
        "recipe_id": _get(doc, "anchor", "recipe_hint"),
        "multiple_basis": "EV/EBITDA",
        # THE ENTRY WINDOW — EMPTY, NEVER PROPOSED. `multiple_basis` names the METRIC; this names
        # the PERIOD the entry multiple's denominator covers (NTM | LTM | FY####). The template
        # cannot know which window the analyst struck their entry multiple on — the dossier
        # publishes a price, not an entry multiple — so proposing one would be the machine
        # inventing the denominator the whole field exists to make explicit. Left blank and
        # refused at create, which is the same treatment as the six other empty cells.
        "entry_basis": "",
        # EMPTY, NEVER PROPOSED, for the same reason as `entry_basis` beside it: the denominator
        # the entry multiple divides is the analyst's to state. It is what turns a window mismatch
        # from an assertion into arithmetic — with it the roll and the re-rating are both
        # computable — so a proposed value would be the machine guessing the bridge.
        "entry_denominator": "",
        "underwrite_date": "",
        "analyst": "",
        "spot": _get(doc, "mechanical", "stock_info", "price", "value"),
        "spot_source": _get(doc, "mechanical", "stock_info", "price", "source_ref"),
        # (PR-7) THE DAY THAT SPOT IS A CLOSE OF, pre-filled from the dossier's own bar date so the
        # schema-1.5 requirement is satisfiable from the template rather than needing a hand-typed
        # date. `stock_info.as_of` IS the EOD bar the price came from — the same object, one level
        # up, because `Sourced` carries no date of its own. All 14 committed dossiers have it.
        "spot_as_of": _get(doc, "mechanical", "stock_info", "as_of"),
        "facts": facts,
        "scenarios": scenarios,
        f"{COMMENTARY_PREFIX}evidence": ev,
        f"{COMMENTARY_PREFIX}note": (
            "Three cells are pre-filled from computed anchors and carry their source and vintage; "
            "move one and you must state the adjustment. Six are EMPTY by design — each says "
            "why it "
            "has no anchor, and the evidence block carries what the dossier already knows. Keys "
            "beginning '_' are commentary and are ignored on create."),
    }



# --- (R4) the EV/NTM EBIT template ---------------------------------------------------------------

#: The bridge's two non-debt lines, by the labels `ciq_sheets.ev_bridge` writes them under.
_PREF_LINE, _MINORITY_LINE = "Total Pref. Equity", "Total Minority Interest"


def r4_bridge_fact(doc: dict[str, Any]) -> dict[str, Any]:
    """The R4 record's `net_debt` fact, from the page's `ev_bridge` — or a refusal, never a guess.

    THE CLAIMS ARE CIQ'S CURRENT TEV BUILD-UP LESS MARKET CAP — Net Debt + preferred + minority
    interest — which the operator confirmed on 2026-10-09 as what "CIQ net debt" meant: the multiple
    is CIQ's, so the bridge is the one CIQ's TEV carries. The exit value is the page's own
    `exit_claims`, where the operator's exit rule has already run (#689).

    REFUSES RATHER THAN PREFILLING, on each of:
    * **no bridge on the page** — FUBO, ORKA and TECX today;
    * **an unchecked or flagged bridge** — no CIQ TEV less market cap to check it against, or one
      it misses by more than `EV_BRIDGE_CIQ_TOL`: the exports sit on different balance sheets;
    * **a bridge and a multiple from two pulls** — the bridge's Estimates export is not the one
      `forward_consensus` (which carries today's EV/NTM EBIT) was read from;
    * **exit claims that differ by fiscal year** — the template cannot choose the record's exit year
      for the analyst. No committed page carries this today; every exit is held.
    """
    from vinci.dossier.ciq_sheets import EV_BRIDGE_CIQ_TOL

    t = doc.get("ticker")
    eb = doc.get("ev_bridge")
    if not isinstance(eb, dict):
        raise ProposalRefusedError(
            f"{t}: the page carries no `ev_bridge`, so an R4 template has no bridge from "
            "enterprise value to equity. Land it (the ev_bridge pass) or re-assemble the page "
            "first.")
    claims, ciq = eb.get("claims"), eb.get("ciq_tev_claims")
    if not isinstance(claims, (int, float)) or not isinstance(ciq, (int, float)):
        raise ProposalRefusedError(
            f"{t}: the page's bridge was never checked against CIQ's own current TEV less market "
            "cap (no comps figure) — an unchecked bridge is not prefilled into an underwrite.")
    if abs(claims - ciq) > EV_BRIDGE_CIQ_TOL:
        raise ProposalRefusedError(
            f"{t}: the page's bridge (${claims:,.1f}M) disagrees with CIQ's own TEV less market "
            f"cap (${ciq:,.1f}M) by ${claims - ciq:,.1f}M — the Financials and comps exports sit "
            "on different balance sheets. Re-pull and rebuild the bridge before underwriting.")
    fc_sha = _get(doc, "forward_consensus", "source_sha256")
    if not fc_sha or eb.get("estimates_sha256") != fc_sha:
        raise ProposalRefusedError(
            f"{t}: the bridge was built against Estimates export {eb.get('estimates_sha256')!r} "
            f"but the page's forward multiples come from {fc_sha!r} — a bridge and a multiple from "
            "two pulls. Rebuild the bridge from the page's own exports.")
    exits = [x for x in eb.get("exit_claims") or [] if isinstance(x, dict)]
    if not exits or any(not isinstance(x.get("value"), (int, float)) for x in exits):
        raise ProposalRefusedError(
            f"{t}: the page's bridge carries no complete exit claims — the operator's exit rule "
            "has not run on it, so there is no exit value to carry. Rebuild the bridge.")
    values = {round(float(x["value"]), 3) for x in exits}
    if len(values) != 1:
        listed = ", ".join(f"{x.get('fiscal_year')} {x['value']:,.1f} ({x.get('method')})"
                           for x in exits)
        raise ProposalRefusedError(
            f"{t}: the page's exit claims differ by fiscal year ({listed}) — the template cannot "
            "choose the record's exit year for you. State the claims for your exit year from "
            "`ev_bridge.exit_claims` by hand, naming that year in the basis.")
    by_label = {ln.get("label"): ln.get("value") for ln in eb.get("lines") or []
                if isinstance(ln, dict)}
    pref, minority = by_label.get(_PREF_LINE) or 0.0, by_label.get(_MINORITY_LINE) or 0.0
    fys = ", ".join(str(x.get("fiscal_year")) for x in exits)
    methods = "/".join(sorted({str(x.get("method")) for x in exits}))
    note = str(eb.get("note") or "").strip()
    return {
        "value": values.pop(),
        "unit": "$M",
        "basis": (
            f"CIQ's TEV claims less market cap: Net Debt {eb.get('net_debt'):,.1f} + preferred "
            f"{pref:,.1f} + minority interest {minority:,.1f} = {claims:,.1f} ($M), at the "
            f"{eb.get('balance_sheet_date')} balance sheet — the build-up CIQ's TEV, and so the "
            "EV/NTM EBIT multiple, carries (operator-confirmed 2026-10-09). At exit ("
            f"{fys}): {methods}" + (f" — {note}" if note else "") + "."),
        "source": (
            f"dossier ev_bridge — CIQ Financials {eb.get('source_file')} (sha "
            f"{eb.get('source_sha256')}), equal to CIQ's TEV less market cap "
            f"(${ciq:,.1f}M, {eb.get('ciq_tev_claims_source')}); Estimates sha "
            f"{eb.get('estimates_sha256')}"),
    }


def _ev_ntm_ebit_band(doc: dict[str, Any]) -> dict[str, Any] | None:
    """The page's own EV/NTM EBIT history band (`forward_multiple_history`), or None."""
    for s in _get(doc, "forward_multiple_history", "series") or []:
        if isinstance(s, dict) and s.get("metric") == "EV/NTM EBIT" and isinstance(
                s.get("band"), dict):
            return dict(s["band"], context_only=s.get("context_only"), note=s.get("note"))
    return None


def _r4_multiple_why(doc: dict[str, Any]) -> str:
    """Why the R4 multiple is not proposed — with the page's own band, when the band says more.

    NOT PROPOSED BECAUSE NOTHING IS RULED, and the page shows what an unruled default would do.
    R1's base anchor is a TRAILING EV/EBITDA median — a different multiple — and no ruling makes the
    EV/NTM EBIT history its R4 counterpart. Measured on AMZN 2026-10-09: the latest observed close,
    22.59x on 2026-09-16, sits BELOW its own nine-year low (23.22x) and the median is 52.56x, so a
    median default would propose 2.3× that close, struck on years when the EBIT it priced was a
    fraction of today's. THAT CLOSE IS NOT TODAY'S MULTIPLE (schema correction, 2026-10-09): the
    sentence names it as the observation it is, with its date.
    """
    why = ("no ruled anchor for a forward EV/EBIT multiple — R1's own-history anchor is a TRAILING "
           "EV/EBITDA, a different multiple, and no ruling makes the page's EV/NTM EBIT history "
           "the base. That history is in the evidence")
    b = _ev_ntm_ebit_band(doc)
    last, lo, hi, med = ((b or {}).get(k)
                         for k in ("latest_observed_close", "low", "high", "median"))
    if b and all(isinstance(v, (int, float)) for v in (last, lo, hi, med)) and last and (
            last < lo or last > hi):
        why += (f"; the latest observed close, {last:.2f}x on {b.get('latest_close_date')}, sits "
                f"OUTSIDE it ({lo:.2f}x–{hi:.2f}x), so its median ({med:.2f}x) would propose "
                f"{med / last:.1f}× that close")
    return why + "."


def r4_evidence(doc: dict[str, Any]) -> dict[str, list[str]]:
    """What the analyst needs beside the R4 cells: EBIT, the multiple, and the bridge.

    Every list is COMPLETE — a template is a file the analyst reads, so no row is capped (the
    operating-driver note above says why). Each line names its source layer.
    """
    ev: dict[str, list[str]] = {"ebit": [], "multiple": [], "net_debt": []}
    fc = doc.get("forward_consensus") or {}
    as_of = fc.get("as_of")

    # ebit — consensus by FY with its dispersion, the path it took, the reported arc, the final
    # consensus's historical miss, and any guidance
    for r in fc.get("spreads") or []:
        if r.get("metric") == "EBIT":
            ev["ebit"].append(
                f"consensus EBIT {r.get('period')} ($M, CIQ Estimates {as_of}): median "
                f"{r.get('median')} · mean {r.get('mean')} · low {r.get('low')} · high "
                f"{r.get('high')} · n {r.get('estimates')} · sd {r.get('std_dev')}")
    for r in fc.get("paths") or []:
        if r.get("metric") == "EBIT" and r.get("points"):
            pts = " → ".join(f"{p.get('months_ago')}m ago {p.get('value')}" for p in r["points"])
            ev["ebit"].append(f"consensus EBIT {r.get('period')} path ($M): {pts}")
    fs = _get(doc, "mechanical", "financial_summary", "annual", "value") or {}
    for row in fs.get("rows") or []:
        if str(row.get("label", "")).strip().lower().split(" (")[0] == "ebit":
            pairs = [f"{c} {v}" for c, v in zip(fs.get("columns") or [], row.get("values") or [],
                                                strict=False) if v is not None]
            if pairs:
                ev["ebit"].append("reported/estimated EBIT arc ($M): " + " → ".join(pairs))
    hfe = doc.get("historical_forecast_error") or {}
    obs = next((s.get("observations") or [] for s in hfe.get("series") or []
                if s.get("metric") == "EBIT"), [])
    if obs:
        ev["ebit"].append(
            f"HOW WRONG THE FINAL CONSENSUS HAS BEEN — EBIT, {len(obs)} fiscal years "
            f"({hfe.get('estimate_type')}). {hfe.get('eligibility_note')} {hfe.get('usage_note')}")
        for o in obs:
            epr = o.get("error_per_forecast_revenue")
            ev["ebit"].append(
                f"  FY{o.get('fiscal_year')} ({o.get('accounting_basis')}): actual "
                f"{o.get('actual')} vs final consensus {o.get('final_estimate')} → "
                f"{o.get('dollar_error')} $M"
                + (f", {epr:+.2%} of forecast revenue" if isinstance(epr, (int, float)) else ""))
    guidance = _guidance_lines(doc)
    ev["ebit"].extend(guidance)
    ps = _get(doc, "mechanical", "primary_source", "releases") or []
    if not any(any(w in str(g.get("metric") or "").lower() for w in ("operating income", "ebit"))
               and "ebitda" not in str(g.get("metric") or "").lower()
               for r in ps if isinstance(r, dict) for g in r.get("guidance") or []):
        ev["ebit"].append("no operating-income or EBIT guidance is read on this page"
                          + (" — the guidance above is on other lines" if guidance else ""))

    # multiple — today's, its own history, and the peers
    cm = [m for m in fc.get("current_multiples") or [] if m.get("metric") == "TEV/EBIT"]
    if cm:
        ev["multiple"].append(
            f"today's EV/EBIT (CIQ Estimates→Multiples, {as_of}): "
            + " · ".join(f"{m.get('period')} {m.get('value')}" for m in cm))
    b = _ev_ntm_ebit_band(doc)
    if b:
        pct = b.get("percentile")
        rank = (f"{float(pct) * 100:.1f}th pctile of its own range"
                if isinstance(pct, (int, float)) else "rank unknown")
        ev["multiple"].append(
            f"own history EV/NTM EBIT (CIQ Financials→Multiples): latest observed close "
            f"{b.get('latest_observed_close')} on {b.get('latest_close_date')} ({rank}; not in the "
            f"distribution) · low {b.get('low')} · median {b.get('median')} · high "
            f"{b.get('high')} · {b.get('n_closes')} earlier closes over "
            f"{b.get('window_span_years')}y"
            + (" · CONTEXT ONLY" if b.get("context_only") else "")
            + (f" · {b['note']}" if b.get("note") else ""))
    tm = _get(doc, "mechanical", "peer_comps", "trading_multiples")
    if isinstance(tm, dict) and tm.get("value"):
        ev["multiple"].append(f"PEER CROSS-SECTION (LTM and NTM) — {tm['value']}")

    # net_debt — the bridge, line by line, its checks, and the exit rule as run
    eb = doc.get("ev_bridge") or {}
    for ln in eb.get("lines") or []:
        sign = "+" if ln.get("sign", 1) > 0 else "−"
        ev["net_debt"].append(f"{sign} {ln.get('label')}: {ln.get('value')} ($M, "
                              f"{ln.get('as_of')})")
    if eb:
        ev["net_debt"].append(
            f"= claims {eb.get('claims')}; CIQ's own TEV less market cap "
            f"{eb.get('ciq_tev_claims')} ({eb.get('ciq_tev_claims_source')}); CIQ 'Net Debt' "
            f"line {eb.get('net_debt')}")
        ev["net_debt"].append(
            f"EDGAR cross-check (lease-inclusive net debt, not the bridge): "
            f"{eb.get('edgar_net_debt')}"
            + (f" — {eb.get('edgar_source')}" if eb.get("edgar_source") else " — withheld"))
        cons = eb.get("consensus") or {}
        for y in cons.get("years") or []:
            ev["net_debt"].append(
                f"consensus net-debt line FY{y.get('fiscal_year')}: reported {y.get('reported')} "
                f"vs balance sheet {y.get('balance_sheet')} ({y.get('balance_sheet_date')}) — gap "
                f"{y.get('gap_ratio')}")
        ev["net_debt"].append(
            f"consensus line same-basis: {cons.get('same_basis')} · current: {cons.get('current')}"
            + (f" · {cons['note']}" if cons.get("note") else ""))
        for x in eb.get("exit_claims") or []:
            ev["net_debt"].append(f"exit claims {x.get('fiscal_year')}: {x.get('value')} "
                                  f"({x.get('method')})")
        ev["net_debt"].append(f"RULE — {eb.get('rule')}")
    drivers = _operating_driver_lines(doc)
    ev["ebit"].extend(drivers)
    ev["multiple"].extend(drivers)
    return ev


def build_r4_template(doc: dict[str, Any]) -> dict[str, Any]:
    """The R4 (EV/NTM EBIT) underwrite template: the recipe's two axes, its bridge, its evidence.

    WHAT IS THE MACHINE'S, AND WHAT IS NOT. The facts are the machine's — the share count
    (`resolve_shares`, as R1) and the bridge (`r4_bridge_fact`, the page's CIQ TEV claims held to
    exit by the operator's rule). The legs are not: NTM EBIT at exit is the recipe's whole leg
    driver (the R3 EPS rule) and no ruling anchors a forward EV/EBIT multiple, so all six cells
    arrive EMPTY with their reasons, and `scenario-create` requires a derivation for each.

    ONLY THE CELLS THE RECIPE READS. `_run_r4` refuses a revenue, margin or EPS on a leg and a D&A
    fact, so none is emitted — a cell the recipe refuses is not a convenience but a trap.
    """
    ticker = str(doc.get("ticker") or "")
    # THE BRIDGE FIRST: it is the input that makes this an R4 template at all, so a page without
    # one is told that — not some other refusal that happens to be checked earlier (FUBO's share
    # counts also disagree, and reporting that first hid the missing bridge).
    bridge = r4_bridge_fact(doc)
    shares, sh_basis, sh_source = resolve_shares(doc)
    facts: dict[str, Any] = {
        "diluted_shares": {"value": shares, "unit": "M shares", "basis": sh_basis,
                           "source": sh_source, "quantity_kind": SHARES_QUANTITY_KIND},
        "net_debt": bridge,
    }
    anchor_fy = _get(doc, "mechanical", "ev_gap", "anchor_fy")
    multiple_why = _r4_multiple_why(doc)
    scenarios: dict[str, Any] = {}
    for leg in LEGS:
        cell: dict[str, Any] = {
            "ebit": None,
            f"{COMMENTARY_PREFIX}ebit_why_no_anchor": R4_EBIT_WHY,
            "ebit_derivation": "",                   # REQUIRED — where this number came from
            "multiple": None,
            f"{COMMENTARY_PREFIX}multiple_why_no_anchor": multiple_why,
            "multiple_derivation": "",               # REQUIRED
            "reason": "",
        }
        if leg == "base":
            cell["years_to_terminal"] = None
            cell[f"{COMMENTARY_PREFIX}years_to_terminal_why_no_anchor"] = HORIZON_WHY
            # NOT PROPOSED, unlike R1's: R1 pre-fills the EV-gap's anchor year because its revenue
            # anchor is struck there, BY CONSTRUCTION. R4 proposes no EBIT, so there is no year the
            # proposal already chose — pre-filling one would be a guess dressed as a statement.
            cell["leg_fy"] = None
            cell[f"{COMMENTARY_PREFIX}leg_fy_why_not_proposed"] = (
                "the fiscal year this leg's NTM EBIT is struck at — not proposed, because R4 "
                "proposes no EBIT to strike it at"
                + (f". A year other than the EV-gap's FY{anchor_fy} states why in `reason`"
                   if anchor_fy else "") + ".")
        if leg == "bear":
            cell["bear_basis"] = ""
        scenarios[leg] = cell
    return {
        "ticker": ticker,
        "recipe_id": RECIPE_R4,
        "multiple_basis": BASIS_EV_NTM_EBIT,
        "entry_basis": "",
        "entry_denominator": "",
        "underwrite_date": "",
        "analyst": "",
        "spot": _get(doc, "mechanical", "stock_info", "price", "value"),
        "spot_source": _get(doc, "mechanical", "stock_info", "price", "source_ref"),
        "spot_as_of": _get(doc, "mechanical", "stock_info", "as_of"),
        "facts": facts,
        "scenarios": scenarios,
        f"{COMMENTARY_PREFIX}evidence": r4_evidence(doc),
        f"{COMMENTARY_PREFIX}note": (
            "R4 — EV/NTM EBIT. No leg cell is pre-filled: NTM EBIT at exit is the recipe's whole "
            "leg driver, and no ruling anchors a forward EV/EBIT multiple, so each cell states why "
            "it is empty and needs a derivation. The two facts are the machine's: the share count, "
            "and the bridge — CIQ's TEV claims less market cap, held to exit by the operator's "
            "rule. Keys beginning '_' are commentary and are ignored on create."),
    }


def legs_from_template(tpl: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """The supplied legs, with commentary keys stripped — what `validate_legs` consumes."""
    out: dict[str, dict[str, Any]] = {}
    for leg, cell in (tpl.get("scenarios") or {}).items():
        out[leg] = {k: v for k, v in cell.items() if not k.startswith(COMMENTARY_PREFIX)}
    return out


def assumptions_from(doc: dict[str, Any], legs: dict[str, dict[str, Any]],
                     *, axes: tuple[str, ...] | None = None,
                     basis: str | None = None) -> dict[str, dict[str, Any]]:
    """The per-axis `AssumptionDerivation` payload — where the record's PROVENANCE actually lives.

    WITHOUT THIS THE WHOLE DESIGN LEAKS, and the first cut of `scenario-create` leaked it. The
    template shows each anchor's source and vintage in a `_`-prefixed commentary key, and
    `legs_from_template` strips those before validation; `ScenarioInput` has nowhere to put a
    `source_ref` either. So the write validated the analyst's adjustments and derivations, confirmed
    every number was accounted for — and then persisted a record containing NONE of it.
    `Anchor.as_refpoint()` had zero production callers: defined, never called.

    A record written that way passes every guard while carrying LESS provenance than the
    hand-authored records this path was built to replace. That is worse than no tool.

    So: each axis gets its anchor as a source- and vintage-bearing `RefPoint`, and a `method`
    sentence assembled from what the analyst actually said on each leg. The method is required
    non-blank by the schema, and here it is composed only of analyst words — never invented.

    ``axes``/``basis`` ARE THE SAME PER-RECIPE PAIR `validate_legs` TAKES, and they are not
    optional in practice: this is that function's sibling, reading the identical leg keys off the
    identical legs. Teaching one recipe-awareness and not the other is this repo's most-repeated
    defect — the record would validate on `earnings`/`multiple` and then compose its provenance
    over `revenue`/`margin`, writing a record whose stated method covers axes its arithmetic does
    not use and omits the two it does. Both callers pass both, from `scenarios.axes_for`.
    """
    axes = axes or AXES
    by = {(a.axis, a.leg): a for a in _anchors_on_basis(propose_anchors(doc), basis)}
    out: dict[str, dict[str, Any]] = {}
    for axis in axes:
        # the LEG FIELD, not the axis — an `earnings` axis states itself in `eps_derivation`,
        # beside the `eps` it explains. Reading `earnings_derivation` here would find nothing and
        # silently fall through to the "stated per leg" placeholder, dropping the analyst's own
        # words out of the one field built to carry them.
        field = AXIS_LEG_FIELD.get(axis, axis)
        said: list[str] = []
        for leg in LEGS:
            cell = legs.get(leg) or {}
            if (axis, leg) in by:
                adj = str(cell.get(f"{field}_adjustment") or "").strip()
                # NAME THE STATISTIC IN WORDS, not the house label: the prose linter flags
                # "anchor" as a house token ("state the claim, not the house label"), and it is
                # right — a reader wants "at the eight-year operating-margin median", not a word
                # that means something only inside this repo. Analyst words are never edited; this
                # is the sentence the MACHINE composes, so it is the machine's to get right.
                a = by[(axis, leg)]
                said.append(f"{leg}: {adj}" if adj else f"{leg}: at the {a.label}")
            else:
                drv = str(cell.get(f"{field}_derivation") or "").strip()
                if drv:
                    said.append(f"{leg}: {drv}")
        refs = [a.as_refpoint().model_dump() for (ax, _lg), a in by.items() if ax == axis]
        out[axis] = {
            "method": " · ".join(said) or f"{axis}: stated per leg in the leg reasons.",
            "references": refs,
        }
    return out
