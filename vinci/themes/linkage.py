"""Criterion-1 SURFACE — propose the candidate shared-linkage; the analyst names the driver.

The machine assembles **what the members share** (their sub-sectors and the cross-taxonomy span),
source-bound to the linkage evidence (each member's EDGAR SIC), and presents it as a prompt for the
analyst — it **never names or ratifies a driver** (`theme_admissibility.md` criterion 1; CLAUDE.md:
the machine proposes, the human concludes). A cluster the analyst cannot name is a momentum bucket
and is inadmissible — that verdict is the human's, exactly like the BUY/AVOID verdict.

The cross-taxonomy signal (members spanning >1 SIC and/or >1 sector) is the value co-movement adds
over SIC: SIC dismembers a real theme into different codes (quantum = 7371/7372/7374; housing = 14
SICs / 5 sectors), and surfacing that span is precisely the candidate the analyst judges.
"""

from __future__ import annotations

from vinci.themes.schemas import CandidateLinkage, ThemeMember


def candidate_linkage(members: list[ThemeMember]) -> CandidateLinkage:
    """Assemble the candidate shared-linkage for a cluster — descriptive, never a named driver."""
    distinct_sics = sorted({m.sic for m in members if m.sic})
    distinct_sectors = sorted({m.sector for m in members})
    crosses = len(distinct_sics) > 1 or len(distinct_sectors) > 1

    span = (
        f"{len(members)} names spanning {len(distinct_sics)} SIC(s) across "
        f"{len(distinct_sectors)} sector(s) ({', '.join(distinct_sectors)})"
    )
    if crosses:
        note = (
            f"{span} — a candidate CROSS-TAXONOMY shared end-market/driver SIC alone cannot group; "
            "the analyst names the driver, or rejects the cluster as a driver-less momentum bucket."
        )
    else:
        note = (
            f"{span} — a single sub-sector cohort; the analyst judges whether a real driver links "
            "these names beyond shared industry beta, or it is a momentum bucket."
        )
    return CandidateLinkage(
        distinct_sics=distinct_sics,
        distinct_sectors=distinct_sectors,
        crosses_taxonomy=crosses,
        shared_note=note,
    )
