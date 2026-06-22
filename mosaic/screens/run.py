"""Run Screen 2 across the stored universe — lazily, so it scales to thousands of names.

The price gates (G1 drawdown, G2 idiosyncratic) are computed from EOD bars for **every** name;
only the survivors pay an EDGAR fetch (G3 multiple-at-floor + non-distress). That confines the
per-name EDGAR cost to the handful of genuine de-ratings rather than the whole universe — the
cheap-gates-gate-the-expensive-ones discipline made operational.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from mosaic.edgar import EdgarClient
from mosaic.eod import EodClient, ingest_prices
from mosaic.schemas.candidate import CandidateRecord, GateResult
from mosaic.screens.assemble import build_price_record, enrich_with_fundamentals
from mosaic.screens.screen2 import (
    Screen2Thresholds,
    evaluate_screen2,
    gate_g1_drawdown,
    gate_g2_idiosyncratic,
)
from mosaic.store import Store
from mosaic.universe import benchmark_identity


def screen_universe(
    store: Store,
    eod: EodClient,
    edgar: EdgarClient,
    *,
    reference_date: date,
    lookback_days: int,
    staleness_days: int,
    benchmark: str = "IWM",
    thresholds: Screen2Thresholds | None = None,
) -> tuple[list[CandidateRecord], dict[str, int]]:
    """Refresh prices, lazily screen the universe, persist candidates; return them + stats."""
    th = thresholds or Screen2Thresholds()
    # Screen the cap-band universe membership (not every security ever stored). Fall back to all
    # non-benchmark securities when no universe snapshot exists yet (e.g. a small test seed).
    ids = store.latest_universe(reference_date)
    if ids:
        universe = [s for iid in ids if (s := store.get_security(iid)) is not None]
    else:
        universe = [s for s in store.iter_securities() if not s.internal_id.startswith("IDX-")]
    start = reference_date - timedelta(days=lookback_days)

    ingest_prices(eod, store, universe, start=start, end=reference_date)
    bench = benchmark_identity(benchmark)
    store.upsert_security(bench)
    ingest_prices(eod, store, [bench], start=start, end=reference_date)
    bench_bars = store.get_price_history(bench.internal_id)

    run_at = datetime.combine(reference_date, datetime.min.time())
    store.clear_candidates()  # FULL replace — a re-screen is a clean snapshot, never an accretion
    candidates: list[CandidateRecord] = []
    g1_survivors = 0
    for s in universe:
        bars = store.get_price_history(s.internal_id)
        rec = build_price_record(
            s, price_bars=bars, benchmark_bars=bench_bars,
            reference_date=reference_date, staleness_days=staleness_days,
        )
        # cheap price gates first — reject without any EDGAR call
        if gate_g1_drawdown(rec, th)[0] is not GateResult.PASS:
            continue
        if gate_g2_idiosyncratic(rec, th)[0] is GateResult.FAIL:
            continue
        g1_survivors += 1
        full = enrich_with_fundamentals(
            rec, edgar=edgar, price_bars=bars, reference_date=reference_date
        )
        cand = evaluate_screen2(full, screen_run_at=run_at, thresholds=th)
        if cand is not None:
            store.save_candidate(cand)
            candidates.append(cand)

    return candidates, {
        "universe": len(universe),
        "g1_g2_survivors": g1_survivors,
        "candidates": len(candidates),
    }
