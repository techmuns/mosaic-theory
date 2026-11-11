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
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import comb
from typing import Any

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
_COMMITTED = frozenset({_LEAN_BULLISH, _LEAN_BEARISH})
#: The two leans the mapping turns into an action (mixed proposes nothing).
COMMITTED_LEANS = _COMMITTED


def lean_key(label: str) -> str:
    """THE ONE KEY for a lean label, read by the mapping below and by the synthesis tally
    (`synthesis.synthesize`): "Strongly bullish" and "strongly-bullish" are one lean. Two keys were
    the hole the vote-rule design found (record §2): the tally lower-cased, the mapping also
    hyphenated, so a build split only by spelling was withheld."""
    return re.sub(r"\s+", "-", label.strip().lower())


# ---------------------------------------------------------------- THE GATE: the vote rule (R1)
#
# DECIDED 2026-11-10 (`docs/records/2026-11-10-the-proposal-vote-rule-design.md` §9, operator:
# "decide as per the expert team"): Option A + C(iii) + C(iv); its independence assumption was not
# falsified (`docs/records/2026-11-11-vote-rule-independence-measured.md`). It stays OUTSIDE the
# three-row mapping, which is unchanged.
#
# R1: a proposal is made only if a ONE-SIDED EXACT BINOMIAL TEST says the build's modal committed
# lean is the input's majority read, at 5% — P(X ≥ x | N, ½) ≤ 0.05 over the N draws ATTEMPTED.
# At five draws that is 5 of 5 and nothing less, so R1 IS today's unanimity rule at five; its words
# hold at any N (9 of 10 at ten). Chosen by face validity only — by what it tests and its error
# rates as functions of a name's lean rate — never by returns, never by which names it proposes.
# R3: a draw that failed, did not parse or carries no recognized lean counts toward NO lean, so 1
# of 5 completed is 1 of 5, not agreement. C(iii): a gate that fails on a committed lean holding a
# majority of the draws is BORDERLINE — the split is printed, no proposal is made.
GATE_ALPHA = 0.05
GATE_RULE = "R1: one-sided exact binomial test that the lean is the majority read, at 5%"
STATE_PROPOSED = "proposed"
STATE_BORDERLINE = "borderline"
STATE_NONE = "none"


def r1_required(attempted: int, alpha: float = GATE_ALPHA) -> int:
    """R1's bar: the least x with P(X ≥ x | attempted, ½) ≤ alpha — 5 of 5, 9 of 10. Below five
    draws no tally can pass (four of four is 1 in 16), so the bar is ``attempted + 1``."""
    for x in range(attempted + 1):
        if sum(comb(attempted, i) for i in range(x, attempted + 1)) / 2 ** attempted <= alpha:
            return x
    return attempted + 1


@dataclass(frozen=True)
class DrawGate:
    """R1, R3 and C(iii) on one build's draws: its modal lean key, how many draws carry it, of how
    many attempted, R1's bar, whether it passes, and the state. ``labels`` is the split, kept for
    printing beside the proposal (R4) — a count, never a rate."""

    lean: str
    count: int
    attempted: int
    required: int
    passes: bool
    state: str
    labels: tuple[tuple[str, int], ...] = field(default=())

    @classmethod
    def from_record(cls, rec: Mapping[str, Any]) -> DrawGate | None:
        """The gate a page's committed `draw_agreement` recorded, or None for a page written before
        R1 (no ``passes``): that page decides by ``unanimous``, as it always did (C7)."""
        if rec.get("passes") is None:
            return None
        labels = {str(k): int(n) for k, n in (rec.get("labels") or {}).items()}
        count, attempted = int(rec["modal_count"]), int(rec["attempted"])
        passes = bool(rec["passes"])
        # the modal lean, derived: the most common label, ties to the first written (the tally keeps
        # draw order, as `draw_gate` breaks ties) — the page stores counts, never a direction
        top = max(labels.values(), default=0)
        lean = next((k for k, n in labels.items() if n == top), "")
        state = (STATE_PROPOSED if passes
                 else STATE_BORDERLINE if lean in _COMMITTED and 2 * count > attempted
                 else STATE_NONE)
        return cls(lean=lean, count=count, attempted=attempted, required=int(rec["required"]),
                   passes=passes, state=state,
                   labels=tuple(sorted(labels.items(), key=lambda kv: (-kv[1], kv[0]))))

    @property
    def split(self) -> str:
        """The split as a count: "5 of 5 draws strongly-bullish (the 5-of-5 rule)", or every label
        when the draws disagree, with the draws that carry no lean named."""
        rule = f"the {self.required}-of-{self.attempted} rule"
        if self.labels and len(self.labels) == 1 and self.count == self.attempted:
            return f"{self.count} of {self.attempted} draws {self.lean} ({rule})"
        parts = [f"{n}x {lab or 'unparsed'}" for lab, n in self.labels]
        drawn = sum(n for _, n in self.labels)
        if drawn < self.attempted:
            parts.append(f"{self.attempted - drawn}x failed")
        return f"{', '.join(parts)} of {self.attempted} draws ({rule})"


