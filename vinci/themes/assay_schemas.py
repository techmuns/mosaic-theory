"""Earliness-assay v0 schemas — assemble-not-conclude (the ``schemas.py`` doctrine).

Two axes per candidate theme, POINT-IN-TIME: (x) disclosed-activity velocity — new filers first-
mentioning the theme's terms per quarter; (y) the price response of a mechanically-derived "obvious
basket" — median excess re-rating vs IWM AND SPY. The per-quarter position is a QUADRANT
characterization (EARLY / PRICED / QUIET / NARRATIVE), the same *kind* of factual label as
``ExposureBasis`` — NEVER a composite score, a rank, or a buy/avoid verdict. The human reads the
card; the machine only assembles it.

Insufficient data is ``None`` + a logged reason (``data_gaps`` / ``caveats``), NEVER a silent 0.0.
NO ``score`` / ``rank`` / ``verdict`` / ``recommend`` field exists anywhere in the tree, by design —
pinned by the no-conclude schema-walk guard (mirrors ``tests/test_dossier.py``).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateSpec(BaseModel, frozen=True):
    """A theme to assay. ``terms`` are IMPORTED BY IDENTITY from a ``DriverSpec.prefilter_terms`` —
    one term source shared with the exposure scan, never a hand-edited copy."""

    key: str
    terms: tuple[str, ...]
    note: str


class BasketMember(BaseModel, frozen=True):
    """One mechanically-selected obvious-basket name (top mention-count, cap-banded). Listed, not
    weighted or ranked — ordering is by mention-count for readability, NOT a quality ranking."""

    ticker: str
    cik: str
    mention_count: int
    cap_asof: float | None  # as-of cap (shares×price); None ⇒ unresolvable (reason in cap_method)
    cap_method: str  # how the cap was derived, OR the drop/degrade reason (never fabricated)


class QuarterRead(BaseModel, frozen=True):
    """One quarter's two-axis read. Every price field is ``float | None``; ``None`` ⇒ a reason in
    ``data_gaps`` (insufficient/absent data is never smoothed to 0.0)."""

    quarter: str  # "YYYYQn"
    new_filers: int  # CIKs first-mentioning ANY term in this quarter (the velocity axis)
    total_mentions: int  # total efts hits across the theme's terms this quarter
    mentions_8k_family: int  # 8-K / press-family split (PRINTED, not weighted — v0)
    mentions_10k_family: int  # 10-K / 10-Q family split
    basket_excess_iwm: float | None  # basket median cumulative return − IWM, from the 8q baseline
    basket_excess_spy: float | None  # basket median cumulative return − SPY
    quadrant_by_combo: dict[str, str]  # combo key → quadrant (EARLY/PRICED/QUIET/NARRATIVE/UNKNOWN)
    data_gaps: list[str] = Field(default_factory=list)


class Residence(BaseModel, frozen=True):
    """EARLY-quadrant residence under ONE boundary combo."""

    longest_early_run: int  # longest run of CONSECUTIVE EARLY quarters (the kill-criterion metric)
    total_early_quarters: int


class AssayCard(BaseModel, frozen=True):
    """One candidate's assay at an as-of. Assemble-not-conclude: NO score / rank / verdict field.

    ``basket_rule`` is the verbatim mechanical selection rule (printed on every card).
    ``residence_by_combo`` maps each combo → its EARLY residence; ``divergence_age_quarters`` =
    quarters of standing activity-vs-price divergence to the as-of under the reference combo (None
    if none / insufficient). ``caveats`` MUST carry the point-in-time notes.
    """

    candidate_key: str
    as_of: str
    quarters: tuple[QuarterRead, ...]
    basket: tuple[BasketMember, ...]
    basket_rule: str
    residence_by_combo: dict[str, Residence]
    divergence_age_quarters: int | None
    caveats: list[str] = Field(default_factory=list)
