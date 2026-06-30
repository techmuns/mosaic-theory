"""SUB-STEP 0 — megacap leader designation (the foundation Components B and C both need).

Component A detects in the $10B-capped ``in_universe``, so its clusters contain NO mega-caps — yet
the theme's LEADERS (whose pattern B reads and whose run C confirms) are >$10B (Part 7: AI-infra =
NVDA/AVGO; housing = DHI/LEN; gold = NEM/AEM). So Stage 2 ASSEMBLES the leaders from OUTSIDE A's
universe, **read-only and confirmation-side only**: a >$10B operating-co slice (reusing the
``build_universe`` machinery), from which a mega-cap is designated a theme leader iff it BOTH
(a) matches the cluster's SIC classes AND (b) residually CO-MOVES with the cluster — the same
co-movement test that defined the theme, applied to the mega-cap band. The machine assembles
(breadth across the whole market a human can't recall); the **analyst ratifies** the set as part of
criterion-1 driver-naming. **A's detection and the sub-$10B holding book are NOT touched** — these
>$10B names exist only to compute the confirmation (C) and leader-first (B) signals.

The mega-cap's residual is computed against A's factor set (market + sector cohort + size + vol)
with the FULL broad-sector cohort (it is not a cohort member, so no leave-one-out), reusing the
committed OLS — never re-fitting or perturbing A's residuals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from vinci.config import Config
from vinci.edgar import EdgarClient
from vinci.eod import PolygonEodClient
from vinci.eod.client import EodClient
from vinci.progress import ProgressFn, ProgressReporter
from vinci.resolver import EntityResolver, ResolutionError
from vinci.sectors import sector_for_sic
from vinci.themes.cluster import _pearson
from vinci.themes.residualize import FactorSet, _ols_residuals, daily_returns
from vinci.themes.schemas import FactorBasis, LeaderSet, MegaLeader
from vinci.universe import admit_security_type, latest_close_and_adv, recent_share_periods

# face-validity: a leader's median residual corr with the cluster must clear this
_CORR_FLOOR = 0.30
_MIN_OVERLAP = 60  # min common days to correlate a leader with a cluster member


@dataclass(frozen=True)
class MegaCap:
    internal_id: str
    ticker: str
    cik: str
    name: str
    market_cap: float
    sic: str | None
    sector: str


@dataclass(frozen=True)
class MegaContext:
    """The >$10B slice + each name's residual vs A's factors (built once, reused across themes)."""

    mega: list[MegaCap]
    residuals: dict[str, dict[date, float]]  # by internal_id, residualized against A's FactorSet
    closes: dict[str, dict[date, float]]  # by TICKER — for B's trajectory + C's confirmation return
    by_id: dict[str, MegaCap]


def pull_symbol_closes(
    eod: EodClient, symbols: set[str], calendar: list[date]
) -> dict[str, dict[date, float]]:
    """Extract closes for ``symbols`` from cached grouped-daily over the calendar (read-only)."""
    out: dict[str, dict[date, float]] = {s: {} for s in symbols}
    for d in calendar:
        bars = eod.grouped_daily(d)
        if not bars:
            continue
        for s in symbols:
            b = bars.get(s)
            if b is not None and b.close > 0:
                out[s][d] = b.close
    return out


def mega_cap_slice(
    cfg: Config,
    resolver: EntityResolver,
    eod: PolygonEodClient,
    edgar: EdgarClient,
    *,
    reference_date: date,
    progress: ProgressFn | None = None,
) -> list[MegaCap]:
    """The >$10B operating-company slice (market cap = close × XBRL shares), gated like the
    universe.

    Reuses the ``build_universe`` breadth tools read-only; it does NOT write the universe or change
    Component A — it is a separate confirmation-side assembly above the $10B holding ceiling.
    """
    band = cfg.universe
    closes, _adv = latest_close_and_adv(eod, reference_date)
    sec_types = eod.security_types()
    shares = edgar.shares_outstanding_by_cik(recent_share_periods(reference_date))
    out: list[MegaCap] = []
    for ident in resolver.iter_universe(band.exchanges):
        close = closes.get(ident.eod_symbol)
        sh = shares.get(ident.cik)
        if close is None or sh is None:
            continue
        cap = close * sh
        if cap <= band.market_cap_max_usd:  # >$10B ONLY (the leaders A's universe excludes)
            continue
        if not admit_security_type(sec_types.get(ident.eod_symbol), band.allowed_security_types):
            continue
        try:
            sic = resolver.sic_for(ident.cik)[0] if ident.cik else None
        except (ResolutionError, KeyError, ValueError, OSError):
            sic = None
        if sic is None or sic in band.excluded_sic_codes:  # operating-cos only (fail-closed)
            continue
        out.append(
            MegaCap(
                internal_id=ident.internal_id, ticker=ident.eod_symbol, cik=ident.cik,
                name=ident.name, market_cap=cap, sic=sic, sector=sector_for_sic(sic),
            )
        )
    return out


def _residualize_external(
    returns: dict[date, float], factors: FactorSet, sector: str
) -> dict[date, float] | None:
    """Residual of a NON-cohort name against A's factors — FULL broad-sector cohort (no LOO)."""
    days = sorted(returns)
    y = [returns[d] for d in days]
    ssum, scnt = factors.sector_sum.get(sector, {}), factors.sector_count.get(sector, {})
    market_col = [factors.market.get(d, 0.0) for d in days]
    sector_col = [ssum.get(d, 0.0) / scnt[d] if scnt.get(d, 0) > 0 else 0.0 for d in days]
    cols = [market_col, sector_col]
    if factors.basis is FactorBasis.FULL:
        cols.append([factors.size.get(d, 0.0) for d in days])
        cols.append([factors.vol.get(d, 0.0) for d in days])
    return _ols_residuals(days, y, cols)


