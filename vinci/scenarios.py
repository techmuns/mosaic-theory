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
import re
import warnings
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ONE bar / ONE formula. The compute layer (vinci.dossier.midcycle) owns the ratified
# convention; the record layer re-exports — judge (clears_bar) and stamp (Result.bar) can no
# longer diverge, and the stamped recipe_formula is the SAME constant the engine states.
from vinci.dossier.midcycle import BAR, R1_FORMULA
from vinci.prose_lint import ProseRegisterWarning, lint_record

SCHEMA_VERSION = "1.4"

# WHERE a bear multiple came from. Each member is a different KIND of evidence, and the difference
# is what the 2026-07-22 audit turned on: an own-history floor drawn from a growth-era-only window
# is not the same claim as a multiple taken from businesses actually in the state being modelled.
BEAR_BASES = frozenset({
    "own-history",        # the name's own committed multiple band
    "bear-state-comps",   # businesses observed IN the downside state (the IT correction)
    "peer-reference",     # a named peer or peer set, not the name's own history
    "analyst",            # judgment, stated as judgment — legitimate, but labelled
})
# WHICH earnings line a margin cell is stated on. The two differ by D&A, and a silent conversion
# between them put a 15.5% EBITDA cell into a brief as a 13.2% EBIT cell.
MARGIN_BASES = frozenset({"EBIT", "EBITDA"})

# --- (schema 1.3, ratified 2026-07-27 — docs/refpoint_schema_proposal.md) ----------------------
# WHAT STATISTIC a reference is. The census of all 132 committed references found the role
# travelling as prose in 50 (38%), and one production consumer already REGEX-PARSING labels for it
# (uw-card's find(/median/i) rendered the PEER median on MVST while the own median sat two rows
# down labelled "unusable" — which median showed was decided by array order). One tag, not a
# statistic×population split (ratified): `peer_median` is its own member because the only
# distinction any code needs today is own-median vs peer-median. Drawn from real usage — every
# member had ≥2 uses at ratification; extend deliberately, as BEAR_BASES is.
REF_ROLES = frozenset({
    "median", "mean", "percentile", "band_low", "band_high", "trough", "peak",
    "current", "reported", "consensus", "guidance", "peer_median", "peer", "analogue",
})
# The unit vocabulary — exactly the units found in legitimate committed use at the census, no
# invention. The one committed unit OUTSIDE this set was a smuggled SENTENCE (":1 (cell A at the
# re-set 14% normal; cell B ≈1.73)") — a second value hidden where only a unit may stand. A unit
# is a unit; a finding is an AxisNote.
REF_UNITS = frozenset({"%", "x", "$M", "$/share", ":1", "years", "% of revenue", "count"})
# From this schema version, reference STRUCTURE must be fields, not label prose: the leg a
# reference anchors, its exclusion, and its unit all live in their fields, and a label carrying
# them as prose is REFUSED at write (the gate names the field to use). Older records predate the
# fields and stay writable — the rule binds forward, never retroactively (BASIS_REQUIRED_FROM
# precedent).
FIELDED_REFS_FROM = "1.3"
# From 1.4 a reference must state WHEN its value is from. A `source` names the source and the
# concept — "CIQ Estimates->Trends", "EDGAR OperatingIncomeLoss / revenue" — and 70 of the 119
# committed references carry no period at all, so the cite answers WHERE and never WHEN. That is
# audit P3 pt1: a provenance label naming the wrong object.
#
# BINDS FORWARD, and the 70 are NOT backfilled. Their vintage is not in the record and not
# recoverable from it: it lives in the analyst's source material (the CIQ export date, the filing
# period behind each concept). Backfilling is a manual pass over 119 references and an OPERATOR
# DECISION, not a queued build — so **P3 pt1 does not close on code.** The field stops the next
# reference from being unstamped; it does not repair the ones that already are.
VINTAGE_REQUIRED_FROM = "1.4"
# The label patterns the 1.3 gate refuses — the exact prose shapes the census found carrying
# structure. Kept beside the model, not in a consumer: a renderer must never need these.
# DELIBERATELY NARROW (the prose_lint convention — each narrowing pinned with the real sentence
# that motivated it): "not derived" is NOT an exclusion token, because AORT's "street operating
# margin, FY2026 - stated, not derived" is PROVENANCE (the street stated it; we did not derive
# it) on a row that IS used — refusing it would force a used reference to claim exclusion.
_LEG_IN_LABEL = re.compile(r"\b(bear|base|bull)\b", re.IGNORECASE)
_EXCLUSION_IN_LABEL = re.compile(
    r"\b(NOT a reference|not used|unusable|DEAD REGIME|STRADDLES)\b", re.IGNORECASE)

# RETIRED VERDICT FIELDS — names that were once written into records and are now gone. They stay
# listed because pydantic's default is extra="ignore": a record file still carrying a retired key
# would load CLEAN and lose the analyst's words on the next write — a silent drop, which is the one
# failure mode this repo never accepts. Loading such a record RAISES instead, naming the key, so
# the words are migrated deliberately or discarded deliberately, never by omission.
RETIRED_VERDICT_FIELDS: frozenset[str] = frozenset({"status_note"})

