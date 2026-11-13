"""The decision-ledger entry — one recorded verdict per candidate the discriminator judges.

The discriminator itself is **manual** (the PM's A/B/C source-binding + CIQ process). This schema
is only the *record* of its verdict. Two disciplines are load-bearing for the validation:

1. **Log AVOIDs as well as BUYs** — the AVOID-terminal verdicts are half the validation set; the
   primary metric is the BUY−AVOID forward-return spread, which needs both legs.
2. **Freeze the entry price + as_of at decision time** — the scoring harness measures forward
   return from this frozen point, so it must be stamped once and never moved.
"""

from __future__ import annotations

import enum
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_serializer, model_validator

# The non-decision events a ledger row may record, each an APPENDED row, never an edit: a close,
# a correction of a decision's entry (RF-D7, operator ruling 2026-11-09), and a VOID of a decision
# (operator ruling 2026-11-11 on GOOGL's BUY).
EVENT_CLOSE = "CLOSE"
EVENT_CORRECTION = "CORRECTION"
EVENT_VOID = "VOID"

# NOTE (item 18a, review finding): there is deliberately NO `FACTS_AVAILABLE_FROM` constant here.
# The first cut declared one, citing the BASIS_REQUIRED_FROM / FIELDED_REFS_FROM pattern — but
# those are READ by real version gates in vinci/scenarios.py, and nothing read this one. It could
# not be read, either: those constants mark a version from which a field becomes REQUIRED, and
# `facts` is permanently optional (a verdict that types nothing is still a verdict). A constant
# that looks like a guard and enforces nothing is worse than no constant, so the forward-binding
# property is stated where it is actually true — on the field, and in the test that pins that no
# committed row was backfilled.

# Close-row id convention. The decision row is "V-{candidate_id}" and re-logging it fails loud —
# that uniqueness rule is what makes the ledger append-only in practice. It is widened HERE, once
# and deliberately: a candidate may carry exactly one decision row and one close row.
CLOSE_ID_PREFIX = "C-"


def close_entry_id(candidate_id: str) -> str:
    """The close row's id for ``candidate_id``'s FIRST decision (``follow_up_id`` names every
    close the writer appends)."""
    return f"{CLOSE_ID_PREFIX}{candidate_id}"


# Correction-row id convention, widened once more (RF-D7): one correction per decision, by
# construction — a second is refused at the writer and collides on the primary key besides.
CORRECTION_ID_PREFIX = "R-"


# Void-row id convention: one void per decision, named from the DECISION's own id ("V-GOOGL" ->
# "X-GOOGL"), so it is unique wherever the decision is.
VOID_ID_PREFIX = "X-"
DECISION_ID_PREFIX = "V-"


def decision_entry_id(candidate_id: str, n: int = 1) -> str:
    """The ``n``-th decision's id for ``candidate_id``: ``V-{candidate}``, then
    ``V-{candidate}-{n}`` (operator ruling 2026-11-11). A candidate holds ONE open decision at a
    time (`log_verdict` refuses a second); a fresh one is logged only after the earlier is closed
    or voided — GOOGL's voided BUY is ``V-GOOGL``, a fresh GOOGL decision ``V-GOOGL-2``."""
    return f"{DECISION_ID_PREFIX}{candidate_id}" + (f"-{n}" if n > 1 else "")


def follow_up_id(prefix: str, decision_entry_id: str) -> str:
    """A row that follows a decision — its close (``C-``), correction (``R-``) or void (``X-``) — is
    named from the DECISION's id, so a candidate's second decision gets its own (``C-GOOGL-2``).
    For every first decision the name is the candidate-keyed one it always was (``C-{candidate}``).
    Given the decision's id, never a candidate's: a candidate id may itself start with ``V-``
    (a screen candidate of Visa is ``V-screen2-…``), and stripping it would mis-name the row."""
    if not decision_entry_id.startswith(DECISION_ID_PREFIX):
        raise ValueError(f"{decision_entry_id!r} is not a decision id ({DECISION_ID_PREFIX}…)")
    return f"{prefix}{decision_entry_id[len(DECISION_ID_PREFIX):]}"


def void_entry_id(decision_entry_id: str) -> str:
    """The void row's id for decision ``decision_entry_id``."""
    return follow_up_id(VOID_ID_PREFIX, decision_entry_id)


# THE PRE-REGISTERED VOID REASONS (operator, 2026-11-13, #1004 item 5: "yes need to do this
# reliably"). A void takes a decision out of every curve, so it is allowed only where the row never
# measured the call it records: its entry price was wrong when sealed, it names the wrong
# instrument, or the wrong issuer. A CHANGE OF MIND IS A CLOSE, and a close stays scored to its
# horizon (the 2026-08-12 ruling) — were it a void, every losing call could be ruled out of the
# spread after the fact, and the spread would measure nothing. Registered here BEFORE any void is
# written under it; X-GOOGL (2026-11-11) predates the list, carries no code, and stays as written.
VOID_DATA_ERROR_AT_ENTRY = "data_error_at_entry"
VOID_WRONG_INSTRUMENT = "wrong_instrument"
VOID_WRONG_IDENTITY = "wrong_identity"
VOID_REASONS = frozenset({VOID_DATA_ERROR_AT_ENTRY, VOID_WRONG_INSTRUMENT, VOID_WRONG_IDENTITY})

