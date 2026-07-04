"""Residual co-movement clustering — criterion-3-as-basis (STATE.md §4 §3.0 amendment).

Given the de-confounded residual returns (``residualize``), cluster names by **residual
correlation**: a threshold graph → connected components, the method the spikes used (τ=0.50).
Stage 1 makes the selection **principled, not a single hardcoded τ** (the review's build condition):

- correlations computed once, edges retained above a floor;
- clusters taken at a central face-validity τ, then **checked for τ-band stability** — a real
  theme's core stays connected across a band of thresholds, a knife-edge artifact does not;
- **coherence** (mean intra-cluster residual correlation) computed EXACTLY from the residuals, which
  is criterion 3's gate and dissolves the chained blobs connected-components can otherwise glue
  together.

All thresholds are face-validity constants, never tuned on forward returns (the ranker's
no-forward-returns discipline; an AST test pins that ``vinci.themes`` imports no scoring/ledger).
Pure Python: a merge-join Pearson over each pair's overlapping days (handles ragged coverage), and
union-find for the components.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date

# Face-validity selection constants (set by what reads as a cluster, NEVER by what would have paid).
_EDGE_FLOOR = 0.40  # retain only pairs at/above this; the τ band lives above it
_TAU_CENTRAL = 0.50  # the spikes' production threshold (STATE.md §4 PHASE-0.7)
# the cluster core must survive across this band (stability, not one τ)
_TAU_BAND = (0.45, 0.50, 0.55)
_MIN_OVERLAP = 60  # a pair needs at least this many common days to correlate (else no edge)
_BLOWUP = 2.0  # at a looser τ a stable core may grow, but not merge into a >2× blob


@dataclass(frozen=True)
class RawCluster:
    """A connected component of residually co-moving names + its principled-selection evidence."""

    members: list[str]
    coherence: float  # exact mean intra-cluster residual correlation (criterion-3 gate input)
    tau_stability: list[float] = field(default_factory=list)  # τ in the band the core survived


# --------------------------------------------------------------------------------------------------
# Correlation
# --------------------------------------------------------------------------------------------------
def _aligned(
    residuals: dict[str, dict[date, float]], calendar: list[date]
) -> dict[str, tuple[tuple[int, ...], tuple[float, ...]]]:
    """Index each name's residuals against the master calendar → (sorted idx tuple, value tuple)."""
    pos = {d: i for i, d in enumerate(calendar)}
    out: dict[str, tuple[tuple[int, ...], tuple[float, ...]]] = {}
    for name, eps in residuals.items():
        items = sorted((pos[d], v) for d, v in eps.items() if d in pos)
        if items:
            out[name] = (tuple(i for i, _ in items), tuple(v for _, v in items))
    return out


def _pearson(
    ai: tuple[int, ...], av: tuple[float, ...],
    bi: tuple[int, ...], bv: tuple[float, ...],
    min_overlap: int,
) -> float | None:
    """Pearson correlation over the common indices of two sorted (idx, val) series (merge-join)."""
    p = q = 0
    n = 0
    sx = sy = sxx = syy = sxy = 0.0
    while p < len(ai) and q < len(bi):
        if ai[p] == bi[q]:
            x, y = av[p], bv[q]
            n += 1
            sx += x
            sy += y
            sxx += x * x
            syy += y * y
            sxy += x * y
            p += 1
            q += 1
        elif ai[p] < bi[q]:
            p += 1
        else:
            q += 1
    if n < min_overlap:
        return None
    cov = n * sxy - sx * sy
    vx = n * sxx - sx * sx
    vy = n * syy - sy * sy
    if vx <= 0.0 or vy <= 0.0:
        return None
    return cov / math.sqrt(vx * vy)


def compute_edges(
    residuals: dict[str, dict[date, float]],
    calendar: list[date],
    *,
    floor: float = _EDGE_FLOOR,
    min_overlap: int = _MIN_OVERLAP,
) -> tuple[list[tuple[str, str, float]], dict[str, tuple[tuple[int, ...], tuple[float, ...]]]]:
    """All pairwise residual correlations at/above ``floor`` (the work; reused across the τ band).

    Returns the edge list and the aligned-series map (so coherence can be recomputed exactly later).
    """
    aligned = _aligned(residuals, calendar)
    names = sorted(aligned)
    edges: list[tuple[str, str, float]] = []
    for i in range(len(names)):
        ai, av = aligned[names[i]]
        for j in range(i + 1, len(names)):
            bi, bv = aligned[names[j]]
            c = _pearson(ai, av, bi, bv, min_overlap)
            if c is not None and c >= floor:
                edges.append((names[i], names[j], c))
    return edges, aligned


