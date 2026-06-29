"""The admissibility SCREEN — criteria 2/3/4 as PASS/FAIL gates (`theme_admissibility.md` §2).

NOT a ranker: gates are necessary conditions, not weighted or scored, and themes are never ranked
against one another. Criterion 1 (nameable driver) is NOT here — it is the analyst's judgment on the
candidate linkage. All thresholds are **face-validity** constants, never tuned on forward returns:

- **breadth** — "a basket, not a pair." No magic N tuned on returns; the floor is the structural
  minimum that is strictly more than a pair (3), a knob the analyst can raise by face-validity.
- **coherence** — the mean intra-cluster residual correlation (after market+sector+size+vol
  stripping) clears a floor, so a loosely-chained connected-component blob fails while a real
  diffuse theme (housing ≈ 0.37 in the spikes) passes.
- **persistence** — the cluster's members still co-move in a recent sub-window (months-to-quarters,
  not a one-week blip); detection supplies the member-retention across windows.
"""

from __future__ import annotations

from vinci.themes.cluster import RawCluster
from vinci.themes.schemas import AdmissibilityReport

# Face-validity floors (set by what reads as a theme, NEVER by what grouping would have paid).
_BREADTH_FLOOR = 3  # strictly more than a pair — the "basket not pair" structural minimum
# below this a connected component is chained, not a coherent residual basket
_COHERENCE_FLOOR = 0.30
# a majority of the basket must recur in the recent sub-window (persistence)
_RETENTION_FLOOR = 0.50


def evaluate_admissibility(
    cluster: RawCluster,
    *,
    member_retention: float | None,
    persistence_note: str,
    breadth_floor: int = _BREADTH_FLOOR,
    coherence_floor: float = _COHERENCE_FLOOR,
    retention_floor: float = _RETENTION_FLOOR,
) -> AdmissibilityReport:
    """Apply the three machine-checkable gates to one cluster (PASS/FAIL, with transparent values).

    ``member_retention is None`` means persistence could NOT be evaluated (the detection window was
    not longer than the persistence sub-window). That is fail-loud (CLAUDE.md): an un-evaluable
    criterion is NOT admissible — never a fabricated pass that silently admits a theme the data
    cannot support."""
    breadth_value = len(cluster.members)
    breadth_pass = breadth_value >= breadth_floor
    coherence_pass = cluster.coherence >= coherence_floor
    persistence_pass = (
        member_retention is not None and member_retention >= retention_floor
    )

    reasons: list[str] = []
    if not breadth_pass:
        reasons.append(f"breadth {breadth_value} < {breadth_floor} (a pair/too thin, not a basket)")
    if not coherence_pass:
        reasons.append(
            f"coherence {cluster.coherence:.2f} < {coherence_floor:.2f} "
            "(loosely chained, not a coherent residual basket)"
        )
    if member_retention is None:
        reasons.append(
            "persistence NOT evaluable — detection window ≤ the persistence sub-window "
            "(use a longer --window-days); not admitted on an untested criterion"
        )
    elif not persistence_pass:
        reasons.append(
            f"persistence: {member_retention:.0%} of members recur in the recent sub-window "
            f"(< {retention_floor:.0%}) — a blip, not months-to-quarters"
        )

    return AdmissibilityReport(
        breadth_value=breadth_value,
        breadth_pass=breadth_pass,
        coherence_value=cluster.coherence,
        coherence_pass=coherence_pass,
        persistence_pass=persistence_pass,
        persistence_note=persistence_note,
        fail_reasons=reasons,
    )
