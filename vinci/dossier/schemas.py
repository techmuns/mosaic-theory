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
from collections.abc import Callable
from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator, model_serializer, model_validator

from vinci.dossier.anchor import Anchor
from vinci.dossier.midcycle import MidCycle
from vinci.sleeves import DEFAULT_SLEEVE, UnknownSleeveError, require_sleeve

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
    def unknown(cls, *, note: str, source_ref: str | None = None) -> Sourced[T]:
        """``source_ref`` is OPTIONAL and means "we looked HERE and it held nothing" — reserved for
        an unknown whose note makes a CLAIM about the source (a view that states its own emptiness),
        so the human can open the file and check it rather than trust the note. An unknown that is
        merely a failure leaves it None: there is no cell to point at."""
        return cls(value=None, source_ref=source_ref, status=SourceStatus.UNKNOWN, note=note)

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
    # (B1) the parsed EX-99.1 drivers joined by accession — WHAT the results showed (adjusted
    # EBITDA/NI/EPS + one-offs + forward outlook), the informative cause that replaces the item-code
    # boilerplate. None until the join runs, or when no parsed release matched the gap's 8-K.
    drivers: Sourced[str] | None = None
    # Does this 8-K carry any item that could plausibly cause the gap? An administrative-only filing
    # (a 5.07 annual-meeting vote, a bylaw amendment) does NOT explain a de-rating — the shape line
    # reads "no earnings/guidance filing" and the What-broke surface suppresses its card, but the
    # filing ref STAYS in JSON (fact preserved, three-tier rule). Defaults True so pre-flag
    # committed dossiers keep rendering their cards until re-assembled.
    explanatory: bool = True

    model_config = {"frozen": True}


class CohortMember(BaseModel):
    """One graph-exposed name's return over the same window (idiosyncratic-vs-shared input)."""

    ticker: str
    hops: int
    ret_180d: float | None  # None when the name's bars don't cover the window (flagged in note)
    via: str  # provenance path from the graph (e.g. "FUBO —customer→ X")

    model_config = {"frozen": True}


class ImpliedExpectationRow(BaseModel):
    """(G) One row: a STATED multiple → the fundamental LEVEL price implies at it (implied_level =
    TEV ÷ multiple). FUNDAMENTALS-SPACE ONLY — this model carries NO price/equity/value/upside/
    discount field (the block-scoped no-conclusion check forbids those tokens). ``implied_level``
    is a metric level in $M (EBITDA or revenue), NEVER a per-share price or an equity value; it is
    UNKNOWN (with a ``note`` reason) when the multiple is NM / negative / absent. No % or gap — the
    consensus anchors are juxtaposed by the container, never differenced."""

    label: str  # e.g. "name NTM TEV/EBITDA"
    metric: str  # "EBITDA" | "Revenue" — the fundamental axis
    multiple: float | None  # the stated multiple used (x); None when NM/absent
    multiple_source: str  # the source_ref the multiple was cross-referenced from
    implied_level: float | None  # TEV ÷ multiple, $M of the metric; None ⇒ UNKNOWN (see note)
    is_identity: bool = False  # the name's own NTM multiple — implied_level ≡ consensus
    note: str | None = None  # the reason implied_level is UNKNOWN (guarded division / NM multiple)

    model_config = {"frozen": True}


class ImpliedExpectations(BaseModel):
    """(G) Price-inverted expectations, MULTIPLES-space. At a FIXED, declared multiple set the block
    reports the fundamental LEVEL price implies (``TEV ÷ multiple``), juxtaposed with the consensus
    path anchors — NEVER differenced (no %, gap, upside, or implied price/equity). The human judges
    earned-vs-residual. TEV is DERIVED from already-sourced Financial-Data fields (simple-TEV basis:
    mcap + net debt [+ pref + minority when surfaced]), and vintage-coherence-gated against the
    multiples sheet so a TEV / multiples pricing-vintage mismatch can't ship silently (G5)."""

    rows: list[ImpliedExpectationRow]
    tev: Sourced[float]  # the derived TEV; source_ref states the simple-TEV formula + inputs' as-of
    anchors: Sourced[str]  # consensus EBITDA path anchors (FY26E/FY27E/NTM), BESIDE the rows
    # the parallel REVENUE anchors — substantiate the TEV/Rev name-row identity (the NTM revenue
    # anchor = the name-NTM revenue implied level). Optional so a pre-fix dossier.json validates.
    rev_anchors: Sourced[str] | None = None
    heterogeneity_gate: str  # the peer-comparability gate, VERBATIM (rendered on the header)
    tev_as_of: str  # the Financial-Data as-of the TEV inputs carry
    multiples_as_of: str  # the multiples-sheet as-of
    vintage_coherent: bool  # G5: |derived-FY26 − direct-FY26 consensus| / direct ≤ 10%
    coherence_note: str  # the residual read (+ the re-pull caveat when not coherent)
    net_debt_reconciled: bool  # (cond. b) net_debt agrees with the cash/debt bridge, in tolerance

    model_config = {"frozen": True}


class OwnHistoryBand(BaseModel):
    """(Phase-3) One own-history valuation band — the CURRENT multiple vs its trailing quarterly
    close range (low/median/high) + percentile. The STRUCTURED series behind range_position's
    display string, so a chart consumes it without re-parsing the string (parsers rule)."""

    metric: str  # "EV/EBITDA (TEV/LTM)" | "P/LTM EPS"
    current: float
    low: float
    high: float
    median: float
    percentile: float  # 0..1 — fraction of trailing history ≤ current
    n_closes: int  # trailing closes, current excluded (matches range_position's "over N closes")
    as_of: str | None = None
    # (Phase-3b) line chart: mean of trailing history ('avg' line; low/high = min/max) + the FULL
    # (date, multiple) close series (current = last point). Additive defaults for round-trip.
    mean: float | None = None
    series: list[tuple[str, float]] = Field(default_factory=list)
    # (periodicity) SELF-DESCRIBING metadata so a band can never again be read as more history than
    # it holds (the 2026-07-21 window-staleness incident: IT's committed band was a genuine but
    # SHORT 5.0y export). periodicity_days_median exposes the close cadence (~91 = quarterly, ~365 =
    # annual); window_span_years is the actual calendar span; periodicity is a coarse label; a
    # data_quality flag fires when quarterly is expected but the spacing is annual. Additive/opt.
    # so pre-metadata committed JSON round-trips byte-identically.
    periodicity_days_median: float | None = None
    window_span_years: float | None = None
    periodicity: str | None = None            # "quarterly" | "annual" | "irregular"
    # "periodicity_mismatch" | "band_incoherent" | both, joined by "+" (fail-loud; see band_guards)
    data_quality: str | None = None
    source_file: str | None = None            # the CIQ export the band was read from
    # (coherence) What the SAME Multiples column implies about this company, from the ratios of its
    # TEV/LTM revenue, EBITDA and EBIT rows — TEV cancels, so these need no absolute figure. Carried
    # on the band because the anchor is computed from committed JSON alone (no workbook re-open) and
    # needs the implied D&A margin to run the recorded-D&A comparison. EV/EBITDA band only; None
    # when the export lacks a TEV/LTM EBIT row. Additive/optional — pre-guard JSON round-trips.
    implied_ebitda_margin: float | None = None
    implied_ebit_margin: float | None = None
    implied_d_and_a_margin: float | None = None
    # (provenance) WHICH bytes produced this band. A filename is not identity — SMPL's band was
    # refreshed from a STALE same-named copy (sha 680fd7bee7, 4.98y) while the canonical export
    # (7bd83a1103, 8.55y) sat elsewhere, and nothing in the artifact showed it. The hash makes a
    # stale read visible IN the record instead of inferable weeks later.
    source_sha256: str | None = None          # first 10 hex of the file actually read
    source_mtime: str | None = None           # ISO mtime of that file

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
    # (Phase-3) STRUCTURED own-history bands (current vs trailing low/median/high + %ile) behind
    # range_position's string, for the band chart. Optional → pre-P3 round-trips; a fresh assembly
    # builds it (shares range_position's computation, so the two can't drift).
    own_history: Sourced[list[OwnHistoryBand]] | None = None
    # (G) price-inverted expectations in multiples-space — renders AFTER cross_sectional, BEFORE the
    # own-history range. Optional so a pre-G dossier.json validates; a fresh assembly builds it.
    implied_expectations: ImpliedExpectations | None = None

    model_config = {"frozen": True}


class TrendPoint(BaseModel):
    """(Phase-3) One point of a per-period metric trend — a period label + its numeric value. The
    STRUCTURED series behind a multi-period display string, so a chart never re-parses it."""

    period: str
    value: float

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
    # (PR-4) How much of the LATEST QUARTER's pre-tax result arrived from below the operating line
    # — `pretax − operating`, derived rather than picked (see `_nonoperating_earnings`). The
    # question it answers is whether GAAP EPS for the period is an operating anchor at all: NFLX's
    # Q1-2026 carries a $2.59bn WBD termination fee (40% of pre-tax) and UBER's Q2-2026 ~$1.39bn of
    # investment revaluation, and neither had ANY route onto a page before this — the CIQ
    # unusual-items block is annual-only, so a quarterly one-off stayed invisible until it landed
    # in a fiscal year. Optional-with-default so committed JSON predating the field round-trips.
    nonoperating_earnings: Sourced[str] | None = None
    liquidity_covenant_flags: Sourced[str]
    multi_year_trajectory: Sourced[str]  # 5y arc of revenue/EBITDA/segment-EBITDA/ROIC (per period)
    # (Phase-3) STRUCTURED per-period ROIC series — the numbers behind multi_year_trajectory's ROIC
    # arc, for the ROIC-trend chart. Optional → pre-P3 round-trips; shares _trajectory_row's read.
    roic_trend: Sourced[list[TrendPoint]] | None = None

    model_config = {"frozen": True}


class SegmentProfitRow(BaseModel):
    """One segment's profit on the FILER'S OWN measure, and its revenue from the identical
    context."""

    segment: str                     # the member humanised ("Amazon Web Services")
    member: str                      # the XBRL member, verbatim — the key a human can check
    profit: float                    # $M
    revenue: float | None = None     # $M; None when the filing does not tag it on that context

    model_config = {"frozen": True}


