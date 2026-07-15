"""Single-source pin for the theme-page "What this theme is" content.

`frontend/themes/context.json` is analyst-owned, but its ``driver_summary`` is NOT free text — it
is the ratified ``DriverSpec`` description's opening sentence, QUOTED verbatim. This test binds the
committed file to `vinci.themes.drivers` so the quote cannot silently drift from the ratified
definition (the single-source rule). The ``analyst_notes`` are judgment and are NOT pinned here —
only their presence/shape is checked.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vinci.themes.drivers import AI_DATACENTER, DEFENSE_DEMAND_SHIFT, TRUCKLOAD_SUPPLY_PURGE

_CONTEXT = Path(__file__).resolve().parents[1] / "frontend" / "themes" / "context.json"

# theme-page slug (getThemeDriver fetches ./themes/<slug>.json) → the ratified spec it quotes.
# NB: the defense theme's slug is "defense", not the driver key "defense-demand-shift".
_SLUG_TO_SPEC = {
    "ai-datacenter": AI_DATACENTER,
    "defense": DEFENSE_DEMAND_SHIFT,
    "truckload-supply-purge": TRUCKLOAD_SUPPLY_PURGE,
}


def _first_sentence(description: str) -> str:
    """The opening sentence of a DriverSpec description (the same rule the generator used)."""
    return description.split(". ", 1)[0] + "."


def _context() -> dict[str, Any]:
    ctx: dict[str, Any] = json.loads(_CONTEXT.read_text())
    return ctx


def test_driver_summary_is_the_spec_first_sentence_verbatim() -> None:
    ctx = _context()
    for slug, spec in _SLUG_TO_SPEC.items():
        assert slug in ctx, f"context.json missing theme {slug!r}"
        ds = ctx[slug]["driver_summary"]
        assert ds["quote"] == _first_sentence(spec.description), (
            f"{slug} driver_summary drifted from the ratified spec — regenerate context.json")
        assert ds["source"] == "ratified driver definition"


def test_every_context_theme_maps_to_a_ratified_spec() -> None:
    """No context.json theme may exist without a backing ratified spec (no orphan quoted text)."""
    for slug in _context():
        assert slug in _SLUG_TO_SPEC, f"context.json theme {slug!r} has no backing DriverSpec"


def test_analyst_notes_present_and_are_nonempty_strings() -> None:
    ctx = _context()
    # truckload carries the four judgment lines; the two calibration themes carry one each.
    assert len(ctx["truckload-supply-purge"]["analyst_notes"]) == 4
    for slug in _SLUG_TO_SPEC:
        notes = ctx[slug]["analyst_notes"]
        assert notes and all(isinstance(n, str) and n.strip() for n in notes), slug


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