def build_mega_context(
    cfg: Config,
    resolver: EntityResolver,
    eod: PolygonEodClient,
    edgar: EdgarClient,
    *,
    reference_date: date,
    factors: FactorSet,
    calendar: list[date],
    progress: ProgressFn | None = None,
) -> MegaContext:
    """Assemble the >$10B slice, pull its window closes, and residualize each name vs A's
    factors."""
    mega = mega_cap_slice(
        cfg, resolver, eod, edgar, reference_date=reference_date, progress=progress
    )
    closes = pull_symbol_closes(eod, {m.ticker for m in mega}, calendar)
    residuals: dict[str, dict[date, float]] = {}
    rep = ProgressReporter("residualizing leaders", len(mega), emit=progress)
    for i, m in enumerate(mega, 1):
        r = daily_returns(closes.get(m.ticker, {}), calendar)
        if r:
            eps = _residualize_external(r, factors, m.sector)
            if eps is not None:
                residuals[m.internal_id] = eps
        rep.tick(i)
    return MegaContext(
        mega=mega, residuals=residuals, closes=closes, by_id={m.internal_id: m for m in mega}
    )


def designate_leaders(
    cluster_member_ids: list[str],
    cluster_residuals: dict[str, dict[date, float]],
    ctx: MegaContext,
    cluster_sics: set[str],
    calendar: list[date],
    *,
    corr_floor: float = _CORR_FLOOR,
) -> LeaderSet:
    """Designate the theme's candidate mega-cap leaders: SIC-matched AND residually co-moving.

    Co-movement = the mega-cap's median residual correlation with the cluster members ≥
    ``corr_floor`` (the same residual-correlation standard that defined the theme). Machine
    assembles; analyst ratifies.
    """
    pos = {d: i for i, d in enumerate(calendar)}

    def aligned(eps: dict[date, float]) -> tuple[tuple[int, ...], tuple[float, ...]]:
        items = sorted((pos[d], v) for d, v in eps.items() if d in pos)
        return tuple(i for i, _ in items), tuple(v for _, v in items)

    member_vecs = [
        aligned(cluster_residuals[m]) for m in cluster_member_ids if m in cluster_residuals
    ]
    leaders: list[MegaLeader] = []
    for m in ctx.mega:
        if m.sic not in cluster_sics or m.internal_id not in ctx.residuals:
            continue
        ai, av = aligned(ctx.residuals[m.internal_id])
        corrs = [
            c for bi, bv in member_vecs
            if (c := _pearson(ai, av, bi, bv, _MIN_OVERLAP)) is not None
        ]
        if not corrs:
            continue
        med = sorted(corrs)[len(corrs) // 2]
        if med >= corr_floor:
            leaders.append(
                MegaLeader(
                    ticker=m.ticker, name=m.name, cik=m.cik, market_cap=m.market_cap, sic=m.sic,
                    sector=m.sector, residual_corr_to_cluster=med,
                    source_ref=(
                        f"cap close×XBRL-shares ${m.market_cap / 1e9:.0f}B; "
                        f"SIC {m.sic} (EDGAR)"
                    ),
                )
            )
    leaders.sort(key=lambda x: x.market_cap, reverse=True)
    rule = (
        f">$10B operating-cos whose SIC ∈ the cluster's classes AND whose median residual "
        f"correlation with the cluster ≥ {corr_floor:.2f} (the co-movement test that defined the "
        f"theme)"
    )
    return LeaderSet(
        rule=rule,
        leaders=leaders,
        ratification_note="ASSEMBLED candidates — the analyst ratifies (add/remove) as part of "
        "naming the driver (criterion 1); these >$10B names never enter detection or holding.",
    )
