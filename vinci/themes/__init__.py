"""Theme detection — Component A (Stage 1 of the theme edge).

Residual co-movement clustering that PROPOSES candidate themes (cluster + candidate shared-linkage +
strength signals) for the analyst to judge. It assembles and cites; it never names a driver, ranks
themes, confirms, selects, or concludes (`theme_admissibility.md`; STATE.md §4 PHASE-0.7/0.8).
Stages 2–4 (confirmation trigger, semantic exposure-classifier/text, pipeline composition) are NOT
built here.
"""

from __future__ import annotations

from vinci.themes.detection import detect_themes
from vinci.themes.render import render_result, render_theme
from vinci.themes.schemas import (
    CandidateTheme,
    FactorBasis,
    ThemeDetectionResult,
)

__all__ = [
    "CandidateTheme",
    "FactorBasis",
    "ThemeDetectionResult",
    "detect_themes",
    "render_result",
    "render_theme",
]