# THE READING FLOOR (coined 2026-11-13, #1004 item 5): a book's curve is READ — its spread printed
# in the report — only once that book holds this many resolved observations. Below it the report
# prints the count and no reading. WHY 20: with a handful of names one outcome moves a mean by tens
# of points, so an early curve reads as a result when it is one draw; at 20 each name carries a
# twentieth of an equal-weight mean, the face-validity point at which no single outcome is the
# reading. B's default under the delegation record, agreed by A on #1004. A DISPLAY RULE ONLY:
# the computed spread (`ScoreReport` and its JSON) is unchanged, and the number was set by face
# validity, never by any outcome — no resolved outcome existed when it was registered.
READING_FLOOR = 20


class OriginRef(BaseModel, frozen=True):
    """WHERE a decision's name came from, named (2026-11-13, #1004 item 5). ``origin`` says only the
    route (screen or followed); this names the run or the entry, so a row can be traced back to
    the screen run that admitted it or the follow decision that covered it. Sealed at log time on
    every new row; ``None`` on a row logged before it, which is every committed row.

    ``screen_run`` names the candidate record (``id`` is its ``candidate_id``) and the run's own
    timestamp and screens; ``follow_entry`` names the follow-list entry (``id`` is its ticker) and
    its ``followed_since``. No route logs a theme-originated decision today (`vinci.themes` retired
    2026-11-04; the `theme` book is not ledger-active), so a theme kind is added with the route that
    writes one, not before."""

    kind: Literal["screen_run", "follow_entry"]
    id: str
    screen_run_at: datetime | None = None   # screen_run only
    screens_fired: tuple[str, ...] = ()     # screen_run only
    followed_since: date | None = None      # follow_entry only

    @model_validator(mode="after")
    def _shape(self) -> OriginRef:
        if not self.id.strip():
            raise ValueError("an origin names its run or entry — a blank id names nothing")
        if self.kind == "screen_run" and (self.screen_run_at is None
                                          or self.followed_since is not None):
            raise ValueError("a screen-run origin states the run's screen_run_at, and no "
                             "followed_since")
        if self.kind == "follow_entry" and (self.followed_since is None
                                            or self.screen_run_at is not None
                                            or self.screens_fired):
            raise ValueError("a follow-entry origin states its followed_since, and no screen run")
        return self


#: The fields added 2026-11-13 (#1004 item 5). Each is WRITTEN ONLY WHEN SET, as `machine_tally`
#: is, so a row logged before them re-serializes byte for byte.
_OMIT_WHILE_UNSET = ("machine_tally", "origin_ref", "underwrite_commit", "underwrite_sha256",
                     "ratio_at_entry_undefined", "no_underwrite_reason", "void_reason_code")


class VoidMark(BaseModel, frozen=True):
    """A voided decision's RESULT TO DATE, sealed in its void row when it is voided — the monitor's
    own mark of the decision at the last session it could read, so the removal can be seen and can
    never read as a hidden loser. The entry is the one the decision was READ at (its correction's,
    when corrected), its price on the mark's split basis as the monitor's row states it; the returns
    are on ``return_basis``."""
    entry_price: float
    entry_date: date
    as_of: date
    price: float
    position_return: float
    benchmark: str
    benchmark_return: float
    excess: float
    return_basis: str


# How a name reached the ledger. SCREEN = through the $300M–$10B hunting ground; FOLLOWED = an
# operator follow decision, deliberately outside the band. The PRIMARY spread counts SCREEN only.
ORIGIN_SCREEN = "screen"
ORIGIN_FOLLOWED = "followed"
ORIGINS = frozenset({ORIGIN_SCREEN, ORIGIN_FOLLOWED})


def origin_of(entry: LedgerEntry) -> str:
    """The row's route, with the legacy row's TRUTHFUL default rather than a guess.

    A row logged before the field existed is necessarily screen-origin: ``log_verdict`` refused any
    name without a ``CandidateRecord``, so no other route could reach this ledger at all. Reading
    through here rather than off the attribute is what lets the spread filter treat legacy and
    tagged rows identically — the alternative is `or ORIGIN_SCREEN` repeated at every call site,
    which is the drift shape this repo refuses."""
    return entry.origin or ORIGIN_SCREEN


def sleeve_of(entry: LedgerEntry) -> str:
    """The row's strategy book, defaulting a legacy row to the only strategy that then existed.

    Imported lazily so this module keeps importing nothing from the sleeve registry at module
    scope — ``vinci.sleeves`` is a leaf, but the ledger schema is imported by almost everything and
    the no-extra-imports property here is load-bearing for the AST guards."""
    from vinci.sleeves import DEFAULT_SLEEVE

    return entry.sleeve or DEFAULT_SLEEVE


