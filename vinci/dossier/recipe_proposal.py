"""THE MACHINE'S R4 PROPOSAL — the three ratified conditions, read off a page, and the recipe they
propose (2026-10-09).

THE RULE IS THE OPERATOR'S (`docs/records/2026-10-08-ev-ntm-ebit-eligibility-ratified.md`, ratified
as written 2026-10-08); its machine definitions were ruled 2026-10-09. All three must hold:

1. **Forward operating profit is positive.** CIQ's NTM TEV/EBIT is present and positive.
2. **R1 cannot anchor.** R1's own anchor declines (`applicable=False`), OR the EBITDA basis is
   divergent (`financial_summary.ebitda_basis.divergent` — consensus-implied D&A at least 2×, or at
   most 0.5×, the actuals), so an EV/EBITDA leg would mix definitions.
3. **R3 cannot price it cleanly.** CIQ's fiscal-year P/E is struck on GAAP EPS
   (`forward_consensus.pe_eps_basis.fiscal_years == "gaap"`), AND at least
   :data:`R4_MIN_MATERIAL_QUARTERS` of the trailing four quarters carry a material block from below
   the operating line (`quality.nonoperating_quarters`).

PROPOSE-ONLY, BY THE EXISTING RULE (ruled 2026-10-09). The proposal replaces the build's FRESH R1
hint; `preserve_operator_tag` then keeps any committed recipe and the build reports the divergence
as a caveat. So AMZN (hand R3) and UBER (committed R2_NEEDED) SHOW "this build proposes R4" and keep
their recipes until the operator re-tags; only a page with no committed recipe takes R4 directly.

FAIL CLOSED. A condition whose input is missing is UNKNOWN, and an unknown condition proposes
nothing — never a guess in either direction. R1's own arithmetic stays in the block untouched: the
proposal changes which recipe the page names, never the numbers beside it.

NOT TUNED ON OUTCOMES. The thresholds are face-validity rulings; the rule was run over the 26 pages
as an ELIGIBILITY test (which names it selects — AMZN and UBER, the ratified table), never a
performance one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vinci.dossier.anchor import Anchor

#: R4's recipe id. Mirrors `vinci.scenarios.RECIPE_R4` (pinned equal in the tests): this module
#: sits on the dossier side, which must not import the scenario engine.
RECIPE_R4 = "R4_forward_ev_ebit"

#: Condition 3's materiality count — ruled 2026-10-09: "at least 2 of the trailing four quarters",
#: recurring rather than a one-off. Today's selection is the same at 1, 2 or 3.
R4_MIN_MATERIAL_QUARTERS = 2


@dataclass(frozen=True)
class Condition:
    """One ratified condition: met (True/False) or UNKNOWN (None), and what it was read from."""

    name: str
    met: bool | None
    detail: str


def _get(d: Any, *path: str) -> Any:
    for k in path:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def r4_conditions(doc: dict[str, Any], r1: Anchor | None) -> list[Condition]:
    """The three conditions on one page. `r1` is the build's own R1 anchor (its `applicable` is
    R1's verdict, never a committed tag's)."""
    ntm = next((m.get("value") for m in _get(doc, "forward_consensus", "current_multiples") or []
                if isinstance(m, dict) and m.get("metric") == "TEV/EBIT"
                and m.get("period") == "NTM"), None)
    c1 = (Condition("NTM EBIT > 0", None, "no NTM TEV/EBIT on the page")
          if not isinstance(ntm, (int, float)) else
          Condition("NTM EBIT > 0", ntm > 0, f"CIQ NTM TEV/EBIT {ntm:.1f}x"))

    eb = _get(doc, "mechanical", "financial_summary", "ebitda_basis")
    declines = r1 is not None and r1.applicable is False
    divergent = isinstance(eb, dict) and eb.get("divergent") is True
    if r1 is None and not isinstance(eb, dict):
        c2 = Condition("R1 cannot anchor", None, "no R1 anchor and no EBITDA-basis read")
    else:
        why = []
        if declines:
            why.append("R1's anchor declines (applicable=False)")
        if divergent:
            why.append(f"EBITDA basis divergent: consensus-implied D&A {eb.get('ratio'):.2f}× "
                       "the actuals")
        c2 = Condition("R1 cannot anchor", declines or divergent,
                       "; ".join(why) or "R1 anchors and the EBITDA basis is not divergent")

    basis = _get(doc, "forward_consensus", "pe_eps_basis", "fiscal_years")
    nq = _get(doc, "mechanical", "quality", "nonoperating_quarters")
    if basis is None or not isinstance(nq, dict):
        c3 = Condition("R3 cannot price it cleanly", None,
                       "no P/E EPS basis" if basis is None else "no structured non-operating count")
    else:
        gaap, material = basis == "gaap", int(nq.get("material", 0))
        c3 = Condition(
            "R3 cannot price it cleanly",
            gaap and material >= R4_MIN_MATERIAL_QUARTERS,
            f"CIQ's FY P/E struck on {basis} EPS; {material} of the trailing {nq.get('window')} "
            f"quarters carry material non-operating income (≥{R4_MIN_MATERIAL_QUARTERS} ruled)")
    return [c1, c2, c3]


def propose(doc: dict[str, Any], r1: Anchor) -> Anchor:
    """`r1` with R4 proposed when all three conditions hold; `r1` unchanged otherwise.

    Only the recipe and its reason change — R1's computed values stay, and so does `applicable`
    (R1's bit). The reason names every condition with the value it was read from."""
    conds = r4_conditions(doc, r1)
    if not all(c.met is True for c in conds):
        return r1
    return r1.model_copy(update={
        "recipe_hint": RECIPE_R4,
        "reason": ("EV/NTM EBIT (R4) — all three ratified conditions hold: "
                   + " · ".join(f"{c.name}: {c.detail}" for c in conds)
                   + ". R1's own arithmetic is left in this block.")})
