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
    """Multiples: the CROSS-SECTIONAL read (vs peers) LEADS; own-history range/percentile is
    secondary — near-tautological post-drawdown, so it barely discriminates. CIQ multiples + G3."""

    # The cross-sectional read (the fund's edge): where the name's multiples sit vs the PEER
    # cross-section, NOT its own history. The screen selects drawdowns, so almost every finalist is
    # at its OWN-history floor (~0th %ile) — a near-constant, non-discriminating metric; the
    # cross-section is what varies across finalists and carries the signal. Leads the render.
    cross_sectional: Sourced[str]
    pe: Sourced[float]
    pe_percentile_5y: Sourced[float]
    ev_ebitda: Sourced[float]  # GAAP TEV/LTM EBITDA (CIQ, trailing)
    ev_ebitda_percentile_5y: Sourced[float]
    ev_ebitda_adjusted_fwd: Sourced[str]  # forward EV / FY-guide adjusted EBITDA (alongside GAAP)
    adjusted_eps: Sourced[str]  # company-adjusted EPS from the 99.1 guide (earnings power, vs GAAP)
    # own-history: current multiple + trailing low–median–high RANGE + sample-size CONFIDENCE (a
    # floor read on a handful of quarterly closes is unreliable — see range_position).
    range_position: Sourced[str]

    model_config = {"frozen": True}


class Quality(BaseModel):
    """Durability: cash generation, margins, leverage, dilution, liquidity/covenant flags."""

    fcf_sign: Sourced[int]
    free_cash_flow: Sourced[float]
    margin_trend: Sourced[str]  # margin % PAIRED with the absolute EBITDA/revenue reconciler
    net_debt_to_ebitda: Sourced[float]  # GAAP consolidated EBITDA basis
    net_debt_to_ocf: Sourced[float]  # OCF basis — leverage read that survives untaggable D&A
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


class RevisionEvent(BaseModel):
    """One CIQ Estimates→Recent-Changes row: a dated broker revision. A RECORDED event — the only
    direction it carries is CIQ's own verbatim ``change_type`` label; the machine adds no reading.
    Every field is a string (verbatim cell text, ``-`` when absent) so a missing broker value can
    never become a fabricated number."""

    date: str  # ISO, decoded from the Excel serial
    change_type: str  # CIQ's own verbatim label, e.g. "Downward Revision", "Initiation of Coverage"
    broker: str
    metric: str  # CIQ "Data Point", e.g. "EBITDA", "EPS Normalized"
    period: str  # e.g. "FY 2026", "FQ2 2026"
    broker_prior: str  # the broker's prior value ("-" if a new estimate)
    broker_current: str  # the broker's revised value
    consensus_before: str
    consensus_after: str

    model_config = {"frozen": True}


class CatalystPath(BaseModel):
    """Horizon-matched estimates / guidance / revision-event view (CIQ Estimates: Revisions, Trends,
    Guidance, Multiples, Recent-Changes, Consensus). The Edge-2 revision-breadth evidence ASSEMBLED
    and source-bound in NATIVE-CADENCE blocks — FQ horizon, monthly acceleration path, NTM anchor —
    never concluded: no field holds a computed upside / fair value / attractiveness / direction; the
    human reads the path and judges. ``as_of`` (the freshest embedded data date) threads into every
    sub-field's source_ref and fires the shared staleness caveat vs the reference date. Each field
    reads UNKNOWN/MISSING when its sheet/rows are absent — ragged by design, never faked."""

    as_of: Sourced[str]  # workbook as-of date (ISO) — the freshest embedded data date
    horizon_read: Sourced[str]  # a. FQ: next-2-FQ levels + 1/2/3-month revision breadth per metric
    acceleration_read: Sourced[str]  # b. monthly path from Trends; deltas between present snapshots
    cross_name_anchor: Sourced[str]  # c. NTM level + forward-multiple ladder (NTM + FY26→FY33)
    guidance_bridge: Sourced[str]  # d. latest guide {range,date} + consensus + actual + track-rec
    revision_events: Sourced[list[RevisionEvent]]  # e. Recent-Changes log; render caps 10, JSON all
    consensus_stats: Sourced[str]  # f. target mean/median/hi-lo/N + rating distribution

    model_config = {"frozen": True}


class PeerRow(BaseModel):
    """One row of the per-peer comparability grid (B1) — a peer, the subject (``is_name``), or the
    synthetic peer-median footer (``is_median``). Every figure is CIQ-sourced; NO computed
    delta/discount/upside field — the human compares the name row against the peers + median."""

    name: str
    ticker: str  # parsed EXCH:SYMBOL tail, or "" (undisclosed / no paren)
    is_name: bool = False  # the subject — rendered visually distinct
    is_median: bool = False  # the peer-median footer row
    market_cap: float | None = None  # $M
    ebitda_margin: float | None = None  # fraction
    rev_growth_1y: float | None = None  # fraction
    ebitda_growth_1y: float | None = None  # fraction
    debt_to_ebitda: str | None = None  # total-debt basis; "NM" preserved, numeric kept as string
    net_debt: float | None = None  # $M

    model_config = {"frozen": True}