class Verdict(enum.StrEnum):
    """Every verdict any sleeve records. WHICH ones a given book may use is the sleeve's own
    vocabulary (``vinci/sleeves.py``), enforced at write time — this enum is the union, not a menu.

    THE NEGATIVE LEG IS PER-BOOK, and that is the whole reason this grew past two. "Terminal
    decline" is the overshoot twin; recording it against a fully-priced compounder would be a FALSE
    RECORD in an append-only ledger, which is why ``quality`` gets ``PASS`` rather than reusing
    ``AVOID_TERMINAL``. A verdict outside its sleeve's vocabulary is refused before the seal."""

    BUY = "BUY"  # overshoot — the de-rating is exaggerated-and-temporary; a reversal is nameable
    AVOID_TERMINAL = "AVOID_TERMINAL"  # the overshoot twin — real-and-permanent decline; no trade
    # The QUALITY twin — the business is sound and the PRICE already pays for it. Deliberately not
    # an AVOID_*: it says "not at this price", never "this is dying", and the underwrite record
    # already carried the concept (`VerdictStatus` literal "passed", `Verdict.avoid_priced`).
    PASS = "PASS"


class Confidence(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Disposition(enum.StrEnum):
    """How the human's verdict relates to the machine's sealed proposal (the 2026-07-13 pivot).

    Stamped at log time by ``log_verdict`` — never recomputed later — so the ledger accumulates
    THREE readable curves: the human-final spread (primary), the machine-proposal spread, and the
    override subset (the most informative disagreement data). ``None`` on an entry == logged
    before the pivot existed."""

    CONFIRMED = "confirmed"  # human verdict == machine proposal
    OVERRIDDEN = "overridden"  # human verdict != machine proposal — the disagreement set
    NO_PROPOSAL = "no_proposal"  # machine abstained (mixed / no read) — human decided cold


class LedgerFact(BaseModel, frozen=True):
    """One source-bound fact a verdict rested on — TYPED, beside the prose, never instead of it.

    WHY THIS EXISTS (item 18a). The item-18 scope check found all three regression-trio facts —
    loan-basis leverage, impairment quantum, buyback pace — living ONLY inside the ``thesis``
    string: VRRM's row carries "68% of EBITDA at ~65% margins" as prose, SMPL's carries its
    guidance range the same way. A guard that must compare the record's facts against the dossier's
    therefore had no usable input. **That is the WRITE PATH'S SHAPE, not one badly-written entry:**
    ``log_verdict`` takes ``thesis: str``, so the next payload is phrased differently by
    construction and no regex over it can be correct.

    Deliberately the same four fields as ``vinci.scenarios.Fact`` — ``basis`` names WHAT the number
    is, ``source`` names WHERE it came from — so a reader moving between the underwrite record and
    the ledger meets one shape, not two. ``source`` is REQUIRED and must be non-blank: a fact whose
    provenance is unstated cannot be verified against a filing, and an unverifiable fact in the
    append-only record is worse than no field at all.
    """

    value: float
    unit: str    # "$M" | "x" | "%" | "shares" | "$/share"
    basis: str   # e.g. "loan-basis net leverage, lease-inclusive (FY2025)"
    source: str  # e.g. "10-K acc 0000793074-26-000071 — Note 9, long-term debt"

    @field_validator("unit", "basis", "source")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "a ledger fact needs its unit, basis and source — refusing to seal a number into "
                "an append-only record with no way to check it against a filing"
            )
        return v


