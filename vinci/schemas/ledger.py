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

from pydantic import BaseModel, model_validator

# The one non-decision event a ledger row may record. A close is an APPENDED row, never an edit.
EVENT_CLOSE = "CLOSE"

# Close-row id convention. The decision row is "V-{candidate_id}" and re-logging it fails loud —
# that uniqueness rule is what makes the ledger append-only in practice. It is widened HERE, once
# and deliberately: a candidate may carry exactly one decision row and one close row.
CLOSE_ID_PREFIX = "C-"


def close_entry_id(candidate_id: str) -> str:
    """The close row's id for ``candidate_id`` — one per candidate, by construction."""
    return f"{CLOSE_ID_PREFIX}{candidate_id}"


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