class SegmentEconomics(BaseModel):
    """(2026-09-21) Where the profit sits, from the latest 10-K's own XBRL instance — the source
    that works for every multi-segment name in the book, where CIQ's ``segment_ebitda`` covers
    two. The MEASURE is the filer's own and is named: an operating income, a gross profit, or a
    filer-defined segment measure is never relabelled as another. ``line`` is the ONE display
    sentence both renderers print; the rows are the structured values anything that computes
    reads."""

    measure: str                     # the XBRL element, verbatim ("us-gaap:OperatingIncomeLoss")
    measure_kind: str                # "operating income" | "gross profit" | "filer-defined …"
    fiscal_year_end: str             # ISO date
    rows: list[SegmentProfitRow]
    segments_sum: float              # $M
    segments_total: float | None = None   # $M — the filer's own operating-segments total, if tagged
    consolidated: float | None = None     # $M — the measure for the whole company, if tagged
    line: str

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
    # (2026-09-21) segment PROFIT from the 10-K's XBRL instance. None for a single-segment filer —
    # a breakdown it does not have is not a gap — and dropped from the JSON when None, so the
    # committed pages it does not apply to stay byte-identical (DROP_WHEN_NONE).
    segment_profit: Sourced[SegmentEconomics] | None = None

    model_config = {"frozen": True}


class DrawdownCause(BaseModel):
    """Why the name fell: shape (discrete event vs gradual bleed) + the 8-Ks at the gap-downs."""

    shape: Sourced[str]  # "discrete event" vs "gradual bleed" — from the gap-down detector
    gap_down_dates: Sourced[list[str]]
    filings: list[FilingRef]  # 8-Ks bound to the gap-down dates (the cause, source-bound)
    revised_guidance: Sourced[str]  # revised FY outlook from the catalyst 8-K's Ex-99.1
    # The detector's own params (screens.assemble constants, copied at assembly — ONE source of
    # truth, no frontend magic numbers). The renderers use them to mark coverage honestly: the
    # 52-wk chart spans ~364d but the detector scans only the last ``gap_window_days``, so a real
    # ≤threshold drop BEFORE the window renders as an unclassified (hollow) marker, never silently
    # unmarked. None on pre-field committed JSON → the renderers skip the boundary/hollow marks.
    gap_threshold: float | None = None  # single-day close-to-close drop that fires the detector
    gap_window_days: int | None = None  # how far back from the reference date the detector scans

    model_config = {"frozen": True}


class IdiosyncraticVsShared(BaseModel):
    """Did the name fall alone (idiosyncratic) or with its graph cohort (shared/thematic)?

    The G2-vs-market compensation: G2 only strips market beta; here we pull the graph-exposed
    cross-section and compare each name's return over the same window. Graph is INPUT, never a
    predictor — ``cohort`` is UNKNOWN when the name isn't in the graph (fail-loud, not fabricated).
    """

    name_180d_return: Sourced[float]
    market_180d_return: Sourced[float]  # the assigned cap-band benchmark (monitor policy)
    rel_vs_market: Sourced[float]  # name − benchmark, recomputed at assembly on the same yardstick
    cohort: Sourced[list[CohortMember]]
    read: Sourced[str]  # "fell alone (idiosyncratic)" vs "fell with cohort (shared/thematic)"
    # cap-band benchmark identity — defaults keep pre-unification committed dossiers loadable
    benchmark_symbol: str = "IWM"
    benchmark_basis: str | None = None  # e.g. "cap-band: $8.7B → mid ($4–25B) → MDY"

    model_config = {"frozen": True}


class PerfPoint(BaseModel):
    """One rebased point on the 52-week performance path — both series indexed to 100 at the window
    start. ``benchmark`` is None only on a date the index has no bar on/before it (the name path
    still renders — fail-loud, never a fabricated flat)."""

    date: str  # ISO trading date
    name: float  # the name's close, rebased to 100 at the window start
    benchmark: float | None  # the assigned benchmark's close, rebased to 100 at the same anchor

    model_config = {"frozen": True}


class StockPerformance(BaseModel):
    """52-week rebased price path — the name vs its assigned cap-band benchmark, both indexed to
    100 at the window start. Assemble/inform ONLY: it *visualizes* the same EOD closes the idio
    comparison (``idiosyncratic_vs_shared``) already sources — never a gate/rank input or verdict.
    The whole object is None on the layer (exhibit absent) when the name has no window bars; a
    point's
    ``benchmark`` is None when the index is absent — fail-loud rather than a fabricated series."""

    points: list[PerfPoint]
    name_symbol: str
    benchmark_symbol: str  # the cap-band assignment (IWM / MDY / SPY)
    as_of: date  # the window end (the exhibit's right edge)
    window_days: int
    name_return: float  # the name's total return over the plotted window (rebased end / 100 − 1)
    benchmark_return: float | None  # the benchmark's, same window (None when the index is absent)
    source_ref: str

    model_config = {"frozen": True}


class ConsensusLevel(BaseModel, frozen=True):
    """(A1) One metric x one forward fiscal year, as the street reported it.

    RAW PAIR. `estimates` is CIQ's own `9/11` — never re-labelled "broker count", because the two
    numbers are not one number and the second is not derivable from the first. Ragged within a
    single name (SMPL 9/11 at FY2026, 11/11 at FY2027), which is why it is persisted PER CELL.
    """

    fy: str
    median: float
    high: float
    low: float
    std_dev: float | None = None
    estimates: str | None = None


class ConsensusContext(BaseModel):
    """Light consensus context (CIQ Estimates) — context for 'am I non-consensus', not a driver."""

    #: (A1) STRUCTURED forward-year consensus, per metric — `{"Revenue": [...], "EBITDA": [...]}`.
    #:
    #: OPTIONAL WITH A None DEFAULT, and that is FORCED rather than chosen: `ConsensusContext` is
    #: non-optional on `MechanicalLayer`, so a required field here would break the load of all
    #: eleven committed dossiers. Forward-binding, the same shape as `RunManifest.universe_as_of`
    #: and `RefPoint.vintage`. None means NOT YET REFRESHED, not "no consensus exists" — the two
    #: are told apart by the fleet pin, not by this field.
    #:
    #: NOTHING RENDERS THIS UNTIL A2. It is machine-complete in the JSON and invisible on the page,
    #: which is stated here so it is not rediscovered as a gap.
    consensus_levels: dict[str, list[ConsensusLevel]] | None = None
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


class GuidanceRow(BaseModel):
    """(H4) One guidance-metric row for the guidance-bridge TABLE — the latest guide, its period and
    date, its age (fresh / Nd stale), the sign-aware delivery record (met/resolved), and the
    most-recent resolved outcome. All display strings (``—`` when a leg is absent) — a RECORDED
    track record, no reading added; the same data the flat ``guidance_bridge`` string carries."""

    metric: str
    latest_guide: str  # the guide value or range, verbatim
    period: str  # the fiscal period the guide is FOR
    dated: str  # ISO guide date
    age: str  # "fresh" or "Nd (stale)" vs the reference date
    record: str  # sign-aware "actual ≥ floor m/n" | "spend ≤ ceiling m/n" | "—" (unresolved)
    most_recent: str  # "FY 2024 MISSED" | "—"

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
    # (H4) the same guidance data as structured rows → a table; optional for pre-H4 JSON.
    guidance_bridge_rows: Sourced[list[GuidanceRow]] | None = None
    revision_events: Sourced[list[RevisionEvent]]  # e. Recent-Changes log; render caps 10, JSON all
    consensus_stats: Sourced[str]  # f. target mean/median/hi-lo/N + rating distribution
    # (PR F) positioning inputs — free, DATED feeds (their own as-ofs, no export-floor). Optional so
    # a pre-F dossier.json still validates; a fresh assembly always builds them (PRESENT/UNKNOWN).
    # Counts / shares / dates only — no interpretation, no direction.
    insider_activity: Sourced[str] | None = None  # g. EDGAR Form 4 (6m): open-market P/S + routine
    short_interest: Sourced[str] | None = None  # h. FINRA settlement: shares short, Δ%, DTC vs ADV

    model_config = {"frozen": True}


class CatalystRow(BaseModel):
    """(catalyst calendar, ratified 2026-07-24) One DATED upcoming event and what it tests —
    machine-ASSEMBLED, never machine-weighted: no probability, no direction, no importance field
    (weighing catalysts is the verdict's job, by constitution). ``expected_date`` is an ISO date
    (YYYY-MM-DD) — or MONTH-granular (YYYY-MM) when the source states only a month (source D:
    "effective in September"; a fabricated day would be a guessed date). Lexicographic sort keeps
    YYYY-MM correctly ahead of every day in its month. ``date_basis`` says how the date is
    known — "stated" (a primary source states it) or "cadence-estimate" (derived from the
    filer's own print rhythm; an ESTIMATE, never a date certain). A date that cannot be sourced
    or soundly estimated produces NO row (fail-loud qa_flag upstream) — never a guessed date."""

    event: str
    expected_date: str  # ISO date (YYYY-MM-DD) or month-granular (YYYY-MM)
    date_basis: str  # "stated" | "cadence-estimate"
    tests_what: str  # which committed claim/guide/wall this event will confirm or refute
    source_ref: str

    model_config = {"frozen": True}


class CatalystCalendar(BaseModel):
    """(catalyst calendar) The assembled dated-event rows + fail-loud QA. Rows sorted by
    ``expected_date``. Empty rows + a qa_flag is an HONEST outcome (cadence unreadable, no
    in-horizon maturities) — the render says so instead of inventing dates."""

    rows: list[CatalystRow] = Field(default_factory=list)
    qa_flags: list[str] = Field(default_factory=list)

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
    # (B2) per-peer LTM valuation multiples from CIQ Trading Multiples — the point of a per-peer
    # comparison. Strings so "NM"/"-" survive; None when the Trading-Multiples sheet/row is absent.
    tev_ebitda: str | None = None  # LTM TEV/EBITDA
    tev_rev: str | None = None  # LTM TEV/Revenue
    pe: str | None = None  # LTM P/E

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