class LedgerEntry(BaseModel, frozen=True):
    """A single recorded paper verdict. Append-only; never mutated after logging."""

    entry_id: str
    candidate_id: str  # links back to the CandidateRecord that was judged
    internal_id: str  # the security judged
    ticker: str
    # Sector (coarse GICS-like, from EDGAR SIC) — captured at log time so the spread can be read
    # PER-SECTOR (where the edge is real). Optional: None == a verdict logged before sector-tagging
    # existed (VRRM). Frozen with the verdict; never derived later.
    sector: str | None = None
    # --- WHICH BOOK, AND HOW THE NAME GOT IN (2026-08-09; STATE.md §4 SLEEVE ARCHITECTURE) ------
    # ``origin`` is the ROUTE the name arrived by — ORIGIN_SCREEN (the $300M–$10B hunting ground)
    # or ORIGIN_FOLLOWED (an operator follow decision, deliberately out of band). ``sleeve`` is the
    # STRATEGY BOOK the verdict is a claim under (`vinci/sleeves.py`).
    #
    # TWO FIELDS AND NOT ONE, because they answer different questions and the PRIMARY BUY−AVOID
    # SPREAD KEYS ON ORIGIN: the spread is the fund's proof and it measures the discriminator ON
    # the hunting ground, so pooling megacap verdicts into it silently changes what the number
    # means. Every other cut accumulates as its own labelled curve beside it — the same shape as
    # the machine-proposal-vs-human-final split (operator decision 2026-08-07).
    #
    # Optional-with-default, the precedent every field above follows: None == a verdict logged
    # before these existed, which is every committed row. Their meaning for those rows is the
    # truthful one — the screen was the ONLY route that could reach this ledger (``log_verdict``
    # refused anything without a CandidateRecord), and overshoot the only strategy. Read them via
    # :func:`origin_of` / :func:`sleeve_of` so a legacy row and a tagged row answer identically.
    origin: str | None = None
    sleeve: str | None = None
    # The run or entry the route names (`OriginRef`); written only when set.
    origin_ref: OriginRef | None = None

    verdict: Verdict
    twin_call: str  # how the twin was ruled out / why it is the twin (the central judgement)

    # Frozen at decision time — the anchor for forward-return scoring.
    entry_price: float
    entry_price_as_of: date
    # The asymmetry the call was made ON, frozen beside the price it was made AT. The underwrite
    # record it came from is editable; this copy is not — so the forward return is always readable
    # against the ratio actually accepted. ``None`` == a verdict logged without an underwrite grid.
    ratio_at_entry: float | None = None
    # Pointer to the underwrite record that justified this row (e.g. "scenarios/IT.json") — the
    # ledger says WHAT was decided; the record says how the numbers were built. None: no record.
    underwrite_ref: str | None = None
    # --- THE UNDERWRITE SEAL (2026-11-13, #1004 item 5) -----------------------------------------
    # Until now no code wrote the two fields above: the three committed rows that carry them were
    # hand-authored, and IT's 6.69 was struck on a record since superseded. `log-verdict` now reads
    # the LIVE `scenarios/<T>.json` and seals the path (``underwrite_ref``), the commit it was read
    # at and the sha256 of its bytes (which must equal that commit's blob), and ``ratio_at_entry``
    # recomputed by the record's own recipe at the frozen entry price. A record whose ratio is
    # undefined at that price seals None with the recipe's reason. A decision with no live record
    # states why in ``no_underwrite_reason``, or it is refused. All written only when set.
    underwrite_commit: str | None = None
    underwrite_sha256: str | None = None
    ratio_at_entry_undefined: str | None = None
    no_underwrite_reason: str | None = None

    thesis: str  # short written thesis (BUY) or rationale (AVOID)
    # (item 18a) The facts the thesis rests on, TYPED and source-stamped — ALONGSIDE the prose,
    # never replacing it. Empty on every row logged before this field existed, and empty is a
    # legitimate permanent state: this records what the analyst chose to type, and a verdict that
    # types nothing is still a verdict. Keyed by a short fact name ("loan_basis_leverage",
    # "impairment_quantum", "buyback_pace") so a consumer selects by name rather than by position.
    facts: dict[str, LedgerFact] = Field(default_factory=dict)
    kill_criteria: str  # what would falsify the thesis
    horizon_days: int  # thesis horizon in calendar days (the de-rating twin resolves in months)
    confidence: Confidence

    decided_at: datetime  # when the verdict was logged
    # The benchmark the BUY−AVOID/excess-return metrics will use (e.g. "IWM").
    benchmark: str = "IWM"

    # --- machine proposal (2026-07-13 pivot), SEALED at log time from the committed dossier ----
    # The machine's proposed verdict is a deterministic derivation of the dossier's committed lean
    # (vinci/dossier/verdict.py — face-validity mapping, never outcome-tuned). All None == a
    # pre-pivot entry; ``machine_proposal is None`` with a disposition == the machine ABSTAINED
    # (mixed / no read) on a post-pivot log. Frozen with the verdict; never derived later.
    machine_proposal: Verdict | None = None
    machine_lean: str | None = None  # the lean label the proposal derived from (None: no read)
    proposal_assembled_at: datetime | None = None  # WHICH dossier artifact proposed (its stamp)
    # THE SPLIT THE SEALED PROPOSAL STANDS ON (the vote rule's R4, 2026-11-11): the page's own
    # build's tally (`page`) and the ten-draw confirmation `log-verdict` draws before this row is
    # written (`confirmation`, C(iv)), each as counts with R1's bar and state — never a rate. None
    # == a row logged before the rule, which is every committed row; omitted from the JSON while
    # None, so those rows re-serialize byte for byte.
    machine_tally: dict[str, Any] | None = None
    disposition: Disposition | None = None  # confirm/override/no-proposal; None == pre-pivot
    # Anti-anchoring provenance (2026-07-13): the brief HIDES the proposal so the human decides
    # blind; this records whether the human peeked at it (via ``--show-proposal``) BEFORE logging.
    # ``False`` in normal flow == an uncontaminated human-vs-machine comparison; ``True`` flags a
    # disposition whose CONFIRMED/OVERRIDDEN reading is anchored and must be down-weighted.
    revealed_pre_verdict: bool = False

    # --- CLOSE ROWS (2026-07-22) ---------------------------------------------------------------
    # A position is closed by APPENDING a row, never by mutating the decision row: the ledger is
    # append-only, and the entry it froze is the anchor the forward spread measures from.
    #
    # ``event`` is the discriminator. ABSENT/None == a DECISION row — which is what every legacy
    # row is, so no committed row changes. ``EVENT_CLOSE`` == a close row, which is NOT a position
    # and must never be counted as one. That is the entire reason this field exists: without it a
    # close appended for IT would be partitioned by ``compute_spread`` as a SECOND BUY leg and
    # double-count the name in the one number this fund exists to measure.
    #
    # ``verdict`` on a close row repeats the ORIGINAL call, for provenance only. Deliberately not a
    # new verdict: closing a BUY is not an AVOID, and a close row carrying its own directional call
    # would put a second, contradictory opinion into an append-only record.
    event: str | None = None                 # None = decision row · "CLOSE" = close row
    closes_entry_id: str | None = None       # CLOSE only — the entry_id being closed
    exit_price: float | None = None          # CLOSE only — the realized exit
    exit_price_as_of: date | None = None     # CLOSE only
    # WHY the position was closed, in the reader-facing register. Distinct from ``thesis``, which
    # on a decision row is the reasoning FOR the call: a close is a different act and states its
    # own grounds. Sealed by the same append-only discipline as everything else in this record —
    # the row is frozen at write.
    reason: str | None = None                # CLOSE and CORRECTION
    # --- CORRECTION ROWS (RF-D7, operator ruling 2026-11-09) -----------------------------------
    # A decision sealed on a stale close is CORRECTED by appending a row that names it here and
    # carries the corrected ``entry_price`` / ``entry_price_as_of`` in the ordinary fields — the
    # last close completed at the decision moment, one rule for every row. The decision row keeps
    # its sealed price forever; every reader of returns reads the corrected one (`corrected`), and
    # the horizon runs from the corrected date. Like a close, it is not a position.
    corrects_entry_id: str | None = None     # CORRECTION only — the decision's entry_id
    # --- VOID ROWS (operator ruling 2026-11-11, GOOGL) -----------------------------------------
    # A decision RULED OUT of the record — "done based on really old and wrong data" — is VOIDED
    # by appending a row that names it here. The decision row, its correction and its void all
    # stay as audit history; every reader of positions and returns leaves a voided decision out
    # (scoring, the curves, the monitor, the supersede guard, a close, a correction), and the void
    # row itself seals the decision's result to date (``void_mark``) and the ruling's date. Only an
    # operator's ruling applies it; the mechanism is generic.
    voids_entry_id: str | None = None        # VOID only — the voided decision's entry_id
    ruled_on: date | None = None             # VOID only — the date of the ruling
    void_mark: VoidMark | None = None        # VOID only — the result to date at the void
    # VOID only — the pre-registered ground (`VOID_REASONS`). Required of every void the writer
    # appends; None on X-GOOGL, which predates the list and is never rewritten.
    void_reason_code: str | None = None

    @model_serializer(mode="wrap")
    def _omit_unset_tally(self, handler: Any) -> dict[str, Any]:
        """``machine_tally`` and the fields of 2026-11-13 (`_OMIT_WHILE_UNSET`) are written only
        when set, so a row logged before them re-serializes byte for byte (the store re-validates
        every row it appends)."""
        data: dict[str, Any] = handler(self)
        for key in _OMIT_WHILE_UNSET:
            if data.get(key) is None:
                data.pop(key, None)
        return data

    @field_validator("void_reason_code")
    @classmethod
    def _void_reason_known(cls, v: str | None) -> str | None:
        """A code outside the pre-registered list is refused: the list IS the rule."""
        if v is not None and v not in VOID_REASONS:
            raise ValueError(
                f"void reason {v!r} is not pre-registered — a void is allowed only for "
                f"{sorted(VOID_REASONS)}. A change of mind is a CLOSE, and it stays scored.")
        return v

    @field_validator("origin")
    @classmethod
    def _origin_known(cls, v: str | None) -> str | None:
        """An unlisted route is refused, but ABSENT is legal — the two are different states.

        None means "logged before the field existed" and reads as screen through
        :func:`origin_of`. A present-but-unknown value is a typo that would silently drop the row
        out of every origin-filtered curve, which is worse than either."""
        if v is not None and v not in ORIGINS:
            raise ValueError(
                f"origin {v!r} is not one of {sorted(ORIGINS)} — a row whose route is unrecognised "
                f"falls out of the origin-filtered spreads without saying so")
        return v

    @field_validator("sleeve")
    @classmethod
    def _sleeve_known(cls, v: str | None) -> str | None:
        """Same shape as ``origin``: absent is legal, unlisted is refused, and the refusal names
        the admissible set (the registry's own message)."""
        if v is None:
            return v
        from vinci.sleeves import UnknownSleeveError, require_sleeve
        try:
            return require_sleeve(v, where=f"{cls.__name__}.sleeve")
        except UnknownSleeveError as exc:
            raise ValueError(str(exc)) from exc

    @model_validator(mode="after")
    def _close_row_shape(self) -> LedgerEntry:
        """A close row is fully specified or refused. Half a close — an exit price with no link, or
        a link with no price — yields an unpairable row that the realized view would silently drop
        instead of failing."""
        close_only = {"closes_entry_id": self.closes_entry_id, "exit_price": self.exit_price,
                      "exit_price_as_of": self.exit_price_as_of}
        if self.event is None:
            stray = sorted(k for k, v in close_only.items() if v is not None)
            if stray:
                raise ValueError(
                    f"{stray} set on a DECISION row (event is None) — those fields belong to a "
                    f"close row; set event={EVENT_CLOSE!r} or remove them")
            if self.corrects_entry_id is not None:
                raise ValueError(f"corrects_entry_id set on a DECISION row {self.entry_id!r} — it "
                                 f"belongs to a correction row (event={EVENT_CORRECTION!r})")
            self._no_void_fields("DECISION")
            return self
        if self.event == EVENT_CORRECTION:
            self._no_void_fields("correction")
            return self._correction_row_shape(close_only)
        if self.event == EVENT_VOID:
            return self._void_row_shape(close_only)
        if self.event != EVENT_CLOSE:
            raise ValueError(f"unknown ledger event {self.event!r} — expected {EVENT_CLOSE!r}, "
                             f"{EVENT_CORRECTION!r}, {EVENT_VOID!r}, or None for a decision row")
        self._no_void_fields("close")
        if self.corrects_entry_id is not None:
            raise ValueError(f"close row {self.entry_id!r} sets corrects_entry_id — a close "
                             "corrects nothing")
        missing = sorted(k for k, v in close_only.items() if v is None)
        if missing:
            raise ValueError(f"close row {self.entry_id!r} is missing {missing} — a close is "
                             "fully specified or it is refused")
        if self.exit_price is not None and self.exit_price <= 0:
            raise ValueError(f"close row {self.entry_id!r}: exit_price must be positive")
        if self.closes_entry_id == self.entry_id:
            raise ValueError(f"close row {self.entry_id!r} closes itself")
        if not (self.reason or "").strip():
            raise ValueError(f"close row {self.entry_id!r} has no reason — a position closes for a "
                             "stated reason, or the record cannot be reviewed later")
        if self.facts:
            # (item 18a) Facts belong to the DECISION they justified. A close repeats the original
            # verdict for provenance and opens no new position, so facts attached here would read
            # as a second, later-dated underwrite of the same call — the same reason a close row
            # carries no directional verdict of its own.
            raise ValueError(
                f"close row {self.entry_id!r} carries facts {sorted(self.facts)} — facts belong to "
                f"the decision row they justified ({self.closes_entry_id!r}), not to its close")
        return self

    def _no_void_fields(self, kind: str) -> None:
        """The void fields belong to a void row alone: on any other row they would read as a
        void that no reader treats as one."""
        stray = sorted(k for k, v in (("voids_entry_id", self.voids_entry_id),
                                       ("ruled_on", self.ruled_on),
                                       ("void_mark", self.void_mark),
                                       ("void_reason_code", self.void_reason_code))
                       if v is not None)
        if stray:
            raise ValueError(f"{stray} set on a {kind} row {self.entry_id!r} — they belong to a "
                             f"void row (event={EVENT_VOID!r})")

    def _void_row_shape(self, close_only: Mapping[str, object]) -> LedgerEntry:
        """A void names its decision, states its grounds and the ruling's date, seals the result
        to date, and carries no close, no correction and no facts."""
        stray = sorted(k for k, v in close_only.items() if v is not None)
        if stray or self.corrects_entry_id is not None:
            raise ValueError(f"void row {self.entry_id!r} sets "
                             f"{stray or ['corrects_entry_id']} — a void is not a close or a "
                             f"correction")
        if not self.voids_entry_id:
            raise ValueError(f"void row {self.entry_id!r} names no decision (voids_entry_id)")
        if self.voids_entry_id == self.entry_id:
            raise ValueError(f"void row {self.entry_id!r} voids itself")
        if not (self.reason or "").strip():
            raise ValueError(f"void row {self.entry_id!r} has no reason — a decision is voided "
                             "only on stated grounds")
        if self.ruled_on is None:
            raise ValueError(f"void row {self.entry_id!r} has no ruled_on — a void is applied by "
                             "an operator's ruling, and states its date")
        if self.void_mark is None:
            raise ValueError(f"void row {self.entry_id!r} has no void_mark — the result to date is "
                             "sealed with the void, so the removal can be seen")
        if self.facts:
            raise ValueError(f"void row {self.entry_id!r} carries facts — facts belong to the "
                             f"decision row ({self.voids_entry_id!r})")
        return self

    def _correction_row_shape(self, close_only: Mapping[str, object]) -> LedgerEntry:
        """A correction names its decision, states its reason, and carries no close and no facts:
        it changes one thing — the entry the decision is measured from."""
        stray = sorted(k for k, v in close_only.items() if v is not None)
        if stray:
            raise ValueError(f"correction row {self.entry_id!r} sets {stray} — a correction is not "
                             "a close")
        if not self.corrects_entry_id:
            raise ValueError(f"correction row {self.entry_id!r} names no decision "
                             "(corrects_entry_id)")
        if self.corrects_entry_id == self.entry_id:
            raise ValueError(f"correction row {self.entry_id!r} corrects itself")
        if not (self.reason or "").strip():
            raise ValueError(f"correction row {self.entry_id!r} has no reason — a correction to an "
                             "append-only record states its grounds")
        if self.facts:
            raise ValueError(f"correction row {self.entry_id!r} carries facts — facts belong to "
                             f"the decision row ({self.corrects_entry_id!r})")
        return self

    @model_validator(mode="after")
    def _sane(self) -> LedgerEntry:
        if self.entry_price <= 0:
            raise ValueError("entry_price must be positive")
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        # Disposition COHERENCE — the stored disposition must be the one the (proposal, verdict)
        # pair derives; an incoherent record would silently corrupt all three spread curves.
        if self.machine_proposal is not None and self.disposition is None:
            raise ValueError("machine_proposal set without a disposition — stamp it at log time")
        if self.disposition is not None:
            want = (
                Disposition.NO_PROPOSAL if self.machine_proposal is None
                else Disposition.CONFIRMED if self.machine_proposal is self.verdict
                else Disposition.OVERRIDDEN
            )
            if self.disposition is not want:
                raise ValueError(
                    f"disposition {self.disposition.value!r} incoherent with proposal/verdict "
                    f"({self.machine_proposal} vs {self.verdict}) — expected {want.value!r}"
                )
        return self


