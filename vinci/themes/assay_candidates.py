"""Candidate registry for the earliness assay.

The ``terms`` for each candidate are IMPORTED BY IDENTITY from the matching ``DriverSpec``'s
``prefilter_terms`` — the assay and the exposure scan draw from ONE term source, never a hand-edited
copy. A drift between the two is then structurally impossible (pinned by a test).
"""

from __future__ import annotations

from vinci.themes.assay_schemas import CandidateSpec
from vinci.themes.drivers import DRIVER_SPECS

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
}
