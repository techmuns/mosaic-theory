"""ONE company-label resolver — every surface resolves sector/industry through here.

The repo grew FIVE labeling lenses (coarse SIC sector, hand-rolled SIC sub-industries, CIQ GICS
on dossiers, a frontend static SIC map, the theme chain-layer). The first four collapse onto this
module + the vendored official SIC table; the theme chain-layer is a different taxonomy and stays
where it is. PRECEDENCE per name:

    CIQ GICS (a committed dossier carries it — depth-stage, manual, ~10 names)
      → official SEC SIC industry title (universe-wide, `vinci.sic_table`)
        → "Unknown" (blank/non-numeric SIC — fail-honest, never guessed)

``sector`` is ALWAYS the coarse `sector_for_sic` bucket regardless of GICS: it is the STABLE
grouping axis (per-sector BUY−AVOID spread, overshoot roll-up, theme factor inputs) and a manual
CIQ pull must never silently reshuffle a grouping. Provenance travels with every resolved label
(`industry_source`), per the fund's source-bound discipline.

Boundaries: `vinci.sectors` stays the pure code→name table (no IO); THIS module owns
resolution + provenance (+ one filesystem reader over committed dossier artifacts). The AST fence
(tests/test_rank.py) forbids `vinci.rank`/`vinci.screens` from importing labels or sectors —
labels INFORM, they never gate, rank, or decide. `frontend/build.py` (stdlib-only) never imports
this module — resolved labels reach it as emitted artifact data.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from vinci.sectors import industry_for_sic, sector_for_sic

IndustrySource = Literal["ciq-gics", "sic", "unknown"]


class CompanyLabel(BaseModel, frozen=True):
    """One name's resolved display labels + provenance."""

    sector: str                          # ALWAYS the coarse SIC bucket — the stable grouping axis
    industry: str                        # best-available fine label per the precedence above
    industry_source: IndustrySource
    industry_source_ref: str | None = None   # the CIQ source_ref when ciq-gics; None otherwise


def resolve_label(sic: str | int | None, *, gics: str | None = None,
                  gics_source_ref: str | None = None) -> CompanyLabel:
    """Resolve one name's labels. ``gics`` is the CIQ GICS industry WHEN PRESENT (callers pass the
    ``Sourced`` value only for status=="present" — an UNKNOWN CIQ read must arrive as None, never
    as a placeholder string)."""
    sector = sector_for_sic(sic)
    if gics is not None and gics.strip():
        return CompanyLabel(sector=sector, industry=gics.strip(), industry_source="ciq-gics",
                            industry_source_ref=gics_source_ref)
    industry = industry_for_sic(sic)
    if industry == "Unknown":
        return CompanyLabel(sector=sector, industry="Unknown", industry_source="unknown")
    return CompanyLabel(sector=sector, industry=industry, industry_source="sic")


def committed_gics_index(dossier_root: Path) -> dict[str, dict[str, str]]:
    """{TICKER: {"industry": ..., "source_ref": ...}} for every committed dossier whose CIQ-GICS
    ``industry`` field is status=="present". Reads the committed artifacts (as-of discipline —
    the label a surface shows is the label the committed dossier carries), skips absent/unknown
    LOUDLY-honestly (no entry), and never fabricates."""
    out: dict[str, dict[str, str]] = {}
    if not dossier_root.is_dir():
        return out
    for folder in sorted(p for p in dossier_root.iterdir() if p.is_dir()):
        f = folder / "dossier.json"
        if not f.is_file():
            continue
        doc = json.loads(f.read_text())
        ind = doc.get("industry") or {}
        if ind.get("status") == "present" and (ind.get("value") or "").strip():
            out[folder.name.upper()] = {
                "industry": ind["value"].strip(),
                "source_ref": ind.get("source_ref") or "",
            }
    return out
