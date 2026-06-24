"""Dossier schemas — the **assemble-not-conclude** contract, enforced by STRUCTURE.

The synthesis output has NO field for a verdict, recommendation, direction, score, rating, or
probability. The LLM cannot conclude because there is nowhere to put a conclusion — the same
discipline as the ranker's no-forward-returns guard, held by structure rather than convention
(``tests/test_dossier.py`` asserts the absence). The human reads the dossier and logs BUY/AVOID with
a frozen entry price separately, via the append-only ledger CLI; logging stays a human act, and this
module imports nothing from ``vinci.ledger`` / ``vinci.scoring`` to keep that line structural too.

Every mechanical fact is a :class:`Sourced` ``{value, source_ref}`` — bound to a specific primary
source so the human verifies the datum, not the summary. A field that could not be found is
``UNKNOWN``; a whole absent source (e.g. an un-pulled CIQ export) is ``MISSING``. Never fabricated.
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar("T")


class SourceStatus(enum.StrEnum):
    """Coverage of one mechanical fact."""

    PRESENT = "present"  # found, bound to a source_ref
    UNKNOWN = "unknown"  # looked for, not found — fail-loud, never a guessed number
    MISSING = "missing"  # the whole source is absent (e.g. CIQ export not pulled for this name)


class Sourced(BaseModel, Generic[T]):
    """One mechanical fact: a value bound to a specific ``source_ref`` — or UNKNOWN/MISSING.

    Contract (validated): PRESENT ⇒ ``value`` and ``source_ref`` are both set; UNKNOWN/MISSING ⇒
    ``value`` is None (an unknown that carried a number would be a silent impute). Construct via the
    classmethods so the contract can't be broken by accident.
    """

    value: T | None = None
    source_ref: str | None = None
    status: SourceStatus = SourceStatus.UNKNOWN
    note: str | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _contract(self) -> Sourced[T]:
        if self.status is SourceStatus.PRESENT:
            if self.value is None or not self.source_ref:
                raise ValueError("PRESENT fact must carry both a value and a source_ref")
        elif self.value is not None:
            raise ValueError(f"{self.status.value} fact must carry no value (would be fabrication)")
        return self

    @classmethod
    def present(cls, value: T, *, source_ref: str, note: str | None = None) -> Sourced[T]:
        return cls(value=value, source_ref=source_ref, status=SourceStatus.PRESENT, note=note)

    @classmethod
    def unknown(cls, *, note: str) -> Sourced[T]:
        return cls(value=None, source_ref=None, status=SourceStatus.UNKNOWN, note=note)

    @classmethod
    def missing(cls, *, note: str) -> Sourced[T]:
        return cls(value=None, source_ref=None, status=SourceStatus.MISSING, note=note)


# --- mechanical layer (deterministic, no LLM; every field source-bound) -----------------------


class FilingRef(BaseModel):
    """One EDGAR 8-K bound to a specific gap-down — the primary source for the de-rating cause.

    ``item_types`` maps the 8-K's codes to their standard titles (so the cause is read from the
    codes, not blanket-labelled "earnings"); ``events`` is the source-bound catalyst parsed from the
    filing's own text (customer/contract/executive action), or an UNKNOWN read-by-hand marker."""

    gap_date: str  # the gap-down this 8-K explains
    filing_date: str
    form: str
    items: list[str]  # 8-K item codes, e.g. ["2.02", "9.01"]
    item_types: list[str]  # code → title, e.g. "5.02 Departure/Election of Directors or Officers"
    accession: str
    url: str
    events: list[str]  # per-item catalyst from the body, or "UNKNOWN — read <acc> by hand"

    model_config = {"frozen": True}


class CohortMember(BaseModel):
    """One graph-exposed name's return over the same window (idiosyncratic-vs-shared input)."""

    ticker: str
    hops: int
    ret_180d: float | None  # None when the name's bars don't cover the window (flagged in note)
    via: str  # provenance path from the graph (e.g. "FUBO —customer→ X")

    model_config = {"frozen": True}


class Valuation(BaseModel):
    """Multiples vs the name's own ~5y history + where in that range (G3 inputs + CIQ multiples)."""

    pe: Sourced[float]
    pe_percentile_5y: Sourced[float]
    ev_ebitda: Sourced[float]  # GAAP TEV/LTM EBITDA (CIQ, trailing)
    ev_ebitda_percentile_5y: Sourced[float]
    ev_ebitda_adjusted_fwd: Sourced[str]  # forward EV / FY-guide adjusted EBITDA (alongside GAAP)
    adjusted_eps: Sourced[str]  # company-adjusted EPS from the 99.1 guide (earnings power, vs GAAP)
    range_position: Sourced[str]  # near-floor / below-center / above-center / near-ceiling

    model_config = {"frozen": True}


class Quality(BaseModel):
    """Durability: cash generation, margins, leverage, dilution, liquidity/covenant flags."""

    fcf_sign: Sourced[int]
    free_cash_flow: Sourced[float]
    margin_trend: Sourced[str]  # margin % PAIRED with the absolute EBITDA/revenue reconciler
    net_debt_to_ebitda: Sourced[float]  # GAAP consolidated EBITDA basis
    net_debt_to_ebitda_adjusted: Sourced[str]  # covenant basis: net debt / FY-guide adjusted EBITDA
    # Solvency as ONE block (leverage + self-funding + nearest refinancing wall) so survival isn't
    # read as one metric among many; any leg UNKNOWN is itself a risk (opacity-as-signal).
    survival_capacity: Sourced[str]
    interest_coverage: Sourced[float]
    share_count_trend: Sourced[str]
    liquidity_covenant_flags: Sourced[str]
    multi_year_trajectory: Sourced[str]  # 5y arc of revenue/EBITDA/segment-EBITDA/ROIC (per period)

    model_config = {"frozen": True}