class CapitalInstrument(BaseModel):
    """(E1) ONE debt instrument from CIQ's Capital-Structure-Details panel — verbatim fields, no
    computed judgment. ``maturity_date`` is an ISO date (decoded from the Excel serial) or None when
    the panel gives '-' (undated)."""

    description: str
    type: str  # "Term Loans", "Bonds and Notes", "Capital Lease", …
    principal_musd: float | None
    coupon: str  # "3.000% - 4.000%", "2.700%", "NA"
    floating_rate: str  # "SOFR + 9.750%", "New Benchmark", "NA"
    maturity_date: str | None  # ISO date, or None (undated)
    seniority: str
    secured: bool
    convertible: bool
    currency: str

    model_config = {"frozen": True}


class CovenantPointer(BaseModel):
    """(H1) One located contract-level filing for an instrument family — the EXECUTION filing that
    carries the agreement as an EXHIBIT, found by an efts full-text search SCOPED to the subject CIK
    and verified to contain an agreement-class exhibit. A cross-CIK hit is rejected (the E4 bug: an
    unscoped 'Convertible Bond' matched AXESSTEL 2005). A generic balance-sheet aggregate with no
    discrete contract (Notes Payable, a lease) carries the honest ``note`` (no accession)."""

    family: str  # the instrument family / class this pointer serves
    filing: str  # "8-K" | "latest 10-K" | "—"
    filing_date: str  # ISO, or ""
    accession: str  # the accession the exhibit lives in, or "" (absent)
    exhibits: list[str]  # located agreement-class exhibit filenames (feed the fenced E5 extract)
    note: str = ""  # e.g. "no contract-level filing expected (aggregate line item)"

    model_config = {"frozen": True}


class CovenantTerm(BaseModel):
    """(E5) One named term extracted VERBATIM from a located agreement exhibit — the value exactly
    as the document states it (a number, a formula like "$1.00 ÷ Conversion Rate", a date), bound to
    the exhibit it came from, or UNKNOWN when the term is absent from the document. NEVER inferred,
    computed, or estimated: a convertible whose stated conversion price is a *formula* renders the
    formula, not a fabricated $/share. This is assembly-and-cite, not conclusion — there is no
    verdict/risk field. The ``value`` is a :class:`Sourced` so PRESENT carries the exhibit ref and
    UNKNOWN carries the reason it was absent."""

    name: str  # the term, e.g. "Conversion price", "Initial term loan", "Maturity date"
    value: Sourced[str]  # PRESENT ⇒ verbatim value + exhibit source_ref; else UNKNOWN (not guessed)
    # (RC-1.5d) OPTIONAL structured interest-rate components for interest-type terms — the
    # deterministic scalars behind the verbatim clause, so the value-lead composes from structure
    # instead of re-parsing the LLM-composed string. NOT Sourced: they inherit ``value``'s citation
    # (same clause, same exhibit). None on every non-interest term and on pre-RC-1.5d JSON. A render
    # composes a lead only when required components are present AND each numeric's digits appear in
    # the parent clause (a transcription slip must never headline the row). margin_pct/margin_bps
    # are mutually-exclusive alternates — units render AS DISCLOSED, never normalized.
    base_rate_label: str | None = None  # e.g. "Term SOFR", "LPR", "New Benchmark"
    margin_pct: float | None = None  # spread over the base, in percent (e.g. 9.75)
    margin_bps: float | None = None  # spread over base, in bps (e.g. 115) — alternate to margin_pct
    floor_pct: float | None = None  # rate floor, in percent (e.g. 3.00)
    pik_pct: float | None = None  # PIK component, in percent (e.g. 3.75)

    model_config = {"frozen": True}


class CapitalStructure(BaseModel):
    """(E1–E5) The structured capital structure — per-instrument detail + summary aggregates + the
    survival reads that hang off it (the maturity wall's 8-Ks, covenant exhibit pointers, and the
    fenced Tier-2 covenant terms). It ASSEMBLES and CITES; there is no probability/risk/verdict
    field. ``detail_as_of`` keeps the panel's own filing note (the detail is panel-dated, the total
    debt is latest-quarter — the reconciliation names the gap)."""

    instruments: Sourced[list[CapitalInstrument]]
    summary: Sourced[str]  # aggregates + QoQ movement (term loans / bonds / leases / principal)
    detail_as_of: str  # the panel's own "Source: A 2025 filed Mar-16-2026" note
    maturity_filings: Sourced[str]  # (E3) 8-Ks filed at/near instrument maturities
    covenant_pointers: Sourced[str]  # (E4) accession-bound exhibit pointers — one-line summary
    # (H1) the structured, CIK-verified pointer rows (rendered as a table); optional for pre-H JSON.
    covenant_pointer_rows: Sourced[list[CovenantPointer]] | None = None
    covenant_terms: Sourced[str]  # (E5) fenced Tier-2 extracted terms — one-line summary/UNKNOWN
    # (H1d/E5) the structured per-term rows the fenced LLM extracted from the located exhibit(s),
    # each a {value, source_ref} or UNKNOWN (rendered as a table); optional for pre-H1d JSON.
    covenant_term_rows: Sourced[list[CovenantTerm]] | None = None
    # (P3/FIX-3) the fenced VERBATIM resolution event at a maturity 8-K — Item 8.01/1.01/3.02
    # (e.g. the 2026-05-28 Notice-of-Conversion: full principal → common stock). value = verbatim
    # (≤400c), source_ref = "8-K <accession> (<date>)". Optional so a pre-P3 dossier.json validates.
    maturity_event: Sourced[str] | None = None
    # (PR-3) HOW OLD THE PANEL IS, and whether a termination has been filed since it was taken.
    # The panel has never carried an age: `freshness._PANEL_KEY` matches `detail_as_of` but
    # `freshness._ISO` wants an ISO date and CIQ writes "Jan-23-2026", so the key was found and the
    # date never extracted — measured, every committed name's schedule is 82-280 DAYS old. Not
    # routed into `check_freshness`, whose ceiling is 45d: all fourteen are past it, so that gate
    # would refuse the whole fleet. Optional-with-default so pre-field JSON round-trips.
    panel_vintage: Sourced[str] | None = None

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
    bridge: Sourced[str]  # + cash, − total debt (TEV → equity), CIQ figures — RENDER-ONLY display
    # STRUCTURED bridge components ($M) — the LOAD-BEARING values consumers read (never re-parse the
    # display string; DESIGN RULE). None when the CIQ row is absent. Default None = back-compat.
    bridge_cash: float | None = None  # "+ Total Cash & ST Investments" ($M)
    bridge_debt: float | None = None  # "- Total Debt" ($M)
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


class FinRow(BaseModel):
    """One row of a financial-summary table — a label + pre-formatted display cells (one per col),
    with '—'/'— (basis)' for a gap or a growth that would cross a reclassification basis. Strings so
    the (R) markers + the actual→estimate boundary read exactly; each figure still traces."""

    label: str
    cells: list[str]
    # (Phase-3 charts) the STRUCTURED numeric behind each display cell (None for a "—"/non-numeric
    # cell), parallel to `cells`, so a chart consumes structured series and NEVER re-parses the
    # display strings (parsers rule). Populated for the raw numeric rows; default [] round-trips a
    # pre-Phase-3 dossier.json (a consumer treats absent/empty as "no structured series").
    values: list[float | None] = Field(default_factory=list)
    # (P1 brief fix, 2026-07-28) Does this row clear the materiality floor? Set ONCE at assembly,
    # where the market cap lives; both brief renderers READ it and neither recomputes — a second
    # copy of the threshold arithmetic in two twins is the parity hazard this repo keeps closing.
    # Default False round-trips every pre-existing dossier.json.
    material: bool = False

    model_config = {"frozen": True}


class FinTable(BaseModel):
    """A financial-summary table — column headers + rows — BORN for the shared compact renderer
    (columns → the header, each row's cells → a data row). No conclusion; assemble + cite."""

    columns: list[str]
    rows: list[FinRow]
    note: str = ""
    # (Phase-3 charts) STRUCTURED per-column consensus-estimate flag (parallel to `columns`) — a
    # chart/table marks E cols as CONSENSUS (never the machine's forecast), not from the label
    # suffix (display formatting must not be load-bearing). Default [] round-trips a pre-P3 JSON.
    is_estimate: list[bool] = Field(default_factory=list)

    model_config = {"frozen": True}


class EbitdaBasis(BaseModel):
    """Implied D&A either side of the annual table's actual→estimate boundary, and whether the two
    `EBITDA ($M)` readings agree.

    STRUCTURED, with the display string ALONGSIDE the numbers rather than instead of them (the
    display-formatting-is-never-load-bearing rule): both renderers gate on `divergent`/`ratio` and
    neither parses `note`.

    Lives HERE rather than beside its builder, matching `CapitalAllocation`: schemas own the shapes
    and the builder module imports them. The first cut inverted that, which forced `read_basis` to
    take `Any` and duck-type its way through a `FinTable` it could not name.
    """

    actual_implied_dna: float | None = None
    estimate_implied_dna: float | None = None
    ratio: float | None = None
    #: True only OUTSIDE [FLAG_LOW, FLAG_HIGH] — a step no depreciation schedule produces.
    divergent: bool = False
    #: Why the answer is what it is, INCLUDING when it could not be computed. Never empty: "not
    #: flagged" and "not checked" are different claims and a blank cannot distinguish them.
    note: str = ""

    model_config = {"frozen": True}


class FinancialSummary(BaseModel):
    """The FINANCIAL-SUMMARY appendix (C1–C4): the fusion of CIQ Financials ACTUALS with Estimates
    CONSENSUS, rendered after the twins. ``annual`` = last-4-FY + LTM + FY26E/FY27E (E cols marked
    + stamped with ``as_of``); ``quarterly`` = trailing-8-Q (the Q1-2026 collapse made visible, YoY
    same-basis only); ``balance_sheet`` = period-labelled posture; ``coherence`` = the BS↔implied-
    bridge reconciliation (both sources shown on disagreement, never silently picked)."""

    annual: Sourced[FinTable]  # C1 + C4 (CF essentials folded in)
    quarterly: Sourced[FinTable]  # C2 — trailing 8 quarters
    balance_sheet: Sourced[str]  # C3 — period-labelled posture block
    coherence: Sourced[str]  # C3 — BS cash/debt vs the implied-valuation bridge
    as_of: Sourced[str]  # the estimates as-of basis stamped on the E columns
    #: Do the ACTUAL and ESTIMATE `EBITDA ($M)` rows of `annual` share a basis? DERIVED from that
    #: table's own implied D&A (EBITDA − EBIT) either side of the boundary — never read off a label,
    #: because the sheet does not carry one. See `vinci.dossier.ebitda_basis`. Optional and
    #: defaulting to None so every already-committed dossier round-trips unchanged.
    ebitda_basis: EbitdaBasis | None = None

    model_config = {"frozen": True}