def corrections_by_decision(entries: Iterable[LedgerEntry]) -> dict[str, LedgerEntry]:
    """Each decision's CORRECTION row, by the decision's ``entry_id`` (RF-D7). Two corrections of
    one decision raise: which one stands could not be told, and the writer refuses a second.

    ``entries`` is the WHOLE ledger: a correction naming no decision row in it raises too, as an
    unpairable close does (`monitor._paired`) — a correction must correct something, and one that
    silently corrects nothing leaves the row it was written for read at its stale close."""
    out: dict[str, LedgerEntry] = {}
    decisions: set[str] = set()
    for e in entries:
        if e.event is None:
            decisions.add(e.entry_id)
        if e.event == EVENT_CORRECTION and e.corrects_entry_id is not None:
            if e.corrects_entry_id in out:
                raise ValueError(f"decision {e.corrects_entry_id!r} is corrected twice "
                                 f"({out[e.corrects_entry_id].entry_id!r}, {e.entry_id!r})")
            out[e.corrects_entry_id] = e
    orphans = sorted(f"{c.entry_id} -> {k}" for k, c in out.items() if k not in decisions)
    if orphans:
        raise ValueError(f"correction row(s) {orphans} name no decision row in the ledger — a "
                         f"correction must correct something")
    return out


def corrected(entry: LedgerEntry, correction: LedgerEntry | None) -> LedgerEntry:
    """The decision as every reader of returns reads it: its entry price and date from its
    correction when it has one, else as sealed. The ledger row itself is never rewritten."""
    if correction is None:
        return entry
    return entry.model_copy(update={"entry_price": correction.entry_price,
                                    "entry_price_as_of": correction.entry_price_as_of})


