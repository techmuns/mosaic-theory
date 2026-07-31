"""Run Screen 2 across the stored universe — lazily, so it scales to thousands of names.

The price gates (G1 drawdown, G2 idiosyncratic) are computed from EOD bars for **every** name;
only the survivors pay an EDGAR fetch (G3 multiple-at-floor + non-distress). That confines the
per-name EDGAR cost to the handful of genuine de-ratings rather than the whole universe — the
cheap-gates-gate-the-expensive-ones discipline made operational.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from vinci.edgar import EdgarClient
from vinci.eod import EodClient, ingest_prices
from vinci.eod.features import window_facts
from vinci.progress import ProgressFn, ProgressReporter
from vinci.schemas.candidate import CandidateRecord, GateResult
from vinci.schemas.market import PriceBar
from vinci.screens.assemble import (
    DECLINE_WINDOW_DAYS,
    build_price_record,
    enrich_with_fundamentals,
)
from vinci.screens.retention import (
    CandidateRow,
    GateOutcome,
    Outcome,
    StampedInput,
    append_rows,
    outcome_from_gate,
    rollup,
)
from vinci.screens.screen2 import (
    Screen2Thresholds,
    evaluate_screen2,
    gate_g1_drawdown,
    gate_g2_idiosyncratic,
)
from vinci.store import Store
from vinci.universe import benchmark_identity


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
    progress: ProgressFn | None = None,
    retain_run_id: str | None = None,
    retain_dir: Path | None = None,
) -> tuple[list[CandidateRecord], dict[str, int]]:
    """Refresh prices, lazily screen the universe, persist candidates; return them + stats.

    RETENTION (``retain_run_id`` + ``retain_dir``, both or neither). Every name the screen TOUCHES
    gets a candidate row — all ~1,800, not the ~318 that survive. The gates ran on them, so the
    record says what the gates saw; a name dropped at G1 simply carries one gate rather than five.

    The reject set is the population that makes the gates falsifiable. Retaining survivors only can
    confirm the screen and never contradict it, and the 2026-07-27 benchmark bound was recoverable
    only because the survivors' values happened to persist — luck, not method.
    """
    # BOTH OR NEITHER, ENFORCED (review finding). The first cut COLLECTED rows on `retain_run_id`
    # but only WROTE them when `retain_dir` was also set — so a caller passing one and not the other
    # got 1,800 rows built, silently dropped, and a stats dict REPORTING them as retained. A
    # partially-configured retention that claims success is worse than one that refuses.
    if (retain_run_id is None) != (retain_dir is None):
        raise ValueError(
            "retain_run_id and retain_dir must be given together — one without the other builds "
            "retention rows and discards them while reporting them as retained")
    th = thresholds or Screen2Thresholds()
    # Screen the cap-band universe membership (not every security ever stored). Fall back to all
    # non-benchmark securities when no universe snapshot exists yet (e.g. a small test seed).
    ids = store.latest_universe(reference_date)
    if ids:
        universe = [s for iid in ids if (s := store.get_security(iid)) is not None]
    else:
        universe = [s for s in store.iter_securities() if not s.internal_id.startswith("IDX-")]
    start = reference_date - timedelta(days=lookback_days)

    ingest_prices(eod, store, universe, start=start, end=reference_date, progress=progress)
    bench = benchmark_identity(benchmark)
    store.upsert_security(bench)
    ingest_prices(eod, store, [bench], start=start, end=reference_date)
    bench_bars = store.get_price_history(bench.internal_id)

    run_at = datetime.combine(reference_date, datetime.min.time())
    store.clear_candidates()  # FULL replace — a re-screen is a clean snapshot, never an accretion
    candidates: list[CandidateRecord] = []
    g1_survivors = 0
    reporter = ProgressReporter("screen", len(universe), emit=progress, step=200)
    retained: list[CandidateRow] = []

    win_start = reference_date - timedelta(days=DECLINE_WINDOW_DAYS)

    def _keep(sec_ticker: str, rec: object, gates: dict[str, GateOutcome],
              name_bars: list[PriceBar]) -> None:
        if retain_run_id is None:
            return
        retained.append(CandidateRow(
            ticker=sec_ticker, run_id=retain_run_id, reference_date=reference_date,
            outcome=rollup(gates),
            gate_inputs=_gate_inputs(rec, name_bars, window_start=win_start), per_gate=gates,
            not_evaluated_reason=_first_unrun(gates)))

    for i, s in enumerate(universe, start=1):
        reporter.tick(i, suffix=f"{g1_survivors} enriched")
        bars = store.get_price_history(s.internal_id)
        rec = build_price_record(
            s, price_bars=bars, benchmark_bars=bench_bars,
            reference_date=reference_date, staleness_days=staleness_days,
        )
        # cheap price gates first — reject without any EDGAR call
        g1, g1_why = gate_g1_drawdown(rec, th)
        gates = {"g1_drawdown": GateOutcome(outcome=outcome_from_gate(g1), reason=g1_why)}
        if g1 is not GateResult.PASS:
            _keep(s.ticker, rec, gates, bars)
            continue
        g2, g2_why = gate_g2_idiosyncratic(rec, th)
        gates["g2_idiosyncratic"] = GateOutcome(outcome=outcome_from_gate(g2), reason=g2_why)
        if g2 is GateResult.FAIL:
            _keep(s.ticker, rec, gates, bars)
            continue
        g1_survivors += 1
        full = enrich_with_fundamentals(
            rec, edgar=edgar, price_bars=bars, reference_date=reference_date
        )
        cand = evaluate_screen2(full, screen_run_at=run_at, thresholds=th)
        if cand is not None:
            store.save_candidate(cand)
            candidates.append(cand)
        # G3 + distress ran inside evaluate_screen2; its verdict is the row's third gate
        gates["g3_and_distress"] = GateOutcome(
            outcome=(Outcome.PASS if cand is not None else Outcome.FAIL),
            reason=("admitted to the candidate set" if cand is not None
                    else "rejected by the multiple floor or a distress signal"))
        _keep(s.ticker, full, gates, bars)

    written = 0
    if retain_run_id is not None and retain_dir is not None:
        written = append_rows(retained, run_id=retain_run_id, snapshots_dir=retain_dir)

    return candidates, {
        "universe": len(universe),
        "g1_g2_survivors": g1_survivors,
        "candidates": len(candidates),
        # WHAT WAS WRITTEN, not what was built — the stat a caller trusts must be the one the
        # writer returned, or it reports evidence that does not exist on disk.
        "retained_candidate_rows": written,
    }


def _gate_inputs(rec: object, bars: list[PriceBar], *, window_start: date
                 ) -> dict[str, StampedInput]:
    """The gate inputs with THEIR OWN stamps — never the run's.

    A gate input claiming the reference date while its data stopped days earlier is exactly what
    made the benchmark incident invisible, so the field's own ``as_of`` and ``note`` travel with it.
    """
    prices = getattr(rec, "prices", None)
    out: dict[str, StampedInput] = {}
    for name in ("drawdown_from_high", "rel_ret_vs_market", "last"):
        f = getattr(prices, name, None)
        if f is None:
            continue
        win = (window_facts(bars, start=window_start, end=f.as_of)
               if name == "rel_ret_vs_market" and f.value is not None else None)
        out[name] = StampedInput(
            value=f.value, as_of=f.as_of if f.value is not None else None,
            source=f.source or "EOD", note=f.note,
            span_days=win[0] if win else None, observations=win[1] if win else None)
    return out


def _first_unrun(gates: dict[str, GateOutcome]) -> str | None:
    """The reason a row reads NOT_EVALUATED — the first gate that could not be assessed."""
    for g, o in gates.items():
        if o.outcome is Outcome.NOT_EVALUATED:
            return f"{g}: {o.reason}"
    return None