# --- RC-1 (A): primary-source release extraction — 8-K EX-99.1, DETERMINISTIC / anchored ----------


# The unit vocabulary a guidance range may be stated in. "$M" is the default because most guides
# are dollar amounts in millions; "$/sh" exists because per-share guides are NOT, and the absence
# of this member is what let adjusted EPS render in millions (2026-07-29).
GUIDANCE_UNITS: frozenset[str] = frozenset({"$M", "%", "$/sh", "bps"})

#: WHAT THE NUMBERS ARE — a LEVEL the metric will reach, or a CHANGE from the prior period.
#: A guide of "$1.345–1.355 billion" and a guide of "decline approximately 375 basis points" are
#: not the same KIND of quantity, and until 2026-08-05 the model could only express the first: ten
#: of seventeen dropped clauses across four names were changes. Capturing them without this field
#: would have stored SMPL's "decline between 300 and 350 basis points" as low=300 high=350 unit="%"
#: — a gross margin of 300-350%, a 100x error in a decision figure, in a parser already fixed twice
#: for exactly that class.
GUIDANCE_BASES: frozenset[str] = frozenset({"level", "change"})


class GuidanceItem(BaseModel):
    """(RC-1 A) One company guidance/outlook metric from a 99.1 press release — a range, or a
    QUALITATIVE-only marker when the outlook names the metric but states NO number (MVST's
    '2026 … continued revenue growth' is qualitative). Verbatim-bound, no reading added."""

    metric: str  # revenue | adjusted ebitda | adjusted eps | gross margin | free cash flow
    period: str  # e.g. "2026"
    low: float | None  # range low, in `unit`. None when QUALITATIVE
    high: float | None  # range high. None when a single value or QUALITATIVE
    # THE UNIT THE VALUES ARE IN — and the vocabulary was UNEXPRESSIVE until 2026-07-29.
    #
    # It held "$M" | "%" over a THREE-value reality, and this field's own docstring used to record
    # the third in prose — "$M; $/sh for EPS; % for margin" — encoding a unit in the METRIC NAME
    # where no formatter reads it. So every adjusted-EPS guide carried `unit="$M"` while holding
    # dollars per share, and the driver composer (which assumes $M for anything not "%") rendered
    # VRRM's $1.19–$1.25 guide as "$1.2–$1.2M": wrong by 1e6, and collapsed to a zero-width range
    # by a hardcoded .1f. A vocabulary that cannot express a unit keeps producing values that
    # claim the wrong one — every new metric inherits the wrong default.
    #
    # Validated against a closed set, on the BEAR_BASES precedent: an unlisted unit is not
    # formattable, so it is added deliberately rather than arriving through a typo.
    unit: str = "$M"
    #: LEVEL (the value the metric reaches) or CHANGE (the movement from the prior period). Defaults
    #: to "level", which is what every guide captured before 2026-08-05 was, so committed dossiers
    #: keep their meaning. A CHANGE carries a signed value: "decline 375bps" is low=high=-375.
    basis: str = "level"
    qualitative: bool  # True ⇒ named in the outlook with NO number (fail-loud honest, not a guess)
    verbatim: str  # the outlook sentence, ≤200c
    source_ref: str  # accession + exhibit

    model_config = {"frozen": True}

    @field_validator("basis")
    @classmethod
    def _basis_known(cls, v: str) -> str:
        if v not in GUIDANCE_BASES:
            raise ValueError(f"guidance basis {v!r} is not one of {sorted(GUIDANCE_BASES)}")
        return v

    @field_validator("unit")
    @classmethod
    def _unit_known(cls, v: str) -> str:
        if v not in GUIDANCE_UNITS:
            raise ValueError(
                f"guidance unit {v!r} is not one of {sorted(GUIDANCE_UNITS)} — an unlisted unit "
                "cannot be formatted, and a value that claims the wrong unit is worse than an "
                "absent one; add the member deliberately")
        return v


class ReconciliationValue(BaseModel):
    """(RC-1 A) One non-GAAP reconciliation ACTUAL from a 99.1 — adjusted EBITDA / net income / EPS
    for a period, sign-aware ('negative $5.5 million' ⇒ -5.5). Verbatim-bound; never a guess."""

    metric: str  # "adjusted ebitda" | "adjusted net income" | "adjusted eps"
    period: str
    value: float  # $M (or $/share for EPS); NEGATIVE for a loss
    # The DIRECTION the release states beside the level ("$230.0 million, an increase of $21.5
    # million" / "up 12.8% year-over-year"). A level alone cannot explain a gap-down — the reader
    # needs to know whether it rose or fell. Verbatim-derived; None when no change is stated.
    # Optional so pre-existing dossier.json still validates.
    change: str | None = None
    verbatim: str
    source_ref: str

    model_config = {"frozen": True}


class OneOffItem(BaseModel):
    """(RC-1 A) One one-off item from a 99.1 — an impairment / charge / write-down: the amount + the
    verbatim description ('$32.5M inventory impairment … ESS components'). Bound to the exhibit."""

    amount: float  # $M
    description: str  # verbatim, ≤200c
    verbatim: str
    source_ref: str

    model_config = {"frozen": True}


class EventImpact(BaseModel):
    """(RC-1 A) One event-impact quantification from a 99.1 — the Avis class: a named event 'expects
    to reduce {metric} by $A to $B'. Direction + range, verbatim-bound; no reading added."""

    metric: str  # e.g. "revenue" | "segment profit"
    effect: str  # "reduce" | "increase" — the event's effect on the metric (a RECORDED verb)
    low: float | None  # $M
    high: float | None
    period: str  # e.g. "2026 annualized"
    verbatim: str
    source_ref: str

    model_config = {"frozen": True}


class ReleaseExtract(BaseModel):
    """(RC-1 A) The DETERMINISTIC extraction of ONE 8-K EX-99.1 earnings/guidance exhibit: guidance,
    non-GAAP reconciliation actuals, one-offs, and event-impact quantifications — every item
    source-bound to the exhibit. ``qa_flags`` carries fail-loud markers ('no anchored pattern
    matched') — a miss is UNKNOWN + a QA note, never an analyst caveat, never a guessed number."""

    # (item 1 clause (c)) The filing's OWN date, structured. `source_ref` carries the
    # accession as a DISPLAY STRING ("8-K 0001702744-26-000021 EX-99.1"); selecting the
    # freshest guide by parsing that string would be the display-string parse this repo
    # forbids. Default None so releases committed before this field round-trip.
    filed: date | None = None
    source_ref: str  # accession + exhibit URL
    guidance: list[GuidanceItem] = Field(default_factory=list)
    reconciliation: list[ReconciliationValue] = Field(default_factory=list)
    one_offs: list[OneOffItem] = Field(default_factory=list)
    event_impacts: list[EventImpact] = Field(default_factory=list)
    qa_flags: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}


# --- RC-1 (B): filing-section extraction — 10-Q/10-K, DETERMINISTIC / anchored --------------------


class GoingConcern(BaseModel):
    """(RC-1 B) The going-concern / liquidity note: whether the filing raises SUBSTANTIAL DOUBT, the
    verbatim sentence (≤400c), and a one-line summary of management's plans. Bound to the filing."""

    substantial_doubt: bool  # True ⇒ the filing states 'substantial doubt about … going concern'
    verbatim: str  # the substantial-doubt sentence, verbatim, ≤400c
    plans: str  # management's plans one-liner ('' when the note states none)
    source_ref: str

    model_config = {"frozen": True}


class DebtTranche(BaseModel):
    """(RC-1 B) One named near-term debt tranche from the debt footnote — filing-basis, verbatim."""

    name: str  # e.g. "bond payable", "convertible loan"
    amount: float  # $M
    maturity: str  # verbatim maturity, e.g. "January 2027" ('' when absent)
    verbatim: str
    source_ref: str

    model_config = {"frozen": True}


class MaturityWall(BaseModel):
    """(RC-1 B) The FILING-BASIS near-term maturity schedule (distinct from the CIQ panel): the
    total due within 12 months + named tranches, verbatim-bound — for the divergence. TWO-STATE:
    ``state='located'`` (a ≤12m-wall statement found) vs ``state='not_stated'`` (a debt section is
    present but states NO near-term wall — a value-free KNOWN, not an unknown; avoids the
    thousands-units trap of a composition table). No debt section located at all ⇒ this is None."""

    within_12m_total: float | None  # $M due within the next 12 months; None when state='not_stated'
    tranches: list[DebtTranche] = Field(default_factory=list)
    state: str = "located"  # "located" | "not_stated"
    note: str = ""  # the value-free note when state='not_stated'
    verbatim: str
    source_ref: str

    model_config = {"frozen": True}


class ConcentrationCustomer(BaseModel):
    """(RC-1 B) One customer's revenue concentration % (+ the prior-period %), verbatim from the
    concentration note."""

    name: str  # e.g. "Customer A", "City of New York Department of Transportation"
    pct: float  # % of revenue, current period (a disclosed FLOOR when value_kind == 'floor')
    prior_pct: float | None  # the prior-period %, when the note gives a comparative
    value_kind: str = "exact"  # "exact" (a stated %) | "floor" ('exceeded N%' — a disclosed floor)

    model_config = {"frozen": True}


class CustomerConcentration(BaseModel):
    """(RC-1 B) The customer-concentration disclosure: the named customers' %s, the top-5 % when
    stated, and any PO / minimum-volume order-terms language. Bound to the filing."""

    customers: list[ConcentrationCustomer] = Field(default_factory=list)
    top5_pct: float | None
    terms: str  # PO / minimum-volume / take-or-pay language ('' when none)
    source_ref: str

    model_config = {"frozen": True}


class Commitment(BaseModel):
    """(RC-1 B) One purchase/capital commitment: amount, the portion due ≤12 months, + verbatim."""

    kind: str  # "purchase" | "capital"
    amount: float  # $M
    within_12m: float | None  # $M due within 12 months, when stated
    verbatim: str
    source_ref: str

    model_config = {"frozen": True}


