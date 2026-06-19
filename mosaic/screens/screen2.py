"""Screen 2 — overshot de-rating, as a conjunction of coarse PASS/FAIL/UNKNOWN gates.

The screen finds the **setup** (a name has been sharply, idiosyncratically de-rated), never the
**edge** — the manual discriminator downstream rules out the twin (*terminal decline*). Per
``FUNNEL_SCREENS.md``: gates, not a composite score; recall over precision; thresholds are coarse
**face-validity** starting points, **never tuned on forward returns**.

Gates (read from the assembled data-record's enveloped fields):
- **G1 sharp drawdown** ≤ −30% from the 52w high (price; the cleanest gate). Defining gate.
- **G2 idiosyncratic** — underperformed the market (IWM) by a wide margin over the decline window.
- **G3 multiple at/near floor** — current multiple in the bottom quartile of its trailing range
  (EDGAR + price; UNKNOWN→defer where XBRL is absent or earnings are negative).

A name is admitted iff **no gate FAILs and G1 PASSes**; UNKNOWN gates are carried forward as depth
tasks (``unknown_gates_for_depth``), they do not block.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from mosaic.schemas.candidate import CandidateRecord, GateResult, TriageBand, derive_unknown_gates
from mosaic.schemas.data_record import DataRecord

TWIN = "terminal decline"


class Screen2Thresholds(BaseModel, frozen=True):
    """Coarse gate thresholds — calibrated by face-validity, never by P&L."""

    drawdown_max: float = -0.30  # G1: at least a 30% fall from the 52w high
    # G1 terminal-by-magnitude cap: a fall worse than this is the market pricing bankruptcy/zero —
    # the terminal side of Edge 2 by definition, not a recoverable overshoot. Set from the thesis,
    # never from testing which cutoff would have paid.
    drawdown_terminal_floor: float = -0.85
    idio_rel_max: float = -0.15  # G2: underperformed the benchmark by ≥15% over the window
    multiple_floor_pctile: float = 0.25  # G3: current multiple in the bottom quartile of its range


def gate_g1_drawdown(rec: DataRecord, th: Screen2Thresholds) -> tuple[GateResult, str]:
    f = rec.prices.drawdown_from_high
    if not f.is_evaluable or f.value is None:
        return GateResult.UNKNOWN, "no drawdown (insufficient price history)"
    dd, floor = f.value, th.drawdown_terminal_floor
    if dd < floor:
        return GateResult.FAIL, f"drawdown {dd:.1%} past terminal floor {floor:.0%}"
    if dd <= th.drawdown_max:
        return GateResult.PASS, f"drawdown {dd:.1%} ≤ {th.drawdown_max:.0%}"
    return GateResult.FAIL, f"drawdown {dd:.1%} shallower than {th.drawdown_max:.0%}"


def gate_g2_idiosyncratic(rec: DataRecord, th: Screen2Thresholds) -> tuple[GateResult, str]:
    f = rec.prices.rel_ret_vs_market
    if not f.is_evaluable or f.value is None:
        return GateResult.UNKNOWN, "no clean market benchmark"
    if f.value <= th.idio_rel_max:
        return GateResult.PASS, f"rel-return {f.value:.1%} ≤ {th.idio_rel_max:.0%} (idiosyncratic)"
    return GateResult.FAIL, f"rel-return {f.value:.1%} — fell with the market, not name-specific"


def gate_g3_multiple_floor(rec: DataRecord, th: Screen2Thresholds) -> tuple[GateResult, str]:
    # Prefer EV/EBITDA percentile; fall back to P/E percentile; else defer.
    f = rec.fundamentals.ev_ebitda_pctile_vs_history
    label = "EV/EBITDA"
    if not f.is_evaluable or f.value is None:
        f = rec.fundamentals.pe_pctile_vs_history
        label = "P/E"
    if not f.is_evaluable or f.value is None:
        return GateResult.UNKNOWN, "no multiple-vs-history (XBRL absent / negative earnings)"
    if f.value <= th.multiple_floor_pctile:
        return GateResult.PASS, f"{label} at {f.value:.0%}ile of trailing range (≤ floor)"
    return GateResult.FAIL, f"{label} at {f.value:.0%}ile — not near its floor"


def _triage(rec: DataRecord) -> TriageBand:
    """Coarse triage by drawdown depth (the single most reliable Screen-2 signal)."""
    dd = rec.prices.drawdown_from_high.value
    if dd is None:
        return TriageBand.C
    if dd <= -0.50:
        return TriageBand.A
    if dd <= -0.40:
        return TriageBand.B
    return TriageBand.C


def _trigger_reason(rec: DataRecord, gate_detail: dict[str, str]) -> str:
    """What hit the name: prefer a recorded de-rating event; else the price drop itself."""
    derate_events = [
        e
        for e in rec.events
        if e.event_type.value in ("guidance_cut", "downgrade", "earnings_gap_down", "threat")
    ]
    if derate_events:
        ev = derate_events[0]
        return f"{ev.event_type.value} on {ev.event_date} + {gate_detail['G1_drawdown']}"
    return f"{gate_detail['G1_drawdown']} (no discrete event detected — price-drop trigger)"


def evaluate_screen2(
    rec: DataRecord,
    *,
    screen_run_at: datetime,
    thresholds: Screen2Thresholds | None = None,
) -> CandidateRecord | None:
    """Evaluate Screen 2 on a data-record. Returns a candidate-record iff admitted, else None."""
    th = thresholds or Screen2Thresholds()
    results: dict[str, GateResult] = {}
    detail: dict[str, str] = {}
    for name, fn in (
        ("G1_drawdown", gate_g1_drawdown),
        ("G2_idiosyncratic", gate_g2_idiosyncratic),
        ("G3_multiple_floor", gate_g3_multiple_floor),
    ):
        results[name], detail[name] = fn(rec, th)

    admitted = GateResult.FAIL not in results.values() and results["G1_drawdown"] is GateResult.PASS
    if not admitted:
        return None

    return CandidateRecord(
        candidate_id=f"{rec.identity.ticker}-screen2-{screen_run_at:%Y%m%d}",
        data_record=rec,
        screens_fired=["screen_2"],
        gate_results=results,
        trigger_reason=_trigger_reason(rec, detail),
        unknown_gates_for_depth=derive_unknown_gates(results),
        twin_to_rule_out=TWIN,
        triage_band=_triage(rec),
        screen_run_at=screen_run_at,
    )
