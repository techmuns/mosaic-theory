"""Component C — megacap confirmation SIGNAL (a signal the human reads; NOT an autonomous trigger).

Part 7 found that for emergence/breakthrough themes the >$10B leaders confirm FIRST (re-rate hard)
before the sub-$10B enablers — a capturable post-confirmation window. C computes that confirmation
signal from the designated leaders (SUB-STEP 0). Confirmation gates a high-stakes enabler search, so
per the dead-signal line the **machine computes the signal; the human decides to act** — it never
fires autonomously.

THE FORWARD BASELINE (a real gap resolved here). Part 7 measured return from a HINDSIGHT-fixed
Part-5 inception — a live detector has no such anchor. The chosen forward baseline is **the start of
A's trailing detection window** (reference_date − window): contemporaneous (no hindsight inception),
available on every run, and the natural anchor (the same window over which the theme became visible
by co-movement). For the live weekly track this is the operational form of "since the theme first
surfaced in detection," to which it converges as a theme persists. (Alternatives considered: a fixed
since-first-surfaced anchor — truest, but needs detection history not yet accrued; a rolling N-month
window — equivalent here since the detection window IS ~12mo.)

THE GRID. The leaders' median cumulative return-from-baseline is presented at the Part-7 thresholds
(+20/+30/+50) across BOTH benchmarks (Finding-2: IWM mega-cap distortion is a material −15pp and is
regime-dependent), so the human sees the call's sensitivity to threshold AND benchmark rather than
trusting one fragile point. Scope: computed ONLY for human-judged-emergence themes (Part 7 — the A+B
logic does not hold for cyclical/choppy/type-ambiguous themes).
"""

from __future__ import annotations

import statistics
from datetime import date

from vinci.themes.schemas import ConfirmationCell, ConfirmationSignal, MegaLeader
from vinci.themes.signals import _horizon_return

_THRESHOLDS: tuple[tuple[str, float], ...] = (("+20%", 0.20), ("+30%", 0.30), ("+50%", 0.50))


def forward_baseline(calendar: list[date]) -> tuple[date, str]:
    """The forward/contemporaneous baseline + its rationale (see the module docstring)."""
    rationale = (
        "start of A's trailing detection window (the same ~12mo window the theme became visible "
        "over) — contemporaneous, no hindsight inception; the live form of 'since first surfaced "
        "in detection'"
    )
    return (calendar[0] if calendar else date.today()), rationale


def confirmation_signal(
    leaders: list[MegaLeader],
    leader_closes: dict[str, dict[date, float]],
    *,
    iwm_closes: dict[date, float],
    spy_closes: dict[date, float],
    calendar: list[date],
) -> ConfirmationSignal:
    """The megacap confirmation grid for ONE (human-judged-emergence) theme.

    Returns leaders' median cumulative return-from-baseline as absolute, excess-vs-IWM, and
    excess-vs-SPY, each with whether it clears +20/+30/+50. Fail-loud: leaders without window
    coverage are excluded; with none, ``n_leaders=0`` and the grid is empty (the signal cannot be
    read)."""
    n = len(calendar)
    baseline, rationale = forward_baseline(calendar)
    rets = [
        r for ld in leaders
        if (r := _horizon_return(leader_closes.get(ld.ticker, {}), calendar, n)) is not None
    ]
    grid: list[ConfirmationCell] = []
    if rets:
        med = statistics.median(rets)
        iwm_r = _horizon_return(iwm_closes, calendar, n)
        spy_r = _horizon_return(spy_closes, calendar, n)
        bases: list[tuple[str, float | None]] = [
            ("absolute", med),
            ("vs IWM", (med - iwm_r) if iwm_r is not None else None),
            ("vs SPY", (med - spy_r) if spy_r is not None else None),
        ]
        for label, val in bases:
            if val is None:
                continue
            grid.append(
                ConfirmationCell(
                    basis=label, value=val,
                    clears={name: val >= thr for name, thr in _THRESHOLDS},
                )
            )
    return ConfirmationSignal(
        baseline_date=baseline,
        baseline_rationale=rationale,
        n_leaders=len(rets),
        grid=grid,
        scope_note="computed ONLY for human-judged-emergence themes (Part 7); the human reads this "
        "signal to decide whether to fire the enabler search — it is not an autonomous trigger.",
    )