class LeverageSurvival(BaseModel):
    """Unified leverage & survival (B2) — ONE block, two LABELED bases, NO basis-mixing (retires the
    net-vs-total 3.9x/5.8x incoherence). The name's CIQ NET-debt/EBITDA AND the comps TOTAL-debt/
    EBITDA (with the peer median on the SAME total basis) sit side by side, each basis named; plus
    interest coverage, the survival line, and the S&P-MI credit-health scores (scale labeled)."""

    net_debt_to_ebitda: Sourced[float]  # name, CIQ NET basis
    total_debt_to_ebitda: Sourced[str]  # name vs peer median, comps TOTAL basis (both labeled)
    interest_coverage: Sourced[float]
    survival: Sourced[str]  # FCF sign + nearest refinancing wall
    credit_health: Sourced[str]  # name vs peer S&P-MI PD scores; scale labeled (1=strongest…4)

    model_config = {"frozen": True}


class ImpliedRow(BaseModel):
    """One CIQ-computed implied-EQUITY row (a valuation basis × Low/Median/Mean/High). Third-party
    (CIQ) output — NOT a machine conclusion; NO discount/upside field."""

    basis: str  # "LTM EBITDA", "NTM Revenue", …
    low: float | None = None
    median: float | None = None
    mean: float | None = None
    high: float | None = None

    model_config = {"frozen": True}


class ImpliedValuation(BaseModel):
    """CIQ's Implied-Valuation sheet (B3), POSED not concluded: the implied EQUITY value at peer
    multiples (basis × Low/Median/Mean/High) + the TEV→equity bridge + the name's ACTUAL market cap
    ADJACENT, for the human to compare. HARD FENCE: no computed %, delta, discount, or upside —
    anywhere. The heterogeneity comparability gate renders verbatim on the header."""

    implied_equity: Sourced[list[ImpliedRow]]  # CIQ-computed implied equity value per basis × stat
    bridge: Sourced[str]  # + cash, − total debt (TEV → equity), CIQ figures
    market_cap: Sourced[float]  # the name's ACTUAL market cap (adjacent, $M) — the human compares
    comparability_gate: Sourced[str]  # the heterogeneity gate, rendered verbatim on the header

    model_config = {"frozen": True}


class PeerComps(BaseModel):
    """Comparable-company multiples FRAMED to RESIST the consensus comp read (CIQ Company Comparable
    Analysis). The peer-vs-name gap is never presentable without (a) the peer-set COMPOSITION — so
    the human judges comparability and can mentally re-draw the thesis-correct set — and (b) the
    fundamental DELTAS — so the discount is judged EARNED (value-trap) vs RESIDUAL (overshoot). The
    machine assembles + POSES the justified-vs-residual question; it NEVER re-draws the set,
    computes a residual, or emits an implied upside."""

    peer_set: Sourced[str]  # roster: each peer's name + market cap + short business + HQ country
    comparability: Sourced[str]  # CONFIDENCE GATE: market-cap + business-model dispersion
    trading_multiples: Sourced[str]  # name's multiples vs peer High/Low/Mean/Median (LTM + NTM fwd)
    fundamental_deltas: Sourced[str]  # name vs peer median: growth / margin / leverage / beta
    # B1 per-peer grid (rows + name + median footer). Optional-with-default for back-compat: a
    # dossier.json predating B1 round-trips; a FRESH assembly always builds it. The median-only
    # fundamental_deltas line above is retained (synthesis input) but the RENDER prefers this grid.
    peer_grid: Sourced[list[PeerRow]] | None = None

    model_config = {"frozen": True}


class MechanicalLayer(BaseModel):
    """The deterministic, source-bound facts — the ONLY input the synthesis LLM is given."""

    valuation: Valuation
    quality: Quality
    concentration: Concentration
    peer_comps: PeerComps  # comparable-company multiples + composition + deltas (consensus-resist)
    drawdown_cause: DrawdownCause
    idiosyncratic_vs_shared: IdiosyncraticVsShared
    consensus_context: ConsensusContext
    # Horizon-matched estimates/guidance/revision-event view (the five previously-unparsed CIQ
    # Estimates sheets). Optional-with-default ONLY for back-compat: a dossier.json predating this
    # field must still round-trip (the flags-PR precedent). A FRESH assembly ALWAYS builds it — the
    # fail-loud lives one level down (each sub-field is UNKNOWN/MISSING when its sheet is absent).
    catalyst_path: CatalystPath | None = None
    # B2 unified leverage & survival (both bases labeled + peer median + credit health) and B3 CIQ
    # implied valuation (posed, no computed %). Optional-with-default for back-compat: old JSON
    # round-trips (its Quality leverage lines render as the fallback); a FRESH assembly builds both.
    leverage_survival: LeverageSurvival | None = None
    implied_valuation: ImpliedValuation | None = None
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
    # Human-review flags split by audience (see vinci.dossier.flags): decision CAVEATS render in the
    # human PDF/web view (re-voiced, incl. the "pull CIQ …" incomplete-input notes); qa_flags are
    # the machine self-checks (citation/twin/overstep/LLM-state) — dev/JSON only, out of human view.
    # Default empty: a flag-free dossier is a valid state, and it lets the schema round-trip
    # JSON predating the audience split. (Analytical fields like cross_sectional stay REQUIRED —
    # a missing computed value must fail loud, never silently default.)
    caveats: list[str] = []
    qa_flags: list[str] = []
    llm_model: str | None
    assembled_at: datetime

    model_config = {"frozen": True}
