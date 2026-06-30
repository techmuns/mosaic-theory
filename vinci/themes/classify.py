"""Component B — theme-type SIGNALS fused into criterion-1 (the machine ASSEMBLES; the human
JUDGES).

Per the analyst decision, theme-type (emergence vs cyclical vs choppy) is NOT auto-classified — it
is the human's call AS PART OF naming the driver (criterion 1). The machine assembles the signals
that make that call reliable and PRESENTS them; it renders no type verdict:

1. PRICE-PATTERN — the designated mega-cap leaders' trajectory vs the sub-$10B members' (reusing A's
   horizon machinery): leader-FIRST (leaders re-rate before the members — the emergence signature,
   Part 7) vs SYNCHRONOUS (cyclical) vs UNSTABLE (choppy). Presented as both trajectories + the
   lead-minus-member shape + a mechanical descriptor — never a type verdict.
2. VOL-STRIP SURVIVAL — did the cluster survive A's vol strip (real theme) or fragment (spec-beta)?
3. HISTORICAL ANALOG (§7.2) — an LLM-assembled reference class of past themes this resembles + how
   they resolved; PROPOSED, source-bound, for the human to weigh (makes the ambiguous cases
   judgeable).
4. The DEFER state — when the signals are mixed (no clean leader-first/synchronous read, no analog),
   the output says **TYPE-AMBIGUOUS → watch, do not fire**; it does NOT force a type.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from vinci.themes.schemas import HistoricalAnalog, PricePattern, TypeSignals
from vinci.themes.signals import _momentum_trajectory

_LEAD_GAP = 0.15  # leaders ahead of members by this much at the long horizons reads as leader-first
_SYNC_BAND = 0.08  # leader−member within this at every horizon reads as synchronous

ANALOG_TOOL: dict[str, Any] = {
    "name": "reference_class",
    "description": "Name past market themes this cluster's driver/pattern resembles, and how each "
    "resolved (emergence / cyclical / fade). Assemble a reference class for the analyst to weigh — "
    "do NOT conclude this theme's type.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reference_themes": {
                "type": "array", "items": {"type": "string"},
                "description": "3–6 named past themes "
                "(e.g. 'AI-infra 2023', 'shale 2010s', 'GLP-1').",
            },
            "note": {
                "type": "string",
                "description": "One or two sentences: how those analogues resolved and what that "
                "implies the analyst should check — never a verdict on THIS theme.",
            },
        },
        "required": ["reference_themes", "note"],
    },
}


def compute_price_pattern(
    leader_closes: dict[str, dict[date, float]],
    member_closes: dict[str, dict[date, float]],
    *,
    calendar: list[date],
    reference_date: date,
) -> PricePattern:
    """Leaders' vs members' momentum trajectory + the lead-lag shape (a presented signal, no
    verdict)."""
    lead = _momentum_trajectory(list(leader_closes), leader_closes, calendar, reference_date,
                                min_members=1)  # a theme can have a single mega-cap leader
    member = _momentum_trajectory(list(member_closes), member_closes, calendar, reference_date)
    diffs: list[tuple[str, float]] = []
    for label, lf in lead.ordered():
        mf = dict(member.ordered())[label]
        if lf.value is not None and mf.value is not None:
            diffs.append((label, lf.value - mf.value))

    long_gap = [d for lbl, d in diffs if lbl in ("6mo", "12mo")]
    short_gap = [d for lbl, d in diffs if lbl in ("1mo", "3mo")]
    if not leader_closes:
        read = "no co-moving mega-cap leaders — leader-first vs synchronous cannot be read"
    elif diffs and all(abs(d) <= _SYNC_BAND for _, d in diffs):
        read = ("SYNCHRONOUS — leaders and members move together across horizons "
                "(cyclical signature)")
    elif long_gap and sum(long_gap) / len(long_gap) >= _LEAD_GAP and (
        not short_gap or sum(short_gap) / len(short_gap) < sum(long_gap) / len(long_gap)
    ):
        read = ("LEADER-FIRST — leaders ran ahead at 6–12mo while the members lag/just turn "
                "(the emergence signature; the analyst judges the type)")
    else:
        read = "MIXED / UNSTABLE — no clean leader-first or synchronous shape (choppy signature)"
    return PricePattern(
        leader_trajectory=lead, member_trajectory=member, lead_minus_member=diffs, read=read
    )


def historical_analog(
    candidate_linkage_note: str,
    leader_tickers: list[str],
    member_tickers: list[str],
    *,
    llm: Any | None,
) -> HistoricalAnalog:
    """An LLM-assembled reference class — proposed, source-bound to named past themes, never a
    verdict."""
    if llm is None:
        return HistoricalAnalog(
            reference_themes=[], note="LLM unavailable — analog not assembled", model=None,
            status="unavailable",
        )
    system = (
        "You assemble a REFERENCE CLASS for a human analyst judging a market theme's type. You "
        "name past themes the pattern resembles and how they resolved. You do NOT conclude this "
        "theme's "
        "type, name its driver, or give any buy/sell view — you assemble analogues for the human."
    )
    user = (
        f"A residual-co-movement cluster of sub-$10B names with these shared traits:\n"
        f"{candidate_linkage_note}\n"
        f"Designated >$10B leaders: {', '.join(leader_tickers) or '(none)'}\n"
        f"Sample members: {', '.join(member_tickers[:12])}\n"
        f"Assemble the reference class."
    )
    try:
        out = llm.extract(system=system, user=user, tool=ANALOG_TOOL)
        return HistoricalAnalog(
            reference_themes=[str(x) for x in out.get("reference_themes", [])],
            note=str(out.get("note", "")), model=getattr(llm, "model", None), status="assembled",
        )
    except Exception as exc:  # noqa: BLE001 — degrade to unavailable, never crash the assembly
        return HistoricalAnalog(
            reference_themes=[], note=f"analog unavailable ({type(exc).__name__})", model=None,
            status="unavailable",
        )


def assemble_type_signals(
    price_pattern: PricePattern,
    *,
    vol_strip_survived: bool,
    vol_strip_note: str,
    analog: HistoricalAnalog,
) -> TypeSignals:
    """Combine B's signals + decide the DEFER state. The human judges the type; the machine never
    does."""
    pattern_unclear = (
        price_pattern.read.startswith("MIXED") or price_pattern.read.startswith("no co-")
    )
    no_analog = analog.status != "assembled" or not analog.reference_themes
    ambiguous = pattern_unclear and no_analog
    defer = (
        "TYPE-AMBIGUOUS → watch, do not fire — the price pattern is not a clean leader-first or "
        "synchronous shape and no analog was assembled; the honest read is wait."
        if ambiguous
        else "signals assembled — the analyst judges the type as part of naming the driver."
    )
    return TypeSignals(
        price_pattern=price_pattern, vol_strip_survived=vol_strip_survived,
        vol_strip_note=vol_strip_note, historical_analog=analog, ambiguous=ambiguous,
        defer_note=defer,
    )