class FilingSectionExtract(BaseModel):
    """(RC-1 B) The DETERMINISTIC heading/anchor-targeted extraction of a 10-Q/10-K: going-concern,
    the filing-basis maturity wall, customer concentration, and purchase/capital commitments — each
    source-bound. ``qa_flags`` fail loud on a miss ('no anchored pattern matched'), not a guess."""

    source_ref: str
    going_concern: GoingConcern | None = None
    maturity_wall: MaturityWall | None = None
    concentration: CustomerConcentration | None = None
    commitments: list[Commitment] = Field(default_factory=list)
    qa_flags: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}


# --- (PR-B) operating drivers — the mechanism tier (anchored A1/A2/A3 + gated LLM-fenced) ---------


class DriverKind(enum.StrEnum):
    """The kind of operating-mechanism fact — the taxonomy the Brief's Mechanism block groups by."""

    LEADING_INDICATOR = "leading_indicator"  # a unit-volume / KPI run-rate (a shipped/added count)
    PRICING_ACTION = "pricing_action"  # a price change taken/announced (dated where stated)
    ATTRIBUTION = "attribution"  # an MD&A price/volume/mix causality sentence ($ + % + cause)
    EVENT = "event"  # a dated CIQ Key-Developments row (typed headline)
    PASS_THROUGH_STRUCTURE = "pass_through_structure"  # indexation / contract pass-through facts
    COMPETITIVE_POSITION = "competitive_position"  # a stated competitive-slack / position claim


class OperatingDriver(BaseModel):
    """(PR-B) One typed, cited, verbatim-bound operating-mechanism fact. ``value`` is the VERBATIM
    stated value; ``value_num``/``unit`` are the STRUCTURED numeric an ANCHORED extractor parsed
    (None on an LLM-fenced row — verbatim-only there, the covenant discipline). ``source_ref`` is
    MACHINE-SET by the extractor; the model/parse never invents a citation. ``tier`` records the
    extraction path (anchored | llm-fenced) so the human weighs deterministic vs LLM-read rows."""

    kind: DriverKind
    metric: str  # e.g. "revenue", "average selling price", a KD Type
    period: str | None = None  # as STATED ("Q1 2026", "FY26"); None when unstated
    value: str  # the VERBATIM stated value ("$32.0 million, or 43.6%", "536 MWh")
    value_num: float | None = None  # STRUCTURED numeric — anchored rows only; consumers read THIS
    unit: str | None = None  # the value_num's unit ("%", "MWh", "$M"); None on verbatim-only rows
    verbatim: str  # the exact sentence/row read from — the human greps for it
    #: THE REST OF THE SPEAKER'S PARAGRAPH after `verbatim`, unclassified (STATE §B1a).
    #:
    #: WHY THE QUOTE ALONE IS NOT ENOUGH. BRBR's row quoted *"In the third quarter, 70% of RTD
    #: shake category volumes were sold on price promotion"* — exact, correctly cited, digits
    #: traceable, passing every guard we have, because every guard takes the QUOTED TEXT as the
    #: check. The sentence the extraction did not take says the figure is *"in line with historical
    #: norms … while DOWN sequentially from the heavier promoted second quarter"*. The synthesis
    #: then argued an escalating sequence its own source contradicts.
    #:
    #: UNCONDITIONAL, AND THAT IS THE DESIGN. No opener list, no contrastive classifier, no rule
    #: deciding which rows deserve context — the moment one exists, the criterion is back. It was
    #: measured and it does not work: BRBR's reversal opens with *"This is"*, the same connective
    #: as VRRM's *"This is a great indication that safety measures are working."* Identical syntax,
    #: opposite function, so a connective regex calls the one case that bit us benign.
    #:
    #: PARAGRAPH, NOT N SENTENCES. A 26-row hand sample put the reading-changing context BEYOND the
    #: next sentence in 4 of 7 cases, so one sentence is the wrong bound. Over all 191 rows:
    #: +1 sentence = 90% of the verbatim payload, +2 = 186%, +3 = 279%, PARAGRAPH = 161% — and the
    #: paragraph is the ONLY bound crossing ZERO call boundaries, because a blank line precedes
    #: every `--- <call> ---` marker. Sentence bounds splice a different transcript onto 1-3 rows.
    #:
    #: COST. ~1.8% of the synthesis prompt on the largest name, and NOTHING for the reader: 0 of
    #: 241 driver verbatims render on the page — this is tier 3, `dossier.json` and the LLM brief.
    following_context: str | None = None
    source_ref: str  # accession + exhibit / "CIQ Key Developments: …" / "CIQ transcript: …"
    tier: str  # "anchored" | "llm-fenced"

    model_config = {"frozen": True}


class OperatingDriversExtract(BaseModel):
    """(PR-B) The assembled operating-driver rows across sources (EX-99.1 A1 + 10-Q MD&A A2 + CIQ
    Key Developments A3 + gated transcript LLM-fenced), plus fail-loud ``qa_flags`` — every miss,
    drop, or parse failure is a loud marker, never a fabricated row."""

    rows: list[OperatingDriver] = Field(default_factory=list)
    qa_flags: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}


# --- RC-1 (C): the primary-source layer — parsed extracts + DERIVED cross-source surfaces ---------


class PrimarySource(BaseModel):
    """(RC-1 C) The primary-source layer — parsed EX-99.1 release(s) + latest 10-Q sections, plus
    the DERIVED cross-source render surfaces (survival self-funding, same-window wall coherence,
    EBITDA-basis triangulation, guide verification). Assembly-time + source-bound; a fetch/parse
    miss is UNKNOWN + a QA note, never an abort, never an analyst caveat. Each derived line is a
    Sourced[str] whose components name their source LAYER (filing vs CIQ panel vs release)."""

    releases: list[ReleaseExtract] = Field(default_factory=list)
    filing: FilingSectionExtract | None = None
    self_funding: Sourced[str]        # two-input read: latest-Q OCF sign AND LTM FCF (MIXED / fund)
    wall_coherence: Sourced[str]      # same-window filing-vs-panel coherence, tranche-matched
    basis_triangulation: Sourced[str]  # EBITDA/margin bases table — every leverage row labeled
    # (item 1 clause (c)) THE VERDICT-RELEVANT CURRENT GUIDE — the split out of
    # `drawdown_cause.revised_guidance`. That field follows the 99.1 on the DRAWDOWN 8-Ks, so it is
    # drawdown-vintage BY CONSTRUCTION: what management said in the filing that caused the gap.
    # Correct as built. But its docstring also claimed "the verdict-relevant number", and the two
    # readings DIVERGE exactly when guidance is revised after the drawdown — which is SMPL: the
    # bear argued the April guide from the drawdown block while the base used the July guide from
    # `releases`, both unlabelled, in one document. One function was trying to be two things.
    # This field is the second thing: the latest results filing's guide, independent of whether a
    # price event occurred. UNKNOWN (attributed) when no release carries one.
    current_guide: Sourced[str] | None = None
    guide_verification: Sourced[str]  # CIQ guide vs release guide (vendor-echo / cross-source)
    qa_flags: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class StockInfo(BaseModel):
    """(Phase-2) The market-data 'stock info' box — CMP + 52-week range (EOD price features), shares
    outstanding (EDGAR XBRL), book value/share + market cap (CIQ). Each value is source-bound and
    fail-honest: UNKNOWN when its source is absent, never a fabricated number. Assemble/inform
    context for the Brief teaser — never a gate/rank input."""

    price: Sourced[float]          # last EOD close — the current market price (CMP)
    high_52w: Sourced[float]       # 52-week high (EOD; UNKNOWN without ~a year of bars)
    low_52w: Sourced[float]        # 52-week low (EOD)
    shares_out: Sourced[float]     # shares outstanding — EDGAR XBRL (raw count)
    book_value_ps: Sourced[float]  # book value / share — CIQ Balance Sheet
    market_cap: Sourced[float]     # market cap in $M — CIQ (from the implied-val bridge)
    as_of: date | None = None      # the EOD price's as-of date (the latest bar used)
    #: The CAP's OWN vintage — the comps workbook as-of, NOT the price's. Structured so the
    #: Snapshot's clause-(e) label binds to the cap's real date rather than a neighbouring panel's
    #: (O3): the vintage used to live only inside `market_cap.source_ref`, which left the renderer
    #: nothing to bind to, so it was wired to `implied_expectations.multiples_as_of` — a DIFFERENT
    #: panel, wrong on 11 of 11 names. Optional because committed dossiers predate the field and
    #: must stay readable; absent → the label prints NO cap date rather than a wrong one.
    market_cap_as_of: date | None = None

    model_config = {"frozen": True}


class RegistrationFiling(BaseModel):
    """One registration statement / prospectus supplement from the EDGAR filing index — form,
    date, accession only. The INDEX is the source; no document body is parsed, so no dollar size
    is asserted (a size would need the prospectus text, and a half-parsed size is worse than a
    dated pointer the human can open)."""

    form: str          # "S-3" / "S-3ASR" / "424B5" / "S-1" / "S-8" …
    filing_date: str   # ISO
    accession: str

    model_config = {"frozen": True}


class DilutionPipeline(BaseModel):
    """FORWARD dilution capacity on file — registration statements and prospectus supplements
    from the EDGAR filing index, over a stated trailing window bounded at the record's as-of.

    THE GAP THIS CLOSES: the stack measured REALIZED dilution (share-count trend) and buybacks,
    but nothing watched the pipeline — an effective shelf, prospectus supplements drawing on it,
    a fresh S-1. For a drawdown name, issuance into the drawdown is the recovery-killer, and it
    is announced in exactly these filings. Assemble-and-cite only: counts, forms and dates — the
    READING (how much risk the pipeline is) stays the human's.

    "NONE ON FILE" IS A FINDING, NOT AN UNKNOWN: an empty window means no registered capacity,
    which is decision-relevant the same way EPAM's never-impaired goodwill is. UNKNOWN is reserved
    for a failed fetch / missing CIK, and the two must never render alike.

    EQUITY AND DEBT ARE NOT DISTINGUISHED, AND THE LABEL SAYS SO. A universal shelf registers
    both, and the index alone cannot tell a 424B5 ATM draw from a 424B2 bond takedown — V's six
    supplements are debt issuance, FUBO's are the equity machinery, and the index shape is
    identical. Asserting "dilution" for a bond deal would be a false claim; reading the prospectus
    to classify is a follow-up, not a reason to guess."""

    filings: list[RegistrationFiling]  # newest first, window-bounded, machine-complete
    line: Sourced[str]                 # the composed MAIN-BODY line (counts + dates, no reading)
    window_days: int                   # the trailing scan the counts describe

    model_config = {"frozen": True}


