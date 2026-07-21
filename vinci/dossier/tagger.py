"""Recipe tagger — PROPOSE-ONLY. Reads committed artifacts, proposes a recipe, writes NOTHING.

Which recipe fits a name is currently decided by hand, one name at a time, and the reasoning is
re-derived from scratch each time. This module states the reasoning ONCE, as signals a machine can
read off the committed record, so the operator ratifies a proposal instead of rebuilding an argument
— and so a name that drifts across the boundary (a margin turning positive, leverage falling) is
noticed rather than left on a stale tag.

**It proposes; it never writes.** No function here returns a mutated artifact, and the CLI path that
DOES write (``anchor-backfill``) preserves an existing hand tag rather than taking a proposal — see
:func:`vinci.dossier.anchor.preserve_operator_tag`. The reason is the same one that keeps the LLM
away from verdicts: the tag decides which arithmetic a name gets, and a wrong tag is not visible in
the output — an R1 grid on an R2 name looks exactly like an R1 grid.

The signals are deliberately crude and READABLE. A tagger nobody can argue with is a tagger nobody
checks, and every proposal here prints the signals that produced it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vinci.dossier.anchor import (
    RECIPE_R1,
    RECIPE_R1_NOT_ROBUST,
    RECIPE_R2,
    RECIPE_UNRESOLVED,
)
from vinci.dossier.band_guards import BAND_INCOHERENT, BAND_UNRECONCILED

# --- thresholds (face-validity, never outcome-tuned) -------------------------------------------
# Net debt this large relative to the equity the anchor itself computes means a one-turn error in
# the exit multiple moves value per share by most of the price — CNXC sat at 139% when it was
# hand-tagged R1_NOT_ROBUST on 2026-07-21, and that judgment is what this encodes.
_LEVERAGE_DOMINANT = 1.0
# A margin history whose EARLY years sit at or below this, and whose LATE years clear it by this
# much, is a RAMP: there is no level for a trailing median to revert to. VITL ran 0 -> 11.6%.
_RAMP_EARLY_CEILING = 0.02
_RAMP_MIN_GAIN = 0.05
# Below this a positive median margin is "low" — R1 technically computes, but a point of margin
# error swamps the answer, so it is flagged for the operator rather than waved through.
_LOW_MARGIN = 0.05


@dataclass(frozen=True)
class Proposal:
    """One name's proposed recipe, the signals behind it, and how it compares to the committed tag.

    ``agrees`` is None when nothing is committed yet — an ABSENT tag is not a disagreement, and
    conflating the two would make the first tagging of a name look like an override."""

    ticker: str
    proposed: str
    committed: str | None
    agrees: bool | None
    signals: list[str] = field(default_factory=list)
    note: str = ""


def _actual_margins(mechanical: dict[str, Any]) -> list[float]:
    """Reported EBIT margin per ACTUAL fiscal year from the committed financial summary, oldest
    first. Estimate columns are excluded — a forecast is not history."""
    ann = ((mechanical.get("financial_summary") or {}).get("annual") or {}).get("value") or {}
    rows = {r.get("label"): (r.get("values") or []) for r in ann.get("rows") or []}
    ebit, rev = rows.get("EBIT ($M)") or [], rows.get("Revenue ($M)") or []
    ise = ann.get("is_estimate") or []
    return [ebit[i] / rev[i] for i in range(min(len(ebit), len(rev)))
            if not (i < len(ise) and ise[i]) and ebit[i] is not None and rev[i]]


def _margin_shape(margins: list[float]) -> tuple[str, str]:
    """(shape, evidence) for the margin history: negative | ramp | low | stable | unknown.

    A RAMP is the shape a trailing median cannot describe in EITHER direction — the early years say
    one business and the late years say another, so the median describes neither."""
    if len(margins) < 3:
        return "unknown", f"only {len(margins)} actual FY of margin history"
    early, late = margins[:3], margins[-3:]
    e, latest = sum(early) / 3, sum(late) / 3
    if latest <= 0:
        return "negative", f"latest-3 mean margin {latest:.1%} — not profitable on a trailing basis"
    if e <= _RAMP_EARLY_CEILING and latest - e >= _RAMP_MIN_GAIN:
        return "ramp", (f"earliest-3 mean {e:.1%} → latest-3 mean {latest:.1%} "
                        f"(+{latest - e:.1%}) — no level for a median to revert to")
    if latest < _LOW_MARGIN:
        return "low", f"latest-3 mean margin {latest:.1%} — a point of error swamps the answer"
    return "stable", f"earliest-3 {e:.1%} → latest-3 {latest:.1%}"


def _leverage(anchor: dict[str, Any]) -> tuple[float | None, str]:
    """Net debt as a multiple of the equity the anchor itself computes. None when either side is
    missing — never a leverage read off half a balance sheet."""
    nd = (anchor.get("net_debt") or {}).get("value")
    base = anchor.get("anchor_base_value_per_share")
    shares = (anchor.get("diluted_shares") or {}).get("value")
    if nd is None or base is None or not shares:
        return None, "leverage not assessable (net debt or anchor equity absent)"
    equity = base * shares / 1e6                      # $/sh × count -> $, to $M
    if equity <= 0:
        return None, "anchor equity is non-positive — leverage ratio undefined"
    return nd / equity, f"net debt {nd:,.0f}M is {nd / equity:.0%} of anchor equity {equity:,.0f}M"


def propose(ticker: str, doc: dict[str, Any]) -> Proposal:
    """Propose a recipe for one committed dossier. Pure: reads, never writes.

    Order matters and encodes precedence. A disqualified multiple beats everything (the arithmetic
    has no denominator); a margin that cannot be computed is a DATA gap, never an R2 signal; a
    negative or ramping margin is the R2 case; dominant leverage means R1 computes but cannot
    discriminate; only a stable, adequate margin on a clean band proposes R1."""
    mech = doc.get("mechanical") or {}
    anchor = doc.get("anchor") or {}
    signals: list[str] = []

    dq = str(anchor.get("data_quality") or "")
    band_dead = BAND_INCOHERENT in dq or BAND_UNRECONCILED in dq
    if band_dead:
        signals.append(f"band guard flagged: {dq} — the exit multiple has no usable denominator")

    margins = _actual_margins(mech)
    shape, evidence = _margin_shape(margins)
    signals.append(f"margin history {shape}: {evidence}")
    lev, lev_note = _leverage(anchor)
    signals.append(lev_note)

    mult = ((mech.get("valuation") or {}).get("own_history") or {}).get("value")
    has_band = any("EBITDA" in str(b.get("metric", "")) and b.get("median") is not None
                   for b in (mult or []) if isinstance(b, dict))
    if not has_band:
        signals.append("no own-history EV/EBITDA band — the trailing multiple series does not "
                       "exist (typically every period NM on a loss-making year)")

    if band_dead or not has_band:
        proposed, note = RECIPE_R2, "no usable trailing multiple — must be anchored forward"
    elif shape == "unknown":
        proposed, note = RECIPE_UNRESOLVED, "margin history too short to characterise"
    elif shape in ("negative", "ramp"):
        proposed, note = RECIPE_R2, f"margin history is {shape} — no trailing level to revert to"
    elif lev is not None and lev >= _LEVERAGE_DOMINANT:
        proposed, note = (RECIPE_R1_NOT_ROBUST,
                          "R1 computes, but at this leverage one turn of multiple error moves "
                          "value per share by most of the price")
    elif shape == "low":
        proposed, note = (RECIPE_R1_NOT_ROBUST,
                          "R1 computes on a thin margin — a point of margin error swamps the "
                          "answer; operator call")
    else:
        proposed, note = RECIPE_R1, "stable, adequate margin history on a clean band"

    committed = anchor.get("recipe_hint")
    return Proposal(ticker=ticker, proposed=proposed, committed=committed,
                    agrees=(None if not committed else committed == proposed),
                    signals=signals, note=note)