def correction_note(entry: LedgerEntry, correction: LedgerEntry) -> str:
    """The line every surface prints for a corrected decision — the sealed and the corrected entry
    side by side, so the original stays in view (RF-D7)."""
    return (f"{entry.entry_id} ({entry.ticker}): ENTRY CORRECTED by {correction.entry_id} — sealed "
            f"{entry.entry_price:g} on {entry.entry_price_as_of}, read at "
            f"{correction.entry_price:g} on {correction.entry_price_as_of} "
            f"({(correction.reason or '').strip()}); the horizon "
            f"runs from {correction.entry_price_as_of}.")


def voids_by_decision(entries: Iterable[LedgerEntry], *, as_of: date | None = None
                      ) -> dict[str, LedgerEntry]:
    """Each voided decision's VOID row, by the decision's ``entry_id`` (operator ruling 2026-11-11).
    ``entries`` is the WHOLE ledger: a void naming no decision row in it raises, as an orphan
    correction does, and two voids of one decision raise — the writer refuses a second.

    A VOID IS IN EFFECT FROM ITS RULING DATE, AS A CLOSE IS FROM ITS EXIT (operator, 2026-11-11:
    "From 2026-11-11 on (Recommended)"; Codex P1 on #984). With ``as_of``, only voids whose
    ``ruled_on`` is on or before it are returned, so a report cut before the ruling reads the
    decision as it was live then and a committed past monitor day still reproduces. Without
    ``as_of`` every void is returned: the ledger as it stands now, which is what a WRITER reads
    (no close or correction of a voided decision, ever). The checks above run on every void either
    way."""
    out: dict[str, LedgerEntry] = {}
    decisions: set[str] = set()
    for e in entries:
        if e.event is None:
            decisions.add(e.entry_id)
        if e.event == EVENT_VOID and e.voids_entry_id is not None:
            if e.voids_entry_id in out:
                raise ValueError(f"decision {e.voids_entry_id!r} is voided twice "
                                 f"({out[e.voids_entry_id].entry_id!r}, {e.entry_id!r})")
            out[e.voids_entry_id] = e
    orphans = sorted(f"{v.entry_id} -> {k}" for k, v in out.items() if k not in decisions)
    if orphans:
        raise ValueError(f"void row(s) {orphans} name no decision row in the ledger — a void must "
                         f"void something")
    if as_of is None:
        return out
    return {k: v for k, v in out.items() if v.ruled_on is not None and v.ruled_on <= as_of}


