"""Component A orchestration — broad universe → residual co-movement → candidate themes.

This is the Stage-1 detector end to end (`theme_admissibility.md`; STATE.md §4 PHASE-0.7/0.8): the
BROAD ``in_universe`` set (NOT the overshoot screen — mega/mid included for theme visibility), 12mo
daily closes from the EXISTING ``PolygonEodClient`` (Bearer key from env, never logged),
residualized against market+sector+size+vol, clustered on the residual, gated on
breadth/coherence/persistence, and surfaced with the criterion-1 candidate linkage + §7.1 strength
signals — for the analyst to judge.

It **assembles and proposes; it never concludes** — no theme is named, ranked, or bought here. Fail
loud: a name with insufficient overlapping history is dropped and counted, never partially imputed.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from vinci.config import Config, get_config
from vinci.eod import PolygonEodClient
from vinci.eod.client import EodClient
from vinci.labels import resolve_label
from vinci.progress import ProgressFn, ProgressReporter
from vinci.resolver import EntityResolver, ResolutionError
from vinci.sectors import sector_for_sic
from vinci.themes import cluster as cl
from vinci.themes.gates import evaluate_admissibility
from vinci.themes.linkage import candidate_linkage
from vinci.themes.residualize import build_factors, daily_returns, residualize
from vinci.themes.schemas import (
    CandidateTheme,
    DetectionStats,
    FactorBasis,
    ThemeDetectionResult,
    ThemeMember,
    WindowSpec,
)
from vinci.themes.signals import compute_strength_signals

_PERSIST_DAYS = 126  # ~6mo recent sub-window for the persistence check (months-to-quarters)


@dataclass(frozen=True)
class _Name:
    internal_id: str
    ticker: str  # the EOD/Polygon symbol (what the analyst recognises)
    cik: str
    name: str
    market_cap: float
    #: WHICH population admitted this name — "primary" (the forward-validation band) or "theme"
    #: (the parallel larger band, 2026-08-31). Carried so every theme-altitude surface can say
    #: where a name came from; a row without provenance is a row that invites the wrong inference.
    band: str = "primary"


def theme_band_as_of(cfg: Config) -> date | None:
    """The committed theme band's own vintage, or None when the band was never built.

    Split out so a caller can PRINT the vintage beside the count: the two bands are built by
    separate runs, and a theme population silently ageing behind the primary one is the
    stale-input class this repo keeps closing elsewhere."""
    p = cfg.snapshots_dir / "theme_universe_snapshot.jsonl"
    if not p.exists():
        return None
    dates = [date.fromisoformat(json.loads(x)["as_of"])
             for x in p.read_text().splitlines() if x.strip()]
    return max(dates) if dates else None


def load_detection_universe(
    cfg: Config, *, include_theme_band: bool = False
) -> tuple[list[_Name], date]:
    """The broad ``in_universe`` set from the committed snapshots (no DB, no network).

    DEFAULTS TO THE PRIMARY BAND ALONE — corrected at review, 2026-08-31, and the reason is the
    whole point of the parallel band. This loader feeds TWO very different consumers:

    * the DRIVER EXPOSURE SCAN, which reads each name's filings independently. Widening its
      population adds names and changes nothing about the names already there. It opts in.
    * COMPONENT A / stage-2 residual detection, which builds CROSS-SECTIONAL factors — the SMB
      leg is a tercile of the population's market caps (``residualize._tercile_spread``) and the
      sector legs are cohort sums. Adding 810 names spanning $10B-$3.7T re-cuts those terciles,
      so EVERY existing primary name's residual moves, its clusters move, and a megacap can enter
      a cluster it is then designated the external "leader" of (``leaders.mega_cap_slice`` is the
      same >$10B population, and its leave-one-out premise assumes non-membership). None of that
      is a theme-band feature; it is a silent redefinition of a different measurement.

    So the union is OPT-IN per call site, not per checkout. ``include_theme_band=True`` unions the
    committed ``theme_universe_snapshot.jsonl`` when present and tags those names ``band="theme"``.

    The returned ``as_of`` is the PRIMARY snapshot's date — the population's own vintage. The
    theme band's rows are filtered to their own latest ``as_of`` independently (see
    :func:`theme_band_as_of`), because the two bands are built by separate runs.
    """
    snaps = cfg.snapshots_dir
    # securities: internal_id → identity
    idents: dict[str, dict[str, str]] = {}
    for line in (snaps / "securities.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            idents[r["internal_id"]] = r
    # universe membership: latest as_of, in_universe only, with market cap
    rows = [
        json.loads(x)
        for x in (snaps / "universe_snapshot.jsonl").read_text().splitlines()
        if x.strip()
    ]
    as_of = max(date.fromisoformat(r["as_of"]) for r in rows)
    names: list[_Name] = []
    for r in rows:
        if date.fromisoformat(r["as_of"]) != as_of or not r.get("in_universe"):
            continue
        ident = idents.get(r["internal_id"])
        cap = r.get("market_cap")
        if ident is None or cap is None:
            continue
        names.append(
            _Name(
                internal_id=r["internal_id"],
                ticker=ident["eod_symbol"],
                cik=ident["cik"],
                name=ident["name"],
                market_cap=float(cap),
            )
        )
    theme_path = snaps / "theme_universe_snapshot.jsonl"
    if include_theme_band and theme_path.exists():
        seen = {n.internal_id for n in names}
        trows = [json.loads(x) for x in theme_path.read_text().splitlines() if x.strip()]
        if trows:
            t_as_of = max(date.fromisoformat(r["as_of"]) for r in trows)
            for r in trows:
                if date.fromisoformat(r["as_of"]) != t_as_of or not r.get("in_universe"):
                    continue
                # A name in BOTH bands keeps its PRIMARY row — the decision-path population wins
                # the identity, so nothing downstream can see one name under two bands.
                if r["internal_id"] in seen:
                    continue
                ident = idents.get(r["internal_id"])
                cap = r.get("market_cap")
                if ident is None or cap is None:
                    continue
                seen.add(r["internal_id"])
                names.append(
                    _Name(
                        internal_id=r["internal_id"],
                        ticker=ident["eod_symbol"],
                        cik=ident["cik"],
                        name=ident["name"],
                        market_cap=float(cap),
                        band="theme",
                    )
                )
    return names, as_of


def resolve_sectors(
    resolver: EntityResolver, names: list[_Name], *, progress: ProgressFn | None = None
) -> tuple[dict[str, str | None], dict[str, str], int]:
    """Live-fetch each name's EDGAR SIC (cached) → (sic_by_id, sector_by_id, n_resolved). Fail-loud:
    a name whose SIC will not resolve is sector ``Unknown`` (honest), counted — never fabricated."""
    sic_by_id: dict[str, str | None] = {}
    sector_by_id: dict[str, str] = {}
    resolved = 0
    rep = ProgressReporter("resolving SIC", len(names), emit=progress)
    for i, n in enumerate(names, 1):
        try:
            sic = resolver.sic_for(n.cik)[0] if n.cik else None
        except (ResolutionError, KeyError, ValueError, OSError):
            sic = None
        if sic is not None:
            resolved += 1
        sic_by_id[n.internal_id] = sic
        sector_by_id[n.internal_id] = sector_for_sic(sic)
        rep.tick(i)
    return sic_by_id, sector_by_id, resolved


def pull_closes(
    eod: EodClient,
    names: list[_Name],
    *,
    reference_date: date,
    window_days: int,
    progress: ProgressFn | None = None,
) -> tuple[dict[str, dict[date, float]], dict[date, float], list[date]]:
    """Pull daily closes for the universe + IWM from cached grouped-daily. Returns
    (closes_by_id, iwm_closes, master_calendar). Weekends skipped; non-trading days return {}."""
    symbol_to_id = {n.ticker: n.internal_id for n in names}
    needed = set(symbol_to_id) | {"IWM"}
    closes_by_id: dict[str, dict[date, float]] = defaultdict(dict)
    iwm: dict[date, float] = {}
    start = reference_date - timedelta(days=window_days)
    days = [start + timedelta(days=i) for i in range((reference_date - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]  # skip weekends (no grouped-daily)
    rep = ProgressReporter("pulling EOD", len(days), emit=progress)
    for i, d in enumerate(days, 1):
        bars = eod.grouped_daily(d)  # {} on a non-trading day (holiday) — legitimate, skipped
        if bars:
            for sym in needed:
                b = bars.get(sym)
                if b is not None and b.close > 0:
                    if sym == "IWM":  # the benchmark is not a universe member — keep it separate
                        iwm[d] = b.close
                    else:
                        closes_by_id[symbol_to_id[sym]][d] = b.close
        rep.tick(i)
    calendar = sorted(iwm)  # master trading calendar = days IWM has a bar
    return dict(closes_by_id), iwm, calendar


def detect_themes(
    config: Config | None = None,
    *,
    reference_date: date | None = None,
    window_days: int = 365,
    basis: FactorBasis = FactorBasis.FULL,
    min_breadth: int = 3,
    max_names: int | None = None,
    persist_days: int = _PERSIST_DAYS,
    progress: ProgressFn | None = None,
) -> ThemeDetectionResult:
    """Run Component A on the broad universe for one factor basis. Assembles candidate themes."""
    cfg = config or get_config()
    resolver = EntityResolver.from_config(cfg)
    eod = PolygonEodClient.from_config(cfg)

    names, snap_as_of = load_detection_universe(cfg)
    if max_names is not None:
        names = names[:max_names]
    ref = reference_date or snap_as_of
    name_by_id = {n.internal_id: n for n in names}
    cap_of = {n.internal_id: n.market_cap for n in names}

    sic_of, sector_of, n_sic = resolve_sectors(resolver, names, progress=progress)
    closes_by_id, iwm, calendar = pull_closes(
        eod, names, reference_date=ref, window_days=window_days, progress=progress
    )

    # returns + residualization over the full window
    returns_by_id: dict[str, dict[date, float]] = {}
    for n in names:
        r = daily_returns(closes_by_id.get(n.internal_id, {}), calendar)
        if r:
            returns_by_id[n.internal_id] = r
    market_returns = daily_returns(iwm, calendar)
    factors = build_factors(
        returns_by_id, market_returns=market_returns, sector_of=sector_of,
        market_cap_of=cap_of, calendar=calendar, basis=basis,
    )
    residuals, dropped = residualize(returns_by_id, factors, sector_of)
    clusters = cl.find_clusters(residuals, calendar, min_breadth=min_breadth)

    # persistence — re-residualize the clustered members on a recent sub-window, check they recur
    member_retention = _persistence(
        clusters, closes_by_id, iwm=iwm, market_caps=cap_of, sector_of=sector_of,
        calendar=calendar, persist_days=persist_days, basis=basis,
    )

    window = WindowSpec(
        reference_date=ref, window_days=window_days,
        start=(calendar[0] if calendar else ref), end=(calendar[-1] if calendar else ref),
        trading_days=len(calendar),
    )
    admitted: list[CandidateTheme] = []
    rejected: list[CandidateTheme] = []
    rej = {"breadth": 0, "coherence": 0, "persistence": 0}
    mo = persist_days // 21
    for k, rc in enumerate(clusters):
        retention = member_retention.get(k)  # None = window too short to evaluate persistence
        note = (
            f"persistence NOT evaluated — window ≤ the ~{mo}mo sub-window"
            if retention is None
            else f"{retention:.0%} of members recur in the recent ~{mo}mo sub-window"
        )
        report = evaluate_admissibility(rc, member_retention=retention, persistence_note=note)
        members = [
            ThemeMember(
                ticker=name_by_id[m].ticker, name=name_by_id[m].name, cik=name_by_id[m].cik,
                sic=sic_of.get(m), sector=sector_of.get(m, "Unknown"),
                industry=(resolve_label(s).industry if (s := sic_of.get(m)) else None),
                sic_source_ref=f"EDGAR submissions SIC for CIK {name_by_id[m].cik}",
            )
            for m in rc.members if m in name_by_id
        ]
        theme = CandidateTheme(
            cluster_id=f"T{k:03d}",
            members=members,
            admissibility=report,
            candidate_linkage=candidate_linkage(members),
            strength_signals=compute_strength_signals(
                rc.members, closes_by_id, market_closes=iwm, calendar=calendar, reference_date=ref
            ),
            residual_basis=basis,
            window=window,
            tau_stability=rc.tau_stability,
        )
        if report.admissible:
            admitted.append(theme)
        else:
            rejected.append(theme)
            if not report.breadth_pass:
                rej["breadth"] += 1
            elif not report.coherence_pass:
                rej["coherence"] += 1
            else:
                rej["persistence"] += 1

    stats = DetectionStats(
        universe_size=len(names), names_with_coverage=len(residuals),
        names_dropped_insufficient_history=len(dropped), sic_resolved=n_sic,
        clusters_found=len(clusters), admissible=len(admitted),
        rejected_breadth=rej["breadth"], rejected_coherence=rej["coherence"],
        rejected_persistence=rej["persistence"],
    )
    return ThemeDetectionResult(
        reference_date=ref, residual_basis=basis, window=window,
        candidate_themes=admitted, rejected=rejected, stats=stats,
    )


def _persistence(
    clusters: list[cl.RawCluster],
    closes_by_id: dict[str, dict[date, float]],
    *,
    iwm: dict[date, float],
    market_caps: dict[str, float],
    sector_of: dict[str, str],
    calendar: list[date],
    persist_days: int,
    basis: FactorBasis,
) -> dict[int, float | None]:
    """Member-retention per cluster on the recent sub-window (criterion-4 persistence input).

    Returns ``None`` for every cluster when the detection window is not longer than the
    sub-window: persistence is then UN-evaluable (no earlier-vs-recent split), and fail-loud
    means NOT admitted — never a fabricated retention that silently auto-passes the gate."""
    if len(calendar) <= persist_days:
        return dict.fromkeys(range(len(clusters)), None)  # window too short — un-evaluable
    sub_cal = calendar[-persist_days:]
    sub_returns: dict[str, dict[date, float]] = {}
    for iid, c in closes_by_id.items():
        r = daily_returns(c, sub_cal)
        if r:
            sub_returns[iid] = r
    sub_market = daily_returns(iwm, sub_cal)
    members_union = {m for rc in clusters for m in rc.members}
    sub_factors = build_factors(
        sub_returns, market_returns=sub_market, sector_of=sector_of,
        market_cap_of=market_caps, calendar=sub_cal, basis=basis,
    )
    sub_residuals, _ = residualize(
        {m: sub_returns[m] for m in members_union if m in sub_returns}, sub_factors, sector_of
    )
    return {
        k: cl.connected_fraction(rc.members, sub_residuals, sub_cal)
        for k, rc in enumerate(clusters)
    }
