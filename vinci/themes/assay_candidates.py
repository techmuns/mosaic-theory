"""Candidate registry for the earliness assay.

Theme ``terms`` are IMPORTED BY IDENTITY from the matching ``DriverSpec``'s ``prefilter_terms`` —
the assay and the exposure scan draw from ONE term source, never a hand-edited copy. A drift between
the two is then structurally impossible (pinned by a test).

``placebo-boilerplate`` is a VALIDATION INSTRUMENT (is_placebo=True), NOT a theme: near-universal
boilerplate whose new-filer series ≈ raw new-registrant flow. Theme cards print a per-quarter RATIO
of theme to placebo new-filers, so a "2021 bump" that is really a listing wave (placebo up too) is
visible. The operator may swap the placebo terms (a placebo has no DriverSpec to borrow from).
"""

from __future__ import annotations

from vinci.themes.assay_schemas import CandidateSpec
from vinci.themes.drivers import DRIVER_SPECS

PLACEBO_KEY = "placebo-boilerplate"

CANDIDATE_SPECS: dict[str, CandidateSpec] = {
    "ai-datacenter": CandidateSpec(
        key="ai-datacenter",
        terms=DRIVER_SPECS["ai-datacenter"].prefilter_terms,  # identity, not a copy-edit
        note="AI-datacenter value-chain demand — the driver's own prefilter terms.",
    ),
    "defense-demand-shift": CandidateSpec(
        key="defense-demand-shift",
        terms=DRIVER_SPECS["defense-demand-shift"].prefilter_terms,  # identity, not a copy-edit
        note="Defense compositional-shift demand — the driver's own prefilter terms.",
    ),
    PLACEBO_KEY: CandidateSpec(
        key=PLACEBO_KEY,
        terms=(
            "annual meeting of stockholders",
            "board of directors",
            "income taxes",
            "working capital",
            "forward-looking statements",
        ),
        note="VALIDATION INSTRUMENT (not a theme): near-universal boilerplate ≈ raw new-registrant "
             "flow. The null the theme ratio must clear.",
        is_placebo=True,
    ),
}
