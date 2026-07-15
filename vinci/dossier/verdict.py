"""Machine verdict PROPOSAL — the 2026-07-13 constitution pivot, deterministic by construction.

The Brief now LEADS with a machine-proposed directional verdict; the HUMAN's confirm/override is
the verdict of record (logged via the ledger CLI, which seals the proposal beside it). Three lines
hold the discipline:

1. The proposal is a FACE-VALIDITY-FROZEN mapping over the synthesis's committed evidence lean
   (``evidence_balance``) — the three rows in ``_PROPOSAL_BY_LEAN``, set by structure and NEVER
   outcome-tuned: no code path reads forward returns when setting this mapping (the tuning
   guardrail), so the proposal is exactly as disciplined as the lean it derives from.
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

# "<lean> — <reason>": em/en dash or hyphen separator, whitespace REQUIRED after it — so the
# hyphen inside "strongly-bearish" never splits the label. Mirrors dossier.js machineReadHtml().
_LEAN_RE = re.compile(r"^\s*([A-Za-z][A-Za-z\- ]*?)\s*[—–-]\s+(.+)$", re.S)


def split_lean(evidence_balance: str) -> tuple[str, str] | None:
    """``evidence_balance`` → ``(lean label, rationale)``, or ``None`` when it doesn't split."""
    m = _LEAN_RE.match(evidence_balance or "")
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


# The face-validity-frozen mapping (2026-07-13 pivot) — the bear case IS the terminal case in this
# dossier's framing, so a committed bearish lean proposes AVOID_TERMINAL; a committed bullish lean
# proposes BUY; ``mixed`` proposes nothing (None). Any other label is UNRECOGNIZED → no proposal,
# fail-honest — never a guessed direction.
_PROPOSAL_BY_LEAN: dict[str, Verdict | None] = {
    "strongly-bearish": Verdict.AVOID_TERMINAL,
    "strongly-bullish": Verdict.BUY,
    "mixed": None,
}


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


def derive_proposal(evidence_balance: str | None) -> MachineProposal:
    """The deterministic proposal — a frozen dict lookup over the lean LABEL, nothing more."""
    if not evidence_balance or not evidence_balance.strip():
        return MachineProposal(None, None, None, "no machine read on this dossier")
    parts = split_lean(evidence_balance)
    if parts is None:
        return MachineProposal(None, None, None, "machine read did not parse — no proposal")
    label, reason = parts
    key = re.sub(r"\s+", "-", label.strip().lower())  # "Strongly bearish" → "strongly-bearish"
    if key not in _PROPOSAL_BY_LEAN:
        return MachineProposal(
            None, label, reason, f"unrecognized lean {label!r} — no proposal (fail-honest)"
        )
    action = _PROPOSAL_BY_LEAN[key]
    if action is None:
        return MachineProposal(None, label, reason, "evidence two-sided (mixed) — the human's call")
    return MachineProposal(action, label, reason, f"derived from the committed lean {label!r}")