def draw_gate(labels: Sequence[str], attempted: int) -> DrawGate:
    """The gate on one build: ``labels`` are the COMPLETED draws' lean labels in draw order (any
    spelling; "" for a lean that did not parse), ``attempted`` every draw sent. The modal lean ties
    to the label that appears first, as the synthesis keeps the first draw carrying it."""
    keys = [lean_key(x) for x in labels]
    tally = Counter(keys)
    required = r1_required(attempted)
    split = tuple(sorted(tally.items(), key=lambda kv: (-kv[1], keys.index(kv[0]))))
    if not tally:
        return DrawGate("", 0, attempted, required, False, STATE_NONE, split)
    top = max(tally.values())
    lean = next(k for k in keys if tally[k] == top)
    committed = lean in _COMMITTED
    passes = committed and top >= required
    state = (STATE_PROPOSED if passes
             else STATE_BORDERLINE if committed and 2 * top > attempted else STATE_NONE)
    return DrawGate(lean, top, attempted, required, passes, state, split)


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
    # THE GATE IS `ledger_active`, NOT "do the labels happen to be enum members" (review #380).
    # `neglect` is explicitly DORMANT and shares overshoot's BUY/AVOID_TERMINAL labels, so a
    # membership test let it through and returned a live proposal for a book the registry says is
    # not activated. `theme` was refused only by the accident of its labels — the right property
    # was never being read. A dormant book proposing a verdict is the activation gate bypassed at
    # its first real consumer.
    if not row.ledger_active:
        return (f"sleeve {sleeve!r} is defined but NOT activated for the decision ledger — "
                f"no proposal until it is (vinci/sleeves.py: ledger_active)")
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
    #: C(iii): "proposed", "borderline" or "none" when the build recorded R1's gate; None for a
    #: page written before it (decided by `unanimous`) and for the single-draw path.
    state: str | None = None
    #: R4: the split the gate read, printed beside the proposal (`DrawGate.split`); None as above.
    split: str | None = None

    @property
    def action_word(self) -> str | None:
        """Display word — AVOID_TERMINAL renders as "AVOID" (display only; the enum is the
        structured value everywhere a parser looks)."""
        if self.action is None:
            return None
        return "AVOID" if self.action is Verdict.AVOID_TERMINAL else self.action.value


def derive_proposal(
    evidence_balance: str | None, *, sleeve: str = DEFAULT_SLEEVE,
    draws_unanimous: bool | None = None, gate: DrawGate | None = None,
) -> MachineProposal:
    """The deterministic proposal — the lean LABEL against the sleeve's own legs, nothing more.

    ``sleeve`` defaults to overshoot so every pre-registry caller keeps the identical mapping.

    ``draws_unanimous`` is the REPRODUCIBILITY GATE, and it is deliberately OUTSIDE the mapping.
    The 3-row lean→action table is face-validity-frozen and stays untouched; this withholds a
    proposal the mapping would otherwise make, when the build's independent draws did not agree on
    the label it was derived from (`synthesis.SYNTHESIS_DRAWS`). ``None`` means NOT MEASURED — the
    single-draw path and every artifact written before 2026-09-26 — and behaves exactly as before,
    so absence is never read as agreement.

    WHY A GATE RATHER THAN A BETTER MAPPING: the mapping is not what is unreliable. Measured on
    identical inputs, one name returned its label 5/5, another 4/5 and another 3/5, so the LABEL the
    mapping consumes is itself a draw. Withholding is the honest response — and it is already a
    normal state here, since `mixed` withholds by design.

    ``gate`` is R1's (`draw_gate`, recorded on the build's tally since the vote rule): where it is
    given it decides, and ``draws_unanimous`` is not read. It carries the split, so a proposal is
    never printed without the count it stands on (R4), and C(iii)'s state."""
    st, sp = (gate.state, gate.split) if gate is not None else (None, None)
    if not evidence_balance or not evidence_balance.strip():
        return MachineProposal(None, None, None, "no machine read on this dossier", st, sp)
    parts = split_lean(evidence_balance)
    if parts is None:
        return MachineProposal(None, None, None, "machine read did not parse — no proposal",
                               st, sp)
    label, reason = parts
    key = lean_key(label)  # "Strongly bearish" → "strongly-bearish"
    if key not in _KNOWN_LEANS:
        return MachineProposal(
            None, label, reason, f"unrecognized lean {label!r} — no proposal (fail-honest)", st, sp
        )
    if key == _LEAN_MIXED:
        return MachineProposal(None, label, reason, "evidence two-sided (mixed) — the human's call",
                               st, sp)
    legs = _legs(sleeve)
    if isinstance(legs, str):                      # the reason there are no legs, stated verbatim
        return MachineProposal(None, label, reason, legs, st, sp)
    action = legs[0] if key == _LEAN_BULLISH else legs[1]
    if gate is not None:
        if not gate.passes or gate.lean != key:
            what = "borderline" if gate.state == STATE_BORDERLINE else "no proposal"
            return MachineProposal(
                None, label, reason,
                f"{what} — {gate.count} of {gate.attempted} draws carry {gate.lean or 'no lean'!r},"
                f" under the {gate.required}-of-{gate.attempted} rule: {label!r} would have "
                f"proposed {action.value}, withheld ({gate.split})", gate.state, gate.split)
        return MachineProposal(action, label, reason,
                               f"derived from the committed lean {label!r}; {gate.split}",
                               STATE_PROPOSED, gate.split)
    if draws_unanimous is False:
        return MachineProposal(
            None, label, reason,
            f"the build's synthesis draws DISAGREED on the lean — {label!r} would have proposed "
            f"{action.value}, withheld because a re-run would not reproduce it (tally on the page)")
    return MachineProposal(action, label, reason, f"derived from the committed lean {label!r}")
