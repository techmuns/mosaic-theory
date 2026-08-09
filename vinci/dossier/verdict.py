"""Machine verdict PROPOSAL — the 2026-07-13 constitution pivot, deterministic by construction.

The Brief now LEADS with a machine-proposed directional verdict; the HUMAN's confirm/override is
the verdict of record (logged via the ledger CLI, which seals the proposal beside it). Three lines
hold the discipline:

1. The proposal is a FACE-VALIDITY-FROZEN mapping over the synthesis's committed evidence lean
   (``evidence_balance``) — three rows, set by structure and NEVER outcome-tuned: no code path
   reads forward returns when setting this mapping (the tuning guardrail), so the proposal is
   exactly as disciplined as the lean it derives from. Since PR-2b the mapping is PER BOOK and
   DERIVED from the sleeve's declared legs (`vinci/sleeves.py`), so its SHAPE is frozen once while
   the labels follow the book — `quality` proposes PASS where `overshoot` proposes AVOID_TERMINAL,
   because "terminal decline" is not what a PASS records.
2. The LLM still emits NO verdict field (``Synthesis`` is unchanged; the no-conclusion schema pin
   stands). The conclusion is DERIVED here, in plain code, from the lean LABEL — never free-written
   by the model. ``mixed`` proposes NOTHING: a genuinely two-sided read is where the human's
   discrimination is the product, and a coin-flip proposal would only anchor it.
3. A proposal is never an order — execution stays human-authorized and paper-gated.

This module also owns THE one shared parser of the ``"<lean> — <reason>"`` shape
(``split_lean``): the synthesis QA layer, the md render, and this derivation all consume it —
two divergent parsers of the same rendered string is the bug class the parser rule exists to kill.
(``machineReadHtml``/``deriveProposal`` in ``frontend/views/shared/dossier.js`` are its JS mirror.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from vinci.schemas.ledger import Verdict
from vinci.sleeves import BY_KEY, DEFAULT_SLEEVE

# "<lean> — <reason>": em/en dash or hyphen separator, whitespace REQUIRED after it — so the
# hyphen inside "strongly-bearish" never splits the label. Mirrors dossier.js machineReadHtml().
_LEAN_RE = re.compile(r"^\s*([A-Za-z][A-Za-z\- ]*?)\s*[—–-]\s+(.+)$", re.S)


def split_lean(evidence_balance: str) -> tuple[str, str] | None:
    """``evidence_balance`` → ``(lean label, rationale)``, or ``None`` when it doesn't split."""
    m = _LEAN_RE.match(evidence_balance or "")
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


# THE FACE-VALIDITY-FROZEN MAPPING (2026-07-13 pivot), now per BOOK — three rows, still frozen.
#
# IT IS DERIVED FROM THE SLEEVE'S OWN LEGS, NOT A SECOND TABLE. A book already declares
# ``verdicts = (long, measured-against)`` in the registry, and the mapping was only ever "the
# bullish lean proposes the long leg, the bearish lean proposes its twin". Written as a per-sleeve
# dict it would be a DUAL WRITE — the shape this repo refuses — and adding a sleeve would mean
# remembering to add its mapping row or silently getting the wrong one. Derived, sleeve N+1 needs
# nothing here at all.
#
# THE SHAPE IS WHAT IS FROZEN, and it is unchanged: bullish → long, bearish → twin, ``mixed`` →
# NOTHING (a two-sided read is where the human's discrimination is the product, and a coin-flip
# would only anchor it). No code path reads forward returns to set it. Only the LABELS vary, and
# they vary because "terminal decline" is not what a PASS records.
_LEAN_BULLISH = "strongly-bullish"
_LEAN_BEARISH = "strongly-bearish"
_LEAN_MIXED = "mixed"
_KNOWN_LEANS = frozenset({_LEAN_BULLISH, _LEAN_BEARISH, _LEAN_MIXED})


def _legs(sleeve: str) -> tuple[Verdict, Verdict] | str:
    """The sleeve's (long, twin) legs as Verdict members, or the REASON there are none.

    TWO DIFFERENT ABSENCES, AND THEY MUST NOT SHARE A SENTENCE — found by running it. A book whose
    labels are not ledger verdicts (``theme`` records RATIFIED / NOT-RATIFIED in its OWN
    append-only ratification ledger) legitimately has no proposal to make here. An UNKNOWN sleeve
    is a typo or a stale artifact. The first cut reported both as "records no ledger verdicts",
    which states something FALSE about the fund's design for the second — the same class as a guard
    that refuses a value and reports it missing, where one of the two has to be a lie.

    Returns the reason rather than raising: this is on the RENDER path, and a page that cannot be
    drawn because its sleeve is misspelled is worse than a page that says so."""
    row = BY_KEY.get(sleeve)
    if row is None:
        return f"unknown sleeve {sleeve!r} — no proposal (fail-honest)"
    if not set(row.verdicts) <= {v.value for v in Verdict}:
        return (f"sleeve {sleeve!r} records no ledger verdicts — no proposal "
                f"(it validates in its own ledger)")
    return Verdict(row.verdicts[0]), Verdict(row.verdicts[1])


@dataclass(frozen=True)
class MachineProposal:
    """The machine's proposed verdict, with its provenance. ``action is None`` == NO proposal —
    ``note`` says why (two-sided · no read · unparseable · unrecognized label)."""

    action: Verdict | None
    lean: str | None  # the parsed lean label the mapping consumed (None: no/unparseable read)
    reason: str | None  # the lean's dash-rationale, verbatim (None when the read didn't split)
    note: str  # one human-readable line on how/why — rendered beside a no-proposal

    @property
    def action_word(self) -> str | None:
        """Display word — AVOID_TERMINAL renders as "AVOID" (display only; the enum is the
        structured value everywhere a parser looks)."""
        if self.action is None:
            return None
        return "AVOID" if self.action is Verdict.AVOID_TERMINAL else self.action.value


def derive_proposal(
    evidence_balance: str | None, *, sleeve: str = DEFAULT_SLEEVE
) -> MachineProposal:
    """The deterministic proposal — the lean LABEL against the sleeve's own legs, nothing more.

    ``sleeve`` defaults to overshoot so every pre-registry caller keeps the identical mapping."""
    if not evidence_balance or not evidence_balance.strip():
        return MachineProposal(None, None, None, "no machine read on this dossier")
    parts = split_lean(evidence_balance)
    if parts is None:
        return MachineProposal(None, None, None, "machine read did not parse — no proposal")
    label, reason = parts
    key = re.sub(r"\s+", "-", label.strip().lower())  # "Strongly bearish" → "strongly-bearish"
    if key not in _KNOWN_LEANS:
        return MachineProposal(
            None, label, reason, f"unrecognized lean {label!r} — no proposal (fail-honest)"
        )
    if key == _LEAN_MIXED:
        return MachineProposal(None, label, reason, "evidence two-sided (mixed) — the human's call")
    legs = _legs(sleeve)
    if isinstance(legs, str):                      # the reason there are no legs, stated verbatim
        return MachineProposal(None, label, reason, legs)
    action = legs[0] if key == _LEAN_BULLISH else legs[1]
    return MachineProposal(action, label, reason, f"derived from the committed lean {label!r}")