def reaffirmations(entries: Iterable[LedgerEntry], *, as_of: date | None = None
                   ) -> dict[str, LedgerEntry]:
    """ONE OBSERVATION PER NAME (2026-11-13, #1004 item 5): each decision that REAFFIRMS an earlier
    one, by its ``entry_id``, mapped to the decision it reaffirms.

    A decision reaffirms when an earlier decision ON THE SAME NAME, in the same book and on the
    same route, made the SAME call, and its own entry falls inside that earlier decision's scoring
    window — from the earlier entry up to (not including) its horizon date. It is not a new
    observation: the earlier call is already being scored over those sessions, and counting the
    second would put one name's return into the spread twice. A close does not end the window (a
    close stays scored to its horizon, the 2026-08-12 ruling); a void does, from its ruling date
    (``as_of`` as `voids_by_decision` reads it). Entries are read at their corrections.

    The one live case: SMPL. `V-SMPL-screen2-20260706` (BUY, entry 2026-07-20, closed 07-24, scored
    to 2027-01-16) and `V-SMPL-screen2-20260729` (BUY, entry 2026-08-04) — the second reaffirms the
    first. A later decision with the OPPOSITE call inside the window is not covered here: it is a
    reversal, not a reaffirmation, and no ledger row is in that state."""
    rows = list(entries)
    voided = voids_by_decision(rows, as_of=as_of)
    fixes = corrections_by_decision(rows)
    decisions = sorted(
        (corrected(e, fixes.get(e.entry_id)) for e in rows
         if e.event is None and e.entry_id not in voided),
        key=lambda e: (e.entry_price_as_of, e.decided_at, e.entry_id))
    counted: list[LedgerEntry] = []
    out: dict[str, LedgerEntry] = {}
    for d in decisions:
        key = (d.internal_id, origin_of(d), sleeve_of(d), d.verdict)
        earlier = next((o for o in counted
                        if (o.internal_id, origin_of(o), sleeve_of(o), o.verdict) == key
                        and o.entry_price_as_of <= d.entry_price_as_of
                        < o.entry_price_as_of + timedelta(days=o.horizon_days)), None)
        if earlier is None:
            counted.append(d)
        else:
            out[d.entry_id] = earlier
    return out


