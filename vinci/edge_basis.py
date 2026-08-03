"""(A4) THE EDGE-BASIS GATE — no verdict without saying what the edge IS.

WHY A GATE AND NOT A FIELD. A verdict already records a thesis, kill-criteria and a twin ruling.
None of them answers the one question the fund's whole apparatus exists to serve: *what do we think
that the price does not*. Left optional it is answered when convenient and skipped when the answer
is uncomfortable, which is exactly the population where it matters.

SILENCE IS REFUSED; AGREEMENT IS ALLOWED — and the second half is what makes the first honest.
A gate that accepted only "we hold a variant expectation" would manufacture views to satisfy a
field, and **a fabricated gap is worse than an honest none**: it survives into the ledger, into the
spread, and into every retrospective, wearing the same shape as a real one. So five of the six
options say "no variant" out loud and remain fully valid verdicts.

IT IS NOT HYPOTHETICAL THAT THE ESCAPES ARE NEEDED. **8 of 11 committed names cannot state a
variant expectation today** — five carry no scenario record, three are R2 records whose margin is
not comparable to the near-term consensus at the anchor. The escape options are the MAJORITY path,
not a courtesy.

THE MACHINE NEVER PICKS. This module validates a choice the human typed; it has no opinion about
which basis is right, and it cannot infer one. That line is the same one `verdict.py` holds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class EdgeBasisError(ValueError):
    """The stated edge basis is absent, unknown, or unsupported by the evidence it claims."""


@dataclass(frozen=True)
class EdgeBasis:
    """One admissible answer to "what is the edge here?"."""

    key: str
    label: str
    requires_variant: bool          # does this option assert a variant expectation?
    needs: str                      # what the human must supply alongside it
    note: str = ""


#: THE SIX. Ordered so the strongest claim is first and the weakest last; the ORDER carries no
#: preference — a watchlist entry honestly labelled is worth more than a variant asserted to fill
#: the field.
EDGE_BASES: tuple[EdgeBasis, ...] = (
    EdgeBasis(
        "variant-expectation", "Variant expectation stated", True,
        "a stated total EV gap (the three-ratio decomposition, or the gap alone where the "
        "decomposition is routed away)",
        "The only option that claims we forecast something the street does not. It REQUIRES the "
        "ratios, because a variant expectation nobody can size is a mood."),
    EdgeBasis(
        "valuation-asymmetry", "No variant; valuation asymmetry at this price", False,
        "the reward:risk grid at the entry price",
        "We agree with consensus and think the PRICE is wrong about it. A legitimate edge and a "
        "different one."),
    EdgeBasis(
        "distribution", "No variant; the distribution, not the central case", False,
        "which tail, and why the market is mispricing it",
        "The central case may be consensus while the spread of outcomes is not."),
    EdgeBasis(
        "event-structural", "No variant; event or structural", False,
        "a named date or trigger",
        "A catalyst, a forced seller, an index event. Must name WHEN, or it is a hope."),
    EdgeBasis(
        "watchlist", "No variant; watchlist, awaiting a named observation", False,
        "the observation being waited for",
        "Honest not-yet. Refusing this option would push every undecided name into a fabricated "
        "variant, which is the failure this gate exists to prevent."),
    EdgeBasis(
        "variant-vs-cross-section", "Variant vs the cross-section", True,
        "the cross-sectional claim, in the analyst's own words",
        "A SLOT ONLY until A5 exists. Renders as ANALYST-ASSERTED, MACHINE VERIFICATION PENDING — "
        "the machine cannot check a cross-sectional claim yet, and a slot that pretended otherwise "
        "would be the false-confirmation defect."),
)

BASIS_BY_KEY: dict[str, EdgeBasis] = {b.key: b for b in EDGE_BASES}

#: Rendered beside option 6 wherever it appears, until A5 can verify a cross-sectional claim.
PENDING_MARK = "analyst-asserted, machine verification pending"


def _gap_statement(ev_gap: Any) -> tuple[bool, str]:
    """Does this name's persisted EV gap STATE a total gap? -> (yes, how-it-reads).

    THE TOTAL IS THE REQUIREMENT, NOT THE DECOMPOSITION. Where routing sends a name to `two-ratio`
    or `price-implied-only`, the three ratios are deliberately not struck — but the gap itself may
    still be stated, and that is enough to claim a variant expectation. Attribution then reads
    SUPPRESSED with its coverage, rather than the option being refused.
    """
    if not isinstance(ev_gap, dict):
        return False, "no EV gap is persisted for this name (the refresh has not run here)"
    if ev_gap.get("status") != "computed":
        return False, str(ev_gap.get("reason") or "no gap is struck for this name")
    ratios = ev_gap.get("ratios") or {}
    total = ratios.get("ev_gap")
    if not isinstance(total, (int, float)):
        return False, "the persisted gap carries no total"
    form = str(ev_gap.get("form") or "")
    if form == "three-ratio":
        return True, f"total gap {total:.2f}x, decomposed"
    n = ((ev_gap.get("routes") or {}).get("EBITDA") or {}).get("n")
    return True, (f"total gap {total:.2f}x — attribution suppressed: coverage n="
                  f"{n if n is not None else '?'}, form {form or 'unrouted'}")


def require_edge_basis(basis_key: str | None, *, ev_gap: Any, note: str | None = None) -> str:
    """Validate the human's stated edge basis, or REFUSE. Returns the line sealed with the verdict.

    REFUSES SILENCE. `None` is not a default — a verdict without a stated basis is the case this
    gate exists for, and defaulting it to the weakest option would be the machine answering the
    question on the human's behalf.

    REFUSES AN UNBACKED VARIANT CLAIM. Option 1 asserts we forecast something the street does not;
    if no total gap is persisted, that claim has nothing behind it and the refusal NAMES the
    alternative rather than merely blocking — the escape options exist precisely for this.
    """
    if not basis_key:
        opts = "\n".join(f"    {b.key:<24} {b.label}" for b in EDGE_BASES)
        raise EdgeBasisError(
            "no --edge-basis given. A verdict must say what the edge IS; silence is refused and "
            "agreement is allowed — five of these six say 'no variant' out loud and are fully "
            f"valid:\n{opts}\n"
            "  A fabricated variant is worse than an honest none: it survives into the ledger, "
            "the spread and every retrospective wearing the same shape as a real one.")
    basis = BASIS_BY_KEY.get(basis_key)
    if basis is None:
        raise EdgeBasisError(
            f"unknown edge basis {basis_key!r} — choose one of {sorted(BASIS_BY_KEY)}")

    if basis.key == "variant-expectation":
        ok, how = _gap_statement(ev_gap)
        if not ok:
            raise EdgeBasisError(
                f"edge basis 'variant-expectation' claims we forecast something the street does "
                f"not, but this name states no total EV gap — {how}. Either state the gap, or pick "
                "an honest alternative: valuation-asymmetry, distribution, event-structural, "
                "watchlist. 8 of 11 committed names cannot state a variant today; that is the "
                "normal path, not a failure.")
        line = f"{basis.label} — {how}"
    elif basis.key == "variant-vs-cross-section":
        line = f"{basis.label} — {PENDING_MARK}"
    else:
        line = basis.label

    if note:
        line += f" · {note.strip()}"
    return line
