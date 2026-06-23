"""Per-screen gate evaluators. Loop 1 ships Screen 2 (overshot de-rating)."""

from vinci.screens.assemble import (
    annual_eps_as_of,
    build_data_record,
    build_price_record,
    detect_gap_downs,
    enrich_with_fundamentals,
    pe_current_and_percentile,
)
from vinci.screens.run import screen_universe
from vinci.screens.screen2 import (
    Screen2Thresholds,
    evaluate_screen2,
    gate_g1_drawdown,
    gate_g2_idiosyncratic,
    gate_g3_multiple_floor,
)

__all__ = [
    "Screen2Thresholds",
    "annual_eps_as_of",
    "build_data_record",
    "build_price_record",
    "detect_gap_downs",
    "enrich_with_fundamentals",
    "evaluate_screen2",
    "gate_g1_drawdown",
    "gate_g2_idiosyncratic",
    "gate_g3_multiple_floor",
    "pe_current_and_percentile",
    "screen_universe",
]
