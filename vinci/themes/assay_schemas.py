"""Earliness-assay schemas — assemble-not-conclude (the ``schemas.py`` doctrine).

Two axes per candidate theme, POINT-IN-TIME: (x) disclosed-activity velocity — new filers first-
mentioning the theme's terms per quarter; (y) the price response of a mechanically-derived "obvious
basket" — median excess re-rating vs IWM AND SPY. The per-quarter position is a QUADRANT
characterization (EARLY / PRICED / QUIET / NARRATIVE), the same *kind* of factual label as
``ExposureBasis`` — NEVER a composite score, a rank, or a buy/avoid verdict. The human reads the
card; the machine only assembles it.

Insufficient data is ``None`` + a logged reason (``data_gaps`` / ``caveats``), NEVER a silent 0.0.
NO ``score`` / ``rank`` / ``verdict`` / ``recommend`` field exists anywhere in the tree, by design —
pinned by the no-conclude schema-walk guard (mirrors ``tests/test_dossier.py``).

v1 hardens the velocity axis + card legibility and records BOTH definitions side by side: the
recorded v0 basis is new_filers (window-relative) + quadrant_by_combo + residence_by_combo;
the v1 calendar-anchored definition is ``new_filers_anchored`` + ``quadrant_by_combo_anchored`` +
``residence_by_combo_anchored``. The anchored definition is computed ALONGSIDE and its adoption is
PENDING OPERATOR SANCTION — nothing here reclassifies the recorded v0 verdict.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateSpec(BaseModel, frozen=True):
    """A theme to assay. ``terms`` are IMPORTED BY IDENTITY from a ``DriverSpec.prefilter_terms`` —
    one term source shared with the exposure scan, never a hand-edited copy. ``is_placebo`` marks a
    VALIDATION INSTRUMENT (near-universal boilerplate ≈ raw new-registrant flow), not a theme."""

    key: str
    terms: tuple[str, ...]
    note: str
    is_placebo: bool = False


class BasketMember(BaseModel, frozen=True):
    """One mechanically-selected obvious-basket name (top mention-count, cap-banded). Listed, not
    weighted or ranked — ordering is by mention-count for readability, NOT a quality ranking."""

    ticker: str
    cik: str
    mention_count: int
    cap_asof: float | None  # as-of cap (shares×price); None ⇒ unresolvable (reason in cap_method)
    cap_method: str  # how the cap was derived, OR the drop/degrade reason (never fabricated)
    # v1 cap provenance (facts behind the number; print-only)
    shares_source: str = ""  # which XBRL frame set supplied the shares
    share_count: float | None = None  # the raw cover-page share count
    price_date: str = ""  # the as-of date the close is from
    cap_qoq_flag: str | None = None  # print-only sanity flag: cap moved >5x in some QoQ step


class TermContribution(BaseModel, frozen=True):
    """One term's new-filer contribution in a quarter (decomposition, aggregation-only). A single
    new filer may be counted under >1 term, so contributions can sum above new_filers."""

    term: str
    new_filers: int


class QuarterRead(BaseModel, frozen=True):
    """One quarter's two-axis read. Every price field is ``float | None``; ``None`` ⇒ a reason in
    ``data_gaps`` (insufficient/absent data is never smoothed to 0.0)."""

    quarter: str  # "YYYYQn"
    new_filers: int  # RECORDED v0: CIKs first-mentioning within the card window (window-relative)
    new_filers_anchored: int  # v1: CIKs new vs a FIXED trailing-12q lookback (window-independent)
    total_mentions: int  # total efts hits across the theme's terms this quarter
    mentions_8k_family: int  # 8-K / press-family split (PRINTED, not weighted)
    mentions_10k_family: int  # 10-K / 10-Q family split
    basket_excess_iwm: float | None  # basket median cumulative return − IWM, from the 8q baseline
    basket_excess_spy: float | None  # basket median cumulative return − SPY
    quadrant_by_combo: dict[str, str]  # RECORDED: combo → quadrant under window-relative velocity
    quadrant_by_combo_anchored: dict[str, str]  # v1: combo → quadrant under the anchored velocity
    rising_median_4q: float | None  # medrise input: trailing-4q median of the recorded velocity
    rising_slope_4q: float | None  # classifier input (sloperise): OLS slope over the trailing 4q
    top_terms: tuple[TermContribution, ...] = ()  # decomposition (anchored-new attribution)
    placebo_ratio: float | None = None  # theme/placebo anchored-filers (None-safe)
    derated_early: bool = False  # excess vs BOTH benchmarks < −20% (a DERATED-EARLY annotation)
    data_gaps: list[str] = Field(default_factory=list)


class Residence(BaseModel, frozen=True):
    """EARLY-quadrant residence under ONE boundary combo."""

    longest_early_run: int  # longest run of CONSECUTIVE EARLY quarters (the kill-criterion metric)
    total_early_quarters: int


class AssayCard(BaseModel, frozen=True):
    """One candidate's assay at an as-of. Assemble-not-conclude: NO score / rank / verdict field.

    ``basket_rule`` is the verbatim mechanical selection rule (printed on every card). Residence is
    recorded THREE ways: ``residence_by_combo`` (RECORDED v0, window-relative velocity),
    ``residence_by_combo_anchored`` (v1 anchored velocity — adoption PENDING SANCTION), and
    ``residence_by_combo_symmetric`` (a ±band flat rule, reported-only, fed to NO verdict).
    """

    candidate_key: str
    as_of: str
    quarters: tuple[QuarterRead, ...]
    basket: tuple[BasketMember, ...]
    basket_rule: str
    residence_by_combo: dict[str, Residence]  # RECORDED v0 basis
    residence_by_combo_anchored: dict[str, Residence]  # v1 anchored (alongside; PENDING SANCTION)
    residence_by_combo_symmetric: dict[str, Residence]  # ±band flat (reported-only, no verdict)
    divergence_age_quarters: int | None
    is_placebo: bool = False
    caveats: list[str] = Field(default_factory=list)