def mean_intra_correlation(
    members: list[str],
    aligned: dict[str, tuple[tuple[int, ...], tuple[float, ...]]],
    *,
    min_overlap: int = _MIN_OVERLAP,
) -> float:
    """Exact mean pairwise residual correlation among ``members`` (criterion-3 coherence value).

    Computed directly from the residuals — including pairs below the edge floor — so a
    chained/blobby component (loosely strung together) reads its true low coherence, not an
    edge-filtered overestimate.
    """
    vals: list[float] = []
    for i in range(len(members)):
        if members[i] not in aligned:
            continue
        ai, av = aligned[members[i]]
        for j in range(i + 1, len(members)):
            if members[j] not in aligned:
                continue
            bi, bv = aligned[members[j]]
            c = _pearson(ai, av, bi, bv, min_overlap)
            if c is not None:
                vals.append(c)
    return sum(vals) / len(vals) if vals else 0.0


# --------------------------------------------------------------------------------------------------
# Components
# --------------------------------------------------------------------------------------------------
def _components(edges: list[tuple[str, str, float]], tau: float) -> list[set[str]]:
    """Connected components of the graph whose edges are the pairs with correlation ≥ ``tau``."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    for a, b, c in edges:
        if c >= tau:
            parent[find(a)] = find(b)
    groups: dict[str, set[str]] = {}
    for node in parent:
        groups.setdefault(find(node), set()).add(node)
    return list(groups.values())


def _stable_taus(
    core: set[str], edges: list[tuple[str, str, float]], band: tuple[float, ...]
) -> list[float]:
    """The τ in ``band`` at which ``core`` stays a single connected cluster (not split, not
    blobbed)."""
    need = math.ceil(0.6 * len(core))
    out: list[float] = []
    for tau in band:
        for comp in _components(edges, tau):
            overlap = len(comp & core)
            if overlap >= need and len(comp) <= _BLOWUP * len(core):
                out.append(tau)
                break
    return out


def connected_fraction(
    members: list[str],
    residuals: dict[str, dict[date, float]],
    calendar: list[date],
    *,
    tau: float = _TAU_CENTRAL,
    min_overlap: int = _MIN_OVERLAP,
) -> float:
    """Largest fraction of ``members`` that stays mutually connected (≥ ``tau``) on ``residuals``.

    Used for criterion-4 persistence: re-residualize the cluster's members on a recent sub-window
    and ask whether the basket still co-moves there (months-to-quarters), not just over the full
    window.
    """
    if not members:
        return 0.0
    aligned = _aligned({m: residuals[m] for m in members if m in residuals}, calendar)
    names = sorted(aligned)
    edges: list[tuple[str, str, float]] = []
    for i in range(len(names)):
        ai, av = aligned[names[i]]
        for j in range(i + 1, len(names)):
            bi, bv = aligned[names[j]]
            c = _pearson(ai, av, bi, bv, min_overlap)
            if c is not None and c >= tau:
                edges.append((names[i], names[j], c))
    comps = _components(edges, tau)
    return (max(len(c) for c in comps) / len(members)) if comps else 0.0


def find_clusters(
    residuals: dict[str, dict[date, float]],
    calendar: list[date],
    *,
    tau_central: float = _TAU_CENTRAL,
    tau_band: tuple[float, ...] = _TAU_BAND,
    min_breadth: int = 3,
) -> list[RawCluster]:
    """Cluster the residuals into candidate themes (connected components ≥ ``min_breadth``).

    Each cluster carries its exact coherence and the τ-band stability evidence (principled
    selection, not a single τ). Singletons/pairs below ``min_breadth`` are not emitted (the breadth
    gate proper lives in ``gates`` — this is just the cluster-size floor for "a basket")."""
    edges, aligned = compute_edges(residuals, calendar)
    clusters: list[RawCluster] = []
    for comp in _components(edges, tau_central):
        if len(comp) < min_breadth:
            continue
        members = sorted(comp)
        clusters.append(
            RawCluster(
                members=members,
                coherence=mean_intra_correlation(members, aligned),
                tau_stability=_stable_taus(comp, edges, tau_band),
            )
        )
    # display order only — NOT a quality rank
    clusters.sort(key=lambda c: len(c.members), reverse=True)
    return clusters