class Concentration(BaseModel):
    """Segment / customer / geographic concentration (CIQ Segments + Customers & Suppliers).

    Segment exposure is carried on BOTH bases: ``segments`` (revenue share) and ``segment_ebitda``
    (EBITDA share). The profit view is the decision-relevant one — a customer can sit in a segment
    that is a small slice of revenue but a large slice of EBITDA."""

    segments: Sourced[str]  # revenue share
    segment_ebitda: Sourced[str]  # EBITDA share — where the profit (and the customer risk) sits
    customers: Sourced[str]
    geographic: Sourced[str]

    model_config = {"frozen": True}


class DrawdownCause(BaseModel):
    """Why the name fell: shape (discrete event vs gradual bleed) + the 8-Ks at the gap-downs."""

    shape: Sourced[str]  # "discrete event" vs "gradual bleed" — from the gap-down detector
    gap_down_dates: Sourced[list[str]]
    filings: list[FilingRef]  # 8-Ks bound to the gap-down dates (the cause, source-bound)
    revised_guidance: Sourced[str]  # revised FY outlook from the catalyst 8-K's Ex-99.1

    model_config = {"frozen": True}


class IdiosyncraticVsShared(BaseModel):
    """Did the name fall alone (idiosyncratic) or with its graph cohort (shared/thematic)?

    The G2-vs-market compensation: G2 only strips market beta; here we pull the graph-exposed
    cross-section and compare each name's return over the same window. Graph is INPUT, never a
    predictor — ``cohort`` is UNKNOWN when the name isn't in the graph (fail-loud, not fabricated).
    """

    name_180d_return: Sourced[float]
    market_180d_return: Sourced[float]  # IWM — the G2 benchmark
    rel_vs_market: Sourced[float]  # name − IWM (the G2 number)
    cohort: Sourced[list[CohortMember]]
    read: Sourced[str]  # "fell alone (idiosyncratic)" vs "fell with cohort (shared/thematic)"

    model_config = {"frozen": True}


class ConsensusContext(BaseModel):
    """Light consensus context (CIQ Estimates) — context for 'am I non-consensus', not a driver."""

    eps_trend: Sourced[str]
    revenue_trend: Sourced[str]
    revision_history: Sourced[str]
    surprise_history: Sourced[str]  # annual estimate beat/miss (Estimates→Surprise)

    model_config = {"frozen": True}


class MechanicalLayer(BaseModel):
    """The deterministic, source-bound facts — the ONLY input the synthesis LLM is given."""

    valuation: Valuation
    quality: Quality
    concentration: Concentration
    drawdown_cause: DrawdownCause
    idiosyncratic_vs_shared: IdiosyncraticVsShared
    consensus_context: ConsensusContext
    management_commentary: Sourced[str]  # earnings-call transcript — QUALITATIVE only, no numbers

    model_config = {"frozen": True}


# --- synthesis layer (LLM, fenced; NO verdict/score/direction/probability field) --------------


class SourcedPoint(BaseModel):
    """A bull or bear point. MUST cite a ``source_ref`` that exists in the mechanical layer.

    ``cited`` is set False by the post-LLM validator when the cited ref does not trace to input —
    an uncited claim is flagged for the human, never silently presented as established."""

    claim: str
    source_ref: str
    cited: bool = True  # validator flips to False (and flags) if source_ref doesn't trace

    model_config = {"frozen": True}


class TwinCase(BaseModel):
    """A specific NAMED historical de-rating analogue, for the human to reason about by analogy.

    Source-bound or tagged ``[LLM-suggested, unverified]``; never numeric (no recovery rate, base
    rate, or probability — analogues inform reasoning, they do not compute an aggregate)."""

    name: str
    outcome: str  # one line: "recovered …" / "went terminal …"
    distinguishing_fact: str  # the source-bound fact that separated it
    source: str  # a source_ref OR the literal "[LLM-suggested, unverified]"

    model_config = {"frozen": True}


class DecisiveQuestion(BaseModel):
    """The single variable the call hinges on — evidence on each side, NOT answered."""

    question: str
    evidence_for: list[SourcedPoint]
    evidence_against: list[SourcedPoint]

    model_config = {"frozen": True}


class Synthesis(BaseModel):
    """The fenced LLM output. NO verdict / recommendation / direction / score / rating / probability
    field exists — the assemble-not-conclude line, structural. The two cases are framing for the
    human (exaggerated/temporary overshoot vs secular/terminal decline), not a conclusion."""

    # A committed, possibly-LOPSIDED balance read — a one-sided reality must NOT be laundered into a
    # symmetric bull/bear list. Required of the LLM (tool schema); "" default only tolerates legacy.
    evidence_balance: str = ""
    bull_points: list[SourcedPoint]  # the overshoot case
    bear_points: list[SourcedPoint]  # the terminal-decline case
    twin_reference_cases: list[TwinCase]
    decisive_question: DecisiveQuestion
    key_unknowns: list[str]

    model_config = {"frozen": True}


class Dossier(BaseModel):
    """A per-finalist dossier: source-bound mechanical facts + fenced synthesis. Assembles, cites;
    never concludes. The human's BUY/AVOID verdict is logged separately via the ledger CLI."""

    ticker: str
    name: str
    cik: str
    reference_date: date
    rank: int | None  # position in the ranked queue — ordering context, never a verdict on the name
    mechanical: MechanicalLayer
    synthesis: Synthesis | None  # None if CIQ/inputs too thin or the synthesis was skipped
    flags: list[str]  # e.g. "pull CIQ for FUBO and re-run", lint flags for human review
    llm_model: str | None
    assembled_at: datetime

    model_config = {"frozen": True}
