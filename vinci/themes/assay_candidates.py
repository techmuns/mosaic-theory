"""Candidate registry for the earliness assay.

Theme ``terms`` are IMPORTED BY IDENTITY from the matching ``DriverSpec``'s ``prefilter_terms`` —
the assay and the exposure scan draw from ONE term source, never a hand-edited copy. A drift between
the two is then structurally impossible (pinned by a test).

``placebo-boilerplate`` is a VALIDATION INSTRUMENT (is_placebo=True), NOT a theme: near-universal
boilerplate whose new-filer series ≈ raw new-registrant flow. Theme cards print a per-quarter RATIO
of theme to placebo new-filers, so a "2021 bump" that is really a listing wave (placebo up too) is
visible. The operator may swap the placebo terms (a placebo has no DriverSpec to borrow from).

v2 DRAFT analyst TIERS (specific_terms / context_terms) — PENDING RATIFICATION. context = broad
terms a wave produces regardless of theme; specific = the remaining shift-specific terms whose
INCUMBENT first-mentions are the contrast signal. context must be a subset of the driver prefilter,
and specific+context PARTITION ``terms`` (fail-loud). The placebo is ALL-SPECIFIC so its incumbent-
specific series is computed identically and reads ~noise (the machinery null).
"""

from __future__ import annotations

from vinci.themes.assay_schemas import CandidateSpec
from vinci.themes.drivers import DRIVER_SPECS

PLACEBO_KEY = "placebo-boilerplate"

_CONTEXT: dict[str, tuple[str, ...]] = {
    "defense-demand-shift": ("defense", "military", "warfighter", "autonomy", "ISR"),
    "ai-datacenter": ("artificial intelligence", "data center", "accelerator", "thermal management",
                      "switchgear"),
}

_PLACEBO_TERMS = (
    "annual meeting of stockholders",
    "board of directors",
    "income taxes",
    "working capital",
    "forward-looking statements",
)


def _theme(key: str, note: str) -> CandidateSpec:
    """A theme candidate with DRAFT tiers computed from its driver prefilter (identity kept)."""
    terms = DRIVER_SPECS[key].prefilter_terms  # identity, not a copy-edit
    context = _CONTEXT[key]
    missing = [t for t in context if t not in terms]
    if missing:  # fail loud — a DRAFT context term must be a real prefilter term
        raise ValueError(f"{key}: DRAFT context terms not in prefilter: {missing}")
    specific = tuple(t for t in terms if t not in context)  # partition; prefilter order preserved
    return CandidateSpec(
        key=key, terms=terms, note=note, specific_terms=specific, context_terms=context)


CANDIDATE_SPECS: dict[str, CandidateSpec] = {
    "ai-datacenter": _theme(
        "ai-datacenter", "AI-datacenter value-chain demand — the driver's own prefilter terms."),
    "defense-demand-shift": _theme(
        "defense-demand-shift",
        "Defense compositional-shift demand — the driver's own prefilter terms."),
    PLACEBO_KEY: CandidateSpec(
        key=PLACEBO_KEY,
        terms=_PLACEBO_TERMS,
        note="VALIDATION INSTRUMENT (not a theme): near-universal boilerplate ≈ raw new-registrant "
             "flow. The null the theme ratio must clear.",
        is_placebo=True,
        specific_terms=_PLACEBO_TERMS,  # ALL terms SPECIFIC → the incumbent-specific machinery null
        context_terms=(),
    ),
}
