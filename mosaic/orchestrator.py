"""Configure-once orchestration for the scheduled jobs (GitHub Actions cron).

Each run is self-contained and idempotent: **rebuild** the working DB from the committed JSONL
snapshots, **refresh** EOD prices for the stored universe (the immutable per-day grouped-daily
responses are cached, so only new days hit the network), run the **screen** (weekly) or the
**scoring** (monthly), then **export** the snapshots back for the workflow to commit. Bulk prices
are not snapshotted (re-pullable + cached); the durable state is the entity master, universe,
candidates, ledger, and as-reported fundamentals.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from mosaic.config import Config, get_config
from mosaic.edgar import EdgarClient
from mosaic.eod import PolygonEodClient, ingest_prices
from mosaic.schemas.data_record import Identity
from mosaic.scoring import score_ledger
from mosaic.screens import build_data_record, evaluate_screen2
from mosaic.store import Store

# ~52 weeks + buffer: enough history for the 52w drawdown and the multiple range.
_SCREEN_LOOKBACK_DAYS = 400
# Monthly scoring refreshes ~2y (the Polygon free-tier max) so verdicts entered within that window
# have their forward prices available; verdicts older than this are beyond the free feed's reach.
_SCORE_LOOKBACK_DAYS = 730


def benchmark_identity(symbol: str) -> Identity:
    """Synthetic identity for a benchmark ETF (not a SEC issuer → not resolver-resolved)."""
    return Identity(
        internal_id=f"IDX-{symbol}", issuer_id="IDX", cik="", ticker=symbol, mic="ARCX",
        exchange="ETF", eod_symbol=symbol, name=f"{symbol} (benchmark)",
    )


def _latest_bar_date(store: Store, internal_id: str) -> date | None:
    bars = store.get_price_history(internal_id)
    return bars[-1].bar_date if bars else None


def run_weekly(
    config: Config | None = None, *, end: date, benchmark: str = "IWM"
) -> dict[str, object]:
    """Weekly: refresh the universe's prices and run Screen 2; persist candidates to snapshots."""
    cfg = config or get_config()
    cfg.ensure_dirs()
    client = PolygonEodClient.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)
    bench = benchmark_identity(benchmark)
    start = end - timedelta(days=_SCREEN_LOOKBACK_DAYS)
    with Store(cfg.db_path) as store:
        store.rebuild_from_snapshots(cfg.snapshots_dir)
        universe = [s for s in store.iter_securities() if not s.internal_id.startswith("IDX-")]
        if not universe:
            return {"status": "no universe in snapshots — seed it first"}
        ingest_prices(client, store, universe, start=start, end=end)
        store.upsert_security(bench)
        ingest_prices(client, store, [bench], start=start, end=end)

        ref = _latest_bar_date(store, universe[0].internal_id) or end
        bench_bars = store.get_price_history(bench.internal_id)
        run_at = datetime.combine(ref, datetime.min.time())
        n_candidates = 0
        for s in universe:
            rec = build_data_record(
                s, price_bars=store.get_price_history(s.internal_id), benchmark_bars=bench_bars,
                edgar=edgar, reference_date=ref, staleness_days=cfg.price_staleness_days,
            )
            cand = evaluate_screen2(rec, screen_run_at=run_at)
            if cand is not None:
                store.save_candidate(cand)
                n_candidates += 1
        store.export_snapshots(cfg.snapshots_dir)
    return {"universe": len(universe), "candidates": n_candidates, "ref": ref.isoformat()}


def run_monthly(
    config: Config | None = None,
    *,
    as_of: date,
    benchmark: str = "IWM",
    cost_bps: float = 25.0,
    lookback_days: int = _SCORE_LOOKBACK_DAYS,
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
            ingest_prices(client, store, universe, start=start, end=as_of)
            store.upsert_security(bench)
            ingest_prices(client, store, [bench], start=start, end=as_of)
        _scores, report = score_ledger(
            store, as_of=as_of, cost_bps=cost_bps, benchmark_internal_id=f"IDX-{benchmark}"
        )
        store.export_snapshots(cfg.snapshots_dir)
    (cfg.snapshots_dir / "scoring_report.md").write_text(report.to_markdown())
    return report.to_dict()