class SbcLine(BaseModel):
    """STOCK-BASED COMPENSATION — the ONGOING dilution engine, as $ and as % of revenue.

    WHY THE RATIO LEADS AND THE DOLLARS FOLLOW. Dollars alone do not compare: NFLX's $368M and
    NCNO's $74M are five times apart in dollars and fifteen times apart the other way in
    intensity, and intensity is the decision-relevant reading. Measured on this fleet the ratio
    spans **0.7% to 12.4%** and sorts almost exactly by business model — one software name
    isolated at the top, the consumer-staples cluster at the bottom.

    **THE NUMERATOR AND DENOMINATOR ARE THE SAME WINDOW, BY CONSTRUCTION.** This is the defect
    the field was built around: the first measurement paired each name's LATEST 10-K SBC with the
    dossier's LTM revenue, and FUBO's FY2024 SBC over its post-merger LTM revenue read **0.7%
    when the true FY2024 ratio is 2.6%** — understated 3.7x. The revenue fact is now matched on
    the SBC fact's EXACT ``start``/``end``, so the two cannot drift apart. Where no revenue fact
    covers the SBC window the ratio is UNKNOWN and the dollars still print — a stated gap, never
    a ratio across mismatched periods.

    IT IS NOT THE EBITDA WEDGE. ``ebitda_basis`` records that the actual row expenses SBC while
    consensus adds it back; this field says how big that recurring charge IS relative to the
    business. The two answer different questions and are read in that order — the wedge matters
    where this ratio is high."""

    expense: Sourced[float]            # $M, the SBC charge over `window`
    pct_revenue: Sourced[float]        # %, over the IDENTICAL window — UNKNOWN if none matches
    window_start: str                  # ISO — the SBC fact's own period, carried so the
    window_end: str                    # reader can see what the ratio is a ratio OF
    line: Sourced[str]                 # the composed MAIN-BODY line

    model_config = {"frozen": True}


class OwnershipFiling(BaseModel):
    """One Schedule 13D/G from the EDGAR filing index — form, date, accession only.

    THE FILER IS NOT HERE, AND THAT IS DELIBERATE. The submissions index carries the SUBJECT
    company's filings; it does not name the ACQUIRER in the recent arrays. Naming who accumulated
    would need each document fetched and parsed, so this block cites the accession and lets the
    human open it rather than asserting an identity the index never supplied."""

    form: str          # "SC 13D" / "SCHEDULE 13D/A" / "SC 13G" / "SCHEDULE 13G" …
    filing_date: str   # ISO
    accession: str

    model_config = {"frozen": True}


class OwnershipEvents(BaseModel):
    """WHO IS ACCUMULATING — Schedule 13D/G beneficial-ownership filings over a trailing window
    bounded at the record's as-of.

    THE TWO SCHEDULES ARE DIFFERENT FACTS AND ARE NEVER SUMMED. A **13D** is filed by a holder
    crossing 5% WITH intent to influence — the activist/control signal. A **13G** is the passive
    short-form used by index funds and institutions crossing the same threshold; on this fleet it
    is the base rate, present on all 14 names. Merging them would bury 51 activist filings under
    430 passive ones and report Vanguard's index re-weight as if it were an activist stake.

    **BOTH EDGAR VOCABULARIES ARE READ, and this is the defect the block exists to avoid.** EDGAR
    renamed these form types: filings appear as ``SC 13D``/``SC 13G`` through 2024 and as
    ``SCHEDULE 13D``/``SCHEDULE 13G`` after. Measured on this fleet's 3y window, an ``SC 13``
    filter sees 153 of 306 filings — **exactly half** — and every one it misses is the RECENT
    half. Two names flip from clean to not: AORT 0 → 1 activist filing, FUBO 0 → 2. A form list
    that reports "no activist interest" because the form was renamed is the false-CLEAN direction,
    the same failure `dilution_pipeline`'s taxonomy pin exists to prevent.

    "NONE IN WINDOW" IS A FINDING, NOT AN UNKNOWN — eight of 14 names carry no 13D, which is a
    fact about the register. UNKNOWN is reserved for no CIK / failed fetch, and the two must never
    render alike.

    COUNTS, FORMS AND DATES ONLY — no reading, no filer identity, no stake size. Whether an
    activist on the register is a risk or a catalyst is the human's call."""

    filings: list[OwnershipFiling]  # newest first, window-bounded, machine-complete
    line: Sourced[str]              # the composed MAIN-BODY line
    window_days: int                # the trailing scan the counts describe

    model_config = {"frozen": True}


class CapitalAllocation(BaseModel):
    """Capital created or destroyed — EDGAR XBRL only, each value naming the tag that answered."""

    goodwill: Sourced[float]                    # $M, latest annual — impairment headroom
    intangibles: Sourced[float]                 # $M, latest annual
    goodwill_impairment: Sourced[float]         # $M, latest annual — what was already written off
    intangible_impairment: Sourced[float]       # $M, latest annual
    buyback_cash: Sourced[float]                # $M, latest annual
    buyback_shares: Sourced[float]              # raw share count, latest annual
    buyback_avg_price: Sourced[float]           # $/share — see AVG_PRICE_BASIS
    acquisition_consideration: Sourced[float]   # $M, latest annual
    #: ALWAYS a stated gap. The brand dimension is footnote prose with no XBRL axis, and an
    #: aggregate impairment with no note reads as though the split were simply not interesting.
    brand_split: Sourced[str]

    model_config = {"frozen": True}


class PeerImpairment(BaseModel):
    """Did this filer WRITE DOWN what it carries, over a stated trailing window?

    THE BALANCE COMPARISON CANNOT ANSWER THIS, and that is why the block exists (STATE.md §M3).
    SMPL carrying 73% of assets as acquired against a 57.6% peer median says the LOAD is ordinary;
    it says nothing about whether the sector marks that load down. The same charge means opposite
    things against a sector that impairs routinely and one that never does.

    FOUR STATES, FOUR SENTENCES — and the live corpus produced all four before a line was written:

    * ``charged``        — an annual charge inside the window (KHC 5 years, CAG 4, MZTI 2).
    * ``explicit-zero``  — the filer TAGS impairment and reports **0**. JJSF states
      ``GoodwillImpairmentLoss`` for 16 consecutive years, every one zero. That is the strongest
      available evidence of "did not write down" — a MEASUREMENT, not a gap — and it must never
      render like an absence.
    * ``none-in-window`` — the filer tags impairment historically but has no annual point inside
      the window. CPB impaired four times between FY2013 and FY2018 and nothing since; over a
      trailing five years it would look identical to a name that never impaired, and it is not
      one. ``last_charge_end`` carries the fact the window drops.
    * ``untagged``       — no annual point under either family, ever (FRPT, BRBR, UTZ).

    ``explicit-zero`` vs ``none-in-window`` vs ``untagged`` is #362's rule at VALUE scope: three
    different facts, and the informative one must not stand in for the empty one.

    ANNUAL DURATIONS ONLY, WHICH IS WHAT MAKES THE SUM SAFE. companyfacts carries overlapping
    year-to-date and quarterly points for the same period, plus restatements of it; summing them
    double-counts. Restricting to ~12-month spans (`ConceptPoint.is_annual`), de-duplicating by
    `period_end` (latest `filed` wins) and then dropping any span overlapping one already kept
    makes the total a sum over DISJOINT years.

    AND THE RULE THAT MAKES THE SUM SAFE EXCLUDES THE SUBJECT'S OWN LIVE CHARGE. SMPL's $369.0M is
    a **272-day year-to-date** point, so it is not annual and is not in the window total — whose
    comparable figure is the $60.9M FY2025 annual charge. Rendering those two adjacent without
    saying so is precisely the basis mistranslation §M3 was written about, so the year-to-date
    charge is carried SEPARATELY in ``pending`` and is never summed into ``total``.
    """

    state: str                              # charged | explicit-zero | none-in-window | untagged
    #: The reader-facing wording, IN THE DATA so the two renderers cannot drift apart —
    #: `is_subject`'s lesson (#372) and the duplicate-definition detector's rule (27a).
    state_label: str = ""
    window_start: date
    window_end: date
    observations: int = 0                   # annual points found INSIDE the window
    charged_years: int = 0                  # of those, how many carry a charge > 0
    total: float | None = None              # $M, summed over disjoint annual years in the window
    pct_acquired: float | None = None       # total / acquired balance
    #: From the FULL history, not the window — the fact `none-in-window` would otherwise hide.
    last_charge_end: date | None = None
    last_charge_amount: float | None = None  # $M
    #: The live year-to-date charge `is_annual` excludes. NEVER summed into `total`.
    pending: float | None = None            # $M
    pending_span: str | None = None
    tags: str | None = None                 # which tag(s) actually answered
    note: str | None = None

    model_config = {"frozen": True}


class PeerCapitalRow(BaseModel):
    """One peer's acquired-asset intensity, or a STATED reason it has none."""

    ticker: str
    #: The SUBJECT's own row. In the DATA rather than left to position: the markdown twin bolded
    #: row 0 while the web twin read an `is_subject` field that did not exist, so the web never
    #: marked it at all — and with no subject present, row 0 is a PEER that the markdown would have
    #: bolded as if it were the name. Two positional conventions that can drift, replaced by one
    #: fact both renderers read.
    is_subject: bool = False
    market_cap: float | None = None      # $M, from the CIQ comps grid
    acquired: float | None = None        # $M, goodwill + intangibles (EDGAR, latest instant)
    total_assets: float | None = None    # $M, EDGAR `Assets`, latest instant
    pct_assets: float | None = None      # acquired / total assets
    pct_market_cap: float | None = None  # acquired / market cap
    #: WHY this row has no figures — and the three reasons are NOT the same fact.
    #: "unresolved" (no CIK), "fetch-failed" (EDGAR unreachable) and "no-tag" (the filer genuinely
    #: reports neither goodwill nor intangibles — Freshpet, an organic grower) must never collapse
    #: into one sentence. #362 exactly: a failed fetch reading as "carries none" is the reassuring
    #: wrong answer.
    note: str | None = None
    #: Did they WRITE DOWN what they carry — the half the balance columns above cannot answer.
    #: `None` only when the row has no figures at all (unresolved / fetch-failed); a resolved peer
    #: always gets one of the four states, because "never impaired" is an answer and not a gap.
    impairment: PeerImpairment | None = None

    model_config = {"frozen": True}


