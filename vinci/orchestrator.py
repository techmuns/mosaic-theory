"""Configure-once orchestration for the scheduled jobs (GitHub Actions cron).

Each run is self-contained and idempotent: **rebuild** the working DB from the committed JSONL
snapshots, **refresh** EOD prices for the stored universe (the immutable per-day grouped-daily
responses are cached, so only new days hit the network), run the **screen** (weekly) or the
**scoring** (monthly), then **export** the snapshots back for the workflow to commit. Bulk prices
are not snapshotted (re-pullable + cached); the durable state is the entity master, universe,
candidates, ledger, and as-reported fundamentals.
"""

from __future__ import annotations

from datetime import date, timedelta

from vinci.config import Config, get_config
from vinci.edgar import EdgarClient
from vinci.eod import PolygonEodClient, ingest_prices
from vinci.progress import ProgressFn
from vinci.scoring import score_ledger
from vinci.scoring.baseline import resolve_baskets
from vinci.screens import screen_universe
from vinci.store import Store
from vinci.universe import benchmark_identity

# ~5y: enough history for the 52w drawdown AND the G3 multiple-at-floor range (Polygon Starter).
_SCREEN_LOOKBACK_DAYS = 1825
# Monthly scoring refreshes ~2y so verdicts in that window have forward prices to score against.
_SCORE_LOOKBACK_DAYS = 730


def run_weekly(
    config: Config | None = None,
    *,
    end: date,
    benchmark: str = "IWM",
    lookback_days: int = _SCREEN_LOOKBACK_DAYS,
    progress: ProgressFn | None = None,
) -> dict[str, object]:
    """Weekly: refresh the universe's prices and lazily run Screen 2; persist candidates."""
    cfg = config or get_config()
    cfg.ensure_dirs()
    eod = PolygonEodClient.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
        if not any(not s.internal_id.startswith("IDX-") for s in store.iter_securities()):
            return {"status": "no universe in snapshots — run build-universe first"}
        _cands, stats = screen_universe(
            store, eod, edgar, reference_date=end, lookback_days=lookback_days,
            staleness_days=cfg.price_staleness_days, benchmark=benchmark, progress=progress,
        )
        store.export_snapshots(cfg.snapshots_dir)
    return {**stats, "ref": end.isoformat()}


def run_monthly(
    config: Config | None = None,
    *,
    as_of: date,
    benchmark: str = "IWM",
    cost_bps: float = 25.0,
    lookback_days: int = _SCORE_LOOKBACK_DAYS,
    progress: ProgressFn | None = None,
) -> dict[str, object]:
    """Monthly: refresh prices, score the decision ledger, and write the report to snapshots.

    Prices are not snapshotted (re-pullable), so we refresh them before scoring — else a fresh CI
    checkout would have no forward prices to score against. The grouped-daily cache keeps this fast.
    """
    cfg = config or get_config()
    cfg.ensure_dirs()
    client = PolygonEodClient.from_config(cfg)
    bench = benchmark_identity(benchmark)
    start = as_of - timedelta(days=lookback_days)
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
        universe = [s for s in store.iter_securities() if not s.internal_id.startswith("IDX-")]
        if universe:
            ingest_prices(client, store, universe, start=start, end=as_of, progress=progress)
            store.upsert_security(bench)
            ingest_prices(client, store, [bench], start=start, end=as_of)
        _scores, report = score_ledger(
            store, as_of=as_of, cost_bps=cost_bps, benchmark_internal_id=f"IDX-{benchmark}",
            # Wired here as well as in `vinci score` — see that call site's note.
            # `scoring_report.md` is the artifact most readers open, so a kill test missing
            # from it is missing.
            baskets=resolve_baskets(cfg.data_dir / "followed.json", store.iter_securities()),
        )
        store.export_snapshots(cfg.snapshots_dir)
    (cfg.snapshots_dir / "scoring_report.md").write_text(report.to_markdown())
    return report.to_dict()
