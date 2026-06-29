"""Multi-factor residualization — the de-confounding leg of theme criterion 3 (STATE.md §4
PHASE-0.7).

Criterion 3 (`theme_admissibility.md`): a theme is the **residual shared variance** that survives
stripping **market + broad-sector + size + volatility** beta — the same "the control says no"
discipline as Edge-2's G2 (`vinci/eod/features.relative_return` is the G2 market-residual; this
generalizes the same pattern to the full factor set). The fail-loud discipline carries over
verbatim: a name with insufficient overlapping history is **EXCLUDED and counted — never a
partial-window number**.

THE SECTOR LEG, DONE PROPERLY (the one genuinely new data-leg in Stage 1). The throwaway spikes
stripped the sector by SUBTRACTING the leave-one-out coarse-sector cohort mean 1:1 (an implicit
β=1, applied sequentially after the market). That is the version STATE.md §2's G2 caveat calls
unbuilt and the review (`theme_admissibility_review.md`) says "Phase 1 must build properly." Here
the sector factor is a **leave-one-out broad-sector cohort return whose loading β_sector is
ESTIMATED JOINTLY with the market (and size/vol) loadings by OLS** — so it neither over- nor
under-strips, and the market common to the sector is not double-counted (the joint regression
assigns the market-common part to the market factor). It is leave-one-out so a name never explains
itself, and the cohort is the BROAD sector (all in-universe peers), so a single small theme barely
moves it (minimal endogeneity).

Pure Python (no numpy — the codebase keeps the core dependency-free, like
``metrics.ols_beta_alpha``): a small symmetric linear solve over a ≤5-parameter normal-equations
system per name.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from vinci.themes.schemas import FactorBasis

# Face-validity constants (set by what reads as a sound regression, NEVER tuned on forward
# returns).
_MIN_OBS = 60  # a name needs at least this many aligned daily returns to residualize (else UNKNOWN)
# a factor column with variance below this is degenerate → dropped for that name
_ZERO_VAR_EPS = 1e-12


# --------------------------------------------------------------------------------------------------
# Returns alignment
# --------------------------------------------------------------------------------------------------
def daily_returns(closes: dict[date, float], calendar: list[date]) -> dict[date, float]:
    """Simple returns on **consecutive calendar days where both closes exist** (no gap-spanning).

    A return is recorded for day ``d`` only if the name has a positive close on ``d`` AND on the
    immediately-preceding calendar day — a missed day breaks the chain rather than spanning the gap
    (which would fabricate a multi-day move as a one-day return). Missing → simply absent.
    """
    out: dict[date, float] = {}
    for i in range(1, len(calendar)):
        d, prev = calendar[i], calendar[i - 1]
        c, pc = closes.get(d), closes.get(prev)
        if c is not None and pc is not None and c > 0 and pc > 0:
            out[d] = c / pc - 1.0
    return out


def realized_vol(returns: dict[date, float]) -> float | None:
    """Sample stdev of a return series — the size/vol-factor sort key. None if too few points."""
    vals = list(returns.values())
    return statistics.pstdev(vals) if len(vals) >= 2 else None


# --------------------------------------------------------------------------------------------------
# Factor construction (built from the universe itself + the IWM benchmark)
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class FactorSet:
    """The confounding factors, as daily-return series keyed by calendar date.

    ``sector_sum`` / ``sector_count`` carry the per-(sector, day) cohort sum and headcount so the
    leave-one-out sector factor for a member can be formed as ``(sum - r_i) / (count - 1)``.
    """

    basis: FactorBasis
    market: dict[date, float]
    size: dict[date, float]
    vol: dict[date, float]
    sector_sum: dict[str, dict[date, float]]
    sector_count: dict[str, dict[date, int]]


def _tercile_spread(
    returns_by_name: dict[str, dict[date, float]],
    rank_key: dict[str, float],
    calendar: list[date],
) -> dict[date, float]:
    """A long/short factor return: mean return of the TOP tercile − the BOTTOM tercile, by
    ``rank_key``.

    Used for SMB (rank_key = market cap → small minus big) and the vol/speculative factor
    (rank_key = realized vol → high minus low). The vol factor is the proven-selective lever
    (STATE.md §4): the
    speculative-beta glue lives in the high-vol tercile, so regressing it out dissolves the risk-on
    amalgam while leaving diffuse low-vol themes (housing) intact.
    """
    ranked = sorted(rank_key, key=lambda n: rank_key[n])
    if len(ranked) < 3:
        return {}
    cut = len(ranked) // 3
    low = set(ranked[:cut])
    high = set(ranked[-cut:])
    out: dict[date, float] = {}
    for d in calendar:
        hi = [returns_by_name[n][d] for n in high if d in returns_by_name.get(n, {})]
        lo = [returns_by_name[n][d] for n in low if d in returns_by_name.get(n, {})]
        if hi and lo:
            out[d] = statistics.fmean(hi) - statistics.fmean(lo)
    return out


def build_factors(
    returns_by_name: dict[str, dict[date, float]],
    *,
    market_returns: dict[date, float],
    sector_of: dict[str, str],
    market_cap_of: dict[str, float],
    calendar: list[date],
    basis: FactorBasis,
) -> FactorSet:
    """Assemble the factor set for ``basis`` (R1 = market+sector; FULL/R2 adds size+vol)."""
    # Broad-sector cohort sums/counts per day (the BROAD sector — all in-universe peers).
    sec_sum: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    sec_cnt: dict[str, dict[date, int]] = defaultdict(lambda: defaultdict(int))
    for name, rets in returns_by_name.items():
        sec = sector_of.get(name, "Unknown")
        for d, r in rets.items():
            sec_sum[sec][d] += r
            sec_cnt[sec][d] += 1

    size: dict[date, float] = {}
    vol: dict[date, float] = {}
    if basis is FactorBasis.FULL:
        caps = {n: market_cap_of[n] for n in returns_by_name if n in market_cap_of}
        size = _tercile_spread(returns_by_name, caps, calendar)
        vols = {
            n: v for n, rets in returns_by_name.items() if (v := realized_vol(rets)) is not None
        }
        vol = _tercile_spread(returns_by_name, vols, calendar)

    return FactorSet(
        basis=basis,
        market=market_returns,
        size=size,
        vol=vol,
        sector_sum={s: dict(v) for s, v in sec_sum.items()},
        sector_count={s: dict(v) for s, v in sec_cnt.items()},
    )


# --------------------------------------------------------------------------------------------------
# Pure-Python OLS (normal equations + symmetric Gaussian elimination)
# --------------------------------------------------------------------------------------------------
def solve_symmetric(a: list[list[float]], b: list[float]) -> list[float] | None:
    """Solve ``A x = b`` for small symmetric ``A`` via Gaussian elimination with partial pivoting.

    Returns None if ``A`` is (numerically) singular — the caller treats that as fail-loud UNKNOWN
    (e.g. a degenerate/collinear design), never a fabricated coefficient.
    """
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]  # augmented
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-15:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        piv = m[col][col]
        for r in range(n):
            if r == col:
                continue
            factor = m[r][col] / piv
            if factor != 0.0:
                for c in range(col, n + 1):
                    m[r][c] -= factor * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def _ols_residuals(
    days: list[date], y: list[float], cols: list[list[float]]
) -> dict[date, float] | None:
    """Residuals of ``y`` regressed on an intercept + ``cols`` (each a same-length factor column).

    Degenerate (near-constant) factor columns are dropped before the solve so a name with, e.g., no
    sector peers does not make the system singular. Returns None if too few observations remain or
    the system is singular (fail-loud → the name is excluded and counted, never partially imputed).
    """
    n = len(y)
    if n < _MIN_OBS:
        return None
    design = [[1.0] for _ in range(n)]  # intercept
    for col in cols:
        if statistics.pvariance(col) > _ZERO_VAR_EPS:  # drop a degenerate column
            for i in range(n):
                design[i].append(col[i])
    k = len(design[0])
    if n < k + 10:  # keep a comfortable margin of observations over parameters
        return None
    # Normal equations: (XᵀX) β = Xᵀy
    xtx = [[sum(design[r][i] * design[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    xty = [sum(design[r][i] * y[r] for r in range(n)) for i in range(k)]
    beta = solve_symmetric(xtx, xty)
    if beta is None:
        return None
    return {days[r]: y[r] - sum(beta[i] * design[r][i] for i in range(k)) for r in range(n)}


def residualize(
    returns_by_name: dict[str, dict[date, float]],
    factors: FactorSet,
    sector_of: dict[str, str],
) -> tuple[dict[str, dict[date, float]], list[str]]:
    """Residualize every name against the factor set. Returns (residuals_by_name, dropped_names).

    For each name the design is [intercept, market, sector_LOO, (size, vol if FULL)] over the name's
    own return days; the residual ε_i is the de-confounded return series clustered on downstream. A
    name that fails to residualize (too few obs / singular) is **dropped and reported** — fail-loud.
    """
    residuals: dict[str, dict[date, float]] = {}
    dropped: list[str] = []
    for name, rets in returns_by_name.items():
        days = sorted(rets)
        y = [rets[d] for d in days]
        market_col = [factors.market.get(d, 0.0) for d in days]
        sec = sector_of.get(name, "Unknown")
        ssum, scnt = factors.sector_sum.get(sec, {}), factors.sector_count.get(sec, {})
        sector_col: list[float] = []
        for d in days:
            cnt = scnt.get(d, 0)
            # leave-one-out cohort mean: remove this name's own return from the broad-sector mean
            sector_col.append((ssum.get(d, 0.0) - rets[d]) / (cnt - 1) if cnt > 1 else 0.0)
        cols = [market_col, sector_col]
        if factors.basis is FactorBasis.FULL:
            cols.append([factors.size.get(d, 0.0) for d in days])
            cols.append([factors.vol.get(d, 0.0) for d in days])
        eps = _ols_residuals(days, y, cols)
        if eps is None:
            dropped.append(name)
        else:
            residuals[name] = eps
    return residuals, dropped