class PeerCapitalIntensity(BaseModel):
    """How acquisitive this balance sheet is versus its peer set — on BOTH denominators.

    TWO DENOMINATORS, AND THE CHOICE IS NOT COSMETIC. Against MARKET CAP a cheap stock shows a high
    ratio on identical accounting, so SMPL's 166% is partly $1.5bn of goodwill and partly a market
    cap that halved — using it alone would measure the de-rating the thesis argues is an overshoot.
    Circular. Against TOTAL ASSETS it measures how acquisitive the balance sheet IS, which is the
    property that is actually comparable. Market cap sizes the exposure; assets make the judgement.

    AND THE MEDIAN IS GIVEN TWICE. The set spans $49M to $30.1bn: a $49M distressed name's ratio
    says nothing about a $1bn one, and a median across that range inherits exactly the
    heterogeneity this metric exists to settle."""

    rows: list[PeerCapitalRow]
    size_floor: float                    # $M market cap for the "large peers" median — STATED
    subject_pct_assets: float | None = None
    subject_pct_market_cap: float | None = None
    median_all_assets: float | None = None
    median_all_market_cap: float | None = None
    median_large_assets: float | None = None
    median_large_market_cap: float | None = None
    n_all: int = 0
    n_large: int = 0

    #: DOES THE SECTOR WRITE DOWN WHAT IT CARRIES — the base rate §M3 records as missing.
    #: The denominator is `imp_n_large_assessed`, NOT `n_large`: a peer whose window holds no
    #: annual observation (CPB) was not measured, and counting it as a clean year would manufacture
    #: the reassuring answer out of an absence.
    imp_window_years: int = 0
    imp_n_large_assessed: int = 0        # large peers in state `charged` or `explicit-zero`
    imp_n_large_charged: int = 0         # of those, how many took a charge
    imp_median_large_pct: float | None = None   # median charge / acquired, over CHARGED large peers
    imp_subject_pct: float | None = None
    imp_subject_state: str | None = None

    model_config = {"frozen": True}


class MechanicalLayer(BaseModel):
    """The deterministic, source-bound facts — the ONLY input the synthesis LLM is given."""

    valuation: Valuation
    quality: Quality
    concentration: Concentration
    #: (A2b) THE EV-GAP FORM — route, ratios, both shape labels, and BOTH panel vintages.
    #:
    #: A FREE-FORM dict rather than a typed model, and that is deliberate for exactly one release:
    #: `build_ev_gap` returns a `status`-tagged shape whose branches differ (`not-computed` carries
    #: a reason and no ratios), and freezing that into a model before the render exists would pin
    #: a shape the render has not yet argued with. It is machine-complete in the JSON either way.
    #: TYPE IT when A2's render lands and the consumed keys are known — recorded so this is a
    #: decision with a trigger, not a shortcut that quietly becomes permanent.
    #:
    #: OPTIONAL WITH A None DEFAULT — forward-binding, the `consensus_levels` precedent. None means
    #: NOT YET REFRESHED. It is NOT the same as the computed `status="not-computed"`, which means
    #: the refresh RAN and could not strike a gap, and says why. The render must tell them apart:
    #: one asks for a refresh, the other is a finished answer.
    ev_gap: dict[str, Any] | None = None
    peer_comps: PeerComps  # comparable-company multiples + composition + deltas (consensus-resist)
    drawdown_cause: DrawdownCause
    idiosyncratic_vs_shared: IdiosyncraticVsShared
    consensus_context: ConsensusContext
    # Horizon-matched estimates/guidance/revision-event view (the five previously-unparsed CIQ
    # Estimates sheets). Optional-with-default ONLY for back-compat: a dossier.json predating this
    # field must still round-trip (the flags-PR precedent). A FRESH assembly ALWAYS builds it — the
    # fail-loud lives one level down (each sub-field is UNKNOWN/MISSING when its sheet is absent).
    catalyst_path: CatalystPath | None = None
    # (catalyst calendar, ratified 2026-07-24) dated upcoming events + what each tests — assembled
    # deterministically (print cadence, guide checkpoints, in-horizon maturities). Optional-with-
    # default for back-compat: old JSON round-trips; a FRESH assembly always builds it.
    catalyst_calendar: CatalystCalendar | None = None
    # B2 unified leverage & survival (both bases labeled + peer median + credit health) and B3 CIQ
    # implied valuation (posed, no computed %). Optional-with-default for back-compat: old JSON
    # round-trips (its Quality leverage lines render as the fallback); a FRESH assembly builds both.
    leverage_survival: LeverageSurvival | None = None
    implied_valuation: ImpliedValuation | None = None
    # (E1) structured capital structure — instruments + aggregates + survival reads. Optional-with-
    # default for back-compat: old JSON falls back to Quality.liquidity_covenant_flags (the string).
    capital_structure: CapitalStructure | None = None
    # Capital CREATED or DESTROYED — goodwill/intangibles remaining (impairment headroom), buyback
    # economics, acquisition consideration. EDGAR XBRL only; every value names the tag that
    # answered and every absence names the family tried. Optional-with-default for back-compat:
    # committed dossiers predate it and must round-trip; a FRESH assembly always builds it.
    capital_allocation: CapitalAllocation | None = None
    # FORWARD dilution capacity — S-3/F-3 shelfs, 424B supplements, S-1/F-1, S-8 — from the EDGAR
    # filing index, window-bounded at the as-of. The mirror of the buyback block above: one side
    # retires shares, this side registers the capacity to issue them. Optional-with-default for
    # back-compat: committed dossiers predate it and must round-trip; a FRESH assembly always
    # builds it (its absent state is "none on file", never a missing block).
    dilution_pipeline: DilutionPipeline | None = None
    # WHO IS ACCUMULATING — Schedule 13D/G. The register side above says how many shares COULD be
    # issued; this side says who has been buying the ones outstanding. Optional-with-default for
    # back-compat: committed dossiers predate it and must round-trip byte-identically; a FRESH
    # assembly always builds it (its empty state is "none in window", never a missing block).
    ownership_events: OwnershipEvents | None = None
    # The ONGOING dilution engine, beside the register (`dilution_pipeline`) and who is filing on
    # it (`ownership_events`). Optional-with-default for back-compat; a FRESH assembly builds it.
    sbc: SbcLine | None = None
    # Peer acquired-asset intensity — the comparison that says whether the subject's
    # goodwill+intangibles load is unusual for its sector or exactly what it looks like.
    # Optional-with-default for back-compat; a FRESH assembly builds it when the comps
    # grid is present (it needs peer tickers, which only that grid supplies).
    peer_capital_intensity: PeerCapitalIntensity | None = None
    # C — the Financial-Summary appendix (actuals + consensus fusion). Optional-with-default for
    # back-compat: old JSON round-trips; a FRESH assembly builds it (sub-fields fail loud if empty).
    financial_summary: FinancialSummary | None = None
    # (RC-1 C) primary-source extraction (99.1 release + 10-Q sections) + derived cross-source
    # surfaces. Optional-with-default for back-compat: old JSON round-trips (no primary-source).
    primary_source: PrimarySource | None = None
    management_commentary: Sourced[str]  # earnings-call transcript — QUALITATIVE only, no numbers
    # (Phase-2) the Motilal-style key-ratios panel — latest RoE / RoCE / RoA + total-debt/equity +
    # current ratio + dividend, from the CIQ Ratios sheet. Optional-with-default for back-compat.
    key_ratios: Sourced[str] | None = None
    # (Phase-4) the Motilal Ratios panel as a PER-PERIOD series — RoE / RoCE / RoA % +
    # total-debt/equity + current ratio + dividend, one column per fiscal period. Feeds the
    # return-ratios line exhibit + YoY table. The three return-ratio rows carry structured
    # `values` (raw CIQ decimals); the chart reads those, x-ratios/dividend are table-only.
    # ACTUALS ONLY — CIQ has no forward ratio columns here (no consensus splice). Pre-P4 opt.
    return_ratios: Sourced[FinTable] | None = None
    # (Phase-2) the market-data 'stock info' box — CMP + 52-week range + shares + book value + cap,
    # each source-bound (EOD / EDGAR / CIQ). Optional-with-default for back-compat.
    stock_info: StockInfo | None = None
    # (Brief) the 52-week rebased price path — the name vs the IWM benchmark, both indexed to 100.
    # Feeds the Brief-card stock-performance exhibit; visualizes the G2 idio EOD closes (assemble,
    # never conclude). Optional-with-default for back-compat; None when the name has no window bars.
    stock_performance: StockPerformance | None = None
    # (PR-B) operating-driver mechanism facts — anchored EX-99.1/10-Q/CIQ-KD rows (+ gated
    # transcript LLM-fenced). Optional-with-default for back-compat: old JSON round-trips; a fresh
    # assembly builds it (empty rows + a qa_flag when every source misses — fail-honest).
    operating_drivers: OperatingDriversExtract | None = None

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


