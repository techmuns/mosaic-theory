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
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

# The one non-decision event a ledger row may record. A close is an APPENDED row, never an edit.
EVENT_CLOSE = "CLOSE"

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
    """The close row's id for ``candidate_id`` — one per candidate, by construction."""
    return f"{CLOSE_ID_PREFIX}{candidate_id}"


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
    """The two verdicts Loop 1 records for Screen 2 (overshot de-rating)."""

    BUY = "BUY"  # overshoot — the de-rating is exaggerated-and-temporary; a reversal is nameable
    AVOID_TERMINAL = "AVOID_TERMINAL"  # the twin — real-and-permanent decline; no trade


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
    reason: str | None = None                # CLOSE only

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
            return self
        if self.event != EVENT_CLOSE:
            raise ValueError(f"unknown ledger event {self.event!r} — expected {EVENT_CLOSE!r}, "
                             "or None for a decision row")
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
