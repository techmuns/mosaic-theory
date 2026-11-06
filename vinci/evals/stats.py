"""Exact tests for comparing two sets of synthesis draws — no sampling, no seed, no SciPy.

THE UNIT IS THE DRAW. Points inside one draw are not independent (one draw writes all of them from
one reading), so a count of flagged points is descriptive; the test runs on one number per draw.

THE PANEL TEST is a stratified permutation test. Within each page, the base and candidate draws
are exchangeable under the null (same inputs, same model, the code change does nothing). Its
statistic is the candidate draws' total, summed over pages; its null distribution is the
convolution of each page's distribution over every way of choosing which of the pooled draws are
"candidate" — EXACT, because a page has C(10, 5) = 252 such choices and the convolution of six is
small. Pages are never pooled across, so a page whose base rate is high cannot carry another
page's effect.

``fisher_two_sided`` is the 2x2 test #920 read five draws against five by, kept so a one-page
comparison here gives the number that record's table gives.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import comb


@dataclass(frozen=True)
class PageDraws:
    """One page's per-draw values (a metric's count, or 0/1) under the two conditions."""

    page: str
    base: tuple[int, ...]
    cand: tuple[int, ...]


@dataclass(frozen=True)
class StratifiedResult:
    """The candidate total, its null mean, and the two one-sided exact p-values.

    ``p_lower`` is P(total <= observed) — evidence the candidate FLAGS LESS (an improvement for an
    error metric). ``p_upper`` is P(total >= observed) — evidence it flags MORE (a worsening).
    Both are exact fractions of equally likely relabelings, rendered as floats only for display.
    """

    observed: int
    null_mean: Fraction
    p_lower: Fraction
    p_upper: Fraction
    base_total: int
    cand_total: int
    pages: int


def _page_null(values: Sequence[int], n_cand: int) -> Counter[int]:
    """Every way of labelling ``n_cand`` of the pooled draws as candidate → the count of each sum.
    Draws are distinct objects even when their values tie, so ties are counted, not collapsed."""
    dist: Counter[int] = Counter()
    for idx in combinations(range(len(values)), n_cand):
        dist[sum(values[i] for i in idx)] += 1
    return dist


def _convolve(a: Counter[int], b: Counter[int]) -> Counter[int]:
    out: Counter[int] = Counter()
    for x, nx in a.items():
        for y, ny in b.items():
            out[x + y] += nx * ny
    return out


def stratified_exact(pages: Sequence[PageDraws]) -> StratifiedResult:
    """The exact stratified permutation test over ``pages`` (see the module docstring).

    Raises ``ValueError`` on an empty panel or a page with no draw in one condition — a page that
    lost every draw of a condition carries no comparison, and silently dropping it would shrink
    the panel without saying so."""
    if not pages:
        raise ValueError("no pages to compare")
    total: Counter[int] = Counter({0: 1})
    observed = base_total = cand_total = 0
    for p in pages:
        if not p.base or not p.cand:
            raise ValueError(f"{p.page}: a condition has no draws (base {len(p.base)}, "
                             f"cand {len(p.cand)})")
        pooled = list(p.base) + list(p.cand)
        total = _convolve(total, _page_null(pooled, len(p.cand)))
        observed += sum(p.cand)
        base_total += sum(p.base)
        cand_total += sum(p.cand)
    n = sum(total.values())
    lower = sum(c for s, c in total.items() if s <= observed)
    upper = sum(c for s, c in total.items() if s >= observed)
    mean = Fraction(sum(s * c for s, c in total.items()), n)
    return StratifiedResult(observed=observed, null_mean=mean, p_lower=Fraction(lower, n),
                            p_upper=Fraction(upper, n), base_total=base_total,
                            cand_total=cand_total, pages=len(pages))


def fisher_two_sided(a: int, n_a: int, b: int, n_b: int) -> Fraction:
    """Fisher's exact test, two-sided, on ``a`` of ``n_a`` against ``b`` of ``n_b``: the summed
    probability of every table with the same margins that is no more likely than the observed one
    (the convention #920's table used — 5/5 vs 0/5 gives 0.008, 3/5 vs 0/5 gives 0.167)."""
    k, n = a + b, n_a + n_b
    denom = comb(n, k)

    def prob(x: int) -> Fraction:
        return Fraction(comb(n_a, x) * comb(n_b, k - x), denom)

    p_obs = prob(a)
    lo, hi = max(0, k - n_b), min(k, n_a)
    return sum((prob(x) for x in range(lo, hi + 1) if prob(x) <= p_obs), Fraction(0))