class DrawAgreement(BaseModel):
    """How many independent synthesis draws this build took, and whether they landed on one label.

    WHY IT EXISTS (measured 2026-09-23/26). The synthesis is sampled, and no request parameter can
    make it reproducible — `temperature`/`top_p`/`top_k` are REMOVED on this model family and answer
    a 400 (`vinci/graph/llm.py`). Asked five times on identical inputs, LLY returned one label 5/5,
    AMZN 4/5 and GOOGL 3/5, so a page could publish a machine proposal that a re-run would not
    reproduce — and nothing on the page said which kind of name the reader was looking at.

    THIS IS A TALLY, NOT A RATE. Five draws cannot support a percentage: 3-of-5 carries a 95%
    confidence interval of roughly [23%, 88%]. It records what happened on THIS build, and consumers
    must render it as a count with its boundary, never as "60% stable".
    """

    attempted: int  # draws asked for
    completed: int  # draws that returned a usable tool call (a 4.8-era incomplete call is a MISS)
    labels: dict[str, int]  # lean label -> how many completed draws produced it
    unanimous: bool  # every COMPLETED draw agreed; the publish gate for the machine proposal

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
    # Reproducibility of THIS build's read. None = the single-draw path (every pre-2026-09-26
    # artifact, and any caller that asks for one draw) — absence means "not measured", never
    # "agreed". It is a measurement of the draws, NOT a verdict: the no-verdict line is unmoved.
    draw_agreement: DrawAgreement | None = None

    model_config = {"frozen": True}

    @model_serializer(mode="wrap")
    def _omit_unmeasured_draw_agreement(
        self, handler: Callable[[Synthesis], dict[str, Any]]
    ) -> dict[str, Any]:
        """Drop ``draw_agreement`` from the JSON when it is None, rather than writing a null.

        TWO REASONS, and the first is a hard invariant. `refresh_dossier` decides whether to rewrite
        by comparing SERIALIZED TEXT (`new_json != path.read_text()`), so a new key — even a null —
        makes a no-op refresh rewrite every committed dossier and
        `test_a_noop_refresh_is_byte_identical` fails. Omitting the unmeasured case keeps all 23
        committed artifacts byte-identical through this change; only a build that actually took
        multiple draws gains the key.

        The second reason is meaning: ABSENT and "agreed" must not look alike. A reader (or a
        consumer) meeting no key learns the read was never re-drawn, which is exactly the state the
        single-draw path is in — writing `null` would invite `.get("unanimous")` to read falsey and
        be mistaken for a measurement.
        """
        data = handler(self)
        if data.get("draw_agreement") is None:
            data.pop("draw_agreement", None)
        return data


class PriceStoreStamp(BaseModel):
    """WHICH price store a dossier was built from, and how far it reached.

    THE RESOLVED PATH IS THE IDENTITY, AND THE DECLARED ONE IS ALSO INFORMATION. This checkout's
    `data/vinci.db` is a SYMLINK to another worktree's store, so the two paths differ while the
    bytes are the same file. Stamping only the declared path would make two dossiers built from
    ONE store look like they came from two; stamping only the resolved path would hide that this
    worktree is reading someone else's data. Both, and a reader can tell either way.

    That symlink is not a hypothetical detail: a corroboration check for BRBR's $11.56 was run
    against `data/vinci.db` here, reported that the store could not see the price, and was wrong
    about WHICH store it had just asked.

    `frontier` is the store's newest bar across every name — the last moment its price data
    actually reaches, and the number that decides whether an as-of can be checked here at all.
    """

    declared_path: str          # the path as configured, e.g. "<worktree>/data/vinci.db"
    resolved_path: str          # symlinks followed — the identity two stamps compare on
    frontier: date | None       # newest bar date in the store; None when it holds no bars

    model_config = {"frozen": True}


class Dossier(BaseModel):
    """A per-finalist dossier: source-bound mechanical facts + fenced synthesis. Assembles, cites;
    never concludes. The human's BUY/AVOID verdict is logged separately via the ledger CLI."""

    ticker: str
    name: str
    cik: str
    reference_date: date
    rank: int | None  # position in the ranked queue — ordering context, never a verdict on the name
    # WHICH STRATEGY BOOK this name is judged under (`vinci/sleeves.py`; STATE.md §4 SLEEVE
    # ARCHITECTURE). NOT a verdict and not a rank — it names the QUESTION the page answers, which
    # is why an untagged megacap was being asked what broke when nothing had. Defaulted rather than
    # required so every dossier committed before the tag existed still round-trips, and `overshoot`
    # is the truthful answer for all of them: the screen is the only route those names had.
    # VALIDATED ON THE MODEL, not only at the followed.json edge — the `bear_basis` precedent
    # (`vinci/scenarios.py`). The value is PERSISTED and read back, so edge-only validation leaves
    # every other writer free to put an unlisted strategy into a committed artifact; a reader would
    # then meet a sleeve no registry row defines, and Phase 2 would have no framing to apply.
    sleeve: str = DEFAULT_SLEEVE
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
    assembled_at: datetime  # UTC-aware build stamp (rendered with time + "UTC"); legacy JSONs naive
    # (26a) WHICH EXTRACTOR produced this document — see vinci.dossier.extraction_version. The
    # assembly DATE says when; this says WITH WHAT, which is the question "are these two dossiers
    # comparable?" actually turns on (#238 left the fleet holding two vintages that dated alike).
    # Default None so dossiers committed before 26a round-trip byte-identically; absent renders as
    # "unstamped" on BOTH twins rather than as nothing, because "vintage unknown" and "no
    # divergence" must not look the same to a reader.
    extraction_version: str | None = None
    # (spot audit, 2026-08-11) WHICH PRICE STORE produced this document. `extraction_version` says
    # with WHAT code, `assembled_at` says WHEN — this says FROM WHICH DATA, the third leg of "are
    # these two dossiers comparable?" and the one nothing recorded.
    #
    # IT IS NOT DRIFT, WHICH IS WHY A STAMP IS THE WHOLE ANSWER. `data/` is per-worktree BY DESIGN
    # (STATE §DATA-TOPOLOGY), so three checkouts holding three frontiers — 2026-08-04, 2026-08-07,
    # 2026-08-05 — is the documented arrangement working, not divergence to repair. What follows is
    # that a reader cannot infer the data behind a page FROM the page: two names assembled the same
    # day out of different worktrees are struck days apart with nothing saying so. Comparability
    # today rests on reference dates happening to lag every frontier — a coincidence, not a
    # guarantee. Default None so committed JSON predating the field round-trips byte-identically.
    price_store: PriceStoreStamp | None = None
    # (teaser/company) Brief-teaser + company-overview context: the SIC-derived coarse sector (the
    # CIQ-GICS fallback), the CIQ GICS Primary Industry Classification (source-bound), the exchange,
    # and the CIQ subject business description. Assemble/inform only — never a gate/rank input.
    # Default None so committed JSON predating these fields still round-trips.
    sector: str | None = None
    industry: Sourced[str] | None = None
    exchange: str | None = None
    business_description: Sourced[str] | None = None
    # (mid-cycle) the cyclical-underwriting record — own/peer margin anchors, EV/EBITDA band, the
    # analyst's scenario grid + the reward/risk ratio (vinci.dossier.midcycle). Default None so a
    # committed dossier.json without it round-trips byte-identically; when absent the render emits
    # nothing (the section is gated on presence).
    midcycle: MidCycle | None = None
    # (anchor) the R1 mid-cycle-margin × own-history-EV/EBITDA fundamental, PERSISTED source-bound
    # so triage is a cheap read (vinci.dossier.anchor). Spot-independent; an ATTENTION FILTER, not
    # a verdict. Default None so a committed dossier.json without it round-trips byte-identically;
    # the UI ignores it for now (data-only).
    anchor: Anchor | None = None

    @field_validator("sleeve")
    @classmethod
    def _sleeve_known(cls, v: str) -> str:
        """An unlisted strategy never reaches a committed artifact.

        The followed-name edge validates too, but that is ONE writer. This is the model every
        writer goes through, and the value is persisted and read back — so edge-only validation
        would leave a reader meeting a sleeve no registry row defines, with no framing to apply.
        Re-raised as ``ValueError`` so it surfaces as an ordinary pydantic validation error at the
        boundary where the field is set, with the registry's own message (which names the
        admissible set) kept intact."""
        try:
            return require_sleeve(v, where=f"{cls.__name__}.sleeve")
        except UnknownSleeveError as exc:
            raise ValueError(str(exc)) from exc

    model_config = {"frozen": True}


#: OPTIONAL-ADDED-LATER mechanical keys that are OMITTED when None, rather than written as
#: `"<key>": null`. That key would assert WE COMPUTED THIS AND GOT NOTHING when the truth is the
#: dossier predates the field: ABSENT means NOT YET REFRESHED. `(parent field or "" for the
#: mechanical root, key)` — `ebitda_basis` sits one level deeper, a property of the
#: financial-summary TABLE rather than of the layer, so each entry names its own parent.
#: Moved here from `vinci/dossier/refresh.py` with `dossier_json` below, which both writers use.
DROP_WHEN_NONE: tuple[tuple[str, str], ...] = (
    ("concentration", "segment_profit"),
    ("consensus_context", "consensus_levels"),
    ("financial_summary", "ebitda_basis"),
    ("", "capital_allocation"),
    ("", "peer_capital_intensity"),
    ("", "dilution_pipeline"),
    ("", "ownership_events"),
    ("", "sbc"),
)


def dossier_json(doc: Dossier) -> str:
    """THE ONE SERIALIZER for a committed `dossier.json` — the assembler and the refresh path both
    write through it, so a no-op refresh cannot rewrite bytes the assembler produced.

    THEY WERE TWO. The assembler wrote `model_dump_json(indent=2)` (pydantic) and the refresh path
    re-dumped the same payload with `json.dumps` after pruning absent keys. The two agree on every
    value the committed corpus happened to hold until PARR's page carried a dilution item at
    0.0000245 of assets: pydantic writes that in decimal, `json.dumps` writes `2.45e-05`, so a
    no-op refresh of PARR rewrote two lines with zero semantic change. Same class as the unicode
    escaping the pruning comment already named — one artifact, one writer, is the only fix that
    does not need a second one later.

    The pruning survives as an `exclude` mapping, computed from the values rather than hardcoded:
    a key is dropped only when it IS None, so a name that HAS the field still writes it.
    """
    mech = doc.mechanical
    root: dict[str, Any] = {}
    for parent, key in DROP_WHEN_NONE:
        holder = getattr(mech, parent, None) if parent else mech
        if holder is None or getattr(holder, key, "absent") is not None:
            continue
        if parent:
            root.setdefault(parent, set()).add(key)
        else:
            root[key] = True
    excl: dict[str, Any] = {"mechanical": root} if root else {}
    # the anchor's mid-cycle gap is set only when it fires; an anchor that does not fire writes no
    # key, so every committed page it does not apply to stays byte-identical
    if doc.anchor is not None and doc.anchor.midcycle_gap is None:
        excl["anchor"] = {"midcycle_gap"}
    return doc.model_dump_json(indent=2, exclude=excl or None)