# From this schema version the BEAR leg must carry both labels at write. Older records predate the
# fields and stay writable — the rule binds forward, never retroactively.
BASIS_REQUIRED_FROM = "1.2"
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
    display-natural units (``4.06`` + ``"%"``, ``6.56`` + ``"x"``) — no consumer re-scales it.

    (schema 1.3) The STRUCTURE a label used to carry as prose is fields now: ``role`` (what
    statistic), ``leg`` (which case it anchors — None for frame-level context, which most are),
    and ``excluded`` (shown-but-not-used, with its reason). Labels stay verbatim analyst text and
    are never parsed — the fields are the machine-readable duplicate of what the label says to a
    human, and the ONLY thing a consumer may select on."""

    label: str
    value: float
    unit: str                      # from REF_UNITS on 1.3 records ("%" | "x" | "$M" | …)
    source: str                    # the filing/tag/run that produced the value
    #: WHEN the value is from — the period it describes, not when it was fetched. Free text
    #: because the answer is a fiscal period as often as a date ("FY2025", "Q1 2026", "2026-07-20"),
    #: and forcing a `date` would make an analyst invent a day for a year. Required from 1.4
    #: (:data:`VINTAGE_REQUIRED_FROM`); None stays legal forever on legacy records.
    vintage: str | None = None
    role: str | None = None        # REF_ROLES member; None = untagged (legal forever on legacy)
    leg: Literal["bear", "base", "bull"] | None = None   # which case this anchors; None = context
    excluded: bool = False         # recorded but NOT used — renders dimmed, never selected
    excluded_reason: str | None = None                   # REQUIRED iff excluded

    model_config = {"frozen": True}

    @field_validator("label", "unit", "source")
    @classmethod
    def _ref_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("a reference value with no label/unit/source cannot be verified — "
                             "refusing to record it")
        return v

    @field_validator("role")
    @classmethod
    def _role_known(cls, v: str | None) -> str | None:
        if v is not None and v not in REF_ROLES:
            raise ValueError(f"role {v!r} is not one of {sorted(REF_ROLES)} — an unlisted role is "
                             "not selectable; add the member deliberately (BEAR_BASES precedent)")
        return v

    @model_validator(mode="after")
    def _excluded_pair_coherent(self) -> RefPoint:
        # mirrors the margin/margin_basis pair: a reason for an exclusion that is not declared is
        # refused, and an exclusion with no reason is a judgment the reader cannot review.
        if self.excluded and not (self.excluded_reason or "").strip():
            raise ValueError(f"{self.label!r}: excluded=True requires excluded_reason — an "
                             "exclusion whose why is unstated cannot be reviewed")
        if not self.excluded and self.excluded_reason is not None:
            raise ValueError(f"{self.label!r}: excluded_reason without excluded=True — a reason "
                             "for an exclusion that is not declared")
        return self


class AxisNote(BaseModel):
    """A dated analyst FINDING about one assumption axis — prose with provenance, in the
    leg-reason register. Exists because the SMPL 2026-07-26 re-verification produced a two-number
    finding (entry-boundary cells 1.96/1.73 vs the 2:1 bar) with nowhere to live: its prose was
    poured into a 380-char reference ``label`` and its second value SMUGGLED into ``unit``. A
    finding is a note beside honest references, never a fake reference."""

    text: str
    date: str                      # ISO date the finding was recorded
    source: str | None = None      # provenance when the note carries numbers

    model_config = {"frozen": True}

    @field_validator("text")
    @classmethod
    def _note_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("a blank note records nothing — refusing it")
        return v

    @field_validator("date")
    @classmethod
    def _note_date_iso(cls, v: str) -> str:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError(f"note date {v!r} is not ISO (YYYY-MM-DD) — an undatable finding "
                             "cannot be sequenced against the record's history")
        return v


class AssumptionDerivation(BaseModel):
    """HOW one assumption axis was modeled: a one-sentence analyst method + the reference frame.
    ``references`` MAY be empty — a pure-judgment method honestly stated beats a fabricated
    reference; a blank method is refused like a blank reason.

    A method sentence is DRAFTED with the run and RATIFIED by the human at review. ``ratified_by``
    /``ratified`` record that second act, so a reviewer can tell a sentence the analyst stood
    behind from one that merely shipped with the run. Absent = not yet ratified (the honest
    default); the machine never sets them."""

    method: str
    references: list[RefPoint] = Field(default_factory=list)
    # (schema 1.3) dated findings about this axis — the home the SMPL boundary-cells narrative
    # never had. Axis-level, not record-level (ratified): the note sits beside the numbers it
    # interprets.
    notes: list[AxisNote] = Field(default_factory=list)
    ratified_by: str | None = None         # who ratified the method sentence; None while draft
    ratified: str | None = None            # ISO date of ratification; None while draft

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

    revenue: float                 # $M  (R2: TERMINAL-year revenue)
    # decimal fraction of revenue (R2: TERMINAL EBIT margin). **OMITTED on an EV/Revenue record** —
    # that basis never reads a margin, so recording one would show a driver the value never used.
    margin: float | None = None
    multiple: float                # turns, on `multiple_basis` (R2: the EXIT multiple)
    reason: str                    # WHY this deviates from the anchor — required, never blank
    # (R2) years from today to this leg's terminal year. Per LEG, not per record: a bear case that
    # takes longer to arrive is worth less today, and forcing one horizon on all three legs would
    # hide exactly that. None on R1 records, which have no horizon.
    years_to_terminal: float | None = None

    # --- BASIS LABELS (2026-07-22) -------------------------------------------------------------
    # WHERE the bear multiple came from, and WHICH earnings line the margin is stated on. Both
    # exist because both have already gone wrong:
    #   * IT's bear multiple was drawn from a band whose window opens inside the growth era, so its
    #     "floor" had never seen the state the bear leg described. Naming the provenance makes that
    #     inspectable instead of implicit.
    #   * an advisory cell of 15.5% EBITDA margin reached a brief as 13.2% EBIT margin — a silent
    #     D&A add-back. A margin without its line is not a number, it is two numbers.
    # Required on the BEAR leg at write from schema 1.2; optional on legacy records, which predate
    # the field and must stay writable.
    bear_basis: str | None = None      # own-history | bear-state-comps | peer-reference | analyst
    margin_basis: str | None = None    # EBIT | EBITDA

    @field_validator("bear_basis")
    @classmethod
    def _bear_basis_known(cls, v: str | None) -> str | None:
        if v is not None and v not in BEAR_BASES:
            raise ValueError(f"bear_basis {v!r} is not one of {sorted(BEAR_BASES)} — an unlisted "
                             "provenance is not reviewable; add the member deliberately")
        return v

    @field_validator("margin_basis")
    @classmethod
    def _margin_basis_known(cls, v: str | None) -> str | None:
        if v is not None and v not in MARGIN_BASES:
            raise ValueError(f"margin_basis {v!r} is not one of {sorted(MARGIN_BASES)}")
        return v

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
    # EBIT / EBITDA ($M). **None on an R2 EV/Revenue leg** — not missing, but never computed: that
    # basis applies its multiple to revenue, so there is no earnings figure behind the value and
    # none is fabricated to fill the field.
    op_income: float | None = None
    ebitda: float | None = None
    ev: float                      # $M
    equity: float                  # $M
    ev_ebit: float | None = None   # CROSS-CHECK
    norm_fcf: float | None = None  # CROSS-CHECK ($M)
    # (R2) the terminal-year bridge and its present value. `value_per_share` above carries the PV —
    # it is what the ratio uses — and `value_terminal` the undiscounted terminal number. BOTH are
    # rendered and labelled: conflating them is how a five-year story gets compared against a price
    # paid today. Absent on R1 records.
    years: float | None = None
    d_and_a_t: float | None = None
    net_debt_t: float | None = None
    shares_t: float | None = None          # MILLIONS, the record convention
    value_terminal: float | None = None
    hurdle: float | None = None


class SurvivalBlock(BaseModel):
    """(R2) The survival gate, recorded in full so its runway arithmetic is re-checkable.

    A terminal value is worthless if the company never reaches the terminal year, so this is a HARD
    BLOCK on confirming a BUY rather than an input to the ratio — an asymmetry computed on a company
    that runs out of money is not a cheap asymmetry, it is a wrong one."""

    status: str                             # "PASS" | "FAIL"
    burn: float | None = None               # annual cash burn ($M, positive); None when FCF >= 0
    burn_basis: str = ""
    burn_source: str = ""
    cash: float | None = None
    facilities: float | None = None         # committed UNDRAWN only
    facilities_source: str | None = None
    runway_years: float | None = None
    years_to_breakeven: float | None = None
    announced_raise: bool = False
    raise_accession: str | None = None      # a raise counts only WITH one
    note: str = ""
    detail: list[str] = Field(default_factory=list)


class SurvivalInput(BaseModel):
    """(R2) The analyst-supplied survival inputs. Kept OFF ``facts`` because two of them are not
    numbers, and a gate whose accession lived in a float field could not carry the one thing that
    makes a raise count."""

    fcf: float | None                       # $M; negative = burn. None = UNKNOWN, never assumed 0
    fcf_basis: str
    fcf_source: str
    cash: float                             # $M
    facilities: float = 0.0                 # $M, committed UNDRAWN only
    facilities_source: str | None = None
    years_to_breakeven: float | None = None
    announced_raise: bool = False
    raise_accession: str | None = None
    raise_shares: float = 0.0               # MILLIONS, the record convention
    raise_proceeds: float = 0.0             # $M — reduces terminal net debt
    # (2026-07-22) A filer that has told the SEC there is substantial doubt about its ability to
    # continue has answered the runway question itself; a positive TRAILING free cash flow cannot
    # overturn it. Setting this FORBIDS the trivial pass and makes burn_override mandatory.
    going_concern_stated: bool = False
    going_concern_accession: str | None = None
    burn_override: float | None = None      # $M/yr, positive — the CURRENT burn
    burn_override_basis: str | None = None
    latest_period_fcf: float | None = None  # $M — drives the sign-contradiction warning


class Result(BaseModel):
    """Filled by the run. ``pass_fail`` records the bar test honestly — a FAIL is a result."""

    per_scenario: dict[str, ScenarioOutcome] = Field(default_factory=dict)
    # (R2) the gate, and the discount rate the PV legs were computed at. Absent on R1 records.
    survival: SurvivalBlock | None = None
    hurdle: float | None = None
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
    # The SAME reasoning in external-reader register (STATE.md §7 item 10): plain thesis prose for
    # someone who has never seen this repo. Analyst-authored like `rationale` — the machine proposes
    # no wording here, it only flags register violations (vinci.prose_lint).
    #
    # BOTH may coexist: the card leads with the restatement and puts the original behind an
    # "as recorded <date>" expander. But the original is NOT retained by rule — §7 makes the
    # scenario-record copy the analyst's to re-word or DROP, and on 2026-07-21 they dropped all
    # four (the append-only LEDGER copy is the sealed one, and it is untouchable). So a record may
    # legitimately carry the restatement alone. Before dropping an original, check the name HAS a
    # ledger row: a watch/no-position verdict has none, so the drop is irreversible.
    # DEPRECATED 2026-07-22 — the single-register ratification. Kept nullable so historical JSON
    # still loads, but NOTHING reads it: renderer, tear-sheet, card emitter and linter all bind
    # `rationale` alone. Its sealing job moved into `rationale` itself (vinci/seal.py: growth is
    # append-only), which is strictly better — the original and its amendments read in one place,
    # in order, instead of the reader having to reconcile two registers of the same claim.
    rationale_plain: str | None = None
    rationale_plain_recorded: str | None = None   # DEPRECATED with the field above
    reunderwrite_triggers: list[str] = Field(default_factory=list)  # what would reopen the name
    # (catalyst calendar) the DATED form — analyst-typed trigger deadlines; additive-only so every
    # legacy record round-trips unchanged; `verdict.rationale` untouched → seal-safe.
    dated_triggers: list[DatedTrigger] = Field(default_factory=list)
    # A recorded BUY is the start of a forward track, so the spread needs the price and the
    # asymmetry AT the moment of the call — not the underwrite-date spot, which has since moved.
    # Both stay None for a verdict that opens no position (watch / passed).
    entry_price: float | None = None       # spot at the instant the human recorded the call
    ratio_at_entry: float | None = None    # reward/risk recomputed at entry_price
    # (avoid-leg) the asymmetry is inverted at today's price — track for short-alpha on PAPER.
    # Recording it does NOT create a position: no code path here approaches execution.
    avoid_priced: bool = False
    avoid_priced_note: str | None = None
    # RETIRED 2026-07-27: `status_note`. It was a one-line caption explaining why the status word
    # read as it did — added when the card carried a "Current state" block, retired when that block
    # was folded into the masthead and the caption turned out to be saying a third time what the
    # band already said. The header is now the RATING alone, so nothing rendered it.

    @model_validator(mode="before")
    @classmethod
    def _no_retired_fields(cls, data: Any) -> Any:
        """A retired key in a record is analyst prose about to vanish silently — refuse it."""
        if isinstance(data, dict):
            gone = sorted(RETIRED_VERDICT_FIELDS & set(data))
            if gone:
                raise ValueError(
                    f"verdict carries retired field(s) {', '.join(gone)} — the schema no longer "
                    "reads them, so a load-and-write would drop the words without saying so. "
                    "Move them somewhere that renders, or delete them deliberately.")
        return data

    @field_validator("entry_price")
    @classmethod
    def _entry_price_real(cls, v: float | None) -> float | None:
        """Absent is honest (no position); zero/negative is not. Every forward return in the
        spread is measured FROM this number — a 0.0 that slipped through would divide the whole
        track record by a price that never traded."""
        if v is not None and v <= 0:
            raise ValueError(f"entry_price {v} is not a traded price — refusing to record an "
                             "entry the forward spread cannot be measured from")
        return v


class RefreshEntry(BaseModel):
    """(record legibility, 2026-07-27) ONE machine data/spot refresh — what changed, old → new.

    THE POINT: a machine refresh is not an amendment to anyone's reasoning, and putting it in the
    sealed rationale made the audit trail read like argument. SMPL's 88-word "machine refresh on
    current data" tag is the specimen: it changed two numbers and cost a fifth of the record's
    prose. Refreshes now land HERE — structured, greppable, and machine-written by
    ``vinci scenario-refresh`` — while ``machine``-class tags are refused from the rationale
    outright (vinci/seal.py).

    Append-only by convention: entries are added, never edited. This log is NOT sealed — it is
    machine-generated fact, reproducible from the sources it names, not a record of judgment."""

    field: str            # dotted path into the record, e.g. "spot" / "facts.ltm_revenue"
    old: str              # rendered old value (str so ints/floats/None all round-trip legibly)
    new: str              # rendered new value
    date: str             # ISO date the refresh ran
    source: str           # WHERE the new value came from — the provenance, never bare "refresh"

    model_config = {"frozen": True}


class DatedTrigger(BaseModel):
    """(catalyst calendar, ratified 2026-07-24) An ANALYST-owned re-underwrite trigger with a
    deadline — the dated form of a ``reunderwrite_triggers`` entry ("Quest stalling two more
    quarters" → the print that closes the window). ANALYST-TYPED ONLY: the machine never invents a
    trigger or its date. The calendar renders these with the TRIGGER-DEADLINE basis; the monitor
    flags a passed deadline as "re-underwrite due" (a flag, never a machine action)."""

    trigger: str          # the falsifier, in the analyst's words
    deadline: str         # ISO date the window closes
    basis: str = ""       # optional: how the deadline was chosen ("second print after verdict")

    model_config = {"frozen": True}


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
    # A machine gate the human consciously overrode, and WHY. A gate that fired and was then
    # walked past leaves no trace otherwise — the record would read as though it never fired,
    # which is the one reading that makes the gate worthless. None == no gate was adjudicated.
    gate_adjudication: str | None = None
    # (R2) TIER — a property of the BUSINESS, not of the answer. "A" = contracted/recurring revenue,
    # gross-profitable, self-funded to breakeven; "B" = survival-gated or unproven unit economics.
    # It feeds CONFIDENCE at the verdict and deliberately does NOT move the bar: a lower bar for a
    # worse business is how a fund talks itself into one. None on R1 records.
    tier: str | None = None
    survival_input: SurvivalInput | None = None      # (R2) inputs to the gate; None on R1
    result: Result = Field(default_factory=Result)
    verdict: Verdict = Field(default_factory=Verdict)
    # (record legibility, 2026-07-27) machine data/spot refreshes, append-only. Written by
    # `vinci scenario-refresh`, never by hand and never into the rationale. Optional-with-default
    # so every legacy record round-trips byte-identical.
    refresh_log: list[RefreshEntry] = Field(default_factory=list)
    # --- SUPERSESSION (2026-07-27) -------------------------------------------------------------
    # A withdrawn or closed verdict can be REISSUED rather than amended forever. The outgoing
    # record is archived (sealed, still publicly rendered) and the two are linked BOTH ways, so a
    # reader can always walk from the live record back to what it replaced and forward again.
    # Archive key form: "<TICKER>-<underwrite_date>" (e.g. "SMPL-2026-07-21").
    #
    # WHY: SMPL's rationale reached 450 words of which 330 were amendment — three-quarters of it
    # construction-era PROCESS, not investment judgment. Amending further would have buried the
    # thesis deeper under its own maintenance history. A reissue gives the reader a clean current
    # record without deleting or rewriting one word of what was recorded before.
    supersedes: str | None = None        # archive key of the record THIS one replaces
    superseded_by: str | None = None     # archive key of the record that replaced THIS one

    @model_validator(mode="after")
    def _assumption_axes_guarded(self) -> ScenarioRecord:
        """Axes guard, both directions. Unknown axis for a KNOWN recipe → refuse at ANY version
        (a typo'd axis silently dropping from the render is data loss). Completeness (exactly
        the recipe's axes) binds FORWARD from schema 1.1 — 1.0 records predate the field and
        stay valid. An unknown recipe_id is unconstrained until it declares its axes."""
        axes = axes_for(self.recipe_id, self.multiple_basis)
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


    @model_validator(mode="after")
    def _survival_blocks_a_confirmed_buy(self) -> ScenarioRecord:
        """(R2) A survival FAIL BLOCKS ``verdict.status = "confirmed"``. The refusal binds on the
        RECORD, not on the runner, because the record is the durable artifact and the verdict is
        written by hand — a guard that lived only in the compute path would be walked straight past
        by an analyst editing JSON.

        An asymmetry computed on a company that runs out of money before its terminal year is not a
        cheap asymmetry, it is a wrong one, so the gate is not overridable by the arithmetic looking
        attractive. Every OTHER status stays reachable: "passed" and "watch" are exactly what a
        failing name should be able to receive, and the record still computes and prints in full."""
        surv = self.result.survival
        if surv and surv.status == "FAIL" and self.verdict.status == "confirmed":
            raise ValueError(
                "survival gate FAILED — refusing to record a confirmed BUY on a company that has "
                f"not been shown to reach its terminal year ({surv.note or 'see survival block'}). "
                "Record it as watch/passed, or clear the gate with a committed raise.")
        return self


RECIPE_R1 = "R1_midcycle_margin_evebitda"

# The assumption AXES each known recipe models. The axes guard binds per-recipe: unknown axes are
# refused for a known recipe at any schema version; completeness (all axes present) binds from
# schema 1.1. A future recipe declares its axes here when it exists — never speculatively.
RECIPE_R2 = "R2_terminal_margin"
AXES_BY_RECIPE: dict[str, tuple[str, ...]] = {
    RECIPE_R1: ("revenue", "margin", "multiple"),
    # R2 models the HORIZON as a fourth axis: when the terminal year arrives is an assumption in
    # its own right (it drives both the discount and the accumulated dilution), so it is stated and
    # reviewed like the other three rather than buried in the leg inputs.
    RECIPE_R2: ("revenue", "margin", "multiple", "horizon"),
}

# R2 on an EV/Revenue basis models THREE axes: the margin axis does not exist, because the value
# does not read a margin. Requiring a margin methodology here would force the analyst to write up
# how they derived an input the arithmetic ignores — a reviewable-looking paragraph attached to
# nothing, which is worse than no paragraph at all.
_R2_REVENUE_AXES: tuple[str, ...] = ("revenue", "multiple", "horizon")


def axes_for(recipe_id: str, multiple_basis: str | None) -> tuple[str, ...] | None:
    """The assumption axes a record must cover, given its recipe AND its multiple basis."""
    # lazy import: the basis constant lives in the engine, which imports back from here
    from vinci.dossier import terminal_margin as tmod

    if recipe_id == RECIPE_R2 and multiple_basis == tmod.BASIS_REVENUE:
        return _R2_REVENUE_AXES
    return AXES_BY_RECIPE.get(recipe_id)


def _run_r2(rec: ScenarioRecord) -> ScenarioRecord:
    """(R2) Compute ``result{}`` via the terminal-margin engine. The machine records the bar test
    and the gate; it does NOT touch ``verdict``.

    UNITS: ``net_debt``/``burn_to_breakeven`` in $M and ``diluted_shares`` in MILLIONS, matching the
    R1 record convention. The engine takes a RAW share count, so the conversion happens HERE, once,
    at the boundary — the two 1e6 defects found on 2026-07-21 both came from a scale applied in the
    wrong place, so there is exactly one in this path and it is named."""
    from vinci.dossier import midcycle as mc
    from vinci.dossier import terminal_margin as tmod

    if rec.multiple_basis not in (tmod.BASIS_EBITDA, tmod.BASIS_EBIT, tmod.BASIS_REVENUE):
        raise ValueError(f"record multiple_basis {rec.multiple_basis!r} is not an R2 basis — "
                         f"expected {tmod.BASIS_EBITDA!r}, {tmod.BASIS_EBIT!r} or "
                         f"{tmod.BASIS_REVENUE!r}")
    on_revenue = rec.multiple_basis == tmod.BASIS_REVENUE
    # d_and_a_ratio is required ONLY where it is read. Demanding it on an EV/Revenue record would
    # make the analyst source a number the arithmetic never touches — the same dead input the
    # engine refuses one layer down, wearing a fact's clothes. Carrying one is refused too.
    needed = ("net_debt", "diluted_shares", "share_growth")
    for key in needed if on_revenue else (*needed, "d_and_a_ratio"):
        if key not in rec.facts:
            raise ValueError(f"recipe {RECIPE_R2} needs fact {key!r} — refusing to assume it")
    if on_revenue and "d_and_a_ratio" in rec.facts:
        raise ValueError(
            f"recipe {RECIPE_R2} on basis {tmod.BASIS_REVENUE} carries a 'd_and_a_ratio' fact that "
            "no computation reads — omit it rather than record a driver the value never used")
    formula = tmod.formula_for(rec.multiple_basis)
    if rec.recipe_formula and rec.recipe_formula != list(formula):
        raise ValueError(f"record's recipe_formula does not match the {rec.multiple_basis} chain — "
                         "refusing to compute under a misstated recipe")
    si = rec.survival_input
    if si is None:
        raise ValueError(f"recipe {RECIPE_R2} needs survival_input — a terminal value on a company "
                         "whose runway is unstated cannot be underwritten")

    surv = tmod.survival_gate(
        fcf=si.fcf, fcf_basis=si.fcf_basis, fcf_source=si.fcf_source, cash=si.cash,
        facilities=si.facilities, facilities_source=si.facilities_source,
        years_to_breakeven=si.years_to_breakeven, announced_raise=si.announced_raise,
        raise_accession=si.raise_accession, going_concern_stated=si.going_concern_stated,
        going_concern_accession=si.going_concern_accession, burn_override=si.burn_override,
        burn_override_basis=si.burn_override_basis, latest_period_fcf=si.latest_period_fcf)
    # A BURNING company must state the cash it consumes on the way. Defaulting this to zero valued
    # the terminal year as though the burn were free: the survival block would read FAIL at 1.25y of
    # runway while the SAME record carried terminal net debt unchanged from today's balance sheet.
    # That is the exact direction of error R2 exists to prevent, and it applies to the whole cohort
    # by definition — they burn. The machine will not fill it in either (deriving burn × years would
    # be the machine proposing an assumption): the analyst states it, or the record refuses.
    burn_fact = rec.facts.get("burn_to_breakeven")
    if burn_fact is None and surv.burn:
        raise ValueError(
            f"recipe {RECIPE_R2} needs fact 'burn_to_breakeven' — the survival block shows a burn "
            f"of {surv.burn:,.1f} a year, so cash IS consumed before the terminal year and cannot "
            "be valued at zero. State the cumulative burn (0.0 only if it is genuinely nil).")
    net_debt = rec.facts["net_debt"].value - si.raise_proceeds
    shares_now = rec.facts["diluted_shares"].value * 1e6          # MILLIONS -> raw count
    per: dict[str, ScenarioOutcome] = {}
    for name, s in rec.scenarios.items():
        if s.years_to_terminal is None:
            raise ValueError(f"{name}: an R2 leg needs years_to_terminal — the horizon drives both "
                             "the discount and the accumulated dilution")
        v = tmod.terminal_value(
            tmod.TerminalLeg(name=name, years=s.years_to_terminal, revenue=s.revenue,
                             margin=s.margin, multiple=s.multiple, reason=s.reason),
            basis=rec.multiple_basis,
            d_and_a_ratio_=(None if on_revenue else rec.facts["d_and_a_ratio"].value),
            net_debt_now=net_debt, burn_to_breakeven=(burn_fact.value if burn_fact else 0.0),
            shares_now=shares_now, g_sbc=rec.facts["share_growth"].value,
            raise_shares=si.raise_shares * 1e6)
        per[name] = ScenarioOutcome(
            value_per_share=v.pv,                 # the PV IS what the ratio uses
            op_income=v.ebit_t, ebitda=v.ebitda_t, ev=v.ev_t, equity=v.equity_t,
            # EV/EBIT is a cross-check on the EBIT the value used; with no EBIT there is nothing
            # to cross-check, and inventing one from a revenue multiple would be circular.
            ev_ebit=(v.ev_t / v.ebit_t if v.ebit_t is not None and v.ebit_t > 0 else None),
            years=v.years, d_and_a_t=v.d_and_a_t, net_debt_t=v.net_debt_t,
            shares_t=v.shares_t / 1e6, value_terminal=v.value_t, hurdle=v.hurdle)

    sb = SurvivalBlock(
        status=surv.status, burn=surv.burn, burn_basis=surv.burn_basis,
        burn_source=surv.burn_source, cash=surv.cash, facilities=surv.facilities,
        facilities_source=surv.facilities_source, runway_years=surv.runway_years,
        years_to_breakeven=surv.years_to_breakeven, announced_raise=surv.announced_raise,
        raise_accession=surv.raise_accession, note=surv.note, detail=list(surv.detail))
    res = Result(per_scenario=per, bar=BAR, survival=sb, hurdle=tmod.HURDLE)
    if "base" in per and "bear" in per:
        rr = mc.reward_risk(base_vps=per["base"].value_per_share,
                            bear_vps=per["bear"].value_per_share, spot=rec.spot)
        res = Result(per_scenario=per, reward=rr.reward, risk=rr.risk, ratio=rr.ratio,
                     ratio_undefined=rr.undefined, bar=BAR, survival=sb, hurdle=tmod.HURDLE,
                     pass_fail=("UNDEFINED" if rr.ratio is None else
                                ("PASS" if rr.clears_bar else "FAIL")))
    return rec.model_copy(update={"result": res, "recipe_formula": list(formula)})


def run_recipe(rec: ScenarioRecord) -> ScenarioRecord:
    """Compute ``result{}`` for a record via the mid-cycle block, and return a NEW record with it.

    Recipe R1: revenue × margin → EBIT; + D&A → EBITDA; × multiple → EV; − net debt → equity ÷
    diluted shares. Reward/risk per the ratified convention (base−spot / spot−bear, bull excluded).
    Units: ``d_and_a``/``net_debt`` in $M, ``diluted_shares`` in MILLIONS → value/share in $.

    The machine records the bar test; it does NOT touch ``verdict``."""
    from vinci.dossier import midcycle as mc

    if rec.recipe_id == RECIPE_R2:
        return _run_r2(rec)
    if rec.recipe_id != RECIPE_R1:
        raise ValueError(f"unknown recipe_id {rec.recipe_id!r} — this runner implements "
                         f"{RECIPE_R1} and {RECIPE_R2}")
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
        # R1 IS a margin recipe — mid-cycle margin × own-history multiple. `margin` became
        # nullable for R2's EV/Revenue basis; on R1 an absent one has no meaning, so refuse here
        # rather than let a None reach the block as a silent zero.
        if s.margin is None:
            raise ValueError(f"{name}: recipe {RECIPE_R1} is a mid-cycle MARGIN recipe — a leg "
                             "without a margin cannot be computed")
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


class AdmissibilityWarning(UserWarning):
    """The bear leg may not describe a downside state. Printed, never blocking."""


def _require_bear_basis(rec: ScenarioRecord) -> None:
    """From schema 1.2 the BEAR leg states where its multiple came from and which line its margin
    is on. Legacy records predate the fields and stay writable — the rule binds forward.

    This one REFUSES rather than warns. The labels cost a word each and their absence is exactly
    what made the IT band defect and the EBITDA/EBIT mistranslation invisible; a warning would be
    read past on the day it mattered."""
    if _schema_ver(rec.schema_version) < _schema_ver(BASIS_REQUIRED_FROM):
        return
    bear = (rec.scenarios or {}).get("bear")
    if bear is None:
        return
    required = ["bear_basis"]
    # margin_basis is required only where a MARGIN EXISTS. An EV/Revenue record refuses a margin
    # outright (terminal_value raises on one), so demanding a label for it would make that basis
    # unwritable — the same dead-input argument that removed the margin axis from it in the first
    # place. A label for a number that cannot exist is not provenance, it is furniture.
    if bear.margin is not None:
        required.append("margin_basis")
    elif bear.margin_basis is not None:
        raise ValueError(
            f"{rec.ticker}: bear leg carries margin_basis={bear.margin_basis!r} but no margin — "
            "on a basis that reads no margin, labelling one states a line nothing sits on")
    missing = [f for f in required if getattr(bear, f, None) is None]
    if missing:
        raise ValueError(
            f"{rec.ticker}: bear leg is missing {missing} — schema {rec.schema_version} requires "
            f"the bear multiple's provenance ({sorted(BEAR_BASES)}) and the margin's earnings "
            f"line ({sorted(MARGIN_BASES)}). Both exist because both have already gone wrong.")


def _schema_ver(s: str) -> tuple[int, ...]:
    """Numeric version compare (shared by the forward-binding gates). String compare would read
    '1.10' < '1.2' as True and let a future record skip a rule — the silent-bypass class the
    versioned gates exist to close."""
    try:
        return tuple(int(x) for x in s.split("."))
    except ValueError:
        return (0,)


def require_fielded_refs(rec: ScenarioRecord) -> None:
    """(schema 1.3 — docs/refpoint_schema_proposal.md, ratified 2026-07-27) From 1.3 a reference's
    STRUCTURE lives in fields, and a label carrying it as prose is REFUSED with the field named.
    Legacy records predate the fields and stay writable — forward-binding, BASIS_REQUIRED_FROM
    precedent.

    REFUSES rather than warns, for the same reason bear_basis does: the prose forms already went
    wrong in production — uw-card's find(/median/i) showed the PEER median on MVST because which
    median a label named was decided by array order, and a whole finding was smuggled into a
    ``unit``. Public (not underscore) because the migration pin validates committed records
    through it directly."""
    if _schema_ver(rec.schema_version) < _schema_ver(FIELDED_REFS_FROM):
        return
    problems: list[str] = []
    for axis, a in (rec.assumptions or {}).items():
        for i, r in enumerate(a.references):
            where = f"assumptions.{axis}.references[{i}]"
            if _LEG_IN_LABEL.search(r.label):
                problems.append(f"{where}: label {r.label!r} names a leg — the leg belongs in "
                                "`leg=`, not the label")
            if _EXCLUSION_IN_LABEL.search(r.label):
                problems.append(f"{where}: label {r.label!r} carries an exclusion as prose — "
                                "use excluded=True + excluded_reason")
            if (_schema_ver(rec.schema_version) >= _schema_ver(VINTAGE_REQUIRED_FROM)
                    and not (r.vintage or "").strip()):
                problems.append(
                    f"{where}: no vintage — `source` names WHERE the value came from and never "
                    "WHEN. State the period it describes (a fiscal period or a date)")
            if r.unit not in REF_UNITS:
                problems.append(f"{where}: unit {r.unit!r} is not one of {sorted(REF_UNITS)} — "
                                "a unit is a unit; a finding belongs in the axis notes")
    if problems:
        raise ValueError(
            f"{rec.ticker}: schema {rec.schema_version} requires fielded references — "
            + "; ".join(problems[:4])
            + (f"; +{len(problems) - 4} more" if len(problems) > 4 else ""))


def _warn_admissibility(rec: ScenarioRecord) -> None:
    """Print the R1 admissibility flags at the moment a record is written or re-run.

    THE IT SIGNATURE CAN NEVER AGAIN PASS SILENTLY: a bear multiple above where the name trades
    today is a downside case that assumes a re-rating upward, and an own-history bear basis on a
    growth-era-only band is a floor that has never seen the state it is standing in for. Both were
    present in a recorded BUY and neither surfaced until an external review forced a re-underwrite.
    Warned, not blocked — the analyst may have a reason, and must be the one to state it."""
    bear = (rec.scenarios or {}).get("bear")
    if bear is None:
        return
    notes: list[str] = []
    if bear.bear_basis == "own-history":
        notes.append("bear_basis is 'own-history' — confirm the band contains a bear-state visit "
                     "(vinci audit r1)")
    if notes:
        warnings.warn(f"{rec.ticker}: " + "; ".join(notes), AdmissibilityWarning, stacklevel=3)


def write_record(rec: ScenarioRecord, *, root: Path | None = None) -> Path:
    """Persist to ``scenarios/<TICKER>.json`` — pretty + diff-able, so committed state reads.

    Prose is register-linted on the way out (:mod:`vinci.prose_lint`). The lint WARNS and never
    blocks: legacy records predate the register rule and must stay writable, and the linter never
    edits analyst words. The warning is the worklist surfacing at the moment it is cheapest to act
    on — while the record is open — rather than at a later audit.
    """
    d = records_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{rec.ticker.upper()}.json"
    _require_bear_basis(rec)
    require_fielded_refs(rec)
    _warn_admissibility(rec)
    flags = lint_record(rec)
    if flags:
        warnings.warn(
            f"{rec.ticker}: {len(flags)} prose-register flag(s) — "
            + "; ".join(str(f) for f in flags[:4])
            + (f"; +{len(flags) - 4} more" if len(flags) > 4 else ""),
            ProseRegisterWarning,
            stacklevel=2,
        )
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


# --- (record legibility, 2026-07-27) THE INSTRUMENTED REFRESH PATH -----------------------------
# Before this, `write_record()` had ZERO programmatic callers: every record edit in this repo's
# history was hand-edited JSON, including the 2026-07-24 SMPL machine refresh. That is why the
# refresh ended up narrated in the sealed rationale — there was nowhere else for it to go.
#
# `refresh_record` is now the ONE path for changing a record's MACHINE inputs. It recomputes the
# result through the engine, appends a structured `refresh_log` entry per field, and REFUSES to
# touch anything the analyst owns. The refusals are asserted, not documented: a refresh that
# silently moved a leg would be the machine overwriting judgment, which is the one thing the
# constitution forbids outright.
REFRESHABLE_FACTS = frozenset({"ltm_revenue", "d_and_a", "net_debt", "diluted_shares",
                               "cash_interest", "cash_tax_rate"})


class RefreshRefusedError(RuntimeError):
    """The refresh would have touched an analyst-owned surface. Raised, never warned."""


def refresh_record(
    rec: ScenarioRecord, *, spot: float | None = None,
    facts: dict[str, float | Fact] | None = None,
    source: str, on_date: str,
) -> ScenarioRecord:
    """Refresh MACHINE inputs on ``rec`` and return a NEW record with the result recomputed.

    ``spot`` and ``facts`` are the only things this may move. Every change is appended to
    ``refresh_log`` with its old → new value, the date, and the SOURCE it came from — provenance is
    required, because a refresh nobody can re-derive is just an untraceable edit.

    **A FACT VALUE MAY CARRY ITS BASIS (2026-07-31).** Pass a bare float to refresh the SAME
    quantity — the basis is unchanged, which is right for a re-read of the same line. Pass a
    :class:`Fact` when the refresh changes what the number IS, and the new ``basis``/``source`` move
    with it, each logged as its own entry.

    The first cut moved the value alone, so swapping ``diluted_shares`` from a weighted average to a
    point-in-time outstanding count would have left the string ``"diluted weighted-average (latest
    10-Q)"`` sitting over a number that is neither weighted nor an average. ``Fact.basis`` documents
    itself as naming WHAT the number is; a writer that moves the value and freezes the basis
    MANUFACTURES a mislabelled figure — the exact defect class the share-count work exists to close,
    inside the writer meant to close it.

    **A UNIT CHANGE IS REFUSED.** Basis is prose about the same quantity; unit is the quantity's
    scale, and silently re-scaling a denominator is how a per-share value becomes wrong by 1e6.

    REFUSES (raises :class:`RefreshRefusedError`) on any attempt to reach an analyst surface: a fact
    outside :data:`REFRESHABLE_FACTS`, or a fact the record does not already carry. The legs,
    assumptions, verdict and rationale are structurally unreachable from here — this function
    cannot express a change to them — and the caller-facing pins assert exactly that.
    """
    if not source.strip():
        raise RefreshRefusedError(
            "a refresh must state its SOURCE — an unattributable refresh is an untraceable edit")
    entries: list[RefreshEntry] = list(rec.refresh_log)
    updates: dict[str, Any] = {}

    if spot is not None and spot != rec.spot:
        entries.append(RefreshEntry(field="spot", old=str(rec.spot), new=str(spot),
                                    date=on_date, source=source))
        updates["spot"] = spot

    if facts:
        bad = sorted(set(facts) - REFRESHABLE_FACTS)
        if bad:
            raise RefreshRefusedError(
                f"{bad} is not a refreshable machine fact — refreshable: "
                f"{sorted(REFRESHABLE_FACTS)}. Analyst-owned inputs are changed by re-underwriting,"
                " never by a refresh")
        missing = sorted(k for k in facts if k not in rec.facts)
        if missing:
            raise RefreshRefusedError(
                f"{missing} is not on this record — a refresh UPDATES a fact the analyst already "
                "recorded; it never introduces one")
        new_facts = dict(rec.facts)
        for k, v in facts.items():
            old = rec.facts[k]
            new_value = v.value if isinstance(v, Fact) else v
            if isinstance(v, Fact) and v.unit != old.unit:
                raise RefreshRefusedError(
                    f"facts.{k}: a refresh may restate the BASIS but never the UNIT "
                    f"({old.unit!r} → {v.unit!r}) — a silent re-scale of a denominator is how a "
                    "per-share value goes wrong by a factor of a million. Re-underwrite instead")
            restated = v if isinstance(v, Fact) and (
                v.basis != old.basis or v.source != old.source) else None
            if new_value == old.value and restated is None:
                continue
            if new_value != old.value:
                entries.append(RefreshEntry(field=f"facts.{k}", old=str(old.value),
                                            new=str(new_value), date=on_date, source=source))
            if restated is not None:
                # ONE ENTRY PER FIELD THAT ACTUALLY MOVED (review finding). The first cut logged a
                # `.basis` entry whenever EITHER basis or source changed, so a source-only
                # restatement wrote an entry whose `old` and `new` were the SAME string — a log
                # claiming a change that did not happen, in the record whose whole job is to say
                # what changed. `test_refresh_moves_machine_inputs_and_logs_provenance` already
                # asserts `e.old != e.new` on refresh entries; this violated the file's own rule.
                for field, was, now in (("basis", old.basis, restated.basis),
                                        ("source", old.source, restated.source)):
                    if was != now:
                        # a number that keeps its value while changing MEANING is exactly the move
                        # a value-diff cannot show, so it gets its own line either way
                        entries.append(RefreshEntry(field=f"facts.{k}.{field}", old=was, new=now,
                                                    date=on_date, source=source))
                new_facts[k] = old.model_copy(update={
                    "value": new_value, "basis": restated.basis, "source": restated.source})
            else:
                new_facts[k] = old.model_copy(update={"value": new_value})
        updates["facts"] = new_facts

    if not entries[len(rec.refresh_log):]:
        return rec                      # nothing actually moved — no entry, no rewrite
    updates["refresh_log"] = entries
    out = run_recipe(rec.model_copy(update=updates))

    # The refusals, ASSERTED on the way out — cheap, and they turn a future refactor that widened
    # this function's reach into a loud failure instead of a silent overwrite of judgment.
    if out.verdict != rec.verdict:
        raise RefreshRefusedError("a refresh moved the VERDICT — refusing to write")
    if out.scenarios != rec.scenarios:
        raise RefreshRefusedError("a refresh moved a SCENARIO LEG — refusing to write")
    if out.assumptions != rec.assumptions:
        raise RefreshRefusedError("a refresh moved an ASSUMPTION — refusing to write")
    return out


# --- SUPERSESSION: archive-and-reissue (2026-07-27) --------------------------------------------
# THE PROBLEM IT SOLVES. A verdict that is withdrawn or closed keeps accreting amendment tags, and
# past some point the audit trail is longer than the thesis: SMPL reached 450 words of which 330
# were amendment, three-quarters of that construction-era process rather than investment judgment.
# The seal (rightly) forbids editing any of it. So the only honest way to give a reader a clean
# current record is to REISSUE — archive the outgoing record intact, write a fresh one, and link
# them both ways so nothing is hidden and nothing is rewritten.
#
# ARCHIVED RECORDS STAY PUBLIC. They render, they are indexed, and they remain in the seal sweep.
# What they leave is the LIVE set: the audit, the monitor and the spread read live records only,
# so an archived record can never be counted twice or scored a second time.
ARCHIVE_DIRNAME = "archive"


class SupersedeRefusedError(RuntimeError):
    """The supersession would break an invariant. Raised, never warned."""


def archive_key(rec: ScenarioRecord) -> str:
    """``<TICKER>-<underwrite_date>`` — stable, human-readable, and unique per underwrite."""
    return f"{rec.ticker.upper()}-{rec.underwrite_date}"


def archive_dir(root: Path | None = None) -> Path:
    return records_dir(root) / ARCHIVE_DIRNAME


def read_archived(key: str, *, root: Path | None = None) -> ScenarioRecord:
    return ScenarioRecord.model_validate_json((archive_dir(root) / f"{key}.json").read_text())


def all_archived(*, root: Path | None = None) -> dict[str, ScenarioRecord]:
    """Every ARCHIVED record, keyed by archive key. Separate from :func:`all_records` on purpose —
    ``all_records`` globs the records dir NON-recursively, so archived records are already outside
    the live set for every consumer that reads it (audit, monitor, spread). This function is the
    deliberate way in, used by the renderer and the seal sweep."""
    d = archive_dir(root)
    if not d.is_dir():
        return {}
    out: dict[str, ScenarioRecord] = {}
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("_"):
            continue
        out[p.stem] = ScenarioRecord.model_validate_json(p.read_text())
    return out


def supersede_record(
    outgoing: ScenarioRecord, incoming: ScenarioRecord, *,
    closed_entry_ids: set[str] | None = None, live_confirmed_open: bool = False,
) -> tuple[ScenarioRecord, ScenarioRecord]:
    """Return ``(archived, live)`` — the pointer-linked pair. Pure: writes nothing.

    REFUSALS, each one an invariant rather than a preference:
      * a LIVE position is never superseded (confirmed status with no close row) — that record is
        amended, because superseding it would move the thesis out from under an open position;
      * the incoming record must be the same ticker (a supersession is a reissue, not a swap);
      * the incoming record must not already point somewhere else;
      * the archived copy's SEALED TEXT must be byte-identical to the outgoing record's — the
        whole point is that archiving alters nothing that was recorded.
    """
    if outgoing.ticker.upper() != incoming.ticker.upper():
        raise SupersedeRefusedError(
            f"ticker mismatch: {outgoing.ticker} -> {incoming.ticker}; a supersession reissues the "
            "SAME name's record")
    if live_confirmed_open:
        raise SupersedeRefusedError(
            f"{outgoing.ticker} is a LIVE position (verdict {outgoing.verdict.status!r} with no "
            "close row) — a live position is AMENDED, never superseded: reissuing would move the "
            "thesis out from under an open position")
    if incoming.supersedes not in (None, archive_key(outgoing)):
        raise SupersedeRefusedError(
            f"incoming record already points at {incoming.supersedes!r}, not "
            f"{archive_key(outgoing)!r}")
    key = archive_key(outgoing)
    archived = outgoing.model_copy(update={"superseded_by": archive_key(incoming)})
    live = incoming.model_copy(update={"supersedes": key, "superseded_by": None})
    # the guarantee, asserted rather than documented: archiving edits NOTHING that was recorded
    if archived.verdict.rationale != outgoing.verdict.rationale:
        raise SupersedeRefusedError(
            "archived rationale differs from the outgoing record — refusing")
    if archived.model_dump(exclude={"superseded_by"}) != outgoing.model_dump(
            exclude={"superseded_by"}):
        raise SupersedeRefusedError(
            "the archived copy differs from the outgoing record beyond its superseded_by pointer")
    if not live.supersedes or not archived.superseded_by:
        raise SupersedeRefusedError("both pointers are required — refusing a one-way link")
    if closed_entry_ids is not None and outgoing.verdict.status == "confirmed" \
            and not closed_entry_ids:
        raise SupersedeRefusedError(
            f"{outgoing.ticker}: confirmed verdict with no close row in the ledger")
    return archived, live


def write_archived(rec: ScenarioRecord, *, root: Path | None = None) -> Path:
    """Persist an archived record. Same serialization as :func:`write_record` so the two stay
    diff-able; no lint warning — an archived record is history, not a worklist."""
    d = archive_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{archive_key(rec)}.json"
    path.write_text(rec.model_dump_json(indent=2) + "\n")
    return path
