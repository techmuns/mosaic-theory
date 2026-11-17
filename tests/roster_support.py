"""Test support: write a coverage roster into a synthetic tree, through the one line writer.

A synthetic tree that holds pages now holds a roster too: every reader that walks the covered names
reads `data/coverage_roster.jsonl` and refuses a page it does not cover (W27)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from vinci import coverage_roster as roster


def write_roster(data_dir: Path, statuses: dict[str, str], *, on: str = "2026-11-13") -> Path:
    """One move per name, all on one date, in the roster's canonical form and order."""
    lines = [roster.render_line(roster.Move(
        date=date.fromisoformat(on), ticker=t, status=s, ruling="test", source="test",
        record=None)) for t, s in sorted(statuses.items())]
    data_dir.mkdir(parents=True, exist_ok=True)
    path = roster.roster_path(data_dir)
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path