def reaffirmation_note(entry: LedgerEntry, earlier: LedgerEntry) -> str:
    """The line every surface prints for a reaffirmation, once."""
    end = earlier.entry_price_as_of + timedelta(days=earlier.horizon_days)
    return (f"{entry.entry_id} ({entry.ticker} {entry.verdict.value}, entry "
            f"{entry.entry_price_as_of}): a REAFFIRMATION of {earlier.entry_id}, whose window "
            f"{earlier.entry_price_as_of} → {end} it entered — not a new observation, so it is in "
            f"no count, spread or curve; one observation per name.")


def void_note(entry: LedgerEntry, void: LedgerEntry) -> str:
    """The line every surface prints for a voided decision, ONCE: what was voided, on what grounds
    and ruling, and its result to date as the void sealed it — so the removal is seen, never a
    quietly missing loser."""
    m = void.void_mark
    result = (f"; its result to date when voided: {m.position_return:+.2%} vs {m.benchmark} "
              f"{m.benchmark_return:+.2%}, excess {m.excess * 100:+.2f} pts ({m.return_basis} "
              f"return, entry {m.entry_price:g} on {m.entry_date}, marked {m.price:g} on "
              f"{m.as_of})") if m is not None else ""
    return (f"{entry.entry_id} ({entry.ticker} {entry.verdict.value}): VOIDED by {void.entry_id} "
            f"on the operator's ruling of {void.ruled_on} — {(void.reason or '').strip()}{result}. "
            f"It is left out of every position, return and curve; its rows stay as audit history.")
