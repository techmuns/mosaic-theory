"""Stage-2 orchestration — Components B (theme-type signals) + C (megacap confirmation) over A's
themes.

READ-ONLY: A's detection / clustering / residualization and the sub-$10B holding universe are NOT
touched. This replays A's pipeline read-only to get the clusters + residuals, then ASSEMBLES the
>$10B
leaders (SUB-STEP 0), the type signals (B), and the confirmation signal (C) for each theme — all
presented for the analyst to judge (no auto-classification, no type verdict, no autonomous trigger).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from vinci.config import Config, get_config
from vinci.edgar import EdgarClient
from vinci.eod import PolygonEodClient
from vinci.progress import ProgressFn
from vinci.resolver import EntityResolver
from vinci.themes import cluster as cl
from vinci.themes import detection as det
from vinci.themes import leaders as ld
from vinci.themes.classify import assemble_type_signals, compute_price_pattern, historical_analog
from vinci.themes.confirmation import confirmation_signal
from vinci.themes.linkage import candidate_linkage
from vinci.themes.residualize import build_factors, daily_returns, residualize
from vinci.themes.schemas import FactorBasis, ThemeMember, ThemeStage2

_BREADTH_FLOOR = 3  # same machine-checkable gates A uses (persistence already validated in A)
_COHERENCE_FLOOR = 0.30


def analyze_stage2(
    config: Config | None = None,
    *,
    reference_date: date | None = None,
    window_days: int = 365,
    max_names: int | None = None,
    llm: Any | None = None,
    progress: ProgressFn | None = None,
) -> list[ThemeStage2]:
    """Run Components B + C over A's admissible candidate themes."""
    cfg = config or get_config()
    resolver = EntityResolver.from_config(cfg)
    eod = PolygonEodClient.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)

    names, snap = det.load_detection_universe(cfg)
    if max_names is not None:
        names = names[:max_names]
    ref = reference_date or snap
    name_by_id = {n.internal_id: n for n in names}
    cap_of = {n.internal_id: n.market_cap for n in names}
    sic_of, sector_of, _ = det.resolve_sectors(resolver, names, progress=progress)
    closes_by_id, iwm, calendar = det.pull_closes(
        eod, names, reference_date=ref, window_days=window_days, progress=progress
    )
    returns_by_id = {
        n.internal_id: r
        for n in names
        if (r := daily_returns(closes_by_id.get(n.internal_id, {}), calendar))
    }
    market_returns = daily_returns(iwm, calendar)

    # A's residual clustering (R2), read-only — exactly as detection does it
    factors_r2 = build_factors(returns_by_id, market_returns=market_returns, sector_of=sector_of,
                               market_cap_of=cap_of, calendar=calendar, basis=FactorBasis.FULL)
    resid_r2, _ = residualize(returns_by_id, factors_r2, sector_of)
    clusters = cl.find_clusters(resid_r2, calendar)
    # R1 edges for the vol-strip-survival signal
    # (did the R2 cluster also cohere before the vol strip?)
    factors_r1 = build_factors(returns_by_id, market_returns=market_returns, sector_of=sector_of,
                               market_cap_of=cap_of, calendar=calendar,
                               basis=FactorBasis.MARKET_SECTOR)
    resid_r1, _ = residualize(returns_by_id, factors_r1, sector_of)
    edges_r1, _ = cl.compute_edges(resid_r1, calendar)

    # SUB-STEP 0 context (the >$10B leader slice) + SPY (Finding-2 broad benchmark)
    ctx = ld.build_mega_context(cfg, resolver, eod, edgar, reference_date=ref, factors=factors_r2,
                                calendar=calendar, progress=progress)
    spy = ld.pull_symbol_closes(eod, {"SPY"}, calendar).get("SPY", {})

    out: list[ThemeStage2] = []
    for k, rc in enumerate(clusters):
        if len(rc.members) < _BREADTH_FLOOR or rc.coherence < _COHERENCE_FLOOR:
            continue
        members = rc.members
        present = [m for m in members if m in name_by_id]
        member_tickers = [name_by_id[m].ticker for m in present]
        cluster_sics = {s for m in members if (s := sic_of.get(m))}
        tm = [
            ThemeMember(ticker=name_by_id[m].ticker, name=name_by_id[m].name, cik=name_by_id[m].cik,
                        sic=sic_of.get(m), sector=sector_of.get(m, "Unknown"),
                        sic_source_ref=f"EDGAR SIC for CIK {name_by_id[m].cik}")
            for m in present
        ]
        linkage = candidate_linkage(tm)

        leader_set = ld.designate_leaders(members, resid_r2, ctx, cluster_sics, calendar)
        leader_closes = {x.ticker: ctx.closes.get(x.ticker, {}) for x in leader_set.leaders}

        # vol-strip survival: did the cluster's core also cohere under R1 (before the vol strip)?
        seed = members[0]
        r1_comp = next((c for c in cl._components(edges_r1, 0.50) if seed in c), set())
        retention = len(set(members) & r1_comp) / len(members) if members else 0.0
        survived = retention >= 0.5
        vol_note = f"{retention:.0%} of members also co-cluster under R1 (pre-vol-strip)"

        member_closes = {m: closes_by_id[m] for m in members if m in closes_by_id}
        pattern = compute_price_pattern(leader_closes, member_closes, calendar=calendar,
                                        reference_date=ref)
        # LLM analog only when leaders exist (bounds cost to the type-relevant themes)
        analog = historical_analog(
            linkage.shared_note, [x.ticker for x in leader_set.leaders], member_tickers,
            llm=llm if leader_set.leaders else None,
        )
        type_signals = assemble_type_signals(pattern, vol_strip_survived=survived,
                                             vol_strip_note=vol_note, analog=analog)
        conf = (
            confirmation_signal(leader_set.leaders, leader_closes, iwm_closes=iwm, spy_closes=spy,
                                calendar=calendar)
            if leader_set.leaders
            else None
        )
        out.append(ThemeStage2(
            cluster_id=f"T{k:03d}", member_tickers=member_tickers,
            candidate_linkage_note=linkage.shared_note, leader_set=leader_set,
            type_signals=type_signals, confirmation=conf,
        ))
    return out
